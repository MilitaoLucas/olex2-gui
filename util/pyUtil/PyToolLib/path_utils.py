import os
import sys
import shutil
from datetime import datetime

import olx

def setup_cctbx(run_cold_start=False):
  build_path = ""
  basedir = olx.BaseDir()
  cctbx_dir = os.environ.get('OLEX2_CCTBX_DIR')
  if cctbx_dir and os.path.isdir(cctbx_dir):
    # check if the build is given, the ../modules/cctbx_project will be set as sources
    if os.path.exists(os.path.join(cctbx_dir, "SConstruct")):
      build_path = os.environ['LIBTBX_BUILD'] = os.path.normpath(cctbx_dir)
      import pathlib
      cctbxRoot = pathlib.Path(cctbx_dir).parent.absolute()
      print("Changing cctbx root to %s" %cctbxRoot)
    else:
      cctbxRoot = cctbx_dir
  else:
    cctbxRoot = os.path.join(basedir, "cctbx")
  if not build_path:
    build_path = os.environ['LIBTBX_BUILD'] = os.path.normpath(
      "%s/cctbx_build" % cctbxRoot)
    cctbxSources = "%s/cctbx_sources" %cctbxRoot
  else:
    cctbxSources = "%s/modules/cctbx_project" %cctbxRoot
  sys.path.append("%s/libtbx" % cctbxSources) # needed to work with old cctbx directory structure
  sys.path.append("%s/libtbx/pythonpath" % cctbxSources) # needed to work with new cctbx directory structure
  sys.path.append(cctbxSources) # needed to work with new cctbx directory structure
  need_cold_start = False
  try:
    sys.on_sys_exit_raise = Exception("cold_start")
    import libtbx.load_env
    # XXX backward incompatibility 2011-10
    if not hasattr(libtbx.env, 'relocatable'):
      need_cold_start = True
    else:
      envi_path = os.path.normpath(abs(libtbx.env.build_path))
      if sys.platform.startswith('win'):
        envi_path = envi_path.lower()
        build_path = build_path.lower()
      need_cold_start = (not os.path.exists(envi_path)
                         or envi_path != build_path)
  except IOError as err:
    if err.args[1] == 'No such file or directory' and err.filename.endswith('libtbx_env'):
      need_cold_start = True
    else:
      raise
  except AssertionError as err:
    need_cold_start = True
  except Exception as err:
    if str(err) == "cold_start":
      need_cold_start = True
    else:
      TAG_file_path = "%s/TAG" %build_path
      ENV_file_path = "%s/libtbx_env" %build_path
      need_cold_start = not os.path.exists(ENV_file_path) or\
         (os.path.exists(TAG_file_path) and
            os.stat(TAG_file_path).st_mtime > os.stat(ENV_file_path).st_mtime)
      if not need_cold_start:
        raise
  if need_cold_start or run_cold_start:
    cold_start(cctbxSources, build_path)
    import libtbx.load_env
    reload(libtbx.load_env)
  cctbxRoot = os.path.realpath(cctbxRoot)
  if sys.platform.startswith('win'):
    root = str(cctbxRoot).lower()
    for i in libtbx.env.pythonpath:
      i = os.path.realpath(abs(i)).lower()
      if not i.startswith(root):
        #print("skpping '%s'" %i)
        continue
      sys.path.append(i)
  else:
    for i in libtbx.env.pythonpath:
      sys.path.append(abs(i))
  if sys.platform.startswith('win'):
    lib_path, lib_sep = 'PATH', ';'
  elif sys.platform.startswith('darwin'):
    lib_path, lib_sep = 'DYLD_LIBRARY_PATH', ':'
  elif sys.platform.startswith('linux'):
    lib_path, lib_sep = 'LD_LIBRARY_PATH', ':'
  else:
    lib_path, lib_sep = 'LD_LIBRARY_PATH', ':'
    # Added as if not os.environ[lib_path] gives false positive is the key is missing
  if not cctbx_dir:
    os.environ['OLEX2_CCTBX_DIR'] = cctbxRoot
  if lib_path in os.environ:
    # synchronise current values as Python anc CRT use cached values!
    os.environ[lib_path] = olx.GetEnv(lib_path)
    if not os.environ[lib_path] or os.environ[lib_path].endswith(lib_sep):
      os.environ[lib_path] += abs(libtbx.env.lib_path)
    else:
      os.environ[lib_path] += lib_sep + abs(libtbx.env.lib_path)
  else:
    os.environ[lib_path] = abs(libtbx.env.lib_path)
  # double check!
  if not need_cold_start and not run_cold_start and False:
    try:
      from cctbx import xray
    except Exception as err:
      print("IMPORT FAILD" + str(err))
      if "boost_python_meta_ext" in str(err):
        setup_cctbx(True)

def cold_start(cctbx_sources, build_path):
  saved_cwd = os.getcwd()
  os.chdir(build_path)
  sys.argv = ['%s/libtbx/configure.py' % cctbx_sources, 'smtbx', 'iotbx', 'fast_linalg']
  #execfile(sys.argv[0])
  import libtbx.configure
  libtbx.configure.run()
  os.chdir(saved_cwd)
  import libtbx.load_env

def cleanup_files(file_ext):
  def cleanup_dir(dir):
    for f in os.listdir(dir):
      full_path = os.path.join(dir, f)
      if os.path.isfile(full_path) and f.endswith(file_ext):
        os.remove(full_path)
      elif os.path.isdir(full_path):
        cleanup_dir(full_path)
  try:
    cleanup_dir(os.path.join(olx.BaseDir(), "util", "pyUtil"))
  except:
    pass

def _cleanup_ac5(base_dir):
  ac5_dir = os.path.join(base_dir, "util", "pyUtil", "AC5")
  if os.path.exists(ac5_dir):
    try:
      shutil.rmtree(ac5_dir)
      ac5_files = [
        "lib/ac5util.so",
        "_ac5util.so",
        "_ac5util.pyd",
        "ac5util.dll",
      ]
      for f in ac5_files:
        f = os.path.join(base_dir, f)
        if os.path.exists(f):
          print("->%s" %f)
          os.remove(f)
    except Exception as e:
      print(e)

def _cleanup_ac6(base_dir):
  ac6_root_dir = os.path.join(base_dir, "util", "pyUtil")
  ac6_dir = os.path.join(ac6_root_dir, "AC6")
  if os.path.exists(ac6_dir):
    try:
      shutil.rmtree(ac6_dir)
      ac6_files = [
        "lib/ac6util.so",
        "_ac6util.so",
        "_ac6util.pyd",
        "ac6util.dll",
      ]
      for f in ac6_files:
        f = os.path.join(base_dir, f)
        if os.path.exists(f):
          print("->%s" %f)
          os.remove(f)
    except Exception as e:
      print(e)

def Cleanup():
  compilation_date = datetime.strptime(
    olx.GetCompilationInfo("yyyy.MM.dd").split()[0], "%Y.%m.%d")
  #print(compilation_date)
  cleanup_files(".tmp")
  base_dir = olx.BaseDir()
  # clean up old AC files
  ac6_dir = os.path.join(base_dir, "util", "pyUtil", "AC6")
  ac7_dir = os.path.join(base_dir, "util", "pyUtil", "AC7")
  if os.path.exists(ac7_dir):
    ac6d_dir = os.path.join(base_dir, "util", "pyUtil", "AC6d")
    if not os.path.exists(ac6d_dir): # abort if development environment
      _cleanup_ac5(base_dir)
      _cleanup_ac6(base_dir)
  elif os.path.exists(ac6_dir):
    _cleanup_ac5(base_dir)

  vi = sys.version_info
  if vi.major == 3 and vi.minor == 8 and vi.micro == 10:
    try:
      dirs = []
      if sys.platform[:3] == 'win':
        import platform
        sp_dir = os.path.join( "Python38", "Lib", "site-packages")
        dirs = [
          os.path.join(sp_dir, r"scipy\sparse\linalg\dsolve"),
          os.path.join(sp_dir, r"scipy\sparse\linalg\eigen"),
          os.path.join(sp_dir, r"scipy\sparse\linalg\isolve"),
        ]
        if platform.architecture()[0] != "32bit":
          dirs.append(os.path.join(sp_dir, r"scipy\.libs"))
        files = [
          "libopenblas.PYQHXLVVQ7VESDPUVUADXEVJOBGHJPAY.gfortran-win_amd64.dll",
          "libopenblas.SVHFG5YE3RK3Z27NVFUDAPL2O3W6IMXW.gfortran-win32.dll",
          ]
        files.append(os.path.join(sp_dir, "numpy", ".libs", files[0]))
        files.append(os.path.join(sp_dir, "numpy", ".libs", files[1]))
        for f in files:
          f = os.path.join(base_dir, f)
          if os.path.exists(f):
            print("Cleaning up: %s" %f)
            os.remove(f)
      elif sys.platform[:3] == 'lin':
        sp_dir = os.path.join("lib", "python3.8", "site-packages")
        dirs = [os.path.join(sp_dir, x) for x in ("scipy-1.2.3-py3.8-linux-x86_64.egg",
                                                  "numpy-1.18.2-py3.8-linux-x86_64.egg")]
      else:
        sp_dir = os.path.join("lib", "python3.8", "site-packages")
        #dirs = [os.path.join(sp_dir, x) for x in ("scipy", "numpy")]
      #clean up old numpy/scipy
      for d in dirs:
        d = os.path.join(base_dir, d)
        if not os.path.exists(d):
          continue
        try:
          print("->%s" %d)
          shutil.rmtree(d)
        except Exception as e:
          print(e)
    except Exception as e:
      print(e)
