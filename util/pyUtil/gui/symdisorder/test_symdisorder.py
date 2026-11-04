"""
gui/symdisorder/test_symdisorder.py

gui/__init__.py needs Olex2, so load this package on its own to run these.
"""

import math
import random
import sys

from . import group_other_orientation
from ._core import colour_orientations, complete_complex, is_metal, symm_code


# ---------------------------------------------------------------------------
# colour_orientations
# ---------------------------------------------------------------------------

def _pyrazine_complex():
  """
    M with two axial X and four pyrazines, each disordered over two orientations
    (geometry of NbCl2(pyz)2 in I4/mmm): 32 C, 32 H, 8 N, 2 Cl, 1 Nb.
    """
  atoms = {'M': ('Nb1', (0.0, 0.0, 0.0)),
           'X1': ('Cl1', (0.0, 0.0, 2.404)), 'X2': ('Cl1', (0.0, 0.0, -2.404))}
  bonds = {frozenset(('M', 'X1')), frozenset(('M', 'X2'))}

  def add(key, label, along, across, z, axis, sign):
    x = (sign * along, across, z) if axis == 0 else (across, sign * along, z)
    atoms[key] = (label, x)

  def bond(a, b):
    bonds.add(frozenset((a, b)))

  for axis in (0, 1):
    for sign in (1, -1):
      r = f'{axis}{sign}'
      add(f'N{r}a', 'N1', 2.157, 0.0, 0.0, axis, sign)
      add(f'N{r}b', 'N1', 4.963, 0.0, 0.0, axis, sign)
      bond('M', f'N{r}a')
      for s in (1, -1):
        for t in (1, -1):
          q = f'{r}{s}{t}'
          add(f'Ca{q}', 'C1', 2.867, s * 0.843, t * 0.798, axis, sign)
          add(f'Cb{q}', 'C1', 4.253, s * 0.843, t * 0.798, axis, sign)
          add(f'Ha{q}', 'H1', 2.300, s * 1.519, t * 1.279, axis, sign)
          add(f'Hb{q}', 'H1', 4.820, s * 1.519, t * 1.279, axis, sign)
          bond(f'Ca{q}', f'Cb{q}')
          bond(f'Ca{q}', f'Ha{q}')
          bond(f'Cb{q}', f'Hb{q}')
          bond(f'N{r}a', f'Ca{q}')
          bond(f'N{r}b', f'Cb{q}')
  return atoms, bonds


def test_one_atom_decides_all_rings():
  atoms, bonds = _pyrazine_complex()
  colours, labels, n_sets, n_clashes = colour_orientations(atoms, bonds)
  assert labels == {'C1', 'H1'}
  assert n_sets == 1
  assert n_clashes == 40
  assert sorted(atoms[k][0] for k, c in colours.items() if c == 0).count('C1') == 16
  assert sorted(atoms[k][0] for k, c in colours.items() if c == 0).count('H1') == 16


def test_each_orientation_is_free_of_clashes():
  atoms, bonds = _pyrazine_complex()
  colours = colour_orientations(atoms, bonds)[0]
  for colour in (0, 1):
    keys = [k for k, c in colours.items() if c == colour]
    for i, a in enumerate(keys):
      for b in keys[i + 1:]:
        if atoms[a][0] == atoms[b][0]:
          assert math.dist(atoms[a][1], atoms[b][1]) > 1.75 or frozenset((a, b)) in bonds


def test_ring_stays_planar_and_hydrogens_follow():
  atoms, bonds = _pyrazine_complex()
  colours = colour_orientations(atoms, bonds)[0]
  assert colours['Ca01' + '1' + '1'] == colours['Ca01' + '-1' + '-1']   # across the N...N axis
  assert colours['Ca01' + '1' + '1'] != colours['Ca01' + '1' + '-1']
  assert colours['Hb01' + '1' + '1'] == colours['Ca01' + '1' + '1']     # H with no contact of its own


def test_neighbouring_rings_avoid_the_h_h_contact():
  atoms, bonds = _pyrazine_complex()
  colours = colour_orientations(atoms, bonds)[0]
  # Ha at (2.30, 1.519, z) and (1.519, 2.30, z) are 1.10 A apart
  assert colours['Ha011' + '1'] != colours['Ha111' + '1']


def test_independent_groups_are_reported():
  atoms = {1: ('C1', (0, 0, 0)), 2: ('C1', (1.6, 0, 0)),
           3: ('C2', (20, 0, 0)), 4: ('C2', (21.6, 0, 0))}
  colours, labels, n_sets, n_clashes = colour_orientations(atoms, set())
  assert labels == {'C1', 'C2'} and n_sets == 2 and n_clashes == 2
  assert colours[1] != colours[2] and colours[3] != colours[4]


def test_contradicting_contacts_give_no_split():
  atoms = {1: ('C1', (0, 0, 0)), 2: ('C1', (1.6, 0, 0)), 3: ('C1', (0.8, 1.385, 0))}
  assert colour_orientations(atoms, set())[0] is None


def test_ordered_structure_has_no_disorder():
  atoms = {1: ('C1', (0, 0, 0)), 2: ('C2', (1.4, 0, 0))}
  colours, labels, n_sets, n_clashes = colour_orientations(atoms, {frozenset((1, 2))})
  assert colours == {} and labels == set() and n_clashes == 0


# ---------------------------------------------------------------------------
# group_other_orientation, against a stand-in for the Olex2 scene
# ---------------------------------------------------------------------------

class FakeScene:
  """
    Selection commands as Olex2 has them for grown atoms: every copy but the a.u.
    one has a number sel() prints and another number sel reads, and after grow,
    fuse or kill most numbers in the table lead nowhere.
    """

  def __init__(self, atoms, bonds, top=59, seed=1):
    rng = random.Random(seed)
    self.atoms, self.bonds = atoms, [tuple(sorted(b)) for b in bonds]
    self.reads, self.prints = {}, {}
    self.bare = {}
    for label in sorted({a[0] for a in atoms.values()}):
      copies = sorted(k for k, a in atoms.items() if a[0] == label)
      self.bare[label] = copies
      self.prints[copies[0]] = label
      numbers = rng.sample(range(1, top + 1), len(copies) - 1)
      shown = rng.sample(range(1, top + 1), len(copies) - 1)
      for key, n, p in zip(copies[1:], numbers, shown):
        self.reads[f'{label}_${n}'] = key
        self.prints[key] = f'{label}_${p}'
    self.sel_atoms, self.sel_bonds, self.groups = set(), set(), {}

  def m(self, cmd):
    grouped_atoms = {k for g in self.groups.values() for k in g[0]}
    grouped_bonds = {b for g in self.groups.values() for b in g[1]}
    if cmd == 'sel -u':
      self.sel_atoms, self.sel_bonds = set(), set()
    elif cmd == 'sel atoms where xatom.bai.z > 0':
      self.sel_atoms |= set(self.atoms)
    elif cmd == 'sel atom bonds -a':
      self.sel_bonds |= {b for b in self.bonds if set(b) & self.sel_atoms}
    elif cmd == 'sel bond atoms -a':
      for b in self.sel_bonds:
        self.sel_atoms |= set(b)
    elif cmd.startswith('sel bonds where'):
      need = (lambda x, y: x or y) if '||' in cmd else (lambda x, y: x and y)
      self.sel_bonds |= {b for b in self.bonds
                         if need(b[0] in self.sel_atoms, b[1] in self.sel_atoms)}
    elif cmd == 'sel -i':
      self.sel_atoms = set(self.atoms) - self.sel_atoms - grouped_atoms
      self.sel_bonds = set(self.bonds) - self.sel_bonds - grouped_bonds
    elif cmd.startswith('group -n='):
      self.groups[cmd[9:]] = (set(self.sel_atoms), set(self.sel_bonds))
      self.sel_atoms, self.sel_bonds = set(), set()
    elif cmd.startswith('sel '):
      for name in cmd.split()[1:]:
        if name in self.bare:
          self.sel_atoms |= set(self.bare[name])
        elif name in self.reads:
          self.sel_atoms.add(self.reads[name])
    else:
      raise ValueError(cmd)

  def f(self, expr):
    if expr == 'sel()':
      words = [self.prints[k] for k in sorted(self.sel_atoms)]
      return ' '.join(words + [self.prints[k] for b in sorted(self.sel_bonds) for k in b])
    if expr == 'crd()':
      xyz = [self.atoms[k][1] for k in self.sel_atoms] or [(0.0, 0.0, 0.0)]
      return ' '.join('%.3f' % (sum(x[i] for x in xyz) / len(xyz)) for i in range(3))
    raise ValueError(expr)

  def Info(self, label, f=True, p=6):
    return '\n'.join('%s X %.6f %.6f %.6f 0.1' % (a[0], *a[1])
                     for a in self.atoms.values() if a[0] == label)


def _click_and_run(scene, key, monkeypatch=None):
  saved = {n: sys.modules.get(n) for n in ('olex', 'olx')}
  sys.modules['olex'] = scene
  sys.modules['olx'] = scene
  try:
    scene.sel_atoms, scene.sel_bonds = {key}, set()
    group_other_orientation()
  finally:
    for n, module in saved.items():
      if module is None:
        del sys.modules[n]
      else:
        sys.modules[n] = module
  return scene.groups.get('dp1')


def _check_group(atoms, bonds, group, clicked):
  group_atoms, group_bonds = group
  assert clicked not in group_atoms
  assert sorted(atoms[k][0] for k in group_atoms) == ['C1'] * 16 + ['H1'] * 16
  assert len(group_bonds) == 40
  for i, a in enumerate(sorted(group_atoms)):
    for b in sorted(group_atoms)[i + 1:]:
      if atoms[a][0] == atoms[b][0] and frozenset((a, b)) not in bonds:
        assert math.dist(atoms[a][1], atoms[b][1]) > 1.75


def test_group_when_printed_numbers_lead_nowhere():
  atoms, bonds = _pyrazine_complex()
  scene = FakeScene(atoms, bonds)
  clicked = next(k for k in scene.reads.values() if atoms[k][0] == 'C1')
  _check_group(atoms, bonds, _click_and_run(scene, clicked), clicked)


def test_group_when_the_clicked_atom_is_the_au_copy():
  atoms, bonds = _pyrazine_complex()
  scene = FakeScene(atoms, bonds)
  clicked = scene.bare['C1'][0]
  _check_group(atoms, bonds, _click_and_run(scene, clicked), clicked)


def test_group_with_a_small_numbering_table():
  atoms, bonds = _pyrazine_complex()
  scene = FakeScene(atoms, bonds, top=31)
  clicked = next(k for k in scene.reads.values() if atoms[k][0] == 'H1')
  _check_group(atoms, bonds, _click_and_run(scene, clicked), clicked)


def test_ordered_atom_makes_no_group():
  atoms, bonds = _pyrazine_complex()
  scene = FakeScene(atoms, bonds)
  assert _click_and_run(scene, 'M') is None


# ---------------------------------------------------------------------------
# complete_complex (cell and asymmetric unit of NbCl2(pyz)2, I4/mmm)
# ---------------------------------------------------------------------------

NB_CELL = (7.1195, 7.1195, 10.684, 90, 90, 90)
NB_ATOMS = [('Nb1', 'Nb', (0.5, 0.5, 0.5)),
            ('Cl1', 'Cl', (0.5, 0.5, 0.725035)),
            ('N1', 'N', (0.802909, 0.5, 0.5)),
            ('C1', 'C', (0.902634, 0.618453, 0.574689)),
            ('H1', 'H', (0.823027, 0.713402, 0.619717))]
NB_RADII = {'Nb': 1.47, 'Cl': 0.99, 'N': 0.71, 'C': 0.75, 'H': 0.32}


def _i4mmm_ops():
  half = (0.5, 0.5, 0.5)
  rotations = [((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, -1, 0), (0, 0, 1)),
               ((0, -1, 0), (1, 0, 0), (0, 0, 1)), ((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
               ((-1, 0, 0), (0, 1, 0), (0, 0, -1)), ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
               ((0, 1, 0), (1, 0, 0), (0, 0, -1)), ((0, -1, 0), (-1, 0, 0), (0, 0, -1))]
  rotations += [tuple(tuple(-v for v in row) for row in r) for r in rotations]
  return [(r, (0.0, 0.0, 0.0)) for r in rotations] + [(r, half) for r in rotations]


def _complex_counts(ops=None):
  codes, strays = complete_complex(NB_CELL, NB_ATOMS, ops or _i4mmm_ops(), 0, NB_RADII)
  counts = {a[0]: 1 for a in NB_ATOMS}
  for labels in codes.values():
    for label in labels:
      counts[label] += 1
  return counts, strays, codes


def test_complex_has_one_metal_and_whole_rings():
  counts, strays, _ = _complex_counts()
  assert counts == {'Nb1': 1, 'Cl1': 2, 'N1': 8, 'C1': 32, 'H1': 32}
  assert strays == []


def test_complex_never_generates_another_metal():
  _, _, codes = _complex_counts()
  assert not any('Nb1' in labels for labels in codes.values())


def test_symm_code_format():
  assert symm_code(((1, 0, 0), (0, -1, 0), (0, 0, 1)), (0, 1, 0)) == '+X,1-Y,+Z'
  assert symm_code(((-1, 0, 0), (0, 1, 0), (0, 0, -1)), (2, 0, 1)) == '2-X,+Y,1-Z'
  assert symm_code(((0, 1, 0), (1, 0, 0), (0, 0, 1)), (-1, 0.5, 0)) == '-1+Y,0.5+X,+Z'


def test_is_metal():
  assert is_metal('Nb') and is_metal('Fe') and not is_metal('C') and not is_metal('Cl')
