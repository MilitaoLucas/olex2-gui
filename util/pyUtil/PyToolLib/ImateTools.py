from __future__ import division
import PngImagePlugin
import Image
import ImageFont, ImageDraw, ImageChops, ImageColor
import OlexVFS
import RoundedCorners


class ImageTools(ArgumentParser):
  def __init__(self):
    super(ImageTools, self).__init__()
    import colorsys
    self.colorsys = colorsys
    self.abort = False
    self.getOlexVariables()

  def getOlexVariables(self):
    self.encoding = test_encoding(olx.CurrentLanguageEncoding()) ##Language
    self.language = "English" ##Language
    if olx.IsCurrentLanguage('Chinese') == "true":
      self.language = 'Chinese'
    self.fonts = self.defineFonts()

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

  def defineFonts(self):
    fonts = {
      "Verdana":"verdana.ttf",
      "Verdana Bold":"verdanab.ttf",
      "Arial":"arial.ttf",
      "Arial UTF":"arialuni.ttf",
      "Arial Bold":"arialbd.ttf",
      "Trebuchet Bold":"trebucbd.ttf",
      "Trebuchet":"trebuc.ttf",
      "Garamond Bold":"garabd.ttf",
      "Times Bold Italic":"timesbi.ttf",
    }
    return fonts

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


  def add_vline(self, draw, height, h_pos, weight=1, colour=(237,237,235)):
    begin = (h_pos, 4)
    end = (h_pos, height - 8)
    draw.line((begin ,end), fill=self.adjust_colour(colour, luminosity = 0.8))
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
      canvas.paste(whitespace, (width, margin_top))
      canvas.paste(image, (weight, 0))
    return canvas

  def add_continue_triangles(self, draw, width, height, shift_up = 4):
    arrow_top = 8 + shift_up
    arrow_middle = 5 + shift_up
    arrow_bottom = 2 + shift_up
    beg_1 = 20
    mid_1 = 16
    beg_2 = 13
    mid_2 = 9
    beg_3 = 7
    mid_3 = 3

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

  def adjust_colour(self, colour, hue=0, luminosity=1, saturation=1):
    if colour == 'base':
      colour = self.gui_timage_colour
    if colour == "bg":
      colour = self.gui_bgcolor
    if colour == "highlight":
      colour = self.gui_highlight_colour
    if colour == "gui_table_bgcolor":
      colour = self.gui_table_bgcolor
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
    for i in xrange(int(height-height*(1-fraction))):
      if i < height/inc:
        incrementA = int(step*0.6*i*(58/height))
        incrementB = int(step*0.6*i*(44/height))
      elif height/inc < i < (height/inc)*2:
        incrementA = int(step*1.2*i*(58/height))
        incrementB = int(step*1.2*i*(44/height))
      else:
        incrementA = int(step*1.4*i*(58/height))
        incrementB = int(step*1.4*i*(44/height))

      begin = (0,i)
      end = (width, i)
      R = int(colour[0]-incrementA)
      G = int(colour[1]-incrementA)
      B = int(colour[2]-incrementB)
      #print i, R,G,B
      draw.line((begin ,end), fill=(R, G, B))


  def write_text_to_draw(self, draw, txt, top_left=(1,0), font_name='Verdana', font_size=11, font_colour="#000000", align="left", max_width=0):
    #txt = olx.TranslatePhrase(str.strip(txt))
    txt = OV.Translate("%%%s%%" %str.strip(txt)) ##Language

    if self.language == 'Chinese':
      font_name = 'Arial UTF'
      font_size=13
      top_left=(top_left[0], top_left[1] -1)
    font_file = self.fonts[font_name]
    font = ImageFont.truetype("%s" %font_file, font_size, encoding=test_encoding("unic")) ##Leave in for Debug!
    try:
      font_file = self.fonts.get(font_name, "aarialuni.ttf")
      font = ImageFont.truetype("%s" %font_file, font_size, encoding=test_encoding("unic"))

    except:
      print "The font %s is required for this option." %font_name
      self.abort = True

    if align == "centre":
      top_left = (centre_text(draw, txt, font, max_width), top_left[1])
    if align == "right":
      top_left = (align_text(draw, txt, font, max_width, 'right'), top_left[1])

    if not self.abort:
      try:
        draw.text(top_left, "%s" %txt.decode(self.encoding), font=font, fill=font_colour)
      except:
        draw.text(top_left, "%s" %txt.decode("ISO8859-1"), font=font, fill=font_colour)
    else:
      pass

  def removeTransparancy(self,im, target_colour = (255,255,255)):
    # Remove transparency
    white = Image.new("RGB",im.size,target_colour) # Create new white image
    r,g,b,a = im.split()
    im = Image.composite(im,white, a) # Create a composite
    return im



  def create_arrows(self, draw, height, direction, colour, type='simple', h_space=4, v_space=4):
    arrow_height = height - (2*v_space)
    arrow_width = arrow_height
    if arrow_width%2 != 0:
      arrow_width -= 1
      arrow_height -= 1
    arrow_half = arrow_width/2
    if type == 'simple':
      if direction == 'up':
        h_space -= 1
        v_space += 2
        begin = (h_space, height-v_space)
        middle = (h_space + arrow_half, v_space -1 )
        end = (h_space + arrow_width, height - v_space )
      elif direction == 'down':
        h_space -= 1
        v_space += 1
        begin = (h_space, v_space)
        middle = (h_space + arrow_half, height - v_space)
        end = (h_space + arrow_width, v_space)
      elif direction == "right":
        h_space += 1
        begin = (h_space,v_space)
        middle = (arrow_width,height/2)
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

    rect_colour = OV.FindValue('gui_bgcolor')
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
