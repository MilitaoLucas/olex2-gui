from __future__ import division
#import PngImagePlugin
import FileSystem as FS
from ArgumentParser import ArgumentParser
import Image
import glob, os
import copy
import ImageDraw, ImageChops, ImageColor
import OlexVFS
#import olex_core
import pickle
import RoundedCorners
import sys
#from olexex import OlexVariables
#OV = OlexVariables()
import olexex
#OV = olexex.OlexFunctions()
from ImageTools import ImageTools
IT = ImageTools()
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import olex_fs


try:
  import olx
  import olex
  datadir = olx.DataDir()
  basedir = olx.BaseDir()
#       newdir = r"%s\etc\gui\images\tools" %datadir
#       if not os.path.isdir(newdir):
#       _mkdir(newdir)
except:
  pass


class ButtonMaker(ImageTools):
  def __init__(self, btn_dict, type="Generic"):
    super(ButtonMaker, self).__init__()
    self.type = type
    self.btn_dict = btn_dict
    self.max_width = OV.FindValue('gui_htmlpanelwidth', 320)
  def run(self):
    if self.type == "Generic":
      im = self.GenericButtonMaker()
    if self.type == "cbtn":
      im = self.cbtn()

  def GenericButtonMaker(self,  font_name = "Vera", font_size = 14):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
    if self.gui_button_font_name:
      font_name = self.gui_button_font_name
    icon_width = OV.FindValue('gui_icon_width', 20)  
    width = int(icon_width * 1.1)
    height = int(icon_width * 0.9)
    
    font_colours = {'H':(220,220,220),'C':(100,100,100),'N':(0,80,180),'O':(230,0,5),'AddH':(50,255,50),'-H':(230,0,5), }
    
    for btn in self.btn_dict:
      width = self.btn_dict[btn].get('width', 18)
      font_size = self.btn_dict[btn].get('font_size', 14)
      d = self.btn_dict[btn]
      image_prefix = d.get("image_prefix", "")
      height = d.get("height", height)
      bgcolour = d.get("bgcolour", self.gui_html_bg_colour)
      txt = d['txt']
      name = d.get('name', txt)
      fontcolouroff = d.get("fontcolouroff", None)
      fontcolouron = d.get("fontcolouron", None)
      grad = d.get('grad', False)
      grad_colour = self.adjust_colour(self.gui_timage_colour, luminosity = 2.1)
      outline_colour = self.gui_html_table_bg_colour
      continue_mark = d.get('continue_mark', False)
      states = d.get('states', [""])
      vline = d.get('vline', False)
      align = d.get('align', 'centre')
      valign = d.get('valign', ("middle", 0.8))
      font_name = d.get('font_name', 'Verdana')
      top_left = d.get('top_left', (0,0))
      titleCase = d.get('titleCase', False)
      lowerCase = d.get('lowerCase', False)
      arrow = d.get('arrow', False)
      showtxt = d.get('showtxt', True)
      whitespace_bottom = d.get('whitespace_bottom', False)
      whitespace_right = d.get('whitespace_right', False)
      try:
        width,number_minus,fixed  = d.get("width", (width,(0,0),0))
        number = number_minus[0]
        minus = number_minus[1]
        if width == "auto":
          width = int(self.gui_htmlpanelwidth)-(number * minus)
          width = (width/number-9)
          if vline:
            vline.setdefault('position', width - 15)
            olx.SetVar("main_toolbar_vline_position, %s" %int(width - 15))
      except:
        width = int(width)
      size = (int(width), int(height))

      for state in states:
        font_colour = self.gui_html_font_colour
        bgcolour = d.get('bgcolour%s' %state, bgcolour)
        if txt in ["report", "solve", "refine"]:
          font_colour = d.get("fontcolour%s" %state, font_colour)
          #font_colour = self.adjust_colour(font_colour, luminosity=0.7)
        image = Image.new('RGBA', size, bgcolour)
        draw = ImageDraw.Draw(image)
        if grad:
          self.gradient_bgr(draw, 
                            width, 
                            height, 
                            colour = grad.get('grad_colour', bgcolour), 
                            fraction=grad.get('fraction', 1),
                            increment=grad.get('increment', 10),
                            step=grad.get('step', 1)
                          )
        if continue_mark:
          if state == "on":
            self.add_continue_triangles(draw, width, height, style=('single', 'up', font_colour))
          elif state == 'off':
            self.add_continue_triangles(draw, width, height, style=('single', 'down', font_colour))
          elif state == 'inactive':
            self.add_continue_triangles(draw, width, height, style=('single', 'down', font_colour))
        if arrow:
          if state == "off":
            self.create_arrows(draw, height, direction="down", h_space=4, v_space=6, colour=font_colour, type='simple')
          elif state == "on":
            self.create_arrows(draw, height, direction="up", h_space=4, v_space=6, colour=font_colour, type='simple')
          elif state == "inactive":
            self.create_arrows(draw, height, direction="down", h_space=4, v_space=6, colour=font_colour, type='simple')
        if vline:
          if state == "on" or state == "off":
            if grad:
              colour = self.adjust_colour(grad_colour, luminosity=0.8)
            else:
              colour = fontcolouroff
            self.add_vline(draw, height=vline.get('height',10), h_pos=vline.get('position',10), v_pos=vline.get('v_pos',2), colour = colour, weight=1,) # colour = IT.adjust_colour(bgcolour, luminosity=1.8))
          else:
            self.add_vline(draw, height=vline.get('height',10), h_pos=vline.get('position',10), v_pos=vline.get('v_pos',2), colour = font_colour, weight=1,) 
            
        if showtxt:  
          self.write_text_to_draw(draw, txt, 
                                        font_name=font_name, 
                                        font_size=font_size, 
                                        font_colour=font_colour, 
                                        top_left=top_left,
                                        align=align, 
                                        max_width=image.size[0],
                                        image_size = image.size,
                                        titleCase=titleCase,
                                        lowerCase=lowerCase,
                                        valign=valign,
                                      ) 
        if txt not in ["report", "solve", "refine"]:        
          if state == "on":
            outline_colour = self.gui_html_highlight_colour
        draw.rectangle((0, 0, image.size[0]-1, image.size[1]-1), outline=outline_colour)
        dup = ImageChops.duplicate(image)
        dup = ImageChops.invert(dup)
        dup = ImageChops.offset(dup, 1, 1)
        image = ImageChops.blend(image, dup, 0.05)
        if whitespace_right:
          image = self.add_whitespace(image=image, side='right',
                                      weight=whitespace_right.get('weight',0), 
                                      colour=whitespace_right.get('colour','#ffffff'))
        if whitespace_bottom:
          image = self.add_whitespace(image=image, side='bottom', 
                                      weight=whitespace_bottom.get('weight',0), 
                                      colour=whitespace_bottom.get('colour','#ffffff'))
        #image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.95))
        OlexVFS.save_image_to_olex(image,'%s-%s%s.png' %(image_prefix, name, state), 2)
      
class GuiSkinChanger(ImageTools):
  def __init__(self, tool_fun=None, tool_arg=None):
    super(GuiSkinChanger, self).__init__()
    self.fun = tool_fun
    self.param = tool_fun

  def setOlexColours(self):
    import olex
    OV.SetGrad()

  def setGuiProperties(self):
    olex.m("SetMaterial InfoBox.Text 2309;1,1,1,1;1,1,1,1")
    olex.m("SetMaterial InfoBox.Plane 3077;0,0,0,1;1,1,1,0.5")
    olex.m("SetFont Notes #olex2.fnt:frb_10")
    olex.m("SetFont Console #olex2.fnt:frb_12")
    olex.m("htmguifontsize %s" %self.gui_html_font_size)
    olex.m("showwindow help false")
    olex.m("grad true")
    
  def setGuiAttributesDefault(self):
    #self.gui_html_base_colour = "#ffffff"
    self.gui_html_bg_colour = "#ffffff"
    self.gui_html_font_colour = "#6f6f8b"
    self.gui_html_font_name = 'Arial'
    self.gui_html_font_size = '2' 
    self.gui_html_icon_size = '20'
    self.gui_html_link_colour = "#6f6f8b"
    self.gui_html_table_bg_colour = "#F3F3F3"
    self.gui_html_table_firstcol_colour = "#E9E9E9"
    self.gui_table_rows = "#F3F3F3"
    self.gui_html_input_bg_colour="#efefef"
    self.gui_timage_colour = "#6464a0"
    self.gui_base_colour = "#6464a0"
    self.gui_logo_colour = "#6464a0"
    self.gui_skin_logo_name = "basedir()\etc\gui\images\src\default.png"
    self.gui_skin_extension="n/a"
    self.gui_html_panelwidth = '350'
    self.gui_snumtitle_colour='#6464a0'
    self.gui_html_highlight_colour = '#ff7800'
    self.gui_grad_top_left = '#05053c'
    self.gui_grad_top_right = '#05053c'
    self.gui_grad_bottom_left = '#ffffff'
    self.gui_grad_bottom_right = '#ffffff' 
    self.gui_htmlpanelwidth = '320' 
    
  def run(self):
    path = r"gui/images/src/default.png"
    skin = self.gui_skin_name
    config = {}
    if "#" in skin:
      #self.getVariables('gui')
      #self.set_custom(skin)
      #self.setGuiAttributes()
      self.getVariables('gui')
      self.setGuiAttributesDefault()
      self.setOlexColours()
      path = r"gui/images/src/default.png"
      import PilTools
    elif "(" in skin:  
      #self.getVariables('gui')
      self.set_custom(skin)
      self.getVariables('gui')
      self.setGuiAttributesDefault()
      self.setVariables("gui")
      self.setOlexColours()
      path = r"gui/images/src/default.png"
      import PilTools
    #elif skin == "default":
      #self.setGuiAttributesDefault()
      #self.setGuiAttributes()
      #self.setVariables('gui')
      #self.setOlexColours()
      #path = r"gui/images/src/default.png"
      #import PilTools
##    this is a 'named' skin - ie should have a plugin-folder associated with it
    else:
      self.getVariables('gui')
      self.setGuiAttributesDefault()
      self.setVariables("gui")
      skinpath = r"%s/util/pyUtil/PluginLib/skins/plugin-%sSkin" %(self.basedir, skin)
      # First try to load the skin extension.
      try:
        extensionFile = open(r"%s/config%s.txt" %(skinpath, self.param.strip()), 'r')
      # Then load the actual named skin.
      except:
        extensionFile = None
        print "Skin definition file\n%s/config%s.txt\nnot found!" %(skinpath, self.param.strip())
      rFile = open(r"%s/config.txt" %(skinpath), 'r')
      files = [extensionFile, rFile]
      for file in files:
        for line in file:
          line= line.strip()
          if line.startswith("#"): continue
          l = line.split("=")
          if len(l) > 1:
            config.setdefault(l[0].strip(), l[1].strip())

      try:
        sys.path.append("%s/util/pyUtil/PluginLib/Skins/plugin-%sSkin" %(olx.BaseDir(), skin))
        PilTools = __import__("PilTools_%s" %skin)
        print "Using %s skin." %"PilTools_%s" %(skin)
      except ImportError:
        print "Using Default PilTools"
        import PilTools
      except Exception, err:
        raise
      self.gui_html_base_colour = config.get('GUI_HTML_BASE_COLOUR', '#0000ff')  
      self.setGuiAttributes(config)
      self.setVariables('gui')
      self.setOlexColours()
    self.resize_skin_logo(self.gui_htmlpanelwidth)
    self.setVariables("gui")
    a = PilTools.sNumTitle()
    a.run()
    a = PilTools.timage()
    a.run()
    olx.HtmlPanelWidth(self.gui_htmlpanelwidth)
    self.setGuiProperties()
    OV.HtmlReload()
    
    #olex.m('panel')


  def set_custom(self, colour=None):
    if not colour:
      colour = olx.Color('hex')
    else:
      if "," in colour:
        c = colour.strip("'")
        c = c.strip("(")
        c = c.strip(")")
        c = c.split(",")
        l = []
        for item in c:
          l.append(int(item.strip()))
        colour = tuple(l)
       
      if type(colour) != str:
        colour = self.RGBToHTMLColor(colour)
    self.gui_html_bg_colour = "#ffffff"
    self.gui_html_font_colour = self.RGBToHTMLColor(self.adjust_colour(colour, hue = 180, luminosity = 0.8))
    self.gui_html_link_colour = "#6f6f8b"
    self.gui_html_table_bg_colour = self.RGBToHTMLColor(self.adjust_colour(colour, luminosity = 2))
    self.gui_html_table_firstcol_colour = self.RGBToHTMLColor(self.adjust_colour(colour, luminosity = 1.8))
    self.gui_html_input_bg_colour = self.RGBToHTMLColor(self.adjust_colour(colour, luminosity = 1.9))
    self.gui_timage_colour = self.RGBToHTMLColor(self.adjust_colour(colour, luminosity = 0.9))


class MatrixMaker(ImageTools):
  def __init__(self):
    super(MatrixMaker, self).__init__()
    #import PngImagePlugin
    #import Image
    #import ImageDraw, ImageChops

  def make_3x3_matrix_image(self, name, matrix, text_def=""):
    width = 52
    height = 55
    size = (width, height)
    font_name = "Arial"
    font_size = 13
    font = self.registerFontInstance(font_name, font_size)
    line_heigth = font_size -2
    im = Image.new('RGBA', size, '#dedede')
    draw = ImageDraw.Draw(im)
    m = []
    i = 0
    max_width = 0
    for item in matrix:
      if i == 9: break
      try:
        item = int(item)
      except:
        item = item
      txt_size = draw.textsize(str(item), font=font)
      w = txt_size[0]
      if w > max_width:
        max_width = w
      i += 1
    if max_width < 15: max_width = 15
    i = 0  
    for item in matrix:
      if i == 9: break
      try:
        item = int(item)
      except:
        item = item
      m.append(item)
      i += 1
      
    i = 0
    j = 0
    k = 0
    for item in m:
      if i < 3:
        j = i
      elif i == 3:
        j = 0
        k = 1
      elif i < 6:
        j = (i-3)
      elif i == 6:
        j = 0
        k = 2
      else:
        j = (i-6)
      txt_size = draw.textsize(str(item), font=font)
      begin = ((j * max_width) + ((max_width - txt_size[0])), k * line_heigth)
      #print i, j, k, begin
      draw.text(begin, "%s" %item, font=font, fill=(100, 100, 100))
      i += 1

    font_size = 10
    line_heigth = font_size -2
    font_nbame = "Arial"
    font = self.registerFontInstance(font_name, font_size)
    for i in xrange(len(text_def)):
      item = text_def[i].get('txt',"")
      colour = text_def[i].get('font_colour',"")
      w = draw.textsize(str(item), font=font)[0]
      draw.text(((width-w)/2, 35 + line_heigth * i), "%s" %item, font=font, fill=(colour))
    name = r"%s.png" %(name)
    OlexVFS.save_image_to_olex(im, name, 2)
    return name, im


def fade_image(image, frames=5, overlay_colour=(255, 255, 255), filename="out.gif"):
  import Image
  import gifmaker
  size = image.size
  overlay = Image.new('RGBA', size, overlay_colour)

  sequence = []

  for i in range(frames):
    im = Image.blend(overlay, image, 1 - (1/frames) * i)
    im.save("C:/t/fred_%i.png" %i)
    im = im.convert("P")
    sequence.append(im)
  fp = open(filename, "wb")
  gifmaker.makedelta(fp, sequence)
  fp.close()



class BarMaker(object):
  def __init__(self, dx, dy, colour):
    self.dx = int(dx)
    self.dy = int(dy)
    self.colour = colour

  def makeBar(self):
    size = (self.dx, self.dy)
    colour = self.colour
    weight = 15
    height = self.dy
    if colour == 'purple':
      colour = [(162, 69, 162), (154, 53, 154), (142, 47, 142), (128, 43, 128), (115, 38, 115)]
    if colour == 'orange':
      colour = [(255, 208, 22), (255, 205, 3), (237, 190, 0), (214, 171, 0), (191, 153, 0)]
    if colour == 'green':
      colour = [(22, 255, 69), (3, 255, 53), (0, 237, 47), (0, 214, 43), (0, 191, 38)]
    if colour == 'green':
      colour = [(22, 237, 69), (3, 214, 53), (0, 191, 47), (0, 180, 43), (0, 170, 38)]

    image = Image.new('RGBA', size, colour[0])
    draw = ImageDraw.Draw(image)

    j = 0
    k = 0
    for i in xrange(weight):
      draw.line(((i, 0) ,(i, size[1])), fill=colour[k])
      j += 1
      if j > 3:
        k+= 1
        j = 0

    adjustment_bottom = (1.1, 1.3, 2)
    adjustment_top = (0.8, 0.95, 1.03)

    #for j in xrange(3):
      #for i in xrange(weight):
        #c = []
        #for item in colour[i]:
          #c.append(item/adjustment_bottom[j])
        #col = (c[0], c[1], c[2])
        #draw.line(((i, height-3+j) ,(i, height-2+j)), fill=col)
        #c = []
        #for item in colour[i]:
          #c.append(item/adjustment_top[j])
        #col = (c[0], c[1], c[2])
        #draw.line(((i, j) ,(i, j+1)), fill=col)
    return image



class BarGenerator(ImageTools):
  def __init__(self, type='vbar', colour='grey', size=100, basedir=""):
    super(BarGenerator, self).__init__()
    self.thickness = 5
    self.type = type
    self.colour = colour
    self.size = size

  def run(self):
    if self.type == "vbar":
      image = self.make_vBar(self.size, self.colour)
      if self.colour == "grey":
        name = r"solve.png"
      else:
        name = r"vBar-%i.png" %(int(self.size))
      OlexVFS.save_image_to_olex(image, name, 2)
      #image.save(r"%s\etc\gui\images\tools\vBar-%s.png" %(datadir, int(self.size)), "PNG")
    return name

  def make_vBar(self, size, colour):
    weight = int(self.thickness)
    height = int(size)
    size = (int(5), int(height))
    if colour == 'purple':
      colour = [(162, 69, 162), (154, 53, 154), (142, 47, 142), (128, 43, 128), (115, 38, 115)]
    if colour == 'orange':
      colour = [(255, 208, 22), (255, 205, 3), (237, 190, 0), (214, 171, 0), (191, 153, 0)]
    if colour == 'green':
      colour = [(22, 240, 69), (3, 240, 53), (0, 225, 47), (0, 200, 43), (0, 180, 38)]
    if colour == 'grey':
      colour = [(210, 210, 210), (205, 205, 205), (200, 200, 200), (190, 190, 190), (170, 170, 170)]

    image = Image.new('RGBA', size, colour[0])
    draw = ImageDraw.Draw(image)

    for i in xrange(weight):
      draw.line(((i, 0) ,(i, size[1])), fill=colour[i])

    adjustment_bottom = (1.1, 1.3, 2)
    adjustment_top = (0.8, 0.95, 1.03)

    for j in xrange(3):
      for i in xrange(weight):
        c = []
        for item in colour[i]:
          c.append(item/adjustment_bottom[j])
        col = (int(c[0]), int(c[1]), int(c[2]))
        draw.line(((i, height-3+j) ,(i, height-2+j)), fill=col)
        c = []
        for item in colour[i]:
          c.append(item/adjustment_top[j])
        col = (int(c[0]), int(c[1]), int(c[2]))
        draw.line(((i, j) ,(i, j+1)), fill=col)

    return image

  def make_RBar(self, R, factor = 300):
    
    if R == 'sol': #grey
      colour = [(210, 210, 210), (205, 205, 205), (200, 200, 200), (190, 190, 190), (170, 170, 170)]
      colour_a = (210,210,210)
      R = 0.23
    elif R > 0.2: #purple
      colour = [(162, 69, 162), (154, 53, 154), (142, 47, 142), (128, 43, 128), (115, 38, 115)]
      colour_a = self.adjust_colour(OV.FindValue('gui_purple'), luminosity=1.2)
    elif R > 0.10: #'orange':
      colour = [(255, 208, 22), (255, 205, 3), (237, 190, 0), (214, 171, 0), (191, 153, 0)]
      colour_a = self.adjust_colour(OV.FindValue('gui_orange'), luminosity=1.2)
    elif R < 0.11: #'green':
      colour = [(22, 240, 69), (3, 240, 53), (0, 225, 47), (0, 200, 43), (0, 180, 38)]
      colour_a = self.adjust_colour(OV.FindValue('gui_green'), luminosity=1.2)
    
      
    size = R * factor
    if size < 1:
      size = 1
    width = int(self.thickness)
    self.thickness = 5
    height = int(size)
    manual = False
    if manual:
      # Manual adjustment of colours from the list above
      size = (width, int(height))
      image = Image.new('RGBA', size, colour[0])
      draw = ImageDraw.Draw(image)
      for i in xrange(weight):
        draw.line(((i, 0) ,(i, size[1])), fill=colour[i])
    else:
      #Automatic adjustment  
      size = (int(height), width)
      image = Image.new('RGBA', size, "#000000")
      grad_colour = self.adjust_colour(colour_a, luminosity = 1)
      draw = ImageDraw.Draw(image)
      self.gradient_bgr(draw, height, width, colour = grad_colour, fraction=1, step=0.8) # width and height are swapped!
      image = image.rotate(90)
      draw = ImageDraw.Draw(image)

    adjustment_bottom = (1.1, 1.3, 2)
    adjustment_top = (0.8, 0.95, 1.03)
    # Create the top and bottom shading for each bar
    for j in xrange(3):
      for i in xrange(width):
        c = []
        samplepixheight = int(image.size[1]/2)
        cpx = image.getpixel((i,samplepixheight))
        for item in cpx:
          c.append(item/adjustment_bottom[j])
        col = (int(c[0]), int(c[1]), int(c[2]))
        draw.line(((i, height-3+j) ,(i, height-2+j)), fill=col)
        c = []
        for item in cpx:
          c.append(item/adjustment_top[j])
        col = (int(c[0]), int(c[1]), int(c[2]))
        draw.line(((i, j) ,(i, j+1)), fill=col)

    return image

class MakeAllRBars(BarGenerator):
  def __init__(self, tool_fun=None, tool_arg=None):
    super(MakeAllRBars, self).__init__()
    self.thickness = 5
    self.factor = 300
    #self.gui_html_bg_colour = OV.FindValue('gui_html_bg_colour')

  def run(self):
    name = "vscale.png"
    OlexVFS.save_image_to_olex(self.makeRBarScale(), name, 2)
    name = "vbar-sol.png"
    OlexVFS.save_image_to_olex(self.make_RBar('sol', factor=self.factor), name, 2)
    for i in xrange(221):
      R = i/1000
      name = "vbar-%i.png" %(R*1000)
      image_exists = olex_fs.Exists(name)
      if image_exists:
        image = self.make_RBar(R, factor=self.factor)
      image = self.make_RBar(R, factor=self.factor)
      if image:
        OlexVFS.save_image_to_olex(image, name, 2)
    
  def run_(self):
    for i in xrange (100):
      size = i + 1
      if i >= 20:
        colour = 'purple'
        size = "22"
      if i < 20:
        colour = 'orange'
      if i <10:
        colour = 'green'
      image = self.make_vBar(int(size * self.scale), colour)
      name = r"vBar-%i.png" %(int(size))
      OlexVFS.save_image_to_olex(image, name, 2)

    name = "vscale.png"
    RBarScale = self.makeRBarScale()
    OlexVFS.save_image_to_olex(RBarScale, name, 2)

  def makeRBarScale(self):
    width = 22
    scale = self.factor/100
    top = 20
    text_width = 14
    height = (top * scale) + 10
    size = (int(width), int(height))
    image = Image.new('RGBA', size, self.gui_html_table_bg_colour)
    draw = ImageDraw.Draw(image)
    draw.line(((width-2, 0) ,(width-2, height)), fill='#666666')

    font_name = "Verdana Bold"
    font_size = 10
    font = self.registerFontInstance(font_name, font_size)

    txt = r"R1"
    hStart = self.centre_text(draw, txt, font, text_width)
    draw.text((hStart, -1), "%s" %txt, font=font, fill='#666666')
    #txt = "%%"
    #draw.text((0, 9), "%s" %txt, font=font, fill='#000000')

    font_name = "Vera"
    font_size = 10
    font = self.registerFontInstance(font_name, font_size)

    divisions = 4
    for i in xrange(divisions):
      if i ==0:
        continue
      txt = str((divisions - (i - 1)) * scale)
      txt = str(int((top/divisions)*(divisions - i)))
      hStart = self.centre_text(draw, txt, font, text_width)
      vpos = int(height/(divisions)*(i))
      draw.text((hStart, vpos-5), "%s" %txt, font=font, fill='#666666')
      draw.line(((width-5, vpos) ,(width-2, vpos)), fill='#666666')

#   draw.line(((width-5, int(height/(i+1)*2) ,(width-1, int(height/4)*2)), fill='#000000')
#   draw.line(((width-5, int(height/(i+1)*3) ,(width-1, int(height/4)*3)), fill='#000000')

    return image

class sNumTitle(ImageTools):
  def __init__(self, width=None, tool_arg=None):
    super(sNumTitle, self).__init__()
    self.have_connection = False
    width = self.gui_htmlpanelwidth
    if not width:
      width = 290
    try:
      width = float(width)
    except:
      width = float(tool_arg)
    if tool_arg:
      args = tool_arg.split(";")
      if args[0] == "None":
        self.gui_base_colour = OV.FindValue('gui_base_colour')
      elif args[0][:1] == "#":
        self.gui_base_colour = self.HTMLColorToRGB(args[0])
      else:
        self.gui_base_colour = args[0]
    else:
        self.gui_base_colour = OV.FindValue('gui_base_colour')
      

    if self.have_connection:
      try:
        import SQLFactories
        self.ds = SQLFactories.SQLFactory()
      except:
        self.have_connection = False
        pass

    self.sNum = self.filename
    try:
      width = float(width)
    except:
      width = float(tool_arg)
    self.width = int((width) - 22)

  def run(self):
    items = {}
    if self.filename != 'none':
      if self.have_connection:
        try:
          from DimasInfo import dimas_info
          self.getInfo = dimas_info("info")
          items = self.getInfo.run()
          items.setdefault("sNum", olx.FileName())
        except Exception, ex:
          raise ex

    if not items:
      items.setdefault("operator", "n/a")
      items.setdefault("submitter", "no info")
      items.setdefault("type", "none")
      items.setdefault("sNum", "none")
      try:
        items["type"] = olx.FileExt()
        items["sNum"] = olx.FileName()
      except Exception, ex:
        raise ex
    image = self.sNumTitleStyle1(items)
     
    name = r"gui/images/sNumTitle.png"
    OlexVFS.save_image_to_olex(image, name, 1)


  def own_sql(self): #not currently used
    sNum = self.sNum
    sql = """SELECT people_status.Nickname
FROM submission INNER JOIN people_status ON submission.OperatorID = people_status.ID
WHERE (((submission.ID)="%s"));""" %sNum
    rs = self.ds.run_select_sql(sql)
    nickname = ""
    for record in rs:
      nickname = record[0]
    items.setdefault("nickname", nickname)

    record = ""
    sql = """SELECT people_fullnames.display
FROM submission INNER JOIN people_fullnames ON submission.SubmitterID = people_fullnames.ID
WHERE (((submission.ID)="%s"));""" %sNum
    rs = self.ds.run_select_sql(sql)
    submitter = ""
    for record in rs:
      submitter = record[0]
    items.setdefault("submitter", submitter)


  def sNumTitleStyle1(self, items, font_name="Arial Bold", font_size=17):
    if self.gui_sNumTitle_font_name:
      font_name = self.gui_sNumTitle_font_name
    width = self.width
    height = 24
    self.height = height
    gap = 0
    bgap = height - gap
    size = (int(width), int(height))
    #cs = copy.deepcopy(cS1)

    if olx.IsFileType("cif") == 'true':
      base = (255, 0, 0)

    base = self.gui_timage_colour
    image = Image.new('RGBA', size, base)

    draw = ImageDraw.Draw(image)
    
    grad_colour = self.adjust_colour("base", luminosity = 1.1)
    self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=0.7)
    cache = {}
    pos = (('Rounded'),('Rounded'),('Square'),('Square'))
    #pos = (('Rounded'),('Rounded'),('Rounded'),('Rounded'))
    #pos = (('Square'),('Square'),('Square'),('Square'))
    image = RoundedCorners.round_image(image, cache, 2, pos=pos) #used to be 10

    #border_rad=20
    #self.make_border(rad=border_rad,
            #draw=draw,
            #width=width,
            #height=height,
            #bg_colour=base,
            #border_colour=base,
            #cBottomLeft=False,
            #cBottomRight=False,
            #border_hls = (0, 1.2, 1)
          #)

    sNum = items["sNum"]
    if sNum == "none": sNum = "No Structure"
    self.write_text_to_draw(draw, 
                       sNum, 
                       top_left=(6, 1), 
                       font_name=font_name, 
                       font_size=17, 
                       image_size = image.size,
                       valign=("middle", 0.8),
                       font_colour=self.adjust_colour("base", luminosity = 2.0))
    
    self.drawFileFullInfo(draw, luminosity=1.8, right_margin=3, bottom_margin=0)
    self.drawSpaceGroupInfo(draw, luminosity=1.8, right_margin=3)


    ### Draw this info ONLY if there is a connection to the MySQL database
    #if self.have_connection:
      #self.drawDBInfo()
      
    dup = ImageChops.duplicate(image)
    dup = ImageChops.invert(dup)
    dup = ImageChops.offset(dup, 1, 1)
    image = ImageChops.blend(image, dup, 0.05)
      
    return image

  def drawFileFullInfo(self, draw, luminosity=1.8, right_margin=0, bottom_margin=0, font_name="Verdana", font_size=8):
    left_start = 120
    txt = self.filefull
    if len(txt) > 26:
      txtbeg = txt[:5]
      txtend = txt [-25:]
      txt = "%s...%s" %(txtbeg, txtend)
      
    font = self.registerFontInstance(font_name, font_size)
    tw = (draw.textsize(txt, font)[0])
    left_start =  (self.width-tw) - right_margin
    bottom = self.height - bottom_margin - 9
    self.write_text_to_draw(draw, 
                       txt, 
                       top_left=(left_start, 12), 
                       font_name=font_name, 
                       font_size=font_size, 
                       font_colour=self.adjust_colour("base", luminosity=luminosity))


  def drawSpaceGroupInfo(self, draw, luminosity=1.9, right_margin=12, font_name="Times Bold"):
    left_start = 120
    font_colour = self.adjust_colour("base", luminosity=luminosity)

    try:
      txt_l = []
      txt_sub = []
      txt_norm = []
      try:
        txt = OV.olex_function('sg(%h)')
      except:
        pass
      if not txt:
        txt="ERROR"
      txt = txt.replace(" 1", "")
      txt = txt.replace(" ", "")
      txt_l = txt.split("</sub>") 
      if len(txt_l) == 1:
        txt_norm = [(txt,0)]
      try:
        font_base = "Times"
        #font_slash = self.registerFontInstance("Times Bold", 18)
        #font_number = self.registerFontInstance("Times Bold", 14)
        #font_letter = self.registerFontInstance("Times Bold Italic", 15.5)
        #font_sub = self.registerFontInstance("Times Bold", 10)
        font_bar = self.registerFontInstance("%s Bold" %font_base, 11)
        font_slash = self.registerFontInstance("%s Bold" %font_base, 18)
        font_number = self.registerFontInstance("%s Bold" %font_base, 14)
        font_letter = self.registerFontInstance("%s Bold Italic" %font_base, 15)
        font_sub = self.registerFontInstance("%s Bold" %font_base, 10)
        norm_kern = 2
        sub_kern = 0
      except:
        font_name = "Arial"
        font_bar = self.registerFontInstance("%s Bold" %font_base, 12)
        font_slash = self.registerFontInstance("%s Bold" %font_base, 18)
        font_number = self.registerFontInstance("%s Bold" %font_base, 14)
        font_letter = self.registerFontInstance("%s Bold Italic" %font_base, 15)
        font_norm = self.registerFontInstance(font_name, 13)
        font_sub = self.registerFontInstance(font_name, 10)
        norm_kern = 0
        sub_kern = 0
      textwidth = 0
      for item in txt_l:
        if item:
          try:
            sub = item.split("<sub>")[1]
          except:
            sub = ""
          norm = item.split("<sub>")[0]
          tw_s = (draw.textsize(sub, font=font_sub)[0]) + sub_kern
          tw_n = (draw.textsize(norm, font=font_number)[0]) + norm_kern
          txt_sub.append((sub, tw_s))
          txt_norm.append((norm, tw_n))
          textwidth += (tw_s + tw_n)
    except:
      txt_l = []
    if txt_l:
      i = 0
      left_start =  (self.width-textwidth) - right_margin -5
      cur_pos = left_start
      advance = 0
      after_kern = 0
      for item in txt_l:
        if item:
          text_normal = txt_norm[i][0]
          for character in text_normal:
            if character == "":
              continue
            cur_pos += advance
            cur_pos += after_kern
            after_kern = 2
            advance = 0
            try:
              int(character)
              font = font_number
              top = 0
              after_kern = 2
            except:
              font = font_letter
              top = -1
              if character == "P" or character == "I" or character == "C":
                norm_kern = -2
                after_kern = 0
                character = " %s" %character
            if character == "-":
              draw.text((cur_pos + 1, -10), "_", font=font_bar, fill=font_colour)
              draw.text((cur_pos + 1, -9), "_", font=font_bar, fill=font_colour)
              advance = -1
              norm_kern = 0
            elif character == "/":
              norm_kern = 0
              after_kern = 0
              draw.text((cur_pos -2, -3), "/", font=font_slash, fill=font_colour)
              advance = ((draw.textsize("/", font=font_slash)[0]) + norm_kern) - 1
            else:
              draw.text((cur_pos + norm_kern, top), "%s" %character, font=font, fill=font_colour)
              advance = (draw.textsize(character, font=font)[0]) + norm_kern
            
          text_in_superscript = txt_sub[i][0]
          if text_in_superscript:
            cur_pos += advance
            draw.text((cur_pos + sub_kern, 5), "%s" %text_in_superscript, font=font_sub, fill=font_colour)
            advance = (draw.textsize(text_in_superscript, font=font_sub)[0]) + sub_kern
            after_kern = -2
            cur_pos += advance
        i+= 1


class timage(ImageTools):

  def __init__(self, width=None, tool_arg=None):
    super(timage, self).__init__()
    #from PilTools import ButtonMaker
    self.abort = False
    width = self.gui_htmlpanelwidth
    if not width:
      width = 290
    else:
      try:
        width = float(width)
      except:
        width = float(tool_arg)
    #self.gui_html_bg_colour = OV.FindValue("gui_html_bg_colour")
    #self.gui_timage_colour = OV.FindValue("gui_timage_colour")
    #self.gui_skin_name = OV.FindValue("gui_skin_name")
    #self.gui_html_highlight_colour = OV.FindValue("gui_html_highlight_colour")
    self.font_name = "Vera"
    self.timer = False
    if self.timer:
      import time
      self.time = time
    if tool_arg:
      args = tool_arg.split(";")
      if args[0] == "None":
        self.gui_base_colour = OV.FindValue('gui_base_colour')
      else:
        self.gui_base_colour = self.HTMLColorToRGB(args[0])
      
    self.width = int((width) - 22)
    if self.width <= 0: self.width = 10
    
    icon_source = "%s/etc/gui/images/src/icons.png" %self.basedir
    image_source = "%s/etc/gui/images/src/images.png" %self.basedir
    self.iconSource = Image.open(icon_source)
    self.imageSource = Image.open(image_source)

    sf = 4
    im = Image.open(image_source)
    cut = 0, 52*sf, 27*sf, 76*sf
    crop =  im.crop(cut)
    self.warning =  Image.new('RGBA', crop.size, self.gui_html_bg_colour)
    self.warning.paste(crop, (0,0), crop)
    name = "warning.png"
    self.warning = self.resize_image(self.warning, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    OlexVFS.save_image_to_olex(self.warning, name, 2)
    
    cut = 140*sf, 58*sf, 170*sf, 81*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_firstcol_colour)
    IM.paste(crop, (0,0), crop)
    #draw = ImageDraw.Draw(IM)
    #draw.rectangle((0, 0, IM.size[0]-1, IM.size[1]-1), outline='#bcbcbc')
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "HelpImage.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 201*sf, 58*sf, 227*sf, 81*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.gui_html_bg_colour)
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
    IM.paste(crop, (0,0), crop)
    #draw = ImageDraw.Draw(IM)
    #draw.rectangle((0, 0, IM.size[0]-1, IM.size[1]-1), outline='#bcbcbc')
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "popout.png"
    OlexVFS.save_image_to_olex(IM, name, 2)
    
    cut = 227*sf, 58*sf, 300*sf, 81*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
    IM.paste(crop, (0,0), crop)
    #draw = ImageDraw.Draw(IM)
    #draw.rectangle((0, 0, IM.size[0]-1, IM.size[1]-1), outline='#bcbcbc')
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "return.png"
    OlexVFS.save_image_to_olex(IM, name, 2)
    
    cut = 0*sf, 0*sf, 275*sf, 55*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.gui_html_bg_colour)
    IM.paste(crop, (0,0), crop)
    cut = 0*sf, 95*sf, 100*sf, 150*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.gui_html_highlight_colour) 
    IM.paste(crop_colouriszed, (190,10), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "olex_help_logo.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    ## SMALL buttons
    cut = 90*sf, 178*sf, 140*sf, 193*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    #crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.gui_html_highlight_colour,luminosity=1.3)) 
    button_names = ("Delete", 
                    "Select", 
                    "Balls & Sticks", 
                    "blank", 
                    "Naming", 
                    )
    states = ["on", "off", ""]
    for state in states:
      if state == "on":
        colour = self.adjust_colour(self.gui_html_highlight_colour,luminosity=1.3)
      elif state == "off":
        colour = self.adjust_colour(self.gui_html_base_colour,luminosity=1.9)
      elif state == "":
        colour = self.adjust_colour(self.gui_html_base_colour,luminosity=1.9)
      for txt in button_names:
        #IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
        crop_colouriszed = self.colourize(crop, (0,0,0), colour) 
        IM =  Image.new('RGBA', crop.size)
        IM.paste(crop_colouriszed, (0,0), crop)
        draw = ImageDraw.Draw(IM)
        t = txt.replace("blank"," _ ") 
        self.write_text_to_draw(draw, 
                     "%s" %t,
                     top_left=(4, 6), 
                     font_name = 'Vera', 
                     font_size=40, 
                     titleCase=True,                  
                     font_colour=self.gui_html_font_colour,
                     max_width = max_width,
                     align='centre'
                     )
        IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
        name = "small-button-%s%s.png" %(txt.replace(" ", "_"), state)
        name = name.lower()
        OlexVFS.save_image_to_olex(IM, name, 2)
        if name == "small-button-blank.png":
          filename = r"%s/small-button-blank.png" %self.datadir
          IM.save(filename)
    
    
    ## THREEE buttons in the HTMLpanelWIDTH
    cut = 0*sf, 178*sf, 91*sf, 195*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    #crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.gui_html_table_firstcol_colour,luminosity=0.7)) 
    button_names = ("Move Near", 
                    "Copy Near", 
                    "Add H", 
                    "Grow Mode", 
                    "Center on Cell", 
                    "Assemble", 
                    "Centre on Cell", 
                    "Largest Part",
                    "Show Basis",
                    "Show Cell",
                    "Fuse",
                    "Grow All",
                    "Edit Atom(s)",
                    "Edit Instructions",
                    "Balls & Sticks", 
                    "Wireframe", 
                    "Tubes", 
                    "Default Style", 
                    "Sphere Packing", 
                    "Ellipsoids | H", 
                    )
    states = ["on", "off", ""]
    for state in states:
      if state == "on":
        colour = self.adjust_colour(self.gui_html_highlight_colour,luminosity=1.3)
      elif state == "off":
        colour = self.adjust_colour(self.gui_html_base_colour,luminosity=1.9)
      elif state == "":
        colour = self.adjust_colour(self.gui_html_base_colour,luminosity=1.9)
  
      for txt in button_names:
        crop_colouriszed = self.colourize(crop, (0,0,0), colour) 
        #IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
        IM =  Image.new('RGBA', crop.size)
        IM.paste(crop_colouriszed, (0,0), crop)
        draw = ImageDraw.Draw(IM)
        self.write_text_to_draw(draw, 
                     "%s" %txt, 
                     top_left=(4, 7), 
                     font_name = 'Vera', 
                     font_size=41, 
                     titleCase=True,                  
                     font_colour=self.gui_html_font_colour,
                     max_width = max_width,
                     align='centre'
                     )
        IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
        name = "button-%s%s.png" %(txt.replace(" ", "_"), state)
        name = name.lower()
        OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 0*sf, 193*sf, 275*sf, 211*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    #crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.gui_html_table_firstcol_colour,luminosity=0.7)) 
    button_names = ("Move Atoms or Model Disorder", 
                    )
    states = ["on", "off", ""]
    for state in states:
      if state == "on":
        colour = self.adjust_colour(self.gui_html_highlight_colour,luminosity=1.3)
      elif state == "off":
        colour = self.adjust_colour(self.gui_html_base_colour,luminosity=1.9)
      elif state == "":
        colour = self.adjust_colour(self.gui_html_base_colour,luminosity=1.9)
      for txt in button_names:
        crop_colouriszed = self.colourize(crop, (0,0,0), colour) 
        IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
        IM.paste(crop_colouriszed, (0,0), crop)
        draw = ImageDraw.Draw(IM)
        self.write_text_to_draw(draw, 
                     "%s" %txt, 
                     top_left=(4, 6), 
                     font_name = 'Vera', 
                     font_size=42, 
                     titleCase=True,                  
                     font_colour=self.adjust_colour(self.gui_html_font_colour,luminosity=0.9),
                     max_width = max_width,
                     align='centre'
                     )
        IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
        name = "button-%s%s.png" %(txt.replace(" ", "_"), state)
        name = name.lower()
        OlexVFS.save_image_to_olex(IM, name, 2)
      
    
    cut = 0*sf, 152*sf, 15*sf, 167*sf
    crop =  im.crop(cut)
    #crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.gui_html_table_firstcol_colour,luminosity=0.7)) 
    crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.gui_html_base_colour,luminosity=1.7)) 
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_firstcol_colour)
    IM.paste(crop_colouriszed, (0,0), crop)
    name = "info.png"
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    draw = ImageDraw.Draw(IM)
    self.write_text_to_draw(draw, 
                 "?", 
                 top_left=(4, 0), 
                 font_name = 'Vera Bold', 
                 font_size=14, 
                 font_colour=self.gui_html_font_colour)
    OlexVFS.save_image_to_olex(IM, name, 2)
    
    cut = 16*sf, 156*sf, 26*sf, 166*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.gui_html_table_firstcol_colour,luminosity=0.7)) 
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
    IM.paste(crop_colouriszed, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "info_tiny.png"
    draw = ImageDraw.Draw(IM)
    self.write_text_to_draw(draw, 
                 "i", 
                 top_left=(1, 1), 
                 font_name = 'Vera Italic', 
                 font_size=6, 
                 font_colour=self.gui_html_font_colour)
    OlexVFS.save_image_to_olex(IM, name, 2)

    
    cut = 16*sf, 156*sf, 26*sf, 166*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.gui_html_table_firstcol_colour,luminosity=0.7)) 
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_firstcol_colour)
    IM.paste(crop_colouriszed, (0,0), crop)
    draw = ImageDraw.Draw(IM)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    self.write_text_to_draw(draw, 
                 "i", 
                 top_left=(2, 1), 
                 font_name = 'Vera', 
                 font_size=10, 
                 font_colour="#ffffff")
    name = "info_tiny_fc.png"
    OlexVFS.save_image_to_olex(IM, name, 2)
    
    cut = 16*sf, 156*sf, 26*sf, 166*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.gui_html_highlight_colour) 
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_firstcol_colour)
    IM.paste(crop_colouriszed, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    draw = ImageDraw.Draw(IM)
    self.write_text_to_draw(draw, 
                 "i", 
                 top_left=(3, -1), 
                 font_name = 'Vera Bold Italic', 
                 font_size=11, 
                 font_colour="#ffffff")
    name = "info_tiny_new.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    
    cut = 30*sf, 150*sf, 55*sf, 175*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.gui_html_table_firstcol_colour) 
    for i in xrange(7):
      IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
      IM.paste(crop_colouriszed, (0,0), crop)
      IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
      draw = ImageDraw.Draw(IM)
      self.write_text_to_draw(draw, 
                   "%s" %(i), 
                   top_left=(5, 1), 
                   font_name = 'Vera Bold', 
                   font_size=19, 
                   font_colour=self.gui_html_font_colour)
      name = "circle_%s.png" %i
      OlexVFS.save_image_to_olex(IM, name, 2)
    
    cut = 55*sf, 150*sf, 80*sf, 175*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "settings_small.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 80*sf, 154*sf, 100*sf, 171*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "delete.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 101*sf, 154*sf, 117*sf, 165*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "delete_small.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 120*sf, 154*sf, 135*sf, 175*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "warning.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 140*sf, 98*sf, 400*sf, 140*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.gui_html_highlight_colour) 
    IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
    IM.paste(crop_colouriszed, (0,0), crop)
    draw = ImageDraw.Draw(IM)
    self.write_text_to_draw(draw, 
                 "You are in a Mode", 
                 top_left=(5, 2), 
                 font_name = 'Vera Bold', 
                 font_size=90, 
                 font_colour=self.gui_html_font_colour,
                 align='centre',
                 max_width=max_width
                 )
    sfm = sf*0.95
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sfm), int((cut[3]-cut[1])/sfm)))
    name = "pop_background.png"
    OlexVFS.save_image_to_olex(IM, name, 2)
    
    
    cut = 90*sf, 95*sf, 140*sf, 140*sf
    crop =  im.crop(cut)
#    IM =  Image.new('RGBA', crop.size, self.gui_html_table_bg_colour)
    IM =  Image.new('RGBA', crop.size)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "warning_big.png"
    OlexVFS.save_image_to_olex(IM, name, 2)
    
    
    self.info_bitmaps()
  
  def create_logo(self):
    factor = 4
    
    #create a new image
    width = self.width * factor
    size = (width, 55 * factor)
    IM =  Image.new('RGBA', size, self.gui_html_bg_colour)
    
    #this is the source of the images required for the logo
    image_source = "%s/etc/gui/images/src/images.png" %self.basedir
    im = Image.open(image_source)

    #first cut the small logo picture from the source 
    cut_left = 200 * factor - (int(self.gui_htmlpanelwidth) - 200) * factor
    if cut_left <= 0:
      cut_left = 0
    cut = cut_left, 0, 200 * factor, 55 * factor #the area of the small image
    crop = im.crop(cut)
    #crop_colourised = self.colourize(crop, (0,0,0), self.gui_logo_colour) 
    IM.paste(crop, (0,0), crop)

    #then cut the actual logo 
    cut = 200 * factor, 0, 372 * factor, 55 * factor #the area of the olex writing
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.gui_logo_colour) 
    IM.paste(crop_colouriszed, (width-(175 * factor),0), crop)

    #finally resize and save the final image
    IM = self.resize_image(IM, (self.width, 55))
    name = r"gui/images/logo.png"
    OlexVFS.save_image_to_olex(IM, name, 2)
    
    
  def run(self):
    do_these = ["make_generated_assorted_images",
                "make_text_and_tab_items",
                "make_label_items",
                "make_button_items",
                "make_cbtn_items",
                "make_icon_items",
                "make_image_items",
                "make_note_items",
                ]
    #do_these = []
    self.create_logo()
    for item in do_these:
      if self.timer:
        t1 = self.time.time()
      a = getattr(self, item)
      a()
      if self.timer:
        print "/t%s took %.3f s to complete" %(item, self.time.time()-t1)

  def make_generated_assorted_images(self):
    size = (6,15)
    colour = self.gui_html_table_firstcol_colour
    #colour = "#00ff00"
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    font_name = "Times Bold Italic"
    self.write_text_to_draw(draw, 
                       "i", 
                       top_left=(1, -1), 
                       font_name=font_name, 
                       font_size=14, 
                       font_colour=self.gui_html_font_colour)
    name = "infos.png"
    OlexVFS.save_image_to_olex(image, name, 2)
    
    
    
    ## Make the wedges for the Q-Peak slider
    scale = 4
    width = (int(self.gui_htmlpanelwidth) - 81)
    height = 8
    
    size = (width*scale, height*scale)
    colour = self.gui_html_table_bg_colour
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)

    left = 8*scale
    right = (int(width/2) -3) *scale
    top = 1*scale
    bottom = height*scale
    
    begin = (left, bottom)
    middle = (right, top)
    end = (right, bottom)
    draw.polygon((begin, middle, end), self.adjust_colour(self.gui_html_table_firstcol_colour, luminosity = 0.9))

    begin = (left, top)
    middle = (right, top)
    end = (left, bottom)
    draw.polygon((begin, middle, end), self.adjust_colour(self.gui_html_table_firstcol_colour, luminosity = 1.1))

    left = (int(width/2)+ 10)*scale
    right = width*scale
    
    begin = (left,  top)
    middle = (right, top)
    end = (left, bottom)
    draw.polygon((begin, middle, end), self.adjust_colour(self.gui_html_table_firstcol_colour, luminosity = 0.9))

    begin = (left, bottom)
    middle = (right, top)
    end = (right, bottom)
    draw.polygon((begin, middle, end), self.adjust_colour(self.gui_html_table_firstcol_colour, luminosity = 1.1))
    
    begin = ((int(width/2)+ 2)*scale, (1*scale) + 1)
    m1 = ((int(width/2)+ 5)*scale, (1*scale) +1)
    m2 = ((int(width/2)+ 5)*scale, (height*scale) -1)
    end = ((int(width/2)+ 2)*scale, (height*scale) -1)
    draw.polygon((begin, m1, m2, end), self.adjust_colour(self.gui_html_table_firstcol_colour, luminosity = 0.8))

    
    image = image.resize((width, height),Image.ANTIALIAS) 
    name = "qwedges.png"
    OlexVFS.save_image_to_olex(image, name, 2)

    
    

  def make_text_and_tab_items(self):
    bitmap = "working"
    olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
    textItems = []
    tabItems = []
    directories = ["etc/gui", "etc/news", "etc/gui/blocks", "etc/gui/snippets"]
    rFile = open("%s/etc/gui/blocks/index-tabs.htm" %(self.basedir), 'r')
    for line in rFile:
      t = line.split("<!-- #include ")[1]
      t = t.split()[0]
      t = t.split('-')[1]
      tabItems.append(t)
      self.tabItems = tabItems
    for directory in directories:
      for htmfile in glob.glob("%s/%s/*.htm" %(self.basedir,  directory)):
        f = (htmfile.replace('\\', '/').split('/')[-1:])
        f = f[0].split(".")[0]
        if f.split("-")[0] != "index" and f[0] != "_":
          textItems.append(f)
        #elif f[0] != "_":
        #  tabItems.append(f)
    for item in ('solution-settings-h3-solution-settings-extra', 'refinement-settings-h3-refinement-settings-extra',
                 'report-settings',):
      textItems.append(item)
        
    for item in textItems:
      states = ["on", "off"]
      name = ""
      for state in states:
        if "h3" in item:
          try:
            img_txt = item.split("-h3-")[1]
          except IndexError:
            img_txt = item
          image = self.timage_style_h3(img_txt, state)
          name = "gui/images/h3-%s-%s.png" %(item, state)
        else:
          img_txt = item
          image = self.timage_style_1(img_txt, state)
          name = "gui/images/h2-%s-%s.png" %(item, state)
        if name:
          OlexVFS.save_image_to_olex(image, name, 2)

    for item in tabItems:
      states = ["on", "off"]
      for state in states:
        image = self.tab_items(item, state)
        name = r"gui/images/tab-%s-%s.png" %(item, state)
        OlexVFS.save_image_to_olex(image, name, 2)
        #image.save(r"%s\etc\gui\images\tab-%s-%s.png" %(datadir, item.split("index-")[1], state), "PNG")

    OV.DeleteBitmap('%s' %bitmap) 

  def make_note_items(self):
    noteItems = [("Clicking on a Space-Group link will reset the structure. Run XS again.","orange","sg", True),
              ("You need an account on dimas.dur.ac.uk to use this feature","orange", "dimas", False),
              ("Click here to reset the history","orange", "historyclear", False),
              ("Reset Structure with Space Group and Formula above", "orange", "reset", False),
              ("Run AutoChem", "orange", "autochem", False),
              ("Calculate Electron Density Map", "orange", "eden", False),
              ("Calculate Voids in the Structure", "orange", "calculatevoids", False),
              ("AutoStructure is only availabe at Durham", "orange", "autostructure", True),
            ]
    for item in noteItems:
      image = self.note_items(item)
      name = r"gui/images/note-%s.png" %(item[2])
      OlexVFS.save_image_to_olex(image, name, 2)
      #image.save(r"%s\etc\gui\images\note-%s.png" %(datadir, item[2]), "PNG")

  def make_label_items(self):
    labelItemsControl = [("Start",0), ("Suffix",0), ("Type",0), ("Cycles",0), ("Q-peaks",0),("Axis",0),("Deg",0),("Step",0),("No.",0), ("More",0) ]
    for item in labelItemsControl:
      #image = self.label_items_control(item)
      image = self.label_items(item)
      name = r"gui/images/label-%s.png" %(item[0])
      OlexVFS.save_image_to_olex(image, name, 2)
      #image.save(r"%s\etc\gui\images\label-%s.png" %(datadir, item[0]), "PNG")

    labelItems = [("Display", 50), ("A-Type", 50), ("Model", 50)]
    for item in labelItems:
      image = self.label_items(item)
      name = r"gui/images/label-%s.png" %(item[0])
      OlexVFS.save_image_to_olex(image, name, 2)
      #image.save(r"%s\etc\gui\images\label-%s.png" %(datadir, item[0]), "PNG")

  def make_cbtn_items(self, font_name = 'Vera'):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
      font_name = "%s Bold" %font_name
      
    settings_button_width = 0
    cbtn_buttons_height = 18
    
    all_cbtn_buttons = {
        'image_prefix':'cbtn',
        'height':cbtn_buttons_height,
        'font_name':font_name,
        'bgcolour':(60,80,140),
        'fontcolouroff':self.adjust_colour(self.gui_timage_colour, luminosity = 1.1),
        'bgcolouroff':self.adjust_colour(self.gui_timage_colour, luminosity = 1.8),
        'bgcolouron':self.gui_timage_colour,
        'fontcolouron':self.gui_html_highlight_colour,
        'fontcolourinactive':self.adjust_colour(self.gui_grey, luminosity = 2.0),
        'bgcolourinactive':self.adjust_colour(self.gui_grey, luminosity = 2.0),
        'states':['','on', 'off', 'inactive'],
        'grad_colour':(237,237,245),
        'vline':{'v_pos':0, 'height':16},
        'grad':{'grad_colour':self.adjust_colour(self.gui_timage_colour, luminosity = 3.8), 
                'fraction':1,
                'increment':0.5,
                'step':1,
                },
        'valign':("middle", 0.7),
        'top_left':(3,1),
        'align':'center',
        'titleCase':False,
        'lowerCase':True,
        'continue_mark':True,
        'whitespace_bottom':{'weight':1, 'colour':self.adjust_colour(self.gui_html_bg_colour, luminosity = 0.98)},

      }
    
    buttonItems = {
      "cbtn-refine":
      {
        'txt':'refine',
        'name':'refine',
        'width':('auto', (3,settings_button_width), 0),
        'whitespace_right':{'weight':1, 'colour':self.gui_html_bg_colour},
        },
      "cbtn-solve":
      {
        'txt':'solve',
        'name':'solve',
        'width':('auto', (3,settings_button_width), 0),
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
    

  def make_button_items(self):
    buttonItems = ["btn", "btn-QC", "btn-refine", "btn-solve"]
    for item in buttonItems:
      states = ["on", "off"]
      for state in states:
        image = self.button_items(item, state)
        name =r"gui/images/%s-%s.png" %(item, state)
        OlexVFS.save_image_to_olex(image, name, 2)
        #image.save(r"%s\etc\gui\images\%s-%s.png" %(datadir, item, state), "PNG")

  def make_image_items(self):
    pass
    #import ImageOps
    #imageIndex = {}
    #imageIndex.setdefault("logo", (0, 0, 275, 55))
    #for imag in imageIndex:
      #bgcolour = self.gui_html_bg_colour
      #image = self.image_items(imageIndex[imag])
      #if self.gui_skin_name == "OD":
        #logo_bild = self.removeTransparancy(image.crop((0,0,100,55)), bgcolour)
        #image = self.removeTransparancy(image, (255,255,255))
        #image = image.convert("L")
        #image = ImageOps.colorize(image, (0,10,40), bgcolour) 
        #image.paste(logo_bild, (0,0))
      #name = r"gui/images/%s.png" %(imag)
      #OlexVFS.save_image_to_olex(image, name, 2)
      ##image.save(r"%s\etc\gui\images\%s.png" %(datadir, imag), "PNG")

  def make_icon_items(self):
    iconIndex = {}
    iconIndex.setdefault("anis", (0, 0))
    iconIndex.setdefault("isot", (0, 1))
    iconIndex.setdefault("cell", (0, 2))
    iconIndex.setdefault("center-on-cell", (0, 3))
    iconIndex.setdefault("labels", (0, 4))
    iconIndex.setdefault("base", (0, 5))
    iconIndex.setdefault("info", (0, 6))
    iconIndex.setdefault("ball-and-stick", (0, 7))
    iconIndex.setdefault("bicoloured-bonds", (0, 8))
    iconIndex.setdefault("wireframe", (0, 9))
    iconIndex.setdefault("move", (1, 0))
    iconIndex.setdefault("weight", (1, 1))
    iconIndex.setdefault("ms", (1, 2))
    iconIndex.setdefault("hadd", (1, 3))
    iconIndex.setdefault("xl", (1, 4))
    iconIndex.setdefault("xs", (1, 5))
    iconIndex.setdefault("cif", (1, 6))
    iconIndex.setdefault("clear", (1, 7))
    iconIndex.setdefault("default", (1, 8))
    iconIndex.setdefault("OH", (1, 9))
    iconIndex.setdefault("OH", (2, 0))
    iconIndex.setdefault("htmlpanelswap", (2, 1))
    iconIndex.setdefault("Q", (2, 2))
    iconIndex.setdefault("H", (2, 3))
    iconIndex.setdefault("C", (2, 4))
    iconIndex.setdefault("N", (2, 5))
    iconIndex.setdefault("O", (2, 6))
    iconIndex.setdefault("F", (2, 7))
    iconIndex.setdefault("S", (2, 8))
    iconIndex.setdefault("Cl", (2, 9))
    iconIndex.setdefault("auto", (3, 0))
    iconIndex.setdefault("edit", (3, 1))
    iconIndex.setdefault("tidy", (3, 2))
    iconIndex.setdefault("QC", (3, 3))
    iconIndex.setdefault("sphere-packing", (3, 4))
    iconIndex.setdefault("open", (3, 5))
    iconIndex.setdefault("lines", (3, 6))
    iconIndex.setdefault("swapbg", (3, 7))
    iconIndex.setdefault("dimas", (3, 8))
    iconIndex.setdefault("chn", (3, 9))
    iconIndex.setdefault("sp3", (4, 0))
    iconIndex.setdefault("sp2", (4, 1))
    iconIndex.setdefault("fvar", (4, 2))
    iconIndex.setdefault("occ", (4, 3))
    iconIndex.setdefault("part", (4, 4))
    iconIndex.setdefault("sp2-1H", (4, 5))
    iconIndex.setdefault("sp3-1H", (4, 6))
    iconIndex.setdefault("sp3-2H", (4, 7))
    iconIndex.setdefault("sp3-3H", (4, 8))
    iconIndex.setdefault("sp2-2H", (4, 9))
    iconIndex.setdefault("O-H", (5, 0))
    iconIndex.setdefault("OK", (5, 2))
    iconIndex.setdefault("olex", (5, 3))
    iconIndex.setdefault("cctbx", (5, 4))
    iconIndex.setdefault("movie", (5, 5))
    iconIndex.setdefault("image", (5, 6))
    iconIndex.setdefault("blank", (5, 7))
    iconIndex.setdefault("pt", (5, 8))
    iconIndex.setdefault("text", (5, 9))
    iconIndex.setdefault("delete", (6, 0))
    iconIndex.setdefault("stop", (6, 3))
    iconIndex.setdefault("electron-density", (6, 4))
    iconIndex.setdefault("editatom", (6, 5))
    iconIndex.setdefault("killH", (6, 6))
    iconIndex.setdefault("home", (6, 7))
    iconIndex.setdefault("settings", (6, 8))
    iconIndex.setdefault("dot-arrow-right", (7, 0, {'colourise':'gui_green'}))
    iconIndex.setdefault("dot-arrow-left", (7, 1, {'colourise':'gui_green'}))
    iconIndex.setdefault("dot-arrow-down", (7, 2, {'colourise':'gui_green'}))
    iconIndex.setdefault("dot-arrow-up", (7, 3, {'colourise':'gui_green'}))

    for icon in iconIndex:
      image = self.icon_items(iconIndex[icon])
      name = r"gui/images/toolbar-%s.png" %(icon)
      OlexVFS.save_image_to_olex(image, name, 2)
      #image.save(r"%s\etc\gui\images\toolbar-%s.png" %(datadir, icon), "PNG")

    height = 10
    width = 10
    bg_colour = self.adjust_colour("base", luminosity = 1.6)
    size = (height,width)
    colour = self.gui_html_bg_colour
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    begin = (1,1)
    middle = (width-1,1)
    end = (width/2,height-1)
    draw.polygon((begin, middle, end), self.adjust_colour("bg",  luminosity = 0.7,))
    name = r"gui/images/toolbar-expand.png"
    OlexVFS.save_image_to_olex(image, name, 2)

    colour = self.gui_html_bg_colour
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    begin = (width/2,1)
    middle = (width-1, height-1)
    end = (1,height-1)
    draw.polygon((begin, middle, end), "#ff0000")
    name = r"gui/images/toolbar-collapse.png"
    OlexVFS.save_image_to_olex(image, name, 2)

    height = 15
    width = 2
    colour = self.gui_html_bg_colour
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    begin = (1,1)
    end = (1,height)
    draw.line((begin, end), "#ff0000")
    name = r"gui/images/toolbar-line.png"
    OlexVFS.save_image_to_olex(image, name, 2)      

    ## Little Icons for up, down, delete
    height = 8
    width = 8
    y_offset = 1
    x_border = 2
    bg_colour = self.gui_html_bg_colour
    size = (width,height)
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    begin = (x_border,height-y_offset)
    middle = (width/2,0)
    end = (width-x_border,height-y_offset)
    draw.polygon((begin, middle, end), self.gui_html_font_colour)
    name = r"gui/images/toolbar-up.png"
    OlexVFS.save_image_to_olex(image, name, 2)
    draw.polygon((begin, middle, end), self.adjust_colour(self.gui_html_table_bg_colour, luminosity = 0.9 ))
    name = r"gui/images/toolbar-up-off.png"
    OlexVFS.save_image_to_olex(image, name, 2)

    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    begin = (x_border,y_offset)
    middle = (width/2,height)
    end = (width-x_border,y_offset)
    draw.polygon((begin, middle, end), self.gui_html_font_colour)
    name = r"gui/images/toolbar-down.png"
    OlexVFS.save_image_to_olex(image, name, 2)
    draw.polygon((begin, middle, end), self.adjust_colour(self.gui_html_table_bg_colour, luminosity = 0.9 ))
    name = r"gui/images/toolbar-down-off.png"
    OlexVFS.save_image_to_olex(image, name, 2)

    height = 10
    width = 12
    size = (width,height)
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    font_name = "Vera"
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name

    #self.write_text_to_draw(draw, 
                 #"x", 
                 #top_left=(x_border, -3), 
                 #font_name=font_name, 
                 #font_size=12, 
                 #font_colour="#ff0000")
    #name = r"gui\images\toolbar-delete.png"
    #OlexVFS.save_image_to_olex(image, name, 2)
    
      

  def XXXtimage_style_1(self, item, state):
    width = self.width
    height = 18
    colour = 250, 250, 250
    size = (int(width), int(height))
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    txt = "%s" %item.replace("-", " ")
    
    self.write_text_to_draw(draw, 
                       txt, 
                       top_left=(10,0), 
                       font_name=self.font_name, 
                       font_size=12, 
                       font_colour=self.adjust_colour("base", luminosity = 0.8))

    #border top
    begin = (0, 1)
    end = (width, 1)
    draw.line((begin ,end), fill="#f2f2f2")

    #border bottom
    begin = (0,height-1)
    end = (width, height-1)
    draw.line((begin ,end), fill="#707295")
    begin = (0,height-2)
    end = (width, height-2)
    draw.line((begin ,end), fill="#d3d3d3")

    #border left
    begin = (0,1)
    end = (0, height-1)
    draw.line((begin ,end), fill="#4e5086")

    dup = ImageChops.duplicate(image)
    dup = ImageChops.invert(dup)
    dup = ImageChops.offset(dup, 1, 1)
    image = ImageChops.blend(image, dup, 0.1)
    filename = item
    return image

  def timage_style_h3(self, item, state, bg_luminosity=1.85, bg_saturation=0.9, luminosity_font=1.0, font_name = "Vera"):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
    width = self.width - 8
    height = 16
    base = self.gui_timage_colour
    base = self.gui_timage_colour
    bg_colour = self.adjust_colour("base", luminosity=bg_luminosity, saturation=bg_saturation)
    size = (int(width), int(height))
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    grad_colour = self.adjust_colour(base, luminosity = 1.9)
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
                       font_colour=self.adjust_colour("base", luminosity=luminosity_font, hue=0),
                       image_size = image.size,
                       titleCase=True,
                       valign = ("middle", 0.7)
                     )

    cache = {}
    rad = 1
    image = RoundedCorners.round_image(image, cache, rad)
    
    
    
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

    if state == "off":
      fill=self.adjust_colour("bg", luminosity=0.8)
      self.create_arrows(draw, height, direction="right", colour=fill, type='simple')
    else:
      fill = self.adjust_colour("highlight",  luminosity = 1.1)
      self.create_arrows(draw, height, direction="up", colour=fill, type='simple')
      
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.9))
    filename = item
    return image


  def timage_style_1(self, item, state, font_name="Vera"):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
    width = self.width + 1
    height = 16
    base = self.gui_timage_colour
    bg_colour = self.adjust_colour("base", luminosity = 1.6)
    #bg_colour = self.gui_timage_colour
    size = (int(width), int(height))
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    grad_colour = self.adjust_colour("base", luminosity = 1.8)
    self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=0.2)
    t = item.split("-")
    txt = ""
    for bit in t:
      txt += bit.title() + " "

    transtest = False
    if transtest:
      image = self.makeTransparentText(image, 
                                          txt, 
                                          font_colour=self.adjust_colour("base", luminosity = 0.7),
                                          top_left=(14,1), 
                                          font_size=11, 
                                          font_name=font_name, 
                                        )
      draw = ImageDraw.Draw(image)
    else:
      self.write_text_to_draw(draw, 
                              txt, 
                              top_left=(14,1), 
                              font_name=font_name, 
                              font_size=11, 
                              image_size = image.size,
                              valign=("middle",0.7),
                              titleCase=True,
                              font_colour=self.adjust_colour("base", luminosity = 0.8))
      cache = {}
      rad = 3
      image = RoundedCorners.round_image(image, cache, rad)
      #self.make_border(rad=9,
              #draw=draw,
              #width=width,
              #height=height,
              #bg_colour=bg_colour,
              #border_colour=bg_colour,
              #border_hls = (0, 0.95, 1),
              #shift = 0,
              #cBottomLeft=False,
              #cBottomRight=False,
              #cTopLeft=False,
              #cTopRight=False
            #)

    if state == "off":
      fill=self.adjust_colour("bg", luminosity=0.6)
      self.create_arrows(draw, height, direction="right", colour=fill, type='simple')
    
    else:
      fill = self.adjust_colour("highlight",  luminosity = 1.0)
      self.create_arrows(draw, height, direction="up", colour=fill, type='simple')
#    im = image
#    mark = Image.new('RGBA', (10,10), (255,255,255,255))
#    im = self.watermark(im, mark, 'tile', 0.5)
#    im = self.watermark(im, mark, 'scale', 1.0)
#    im = self.watermark(im, mark, (1, 1), 1)      
#    image = im  
    image = self.add_whitespace(image=image, side='bottom', margin_left=rad, weight=1, colour = self.adjust_colour("bg", luminosity = 0.90))
    image = self.add_whitespace(image=image, side='bottom', margin_left=rad, weight=1, colour = self.adjust_colour("bg", luminosity = 0.95))
    filename = item
    return image


  def tab_items(self, item, state, font_name = "Vera", font_size=13):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
      font_name = "%s Bold" %font_name

    width = int((self.width)/len(self.tabItems)-2)
    height = 17
    base = self.gui_timage_colour
    font_colour = base
    size = (int(width), int(height))
    image = Image.new('RGBA', size, base)
    draw = ImageDraw.Draw(image)
    grad_colour = self.adjust_colour(self.gui_timage_colour, luminosity = 1.1)
    self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=0.4)

    begin = (2, 7)
    middle = (2, 2)
    end = (7, 2)


    if state == "off":
      #triangle left-off
      font_colour = self.adjust_colour("base", luminosity = 1.9, saturation = 1.2)
      draw.polygon((begin, middle, end), self.adjust_colour("base", luminosity = 1.2))
    if state != "off":
      #triangle left-on
      draw.polygon((begin, middle, end), fill=self.gui_html_highlight_colour)
      font_colour = self.gui_html_highlight_colour

    cache = {}
    pos = (('Square'),('Rounded'),('Square'),('Square'))
    image = RoundedCorners.round_image(image, cache, 7, pos=pos)
  
    #self.make_border(rad=11,
            #draw=draw,
            #width=width,
            #height=height,
            #bg_colour=base,
            #border_colour=base,
            #border_hls=(0, 1.3, 1),
            #cBottomLeft=False,
            #cBottomRight=False,
            #cTopLeft=False)
    txt = item.replace("index-", "")

    self.write_text_to_draw(draw, 
                            txt, 
                            align = "right",
                            top_left = (0, 0),
                            max_width = width-5,
                            font_name=font_name, 
                            font_size=font_size, 
                            font_colour=font_colour,
                            image_size = image.size,
                            lowerCase = True,
                            valign=(middle,0.8)
                          )


    #dup = ImageChops.invert(dup)
    #dup = ImageChops.offset(dup, 1, 1)
    #image = ImageChops.blend(image, dup, 0.05)
    image = self.add_whitespace(image=image, side='top', weight=2, colour=self.gui_html_bg_colour)
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.90))
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.95))
    image = self.add_whitespace(image=image, side='right', margin_top=4, weight=1, colour = self.adjust_colour("bg", luminosity = 0.95))
    filename = item
    return image



  def note_items(self, item):
    #cs = self.cs
    base = self.gui_timage_colour
    needs_warning=item[3]
    font_size = 9
    line = int(font_size + font_size * 0.18)
    width = self.width - 25
    if needs_warning:
      w = self.warning.size[0] + 8
      width = width - w

    text = OV.TranslatePhrase(item[0])
    #if olx.IsCurrentLanguage('Chinese') == 'true':
    #  text = text.decode('GB2312')
    
    text = text.split()
    if olx.IsCurrentLanguage('Chinese') == 'true':
      font_name = "Arial UTF"
    else:
      font_name = "Vera"
      if self.gui_image_font_name:
        font_name = self.gui_image_font_name

    font = self.registerFontInstance(font_name, font_size)
      
    inner_border = 0
    border_rad = 0
    bcol = item[1]
    if bcol == 'orange':
      border_colour = {'top':(253, 133, 115),'bottom':(253, 133, 115),'right':(253, 133, 115),'left':(253, 133, 115)}
      bg_colour = (253, 233, 115)
    elif bcol == 'green':
      border_colour = {'top':(91, 255, 91),'bottom':(91, 255, 91),'right':(91, 255, 91),'left':(91, 255, 91)}
      bg_colour = (176, 255 , 176)
    else:
      border_colour = {'top':(253, 133, 115),'bottom':(253, 133, 115),'right':(253, 133, 115),'left':(253, 133, 115)}
      bg_colour = (253, 233, 115)


    dummy_size = (int(width), 18)
    dummy_image = Image.new('RGBA', dummy_size, bg_colour)
    dummy_draw = ImageDraw.Draw(dummy_image)
    number_of_lines = 1
    text_width = 0
    line_txt = ""
    lines = []

    for txt in text:
      txt_size = dummy_draw.textsize(txt + " ", font=font)
      text_width += txt_size[0]
      if text_width > (width - inner_border):
        number_of_lines += 1
        lines.append(line_txt)
        line_txt = ""
        text_width = 0
        line_txt += txt + " "
      else:
        line_txt += txt + " "
    lines.append(line_txt)

    height = (number_of_lines * line) + 5
    font_colour="#4e5086"
    size = (int(width), int(height))
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)

    self.make_border(rad=border_rad,
            draw=draw,
            width=width,
            height=height,
            bg_colour=bg_colour,
            border_colour=bg_colour,
            border_hls = (0, 0.7, 1)
          )

    i = 0
    for txt in lines:
      txt_size = draw.textsize(txt, font=font)
      text_width = txt_size[0]
      self.write_text_to_draw(draw, 
                   txt, 
                   top_left=(((width - text_width)/2), (line * i) + 1), 
                   font_name=font_name, 
                   font_size=font_size, 
                   font_colour=font_colour)
      #draw.text((((width - text_width)/2), (line * i) + 1), "%s" %txt, font=font, fill=font_colour)
      i += 1
    if needs_warning:
      image = self.add_whitespace(image=image, side='left', weight=w, colour=self.gui_html_bg_colour)
      image.paste(self.warning, (2,2), self.warning)

    image = self.add_whitespace(image=image, side='top', weight=2, colour=self.gui_html_bg_colour)

    return image

  def label_items(self, item, font_name = 'Vera'):
    text = item[0]
    width = item[1]
    base = self.gui_timage_colour
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name

    if width == 0:
      width = len(text) * 7
    else:
      width = width
    height = 16
    bg_colour = 250, 250, 250
    font_colour="#4e5086"
    size = (int(width), int(height))
    image = Image.new('RGBA', size, base)
    draw = ImageDraw.Draw(image)

#               border_colour=("#f2f2f2","#f2f2f2","#f2f2f2","#f2f2f2")
    self.make_border(rad=11,
            draw=draw,
            width=width,
            height=height,
            bg_colour=base,
            border_colour=base,
            border_hls = (50, 0.4, 0.4)
          )

    txt = text.replace("-", " ")
    self.write_text_to_draw(draw, 
                       txt, 
                       font_name=font_name, 
                       font_size=10, 
                       font_colour=self.adjust_colour(base, luminosity = 1.2)
                     )
    
#    draw.text((((width-txt_size[0])/2), 0), "%s" %text, font=font, fill=font_colour)
#               image = self.add_whitespace(image=image, side='top', weight=2, colour='white')
    #dup = ImageChops.duplicate(image)
    #dup = ImageChops.invert(dup)
    #dup = ImageChops.offset(dup, 1, 1)
    #image = ImageChops.blend(image, dup, 0.05)
    return image

  def label_items_control(self, item, font_name="Verdana"):
    #cs = self.cs
    base = self.gui_timage_colour
    text = item[0]
    width = item[1]
    if width == 0:
      width = len(text) * 7
    else:
      width = width
    height = 18
    size = (int(width), int(height))
    colour = 100, 100, 160
    font_colour = "#f2f2f2"
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    self.write_text_to_draw(draw, 
                   text.replace("-", " "), 
                   font_name=font_name, 
                   font_size=11, 
                   font_colour=self.adjust_colour(base, luminosity = 1.2)
                 )

    begin = (0,height-2)
    end = (width, height-2)
    draw.line((begin ,end), fill=base)

    begin = (0,0)
    end = (width, 0)
    draw.line((begin ,end), fill=base)

    begin = (0,height-1)
    end = (width, height-1)
    draw.line((begin ,end), fill=cs["white"])

    dup = ImageChops.duplicate(image)
    dup = ImageChops.invert(dup)
    dup = ImageChops.offset(dup, 1, 1)
    image = ImageChops.blend(image, dup, 0.05)
    return image

  def cbtn_items(self, item, state, font_name = "Vera"):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name

    width = 75
    height = 30
    size = (int(width), int(height))
    if state == "off":
      colour = 100, 100, 160
      colour = self.gui_timage_colour
    else:
      colour = 220, 220, 220
      colour = self.gui_html_highlight_colour
    try:  
      font_colour = OV.FindValue('gui_html_font_colour')
    except:
      font_colour = "#777777"
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    self.gradient_bgr(draw, width, height)
    txt = item.replace("cbtn-", "")
    self.write_text_to_draw(draw, 
                               txt, 
                               font_colour=font_colour, 
                               align='centre', 
                               font_name = font_name,
                               font_size = 11,
                               max_width=image.size[0]
                             ) 
    txt = "..."
    self.write_text_to_draw(draw, 
                               txt, 
                               font_colour=font_colour, 
                               font_size=9, 
                               font_name=font_name,
                               top_left=(1,17), 
                               align='right', 
                               max_width=image.size[0]) 
    draw.rectangle((0, 0, image.size[0]-1, image.size[1]-1), outline='#aaaaaa')
    dup = ImageChops.duplicate(image)
    dup = ImageChops.invert(dup)
    dup = ImageChops.offset(dup, 1, 1)
    image = ImageChops.blend(image, dup, 0.05)
    return image


  def button_items(self, item, state, font_name = 'Vera'):
    if self.gui_image_font_name:
      font_name = self.gui_image_font_name
    width = 50
    height = 17
    size = (int(width), int(height))
    if state == "off":
      colour = 100, 100, 160
    else:
      colour = 255, 0, 0
    try:  
      font_colour = OV.FindValue('gui_html_font_colour')
    except:
      font_colour = "#aaaaaa"
    image = Image.new('RGBA', size, colour)
    font_size = 11
    font = self.registerFontInstance(font_name, font_size)
    draw = ImageDraw.Draw(image)
    self.gradient_bgr(draw, width, height)
    txt = item.replace("btn-", "")
    self.write_text_to_draw(draw, txt, font_colour=font_colour, align='centre', max_width=image.size[0]) 
    draw.rectangle((0, 0, image.size[0]-1, image.size[1]-1), outline='#aaaaaa')
    dup = ImageChops.duplicate(image)
    dup = ImageChops.invert(dup)
    dup = ImageChops.offset(dup, 1, 1)
    image = ImageChops.blend(image, dup, 0.05)
    return image

  def image_items(self, idx):
    posX = idx[0]
    posY = idx[1]
    sizeX = idx[2]
    sizeY = idx[3]
    size = (sizeX, sizeY)
    cut = posX, posY, posX + sizeX, posY + sizeY
    colour = 255, 255, 255
    image = Image.new('RGBA', size, colour)
    content = self.imageSource.crop(cut)
    image.paste(content)
    return image

  def icon_items(self, idx):
    d = {}
    border = True
    colourise = False
    idxX = idx[0]
    idxY = idx[1]
    if len(idx) > 2:
      d = idx[2]
    border = d.get('border', True)
    colourise = d.get('colourise', False)
    offset = d.get('offset', False)

    #cs = self.cs
    
    width = 64
    height = 64
    
    size = (int(width), int(height))
    colour = 255, 255, 255,
    image = Image.new('RGBA', size, colour)
    cut = idxY * width, idxX * height, idxY * width + width, idxX * height + height
    
    crop = self.iconSource.crop(cut)
    if colourise:
      crop_colourised = self.colourize(crop, (0,0,0), getattr(self,colourise)) 
      image.paste(crop_colourised, (0,0), crop)
    else:
      image.paste(crop)
      
    
    # strip a bit off the top and the bottom of the square image - it looks better slightly elongated
    strip = int(width * 0.05)
    cut = (0, strip, width, width - strip)
    image = image.crop(cut)
   
    image = image.resize(  ( int(self.gui_html_icon_size) , int(int(self.gui_html_icon_size)*(width-2*strip)/width)  ), Image.ANTIALIAS)
    draw = ImageDraw.Draw(image)
      
    if border:
      draw.rectangle((0, 0, image.size[0]-1, image.size[1]-1), outline='#bcbcbc')
    if offset:
      dup = ImageChops.duplicate(image)
      dup = ImageChops.invert(dup)
      dup = ImageChops.offset(dup, 1, 1)
      image = ImageChops.blend(image, dup, 0.05)
    return image

  def info_bitmaps(self):
    info_bitmap_font = "Verdana"
    info_bitmaps = {
      'refine':{'label':'Refining...',
                'name':'refine',
                'color':'#ff4444',
                'size':(64, 16),
                'font_colour':"#ffffff",
                },
      'solve':{'label':'Solving...',
               'name':'solve',
               'color':'#ff4444',
               'size':(64, 16),
                'font_colour':"#ffffff",
               },
      'working':{'label':'Working...',
                'name':'working',
                'color':'#ff4444',
                'size':(64, 16),
                'font_colour':"#ffffff",
                },
                }
    for bit in info_bitmaps:
      map = info_bitmaps[bit]
      colour = map.get('color', '#ffffff')
      name = map.get('name','untitled')
      txt = map.get('label', '')
      size = map.get('size')
      image = Image.new('RGBA', size, colour)
      draw = ImageDraw.Draw(image)
      self.write_text_to_draw(draw, 
                                 txt, 
                                 top_left = (1, -1),
                                 font_name=info_bitmap_font,
                                 font_size=13,
                                 font_colour = map.get('font_colour', '#000000')
                               )
      OlexVFS.save_image_to_olex(image, name, 2)      

      
  #def gradient_bgr(self, draw, width, height):
    #for i in xrange(16):
      #if i < height/3:
        #incrementA = int(0.6*i*(58/height))
        #incrementB = int(0.6*i*(44/height))
      #elif height/3 < i < (height/3)*2:
        #incrementA = int(1.2*i*(58/height))
        #incrementB = int(1.2*i*(44/height))
      #else:
        #incrementA = int(1.4*i*(58/height))
        #incrementB = int(1.4*i*(44/height))

      #begin = (0,i)
      #end = (width, i)
      #R = int(237-incrementA)
      #G = int(237-incrementA)
      #B = int(245-incrementB)
      ##print i, R,G,B
      #draw.line((begin ,end), fill=(R, G, B))

      
def resize_skin_logo(width):
  IT.resize_skin_logo(width)
  return "Done"
OV.registerFunction(resize_skin_logo)
    

class Boxplot(ImageTools):
  def __init__(self, inlist, width=150, height=50):
    super(Boxplot, self).__init__()
    self.width = width
    self.height = height
    self.list = inlist
    self.getOlexVariables()
  
  def makeBoxplot(self):
    #bgcolour = (255,255,255)
    colour = (255,255,255)
    #outline = (60,60,60)
    bgcolour = self.gui_html_bg_colour
    outline = self.gui_timage_colour
    outline = self.adjust_colour(self.gui_timage_colour,hue=180)
    size = (self.width, self.height)
    plotWidth = int(self.width * 0.8)
    plotHeight = int(self.height * 0.8)
    borderWidth = (self.width - plotWidth)/2
    borderHeight = (self.height - plotHeight)/2
    
    image = Image.new('RGBA', size, bgcolour)
    draw = ImageDraw.Draw(image)
    
    lower = int(self.list[1]*100)
    lowerQ = int(self.list[2]*100)
    median = int(self.list[3]*100)
    upperQ = int(self.list[4]*100)
    upper = int(self.list[5]*100)
    
    xlower = borderWidth + lower * (plotWidth/100)
    xlowerQ = borderWidth + lowerQ * (plotWidth/100)
    xmedian = borderWidth + median * (plotWidth/100)
    xupperQ = borderWidth + upperQ * (plotWidth/100)
    xupper = borderWidth + upper * (plotWidth/100)
    
    ybottom = borderHeight
    ymid = borderHeight + plotHeight/2
    ytop = borderHeight + plotHeight
    
    draw.rectangle((0,0,self.width-1,self.height-1), fill=bgcolour, outline=outline)
    draw.rectangle((xlowerQ,ybottom,xupperQ,ytop), fill=colour, outline=outline)
    draw.line((xmedian,ybottom,xmedian,ytop), fill=self.gui_red) # draw median line
    draw.line((xlower,ymid - plotHeight/4,xlower,ymid + plotHeight/4), fill=outline)
    draw.line((xupper,ymid - plotHeight/4,xupper,ymid + plotHeight/4), fill=outline)
    draw.line((xlower,ymid,xlowerQ,ymid), fill=outline)
    draw.line((xupperQ,ymid,xupper,ymid), fill=outline)
    
    OlexVFS.save_image_to_olex(image, "boxplot.png", 0)
    
if __name__ == "__main__":
  colour = "green"
  size = 90
  type = 'vbar'
  basedir = "C:\Documents and Settings\Horst\Desktop\OlexNZIP"
  #a = BarGenerator(colour = colour, size = size, type = type, basedir = basedir)
  #a.run()
  a = timage(size = 290, basedir = basedir)
  a.run()
  
  #a = Boxplot((0.054999999999999938, 0.56999999999999995, 0.63500000000000001, 0.67000000000000004, 0.68999999999999995, 0.76000000000000001))
  #a.makeBoxplot()