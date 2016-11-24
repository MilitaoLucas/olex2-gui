import olex
import olx
from olexFunctions import OlexFunctions
OV = OlexFunctions()

class MapUtil:

  def __init__(self):
    self.scale = 50

  def deal_with_map_buttons(self, onoff, img_bases, map_type):
    ## First, set all images to hidden
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
    if OV.IsControl('SNUM_XGRID_SLIDE'):
      olx.html.SetValue('SNUM_XGRID_SLIDE', '%f,%f'
                        %(float(olx.xgrid.GetMin())*self.scale,
                          float(olx.xgrid.GetMax())*self.scale))
      olx.html.SetValue('SNUM_XGRID_SLIDE', '%f'
                        %(float(olx.xgrid.Scale())*self.scale))


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
#    olx.StartLogging(voidfile)
#    OV.registerCallback("procout", self.void_observer)
    olex.m(cmd)
#    olx.Flush()
#    olx.Stop('Logging')
#    OV.unregisterCallback("procout", self.void_observer)


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
    if self.deal_with_map_buttons(onoff, img_bases, 'eden'):
      return

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

    self.SetXgridView(False)

    if map_source == "olex":
      olex.m("calcFourier -%s -r=%s %s" %(map_type, map_resolution, mask_val))
    else:
      olex.m("calcFourier -%s -%s -r=%s %s" %(map_type, map_source, map_resolution, mask_val))

    self.deal_with_controls()
    OV.SetVar('olex2.map_type', 'eden')

  def SetXgridView(self, update_controls=True):
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

  def Round(self, value, digits):
    value = float(value)
    e = "%%.%sf" %digits
    return e%value


if OV.HasGUI():
  mu = MapUtil()
  OV.registerFunction(mu.VoidView, False, "gui.maps")
  OV.registerFunction(mu.SetXgridView, False, "gui.maps")
  OV.registerFunction(mu.MapView, False, "gui.maps")
  OV.registerFunction(mu.MaskView, False, "gui.maps")
  OV.registerFunction(mu.Round, False, "gui.maps")
