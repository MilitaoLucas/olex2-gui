#-*- coding:utf8 -*-

from __future__ import division
#import PngImagePlugin
import Image
import ImageDraw, ImageChops, ImageColor
import OlexVFS
import RoundedCorners
from ArgumentParser import ArgumentParser
import colorsys
from olexFunctions import OlexFunctions
from FontInstances import FontInstances
OV = OlexFunctions()
import os
global sizedraw
sizedraw_dummy_draw  = ImageDraw.Draw(Image.new('RGBA',(300, 300)))
import olx


class ImageTools(FontInstances):
  def __init__(self):
    import ImageColor
    super(ImageTools, self).__init__()
    self.colorsys = colorsys
    self.abort = False
    self.getOlexVariables()
    self.gui_language_encoding = OV.CurrentLanguageEncoding()
    #font = "Vera"
    #font = "VeraSE"
    #font = "VeraMono"
    font = "Verdana"
    #font = "Trebuchet"
    #font = "HelveticaMedCd"
    #font = "Optane"
    self.gui_timage_font_name = "%s" %font
    self.gui_tab_font_name = "%s Bold" %font
    self.gui_sNumTitle_font_name = "%s Bold" %font
    self.gui_button_font_name = "%s Bold" %font

    
  def show_image(self, IM):
    import sys
    sys.path.append("C:\Users\Horst\Documents\olex-trunk\Python26\Lib\site-packages\wx-2.8-msw-unicode")
    import wx
    a = wx.PySimpleApp()
    wximg = wx.Image('%s/splash.jpg' %OV.BaseDir(),wx.BITMAP_TYPE_JPEG)
    wxbmp=wx.BitmapFromImage( wximg )
    f = wx.Frame(None, -1, "Show JPEG demo")
    f.SetSize( wxbmp.GetSize() )
    wx.StaticBitmap(f,-1,wxbmp,(0,0))
    f.Show(True)
    
    def callback(evt,a=a,f=f):
      # Closes the window upon any keypress
      f.Close()
      a.ExitMainLoop()
      wx.EVT_CHAR(f,callback)
      a.MainLoop()
    
    
  def get_unicode_characters(self, txt):
    txt = txt.replace("lambda", unichr(61548))
    txt = txt.replace("theta", unichr(61553))
    txt = txt.replace("sigma", unichr(61555))
    txt = txt.replace("^2", unichr(178))
    txt = txt.replace("^3", unichr(179))
    txt = txt.replace(">", unichr(61681))
    txt = txt.replace("<", unichr(61665))
    txt = txt.replace("Fo2", "Fo%s" %(unichr(178)))
    txt = txt.replace("Fexp", "F%s" %(unichr(2091)))
    #txt  = txt.replace("info", unichr(65353))
    txt  = txt.replace("info", unichr(61600))
    return txt
    
    
  def centre_text(self, draw, txt, font, maxWidth):
    txt_size = draw.textsize(txt, font=font)
    hStart = int((maxWidth - txt_size[0])/2)
    return hStart
  
  def align_text(self, draw, txt, font, maxWidth, align):
    if align == "centre":
      txt_size = draw.textsize(txt, font=font)
      hStart = int((maxWidth - txt_size[0])/2)
      retVal = hStart
    if align == "right":
      txt_size = draw.textsize(txt, font=font)
      hStart = int((maxWidth - txt_size[0]))
      retVal = hStart
    return retVal
    
    
  def getOlexVariables(self):
    self.getVariables('gui')
    #self.encoding = self.test_encoding(self.gui_language_encoding) ##Language
    #self.language = "English" ##Language
    #if olx.IsCurrentLanguage('Chinese') == "true":
    #  self.language = 'Chinese'
    self.fonts = self.defineFonts()
 
  def dec2hex(self, n):
    """return the hexadecimal string representation of integer n"""
    return "%X" % n
     
  def hex2dec(self, s):
    """return the integer value of a hexadecimal string s"""
    l = list(s)
    c = "%s%s%s%s%s%s" %(l[5], l[6], l[3], l[4], l[1], l[2])
    return int(c, 16)    
        
    
  def RGBToHTMLColor(self, rgb_tuple):
      """ convert an (R, G, B) tuple to #RRGGBB """
      hexcolor = '#%02x%02x%02x' % rgb_tuple
      # that's it! '%02x' means zero-padded, 2-digit hex values
      return hexcolor

  def HTMLColorToRGB(self, colorstring):
      """ convert #RRGGBB to an (R, G, B) tuple """
      colorstring = colorstring.strip()
      if colorstring[0] == '#': colorstring = colorstring[1:]
      if len(colorstring) != 6:
          raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
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
    layer = Image.new('RGBA', im.size, (0,0,0,0))
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
  
  
  def makeBackgroundTransparent(self, img, col=(255,255,255)):
    
    col = self.HTMLColorToRGB(col)
    img = img.convert("RGBA")
    pixdata = img.load()

    for y in xrange(img.size[1]):
      for x in xrange(img.size[0]):
        if pixdata[x, y] == (255, 255, 255, 255):
            pixdata[x, y] = (255, 255, 255, 0)
    return img

  def makeTransparentText(self, im, txt, top_left=(1,0), font_colour="#000000", font_name = "Arial Bold", font_size=14):
    # Make a grayscale image of the font, white on black.
    font_file = self.fonts[font_name]
    imtext = Image.new("L", im.size, 0)
    alpha = Image.new("L", im.size, "Black")
    drtext = ImageDraw.Draw(imtext)
    font = ImageFont.truetype(font_file, font_size)
    drtext.text(top_left, txt, font=font, fill="white")
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
  
  def make_colour_sample(self, colour, size=(20,12)):
    if not colour:
      return
    IM = Image.new('RGBA', size, colour)
    draw = ImageDraw.Draw(IM)
    draw.rectangle((0, 0, IM.size[0]-1, IM.size[1]-1), outline='#bcbcbc')

    name = r"colour_%s.png" %colour[1:]
    OlexVFS.save_image_to_olex(IM, name, 2)
    return name
  
  def resize_image(self, image, size):
    image = image.resize(size, Image.ANTIALIAS)
    return image

  def resize_skin_logo(self, width):
    #self.getVariables('gui')
    logopath = r"%s" %(self.gui_skin_logo_name)
    logopath = logopath.replace("basedir()", self.basedir)
    if os.path.exists(logopath):
      im = Image.open(logopath)
      width = int(width) - 20
      factor = im.size[0]/width
      height = int(im.size[1] / factor)
      im = self.resize_image(im, (width, height))
      name = r"skin_logo.png"
      OlexVFS.save_image_to_olex(im, name, 2)
    else:
      pass
    return "Done"

  def resize_to_panelwidth(self, args):
    name = args['i']
    colourize = args.get('c',False)
    path = ("%s/etc/%s" %(self.basedir, name))
    width = OV.FindValue('gui_htmlpanelwidth')
    if os.path.exists(path):
      im = Image.open(path)
      if colourize:
        im = self.colourize(im, (0,0,0), OV.FindValue('gui_logo_colour')) 
      width = int(width) - 47
      factor = im.size[0]/width
      height = int(im.size[1] / factor)
      im = self.resize_image(im, (width, height))
      name = name.split(".")[0]
      OlexVFS.save_image_to_olex(im, name, 2)
    else:
      pass
    return "Done"

  def reduce_opacity(self, im, opacity):
    """Returns an image with reduced opacity."""
    import ImageEnhance
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

  
  def add_vline(self, draw, height, h_pos, v_pos, weight=1, colour=(237,237,235)):
    begin = (h_pos, v_pos)
    end = (h_pos, height)
    draw.line((begin ,end), fill=self.adjust_colour(colour, luminosity = 1))
    pass

  def add_whitespace(self, image, side, weight, colour, margin_left=0, margin_right=0, margin_top=0, margin_bottom=0):
    width, height = image.size
    top = 0 + margin_top
    left = 0 + margin_left
    bottom = height - margin_bottom
    right = width - margin_right
    if side == "top":
      whitespace = Image.new('RGBA', (width - margin_left - margin_right, weight), colour)
      canvas = Image.new('RGBA', (width,height + weight),(0,0,0,0))
      canvas.paste(whitespace, (margin_left, 0))
      canvas.paste(image, (0, weight))
    elif side == "bottom":
      whitespace = Image.new('RGBA', (width - margin_left - margin_right, weight), colour)
      canvas = Image.new('RGBA', (width,height + weight),(0,0,0,0))
      canvas.paste(whitespace, (margin_left, height))
      canvas.paste(image, (0, 0))
    elif side == "right":
      whitespace = Image.new('RGBA', (weight, height - margin_top - margin_bottom), colour)
      canvas = Image.new('RGBA', (width + weight,height),(0,0,0,0))
      canvas.paste(whitespace, (width, margin_top))
      canvas.paste(image, (0, 0))
    elif side == "left":
      whitespace = Image.new('RGBA', (weight, height - margin_top - margin_bottom), colour)
      canvas = Image.new('RGBA', (width + weight,height),(0,0,0,0))
      canvas.paste(whitespace, (0, margin_top))
      canvas.paste(image, (weight, 0))
    return canvas

  def colourize(self, IM, col_1, col_2):
    import ImageOps
    #IM = self.removeTransparancy(IM, (255,255,255))
    IM= IM.convert("L")
    IM = ImageOps.colorize(IM, col_1, col_2) 
    return IM

  
  def add_continue_triangles(self, draw, width, height, shift_up = 4, shift_left = 5, style=('multiple')):
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
      begin = (width-beg_1,height-arrow_top)
      middle = (width-mid_1,height-arrow_middle)
      end = (width-beg_1, height-arrow_bottom)
      draw.polygon((begin, middle, end), colour)
      colour = self.adjust_colour(colour, luminosity=0.7)
      begin = (width-beg_2,height-arrow_top)
      middle = (width-mid_2,height-arrow_middle)
      end = (width-beg_2, height-arrow_bottom)
      draw.polygon((begin, middle, end), colour)
      colour = self.adjust_colour(colour, luminosity=0.7)
      begin = (width-beg_3,height-arrow_top)
      middle = (width-mid_3,height-arrow_middle)
      end = (width-beg_3, height-arrow_bottom)
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
        begin = (width-beg_3,height-arrow_top)
        middle = (width-mid_3,height-arrow_middle)
        end = (width-beg_3, height-arrow_bottom)
      elif direction == "up":
        begin = (width-beg_3+arrow_width/2,height-arrow_top)
        middle = (width-mid_3,height-arrow_bottom)
        end = (width-beg_3, height-arrow_bottom)
      elif direction == "down":
        begin = (width-beg_3,height-arrow_top)
        middle = (width-mid_3,height-arrow_top)
        end = (width-beg_3+arrow_width/2, height-arrow_bottom)
      elif direction == "left":
        begin = (width-beg_3 + arrow_width,height-arrow_top)
        middle = (width-beg_3,height-arrow_middle)
        end = (width-beg_3 + arrow_width, height-arrow_bottom)
      if begin:
        draw.polygon((begin, middle, end), colour)

  def adjust_colour(self, colour, hue=0, luminosity=1, saturation=1):
    hue = float(hue)
    luminosity = float(luminosity)
    saturation = float(saturation)
    if colour == 'base':
      colour = self.gui_timage_colour
    if colour == "bg":
      colour = self.gui_html_bg_colour
    if colour == "highlight":
      colour = self.gui_html_highlight_colour
    if colour == "gui_html_table_bg_colour":
      colour = self.gui_html_table_bg_colour
    else:
      colour = colour

    if "#" in colour:
      colour = ImageColor.getrgb(colour)
    c = self.colorsys.rgb_to_hls(*[x/255.0 for x in colour])
    l = list(c)
    l[0] = l[0] + hue/360.
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
    nc = tuple(l)
    return nc

    
    
  def gradient_bgr(self, draw, width, height, colour=(237,237,235), fraction=0.85, increment=10, step=1):
    inc = increment
    if "#" in colour: colour = self.HTMLColorToRGB(colour)
    for i in xrange(int(height*fraction)):
      if i < height/inc:
        adjusted_step = 0.6*step
      elif height/inc < i < (height/inc)*2:
        adjusted_step = 1.2*step
      else:
        adjusted_step = 1.4*step
      incrementA = int(adjusted_step*i*(58/height))
      incrementB = int(adjusted_step*i*(44/height))

      begin = (0,i)
      end = (width, i)
      R = int(colour[0]-incrementA)
      G = int(colour[1]-incrementA)
      B = int(colour[2]-incrementB)
      #print i, R,G,B
      draw.line((begin ,end), fill=(R, G, B))

      
  def sort_out_encoding():
    font = ImageFont.truetype("%s" %font_file, font_size, encoding=self.test_encoding("unic")) ##Leave in for Debug!
    try:  
      font_file = self.fonts.get(font_name, "arialuni.ttf")
      font = ImageFont.truetype("%s" %font_file, font_size, encoding=self.test_encoding("unic"))
     
    except:
      print "The font %s is required for this option." %font_name
      self.abort = True
    pass
  
  def textsize(self,
                   draw,
                   txt,
                   font_size,
                   font_name='Vera',
                   titleCase=False,
                   lowerCase=False,
                   translate=True):
    return self.write_text_to_draw(draw=draw, txt=txt, font_name=font_name, font_size=font_size, titleCase=titleCase, lowerCase=lowerCase, translate=translate, getXY_only=True)
    
  
  def write_text_to_draw(self,
                         draw,
                         txt, 
                         top_left=(1,0), 
                         font_name='Vera', 
                         font_size=11, 
                         font_colour="#000000", 
                         align="left", 
                         max_width=0, 
                         image_size=None,
                         titleCase=False,
                         lowerCase=False,
                         valign=None,
                         translate=True,
                         getXY_only=False):
    if translate:
      txt = OV.Translate("%%%s%%" %txt.strip()) ##Language
      

    if titleCase:
      txt = txt.title()
    if lowerCase:
      txt = txt.lower()
    top = top_left[1]
    left = top_left[0]

    
    good_encodings = ["ISO8859-1", "ISO8859-2", "ISO8859-7"]
    good_encodings = ["ISO8859-1", "ISO8859-2"]
    self.gui_language_encoding = olx.CurrentLanguageEncoding()
    self.gui_current_language = olx.CurrentLanguage()
    encoding = 'unic'
    if self.gui_language_encoding not in good_encodings:
      self.gui_language_encoding = "unic"
      encoding = 'unic'
      if self.gui_current_language == "Chinese":
        #font_name = "Simhei TTF"
        font_name = 'Arial UTF'
      else:
        font_name = 'Arial UTF'
      #font_name = "Chinese"
      #font_name = "Simsun TTF"
      #font_name = "Simsun TTC"
      original_font_size = font_size
      
      #if font_size < 18:
      #  font_size = 18
      
      if not translate:
        font_name = 'Vera'
        font_size = original_font_size
        
      
      try:
        txt.encode('ascii')
        font_name = 'Vera'
        font_size = original_font_size
      except:
        top -= 1
        pass
    
    

    if valign:
      
      top = top
      rel_size = valign[1]
      position = valign[0]
      font_size = int(rel_size * image_size[1])
      font = self.fonts[font_name]["fontInstance"].get(font_size,None)
      if not font:
        font = self.registerFontInstance(font_name, font_size)

      font_peculiarities = {
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
        "Simhei TTF":{"top_adjust":-0.2,
                      "rel_adjust":+0.3},
        }
      
      if self.gui_current_language == "Chinese":
        font_peculiarities.setdefault("Arial UTF",{"top_adjust":-0.7,
                                            "rel_adjust":+0.4})
        
      elif self.gui_current_language == "Greek":
        font_peculiarities.setdefault("Arial UTF",{"top_adjust":-1,
                                            "rel_adjust":+0.4})

      elif self.gui_current_language == "Russian":
        font_peculiarities.setdefault("Arial UTF",{"top_adjust":-1,
                                            "rel_adjust":+0.4})
        
        
      top_adjust = 0
      rel_adjust = 0
      for f in font_peculiarities:
        if f in font_name:
          top_adjust = font_peculiarities[f]["top_adjust"]
          rel_adjust = font_peculiarities[f]["rel_adjust"]
        
        
      letting_width, lettering_height = draw.textsize(txt, font=font)
      increase = True
      while increase:
        if lettering_height < (image_size[1] * (valign[1]+rel_adjust)):
          font_size += 1
          top += top_adjust
          font = self.registerFontInstance(font_name, font_size)
          letting_width, lettering_height = draw.textsize(txt, font=font)
        else:
          increase = False
    
    

    try:
      font = self.fonts[font_name]["fontInstance"].get(font_size,None)
    except:
      font = self.registerFontInstance(font_name, font_size)
    if not font:
      font = self.registerFontInstance(font_name, font_size, encoding=encoding)
    
      
    if align == "centre":
      left = (self.centre_text(draw, txt, font, max_width))
    elif align == "right":
      left = (self.align_text(draw, txt, font, max_width, 'right'))
      
    if getXY_only:
      wX, wY = draw.textsize(txt, font=font)
      return wX, wY
    
    if not self.abort:
      try:
        if "(" in font_colour:
          font_colour = eval(font_colour)
        draw.text((left,int(top)), txt, font=font, fill=font_colour)
      except:
        print "Text %s could not be drawn" %txt
    else:
      pass    
    
  def addTransparancy(self, im, target_colour = (255,255,255)):
    mask = im.point(lambda i : i == 0 and 0) # create RGB mask
    mask = mask.convert('L') # mask to grayscale
    mask = mask.point(lambda i : i == 0 and 0) # mask to B&W grayscale
    mask = ImageChops.invert(mask)
    # merge mask with image
    R, G, B = im.split()
    n_img = Image.merge('RGBA', (R, G, B, mask))
    return n_img
  
  def removeTransparancy(self,im, target_colour = (255,255,255)):
    # Remove transparency
    white = Image.new("RGB",im.size,target_colour) # Create new white image
    r,g,b,a = im.split()
    im = Image.composite(im,white, a) # Create a composite
    return im

  def getTxtWidthAndHeight(self, txt, font_name='Vera', font_size=12):
    global sizedraw_dummy_draw
    font = self.fonts[font_name]["fontInstance"].get(font_size,None)
    if not font:
      font = self.registerFontInstance(font_name, font_size)
    wX, wY = sizedraw_dummy_draw.textsize(txt, font=font)
    return wX, wY
  
  def make_pop_image(self, d):
    size = d.get('size')
    bgcolour = d.get('bgcolour')
    txt_l = d.get('txt')
    name = d.get('name')
    im = Image.new("RGB",size,bgcolour)
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
      font_name = "%s %s" %(self.gui_timage_font_name, font_weight)
      font_name = font_name.strip()
      after = t.get('after')
      
      font = self.fonts[font_name]["fontInstance"].get(font_size,None)
      if not font:
        font = self.registerFontInstance(font_name, font_size)
      wX, wY = draw.textsize(txt, font=font)
      
      self.write_text_to_draw(
        draw, 
        txt, 
        top_left=(curr_pos_x,curr_pos_y), 
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

  def draw_advertise_new(self,draw,image):
    max_width = image.size[0]
    max_height = image.size[1]
    font_name = "%s Bold" %self.gui_timage_font_name
    font_size = int(max_height)
    colour = self.gui_html_highlight_colour
    txt="New!"
    dX, dY = self.getTxtWidthAndHeight(txt, font_name, font_size)
    
    draw.rectangle((max_width - dX - 2, 2, max_width - 2, max_height - 2), fill='#ffee00')
    
    self.write_text_to_draw(
      draw,
      txt = txt,
      top_left=(60, -1),
      align='right',
      max_width=max_width,
      font_name=font_name, 
      font_size=font_size, 
      titleCase=True,
      font_colour=colour,)
    
    font_size = 8
    txt = "New!"
    dX, dY = self.getTxtWidthAndHeight(txt, font_name, font_size)
    IM = Image.new('RGBA', (dX, dY))
    IMdraw = ImageDraw.Draw(IM)
    IMdraw.rectangle((0, 0, dX + 2, dY), fill='#ffee00')
    self.write_text_to_draw(
      IMdraw,
      txt = txt,
      top_left=(0, -1),
      max_width=max_width,
      font_name=font_name, 
      font_size=font_size, 
      titleCase=True,
      font_colour=colour,)
    OlexVFS.save_image_to_olex(IM, "new", 2)


  def create_arrows(self, draw, height, direction, colour, type='simple', h_space=4, v_space=4, offset_y = 0, char_pos=(0,0), char_char="+"):
    arrow_height = height - (2*v_space)
    arrow_width = arrow_height 
    if arrow_width%2 != 0:
      arrow_width -= 1
      arrow_height -= 1
    arrow_half = arrow_width/2
    if type == 'simple':
      if direction == 'up':
        h_space -= 2
        v_space += 2
        begin = (h_space, height-v_space + 1)
        middle = (h_space + arrow_half, v_space - 1)
        end = (h_space + arrow_width, height-v_space + 1)
      elif direction == 'down':
        h_space -= 1
        v_space += 1
        begin = (h_space, v_space)
        middle = (h_space + arrow_half, height - v_space)
        end = (h_space + arrow_width, v_space)
      elif direction == "right":
        h_space += 1
        begin = (h_space,v_space)
        middle = (arrow_width+1,height/2)
        end = (h_space, height-v_space)
      elif direction == "right_":
        begin = (3,3)
        middle = (9,height/2)
        end = (3, height-3)
      draw.polygon((begin, middle, end), colour)
    elif type == "composite":
      if direction == "up":
        begin = (8, 5) 
        middle = (4, height-5)
        end = (8, height-7)
        draw.polygon((begin, middle, end), self.adjust_colour(colour, luminosity = 0.8))
        middle = (12, height-5)
        draw.polygon((begin, middle, end), self.adjust_colour(colour, luminosity = 0.6))
      if direction == "down":
        begin = (8, height-5)
        middle = (4, 5)
        end = (8, 7)
        draw.polygon((begin, middle, end), fill=self.adjust_colour(colour, luminosity = 0.8))
        middle = (12, 5)
        draw.polygon((begin, middle, end), fill=self.adjust_colour(colour, luminosity = 0.6))
    elif type == "char":
      if direction == 'up':
        font_size = 13
      else:
        font_size = 13
      
      font_name = "%s Bold" %self.gui_timage_font_name
      self.write_text_to_draw(
        draw, 
        char_char, 
        top_left=char_pos, 
        font_name=font_name, 
        font_size=font_size, 
        titleCase=True,
        font_colour=colour,)
    elif type == "circle":
      xy = (4,4,8,8)
      draw.ellipse(xy, fill = colour)

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
    hrad = int(rad/2-1)
    hrad_TL = 0
    hrad_TR = 0
    hrad_BL = 0
    hrad_BR = 0
  
    #border_colour = bg_colour
    border_colour = self.adjust_colour(border_colour, hue=border_hls[0], luminosity=border_hls[1], saturation=border_hls[2])
    #border top
    begin = (0, 0)
    end = (width, 0)
  #       draw.line((begin ,end), fill=border_colour['top'])
    draw.line((begin ,end), fill=border_colour)
  
    #border bottom
    begin = (0, height-1)
    end = (width-1, height-1)
  #       draw.line((begin ,end), fill=border_colour['bottom'])
    draw.line((begin ,end), fill=border_colour)
  
    #border left
    begin = (0, 0)
    end = (0, height-1)
  #       draw.line((begin ,end), fill=border_colour['left'])
    draw.line((begin ,end), fill=border_colour)
  
    #border right
    begin = (width-1 ,0)
    end = (width-1, 0)
  #       draw.line((begin ,end), fill=border_colour['right'])
    draw.line((begin ,end), fill=border_colour)
  
    rect_colour = OV.FindValue('gui_html_bg_colour')
    pie_colour = bg_colour
    
    pie_colour = (0,0,0,255)
    rect_colour = (0,0,0,255)
    #top-left corner
    if cTopLeft:
      draw.rectangle((0, 0, hrad, hrad), fill=rect_colour)
      draw.pieslice((0, 0, rad, rad), 180, 270, fill=pie_colour)
      draw.arc((0, 0, rad, rad), 180, 270, fill=border_colour)
      hrad_TL = hrad
    #bottom-right corner
    if cBottomRight:
      draw.rectangle((width-hrad, height-hrad, width, height),  fill=rect_colour)
      draw.pieslice((width-rad-shift, height-rad-shift, width-shift, height-shift), 0, 90, fill=pie_colour)
      draw.arc((width-rad-shift, height-rad-shift, width-shift, height-shift), 0, 90, fill=border_colour)
      hrad_BR = hrad
    #bottom-left corner
    if cBottomLeft:
      draw.rectangle((0, height-hrad, hrad, height), fill=rect_colour)
      draw.pieslice((0, height-rad-shift, rad, height-shift), 90, 180, fill=pie_colour)
      draw.arc((0, height-rad-shift, rad, height-shift), 90, 180, fill=border_colour)
      hrad_BL = hrad
    #top-right corner
    if cTopRight:
#      draw.rectangle((width-hrad, 0, width, hrad), fill=rect_colour)
#      draw.pieslice((width-rad-shift, 0, width-shift, rad), 270, 360, fill=pie_colour)
      draw.arc((width-rad-shift, 0, width-shift, rad), 270, 360, fill=border_colour)
      hrad_TR = hrad
  
    #border top
    begin = (hrad_TL, 0)
    end = (width-hrad_TR, 0)
    draw.line((begin ,end), fill=border_colour)
  
    #border bottom
    begin = (hrad_BL-1, height-1)
    end = (width-hrad_BR-1, height-1)
    draw.line((begin ,end), fill=border_colour)
  
    #border left
    begin = (0, hrad_TL)
    end = (0, height-hrad_BL-1)
    draw.line((begin ,end), fill=border_colour)
  
    #border right
    begin = (width-1 ,hrad_TR)
    end = (width-1, height-hrad_TL)
    draw.line((begin ,end), fill=border_colour)


a = ImageTools()
OV.registerMacro(a.resize_to_panelwidth, 'i-Image&;c-Colourize')
