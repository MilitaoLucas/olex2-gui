"""
gui/symdisorder/_core.py

The pure-Python parts of gui/symdisorder, testable without Olex2.
"""

from __future__ import annotations
import math
import re


# ---------------------------------------------------------------------------
# Orientations of a symmetry-disordered group in a grown structure
# ---------------------------------------------------------------------------

# Non-bonded copies of one atom closer than this (A) cannot exist together.
CLASH_LIMIT_H = 1.5
CLASH_LIMIT_OTHER = 1.75


def _element(label: str) -> str:
  """'Cl1' -> 'Cl', 'C1A' -> 'C'."""
  return re.match(r'[A-Z][a-z]?', label).group()


def colour_orientations(atoms: dict, bonds: set) -> tuple:
  """
    Sort the copies of symmetry-disordered atoms into clash-free sets.

    Non-bonded copies of the same atom that are too close must be in different
    sets, bonded disordered atoms in the same one. Hydrogens with no contact of
    their own follow their parent atom.

    atoms : {key: (label, (x, y, z))}, Cartesian coordinates in A
    bonds : set of frozenset({key_a, key_b})

    Returns (colours, labels, n_sets, n_clashes, sets):
      colours   : {key: 0 or 1} for every copy of a disordered atom; None if the
                  contacts contradict each other (no clash-free split exists)
      labels    : the disordered atom labels
      n_sets    : number of independent sets; with 1, choosing one atom decides all
      n_clashes : number of too-close pairs found
      sets      : {key: set id} for the keys in colours; colours compare only
                  within one set
    """
  keys = sorted(atoms)
  clashes = []
  for i, a in enumerate(keys):
    for b in keys[i + 1:]:
      if atoms[a][0] != atoms[b][0] or frozenset((a, b)) in bonds:
        continue
      limit = CLASH_LIMIT_H if _element(atoms[a][0]) == 'H' else CLASH_LIMIT_OTHER
      if math.dist(atoms[a][1], atoms[b][1]) < limit:
        clashes.append((a, b))

  labels = {atoms[k][0] for pair in clashes for k in pair}
  pairs = [tuple(p) for p in bonds]
  neighbours = {k: set() for k in keys}
  for a, b in pairs:
    neighbours[a].add(b)
    neighbours[b].add(a)
  copies = {}
  for k in keys:
    copies.setdefault(atoms[k][0], []).append(k)

  # union-find, each node carrying whether it differs from its parent
  parent = {k: (k, 0) for k in keys if atoms[k][0] in labels}

  def find(x):
    differs = 0
    while parent[x][0] != x:
      differs ^= parent[x][1]
      x = parent[x][0]
    return x, differs

  def link(a, b, differ) -> bool:
    root_a, diff_a = find(a)
    root_b, diff_b = find(b)
    if root_a == root_b:
      return diff_a ^ diff_b == differ
    parent[root_a] = (root_b, diff_a ^ diff_b ^ differ)
    return True

  consistent = True
  for a, b in pairs:
    if a in parent and b in parent:
      consistent = link(a, b, 0) and consistent
  for a, b in clashes:
    consistent = link(a, b, 1) and consistent

  # Atoms far from their own copies belong to an orientation through their
  # bonds: a label joins when every copy is bonded to disordered atoms, without
  # contradiction. A copy bonded to both orientations (the atom the group hangs
  # on, or one on the symmetry element) keeps the label shared.
  growing = consistent
  while growing:
    growing = False
    for label, keys_of in copies.items():
      if label in labels or len(keys_of) < 2 \
          or not all(any(n in parent for n in neighbours[k]) for k in keys_of):
        continue
      saved = dict(parent)
      for k in keys_of:
        parent[k] = (k, 0)
      if all(link(k, n, 0) for k in keys_of for n in neighbours[k] if n in parent and n != k):
        labels = labels | {label}
        growing = True
      else:
        parent.clear()
        parent.update(saved)
  if not consistent:
    return None, labels, 0, len(clashes), {}
  colours = {k: find(k)[1] for k in parent}
  sets = {k: find(k)[0] for k in parent}
  return colours, labels, len(set(sets.values())), len(clashes), sets


# ---------------------------------------------------------------------------
# One metal with complete ligands
# ---------------------------------------------------------------------------

_NON_METALS = {'H', 'D', 'T', 'He', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Si', 'P', 'S', 'Cl', 'Ar',
               'As', 'Se', 'Br', 'Kr', 'Te', 'I', 'Xe', 'At', 'Rn', 'Q'}
_BOND_TOLERANCE = 0.5  # A, as Olex2's connectivity


def is_metal(element: str) -> bool:
  return element not in _NON_METALS


def symm_code(rotation, translation) -> str:
  """Symmetry operator as Olex2 writes it: ((1,0,0),(0,-1,0),(0,0,1)), (0,1,0) -> '+X,1-Y,+Z'."""
  parts = []
  for row, t in zip(rotation, translation):
    terms = ''.join(('+' if r > 0 else '-') + axis
                    for r, axis in zip(row, 'XYZ') if r)
    if abs(t) > 1e-6:
      parts.append(('%g' % t) + terms)
    else:
      parts.append(terms)
  return ','.join(parts)


class PolymericError(ValueError):
  """Bonds lead on without end: the structure is a network, not fragments."""


# A fragment grown further than this from its seed (in cells, along any axis)
# is taken to be polymeric.
_POLYMER_LIMIT = 1.5


def _cell_axes(cell):
  """Cartesian vectors of a, b and c, as Olex2 orients them (a along x)."""
  ca, cb, cg = [math.cos(math.radians(v)) for v in cell[3:]]
  sg = math.sin(math.radians(cell[5]))
  a, b, c = cell[:3]
  cz = math.sqrt(max(0.0, 1 - ca * ca - cb * cb - cg * cg + 2 * ca * cb * cg)) / sg
  return (a, 0.0, 0.0), (b * cg, b * sg, 0.0), (c * cb, c * (ca - cb * cg) / sg, c * cz)


def cartesian(cell, u):
  va, vb, vc = _cell_axes(cell)
  return tuple(va[i] * u[0] + vb[i] * u[1] + vc[i] * u[2] for i in range(3))


def fractional(cell, x):
  va, vb, vc = _cell_axes(cell)
  w = x[2] / vc[2]
  v = (x[1] - vc[1] * w) / vb[1]
  return ((x[0] - vb[0] * v - vc[0] * w) / va[0], v, w)


def complete_fragments(cell, atoms, ops, shown, radii: dict) -> dict:
  """
    The atoms that complete the fragments of the atoms shown. A metal is never
    added: a fragment ends at a metal that is not shown, so that bridging
    ligands are complete without the metal on their far side. Hydrogens are
    ends only (their short contacts between disordered groups are not bonds,
    and would lead on to the neighbours).

    cell   : (a, b, c, alpha, beta, gamma)
    atoms  : [(label, element, (x, y, z))], fractional asymmetric unit
    ops    : [(rotation, translation)], all operators of the cell
    shown  : [(index into atoms, fractional (x, y, z))], the atoms on screen
    radii  : {element: bonding radius in A}

    Returns {symmetry code: [labels]} for the atoms to add. Raises
    PolymericError if the bonds lead on without end.
    """
  def images(index):
    """Every image of an atom in the block of cells around the origin cell."""
    x = atoms[index][2]
    for rotation, translation in ops:
      y = [sum(r * v for r, v in zip(row, x)) + t for row, t in zip(rotation, translation)]
      base = [v - math.floor(v) for v in y]
      shift = [p - q for p, q in zip(base, y)]
      for i in range(-2, 3):
        for j in range(-2, 3):
          for k in range(-2, 3):
            yield tuple(q + s for q, s in zip(base, (i, j, k))), rotation,               [t + sh + s for t, sh, s in zip(translation, shift, (i, j, k))]

  # every image, in bins of the longest bond, so that only the neighbouring
  # bins need searching; metals only for placing the shown ones
  used = {e for _, e, _ in atoms}
  bin_size = 2 * max(radii[e] for e in used) + _BOND_TOLERANCE

  def bin_of(xyz):
    return tuple(math.floor(v / bin_size) for v in xyz)

  bins, metal_bins = {}, {}
  for n in range(len(atoms)):
    target = metal_bins if is_metal(atoms[n][1]) else bins
    for xyz, rot, tr in images(n):
      cart = cartesian(cell, xyz)
      target.setdefault(bin_of(cart), []).append((n, xyz, cart, rot, tr))

  def near(cart, table):
    i0, j0, k0 = bin_of(cart)
    for i in (i0 - 1, i0, i0 + 1):
      for j in (j0 - 1, j0, j0 + 1):
        for k in (k0 - 1, k0, k0 + 1):
          yield from table.get((i, j, k), ())

  def key_of(n, xyz):
    return n, tuple(round(v, 4) for v in xyz)

  # the shown atoms, placed on their exact images
  seeds = []
  for n, xyz in shown:
    cart = cartesian(cell, xyz)
    table = metal_bins if is_metal(atoms[n][1]) else bins
    best = min((math.dist(cart, image[2]), image[1]) for image in near(cart, table) if image[0] == n)
    if best[0] > 0.05:
      raise ValueError(f'{atoms[n][0]} is not where the symmetry puts it')
    seeds.append((n, best[1]))

  kept = {key_of(n, xyz): None for n, xyz in seeds}
  for seed, start in seeds:
    frontier = [(seed, start)]
    while frontier:
      index, here = frontier.pop()
      element = atoms[index][1]
      if element in ('H', 'D') or (is_metal(element) and (index, here) != (seed, start)):
        continue
      if max(abs(p - q) for p, q in zip(here, start)) > _POLYMER_LIMIT:
        raise PolymericError(atoms[seed][0])
      cart = cartesian(cell, here)
      for n, xyz, other_cart, rot, tr in near(cart, bins):
        other = atoms[n][1]
        if other in ('H', 'D') and element in ('H', 'D'):
          continue
        gap = math.dist(cart, other_cart)
        if gap < 0.1 or gap > radii[element] + radii[other] + _BOND_TOLERANCE:
          continue
        key = key_of(n, xyz)
        if key not in kept:
          kept[key] = (rot, tr)
          frontier.append((n, xyz))

  codes = {}
  for (n, _), op in kept.items():
    if op is not None:
      codes.setdefault(symm_code(*op), []).append(atoms[n][0])
  return codes
