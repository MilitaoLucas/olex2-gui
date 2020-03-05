import os
import sys
import time
import subprocess

fchk_dir = os.getenv("cuqct_dir", "")
fchk_file = os.getenv("cuqct_file", "")
if not os.path.exists(fchk_dir):
  print("Incorrect launching directory!")
  time.sleep(10)
  exit(1)
os.chdir(fchk_dir)
args = os.getenv("cuqct_cmd", "").split('+&-')
#print("Running: '" + ' '.join(args) + "'" + ' in: ' + fchk_dir)
p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
tries = 0
while not os.path.exists('wfn_2_fchk.log'):
  time.sleep(1)
  tries += 1
  if tries >= 5:
    print("Failed to locate the output file")
    time.sleep(10)
    exit(1)
with open('wfn_2_fchk.log', "rU") as stdout:
  while p.poll() is None:
    x = stdout.read()
    if x:
      print x
    time.sleep(3)
  
print "Finished"
