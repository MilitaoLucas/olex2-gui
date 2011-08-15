import os
import sys

import olx

def setup_cctbx():
  basedir = olx.BaseDir()
  cctbx_dir = os.environ.get('OLEX2_CCTBX_DIR')
  if cctbx_dir and os.path.isdir(cctbx_dir):
    cctbxRoot = cctbx_dir
  else:
    cctbxRoot = str("%s/cctbx" %basedir)
  build_path = os.environ['LIBTBX_BUILD'] = os.path.normpath(
    str("%s/cctbx_build" % cctbxRoot))
  if os.path.isdir("%s/cctbx_project" %cctbxRoot):
    cctbxSources = "%s/cctbx_project" %cctbxRoot
  else:
    cctbxSources = "%s/cctbx_sources" %cctbxRoot
  sys.path.append(str("%s/libtbx" % cctbxSources)) # needed to work with old cctbx directory structure
  sys.path.append(str("%s/libtbx/pythonpath" % cctbxSources)) # needed to work with new cctbx directory structure
  sys.path.append(str(cctbxSources)) # needed to work with new cctbx directory structure
  try:
    import libtbx.load_env
    if os.name == "nt":
      cleaned_build_path = libtbx.env.abs_path_clean(build_path)
    else:
      cleaned_build_path = build_path
    need_cold_start = (not os.path.exists(libtbx.env.build_path)
                       or libtbx.env.build_path != cleaned_build_path)
  except IOError, err:
    if err.args[1] == 'No such file or directory' and err.filename.endswith('libtbx_env'):
      need_cold_start = True
    else:
      raise
  except AssertionError, err:
    need_cold_start = True
  except Exception, err:
    raise
  cctbx_TAG_file_path = "%s/TAG" %cctbxSources
  if not os.path.isdir('%s/.svn' %cctbxSources)\
     and os.path.exists(cctbx_TAG_file_path):
    cctbx_TAG_file = open("%s/TAG" %cctbxSources,'r')
    cctbx_compile_date = cctbx_TAG_file.readline().strip()
    cctbx_TAG_file.close()
    cctbx_compatible_version = "2010_12_16_0000"
    if int(cctbx_compile_date.replace('_','')) < int(cctbx_compatible_version.replace('_','')):
      sys.stdout.write("""Warning: An incompatible version of the cctbx is installed.
Please update to cctbx build '%s' or later.
Current cctbx build: '%s'
""" %(cctbx_compatible_version, cctbx_compile_date))
  if not need_cold_start:
    need_cold_start = not libtbx.env.has_module('antlr3')
  if need_cold_start:
    cold_start(cctbxSources, build_path)
    import libtbx.load_env
    reload(libtbx.load_env)
  sys.path.extend(libtbx.env.pythonpath)
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
  if os.environ.has_key(lib_path):
    if not os.environ[lib_path] or os.environ[lib_path].endswith(lib_sep):
      os.environ[lib_path] += libtbx.env.lib_path
    else:
      os.environ[lib_path] += lib_sep + libtbx.env.lib_path
  else:
    os.environ[lib_path] = libtbx.env.lib_path

def cold_start(cctbx_sources, build_path):
  saved_cwd = os.getcwd()
  os.chdir(build_path)
  sys.argv = ['%s/libtbx/configure.py' % cctbx_sources, 'smtbx', 'iotbx']
  #execfile(sys.argv[0])
  import libtbx.configure
  libtbx.configure.run()
  os.chdir(saved_cwd)
  import libtbx.load_env
