import sys, os

def debugInVSC():
  import olx
  cd = os.getcwd()
  try:
    os.chdir(os.path.join(olx.BaseDir(), "util", "pyUtil"))
    import ptvsd
    sys.argv = [olx.app.GetArg(0)]
    # 5678 is the default attach port in the VS Code debug configurations
    print("Waiting for debugger attach")
    ptvsd.enable_attach(address=('localhost', 5678), redirect_output=False)
    ptvsd.wait_for_attach()
    breakpoint()
  except Exception as x:
    print(x)
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
