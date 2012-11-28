# initpy.py
import olex
import sys

datadir = olex.f("DataDir()")
basedir = olex.f("BaseDir()")
if sys.platform[:3] == 'win':
  sys.path = [''] # first should be empty string to avoid problem if cctbx needs cold start
  python_dir = r"%s\Python27" %basedir
  sys.path.append(python_dir)
  sys.path.append(r"%s\DLLs" %python_dir)
  sys.path.append(r"%s\Lib" %python_dir)
  sys.path.append(r"%s\Lib\site-packages" %python_dir)
  sys.path.append(r"%s\Lib\site-packages\PIL" %python_dir)
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
import time

debug = True
if debug == True:
  try:
    import wingdbstub
  except:
    pass

locale.setlocale(locale.LC_ALL, 'C')


if os.environ.get('OLEX_DBG_NO_STDERR_REDIRECTION') is not None:
  stderr_redirection = False
else:
  stderr_redirection = True
''' Debug, if possible '''


sys.on_sys_exit_raise = None
def our_sys_exit(i):
  if sys.on_sys_exit_raise:
    e = sys.on_sys_exit_raise
    sys.on_sys_exit_raise = None
    raise e
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

  def formatExceptionInfo(maxTBlevel=5):
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
      lineno = frame.f_lineno
      def reader():
        try:
          yield inspect.getsource(frame)
        except:
          print ">>>>> ERROR (formatExceptionInfo)"
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
  sys.path.append("%s/etc/scripts" %basedir)
  sys.path.append("%s/util/pyUtil" %basedir)
  sys.path.append("%s/util/pyUtil/misc" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib/FileReaders" %basedir)
  sys.path.append("%s/util/pyUtil/CctbxLib" %basedir)

def set_plugins_paths():
  plugins = olexex.InstalledPlugins()
  sys.path.append("%s/util/pyUtil/PluginLib" %(basedir))
  for plugin in plugins:
    sys.path.append("%s/util/pyUtil/PluginLib/plugin-%s" %(basedir,plugin))
  for plugin in plugins:
    try:
      exec("import " + plugin)
    except Exception, err:
      print err

    ##Dependencies
    if plugin == "plugin-SQLAlchemy":
      sys.path.append("%s/util/pyUtil/PythonLib/sqlalchemy" %basedir)

def setup_cctbx():
  import path_utils
  path_utils.setup_cctbx()

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

olx.Clear()

try:
  setup_cctbx()
except Exception, err:
  print "There is a problem with the cctbx"
  print err

import variableFunctions
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
  from gui.home import *
  from gui.report import *
  from gui.cif import *
  from gui.tools import *
  from gui.metadata import *
  from gui.maps import *

def onstartup():
  OV.SetVar('cbtn_solve_on','false')
  OV.SetVar('cbtn_refine_on','false')
  OV.SetVar('cbtn_report_on','false')

  ## copy sample directory to datadir
  import shutil
  svn_samples_directory = '%s/sample_data' %OV.BaseDir()
  user_samples_directory = '%s/samples' %OV.DataDir()
  if os.path.exists(user_samples_directory):
    OV.SetVar('sample_dir',user_samples_directory)
  else:
    os.mkdir(user_samples_directory)

  if sys.version_info[0] >= 2 and sys.version_info[1] >=6:
    ignore_patterns = shutil.ignore_patterns('*.svn')
  else:
    ignore_patterns = None # back compatiblity for python < 2.6

  samples = os.listdir(svn_samples_directory)
  for sample in samples:
    if sample == '.svn': continue
    if not os.path.exists('%s/%s' %(user_samples_directory,sample)):
      try:
        dirname1 = '%s/%s' %(svn_samples_directory,sample)
        dirname2 = '%s/%s' %(user_samples_directory,sample)
        if ignore_patterns is not None:
          shutil.copytree(dirname1, dirname2, ignore=ignore_patterns)
        else:
          shutil.copytree(dirname1, dirname2)
        OV.SetVar('sample_dir','%s/samples' %OV.DataDir())
      except:
        pass
    else:
      continue

  ## initialise userDictionaries objects
  import userDictionaries
  if not userDictionaries.people:
    userDictionaries.People()
  if not userDictionaries.localList:
    userDictionaries.LocalList()

onstartup()

#if debug:
#       keys = os.environ.keys()
#       keys.sort()
#       for k in keys:
#               print "%s\t%s" %(k, os.environ[k])
#
#       for bit in sys.path:
#               print bit

import urllib2
# this overwrites the urllib2 default HTTP and HTTPS handlers
import multipart


if olx.IsPluginInstalled('MySQL') == "true":
  try:
    import OlexToMySQL
    from OlexToMySQL import DownloadOlexLanguageDictionary
    a = DownloadOlexLanguageDictionary()
    #olex.registerFunction(a.downloadTranslation)
  except Exception, ex:
    print "MySQL Plugin is installed but a connection to the default server could not be established"
    print ex


if OV.HasGUI():
  olexex.check_for_recent_update()

if sys.platform[:3] == 'win':
  OV.SetVar('defeditor','notepad')
  OV.SetVar('defexplorer','shell')
#else:
  #olx.SetVar('defeditor','gedit')
  #olx.SetVar('defexplorer','nautilus')


try:
  import customScripts
except ImportError, err:
  print "Could not import customScripts: %s" %err

try:
  import userScripts
except ImportError, err:
  print "Could not import userScripts: %s" %err



print "Welcome to Olex2"
print "\nWe are grateful to our users for testing and supporting Olex2"
print "Please find the link to credits in the About box"
print "\nDolomanov, O.V.; Bourhis, L.J.; Gildea, R.J.; Howard, J.A.K.; Puschmann, H.," +\
      "\nOLEX2: A complete structure solution, refinement and analysis program (2009)."+\
      "\nJ. Appl. Cryst., 42, 339-341.\n"
## These imports will register macros and functions for spy.
if OV.HasGUI():
  from Skin import Skin
  from Analysis import Analysis
from RunPrg import RunPrg

