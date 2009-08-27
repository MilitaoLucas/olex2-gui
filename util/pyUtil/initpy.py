# initpy.py
import olex
import sys

debug = True
if debug == True:
  try:
    import wingdbstub
  except:
    pass

datadir = olex.f("DataDir()")
basedir = olex.f("BaseDir()")
if sys.platform[:3] == 'win':
  sys.path = [''] # first should be empty string to avoid problem if cctbx needs cold start
  python_dir = "%s/Python26" %basedir
  sys.path.append(python_dir)
  sys.path.append("%s/DLLs" %python_dir)
  sys.path.append("%s/Lib" %python_dir)
  sys.path.append("%s/Lib/site-packages" %python_dir)
  sys.path.append("%s/Lib/site-packages/PIL" %python_dir)
else:
  set_sys_path = True
  try:
    import os
    set_sys_path = os.path.exists(basedir + '/Python26')
  except:
    pass
  if set_sys_path:
    sys.prefix = basedir + '/Python26'
    sys.path = ['',
      sys.prefix + '/python2.6',
      sys.prefix + '/python2.6/lib-tk',
      sys.prefix + '/python2.6/lib-old',
      sys.prefix + '/python2.6/lib-dynload',
      sys.prefix + '/python2.6/site-packages',
      sys.prefix + '/python2.6/site-packages/PIL'
    ]
    if sys.platform == 'darwin':
      sys.path.append(sys.prefix + '/python2.6/plat-darwin')
      sys.path.append(sys.prefix + '/python2.6/plat-mac')
    elif sys.platform == 'linux2':
      sys.path.append(sys.prefix + '/python2.6/plat-linux2')
sys.path.append(datadir)
stdout_redirection = True

import os
import locale
import time

locale.setlocale(locale.LC_ALL, 'C') 


if os.environ.get('OLEX_DBG_NO_STDERR_REDIRECTION') is not None:
  stderr_redirection = False
else:
  stderr_redirection = True
''' Debug, if possible '''


def our_sys_exit(i):
  print "Terminate with %i" % i
sys.exit = our_sys_exit


class StreamRedirection:
  def __init__(self, stream, is_redirecting=True):
    self.redirected = stream
    self.is_redirecting = is_redirecting
    self.isErrorStream = (stream==sys.stderr)
    self.refresh=False
    self.graph=False
    self.t0 = time.time()

    if self.isErrorStream:
      self.errFile = open("%s/PythonError.log" %olex.f("DataDir()"), 'w')
      self.version = olex.f("GetCompilationInfo()")
      try:
        rFile = open("%s/version.txt" %olex.f("BaseDir()"), 'r')
        self.GUIversion = rFile.readline()
        rFile.close()
      except:
        self.GUIversion = "unknown"
      self.errFile.write("================= PYTHON ERROR ================= Olex Version %s -- %s\n\n" %(self.version, self.GUIversion))
      
  def write(self, Str):
    if self.is_redirecting:
      if self.isErrorStream:
        self.errFile.write(Str)
        self.errFile.flush()
      olex.post( '\'' + Str + '\'')
      if self.refresh:
        t1 = time.time()
        if t1 - self.t0 > 1:
          olex.m("refresh")
          self.t0 = t1
      if self.graph!=False:
        self.graph(Str)
        
    else:
      self.redirected.write(Str)
      
  def flush(self):
    pass
  
  def formatExceptionInfo(maxTBlevel=5):
    import traceback
    import inspect
    import tokenize
    traceback.print_exc()
    tb = sys.exc_info()[2]
    OV.Cursor("")
    if tb is not None:
      while tb.tb_next is not None: tb = tb.tb_next
      frame = tb.tb_frame
      lineno = frame.f_lineno
      filename = inspect.getsourcefile(frame) or inspect.getfile(frame)
      def reader():
        yield open(filename).readlines()[lineno-1]
      recording_args = False
      args = {}
      try:
        for ttype, token, start, end, line in inspect.tokenize.generate_tokens(reader().next):
          if ttype == tokenize.NAME and token in frame.f_locals:
            args[token] = frame.f_locals[token]
        if args:
          print >> sys.stderr, 'Key variable values:'
          for var,val in args.iteritems():
            print >> sys.stderr, '\t%s = %s' % (var, repr(val))
      except inspect.tokenize.TokenError:
        pass

def get_prg_roots():
  prg_roots = {}
  path = r"%s/util/pyUtil/prg_root.txt" %basedir
  try:
    rFile = open(path)
  except:
    pass
  for li in rFile:
    prg = li.split('=')[0]
    root = li.split('=')[1]
    root = root.strip('"')
    prg_roots.setdefault(prg, root)
  retval = prg_roots
  return retval

def print_python_version():
  ''' Print Python Version '''
  version = sys.version
  if debug: print
  if debug: print
  if debug: print "** %s **" % version
  version = version[:3]
  retval = version
  return version

def set_olex_paths():
  sys.path.append("%s" %basedir)
  sys.path.append("%s/util/pyUtil" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib/FileReaders" %basedir)
  sys.path.append("%s/util/pyUtil/CctbxLib" %basedir)  

def set_plugins_paths():  
  plugins = olexex.InstalledPlugins()
  for plugin in plugins:
    sys.path.append("%s/util/pyUtil/PluginLib/plugin-%s" %(basedir,plugin))
    
    ##Dependencies
    if plugin == "plugin-SQLAlchemy":
      sys.path.append("%s/util/pyUtil/PythonLib/sqlalchemy" %basedir)
  
def setup_cctbx():
  cctbx_dir = os.environ.get('OLEX2_CCTBX_DIR')
  if cctbx_dir and os.path.isdir(cctbx_dir):
    cctbxRoot = cctbx_dir
  else:
    cctbxRoot = str("%s/cctbx" %basedir)
  build_path = os.environ['LIBTBX_BUILD'] = os.path.normpath(str("%s/cctbx_build" % cctbxRoot))
  if os.path.isdir("%s/cctbx_project" %cctbxRoot):
    cctbxSources = "%s/cctbx_project" %cctbxRoot
  else:
    cctbxSources = "%s/cctbx_sources" %cctbxRoot
  sys.path.append(str("%s/libtbx" % cctbxSources)) # needed to work with old cctbx directory structure
  sys.path.append(str("%s/libtbx/pythonpath" % cctbxSources)) # needed to work with new cctbx directory structure
  sys.path.append(str(cctbxSources)) # needed to work with new cctbx directory structure
  try:
    import libtbx.load_env
    need_cold_start = not os.path.exists(libtbx.env.build_path)
  except IOError, err:
    if err.args[1] == 'No such file or directory' and err.filename.endswith('libtbx_env'):
      need_cold_start = True
    else:
      raise
  except Exception, err:
    raise
  cctbx_TAG_file_path = "%s/TAG" %cctbxSources
  if not os.path.isdir('%s/.svn' %cctbxSources)\
     and os.path.exists(cctbx_TAG_file_path):
    cctbx_TAG_file = open("%s/TAG" %cctbxSources,'r')
    cctbx_compile_date = cctbx_TAG_file.readline().strip()
    cctbx_TAG_file.close()
    cctbx_compatible_version = "2008_09_13_0905"
    if int(cctbx_compile_date.replace('_','')) < int(cctbx_compatible_version.replace('_','')):
      sys.stdout.write("""An incompatible version of the cctbx is installed.
      Please update to cctbx build '%s' or later.
      """ %cctbx_compatible_version)

  if need_cold_start:
    saved_cwd = os.getcwd()
    os.chdir(build_path)
    sys.argv = ['%s/libtbx/configure.py' % cctbxSources, 'smtbx', 'iotbx']
    execfile(sys.argv[0])
    os.chdir(saved_cwd)
    import libtbx.load_env
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
    
  # Import these files now to reduce time taken on running cctbx for the first time
  #import my_refine_util
  import cctbx_olex_adapter
  import cctbx_controller

''' Redirect prints to Olex '''
sys.stdout = StreamRedirection(sys.stdout, stdout_redirection)
sys.stderr = StreamRedirection(sys.stderr, stderr_redirection)

import olx

basedir = olx.BaseDir()
datadir = olx.DataDir()

set_olex_paths()

try:
  setup_cctbx()
except Exception, err:
  print "There is a problem with the cctbx"
  print err

import variableFunctions
variableFunctions.InitialiseVariables('startup')
variableFunctions.LoadParams()
import olexex
import CifInfo # import needed to register functions to olex

set_plugins_paths()

#if debug:
# version = print_python_version()
#try:
# prg_roots = get_prg_roots()
#except:
# pass


from olexFunctions import OlexFunctions
OV = OlexFunctions()
if OV.HasGUI():
  import htmlMaker

olx.Clear()

#if debug:
#       keys = os.environ.keys()
#       keys.sort()
#       for k in keys:
#               print "%s\t%s" %(k, os.environ[k])
#
#       for bit in sys.path:
#               print bit
    
if olx.IsPluginInstalled('plugin-Batch') == "true":
  import plugin_batch_exex

if olx.IsPluginInstalled('Olex2Portal') == "true":
    import olex_logon
  
  
if olx.IsPluginInstalled('MySQL') == "true":
  try:
    import OlexToMySQL
    from OlexToMySQL import DownloadOlexLanguageDictionary
    a = DownloadOlexLanguageDictionary()
    #olex.registerFunction(a.downloadTranslation)
  except Exception, ex:
    print "MySQL Plugin is installed but a connection to the default server could not be established"
    print ex

if olexex.getKey():
  olexex.GetACF()

olexex.check_for_recent_update()

if sys.platform[:3] == 'win':
  OV.SetVar('defeditor','notepad')
  OV.SetVar('defexplorer','explorer')
#else:
  #olx.SetVar('defeditor','gedit')
  #olx.SetVar('defexplorer','nautilus')

print "Welcome to Olex2"


## These imports will register macros and functions for spy.  
if OV.HasGUI():
  from Skin import Skin
  from Analysis import Analysis
from RunPrg import RunPrg

