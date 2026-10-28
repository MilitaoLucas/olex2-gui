"""Incommensurately modulated structures, (3+1)D: hklm data, superspace group, refinement and the wiggle movie.

The 3D model in Olex2 is the average (basic) structure, e.g. a FLINT solution of the m = 0 reflections; q, the
x4 translations tau and the displacement waves live in the .ins header (scope 'modulation'). The maths is
smtbx.modulation.

  spy.modulation.load(file, [qx, qy, qz])  .hklm (4I4,2F8 or free) or msCIF/fcf becomes the HKL source; Olex2
                                           reads .hklm natively (3D tools see m = 0, olx.HKLM() counts satellites)
  spy.modulation.candidates()              superspace groups of the current space group + q, ranked by absences
  spy.modulation.choose(n)                 take candidate n of the last ranking
  spy.modulation.refine([cycles, harmonics])  also refines the occupancy/ADP waves, crenels, Legendre and
                                           x-harmonic terms the model has (msCIF import or an earlier refine)
  spy.modulation.hold([family, on])        hold one of those families fixed in refine: occ_waves, adp_waves,
                                           crenel, legendre, xharm, u_xharm (no argument: list what is held)
  spy.modulation.wiggle() / stop()         animate the asymmetric unit in the viewer, section t = 0..1
  spy.modulation.movie([file])             GIF of a supercell along q, every symmetry copy on its own wave
  spy.modulation.de_wolff([label, axis])   de Wolff section x_i - x4 of the superspace Fourier map (PNG)
A JANA msCIF can be loaded too: spy.modulation.load(file.cif) takes q, its superspace operators and the
displacive waves from it, and the hklm data from its refln loop or <name>.fcf.
With NoSpherA2 on, updating its table with q set also writes <name>.tscm, the form factors at every S = h + m q
from the same wavefunction (rigid-atom: the aspherical density moves with its atom); refine and de_wolff use it.
"""
import math
import os

import numpy as np

import olex
import olx
from olexFunctions import OV
from misc.ins_header import OlxInsHeaderScope
import hklm_util

from cctbx import adptbx, sgtbx, uctbx
try:
  from smtbx import modulation as smod
except ImportError:  # an older cctbx bundle: Olex2 must still start, the functions say why they fail
  smod = None

class _Store(object):
  """The .ins header (scope 'modulation'), mirrored into <name>.modulation beside the structure: a solve
  (FLINT's reset and re-reap of the .res) drops the header, the sidecar carries q and the waves across."""

  def __init__(self):
    self.header = OlxInsHeaderScope("modulation")

  def _path(self):
    return os.path.join(OV.FilePath(), OV.FileName() + ".modulation")

  def _side(self):
    out = {}
    if os.path.exists(self._path()):
      for line in open(self._path()):
        if "=" in line:
          k, v = line.rstrip("\n").split("=", 1)
          out[k] = v
    return out

  def get(self, key, default=None):
    v = self.header.get(key)
    if v in (None, ""):
      v = self._side().get(key, default)
      if v not in (None, ""):
        self.header.set(key, v)
    return v

  def set(self, key, value):
    self.header.set(key, value)
    side = self._side()
    side[key] = str(value)
    with open(self._path(), "w") as f:
      for k in sorted(side):
        f.write("%s=%s\n" % (k, side[k]))


store = _Store()
_last_ranking = []


# what belongs to the data rather than to a model, and so outlives reset(): the hklm path, its q (the m index
# means nothing without it) and the families the user holds fixed
_KEEP_ACROSS_RESET = ("hklm", "q", "hold")


def reset():
  """Forget the superspace group, the waves and the fit: a new solution starts from 3D. The hklm path and its q stay
  (they describe the data, not the model), so the solve can rank the superspace groups of the group it finds."""
  side = store._side()
  keys = set(side) | {"q", "ops", "taus", "group", "scale", "r1", "commensurate"}
  keys |= {pre + olx.xf.au.GetAtomName(i) for i in range(int(olx.xf.au.GetAtomCount())) for pre in ("wave.", "mwave.")}
  kept = dict((k, store.get(k)) for k in _KEEP_ACROSS_RESET if store.get(k) not in (None, ""))
  for k in keys:
    if k in kept:
      continue
    try:
      store.header.delete(k)
    except Exception:
      pass
  if os.path.exists(store._path()) or kept:
    with open(store._path(), "w") as f:
      for k in sorted(kept):
        f.write("%s=%s\n" % (k, kept[k]))
  _clear_caches()


def after_solve():
  """After a structure solution (tidy_solution): rank the superspace groups of the group found when q is known,
  else say how to give it. Returns True when candidates() ran."""
  if store.get("q"):
    candidates()
    return True
  if olx.HKLSrc().lower().endswith(".hklm"):
    print("modulation: solved from the main reflections; give q (spy.modulation.set_q, or 'set q' under "
          "the HOS) for the superspace groups and the modulated refinement")
  return False
_stop = [False]


def _file_key(path):
  """What identifies a data file's contents for the caches here: path, size and mtime in ns."""
  st = os.stat(path)
  return (os.path.abspath(path), st.st_size, st.st_mtime_ns)


# Caches, each keyed on everything its value depends on and emptied by reset():
#   _data_cache     the hklm data: keyed on the file (path, size, mtime)
#   _ranking_cache  candidates()' ranked list: keyed on the basic group (Hall), q, the data file and the tau
#                   values, so a FLINT solve that lands on the same group with the same q and data reuses it
#   _stats_cache    satellite_stats: keyed on the file, q, taus, ops, cell and Hall symbol
_data_cache, _ranking_cache = {}, {}


def _clear_caches():
  _data_cache.clear()
  _ranking_cache.clear()
  _stats_cache.clear()


def _floats(s):
  return [float(v) for v in str(s).replace(",", " ").split()]


# the block families beyond the displacive waves, by their smtbx.modulation flag, and the atom attributes of each
EXTRA_FAMILIES = (("occ_waves", ("occ_sin", "occ_cos")), ("adp_waves", ("u_sin", "u_cos")), ("crenel", ("crenel",)),
                  ("legendre", ("legendre",)), ("xharm", ("xharm",)), ("u_xharm", ("u_xharm",)))
_EXTRA_WIDTH = {"occ_sin": 1, "occ_cos": 1, "u_sin": 6, "u_cos": 6, "legendre": 3, "xharm": 3, "u_xharm": 6}


def extras_text(at):
  """The atom's waves other than the displacive ones as one store line, 'name v v ...; name ...'; '' if none.
  The sawtooth is carried too (it is not refined)."""
  parts = []
  for name in ("occ_sin", "occ_cos", "u_sin", "u_cos", "legendre", "xharm", "u_xharm"):
    v = np.asarray(getattr(at, name), dtype=float).ravel()
    if v.size:
      parts.append(name + " " + " ".join("%.10g" % x for x in v))
  if getattr(at, "crenel", None):
    parts.append("crenel %.10g %.10g" % tuple(at.crenel))
  if getattr(at, "sawtooth", None) is not None:
    a, c, w = at.sawtooth
    parts.append("sawtooth " + " ".join("%.10g" % x for x in list(a) + [c, w]))
  return "; ".join(parts)


def apply_extras(at, text):
  """Put the waves of an extras_text line onto a modulated_atom."""
  for part in (text or "").split(";"):
    t = part.split()
    if not t:
      continue
    name, v = t[0], [float(x) for x in t[1:]]
    if name in _EXTRA_WIDTH:
      arr = np.array(v, dtype=float)
      setattr(at, name, arr if _EXTRA_WIDTH[name] == 1 else arr.reshape(-1, _EXTRA_WIDTH[name]))
    elif name == "crenel":
      at.crenel = (v[0], v[1])
    elif name == "sawtooth":
      at.sawtooth = (np.array(v[:3]), v[3], v[4])
  return at


def _held():
  return set((store.get("hold") or "").split())


def refine_flags(atoms, held=()):
  """smtbx.modulation flags for refine: each family on where some atom has it and it is not held. A family no atom
  has is off either way (its blocks are empty), so a model with displacive waves only refines as before."""
  flags = {}
  for family, names in EXTRA_FAMILIES:
    present = any(bool(at.crenel) if n == "crenel" else len(getattr(at, n)) for at in atoms for n in names)
    flags[family] = bool(present) and family not in held
  return flags


def hold(family="", on=True):
  """Hold a block family fixed in spy.modulation.refine (on=False frees it again); no family: list them."""
  families = [f for f, _ in EXTRA_FAMILIES]
  held = _held()
  if family:
    if family not in families:
      print("modulation: hold takes one of %s" % ", ".join(families))
      return
    if str(on).lower() in ("false", "0", "no", "off"):
      held.discard(family)
    else:
      held.add(family)
    store.set("hold", " ".join(sorted(held)))
  print("modulation: held in refine: %s" % (", ".join(sorted(held)) or "nothing"))


def _q():
  if smod is None:
    raise RuntimeError("this cctbx bundle has no smtbx.modulation")
  q = store.get("q")
  if not q:
    raise RuntimeError("no q vector: spy.modulation.load(file, qx, qy, qz) first")
  q = np.array(_floats(q))
  sec = _commensurate()
  if sec is not None:
    q = np.round(q * sec[1]) / sec[1]     # commensurate: q exactly r / N (the store keeps 6 decimals)
  return q


def _commensurate():
  """(t0, N) when the loaded msCIF is a commensurate JANA refinement (store "commensurate"), else None."""
  v = store.get("commensurate")
  if not v:
    return None
  t0, n = v.split()
  return float(t0), int(n)


def read_hklm(path):
  """(h (N,3), m (N,), I, sigma, q or None) from an hklm text file (4I4,2F8) or a CIF refln loop."""
  if path.lower().endswith((".cif", ".fcf")):
    import iotbx.cif
    model = iotbx.cif.reader(file_path=path).model()
    for block in model.values():
      if "_refln_index_h" not in block:
        continue
      mkey = "_refln_index_m_1" if "_refln_index_m_1" in block else "_refln_index_m"
      if mkey not in block:
        raise RuntimeError("%s has no _refln_index_m column" % path)
      if "_refln_index_m_2" in block:
        raise RuntimeError("(3+2)D data: only one q vector is supported")
      col = lambda k: np.array([float(v) for v in block[k]])
      h = np.array([col("_refln_index_h"), col("_refln_index_k"), col("_refln_index_l")]).T.astype(int)
      q = None
      if "_cell_wave_vector_x" in block:
        first = lambda k: float(block[k]) if isinstance(block[k], str) else float(list(block[k])[0])
        q = np.array([first("_cell_wave_vector_" + a) for a in "xyz"])
      return (h, col(mkey).astype(int), col("_refln_F_squared_meas"), col("_refln_F_squared_sigma"), q)
    raise RuntimeError("no refln loop in %s" % path)
  return hklm_util.read_hklm(path) + (None,)


_MARK = "# hklm written by spy.modulation"


def _write_hklm(path, h, m, i_obs, sig, source):
  """h k l m I sigma as 4I4,2F8 under a marker line; an existing .hklm is only replaced when it carries the
  marker, so a user's own data file is never overwritten."""
  if os.path.exists(path) and not open(path, errors="replace").readline().startswith(_MARK):
    raise RuntimeError("%s exists and was not written by spy.modulation; not overwriting it" % path)
  f8 = lambda x: ("%8.2f" % x) if len("%8.2f" % x) <= 8 else ("%8.0f" % x)[:8]
  with open(path, "w") as f:
    f.write("%s from %s\n" % (_MARK, os.path.basename(source)))
    for (a, b, c), mm, ii, ss in zip(h, m, i_obs, sig):
      f.write("%4d%4d%4d%4d%s%s\n" % (a, b, c, mm, f8(ii), f8(ss)))
    f.write("   0   0   0   0    0.00    0.00\n")


def _data():
  path = store.get("hklm")
  if not path or not os.path.exists(path):
    raise RuntimeError("hklm file %r not found: spy.modulation.load(file) first" % path)
  key = _file_key(path)
  if _data_cache.get("key") != key:
    _data_cache.update(key=key, value=read_hklm(path)[:4])
  return _data_cache["value"]


def _table_path():
  return os.path.join(OV.FilePath(), OV.FileName() + ".tscm")


def _main_box_rows(box, d_min):
  """The m = 0 indices NoSpherA2 generates from -hkl_min_max and -dmin (generate_hkl): every h with
  d* <= 1/(0.999 d_min) one of whose images h R, or -h R, lies in the box (box None: the whole sphere); one of each
  +- pair, first non-zero index positive like calculator.table_indices."""
  uc = uctbx.unit_cell(_floats(olx.xf.au.GetCell()))
  d_keep = d_min * (1 - 1e-3)
  lim = [int(p / d_keep + 1e-4) for p in uc.parameters()[:3]]
  g = np.array(uc.reciprocal_metrical_matrix())
  hh = np.array(np.meshgrid(*[np.arange(-k, k + 1) for k in lim], indexing="ij")).reshape(3, -1).T
  ds = (hh ** 2).dot(g[:3]) + 2 * (hh[:, 0] * hh[:, 1] * g[3] + hh[:, 0] * hh[:, 2] * g[4] + hh[:, 1] * hh[:, 2] * g[5])
  hh = hh[(ds <= 1 / d_keep ** 2) & np.any(hh != 0, axis=1)]
  if box is not None:
    lo, hi = np.array(box[0]), np.array(box[1])
    inside = lambda k: np.all((k >= lo) & (k <= hi), axis=1)
    keep = np.zeros(len(hh), dtype=bool)
    for op in _basic_group().all_ops():
      k = hh.dot(np.array(op.r().as_double()).reshape(3, 3))
      keep |= inside(k) | inside(-k)
    hh = hh[keep]
  first = hh[np.arange(len(hh)), np.argmax(hh != 0, axis=1)]
  return np.unique(hh * np.sign(first)[:, None], axis=0)


def satellite_request(box=None, d_min=None, ed=False):
  """(index list, scale, table path, rows, main rows) for one NoSpherA2 call that makes both tables of a modulated
  structure: S = h + m q of every measured reflection and its images, plus the m = 0 set NoSpherA2 would generate
  from the measured box and d_min (so the ordinary table can be cut out of it); under -ED that set is the sphere to
  d_min/2 - 0.001 with no box. None when this is not a modulated structure."""
  if smod is None or not hasattr(smod, "TABLE_SCALE") or not store.get("q"):
    return None
  h, m, _, _ = _data()
  n = smod.TABLE_SCALE
  rows = smod.calculator(h, m).table_indices(_ssg())
  if d_min is not None and (box is not None or ed):
    main = _main_box_rows(None, d_min / 2.0 - 0.001) if ed else _main_box_rows(box, d_min)
    rows = np.unique(np.vstack([rows, n * main]), axis=0)
  path = os.path.join(OV.FilePath(), OV.FileName() + "_sat.hkl")
  np.savetxt(path, rows, fmt="%d")
  return path, n, _table_path(), len(rows), int(np.all(rows % n == 0, axis=1).sum())


def _table():
  """The NoSpherA2 satellite table when aspherical form factors are switched on, else None (IAM)."""
  if not OV.GetParam("snum.NoSpherA2.use_aspherical"):
    return None
  if not hasattr(smod, "form_factor_table"):
    raise RuntimeError("this cctbx bundle cannot read NoSpherA2 satellite tables; switch NoSpherA2 off for IAM")
  if not os.path.exists(_table_path()):
    raise RuntimeError("NoSpherA2 is on but %s does not exist: update the NoSpherA2 table with q set, or switch "
                       "NoSpherA2 off for IAM" % os.path.basename(_table_path()))
  return smod.form_factor_table(_table_path())


def _calc_kw():
  """(table, calculator keywords): the NoSpherA2 table when on, electron form factors for an electron wavelength;
  keywords only when needed, so X-ray work keeps running on a cctbx bundle without them."""
  tab = _table()
  kw = {} if tab is None else {"table": tab}
  if OV.IsEDData():
    if "electron" not in getattr(smod, "RADIATIONS", ()):
      raise RuntimeError("this cctbx bundle cannot refine modulated electron diffraction data")
    kw["radiation"] = "electron"
  return tab, kw


def _shelx_labels(labels, types):
  """{label: label of at most 4 characters}, unchanged where possible (SHELX .ins limit)."""
  out, used = {}, set(l for l in labels if len(l) <= 4)
  for lab, t in zip(labels, types):
    if len(lab) <= 4:
      out[lab] = lab
      continue
    k = 1
    while ("%s%d" % (t, k)) in used:
      k += 1
    out[lab] = "%s%d" % (t, k)
    used.add(out[lab])
  return out


def _load_mscif(path, rename=None):
  """A JANA msCIF with a modulated model: q, the superspace operators as listed and the displacive waves go to
  the store, the refln loop (in the CIF or <name>.fcf) becomes the hklm data. Returns (h, m, I, sigma, q)."""
  from smtbx.modulation import mscif
  rename = rename or {}
  fcf = os.path.splitext(path)[0] + ".fcf"
  xs, d = mscif.read(path, fcf if os.path.exists(fcf) else None)
  if d is None:
    raise RuntimeError("%s has no refln loop with m (and no %s)" % (path, fcf))
  store.set("ops", "|".join(op.xyz for op in xs.ssg.generators))
  sec = d.get("commensurate")
  store.set("commensurate", "%.6f %d" % sec if sec else "")
  if sec:
    print("modulation: commensurate refinement in JANA, section t0 = %.4f, N = %d: refine uses that section "
          "(crenel centres and widths stay fixed)" % sec)
  store.set("group", xs.ssg.label())
  for at in xs.atoms:
    store.set("wave." + rename.get(at.label, at.label), " ".join(["%d" % at.n_harmonics] + ["%.6f" % v for v in at.a.ravel()]
                                            + ["%.6f" % v for v in at.b.ravel()]))
    store.set("mwave." + rename.get(at.label, at.label), extras_text(at))
  extra = [f for f, on in refine_flags(xs.atoms).items() if on]
  if extra:
    print("modulation: the model also has %s; spy.modulation.refine refines them (spy.modulation.hold to fix one), "
          "the movie shows the displacive waves only" % ", ".join(extra))
  ok = np.isfinite(d["f_sq_meas"])
  return d["h"][ok], d["m"][ok], d["f_sq_meas"][ok], d["f_sq_sigma"][ok], xs.q


def open_mscif(path):
  """Open a JANA msCIF: Olex2's CIF reader does not take msCIF atom loops, so the average structure is written
  to <name>_avg.ins and reaped, then q, the superspace operators, the waves and the hklm data are loaded."""
  from cctbx import crystal, xray
  from cctbx.array_family import flex
  from iotbx.shelx import writer
  from smtbx.modulation import mscif
  path = os.path.abspath(path)
  fcf = os.path.splitext(path)[0] + ".fcf"
  xs, d = mscif.read(path, fcf if os.path.exists(fcf) else None)
  rename = _shelx_labels([a.label for a in xs.atoms], [a.scattering_type for a in xs.atoms])
  sc = flex.xray_scatterer()
  for at in xs.atoms:
    s = xray.scatterer(label=rename[at.label], site=tuple(at.site), u=at.u_iso, occupancy=at.occupancy,
                       scattering_type=at.scattering_type)
    if at.u_star is not None:
      s.u_star = tuple(at.u_star)
      s.flags.set_use_u_iso(False)
      s.flags.set_use_u_aniso(True)
    sc.append(s)
  structure = xray.structure(crystal_symmetry=crystal.symmetry(xs.unit_cell, space_group=xs.ssg.basic), scatterers=sc)
  ins = os.path.splitext(path)[0] + "_avg.ins"
  if os.path.exists(ins) and "average structure from msCIF" not in open(ins).readline():
    raise RuntimeError("%s exists and was not written by spy.modulation.open_mscif; not overwriting it" % ins)
  with open(ins, "w") as f:
    # the wavelength on CELL tells Olex2 (OV.IsEDData) and the modulation refinement that the data are electrons
    for line in writer.generator(structure, title="average structure from msCIF %s" % os.path.basename(path),
                                 wavelength=(d or {}).get("wavelength"), full_matrix_least_squares_cycles=0,
                                 sort_scatterers=False):
      f.write(line)
  olex.m("@reap '%s'" % ins)
  renamed = ["%s -> %s" % kv for kv in rename.items() if kv[0] != kv[1]]
  if renamed:
    print("modulation: labels shortened for SHELX: " + ", ".join(renamed))
  load(path, rename=rename)


def load(path, qx=None, qy=None, qz=None, rename=None):
  """Read hklm data (or a JANA msCIF with its model), store q and make the .hklm the HKL source: Olex2 reads
  .hklm natively (main reflections for every 3D tool, satellites kept aside, see olx.HKLM())."""
  path = os.path.abspath(path)
  text = open(path, errors="replace").read(200000) if path.lower().endswith(".cif") else ""
  hklm = path
  if "_atom_site_label" in text and "_cell_wave_vector" in text:
    store.set("ops", "")
    h, m, i_obs, sig, q_file = _load_mscif(path, rename)
    hklm = os.path.join(OV.FilePath(), OV.FileName() + ".hklm")
    _write_hklm(hklm, h, m, i_obs, sig, path)
  else:
    store.set("ops", "")
    store.set("commensurate", "")     # plain hklm data: the model is incommensurate unless an msCIF says so
    h, m, i_obs, sig, q_file = read_hklm(path)
    if not path.lower().endswith(".hklm"):
      # Olex2 recognises the four-index format by the extension
      hklm = os.path.join(OV.FilePath(), OV.FileName() + ".hklm")
      _write_hklm(hklm, h, m, i_obs, sig, path)
  if qx is not None:
    q = np.array([float(qx), float(qy), float(qz)])
  elif q_file is not None:
    q = q_file
  else:
    raise RuntimeError("give q: spy.modulation.load(file, qx, qy, qz)")
  store.set("q", " ".join("%.6f" % v for v in q))
  store.set("hklm", hklm)
  src = hklm
  if not native_hklm():
    src = os.path.join(OV.FilePath(), OV.FileName() + "_m0.hkl")
    hklm_util.write_main_hkl(hklm, src)
    print("modulation: this Olex2 build cannot read .hklm, the HKL source is the main reflections in %s" % src)
  OV.HKLSrc(src)
  counts = ", ".join("|m|=%d: %d" % (k, np.sum(np.abs(m) == k)) for k in sorted(set(np.abs(m))))
  print("modulation: %d reflections (%s), q = (%s); HKL source %s"
        % (len(m), counts, " ".join("%.4f" % v for v in q), src))
  _refresh()


def native_hklm():
  """True when this Olex2 reads .hklm itself (xlib from 21 Oct 2026, olx.HKLM exists). An older build must never see
  one as HKL source: HKLSrc() renames a file it does not recognise to .hkl.fcf and THklFile reads a 4I4,2F8 line as
  free-format h k l I sigma batch."""
  return hasattr(olx, "HKLM")


def set_q(qx=None, qy=None, qz=None):
  """q for the current .hklm HKL source, e.g. after solving straight from it; asked for when not given."""
  if qx is None:
    txt = OV.GetUserInput(1, "Modulation wave vector q (three numbers, reciprocal cell units)", store.get("q") or "")
    if not txt:
      return
    qx, qy, qz = _floats(txt)[:3]
  store.set("q", " ".join("%.6f" % float(v) for v in (qx, qy, qz)))
  src = olx.HKLSrc()
  if src.lower().endswith(".hklm"):
    store.set("hklm", src)
  print("modulation: q = (%s)" % store.get("q"))
  _refresh()


_stats_cache = {}


def satellite_stats():
  """smtbx reflection_statistics of the .hklm source per |m| and for all satellites ('sat') under the current
  superspace group, cached on file, q, group and cell; None without an .hklm source or q."""
  src = store.get("hklm") or olx.HKLSrc()
  if smod is None or not src or not src.lower().endswith(".hklm") or not os.path.exists(src) or not store.get("q"):
    return None
  key = (_file_key(src), store.get("q"), store.get("taus"), store.get("ops"), olx.xf.au.GetCell(),
         olx.xf.au.GetCellSymm("hall"))
  if _stats_cache.get("key") != key:
    try:
      h, m, i_obs, sig = hklm_util.read_hklm(src)
      value = smod.reflection_statistics(_ssg(), uctbx.unit_cell(_floats(olx.xf.au.GetCell())), h, m, i_obs, sig)
    except smod.IncompatibleQ as e:
      print("modulation: no satellite statistics - %s" % e)
      value = None
    _stats_cache.update(key=key, value=value)
  return _stats_cache["value"]


def stats():
  """Print I/sigma, R_int, completeness and d_min for the main reflections and each satellite order."""
  st = satellite_stats()
  if not st:
    print("modulation: needs an .hklm HKL source and q")
    return
  print("modulation: reflection statistics (superspace point group + Friedel; completeness within each order's d_min)")
  print("   order   measured  unique   I/sigma   R_int   complete   d_min")
  for k in [k for k in st if k != "sat"] + (["sat"] if "sat" in st else []):
    s = st[k]
    name = "m=0" if k == 0 else ("all sat" if k == "sat" else "|m|=%d" % k)
    print("  %-8s %8d %7d %9.1f %7s %9s %7.3f" % (
      name, s["measured"], s["unique"], s["i_over_sigma"], "-" if s["r_int"] is None else "%.2f%%" % (100 * s["r_int"]),
      "-" if s["completeness"] is None else "%.1f%%" % (100 * s["completeness"]), s["d_min"]))
  return st


def _basic_group():
  return sgtbx.space_group(olx.xf.au.GetCellSymm("hall"))


def _taus():
  s = store.get("taus") or ""
  return {k: float(v) for k, v in (it.split("=") for it in s.split(";") if "=" in it)}


def _ssg():
  ops = store.get("ops")
  if ops:
    return smod.superspace_group.from_ops(ops.split("|"), _q())
  return smod.superspace_group(_basic_group(), _q(), _taus())


def candidates(apply=True):
  """Rank the superspace groups the current space group allows with q by satellite absences; store the best."""
  q = _q()
  sg = _basic_group()
  path = store.get("hklm")
  key = (olx.xf.au.GetCellSymm("hall"), tuple(q), _file_key(path) if path and os.path.exists(path) else path,
         (0.0, 0.5))
  if _ranking_cache.get("key") != key:
    try:
      cands = smod.candidate_superspace_groups(sg, q)
    except smod.IncompatibleQ as e:
      sub = smod.compatible_subgroup(sg, q)
      print("modulation: %s\n  the largest subgroup compatible with q is %s; change the space group to it"
            % (e, sub.info().symbol_and_number()))
      return
    h, m, i_obs, sig = _data()
    _ranking_cache.update(key=key, value=smod.rank_by_absences(cands, h, m, i_obs, sig))
  del _last_ranking[:]
  _last_ranking.extend(_ranking_cache["value"])
  print("modulation: superspace groups of %s with q, best first" % sg.info().symbol_and_number())
  print("   #  violations  predicted absences  group")
  for k, (v, n, g) in enumerate(_last_ranking):
    print("  %2d  %10d  %18d  %s" % (k, v, n, g.label()))
  if apply in (True, "True", "true"):
    choose(0)


def choose(n=0):
  g = _last_ranking[int(n)][2]
  store.set("ops", "")
  store.set("taus", ";".join("%s=%.6f" % (op.xyz, op.tau) for op in g.generators))
  store.set("group", g.label())
  print("modulation: using %s" % g.label())
  _refresh()


def _u_star(i, uc):
  """U* of an anisotropic atom, None when isotropic. Olex2 holds Cartesian U in SHELX order (11 22 33 23 13 12),
  in cctbx's Cartesian frame (as my_refine_util.shelx_adp_converter reads it)."""
  q = _floats(olx.xf.au.GetAtomU(i))
  if len(q) != 6:
    return None
  return np.array(adptbx.u_cart_as_u_star(uc, (q[0], q[1], q[2], q[5], q[4], q[3])))


def _atoms(uc):
  """AU indices and smtbx atoms of the current model with their stored waves (Q peaks and deleted atoms left out)."""
  out = []
  for i in range(int(olx.xf.au.GetAtomCount())):
    if olx.xf.au.IsAtomDeleted(i) == "true" or olx.xf.au.GetAtomType(i) == "Q":
      continue
    label = olx.xf.au.GetAtomName(i)
    a = b = None
    nh = 1
    w = store.get("wave." + label)
    if w:
      v = _floats(w)
      nh = int(v[0])
      a, b = np.array(v[1:1 + 3 * nh]), np.array(v[1 + 3 * nh:1 + 6 * nh])
    at = smod.modulated_atom(label, olx.xf.au.GetAtomType(i), _floats(olx.xf.au.GetAtomCrd(i)),
                             float(olx.xf.au.GetAtomUiso(i)), float(olx.xf.au.GetAtomOccu(i)),
                             nh, a, b, u_star=_u_star(i, uc))
    apply_extras(at, store.get("mwave." + label))
    at.part = int(olx.xf.au.GetAtomPart(i))   # picks between scatterer ids on one site in a NoSpherA2 table
    out.append((i, at))
  return out


def _structure(harmonics=None):
  uc = uctbx.unit_cell(_floats(olx.xf.au.GetCell()))
  ids_atoms = _atoms(uc)
  if harmonics:
    for _, at in ids_atoms:
      nh = int(harmonics)
      if at.n_harmonics != nh:
        a, b = np.zeros((nh, 3)), np.zeros((nh, 3))
        k = min(nh, at.n_harmonics)
        a[:k], b[:k] = at.a[:k], at.b[:k]
        at.a, at.b = a, b
  scale = float(store.get("scale") or 1.0)
  return [i for i, _ in ids_atoms], smod.modulated_structure(uc, _ssg(), [a for _, a in ids_atoms], scale)


class _Average(object):
  """olex2.refine's parametrisation of the 3D model (AFIX, EXYZ/EADP, rigid groups, fixed parameters) and its
  restraints, for smod.refine(average=...). Riding atoms (AFIX m > 0) also ride on their pivot's waves."""

  def __init__(self, ids, xs):
    from refinement import FullMatrixRefine
    self.fmr = FullMatrixRefine()
    self.rep = self.fmr.run(reparametrisation_only=True)
    if self.rep is None:
      raise RuntimeError("olex2.refine could not set up the model")
    self.rm = self.fmr.restraints_manager()
    self.xs = xs
    sc_of = {aid: k for k, aid in enumerate(self.fmr.olx_atoms.atom_ids)}
    self.sc = [sc_of[i] for i in ids]
    self.shift(np.zeros(self.rep.n_independents))   # riding atoms where the constraints put them
    ours = {aid: k for k, aid in enumerate(ids)}
    self.follow = {}
    uc = xs.unit_cell
    for m, n, pivot, dependent, _, _ in self.fmr.olx_atoms.afix_iterator():
      if m == 0:  # ponytail: rigid groups keep their own waves; one shared wave set when it matters
        continue
      kp = ours.get(self.fmr.olx_atoms.atom_ids[pivot])
      for dep in dependent:
        k = ours.get(self.fmr.olx_atoms.atom_ids[dep])
        if k is None or kp is None:
          continue
        d = xs.atoms[k].site - xs.atoms[kp].site
        d -= np.round(d)
        if uc.length(tuple(d)) < 1.6:   # else the pivot is a symmetry image: the wave stays free
          self.follow[k] = (kp, float(xs.q.dot(d)))

  def _jt(self):
    jt = self.rep.jacobian_transpose_matching(self.rep.mapping_to_grad_fc_all)
    return jt, jt.as_dense_matrix().as_numpy_array().T   # (n_grad_fc, n_independent)

  def jacobian(self):
    _, j = self._jt()
    pm = self.rep.parameter_map()
    rows = []
    for k, at in zip(self.sc, self.xs.atoms):
      e = pm[k]
      for start, n in ((e.site, 3), (e.u_iso, 1) if at.u_star is None else (e.u_aniso, 6)):
        rows.extend([j[start + i] if start >= 0 else np.zeros(j.shape[1]) for i in range(n)])
    return np.array(rows)

  def shift(self, x):
    from scitbx.array_family import flex
    self.rep.apply_shifts(flex.double(list(np.asarray(x, dtype=float))))
    self.rep.linearise()
    self.rep.store()
    scs = self.rep.structure.scatterers()
    for k, at in zip(self.sc, self.xs.atoms):
      at.site = np.array(scs[k].site)
      if at.u_star is None:
        at.u_iso = scs[k].u_iso
      else:
        at.u_star = np.array(scs[k].u_star)

  def restraints(self):
    le = self.rm.build_linearised_eqns(self.rep.structure, self.rep.parameter_map())
    if le.n_restraints() == 0:
      return None
    jt, _ = self._jt()
    design = (le.design_matrix * jt.transpose()).as_dense_matrix().as_numpy_array()
    return design, le.deltas.as_numpy_array(), le.weights.as_numpy_array()


def refine(cycles=10, harmonics=1, n_x4="auto"):
  """Least squares on F^2 of all hklm data: average sites, Uiso/Uaniso, displacive waves and scale, under the
  superspace site symmetry; and whatever occupancy/ADP waves, crenels, Legendre and x-harmonic terms the model
  carries (from an msCIF, kept in the store), unless held (spy.modulation.hold). The constraints and restraints of
  the 3D model (as olex2.refine sets them up) hold; riding atoms take their pivot's waves.

  n_x4: x4 nodes per atom, or "auto" (smtbx.modulation.auto_n_x4; the default).

  shortcut: no merging or extinction.
  """
  if str(n_x4) != "auto":
    n_x4 = int(n_x4)
  elif not hasattr(smod, "auto_n_x4"):
    n_x4 = 32     # a cctbx bundle from before n_x4 = "auto"
  h, m, i_obs, sig = _data()
  ids, xs = _structure(harmonics)
  tab, kw = _calc_kw()
  try:
    avg = _Average(ids, xs)
  except Exception as e:
    avg = None
    print("modulation: refining without the 3D constraints and restraints (%s)" % e)
  if store.get("scale") is None:
    _, fc, _ = smod.calculator(h[m == 0], m[m == 0], n_x4, **kw).compute(xs)
    xs.scale = float(np.sum(i_obs[m == 0] * fc) / max(np.sum(fc * fc), 1e-30))
  print("modulation: refining %d atoms, %d harmonic(s), %d reflections in %s, form factors %s%s"
        % (len(ids), int(harmonics), len(m), xs.ssg.label(), "IAM" if tab is None else os.path.basename(tab.path),
           " (electrons, kinematical)" if "radiation" in kw else ""))
  flags = refine_flags(xs.atoms, _held())
  sec = _commensurate()
  if sec is not None:
    if hasattr(smod, "commensurate_section"):
      kw["commensurate"] = sec
      flags["crenel"] = False     # a finite sum has no gradient with respect to the crenel
    else:
      print("modulation: this cctbx bundle has no commensurate sections; refining the incommensurate model")
  on = [f for f, v in flags.items() if v]
  if on:
    print("modulation: also refining %s" % ", ".join(on))
  hist = smod.refine(xs, h, m, i_obs, sig, flags=flags, cycles=int(cycles), n_x4=n_x4, average=avg, **kw)
  for i, at in zip(ids, xs.atoms):
    olx.xf.au.SetAtomCrd(i, *at.site)
    if at.u_star is None:
      olx.xf.au.SetAtomU(i, at.u_iso)
    else:
      u = adptbx.u_star_as_u_cart(xs.unit_cell, tuple(at.u_star))
      olx.xf.au.SetAtomU(i, u[0], u[1], u[2], u[5], u[4], u[3])
    store.set("wave." + at.label, " ".join(["%d" % at.n_harmonics] + ["%.6f" % v for v in at.a.ravel()]
                                            + ["%.6f" % v for v in at.b.ravel()]))
    if extras_text(at) or store.get("mwave." + at.label):
      store.set("mwave." + at.label, extras_text(at))
  store.set("scale", "%.8g" % xs.scale)
  r = hist[-1]["R1"]
  store.set("r1", " ".join("%s:%.4f" % (k, v) for k, v in r.items()))
  olx.xf.EndUpdate()
  _refresh()
  return hist


def write_mscif(path=""):
  """The current model as a JANA-style msCIF (smtbx.modulation.mscif.write): cell, q, the superspace group,
  atoms with their waves, crenels, Legendre and x-harmonic terms, and the hklm data with F^2calc (current scale,
  form factors as refine uses them). Default <name>_modulated.cif next to the structure."""
  from smtbx.modulation import mscif
  h, m, i_obs, sig = _data()
  _, xs = _structure()
  tab, kw = _calc_kw()
  path = path or os.path.join(OV.FilePath(), OV.FileName() + "_modulated.cif")
  mscif.write(xs, path, h, m, f_sq_meas=i_obs, f_sq_sigma=sig, name=OV.FileName() or "olex2", table=tab,
              radiation=kw.get("radiation", "xray"))
  print("modulation: wrote %s (%d atoms, %d reflections)" % (path, len(xs.atoms), len(m)))
  return path


def _supercell_positions(xs, t, amplify, cells):
  """Cartesian positions and types of every atom image in the supercell at section t (own superspace argument)."""
  pos, types = [], []
  q = xs.q
  lat = np.array(list(np.ndindex(*cells)), dtype=float)
  for op in xs.ssg.ops:
    for at in xs.atoms:
      xb = op.r.dot(at.site) + op.t
      xbl = xb - np.floor(xb) + lat
      x4 = op.eps * (xbl.dot(q) + t - op.m.dot(at.site) - op.tau)
      pos.append(xbl + amplify * at.displacement(x4).dot(op.r.T))
      types += [at.scattering_type] * len(lat)
  orth = np.array(xs.unit_cell.orthogonalization_matrix()).reshape(3, 3)
  return np.vstack(pos).dot(orth.T), types


_colours = {"C": (90, 90, 90), "H": (230, 230, 230), "O": (220, 30, 30), "N": (40, 70, 230), "S": (230, 200, 40),
            "Cl": (40, 200, 40), "F": (120, 220, 120), "P": (250, 130, 0), "Br": (150, 40, 30)}


def movie(path="", frames=24, amplify=10, size=640, ms=80):
  """GIF of the modulation: a supercell spanning about one wavelength along q, viewed down the cell axis q
  leaves (nearly) unchanged; each symmetry copy moves on its own section, displacements x amplify."""
  from PIL import Image, ImageDraw
  from cctbx.eltbx import covalent_radii
  _, xs = _structure()
  q = np.abs(xs.q)
  view = int(np.argmin(q))
  cells = [1 if k == view else (2 if q[k] < 1e-6 else int(min(8, math.ceil(1.0 / q[k])))) for k in range(3)]
  base, types = _supercell_positions(xs, 0.0, 0.0, cells)
  rad = np.array([covalent_radii.table(t).radius() for t in types])
  bonds = []
  if len(base) <= 4000:
    d = np.linalg.norm(base[:, None, :] - base[None, :, :], axis=2)
    ii, jj = np.where(np.triu(d < 1.15 * (rad[:, None] + rad[None, :]), 1) & (d > 0.1))
    bonds = list(zip(ii, jj))
  axes = [k for k in range(3) if k != view]
  orth = np.array(xs.unit_cell.orthogonalization_matrix()).reshape(3, 3)
  u = orth[:, axes[0]] / np.linalg.norm(orth[:, axes[0]])
  w = np.cross(u, orth[:, view]); w /= np.linalg.norm(w)
  depth = np.cross(u, w)
  view_m = np.array([u, w, depth]).T
  pb = base.dot(view_m)
  lo, hi = pb[:, :2].min(axis=0) - 2, pb[:, :2].max(axis=0) + 2
  sc = (size - 20) / max(hi - lo)
  imgs = []
  for f in range(int(frames)):
    t = f / float(frames)
    p, _ = _supercell_positions(xs, t, float(amplify), cells)
    pp = p.dot(view_m)
    xy = (pp[:, :2] - lo) * sc + 10 + (size - 20 - (hi - lo) * sc) / 2   # centred
    xy[:, 1] = size - xy[:, 1]
    img = Image.new("RGB", (size, size), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    for i, j in bonds:
      dr.line([tuple(xy[i]), tuple(xy[j])], fill=(150, 150, 150), width=2)
    for k in np.argsort(pp[:, 2]):
      r = max(2.0, 0.35 * rad[k] * sc)
      c = _colours.get(types[k], (200, 120, 200))
      dr.ellipse([xy[k][0] - r, xy[k][1] - r, xy[k][0] + r, xy[k][1] + r], fill=c, outline=(0, 0, 0))
    dr.text((10, 10), "t = %.2f   displacements x%g   %s" % (t, float(amplify), xs.ssg.label()), fill=(0, 0, 0))
    imgs.append(img.convert("P", palette=Image.ADAPTIVE))
  path = path or os.path.join(OV.FilePath(), OV.FileName() + "_modulation.gif")
  imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=int(ms), loop=0)
  print("modulation: %d frames, %s cells, -> %s" % (len(imgs), "x".join(map(str, cells)), path))
  return path


def de_wolff(label="", axis="", width=1.0, kind="obs", follow=False, path="", show=True):
  """De Wolff section x_axis - x4 of the superspace Fourier map through an atom (default: the atom with the
  largest displacement, along its largest component), as a PNG; kind obs | calc | diff; follow=True moves the
  other two coordinates with the atom. The cyan line is the model's string."""
  from PIL import Image, ImageDraw
  h, m, i_obs, sig = _data()
  _, xs = _structure()
  _, kw = _calc_kw()
  _, fc, _ = smod.calculator(h, m, **kw).compute(xs)
  xs.scale = float(np.sum(i_obs * fc) / max(np.sum(fc * fc), 1e-30))
  abc = np.array(xs.unit_cell.parameters()[:3])
  amp = {at.label: np.sqrt((at.a ** 2 + at.b ** 2).sum(axis=0)) * abc for at in xs.atoms}
  heavy = [at.label for at in xs.atoms if at.scattering_type not in ("H", "D")] or list(amp)
  label = label or max(heavy, key=lambda k: amp[k].max())
  ax = "xyz".index(axis) if axis else int(np.argmax(amp[label]))
  follow = follow in (True, "True", "true", "1")
  s, x4, rho, curve = smod.de_wolff_section(xs, h, m, i_obs, label, ax, float(width), kind=kind, follow=follow, **kw)
  lo, hi = (np.percentile(rho, 1), rho.max()) if kind != "diff" else (-np.abs(rho).max(), np.abs(rho).max())
  v = np.clip((rho - lo) / max(hi - lo, 1e-30), 0, 1)
  if kind == "diff":   # blue - white - red
    rgb = np.stack([255 * np.clip(2 * v, 0, 1), 255 * (1 - np.abs(2 * v - 1)), 255 * np.clip(2 - 2 * v, 0, 1)], -1)
  else:                # black - red - yellow - white
    rgb = np.stack([255 * np.clip(1.5 * v, 0, 1), 255 * np.clip(1.5 * v - 0.5, 0, 1), 255 * np.clip(3 * v - 2, 0, 1)], -1)
  img = Image.fromarray(rgb[::-1].astype(np.uint8)).resize((5 * len(s), 5 * len(x4)), Image.BILINEAR)
  dr = ImageDraw.Draw(img)
  px = (curve - s[0]) / (s[-1] - s[0]) * (img.size[0] - 1)
  py = img.size[1] - 1 - np.arange(len(x4)) * img.size[1] / float(len(x4))
  dr.line(list(zip(px, py)), fill=(0, 255, 255), width=2)
  dr.text((4, 4), "%s  %s (+-%g A) vs x4  %s%s  rho %.2f..%.2f e/A^3" % (
    label, "xyz"[ax], float(width), kind, ", following" if follow else "", rho.min(), rho.max()), fill=(255, 255, 255))
  path = path or os.path.join(OV.FilePath(), "%s_deWolff_%s_%s_%s.png" % (OV.FileName(), label, "xyz"[ax], kind))
  img.save(path)
  print("modulation: de Wolff section %s %s-x4 (%s) -> %s" % (label, "xyz"[ax], kind, path))
  if show in (True, "True", "true"):
    try:
      olx.Shell(path)
    except Exception:
      pass
  return path


def wiggle(frames=24, amplify=10, loops=3, delay=60):
  """Animate the asymmetric unit in the viewer through one period of t; the model is put back afterwards.

  Olex2 regrows symmetry copies rigidly from the asymmetric unit, so only the AU atoms move on their own waves
  here; spy.modulation.movie() draws every copy correctly."""
  ids, xs = _structure()
  orig = [(i, olx.xf.au.GetAtomCrd(i)) for i in ids]
  _stop[0] = False
  try:
    for _ in range(int(loops)):
      for f in range(int(frames)):
        if _stop[0]:
          return
        t = f / float(frames)
        for i, p in zip(ids, xs.positions_at(t, float(amplify))):
          olx.xf.au.SetAtomCrd(i, *p)
        olx.xf.EndUpdate()
        OV.Refresh()
        try:
          olx.Wait(int(delay))
        except Exception:
          pass
  finally:
    for i, crd in orig:
      olx.xf.au.SetAtomCrd(i, *_floats(crd))
    olx.xf.EndUpdate()
    OV.Refresh()


def stop():
  _stop[0] = True


def panel(html=True):
  """The modulation block under the HOS: reflections per order, q, the superspace group, R1 per |m| and the
  actions, in short lines of its own full-width table so it never widens the panel. Never raises: it is evaluated on
  every redraw of snum-info.htm."""
  try:
    lines = _panel()
  except Exception:
    return ""
  if not lines:
    return ""
  return ("<table border='0' width='100%%' cellpadding='0' cellspacing='2' bgcolor='%s'><tr><td align='left'>%s"
          "</td></tr></table>" % (OV.GetVar('HtmlTableBgColour', ''), "<br>".join(lines)))


def _counts():
  """'N main + M satellites (|m| = 1)' from olx.HKLM(), or '' without an .hklm source."""
  try:
    n = olx.HKLM()
  except Exception:
    n = ""
  if not n:
    return ""
  main, sat, mmax = n.split(",")
  orders = "|m| = 1" if mmax == "1" else "1 &lt;= |m| &lt;= %s" % mmax
  return "%s main + %s satellites (%s)" % (main, sat, orders)


def _panel():
  q = store.get("q")
  green = OV.GetParam('gui.green_text').hexadecimal
  counts = _counts()
  if not q:
    if not counts:
      return []
    return ["<b><font color='%s'>hklm</font></b> %s <a href='spy.modulation.set_q()'>set q</a>" % (green, counts)]
  # q on the line of the actions; clicking it asks for a new q
  lines = ["<a href='spy.modulation.set_q()'><b><font color='%s'>q [%s]</font></b></a>"
           " <a href='spy.modulation.candidates()'>SSG</a> <a href='spy.modulation.refine()'>Refine</a>"
           " <a href='spy.modulation.wiggle()'>Wiggle</a> <a href='spy.modulation.movie()'>GIF</a>"
           " <a href='spy.modulation.de_wolff()'>de Wolff</a>"
           % (green, ", ".join("%.4g" % v for v in _floats(q)))]
  info = []
  if store.get("group"):
    info.append(store.get("group").split(" q=")[-1].split(")", 1)[-1].strip())
  if counts:
    info.append(counts)
  if info:
    lines.append(" ".join(info))
  second = []
  if store.get("r1"):
    second.append("R1 " + " ".join(store.get("r1").replace("m=", "").split()[1:]))
  if OV.GetParam("snum.NoSpherA2.use_aspherical"):
    second.append("f: %s" % ("NoSpherA2" if os.path.exists(_table_path()) else "<font color='red'>no .tscm</font>"))
  if OV.IsEDData():
    second.append("ED")
  if second:
    lines.append(" ".join(second))
  return lines


def _refresh():
  try:
    olx.html.Update()
  except Exception:
    pass


def _needs_smtbx(f):
  """A clear message instead of an AttributeError on None when this Olex2's cctbx bundle predates smtbx.modulation."""
  def g(*args, **kwds):
    if smod is None:
      print("modulation: spy.modulation.%s needs smtbx.modulation (cctbx from 21 Oct 2026); this Olex2's cctbx "
            "bundle is older" % f.__name__)
      return None
    return f(*args, **kwds)
  g.__name__, g.__doc__ = f.__name__, f.__doc__
  return g


for _f in (load, open_mscif, stats, candidates, choose, refine, wiggle, movie, de_wolff, hold, write_mscif):
  olex.registerFunction(_needs_smtbx(_f), False, "modulation")
for _f in (set_q, stop, panel):
  olex.registerFunction(_f, False, "modulation")
