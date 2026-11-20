"""Atom and bond labels for saved images: placed by Python, drawn in a real font.

On screen Olex2 draws the labels itself ('label' macro, font slots AtomLabels
and BondLabels; a vector font such as @20 makes them zoom with the
structure).  When an image is saved with user.image.labels.smart, the labels
are drawn by this module:

  1. read   'save model' writes every atom and bond label: its text, whether
            it shows, where it belongs (offset: the atom, or the middle of the
            bond, Cartesian) and how far it was dragged by hand (center)
  2. place  labels moved by hand keep their place (a line along the move when
            they are far from their atom); every other label gets the free
            spot closest to its atom or bond, scored against atoms, bonds and
            the labels placed before it; a label that has to move away gets a
            thin leader line with a gap at both ends
  3. draw   Olex2's labels are hidden ('kill labels' only hides them), the
            picture is rendered (the legend in a real font, not the vector
            preview font), the labels are drawn with PIL, and Olex2's labels
            are shown again: atom labels keep where they were dragged, bond
            labels are made again and lose a drag (Olex2 has no way to keep it)

Everything is placed in Angstrom of the view (x right, y up, see
screenbox.py), so the labels have the same size relative to the structure in
every image.  Sizes come from user.image.labels.*.

How far a dragged label is from its atom: the core keeps the drag as a vector
'center' and draws it at basis zoom * center pixels (as its own label aligner
sets it); user.image.labels.shift_scale corrects that if needed.  Olex2 itself
gives new labels a small offset; drags below user.image.labels.moved_min
pixels count as not moved.
"""
import io
import math
import os
import re
import sys
import zipfile

from . import screenbox

# covalent radii (Angstrom) for the bonds that labels should avoid
COVALENT = {'H': 0.31, 'B': 0.84, 'C': 0.76, 'N': 0.71, 'O': 0.66, 'F': 0.57, 'Si': 1.11,
            'P': 1.07, 'S': 1.05, 'Cl': 1.02, 'Br': 1.20, 'I': 1.39, 'Se': 1.20}
METAL_RADIUS = 1.4
BOND_TOLERANCE = 0.45
RING_STEP = 0.45       # Angstrom between rings of candidate places
RINGS = 4              # ring 0 next to the atom, rings 1.. need a leader line
DIRECTIONS = 24
BOND_LABEL_REACH = 0.08


def _report(what, err):
  print("Labels: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def _params():
  from olexFunctions import OV
  g = lambda k, d: OV.GetParam('user.image.labels.%s' % k, d)
  num = lambda k, d: float(g(k, d) if g(k, d) is not None else d)
  return {'height': num('height', 0.26), 'bond_scale': num('bond_scale', 0.75),
          'font': str(g('font', '') or ''),
          'colour': str(g('colour', '') or ''), 'gap': num('gap', 0.12),
          'leader_width': num('leader_width', 0.025), 'shift_scale': num('shift_scale', 1.0),
          'leader_after': num('leader_after', 0.15), 'moved_min': num('moved_min', 3.0),
          'legend_size': num('legend_size', 0), 'bonds': bool(g('bonds', True))}


VECTOR_REFERENCE = 20.0  # user.image.labels.height is for this vector font size


def screen_font_scale():
  """How big the labels are on screen, relative to the vector font @20: the
  image labels follow it (@15 -> 0.75).  1 for other fonts."""
  try:
    import olx
    font = olx.GetFont('AtomLabels') or ''
  except Exception as err:
    _report("read the label font", err)
    return 1.0
  if not font.startswith('@'):
    return 1.0
  size = font[1:]
  return (float(size) if size.replace('.', '', 1).isdigit() else 15.0) / VECTOR_REFERENCE


# --- 1. reading the labels ---------------------------------------------------

def read_model(path):
  """The text of the 'model' entry of an .oxm file ('oxm' + a zip)."""
  with open(path, 'rb') as f:
    data = f.read()
  if data[:3] == b'oxm':
    data = data[3:]
  with zipfile.ZipFile(io.BytesIO(data)) as z:
    return z.read('model').decode('utf-8', errors='replace')


_ATTR = re.compile(r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s<>]+))')
_ITEM = re.compile(r'\s*<(\w+)\b([^<>]*)>?')


def _vec(text):
  try:
    v = [float(x) for x in re.split(r'[,\s]+', text.strip()) if x]
  except ValueError:
    return None
  return tuple(v[:3]) if len(v) >= 3 else None


def _section(model_text, name):
  """[attrs] of the <Label> items of section name (AtomLabels, BondLabels):
  the item, not the font of the same name (<AtomLabels "1;14;...">) that a
  saved model lists earlier among its fonts."""
  m = re.search(r'<%s(?!\s*")' % name, model_text)
  if not m:
    return []
  out = []
  pos = m.end()
  while True:
    it = _ITEM.match(model_text, pos)
    if not it or it.group(1) != 'Label':
      break
    out.append(dict((a.group(1), a.group(2) if a.group(2) is not None else
                     a.group(3) if a.group(3) is not None else a.group(4))
                    for a in _ATTR.finditer(it.group(2))))
    pos = it.end()
  return out


def _labels(model_text, name):
  out = []
  for attrs in _section(model_text, name):
    xyz = _vec(attrs.get('offset', ''))
    if xyz is None:
      continue
    out.append({'text': attrs.get('text', ''),
                'visible': str(attrs.get('visible', '')).lower() in ('true', '1'),
                'xyz': xyz, 'drag': _vec(attrs.get('center', '')) or (0.0, 0.0, 0.0)})
  return out


def parse_atom_labels(model_text):
  """[{'text', 'visible', 'xyz', 'drag'}] of the atom labels of a saved model."""
  return _labels(model_text, 'AtomLabels')


def parse_bond_labels(model_text):
  """The same for the bond labels; xyz is the middle of the bond."""
  return _labels(model_text, 'BondLabels')


def _temp_model_path(tag):
  import tempfile
  # forward slashes: Olex2's command parser may take backslashes as escapes
  return os.path.join(tempfile.gettempdir(), 'olex2_labels_%s_%d.oxm'
                      % (tag, os.getpid())).replace('\\', '/')


def current_model():
  """The text of a model saved now (temporary file)."""
  import olex
  path = _temp_model_path('now')
  try:
    olex.m('save model "%s"' % path)
    return read_model(path)
  finally:
    if os.path.exists(path):
      os.remove(path)


def current_labels():
  return parse_atom_labels(current_model())


# --- 2. placing them ---------------------------------------------------------

def element(text):
  m = re.match(r'([A-Z][a-z]?)', text or '')
  return m.group(1) if m else 'C'


def atom_name(text):
  """The atom name in a label text ('C1', 'C1_$2', 'C1\\+\\i' -> 'C1')."""
  return re.split(r'[_\\\s^]', text or '')[0]


def find_bonds(atoms):
  """[(i, j)] of atoms closer than their covalent radii plus a tolerance."""
  out = []
  rad = [COVALENT.get(element(a['text']), METAL_RADIUS) for a in atoms]
  for i in range(len(atoms)):
    xi = atoms[i]['xyz']
    for j in range(i + 1, len(atoms)):
      xj = atoms[j]['xyz']
      d2 = sum((xi[k] - xj[k]) ** 2 for k in range(3))
      lim = rad[i] + rad[j] + BOND_TOLERANCE
      if 0.1 < d2 < lim * lim:
        out.append((i, j))
  return out


def bond_of(midpoint, atoms, tol=0.02):
  """(i, j) of the two atoms whose middle is midpoint, or None."""
  best = None
  for i in range(len(atoms)):
    a = atoms[i]['xyz']
    for j in range(i + 1, len(atoms)):
      b = atoms[j]['xyz']
      d = max(abs((a[k] + b[k]) / 2.0 - midpoint[k]) for k in range(3))
      if d < tol and (best is None or d < best[0]):
        best = (d, i, j)
  return best and best[1:]


def _rect_circle(rect, c, r):
  """How deep a circle reaches into a rectangle (0 = apart)."""
  x0, y0, x1, y1 = rect
  dx = max(x0 - c[0], 0, c[0] - x1)
  dy = max(y0 - c[1], 0, c[1] - y1)
  return max(0.0, r - math.hypot(dx, dy))


def _seg_rect(p, q, rect, pad=0.0):
  """Whether segment p-q passes through the rectangle (grown by pad)."""
  x0, y0, x1, y1 = rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad
  for t in [i / 12.0 for i in range(13)]:
    x = p[0] + (q[0] - p[0]) * t
    y = p[1] + (q[1] - p[1]) * t
    if x0 <= x <= x1 and y0 <= y <= y1:
      return True
  return False


def _rect_overlap(a, b):
  w = min(a[2], b[2]) - max(a[0], b[0])
  h = min(a[3], b[3]) - max(a[1], b[1])
  return w * h if w > 0 and h > 0 else 0.0


def _leader(ax, ay, start_r, rect, gap):
  """A line from start_r beyond (ax, ay) towards the rectangle, ending a gap
  before it; None when that is too short to show."""
  nx = min(max(ax, rect[0]), rect[2])
  ny = min(max(ay, rect[1]), rect[3])
  vx, vy = nx - ax, ny - ay
  dist = math.hypot(vx, vy)
  if dist < start_r + gap * 2.5:
    return None
  ux, uy = vx / dist, vy / dist
  return ((ax + ux * start_r, ay + uy * start_r), (nx - ux * gap, ny - uy * gap))


def place(items, gap, box_size, leader_after=0.5):
  """Place labels in view coordinates.

  items: [{'xy': (x, y), 'reach': r, 'text', 'show': bool, 'kind': 'atom' or
  'bond', 'fixed': (x, y) or None (bottom-left of a hand-moved label),
  'bond': (i, j) for bond labels}].  Atoms (kind 'atom') are the obstacles.
  box_size(text) -> (w, h) in Angstrom.  Returns, for each shown item,
  {'index', 'rect': (x0, y0, x1, y1), 'leader': ((x, y), (x, y)) or None,
  'moved': bool}.
  """
  atoms = [i for i, it in enumerate(items) if it.get('kind', 'atom') == 'atom']
  bonds = [(atoms[a], atoms[b]) for a, b in find_bonds(
    [{'text': items[i]['text'], 'xyz': (items[i]['xy'][0], items[i]['xy'][1],
                                        items[i].get('z', 0.0))} for i in atoms])]
  neighbours = dict((i, []) for i in range(len(items)))
  for i, j in bonds:
    neighbours[i].append(j)
    neighbours[j].append(i)
  segs = [(items[i]['xy'], items[j]['xy']) for i, j in bonds]
  placed = []
  out = []
  # hand-moved labels first: they are fixed obstacles
  for i, it in enumerate(items):
    if it.get('show') and it.get('fixed') is not None:
      w, h = box_size(it['text'])
      x, y = it['fixed']
      rect = (x, y, x + w, y + h)
      placed.append(rect)
      ax, ay = it['xy']
      start = it['reach'] + gap
      leader = None
      nx = min(max(ax, rect[0]), rect[2])
      ny = min(max(ay, rect[1]), rect[3])
      if math.hypot(nx - ax, ny - ay) > start + leader_after:
        leader = _leader(ax, ay, start, rect, gap)
      out.append({'index': i, 'rect': rect, 'leader': leader, 'moved': True})
  # the others, atoms before bonds, most crowded first
  todo = [i for i, it in enumerate(items) if it.get('show') and it.get('fixed') is None]

  def order(i):
    x, y = items[i]['xy']
    crowd = sum(1 for j in atoms if math.hypot(items[j]['xy'][0] - x, items[j]['xy'][1] - y) < 2.5)
    return (items[i].get('kind', 'atom') == 'bond', -crowd)
  todo.sort(key=order)
  for i in todo:
    it = items[i]
    w, h = box_size(it['text'])
    ax, ay = it['xy']
    own_r = it['reach'] + gap
    is_bond = it.get('kind') == 'bond'
    best = None
    for ring in range(RINGS):
      d = own_r + ring * RING_STEP
      for k in range(DIRECTIONS):
        ang = 2 * math.pi * k / DIRECTIONS
        ux, uy = math.cos(ang), math.sin(ang)
        px, py = ax + ux * d, ay + uy * d
        # the side of the box facing the atom touches (px, py)
        x0 = px - w / 2.0 + ux * w / 2.0
        y0 = py - h / 2.0 + uy * h / 2.0
        rect = (x0, y0, x0 + w, y0 + h)
        score = 6.0 * ring
        if _rect_circle(rect, (ax, ay), own_r) > 1e-6:
          score += 100.0
        for j in atoms:
          if j != i:
            depth = _rect_circle(rect, items[j]['xy'], items[j]['reach'] + gap * 0.5)
            if depth > 0:
              score += 40.0 + 60.0 * depth
        for p, q in segs:
          if _seg_rect(p, q, rect, gap * 0.3):
            score += 25.0
        pad = gap * 0.5  # labels keep a little space between them
        for r in placed:
          ov = _rect_overlap(rect, (r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad))
          if ov > 0:
            score += 200.0 + 400.0 * ov
        if is_bond and it.get('bond'):
          # beside the bond: across it, not along it
          a, b = it['bond']
          bx, by = items[b]['xy'][0] - items[a]['xy'][0], items[b]['xy'][1] - items[a]['xy'][1]
          n = math.hypot(bx, by) or 1.0
          score += 4.0 * abs(ux * bx + uy * by) / n
        else:
          # away from the own bonds
          for j in neighbours[i]:
            bx, by = items[j]['xy'][0] - ax, items[j]['xy'][1] - ay
            n = math.hypot(bx, by) or 1.0
            score += 3.0 * max(0.0, (ux * bx + uy * by) / n)
        if best is None or score < best[0]:
          best = (score, rect, ring)
      if best is not None and best[0] < 6.0 * ring + 3.0:
        break  # a clean place on this ring: no need to go further out
    score, rect, ring = best
    leader = _leader(ax, ay, own_r, rect, gap) if ring > 0 else None
    placed.append(rect)
    out.append({'index': i, 'rect': rect, 'leader': leader, 'moved': False})
  return out


# --- 3. drawing --------------------------------------------------------------

def font_path(name=''):
  """A font file: the given one, else the GUI's default font."""
  from olexFunctions import OV
  name = name or str(OV.GetParam('gui.default_font_name', '') or '')
  if name and os.path.isabs(name) and os.path.exists(name):
    return name
  # the theme's font folders (gui.theme.fontfiles), named here so that this
  # also works where the theme package cannot be imported
  dirs = [os.path.join(OV.DataDir(), 'fonts'), os.path.join(OV.BaseDir(), 'etc', 'gui', 'fonts')]
  for d in dirs:
    for fn in (name, name + '.ttf', name + '.otf'):
      p = os.path.join(d, fn)
      if fn and os.path.isfile(p):
        return p
  return None


class Measure:
  """Text sizes in Angstrom for a label height (cap height) in Angstrom."""
  NOMINAL = 100

  def __init__(self, path, height):
    from PIL import ImageFont
    self.path, self.height = path, height
    try:
      self.font = ImageFont.truetype(path, self.NOMINAL) if path else ImageFont.load_default()
    except OSError:
      self.font = ImageFont.load_default()
    # cap height of the font at NOMINAL px, from 'H'
    self.cap = self._box('H')[1] or self.NOMINAL * 0.7

  def _box(self, text):
    if hasattr(self.font, 'getbbox'):
      b = self.font.getbbox(text)
      return b[2] - b[0], b[3] - b[1]
    return self.font.getsize(text)

  def size(self, text):
    w = self._box(text)[0]
    k = self.height / float(self.cap)
    return w * k, self.height


def _luminance(c):
  r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
  return 0.299 * r + 0.587 * g + 0.114 * b


def colour_for(params, light):
  """user.image.labels.colour, else the theme's atom label colour for this
  background (gui.theme.glcolours), else black on light, white on dark.  A
  colour that would vanish on the background is replaced by black or white."""
  c = params['colour']
  if not re.match(r'^#[0-9a-fA-F]{6}$', c or ''):
    c = None
    try:
      from gui.theme import glcolours
      c = glcolours.effective('label_colours.atoms', light)
    except Exception as err:
      _report("read the label colour", err)
  if not c:
    return '#000000' if light else '#ffffff'
  if light and _luminance(c) > 150:
    return '#000000'
  if not light and _luminance(c) < 105:
    return '#ffffff'
  return c


def picture_is_light():
  """Whether the picture about to be made has a light background: a
  transparent png counts as light (it goes on a page), else the 3D view's."""
  from olexFunctions import OV
  if OV.GetParam('user.image.bitmap.transparent_background'):
    from . import has_alpha
    if has_alpha(OV.GetParam('user.image.bitmap.type')):
      return True
  try:
    from gui.theme import glcolours
    return glcolours.background_is_light()
  except Exception as err:
    _report("tell the background brightness", err)
    return True


def draw(image_path, items, placed, view_scale, image_centre, params, light, colour=None):
  """Draw the placed labels into the image file (saved in place).
  view_scale: image pixels per Angstrom; image_centre: pixel of the view origin."""
  from PIL import Image, ImageDraw, ImageFont
  im = Image.open(image_path)
  im.load()
  if im.mode not in ('RGB', 'RGBA'):
    im = im.convert('RGBA')
  d = ImageDraw.Draw(im)
  path = font_path(params['font'])

  def font_for(height):
    m = Measure(path, height)
    px = max(4, int(round(m.NOMINAL * height / float(m.cap) * view_scale)))
    try:
      return ImageFont.truetype(path, px) if path else ImageFont.load_default()
    except OSError:
      return ImageFont.load_default()
  fonts = {'atom': font_for(params['height']),
           'bond': font_for(params['height'] * params['bond_scale'])}
  colour = colour or colour_for(params, light)
  lw = max(1, int(round(params['leader_width'] * view_scale)))
  cx, cy = image_centre

  def to_px(x, y):
    return cx + x * view_scale, cy - y * view_scale
  for p in placed:
    text = items[p['index']]['text']
    font = fonts['bond' if items[p['index']].get('kind') == 'bond' else 'atom']
    ascent = font.getmetrics()[0] if hasattr(font, 'getmetrics') else 10
    x0, y0 = p['rect'][:2]
    left, base = to_px(x0, y0)
    # baseline at the bottom of the box: move up by the ascent
    d.text((left, base - ascent), text, font=font, fill=colour)
    if p['leader']:
      (sx, sy), (ex, ey) = p['leader']
      d.line([to_px(sx, sy), to_px(ex, ey)], fill=colour, width=lw)
  im.save(image_path)


# --- the whole job -----------------------------------------------------------

def prepare(window=None, view=None):
  """Read and place the labels for the view now.  Returns a plan for
  finish(), or None when there are no labels to draw."""
  params = _params()
  model = current_model()
  atom_labels = parse_atom_labels(model)
  bond_labels = parse_bond_labels(model) if params['bonds'] else []
  shown = [l for l in atom_labels + bond_labels if l['visible']]
  if not shown:
    print("Labels: %d atom and %d bond labels in the saved model, none shown: Olex2 draws "
          "the picture itself (spy.gui.images.labels_probe tells more)"
          % (len(atom_labels), len(bond_labels)))
    return None
  rows, centre, zoom = view or screenbox.basis()
  w, h = window or screenbox.window_size()
  reach = {}
  try:
    for name, _, r in screenbox.atoms_with_reach():
      reach[name] = r
  except Exception as err:
    _report("read the atom sizes", err)
  params['height'] *= screen_font_scale()
  m = Measure(font_path(params['font']), params['height'])
  mb = Measure(font_path(params['font']), params['height'] * params['bond_scale'])
  kinds = {}

  def box_size(text):
    # bond labels (lengths) are smaller than atom labels
    return (mb if kinds.get(text) == 'bond' else m).size(text)
  px_per_a = zoom * h

  def fixed_of(v, drag):
    # a dragged label: its bottom left sits zoom * drag pixels from the anchor
    # Olex2 gives new labels a small offset of its own: below moved_min
    # pixels a label counts as not moved
    if math.hypot(drag[0], drag[1]) * zoom * params['shift_scale'] < params['moved_min']:
      return None
    k = zoom * params['shift_scale'] / px_per_a
    return (v[0] + drag[0] * k, v[1] + drag[1] * k)
  items = []
  for l in atom_labels:
    v = screenbox.project(l['xyz'], rows, centre)
    name = atom_name(l['text'])
    r = reach.get(name, screenbox.H_REACH if element(name) == 'H' else 0.35)
    items.append({'xy': (v[0], v[1]), 'z': v[2], 'reach': r, 'text': l['text'],
                  'show': l['visible'], 'kind': 'atom', 'fixed': fixed_of(v, l['drag'])})
  n_atoms = len(items)
  bond_atoms = []
  for l in bond_labels:
    if not l['visible']:
      continue
    v = screenbox.project(l['xyz'], rows, centre)
    pair = bond_of(l['xyz'], atom_labels)
    items.append({'xy': (v[0], v[1]), 'z': v[2], 'reach': BOND_LABEL_REACH, 'text': l['text'],
                  'show': True, 'kind': 'bond', 'bond': pair,
                  'fixed': fixed_of(v, l['drag'])})
    if pair:
      bond_atoms.append((atom_name(atom_labels[pair[0]]['text']),
                         atom_name(atom_labels[pair[1]]['text']),
                         abs(l['drag'][0]) + abs(l['drag'][1]) > 1e-6))
    else:
      print("Labels: bond label '%s' belongs to no bond found; it is not shown again "
            "after the image" % l['text'])
  for it in items:
    if it['kind'] == 'bond':
      kinds[it['text']] = 'bond'
  placed = place(items, params['gap'], box_size, params['leader_after'])
  return {'items': items, 'placed': placed, 'params': params, 'window': (w, h),
          'zoom': zoom, 'bond_atoms': bond_atoms,
          'names': sorted(set(atom_name(l['text']) for l in atom_labels if l['visible'])),
          'n_atoms': n_atoms}


def hide_native():
  import olex
  olex.m('kill labels')


def restore_native(plan):
  """Show Olex2's labels again: 'label <atoms>' keeps where atom labels were
  dragged; bond labels are made again from their two atoms."""
  import olex
  names = plan['names']
  for i in range(0, len(names), 60):
    olex.m('label %s' % ' '.join(names[i:i + 60]))
  moved = 0
  for a, b, was_moved in plan['bond_atoms']:
    olex.m('sel -u')
    olex.m('sel -a %s %s' % (a, b))
    olex.m('sel atom bonds')
    olex.m('sel -u %s %s' % (a, b))
    olex.m('label')
    moved += was_moved
  if plan['bond_atoms']:
    olex.m('sel -u')
  if moved:
    print("Labels: %d bond label%s moved by hand %s back at the bond on screen (the image "
          "has them where they were)" % (moved, '' if moved == 1 else 's',
                                         'is' if moved == 1 else 'are'))


def legend_font(params):
  """The system font for the legend in the picture: the labels' font, which
  is registered with the system (gui.theme.fontfiles)."""
  path = font_path(params['font'])
  if not path:
    return None
  try:
    from PIL import ImageFont
    family, style = ImageFont.truetype(path, 12).getname()
    from gui.theme import fontfiles
    fontfiles.register_file(path)
  except Exception as err:
    _report("prepare the legend font", err)
    return None
  pt = int(round(params['legend_size'])) or legend_points(params)
  weight = 700 if 'bold' in (style or '').lower() else 400
  return '1;%d;%d;0;0;0;%d;0;0;0;0;3;2;1;34;%s' % (pt, -int(round(pt * 96 / 72.0)), weight,
                                                  family)


LEGEND_POINTS_PER_PX = 72 / 96.0 / 0.7  # cap height ~0.7 of the point size
_current_plan = {}


def legend_points(params, plan=None):
  """A point size for the legend that matches the atom labels: their height
  in pixels of the 3D window, as a font size."""
  plan = plan or _current_plan.get('plan')
  if not plan:
    return 14
  px = params['height'] * plan['zoom'] * plan['window'][1]
  return max(6, int(round(px * LEGEND_POINTS_PER_PX)))


def finish(plan, image_path):
  """Draw the planned labels into a picture of the whole 3D window."""
  from PIL import Image
  w, h = plan['window']
  with Image.open(image_path) as im:
    iw, ih = im.size
  view_scale = plan['zoom'] * h * (iw / float(w))
  light = plan.get('light', True)
  draw(image_path, plan['items'], plan['placed'], view_scale, (iw / 2.0, ih / 2.0),
       plan['params'], light, plan.get('colour'))


def extend_box(box, plan):
  """The screen box (pixels of the 3D window) grown to take in the placed
  labels, so trimming does not cut them off."""
  if not plan or not plan['placed'] or not box:
    return box
  w, h = plan['window']
  s = plan['zoom'] * h
  left, top, right, bottom = box
  for p in plan['placed']:
    x0, y0, x1, y1 = p['rect']
    left = min(left, w / 2.0 + x0 * s)
    right = max(right, w / 2.0 + x1 * s)
    top = min(top, h / 2.0 - y1 * s)
    bottom = max(bottom, h / 2.0 - y0 * s)
  return left, top, right, bottom


def safe_prepare():
  """prepare(), None (and a message) when it fails."""
  try:
    return prepare()
  except Exception as err:
    _report("place the labels", err)
    return None


def render(pict_command, image_path, plan=None):
  """Run pict_command (an Olex2 'pict...' macro writing image_path) with the
  labels drawn by this module (plan from prepare(), made now if not given).
  False if there was nothing to do (the command then still ran)."""
  import olex
  import olx
  if plan is None:
    plan = safe_prepare()
  if plan is None:
    olex.m(pict_command)
    return False
  # the legend is drawn with the AtomLabels font: a real one for the picture
  old_font = None
  try:
    old_font = olx.GetFont('AtomLabels')
  except Exception as err:
    _report("read the label font", err)
  _current_plan['plan'] = plan
  new_font = legend_font(plan['params']) if old_font and old_font.startswith('@') else None
  # one colour for the labels and the legend, for the picture's background
  plan['light'] = picture_is_light()
  plan['colour'] = colour_for(plan['params'], plan['light'])
  hide_native()
  try:
    if new_font:
      olx.SetFont('AtomLabels', new_font)
    try:
      from gui.theme import glcolours
      olx.SetMaterial('AtomLegend.Text', glcolours.material(plan['colour'], 2049))
    except Exception as err:
      _report("colour the legend", err)
    olex.m(pict_command)
  finally:
    if new_font:
      olx.SetFont('AtomLabels', old_font)
    restore_native(plan)
    try:
      from gui.theme import glcolours
      glcolours.apply(restore=True)
    except Exception as err:
      _report("restore the theme colours", err)
  if os.path.exists(image_path):
    finish(plan, image_path)
  return True


def preview(path=''):
  """spy.gui.images.labels_preview([file]): the normal image (Ctrl+P: size,
  quality, trimming) with the labels placed and drawn by Python, in the
  structure's folder unless a file is given (Ctrl+Shift+P)."""
  from . import MakeLabelledImage
  return MakeLabelledImage(path)


def probe_model():
  """Step by step: save the model, open it, find the labels."""
  import olex
  path = _temp_model_path('probe')
  if os.path.exists(path):
    os.remove(path)
  cmd = 'save model "%s"' % path
  print("1 command: %s" % cmd)
  olex.m(cmd)
  if not os.path.exists(path):
    folder = os.path.dirname(path)
    print("  no file at %s; .oxm files there: %s" % (path, [f for f in os.listdir(folder)
                                                            if f.endswith('.oxm')]))
    return
  data = open(path, 'rb').read()
  print("2 file: %d bytes, starts with %r" % (len(data), data[:8]))
  try:
    text = read_model(path)
  except Exception as err:
    print("  cannot open it as oxm + zip: %s" % err)
    return
  print("3 model text: %d characters" % len(text))
  for name, labels in (('atom', parse_atom_labels(text)), ('bond', parse_bond_labels(text))):
    print("4 %s labels: %d, shown: %d, dragged: %d" % (
      name, len(labels), sum(1 for l in labels if l['visible']),
      sum(1 for l in labels if abs(l['drag'][0]) + abs(l['drag'][1]) > 1e-6)))
    for l in [l for l in labels if l['visible']][:6]:
      print("   %-12s drag %s" % (l['text'], ', '.join('%.3g' % v for v in l['drag'])))
  os.remove(path)


def probe():
  """spy.gui.images.labels_probe(): print how the labels are read, where
  dragged ones are taken to be, and the view (read-only)."""
  probe_model()
  plan = prepare()
  if not plan:
    return
  w, h = plan['window']
  s = plan['zoom'] * h
  print("5 window %s x %s, zoom %.5f, %.1f px per Angstrom" % (w, h, plan['zoom'], s))
  for p in plan['placed']:
    it = plan['items'][p['index']]
    ax, ay = w / 2.0 + it['xy'][0] * s, h / 2.0 - it['xy'][1] * s
    lx, ly = w / 2.0 + p['rect'][0] * s, h / 2.0 - p['rect'][1] * s
    print("  %-4s %-10s at %5.0f,%5.0f  label bottom-left %5.0f,%5.0f  %s%s" % (
      it['kind'], it['text'], ax, ay, lx, ly, 'moved by hand' if p['moved'] else 'placed',
      ', leader line' if p['leader'] else ''))
