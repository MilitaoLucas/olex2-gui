"""The file-type band under the sNum title image (top of the HTML panel).

The title itself is drawn in the skin's colours.  What kind of file is loaded
shows as a thin band of diagonal stripes along its bottom edge:

  res/ins  gui.blue      cif  gui.green      oxm  gui.orange      other  gui.grey

Electron diffraction data alternate the file-type stripes with gui.ed_fg.
Each colour can be set per skin in gui.timage.snumtitle.type_colour_<kind>;
type_band_height = 0 turns the band off.

PilTools.make_timage calls add_band() before the final resize.

user.file_type_mark chooses between this band ('stripes') and the original
look ('colour'): the whole title in a file-type colour -- cif dark green with
yellow text, oxm orange, ED ed_bg/ed_fg -- and no band.  It lives in the user
scope so that a skin change keeps it; spy.gui.theme.set_file_type_mark()
switches it.
"""
from PIL import Image, ImageDraw

from olexFunctions import OV

MARKS = ('stripes', 'colour')

# kind -> the skin colour used when type_colour_<kind> is not set
FALLBACK = {
  'ins': 'blue',
  'cif': 'green',
  'oxm': 'orange',
  'other': 'grey',
  'ed': 'ed_fg',
}


def file_kind():
  ext = (OV.FileExt() or '').lower()
  if ext in ('ins', 'res'):
    return 'ins'
  if ext in ('cif', 'oxm'):
    return ext
  return 'other'


def colour(kind):
  """The band colour for 'kind' as an (r, g, b) tuple."""
  v = OV.GetParam('gui.timage.snumtitle.type_colour_%s' % kind)
  if v is None:
    v = OV.GetParam('gui.%s' % FALLBACK[kind])
  return getattr(v, 'rgb', v)


def colours():
  """Stripe colours in drawing order: file type, then ED if ED data."""
  out = [colour(file_kind())]
  if OV.IsEDData():
    out.append(colour('ed'))
  return out


def mark():
  """'stripes' (band under a skin-coloured title) or 'colour' (title colour)."""
  m = OV.GetParam('user.file_type_mark', 'stripes')
  return m if m in MARKS else 'stripes'


def title_colours(params, grad_colour, filefullinfo_colour):
  """(grad_colour, filefullinfo_colour) for the title background and info
  text.  With the 'colour' mark the file type sets them, as Olex2 always did;
  with stripes the skin colours stay."""
  if mark() != 'colour':
    return grad_colour, filefullinfo_colour
  if OV.FileExt() == "cif":
    grad_colour = params.dark_green.rgb
  elif OV.FileFull().endswith(".oxm"):
    grad_colour = params.orange.rgb
  if OV.IsEDData():
    grad_colour = params.ed_bg.rgb
    filefullinfo_colour = params.ed_fg.rgb
  return grad_colour, filefullinfo_colour


def title_font_colour(font_colour):
  """The name of a cif data block was written in yellow on the green title."""
  if mark() == 'colour' and OV.FileFull().endswith('.cif'):
    return '#ffdf09'
  return font_colour


def redraw():
  """Draw sNumTitle.png again for the loaded file."""
  import olx
  import olex
  import OlexVFS
  if not OV.HasGUI or olx.IsFileLoaded() == 'false':
    return
  from PilTools import TI
  image = TI.make_timage('snumtitle', OV.FileName(), 'on', titleCase=False)
  OlexVFS.save_image_to_olex(image, 'sNumTitle.png', 1)
  OV.CopyVFSFile('sNumTitle.png', 'SNUMTITLE', 2)
  olex.m('html.Update')


def set_file_type_mark(name=''):
  """spy.gui.theme.set_file_type_mark([stripes|colour]): how the sNum title
  shows the file type; without an argument it toggles."""
  import olex
  if not name:
    name = 'colour' if mark() == 'stripes' else 'stripes'
  if name not in MARKS:
    print("Unknown file type mark '%s': use 'stripes' or 'colour'" % name)
    return
  OV.SetParam('user.file_type_mark', name)
  olex.m('spy.SaveUserParams()')
  redraw()
  print("File type mark: %s" % name)


def add_band(image, scale, underground):
  """Return (image with the band added below, band height in unscaled px).

  image is the title at 'scale' times its final size; the band sits on the
  panel background ('underground') and is part of the same image, so the
  HTML needs no change."""
  if mark() != 'stripes':
    return image, 0
  height = OV.GetParam('gui.timage.snumtitle.type_band_height', 4) or 0
  if height <= 0:
    return image, 0
  period = OV.GetParam('gui.timage.snumtitle.type_band_period', 8) or 8
  band = int(height * scale)
  period = max(2, int(period * scale))
  stripe = max(1, period // 2)
  w, h = image.size
  out = Image.new('RGBA', (w, h + band), underground)
  out.paste(image, (0, 0))
  draw = ImageDraw.Draw(out)
  cols = colours()
  bottom = h + band
  # stripes lean right at 45 degrees: start left of the image so the first
  # one is cut by the edge rather than missing
  for i, x in enumerate(range(-band, w + band, period)):
    draw.polygon([(x, bottom), (x + stripe, bottom),
                  (x + stripe + band, h), (x + band, h)],
                 fill=cols[i % len(cols)])
  return out, height
