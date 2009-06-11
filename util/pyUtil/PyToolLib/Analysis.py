#from __future__ import division
# -*- coding: latin-1 -*-

import math
from itertools import izip
import ExternalPrgParameters
import OlexVFS
import Image
import ImageFont, ImageDraw, ImageChops
from ImageTools import ImageTools
import ImageFilter
try:
  import olx
  import olex
  import olexex
  import htmlTools
except:
  pass

from olexFunctions import OlexFunctions
OV = OlexFunctions()

from scitbx.math import erf

class Graph(ImageTools):
  def __init__(self):
    ImageTools.__init__(self)
    self.dataset_counter = 0
    self.function_counter = 0
    self.auto_axes = True
    self.reverse_x = False
    self.reverse_y = False
    self.draw_origin = False
    self.data = {}
    self.metadata = {}
    self.draw = ""
    self.map_txt_list = []
    
    self.graphInfo = {
      "imSize":(900, 500),
      "TopRightTitle":self.filename,
      "FontScale":0.02,
      "marker":{
        'colour':(254,150,50),
        'border_colour':(254/2,150/2,50/2),
        },
      "plot_function":{
        'colour1':(0,0,0),
        'colour2':(0,0,255),
        'colour3':(255,0,0),
        },
    }
  
  def plot_function(self, function, n_points=50):
    self.get_division_spacings_and_scale()
    spacing = self.delta_x/n_points
    x_values = []
    y_values = []
    x = self.min_x
    for i in xrange(0,n_points+1):
      x_values.append(x)
      y_values.append(function(x))
      x += spacing
      
    data = Dataset(x_values,y_values,metadata=None)
    
    min_x = self.min_x
    max_x = self.max_x
    scale_x = self.scale_x
    delta_x = self.delta_x
    max_y = self.max_y
    min_y = self.min_y
    scale_y = self.scale_y
    delta_y = self.delta_y
    xy_pairs = data.xy_pairs()
    self.function_counter += 1
    fill = self.graphInfo['plot_function']['colour%s' %self.function_counter]
    
    pixel_coordinates = []
    
    for x_value,y_value in xy_pairs:
      
      if self.reverse_x:
        x = self.bX \
          - (self.boxXoffset
             + ((float(x_value) * self.scale_x)) 
             + ((0 - max_x) * self.scale_x) 
             + (delta_x * self.scale_x))
      else:
        x = (self.graph_left
             + ((float(x_value) * self.scale_x))
             + ((0 - max_x) * self.scale_x)
             + (delta_x * self.scale_x))
      if self.reverse_y:
        y = (self.graph_top
             + ((float(y_value) * scale_y)) 
             + ((0 - max_y) * scale_y) 
             + (delta_y * scale_y))
      else:
        y = self.bY \
          - (self.boxYoffset 
             + ((float(y_value) * scale_y)) 
             + ((0 - max_y) * scale_y) 
             + (delta_y * scale_y))
        
      pixel_coordinates.append((round(x),round(y)))
      
    for i in range(0,n_points):
      first_point = pixel_coordinates[i]
      second_point = pixel_coordinates[i+1]
      if (second_point[1] < (self.graph_bottom) 
          and second_point[1] >= self.boxYoffset
          and second_point[0] <= self.graph_right
          and second_point[0] >= self.graph_left): 
        line = (first_point,second_point)
        self.draw.line(line,fill=fill,)
    #self.draw_help_lines()
        
  def draw_help_lines(self):
    "Draws guide lines on the image to show box offset, etc."
    
    x = self.boxXoffset
    self.draw.line(((x, -500),(x, 1500)), width=self.line_width, fill=(255, 200, 200))
    txt = "self.boxXoffset"
    self.draw.text((x+5, 30), "%s" %txt, font=self.font_tiny, fill=(100, 255, 100))
    
    x = self.boxX
    self.draw.line(((x, -500),(x, 1500)), width=self.line_width, fill=(255, 200, 200))
    txt = "self.boxX"
    self.draw.text((x-60, 30), "%s" %txt, font=self.font_tiny, fill=(100, 255, 100))
    
    x = self.graph_right
    self.draw.line(((x, -500),(x, 1500)), width=self.line_width, fill=(255, 200, 200))
    txt = "self.graph_right"
    self.draw.text((x-60, 30), "%s" %txt, font=self.font_tiny, fill=(100, 255, 100))
    
    y = self.boxYoffset
    self.draw.line(((-500, y),(1500, y)), width=self.line_width, fill=(255, 200, 200))
    txt = "self.boxYoffset"
    self.draw.text((100, y + 5), "%s" %txt, font=self.font_tiny, fill=(255, 100, 100))
    
    y = self.boxYoffset + self.boxY
    self.draw.line(((-500, y),(1500, y)), width=self.line_width, fill=(255, 200, 200))
    txt = "self.boxYoffset + self.boxY"
    self.draw.text((150, y + 5), "%s" %txt, font=self.font_tiny, fill=(255, 100, 100))
    
    y = self.graph_bottom
    self.draw.line(((-500, y),(1500, y)), width=self.line_width, fill=(255, 200, 200))
    txt = "self.graph_bottom"
    self.draw.text((200, y + 5), "%s" %txt, font=self.font_tiny, fill=(255, 100, 100))
    
    y = self.graph_top
    self.draw.line(((-500, y),(1500, y)), width=self.line_width, fill=(255, 200, 200))
    txt = "self.graph_top"
    self.draw.text((250, y + 5), "%s" %txt, font=self.font_tiny, fill=(255, 100, 100))
    
  def draw_key(self,dictionary):
    max_length = 0
    for item in dictionary.values():
      label = item['label']
      if len(label) > max_length:
        max_length = len(label)
    boxWidth = 60 + 8 * max_length
    boxHeight = 30 * len(dictionary.keys())
    #boxTopOffset = self.imY * 0.035
    colour = self.gui_html_bg_colour
    im = Image.new('RGB', (boxWidth,boxHeight), colour)
    draw = ImageDraw.Draw(im)
    box = (2,2,boxWidth-2,boxHeight-2)
    draw.rectangle(box, fill=self.gui_html_bg_colour, outline=(200, 200, 200))
    margin_left = int((boxWidth/4))
    margin_right = int((boxWidth/4)*3)
    
    txt_colour = "#444444"
    top = 10
    for item in dictionary.values():
      label = item['label']
      colour = item['colour']
      left = 15
      wX, wY = draw.textsize(label, font=self.font_tiny)
      draw.line((left,top+wY/2,left+30,top+wY/2),fill=colour,width=2)
      left = 60
      draw.text((left,top), "%s" %label, font=self.font_tiny, fill=txt_colour)
      top += wY + 10
      
    return im
  
  def get_unicode_characters(self, txt):
    txt = txt.replace("lambda", unichr(61548))
    txt = txt.replace("theta", unichr(61553))
    txt = txt.replace("sigma", unichr(61555))
    txt = txt.replace("^2", unichr(178))
    txt = txt.replace("^3", unichr(179))
    txt = txt.replace(">", unichr(61681))
    txt = txt.replace("<", unichr(61665))
    txt = txt.replace("Fo2", "Fo%s" %(unichr(178)))
    #txt = txt.replace("Fexp2", "Fexp%s" %(unichr(178)))
    #txt = txt.replace("Fo2", "F%s%s" %(unichr(2092),unichr(178)))
    txt = txt.replace("Fexp", "F%s" %(unichr(2091)))
    return txt
    
  def make_x_y_plot(self):
    pass
    #im = self.make_empty_graph()

  def make_empty_graph(self, axis_x=False):
    import Image
    import ImageFont, ImageDraw, ImageChops
    
    #import PngImagePlugin
    self.imX = self.graphInfo["imSize"][0]
    self.imY = self.graphInfo["imSize"][1]
    
    fontsize = int(0.08 * self.imX)
    fontscale = 0.02 * self.imX
    f = self.graphInfo.get("FontScale", 0.02)
    fontscale = f * self.imX
    
    font_name = "Vera"
    self.font_large = self.registerFontInstance(font_name, int(1.4 * fontscale))
    self.font_normal = self.registerFontInstance(font_name, int(1.0 * fontscale))
    self.font_small = self.registerFontInstance(font_name, int(0.9 *fontscale))
    self.font_tiny = self.registerFontInstance(font_name, int(0.7 * fontscale))
    font_name = "Vera Bold"
    self.font_bold_large = self.registerFontInstance(font_name, int(1.4 * fontscale))
    self.font_bold_normal = self.registerFontInstance(font_name, int(1.0 * fontscale))
    
    self.filenameColour = "#bbbbbb"
    self.titleColour = "#777777"
    self.bSides = round(0.015 * self.imX)
    self.xSpace = 0
    self.axis_x = axis_x
    if self.axis_x:
      self.xSpace  = 0.04 * self.imX
    self.bTop = round(0.013 * self.imY)
    self.currX = 0
    self.currY = 0
    size = ((int(self.imX), int(self.imY)))
    colour = self.gui_html_bg_colour
    #colour = "#000000"
    im = Image.new('RGB', size, colour)
    draw = ImageDraw.Draw(im)
    self.draw = draw
    
    txt = self.graphInfo["Title"]
    #txt = self.metadata.get("Title",self.graphInfo["Title"]).title()
    
    if not txt: txt = "Not available"
    x = 0 + self.bSides+self.xSpace
    y = self.bTop
    
    self.draw.text((x, y), "%s" %txt, font=self.font_large, fill=self.titleColour)
    currX, currY = self.draw.textsize(txt, font=self.font_bold_large)
    
    # Write something in the right-hand top spot on the graph
    txt = self.graphInfo.get("TopRightTitle", "")
    font = self.font_bold_large
    txtX, txtY = self.draw.textsize(txt, font=font)
    x = (self.imX - self.bSides - txtX) # align text right
    y = self.bTop
    draw.text((x, y), "%s" %txt, font=font, fill=self.filenameColour)
    currX, currY = draw.textsize(txt, font=self.font_bold_large)
    self.currX += currX
    self.currY += currY
    
    self.yAxisSpace = 5
    self.graphX = self.imX - (self.bSides + self.xSpace)
    self.graph_top = int(self.currY + 0.1 * self.imY) + self.yAxisSpace
    self.graphY = self.imY - 2*self.bTop - self.graph_top
    self.graph_bottom = int(self.graphY + currY + 0.03*self.imY - self.yAxisSpace)
    self.line_width = int(self.imX * 0.002)
    
    dx = self.imX - 1*self.bSides
    dy = self.graph_bottom
    box = (self.bSides + self.xSpace, currY + 0.03*self.imY, dx, dy)
    if self.line_width > 0:
      fill = (200, 200, 200)
    else:
      fill = self.gui_html_bg_colour
    draw.rectangle(box,  fill=fill, outline=(200, 200, 200))
    self.boxX = dx - self.bSides*2 + self.xSpace
    self.boxY = dy - currY
    self.boxXoffset = self.bSides+self.xSpace
    self.graph_right = self.imX - self.bSides
    self.graph_left = self.boxXoffset
    self.boxYoffset = currY + 0.03*self.imY
    self.graph_top = self.boxYoffset
    if self.line_width > 0:
      box = (box[0] + self.line_width, box[1] + self.line_width, box[2] - self.line_width, box[3] -self.line_width)
      draw.rectangle(box, fill=self.gui_html_bg_colour, outline=(200, 200, 200))
    self.im = im
    self.draw = draw
    
  def draw_yAxis(self):
    yAxis = []
    for item in self.graphInfo["y_axis"]:
      try:
        f = float(item)
        if f < 1:
          yAxis.append(  "%.2f" %(float(item)))
        elif f > 1:
          yAxis.append(  "%.1f" %(float(item)))
      except:
        pass
      
    if not yAxis:
      for item in self.graphInfo["y_axis"]:
        yAxis.append(item)
        
    barX = self.graphX/len(yAxis)
    
    i = 0
    for item in yAxis:
      txt = item
      wX, wY = self.draw.textsize(txt, font=self.font_small)
      x = int(self.bSides + i * barX + (barX - wX)/2)
      y = self.graph_bottom 
      self.draw.text((x, y), "%s" %txt, font=self.font_small, fill="#444444")
      i += 1
      
  def draw_fit_line(self, slope, y_intercept):
    y1 = (slope * self.min_x + y_intercept)
    y2 = (slope * self.max_x + y_intercept)
    
    if y1 > self.max_y:
      y1 = self.max_y
    elif y1 < self.min_y:
      y1 = self.min_y
      
    x1 = (y1-y_intercept)/slope
    x1 = self.graph_left \
       + ((float(x1) * self.scale_x)) \
       + ((0 - self.max_x) * self.scale_x) \
       + (self.delta_x * self.scale_x)
        
    if y2 > self.max_y:
      y2 = self.max_y
    elif y2 < self.min_y:
      y2 = self.min_y
      
    x2 = (y2-y_intercept)/slope    
    x2 = self.graph_left \
       + ((float(x2) * self.scale_x)) \
       + ((0 - self.max_x) * self.scale_x) \
       + (self.delta_x * self.scale_x)
    
    if self.reverse_y:
      y1 = (self.graph_top 
            + (float(y1) * self.scale_y)
            + (0 - self.max_y) * self.scale_y 
            + (self.delta_y * self.scale_y))
      y2 = (self.graph_top 
            + (float(y2) * self.scale_y) 
            + (0 - self.max_y) * self.scale_y 
            + (self.delta_y * self.scale_y))
    else:
      y1 = self.bY \
         - (self.boxYoffset 
            + ((float(y1) * self.scale_y)) 
            + ((0 - self.max_y) * self.scale_y) 
            + (self.delta_y * self.scale_y))
      y2 = self.bY \
         - (self.boxYoffset 
            + ((float(y2) * self.scale_y)) 
            + ((0 - self.max_y) * self.scale_y) 
            + (self.delta_y * self.scale_y))
      
    self.draw.line((x1+2, y1, x2-2, y2), width=5, fill="#eeeeee")
    
    two_thirds = (self.min_x + (self.max_x - self.min_x) * 0.66)
    if y_intercept >= 0: sign = '+'
    else: sign = '-'
    txt = "y = %.3fx %s %.3f" %(slope,sign,abs(y_intercept))
    wX, wY = self.draw.textsize(txt, font=self.font_small)
    y = (slope * two_thirds + y_intercept) *self.scale_y 
    x = self.bSides + self.boxXoffset + ((two_thirds * self.scale_x)) + ((0 - self.max_x) * self.scale_x) + (self.delta_x * self.scale_x)
#    x = self.graph_left + abs(two_thirds * self.scale_x)
    self.draw.text((x, y+wY), "%s" %txt, font=self.font_small, fill="#444444")
    
  def draw_pairs(self, reverse_y=False, reverse_x=False): 
    self.reverse_y = reverse_y
    self.reverse_x = reverse_x
    self.n_divisions = 5
    self.ax_marker_length = int(self.imX * 0.006)
    
    self.marker_width = int(self.graphInfo["marker"].get('size', int(self.im.size[0]/80)))
    
    self.get_division_spacings_and_scale()
    self.draw_x_axis()
    self.draw_y_axis()
    self.map_txt_list = [ "<map name='map_analysis'>" ]
    for dataset in self.data.values():
      if dataset.metadata().get("fit_slope") and dataset.metadata().get("fit_slope"):
        slope = float(dataset.metadata().get("fit_slope"))
        y_intercept = float(dataset.metadata().get("fit_y_intercept"))
        self.draw_fit_line(slope, y_intercept)
      self.draw_data_points(dataset.xy_pairs())
      
    self.map_txt_list.append("</map>")
    
  def map_txt(self):
    return '\n'.join(self.map_txt_list)
  map_txt = property(map_txt)
    
  def get_division_spacings_and_scale(self):  
    min_xs = []
    min_ys = []
    max_xs = []
    max_ys = []
    
    assert len(self.data) > 0
    for dataset in self.data.values():
      if self.auto_axes:
        min_xs.append(min(dataset.x))
        min_ys.append(min(dataset.y))
      max_xs.append(max(dataset.x))
      max_ys.append(max(dataset.y))
      
    if self.auto_axes:
      min_x = min(min_xs)
      min_y = min(min_ys)
    else:
      min_x = 0.0
      min_y = 0.0
    max_x = max(max_xs)
    max_y = max(max_ys)
    
    self.max_x = max_x
    self.min_x = min_x
    self.max_y = max_y
    self.min_y = min_y
    
    delta_x = max_x - min_x
    delta_y = max_y - min_y
    self.delta_x = delta_x
    self.delta_y = delta_y
    self.scale_x = ((self.graph_right - self.graph_left)/delta_x)
    self.scale_y = ((self.graph_bottom - self.graph_top)/delta_y)
    
    self.bY = (self.graph_bottom + self.graph_top)
    self.bX = (self.graph_left + self.graph_right)
    
  def get_divisions(self, delta):
    assert delta != 0
    dv = delta/self.n_divisions
    
    precision = -(int(math.log10(dv))) + 1
    dv_ = round(dv * math.pow(10,precision))
    if dv_ < 2:
      dv_ = 1.0
    elif dv_ < 2.5:
      dv_ = 2.0
    elif dv_ < 4:
      dv_ = 2.5
    elif dv_ < 5:
      dv_ = 4.0
    elif dv_ < 10:
      dv_ = 5.0
    else:
      dv_ = round(dv_, -1)
    return dv_/math.pow(10,precision)
  
  def draw_data_points(self, xy_pairs):
    min_x = self.min_x
    max_x = self.max_x
    scale_x = self.scale_x
    delta_x = self.delta_x
    max_y = self.max_y
    min_y = self.min_y
    scale_y = self.scale_y
    delta_y = self.delta_y
    
    fill = self.graphInfo['marker']['colour']
    outline = self.graphInfo['marker']['border_colour']
    marker_width = self.marker_width
    
    if self.reverse_x:
      x_constant = self.bX \
                 - (marker_width/2 + self.boxXoffset
                    + ((0 - max_x) * self.scale_x) 
                    + (delta_x * self.scale_x))
      scale_x = -self.scale_x
    else:
      x_constant = (self.graph_left - marker_width/2
                    + ((0 - max_x) * self.scale_x)
                    + (delta_x * self.scale_x))
      scale_x = self.scale_x
      
    if self.reverse_y:
      y_constant = (self.graph_top - marker_width/2
                    + ((0 - max_y) * scale_y)
                    + (delta_y * scale_y))
      scale_y = self.scale_y
    else:
      y_constant = self.bY \
          - (marker_width/2 + self.boxYoffset 
             + ((0 - max_y) * scale_y) 
             + (delta_y * scale_y))
      scale_y = -self.scale_y
      
    map_txt_list = self.map_txt_list
    for xr, yr in xy_pairs:
      x = x_constant + xr * scale_x
      y = y_constant + yr * scale_y
      
      box = (x,y,x+marker_width,y+marker_width)
      self.draw.rectangle(box, fill=fill, outline=outline)
      
      if self.item == "AutoChem":
        map_txt_list.append("""<area shape="rect" coords="%i,%i,%i,%i" href="reap %s"  target="%s">"""
                            % (x, y, x+marker_width, y+marker_width, xr, yr))
      else:
        map_txt_list.append("""<area shape="rect" coords="%i,%i,%i,%i" href="Html.Update" target="(%.3f,%.3f)">"""
                            % (x, y, x+marker_width, y+marker_width, xr, yr))
        
      #if self.item == "AutoChem":
        #self.map_txt += '''
#<area shape="rect" coords="%s,%s,%s,%s" href="reap %s"  target="%s">
#''' %(int(x),int(y),int(x+marker_width),int(y+marker_width), item[-2:-1][0], item[-1:][0])
      #else:
        #self.map_txt += '''
#<area shape="rect" coords="%s,%s,%s,%s" href="Html.Update" target="(%.3f,%.3f)">
#''' %(int(x),int(y),int(x+marker_width),int(y+marker_width), item[0], item[1])
        
  def draw_y_axis(self):
    max_y = self.max_y
    min_y = self.min_y
    scale_y = self.scale_y
    delta_y = self.delta_y
    dv_y = self.get_divisions(delta_y)
    y_axis = []
    precision = len(str(dv_y).split('.')[-1])
    
    if min_y < 0 and max_y > 0: # axis are in range to be drawn
      div_val = 0.0
      while div_val > min_y:
        div_val -= dv_y
    else:
      div_val = round(min_y-dv_y, precision-1) # minimum value of div_val
    y_axis.append(div_val)
    while div_val < max_y:
      div_val = div_val + float(dv_y)
      y_axis.append(div_val)
      
    for item in y_axis:
      val = float(item)
      if dv_y < 0.01:
        txt = "%.3f" %item
      elif max_y < 10:
        txt = "%.2f" %item
      elif max_y <= 100:
        txt = "%.1f" %item
      elif max_y > 100:
        txt = "%.0f" %item
        
      wX, wY = self.draw.textsize(txt, font=self.font_small)
      x = self.imX * 0.01
      if self.reverse_y:
        y = (self.boxYoffset + wY/2 
             + ((val * scale_y)) 
             + ((0 - max_y) * scale_y) 
             + (delta_y * scale_y))
      else:
        y = self.bY \
          - (self.boxYoffset + wY/2 
             + ((val * scale_y)) 
             + ((0 - max_y) * scale_y) 
             + (delta_y * scale_y))
        
      y = round(y,1)
      if y < (self.graph_bottom) and y >= self.boxYoffset -wY/2: 
        self.draw.text((x, y), "%s" %txt, font=self.font_small, fill="#444444")
        x = x + int(self.imX * 0.045)
        y = y + int(wY/2)
        self.draw.line(((x, y),(x+self.ax_marker_length, y)), width=self.line_width, fill=(200, 200, 200))
        
    if self.draw_origin:
      line = (self.graph_left - self.min_x * self.scale_x, self.graph_bottom,
              self.graph_left - self.min_x * self.scale_x, self.graph_top)
      self.draw.line(line, fill=(200, 200, 200), width=self.line_width)
      
    txt = self.metadata.get("y_label", "y Axis Label")
    txt = self.get_unicode_characters(txt)
    wX, wY = self.draw.textsize(txt, font=self.font_small)
    size = (wX, wY)
    colour = self.gui_html_bg_colour
    new = Image.new('RGB', size, colour)
    draw = ImageDraw.Draw(new)
    x = 0
    y = 0
    draw.text((x, y), "%s" %txt, font=self.font_small, fill="#444444")
    new = new.rotate(90)
    self.im.paste(new, (int(self.xSpace+self.bSides + wY/2), int(self.bTop + wY + self.bSides *2)))
    
  def draw_x_axis(self):
    min_x = self.min_x
    max_x = self.max_x
    scale_x = self.scale_x
    delta_x = self.delta_x
    dv_x = self.get_divisions(delta_x)
    x_axis = []
    
    precision = len(str(dv_x).split('.')[-1])
    
    if min_x < 0 and max_x > 0: # axis are in range to be drawn
      div_val = 0.0
      while div_val > min_x:
        div_val -= dv_x
    else:
      div_val = round(min_x-dv_x, precision-1) # minimum value of div_val
    x_axis.append(div_val)
    while div_val < max_x:
      div_val = div_val + float(dv_x)
      x_axis.append(div_val)
      
    for item in x_axis:
      val = float(item)
      if dv_x < 0.01:
        txt = "%.3f" %item
      elif max_x < 10:
        txt = "%.2f" %item
      elif max_x < 100:
        txt = "%.1f" %item
      elif max_x >= 10:
        txt = "%.0f" %item
        
      wX, wY = self.draw.textsize(txt, font=self.font_small)
      y = self.graph_bottom
      #if self.draw_origin:
        #y += (self.min_y * self.scale_y)
       
      if self.reverse_x:
        x = self.bX \
          -(self.boxXoffset + wX/2
            + ((val * scale_x) - self.marker_width/2)
            + ((0 - max_x) * scale_x)
            + (self.delta_x * scale_x))
      else:
        x = (self.boxXoffset - wX/2
             + ((val * scale_x) - self.marker_width/2)
             + ((0 - max_x) * scale_x)
             + (self.delta_x * scale_x))
        
      if (x+wX)  <= (self.graph_right) and x >= self.graph_left - wX/2:
        self.draw.text((x, y), "%s" %txt, font=self.font_small, fill="#444444")
        x = int(x + wX/2)
        y = y - self.imY * 0.005
        self.draw.line(((x, y),(x, y-self.ax_marker_length)), width=self.line_width, fill=(200, 200, 200))
        
    if self.draw_origin:
      line = (self.bSides + self.xSpace, self.graph_bottom + self.min_y * self.scale_y,
              self.imX - self.bSides, self.graph_bottom + self.min_y * self.scale_y)
      self.draw.line(line, fill=(200, 200, 200), width=self.line_width)
    
    txt = self.metadata.get("x_label", "x Axis Label")
    txt = self.get_unicode_characters(txt)
    wX, wY = self.draw.textsize(txt, font=self.font_small)
    x = self.boxX - wX - self.bSides - self.imX * 0.002
    y = self.boxY  + self.imY * 0.01
    #if self.draw_origin:
      #y += (self.min_y * self.scale_y)
    self.draw.text((x, y), "%s" %txt, font=self.font_small, fill="#444444")
    
  def draw_bars(self):
    import ImageFont
    data = []
    for item in self.graphInfo["Data"]:
      try:
        data.append(float(item))
      except:
        pass
    barX = self.graphX/len(data)
    barScale = self.graphY/max(data)
    
    i = 0
    for item in data:
      barHeight = (item * barScale)
      fill = (0, 0, 0)
      fill = self.gui_html_bg_colour
      for barcol in self.barcolour:
        if item > barcol[0]:
          fill = barcol[1]
          
      x = self.bSides + i * barX
      y = (self.graph_bottom - barHeight + self.yAxisSpace)
      dx = ((i + 1) * barX) + self.bSides
      box = (x, y, dx, self.graph_bottom)
      self.draw.rectangle(box, fill=fill, outline=(100, 100, 100))
      font_size = int(barX/2)
      if font_size > 11: font_size = 11
      font_name = "Verdana"
      font = self.registerFontInstance(font_name, font_size)
      if item >= 10:
        txt = "%.0f" %item
      else:
        txt = "%.1f" %item
      wX, wY = self.draw.textsize(txt, font=font)
      if barHeight > wY * 2:
        self.draw.text((x + (barX - wX)/2, y + self.graphY * 0.01), "%s" %txt, font=font, fill="#222222")
      i += 1

class Analysis(Graph):
  def __init__(self, function=None, param=None):
    Graph.__init__(self)
    self.basedir = OV.BaseDir()
    self.filefull = OV.FileFull()
    self.filepath = OV.FilePath()
    self.filename = OV.FileName()
    self.datadir = OV.DataDir()
    self.gui_html_bg_colour = OV.FindValue('gui_html_bg_colour')
    self.gui_html_highlight_colour = OV.FindValue('gui_html_highlight_colour')
    self.SPD, self.RPD = ExternalPrgParameters.defineExternalPrograms()
    self.debug = False
    self.function = function
    if param:
      self.param = param.split(';')
    #self.file = ""
    self.fl = []
    self.item = None
    
  def run_Analysis(self, f, args):
    self.basedir = OV.BaseDir()
    self.filefull = OV.FileFull()
    self.filepath = OV.FilePath()
    self.filename = OV.FileName()
    self.datadir = OV.DataDir()
    self.data = {}
    
    fun = f
    self.n_bins = abs(int(args.get('n_bins',0))) #Number of bins for Histograms
    self.method = args.get('method','olex')      #Method by which graphs are generated
    if fun == "AutoChem":
      self.item = "AutoChem"
      self.graphInfo["imSize"] = (512, 256)
      self.graphInfo["Title"] = "AutoChem Statistics"
      self.graphInfo["pop_html"] = "ac_stats"
      self.graphInfo["pop_name"] = "ac_stats"
      self.graphInfo["TopRightTitle"] = ""
      self.graphInfo["FontScale"] = 0.025
      self.graphInfo["marker"] = {
        'size':3,
        'colour':(254,150,50),
        'border_colour':(254/2,150/2,50/2)
      }
      self.make_analysis_image()

    elif fun == "lst":
      self.file_reader("%s/%s.lst" %(filepath, filename))
      self.analyse_lst()
      for item in self.graphInfo:
#     items = ["K", "DisagreeReflections", "UniqueData"]
#     for item in items:
        self.item = item
        self.make_analysis_image()
        
    else:
      raise Exception("Unknown command: expected 'lst'")

    
  def make_simple_x_y_pair_plot(self, imX=512, imY=256):
    self.imX = imX
    self.imY = imY
    self.make_empty_graph(axis_x = True)
    self.draw_pairs()
    
  def make_K_graph(self):
    self.barcolour = [(0, (60, 240, 0)), (1.1, (255, 240, 20)), (1.7, (255, 0, 0))]
    self.imY = 128
    self.imX = 256
    self.draw_bars()
    self.draw_yAxis()
    
  def make_UniqeData_graph(self):
    self.barcolour = [(0, (60, 240, 0)), (1.1, (255, 240, 20)), (1.7, (255, 0, 0))]
    self.imY = 128
    self.imX = 256
    self.draw_bars()
    self.draw_yAxis()
    
  def make_DisagreeReflections_graph(self):
    total = (self.graphInfo["Data"][0] + self.graphInfo["Data"][1])
    t = total * 0.85
    self.barcolour = [(0, (60, 240, 0)), (total * 0.6, (255, 240, 20)),  (total * 0.9, (255, 0, 0))]
    self.imX = 128
    self.imY = 256
    self.draw_bars()
    self.draw_yAxis()

  def file_reader(self, filepath):
    fl = []
    try:
      rfile = open(filepath, 'r')
      for li in rfile:
        fl.append(li)
    except:
      pass
    return fl

  def get_simple_x_y_pair_data_from_file(self, filepath):
    file_data = self.file_reader(filepath)
    x = []
    y = []
    metadata = {}
    for li in file_data:
      li = li.strip()
      if li.startswith("#"):
        var = li.split("=")[0].strip("#")
        var = var.strip()
        val = li.split("=")[1].strip()
        metadata.setdefault(var, val)
      else:
        xy = li.split(",")
        try:
          data_name = xy[-1:][0]
        except:
          data_name = 'n/a'
        try:
          data_path = xy[-3:][-2]
        except:
          data_path = 'n/a'
        #data.append((float(xy[0]), float(xy[1]), data_path, data_name))
        x.append(float(xy[0]))
        y.append(float(xy[1]))
        
    self.data.setdefault('dataset1',Dataset(x,y,metadata))
    self.metadata = metadata

  def popout(self):
    assert self.item is not None
    image_location = "%s.png" %(self.item)
    OlexVFS.save_image_to_olex(self.im, image_location, 1)
    width, height = self.im.size
    pop_html = self.graphInfo.get("pop_html", None)
    pop_name = self.graphInfo.get("pop_name", None)
    if not pop_html or not pop_name:
      return
    
    str = '''
<html>
<body>
%s
<zimg border="0" src="%s.png" usemap=#map_analysis>
</body>
</html>
''' %(self.map_txt, self.item)
    htm_location = "%s.htm" %pop_html
    OlexVFS.write_to_olex(htm_location, str)
    extraX = 29
    extraY = 48
    pstr = "popup %s '%s' -b=stcr -t='%s' -w=%s -h=%s -x=1 -y=50" %(
      pop_name, htm_location, pop_name, width +extraX, height + extraY)
    olex.m(pstr)
    olx.html_SetBorders(pop_name,0)
    olx.html_Reload(pop_name)

  def analyse_lst(self):
    fl = self.fl
    i = 0
    AnalysisInfo = {}
    if not fl:
      return
    for li in fl:
      if len(li.split("Analysis of variance for reflections employed in refinement")) > 1:
        AnalysisInfo.setdefault("K", {})
        AnalysisInfo["K"].setdefault("Title", "Mean[Fo^2] / Mean[Fc^2]")
        k_row = fl[i+3]
        AnalysisInfo["K"].setdefault("y_label", "Fc/Fc(max)")
        AnalysisInfo["K"].setdefault("y_axis", k_row.split())
        k_row = fl[i+9]
        AnalysisInfo["K"].setdefault("Data", k_row.split())
        AnalysisInfo["K"].setdefault("imSize", (256, 128))
        
      elif len(li.split("NUMBER OF UNIQUE DATA AS A FUNCTION OF RESOLUTION IN ANGSTROMS")) > 1:
        AnalysisInfo.setdefault("UniqueData", {})
        AnalysisInfo["UniqueData"].setdefault("Title", "Unique Data")
        AnalysisInfo["UniqueData"].setdefault("y_label", "Two-theta")
        k_row = (fl[i+6]).split()
        AnalysisInfo["UniqueData"].setdefault("Data", k_row)
        k_row = fl[i+10]
        AnalysisInfo["UniqueData"].setdefault("y_axis", k_row.split())
        AnalysisInfo["UniqueData"].setdefault("imSize", (256, 128))
        
      elif len(li.split("Most Disagreeable Reflections")) > 1:
        AnalysisInfo.setdefault("DisagreeReflections", {})
        AnalysisInfo["DisagreeReflections"].setdefault("Title", "Most Disagreeable Reflections")
        AnalysisInfo["DisagreeReflections"].setdefault("y_label", "Numbers")
        j = i + 4
        fobs=0
        fcalc=0
        while fl[j] != "\n":
          k_row = fl[j]
          r = k_row.split()
          assert(len(r) >= 4)
          if r[3] > r[4]:
            fobs += 1
          else:
            fcalc += 1
          j += 1
        AnalysisInfo["DisagreeReflections"].setdefault("y_axis", ["Fobs > Fcalc", "Fcalc > Fobs"])
        AnalysisInfo["DisagreeReflections"].setdefault("Data", [fobs, fcalc])
        AnalysisInfo["DisagreeReflections"].setdefault("imSize", (256, 128))
      i += 1
      
    #for value in AnalysisInfo["K"]: print value
    self.graphInfo = AnalysisInfo
    
  def make_analysis_image(self):
    if not self.graphInfo:
      image_location = "%s/%s.png" %(self.filepath, self.item)
      self.im.save(image_location, "PNG")
      return
    
    if self.item == "K":
      self.make_K_graph()
    elif self.item == "DisagreeReflections":
      self.make_DisagreeReflections_graph()
    elif self.item == "AutoChem":
      self.make_AutoChem_plot()
    
    ## This whole writing of files to a specific location was only a test, that's been left in by mistake. Sorry John!
    if self.debug:
      if sys.platform.startswith('lin'): # This is to alter path for linux
        testpicturepath = "/tmp/test.png"
      elif sys.platform.startswith('win'): # For windows
        testpicturepath = "C:/test.png"
      elif sys.platform.startswith('darwin'): # For MAC
        testpicturepath = "/tmp/test.png"
      else: # If all else fails assume evil windows
        testpicturepath = "C:/test.png"
      self.im.save("%s"%testpicturepath, "PNG")
      
    self.popout()

  def make_AutoChem_plot(self):
    filepath = self.file_reader("%s/%s.csv" %(self.datadir,"ac_stats"))
    self.get_simple_x_y_pair_data_from_file(filepath)
    self.make_empty_graph(axis_x = True)
    self.draw_pairs()
    
  def ProgramHtml(self, program, method, process, img_name):
    return_to_menu_txt = str(OV.Translate("Return to main menu"))
    if process == "Refining":
      prg = OV.FindValue("snum_refinement_program",None)
      method = OV.FindValue("snum_refinement_method",None)
      program = self.RPD.programs[prg]
    else:
      prg = OV.FindValue("snum_solution_program",None)
      method = OV.FindValue("snum_solution_method",None)
      program = self.SPD.programs[prg]
    name = method  
    method = program.methods[method]
      
    authors = program.author
    reference = program.reference
    help = OV.TranslatePhrase(method.help)
    info = OV.TranslatePhrase(method.info)
    
    txt = htmlTools.get_template("pop_prg_analysis")
    
    if txt:
      txt = txt %(process, self.filename, prg, name, authors, reference, img_name)
    else:
      txt = 'Please provide a template in folder basedir()/etc/gui/blocks/templates/'
    return txt

  def output_data_as_csv(self, filename=None):
    from iotbx import csv_utils
    if filename is None:
      filename = '%s-%s.csv' %(self.filename,self.item)
    filefull = '%s/%s' %(self.filepath,filename)
    f = open(filefull, 'w')
    for dataset in self.data.values():
      fieldnames = (dataset.metadata().get('x_label', 'x'),
                    dataset.metadata().get('y_label', 'y'))
      csv_utils.writer(f, (dataset.x,dataset.y), fieldnames)
    f.close()
    print "%s was created" %filefull

class PrgAnalysis(Analysis):
  
  def __init__(self,prg):
    Analysis.__init__(self)
    self.counter = 0
    self.attempt = 1
    size = (int(OV.FindValue('gui_htmlpanelwidth'))- 30, 150)
    self.item = prg
    self.graphInfo["Title"] = self.item
    self.graphInfo["imSize"] = size
    self.graphInfo["FontScale"] = 0.03
    self.graphInfo["TopRightTitle"] = self.filename
    self.graphInfo["n_cycles"] = OV.FindValue("snum_refinement_max_cycles")
    if self.item == "ShelXL" or self.item == "smtbx-refine":
      #OV.unregisterCallback("procout", self.ShelXL)
      self.prg_type = "refinement"
    elif self.item == "ShelXS" or self.item == "smtbx-solve":
      #OV.unregisterCallback("procout", self.ShelXS)
      self.prg_type = "solution"
      
    self.xl_d = {}
    self.new_graph_please = False
    self.cycle = 0
    self.new_graph = True
    
    self.make_empty_graph()
    if self.prg_type == "refinement":
      program = self.RPD.programs["%s" %self.item]
    elif self.prg_type == "solution":
      program = self.SPD.programs["%s" %self.item]
      
    method = OV.FindValue('snum_%s_method' % self.prg_type)
    method = program.methods[method]
    img_name = "%s.png" %self.item 
    txt = self.ProgramHtml(program, method, "%s: " %self.prg_type.title(), img_name)
    
    OlexVFS.write_to_olex("%s_image.htm" % self.prg_type, txt)
     
    OV.htmlReload()
    self.popout()

  def smtbx_refine(self, line):
    self.new_graph_please = True
    if self.new_graph_please:
      self.run_ShelXS_graph()

  def smtbx_solve(self, line):
    self.new_graph_please = True
    if self.new_graph_please:
      self.run_ShelXS_graph()
      
  def ShelXS(self, line):
    self.new_graph_please = True
    if self.new_graph_please:
      self.run_ShelXS_graph()
    
    
  def ShelXL(self, line):
    self.new_graph_please = False
    mean_shift = 0
    max_shift = 0
    if "before cycle" in line:
      self.cycle = int(line.split("before cycle")[1].strip().split()[0])
      self.xl_d.setdefault("cycle_%i" %self.cycle, {})
    elif "Mean shift/esd =" in line:
      mean_shift = float(line.split("Mean shift/esd =")[1].strip().split()[0])
      self.xl_d["cycle_%i" %self.cycle].setdefault('mean_shift',mean_shift)
    elif "Max. shift = " in line:
      max_shift = float(line.split("Max. shift =")[1].strip().split()[0])
      max_shift_atom = line.split("for")[1].strip().split()[0]
      self.xl_d["cycle_%i" %self.cycle].setdefault('max_shift',max_shift)
      self.xl_d["cycle_%i" %self.cycle].setdefault('max_shift_atom',max_shift_atom)
      self.new_graph_please = True
    if self.new_graph_please:
      self.run_ShelXL_graph()

  def observe_prg(self):
    obs = self.item.replace("-", "_")
    observer = getattr(self,obs)
    OV.registerCallback("procout", observer)

  def observe_shelx_s(self):
    OV.registerCallback("procout", self.ShelXS)

  def run_ShelXS_graph(self):
    cycle = self.cycle
    data = self.xl_d
    top = self.graph_top
    marker_width = 5
    title = self.graphInfo.get('Title', "")
    size = self.graphInfo.get('imSize', "")
    width = size[0]
    height = size[1] - top
    height = self.graph_bottom - self.graph_top
    legend_top = height + 20
    
    legend_top = height + 20
    legend_top = self.graph_bottom + 2
    m_offset = 5
    ## Wipe the legend area
    box = (0,legend_top,width,legend_top + 20)
    self.draw.rectangle(box, fill=self.gui_html_bg_colour)

    x = self.bSides
    y = legend_top
    txt = "No Graphical Output available at this time."
    self.draw.text((x, y), "%s" %txt, font=self.font_large, fill=self.gui_red)

    #txt = str(number)
    ### Draw Current Numbers
    #wX, wY = self.draw.textsize(txt, font=self.font_large)
    #x = width - wX - self.bSides
    #self.draw.text((x, legend_top), "%s" %txt, font=self.font_large, fill="#888888")
    
    image_location = "%s.png" %self.item
    OlexVFS.save_image_to_olex(self.im, image_location, 0)
    self.im.save("%s/.olex/ShelXS.png" %self.filepath, "PNG")
    
    if OV.IsControl('POP_PRG_ANALYSIS'):
      olx.html_SetImage("POP_PRG_ANALYSIS","%s.png" %self.item)
    if self.new_graph:
      OV.htmlReload()
      self.new_graph = False

    
    
  def run_ShelXL_graph(self):
    cycle = self.cycle
    data = self.xl_d
    top = self.graph_top
    marker_width = 5
    title = self.graphInfo.get('Title', "")
    size = self.graphInfo.get('imSize', "")
    width = size[0]
    height = size[1] - top
    height = self.graph_bottom - self.graph_top
    legend_top = height + 20
    bar_width = int((width-2*self.bSides)/self.graphInfo["n_cycles"]) -1 
    
    mean_shift = data["cycle_%i" %cycle].get("mean_shift","n/a")
    max_shift = data["cycle_%i" %cycle].get("max_shift","n/a")
    max_shift_atom = data["cycle_%i" %cycle].get("max_shift_atom","n/a")
    bar_left = ((cycle - 1) * bar_width) + self.bSides + 1
    bar_right = bar_left + bar_width
    bar_bottom = self.graph_bottom -1
    
    number = 0
    if mean_shift != "n/a":
      number = mean_shift
      txt = "Mean shift/esd"
      wX, wY = self.draw.textsize(txt, font=self.font_large)
      x = width - 2*self.bSides - wX
      y = wY + 6
      self.draw.text((x, y), "%s" %txt, font=self.font_large, fill="#888888")
      
      if mean_shift >= 1:
        bar_top = top
      else:
        bar_top = height + top  - (mean_shift * (height))
        
      rR = int(255*mean_shift*2)
      rG = int(255*(1.3-mean_shift*2))
      rB = 0
      
      box = (bar_left,bar_top,bar_right,bar_bottom)
      self.draw.rectangle(box, fill=(rR, rG, rB), outline=(100, 100, 100))

      txt = str("%.3f" %mean_shift)
      wX, wY = self.draw.textsize(txt, font=self.font_large)
      if wX < bar_width:
        x = bar_left + ( bar_width - wX/2 -wX) + self.bSides
        x = bar_left + ( bar_width - wX)/2
        
        if mean_shift < 0.8:
          y = bar_top - 14
        else:
          y = bar_top + 6
        self.draw.text((x, y), "%s" %txt, font=self.font_large, fill="#888888")
        
      if mean_shift < 0.003:
        txt = "OK"
        wX, wY = self.draw.textsize(txt, font=self.font_large)
        x = width - 2*self.bSides - wX
        y = wY + 30
        self.draw.text((x, y - 10), "%s" %txt, font=self.font_large, fill=self.gui_green)
      
    elif max_shift != "n/a":
      number = max_shift
      txt = "Max shift in A"
      wX, wY = self.draw.textsize(txt, font=self.font_large)
      x = width - 2*self.bSides - wX
      y = wY + 3
      self.draw.text((x, y), "%s" %txt, font=self.font_large, fill="#888888")
      if max_shift >= 1:
        bar_top = top
      else:
        bar_top = height + top - (max_shift *(height - top))
      
      rR = int(255*max_shift*2)
      rG = int(255*(1.3-max_shift*2))
      rB = 0
        
      box = (bar_left,bar_top,bar_right,bar_bottom)
      self.draw.rectangle(box, fill=(rR, rG, rB), outline=(100, 100, 100))
      
      txt = str(max_shift_atom)
      wX, wY = self.draw.textsize(txt, font=self.font_large)
      x = bar_left + wX/2 + self.bSides
      y = bar_top - 13
      self.draw.text((x, y), "%s" %txt, font=self.font_large, fill="#888888")

      
    legend_top = height + 20
    legend_top = self.graph_bottom + 2
    m_offset = 5
    ## Wipe the legend area
    box = (0,legend_top,width,legend_top + 20)
    self.draw.rectangle(box, fill=self.gui_html_bg_colour)

    txt = str(number)
    ## Draw Current Numbers
    wX, wY = self.draw.textsize(txt, font=self.font_large)
    x = width - wX - self.bSides
    self.draw.text((x, legend_top), "%s" %txt, font=self.font_large, fill="#888888")
    
    image_location = "%s.png" %self.item
    OlexVFS.save_image_to_olex(self.im, image_location, 0)
    self.im.save("%s/.olex/Refinement.png" %self.filepath, "PNG")
    
    if OV.IsControl('POP_PRG_ANALYSIS'):
      olx.html_SetImage("POP_PRG_ANALYSIS","ShelXL.png")
    if self.new_graph:
      OV.htmlReload()
      self.new_graph = False
    

class WilsonPlot(Analysis):
  def __init__(self, n_bins=10, method="olex"):
    Analysis.__init__(self)
    self.n_bins = abs(int(n_bins)) #Number of bins for Histograms
    self.method = method      #Method by which graphs are generated
    self.item = "wilson"
    self.graphInfo["Title"] = "Wilson Plot"
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.make_wilson_plot()
    self.popout()

  def make_wilson_plot(self):
    if self.method == 'cctbx':
      self.cctbx_wilson_statistics()
    else:
      filepath = "%s/%s.%s.csv" %(self.filepath,self.filename,"wilson")
      self.get_simple_x_y_pair_data_from_file(filepath)
    self.make_empty_graph(axis_x = True)
    self.draw_pairs(reverse_y = True)
    grad = self.make_gradient_box(size = ((int(self.imX * 0.64), int(self.imY * 0.1))))
    size = ((self.im.size[0]), (self.im.size[1] + grad.size[1]))
    colour = self.gui_html_bg_colour
    new = Image.new('RGB', size, colour)
    new.paste(self.im, (0,0))
    new.paste(grad, (int(self.xSpace+self.bSides),int(self.im.size[1]-20)))
    draw = ImageDraw.Draw(new)
    
    imX, imY = new.size
    
    metadata = self.data['dataset1'].metadata()
    estats = metadata.get("<|E^2-1|>", 'n/a')
    
    text = []
    text.append("B = %.3f" %float(metadata.get("B")))
    text.append("K = %.3f" %float(metadata.get("K")))
    text.append("<|E^2-1|> = %.3f" %float(metadata.get("<|E^2-1|>", 0)))
    text.append(r"%%|E| > 2 = %.3f"%float(metadata.get(r"%|E| > 2", 0)))
    
    left = grad.size[0] + self.xSpace + imX * 0.04
    top = self.im.size[1] - imY * 0.02
    top_original = top
    i = 0
    for txt in text:
      unicode_txt = self.get_unicode_characters(txt)
      wX, wY = draw.textsize(unicode_txt, font=self.font_tiny)
      colour = "#444444"
      if "E^2" in txt:
        if float(estats) < float(self.wilson_grad_begin):
          colour = "#ff0000"
        elif float(estats) > float(self.wilson_grad_end):
          colour = "#ff0000"
      draw.text((left, top), "%s" %unicode_txt, font=self.font_tiny, fill=colour)
      top += wY +2
      i += 1
      if i == 2:
        top = top_original
        left = int(grad.size[0] + self.xSpace + imX * 0.14)
    self.im = new

  def cctbx_wilson_statistics(self):  
    from cctbx_olex_adapter import OlexCctbxGraphs
    cctbx = OlexCctbxGraphs('wilson', n_bins=2*self.n_bins)
    wp = cctbx.run()
    metadata = {}
    metadata.setdefault("K", 1/wp.wilson_intensity_scale_factor)
    metadata.setdefault("B", wp.wilson_b)
    metadata.setdefault("y_label", "sin^2(theta)/lambda^2")
    metadata.setdefault("x_label", "ln(<Fo2>).Fexp2)")
    # convert axes in formula
    metadata.setdefault("fit_slope", 1/wp.fit_slope)
    metadata.setdefault("fit_y_intercept", -wp.fit_y_intercept/wp.fit_slope)
    metadata.setdefault("<|E^2-1|>", wp.mean_e_sq_minus_1)
    metadata.setdefault("%|E| > 2", wp.percent_e_sq_gt_2)
    self.metadata = metadata
    self.data.setdefault('dataset1', Dataset(wp.y,wp.x,metadata))

  def make_gradient_box(self, size = (320, 35)):
    boxWidth = size[0]
    boxHeight = size[1]*0.4
    boxTopOffset = self.imY * 0.035
    colour = self.gui_html_bg_colour
    im = Image.new('RGB', size, colour)
    draw = ImageDraw.Draw(im)
    #target_left = (0,0,255)
    #target_right = (0,255,0)
    middle = boxWidth/2
    box = (0,boxTopOffset,boxWidth-1,boxTopOffset+boxHeight-1)
    draw.rectangle(box, fill=self.gui_html_bg_colour, outline=(200, 200, 200))
    margin_left = int((boxWidth/4))
    margin_right = int((boxWidth/4)*3)
    
    scale = float((0.968-0.736)/(boxWidth - (margin_right - margin_left)))
    metadata = self.data['dataset1'].metadata()
    value = float(metadata.get("<|E^2-1|>", 0))
    
    begin = (0.736 - margin_left * scale)
    end = (0.968 + margin_left * scale)
    self.wilson_grad_begin = begin
    self.wilson_grad_end = end
    
    if value < (0.736 - 0.736*0.2):
      max1 = 128.0
      c1 = (255.0, 0 , 0)
      max2 = 128.0
      c2 = (0, 0, 0)
    elif (0.736 - 0.736*0.1) < value < (0.736 + 0.736*0.1):
      max1 = 128.0
      c1 = (0, 255.0 , 0)
      max2 = 128.0
      c2 = (0, 0, 0)
    elif (0.736 + 0.736*0.1) <= value <= (0.968 - 0.968*0.1):
      max1 = 128.0
      c1 = (255.0, 0, 0)
      max2 = 128.0
      c2 = (255.0, 0, 0)
    elif (0.968 - 0.968*0.1) < value < (0.968 + 0.968*0.1):
      max1 = 128.0
      c1 = (0, 0, 0)
      max2 = 128.0
      c2 = (0, 255.0, 0)
    elif value > (0.968 + 0.968*0.1):
      max1 = 128.0
      c1 = (0, 0, 0)
      max2 = 128.0
      c2 = (255.0, 0, 0)
    else:
      max1 = 128.0
      c1 = (255.0, 0, 0)
      max2 = 128.0
      c2 = (255.0, 0, 0)
      
    for i in xrange(boxWidth-2):
      i += 1
      if i == margin_left:
        txt = "non-centrosymmetric"
        wX, wY = draw.textsize(txt, font=self.font_tiny)
        draw.text((i-int(wX/2), 0), "%s" %txt, font=self.font_tiny, fill=self.gui_html_highlight_colour)
        txt = "0.736"
        wX, wY = draw.textsize(txt, font=self.font_tiny)
        draw.text((i-int(wX/2), boxTopOffset+boxHeight-1), "%s" %txt, font=self.font_tiny, fill=self.titleColour)
      if i == (margin_right):
        txt = "centrosymmetric"
        wX, wY = draw.textsize(txt, font=self.font_tiny)
        draw.text((i-int(wX/2), 0), "%s" %txt, font=self.font_tiny, fill=self.gui_html_highlight_colour)
        txt = "0.968"
        wX, wY = draw.textsize(txt, font=self.font_small)
        draw.text((i-int(wX/2), boxTopOffset+boxHeight-1), "%s" %txt, font=self.font_tiny, fill=self.titleColour)
      top =  int(boxTopOffset+1)
      bottom = int(boxTopOffset+boxHeight-2)
      if i < margin_left:
        step = (max1)/margin_left
        col = max1+step*(margin_left - i)
        col = int(col)
        fill = self.grad_fill(max1, c1, col)
        draw.line(((i, top),(i, bottom)), fill=fill)
      elif i == margin_left:
        draw.line(((i, top),(i, bottom)), fill=(200, 200, 200))
      elif i < middle:
        step = (max1)/(middle-margin_left)
        col = max1+step*(i - margin_left)
        col = int(col)
        fill = self.grad_fill(max1, c1, col)
        draw.line(((i, top),(i, bottom)), fill=fill)
      elif i == middle:
        draw.line(((i, top),(i, bottom)), fill=(200, 200, 200))
      elif i > middle and i < (margin_right):
        step = (max2)/(margin_right-middle)
        col = max2+step*(margin_right - i)
        col = int(col)
        fill = self.grad_fill(max2, c2, col)
        draw.line(((i, top),(i, bottom)), fill=fill)
      elif i == (margin_right):
        draw.line(((i, top),(i, bottom)), fill=(200, 200, 200))
      else:
        step = ((max2)/(boxWidth-margin_right))
        col = max2+step*(i - margin_right)
        col = int(col)
        fill = self.grad_fill(max2, c2, col)
        draw.line(((i, top),(i, bottom)), fill=fill)
    val = int((value - begin) / scale)
    txt = unichr(8226)
    wX, wY = draw.textsize(txt, font=self.font_bold_normal)
#    draw.line(((val, boxTopOffset+1),(val, boxTopOffset+boxHeight-1)), width=wX , fill=(255,235,10))
    draw.ellipse(((val-int(wX/2), boxTopOffset+3),(val+int(wX/2), boxTopOffset+boxHeight-3)), fill=(255,235,10))
    draw.text((val-int(wX/2), boxTopOffset-self.imY*0.001), "%s" %txt, font=self.font_bold_normal, fill="#ff0000")
    image_location = "%s.png" %("grad")
#    im.save("C:/grad.png", "PNG")
    OlexVFS.save_image_to_olex(im, image_location,  1)
    return im
  
  def grad_fill(self, max, c1, col):
    fill = []
    for c in c1:
      if not c:
        c = col
        fill.append(int(col))
      else:
        fill.append(int(c))
    fill = tuple(fill)
    return fill

class ChargeFlippingPlot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.counter = 0
    self.attempt = 1
    size = (int(OV.FindValue('gui_htmlpanelwidth'))- 30, 150)
    self.graphInfo["Title"] = "Charge Flipping"
    self.graphInfo["imSize"] = size
    self.graphInfo["FontScale"] = 0.03
    self.graphInfo["TopRightTitle"] = self.filename
    self.new_graph = True
    
    self.make_empty_graph()
    program = self.SPD.programs["smtbx-solve"]
    method = program.methods["Charge Flipping"]
    img_name = "XY.png"
    txt = self.ProgramHtml(program, method, "Solving", img_name)
    OlexVFS.write_to_olex('xy.htm', txt)
    OlexVFS.write_to_olex('solution_image.htm', txt)

  def run_charge_flipping_graph(self, flipping, solving, previous_state):
    top = self.graph_top
    marker_width = 5
    title = self.graphInfo.get('Title', "")
    size = self.graphInfo.get('imSize', "")
    width = size[0]
    height = size[1] - top
    height = self.graph_bottom - self.graph_top
    
    if solving.state is solving.guessing_delta:
      if previous_state is not solving.guessing_delta:
        t = "%s" %self.attempt
        wX, wY = self.draw.textsize(t, font=self.font_bold_large)
        x = self.counter + marker_width + 5
        self.draw.text((x, self.graph_bottom - wY -3), "%s" %t, font=self.font_bold_large, fill="#888888")
        self.attempt += 1
        if self.counter != 0:
          self.counter += 1
          self.draw.line(((self.counter + marker_width, self.graph_top),(self.counter + marker_width, self.graphY+self.graph_top - 2)), width=1, fill=(230, 230, 230))
        return
    
    elif solving.state is solving.solving:
      cc = flipping.c_tot_over_c_flip()
      R1 = flipping.r1_factor()
      self.counter+=marker_width
      if self.counter > width - 10:
        self.make_empty_graph()
        self.draw = ImageDraw.Draw(self.im)
        self.counter = self.bSides
        t = "...continued"
        wX, wY = self.draw.textsize(t, font=self.font_normal)
        x = width - wX - self.bSides - 3
        self.draw.text((x, 20), "%s" %t, font=self.font_normal, fill="#888888")
      x = self.counter
      
      ## Draw CC
      txt = "cc=%.3f" %cc
      if cc > 1: cc = 1
      ccR = int(255*cc)
      ccG = int(255*(1.3-cc))
      ccB = 0
      cc = height*(1-cc) + top
      box = (x,cc,x+marker_width,cc+marker_width)
      self.draw.rectangle(box, fill=(ccR, ccG, ccB), outline=(ccR/2, ccG/2, 0))
      
      ## Draw R1
      txt += ", R1=%.3f" %R1
      rR = int(255*R1*2)
      rG = int(255*(1.3-R1*2))
      rB = 0
      R1 = height*(1-R1) + top
      box = (x,R1,x+marker_width,R1+2)
      self.draw.rectangle(box, fill=(rR, rG, rB), outline=(rR/2, rG/2, 0))
      font_name = "Vera"
      font_size = 10
      font = self.registerFontInstance(font_name, font_size)
      
      legend_top = height + 20
      legend_top = self.graph_bottom + 1
      m_offset = 5
      ## Wipe the legend area
      box = (0,legend_top,width,legend_top + 20)
      self.draw.rectangle(box, fill=self.gui_html_bg_colour)
      
      ## Draw CC Legend
      box = (10,legend_top +m_offset,10+marker_width, legend_top+marker_width + m_offset)
      self.draw.rectangle(box, fill=(ccR, ccG, ccB), outline=(ccR/2, ccG/2, 0))
      tt = "CC"
      self.draw.text((10+marker_width+3, legend_top), "%s" %tt, font=self.font_large, fill="#888888")
      
      ## Draw R1 Legend
      box = (40,legend_top + m_offset + 1,40+marker_width,legend_top + m_offset + 3)
      self.draw.rectangle(box, fill=(rR, rG, rB), outline=(rR/2, rG/2, 0))
      tt = "R1"
      self.draw.text((40+marker_width+3, legend_top), "%s" %tt, font=self.font_large, fill="#888888")
      
      ## Draw Current Numbers
      wX, wY = self.draw.textsize(txt, font=self.font_large)
      x = width - wX - self.bSides
      self.draw.text((x, legend_top), "%s" %txt, font=self.font_large, fill="#888888")
      
      image_location = "XY.png"
      res = OlexVFS.save_image_to_olex(self.im, image_location,  0)
      self.im.save("%s/.olex/Solution.png" %self.filepath, "PNG")
      
      if OV.IsControl('POP_PRG_ANALYSIS'):
        olx.html_SetImage("POP_PRG_ANALYSIS","XY.png")
      if self.new_graph:
        OV.htmlReload()
        self.new_graph = False

class CumulativeIntensityDistribution(Analysis):
  def __init__(self, n_bins=20, output_csv_file=False):
    Analysis.__init__(self)
    self.n_bins = abs(int(n_bins)) #Number of bins for Histograms
    self.item = "cumulative"
    self.graphInfo["Title"] = "Cumulative Intensity Distribution"
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    self.make_cumulative_intensity_distribution()
    self.popout()
    if output_csv_file in (True, 'true', 'True'):
      self.output_data_as_csv()

  def make_cumulative_intensity_distribution(self):
    # Ideal distributions
    def acentric_distribution(x):
      return 1-math.exp(-x)
    def centric_distribution(x):
      return math.sqrt(erf(0.5*x))
    def twinned_acentric_distribution(x):
      ## twinned acentric distribution
      ## E. Stanley, J.Appl.Cryst (1972). 5, 191
      return 1-(1+2*x)*math.exp(-2*x)

    self.cctbx_cumulative_intensity_distribution()
    self.make_empty_graph(axis_x = True)
    self.plot_function(centric_distribution)
    self.plot_function(acentric_distribution)
    # E. Stanley, J.Appl.Cryst (1972). 5, 191
    self.plot_function(twinned_acentric_distribution)
    
    colour1 = self.graphInfo['plot_function']['colour1']
    colour2 = self.graphInfo['plot_function']['colour2']
    colour3 = self.graphInfo['plot_function']['colour3']
    
    key = self.draw_key({1:{'label':'Centric',
                            'colour':colour1,
                            },
                         2:{'label':'Acentric',
                            'colour':colour2,
                            },
                         3:{'label':'Twinned Acentric',
                            'colour':colour3,
                            },
                         })
    self.im.paste(key, 
                  (int(self.graph_right-(key.size[0]+50)),
                   int(self.graph_bottom-(key.size[1]+50)))
                  )
    
    self.draw_pairs()

  def cctbx_cumulative_intensity_distribution(self):
    from cctbx_olex_adapter import OlexCctbxGraphs
    cctbx = OlexCctbxGraphs('cumulative', n_bins=self.n_bins)
    xy_plot = cctbx.run()
    metadata = {}
    metadata.setdefault("y_label", xy_plot.yLegend)
    metadata.setdefault("x_label", xy_plot.xLegend)
    self.metadata = metadata
    #self.data.setdefault('dataset1', Dataset(xy_plot.x,[i*100 for i in xy_plot.y],metadata))
    self.data.setdefault('dataset1', Dataset(xy_plot.x, xy_plot.y,metadata))
    self.data['dataset1'].show_summary()

class CompletenessPlot(Analysis):
  def __init__(self, n_bins=20, output_csv_file=False):
    Analysis.__init__(self)
    self.item = "completeness"
    self.n_bins = abs(int(n_bins))
    self.graphInfo["Title"] = "Completeness Plot"
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    self.cctbx_completeness_statistics()
    self.make_empty_graph(axis_x = True)
    self.draw_pairs(reverse_x=True)
    self.popout()
    if output_csv_file in (True, 'true', 'True'):
      self.output_data_as_csv()

  def cctbx_completeness_statistics(self):
    from cctbx_olex_adapter import OlexCctbxGraphs
    cctbx = OlexCctbxGraphs('completeness', n_bins=self.n_bins)
    data_object = cctbx.run()
    data_object.completeness.show()
    metadata = {}
    metadata.setdefault("y_label", "Shell Completeness")
    metadata.setdefault("x_label", "Resolution")
    self.metadata = metadata
    self.data.setdefault('dataset1', Dataset(data_object.x,[i*100 for i in data_object.y],metadata))

class SystematicAbsencesPlot(Analysis):
  def __init__(self, output_csv_file=False):
    Analysis.__init__(self)
    self.item = "sys_absences"
    self.graphInfo["Title"] = "Systematic Absences Intensity Distribution"
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    self.cctbx_systematic_absences_plot()
    if self.have_data:
      self.popout()
      if output_csv_file in (True, 'true', 'True'):
        self.output_data_as_csv()

  def cctbx_systematic_absences_plot(self):
    from cctbx_olex_adapter import OlexCctbxGraphs
    cctbx = OlexCctbxGraphs('sys_absent')
    xy_plot = cctbx.run()
    
    metadata = {}
    metadata.setdefault("y_label", xy_plot.yLegend)
    metadata.setdefault("x_label", xy_plot.xLegend)
    self.metadata = metadata
    if xy_plot.x is None:
      self.have_data = False
      print "No systematic absences present"
      return
    self.have_data = True
    self.data.setdefault('dataset1', Dataset(xy_plot.x, xy_plot.y, metadata))
    self.data['dataset1'].show_summary()
    self.draw_origin = True
    self.make_empty_graph(axis_x = True)
    self.graphInfo['marker']['size'] = int(self.im.size[0]/120)
    ratio = 0.75
    colour = self.graphInfo['marker']['colour']
    border_colour = (int(colour[0] * ratio),
                     int(colour[1] * ratio),
                     int(colour[2] * ratio))
    self.graphInfo['marker']['border_colour'] = border_colour
    self.draw_pairs()

class Fobs_Fcalc_plot(Analysis):
  def __init__(self, output_csv_file=False):
    Analysis.__init__(self)
    self.item = "Fobs_Fcalc"
    self.graphInfo["Title"] = "Fobs vs Fcalc"
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    self.make_f_obs_f_calc_plot()
    self.popout()
    if output_csv_file in (True, 'true', 'True'):
      self.output_data_as_csv()

  def make_f_obs_f_calc_plot(self):
    from cctbx_olex_adapter import OlexCctbxGraphs
    cctbx = OlexCctbxGraphs('f_obs_f_calc')
    xy_plot = cctbx.run()
    data = Dataset(xy_plot.f_calc_sq,xy_plot.f_obs_sq,metadata={})
    self.data.setdefault('dataset1', data)
    self.make_empty_graph(axis_x = True)
    self.draw_pairs()

class Dataset(object):
  def __init__(self, x, y, metadata):
    self.x = x
    self.y = y
    self._metadata = metadata

  def xy_pairs(self):
    return izip(self.x,self.y)

  def metadata(self):
    return self._metadata

  def show_summary(self):
    print ''.join("%f, %f\n" %(x,y) for x,y in self.xy_pairs())

Analysis_instance = Analysis()
OV.registerMacro(Analysis_instance.run_Analysis,
                 'n_bins-Number of bins (for histograms only!)&;method-olex or cctbx')

OV.registerFunction(WilsonPlot)
OV.registerFunction(CumulativeIntensityDistribution)
OV.registerFunction(CompletenessPlot)
OV.registerFunction(SystematicAbsencesPlot)
OV.registerFunction(Fobs_Fcalc_plot)

def array_scalar_multiplication(array, multiplier):
  return [i * multiplier for i in array]
