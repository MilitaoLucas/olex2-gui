import os
import re
import struct
import shutil
import time
from cctbx import miller
import olex
import olx
import olex_core
import math
import numpy as np
import itertools
from scipy import linalg
import textwrap
from typing import List, Sequence, Union

from olexFunctions import OV
from variableFunctions import nsa2_get_param, nsa2_set_param
from cctbx_olex_adapter import OlexCctbxAdapter
from smtbx.structure_factors import direct
from cctbx import sgtbx
from cctbx import adptbx
from cctbx.array_family import flex
from cctbx_olex_adapter import OlexCctbxMasks
from cctbx.eltbx import tiny_pse
from iotbx.cif import miller_indices_as_cif_loop
from libtbx.containers import OrderedDict
if OV.HasGUI():
  import olex_xgrid

#import NoSpherA2
from utilities import is_disordered, is_pause_break_pressed, terminate_process_tree, consume_interrupt_request
from utilities import open  # code page independent, see utilities.open
#import Wfn_Job
from decors import run_with_bitmap

a2b = 0.529177210903

try:
  from_outside = False
  p_path = os.path.dirname(os.path.abspath(__file__))
except:
  from_outside = True
  p_path = os.path.dirname(os.path.abspath("__file__"))

class HermitePolynomial:
  THIRD_ORDER_COEFFICIENTS = ([0, 0, 0], [0, 0, 1], [0, 0, 2], [0, 1, 1],
                              [0, 1, 2], [0, 2, 2], [1, 1, 1], [1, 1, 2],
                              [1, 2, 2], [2, 2, 2])
  FOURTH_ORDER_COEFFICIENTS = ([0, 0, 0, 0], [0, 0, 0, 1], [0, 0, 0, 2],
                               [0, 0, 1, 1], [0, 0, 1, 2], [0, 0, 2, 2],
                               [0, 1, 1, 1], [0, 1, 1, 2], [0, 1, 2, 2],
                               [0, 2, 2, 2], [1, 1, 1, 1], [1, 1, 1, 2],
                               [1, 1, 2, 2], [1, 2, 2, 2], [2, 2, 2, 2])

  def __init__(self, coefficients: Sequence[int]):
    self.c = coefficients
    self.order = len(coefficients)
    if self.order == 3:
      self._call = self._call_for_order_3
    elif self.order == 4:
      self._call = self._call_for_order_4
    else:
      raise NotImplementedError(f'Order {self.order} is not implemented')

  def __call__(self, u: np.ndarray, si_inv: np.ndarray) -> np.ndarray:
    return self._call(u, si_inv)

  def __str__(self) -> str:
    return 'H' + ''.join([str(c + 1) for c in self.c])

  def _call(self, u: np.ndarray, si_inv: np.ndarray) -> np.ndarray:
    """This method is abstract, to be overwritten by `self._call_for_order_*`"""

  def _call_for_order_3(self, u: np.ndarray, si_inv: np.ndarray) -> np.ndarray:
    wj, wk, wl = self.w(u, si_inv)
    r = wj * wl * wk - wj * si_inv[self.c[1], self.c[2]]\
      - wk * si_inv[self.c[2], self.c[0]] - wl * si_inv[self.c[0], self.c[1]]
    return r * self.unique_indexing_permutations

  def _call_for_order_4(self, u: np.ndarray, si_inv: np.ndarray) -> np.ndarray:
    wj, wk, wl, wm = self.w(u, si_inv)
    r = (wj * wk * wl * wm
         - wj * wk * si_inv[self.c[2], self.c[3]]
         - wj * wl * si_inv[self.c[1], self.c[3]]
         - wj * wm * si_inv[self.c[1], self.c[2]]
         - wk * wl * si_inv[self.c[3], self.c[0]]
         - wk * wm * si_inv[self.c[2], self.c[0]]
         - wl * wm * si_inv[self.c[0], self.c[1]]
         + si_inv[self.c[0], self.c[1]] * si_inv[self.c[2], self.c[3]]
         + si_inv[self.c[0], self.c[2]] * si_inv[self.c[3], self.c[1]]
         + si_inv[self.c[0], self.c[3]] * si_inv[self.c[1], self.c[2]])
    return r * self.unique_indexing_permutations

  @property
  def order_factorial(self) -> int:
    return math.factorial(self.order)

  @property
  def unique_indexing_permutations(self) -> int:
    return self.order_factorial / \
        np.prod([math.factorial(self.c.count(i)) for i in range(self.order)])

  def w(self, u: np.ndarray, si_inv: np.ndarray) -> List[np.ndarray]:
    return [sum(si_inv[c, i] * u[:, i] for i in range(3)) for c in self.c]


hermite_polynomials_of_3rd_and_4th_order = \
  [HermitePolynomial(c) for c in HermitePolynomial.THIRD_ORDER_COEFFICIENTS] +\
  [HermitePolynomial(c) for c in HermitePolynomial.FOURTH_ORDER_COEFFICIENTS]

hermite_polynomials_of_3rd_order = \
  [HermitePolynomial(c) for c in HermitePolynomial.THIRD_ORDER_COEFFICIENTS]


def kuhs_limit(order: int, adp: np.ndarray) -> float:
  """Resolution required to model anharmonic ADP; see doi: 10.1071/PH880369"""
  return (2. * np.pi) ** -1.5 * (2. * order * np.log(2) / adp) ** 0.5

def _wfn_file():
  # the wavefunction of the displayed model, in the structure folder
  for ext in (".gbw", ".wfx", ".ffn", ".wfn", ".molden", ".xtb"):
    fn = os.path.join(OV.FilePath(), OV.ModelSrc() + ext)
    if os.path.exists(fn):
      return fn
  return None

# NoSpherA2 products live under olex2/NoSpherA2/<structure key>[/<wavefunction key>]: a refined geometry or a new
# wavefunction makes the old ones unreachable, an unchanged one is shown again without running NoSpherA2
_wfn_keys = {}

def _salted_model():
  # the SALTED model selected in the refinement panel, resolved against the structure folder; None without one
  model = nsa2_get_param("selected_salted_model") or ""
  for c in (model, os.path.join(OV.FilePath(), model)):
    if model and os.path.isdir(c):
      return c
  return None

def has_density_source():
  # the Properties panel shows when NoSpherA2 can compute a density: a wavefunction, or a SALTED model for the xyz
  return bool(_wfn_file() or _salted_model())
OV.registerFunction(has_density_source, False, 'NoSpherA2')

def _cache_dir(wfn=None):
  from crystal_energies import _structure, _structure_hash
  d = os.path.join(OV.FilePath(), "olex2", "NoSpherA2", _structure_hash(*_structure()).hexdigest()[:16])
  if not wfn and _salted_model():  # SALTED products are keyed by the model, like wavefunction products by the file
    d = os.path.join(d, "SALTED_" + os.path.basename(os.path.normpath(_salted_model())))
  if wfn:
    st = os.stat(wfn)
    k = _wfn_keys.get((wfn, st.st_size, st.st_mtime))
    if k is None:
      import hashlib
      with open(wfn, "rb") as f:
        k = _wfn_keys[(wfn, st.st_size, st.st_mtime)] = hashlib.sha1(f.read()).hexdigest()[:16]
    d = os.path.join(d, k)
  return d

def _ensure(d):
  # creates a product folder and records it under the current history node in olex2/NoSpherA2/index.json
  if os.path.isdir(d):
    return d
  os.makedirs(d)
  import json
  fn = os.path.join(OV.FilePath(), "olex2", "NoSpherA2", "index.json")
  idx = json.load(open(fn)) if os.path.isfile(fn) else {}
  node = OV.GetParam('snum.history.current_node') or ""
  rel = os.path.relpath(d, os.path.dirname(fn)).replace("\\", "/")
  if rel not in idx.setdefault(node, []):
    idx[node].append(rel)
  json.dump(idx, open(fn, "w"), indent=1)
  return d

def _p(fn, d=None):
  # path of a product of the displayed model (with its wavefunction when there is one);
  # NoSpherA2 runs with -cubeb, so a .cube product is the binary .cubeb when that exists
  fn = os.path.join(d or _cache_dir(_wfn_file()), fn)
  if fn.endswith(".cube") and os.path.isfile(fn + "b"):
    return fn + "b"
  return fn

def _cached_wfn():
  # NoSpherA2 writes its cubes next to the wavefunction, so the wavefunction gets a copy in its product folder
  wfn = _wfn_file()
  if not wfn:
    return None
  target = os.path.join(_ensure(_cache_dir(wfn)), os.path.basename(wfn))
  if not os.path.exists(target):
    shutil.copy2(wfn, target)
  return target

def _source():
  # what NoSpherA2 computes the density from, (input args, folder): the cached wavefunction, else the displayed
  # molecule as xyz with the selected SALTED model (charge-constrained prediction), else (None, None)
  wfn = _cached_wfn()
  if wfn:
    return ["-wfn", wfn], os.path.dirname(wfn)
  model = _salted_model()
  if not model:
    print("No wavefunction next to the structure (gbw, wfx, ffn, wfn, molden or xtb) and no SALTED model selected")
    return None, None
  d = _ensure(_cache_dir())
  xyz = os.path.join(d, OV.ModelSrc() + ".xyz")
  if not os.path.isfile(xyz):
    olx.Kill("$Q")
    olx.File(xyz, p=10)
  return ["-xyz", xyz] + _salted_args(model), d

def _salted_args(model):
  return ["-SALTED", model]

def _cif_arg():
  return ["-cif", os.path.join(OV.FilePath(), OV.ModelSrc() + ".cif")]

def _run_nsa2(args, wait=False, cwd=None, on_tick=None):
  # NoSpherA2 <args> in cwd (default the structure folder), log NoSpherA2_cube.log; True when it started (wait: finished with 0)
  NoSpherA2 = OV.GetVar("NoSpherA2")
  if not NoSpherA2:
    print("NoSpherA2 executable is not configured.")
    return False
  if os.path.isabs(NoSpherA2) and not os.path.exists(NoSpherA2):
    print(f"NoSpherA2 executable not found: {NoSpherA2}")
    return False
  args = [NoSpherA2, "-cpus", nsa2_get_param('ncpus'), "-cubeb"] + args  # binary cubes, _read_cube loads them in ms
  if nsa2_get_param('NoSpherA2_debug'):
    args.append("-v")

  cube_dir = _ensure(cwd) if cwd else OV.FilePath()
  cube_log = os.path.join(cube_dir, "NoSpherA2_cube.log")
  for old_log in (cube_log, os.path.join(cube_dir, "NoSpherA2.log")):  # both are tailed below, so neither may hold a previous run
    if os.path.exists(old_log):
      shutil.move(old_log, old_log + "_org")

  import subprocess
  startinfo = None
  creationflags = 0
  if os.name == 'nt':
    startinfo = subprocess.STARTUPINFO()
    startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startinfo.wShowWindow = 0
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

  log_handle = open(cube_log, "w", encoding="utf-8", errors="replace")
  try:
    p = subprocess.Popen(
      args,
      cwd=cube_dir,
      stdout=log_handle,
      stderr=subprocess.STDOUT,
      stdin=subprocess.DEVNULL,
      startupinfo=startinfo,
      creationflags=creationflags,
    )
    if wait:
      rc = _stream_nsa2(p, cube_dir, on_tick)
    else:
      time.sleep(0.2)
      rc = p.poll()
    if rc is not None and rc != 0:
      print(f"NoSpherA2 exited with code {rc}.")
      try:
        with open(cube_log, "r", encoding="utf-8", errors="replace") as lf:
          content = lf.read().strip()
          if content:
            print(content)
      except Exception:
        pass
      return False
    if not wait:
      print("Cube calculation started in background.")
    return True
  except Exception as e:
    print(f"Failed to start NoSpherA2: {e}")
    return False
  finally:
    log_handle.close()

def _stream_nsa2(p, cube_dir, on_tick=None):
  # Tails the logs NoSpherA2 writes (NoSpherA2.log from main, NoSpherA2_cube.log from the property run) into the
  # console while it runs and pumps the GUI, like the partitioning run in utilities; the progress bars grow line-wise
  # because the exe rewrites them in place. Ctrl+Break / stop_current_process kills the run. Returns the exit code.
  logs = {}
  bitmap = "NoSpherA2"
  gui = OV.HasGUI()
  if gui:
    run_with_bitmap(bitmap)  # renders the bitmap image; CreateBitmap only shows it
    OV.CreateBitmap(bitmap)
  try:
    while True:
      rc = p.poll()
      for fn in ("NoSpherA2.log", "NoSpherA2_cube.log"):
        path = os.path.join(cube_dir, fn)
        if fn not in logs and os.path.isfile(path):
          logs[fn] = open(path, "r")
      for f in logs.values():
        x = f.read()
        if x:
          print(x, end='')
      if rc is not None:
        return rc
      if OV.GetVar("stop_current_process") or is_pause_break_pressed():
        print("NoSpherA2 aborted by INTERRUPT!")
        terminate_process_tree(p)
        OV.SetVar("stop_current_process", False)
        consume_interrupt_request()
        return -1
      if on_tick:
        on_tick()
      if gui:
        olx.Refresh()
      time.sleep(0.1)
  finally:
    for f in logs.values():
      f.close()
    if gui:
      OV.DeleteBitmap(bitmap)
      olx.Refresh()

def calculate_cubes():
  if is_disordered():
    print("Disordered structures not implemented!")
    return

  args, cwd = _source()
  if args is None:
    return
  Lap = nsa2_get_param('Property_Lap')
  Eli = nsa2_get_param('Property_Eli')
  Elf = nsa2_get_param('Property_Elf')
  RDG = nsa2_get_param('Property_RDG')
  ESP = nsa2_get_param('Property_ESP')
  ESP_surface = nsa2_get_param('Property_ESP_surface')
  MO = nsa2_get_param('Property_MO')
  ATOM = nsa2_get_param('Property_ATOM')
  DEF = nsa2_get_param('Property_DEF')
  all_MOs = nsa2_get_param('Property_all_MOs')
  Fukui = nsa2_get_param('Property_Fukui')
  if args[0] == "-xyz" and (Elf or RDG or MO or ATOM or DEF or Fukui):  # orbital properties need a wavefunction
    print("SALTED density: ELF, RDG, MOs, Fukui functions, atomic and static deformation densities need a wavefunction, skipped")
    Elf = RDG = MO = ATOM = DEF = Fukui = False
  if Lap:
    args.append("-lap")
  if Eli:
    args.append("-eli")
  if Elf:
    args.append("-elf")
  if RDG:
    args.append("-rdg")
  if ESP:
    args.append("-esp")
  if ESP_surface:
    args.append("-esp_isosurface")
    if not ESP:  # the rho + esp cubes give the same surface with the isovalue on the slider
      args.append("-esp")
  if ATOM:
    args.append("-HDEF")
  if DEF:
    args.append("-def")
  if Fukui:
    args.append("-fukui")
    # The Fukui functions need the LUMO, so the wavefunction file has to carry
    # virtual orbitals. A .gbw, .molden or .fchk does; a .wfx or .wfn written
    # with only the occupied orbitals does not, and NoSpherA2 will then report
    # that it found no frontier pair and skip. Warn here rather than let that
    # look like a silent failure of the checkbox.
    wfn_path = args[1]
    if wfn_path.endswith((".wfn", ".wfx", ".ffn")):
      print(f"Note: Fukui functions need virtual orbitals. '{os.path.basename(wfn_path)}' "
            "may only store the occupied ones - if no Fukui maps appear, check "
            "NoSpherA2_cube.log and re-run the wavefunction job so a .gbw or "
            ".molden is available.")
  if MO:
    args.append("-MO")
    if all_MOs:
      args.append("all")
    else:
      args.append(str(int(nsa2_get_param('Property_MO_number')) - 1))
  if _run_nsa2(args + _grid_args() + _cif_arg(), cwd=cwd) and ESP_surface:
    _stamp(False, _surface_obj("ESP surface"))
OV.registerFunction(calculate_cubes,False,'NoSpherA2')

SURFACE_RESOLUTION = 0.1  # Angstrom; 4x the faces of 0.2 and half the shape index jumps, 0.05 is 16x the faces for no further gain

NCI_RESOLUTION = 0.05  # Angstrom; NoSpherA2 only walks the box where the fragments overlap, so the fine grid is cheap

def _grid_args(box=False, surface=False, fine=False):
  # the box types need the intermolecular region around the molecule; the cell types leave every point further than
  # the radius from an atom at zero, and at 1 A an MO, the ESP and rho at 0.002 still carry 0.2, 0.4 and 0.005 there,
  # so their surfaces end on that voxelised rim; at 2.5 A the rim is below every default level. A Hirshfeld
  # surface is a mesh, not a cube, so it never goes finer than SURFACE_RESOLUTION; the intermolecular NCI
  # never goes coarser than NCI_RESOLUTION
  radius = str(max(float(nsa2_get_param('map.radius')), 2.5))
  resolution = nsa2_get_param('map.resolution')
  if surface:
    resolution = str(max(float(resolution), SURFACE_RESOLUTION))
  if fine:
    resolution = str(min(float(resolution), NCI_RESOLUTION))
  return ["-resolution", resolution, "-radius", radius]

def _grid_covers(have, want):
  # ["-resolution", r, "-radius", R] as _grid_args writes them: the same box, and points at least as dense
  if have == want:
    return True
  try:
    return float(have[3]) == float(want[3]) and float(have[1]) <= float(want[1]) + 1e-9
  except (IndexError, ValueError):
    return False

def _fresh(fn, box=False, surface=False, fine=False):
  # an on-demand product exists and its grid still answers what is asked: the same radius (the box has to match)
  # and a resolution that is not coarser. A finer cube or mesh stays valid for a coarser request - every point
  # asked for is in it - so turning the resolution down never recalculates. Turning it up does: refining a grid
  # only reuses the old points when the new step count is an exact multiple of the old one, and even then that
  # is 1/k**3 of the work (1/8 for a halved step), so there is nothing to salvage. The grid a product was made
  # on sits in <fn>.grid (no sidecar = made before this check, kept)
  if not os.path.isfile(fn):
    return False
  g = fn + ".grid"
  return not os.path.isfile(g) or _grid_covers(open(g).read().split(), _grid_args(box, surface, fine))

def _stamp(box, *fns, surface=False, fine=False):
  for fn in fns:
    with open(fn + ".grid", "w") as f:
      f.write(" ".join(_grid_args(box, surface, fine)))

# "Rho + ESP" and "Rho + ELI" are molecular box cubes (no -cif, no wrapping) in <cache>/box, computed on demand
BOX_TYPES = {"Rho + ESP": "-esp", "Rho + ELI": "-eli"}

def _box_cubes(Type):
  # the rho cube and the colour cube of a box type, running NoSpherA2 when they are missing
  args, cwd = _source()
  if args is None:
    return None
  d = _ensure(os.path.join(cwd, "box"))
  args[1] = os.path.join(d, os.path.basename(args[1]))  # NoSpherA2 writes next to its input, so the box gets a copy
  if not os.path.exists(args[1]):
    shutil.copy2(os.path.join(cwd, os.path.basename(args[1])), args[1])
  name = OV.ModelSrc()
  cubes = lambda: (_p(name + "_rho.cube", d), _p(name + BOX_TYPES[Type].replace("-", "_") + ".cube", d))
  if not all(_fresh(c, box=True) for c in cubes()):
    if not _run_nsa2(args + [BOX_TYPES[Type]] + _grid_args(box=True), wait=True, cwd=d):
      return None
    _stamp(True, *cubes())
  return cubes()  # resolved after the run: _p picks the .cubeb NoSpherA2 just wrote

# surfaces come as Wavefront obj in bohr; AddObject poly reads the face colours from the mtl
SURFACE_OBJS = {"ESP surface": "%s_rho_esp.obj", "Hirshfeld ESP": "Hirshfeld_surface_esp.obj",
                "Hirshfeld d_i": "Hirshfeld_surface_i.obj", "Hirshfeld d_e": "Hirshfeld_surface_e.obj",
                "Hirshfeld d_norm": "Hirshfeld_surface_norm.obj",
                "Hirshfeld shape index": "Hirshfeld_surface_i.obj", "Hirshfeld curvedness": "Hirshfeld_surface_i.obj",
                "Intermolecular NCI": "%s_hs_mol_%s_hs_env_nci.obj"}
# the Hirshfeld types share one geometry; Hirshfeld_surface.dat holds the property per face and the map colour
# controls set the ramp (default limits: d_i/d_e from the data, ESP symmetric, d_norm from the closest contact,
# shape index -1..1 and curvedness -4..0.4 as CrystalExplorer)
HS_COLUMNS = {"Hirshfeld d_i": "d_i", "Hirshfeld d_e": "d_e", "Hirshfeld d_norm": "d_norm", "Hirshfeld ESP": "esp",
              "Hirshfeld shape index": "shape_index", "Hirshfeld curvedness": "curvedness"}

# the surfaces of the displayed or selected molecule against its crystal environment, with a value per face
FRAG_SURFACES = set(HS_COLUMNS) | {"Intermolecular NCI"}

def _surface_obj(Type, d=None):
  return _p(SURFACE_OBJS[Type].replace("%s", OV.ModelSrc()), d or (_frag_dir() if Type in FRAG_SURFACES else None))

def _hs_values(Type):
  # the per-face column of a Hirshfeld type, None when the table (older NoSpherA2) or the column is missing;
  # the intermolecular NCI has sign(l2)rho per face in the .dat next to its obj
  if Type == "Intermolecular NCI":
    fn = _surface_obj(Type).replace(".obj", ".dat")
    return np.loadtxt(fn, ndmin=1) if os.path.isfile(fn) else None
  fn = _p("Hirshfeld_surface.dat", _frag_dir())
  if Type not in HS_COLUMNS or not os.path.isfile(fn):
    return None
  with open(fn) as f:
    names = f.readline().split()[1:]
  if HS_COLUMNS[Type] not in names:
    return None
  return np.loadtxt(fn, usecols=names.index(HS_COLUMNS[Type]), ndmin=1)

def _preview_surface(obj):
  # put a mesh on screen without touching the colour ramp or _state: it is a stand-in, not the answer. Two of them
  # are free - the stale coarser mesh still in the cache before a finer run starts, and the fresh shape the run
  # writes before it begins the per-face ESP, which is the long pole of every surface run
  if _state.get("hidden") or not os.path.isfile(obj):
    return
  olex_xgrid.SetVisible(False)
  olx.AddObject("poly", "nsa2_surface", 0, obj, s=0.529177, t=_alpha())
  olx.Refresh()

def _stage1_ticker(obj):
  # NoSpherA2 writes <obj>.stage1 once the shape is complete on disk; the flag of the previous run goes first so
  # the hook only fires on this one, and it fires once
  marker = obj + ".stage1"
  if os.path.isfile(marker):
    os.remove(marker)
  fired = []
  def tick():
    if not fired and os.path.isfile(marker):
      fired.append(True)
      _preview_surface(obj)
  return tick

def _show_surface(Type):
  olex_xgrid.SetVisible(False)  # one thing on screen: the surface replaces the map and vice versa
  values = _hs_values(Type)
  if values is None:
    olx.AddObject("poly", "nsa2_surface", 0, _surface_obj(Type), s=0.529177, t=_alpha())
    olx.Visible("nsa2_surface", "true")  # Kill only hides it, and AddObject reuses a hidden one by name
    _legend(False)
    return
  if _state.get("type") != Type:
    lo, hi = float(values.min()), float(values.max())
    if Type in ("Hirshfeld d_i", "Hirshfeld d_e"):
      hi *= 0.9
    elif Type == "Hirshfeld ESP":
      lo = -max(-lo, hi)
      hi = -lo
    elif Type == "Hirshfeld shape index":  # magenta = concave (-1), cyan = convex (+1)
      lo, hi = -1.0, 1.0
    elif Type == "Hirshfeld curvedness":  # magenta = flat, cyan = edges
      lo, hi = -4.0, 0.4
    elif Type == "Intermolecular NCI":  # NoSpherA2's vmd convention: BGR on sign(l2)rho, +-0.015 a.u.
      lo, hi = -0.015, 0.015
    else:  # d_norm as CrystalExplorer: red = closest contact, white at 0 (vdW contact), blue = the farthest point
      lo = min(lo, -0.1)
      hi = max(hi, 0.1)
    # red = close contact / negative potential, as CrystalExplorer; the shape descriptors get their own ramp
    nsa2_set_param('map.scale_name', "MYC" if Type in ("Hirshfeld shape index", "Hirshfeld curvedness")
                   else "BGR" if Type == "Intermolecular NCI" else "RWB")
    nsa2_set_param('map.scale_min', "%.4g" % lo)
    nsa2_set_param('map.scale_max', "%.4g" % hi)
    _state["type"] = Type
  colours = _p("nsa2_surface_colours.txt")
  np.savetxt(colours, _colors(values) & 0xFFFFFF, fmt="%d")
  olx.AddObject("poly", "nsa2_surface", 0, _surface_obj(Type), s=0.529177, f=colours, t=_alpha())
  olx.Visible("nsa2_surface", "true")
  _legend()

def map_shown():
  # the map controls apply to a visible grid, to a surface, and to either of them while hidden - it is loaded
  return (olx.xgrid.Visible() == "true" or _state.get("type") in SURFACE_OBJS
          or bool(_state.get("hidden")))
OV.registerFunction(map_shown,False,'NoSpherA2')

def alpha_applies():
  # the opacity knob bites where the colours carry the alpha: the coloured grids and the surface objs
  return is_colored() or nsa2_get_param('map.type') in SURFACE_OBJS
OV.registerFunction(alpha_applies,False,'NoSpherA2')

def map_hidden():
  return bool(_state.get("hidden"))
OV.registerFunction(map_hidden,False,'NoSpherA2')

def hide_map(hide="true"):
  # hide without dropping anything: the grid keeps its data and the surface object stays in the scene (the
  # picker skips invisible objects, so it stops catching the mouse), which makes showing it again instant -
  # Disable Map kills both and the next look has to re-read and re-triangulate the obj
  hide = str(hide).lower() not in ("false", "0", "no")
  if _state.get("type") in SURFACE_OBJS:
    olx.Visible("nsa2_surface", "false" if hide else "true")
    _legend(not hide and _state["type"] in FRAG_SURFACES)
  else:
    olex_xgrid.SetVisible(not hide)
  _state["hidden"] = hide
OV.registerFunction(hide_map,False,'NoSpherA2')

def disable_map():
  olex_xgrid.SetVisible(False)
  olx.Kill("nsa2_surface")
  _state["type"] = None
  _state["frag"] = None
  _state["hidden"] = False
OV.registerFunction(disable_map,False,'NoSpherA2')

def _selection():
  # the atoms selected with the mouse as (element, xyz in Angstrom), symmetry-generated ones included: sel(a)
  # names them (C11 C12_$2 ...) without touching the selection, the info table of those names gives the
  # coordinates (info with no names would read the selection but also clear it); [] with nothing selected
  sel = []
  try:
    names = olex.f("sel(a)")  # not available headless
  except Exception:
    names = ""
  out = olx.Info(*names.split(), f=True, p=8) if isinstance(names, str) and names.strip() else ""
  for l in (out if isinstance(out, str) else "").splitlines():
    t = l.split()
    try:
      if len(t) > 4 and t[1] != "Q":
        sel.append((("H" if t[1] in ("D", "T") else t[1]), [float(v) for v in t[2:5]]))
    except ValueError:
      pass
  return sel

def _frag_dir():
  # the product folder of the surface fragments: a selection gets its own, sel_<hash of the selected atoms>, under
  # the model's folder, and stays current until the map is switched off, so changing the surface type after a
  # click elsewhere does not fall back to the whole model
  base = _cache_dir(_wfn_file())
  sel = _selection()
  if sel:
    import hashlib
    key = hashlib.sha1("\n".join(sorted("%s %.3f %.3f %.3f" % (e, x[0], x[1], x[2]) for e, x in sel)).encode()).hexdigest()[:8]
    _state["frag"] = (base, "sel_" + key)
  frag = _state.get("frag")
  return os.path.join(base, frag[1]) if frag and frag[0] == base else base

def _crystal_env(X, reach):
  # every crystal atom within reach of the centroid of X that is not an atom of X, as (element, xyz) rows: the
  # asymmetric unit (disorder parts above 1 left out, as _structure does) under every symmetry operation and
  # lattice translation, duplicates from special positions dropped
  from crystal_energies import _structure, _cell_matrix
  cell, atoms, ops = _structure()
  M = _cell_matrix(cell)
  Minv = np.linalg.inv(M)
  F = np.array([a[2] for a in atoms])
  el = [("H" if a[1] in ("D", "T") else a[1]) for a in atoms]
  cent = X.mean(axis=0)
  fcent = cent @ Minv.T
  span = np.ceil(reach * np.linalg.norm(Minv, axis=1) + 0.5).astype(int)  # cells to walk per axis
  placed, rows = X, []
  for op in ops:
    op = np.array(op, dtype=float)
    G = F @ op[:, :3].T + op[:, 3]
    G -= np.floor(G - fcent + 0.5)  # each atom into the cell centred on the molecule
    for t in np.ndindex(*(2 * span + 1)):
      P = (G + t - span) @ M.T
      for i in np.nonzero(np.linalg.norm(P - cent, axis=1) <= reach)[0]:
        if np.min(np.linalg.norm(placed - P[i], axis=1)) >= 0.1:  # ponytail: O(n^2) overlap test, fine below 1e4 atoms
          placed = np.vstack([placed, P[i]])
          rows.append((el[i], P[i]))
  return rows

def _write_xyz(fn, rows, title):
  with open(fn, "w") as f:
    f.write("%d\n%s\n" % (len(rows), title))
    for e, x in rows:
      f.write("%-2s %14.8f %14.8f %14.8f\n" % (e, x[0], x[1], x[2]))

def _selection_wfn(mol):
  # the wavefunction of the selected molecule for the ESP colour, computed like the model's own (same source,
  # basis, method, charge and multiplicity) into the selection's folder; None when the model has no wavefunction,
  # the source cannot run on a plain xyz, or the calculation fails (the surface then has no ESP)
  if not _wfn_file():
    return None
  d, name = os.path.dirname(mol), OV.ModelSrc() + "_sel"
  found = lambda: next((os.path.join(d, name + e) for e in (".gbw", ".wfx", ".ffn", ".wfn", ".molden", ".xtb", ".fchk")
                        if os.path.isfile(os.path.join(d, name + e))), None)
  if found():
    return found()
  from utilities import software
  soft = software()
  if soft in ("Hybrid", "fragHAR", "OCC", "Thakkar IAM", "SALTED"):
    print("Hirshfeld ESP of a selection needs a wavefunction of the selection, which %s cannot compute: surface without ESP" % soft)
    return None
  import Wfn_Job
  from NoSpherA2.NoSpherA2 import NoSpherA2_instance
  shutil.copy(mol, os.path.join(d, name + ".xyz"))  # the job keeps an existing xyz instead of exporting the model
  try:
    job = Wfn_Job.wfn_Job(NoSpherA2_instance, name, d, soft)
    job.write_input(cover=False, embed=False)  # embedding would cluster the whole model, not the selection; ponytail: the model's charge and multiplicity; a selected ion of a salt needs its own
    job.run(copy=False)
  except Exception as e:
    print("Wavefunction of the selection failed, surface without ESP: %s" % e)
    return None
  for src, ext in (("molden.input", ".molden"), ("wfn.xtb", ".xtb"), ("Test.FChk", ".fchk")):  # what run(copy=True) renames
    if os.path.isfile(os.path.join(d, src)):
      shutil.move(os.path.join(d, src), os.path.join(d, name + ext))
  return found()

def _fragments():
  # the surface molecule and its crystal environment as xyz files in the product folder: the atoms selected with
  # the mouse (one molecule of a Z' > 1 or grown model) against every other atom of the crystal, else the
  # displayed model against its symmetry images
  from Wfn_Job import _crystal_cluster
  import numpy as np
  name = OV.ModelSrc()
  sel = _selection()
  folder = _ensure(_frag_dir())
  mol = os.path.join(folder, name + "_hs_mol.xyz")
  env = os.path.join(folder, name + "_hs_env.xyz")
  if os.path.isfile(mol) and os.path.isfile(env):
    return mol, env
  if sel:
    X = np.array([x for e, x in sel])
    rows = _crystal_env(X, np.max(np.linalg.norm(X - X.mean(axis=0), axis=1)) + 6.0)
    _write_xyz(mol, sel, "Selected molecule of %s" % name)
    _write_xyz(env, rows, "Environment of the selection: %d atoms" % len(rows))
    return mol, env
  olx.Kill("$Q")
  olx.File(mol, p=10)
  lines = open(mol).read().splitlines()
  X = np.array([[float(v) for v in l.split()[1:4]] for l in lines[2:2 + int(lines[0])]])
  reach = np.max(np.linalg.norm(X - X.mean(axis=0), axis=1)) + 6.0  # neighbours that can touch the surface
  n, nsub, el = _crystal_cluster(mol, env, reach)
  lines = open(env).read().splitlines()
  with open(env, "w") as f:  # the cluster without its first subunit, the molecule itself
    f.write("%d\nEnvironment of %s: %d neighbours\n" % (n * (nsub - 1), name, nsub - 1))
    f.write("\n".join(lines[2 + n:]) + "\n")
  return mol, env

def hirshfeld_surface(Type=None):
  # Hirshfeld surface of the displayed or the selected molecule against its crystal environment, ESP-coloured when
  # a wavefunction (of the selection: its own, see _selection_wfn) or a SALTED model gives a density
  model = None if _wfn_file() else _salted_model()
  Type = Type or ("Hirshfeld ESP" if _wfn_file() or model else "Hirshfeld d_norm")
  if not _fresh(_surface_obj(Type), surface=True):
    mol, env = _fragments()
    wfn = _selection_wfn(mol) if os.path.basename(os.path.dirname(mol)).startswith("sel_") else _cached_wfn()
    args = ["-hirshfeld_surface", wfn or mol, env] + (_salted_args(model) if model else [])
    shape = _surface_obj("Hirshfeld d_i")  # the geometry every Hirshfeld type shares, written before the ESP
    _preview_surface(shape)                # whatever the last run left: coarser, but on screen now
    if not _run_nsa2(args + _grid_args(surface=True), wait=True, cwd=os.path.dirname(mol),
                     on_tick=_stage1_ticker(shape)):
      return
    _stamp(False, *[_surface_obj(t) for t in HS_COLUMNS], surface=True)  # one run writes every Hirshfeld obj
  nsa2_set_param('map.type', Type)
  _show_surface(Type)
OV.registerFunction(hirshfeld_surface,False,'NoSpherA2')

def intermolecular_nci():
  # promolecular NCI between the displayed molecule and its crystal environment, coloured like NoSpherA2's vmd file
  # as a marching-cubes mesh (NoSpherA2's _nci.obj, the cubes stay for VMD)
  Type = "Intermolecular NCI"
  obj = _surface_obj(Type)
  if not _fresh(obj, box=True, fine=True):
    mol, env = _fragments()
    args = ["-promol_nci", mol, env] + _grid_args(box=True, fine=True)
    if not _run_nsa2(args, wait=True, cwd=os.path.dirname(mol)):
      return
    _stamp(True, obj, fine=True)
  nsa2_set_param('map.type', Type)
  _show_surface(Type)
OV.registerFunction(intermolecular_nci,False,'NoSpherA2')

def get_map_types():
  name = OV.ModelSrc()
  d = _cache_dir(_wfn_file())  # once, the structure hash walks every atom
  list = ";Residual<-diff;Deformation<-fcfmc;2Fo-Fc<-tomc;Fobs<-fobs;Fcalc<-fcalc;"
  if os.path.isfile(_p(name + "_eli.cube", d)):
    list += "ELI-D;"
  if os.path.isfile(_p(name + "_lap.cube", d)):
    list += "Laplacian;"
  if os.path.isfile(_p(name + "_elf.cube", d)):
    list += "ELF;"
  if os.path.isfile(_p(name+"_esp.cube", d)):
    list += "ESP;"
  for Type in SURFACE_OBJS:
    # the intermolecular NCI is computed on demand from the displayed molecule
    if os.path.isfile(_surface_obj(Type, d)) or (Type == "ESP surface" and has_density_source()) or Type == "Intermolecular NCI":
      list += Type + ";"
  if os.path.isfile(_p(name + "_rdg.cube", d)):
    list += "RDG;"
  if os.path.isfile(_p(name + "_def.cube", d)):
    list += "Stat. Def.;"
  if os.path.isfile(_p(name + "_rdg.cube", d)) and os.path.isfile(_p(name + "_signed_rho.cube", d)):
    list += "NCI;"
  # "Rho + ESP" / "Rho + ELI" still work via map.type, but are off the menu: the ESP and Hirshfeld surfaces replace them
  if os.path.isfile(_p(name + "_fukui_plus.cube", d)):
    list += "Fukui f+;"
  if os.path.isfile(_p(name + "_fukui_minus.cube", d)):
    list += "Fukui f-;"
  if os.path.isfile(_p(name + "_fukui_zero.cube", d)):
    list += "Fukui f0;"
  if os.path.isfile(_p(name + "_dual_descriptor.cube", d)):
    list += "Dual Descriptor;"
  from utilities import get_nmo, get_ncen
  nmo = get_nmo()
  if nmo != -1:
    exists = False
    for i in range(int(nmo) + 1):
      if os.path.isfile(_p(name+"_MO_"+str(i)+".cube", d)):
        exists = True
    if exists:
      list += "MO;"
  ncen = get_ncen()
  if ncen != -1:
    exists = False
    for i in range(int(ncen)+1):
      if os.path.isfile(_p(name + "_HDEF_" + str(i) + ".cube", d)):
        exists = True
    if exists:
      list += "HDEF;"
  if list == "":
    return "None;"
  return list
OV.registerFunction(get_map_types,False,'NoSpherA2')

_state = {}

def change_map():
  Type = nsa2_get_param('map.type')
  if Type == "None" or Type == "":
    return
  if Type not in SURFACE_OBJS:
    olx.Kill("nsa2_surface")
  name = OV.ModelSrc()
  if Type == "ELI-D":
    plot_cube(_p(name+"_eli.cube"),None)
  elif Type == "Laplacian":
    plot_cube(_p(name+"_lap.cube"),None)
  elif Type == "ELF":
    plot_cube(_p(name+"_elf.cube"),None)
  elif Type == "ESP":
    plot_cube(_p(name+"_esp.cube"),None)
  elif Type in SURFACE_OBJS:
    if Type == "ESP surface" and not _fresh(_surface_obj(Type)):
      args, cwd = _source()
      if args is None:
        return
      obj = _surface_obj(Type)
      _preview_surface(obj)  # the last run's isosurface, until this one has its own
      if not _run_nsa2(args + ["-esp_isosurface"] + _grid_args() + _cif_arg(), wait=True, cwd=cwd,
                       on_tick=_stage1_ticker(obj.replace(".obj", "_shape.obj"))):
        return
      _stamp(False, obj)
    elif Type in HS_COLUMNS and not _fresh(_surface_obj(Type), surface=True):
      hirshfeld_surface(Type)
      return
    elif Type == "Intermolecular NCI" and not _fresh(_surface_obj(Type), box=True, fine=True):
      intermolecular_nci()
      return
    _show_surface(Type)
  elif Type == "Stat. Def.":
    plot_cube(_p(name+"_def.cube"),None)
  elif Type == "NCI":
    nsa2_set_param('map.scale_name', "RGB")
    plot_cube(_p(name+"_rdg.cube"),_p(name+"_signed_rho.cube"))
  elif Type == "RDG":
    plot_cube(_p(name+"_rdg.cube"),None)
  elif Type in BOX_TYPES:
    cubes = _box_cubes(Type)
    if cubes is None:
      return
    if _state.get("type") != Type:  # ESP in a.u. around 0, ELI-D 1 = homogeneous electron gas
      nsa2_set_param('map.scale_name', "BWR")
      nsa2_set_param('map.scale_min', "-0.05" if Type == "Rho + ESP" else "1.0")
      nsa2_set_param('map.scale_max', "0.05" if Type == "Rho + ESP" else "2.0")
    plot_cube(cubes[0], cubes[1], box=True)
  elif Type == "Fukui f+":
    plot_cube(name+"_fukui_plus.cube",None)
  elif Type == "Fukui f-":
    plot_cube(name+"_fukui_minus.cube",None)
  elif Type == "Fukui f0":
    plot_cube(name+"_fukui_zero.cube",None)
  elif Type == "Dual Descriptor":
    # Signed field: positive marks electrophilic regions (open to nucleophilic
    # attack), negative nucleophilic ones. A diverging blue-white-red scale is
    # what makes that readable, so force it the way NCI/Rho+ESP force theirs.
    nsa2_set_param('map.scale_name', "BWR")
    plot_cube(name+"_dual_descriptor.cube",None)
  elif Type == "fcfmc" or Type == "diff" or Type == "tomc" or Type == "fobs" or Type == "fcalc":
    OV.SetVar('map_slider_scale',-50)
    nsa2_set_param('snum.map.type',Type)
    show_fft_map(float(nsa2_get_param('map.resolution')), map_type=Type)
    minimal = float(olx.xgrid.GetMin())
    maximal = float(olx.xgrid.GetMax())
    if -minimal > maximal:
      maximal = -minimal
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',maximal*50)
    olex.m("html.Update()")
  elif Type == "MO":
    number = int(nsa2_get_param('Property_MO_number')) -1
    plot_cube(_p(name+"_MO_"+str(number)+".cube"),None)
  elif Type == "HDEF":
    number = int(nsa2_get_param('Property_ATOM_number')) -1
    plot_cube(_p(name+"_HDEF_"+str(number)+".cube"),None)
  else:
    print("Sorry, no map type available or selected map type not correct!")
    return
  _state["type"] = Type
  if _state.get("hidden"):
    hide_map(False)
OV.registerFunction(change_map,False,'NoSpherA2')

def change_pointsize():
  PS = nsa2_get_param('gl_pointsize')
  olex.m('gl.PointSize ' + PS)
OV.registerFunction(change_pointsize,False,'NoSpherA2')

CUBEB_MAGIC = b"NSA2CUBE"
CUBEB_VERSION = 1

def _read_cubeb(name):
  # NoSpherA2's binary cube (cube.cpp): magic, uint32 version, uint32 offset of the values, int32 na, int32 size[3],
  # double origin[3], double vectors[3][3], two length-prefixed comments, na x (int32 Z, double xyz[3]), double values
  with open(name, "rb") as f:
    head = f.read(16)
    version, offset = struct.unpack("<II", head[8:16])
    if version != CUBEB_VERSION:
      raise ValueError("%s: binary cube version %d, this reader knows %d" % (name, version, CUBEB_VERSION))
    na = struct.unpack("<i", f.read(4))[0]
    dims = struct.unpack("<3i", f.read(12))
    origin = np.frombuffer(f.read(24), dtype="<f8")
    axes = np.frombuffer(f.read(72), dtype="<f8").reshape(3, 3)
    f.seek(offset)
    values = np.fromfile(f, dtype="<f8", count=int(np.prod(dims)))
  if values.size != np.prod(dims):
    raise ValueError("%s: %d values for a %s grid" % (name, values.size, dims))
  return values.reshape(dims), origin * a2b, axes * a2b

def _read_cube(name):
  # values (nx, ny, nz) in C order, origin and the three step vectors in Angstrom; text .cube or binary .cubeb
  with open(name, "rb") as f:
    if f.read(8) == CUBEB_MAGIC:
      return _read_cubeb(name)
  with open(name) as f:
    lines = f.readlines()
  na = int(lines[2].split()[0])
  head = [[float(v) for v in l.split()] for l in lines[2:6]]
  dims = tuple(int(h[0]) for h in head[1:])
  values = np.fromstring(" ".join(lines[6 + abs(na):]), dtype=np.float64, sep=" ")
  if values.size != np.prod(dims):
    raise ValueError("%s: %d values for a %s grid" % (name, values.size, dims))
  return values.reshape(dims), np.array(head[0][1:4]) * a2b, np.array([h[1:4] for h in head[1:]]) * a2b

# default isovalue per map type; others take 2/3 of the value span
DEFAULT_ISO = {"NCI": 0.5, "RDG": 0.5, "Intermolecular NCI": 0.5, "Rho + ESP": 0.002, "Rho + ELI": 0.002,
               "ELI-D": 1.65,  # 1.5 merged the basins into one blob; still low enough for the C-C and C-O bond basins
               "Laplacian": -0.5,  # negative: xgrid then draws -0.5 and +0.5, concentration and depletion
               "MO": -0.05,  # both phases; the 2/3 (|min|+|max|) default sits above the lobes and draws nothing
               "ELF": 0.85,  # 0.7 is one valence blob, 0.85 splits the C-H basins off (epoxide: 6 -> 10 domains)
               "ESP": -0.04,  # a.u., both signs: the nuclei reach 30, the lone-pair minimum is -0.07
               "Stat. Def.": -0.03}  # a.u., both signs: bond and lone-pair peaks, the core depletions

def plot_cube(name, color_cube, box=False):
  # box: the cube is a molecular box in Cartesian space, drawn as it is instead of wrapped into the cell
  if not os.path.isfile(name):
    print("Cube file does not exist!")
    return
  data, origin, axes = _read_cube(name)
  colors = None
  if color_cube is not None:
    data2 = _read_cube(color_cube)[0]
    if data2.shape != data.shape:
      print("Colour cube %s does not match the grid of %s" % (color_cube, name))
      return
    colors = _colors(data2).tobytes()
  dims = data.shape
  args = [dims, dims, data.tobytes(), 0]
  if colors is not None or box:
    args.append(colors if colors is not None else b"")
  if box:
    args.append(tuple(float(v) for v in np.concatenate([origin, axes.ravel()])))
  olex_xgrid.Import(*args)
  Type = nsa2_get_param('map.type')
  if Type == "Laplacian":
    OV.SetVar('map_min', 0)
    OV.SetVar('map_max', 40)
    OV.SetVar('map_slider_scale',40)
  elif Type == "ELI-D":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',60)
    OV.SetVar('map_slider_scale',20)
  elif Type == "ELF":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',40)
    OV.SetVar('map_slider_scale',40)
  elif Type == "ESP":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',50)
  elif Type in ("NCI", "RDG", "Intermolecular NCI"):  # slider 0..100 -> RDG 0..1
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  elif Type in BOX_TYPES:  # slider 0..100 -> rho 0..0.05 a.u.
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',2000)
  elif Type == "MO":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  elif Type == "HDEF":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  elif Type == "Stat. Def.":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale', 100)
  elif Type in ("Fukui f+", "Fukui f-", "Fukui f0", "Dual Descriptor"):
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  mi = float(data.min())
  ma = float(data.max())
  iso = DEFAULT_ISO.get(Type, (abs(mi) + abs(ma)) * 2 / 3)
  if Type in ("Fukui f+", "Fukui f-", "Fukui f0", "Dual Descriptor"):
    # The generic (|min|+|max|)*2/3 above assumes a roughly symmetric field, as
    # an MO amplitude is. These are not.
    #   f+, f-, f0 are non-negative, so min is 0 and the formula gives 2/3 of the
    #   maximum - a surface right at the very top of the distribution, showing
    #   almost nothing.
    #   The dual descriptor is signed but strongly asymmetric: f- routinely peaks
    #   several times higher than f+ because the LUMO is the more diffuse orbital
    #   (on sucrose, -0.076 against +0.014). The formula then lands ABOVE the
    #   positive maximum, so the electrophilic lobe silently never renders at all.
    # Scale to the smaller of the two extremes so both signs are present.
    extremes = [abs(v) for v in (mi, ma) if abs(v) > 0]
    if extremes:
      iso = 0.3 * min(extremes)
  nsa2_set_param('snum.xgrid.scale',"{:.4f}".format(iso))
  if OV.HasGUI():
    olex_xgrid.SetMinMax(mi, ma)
    olex_xgrid.SetSurfaceScale(iso)
    olex_xgrid.SetVisible(True)
    # no snum.map.mask here: it cuts voxel by voxel at 1.1 A from the atoms, and an MO lobe, the ESP or the
    # deformation density at their levels reach past that, so the whole surface became the mask's staircase;
    # a NoSpherA2 cube already stops at its own -radius
    olex_xgrid.InitSurface(not box, -100)
    _xgrid_transparent(colors is not None)
    if colors is not None:
      _legend()

OV.registerFunction(plot_cube,False,'NoSpherA2')

def plot_cube_single(name):
  if not os.path.isfile(name):
    print("Cube file does not exist!")
    return
  values = _read_cube(name)[0]
  data = flex.double(values.ravel())
  data.reshape(flex.grid(*values.shape))
  mmm = data.min_max_mean()
  rms = data.rms()

  gridding = data.accessor()
  type = isinstance(data, flex.int)
  olex_xgrid.Import(
    gridding.all(), gridding.focus(), data.copy_to_byte_str(), type)

  OV.SetVar('map_min', 0)
  OV.SetVar('map_max', 40)
  OV.SetVar('map_slider_scale', 100)
  del data
  print("Map Min = %.3f, Max = %.3f, RMS = %.3f"%(mmm.min,mmm.max,rms))
  if OV.HasGUI():
    olex_xgrid.SetMinMax(mmm.min, mmm.max)
    olex_xgrid.SetVisible(True)
    if nsa2_get_param('snum.map.mask'):
      olex_xgrid.InitSurface(True, 1.1)
    else:
      olex_xgrid.InitSurface(True, -100)
    iso = float(rms * 2.)
    olex_xgrid.SetSurfaceScale(iso)
    nsa2_set_param('snum.xgrid.scale', "{:.3f}".format(iso))
    olex.m("html.Update()")

OV.registerFunction(plot_cube_single,False,'NoSpherA2')

def save_map_cube(map_type, resolution):
  olex.m('CalcFourier -fcf -%s -r=%s'%(map_type,resolution))
  cctbx_adapter = OlexCctbxAdapter()
  xray_structure = cctbx_adapter.xray_structure()
  uc = xray_structure.unit_cell()
  temp = olex_xgrid.GetSize()
  size = [int(temp[0]),int(temp[1]),int(temp[2])]
  name = OV.ModelSrc()

  n_atoms = int(olx.xf.au.GetAtomCount())
  positions = [[float(0.0) for k in range(3)] for l in range(n_atoms)]
  cm = list(uc.orthogonalization_matrix())
  for i in range(9):
    cm[i] /= a2b
  cm = tuple(cm)
  for a in range(n_atoms):
    coord = olx.xf.au.GetAtomCrd(a)
    pos = olx.xf.au.Orthogonalise(coord).split(' ')
    positions[a] = [float(pos[0]) / a2b, float(pos[1]) / a2b, float(pos[2]) / a2b]

  vecs = [(cm[0] / (size[0] - 1), cm[1] / (size[1] - 1), cm[2] / (size[2] - 1)),
          (cm[3] / (size[0] - 1), cm[4] / (size[1] - 1), cm[5] / (size[2] - 1)),
          (cm[6] / (size[0] - 1), cm[7] / (size[1] - 1), cm[8] / (size[2] - 1))]

  print("start writing a %4d x %4d x %4d cube" % (size[0], size[1], size[2]))

  with open("%s_%s.cube" % (name, map_type), 'w') as cube:
    cube_header = textwrap.dedent(f"""\
      {map_type}-type map created by Olex2
      Model name: {name}
      {n_atoms:5d} {0:11.6f} {0:11.6f} {0:11.6f}
      {size[0]:5d} {vecs[0][0]:11.6f} {vecs[1][0]:11.6f} {vecs[2][0]:11.6f}
      {size[1]:5d} {vecs[0][1]:11.6f} {vecs[1][1]:11.6f} {vecs[2][1]:11.6f}
      {size[2]:5d} {vecs[0][2]:11.6f} {vecs[1][2]:11.6f} {vecs[2][2]:11.6f}""")
    cube.write(cube_header)
    for i in range(n_atoms):
      atom_type = olx.xf.au.GetAtomType(i)
      charge = 200
      for j in range(1, 104):
        if tiny_pse.table(j).symbol() == atom_type:
          charge = j
          break
      if charge == 200 and atom_type != "Q":
        print("ATOM NOT FOUND!")
      cube.write(f'\n{charge:5d} {charge:11.6f} {positions[i][0]:11.6f} '
                 f'{positions[i][1]:11.6f} {positions[i][2]:11.6f}')
    for x in range(size[0]):
      for y in range(size[1]):
        string = ""
        for z in range(size[2]):
          string += ("%13.5e" % olex_xgrid.GetValue(x,y,z))
          if (z+1) % 6 == 0 and (z+1) != size[2]:
            string += '\n'
        if (y != (size[1] - 1)):
          string += '\n'
        cube.write(string)
      if(x != (size[0] -1)):
        cube.write('\n')

    cube.close()

  print("Saved Fourier map successfully")

OV.registerFunction(save_map_cube, False, 'NoSpherA2')

def _alpha():
  # opacity of the surfaces, 0..1 (map.alpha); 1 = solid as before
  try:
    a = float(nsa2_get_param('map.alpha'))
  except (TypeError, ValueError):
    a = 0.5
  return min(max(a, 0.05), 1.0)

def _xgrid_transparent(on):
  # the isosurface only blends with sglmTransparent (0x400) on its material; flip that one bit and leave the
  # rest of the style alone - colour, shininess and the rest belong to the user (Edit Style)
  for p in ("+Surface", "-Surface"):
    try:
      m = olx.GetMaterial("XGrid.%s" % p)
    except Exception:
      return
    if not m or ';' not in m:
      return
    f = m.split(';')
    flags = int(f[0])
    f[0] = str((flags | 0x400) if on else (flags & ~0x400))
    if f[0] != m.split(';')[0]:
      olx.SetMaterial("XGrid.%s" % p, ';'.join(f))

# low, middle, high colour of each map scale, linear in between; the name read backwards is the reversed ramp
COLOUR_RAMPS = {"BWR": ((0, 0, 1), (1, 1, 1), (1, 0, 0)), "BGR": ((0, 0, 1), (0, 1, 0), (1, 0, 0)),
                "MYC": ((1, 0, 1), (1, 1, 0), (0, 1, 1))}

def _colors(values):
  # RGBA uint32 per point on the map colour scale between map.scale_min and map.scale_max, the alpha of a
  # transparent material comes from here (the surface objs get theirs from AddObject -t instead)
  lo = float(nsa2_get_param('map.scale_min'))
  hi = float(nsa2_get_param('map.scale_max'))
  scale = nsa2_get_param('map.scale_name')  # BWR = Blue White Red, BGR = Blue Green Red; RWB/RGB reversed
  # the middle colour sits at 0 when the limits straddle it (asymmetric min/max keep white = zero), else halfway
  mid = 0.0 if lo < 0.0 < hi else 0.5 * (lo + hi)
  v = np.asarray(values, dtype=np.float64)
  x = np.clip(np.where(v < mid, 0.5 * (v - lo) / (mid - lo), 0.5 + 0.5 * (v - mid) / (hi - mid)), 0.0, 1.0)
  if scale not in COLOUR_RAMPS and scale[::-1] in COLOUR_RAMPS:  # RWB, RGB, CYM: the reversed ramp
    x = 1 - x
    scale = scale[::-1]
  c0, c1, c2 = (np.array(c, dtype=np.float64) for c in COLOUR_RAMPS.get(scale, COLOUR_RAMPS["BWR"]))
  t = 2 * x[..., None]
  r, g, b = np.where(t <= 1, c0 + (c1 - c0) * t, c1 + (c2 - c1) * (t - 1)).T
  to8 = lambda c: (255 * c).astype(np.uint32)
  return (np.uint32(int(255 * _alpha() + 0.5)) << 24) | (to8(b) << 16) | (to8(g) << 8) | to8(r)

def _legend(show=True):
  # the current colour scale as a legend in the top right of the view (shift+drag moves it, the place is kept);
  # an Olex2 without olex_xgrid.SetLegend simply has none
  if not OV.HasGUI() or not hasattr(olex_xgrid, "SetLegend"):
    return
  if not show:
    olex_xgrid.SetLegend(b"", [])
    return
  lo = float(nsa2_get_param('map.scale_min'))
  hi = float(nsa2_get_param('map.scale_max'))
  c = _colors(np.linspace(hi, lo, 32))  # top row = maximum
  rgb = np.stack([c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF], axis=1).astype(np.uint8)
  olex_xgrid.SetLegend(rgb.tobytes(), ["%.3f" % v for v in np.linspace(hi, lo, 5)])

def get_color(value):
  return int(_colors([float(value)])[0])
OV.registerFunction(get_color,False,'NoSpherA2')

def is_colored():
  Type = nsa2_get_param('map.type')
  return Type in ("NCI", "Rho + ESP", "Rho + ELI", "Intermolecular NCI") or Type in HS_COLUMNS
OV.registerFunction(is_colored,False,'NoSpherA2')

def plot_fft_map(fft_map, peak_frac=None, level=None):
  # peak_frac: level at that fraction of the weaker extreme instead of 3.3 sigma - a residual's 3.3 sigma can sit
  # above both of its peaks and draw nothing
  # level: a fixed level in e/A^3 - sigma of a density map scales with the heaviest core and leaves only the cores
  if fft_map is None:
    print("The Calculation of Maps was unsuccesfull, aborting")
    return
  data = fft_map.real_map_unpadded()
  gridding = data.accessor()
  type = isinstance(data, flex.int)
  olex_xgrid.Import(
    gridding.all(), gridding.focus(), data.copy_to_byte_str(), type)
  statistics = fft_map.statistics()
  min_v = statistics.min()
  max_v = statistics.max()
  sigma = statistics.sigma()
  del data
  if OV.HasGUI():
    olex_xgrid.SetMinMax(min_v, max_v)
    olex_xgrid.SetVisible(True)
    mask = nsa2_get_param('snum.map.mask')
    if mask:
      olex_xgrid.InitSurface(True, 1.1)
    else:
      olex_xgrid.InitSurface(True, -100)
    iso = float(-sigma*3.3) if peak_frac is None else float(-peak_frac*min(max_v, -min_v))  # negative: both signs
    if level is not None:
      iso = -abs(float(level))  # negative: density in the positive (green) colour; a positive scale draws it red
    olex_xgrid.SetSurfaceScale(iso)
  print("Map max val %.3f min val %.3f RMS: %.3f"%(max_v,min_v,sigma))
  print("Map size: %d x %d x %d"%(fft_map.n_real()[0],fft_map.n_real()[1],fft_map.n_real()[2]))

OV.registerFunction(plot_fft_map, False, 'NoSpherA2')

def SetSurface(iso):
    try:
        iso = float(iso)
    except:
        print("Invalid iso value!")
        return
    if OV.HasGUI():
        olex_xgrid.SetSurfaceScale(iso)

OV.registerFunction(SetSurface, False, 'NoSpherA2')

def plot_map(data, iso, dist=1.0, min_v=0, max_v=20):
  if not OV.HasGUI():
    return
  gridding = data.accessor()
  type = isinstance(data, flex.int)
  olex_xgrid.Import(
    gridding.all(), gridding.focus(), data.copy_to_byte_str(), type)
  olex_xgrid.SetMinMax(min_v, max_v)
  mask = nsa2_get_param('snum.map.mask')
  if mask == True:
    olex_xgrid.InitSurface(True, dist)
  else:
    olex_xgrid.InitSurface(True, -100)
  OV.SetVar('map_min', min_v)
  OV.SetVar('map_max', max_v)
  OV.SetVar('map_slider_scale', -max_v/2)
  olex.m("xgrid.RenderMode(line)")
  olex_xgrid.SetSurfaceScale(iso)
  olex_xgrid.SetVisible(True)


def write_map_to_cube(fft_map, map_name: str, size: tuple = (), binary: bool = False) -> None:
  # binary=True writes <model>_<map>.cubeb (NoSpherA2 reads both; NoSpherA2 -cube_convert makes the text .cube)
  cctbx_adapter = OlexCctbxAdapter()
  xray_structure = cctbx_adapter.xray_structure()
  uc = xray_structure.unit_cell()
  try:
    values = fft_map.real_map_unpadded()
    temp = values.focus()
  except:
    values = fft_map
    temp = size
  size = [int(t) for t in temp[0:3]]
  model_name = OV.ModelSrc()

  n_atoms = int(olx.xf.au.GetAtomCount())
  positions = [[0., 0., 0.] for _ in range(n_atoms)]
  cm = list(uc.orthogonalization_matrix())
  for i in range(9):
    cm[i] /= a2b
  cm = tuple(cm)
  nat = n_atoms
  for a in range(nat):
    if olx.xf.au.GetAtomType(a) == 'Q':
      n_atoms -= 1
      continue
    position = olx.xf.au.Orthogonalise(olx.xf.au.GetAtomCrd(a)).split(' ')
    positions[a] = [float(position[i]) / a2b for i in range(3)]

  vecs = [(cm[0] / (size[0]), cm[1] / (size[1]), cm[2] / (size[2])),
          (cm[3] / (size[0]), cm[4] / (size[1]), cm[5] / (size[2])),
          (cm[6] / (size[0]), cm[7] / (size[1]), cm[8] / (size[2]))]

  charges = []
  for i in range(n_atoms):
    atom_type = olx.xf.au.GetAtomType(i)
    charge = 200
    for j in range(1, 104):
      if tiny_pse.table(j).symbol() == atom_type:
        charge = j
        break
    if charge == 200 and atom_type != "Q":
      print("ATOM NOT FOUND!")
    charges.append(charge)

  print(f'Started writing a {size[0]:4d} x {size[1]:4d} x {size[2]:4d} cube')
  if binary:
    # the layout of _read_cubeb; the map is C-ordered x, y, z like the text cube
    if hasattr(values, "as_numpy_array"):
      values = values.as_numpy_array()
    values = np.ascontiguousarray(np.asarray(values, dtype="<f8").ravel()[:size[0] * size[1] * size[2]])
    comments = (f"{map_name}-type map created by Olex2".encode(), f"Model name: {model_name}".encode())
    header = struct.pack("<4i", n_atoms, *size) + struct.pack("<3d", 0.0, 0.0, 0.0)
    header += struct.pack("<9d", *(vecs[k][i] for i in range(3) for k in range(3)))  # row i = grid axis i, as the text lines
    for c in comments:
      header += struct.pack("<I", len(c)) + c
    for i in range(n_atoms):
      header += struct.pack("<i3d", charges[i], *positions[i])
    with open(f'{model_name}_{map_name}.cubeb', 'wb') as cube:
      cube.write(CUBEB_MAGIC + struct.pack("<II", CUBEB_VERSION, 16 + len(header)) + header)
      values.tofile(cube)
      print(f'Saved {map_name}-type map as {os.path.realpath(cube.name)}')
    return
  with open(f'{model_name}_{map_name}.cube', 'w') as cube:
    cube_header = textwrap.dedent(f"""\
      {map_name}-type map created by Olex2
      Model name: {model_name}
      {n_atoms:5d} {0:11.6f} {0:11.6f} {0:11.6f}
      {size[0]:5d} {vecs[0][0]:11.6f} {vecs[1][0]:11.6f} {vecs[2][0]:11.6f}
      {size[1]:5d} {vecs[0][1]:11.6f} {vecs[1][1]:11.6f} {vecs[2][1]:11.6f}
      {size[2]:5d} {vecs[0][2]:11.6f} {vecs[1][2]:11.6f} {vecs[2][2]:11.6f}""")
    cube.write(cube_header)

    for i in range(n_atoms):
      charge = charges[i]
      cube.write(f'\n{charge:5d} {charge:11.6f} {positions[i][0]:11.6f} '
                 f'{positions[i][1]:11.6f} {positions[i][2]:11.6f}')
    cube.write('\n')
    # one %-format per block of z-lines instead of one f-string per value:
    # same text (six to a line, a z-line never spans two)
    if hasattr(values, "as_numpy_array"):
      values = values.as_numpy_array()
    rows = np.asarray(values, dtype=float).ravel()[:size[0] * size[1] * size[2]].reshape(-1, size[2])
    row_fmt = ('%13.5e' * 6 + '\n') * (size[2] // 6)
    if size[2] % 6:
      row_fmt += '%13.5e' * (size[2] % 6) + '\n'
    block = max(1, 200000 // size[2])
    for i in range(0, rows.shape[0], block):
      chunk = rows[i:i + block]
      cube.write((row_fmt * chunk.shape[0]) % tuple(chunk.ravel().tolist()))
    print(f'Saved {map_name}-type map as {os.path.realpath(cube.name)}')


def f_calc_no_dispersion(cctbx_adapter, miller_set, table_name=None):
  """ F(calc) on miller_set without f' and f'': a map is an electron density.

  A copy of the structure with fp = fdp = 0 (both evaluators add the
  scatterers' fp/fdp on top of the spherical or tabulated form factor), with
  the same extinction as get_fo_sq_fc applies. The DispRadial falloff only
  scales f'/f'' and so drops out with them.
  None if this cctbx cannot evaluate the table: the caller keeps the
  dispersive arrays, as before this existed.
  """
  xs = cctbx_adapter.xray_structure().deep_copy_scatterers()
  for sc in xs.scatterers():
    sc.fp = 0
    sc.fdp = 0
  if not table_name:
    # plain cctbx, as get_fo_sq_fc does it: works on master cctbx too
    fc = miller_set.structure_factors_from_scatterers(xs, algorithm="direct").f_calc()
  else:
    try:
      from cctbx_olex_adapter import get_table_contribution
      one_h = direct.f_calc_modulus_squared(
        xs, scatterer_contribution=get_table_contribution(xs, table_name))
    except Exception as e:  # master cctbx has no scatterer_contribution keyword
      print("Map keeps f'/f'': no table-based F(calc) in this cctbx (%s)" % e)
      return None
    evaluate_many = getattr(one_h, "evaluate_many", None)
    if evaluate_many is not None:
      data = evaluate_many(miller_set.indices())
    else:  # master cctbx: one reflection at a time
      data = flex.complex_double()
      for mi in miller_set.indices():
        one_h.evaluate(mi)
        data.append(one_h.f_calc)
    fc = miller_set.array(data=data)
  if cctbx_adapter.exti is not None:
    fc = fc.apply_shelxl_extinction_correction(cctbx_adapter.exti, cctbx_adapter.wavelength)
  return fc

def without_dispersion(cctbx_adapter, f_sq_obs, f_calc, f_mask=None, table_name=None):
  """ Fo^2 and Fc with the anomalous dispersion taken out, for Fourier maps.

  f_calc is the refinement's Fc (with dispersion, and with f_mask if given).
  Fc is recomputed without f'/f''; Fo^2 has no such switch and is rescaled by
  |Fc_nd/Fc|^2, sigmas alike (the XD convention). Bijvoet mates then agree up
  to noise; the real part of the FFT averages them, so they are not merged.
  """
  fc = f_calc_no_dispersion(cctbx_adapter, f_calc, table_name)
  if fc is None:
    return f_sq_obs, f_calc
  if f_mask:
    fc = fc.array(data=fc.data() + f_mask.data())
  old = flex.norm(f_calc.data())
  new = flex.norm(fc.data())
  zero = old == 0
  old.set_selected(zero, 1)
  new.set_selected(zero, 1)
  r = new / old
  sigmas = f_sq_obs.sigmas()
  f_sq_obs = f_sq_obs.customized_copy(data=f_sq_obs.data() * r,
                                      sigmas=None if sigmas is None else sigmas * r)
  return f_sq_obs, fc

def residual_map(resolution=0.1,return_map=False,print_peaks=False,binary=False):
  cctbx_adapter = OlexCctbxAdapter()
  xray_structure = cctbx_adapter.xray_structure()
  hklf_code = cctbx_adapter.hklf_code
  use_tsc = OV.IsNoSpherA2()
  one_h = None
  table_name = None
  if use_tsc:
    table_name = str(nsa2_get_param("file"))
    print("Calculating Structure Factors from files...")
    if not os.path.exists(table_name):
      print("Error! Form factor file does not exist!")
      return
    from cctbx_olex_adapter import get_table_contribution
    one_h = direct.f_calc_modulus_squared(
        xray_structure, scatterer_contribution=get_table_contribution(
          xray_structure, table_name))
    if not OV.IsEDRefinement():
      if hklf_code == 2:
        f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h, merge=False)
        f_sq_obs = f_sq_obs.customized_copy(
          space_group_info=sgtbx.space_group_info(cctbx_adapter.space_group))
        f_sq_obs = f_sq_obs.merge_equivalents(algorithm="shelx").array().map_to_asu()
        f_calc = f_calc.customized_copy(crystal_symmetry=f_sq_obs.crystal_symmetry())
        f_calc = f_calc.common_set(f_sq_obs)
        if f_calc.size() != f_sq_obs.size():
          f_sq_obs = f_sq_obs.common_set(f_calc)
      else:
        f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
  else:
    print("Non NoSpherA2 map...")
    if hklf_code == 2:
      f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(merge=False)
      f_sq_obs = f_sq_obs.customized_copy(
        space_group_info=sgtbx.space_group_info(cctbx_adapter.space_group))
      f_sq_obs = f_sq_obs.merge_equivalents(algorithm="shelx").array().map_to_asu()
      f_calc = f_calc.customized_copy(crystal_symmetry=f_sq_obs.crystal_symmetry())
      f_calc = f_calc.common_set(f_sq_obs)
      if f_calc.size() != f_sq_obs.size():
        f_sq_obs = f_sq_obs.common_set(f_calc)
    else:
      f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()

  if not OV.IsEDRefinement():
    f_mask = None
    if OV.GetParam("snum.refinement.use_solvent_mask"):
      f_mask = cctbx_adapter.load_mask()
      if not f_mask:
        OlexCctbxMasks()
        if olx.current_mask.flood_fill.n_voids() > 0:
          f_mask = olx.current_mask.f_mask()
      if f_mask:
        if not f_sq_obs.space_group().is_centric() and f_sq_obs.anomalous_flag():
          f_mask = f_mask.generate_bijvoet_mates()
        f_mask = f_mask.common_set(f_sq_obs)
        f_calc = f_calc.array(data=(f_calc.data() + f_mask.data()))
    f_sq_obs, f_calc = without_dispersion(cctbx_adapter, f_sq_obs, f_calc, f_mask, table_name)
    f_obs = f_sq_obs.f_sq_as_f()
    if hklf_code == 2:
      fc2_data = flex.norm(f_calc.data())
      weights = cctbx_adapter.compute_weights(
        f_sq_obs, f_calc, fc2_data=fc2_data, reset_scale_factor=True)
      scale = flex.sum(weights * f_sq_obs.data() * fc2_data) / \
              flex.sum(weights * flex.pow2(fc2_data))
      scale = scale ** 0.5
    else:
      k = OV.GetOSF()
      if k is None:
        print("Error! Overall scale factor is not set! Using 1.0 as default.")
        k = 1.0
      scale = k ** 0.5
    f_diff = f_obs.f_obs_minus_f_calc(1.0/ scale, f_calc)
    if OV.IsEDData():
      f_diff = f_diff.apply_scaling(factor=3.324943664)
    f_diff = f_diff.expand_to_p1()
  else:
    I_obs, I_calc = OV.GetACI().EDI.compute_Io_Ic(merge=True)
    f_calc = cctbx_adapter.f_calc(I_obs, None, True, False,
                       one_h_function=one_h, twin_data=False)
    f_obs = I_obs.f_sq_as_f()
    new_data = []
    for i in range(I_obs.size()):
      mfc = math.sqrt(I_calc.data()[i])
      if mfc == 0:
        s = 1
      else:
        s = abs(f_calc.data()[i])/mfc
      fo = f_obs.data()[i] * s
      new_data.append(fo)
    f_obs = f_obs.customized_copy(data=flex.double(new_data))
    #re-compute the scale
    fo2 = f_obs.as_intensity_array()
    f_calc_sq = f_calc.as_intensity_array()
    weights = cctbx_adapter.compute_weights(fo2, f_calc, fc2_data=f_calc_sq.data(), reset_scale_factor=True)
    scale = flex.sum(weights * fo2.data() * f_calc_sq.data()) \
            / flex.sum(weights * flex.pow2(f_calc_sq.data()))
    #
    f_diff = f_obs.f_obs_minus_f_calc(1. / scale**0.5 , f_calc)
    f_diff = f_diff.apply_scaling(factor=3.324943664)
    f_diff = f_diff.expand_to_p1()

  print("Using %d reflections for Fourier synthesis"%f_diff.size())
  diff_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                            resolution_factor=1,grid_step=float(resolution)).apply_volume_scaling()
  if print_peaks == True or print_peaks == "True":
    from cctbx import maptbx
    max_peaks=10
    peaks = diff_map.peak_search(
      parameters=maptbx.peak_search_parameters(
        peak_search_level=2,
        interpolate=False,
        min_distance_sym_equiv=1.0,
        max_clusters=max_peaks+len(xray_structure.scatterers())),
      verify_symmetry=True
      ).all()
    i = 0
    olx.Kill('$Q', au=True) #HP-JUL18 -- Why kill the peaks? -- cause otherwise they accumulate! #HP4/9/18
    for xyz, height in zip(peaks.sites(), peaks.heights()):
      if i < max_peaks:
        a = olx.xf.uc.Closest(*xyz).split(' ')
        if OV.IsEDData():
          pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A, %.3f A away from %s"
        else:
          pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A^3, %.3f A away from %s" % (
            i + 1, xyz[0], xyz[1], xyz[2], height, float(a[1]), a[0])
        print(pi)
      id = olx.xf.au.NewAtom("%.2f" %(height), *xyz)
      if id != '-1':
        olx.xf.au.SetAtomU(id, "0.06")
        i = i+1
      if i == 100 or i >= max_peaks:
        break
    if OV.HasGUI():
      basis = olx.gl.Basis()
      frozen = olx.Freeze(True)
    olx.xf.EndUpdate(True) #clear LST
    olx.Compaq(q=True)
    if OV.HasGUI():
      olx.gl.Basis(basis)
      olx.Freeze(frozen)
  if return_map == True:
    return diff_map
  write_map_to_cube(diff_map, "diff", binary=binary in (True, "True"))

OV.registerFunction(residual_map, False, "NoSpherA2")

def _fcalc_read_xyz_records(xyz_path):
  with open(xyz_path, 'r') as xyz_file:
    lines = xyz_file.readlines()
  n_atoms = int(lines[0].strip())
  atom_lines = lines[2:2+n_atoms]
  records = []
  for line in atom_lines:
    parts = line.split()
    if len(parts) < 4:
      raise ValueError("Invalid xyz atom line in %s: %s" % (xyz_path, line.rstrip()))
    records.append((parts[0], float(parts[1]), float(parts[2]), float(parts[3]), parts[4:]))
  if len(records) != n_atoms:
    raise ValueError("Expected %d atoms in %s, found %d" % (n_atoms, xyz_path, len(records)))
  return lines[:2], records

def _fcalc_build_bond_graph(olx_atoms, n_atoms):
  graph = [set() for _ in range(n_atoms)]
  if len(olx_atoms) != n_atoms:
    raise ValueError("Olex model has %d atoms, xyz file has %d atoms" % (len(olx_atoms), n_atoms))
  for i, atom in enumerate(olx_atoms):
    for neighbour in atom.get('neighbours', ()):
      j = neighbour[0] if isinstance(neighbour, tuple) else neighbour
      if 0 <= j < n_atoms and j != i:
        graph[i].add(j)
        graph[j].add(i)
  return [tuple(sorted(neighbours)) for neighbours in graph]

def _fcalc_minimum_image_delta(a, b):
  return tuple((b[i] - a[i]) - math.floor((b[i] - a[i]) + 0.5) for i in range(3))

def _fcalc_compact_xyz_records(records, unit_cell, bond_graph):
  frac_sites = [
    unit_cell.fractionalize((x, y, z))
    for _element, x, y, z, _tail in records
  ]
  compact_frac = [None] * len(records)
  compact_cart = [None] * len(records)
  for root in range(len(records)):
    if compact_frac[root] is not None:
      continue
    component = []
    queue = [root]
    compact_frac[root] = tuple(frac_sites[root])
    while queue:
      i = queue.pop(0)
      component.append(i)
      for j in bond_graph[i]:
        if compact_frac[j] is None:
          delta = _fcalc_minimum_image_delta(frac_sites[i], frac_sites[j])
          compact_frac[j] = tuple(compact_frac[i][k] + delta[k] for k in range(3))
          queue.append(j)
    centroid = tuple(
      sum(compact_frac[i][k] for i in component) / len(component)
      for k in range(3)
    )
    shift = tuple(math.floor(centroid[k]) for k in range(3))
    for i in component:
      compact_frac[i] = tuple(compact_frac[i][k] - shift[k] for k in range(3))
  for i, frac in enumerate(compact_frac):
    compact_cart[i] = unit_cell.orthogonalize(frac)
  return compact_frac, compact_cart

def _fcalc_write_compact_xyz(xyz_path, header_lines, records, compact_cart, keep_mask=None):
  if keep_mask is None:
    keep_mask = [True] * len(records)
  header_lines = list(header_lines)
  header_lines[0] = "%d\n" % sum(1 for keep in keep_mask if keep)
  with open(xyz_path, 'w') as out:
    out.writelines(header_lines)
    for keep, (element, _x, _y, _z, tail), xyz in zip(keep_mask, records, compact_cart):
      if not keep:
        continue
      tail_text = (" " + " ".join(tail)) if tail else ""
      out.write("%-2s %16.8f %16.8f %16.8f%s\n" % (
        element, xyz[0], xyz[1], xyz[2], tail_text))

def _fcalc_connected_components(bond_graph, n_atoms):
  seen = [False] * n_atoms
  components = []
  for root in range(n_atoms):
    if seen[root]:
      continue
    comp = []
    stack = [root]
    seen[root] = True
    while stack:
      i = stack.pop()
      comp.append(i)
      for j in bond_graph[i]:
        if not seen[j]:
          seen[j] = True
          stack.append(j)
    components.append(comp)
  return components

def _fcalc_solvent_mask(records, bond_graph):
  """Flag atoms whose bonded component contains no C and no N (waters, ions):
  these are treated as solvent and excluded from the structure-factor sum."""
  n = len(records)
  is_solvent = [False] * n
  for comp in _fcalc_connected_components(bond_graph, n):
    elements = {records[i][0].strip() for i in comp}
    if ('C' not in elements) and ('N' not in elements):
      for i in comp:
        is_solvent[i] = True
  return is_solvent

def _fcalc_reference_mean_frac(sites_frac, keep_mask):
  kept = [sites_frac[i] for i in range(len(sites_frac)) if keep_mask[i]] or list(sites_frac)
  n = len(kept)
  return tuple(sum(s[k] for s in kept) / n for k in range(3))

def _fcalc_remove_drift(compact_frac, keep_mask, ref_mean):
  """Remove the net rigid translation of the cell contents relative to a fixed
  reference (lattice-preserving), so the coherent average <F> is not dephased."""
  kept = [compact_frac[i] for i in range(len(compact_frac)) if keep_mask[i]] or list(compact_frac)
  n = len(kept)
  mean = tuple(sum(s[k] for s in kept) / n for k in range(3))
  shift = tuple(mean[k] - ref_mean[k] for k in range(3))
  return [tuple(fc[k] - shift[k] for k in range(3)) for fc in compact_frac]

def _fcalc_apply_swat_correction(f_calc, swat):
  if swat is None:
    return f_calc
  g, U = swat
  # shelxl_SWAT_correction is the Fc^2 multiplier; complex Fc needs sqrt().
  correction = flex.sqrt(f_calc.shelxl_SWAT_correction(g, U))
  return f_calc.customized_copy(data=f_calc.data() * correction)

def _fcalc_with_xray_structure(cctbx_adapter, xray_structure, miller_set, one_h_function=None):
  original_xray_structure = cctbx_adapter._xray_structure
  try:
    cctbx_adapter._xray_structure = xray_structure
    return cctbx_adapter.f_calc(miller_set, one_h_function=one_h_function)
  finally:
    cctbx_adapter._xray_structure = original_xray_structure

def _fcalc_bool(value):
  if isinstance(value, bool):
    return value
  if isinstance(value, str):
    value = value.strip().lower()
    if value in ('1', 'true', 't', 'yes', 'y', 'on'):
      return True
    if value in ('0', 'false', 'f', 'no', 'n', 'off'):
      return False
  return bool(value)

def _fcalc_select_files(file_list, frame_selector):
  if frame_selector is None:
    return file_list
  selector = str(frame_selector).strip()
  if not selector or selector.lower() in ('all', '*'):
    return file_list
  if ',' in selector:
    selected = []
    seen = set()
    for part in selector.split(','):
      for file_name in _fcalc_select_files(file_list, part):
        if file_name not in seen:
          selected.append(file_name)
          seen.add(file_name)
    return selected
  if ':' in selector:
    parts = selector.split(':')
    if 2 <= len(parts) <= 3:
      start = int(parts[0]) if parts[0] else None
      stop = int(parts[1]) if parts[1] else None
      step = int(parts[2]) if len(parts) == 3 and parts[2] else None
      return file_list[slice(start, stop, step)]
  if selector.lstrip('-').isdigit():
    index = int(selector)
    try:
      return [file_list[index]]
    except IndexError:
      raise ValueError("Frame index %d is outside the %d available xyz files" % (index, len(file_list)))
  matches = [
    file_name for file_name in file_list
    if file_name == selector or os.path.splitext(file_name)[0] == selector
  ]
  if not matches:
    raise ValueError("Frame selector '%s' did not match any xyz file" % selector)
  return matches

def _fcalc_reference_cif_path(folder):
  cif_path = os.path.join(folder, OV.FileName() + ".cif")
  if os.path.exists(cif_path):
    return cif_path
  olex.m("CifCreate_4NoSpherA2")
  generated_cif = os.path.join(folder, OV.FileName() + ".cif_NoSpherA2")
  if os.path.exists(generated_cif):
    return generated_cif
  raise FileNotFoundError(
    "Could not find or generate %s or %s for NoSpherA2 Fcalc" %
    (cif_path, generated_cif))

def Fcalc(non_spherical:bool = False, zero_adp:bool = True,
          remove_drift:bool = True, skip_solvent:bool = True, residual_B:float = 0.0,
          frame_selector = None, write_spherical:bool = True, ncpus = 20,
          overwrite:bool = True, salted_model = None):
  # zero_adp:     drop the deposited ADPs so the MD ensemble alone supplies the
  #               Debye-Waller smearing (otherwise the displacement is double-counted).
  # remove_drift: remove the per-frame rigid translation of the cell contents so the
  #               coherent average <F> over frames is not dephased.
  # skip_solvent: remove waters/ions (bonded components with no C or N) from the
  #               SALTED table model and structure-factor sum.
  # residual_B:   optional small isotropic B (A^2) for sub-frame motion; 0 = none.
  zero_adp = _fcalc_bool(zero_adp)
  remove_drift = _fcalc_bool(remove_drift)
  skip_solvent = _fcalc_bool(skip_solvent)
  write_spherical = _fcalc_bool(write_spherical)
  overwrite = _fcalc_bool(overwrite)
  cctbx_adapter = OlexCctbxAdapter()
  olx.Kill('$Q', au=True)
  uc = cctbx_adapter._xray_structure.unit_cell()
  from cctbx.array_family import flex
  res_u = float(residual_B) / (8.0 * math.pi * math.pi)
  
  d2 = olex_core.GetHklStat()
  hkl_min = list(d2['FileMinIndices'])
  hkl_max = list(d2['FileMaxIndices'])
  miller_indices = flex.miller_index()
  for h in flex.nested_loop(hkl_min, hkl_max, open_range=False):
    if h == (0, 0, 0):
      continue
    miller_indices.append(h)

  miller_set = miller.set(
      crystal_symmetry=cctbx_adapter._xray_structure.crystal_symmetry(),
      indices=miller_indices,
      anomalous_flag=False)

  #Get a list of all .xyz files in the current structure folder that matches _XXXX.xyz
  file_list = sorted(
    f for f in os.listdir(OV.FilePath())
    if f.endswith('.xyz') and (OV.FileName()+"_") in f and not f.endswith("_compact.xyz")
  )
  if not file_list:
    print("No .xyz files found in the current structure folder.")
    return
  file_list = _fcalc_select_files(file_list, frame_selector)
  if not file_list:
    print("Frame selector produced an empty xyz file list.")
    return
  print("Fcalc will process %d xyz frame(s)" % len(file_list))

  if ncpus is not None and str(ncpus).strip() != "":
    nsa2_set_param('ncpus', int(ncpus))
  bond_graph = None

  for file in file_list:
    base_name = os.path.splitext(file)[0]
    salted_hkl_path = os.path.join(OV.FilePath(), base_name + ".SALTED_syn_hkl")
    spherical_hkl_path = os.path.join(OV.FilePath(), base_name + ".syn_hkl")
    if not overwrite and os.path.exists(salted_hkl_path) and (not write_spherical or os.path.exists(spherical_hkl_path)):
      print("Skipping %s because output already exists" % file)
      continue

    from utilities import cuqct_tsc
    # Calculate structure factors using non-spherical scattering factors
    print("NoSpherA2 based calculation")
    NoSpherA2_cif = base_name + "_work.cif"
    folder = OV.FilePath()
    NoSpherA2_cif_path = os.path.join(folder, NoSpherA2_cif)
    compact_xyz = base_name + "_compact.xyz"
    compact_xyz_path = os.path.join(folder, compact_xyz)
    shutil.copy(_fcalc_reference_cif_path(folder), NoSpherA2_cif_path)
    xyz_header, xyz_records = _fcalc_read_xyz_records(os.path.join(folder, file))
    if bond_graph is None:
      bond_graph = _fcalc_build_bond_graph(cctbx_adapter.olx_atoms.atoms(), len(xyz_records))
      n_bonds = sum(len(neighbours) for neighbours in bond_graph) // 2
      print("Using %d stable bonds to compact xyz frames" % n_bonds)
      solvent_mask = _fcalc_solvent_mask(xyz_records, bond_graph) if skip_solvent else [False] * len(xyz_records)
      keep_mask = [not s for s in solvent_mask]
      if skip_solvent:
        print("Skipping %d solvent/ion atoms (no C or N in their bonded component)" % sum(solvent_mask))
      ref_mean_frac = _fcalc_reference_mean_frac(cctbx_adapter._xray_structure.sites_frac(), keep_mask) if remove_drift else None
    compact_frac, compact_cart = _fcalc_compact_xyz_records(xyz_records, uc, bond_graph)
    if remove_drift and ref_mean_frac is not None:
      compact_frac = _fcalc_remove_drift(compact_frac, keep_mask, ref_mean_frac)
      compact_cart = [uc.orthogonalize(fc) for fc in compact_frac]
    _fcalc_write_compact_xyz(compact_xyz_path, xyz_header, xyz_records, compact_cart, keep_mask)
    cif_lines = open(NoSpherA2_cif_path, 'r').readlines()
    with open(NoSpherA2_cif_path, 'w') as cif_file:
      run = 0
      #read until after "_atom_site_occupancy"
      while("atom_site_occupancy" not in cif_lines[run]):
          run += 1
      run += 1
      #update the position based on the compacted xyz file
      for i, fc in enumerate(compact_frac):
        sc = cctbx_adapter._xray_structure._scatterers[i]
        old_entries = cif_lines[run+i].split()
        # guard against a silent xyz/model atom-order mismatch
        if old_entries[1].strip() != xyz_records[i][0].strip():
          raise ValueError(
            "Atom-order mismatch at index %d: cif type '%s' vs xyz element '%s'. "
            "The .xyz frames must list atoms in the same order as the model." %
            (i, old_entries[1], xyz_records[i][0]))
        sc.site = fc
        if zero_adp:
          # the MD snapshot already encodes the displacement; the ensemble average
          # supplies the Debye-Waller envelope, so remove the deposited ADP here.
          sc.u_iso = res_u
          try:
            if sc.flags.use_u_aniso():
              sc.u_star = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
          except Exception:
            pass
        new_x, new_y, new_z = fc
        uiso_out = ("%.6f" % res_u) if zero_adp else old_entries[5]
        occu_out = 1.0
        #   Label           Type              A           B             C      Uiso            Occu
        cif_lines[run+i] = f" {old_entries[0]} {old_entries[1]} {new_x:.6f} {new_y:.6f} {new_z:.6f} {uiso_out} {occu_out:.6f}\n"
      cif_lines = (
        cif_lines[:run] +
        [cif_lines[run+i] for i, keep in enumerate(keep_mask) if keep] +
        cif_lines[run+len(compact_frac):])
      cif_file.writelines(cif_lines)
    frame_xray_structure = cctbx_adapter._xray_structure.deep_copy_scatterers().select(
      flex.bool(keep_mask))
    nsa2_set_param('source', "  SALTED")
    salted_model = str(salted_model or "").strip()
    if salted_model:
      nsa2_set_param('selected_salted_model', salted_model)
    else:
      available_models = OV.GetParam('user.NoSpherA2.salted_models_list')
      nsa2_set_param('selected_salted_model', available_models.split(";")[1])
    ncpus = nsa2_get_param('ncpus')
    args = []
    NoSpherA2 = OV.GetVar("NoSpherA2")
    args.append(NoSpherA2)
    salted_model_dir = nsa2_get_param('selected_salted_model')
    args.append("-salted")
    args.append(salted_model_dir)
    if (int(ncpus) >= 1):
      args.append('-cpus')
      args.append(ncpus)
    
    if nsa2_get_param('NoSpherA2_Partition') == "RI-Fit":
      if is_orca_new():
        from utilities import ri_fit_args
        args += ri_fit_args()
        mem = float(nsa2_get_param('mem')) * 1000 #Mem in MB
        args.append("-mem")
        args.append(str(mem))
      else:
        print("WARNING! RI-FIT currently only works with ORCA newer than Version 5.0! Please update your ORCA version!")
        print("Performing refinement without RI fit!")
    elif nsa2_get_param('NoSpherA2_Partition') == "TFVC":
      args.append("-TFVC")
    elif nsa2_get_param('NoSpherA2_Partition') == "Becke":
      args.append("-Becke")
    elif nsa2_get_param('NoSpherA2_Partition') == "MBIS":
      args.append("-MBIS")
    elif nsa2_get_param('NoSpherA2_Partition') == "EMBIS":
      args.append("-EMBIS")
  
    args.append("-hkl_min_max")
    args.append(str(hkl_min[0]))
    args.append(str(hkl_max[0]))
    args.append(str(hkl_min[1]))
    args.append(str(hkl_max[1]))
    args.append(str(hkl_min[2]))
    args.append(str(hkl_max[2]))
    hkl_src = ""
    try:
      hkl_src = OV.HKLSrc()
    except Exception:
      try:
        hkl_src = olx.HKLSrc()
      except Exception:
        hkl_src = ""
    if hkl_src:
      if not os.path.isabs(hkl_src):
        hkl_src = os.path.join(folder, hkl_src)
      if os.path.exists(hkl_src):
        if hkl_src.lower().endswith(".hklm"):
          # NoSpherA2 reads three indices: the main reflections of (3+1)D data
          from hklm_util import write_main_hkl
          main = os.path.join(folder, os.path.splitext(os.path.basename(hkl_src))[0] + "_main.hkl")
          write_main_hkl(hkl_src, main)
          hkl_src = main
        args.append("-hkl")
        args.append(hkl_src)
      else:
        print("WARNING! Active HKL file not found for NoSpherA2: %s" % hkl_src)

    args.append("-wfn")
    args.append(compact_xyz)
    args.append("-cif")
    args.append(NoSpherA2_cif)
    
    import sys
    import subprocess
    import time
    from utilities import terminate_process_tree, consume_interrupt_request, is_pause_break_pressed
    out_fn = "NoSpherA2.log"
    out_fn_abs = os.path.join(folder, out_fn)
    launch_log_abs = os.path.join(folder, base_name + ".NoSpherA2.launch.log")
    experimental_tscb = os.path.join(folder, "experimental.tscb")
    if os.path.exists(out_fn_abs):
      os.remove(out_fn_abs)
    if os.path.exists(launch_log_abs):
      os.remove(launch_log_abs)
    if os.path.exists(experimental_tscb):
      os.remove(experimental_tscb)

    p = None
    print("Launching NoSpherA2: %s" % " ".join(args))
    launch_log = open(launch_log_abs, "w")
    launch_log.write("cwd: %s\n" % folder)
    launch_log.write("args: %s\n" % repr(args))
    launch_log.flush()
    launch_env = dict(os.environ)
    if 'OLD_LIBRARY_PATH' in launch_env:
      launch_env["LD_LIBRARY_PATH"] = launch_env["OLD_LIBRARY_PATH"]
    if sys.platform[:3] == 'win':
      startinfo = subprocess.STARTUPINFO()
      startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
      startinfo.wShowWindow = 0
      creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
      p = subprocess.Popen(args, startupinfo=startinfo, creationflags=creationflags, cwd=folder,
        stdout=launch_log, stderr=subprocess.STDOUT, env=launch_env)
    else:
      p = subprocess.Popen(args, cwd=folder, stdout=launch_log, stderr=subprocess.STDOUT,
        env=launch_env)
  
    start_time = time.monotonic()
    log_startup_timeout = 120
    while not os.path.exists(out_fn_abs):
      if OV.GetVar("stop_current_process") or is_pause_break_pressed():
        print("Partitioning aborted by INTERRUPT before log creation!")
        terminate_process_tree(p)
        OV.SetVar("stop_current_process", False)
        consume_interrupt_request()
        OV.SetVar('NoSpherA2-Error', "Wfn-Interrupted")
        raise NameError('NoSpherA2/partitioning aborted by user.')
      if p.poll() is None:
        time.sleep(0.2)
        if time.monotonic() - start_time >= log_startup_timeout:
          print("Failed to locate the output file")
          terminate_process_tree(p)
          OV.SetVar('NoSpherA2-Error',"NoSpherA2-Output not found!")
          raise NameError('NoSpherA2-Output not found!')
      else:
        print("process ended before the output file was found")
        launch_log.flush()
        OV.SetVar('NoSpherA2-Error',"NoSpherA2 ended unexpectedly!")
        raise NameError('NoSpherA2 ended unexpectedly!')
    launch_log.close()
    with open(out_fn_abs, "r", encoding="utf-8", errors="replace") as stdout:
      while p.poll() is None:
        x = stdout.read()
        if x:
          print(x, end='')
        if OV.GetVar("stop_current_process") or is_pause_break_pressed():
          print("Calculation aborted by INTERRUPT!")
          terminate_process_tree(p)
          OV.SetVar("stop_current_process", False)
          consume_interrupt_request()
          aborted_by_user = True
          break
        else:
          time.sleep(0.1)
    return_code = p.poll()
    with open(launch_log_abs, "a") as launch_log_done:
      launch_log_done.write("returncode: %s\n" % return_code)
    if return_code not in (0, None):
      OV.SetVar('NoSpherA2-Error', "NoSpherA2 exited with code %s" % return_code)
      raise NameError('NoSpherA2 exited with code %s' % return_code)
  
    print("\n.tsc calculation ended!")
    
    sfac_name = base_name + ".tscb"
    sfac_path = os.path.join(folder, sfac_name)
    if os.path.exists(sfac_path):
      os.remove(sfac_path)
    if not os.path.exists(experimental_tscb):
      tscb_candidates = [
        os.path.join(folder, fn) for fn in os.listdir(folder)
        if fn.endswith(".tscb") and fn != sfac_name
      ]
      if len(tscb_candidates) == 1:
        experimental_tscb = tscb_candidates[0]
      else:
        print("NoSpherA2 did not produce experimental.tscb in %s" % folder)
        if tscb_candidates:
          print("Found other TSCB candidates: %s" % ", ".join(tscb_candidates))
        OV.SetVar('NoSpherA2-Error', "NoSpherA2 did not produce experimental.tscb")
        raise NameError('NoSpherA2 did not produce experimental.tscb')
    shutil.move(experimental_tscb, sfac_path)
    one_h = direct.f_calc_modulus_squared(frame_xray_structure, table_file_name=sfac_path)
    print("The file was read, calcualting values")
    f_calc = _fcalc_with_xray_structure(
      cctbx_adapter, frame_xray_structure, miller_set, one_h_function=one_h)
    f_calc = _fcalc_apply_swat_correction(f_calc, cctbx_adapter.swat)
    f_calc_data = f_calc.data()
    invalid_f_calc = None
    for i, f_calc_value in enumerate(f_calc_data):
      if not (math.isfinite(f_calc_value.real) and math.isfinite(f_calc_value.imag)):
        invalid_f_calc = (i, f_calc_value)
        break
    if invalid_f_calc is not None:
      i, f_calc_value = invalid_f_calc
      hkl = miller_indices[i]
      diagnostic_log = os.path.join(folder, base_name + ".NoSpherA2.log")
      if os.path.exists(out_fn_abs):
        if os.path.exists(diagnostic_log):
          os.remove(diagnostic_log)
        shutil.move(out_fn_abs, diagnostic_log)
      print("Invalid SALTED Fcalc for %s at reflection %s: %s" % (base_name, hkl, f_calc_value))
      print("Preserved diagnostic files: %s, %s, %s, %s" % (
        sfac_path, NoSpherA2_cif_path, compact_xyz_path, diagnostic_log))
      OV.SetVar('NoSpherA2-Error', "NoSpherA2 produced non-finite Fcalc")
      raise NameError('NoSpherA2 produced non-finite Fcalc')
    
    #Write results to a .hkl-like file
    print("Writing file...")
    hkl_file_name = base_name + ".SALTED_syn_hkl"
    with open(os.path.join(folder, hkl_file_name), 'w', buffering=1024 * 1024) as hkl_file:
      hkl_file.write("! Generated by Olex2 NoSpherA2 plugin\n")
      hkl_file.write("! h k l F_calc\n")
      hkl_file.writelines(
        f"{h} {k} {l} {f_calc_sq:.6f}\n"
        for (h, k, l), f_calc_sq in zip(miller_indices, f_calc_data)
      )
    
    print("...done\nNon NoSpherA2 file...")
    if write_spherical:
      f_calc = _fcalc_with_xray_structure(
        cctbx_adapter, frame_xray_structure, miller_set)
      f_calc = _fcalc_apply_swat_correction(f_calc, cctbx_adapter.swat)
      
      #Write results to a .hkl-like file
      print("Writing file...")
      hkl_file_name = base_name + ".syn_hkl"
      with open(os.path.join(folder, hkl_file_name), 'w', buffering=1024 * 1024) as hkl_file:
        hkl_file.write("! Generated by Olex2 NoSpherA2 plugin\n")
        hkl_file.write("! h k l F_calc\n")
        hkl_file.writelines(
          f"{h} {k} {l} {f_calc_sq:.6f}\n"
          for (h, k, l), f_calc_sq in zip(miller_indices, f_calc.data())
        )
      print("...done")
    os.remove(sfac_path)
    os.remove(NoSpherA2_cif_path)
    if os.path.exists(compact_xyz_path):
        os.remove(compact_xyz_path)
    if os.path.exists(out_fn_abs):
        os.remove(out_fn_abs)
    partition_log = os.path.join(folder, OV.FileName()+".partitionlog")
    if os.path.exists(partition_log):
        os.remove(partition_log)

OV.registerFunction(Fcalc, False, "NoSpherA2")


def diff_sig_map(resolution=0.1,return_map=False,print_peaks=False):
  cctbx_adapter = OlexCctbxAdapter()
  xray_structure = cctbx_adapter.xray_structure()
  use_tsc = OV.IsNoSpherA2()
  one_h = None
  table_name = None
  if use_tsc:
    table_name = str(nsa2_get_param("file"))
    print("Calculating Structure Factors from files...")
    if not os.path.exists(table_name):
      print("Error! Form factor file does not exist!")
      return
    from cctbx_olex_adapter import get_table_contribution
    one_h = direct.f_calc_modulus_squared(
        xray_structure, scatterer_contribution=get_table_contribution(
          xray_structure, table_name))
    if not OV.IsEDRefinement():
      f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
  else:
    print("Non NoSpherA2 map...")
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()

  if not OV.IsEDRefinement():
    f_mask = None
    if OV.GetParam("snum.refinement.use_solvent_mask"):
      f_mask = cctbx_adapter.load_mask()
      if not f_mask:
        OlexCctbxMasks()
        if olx.current_mask.flood_fill.n_voids() > 0:
          f_mask = olx.current_mask.f_mask()
      if f_mask:
        if not f_sq_obs.space_group().is_centric() and f_sq_obs.anomalous_flag():
          f_mask = f_mask.generate_bijvoet_mates()
        f_mask = f_mask.common_set(f_sq_obs)
        f_calc = f_calc.array(data=(f_calc.data() + f_mask.data()))
    f_sq_obs, f_calc = without_dispersion(cctbx_adapter, f_sq_obs, f_calc, f_mask, table_name)
    f_obs = f_sq_obs.f_sq_as_f()
    k = OV.GetOSF()
    if k is None:
      print("Error! Overall scale factor is not set! Using 1.0 as default.")
      k = 1.0
    scale = k ** 0.5
    f_diff = f_obs.f_obs_minus_f_calc(1.0/ scale, f_calc)
    f_diff = f_diff.array(data=f_diff.data() * (2*flex.abs(f_obs.data())/f_sq_obs.sigmas()))
    if OV.IsEDData():
      f_diff = f_diff.apply_scaling(factor=3.324943664)
    f_diff = f_diff.expand_to_p1()
  else:
    I_obs, I_calc = OV.GetACI().EDI.compute_Io_Ic(merge=True)
    f_calc = cctbx_adapter.f_calc(I_obs, None, True, False,
                       one_h_function=one_h, twin_data=False)
    f_obs = I_obs.f_sq_as_f()
    new_data = []
    for i in range(I_obs.size()):
      mfc = math.sqrt(I_calc.data()[i])
      if mfc == 0:
        s = 1
      else:
        s = abs(f_calc.data()[i])/mfc
      fo = f_obs.data()[i] * s
      new_data.append(fo)
    f_obs = f_obs.customized_copy(data=flex.double(new_data))
    #re-compute the scale
    fo2 = f_obs.as_intensity_array()
    f_calc_sq = f_calc.as_intensity_array()
    weights = cctbx_adapter.compute_weights(fo2, f_calc, fc2_data=f_calc_sq.data(), reset_scale_factor=True)
    scale = flex.sum(weights * fo2.data() * f_calc_sq.data()) \
            / flex.sum(weights * flex.pow2(f_calc_sq.data()))
    #
    f_diff = f_obs.f_obs_minus_f_calc(1. / scale**0.5 , f_calc)
    f_diff = f_diff.array(data=f_diff.data() * (2*flex.abs(f_obs.data())/f_sq_obs.sigmas()))
    f_diff = f_diff.apply_scaling(factor=3.324943664)
    f_diff = f_diff.expand_to_p1()

  print("Using %d reflections for Fourier synthesis"%f_diff.size())
  diff_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                            resolution_factor=1,grid_step=float(resolution)).apply_volume_scaling()
  if print_peaks == True or print_peaks == "True":
    from cctbx import maptbx
    max_peaks=10
    peaks = diff_map.peak_search(
      parameters=maptbx.peak_search_parameters(
        peak_search_level=2,
        interpolate=False,
        min_distance_sym_equiv=1.0,
        max_clusters=max_peaks+len(xray_structure.scatterers())),
      verify_symmetry=True
      ).all()
    i = 0
    olx.Kill('$Q', au=True) #HP-JUL18 -- Why kill the peaks? -- cause otherwise they accumulate! #HP4/9/18
    for xyz, height in zip(peaks.sites(), peaks.heights()):
      if i < max_peaks:
        a = olx.xf.uc.Closest(*xyz).split(' ')
        if OV.IsEDData():
          pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A, %.3f A away from %s"
        else:
          pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A^3, %.3f A away from %s" % (
            i + 1, xyz[0], xyz[1], xyz[2], height, float(a[1]), a[0])
        print(pi)
      id = olx.xf.au.NewAtom("%.2f" %(height), *xyz)
      if id != '-1':
        olx.xf.au.SetAtomU(id, "0.06")
        i = i+1
      if i == 100 or i >= max_peaks:
        break
    if OV.HasGUI():
      basis = olx.gl.Basis()
      frozen = olx.Freeze(True)
    olx.xf.EndUpdate(True) #clear LST
    olx.Compaq(q=True)
    if OV.HasGUI():
      olx.gl.Basis(basis)
      olx.Freeze(frozen)
  if return_map == True:
    return diff_map
  write_map_to_cube(diff_map, "diff")

OV.registerFunction(diff_sig_map, False, "NoSpherA2")

#This is a copy of the original class from cctbx to allow custom formatting
class NSA2_miller_arrays_as_cif_block():

  def __init__(self, array, array_type=None,
               column_name=None, column_names=None,
               miller_index_prefix='_refln',
               format="mmcif",
               string_format="%d"):
    wformat = format.lower()
    assert wformat in ("corecif", "mmcif")
    if wformat == "mmcif":
      separator = '.'
    else:
      separator = '_'
    self.cif_block = array.crystal_symmetry().as_cif_block(format=format)
    self.prefix = miller_index_prefix + separator
    self.indices = array.indices().deep_copy()
    self.refln_loop = None
    self.add_miller_array(array, array_type, column_name, column_names, string_format=string_format)
    self.cif_block.add_loop(self.refln_loop)

  def add_miller_array(self, array, array_type=None,
                       column_name=None, column_names=None,
                       string_format="%d"):
    """
    Accepts a miller array, and one of array_type, column_name or column_names.
    """

    assert [array_type, column_name, column_names].count(None) == 2
    if array_type is not None:
      assert array_type in ('calc', 'meas')
    elif column_name is not None:
      column_names = [column_name]
    if array.is_complex_array():
      if column_names is None:
        column_names = [self.prefix+'F_'+array_type,
                        self.prefix+'phase_'+array_type]
      else: assert len(column_names) == 2
      if (('_A_' in column_names[0] and '_B_' in column_names[1]) or
          ('.A_' in column_names[0] and '.B_' in column_names[1])):
        data = [flex.real(array.data()).as_string(string_format),
                 flex.imag(array.data()).as_string(string_format)]
      elif (('_F_squared_calc' in column_names[0] and 'phase_calc' in column_names[1]) or
            ('_F_squared_calc' in column_names[1] and 'phase_calc' in column_names[0])):
        data = [flex.norm(array.data()).as_string(string_format),
                 array.phases(deg=True).data().as_string(string_format)]
      else:
        data = [flex.abs(array.data()).as_string(string_format),
                 array.phases(deg=True).data().as_string(string_format)]
    else:
      if array_type is not None:
        if array.is_xray_intensity_array():
          obs_ext = 'squared_'
        else: obs_ext = ''
        column_names = [self.prefix+'F_'+obs_ext+array_type]
        if array.sigmas() is not None:
          column_names.append(self.prefix+'F_'+obs_ext+'sigma')
      if isinstance(array.data(), flex.std_string):
        data = [array.data()]
      else:
        data = [array.data().as_string(string_format)]
      if array.anomalous_flag():
        if ((array.sigmas() is not None and len(column_names) == 4) or
            (array.sigmas() is None and len(column_names) == 2)):
          data = []
          asu, matches = array.match_bijvoet_mates()
          for anomalous_sign in ("+", "-"):
            sel = matches.pairs_hemisphere_selection(anomalous_sign)
            sel.extend(matches.singles_hemisphere_selection(anomalous_sign))
            if (anomalous_sign == "+"):
              indices = asu.indices().select(sel)
              hemisphere_column_names = column_names[:len(column_names)//2]
            else:
              indices = -asu.indices().select(sel)
              hemisphere_column_names = column_names[len(column_names)//2:]
            hemisphere_data = asu.data().select(sel)
            hemisphere_array = miller.array(miller.set(
              array.crystal_symmetry(), indices), hemisphere_data)
            if array.sigmas() is not None:
              hemisphere_array.set_sigmas(asu.sigmas().select(sel))
            if self.refln_loop is None:
              # then this is the first array to be added to the loop,
              # hack so we don't have both hemispheres of indices
              self.indices = indices
            self.add_miller_array(
              hemisphere_array, column_names=hemisphere_column_names)
          return
      if array.sigmas() is not None and len(column_names) == 2:
        data.append(array.sigmas().as_string(string_format))
    if not (self.indices.size() == array.indices().size() and
            self.indices.all_eq(array.indices())):
      from cctbx.miller import match_indices
      other_indices = array.indices().deep_copy()
      match = match_indices(self.indices, other_indices)
      if match.singles(0).size():
        # array is missing some reflections indices that already appear in the loop
        # therefore pad the data with '?' values
        other_indices.extend(self.indices.select(match.single_selection(0)))
        for d in data:
          d.extend(flex.std_string(['?']*(other_indices.size() - d.size())))
        for d in data:
          assert d.size() == other_indices.size()
        match = match_indices(self.indices, other_indices)
      if match.singles(1).size():
        # this array contains some reflections that are not already present in the
        # cif loop, therefore need to add rows of '?' values
        single_indices = other_indices.select(match.single_selection(1))
        self.indices.extend(single_indices)
        n_data_columns = len(self.refln_loop) - 3
        for hkl in single_indices:
          row = list(hkl) + ['?'] * n_data_columns
          self.refln_loop.add_row(row)
        match = match_indices(self.indices, other_indices)

      match = match_indices(self.indices, other_indices)
      perm = match.permutation()
      data = [d.select(perm) for d in data]
    if self.refln_loop is None:
      self.refln_loop = miller_indices_as_cif_loop(self.indices, prefix=self.prefix)
    columns = OrderedDict(zip(column_names, data))
    for key in columns:
      assert key not in self.refln_loop
    self.refln_loop.add_columns(columns)

def residual_fcf(expand = False):
  cctbx_adapter = OlexCctbxAdapter()
  xray_structure = cctbx_adapter.xray_structure()
  use_tsc = OV.IsNoSpherA2()
  one_h = None
  f_diff = None
  f_mask = None
  if use_tsc:
    table_name = str(nsa2_get_param("file"))
    print("Calculating Structure Factors from files...")
    if not os.path.exists(table_name):
      print("Error! Form factor file does not exist!")
      return
    from cctbx_olex_adapter import get_table_contribution
    one_h = direct.f_calc_modulus_squared(
      xray_structure, scatterer_contribution=get_table_contribution(
        xray_structure, table_name))
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
  else:
    print("Non NoSpherA2 map...")
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()
  if OV.GetParam("snum.refinement.use_solvent_mask"):
    f_mask = cctbx_adapter.load_mask()
    if not f_mask:
      OlexCctbxMasks()
      if olx.current_mask.flood_fill.n_voids() > 0:
        f_mask = olx.current_mask.f_mask()
    if f_mask:
      if not f_sq_obs.space_group().is_centric() and f_sq_obs.anomalous_flag():
        f_mask = f_mask.generate_bijvoet_mates()
      f_mask = f_mask.common_set(f_sq_obs)
      f_obs = f_sq_obs.f_sq_as_f()
      f_calc = f_calc.array(data=(f_calc.data() + f_mask.data()))
      k = math.sqrt(OV.GetOSF())
      f_diff = f_obs.f_obs_minus_f_calc(1.0/k, f_calc)
  else:
    f_obs = f_sq_obs.f_sq_as_f()
    k = math.sqrt(OV.GetOSF())
    f_diff = f_obs.f_obs_minus_f_calc(1.0/k, f_calc)

  if OV.IsEDRefinement():
    I_obs, I_calc = OV.GetACI().EDI.compute_Io_Ic(merge=True)
    f_calc = cctbx_adapter.f_calc(I_obs, None, True, False,
                       one_h_function=one_h, twin_data=False)
    Fc2Ug = OV.GetACI().EDI.get_Fc2Ug()
    new_data = []
    for i in range(I_obs.size()):
      mfc = math.sqrt(I_calc.data()[i])
      if mfc == 0:
        s = 1
      else:
        s = abs(f_calc.data()[i])/mfc
      Io = I_obs.data()[i]
      new_data.append(0 if Io < 0 else math.sqrt(Io)*s)
    I_obs = I_obs.customized_copy(data=flex.double(new_data))
    f_diff = I_obs.f_obs_minus_f_calc(1. , f_calc)
    f_diff = f_diff.apply_scaling(factor=3.324943664/Fc2Ug)
    f_diff = f_diff.expand_to_p1()
  else:
    if OV.IsEDData():
      f_diff = f_diff.apply_scaling(factor=3.324943664)    
    #f_diff = f_diff.expand_to_p1()

  with open(f"{OV.ModelSrc()}_residual.fcf", 'w') as fcf_file:
    if expand:
      f_diff = f_diff.expand_to_p1()
      f_calc = f_calc.expand_to_p1()
      f_sq_obs = f_sq_obs.expand_to_p1()
      
    refln_loop = NSA2_miller_arrays_as_cif_block(f_calc.as_intensity_array(), array_type='calc', format="coreCIF", string_format="%14.8e")
    refln_loop.add_miller_array(f_sq_obs, array_type='meas', string_format="%14.8e")
    refln_loop.add_miller_array(f_sq_obs.f_sq_as_f(), array_type="meas", string_format="%14.8e")
    refln_loop.add_miller_array(f_calc, column_names=['_refln_A_calc','_refln_B_calc'], string_format="%14.8e")
    refln_loop.add_miller_array(f_calc, array_type='calc', string_format="%14.8e")
    refln_loop.add_miller_array(f_diff, column_names=['_refln_A_residual','_refln_B_residual'], string_format="%14.8e")
    refln_loop.add_miller_array(f_diff.as_intensity_array(), column_names=['_refln_I_residual'], string_format="%14.8e")
    refln_loop.add_miller_array(f_calc.d_spacings(), column_name="_refln_d_spacing", string_format="%14.8e")
    if OV.GetParam("snum.refinement.use_solvent_mask"):
      if expand:
        f_mask = f_mask.expand_to_p1()
      refln_loop.add_miller_array(f_mask, column_names=['_refln_A_mask','_refln_B_mask'], string_format="%14.8e")
    
    fcf_file.write(str(refln_loop.cif_block))
  print(f"Saved residual structure factors as {os.path.realpath(fcf_file.name)}")

OV.registerFunction(residual_fcf, False, "NoSpherA2")

def residual_E(expand = False):
  from smtbx.refinement import least_squares
  def get_shelxl_weighting(cca=None):
    weight = cca.olx_atoms.model['weight']
    params = dict(a=0.1, b=0,
                  #c=0, d=0, e=0, f=1./3,
                  )
    for param, value in zip(list(params.keys())[:min(2, len(weight))], weight):
      params[param] = value
    return least_squares.mainstream_shelx_weighting(**params)
  cctbx_adapter = OlexCctbxAdapter()
  xray_structure = cctbx_adapter.xray_structure()
  use_tsc = OV.IsNoSpherA2()
  one_h = None
  f_diff = None
  f_mask = None
  if use_tsc:
    table_name = str(nsa2_get_param("file"))
    print("Calculating Structure Factors from files...")
    if not os.path.exists(table_name):
      print("Error! Form factor file does not exist!")
      return
    from cctbx_olex_adapter import get_table_contribution
    one_h = direct.f_calc_modulus_squared(
      xray_structure, scatterer_contribution=get_table_contribution(
        xray_structure, table_name))
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
  else:
    print("Non NoSpherA2 map...")
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()
  if OV.GetParam("snum.refinement.use_solvent_mask"):
    f_mask = cctbx_adapter.load_mask()
    if not f_mask:
      OlexCctbxMasks()
      if olx.current_mask.flood_fill.n_voids() > 0:
        f_mask = olx.current_mask.f_mask()
    if f_mask:
      if not f_sq_obs.space_group().is_centric() and f_sq_obs.anomalous_flag():
        f_mask = f_mask.generate_bijvoet_mates()
      f_mask = f_mask.common_set(f_sq_obs)
      f_obs = f_sq_obs.f_sq_as_f()
      f_calc = f_calc.array(data=(f_calc.data() + f_mask.data()))
      k = math.sqrt(OV.GetOSF())
      f_diff = f_obs.f_obs_minus_f_calc(1.0/k, f_calc)
      
  else:
    f_obs = f_sq_obs.f_sq_as_f()
    k = math.sqrt(OV.GetOSF())
    f_diff = f_obs.f_obs_minus_f_calc(1.0/k, f_calc)

  if OV.IsEDRefinement():
    I_obs, I_calc = OV.GetACI().EDI.compute_Io_Ic(merge=True)
    f_calc = cctbx_adapter.f_calc(I_obs, None, True, False,
                       one_h_function=one_h, twin_data=False)
    Fc2Ug = OV.GetACI().EDI.get_Fc2Ug()
    new_data = []
    for i in range(I_obs.size()):
      mfc = math.sqrt(I_calc.data()[i])
      if mfc == 0:
        s = 1
      else:
        s = abs(f_calc.data()[i])/mfc
      Io = I_obs.data()[i]
      new_data.append(0 if Io < 0 else math.sqrt(Io)*s)
    I_obs = I_obs.customized_copy(data=flex.double(new_data))
    f_diff = I_obs.f_obs_minus_f_calc(1. , f_calc)
    f_diff = f_diff.apply_scaling(factor=3.324943664/Fc2Ug)
    f_diff = f_diff.expand_to_p1()
  else:
    if OV.IsEDData():
      f_diff = f_diff.apply_scaling(factor=3.324943664)    

  if expand:
    f_diff = f_diff.expand_to_p1()
    
  shelx_weight = get_shelxl_weighting(cctbx_adapter)
  sigmas = f_sq_obs.sigmas()
  s_weights = flex.double(f_sq_obs.size(), 1.0)
  u_weights = 1/(sigmas*sigmas)
  fo_d = f_sq_obs.data()
  fc_d = f_calc.as_intensity_array().data()
  ind = f_sq_obs.indices()
  for i in range(f_sq_obs.size()):
    s_weights[i] = shelx_weight.compute(fo_d[i], sigmas[i], fc_d[i], ind[i], OV.GetOSF())
  
  I_diff = f_diff.as_intensity_array()
  stl_sq = f_diff.sin_theta_over_lambda_sq()
  ratio = I_diff.data() / stl_sq.data()
  E_coul = 1.0/(2.0*np.pi*f_diff.unit_cell().volume()) * sum(ratio)
  E_coul_u = 1.0/(2.0*np.pi*f_diff.unit_cell().volume()) * sum(ratio * u_weights)
  E_coul_s = 1.0/(2.0*np.pi*f_diff.unit_cell().volume()) * sum(ratio * s_weights)
  print(f"{E_coul:.5e} e/A, sigma_weight: {E_coul_u:.5e} e/A, shelx_weight: {E_coul_s:.5e}")

OV.registerFunction(residual_E, False, "NoSpherA2")

def adp_list_to_array(a: Sequence) -> np.ndarray:
  return np.array([(a[0], a[3], a[4]), (a[3], a[1], a[5]), (a[4], a[5], a[2])])

def adp_list_to_sigma_inv(adp: Sequence) -> np.ndarray:
  return linalg.inv(adp_list_to_array(adp))

def digest_boolinput(i: Union[str, bool]) -> bool:
  if isinstance(i, bool):
    return i
  elif isinstance(i, str):
    if i.lower() in {'f', 'false', '0'}:
      return False
    elif i.lower() in {'t', 'true', '1'}:
      return True
  raise ValueError(f'Parameter {i!r} cannot be interpreted as boolean. '
                   f'Use "True" / "T" / "1" or "False" / "F" / "0" instead.')

@run_with_bitmap("Calculating PDF")
def PDF_map(resolution=0.1, dist=1.0, second=True, third=True, fourth=True, only_anh=True, do_plot=True, save_cube=False):
  second = digest_boolinput(second)
  third = digest_boolinput(third)
  fourth = digest_boolinput(fourth)
  do_plot = digest_boolinput(do_plot)
  save_cube = digest_boolinput(save_cube)
  only_anh = digest_boolinput(only_anh)
  print("PDF Maps implemented and tested by Florian Kleemiss and Daniel Tchon")
  if second == False and third == False and fourth == False:
    print("Well, what should I print then? Please decide what you want to see!")
    return
  try:
    dist = float(dist)
    cctbx_adapter = OlexCctbxAdapter()
    uc = cctbx_adapter.xray_structure().unit_cell()
    fixed = math.pow(2 * math.pi, 1.5)
    cm = tuple(list(uc.orthogonalization_matrix()))
    fm = list(uc.fractionalization_matrix())
    adp_stars, anharms, labels, posn, pre, sigmas = [], [], [], [], [], []
    for atom in cctbx_adapter.xray_structure()._scatterers:
      labels.append(atom.label)
      posn.append([coord % 1 for coord in atom.site])
      if atom.u_star != (-1., -1., -1., -1., -1., -1.):
        adp_star = atom.u_star
      else:
        adp_star = adptbx.u_iso_as_u_star(uc, atom.u_iso)
      adp_stars.append(adp_star)
      if atom.anharmonic_adp == None:
        anharms.append(None)
      else:
        order = atom.anharmonic_adp.get_order()
        anharmonic_values = np.array(atom.anharmonic_adp.data())
        if order == 3:
          anharmonic_use = np.array([third, ] * 10, dtype=float)
        elif order == 4:
          anharmonic_use = np.array([third, ] * 10 + [fourth, ] * 15, dtype=float)
        anharms.append(anharmonic_use * anharmonic_values)
      sigmas.append(adp_list_to_sigma_inv(adp_star))
      #check for problems in sigmas
      try:
        pre_temp = linalg.det(sigmas[-1])
        if pre_temp < 0:
          print("Skipping NPD Atom %s"%atom.label)
          pre_temp = -math.sqrt(-pre_temp) / fixed
        else:
          pre_temp = math.sqrt(pre_temp) / fixed
      except:
        print("Problem with atom %s"%atom.label)
        pre_temp = 0
        pass
      pre.append(pre_temp)

    gridding = cctbx_adapter.xray_structure().gridding(step=float(resolution))
    size = tuple(gridding.n_real())
    n_atoms = len(posn)

    vecs = [(cm[0] / (size[0]), cm[1] / (size[1]), cm[2] / (size[2])),
            (cm[3] / (size[0]), cm[4] / (size[1]), cm[5] / (size[2])),
            (cm[6] / (size[0]), cm[7] / (size[1]), cm[8] / (size[2]))]

    print("Calculating Grid %4d x %4d x %4d..." % (size[0], size[1], size[2]))

    def index_limits(center: np.ndarray,
                     radius: float,
                     fractionization_array: np.ndarray,
                     size_array: np.ndarray) -> Sequence[np.ndarray]:
      """Calculate evaluation range based on radius and center"""
      plus_minus_ones = np.array(list(itertools.product([-1, +1], repeat=3)))
      corners_cart = center + plus_minus_ones * radius
      corners_frac = (fractionization_array @ corners_cart.T).T
      return np.floor(np.min(corners_frac, axis=0) * size_array).astype(int), \
             np.ceil(np.max(corners_frac, axis=0) * size_array).astype(int)

    # determine grid index limits for every atom in asymmetric unit
    corner1_indices = np.full(shape=(n_atoms, 3), fill_value= np.inf)
    corner2_indices = np.full(shape=(n_atoms, 3), fill_value=-np.inf)
    frac_arr = np.array(fm, dtype=float).reshape(3, 3)
    size_arr = np.array(size)
    for a in range(n_atoms):
      if second is False or only_anh is True:
        if anharms[a] is None:
          continue
      atom_coords_cart = np.array(uc.orthogonalize(posn[a]))
      corner1_indices[a], corner2_indices[a] = \
          index_limits(atom_coords_cart, dist, frac_arr, size_arr)

    # generate a whole grid to be evaluated
    if np.isinf(corner1_indices).all() or np.isinf(corner2_indices).all():
      xi_min = yi_min = zi_min = xi_max = yi_max = zi_max = 0
    else:
      xi_min, yi_min, zi_min = np.min(corner1_indices, axis=0).astype(int)
      xi_max, yi_max, zi_max = np.max(corner2_indices, axis=0).astype(int)
    xyz_grid = np.array(np.mgrid[xi_min:xi_max, yi_min:yi_max, zi_min:zi_max])
    xi, yi, zi = map(np.ravel, xyz_grid)

    # determine pieces of grid around atoms that really need evaluation
    masks = []
    for a in range(n_atoms):
      if np.isinf(corner1_indices[a]).any():  # not evaluated, no box
        masks.append(None)
        continue
      corner1_ind = corner1_indices[a]
      corner2_ind = corner2_indices[a]
      x_mask = (xi >= corner1_ind[0]) & (xi <= corner2_ind[0])
      y_mask = (yi >= corner1_ind[1]) & (yi <= corner2_ind[1])
      z_mask = (zi >= corner1_ind[2]) & (zi <= corner2_ind[2])
      masks.append(x_mask & y_mask & z_mask)

    # prepare lists for integration and evaluate the PDF on the grid
    positive_integrals, negative_integrals, negative_volumes = [], [], []
    volume_scale_factor = linalg.det(np.array(vecs)) / uc.volume()
    pdfs = np.zeros_like(xi, dtype=float)
    for a in range(n_atoms):
      if (second is False or only_anh is True) and anharms[a] is None:
        pdf = np.zeros(1)
      elif pre[a] <= 0:  # Skip NPD atoms
        pdf = np.zeros(1)
      else:
        u = np.vstack([xi[masks[a]] / size[0] - posn[a][0],
                       yi[masks[a]] / size[1] - posn[a][1],
                       zi[masks[a]] / size[2] - posn[a][2]]).T
        mhalfuTUu = np.clip(-0.5 * np.sum(u * (u @ sigmas[a]), axis=1),
                            a_min=None, a_max=0)
        p0 = pre[a] * np.exp(mhalfuTUu)
        p0[abs(p0) < 1E-30] = 0
        fact = float(second)
        if anharms[a] is not None:
          poly = 0
          if len(anharms[a]) == 10:
              poly = hermite_polynomials_of_3rd_order
          elif len(anharms[a]) == 25:
              poly = hermite_polynomials_of_3rd_and_4th_order
          for i, h in enumerate(poly):
            if anharms[a][i] != 0:
              fact += anharms[a][i] * h(u, sigmas[a]) / h.order_factorial
        pdf = p0 * fact
        pdfs[masks[a]] += pdf
      positive_integrals.append(np.sum(pdf[pdf > 0]) * volume_scale_factor)
      negative_integrals.append(np.sum(pdf[pdf < 0]) * volume_scale_factor)
      negative_volumes.append(pdf[pdf < 0].size * volume_scale_factor)

    pdfs /= uc.volume()
    # the checks need the evaluated boxes only; the full-cell grid below is for the map
    stats_min = float(pdfs.min()) if pdfs.size else 0.0
    stats_max = float(pdfs.max()) if pdfs.size else 0.0
    OV.SetVar("Negative_PDF", False)
    if stats_min < -0.05:
      index = int(np.argmin(pdfs))
      x, y, z = xi[index], yi[index], zi[index]
      pos = [(x) * vecs[0][0] + (y) * vecs[0][1] + (z) * vecs[0][2],
             (x) * vecs[1][0] + (y) * vecs[1][1] + (z) * vecs[1][2],
             (x) * vecs[2][0] + (y) * vecs[2][1] + (z) * vecs[2][2]]
      min_dist = cm[0] + cm[4] + cm[8]
      atom_nr = 0
      for i in range(n_atoms):
        pos_cart = uc.orthogonalize(posn[i])
        diff = [(pos[0] - pos_cart[0]), (pos[1] - pos_cart[1]), (pos[2] - pos_cart[2])]
        dist_ = np.sqrt(diff[0] * diff[0] + diff[1] * diff[1] + diff[2] * diff[2])
        if dist_ < min_dist:
          min_dist = dist_
          atom_nr = i
      print(f"WARNING! Significant negative PDF for Atom: {labels[atom_nr]}"
            f" at a distance of {min_dist:8.3f} Angs")
      OV.SetVar("Negative_PDF", True)
      for a in range(n_atoms):
        if negative_integrals[a] < -0.001:
          label = str(cctbx_adapter.xray_structure()._scatterers[a].label)
          print(f"WARNING! Integrated negative probability of "
                f"{-negative_integrals[a]:.2%} to find atom {label} "
                f"in a {1e6 * negative_volumes[a]:.0f} pm^3 volume")
    OV.SetVar("Kuhs_Rule", False)
    for a in range(n_atoms):
      order = 0 if anharms[a] is None else 4 if any(_ for _ in anharms[a][10:])         else 3 if any(_ for _ in anharms[a][:10]) else 0
      if order:
        adp = adptbx.u_star_as_u_iso(uc, adp_stars[a])
        if (k := 0.5 / kuhs_limit(order, adp)) <= olex_core.GetHklStat()['MinD']:
          order_str = '3rd order' if order == 3 else '4th order'
          label = str(cctbx_adapter.xray_structure()._scatterers[a].label)
          OV.SetVar("Kuhs_Rule", True)
          print(f"WARNING! Kuhs' rule: d_min < {k:.2f}A required"
                f" for {order_str} for atom {label} (Ueq {adp:.2e})")
    if not save_cube and not (do_plot and OV.HasGUI()):
      return

    # wrap the results back to the unit cell and assign them to the data flex
    data_array = np.zeros(shape=(size[0], size[1], size[2], ))
    x_cases = (xi < 0, (xi >= 0) & (xi < size[0]), xi >= size[0])
    y_cases = (yi < 0, (yi >= 0) & (yi < size[1]), yi >= size[1])
    z_cases = (zi < 0, (zi >= 0) & (zi < size[2]), zi >= size[2])
    cases = (c[0] & c[1] & c[2] for c in itertools.product(x_cases, y_cases, z_cases))
    for c in cases:
      data_array[xi[c] % size[0], yi[c] % size[1], zi[c] % size[2]] += pdfs[c]
    data = flex.double(data_array.flatten())
    data.reshape(flex.grid(size[0], size[1], size[2]))
    if save_cube:
      write_map_to_cube(data, "PDF", size)

    if do_plot and OV.HasGUI():
      iso = -0.05 if second is False else -3.1415
      if OV.GetVar("Negative_PDF") == True:
        iso = stats_min * 0.6
      plot_map(data, iso, dist, min_v=stats_min, max_v=stats_max)
  except Exception as e:
    OV.DeleteBitmap("working")
    raise(e)

  OV.DeleteBitmap("working")
OV.registerFunction(PDF_map, False, "NoSpherA2")

def tomc_map(resolution=0.1, return_map=False, use_f000=False):
  cctbx_adapter = OlexCctbxAdapter()
  use_tsc = OV.IsNoSpherA2()
  table_name = None
  f_mask = None
  if use_tsc == True:
    table_name = str(nsa2_get_param("file"))
    print("Calculating Structure Factors from files...")
    xray_structure = cctbx_adapter.xray_structure()
    if not os.path.exists(table_name):
      print("Error! Form factor file does not exist!")
      return
    from cctbx_olex_adapter import get_table_contribution
    one_h = direct.f_calc_modulus_squared(
                       xray_structure, scatterer_contribution=
                       get_table_contribution(xray_structure, table_name))
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
  else:
    print("Non NoSpherA2 map...")
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()
  if OV.GetParam("snum.refinement.use_solvent_mask"):
    f_mask = cctbx_adapter.load_mask()
    if not f_mask:
      OlexCctbxMasks()
      if olx.current_mask.flood_fill.n_voids() > 0:
        f_mask = olx.current_mask.f_mask()
    if f_mask:
      if not f_sq_obs.space_group().is_centric() and f_sq_obs.anomalous_flag():
        f_mask = f_mask.generate_bijvoet_mates()
      f_mask = f_mask.common_set(f_sq_obs)
      f_calc = f_calc.array(data=(f_calc.data() + f_mask.data()))
  f_sq_obs, f_calc = without_dispersion(cctbx_adapter, f_sq_obs, f_calc, f_mask, table_name)
  f_obs = f_sq_obs.f_sq_as_f()
  k = math.sqrt(OV.GetOSF())
  f_diff = f_obs.f_obs_minus_f_calc(2.0/k, f_calc)

  f_diff = f_diff.expand_to_p1()
  if OV.IsEDData():
    f_diff = f_diff.apply_scaling(factor=3.324943664)  # scales from A-2 to eA-1
  if use_f000 == True or use_f000 == "True":
    f000 = float(olx.xf.GetF000())
    tomc_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1,grid_step=float(resolution),
                              f_000=f000).apply_volume_scaling()
  else:
    tomc_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1, grid_step=float(resolution)).apply_volume_scaling()
  if return_map == True:
    return tomc_map
  write_map_to_cube(tomc_map, "tomc")

OV.registerFunction(tomc_map, False, "NoSpherA2")

def deformation_map(resolution=0.1, return_map=False):
  use_tsc = OV.IsNoSpherA2()
  if use_tsc == False:
    print("ERROR! Deformation is only available when using a .tsc file!")
    return
  cctbx_adapter = OlexCctbxAdapter()
  table_name = str(nsa2_get_param("file"))
  print("Calculating Structure Factors from files...")
  xray_structure = cctbx_adapter.xray_structure()
  if not os.path.exists(table_name):
    print("Error! Form factor file does not exist!")
    return
  from cctbx_olex_adapter import get_table_contribution
  one_h = direct.f_calc_modulus_squared(
        xray_structure, scatterer_contribution=get_table_contribution(
          xray_structure, table_name))
  f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
  f_sq_obs, f_calc_spher = cctbx_adapter.get_fo_sq_fc()
  print("Fspher_Fcalc R1:")
  print(f_calc_spher.r1_factor(f_calc, scale_factor=1))
  f_diff = f_calc.f_obs_minus_f_calc(1, f_calc_spher)
  f_diff = f_diff.expand_to_p1()
  if OV.IsEDData():
    f_diff = f_diff.apply_scaling(factor=3.324943664)  # scales from A-2 to eA-1
  def_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                           resolution_factor=1,grid_step=float(resolution)).apply_volume_scaling()
  if return_map==True:
    return def_map
  write_map_to_cube(def_map, "deform")

OV.registerFunction(deformation_map, False, "NoSpherA2")

def def_sig_map(resolution=0.1, return_map=False):
  use_tsc = OV.IsNoSpherA2()
  if use_tsc == False:
    print("ERROR! Deformation is only available when using a .tsc file!")
    return
  cctbx_adapter = OlexCctbxAdapter()
  table_name = str(nsa2_get_param("file"))
  print("Calculating Structure Factors from files...")
  xray_structure = cctbx_adapter.xray_structure()
  if not os.path.exists(table_name):
    print("Error! Form factor file does not exist!")
    return
  from cctbx_olex_adapter import get_table_contribution
  one_h = direct.f_calc_modulus_squared(
        xray_structure, scatterer_contribution=get_table_contribution(
          xray_structure, table_name))
  f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
  f_sq_obs, f_calc_spher = cctbx_adapter.get_fo_sq_fc()
  print("Fspher_Fcalc R1:")
  print(f_calc_spher.r1_factor(f_calc, scale_factor=1))
  f_diff = f_calc.f_obs_minus_f_calc(1, f_calc_spher)
  f_diff = f_diff.array(data=f_diff.data() * (2*flex.abs(f_sq_obs.f_sq_as_f().data())/f_sq_obs.sigmas()))
  f_diff = f_diff.expand_to_p1()
  if OV.IsEDData():
    f_diff = f_diff.apply_scaling(factor=3.324943664)  # scales from A-2 to eA-1
  def_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                           resolution_factor=1,grid_step=float(resolution)).apply_volume_scaling()
  if return_map==True:
    return def_map
  write_map_to_cube(def_map, "deform")

OV.registerFunction(def_sig_map, False, "NoSpherA2")

def obs_map(resolution=0.1, return_map=False, use_f000=False):
  cctbx_adapter = OlexCctbxAdapter()
  use_tsc = OV.IsNoSpherA2()
  table_name = None
  if use_tsc == True:
    table_name = str(nsa2_get_param("file"))
    print("Calculating Structure Factors from files...")
    xray_structure = cctbx_adapter.xray_structure()
    if not os.path.exists(table_name):
      print("Error! Form factor file does not exist!")
      return
    from cctbx_olex_adapter import get_table_contribution
    one_h = direct.f_calc_modulus_squared(
        xray_structure, scatterer_contribution=get_table_contribution(
          xray_structure, table_name))
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
  else:
    print("Non NoSpherA2 map...")
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()
  f_sq_obs, f_calc = without_dispersion(cctbx_adapter, f_sq_obs, f_calc, table_name=table_name)
  f_obs = f_sq_obs.f_sq_as_f()
  k = math.sqrt(OV.GetOSF())
  f_obs = f_obs.apply_scaling(factor=1./k)  # on the F(000) scale, which is absolute
  f_obs = f_obs.phase_transfer(f_calc)
  if OV.IsEDData():
    f_obs = f_obs.apply_scaling(factor=3.324943664)  # scales from A-2 to eA-1
  if use_f000 == True or use_f000 == "True":
    f000 = float(olx.xf.GetF000())
    obs_map = f_obs.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1,
                              grid_step=float(resolution),
                              f_000=f000).apply_volume_scaling()
  else:
    obs_map = f_obs.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1,grid_step=float(resolution)).apply_volume_scaling()
  if return_map==True:
    return obs_map
  write_map_to_cube(obs_map, "obs")

OV.registerFunction(obs_map, False, "NoSpherA2")

def calc_map(resolution=0.1,return_map=False, use_f000=False):
  cctbx_adapter = OlexCctbxAdapter()
  use_tsc = OV.IsNoSpherA2()
  table_name = None
  if use_tsc == True:
    table_name = str(nsa2_get_param("file"))
    print("Calculating Structure Factors from files...")
    xray_structure = cctbx_adapter.xray_structure()
    if not os.path.exists(table_name):
      print("Error! Form factor file does not exist!")
      return
    from cctbx_olex_adapter import get_table_contribution
    one_h = direct.f_calc_modulus_squared(
        xray_structure, scatterer_contribution=get_table_contribution(
          xray_structure, table_name))
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
  else:
    print("Non NoSpherA2 map...")
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()
  f_calc = f_calc_no_dispersion(cctbx_adapter, f_calc, table_name) or f_calc
  if OV.IsEDData():
    f_calc = f_calc.apply_scaling(factor=3.324943664)  # scales from A-2 to eA-1
  if use_f000 == True or use_f000 == "True":
    f000 = float(olx.xf.GetF000())
    calc_map = f_calc.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1, grid_step=float(resolution),
                              f_000=f000).apply_volume_scaling()
  else:
    calc_map = f_calc.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1, grid_step=float(resolution)).apply_volume_scaling()
  if return_map==True:
    return calc_map
  write_map_to_cube(calc_map, "calc")

OV.registerFunction(calc_map, False, "NoSpherA2")

def mask_map(resolution=0.1, return_map=False, use_f000=False):
  cctbx_adapter = OlexCctbxAdapter()
  if cctbx_adapter.twin_components or cctbx_adapter.hklf_code == 5:
    f_sq_obs = cctbx_adapter.get_fo_sq_fc()[0]  # the detwinned set
  else:
    # only the observed set is wanted: the direct F(calc) get_fo_sq_fc pays
    # for is several seconds on a protein, for nothing
    f_sq_obs = cctbx_adapter.reflections.f_sq_obs_filtered.merge_equivalents(
      algorithm="shelx").array().map_to_asu()
  if OV.GetParam("snum.refinement.use_solvent_mask"):
    f_mask = cctbx_adapter.load_mask()
    if not f_mask:
      OlexCctbxMasks()
      if olx.current_mask.flood_fill.n_voids() > 0:
        f_mask = olx.current_mask.f_mask()
    if f_mask:
      if not f_sq_obs.space_group().is_centric() and f_sq_obs.anomalous_flag():
        f_mask = f_mask.generate_bijvoet_mates()
      f_mask = f_mask.common_set(f_sq_obs)
  if OV.IsEDData():
    f_mask = f_mask.apply_scaling(factor=3.324943664)  # scales from A-2 to eA-1
  if use_f000 == True or use_f000 == "True":
    # the masked region's own electron count, not the cell's F(000); a mask
    # read back from the .fab carries none, so it is computed afresh
    if getattr(olx.current_mask, "f_000_s", None) is None:
      OlexCctbxMasks()
    f000 = float(olx.current_mask.f_000_s)  # sum of the void counts, ED already scaled
    print("Mask map F(000) = %.1f, the masked electrons" % f000)
    mask_map = f_mask.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1, grid_step=float(resolution),
                              f_000=f000).apply_volume_scaling()
  else:
    mask_map = f_mask.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1, grid_step=float(resolution)).apply_volume_scaling()
  if return_map==True:
    return mask_map
  write_map_to_cube(mask_map, "mask")

OV.registerFunction(mask_map, False, "NoSpherA2")

DENSITY_MAP_LEVEL = 1.0  # e/A^3, below the C-C / C-O bond density, so the bonds show and not only the cores

def show_fft_map(resolution=0.1,map_type="diff",use_f000=False,print_peaks=False):
  if map_type == "diff":
    plot_fft_map(residual_map(resolution, return_map=True,print_peaks=print_peaks), peak_frac=0.5)
  elif map_type == "fcfmc":
    plot_fft_map(deformation_map(resolution, return_map=True))
  elif map_type in ("obs", "fobs"):  # the map menu sends fobs/fcalc
    plot_fft_map(obs_map(resolution,return_map=True,use_f000=use_f000), level=DENSITY_MAP_LEVEL)
  elif map_type in ("calc", "fcalc"):
    plot_fft_map(calc_map(resolution,return_map=True,use_f000=use_f000), level=DENSITY_MAP_LEVEL)
  elif map_type == "tomc":
    plot_fft_map(tomc_map(resolution, return_map=True, use_f000=use_f000), level=DENSITY_MAP_LEVEL)
  elif map_type == "mask":
    plot_fft_map(mask_map(resolution, return_map=True, use_f000=use_f000))
  elif map_type == "diff_sig":
    plot_fft_map(diff_sig_map(resolution, return_map=True, print_peaks=print_peaks), peak_frac=0.5)
  elif map_type == "def_sig":
    plot_fft_map(def_sig_map(resolution, return_map=True))

OV.registerFunction(show_fft_map, False, "NoSpherA2")
