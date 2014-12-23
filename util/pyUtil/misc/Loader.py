import os
import sys
import olx
import olex
import shutil
from threading import Thread
from threads import ThreadEx
from threads import ThreadRegistry

available_modules = None #list of Module
avaialbaleModulesRetrieved = False
failed_modules = {}
current_module = None
info_file_name = "modules-info.htm"

debug = (olx.app.IsDebugBuild() == 'true')

class Module:
  def __init__(self, name, folder_name, description, url, release_date, action):
    self.name = name
    self.folder_name = folder_name
    self.description = description
    self.url = url
    self.release_date = release_date
    self.action = action # 0 - nothing, 1 - install, 2 - update, 3-re-install
    self.interbal = False

def getModulesDir():
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  base = olex.f(OV.GetParam('user.modules.location'))
  return "%s%smodules" %(base, os.sep)

def getModule(name, email=None):
  import HttpTools
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  url_base = OV.GetParam('user.modules.provider_url')
  dir = getModulesDir()
  if not os.path.exists(dir):
    os.mkdir(dir)

  etoken = None
  etoken_fn = "%s%setoken" %(dir, os.sep)
  if email:
    import re
    email = email.strip()
    if not re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", email):
      olex.writeImage(info_file_name, "Failed to validate e-mail address", 0)
      return False
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
<font color='red'><b>An error occurred while downloading the extension.</b></font>
<br>%s<br>Please restart Olex2 and try again.
''' %(str(e))
      if debug:
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
<font color='red'><b>An error occurred while installing the extension.</b></font>
<br>%s<br>Please restart Olex2 and try again.
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
      'ref': OV.GetParam("user.modules.reference", ""),
      't' : OV.GetTag()
    }
    f = HttpTools.make_url_call(url, values)
    f = f.read()
    if f.startswith('<html>'):
      olex.writeImage(info_file_name, f[6:], 0)
    else:
      zp = ZipFile(StringIO(f))
      zp.extractall(path=dir)
      msg = "Module <b>%s</b> has been successfully installed/updated" %name
      msg += "<br>You have 30 days to evaluate this extension module. Please contact us for further information."
      msg += "<br><font color='green'><b><Please restart Olex2 to activate the extension module.</b></font>"
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
<font color='red'><b>An error occurred while installing the extension.</b></font>
<br>%s<br>Please restart Olex2 and try again.
''' %(str(e))
    olex.writeImage(info_file_name, msg, 0)
    return False

def loadAll():
  dir = getModulesDir()
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
      if _plgl.loadPlugin(d, key, dir):
        print("Module %s has been successfully loaded." %d)
    except Exception, e:
      global failed_modules
      failed_modules[d] = str(e)
      print("Error occurred while loading module: %s" %d)
      if debug:
        sys.stdout.formatExceptionInfo()
  getAvailableModules() #thread
  if olx.HasGUI() == 'true':
    olx.Schedule(2, "spy.plugins.AskToUpdate()", g=True)


def updateKey(module):
  import HttpTools
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  if isinstance(module, basestring):
    found = False
    if available_modules:
      for m in available_modules:
        if m.folder_name == module:
          module = m
          found = True
          break
    if not found:
      print "No modules information available"
      return
  try:
    dir = getModulesDir()
    etoken_fn = "%s%setoken" %(dir, os.sep)
    if os.path.exists(etoken_fn):
      etoken = open(etoken_fn, "rb").readline().strip()
    else:
      print("Failed to update the key - email is not registered")
      return False
    url = OV.GetParam('user.modules.provider_url') + "update"
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
    if debug:
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
  if not OV.canNetwork(show_msg=False):
    return
  url_base = OV.GetParam('user.modules.provider_url')
  try:
    url = url_base + "available"
    values = {
     't' : OV.GetTag()
    }
    f = HttpTools.make_url_call(url, values)
    xml = et.fromstring(f.read())
    for m in xml.getchildren():
      if m.tag == "module" or m.tag == "internal_module":
        try:
          module = Module(m.find("title").text,
                          m.find("name").text,
                          m.find("description").text,
                          m.find("url").text,
                          m.find("release").text, 0)
          if m.tag == "internal_module":
            module.internal = True
          else:
            module.internal = False
          available_modules.append(module)
        except Exception, e:
          if debug:
            sys.stdout.formatExceptionInfo()
          pass
    dir = getModulesDir()
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
              m.action = 3 #reinstall
          else:
            m.action = 3
        elif d < m.release_date:
          m.action = 2
      else:
        m.action = 1
  except Exception, e:
    if debug:
      sys.stdout.formatExceptionInfo()
    return "No modules information available"
  finally:
    avaialbaleModulesRetrieved = True

class ModuleListThread(ThreadEx):
  instance = None
  def __init__(self):
    Thread.__init__(self)
    ThreadRegistry().register(ModuleListThread)
    ModuleListThread.instance = self

  def run(self):
    import time
    time.sleep(3)
    getAvailableModules_()
    ModuleListThread.instance = None

def getAvailableModules(in_thread=True):
  global avaialbaleModulesRetrieved
  if avaialbaleModulesRetrieved:
    return
  if ModuleListThread.instance:
    if not in_thread:
      ModuleListThread.instance.join()
    else:
      return
  else:
    if in_thread:
      ModuleListThread().start()
    else:
      ModuleListThread().run()

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
  getAvailableModules(False)
  global available_modules
  rv = []
  for idx, m in enumerate(available_modules):
    if m.internal: continue
    rv.append(getModuleCaption(m) + ("<-%d" %(idx)))
  return ';'.join(rv)

def getInfo():
  global current_module
  if not current_module:
    return ""
  preambula = ""
  if current_module.action == 3:
    preambula = "<font color='red'>This module has <b>expired</b></font>, please either re-install it or contact"+\
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
  import HttpTools
  if not HttpTools.auto_update:
    return
  global avaialbaleModulesRetrieved
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  if not OV.canNetwork(show_msg=False):
    return
  if not avaialbaleModulesRetrieved and olx.HasGUI() == 'true':
    olx.Schedule(2, "spy.plugins.AskToUpdate()", g=True)
    return
  manual_update = OV.GetParam("user.modules.manual_update", False)
  if manual_update:
    return
  dir = getModulesDir()
  etoken_fn = "%s%setoken" %(dir, os.sep)
  if not os.path.exists(etoken_fn):
    return
  to_update = []
  to_update_names = []
  global available_modules
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
      OV.SetParam("user.modules.manual_update", True)
    if 'Y' in res:
      for m in to_update:
        status = getModule(m.folder_name)
        if status: status = "OK, restart Olex2 to load new version"
        else: status = "Failed"
        print("Updating '%s': %s" %(m.folder_name, status))

def offlineInstall():
  import gui
  src = gui.FileOpen("Please choose the offline module archive", "*.zip", ".")
  if not src:
    return
  from zipfile import ZipFile
  zip = ZipFile(src)
  names = zip.namelist()
  if not names:
    print("Empty archive...")
    return
  module_name = names[0].split('/')[0]
  if not module_name:
    print("Invalid archive")
    return
  licence_files = ('licence.txt', 'licence.htm')
  licence_file_name = ''
  for n in names:
    for l in licence_files:
     if n.endswith(l):
       licence_file_name = n
       break
     if licence_file_name:
       break
  if licence_file_name:
    lic = zip.open(licence_file_name).read()
    sz = [int(i) for i in olx.GetWindowSize().split(',')]
    w = int(sz[2]*2/3)
    h = int(sz[3]*2/3)
    olex.writeImage("module_licence_content", lic)
    olex.writeImage("module_licence",
"""
 <html><body>
  <table width='100%%'>
    <tr><td colspan='2'>
     <input type='text' multiline='true'
      value="spy.vfs.read_from_olex('module_licence_content')" width='100%%' height='%s' />
     </td></tr>
    <tr>
     <td align='center'><input type='button' value='Accept' onclick="html.EndModal('~popup_name~', 1)"></td>
     <td align='center'><input type='button' value='Decline' onclick="html.EndModal('~popup_name~', 2)"></td>
    </tr>
  </table>
  </body></html>
""" %(h-100),
      0)
    olx.Popup("module_licence", "module_licence",
       b="t",  t="Licence agreement",
       x=sz[0] + sz[2]/2 - w/2, y=sz[1] + sz[3]/2 - h/2,
       w=w, h=h, s=False)
    res = olx.html.ShowModal("module_licence", True)
    olex.writeImage("module_licence_content", "", 0)
    olex.writeImage("module_licence", "", 0)
    if int(res) != 1:
      zip.close()
      return
  dir = getModulesDir()
  if not os.path.exists(dir):
    os.mkdir(dir)
  else:
    mdir = dir + os.sep + module_name
    if os.path.exists(mdir):
      res = olx.Alert("Warning", "Destination folder exists.\nOverwrite?", "YCQ")
      if res != 'Y':
        return
      print("Removing previous installation...")
      try:
        shutil.rmtree(mdir)
      except:
        print("Failed to remove previous installation. Please restart Olex2 and try again...")
        return
  zip.extractall(path=dir)
  zip.close()
  print("Installed successfully '%s'. Please restart Olex2 to load it." %module_name)


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
    olex.registerFunction(updateKey, False, "plugins")
    olex.registerFunction(offlineInstall, False, "plugins")
    loadAll()
  except Exception, e:
    print("Plugin loader initialisation failed: '%s'" %e)
else:
  print("Plugin loader is not initialised")
