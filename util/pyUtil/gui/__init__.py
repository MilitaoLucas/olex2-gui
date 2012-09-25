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

def get_OV_path(path):
  if "()" in path:
    p = getattr(OV, path.split('()')[0])()
    path = "%s/%s" %(p, path.split('()')[1])
  return path


def GetFolderList(root="", format="combo_items"):
  import os
  t = ""
  if not root:
    print "Please provide a root folder!"
    return
  root_c = get_OV_path(root)
  t = []
  i = 0
  for root, dirs, files in os.walk(root_c, topdown=True):
    for dir in dirs:
      s = "%s/%s" %(root.lstrip(root_c), dir)
      s = s.lstrip("\\")
      s = s.lstrip("\\\\")
      s = s.lstrip(r"/")
      t.append("%s" %s)
  t.sort()
  t = ";".join(t)
  return t.replace("\\",'/')

  #names = [x[1] for x in os.walk(root)]
  #paths = [x[0] for x in os.walk(root)]
  #if format == "combo_items":
    #retVal = ""
    #i = 1
    #j = 0
    #l = names[1:]
    #for item in names[0]:

      #path = paths[i]
      #retVal += "%s<-%s;" %(item, item)
      #while l[j]:
        #retVal += "%s/%s<-%s;" %(item, l[j][0],l[j][0])
        #j += 1
      #i += 1
      #j += 1
  #return retVal

olex.registerFunction(GetFolderList, False, "gui")



