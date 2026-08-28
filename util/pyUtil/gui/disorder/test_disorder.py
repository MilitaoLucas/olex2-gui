"""
gui/disorder/test_disorder.py

Tests for the pure-Python parts of gui/disorder.
Run from the parent directory: python -m pytest disorder/test_disorder.py -v
"""

from ._core import _parse_atom_table


# ---------------------------------------------------------------------------
# _parse_atom_table
# ---------------------------------------------------------------------------

SAMPLE_INFO_OUTPUT = [
    "Some header line",
    "",
    "Atom Type    x         y         z         Ueq",
    "C1   C    0.12345   0.23456   0.34567   0.03210",
    "O1   O    0.45678   0.56789   0.67890   0.04321",
    "N1   N    0.78901   0.89012   0.90123   0.02109",
    "Mean Uiso  0.033",
    "Some footer",
]


def test_parse_atom_table_basic():
  result = _parse_atom_table(SAMPLE_INFO_OUTPUT)
  assert set(result.keys()) == {'C1', 'O1', 'N1'}


def test_parse_atom_table_values():
  result = _parse_atom_table(SAMPLE_INFO_OUTPUT)
  assert result['C1']['Type'] == 'C'
  assert result['C1']['x'] == '0.12345'
  assert result['O1']['Ueq'] == '0.04321'


def test_parse_atom_table_empty():
  assert _parse_atom_table([]) == {}


def test_parse_atom_table_no_table():
  lines = ["No table here", "Just some text", "Nothing useful"]
  assert _parse_atom_table(lines) == {}


def test_parse_atom_table_stops_at_mean_uiso():
  lines = SAMPLE_INFO_OUTPUT + [
        "Extra C2   C    0.11   0.22   0.33   0.044",
    ]
  result = _parse_atom_table(lines)
  assert 'Extra' not in result
  assert len(result) == 3


def test_parse_atom_table_skips_blank_lines():
  lines = [
        "Atom Type    x    y    z    Ueq",
        "",
        "C1   C    0.1   0.2   0.3   0.04",
        "",
        "Mean Uiso  0.04",
    ]
  result = _parse_atom_table(lines)
  assert 'C1' in result


def test_parse_atom_table_mismatched_row_ignored():
  """Rows with wrong column count are silently skipped."""
  lines = [
        "Atom Type    x    y    z    Ueq",
        "C1   C    0.1   0.2   0.3   0.04",
        "C2   C    0.1   0.2",          # too short — skipped
        "Mean Uiso  0.04",
    ]
  result = _parse_atom_table(lines)
  assert 'C1' in result
  assert 'C2' not in result


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
