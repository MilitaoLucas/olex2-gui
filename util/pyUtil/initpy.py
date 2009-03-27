# initpy.py
import olex
import sys

debug = True
if debug == True:
  try:
    import wingdbstub
  except:
    pass


if sys.platform[:3] == 'win':
  sys.path = []
sys.path.insert(0, olex.f("DataDir()"))
sys.path.append(r"%s/util/pyUtil" %olex.f("BaseDir()"))
python_lib = r"%s/util/pyUtil/PythonLib" %olex.f("BaseDir()")
#pyTool_lib = r"%s/util/pyUtil/PyToolLib" %olex.f("BaseDir()")
#file_readers_lib = r"%s/FileReaders" %pyTool_lib
sys.path.insert(0, python_lib)
#sys.path.insert(0, pyTool_lib)
#sys.path.insert(0, file_readers_lib)
stdout_redirection = True
import os
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
        olex.m("refresh")
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
  python_dir = "%s/util/pyUtil/PythonLib" %basedir
  #python_dir = "%s/util/pyUtil/PythonLib2.6" %basedir
  sys.path.append("%s" %basedir)
  sys.path.append("%s" %datadir)
  sys.path.append("%s/util/pyUtil" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib/FileReaders" %basedir)
  sys.path.append("%s/util/pyUtil/CctbxLib" %basedir)
  sys.path.append("%s/MySQLdb" %python_dir)
  sys.path.append("%s/encodings" %python_dir)
  sys.path.append("%s/PIL" %python_dir)
  sys.path.append(python_dir)
  sys.path.append("%s/util/pyUtil/PluginLib" %basedir)

def set_plugins_paths():  
  plugins = olexex.InstalledPlugins()
  for plugin in plugins:
    sys.path.append("%s/util/pyUtil/PluginLib/%s" %(basedir,plugin))
    
    ##Dependencies
    if plugin == "plugin-SQLAlchemy":
      sys.path.append("%s/util/pyUtil/PythonLib/sqlalchemy" %basedir)
  
def setup_cctbx():
  cctbx_dir = os.environ.get('OLEX2_CCTBX_DIR')
  if cctbx_dir and os.path.isdir(cctbx_dir):
    cctbxRoot = cctbx_dir
  else:
    cctbxRoot = str("%s/util/pyUtil/CctbxLib/cctbx_win" %basedir)
  build_path = os.environ['LIBTBX_BUILD'] = os.path.normpath(str("%s/cctbx_build" % cctbxRoot))
  sys.path.append(str("%s/cctbx_sources/libtbx" % cctbxRoot)) # needed to work with old cctbx directory structure
  sys.path.append(str("%s/cctbx_sources/libtbx/pythonpath" % cctbxRoot)) # needed to work with new cctbx directory structure
  sys.path.append(str("%s/cctbx_sources" % cctbxRoot)) # needed to work with new cctbx directory structure
  try:
    import libtbx.load_env
  except IOError, err:
    if err.args[1] == 'No such file or directory' and err.filename.endswith('libtbx_env'):
      need_cold_start = True
    else:
      raise
  else:
    need_cold_start = not os.path.exists(libtbx.env.build_path)
  cctbx_TAG_file_path = "%s/cctbx_sources/TAG" %cctbxRoot
  if not os.path.isdir('%s/cctbx_sources/.svn' %cctbxRoot)\
     and os.path.exists(cctbx_TAG_file_path):
    cctbx_TAG_file = open("%s/cctbx_sources/TAG" %cctbxRoot,'r')
    cctbx_compile_date = cctbx_TAG_file.readline().strip()
    cctbx_TAG_file.close()
    cctbx_compatibale_version = "2008_09_13_0905"
    if int(cctbx_compile_date.replace('_','')) < int(cctbx_compatibale_version.replace('_','')):
      sys.stdout.write("""An incompatible version of the cctbx is installed.
      Please update to cctbx build '%s' or later.
      """ %cctbx_compatibale_version)
      
  if need_cold_start:
    saved_cwd = os.getcwd()
    os.chdir(build_path)
    sys.argv = ['%s/cctbx_sources/libtbx/configure.py' % cctbxRoot, 'smtbx', 'iotbx']
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
    #print "%s key is present"%lib_path
    if not os.environ[lib_path] or os.environ[lib_path].endswith(lib_sep):
      os.environ[lib_path] += libtbx.env.lib_path
    else:
      os.environ[lib_path] += lib_sep + libtbx.env.lib_path
  else:
    #print "%s is NOT present ADDING"%lib_path
    #print "libtbx.env.lib_path = %s"%libtbx.env.lib_path
    os.environ[lib_path] = libtbx.env.lib_path
    #print "State of os.environ %s"%os.environ[lib_path]
    
  # Import these files now to reduce time taken on running cctbx for the first time
  #import my_refine_util
  import cctbx_olex_adapter
  import cctbx_controller
  
# Org code!    
#  if not os.environ[lib_path] or os.environ[lib_path].endswith(lib_sep):
#    os.environ[lib_path] += libtbx.env.lib_path
#  else:
#    os.environ[lib_path] += lib_sep + libtbx.env.lib_path

''' Redirect prints to Olex '''
sys.stdout = StreamRedirection(sys.stdout, stdout_redirection)
sys.stderr = StreamRedirection(sys.stderr, stderr_redirection)

import olx

basedir = olx.BaseDir()
datadir = olx.DataDir()

set_olex_paths()

import variableFunctions
variableFunctions.InitialiseVariables('startup')
import olexex

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

if OV.IsPluginInstalled('plugin-cctbx'):
  #set_cctbx_paths()
  try:
    setup_cctbx()
  except Exception, err:
    print "There is a problem with the cctbx"
    print err

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
if olx.IsPluginInstalled('plugin-MySQL') == "true":
  try:
    from OlexToMySQL import DownloadOlexLanguageDictionary
    a = DownloadOlexLanguageDictionary()
    olex.registerFunction(a.downloadTranslation)
  except:
    print "MySQL Plugin is installed but a connection to the default server could not be established."

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
  
  
## Thes imports will register macros and functions for spy.  
if OV.HasGUI():
  from Skin import Skin
  from Analysis import Analysis
from RunPrg import RunPrg

