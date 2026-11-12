"""Tidying free variables in .res text; no Olex2 needed."""
import os
import sys
import unittest

RESTRAINTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RESTRAINTS)
sys.path.insert(0, os.path.join(os.path.dirname(RESTRAINTS), 'db'))
import fvar_sanitise as fs
import part_sanitise as ps
import form
import style

RES = """TITL x
CELL 0.71 10 10 10 90 90 90
SFAC C H
UNIT 1 1
L.S. 4
SADI_1 c1 c2
WGHT    0.1
FVAR       0.08197   0.48650   0.48897   0.70917   0.52899
C0    1    0.1    0.1    0.1    11.00000    0.01    0.02 =
         0.03    0.00    0.00    0.00
PART 1 21
C1    1    0.1    0.2    0.3    21.00000    0.01    0.02 =
         0.03    0.00    0.00    0.00
AFIX  43
H1    2    0.1    0.2    0.3    21.00000   -1.20000
AFIX   0
PART 2 -21
C1'   1    0.1    0.2    0.3   -21.00000    0.01
PART 3 31
C2    1    0.1    0.2    0.3    31.00000    0.01
PART 4 -31
C2'   1    0.1    0.2    0.3   -31.00000    0.01
PART 5 41
C3    1    0.1    0.2    0.3    41.00000    0.01
PART 6 -41
C3'   1    0.1    0.2    0.3   -41.00000    0.01
PART 7 51
C4    1    0.1    0.2    0.3    51.00000    0.01
PART 8 -51
C4'   1    0.1    0.2    0.3   -51.00000    0.01
PART 0
HKLF 4
END
"""


def occupancies(text):
  """{atom: real occupancy} from the FVAR line and sof codes."""
  lines = text.splitlines(True)
  values, _, _ = fs._read(lines)
  out = {}
  for card in fs._cards(lines):
    tokens = fs._tokens(lines, card)
    if tokens and fs._is_atom(tokens):
      code = float(tokens[5])
      used = fs.decode(code)
      if used:
        v = values[used[0]]
        out[tokens[0]] = used[1] * (v if code > 0 else 1 - v)
      else:
        out[tokens[0]] = abs(code) - 10
  return out


class CodesTest(unittest.TestCase):
  def test_decode(self):
    self.assertEqual(fs.decode(21.0), (2, 1.0))
    self.assertEqual(fs.decode(-81.0), (8, 1.0))
    self.assertEqual(fs.decode(30.5), (3, 0.5))
    self.assertIsNone(fs.decode(11.0))
    self.assertIsNone(fs.decode(0.3))
    self.assertIsNone(fs.decode(-1.2))

  def test_encode(self):
    self.assertEqual(fs.encode(81.0, 2, False), 21.0)
    self.assertEqual(fs.encode(81.0, 2, True), -21.0)
    self.assertEqual(fs.encode(-81.0, 2, True), 21.0)
    self.assertEqual(fs.encode(30.5, 2, True), -20.5)


class GroupsTest(unittest.TestCase):
  def test_same(self):
    self.assertEqual(fs.groups({2: 0.40, 3: 0.41}), [(2, [(3, False)])])

  def test_complement(self):
    self.assertEqual(fs.groups({2: 0.8, 3: 0.2}), [(2, [(3, True)])])

  def test_nothing_alike(self):
    self.assertEqual(fs.groups({2: 0.10, 3: 0.30, 4: 0.75 - 0.3}), [])

  def test_a_chain_is_not_merged_end_to_end(self):
    found = fs.groups({2: 0.10, 3: 0.125, 4: 0.15})
    self.assertEqual(found, [(2, [(3, False)])])

  def test_values_outside_0_to_1_are_ignored(self):
    self.assertEqual(fs.groups({2: 1.2, 3: 1.21, 4: -0.01}), [])

  def test_the_example(self):
    values = {2: .4865, 3: .48897, 4: .46736, 5: .70917, 6: .92481, 7: .85362, 8: .52899}
    self.assertEqual(fs.groups(values), [(2, [(3, False), (4, False), (8, True)])])


class PlanTest(unittest.TestCase):
  def test_merge_and_renumber(self):
    p = fs.plan(RES)
    self.assertEqual(p.merges[0][:2], (2, [(3, False), (5, True)]))
    self.assertEqual(p.mapping, {2: (2, False), 3: (2, False), 4: (3, False), 5: (2, True)})
    self.assertEqual(len(p.values), 3)
    self.assertAlmostEqual(p.values[0], 0.08197)
    self.assertAlmostEqual(p.values[1], (.4865 + .48897 + (1 - .52899)) / 3)
    self.assertAlmostEqual(p.values[2], .70917)

  def test_apply_rewrites_every_reference(self):
    new = fs.apply(RES, fs.plan(RES))
    self.assertIn('C2    1    0.1    0.2    0.3    21.00000', new)
    self.assertIn("C2'   1    0.1    0.2    0.3   -21.00000", new)
    self.assertIn('C3    1    0.1    0.2    0.3    31.00000', new)  # FV 4 is now FV 3
    self.assertIn('C4    1    0.1    0.2    0.3    -21.00000', new)  # the complement
    self.assertNotIn('51.00000', new)
    self.assertIn('PART 3 21\n', new)
    self.assertIn('PART 7 -21\n', new)
    self.assertIn('PART 8 21\n', new)
    self.assertIn('PART 5 31\n', new)
    self.assertIn('PART 1 21\n', new)
    self.assertEqual(sum(l.startswith('FVAR') for l in new.splitlines()), 1)

  def test_afix_codes_are_not_variables(self):
    # AFIX 43 once read as a reference to free variable 4
    self.assertEqual(fs.plan(RES).locked, [])

  def test_occupancies_barely_move(self):
    before, after = occupancies(RES), occupancies(fs.apply(RES, fs.plan(RES)))
    self.assertEqual(sorted(before), sorted(after))
    for atom in before:
      self.assertAlmostEqual(before[atom], after[atom], delta=0.03, msg=atom)

  def test_only_the_changed_lines_change(self):
    new = fs.apply(RES, fs.plan(RES)).splitlines()
    self.assertIn("C0    1    0.1    0.1    0.1    11.00000    0.01    0.02 =", new)
    self.assertIn("SADI_1 c1 c2", new)
    self.assertEqual(new[-2:], ['HKLF 4', 'END'])

  def test_clean_file_gives_no_plan(self):
    text = RES.replace('0.48897', '0.40000').replace('0.52899', '0.20000')
    self.assertIsNone(fs.plan(text))

  def test_second_pass_finds_nothing(self):
    self.assertIsNone(fs.plan(fs.apply(RES, fs.plan(RES))))

  def test_unused_variable_is_dropped(self):
    text = RES.replace('0.48897', '0.40000').replace('0.52899', '0.20000')
    text = text.replace('C4\'   1    0.1    0.2    0.3   -51.00000', "C4'   1    0.1    0.2    0.3    11.00000")
    text = text.replace('C4    1    0.1    0.2    0.3    51.00000', 'C4    1    0.1    0.2    0.3    11.00000')
    text = text.replace('PART 7 51', 'PART 7').replace('PART 8 -51', 'PART 8')
    p = fs.plan(text)
    self.assertEqual(p.unused, [5])
    self.assertEqual(len(p.values), 4)

  def test_sump_locks_its_variables(self):
    # 3 and 5 were the only partners of 2, so nothing is left to merge
    text = RES.replace('WGHT    0.1', 'WGHT    0.1\nSUMP 1 0.01 1 3 1 5')
    self.assertIsNone(fs.plan(text))

  def test_a_locked_variable_keeps_its_number_when_others_move(self):
    text = RES.replace('WGHT    0.1', 'WGHT    0.1\nDFIX 41.0 0.01 C3 C4')
    p = fs.plan(text)
    self.assertEqual(p.locked, [4])
    self.assertEqual(p.mapping[4], (4, False))
    new = fs.apply(text, p)
    self.assertIn('DFIX 41.0 0.01 C3 C4', new)
    self.assertIn('41.00000', new)

  def test_coordinate_reference_locks(self):
    text = RES.replace('C2    1    0.1    0.2    0.3    31.00000',
                       'C2    1    31.00000    0.2    0.3    31.00000')
    self.assertIn(3, fs.plan(text).locked)

  def test_keeps_windows_line_ends(self):
    text = RES.replace('\n', '\r\n')
    new = fs.apply(text, fs.plan(text))
    self.assertEqual(new.count('\n'), new.count('\r\n'))

  def test_two_fvar_lines_become_one_block(self):
    text = RES.replace('0.70917   0.52899', '0.70917\nFVAR    0.52899')
    new = fs.apply(text, fs.plan(text))
    self.assertEqual(sum(l.startswith('FVAR') for l in new.splitlines()), 1)

  def test_describe(self):
    words = '\n'.join(fs.describe(fs.plan(RES)))
    self.assertIn('FV 2, FV 3, 1 - FV 5 are one variable', words)
    self.assertIn('FV 4 to 3', words)


class TicksTest(unittest.TestCase):
  def test_all_ticked_is_the_full_plan(self):
    self.assertEqual(fs.plan(RES, include={2, 3, 5}), fs.plan(RES))

  def test_unticked_variable_stays(self):
    p = fs.plan(RES, include={2, 3})
    self.assertEqual(p.merges[0][:2], (2, [(3, False)]))
    self.assertEqual(p.mapping[5], (4, False))  # kept, renumbered into the gap
    self.assertEqual(len(p.values), 4)

  def test_keeper_can_be_unticked(self):
    p = fs.plan(RES, include={3, 5})
    self.assertEqual(p.merges[0][:2], (3, [(5, True)]))
    self.assertEqual(p.mapping[2], (2, False))
    new = fs.apply(RES, p)
    self.assertIn('PART 7 -31\n', new)

  def test_one_tick_in_a_group_merges_nothing(self):
    self.assertIsNone(fs.plan(RES, include={2}))

  def test_nothing_ticked(self):
    self.assertIsNone(fs.plan(RES, include=set()))

  def test_unused_variables_go_even_with_no_ticks(self):
    text = RES.replace('0.70917   0.52899', '0.70917   0.52899   0.10000')
    p = fs.plan(text, include=set())
    self.assertEqual(p.unused, [6])
    self.assertEqual(p.merges, [])

  def test_two_passes_make_two_pairs(self):
    values = 'FVAR 0.1 0.50 0.505 0.51 0.515'
    atoms = ''.join('C%d 1 0.1 0.1 0.1 %d1.00000 0.01\n' % (n, n) for n in (2, 3, 4, 5))
    text = 'TITL x\n%s\n%sHKLF 4\nEND\n' % (values, atoms)
    first = fs.apply(text, fs.plan(text, include={2, 3}))
    self.assertEqual(len(fs._read(first.splitlines(True))[0]), 4)
    # now FV 2 is the merged pair, and the old 4 and 5 are 3 and 4
    second = fs.apply(first, fs.plan(first, include={3, 4}))
    values = fs._read(second.splitlines(True))[0]
    self.assertEqual(len(values), 3)
    self.assertAlmostEqual(values[2], 0.5025)
    self.assertAlmostEqual(values[3], 0.5125)


class DialogTest(unittest.TestCase):
  P = style.palette()

  def test_locations(self):
    loc = fs.locations("RESI 2\nPART 1 21\nC1 1 0.1 0.1 0.1 21.0 0.01\nH1 2 0.1 0.1 0.1 21.0 -1.2\n"
                       "PART 2 -21\nC2 1 0.1 0.1 0.1 -21.0 0.01\nHKLF 4\n")
    self.assertEqual(loc[2], {'residues': ['2'], 'parts': ['1', '2'], 'atoms': 3, 'first': 'C1'})
    self.assertEqual(fs.where(loc[2]), 'residue 2, PART 1/2, 3 atoms from C1')

  def test_page(self):
    html = fs.page(RES, form, self.P)
    for tag in ('table', 'tr', 'td', 'font'):
      self.assertEqual(html.count('<%s ' % tag) + html.count('<%s>' % tag), html.count('</%s>' % tag), tag)
    for n in (2, 3, 5):
      self.assertIn('name="%s" checked="true"' % fs.tick_name(n), html)
    self.assertNotIn(fs.tick_name(4), html)
    self.assertIn('(1 - 0.471)', html)
    self.assertIn('sanitise_FVARs_close(True)', html)
    self.assertIn('sanitise_FVARs_close(False)', html)

  def test_page_lists_unused(self):
    text = RES.replace('0.70917   0.52899', '0.70917   0.52899   0.10000')
    self.assertIn('Not used by any atom: FV 6', fs.page(text, form, self.P))


def structure(body, fvar='0.1 0.4 0.3', symm='', latt=-1):
  """A 10 A cubic cell: fractional 0.1 is 1 A."""
  return ('TITL x\nCELL 0.71 10 10 10 90 90 90\nZERR 1 0 0 0 0 0 0\nLATT %d\n%sSFAC C H\nUNIT 1 1\n'
          'FVAR %s\n%sHKLF 4\nEND\n' % (latt, symm, fvar, body))


def atom(name, x, code):
  return '%s 1 %.3f 0.5 0.5 %s 0.05\n' % (name, x, code)


FAR = ('PART 1 21\n' + atom('A1', .10, '21') + 'PART 2 -21\n' + atom('A2', .12, '-21') +
       'PART 3 31\n' + atom('B1', .60, '31') + 'PART 4 -31\n' + atom('B2', .62, '-31') + 'PART 0\n')
NEAR = FAR.replace('.600', '.200').replace('0.620', '0.220').replace('.620', '.220')


class PartTest(unittest.TestCase):
  def numbers(self, text):
    return [l.split()[1] for l in text.splitlines() if l.startswith('PART')]

  def test_far_apart_pairs_share_1_2(self):
    p = ps.plan(structure(FAR))
    self.assertEqual(p.mapping, {3: 1, 4: 2})
    self.assertEqual(self.numbers(ps.apply(structure(FAR), p)), ['1', '2', '1', '2', '0'])

  def test_keeps_the_occupancy_on_the_part_line(self):
    new = ps.apply(structure(FAR), ps.plan(structure(FAR)))
    self.assertIn('PART 1 31\n', new)
    self.assertIn('PART 2 -31\n', new)

  def test_pairs_that_would_bond_keep_separate_sets(self):
    text = structure(FAR.replace('0.600', '0.200').replace('0.620', '0.220'))
    self.assertIsNone(ps.plan(text))

  def test_sets_are_compacted_around_a_clash(self):
    body = ('PART 5 21\n' + atom('A1', .10, '21') + 'PART 6 -21\n' + atom('A2', .12, '-21') +
            'PART 7 31\n' + atom('B1', .20, '31') + 'PART 8 -31\n' + atom('B2', .22, '-31') + 'PART 0\n')
    p = ps.plan(structure(body))
    self.assertEqual(p.mapping, {5: 1, 6: 2, 7: 3, 8: 4})
    self.assertEqual(p.rows[1].blocked_by.pos, 5)

  def test_symmetry_copy_counts_as_a_clash(self):
    # B1 at -0.2 is 0.3 from A1's inverse at -0.1 ... use the inversion: A1 0.1 -> -0.1, B1 -0.2
    body = ('PART 1 21\n' + atom('A1', .10, '21') +
            'PART 3 31\n' + '%s 1 -0.200 -0.5 -0.5 31 0.05\n' % 'B1' + 'PART 0\n')
    self.assertIsNone(ps.plan(structure(body, latt=1)))
    self.assertEqual(ps.plan(structure(body, latt=-1)).mapping, {3: 1})

  def test_complement_puts_the_positive_part_first(self):
    body = 'PART 1 -21\n' + atom('A1', .1, '-21') + 'PART 2 21\n' + atom('A2', .12, '21') + 'PART 0\n'
    self.assertEqual(ps.plan(structure(body)).mapping, {1: 2, 2: 1})

  def test_already_tidy(self):
    body = 'PART 1 21\n' + atom('A1', .1, '21') + 'PART 2 -21\n' + atom('A2', .12, '-21') + 'PART 0\n'
    self.assertIsNone(ps.plan(structure(body)))
    self.assertFalse(ps.could_change(structure(body)))

  def test_second_pass_finds_nothing(self):
    text = structure(FAR)
    self.assertIsNone(ps.plan(ps.apply(text, ps.plan(text))))

  def test_negative_part_stays_and_does_not_reserve(self):
    body = 'PART -1\n' + atom('S1', .8, '10.5') + FAR
    new = ps.apply(structure(body), ps.plan(structure(body)))
    self.assertEqual(self.numbers(new)[0], '-1')
    self.assertEqual(ps.plan(structure(body)).mapping, {3: 1, 4: 2})

  def test_fixed_occupancy_part_reserves_its_number(self):
    body = 'PART 1\n' + atom('S1', .8, '10.5') + 'PART 3 21\n' + atom('A1', .1, '21') + 'PART 4 -21\n' + \
           atom('A2', .12, '-21') + 'PART 0\n'
    self.assertIsNone(ps.plan(structure(body)))

  def test_sump_variable_is_left_alone(self):
    body = 'SUMP 1 0.01 1 2 1 3\n' + FAR
    self.assertIsNone(ps.plan(structure(body)))

  def test_bind_part_is_left_alone(self):
    p = ps.plan(structure('BIND 3 4\n' + FAR))
    self.assertIsNone(p)

  def test_excluded_pair_stays_and_blocks_its_numbers(self):
    body = FAR.replace('PART 1 ', 'PART 5 ').replace('PART 2 ', 'PART 6 ')
    self.assertEqual(ps.plan(structure(body)).mapping, {3: 1, 4: 2, 5: 1, 6: 2})
    p = ps.plan(structure(body), exclude={3})
    self.assertEqual(p.mapping, {5: 1, 6: 2})

  def test_two_pairs_of_one_variable(self):
    body = FAR.replace('31', '21').replace('.600', '.600')
    body = body.replace('-31', '-21')
    self.assertEqual(ps.plan(structure(body, fvar='0.1 0.4')).mapping, {3: 1, 4: 2})

  def test_hydrogens_do_not_clash(self):
    h = '%s 2 %.3f 0.5 0.5 %s 0.05\n'
    body = ('PART 1 21\n' + h % ('H1', .10, '21') + 'PART 3 31\n' + h % ('H2', .11, '31') + 'PART 0\n')
    self.assertEqual(ps.plan(structure(body)).mapping, {3: 1})

  def test_symm_parsing(self):
    m, t = ps._parse_symm('-X,1/2+Y,-Z+0.25')
    self.assertEqual(m, [[-1, 0, 0], [0, 1, 0], [0, 0, -1]])
    self.assertEqual(t, [0, 0.5, 0.25])

  def test_after_a_complement_merge(self):
    body = ('PART 1 21\n' + atom('A1', .10, '21') + 'PART 2 -21\n' + atom('A2', .12, '-21') +
            'PART 3 31\n' + atom('B1', .60, '31') + 'PART 4 -31\n' + atom('B2', .62, '-31') + 'PART 0\n')
    text = structure(body, fvar='0.1 0.4 0.6')
    merged = fs.apply(text, fs.plan(text))
    self.assertIn('PART 3 -21', merged)
    self.assertEqual(ps.plan(merged).mapping, {3: 2, 4: 1})

  def test_page(self):
    html = ps.page(structure(FAR), form, style.palette())
    for tag in ('table', 'tr', 'td', 'font'):
      self.assertEqual(html.count('<%s ' % tag) + html.count('<%s>' % tag), html.count('</%s>' % tag), tag)
    self.assertIn('name="PART_TICK_3" checked="true"', html)
    self.assertNotIn('PART_TICK_1"', html)
    self.assertIn('becomes <b>1/2</b>', html)


if __name__ == '__main__':
  unittest.main()
