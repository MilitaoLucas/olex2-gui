import olex
import olx
import os
import glob
import sys
from olexFunctions import OlexFunctions
OV = OlexFunctions()
from ImageTools import IT

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

def SaveModel():
  fn = FileSave("Please choose the file to save to", "Olex2 model files|*.oxm", olx.FilePath())
  if fn:
    olx.Save("model", fn)

olex.registerFunction(FileOpen, False, "gui.dialog")
olex.registerFunction(FileSave, False, "gui.dialog")
olex.registerFunction(SaveModel, False, "gui.dialog")

def About():
  sz = [int(i) for i in olx.GetWindowSize().split(',')]
  w = int(olx.html.ClientWidth('self'))
  h = int(olx.html.ClientHeight('self'))
  sw = 600+2*15+10
  sh = 400+2*15+150
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


def SwitchTool(name=None):
  #e.g h2-tools-images
  l = name.split("-")
  SwitchPanel(l[1])
  OV.setItemstate("%s 1" %name)
olex.registerFunction(SwitchTool, False, "gui")

def PopTool(name=None):
  #e.g h2-tools-images
  pop_name = name
  wFilePath = os.sep.join([OV.BaseDir(), "etc", name])
  title = name
  olx.Popup(pop_name, wFilePath,
    b="tcr", t=title)
olex.registerFunction(PopTool, False, "gui")

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
  if not retVal:
    return retVal
  if "()" in retVal:
    func = retVal.split("()")[0]
    rest = retVal.split("()")[1]
    res = getattr(OlexFunctions, func)
    retVal = res(OV) + rest
    retVal = OV.standardizePath(retVal)
  return retVal
olex.registerFunction(GetPathParam, False, "gui")

def GetFileList(root, extensions):
  import ntpath
  l = []
  if type(extensions) == unicode:
    extensions = extensions.split(";")
  for extension in extensions:
    extension = extension.strip("'")
    g = glob.glob(r"%s%s*.%s" %(root, os.sep, extension))
    for f in g:
      f = OV.standardizePath(f)
      l.append((ntpath.basename(f),f))
  return l
olex.registerFunction(GetFileList, False, "gui")

def GetFileListAsDropdownItems(root, extensions):
  l = GetFileList(root, extensions)
  txt = ""
  for item in l:
    txt += "%s<-%s;" %(item[0], item[1])
  return txt
olex.registerFunction(GetFileListAsDropdownItems, False, "gui")

def GetDropdownItemsFromList(l):
  txt = ""
  for item in l:
    if len(item) == 1:
      txt += "%s;" %(item)
    elif len(item) == 2:
      txt += "%s<-%s;" %(item[0], item[1])
  return txt
olex.registerFunction(GetDropdownItemsFromList, False, "gui")

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

def GetBoxPosition(w, h):
  sz = [int(x) for x in olx.GetWindowSize().split(',')]
  y = (sz[3]-sz[1]-w)/2
  x = (sz[2]-sz[0]-w)/2
  if x < 0: x = 0
  if y < 0: y = 0
  return x,y

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


def IsMouseLocked(which=None,state=None):
  if not which:
    return

  l = ["translation", "rotation", "zooming"]
  l.remove(which)

  all_locked = True
  for what in l:
    _ = olx.mouse.IsEnabled(what)
    if _ == "true":
      all_locked = False
      break
  if all_locked:
    all_locked = (state=='true')

  if state == "false":
    olx.mouse.Enable(which)
  else:
    olx.mouse.Disable(which)

  return all_locked
olex.registerFunction(IsMouseLocked, False, "gui")


def do_sort():
  args = []
  args.append('+%s%s%s%s' %(OV.GetParam("user.sorting.cat1", ''),
    OV.GetParam("user.sorting.cat2", ''),
    OV.GetParam("user.sorting.cat3", ''),
    OV.GetParam("user.sorting.cat4", '')))
  try:
    if olx.html.GetState('atom_sequence_inplace') == 'true':
      args[0] += 'w'
    elif olx.html.GetState('atom_sequence_first') == 'true':
      args[0] += 'f'
  except:
    pass
  if OV.GetParam("user.sorting.h", False):
    args[0] += 'h'
  args += olx.GetVar("sorting.atom_order", "").split()
  arg3 = OV.GetParam("user.sorting.moiety")
  if arg3 is not None:
    args.append("moiety")
    if arg3 != 'default':
      args.append('+' + arg3)
  args += olx.GetVar("sorting.moiety_order", "").split()
  olx.Sort(*args)
olex.registerFunction(do_sort, False, "gui")


def copytree(src, dst, symlinks=False, ignore=None):
  ## From https://groups.google.com/forum/embed/#!topic/comp.lang.python/8MpGFEhFCm0
  import os
  from shutil import copy2, copystat, Error

  names = os.listdir(src)
  if ignore is not None:
      ignored_names = ignore(src, names)
  else:
      ignored_names = set()

  try:
      os.makedirs(dst)
  except OSError, exc:
      # XXX - this is pretty ugly
      if "file already exists" in exc[1]:  # Windows
          pass
      elif "File exists" in exc[1]:        # Linux
          pass
      else:
          raise

  errors = []
  for name in names:
      if name in ignored_names:
          continue
      srcname = os.path.join(src, name)
      dstname = os.path.join(dst, name)
      try:
          if symlinks and os.path.islink(srcname):
              linkto = os.readlink(srcname)
              os.symlink(linkto, dstname)
          elif os.path.isdir(srcname):
              copytree(srcname, dstname, symlinks, ignore)
          else:
              copy2(srcname, dstname)
          # XXX What about devices, sockets etc.?
      except (IOError, os.error), why:
          errors.append((srcname, dstname, str(why)))
      # catch the Error from the recursive copytree so that we can
      # continue with other files
      except Error, err:
          errors.extend(err.args[0])
  try:
      copystat(src, dst)
  except WindowsError:
      # can't copy file access times on Windows
      pass
  except OSError, why:
      errors.extend((src, dst, str(why)))
  if errors:
      raise Error, errors

def copy_datadir_items(force=False):
  '''
  This will copy the directories containg the shipped samples as well as a directory called 'customisation' to the DataDir(). It will only copy those sub-directories that are NOT present already. When force=True, all directories will be *merged*. Existing files will not be overwritten.
  This function can be called from the command line with spy.gui.copy_datadir_items(TRUE/FALSE) and is called on every startup of Olex2 from InitPy (with FALSE).
  '''
  import shutil

  ignore_patterns = shutil.ignore_patterns('*.svn')

  svn_samples_directory = '%s%ssample_data' %(OV.BaseDir(),os.sep)
  user_samples_directory = OV.GetParam('user.sample_dir')
  if not user_samples_directory:
    user_samples_directory = '%s%ssamples' %(OV.DataDir(),os.sep)
    OV.SetParam('user.sample_dir', user_samples_directory)

  svn_customisation_directory = '%s%setc%scustomisation' %(OV.BaseDir(),os.sep,os.sep)
  user_customisation_directory = OV.GetParam('user.customisation_dir')
  if not user_customisation_directory:
    user_customisation_directory = '%s%scustomisation' %(OV.DataDir(),os.sep)

  dirs = ((svn_samples_directory, user_samples_directory), )

  for src, dest in dirs:
    if not os.path.exists(dest):
      os.makedirs(dest)
      if "sample_data" in src:
        OV.SetVar('sample_dir', dest)
      elif "customisation" in src:
        OV.SetParam('user.customisation_dir',dest)
    else:
      if "sample_data" in src:
        OV.SetVar('sample_dir', dest)
      elif "customisation" in src:
        OV.SetParam('user.customisation_dir',dest)
    things = os.listdir(src)
    for thing in things:
      if thing == '.svn': continue
      try:
        from_f = '%s%s%s' %(src,os.sep,thing)
        to_f = '%s%s%s' %(dest,os.sep,thing)
        if not force and os.path.exists(to_f):
          continue
        copytree(from_f, to_f, ignore=ignore_patterns)
      except Exception, err:
        print err
        pass

olex.registerFunction(copy_datadir_items, False, "gui")


def escape_for_html(s):
  s = s.replace("(", "&#40;")
  s = s.replace(")", "&#41;")
  return s
olex.registerFunction(escape_for_html, False, "gui")
  