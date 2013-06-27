import olex
import olx

from olexFunctions import OlexFunctions
OV = OlexFunctions()


def FileOpen(title, filter, location, default='', default_name=''):
  res = olx.FileOpen(title, filter,location, default_name)
  if not res:
    return default
  return res

def FileSave(title, filter, location, default='', default_name=''):
  res = olx.FileSave(title, filter,location, default_name)
  if not res:
    return default
  return res

olex.registerFunction(FileOpen, False, "gui.dialog")
olex.registerFunction(FileSave, False, "gui.dialog")

def About():
  sz = [int(i) for i in olx.GetWindowSize().split(',')]
  w = int(olx.html.ClientWidth('self'))
  h = int(olx.html.ClientHeight('self'))
  sw = 500+2*15+10
  sh = 280+2*15+150
  olx.Popup("about '%s/etc/gui/help/about.htm' -x=%d -y=%d -w=%d -h=%d"
            %(olx.BaseDir(),
              sz[0] + w/2 + sw/2,
              sz[1] + h/2 - sh/2,
              sw,
              sh))


olex.registerFunction(About, False, "gui")

def SwitchSettings(name="solve"):
  name = name.lower()
  auto_close_settings = OV.GetParam('user.auto_close_settings_panel')
  if not auto_close_settings:
    t = "cbtn* 1 cbtn-%s 1 *settings 0 %s-settings 0 1" %(name, name)
  else:
    t = "cbtn* 1 cbtn-%s 1 *settings 0" %name
  olx.html.ItemState(t)

olex.registerFunction(SwitchSettings, False, "gui")


def SwitchPanel(name="home"):
  name = name.lower()
  if name == "home":
    olx.html.ItemState("* 0 tab* 2 tab-home 1 logo1 1 index-home* 1 info-title 1")
    #olx.html.ItemState("index* 0 index-home 1 tab* 2")
  elif name == "work":
    if olx.IsFileLoaded() != "false":
      olx.html.ItemState("* 0 tab* 2 tab-work 1 logo1 1 index-work* 1 info-title 1")
  elif name == "view":
    olx.html.ItemState("* 0 tab* 2 tab-view 1 logo1 1 index-view* 1 info-title 1")
  elif name == "tools":
    olx.html.ItemState("* 0 tab* 2 tab-tools 1 logo1 1 index-tools* 1 info-title 1")
  elif name == "info":
    olx.html.ItemState("* 0 tab* 2 tab-info 1 logo1 1 index-info* 1 info-title 1")
  else:
    print "Invalid argument for the panel name: " + name
  return ""

olex.registerFunction(SwitchPanel, False, "gui")


def GetFolderList(root):
  import os
  t = ""
  assert root
  root_c = olex.f(root)
  t = []
  for root, dirs, files in os.walk(root_c, topdown=True):
    pre = root[len(root_c):].replace('\\', '/').lstrip('/')
    for dir in dirs:
      if pre: dir = "%s/%s" %(pre, dir)
      t.append(dir)
  t.sort()
  t = ";".join(t)
  return t

olex.registerFunction(GetFolderList, False, "gui")

#'static' class
class ImageListener_:
  listeners = []
  
  def Register(self, listener):
    ImageListener.listeners.append(listener)
    
  def Unregister(self, listener):
    ImageListener.listeners.remove(listener)
    
  def OnChange(self):
    for i in ImageListener.listeners:
      i()
  
ImageListener = ImageListener_()
