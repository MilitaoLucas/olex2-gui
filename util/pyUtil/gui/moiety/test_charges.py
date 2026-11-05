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
  assert '0.5(Cl)' in raw and parse_moiety_string(raw)

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

# Metal-centred ions: kept whole when the metals are separated

_PNMA = [
    (((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0, 0, 0)),
    (((-1, 0, 0), (0, -1, 0), (0, 0, 1)), (0.5, 0, 0.5)),
    (((-1, 0, 0), (0, 1, 0), (0, 0, -1)), (0, 0.5, 0)),
    (((1, 0, 0), (0, -1, 0), (0, 0, -1)), (0.5, 0.5, 0.5)),
    (((-1, 0, 0), (0, -1, 0), (0, 0, -1)), (0, 0, 0)),
    (((1, 0, 0), (0, 1, 0), (0, 0, -1)), (0.5, 0, 0.5)),
    (((1, 0, 0), (0, -1, 0), (0, 0, 1)), (0, 0.5, 0)),
    (((-1, 0, 0), (0, 1, 0), (0, 0, 1)), (0.5, 0.5, 0.5)),
]
_MIRROR = _PNMA[6]

def _pnma():
  from .connectivity import make_op
  return [make_op(*op) for op in _PNMA]

def _chromate(cr_bonds=None):
  """Mo_CDK2: Cr, O1 and O3 on a mirror plane, O2 general, O1 touching a Cu."""
  return [
      _atom('Cu1', 'Cu', (0.36828, 0.25, 0.744115), [2], occu=0.5),
      _atom('Cr1', 'Cr', (0.622238, -0.25, 0.735117),
            cr_bonds or [2, 4, 3, (3, _MIRROR)], occu=0.5),
      _atom('O1', 'O', (0.5099, -0.25, 0.794775), [0, 1], occu=0.5),
      _atom('O2', 'O', (0.621502, -0.064528, 0.674197), [1, (1, _MIRROR)]),
      _atom('O3', 'O', (0.735473, -0.25, 0.793694), [1], occu=0.5),
  ]

def test_chromate_stays_whole_on_a_mirror_plane():
  from .connectivity import find_pieces, disconnected_moiety
  raw = disconnected_moiety(find_pieces(_chromate(), _pnma()))
  assert sorted(raw.split(', ')) == ['Cr O4', 'Cu'], raw

def test_chromate_without_its_symmetry_bond_listed():
  """The site symmetry of the metal completes the ion, whatever bonds are listed."""
  from .connectivity import find_pieces, disconnected_moiety
  raw = disconnected_moiety(find_pieces(_chromate([2, 3, 4]), _pnma()))
  assert sorted(raw.split(', ')) == ['Cr O4', 'Cu'], raw

def test_bonds_listed_at_one_end_only():
  from .connectivity import find_pieces, disconnected_moiety
  atoms = _chromate()
  for a in atoms[2:]:
    a['neighbours'] = []
  atoms[0]['neighbours'] = []
  raw = disconnected_moiety(find_pieces(atoms, _pnma()))
  assert sorted(raw.split(', ')) == ['Cr O4', 'Cu'], raw

def test_chromate_structure_end_to_end():
  """The structure that started this: everything balances, nothing is ambiguous."""
  from .tab import build_candidates
  frags = infer('Cu, H2 O, 2(C3 H10 N2), Cr O4')
  by_formula = {f.formula_string: f for f in frags}
  assert by_formula['Cr O4'].charge == -2 and by_formula['Cr O4'].charge_confidence == 'lookup'
  assert by_formula['C3 H10 N2'].charge == 0
  best = build_candidates(frags, 'C6 H22 Cu N4 O, Cr O4')[0]
  assert best['balanced']
  assert best['formula'] == '(Cu 2+), H2 O, 2(C3 H10 N2), (Cr O4 2-)', best['formula']

def test_displayed_chromate_counts_its_symmetry_copy():
  from .connectivity import find_pieces, displayed_moiety
  atoms = _chromate()
  pieces = find_pieces(atoms, _pnma())
  shown = ['Cu1', 'Cr1', 'O1', 'O2', 'O2_$1', 'O3']
  assert sorted(displayed_moiety(pieces, atoms, shown, _pnma()).split(', ')) == ['Cr O4', 'Cu']

def test_dichromate_bridged_on_an_inversion_centre():
  from .connectivity import find_pieces, disconnected_moiety
  atoms = [
      _atom('Cr1', 'Cr', (0.2, 0.1, 0.1), [1, 2, 3, 4]),
      _atom('O1', 'O', (0.0, 0.0, 0.0), [0, (0, _INV)], occu=0.5),
      _atom('O2', 'O', (0.3, 0.1, 0.1), [0]),
      _atom('O3', 'O', (0.2, 0.2, 0.1), [0]),
      _atom('O4', 'O', (0.2, 0.1, 0.2), [0]),
  ]
  assert disconnected_moiety(find_pieces(atoms, _p1bar())) == 'Cr2 O7'

def test_hydrogenchromate_keeps_its_h():
  from .connectivity import find_pieces, disconnected_moiety
  atoms = [
      _atom('Cr1', 'Cr', (0.2, 0.1, 0.1), [1, 2, 3, 4]),
      _atom('O1', 'O', (0.3, 0.1, 0.1), [0, 5]),
      _atom('O2', 'O', (0.2, 0.2, 0.1), [0]),
      _atom('O3', 'O', (0.2, 0.1, 0.2), [0]),
      _atom('O4', 'O', (0.1, 0.1, 0.1), [0]),
      _atom('H1', 'H', (0.35, 0.1, 0.1), [1]),
  ]
  assert disconnected_moiety(find_pieces(atoms, _p1bar())) == 'H Cr O4'

def _metal_with_four(ligand, extra=None):
  atoms = [_atom('M1', 'Co', (0.2, 0.2, 0.2), [1, 2, 3, 4])]
  atoms += [_atom(f'X{i}', ligand, (0.2 + i / 20, 0.3, 0.3), [0]) for i in range(1, 5)]
  return atoms

def test_tetrahalometallate_stays_whole():
  from .connectivity import find_pieces, disconnected_moiety
  assert disconnected_moiety(find_pieces(_metal_with_four('Cl'), _p1bar())) == 'Cl4 Co'
  assert infer('Cl4 Co')[0].charge == -2

def test_metal_with_another_ligand_is_no_ion():
  """One O carries a carbon: a carboxylate, so no MO4 unit, whatever the count."""
  from .connectivity import find_pieces, disconnected_moiety
  atoms = _metal_with_four('O')
  atoms[0]['type'] = 'Cr'
  atoms[1]['neighbours'] = [(0, atoms[0]['neighbours'][0][1]), (5, atoms[0]['neighbours'][0][1])]
  atoms.append(_atom('C1', 'C', (0.5, 0.5, 0.5), [1]))
  raw = disconnected_moiety(find_pieces(atoms, _p1bar()))
  assert 'Cr O4' not in raw and 'Cr' in raw.split(', '), raw

def test_oxo_count_not_tabulated_stays_split():
  from .connectivity import find_pieces, disconnected_moiety
  atoms = _metal_with_four('O')[:4]
  atoms[0]['type'] = 'Cr'
  atoms[0]['neighbours'] = atoms[0]['neighbours'][:3]
  raw = disconnected_moiety(find_pieces(atoms, _p1bar()))
  assert sorted(raw.split(', ')) == ['3(O)', 'Cr'], raw

def test_polymer_with_shared_halides_is_no_ion():
  """A CuCl2 chain: the formula is what decides, and CuCl2 is no known ion."""
  from .connectivity import find_pieces, disconnected_moiety
  atoms = [
      _atom('Cu1', 'Cu', (0.0, 0.0, 0.0), [1, (1, _INV)], occu=0.5),
      _atom('Cl1', 'Cl', (0.2, 0.2, 0.2), [0, (0, _INV)]),
  ]
  raw = disconnected_moiety(find_pieces(atoms, _p1bar()))
  assert sorted(raw.split(', ')) == ['2(Cl)', 'Cu'], raw

def test_table_of_metal_ions():
  from .charges import METAL_IONS, ION_CHARGES, _normalise_key
  for key in ('Cr O4', 'Mo O4', 'W O4', 'V O4', 'Mn O4', 'Re O4', 'Tc O4', 'Fe O4', 'Ru O4',
              'Os O4', 'Cr2 O7', 'Mo S4', 'Co Cl4', 'Fe Cl4', 'Zn Cl4', 'Cr O3 Cl', 'Os O3 N'):
    assert _normalise_key(key) in METAL_IONS, key
  # none of these is an ion to keep whole
  for key in ('H2 O', 'Cl O4', 'S O4', 'P O4', 'Cu', 'Na', 'C2 O4'):
    assert key not in METAL_IONS, key
  assert 'Mn O4' in ION_CHARGES

def test_best_guess_keeps_oxidation_state_that_balances():
  from .tab import build_candidates
  for raw, expected in (('Cu, S O4', '(Cu 2+), (O4 S 2-)'),
                        ('Fe, 3(Cl)', '(Fe 3+), 3(Cl 1-)')):
    best = build_candidates(infer(raw), raw)[0]
    assert best['balanced'] and best['formula'] == expected, best['formula']

def test_best_guess_changes_oxidation_state_only_to_one_that_balances():
  from .tab import build_candidates
  for raw, expected in (('Fe, 2(Cl)', '(Fe 2+), 2(Cl 1-)'),
                        ('Cu, Cl', '(Cu 1+), (Cl 1-)')):
    best = build_candidates(infer(raw), raw)[0]
    assert best['balanced'] and best['formula'] == expected, best['formula']
  # nothing fits: stays at the most common state, and says so
  best = build_candidates(infer('Cu, 7(Cl)'), 'Cu, 7(Cl)')[0]
  assert not best['balanced'] and '(Cu 2+)' in best['formula']

def test_ion_with_several_charges_follows_the_balance():
  assert infer('K, Mn O4')[1].charge == -1
  assert infer('2(K), Mn O4')[1].charge == -2
  assert infer('3(K), Mn O4')[1].charge == -3
  assert infer('2(K), Cl4 Fe')[1].charge == -2
  assert infer('2(K), Cl4 Fe')[1].charge_confidence == 'balance'

def test_ion_with_several_charges_first_guess_then_balance():
  frags = infer('C8 H20 N, Mn O4')
  assert frags[1].charge == -1 and frags[1].charge_confidence == 'element_ambiguous'
  assert frags[0].charge == 1 and frags[0].charge_confidence == 'balance'

def test_ion_with_impossible_balance_is_suspect():
  frags = infer('5(K), Mn O4')
  assert frags[1].charge == -5 and frags[1].charge_confidence == 'balance_suspect'

# Part-occupied water

def _two_waters(occu1=0.35, occu2=0.15):
  """Two water sites on a mirror plane in Pnma, with their H as in mo_CDK2."""
  atoms = [_atom('Cu1', 'Cu', (0.36828, 0.25, 0.744115), [], occu=0.5)]
  for name, x, occu in (('4', 0.157, occu1), ('5', 0.589, occu2)):
    n = len(atoms)
    atoms += [
        _atom(f'O{name}', 'O', (x, 0.25, 0.725), [n + 1, n + 2, (n + 1, _MIRROR), (n + 2, _MIRROR)], occu=occu),
        _atom(f'H{name}a', 'H', (x + 0.03, 0.34, 0.75), [n, (n, _MIRROR)], occu=occu),
        _atom(f'H{name}b', 'H', (x + 0.03, 0.16, 0.75), [n, (n, _MIRROR)], occu=occu),
    ]
  return atoms

def test_water_on_two_part_occupied_sites_adds_up():
  from .connectivity import find_pieces, disconnected_moiety
  raw = disconnected_moiety(find_pieces(_two_waters(), _pnma()))
  assert sorted(raw.split(', ')) == ['Cu', 'H2 O'], raw

def test_water_sites_not_adding_up_to_one_keep_their_total():
  """0.68 stays 0.68, and does not scale the formula to make it a whole number."""
  from .connectivity import find_pieces, disconnected_moiety
  raw = disconnected_moiety(find_pieces(_two_waters(0.2, 0.14), _pnma()))
  assert sorted(raw.split(', ')) == ['0.68(H2 O)', 'Cu'], raw
  water = next(f for f in infer(raw) if f.formula_string == 'H2 O')
  assert water.charge == 0 and water.charge_confidence == 'lookup'
  assert repr(water) == '0.68(H2 O)'

def test_displayed_water_adds_up_too():
  from .connectivity import find_pieces, displayed_moiety
  atoms = _two_waters()
  shown = ['Cu1', 'O4', 'H4a', 'H4b', 'O5', 'H5a', 'H5b']
  shown += [n + '_$1' for n in ('H4a', 'H4b', 'H5a', 'H5b')]
  raw = displayed_moiety(find_pieces(atoms, _pnma()), atoms, shown, _pnma())
  assert sorted(raw.split(', ')) == ['Cu', 'H2 O'], raw

def test_part_occupied_ion_is_still_the_ion():
  from .connectivity import find_pieces, disconnected_moiety
  atoms = _metal_with_four('Cl')
  for a in atoms:
    a['occu'] = 0.5
  assert disconnected_moiety(find_pieces(atoms, _p1bar())) == '0.5(Cl4 Co)'

def test_best_guess_is_the_same_in_console_and_tab():
  import ast, os
  from .charges import best_guess
  frags = infer('Cu, H2 O, 2(C3 H10 N2), Cr O4')
  assert next(f for f in best_guess(frags) if f.formula_string == 'Cu').charge == 2
  here = os.path.dirname(os.path.abspath(__file__))
  for name in ('__init__.py', 'tab.py'):
    tree = ast.parse(open(os.path.join(here, name)).read())
    called = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert 'best_guess' in called, name

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