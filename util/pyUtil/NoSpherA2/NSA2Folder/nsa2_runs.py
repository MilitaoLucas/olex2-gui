"""
The NoSpherA2 runs of one structure, read from its olex2/NoSpherA2_history.

No Olex2 imports: everything here works on plain paths, so it can be tested
outside Olex2.

Layout (written by NoSpherA2.py, not by this tool):
  <dir>/<name>.tscb, .wfnlog, .xtb/.gbw/...   the latest run (not yet archived)
  <dir>/olex2/NoSpherA2_history/<name>_<YYYY-mm-dd_HH-MM-SS>/
                                              one earlier run each: the table,
                                              its .wfnlog and the wavefunction;
                                              the folder is named after the
                                              table's modification time
At the start of a run NoSpherA2 moves the files of the previous run from <dir>
into a history folder, so the latest run only reaches the history when the next
one starts.
"""

import datetime
import hashlib
import os
import re
import shutil

HISTORY_DIR = os.path.join("olex2", "NoSpherA2_history")
# the files NoSpherA2 archives (NoSpherA2.py, backup_endings)
BACKUP_ENDINGS = (".wfn", ".wfx", ".molden", ".gbw", ".fchk", ".owf.fchk", ".ffn",
                  ".xtb", ".tshb", ".tscb", ".tsc", ".wfnlog")
TABLE_ENDINGS = (".tshb", ".tscb", ".tsc")
WFN_ENDINGS = (".gbw", ".xtb", ".wfx", ".wfn", ".molden", ".fchk", ".owf.fchk", ".ffn")
_STAMP = "%Y-%m-%d_%H-%M-%S"
# runs further apart than this (seconds) belong to different refinements
GROUP_GAP = 60

# programs whose method and basis set mean something; the others (pTB, xTB,
# DiSCaMB, Thakkar, ELMOdb, SALTED ...) have their own fixed model, while the
# table header still records whatever the GUI had selected
_QM_PROGRAMS = ("ORCA", "pySCF", "Psi4", "Tonto", "Gaussian", "fragHAR", "Hybrid")

# banner text in a .wfnlog -> program
_BANNERS = (
  ("O   R   C   A", "ORCA"),
  ("P T B", "pTB"),
  ("x T B", "xTB"),
  ("PySCF", "pySCF"),
  ("pyscf", "pySCF"),
  ("Psi4", "Psi4"),
  ("T O N T O", "Tonto"),
  ("Tonto", "Tonto"),
  ("ELMO", "ELMOdb"),
  ("DiSCaMB", "DiSCaMB"),
  ("discamb", "DiSCaMB"),
  ("Thakkar", "Thakkar"),
  ("Gaussian", "Gaussian"),
)

_BASIS_RE = re.compile(
  r"(?i)^(ma-)?(def2-|cc-p|aug-cc-|x2c-|jorge-|sto-|ano-|sapporo|dhf-|pc-?\d|"
  r"\d-\d+\+*G)")
_METHOD_RE = re.compile(
  r"(?i)(lyp|pbe|scan|tpss|m06|wb97|b97|bp86|^u?hf$|^r?hf$|mp2|ccsd|pw91|"
  r"x3lyp|bhandh|-3c$)")


def _read_head(path, size=65536):
  try:
    with open(path, "rb") as f:
      return f.read(size).decode("latin-1")
  except (IOError, OSError):
    return ""


def read_table_header(path):
  """The NSA2_<key>: value lines of a table header as {key: value}; {} when the
  table carries none (tables made before the settings were recorded)."""
  found = {}
  for line in _read_head(path).splitlines():
    s = line.strip()
    if s.startswith("SOURCE_LABELS") or s.startswith("DATA:"):
      break
    if s.startswith("NSA2_") and ":" in s:
      k, v = s.split(":", 1)
      found[k[len("NSA2_"):].strip()] = v.strip()
  return found


def read_wfnlog(path):
  """What a .wfnlog says about its run: program, version, method, basis,
  charge, multiplicity, energy -- whatever can be found; missing keys are
  simply absent."""
  info = {}
  if not path or not os.path.exists(path):
    return info
  try:
    with open(path, "r", encoding="latin-1") as f:
      text = f.read()
  except (IOError, OSError):
    return info
  head = text[:6000]
  for banner, prog in _BANNERS:
    if banner in head:
      info["program"] = prog
      break
  m = re.search(r"Program Version\s+([\d.]+)", text)
  if m:
    info["version"] = m.group(1)
  if info.get("program") == "pTB":
    m = re.search(r"^\s*Version\s+([\d.]+)", head, re.M)
    if m:
      info["version"] = m.group(1)
  # ORCA echoes its input:  |  1> ! r2SCAN 3-21G ...
  keywords = []
  for m in re.finditer(r"^\|\s*\d+>\s*!(.*)$", text, re.M):
    keywords.extend(m.group(1).split())
  if keywords:
    basis = [k for k in keywords if _BASIS_RE.search(k) and "/" not in k]
    method = [k for k in keywords if k not in basis and _METHOD_RE.search(k)]
    if basis:
      info["basis_name"] = basis[0]
    if method:
      info["method"] = method[0]
  m = re.search(r"^\|\s*\d+>\s*charge\s+(-?\d+)", text, re.M | re.I)
  if m:
    info["charge"] = m.group(1)
  m = (re.search(r"^\|\s*\d+>\s*mult\s+(\d+)", text, re.M | re.I)
       or re.search(r"Multiplicity\s*:\s*(\d+)", text))
  if m:
    info["multiplicity"] = m.group(1)
  m = re.search(r"^\s*nopen\s+(\d+)", text, re.M)
  if m and "multiplicity" not in info:
    info["multiplicity"] = str(int(m.group(1)) + 1)
  m = None
  for m in re.finditer(r"FINAL SINGLE POINT ENERGY\s+(-?[\d.]+)", text):
    pass
  if m:
    info["energy"] = m.group(1)
  return info


def program_name(source):
  """A short program name from a header 'source'/'origin' ('ORCA 6.1' ->
  'ORCA', 'discambMATTS2021' -> 'DiSCaMB')."""
  s = str(source or "").strip()
  low = s.lower()
  for key, name in (("orca", "ORCA"), ("ptb", "pTB"), ("xtb", "xTB"),
                    ("pyscf", "pySCF"), ("psi4", "Psi4"), ("tonto", "Tonto"),
                    ("elmo", "ELMOdb"), ("discamb", "DiSCaMB"),
                    ("thakkar", "Thakkar"), ("salted", "SALTED"),
                    ("gaussian", "Gaussian"), ("fraghar", "fragHAR"),
                    ("hybrid", "Hybrid")):
    if key in low:
      return name
  return s


def uses_basis(program):
  return any(program.startswith(p) for p in _QM_PROGRAMS)


def file_sha256(path, _cache={}):
  """sha256 of a file, cached by (path, mtime, size)."""
  try:
    st = os.stat(path)
  except OSError:
    return None
  key = (os.path.normcase(os.path.abspath(path)), st.st_mtime, st.st_size)
  if key not in _cache:
    h = hashlib.sha256()
    with open(path, "rb") as f:
      for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
    _cache[key] = h.hexdigest()
  return _cache[key]


def belongs(filename, name):
  """True for the files of structure `name` that NoSpherA2 archives: <name>.ext
  and, for disorder, the per-part <name>_part<N>.ext."""
  return (filename.endswith(BACKUP_ENDINGS)
          and (filename.startswith(name + ".")
               or re.match(re.escape(name) + r"_part\d+\.", filename) is not None))


def _find(folder, name, endings):
  """<name><ending>, else the first part's <name>_part1<ending>."""
  for stem in (name, name + "_part1"):
    for e in endings:
      p = os.path.join(folder, stem + e)
      if os.path.exists(p):
        return p
  return None


def _parts(folder, name):
  pat = re.compile(re.escape(name) + r"_part(\d+)\.wfnlog$")
  return len([f for f in os.listdir(folder) if pat.match(f)])


def _make_run(folder, name, label, when):
  table = None
  for e in TABLE_ENDINGS:
    if os.path.exists(os.path.join(folder, name + e)):
      table = os.path.join(folder, name + e)
      break
  if table is None:
    return None
  log = _find(folder, name, (".wfnlog",))
  wfn = _find(folder, name, WFN_ENDINGS)
  header = read_table_header(table)
  loginfo = read_wfnlog(log)
  program = program_name(header.get("source") or header.get("origin")
                         or loginfo.get("program") or "")
  if not program and wfn:
    program = {".gbw": "ORCA", ".xtb": "pTB"}.get(os.path.splitext(wfn)[1], "")
  run = dict(label=label, folder=folder, table=table, log=log, wfn=wfn,
             time=when, header=bool(header), program=program or "?",
             version=header.get("ORCA_Version") or loginfo.get("version", ""))
  for key in ("method", "basis_name", "charge", "multiplicity"):
    # the log says what really ran; the header what the GUI had set
    run[key] = loginfo.get(key) or header.get(key, "")
  if not uses_basis(run["program"]):
    run["method"] = run["basis_name"] = ""
  run["energy"] = loginfo.get("energy", "")
  run["qmmm"] = header.get("ORCA_USE_CRYSTAL_QMMM", "") == "True"
  run["relativistic"] = header.get("Relativistic", "") == "True"
  run["solvation"] = header.get("ORCA_Solvation", "")
  # disorder: one wavefunction per part; the first part's log is read
  run["parts"] = _parts(folder, name)
  run["fp"] = _fingerprint(folder, name)
  return run


def history_root(struct_dir):
  return os.path.join(struct_dir, HISTORY_DIR)


def scan(struct_dir, name):
  """All runs of structure `name` in `struct_dir`, oldest first. The latest,
  not yet archived run (the table in `struct_dir` itself) is included, with
  live=True, unless it is a copy of one in the history (a run switched to)."""
  runs = []
  root = history_root(struct_dir)
  prefix = name + "_"
  if os.path.isdir(root):
    for d in os.listdir(root):
      if not d.startswith(prefix):
        continue
      try:
        when = datetime.datetime.strptime(d[len(prefix):], _STAMP)
      except ValueError:
        continue
      run = _make_run(os.path.join(root, d), name, d, when)
      if run:
        runs.append(run)
  runs.sort(key=lambda r: r["time"])
  # a run switched to and then archived again by NoSpherA2 under a new name
  # (its table rewritten, so a new time): the same logs, shown once
  seen, unique = set(), []
  for r in runs:
    if r["fp"] and r["fp"] in seen:
      continue
    seen.add(r["fp"])
    unique.append(r)
  runs = unique
  top = _find(struct_dir, name, TABLE_ENDINGS)
  if top is not None and copy_of(runs, struct_dir, name) is None:
    when = datetime.datetime.fromtimestamp(os.path.getmtime(top)).replace(microsecond=0)
    run = _make_run(struct_dir, name, "latest (not archived)", when)
    if run:
      run["live"] = True
      runs.append(run)
  return runs


def _fingerprint(folder, name):
  """(file, size, mtime) of the logs and wavefunctions of the run in `folder`.
  These are copied with their times kept and never rewritten -- unlike the
  table, which Olex2 relabels to the current model when it takes it up."""
  fp = []
  for f in sorted(os.listdir(folder)):
    if belongs(f, name) and not f.endswith(TABLE_ENDINGS):
      st = os.stat(os.path.join(folder, f))
      fp.append((f, st.st_size, int(st.st_mtime)))
  return tuple(fp)


def copy_of(runs, struct_dir, name):
  """Index of the history run whose files are in `struct_dir` (a run switched
  to), or None. Told by the logs and wavefunctions; by the table only when
  there are none."""
  fp = _fingerprint(struct_dir, name)
  if fp:
    for i, r in enumerate(runs):
      if not r.get("live") and r["fp"] == fp:
        return i
    return None
  table = _find(struct_dir, name, TABLE_ENDINGS)
  if not table:
    return None
  size = os.path.getsize(table)
  sha = None
  for i, r in enumerate(runs):
    if r.get("live") or os.path.getsize(r["table"]) != size:
      continue
    if sha is None:
      sha = file_sha256(table)
    if file_sha256(r["table"]) == sha:
      return i
  return None


def active_index(runs, struct_dir, name):
  """Index of the run in use: the latest (not archived) one, or the one
  switched to."""
  for i, r in enumerate(runs):
    if r.get("live"):
      return i
  return copy_of(runs, struct_dir, name)


def _signature(run):
  return (run["program"], run["method"], run["basis_name"], run["charge"],
          run["multiplicity"], run["qmmm"], run["relativistic"])


def group(runs, gap=GROUP_GAP):
  """Split runs (oldest first) into refinements: a new group starts after a
  pause longer than `gap` seconds or when the settings change."""
  groups = []
  prev = None
  for r in runs:
    if (prev is None or (r["time"] - prev["time"]).total_seconds() > gap
        or _signature(r) != _signature(prev)):
      groups.append([])
    groups[-1].append(r)
    prev = r
  return groups


def _top_files(struct_dir, name):
  return [f for f in os.listdir(struct_dir)
          if belongs(f, name) and os.path.isfile(os.path.join(struct_dir, f))]


def archive_top(struct_dir, name):
  """Clear the run in `struct_dir` into the history. A run switched to is
  already there: its copies are removed -- its table too, which Olex2 may
  have relabelled, the original staying in the history. Otherwise the files
  are moved as NoSpherA2 does at the start of a run: into <name>_<table
  mtime>. Returns the history folder, or None when there was nothing."""
  files = _top_files(struct_dir, name)
  table = _find(struct_dir, name, TABLE_ENDINGS)
  if not files or table is None:
    return None
  runs = scan(struct_dir, name)
  i = copy_of(runs, struct_dir, name)
  if i is not None:
    dest = runs[i]["folder"]
  else:
    stamp = datetime.datetime.fromtimestamp(os.path.getmtime(table)).strftime(_STAMP)
    dest = os.path.join(history_root(struct_dir), "%s_%s" % (name, stamp))
    if not os.path.isdir(dest):
      os.makedirs(dest)
  for f in files:
    src = os.path.join(struct_dir, f)
    dst = os.path.join(dest, f)
    if os.path.exists(dst) and (i is not None or os.path.getsize(dst) == os.path.getsize(src)):
      os.remove(src)
    else:
      shutil.move(src, dst)
  return dest


def switch_to(struct_dir, name, run):
  """Make `run` the current one: archive what is in `struct_dir`, then copy
  the run's files (table, .wfnlog, wavefunction) there, keeping their times so
  that NoSpherA2 archives them back into the same history folder. Returns the
  path of the table now in `struct_dir`."""
  if run.get("live"):
    return run["table"]
  archive_top(struct_dir, name)
  table = None
  for f in os.listdir(run["folder"]):
    if not belongs(f, name):
      continue
    dst = os.path.join(struct_dir, f)
    shutil.copy2(os.path.join(run["folder"], f), dst)
    if f.endswith(TABLE_ENDINGS):
      table = dst
  return table
