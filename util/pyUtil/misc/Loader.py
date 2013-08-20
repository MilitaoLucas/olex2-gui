import os
import sys
import olx
import olex
import shutil

available_modules = None #list of Module
current_module = None
info_file_name = "modules-info.htm"

class Module:
  def __init__(self, name, folder_name, description, url, release_date, action):
    self.name = name
    self.folder_name = folder_name
    self.description = description
    self.url = url
    self.release_date = release_date
    self.action = action

def getModule(name, email=None):
  import HttpTools
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  url_base = OV.GetParam('modules.provider_url')
  dir = os.path.normpath("%s/modules" %(olx.app.SharedDir()))
  if not os.path.exists(dir):
    os.mkdir(dir)
  else:
    pdir = os.path.normpath("%s/%s" %(dir, name))
    if os.path.exists(pdir):
      try:
        shutil.rmtree(pdir)
      except Exception, e:
        msg = '''
An error occurred while installing the extension.<br>%s<br>Please restart Olex2 and try again.
''' %(str(e))
        olex.writeImage(info_file_name, msg, 0)
        return

  etoken = None
  etoken_fn = os.path.normpath("%s/etoken" %(dir))
  if email:
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
        olex.writeImage(info_file_name, "Failed to register e-mail ''" %email, 0)
        return
      efn = open(etoken_fn, "wb")
      efn.write(f)
      efn.close()
      etoken = f
    except Exception, e:
      msg = '''
An error occurred while downloading the extension.<br>%s<br>Please restart Olex2 and try again.
''' %(str(e))
      olex.writeImage(info_file_name, msg, 0)
      return

  if etoken is None:
    if os.path.exists(etoken_fn):
      etoken = open(etoken_fn, "rb").readline().strip()
  
  if etoken is None:
    if not email:
      olex.writeImage(info_file_name, "Please provide your e-mail", 0)
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
      olex.writeImage(info_file_name, f, 0)
    else:
      zp = ZipFile(StringIO(f))
      zp.extractall(path=dir)
      msg = "Module %s has been successfully installed" %name
      msg += "<br>You have 30 days to evaluate this extension module."
      msg += "<br>Please restart Olex2 to activate the extension module."
      olex.writeImage(info_file_name, msg, 0)
      global available_modules
      idx = available_modules.index(current_module)
      if idx >= 0:
        del available_modules[idx]
  except Exception, e:
    msg = '''
An error occurred while installing the extension.<br>%s<br>Please restart Olex2 and try again.
''' %(str(e))
    olex.writeImage(info_file_name, msg, 0)

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


def getAvailableModules():
  global current_module
  global available_modules
  if available_modules:
    return
  current_module = None
  available_modules = []
  import HttpTools
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  url_base = OV.GetParam('modules.provider_url')
  try:
    url = url_base + OV.GetParam('modules.available_modules_file')
    f = HttpTools.make_url_call(url, None)
    f = f.readlines()
    for l in f:
      l = l.strip().split('&;')
      if len(l) == 5: # name, readable name, short description, url, release date
        try:
          d = int(l[4])
          available_modules.append(Module(l[0], l[1], l[2], l[3], d, 0))
        except:
          continue

    dir = "%s%smodules" %(olx.app.SharedDir(), os.sep)
    for m in available_modules:
      md = "%s%s%s" %(dir, os.sep, m.folder_name)
      if os.path.exists(md):
        rd = "%s%srelease" %(md, os.sep)
        d = 0
        if os.path.exists(rd):
          try:
            d = int(file(rd, 'rb').read().strip())
          except:
            pass
        if d < m.release_date:
          m.action = 2
      else:
        m.action = 1
  except Exception, e:
    sys.stdout.formatExceptionInfo()
    return "No modules information available"

# GUI specific functions
def getModuleCaption(m):
  if m.action == 0:
    return "%s - Up-to-date" %(m.name)
  elif m.action == 1:
    return "%s - Install" %(m.name)
  else:
    return "%s - Update" %(m.name)

def getModuleList():
  global available_modules
  rv = []
  for idx, m in enumerate(available_modules):
    rv.append(getModuleCaption(m) + ("<-%d" %(idx)))
  return ';'.join(rv)

def getInfo():
  global current_module
  if not current_module:
    return ""
  return "<a href='shell %s'>Module URL: </a> %s<br>%s"\
     %(current_module.url, current_module.url, current_module.description)
  
def update(idx):
  global current_module
  global available_modules
  idx = int(idx)
  current_module = available_modules[idx]
  olex.writeImage(info_file_name, "", 0)
  olx.html.Update()

def getAction():
  global current_module
  if current_module is None:
    action = 'Please choose a module'
  elif current_module.action == 1:
    action = "Install"
  elif current_module.action == 2:
    action = "Update"
  else:
    action = 'Nothing to do'
  return action

def doAct():
  global current_module
  if current_module is None or current_module.action == 0:
    return
  else:
    getModule(current_module.folder_name, olx.html.GetValue('MODULES_EMAIL'))
    current_module = None
    olx.html.Update()
  

def getCurrentModuleName():
  global current_module
  global available_modules
  if current_module is None:
    return ""
  return "%d" %available_modules.index(current_module)
   
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
    olex.registerFunction(getAvailableModules, False, "plugins")
    olex.registerFunction(getModuleList, False, "plugins.gui")
    olex.registerFunction(update, False, "plugins.gui")
    olex.registerFunction(getInfo, False, "plugins.gui")
    olex.registerFunction(getAction, False, "plugins.gui")
    olex.registerFunction(getCurrentModuleName, False, "plugins.gui")
    olex.registerFunction(doAct, False, "plugins.gui")
    loadAll()
  except Exception, e:
    print("Plugin loader initialisation failed: '%s'" %e)
else:
  print("Plugin loader is not initialised")
