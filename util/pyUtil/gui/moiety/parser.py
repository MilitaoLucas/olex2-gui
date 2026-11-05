"""
moiety/parser.py

Parse the string returned by xf.latt.GetMoietyFormula into a list of
MoietyFragment objects, with re-factorisation of any non-integer element
counts (a presentation artefact from GetMoietyFormula, not a data error).

Format produced by GetMoietyFormula (always, per Horst):
  - Moieties separated by ', '
  - Optional integer or fractional outer multiplicity: '2(H2 O)', '4(H O0.5)'
  - Elements separated by spaces, each as Symbol + optional count: 'C4 H8 O3'
  - Charge suffix separated by a space: 'C12 H17 N4 O S 1+', '(Cd 2+)3'
  - GetMoietyFormula returns None when no structure is loaded

Pipeline position:
  raw string -> [THIS MODULE] -> list[MoietyFragment] -> charge inference -> GUI
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd
from functools import reduce
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class MoietyFragment:
  """One distinct moiety type in the formula, e.g. '2(H2 O)'."""

  multiplicity: int                    # outer multiplicity (always integer after refactorisation)
  elements: dict[str, int]             # {symbol: count}, always integers after refactorisation
  charge: Optional[int] = None         # None = unknown; set by charge inference layer
  charge_confidence: str = 'unknown'   # 'lookup', 'balance', 'user', 'unknown'

  # Set by parser; cleared after refactorisation
  _raw: str = field(default='', repr=False)
  _had_fractions: bool = field(default=False, repr=False)
  _occupancy: float = field(default=1.0, repr=False)  # <1.0 = partial occupancy

  @property
  def formula_string(self) -> str:
    """Reconstruct the element string (C H first, then alphabetical)."""
    parts = []
    for sym in _element_order(self.elements):
      count = self.elements[sym]
      parts.append(sym if count == 1 else f"{sym}{count}")
    return ' '.join(parts)

  @property
  def count(self):
    """
    Number of this moiety per formula unit: multiplicity x _occupancy.
    Differs from multiplicity for fractional counts, e.g. 0.75(...) or
    1.5(H3 O) when Z' > 1. int when whole, else Fraction.
    """
    n = self.multiplicity * Fraction(self._occupancy).limit_denominator(1000)
    return int(n) if n.denominator == 1 else n

  @property
  def total_atoms(self) -> int:
    return self.multiplicity * sum(self.elements.values())

  def __repr__(self) -> str:
    formula = self.formula_string
    charge_str = ''
    if self.charge:  # 0 charge = neutral, omit from IUCr string
      sign = '+' if self.charge > 0 else '-'
      mag = abs(self.charge)
      # IUCr always requires the digit, even for 1+ / 1-
      charge_str = f" {mag}{sign}"
    # Partial occupancy: show as e.g. 0.68(H2 O) -- not valid IUCr
    # but honest; user must decide how to round in the edit box
    if self._occupancy != 1.0:
      occ = str(self._occupancy).rstrip('0').rstrip('.')
      return f"{occ}({formula}{charge_str})"
    mult = f"{self.multiplicity}" if self.multiplicity > 1 else ''
    needs_parens = self.multiplicity > 1 or charge_str
    if needs_parens:
      return f"{mult}({formula}{charge_str})"
    else:
      return formula


def _element_order(elements: dict[str, int]) -> list[str]:
  """C first, H second, then strictly alphabetical -- IUCr rule."""
  c = ['C'] if 'C' in elements else []
  h = ['H'] if 'H' in elements else []
  rest = sorted(sym for sym in elements if sym not in ('C', 'H'))
  return c + h + rest


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

# Matches one element token: capital letter + optional lowercase + optional
# integer or decimal count, e.g. 'C4', 'H', 'O0.5', 'Cl2'
_ELEMENT_RE = re.compile(
    r'([A-Z][a-z]?)(\d+\.?\d*|\.\d+)?'
)

# Matches an outer multiplicity (integer or decimal) before '('
_MULT_RE = re.compile(r'^(\d+\.?\d*|\.\d+)\((.+)\)$')


def _parse_element_string(s: str) -> tuple[dict[str, Fraction], bool]:
  """
  Parse 'C4 H8 O0.5' into {C: Fraction(4), H: Fraction(8), O: Fraction(1,2)}.
  Returns (elements, had_fractions).
  Raises ValueError if the string contains unrecognised tokens.
  """
  elements: dict[str, Fraction] = {}
  had_fractions = False
  # Strip charge suffix if present (e.g. '1+', '2-', '+', '-')
  s = re.sub(r'\s+\d*[+-]$', '', s.strip())
  s = s.strip()
  tokens = s.split()
  for token in tokens:
    m = _ELEMENT_RE.fullmatch(token)
    if not m:
      raise ValueError(f"Unrecognised element token: {repr(token)}")
    sym = m.group(1)
    raw_count = m.group(2)
    if raw_count is None:
      count = Fraction(1)
    else:
      # limit_denominator(1000) handles e.g. 0.5->1/2, 0.333->1/3,
      # 0.25->1/4, 22.5->45/2 cleanly
      count = Fraction(raw_count).limit_denominator(1000)
    if count.denominator != 1:
      had_fractions = True
    elements[sym] = elements.get(sym, Fraction(0)) + count
  return elements, had_fractions


def _parse_charge(s: str) -> Optional[int]:
  """
  Extract charge from a moiety string suffix.
  Recognises: '1+', '2-', '+', '-', '3+' etc.
  Returns signed integer or None.
  """
  m = re.search(r'\s+(\d*)([+-])$', s.strip())
  if not m:
    return None
  mag_str, sign = m.group(1), m.group(2)
  mag = int(mag_str) if mag_str else 1
  return mag if sign == '+' else -mag


def _lcm(a: int, b: int) -> int:
  return a * b // gcd(a, b)


def _refactorise(
    multiplicity: Fraction,
    elements: dict[str, Fraction],
    raw: str,
) -> MoietyFragment:
  """
  Given a (possibly fractional) multiplicity and (possibly fractional)
  element counts, find the canonical integer presentation.

  The invariant is:  multiplicity * elements[sym]  must be integer for all sym.
  We find the smallest integer k such that k * elements[sym] is integer for
  all sym, then set:
      new_elements[sym]    = k * elements[sym]   (integer)
      new_multiplicity     = multiplicity / k      (must also be integer)

  If new_multiplicity is not a positive integer after this, something is
  genuinely wrong upstream and we raise.
  """
  had_fractions = any(v.denominator != 1 for v in elements.values())
  mult_frac = Fraction(multiplicity)

  if not had_fractions and mult_frac.denominator == 1:
    # Happy path -- everything already integer
    return MoietyFragment(
        multiplicity=int(mult_frac),
        elements={sym: int(v) for sym, v in elements.items()},
        _raw=raw,
        _had_fractions=False,
    )

  # Find LCM of all element count denominators
  denominators = [v.denominator for v in elements.values()]
  k = reduce(_lcm, denominators, 1)

  # Guard: if k is large (> 12), the fractions are refinement noise
  # (e.g. C4.004 from partial occupancy), not chemically meaningful
  # fractions (1/2, 1/3, 1/4). Round element counts to nearest integer instead.
  if k > 12:
    new_elements = {sym: max(1, round(float(v))) if float(v) >= 0.5 else None
                    for sym, v in elements.items()}
    # Drop elements that rounded to zero
    new_elements = {sym: n for sym, n in new_elements.items() if n}
    if mult_frac.denominator == 1 and mult_frac > 0:
      return MoietyFragment(
          multiplicity=int(mult_frac),
          elements=new_elements,
          _raw=raw,
          _had_fractions=True,  # flag that rounding occurred
      )
    else:
      # Fractional outer multiplicity with noisy inner counts
      return MoietyFragment(
          multiplicity=1,
          elements=new_elements,
          _raw=raw,
          _had_fractions=True,
          _occupancy=float(mult_frac),
      )

  new_elements = {}
  for sym, v in elements.items():
    scaled = v * k
    if scaled.denominator != 1:
      raise ValueError(
          f"Cannot rationalise element count for {sym}: {v} * {k} = {scaled} "
          f"(raw: {repr(raw)})"
      )
    new_elements[sym] = int(scaled)

  new_mult = mult_frac / k
  if new_mult.denominator != 1 or new_mult <= 0:
    # The multiplicity is genuinely fractional and irreducible --
    # e.g. 0.679(H2 O) or 3.186(H2 O): measured partial occupancy.
    # Both cases are treated the same: store as _occupancy and flag
    # for the user to decide how to report. Never round silently.
    return MoietyFragment(
        multiplicity=1,
        elements=new_elements,
        _raw=raw,
        _had_fractions=True,
        _occupancy=float(new_mult),
    )

  return MoietyFragment(
      multiplicity=int(new_mult),
      elements=new_elements,
      _raw=raw,
      _had_fractions=had_fractions,
  )


def _parse_single_moiety(raw: str) -> MoietyFragment:
  """
  Parse one moiety token (already split on ',') into a MoietyFragment.
  Handles:
      'C4 H8 O3'           -> mult=1, no charge
      '2(H2 O)'            -> mult=2, no charge
      '4(H O0.5)'          -> mult=4, fractional -> refactorised to 2(H2 O)
      'C12 H17 N4 O S 1+'  -> mult=1, charge=+1
      '(Cd 2+)3'           -> mult=3, charge=+2  [IUCr alternate form]
  """
  s = raw.strip()

  # --- Detect charge (always at end, space-separated) ---
  charge = _parse_charge(s)

  # --- Detect outer multiplicity: '2(...)' or '(...)3' ---
  # Form A: N(...)  -- Olex2 output form
  m_a = re.match(r'^(\d+\.?\d*|\.\d+)?\((.+)\)$', s)
  # Form B: (...)N  -- IUCr alternate form
  m_b = re.match(r'^\((.+)\)(\d+)$', s)

  if m_a:
    mult_str = m_a.group(1)
    inner = m_a.group(2)
    multiplicity = Fraction(mult_str) if mult_str else Fraction(1)
    inner_charge = _parse_charge(inner)
    if inner_charge is not None and charge is None:
      charge = inner_charge
    elements, had_frac = _parse_element_string(inner)
  elif m_b:
    inner = m_b.group(1)
    mult_str = m_b.group(2)
    multiplicity = Fraction(mult_str)
    inner_charge = _parse_charge(inner)
    if inner_charge is not None and charge is None:
      charge = inner_charge
    elements, had_frac = _parse_element_string(inner)
  else:
    # No parentheses -- plain formula, multiplicity = 1
    multiplicity = Fraction(1)
    elements, had_frac = _parse_element_string(s)

  fragment = _refactorise(multiplicity, elements, raw)
  if charge is not None:
    fragment.charge = charge
    fragment.charge_confidence = 'parsed'
  return fragment


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_moiety_string(s: Optional[str]) -> list[MoietyFragment]:
  """
  Parse the string returned by xf.latt.GetMoietyFormula.

  Returns an empty list if s is None or empty (no structure loaded).
  Raises ValueError with a descriptive message on malformed input.

  Examples
  --------
  >>> parse_moiety_string("C4 H8 Ca O8, 2(H2 O)")
  [C4 H8 Ca O8, 2(H2 O)]

  >>> parse_moiety_string("4(H O0.5)")
  [2(H2 O)]   # refactorised; _had_fractions=True records it was mangled

  >>> parse_moiety_string(None)
  []
  """
  if not s:
    return []

  fragments = []
  for token in s.split(','):
    token = token.strip()
    if not token:
      continue
    try:
      frag = _parse_single_moiety(token)
    except ValueError as e:
      raise ValueError(f"Failed to parse moiety token {repr(token)}: {e}") from e
    fragments.append(frag)

  return fragments


def same_moiety(a: str, b: str) -> bool:
  """
  True if two moiety strings list the same units, in whatever order and
  whatever the common multiple ('2(K), C2 O4' and '4(K), 2(C2 O4)' are the same).
  """
  def normal(s):
    units = []
    for token in s.split(', '):
      m = re.fullmatch(r'(\d+)\((.*)\)', token)
      units.append((int(m.group(1)), f"({m.group(2)})") if m else (1, token))
    common = reduce(gcd, (n for n, _ in units), 0) or 1
    return sorted((n // common, unit.strip('()')) for n, unit in units)
  return normal(a) == normal(b)


def format_moiety_string(fragments: list[MoietyFragment]) -> str:
  """
  Format a list of MoietyFragments back to an IUCr-compliant moiety string.
  This is the *output* formatter -- charge inference runs before this.
  """
  return ', '.join(repr(f) for f in fragments)

def format_moiety_string_with_mask(fragments, masked_fragments=None, unknown_masked=False):
  """
  Format ordered + masked fragments to an IUCr-compliant moiety string,
  with masked content in square brackets (Spek/SQUEEZE convention).

  fragments         : ordered model fragments
  masked_fragments  : list[MoietyFragment] for masked region, or None
  unknown_masked    : if True and no masked_fragments, append '[+ solvent]'

  Examples
  --------
  format_moiety_string_with_mask(frags)
    -> '(Cu 2+), 2(C10 H8 N2), 2(Cl 1-)'

  format_moiety_string_with_mask(frags, masked_fragments=[water2])
    -> '(Cu 2+), 2(C10 H8 N2), 2(Cl 1-), [2(H2 O)]'

  format_moiety_string_with_mask(frags, unknown_masked=True)
    -> '(Cu 2+), 2(C10 H8 N2), 2(Cl 1-), [+ solvent]'
  """
  ordered = ', '.join(repr(f) for f in fragments)
  if masked_fragments:
    masked = ', '.join(repr(f) for f in masked_fragments)
    return f"{ordered}, [{masked}]"
  elif unknown_masked:
    return f"{ordered}, [+ solvent]"
  else:
    return ordered