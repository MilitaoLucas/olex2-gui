"""
gui/symsnap/_core.py

Pure-Python part of Symmetry Snap, testable without Olex2.

Atoms are given in fractional coordinates; symmetry operators as
(rotation, translation) pairs in fractional space, as olex_core.SGInfo()
['MatricesAll'] gives them. Lattice translations are handled by taking the
nearest image, so the operator list need not hold them.

Occupancies are crystallographic (SHELX style): the number of atoms in the cell
is occupancy x the number of general positions, whether or not the atom sits on
a special position. That count is kept: a merged atom gets the sum of its
members' occupancies, and an atom snapped onto a special position keeps its own.
"""

from __future__ import annotations
import math

DEFAULT_TOLERANCE = 0.5  # A, between an atom and a symmetry image that counts as "the same"
_IDENTITY = (((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0.0, 0.0, 0.0))


def metric(cell) -> tuple:
  """Metric tensor G of a cell (a, b, c, alpha, beta, gamma)."""
  a, b, c = cell[:3]
  ca, cb, cg = [math.cos(math.radians(v)) for v in cell[3:6]]
  return ((a * a, a * b * cg, a * c * cb),
          (a * b * cg, b * b, b * c * ca),
          (a * c * cb, b * c * ca, c * c))


def length(G, d) -> float:
  return math.sqrt(max(0.0, sum(d[i] * G[i][j] * d[j] for i in range(3) for j in range(3))))


def _apply(op, x) -> tuple:
  rotation, translation = op
  return tuple(sum(rotation[i][j] * x[j] for j in range(3)) + translation[i] for i in range(3))


def _toward(y, ref) -> tuple:
  """The lattice translate of y closest to ref."""
  return tuple(ref[i] + (y[i] - ref[i]) - round(y[i] - ref[i]) for i in range(3))


def nearest_image(G, ops, x, ref) -> tuple:
  """(distance in A, fractional position) of the image of x closest to ref."""
  best = (math.inf, None)
  for op in ops:
    y = _toward(_apply(op, x), ref)
    d = length(G, [y[i] - ref[i] for i in range(3)])
    if d < best[0]:
      best = (d, y)
  return best


def _with_identity(ops) -> list:
  ops = [(tuple(tuple(int(round(v)) for v in r) for r in rot), tuple(float(t) for t in tr))
         for rot, tr in ops]
  return ops if _IDENTITY in ops else [_IDENTITY] + ops


def snap_to_site(G, ops, x, tol: float = DEFAULT_TOLERANCE) -> tuple:
  """
    Move x onto the special position it is close to.

    Returns (fractional position, site order k). The operators that map x to
    within tol of itself form its site-symmetry group; the mean of those images
    is the projection onto the symmetry element. k == 1: a general position.
    """
  k = 1
  for _ in range(3):
    images = [y for y in (_toward(_apply(op, x), x) for op in ops)
              if length(G, [y[i] - x[i] for i in range(3)]) < tol]
    k = len(images)
    new = tuple(sum(y[i] for y in images) / k for i in range(3))
    if length(G, [new[i] - x[i] for i in range(3)]) < 1e-6:
      return new, k
    x = new
  return x, k


def merge_plan(cell, ops, atoms, tol: float = DEFAULT_TOLERANCE) -> list:
  """
    Plan how to make near-symmetry-equivalent atoms exactly equivalent.

    atoms: [(label, element, (x, y, z), occupancy)], the first of each group is
    kept (pass them in a.u. order). Atoms of one element whose symmetry images
    come within tol of each other form a group: it becomes one atom at the mean
    of the aligned positions, with the summed occupancy. Each resulting atom,
    single ones too, is then snapped onto a special position within tol.

    Returns one dict per atom that changes:
      keep      label kept
      remove    labels to delete (merged into keep)
      xyz       new fractional position
      occu      new occupancy
      site      site order k (1 = general position)
      moved     A the kept atom moves
      spread    A, largest distance of a member's image from the new position
      overfull  True if occu exceeds a fully occupied site (1/k)
    """
  G = metric(cell)
  ops = _with_identity(ops)
  n = len(atoms)
  parent = list(range(n))

  def find(i):
    while parent[i] != i:
      parent[i] = parent[parent[i]]
      i = parent[i]
    return i

  for i in range(n):
    for j in range(i + 1, n):
      if atoms[i][1] != atoms[j][1]:
        continue
      if nearest_image(G, ops, atoms[j][2], atoms[i][2])[0] < tol:
        parent[find(j)] = find(i)

  groups = {}
  for i in range(n):
    groups.setdefault(find(i), []).append(i)

  plan = []
  for members in sorted(groups.values()):
    keep = members[0]
    ref = atoms[keep][2]
    aligned = [ref] + [nearest_image(G, ops, atoms[m][2], ref)[1] for m in members[1:]]
    mean = tuple(sum(p[i] for p in aligned) / len(aligned) for i in range(3))
    xyz, k = snap_to_site(G, ops, mean, tol)
    moved = length(G, [xyz[i] - ref[i] for i in range(3)])
    if len(members) == 1 and moved < 1e-4:
      continue
    occu = sum(atoms[m][3] for m in members)
    spread = max(nearest_image(G, ops, atoms[m][2], xyz)[0] for m in members)
    plan.append({'keep': atoms[keep][0],
                 'remove': [atoms[m][0] for m in members[1:]],
                 'xyz': xyz, 'occu': occu, 'site': k,
                 'moved': moved, 'spread': spread,
                 'overfull': occu > 1.0 / k + 1e-3})
  return plan
