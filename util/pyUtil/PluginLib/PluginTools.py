import olex
import olx
import os
import OlexVFS
import time
import glob
import shutil
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import gui
debug = bool(OV.GetParam("olex2.debug", False))
import HttpTools

class PluginTools(object):
  def __init__(self):
    if olx.HasGUI() == 'true':
      from gui.tools import deal_with_gui_phil
      deal_with_gui_phil('load')
      olx.InstalledPlugins.add(self)

  def endKickstarter(self):
    p = os.sep.join([self.p_path, self.p_htm + ".htm"])
    if OV.HasGUI():
      try:
        t = gui.file_open(p, 'r').read()
        OlexVFS.write_to_olex(p, t)
        olx.html.Update()
      except:
        print("No GUI available")

  def get_plugin_date(self):
    return time.ctime(os.path.getmtime(self.p_path))

  def print_version_date(self):
    print "Loading %s (Version %s)\n" %(self.p_name, self.get_plugin_date()),

  def deal_with_phil(self, operation='read', which='user_local'):
    user_phil_file = "%s/%s.phil" %(OV.DataDir(),self.p_scope)
    phil_file_p = r"%s/%s.phil" %(self.p_path, self.p_scope)
    gui_phil_file_p = r"%s/%s.phil" %(self.p_path, self.p_name.lower())
    if operation == "read":
      phil_file = open(phil_file_p, 'r')
      phil = phil_file.read()
      phil_file.close()

      olx.phil_handler.adopt_phil(phil_string=phil)
      olx.phil_handler.rebuild_index()

      if os.path.exists(gui_phil_file_p):
        gui_phil_file = open(gui_phil_file_p, 'r')
        gui_phil = gui_phil_file.read()
        gui_phil_file.close()

        olx.gui_phil_handler.adopt_phil(phil_string=gui_phil)
        olx.gui_phil_handler.merge_phil(phil_string=gui_phil)
        olx.gui_phil_handler.rebuild_index()
        self.g = getattr(olx.gui_phil_handler.get_python_object(), 'gui')

      if os.path.exists(user_phil_file):
        olx.phil_handler.update(phil_file=user_phil_file)

      self.params = getattr(olx.phil_handler.get_python_object(), self.p_scope)


    elif operation == "save":
      olx.phil_handler.save_param_file(
        file_name=user_phil_file, scope_name='%s' %self.p_scope, diff_only=False)
      #olx.phil_handler.save_param_file(
        #file_name=user_phil_file, scope_name='snum.%s' %self.p_name, diff_only=True)

  def setup_gui(self):
    
    if not hasattr(self, 'p_onclick'):
        self.p_onclick = ""
    if olx.HasGUI() != 'true':
      return
    from gui.tools import make_single_gui_image
    from gui.tools import add_tool_to_index
    import gui.help
    for image, img_type in self.p_img:
      make_single_gui_image(image, img_type=img_type)
    olx.FlushFS()

    if self.p_htm:
      image = self.p_img[0][0]
      try:
        location = self.p_location
        before = self.p_before
      except:
        location = self.params.gui.location
        before = self.params.gui.before
      try:
        add_tool_to_index(scope=self.p_name, link=self.p_htm, path=self.p_path, location=location, before=before, filetype='', image=image, onclick=self.p_onclick)
      except:
        pass
    gui.help.gh.git_help(quick=False, specific=self.p_path)

  def edit_customisation_folder(self,custom_name=None):
    self.get_customisation_path(custom_name=None)
    p = self.customisation_path
    if not p:
      p = self.p_path + "_custom"
      IGNORE_PATTERNS = ('*.pyc', '*.py', '*.git')
      shutil.copytree(self.p_path, p, ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))
      os.rename("%s/templates/default" %p, "%s/templates/custom" %p)
      os.rename("%s/branding/olex2" %p, "%s/branding/custom" %p)
    else:
      if os.path.exists(p):
        print "The location %s already exists. No files have been copied" %p
      else:
        print "This path %s should exist, but does not." %p
        return
    olx.Shell(p)

  def get_customisation_path(self,custom_name=None):
    if custom_name:
      p = self.p_path + custom_name
      if os.path.exists(p):
        self.customisation_path = p
      else:
        self.customisation_path = None
    else: self.customisation_path = None

def make_new_plugin(name,overwrite=False):
  plugin_base = "%s/util/pyUtil/PluginLib/" %OV.BaseDir()
  path = "%s/plugin-%s" %(plugin_base, name)
  xld = "%s/plugins.xld" %OV.BaseDir()

  if os.path.exists(path):
    if overwrite:
      import shutil
      shutil.rmtree(path)
    else:
      print "This plugin already exists."
      return
  if not os.path.exists (path):
    try:
      os.mkdir(path)
    except:
      print "Failed to make folder %s" %path
      return

  d = {'name':name,
       'name_lower':name.lower(),
       'plugin_base':plugin_base,
       }
  template_src = os.sep.join([os.path.dirname(os.path.abspath(__file__)), 'plugin_skeleton.txt'])
  py = gui.tools.TemplateProvider.get_template('plugin_skeleton_py', marker='@-@', path=template_src, force=debug)%d

  wFile = open("%(plugin_base)s/plugin-%(name)s/%(name)s.py"%d,'w')
  wFile.write(py)
  wFile.close()

  phil = gui.tools.TemplateProvider.get_template('plugin_skeleton_phil', marker='@-@', path=template_src, force=debug)%d

  wFile = open("%(plugin_base)s/plugin-%(name)s/%(name_lower)s.phil"%d,'w')
  wFile.write(phil)
  wFile.close()

  html = gui.tools.TemplateProvider.get_template('plugin_skeleton_html', path=template_src, force=debug)%d
  wFile = open("%(plugin_base)s/plugin-%(name)s/%(name_lower)s.htm"%d,'w')
  wFile.write(html)
  wFile.close()

  def_t = gui.tools.TemplateProvider.get_template('plugin_skeleton_def', path=template_src, force=debug)%d

  wFile = open("%(plugin_base)s/plugin-%(name)s/def.txt"%d,'w')
  wFile.write(def_t)
  wFile.close()

  h3_extras = gui.tools.TemplateProvider.get_template('plugin_h3_extras', path=template_src, force=debug)%d

  wFile = open("%(plugin_base)s/plugin-%(name)s/h3-%(name)s-extras.htm"%d,'w')
  wFile.write(h3_extras)
  wFile.close()



  if not os.path.exists(xld):
    wFile = open(xld, 'w')
    t = r'''
<Plugin
  <%(name)s>
>''' %d
    wFile.write(t)
    wFile.close()
    return

  rFile = open(xld, 'r').read().split()
  if name in " ".join(rFile):
    return
  t = ""
  for line in rFile:
    t += "%s\n" %line
    if line.strip() == "<Plugin":
      t += "<%(name)s>\n" %d
  wFile = open(xld, 'w')
  wFile.write(t)
  wFile.close()

  print "New Plugin %s created. Please restart Olex2" %name


OV.registerFunction(make_new_plugin,False,'pt')
