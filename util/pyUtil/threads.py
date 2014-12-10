import os
import olex
import olx
from threading import Thread

# All threads are implemented as singletons - only once instance should be
# running at any given time. So the implementation must contain a static 'instance;
# variable

class ThreadRegistry:
  threads = set()
#must be called before destroying host application  
  def __init__(self):
    pass

  def register(self, klass):
    ThreadRegistry.threads.add(klass)

  def joinAll(self):
    for th in ThreadRegistry.threads:
      try:
        if th.instance: th.instance.join(1)
        if th.instance and th.instance.is_alive():
          th.instance.force_exit()
      except Exception, e:
        print e
        pass


# implement force_exit to premature thread termination
class ThreadEx(Thread):
  def force_exit(self):
    import ctypes
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident,
       ctypes.py_object(SystemExit))
    if res == 0:
      raise ValueError("invalid thread id")
    elif res != 1:
      ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
      raise SystemError("PyThreadState_SetAsyncExc failed")

class ShellExec:
  def run(self, arg):
    olx.Shell(arg)

shellExec = None
if not shellExec:
  shellExec = ShellExec()
  olex.registerFunction(shellExec.run, False, "threading.shell")
  threads = ThreadRegistry()
  olex.registerFunction(threads.joinAll, False, "threading")
