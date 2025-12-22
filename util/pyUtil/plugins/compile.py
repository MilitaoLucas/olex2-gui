import os, sys
import shutil
import subprocess

def copytree(src, dst, symlinks=False, ignore=None, search=None, replace=None):
  for item in os.listdir(src):
    if item == ".git":
      continue
    if search:
      item_new = item.replace(search,replace)
    s = os.path.join(src, item)
    d = os.path.join(dst, item_new)
    if os.path.isdir(s):
      shutil.copytree(s, d, symlinks, ignore)
    else:
      print(f"{s} -> {d}")
      shutil.copy2(s, d)

def do_compile(location):
  try :
    for f in os.listdir('.'):
      if f.endswith(".pyc"):
        os.remove(os.path.join('.', f))
    cmd = "%s -m compileall -l %s" %(sys.executable, location)
    print("Running: %s" %(cmd))
    if subprocess.call([sys.executable, '-m', 'compileall', '-l', location]) != 0:
      raise RuntimeError("Failed to compile the sources")
    print("Copying compiled files")
    src = os.path.join(location, "__pycache__")
    dst = location
    print("Copying compiled files from %s to %s" %(src, dst))
    copytree(src, dst,
      search='.cpython-%s%s' %(sys.version_info.major, sys.version_info.minor), replace="")
    return True
  except Exception as e:
    print(e)
    return False

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("Please provide the location to compile files for!")
    exit(1)
  print("Compiling %s" %sys.argv[1])
  if not do_compile(sys.argv[1]):
    exit(1)
  exit(0)