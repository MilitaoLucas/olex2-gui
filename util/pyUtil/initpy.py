# initpy.py
import sys
import olex
import os
import time
timer = True
if timer:
  t = time.time()
  beginning_of_t = t
  tt = []
  tt.append("= T I M I N G S ============================================")

datadir = olex.f("DataDir()")
basedir = olex.f("BaseDir()")
if sys.platform[:3] == 'win':
  sys.path = [''] # first should be empty string to avoid problem if cctbx needs cold start
  _ = os.environ.get("PYTHONHOME")
  if _:
    python_dir = _
  else:
    python_dir = r"%s\Python27" %basedir
  sys.path.append(python_dir)
  sys.path.append(r"%s\DLLs" %python_dir)
  sys.path.append(r"%s\Lib" %python_dir)
  sys.path.append(r"%s\Lib\site-packages" %python_dir)
  sys.path.append(r"%s\Lib\site-packages\PIL" %python_dir)
  sys.path.append(r"%s\Lib\site-packages\win32" %python_dir)
  sys.path.append(r"%s\Lib\site-packages\win32\lib" %python_dir)

else:
  set_sys_path = True
  try:
    import os
    set_sys_path = os.path.exists(basedir + '/lib/python2.7')
  except:
    pass
  if set_sys_path:
    sys.prefix = basedir + '/lib/python2.7'
    sys.path = ['',
      sys.prefix,
      sys.prefix + '/lib-tk',
      sys.prefix + '/lib-old',
      sys.prefix + '/lib-dynload',
      sys.prefix + '/site-packages',
      sys.prefix + '/site-packages/PIL'
    ]
    if sys.platform == 'darwin':
      sys.path.append(sys.prefix + '/plat-darwin')
      sys.path.append(sys.prefix + '/plat-mac')
    elif sys.platform == 'linux2':
      sys.path.append(sys.prefix + '/plat-linux2')
sys.path.append(datadir)
stdout_redirection = True

import os
import locale
def onexit():
  pass
olex.registerFunction(onexit,False)

debug = 'OLEX2_ATTACHED_WITH_PYDEBUGGER' in os.environ
if debug == True:
  try:
    import wingdbstub
  except:
    pass
# we need to use the user's locale for proper functioning of functions working
# with multi-byte strings
#locale.setlocale(locale.LC_ALL, 'C')

if os.environ.get('OLEX_DBG_NO_STDERR_REDIRECTION') is not None:
  stderr_redirection = False
else:
  stderr_redirection = True
''' Debug, if possible '''

if timer:
  tt.append("Initial imports took %.3f s" %(time.time() - t))
  t = time.time()


sys.on_sys_exit_raise = None
def our_sys_exit(i):
  '''
  some scripts call exit - and Olex2 does exit if not for this function
  '''
  if sys.on_sys_exit_raise:
    e = sys.on_sys_exit_raise
    sys.on_sys_exit_raise = None
    raise e
  print(("Terminate with %i" %i))
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
      self.errFile = open(os.path.join(datadir, "PythonError.log"), 'w')
      self.version = olex.f("GetCompilationInfo()")
      try:
        self.GUIversion = open(os.path.join(basedir, "version.txt"), 'r').readline()
      except:
        self.GUIversion = "unknown"
      self.errFile.write("================= PYTHON ERROR ================= Olex2 Version %s -- %s\n\n" %(self.version, self.GUIversion))

  def write(self, Str):
    if self.is_redirecting:
      if self.isErrorStream:
        self.errFile.write(Str)
        self.errFile.flush()
      olex.post( '\'' + Str + '\'')
      if self.refresh:
        t1 = time.time()
        if t1 - self.t0 > 0.5:
          olex.m("refresh")
          self.t0 = t1
      if self.graph!=False:
        self.graph(Str)

    else:
      self.redirected.write(Str)

  def flush(self):
    pass

  def formatExceptionInfo(self, maxTBlevel=5):
    import traceback
    import inspect
    import tokenize
    traceback.print_exc()
    tb = sys.exc_info()[2]
    if OV.HasGUI():
      olx.Cursor("")
    if tb is not None:
      while tb.tb_next is not None: tb = tb.tb_next
      frame = tb.tb_frame
      def reader():
        try:
          yield inspect.getsource(frame)
        except:
          print(">>>>> ERROR (formatExceptionInfo)")
      args = {}
      try:
        for ttype, token, start, end, line in inspect.tokenize.generate_tokens(reader().next):
          if ttype == tokenize.NAME and token in frame.f_locals:
            args[token] = frame.f_locals[token]
        if args:
          sys.stderr.write('Key variable values:\n')
          for var,val in args.items():
            sys.stderr.write('\t%s = %s\n' % (var, repr(val)))
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

def set_olex_paths():
  sys.path.append("%s" %basedir)
  sys.path.append("%s/etc/scripts" %basedir)
  sys.path.append("%s/util/pyUtil" %basedir)
  sys.path.append("%s/util/pyUtil/misc" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib/FileReaders" %basedir)
  sys.path.append("%s/util/pyUtil/CctbxLib" %basedir)
  sys.path.append("%s/util/pyUtil/HAR" %basedir)
  sys.path.append("%s/util/pyUtil/PluginLib" %(basedir))
  olx.VFSDependent = set()

def set_plugins_paths():

  plugins = olexex.InstalledPlugins()
  olx.InstalledPlugins = set()
  import AC4
  if not OV.HasGUI() and not os.environ.get("LOAD_HEADLESS_PLUGINS"):
    return

  from PluginTools import PluginTools
  import FragmentDB
  for plugin in plugins:
    sys.path.append("%s/util/pyUtil/PluginLib/plugin-%s" %(basedir,plugin))
  for plugin in plugins:
    if timer:
      t = time.time()
    try:
      exec("import " + plugin)
    except Exception as err:
      if debug:
        sys.stdout.formatExceptionInfo()
      else:
        print("Failed to load plugin '%s': %s" %(plugin, err))

    ##Dependencies
    if plugin == "plugin-SQLAlchemy":
      sys.path.append("%s/util/pyUtil/PythonLib/sqlalchemy" %basedir)

    if timer:
      tt.append("\t%.3f s --> %s" %((time.time() - t), plugin))

def setup_cctbx():
  import path_utils
  path_utils.setup_cctbx()

  # Import these files now to reduce time taken on running cctbx for the first time
  import my_refine_util
  import cctbx_olex_adapter
  import cctbx_controller
  import olex_twinning

''' Redirect prints to Olex '''
sys.stdout = StreamRedirection(sys.stdout, stdout_redirection)
sys.stderr = StreamRedirection(sys.stderr, stderr_redirection)
t = time.time()
try:
  import olx
except Exception as e:
  try:
    x = os.getcwdu()
  except AttributeError:
    x = os.getcwd()
  os.chdir(datadir)
  import olx
  os.chdir(x)

if timer:
  tt.append("%.3f s == import olx" %(time.time() - t))
  t = time.time()

basedir = olx.BaseDir()
datadir = olx.DataDir()

set_olex_paths()
if timer:
  tt.append("%.3f s == set_olex_paths()" %(time.time() - t))
  t = time.time()

olx.Clear()

import urllib2
# this overwrites the urllib2 default HTTP and HTTPS handlers
import multipart

t = time.time()
try:
  setup_cctbx()
except Exception as err:
  print("There is a problem with the cctbx")
  print(err)
if timer:
  tt.append("%.3f s == setup_cctbx()" %(time.time() - t))
  t = time.time()

import variableFunctions
if timer:
  tt.append("%.3f s == variableFunctions" %(time.time() - t))
  t = time.time()
variableFunctions.LoadParams()
if timer:
  tt.append("%.3f s == variableFunctions.LoadParams" %(time.time() - t))
  t = time.time()

import olexex
if timer:
  tt.append("%.3f s == olexex" %(time.time() - t))
  t = time.time()

import CifInfo # import needed to register functions to olex
if timer:
  tt.append("%.3f s == CifInfo" %(time.time() - t))
  t = time.time()

from olexFunctions import OlexFunctions
OV = OlexFunctions()

if timer:
  tt.append("%.3f s == olxFunctions" %(time.time() - t))
  t = time.time()

from gui.tools import *
from gui.skin import *
if OV.HasGUI():
  import htmlMaker
  from gui.home import *
  from gui.report import *
  from gui.cif import *
  from gui.metadata import *
  from gui.maps import *
  from gui.images import *
  from gui.db import *
  from gui.help import *
  #import Tutorials
  #load_user_gui_phil()
  #export_parameters()
  from Analysis import Analysis
#from gui.skin import *

if timer:
  tt.append("%.3f s == GUI Imports" %(time.time() - t))
  t = time.time()

def onstartup():
  OV.SetVar('cbtn_solve_on','false')
  OV.SetVar('cbtn_refine_on','false')
  OV.SetVar('cbtn_report_on','false')

  import leverage
  import userDictionaries
  if not userDictionaries.people:
    userDictionaries.init_userDictionaries()
  if not userDictionaries.localList:
    userDictionaries.LocalList()
  import gui
  if timer:
    t = time.time()
  gui.copy_datadir_items()
  if timer:
    tt.append("\t%.3f s --> %s" %((time.time() - t), 'gui.copy_datadir_items'))
  sys.path.append("%s/scripts" %OV.GetParam('user.customisation_dir'))

onstartup()

if timer:
  tt.append("%.3f s == onstartup()" %(time.time() - t))
  t = time.time()
  tt.append("IMPORTING PLUGINS...")
set_plugins_paths()
if timer:
  tt.append("%.3f s == set_plugins_paths()" %(time.time() - t))
  t = time.time()

import Loader

if timer:
  tt.append("%.3f s == Loader" %(time.time() - t))
  t = time.time()

if olx.IsPluginInstalled('MySQL') == "true":
  try:
    import OlexToMySQL
    from OlexToMySQL import DownloadOlexLanguageDictionary
    a = DownloadOlexLanguageDictionary()
    #olex.registerFunction(a.downloadTranslation)
  except Exception as ex:
    print("MySQL Plugin is installed but a connection to the default server could not be established")
    print(ex)
if timer:
  tt.append("%.3f s == MySQL()" %(time.time() - t))
  t = time.time()

if OV.HasGUI():
  olexex.check_for_recent_update()

if sys.platform[:3] == 'win':
  OV.SetVar('defeditor','notepad')
  OV.SetVar('defexplorer','shell')
#else:
  #olx.SetVar('defeditor','gedit')
  #olx.SetVar('defexplorer','nautilus')

t = time.time()
try:
  import customScripts
except ImportError as err:
  print("Could not import customScripts: %s" %err)

try:
  import userScripts
except ImportError as err:
  print("Could not import userScripts: %s" %err)
if timer:
  tt.append("%.3f s == Custom and User Scripts" %(time.time() - t))
  t = time.time()

def pip(package):
  import sys
  sys.stdout.isatty = lambda: False
  sys.stdout.encoding = sys.getdefaultencoding()
  import pip
  try:
    from pip import main as pipmain
  except:
    from pip._internal import main as pipmain
  pipmain(['install', '--user', package])
#  pip.main(['install', package])
OV.registerFunction(pip,False)

if timer:
  tt.append("InitPy took %s s" %(time.time() - beginning_of_t))
  tt.append("==================================================")
  for item in tt:
    print(item)
print("Welcome to Olex2")
print("\nWe are grateful to our users for testing and supporting Olex2")
print("Please find the link to credits in the About box")
print("\nDolomanov, O.V.; Bourhis, L.J.; Gildea, R.J.; Howard, J.A.K.; Puschmann, H.," +\
      "\nOLEX2: A complete structure solution, refinement and analysis program (2009)."+\
      "\nJ. Appl. Cryst., 42, 339-341.\n")
## These imports will register macros and functions for spy.
from RunPrg import RunPrg

if OV.HasGUI() and not os.environ.get("LOAD_HEADLESS_PLUGINS"):
  from HAR import HARp