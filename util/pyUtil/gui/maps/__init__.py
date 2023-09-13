import olex
import olx
from olexFunctions import OV
import os

debug = OV.IsDebugging()

class MapUtil:

  def __init__(self):
    self.scale = 50

  def deal_with_map_buttons(self, onoff, img_bases, map_type):
    ## First, set all images to hidden
    retVal = True
    if onoff is None:
      if olx.xgrid.Visible() == 'true':
        if OV.GetVar("olex2.map_type") != map_type:
          onoff = "on"
        else:
          onoff = "off"
      else:
        onoff = "on"

    if onoff == 'off':
      olex.m('xgrid.visible(false)')
      for img_base in img_bases:
        use_image= "up=%soff.png" %img_base
        OV.SetImage("IMG_%s" %img_base.upper(),use_image)
      retVal = True

    if onoff == 'on':
      for img_base in img_bases:
        use_image= "up=%son.png" %img_base
        OV.SetImage("IMG_%s" %img_base.upper(),use_image)
      retVal = False
    return retVal

  def deal_with_controls(self):
    self.get_map_scale()
    if OV.IsControl('SNUM_XGRID_SCALE_SLIDE'):
      olx.html.SetValue('SNUM_XGRID_SCALE_SLIDE', self.value)
    if OV.IsControl('SNUM_XGRID_SCALE_VALUE'):
      olx.html.SetValue('SNUM_XGRID_SCALE_SLIDE', self.value)

  def VoidView(self, recalculate='0', onoff=None):
    img_bases = ['small-Void']
    if self.deal_with_map_buttons(onoff, img_bases, 'void'):
      return
    if OV.IsControl('SNUM_MAP_BUTTON'):
      # set electron density map button to 'up' state
      olx.html.SetState('SNUM_MAP_BUTTON','up')
      olx.html.SetLabel('SNUM_MAP_BUTTON',OV.Translate('Calculate'))

    resolution = OV.GetParam("snum.calcvoid.resolution")
    distance = OV.GetParam("snum.calcvoid.distance")
    precise = OV.GetParam("snum.calcvoid.precise")
    self.SetXgridView(False)
    cmd = "calcVoid -r=%s -d=%s" %(resolution, distance)
    if precise:
      cmd += " -p"

    self.void_html = ""
    voidfile = '%s/voids.txt' %OV.DataDir()
    self.map_type = 'void'
    self.SetXgridView(True)
    self.deal_with_controls()
    OV.SetVar('olex2.map_type', 'void')
    olex.m(cmd)

  def void_observer(self, msg):
    try:
      if "penetrated" in msg:
        print("@@@@@@@@@@@@@@@@@@@@@@@@@")
        self.void_html += msg
    except:
      pass

  def MaskView(self, onoff=None):
    img_bases = ['small-Mask']
    if self.deal_with_map_buttons(onoff, img_bases, 'mask'):
      self.SetXgridView(True)
      return
    self.SetXgridView(False)
    self.map_type = 'mask'
    OV.SetVar('olex2.map_type', 'mask')
    self.deal_with_controls()
    olex.m('spy.OlexCctbxMasks(True, True)')

  def MapView(self, onoff=None):
    img_bases = ['full-Electron_Density_Map', 'small-Map']
    if self.deal_with_map_buttons(onoff, img_bases, 'eden'):
      self.SetXgridView(True)
      return
    update_controls = True
    if OV.IsControl('SNUM_CALCVOID_BUTTON'):
      # set calcvoid button to 'up' state
      olx.html.SetState('SNUM_CALCVOID_BUTTON','up')
      olx.html.SetLabel('SNUM_CALCVOID_BUTTON',OV.Translate('Calculate Voids'))

    map_type =  OV.GetParam("snum.map.type")
    map_source = OV.GetParam("snum.map.source")
    map_resolution = OV.GetParam("snum.map.resolution")
    mask = OV.GetParam("snum.map.mask")
    scale = OV.GetParam("snum.map.scale")

    if map_type == "fcalc":
      map_type = "calc"
    elif map_type == "fobs":
      map_type = "obs"

    if mask:
      mask_val = "-m=%s" %(OV.GetParam("snum.map.mask_d", 1.0))
    else:
      mask_val = ""
    cf_cmd = "CalcFourier -%s -r=%s %s -scale=%s" % (map_type, map_resolution, mask_val, scale)
    if map_type == "PDF":
      second = OV.GetParam('snum.map.PDF_second_order')
      third = OV.GetParam('snum.map.PDF_third_order')
      fourth = OV.GetParam('snum.map.PDF_fourth_order')
      olex.m("spy.NoSpherA2.PDF_map(%s,%f,%d,%d,%d)" % (map_resolution, 1.0, second, third, fourth))
    else:
      self.map_type = 'eden'
      OV.SetVar('olex2.map_type', 'eden')

      NoSpherA2 = OV.IsNoSpherA2()
      if map_source == "fcf":
        olex.m(cf_cmd + " -fcf")
      elif map_source == "olex":
        if NoSpherA2 == True:
          print("NoSpherA2 maps only possible with .fcf or cctbx")
          print("WARNING: Switching to cctbx maps!")
          OV.SetParam("snum.map.source", "cctbx")
          olex.m("spy.NoSpherA2.show_fft_map(%s,%s)" % (map_resolution, map_type))
        else:
          olex.m(cf_cmd)
      else:
        if OV.GetParam("snum.refinement.program") == "olex2.refine":
          olex.m("spy.NoSpherA2.show_fft_map(%s,%s)" % (map_resolution, map_type))
        else:
          olex.m(cf_cmd)

    self.SetXgridView(update_controls)


  def SetXgridView(self, update_controls=False):
    update_controls = bool(update_controls)
    view = OV.GetParam("snum.xgrid.view")
    extended = OV.GetParam("snum.xgrid.extended")
    if view == "2D":
      olex.m("xgrid.RenderMode(plane)")
    elif view == "surface":
      olex.m("xgrid.RenderMode(fill)")
    elif view == "wire":
      olex.m("xgrid.RenderMode(line)")
    elif view == "points":
      olex.m("xgrid.RenderMode(point)")
    else:
      view += " " + OV.GetParam("snum.xgrid.heat_colours","")
      olex.m("xgrid.RenderMode %s" %view)
    olex.m("xgrid.Extended(%s)" %extended)
    try:
      _ = olx.GetVar('map_slider_scale')
    except:
      _ = None
    if update_controls in (True, 'true') or not _:

      self.deal_with_controls()
      olx.html.Update()

  def Round(self, value, digits):
    value = float(value)
    e = "%%.%sf" %digits
    return e%value


  def get_best_contour_maps(self):
    maximum = float(olx.xgrid.GetMax())
    minimum = float(olx.xgrid.GetMin())
    contours = OV.GetParam('snum.xgrid.contours') - 1

    map_maximum = round(maximum*10,0)/10
    map_minimum = round(minimum*10,0)/10

    if debug:
      print("Map Maximum = %s (%s)" %(map_maximum, maximum))
      print("Map Minimum = %s (%s)" %(map_minimum, minimum))


    if maximum > 0 and minimum < 0:
      difference = abs(maximum) + abs(minimum)
    else:
      difference = abs(maximum - minimum)

    step = round((difference/contours) * 100, 0)/100
    if debug:
      print("Map Step = %s" %(step))

    OV.SetParam('snum.xgrid.step',step)
    OV.SetParam('snum.xgrid.fix',map_minimum)

    slider_scale = int(50/difference)
    OV.SetParam('snum.xgrid.slider_scale',slider_scale)

    #if difference < 1:
      #OV.SetParam('snum.xgrid.slider_scale',20)
    #elif difference < 2:
      #OV.SetParam('snum.xgrid.slider_scale',10)
    #elif difference < 5:
      #OV.SetParam('snum.xgrid.slider_scale',5)

    olx.xgrid.Fix(map_minimum, step)
    olx.html.Update()

  def getActionString(self, what="Map", control=""):
    control = control.strip("'")
    if olx.xgrid.Visible() == "false":
      retVal =  "Show %s" %what
    else:
      retVal = "Hide %s" %what

    if control:
      if OV.IsControl(control):
        olx.html.SetLabel(control, retVal)

    return retVal

  def get_map_scale(self):
    SCALED_TO = 50

    olx.SetVar('map_slider_scale', 10)
    olx.SetVar('map_min',1)
    olx.SetVar('map_max',0)
    olx.SetVar('map_value',0)
    self.value = 0
    self.scale = 0
    map_type = None
    try:
      map_type = self.map_type
    except AttributeError:
      map_type = None
    if olx.xgrid.Visible() == "false":
      return

    val_min = float(olx.xgrid.GetMin())  #* -1
    val_max = float(olx.xgrid.GetMax())  # * -1

    if abs(val_min) > abs(val_max):
      difference = val_min
      val_min = val_max
    else:
      difference = val_max

    slider_scale = int(SCALED_TO/difference)
    olx.SetVar('map_slider_scale', slider_scale)
    self.scale = slider_scale

    map_max = int(round((val_min * slider_scale * 0.1),0)) * 10
    map_max = int(round(difference * slider_scale))

    if map_type == 'eden':
      map_min = abs(int(round(val_min / 5 * slider_scale)))
    else:
      map_min = 0

    olx.SetVar('map_max',map_max)
    olx.SetVar('map_min',map_min)

    map_value = int(round(float(olx.xgrid.Scale()) * slider_scale))
    self.value = map_value

    print("slider_scale: %s" %slider_scale)
    print("map_min: %s" %map_min)
    print("map_max: %s" %map_max)
    print("map_value: %s" %map_value)

    s = abs(slider_scale)
    if 0 <= s < 15:
      slider_scale = 10
    elif  15 <= s < 25:
      slider_scale = 20
    elif 25 <= s < 75:
      slider_scale = 50
    elif 75 <= s < 125:
      slider_scale = 100
    elif 125 <= s < 175:
      slider_scale = 150
    elif 175 <= s < 225:
      slider_scale = 200
    elif 225 <= s < 275:
      slider_scale = 250
    elif 275 <= s < 325:
      slider_scale = 300

    olx.SetVar('map_slider_scale', slider_scale* -1)

    _ = round(float(olx.xgrid.Scale()),3)
    OV.SetParam('snum.xgrid.scale', _)
    olx.SetVar('snum.xgrid.scale', _)
    olx.SetVar('map_value', olx.xgrid.Scale())

if OV.HasGUI():
  mu = MapUtil()
  OV.registerFunction(mu.VoidView, False, "gui.maps")
  OV.registerFunction(mu.SetXgridView, False, "gui.maps")
  OV.registerFunction(mu.MapView, False, "gui.maps")
  OV.registerFunction(mu.MaskView, False, "gui.maps")
  OV.registerFunction(mu.Round, False, "gui.maps")
  OV.registerFunction(mu.get_best_contour_maps, False, "gui.maps")
  OV.registerFunction(mu.get_map_scale, False, "gui.maps")
  OV.registerFunction(mu.getActionString, False, "gui.maps")
