import olex
import olx
import os
import time

from olexFunctions import OlexFunctions
OV = OlexFunctions()

from gui.tools import *


class PluginTools(object):
  def __init__(self):
    pass

  def get_plugin_date(self):
    return time.ctime(os.path.getmtime(self.p_path))

  def print_version_date(self):
    print "Loading %s (Version %s)" %(self.p_name, self.get_plugin_date()),
    
  def deal_with_phil(self, operation='read', which='user_local'):
    user_phil_file = "%s/%s.phil" %(OV.DataDir(),self.p_scope)
    phil_file = r"%s/%s.phil" %(self.p_path, self.p_name)
    if operation == "read":
      phil_file = open(phil_file, 'r')
      phil = phil_file.read()
      phil_file.close()
      
      olx.phil_handler.adopt_phil(phil_string=phil)
      olx.phil_handler.rebuild_index()
      
      if os.path.exists(user_phil_file):
        olx.phil_handler.update(phil_file=user_phil_file)
        
      self.params = getattr(olx.phil_handler.get_python_object(), self.p_scope)
      
    elif operation == "save":
      olx.phil_handler.save_param_file(
        file_name=user_phil_file, scope_name='%s' %self.p_scope, diff_only=False)
      #olx.phil_handler.save_param_file(
        #file_name=user_phil_file, scope_name='snum.%s' %self.p_name, diff_only=True)
      
  def setup_gui(self):
    for image, img_type in self.p_img:
      make_single_gui_image(image, img_type=img_type)
    add_tool_to_index(scope=self.p_name, link=self.p_htm, path=self.p_path, location=self.params.gui.location, before=self.params.gui.before, filetype='')
   