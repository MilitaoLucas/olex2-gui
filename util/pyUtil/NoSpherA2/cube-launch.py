import os
import sys
import time
import subprocess

fchk_dir = os.getenv("cube_dir", "")
fchk_file = os.getenv("cube_file", "")
if not os.path.exists(fchk_dir):
  print("Incorrect launching directory! %s"%fchk_dir)
  time.sleep(10)
  exit(1)
os.chdir(fchk_dir)
args = os.getenv("cube_cmd", "").split('+&-')
if os.path.exists('NoSpherA2_cube.log'):
  import shutil
  shutil.move('NoSpherA2_cube.log','NoSpherA2_cube.log_org')
#print("Running: '" + ' '.join(args) + "'" + ' in: ' + fchk_dir)
p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
tries = 0
while not os.path.exists('NoSpherA2_cube.log'):
  time.sleep(1)
  tries += 1
  if tries >= 5:
    print("Failed to locate the output file")
    time.sleep(10)
    exit(1)
with open('NoSpherA2_cube.log', "r") as stdout:
  import sys
  while p.poll() is None:
    x = stdout.read()
    if x:
      sys.stdout.write(x)
      sys.stdout.flush()
    time.sleep(1)
    
print(" ")
os.system("pause")
