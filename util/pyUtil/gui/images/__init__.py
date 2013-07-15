from __future__ import division
import olex
import olx

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import inspect, os
curr_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

class GuiImages:

  def __init__(self):
    img_root = OV.GetParam("gui.GuiImages.action", "%s/etc/gui/images/action" %OV.BaseDir())
    height = OV.GetParam('gui.html.input_height')
    self.img_d = {
      'root':img_root,
      'width':height,
      'height':height,
      'bg':OV.GetParam('gui.html.table_bg_colour').hexadecimal,
    }

  def make_action_button_html(self):
    link = '''
      <input
        type="button"
        image="up=%(root)s/%(which)s_off.png,down=%(root)s/%(which)s_on.png,hover=%(root)s/%(which)s_hover.png"
        hint="%(hint)s"
        width="%(width)s"
        height="%(height)s"
        onclick="%(onclick)s"
        bgcolor="%(bg)s"
      >''' %self.img_d
    return link
    
  def get_action_button_html(self, which, onclick, hint):
    self.img_d['which'] = which
    self.img_d['onclick'] = onclick
    self.img_d['hint'] = hint
    return self.make_action_button_html()
  
GI = GuiImages()

##Moved from olexex: Anything to do with structure image generation
def GetBitmapSize(px_changed=False):
  resolution = OV.GetValue('IMAGE_BITMAP_RESOLUTION')
  try:
    resolution = float(resolution)
  except:
    return False, False
  width = OV.GetValue('IMAGE_BITMAP_WIDTH')
  try:
    width = float(width)
  except:
    return False, False
  unit = OV.GetValue('IMAGE_BITMAP_WIDTH_UNIT')
  size = OV.GetValue('IMAGE_BITMAP_SIZE')
  try:
    size = float(size)
  except:
    return False, False
  factor = 1
  if unit == "cm":
    factor = 0.393700787
  if px_changed:
    width = size/(resolution * factor)
    olx.html.SetValue('IMAGE_BITMAP_width',round(width,3))
  else:
    size = resolution * width * factor
    olx.html.SetValue('IMAGE_BITMAP_SIZE',int(round(size,0)))
  return int(round(resolution,0)), int(round(size,0))
OV.registerFunction(GetBitmapSize,False,'gui.images')


def GetBitmapImageInstructions():
  from ImageTools import ImageTools
  IT = ImageTools()
  filefull, filename, fileext = GetImageFilename(image_type = "BITMAP")
  if not filefull:
    return
  resolution, filesize = GetBitmapSize()
  if not filesize:
    return
  resolution = "-dpi=%s" %resolution
  if olx.html.GetState('BITMAP_NO_BG') == 'true':
    nbg = "-nbg"
  else:
    nbg = ""
  if fileext == "png/s":
    filefull = "%s.png" %filename
    filesize = 1
    pict = "a "
  else:
    pict = " -pq"
  OV.Cursor('busy','Please Wait. Making image %s.%s. This may take some time' %(filename, fileext))
  
  filesize = int(round(filesize,0))

  if olx.html.GetState('TRIM_IMAGE') == 'true':
    temp_name = '%s_temp.bmp' %(filefull.strip("'"))
    try:
      olex.m('picta "%s" 1' %(temp_name))
      padding = float(olx.html.GetValue('TRIM_PADDING'))
      border = float(olx.html.GetValue('TRIM_BORDER'))
      colour = olx.html.GetValue('TRIM_BORDER_COLOUR')
      new_width, old_width = IT.trim_image(im=temp_name,  padding=padding, border=border, border_col=colour, dry=True)
      target_size = filesize
      filesize = filesize * (old_width/new_width)
      olex.m('pict%s %s %s %s %s' %(pict, nbg, filefull, resolution, int(round(filesize,0))))
      IT.trim_image(im=filefull, padding=padding, border=border, border_col=colour, target_size=target_size)
    finally:
      if os.path.exists(temp_name):
        os.unlink(temp_name)
  else:
    olex.m('pict%s %s %s %s %s' %(pict, nbg, filefull, resolution, filesize))
    
  #import Image
  OV.Cursor()
  from gui import ImageListener
  ImageListener.OnChange()
OV.registerFunction(GetBitmapImageInstructions,False,'gui.images')

def GetPRImageInstructions():
  filefull, filename, fileext = GetImageFilename(image_type = "PR")
  if not filefull:
    return
  OV.Cursor('busy','Please Wait. Making image %s.%s. This may take some time' %(filename, fileext))
  olex.m('pictPR %s' %filefull)
  print 'Image %s created' %filefull
  OV.Cursor()
  from gui import ImageListener
  ImageListener.OnChange()
OV.registerFunction(GetPRImageInstructions,False,'gui.images')

def GetPSImageInstructions():
  filefull, filename, fileext = GetImageFilename(image_type = "PS")
  if not filefull:
    return
  OV.Cursor('busy','Please Wait. Making image %s.%s. This may take some time' %(filename, fileext))

  colour_line = OV.GetParam('snum.image.ps.colour_line')
  colour_bond = OV.GetParam('snum.image.ps.colour_bond')
  colour_fill = OV.GetParam('snum.image.ps.colour_fill')
  image_perspective = OV.GetParam('snum.image.ps.perspective')
  lw_ellipse = str(OV.GetParam('snum.image.ps.outline_width'))
  lw_octant = str(OV.GetParam('snum.image.ps.octant_width'))
  lw_pie = str(OV.GetParam('snum.image.ps.pie_width'))
  lw_font = str(OV.GetParam('snum.image.ps.font_weight'))
  div_pie = str(OV.GetParam('snum.image.ps.octant_count'))
  scale_hb = str(OV.GetParam('snum.image.ps.h_bond_width'))
  octant_atoms = str(OV.GetValue('IMAGE_PS_OCTANTS_ATOMS'))

  olex.m("pictps" + \
         " " + filefull + \
         " " + colour_line + \
         " " + colour_bond + \
         " " + colour_fill + \
         " " + "-lw_ellipse=" + lw_ellipse + \
         " " + "-lw_octant=" + lw_octant + \
         " " + "-lw_pie=" + lw_pie + \
         " " + "-lw_font=" + lw_font + \
         " " + "-div_pie=" + div_pie + \
         " " + "-octants=" + octant_atoms + \
         " " + "-scale_hb=" + scale_hb)

  print 'Image %s created' %filefull
  OV.Cursor()
  from gui import ImageListener
  ImageListener.OnChange()
OV.registerFunction(GetPSImageInstructions,False,'gui.images')

def GetImageFilename(image_type):
  filename = OV.GetParam('snum.image.name')
  if image_type == "PS":
    fileext = "eps"
  elif image_type == "PR":
    fileext = "pov"
  else:
    fileext = OV.GetParam('snum.image.%s.type' %image_type.lower())
  if not filename:
    try:
      filename = OV.GetValue('IMAGE_NAME')
    except:
      filename = None
    if not filename:
      import gui
      filename = gui.FileSave("Choose Filename", "*.%s" %fileext, OV.FilePath())
    if not filename:
      return None, None, None
  if_exists = OV.GetParam('snum.image.if_file_exists')
  if os.path.exists("%s.%s" %(filename, fileext)):
    if if_exists == 'increment':
      fp = olx.FilePath()
      fn = filename
      inc = 1
      while True:
        tf = os.path.normpath('%s/%s%d.%s' %(fp, fn, inc, fileext))
        if not os.path.exists(tf):
          filename = '%s%d' %(fn, inc)
          filefull = "'%s.%s'" %(filename, fileext)
          break
        inc += 1
    elif if_exists == 'ask':
      import gui
      filename = gui.FileSave("Choose Filename", "*.%s" %fileext, OV.FilePath(),
                              default_name=filename)
      if not filename:
        return None, None, None
  if filename.endswith(".%s" %fileext):
    filefull = "'%s'" %filename
  else:
    filefull = "'%s.%s'" %(filename, fileext)
  OV.SetParam('snum.image.%s.name' %image_type.lower(),None)
  return filefull, filename, fileext

