import olex
import olx
import os
import time
import glob
import shutil
from olexFunctions import OlexFunctions
OV = OlexFunctions()

import HttpTools

class PluginTools(object):
  def __init__(self):
    if olx.HasGUI() == 'true':
      from gui.tools import deal_with_gui_phil
      deal_with_gui_phil('load')

  def get_plugin_date(self):
    return time.ctime(os.path.getmtime(self.p_path))

  def print_version_date(self):
    print "Loading %s (Version %s)" %(self.p_name, self.get_plugin_date()),

  def deal_with_phil(self, operation='read', which='user_local'):
    user_phil_file = "%s/%s.phil" %(OV.DataDir(),self.p_scope)
    phil_file_p = r"%s/%s.phil" %(self.p_path, self.p_scope)
    gui_phil_file_p = r"%s/gui_%s.phil" %(self.p_path, self.p_name.lower())
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
    if olx.HasGUI() != 'true':
      return
    from gui.tools import make_single_gui_image
    from gui.tools import add_tool_to_index

    for image, img_type in self.p_img:
      make_single_gui_image(image, img_type=img_type)
    olx.FlushFS()

    if self.p_htm:
      add_tool_to_index(scope=self.p_name, link=self.p_htm, path=self.p_path, location=self.params.gui.location, before=self.params.gui.before, filetype='')

  def edit_customisation_folder(self):
    self.get_customisation_path()
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

  def get_customisation_path(self):
    p = self.p_path + "_custom"
    if os.path.exists(p):
      self.customisation_path = p
    else:
      self.customisation_path = None


def make_new_plugin(name,overwrite=False):
  plugin_base = "%s/util/pyUtil/pluginLib/" %OV.BaseDir()
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

  py = '''
from olexFunctions import OlexFunctions
OV = OlexFunctions()

import os
import htmlTools
import olex
import olx

instance_path = OV.DataDir()

p_path = os.path.dirname(os.path.abspath(__file__))

l = open(os.sep.join([p_path, 'def.txt'])).readlines()
d = {}
for line in l:
  line = line.strip()
  if not line or line.startswith("#"):
    continue
  d[line.split("=")[0].strip()] = line.split("=")[1].strip()

p_name = d['p_name']
p_htm = d['p_htm']
p_img = eval(d['p_img'])
p_scope = d['p_scope']

OV.SetVar('%(name)s_plugin_path', p_path)

from PluginTools import PluginTools as PT

class %(name)s(PT):

  def __init__(self):
    super(%(name)s, self).__init__()
    self.p_name = p_name
    self.p_path = p_path
    self.p_scope = p_scope
    self.p_htm = p_htm
    self.p_img = p_img
    self.deal_with_phil(operation='read')
    self.print_version_date()
    self.setup_gui()
    OV.registerFunction(self.print_formula,True,"%(name)s")

  def print_formula(self):
    formula = {}
    for element in str(olx.xf.GetFormula('list')).split(','):
      element_type, n = element.split(':')
      print "%%s: %%s" %%(element_type, n)
      formula.setdefault(element_type, float(n))

%(name)s_instance = %(name)s()
print "OK."''' %d

  wFile = open("%(plugin_base)s/plugin-%(name)s/%(name)s.py"%d,'w')
  wFile.write(py)
  wFile.close()

  phil = '''
%(name_lower)s{
  gui{
    location = 'tools'
      .type = str
      .help = The tab item where the %(name)s GUI shall appear.
    before = 'images'
      .type = str
      .help = The tool before which the %(name)s GUI shall appear.
    }
}
''' %d
  wFile = open("%(plugin_base)s/plugin-%(name)s/%(name_lower)s.phil"%d,'w')
  wFile.write(phil)
  wFile.close()


  html = r'''
<!-- #include tool-top gui/blocks/tool-top.htm;image=#image;onclick=#onclick;1; -->
<!-- #include tool-row-help gui/blocks/tool-row-help.htm;name=%(name)s_1; help_ext=%(name)s_1;1; -->
  <td ALIGN='left' width='100%%'>
    <b>Welcome to your new Plugin: %(name)s</b>
  </td>
<!-- #include row_table_off gui/blocks/row_table_off.htm;1; -->

<!-- #include tool-row-help gui/blocks/tool-row-help.htm;name=%(name)s_2; help_ext=%(name)s_2;1; -->
  <td ALIGN='left' width='100%%'>
    <b><a href="spy.%(name)s.print_formula()">RUN</a>
  </td>
<!-- #include row_table_off gui/blocks/row_table_off.htm;1; -->

<!-- #include tool-footer gui/blocks/tool-footer.htm;colspan=2;1; -->
  ''' %d
  wFile = open("%(plugin_base)s/plugin-%(name)s/%(name_lower)s.htm"%d,'w')
  wFile.write(html)
  wFile.close()

  def_t = r'''
  p_name = %(name)s
  p_htm = %(name)s
  p_img = [("%(name)s",'h1')]
  p_scope = %(name_lower)s'''%d

  wFile = open("%(plugin_base)s/plugin-%(name)s/def.txt"%d,'w')
  wFile.write(def_t)
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
