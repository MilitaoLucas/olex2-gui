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

  stopwatch.start("import variableFunctions")
  import variableFunctions
  stopwatch.run(variableFunctions.LoadParams)

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

  stopwatch.start("import Loader")
  import Loader

  # timed inside
  initpy.setup_MySQL()

  if OV.HasGUI():
    olexex.check_for_recent_update()

  if sys.platform[:3] == 'win':
    OV.SetVar('defeditor','notepad')
    OV.SetVar('defexplorer','shell')
  #else:
    #olx.SetVar('defeditor','gedit')
    #olx.SetVar('defexplorer','nautilus')

  stopwatch.run(initpy.import_caustom_and_user_sripts)
  ## These imports will register macros and functions for spy.
  stopwatch.exec("from RunPrg import RunPrg")

  stopwatch.start("NSF")
  try:
    from NoSpherA2 import NoSpherA2
  except Exception as e:
    olx.Echo(e, m="error")
  stopwatch.stop()

  if OV.IsDebugging():
    olx.stopwatch.log()
  else:
    olx.stopwatch.actvive = False
    olx.stopwatch.reset()

  print("Welcome to Olex2")
  print("\nWe are grateful to our users for testing and supporting Olex2")
  print("Please find the link to credits in the About box")
  print("\nDolomanov, O.V.; Bourhis, L.J.; Gildea, R.J.; Howard, J.A.K.; Puschmann, H.," +\
        "\nOLEX2: A complete structure solution, refinement and analysis program (2009)."+\
        "\nJ. Appl. Cryst., 42, 339-341.\n")

########################### THE INITIALISATIOn ENTRY POINT ####################
do_init()
