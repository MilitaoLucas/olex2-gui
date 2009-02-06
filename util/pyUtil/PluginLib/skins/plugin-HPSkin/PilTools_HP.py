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
    #self.setGuiAttributes()

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
      

  def setGuiProperties(self):
    import olex
    olex.m("SetMaterial InfoBox.Text %s" %self.gui_infobox_text)
    olex.m("SetMaterial InfoBox.Plane %s" %self.gui_infobox_plane)
    olex.m("SetMaterial execout 2305;0.000,0.000,0.502,1.000") 
    olex.m("htmguifontsize %s" %self.gui_html_font_size)
    
  
class sNumTitle(sNumTitle):
  def __init__(self, width=290, tool_arg=None):
    super(sNumTitle, self).__init__(width=290, tool_arg=None)
    #self.gui_image_font_name = OV.FindValue('gui_image_font_name')

  def sNumTitleStyle1(self, items, font_name="Courier Bold", font_size=21):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
      font_name = "%s Bold" %font_name
    width = self.width
    height = 26
    self.height = height
    gap = 0
    bgap = height - gap
    size = (int(width), int(height))
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
    #image = self.add_whitespace(image=image, side='right', weight=1, colour = self.adjust_colour(self.gui_html_bg_colour, luminosity = 0.98))

    #dup = ImageChops.duplicate(image)
    #dup = ImageChops.invert(dup)
    #dup = ImageChops.offset(dup, 1, 1)
    #image = ImageChops.blend(image, dup, 0.05)
    return image



class timage(timage):

  def __init__(self, width=290, tool_arg=None):
    super(timage, self).__init__(width=290, tool_arg=None)
    self.beginning_block_weight = 5
    #self.gui_image_font_name = OV.FindValue('gui_image_font_name')

    #setGuiColours(self)
    
  def make_cbtn_items(self, font_name = 'Courier'):
    from PilTools import ButtonMaker
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
      font_name = "%s Bold" %font_name
    
    settings_button_width = 0
    cbtn_buttons_height = 18
    
    all_cbtn_buttons = {
        'image_prefix':'cbtn',
        'height':cbtn_buttons_height,
        'font_size':12,
        'font_name':font_name,
        'bgcolour':self.gui_html_bg_colour,
        
        'fontcolouroff':self.gui_html_font_colour,
        'bgcolouroff':self.gui_html_bg_colour,
        
        'fontcolouron':self.gui_html_highlight_colour,
        'bgcolouron':self.gui_html_bg_colour,
        
        'fontcolourinactive':self.adjust_colour(self.gui_html_bg_colour, luminosity = 0.9),
        'bgcolourinactive':self.gui_html_bg_colour,

        'states':['','on', 'off', 'inactive'],
        'grad_colour':(237,237,245),
        'vline':{'v_pos':0, 'height':18},
        'grad':False,
        'valign':("middle", 0.7),
        'top_left':(3,2),
        'align':'center',
        'titleCase':False,
        'lowerCase':True,
        'continue_mark':True,
        'whitespace_bottom':{'weight':1, 'colour':self.gui_html_bg_colour},
      }
    
    buttonItems = {
      "cbtn-refine":
      {
        'txt':'refine',
        'name':'refine',
        'width':('auto', (3,settings_button_width), 0),
#        'whitespace_right':{'weight':1, 'colour':'#ff0000'},
        'whitespace_right':{'weight':1, 'colour':self.gui_html_bg_colour},
        },
      "cbtn-solve":
      {
        'txt':'solve',
        'name':'solve',
        'width':('auto', (3,settings_button_width), 0),
#        'whitespace_right':{'weight':1, 'colour':'#ff0000'},
        'whitespace_right':{'weight':1, 'colour':self.gui_html_bg_colour},
        }, 
      "cbtn-report":
      {
        'txt':'report',
        'name':'report',
        'width':('auto', (3,settings_button_width), 0),
        'whitespace_right':False,
      },
    }
    
    for d in buttonItems:
      buttonItems[d].update(all_cbtn_buttons)

    BM = ButtonMaker(buttonItems)
    im = BM.run()
    
    

  def timage_style_1(self, item, state, font_name="Vera"):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
      font_name = "%s" %font_name
    width = self.width + 2 - self.beginning_block_weight
    height = 17
    base = self.gui_timage_colour
    bg_colour = self.adjust_colour("base", luminosity = 0.95)
    size = (int(width), int(height))
    #image = Image.new('RGB', size, (0,0,0))
    image = Image.new('RGB', size, bg_colour)
    draw = ImageDraw.Draw(image)
    t = item.split("-")
    txt = ""
    for bit in t:
      txt += "%s " %bit
## GRADIENT      
#    grad_colour = "#dedede"
#    self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=0.5)


    transtest = False
    if transtest:
      image = self.makeTransparentText(image, txt, font_colour=self.adjust_colour("base", luminosity = 0.7))
    else:
      self.write_text_to_draw(
        draw, 
        txt, 
        top_left=(4,1), 
        font_name=font_name, 
        font_size=11, 
        titleCase=True,
        font_colour=self.gui_timage_font_colour)
      cache = {}
#      pos = (('Rounded'),('Rounded'),('Rounded'),('Rounded'))
#      image = RoundedCorners.round_image(image, cache, 3, pos=pos)

## ARROWS      
    if state == "off":
      self.create_arrows(draw, height, direction='down',
                         colour=self.adjust_colour("base", luminosity = 0.6),
                         type='char',
                         char_pos=(width-14,0), char_char="+", h_space=4, v_space=4)
      image = self.add_whitespace(image=image, side='left', weight=self.beginning_block_weight, colour = self.adjust_colour("base", luminosity = 0.8))
    else:
      self.create_arrows(draw, height, direction='up',
                         colour=self.adjust_colour("base", luminosity = 0.6),
                         type='char',
                         char_pos=(width-14,0), char_char="~", h_space=4, v_space=4)
      image = self.add_whitespace(image=image, side='left', weight=self.beginning_block_weight, colour = self.gui_html_highlight_colour)
      
      
      #self.make_border(rad=8,
          #draw=draw,
          #width=width,
          #height=height,
          #bg_colour=bg_colour,
          #border_colour=self.adjust_colour(self.gui_timage_colour, luminosity = 0.9),
          #border_hls = (0, 0.8, 1),
          #cBottomLeft=False,
          #cBottomRight=False,
          #cTopLeft=False,
          #cTopRight=False
          #)

    filename = item
#    image = self.add_whitespace(image=image, side='top', weight=1, colour = self.adjust_colour("bg", luminosity = 0.95))
#    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.95),)
#    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.98),)
#    image = self.add_whitespace(image=image, side='right', weight=1, colour = self.adjust_colour("bg", luminosity = 0.95), )
#    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.gui_html_table_bg_colour)
    return image
  
  def timage_style_h3(self, item, state, bg_luminosity=0.9, bg_saturation=1.0, luminosity_font=0.5, font_name = "Vera"):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
    width = self.width - 8 - 2
    height = 14
    base = self.gui_timage_colour
    base = self.gui_timage_colour
    bg_colour = self.adjust_colour("base", luminosity=bg_luminosity, saturation=bg_saturation)
    size = (int(width), int(height))
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    #grad_colour = self.adjust_colour(base, luminosity = 1.05)
    #self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=0.3)

    t = item.split("-")
    txt = ""
    for bit in t:
      txt += bit.title() + " "

    self.write_text_to_draw(draw, 
                       txt, 
                       top_left=(5,1), 
                       font_name=font_name, 
                       font_size=10, 
                       font_colour=self.gui_timage_font_colour,
                       image_size = image.size,
                       titleCase=True,
                       valign = ("middle", 0.75)
                     )

    cache = {}
    #rad = 1
    #image = RoundedCorners.round_image(image, cache, rad)

## ARROWS      
    if state == "off":
      self.create_arrows(draw, height, direction='down',
                         colour=self.adjust_colour("base", luminosity = 0.6),
                         type='char',
                         char_pos=(width-14,0), char_char="+", h_space=4, v_space=4)
      image = self.add_whitespace(image=image, side='left', weight=3, colour = self.adjust_colour("base", luminosity = 0.8))
    else:
      self.create_arrows(draw, height, direction='up',
                         colour=self.adjust_colour("base", luminosity = 0.6),
                         type='char',
                         char_pos=(width-14,0), char_char="~", h_space=4, v_space=4)
      image = self.add_whitespace(image=image, side='left', weight=3, colour = self.gui_html_highlight_colour)
    
    
    #if state == "off":
      #fill=self.adjust_colour("bg", luminosity=0.8)
      #self.create_arrows(draw, height, direction="right", colour=fill, type='simple')
    #else:
      #fill = self.adjust_colour("highlight",  luminosity = 1.1)
      #self.create_arrows(draw, height, direction="up", colour=fill, type='simple')
      
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

    self.make_border(rad=11,
                     draw=draw,
                     width=width,
                     height=height,
                     bg_colour=bg_colour,
                     border_colour=bg_colour,
                     border_hls = (0, 0.85, 1),
                     shift = 0,
                     cBottomLeft=False,
                     cBottomRight=False,
                     cTopLeft=False,
                     cTopRight=False
                   )

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
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
      font_name = "%s Bold" %font_name

    width = int((self.width)/len(self.tabItems)-2)
    height = 17
    base = self.adjust_colour("base",luminosity = 0.7, saturation = 1.2)
    size = (int(width), int(height))
    image = Image.new('RGBA', size, base)
    draw = ImageDraw.Draw(image)

#    grad_colour = base
#    self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=0.6)

    begin = (2, 7)
    middle = (2, 2)
    end = (7, 2)

    
## ARROWS      
    #if state == "off":
      #self.create_arrows(draw, height, direction='down',
                         #colour=self.adjust_colour("base", luminosity = 0.6),
                         #type='char',
                         #char_pos=(width-14,0), char_char="+", h_space=4, v_space=4)
      #image = self.add_whitespace(image=image, side='left', weight=3, colour = self.adjust_colour("base", luminosity = 0.8))
      #font_colour = self.adjust_colour("base", luminosity = 0.9, saturation = 1.2)
    #else:
      #font_colour = self.adjust_colour("highlight")
      #self.create_arrows(draw, height, direction='up',
                         #colour=self.gui_html_highlight_colour,
                         #type='char',
                         #char_pos=(width-14,0), char_char="~", h_space=4, v_space=4)
      #image = self.add_whitespace(image=image, side='left', weight=3, colour = self.gui_html_highlight_colour)
    
    
    
    #cache = {}
#    pos = (('Square'),('Rounded'),('Square'),('Square'))
#    image = RoundedCorners.round_image(image, cache, 8, pos=pos)
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

    if state == "off":
      font_colour = self.adjust_colour(self.gui_tab_font_colour, luminosity = 0.9, saturation = 1)
    if state != "off":
      font_colour = self.adjust_colour(self.gui_tab_font_colour, luminosity = 1.1, saturation = 1)
    
    self.write_text_to_draw(draw, 
                            txt, 
                            align = "right",
                            max_width = width-5,
                            top_left=(6,1), 
                            font_name=font_name, 
                            font_size=font_size, 
                            font_colour=font_colour)

    if state == "off":
      #triangle left-off
      #self.make_border(rad=0,draw=draw,width=width,height=height,bg_colour=base,shift = 0,
            #border_colour=base,
            #border_hls=(0, 1.2, 1),
            #cBottomLeft=False,
            #cBottomRight=False,
            #cTopLeft=False,
          #)
      image = self.add_whitespace(image=image, side='bottom', weight=3, colour = self.adjust_colour("base", luminosity = 0.8))

#      draw.polygon((begin, middle, end), self.adjust_colour(base, luminosity = 1.2))
    if state != "off":
      #triangle left-on
#      draw.polygon((begin, middle, end), fill=(255, 80, 0))
      #self.make_border(rad=0,draw=draw,width=width,height=height,bg_colour=base,shift = 0,
            #border_colour=self.gui_html_highlight_colour,
            #border_hls=(0, 1.2, 1),
            #cBottomLeft=False,
            #cBottomRight=False,
            #cTopLeft=False,
          #)
      image = self.add_whitespace(image=image, side='bottom', weight=3, colour = self.gui_html_highlight_colour)
    #dup = ImageChops.duplicate(image)
    #dup = ImageChops.invert(dup)
    #dup = ImageChops.offset(dup, 1, 1)
    #image = ImageChops.blend(image, dup, 0.05)
    #image = self.add_whitespace(image=image, side='top', weight=1,  margin_right=8, colour=self.adjust_colour(self.gui_html_bg_colour, luminosity=0.95))
    if 'info' not in txt:
      image = self.add_whitespace(image=image, side='right', weight=2, colour=self.adjust_colour(self.gui_html_bg_colour, luminosity=1.0))
      #image = self.add_whitespace(image=image, side='right', weight=2, colour='#ff0000')
    #image = self.add_whitespace(image=image, side='bottom', weight=1, colour=self.adjust_colour(self.gui_html_bg_colour, luminosity=0.90))
    #image = self.add_whitespace(image=image, side='bottom', weight=1, colour=self.adjust_colour(self.gui_html_bg_colour, luminosity=0.95))
    filename = item
    return image