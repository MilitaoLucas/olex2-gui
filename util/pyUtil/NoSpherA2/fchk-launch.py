import os
import sys
import time
import subprocess
import signal

fchk_dir = os.getenv("fchk_dir", "")
fchk_file = os.getenv("fchk_file", "")
if not os.path.exists(fchk_dir):
  print("Incorrect launching directory!")
  time.sleep(10)
  exit(-1)
os.chdir(fchk_dir)
args = os.getenv("fchk_cmd", "").split('+&-')
out_fn = os.path.split(os.getenv("fchk_out_fn", None))[1]

print("Running: '" + ' '.join(args) + "' into out file:" + out_fn)

try:
  log = None
  err_fn = None
  inp = None
  if any("elmo" in x for x in args):
    inp = open(args[2], 'r')
  log = open(out_fn, 'w')
  log.write("Command: " + ' '.join(args))

  with subprocess.Popen(args, stdout=log, stderr=log) as rp:
    # def handler(sig, frame):
    #  rp.kill()
    # with open("NoSpherA2.pidfile", "w") as pf:
    #  print(os.getpid())
    #  pf.write(str(os.getpid()) + '\n')
    #  pf.flush()
    #  pf.close()
    #signal.signal(signal.SIGTERM, handler)
    tries = 0
    while not os.path.exists(out_fn):
      time.sleep(1)
      tries += 1
      if tries >= 5:
        if "python" in args[2] and tries <= 10:
          continue
        print("Failed to locate the output file")
        exit(-1)
    with open(out_fn, "r") as stdout:
      while rp.poll() is None:
        x = stdout.read()
        if x:
          sys.stdout.write(x)
          sys.stdout.flush()
        time.sleep(0.5)
except Exception as e:
  print(e)
  os.remove("NoSpherA2.pidfile")
  time.sleep(2)
  
log.close()

print("Finished")
