"""
moiety/test_parser.py

Run with:  python -m pytest util/pyUtil/gui/moiety/test_parser.py -v
or simply: python test_parser.py
"""

from .parser import parse_moiety_string, format_moiety_string, MoietyFragment


def check(raw, expected_reprs, expected_had_fractions=None, label=''):
    frags = parse_moiety_string(raw)
    reprs = [repr(f) for f in frags]
    assert reprs == expected_reprs, (
        f"\n  CASE: {label or repr(raw)}"
        f"\n  GOT:  {reprs}"
        f"\n  WANT: {expected_reprs}"
    )
    if expected_had_fractions is not None:
        actual = [f._had_fractions for f in frags]
        assert actual == expected_had_fractions, (
            f"\n  CASE: {label or repr(raw)}"
            f"\n  had_fractions GOT:  {actual}"
            f"\n  had_fractions WANT: {expected_had_fractions}"
        )
    return frags


# ---------------------------------------------------------------------------
# None / empty — no structure loaded
# ---------------------------------------------------------------------------

def test_none():
    assert parse_moiety_string(None) == []

def test_empty():
    assert parse_moiety_string('') == []

def test_whitespace():
    assert parse_moiety_string('   ') == []


# ---------------------------------------------------------------------------
# Simple cases — no multiplicity, no charge
# ---------------------------------------------------------------------------

def test_simple_organic():
    check("C7 H4 Cl Hg N O3 S",
          ["C7 H4 Cl Hg N O3 S"],
          label="simple organic with several elements")

def test_single_metal():
    check("Ca",
          ["Ca"],
          label="bare metal atom")

def test_single_water():
    check("H2 O",
          ["H2 O"],
          label="water, no multiplicity")


# ---------------------------------------------------------------------------
# Multiplicity
# ---------------------------------------------------------------------------

def test_multiplicity_water():
    check("2(H2 O)",
          ["2(H2 O)"],
          label="2 waters with explicit multiplicity")

def test_multiplicity_five():
    check("5(H2 O1)",
          ["5(H2 O)"],    # O1 → O (count 1 suppressed in repr)
          label="5 waters, O count explicit")

def test_comma_separated():
    check("C4 H8 Ca O8, 2(H2 O)",
          ["C4 H8 Ca O8", "2(H2 O)"],
          label="calcium solvate")


# ---------------------------------------------------------------------------
# Metal-separated output (conn $M 0)
# ---------------------------------------------------------------------------

def test_metal_separated():
    check("Ca, C4 H4 O6, 4(H2 O)",
          ["Ca", "C4 H4 O6", "4(H2 O)"],
          label="Ca tartrate with conn $M 0")


# ---------------------------------------------------------------------------
# Charges — parsed from string (IUCr format)
# ---------------------------------------------------------------------------

def test_charge_cation():
    frags = check("C12 H17 N4 O S 1+, C6 H2 N3 O7 1-",
                  ["(C12 H17 N4 O S 1+)", "(C6 H2 N3 O7 1-)"],
                  label="salt with charges")
    assert frags[0].charge == +1
    assert frags[1].charge == -1

def test_charge_multivalent():
    frags = check("(Cd 2+)3, (C6 N6 Cr 3-)2, 2(H2 O)",
                  ["3(Cd 2+)", "2(C6 Cr N6 3-)", "2(H2 O)"],
                  label="IUCr example with mult outside parens")
    assert frags[0].charge == +2
    assert frags[1].charge == -3
    assert frags[2].charge is None


# ---------------------------------------------------------------------------
# Fractional counts — the presentation artefact from GetMoietyFormula
# ---------------------------------------------------------------------------

def test_fractional_water():
    """4(H O0.5) is the same as 2(H2 O) — just badly factorised."""
    frags = check("4(H O0.5)",
                  ["2(H2 O)"],
                  expected_had_fractions=[True],
                  label="fractional water presentation")
    assert frags[0]._had_fractions is True

def test_fractional_oxygen():
    """2(O22.5) → O45 — mult=1 after refactorisation, no parens needed.
    Chemically this is nonsense (45 oxide atoms) but arithmetically
    it is what GetMoietyFormula produced and we preserve it faithfully."""
    frags = check("2(O22.5)",
                  ["O45"],
                  expected_had_fractions=[True],
                  label="fractional oxygen")

def test_fractional_outer_multiplicity():
    """0.679(H2 O) — partial occupancy solvent, common in real structures."""
    frags = parse_moiety_string("0.679(H2 O)")
    assert len(frags) == 1
    f = frags[0]
    assert f.elements == {'H': 2, 'O': 1}
    assert f.multiplicity == 1
    assert f._had_fractions is True
    assert abs(f._occupancy - 0.679) < 0.001
    assert '0.679' in repr(f)   # exact value preserved

def test_partial_occupancy_dcm():
    """0.5(C H2 Cl2) — half-occupancy DCM."""
    frags = parse_moiety_string("0.5(C H2 Cl2)")
    assert len(frags) == 1
    f = frags[0]
    assert f.elements == {'C': 1, 'H': 2, 'Cl': 2}
    assert abs(f._occupancy - 0.5) < 0.001


# ---------------------------------------------------------------------------
# Charge balance check (not inference — just the balance sum)
# ---------------------------------------------------------------------------

def test_balance_neutral():
    frags = parse_moiety_string("C12 H17 N4 O S 1+, C6 H2 N3 O7 1-")
    total = sum(f.multiplicity * (f.charge or 0) for f in frags)
    assert total == 0

def test_balance_salt():
    frags = parse_moiety_string("(Cd 2+)3, (C6 N6 Cr 3-)2, 2(H2 O)")
    total = sum(f.multiplicity * (f.charge or 0) for f in frags)
    assert total == 0   # 3*2 + 2*(-3) + 2*0 = 6 - 6 = 0


# ---------------------------------------------------------------------------
# Round-trip: parse → format → parse
# ---------------------------------------------------------------------------

def test_roundtrip_simple():
    s = "C4 H8 Ca O8, 2(H2 O)"
    frags = parse_moiety_string(s)
    s2 = format_moiety_string(frags)
    frags2 = parse_moiety_string(s2)
    assert [repr(f) for f in frags] == [repr(f) for f in frags2]

def test_roundtrip_charged():
    s = "C12 H17 N4 O S 1+, C6 H2 N3 O7 1-"
    frags = parse_moiety_string(s)
    s2 = format_moiety_string(frags)
    frags2 = parse_moiety_string(s2)
    assert [f.charge for f in frags] == [f.charge for f in frags2]


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_bad_token():
    import pytest
    with pytest.raises(ValueError, match="Unrecognised element token"):
        parse_moiety_string("C4 H8 ??? O3")


# ---------------------------------------------------------------------------
# Runner (no pytest needed)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
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