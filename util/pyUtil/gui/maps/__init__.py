import olex
import olx
from olexFunctions import OlexFunctions
OV = OlexFunctions()

debug = bool(OV.GetParam("olex2.debug", False))

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
    olex.m(cmd)
    self.map_type = 'void'
    self.SetXgridView(True)
    self.deal_with_controls()
    OV.SetVar('olex2.map_type', 'void')

  def void_observer(self, msg):
    try:
      if "penetrated" in msg:
        print "@@@@@@@@@@@@@@@@@@@@@@@@@"
        self.void_html += msg
    except:
      pass

  def MaskView(self, onoff=None):
    img_bases = ['small-Mask']
    if self.deal_with_map_buttons(onoff, img_bases, 'mask'):
      return
    self.SetXgridView(False)
    olex.m('spy.OlexCctbxMasks(True, True)')
    self.deal_with_controls()
    OV.SetVar('olex2.map_type', 'mask')

  def MapView(self, onoff=None):
    img_bases = ['full-Electron_Density_Map', 'small-Map']
    if not self.deal_with_map_buttons(onoff, img_bases, 'eden'):
      update_controls = True
      if OV.IsControl('SNUM_CALCVOID_BUTTON'):
        # set calcvoid button to 'up' state
        olx.html.SetState('SNUM_CALCVOID_BUTTON','up')
        olx.html.SetLabel('SNUM_CALCVOID_BUTTON',OV.Translate('Calculate Voids'))

      map_type =  OV.GetParam("snum.map.type")
      map_source =  OV.GetParam("snum.map.source")
      map_resolution = OV.GetParam("snum.map.resolution")
      mask = OV.GetParam("snum.map.mask")

      if map_type == "fcalc":
        map_type = "calc"
      elif map_type == "fobs":
        map_type = "obs"

      if mask:
        mask_val = "-m"
      else:
        mask_val = ""

      if map_source == "olex":
        olex.m("calcFourier -%s -r=%s %s" %(map_type, map_resolution, mask_val))
      else:
        olex.m("calcFourier -%s -%s -r=%s %s" %(map_type, map_source, map_resolution, mask_val))
    else:
      update_controls = True
    self.map_type = 'eden'
    self.SetXgridView(update_controls)
    OV.SetVar('olex2.map_type', 'eden')

  def SetXgridView(self, update_controls=False):
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
    if update_controls in (True, 'true'):
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
    difference = maximum + minimum * -1

    map_maximum = round(maximum*10,0)/10
    map_minimum = round(minimum*10,0)/10

    if debug:
      print "Map Maximum = %s (%s)" %(map_maximum, maximum)
      print "Map Minimum = %s (%s)" %(map_minimum, minimum)


    if maximum > 0 and minimum < 0:
      difference = abs(maximum) + abs(minimum)
    else:
      difference = abs(maximum - minimum)

    step = round((difference/contours) * 100, 0)/100
    if debug:
      print "Map Step = %s" %(step)

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

  def get_map_scale(self):
    SCALED_TO = 50

    olx.SetVar('map_slider_scale', 10)
    olx.SetVar('map_min',1)
    olx.SetVar('map_max',0)
    olx.SetVar('map_value',0)
    self.value = 0
    self.scale = 0
    if olx.xgrid.Visible() == "false":
      return

    val_min = float(olx.xgrid.GetMin())
    val_max = float(olx.xgrid.GetMax())

    if self.map_type == 'void':
      if val_max > 0 and val_min< 0:
        difference = abs(val_max) + abs(val_min)
      else:
        difference = abs(val_max - val_min)
    elif self.map_type == 'eden':
      print "val_min: %s" %val_min
      if val_min > 0 and val_min < 0.01:
        val_min = 0.01
      if val_min > 0.01:
        val_min = -0.01
      difference = val_min * -1

    slider_scale = int(SCALED_TO/difference)
    olx.SetVar('map_slider_scale', slider_scale)
    print "slider_scale: %s" %slider_scale
    self.scale = slider_scale

    map_min =  int(round((val_min * slider_scale * 0.1),0)) * 10
    print "map_min: %s" %map_min
    olx.SetVar('map_min',map_min)

    if self.map_type == 'eden':
      map_max =  int(round((val_min/4 * slider_scale * 0.1),0)) * 10
    else:
      map_max = int(round(val_max * slider_scale))
    print "map_max: %s" %map_max
    olx.SetVar('map_max',map_max)

    map_value = int(round(float(olx.xgrid.Scale()) * slider_scale))
    self.value = map_value
    olx.SetVar('map_value', olx.xgrid.Scale())
    OV.SetParam('snum.xgrid.scale', olx.xgrid.Scale())


    #if 0 <= slider_scale < 15:
      #slider_scale = 10
    #elif  15 <= slider_scale < 25:
      #slider_scale = 20
    #elif 25 <= slider_scale < 75:
      #slider_scale = 50
    #elif 75 <= slider_scale < 125:
      #slider_scale = 100
    #elif 125 <= slider_scale < 175:
      #slider_scale = 150
    #elif 175 <= slider_scale < 225:
      #slider_scale = 200
    #elif 225 <= slider_scale < 275:
      #slider_scale = 250
    #elif 275 <= slider_scale < 325:
      #slider_scale = 300

    olx.SetVar('snum.xgrid.scale', olx.xgrid.Scale())




if OV.HasGUI():
  mu = MapUtil()
  OV.registerFunction(mu.VoidView, False, "gui.maps")
  OV.registerFunction(mu.SetXgridView, False, "gui.maps")
  OV.registerFunction(mu.MapView, False, "gui.maps")
  OV.registerFunction(mu.MaskView, False, "gui.maps")
  OV.registerFunction(mu.Round, False, "gui.maps")
  OV.registerFunction(mu.get_best_contour_maps, False, "gui.maps")
  OV.registerFunction(mu.get_map_scale, False, "gui.maps")
