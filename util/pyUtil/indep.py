import sys, os

def debugInVSC():
  cd = os.getcwd()
  print("Attaching to MS Visual Studio Code debugger")
  try:
    import olex
    basedir = olex.f("BaseDir()")
    os.chdir(os.path.join(basedir, "util", "pyUtil"))
    sys.argv = [olex.f("app.GetArg(0)")]
    # 5678 is the default attach port in the VS Code debug configurations.
    # launch.json asks for "type": "debugpy" and the current VS Code Python
    # extension no longer talks to a ptvsd 4.x server, so prefer debugpy and
    # keep ptvsd only for an interpreter that has nothing else.
    try:
      import debugpy
      # Run the debug adapter inside this process rather than spawning one.
      #
      # By default listen() starts a separate adapter process which owns the
      # listening socket. Out of an embedded interpreter that adapter dies
      # immediately: listen() still returns, so nothing looks wrong, but the
      # port disappears, VS Code gets ECONNREFUSED on 5678, and Olex2 is left
      # blocked in wait_for_client() below - hung before its window ever
      # appears, with only "Waiting for debugger attach" in PythonError.log to
      # show for it.
      try:
        debugpy.listen(("localhost", 5678), in_process_debug_adapter=True)
      except TypeError:
        # older debugpy without the flag: fall back to the spawned adapter,
        # pointed at a real interpreter since sys.executable is olex2.exe
        python_exe = os.path.join(sys.prefix, "python.exe")
        if os.path.exists(python_exe):
          debugpy.configure(python=python_exe)
        debugpy.listen(("localhost", 5678))
      print("Waiting for debugger attach on port 5678 (debugpy)")
      debugpy.wait_for_client()
    except ImportError:
      import ptvsd
      print("Waiting for debugger attach on port 5678 (ptvsd)")
      ptvsd.enable_attach(address=('localhost', 5678), redirect_output=False)
      ptvsd.wait_for_attach()
  except Exception as x:
    print("VS Code attach unavailable, Olex2 continues without it: %s: %s"
          % (type(x).__name__, x))
    sys.stdout.formatExceptionInfo()
  finally:
    os.chdir(cd)

def setup_openblas():
  import olx
  vn = 'OPENBLAS_NUM_THREADS'
  if vn not in os.environ:
    tn_max = int(olx.app.OptValue("openblas.thread_n_max", 24))
    tn = int(olx.app.OptValue("openblas.thread_n", -1))
    if tn < 1:
      tn = int(min(os.cpu_count(), tn_max) * 2 /3)
    os.environ[vn] = str(tn)

def run_timed(func, *args, **kwds):
  import olx
  if olx.stopwatch:
    return olx.stopwatch.run(func, *args, **kwds)
  return func(*args, **kwds)