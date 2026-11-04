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

    Returns (colours, labels, n_sets, n_clashes):
      colours   : {key: 0 or 1} for every copy of a disordered atom; None if the
                  contacts contradict each other (no clash-free split exists)
      labels    : the disordered atom labels
      n_sets    : number of independent sets; with 1, choosing one atom decides all
      n_clashes : number of too-close pairs found
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
  for a, b in pairs:
    if atoms[a][0] in labels and _element(atoms[b][0]) == 'H':
      labels = labels | {atoms[b][0]}
    if atoms[b][0] in labels and _element(atoms[a][0]) == 'H':
      labels = labels | {atoms[a][0]}

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
  if not consistent:
    return None, labels, 0, len(clashes)
  colours = {k: find(k)[1] for k in parent}
  return colours, labels, len({find(k)[0] for k in parent}), len(clashes)


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


def complete_complex(cell, atoms, ops, metal: int, radii: dict) -> tuple:
  """
    The atoms of one metal with its ligands complete, without any other metal:
    everything reached by bonds from the metal, never passing through a metal,
    and with hydrogens as ends only (their short contacts between disordered
    rings are not bonds, and would lead on to the next metal's ligands).

    cell   : (a, b, c, alpha, beta, gamma)
    atoms  : [(label, element, (x, y, z))], fractional asymmetric unit
    ops    : [(rotation, translation)], all operators of the cell
    metal  : index into atoms; stays where it is
    radii  : {element: bonding radius in A}

    Returns (codes, strays): codes is {symmetry code: [labels]} for the images
    that are not the asymmetric unit itself, strays the asymmetric unit labels
    that are not part of the complex.
    """
  ca, cb, cg = [math.cos(math.radians(v)) for v in cell[3:]]
  sg = math.sin(math.radians(cell[5]))
  a, b, c = cell[:3]
  cz = math.sqrt(max(0.0, 1 - ca * ca - cb * cb - cg * cg + 2 * ca * cb * cg)) / sg

  def distance(u, v):
    d = [p - q for p, q in zip(u, v)]
    return math.sqrt((a * d[0] + b * cg * d[1] + c * cb * d[2]) ** 2
                     + (b * sg * d[1] + c * (ca - cb * cg) / sg * d[2]) ** 2
                     + (c * cz * d[2]) ** 2)

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
            yield tuple(q + s for q, s in zip(base, (i, j, k))), rotation, \
              [t + sh + s for t, sh, s in zip(translation, shift, (i, j, k))]

  all_images = [(n, xyz, rot, tr) for n in range(len(atoms)) for xyz, rot, tr in images(n)]
  start = tuple(atoms[metal][2])
  kept = {(metal, tuple(round(v, 4) for v in start)): None}
  frontier = [(metal, start)]
  while frontier:
    index, here = frontier.pop()
    element = atoms[index][1]
    if element in ('H', 'D') or (is_metal(element) and index != metal):
      continue
    if is_metal(element) and distance(here, start) > 1e-3:
      continue
    for n, xyz, rot, tr in all_images:
      other = atoms[n][1]
      if is_metal(other) or (other in ('H', 'D') and element in ('H', 'D')):
        continue
      reach = radii[element] + radii[other] + _BOND_TOLERANCE
      gap = distance(xyz, here)
      if gap < 0.1 or gap > reach:
        continue
      key = (n, tuple(round(v, 4) for v in xyz))
      if key not in kept:
        kept[key] = (rot, tr)
        frontier.append((n, xyz))

  codes = {}
  shown = {metal}
  for (n, xyz), op in kept.items():
    if op is None:
      continue
    if distance(xyz, atoms[n][2]) < 1e-3:
      shown.add(n)
      continue
    codes.setdefault(symm_code(*op), []).append(atoms[n][0])
  strays = [atoms[n][0] for n in range(len(atoms)) if n not in shown]
  return codes, strays
