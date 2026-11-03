"""
Tests for twin_details.py -- run from util/pyUtil/PyToolLib:

    python -m unittest test_twin_details
"""

import math
import unittest

import twin_details as T

# str1878Pbca_pl: pseudo-tetragonal Pbca cell, a ~ c
PBCA = (21.2118, 13.9553, 21.2149, 90, 90, 90)
MONO = (10.0, 11.0, 12.0, 90, 105, 90)


def _matrix_for(cell, axis_cart, angle):
  """Twin matrix (on hkl) for a Cartesian rotation: M = B^-1 R B."""
  x, y, z = (c / math.sqrt(sum(v * v for v in axis_cart)) for c in axis_cart)
  c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
  r = [[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
       [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
       [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]]
  A = T.orthogonalisation(cell)
  B = T._t(T._inv(A))
  return T._mul(T._mul(T._inv(B), r), B)


class TwinDetailsTest(unittest.TestCase):

  def test_this_structure(self):
    text = T.describe('0 0 1 0 -1 0 1 0 0 2', PBCA)
    self.assertEqual(
      text, "Twin law (TWIN 0 0 1 0 -1 0 1 0 0 2): component 2 rotated by "
            "180\\% around [0.71 0.00 0.71] (reciprocal) or "
            "[0.71 0.00 0.71] (direct).")
    self.assertTrue(text.startswith(T.PREFIX))
    text.encode('ascii')                       # metacif takes ASCII only

  def test_small_rotation_recovered(self):
    # like a non-merohedral law from data reduction: 2.2444 deg about an
    # arbitrary axis -- angle and axis must come back exactly
    axis = (0.3, -0.5, 0.81)
    m = _matrix_for(MONO, axis, 2.2444)
    angle, recip, direct, proper = T.rotation_of(m, MONO)
    self.assertTrue(proper)
    self.assertAlmostEqual(angle, 2.2444, places=6)
    A = T.orthogonalisation(MONO)
    # the direct axis, back in Cartesian, is parallel to the input axis
    cart = T._unit(T._apply(A, direct))
    ref = T._unit(list(axis))
    self.assertAlmostEqual(abs(sum(a * b for a, b in zip(cart, ref))), 1.0, places=9)
    # and the reciprocal axis describes the same direction
    cart_r = T._unit(T._apply(T._t(T._inv(A)), recip))
    self.assertAlmostEqual(abs(sum(a * b for a, b in zip(cart_r, ref))), 1.0, places=9)

  def test_twofold_about_b_in_monoclinic(self):
    angle, recip, direct, proper = T.rotation_of(
      [[-1, 0, 0], [0, 1, 0], [0, 0, -1]], MONO)
    self.assertAlmostEqual(angle, 180.0, places=6)
    self.assertEqual([round(x, 6) for x in direct], [0, 1, 0])
    self.assertEqual([round(x, 6) for x in recip], [0, 1, 0])

  def test_pure_inversion_is_skipped(self):
    self.assertIsNone(T.describe('-1 0 0 0 -1 0 0 0 -1 2', MONO))
    self.assertIsNone(T.describe('-1 0 0 0 -1 0 0 0 -1', MONO))

  def test_improper_law(self):
    # mirror perpendicular to b = inversion combined with a twofold about b
    text = T.describe('1 0 0 0 -1 0 0 0 1 2', MONO)
    self.assertIn('rotated by 180\\%', text)
    self.assertIn('combined with inversion', text)

  def test_three_components(self):
    # threefold about c in a hexagonal cell: components 2 and 3 at 120 and
    # 240 deg (= 120 about the opposite direction). The TWIN matrix acts on
    # hkl, i.e. it is the inverse transpose of the coordinate threefold
    # (0 -1 0 1 -1 0 0 0 1) -- using that one by mistake gives 109 deg.
    hexa = (5.0, 5.0, 8.0, 90, 90, 120)
    text = T.describe('-1 -1 0 1 0 0 0 0 1 3', hexa)
    self.assertEqual(text.count('rotated by 120\\%'), 2)
    self.assertIn('component 3', text)

  def test_negative_n_mentions_inversion_partners(self):
    text = T.describe('0 0 1 0 -1 0 1 0 0 -4', PBCA)
    self.assertIn('component 2 rotated by 180\\%', text)
    self.assertIn('inversion partner', text)

  def test_twinning_from_model(self):
    # shaped like OV.GetRefinementModel(False) (see olexex.GetTwinLawAndBASF)
    rm = {'twin': {'matrix': [[0, 0, 1], [0, -1, 0], [1, 0, 0]], 'n': 2, 'basf': [0.45]},
          'hklf': {'value': 4, 'matrix': [[1, 0, 0], [0, 0, 1], [0, -1, 0]]}}
    twin, hklf = T.twinning_from_model(rm)
    self.assertEqual(twin, '0 0 1 0 -1 0 1 0 0 2')
    self.assertEqual(hklf, '4 1 1 0 0 0 0 1 0 -1 0')
    self.assertEqual(T.describe(twin, PBCA), T.describe('0 0 1 0 -1 0 1 0 0 2', PBCA))
    self.assertEqual(T.twinning_from_model({'hklf': {'value': 5}}), (None, '5'))
    self.assertEqual(T.twinning_from_model({}), (None, ''))

  def test_bad_input(self):
    with self.assertRaises(ValueError):
      T.parse_twin('1 0 0')



# ---------------------------------------------------------------------------
# HKLF 5
# ---------------------------------------------------------------------------

import itertools
import random

MMM = [((a, 0, 0), (0, b, 0), (0, 0, c)) for a, b, c in itertools.product((1, -1), repeat=3)]
P2M = [((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, -1, 0), (0, 0, -1)),
       ((-1, 0, 0), (0, 1, 0), (0, 0, -1)), ((1, 0, 0), (0, -1, 0), (0, 0, 1))]


def _hklf5_lines(pairs, ops, seed=1):
  """HKLF 5 text: each pair as a group, component 2 as a random equivalent."""
  rnd = random.Random(seed)
  out = []
  for h1, h2 in pairs:
    g = rnd.choice(ops)
    e = [int(round(sum(g[i][k] * h2[k] for k in range(3)))) for i in range(3)]
    out.append("%4d%4d%4d%8.2f%8.2f%4d" % (e[0], e[1], e[2], 100.0, 1.0, -2))
    out.append("%4d%4d%4d%8.2f%8.2f%4d" % (h1[0], h1[1], h1[2], 100.0, 1.0, 1))
  out.append("%4d%4d%4d%8.2f%8.2f%4d" % (0, 0, 0, 0, 0, 0))
  return out


def _grid(n):
  return [h for h in itertools.product(range(-n, n + 1), repeat=3) if any(h)]


class Hklf5Test(unittest.TestCase):

  def test_groups_parsed(self):
    lines = ["   1   2   3  100.00    1.00  -2",
             "   3   2   1  100.00    1.00   1",
             "   5   5   5  100.00    1.00   1",      # single: not an overlap
             "   0   0   0    0.00    0.00   0",
             "   9   9   9  100.00    1.00  -2"]     # after the terminator
    self.assertEqual(list(T.overlap_groups(lines)), [{2: (1, 2, 3), 1: (3, 2, 1)}])

  def test_merohedral_law_as_twin_card(self):
    # the Pbca twin law, component-2 indices as random mmm equivalents
    m = [[0, 0, 1], [0, -1, 0], [1, 0, 0]]
    pairs = [(h, T._apply(m, list(h))) for h in _grid(4)]
    laws = T.fit_laws(T.overlap_groups(_hklf5_lines(pairs, MMM)), laue_ops=MMM)
    self.assertLess(laws[2][2], 1e-9)
    text = T.describe_hklf5(laws, PBCA, MMM)
    twin = T.describe('0 0 1 0 -1 0 1 0 0 2', PBCA)
    self.assertEqual(text.split('): ')[1], twin.split('): ')[1])
    self.assertTrue(text.startswith(T.PREFIX + 'HKLF 5'))

  def test_non_merohedral_twofold(self):
    # classic monoclinic non-merohedral twin, a twofold about a direction
    # that is not a lattice symmetry axis (here ~ the direct c axis). On hkl:
    # h' = -h, k' = -k, l' = l + (2 c cos(beta) / a) h -- non-integer, so
    # only some reflections overlap and component-2 indices are rounded
    a, c, beta = MONO[0], MONO[2], math.radians(MONO[4])
    m = [[-1, 0, 0], [0, -1, 0], [2 * c * math.cos(beta) / a, 0, 1]]
    pairs = []
    for h in _grid(9):
      p = T._apply(m, list(h))
      if max(abs(x - round(x)) for x in p) < 0.2:
        pairs.append((h, [round(x) for x in p]))
    laws = T.fit_laws(T.overlap_groups(_hklf5_lines(pairs, P2M)), laue_ops=P2M)
    self.assertLess(laws[2][2], T.MAX_RMS)
    fitted = T.canonical_law(laws[2][0], MONO, P2M)
    angle, recip, direct, proper = T.rotation_of(fitted, MONO)
    self.assertAlmostEqual(angle, 180.0, delta=0.5)
    # same axis as the exact law, or as its 2/m equivalent (2_b times it)
    A = T.orthogonalisation(MONO)
    got = T._unit(T._apply(A, direct))
    refs = []
    for g in (P2M[0], P2M[2]):
      d = T.rotation_of(T._mul([list(r) for r in g], m), MONO)[2]
      refs.append(T._unit(T._apply(A, d)))
    self.assertGreater(max(abs(sum(x * y for x, y in zip(got, r))) for r in refs), 0.999)
    text = T.describe_hklf5(laws, MONO, P2M)
    self.assertIn('rotated by 18', text)

  def test_small_angle_not_reported(self):
    # a 2.2444 deg twin: only coinciding reflections overlap, the indices
    # carry no angle -- must not be reported as a rotation by 0 deg
    m = _matrix_for(MONO, (0.3, -0.5, 0.81), 2.2444)
    pairs = []
    for h in _grid(9):
      p = T._apply(m, list(h))
      if max(abs(x - round(x)) for x in p) < 0.25:
        pairs.append((h, [round(x) for x in p]))
    laws = T.fit_laws(T.overlap_groups(_hklf5_lines(pairs, P2M)), laue_ops=P2M)
    self.assertIsNone(T.describe_hklf5(laws, MONO, P2M))

  def test_hklf_matrix_applied(self):
    # file indices in another setting (h <-> l swapped); HKLF 5 matrix maps back
    swap = [[0, 0, 1], [0, 1, 0], [1, 0, 0]]
    m = [[0, 0, 1], [0, -1, 0], [1, 0, 0]]
    pairs = [(T._apply(swap, list(h)), T._apply(swap, T._apply(m, list(h)))) for h in _grid(3)]
    laws = T.fit_laws(T.overlap_groups(_hklf5_lines(pairs, [T.IDENTITY])),
                      transform=swap, laue_ops=MMM)
    self.assertLess(laws[2][2], 1e-9)

  def test_unrelated_indices_give_nothing(self):
    rnd = random.Random(7)
    pairs = [(h, [rnd.randint(-9, 9) for _ in range(3)]) for h in _grid(3)]
    laws = T.fit_laws(T.overlap_groups(_hklf5_lines(pairs, [T.IDENTITY])), laue_ops=MMM)
    self.assertGreater(laws[2][2], T.MAX_RMS)
    self.assertIsNone(T.describe_hklf5(laws, PBCA, MMM))

  def test_no_inversion_wording_for_hklf5(self):
    # 2026-10-01 in Olex2: a real HKLF 5 law came out "..., combined with
    # inversion" because the Laue operators lacked -1 (cctbx smx() default).
    # Even with such an incomplete set the description must be proper.
    m = [[1, 0, 0], [0, 1, 0], [0.62, 0, -1]]          # det -1
    half = [P2M[0], P2M[2]]                             # 2/m without -1
    text = T.describe_hklf5({2: (m, 100, 0.1)}, MONO, half)
    self.assertIn('rotated by 180\\%', text)
    self.assertNotIn('inversion', text)

  def test_twofold_preferred_over_smaller_angle(self):
    # pseudo-tetragonal a ~ c: 90 deg about b is an equivalent law, but the
    # twofold about [101] is the conventional description
    law = T.canonical_law([[0, 0, 1], [0, 1, 0], [1, 0, 0]], PBCA, MMM)
    self.assertAlmostEqual(T.rotation_of(law, PBCA)[0], 180.0, places=4)


if __name__ == '__main__':
  unittest.main()
