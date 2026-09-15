"""X-ray constrained wavefunction fitting from the NoSpherA2 refine tab.

Experimental. The block (hybrid_GUI.make_XCW_GUI) is shown only with
user.NoSpherA2.show_XCW. What it does:

  Run XCW  writes olex2/XCW/<name>.cif, <name>.hkl and <name>_xcw_settings.txt
           from the snum.NoSpherA2.XCW parameters and starts
           NoSpherA2 -do_XCW ... in the background, cwd = that folder
  Stop     kills the job
  status   the last lambda row of NoSpherA2.log while it runs, the recommended
           halting lambda when it finished
  Use      copies the chosen NA2_<lambda>.tscb next to the structure as
           <name>_xcw_<lambda>.tscb and makes it the tsc source

Still to do: the parameter count is taken from the last refinement only when
one has run (params = 0 in the phil); charge/multiplicity are the shared
NoSpherA2 values; twin laws are not passed.
"""

import glob
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
  n = int(_param("params", 0) or 0)
  if n > 0:
    return n
  try:
    from gui.tools import get_parameter_number, GetNParams
    n = int(get_parameter_number() or 0)
    if n <= 0:  # nothing refined yet in this session: count the parameters now
      GetNParams()  # stores the count in a variable, returns nothing
      n = int(get_parameter_number() or 0)
  except Exception:
    n = 0
  return n


def _write_settings(path, n_params):
  """The settings file NoSpherA2 reads with -XCW_settings (XCW.cpp), one keyword per line."""
  lines = [
    str(_param("scf_preset", "normal")),
    str(_param("conv_preset", "normal_conv")),
    "params %d" % n_params,
    "basis_set %s" % _param("basis_name", nsa2_get_param("basis_name")),
  ]
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
  exe = OV.GetVar("NoSpherA2")
  args = [exe, "-do_XCW", "-cif", name + ".cif", "-hkl", name + ".hkl", "-XCW_settings", settings,
          "-cpus", str(nsa2_get_param("ncpus")), "-mem", str(float(nsa2_get_param("mem")) * 1000), "-no_date",
          "-charge", str(_charge()), "-mult", str(_mult())]
  anom = _param("anom_disp_file")
  if anom:
    if not os.path.isabs(anom):
      anom = os.path.join(OV.FilePath(), anom)
    if os.path.isfile(anom):
      shutil.copy(anom, os.path.join(folder, "anom_disp.txt"))
      args += ["-anom_disp", "anom_disp.txt"]
    else:
      print("XCW: anomalous dispersion file %s not found, running without" % anom)
  if _param("gaussian_halt") == True:
    args.append("-xcw_gaussian_halt")
  args += ["-xcw_strong_cutoff", str(_param("strong_cutoff", 3.0))]
  if _param("incremental") == True:
    args.append("-xcw_incremental")
  args += ["-xcw_int_precision", str(_param("int_precision", 1e-10))]
  if _param("extrapolate", True) != True:
    args.append("-no_xcw_extrapolate")
  if _param("use_gpu") != True:
    args.append("-no_gpu")
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
  """The NA2_<lambda>.tscb files of the last run as combo items, newest run only."""
  files = sorted(glob.glob(os.path.join(_job_dir(), "NA2_*.tscb")))
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
    _write_hkl(os.path.join(folder, name + ".hkl"))
    settings = name + "_xcw_settings.txt"
    _write_settings(os.path.join(folder, settings), n_params)
  except Exception as e:
    print("XCW: could not prepare the input: %s: %s" % (type(e).__name__, e))
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
  lam = os.path.splitext(chosen)[0].replace("NA2_", "")
  target = "%s_xcw_%s.tscb" % (_name(), lam)
  shutil.copy(src, os.path.join(OV.FilePath(), target))
  nsa2_set_param("source", target)
  reset_unused_generator_flags(target)
  get_NoSpherA2_instance().set_tsc_file_with_metadata(target, "XCW")
  print("XCW: %s is now the tsc source" % target)


for _f in (xcw_run, xcw_stop, xcw_status, xcw_finished, xcw_tscb_list, xcw_use_tscb):
  OV.registerFunction(_f, False, "NoSpherA2")
