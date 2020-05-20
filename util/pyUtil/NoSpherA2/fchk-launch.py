import os
import sys
import time
import subprocess

fchk_dir = os.getenv("fchk_dir", "")
fchk_file = os.getenv("fchk_file", "")
if not os.path.exists(fchk_dir):
  print("Incorrect launching directory!")
  time.sleep(10)
  exit(1)
os.chdir(fchk_dir)
args = os.getenv("fchk_cmd", "").split('+&-')
#print("Running: '" + ' '.join(args) + "'")
log = None
err_fn = None
out_fn = None
if "orca" in args[0]:
  log = open(fchk_file + '_orca.log', 'w')
  out_fn = fchk_file + "_orca.log"
p = subprocess.Popen(args, stdout=log)
if "ubuntu" in args[0]:
  print("Starting Ubuntu and running pySCF, please be patient for start")
if "ubuntu" in args[0]:
  out_fn = fchk_file + "_pyscf.log"
elif out_fn == None:
  out_fn = fchk_file + ".log"
tries = 0
while not os.path.exists(out_fn):
  time.sleep(1)
  if "ubuntu" in args[0]:
    time.sleep(5)
  tries += 1
  if tries >= 5:
    print("Failed to locate the output file")
    exit(1)
with open(out_fn, "rU") as stdout:
  import sys
  while p.poll() is None:
    x = stdout.read()
    if x:
      sys.stdout.write(x)
      sys.stdout.flush()
    time.sleep(0.5)
  
print("Finished")
