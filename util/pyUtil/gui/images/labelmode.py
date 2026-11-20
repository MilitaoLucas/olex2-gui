"""Label modes: 'normal' (Olex2 as it always was) and 'vector'.

Vector mode sets the atom and bond label fonts to Olex2's vector font
(@<size>), so labels zoom with the structure and keep where they were dragged.
Ctrl+P then makes the usual image, but draws every shown label in a real font
where it is on screen (Olex2's vector labels are thin):

  - the labels are read from a saved model (gui.images.labels: text, anchor =
    atom or middle of the bond, drag)
  - during 'pict' Olex2's labels get a vector font of size 1 (HIDE_FONT) and
    their fonts are put back afterwards; drags are kept; the legend has its
    own font and stays as it is.  vector_both leaves them in, for comparing
  - each label is drawn at its screen place and size, from a calibration

Calibration (spy.gui.images.label_calibrate) measures instead of guessing: it
renders the 3D window once with the labels in pure magenta, finds them in the
pixels and fits
  label height (Angstrom) = size_per_pt * vector font size
  bottom left (Angstrom)  = anchor + drag_scale * drag + (offset_x, offset_y)
(view coordinates, see screenbox.py).  The results are kept in
user.image.labels.calib_*.

spy.gui.images.label_mode([normal|vector]) switches; the fonts used before
vector mode come back in normal mode.
"""
import math
import os
import sys

from . import labels as L
from . import screenbox

MAGENTA = '#ff00ff'


def _report(what, err):
  print("Label mode: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def _get(key, default=None):
  from olexFunctions import OV
  v = OV.GetParam('user.image.labels.%s' % key, default)
  return default if v is None else v


def _set(key, value):
  from olexFunctions import OV
  OV.SetParam('user.image.labels.%s' % key, value)


def current():
  return str(_get('mode', 'normal') or 'normal')


def sizes():
  return int(_get('vector_atom_size', 12)), int(_get('vector_bond_size', 7))


def set_mode(mode=''):
  """spy.gui.images.label_mode([normal|vector]): switch; no argument prints the mode."""
  import olx
  mode = str(mode or '').strip().lower()
  if not mode:
    print("Label mode: %s" % current())
    return current()
  if mode not in ('normal', 'vector'):
    print("Label mode: use normal or vector")
    return current()
  if mode == 'vector':
    atom, bond = sizes()
    for slot, key, size in (('AtomLabels', 'normal_atom_font', atom),
                            ('BondLabels', 'normal_bond_font', bond)):
      try:
        old = olx.GetFont(slot)
        if old and not old.startswith('@'):
          _set(key, old)
        olx.SetFont(slot, '@%d' % size)
      except Exception as err:
        _report("set the %s font" % slot, err)
  else:
    for slot, key in (('AtomLabels', 'normal_atom_font'), ('BondLabels', 'normal_bond_font')):
      try:
        if not (olx.GetFont(slot) or '').startswith('@'):
          continue  # not a vector font: nothing to undo
        # the font from before vector mode; lost when the parameters were not
        # saved (before 2026-11-14): then the scene's own, then Olex2's default
        old = str(_get(key, '') or '') or scene_font(slot) or DEFAULT_FONT
        olx.SetFont(slot, old)
      except Exception as err:
        _report("set the %s font" % slot, err)
  _set('mode', mode)
  try:
    import olex
    olex.m('spy.SaveUserParams()')  # the mode and the fonts to come back to
  except Exception as err:
    _report("save the label mode", err)
  print("Label mode: %s" % mode)
  return mode


DEFAULT_FONT = '#olex2.fnt:frb_18'


def scene_font(slot):
  """The font of a label slot in the scene in use (user.def_scene), or None."""
  import re
  from olexFunctions import OV
  name = OV.GetParam('user.def_scene', '') or ''
  for d in (os.path.join(OV.DataDir(), 'styles'), os.path.join(OV.BaseDir(), 'etc', 'styles')):
    p = os.path.join(d, name + '.glsp')
    if name and os.path.isfile(p):
      try:
        with open(p, encoding='utf-8-sig', errors='replace') as f:
          m = re.search(r'<%s\s+id="([^"]+)"' % slot, f.read())
      except OSError as err:
        _report("read the scene %s" % p, err)
        return None
      return m.group(1) if m else None
  return None


def reapply(force=False):
  """In vector mode, the vector fonts again: after a start, a skin change or
  the Bitmap Images panel (which sets its own label fonts); force: also when
  a vector font is set, for new sizes (then saved)."""
  force = str(force).lower() in ('true', '1')
  if current() == 'vector':
    import olx
    atom, bond = sizes()
    for slot, key, size in (('AtomLabels', 'normal_atom_font', atom),
                            ('BondLabels', 'normal_bond_font', bond)):
      try:
        old = olx.GetFont(slot) or ''
        if force or not old.startswith('@'):
          if old and not old.startswith('@'):
            _set(key, old)  # the font to come back to in normal mode
          olx.SetFont(slot, '@%d' % size)
      except Exception as err:
        _report("set the %s font" % slot, err)
    if force:
      try:
        import olex
        olex.m('spy.SaveUserParams()')
      except Exception as err:
        _report("save the label sizes", err)


def vector_size(slot):
  import olx
  try:
    f = olx.GetFont(slot) or ''
  except Exception as err:
    _report("read the %s font" % slot, err)
    return None
  if not f.startswith('@'):
    return None
  s = f[1:]
  return float(s) if s.replace('.', '', 1).isdigit() else 15.0


# --- where the labels are on screen --------------------------------------------

# How big Olex2 draws a vector label (gxlib/gllabel.cpp TXGlLabel::Orient):
# DrawVectorText(..., zoom / CalcZoom()), CalcZoom = 1 / |max - min| of the
# scene.  So on screen, in view Angstrom, a label is  k * pt / CalcZoom  high:
# it does NOT stay the same size in Angstrom when the structure is grown (the
# scene gets bigger, CalcZoom smaller, the labels bigger).  k is calibrated
# (calib_size_k).  Calibrations made before 2026-11-14 hold calib_size_per_pt
# (= k / CalcZoom of the structure then) and are used as they are until the
# next calibration.  The drag (TXGlLabel::GetVectorPosition) is added in 3D
# before the projection, so perspective scales it like the atom positions; the
# label size is not changed by perspective.

def size_constant():
  """(constant, per_calczoom): calib_size_k if calibrated since 2026-11-14,
  else the older calib_size_per_pt (or the first estimate)."""
  k = float(_get('calib_size_k', 0) or 0)
  if k:
    return k, True
  # first estimate: printed labels came out half as high as Olex2's (2026-11-13)
  return float(_get('calib_size_per_pt', 0) or 0) or 0.026, False


def calibration(window_h):
  """(size, drag_scale, offset_x, offset_y) in Angstrom; the defaults are the
  first estimate, label_calibrate replaces them.  size multiplies an item's
  'pt' (see screen_labels)."""
  size = size_constant()[0]
  # the drag is not calibrated: TXGlLabel::GetVectorPosition adds it times
  # GetScale() = 1/Height of the window, in 3D, before the projection, so it is
  # drag / height in view Angstrom.  (A fitted drag scale from a calibration
  # with few or small drags threw labels far off, 2026-11-14.)
  drag = 1.0 / max(1, window_h)
  # printed labels started ~0.05 A left of Olex2's (image of 2026-11-13); baselines agreed
  ox = float(_get('calib_offset_x', 0) or 0) or 0.05
  return size, drag, ox, float(_get('calib_offset_y', 0) or 0)


def ttf_scale():
  """The printed (TrueType) labels against Olex2's printed vector ones: Olex2
  prints its vector labels a little bigger than it shows them (user, 2026-11-14:
  ours came out ~0.9 of Olex2's printed ones; 2026-11-16 at 1.1: ~0.93 -> 1.18)."""
  try:
    return float(_get('ttf_scale', 1.18) or 1.18)
  except (TypeError, ValueError):
    return 1.18


def screen_labels(model=None, view=None, window=None, per_calczoom=None):
  """[{'text', 'kind', 'anchor': (x, y), 'drag': (x, y), 'pt', 'f', 'reach'}]
  of the shown atom and bond labels, in view Angstrom; and the view.  'pt' is
  the vector font size, divided by CalcZoom when the size constant is one of
  those (per_calczoom, default: as calibrated); 'f' the perspective factor."""
  model = model or L.current_model()
  if per_calczoom is None:
    per_calczoom = size_constant()[1]
  cz = screenbox.calc_zoom(model) if per_calczoom else 1.0
  reach = {}
  try:
    for name, _, r in screenbox.atoms_with_reach():
      reach[name] = r
  except Exception as err:
    _report("read the atom sizes", err)
  rows, centre, zoom = view or screenbox.basis()
  w, h = window or screenbox.window_size()
  angle = screenbox.perspective_angle()
  out = []
  for kind, slot, labels in (('atom', 'AtomLabels', L.parse_atom_labels(model)),
                             ('bond', 'BondLabels', L.parse_bond_labels(model))):
    pt = vector_size(slot) or (sizes()[0] if kind == 'atom' else sizes()[1])
    for l in labels:
      if not l['visible'] or not l['text']:
        continue
      # perspective moves the anchor and scales the drag (see above), not the size
      x, y, f = screenbox.flat(l['xyz'], rows, centre, zoom, angle)
      if kind == 'atom':
        name = L.atom_name(l['text'])
        r = reach.get(name, screenbox.H_REACH if L.element(name) == 'H' else 0.35)
      else:
        r = L.BOND_LABEL_REACH
      out.append({'text': l['text'], 'kind': kind, 'anchor': (x, y),
                  'drag': (l['drag'][0], l['drag'][1]), 'pt': pt / cz, 'f': f,
                  'reach': r * f})
  return out, (rows, centre, zoom), (w, h)


def placed(items, window, measure_for, gap=0.12, leader_after=0.15):
  """The label boxes where Olex2 shows them (calibrated), as labels.draw wants.
  A label further than leader_after beyond its atom (its drawn size) or its
  bond gets a connecting line, a gap away from both ends."""
  size, drag, ox, oy = calibration(window[1])
  scale = ttf_scale()
  out = []
  for i, it in enumerate(items):
    height = size * it['pt'] * scale
    w = measure_for(height).size(it['text'])[0]
    f = it.get('f', 1.0)
    x0 = it['anchor'][0] + f * drag * it['drag'][0] + ox
    y0 = it['anchor'][1] + f * drag * it['drag'][1] + oy
    it['height'] = height
    rect = (x0, y0, x0 + w, y0 + height)
    ax, ay = it['anchor']
    start = it.get('reach', 0.08) + gap
    nx = min(max(ax, rect[0]), rect[2])
    ny = min(max(ay, rect[1]), rect[3])
    leader = None
    if math.hypot(nx - ax, ny - ay) > start + leader_after:
      leader = L._leader(ax, ay, start, rect, gap)
    out.append({'index': i, 'rect': rect, 'leader': leader, 'moved': True})
  return out


# --- the picture -----------------------------------------------------------------

def _material(name):
  import olx
  try:
    return olx.GetMaterial(name)
  except Exception as err:
    _report("read the material %s" % name, err)
    return None


def _measurer(font_file):
  cache = {}

  def measure_for(height):
    key = round(height, 4)
    if key not in cache:
      cache[key] = L.Measure(font_file, height)
    return cache[key]
  return measure_for


def label_boxes_px(model=None):
  """Window-pixel boxes of the labels as vector mode prints them (for the
  trim); [] when there are none or they cannot be read."""
  try:
    items, view, window = screen_labels(model)
    if not items:
      return []
    params = L._params()
    boxes = placed(items, window, _measurer(L.font_path(params['font'])),
                   params['gap'], params['leader_after'])
  except Exception as err:
    _report("place the labels for the trim", err)
    return []
  return [screenbox.flat_rect_to_px(b['rect'], view[2], window) for b in boxes]


def show_both():
  """user.image.labels.vector_both: keep Olex2's own vector labels in the image
  under the printed ones (for comparing); off by default."""
  return str(_get('vector_both', False)).lower() in ('true', '1')


# Hiding Olex2's labels during 'pict': a transparent PLabels.Text material does
# not hide vector text (2026-11-13), and 'kill labels' + 'label' re-anchors
# the labels (macLabel: SetOffset; bond labels lose their drag).  Changing the
# font keeps every drag (as switching the label mode does), so for the picture
# the label fonts become a vector font of size 1 -- a speck at each label's
# lower left, which the printed label covers.  (@0 is accepted by Olex2 too,
# but a zero-size font may divide by zero in the core.)
HIDE_FONT = '@1'


def _hide_fonts():
  """Set the label fonts to HIDE_FONT; [(slot, font to put back)]."""
  import olx
  saved = []
  for slot in ('AtomLabels', 'BondLabels'):
    try:
      old = olx.GetFont(slot)
      if old:
        olx.SetFont(slot, HIDE_FONT)
        saved.append((slot, old))
    except Exception as err:
      _report("hide the %s" % slot, err)
  return saved


def _restore_fonts(saved):
  import olx
  for slot, old in saved:
    try:
      olx.SetFont(slot, old)
    except Exception as err:
      _report("put back the %s font %s" % (slot, old), err)


def render(pict_command, image_path):
  """Run the pict command without Olex2's own labels (unless vector_both),
  then draw them in a real font where they are on screen.  False if there
  were no labels."""
  import olex
  import olx
  from olexFunctions import OV
  try:
    items, view, window = screen_labels()
  except Exception as err:
    _report("read the labels", err)
    items = []
  if not items:
    olex.m(pict_command)
    return False
  params = L._params()
  path = L.font_path(params['font'])
  boxes = placed(items, window, _measurer(path), params['gap'], params['leader_after'])
  light = L.picture_is_light()
  colour = L.colour_for(params, light)
  saved = [] if show_both() else _hide_fonts()
  try:
    olex.m(pict_command)
  finally:
    _restore_fonts(saved)
  if os.path.exists(image_path):
    draw(image_path, items, boxes, view[2] * window[1], window, path, colour,
         params['leader_width'])
  return True


def draw(image_path, items, boxes, px_per_a, window, font_file, colour, leader_width=0.025):
  """Draw each label at its box, its own height, into the picture of the
  whole 3D window (any resolution)."""
  from PIL import Image, ImageDraw, ImageFont
  im = Image.open(image_path)
  im.load()
  if im.mode not in ('RGB', 'RGBA'):
    im = im.convert('RGBA')
  iw, ih = im.size
  scale = px_per_a * iw / float(window[0])
  d = ImageDraw.Draw(im)
  fonts = {}
  for b in boxes:
    it = items[b['index']]
    m = L.Measure(font_file, it['height'])
    px = max(4, int(round(m.NOMINAL * it['height'] / float(m.cap) * scale)))
    if px not in fonts:
      try:
        fonts[px] = ImageFont.truetype(font_file, px) if font_file else ImageFont.load_default()
      except OSError:
        fonts[px] = ImageFont.load_default()
    f = fonts[px]
    x0, y0 = b['rect'][:2]
    left = iw / 2.0 + x0 * scale
    base = ih / 2.0 - y0 * scale
    ascent = f.getmetrics()[0] if hasattr(f, 'getmetrics') else px
    d.text((left, base - ascent), it['text'], font=f, fill=colour)
    if b.get('leader'):
      (sx, sy), (ex, ey) = b['leader']
      d.line([(iw / 2.0 + sx * scale, ih / 2.0 - sy * scale),
              (iw / 2.0 + ex * scale, ih / 2.0 - ey * scale)],
             fill=colour, width=max(1, int(round(leader_width * scale))))
  im.save(image_path)


# --- calibration -----------------------------------------------------------------

def find_boxes(image_path, colour=(255, 0, 255), tol=60, min_px=4, join=3):
  """Bounding boxes (x0, y0, x1, y1, pixels) of the magenta text in a picture:
  pixels near the colour, grouped when closer than 'join' pixels."""
  from PIL import Image
  im = Image.open(image_path).convert('RGB')
  w, h = im.size
  px = im.load()
  hit = set()
  for y in range(h):
    for x in range(w):
      r, g, b = px[x, y]
      if abs(r - colour[0]) < tol and abs(g - colour[1]) < tol and abs(b - colour[2]) < tol:
        hit.add((x, y))
  boxes = []
  while hit:
    stack = [hit.pop()]
    xs, ys = [], []
    while stack:
      x, y = stack.pop()
      xs.append(x)
      ys.append(y)
      for dx in range(-join, join + 1):
        for dy in range(-join, join + 1):
          n = (x + dx, y + dy)
          if n in hit:
            hit.remove(n)
            stack.append(n)
    if len(xs) >= min_px:
      boxes.append((min(xs), min(ys), max(xs) + 1, max(ys) + 1, len(xs)))
  return boxes


def _d(it, axis):
  """An item's drag, scaled by perspective like Olex2 does (see size_constant)."""
  return it.get('f', 1.0) * it['drag'][axis]


def fit(items, boxes, window, px_per_a):
  """Match labels to measured boxes (nearest to the expected place) and fit
  size_per_pt, drag_scale, offset_x, offset_y.  Returns (values, matches)."""
  w, h = window
  size, drag, ox, oy = calibration(h)
  pairs = []
  used = set()
  for it in items:
    ex = it['anchor'][0] + drag * _d(it, 0) + ox
    ey = it['anchor'][1] + drag * _d(it, 1) + oy
    best = None
    for k, b in enumerate(boxes):
      if k in used:
        continue
      bx = (b[0] - w / 2.0) / px_per_a
      by = (h / 2.0 - b[3]) / px_per_a
      d = math.hypot(bx - ex, by - ey)
      if best is None or d < best[0]:
        best = (d, k, bx, by, (b[3] - b[1]) / px_per_a)
    if best is not None:
      used.add(best[1])
      pairs.append((it, best[2], best[3], best[4]))
  if not pairs:
    return None, []
  # height per point: the tallest boxes are labels with capitals and digits
  size_per_pt = sorted(hgt / it['pt'] for it, _, _, hgt in pairs)[len(pairs) // 2]
  # bottom left = anchor + s * drag + offset, least squares per axis, shared s;
  # then once more without the matches that do not fit (labels that touch
  # are found as one box)
  def solve(ps):
    # the drag scale is known (calibration()); only the offset is fitted: the
    # median of what is left once anchor and drag are taken off
    s = drag
    rx = sorted(bx - it['anchor'][0] - s * _d(it, 0) for it, bx, _, _ in ps)
    ry = sorted(by - it['anchor'][1] - s * _d(it, 1) for it, _, by, _ in ps)
    return s, rx[len(rx) // 2], ry[len(ry) // 2]

  def residual(p, s, ox, oy):
    it, bx, by, _ = p
    return math.hypot(bx - (it['anchor'][0] + s * _d(it, 0) + ox),
                      by - (it['anchor'][1] + s * _d(it, 1) + oy))
  s, ox, oy = solve(pairs)
  if len(pairs) > 3:
    res = sorted(residual(p, s, ox, oy) for p in pairs)
    limit = max(3 * res[len(res) // 2], 2.0 / px_per_a)
    good = [p for p in pairs if residual(p, s, ox, oy) <= limit]
    if len(good) >= 3 and len(good) < len(pairs):
      pairs = good
      s, ox, oy = solve(pairs)
      size_per_pt = sorted(hgt / it['pt'] for it, _, _, hgt in pairs)[len(pairs) // 2]
  return (size_per_pt, s, ox, oy), pairs


def _lstsq(rows):
  """Solve [a b c] . [s ox oy] = y in the least-squares sense (3x3 normal equations)."""
  n = 3
  A = [[0.0] * n for _ in range(n)]
  B = [0.0] * n
  for a, b, c, y in rows:
    v = (a, b, c)
    for i in range(n):
      B[i] += v[i] * y
      for j in range(n):
        A[i][j] += v[i] * v[j]
  # without varied drags s cannot be told from the offset: keep it fixed
  if A[0][0] < 1e-9 or abs(A[0][0] * A[1][1] - A[0][1] ** 2) < 1e-12:
    return None, (B[1] / A[1][1] if A[1][1] else 0.0), (B[2] / A[2][2] if A[2][2] else 0.0)
  M = [A[i] + [B[i]] for i in range(n)]
  for c in range(n):
    p = max(range(c, n), key=lambda r: abs(M[r][c]))
    M[c], M[p] = M[p], M[c]
    if abs(M[c][c]) < 1e-12:
      return None, 0.0, 0.0
    for r in range(n):
      if r != c:
        f = M[r][c] / M[c][c]
        M[r] = [M[r][k] - f * M[c][k] for k in range(n + 1)]
  return tuple(M[i][n] / M[i][i] for i in range(n))


def calibrate():
  """spy.gui.images.label_calibrate(): measure where and how big Olex2 draws
  the labels (vector mode, labels shown; best with a few labels dragged), and
  keep the result for Ctrl+P."""
  import olex
  import olx
  import tempfile
  from olexFunctions import OV
  if current() != 'vector':
    print("Label calibration: switch to vector mode first (spy.gui.images.label_mode(vector))")
    return None
  # sizes per CalcZoom (see size_constant): right for grown structures too
  items, view, window = screen_labels(per_calczoom=True)
  if not items:
    print("Label calibration: show some labels first ('label', or select bonds and 'label')")
    return None
  path = os.path.join(tempfile.gettempdir(), 'olex2_label_calib.png').replace('\\', '/')
  old = _material('PLabels.Text')
  from gui.theme import glcolours
  olx.SetMaterial('PLabels.Text', glcolours.material(MAGENTA, 2049))
  try:
    olex.m('pict "%s" 1' % path)
  finally:
    if old:
      olx.SetMaterial('PLabels.Text', old)
    else:
      glcolours.apply(restore=True)
  if not os.path.exists(path):
    print("Label calibration: no picture was made")
    return None
  boxes = find_boxes(path)
  from PIL import Image
  with Image.open(path) as im:
    iw, ih = im.size
  # a picture at scale 1 is the window: pixels per Angstrom as on screen
  px_per_a = view[2] * window[1] * iw / float(window[0])
  values, pairs = fit(items, boxes, (iw, ih), px_per_a)
  print("Label calibration: %d labels, %d magenta boxes, %d matched"
        % (len(items), len(boxes), len(pairs)))
  if not values:
    return None
  size_k, s, ox, oy = values
  for key, v in (('calib_size_k', size_k), ('calib_offset_x', ox), ('calib_offset_y', oy)):
    _set(key, round(v, 8))
  olex.m('spy.SaveUserParams()')
  print("  size constant %.6f (atom labels %.3f A at @%d here), drag 1/%d px (from Olex2's "
        "code), offset %.3f, %.3f A" % (size_k, size_k * items[0]['pt'], sizes()[0],
                                        window[1], ox, oy))
  os.remove(path)
  return values
