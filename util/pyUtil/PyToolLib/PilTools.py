from __future__ import division
#import PngImagePlugin
import FileSystem as FS
from ArgumentParser import ArgumentParser
import Image
import glob, os
import copy
import ImageDraw, ImageChops, ImageColor, ImageEnhance
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
import olx
import time
global isPro

olx.banner_slide = {}

try:
  import olx
  import olex
  datadir = olx.DataDir()
  basedir = olx.BaseDir()
#       newdir = r"%s\etc\$tools" %datadir
#       if not os.path.isdir(newdir):
#       _mkdir(newdir)
except:
  pass


#self.params.html.highlight_colour.rgb = self.params.html.highlight_colour.rgb
#self.params.html.bg_colour.rgb = self.params.html.bg_colour.rgb
#self.params.html.table_bg_colour.rgb = self.params.html.table_bg_colour.rgb
#self.params.html.font_colour.rgb = self.params.html.font_colour.rgb
#self.params.logo_colour.rgb = self.params.logo_colour.rgb
#self.params.html.link_colour.rgb = self.params.html.link_colour.rgb
#self.params.html.input_bg_colour.rgb = self.params.html.input_bg_colour.rgb
#self.params.html.base_colour.rgb = self.params.html.base_colour.rgb
#self.params.html.table_firstcol_colour.rgb = self.params.html.table_firstcol_colour.rgb
#self.params.button_colouring.rgb = self.params.button_colouring.rgb
#self.params.grey.rgb = self.params.grey.rgb
#self.params.green.rgb = self.params.green.rgb
#self.params.red.rgb = self.params.red.rgb
#self.params.html.base_colour.rgb = self.params.html.base_colour.rgb

class ButtonMaker(ImageTools):
  def __init__(self, btn_dict, type="Generic"):
    super(ButtonMaker, self).__init__()
    self.params = OV.GuiParams()
    self.type = type
    self.btn_dict = btn_dict
    self.max_width = OV.FindValue('gui_htmlpanelwidth', 400)
  def run(self):
    if self.type == "Generic":
      im = self.GenericButtonMaker()
    if self.type == "cbtn":
      im = self.cbtn()

  def GenericButtonMaker(self,  font_name = "Vera", font_size = 14):
    if self.params.image_font_name:
      font_name = self.params.image_font_name
    if self.params.button_font_name:
      font_name = self.params.button_font_name
    icon_height = int(OV.GetParam('gui.skin.icon_size')) * 0.9
    height = int(icon_height)
    width = int(icon_height * 1.1)

    font_colours = {'H':(220,220,220),'C':(100,100,100),'N':(0,80,180),'O':(230,0,5),'AddH':(50,255,50),'-H':(230,0,5), }

    for btn in self.btn_dict:
      width = self.btn_dict[btn].get('width', 18)
      font_size = self.btn_dict[btn].get('font_size', 14)
      d = self.btn_dict[btn]
      image_prefix = d.get("image_prefix", "")
      height = d.get("height", height)
      bgcolour = d.get("bgcolour", self.params.html.bg_colour.rgb)
      txt = d['txt']
      name = d.get('name', txt)
      fontcolouroff = d.get("fontcolouroff", None)
      fontcolouron = d.get("fontcolouron", None)
      grad = d.get('grad', False)
      grad_colour = self.adjust_colour(self.params.html.base_colour.rgb, luminosity = 2.1)
      outline_colour = d.get("outline_colour", self.params.html.table_bg_colour.rgb)
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
          width = int(self.params.htmlpanelwidth)-(number * minus)
          width = (width/number-9)
          if vline:
            vline.setdefault('position', width - 20)
            OV.SetParam('olex2.main_toolbar_vline_position', int(width - OV.GetParam('gui.timage.cbtn.vline')))
      except:
        width = int(width)
      size = (int(width), int(height))

      for state in states:
        font_colour = self.params.html.font_colour.rgb
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
            self.create_arrows(image, draw, height, direction="down", h_space=8, v_space=8, colour=font_colour, type='simple')
          elif state == "on":
            self.create_arrows(image, draw, height, direction="up", h_space=8, v_space=8, colour=font_colour, type='simple')
          elif state == "inactive":
            self.create_arrows(image, draw, height, direction="down", h_space=8, v_space=8, colour=font_colour, type='simple')
        if vline:
          if state == "on" or state == "off":
            if grad:
              colour = self.adjust_colour(grad_colour, luminosity=1)
            else:
              colour = outline_colour
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
            outline_colour = self.params.html.highlight_colour.rgb
        draw.rectangle((0, 0, image.size[0]-1, image.size[1]-1), outline=outline_colour)
        #dup = ImageChops.duplicate(image)
        #dup = ImageChops.invert(dup)
        #dup = ImageChops.offset(dup, 1, 1)
        #image = ImageChops.blend(image, dup, 0.05)
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
    self.params = OV.GuiParams()

    self.fun = tool_fun
    self.param = tool_fun

  def setOlexColours(self):
    import olex
    #OV.SetGrad()

  def setGuiProperties(self):
    olex.m("SetMaterial InfoBox.Text 2309;1,1,1,1;1,1,1,1")
    olex.m("SetMaterial InfoBox.Plane 3077;0,0,0,1;1,1,1,0.5")
    olex.m("SetFont Notes #olex2.fnt:frb_10")
    olex.m("SetFont Default #olex2.fnt:frb_12")
    olex.m("htmguifontsize %s" %self.params.html.font_size)
    olex.m("showwindow help false")
    #olex.m("grad true")

  def setGuiAttributesDefault(self):
    return


  def run_GuiSkinChanger(self):
    verbose = OV.GetParam('olex2.verbose')
    path = r"src/default.png"
    skin = self.params.skin.name
    skin_extension = self.params.skin.extension
    if skin_extension == "None": skin_extension = None
    config = {}
    if "#" in skin:
      #self.set_custom(skin)
      #self.setGuiAttributes()
      self.setGuiAttributesDefault()
      self.setOlexColours()
      path = r"src/default.png"
      import PilTools
    elif "(" in skin:
      self.set_custom(skin)
      self.setGuiAttributesDefault()
      self.setOlexColours()
      path = r"src/default.png"
      import PilTools
    #elif skin == "default":
      #self.setGuiAttributesDefault()
      #self.setGuiAttributes()
      #self.setOlexColours()
      #path = r"src/default.png"
      #import PilTools
##    this is a 'named' skin - ie should have a plugin-folder associated with it
    else:
      self.setGuiAttributesDefault()
      skinpath = r"%s/util/pyUtil/PluginLib/skins/plugin-%sSkin" %(self.basedir, skin)
      # First try to load the skin extension.
      extensionFile = None
      files = []
      if skin_extension:
        try:
          extensionFile = open(r"%s/config%s.txt" %(skinpath, skin_extension), 'r')
          files.append(extensionFile)
        except:
          print "Skin definition file\n%s/config%s.txt\nnot found!" %(skinpath, skin_extension)
      # Then load the actual named skin.
      path = r"%s/config.txt" %(skinpath)
      if os.path.exists(path):
        rFile = open(path, 'r')
      else:
        print "The file %s can not be found" %path
        return
      files.append(rFile)
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
        if verbose:
          print "Using %s skin." %"PilTools_%s" %(skin)
      except ImportError, err:
        print "Import Error: %s (Now Using Default PilTools)" %err
        import PilTools
      except Exception, err:
        raise
      #self.params.html.base_colour.rgb = config.get('GUI_HTMLself.params.html.base_colour.rgb', '#0000ff')
      self.setGuiAttributes(config)
      self.setOlexColours()
    self.resize_skin_logo(self.params.htmlpanelwidth)
    #sNumTitle_instance.run_sNumTitle()
    #timage_instance.run_timage()
    width = OV.FindValue('gui_htmlpanelwidth')
    olx.HtmlPanelWidth(width)
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
    #self.params.html.bg_colour.rgb = "#ffffff"
    #self.params.html.font_colour.rgb = self.RGBToHTMLColor(self.adjust_colour(colour, hue = 180, luminosity = 0.8))
    #self.params.html.link_colour.rgb = "#6f6f8b"
    #self.params.html.table_bg_colour.rgb = self.RGBToHTMLColor(self.adjust_colour(colour, luminosity = 2))
    #self.params.html.table_firstcol_colour.rgb = self.RGBToHTMLColor(self.adjust_colour(colour, luminosity = 1.8))
    #inputself.params.html.bg_colour.rgb = self.RGBToHTMLColor(self.adjust_colour(colour, luminosity = 1.9))
    #self.params.html.base_colour.rgb = self.RGBToHTMLColor(self.adjust_colour(colour, luminosity = 0.9))


class MatrixMaker(ImageTools):
  def __init__(self):
    super(MatrixMaker, self).__init__()
    self.params = OV.GuiParams()

    #import PngImagePlugin
    #import Image
    #import ImageDraw, ImageChops

  def make_3x3_matrix_image(self, name, matrix, text_def="", state=''):
    if state == "on":
      bgcolor = OV.GetParam('gui.html.highlight_colour').rgb
    if state == "off":
      bgcolor = '#dedede'
    width = 52
    height = 55
    size = (width, height)
    font_name = "Arial"
    font_size = 13
    font = self.registerFontInstance(font_name, font_size)
    line_heigth = font_size -2
    im = Image.new('RGBA', size, bgcolor)
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
      if item == -1:
        colour = (255, 0, 0)
      else:
        colour = (100, 100, 100)
      draw.text(begin, "%s" %item, font=font, fill=colour)
      i += 1

    font_size = 10
    line_heigth = font_size -2
    font_name = "Arial"
    font = self.registerFontInstance(font_name, font_size)
    for i in xrange(len(text_def)):
      item = text_def[i].get('txt',"")
      colour = text_def[i].get('font_colour',"")
      w = draw.textsize(str(item), font=font)[0]
      draw.text(((width-w)/2, 35 + line_heigth * i), "%s" %item, font=font, fill=(colour))
    namestate = r"%s%s.png" %(name, state)
    name = r"%s" %(name)
    OlexVFS.save_image_to_olex(im, namestate)
    if state == "off":
      OlexVFS.save_image_to_olex(im, "%s.png" %name)
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
    self.params = OV.GuiParams()

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
    self.params = OV.GuiParams()

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
      #image.save(r"%s\etc\$tools\vBar-%s.png" %(datadir, int(self.size)), "PNG")
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
      colour_a = self.adjust_colour(self.params.green.rgb, luminosity=1.2)


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
    self.params = OV.GuiParams()

    self.thickness = 5
    self.factor = 300
    #self.params.html.bg_colour.rgb = OV.FindValue('gui_htmlself.params.html.bg_colour.rgb')

  def run_MakeAllRBars(self):
    return
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
    image = Image.new('RGBA', size, self.params.html.table_bg_colour.rgb)
    draw = ImageDraw.Draw(image)
    draw.line(((width-2, 0) ,(width-2, height)), fill='#666666')

    font_name = "Verdana Bold"
    font_size = 10
    font = self.registerFontInstance(font_name, font_size)

    txt = r"R1"
    hStart = self.centre_text(draw, txt, font, text_width)
    draw.text((hStart, -1), "%s" %txt, font=font, fill='#666666')

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
    image = self.makeBackgroundTransparent(image,col=self.params.html.table_bg_colour.rgb)

    return image

MakeAllRBars_instance = MakeAllRBars()
OV.registerMacro(MakeAllRBars_instance.run_MakeAllRBars, '')


class sNumTitle(ImageTools):
  def __init__(self, width=None, tool_arg=None):
    super(sNumTitle, self).__init__()
    self.params = OV.GuiParams()
    self.have_connection = False
    width = self.params.htmlpanelwidth
    if not width:
      width = 290
    try:
      width = float(width)
    except:
      width = float(tool_arg)

    if self.have_connection:
      try:
        import SQLFactories
        self.ds = SQLFactories.SQLFactory()
      except:
        self.have_connection = False
        pass

    self.sNum = self.filename
    self.width = int((width) - 22)

  def run_sNumTitle(self, force=False):
    #self.params.html.base_colour.rgb = OV.FindValue('gui_htmlself.params.html.base_colour.rgb')
    self.width = OV.GetParam('gui.htmlpanelwidth') - OV.GetParam('gui.htmlpanelwidth_margin_adjust')
    self.basedir = OV.BaseDir()
    self.filefull = OV.FileFull()
    self.filepath = OV.FilePath()
    self.filename = OV.FileName()
    self.datadir = OV.DataDir()
    self.sNum = self.filename
    self.space_group = OV.olex_function('sg(%h)')
    id_string = self.space_group+self.filefull
    curr_id = OV.GetParam("olex2.sNum_id_string")

    if id_string == curr_id:
      if not force:
        return
    OV.SetParam("olex2.sNum_id_string",id_string)

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

    name = r"sNumTitle.png"
    OlexVFS.save_image_to_olex(image, name, 1)
    OV.CopyVFSFile(name, 'SNUMTITLE',2)



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
    sNum = items["sNum"]
    a = timage()
    return a.make_timage('snumtitle', sNum, 'on', titleCase=False)
    #base_colour = self.params.snumtitle.base_colour.rgb
    #height = self.params.snumtitle.height
    #font_name = self.params.snumtitle.font_name
    #grad_step = self.params.snumtitle.grad_step

    #bg_colour = self.adjust_colour(base_colour, luminosity = self.params.snumtitle.bg_colour_L)
    #grad_colour = self.adjust_colour(base_colour, luminosity = self.params.snumtitle.grad_colour_L)
    #font_colour = self.adjust_colour(base_colour, luminosity = self.params.snumtitle.font_colour_L)


    #width = self.width
    #self.height = height
    #gap = 0
    #bgap = height - gap
    #size = (int(width), int(height))
    ##cs = copy.deepcopy(cS1)

    #if olx.IsFileType("cif") == 'true':
      #base_colour = (255, 0, 0)

    #image = Image.new('RGBA', size, base_colour)

    #draw = ImageDraw.Draw(image)

    #if grad_step:
      #self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=grad_step)
    #cache = {}
    #pos = (('Rounded'),('Rounded'),('Square'),('Square'))
    ##pos = (('Rounded'),('Rounded'),('Rounded'),('Rounded'))
    ##pos = (('Square'),('Square'),('Square'),('Square'))
    #image = RoundedCorners.round_image(image, cache, 2, pos=pos) #used to be 10

    ##border_rad=20
    ##self.make_border(rad=border_rad,
            ##draw=draw,
            ##width=width,
            ##height=height,
            ##bg_colour=base_colour,
            ##border_colour=base_colour,
            ##cBottomLeft=False,
            ##cBottomRight=False,
            ##border_hls = (0, 1.2, 1)
          ##)

    #sNum = items["sNum"]
    #if sNum == "none": sNum = "No Structure"
    #wX, wY = self.write_text_to_draw(draw,
                       #sNum,
                       #top_left=(6, 1),
                       #font_name=font_name,
                       #font_size=17,
                       #image_size = image.size,
                       #valign=("middle", 0.8),
                       #font_colour=self.adjust_colour(base_colour, luminosity = 2.0)
                      #)
    #info_size = OV.GetParam('gui.timage.snumtitle.filefullinfo_size')
    #colour = OV.GetParam('gui.timage.snumtitle.filefullinfo_colour').rgb
    #self.drawFileFullInfo(draw, colour, right_margin=5, height=height, font_size=info_size, left_start=wX + 15)
    #self.drawSpaceGroupInfo(draw, luminosity=1.8, right_margin=3)


    #### Draw this info ONLY if there is a connection to the MySQL database
    ##if self.have_connection:
      ##self.drawDBInfo()

    ##dup = ImageChops.duplicate(image)
    ##dup = ImageChops.invert(dup)
    ##dup = ImageChops.offset(dup, 1, 1)
    ##image = ImageChops.blend(image, dup, 0.05)

    #return image

  #def drawFileFullInfo(self, draw, colour='#ff0000', right_margin=0, height=10, font_name="Verdana", font_size=8, left_start = 40):
    #base_colour = self.params.html.base_colour.rgb
    #txt = OV.FileFull()
    #if txt == "none":
      #return
    #font = self.registerFontInstance(font_name, font_size)
    #tw = (draw.textsize(txt, font)[0])
    #n = int(len(txt)/2)
    #txtbeg = txt[:n]
    #txtend = txt [-n:]
    #while tw > self.width - left_start:
      #txtbeg = txt[:n]
      #txtend = txt [-n:]
      #tw = (draw.textsize("%s...%s" %(txtbeg, txtend), font)[0])
      #n -= 1
    #txt = "%s...%s" %(txtbeg, txtend)

    #wX, wY  = draw.textsize(txt, font)
    #left_start =  (self.width-wX) - right_margin
    #top = height - wY - 2
    #self.write_text_to_draw(draw,
                       #txt,
                       #top_left=(left_start, top),
                       #font_name=font_name,
                       #font_size=font_size,
                       #font_colour=colour)


  #def drawSpaceGroupInfo(self, draw, luminosity=1.9, right_margin=12, font_name="Times Bold"):
    #base_colour = self.params.html.base_colour.rgb
    #left_start = 120
    #font_colour = self.adjust_colour(base_colour, luminosity=luminosity)
    #scale = OV.GetParam('gui.sginfo.scale')
    #try:
      #txt_l = []
      #txt_sub = []
      #txt_norm = []
      #try:
        #txt = OV.olex_function('sg(%h)')
      #except:
        #pass
      #if not txt:
        #txt="ERROR"
      #txt = txt.replace(" 1", "")
      #txt = txt.replace(" ", "")
      #txt_l = txt.split("</sub>")
      #if len(txt_l) == 1:
        #txt_norm = [(txt,0)]
      #try:
        #font_base = "Times"
        ##font_slash = self.registerFontInstance("Times Bold", 18)
        ##font_number = self.registerFontInstance("Times Bold", 14)
        ##font_letter = self.registerFontInstance("Times Bold Italic", 15.5)
        ##font_sub = self.registerFontInstance("Times Bold", 10)
        #font_bar = self.registerFontInstance("%s Bold" %font_base, int(11 * scale))
        #font_slash = self.registerFontInstance("%s Bold" %font_base, int(18 * scale))
        #font_number = self.registerFontInstance("%s Bold" %font_base, int(14 * scale))
        #font_letter = self.registerFontInstance("%s Bold Italic" %font_base, int(15 * scale))
        #font_sub = self.registerFontInstance("%s Bold" %font_base, int(10 * scale))
        #norm_kern = 2
        #sub_kern = 0
      #except:
        #font_name = "Arial"
        #font_bar = self.registerFontInstance("%s Bold" %font_base, 12)
        #font_slash = self.registerFontInstance("%s Bold" %font_base, 18)
        #font_number = self.registerFontInstance("%s Bold" %font_base, 14)
        #font_letter = self.registerFontInstance("%s Bold Italic" %font_base, 15)
        #font_norm = self.registerFontInstance(font_name, 13)
        #font_sub = self.registerFontInstance(font_name, 10)
        #norm_kern = 0
        #sub_kern = 0
      #textwidth = 0
      #for item in txt_l:
        #if item:
          #try:
            #sub = item.split("<sub>")[1]
          #except:
            #sub = ""
          #norm = item.split("<sub>")[0]
          #tw_s = (draw.textsize(sub, font=font_sub)[0]) + sub_kern
          #tw_n = (draw.textsize(norm, font=font_number)[0]) + norm_kern
          #txt_sub.append((sub, tw_s))
          #txt_norm.append((norm, tw_n))
          #textwidth += (tw_s + tw_n)
    #except:
      #txt_l = []
    #if txt_l:
      #i = 0
      #left_start =  (self.width-textwidth) - right_margin -5
      #cur_pos = left_start
      #advance = 0
      #after_kern = 0
      #for item in txt_l:
        #if item:
          #text_normal = txt_norm[i][0]
          #for character in text_normal:
            #if character == "":
              #continue
            #cur_pos += advance
            #cur_pos += after_kern
            #after_kern = 2
            #advance = 0
            #try:
              #int(character)
              #font = font_number
              #top = 0
              #after_kern = 2
            #except:
              #font = font_letter
              #top = -1
              #if character == "P" or character == "I" or character == "C":
                #norm_kern = -2
                #after_kern = 0
                #character = " %s" %character
            #if character == "-":
              #draw.text((cur_pos + 1, -10), "_", font=font_bar, fill=font_colour)
              #draw.text((cur_pos + 1, -9), "_", font=font_bar, fill=font_colour)
              #advance = -1
              #norm_kern = 0
            #elif character == "/":
              #norm_kern = 0
              #after_kern = 0
              #draw.text((cur_pos -2, -3), "/", font=font_slash, fill=font_colour)
              #advance = ((draw.textsize("/", font=font_slash)[0]) + norm_kern) - 1
            #else:
              #draw.text((cur_pos + norm_kern, top), "%s" %character, font=font, fill=font_colour)
              #advance = (draw.textsize(character, font=font)[0]) + norm_kern

          #text_in_superscript = txt_sub[i][0]
          #if text_in_superscript:
            #cur_pos += advance
            #draw.text((cur_pos + sub_kern, 5), "%s" %text_in_superscript, font=font_sub, fill=font_colour)
            #advance = (draw.textsize(text_in_superscript, font=font_sub)[0]) + sub_kern
            #after_kern = -2
            #cur_pos += advance
        #i+= 1


class timage(ImageTools):

  def __init__(self, width=None, tool_arg=None):
    super(timage, self).__init__()
    self.params = OV.GuiParams()

    self.advertise_new = False

    new_l = open("%s/etc/gui/images/advertise_as_new.txt" %OV.BaseDir(),'r').readlines()
    self.new_l = map(lambda s: s.strip(), new_l)

    self.available_width = int(OV.GetParam('gui.htmlpanelwidth') - OV.GetParam('gui.htmlpanelwidth_margin_adjust'))

#    self.available_width = OV.htmlPanelWidth() - OV.GetParam('gui.htmlpanelwidth_margin_adjust')
    self.size_factor = OV.GetParam('gui.skin.size_factor')

    #from PilTools import ButtonMaker
    self.abort = False
    width = self.params.htmlpanelwidth
    if not width:
      width = 350
    else:
      try:
        width = float(width)
      except:
        width = float(tool_arg)
    self.font_name = "Vera"
    self.timer = False
    if self.timer:
      import time
      self.time = time
      self.text_time = 0

    #if tool_arg:
      #args = tool_arg.split(";")
      #if args[0] == "None":
        #self.params.html.base_colour.rgb = OV.FindValue('gui_htmlself.params.html.base_colour.rgb')
      #else:
        #self.params.html.base_colour.rgb = self.HTMLColorToRGB(args[0])
    self.width = int((width) - 22)
    if self.width <= 0: self.width = 10
    icon_source = "%s/etc/gui/images/src/icons.png" %self.basedir
    image_source = "%s/etc/gui/images/src/images.png" %self.basedir
    self.iconSource = Image.open(icon_source)
    self.imageSource = Image.open(image_source)
    self.olex2_has_recently_updated = OV.GetParam('olex2.has_recently_updated')
    sf = 4 #images are four times larger than the nominal width of 350
    sfs = sf * 350/int(self.params.htmlpanelwidth)
    self.sf = sf
    self.sfs = sfs


  def run_timage(self,force_images=False):

    self.highlight_colour = OV.GetParam('gui.html.highlight_colour').rgb
    self.width = OV.GetParam('gui.htmlpanelwidth') - OV.GetParam('gui.htmlpanelwidth_margin_adjust')
    self.available_width = int(OV.GetParam('gui.htmlpanelwidth') - OV.GetParam('gui.htmlpanelwidth_margin_adjust'))



    do_these = []
    if olx.fs_Exists("logo.png") == 'false':
      force_images = True

    if not self.olex2_has_recently_updated:
      if not OV.GetParam('olex2.force_images') and not force_images:
        do_these = [
                "make_cbtn_items",
                "info_bitmaps",
                ]
    if not do_these:
      do_these = ["make_generated_assorted_images",
                  "make_text_and_tab_items",
                  "make_label_items",
                  "make_button_items",
                  "make_cbtn_items",
                  "make_icon_items",
                  "make_image_items",
                  "make_note_items",
                  "make_images_from_fb_png",
                  "make_popup_banners",
                  "info_bitmaps",
                  #"makeTestBanner",
                  "resize_news_image",
                  "create_logo"
                  ]

    #self.params.html.base_colour.rgb = OV.FindValue('gui_htmlself.params.html.base_colour.rgb')
    self.width = int(OV.GetParam('gui.htmlpanelwidth')) - int(OV.GetParam('gui.htmlpanelwidth_margin_adjust'))
    self.basedir = OV.BaseDir()
    self.filefull = OV.FileFull()
    self.filepath = OV.FilePath()
    self.filename = OV.FileName()
    self.datadir = OV.DataDir()
    self.sNum = self.filename

    #MakeAllRBars_instance.run_MakeAllRBars()


    self.params = OV.GuiParams()
    for item in do_these:
      if self.timer:
        t1 = self.time.time()
      a = getattr(self, item)
      a()
      if self.timer:
        print "\t - %s took %.3f s to complete" %(item, self.time.time()-t1)

  def make_popup_banners(self):
    txt_l = [('setup',330), ('help',410), ('tutorial',375)]
    image_source = "%s/etc/gui/images/src/banner.png" %self.basedir
    for item in txt_l:
      txt = item[0]
      IM = Image.open(image_source)
      width = int(item[1])
      height = int(width * IM.size[1]/IM.size[0])
      draw = ImageDraw.Draw(IM)
      self.write_text_to_draw(draw,
                 "%s" %txt,
                 top_left=(440, 32),
                 font_name = 'Vera',
                 font_size=42,
                 titleCase=False,
                 font_colour="#525252",
                 align='left'
                 )
      IM = self.resize_image(IM, (width, height))
      name = "banner_%s.png" %txt
      OlexVFS.save_image_to_olex(IM, name, 2)

  def make_images_from_fb_png(self):
    sf = self.sf
    image_source = self.imageSource
    self.getImageItemsFromTextFile()

    im = image_source
    cut = 0, 52*sf, 27*sf, 76*sf
    crop =  im.crop(cut)
    self.warning =  Image.new('RGBA', crop.size, self.params.html.bg_colour.rgb)
    self.warning.paste(crop, (0,0), crop)
    name = "warning.png"
    self.warning = self.resize_image(self.warning, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    OlexVFS.save_image_to_olex(self.warning, name, 2)

    cut = 140*sf, 58*sf, 170*sf, 81*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_firstcol_colour.rgb)
    IM.paste(crop, (0,0), crop)
    #draw = ImageDraw.Draw(IM)
    #draw.rectangle((0, 0, IM.size[0]-1, IM.size[1]-1), outline='#bcbcbc')
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "HelpImage.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 201*sf, 58*sf, 227*sf, 81*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.params.html.bg_colour.rgb)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM.paste(crop, (0,0), crop)
    #draw = ImageDraw.Draw(IM)
    #draw.rectangle((0, 0, IM.size[0]-1, IM.size[1]-1), outline='#bcbcbc')
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "popout.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 227*sf, 58*sf, 300*sf, 81*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM.paste(crop, (0,0), crop)
    #draw = ImageDraw.Draw(IM)
    #draw.rectangle((0, 0, IM.size[0]-1, IM.size[1]-1), outline='#bcbcbc')
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "return.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 0*sf, 0*sf, 275*sf, 55*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.params.html.bg_colour.rgb)
    IM.paste(crop, (0,0), crop)
    cut = 0*sf, 95*sf, 100*sf, 150*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.params.html.highlight_colour.rgb)
    IM.paste(crop_colouriszed, (190,10), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "olex_help_logo.png"
    OlexVFS.save_image_to_olex(IM, name, 2)


    cut = 140*sf, 154*sf, 220*sf, 175*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    txt_l= ("Prepare",
              "Solve",
              "Refine",
              "Analyze", )
    states = ["on", "off", "", "highlight"]
    for state in states:
      if state == "on":
        colour = self.adjust_colour(self.params.html.highlight_colour.rgb,luminosity=1.3)
      elif state == "off":
        colour = self.adjust_colour(self.params.html.base_colour.rgb,luminosity=1.9)
      elif state == "":
        colour = self.adjust_colour(self.params.html.base_colour.rgb,luminosity=1.9)
      for txt in txt_l:
        #IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
        #crop_colouriszed = self.colourize(crop, (0,0,0), colour)
        crop_colouriszed = crop
        IM =  Image.new('RGBA', crop.size)
        circle = self.makeCharcterCircles(str('1'), im, self.params.html.table_firstcol_colour.rgb, resize = False)
        IM.paste(crop_colouriszed, (0,0), crop)
        IM.paste(circle,(0,0), circle)
        draw = ImageDraw.Draw(IM)
        t = txt.replace("blank"," _ ")
        self.write_text_to_draw(draw,
                     "%s" %t,
                     top_left=(10, 6),
                     font_name = 'Vera',
                     font_size=48,
                     titleCase=True,
                     font_colour="#ff0000",
                     max_width = max_width,
                     align='centre'
                     )
        IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
        name = "comp-%s%s.png" %(txt.replace(" ", "_"), state)
        name = name.lower()
        OlexVFS.save_image_to_olex(IM, name, 2)
        if name == "button_small-blank.png":
          OlexVFS.save_image_to_olex(IM, name, 2)
#          filename = r"%s/button_small-blank.png" %self.datadir
#          IM.save(filename)


    IM =  Image.new('RGBA', crop.size)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "test.png"
    OlexVFS.save_image_to_olex(IM, name, 2)


    available_width = int(OV.GetParam('gui.htmlpanelwidth') - OV.GetParam('gui.htmlpanelwidth_margin_adjust'))
    ## TINY buttons
    cut = 138*sf, 178*sf, 158*sf, 195*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    button_names = self.image_items_d.get("TINY BUTTONS")
    scale = self.sf / 1.2
    tiny_width= OV.GetParam('gui.timage.tinybutton.width')
    self.produce_buttons(button_names, crop, cut, max_width, scale,"_tiny",width=tiny_width)

    ## SMALL buttons
    cut = 90*sf, 178*sf, 138*sf, 193*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    button_names = self.image_items_d.get("SMALL BUTTONS")
    width = OV.GetParam('gui.buttons.small_buttons.width')
    width = int(round(width * self.size_factor,0))
    self.produce_buttons(button_names, crop, cut, max_width,self.sf,"_small",width=width)

    ## TWO buttons in the HTMLpanelWIDTH
    cut = 0*sf, 178*sf, 91*sf, 195*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    button_names = self.image_items_d.get("TWO BUTTONS PER ROW", button_names)
    width = int(available_width/2) - 15
    self.produce_buttons(button_names, crop, cut, max_width,self.sfs,"",width=width)

    ## THREE buttons in the HTMLpanelWIDTH
    cut = 0*sf, 178*sf, 91*sf, 195*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    button_names = self.image_items_d.get("THREE BUTTONS PER ROW", button_names)
    width = int(available_width/3) - 15
    self.produce_buttons(button_names, crop, cut, max_width,self.sfs,"",width=width)

    ## FULL ROW buttons in the HTMLpanelWIDTH
    cut = 0*sf, 193*sf, 275*sf, 211*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    button_names = self.image_items_d.get("FULL ROW", button_names)
    width = available_width - OV.GetParam('gui.htmlpanelwidth_margin_adjust')
    self.produce_buttons(button_names, crop, cut, max_width,self.sfs,"_full",width=width)

    ## G3 BIG BUTTON
    cut = 0*sf, 193*sf, 275*sf, 211*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    button_names = self.image_items_d.get("G3 BIG BUTTON", button_names)
    width = available_width
    self.produce_buttons(button_names, crop, cut, max_width,self.sfs,"_g3_big",width=width)

    
    
    cut = 0*sf, 152*sf, 15*sf, 169*sf
    crop =  im.crop(cut)
    #crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.params.html.table_firstcol_colour.rgb,luminosity=1.98))
    states = ['', 'on', 'off', 'hover', 'hoveron']
    for state in states:
      if state == "off":
        crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.params.green.rgb,luminosity=1.3,saturation=0.7))
      else:
        crop_colouriszed = self.colourize(crop, (0,0,0), self.highlight_colour)

      IM =  Image.new('RGBA', crop.size, OV.GetParam('gui.html.table_firstcol_colour').rgb)
      IM.paste(crop_colouriszed, (0,0), crop)
      name = "info.png"
      info_size_scale = OV.GetParam('gui.timage.info_size_scale')
      IM = self.resize_image(IM, (int((cut[2]-cut[0])/info_size_scale), int((cut[3]-cut[1])/info_size_scale)))
      draw = ImageDraw.Draw(IM)
      #txt = IT.get_unicode_characters('info')
      #txt = "i"
      #self.write_text_to_draw(draw,
      #             txt,
      #             top_left=(6, 0),
      #             font_name = 'Vera',
      #             font_size=14,
      #             translate=False,
      #             font_colour=self.adjust_colour(self.params.html.table_firstcol_colour.rgb,luminosity=0.7))
      OlexVFS.save_image_to_olex(IM, "btn-info%s.png" %(state), 2)

    cut = 16*sf, 156*sf, 26*sf, 166*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.params.html.table_firstcol_colour.rgb,luminosity=1.7))
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM.paste(crop_colouriszed, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "info_tiny.png"
    draw = ImageDraw.Draw(IM)
    txt = IT.get_unicode_characters('info')
    self.write_text_to_draw(draw,
                 txt,
                 top_left=(1, 1),
                 font_name = 'Vera',
                 font_size=6,
                 font_colour=self.params.html.font_colour.rgb)
    OlexVFS.save_image_to_olex(IM, name, 2)


    cut = 16*sf, 156*sf, 26*sf, 166*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.adjust_colour(self.params.html.table_firstcol_colour.rgb,luminosity=0.7))
    IM =  Image.new('RGBA', crop.size, self.params.html.table_firstcol_colour.rgb)
    IM.paste(crop_colouriszed, (0,0), crop)
    draw = ImageDraw.Draw(IM)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    self.write_text_to_draw(draw,
                 "iX",
                 top_left=(2, 1),
                 font_name = 'Vera',
                 font_size=10,
                 font_colour="#ffffff")
    name = "info_tiny_fc.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 16*sf, 156*sf, 26*sf, 166*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.params.html.highlight_colour.rgb)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_firstcol_colour.rgb)
    IM.paste(crop_colouriszed, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    draw = ImageDraw.Draw(IM)
    self.write_text_to_draw(draw,
                 "iY",
                 top_left=(3, -1),
                 font_name = 'Vera Bold Italic',
                 font_size=11,
                 font_colour="#ffffff")
    name = "info_tiny_new.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    ## Create big circles with Writing In
    #cut = 30*sf, 150*sf, 55*sf, 175*sf
    #crop =  im.crop(cut)
    #crop_colouriszed = self.colourize(crop, (0,0,0), self.params.html.table_firstcol_colour.rgb)
    for i in xrange(12):
      self.makeCharcterCircles(str(i), im, self.params.html.table_firstcol_colour.rgb)

    colo =  self.adjust_colour(self.params.green.rgb,saturation=0.7,luminosity=2.1)
    l = ["a", "b", "c", "d", "e", "f"]
    for letter in l:
      self.makeCharcterCircles(letter, im, colo)

    cut = 55*sf, 150*sf, 80*sf, 175*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "settings_small.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 80*sf, 154*sf, 100*sf, 171*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "delete.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 101*sf, 154*sf, 117*sf, 165*sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "delete_small.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 136*sf, 154*sf, 185*sf, 170*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.params.html.base_colour.rgb)
    IM =  Image.new('RGBA', crop.size)
    IM.paste(crop_colouriszed, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "bottom.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 185*sf, 154*sf, 205*sf, 170*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.params.html.highlight_colour.rgb)
    IM =  Image.new('RGBA', crop.size)
    IM.paste(crop_colouriszed, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "next.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 205*sf, 154*sf, 220*sf, 170*sf
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.params.html.highlight_colour.rgb)
    IM =  Image.new('RGBA', crop.size)
    IM.paste(crop_colouriszed, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "previous.png"
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
    crop_colouriszed = self.colourize(crop, (0,0,0), self.params.html.highlight_colour.rgb)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM.paste(crop_colouriszed, (0,0), crop)
    draw = ImageDraw.Draw(IM)
    self.write_text_to_draw(draw,
                 "You are in a Mode",
                 top_left=(5, 1),
                 font_name = 'Vera Bold',
                 font_size=90,
                 font_colour=self.params.html.font_colour.rgb,
                 align='centre',
                 max_width=max_width
                 )
    sfm = sf*0.95
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sfm), int((cut[3]-cut[1])/sfm)))
    name = "pop_background.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

    cut = 140*sf, 98*sf, 400*sf, 140*sf
    max_width = cut[2] - cut[0]
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), self.params.html.highlight_colour.rgb)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM.paste(crop_colouriszed, (0,0), crop)
    draw = ImageDraw.Draw(IM)
    self.write_text_to_draw(draw,
                 "You are in a Mode",
                 top_left=(5, 1),
                 font_name = 'Vera Bold',
                 font_size=90,
                 font_colour=self.params.html.font_colour.rgb,
                 align='centre',
                 max_width=max_width
                 )
    sfm = sf*0.95
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sfm), int((cut[3]-cut[1])/sfm)))
    name = "pop_background.png"
    OlexVFS.save_image_to_olex(IM, name, 2)


    cut = 90*sf, 95*sf, 140*sf, 140*sf
    crop =  im.crop(cut)
#    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    IM =  Image.new('RGBA', crop.size)
    IM.paste(crop, (0,0), crop)
    IM = self.resize_image(IM, (int((cut[2]-cut[0])/sf), int((cut[3]-cut[1])/sf)))
    name = "warning_big.png"
    OlexVFS.save_image_to_olex(IM, name, 2)

  def produce_buttons(self, button_names, crop, cut, max_width,scale,btn_type,width=None):
    states = ["on", "off", "", "highlight", "hover", "hoveron"]
    for state in states:
      if state == "on":
        colour = self.adjust_colour(self.params.html.highlight_colour.rgb,luminosity=1.3)
      elif state == "off":
        #colour = self.adjust_colour(self.params.html.base_colour.rgb,luminosity=1.9)
        colour = self.params.button_colouring.rgb
      elif state == "":
        #colour = self.adjust_colour(self.params.html.base_colour.rgb,luminosity=1.9)
        colour = self.params.button_colouring.rgb
      elif state == "hover":
        colour = self.adjust_colour(self.params.button_colouring.rgb,luminosity=1.1)
      elif state == "hoveron":
        colour = self.adjust_colour(self.params.button_colouring.rgb,luminosity=0.5)

      for txt in button_names:
        if width is None: width = max_width
        use_new = True
        if use_new:
          if txt in self.new_l:
            self.advertise_new = True
          if btn_type =="_tiny":
            button_type = 'tinybutton'
          elif btn_type =="_g3_big":
            button_type = 'g3_big'
          else:
            button_type = 'button'
          IM = self.make_timage(item_type=button_type, item=txt, state=state, width=width, titleCase=False)
          self.advertise_new = False
          name = "button%s-%s%s.png" %(btn_type, txt.replace(" ", "_"), state)
          name = name.lower()
          OlexVFS.save_image_to_olex(IM, name, 2)
        else:


          #IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
          crop = self.make_timage(item_type='button', item="", state=state, width=width)
          crop_colouriszed = self.colourize(crop, (0,0,0), colour)
          IM =  Image.new('RGBA', crop.size)
          IM.paste(crop_colouriszed, (0,0), crop)
          draw = ImageDraw.Draw(IM)
          t = txt.replace("blank"," _ ")
          self.write_text_to_draw(draw,
                       "%s" %t,
                       top_left=(4, 7),
                       font_name = 'Vera',
                       font_size=40,
                       titleCase=False,
                       font_colour=self.params.button_writing,
                       max_width = max_width,
                       align='centre'
                       )
          IM = self.resize_image(IM, (int((cut[2]-cut[0])/scale), int((cut[3]-cut[1])/scale)))
          name = "button%s-%s%s.png" %(btn_type, txt.replace(" ", "_"), state)
          name = name.lower()
          OlexVFS.save_image_to_olex(IM, name, 2)

  def makeTestBanner(self):
    if not OV.FindValue('user_refinement_gui2'):
      return

    name = "banner.png"

    if not OV.GetParam('olex2.force_images'):
      timestamp = olex_fs.Timestamp(name)
      if timestamp:
        if time.time() - timestamp < time.clock():
          return

    bannerbg = "#fdff72"
    bannerbg = self.params.html.base_colour.rgb
    col_0 = self.adjust_colour(bannerbg,luminosity=0.85)
    col_1 = self.adjust_colour(bannerbg,luminosity=1.7)
    cmd_col = "#fff600"
    font_size_l = [42, 13, 13]
    font_l = ["Vera Bold", "Vera", "Vera"]

    txt_items = {"Olex2":{'name':'olex2','pix':0,'row':0,'colour':col_0,
                          'itemstate':"aio-olex2* 1 "},
                 "Prepare":{'name':'prepare','pix':150,'row':0,'colour':col_0,
                            'itemstate':"aio-prepare* 2  "},
                 "Solve":{'name':'solve','pix':390,'row':0,'colour':col_0,
                          'itemstate':"aio-solve* 2 "},
                 "Refine":{'name':'refine','pix':550,'row':0,'colour':col_0,
                           'itemstate':"aio-refine* 2 "},
                 "Analyze":{'name':'analyze','pix':750,'row':0,'colour':col_0,
                            'itemstate':"aio-analyze* 2 "},
                 "Publish":{'name':'publish','pix':1050,'row':0,'colour':col_0,
                            'itemstate':"aio-report* 2 "},

                 "recent":{'name':'recent','pix':-40,'row':1,'colour':col_1,
                             'itemstate':"aio-olex2* 2 aio-olex2-recent* 1"},
                 "history":{'name':'history','pix':-10,'row':2,'colour':col_1,
                             'itemstate':"aio-olex2* 2 aio-olex2-history 1"},
                 "setup":{'name':'setup','pix':20,'row':1,'colour':cmd_col,
                          'itemstate':"aio-olex2* 2 ", 'cmd':'setup'},
                 "configuration":{'name':'configuration','pix':40,'row':2,'colour':cmd_col,
                          'itemstate':"aio-olex2* 2 ", 'cmd':'config'},
                 "settings":{'name':'settings','pix':80,'row':1,'colour':col_1,
                             'itemstate':"aio-olex2* 2 aio-olex2-settings 1"},

                 "reflections":{'name':'reflections','pix':150,'row':1,'colour':col_1,
                                'itemstate':"aio-prepare* 2 aio-prepare-reflections 1", 'cmd':""},
                 "space group":{'name':'space group','pix':190,'row':2,'colour':col_1,
                                'itemstate':"aio-prepare* 2 aio-prepare-space* 1", 'cmd':"sg"},
                 "formula":{'name':'formula','pix':290,'row':1,'colour':col_1,'cmd':"",
                            'itemstate':"aio-prepare* 2 aio-prepare-formula 1", 'cmd':""},

                 "solve":{'name':'solve now','pix':370,'row':2,'colour':col_1,
                              'itemstate':"aio-solve* 2 aio-solve-solve 1"},

                 "assign solution":{'name':'assign solution','pix':430,'row':1,'colour':cmd_col,'cmd':"",
                                    'itemstate':"aio-solve* 2 aio-solve-solve 1", 'cmd':"vss(True)"},

                 "refine":{'name':'refine now','pix':530,'row':2,'colour':col_1,
                               'itemstate':"aio-refine* 2 aio-refine-refine 1", 'Xcmd':"refine>>compaq"},
                 "assemble":{'name':'refine now','pix':560,'row':1,'colour':cmd_col,
                               'itemstate':"aio-refine* 2 aio-refine-refine 1", 'cmd':"compaq"},
                 "assign":{'name':'assign','pix':600,'row':2,'colour':cmd_col,'cmd':"",
                           'itemstate':"aio-refine* 2 aio-refine-refine 1", 'cmd':"ata(1)>>refine>>ata(1)>>compaq"},
                 "anisotropic":{'name':'anisotropic','pix':630,'row':1,'colour':cmd_col,
                                'itemstate':"aio-refine* 2 aio-refine-refine 1", 'cmd':"anis>>refine>>compaq"},
                 "add hydrogen":{'name':'add hydrogen','pix':670,'row':2,'colour':cmd_col,'cmd':"",
                                 'itemstate':"aio-refine* 2 aio-refine-refine 1", 'cmd':"hadd>>refine>>compaq"},

                 "disorder":{'name':'disorder','pix':760,'row':2,'colour':col_1,'cmd':"",
                             'itemstate':"aio-disorder* 2 aio-disorder-disorder 1", 'cmd':""},

                 "contraints&restraints":{'name':'constraints&restraints','pix':850,'row':1,'colour':col_1,'cmd':"",
                             'itemstate':"aio-disorder* 1 ", 'cmd':""},

                 "name atoms":{'name':'atom naming','pix':950,'row':2,'colour':col_1,
                                'itemstate':"aio-publish* 2 aio-publish-naming* 1", 'cmd':""},

                 "measure":{'name':'geometric measurements','pix':1000,'row':1,'colour':col_1,
                                           'itemstate':"aio-geometry* 1", 'cmd':""},

                 "match":{'name':'matching','pix':1050,'row':2,'colour':col_1,
                            'itemstate':"aio-analyze* 2 aio-analyze-match* 1", 'cmd':""},
                 }


    for item in txt_items:
      row = txt_items[item].get("row",0)
      txt = item
      font_size = font_size_l[row]
      font_name = font_l[row]
      txt_dimensions = self.getTxtWidthAndHeight(txt, font_name=font_name, font_size=font_size)
      txt_items[item].setdefault('txt_dimensions',txt_dimensions)


#    bannerbg = self.params.html.font_colour.rgb
    offset = 180
    height = 44
    width = 1700
    size = (width,height)


    IM =  Image.new('RGBA', size, self.params.html.table_bg_colour.rgb)
    IM =  Image.new('RGBA', size, bannerbg)
    #IM =  Image.new('RGBA', size, "#aaaa00")
    draw = ImageDraw.Draw(IM)
    for i in xrange(22):
      lum = 1.00 - ((5-i) * (0.02))
      draw.line(((0,i),(width,i)), fill=self.adjust_colour(bannerbg,luminosity=lum,saturation = lum))
    for i in xrange(22):
      lum = 1.00 - ((5 -i) * (0.02))
      draw.line(((0,height  - i),(width,height - i)), fill=self.adjust_colour(bannerbg,luminosity=lum, saturation = lum))

    margin_top_l = [-3, 12, 26]
    title_l = [True, False, False]
    lower_l = [False, True, True]

    for i in xrange(3):
      for item in txt_items:
        row = txt_items[item].get("row",0)
        if row != i:
          continue
        txt = item
        x_pos = txt_items[item].get("pix",0) + offset
        font_colour = txt_items[item].get("colour")
        font_size = font_size_l[row]
        font_name = font_l[row]
        titleCase = title_l[row]
        lower_case = lower_l[row]
        wX = txt_items[item].get('txt_dimensions')[0]
        wY = txt_items[item].get('txt_dimensions')[1]
        olex_pos = x_pos + wX/2 - (int(self.params.htmlpanelwidth) - 24)/2
        olex_pos = "%.0f" %(olex_pos/10.0)
        if row != 0:
          olx.banner_slide.setdefault(int(olex_pos),txt_items[item])
        OV.SetVar("snum_slide_%s" %txt.lower(),olex_pos)
        self.write_text_to_draw(draw,
                     "%s" %(txt),
                     top_left=(x_pos,margin_top_l[row]),
                     font_name = font_name,
                     font_size=font_size,
                     titleCase=titleCase,
                     lowerCase=lower_case,
                     font_colour=font_colour)
    width = int(self.params.htmlpanelwidth) - 24

    size = (width, height)
    self.banner_make_decoration_image(size)

    for j in xrange(129):
      self.banner_map = "<map name='banner_map'>"
      step = 10
      x1 = 0 + j * step
      x2 = x1 + width
      cut = (x1, 0, x2, height)
      crop =  IM.crop(cut)

#      crop =  Image.new('RGBA', (width, height), bannerbg)
      draw = ImageDraw.Draw(crop)

      margin_top_l = [-3, 8, 24]
      font_size_l = [42, 13, 13]
      font_l = ["Vera Bold", "Vera", "Vera"]
      title_l = [True, False, False]
      lower_l = [False, True, True]

      for i in xrange(3):
        for item in txt_items:
          row = txt_items[item].get("row",0)
          if row != i:
            continue
          x_pos = (txt_items[item].get("pix",0) + offset) - (j * step)
          y_pos = margin_top_l[row]
          wX = txt_items[item].get('txt_dimensions')[0]
          wY = txt_items[item].get('txt_dimensions')[1]
          if row != 0:
            self.banner_map_add_area(txt_items[item], x_pos, y_pos, wX, wY)

      self.banner_map_complete()
      self.banner_write_file(j)
      #crop = self.decorate_banner_image(crop, size, bannerbg, j)
      crop.paste(self.banner_decoration_image[0], mask = self.banner_decoration_image[1])
      name = "banner_%s.png" %j
      OlexVFS.save_image_to_olex(crop, name, 2)
      if j == 0:
        OlexVFS.save_image_to_olex(crop, "banner.png", 2)
    return "Done"

  def banner_map_add_area(self, d, x_pos, y_pos, wX, wY):
    itemstate = d.get('itemstate', "")
    cmd = d.get('cmd', "")
    name = d.get('name',"No Name Found")
    txt = '''
      <area shape="rect"
        coords="%s,%s,%s,%s"
        href="itemstate %s>>%s"
        target="Change GUI2 state to %s">
    '''%(x_pos, y_pos, (x_pos + wX), (y_pos + wY), itemstate, cmd, name)
    self.banner_map += txt


  def banner_map_complete(self):
    txt = '''
    </map>
    <zimg name="BANNER_IMAGE" border="0" src="banner.png" usemap="banner_map">
  <input
    type="slider"
    name = "BANNER_SLIDE"
    width="$eval(html.clientwidth(self)-24)"
    height="20"
    value="GetVar(snum_refinement_banner_slide)"
    bgcolor="$GetVar(gui_htmlself.params.html.tableself.params.html.bg_colour.rgb.rgb)"
    fgcolor="$GetVar(gui_htmlself.params.html.font_colour.rgb)"
    min="0"
    max="119"
    onchange = "SetImage(BANNER_IMAGE,strcat(banner_,GetValue(BANNER_SLIDE).png))"
    onmouseup = "SetVar(snum_refinement_banner_slide,GetValue(BANNER_SLIDE))>>
spy.doBanner(GetVar(snum_refinement_banner_slide))
"
>
'''
    self.banner_map += txt

  def banner_write_file(self, i):
    htm_location = "banner_%i.htm" %i
    OlexVFS.write_to_olex(htm_location, self.banner_map)
    if i == 0:
      htm_location = "banner.htm"
      OlexVFS.write_to_olex(htm_location, self.banner_map)


  def banner_make_decoration_image(self, size):
    marker_colour = "#ff0000"
    width, height = size
    heigth = height -1
    IM =  Image.new('RGBA', size, (0,0,0,0))
    draw = ImageDraw.Draw(IM)


    #for i in xrange(22):
      #trans = 255 - (2 * (22 - i))
      #draw.line(((i,0),(i,height)), fill=(0,0,0, trans))
    #for i in xrange(22):
      #trans = 255 - (2 * i)
      #draw.line(((width -i,0),(width - i,height)), fill=(0,0,0, trans))

    draw.line(((width/2 + 2,0),(width/2 + 2,height)), fill=(0,0,0,125))


    #Draw triangle shadow
    begin = (width/2 - 3, height)
    middle = (width/2,height -6)
    end = (width/2 + 7, height)
    draw.polygon((begin, middle, end), (0,0,0,90))

    begin = (width/2 - 5, height)
    middle = (width/2,height -6)
    end = (width/2 + 5, height)
    draw.polygon((begin, middle, end), marker_colour)

    begin = (width/2 - 3, 0)
    middle = (width/2,6)
    end = (width/2 + 7, 0)
    draw.polygon((begin, middle, end), (0,0,0,90))

    begin = (width/2 - 5, 0)
    middle = (width/2,6)
    end = (width/2 + 5, 0)
    draw.polygon((begin, middle, end), marker_colour)

    draw.line(((width/2,0),(width/2,height)), fill=marker_colour)
    division_col = IT.HTMLColorToRGB(self.params.html.base_colour.rgb) + (255,)
    left = width/2
    right = width/2
    for j in xrange(40):
      y1 = 1
      if j % 2:
        y1 = 2
      right += 8
      draw.line(((right,(height/2)-y1), (right, (height/2)+y1)), fill=division_col)
      left -= 10
      draw.line(((left,(height/2)-y1),(left,(height/2)+y1)), fill=division_col)
    r,g,b,a = IM.split()
    #paste the overlay into the base image in the boundingBox using mask as a filter
    self.banner_decoration_image = (IM,a)

  def decorate_banner_image(self, crop, size, bannerbg, i):
    marker_colour = "#ff0000"
    width, height = size
    heigth = height -1
    draw = ImageDraw.Draw(crop)

    #for j in xrange(22):
      #region = (j,0,j+1,height)
      #region_im =  crop.crop(region)
      #region_im = region_im.point(lambda i: i * 1 - 0.01 * (22-j))
      #region_im = ImageEnhance.Brightness(region_im).enhance(1 - j * 0.01)
      #crop.paste(region_im, region)
    #for j in xrange(22):
      #region = (width - j - 2  ,0,width - j , height)
      #region_im =  crop.crop(region)
      #region_im = region_im.point(lambda i: i * 1 - 0.01 * j)
      #crop.paste(region_im, region)


    ## Shadow Marker Line
    region = (int(width/2) + 2,0,int(width/2) + 3,height)
    region_im =  crop.crop(region)
#    region_im = region_im.point(lambda i: i * 0.8)
    region_im = ImageEnhance.Brightness(region_im).enhance(1.1)
    crop.paste(region_im, region)


    begin = (width/2 - 5, height)
    middle = (width/2,height -6)
    end = (width/2 + 5, height)
    draw.polygon((begin, middle, end), marker_colour)
    begin = (width/2 - 5, 0)
    middle = (width/2,6)
    end = (width/2 + 5, 0)
    draw.polygon((begin, middle, end), marker_colour)

    draw.line(((width/2,0),(width/2,height)), fill=marker_colour)

    #division_col = "#ababab"
    division_col = self.params.html.base_colour.rgb
    left = width/2
    right = width/2
    for j in xrange(40):
      y1 = 1
      if j % 2:
        y1 = 2
      right += 8
      draw.line(((right,(height/2)-y1), (right, (height/2)+y1)), fill=division_col)
      left -= 10
      draw.line(((left,(height/2)-y1),(left,(height/2)+y1)), fill=division_col)
    return crop


  def makeCharcterCircles(self, character, im, colour, resize = True):
    cut = 30*self.sf, 150*self.sf, 55*self.sf, 175*self.sf
    crop =  im.crop(cut)
    IM =  Image.new('RGBA', crop.size, self.params.html.table_bg_colour.rgb)
    #IM =  Image.new('RGBA', crop.size)
    crop_colouriszed = self.colourize(crop, (0,0,0,0), colour)
    IM.paste(crop_colouriszed, (0,0), crop)
    draw = ImageDraw.Draw(IM)
    self.write_text_to_draw(draw,
                 "%s" %(character),
                 top_left=(24, 6),
                 font_name = 'Vera Bold',
                 font_size=70,
                 font_colour=self.params.html.font_colour.rgb)
    if resize:
      IM = self.resize_image(IM, (int((cut[2]-cut[0])/self.sf), int((cut[3]-cut[1])/self.sf)))
    name = "circle_%s.png" %character
    OlexVFS.save_image_to_olex(IM, name, 2)
    return IM


  def getImageItemsFromTextFile(self):
    path = "%s/etc/gui/images/image_items.txt" %self.basedir
    im_d = {}
    if not os.path.exists(path):
      return
    rFile = open(path, 'r')
    lines = rFile.readlines()
    for line in lines:
      if line.startswith("["):
        key = line.strip().strip('[').strip(']')
        im_d.setdefault(key,[])
      elif line.startswith("#"):
        continue
      else:
        if key:
          im_d[key].append(line.strip())
    self.image_items_d = im_d


  def create_logo(self):
    factor = 4

    #create a new image
    width = self.width * factor
    size = (width, 55 * factor)
    IM =  Image.new('RGBA', size, OV.GetParam('gui.html.bg_colour').rgb)

    #this is the source of the images required for the logo
    image_source = "%s/etc/gui/images/src/images.png" %self.basedir
    im = Image.open(image_source)

    #first cut the small logo picture from the source
    cut_right = (int(OV.GetParam('gui.htmlpanelwidth')) - 213) * factor
    if cut_right > 1400:
      cut_right = 1400
    cut = 0, 228, cut_right, 430 * factor #the area of the small image
    crop = im.crop(cut)
    #crop_colourised = self.colourize(crop, (0,0,0), self.params.logo_colour.rgb)
    IM.paste(crop, (0,0), crop)

    #then cut the actual logo
    cut = 200 * factor, 0, 372 * factor, 55 * factor #the area of the olex writing
    crop =  im.crop(cut)
    crop_colouriszed = self.colourize(crop, (0,0,0), OV.GetParam('gui.logo_colour').rgb)
    IM.paste(crop_colouriszed, (width-(175 * factor),0), crop)


    # Add Version and Tag info
    size = (203,95)
    new = Image.new('RGB', size, self.params.html.highlight_colour.rgb)
    draw = ImageDraw.Draw(new)
    x = 0
    y = 0

    # Add Tag
    txt = "%s" %OV.GetTag()
    self.write_text_to_draw(draw,
                 "%s" %(txt),
                 top_left=(5, 5),
                 font_name = 'Vera',
                 font_size=38,
                 font_colour=self.adjust_colour(self.params.html.font_colour.rgb, luminosity = 0.8))
#                 font_colour='#ffffff')

    # Add version Number
    txt = "%s" %OV.GetSVNVersion()
    self.write_text_to_draw(draw,
                 "%s" %(txt),
                 top_left=(5, 45),
                 font_name = 'Vera Bold',
                 font_size=43,
                 font_colour='#ffffff')

    new = new.rotate(90)
    IM.paste(new, (0, 0))


    #finally resize and save the final image
    IM = self.resize_image(IM, (self.width, 55))
    name = r"logo.png"
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
    colour = self.params.html.table_firstcol_colour.rgb
    #colour = "#00ff00"
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    font_name = "Times Bold Italic"
    self.write_text_to_draw(draw,
                       "iZ",
                       top_left=(1, -1),
                       font_name=font_name,
                       font_size=14,
                       font_colour=self.params.html.font_colour.rgb)
    name = "infos.png"
    OlexVFS.save_image_to_olex(image, name, 2)



    ## Make the wedges for the Q-Peak slider
    scale = 4
    width = (int(self.params.htmlpanelwidth) - 81)
    height = 8

    size = (width*scale, height*scale)
    colour = self.params.html.table_bg_colour.rgb
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)

    left = 8*scale
    right = (int(width/2) -3) *scale
    top = 1*scale
    bottom = height*scale

    begin = (left, bottom)
    middle = (right, top)
    end = (right, bottom)
    draw.polygon((begin, middle, end), self.adjust_colour(self.params.html.table_firstcol_colour.rgb, luminosity = 0.9))

    begin = (left, top)
    middle = (right, top)
    end = (left, bottom)
    draw.polygon((begin, middle, end), self.adjust_colour(self.params.html.table_firstcol_colour.rgb, luminosity = 1.1))

    left = (int(width/2)+ 10)*scale
    right = width*scale

    begin = (left,  top)
    middle = (right, top)
    end = (left, bottom)
    draw.polygon((begin, middle, end), self.adjust_colour(self.params.html.table_firstcol_colour.rgb, luminosity = 0.9))

    begin = (left, bottom)
    middle = (right, top)
    end = (right, bottom)
    draw.polygon((begin, middle, end), self.adjust_colour(self.params.html.table_firstcol_colour.rgb, luminosity = 1.1))

    begin = ((int(width/2)+ 2)*scale, (1*scale) + 1)
    m1 = ((int(width/2)+ 5)*scale, (1*scale) +1)
    m2 = ((int(width/2)+ 5)*scale, (height*scale) -1)
    end = ((int(width/2)+ 2)*scale, (height*scale) -1)
    draw.polygon((begin, m1, m2, end), self.adjust_colour(self.params.html.table_firstcol_colour.rgb, luminosity = 0.8))


    image = image.resize((width, height),Image.ANTIALIAS)
    name = "qwedges.png"
    OlexVFS.save_image_to_olex(image, name, 2)

  def make_text_and_tab_items(self):
    bitmap = "working"
    if olx.fs_Exists(bitmap) == 'true':
      olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
    textItems = []
    textItems.append("autochem")
    tabItems = []
    g3tabItems = ['g3-solve', 'g3-refine', 'g3-image', 'g3-report', 'g3-tools']

    directories = ["etc/gui", "etc/news", "etc/gui/blocks", "etc/gui/snippets", "etc/gui/g3", "etc/tutorials"]
    rFile = open("%s/etc/gui/blocks/index-tabs.htm" %(self.basedir), 'r')
    for line in rFile:
      t = line.split("<!-- #include ")[1]
      t = t.split()[0]
      t = t.split('-')[1]
      if t not in tabItems:
        tabItems.append(t)
    tabItem_l = [tabItems, g3tabItems]
    self.tabItems = tabItems
    for directory in directories:
      for htmfile in OV.ListFiles("%s/%s/*.htm" %(self.basedir,  directory)):
        f = (htmfile.replace('\\', '/').split('/')[-1:])
        f = f[0].split(".")[0]
        if f.split("-")[0] != "index" and f[0] != "_":
          f = f.replace("-and-", "-&-")
          if f not in textItems:
            textItems.append(f)
        #elif f[0] != "_":
        #  tabItems.append(f)
    for item in ('solution-settings-h3-solution-settings-extra', 'refinement-settings-h3-refinement-settings-extra',
                 'report-settings',):
      textItems.append(item)

    for item in textItems:
      if self.timer:
        t1 = time.time()
      states = ["on", "off", "highlight", "", "hover", "hoveron"]
      name = ""
      for state in states:
        if "h3" in item:
          try:
            img_txt = item.split("-h3-")[1]
          except IndexError:
            img_txt = item.replace('h3-','')
          if img_txt.lower() in self.new_l:
            self.advertise_new = True
          image = self.make_timage('h3', img_txt, state)
          self.advertise_new = False
          name = "h3-%s%s.png" %(item, state)
        else:
          img_txt = item
          if img_txt in self.new_l:
            self.advertise_new = True
          image = self.make_timage('h1', img_txt, state)
          self.advertise_new = False
          name = "h2-%s%s.png" %(item, state)
          name = name.replace(".new.","")

        if name:
          OlexVFS.save_image_to_olex(image, name.lower(), 2)
          #name = "h2-%s-%s.png" %(item, state)
          #image.save("C:/tmp/%s" %name)
      if self.timer:
        t = self.time.time()-t1
        self.text_time += t
        print "\t - %.3f [%.1f]- to complete %s" %(self.time.time()-t1, self.text_time, item)

    for tabItems in tabItem_l:
      if self.timer:
        t1 = time.time()
      for item in tabItems:
        states = ["on", "off", "highlight", "", "hover", "hoveron"]
        for state in states:
          use_new = True
          if use_new:
            width = int(self.available_width/len(tabItems)) - 1
            image = self.make_timage(item_type='tab', item=item.lstrip('g3-'), state=state, width=width)
          else:
            image = self.tab_items(item, state)

          name = r"tab-%s%s.png" %(item, state)
          OlexVFS.save_image_to_olex(image, name, 2)
        if self.timer:
          print "\t - %s took %.3f s to complete" %(item, self.time.time()-t1)

        #name = r"tab-%s-%s.png" %(item, state)
        #image.save("C:/tmp/%s" %name)
        #image.save(r"%s\etc\$tab-%s-%s.png" %(datadir, item.split("index-")[1], state), "PNG")

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
      name = r"note-%s.png" %(item[2])
      OlexVFS.save_image_to_olex(image, name, 2)
      #image.save(r"%s\etc\note-%s.png" %(datadir, item[2]), "PNG")

  def make_label_items(self):
    labelItemsControl = [("Start",0), ("Suffix",0), ("Type",0), ("Cycles",0), ("Q-peaks",0),("Axis",0),("Deg",0),("Step",0),("No.",0), ("More",0) ]
    for item in labelItemsControl:
      #image = self.label_items_control(item)
      image = self.label_items(item)
      name = r"label-%s.png" %(item[0])
      OlexVFS.save_image_to_olex(image, name, 2)
      #image.save(r"%s\etc\$label-%s.png" %(datadir, item[0]), "PNG")

    labelItems = [("Display", 50), ("A-Type", 50), ("Model", 50)]
    for item in labelItems:
      image = self.label_items(item)
      name = r"label-%s.png" %(item[0])
      OlexVFS.save_image_to_olex(image, name, 2)
      #image.save(r"%s\etc\$label-%s.png" %(datadir, item[0]), "PNG")

  def make_cbtn_items(self, font_name = 'Vera'):
    new_style = True
    if new_style:
      buttons = ['Solve', 'Refine', 'Report']
      states = ['on', 'off', 'inactive', 'highlight', 'hover', 'hoveron']
      for state in states:
        for item in buttons:
          width = int(round(self.available_width/3,0)) - 5
          cut = width - OV.GetParam('gui.timage.cbtn.vline')
          if cut > width:
            cut = width - 1
            print ("WARNING: HtmlPanelWidth is smaller than intended. Some GUI images may not display correctly")
          image = self.make_timage(item_type='cbtn', item=item, state=state, width=width)
          images = IT.cut_image(image,(cut,))
          i = 0
          for image in images:
            prefixes = ['btn', 'cbtn']
            name = '%s-%s%s.png' %(prefixes[i], item.lower(), state)
            OlexVFS.save_image_to_olex(image,name, 2)
            #image.save("C:/tmp/%s" %name)
            i += 1


    else:
      if self.params.image_font_name:
        font_name = self.params.image_font_name
        font_name = "%s Bold" %font_name

      settings_button_width = 0
      cbtn_buttons_height = 22

      all_cbtn_buttons = {
          'image_prefix':'cbtn',
          'height':cbtn_buttons_height,
          'font_name':font_name,
          #'bgcolouroff':self.adjust_colour(self.params.html.base_colour.rgb, luminosity = 1.0),
          #'bgcolouron':self.params.html.base_colour.rgb,
          #'fontcolouroff':self.adjust_colour(self.params.html.base_colour.rgb, luminosity = 1.6),
          #'fontcolouron':self.params.html.highlight_colour.rgb,
          'bgcolouroff':self.params.html.bg_colour.rgb,
          'bgcolouron':self.params.html.bg_colour.rgb,
          'fontcolouroff':self.params.html.base_colour.rgb,
          'fontcolouron':self.params.html.highlight_colour.rgb,
          'fontcolourinactive':self.adjust_colour(self.params.grey.rgb, luminosity = 2.0),
          'bgcolourinactive':self.adjust_colour(self.params.grey.rgb, luminosity = 2.0),
          'states':['','on', 'off', 'inactive', 'highlight'],
          'outline_colour':self.adjust_colour(self.params.html.table_bg_colour.rgb, luminosity = 0.8),
          'grad_colour':(237,237,245),
          'vline':{'v_pos':0, 'height':18},
          #'grad':{'grad_colour':self.adjust_colour(self.params.timage_colour, luminosity = 1.8),
                  #'fraction':1,
                  #'increment':0.5,
                  #'step':1,
                  #},
          'valign':("middle", 0.7),
          'top_left':(3,1),
          'align':'center',
          'titleCase':False,
          'lowerCase':True,
          'continue_mark':True,
          'whitespace_bottom':{'weight':1, 'colour':self.adjust_colour(self.params.html.bg_colour.rgb, luminosity = 0.98)},

        }

      buttonItems = {
        "cbtn-refine":
        {
          'txt':'refine',
          'name':'refine',
          'width':('auto', (3,settings_button_width), 0),
          'whitespace_right':{'weight':1, 'colour':self.params.html.bg_colour.rgb},
          },
        "cbtn-solve":
        {
          'txt':'solve',
          'name':'solve',
          'width':('auto', (3,settings_button_width), 0),
          'whitespace_right':{'weight':1, 'colour':self.params.html.bg_colour.rgb},
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
      states = ["on", "off", "highlight", "hover", "hoveron"]
      for state in states:
        image = self.button_items(item, state)
        name =r"%s-%s.png" %(item, state)
        OlexVFS.save_image_to_olex(image, name, 2)
        #image.save(r"%s\etc\$%s-%s.png" %(datadir, item, state), "PNG")

  def make_image_items(self):
    pass
    #import ImageOps
    #imageIndex = {}
    #imageIndex.setdefault("logo", (0, 0, 275, 55))
    #for imag in imageIndex:
      #bgcolour = self.params.html.bg_colour.rgb
      #image = self.image_items(imageIndex[imag])
      #if self.params.skin.name == "OD":
        #logo_bild = self.removeTransparancy(image.crop((0,0,100,55)), bgcolour)
        #image = self.removeTransparancy(image, (255,255,255))
        #image = image.convert("L")
        #image = ImageOps.colorize(image, (0,10,40), bgcolour)
        #image.paste(logo_bild, (0,0))
      #name = r"%s.png" %(imag)
      #OlexVFS.save_image_to_olex(image, name, 2)
      ##image.save(r"%s\etc\$%s.png" %(datadir, imag), "PNG")

  def make_icon_items(self):
    base_colour = self.params.html.base_colour.rgb

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
    iconIndex.setdefault("center", (2, 8, {'colourise':self.params.html.highlight_colour.rgb}))
    iconIndex.setdefault("Cl", (2, 9))
    iconIndex.setdefault("auto", (3, 0))
    iconIndex.setdefault("edit", (3, 1))
    iconIndex.setdefault("tidy", (3, 2))
    iconIndex.setdefault("blank", (3, 3))
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
    iconIndex.setdefault("QH", (5, 7))
    iconIndex.setdefault("QC", (5, 8))
    iconIndex.setdefault("text", (5, 9))
    iconIndex.setdefault("delete", (6, 0))
    iconIndex.setdefault("stop", (6, 3))
    iconIndex.setdefault("eden", (6, 4))
    iconIndex.setdefault("editatom", (6, 5))
    iconIndex.setdefault("killH", (6, 6))
    iconIndex.setdefault("home", (6, 7))
    iconIndex.setdefault("settings", (6, 8))
    iconIndex.setdefault("dot-arrow-right", (7, 0, {'colourise':self.params.green.rgb}))
    iconIndex.setdefault("dot-arrow-left", (7, 1, {'colourise':self.params.green.rgb}))
    iconIndex.setdefault("dot-arrow-down", (7, 2, {'colourise':self.params.green.rgb}))
    iconIndex.setdefault("dot-arrow-up", (7, 3, {'colourise':self.params.green.rgb}))
    iconIndex.setdefault("polyhedra", (6, 9))

    also_make_small_icons_l = ['open']

    for icon in iconIndex:
      states = ["on", "off", "hover", "", "hoveron", "highlight"]
      for state in states:
        image = self.icon_items(iconIndex[icon], state)
        name = r"toolbar-%s%s.png" %(icon,state)
        name = name.lower()
        OlexVFS.save_image_to_olex(image, name, 2)
      #image.save(r"%s\etc\$toolbar-%s.png" %(datadir, icon), "PNG")

      if icon in also_make_small_icons_l:
        states = ["on", "off", "hover", "", "hoveron", "highlight"]
        for state in states:
          image = self.icon_items(iconIndex[icon], state, icon_size=OV.GetParam('gui.html.combo_height'))
          name = r"toolbar_small-%s%s.png" %(icon,state)
          name = name.lower()
          OlexVFS.save_image_to_olex(image, name, 2)

    height = 10
    width = 10
    bg_colour = self.adjust_colour(base_colour, luminosity = 1.6)
    size = (height,width)
    colour = self.params.html.bg_colour.rgb
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    begin = (1,1)
    middle = (width-1,1)
    end = (width/2,height-1)
    draw.polygon((begin, middle, end), self.adjust_colour("bg",  luminosity = 0.7,))
    name = r"toolbar-expand.png"
    OlexVFS.save_image_to_olex(image, name, 2)

    colour = self.params.html.bg_colour.rgb
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    begin = (width/2,1)
    middle = (width-1, height-1)
    end = (1,height-1)
    draw.polygon((begin, middle, end), "#ff0000")
    name = r"toolbar-collapse.png"
    OlexVFS.save_image_to_olex(image, name, 2)


    image = Image.new('RGBA', (1,1), (0,0,0,0))
    OlexVFS.save_image_to_olex(image, "blank.png", 2)

    height = 15
    width = 2
    colour = self.params.html.bg_colour.rgb
    image = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(image)
    begin = (1,1)
    end = (1,height)
    draw.line((begin, end), "#ff0000")
    name = r"toolbar-line.png"
    OlexVFS.save_image_to_olex(image, name, 2)

    ## Little Icons for up, down, delete
    height = 8
    width = 8
    y_offset = 1
    x_border = 2
    bg_colour = self.params.html.bg_colour.rgb
    size = (width,height)
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    begin = (x_border,height-y_offset)
    middle = (width/2,0)
    end = (width-x_border,height-y_offset)
    draw.polygon((begin, middle, end), self.params.html.font_colour.rgb)
    name = r"toolbar-up.png"
    OlexVFS.save_image_to_olex(image, name, 2)
    draw.polygon((begin, middle, end), self.adjust_colour(self.params.html.table_bg_colour.rgb, luminosity = 0.9 ))
    name = r"toolbar-up-off.png"
    OlexVFS.save_image_to_olex(image, name, 2)

    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    begin = (x_border,y_offset)
    middle = (width/2,height)
    end = (width-x_border,y_offset)
    draw.polygon((begin, middle, end), self.params.html.font_colour.rgb)
    name = r"toolbar-down.png"
    OlexVFS.save_image_to_olex(image, name, 2)
    draw.polygon((begin, middle, end), self.adjust_colour(self.params.html.table_bg_colour.rgb, luminosity = 0.9 ))
    name = r"toolbar-down-off.png"
    OlexVFS.save_image_to_olex(image, name, 2)

    height = 10
    width = 12
    size = (width,height)
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    font_name = "Vera"
    if self.params.image_font_name:
      font_name = self.params.image_font_name

    #self.write_text_to_draw(draw,
                 #"TINY BUTTONS",
                 #top_left=(x_border, -3),
                 #font_name=font_name,
                 #font_size=12,
                 #font_colour="#ff0000")
    #name = r"$toolbar-delete.png"
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
                       font_colour=self.adjust_colour(base_colour, luminosity = 0.8))

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
    if self.params.image_font_name:
      font_name = self.params.image_font_name
    width = self.width - 8

    if "GB" in self.gui_language_encoding: #--!--
      height = 18
    else:
      height = 16
    base_colour = self.params.html.base_colour.rgb
    bg_colour = self.adjust_colour(base_colour, luminosity=bg_luminosity, saturation=bg_saturation)
    size = (int(width), int(height))
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)
    grad_colour = self.adjust_colour(base_colour, luminosity = 1.9)
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
                       font_colour=self.adjust_colour(base_colour, luminosity=luminosity_font, hue=0),
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

    if self.advertise_new:
      self.draw_advertise_new(draw, image)

    if state == "off":
      fill=self.adjust_colour("bg", luminosity=0.8)
      self.create_arrows(image, draw, height, direction="right", colour=fill, type='simple')
    else:
      fill = self.adjust_colour("highlight",  luminosity = 1.1)
      self.create_arrows(image, draw, height, direction="up", colour=fill, type='simple')

    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.9))
    filename = item
    return image


  def timage_style_1(self, item, state, font_name="Vera"):

    base_colour = self.params.html.base_colour.rgb

    bg_colour_L = self.params.timage.bg_colour_L
    grad = self.params.timage.grad
    grad_colour_L = self.params.timage.grad_colour_L
    grad_step = self.params.timage.grad_step
    font_colour_L = self.params.timage.font_colour_L

    bg_colour = self.adjust_colour(base_colour, luminosity = bg_colour_L)
    grad_colour = self.adjust_colour(base_colour, luminosity = grad_colour_L)
    font_colour = self.adjust_colour(base_colour, luminosity = font_colour_L)

    height = self.params.timage.height
    font_name = self.params.timage.font_name
    font_size = self.params.timage.font_size
    corner_rad = self.params.timage.corner_rad

    top = self.params.timage.top
    left = self.params.timage.left

    width = self.width + 1

    if "GB" in self.gui_language_encoding: #--!--
      height = height + 2
    else:
      height = height

    size = (int(width), int(height))
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)

    if grad:
      self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=grad_step)
    t = item.split("-")
    txt = ""
    for bit in t:
      txt += bit.title() + " "

    transtest = False
    if transtest:
      image = self.makeTransparentText(image,
                                          txt,
                                          font_colour=font_colour,
                                          top_left=(left,top),
                                          font_size=font_size,
                                          font_name=font_name,
                                        )
      draw = ImageDraw.Draw(image)
    else:
      self.write_text_to_draw(draw,
                              txt,
                              top_left=(left,top),
                              font_name=font_name,
                              font_size=font_size,
                              image_size = image.size,
                              valign=("middle",0.7),
                              titleCase=True,
                              font_colour=font_colour)
      cache = {}
      rad = 3
      image = RoundedCorners.round_image(image, cache, corner_rad)

    if state == "off":
      fill=self.adjust_colour("bg", luminosity=0.6)
      self.create_arrows(image, draw, height, direction="right", colour=fill, type='simple')

    else:
      fill = self.adjust_colour("highlight",  luminosity = 1.0)
      self.create_arrows(image, draw, height, direction="up", colour=fill, type='simple')

    if self.advertise_new:
      self.draw_advertise_new(draw, image)

    image = self.add_whitespace(image=image, side='bottom', margin_left=rad, weight=1, colour = self.adjust_colour("bg", luminosity = 0.90))
    image = self.add_whitespace(image=image, side='bottom', margin_left=rad, weight=1, colour = self.adjust_colour("bg", luminosity = 0.95))
    filename = item
    return image


  def make_timage(self, item_type, item, state, font_name="Vera", width=None, colour=None, whitespace=None, titleCase=True):
    if not width:
      width = self.width

    base_colour = OV.GetParam('gui.timage.%s.base_colour' %item_type)
    highlight_colour = OV.GetParam('gui.html.highlight_colour').rgb
    self.highlight_colour = highlight_colour

    if not base_colour:
      base_colour = OV.GetParam('gui.timage.base_colour')
      if not base_colour:
        base_colour = OV.GetParam('gui.base_colour').rgb
      else:
        base_colour = base_colour.rgb
    else:
      base_colour = base_colour.rgb

    grad_step = OV.GetParam('gui.timage.%s.grad_step' %item_type)
    grad_colour = OV.GetParam('gui.timage.%s.grad_colour' %item_type)
    font_colour = OV.GetParam('gui.timage.%s.font_colour' %item_type)

    #if state == "highlight":
    #  font_colour = OV.GetParam('gui.html.highlight_colour')

    bg_colour = self.adjust_colour(base_colour, luminosity = OV.GetParam('gui.timage.%s.bg_colour_L' %item_type))
    if state == "highlight":
      bg_colour = OV.GetParam('gui.html.highlight_colour').rgb

    if grad_colour is None:
      grad_colour = self.adjust_colour(base_colour, luminosity = OV.GetParam('gui.timage.%s.grad_colour_L' %item_type))
    else:
      grad_colour = grad_colour.rgb
    if font_colour is None:
      font_colour = self.adjust_colour(base_colour, luminosity = OV.GetParam('gui.timage.%s.font_colour_L' %item_type))
    else:
      font_colour = font_colour.rgb
    font_name = OV.GetParam('gui.timage.%s.font_name' %item_type)
    if not font_name:
      font_name = OV.GetParam('gui.timage.font_name')
    font_size = OV.GetParam('gui.timage.%s.font_size' %item_type)
    if font_size is None:
      valign = ('middle',0.7,)
    else:
      valign = False
      font_size = int(round(font_size * self.size_factor,0))
    arrows = OV.GetParam('gui.timage.%s.arrows' %item_type)

    if state == "highlight":
      grad_colour = OV.GetParam('gui.html.highlight_colour').rgb
    elif state == "inactive":
      grad_colour = '#ababab'
      bg_colour = '#ababab'
    elif state == "hover":
#      grad_colour = IT.adjust_colour(grad_colour, luminosity = 1.02)
      grad_colour = IT.adjust_colour(grad_colour, luminosity = 0.98)
#      font_colour = IT.adjust_colour(highlight_colour, luminosity = 0.9)
    elif state == "hoveron":
      grad_colour = IT.adjust_colour(grad_colour, luminosity = 0.95)
#      font_colour = IT.adjust_colour(font_colour, luminosity = 0.9)

    height = int(round(OV.GetParam('gui.timage.%s.height' %item_type) * self.size_factor, 0))
    top = int(round(OV.GetParam('gui.timage.%s.top' %item_type) * self.size_factor,0))
    left = int(round(OV.GetParam('gui.timage.%s.left' %item_type) * self.size_factor,0))
    corner_rad = int(round(OV.GetParam('gui.timage.%s.corner_rad' %item_type) * self.size_factor,0))
    halign = OV.GetParam('gui.timage.%s.halign' %item_type)

    shadow = OV.GetParam('gui.timage.%s.shadow' %item_type)
    if shadow is None: shadow = True
    border = False
    arrow_scale = 1.0

    if item_type == "h1":
      width += 1
      underground = OV.GetParam('gui.html.bg_colour').rgb

    elif item_type == "h3":
      width -= OV.GetParam('gui.html.table_firstcol_width')
      underground = OV.GetParam('gui.html.table_firstcol_colour').rgb

    elif "tab" in item_type:
      underground = OV.GetParam('gui.html.bg_colour').rgb
      if state == 'on':
        font_colour = self.highlight_colour

    elif item_type == "snumtitle":
      underground = OV.GetParam('gui.html.bg_colour').rgb
      title_case = False

    elif item_type == 'button':
      underground = OV.GetParam('gui.html.table_bg_colour').rgb
      shadow = False
      buttonmark = True
      if state == "on":
        grad_colour = highlight_colour
      elif state == "hover":
        grad_colour = IT.adjust_colour(highlight_colour, luminosity = 0.95)

    elif item_type == 'tinybutton':
      underground = OV.GetParam('gui.html.table_bg_colour').rgb
      shadow = False
      if colour:
        grad_colour = colour
      if state == "on":
        grad_colour = OV.GetParam('gui.html.highlight_colour').rgb
      if state == "hover":
        if colour:
          grad_colour = IT.adjust_colour(colour, luminosity=0.9)
      if state == "highlight":
        font_colour = OV.GetParam('gui.html.highlight_colour').rgb

    elif item_type == 'g3_big':
      underground = OV.GetParam('gui.html.bg_colour').rgb
      shadow = True
      buttonmark = True
      whitespace = "top:4:%s" %OV.GetParam('gui.html.bg_colour').hexadecimal
      if state == "on":
        grad_colour = highlight_colour
      elif state == "hover":
        grad_colour = IT.adjust_colour(highlight_colour, luminosity = 0.95)
        
    elif item_type =='cbtn':
      underground = OV.GetParam('gui.html.bg_colour').rgb
      if state == 'on':
        font_colour = self.highlight_colour
      else:
        font_colour = IT.adjust_colour(grad_colour, luminosity = OV.GetParam('gui.timage.font_colour_L'))
      border = True
      border_weight = 1
      border_fill = IT.adjust_colour(grad_colour, luminosity = 0.8)
      arrow_scale = 0.7
      bg_colour = '#229922'

    self.font_colour = font_colour


    if "GB" in self.gui_language_encoding: #--!--
      height = height + 2
    else:
      height = height

    size = (int(width), int(height))
    bg_colour = underground #hp
    image = Image.new('RGBA', size, bg_colour)
    draw = ImageDraw.Draw(image)

    if grad_step:
      self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=grad_step)


    ## Prepare text for printing on the new image. If '-' is present in the string, this will
    ## be replaced with a space and the parts will be made into title case.
    t = item.split("-")
    txt = ""
    if len(t) > 1:
      for bit in t:
        txt += bit.title() + " "
    else:
      txt = item
    
    ## Actually print the text on the new image item.
    wX, wY = self.write_text_to_draw(draw,
                            txt,
                            top_left=(left,top),
                            font_name=font_name,
                            font_size=font_size,
                            image_size = image.size,
                            valign=valign,
                            align=halign,
                            max_width=width,
                            titleCase=titleCase,
                            font_colour=font_colour)
    cache = {}

    if item_type == "snumtitle":
      info_size = OV.GetParam('gui.timage.snumtitle.filefullinfo_size')
      colour = OV.GetParam('gui.timage.snumtitle.filefullinfo_colour').rgb
      self.drawFileFullInfo(draw, colour, right_margin=5, height=height, font_size=info_size, left_start=wX + 15)
      self.drawSpaceGroupInfo(draw, luminosity=OV.GetParam('gui.timage.snumtitle.sg_L'), right_margin=3)

    if self.advertise_new:
      draw = ImageDraw.Draw(image)
      self.draw_advertise_new(draw, image)
      self.advertise_new = False

    if arrows:
      off_L = OV.GetParam('gui.timage.%s.off_L' %item_type)

      if off_L is None:
        off_L = 1.0
      on_L = OV.GetParam('gui.timage.%s.on_L' %item_type)

      if on_L is None:
        on_L = 1.0
      hover_L = OV.GetParam('gui.timage.%s.hover_L' %item_type)

      if hover_L is None:
        hover_L = 1.0

      image = self.make_arrows(state, width, arrows, image, height, base_colour, off_L, on_L, hover_L, arrow_scale)

    if border:
      image = self.make_timage_border(image, fill = border_fill)

    if corner_rad:
      rounded = OV.GetParam('gui.timage.%s.rounded' %item_type)
      if rounded is None: rounded = '1111'
      image = self.make_corners(rounded, image, corner_rad, underground)

    if shadow:
      image = self.make_shadow(image, underground, corner_rad)

    if whitespace:
      w = whitespace.split(':')
      side = w[0]
      weight = int(w[1])
      bg = w[2]
      image = self.add_whitespace(image, side, weight, bg)
    filename = item
    return image

  def make_timage_border (self, image, weight=1, fill='#ababab'):
    width, height = image.size
    draw = ImageDraw.Draw(image)
    draw.line((0,0,width-1,0), fill = fill)
    draw.line((0,height -1,width-1,height -1), fill = fill)
    draw.line((0,0,0,height - 1), fill = fill)
    draw.line((width -1,0,width-1,height -1), fill = fill)
    return image

  def make_corners(self, rounded, image, corner_rad, underground):
    cache = {}
    rounded_pos = []
    for ritem in rounded:
      if ritem == '0':
        r = 'Square'
      elif ritem == '1':
        r = 'Rounded'
      rounded_pos.append(r)
    pos = tuple(rounded_pos)
    image = RoundedCorners.round_image(image, cache, radius=corner_rad, pos=pos, back_colour=underground)
    return image

  def make_shadow(self, image, underground, corner_rad):
    image = self.add_whitespace(image=image, side='bottom', margin_left=corner_rad, weight=1, colour = self.adjust_colour(underground, luminosity = 0.97))
    image = self.add_whitespace(image=image, side='bottom', margin_left=corner_rad, weight=1, colour = self.adjust_colour(underground, luminosity = 0.99))
    return image


  def make_arrows(self, state, width, arrows, image, height, base_colour, off_L, on_L, hover_L, scale=1.0):
    draw = None
    if state == "off":
      fill = self.adjust_colour(base_colour, luminosity=off_L)
    elif state == "on":
      fill = self.adjust_colour(OV.GetParam('gui.html.highlight_colour').rgb, luminosity=on_L)
    elif state == "hover":
#      fill = self.adjust_colour(OV.GetParam('gui.html.highlight_colour').rgb, luminosity=on_L)
      fill = self.adjust_colour(OV.GetParam('gui.html.base_colour').rgb, luminosity=hover_L)
    elif state == "hoveron":
      fill = self.adjust_colour(OV.GetParam('gui.html.highlight_colour').rgb, luminosity=on_L)
    else:
      fill = '#888888'

    if 'img' in arrows:
      side = arrows.split('img:')[1].split(':')[0].split(',')[0]
      image_name = (arrows.split('img:')[1].split(',')[0].split(':')[1]).split(',')[0]
      p = "%s/etc/skins/%s_%s.png" %(OV.BaseDir(), image_name, state)
      if os.path.exists(p):
        img = Image.open(p)
        oSize = img.size
        s = oSize[1]/image.size[1]
        nSize = (int(oSize[0]/s), int(oSize[1]/s))
        img = img.resize(nSize)
        image.paste(img,(0,0))

    if 'bar' in arrows:
      draw = ImageDraw.Draw(image)
      try:
        side = arrows.split('bar:')[1].split(':')[0].split(',')[0]
      except:
        side = 'left'
      try:
        weight = int(arrows.split('bar:')[1].split(',')[0].split(':')[1])
      except:
        weight = 2
      #weight = int(round(weight * self.size_factor,0))
      if side == 'right':
        sidefill = fill
      else:
        sidefill = fill
      image = self.add_whitespace(image=image, side=side, weight=weight, colour = sidefill, overwrite=True)

    if 'arrow' in arrows:
      draw = ImageDraw.Draw(image)
      direction = "up"
      align = 'left'
      if "arrow_right" in arrows:
        align = 'right'
      elif "arrow_left" in arrows:
        align = 'left'

      try:
        direction = arrows.split(":"+state)[1].split(':')[0].split(',')[0]
      except:
        if state == 'off':
          direction = 'right'
        elif state == 'on':
          direction = 'up'
        #elif state == 'hover':
          #direction = 'down'
        #elif state == 'hoveron':
          #direction = 'up'
        elif state == 'inactive':
          direction = 'up'

      if 'bar' in arrows:
        if state == 'on':
          fill = IT.adjust_colour(fill,luminosity = 1.6)
        else:
          fill = IT.adjust_colour(fill,luminosity = 0.8)

      self.create_arrows(image, draw, height, direction=direction, colour=fill, type='dots', align = align, width=width, scale = scale)

    if 'char' in arrows:
      draw = ImageDraw.Draw(image)
      if 'right' in arrows:
        fill = IT.adjust_colour(fill, luminosity=0.5)
      draw = ImageDraw.Draw(image)
      try:
        char = arrows.split(state)[1].split(':')[0].split(',')[0]
      except:
        side = '0'
        char = "#"

      self.create_arrows(image,
                         draw,
                         height,
                         direction='down',
                         colour=fill,
                         type='char',
                         char_pos='Auto',
                         char_char = char,
                         h_space=4,
                         v_space=4,
                         width = width)


    if 'triangle' in arrows:
      draw = ImageDraw.Draw(image)
      try:
        side = arrows.split('triangle:')[1].split(',')[0]
      except:
        side = 'left'
      begin = (2, 7)
      middle = (2, 2)
      end = (7, 2)
      draw.polygon((begin, middle, end), fill)

    if 'buttonmark' in arrows:
      if state == "hover":
        fill = IT.adjust_colour(self.font_colour, luminosity=1.2)
      else:
        fill = "#ffffff"

      margin = int(arrows.split('buttonmark:')[1].split(',')[0])
      if not draw:
        draw = ImageDraw.Draw(image)
      w,h = image.size
      for i in xrange(int(h/2) - 2):
        y = 2 + i * 2
        for j in xrange(4):
          x = (w - margin) + j * 2
          draw.point((x, y), fill)
    return image

  def drawFileFullInfo(self, draw, colour='#ff0000', right_margin=0, height=10, font_name="Verdana", font_size=8, left_start = 40):
    base_colour = self.params.html.base_colour.rgb
    txt = OV.FileFull()
    if txt == "none":
      return
    font = self.registerFontInstance(font_name, font_size)
    tw = (draw.textsize(txt, font)[0])
    n = int(len(txt)/2)
    txtbeg = txt[:n]
    txtend = txt [-n:]

    if left_start > self.width:
      left_start = 50
    else:
      left_start = left_start

    xx = 0
    while tw > self.width - left_start:
      txtbeg = txt[:n]
      txtend = txt [-n:]
      tw = (draw.textsize("%s...%s" %(txtbeg, txtend), font)[0])
      n -= 1
      xx += 1
      if xx > 100:
        break
    txt = "%s...%s" %(txtbeg, txtend)

    wX, wY  = draw.textsize(txt, font)
    left_start =  (self.width-wX) - right_margin
    top = height - wY - 2
    self.write_text_to_draw(draw,
                       txt,
                       top_left=(left_start, top),
                       font_name=font_name,
                       font_size=font_size,
                       font_colour=colour)


  def drawSpaceGroupInfo(self, draw, luminosity=1.9, right_margin=8, font_name="Times Bold"):
    base_colour = self.params.html.base_colour.rgb
    left_start = 150
    font_colour = self.adjust_colour(base_colour, luminosity=luminosity)
    scale = OV.GetParam('gui.timage.snumtitle.sginfo_scale')
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
        font_bar = self.registerFontInstance("%s Bold" %font_base, int(11 * scale))
        font_slash = self.registerFontInstance("%s Bold" %font_base, int(18 * scale))
        font_number = self.registerFontInstance("%s Bold" %font_base, int(14 * scale))
        font_letter = self.registerFontInstance("%s Bold Italic" %font_base, int(15 * scale))
        font_sub = self.registerFontInstance("%s Bold" %font_base, int(10 * scale))
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

  def tab_items(self, item, state, font_name = "Vera", font_size=13):
    if self.params.image_font_name:
      font_name = self.params.image_font_name
      font_name = "%s Bold" %font_name
    language = olx.CurrentLanguage()

    base_colour = self.params.tab.base_colour.rgb
    rounded =  self.params.tab.rounded
    decorated = self.params.tab.decorated

    bg_colour_L = self.params.tab.bg_colour_L
    grad = self.params.tab.grad
    grad_colour_L = self.params.tab.grad_colour_L
    grad_step = self.params.tab.grad_step
    font_colour_L = self.params.tab.font_colour_L

    bg_colour = self.adjust_colour(base_colour, luminosity = bg_colour_L)
    grad_colour = self.adjust_colour(base_colour, luminosity = grad_colour_L)
    font_colour = self.adjust_colour(base_colour, luminosity = font_colour_L)

    height = self.params.tab.height
    font_name = self.params.tab.font_name
    font_size = self.params.tab.font_size

    top = self.params.tab.top
    left = self.params.tab.left

    width = self.width/len(self.tabItems)-2
    if language == "Chinese":
      height = height + 2
      top += 2
      size_factor = 0.6

    elif language == "Russian":
      height = height
      size_factor = 0.7

    else:
      height = height
      top += 3
      size_factor = 1

    size = (int(width), int(height))
    image = Image.new('RGBA', size, base_colour)
    draw = ImageDraw.Draw(image)
    if grad:
      self.gradient_bgr(draw, width, height, colour = grad_colour, fraction=1, step=grad_step)

    begin = (2, 7)
    middle = (2, 2)
    end = (7, 2)

    if state == "off":
      #triangle left-off
      font_colour = self.adjust_colour(base_colour, luminosity = 1.9, saturation = 1.2)
      if decorated == 'top_left_triangle':
        draw.polygon((begin, middle, end), self.adjust_colour(base_colour, luminosity = 1.3))
    if state != "off":
      #triangle left-on
      if decorated == 'top_left_triangle':
        draw.polygon((begin, middle, end), fill=self.highlight_colour)
      font_colour = self.highlight_colour


    ## ROUNDEDNESS OR OTHERWISE
    cache = {}
    rounded_pos = []
    for ritem in rounded:
      if ritem == '0':
        r = 'Square'
      elif ritem == '1':
        r = 'Rounded'
      rounded_pos.append(r)
    pos = tuple(rounded_pos)
    image = RoundedCorners.round_image(image, cache, 7, pos=pos)

    txt = item.replace("index-", "")

    self.write_text_to_draw(draw,
                            txt,
                            #align = "right",
                            top_left = (left, top),
                            max_width = width-5,
                            font_name=font_name,
                            font_size=font_size,
                            font_colour=font_colour,
                            image_size = image.size,
                            lowerCase = True,
                            #valign=(middle,size_factor)
                          )


    image = self.add_whitespace(image=image, side='top', weight=2, colour=self.params.html.bg_colour.rgb)
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.90))
    image = self.add_whitespace(image=image, side='bottom', weight=1, colour = self.adjust_colour("bg", luminosity = 0.95))
    image = self.add_whitespace(image=image, side='right', margin_top=4, weight=1, colour = self.adjust_colour("bg", luminosity = 0.95))
    filename = item
    return image



  def note_items(self, item):
    #cs = self.cs
    base_colour = self.params.html.base_colour.rgb
    needs_warning=item[3]
    font_size = 9
    line = int(font_size + font_size * 0.18)
    width = self.width - 25
    #if needs_warning:
    #  w = self.warning.size[0] + 8
    #  width = width - w

    text = OV.TranslatePhrase(item[0])
    #if olx.IsCurrentLanguage('Chinese') == 'true':
    #  text = text.decode('GB2312')

    text = text.split()
    if olx.IsCurrentLanguage('Chinese') == 'true':
      #font_name = "Arial UTF"
      font_name = self.params.chinese_font_name
    else:
      font_name = "Vera"
      if self.params.image_font_name:
        font_name = self.params.image_font_name

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
    #if needs_warning:
    #  image = self.add_whitespace(image=image, side='left', weight=w, colour=self.params.html.bg_colour.rgb)
    #  image.paste(self.warning, (2,2), self.warning)

    image = self.add_whitespace(image=image, side='top', weight=2, colour=self.params.html.bg_colour.rgb)

    return image

  def label_items(self, item, font_name = 'Vera'):
    text = item[0]
    width = item[1]
    base_colour = self.params.html.base_colour.rgb
    if self.params.image_font_name:
      font_name = self.params.image_font_name

    if width == 0:
      width = len(text) * 7
    else:
      width = width
    height = 16
    bg_colour = 250, 250, 250
    font_colour="#4e5086"
    size = (int(width), int(height))
    image = Image.new('RGBA', size, base_colour)
    draw = ImageDraw.Draw(image)

#               border_colour=("#f2f2f2","#f2f2f2","#f2f2f2","#f2f2f2")
    self.make_border(rad=11,
            draw=draw,
            width=width,
            height=height,
            bg_colour=base_colour,
            border_colour=base_colour,
            border_hls = (50, 0.4, 0.4)
          )

    txt = text.replace("-", " ")
    self.write_text_to_draw(draw,
                       txt,
                       font_name=font_name,
                       font_size=10,
                       font_colour=self.adjust_colour(base_colour, luminosity = 1.2)
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
    base_colour = self.params.html.base_colour.rgb
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
                   font_colour=self.adjust_colour(base_colour, luminosity = 1.2)
                 )

    begin = (0,height-2)
    end = (width, height-2)
    draw.line((begin ,end), fill=base_colour)

    begin = (0,0)
    end = (width, 0)
    draw.line((begin ,end), fill=base_colour)

    begin = (0,height-1)
    end = (width, height-1)
    draw.line((begin ,end), fill=cs["white"])

    dup = ImageChops.duplicate(image)
    dup = ImageChops.invert(dup)
    dup = ImageChops.offset(dup, 1, 1)
    image = ImageChops.blend(image, dup, 0.05)
    return image

  def cbtn_items(self, item, state, font_name = "Vera"):
    if self.params.image_font_name:
      font_name = self.params.image_font_name

    width = 75
    height = 30
    size = (int(width), int(height))
    if state == "off":
      colour = 100, 100, 160
      colour = self.params.html.base_colour.rgb
    else:
      colour = 220, 220, 220
      colour = self.highlight_colour
    try:
      font_colour = OV.FindValue('gui_htmlself.params.html.font_colour.rgb')
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
    if self.params.image_font_name:
      font_name = self.params.image_font_name
    width = 50
    height = 17
    size = (int(width), int(height))
    if state == "off":
      colour = 100, 100, 160
    else:
      colour = 255, 0, 0
    try:
      font_colour = self.params.html.font_colour.rgb
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

  def icon_items(self, idx, state, icon_size=None):
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

    if state == "highlight":
      colourise = '#ff0000'

    if colourise:
      crop_colourised = self.colourize(crop, (0,0,0), colourise)
      image.paste(crop_colourised, (0,0), crop)
    else:
      image.paste(crop)


    # strip a bit off the top and the bottom of the square image - it looks better slightly elongated
    strip = int(width * 0.05)
    cut = (0, strip, width, width - strip)
    image = image.crop(cut)
    if not icon_size:
      icon_size = self.params.skin.icon_size
      icon_size = OV.GetParam('gui.skin.icon_size')
    else:
      icon_size = icon_size + 2

    image = image.resize(  (icon_size , int(icon_size*(width-2*strip)/width)  ), Image.ANTIALIAS)
    draw = ImageDraw.Draw(image)

    if state == "hover":
      outline_colour = self.params.html.highlight_colour.rgb
    elif state == "on":
      outline_colour = self.params.html.highlight_colour.rgb
    elif state == "highlight":
      outline_colour = self.params.html.highlight_colour.rgb
    else:
      outline_colour = '#bcbcbc'

    if border:
      draw.rectangle((0, 0, image.size[0]-1, image.size[1]-1), outline=outline_colour)
    if offset:
      dup = ImageChops.duplicate(image)
      dup = ImageChops.invert(dup)
      dup = ImageChops.offset(dup, 1, 1)
      image = ImageChops.blend(image, dup, 0.05)

    return image

  def info_bitmaps(self):

    if olx.CurrentLanguage() == "Chinese":
      font_size = 24
      top = 4
    else:
      font_size = 24
      top = -1

    info_bitmap_font = "Verdana"
    info_bitmaps = {
      'refine':{'label':'Refining',
                'name':'refine',
                'color':'#ff4444',
                'size':(128, 32),
                'font_colour':"#ffffff",
                },
      'solve':{'label':'Solving',
               'name':'solve',
               'color':'#ff4444',
               'size':(128, 32),
                'font_colour':"#ffffff",
               },
      'working':{'label':'Working',
                'name':'working',
                'color':'#ff4444',
                'size':(128, 32),
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
                                 top_left = (5, top),
                                 font_name=info_bitmap_font,
                                 font_size=font_size,
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


def drawSpaceGroupInfo(draw, luminosity=1.9, right_margin=12, font_name="Times Bold"):
  base_colour = OV.GetParam('gui.html.base_colour').rgb
  left_start = 120
  font_colour = OV.GetParam('gui.html.font_colour').rgb

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
    bgcolour = self.params.html.bg_colour.rgb
    outline = self.params.html.base_colour.rgb
    outline = self.adjust_colour(self.params.html.base_colour.rgb,hue=180)
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
    draw.line((xmedian,ybottom,xmedian,ytop), fill=self.params.red.rgb) # draw median line
    draw.line((xlower,ymid - plotHeight/4,xlower,ymid + plotHeight/4), fill=outline)
    draw.line((xupper,ymid - plotHeight/4,xupper,ymid + plotHeight/4), fill=outline)
    draw.line((xlower,ymid,xlowerQ,ymid), fill=outline)
    draw.line((xupperQ,ymid,xupper,ymid), fill=outline)

    OlexVFS.save_image_to_olex(image, "boxplot.png", 0)


timage_instance_TestBanner = timage()
OV.registerFunction(timage_instance_TestBanner.makeTestBanner)



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