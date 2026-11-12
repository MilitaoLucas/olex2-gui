"""Tidy PART numbers: disorder pairs share 1/2, and need 3/4 only when they must.

A unit is the pair of PARTs one free variable links: the part with the positive
reference ('21') goes to the odd number, the part with the negative one ('-21')
to the even number.  Units go to the lowest set (1/2, then 3/4, ...) that holds
nothing they would bond to: atoms in the same PART bond, atoms in different
PARTs do not, so two units can share numbers only if their same-sign atoms stay
further apart than the sum of their radii + 0.5 A (SHELXL's CONN default),
symmetry equivalents included.

Left alone: PART 0, negative PARTs, a part with fixed occupancies or several
variables, a part named by BIND, and a variable used outside occupancies (three-
way disorder with SUMP).  The numbers of positive parts left alone stay reserved.

Works on the text of a .res/.ins and imports nothing from Olex2.
"""
import collections
import itertools
import math
import re

try:
  from . import fvar_sanitise as fs
except ImportError:  # tests: imported without the package
  import fvar_sanitise as fs

BOND_MARGIN = 0.5
DEFAULT_RADIUS = 2.0  # an element not listed: rather too many clashes than a false bond
RADII = dict(
  B=.84, C=.76, N=.71, O=.66, F=.57, NA=1.66, MG=1.41, AL=1.21, SI=1.11, P=1.07, S=1.05, CL=1.02,
  K=2.03, CA=1.76, SC=1.70, TI=1.60, V=1.53, CR=1.39, MN=1.39, FE=1.32, CO=1.26, NI=1.24,
  CU=1.32, ZN=1.22, GA=1.22, GE=1.20, AS=1.19, SE=1.20, BR=1.20, RB=2.20, SR=1.95, Y=1.90,
  ZR=1.75, NB=1.64, MO=1.54, RU=1.46, RH=1.42, PD=1.39, AG=1.45, CD=1.44, IN=1.42, SN=1.39,
  SB=1.39, TE=1.38, I=1.39, CS=2.44, BA=2.15, HF=1.75, TA=1.70, W=1.62, RE=1.51, OS=1.44,
  IR=1.41, PT=1.36, AU=1.36, HG=1.32, TL=1.45, PB=1.46, BI=1.48)
CENTRING = {1: [(0, 0, 0)], 2: [(0, 0, 0), (.5, .5, .5)],
            3: [(0, 0, 0), (2 / 3., 1 / 3., 1 / 3.), (1 / 3., 2 / 3., 2 / 3.)],
            4: [(0, 0, 0), (0, .5, .5), (.5, 0, .5), (.5, .5, 0)],
            5: [(0, 0, 0), (0, .5, .5)], 6: [(0, 0, 0), (.5, 0, .5)], 7: [(0, 0, 0), (.5, .5, 0)]}

Unit = collections.namedtuple('Unit', 'pos neg variable')
Plan = collections.namedtuple('Plan', 'mapping rows')
# a row: the unit, its new numbers, and the set it could not share (or None)
Row = collections.namedtuple('Row', 'unit target blocked_by')


class Model(object):
  """What the text says about cell, symmetry and the atoms of each PART."""

  def __init__(self, text):
    self.lines = text.splitlines(True)
    self.cell = None
    self.latt = 1
    self.symm = []
    self.sfac = []
    self.bind = set()
    self.atoms = collections.defaultdict(list)   # part -> [(element, xyz)]
    self.codes = collections.defaultdict(set)    # part -> {(variable or None, sign)}
    self.info = collections.defaultdict(lambda: {'residues': [], 'atoms': 0, 'first': ''})
    self._read()
    self.other = fs._read(self.lines)[2]
    self.values = fs._read(self.lines)[0]

  def _read(self):
    part, residue = 0, ''
    for card in fs._cards(self.lines):
      tokens = fs._tokens(self.lines, card)
      if not tokens:
        continue
      word = tokens[0].split('_')[0].upper()
      if word == 'CELL':
        self.cell = [float(t) for t in tokens[2:8]]
      elif word == 'LATT':
        self.latt = int(tokens[1])
      elif word == 'SYMM':
        self.symm.append(''.join(tokens[1:]))
      elif word == 'SFAC':
        self.sfac += [t.upper() for t in tokens[1:] if t.isalpha()]
      elif word == 'BIND':
        self.bind.update(int(t) for t in tokens[1:] if re.match(r'^-?\d+$', t))
      elif word == 'RESI':
        residue = ' '.join(tokens[1:])
      elif word == 'PART':
        part = int(tokens[1]) if len(tokens) > 1 else 0
      elif fs._is_atom(tokens) and part:
        self._atom(tokens, part, residue)

  def _atom(self, tokens, part, residue):
    code = float(tokens[5])
    used = fs.decode(code)
    self.codes[part].add((used[0], code > 0) if used else (None, True))
    d = self.info[part]
    d['atoms'] += 1
    d['first'] = d['first'] or tokens[0]
    if residue and residue not in d['residues']:
      d['residues'].append(residue)
    index = int(tokens[1]) - 1
    element = self.sfac[index] if 0 <= index < len(self.sfac) else ''
    if element not in ('H', 'D'):
      xyz = [math.fmod(float(t), 10) if abs(float(t)) >= 5 else float(t) for t in tokens[2:5]]
      self.atoms[part].append((element, xyz))

  def operators(self):
    """All symmetry operators as (3x3 matrix, translation)."""
    ops = [([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0])] + [_parse_symm(s) for s in self.symm]
    if self.latt > 0:
      ops += [([[-x for x in row] for row in m], [-x for x in t]) for m, t in ops]
    out = []
    for m, t in ops:
      for c in CENTRING.get(abs(self.latt), CENTRING[1]):
        out.append((m, [t[i] + c[i] for i in range(3)]))
    return out


def _parse_symm(text):
  matrix, translation = [], []
  for part in text.upper().split(','):
    row, shift = [0, 0, 0], 0.0
    for sign, number, axis in re.findall(r'([+-]?)(\d*\.?\d*(?:/\d+)?)([XYZ]?)', part):
      if not number and not axis:
        continue
      s = -1 if sign == '-' else 1
      if axis:
        row['XYZ'.index(axis)] = s
      else:
        a, _, b = number.partition('/')
        shift += s * float(a) / (float(b) if b else 1)
    matrix.append(row)
    translation.append(shift)
  return matrix, translation


def _metric(cell):
  a, b, c = cell[:3]
  ca, cb, cg = (math.cos(math.radians(x)) for x in cell[3:6])
  return [[a * a, a * b * cg, a * c * cb], [a * b * cg, b * b, b * c * ca],
          [a * c * cb, b * c * ca, c * c]]


def _bonded(model, atoms_a, atoms_b):
  """Would any atom of a bond to any atom of b, or to a symmetry copy of one?"""
  if not atoms_a or not atoms_b or not model.cell:
    return False
  g = _metric(model.cell)
  ops = model.operators()
  shifts = list(itertools.product((-1, 0, 1), repeat=3))
  for element_b, xyz in atoms_b:
    rb = RADII.get(element_b, DEFAULT_RADIUS)
    for m, t in ops:
      copy = [sum(m[i][j] * xyz[j] for j in range(3)) + t[i] for i in range(3)]
      for element_a, other in atoms_a:
        limit = rb + RADII.get(element_a, DEFAULT_RADIUS) + BOND_MARGIN
        base = [other[i] - copy[i] for i in range(3)]
        base = [d - round(d) for d in base]
        for s in shifts:
          d = [base[i] + s[i] for i in range(3)]
          d2 = sum(d[i] * g[i][j] * d[j] for i in range(3) for j in range(3))
          if d2 < limit * limit:
            return True
  return False


def _find_units(model):
  """(units sorted by lowest number, positive numbers that must stay)."""
  reserved = set()
  by_variable = collections.defaultdict(lambda: ([], []))
  for part, codes in model.codes.items():
    code = next(iter(codes))
    if part < 0:
      continue
    if len(codes) != 1 or code[0] is None or code[0] in model.other or part in model.bind:
      reserved.add(part)
    else:
      by_variable[code[0]][0 if code[1] else 1].append(part)
  units = []
  for variable, (pos, neg) in by_variable.items():
    pos, neg = sorted(pos), sorted(neg)
    for p in list(pos):  # neighbours belong together
      partner = next((n for n in neg if abs(n - p) == 1), None)
      if partner is not None:
        units.append(Unit(p, partner, variable))
        pos.remove(p)
        neg.remove(partner)
    while pos and neg:
      units.append(Unit(pos.pop(0), neg.pop(0), variable))
    units += [Unit(p, None, variable) for p in pos] + [Unit(None, n, variable) for n in neg]
  return sorted(units, key=lambda u: min(x for x in u[:2] if x is not None)), reserved


def key(unit):
  """A unit's name, stable between the dialog and the plan."""
  return min(x for x in unit[:2] if x is not None)


def could_change(text):
  """Cheap test for the button, without distances: is any unit not at 1/2?"""
  units, _ = _find_units(Model(text))
  return any(u.pos not in (None, 1) or u.neg not in (None, 2) for u in units)


def plan(text, exclude=()):
  """What to renumber, or None if nothing changes; exclude holds unit keys to leave."""
  model = Model(text)
  units, reserved = _find_units(model)
  kept = [u for u in units if key(u) in exclude]
  for u in kept:
    reserved.update(x for x in u[:2] if x is not None)
  sets = collections.defaultdict(list)
  mapping, rows = {}, []
  for unit in (u for u in units if key(u) not in exclude):
    k, blocked = 0, None
    while True:
      numbers = (2 * k + 1, 2 * k + 2)
      clash = next((o for o in sets[k]
                    if _bonded(model, model.atoms[unit.pos], model.atoms[o.pos])
                    or _bonded(model, model.atoms[unit.neg], model.atoms[o.neg])), None)
      if clash is None and not reserved.intersection(numbers):
        break
      if clash is not None and blocked is None:
        blocked = clash
      k += 1
    sets[k].append(unit)
    target = (numbers[0] if unit.pos is not None else None,
              numbers[1] if unit.neg is not None else None)
    for old, new in zip(unit[:2], target):
      if old is not None and old != new:
        mapping[old] = new
    rows.append(Row(unit, target, blocked))
  return Plan(mapping, rows) if mapping else None


def apply(text, p):
  """The .res text with the PARTs renumbered."""
  lines = text.splitlines(True)
  out = list(lines)
  for card in fs._cards(lines):
    tokens = fs._tokens(lines, card)
    if tokens and tokens[0].upper() == 'PART' and len(tokens) > 1:
      new = p.mapping.get(int(tokens[1]))
      if new is not None:
        out[card[0]] = fs._replace_token(lines[card[0]], 1, str(new))
  return ''.join(out)


def _pair(a, b):
  return '/'.join(str(x) for x in (a, b) if x is not None)


def describe(p):
  return ['PART %s to %s' % (_pair(r.unit.pos, r.unit.neg), _pair(*r.target))
          for r in p.rows if r.target != r.unit[:2]]


def tick_name(unit):
  return 'PART_TICK_%d' % key(unit)


def changing(p):
  """The rows that change something, which are the ones with a tick."""
  return [r for r in p.rows if r.target != r.unit[:2]]


def page(text, form, p):
  """The dialog: a tick for every pair that would be renumbered."""
  model = Model(text)
  current = plan(text)
  rows = []
  for r in changing(current):
    info = model.info[key(r.unit)]
    where = []
    if info['residues']:
      where.append('residue %s' % ', '.join(info['residues']))
    where.append('FV %d' % r.unit.variable)
    where.append('from %s' % info['first'])
    if r.blocked_by is not None:
      where.append('cannot share %s: atoms would bond' % _pair(r.blocked_by.pos, r.blocked_by.neg))
    rows.append(form.row(
      form.checkbox(tick_name(r.unit), p, checked=True) + ' PART %s' % _pair(*r.unit[:2]),
      'becomes <b>%s</b> &nbsp; <font color="%s">%s</font>'
      % (_pair(*r.target), p['muted'], ', '.join(where)), p, label_width='26%'))
  body = form.section('PARTs', rows, p) + form.spacer() + form.buttons(
    [form.button('Leave PARTs', 'spy.gui.sanitise_FVARs_close(False)', p, width=120)],
    [form.button('Renumber ticked', 'spy.gui.sanitise_FVARs_close(True)', p, primary=True, width=130)])
  return form.page('Sanitise PARTs', body, p, intro=(
    'Disorder pairs can share PART 1/2 unless their atoms would then bond to each other. '
    'The part with the positive free variable reference becomes the odd number. Only the '
    'numbers change, not the model.'))
