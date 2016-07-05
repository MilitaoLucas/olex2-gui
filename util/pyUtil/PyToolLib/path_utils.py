import os
import sys

import olx

def setup_cctbx():
  basedir = olx.BaseDir().encode('utf-8')
  cctbx_dir = os.environ.get('OLEX2_CCTBX_DIR')
  if cctbx_dir and os.path.isdir(cctbx_dir):
    cctbxRoot = cctbx_dir
  else:
    cctbxRoot = "%s/cctbx" %basedir
  build_path = os.environ['LIBTBX_BUILD'] = os.path.normpath(
    "%s/cctbx_build" % cctbxRoot)
  if os.path.isdir("%s/cctbx_project" %cctbxRoot):
    cctbxSources = "%s/cctbx_project" %cctbxRoot
  else:
    cctbxSources = "%s/cctbx_sources" %cctbxRoot
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
  except IOError, err:
    if err.args[1] == 'No such file or directory' and err.filename.endswith('libtbx_env'):
      need_cold_start = True
    else:
      raise
  except AssertionError, err:
    need_cold_start = True
  except Exception, err:
    if str(err) == "cold_start":
      need_cold_start = True
    else:
      TAG_file_path = "%s/TAG" %build_path
      ENV_file_path = "%s/libtbx_env" %build_path
      need_cold_start =\
        os.stat(TAG_file_path).st_mtime > os.stat(ENV_file_path).st_mtime
      if not need_cold_start:
        raise
  cctbx_TAG_file_path = "%s/TAG" %cctbxSources
  if not os.path.isdir('%s/.svn' %cctbxSources)\
     and os.path.exists(cctbx_TAG_file_path):
    cctbx_TAG_file = open("%s/TAG" %cctbxSources,'r')
    cctbx_compile_date = cctbx_TAG_file.readline().strip()
    cctbx_TAG_file.close()
    cctbx_compatible_version = "2011_10_10_0000"
    if int(cctbx_compile_date.replace('_','')) < int(cctbx_compatible_version.replace('_','')):
      sys.stdout.write("""Warning: An incompatible version of the cctbx is installed.
Please update to cctbx build '%s' or later.
Current cctbx build: '%s'
""" %(cctbx_compatible_version, cctbx_compile_date))
  if need_cold_start:
    cold_start(cctbxSources, build_path)
    import libtbx.load_env
    reload(libtbx.load_env)
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
  if os.environ.has_key(lib_path):
    # synchronise current values as Python anc CRT use cached values!
    os.environ[lib_path] = olx.GetEnv(lib_path)
    if not os.environ[lib_path] or os.environ[lib_path].endswith(lib_sep):
      os.environ[lib_path] += abs(libtbx.env.lib_path)
    else:
      os.environ[lib_path] += lib_sep + abs(libtbx.env.lib_path)
  else:
    os.environ[lib_path] = abs(libtbx.env.lib_path)

def cold_start(cctbx_sources, build_path):
  saved_cwd = os.getcwdu()
  os.chdir(build_path)
  sys.argv = ['%s/libtbx/configure.py' % cctbx_sources, 'smtbx', 'iotbx']
  #execfile(sys.argv[0])
  import libtbx.configure
  libtbx.configure.run()
  os.chdir(saved_cwd)
  import libtbx.load_env
