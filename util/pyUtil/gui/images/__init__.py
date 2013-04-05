import olex

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import inspect, os
curr_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

class GuiImages:

  def __init__(self):
    img_root = OV.GetParam("gui.GuiImages.action", "%s/default/action" %curr_path)
    height = OV.GetParam('gui.html.input_height')
    self.img_d = {
      'root':img_root,
      'width':height,
      'height':height,
      'bg':OV.GetParam('gui.html.table_bg_colour').hexadecimal,
    }

  def make_action_button_html(self):
    link = '''
      <input
        type="button"
        image="up=%(root)s/%(which)s_off.png,down=%(root)s/%(which)s_on.png,hover=%(root)s/%(which)s_hover.png"
        hint="%(hint)s"
        width="%(width)s"
        height="%(height)s"
        onclick="%(onclick)s"
        bgcolor="%(bg)s"
      >''' %self.img_d
    return link
    
  def get_action_button_html(self, which, onclick, hint):
    self.img_d['which'] = which
    self.img_d['onclick'] = onclick
    self.img_d['hint'] = hint
    return self.make_action_button_html()
  
GI = GuiImages()