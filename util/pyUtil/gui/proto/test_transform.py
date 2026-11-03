"""
Tests for gui/proto/transform.py -- run from util/pyUtil/gui:

    python -m unittest proto.test_transform

A change of basis re-describes the same crystal, so the tests check what
must not change: interatomic distances, Ueq and the principal values of
each U tensor, and the action of symmetry operators (EQIV).
"""

import math
import unittest

from . import transform as T

# P21/c-like monoclinic cell and a unimodular change of basis
# a' = a, b' = -b, c' = -a - c  (coordinates: x' = R x)
OLD_CELL = (10.0, 11.0, 12.0, 90.0, 105.0, 90.0)
R_BASIS = ((1, 0, 0), (0, -1, 0), (-1, 0, -1))     # rows: new basis in old


def _inv3(m):
  return T._inverse([[T.Fraction(x) for x in row] for row in m])


def _metric(cell):
  a, b, c = cell[:3]
  al, be, ga = (math.radians(x) for x in cell[3:])
  return [[a * a, a * b * math.cos(ga), a * c * math.cos(be)],
          [a * b * math.cos(ga), b * b, b * c * math.cos(al)],
          [a * c * math.cos(be), b * c * math.cos(al), c * c]]


def _cell_from_metric(g):
  a, b, c = (math.sqrt(g[i][i]) for i in range(3))
  return (a, b, c,
          math.degrees(math.acos(g[1][2] / (b * c))),
          math.degrees(math.acos(g[0][2] / (a * c))),
          math.degrees(math.acos(g[0][1] / (a * b))))


def _new_cell_and_r9(old_cell, basis):
  """New cell for basis rows (new vectors in old ones) and the coordinate R."""
  g = _metric(old_cell)
  b = [list(map(float, row)) for row in basis]
  g_new = T._mul(T._mul(b, g), T._transpose(b))
  # coordinates transform with the inverse transpose of the basis matrix
  r = T._transpose(_inv3(basis))
  r9 = tuple(float(x) for row in r for x in row)
  return _cell_from_metric(g_new), r9


def _dist(cell, p, q):
  g = _metric(cell)
  d = [p[i] - q[i] for i in range(3)]
  return math.sqrt(sum(d[i] * g[i][j] * d[j] for i in range(3) for j in range(3)))


def _u_cart_invariants(cell, u_shelx):
  """(trace/3 = Ueq, det) of U in Cartesian space: basis independent."""
  ra = T.reciprocal_lengths(cell)
  u11, u22, u33, u23, u13, u12 = u_shelx
  u = [[u11, u12, u13], [u12, u22, u23], [u13, u23, u33]]
  ustar = [[u[i][j] * ra[i] * ra[j] for j in range(3)] for i in range(3)]
  g = _metric(cell)
  # U_cart similar to G U* (same eigenvalues)
  m = T._mul(g, ustar)
  tr = m[0][0] + m[1][1] + m[2][2]
  det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
         - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
         + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
  return tr / 3, det


MODEL = """TITL old
CELL 0.71073 10.0 11.0 12.0 90 105 90
ZERR 4 0.001 0.001 0.001 0 0.01 0
LATT 1
SYMM -X, 0.5+Y, 0.5-Z
SFAC C H N
UNIT 24 24 4
EQIV $1 -x+1, y+1/2, -z+1/2
DFIX 1.5 C1 N1_$1
FVAR 0.5
C1    1    0.100000    0.200000    0.300000    11.00000    0.02000    0.03000 =
    0.04000    0.00100    0.00500    0.00200
N1    3    10.25000    0.150000    0.350000    11.00000    0.03
H1A   2    0.120000    0.210000    0.330000    11.00000   -1.20000
Q1    1    0.500000    0.500000    0.500000    11.00000    0.05000    1.23
HKLF 4
END
"""


class TransformTest(unittest.TestCase):

  def setUp(self):
    self.new_cell, self.r9 = _new_cell_and_r9(OLD_CELL, R_BASIS)
    self.t = (0.0, 0.0, 0.0)
    self.out = T.transform_model(
        MODEL, self.r9, self.t, OLD_CELL, self.new_cell,
        replace={'CELL': ['CELL 0.71073 new'], 'ZERR': ['ZERR 4 new'],
                 'SYMM': ['LATT 1', 'SYMM new']})
    self.lines = self.out.splitlines()

  def _atom(self, label):
    for i, l in enumerate(self.lines):
      if l.split() and l.split()[0] == label:
        tok = l.rstrip(' =').split()
        if l.rstrip().endswith('='):
          tok += self.lines[i + 1].split()
        return tok
    self.fail("atom %s not in output" % label)

  def test_distances_preserved(self):
    old = {'C1': (0.1, 0.2, 0.3), 'N1': (0.25, 0.15, 0.35), 'H1A': (0.12, 0.21, 0.33)}
    new = {k: tuple(float(x) for x in self._atom(k)[2:5]) for k in old}
    for a in old:
      for b in old:
        self.assertAlmostEqual(_dist(OLD_CELL, old[a], old[b]),
                               _dist(self.new_cell, new[a], new[b]), places=4)

  def test_u_invariants_preserved(self):
    old_u = (0.02, 0.03, 0.04, 0.001, 0.005, 0.002)
    ueq_o, det_o = _u_cart_invariants(OLD_CELL, old_u)
    # exact transformation: Ueq and det (principal values) unchanged
    new_u = T.transform_u(old_u, self.r9, OLD_CELL, self.new_cell)
    ueq_n, det_n = _u_cart_invariants(self.new_cell, new_u)
    self.assertAlmostEqual(ueq_o, ueq_n, places=12)
    self.assertAlmostEqual(det_o / det_n, 1.0, places=10)
    # as written to the file (5 decimals)
    written = tuple(float(x) for x in self._atom('C1')[6:12])
    self.assertAlmostEqual(ueq_o, _u_cart_invariants(self.new_cell, written)[0], places=5)

  def test_fixed_coordinate_code_dropped(self):
    # N1 x was 10.25 (fixed at 0.25): transformed from 0.25, no 10 offset
    x = [float(v) for v in self._atom('N1')[2:5]]
    self.assertTrue(all(abs(v) < 2 for v in x))

  def test_other_fields_kept(self):
    self.assertEqual(self._atom('H1A')[5:], ['11.00000', '-1.20000'])
    self.assertEqual(self._atom('Q1')[5:], ['11.00000', '0.05000', '1.23'])
    self.assertIn('DFIX 1.5 C1 N1_$1', self.lines)
    self.assertIn('FVAR 0.5', self.lines)
    self.assertIn('SFAC C H N', self.lines)

  def test_cell_and_symmetry_replaced(self):
    self.assertIn('CELL 0.71073 new', self.lines)
    self.assertIn('ZERR 4 new', self.lines)
    self.assertEqual([l for l in self.lines if l[:4] in ('LATT', 'SYMM')],
                     ['LATT 1', 'SYMM new'])
    # symmetry sits where the old block was: after ZERR, before SFAC
    self.assertLess(self.lines.index('ZERR 4 new'), self.lines.index('LATT 1'))
    self.assertLess(self.lines.index('SYMM new'), self.lines.index('SFAC C H N'))

  def test_eqiv_consistent_with_coordinates(self):
    # C(S x) must equal S'(C x) for any point x
    eq = [l for l in self.lines if l.startswith('EQIV')][0]
    new_op = eq.split(None, 2)[2]
    s_r, s_t = T.parse_symop('-x+1, y+1/2, -z+1/2')
    n_r, n_t = T.parse_symop(new_op)
    x = (0.13, 0.27, 0.41)
    sx = tuple(sum(float(s_r[i][k]) * x[k] for k in range(3)) + float(s_t[i]) for i in range(3))
    lhs = T.transform_xyz(sx, self.r9, self.t)
    cx = T.transform_xyz(x, self.r9, self.t)
    rhs = tuple(sum(float(n_r[i][k]) * cx[k] for k in range(3)) + float(n_t[i]) for i in range(3))
    for a, b in zip(lhs, rhs):
      self.assertAlmostEqual(a, b, places=9)

  def test_symmetry_inserted_when_model_has_none(self):
    model = "TITL p-1\nCELL 0.71073 5 6 7 80 85 95\nZERR 2 0 0 0 0 0 0\nSFAC C\nUNIT 2\nC1 1 0.1 0.2 0.3 11 0.02\nEND\n"
    out = T.transform_model(model, (1, 0, 0, 0, 1, 0, 0, 0, 1), (0, 0, 0),
                            (5, 6, 7, 80, 85, 95), (5, 6, 7, 80, 85, 95),
                            replace={'SYMM': ['LATT 1']}).splitlines()
    self.assertEqual(out[3], 'LATT 1')      # after TITL, CELL, ZERR

  def test_symop_round_trip(self):
    for op in ('-x+1, y+1/2, -z+1/2', 'x, -y, z', '1-X, 0.5+Y, 0.5-Z', '-x+y, -x, z+1/3'):
      r, t = T.parse_symop(op)
      self.assertEqual(T.parse_symop(T.format_symop(r, t)), (r, t))


if __name__ == '__main__':
  unittest.main()
