from PilTools import timage
from PilTools import sNumTitle
from PilTools import GuiSkinChanger
from PilTools import MakeAllRBars
from PilTools import BarGenerator
import Image
import ImageDraw, ImageChops, ImageColor
import RoundedCorners


class GuiSkinChanger(GuiSkinChanger):
  def __init__(self, tool_fun=None, tool_arg=None):
    super(GuiSkinChanger, self).__init__()
    self.param = tool_fun

  def setGuiAttributes(self, config):
    colour = self.gui_html_base_colour
    
    for item in config:
      if item.startswith("L_"): continue
      val = config.get(item, "")
      if not val:
        luminosity = config.get("L_%s" %item, "")
        if luminosity:
          val = self.RGBToHTMLColor(self.adjust_colour(colour, luminosity = luminosity))
        else:
          val = "#ff0000"
      setattr(self, item.lower(), val)
      print "self.%s = %s" %(item.lower(), getattr(self, item.lower()))
