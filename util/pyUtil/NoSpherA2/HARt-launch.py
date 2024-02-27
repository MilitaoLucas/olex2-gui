import os
import sys
import time
from subprocess import Popen

hart_dir = os.getenv("hart_dir", "")
hart_file = os.getenv("hart_file", "")
if not os.path.exists(hart_dir):
  print("Incorrect launching directory!")
  time.sleep(20)
  exit(1)
os.chdir(hart_dir)
args = os.getenv("hart_cmd", "").split('+&-')
print("Running: '" + ' '.join(args) + "'")
p = Popen(args)
err_fn = hart_file + "_tonto.out"
out_fn = hart_file + "_tonto.out"
tries = 0
while not os.path.exists(out_fn):
  time.sleep(1)
  tries += 1
  if tries >= 5:
    print("Failed to locate the output file")
    exit(1)
with open(out_fn, "r") as stdout:
  import sys
  while p.poll() is None:
    x = stdout.read()
    if x:
      sys.stdout.write(x)
      sys.stdout.flush()
    time.sleep(1)
with open(err_fn, "rU") as stderr:
  print(stderr.read())

print("Finished")
