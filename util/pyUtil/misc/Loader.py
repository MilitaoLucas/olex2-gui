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

from olexFunctions import OlexFunctions
OV = OlexFunctions()
green = OV.GetParam('gui.green')
orange = OV.GetParam('gui.orange')
red = OV.GetParam('gui.red')
at = None

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
  base = olex.f(OV.GetParam('user.modules.location'))
  return "%s%smodules" %(base, os.sep)

def getAuthenticationToken(force=False):
  global at
  force = force in [True, 'True', 'true']
  if force:
    at = None
  elif at:
    return at
  tfn = os.path.join(olx.app.SharedDir(), "ext1.token")
  if not force and os.path.exists(tfn):
    import time
    fst = os.stat(tfn)
    tdiff = long(time.time()) - fst.st_ctime
    #read cache only if within 36 days of creation
    if tdiff < 60*60*24*36:
      with open(tfn, "r") as tf:
        at = tf.readline().strip()
      if _plgl.doesNeedUpdating(at):
        at = None
  if not at:
    ats = _plgl.createAuthenticationTokens()
    if ';' in ats:
      try:
        import HttpTools
        url_base = OV.GetParam('user.modules.provider_url')
        url = url_base + "match"
        values = {
          'at': ats
        }
        f = HttpTools.make_url_call(url, values, http_timeout=30)
        f = f.read().strip()
        if f:
          if "Error" not in f:
            at = f
        else:
          at = ats.split(";")[-1]
      except Exception, e:
        print("Failed to match the authentication tokens %s" %str(e))
        at = _plgl.createAuthenticationToken()
    else:
      at = ats
    if at:
      with open(tfn, "wb") as tf:
        tf.write(at)
    else:
      raise Exception("Could not retrieve authentication token")
  return at

def getModule(name, email=None):
  import HttpTools
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  url_base = OV.GetParam('user.modules.provider_url')
  m_dir = getModulesDir()
  if not os.path.exists(m_dir):
    os.mkdir(m_dir)

  etoken = None
  etoken_fn = "%s%setoken" %(m_dir, os.sep)
  if email:
    import re
    email = email.strip()
    if not re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", email):
      olex.writeImage(info_file_name, "<font color='%s'><b>Failed to validate e-mail address</b></font>" %red, 0)
      return False
  if email:
    try:
      url = url_base + "register"
      values = {
        'e': email
      }
      f = HttpTools.make_url_call(url, values, http_timeout=30)
      f = f.read().strip()
      if "Error" in f:
        olex.writeImage(info_file_name, "<font color='%s'><b>Failed to register e-mail '%s': %s</b></font>" %(red, email, f), 0)
        return False
      with open(etoken_fn, "wb") as efn:
        efn.write(f)
      etoken = f
    except Exception, e:
      msg = '''
<font color='%s'><b>An error occurred while downloading the extension.</b></font>
<br>%s<br>Please restart Olex2 and try again.
''' %(red, str(e))
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

  try:
    url = url_base + "get"
    values = {
      'name': name,
      'at': getAuthenticationToken(),
      'et': etoken,
      'ref': OV.GetParam("user.modules.reference", ""),
      't' : OV.GetTag()
    }
    f = HttpTools.make_url_call(url, values, http_timeout=30)
    f = f.read()
    if f.startswith('<html>'):
      txt = f[6:]
      txt = txt.replace("Your licence has expired","<font color='%s'><b>Your %s licence has expired</b></font>" %(red,name))
      txt = txt.replace("Unknown/invalid module name","<font color='%s'><b>Unknown or invalid module %s</b></font>" %(red,name))
      txt = txt.replace("The activation link is sent. Check your e-mail. Once the download is activated, install the module again","<font color='%s'>Please check your e-mail to activate the <b>%s</b> module and then press the <b>Install</b> button above.</font>" %(green,name))

      #if "expired" in txt:
        #expired_pop(name)

      olex.writeImage(info_file_name, txt, 0)

    else:
      _ = os.path.join(m_dir, "%s.update" %name)
      with open(_,'wb') as wFile:
        wFile.write(f)

      if not update_or_install(name):
        msg = "<font color='%s'>Module <b>%s</b> update failed.</font><br>" %(red, name)
        olex.writeImage(info_file_name, msg, 0)
        return

      msg = "<font color='%s'>Module <b>%s</b> has been successfully installed or updated.</font><br>" %(green, name)
      msg += "<br>This module will expire at some point. If that happens, please contact us for further information."
      msg += "<br><font color='%s'><b><Restart Olex2 to load the new extension module.</b></font>" %orange
      olex.writeImage(info_file_name, msg, 0)


      global available_modules
      if current_module:
        current_module.action = 4
        ##if idx >= 0:
          ##del available_modules[idx]
        ##getAvailableModules()
      return True
  except Exception, e:
    msg = '''
<font color='%s'><b>An error occurred while installing the extension.</b></font>
<br>%s<br>Please restart Olex2 and try again.
''' %(red, str(e))
    olex.writeImage(info_file_name, msg, 0)
    return False


def rollback(d):
  print "Rolling back extension module %s" %d
  update_or_install(d,rollback=True)

def update_or_install(d, rollback=False):
  """Update or install extension modules.

  Updating or installing happens from a ZIP file. This can be a file obtained from the distro or can be a previous version of the module (rollback).
 """

  m_dir = getModulesDir()
  if rollback:
    update_zip = os.path.join(m_dir, "%s.rollback.zip" %d)
  elif ".update" not in d:
    update_zip = os.path.join(m_dir, "%s.update" %d)
  else:
    update_zip = os.path.join(m_dir, d)

  if os.path.exists(update_zip):
    #try to clean up the folder if already exists
    pdir = "%s%s%s" %(m_dir, os.sep, d.replace(".update",""))
    if os.path.exists(pdir):
      if ".update" not in pdir:
        try:
          if not rollback:
            rollback_zip = os.path.join("%s.rollback" %pdir)
            shutil.make_archive(rollback_zip, 'zip', pdir)
            print "The original module %s has been backed up." %d
          shutil.rmtree(pdir)
        except Exception, e:
          print "The original module %s could not be removed" %d
          return False
    try:
      from zipfile import ZipFile
      zp = ZipFile(update_zip)
      path = m_dir
      if rollback:
        path = os.path.join(m_dir, d)
      zp.extractall(path=path)
      zp.close()
      print "Module %s has been installed/updated" %d
      retVal = True
    except:
      print "Module %s is no longer present" %d
      return False
    try:
      os.remove(update_zip)
      retVal = True
    except:
      print "Update file for module %s could not be removed" %d
      return False
    return retVal
  else:
    print "This function expected the file %s, but it could not be found." %update_zip
    return False

def loadAll():
  global available_modules
  m_dir = getModulesDir()
  if not os.path.exists(m_dir):
    return
  all_m = os.listdir(m_dir)

  for d in all_m:
    if ".update" in d:
      if not update_or_install(d):
        continue
      all_m.remove(d)

  for d in all_m:
    dl = "%s%s%s" %(m_dir, os.sep, d)
    if not os.path.isdir(dl):continue
    key = "%s%skey" %(dl, os.sep)
    enc = "%s%s%s.pyc" %(dl, os.sep, d)
    if not os.path.exists(enc):
      continue
    if not os.path.exists(key):
      print("The module %s does not contain key file, skipping" %d)
      continue

    key = open(key, 'rb').readline()
    try:
      if _plgl.loadPlugin(d, key, m_dir):
        print("Module %s has been successfully loaded." %d)
    except Exception, e:
      global failed_modules
      failed_modules[d] = str(e)
      print("Error occurred while loading module: %s" %d)
      if debug:
        sys.stdout.formatExceptionInfo()
  getAvailableModules() #thread


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
    m_dir = getModulesDir()
    etoken_fn = "%s%setoken" %(m_dir, os.sep)
    if os.path.exists(etoken_fn):
      etoken = open(etoken_fn, "rb").readline().strip()
    else:
      print("Failed to update the key - email is not registered")
      return False
    url = OV.GetParam('user.modules.provider_url') + "update"
    values = {
      'n': module.folder_name,
      'at': getAuthenticationToken(),
      'et': etoken
    }
    f = HttpTools.make_url_call(url, values, http_timeout=30)
    key = f.read()
    if key.startswith("<html>") or len(key) < 40:
      raise Exception(key[6:])
    keyfn = "%s%s%s%skey" %(m_dir, os.sep, module.folder_name, os.sep)
    with open(keyfn, "wb") as keyf:
      keyf.write(key)
    try:
      if _plgl.loadPlugin(module.folder_name, key, m_dir):
        print("Module %s has been successfully loaded." %(module.name))
        module.action = 0
        return True
    except Exception, e:
      msg = e.message
      if "is expired" in e.message:
        msg = "The key has expired."
      print("Error while reloading '%s': %s" %(module.name, msg))
      return False
  except Exception, e:
    if debug:
      sys.stdout.formatExceptionInfo()
      print("Error while updating the key for '%s': '%s'" %(module.name, e))
    return False

def updateKeys():
  global available_modules
  for m in available_modules:
    if m.folder_name in failed_modules and "expired" in failed_modules[m.folder_name]:
      updateKey(m)
  olx.Schedule(1, "spy.plugins.CheckLicences()", g=True)


def expired_pop(m):
  import OlexVFS

  name = m.folder_name
  full_name = m.name
  d = {}
  d['name'] = name
  d['full_name'] = full_name
  d['email'] = OV.GetParam('user.email')
  d['token'] = getAuthenticationToken()
  d['tag'] = OV.GetTag()

  _ = os.path.join(OV.BaseDir(), "util", "pyUtil", "misc", "expired_pop.html")
  t = open(_,'r').read()%d

  pop_name = "sorry-%s"%name
  htm = "sorry-%s.htm"%name
  OlexVFS.write_to_olex(htm, t)

  width = 800
  border = 10
  height = 520
  x = 50
  y = 50

  pstr = "popup '%s' '%s' -t='%s' -w=%s -h=%s -x=%s -y=%s" %(
    pop_name, htm, pop_name, width+border*2 +10, height+border*2, x, y)
  olx.Schedule(1, pstr)
  olx.Schedule(1, "html.ShowModal(%s, True)"%pop_name)

  #olx.html.SetBorders(pop_name,border)
  #OV.cmd(pstr)
  #olx.html.SetBorders(pop_name,border)

def recordFeedback(email, token, plugin):
  try:
    import HttpTools
    url_base = OV.GetParam('user.modules.provider_url')
    url = url_base + "recordFeedback"
    values = {
      'email': email,
      'token': token,
      'plugin': plugin
    }
    HttpTools.make_url_call(url, values, http_timeout=30)
  except:
    if debug:
      sys.stdout.formatExceptionInfo()
    pass

def ask_for_licence_extension(name, token, tag, institute, confession_status=False,
                              confession_structures=False, confession_have_licence=False,
                              confession_keep_evaluating=False, confession_no_thanks=False):
  d = {}
  d['institute'] = institute
  d['name'] = name
  d['tag'] = tag
  d['token'] = token
  d['email'] = OV.GetParam('user.email')

  t = "mailto:enquiries@olexsys.org?"+\
  "subject=Licence extension for: %(name)s&"+\
  "body=Reference: %(token)s, Olex2 tag: %(tag)s, e-mail: %(email)s@@"

  t += "@@"

  if institute:
    t += "Affiliation: %(institute)s@@"
  else:
    t += "[Please let us know your affiliation!]@@"

  t += "@@"

  if confession_status == 'true':
    t += "-- I am a Student or Postdoc@@"

  if confession_structures == 'true':
    t += "-- I am using this module <b>only</b> for my own work.@@"

  if confession_keep_evaluating == 'true':
    t += "-- I would like to evaluate this module for some more time.@@"

  if confession_have_licence == 'true':
    t += "-- My institution has already purchased a licence.@@"

  if confession_no_thanks == 'true':
    t += "-- I am no longer interested in using this extension module.@@"

  t += "@@"

  t += "If you have any comments or suggestions about %(name)s, please tell us!@@"

  t = t %d
  t = t.replace('@@', '%0D%0A')
  t = t.replace(' ', '%20')
  olx.Shell(t)

  if confession_no_thanks == 'true':
    mdir = getModulesDir() + os.sep + name
    try:
      shutil.rmtree(mdir)
      print "%s has been deleted" %name
    except:
      print "Could not delete %s. Is this folder open?" %name
  else:
    recordFeedback(d['email'], token, name)

def checkLicences():
  queue_pop = [m for m in available_modules if m.action == 3]
  for m in queue_pop:
    expired_pop(m)
  if olx.HasGUI() == 'true':
    olx.Schedule(1, "spy.plugins.AskToUpdate()", g=True)

def getCurrentPlatformString():
  import platform
  sname = platform.system().lower()
  if sname == "darwin":
    sname = "mac"
  else:
    sname = sname[:3]
  arch= platform.architecture()[0]
  if arch == "64bit":
    sname += "64"
  else:
    sname += "32"
  return sname

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
    f = HttpTools.make_url_call(url, values, http_timeout=30)
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
          plat = m.find("platform", "")
          if plat:
            if getCurrentPlatformString() not in plat:
              continue
          available_modules.append(module)
        except Exception, e:
          if debug:
            sys.stdout.formatExceptionInfo()
          pass
    m_dir = getModulesDir()
    for m in available_modules:
      md = "%s%s%s" %(m_dir, os.sep, m.folder_name)
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
            m.action = 3 #reinstall
        elif d < m.release_date:
          m.action = 2
      elif os.path.exists(md + ".rollback.zip"):
        m.action = 5
      else:
        m.action = 1
  except Exception, e:
    if debug:
      sys.stdout.formatExceptionInfo()
    return "No modules information available"
  finally:
    avaialbaleModulesRetrieved = True
    olx.Schedule(1, "spy.plugins.updateKeys()", g=False)

class ModuleListThread(ThreadEx):
  instance = None
  def __init__(self):
    Thread.__init__(self)
    ThreadRegistry().register(ModuleListThread)
    ModuleListThread.instance = self

  def run(self):
    getAvailableModules_()
    ModuleListThread.instance = None

def getAvailableModules(in_thread=True):
  global avaialbaleModulesRetrieved
  OV.Cursor("Getting information about available modules. Please Wait...")
  try:
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
  finally:
    OV.Cursor()

# GUI specific functions
def getModuleCaption(m):
  if m.action == 1:
    return "%s - Install" %(m.name)
  elif m.action == 2:
    return "%s - Update" %(m.name)
  elif m.action == 3:
    return "%s - Re-install" %(m.name)
  elif m.action == 4:
    return "%s - Restart Olex2" %(m.name)
  elif m.action == 5:
    return "%s - Roll-back" %(m.name)
  else:
    return "%s - Up-to-date" %(m.name)

def getModuleList():
  getAvailableModules(False)
  global available_modules
  global current_module
  rv = []
  for idx, m in enumerate(available_modules):
    if m.internal: continue
    rv.append(getModuleCaption(m) + ("<-%d" %(idx)))
  if current_module:
    _ = getModuleCaption(current_module)
    if _ not in ';'.join(rv):
      rv.append(_ + ("<-%d" %(available_modules.index(current_module)))
)
  return ';'.join(rv)

def getInfo():
  global current_module
  if not current_module:
    _ = 'Select a module from the drop-down menu or type the name of a custom module'
    try:
      if olx.html.GetValue('available_modules') != "":
        _ = 'Install Custom Module'
    except:
      pass
    return _
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  preambula = ""
  if current_module.action == 3:
    t = "<a href='shell(mailto:enquiries@olexsys.org?"+\
    "subject=Licence extension for: %s&"+\
    "body=Customer reference: %s, Olex2 tag: %s)'>OlexSys Ltd</a>"
    t = t %(current_module.name, getAuthenticationToken(), OV.GetTag())
    t.replace(' ', '%20')
    preambula = """<font color='%s'>This module has <b>expired</b></font>,
please either re-install it or contact %s to extend the licence.<br>""" %(red, t)
  return preambula + "<font size='3'><b>%s</b></font><br><a href='shell %s'>More Information</a>"\
     %(current_module.description,current_module.url)

def get_module_idx(name):
  global available_modules
  i = 0
  for m in available_modules:
    if m.folder_name == name:
      return i
    i += 1
  return None

def update(idx):
  global current_module
  global available_modules
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  try:
    idx = int(idx)
  except:
    idx = get_module_idx(idx)
    if idx is None:
      return
  current_module = available_modules[idx]
  olx.html.SetItems('available_modules', getModuleList())
  olex.writeImage(info_file_name, "", 0)
  #except:
    #getModule(idx, OV.GetParam('user.email'))
  olx.html.Update()

def getAction():
  global current_module
  if current_module is None:
    action = 'Please Choose'
    try:
      if olx.html.GetValue('available_modules') != "":
        action = 'Install Custom Module'
    except:
      pass
    return action
  elif current_module.action == 1:
    action = "Install"
  elif current_module.action == 2:
    action = "Update"
  elif current_module.action == 3:
    action = "Re-install"
  elif current_module.action == 4:
    action = "Restart Olex2"
  elif current_module.action == 5:
    action = "Enable"
  else:
    action = 'Disable'
  return action

def doAct():
  global current_module
  global avaialbaleModulesRetrieved
  if current_module is None:
    return
  elif current_module.action == 4:
    olx.Restart()
  elif current_module.action == 5:
    rollback(current_module.folder_name)
    avaialbaleModulesRetrieved = False
    getAvailableModules_()
    olx.html.Update()

  elif current_module.action == 0:
    pdir = os.path.join(OV.DataDir(), "modules", current_module.folder_name)
    if not os.path.exists(pdir):
      print("The module folder %s does not exist" %pdir)
      return
    rollback_zip = os.path.join("%s.rollback" %pdir)
    shutil.make_archive(rollback_zip, 'zip', pdir)
    avaialbaleModulesRetrieved = False
    
    print "The original module %s has been backed up and deleted." %current_module.name
    shutil.rmtree(pdir)
    avaialbaleModulesRetrieved = False
    getAvailableModules_()
    olx.html.Update()
    
  else:
    getModule(current_module.folder_name, olx.html.GetValue('modules_email'))
    #current_module = None
    olx.html.Update()

def getCurrentModuleName():
  global current_module
  global available_modules
  if current_module is None:
    return ""
  return "%d" %available_modules.index(current_module)

def AskToUpdate():
  import HttpTools
  global avaialbaleModulesRetrieved
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  if not OV.canNetwork(show_msg=False):
    return
  if not avaialbaleModulesRetrieved:
    if olx.HasGUI() == 'true':
      olx.Schedule(1, "spy.plugins.AskToUpdate()", g=True)
    return
  manual_update = OV.GetParam("user.modules.manual_update", False)
  m_dir = getModulesDir()
  etoken_fn = "%s%setoken" %(m_dir, os.sep)
  if not os.path.exists(etoken_fn):
    if debug:
      print("No email token found - aborting")
    return
  to_update = []
  to_update_names = []
  global available_modules
  for m in available_modules:
    if m.action == 2:
      to_update.append(m)
      to_update_names.append(m.name)
  if manual_update or not HttpTools.auto_update:
    if to_update_names:
      print('Update is available for the following module(s): ' + ' '.join(to_update_names))
      if not HttpTools.auto_update:
        print('But updates are disabled')
    return
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
  m_dir = getModulesDir()
  if not os.path.exists(m_dir):
    os.mkdir(m_dir)
  else:
    mdir = m_dir + os.sep + module_name
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
  zip.extractall(path=m_dir)
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
    olex.registerFunction(updateKeys, False, "plugins")
    olex.registerFunction(offlineInstall, False, "plugins")
    olex.registerFunction(expired_pop, False, "plugins")
    olex.registerFunction(checkLicences, False, "plugins")
    olex.registerFunction(ask_for_licence_extension, False, "plugins")
    olex.registerFunction(rollback, False, "plugins")
    loadAll()
  except Exception, e:
    print("Plugin loader initialisation failed: '%s'" %e)
else:
  print("Plugin loader is not initialised")
