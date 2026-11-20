"""
gui/symsnap/test_symsnap.py

gui/__init__.py needs Olex2, so load this package on its own to run these.
Fixture: the water in C:/Users/Horst/Documents/RSC/CC-COM-11-2026-007207 (I2/a),
O1 on the 2-fold axis 1/2-x, y, 1-z with two half H atoms.
"""

from ._core import merge_plan, metric, length

CELL = (12.2314, 6.277, 50.463, 90.0, 90.318, 90.0)


def _i2a_ops():
  base = [(((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0.0, 0.0, 0.0)),
          (((-1, 0, 0), (0, 1, 0), (0, 0, -1)), (0.5, 0.0, 0.0)),
          (((-1, 0, 0), (0, -1, 0), (0, 0, -1)), (0.0, 0.0, 0.0)),
          (((1, 0, 0), (0, -1, 0), (0, 0, 1)), (0.5, 0.0, 0.0))]
  return base + [(r, tuple(t + 0.5 for t in tr)) for r, tr in base]


O1 = ('O1', 'O', (0.25, 0.326996, 0.5), 0.5)
H1A = ('H1a', 'H', (0.239359, 0.418378, 0.513394), 0.5)
H1B = ('H1b', 'H', (0.283245, 0.404355, 0.488411), 0.5)


def _close(a, b, eps=1e-5):
  return all(abs(x - y) < eps for x, y in zip(a, b))


def test_water_h_merge_into_one_full_h():
  plan = merge_plan(CELL, _i2a_ops(), [O1, H1A, H1B])
  assert len(plan) == 1, plan
  step = plan[0]
  assert step['keep'] == 'H1a' and step['remove'] == ['H1b']
  # H1a's own position, averaged with the image of H1b next to it
  assert _close(step['xyz'], (0.228057, 0.411367, 0.512492), 1e-5), step['xyz']
  assert abs(step['occu'] - 1.0) < 1e-9 and step['site'] == 1 and not step['overfull']
  # O-H 0.87 A, H...H' 1.37 A through the 2-fold
  G = metric(CELL)
  x = step['xyz']
  oh = length(G, [x[i] - O1[2][i] for i in range(3)])
  hh = length(G, [x[0] - (0.5 - x[0]), 0.0, x[2] - (1 - x[2])])
  assert abs(oh - 0.866) < 0.005, oh
  assert abs(hh - 1.370) < 0.005, hh


def test_atom_on_special_position_is_left_alone():
  assert merge_plan(CELL, _i2a_ops(), [O1]) == []


def test_atom_near_axis_is_snapped_on_it():
  near = ('H9', 'H', (0.26, 0.40, 0.502), 0.5)
  plan = merge_plan(CELL, _i2a_ops(), [near])
  assert len(plan) == 1
  step = plan[0]
  assert _close(step['xyz'], (0.25, 0.40, 0.5)), step['xyz']
  assert step['site'] == 2 and step['remove'] == [] and abs(step['occu'] - 0.5) < 1e-9
  assert not step['overfull']


def test_full_atom_snapped_is_overfull():
  near = ('H9', 'H', (0.26, 0.40, 0.502), 1.0)
  assert merge_plan(CELL, _i2a_ops(), [near])[0]['overfull']


def test_different_elements_and_far_atoms_are_not_merged():
  far = ('H2', 'H', (0.10, 0.10, 0.10), 1.0)
  plan = merge_plan(CELL, _i2a_ops(), [H1A, far])
  assert plan == []
  near_o = ('O2', 'O', H1B[2], 0.5)
  assert merge_plan(CELL, _i2a_ops(), [H1A, near_o]) == []


def test_tolerance_is_honoured():
  assert merge_plan(CELL, _i2a_ops(), [H1A, H1B], tol=0.2) == []
  assert len(merge_plan(CELL, _i2a_ops(), [H1A, H1B], tol=0.5)) == 1


def run_all():
  failed = 0
  tests = [(k, v) for k, v in globals().items() if k.startswith('test_') and callable(v)]
  for name, fn in tests:
    try:
      fn()
      print("PASS", name)
    except Exception as e:
      failed += 1
      print("FAIL", name, repr(e))
  print(f"{len(tests) - failed} passed, {failed} failed")
  return failed
