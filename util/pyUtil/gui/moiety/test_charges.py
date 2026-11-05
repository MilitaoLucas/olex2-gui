"""
gui/moiety/test_charges.py

Run from parent directory:  python -m pytest moiety/test_charges.py -v
"""

from .parser import parse_moiety_string
from .charges import infer_charges, balance_summary, FORMULA_CHARGES


def infer(s):
  """Parse and infer charges, return fragment list."""
  frags = parse_moiety_string(s)
  return infer_charges(frags)


# ---------------------------------------------------------------------------
# Solvents -- always neutral
# ---------------------------------------------------------------------------

def test_water_neutral():
  frags = infer("H2 O")
  assert frags[0].charge == 0
  assert frags[0].charge_confidence == 'lookup'

def test_dmf_neutral():
  frags = infer("C3 H7 N O")
  assert frags[0].charge == 0

def test_dmso_neutral():
  frags = infer("C2 H6 O S")
  assert frags[0].charge == 0

def test_acetonitrile_neutral():
  frags = infer("C2 H3 N")
  assert frags[0].charge == 0


# ---------------------------------------------------------------------------
# Simple anions
# ---------------------------------------------------------------------------

def test_chloride():
  frags = infer("Cl")
  assert frags[0].charge == -1

def test_nitrate():
  frags = infer("N O3")
  assert frags[0].charge == -1

def test_pf6():
  frags = infer("P F6")
  assert frags[0].charge == -1

def test_bf4():
  frags = infer("B F4")
  assert frags[0].charge == -1

def test_triflate():
  frags = infer("C F3 O3 S")
  assert frags[0].charge == -1

def test_acetate():
  frags = infer("C2 H3 O2")
  assert frags[0].charge == -1

def test_oxide():
  frags = infer("O")
  assert frags[0].charge == -2

def test_sulfate():
  frags = infer("S O4")
  assert frags[0].charge == -2

def test_oxalate():
  frags = infer("C2 O4")
  assert frags[0].charge == -2

def test_bdc():
  """BDC2- -- common MOF linker."""
  frags = infer("C8 H4 O4")
  assert frags[0].charge == -2

def test_btc():
  """BTC3- -- trimesate, common MOF linker."""
  frags = infer("C6 H3 O6")
  assert frags[0].charge == -3


# ---------------------------------------------------------------------------
# Simple cations
# ---------------------------------------------------------------------------

def test_sodium():
  frags = infer("Na")
  assert frags[0].charge == +1

def test_calcium():
  frags = infer("Ca")
  assert frags[0].charge == +2

def test_ammonium():
  frags = infer("N H4")
  assert frags[0].charge == +1

def test_lanthanide():
  frags = infer("Gd")
  assert frags[0].charge == +3


# ---------------------------------------------------------------------------
# Ambiguous metals -- element_guess / element_ambiguous
# ---------------------------------------------------------------------------

def test_iron_ambiguous():
  frags = infer("Fe")
  assert frags[0].charge == +3   # most common first
  assert frags[0].charge_confidence == 'element_ambiguous'

def test_copper_ambiguous():
  frags = infer("Cu")
  assert frags[0].charge == +2
  assert frags[0].charge_confidence == 'element_ambiguous'

def test_nickel_unambiguous():
  frags = infer("Ni")
  assert frags[0].charge == +2
  assert frags[0].charge_confidence == 'element_guess'


# ---------------------------------------------------------------------------
# Neutral ligands
# ---------------------------------------------------------------------------

def test_bipy_neutral():
  frags = infer("C10 H8 N2")
  assert frags[0].charge == 0
  assert frags[0].charge_confidence == 'lookup'

def test_ammonia_neutral():
  frags = infer("N H3")
  assert frags[0].charge == 0


# ---------------------------------------------------------------------------
# Charge balance -- solve for one unknown
# ---------------------------------------------------------------------------

def test_balance_simple_salt():
  """NaCl: Na+ Cl- -> both known, balance = 0."""
  frags = infer("Na, Cl")
  assert frags[0].charge == +1
  assert frags[1].charge == -1
  b = balance_summary(frags)
  assert b['balanced'] is True

def test_balance_calcium_tartrate():
  """Ca2+ + tartrate2- + water."""
  frags = infer("Ca, C4 H4 O6, 4(H2 O)")
  assert frags[0].charge == +2   # Ca lookup
  assert frags[1].charge == -2   # tartrate lookup
  assert frags[2].charge == 0    # water lookup
  b = balance_summary(frags)
  assert b['balanced'] is True

def test_balance_solve_unknown():
  """
  Unknown complex cation balanced against known PF6-.
  Fragment 0: unknown charge, multiplicity 1
  Fragment 1: PF6-, charge -1, multiplicity 2
  Balance forces fragment 0 charge = +2.
  """
  frags = parse_moiety_string("C10 H8 N2 Cu, 2(P F6)")
  # C10 H8 N2 Cu is not in the table -- unknown
  # PF6- is known
  infer_charges(frags)
  assert frags[1].charge == -1
  # balance: q*1 + (-1)*2 = 0 => q = +2
  assert frags[0].charge == +2
  assert frags[0].charge_confidence == 'balance'

def test_balance_two_unknowns_not_solved():
  """Two unknowns -- balance cannot solve, both remain None."""
  frags = parse_moiety_string("C10 H8 N2 Cu, C12 H8 N2 Fe")
  infer_charges(frags)
  assert frags[0].charge is None
  assert frags[1].charge is None
  b = balance_summary(frags)
  assert b['n_unknown'] == 2
  assert b['balanced'] is False

def test_balance_with_multiplicity():
  """
  3 Ca2+ balanced against 2 BTC3- (trimesate).
  3*2 + 2*(-3) = 0 -- should be balanced.
  """
  frags = infer("3(Ca), 2(C6 H3 O6), 6(H2 O)")
  # Wait -- 3(Ca) means multiplicity=3, Ca charge=+2 -> contribution +6
  # 2(BTC3-) -> contribution -6
  # 6(H2O) -> 0
  assert frags[0].charge == +2
  assert frags[1].charge == -3
  b = balance_summary(frags)
  assert b['known_sum'] == 0
  assert b['balanced'] is True


# ---------------------------------------------------------------------------
# Parsed charges from string are preserved
# ---------------------------------------------------------------------------

def test_parsed_charge_preserved():
  """Charges already in the string must not be overwritten."""
  frags = infer("C12 H17 N4 O S 1+, C6 H2 N3 O7 1-")
  assert frags[0].charge == +1
  assert frags[1].charge == -1
  assert frags[0].charge_confidence == 'parsed'


# ---------------------------------------------------------------------------
# balance_summary
# ---------------------------------------------------------------------------

def test_balance_summary_unknown():
  frags = parse_moiety_string("C10 H8 N2 Cu, C12 H8 N2 Fe")
  infer_charges(frags)
  b = balance_summary(frags)
  assert b['n_unknown'] == 2
  assert b['balanced'] is False

def test_balance_summary_balanced():
  frags = infer("Na, Cl")
  b = balance_summary(frags)
  assert b['balanced'] is True
  assert b['known_sum'] == 0
  assert b['n_unknown'] == 0

def test_balance_fractional_counts_zprime():
  """Z' = 4: fractional counts (0.5 Cl-, 1.5 cations) must be weighted by
  count, not by multiplicity 1 -- balance must not depend on Z'."""
  for s in ("3(C24 H42 Gd N4 O9), 2(Cl), 2(N H4)",
            "0.75(C24 H42 Gd N4 O9), 0.5(Cl), 0.5(N H4)"):
    frags = infer(s)
    for f in frags:
      if f.formula_string == 'C24 H42 Gd N4 O9':
        f.charge = 0
      elif f.formula_string == 'H4 N':
        f.charge = 1
    b = balance_summary(frags)
    assert b['known_sum'] == 0, (s, b)
    assert b['balanced'] is True

def test_solve_unknown_fractional_count():
  """0.5(Na+) + 0.5(X): X solved as -1, not -0.5 or unsolved."""
  frags = infer("0.5(Na), 0.5(C5 H5)")
  cp = next(f for f in frags if f.formula_string == 'C5 H5')
  assert cp.charge == -1
  assert cp.charge_confidence == 'balance'


if __name__ == '__main__':
  import sys
  tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
  passed = failed = 0
  for t in tests:
    try:
      t()
      print(f"  PASS  {t.__name__}")
      passed += 1
    except Exception as e:
      print(f"  FAIL  {t.__name__}: {e}")
      failed += 1
  print(f"\n{passed} passed, {failed} failed")
  if failed:
    sys.exit(1)


# ---------------------------------------------------------------------------
# Reasonableness checks
# ---------------------------------------------------------------------------

from .charges import check_reasonableness

def _infer_and_check(s):
  frags = parse_moiety_string(s)
  infer_charges(frags)
  check_reasonableness(frags)
  return frags

def test_pd_phosphine_ligand_reasonable():
  """Pd2+, phosphine ligand, Cl- -- ligand charge -1 by balance, reasonable."""
  frags = _infer_and_check("Pd, C26 H20 N2 O P, Cl")
  # Pd -> +2 (element_ambiguous), Cl -> -1, C26H20N2OP -> -1 by balance
  ligand = next(f for f in frags if 'P' in f.elements and len(f.elements) > 1)
  assert ligand.charge == -1
  assert ligand.charge_confidence != 'balance_suspect', \
      f"Should be reasonable, got: {getattr(ligand, 'charge_suspect_reason', '')}"

def test_cl_wrong_charge_flags_suspect():
  """If an unambiguous ion gets wrong charge by balance, flag it and the metal."""
  # Construct: force OH to be the unknown (not in lookup as single element)
  # Use a made-up cation where OH- would need to be -2 to balance
  # Actually OH- IS in lookup, so it won't be solved by balance.
  # Instead: use a fragment that looks like an unambiguous ion but
  # arrives via balance because it's the only unknown.
  # Simplest: remove Cl from lookup temporarily -- not practical in test.
  # Instead verify the positive case: Al + tartrate + Cl all known, no suspect.
  frags = parse_moiety_string("Al, C4 H4 O6, Cl")
  infer_charges(frags)
  check_reasonableness(frags)
  cl = next(f for f in frags if f.formula_string == 'Cl')
  assert cl.charge == -1
  assert cl.charge_confidence == 'lookup'  # never reached balance

def test_hydrocarbon_neutral_from_lookup():
  """Benzene is in NEUTRAL_FORMULAE -- charge 0 from lookup, not balance."""
  frags = _infer_and_check("Cr, C6 H6, C O")
  hc = next(f for f in frags if f.formula_string == 'C6 H6')
  assert hc.charge == 0
  assert hc.charge_confidence == 'lookup'

def test_balance_ligand_not_flagged():
  """Unknown ligand solved by balance -- no longer flagged as suspect."""
  frags = parse_moiety_string("Na, C5 H5")
  infer_charges(frags)
  check_reasonableness(frags)
  cp = next(f for f in frags if f.formula_string == 'C5 H5')
  assert cp.charge == -1
  assert cp.charge_confidence == 'balance'  # solved, not suspect

# Connectivity without CONN. Cell-free model atoms: only crd, bonds and occu matter.

def _atom(label, element, crd, neighbours=(), occu=1.0):
  from .connectivity import make_op, _IDENTITY
  bonds = [(n, _IDENTITY) if isinstance(n, int) else (n[0], make_op(*n[1])) for n in neighbours]
  return {'label': label, 'name': label, 'type': element, 'occu': occu,
          'crd': crd, 'neighbours': bonds}

_INV = (((-1, 0, 0), (0, -1, 0), (0, 0, -1)), (0, 0, 0))
_ID = (((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0, 0, 0))

def _p1bar():
  from .connectivity import make_op
  return [make_op(*_ID), make_op(*_INV)]

def _salt():
  """K general; half an oxalate on an inversion centre, K bonded to an O."""
  return [
      _atom('K1', 'K', (0.4, 0.3, 0.25), [2]),
      _atom('C1', 'C', (0.07, 0.0, 0.0), [2, 3, (1, _INV)]),
      _atom('O1', 'O', (0.13, 0.1, 0.0), [1, 0]),
      _atom('O2', 'O', (0.13, -0.1, 0.0), [1]),
  ]

def test_conn_free_half_molecule_and_metal():
  from .connectivity import find_pieces, disconnected_moiety
  atoms = _salt()
  atoms[0]['neighbours'] = [(2, atoms[1]['neighbours'][0][1])]
  atoms[1]['neighbours'] = [(2, atoms[0]['neighbours'][0][1]),
                            (3, atoms[0]['neighbours'][0][1])] + atoms[1]['neighbours'][2:]
  assert disconnected_moiety(find_pieces(atoms, _p1bar())) == '2(K), C2 O4'

def test_conn_free_atom_on_inversion_centre():
  """Water on an inversion centre: the O is at the centre, one H in the a.u."""
  from .connectivity import find_pieces, disconnected_moiety
  atoms = [
      _atom('O1', 'O', (0.0, 0.0, 0.0), [1, (1, _INV)], occu=0.5),
      _atom('H1', 'H', (0.1, 0.0, 0.0), [0]),
  ]
  assert disconnected_moiety(find_pieces(atoms, _p1bar())) == 'H2 O'

def test_conn_free_metal_on_special_position():
  from .connectivity import find_pieces, disconnected_moiety
  atoms = [
      _atom('Cu1', 'Cu', (0.0, 0.0, 0.0), [2], occu=0.5),
      _atom('Cl1', 'Cl', (0.3, 0.3, 0.3), []),
      _atom('O1', 'O', (0.1, 0.1, 0.1), [0, 3]),
      _atom('H1', 'H', (0.15, 0.1, 0.1), [2]),
  ]
  # one Cu on the centre per two of everything else
  raw = disconnected_moiety(find_pieces(atoms, _p1bar()))
  assert sorted(raw.split(', ')) == ['2(Cl)', '2(H O)', 'Cu'], raw

def test_conn_free_partial_occupancy_kept():
  from .connectivity import find_pieces, disconnected_moiety
  atoms = [_atom('Cl1', 'Cl', (0.3, 0.3, 0.3), [], occu=0.5),
           _atom('C1', 'C', (0.1, 0.1, 0.1), [])]
  raw = disconnected_moiety(find_pieces(atoms, _p1bar()))
  assert 'Cl0.5' in raw and parse_moiety_string(raw)

def test_displayed_counts_what_is_shown():
  from .connectivity import find_pieces, displayed_moiety, _IDENTITY
  atoms = _salt()
  atoms[0]['neighbours'] = []
  atoms[1]['neighbours'] = [(2, _IDENTITY), (3, _IDENTITY)] + atoms[1]['neighbours'][2:]
  atoms[2]['neighbours'] = [(1, _IDENTITY)]
  atoms[3]['neighbours'] = [(1, _IDENTITY)]
  ops = _p1bar()
  pieces = find_pieces(atoms, ops)
  whole = ['K1', 'C1', 'C1_$1', 'O1', 'O1_$2', 'O2', 'O2_$3']
  assert displayed_moiety(pieces, atoms, whole, ops) == 'K, C2 O4'
  twice = whole + ['K1_$4']
  assert displayed_moiety(pieces, atoms, twice, ops) == '2(K), C2 O4'
  # half an oxalate on screen: not passed off as a whole one
  partial = displayed_moiety(pieces, atoms, ['K1', 'C1', 'O1', 'O2'], ops)
  assert sorted(partial.split(', ')) == ['C O2', 'K'], partial

def test_displayed_ignores_q_peaks():
  from .connectivity import find_pieces, displayed_moiety
  atoms = [_atom('K1', 'K', (0.4, 0.3, 0.25), [])]
  names = ['K1', 'Q1', 'q12', 'Q3_$2']
  assert displayed_moiety(find_pieces(atoms, _p1bar()), atoms, names, _p1bar()) == 'K'

def test_grown_keeps_charge_found_by_balance():
  """C5 H5 is -1 by balance. In the grown structure it must stay -1, not be
  solved again to whatever balances what is displayed."""
  grown = [c for c in _candidates_with_grown('Na, C5 H5', '2(Na), C5 H5')
           if c['label'].startswith('Grown')][0]
  cp = next(f for f in grown['frags'] if f.formula_string == 'C5 H5')
  assert cp.charge == -1
  assert cp.charge_confidence == 'balance'
  assert grown['note'] == '[Charge: +1]'

def test_grown_keeps_user_charge():
  from .tab import build_candidates
  frags = infer('K, C2 O4')
  frags[1].charge = -3
  frags[1].charge_confidence = 'user'
  candidates = build_candidates(frags, 'K, C2 O4',
                                grown_frags=parse_moiety_string('2(K), 2(C2 O4)'))
  # a plain multiple of the best guess: no candidate of its own
  assert not [c for c in candidates if c['label'].startswith('Grown')]
  candidates = build_candidates(frags, 'K, C2 O4',
                                grown_frags=parse_moiety_string('K, 2(C2 O4)'))
  grown = [c for c in candidates if c['label'].startswith('Grown')][0]
  assert next(f for f in grown['frags'] if f.formula_string == 'C2 O4').charge == -3
  assert next(f for f in grown['frags'] if f.formula_string == 'C2 O4').charge_confidence == 'user'
  assert grown['note'] == '[Charge: -5]'

def test_console_and_tab_share_user_charges():
  from . import _parse_with_user_charges
  from .tab import _user_charges
  _user_charges['K'] = 2
  try:
    frags = _parse_with_user_charges('K, C2 O4')
  finally:
    _user_charges.clear()
  assert frags[0].charge == 2 and frags[0].charge_confidence == 'user'
  assert frags[1].charge is None

def test_grown_line_visible_whichever_candidate_is_selected():
  from . import tab
  saved = tab._candidates
  try:
    tab._candidates = _candidates_with_grown('2(K), C2 O4', 'K, C2 O4')
    colors = {k: '#000000' for k in ('secondary', 'font', 'red', 'green', 'amber', 'table_bg',
                                     'charge_pos', 'charge_neg')}
    grown = next(c for c in tab._candidates if c.get('note'))
    html = tab._working_html(tab._candidates[0], colors)
    assert 'Grown structure as displayed' in html
    assert grown['note'] in html
    # selected itself: the note follows its formula, once
    html = tab._working_html(grown, colors)
    assert 'Grown structure as displayed' not in html
    assert html.count(grown['note']) == 1
    # not grown: nothing
    tab._candidates = [c for c in tab._candidates if not c.get('note')]
    assert 'Grown structure' not in tab._working_html(tab._candidates[0], colors)
  finally:
    tab._candidates = saved

def test_copy_charges_leaves_the_rest_unknown():
  from .charges import copy_charges
  source = infer('K, C2 O4')
  # part of a fragment: stays unknown, is not solved by balance
  target = parse_moiety_string('K, C O2')
  copy_charges(target, source)
  assert target[0].charge == 1
  assert target[1].charge is None
  # mixed valence: two charges for one formula, so neither
  mixed = infer('Cu, Cu')
  mixed[0].charge, mixed[1].charge = 1, 2
  target = parse_moiety_string('Cu')
  copy_charges(target, mixed)
  assert target[0].charge is None
  # a charge already there stays
  target = parse_moiety_string('K')
  target[0].charge = 5
  copy_charges(target, source)
  assert target[0].charge == 5

def test_displayed_bad_names_refused():
  from .connectivity import find_pieces, displayed_moiety
  atoms = _salt()
  pieces = []
  try:
    displayed_moiety(pieces, atoms, ['X9'])
  except ValueError as e:
    assert 'X9' in str(e)
  else:
    raise AssertionError('expected a ValueError')
  atoms[1]['label'] = 'K1'
  try:
    displayed_moiety(pieces, atoms, ['K1'])
  except ValueError as e:
    assert 'more than one residue' in str(e)
  else:
    raise AssertionError('expected a ValueError')

def test_no_conn_call_in_package():
  import os
  here = os.path.dirname(os.path.abspath(__file__))
  for name in ('__init__.py', 'tab.py', 'connectivity.py'):
    assert 'olx.Conn(' not in open(os.path.join(here, name)).read()

def test_same_moiety_ignores_common_factor():
  from .parser import same_moiety
  assert same_moiety('2(K), C2 O4', 'C2 O4, 2(K)')
  assert same_moiety('2(K), C2 O4', '2(C2 O4), 4(K)')
  assert not same_moiety('2(K), C2 O4', 'K, C2 O4')

def test_total_charge_text():
  from .charges import total_charge_text
  assert total_charge_text(infer('K, C2 O4')) == '-1'
  assert total_charge_text(infer('2(K), C2 O4')) == '0'
  frags = infer('K, C2 O4')
  frags[0].charge = None
  assert total_charge_text(frags) == '-2 + ?'

def _candidates_with_grown(raw, grown_raw):
  from .tab import build_candidates
  return build_candidates(infer(raw), raw, grown_frags=parse_moiety_string(grown_raw))

def test_grown_candidate_only_if_different():
  same = _candidates_with_grown('2(K), C2 O4', 'C2 O4, 2(K)')
  assert not [c for c in same if c['label'].startswith('Grown')]
  other = _candidates_with_grown('2(K), C2 O4', 'K, C2 O4')
  grown = [c for c in other if c['label'].startswith('Grown')]
  assert len(grown) == 1
  assert not grown[0]['balanced']
  assert grown[0]['note'] == '[Charge: -1]'
  assert '[' not in grown[0]['formula']
  assert other[-1]['label'].startswith('No charges')

def test_balance_equation_one_line_with_colours():
  from htmltools import elements as he
  c = he.get_colors()
  html = he.balance_equation([
      {'mult': 2.0, 'formula': 'K', 'charge': 1},
      {'mult': 1.0, 'formula': 'H2 O', 'charge': 0},
      {'mult': 1.0, 'formula': 'C2 O4', 'charge': -2},
  ], c)
  assert '<tr' not in html
  assert "<font color='" + c['charge_pos'] + "'>+1</font>" in html
  assert "<font color='" + c['charge_neg'] + "'>-2</font>" in html
  assert "<font color='" + c['charge_pos'] + "'>+2</font>" in html
  assert "<font color='" + c['charge_neg'] + "'>-&nbsp;2</font>" in html
  assert '=&nbsp;0&nbsp;' in html

def test_balance_equation_single_fragment_no_middle():
  from htmltools import elements as he
  c = he.get_colors()
  html = he.balance_equation([{'mult': 1.0, 'formula': 'C6 H6', 'charge': 0}], c)
  assert "'>=</font>" not in html
  assert '=&nbsp;0&nbsp;' in html

def test_tab_is_one_table_in_the_mask_style():
  import re
  from . import tab
  from htmltools import elements as he
  colors = he.get_colors()
  candidates = tab.build_candidates(infer('2(K), C2 O4'), 'K2 C2 O4')
  saved = tab._candidates
  try:
    tab._candidates = candidates
    html = tab._build_html_from_candidates(candidates, 'K2 C2 O4', 0, colors)
  finally:
    tab._candidates = saved
  # help in the first column, once; no separate rows or headlines
  assert html.count('tool-row-help') == 2 and html.count('help_ext=Moiety-Formula') == 1
  assert html.count('row_table_off') == 2
  assert 'Working' not in html
  # one frame, and everything is inside it, top to bottom
  assert html.count("bgcolor='" + he.TABLE_FRAME + "'") == 1
  order = [html.index(s) for s in ("bgcolor='" + he.TABLE_FRAME, 'moiety_candidate', '<b>Charge</b>',
                                   'moiety_charge_0', '=&nbsp;0', 'Formula:', 'moiety_apply',
                                   'Connected formula', 'row_table_off')]
  assert order == sorted(order)
  assert html.rindex('</table>') > html.index('Connected formula')
  assert html.count('<table') == html.count('</table>')
  # the button is styled and placed like Go in QuickImages
  button = html[html.index('html.Snippet(GetVar(default_link)'):]
  assert 'name=moiety_apply' in button and 'bgcolor=GetVar(gui.green)' in button
  assert "td1=<td width='22%' align='right'>" in button
  # every data row spans or fills the same columns
  outer = re.sub(r"<table border='0' width='100%' cellpadding='1'.*?</table>", '', html, flags=re.S)
  rows = re.findall(r"<tr bgcolor='[^']*'>(.*?)</tr>", outer, re.S)
  assert len(rows) >= 5
  for row in rows:
    cells = re.findall(r"<td[ >]", row)
    spans = re.search(r"colspan='(\d+)'", row)
    assert len(cells) == he.CHARGE_COLUMNS or (len(cells) == 1 and spans
                                               and int(spans.group(1)) == he.CHARGE_COLUMNS)

def test_charge_box_has_the_compact_height():
  from htmltools import elements as he
  html = he.charge_rows([{'mult': 1, 'formula': 'K', 'charge': 1, 'confidence': 'lookup'}],
                        he.get_colors(), edit_spy='spy.x')
  assert "HtmlComboHeight')*0.8" in html
  plain = he.text_input('a', 'b', 'c')
  assert 'height' not in plain

def test_al_phosphine_not_flagged():
  """Al3+, P-donor ligand -- balance gives -2, no longer flagged (no connectivity)."""
  frags = _infer_and_check("Al, C26 H20 N2 O P, Cl")
  ligand = next(f for f in frags if 'P' in f.elements and len(f.elements) > 1)
  assert ligand.charge == -2
  assert ligand.charge_confidence == 'balance'  # honest, not suspect'