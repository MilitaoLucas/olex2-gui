print("Hello")
import subprocess
from subprocess import call
import sys
import os
import re
import glob
import xml.etree.ElementTree as ET
global nqa
nqa = False
from shutil import copyfile

def query_yes_no(question, default="yes"):
  """Ask a yes/no question via raw_input() and return their answer.

  "question" is a string that is presented to the user.
  "default" is the presumed answer if the user just hits <Enter>.
  It must be "yes" (the default), "no" or None (meaning
  an answer is required of the user).

  The "answer" return value is True for "yes" or False for "no".
  """
  if nqa:
    print("Bye!")
    return False

  valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
  if default is None:
    prompt = " [y/n] "
  elif default == "yes":
    prompt = " [Y/n] "
  elif default == "no":
    prompt = " [y/N] "
  else:
    raise ValueError("invalid default answer: '%s'" % default)

  while True:
    sys.stdout.write(question + prompt)
    choice = input().lower()
    if default is not None and choice == '':
      return valid[default]
    elif choice in valid:
      return valid[choice]
    else:
      sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

def do_update_instructions():
  from subprocess import call
  fp = "update_instructions.txt"
  if not os.path.exists(fp):
    print("No special update instructions!")
    return

  _ = open("def.txt",'r').readlines()
  for line in _:
    if "p_scope" in line:
      o_scope = line.split("=")[1].strip()
      print("============")
      print("The original scope of this plugin is: %s" %o_scope)

  scope = None	
  ##RUN UPDATE INSTRUCTIONS
  print("**** %s" %fp)
  rFile=open(fp, 'r').readlines()
  for instruction in rFile:
    print("%s" %instruction)
    if "=" not in instruction:
      call(instruction.split())

    elif ">" in instruction:
      if not scope:
        ##GET SCOPE STRING
        _ = open("def.txt",'r').readlines()
        for line in _:
          if "p_scope" in line:
            scope = line.split("=")[1].strip()
        print("============")
        print("The scope of this plugin will be: %s" %scope)

      f_src = instruction.split("=>")[0].strip()
      f_dst = instruction.split("=>")[1].strip()
      print(("%s: Replacing '%s' in file with '%s'" %(f_src, o_scope, scope)))
      t = open (f_src, 'r').read()
      t = t.replace(o_scope, scope)
      wFile = open(f_dst,'w')
      wFile.write(t)
      if f_src != f_dst:
        os.remove(f_src)

    else:
      print("Not an os call")
      ins = instruction.strip().split("=")[0]
      arg = instruction.strip().split("=")[1].split(",")
      arg.append('olex2')
      arg.append('default')
      arg.append('tables')
      print(ins)
      print(arg)
      a_dir = r"./%s"%ins
      l = [name for name in os.listdir(a_dir) if os.path.isdir(os.path.join(a_dir, name))]
      print(l)
      for item in l:
        if item in arg:
          continue
        else:
          command = "rm -r ./%s/%s" %(ins, item) 
          print("deleting %s" %item)
          call(command.split())

def get_current_timestamp():
  import datetime
  return datetime.datetime.now().strftime("%Y%m%d%H%M")

def git(*args):
  return subprocess.check_call(['git'] + list(args))

def replace_time_stamp(s, m, t):
  import xml.dom.minidom
  import io

  dom = xml.dom.minidom.parse(io.StringIO(s))
  l = ['module', 'internal_module']
  for bit in l:
    for module in dom.getElementsByTagName(bit):
      name = module.getElementsByTagName("name")[0]
      if name.childNodes[0].wholeText != '%s' %m: continue
      release = module.getElementsByTagName("release")[0]
      # this is the <release> ... </release> and ... is a child text node
      # of that object
      release.childNodes[0].replaceWholeText(t)
  print(dom.toxml())
  return dom.toxml()

import os, shutil
def copytree(src, dst, symlinks=False, ignore=None, search=None, replace=None):
  for item in os.listdir(src):
    if search:
      item_new = item.replace(search,replace)
    s = os.path.join(src, item)
    d = os.path.join(dst, item_new)
    if os.path.isdir(s):
      shutil.copytree(s, d, symlinks, ignore)
    else:
      shutil.copy2(s, d)	

def update():
  ## 1) Figure out what is to do
  print("Now running this script: %s" %sys.argv[0])
  if len(sys.argv) == 1:
    print("Please provide <olex2 release tag> <module>.")
    print("If no release tag is provided, 'alpha' is assumed.")
    print("Bye.")
    return

  elif len(sys.argv) == 2:
    module = sys.argv[1]
    olex2_version = "alpha"

  elif len(sys.argv) == 3:
    olex2_version = sys.argv[1]
    module = sys.argv[2]
  print("Version" + olex2_version)

  modules = []
  vp = os.sep.join([r"/var/www/plugins", olex2_version, module])
  g = glob.glob(vp)
  for directory in g:
    modules.append(directory)
    print("Updating: " + directory)
  if not modules:
    if "plugin-" not in module:
      module = "plugin-" + module
    modules.append(os.sep.join([r"/var/www/plugins", olex2_version, module]))
    print("Updating: " + module)

  if "1.2" not in olex2_version:
    olex2_version = "1.2-" + olex2_version

  ## 2) Deal with GIT	
  if not query_yes_no("This will update the modules printed above. Continue?", "no"):
    return

  for dp in modules:
    try:
      print(dp)
      if not os.path.exists(dp):
        print(("This module does not exist %s" %dp))
        continue

      print(("Updating module %s" %dp))
      os.chdir(dp)
      git("status")
      print("GIT status printed above.\n")
      if not query_yes_no("Continue? Next step will perform a hard reset!"):
        return
      git("reset", "--hard")
      git("pull")
      git("status")

      filelist = [ f for f in os.listdir('.') if f.endswith(".pyc") ]
      for f in filelist:
        os.remove(os.path.join('.', f)) 


      
      if "1.5" in olex2_version:
        cmd = "%s -m compileall -l ." %(sys.executable)
      else:
        cmd = "%s -m compileall -l ." %("python2")
      print("Running: %s using %s" %(cmd, sys.executable))
      if subprocess.call(cmd, shell=True) != 0: #This also works
      #if subprocess.call([sys.executable, '-m', 'compileall', '-l', '.']) != 0:
        raise RuntimeError("Failed to compile the sources")
      #if "python3" in sys.executable:
      if "1.5" in olex2_version:
        print("Copying compiled files")
        src = "./__pycache__"
        dst = "."
        print("Copying compiled files from %s to %s" %(src, dst))
        copytree(src, dst, search='.cpython-38', replace="")

      ## Run Updating instructions
      if not query_yes_no("Continue running the update instructions?"):
        return
      do_update_instructions()

      if not query_yes_no("Release this update?"):
        return
      t_str = get_current_timestamp()
      wFile =open("release",'w')
      wFile.write(t_str)
      wFile.close()

      print(repr(sys.argv[0]))

      os.chdir("..")
      l = []
      m_name = module.lstrip("plugin-").rstrip("/")

      t = open('available.xml', 'r').read()
      xml = replace_time_stamp(t, m_name, t_str)

      if not query_yes_no("Write this file?"):
        return

      f = open('available.xml', 'w')
      f.write(xml)
      f.close()
    except Exception as e:
      print("UPDATE FAILED!: %s" %e)
update()
