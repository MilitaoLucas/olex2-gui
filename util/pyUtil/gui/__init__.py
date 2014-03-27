import olex
import olx
import os
import glob
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import htmlTools


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
  olx.Popup("about", olx.BaseDir() + "/etc/gui/help/about.htm",
            x=sz[0] + w/2 + sw/2, y=sz[1] + h/2 - sh/2, w=sw, h=sh)


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
    OV.setItemstate("* 0 tab* 2 tab-home 1 logo1 1 index-home* 1 info-title 1")
    #olx.html.ItemState("index* 0 index-home 1 tab* 2")
  elif name == "work":
    if olx.IsFileLoaded() != "false":
      OV.setItemstate("* 0 tab* 2 tab-work 1 logo1 1 index-work* 1 info-title 1")
  elif name == "view":
    OV.setItemstate("* 0 tab* 2 tab-view 1 logo1 1 index-view* 1 info-title 1")
  elif name == "tools":
    OV.setItemstate("* 0 tab* 2 tab-tools 1 logo1 1 index-tools* 1 info-title 1")
  elif name == "info":
    OV.setItemstate("* 0 tab* 2 tab-info 1 logo1 1 index-info* 1 info-title 1")
  else:
    print "Invalid argument for the panel name: " + name
  return ""

olex.registerFunction(SwitchPanel, False, "gui")

def UpdateWeight():
  w = OV.GetParam('snum.refinement.suggested_weight')
  if not w:
    print "No suggested weighting scheme present. Please refine and try again."
    return ""
  olex.m("UpdateWght %s %s" %(w[0], w[1]))
  print "Weighting scheme has been updated"
olex.registerFunction(UpdateWeight, False, "gui")

def GetPathParam(variable, default=None):
  retVal = OV.GetParam(variable, default)
  if "()" in retVal:
    func = retVal.split("()")[0]
    rest = retVal.split("()")[1]
    res = getattr(OlexFunctions, func)
    retVal = res(OV) + rest
  return retVal
olex.registerFunction(GetPathParam, False, "gui")


def GetFileList(root, extensions):
  l = []
  if type(extensions) == unicode:
    extensions = [extensions]
  for extension in extensions:
    extension = extension.strip("'")
    g = glob.glob(r"%s/*.%s" %(root, extension))
    for f in g:
      f = OV.standardizePath(f)
      name = f.split(".%s"%extension)[0].split("/")[-1]
      l.append((name,f))
  return l
olex.registerFunction(GetFileList, False, "gui")

def GetFileListAsDropdownItems(root, extensions):
  l = GetFileList(root, extensions)
  txt = ""
  for item in l:
    txt += "%s<-%s;" %(item[0], item[1])
  return txt
olex.registerFunction(GetFileListAsDropdownItems, False, "gui")


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


def do_sort():
  args = []
  args.append('+%s%s%s%s' %(OV.GetParam("user.sorting.cat1", ''),
    OV.GetParam("user.sorting.cat2", ''),
    OV.GetParam("user.sorting.cat3", ''),
    OV.GetParam("user.sorting.cat4", '')))
  if olx.html.GetState('atom_sequence_inplace') == 'true':
      args[0] += 'w'
  elif olx.html.GetState('atom_sequence_first') == 'true':
      args[0] += 'f'
  if OV.GetParam("user.sorting.h", False):
    args[0] += 'h'
  args += olx.GetVar("sorting.atom_order", "").split()
  arg3 = OV.GetParam("user.sorting.moiety")
  if arg3:
    args.append("moiety")
    args.append('+' + arg3)
  args += olx.GetVar("sorting.moiety_order", "").split()
  olx.Sort(*args)

olex.registerFunction(do_sort, False, "gui")
