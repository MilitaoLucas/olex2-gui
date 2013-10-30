import os
import sys
import olx
import olex
import shutil

available_modules = None #list of Module
avaialbaleModulesRetrieved = False
failed_modules = {}
current_module = None
info_file_name = "modules-info.htm"

class Module:
  def __init__(self, name, folder_name, description, url, release_date, action):
    self.name = name
    self.folder_name = folder_name
    self.description = description
    self.url = url
    self.release_date = release_date
    self.action = action # 0 - nothing, 1 - install, 2 - update, 3-re-install

def getModule(name, email=None):
  import HttpTools
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  url_base = OV.GetParam('modules.provider_url')
  dir = "%s%smodules" %(olx.app.SharedDir(), os.sep)
  if not os.path.exists(dir):
    os.mkdir(dir)

  etoken = None
  etoken_fn = "%s%setoken" %(dir, os.sep)
  if email:
    try:
      url = url_base + "register"
      values = {
        'e': email
      }
      f = HttpTools.make_url_call(url, values)
      f = f.read().strip()
      if "Error" in f:
        olex.writeImage(info_file_name, "Failed to register e-mail '%s': %s"  %(email, f), 0)
        return False
      efn = open(etoken_fn, "wb")
      efn.write(f)
      efn.close()
      etoken = f
    except Exception, e:
      msg = '''
An error occurred while downloading the extension.<br>%s<br>Please restart Olex2 and try again.
''' %(str(e))
      sys.stdout.formatExceptionInfo()
      olex.writeImage(info_file_name, msg, 0)
      return False

  if etoken is None:
    if os.path.exists(etoken_fn):
      etoken = open(etoken_fn, "rb").readline().strip()
  
  if etoken is None:
    if not email:
      olex.writeImage(info_file_name, "Please provide your e-mail", 0)
    return False
      
  #try to clean up the folder if already exists
  pdir = "%s%s%s" %(dir, os.sep, name)
  old_folder = None
  if os.path.exists(pdir):
    try:
      new_name = pdir + "_"
      if os.path.exists(new_name):
        shutil.rmtree(new_name)
      os.rename(pdir, new_name)
      old_folder = new_name
    except Exception, e:
      msg = '''
An error occurred while installing the extension.<br>%s<br>Please restart Olex2 and try again.
''' %(str(e))
      olex.writeImage(info_file_name, msg, 0)
      return False

  from zipfile import ZipFile
  from StringIO import StringIO
  try:
    url = url_base + "get"
    values = {
      'name': name,
      'at': _plgl.createAuthenticationToken(),
      'et': etoken,
      'ref': OV.GetParam("user.reference", "")
    }
    f = HttpTools.make_url_call(url, values)
    f = f.read()
    if f.startswith('<html>'):
      olex.writeImage(info_file_name, f[6:], 0)
    else:
      zp = ZipFile(StringIO(f))
      zp.extractall(path=dir)
      msg = "Module %s has been successfully installed/updated" %name
      msg += "<br>You have 30 days to evaluate this extension module."
      msg += "<br>Please restart Olex2 to activate the extension module."
      olex.writeImage(info_file_name, msg, 0)
      global available_modules
      if current_module:
        idx = available_modules.index(current_module)
        if idx >= 0:
          del available_modules[idx]
      #clean up the old folder if was created
      if old_folder is not None:
        try:
          shutil.rmtree(old_folder)
        except: # must not happen, but not dangerous
          pass
      return True
  except Exception, e:
    msg = '''
An error occurred while installing the extension.<br>%s<br>Please restart Olex2 and try again.
''' %(str(e))
    olex.writeImage(info_file_name, msg, 0)
    return False

def loadAll():
  dir = "%s%smodules" %(olx.app.SharedDir(), os.sep)
  if not os.path.exists(dir):
    return
  all = os.listdir(dir)
  for d in all:
    dl = "%s%s%s" %(dir, os.sep, d)
    if not os.path.isdir(dl): continue
    key = "%s%skey" %(dl, os.sep)
    enc = "%s%s%s.pyc" %(dl, os.sep, d)
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
      global failed_modules
      failed_modules[d] = str(e)
      print("Error occurred while loading module: %s" %d)
  getAvailableModules() #thread
  olx.Schedule(2, "spy.plugins.AskToUpdate()", g=True)


def updateKey(module):
  import HttpTools
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  try:
    dir = "%s%smodules" %(olx.app.SharedDir(), os.sep)
    etoken_fn = "%s%setoken" %(dir, os.sep)
    if os.path.exists(etoken_fn):
      etoken = open(etoken_fn, "rb").readline().strip()
    else:
      print("Failed to update the key - email is not registered")
      return False
    url = OV.GetParam('modules.provider_url') + "update"
    values = {
      'n': module.folder_name,
      'at': _plgl.createAuthenticationToken(),
      'et': etoken
    }
    f = HttpTools.make_url_call(url, values)
    key = f.read()
    if key.startswith("<html>") or len(key) < 40:
      raise Exception(key[6:])
    keyfn = "%s%s%s%skey" %(dir, os.sep, module.folder_name, os.sep)
    keyf = open(keyfn, "wb")
    keyf.write(key)
    keyf.close()
    try:
      if _plgl.loadPlugin(module.folder_name, key):
        print("Module %s has been successfully loaded." %(module.name))
        return True
    except Exception, e:
      print("Error while reloading '%s': %s" %(module.name, e))
      return False
  except Exception, e:
    sys.stdout.formatExceptionInfo()
    print("Error while updating the key for '%s': '%s'" %(module.name, e))
    return False

def getAvailableModules_():
  global avaialbaleModulesRetrieved
  global current_module
  global available_modules
  global failed_modules
  if avaialbaleModulesRetrieved:
    return
  import xml.etree.cElementTree as et
  current_module = None
  available_modules = []
  import HttpTools
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  url_base = OV.GetParam('modules.provider_url')
  try:
    url = url_base + OV.GetParam('modules.available_modules_file')
    f = HttpTools.make_url_call(url, None)
    xml = et.fromstring(f.read())
    for m in xml.getchildren():
      if m.tag == "module":
        try:
          module = Module(m.find("title").text,
                          m.find("name").text,
                          m.find("description").text,
                          m.find("url").text,
                          m.find("release").text, 0)
          available_modules.append(module)
        except:
          pass
    dir = "%s%smodules" %(olx.app.SharedDir(), os.sep)
    for m in available_modules:
      md = "%s%s%s" %(dir, os.sep, m.folder_name)
      if os.path.exists(md):
        rd = "%s%srelease" %(md, os.sep)
        d = 0
        if os.path.exists(rd):
          try:
            d = file(rd, 'rb').read().strip()
          except:
            pass
        if m.folder_name in failed_modules:
          if "expired" in failed_modules[m.folder_name]:
            if updateKey(m):
              m.action = 1
          else:
            m.action = 3
        elif d < m.release_date:
          m.action = 2
      else:
        m.action = 1
  except Exception, e:
    sys.stdout.formatExceptionInfo()
    return "No modules information available"
  finally:
    avaialbaleModulesRetrieved = True

def getAvailableModules():
  from threads import ThreadEx
  class AMT(ThreadEx):
    instance = None
    def run(self):
      AMT.instance = self
      getAvailableModules_()
      AMT.instance = None
  if AMT.instance:
    return
  AMT().start()
  

# GUI specific functions
def getModuleCaption(m):
  if m.action == 1:
    return "%s - Install" %(m.name)
  elif m.action == 2:
    return "%s - Update" %(m.name)
  elif m.action == 3:
    return "%s - Re-install" %(m.name)
  else:
    return "%s - Up-to-date" %(m.name)

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
  preambula = ""
  if current_module.action == 3:
    preambula = "This module has <b>expired</b>, please either re-install it or contact"+\
      " <a href='shell(mailto:enquiries@olexsys.org?subject=Olex2%20extensions%20licence)'>"+\
      "OlexSys Ltd</a> to extend the licence.<br>"
  return preambula + "<a href='shell %s'>Module URL: </a> %s<br>%s"\
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
  elif current_module.action == 3:
    action = "Re-install"
  else:
    action = 'Nothing to do'
  return action

def doAct():
  global current_module
  if current_module is None or current_module.action == 0:
    return
  else:
    getModule(current_module.folder_name, olx.html.GetValue('modules_email'))
    current_module = None
    olx.html.Update()
  

def getCurrentModuleName():
  global current_module
  global available_modules
  if current_module is None:
    return ""
  return "%d" %available_modules.index(current_module)

def AskToUpdate():
  import ConfigParser
  global available_modules
  global avaialbaleModulesRetrieved
  if not avaialbaleModulesRetrieved:
    olx.Schedule(3, "spy.plugins.AskToUpdate()", g=True)
    return
  dir = "%s%smodules" %(olx.app.SharedDir(), os.sep)
  cfg_fn = "%s%smodules.cfg" %(dir, os.sep)
  manual_update = False
  try:
    if os.path.exists(cfg_fn):
      config = ConfigParser.RawConfigParser()
      config.read(cfg_fn)  
      manual_update = config.getboolean("Update", "manual")
      if manual_update:
        return
  except:
    pass
  etoken_fn = "%s%setoken" %(dir, os.sep)
  if not os.path.exists(etoken_fn):
    return
  to_update = []
  to_update_names = []
  for m in available_modules:
    if m.action == 2:
      to_update.append(m)
      to_update_names.append(m.name)
  if to_update:
    res = olx.Alert("Module updates available",
          "Would you like to try updating the Olex2 extension modules?\n"+
          "Updates are available for: " +' '.join(to_update_names),
          "YNR", "Manage modules manually")
    if 'R' in res:
      try:
        config = ConfigParser.RawConfigParser()
        if os.path.exists(cfg_fn):
          config.read(cfg_fn)
        if not config.has_section("Update"):
          config.add_section("Update")
        config.set("Update", "manual", True)
        with open(cfg_fn, "wb") as cfg_file:
          config.write(cfg_file)
      except:
        pass
    if 'Y' in res:
      for m in to_update:
        status = getModule(m.folder_name)
        if status: status = "OK, restart Olex2 to load new version"
        else: status = "Failed"
        print("Updating '%s': %s" %(m.folder_name, status))
   
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
    olex.registerFunction(AskToUpdate, False, "plugins")
    loadAll()
  except Exception, e:
    print("Plugin loader initialisation failed: '%s'" %e)
else:
  print("Plugin loader is not initialised")
