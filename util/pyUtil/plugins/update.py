print("Hello")
import subprocess
import sys
import os
import glob
nqa = False
import shutil

git_cmd = "git"

def query_yes_no(question, default="yes"):
  """Ask a yes/no question via raw_input() and return their answer.

  "question" is a string that is presented to the user.
  "default" is the presumed answer if the user just hits <Enter>.
  It must be "yes" (the default), "no" or None (meaning
  an answer is required of the user).

  The "answer" return value is True for "yes" or False for "no".
  """
  global nqa
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
  return subprocess.check_call([git_cmd] + list(args))

def replace_time_stamp(s, m, t):
  import xml.dom.minidom
  import io

  dom = xml.dom.minidom.parse(io.StringIO(s))
  l = ['module', 'internal_module']
  for bit in l:
    for module in dom.getElementsByTagName(bit):
      name = module.getElementsByTagName("name")[0]
      if name.childNodes[0].wholeText != m:
        continue
      release = module.getElementsByTagName("release")[0]
      # this is the <release> ... </release> and ... is a child text node
      # of that object
      release.childNodes[0].replaceWholeText(t)
      print("XML date updated")
  return dom.toxml()

def update(base_dir, pythons_exe, modules_path, olex2_tag, module):
  print("Updating: " + module)

  if not query_yes_no("This will update the modules printed above. Continue?", "no"):
    return False

  for python_def in pythons_exe:
    try:
      dp = os.path.join(os.path.join(modules_path, olex2_tag) + python_def[1], module)
      print(dp)
      if not os.path.exists(dp):
        print("This module does not exist %s" %dp)
        continue

      print("Updating module %s" %dp)
      os.chdir(dp)
      git("status")
      print("GIT status printed above.\n")
      if not query_yes_no("Continue? Next step will perform a hard reset!"):
        return False
      # git("reset", "--hard")
      # git("pull")
      # git("status")

      if subprocess.call([python_def[0], os.path.join(base_dir, "compile.py"), dp]) != 0:
        raise RuntimeError("Failed to compile the sources")
      ## Run Updating instructions
      if not query_yes_no("Continue running the update instructions?"):
        return
      do_update_instructions()

      if not query_yes_no("Release this update?"):
        return False
      t_str = get_current_timestamp()
      with open("release",'w') as wFile:
        wFile.write(t_str)
      os.chdir("..")
      m_name = os.path.split(module)[1][7:]
      t = open('available.xml', 'r').read()
      xml = replace_time_stamp(t, m_name, t_str)
      with open('available.xml', 'w') as f:
        f.write(xml)
    except Exception as e:
      print("UPDATE FAILED!: %s" %e)
      return False
  return True

if __name__ == '__main__':
  from optparse import OptionParser

  os.environ['GIT_SSH'] = "C:/Program Files/PuTTY/plink.exe"

  parser = OptionParser(usage='update.py module [1.5-dev]')
  parser.add_option('--plugins-path',
      dest='plugins_path',
      default="/var/www/plugins",
      help='the path to the directory that contains the modules')
  options, args = parser.parse_args()

  print("Now running this script: %s" %sys.argv[0])
  if len(args) == 0:
    print("Please provide <module> <olex2 release tag>[1.5-dev].")
    print("Bye.")
    exit(1)
  elif len(args) == 1:
    module = args[0]
    olex2_version = "1.5-dev"
  elif len(args) == 2:
    module = args[0]
    olex2_version = args[1]
  print("Olex2 tag: " + olex2_version)
  if "plugin-" not in module:
    module = "plugin-" + module
  if sys.platform[:3] == "win":
    py_def = [("d:/python38x64/python.exe", ""), ("d:/python313x64/python.exe", "-py313")]
    git_cmd = "C:/Program Files/Git/bin/git.exe"
  else:
    py_def = [("python3.8", ""), ("python3.13", "-py313")]
  if not update(os.path.split(__file__)[0], py_def, options.plugins_path, olex2_version, module):
    exit(1)
  exit(0)