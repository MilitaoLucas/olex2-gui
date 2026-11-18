"""The background of the 3D view, as part of a theme.

Olex2 draws the background in one of three ways:

  plain     one colour (gl.lm.ClearColor).  A scene (.glsp) brings one, and so
            does the skin (gui.skin.clearcolor, set when a skin loads).
  gradient  four corner colours ('grad c1 c2 c3 c4', then 'grad true')
  picture   an image stretched over the view ('grad -p=<file>'); best with
            power-of-2 sides, such as 512x256

F2 (swapbg) swaps between white and the colour, F4 ('grad -i') between the
gradient and the plain colour: both keep working with whatever is set here.

Olex2 keeps the gradient and picture in its own settings, not in the scene, so
a theme records them here (overlay.py, key 'background'):

  {'mode': 'plain'|'gradient'|'picture',
   'colour': '#rrggbb' or None (None: the scene's own colour),
   'gradient': ['#rrggbb'] * 4 or None, in the order of Olex2's gradient
               dialog: bottom left, bottom right, top right, top left,
   'picture': a file path or None}

Kept free of other theme imports except overlay: it may run while Olex2 starts.
"""
import os
import sys

from . import overlay

MODES = ('plain', 'gradient', 'picture')
CORNERS = ('Bottom left', 'Bottom right', 'Top right', 'Top left')


def _report(what, err):
  print("Theme: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def to_int(colour):
  """'#rrggbb' -> the integer Olex2 uses for GL colours (red in the low byte)."""
  c = colour.lstrip('#')
  r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
  return r | (g << 8) | (b << 16)


def to_hex(value):
  """An Olex2 GL colour integer (alpha in the top byte is ignored) -> '#rrggbb'."""
  v = int(value)
  return '#%02x%02x%02x' % (v & 255, (v >> 8) & 255, (v >> 16) & 255)


def settings():
  """The recorded settings with every key present."""
  s = {'mode': 'plain', 'colour': None, 'gradient': None, 'picture': None}
  s.update(overlay.background())
  if s['mode'] not in MODES:
    s['mode'] = 'plain'
  return s


def current_colour():
  """The plain background colour now on screen, '#rrggbb', or None."""
  import olx
  try:
    return to_hex(olx.gl.lm.ClearColor())
  except (ValueError, TypeError, AttributeError) as err:
    _report("read the background colour", err)
    return None


def apply(s=None, base_dir=None):
  """Show the background settings s (default: the recorded ones).  A relative
  picture path is taken from base_dir (a theme's folder)."""
  import olex
  s = s or settings()
  if s.get('colour'):
    olex.m('gl.lm.ClearColor(%d)' % to_int(s['colour']))
  mode = s.get('mode', 'plain')
  corners = s.get('gradient')
  if corners and len(corners) == 4:
    olex.m('grad %s' % ' '.join(str(to_int(c)) for c in corners))
  picture = s.get('picture')
  if picture and base_dir and not os.path.isabs(picture):
    picture = os.path.join(base_dir, picture)
  if mode == 'picture' and picture:
    if os.path.isfile(picture):
      olex.m('grad -p="%s"' % picture)
      olex.m('grad true')
      return
    print("Background picture not found: %s" % picture)
  # '-p' without a file removes a picture an earlier theme left (untested in Olex2)
  olex.m('grad -p')
  olex.m('grad %s' % ('true' if mode == 'gradient' and corners else 'false'))


def update(**changes):
  """Change some settings, keep them and show the result."""
  s = settings()
  s.update(changes)
  overlay.set_background(s)
  apply(s)
  # text colours of the 3D view may differ on a light background
  from . import glcolours
  glcolours.apply(restore=True)
  return s


def forget_colour():
  """A new scene brings its own colour: stop laying ours over it."""
  s = settings()
  if s.get('colour'):
    s['colour'] = None
    overlay.set_background(s)
