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
    import olex
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
    #olex.m("grad true -p='%s/util/pyUtil/PluginLib/skins/plugin-ODSkin/ODstartup.png'" %self.basedir)

  def setGuiProperties(self):
    import olex
    olex.m("SetMaterial InfoBox.Text %s" %self.gui_infobox_text)
    olex.m("SetMaterial InfoBox.Plane %s" %self.gui_infobox_plane)
    olex.m("htmguifontsize %s" %self.gui_html_font_size)
    olex.m("grad True")
  
class sNumTitle(sNumTitle):
  def __init__(self, width=290, tool_arg=None):
    super(sNumTitle, self).__init__(width=290, tool_arg=None)
    #setGuiColours(self)
    #setGuiAttributes(self)
    #self.setVariables('gui')

  def sNumTitleStyle1(self, items, font_name="Arial Bold", font_size=20):
    width = self.width
    height = 26
    self.height = height
    gap = 0
    bgap = height - gap
    size = (int(width), int(height))
    base = self.gui_base_colour
    base = self.gui_snumtitle_colour
    image = Image.new('RGBA', size, base)
    draw = ImageDraw.Draw(image)
    border_rad=0
    self.make_border(rad=border_rad,
                     draw=draw,
                     width=width,
                     height=height,
                     bg_colour=base,
                     border_colour=base,
                     border_hls = (0, 0.7, 1)
                   )

    sNum = items["sNum"]
    if sNum == "none": sNum = "No Structure"
    self.write_text_to_draw(draw, 
                            sNum, 
                            top_left=(6, 1), 
                            font_name=font_name, 
                            font_size=font_size, 
                            font_colour=self.gui_snumtitle_font_colour)
    self.drawFileFullInfo(draw, luminosity=0.6, right_margin=3, bottom_margin=0)
    self.drawSpaceGroupInfo(draw, luminosity=0.4, right_margin=3)
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour(self.gui_html_bg_colour, luminosity = 0.95))
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour(self.gui_html_bg_colour, luminosity = 0.98))
    image = self.add_whitespace(image=image, side='right', weight=1, colour = self.adjust_colour(self.gui_html_bg_colour, luminosity = 0.98))

    #dup = ImageChops.duplicate(image)
    #dup = ImageChops.invert(dup)
    #dup = ImageChops.offset(dup, 1, 1)
    #image = ImageChops.blend(image, dup, 0.05)
    return image


class timage(timage):

  def __init__(self, width=290, tool_arg=None):
    super(timage, self).__init__(width=290, tool_arg=None)
    #setGuiColours(self)

  def timage_style_1(self, item, state, font_name="Vera"):
    width = self.width + 2
    height = 18
    base = self.gui_timage_colour
    bg_colour = self.adjust_colour("base", luminosity = 1.3)
    bg_colour = base
    size = (int(width), int(height))
    image = Image.new('RGB', size, (0,0,0))
    draw = ImageDraw.Draw(image)
    t = item.split("-")
    txt = ""
    for bit in t:
      txt += "%s " %bit
    grad_colour = "#dedede"
    grad_colour = base
    self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=0.5)
    if state == "off":
      self.create_arrows(draw, height, 'right', self.adjust_colour("base", luminosity = 0.8), type='simple', h_space=4, v_space=4)

    else:
      self.create_arrows(draw, height, 'up', self.gui_html_highlight_colour, type='simple', h_space=4, v_space=4)

    transtest = False
    if transtest:
      image = self.makeTransparentText(image, txt, font_colour=self.adjust_colour("base", luminosity = 0.7))
    else:
      self.write_text_to_draw(
        draw, 
        txt, 
        top_left=(16,1), 
        font_name=font_name, 
        font_size=13, 
        titleCase=True,
        font_colour=self.gui_timage_font_colour)
      cache = {}
      pos = (('Rounded'),('Rounded'),('Rounded'),('Rounded'))
      image = RoundedCorners.round_image(image, cache, 3, pos=pos)

      #self.make_border(rad=8,
          #draw=draw,
          #width=width,
          #height=height,
          #bg_colour=bg_colour,
          #border_colour=bg_colour,
          #border_hls = (0, 0.8, 1),
          #cBottomLeft=False,
          #cBottomRight=False,
          #cTopLeft=False,
          #cTopRight=False
          #)

    filename = item
    image = self.add_whitespace(image=image, side='top', weight=1, colour = self.adjust_colour("bg", luminosity = 0.95))
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.95),)
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.98),)
    image = self.add_whitespace(image=image, side='right', weight=1, colour = self.adjust_colour("bg", luminosity = 0.95), )
    return image
  
  def timage_style_h3(self, item, state, bg_luminosity=0.8, bg_saturation=0.9, luminosity_font=1.7, font_name = "Vera"):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
    width = self.width - 8
    height = 16
    base = self.gui_timage_colour
    bg_colour = self.adjust_colour("base", luminosity=bg_luminosity, saturation=bg_saturation)
    size = (int(width), int(height))
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    grad_colour = self.adjust_colour(base, luminosity = 1.00)
    self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=0.3)

    t = item.split("-")
    txt = ""
    for bit in t:
      txt += bit.title() + " "

    self.write_text_to_draw(draw, 
                       txt, 
                       top_left=(13,0), 
                       font_name=font_name, 
                       font_size=10, 
                       font_colour=self.gui_timage_font_colour,
                       image_size = image.size,
                       titleCase=True,
                       valign = ("middle", 0.7)
                     )

    cache = {}
    rad = 1
    image = RoundedCorners.round_image(image, cache, rad)

    if state == "off":
      fill=self.adjust_colour(base, luminosity=0.8)
      self.create_arrows(draw, height, direction="right", colour=fill, type='simple')
    else:
      fill = self.gui_html_highlight_colour
      self.create_arrows(draw, height, direction="up", colour=fill, type='simple')
      
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.9))
    filename = item
    return image

  #def timage_style_h3(self, item, state, bg_luminosity=1.2, bg_saturation=0.9, luminosity_font=0.6, font_name="Arial"):
    #width = self.width - 8
    #height = 15
    #base = self.gui_timage_colour
    #bg_colour = self.adjust_colour("base", luminosity=bg_luminosity, saturation=bg_saturation)
    #size = (int(width), int(height))
    #image = Image.new('RGBA', size, bg_colour)
    #draw = ImageDraw.Draw(image)
    #t = item.split("-")
    #txt = ""
    #for bit in t:
      #txt += "%s " %bit

    #self.write_text_to_draw(draw, 
                            #txt, 
                            #top_left=(12,1), 
                            #font_name=font_name, 
                            #font_size=10, 
                            #font_colour=self.adjust_colour("base", luminosity=luminosity_font, hue=0))

    #self.make_border(rad=11,
                     #draw=draw,
                     #width=width,
                     #height=height,
                     #bg_colour=bg_colour,
                     #border_colour=bg_colour,
                     #border_hls = (0, 0.85, 1),
                     #shift = 0,
                     #cBottomLeft=False,
                     #cBottomRight=False,
                     #cTopLeft=False,
                     #cTopRight=False
                   #)

    #if state == "off":
      #fill=self.adjust_colour("bg", luminosity=0.8)
      #self.create_arrows(draw, height, direction="right", colour=fill, type='simple')
    #else:
      #fill = self.adjust_colour("highlight",  luminosity = 1.1)
      #self.create_arrows(draw, height, direction="up", colour=fill, type='simple')

    ##image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.9))
    #filename = item
    #return image


  def tab_items(self, item, state, font_name = "Vera Bold", font_size=13):
    width = int((self.width)/len(self.tabItems)-2)
    height = 19
    #base = self.adjust_colour("base",luminosity = 1.2, saturation = 1.2)
    #base = "#4A63DE"
    #base = (75, 100, 220)
    #base = (100, 120, 210)
    base = self.gui_tab_colour
    #font_colour = base
    size = (int(width), int(height))
    image = Image.new('RGBA', size, base)
    draw = ImageDraw.Draw(image)

    grad_colour = base
    self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=0.6)

    begin = (2, 7)
    middle = (2, 2)
    end = (7, 2)

    if state == "off":
      #triangle left-off
      font_colour = self.adjust_colour("base", luminosity = 1.9, saturation = 1.2)
      draw.polygon((begin, middle, end), self.adjust_colour(base, luminosity = 1.2))
    if state != "off":
      #triangle left-on
      draw.polygon((begin, middle, end), fill=(255, 80, 0))
      font_colour = self.adjust_colour("highlight")
    cache = {}
    pos = (('Square'),('Rounded'),('Square'),('Square'))
    image = RoundedCorners.round_image(image, cache, 8, pos=pos)
    #self.make_border(rad=15,
          #draw=draw,
          #width=width,
          #height=height,
          #bg_colour=base,
          #shift = 0,
          #border_colour=base,
          #border_hls=(0, 1.2, 1),
          #cBottomLeft=False,
          #cBottomRight=False,
          #cTopLeft=False,
        #)
    txt = item.replace("index-", "")

    #right_align_position = (width - int(width * 0.05) - draw.textsize(txt, font=font)[0])

    self.write_text_to_draw(draw, 
                            txt, 
                            align = "right",
                            max_width = width-5,
                            top_left=(6,1), 
                            font_name=font_name, 
                            font_size=font_size, 
                            font_colour=font_colour)

    #dup = ImageChops.duplicate(image)
    #dup = ImageChops.invert(dup)
    #dup = ImageChops.offset(dup, 1, 1)
    #image = ImageChops.blend(image, dup, 0.05)
    image = self.add_whitespace(image=image, side='top', weight=1,  margin_right=8, colour=self.adjust_colour(self.gui_html_bg_colour, luminosity=0.95))
    image = self.add_whitespace(image=image, side='right', weight=1, colour=self.adjust_colour(self.gui_html_bg_colour, luminosity=1.0))
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour=self.adjust_colour(self.gui_html_bg_colour, luminosity=0.90))
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour=self.adjust_colour(self.gui_html_bg_colour, luminosity=0.95))
    filename = item
    return image