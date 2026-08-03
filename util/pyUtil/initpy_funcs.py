import os, sys

class initpy_funcs():
  def __init__(self, basedir, datadir):
    import olx
    self.OV = None # must be initialised
    self.olx = olx
    self.basedir = basedir
    self.datadir = datadir
    pv = sys.version_info
    self.py_version = "%s%s" %(pv.major, pv.minor)
    self.py_ds_version = "%s.%s" %(pv.major, pv.minor)

  def set_python_paths(self):
    if sys.platform[:3] == 'win':
      sys.path = [''] # first should be empty string to avoid problem if cctbx needs cold start
      _ = os.environ.get("PYTHONHOME")
      if _:
        python_dir = _
      else: # not sure this could ever happen as without PYTHONHOME exe cannot start
        python_dir = r"%s\Python%s" %(self.basedir, self.py_version)
      sys.path.append(python_dir)
      sys.path.append(r"%s\DLLs" %python_dir)
      sys.path.append(r"%s\Lib" %python_dir)
      sys.path.append(r"%s\Lib\site-packages" %python_dir)
      sys.path.append(r"%s\Lib\site-packages\PIL" %python_dir)
      os.add_dll_directory(self.basedir)
    else:
      #it looks like we do not want to set the sys PATH on Linux or Mac!
      set_sys_path = True
      try:
        set_sys_path = os.path.exists(self.basedir + '/lib/python3.9_')
      except:
        pass
      if set_sys_path:
        sys.prefix = self.basedir + '/lib/python%s' %self.py_ds_version
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
    if sys.version_info.major >= 3 and sys.version_info.minor > 8:
      py_version = "-%s%s" %(sys.version_info.major, sys.version_info.minor)
    else:
      py_version = ""
    sys.path.append(os.path.join(self.datadir, "site-packages%s" %py_version))

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
    def _append_unique(path):
      if path not in sys.path:
        sys.path.append(path)

    _append_unique("%s" %self.basedir)
    _append_unique(os.path.join(self.basedir, "etc", "scripts"))
    up = os.path.join(self.basedir, "util", "pyUtil")
    _append_unique(up)
    _append_unique(os.path.join(up, "misc"))
    _append_unique(os.path.join(up, "PyToolLib"))
    _append_unique(os.path.join(up, "PyToolLib", "FileReaders"))
    _append_unique(os.path.join(up, "CctbxLib"))
    _append_unique(os.path.join(up, "HAR"))
    _append_unique(os.path.join(up, "NoSpherA2"))
    _append_unique(os.path.join(up, "NoMoRe"))
    _append_unique(os.path.join(up, "DispRadial"))
    _append_unique(os.path.join(up, "PluginLib"))
    self.olx.VFSDependent = set()

  def set_plugins_paths(self):
    import olex_core
    plugins = olex_core.GetPluginList() or []
    plugins = list(dict.fromkeys(plugins))
    self.olx.InstalledPlugins = set()

    def _append_unique(path):
      if path not in sys.path:
        sys.path.append(path)

    def _timed_import(module_name):
      self.olx.stopwatch.start("import " + module_name, False)
      __import__(module_name)
      self.olx.stopwatch.stop()

    if not self.OV.HasGUI() and not os.environ.get("LOAD_HEADLESS_PLUGINS"):
      return

    for plugin in plugins:
      _append_unique("%s/util/pyUtil/PluginLib/plugin-%s" %(self.basedir,plugin))

    self._startup_plugins = plugins
    if os.environ.get("OLEX2_DEFER_PLUGIN_IMPORTS"):
      import olex
      olex.registerFunction(self.import_startup_plugins_deferred, False, "initpy")
      self.olx.Schedule(1, "spy.initpy.import_startup_plugins_deferred()", g=True)
      return

    self.import_startup_plugins_deferred()

  def import_startup_plugins_deferred(self):
    if getattr(self, "_startup_plugins_loaded", False):
      return
    self._startup_plugins_loaded = True

    plugins = getattr(self, "_startup_plugins", [])

    def _append_unique(path):
      if path not in sys.path:
        sys.path.append(path)

    def _timed_import(module_name):
      self.olx.stopwatch.start("import " + module_name, False)
      __import__(module_name)
      self.olx.stopwatch.stop()

    if os.environ.get("OLEX2_DEFER_AC7_IMPORTS"):
      import olex
      olex.registerFunction(self.import_ac7_deferred, False, "initpy")
      self.olx.Schedule(1, "spy.initpy.import_ac7_deferred()", g=True)
    else:
      self.import_ac7_deferred()

    _timed_import("PluginTools")
    if os.environ.get("OLEX2_LAZY_FRAGMENTDB"):
      # Hybrid lazy mode: keep GUI/tool registration intact, but rely on
      # FragmentDB's own runtime guards to defer heavy DB setup until first use.
      if os.environ.get("OLEX2_LAZY_FRAGMENTDB_KEEP_GUI", "True").lower() in ("1", "true", "yes"):
        _timed_import("FragmentDB")
      else:
        self._register_lazy_fragmentdb_proxies()
    else:
      _timed_import("FragmentDB")

    for plugin in plugins:
      if plugin in sys.modules:
        continue
      try:
        _timed_import(plugin)
      except Exception as err:
        if self.OV.IsDebugging():
          sys.stdout.formatExceptionInfo()
        else:
          print("Failed to load plugin '%s': %s" %(plugin, err))
      ##Dependencies
      if plugin == "plugin-SQLAlchemy":
        _append_unique("%s/util/pyUtil/PythonLib/sqlalchemy" %self.basedir)

  def import_ac7_deferred(self):
    if getattr(self, "_ac7_loaded", False):
      return
    self._ac7_loaded = True
    self.olx.stopwatch.start("import AC7", False)
    import AC7
    self.olx.stopwatch.stop()

  def _register_lazy_fragmentdb_proxies(self):
    if getattr(self, "_lazy_fragmentdb_registered", False):
      return
    self._lazy_fragmentdb_registered = True

    import olex

    def _call_fragmentdb(method_name, *args):
      try:
        import FragmentDB
        if method_name == "results":
          target_obj = getattr(FragmentDB, "ref", None)
        else:
          target_obj = getattr(FragmentDB, "fdb", None)
        if target_obj is None:
          print("FragmentDB lazy load failed: plugin instance is unavailable")
          return None
        target = getattr(target_obj, method_name, None)
        if target is None:
          print("FragmentDB lazy load failed: method '%s' is unavailable" % method_name)
          return None
        return target(*args)
      except Exception as e:
        print("FragmentDB lazy load failed: %s" % str(e))
        return None

    methods = [
      "det_refmodel", "set_id", "imagedisp", "prepare_selected_atoms", "exportfrag",
      "init_plugin", "get_fvar_occ", "search_fragments", "show_reference", "make_selctions_picture",
      "set_frag_atoms", "open_edit_fragment_window", "list_all_fragments", "get_fragments", "fit_db_fragment",
      "get_resi_class", "find_free_residue_num", "get_frag_for_gui", "set_occu", "set_resiclass",
      "store_new_fragment", "set_fragment_picture", "get_chemdrawstyle", "add_new_frag", "update_fragment",
      "delete_fragment", "display_large_image", "save_picture", "store_picture", "display_image",
      "revert_last", "make_history", "clear_mainvalues"
    ]
    def _register_proxy(method_name):
      def _proxy(*args):
        return _call_fragmentdb(method_name, *args)
      _proxy.__name__ = method_name
      olex.registerFunction(_proxy, False, "FragmentDB")
      olex.registerFunction(_proxy, False, "fragmentdb")

    for method_name in methods:
      _register_proxy(method_name)

    _register_proxy("results")

  def setup_cctbx(self):
    import path_utils
    path_utils.setup_cctbx()

    if os.environ.get("OLEX2_SKIP_CCTBX_WARM_IMPORTS"):
      return

    # Import these files now to reduce time taken on running cctbx for the first time
    import my_refine_util
    import cctbx_olex_adapter
    import cctbx_controller
    import olex_twinning

  def NoSpherA2(self):
    try:
      self.olx.stopwatch.exec("from NoSpherA2 import NoSpherA2")
    except Exception as e:
      self.olx.Echo(e, m="error")
      print("Failed to load NoSpherA2. Please check your installation.")
      return

  def NoMoRe(self):
    try:
      self.olx.stopwatch.exec("import nomore")
    except Exception as e:
      self.olx.Echo(e, m="error")
      print("Failed to load NoMoRe. Please check your installation.")
      return

  def DispRadial(self):
    try:
      self.olx.stopwatch.exec("import disp_radial")
    except Exception as e:
      self.olx.Echo(e, m="error")
      print("Failed to load DispRadial. Please check your installation.")
      return

  def onstartup(self):
    self.OV.SetVar('cbtn_solve_on','false')
    self.OV.SetVar('cbtn_refine_on','false')
    self.OV.SetVar('cbtn_report_on','false')

    # define global var names here
    self.olx.var_name_par_files = "par_files"
    self.olx.var_name_param_N = "param_N"

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
      if os.environ.get("OLEX2_DEFER_HEAVY_GUI_IMPORTS"):
        self._register_heavy_gui_proxies()
        import olex
        olex.registerFunction(self.import_gui_heavy_deferred, False, "initpy")
        self.olx.Schedule(1, "spy.initpy.import_gui_heavy_deferred()", g=True)
      else:
        self.olx.stopwatch.exec("from  gui.help import *")
        self.olx.stopwatch.exec("import Analysis")
      #import Tutorials
      #load_user_gui_phil()
      #export_parameters()
      if self.OV.IsDeveloping():
        self.olx.stopwatch.exec("from gui import dimas")

  def _register_heavy_gui_proxies(self):
    if getattr(self, "_heavy_gui_proxies_registered", False):
      return
    self._heavy_gui_proxies_registered = True

    def _make_hos_proxy(*args):
      import Analysis
      return Analysis.HOS_instance.make_HOS(*args)

    _make_hos_proxy.__name__ = "make_HOS"
    self.OV.registerFunction(_make_hos_proxy)

  def import_gui_heavy_deferred(self):
    if getattr(self, "_gui_heavy_imports_loaded", False):
      return
    self._gui_heavy_imports_loaded = True
    self.olx.stopwatch.exec("from  gui.help import *")
    self.olx.stopwatch.exec("import Analysis")

  def import_custom_and_user_sripts(self):
    try:
      import customScripts
    except ImportError as err:
      print("Could not import customScripts: %s" %err)

    try:
      import userScripts
    except ImportError as err:
      print("Could not import userScripts: %s" %err)

  def check_exec_flag(self):
    if sys.platform[:3] == 'win':
      return
    import stat
    # leave olex2c as the last one!
    to_check = ["pyl", "NoSpherA2", "hart", "hart_mpi",
                "etc/bin/restart.sh",
                "etc/bin/restart-mac.sh",
                "olex2c"]
    if sys.platform == 'darwin':
      to_check[-1] = to_check[-1] + "_exe"
    for f in to_check:
      f = os.path.join(self.basedir, f)
      if not os.path.exists(f):
        continue
      try:
        if not (os.stat(f)[stat.ST_MODE] & stat.S_IXUSR):
          os.chmod(f, stat.S_IXUSR | stat.S_IREAD)
      except:
        self.olx.Echo(
          "Failed make required files (%s) executable - please fix manually." %(", ".join(to_check)),
          m="error")
        return
  def get_phil_extensions(self):
    dev_path = os.path.join(self.basedir, "util", "pyUtil", "ACED7d")
    if os.path.exists(dev_path):
      return [os.path.join(dev_path, "aced.phil")]
    return [os.path.join(self.basedir, "util", "pyUtil", "ACED", "aced.phil")]

  def final_checks(self):
    if sys.platform.startswith('linux'):
      import pathlib
      old_dd = os.path.join(pathlib.Path.home(), ".olex2")
      if os.path.exists(old_dd):
        self.olx.Echo(
          "Olex2 settings have been migrated from '~/.olex2' to '%s'" %os.path.split(self.datadir)[0],
          m="warning")
      lib_path = 'LD_LIBRARY_PATH'
      paths = self.olx.GetEnv(lib_path)
      internal_lib_path = os.path.join(self.basedir, "ilib")
      if internal_lib_path not in paths:
        self.olx.Echo(
          f"'{internal_lib_path}' Folder must be on {lib_path}. Please update your 'start' script",
          m="warning")
