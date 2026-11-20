"""Read the grown structure of a saved model (.oxm) and turn it into commands.

An .oxm is 'oxm' + a zip with 'model' (an XL text) and 'grid'.  In the model:

  XFiles/0/Lattice/AUnit/residues  the asymmetric unit, atom by atom (label, x y z)
  XFiles/0/Lattice/Matrices        the symmetry operators in use: <symop "1/2-X,..">
  XFiles/0/Lattice/Atoms           every atom drawn: atom_id (position in the
                                   asymmetric unit), matrix_id (position in
                                   Matrices), crd (Cartesian)
  Basis                            the view: matrix, center, zoom
  Visibility atoms=                one bit per drawn atom (base64 + count%8), 0 = hidden

So the picture is a set of (label, operator) pairs (Q-peaks left out); 'sgen <op> <labels>' grows
the same pairs on any model of the same compound in the same setting.

The atom_id order is checked against the coordinates (identity copies must sit
on their asymmetric-unit atom); where it does not hold, the label is found by
position.  No Olex2 imports: tested with test_fromoxm.py.
"""
import base64
import io
import math
import re
import zipfile

TOLERANCE = 0.1  # Angstrom: a drawn atom on the position of its asymmetric-unit atom
IDENTITY = '+X,+Y,+Z'


class SampleError(Exception):
  pass


def read_model(path):
  """The model text of an .oxm file."""
  with open(path, 'rb') as f:
    data = f.read()
  start = data.find(b'PK\x03\x04')
  if start < 0:
    raise SampleError("%s is not a saved model (.oxm)" % path)
  try:
    z = zipfile.ZipFile(io.BytesIO(data[start:]))
    return z.read('model').decode('utf-8', 'replace')
  except (zipfile.BadZipFile, KeyError) as err:
    raise SampleError("cannot read %s: %s" % (path, err))


def _section(text, start, end):
  i = text.find(start)
  if i < 0:
    raise SampleError("the model has no %s" % start.strip('< '))
  j = text.find(end, i)
  return text[i:j if j > 0 else len(text)]


def _attrs(tag):
  return dict(re.findall(r'(\w+)="([^"]*)"', tag))


def _num(v):
  """'18.791(3)' -> 18.791"""
  return float(re.sub(r'\(.*\)', '', v))


def cell_matrix(cell):
  """Fractional -> Cartesian as Olex2 does it: a along x, b in the xy plane."""
  a, b, c = (cell[k] for k in ('a', 'b', 'c'))
  al, be, ga = (math.radians(cell[k]) for k in ('alpha', 'beta', 'gamma'))
  cg, sg = math.cos(ga), math.sin(ga)
  cb, ca = math.cos(be), math.cos(al)
  v = math.sqrt(max(0.0, 1 - ca * ca - cb * cb - cg * cg + 2 * ca * cb * cg))
  return ((a, b * cg, c * cb),
          (0.0, b * sg, c * (ca - cb * cg) / sg),
          (0.0, 0.0, c * v / sg))


def to_cart(m, f):
  return tuple(sum(m[i][j] * f[j] for j in range(3)) for i in range(3))


def apply_symop(op, f):
  """'1/2-X,-1/2+Y,3/2-Z' applied to fractional coordinates."""
  out = []
  env = {'X': f[0], 'Y': f[1], 'Z': f[2]}
  for part in op.upper().split(','):
    if not re.match(r'^[0-9XYZ+\-*/. ]+$', part):
      raise SampleError("not a symmetry operator: %s" % op)
    expr = re.sub(r'(\d+)/(\d+)', r'(\1.0/\2)', part)
    out.append(eval(expr, {'__builtins__': {}}, env))
  return tuple(out)


def _visibility(text, count):
  m = re.search(r'<Visibility [^\n]*?atoms="([^"]+)"', text)
  if not m or len(m.group(1)) % 4 != 1:
    return [True] * count
  s = m.group(1)
  raw = base64.b64decode(s[:-1])
  n = len(raw) * 8 - (8 - int(s[-1]))
  bits = [bool((raw[i // 8] >> (i % 8)) & 1) for i in range(n)]
  return (bits + [True] * count)[:count]


def parse(text):
  """{'cell', 'labels', 'symops', 'drawn': [(label, op, visible)], 'view'}."""
  xf = _section(text, '<Lattice', '\n  <')  # the first file's lattice
  au = _section(xf, '<AUnit', '<Matrices')
  cell_tag = re.search(r'<cell [^\n]*', au)
  if not cell_tag:
    raise SampleError("the model has no cell")
  cell = dict((k, _num(v)) for k, v in _attrs(cell_tag.group(0)).items()
              if k in ('a', 'b', 'c', 'alpha', 'beta', 'gamma'))
  atoms = []
  for tag in re.findall(r'<atom [^\n]*', _section(au, '<residues', '\n    >')):
    a = _attrs(tag)
    if 'label' in a and 'x' in a:
      atoms.append((a['label'], (float(a['x']), float(a['y']), float(a['z'])),
                    a.get('type', '')))
  # the space group: <symm latt="n" <symmop "..."> ...> (SHELX LATT and SYMM)
  symm = re.search(r'<symm latt="(-?\d+)"(.*?)<residues', au, re.S)
  latt = int(symm.group(1)) if symm else 1
  group_ops = re.findall(r'<symmop "([^"]+)"', symm.group(2)) if symm else []
  symops = re.findall(r'<symop "([^"]+)"', _section(xf, '<Matrices', '<Atoms'))
  lat = []
  for tag in re.findall(r'<Atom [^\n]*', _section(xf, '\n    <Atoms', '\n    <Bonds')):
    a = _attrs(tag)
    lat.append((int(a['atom_id']), int(a['matrix_id']),
                tuple(float(x) for x in a['crd'].split(','))))
  if not atoms or not symops or not lat:
    raise SampleError("the model has no grown structure to copy")
  m = cell_matrix(cell)
  carts = {}  # (atom index, op index) -> Cartesian, computed on demand

  def cart(k, op_i):
    if (k, op_i) not in carts:
      carts[(k, op_i)] = to_cart(m, apply_symop(symops[op_i], atoms[k][1]))
    return carts[(k, op_i)]

  def near(p, q):
    return sum((p[i] - q[i]) ** 2 for i in range(3)) < TOLERANCE ** 2

  visible = _visibility(text, len(lat))
  drawn, xyz = [], []
  index = {}  # atom_id as saved -> position in atoms (they differ when the order does)
  for n, (atom_id, op_i, crd) in enumerate(lat):
    if op_i >= len(symops):
      raise SampleError("atom %d uses an unknown operator" % n)
    k = atom_id
    if k >= len(atoms) or not near(cart(k, op_i), crd):
      # the order of the asymmetric unit differs: find the atom by position
      k = next((j for j in range(len(atoms)) if near(cart(j, op_i), crd)), None)
      if k is None:
        raise SampleError("atom %d of the sample matches no atom of its asymmetric unit"
                          % n)
    index[atom_id] = k
    if atoms[k][2].upper() == 'Q':
      continue  # Q-peaks belong to one refinement, not to the compound
    drawn.append((atoms[k][0], symops[op_i], visible[n]))
    xyz.append(crd)
  return {'cell': cell, 'labels': [a[0] for a in atoms if a[2].upper() != 'Q'],
          'au': [a for a in atoms if a[2].upper() != 'Q'], 'latt': latt,
          'group': group_ops,
          'symops': symops, 'drawn': drawn, 'xyz': xyz, 'view': _view(text),
          'planes': _planes(xf, text, atoms, index), 'lines': _lines(text),
          'style': style_text(text)}


def _top_section(text, tag):
  """A top-level item of the model (one space in), up to the next one."""
  m = re.search(r'\n <%s\b' % tag, text)
  if not m:
    return None
  end = re.search(r'\n <\w', text[m.end():])
  return text[m.start() + 1:m.end() + (end.start() if end else len(text) - m.end())]


def style_text(text):
  """The drawing style of the sample as the text of a .glds file, linking no
  scene (a style's LinkFile would load that scene too), or None."""
  s = _top_section(text, 'Style')
  if not s:
    return None
  s = s.lstrip().replace('<Style', '<style', 1)
  s = re.sub(r'LinkFile="[^"]*"', 'LinkFile=""', s, count=1)
  return s.rstrip() + '\n'


# --- the sample's style --------------------------------------------------------
# A saved model holds only the *structure* style (TGXApp::SaveStructureStyle: the
# styles of the objects in the scene, plus atom and bond settings).  It is NOT
# loaded: 'load style' rebuilds every atom from the saved defaults, and the draw
# style set with 'ads'/'telp' (a runtime DS parameter of each atom's style) is
# lost -- ellipsoids became spheres, atoms lost their look (user, 2026-11-14).
# Instead the sample's materials are set live with 'SetMaterial name.primitive'
# on what exists here (style_materials).

class XL:
  """One <Name field="v" "value" ... children ...> item of an Olex2 XL file."""

  def __init__(self, name, fields=None, children=None):
    self.name = name
    self.fields = fields or []      # [(key or None, raw text as in the file)]
    self.children = children or []

  def get(self, key):
    for k, v in self.fields:
      if k == key:
        return v[1:-1] if v.startswith('"') and v.endswith('"') else v
    return None

  def set(self, key, value):
    raw = '"%s"' % value
    for i, (k, _) in enumerate(self.fields):
      if k == key:
        self.fields[i] = (k, raw)
        return
    self.fields.append((key, raw))

  def value(self):
    for k, v in self.fields:
      if k is None:
        return v[1:-1] if v.startswith('"') and v.endswith('"') else v
    return None

  def child(self, name):
    return next((c for c in self.children if c.name == name), None)


_XL_TOKEN = re.compile(r'"[^"]*"|<|>|=|[^\s<>="]+')


def parse_xl(text):
  """The top-level items of XL text."""
  tokens = _XL_TOKEN.findall(text)
  pos = 0

  def item():
    nonlocal pos
    pos += 1  # '<'
    it = XL(tokens[pos])
    pos += 1
    while pos < len(tokens):
      t = tokens[pos]
      if t == '>':
        pos += 1
        return it
      if t == '<':
        it.children.append(item())
        continue
      if pos + 2 < len(tokens) and tokens[pos + 1] == '=':
        it.fields.append((t, tokens[pos + 2]))
        pos += 3
      else:
        it.fields.append((None, t))
        pos += 1
    return it

  out = []
  while pos < len(tokens):
    if tokens[pos] == '<':
      out.append(item())
    else:
      pos += 1
  return out


# entries of the scene, not of the structure: the theme's business, never taken
NOT_STRUCTURE = re.compile(
  r'^(3DFrame|AtomLegend|Background|Ceiling|Console|Cursor|DBasis|DUnitCell\d*|'
  r'Fader|HelpWindow|InfoBox|Labels|PLabels|Selection|Tooltip|XGrid.*|db_label|'
  r'duc_label|facectrl|Grid.*|DSphere|DFrame|GL|Stereo|button|Button|Quad)$')


def style_materials(style_text, structure_only=True):
  """[(entry name, primitive, material)] of the top-level entries of a style
  (a saved model's structure style), material references resolved."""
  items = [i for i in parse_xl(style_text or '') if i.name.lower() == 'style']
  if not items:
    return []
  style = items[0]
  table = dict((p.name, p.value()) for p in (style.child('Materials') or XL('')).children)
  root = style.child('Root')
  subs = root.child('SubStyles') if root else None
  out = []
  for entry in (subs.children if subs else []):
    name = entry.get('Name')
    if structure_only and name and NOT_STRUCTURE.match(name):
      continue
    for prim in entry.children:
      pname = prim.get('PName')
      mat = prim.child('Material')
      if not name or not pname or mat is None:
        continue
      ref = mat.value() or ''
      # a reference into the table: 'style.Materials.Prop3' in a .glds,
      # 'olex_model.Style.Materials.Prop3' in a saved model
      if '.Materials.' in ref:
        ref = table.get(ref.split('.')[-1])
      if ref and ';' in ref:
        out.append((name, pname, ref))
  return out



def _planes(xf, text, atoms, index):
  """[{'name', 'labels'}] one per plane definition (Olex2 draws it again for
  every grown copy whose atoms are all there)."""
  try:
    block = _section(xf, '\n    <Planes', '\n    >')
  except SampleError:
    return []
  defs = {}
  for m in re.finditer(r'<Plane def_id="(\d+)"[^\n]*\n((?:\s+<atom [^\n]*\n)+)', block):
    d = int(m.group(1))
    if d in defs:
      continue
    labels = []
    for t in re.findall(r'<atom [^\n]*', m.group(2)):
      k = index.get(int(_attrs(t).get('a_id', -1)), int(_attrs(t).get('a_id', -1)))
      if 0 <= k < len(atoms):
        labels.append(atoms[k][0])
    defs[d] = labels
  # names: kept under a hash of the definition, in definition order; they can
  # be paired only when every definition has one
  names = re.findall(r'<item id="[^"]*" value="([^"]*)"',
                     (_top_section(text, 'NameRegistry') or '').split('<Atoms')[0])
  ids = sorted(defs)
  if names and len(names) != len(ids):
    print("from_oxm: %d plane names for %d planes: the planes come without names"
          % (len(names), len(ids)))
    names = []
  return [{'name': names[i] if names else '', 'labels': defs[d]} for i, d in enumerate(ids)]


def _lines(text):
  s = _top_section(text, 'Lines') or ''
  out = []
  for m in re.finditer(r'<object "([^"]*)" ([^\n]*)', s):
    a = _attrs(m.group(2))
    try:
      out.append({'name': m.group(1),
                  'base': tuple(float(x) for x in a['base'].split(',')),
                  'edge': tuple(float(x) for x in a['edge'].split(','))})
    except (KeyError, ValueError):
      continue
  return out


def _view(text):
  m = re.search(r'\n <Basis zoom="([^"]+)"\s*<matrix ([^>]*)>\s*<center ([^>]*)>', text)
  if not m:
    return None
  mx, c = _attrs(m.group(2)), _attrs(m.group(3))
  return {'zoom': float(m.group(1)),
          'matrix': [float(mx[k]) for k in ('xx', 'xy', 'xz', 'yx', 'yy', 'yz',
                                             'zx', 'zy', 'zz')],
          'center': [float(c[k]) for k in ('x', 'y', 'z')]}


def cell_differences(a, b, length=0.02, angle=1.0):
  """Cell parameters that differ by more than 2 % (lengths) or 1 degree."""
  out = []
  for k in ('a', 'b', 'c'):
    if abs(a[k] - b[k]) > length * a[k]:
      out.append('%s %.4g vs %.4g' % (k, a[k], b[k]))
  for k in ('alpha', 'beta', 'gamma'):
    if abs(a[k] - b[k]) > angle:
      out.append('%s %.4g vs %.4g' % (k, a[k], b[k]))
  return out


def _norm(op):
  return op.replace(' ', '').upper()


# --- matching atoms by position -------------------------------------------------
# Labels need not agree between two refinements of the same compound.  Atoms
# are paired by where they are: a sample atom and an atom of the model now are
# the same when one is on a symmetry equivalent of the other (space group
# operators, inversion, centring, lattice translations) within a margin, and of
# the same element.  An atom the model holds at another equivalent position is
# moved there first ('sgen -m'), so that growing gives the sample's picture.

CENTRING = {1: [(0, 0, 0)], 2: [(0, 0, 0), (.5, .5, .5)],
            3: [(0, 0, 0), (2 / 3., 1 / 3., 1 / 3.), (1 / 3., 2 / 3., 2 / 3.)],
            4: [(0, 0, 0), (0, .5, .5), (.5, 0, .5), (.5, .5, 0)],
            5: [(0, 0, 0), (0, .5, .5)], 6: [(0, 0, 0), (.5, 0, .5)],
            7: [(0, 0, 0), (.5, .5, 0)]}
DEFAULT_MARGIN = 0.5  # Angstrom


def symop_matrix(op):
  """'1/2-X,1/2+Y,1/2-Z' -> (3x3 rows, translation)."""
  t = apply_symop(op, (0.0, 0.0, 0.0))
  cols = [apply_symop(op, e) for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
  rows = [[round(cols[j][i] - t[i]) for j in range(3)] for i in range(3)]
  return rows, t


def group(symops, latt):
  """Every operator (rows, translation) of the space group: identity, the
  SYMM operators, their inverses when centrosymmetric (LATT > 0), each with
  the centring translations."""
  base = [([[1, 0, 0], [0, 1, 0], [0, 0, 1]], (0.0, 0.0, 0.0))]
  base += [symop_matrix(op) for op in symops]
  if latt > 0:
    base += [([[-v for v in r] for r in R], tuple(-x for x in t)) for R, t in base]
  out = []
  for R, t in base:
    for c in CENTRING.get(abs(latt), CENTRING[1]):
      out.append((R, tuple(t[i] + c[i] for i in range(3))))
  return out


def _apply(R, t, f):
  return tuple(sum(R[i][j] * f[j] for j in range(3)) + t[i] for i in range(3))


def element(label_or_type):
  m = re.match(r'([A-Za-z][a-z]?)', label_or_type or '')
  return m.group(1).capitalize() if m else ''


def format_symop(R, t):
  """(rows, translation) -> '1/2-X,-1+Y,+Z', as Olex2 writes operators."""
  from fractions import Fraction
  parts = []
  for i in range(3):
    s = ''
    tf = Fraction(t[i]).limit_denominator(12)
    if tf:
      s += str(tf)
    for j, ax in enumerate('XYZ'):
      if R[i][j]:
        s += ('+' if R[i][j] > 0 else '-') + ax
    parts.append(s)
  return ','.join(parts)


def match_atoms(sample, current, cell, margin=DEFAULT_MARGIN):
  """Pair the sample's atoms with the model's by position.
  current: [(label, frac, type)].  Returns (pairs, unmatched sample labels,
  unmatched model labels); pairs = {sample label: (model label, move, distance)}
  where move is the operator ('...' string) that takes the model's atom onto
  the sample's position, or None when it is there already."""
  m = cell_matrix(cell)
  ops = group(sample.get('group', []), sample.get('latt', 1))
  candidates = []
  for s_label, s_frac, s_type in sample['au']:
    s_el = element(s_type or s_label)
    for c_label, c_frac, c_type in current:
      if element(c_type or c_label) != s_el:
        continue
      best = None
      for k, (R, t) in enumerate(ops):
        p = _apply(R, t, c_frac)
        d = [p[i] - s_frac[i] for i in range(3)]
        n = [round(x) for x in d]
        cart = to_cart(m, [d[i] - n[i] for i in range(3)])
        dist = math.sqrt(sum(x * x for x in cart))
        if best is None or dist < best[0]:
          best = (dist, k, n)
        if dist < 1e-3:
          break
      if best[0] <= margin:
        candidates.append((best[0], s_label, c_label, best[1], best[2]))
  candidates.sort()
  pairs, used = {}, set()
  for dist, s_label, c_label, k, n in candidates:
    if s_label in pairs or c_label in used:
      continue
    R, t = ops[k]
    shift = tuple(t[i] - n[i] for i in range(3))
    identity = (k == 0 and not any(n))
    pairs[s_label] = (c_label, None if identity else format_symop(R, shift), dist)
    used.add(c_label)
  unmatched_s = [l for l, _, _ in sample['au'] if l not in pairs]
  unmatched_c = [l for l, _, _ in current if l not in used]
  return pairs, unmatched_s, unmatched_c


def renamed(pairs):
  """[(model label, sample label)] of the pairs whose names differ."""
  return sorted((c, s) for s, (c, _, _) in pairs.items() if c.upper() != s.upper())


def rename_commands(pairs, existing):
  """'name' commands that give the model's atoms the sample's names, through
  temporary names, so that swapped or taken names do not get in each other's
  way; hydrogen atoms last (naming a parent may rename its H atoms)."""
  todo = renamed(pairs)
  if not todo:
    return []
  taken = set(l.upper() for l in existing) | set(s.upper() for _, s in todo)
  temps, counter = {}, 0
  digits = '0123456789abcdefghijklmnopqrstuvwxyz'
  for c, s in todo:
    el = element(c)
    while True:
      counter += 1
      tag, n = '', counter
      while n:
        tag = digits[n % 36] + tag
        n //= 36
      tmp = el + 'Z' + tag  # only for a moment: may be longer than SHELX's 4
      if tmp.upper() not in taken:
        break
    taken.add(tmp.upper())
    temps[c] = tmp
  is_h = lambda l: element(l) in ('H', 'D')
  first = ['name %s %s' % (c, temps[c]) for c, _ in todo]
  second = ['name %s %s' % (temps[c], s) for c, s in sorted(todo, key=lambda p: is_h(p[0]))]
  return first + second


PARTS = ('grow', 'view', 'styles', 'planes', 'lines')
LINE_SNAP = 0.1  # Angstrom: a line end this close to a drawn atom follows that atom


def line_end(sample, p, current=None, current_cell=None):
  """Where a line end of the sample is in the model now: on the same atom
  (label and operator) when it sat on one, else where it was."""
  if current and current_cell:
    best, best_d = None, LINE_SNAP ** 2
    for (label, op, _), q in zip(sample['drawn'], sample['xyz']):
      d = sum((p[i] - q[i]) ** 2 for i in range(3))
      if d < best_d:
        best, best_d = (label, op), d
    if best and best[0].upper() in current:
      return to_cart(cell_matrix(current_cell),
                     apply_symop(best[1], current[best[0].upper()]))
  return p


def positions_after(pairs, current):
  """{SAMPLE LABEL: fractional position} of the paired model atoms once moved
  onto the sample's positions.  current: [(label, frac, type)]."""
  frac = dict((l, f) for l, f, _ in current)
  out = {}
  for s, (c, move, _) in pairs.items():
    if c in frac:
      f = frac[c]
      if move:
        R, t = symop_matrix(move)
        f = _apply(R, t, f)
      out[s.upper()] = f
  return out


def commands(sample, present, parts=PARTS, chunk=40, current=None, current_cell=None,
             pairs=None):
  """(commands, missing labels).  present: the labels of the model in Olex2
  (case does not matter).  parts (PARTS):
    planes  the named planes, defined before growing so every copy gets one
    grow    each operator's atoms; what was hidden, where a label has one copy
    lines   the named lines, their ends on the same atoms ({LABEL: frac} in
            current, with current_cell) or where they were
    view    orientation, centre and zoom
  pairs (match_atoms): the model's atoms by position instead of by label;
  atoms on another equivalent position are moved first ('sgen -m').
  'styles' is not done here: __init__._apply_materials, once the planes and
  lines exist."""
  parts = set(parts)
  if pairs is not None:
    have = dict((s.upper(), c) for s, (c, _, _) in pairs.items())
  else:
    have = dict((l.upper(), l) for l in present)
  missing = sorted(set(l for l, _, _ in sample['drawn'] if l.upper() not in have))
  cmds = []
  if parts & {'grow', 'planes'}:
    cmds.append('fuse')
    moves = {}
    for s, (c, move, _) in sorted((pairs or {}).items()):
      if move:
        moves.setdefault(move, []).append(c)
    for move, labels in sorted(moves.items()):
      for i in range(0, len(labels), chunk):
        cmds.append('sgen -m %s %s' % (move, ' '.join(labels[i:i + chunk])))
  if 'planes' in parts:
    for p in sample.get('planes', []):
      labels = [have[l.upper()] for l in p['labels'] if l.upper() in have]
      if len(labels) >= 3:
        cmds.append('mpln %s%s' % ('-n=%s ' % p['name'] if p['name'] else '',
                                   ' '.join(labels)))
  if 'grow' in parts:
    by_op = {}
    for label, op, _ in sample['drawn']:
      if label.upper() in have and _norm(op) != IDENTITY:
        by_op.setdefault(op, [])
        if have[label.upper()] not in by_op[op]:
          by_op[op].append(have[label.upper()])
    for op in sample['symops']:
      labels = by_op.get(op, [])
      for i in range(0, len(labels), chunk):
        cmds.append('sgen %s %s' % (op, ' '.join(labels[i:i + chunk])))
    copies = {}
    for label, _, _ in sample['drawn']:
      copies[label.upper()] = copies.get(label.upper(), 0) + 1
    hidden = [have[l.upper()] for l, _, vis in sample['drawn']
              if not vis and l.upper() in have and copies[l.upper()] == 1]
    if hidden:
      cmds.append('hide -b %s' % ' '.join(hidden))
  if 'lines' in parts:
    for ln in sample.get('lines', []):
      a = line_end(sample, ln['base'], current, current_cell)
      b = line_end(sample, ln['edge'], current, current_cell)
      cmds.append('line %s%s' % ('-n=%s ' % ln['name'] if ln['name'] else '',
                                 ' '.join('%.6f' % x for x in tuple(a) + tuple(b))))
  v = sample.get('view')
  if 'view' in parts and v:
    mx = v['matrix']
    # matr transposes the nine numbers it gets
    cmds.append('matr %s' % ' '.join('%.6f' % mx[i] for i in (0, 3, 6, 1, 4, 7, 2, 5, 8)))
    cmds.append('center %s' % ' '.join('%.6f' % -c for c in v['center']))
    cmds.append('gl.Zoom -a %.6f' % v['zoom'])
  return cmds, missing
