"""Interaction energies between the molecules of a crystal, drawn as rods between molecular centroids.

NoSpherA2 -interaction_energies predicts the density of every unique molecule with the selected SALTED
model, lists every pair of molecules in contact and writes one table. The rods show one energy kind
(CE_kind), one colour per kind and the radius proportional to |E|, for every symmetry image of a pair that
touches a molecule on screen, or the whole 3x3x3 block of cells (the energy framework). The table is cached per structure
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

_state = {"thread": None, "key": None, "rods": 0, "message": "", "block": False}
# one colour per energy kind for attractive values; repulsive ones fade towards white
KINDS = {"elst": (0, 0, 255), "pol": (255, 140, 0), "disp": (0, 160, 0), "rep": (255, 0, 0), "xc": (255, 220, 0), "total": (150, 0, 200)}
_columns = {"E_elst": "elst", "E_pol": "pol", "E_disp": "disp", "E_rep": "rep", "E_xc": "xc", "E_total": "total"}
_rod_radius = (0.3, 3.0)  # rod radius (line -r=) for |E| = 0 and |E| = the largest of the table
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


def _structure_hash(cell, atoms, ops):
  """sha1 of the geometry: cell, atom types and fractional coordinates, symmetry. Shared by every cached product."""
  h = hashlib.sha1()
  h.update(" ".join("%.4f" % v for v in cell).encode())
  for a in atoms:
    h.update(("%s %.5f %.5f %.5f" % (a[1], a[2][0], a[2][1], a[2][2])).encode())
  h.update(repr(ops).encode())
  return h


def _key(cell, atoms, ops, model, cutoff):
  h = _structure_hash(cell, atoms, ops)
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
  names = None
  with open(path) as f:
    for line in f:
      if line.startswith("# A B symop"):
        names = line[1:].split()
        continue
      if line.startswith("#") or not line.strip() or names is None:
        continue
      t = line.split()
      r = {"A": int(t[0]), "B": int(t[1]), "symop": t[2], "n": [int(v) for v in t[3:6]], "R": float(t[6]),
           "cA": [float(v) for v in t[7:10]], "cB": [float(v) for v in t[10:13]], "xc": 0.0}
      for name, v in zip(names[13:], t[13:]):
        r[_columns.get(name, name)] = float(v)
      rows.append(r)
  return rows


def _colour(E, kind):
  rgb = KINDS[kind]
  if E > 0:  # repulsive: 60 % of the way to white
    rgb = [v + (255 - v) * 0.6 for v in rgb]
  r, g, b = [int(v) for v in rgb]
  return r | (g << 8) | (b << 16) | (255 << 24)


def _material(E, kind):
  # front and back (flags 255): a rod cut open by the near clip plane shows its
  # inside, and a front-only material leaves those back faces black
  c = _colour(E, kind)
  return "255;%d;%d;%d;%d;4290822336;4290822336;32;32" % (c, c, c, c)


def _ops_arrays(ops):
  import numpy as np
  return (np.array([[m[r][:3] for r in range(3)] for m in ops], float),
          np.array([[m[r][3] for r in range(3)] for m in ops], float))


def _visible_centroids(folder, cell, atoms, ops):
  """Fractional centroids of the molecule images on screen: every displayed atom is matched to an image of a unique molecule."""
  import numpy as np
  Minv = np.linalg.inv(_cell_matrix(cell))
  R, T = _ops_arrays(ops)
  xyz = os.path.join(folder, "displayed.xyz")
  olx.File(xyz, p=6)
  with open(xyz) as f:
    lines = f.read().splitlines()
  X = np.array([[float(v) for v in l.split()[1:4]] for l in lines[2:2 + int(lines[0])] if l.split()[0] != "Q"]).reshape(-1, 3)
  F = X @ Minv.T
  found = set()
  for mol in _molecules(cell, atoms, ops):
    P = np.array([p for sym, p in mol]) @ Minv.T
    c = P.mean(axis=0)
    for o in range(len(ops)):
      d = F[:, None, :] - (P @ R[o].T + T[o])[None, :, :]
      n = np.round(d)
      hit = np.all(np.abs(d - n) < 1e-3, axis=2)
      for t in np.unique(n[hit], axis=0):
        found.add(tuple(np.round(R[o] @ c + T[o] + t, 3)))
  return sorted(found)


def _block_centroids(cell, atoms, ops):
  """Fractional centroids of every molecule image in the 3x3x3 block of cells around the origin cell."""
  import numpy as np
  from itertools import product
  Minv = np.linalg.inv(_cell_matrix(cell))
  R, T = _ops_arrays(ops)
  found = set()
  for mol in _molecules(cell, atoms, ops):
    c = Minv @ np.mean([p for sym, p in mol], axis=0)
    for o in range(len(ops)):
      ci = R[o] @ c + T[o]
      ci -= np.floor(ci)
      for t in product((-1, 0, 1), repeat=3):
        found.add(tuple(np.round(ci + t, 3)))
  return sorted(found)


def _bars(rows, cell, ops, centroids):
  """Symmetry images of the table's pairs with at least one end at one of the fractional centroids.

  Each bar once (unordered ends, rounded), as (row, cartesian A, cartesian B)."""
  import numpy as np
  M = _cell_matrix(cell)
  Minv = np.linalg.inv(M)
  R, T = _ops_arrays(ops)
  C = np.array(centroids, float).reshape(-1, 3)
  seen = set()
  bars = []
  for r in rows:
    fA, fB = Minv @ r["cA"], Minv @ r["cB"]
    for o in range(len(ops)):
      a, b = R[o] @ fA + T[o], R[o] @ fB + T[o]
      for end in (a, b):
        d = C - end
        n = np.round(d)
        for t in n[np.all(np.abs(d - n) < 1e-3, axis=1)]:
          key = tuple(sorted((tuple(np.round(a + t, 3)), tuple(np.round(b + t, 3)))))
          if key not in seen:
            seen.add(key)
            bars.append((r, M @ (a + t), M @ (b + t)))
  return bars


def _setup():
  model = nsa2_get_param("selected_salted_model") or ""
  cutoff = float(nsa2_get_param("CE_cutoff") or 3.8)
  cell, atoms, ops = _structure()
  key = _key(cell, atoms, ops, model, cutoff)
  folder = os.path.join(OV.FilePath(), _folder, key)
  return model, cutoff, cell, atoms, ops, key, folder


def _style_images(ads):
  """Symmetry-generated atoms on screen as balls (sph) or back to their saved style (def), the asymmetric unit untouched.

  'ads -t' keeps the balls out of the saved style: that style is shared with the
  asymmetric-unit atoms of the same element, so a saved 'sph' and a forced 'elp'
  restore changed the user's ellipsoids for good."""
  olex.m("sel -u")
  olex.m("sel atoms where xatom.symm==1")  # the symm evaluator has == only
  olex.m("sel -i")
  if ads == "sph":
    if not olex.m("ads sph -t sel"):
      olex.m("ads sph sel")  # binaries before 'ads -t'
  elif not olex.m("ads def sel"):
    olex.m("ads elp sel")  # binaries before 'ads def'
  olex.m("sel -u")
  _state["styled"] = ads == "sph"


def _progress(folder):
  """The exe's last 'PAIR i/n' line, or 'predicting' while the SALTED densities are still being made."""
  try:
    with open(os.path.join(folder, "NoSpherA2_CE.log")) as f:
      pairs = [l.split()[1] for l in f if l.startswith("PAIR ")]
  except (IOError, IndexError):
    return ""
  return "pair " + pairs[-1] if pairs else "predicting"


def crystal_energies_status():
  t = _state["thread"]
  if t is not None and t.is_alive():
    olx.Schedule(3, "html.Update")  # the panel re-reads this status while the exe runs
    try:
      return "running %s" % _progress(_setup()[-1])
    except Exception:
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
  # always: rods left by a reloaded module or a lost state would stay on screen. kill tries atoms before objects,
  # and "ce_*" was atom Ce in any residue: every refine deleted a Ce atom labelled Ce. A prefix longer than
  # max_label_length (4) without '_' matches no atom
  olex.m("kill cerods*")
  if _state.get("styled"):
    _style_images("def")
  _state["rods"] = 0
  _state["key"] = None
  _state["message"] = ""


def crystal_energies_invalidate():
  """Called when a refinement starts: the energies of the previous geometry are void."""
  try:
    crystal_energies_clear()
  except Exception:
    pass


def crystal_energies_draw(quiet=False, block=False):
  """Rods of the selected energy kind (CE_kind) for the molecules on screen, or for the 3x3x3 block of cells."""
  model, cutoff, cell, atoms, ops, key, folder = _setup()
  rows = _table(folder)
  if rows is None:
    _state["message"] = ""
    if not quiet:
      print("Crystal energies: nothing cached for this geometry, press Calculate")
    return False
  block = str(block).lower() in ("true", "1")
  kind = nsa2_get_param("CE_kind") or "total"
  if kind not in KINDS:
    kind = "total"
  crystal_energies_clear()
  centroids = _block_centroids(cell, atoms, ops) if block else _visible_centroids(folder, cell, atoms, ops)
  shown = _selected_pairs(rows)
  bars = _bars([rows[i] for i in shown], cell, ops, centroids)
  scale = max([abs(r[kind]) for r in rows] + [1e-6])  # radius relative to the whole table, one pair or all
  for i, (r, a, b) in enumerate(bars):
    name = "cerods%d" % (i + 1)
    radius = _rod_radius[0] + (_rod_radius[1] - _rod_radius[0]) * abs(r[kind]) / scale
    line = "line -n=%s -r=%.3f %%s %.4f %.4f %.4f %.4f %.4f %.4f" % ((name, radius) + tuple(a) + tuple(b))
    # bare -l hides the label, the energies are in the printed table; an Olex2 without -l rejects the
    # whole call, so fall back to the length label
    if not (_state.get("line_l", True) and olex.m(line % "-l")):
      _state["line_l"] = False
      olex.m(line % "")
    # after the line: the collection must exist for SetMaterial to reach its primitives
    olex.m("mask %s 7" % name)  # cone + both end disks
    mat = _material(r[kind], kind)
    for p in ("Single cone", "Top disk", "Bottom disk"):  # by name: the GUI's SetMaterial would store '*' as a material
      olx.SetMaterial("%s.%s" % (name, p), mat)  # one argument each: the space in the name
  _state["rods"] = len(bars)
  _state["key"] = key
  _state["block"] = block
  _style_images("sph")
  print("Crystal energies (kJ/mol): %d rods of E_%s for %d molecule(s), radius scaled to %.1f, attractive in colour, repulsive pale" % (
    len(bars), kind, len(centroids), scale))
  print("  pair  A  B  symop            n        R/A   E_elst   E_pol  E_disp   E_rep    E_xc  E_total")
  for i, r in enumerate(rows):
    print("  %-4d  %d  %d  %-16s %2d %2d %2d %7.3f %8.2f %7.2f %7.2f %7.2f %7.2f %8.2f%s" % (
      i + 1, r["A"] + 1, r["B"] + 1, r["symop"], r["n"][0], r["n"][1], r["n"][2], r["R"],
      r["elst"], r["pol"], r["disp"], r["rep"], r["xc"], r["total"], "  shown" if i in shown else ""))
  olex.m("html.Update")
  return True


def _pair_label(i, r):
  return "%d: %d-%d %s %.2fA" % (i + 1, r["A"] + 1, r["B"] + 1, r["symop"], r["R"])


def _selected_pairs(rows):
  """Indices of the cached pairs the CE_pair dropdown selects: every pair for 'all', else the one numbered pair."""
  choice = nsa2_get_param("CE_pair") or "all"
  try:
    i = int(choice.split(":")[0]) - 1
    if 0 <= i < len(rows):
      return [i]
  except ValueError:
    pass
  return list(range(len(rows)))


def crystal_energies_pairs():
  """Items of the pair dropdown: 'all' and one entry per cached pair (number, molecules, symop, centroid distance)."""
  try:
    rows = _table(_setup()[-1]) or []
  except Exception:
    rows = []
  return ";".join(["all"] + [_pair_label(i, r) for i, r in enumerate(rows)])


def crystal_energies_framework():
  """The energy framework of the 3x3x3 block of cells around the origin cell."""
  crystal_energies_draw(block=True)


def crystal_energies_redraw():
  """After a change of the energy kind: the rods on screen again, in the same mode."""
  if _state["rods"]:
    crystal_energies_draw(quiet=True, block=_state["block"])


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


for _f in (crystal_energies_calculate, crystal_energies_recalculate, crystal_energies_draw, crystal_energies_framework,
           crystal_energies_redraw, crystal_energies_clear, crystal_energies_invalidate, crystal_energies_finished,
           crystal_energies_status, crystal_energies_pairs):
  OV.registerFunction(_f, False, "NoSpherA2")
