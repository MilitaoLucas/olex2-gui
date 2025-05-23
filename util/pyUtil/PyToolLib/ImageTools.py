# -*- coding:utf8 -*-
# import PngImagePlugin
from PIL import Image
from PIL import ImageDraw, ImageChops, ImageColor

from io import StringIO

import OlexVFS
import RoundedCorners
import colorsys
from olexFunctions import OV
from FontInstances import FontInstances
import os
global sizedraw
sizedraw_dummy_draw = ImageDraw.Draw(Image.new('RGBA', (300, 300)))
import olx
import math

#debug = OV.IsDebugging()
debug = False

global dpi_scale
global dpi_scaling

if OV.HasGUI():
  import olex_gui
  dpi_scale = olex_gui.GetPPI()[0]/96
else:
  dpi_scale = 1
  dpi_scaling = OV.GetParam('gui.dpi_scaling')



# self.params.html.highlight_colour.rgb = self.params.html.highlight_colour.rgb
# self.params.timage.colour.rgb = self.params.timage.colour.rgb
# self.params.html.bg_colour.rgb = self.params.html.bg_colour.rgb
# self.params.html.table_bg_colour.rgb = self.params.html.table_bg_colour.rgb
# self.params.html.font_colour.rgb = self.params.html.font_colour.rgb
# self.params.logo_colour.rgb = self.params.logo_colour.rgb
# self.params.html.link_colour.rgb = self.params.html.link_colour.rgb
# self.params.html.input_bg_colour.rgb = self.params.html.input_bg_colour.rgb
# self.params.html.base_colour.rgb = self.params.html.base_colour.rgb
# self.params.html.table_firstcol_colour.rgb = self.params.html.table_firstcol_colour.rgb
# self.params.button_colouring.rgb = self.params.button_colouring.rgb
# self.params.grey.rgb = self.params.grey.rgb
# self.params.green.rgb = self.params.green.rgb
# self.params.red.rgb = self.params.red.rgb

# Compatibility function for text size to allow newer Pillow versions to work with older Olex versions
def get_text_size(draw, text, font):
  if hasattr(draw, 'textbbox'):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]
  else:
    return draw.textsize(text, font=font)

class ImageTools(FontInstances):
  def __init__(self):
    from PIL import ImageColor
    super(ImageTools, self).__init__()
    self.colorsys = colorsys
    self.abort = False
    self.getOlexVariables()
    self.scale = None

    # #Encodings
    self.good_encodings = ["ISO8859-1", "ISO8859-2"]
    self.gui_language_encoding = olx.CurrentLanguageEncoding()
    if OV.HasGUI():
      self.gui_current_language = olx.CurrentLanguage()
    else:
      self.gui_current_language = 'English'

    self.get_font_peculiarities()

    font = "Verdana"

    self.gui_timage_font_name = "%s" % font
    self.gui_tab_font_name = "%s Bold" % font
    self.gui_sNumTitle_font_name = "%s Bold" % font
    self.gui_button_font_name = "%s Bold" % font
    self.params = OV.GuiParams()

    if olx.HasGUI() == "false":
      self.available_width = 200
      self.available_width_full = 200
    else:
#      self.get_available_width()
      self.css = OV.GuiParams().css
    self.dpi_scale=None
    self.im_cache = {}

  def get_available_width(self):
    global dpi_scale
    global dpi_scaling
    dpi_scaling = OV.GetParam('gui.dpi_scaling')

    if dpi_scaling:
      w = OV.GetParam('gui.skin.base_width')
    else:
      if OV.HasGUI():
        w = int(olx.html.ClientWidth('self'))
      else:
        w = 800

    self.skin_width = w
    self.skin_width_margin = w - OV.GetParam('gui.htmlpanelwidth_margin_adjust')
    self.skin_width_table = self.skin_width_margin - OV.GetParam('gui.html.table_firstcol_width')
    self.history_width = self.skin_width_table - int(OV.GetParam('gui.html.table_firstcol_width'))
    self.max_width = w

    self.skin_width = self.skin_width_margin

    if OV.HasGUI():
      client_width = int(olx.html.ClientWidth('self'))
    else:
      client_width = 800

    self.dpi_scale = (client_width-OV.GetParam('gui.htmlpanelwidth_margin_adjust'))/self.skin_width

    if debug:
      print("====== dpi_scaling set to %s ======" %self.dpi_scale)

  def show_image(self, IM):
    import sys
    sys.path.append("C:\\Users\Horst\Documents\olex-trunk\Python26\Lib\site-packages\wx-2.8-msw-unicode")
    import wx
    a = wx.PySimpleApp()
    wximg = wx.Image('%s/splash.jpg' % OV.BaseDir(), wx.BITMAP_TYPE_JPEG)
    wxbmp = wx.BitmapFromImage(wximg)
    f = wx.Frame(None, -1, "Show JPEG demo")
    f.SetSize(wxbmp.GetSize())
    wx.StaticBitmap(f, -1, wxbmp, (0, 0))
    f.Show(True)

    def callback(evt, a=a, f=f):
      # Closes the window upon any keypress
      f.Close()
      a.ExitMainLoop()
      wx.EVT_CHAR(f, callback)
      a.MainLoop()


  def get_unicode_characters(self, txt):
    if not txt:
      return txt

    txt = txt.replace("two_theta", "2theta")
    txt = txt.replace("stol", "(sin(theta)/lambda)")
    txt = txt.replace("_sq", "^2")
    txt = txt.replace("_star", "*")
    txt = txt.replace("_", " ")
    txt = txt.replace("alpha", chr(945))
    txt = txt.replace("beta", chr(946))
    txt = txt.replace("lambda", chr(955))
    txt = txt.replace("theta", chr(952))
    txt = txt.replace("Theta", chr(920))
    txt = txt.replace("sigma", chr(963))
    txt = txt.replace("^2", chr(178))
    txt = txt.replace("^3", chr(179))
    txt = txt.replace(">m", chr(61681))
    txt = txt.replace("<m", chr(61665))
    txt = txt.replace("Fo2", "Fo%s" % (chr(178)))
    txt = txt.replace("Fc2", "Fc%s" % (chr(178)))
    txt = txt.replace("Sum", chr(8721))
    # txt = txt.replace("Fexp2", "Fexp%s" %(unichr(178)))
    # txt = txt.replace("Fo2", "F%s%s" %(unichr(2092),unichr(178)))
    txt = txt.replace("Fexp", "F%s" % (chr(2091)))
    txt = txt.replace("Angstrom", chr(197))
    txt = txt.replace("degrees", "\u00B0")
    txt = txt.replace("alpha", chr(945))
    txt = txt.replace("beta", chr(946))
    return txt


  def centre_text(self, draw, txt, font, maxWidth):
    txt_size = get_text_size(draw, txt, font=font)
    hStart = self.txt_left + int((maxWidth - txt_size[0]) / 2)
    return hStart

  def align_text(self, draw, txt, font, maxWidth, align):
    if align == "centre":
      txt_size = get_text_size(draw, txt, font=font)
      hStart = int((maxWidth - txt_size[0]) / 2)
      retVal = hStart
    if align == "right":
      txt_size = get_text_size(draw, txt, font=font)
      hStart = int((maxWidth - txt_size[0]))
      retVal = hStart
    return retVal

  def decimalColorToHTMLcolor(self, dec_colour):
    
    r = hex(dec_colour&255)[2:]
    g = hex((dec_colour>>8)&255)[2:]
    b = hex((dec_colour>>16)&255)[2:]

    if r == '0':
      r = '00'
    if g == "0":
      g = "00"
    if b == "0":
      b = "00"
      
    retVal = "#%s%s%s" %(r, g, b)
    return retVal
  
  def decimalColorToRGB(self, dec_colour):
    
    r = dec_colour & 255
    g = (dec_colour >> 8) & 255
    b = (dec_colour >> 16) & 255

    retVal = (r, g, b)
    return retVal  

  def getOlexVariables(self):
    # self.encoding = self.test_encoding(self.gui_language_encoding) ##Language
    # self.language = "English" ##Language
    # if olx.IsCurrentLanguage('Chinese') == "true":
    #  self.language = 'Chinese'
    self.fonts = self.defineFonts()
    self.gui_red = OV.GetParam('gui.red').rgb
    self.gui_green = OV.GetParam('gui.green').rgb
    self.gui_blue = OV.GetParam('gui.blue').rgb
    self.gui_grey = OV.GetParam('gui.grey').rgb

  def dec2hex(self, n):
    """return the hexadecimal string representation of integer n"""
    return "%X" % n

  def hex2dec(self, s):
    """return the integer value of a hexadecimal string s"""
    l = list(s)
    c = "%s%s%s%s%s%s" % (l[5], l[6], l[3], l[4], l[1], l[2])
    return int(c, 16)


  def RGBToHTMLColor(self, rgb_tuple):
      """ convert an (R, G, B) tuple to #RRGGBB """
      hexcolor = '#%02x%02x%02x' % rgb_tuple
      # that's it! '%02x' means zero-padded, 2-digit hex values
      return hexcolor

  def HTMLColorToRGB(self, colorstring):
      """ convert #RRGGBB to an (R, G, B) tuple """
      try:
        colorstring = colorstring.strip()
      except:
        return colorstring
      if colorstring[0] == '#': colorstring = colorstring[1:]
      if len(colorstring) != 6:
          raise ValueError("input #%s is not in #RRGGBB format" % colorstring)
      r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
      r, g, b = [int(n, 16) for n in (r, g, b)]
      return (r, g, b)

  def watermark(self, im, mark, position, opacity=1):
    """Adds a watermark to an image."""
    if opacity < 1:
        mark = self.reduce_opacity(mark, opacity)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    # create a transparent layer the size of the image and draw the
    # watermark in that layer.
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    if position == 'tile':
        for y in range(0, im.size[1], mark.size[1]):
            for x in range(0, im.size[0], mark.size[0]):
                layer.paste(mark, (x, y))
    elif position == 'scale':
        # scale, but preserve the aspect ratio
        ratio = min(
            float(im.size[0]) / mark.size[0], float(im.size[1]) / mark.size[1])
        w = int(mark.size[0] * ratio)
        h = int(mark.size[1] * ratio)
        mark = mark.resize((w, h))
        layer.paste(mark, ((im.size[0] - w) / 2, (im.size[1] - h) / 2))
    else:
        layer.paste(mark, position)
    # composite the watermark with the layer
    return Image.composite(layer, im, layer)


  def makeBackgroundTransparent(self, img, col=(255, 255, 255)):

    col = self.HTMLColorToRGB(col)
    img = img.convert("RGBA")
    pixdata = img.load()

    for y in range(img.size[1]):
      for x in range(img.size[0]):
        if pixdata[x, y] == (255, 255, 255, 255):
            pixdata[x, y] = (255, 255, 255, 0)
    return img

  def makeTransparentText(self, im, txt, top_left=(1, 0), font_colour="#000000", font_name="Arial Bold", font_size=14):
    # Make a grayscale image of the font, white on black.
    font_file = self.fonts[font_name]
    imtext = Image.new("L", im.size, 0)
    alpha = Image.new("L", im.size, "Black")
    drtext = ImageDraw.Draw(imtext)
    font = ImageFont.truetype(font_file, font_size)
    drtext.text(top_left, OV.correct_rendered_text(txt), font=font, fill="white")
    # Add the white text to our collected alpha channel. Gray pixels around
    # the edge of the text will eventually become partially transparent
    # pixels in the alpha channel.
    alpha = ImageChops.lighter(alpha, imtext)
    # Make a solid color, and add it to the color layer on every pixel
    # that has even a little bit of alpha showing.
    solidcolor = Image.new("RGBA", im.size, font_colour)
    immask = Image.eval(imtext, lambda p: 255 * (int(p != 0)))
    im = Image.composite(solidcolor, im, immask)
    im.putalpha(alpha)
    return im


  def make_colour_pixel(self, colour):
    if not colour:
      return
    size = (10, 10)
    IM = Image.new('RGBA', size, colour)
    name = r"pixel_%s.png" % colour[1:]
    OlexVFS.save_image_to_olex(IM, name, 2)
    return name


  def make_colour_sample(self, colour, size=(20, 12)):
    if not colour:
      return
    IM = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(IM)
    draw.rectangle((0, 0, IM.size[0] - 1, IM.size[1] - 1), outline='#bcbcbc')

    name = r"colour_%s.png" % colour[1:]
    OlexVFS.save_image_to_olex(IM, name, 2)
    return name

  def set_htmlpanel_width(self, new_width):
    if not new_width:
      return
    new_width = float(new_width)
    #if dpi_scaling:
      #new_width = int(round(new_width*dpi_scale))
    if OV.HasGUI():
      if new_width <=1:
        olx.HtmlPanelWidth("%i %%" %int(new_width*100))
      else:
        olx.HtmlPanelWidth(new_width)
    self.get_available_width()
    if debug:
      print("============== resized panel to %s, using dpi_scaling: %s ==============" %(new_width, repr(dpi_scaling)))
      print("---- IT.max_width = %s" %IT.max_width)
      print("---- gui.htmlpanelwidth = %s" %OV.GetParam('gui.htmlpanelwidth'))
      print("---- gui.skin.base_width = %s" %OV.GetParam('gui.skin.base_width'))
      print("---- self.dpi_scale = %s" %IT.dpi_scale)
      print("======================================================")

  def resize_image(self, image, size, name=None):
    #cache_name = "%s_%s_%s" %(name, width)
    if not self.dpi_scale:
      self.get_available_width()
    s = self.dpi_scale
    if dpi_scaling:
      width = int(size[0] * s)
      height = int(size[1] * s)
    else:
      width = int(size[0])
      height = int(size[1])

    #if name:
      #cache_name = "%s_%s" %(name, width)
      #_ = self.im_cache.get(cache_name,None)
      #if _:
        #if repr(width) in cache_name:
          #if debug:
            #print "--- Return %s from Cache!" %name
          #return _

    image = image.resize((width,height), Image.LANCZOS)
    if debug:
      print("+++ Resize %s (%s)!" %(name, s))
    #if name:
      #self.im_cache[cache_name] = image
    return image

  def resize_skin_logo(self, width):
    logopath = "%s/%s" % (self.basedir, OV.GetParam('gui.skin.logo_name'))
    name = r"skin_logo.png"
    if os.path.exists(logopath):
      im = Image.open(logopath)
      factor = im.size[0] / width
      height = int(im.size[1] / factor)
      im = self.resize_image(im, (width, height), name=name)
      OlexVFS.save_image_to_olex(im, name, 2)
      txt = '<zimg border="0" src="skin_logo.png">'
    else:
      txt = " "
    OlexVFS.write_to_olex('logo1_txt.htm', txt, 2)
    return "Done"

  def resize_to_panelwidth(self, i, colourize=False, width_adjust=0, width=None, outname=None, persistence=2):
    import olex
    import io
    do_cache_image = True
    name = i
    im = None
    if name.endswith("@vfs"):  # name_tmp@vfs
      do_cache_image = False
      name = name[:-4]
      s = OlexVFS.read_from_olex(name)
      if s is None:
        return
      olex.writeImage(name, b"")
      name = name[:-4]
      sio = io.BytesIO(s)
      if not sio.getbuffer().nbytes:  # resize was called twice in a raw
        return
      im = Image.open(sio)
    elif os.path.exists(name):
      im = Image.open(name)
    else:
      path = ("%s/etc/%s" % (self.basedir, name))
      if os.path.exists(path):
        im = Image.open(path)
        name = name[:-4]
    if not width:
      width = int(olx.html.ClientWidth('self')) - OV.GetParam('gui.htmlpanelwidth_margin_adjust')
      #width = int(self.skin_width*0.97)

    if im:
      if colourize:
        im = self.colourize(im, (0, 0, 0), OV.GetParam('gui.logo_colour'))
      width = int(width) - width_adjust
      if width < 10: return
      factor = im.size[0] / width
      height = int(im.size[1] / factor)
      if do_cache_image:
        im = self.resize_image(im, (width, height), name=name)
      else:
        im = self.resize_image(im, (width, height))
      if outname: name = outname
      OlexVFS.save_image_to_olex(im, name, persistence)
    else:
      pass
    return "Done"

  def reduce_opacity(self, im, opacity):
    """Returns an image with reduced opacity."""
    from PIL import ImageEnhance
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im


  def doDup(self, image, offset_x=1, offset_y=1, blend=0.1):
    dup = ImageChops.duplicate(image)
    dup = ImageChops.invert(dup)
    dup = ImageChops.offset(dup, offset_x, offset_y)
    image = ImageChops.blend(image, dup, blend)
    return image


  def add_vline(self, draw, height, h_pos, v_pos, weight=1, colour=(237, 237, 235)):
    begin = (h_pos, v_pos)
    end = (h_pos, height)
    draw.line((begin , end), fill=self.adjust_colour(colour, luminosity=1))
    pass

  def add_whitespace(self, image, side, weight, colour, margin_left=0, margin_right=0, margin_top=0, margin_bottom=0, overwrite=False):
    weight = int(weight)
    width, height = image.size
    top = 0 + margin_top
    left = 0 + margin_left
    bottom = height - margin_bottom
    right = width - margin_right
    if overwrite:
      weight_add = 0
    else:
      weight_add = weight
    if side == "top":
      whitespace = Image.new('RGBA', (width - margin_left - margin_right, weight), colour)
      canvas = Image.new('RGBA', (width, height + weight_add), colour)
      canvas.paste(whitespace, (margin_left, 0))
      canvas.paste(image, (0, weight))
    elif side == "bottom":
      whitespace = Image.new('RGBA', (width - margin_left - margin_right, weight), colour)
      canvas = Image.new('RGBA', (width, height + weight_add), colour)
      canvas.paste(whitespace, (margin_left, height - weight + margin_top))
      canvas.paste(image, (0, 0))
    elif side == "right":
      whitespace = Image.new('RGBA', (weight, height - margin_top - margin_bottom), colour)
      canvas = Image.new('RGBA', (width + weight_add, height), colour)
      canvas.paste(image, (0, 0))
      canvas.paste(whitespace, (width - weight + weight_add, margin_top))
    elif side == "left":
      whitespace = Image.new('RGBA', (weight, height - margin_top - margin_bottom), colour)
      canvas = Image.new('RGBA', (width + weight_add, height), colour)
      canvas.paste(whitespace, (0, margin_top))
      canvas.paste(image, (weight, 0))
    return canvas

  def cut_image(self, image, cuts=(10, 20)):
    ''' Returns a list of images, cut left to right at the cuts positions '''
    retVal = []
    size = image.size
    current = 0
    for cut in cuts:
      left = 0
      right = cut
      current += right
      retVal.append(image.crop((left, 0, right, size[1])))
    retVal.append(image.crop((current, 0, size[0], size[1])))
    return retVal


  def colourize(self, IM, col_1, col_2):
    from PIL import ImageOps
    # IM = self.removeTransparancy(IM, (255,255,255))
    IM = IM.convert("L")
    if type(col_1) == str:
      col_1 = self.RGBToHTMLColor(col_1)
      col_2 = self.RGBToHTMLColor(col_2)
    try:
      IM = ImageOps.colorize(IM, col_1, col_2)
    except:
      pass
    return IM

  def make_full_width_empty_image(self, height=100, colour='#b40000', scale=1, width_adjust=0):
    adjusted_width = self.available_width_full - width_adjust
    size = (adjusted_width * scale, height * scale)
    im = Image.new("RGB", size, colour)
    draw = ImageDraw.Draw(im)
    return im, draw, adjusted_width

  def add_continue_triangles(self, draw, width, height, shift_up=4, shift_left=5, style=('multiple')):
    arrow_top = 8 + shift_up
    arrow_middle = 5 + shift_up
    arrow_bottom = 2 + shift_up
    beg_1 = 20 + shift_left
    mid_1 = 16 + shift_left
    beg_2 = 13 + shift_left
    mid_2 = 9 + shift_left
    beg_3 = 7 + shift_left
    mid_3 = 3 + shift_left

    if 'multiple' in style:
      colour = (150, 190, 230)
      colour = self.gui_timage_colour
      begin = (width - beg_1, height - arrow_top)
      middle = (width - mid_1, height - arrow_middle)
      end = (width - beg_1, height - arrow_bottom)
      draw.polygon((begin, middle, end), colour)
      colour = self.adjust_colour(colour, luminosity=0.7)
      begin = (width - beg_2, height - arrow_top)
      middle = (width - mid_2, height - arrow_middle)
      end = (width - beg_2, height - arrow_bottom)
      draw.polygon((begin, middle, end), colour)
      colour = self.adjust_colour(colour, luminosity=0.7)
      begin = (width - beg_3, height - arrow_top)
      middle = (width - mid_3, height - arrow_middle)
      end = (width - beg_3, height - arrow_bottom)
      draw.polygon((begin, middle, end), colour)

    elif 'single' in style:
      beg_3 = 10 + shift_left
      mid_3 = 4 + shift_left
      direction = style[1]
      colour = style[2]
      if "(" in colour:
        colour = eval(colour)
      arrow_width = 12
      if direction == "right":
        begin = (width - beg_3, height - arrow_top)
        middle = (width - mid_3, height - arrow_middle)
        end = (width - beg_3, height - arrow_bottom)
      elif direction == "up":
        begin = (width - beg_3 + arrow_width / 2, height - arrow_top)
        middle = (width - mid_3, height - arrow_bottom)
        end = (width - beg_3, height - arrow_bottom)
      elif direction == "down":
        begin = (width - beg_3, height - arrow_top)
        middle = (width - mid_3, height - arrow_top)
        end = (width - beg_3 + arrow_width / 2, height - arrow_bottom)
      elif direction == "left":
        begin = (width - beg_3 + arrow_width, height - arrow_top)
        middle = (width - beg_3, height - arrow_middle)
        end = (width - beg_3 + arrow_width, height - arrow_bottom)
      if begin:
        draw.polygon((begin, middle, end), colour)

  def adjust_colour(self, colour, hue=0, luminosity=1, saturation=1, as_format='rgb'):
    '''
    Adjusts the colour of a color value. It can be either a pre-defined value
    like "highlight" or a rgb value. Hue, luminosity and saturation can be
    controlled by the optional parameters.
    Returns a modified rgb color value.
    :type colour: string
    :return nc: string
    '''
    hue = float(hue)
    if not luminosity:
      luminosity = 1
    try:
      luminosity = float(luminosity)
      saturation = float(saturation)
    except:
      luminosity = 1
      saturation = 1
    if colour == 'base':
      colour = self.params.timage.base_colour.rgb
    if colour == "bg":
      colour = self.params.html.bg_colour.rgb
    if colour == "highlight":
      colour = self.params.html.highlight_colour.rgb
    if colour == "gui_html_table_bg_colour":
      colour = self.params.html.table_bg_colour.rgb
    else:
      try:
        colour = colour.rgb
      except:
        colour = colour

    if "#" in str(colour):
      colour = ImageColor.getrgb(colour)
    try:
      c = self.colorsys.rgb_to_hls(*[x / 255.0 for x in colour])
    except:
      pass
    l = list(c)
    l[0] = l[0] + hue / 360.
    if l[0] > 1:
      l[0] = l[0] - 1
    l[1] = l[1] * luminosity
    l[2] = l[2] * saturation
    c = tuple(l)
    nc = self.colorsys.hls_to_rgb(*[x for x in c])
    l = []
    for item in nc:
      value = int(item * 255)
      if value >= 255:
        value = 255
      if value <= 0:
        value = 0
      l.append(value)
      
    if as_format.lower() == "rgb":
      nc = tuple(l)
    elif as_format.lower() == "hex" or as_format.lower() == "html":
      nc = IT.RGBToHTMLColor(tuple(l))
    else:
      nc = tuple(l)
    return nc

  def is_lighter_than_gray(self, hex_color):
    """Check if a given hex color is lighter than medium gray (#808080)."""
    hex_color = hex_color.lstrip("#")  # Remove '#' if present
    r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]  # Convert to RGB
  
    # Compute luminance (brightness)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
  
    return luminance > 128  # True if lighter, False if darker

  def gradient_bgr(self, draw, width, height, colour=(237, 237, 235), fraction=0.85, increment=10, step=1):
    inc = increment
    if "#" in colour: colour = self.HTMLColorToRGB(colour)
    for i in range(int(height * fraction)):
      if i < height / inc:
        adjusted_step = 0.6 * step
      elif height / inc < i < (height / inc) * 2:
        adjusted_step = 1.2 * step
      else:
        adjusted_step = 1.4 * step
      incrementA = int(adjusted_step * i * (58 / height))
      incrementB = int(adjusted_step * i * (44 / height))

      begin = (0, i)
      end = (width, i)
      R = int(colour[0] - incrementA)
      G = int(colour[1] - incrementA)
      B = int(colour[2] - incrementB)
      # print i, R,G,B
      draw.line((begin , end), fill=(R, G, B))


  def sort_out_encoding():
    font = ImageFont.truetype("%s" % font_file, font_size, encoding=self.test_encoding("unic"))  # #Leave in for Debug!
    try:
      font_file = self.fonts.get(font_name, "arialuni.ttf")
      font = ImageFont.truetype("%s" % font_file, font_size, encoding=self.test_encoding("unic"))

    except:
      print("The font %s is required for this option." % font_name)
      self.abort = True
    pass

  def textsize(self,
                   draw,
                   txt,
                   font_size,
                   font_name="DefaultFont",
                   titleCase=False,
                   lowerCase=False,
                   translate=True):
    return self.write_text_to_draw(draw=draw, txt=txt, font_name=font_name, font_size=font_size, titleCase=titleCase, lowerCase=lowerCase, translate=translate, getXY_only=True)


  def get_im_data_d_from_filename(self, filename, units='pt', target_width=0, max_height=0):
    import base64

    if type(filename) == str or type(filename) == str:
      if os.path.exists(filename):
        im = Image.open(filename)
        data = open(filename, 'rb').read()
        data = base64.b16encode(data)
    d = {}
    if units == 'twip':
      multiplier = 10
    else:
      multiplier = 1
    if not target_width:
      d.setdefault('image_height', im.size[1] * multiplier)
      d.setdefault('image_width', im.size[0] * multiplier)
    else:
      h = int((im.size[1] / im.size[0]) * target_width)
      if max_height and h > max_height:
        h = max_height
        w = int((im.size[0] / im.size[1]) * max_height)
      else:
        w = target_width
      d.setdefault('image_height', h)
      d.setdefault('image_width', w)


    d.setdefault('image_format', im.format)
    d.setdefault('image_data', data)
    return d


  def get_im_and_draw_from_filename(self, filename):
    if type(filename) == str:
      if os.path.exists(filename):
        im = Image.open(filename)
        draw = ImageDraw.Draw(im)
      else:
        im = None
        draw = None
    return im, draw


  def make_round_corners(self, im, radius=10, colour=(80, 130, 130)):
    cache = {}
    im = RoundedCorners.round_image(im, cache, radius, solid_colour=colour)
    return im

  def deal_with_encodings_and_languages(self):
    ''' Determines the font and some font settings for various encodings '''

    encoding = 'unic'
    original_font_size = self.font_size
    if self.gui_language_encoding not in self.good_encodings:
      self.gui_language_encoding = "unic"
      encoding = 'unic'
      if self.gui_current_language == "Chinese":
        self.font_name = OV.GetParam('gui.chinese_font_name')
      else:
        self.font_name = 'Arial UTF'
      if not self.translate:
        self.font_name = "DefaultFont"
        self.font_size = original_font_size

    try:
      self.txt.encode('ascii')
    except:
      if self.gui_current_language != "Chinese":
        self.font_name = 'DefaultFont'
        # self.top -= 3
      else:
        pass

    if self.gui_current_language == "Chinese":
      self.font_peculiarities.setdefault("Arial UTF", {"top_adjust":-0.7,
                                                 "rel_adjust":+0.4})
    elif self.gui_current_language == "Greek":
      self.font_peculiarities.setdefault("Arial UTF", {"top_adjust":-1,
                                                 "rel_adjust":+0.4})
    elif self.gui_current_language == "Russian":
      self.font_peculiarities.setdefault("Arial UTF", {"top_adjust":-1,
                                                 "rel_adjust":+0.4})


  def get_font_peculiarities(self):
    self.font_peculiarities = {
      "Paddington":{"top_adjust":0,
                    "rel_adjust":0},
      "Verdana":{"top_adjust":-0.1,
                    "rel_adjust":+0.1},
      "Trebuchet":{"top_adjust":-0.5,
                    "rel_adjust":+0.2},
      "Helvetica":{"top_adjust":-0.5,
                    "rel_adjust":0.1},
      "Courier":{"top_adjust":-0.1,
                    "rel_adjust":+0.1},
      "Vera":{"top_adjust":0,
                    "rel_adjust":-0.1},
      "Signika":{"top_adjust":0,
                    "rel_adjust":-0.1},
      "Simhei TTF":{"top_adjust":-0.2,
                    "rel_adjust":+0.3},
      }
    self.font_peculiarities.setdefault("DefaultFont", self.font_peculiarities["Signika"])

  def get_text_modifications(self):
    if self.translate:
      self.txt = OV.Translate("%%%s%%" % self.txt.strip())  # #Language
    if self.titleCase:
      self.txt = self.txt.title()
    if self.lowerCase:
      self.txt = self.txt.lower()

  def get_valign_font_modifications(self):
    if not self.valign:
      self.txt_top += self.top_adjust + OV.GetParam('gui.font_top_system_adjust', 0)
      return
    try:
      letting_width, lettering_height = get_text_size(self.draw, self.txt, font=self.font)
      rel_size = self.valign[1]
      position = self.valign[0]
      self.font_size = int(rel_size * self.image_size[1])
      while True:
        if lettering_height < (self.image_size[1] * (rel_size + self.rel_adjust)):
          self.font_size += 1
          lettering_height += 1
          self.txt_top += self.top_adjust
        else:
          break
    except Exception as err:
      print(err)

  def _shorten_text(self, txt, draw, left_start, width, font):
    tw = (get_text_size(draw, txt, font)[0])
    if tw < width:
      return txt

    n = int(len(txt)/2)
    txtbeg = txt[:n]
    txtend = txt [-n:]

    if left_start > width:
      left_start = 50 * self.scale
    else:
      left_start = left_start

    xx = 0
    while tw > width - left_start - 5 * self.scale:
      txtbeg = txt[:n]
      txtend = txt [-n:]
      tw = (get_text_size(draw, "%s...%s" %(txtbeg, txtend), font)[0])
      n -= 1
      xx += 1
      if xx > 100 * self.scale:
        break
    return "%s...%s" %(txtbeg, txtend)


  def write_text_to_draw(self,
                         draw,
                         txt,
                         top_left=(1, 0),
                         font_name="DefaultFont",
                         font_size=11,
                         font_colour="#000000",
                         align="left",
                         max_width=1000,
                         image_size=None,
                         titleCase=False,
                         lowerCase=False,
                         valign=None,
                         translate=True,
                         getXY_only=False,
                         scale=1):

    # if max_width < 100:
    #  max_width = OV.GetParam('gui.htmlpanelwidth')

    if not self.scale:
      self.scale = scale
    self.font_size = font_size
    self.font_name = font_name
    self.translate = translate
    self.txt = txt
    self.txt_top = top_left[1]
    self.txt_left = top_left[0]
    self.titleCase = titleCase
    self.lowerCase = lowerCase
    self.valign = valign
    self.draw = draw
    self.image_size = image_size

    self.get_text_modifications()
    self.deal_with_encodings_and_languages()
    txt = self.txt = OV.correct_rendered_text(self.txt)
    font = self.get_font(font_name=self.font_name, font_size=self.font_size)
    self.font = font

    if txt == "%%":
      txt = "%"
    self.font_colour = font_colour

    self.get_valign_font_modifications()

    if align == "centre" or align == 'middle':
      self.txt_left = (self.centre_text(draw, txt, font, max_width))

    elif align == "right":
      self.txt_left = (self.align_text(draw, txt, font, max_width, 'right'))

    wX, wY = get_text_size(draw, txt, font=font)
    if getXY_only:
      return wX, wY

    txt_l = []
    t = ""
    wXT = 0
    if wX > max_width and " " in txt:
      txt_in = txt.split()

      for word in txt_in:
        wX, wY = get_text_size(draw, word, font=font)
        wXT += wX
        if wXT < max_width-1:
          t += " %s" % word
        else:
          txt_l.append(t.strip())
          wXT = 0
          t = "%s" % word
      txt_l.append(t.strip())
    else:
      txt = self._shorten_text(txt, draw, 0, max_width, font)

    if "</p>" in txt:
      self.txt = txt
      self.print_html_to_draw()
      return
    elif '<br>' in txt:
      txt = txt.split('<br>')
      txt_l = txt
    else:
      txt_l.append(txt)

    if not self.abort:
      if type(font_colour) != str and type(font_colour) != tuple and type(font_colour) != str:
        try:
          font_colour = font_colour.hexadecimal
        except Exception as ex:
          print("font_colour is ill defined: %s" % ex)
      try:
        i = 0
        for txt in txt_l:
          left = self.txt_left
          top_n = self.txt_top + wY * i
          if '<sub>' in txt:
            t = txt.split('<sub>')
            _ = t[1].split('</sub>')
            t[1] = _[0]
            t.append(_[1])
            j = 0
            for item in t:
              top = int(top_n)
              f = font
              if j == 1:
                f = self.get_font(font_name, int(font_size * 0.7))
                top += int(font_size / 2)
              j += 1
              wX, wY = get_text_size(draw, item, font=f)
              draw.text((left, top), item, font=f, fill=font_colour)
              left += wX
          else:
            draw.text((left, int(top_n)), txt, font=font, fill=font_colour)
          i += 1
      except Exception as ex:
        print("Text %s could not be drawn: %s" % (txt, ex))
    else:
      pass
    return wX, wY

  def print_html_to_draw(self):
    top = self.txt_top
    left = self.txt_left
    gap = 5 * self.scale

    self.txt = self.txt.strip().replace('\n', '')
    l = self.txt.split('</p>')
    for line in l:
      if not line:
        continue
      line = line.strip()
      _ = line.split('>')
      if 'class' in line:
        self.css_class = _[0].strip(' ').split('class=')[1]
        self.set_css_settings()
      txt = ">".join(_[1:])

      if '<b>' in txt:
        l = left
        t = txt.split('<b>')
        for item in t:
          if "</b>" in item:
            f = self.get_font("%s Bold" % self.font_name, self.font_size)
            item = item.strip("</b>")
          else:
            f = self.font
          bX, bY = get_text_size(self.draw, item, font=f)
          self.draw.text((l, top), item, font=f, fill=self.font_colour)
          l += bX
        top += self.line_height

      else:
        self.draw.text((left, top), txt, font=self.font, fill=self.font_colour)
        top += self.line_height

  def set_css_settings(self):
    c = OV.GetParam('gui.css.%s' % self.css_class)
    if not c:
      return
    self.font_name = OV.GetParam('gui.css.%s.font_name' % self.css_class)
    self.font_size = OV.GetParam('gui.css.%s.font_size' % self.css_class) * self.scale
    self.font_colour = OV.GetParam('gui.css.%s.color' % self.css_class).hexadecimal
    self.get_font()
    self.line_height = OV.GetParam('gui.css.%s.line_height' % self.css_class) * self.scale


  def addTransparancy(self, im, target_colour=(255, 255, 255)):
    mask = im.point(lambda i : i == 0 and 0)  # create RGB mask
    mask = mask.convert('L')  # mask to grayscale
    mask = mask.point(lambda i : i == 0 and 0)  # mask to B&W grayscale
    mask = ImageChops.invert(mask)
    # merge mask with image
    R, G, B = im.split()
    n_img = Image.merge('RGBA', (R, G, B, mask))
    return n_img

  def removeTransparancy(self, im, target_colour=(255, 255, 255)):
    # Remove transparency
    white = Image.new("RGB", im.size, target_colour)  # Create new white image
    r, g, b, a = im.split()
    im = Image.composite(im, white, a)  # Create a composite
    return im

  def getTxtWidthAndHeight(self, txt, font_name="DefaultFont", font_size=12):
    global sizedraw_dummy_draw
    font = self.fonts[font_name]["fontInstance"].get(font_size, None)
    if not font:
      font = self.registerFontInstance(font_name, font_size)
    wX, wY = get_text_size(sizedraw_dummy_draw, txt, font=font)
    try:
      offset = font.getoffset(txt)[1]
    except Exception as e:
      #print e
      offset = 0
    return wX, wY, offset

  def get_font(self, font_name=None, font_size=None):
    system_top_adjust = OV.GetParam('gui.font_top_system_adjust', 0)
    if not font_name: font_name = self.font_name
    if not font_size: font_size = self.font_size
    self.top_adjust = 0
    self.rel_adjust = 0
    try:
      font = self.fonts[font_name]["fontInstance"].get(font_size, None)
      if not font:
        font = self.registerFontInstance(font_name, font_size)
      if self.font_peculiarities.get(font_name):
        self.top_adjust = self.font_peculiarities[self.font_name].get('top_adjust', 0) + system_top_adjust
        self.rel_adjust = self.font_peculiarities[self.font_name].get('rel_adjust', 0) + system_top_adjust
    except:
      pass
    self.font = font
    return font

  def make_pop_image(self, d):
    size = d.get('size')
    bgcolour = d.get('bgcolour')
    txt_l = d.get('txt')
    name = d.get('name')
    im = Image.new("RGB", size, bgcolour)
    draw = ImageDraw.Draw(im)

    margin = 4

    line_count = 0
    curr_pos_x = margin
    curr_pos_y = margin
    for t in txt_l:
      txt = t.get('txt')
      colour = t.get('colour')
      font_size = t.get('size')
      font_weight = t.get('weight')
      font_name = "%s %s" % (self.gui_timage_font_name, font_weight)
      font_name = font_name.strip()
      after = t.get('after')

      font = self.fonts[font_name]["fontInstance"].get(font_size, None)
      if not font:
        font = self.registerFontInstance(font_name, font_size)
      wX, wY = get_text_size(draw, txt, font=font)

      self.write_text_to_draw(
        draw,
        txt,
        top_left=(curr_pos_x, curr_pos_y),
        font_name=font_name,
        font_size=font_size,
        font_colour=colour,)

      if '<br>' in after:
        s = after.split('<br>')
        if len(s) > 1:
          mul = s[1]
          if not mul: mul = 0
          mul = int(wY * float(mul))
          curr_pos_y += (wY + mul)
        line_count += 1
        curr_pos_x = margin
      else:
        curr_pos_x += wX

    OlexVFS.save_image_to_olex(im, name, 2)

  def draw_advertise_new(self, draw, image):
    max_width = image.size[0]
    max_height = image.size[1]
    font_name = "%s Bold" % OV.GetParam('gui.html.font_name')
    font_size = int(max_height) - 5
    colour = OV.GetParam('gui.html.highlight_colour')
    txt = "New!"
    dX, dY = self.getTxtWidthAndHeight(txt, font_name, font_size)
    from_right = 15
    left_start = max_width - dX - from_right
    draw.rectangle((left_start, 2, max_width - from_right, int(dY * 0.75)), fill='#ffee00')
    # draw.ellipse((left_start, -dY, max_width - from_right, int(dY*0.8)), fill='#ffee00')

    self.write_text_to_draw(
      draw,
      txt=txt,
      top_left=(left_start, -1),
#      align='right',
      max_width=max_width - 1,
      font_name=font_name,
      font_size=font_size,
      titleCase=True,
      font_colour=colour,)

    # font_size = 8
    # txt = "New!"
    # dX, dY = self.getTxtWidthAndHeight(txt, font_name, font_size)
    # IM = Image.new('RGBA', (dX, dY))
    # IMdraw = ImageDraw.Draw(IM)
    # IMdraw.rectangle((0, 0, dX + 2, dY), fill='#ffee00')
    # self.write_text_to_draw(
      # IMdraw,
      # txt = txt,
      # top_left=(0, -1),
      # max_width=max_width,
      # font_name=font_name,
      # font_size=font_size,
      # titleCase=True,
      # font_colour=colour,)
    # OlexVFS.save_image_to_olex(IM, "new", 2)


  def create_arrows(self, image, draw, height, direction, colour, type='simple', h_space=4, v_space=4, offset_y=0, char_pos=(0, 0), char_char="+", width=10, align='left', scale=1.0):
    if align == 'right':
      adval_parameter = OV.GetParam('gui.timage.adval')
      adval = int(round(adval_parameter * scale, 0))
      char_pos = (width - adval, char_pos[1])
      h_space = width - h_space - adval
      # h_space = width - height
    arrow_height = height - (2 * v_space)
    arrow_width = arrow_height

    arrow_height = int(round(arrow_height * scale, 0))
    arrow_width = int(round(arrow_width * scale, 0))
    # h_space = int(round(h_space*scale/1,0))
    v_space = int(round(v_space * (1 / scale), 0))

    if arrow_width % 2 != 0:
      arrow_width -= 1
      arrow_height -= 1
    arrow_half = int(round(arrow_width / 2, 0))
    if type == 'simple':
      if direction == 'up':
        h_space -= 2
        v_space += 2
        begin = (h_space, height - v_space + 1)
        middle = (h_space + arrow_half, v_space - 1)
        end = (h_space + arrow_width, height - v_space + 1)
      elif direction == 'down':
        h_space -= 1
        v_space += 1
        begin = (h_space, v_space)
        middle = (h_space + arrow_half, height - v_space)
        end = (h_space + arrow_width, v_space)
      elif direction == "right":
        h_space += 1
        begin = (h_space, v_space)
        middle = (arrow_width + 1, height / 2)
        end = (h_space, height - v_space)
      elif direction == "right_":
        begin = (3, 3)
        middle = (9, height / 2)
        end = (3, height - 3)
      draw.polygon((begin, middle, end), colour)
    elif type == "composite":
      if direction == "up":
        begin = (8, 5)
        middle = (4, height - 5)
        end = (8, height - 7)
        draw.polygon((begin, middle, end), self.adjust_colour(colour, luminosity=0.8))
        middle = (12, height - 5)
        draw.polygon((begin, middle, end), self.adjust_colour(colour, luminosity=0.6))
      if direction == "down":
        begin = (8, height - 5)
        middle = (4, 5)
        end = (8, 7)
        draw.polygon((begin, middle, end), fill=self.adjust_colour(colour, luminosity=0.8))
        middle = (12, 5)
        draw.polygon((begin, middle, end), fill=self.adjust_colour(colour, luminosity=0.6))
    elif type == "char":
      font_size = int(13 * scale)
      font_name = "%s Bold" % self.gui_timage_font_name
      if char_pos == "Auto":
        wX, wY = self.getTxtWidthAndHeight(char_char, font_name, font_size)
        char_pos = (width * scale - wX - 5, 1)

      self.write_text_to_draw(
        draw,
        char_char,
        top_left=char_pos,
        font_name=font_name,
        font_size=font_size,
        titleCase=True,
        font_colour=colour,)

    elif type == "circle":
      xy = (4, 4, 8, 8)
      draw.ellipse(xy, fill=colour)

    elif type == "dots":
      dot_size = OV.GetParam('gui.timage.cbtn.dot_size')
      pad = OV.GetParam('gui.timage.cbtn.dot_pad')
      left_start = OV.GetParam('gui.timage.cbtn.dot_left')
      colour_off = OV.GetParam('gui.timage.cbtn.dot_colour_off').hexadecimal
      colour_on = OV.GetParam('gui.timage.cbtn.dot_colour_on').hexadecimal
      l = (width - height + left_start) * scale
      t = pad
      b = height - pad
      r = width - pad

      mark = self.get_PIL_image_from_olex_VFS('%s_raw.png' % direction)

      if mark:
        watermark = True
        if watermark:
          _ = image.size[1] - (pad*scale*2)
          mark = mark.resize((_,_), Image.LANCZOS)
          image = self.watermark(image, mark, (int(round(l)), int(round(t))), opacity=1)
        else:
          mark_colouriszed = self.colourize(mark, (0, 0, 0), self.params.html.base_colour.rgb)
          IM = Image.new('RGBA', mark.size)
          IM.paste(mark_colouriszed, (0, 0), mark)
          IM = self.resize_image(IM, (image.size[1], image.size[1]), name="mark_colourised")
          image.paste(IM, (l, t))
        return image
      else:
        if direction == "up":

          fill = colour_on
          i = 0
          top = b - pad
          w_counter = 0
          while top > (pad + dot_size) and w_counter < 1000:
            w_counter += 1
            left = l + i * dot_size / 2
            top = b - i * dot_size - dot_size
            xy = (int(left), int(top), left + dot_size, top + dot_size)
            draw.ellipse(xy, fill=fill)
            i += 1
          j = i
          w_counter = 0
          while top < (height - pad - dot_size) and w_counter < 1000:
            w_counter += 1
            left = l + j * dot_size / 2
            top = b - i * dot_size - dot_size
            xy = (int(left), int(top), left + dot_size, top + dot_size)
            draw.ellipse(xy, fill=fill)
            i -= 1
            j += 1
        elif direction == 'down':
          fill = colour_off
          i = 0
          top = t
          w_counter = 0
          while (top < height - pad - dot_size * 2) and w_counter < 1000:
            w_counter += 1
            left = l + i * dot_size / 2
            top = t + i * dot_size
            xy = (int(left), int(top), left + dot_size, top + dot_size)
            draw.ellipse(xy, fill=fill)
            i += 1
          j = i
          w_counter = 0
          while top > pad and w_counter < 1000:
            w_counter += 1
            left = l + j * dot_size / 2
            top = t + i * dot_size
            xy = (int(left), int(top), left + dot_size, top + dot_size)
            draw.ellipse(xy, fill=fill)
            i -= 1
            j += 1
        elif direction == "right":
          im_data = OlexVFS.read_from_olex('toolbar-dot-arrow-right.png')
        elif direction == "left":
          im_data = OlexVFS.read_from_olex('toolbar-dot-arrow-left.png')

#      IM = Image.open(StringIO(im_data))
#      IM = IM.resize((height, height))
#      box = (width - height, 0)
#      image.paste(IM, box)

  def make_simple_text_to_image(self, width, height, txt, font_name="DefaultFont", font_size=16, bg_colour='#fff6bf', font_colour='#222222'):
    IM = Image.new('RGB', (width, height), bg_colour)
    draw = ImageDraw.Draw(IM)
    txt = txt.strip()
    self.write_text_to_draw(
      draw,
      top_left=(3, 3),
      max_width=width - 40,
      txt=txt,
      font_name=font_name,
      font_size=font_size,
      titleCase=False,
      font_colour=font_colour,)
    return IM

  def make_border(self, rad,
              draw,
              width,
              height,
              border_colour,
              bg_colour="white",
              cTopLeft=True,
              cTopRight=True,
              cBottomLeft=True,
              cBottomRight=True,
              shift=1,
              border_hls=(0, 1, 1),
              ):
    hrad = int(rad / 2 - 1)
    hrad_TL = 0
    hrad_TR = 0
    hrad_BL = 0
    hrad_BR = 0

    # border_colour = bg_colour
    border_colour = self.adjust_colour(border_colour, hue=border_hls[0], luminosity=border_hls[1], saturation=border_hls[2])
    # border top
    begin = (0, 0)
    end = (width, 0)
  #       draw.line((begin ,end), fill=border_colour['top'])
    draw.line((begin , end), fill=border_colour)

    # border bottom
    begin = (0, height - 1)
    end = (width - 1, height - 1)
  #       draw.line((begin ,end), fill=border_colour['bottom'])
    draw.line((begin , end), fill=border_colour)

    # border left
    begin = (0, 0)
    end = (0, height - 1)
  #       draw.line((begin ,end), fill=border_colour['left'])
    draw.line((begin , end), fill=border_colour)

    # border right
    begin = (width - 1 , 0)
    end = (width - 1, 0)
  #       draw.line((begin ,end), fill=border_colour['right'])
    draw.line((begin , end), fill=border_colour)

    rect_colour = OV.GetParam('gui.html.bg_colour')
    pie_colour = bg_colour

    pie_colour = (0, 0, 0, 255)
    rect_colour = (0, 0, 0, 255)
    # top-left corner
    if cTopLeft:
      draw.rectangle((0, 0, hrad, hrad), fill=rect_colour)
      draw.pieslice((0, 0, rad, rad), 180, 270, fill=pie_colour)
      draw.arc((0, 0, rad, rad), 180, 270, fill=border_colour)
      hrad_TL = hrad
    # bottom-right corner
    if cBottomRight:
      draw.rectangle((width - hrad, height - hrad, width, height), fill=rect_colour)
      draw.pieslice((width - rad - shift, height - rad - shift, width - shift, height - shift), 0, 90, fill=pie_colour)
      draw.arc((width - rad - shift, height - rad - shift, width - shift, height - shift), 0, 90, fill=border_colour)
      hrad_BR = hrad
    # bottom-left corner
    if cBottomLeft:
      draw.rectangle((0, height - hrad, hrad, height), fill=rect_colour)
      draw.pieslice((0, height - rad - shift, rad, height - shift), 90, 180, fill=pie_colour)
      draw.arc((0, height - rad - shift, rad, height - shift), 90, 180, fill=border_colour)
      hrad_BL = hrad
    # top-right corner
    if cTopRight:
#      draw.rectangle((width-hrad, 0, width, hrad), fill=rect_colour)
#      draw.pieslice((width-rad-shift, 0, width-shift, rad), 270, 360, fill=pie_colour)
      draw.arc((width - rad - shift, 0, width - shift, rad), 270, 360, fill=border_colour)
      hrad_TR = hrad

    # border top
    begin = (hrad_TL, 0)
    end = (width - hrad_TR, 0)
    draw.line((begin , end), fill=border_colour)

    # border bottom
    begin = (hrad_BL - 1, height - 1)
    end = (width - hrad_BR - 1, height - 1)
    draw.line((begin , end), fill=border_colour)

    # border left
    begin = (0, hrad_TL)
    end = (0, height - hrad_BL - 1)
    draw.line((begin , end), fill=border_colour)

    # border right
    begin = (width - 1 , hrad_TR)
    end = (width - 1, height - hrad_TL)
    draw.line((begin , end), fill=border_colour)


  def make_pie_graph(self, number=3, segments=[('R', 0.5, '#ee0000'), ('G', 0.5, '#00ee00')], rotation=-90, name='fred'):
    rotation = int(rotation)
    number = int(number)
    red = self.gui_red
    green = self.gui_green
    blue = self.gui_blue
    grey = self.gui_grey
    colours = [red, green, blue, grey]

    map_l = []

    if not number:
      number = len(segments)
    if number == 2:
      rotation = 90
      segments = [('Solve', 0.5, red), ('Refine', 0.5, green)]
      rad_factor = 4
    if number == 3:
      segments = [('R', 0.333, red), ('G', 0.333, green), ('B', 0.333, blue)]
      rad_factor = 4
    if number == 4:
      rotation = -135
      segments = [('R', 0.25, red), ('G', 0.25, green), ('B', 0.25, blue), ('Grey', 0.25, '#888888')]
      rad_factor = 3.4

    colour = (0, 0, 0, 0)
    colour = OV.GetParam('gui.html.bg_colour').rgb
    size = (300, 300)
    im_size = (size[0] + 1, size[1] + 1)
    IM = Image.new('RGBA', im_size, colour)
    draw = ImageDraw.Draw(IM)
    font_size = int(size[0] / 8)
    font_name = "DefaultFont Bold"
    font = self.get_font(font_size=font_size, font_name=font_name)
    font_colour = '#ababab'
    border_colour = "#ffffff"
    border_width = 0
    rad_width = size[0] - 2 - border_width * 2
    rad_height = size[1] - 2 - border_width * 2
    margin = 0
    center = (int(size[0] / 2), int(size[1] / 2))
    draw.ellipse((margin, margin, rad_width, rad_height), fill=border_colour)

    curr_end = rotation
    i = 0
    for segment in segments:
      var = segment[0]
      map_l.append({'var':var, 'href':var, 'target':var})
      value = 1 / len(segments)
      pie_colour = colours[i]
      begin = int(curr_end)
      end = begin + int(round(360 * value, 0))
      draw.pieslice((margin + border_width, margin + border_width, rad_width, rad_height), begin, end, fill=pie_colour)
      curr_end = end
      i += 1

    curr_end = 0
    if number == 2:
      curr_end = 180
    elif number == 4:
      curr_end = -45

    i = 0
    for segment in segments:
      var = segment[0]
      pie_colour = colours[i]
      font_colour = self.adjust_colour(pie_colour, luminosity=1.6)
      font_colour = '#ffffff'
      begin = int(curr_end)
      end = begin + int(round(360 * value, 0))
      angle = (end - begin) / 2 + begin
      angle = math.radians(angle)

      wX, wY = self.textsize(draw, var, font_size, font_name)
      left = (center[0] + math.sin(angle) * rad_width / rad_factor) - wX / 2
      top = ((center[1] + (math.cos(angle) * -1) * rad_height / 3.2)) - wY / 2

      draw.text((int(left), int(top)), var, font=font, fill=font_colour)
      curr_end = end
      i += 1

    map_width = 200
    map_height = 100
    pie_map = self.make_pie_map(map_l, (map_width, map_height))

    html = '''
<table align='center' width='100%%'>
<tr align='center'>
<td align='center'>
<zimg border="0" width="200" height="100" src="fred.png" usemap="pie">
%s
</td>
</tr>
</table>''' % (pie_map)

    IM.save("%s/%s.png" % (OV.DataDir(), name))
    OlexVFS.save_image_to_olex(IM, name, 1)
    OlexVFS.write_to_olex('pie.htm', html, True)
    OV.UpdateHtml()

  def get_PIL_image_from_olex_VFS(self, name):
    import io

    if olx.fs.Exists(name) != "true":
      from PilTools import timage
      a = timage()
      a.make_images_from_fb_png()

    if olx.fs.Exists(name) == "true":
      _ = OlexVFS.read_from_olex(name)
      sio = io.BytesIO(_)
      retVal = Image.open(sio)
    else:
      retVal = False
    return retVal

  def trim_image(self, im, trimcolour=None, padding=None, border=None, border_col=None, dry=False, target_size=None):
    ''' Takes either an image or a path to an image, then trims off all whitespace and either returns the trimmed image or saves it to the same path as the original one '''

    if not padding:
      padding = float(OV.GetParam('user.image.bitmap.trim_padding',1))
    if not border:
      border = float(OV.GetParam('user.image.bitmap.trim_border',1))
    if not border_col:
      border_col = OV.GetParam('user.image.trim_border_colour')

    from PIL import Image, ImageChops, ImageOps
    p = None
    if type(im) == str or type(im) == str:
      im = im.strip("'")
      im = im.strip('"')
      if os.path.exists("%s" % im):
        p = im
        try:
          im = Image.open("%s" % im)
        except:
          print("Sorry, cannot trim image of this kind")
          return
      else:
        print("No such image")
        return

    if not trimcolour and OV.HasGUI():
      import struct
      _ = struct.unpack("4B",struct.pack(">I",int(olx.gl.lm.ClearColor())))
      trimcolour = (_[3], _[2], _[1])

    original_width = im.size[0]
    bg = Image.new(im.mode, im.size, trimcolour)
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    im = im.crop(bbox)

    padding = int(im.size[0] / 100 * padding)
    border = int(im.size[0] / 100 * border)
    border_col = str(border_col)

    adjust = 0
    if target_size:
      curr_width = im.size[0] + padding * 2 + border * 2
      diff = target_size - curr_width
      padding += int(diff / 2)
      curr_width = im.size[0] + padding * 2 + border * 2
      if curr_width > target_size:
        adjust = -1
      elif curr_width < target_size:
        padding += 1
        adjust = -1

    if padding:
      im = ImageOps.expand(im, border=padding, fill=trimcolour)
    if adjust:
      bbox = (0, 0, im.size[0] - 1, im.size[1])
      im = im.crop(bbox)
    if border:
      im = ImageOps.expand(im, border=border, fill=border_col)
    if dry:
      return im.size[0], original_width
    if p:
      im.save(p)
    else:
      return im

  def make_pie_map(self, map_l, size):

    width = size[0]
    height = size[1]
    map = "<map name='pie'>"

    if len(map_l) == 2:
      i = 0
      for item in map_l:
        href = item.get('href', 'n/a')
        target = item.get('target', 'n/a')
        left = i * int(width / 2)
        if i == 0:
          right = width / 2
        else:
          right = width
        if len(map_l) == 4:
          top = i * height / 2
          bottom = height
        elif len(map_l) == 2:
          top = 0
          bottom = height
        map += '''
<area shape='rect' coords='%s,%s,%s,%s' href='%s' target='%s'>''' % (int(left), int(top), int(right), int(bottom), href, target)
        i += 1

#      <area shape='rect'
#        coords='100,0,200,100'
#        href='refine'
#        target='refine'>
#      </map>'''
    # elif len(map_l) == 3:
      # map = '''
      # <map name='pie'>
      # <area shape='rect'
        # coords='0,0,100,100'
        # href='solve'
        # target='solve'>
      # <area shape='rect'
        # coords='100,0,200,100'
        # href='refine'
        # target='refine'>'''
#    elif len(map_l) == 4:
      # #map = '''
      # #<map name='pie'>
      # #<area shape='rect'
        # #coords='0,0,100,100'
        # #href='solve'
        # #target='solve'>
      # #<area shape='rect'
        # #coords='100,0,200,100'
        # #href='refine'
        # #target='refine'>
      # #</map>'''
    map += "</map>"
    return map

IT = ImageTools()
IT.get_available_width()
if olx.HasGUI() == 'true':
  OV.registerMacro(IT.resize_to_panelwidth, 'i-Image&;c-Colourize')
  OV.registerFunction(IT.make_pie_graph, False, 'it')

OV.registerFunction(IT.trim_image, False, 'it')
