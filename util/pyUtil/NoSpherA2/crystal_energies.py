"""Interaction energies between the molecules of a crystal, drawn as rods between molecular centroids.

NoSpherA2 -interaction_energies predicts the density of every unique molecule with the selected SALTED
model, lists every pair of molecules in contact and writes one table. The table is cached per structure
under olex2/CrystalEnergies/<key>, where the key hashes the atom types, fractional coordinates, cell,
symmetry, model and cutoff, so a moved atom or a refinement makes the old table unreachable.
"""
import os
import sys
import hashlib
import subprocess
import threading
import olx
import olex
import olex_core
from olexFunctions import OV
from variableFunctions import nsa2_get_param

_state = {"thread": None, "key": None, "rods": 0, "message": ""}
_folder = os.path.join("olex2", "CrystalEnergies")
_covalent = {"H": 0.31, "D": 0.31, "B": 0.84, "C": 0.76, "N": 0.71, "O": 0.66, "F": 0.57, "Si": 1.11, "P": 1.07,
             "S": 1.05, "Cl": 1.02, "Br": 1.20, "I": 1.39, "Se": 1.20, "Li": 1.28, "Na": 1.66, "K": 2.03}


def _radius(symbol):
  try:
    from cctbx.eltbx import covalent_radii
    return covalent_radii.table(symbol).radius()
  except Exception:
    return _covalent.get(symbol, 1.4)


def _floats(s):
  return [float(v) for v in s.replace(",", " ").split()]


def _cell_matrix(cell):
  import numpy as np
  a, b, c = cell[:3]
  ca, cb, cg = [np.cos(np.radians(v)) for v in cell[3:]]
  sg = np.sin(np.radians(cell[5]))
  V = a * b * c * np.sqrt(1 - ca * ca - cb * cb - cg * cg + 2 * ca * cb * cg)
  return np.array([[a, b * cg, c * cb], [0, b * sg, c * (ca - cb * cg) / sg], [0, 0, V / (a * b * sg)]])


def _structure():
  cell = _floats(olx.xf.au.GetCell())
  atoms = []
  skipped = 0
  for i in range(int(olx.xf.au.GetAtomCount())):
    if olx.xf.au.IsAtomDeleted(i).lower() == "true":
      continue
    t = olx.xf.au.GetAtomType(i)
    if t == "Q":
      continue
    if int(olx.xf.au.GetAtomPart(i)) > 1:
      skipped += 1
      continue
    atoms.append((olx.xf.au.GetAtomlabel(i), t, _floats(olx.xf.au.GetAtomCrd(i))))
  if skipped:
    print("Crystal energies: %d atoms of disorder parts above 1 left out" % skipped)
  ops = [tuple(tuple(r) for r in m) for m in olex_core.SGInfo()["MatricesAll"]]
  identity = ((1, 0, 0, 0.0), (0, 1, 0, 0.0), (0, 0, 1, 0.0))
  if identity not in ops:
    ops.insert(0, identity)
  return cell, atoms, ops


def _key(cell, atoms, ops, model, cutoff):
  h = hashlib.sha1()
  h.update(" ".join("%.4f" % v for v in cell).encode())
  for a in atoms:
    h.update(("%s %.5f %.5f %.5f" % (a[1], a[2][0], a[2][1], a[2][2])).encode())
  h.update(repr(ops).encode())
  h.update(("%s %.3f" % (os.path.normcase(os.path.abspath(model)), cutoff)).encode())
  return h.hexdigest()[:16]


def _molecules(cell, atoms, ops):
  """Grows every unique molecule from the asymmetric unit over the symmetry of the cell.

  Returns a list of molecules, each a list of (element, cartesian position in Angstrom)."""
  import numpy as np
  M = _cell_matrix(cell)
  N = len(atoms)
  X = np.array([a[2] for a in atoms], float)
  R = np.array([[m[r][:3] for r in range(3)] for m in ops], float)
  T = np.array([[m[r][3] for r in range(3)] for m in ops], float)
  img = np.einsum("oij,nj->oni", R, X) + T[:, None, :]
  rad = np.array([_radius(a[1]) for a in atoms])
  ident = [i for i, m in enumerate(ops) if all(m[r][:3] == ((1, 0, 0), (0, 1, 0), (0, 0, 1))[r] and abs(m[r][3]) < 1e-6 for r in range(3))][0]
  limit = max(4 * N, 500)
  covered = set()
  molecules = []
  for seed in range(N):
    if seed in covered:
      continue
    queue = [(seed, ident, np.zeros(3))]
    positions = {}
    members = []
    while queue:
      j, o, n = queue.pop()
      p = img[o, j] + n
      pk = tuple(np.round(p, 3))
      if pk in positions:
        continue
      positions[pk] = True
      members.append((j, p))
      if len(members) > limit:
        raise RuntimeError("molecule grown from %s does not close: polymeric or overlapping disorder?" % atoms[seed][0])
      d = p[None, None, :] - img
      nn = np.round(d)
      dist = np.linalg.norm((d - nn) @ M.T, axis=-1)
      bonded = dist < (rad[j] + rad)[None, :] + 0.4
      for o2, k in zip(*np.nonzero(bonded)):
        queue.append((k, o2, nn[o2, k]))
    covered.update(j for j, p in members)
    molecules.append([(atoms[j][1], M @ p) for j, p in members])
  return molecules


def _write_inputs(folder, cell, atoms, ops, cutoff):
  molecules = _molecules(cell, atoms, ops)
  a, b, c = cell[:3]
  import numpy as np
  V = float(np.linalg.det(_cell_matrix(cell)))
  with open(os.path.join(folder, "structure.cif"), "w") as f:
    f.write("data_crystal_energies\n_cell_length_a %.6f\n_cell_length_b %.6f\n_cell_length_c %.6f\n" % (a, b, c))
    f.write("_cell_angle_alpha %.5f\n_cell_angle_beta %.5f\n_cell_angle_gamma %.5f\n_cell_volume %.4f\n" % (cell[3], cell[4], cell[5], V))
    f.write("loop_\n_space_group_symop_operation_xyz\n")
    for m in ops:
      f.write("'%s'\n" % olex_core.MatrixToString(m))
  with open(os.path.join(folder, "job.txt"), "w") as f:
    f.write("cif structure.cif\ncutoff %.3f\noutput interaction_energies.txt\n" % cutoff)
    for i, mol in enumerate(molecules):
      name = "molecule_%d.xyz" % (i + 1)
      with open(os.path.join(folder, name), "w") as x:
        x.write("%d\nunique molecule %d from Olex2\n" % (len(mol), i + 1))
        for sym, p in mol:
          x.write("%-2s %12.6f %12.6f %12.6f\n" % (sym, p[0], p[1], p[2]))
      f.write("molecule %s\n" % name)
  return len(molecules)


def _table(folder):
  rows = []
  path = os.path.join(folder, "interaction_energies.txt")
  if not os.path.exists(path):
    return None
  with open(path) as f:
    for line in f:
      if line.startswith("#") or not line.strip():
        continue
      t = line.split()
      rows.append({"A": int(t[0]), "B": int(t[1]), "symop": t[2], "n": [int(v) for v in t[3:6]], "R": float(t[6]),
                   "cA": [float(v) for v in t[7:10]], "cB": [float(v) for v in t[10:13]],
                   "elst": float(t[13]), "pol": float(t[14]), "disp": float(t[15]), "rep": float(t[16]), "total": float(t[17])})
  return rows


def _colour(E, scale):
  x = max(-1.0, min(1.0, E / scale)) if scale > 0 else 0.0
  if x < 0:
    r, g, b = 1 + x, 1 + x, 1.0
  else:
    r, g, b = 1.0, 1 - x, 1 - x
  return int(255 * r) | (int(255 * g) << 8) | (int(255 * b) << 16) | (255 << 24)


def _material(E, scale):
  c = _colour(E, scale)
  return "85;%d;%d;4290822336;32" % (c, c)


def _setup():
  model = nsa2_get_param("selected_salted_model") or ""
  cutoff = float(nsa2_get_param("CE_cutoff") or 3.8)
  cell, atoms, ops = _structure()
  key = _key(cell, atoms, ops, model, cutoff)
  folder = os.path.join(OV.FilePath(), _folder, key)
  return model, cutoff, cell, atoms, ops, key, folder


def crystal_energies_status():
  t = _state["thread"]
  if t is not None and t.is_alive():
    return "running"
  if _state["message"]:
    return _state["message"]
  try:
    model, cutoff, cell, atoms, ops, key, folder = _setup()
  except Exception:
    return ""
  if _table(folder) is not None:
    return "cached" if _state["key"] != key or not _state["rods"] else "shown"
  return "not calculated"


def crystal_energies_clear():
  if _state["rods"]:
    olex.m("kill ce_*")
  _state["rods"] = 0
  _state["key"] = None
  _state["message"] = ""


def crystal_energies_invalidate():
  """Called when a refinement starts: the energies of the previous geometry are void."""
  try:
    crystal_energies_clear()
  except Exception:
    pass


def crystal_energies_draw(quiet=False):
  model, cutoff, cell, atoms, ops, key, folder = _setup()
  rows = _table(folder)
  if rows is None:
    _state["message"] = ""
    if not quiet:
      print("Crystal energies: nothing cached for this geometry, press Calculate")
    return False
  crystal_energies_clear()
  scale = max([abs(r["total"]) for r in rows] + [1e-6])
  for i, r in enumerate(rows):
    name = "ce_%d" % (i + 1)
    olex.m("SetMaterial %s.'Single cone' %s" % (name, _material(r["total"], scale)))
    olex.m("line -n=%s %.4f %.4f %.4f %.4f %.4f %.4f" % ((name,) + tuple(r["cA"]) + tuple(r["cB"])))
  _state["rods"] = len(rows)
  _state["key"] = key
  print("Crystal energies (kJ/mol), blue attractive, red repulsive, scaled to %.1f:" % scale)
  print("  rod  A  B  symop            n        R/A   E_elst   E_pol  E_disp   E_rep  E_total")
  for i, r in enumerate(rows):
    print("  %-4s %d  %d  %-16s %2d %2d %2d %7.3f %8.2f %7.2f %7.2f %7.2f %8.2f" % (
      "ce_%d" % (i + 1), r["A"] + 1, r["B"] + 1, r["symop"], r["n"][0], r["n"][1], r["n"][2], r["R"],
      r["elst"], r["pol"], r["disp"], r["rep"], r["total"]))
  olex.m("html.Update")
  return True


def crystal_energies_finished():
  _state["thread"] = None
  try:
    if not crystal_energies_draw(quiet=True):
      _state["message"] = "failed, see NoSpherA2_CE.log"
      print("Crystal energies: NoSpherA2 wrote no table, see the log in %s" % _folder)
  except Exception:
    sys.stderr.formatExceptionInfo()
  olex.m("html.Update")


class _Runner(threading.Thread):
  def __init__(self, args, folder):
    threading.Thread.__init__(self)
    self.args = args
    self.folder = folder

  def run(self):
    olex_core.IncRunningThreadsCount()
    try:
      startinfo = None
      flags = 0
      if sys.platform[:3] == "win":
        from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW, SW_HIDE
        startinfo = STARTUPINFO()
        startinfo.dwFlags |= STARTF_USESHOWWINDOW
        startinfo.wShowWindow = SW_HIDE
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
      with open(os.path.join(self.folder, "NoSpherA2_CE.log"), "w") as log:
        subprocess.call(self.args, cwd=self.folder, stdout=log, stderr=subprocess.STDOUT, startupinfo=startinfo, creationflags=flags)
    except Exception:
      sys.stderr.formatExceptionInfo()
    finally:
      olex_core.DecRunningThreadsCount()
      olx.Schedule(1, "spy.NoSpherA2.crystal_energies_finished()")


def crystal_energies_calculate():
  """Draws the cached rods for the current geometry, or predicts the energies in the background first."""
  t = _state["thread"]
  if t is not None and t.is_alive():
    print("Crystal energies: a calculation is still running")
    return
  model, cutoff, cell, atoms, ops, key, folder = _setup()
  if not model:
    print("Crystal energies: select a SALTED model in the NoSpherA2 refinement panel first")
    return
  if not os.path.isdir(model):
    for candidate in (model, os.path.join(OV.FilePath(), model)):
      if os.path.isdir(candidate):
        model = candidate
        break
    else:
      print("Crystal energies: SALTED model %s not found" % model)
      return
  if _table(folder) is not None:
    crystal_energies_draw()
    return
  if not os.path.isdir(folder):
    os.makedirs(folder)
  try:
    n = _write_inputs(folder, cell, atoms, ops, cutoff)
  except Exception as e:
    print("Crystal energies: %s" % e)
    return
  args = [OV.GetVar("NoSpherA2"), "-SALTED", model, "-interaction_energies", "job.txt", "-cpus", str(nsa2_get_param("ncpus")), "-no_date"]
  _state["message"] = ""
  _state["thread"] = _Runner(args, folder)
  _state["thread"].start()
  print("Crystal energies: predicting %d unique molecule(s) with %s in the background, cutoff %.2f A" % (n, os.path.basename(os.path.normpath(model)), cutoff))
  olex.m("html.Update")


def crystal_energies_recalculate():
  """Discards the cached table for the current geometry and calculates again."""
  model, cutoff, cell, atoms, ops, key, folder = _setup()
  path = os.path.join(folder, "interaction_energies.txt")
  if os.path.exists(path):
    os.remove(path)
  crystal_energies_clear()
  crystal_energies_calculate()


for _f in (crystal_energies_calculate, crystal_energies_recalculate, crystal_energies_draw, crystal_energies_clear,
           crystal_energies_invalidate, crystal_energies_finished, crystal_energies_status):
  OV.registerFunction(_f, False, "NoSpherA2")
