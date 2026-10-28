# Per-structure history of NoSpherA2 calculations: olex2/<name>_calculation_log.txt next to the
# structure. Append-only, one block per refinement or table calculation, each line written as it
# happens so an aborted run still leaves its record. Nothing here may break or change a refinement:
# every entry point swallows its own errors, and settings are read without nsa2_get_param, which
# writes what it returns into the structure header.
# Always import as NoSpherA2.calc_log: the open entry is module state.
import os, time, datetime, functools
from olexFunctions import OV

_entry = None

# NSA2_ header keys (upper-cased) that describe each generator; the rest of the header is GUI state it ignored
_COMMON = ('CHARGE', 'MULTIPLICITY', 'NOSPHERA2_SF', 'BECKE_ACCURACY')
_QM = ('METHOD', 'BASIS_NAME', 'RELATIVISTIC')
_BY_SOURCE = (
  ('ORCA', _QM + ('ORCA_RELATIVISTIC', 'ORCA_VERSION', 'ORCA_SCF_CONV', 'ORCA_SCF_STRATEGY', 'ORCA_SOLVATION',
                  'ORCA_USE_CRYSTAL_QMMM', 'ORCA_CRYSTAL_QMMM_TYPE', 'ORCA_CRYSTAL_QMMM_RADIUS')),
  ('PYSCF', _QM + ('PYSCF_DAMPING',)),
  ('TONTO', _QM + ('CLUSTER_RADIUS', 'CLUSTER_GROW', 'DIIS')),
  ('PTB', ()),
  ('XTB', ('METHOD',)),
  ('SALTED', ('SELECTED_SALTED_MODEL',)),
  ('THAKKAR', ('THAKKAR_CATIONS', 'THAKKAR_ANIONS')),
  ('HYBRID', ()),
)


def _safe(fn):
  @functools.wraps(fn)
  def wrapped(*a, **k):
    try:
      return fn(*a, **k)
    except Exception as e:
      print("Calculation log (%s): %s" % (fn.__name__, e))
  return wrapped


def _p(key):
  """a NoSpherA2 setting as nsa2_get_param resolves it, without storing it in the header"""
  from variableFunctions import _nsa2_normalize_param_key, _nsa2_header_key_from_param
  k = _nsa2_normalize_param_key(key)
  v = OV.GetHeaderParam(_nsa2_header_key_from_param(k), None)
  return v if v not in (None, '') else OV.GetParam(k)


def _path():
  d = os.path.join(OV.FilePath(), "olex2")
  os.makedirs(d, exist_ok=True)
  return os.path.join(d, "%s_calculation_log.txt" % OV.FileName())


def _write(*lines):
  try:
    with open(_path(), 'a', encoding='utf-8') as f:
      for l in lines:
        f.write(l + "\n")
  except Exception as e:
    print("Calculation log not written: %s" % e)


def _now():
  return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def _dur(s):
  if s < 60:
    return "%.1f s" % s
  return str(datetime.timedelta(seconds=int(round(s))))


def _num(v, scale=1.0, fmt="%.2f"):
  try:
    return fmt % (float(v) * scale)
  except (TypeError, ValueError):
    return "n/a"


def _table():
  t = str(_p('file') or '').strip()
  if t and not os.path.isabs(t):
    t = os.path.join(OV.FilePath(), t)
  return t


def _table_settings(table):
  try:
    from NoSpherA2.utilities import nsa2_read_settings_header
    return nsa2_read_settings_header(table) if table and os.path.exists(table) else None
  except Exception:
    return None


def _settings_lines(rec, source):
  """the settings that made a table, as key = value lines, restricted to what its generator uses"""
  if rec is None:
    return ["  (table header records no settings; GUI state: method = %s, basis = %s, charge = %s, multiplicity = %s)"
            % (_p('method'), _p('basis_name'), _p('charge'), _p('multiplicity'))]
  key = (str(rec.get('ORIGIN') or '') + str(rec.get('SOURCE') or '') + source).replace(' ', '').upper()
  keys = ('METHOD', 'BASIS_NAME')
  for name, k in _BY_SOURCE:
    if name in key:
      keys = k
      break
  keys = _COMMON + keys + tuple(sorted(k for k in rec if k.startswith('HYBRID.')))
  if 'TRUE' not in str(rec.get('ORCA_USE_CRYSTAL_QMMM', '')).upper():
    keys = tuple(k for k in keys if not k.startswith('ORCA_CRYSTAL_QMMM_'))
  if 'TRUE' not in str(rec.get('RELATIVISTIC', '')).upper():
    keys = tuple(k for k in keys if k != 'ORCA_RELATIVISTIC')
  out = ["  %s = %s" % (k.lower(), rec[k]) for k in keys if k in rec]
  if 'PTB' in key:
    out.append("  ptb_use_purify = %s" % _p('PTB_use_purify'))
  return out


def _header(kind, source):
  lines = ["", "=== %s: %s ===" % (kind, _now()),
           "structure = %s" % OV.FileFull(),
           "source = %s" % source]
  try:
    from NoSpherA2.utilities import nsa2_model_fingerprint
    fp = nsa2_model_fingerprint()
    if 'hkl' in fp:
      lines.append("hkl = %s (sha256 %s)" % (fp['hkl'], fp.get('hkl_sha256', '')[:16]))
  except Exception:
    pass
  try:
    parts = OV.ListParts()
    if parts:
      lines.append("parts = %s" % ", ".join(str(p) for p in parts))
  except Exception:
    pass
  lines.append("cpus = %s, memory = %s GB" % (_p('ncpus'), _p('mem')))
  return lines


class _Refinement:
  def __init__(self, source):
    self.source = source
    self.t0 = time.time()
    self.cycle_t0 = None
    self.wfn_s = 0.0
    self.last = None
    self.cycles = []
    self.closed = False
    self.in_cycle = False


@_safe
def begin_refinement(source, prerefine_note, full_har, max_cycles, n_pre):
  global _entry
  _entry = _Refinement(source)
  lines = _header("NoSpherA2 refinement", source)
  pre = " after %d pTB cycle%s" % (n_pre, "" if n_pre == 1 else "s") if n_pre else ""
  mode = ("iterative, max %d HAR cycles" % max_cycles if full_har else "single cycle") + pre
  if 'FALSE' in str(_p('run_refine')).upper():
    mode += ", refinement switched off (table only)"
  lines.append("mode = %s" % mode)
  lines.append("pTB pre-refinement = %s" % prerefine_note)
  lines.append("h_aniso = %s, h_afix = %s" % (_p('h_aniso'), _p('h_afix')))
  _write(*lines)


@_safe
def cycle_start(pre=False):
  if _entry is not None:
    _entry.cycle_t0 = time.time()
    _entry.wfn_s = 0.0
    _entry.in_cycle = not pre


@_safe
def table_done(source, ok, seconds):
  """called by NoSpherA2.launch; inside a refinement it only books the time, alone it is its own entry"""
  if _entry is not None and not _entry.closed:
    _entry.wfn_s += seconds
    return
  if ".tsc" in source or "Please S" in source:
    return
  lines = _header("NoSpherA2 table calculation (no refinement)", source)
  if ok:
    table = _table()
    lines += ["settings:"] + _settings_lines(_table_settings(table), source)
    lines.append("result = table written: %s, %s" % (os.path.basename(table), _dur(seconds)))
  else:
    lines.append("result = failed after %s (NoSpherA2-Error: %s)" % (_dur(seconds), OV.GetVar('NoSpherA2-Error')))
  lines.append("=== end ===")
  _write(*lines)


@_safe
def cycle_end(run, pre, source, r=None):
  """one line per HAR cycle; the settings block is repeated only when the generator or its settings change"""
  e = _entry
  if e is None:
    return
  rec = _table_settings(_table())
  block = [source] + _settings_lines(rec, source)
  if rec and ".tsc" in source.lower():  # refinement on an existing table: the program that made it is the level
    block.append("  generator = %s" % str(rec.get('SOURCE') or '').strip())
  lines = []
  if block != e.last:
    lines.append("settings (%s, from cycle %d):" % (source, run))
    lines += block[1:]
    lines.append("  cycle  source           wfn+tsc   refine   max shift/esd  label            R1[%]  wR2[%]")
    e.last = block
  total = time.time() - (e.cycle_t0 or e.t0)
  if r is None:
    lines.append("  %5d  %-15s %8s %8s   (table only, no refinement)" % (run, source[:15], _dur(e.wfn_s), "-"))
  else:
    lines.append("  %5d  %-15s %8s %8s %15s  %-15s %6s %7s" % (
      run, source[:15], _dur(e.wfn_s), _dur(total - e.wfn_s), _num(r.max_overall, fmt="%.4f"),
      str(r.label_overall or "n/a")[:15], _num(r.r1, 100), _num(r.wr2, 100)))
  e.cycles.append((source, pre, r is not None))
  e.in_cycle = False
  _write(*lines)


@_safe
def end_refinement(converged, full_har, failed):
  e = _entry
  if e is None or e.closed:
    return
  n_pre = sum(1 for s, p, refined in e.cycles if p)
  n = len(e.cycles)
  split = " (%d pTB + %d %s)" % (n_pre, n - n_pre, e.source) if n_pre else ""
  e.closed = True
  if not any(refined for s, p, refined in e.cycles):
    _write("result = table written, no refinement: %s, %s" % (os.path.basename(_table()), _dur(time.time() - e.t0)),
           "=== end ===")
    return
  if any("pTB pre-refinement" in str(f) for f in failed or []):
    status = "STOPPED by the R1 guard in pTB cycle %d, follow-up source not run" % n
  elif converged and full_har:
    status = "converged after %d cycles%s" % (n, split)
  elif converged or not full_har:
    status = "finished, %d cycle(s)%s" % (n, split)
  else:
    status = "NOT converged after %d cycles%s" % (n, split)
  lines = ["result = %s, total %s" % (status, _dur(time.time() - e.t0))]
  for f in failed or []:
    lines.append("warning = %s" % f)
  lines.append("final R1 = %s %%, wR2 = %s %%, GoF = %s" % (
    _num(OV.GetParam('snum.refinement.last_R1'), 100), _num(OV.GetParam('snum.refinement.last_wR2'), 100),
    _num(OV.GetParam('snum.refinement.goof'), fmt="%.4f")))
  lines.append("residual density max/min/rms = %s / %s / %s e/A^3" % (
    _num(OV.GetParam('snum.refinement.max_peak'), fmt="%+.3f"), _num(OV.GetParam('snum.refinement.max_hole'), fmt="%+.3f"),
    _num(OV.GetParam('snum.refinement.res_rms'), fmt="%.3f")))
  lines.append("table = %s" % os.path.basename(_table()))
  lines.append("=== end ===")
  _write(*lines)


_LEVEL_KEYS = ('method', 'basis_name')


def _level(source, settings):
  """what defines a level of theory: the program, method and basis, per part for Hybrid"""
  return (source.upper(),) + tuple(sorted((k, v.upper()) for k, v in settings.items()
          if k in _LEVEL_KEYS or (k.startswith('hybrid.') and k.split('.')[1].rsplit('_part', 1)[0] in ('software',) + _LEVEL_KEYS)))


def _path_if_any():
  path = os.path.join(OV.FilePath(), "olex2", "%s_calculation_log.txt" % OV.FileName())
  return path if os.path.exists(path) else None


def has_log():
  try:
    return _path_if_any() is not None
  except Exception:
    return False


def _history():
  """the level of theory of every refined cycle in this structure's log, oldest first"""
  path = _path_if_any()
  if path is None:
    return []
  rows, in_run, source, settings, in_settings = [], False, "", {}, False
  with open(path, encoding='utf-8') as f:
    lines = f.readlines()
  for line in lines:
    s = line.strip()
    if s.startswith("=== "):
      in_run = s.startswith("=== NoSpherA2 refinement:")
    elif not in_run:
      continue
    elif s.startswith("settings (") and s.endswith("):"):
      source, settings, in_settings = s[len("settings ("):].rsplit(", from cycle", 1)[0], {}, True
    elif s.startswith("(table header records no settings"):
      for k, n in (('method', 'method'), ('basis_name', 'basis')):
        settings[k] = s.split(" %s = " % n, 1)[1].split(",", 1)[0] if " %s = " % n in s else ""
    elif s.startswith("cycle  source"):
      in_settings = False
    elif in_settings and " = " in s:
      k, v = s.split(" = ", 1)
      settings[k.lower()] = v.strip()
    elif s.split(" ", 1)[0].isdigit() and "(table only" not in s:
      rows.append(_level(settings.get('generator') or source, settings))
  return rows


@_safe
def ptb_before_level(software, method, basis, hybrid):
  """(pTB cycles, cycles after them) when the log shows that the last pTB refinement cycles, from the pre-refine
  checkbox or from pTB chosen as the source, were followed only by refinements at this table's level of theory
  (software, method, basis, HYBRID.* record); None when it does not show that"""
  rows = _history()
  # olex2.refine builds the CIF inside the cycle, before cycle_end logs it: that cycle refines with this very table
  if _entry is not None and not _entry.closed and _entry.in_cycle:
    rows.append(None)
  last = max((i for i, l in enumerate(rows) if l and l[0] == "PTB"), default=None)
  if last is None:
    return None
  after = rows[last + 1:]
  logged = [l for l in after if l is not None]
  if not after or len(set(logged)) > 1:
    return None
  if logged:
    src, kv = logged[0][0], dict(logged[0][1:])
    if not src or src != str(software).strip().upper() or (src == "HYBRID" and not hybrid):
      return None
    want = {'method': method, 'basis_name': basis}
    want.update((k.lower(), v) for k, v in (hybrid or {}).items())
    for k, v in kv.items():
      if k in want and str(want[k]).strip().upper() != v.strip():
        return None
  n = last
  while n > 0 and rows[n - 1] and rows[n - 1][0] == "PTB":
    n -= 1
  return last + 1 - n, len(after)


@_safe
def close_refinement(error=None):
  """the run is over however it ended; an entry that end_refinement did not finish records how it stopped"""
  global _entry
  e = _entry
  _entry = None
  if e is None or e.closed:
    return
  nsa2_error = OV.GetVar('NoSpherA2-Error')
  if error is not None:
    why = "error: %s" % error
  elif nsa2_error and str(nsa2_error) != "None":
    why = "aborted (NoSpherA2-Error: %s)" % nsa2_error
  else:
    why = "aborted"
  _write("result = %s after %d cycle(s), %s" % (why, len(e.cycles), _dur(time.time() - e.t0)), "=== end ===")
