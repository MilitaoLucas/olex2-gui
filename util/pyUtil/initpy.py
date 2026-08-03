# initpy.py
import os, sys, time
import olex

def do_init():
  datadir = olex.f("DataDir()")
  basedir = olex.f("BaseDir()")
  sys.path.append(os.path.join(basedir, "util", "pyUtil"))
  sys.path.append(datadir)
  import initpy_funcs, olxtm
  stopwatch = olxtm.olxtm()

  stopwatch.start("Initial imports")
  stopwatch.start("import olx")
  try:
    x = os.getcwd()
    os.chdir(datadir)
    import olx
    olx.stopwatch = stopwatch
  except Exception as e:
    print("Failed to import olx: %s" %str(e))
  finally:
    os.chdir(x)
  stopwatch.stop()

  initpy = initpy_funcs.initpy_funcs(basedir=basedir, datadir=datadir)
  fast_startup = os.environ.get("OLEX2_FAST_STARTUP", "").lower() in ("1", "true", "yes")

  olex.registerFunction(initpy.onexit, False)
  sys.on_sys_exit_raise = None
  sys.exit = initpy.our_sys_exit

  initpy.set_python_paths()
  initpy.set_redirectoin()
  initpy.attach_debugger()
  #make pyl, hart, NSF executable on non-Windows platforms
  initpy.check_exec_flag()

  # we need to use the user's locale for proper functioning of functions working
  # with multi-byte strings
  #locale.setlocale(locale.LC_ALL, 'C')

  # sets max number of threads...
  import indep
  indep.setup_openblas()

  #!! transient structure parameters, cleared on loading a structure
  olx.structure_params = {}

  stopwatch.run(initpy.set_olex_paths)

  if olx.app.IsBaseDirWritable() == "true":
    import path_utils
    stopwatch.run(path_utils.Cleanup)

  olx.Clear()

  import urllib.request, urllib.error, urllib.parse
  # this overwrites the urllib2 default HTTP and HTTPS handlers
  import multipart

  try:
    stopwatch.run(initpy.setup_cctbx)
  except Exception as err:
    print("There is a problem with the cctbx: %s" %str(err))

###############################################################################
  stopwatch.start("import variableFunctions")
  import variableFunctions
  stopwatch.run(variableFunctions.LoadParams,
                extensions=initpy.get_phil_extensions())
###############################################################################

  defer_olexex = os.environ.get("OLEX2_DEFER_OLEXEX_IMPORTS")
  if defer_olexex:
    olexex_loaded = [False]
    def import_olexex_deferred():
      try:
        if olexex_loaded[0]:
          return
        olexex_loaded[0] = True
        stopwatch.start("import olexex")
        import olexex
      except Exception as e:
        print("Deferred olexex import failed: %s" %str(e))

    olex.registerFunction(import_olexex_deferred, False, "initpy")
    olx.Schedule(1, "spy.initpy.import_olexex_deferred()", g=True)
  else:
    stopwatch.start("import olexex")
    import olexex

  stopwatch.start("import CifInfo")
  import CifInfo # import needed to register functions to olex

  stopwatch.start("from olexFunctions import OV")
  from olexFunctions import OV
  initpy.OV = OV
  # stop collecting if no interest!
  stopwatch.active = OV.IsDebugging()

  stopwatch.run(initpy.import_gui)
  stopwatch.run(initpy.onstartup)
  stopwatch.run(initpy.set_plugins_paths)

  if os.environ.get("OLEX2_DEFER_LOADER_IMPORTS"):
    def import_loader_deferred():
      try:
        import Loader
      except Exception as e:
        print("Deferred Loader import failed: %s" %str(e))

    olex.registerFunction(import_loader_deferred, False, "initpy")
    olx.Schedule(1, "spy.initpy.import_loader_deferred()", g=True)
  else:
    stopwatch.start("import Loader")
    import Loader

  # timed inside
  initpy.setup_MySQL()

  if OV.HasGUI():
    if defer_olexex:
      olx.Schedule(2, "spy.initpy.import_olexex_deferred()", g=True)
      olx.Schedule(3, "spy.check_for_recent_update()", g=True)
    else:
      olexex.check_for_recent_update()

  if sys.platform[:3] == 'win':
    OV.SetVar('defeditor','notepad')
    OV.SetVar('defexplorer','shell')
  #else:
    #olx.SetVar('defeditor','gedit')
    #olx.SetVar('defexplorer','nautilus')

  stopwatch.run(initpy.import_custom_and_user_sripts)
  ## These imports will register macros and functions for spy.
  stopwatch.exec("from RunPrg import RunPrg")

  if fast_startup:
    def _call_nsa2(name, *args):
      # Preserve NoSpherA2 GUI calls in fast mode by lazy-loading on first use.
      try:
        import importlib
        nsa2_mod = importlib.import_module("NoSpherA2.NoSpherA2")
        target = getattr(nsa2_mod, name, None)
        if target is None:
          nsa2_pkg = importlib.import_module("NoSpherA2")
          getter = getattr(nsa2_pkg, "get_NoSpherA2_instance", None)
          if getter is not None:
            target = getattr(getter(), name, None)
        if target is None:
          print("NoSpherA2 lazy load failed: method '%s' is unavailable" % name)
          return "Please Select;" if name == "get_sources_string" else None
        return target(*args)
      except Exception as e:
        print("NoSpherA2 lazy load failed: %s" % str(e))
        return "Please Select;" if name == "get_sources_string" else None

    def _register_nsa2_proxy(name):
      def _proxy(*args):
        return _call_nsa2(name, *args)
      _proxy.__name__ = name
      OV.registerFunction(_proxy, False, "NoSpherA2")

    for nsa2_function in (
      "get_sources_string",
      "toggle_GUI",
      "make_NSA2_GUI",
      "hybrid_GUI",
      "get_functional_list",
      "change_tsc_generator",
      "change_basisset",
      "set_default_cpu_and_mem",
      "available",
      "launch",
      "getBasisListStr",
      "getCPUListStr",
      "getwfn_softwares",
      "get_distro_list",
      "disable_relativistics",
    ):
      _register_nsa2_proxy(nsa2_function)

    print("Fast startup mode: skipping NoSpherA2/NoMoRe/DispRadial preload")
  else:
    stopwatch.run(initpy.NoSpherA2)
    stopwatch.run(initpy.NoMoRe)
    stopwatch.run(initpy.DispRadial)

  stopwatch.start("Peanut")
  try:
    from peanut import Peanut
  except Exception as e:
    olx.Echo(e, m="error")
  stopwatch.stop()

  if OV.IsDebugging():
    olx.stopwatch.log()
  else:
    olx.stopwatch.active = False
    olx.stopwatch.reset()

  print("Welcome to Olex2")
  print("\nWe are grateful to our users for testing and supporting Olex2")
  print("Please find the link to credits in the About box")
  print("\nDolomanov, O.V.; Bourhis, L.J.; Gildea, R.J.; Howard, J.A.K.; Puschmann, H.," +\
        "\nOLEX2: A complete structure solution, refinement and analysis program (2009)."+\
        "\nJ. Appl. Cryst., 42, 339-341.\n")

  initpy.final_checks()
########################### THE INITIALISATION ENTRY POINT ####################
do_init()
