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
import os
try:
  import olx
  import olex
  import olexex
  import htmlTools
  import olex_core
except:
  pass

from ImageTools import ImageTools
IT = ImageTools()

from olexFunctions import OlexFunctions
OV = OlexFunctions()
guiParams = OV.GuiParams()


from scitbx.math import erf

global GuiGraphChooserComboExists
GuiGraphChooserComboExists = False

global PreviousHistoryNode
PreviousHistoryNode = None


class Graph(ImageTools):
  def __init__(self):
    ImageTools.__init__(self)
    self.params = OV.Params().graphs.reflections
    self.marker_params = (self.params.marker_1, self.params.marker_2)
    self.function_params = (self.params.function_1, self.params.function_2, self.params.function_3)
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
    self.min_x = None
    self.min_y = None
    self.max_x = None
    self.max_y = None
    self.decorated = False

    self.graphInfo = {
      "TopRightTitle":self.filename,
    }

  def plot_function(self, function, locals=None, width=1, n_points=50):
    if locals is None:
      locals = {}
    self.get_division_spacings_and_scale()
    spacing = self.delta_x/n_points
    x_values = []
    y_values = []
    x = self.min_x
    for i in xrange(0,n_points+1):
      x_values.append(x)
      locals['x'] = x
      y_values.append(eval(function, math.__dict__, locals))
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
    fill = self.function_params[self.function_counter-1].colour.rgb
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
        self.draw.line(line, fill=fill, width=width)
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

  def draw_key(self, keys_to_draw):
    max_length = 0
    for key in keys_to_draw:
      max_length = max(max_length, len(key['label']))
    boxWidth = int(0.6 * self.font_size_tiny * max_length) + 60
    boxHeight = int((self.font_size_tiny + 10) * (len(keys_to_draw))) + 20
    colour = self.gui_html_bg_colour
    im = Image.new('RGB', (boxWidth,boxHeight), colour)
    draw = ImageDraw.Draw(im)
    box = (2,2,boxWidth-2,boxHeight-2)
    draw.rectangle(box, fill=self.gui_html_bg_colour, outline=(200, 200, 200))
    margin_left = int((boxWidth/4))
    margin_right = int((boxWidth/4)*3)

    txt_colour = "#444444"
    top = 10
    for key in keys_to_draw:
      key_type = key['type']
      assert key_type in ("function", "marker")
      label = key['label']
      left = 15
      wX, wY = draw.textsize(label, font=self.font_tiny)
      if key_type == "function":
        fill = self.function_params[key['number']-1].colour.rgb
        draw.line((left,top+wY/2,left+30,top+wY/2),fill=fill,width=2)
      elif key_type == "marker":
        marker = self.marker_params[key['number']-1]
        marker_width = int(self.im.size[0])*marker.size_factor
        draw.rectangle((left, top+wY/2-marker_width/2, left+marker_width, top+wY/2 + marker_width/2),
                       fill=marker.fill.rgb, outline=marker.border.rgb)
      left = 60
      draw.text((left,top), "%s" %label, font=self.font_tiny, fill=txt_colour)
      top += wY + 10

    return im

  def get_unicode_characters(self, txt):
    txt = txt.replace("two_theta", "2theta")
    txt = txt.replace("stol", "(sin(theta)/lambda)")
    txt = txt.replace("_sq", "^2")
    txt = txt.replace("_star", "*")
    txt = txt.replace("_", " ")
    txt = txt.replace("lambda", unichr(61548))
    txt = txt.replace("theta", unichr(61553))
    txt = txt.replace("sigma", unichr(61555))
    txt = txt.replace("^2", unichr(178))
    txt = txt.replace("^3", unichr(179))
    txt = txt.replace(">", unichr(61681))
    txt = txt.replace("<", unichr(61665))
    txt = txt.replace("Fo2", "Fo%s" %(unichr(178)))
    txt = txt.replace("Fc2", "Fc%s" %(unichr(178)))
    txt = txt.replace("Sum", unichr(8721))
    #txt = txt.replace("Fexp2", "Fexp%s" %(unichr(178)))
    #txt = txt.replace("Fo2", "F%s%s" %(unichr(2092),unichr(178)))
    txt = txt.replace("Fexp", "F%s" %(unichr(2091)))
    txt = txt.replace("angstrom", unichr(197))
    return txt

  def make_x_y_plot(self):
    pass

  def make_empty_graph(self, axis_x=False, draw_title=True):
    import Image
    import ImageFont, ImageDraw, ImageChops

    self.imX = self.params.size_x
    self.imY = self.params.size_y
    fontsize = int(0.08 * self.imX)
    fontscale = 0.02 * self.imX
    f = self.params.font_scale
    fontscale = f * self.imX
    font_name = "Vera"
    self.font_size_large = int(1.4 * fontscale)
    self.font_large = self.registerFontInstance(font_name, self.font_size_large)
    self.font_size_normal = int(1.0 * fontscale)
    self.font_normal = self.registerFontInstance(font_name, self.font_size_normal)
    self.font_size_small = int(0.9 *fontscale)
    self.font_small = self.registerFontInstance(font_name, self.font_size_small)
    self.font_size_tiny = int(0.7 * fontscale)
    self.font_tiny = self.registerFontInstance(font_name, self.font_size_tiny)
    self.light_grey = "#888888"
    self.grey = "#444444"
    self.dark_grey = "#222222"
    font_name = "Vera Bold"
    self.font_bold_large = self.registerFontInstance(font_name, int(1.4 * fontscale))
    self.font_bold_normal = self.registerFontInstance(font_name, int(1.0 * fontscale))

    self.filenameColour = "#bbbbbb"
    self.titleColour = "#777777"
    self.bSides = round(0.012 * self.imX)
    self.xSpace = 0
    self.axis_x = axis_x
    if self.axis_x:
      self.xSpace  = 0.04 * self.imX
    self.bTop = round(0.013 * self.imY)
    self.currX = 0
    self.currY = 0
    size = ((int(self.imX), int(self.imY)))
    colour = self.gui_html_bg_colour
    im = Image.new('RGB', size, colour)
    draw = ImageDraw.Draw(im)
    self.draw = draw

    if draw_title:
      txt = self.graphInfo["Title"]
      if not txt: txt = "Not available"
      x = 0 + self.bSides+self.xSpace
      y = self.bTop
      top_left = (x,y)
      IT.write_text_to_draw(draw, txt, top_left=top_left, font_size=self.font_size_large, font_colour=self.titleColour)
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
    self.graph_bottom = int(self.graphY + self.currY + 0.03*self.imY - self.yAxisSpace)
    self.line_width = int(self.imX * 0.002)

    dx = self.imX - 1*self.bSides
    dy = self.graph_bottom
    box = (self.bSides + self.xSpace, self.currY + 0.03*self.imY, dx, dy)
    if self.line_width > 0:
      fill = (200, 200, 200)
    else:
      fill = self.gui_html_bg_colour
    draw.rectangle(box,  fill=fill, outline=(200, 200, 200))
    self.boxX = dx - self.bSides*2 + self.xSpace
    self.boxY = dy - self.currY
    self.boxXoffset = self.bSides+self.xSpace
    self.graph_right = self.imX - self.bSides
    self.graph_left = self.boxXoffset
    self.boxYoffset = self.currY + 0.03*self.imY
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
      wX, wY = IT.textsize(self.draw, txt, font_size=self.font_size_small)
      x = int(self.bSides + i * barX + (barX - wX)/2)
      y = self.graph_bottom
      top_left = (x,y)
      IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_small, font_colour=self.grey)
      i += 1

  def draw_fit_line(self, slope, y_intercept, write_equation=True):
    if self.min_x is None: self.get_division_spacings_and_scale()
    y1 = (slope * self.min_x + y_intercept)
    y2 = (slope * self.max_x + y_intercept)

    if y1 > self.max_y:
      y1 = self.max_y
    elif y1 < self.min_y:
      y1 = self.min_y

    if slope == 0.0:
      x1 = 0.0
    else:
      x1 = (y1-y_intercept)/slope
    x1 = self.graph_left \
       + ((float(x1) * self.scale_x)) \
       + ((0 - self.max_x) * self.scale_x) \
       + (self.delta_x * self.scale_x)

    if y2 > self.max_y:
      y2 = self.max_y
    elif y2 < self.min_y:
      y2 = self.min_y

    if slope == 0.0:
      x2 = self.max_x
    else:
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

    if slope == 0.0:
      width = 4
    else:
      width = 5
    self.draw.line((x1+2, y1, x2-2, y2), width=width, fill="#eeeeee")

    if y_intercept >= 0: sign = '+'
    else: sign = '-'
    txt = "y = %.3fx %s %.3f" %(slope,sign,abs(y_intercept))

    wX, wY = IT.textsize(self.draw, txt, font_size=self.font_size_small)

    if write_equation:
      if slope > 0 or (self.reverse_x or self.reverse_y):
        x = self.graph_left + self.imX * 0.1 # write equation top left
      else:
        x = self.graph_right - wX - self.imX * 0.1  # write equation top right
      y = self.graph_top + self.imY * 0.1
      top_left = (x,y)
      IT.write_text_to_draw(
        self.draw, txt, top_left=top_left, font_size=self.font_size_small, font_colour=self.grey)

  def draw_pairs(self, reverse_y=False, reverse_x=False, marker_size_factor=None):
    self.reverse_y = reverse_y
    self.reverse_x = reverse_x
    self.ax_marker_length = int(self.imX * 0.006)
    self.get_division_spacings_and_scale()
    self.draw_x_axis()
    self.draw_y_axis()
    for dataset in self.data.values():
      if dataset.metadata().get("fit_slope") and dataset.metadata().get("fit_slope"):
        slope = float(dataset.metadata().get("fit_slope"))
        y_intercept = float(dataset.metadata().get("fit_y_intercept"))
        self.draw_fit_line(slope, y_intercept)
      self.draw_data_points(
        dataset.xy_pairs(), sigmas=dataset.sigmas, indices=dataset.indices,
        marker_size_factor=marker_size_factor)

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
        if dataset.sigmas is not None:
          min_ys.append(min(dataset.y-dataset.sigmas))
        else:
          min_ys.append(min(dataset.y))
      max_xs.append(max(dataset.x))
      if dataset.sigmas is not None:
        max_ys.append(max(dataset.y+dataset.sigmas))
      else:
        max_ys.append(max(dataset.y))

    if self.auto_axes:
      min_x = min(min_xs)
      min_y = min(min_ys)
    else:
      min_x = 0.0
      min_y = 0.0
    max_x = max(max_xs)
    max_y = max(max_ys)
    self.max_y = max_y + .05*abs(max_y - min_y)
    self.max_x = max_x + .05*abs(max_x - min_x)
    if min_x != 0.0:
      self.min_x = min_x - .05*abs(max_x - min_x)
    else: self.min_x = 0.0
    if min_y != 0.0:
      self.min_y = min_y - .05*abs(max_y - min_y)
    else: self.min_y = 0.0

    delta_x = self.max_x - self.min_x
    delta_y = self.max_y - self.min_y
    self.delta_x = delta_x
    self.delta_y = delta_y
    self.scale_x = ((self.graph_right - self.graph_left)/delta_x)
    self.scale_y = ((self.graph_bottom - self.graph_top)/delta_y)

    self.bY = (self.graph_bottom + self.graph_top)
    self.bX = (self.graph_left + self.graph_right)

  def get_divisions(self, delta):
    assert delta != 0
    dv = delta/self.params.n_divisions
    if dv < 10 and dv > 1.0:
      pow10 = 0
    else:
      log10 = math.log10(dv)
      if log10 < -1.25:
        pow10 = math.floor(log10)
      else:
        pow10 = round(log10)
    #dv_ = math.ceil(dv / math.pow(10,pow10))
    dv_ = dv / math.pow(10,pow10)
    if dv_ < 2:
      dv_ = 1.0
    elif dv_ < 2.5:
      dv_ = 2.0
    elif dv_ < 4:
      dv_ = 2.5
    elif dv_ < 5:
      dv_ = 4.0
    else:
      dv_ = 5.0
    return dv_ * math.pow(10, round(pow10))

  def draw_bars(self, dataset, y_scale_factor=1.0, bar_labels=None, colour_function=None, draw_bar_labels=True):
    top = self.graph_top
    marker_width = 5
    width = self.params.size_x
    height = self.graph_bottom - self.graph_top
    legend_top = height + 20
    labels = dataset.metadata().get('labels')
    y_label = dataset.metadata().get('y_label')
    title = self.graphInfo.get('Title')
    n_bars = len(dataset.x)
    bar_width = math.floor((width-2*self.bSides)/n_bars)
    if title is not None:
      wX, wY = IT.textsize(self.draw, title, font_size=self.font_size_large)
      x = width - 2*self.bSides - wX
      y = wY + 6
      top_left = (x,y)
      IT.write_text_to_draw(self.draw, title, top_left=top_left, font_size=self.font_size_large, font_colour=self.light_grey)

    for i, xy in enumerate(dataset.xy_pairs()):
      last = len(dataset.x)
      x_value, y_value = xy
      bar_left = ((i) * bar_width) + self.bSides + 1
      bar_right = bar_left + bar_width
      bar_bottom = self.graph_bottom -1
      y_value_scale = y_value * y_scale_factor

      if y_value_scale >= 1:
        bar_top = top
      else:
        bar_top = height + top  - (y_value_scale * (height))

      if colour_function is not None:
        fill = colour_function(y_value_scale)
      else:
        fill = (0,0,0)

      if i == last -1:
        bar_right = width - self.bSides - 1
      box = (bar_left,bar_top,bar_right,bar_bottom)

      self.draw.rectangle(box, fill=fill, outline=(100, 100, 100))

      if dataset.hrefs is not None:
        href = dataset.hrefs[i]
      else:
        #href = "Html.Update"
        href = ""
      if dataset.targets is not None:
        target = dataset.targets[i]
      else:
        target = "%.3f" %y_value
      self.map_txt_list.append(
        """<zrect coords="%i,%i,%i,%i" href="%s" target="%s">"""
        % (bar_left, top, bar_right, bar_bottom, href, target))
      if draw_bar_labels:
        if bar_labels is not None:
          txt = bar_labels[i]
        else:
          txt = "%.3f" %y_value
        wX, wY = IT.textsize(self.draw, txt, font_size=self.font_size_large)

        if wX < bar_width:
          x = bar_left + ( bar_width - wX/2 -wX) + self.bSides
          x = bar_left + ( bar_width - wX)/2
          if y_value < 0.8:
            y = bar_top - 14
          else:
            y = bar_top + 6
          top_left = (x,y)
          IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_large, font_colour=self.light_grey)

        if y_value < 0.003:
          txt = "OK"
          wX, wY = IT.textsize(self.draw, txt, font_size=self.font_size_large)
          x = width - 2*self.bSides - wX
          y = wY + 30
          top_left = (x, y - 10)
          top_left = (x,y)
          IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_large, font_colour=self.gui_green)


  def draw_history_bars(self, dataset, y_scale_factor=1.0, bar_labels=None, colour_function=None, draw_bar_labels=True):
    top = self.graph_top
    marker_width = 5
    width = self.params.size_x
    height = self.graph_bottom - self.graph_top
    legend_top = height + 20
    labels = dataset.metadata().get('labels')
    y_label = dataset.metadata().get('y_label')
    title = self.graphInfo.get('Title')
    n_bars = len(dataset.x)
    max_bars = self.params.max_bars
    all_in_one_history = self.params.all_in_one_history

    if all_in_one_history:
      bar_width = math.floor((width-10)/n_bars)
      if n_bars <= max_bars:
        bar_width = int(width/max_bars)
      max_bars = n_bars

    else:
      bar_width = int(width/max_bars)

    if title is not None:
      wX, wY = IT.textsize(self.draw, title, font_size=self.font_size_large)
      x = width - 2*self.bSides - wX
      y = wY + 6
      top_left = (x,y)
      IT.write_text_to_draw(self.draw, title, top_left=top_left, font_size=self.font_size_large, font_colour=self.light_grey)

    j = 0
    img_no = 0
    colour = self.gui_html_bg_colour
    for i, xy in enumerate(dataset.xy_pairs()):
      if j == 0:
        barImage = Image.new('RGB', (int(width-2*self.bSides-1), int(height-1)), color=colour)
        barDraw = ImageDraw.Draw(barImage)
      last = len(dataset.x)
      x_value, y_value = xy
#      bar_left = ((i) * bar_width) + self.bSides + 1
      bar_left = ((j) * bar_width)
      bar_right = bar_left + bar_width
      bar_bottom = self.graph_bottom - 4
      y_value_scale = y_value * y_scale_factor
      if y_value_scale >= 1:
        bar_top = top - self.bTop
        bar_top = 0
      else:
        bar_top = height - self.bTop + top  - (y_value_scale * (height))
        bar_top = height - (y_value_scale * (height))

      if colour_function is not None:
        fill = colour_function(y_value_scale)
      else:
        fill = (0,0,0)

      if i == last - 1 and n_bars > max_bars and all_in_one_history:
        bar_right = width - self.bSides - 1

      box = (bar_left,bar_top,bar_right,bar_bottom)

      outline_colour = (200,200,200)

      if self.decorated:
        decorated_fill = OV.FindValue('gui_html_highlight_colour')
        barDraw.rectangle(box, fill=decorated_fill, outline=outline_colour)
        barDraw.rectangle((bar_left+3,bar_top+3,bar_right-3,bar_bottom-3), fill=fill)

        self.decorated = False
      else:
        barDraw.rectangle(box, fill=fill, outline=outline_colour)
        barDraw.rectangle(box, fill=fill, outline=outline_colour)


      if dataset.hrefs is not None:
        href = dataset.hrefs[i]
      else:
        href = ""
      if dataset.targets is not None:
        target = dataset.targets[i]
      else:
        target = "%.3f" %y_value
      self.map_txt_list.append(
        """<zrect coords="%i,%i,%i,%i" href="%s" target="%s">"""
        % (bar_left, top, bar_right, bar_bottom, href, target))
      if draw_bar_labels:
        if bar_labels is not None:
          txt = bar_labels[i]
        else:
          txt = "%.3f" %y_value
        wX, wY = IT.textsize(self.draw, txt, font_size=self.font_size_large)

        if wX < bar_width:
          x = bar_left + ( bar_width - wX/2 -wX) + self.bSides
          #x = bar_left + ( bar_width - wX)/2
          if y_value < 0.8:
            y = bar_top - 14
          else:
            y = bar_top + 6
          top_left = (x,y)
          IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_large, font_colour=self.light_grey)

        if y_value < 0.003:
          txt = "OK"
          wX, wY = IT.textsize(self.draw, txt, font_size=self.font_size_large)
          x = width - 2*self.bSides - wX
          y = wY + 30
          top_left = (x, y - 10)
          top_left = (x,y)
          IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_large, font_colour=self.gui_green)

      j += 1
      if j == max_bars or i == last - 1:
        img_no += 1
        j = 0
        self.image_location = "history_%s.png" %img_no

        historyText = """\
        <zimg name="HISTORY_IMAGE" border="0" src="%s">
        %s
        </zimg>
        """ %(self.image_location, self.map_txt)


        previous_img = img_no -1
        next_img = img_no + 1

        scaleTxt = '''
<input
  type="spin"
  name="HistoryScale"
  width="45"
  label="Scale "
  bgcolor="$spy.GetParam(gui.html.table_bg_colour)"
  fgcolor="$spy.GetParam(gui.html.font_colour)"
  valign='center'
  min="2"
  height="$spy.GetParam(gui.html.spin_height)"
  value="$spy.GetParam(graphs.program_analysis.y_scale_factor)"
  onchange="spy.SetParam(graphs.program_analysis.y_scale_factor,GetValue(HistoryScale))>>spy._make_history_bars()>>html.Reload"
>'''

        if all_in_one_history:
          all_in_oneText = "<a href='spy.SetParam(graphs.program_analysis.all_in_one_history,False)>>spy._make_history_bars()>>html.reload'>Split Display</a>"
          previous_img = ""
          next_img = ""
        else:
          all_in_oneText = '''
<a href='spy.SetParam(graphs.program_analysis.all_in_one_history,True)>>spy._make_history_bars()>>html.reload'>Show All Bars</a>'''
          previous_img = "<a href='spy.olex_fs_copy(history-info_%s.htm,history-info.htm)>>updatehtml'><zimg src=previous.png></a>" %(img_no -1)
          next_img = "<a href='spy.olex_fs_copy(history-info_%s.htm,history-info.htm)>>updatehtml'><zimg src=next.png></a>" %(img_no + 1)

        historyTextNext = '''
<table width='100%%' border='0' cellpadding='0'>
<tr>
  <td align='left' width='20%%'></td>
  <td align='center' width='30%%'>%s</td>
  <td align='center' width='30%%'>%s</td>
  <td align='right' width='20%%'>%s</td>
</tr>
</table>''' %(scaleTxt, all_in_oneText, next_img)
        historyTextPrevious = '''
<table width='100%%' border='0' cellpadding='0'>
<tr>
  <td align='left' width='20%%' >%s</td>
  <td align='center' width='30%%'>%s</td>
  <td align='center' width='30%%'>%s</td>
  <td align='right' width='20%%'></td>
</tr>
</table>''' %(previous_img, scaleTxt, all_in_oneText)
        historyTextBoth = '''
<table width='100%%' border='0' cellpadding='0'>
<tr>
  <td align='left' width='20%%'>%s</td>
  <td align='center' width='30%%'>%s</td>
  <td align='center' width='30%%'>%s</td>
  <td align='right' width='20%%'>%s</td>
</tr>
</table>''' %(previous_img, scaleTxt, all_in_oneText, next_img)
        if img_no == 1 and i != last - 1:
#          IT.write_text_to_draw(barDraw, 'previous', align='left', max_width=width)
          historyText += historyTextNext
        elif img_no == 1 and i == last - 1 and not all_in_one_history:
          historyText += scaleTxt
          pass
#          IT.write_text_to_draw(barDraw, 'previous', align='left', max_width=width)
        elif i == last - 1:
#          IT.write_text_to_draw(barDraw, 'previous', align='left', max_width=width)
          historyText += historyTextPrevious
#          IT.write_text_to_draw(barDraw, 'next', align='right', max_width=width)#
        else:
#          IT.write_text_to_draw(barDraw, 'previous', align='left', max_width=width)
          historyText += historyTextBoth

        self.im.paste(barImage, (int(self.bSides+1),int(top+1)), None)
        label = '%s (%s)' %(self.tree.active_node.program, self.tree.active_node.method)
        try:
          label += ' - %.2f%%' %(self.tree.active_node.R1 * 100)
        except (ValueError, TypeError):
          pass
        self.draw_legend(label, font_size=self.font_size_normal)
        OlexVFS.save_image_to_olex(self.im, self.image_location, 0)
        #self.draw_legend("%.3f" %(bars[self.i_active_node][0]))
        OV.write_to_olex('history-info_%s.htm' %img_no, historyText)
        OV.write_to_olex('history-info.htm', historyText)

  def draw_legend(self, txt, font_size=None):
    if not font_size:
      self.font_size_large
    height = self.graph_bottom - self.graph_top
    width = self.params.size_x
    legend_top = height + 20
    legend_top = self.graph_bottom + 2
    m_offset = 5
    ## Wipe the legend area
    box = (0,legend_top,width,legend_top + 20)
    self.draw.rectangle(box, fill=self.gui_html_bg_colour)
    #txt = '%.3f' %(y_value)
    ## Draw Current Numbers
    wX, wY = IT.textsize(self.draw, txt, font_size=font_size)
    x = width - wX - self.bSides
    top_left = (x, legend_top)
    IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=font_size, font_colour=self.light_grey)

  def draw_data_points(self, xy_pairs, indices=None, sigmas=None, marker_size_factor=None):
    min_x = self.min_x
    max_x = self.max_x
    scale_x = self.scale_x
    delta_x = self.delta_x
    max_y = self.max_y
    min_y = self.min_y
    scale_y = self.scale_y
    delta_y = self.delta_y

    marker = self.marker_params[self.dataset_counter]
    self.dataset_counter += 1
    fill = marker.fill.rgb
    outline = marker.border.rgb
    marker_width = int(self.im.size[0])*marker.size_factor
    if marker_size_factor is not None:
      marker_width *= marker_size_factor
    half_marker_width = marker_width/2

    if self.reverse_x:
      x_constant = self.bX \
                 - (half_marker_width + self.boxXoffset
                    + ((0 - max_x) * self.scale_x)
                    + (delta_x * self.scale_x))
      scale_x = -self.scale_x
    else:
      x_constant = (self.graph_left - half_marker_width
                    + ((0 - max_x) * self.scale_x)
                    + (delta_x * self.scale_x))
      scale_x = self.scale_x

    if self.reverse_y:
      y_constant = (self.graph_top - half_marker_width
                    + ((0 - max_y) * scale_y)
                    + (delta_y * scale_y))
      scale_y = self.scale_y
    else:
      y_constant = self.bY \
          - (half_marker_width + self.boxYoffset
             + ((0 - max_y) * scale_y)
             + (delta_y * scale_y))
      scale_y = -self.scale_y

    map_txt_list = self.map_txt_list
    if sigmas is not None:
      for i, (xr, yr) in enumerate(xy_pairs):
        x = x_constant + xr * scale_x
        y = y_constant + yr * scale_y
        dy = sigmas[i]*scale_y
        x_centre = x+half_marker_width
        y_centre = y+half_marker_width
        y_plus_dy = y+half_marker_width+dy
        y_minus_dy = y+half_marker_width-dy
        line = ((x+half_marker_width, y_plus_dy),
                (x+half_marker_width, y_minus_dy))
        self.draw.line(line, width=self.line_width, fill=(200,200,200))
        self.draw.line(((x, y_plus_dy), (x+marker_width, y_plus_dy)),
                       width=1, fill=(200,200,200))
        self.draw.line(((x, y_minus_dy), (x+marker_width, y_minus_dy)),
                       width=1, fill=(200,200,200))

    for i, (xr, yr) in enumerate(xy_pairs):
      x = x_constant + xr * scale_x
      y = y_constant + yr * scale_y

      if self.im.getpixel((x+half_marker_width, y+half_marker_width)) == fill:
        continue # avoid wasting time drawing points that overlap too much
      box = (x,y,x+marker_width,y+marker_width)
      self.draw.rectangle(box, fill=fill, outline=outline)

      if self.item == "AutoChem":
        map_txt_list.append("""<zrect coords="%i,%i,%i,%i" href="reap %s"  target="%s">"""
                            % (box + (xr, yr)))
      else:
        href="UpdateHtml"
        href=""
        if indices is None:
          target = '(%.3f,%.3f)' %(xr, yr)
        else:
          target = '(%.3f,%.3f) %s' %(xr, yr, indices[i])
        map_txt_list.append("""<zrect coords="%i,%i,%i,%i" href="%s" target="%s">"""
                            % (box + (href, target)))

  def draw_y_axis(self):
    max_y = self.max_y
    min_y = self.min_y
    scale_y = self.scale_y
    delta_y = self.delta_y
    dv_y = self.get_divisions(delta_y)
    y_axis = []

    modulo = dv_y % 1
    if modulo == 0.0:
      precision = 0
    else:
      precision = len(str(modulo).split('.')[-1])

    if min_y < 0 and max_y > 0: # axis are in range to be drawn
      div_val = 0.0
      while div_val > min_y:
        div_val -= dv_y
    else:
      #if dv_y <= 10:
        #div_val = round(min_y-dv_y, precision-1) # minimum value of div_val
      #else:
        #div_val = round(min_y-dv_y, precision)
      div_val = round(min_y-dv_y, precision)
    if div_val == 0.0: div_val = 0.0 # work-around for if div_val is -0.0
    y_axis.append(div_val)
    while div_val < max_y:
      div_val = div_val + float(dv_y)
      y_axis.append(div_val)

    format_string = "%%.%if" %precision
    for item in y_axis:
      val = float(item)
      txt = format_string %item

      wX, wY = self.draw.textsize(txt, font=self.font_small)
      x = self.graph_left - wX - self.imX * 0.01
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
        top_left = (x,y)
      if y + wY/2 <= (self.graph_bottom) and y >= self.boxYoffset -wY/2:
        self.draw.text((x, y), "%s" %txt, font=self.font_small, fill="#444444")
        IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_small, font_colour=self.grey)
        x = self.graph_left
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
    self.im.paste(new, (int(self.xSpace+self.bSides + wY/2), int(self.graph_top +wY/2)))

  def draw_x_axis(self):
    min_x = self.min_x
    max_x = self.max_x
    scale_x = self.scale_x
    delta_x = self.delta_x
    dv_x = self.get_divisions(delta_x)
    x_axis = []

    modulo = dv_x % 1
    if modulo == 0.0:
      precision = 0
    else:
      precision = len(str(modulo).split('.')[-1])

    if min_x < 0 and max_x > 0: # axis are in range to be drawn
      div_val = 0.0
      while div_val > min_x:
        div_val -= dv_x
    else:
      div_val = round(min_x-dv_x, precision-1) # minimum value of div_val
    if div_val == 0.0: div_val = 0.0 # work-around for if div_val is -0.0
    x_axis.append(div_val)
    while div_val < max_x:
      div_val = div_val + float(dv_x)
      x_axis.append(div_val)

    format_string = "%%.%if" %precision
    for item in x_axis:
      val = float(item)
      txt = format_string %item

      wX, wY = self.draw.textsize(txt, font=self.font_small)
      y = self.graph_bottom + self.imX * 0.01

      if self.reverse_x:
        x = self.bX \
          -(self.boxXoffset + wX/2
            + ((val * scale_x))
            + ((0 - max_x) * scale_x)
            + (self.delta_x * scale_x))
      else:
        x = (self.boxXoffset - wX/2
             + ((val * scale_x))
             + ((0 - max_x) * scale_x)
             + (self.delta_x * scale_x))
      if (x+wX)  <= (self.graph_right) and x >= self.graph_left - wX/2:
        self.draw.text((x, y), "%s" %txt, font=self.font_small, fill="#444444")
        x = int(x + wX/2)
        y = y - self.imY * 0.005
        y = self.graph_bottom
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
    self.draw.text((x, y), "%s" %txt, font=self.font_small, fill="#444444")

  #def draw_bars(self):
    #import ImageFont
    #data = []
    #for item in self.graphInfo["Data"]:
      #try:
        #data.append(float(item))
      #except:
        #pass
    #barX = self.graphX/len(data)
    #barScale = self.graphY/max(data)

    #i = 0
    #for item in data:
      #barHeight = (item * barScale)
      #fill = (0, 0, 0)
      #fill = self.gui_html_bg_colour
      #for barcol in self.barcolour:
        #if item > barcol[0]:
          #fill = barcol[1]

      #x = self.bSides + i * barX
      #y = (self.graph_bottom - barHeight + self.yAxisSpace)
      #dx = ((i + 1) * barX) + self.bSides
      #box = (x, y, dx, self.graph_bottom)
      #self.draw.rectangle(box, fill=fill, outline=(100, 100, 100))
      #font_size = int(barX/2)
      #if font_size > 11: font_size = 11
      #font_name = "Verdana"
      #font = self.registerFontInstance(font_name, font_size)
      #if item >= 10:
        #txt = "%.0f" %item
      #else:
        #txt = "%.1f" %item
      #wX, wY = IT.textsize(self.draw, txt, font_size=font_size)

      #if barHeight > wY * 2:
        #top_left = (x + (barX - wX)/2, y + self.graphY * 0.01)
        #IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_small, font_colour=self.dark_grey)
      #i += 1

class Analysis(Graph):
  def __init__(self, function=None, param=None):
    Graph.__init__(self)
    self.basedir = OV.BaseDir()
    self.filefull = OV.FileFull()
    self.filepath = OV.FilePath()
    self.filename = OV.FileName()
    self.datadir = OV.DataDir()
    self.gui_html_bg_colour = OV.GetParam('gui.html.bg_colour').rgb
    self.gui_html_highlight_colour = OV.GetParam('gui.html.highlight_colour').rgb
    self.SPD, self.RPD = ExternalPrgParameters.SPD, ExternalPrgParameters.RPD
    self.debug = False
    self.function = function
    if param:
      self.param = param.split(';')
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
        try:
          x.append(float(xy[0]))
          y.append(float(xy[1]))
        except:
          pass

    self.data.setdefault('dataset1',Dataset(x,y,metadata=metadata))
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
<zimg border="0" src="%s.png">
%s
</zimg>
</body>
</html>
''' %(self.item, self.map_txt)
    htm_location = "%s.htm" %pop_html
    OlexVFS.write_to_olex(htm_location, str)
    extraX = 29
    extraY = 48
    pstr = "popup %s '%s' -b=stcr -t='%s' -w=%s -h=%s -x=1 -y=50" %(
      pop_name, htm_location, pop_name, int(width*1.033), int(height*1.1))
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
        AnalysisInfo["UniqueData"].setdefault("Title", OV.TranslatePhrase("Unique Data"))
        AnalysisInfo["UniqueData"].setdefault("y_label", "Two-theta")
        k_row = (fl[i+6]).split()
        AnalysisInfo["UniqueData"].setdefault("Data", k_row)
        k_row = fl[i+10]
        AnalysisInfo["UniqueData"].setdefault("y_axis", k_row.split())
        AnalysisInfo["UniqueData"].setdefault("imSize", (256, 128))

      elif len(li.split("Most Disagreeable Reflections")) > 1:
        AnalysisInfo.setdefault("DisagreeReflections", {})
        AnalysisInfo["DisagreeReflections"].setdefault("Title", OV.TranslatePhrase("Most Disagreeable Reflections"))
        AnalysisInfo["DisagreeReflections"].setdefault("y_label", OV.TranslatePhrase("Numbers"))
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
  def __init__(self, program, method):
    Analysis.__init__(self)
    self.params = OV.Params().graphs.program_analysis
    self.counter = 0
    self.attempt = 1
    size = (int(OV.GetParam('gui.htmlpanelwidth'))- 30, 150)
    self.item = program.name
    self.graphInfo["Title"] = self.item
    self.params.size_x, self.params.size_y = size
    self.graphInfo["TopRightTitle"] = self.filename
    self.graphInfo["n_cycles"] = OV.GetParam("snum.refinement.max_cycles")
    self.program = program
    self.method = method
    #self.xl_d = {}
    self.new_graph_please = False
    self.cycle = 0
    self.new_graph = True
    self.make_empty_graph()
    self.image_location = "%s.png" %self.item
    txt = self.ProgramHtml()
    OlexVFS.write_to_olex("%s_image.htm" %program.program_type, txt)
    self.update_image()
    self.popout()

  def ProgramHtml(self):
    return_to_menu_txt = str(OV.Translate("Return to main menu"))
    authors = self.program.author
    reference = self.program.reference
    help = OV.TranslatePhrase(self.method.help)
    info = OV.TranslatePhrase(self.method.info)
    txt = htmlTools.get_template("pop_prg_analysis")
    if txt:
      txt = txt %(
        self.program.program_type, self.filename, self.program.name, self.method.name,
        authors, reference, self.program.program_type.upper(), self.image_location,self.map_txt)
    else:
      txt = 'Please provide a template in folder basedir()/etc/gui/blocks/templates/'
    return txt

  def update_image(self):
    OlexVFS.save_image_to_olex(self.im, self.image_location, 0)
    if OV.IsControl('POP_%s_PRG_ANALYSIS' %self.program.program_type.upper()):
      olx.html_SetImage(
        'POP_%s_PRG_ANALYSIS' %self.program.program_type.upper(), self.image_location)
    OlexVFS.write_to_olex("%s_image.htm" %self.program.program_type, self.ProgramHtml())
    if self.new_graph:
      OV.htmlReload()
      self.new_graph = False

class refinement_graph(PrgAnalysis):
  def __init__(self, program, method):
    PrgAnalysis.__init__(self, program, method)

  def get_max_shift_bar_colours(self, shift):
    rR = int(255*shift*2)
    rG = int(255*(1.3-shift*2))
    rB = 0
    return rR, rG, rB

  def get_mean_shift_esd_bar_colours(self, shift):
    rR = int(255*shift*2)
    rG = int(255*(1.3-shift*2))
    rB = 0
    return rR, rG, rB

  def make_graph(self):
    self.make_empty_graph()
    mean_shifts = self.data.get("mean_shift")
    max_shifts = self.data.get("max_shift")
    if max_shifts is not None:
      max_shift_atom = self.data["max_shift"].metadata()["labels"]

    if mean_shifts is not None:
      self.draw_bars(dataset=mean_shifts, y_scale_factor=3.0, colour_function=self.get_mean_shift_esd_bar_colours)
      self.draw_legend("%.3f" %mean_shifts.y[-1])
    elif max_shifts is not None:
      self.draw_bars(dataset=max_shifts, y_scale_factor=3.0, bar_labels=max_shift_atom, colour_function=self.get_max_shift_bar_colours)
      self.draw_legend("%.3f" %max_shifts.y[-1])

    self.update_image()
    return

class smtbx_refine_graph(refinement_graph):
  def __init__(self):
    program = ExternalPrgParameters.defineExternalPrograms()[1].programs["smtbx-refine"]
    method = program.methods["LBFGS"]
    self.item = "smtbx-refine"
    refinement_graph.__init__(self, program, method)
    y_label = self.get_unicode_characters('Max shift in angstrom')
    metadata={'labels':[], 'y_label':y_label}
    self.data.setdefault('max_shift', Dataset(metadata=metadata))

  def observe(self, max_shift, scatterer):
    self.cycle += 1
    self.data['max_shift'].add_pair(self.cycle, max_shift)
    self.data['max_shift']._metadata['labels'].append(scatterer.label)
    self.make_graph()

class ShelXL_graph(refinement_graph):
  def __init__(self, program, method):
    refinement_graph.__init__(self, program, method)

  def observe(self, line):
    mean_shift = 0
    max_shift = 0
    if "before cycle" in line:
      self.cycle = int(line.split("before cycle")[1].strip().split()[0])
      self.data.setdefault("cycle_%i" %self.cycle, {})
    elif "Mean shift/esd =" in line:
      if not self.data.has_key('mean_shift'):
        metadata={'labels':[], 'y_label':'Mean shift/esd'}
        self.data.setdefault('mean_shift', Dataset(metadata=metadata))
      mean_shift = float(line.split("Mean shift/esd =")[1].strip().split()[0])
      self.data['mean_shift'].add_pair(self.cycle, mean_shift)
    elif "Max. shift = " in line:
      if not self.data.has_key('max_shift'):
        y_label = self.get_unicode_characters('Max shift in angstrom')
        metadata={'labels':[], 'y_label':y_label}
        self.data.setdefault('max_shift', Dataset(metadata=metadata))
      max_shift = float(line.split("Max. shift =")[1].strip().split()[0])
      max_shift_atom = line.split("for")[1].strip().split()[0]
      self.data['max_shift'].add_pair(self.cycle, max_shift)
      self.data['max_shift']._metadata['labels'].append(max_shift_atom)
      self.new_graph_please = True
    #self.new_graph_please = True
    if self.new_graph_please:
      self.make_graph()

class ShelXS_graph(PrgAnalysis):
  def __init__(self, program, method):
    PrgAnalysis.__init__(self, program, method)

  def observe(self, line):
    self.new_graph_please = True
    if self.new_graph_please:
      self.make_ShelXS_graph()

  def make_ShelXS_graph(self):
    return

class WilsonPlot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "wilson"
    self.graphInfo["Title"] = OV.TranslatePhrase("Wilson Plot")
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.make_wilson_plot()
    self.popout()

  def make_wilson_plot(self):
    if self.params.wilson_plot.method == 'cctbx':
      self.cctbx_wilson_statistics()
    else:
      olex.m('wilson -b=%i -p' %self.params.wilson_plot.n_bins)
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
      wX, wY = IT.textsize(draw, txt, font_size=self.font_size_tiny)

      colour = "#444444"
      if "E^2" in txt:
        if float(estats) < float(self.wilson_grad_begin):
          colour = "#ff0000"
        elif float(estats) > float(self.wilson_grad_end):
          colour = "#ff0000"
      top_left = (left, top)
      IT.write_text_to_draw(draw, txt, top_left=top_left, font_size=self.font_size_tiny, font_colour=colour)
      top += wY +2
      i += 1
      if i == 2:
        top = top_original
        left = int(grad.size[0] + self.xSpace + imX * 0.14)
    self.im = new

  def cctbx_wilson_statistics(self):
    from reflection_statistics import OlexCctbxGraphs
    n_bins = 2*self.params.wilson_plot.n_bins
    wp = OlexCctbxGraphs('wilson', n_bins=n_bins).xy_plot
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
    self.data.setdefault('dataset1', Dataset(wp.y,wp.x,metadata=metadata))

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
        txt = "acentric"
        txt = OV.TranslatePhrase(txt)
        wX, wY = IT.textsize(draw, txt, font_size=self.font_size_tiny)
        top_left = (i-int(wX/2), 0)
        IT.write_text_to_draw(draw, txt, top_left=top_left, font_size=self.font_size_tiny, font_colour=self.gui_html_highlight_colour)
        txt = "0.736"
        wX, wY = draw.textsize(txt, font=self.font_tiny)
        draw.text((i-int(wX/2), boxTopOffset+boxHeight-1), "%s" %txt, font=self.font_tiny, fill=self.titleColour)
      if i == (margin_right):
        txt = "centric"
        txt = OV.TranslatePhrase(txt)
        wX, wY = draw.textsize(txt, font=self.font_tiny)
        top_left = (i-int(wX/2), 0)
        IT.write_text_to_draw(draw, txt, top_left=top_left, font_size=self.font_size_tiny, font_colour=self.gui_html_highlight_colour)
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
    draw.ellipse(((val-int(wX/2), boxTopOffset+3),(val+int(wX/2), boxTopOffset+boxHeight-3)), fill=(255,235,10))
    draw.text((val-int(wX/2), boxTopOffset-self.imY*0.001), "%s" %txt, font=self.font_bold_normal, fill="#ff0000")
    image_location = "%s.png" %("grad")
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

class ChargeFlippingPlot(PrgAnalysis):
  def __init__(self):
    program = ExternalPrgParameters.defineExternalPrograms()[0].programs["smtbx-solve"]
    method = program.methods["Charge Flipping"]
    self.item = "Charge Flipping"
    PrgAnalysis.__init__(self, program, method)

  def run_charge_flipping_graph(self, flipping, solving, previous_state):
    top = self.graph_top
    marker_width = 5
    title = self.graphInfo.get('Title', "")
    width = self.params.size_x
    height = self.graph_bottom - self.graph_top

    if solving.state is solving.guessing_delta:
      if previous_state is not solving.guessing_delta:
        txt = "%s" %self.attempt
        wX, wY = IT.textsize(self.draw, txt, font_size=self.font_size_large, font_name = "Vera Bold")
        x = self.counter + marker_width + 5
        top_left = (x, self.graph_bottom -wY -3)
        IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_large, font_name = "Vera Bold", font_colour=self.light_grey)
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
        txt = "...continued"
        wX, wY = IT.textsize(self.draw, txt, font_size=self.font_size_normal)
        x = width - wX - self.bSides - 3
        top_left = (x, 20)
        IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_normal, font_colour=self.light_grey)
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
      top_left = (10+marker_width+3, legend_top)
      IT.write_text_to_draw(self.draw, txt, top_left=top_left, font_size=self.font_size_normal, font_colour=self.light_grey)


      ## Draw R1 Legend
      box = (40,legend_top + m_offset + 1,40+marker_width,legend_top + m_offset + 3)
      self.draw.rectangle(box, fill=(rR, rG, rB), outline=(rR/2, rG/2, 0))
      tt = "R1"
      self.draw.text((40+marker_width+3, legend_top), "%s" %tt, font=self.font_large, fill="#888888")

      ## Draw Current Numbers
      wX, wY = self.draw.textsize(txt, font=self.font_large)
      x = width - wX - self.bSides
      self.draw.text((x, legend_top), "%s" %txt, font=self.font_large, fill="#888888")
      self.update_image()

class CumulativeIntensityDistribution(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "cumulative"
    self.graphInfo["Title"] = OV.TranslatePhrase("Cumulative Intensity Distribution")
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    self.make_cumulative_intensity_distribution()
    self.popout()
    if self.params.cumulative_intensity.output_csv_file:
      self.output_data_as_csv()

  def make_cumulative_intensity_distribution(self):
    acentric = "1-exp(-x)"
    centric = "sqrt(erf(0.5*x))"
    twinned_acentric = "1-(1+2*x)*exp(-2*x)" # E. Stanley, J.Appl.Cryst (1972). 5, 191
    locals = {'erf':erf}
    self.cctbx_cumulative_intensity_distribution()
    self.make_empty_graph(axis_x = True)
    self.plot_function(centric, locals=locals)
    self.plot_function(acentric, locals=locals)
    self.plot_function(twinned_acentric, locals=locals)

    key = self.draw_key(({'type': 'function',
                         'number': 1,
                         'label': OV.TranslatePhrase('Centric')},
                        {'type':'function',
                         'number': 2,
                         'label': OV.TranslatePhrase('Acentric')},
                        {'type': 'function',
                         'number': 3,
                         'label': OV.TranslatePhrase('Twinned Acentric')}
                        ))
    self.im.paste(key,
                  (int(self.graph_right-(key.size[0]+40)),
                   int(self.graph_bottom-(key.size[1]+40)))
                  )

    self.draw_pairs()

  def cctbx_cumulative_intensity_distribution(self, verbose=False):
    from reflection_statistics import OlexCctbxGraphs
    xy_plot = OlexCctbxGraphs(
      'cumulative',
      n_bins=self.params.cumulative_intensity.n_bins).xy_plot
    metadata = {}
    metadata.setdefault("y_label", xy_plot.yLegend)
    metadata.setdefault("x_label", xy_plot.xLegend)
    self.metadata = metadata
    self.data.setdefault('dataset1', Dataset(xy_plot.x, xy_plot.y,metadata=metadata))
    if verbose:
      self.data['dataset1'].show_summary()

class CompletenessPlot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "completeness"
    self.graphInfo["Title"] = OV.TranslatePhrase("Completeness Plot")
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    self.reverse_x = self.params.completeness.resolution_as in ('d_spacing', 'd_star_sq')
    self.cctbx_completeness_statistics()
    self.make_empty_graph(axis_x = True)
    self.draw_pairs(reverse_x=self.reverse_x)
    self.popout()
    if self.params.completeness.output_csv_file:
      self.output_data_as_csv()

  def cctbx_completeness_statistics(self):
    from reflection_statistics import OlexCctbxGraphs
    params = self.params.completeness
    xy_plot = OlexCctbxGraphs(
      'completeness',
      reflections_per_bin=params.reflections_per_bin,
      bin_range_as=params.resolution_as).xy_plot
    metadata = {}
    metadata.setdefault("y_label", OV.TranslatePhrase("Shell Completeness"))
    metadata.setdefault("x_label", params.resolution_as)
    self.metadata = metadata
    self.data.setdefault('dataset1', Dataset(xy_plot.x,[i*100 for i in xy_plot.y],metadata=metadata))

class SystematicAbsencesPlot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "sys_absences"
    self.graphInfo["Title"] = OV.TranslatePhrase("Systematic Absences Intensity Distribution")
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = True
    self.cctbx_systematic_absences_plot()
    if self.have_data:
      self.popout()
      if self.params.systematic_absences.output_csv_file:
        self.output_data_as_csv()

  def cctbx_systematic_absences_plot(self):
    from reflection_statistics import OlexCctbxGraphs
    xy_plot = OlexCctbxGraphs('sys_absent').xy_plot
    metadata = {}
    metadata.setdefault("y_label", xy_plot.yLegend)
    metadata.setdefault("x_label", xy_plot.xLegend)
    self.metadata = metadata
    if xy_plot.x is None:
      self.have_data = False
      print "No systematic absences present"
      return
    self.have_data = True
    self.data.setdefault('dataset1', Dataset(xy_plot.x, xy_plot.y, indices=xy_plot.indices, metadata=metadata))
    self.draw_origin = True
    self.make_empty_graph(axis_x = True)
    self.draw_pairs(marker_size_factor = 1/1.5)

class bijvoet_differences_scatter_plot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "bijvoet_differences_scatter"
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = True
    import reflection_statistics
    use_students_t = self.params.bijvoet_differences_scatter_plot.use_students_t
    xy_plot = reflection_statistics.bijvoet_differences_scatter_plot(
      use_students_t=use_students_t).xy_plot_info()
    if xy_plot is None:
      self.have_data = False
      return
    self.graphInfo["Title"] = OV.TranslatePhrase(xy_plot.title)
    metadata = {}
    metadata.setdefault("fit_slope", xy_plot.fit_slope)
    metadata.setdefault("fit_y_intercept", xy_plot.fit_y_intercept)
    metadata.setdefault("y_label", xy_plot.yLegend)
    metadata.setdefault("x_label", xy_plot.xLegend)
    self.metadata = metadata

    self.have_data = True
    self.data.setdefault(
      'dataset1', Dataset(xy_plot.x, xy_plot.y, sigmas=xy_plot.sigmas,
                          indices=xy_plot.indices, metadata=metadata))
    self.draw_origin = True
    self.make_empty_graph(axis_x = True)
    self.draw_pairs(marker_size_factor = 1/1.5)
    if self.have_data:
      self.popout()
      if self.params.bijvoet_differences_scatter_plot.output_csv_file:
        self.output_data_as_csv()

class bijvoet_differences_NPP(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "bijvoet_differences_NPP"
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = True
    import reflection_statistics
    params = self.params.bijvoet_differences_probability_plot
    use_students_t = params.use_students_t
    use_fcf = params.source == "fcf"
    xy_plot = reflection_statistics.bijvoet_differences_NPP(
      use_students_t=use_students_t, use_fcf=use_fcf).xy_plot_info()
    if xy_plot is None:
      self.have_data = False
      return
    self.graphInfo["Title"] = OV.TranslatePhrase(xy_plot.title)
    metadata = {}
    metadata.setdefault("fit_slope", xy_plot.fit_slope)
    metadata.setdefault("fit_y_intercept", xy_plot.fit_y_intercept)
    metadata.setdefault("y_label", xy_plot.yLegend)
    metadata.setdefault("x_label", xy_plot.xLegend)
    self.metadata = metadata
    self.have_data = True
    self.data.setdefault('dataset1', Dataset(xy_plot.x, xy_plot.y, indices=xy_plot.indices, metadata=metadata))
    self.draw_origin = True
    self.make_empty_graph(axis_x = True)
    self.draw_pairs(marker_size_factor = 1/1.5)
    if self.have_data:
      self.popout()
      if self.params.bijvoet_differences_probability_plot.output_csv_file:
        self.output_data_as_csv()

class Normal_probability_plot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "Normal_probability_plot"
    self.graphInfo["Title"] = OV.TranslatePhrase("Normal probability plot")
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = True
    self.draw_origin = True
    self.make_normal_probability_plot()
    self.popout()
    if self.params.normal_probability.output_csv_file in (True, 'true', 'True'):
      self.output_data_as_csv()

  def make_normal_probability_plot(self):
    from reflection_statistics import normal_probability_plot
    xy_plot = normal_probability_plot().xy_plot_info()
    self.metadata.setdefault("y_label", xy_plot.yLegend)
    self.metadata.setdefault("x_label", xy_plot.xLegend)
    metadata = {}
    metadata.setdefault("fit_slope", xy_plot.fit_slope)
    metadata.setdefault("fit_y_intercept", xy_plot.fit_y_intercept)
    data = Dataset(
      xy_plot.x, xy_plot.y, indices=xy_plot.indices, metadata=metadata)
    self.data.setdefault('dataset1', data)
    self.make_empty_graph(axis_x = True)
    self.draw_pairs()


class Fobs_Fcalc_plot(Analysis):
  def __init__(self, batch_number=None):
    Analysis.__init__(self)
    self.item = "Fobs_Fcalc"
    self.graphInfo["Title"] = OV.TranslatePhrase("Fobs vs Fcalc")
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    try:
      batch_number = int(batch_number)
    except (ValueError, TypeError):
      self.batch_number = None
    else:
      self.batch_number = batch_number
    try:
      self.make_f_obs_f_calc_plot()
    except AssertionError, e:
      if str(e) == "model.scatterers().size() > 0":
        print "You need some scatterers to do this!"
        return
      else:
        raise AssertionError, e
    self.popout()
    if self.params.fobs_fcalc.output_csv_file:
      self.output_data_as_csv()

  def make_f_obs_f_calc_plot(self):
    from reflection_statistics import f_obs_vs_f_calc
    xy_plot = f_obs_vs_f_calc(batch_number=self.batch_number).xy_plot
    self.metadata.setdefault("y_label", xy_plot.yLegend)
    self.metadata.setdefault("x_label", xy_plot.xLegend)
    metadata = {}
    metadata.setdefault("fit_slope", xy_plot.fit_slope)
    metadata.setdefault("fit_y_intercept", xy_plot.fit_y_intercept)
    data = Dataset(
      xy_plot.f_calc, xy_plot.f_obs, indices=xy_plot.indices, metadata=metadata)
    self.data.setdefault('dataset1', data)
    if xy_plot.f_obs_omitted.size():
      data_omitted = Dataset(
        xy_plot.f_calc_omitted, xy_plot.f_obs_omitted, indices=xy_plot.indices_omitted)
      self.data.setdefault('dataset2', data_omitted)
    self.make_empty_graph(axis_x = True)
    self.draw_pairs()
    key = self.draw_key(({'type': 'marker',
                         'number': 1,
                         'label': OV.TranslatePhrase('Filtered Data')},
                        {'type':'marker',
                         'number': 2,
                         'label': OV.TranslatePhrase('Omitted Data')}
                        ))
    self.im.paste(key,
                  (int(self.graph_right-(key.size[0]+40)),
                   int(self.graph_bottom-(key.size[1]+40)))
                  )

class Fobs_over_Fcalc_plot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "Fobs_over_Fcalc"
    self.graphInfo["Title"] = OV.TranslatePhrase("Fobs/Fcalc vs resolution")
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    self.max_y = 1.05
    try:
      self.make_plot()
    except AssertionError, e:
      if str(e) == "model.scatterers().size() > 0":
        print "You need some scatterers to do this!"
        return
      else:
        raise AssertionError, e
    self.popout()
    if self.params.fobs_over_fcalc.output_csv_file:
      self.output_data_as_csv()

  def make_plot(self):
    from reflection_statistics import f_obs_over_f_calc
    params = self.params.fobs_over_fcalc
    xy_plot = f_obs_over_f_calc(
      binning=params.binning,
      n_bins=params.n_bins,
      resolution_as=params.resolution_as).xy_plot
    self.metadata.setdefault("y_label", xy_plot.yLegend)
    self.metadata.setdefault("x_label", xy_plot.xLegend)
    metadata = {}
    if not params.binning:
      indices = xy_plot.indices
    else:
      indices = None
    data = Dataset(
      xy_plot.resolution, xy_plot.f_obs_over_f_calc,
      indices=indices, metadata=metadata)
    reverse_x = params.resolution_as in ('d_spacing', 'd_star_sq')
    self.data.setdefault('dataset1', data)
    self.make_empty_graph(axis_x=True)
    #self.plot_function("1")
    self.draw_fit_line(slope=0, y_intercept=1, write_equation=False)
    self.draw_pairs(reverse_x=reverse_x)

class scale_factor_vs_resolution_plot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "scale_factor_vs_resolution"
    self.graphInfo["Title"] = OV.TranslatePhrase("Scale factor vs resolution")
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    self.max_y = 1.05
    try:
      self.make_plot()
    except AssertionError, e:
      if str(e) == "model.scatterers().size() > 0":
        print "You need some scatterers to do this!"
        return
      else:
        raise AssertionError, e
    self.popout()
    if self.params.scale_factor_vs_resolution.output_csv_file:
      self.output_data_as_csv()

  def make_plot(self):
    from reflection_statistics import scale_factor_vs_resolution
    params = self.params.scale_factor_vs_resolution
    xy_plot = scale_factor_vs_resolution(
      params.n_bins, params.resolution_as).xy_plot_info()
    self.metadata.setdefault("y_label", xy_plot.yLegend)
    self.metadata.setdefault("x_label", xy_plot.xLegend)
    metadata = {}
    data = Dataset(
      xy_plot.x, xy_plot.y, metadata=metadata)
    self.data.setdefault('dataset1', data)
    self.make_empty_graph(axis_x=True)
    self.draw_fit_line(slope=0, y_intercept=1, write_equation=False)
    reverse_x = params.resolution_as in ('d_spacing', 'd_star_sq')
    self.draw_pairs(reverse_x=reverse_x)

class r1_factor_vs_resolution_plot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "r1_factor_vs_resolution"
    self.graphInfo["Title"] = OV.TranslatePhrase("R1 factor vs resolution")
    self.graphInfo["pop_html"] = self.item
    self.graphInfo["pop_name"] = self.item
    self.graphInfo["TopRightTitle"] = self.filename
    self.auto_axes = False
    #self.max_y = 1.05
    try:
      self.make_plot()
    except AssertionError, e:
      if str(e) == "model.scatterers().size() > 0":
        print "You need some scatterers to do this!"
        return
      else:
        raise AssertionError, e
    self.popout()
    if self.params.r1_factor_vs_resolution.output_csv_file:
      self.output_data_as_csv()

  def make_plot(self):
    from reflection_statistics import r1_factor_vs_resolution
    params = self.params.r1_factor_vs_resolution
    xy_plot = r1_factor_vs_resolution(
      params.n_bins, params.resolution_as).xy_plot_info()
    self.metadata.setdefault("y_label", xy_plot.yLegend)
    self.metadata.setdefault("x_label", xy_plot.xLegend)
    metadata = {}
    data = Dataset(
      xy_plot.x, [y*100 for y in xy_plot.y], metadata=metadata)
    self.data.setdefault('dataset1', data)
    self.make_empty_graph(axis_x=True)
    reverse_x = params.resolution_as in ('d_spacing', 'd_star_sq')
    self.draw_pairs(reverse_x=reverse_x)


class X_Y_plot(Analysis):
  def __init__(self):
    Analysis.__init__(self)
    self.item = "X_Y_plot"
    print("Good things will come to those who wait")
    self.run()

  def run(self):
#    filepath = self.file_reader("%s/%s.csv" %(self.datadir,"ac_stats"))
    filepath = ("%s/%s.csv" %(self.datadir,"ac_stats"))
    self.get_simple_x_y_pair_data_from_file(filepath)
    self.graphInfo.update(self.metadata)
    self.make_empty_graph(axis_x = True)
    self.draw_pairs()
    self.graphInfo.setdefault("pop_html", 'acgraph.htm')
    self.graphInfo.setdefault("pop_name", 'acgraph')

    self.popout()


class HistoryGraph(Analysis):

  def __init__(self, history_tree):
    Analysis.__init__(self)
    self.params = OV.Params().graphs.program_analysis
    self.i_bar = 0
    self.tree = history_tree
    #size = (OV.GetParam('gui.htmlpanelwidth')- 32, 100)
    self.item = "history"
    #self.params.size_x, self.params.size_y = size
    #self.make_empty_graph(draw_title=False)
    #self.image_location = "history.png"
    self.green = OV.GetParam('gui.green').rgb[1]
    self.red = OV.GetParam('gui.red').rgb[0]
    self.blue = 0
    self.make_graph()
    #self.popout()


  def make_graph(self):
    global PreviousHistoryNode
    bars = []

    node = self.tree.active_child_node
    #if node == PreviousHistoryNode:
    #  return
    #else:
    #  PreviousHistoryNode = node

    while node is not None:
      R1 = node.R1
      href = "spy.revert_history(%s)>>UpdateHtml>>if html.IsPopup(history-tree) then spy.popout_history_tree()" %(node.name)
      target = '%s (%s)' %(node.program, node.method)
      if node.is_solution:
        R1 = 1
      else:
        if R1 == 'n/a': R1 = 0.99
        try:
          target += ' - %.2f%%' %(node.R1 * 100)
        except (ValueError, TypeError):
          pass
      if node is self.tree.active_node:
        self.i_active_node = len(bars)
      bars.append((R1,href,target))
      node = node.active_child_node
    n_bars = len(bars)
    size = (OV.GetParam('gui.htmlpanelwidth')- 32, 100)
    self.params.size_x, self.params.size_y = size
    self.make_empty_graph(draw_title=False)

    y_scale_factor = self.params.y_scale_factor


    if len(bars) > 0:
      x = []
      y = []
      hrefs = []
      targets = []
      for i, bar in enumerate(bars):
        x.append(i+1)
        y.append(bar[0]) # R factor
        hrefs.append(bar[1])
        targets.append(bar[2])
      data = Dataset(x, y, hrefs=hrefs, targets=targets)
      self.draw_history_bars(dataset=data, y_scale_factor=y_scale_factor,
                     colour_function=self.get_bar_colours,
                     draw_bar_labels=False)
      #label = '%s (%s)' %(self.tree.active_node.program, self.tree.active_node.method)
      #try:
        #label += ' - %.2f%%' %(self.tree.active_node.R1 * 100)
      #except (ValueError, TypeError):
        #pass
      #self.draw_legend(label)
    ##self.draw_legend("%.3f" %(bars[self.i_active_node][0]))
    #historyText = """\
#<zimg name="HISTORY_IMAGE" border="0" src="%s">
#%s
#</zimg>
#""" %(self.image_location, self.map_txt)
    #OV.write_to_olex('history-info.htm',historyText)

  def get_bar_colours(self, bar_height):
    factor = self.params.y_scale_factor
    #if self.i_bar == self.i_active_node:
      #fill = (int(255*bar_height), int(255*(1.3-bar_height)), 0)
      #self.decorated = True
      ##fill = OV.GetParam('gui.grey').rgb
    if bar_height == factor:
      fill = (139, 0, 204)
    else:
      fill = (int(self.red*bar_height), int(self.green*(1.3-bar_height)), self.blue)
    #if self.i_bar != self.i_active_node:
      #fill = IT.adjust_colour(fill, luminosity=1.5)
    self.i_bar += 1
    return fill


class Dataset(object):
  def __init__(self, x=None, y=None, indices=None, sigmas=None,
               hrefs=None, targets=None, metadata={}):
    if x is None: x = []
    if y is None: y = []
    self.x = x
    self.y = y
    self.sigmas = sigmas
    self.hrefs = hrefs
    self.targets = targets
    self.indices = indices
    self._metadata = metadata

  def xy_pairs(self):
    return zip(self.x,self.y)

  def metadata(self):
    return self._metadata

  def show_summary(self):
    print ''.join("%f, %f\n" %(x,y) for x,y in self.xy_pairs())

  def add_pair(self, x, y):
    self.x.append(x)
    self.y.append(y)

Analysis_instance = Analysis()
OV.registerMacro(Analysis_instance.run_Analysis,
                 'n_bins-Number of bins (for histograms only!)&;method-olex or cctbx')

OV.registerFunction(WilsonPlot)
OV.registerFunction(CumulativeIntensityDistribution)
OV.registerFunction(CompletenessPlot)
OV.registerFunction(SystematicAbsencesPlot)
OV.registerFunction(Fobs_Fcalc_plot)
OV.registerFunction(Fobs_over_Fcalc_plot)
OV.registerFunction(Normal_probability_plot)
OV.registerFunction(r1_factor_vs_resolution_plot)
OV.registerFunction(scale_factor_vs_resolution_plot)
OV.registerFunction(X_Y_plot)
OV.registerFunction(bijvoet_differences_scatter_plot)
OV.registerFunction(bijvoet_differences_NPP)

def array_scalar_multiplication(array, multiplier):
  return [i * multiplier for i in array]


def makeReflectionGraphOptions(graph, name):
  value = graph.short_caption
  options_gui = []
  i = 1
  for object in graph.active_objects():
    i += 1
    data_type = object.type.phil_type
    caption = object.caption
    value = object.extract()
    obj_name = name.upper() + "_" +  object.caption.upper().replace(" ","_").replace("%","").replace("-","_")
    if data_type == "int":
      ctrl_name = 'SPIN_%s' %(obj_name)
      d = {'ctrl_name':ctrl_name,
           'value':value,
           'max':'30',
           'label':'%s ' %caption,
           'onchange':'spy.SetParam(graphs.reflections.%s.%s,GETVALUE(%s))' %(
             graph.name, object.name,ctrl_name),
           }
      options_gui.append(htmlTools.make_spin_input(d))

    elif data_type in ("str", "float"):
      ctrl_name = 'TEXT_%s' %(obj_name)
      d = {'ctrl_name':ctrl_name,
           'value':value,
           'label':'%s ' %caption,
           'onchange':'spy.SetParam(graphs.reflections.%s.%s,GETVALUE(%s))' %(
             graph.name, object.name,ctrl_name),
           'readonly':'readonly',
           }
      options_gui.append(htmlTools.make_input_text_box(d))

    elif data_type == "bool":
      ctrl_name = 'TICK_%s' %(obj_name)
      d = {'ctrl_name':ctrl_name,
           'value':'%s ' %caption,
           'checked':'%s' %value,
           'oncheck':'spy.SetParam(graphs.reflections.%s.%s,True)' %(
             graph.name, object.name),
           'onuncheck':'spy.SetParam(graphs.reflections.%s.%s,False)' %(
             graph.name, object.name),
           'width':80,
           'bgcolor':"",
           'fgcolor':"",
           }
      options_gui.append(htmlTools.make_tick_box_input(d))

    elif data_type == "choice":
      items_l = []
      ctrl_name = 'COMBO_%s' %(obj_name)
      for thing in object.words:
        items_l.append(thing.value.lstrip('*'))
      items = ";".join(items_l)
      d = {'ctrl_name':ctrl_name,
           'label':'%s ' %caption,
           'items':items,
           'value':object.extract(),
           'onchange':'spy.SetParam(graphs.reflections.%s.%s,GETVALUE(%s))>>spy.make_reflection_graph(GetValue(SET_REFLECTION_STATISTICS))' %(
             graph.name, object.name,ctrl_name),
           'width':'',
           }
      options_gui.append(htmlTools.make_combo_text_box(d))

  options_gui = '\n<td>%s</td>\n' %'</td>\n<td>'.join(options_gui)
  colspan = i
  return options_gui, colspan

def makeReflectionGraphGui():
  global GuiGraphChooserComboExists

  value = False
  gui_d = {}
  gui_d.setdefault('colspan', '1')
  gui_d.setdefault('options_gui', "")
  gui_d.setdefault('make_graph_button', "")
  gui_d.setdefault('graph_chooser', "")

  if GuiGraphChooserComboExists:
    value = OV.GetValue('SET_REFLECTION_STATISTICS')
  if not value:
    GuiGraphChooserComboExists = True
    value = "- %Please Select% -"
    help_name = None
    name = None
  else:
    name = value.lower().replace(" ", "_").replace("-", "_")
    graph = olx.phil_handler.get_scope_by_name('graphs.reflections.%s' %name)
    if not graph:
      value = "no phil"
      help_name = None
    else:
      gui_d['options_gui'], gui_d['colspan'] = makeReflectionGraphOptions(graph, name)
      help_name = graph.help
      onclick = 'spy.make_reflection_graph\(%s)' %name
      d = {'name':'BUTTON_MAKE_REFLECTION_GRAPH',
           'bgcolor':guiParams.html.input_bg_colour,
           'onclick': onclick,
           'width':'30',
           'value':'Go',
           'valign':'top',
          }
      #gui_d['make_graph_button'] = htmlTools.make_input_button(d)
      gui_d['make_graph_button'] = '$spy.MakeHoverButton(button_small-go@MakeGraphs,%s)' %onclick

  gui_d['help'] = htmlTools.make_table_first_col(
    help_name=help_name, popout=False)
  d = {'ctrl_name':'SET_REFLECTION_STATISTICS',
     'items':"-- %Please Select% --;%Wilson Plot%;%Cumulative Intensity%;" +\
             "%Systematic Absences%;%Fobs-Fcalc%;%Fobs over Fcalc%;" +\
             "%Completeness%;%Normal Probability%;" +\
             "%Scale factor vs resolution%;%R1 factor vs resolution%;" +\
             "%Bijvoet Differences% %Probability Plot%;" +\
             "%Bijvoet Differences% %Scatter Plot%",
     'height':guiParams.html.combo_height,
     'bgcolor':guiParams.html.input_bg_colour,
     'value':value,
     'onchange':'spy.make_reflection_graph(GetValue(SET_REFLECTION_STATISTICS))>>updatehtml',
     'manage':'manage',
     'readonly':'readonly',
     'width':'$eval(html.clientwidth(self)-140)',
     'readonly':'readonly',
    }
  gui_d['graph_chooser']=htmlTools.make_combo_text_box(d)

  gui_d['row_table_on'] = htmlTools.include_block('gui/blocks/row_table_on.htm').replace('%','%%')
  gui_d['row_table_off'] = htmlTools.include_block('gui/blocks/row_table_off.htm')
  gui_d['bgcolor'] = guiParams.html.table_firstcol_colour


  txt = '''
<tr>
%(help)s
%(row_table_on)s
<td>
%(graph_chooser)s
</td>
<td align='right'>
%(make_graph_button)s
</td>
%(row_table_off)s
</tr>
''' %gui_d
  if gui_d['options_gui'] != '':
    txt += '''
<tr>
<td valign='center' width="8" align='center' bgcolor=%(bgcolor)s>
</td>
%(row_table_on)s
%(options_gui)s
%(row_table_off)s
</tr>
''' %gui_d
  txt = OV.Translate(txt)

  return txt

OV.registerFunction(makeReflectionGraphGui)

def make_reflection_graph(name):
  name = name.lower().replace(" ", "_").replace("-", "_")
  run_d = {'wilson_plot': WilsonPlot,
           'cumulative_intensity': CumulativeIntensityDistribution,
           'systematic_absences': SystematicAbsencesPlot,
           'fobs_fcalc': Fobs_Fcalc_plot,
           'fobs_over_fcalc': Fobs_over_Fcalc_plot,
           'completeness': CompletenessPlot,
           'normal_probability': Normal_probability_plot,
           'r1_factor_vs_resolution': r1_factor_vs_resolution_plot,
           'scale_factor_vs_resolution': scale_factor_vs_resolution_plot,
           'bijvoet_differences_probability_plot': bijvoet_differences_NPP,
           'bijvoet_differences_scatter_plot': bijvoet_differences_scatter_plot,
           }
  func = run_d.get(name)
  if func is not None:
    func()

OV.registerFunction(make_reflection_graph)


class HealthOfStructure():
  def __init__(self):
    self.hkl_stats = {}
    if not olexex.isPro():
      return
    phil_file = r"%s/etc/CIF/diagnostics.phil" %(OV.BaseDir())
    olx.phil_handler.adopt_phil(phil_file=phil_file)
    self.grade_1_colour = OV.GetParam('gui.skin.diagnostics.colour_grade1')
    self.grade_2_colour = OV.GetParam('gui.skin.diagnostics.colour_grade2')
    self.grade_3_colour = OV.GetParam('gui.skin.diagnostics.colour_grade3')
    self.grade_4_colour = OV.GetParam('gui.skin.diagnostics.colour_grade4')
    self.available_width = int(OV.GetParam('gui.htmlpanelwidth') - OV.GetParam('gui.htmlpanelwidth_margin_adjust'))

    hkl = OV.HKLSrc()
    if not os.path.exists(hkl):
      print "There is no reflection file associated with this structure"
      txt = "<tr><table width='100%%'><tr bgcolor=%s align='center'>" %self.grade_4_colour
      txt += "<td colspan='2'><font color=#ffffff>There is no reflection file</font><td>"
      txt += "</tr></table></tr>"
      txt = txt.decode('utf-8')
      OV.write_to_olex("hos.htm" , txt)
      return
    self.hkl_stats = olex_core.GetHklStat()
    self.make_HOS_html()

  def make_HOS_html(self):
    txt = "<tr><table width='100%%' cellpadding=0 cellspacing=0><tr>"
    l = ['MeanIOverSigma','Rint']
    for item in l:
      bg_colour = self.get_bg_colour(item)
      display = OV.GetParam('diagnostics.hkl.%s.display' %item)
      value_format = OV.GetParam('diagnostics.hkl.%s.value_format' %item)
      value = self.hkl_stats[item]
      raw_val = value
      if "%" in value_format:
        value_format = value_format.replace('%','f%%')
        value = value * 100
        #raw_val = value
      value_format = "%." + value_format
      value = value_format %value
      use_image = False
      if use_image:
        txt += self.make_hos_images(item=item, colour=bg_colour, display=display, value_raw=raw_val, value_display=value, n=len(l))
      else:
        txt += '''
  <td bgcolor=%s align='center' width='%s%%'><font color='#ffffff'>
    %s: <b>%s</b>
  </font></td>
'''%(bg_colour, 100/len(l), display, value)

    txt += "</tr></table></tr>"
    txt = txt.decode('utf-8')
    OV.write_to_olex("hos.htm" , txt)

  def make_hos_images(self, item='test', colour='#ff0000', display='Display', value_display='10%', value_raw='0.1', n=1):
    boxWidth = self.available_width/n - 10
    boxHeight = 20
    boxHalf = 8
    im = Image.new('RGB', (boxWidth,boxHeight), colour.hexadecimal)
    im = Image.new('RGB', (boxWidth,boxHeight), OV.GetParam('gui.html.table_firstcol_colour').hexadecimal)
    draw = ImageDraw.Draw(im)
    value_raw = float(value_raw)
    op = OV.GetParam('diagnostics.hkl.%s.op' %item)
    curr_x = 0
    for i in xrange(4):
      i += 1
      top = OV.GetParam('diagnostics.hkl.%s.top' %item)
      limit = OV.GetParam('diagnostics.hkl.%s.grade%s' %(item, i))
      print item, limit
#      if limit > value_raw:
#        continue
      limit_width = int((limit/top) * boxWidth)
      if op == "greater":
        box = (0,boxHalf,limit_width,boxHeight)
      elif op == 'smaller':
        box = (curr_x,boxHalf,limit_width,boxHeight)
        curr_x += limit_width
      fill = OV.GetParam('gui.skin.diagnostics.colour_grade%i' %i).hexadecimal
      draw.rectangle(box, fill=fill)

    if item == "MeanIOverSigma":
      display = IT.get_unicode_characters("I/sigma")
    if item == "Rint":
      display = "Rint"
    font = IT.registerFontInstance("Vera", 11)
    x = 2
    y = boxHalf
    draw.text((x, y), "%s" %display, font=font, fill="#ffffff")
#    IT.write_text_to_draw(draw, display, font_colour='#ffffff', font_size=12)
#    IT.write_text_to_draw(draw, value_display, align='right', max_width=boxWidth - 2, font_colour='#ffffff', font_size=17)
    IT.write_text_to_draw(draw, str(top), align='right', max_width=boxWidth - 2, font_colour='#ffffff', font_size=11)
    y = 0
    r = 18
    x = int((value_raw/top) * boxWidth - r/2)
    draw.ellipse(((x, y),(x+r, y+r)), fill="#ff0000")
    draw.text((x, y), "%s" %value_display, font=font, fill="#ffffff")


    OlexVFS.save_image_to_olex(im, item, 0)
    txt = '''
<td align='center'><zimg src=%s></td>''' %item
    return txt

  def get_bg_colour(self, item):
    op = OV.GetParam('diagnostics.hkl.%s.op' %item)
    val = self.hkl_stats[item]
    for i in xrange(4):
      i += 1
      if op == "greater":
        if val >= OV.GetParam('diagnostics.hkl.%s.grade%s' %(item, i)):
          break
      elif op == 'smaller':
        if val <= OV.GetParam('diagnostics.hkl.%s.grade%s' %(item, i)):
          break

    if i == 1:
      retVal = self.grade_1_colour
    elif i == 2:
      retVal = self.grade_2_colour
    elif i == 3:
      retVal = self.grade_3_colour
    elif i == 4:
      retVal = self.grade_4_colour

    return retVal

OV.registerFunction(HealthOfStructure)
