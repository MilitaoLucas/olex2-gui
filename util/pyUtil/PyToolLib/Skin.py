from olexFunctions import OlexFunctions
OV = OlexFunctions()
import sys
import olex_gui
import olx
import olex
import os
import PilTools
from ImageTools import ImageTools
IT = ImageTools()

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import OlexVFS

import time

timing = bool(OV.GetParam('gui.timing'))

class Skin():
  def __init__(self):
    return
    #self.change()

  def change(self):
    skin = OV.GetParam('gui.skin.name')
    skin_extension = OV.GetParam('gui.skin.extension')
    try:
      skin_path = "%s/util/pyUtil/PluginLib/skins/plugin-%sSkin" %(OV.BaseDir(), skin)
      if skin_path not in sys.path:
        sys.path.append("%s/util/pyUtil/PluginLib/skins/plugin-%sSkin" %(OV.BaseDir(), skin))
      PilTools = __import__("PilTools_%s" %skin)
      #print "pyTools -- Using %s skin." %"PilTools_%s: %s" %(skin, tool)
    except ImportError:
      #print "pyTools -- Using Default PilTools for Tool: %s" %tool
      import PilTools
    except Exception, err:
      raise
    self.GuiSkinChanger_instance = PilTools.GuiSkinChanger()
    self.GuiSkinChanger_instance.run_GuiSkinChanger()
    self.timage_instance = PilTools.timage()
    OV.SetVar('olex2_sNum_id_string',"")
    self.sNumTitle_instance = PilTools.sNumTitle()
    #self.adjust_font_size_for_ppi()

  def run_skin(self, f, args=None):
    if timing:
      t = time.time()
    if f == 'timage':
      a = PilTools.timage()
      a.run_timage(force_images=True)
      if timing:
        print "run_skin timage took %.4fs" %(time.time()-t)
    elif f == 'sNumTitle':
      items = {}
      sNum = items.setdefault("sNum", OV.FileName())
      a = PilTools.timage()
      image = a.make_timage('snumtitle', sNum, 'on', titleCase=False)
      name = r"sNumTitle.png"
      OlexVFS.save_image_to_olex(image, name, 1)
      OV.CopyVFSFile(name, 'SNUMTITLE',2)
      if timing:
        print "run_skin sNumTitle took %.4fs" %(time.time()-t)

    elif f == 'change':
      self.change()
      self.timage_instance.run_timage()
      self.sNumTitle_instance.run_sNumTitle(force=True)
      if timing:
        print "run_skin change took %.4fs" %(time.time()-t)

    olx.FlushFS()

  def adjust_font_size_for_ppi(self):
    ppi = olex_gui.GetPPI()[0]
    html_font_size = int(OV.FindValue('gui_html_font_size').strip())
    if ppi > 96:
      OV.SetVar('gui_html_font_size',html_font_size -1)
    else:
      OV.SetVar('gui_html_font_size',html_font_size +2)

Skin_instance = Skin()
OV.registerMacro(Skin_instance.run_skin, 'function-The function to call')

def check_for_first_run():
  if not os.path.exists("%s/global.odb" %OV.DataDir()):
    change_skin('default')
    return True
  return False

def export_parameters(load_phil=True):
  try:
    if load_phil.lower() == "false":
      load_phil = False
  except:
    pass
  if timing:
    t = time.time()
  if check_for_first_run():
    return
  if load_phil:
    deal_with_gui_phil(action='load')
  OV.SetVar('HtmlTableFirstcolColour', OV.GetParam('gui.html.table_firstcol_colour').hexadecimal)
  OV.SetVar('HtmlTableFirstcolWidth', OV.GetParam('gui.html.table_firstcol_width'))
  OV.SetVar('HtmlTableBgColour', OV.GetParam('gui.html.table_bg_colour').hexadecimal)
  OV.SetVar('HtmlInputBgColour', OV.GetParam('gui.html.input_bg_colour').hexadecimal)
  OV.SetVar('HtmlFontColour', OV.GetParam('gui.html.font_colour').hexadecimal)
  OV.SetVar('HtmlComboHeight', OV.GetParam('gui.html.combo_height'))
  OV.SetVar('HtmlComboWidth2', OV.GetParam('gui.html.combo_width_2'))
  OV.SetVar('HtmlInputHeight', OV.GetParam('gui.html.input_height'))
  OV.SetVar('HtmlHighlightColour', OV.GetParam('gui.html.highlight_colour').hexadecimal)
  OV.SetVar('HtmlCheckboxHeight', OV.GetParam('gui.html.checkbox_height'))
  OV.SetVar('HtmlCheckboxWidth', OV.GetParam('gui.html.checkbox_width'))
  OV.SetVar('HtmlCheckboxWidth2', OV.GetParam('gui.html.checkbox_width_2'))
  OV.SetVar('TimageColour', OV.GetParam('gui.timage.grad_colour').hexadecimal)
  OV.SetVar('HtmlSpinHeight', OV.GetParam('gui.html.spin_height'))
  OV.SetVar('HtmlLinkColour', OV.GetParam('gui.html.link_colour').hexadecimal)
  OV.SetVar('HtmlBgColour', OV.GetParam('gui.html.bg_colour').hexadecimal)
  OV.SetVar('HtmlFontName', OV.GetParam('gui.html.font_name'))
  OV.SetVar('HtmlGuiFontSize', OV.GetParam('gui.html.font_size'))
  OV.SetVar('HtmlPanelWidth', OV.GetParam('gui.htmlpanelwidth'))
  OV.SetVar('HtmlButtonHeight', OV.GetParam('gui.timage.button.height'))
  if timing:
    print "export_parameters took %.4fs" %(time.time()-t)
OV.registerFunction(export_parameters,False,'skin')

def deal_with_gui_phil(action='load', skin_name=None, force=False):
  if not skin_name:
    skin_name = OV.GetParam('gui.skin.name')
  if not skin_name:
    skin_name = 'default'
  
  gui_phil_path = "%s/gui.phil" %(OV.DataDir())
  if action == 'load':
    OV.SetHtmlFontSize()
    OV.SetHtmlFontSizeControls()
    skin_extension = None
    if timing:
      t1 = time.time()
      t2 = 0
    else:
      force = True
      olx.gui_phil_handler.reset_scope('gui')
      if len(skin_name.split("_")) > 1:
        skin_extension = skin_name.split("_")[1]
        skin_name = skin_name.split("_")[0]
  
    gui_skin_phil_path = "%s/etc/skins/%s.phil" %(OV.BaseDir(), skin_name)
    if os.path.isfile(gui_skin_phil_path):
      gui_skin_phil_file = open(gui_skin_phil_path, 'r')
      gui_skin_phil = gui_skin_phil_file.read()
      gui_skin_phil_file.close()
      olx.gui_phil_handler.update(phil_string=gui_skin_phil)
  
    if skin_extension:
      force = True
      gui_skin_phil_path = "%s/etc/skins/%s.phil" %(OV.BaseDir(), skin_extension)
      if os.path.isfile(gui_skin_phil_path):
        gui_skin_phil_file = open(gui_skin_phil_path, 'r')
        gui_skin_phil = gui_skin_phil_file.read()
        gui_skin_phil_file.close()
        olx.gui_phil_handler.update(phil_string=gui_skin_phil)
  
    if timing:
      t = time.time()
      print "After 'Reading PHIL Stuff': %.2f s (%.2f s)" % ((t - t1), (t - t1))
      t2 = t
  else:
    olx.gui_phil_handler.save_param_file(
      file_name=gui_phil_path, scope_name='gui', diff_only=True)


def change_skin(skin_name=None, force=False):
  
  olx.fs.Clear(2)
  
  if timing:
    t1 = time.time()
    t2 = 0

  deal_with_gui_phil(action='load', skin_name=skin_name, force=False)
  try:
    adjust_skin_luminosity()
  except:
    pass

  if timing:
    t = time.time()
    print "After 'adjust_skin_luminosity': %.2f s (%.5f s)" % ((t - t1), (t - t2))
    t2 = t

  width = OV.GetParam('gui.htmlpanelwidth')

  IT.resize_skin_logo(width)
  IT.resize_news_image()
  if timing:
    t = time.time()
    print "After 'resize_skin_logo': %.2f s (%.5f s)" % ((t - t1), (t - t2))
    t2 = t

  a = PilTools.timage()
  a.run_timage(force_images=force)

  if timing:
    t = time.time()
    print "After 'run_timage': %.2f s (%.5f s)" % ((t - t1), (t - t2))
    t2 = t

  if timing:
    t = time.time()
    print "After 'sNumTitle': %.2f s (%.5f s)" % ((t - t1), (t - t2))
    t2 = t

  SetGrad()
  SetMaterials()

  OV.setAllMainToolbarTabButtons()

  #if OV.FileFull() != "none":
    #import History
    #from History import hist
    #try:
      #hist._make_history_bars()
    #except:
      #pass
      
  a = PilTools.sNumTitle()
  a.run_sNumTitle(force=True)
  olx.FlushFS()

  olex.m('htmlpanelwidth %s' %width)
  olex.m('htmlpanelswap %s' %OV.GetParam('gui.htmlpanel_side'))

  if timing:
    t = time.time()
    print "After 'Reload': %.2f s (%.5f s)" % ((t - t1), (t - t2))
    t2 = t

    deal_with_gui_phil(action='save', skin_name=skin_name, force=False)

  if timing:
    t = time.time()
    print "After 'Save PHIL': %.2f s (%.5f s)" % ((t - t1), (t - t2))
    t2 = t

  export_parameters()
  
OV.registerFunction(change_skin)


def adjust_skin_colours():
  base_colour = OV.GetParam('gui.html.base_colour')
  item = ['tab', 'timage', 'snumtitle']
  for tem in item:
    if not OV.GetParam('gui.%s.base_colour' %tem) :
      OV.SetParam('gui.%s.base_colour' %tem, base_colour)

  if OV.GetParam('gui.snumtitle.filefullinfo_colour') is None:
    OV.SetParam('gui.snumtitle.filefullinfo_colour', IT.adjust_colour(base_colour.rgb, luminosity = OV.GetParam('gui.snumtitle.filefullinfo_colour_L')))

def adjust_skin_luminosity():
  base_colour = OV.GetParam('gui.base_colour')

  scope_l= ['gui',
            'gui.timage',
            'gui.timage.button',
            'gui.timage.h1',
            'gui.timage.h3',
            'gui.timage.tab',
            'gui.timage.cbtn',
            'gui.timage.snumtitle']

  for scope in scope_l:
    gui = olx.gui_phil_handler.get_scope_by_name(scope)
    for object in gui.active_objects():
      if object.is_scope:
        continue
      try:
        data_type = object.type.phil_type
        if data_type == 'colour':
          name = object.name
          if object.extract() is None:
            name = object.name
            if "base_colour" in name:
              OV.SetParam('%s.%s' %(scope,name), base_colour)
            else:
              OV.SetParam('%s.%s' %(scope,name), IT.adjust_colour(base_colour.rgb, luminosity = OV.GetParam('%s.%s_L' %(scope,name))))
          #print "%s.%s: %s" %(scope, name, OV.GetParam('%s.%s' %(scope,name)))
      except Exception, ex:
        print ex
        pass
        #print "Something has gone wrong with SKIN adjust_skin_luminosity: %s" %ex

def SetGrad():
  from ImageTools import ImageTools
  IT = ImageTools()
  l = ['top_right', 'top_left', 'bottom_right', 'bottom_left']
  v = []
  for i in xrange(4):
    val = OV.GetParam('gui.grad_%s' %(l[i])).hexadecimal
    if not val:
      val = "#ffffff"
    val = IT.hex2dec(val)
    v.append(val)
  olx.Grad("%i %i %i %i" %(v[0], v[1], v[2], v[3]))

def SetMaterials():
  if OV.GetParam('gui.skin.materials_have_been_set'):
    return
  olx.SetMaterial("InfoBox.Text %s" %OV.GetParam('gui.infobox_text'))
  olx.SetMaterial("InfoBox.Plane %s" %OV.GetParam('gui.infobox_plane'))
  olx.SetMaterial("Console.Text %s" %OV.GetParam('gui.infobox_text'))
  olx.SetMaterial("XGrid.+Surface %s" %OV.GetParam('gui.xgrid.positive_surface_material'))
  olx.SetMaterial("XGrid.-Surface %s" %OV.GetParam('gui.xgrid.negative_surface_material'))
  olex.m("gl.lm.ClearColor(%s)" %OV.GetParam('gui.skin.clearcolor'))
  olex.m("SetFont Default %s" %OV.GetParam('gui.console_font'))
  olex.m("SetFont Labels %s" %OV.GetParam('gui.labels_font'))
  olx.HtmlPanelWidth(OV.GetParam('gui.htmlpanelwidth'))

  olex.m("lines %s" %OV.GetParam('gui.lines_of_cmd_text'))

  OV.SetParam('gui.skin.materials_have_been_set', True)

def load_user_gui_phil():
  gui_phil_path = "%s/gui.phil" %(OV.DataDir())
  if os.path.exists(gui_phil_path):
    gui_phil_file = open(gui_phil_path, 'r')
    gui_phil = gui_phil_file.read()
    gui_phil_file.close()
    olx.gui_phil_handler.update(phil_string=gui_phil)

OV.registerFunction(load_user_gui_phil)