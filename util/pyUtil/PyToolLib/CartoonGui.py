"""The polymer row in Quick Drawing Styles: buttons, icons and the colour list.

A protein needs two independent display decisions - how the backbone is drawn
and how everything else is - and Olex2 only had controls for the second. The
buttons here make the first one, and because the cartoon hides the atoms it
draws, the wireframe/ellipsoid/packing controls above then apply to what is
left: the ligands, sugars, metals and waters.

The icons are drawn rather than cropped from the icon sheet. Every other
toolbar icon comes out of one 640x640 image of 64x64 cells
(etc/gui/images/src/icons.png, read by PilTools.make_icon_items), so a new one
normally means editing a binary file in a versioned tree that nobody can review
in a diff. Drawing them keeps the picture next to the code that decides what it
means, and lets them follow the skin's icon size and highlight colour.

The palette is the one every structure viewer uses: helices red, strands
yellow, coil and plain trace grey-blue. That is what makes the buttons
self-explaining - the picture already means something to anyone who has seen a
protein drawn before.
"""
import math

import olex
import OlexVFS
from olexFunctions import OV

from PIL import Image, ImageDraw


# supersampling: everything is drawn this many times larger and resized down,
# which is the whole of the anti-aliasing
_SS = 4
_CELL = 64

_HELIX = (200, 50, 45)
_HELIX_DARK = (140, 30, 26)
_STRAND = (232, 183, 58)
_STRAND_DARK = (168, 128, 30)
_COIL = (120, 138, 155)
_COIL_DARK = (78, 92, 106)
_LIGAND = (60, 60, 62)
_LIGAND_O = (214, 62, 48)
_LIGAND_N = (58, 96, 190)

# name, phil value, macro, hint
STYLES = (
  ('trace', 'trace', 'cartoon on -r=trace -n=hide',
   'Ribbon only: a plain tube along the backbone, nothing else drawn'),
  ('cartoon', 'cartoon', 'cartoon on -r=cartoon -n=hide',
   'Cartoon: helix ribbons and strand arrows, nothing else drawn'),
  ('ligands', 'cartoon+ligands', 'cartoon on -r=cartoon -n=nowater',
   'Cartoon with the ligands, sugars and metals drawn as atoms'),
  ('off', 'off', 'cartoon off',
   'No cartoon: atoms and bonds, the way Olex2 draws everything else'),
)

# The colour and sidechain lists live in snippet-cartoon-styles.htm, in the
# combo's own 'Display<-value' notation, so there is one copy of them.


#-----------------------------------------------------------------------------
# Drawing
#-----------------------------------------------------------------------------
def _band(draw, pts, half, fill, outline):
  """A ribbon of half-width `half` about the centre line `pts`.

  The edges are offset along the normal rather than vertically, so a steep
  part of the curve does not come out thinner than a flat one - which is the
  difference between a ribbon and a smear.
  """
  top, bottom = [], []
  for i in range(len(pts)):
    x, y = pts[i]
    j = min(i + 1, len(pts) - 1)
    k = max(i - 1, 0)
    dx = pts[j][0] - pts[k][0]
    dy = pts[j][1] - pts[k][1]
    n = math.hypot(dx, dy) or 1.0
    nx, ny = -dy/n, dx/n
    top.append((x + nx*half, y + ny*half))
    bottom.append((x - nx*half, y - ny*half))
  poly = top + bottom[::-1]
  draw.polygon(poly, fill=fill)
  draw.line(poly + [poly[0]], fill=outline, width=_SS)


def _sine(x0, x1, yc, amp, turns, n=80):
  return [(x0 + (x1 - x0)*t/n, yc + amp*math.sin(2*math.pi*turns*t/n))
          for t in range(n + 1)]


def _helix(draw, x0, x1, yc, amp, turns, half, n=160):
  """A helix, side on, as a coil actually going round an axis.

  Projected from three dimensions rather than drawn as a wave: the coil is cut
  into short pieces, each shaded by its depth, and they are drawn far to near
  so the front of a turn covers the back of it. A flat wave, however it is
  shaded, reads as a snake - which is the glyph for the plain trace, and the
  two have to be told apart at 25 pixels.
  """
  pts, depth = [], []
  for i in range(n + 1):
    t = i/float(n)
    a = 2*math.pi*turns*t
    pts.append((x0 + (x1 - x0)*t, yc - amp*math.cos(a)))
    depth.append(math.sin(a))
  pieces, step = [], 4
  for i in range(0, n, step):
    seg = pts[i:i + step + 2]
    if len(seg) < 2:
      continue
    pieces.append((sum(depth[i:i + step + 1])/float(step + 1), seg))
  pieces.sort(key=lambda p: p[0])
  for z, seg in pieces:
    f = (z + 1)*0.5                     # 0 at the back, 1 at the front
    c = tuple(int(_HELIX_DARK[j] + (_HELIX[j] - _HELIX_DARK[j])*f)
              for j in range(3))
    _band(draw, seg, half, c, c)


def _arrow(draw, x0, x1, yc, w):
  """A strand: a flat band with a wide head, pointing right."""
  head = (x1 - x0)*0.42
  body = x1 - head
  draw.polygon([(x0, yc - w*0.5), (body, yc - w*0.5), (body, yc - w),
                (x1, yc), (body, yc + w), (body, yc + w*0.5),
                (x0, yc + w*0.5)],
               fill=_STRAND, outline=_STRAND_DARK)


def _sticks(draw, cx, cy, r):
  """A ball-and-stick fragment, for what the ribbon does not draw."""
  arms = ((-1.0, 0.25, _LIGAND_O), (0.15, -1.0, _LIGAND_N), (1.0, 0.35, _LIGAND))
  for dx, dy, c in arms:
    draw.line([(cx, cy), (cx + dx*r, cy + dy*r)], fill=_LIGAND,
              width=int(r*0.30))
  for dx, dy, c in arms:
    bx, by = cx + dx*r, cy + dy*r
    draw.ellipse([bx - r*0.30, by - r*0.30, bx + r*0.30, by + r*0.30],
                 fill=c, outline=(30, 30, 30))
  draw.ellipse([cx - r*0.26, cy - r*0.26, cx + r*0.26, cy + r*0.26],
               fill=_LIGAND, outline=(30, 30, 30))


def glyph(kind):
  """One 64x64 RGBA cell, transparent outside the drawing."""
  n = _CELL*_SS
  im = Image.new('RGBA', (n, n), (0, 0, 0, 0))
  d = ImageDraw.Draw(im)
  u = n/64.0                            # one cell pixel

  if kind == 'trace':
    _band(d, _sine(5*u, 59*u, 32*u, 13*u, 2.0), 3.4*u, _COIL, _COIL_DARK)
  elif kind == 'cartoon':
    # coil in, helix, coil, strand arrow out - the whole vocabulary in one cell
    _band(d, [(2*u, 32*u), (11*u, 32*u)], 2.0*u, _COIL, _COIL_DARK)
    _helix(d, 8*u, 34*u, 32*u, 12*u, 2.5, 3.4*u)
    _band(d, [(32*u, 32*u), (41*u, 32*u)], 2.0*u, _COIL, _COIL_DARK)
    _arrow(d, 37*u, 61*u, 32*u, 9*u)
  elif kind == 'ligands':
    # the same, made room for the thing the ribbon does not draw
    _band(d, [(1*u, 20*u), (7*u, 20*u)], 1.8*u, _COIL, _COIL_DARK)
    _helix(d, 5*u, 27*u, 20*u, 10*u, 2.5, 2.9*u)
    _band(d, [(26*u, 20*u), (32*u, 20*u)], 1.8*u, _COIL, _COIL_DARK)
    _arrow(d, 29*u, 55*u, 20*u, 7.5*u)
    _sticks(d, 41*u, 46*u, 13*u)
  elif kind == 'off':
    _sticks(d, 32*u, 32*u, 20*u)
  else:
    raise ValueError(kind)

  return im.resize((_CELL, _CELL), Image.LANCZOS)


#-----------------------------------------------------------------------------
# The images the button html asks for
#-----------------------------------------------------------------------------
# what the icons in the file system were last drawn for, so a skin change
# redraws them and nothing else does
_drawn_for = [None]


def _icon_name(kind, state):
  return 'toolbar-cartoon-%s%s.png' % (kind, state)


def _make_icon(kind, state, icon_size, params):
  """The glyph finished the way PilTools.icon_items finishes a sprite cell.

  Same 5% strip off the top and bottom, same resize, same border in the state
  colour - otherwise this row sits at a different height from the one above it
  and the skin stops looking like one thing.
  """
  im = glyph(kind)
  strip = int(_CELL*0.05)
  im = im.crop((0, strip, _CELL, _CELL - strip))
  h = int(icon_size*(_CELL - 2*strip)/float(_CELL))
  im = im.resize((icon_size, h), Image.LANCZOS)
  if state in ('on', 'hover', 'hoveron', 'highlight'):
    outline = params.html.highlight_colour.rgb
  else:
    outline = params.skin.icon_border_colour.rgb
  d = ImageDraw.Draw(im)
  d.rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), outline=outline)
  return im


def make_icons(force=False):
  """Draws every state of every button, when the skin has changed.

  Keyed on the icon size and the two colours the states are drawn in: those
  are all a skin can change here, and redrawing twelve images on every refresh
  of the View tab would be paid for on every click in it.
  """
  params = OV.GuiParams()
  icon_size = int(OV.GetParam('gui.skin.icon_size'))
  key = (icon_size, str(params.html.highlight_colour.rgb),
         str(params.skin.icon_border_colour.rgb))
  if not force and _drawn_for[0] == key:
    return
  for kind, phil_value, cmds, hint in STYLES:
    for state in ('on', 'off', 'hover', '', 'hoveron', 'highlight'):
      OlexVFS.save_image_to_olex(
        _make_icon(kind, state, icon_size, params), _icon_name(kind, state), 2)
  _drawn_for[0] = key


#-----------------------------------------------------------------------------
# The row
#-----------------------------------------------------------------------------
def button(kind):
  """One image button, in the form MakeHoverButtonOff produces.

  Not through MakeHoverButton itself: that regenerates a missing image by
  looking the name up in the sprite index, where these are not and cannot be.
  """
  make_icons()
  for k, phil_value, cmds, hint in STYLES:
    if k != kind:
      continue
    on = OV.GetParam('user.cartoon.representation') == _representation(k) and \
      OV.GetParam('user.cartoon.non_protein') == _non_protein(k)
    img = 'toolbar-cartoon-%s' % k
    # $GetVar is left for the html preprocessor, which evaluates what a $spy
    # call returns as well as what is written in the file
    return '''
<font size='$GetVar(HtmlFontSizeControls)'>
<input
  name="IMG_CARTOON_%(K)s"
  type="button"
  image="up=%(img)s%(up)s.png,down=%(img)soff.png,hover=%(img)shover.png"
  hint="%(hint)s"
  onclick="spy.cartoon.set_style('%(k)s')>>html.Update()"
  bgcolor="%(bg)s"
>
</font>
''' % {'K': k.upper(), 'k': k, 'img': img,
       'up': 'on' if on else 'off',
       'hint': hint,
       'bg': OV.GetParam('gui.html.HtmlTableGroupBgColour')}
  raise ValueError(kind)


def _representation(kind):
  return 'off' if kind == 'off' else ('trace' if kind == 'trace' else 'cartoon')


def _non_protein(kind):
  return 'nowater' if kind == 'ligands' else 'show' if kind == 'off' else 'hide'


def set_style(kind):
  """A button: record the choice, then make the display match it."""
  OV.SetParam('user.cartoon.representation', _representation(kind))
  OV.SetParam('user.cartoon.non_protein', _non_protein(kind))
  for k, phil_value, cmds, hint in STYLES:
    if k == kind:
      olex.m(cmds)
      return
  raise ValueError(kind)


def set_colour(mode):
  OV.SetParam('user.cartoon.colour', mode)
  olex.m('cartoon -c=%s' % mode)


def set_sidechains(mode):
  OV.SetParam('user.cartoon.sidechains', mode)
  olex.m('cartoon -sc=%s' % mode)


def cartoon_is_on():
  return OV.GetParam('user.cartoon.representation') != 'off'


def cartoon_is_off():
  # the controls that only mean something with a ribbon up are disabled on
  # this, and a snippet's disabled= takes a call, not an expression
  return not cartoon_is_on()


def apply_stored():
  """Puts the stored choices onto a structure that has just been traced.

  The renderer decides for itself whether to draw a cartoon - above a residue
  count it does, which is what makes a protein usable on the first look - but
  it has no idea which representation and colour this user settled on. Without
  this the row's highlighted button and the display disagree until something
  is clicked.

  Every phil default here is the value the renderer already holds, so a user
  who has changed nothing gets no rebuild: each setter returns early when the
  value is the one it has.
  """
  try:
    if not cartoon_is_on():
      olex.m('cartoon off')
      return
    olex.m('cartoon on -r=%s -n=%s -c=%s -sc=%s'
           % (OV.GetParam('user.cartoon.representation'),
              OV.GetParam('user.cartoon.non_protein'),
              OV.GetParam('user.cartoon.colour'),
              OV.GetParam('user.cartoon.sidechains')))
  except Exception as e:
    print('CartoonGui.apply_stored: %s' % str(e))


olex.registerFunction(button, False, 'cartoon')
olex.registerFunction(set_style, False, 'cartoon')
olex.registerFunction(set_colour, False, 'cartoon')
olex.registerFunction(set_sidechains, False, 'cartoon')
olex.registerFunction(cartoon_is_on, False, 'cartoon')
olex.registerFunction(cartoon_is_off, False, 'cartoon')
olex.registerFunction(apply_stored, False, 'cartoon')
olex.registerFunction(make_icons, False, 'cartoon')
