"""Flat, skinnable toolbar icons.

The icons are drawn as SVG in etc/gui/images/src/icons/ (one file per icon,
24x24 grid) using only four colour *roles*, given as CSS classes:

  ink  - the main drawing: outlines, glyphs                (f-ink / s-ink)
  acc  - the one accent that carries the meaning            (f-acc / s-acc)
  sec  - a secondary colour for a second distinct element   (f-sec / s-sec)
  mut  - a quiet fill behind outlines                       (f-mut / s-mut)

(f- = fill, s- = stroke.)  build/build_icons.py renders all of them
into one sprite, icons_flat.png, with the same 10x10 grid of 64x64 cells as the
old icons.png, painting each role in a pure key colour: ink red, acc green,
sec blue and mut black.  Because rendering is linear, every pixel of the sprite
is an exact sum of role coverages, also on anti-aliased edges, so the roles can
be pulled apart again here and painted in the colours of the current skin.
Nothing but PIL is needed at runtime.

LAYOUT is the single list of icons: name -> cell, plus optional role
overrides, e.g. {'acc': 'red'} draws the accent of 'delete' in the skin's red.
"""

from PIL import Image, ImageChops

CELL = 64
GRID = 10

ROLES = ('ink', 'acc', 'sec', 'mut')

# key colours used when building the sprite; mut is whatever is left of alpha
KEY_CSS = (
  ".f-ink{fill:#ff0000}.s-ink{stroke:#ff0000}"
  ".f-acc{fill:#00ff00}.s-acc{stroke:#00ff00}"
  ".f-sec{fill:#0000ff}.s-sec{stroke:#0000ff}"
  ".f-mut{fill:#000000}.s-mut{stroke:#000000}"
)

# name: (row, col[, role overrides])   - same cells as the old icons.png
LAYOUT = {
  'anis': (0, 0), 'isot': (0, 1), 'cell': (0, 2), 'center-on-cell': (0, 3),
  'labels': (0, 4), 'base': (0, 5), 'info': (0, 6), 'ball-and-stick': (0, 7),
  'bicoloured-bonds': (0, 8), 'wireframe': (0, 9),
  'move': (1, 0), 'weight': (1, 1), 'ms': (1, 2), 'hadd': (1, 3),
  'cif': (1, 6), 'clear': (1, 7, {'acc': 'red'}), 'default': (1, 8),
  'OH': (1, 9, {'acc': 'red'}),
  'twins': (2, 0), 'htmlpanelswap': (2, 1), 'Q': (2, 2), 'H': (2, 3),
  'C': (2, 4, {'acc': 'ink'}), 'N': (2, 5, {'acc': 'sec'}),
  'O': (2, 6, {'acc': 'red'}), 'F': (2, 7, {'acc': 'green'}), 'center': (2, 8),
  'platon': (2, 9),
  'edit': (3, 1), 'tidy': (3, 2), 'blank': (3, 3), 'sphere-packing': (3, 4),
  'open': (3, 5), 'lines': (3, 6), 'swapbg': (3, 7), 'dimas': (3, 8),
  'chn': (3, 9),
  'sp3': (4, 0), 'sp2': (4, 1), 'fvar': (4, 2), 'occ': (4, 3), 'part': (4, 4),
  'sp2_1H': (4, 5), 'sp3_1H': (4, 6), 'sp3_2H': (4, 7), 'sp3_3H': (4, 8),
  'sp2_2H': (4, 9),
  'O_H': (5, 0), 'OK': (5, 2, {'acc': 'green'}), 'olex': (5, 3),
  'cctbx': (5, 4), 'movie': (5, 5), 'image': (5, 6), 'QH': (5, 7),
  'QC': (5, 8), 'text': (5, 9),
  'delete': (6, 0, {'acc': 'red'}), 'stop': (6, 3, {'acc': 'red'}),
  'eden': (6, 4, {'acc': 'green', 'sec': 'red'}), 'editatom': (6, 5),
  'killH': (6, 6, {'acc': 'red'}),
  'home': (6, 7), 'settings': (6, 8), 'polyhedra': (6, 9),
  'dot-arrow-right': (7, 0), 'dot-arrow-left': (7, 1),
  'dot-arrow-down': (7, 2), 'dot-arrow-up': (7, 3),
  'more': (7, 4, {'acc': 'green'}), 'less': (7, 5, {'acc': 'red'}),
  'refresh': (7, 6), 'anisH': (7, 7), 'cap': (7, 8),
  'mask': (8, 5),
  # action buttons (gui.images.get_action_button_html) and the image player
  'up': (6, 1), 'down': (6, 2),
  'player-back': (9, 0), 'player-forward': (9, 1), 'player-play': (9, 2),
  'player-stop': (9, 3),
}

# icon states used for the action buttons, as role overrides
STATE_OVERRIDES = {
  'off': {},
  'hover': {'ink': 'acc', 'sec': 'acc'},
  'on': {'ink': 'acc', 'sec': 'acc', 'mut': 'acc_mut'},
}


def _rgba(colour, alpha=255):
  """'#rrggbb', (r, g, b) or (r, g, b, a) -> (r, g, b, a)"""
  if isinstance(colour, str):
    c = colour.lstrip('#')
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), alpha)
  if len(colour) == 3:
    return tuple(colour) + (alpha,)
  return tuple(colour)


def make_palette(ink, acc, sec, red=None, green=None, mut=None, mut_alpha=64):
  """Named colours an icon can be painted with.  mut is drawn at mut_alpha
  (0-255) and defaults to the ink colour: a faint ink keeps working on both
  light and dark backgrounds."""
  ink = _rgba(ink)
  acc = _rgba(acc)
  p = {
    'ink': ink,
    'acc': acc,
    'acc_mut': acc[:3] + (mut_alpha,),
    'sec': _rgba(sec),
    'mut': (_rgba(mut)[:3] if mut else ink[:3]) + (mut_alpha,),
    'red': _rgba(red or '#c0392b'),
    'green': _rgba(green or '#2e8b57'),
  }
  return p


# where each colour comes from: gui.icons.<name> first, then the skin colours
SOURCES = (
  ('ink', 'icons.ink', ('html.font_colour',)),
  ('acc', 'icons.accent', ('html.highlight_colour',)),
  ('sec', 'icons.secondary', ('action_colour', 'html.link_colour', 'blue')),
  ('mut', 'icons.muted', ()),
  ('red', 'icons.red', ('red',)),
  ('green', 'icons.green', ('green',)),
)


def _hex(v):
  v = getattr(v, 'hexadecimal', v)
  v = str(v or '').strip().strip("'\"")
  if len(v) == 7 and v.startswith('#'):
    try:
      int(v[1:], 16)
      return v.lower()
    except ValueError:
      pass
  return None


def _get(params, path):
  v = params
  for bit in path.split('.'):
    v = getattr(v, bit, None)
    if v is None:
      return None
  return v


def resolved_colours(params):
  """{role: (hex, where it came from)} for the gui params (OV.GuiParams())."""
  out = {}
  for role, own, skin in SOURCES:
    c = _hex(_get(params, own))
    if c:
      out[role] = (c, 'gui.' + own)
      continue
    for path in skin:
      c = _hex(_get(params, path))
      if c:
        out[role] = (c, 'gui.' + path)
        break
    else:
      out[role] = (None, 'ink' if role == 'mut' else 'default')
  return out


def palette_from_params(params):
  """Palette for the current skin and gui.icons settings."""
  c = dict((k, v[0]) for k, v in resolved_colours(params).items())
  opacity = _get(params, 'icons.muted_opacity')
  opacity = 25 if opacity is None else max(0, min(100, int(opacity)))
  return make_palette(ink=c['ink'] or '#262b33', acc=c['acc'] or '#c65100',
                      sec=c['sec'] or '#1069da', red=c['red'], green=c['green'],
                      mut=c['mut'], mut_alpha=int(round(opacity * 2.55)))


def role_weights(cell):
  """Split a key-coloured RGBA cell into one 'L' coverage image per role."""
  r, g, b, a = cell.convert('RGBA').split()
  rp, gp, bp = (ImageChops.multiply(x, a) for x in (r, g, b))
  k = ImageChops.subtract(ImageChops.subtract(ImageChops.subtract(a, rp), gp), bp)
  return {'ink': rp, 'acc': gp, 'sec': bp, 'mut': k}


def paint(weights, palette, overrides=None):
  """Paint role coverages with palette colours -> RGBA image."""
  overrides = overrides or {}
  size = weights['ink'].size
  acc = [Image.new('L', size, 0) for _ in range(4)]  # premultiplied r, g, b, a
  for role in ROLES:
    w = weights[role]
    if not w.getbbox():
      continue
    cr, cg, cb, ca = palette[overrides.get(role, role)]
    for i, c in enumerate((cr * ca / 255.0, cg * ca / 255.0, cb * ca / 255.0, ca)):
      f = c / 255.0
      acc[i] = ImageChops.add(acc[i], w.point(lambda v, f=f: int(v * f + 0.5)))
  return Image.merge('RGBa', acc).convert('RGBA')


class IconSheet(object):
  """The key-coloured sprite, recoloured per icon on request."""

  def __init__(self, path):
    self.sheet = Image.open(path).convert('RGBA')
    self._weights = {}

  def cell(self, name):
    row, col = LAYOUT[name][:2]
    return self.sheet.crop((col * CELL, row * CELL, (col + 1) * CELL, (row + 1) * CELL))

  def has(self, name):
    """True if the icon has been drawn (its cell is not empty)."""
    return name in LAYOUT and self.cell(name).getbbox() is not None

  def icon(self, name, palette, overrides=None):
    if name not in self._weights:
      self._weights[name] = role_weights(self.cell(name))
    spec = LAYOUT[name]
    o = dict(spec[2]) if len(spec) > 2 else {}
    o.update(overrides or {})
    return paint(self._weights[name], palette, o)
