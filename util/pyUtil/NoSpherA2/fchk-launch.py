import os
import sys
import time
import subprocess
import shutil

fchk_dir = os.getenv("fchk_dir", "")
fchk_file = os.getenv("fchk_file", "")
if not os.path.exists(fchk_dir):
  print("Incorrect launching directory!")
  time.sleep(10)
  exit(1)
os.chdir(fchk_dir)
args = os.getenv("fchk_cmd", "").split('+&-')
print("Running: '" + ' '.join(args) + "'")
log = None
err_fn = None
out_fn = None
inp = None
nr = 0
if sys.platform[:3] == 'win':
    nr = 2
if "orca" in args[0]:
  out_fn = fchk_file + "_orca.log"
elif "g" in args[0]:
  out_fn = fchk_file + ".out"
elif "elmo" in args[nr]:
  if sys.platform[:3] != 'win':
    inp = open(args[2],'r')
  out_fn = fchk_file + '.out'
elif "python" in args[2]:
  out_fn = fchk_file + "_pyscf.log"

if os.path.exists(out_fn):
  shutil.move(out_fn,out_fn+'_old')
if out_fn:
  log = open(out_fn, 'w')
  print(out_fn)

p = None

if any("elmo" in x for x in args):
  if sys.platform[:3] != 'win':
    p = subprocess.Popen(args, stdin=inp, stdout=log)
  else:
    p = subprocess.Popen(args, stdout=log)
else:
  p = subprocess.Popen(args, stdout=log)

if "ubuntu" in args[0]:
  print("Starting Ubuntu and running pySCF, please be patient for start")
if out_fn == None:
  if "ubuntu" in args[0]:
    out_fn = fchk_file + "_pyscf.log"
  elif out_fn == None:
    out_fn = fchk_file + ".log"
tries = 0
while not os.path.exists(out_fn):
  time.sleep(1)
  tries += 1
  if tries >= 5:
    if "python" in args[2] and tries <=10:
      continue
    print("Failed to locate the output file")
    exit(1)
with open(out_fn, "r") as stdout:
  import sys
  while p.poll() is None:
    x = stdout.read()
    if x:
      sys.stdout.write(x)
      sys.stdout.flush()
    time.sleep(0.5)

print("Finished")
