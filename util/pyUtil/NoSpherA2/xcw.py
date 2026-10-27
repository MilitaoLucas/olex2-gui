"""X-ray constrained wavefunction fitting from the NoSpherA2 refine tab.

Experimental. The block (hybrid_GUI.make_XCW_GUI) is shown only with
user.NoSpherA2.show_XCW. What it does:

  Run XCW  writes olex2/XCW/<name>.cif (with the refinement's f'/f'' per
           type and per atom), <name>.hkl, anom_disp.txt (the same per
           element, for older NoSpherA2) and <name>_xcw_settings.txt from the
           snum.NoSpherA2.XCW parameters and starts
           NoSpherA2 -do_XCW ... in the background, cwd = that folder
  Stop     kills the job
  status   the last lambda row of NoSpherA2.log while it runs, the recommended
           halting lambda when it finished
  Use      copies the chosen NA2_<lambda>.tscb (or .tshb) next to the structure
           as <name>_xcw_<lambda>.tscb (.tshb) and makes it the tsc source
  .tshb    each step writes an RI fit of its density (-tshb with the RI-fit
           aux basis and multipole restraints of the refine tab) instead of its
           table; the fit is another partition, F differs at the 1e-2 level
  Partition  hirshfeld/becke grid weights, or ri (-xcw_partition ri, the
           refine tab's aux basis + multipole restraint, which also offers
           TFVC/MBIS/EMBIS targets)

Still to do: charge/multiplicity are the shared NoSpherA2 values; twin laws
are not passed.
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import threading

import olex
import olex_core
import olx
from olexFunctions import OV
from variableFunctions import nsa2_get_param, nsa2_set_param

_folder = os.path.join("olex2", "XCW")
_state = {"proc": None, "thread": None, "message": ""}


def _job_dir():
  return os.path.join(OV.FilePath(), _folder)


def _name():
  return olx.FileName()


def _param(key, default=None):
  v = nsa2_get_param("XCW.%s" % key)
  return default if v in (None, "") else v


def _charge():
  return int(nsa2_get_param("charge") or 0)


def _mult():
  """The shared NoSpherA2 multiplicity; 0 means 1 everywhere else in the package."""
  return int(nsa2_get_param("multiplicity") or 0) or 1


def _executable():
  exe = OV.GetVar("NoSpherA2")
  if _param("basis_adv") == True:
    root, extension = os.path.splitext(exe)
    advanced = root + "_XCW" + extension
    if os.path.isfile(advanced):
      return advanced
  return exe


def xcw_basis_list():
  from NoSpherA2 import get_NoSpherA2_instance
  bases = get_NoSpherA2_instance().basis_list_str
  if not bases:
    raise RuntimeError("No basis sets found for XCW")
  return bases


def _write_hkl(path):
  """The measured, merged data: XCW fits against a real reflection file, -dmin is not honoured."""
  from cctbx_olex_adapter import OlexCctbxAdapter
  original = OV.GetParam("snum.masks.original_hklsrc")
  current = OV.HKLSrc()
  if original and current != original:
    OV.HKLSrc(original)  # a mask is active: use the unmasked intensities
  try:
    f_sq_obs = OlexCctbxAdapter().reflections.f_sq_obs_merged
    with open(path, "w") as out:
      f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
  finally:
    if original and current != original:
      OV.HKLSrc(current)


def _n_params():
  """The refined parameter count of the model, as the GUI status bar shows it."""
  try:
    from gui.tools import get_parameter_number, GetNParams
    n = int(get_parameter_number() or 0)
    if n <= 0:  # nothing refined yet in this session: count the parameters now
      GetNParams()  # stores the count in a variable, returns nothing
      n = int(get_parameter_number() or 0)
  except Exception:
    n = 0
  return n


def _append_dispersion(path):
  """f' f'' as the refinement uses them (cctbx_olex_adapter.xray_structure: resonant table, SFAC overrides,
  refined DISP per atom), appended to the CifCreate_4NoSpherA2 file. One _atom_type row per type; an atom whose
  values differ from the first atom of its type gets an _atom_site_dispersion row, which NoSpherA2 applies to
  that site alone (convenience.cpp read_CIF, density_source 4917b79b on)."""
  import iotbx.cif
  from cctbx_olex_adapter import OlexCctbxAdapter
  block = list(iotbx.cif.reader(file_path=path).model().values())[0]
  if "_atom_type_symbol" in block:
    raise RuntimeError("the CIF already has an _atom_type loop")
  labels, types = block["_atom_site_label"], block["_atom_site_type_symbol"]
  scatterers = OlexCctbxAdapter().xray_structure().scatterers()
  if len(labels) != scatterers.size():
    raise RuntimeError("%d atoms in the CIF against %d scatterers" % (len(labels), scatterers.size()))
  per_type, per_site = {}, []
  for label, t, sc in zip(labels, types, scatterers):
    # the CIF label may carry a residue suffix (GetResiLabel), the scatterer has the plain name
    if not label.lower().startswith(sc.label.lower()):
      raise RuntimeError("CIF atom %s paired with scatterer %s" % (label, sc.label))
    v = (sc.fp, sc.fdp)
    if max(abs(a - b) for a, b in zip(per_type.setdefault(t, v), v)) > 1e-6:
      per_site.append((label, v))
  with open(path, "a") as out:
    out.write("\nloop_\n  _atom_type_symbol\n  _atom_type_scat_dispersion_real\n"
              "  _atom_type_scat_dispersion_imag\n")
    for t, (fp, fdp) in sorted(per_type.items()):
      out.write("  %s %.6f %.6f\n" % (t, fp, fdp))
    if per_site:
      out.write("\nloop_\n  _atom_site_dispersion_label\n  _atom_site_dispersion_real\n"
                "  _atom_site_dispersion_imag\n")
      for label, (fp, fdp) in per_site:
        out.write("  %s %.6f %.6f\n" % (label, fp, fdp))


def _write_anom_disp(path):
  """f' f'' per element for NoSpherA2 before density_source 4917b79b, which reads them only from -anom_disp
  ('symbol fp fdp' lines); later builds ignore -anom_disp with a warning and use the CIF loops above.
  Drop this and -anom_disp once the NoSpherA2 that Olex2 ships has 4917b79b."""
  from cctbx_olex_adapter import OlexCctbxAdapter
  values = {}
  for sc in OlexCctbxAdapter().xray_structure().scatterers():
    el = sc.scattering_type.rstrip("+-0123456789")
    v = (sc.fp, sc.fdp)
    if el in values and max(abs(a - b) for a, b in zip(values[el], v)) > 1e-4:
      print("XCW: %s has several f'/f'' (DISP per atom), using %.4f %.4f" % ((el,) + values[el]))
    values.setdefault(el, v)
  with open(path, "w") as out:
    for el, (fp, fdp) in sorted(values.items()):
      out.write("%s %.6f %.6f\n" % (el, fp, fdp))


def _write_settings(path, n_params):
  """The settings file NoSpherA2 reads with -XCW_settings (XCW.cpp), one keyword per line."""
  lines = [
    str(_param("scf_preset", "normal")),
    str(_param("conv_preset", "normal_conv")),
    "params %d" % n_params,
    "basis_set %s" % _param("basis_name", nsa2_get_param("basis_name")),
  ]
  if _param("basis_adv") == True:
    folder = os.path.dirname(os.path.abspath(path))
    exe = _executable()
    help_result = subprocess.run([exe, "-help"], cwd=folder, check=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if b"basis_overrides <file>" not in help_result.stdout:
      raise RuntimeError("This NoSpherA2 executable does not support XCW advanced bases; install a build with basis_overrides support.")
    from basis_set_api import get_basis_overrides_json
    import olexex
    from utilities import ELEMENTS_BY_SYMBOL
    atoms = olexex.OlexRefinementModel()._atoms
    present = {ELEMENTS_BY_SYMBOL[atom['type']] for atom in atoms}
    data = get_basis_overrides_json(str(_param("basis_adv_string", "")), present)
    filename = "xcw_basis_overrides.json"
    with open(os.path.join(folder, filename), "w") as out:
      json.dump(data, out, indent=2)
      out.write("\n")
    lines.append("basis_overrides %s" % filename)
  if _param("df_basis"):
    lines.append("df_basis %s" % _param("df_basis"))
  lines.append("max_iter %d" % int(_param("max_iter", 100)))
  lines.append(str(_param("target", "F")))
  if _param("weighted") == True:
    lines.append("weighted")
  lines.append("charge %d" % _charge())
  lines.append("mult %d" % _mult())
  lines.append(str(_param("reference", "rhf")))
  lines.append("start %s" % _param("start", 0.0))
  lines.append("step_size %s" % _param("step_size", 0.01))
  lines.append("end %s" % _param("end", 1.0))
  if int(_param("i_tensor_mb", 0) or 0) > 0:
    lines.append("i_tensor_mb %d" % int(_param("i_tensor_mb")))
  # whatever the user typed into "Extra settings", one line per ; (or newline)
  for extra in str(_param("extra_settings", "") or "").replace(";", "\n").splitlines():
    if extra.strip():
      lines.append(extra.strip())
  with open(path, "w") as out:
    out.write("\n".join(lines) + "\n")


def _args(folder, name, settings):
  exe = _executable()
  args = [exe, "-do_XCW", "-cif", name + ".cif", "-hkl", name + ".hkl", "-XCW_settings", settings,
          "-cpus", str(nsa2_get_param("ncpus")), "-mem", str(float(nsa2_get_param("mem")) * 1000), "-no_date",
          "-charge", str(_charge()), "-mult", str(_mult()), "-anom_disp", "anom_disp.txt"]
  if _param("gaussian_halt") == True:
    args.append("-xcw_gaussian_halt")
  # the GUI value is I/sigma(I); sigma(I) = 2 F sigma(F), so the same reflections are F/sigma(F) >= 2x for target F
  cutoff = float(_param("strong_cutoff", 2.0))
  if str(_param("target", "F")) == "F":
    cutoff *= 2
  args += ["-xcw_strong_cutoff", "%g" % cutoff]
  if _param("incremental") == True:
    args.append("-xcw_incremental")
  args += ["-xcw_int_precision", str(_param("int_precision", 1e-10))]
  if _param("extrapolate", True) != True:
    args.append("-no_xcw_extrapolate")
  if _param("use_gpu") != True:
    args.append("-no_gpu")
  from utilities import ri_fit_args, tshb_supported
  # ponytail: tfvc/mbis/embis grid XCW give R1 ~0.57 (the weights see no density) until the next NoSpherA2 round
  partition = str(_param("partition", "hirshfeld"))
  if partition == "becke":
    args.append("-becke")
  tshb = _param("tshb") == True and tshb_supported()
  if partition == "ri" or tshb:
    args += ri_fit_args()
  if partition == "ri":
    args += ["-xcw_partition", "ri"]
  if tshb:
    args.append("-tshb")
  return args


class _Runner(threading.Thread):
  def __init__(self, args, folder):
    threading.Thread.__init__(self)
    self.args = args
    self.folder = folder

  def run(self):
    olex_core.IncRunningThreadsCount()
    try:
      env = dict(os.environ)
      env["OCC_DATA_PATH"] = os.path.join(os.path.dirname(OV.GetVar("NoSpherA2")), "occ", "share")
      startinfo = None
      flags = 0
      if sys.platform[:3] == "win":
        from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW, SW_HIDE
        startinfo = STARTUPINFO()
        startinfo.dwFlags |= STARTF_USESHOWWINDOW
        startinfo.wShowWindow = SW_HIDE
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
      with open(os.path.join(self.folder, "XCW_console.log"), "w") as log:
        _state["proc"] = subprocess.Popen(self.args, cwd=self.folder, stdout=log, stderr=subprocess.STDOUT,
                                          startupinfo=startinfo, creationflags=flags, env=env)
        rc = _state["proc"].wait()
      _state["message"] = "" if rc == 0 else "NoSpherA2 exited with %d, see NoSpherA2.log in %s" % (rc, _folder)
    except Exception:
      sys.stderr.formatExceptionInfo()
      _state["message"] = "failed to start NoSpherA2"
    finally:
      _state["proc"] = None
      olex_core.DecRunningThreadsCount()
      olx.Schedule(1, "spy.NoSpherA2.xcw_finished()")


def _log_lines():
  path = os.path.join(_job_dir(), "NoSpherA2.log")
  if not os.path.isfile(path):
    return []
  try:
    with open(path, "r", errors="replace") as fh:
      return fh.read().splitlines()
  except Exception:
    return []


def _last_lambda_row(lines):
  """The last 'Lambda ... ' data row; the header is tab separated, the rows start with a number."""
  in_table = False
  last = ""
  for line in lines:
    if line.startswith("Lambda"):
      in_table = True
      continue
    if in_table:
      s = line.strip()
      if s and (s[0].isdigit() or s[0] == "-"):
        last = " ".join(s.split())
      elif s:
        in_table = False
  return last


def xcw_status():
  t = _state["thread"]
  if t is not None and t.is_alive():
    row = _last_lambda_row(_log_lines())
    return "running: " + row if row else "running"
  if _state["message"]:
    return _state["message"]
  for line in reversed(_log_lines()):
    if line.startswith("Recommended halting lambda"):
      return line.strip()
    if line.startswith("Finished XCW"):
      return "finished, no halting lambda reported"
  return "not run"


def xcw_tscb_list():
  """The NA2_<lambda>.tscb/.tshb files of the last run as combo items, newest run only."""
  files = sorted(glob.glob(os.path.join(_job_dir(), "NA2_*.tscb")) + glob.glob(os.path.join(_job_dir(), "NA2_*.tshb")))
  return ";".join(os.path.basename(f) for f in files)


def xcw_run():
  """Writes cif, hkl and the settings file, then starts NoSpherA2 -do_XCW in the background."""
  t = _state["thread"]
  if t is not None and t.is_alive():
    print("XCW: a job is still running")
    return
  name = _name()
  folder = _job_dir()
  if os.path.isdir(folder):
    for f in glob.glob(os.path.join(folder, "NA2_*")) + glob.glob(os.path.join(folder, "*.log")):
      try:
        os.remove(f)
      except OSError:
        pass
  else:
    os.makedirs(folder)
  n_params = _n_params()
  if n_params <= 0:
    print("XCW: the number of refined parameters is unknown - run a refinement first or set Params")
    return
  try:
    olex.m("CifCreate_4NoSpherA2")
    shutil.move(os.path.join(OV.FilePath(), name + ".cif_NoSpherA2"), os.path.join(folder, name + ".cif"))
    _append_dispersion(os.path.join(folder, name + ".cif"))
    _write_hkl(os.path.join(folder, name + ".hkl"))
    _write_anom_disp(os.path.join(folder, "anom_disp.txt"))
    settings = name + "_xcw_settings.txt"
    _write_settings(os.path.join(folder, settings), n_params)
  except Exception as e:
    _state["message"] = "could not prepare the input: %s: %s" % (type(e).__name__, e)
    print("XCW: %s" % _state["message"])
    sys.stderr.formatExceptionInfo()
    return
  args = _args(folder, name, settings)
  with open(os.path.join(folder, "XCW_command.txt"), "w") as out:
    out.write(" ".join(args) + "\n")
  _state["message"] = ""
  nsa2_set_param("XCW.selected_tscb", "")
  _state["thread"] = _Runner(args, folder)
  _state["thread"].start()
  print("XCW: fitting %s in %s with %d parameters, lambda %s to %s step %s" % (
    _param("basis_name", nsa2_get_param("basis_name")), _folder, n_params,
    _param("start", 0.0), _param("end", 1.0), _param("step_size", 0.01)))


def xcw_stop():
  p = _state["proc"]
  if p is None:
    print("XCW: nothing is running")
    return
  try:
    p.kill()
    _state["message"] = "stopped"
    print("XCW: job stopped")
  except Exception as e:
    print("XCW: could not stop the job: %s" % e)


def xcw_finished():
  _state["thread"] = None
  tscbs = xcw_tscb_list()
  if tscbs:
    last = tscbs.split(";")[-1]
    nsa2_set_param("XCW.selected_tscb", last)
    print("XCW: %s - %d table(s) in %s" % (xcw_status(), len(tscbs.split(";")), _folder))
  elif not _state["message"]:
    _state["message"] = "finished without tables, see NoSpherA2.log in %s" % _folder
  olex.m("html.Update")


def xcw_use_tscb():
  """Copies the chosen table next to the structure and makes it the NoSpherA2 source."""
  from utilities import reset_unused_generator_flags
  from NoSpherA2 import get_NoSpherA2_instance
  chosen = _param("selected_tscb")
  if not chosen:
    print("XCW: choose a table first")
    return
  src = os.path.join(_job_dir(), chosen)
  if not os.path.isfile(src):
    print("XCW: %s not found" % src)
    return
  lam, ext = os.path.splitext(chosen)
  target = "%s_xcw_%s%s" % (_name(), lam.replace("NA2_", ""), ext)
  shutil.copy(src, os.path.join(OV.FilePath(), target))
  nsa2_set_param("source", target)
  reset_unused_generator_flags(target)
  get_NoSpherA2_instance().set_tsc_file_with_metadata(target, "XCW")
  print("XCW: %s is now the tsc source" % target)


for _f in (xcw_run, xcw_stop, xcw_status, xcw_finished, xcw_tscb_list, xcw_use_tscb, xcw_basis_list):
  OV.registerFunction(_f, False, "NoSpherA2")
