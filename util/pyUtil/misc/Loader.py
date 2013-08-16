import os
import sys
import olx
import olex
import shutil

def getModule(name, email=None):
  import HttpTools
  url_base = "http://www.olex2.org/PluginProvider/"
  dir = os.path.normpath("%s/modules" %(olx.app.SharedDir()))
  if not os.path.exists(dir):
    os.mkdir(dir)
  else:
    pdir = os.path.normpath("%s/%s" %(dir, name))
    if os.path.exists(pdir):
      try:
        shutil.rmtree(pdir)
      except Exception, e:
        print(e)
        print("An error occurred while installing the plugin. Please restart Olex2 and try again.")
        return

  etoken = None
  etoken_fn = os.path.normpath("%s/etoken" %(dir))
  if email is not None:
    try:
      url = url_base + "register"
      values = {
        'e': email,
      }
      f = HttpTools.make_url_call(url, values)
      f = f.read().strip()
      if "Try again" in f:
        f = HttpTools.make_url_call(url, values)
        f = f.read().strip()
      if "Try again" in f:
        print("Failed to register")
        return
      efn = open(etoken_fn, "wb")
      efn.write(f)
      efn.close()
      etoken = f
    except Exception, e:
      sys.stdout.formatExceptionInfo()
      return

  if etoken is None:
    if os.path.exists(etoken_fn):
      etoken = open(etoken_fn, "rb").readline().strip()
  
  if etoken is None:
    if email is None:
      print("Please provide your e-mail address as the second parameter")
    return
      
  from zipfile import ZipFile
  from StringIO import StringIO
  try:
    url = url_base + "get"
    values = {
      'name': name,
      'at': _plgl.createAuthenticationToken(),
      'et': etoken
    }
    f = HttpTools.make_url_call(url, values)
    f = f.read()
    if f.startswith('<html>'):
      print(f)
    else:
      zp = ZipFile(StringIO(f))
      zp.extractall(path=dir)
      print("Module %s has been successfully installed" %name)
      print("You have 30 days to evaluate this module")
  except Exception, e:
    sys.stdout.formatExceptionInfo()

def loadAll():
  dir = os.path.normpath("%s/modules" %(olx.app.SharedDir()))
  if not os.path.exists(dir):
    return
  all = os.listdir(dir)
  for d in all:
    dl = os.path.normpath("%s/%s" %(dir, d))
    if not os.path.isdir(dl): continue
    key = os.path.normpath("%s/key" %(dl))
    enc = os.path.normpath("%s/%s.pyc" %(dl, d))
    if not os.path.exists(enc):
      continue
    if not os.path.exists(key):
      print("The module %s does not contain key file, skipping" %d)
      continue
    key = open(key, 'rb').readline()
    try:
      if _plgl.loadPlugin(d, key):
        print("Module %s has been successfully loaded." %d)
    except Exception, e:
      print("Error occurred while loading module: %s" %d)
      print(e)
  
path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path)

if sys.platform[:3] == 'win':
  ext = 'pyd'
else:
  ext = 'so'
lib_name = "%s/_plgl.%s" %(path, ext)
if os.path.exists(lib_name) or olx.app.IsDebugBuild() == 'true':
  try:
    import _plgl
    olx.LoadDll(lib_name)
    olex.registerFunction(getModule, False, "plugins")
    loadAll()
  except Exception, e:
    print("Plugin loader initialisation failed: '%s'" %e)
else:
  print("Plugin loader is not initialised")
