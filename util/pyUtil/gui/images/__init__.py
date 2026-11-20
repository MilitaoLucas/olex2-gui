import olex
import olx
from olexFunctions import OV

import inspect, os
curr_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

class GuiImages:

  def __init__(self):
    if olx.HasGUI() != 'true':
      return

    # the images are action-<which>_<state>.png in the VFS, made by PilTools from
    # the current icon set (gui.GuiImages.action still names the classic folder)
    height = OV.GetParam('gui.html.input_height')
    self.img_d = {
      'width':height,
      'height':height,
      'bg':OV.GetParam('gui.html.table_bg_colour').hexadecimal,
    }

  def make_action_button_html(self):
    link = '''
      <input
        type="button"
        image="up=action-%(which)s_off.png,down=action-%(which)s_on.png,hover=action-%(which)s_hover.png"
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
OV.registerFunction(GI.make_action_button_html,False,'gui.images')
OV.registerFunction(GI.get_action_button_html,False,'gui.images')


##Moved from olexex: Anything to do with structure image generation
def GetBitmapSize(px_changed=False):
  resolution = OV.GetParam('user.image.bitmap.resolution')
  try:
    resolution = float(resolution)
  except:
    return False, False
  width = OV.GetParam('user.image.bitmap.resolution_width')
  try:
    width = float(width)
  except:
    return False, False
  unit = OV.GetParam('user.image.bitmap.resolution_unit')
  size = OV.GetParam('user.image.bitmap.size')
  try:
    size = float(size)
  except:
    return False, False
  factor = 1
  if unit == "cm":
    factor = 0.393700787
  if px_changed:
    width = size/(resolution * factor)
    OV.SetControlValue('IMAGE_BITMAP_width',round(width,3))
    OV.SetParam('user.image.bitmap.resolution_width',round(width,3))
  else:
    size = resolution * width * factor
    OV.SetControlValue('IMAGE_BITMAP_SIZE',int(round(size,0)))
    OV.SetParam('user.image.bitmap.size',int(round(size,0)))
  return int(round(resolution,0)), int(round(size,0))
OV.registerFunction(GetBitmapSize,False,'gui.images')


def has_alpha(fileext):
  """Whether images of this type can be transparent."""
  return str(fileext or '').lower().split('/')[0] in ('png', 'tif', 'tiff')


def _save_model_beside(image_file):
  """The model (.oxm: atoms, view, labels) next to the image, so the image
  can be made again after small changes ('reap <file>.oxm')."""
  path = os.path.splitext(image_file.strip("'").strip('"'))[0]
  if not os.path.isabs(path):
    path = os.path.join(OV.FilePath(), path)
  try:
    olex.m('save model "%s.oxm"' % path.replace(os.sep, '/'))
  except Exception as err:
    print("Image: the model was not saved next to it: %s" % err)


def _pict(command, path, plan=None):
  """Run a pict command; with user.image.labels.smart the atom labels are
  placed and drawn by gui.images.labels instead of Olex2 (plan: placed
  already, see _make_trimmed)."""
  if OV.GetParam('user.image.labels.mode', 'normal') == 'vector':
    # labels drawn in a real font where they are on screen (gui.images.labelmode)
    from . import labelmode
    labelmode.render(command, path)
  elif OV.GetParam('user.image.labels.smart', False):
    from . import labels
    labels.render(command, path, plan)
  else:
    olex.m(command)


def _make_trimmed(pict, nbg, filefull, resolution, target_width):
  """The image trimmed to the structure, from where its atoms are on screen
  (gui.images.screenbox): one rendering at the size that makes the structure
  target_width wide with its padding and border, then a crop.  No pixels are
  compared, so a gradient, a picture or a transparent background trims like a
  plain one.  False if the structure's box cannot be had."""
  import sys
  from . import labelmode, labels, screenbox
  try:
    window = screenbox.window_size()
    view = screenbox.basis()
    model = labels.current_model()
    # every atom drawn (grown copies too, hidden ones not), with perspective
    atoms = screenbox.drawn_atoms(model) or screenbox.atoms_with_reach()
    atom_box = screenbox.screen_box(atoms, view, window,
                                    angle=screenbox.perspective_angle())
    if not atom_box or atom_box[2] <= atom_box[0]:
      print("Trim: no atoms on screen; trimming by the background colour")
      return False
    # the legend and the labels belong to the picture too
    elements = set(screenbox.element_of(a[0]) for a in atoms) - {''}
    legend = screenbox.legend_box(model, len(elements))
    label_boxes = labelmode.label_boxes_px(model)
    box = screenbox.union(atom_box, legend, *label_boxes)
  except Exception as err:  # any failure: fall back to the trim by colour, say why
    import traceback
    print("Trim: could not work out the picture's box (%s: %s); trimming by the "
          "background colour" % (type(err).__name__, err))
    traceback.print_exc()
    if hasattr(sys, '_wing_debugger'):
      raise
    return False
  print("Trim: %d atoms -> %.0f x %.0f px; legend %s; %d labels -> %.0f x %.0f px "
        "(window %d x %d, perspective %s)"
        % (len(atoms), atom_box[2] - atom_box[0], atom_box[3] - atom_box[1],
           'at %.0f,%.0f' % legend[:2] if legend else 'hidden', len(label_boxes),
           box[2] - box[0], box[3] - box[1], window[0], window[1],
           screenbox.perspective_angle() or 'off'))
  plan = None
  padding = float(OV.GetParam('user.image.bitmap.trim_padding', 1))
  border = float(OV.GetParam('user.image.bitmap.trim_border', 1))
  # the panel sets user.image.trim_border_colour; bitmap.* is the declared one
  border_col = (OV.GetParam('user.image.trim_border_colour') or
                OV.GetParam('user.image.bitmap.trim_border_colour'))
  if not border_col or str(border_col) == 'None':
    border_col = '#ababab'
  width = screenbox.render_width(box, window[0], target_width, padding, border)
  # 'picta' takes a scale of the screen, 'pict' a width in pixels
  size = round(width / float(window[0]), 4) if pict.strip() == 'a' else int(round(width))
  filefull = filefull.strip("'").strip('"')
  _pict('pict%s %s "%s" %s %s' % (pict, nbg, filefull, resolution, size), filefull, plan)
  if not os.path.exists(filefull):
    print("Trim: no image was written to %s" % filefull)
    return True
  screenbox.trim_rendered(filefull, box, window, target_width, padding, border, border_col)
  return True


def MakeBitmapImage(notify_listener=True, output_folder=None):
  from ImageTools import IT
  filefull, filename, fileext = GetImageFilename(image_type = "BITMAP")
  if not filefull:
    if output_folder:
      name = OV.HKLSrc()
      _ = os.path.join(output_folder, "%s.%s" %(name, fileext))
      filefull = _
  if not filefull:
    return
  resolution, filesize = GetBitmapSize()
  if not filesize:
    return
  resolution = "-dpi=%s" %resolution
  if has_alpha(fileext) and OV.GetParam('user.image.bitmap.transparent_background'):
    nbg = "-nbg"
  else:
    # a jpg or bmp cannot be transparent: it keeps the real background
    # (colour, gradient or picture) instead of coming out white
    nbg = ""
  if fileext == "png/s":
    filefull = "%s.png" %filename
    filesize = 1
    pict = "a "
  else:
    pict = " -pq"
  OV.Cursor('busy','Please Wait. Making image %s.%s. This may take some time' %(filename, fileext))

  filesize = int(round(filesize,0))

  vector = OV.GetParam('user.image.labels.mode', 'normal') == 'vector'
  if vector and OV.GetParam('user.image.bitmap.trim') and _make_trimmed(
      pict, nbg, filefull, resolution, filesize):
    # experimental vector mode: trimmed from the geometry (works on gradients)
    pass
  elif OV.GetParam('user.image.bitmap.trim'):
    # normal mode, as Olex2 always did it: an intermediate bitmap is trimmed by
    # the background colour (not for gradient or picture backgrounds)
    temp_name = '%s_temp.bmp' %(filefull.strip("'"))
    temp_name = 'temp.bmp'
    try:
      olex.m('picta "%s" 1' %(temp_name))
      new_width, old_width = IT.trim_image(im=temp_name, dry=True)
      target_size = filesize
      filesize = filesize * (old_width/new_width)
      # _pict: plain 'pict' in normal mode; draws the labels in vector mode
      _pict('pict%s %s "%s" %s %s' %(pict, nbg, filefull, resolution, int(round(filesize,0))),
            filefull.strip("'").strip('"'))
      if OV.GetParam('user.image.bitmap.transparent_background'):
        trimcolour=(255,255,255,0)
      else:
        trimcolour = None
      IT.trim_image(im=filefull, trimcolour=trimcolour, target_size=target_size)
    finally:
      if os.path.exists(temp_name):
        os.unlink(temp_name)
  else:
    _pict('pict%s %s "%s" %s %s' %(pict, nbg, filefull, resolution, filesize),
          filefull.strip("'").strip('"'))

  _save_model_beside(filefull)
  #from PIL import Image
  OV.Cursor()
  if notify_listener:
    from gui import ImageListener
    ImageListener.OnChange()
OV.registerFunction(MakeBitmapImage,False,'gui.images')

def MakePovRayImage():
  filefull, filename, fileext = GetImageFilename(image_type = "PR")
  if not filefull:
    return
  OV.Cursor('busy','Please Wait. Making image %s.%s. This may take some time' %(filename, fileext))
  olex.m('pictPR "%s"' %filefull)
  print('Image %s created' %filefull)
  OV.Cursor()
  from gui import ImageListener
  ImageListener.OnChange()
OV.registerFunction(MakePovRayImage,False,'gui.images')

def MakePostScriptImage(notify_listener=True, output_folder=None):
  filefull, filename, fileext = GetImageFilename(image_type = "PS")
  if output_folder:
    filefull = "%s/%s.%s" %(output_folder, filename, fileext)
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
  octant_atoms = '-$C'
  import olex_gui
  if olex_gui.IsControl('IMAGE_PS_OCTANTS_ATOMS'):
    octant_atoms = OV.GetControlValue('IMAGE_PS_OCTANTS_ATOMS')

  if image_perspective.lower() == 'true':
    image_perspective = "-p"

  olex.m("pictps" + \
         " '" + filefull + \
         "' " + colour_line + \
         " " + colour_bond + \
         " " + image_perspective + \
         " " + colour_fill + \
         " " + "-bond_outline_oversize=" + "20" + \
         " " + "-atom_outline_color=" + "16777215" + \
         " " + "-bond_outline_color=" + "15592941" + \
         " " + "-lw_ellipse=" + lw_ellipse + \
         " " + "-lw_octant=" + lw_octant + \
         " " + "-lw_pie=" + lw_pie + \
         " " + "-lw_font=" + lw_font + \
         " " + "-div_pie=" + div_pie + \
         " " + "-octants=" + octant_atoms + \
         " " + "-scale_hb=" + scale_hb)

  print('Image %s created' %filefull)
  OV.Cursor()
  if notify_listener:
    from gui import ImageListener
    ImageListener.OnChange()
OV.registerFunction(MakePostScriptImage,False,'gui.images')

def GetImageFilename(image_type):
  filename = OV.GetParam('snum.image.name')
  OV.SetParam('snum.image.name', None)
  if image_type == "PS":
    fileext = "eps"
  elif image_type == "PR":
    fileext = "pov"
  elif image_type == "BITMAP":
    fileext = OV.GetParam('user.image.bitmap.type')
  else:
    fileext = OV.GetParam('snum.image.%s.type' %image_type.lower())
  if not filename:
    try:
      current = int(olx.xf.CurrentData())
      filename = olx.xf.DataName(current)
    except:
      filename = OV.FileName()
    if not filename:
      import gui
      filename = gui.FileSave("Choose Filename", "*.%s" %fileext, OV.FilePath())
    if not filename:
      return None, None, None
  if_exists = OV.GetParam('user.image.if_file_exists')
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
    filefull = "%s" %filename
  else:
    filefull = "%s.%s" %(filename, fileext)
  OV.SetParam('snum.image.%s.name' %image_type.lower(),None)
  return filefull, filename, fileext


def labels_preview(path=''):
  return MakeLabelledImage(path)


def MakeLabelledImage(path=''):
  """spy.gui.images.MakeLabelledImage([file]) (Ctrl+Shift+P): the image of
  Ctrl+P, with the labels placed and drawn by Python (gui.images.labels),
  saved in the structure's folder."""
  if not path:
    try:
      name = olx.xf.DataName(int(olx.xf.CurrentData()))
    except (ValueError, RuntimeError, AttributeError):
      name = OV.FileName()
    path = os.path.join(OV.FilePath(), name)
  if path.lower().endswith(('.png', '.jpg', '.tif', '.bmp')):
    path = os.path.splitext(path)[0]
  OV.SetParam('snum.image.name', path)
  was = OV.GetParam('user.image.labels.smart', False)
  OV.SetParam('user.image.labels.smart', True)
  try:
    MakeBitmapImage()
  finally:
    OV.SetParam('user.image.labels.smart', was)
  return path


def labels_probe():
  from . import labels
  labels.probe()


OV.registerFunction(labels_preview, False, 'gui.images')
OV.registerFunction(labels_probe, False, 'gui.images')
OV.registerFunction(MakeLabelledImage, False, 'gui.images')


def label_mode(mode=''):
  from . import labelmode
  return labelmode.set_mode(mode)


def label_calibrate():
  from . import labelmode
  return labelmode.calibrate()


def label_reapply(force=''):
  """spy.gui.images.label_reapply([true]): the vector fonts again in vector
  mode (the Bitmap Images panel sets label fonts of its own); true: new sizes."""
  from . import labelmode
  labelmode.reapply(force)


OV.registerFunction(label_reapply, False, 'gui.images')


OV.registerFunction(label_mode, False, 'gui.images')
OV.registerFunction(label_calibrate, False, 'gui.images')


def perspective(angle=''):
  """spy.gui.images.perspective([angle|off]): gl.Perspective, remembered for
  the trim of vector mode (Olex2 cannot be asked whether perspective is on).
  No argument prints the angle in use.  Not kept over a restart, as in Olex2."""
  a = str(angle or '').strip().lower()
  if not a:
    v = OV.GetParam('user.image.perspective', 0) or 0
    print("Perspective: %s" % (('%g degrees' % v) if v else 'off'))
    return v
  if a in ('off', 'false', 'no', '0'):
    olex.m('gl.Perspective')
    OV.SetParam('user.image.perspective', 0)
    return 0
  try:
    v = min(180.0, max(1.0, float(a)))
  except ValueError:
    print("Perspective: give an angle (1-180 degrees) or off")
    return None
  olex.m('gl.Perspective %g' % v)
  OV.SetParam('user.image.perspective', v)
  return v


OV.registerFunction(perspective, False, 'gui.images')
