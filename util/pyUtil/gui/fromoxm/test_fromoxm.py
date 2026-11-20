"""Tests for gui/fromoxm/_core.py (no Olex2 needed): python test_fromoxm.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _core as C  # noqa: E402

# a real sample, if this machine has it (user data, not shipped)
REAL = os.environ.get('FROMOXM_OXM',
                      r'C:\Users\Horst\Documents\RSC\Prana_26_11_14\Frag1b.oxm')

# monoclinic cell, two atoms; O1 drawn at identity and at 1/2-X,1/2+Y,1/2-Z,
# C2 at identity only and hidden
CELL = {'a': 10.0, 'b': 5.0, 'c': 8.0, 'alpha': 90.0, 'beta': 100.0, 'gamma': 90.0}


def _model(order_swapped=False):
  m = C.cell_matrix(CELL)
  o1, c2 = (0.1, 0.2, 0.3), (0.4, 0.1, 0.2)
  ops = [C.IDENTITY, '1/2-X,1/2+Y,1/2-Z']
  drawn = [(0, 0, o1), (1, 0, c2), (0, 1, C.apply_symop(ops[1], o1))]
  ids = {0: 1, 1: 0} if order_swapped else {0: 0, 1: 1}
  atoms = ''.join('     <Atom atom_id="%d" crd="%s" matrix_id="%d">\n'
                  % (ids[k], ','.join('%.6f' % x for x in C.to_cart(m, f)), op)
                  for k, op, f in drawn)
  # visibility: 3 atoms, bits 1,1,0 -> 0b011 = 3 -> 'Aw==' + '3'
  return '''<olex_model version="1"
 <XFiles
  <0 FileName="x.oxm"
   <Lattice delta="0.5"
    <AUnit
     <cell a="10.0(1)" alpha="90" b="5.0" beta="100" c="8.0" gamma="90">
     <symm latt="1"
      <symmop "-X,1/2+Y,1/2-Z">
     >
     <residues
      <default
       <atom label="O1" type="O" x="0.1" y="0.2" z="0.3"
       >
       <atom label="C2" type="C" x="0.4" y="0.1" z="0.2"
       >
       <atom label="Q1" type="Q" x="0.9" y="0.9" z="0.9"
       >
       <atom label="N3" type="N" x="0.2" y="0.3" z="0.1"
       >
      >
     >
    >
    <Matrices
     <symop "+X,+Y,+Z" id="1">
     <symop "1/2-X,1/2+Y,1/2-Z" id="2">
    >
    <Atoms
%s    >
    <Bonds
    >
    <Planes
     <Plane def_id="0" normal="0,0,1" ns="1.5"
      <atom "1" a_id="0" au_id="0" m_id="1">
      <atom "1" a_id="1" au_id="0" m_id="1">
      <atom "1" a_id="3" au_id="0" m_id="1">
     >
     <Plane def_id="0" normal="0,0,1" ns="1.5"
      <atom "1" a_id="0" au_id="0" m_id="2">
      <atom "1" a_id="1" au_id="0" m_id="2">
      <atom "1" a_id="3" au_id="0" m_id="2">
     >
    >
   >
  >
 >
 <Style LinkFile="./etc/styles/x.glsp" Name="" Version="2"
  <Materials
  >
 >
 <NameRegistry
  <Planes
   <item id="d41d8" value="ring">
  >
  <Atoms>
 >
 <Basis zoom="0.05"
  <matrix xx="1" xy="0" xz="0" yx="0" yy="0" yz="1" zx="0" zy="-1" zz="0">
  <center x="1.5" y="2" z="-3">
 >
 <Visibility atoms="Aw==3" basis="true">
 <Lines
  <object "dots" base="%s" edge="9,9,9" r="0.8"
   <Label center="0,0,0" font_id="5" offset="0,0,0" text="1" visible="false">
  >
 >
>''' % (atoms, ','.join('%.6f' % x for x in C.to_cart(m, o1)))


class CoreTest(unittest.TestCase):
  def test_parse_pairs_hidden_and_view(self):
    s = C.parse(_model())
    self.assertEqual(s['labels'], ['O1', 'C2', 'N3'])
    self.assertEqual([a[0] for a in s['au']], ['O1', 'C2', 'N3'])
    self.assertEqual(s['drawn'], [('O1', C.IDENTITY, True), ('C2', C.IDENTITY, True),
                                  ('O1', '1/2-X,1/2+Y,1/2-Z', False)])
    self.assertEqual(s['view']['zoom'], 0.05)
    self.assertEqual(s['cell']['a'], 10.0)

  def test_wrong_atom_order_is_found_by_position(self):
    self.assertEqual(C.parse(_model(order_swapped=True))['drawn'],
                     C.parse(_model())['drawn'])

  def test_grow_and_view(self):
    s = C.parse(_model())
    cmds, missing = C.commands(s, ['o1', 'C2', 'N3'], ('grow', 'view'))
    self.assertEqual(missing, [])
    self.assertEqual(cmds[0], 'fuse')
    self.assertEqual(cmds[1], 'sgen 1/2-X,1/2+Y,1/2-Z o1')
    self.assertNotIn('hide', ' '.join(cmds))  # O1 has two copies: not hidden
    self.assertEqual(cmds[2], 'matr 1.000000 0.000000 0.000000 0.000000 0.000000 '
                              '-1.000000 0.000000 1.000000 0.000000')
    self.assertEqual(cmds[3], 'center -1.500000 -2.000000 3.000000')
    self.assertEqual(cmds[4], 'gl.Zoom -a 0.050000')
    cmds, missing = C.commands(s, ['C2'], ('grow',))
    self.assertEqual(missing, ['O1'])
    self.assertEqual(cmds, ['fuse'])

  def test_all_parts_in_order(self):
    s = C.parse(_model())
    self.assertEqual(s['planes'], [{'name': 'ring', 'labels': ['O1', 'C2', 'N3']}])
    self.assertIn('LinkFile=""', s['style'])
    self.assertTrue(s['style'].startswith('<style '))
    # the model now: O1 moved a little; the line end follows it
    current = {'O1': (0.11, 0.2, 0.3), 'C2': (0.4, 0.1, 0.2), 'N3': (0.2, 0.3, 0.1)}
    cmds, _ = C.commands(s, ['O1', 'C2', 'N3'], C.PARTS, current=current,
                         current_cell=CELL)
    kinds = [c.split()[0] for c in cmds]
    # never 'load style': it would lose the atoms' draw styles (ellipsoids)
    self.assertEqual(kinds, ['fuse', 'mpln', 'sgen', 'line', 'matr', 'center', 'gl.Zoom'])
    self.assertEqual(cmds[1], 'mpln -n=ring O1 C2 N3')
    end = C.to_cart(C.cell_matrix(CELL), current['O1'])
    self.assertEqual(cmds[3], 'line -n=dots %s 9.000000 9.000000 9.000000'
                     % ' '.join('%.6f' % x for x in end))
    # without the model's coordinates the end stays where it was
    cmds, _ = C.commands(s, ['O1', 'C2', 'N3'], ('lines',))
    self.assertNotIn('%.6f' % end[0], cmds[0])

  def test_cell_differences(self):
    other = dict(CELL, b=5.5, beta=103.0)
    self.assertEqual(len(C.cell_differences(CELL, other)), 2)
    self.assertEqual(C.cell_differences(CELL, dict(CELL, a=10.05)), [])

  def test_symop_is_checked(self):
    with self.assertRaises(C.SampleError):
      C.apply_symop('__import__("os")', (0, 0, 0))

  def test_space_group(self):
    s = C.parse(_model())
    self.assertEqual((s['latt'], s['group']), (1, ['-X,1/2+Y,1/2-Z']))
    self.assertEqual(len(C.group(s['group'], s['latt'])), 4)  # P2/c
    self.assertEqual(len(C.group([], -7)), 2)  # C centred, not centric
    R, t = C.symop_matrix('1/2-X,-1+Y,3/2-Z')
    self.assertEqual(R, [[-1, 0, 0], [0, 1, 0], [0, 0, -1]])
    self.assertEqual(C.format_symop(R, t), '1/2-X,-1+Y,3/2-Z')

  def test_atoms_are_found_by_position_under_other_names(self):
    s = C.parse(_model())
    current = [('O9', (0.9, 0.8, 0.7), 'O'),       # O1, inverted (1-X,1-Y,1-Z)
               ('C2', (0.4, 0.1, 0.2), 'C'),        # where it was
               ('N7', (0.205, 0.3, 0.1), 'N'),      # N3, 0.05 A off
               ('C5', (0.6, 0.6, 0.6), 'C')]        # not in the sample
    pairs, lost, extra = C.match_atoms(s, current, CELL)
    self.assertEqual(sorted(pairs), ['C2', 'N3', 'O1'])
    self.assertEqual(pairs['C2'][:2], ('C2', None))
    self.assertEqual(pairs['N3'][:2], ('N7', None))
    self.assertEqual(pairs['O1'][0], 'O9')
    R, t = C.symop_matrix(pairs['O1'][1])
    moved = C._apply(R, t, (0.9, 0.8, 0.7))
    for a, b in zip(moved, (0.1, 0.2, 0.3)):
      self.assertAlmostEqual(a, b)
    self.assertEqual((lost, extra), ([], ['C5']))
    # a different element is never paired, however close
    pairs, lost, _ = C.match_atoms(s, [('S1', (0.1, 0.2, 0.3), 'S')], CELL)
    self.assertEqual(pairs, {})
    # renaming through temporary names
    self.assertEqual(C.renamed(C.match_atoms(s, current, CELL)[0]), [('N7', 'N3'), ('O9', 'O1')])
    cmds = C.rename_commands(C.match_atoms(s, current, CELL)[0], [a[0] for a in current])
    self.assertEqual(len(cmds), 4)
    self.assertTrue(cmds[0].startswith('name N7 NZ'))
    self.assertTrue(cmds[2].endswith(' N3') and cmds[3].endswith(' O1'))
    # commands use the model's names and move O9 first
    cmds, _ = C.commands(s, [a[0] for a in current], ('grow',), pairs=C.match_atoms(
      s, current, CELL)[0])
    self.assertEqual(cmds[0], 'fuse')
    self.assertTrue(cmds[1].startswith('sgen -m ') and cmds[1].endswith(' O9'))
    self.assertEqual(cmds[2], 'sgen 1/2-X,1/2+Y,1/2-Z O9')

  def test_swapped_names(self):
    pairs = {'C1': ('C2', None, 0.0), 'C2': ('C1', None, 0.0)}
    cmds = C.rename_commands(pairs, ['C1', 'C2'])
    temps = [c.split()[2] for c in cmds[:2]]
    self.assertNotIn('C1', temps)
    self.assertNotIn('C2', temps)
    self.assertEqual(sorted(c.split()[2] for c in cmds[2:]), ['C1', 'C2'])

  def test_style_materials(self):
    style = chr(10).join([
      '<style Name="" Version="2"', ' <Materials', '  <Prop0 "85;9;9;9;9">', ' >',
      ' <Root Name="Root"', '  <SubStyles',
      '   <S_0 Name="AtomParams" DefDS="2">',
      '   <S_1 Name="dots" PMask="6144"', '    <S0 PName="Balls bond"',
      '     <Material style.Materials.Prop0>', '    >', '   >',
      '  >', ' >', '>', ''])
    self.assertEqual(C.style_materials(style), [('dots', 'Balls bond', '85;9;9;9;9')])
    self.assertEqual(C.style_materials(''), [])

  @unittest.skipUnless(os.path.isfile(REAL), 'no real sample here')
  def test_real_style_materials(self):
    mats = C.style_materials(C.parse(C.read_model(REAL))['style'])
    names = set(n for n, _, _ in mats)
    self.assertIn(('dots', 'Balls bond'), set((n, p) for n, p, _ in mats))
    self.assertNotIn('AtomParams', names)  # settings, not colours: never touched
    # the scene's own entries (console, background, legend ...) belong to the theme
    for gui in ('Console', 'Background', 'AtomLegend', 'InfoBox', 'PLabels'):
      self.assertNotIn(gui, names)
    self.assertTrue({'C', 'O-H', 'TXPlane0'} <= names)
    self.assertTrue(all(';' in m for _, _, m in mats))

  @unittest.skipUnless(os.path.isfile(REAL), 'no real sample here')
  def test_real_sample(self):
    s = C.parse(C.read_model(REAL))
    self.assertEqual(len(s['labels']), 49)  # 54 less 5 Q-peaks
    self.assertEqual(len(s['lines']), 4)
    self.assertEqual(s['lines'][0]['name'], 'dots')
    self.assertEqual([len(p['labels']) for p in s['planes']], [6, 6])  # two rings
    self.assertIn('Name="dots"', s['style'])
    self.assertEqual(len(s['symops']), 7)
    self.assertEqual(len(s['drawn']), 294)  # the 5 hidden Q-peaks left out
    self.assertEqual(sum(1 for _, _, v in s['drawn'] if not v), 0)
    cmds, missing = C.commands(s, s['labels'])
    self.assertEqual(missing, [])
    # the sample against itself: every atom found where it is
    pairs, lost, extra = C.match_atoms(s, s['au'], s['cell'])
    self.assertEqual((len(pairs), lost, extra), (49, [], []))
    self.assertTrue(all(move is None for _, move, _ in pairs.values()))
    self.assertEqual(len(set(c.split()[1] for c in cmds if c.startswith('sgen'))), 6)
    self.assertTrue(cmds[-3].startswith('matr '))


if __name__ == '__main__':
  unittest.main()
