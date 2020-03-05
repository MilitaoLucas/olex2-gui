import os
import sys
import time
import subprocess

discamb_file = os.getenv("discamb_file", "")
if not os.path.exists(discamb_file):
  print("Incorrect launching directory!")
  time.sleep(10)
  exit(1)
os.chdir(discamb_file)
args = os.getenv("discamb_cmd", "").split('+&-')
#print("Running: '" + ' '.join(args) + "'" + ' in: ' + discamb_file)
p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
tries = 0
while not os.path.exists('discamb2tsc.log'):
  time.sleep(1)
  tries += 1
  if tries >= 5:
    print("Failed to locate the output file")
    time.sleep(10)
    exit(1)
with open('discamb2tsc.log', "rU") as stdout:
  while p.poll() is None:
    x = stdout.read()
    if x:
      print x
    time.sleep(1)
  
print "Finished"
