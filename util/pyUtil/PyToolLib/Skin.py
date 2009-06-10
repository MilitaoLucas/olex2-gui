from olexFunctions import OlexFunctions
OV = OlexFunctions()
import sys
import olex_gui

class Skin():
  def __init__(self):
    self.change()
    
  def change(self):
    skin = OV.FindValue('gui_skin_name',None)
    skin_extension = OV.FindValue('gui_skin_extension',"None")
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
    
  def run_skin(self, f, args):
    if f == 'timage':
      self.timage_instance.run_timage()
    elif f == 'sNumTitle':
      self.sNumTitle_instance.run_sNumTitle()
    elif f == 'change':
      self.change()
      #self.GuiSkinChanger_instance.run_GuiSkinChanger()
      self.timage_instance.run_timage()
      self.sNumTitle_instance.run_sNumTitle()
    #self.adjust_font_size_for_ppi()
    
  def adjust_font_size_for_ppi(self):
    ppi = olex_gui.GetPPI()[0]
    html_font_size = int(OV.FindValue('gui_html_font_size').strip())
    if ppi > 96:
      OV.SetVar('gui_html_font_size',html_font_size -1)
    else:
      OV.SetVar('gui_html_font_size',html_font_size +2)

Skin_instance = Skin()
OV.registerMacro(Skin_instance.run_skin, 'function-The function to call')
