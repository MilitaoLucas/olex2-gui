"""Bonding analysis of the displayed molecule, values written onto the bonds.

Experimental. The block (make_BondAtlas_GUI) shows only with
user.NoSpherA2.show_BondAtlas in debug or guru mode. What it does:

  Run    in olex2/BondAtlas/<geometry hash>: takes the wavefunction next to
         the structure, or computes one with OCC (method, basis, charge and
         multiplicity of the NoSpherA2 panel) when there is none, then runs
         NoSpherA2 with the chosen analysis in the background
  Show   reads the analysis output and writes the chosen value as a loose label:
         bond orders at the bond midpoint, critical-point and ELI-D bond values
         at a small ball on the point, charges and populations at the atom
         (labels and spheres ba_*); Clear removes them

Atoms are matched to the wavefunction by position in the xyz written next
to it, which is the order every NoSpherA2 wavefunction job uses.
"""

import os
import re
import shutil
import subprocess
import sys
import threading

import olex
import olex_core
import olx
from olexFunctions import OV
from variableFunctions import nsa2_get_param, nsa2_set_param

_folder = os.path.join("olex2", "BondAtlas")
_state = {"proc": None, "thread": None, "message": "", "labels": 0, "balls": 0}
_wfn_ext = (".gbw", ".wfx", ".ffn", ".wfn", ".molden", ".xtb", ".fchk")
# combo item: NoSpherA2 runs, each (command line before the wavefunction, after it)
_analyses = {
  "Full": [(["-fba"], [])],
  "RGBI": [(["-wfn"], ["-rgbi"])],
  "QTAIM": [(["-eli_analysis"], [])],
  "NBO": [(["-nbo_native"], ["-nrt"])],
}
# RGBI needs the density matrix over the contracted basis, which the fchk reader does not keep (OCC writes
# only fchk): there Full is QTAIM/ELI-D and NBO/NRT, and RGBI refuses
_fchk_full = _analyses["QTAIM"] + _analyses["NBO"]


def show_BondAtlas():
  from utilities import dev_features
  return OV.GetParam("user.NoSpherA2.show_BondAtlas") == True and dev_features()


def _param(key, default=None):
  v = nsa2_get_param("BondAtlas.%s" % key)
  return default if v in (None, "") else v


def _job_dir():
  from crystal_energies import _structure, _structure_hash
  return os.path.join(OV.FilePath(), _folder, _structure_hash(*_structure()).hexdigest()[:16])


def _name():
  return olx.FileName()


def _wfn(folder, copy=False):
  """The wavefunction of this geometry: one already in the job folder (OCC or copied), else the one next to the
  structure, copied in with copy so NoSpherA2 writes its section logs into the job folder."""
  for fn in [os.path.join(folder, _name() + ".owf.fchk")] + [os.path.join(folder, OV.ModelSrc() + e) for e in _wfn_ext]:
    if os.path.isfile(fn):
      return fn
  for e in _wfn_ext:
    fn = os.path.join(OV.FilePath(), OV.ModelSrc() + e)
    if os.path.isfile(fn):
      if not copy:
        return fn
      target = os.path.join(folder, os.path.basename(fn))
      shutil.copy2(fn, target)
      return target
  return None


def _xyz(folder):
  """Element and Cartesian position of every wavefunction atom, in wavefunction order."""
  atoms = []
  with open(os.path.join(folder, _name() + ".xyz")) as f:
    n = int(f.readline())
    f.readline()
    for _ in range(n):
      t = f.readline().split()
      atoms.append((t[0], tuple(float(x) for x in t[1:4])))
  return atoms


def _exe():
  return OV.GetVar("NoSpherA2")


class _Runner(threading.Thread):
  """OCC first when the toml is given, then the analysis; one console log for both."""
  def __init__(self, toml, runs, folder):
    threading.Thread.__init__(self)
    self.toml = toml
    self.runs = runs
    self.folder = folder

  def _run(self, args, log):
    _state["proc"] = subprocess.Popen(args, cwd=self.folder, stdout=log, stderr=subprocess.STDOUT,
                                      startupinfo=self.startinfo, creationflags=self.flags, env=self.env)
    return _state["proc"].wait()

  def run(self):
    olex_core.IncRunningThreadsCount()
    try:
      self.env = dict(os.environ)
      self.env["OCC_DATA_PATH"] = os.path.join(os.path.dirname(_exe()), "occ", "share")
      self.startinfo = None
      self.flags = 0
      if sys.platform[:3] == "win":
        self.startinfo = subprocess.STARTUPINFO()
        self.startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.startinfo.wShowWindow = 0
        self.flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
      cpus = ["-cpus", str(nsa2_get_param("ncpus"))]
      with open(os.path.join(self.folder, "BondAtlas_console.log"), "w") as log:
        rc = 0
        if self.toml:
          _state["message"] = "running OCC"
          rc = self._run([_exe()] + cpus + ["-occ", self.toml], log)
          wfn = os.path.splitext(self.toml)[0] + ".owf.fchk"
          if rc == 0 and not os.path.isfile(wfn):
            rc = -1
          self.runs = [[a if a != "<wfn>" else wfn for a in args] for args in self.runs]
        for args in self.runs:
          if rc != 0:
            break
          _state["message"] = "running " + args[0].lstrip("-")
          rc = self._run([_exe()] + cpus + args, log)
      _state["message"] = "" if rc == 0 else "NoSpherA2 exited with %d, see BondAtlas_console.log" % rc
    except Exception:
      sys.stderr.formatExceptionInfo()
      _state["message"] = "failed to start NoSpherA2"
    finally:
      _state["proc"] = None
      olex_core.DecRunningThreadsCount()
      olx.Schedule(1, "spy.NoSpherA2.ba_finished()")


def ba_run():
  t = _state["thread"]
  if t is not None and t.is_alive():
    print("BondAtlas: a job is still running")
    return
  if not _exe():
    print("BondAtlas: NoSpherA2 executable is not configured")
    return
  from Wfn_Job import wfn_Job
  folder = _job_dir()
  os.makedirs(folder, exist_ok=True)
  job = wfn_Job(None, _name(), folder, "OCC")
  wfn = _wfn(folder, copy=True)
  toml = None
  if wfn is None:
    job.write_occ_input(True)  # xyz and toml from the panel's method, basis, charge, multiplicity
    toml = job.input_fn
    wfn = "<wfn>"
  else:
    job.write_xyz_file(normalize_h_isotopes=True)
  analysis = _param("analysis", "Full")
  runs = _analyses[analysis]
  if toml or wfn.endswith(".fchk"):
    if analysis == "RGBI":
      _state["message"] = "RGBI needs a .gbw or .molden wavefunction, OCC writes only fchk"
      print("BondAtlas: " + _state["message"])
      return
    if analysis == "Full":
      runs = _fchk_full
  ba_clear()
  _state["message"] = ""
  _state["thread"] = _Runner(toml, [before + [wfn] + after for before, after in runs], folder)
  _state["thread"].start()
  print("BondAtlas: %s analysis of %s in %s" % (analysis,
        "a new OCC wavefunction" if toml else os.path.basename(wfn), folder))


def ba_stop():
  p = _state["proc"]
  if p is None:
    print("BondAtlas: nothing is running")
    return
  p.kill()
  _state["message"] = "stopped"


def ba_status():
  t = _state["thread"]
  if t is not None and t.is_alive():
    olx.Schedule(3, "html.Update")  # the panel re-reads this status while the exe runs
    return _state["message"] or "running"
  if _state["message"]:
    return _state["message"]
  try:
    folder = _job_dir()
  except Exception:
    return ""
  if _wfn(folder) is None:
    return "no wavefunction: Run computes one with OCC first"
  n = len(_values(folder))
  return "%d properties available" % n if n else "not analysed"


def ba_finished():
  _state["thread"] = None
  if not _state["message"]:
    props = ba_properties()
    if props and _param("property") not in props.split(";"):
      nsa2_set_param("BondAtlas.property", props.split(";")[0])
    ba_show()
  olex.m("html.Update")


def ba_properties():
  try:
    return ";".join(sorted(_values(_job_dir())))
  except Exception:
    return ""


def ba_show():
  ba_clear()
  folder = _job_dir()
  prop = _param("property")
  values = _values(folder).get(prop)
  if not values:
    print("BondAtlas: no %s values in %s" % (prop, folder))
    return
  xyz = _xyz(folder)
  fmt = "%%.%df" % int(_param("decimals", 2))
  centre = [sum(p[k] for _, p in xyz) / len(xyz) for k in range(3)]
  for key, (v, at, ball) in values.items():
    if at is None and isinstance(key[0], str):
      at = [float(x) for x in olx.Crd(key[0]).split()]
    elif at is None and len(key) == 1:
      at = xyz[key[0]][1]
    elif at is None:
      at = [(a + b) / 2 for a, b in zip(xyz[key[0]][1], xyz[key[1]][1])]
    if ball:
      name = "ba_s%d" % _state["balls"]
      olex.m("AddObject sphere %s 0 0.13 %f %f %f" % ((name,) + tuple(at)))  # wider than a bond stick
      c = _balls[ball]
      olx.SetMaterial(name + ".Object", "1109;%s,1;%s,1;0.8,0.8,0.8,1;32" % (c, c))
      _state["balls"] += 1
      # the label off the ball, away from the molecule's centre
      d = [a - m for a, m in zip(at, centre)]
      r = max(sum(x * x for x in d) ** 0.5, 1e-6)
      at = [a + 0.25 * x / r for a, x in zip(at, d)]
    olx.AddLabel("ba_%d" % _state["labels"], *at, fmt % v)
    olx.SetMaterial("ba_%d.Text" % _state["labels"], "2309;0.75,0,0.1,1;0.75,0,0.1,1")  # crimson, apart from atom labels
    _state["labels"] += 1
  print("BondAtlas: %s, %d values: %s" % (prop, len(values), _describe(prop)))
  olex.m('legend true "%s: %s"' % (prop, _describe(prop)))  # caption under the element keys


def ba_describe():
  p = _param("property")
  return _describe(p) if p else ""


def ba_clear():
  if _state["labels"] or _state["balls"]:
    olex.m("kill ba_*")
    olex.m('legend false ""')
  _state["labels"] = _state["balls"] = 0


# --- output parsers: {property: {key: (value, position or None, ball or None)}} ---
# key: (i, j) a bond, i < j; (i,) an atom; (label,) an Olex2 atom label; ("ring"|"cage", n) a critical point.
# Atom indices are 0-based in wavefunction order: RGBI, QTAIM and ELI-D logs number from 0, the NBO json from 1.
# Positions are Cartesian Angstrom; the logs give bohr in the frame of the xyz, which is Olex2's.

_bohr = 0.529177210544
_rgbi_row = re.compile(r"^\s*(\d+)\s+-\s*(\d+)\s+[A-Z][a-z]?\s+-\s*[A-Z][a-z]?((?:\s+-?\d+\.\d+){9})\s*$")
_cp_head = re.compile(r"^\s+CP\s+(\d+)\s+\[(\w+)\s*\]\s+(NOT )?converged\s*(?:(\S+?)-(\S+) bond)?")
_cp_value = re.compile(r"^\s+(Position|Rho|DelSqRho|Bond Ellipticity)\s*:\s+(.+)$")
_di_row = re.compile(r"^  (\S+)\s+(\S+)\s+(\d+\.\d{4})$")
# basin tables: QTAIM electrons charge volume maximum x y z, ELI-D electrons volume maximum x y z
_basin_row = re.compile(r"^\s+\d+\s+(\S+)(?: (\w+))?((?:\s+-?\d+\.\d+){6,7})\s*$")
_float = re.compile(r"^-?\d+\.\d+$")
_balls = {"bond": "0.1,0.6,0.2", "ring": "0.85,0.1,0.1", "cage": "0.1,0.3,0.9", "eli": "0.85,0.65,0.1"}
_desc = {
  "RGBI bond index": "Roby-Gould bond index, at the bond midpoint",
  "RGBI covalent": "Roby-Gould covalent bond index, at the bond midpoint",
  "RGBI ionic": "Roby-Gould ionic bond index, at the bond midpoint",
  "QTAIM rho CP": "density at the critical points in e/bohr^3; green bond, red ring, blue cage",
  "QTAIM Laplacian CP": "Laplacian of the density at the critical points in e/bohr^5; green bond, red ring, blue cage",
  "QTAIM ellipticity BCP": "bond ellipticity at the bond critical points",
  "QTAIM DI": "delocalization index, shared electron pairs, at the bond critical point",
  "QTAIM charge": "QTAIM atomic charge in e, at the atom",
  "ELI-D bond electrons": "ELI-D bond basin population in e, at the basin maximum",
  "ELI-D bond maximum": "ELI-D value at the bond basin maximum",
  "ELI-D core electrons": "ELI-D core basin population in e, at the atom",
  "NPA charge": "natural population analysis charge in e, at the atom",
  "NRT total": "natural resonance theory bond order, at the bond midpoint",
  "NRT covalent": "natural resonance theory covalent bond order, at the bond midpoint",
  "NRT ionic": "natural resonance theory ionic bond order, at the bond midpoint",
  "NBO bonds": "number of two-centre NBO bonds, at the bond midpoint",
}


def _describe(prop):
  if prop in _desc:
    return _desc[prop]
  return "%s partition atomic charge in e, at the atom" % prop.split()[0]


def _atom(label, wfx):
  """0-based index from a QTAIM/ELI-D name, label + index: N0, or with a wfx label C1 + 0 = C10."""
  m = re.match(r"[A-Za-z]+(\d+)$", label)
  if not m:
    return None  # NNA near ..., core/shell basins
  d = m.group(1)
  if wfx:
    for k in range(1, len(d)):
      if d[:k] == str(int(d[k:]) + 1):
        return int(d[k:])
  return int(d)


def _put(out, prop, key, v, at=None, ball=None):
  if None in key or (len(key) == 2 and key[0] == key[1]):
    return
  if len(key) == 2 and isinstance(key[0], int):
    key = (min(key), max(key))
  out.setdefault(prop, {}).setdefault(key, (float(v), at, ball))  # the first table wins (spin/group tables follow)


def _lines(fn):
  if not os.path.isfile(fn):
    return []
  with open(fn, errors="replace") as f:
    return f.read().splitlines()


def _charge_table(out, lines, key):
  """'Table of Charges' of a NoSpherA2 partition: a header of scheme names, then label and one charge per scheme."""
  cols, have = None, set(out)
  for line in lines:
    if line.startswith("Table of Charges"):
      cols = []
      continue
    if cols == []:
      cols = line.split()[1:]
      continue
    t = line.split()
    if cols and len(t) == len(cols) + 1 and all(_float.match(x) for x in t[1:]):
      for s, v in zip(cols, t[1:]):
        if s + " charge" not in have:
          _put(out, s + " charge", key(t[0]), v)
    else:
      cols = None


def _values(folder):
  wfn = _wfn(folder)
  if wfn is None:
    return {}
  stem = os.path.splitext(wfn)[0]
  wfx = wfn.endswith(".wfx")
  out = {}
  for line in _lines(stem + ".rgbi_log"):
    m = _rgbi_row.match(line)
    if m:
      v = m.group(3).split()  # n_A n_B n_AB s_AB cov ion tot pyth arak
      k = (int(m.group(1)), int(m.group(2)))
      _put(out, "RGBI bond index", k, v[6])
      _put(out, "RGBI covalent", k, v[4])
      _put(out, "RGBI ionic", k, v[5])
  cp, at, in_di, bcp = None, None, False, {}
  names = {"Rho": "QTAIM rho CP", "DelSqRho": "QTAIM Laplacian CP", "Bond Ellipticity": "QTAIM ellipticity BCP"}
  for line in _lines(stem + ".qtaim_log"):
    m = _cp_head.match(line)
    if m:
      n, kind = int(m.group(1)), m.group(2)
      cp = None
      if not m.group(3) and kind == "bond":
        cp = (kind, (_atom(m.group(4), wfx), _atom(m.group(5), wfx)))
      elif not m.group(3) and kind in ("ring", "cage"):
        cp = (kind, (kind, n))
      continue
    m = _cp_value.match(line)
    if m and cp:
      if m.group(1) == "Position":
        at = tuple(float(x) * _bohr for x in m.group(2).split()[:3])
        if cp[0] == "bond" and None not in cp[1]:
          bcp[tuple(sorted(cp[1]))] = at
      elif cp[0] == "bond" or m.group(1) != "Bond Ellipticity":
        _put(out, names[m.group(1)], cp[1], m.group(2).split()[0], at, cp[0])
    m = _basin_row.match(line)
    if m and not m.group(2) and len(m.group(3).split()) == 7:
      _put(out, "QTAIM charge", (_atom(m.group(1), wfx),), m.group(3).split()[1])
    if line.startswith("  basin pair"):
      in_di = True
    elif in_di:
      m = _di_row.match(line)
      if m:
        k = (_atom(m.group(1), wfx), _atom(m.group(2), wfx))
        k = tuple(sorted(k)) if None not in k else k
        if k in bcp:  # every pair above 0.01 is listed; keep the bonded ones, those with a bond path
          _put(out, "QTAIM DI", k, m.group(3), bcp[k], "bond")
      elif line.strip() and not line.startswith("  NNA"):
        in_di = False
  for line in _lines(stem + ".eli_log"):
    m = _basin_row.match(line)
    if not m or len(m.group(3).split()) != 6:
      continue
    v = m.group(3).split()  # electrons volume maximum x y z
    if m.group(2) == "core":
      _put(out, "ELI-D core electrons", (_atom(m.group(1), wfx),), v[0])
    elif m.group(2) == "bond" and "-" in m.group(1):
      k = tuple(_atom(a, wfx) for a in m.group(1).split("-", 1))
      at = tuple(float(x) * _bohr for x in v[3:6])
      _put(out, "ELI-D bond electrons", k, v[0], at, "eli")
      _put(out, "ELI-D bond maximum", k, v[2], at, "eli")
  fn = stem + ".native.nbo.json"
  if os.path.isfile(fn):
    import json
    with open(fn) as f:
      nbo = json.load(f)
    for a in nbo.get("npa", []):
      if a.get("spin", "") == "":
        _put(out, "NPA charge", (a["atom"] - 1,), a["charge"])
    for b in nbo.get("nrt", {}).get("bond_orders", []):
      if not b.get("diagonal") and b.get("spin", "") == "" and b["total"] > 0:  # zero-order pairs are not bonds
        for key in ("total", "covalent", "ionic"):
          _put(out, "NRT " + key, (b["atom1"] - 1, b["atom2"] - 1), b[key])
    count = {}
    for b in nbo.get("nbos", []):
      if b.get("type") == "BD" and b.get("spin", "") in ("", "alpha") and len(b.get("centers", [])) == 2:
        k = tuple(sorted(c - 1 for c in b["centers"]))
        count[k] = count.get(k, 0) + 1
    for k, n in count.items():
      _put(out, "NBO bonds", k, n)
  # partition charges: all schemes from the full analysis, else the refinement's scheme next to the structure
  _charge_table(out, _lines(stem + ".partition_log"), lambda l: (_atom(l, wfx),))
  _charge_table(out, _lines(os.path.join(OV.FilePath(), OV.ModelSrc() + ".partitionlog")), lambda l: (l,))
  return out


def make_BondAtlas_GUI():
  if not show_BondAtlas():
    return ""
  from hybrid_GUI import begin_new_line, end_line, labeled_combo, labeled_text, button

  def combo(name, label, key, items, wl, wc, onchange=""):
    return labeled_combo("NoSpherA2_BA_%s@refine" % name, label, items, "spy.nsa2_get_param('BondAtlas.%s')" % key,
                         "spy.nsa2_set_param('BondAtlas.%s', html.GetValue('~name~'))%s" % (key, onchange),
                         width_label=wl, width_combo=wc)
  t = begin_new_line("NoSpherA2_BondAtlas", "1") + \
      combo("analysis", "Analysis", "analysis", ";".join(_analyses), 14, 18) + \
      button("NoSpherA2_BA_run", "Run", "spy.NoSpherA2.ba_run() >> html.Update()", width=10,
             hint="Compute the wavefunction with OCC if there is none, then run the analysis in the background") + \
      button("NoSpherA2_BA_stop", "Stop", "spy.NoSpherA2.ba_stop() >> html.Update()", width=10) + \
      "<td width='48%%' align='left'><i>%s</i></td>" % ba_status() + \
      end_line()
  props = ba_properties()
  if props:
    t += begin_new_line("NoSpherA2_BondAtlas", "2") + \
         combo("property", "Property", "property", props, 14, 30, " >> spy.NoSpherA2.ba_show()") + \
         labeled_text("NoSpherA2_BA_decimals@refine", "Decimals", "spy.nsa2_get_param('BondAtlas.decimals')",
                      "spy.nsa2_set_param('BondAtlas.decimals', html.GetValue('~name~'))", width_label=14, width_textbox=8) + \
         button("NoSpherA2_BA_show", "Show", "spy.NoSpherA2.ba_show()", width=10) + \
         button("NoSpherA2_BA_clear", "Clear", "spy.NoSpherA2.ba_clear()", width=10) + \
         "<td width='14%'></td>" + \
         end_line() + \
         begin_new_line("NoSpherA2_BondAtlas", "3") + \
         "<td width='100%%' align='left'><i>%s</i></td>" % ba_describe() + \
         end_line()
  return t


for _f in (make_BondAtlas_GUI, show_BondAtlas, ba_run, ba_stop, ba_status, ba_finished, ba_properties, ba_show, ba_describe, ba_clear):
  OV.registerFunction(_f, False, "NoSpherA2")
