"""Where the structure is on screen, in pixels of the 3D window, from the view.

Used to trim exported images to the structure (MakeBitmapImage) without
looking at pixels, so gradients, pictures and transparent backgrounds trim as
well as plain ones, and to place the atom legend.

The view (confirmed on a real structure, 2026-11-12):
  gl.Basis() reads   zoom="z" <matrix xx= xy= .. zz=> <center x= y= z=>
  a Cartesian point p is at  v_i = sum_j M[j][i] * (p_j + centre_j)
  (the matrix applied by columns) and one Angstrom is zoom * (height of the
  3D window) pixels, from the middle of the window, y up.
  GetWindowSize('gl') = x,y,w,h.

Only the atom centres are known, so spheres and ellipsoids are allowed
'reach' Angstrom beyond them; labels outside that are not part of the box.
"""
import re
import sys

import olx

DEFAULT_REACH = 0.5


def _report(what, err):
  print("Screen box: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def basis(text=None):
  """(3x3 rows, centre, zoom) from gl.Basis()."""
  text = olx.gl.Basis() if text is None else text
  get = lambda key: float(re.search(r'\b%s="([^"]+)"' % key, text).group(1))
  rows = [[get(r + c) for c in 'xyz'] for r in 'xyz']
  centre = [float(re.search(r'<center[^>]*\b%s="([^"]+)"' % a, text).group(1)) for a in 'xyz']
  return rows, centre, get('zoom')


def project(xyz, rows, centre):
  """View coordinates (Angstrom, x right, y up) of a Cartesian point."""
  v = [xyz[i] + centre[i] for i in range(3)]
  return [sum(rows[j][i] * v[j] for j in range(3)) for i in range(3)]


def window_size():
  """(width, height) of the 3D window in pixels."""
  return tuple(int(v) for v in olx.GetWindowSize('gl').split(',')[2:4])


def shown_atoms():
  """[(label, (x, y, z))] of the atoms on screen, Cartesian: the asymmetric
  unit (olx.Crd), which is what is shown unless the structure was grown.
  (all_copies() also takes what olx.Info lists, which can include copies
  that are not drawn: it made the box too big in a test, 2026-11-12.)"""
  out = []
  try:
    n = int(olx.xf.au.GetAtomCount())
  except (ValueError, AttributeError, RuntimeError) as err:
    _report("count the atoms", err)
    return out
  for i in range(n):
    try:
      label = olx.xf.au.GetAtomName(i)
      out.append((label, tuple(float(v) for v in olx.Crd(label).split())))
    except (ValueError, AttributeError, RuntimeError):
      continue
  return out


# How far a drawn atom reaches beyond its centre, in the default drawing
# (telp 50: ellipsoids at 50 % probability, 'arad isot'): TELP_SCALE * sqrt(U),
# with U the Uiso or Ueq; H atoms are drawn as small spheres of their own.
TELP_SCALE = 1.5382
H_REACH = 0.15


def drawn_reach(label, u):
  if re.match(r'H(?![a-z])', label or ''):
    return H_REACH
  try:
    return TELP_SCALE * max(0.0, float(u)) ** 0.5
  except (TypeError, ValueError):
    return DEFAULT_REACH


def atoms_with_reach():
  """[(label, (x, y, z), reach)] of the asymmetric unit: each atom with how far
  it is drawn beyond its centre (drawn_reach)."""
  out = []
  try:
    n = int(olx.xf.au.GetAtomCount())
  except (ValueError, AttributeError, RuntimeError) as err:
    _report("count the atoms", err)
    return out
  for i in range(n):
    try:
      label = olx.xf.au.GetAtomName(i)
      xyz = tuple(float(v) for v in olx.Crd(label).split())
      out.append((label, xyz, drawn_reach(label, olx.xf.au.GetAtomUiso(i))))
    except (ValueError, AttributeError, RuntimeError):
      continue
  return out


def all_copies():
  """[(label, (x, y, z))] of every copy of every atom olx.Info lists, Cartesian;
  for a grown structure, once it is clear which of them are drawn."""
  out = []
  try:
    n = int(olx.xf.au.GetAtomCount())
  except (ValueError, AttributeError, RuntimeError) as err:
    _report("count the atoms", err)
    return out
  for i in range(n):
    try:
      label = olx.xf.au.GetAtomName(i)
      found = False
      for line in olx.Info(label, f=True, p=6).splitlines():
        t = line.split()
        if len(t) > 4 and t[0] == label:
          out.append((label, tuple(float(v) for v in t[2:5])))
          found = True
      if not found:  # deleted or hidden copies print nothing: use the a.u. one
        out.append((label, tuple(float(v) for v in olx.Crd(label).split())))
    except (ValueError, AttributeError, RuntimeError):
      continue
  return out


# --- perspective ------------------------------------------------------------
# Olex2 (glib/glrender.cpp SetView): the eye looks from 2 view units in front of
# the centre (NearPlane 1, translate -(NearPlane+1)/zoom), with a frustum of
# half height tan(angle/2) * 0.5 at the near plane.  So a point at view
# coordinates v is drawn at  h * zoom * v / (tan(angle/2) * (2 - zoom * v_z))
# pixels from the middle, instead of h * zoom * v without perspective.
# Olex2 cannot be asked whether perspective is on: spy.gui.images.perspective()
# sets it and keeps the angle in user.image.perspective (0 = off).

def perspective_angle():
  try:
    from olexFunctions import OV
    return float(OV.GetParam('user.image.perspective', 0) or 0)
  except (ImportError, TypeError, ValueError):
    return 0.0


def depth_factor(v_z, zoom, angle):
  """How much bigger than without perspective a point at depth v_z is drawn."""
  if not angle:
    return 1.0
  import math
  d = 2.0 - zoom * v_z
  return 1.0 / (math.tan(math.radians(angle) / 2.0) * max(d, 1e-3))


def flat(xyz, rows, centre, zoom, angle=0.0):
  """(x, y, factor): view coordinates with perspective applied, still in
  Angstrom as without it (pixels = value * zoom * height), and the factor."""
  v = project(xyz, rows, centre)
  f = depth_factor(v[2], zoom, angle)
  return v[0] * f, v[1] * f, f


# --- what is drawn, from a saved model -----------------------------------------

def drawn_atoms(model_text, uiso=None):
  """[(label, xyz, reach)] of every atom drawn, grown copies included, hidden
  ones left out: the lattice atoms of a saved model (see gui.fromoxm).
  uiso: {label: U} for the reach; read from Olex2 when not given."""
  from gui.fromoxm import _core as G
  xf = G._section(model_text, '<Lattice', '\n  <')
  au = G._section(xf, '<AUnit', '<Matrices')
  labels = [G._attrs(t).get('label') for t in
            re.findall(r'<atom [^\n]*', G._section(au, '<residues', '\n    >'))]
  lat = re.findall(r'<Atom [^\n]*', G._section(xf, '\n    <Atoms', '\n    <Bonds'))
  # deleted atoms (flag 1) have no visibility bit (TGXApp::SaveModel)
  lat = [t for t in lat if not int(G._attrs(t).get('flags', '0') or 0) & 1]
  visible = G._visibility(model_text, len(lat))
  # hydrogen atoms and Q-peaks switched off as a whole keep their own bits
  vis = re.search(r'<Visibility [^\n]*', model_text)
  flags = dict(re.findall(r'\b(h_atoms|q_atoms)="(\w+)"', vis.group(0) if vis else ''))
  hidden_kinds = set(k for k, key in (('H', 'h_atoms'), ('Q', 'q_atoms'))
                     if flags.get(key, 'true').lower() != 'true')
  if uiso is None:
    uiso = {}
    try:
      for i in range(int(olx.xf.au.GetAtomCount())):
        uiso[olx.xf.au.GetAtomName(i)] = olx.xf.au.GetAtomUiso(i)
    except (ValueError, AttributeError, RuntimeError) as err:
      _report("read the atom sizes", err)
  out = []
  for n, tag in enumerate(lat):
    if not visible[n]:
      continue
    a = G._attrs(tag)
    k = int(a['atom_id'])
    label = labels[k] if k < len(labels) else ''
    if element_of(label) in hidden_kinds or (element_of(label) == 'D' and 'H' in hidden_kinds):
      continue
    xyz = tuple(float(x) for x in a['crd'].split(','))
    out.append((label, xyz, drawn_reach(label, uiso.get(label, 0.05))))
  return out


def calc_zoom(model_text):
  """Olex2's CalcZoom() for the scene of a saved model: 1 / |max - min| of
  <Renderer max= min=> (at least 1 Angstrom), as glib/glrender.cpp does it.
  Vector labels are drawn at zoom / CalcZoom (see labelmode)."""
  m = re.search(r'<Renderer max="([^"]+)" min="([^"]+)"', model_text)
  if not m:
    return 1.0
  a = [float(x) for x in m.group(1).split(',')]
  b = [float(x) for x in m.group(2).split(',')]
  return 1.0 / max(1.0, sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5)


def legend_box(model_text, element_count):
  """(left, top, right, bottom) of the atom legend in window pixels, or None
  when it is hidden.  Its place is in the saved model (style entry
  AtomLegend Left/Top); its size is not, so it comes from the legend
  measurement of the theme designer (user.legend.width, row_height)."""
  m = re.search(r'<S_\d+ ([^\n]*Name="AtomLegend"[^\n]*)', model_text)
  if not m:
    return None
  from gui.fromoxm import _core as G
  a = G._attrs(m.group(1))
  if str(a.get('visible', 'true')).lower() != 'true':
    return None
  vis = re.search(r'<Visibility [^\n]*legend="(\w+)"', model_text)
  if vis and vis.group(1).lower() != 'true':
    return None
  try:
    from olexFunctions import OV
    width = float(OV.GetParam('user.legend.width', 0) or 0) or 60.0
    row = float(OV.GetParam('user.legend.row_height', 0) or 0) or 26.0
  except (ImportError, TypeError, ValueError):
    width, row = 60.0, 26.0
  left, top = float(a.get('Left', 0)), float(a.get('Top', 0))
  return (left, top, left + width, top + row * max(1, element_count))


def element_of(label):
  m = re.match(r'([A-Z][a-z]?)', label or '')
  return m.group(1) if m else ''


def union(*boxes):
  boxes = [b for b in boxes if b]
  if not boxes:
    return None
  return (min(b[0] for b in boxes), min(b[1] for b in boxes),
          max(b[2] for b in boxes), max(b[3] for b in boxes))


def screen_box(atoms=None, view=None, size=None, reach=DEFAULT_REACH, angle=0.0):
  """(left, top, right, bottom) of the structure in pixels of the 3D window,
  from its top left corner, or None without atoms.  atoms are (label, xyz) and
  reach beyond each centre by 'reach' Angstrom, or (label, xyz, own reach).
  angle: the perspective angle, 0 without."""
  atoms = shown_atoms() if atoms is None else atoms
  if not atoms:
    return None
  rows, centre, zoom = view or basis()
  w, h = size or window_size()
  scale = zoom * h
  left = top = right = bottom = None
  for a in atoms:
    x, y, f = flat(a[1], rows, centre, zoom, angle)
    r = (a[2] if len(a) > 2 else reach) * f
    left = x - r if left is None else min(left, x - r)
    right = x + r if right is None else max(right, x + r)
    top = y + r if top is None else max(top, y + r)
    bottom = y - r if bottom is None else min(bottom, y - r)
  return (w / 2.0 + left * scale, h / 2.0 - top * scale,
          w / 2.0 + right * scale, h / 2.0 - bottom * scale)


def flat_rect_to_px(rect, zoom, size):
  """A rectangle (x0, y0, x1, y1) in flat view Angstrom -> window pixels."""
  w, h = size
  s = zoom * h
  return (w / 2.0 + rect[0] * s, h / 2.0 - rect[3] * s,
          w / 2.0 + rect[2] * s, h / 2.0 - rect[1] * s)


# --- trimming an exported image ---------------------------------------------

def render_width(box, window_width, target_width, padding_pct, border_pct):
  """The width to render the whole view at, so that the structure's box plus
  padding and border comes out target_width wide."""
  border = int(target_width * border_pct / 100.0)
  padding = int(target_width * padding_pct / 100.0)
  inner = max(1, target_width - 2 * border - 2 * padding)
  return inner * float(window_width) / max(1.0, box[2] - box[0])


def crop_box(box, window_size, image_size, padding_px):
  """The box in the rendered image's pixels, widened by padding_px and kept
  inside the image."""
  fx = image_size[0] / float(window_size[0])
  fy = image_size[1] / float(window_size[1])
  left = max(0, int(round(box[0] * fx)) - padding_px)
  top = max(0, int(round(box[1] * fy)) - padding_px)
  right = min(image_size[0], int(round(box[2] * fx)) + padding_px)
  bottom = min(image_size[1], int(round(box[3] * fy)) + padding_px)
  return left, top, right, bottom


def trim_rendered(path, box, window, target_width, padding_pct, border_pct, border_col):
  """Crop the image at path to the structure's box: the padding is the real
  background of the rendering (gradient, picture or transparency), then the
  border is added.  Saved in place."""
  from PIL import Image, ImageOps
  im = Image.open(path)
  im.load()
  border = int(target_width * border_pct / 100.0)
  padding = int(target_width * padding_pct / 100.0)
  im = im.crop(crop_box(box, window, im.size, padding))
  if border:
    im = ImageOps.expand(im, border=border, fill=str(border_col))
  im.save(path)
  return im.size
