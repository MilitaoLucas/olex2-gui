"""
gui/moiety/connectivity.py

Works out the fragments with metals disconnected, from the bonds in the
refinement model. Everything here only reads: no CONN instruction is issued,
so the connectivity of the structure stays exactly as the user has set it.

A 'piece' is a set of asymmetric unit atoms bonded to each other once metals
are left out; each metal is a piece of its own. The symmetry operators on the
bonds tell how the piece completes itself: half a molecule on an inversion
centre has a bond to its own inverted copy, so it counts twice per molecule,
and the asymmetric unit holds half a molecule.

No Olex2 import here, so all of this can be tested outside Olex2.
"""

from __future__ import annotations

import re
from fractions import Fraction
from math import gcd

from .charges import _METALS
from .parser import _element_order

_IDENTITY = (((1, 0, 0), (0, 1, 0), (0, 0, 1)), (Fraction(0), Fraction(0), Fraction(0)))
_MAX_GROUP = 192   # the largest crystallographic group, with centring
_SITE_TOLERANCE = 0.01


# ---------------------------------------------------------------------------
# Symmetry operators: (rotation rows, translation mod 1)
# ---------------------------------------------------------------------------

def make_op(rows, translation):
  rotation = tuple(tuple(int(round(v)) for v in row) for row in rows)
  return (rotation, tuple(Fraction(float(t)).limit_denominator(24) % 1 for t in translation))


def _compose(a, b):
  """The operator a applied after b."""
  rotation = tuple(
      tuple(sum(a[0][i][k] * b[0][k][j] for k in range(3)) for j in range(3))
      for i in range(3))
  translation = tuple(
      (sum(a[0][i][k] * b[1][k] for k in range(3)) + a[1][i]) % 1
      for i in range(3))
  return (rotation, translation)


def _inverse(op):
  power = op
  for _ in range(_MAX_GROUP):
    following = _compose(power, op)
    if following == _IDENTITY:
      return power
    power = following
  if op == _IDENTITY:
    return op
  raise ValueError(f"Symmetry operator without a finite order: {op}")


def _closure(generators):
  group = {_IDENTITY}
  todo = list(generators)
  while todo:
    g = todo.pop()
    if g in group:
      continue
    new = {g} | {_compose(g, h) for h in group} | {_compose(h, g) for h in group}
    group.add(g)
    todo.extend(new - group)
    if len(group) > _MAX_GROUP:
      raise ValueError("The symmetry operators on the bonds do not form a group")
  return group


def _fixes(op, xyz):
  """True if op maps the position onto itself, or onto a lattice-translated copy."""
  for i in range(3):
    moved = sum(op[0][i][k] * xyz[k] for k in range(3)) + float(op[1][i])
    delta = (moved - xyz[i]) % 1
    if min(delta, 1 - delta) > _SITE_TOLERANCE:
      return False
  return True


# ---------------------------------------------------------------------------
# Reading the refinement model
# ---------------------------------------------------------------------------

def atoms_from_model(model):
  """
  Flatten olex_core.GetRefinementModel(True) to one dict per atom: index in
  the list is what 'neighbours' refer to. A neighbour is either an atom index
  or a tuple (index, distance, (row, row, row, translation)).
  """
  atoms = []
  for residue in model['aunit']['residues']:
    number = residue.get('number')
    default = residue.get('class', 'default') == 'default'
    for a in residue['atoms']:
      label = str(a['label'])
      neighbours = []
      for b in a.get('neighbours', ()):
        if isinstance(b, tuple):
          neighbours.append((b[0], make_op(b[2][:3], b[2][3])))
        else:
          neighbours.append((b, _IDENTITY))
      atoms.append({
          'label':      label,
          'name':       label if default else f"{label}_{number}",
          'type':       str(a['type']),
          'occu':       float(a['occu'][0]),
          'crd':        tuple(float(v) for v in a['crd'][0]),
          'neighbours': neighbours,
      })
  return atoms


def _chemical_weight(atom, group_ops):
  """
  How much of an atom one displayed copy is. The model holds the occupancy as
  in the ins file, so 0.5 for a full atom on an inversion centre: scale by the
  site symmetry. Capped at 1, which also makes it safe if an occupancy already
  is the chemical one.
  """
  site_order = sum(1 for g in group_ops if _fixes(g, atom['crd'])) if group_ops else 1
  return min(1.0, atom['occu'] * max(site_order, 1))


# ---------------------------------------------------------------------------
# Pieces
# ---------------------------------------------------------------------------

def find_pieces(atoms, group_ops=None):
  """
  Split the atoms into pieces, metals disconnected. group_ops: all operators of
  the space group as make_op() tuples; without them, atoms on special positions
  that have no bond to their own copy are taken for general ones.

  Each piece: atoms (indices), copies ({index: displayed copies per piece}),
  counts ({element: atoms per piece}) and per_au (pieces per asymmetric unit).
  """
  usable = [i for i, a in enumerate(atoms) if a['type'] not in ('Q', 'q')]
  is_metal = {i: atoms[i]['type'].capitalize() in _METALS for i in usable}

  seen = set()
  pieces = []
  for start in usable:
    if start in seen:
      continue
    seen.add(start)
    placed = {start: _IDENTITY}
    generators = []
    todo = [start]
    while todo:
      u = todo.pop()
      for v, op in atoms[u]['neighbours']:
        if v not in is_metal or is_metal[u] or is_metal[v]:
          continue
        reached = _compose(placed[u], op)
        if v in placed:
          generator = _compose(reached, _inverse(placed[v]))
          if generator != _IDENTITY:
            generators.append(generator)
        else:
          placed[v] = reached
          seen.add(v)
          todo.append(v)

    # Symmetry of the piece: closes through its bonds, or it lies on the
    # element as a whole, such as a molecule entirely in a mirror plane.
    members = sorted(placed)
    on_element = [g for g in (group_ops or ())
                  if all(_fixes(g, atoms[i]['crd']) for i in members)]
    symmetry = _closure(generators + on_element)

    copies = {}
    counts = {}
    for i in members:
      n = len(symmetry) // max(1, sum(1 for g in symmetry if _fixes(g, atoms[i]['crd'])))
      copies[i] = n
      element = atoms[i]['type'].capitalize()
      counts[element] = counts.get(element, 0) + n * _chemical_weight(atoms[i], group_ops)
    pieces.append({
        'atoms':  members,
        'copies': copies,
        'counts': counts,
        'per_au': Fraction(1, len(symmetry)),
    })
  return pieces


def _body(counts):
  rounded = {e: round(n, 3) for e, n in counts.items() if round(n, 3) > 0}
  return ' '.join(sym if rounded[sym] == 1 else f"{sym}{rounded[sym]:g}"
                  for sym in _element_order(rounded))


def _join(merged):
  tokens = []
  for body, n in merged.items():
    if n == 1:
      tokens.append(body)
    elif Fraction(n).denominator == 1:
      tokens.append(f"{int(n)}({body})")
    else:
      tokens.append(f"{float(n):g}({body})")
  return ', '.join(tokens)


def disconnected_moiety(pieces):
  """Moiety string of the whole structure, in whole formula units."""
  merged = {}
  for piece in pieces:
    body = _body(piece['counts'])
    if body:
      merged[body] = merged.get(body, 0) + piece['per_au']
  scale = 1
  for n in merged.values():
    denominator = Fraction(n).denominator
    scale = scale * denominator // gcd(scale, denominator)
  return _join({body: n * scale for body, n in merged.items()})


def _atom_lookup(atoms):
  """{lower-case name: atom index}; a label shared between residues maps to None."""
  lookup = {}
  for i, a in enumerate(atoms):
    lookup[a['name'].lower()] = i
    label = a['label'].lower()
    lookup[label] = None if label in lookup and lookup[label] != i else i
  return lookup


def displayed_moiety(pieces, atoms, names, group_ops=None):
  """
  Moiety string of what is displayed. names: one name for each displayed atom,
  from xf.latt.GetFragmentAtoms. Complete pieces are counted as such, the atoms
  left over from a piece that is only partly displayed form a fragment of their
  own. Not reduced to formula units: this is what is there.

  Raises ValueError if a name does not identify exactly one atom.
  """
  lookup = _atom_lookup(atoms)
  shown = {}
  for name in names:
    key = re.sub(r'_\$\d+$', '', name.strip()).lower()
    # Q peaks are in the lattice but not in the model; no element starts with Q
    if not key or key.startswith('q'):
      continue
    i = lookup.get(key, -1)
    if i == -1:
      i = lookup.get(key.split('_')[0], -1)
    if i == -1:
      raise ValueError(f"unknown atom {name!r}")
    if i is None:
      raise ValueError(f"atom name {name!r} is used in more than one residue")
    if atoms[i]['type'] not in ('Q', 'q'):
      shown[i] = shown.get(i, 0) + 1

  merged = {}
  for piece in pieces:
    members = piece['atoms']
    whole = min(shown.get(i, 0) // piece['copies'][i] for i in members)
    if whole:
      body = _body(piece['counts'])
      merged[body] = merged.get(body, 0) + whole
    rest = {}
    for i in members:
      left = shown.get(i, 0) - whole * piece['copies'][i]
      if left:
        element = atoms[i]['type'].capitalize()
        rest[element] = rest.get(element, 0) + left * _chemical_weight(atoms[i], group_ops)
    if rest:
      body = _body(rest)
      merged[body] = merged.get(body, 0) + 1
  return _join(merged)
