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

One exception to leaving metals out: a metal with only single-atom ligands whose
formula is a known ion (charges.METAL_IONS), such as chromate, is one piece. In
those ions the bonds to the metal are what holds the ion together: split, a
chromate would be Cr and 4 O, and its charge could not be looked up.

No Olex2 import here, so all of this can be tested outside Olex2.
"""

from __future__ import annotations

import re
from fractions import Fraction
from math import gcd

from .charges import _METALS, METAL_IONS
from .parser import _element_order, split_occupancy

_IDENTITY = (((1, 0, 0), (0, 1, 0), (0, 0, 1)), (Fraction(0), Fraction(0), Fraction(0)))
_MAX_GROUP = 192   # the largest crystallographic group, with centring
_SITE_TOLERANCE = 0.01
_ION_LIGANDS = frozenset(('O', 'S', 'Se', 'N', 'F', 'Cl', 'Br', 'I'))


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

def _both_ways(atoms):
  """The bonds of each atom, also where the model lists a bond at one end only."""
  bonds = [list(a['neighbours']) for a in atoms]
  for u, a in enumerate(atoms):
    for v, op in a['neighbours']:
      if 0 <= v < len(atoms) and (u, _inverse(op)) not in bonds[v]:
        bonds[v].append((u, _inverse(op)))
  return bonds


def _grow(start, bonds, joined):
  """Atoms reached from start: ({index: operator}, symmetry generators of the piece)."""
  placed = {start: _IDENTITY}
  generators = []
  todo = [start]
  while todo:
    u = todo.pop()
    for v, op in bonds[u]:
      if not joined(u, v):
        continue
      reached = _compose(placed[u], op)
      if v in placed:
        generator = _compose(reached, _inverse(placed[v]))
        if generator != _IDENTITY:
          generators.append(generator)
      else:
        placed[v] = reached
        todo.append(v)
  return placed, generators


def _make_piece(atoms, placed, generators, group_ops, centres=()):
  """
  Symmetry of the piece: closes through its bonds, or it lies on the element as
  a whole, such as a molecule entirely in a mirror plane. All ligands of an ion
  are in the ion, so the site symmetry of its metal centres counts as well.
  """
  members = sorted(placed)
  on_element = [g for g in (group_ops or ())
                if all(_fixes(g, atoms[i]['crd']) for i in members)
                or any(_fixes(g, atoms[i]['crd']) for i in centres)]
  symmetry = _closure(generators + on_element)

  copies = {}
  counts = {}
  for i in members:
    n = len(symmetry) // max(1, sum(1 for g in symmetry if _fixes(g, atoms[i]['crd'])))
    copies[i] = n
    element = atoms[i]['type'].capitalize()
    counts[element] = counts.get(element, 0) + n * _chemical_weight(atoms[i], group_ops)
  return {
      'atoms':  members,
      'copies': copies,
      'counts': counts,
      'per_au': Fraction(1, len(symmetry)),
  }


def _ion_atoms(start, atoms, bonds, is_metal):
  """
  The metal start, the metals of its element bridged to it, their ligands and
  the H on those; None if a metal has anything but a single-atom ligand. Bonds
  to other metals do not count: a chromate O may also touch a copper.
  """
  def known(v):
    return v in is_metal

  def is_ligand(v):
    return (atoms[v]['type'].capitalize() in _ION_LIGANDS
            and all(atoms[w]['type'] == 'H' or is_metal[w] for w, _ in bonds[v] if known(w)))

  element = atoms[start]['type']
  found = {start}
  todo = [start]
  while todo:
    u = todo.pop()
    for v, _ in bonds[u]:
      if not known(v) or v in found:
        continue
      if is_metal[u]:
        if is_metal[v]:
          continue
        if not is_ligand(v):
          return None
        found.add(v)
        todo.append(v)
      elif atoms[v]['type'] == 'H':
        found.add(v)
      elif atoms[v]['type'] == element:
        found.add(v)
        todo.append(v)
  return found


def _find_ions(atoms, bonds, is_metal, group_ops):
  """The sets of atoms that form a known ion. A ligand claimed twice stays out."""
  ions = []
  seen = set()
  for start in sorted(is_metal):
    if not is_metal[start] or start in seen:
      continue
    found = _ion_atoms(start, atoms, bonds, is_metal)
    if found is None:
      continue
    seen |= found
    placed, generators = _grow(start, bonds, lambda u, v: u in found and v in found)
    centres = [i for i in found if is_metal[i]]
    piece = _make_piece(atoms, placed, generators, group_ops, centres)
    if len(placed) == len(found) and _formula_and_amount(piece['counts'])[0] in METAL_IONS:
      ions.append(found)
  return [ion for ion in ions if not any(ion & other for other in ions if other is not ion)]


def find_pieces(atoms, group_ops=None):
  """
  Split the atoms into pieces, metals disconnected unless part of a known ion.
  group_ops: all operators of the space group as make_op() tuples; without them,
  atoms on special positions that have no bond to their own copy are taken for
  general ones.

  Each piece: atoms (indices), copies ({index: displayed copies per piece}),
  counts ({element: atoms per piece}) and per_au (pieces per asymmetric unit).
  """
  usable = [i for i, a in enumerate(atoms) if a['type'] not in ('Q', 'q')]
  is_metal = {i: atoms[i]['type'].capitalize() in _METALS for i in usable}
  bonds = _both_ways(atoms)

  ion_of = {}
  for n, ion in enumerate(_find_ions(atoms, bonds, is_metal, group_ops)):
    ion_of.update((i, n) for i in ion)

  def joined(u, v):
    if v not in is_metal:
      return False
    if u in ion_of or v in ion_of:
      return ion_of.get(u) == ion_of.get(v)
    return not is_metal[u] and not is_metal[v]

  seen = set()
  pieces = []
  for start in usable:
    if start in seen:
      continue
    placed, generators = _grow(start, bonds, joined)
    seen.update(placed)
    centres = [i for i in placed if i in ion_of and is_metal[i]]
    pieces.append(_make_piece(atoms, placed, generators, group_ops, centres))
  return pieces


def _body(counts):
  rounded = {e: round(n, 3) for e, n in counts.items() if round(n, 3) > 0}
  return ' '.join(sym if rounded[sym] == 1 else f"{sym}{rounded[sym]:g}"
                  for sym in _element_order(rounded))


def _formula_and_amount(counts):
  """
  (formula, amount of it) for one piece: H1.4 O0.7 is 0.7 of H2 O, so that part-
  occupied sites of one species add up, here to one water with the other 0.3.
  """
  split = split_occupancy({e: round(n, 3) for e, n in counts.items() if round(n, 3) > 0})
  if split:
    return _body(split[0]), Fraction(split[1]).limit_denominator(1000)
  return _body(counts), Fraction(1)


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
  units = {}
  for piece in pieces:
    body, amount = _formula_and_amount(piece['counts'])
    if body:
      merged[body] = merged.get(body, 0) + piece['per_au'] * amount
      units[body] = units.get(body, 0) + piece['per_au']
  # Whole formula units follow from the symmetry; an occupancy is what it is
  scale = 1
  for n in units.values():
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
      body, amount = _formula_and_amount(piece['counts'])
      merged[body] = merged.get(body, 0) + whole * amount
    rest = {}
    for i in members:
      left = shown.get(i, 0) - whole * piece['copies'][i]
      if left:
        element = atoms[i]['type'].capitalize()
        rest[element] = rest.get(element, 0) + left * _chemical_weight(atoms[i], group_ops)
    if rest:
      body, amount = _formula_and_amount(rest)
      merged[body] = merged.get(body, 0) + amount
  return _join(merged)
