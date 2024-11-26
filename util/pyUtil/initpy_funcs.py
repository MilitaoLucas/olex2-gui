import os, sys

class initpy_funcs():
  def __init__(self, basedir, datadir):
    import olx
    self.OV = None # must be initialised
    self.olx = olx
    self.basedir = basedir
    self.datadir = datadir

  def set_python_paths(self):
    if sys.platform[:3] == 'win':
      sys.path = [''] # first should be empty string to avoid problem if cctbx needs cold start
      _ = os.environ.get("PYTHONHOME")
      if _:
        python_dir = _
      else:
        python_dir = r"%s\Python38" %self.basedir
      sys.path.append(python_dir)
      sys.path.append(r"%s\DLLs" %python_dir)
      sys.path.append(r"%s\Lib" %python_dir)
      sys.path.append(r"%s\Lib\site-packages" %python_dir)
      sys.path.append(r"%s\Lib\site-packages\PIL" %python_dir)
      sys.path.append(r"%s\Lib\site-packages\win32" %python_dir)
      sys.path.append(r"%s\Lib\site-packages\win32\lib" %python_dir)
      os.add_dll_directory(self.basedir)
    else:
      #it looks like we do not want to set the sys PATH on Linux or Mac!
      set_sys_path = True
      try:
        set_sys_path = os.path.exists(self.basedir + '/lib/python3.8_')
      except:
        pass
      if set_sys_path:
        sys.prefix = self.basedir + '/lib/python3.8'
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
    sys.path.append(os.path.join(self.datadir, "site-packages"))

  def onexit(self):
    sps = self.OV.GetVar("launched_server.ports", "")
    host = self.OV.GetParam("user.Server.host")
    share = self.OV.GetParam("user.Server.shared_localhost")
    if not share and host == "localhost" and sps:
      print("Shutting down the server(s)")
      import socket
      for sp in sps.split(','):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
          try:
            s.connect((host, int(sp)))
            s.sendall(b"stop\n")
          except:
            pass

  def attach_debugger(self):
    debug = 'OLEX2_ATTACHED_WITH_PYDEBUGGER' in os.environ
    if debug == True:
      print("Trying to connect to WING.")
      try:
        import wingdbstub
      except Exception as err:
        print("Wing has failed: %s" %err)
        pass
    elif 'OLEX2_DEBUG_IN_VSC' in os.environ:
      import indep
      indep.debugInVSC()

  def our_sys_exit(i):
    '''
    some scripts call exit - and Olex2 does exit if not for this function
    '''
    if sys.on_sys_exit_raise:
      e = sys.on_sys_exit_raise
      sys.on_sys_exit_raise = None
      raise e
    print("Terminate with %i" %i)

  def get_prg_roots(self):
    prg_roots = {}
    path = r"%s/util/pyUtil/prg_root.txt" %self.basedir
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

  def set_olex_paths(self):
    sys.path.append("%s" %self.basedir)
    sys.path.append(os.path.join(self.basedir, "etc", "scripts"))
    up = os.path.join(self.basedir, "util", "pyUtil")
    sys.path.append(up)
    sys.path.append(os.path.join(up, "misc"))
    sys.path.append(os.path.join(up, "PyToolLib"))
    sys.path.append(os.path.join(up, "PyToolLib", "FileReaders"))
    sys.path.append(os.path.join(up, "CctbxLib"))
    sys.path.append(os.path.join(up, "HAR"))
    sys.path.append(os.path.join(up, "NoSpherA2"))
    sys.path.append(os.path.join(up, "PluginLib"))
    self.olx.VFSDependent = set()

  def set_plugins_paths(self):
    import olexex
    plugins = olexex.InstalledPlugins()
    self.olx.InstalledPlugins = set()

    self.olx.stopwatch.start("import AC7", False)
    import AC7
    self.olx.stopwatch.stop()

    if not self.OV.HasGUI() and not os.environ.get("LOAD_HEADLESS_PLUGINS"):
      return

    self.olx.stopwatch.exec("import PluginTools")
    self.olx.stopwatch.exec("import FragmentDB")
    for plugin in plugins:
      sys.path.append("%s/util/pyUtil/PluginLib/plugin-%s" %(self.basedir,plugin))
    for plugin in plugins:
      try:
        self.olx.stopwatch.exec("import " + plugin)
      except Exception as err:
        if self.OV.IsDebugging():
          sys.stdout.formatExceptionInfo()
        else:
          print("Failed to load plugin '%s': %s" %(plugin, err))
      ##Dependencies
      if plugin == "plugin-SQLAlchemy":
        sys.path.append("%s/util/pyUtil/PythonLib/sqlalchemy" %self.basedir)

  def setup_cctbx(self):
    import path_utils
    path_utils.setup_cctbx()

    # Import these files now to reduce time taken on running cctbx for the first time
    import my_refine_util
    import cctbx_olex_adapter
    import cctbx_controller
    import olex_twinning

  def onstartup(self):
    self.OV.SetVar('cbtn_solve_on','false')
    self.OV.SetVar('cbtn_refine_on','false')
    self.OV.SetVar('cbtn_report_on','false')

    import leverage
    import userDictionaries
    if not userDictionaries.people:
      self.olx.stopwatch.run(userDictionaries.init_userDictionaries)
    if not userDictionaries.localList:
      self.olx.stopwatch.run(userDictionaries.LocalList)
    import gui
    self.olx.stopwatch.run(gui.copy_datadir_items)
    sys.path.append(os.path.join(self.OV.GetParam('user.customisation_dir'), "scripts"))

  def setup_MySQL(self):
    if self.olx.IsPluginInstalled('MySQL') == "true":
      self.olx.stopwatch.start("MySQL")
      try:
        import OlexToMySQL
        from OlexToMySQL import DownloadOlexLanguageDictionary
        a = DownloadOlexLanguageDictionary()
        #olex.registerFunction(a.downloadTranslation)
      except Exception as ex:
        print("MySQL Plugin is installed but a connection to the default server could not be established")
        print(ex)
      finally:
        self.olx.stopwatch.stop()

  def set_redirectoin(self):
    from olxio import StreamRedirection
    ''' Redirect prints to Olex '''
    sys.stdout = StreamRedirection(sys.stdout, self.basedir, self.datadir, True)
    sys.stderr = StreamRedirection(sys.stderr, self.basedir, self.datadir,
      'OLEX_DBG_NO_STDERR_REDIRECTION' not in os.environ)

  def import_gui(self):
    self.olx.stopwatch.exec("from gui.tools import *")
    self.olx.stopwatch.exec("from gui.skin import *")
    if self.OV.HasGUI():
      self.olx.stopwatch.exec("import htmlMaker")
      self.olx.stopwatch.exec("from gui.home import *")
      self.olx.stopwatch.exec("from gui.report import *")
      self.olx.stopwatch.exec("from gui.cif import *")
      self.olx.stopwatch.exec("from gui.metadata import *")
      self.olx.stopwatch.exec("from gui.maps import *")
      self.olx.stopwatch.exec("from gui.images import *")
      self.olx.stopwatch.exec("from gui.db import *")
      self.olx.stopwatch.exec("from  gui.help import *")
      #import Tutorials
      #load_user_gui_phil()
      #export_parameters()
      self.olx.stopwatch.exec("import Analysis")

  def import_caustom_and_user_sripts(self):
    try:
      import customScripts
    except ImportError as err:
      print("Could not import customScripts: %s" %err)

    try:
      import userScripts
    except ImportError as err:
      print("Could not import userScripts: %s" %err)
