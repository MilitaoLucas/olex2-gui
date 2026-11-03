"""
gui/moiety/charges.py

Charge inference for moiety fragments, via:
  1. Exact formula lookup  (common ions, solvents, ligands)
  2. Single-element metal  (element -> most likely charge(s))
  3. Charge balance        (solve for one unknown if all others known)
  4. Remaining unknowns    (left as None for user to assign in GUI)

Pipeline position:
  list[MoietyFragment] -> [THIS MODULE] -> list[MoietyFragment] (charges filled)

All lookup data is in this file as plain dicts so it can be extended easily.
The keys are *canonical formula strings* as produced by MoietyFragment.formula_string
(C first, H second, then alphabetical, counts omitted when 1, no spaces between
symbol and count but spaces between tokens) -- e.g. 'H2 O', 'C2 O4', 'P F6'.
"""

from __future__ import annotations
from fractions import Fraction
from typing import Optional
from .parser import MoietyFragment


# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

# Exact formula -> charge (int)
# Key is the canonical formula_string from MoietyFragment
# Confidence: 'lookup'

FORMULA_CHARGES: dict[str, int] = {

    # --- Solvents (neutral) ---
    'H2 O':              0,   # water
    'C H4 O':            0,   # methanol
    'C2 H6 O':           0,   # ethanol
    'C2 H6 O S':         0,   # DMSO
    'C3 H7 N O':         0,   # DMF
    'C3 H6 O':           0,   # acetone
    'C2 H3 N':           0,   # acetonitrile
    'C H2 Cl2':          0,   # DCM
    'C Cl3 H':           0,   # chloroform (CHCl3)  -- CHCl3
    'C7 H8':             0,   # toluene
    'C6 H6':             0,   # benzene
    'C4 H8 O':           0,   # THF
    'C4 H8 O2':          0,   # 1,4-dioxane / ethyl acetate
    'C5 H5 N':           0,   # pyridine (as solvent)
    'C3 H8 O':           0,   # isopropanol
    'C2 H5 N O':         0,   # NMP fragment / acetamide
    'C5 H9 N O':         0,   # NMP (N-methyl-2-pyrrolidone)
    'C3 H7 N O2':        0,   # DMF isomer / nitropropane
    'C8 H10':            0,   # xylene
    'C6 H12':            0,   # cyclohexane
    'C6 H14':            0,   # hexane
    'C5 H12':            0,   # pentane
    'C4 H10 O':          0,   # diethyl ether
    'C6 H5 Cl':          0,   # chlorobenzene

    # --- Simple anions ---
    'F':                -1,
    'Cl':               -1,
    'Br':               -1,
    'I':                -1,
    'O H':              -1,   # hydroxide
    'N3':               -1,   # azide
    'N C S':            -1,   # thiocyanate
    'N C O':            -1,   # cyanate
    'C N':              -1,   # cyanide
    'N O2':             -1,   # nitrite
    'N O3':             -1,   # nitrate
    'Cl O4':            -1,   # perchlorate
    'Cl O3':            -1,   # chlorate
    'B F4':             -1,   # tetrafluoroborate
    'P F6':             -1,   # hexafluorophosphate
    'Sb F6':            -1,   # hexafluoroantimonate
    'As F6':            -1,   # hexafluoroarsenate
    'C F3 O3 S':        -1,   # triflate (OTf-)
    'C2 F3 O2':         -1,   # trifluoroacetate
    'C2 H3 O2':         -1,   # acetate
    'H C O2':           -1,   # formate
    'C H O2':           -1,   # formate (alt element order -- should not occur but guard)
    'C7 H5 O2':         -1,   # benzoate
    'C7 H4 F3 O2':      -1,   # 4-fluorobenzoate / trifluoromethylbenzoate
    'N2 F3 S2 O4':      -1,   # bis(trifluoromethanesulfonyl)imide (NTf2-)  -- approx
    'C2 F6 N O4 S2':    -1,   # NTf2- exact

    # --- Dianions ---
    'O':                -2,   # oxide
    'S':                -2,   # sulfide
    'Se':               -2,   # selenide
    'Te':               -2,   # telluride
    'O2':               -2,   # peroxide
    'S O4':             -2,   # sulfate
    'S O3':             -2,   # sulfite
    'S2 O3':            -2,   # thiosulfate
    'S2 O7':            -2,   # pyrosulfate
    'C O3':             -2,   # carbonate
    'Cr O4':            -2,   # chromate
    'C2 O4':            -2,   # oxalate
    'C4 H4 O4':         -2,   # fumarate / maleate
    'C4 H4 O6':         -2,   # tartrate (fully deprotonated)
    'C6 H4 O4':         -2,   # phthalate / terephthalate (BDC2-)
    'C8 H4 O4':         -2,   # BDC2- (1,4-benzenedicarboxylate)
    'C10 H6 O4':        -2,   # 2,6-NDC2- (naphthalenedicarboxylate)
    'C12 H8 O4':        -2,   # BPDC2- (biphenyldicarboxylate)
    'H P O4':           -2,   # hydrogen phosphate
    'Mo O4':            -2,   # molybdate
    'W O4':             -2,   # tungstate
    'Si F6':            -2,   # hexafluorosilicate
    'Sn Cl6':           -2,   # hexachlorostannate
    'Pt Cl4':           -2,   # tetrachloroplatinate(II)

    # --- Trianions ---
    'N':                -3,   # nitride
    'P':                -3,   # phosphide
    'P O4':             -3,   # phosphate
    'C6 H3 O6':         -3,   # BTC3- (1,3,5-benzenetricarboxylate, trimesate)
    'C9 H3 O6':         -3,   # BTC3- (alt, trimellitate)
    'C6 H3 O9':         -3,   # citrate (fully deprotonated, C6H5O7 loses 3H)
    'C6 H5 O7':         -3,   # citrate

    # --- Tetraanions ---
    'C8 H2 O8':         -4,   # BTEC4- (1,2,4,5-benzenetetracarboxylate)
    'C10 H2 O8':        -4,   # NTEC4- (naphthalenetetracarboxylate)

    # --- Simple cations ---
    'H':                +1,   # proton
    'Li':               +1,
    'Na':               +1,
    'K':                +1,
    'Rb':               +1,
    'Cs':               +1,
    'Ag':               +1,
    'Tl':               +1,
    'N H4':             +1,   # ammonium
    'H2 N':             +1,   # ... shouldn't appear but guard
    'C H6 N':           +1,   # methylammonium
    'C2 H8 N':          +1,   # dimethylammonium / ethylammonium
    'C4 H12 N':         +1,   # tetramethylammonium
    'C5 H6 N':          +1,   # pyridinium
    'C10 H9 N2':        +1,   # 4,4'-bipyridinium (monocation)

    # --- Dications ---
    'Mg':               +2,
    'Ca':               +2,
    'Sr':               +2,
    'Ba':               +2,
    'Zn':               +2,
    'Cd':               +2,
    'Hg':               +2,
    'Pb':               +2,
    'Sn':               +2,   # Sn(II) -- Sn(IV) also common
    'Pd':               +2,
    'Pt':               +2,   # Pt(II) most common
    'C10 H10 N2':       +2,   # 4,4'-bipyridinium (dication, paraquat)
    'C12 H14 N2':       +2,   # viologen family

    # --- Trications ---
    'Al':               +3,
    'Ga':               +3,
    'In':               +3,
    'Bi':               +3,
    'Sc':               +3,
    'Y':                +3,
    'La':               +3,
    'Ce':               +3,
    'Pr':               +3,
    'Nd':               +3,
    'Sm':               +3,
    'Eu':               +3,   # Eu(II) also known but rare
    'Gd':               +3,
    'Tb':               +3,
    'Dy':               +3,
    'Ho':               +3,
    'Er':               +3,
    'Tm':               +3,
    'Yb':               +3,
    'Lu':               +3,

}

# Single bare element -> list of likely charges, most common first
# Used when formula is a single element not in FORMULA_CHARGES
# Confidence: 'element_guess'

ELEMENT_CHARGES: dict[str, list[int]] = {
    # Transition metals -- ambiguous, list most common first
    'Fe':  [+3, +2],
    'Co':  [+2, +3],
    'Ni':  [+2],
    'Cu':  [+2, +1],
    'Mn':  [+2, +3, +4],
    'Cr':  [+3, +2, +6],
    'V':   [+3, +4, +5, +2],
    'Ti':  [+4, +3],
    'Mo':  [+4, +6, +3, +5],
    'W':   [+4, +6],
    'Re':  [+3, +4, +5, +6, +7],
    'Ru':  [+2, +3],
    'Rh':  [+3, +2],
    'Os':  [+2, +3, +4],
    'Ir':  [+3, +2],
    'Au':  [+3, +1],
    'Hf':  [+4],
    'Zr':  [+4],
    'Nb':  [+5, +4, +3],
    'Ta':  [+5],
    'Tc':  [+4, +7],
    'Ag':  [+1],
    # p-block with variable oxidation state
    'Sn':  [+4, +2],
    'Pb':  [+2, +4],
    'Sb':  [+3, +5],
    'Bi':  [+3, +5],
    'Ge':  [+4, +2],
    'As':  [+3, +5],
    # Lanthanides with variable states
    'Ce':  [+3, +4],
    'Eu':  [+3, +2],
    'Sm':  [+3, +2],
    'Yb':  [+3, +2],
    'Tb':  [+3, +4],
}

# Formulae that are definitely neutral but not solvents
# (ligands coordinated as neutral donors, gases, etc.)
NEUTRAL_FORMULAE: set[str] = {
    'C O',        # carbon monoxide
    'N O',        # nitric oxide (as ligand)
    'N2',         # dinitrogen
    'C2 H8 N2',   # ethylenediamine (en) -- neutral ligand
    'C10 H8 N2',  # 2,2'-bipyridine (bipy) -- neutral ligand
    'C12 H8 N2',  # 1,10-phenanthroline (phen)
    'C15 H11 N3', # terpyridine (terpy)
    'C3 H7 N O',  # DMF (also in solvents above)
    'C18 H15 P',  # triphenylphosphine (PPh3)
    'C4 H6 O',    # furan / crotonaldehyde -- neutral
    'C5 H5 N',    # pyridine -- neutral ligand (also in solvents)
    'N H3',       # ammonia -- neutral ligand
    'C2 H6 S',    # dimethylsulfide -- neutral ligand
}


# ---------------------------------------------------------------------------
# Inference engine
# ---------------------------------------------------------------------------

def _canonical(f: MoietyFragment) -> str:
  """Return the canonical formula string for lookup."""
  return f.formula_string


def _lookup_exact(f: MoietyFragment) -> Optional[int]:
  """Exact formula match in FORMULA_CHARGES or NEUTRAL_FORMULAE."""
  key = _canonical(f)
  if key in NEUTRAL_FORMULAE:
    return 0
  return FORMULA_CHARGES.get(key, None)


def _lookup_element(f: MoietyFragment) -> Optional[int]:
  """
  Single bare element with known common oxidation state.
  Returns the *most common* charge as a best guess.
  Confidence will be 'element_guess' to flag ambiguity.
  """
  if len(f.elements) == 1:
    sym = next(iter(f.elements))
    charges = ELEMENT_CHARGES.get(sym)
    if charges:
      return charges[0]
  return None


def _element_guess_is_ambiguous(f: MoietyFragment) -> bool:
  """True if the element has multiple common oxidation states."""
  if len(f.elements) == 1:
    sym = next(iter(f.elements))
    charges = ELEMENT_CHARGES.get(sym, [])
    return len(charges) > 1
  return False


def as_number(x):
  """int if x is whole, else a float (3 decimals) -- for charge sums."""
  x = Fraction(x).limit_denominator(1000)
  return int(x) if x.denominator == 1 else round(float(x), 3)


def _charge_balance(fragments: list[MoietyFragment]):
  """
  Sum of count * charge for all fragments with known charge. Uses count,
  not multiplicity: with Z' > 1 a fragment can be present 0.5 or 1.5 times.
  """
  return as_number(sum(
      f.count * f.charge
      for f in fragments
      if f.charge is not None
  ))


def _solve_unknown(fragments: list[MoietyFragment]) -> list[MoietyFragment]:
  """
  If exactly one fragment has unknown charge, solve from balance.
  Modifies in place, returns same list.

  Guard: only solve if at least one other fragment has a known NON-ZERO
  charge. Without that constraint, balance trivially gives q=0 for any
  single unknown -- which is not a real inference, just a vacuous truth.
  A single-fragment formula with no other constraints must remain None.
  """
  unknowns = [f for f in fragments if f.charge is None]
  if len(unknowns) != 1:
    return fragments

  # Check that balance is actually constrained by something non-trivial
  known_nonzero = any(
      f.charge is not None and f.charge != 0
      for f in fragments
  )
  if not known_nonzero:
    # All other fragments are neutral (or there are none) --
    # balance would give q=0 but that's not a real inference
    return fragments

  unknown = unknowns[0]
  known_sum = _charge_balance(fragments)
  # unknown.count * q + known_sum = 0
  if unknown.count == 0:
    return fragments
  q = Fraction(-known_sum).limit_denominator(1000) / unknown.count
  if q.denominator == 1:
    unknown.charge = int(q)
    unknown.charge_confidence = 'balance'
  return fragments


# Elements that indicate ionic context is plausible
_METALS = {
    'Li','Na','K','Rb','Cs',                          # alkali
    'Mg','Ca','Sr','Ba',                              # alkaline earth
    'Al','Ga','In','Tl',                              # p-block metals
    'Sn','Pb','Bi','Sb',
    'Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn', # 3d transition
    'Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd', # 4d transition
    'Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg',      # 5d transition
    'La','Ce','Pr','Nd','Pm','Sm','Eu','Gd',          # lanthanides
    'Tb','Dy','Ho','Er','Tm','Yb','Lu',
    'Th','U',                                          # actinides
}

# Known ionic species (single elements or simple formulae always charged)
_ALWAYS_IONIC = {'F','Cl','Br','I','O','S','Se','Te','N3'}


def _has_ionic_context(fragments):
  """
  Return True if the fragment list contains at least one metal or known
  ionic species. Without ionic context, balance inference is not meaningful
  for unknown fragments.

  Rules:
  - Metals are recognised anywhere in a fragment (bare or coordinated)
  - Simple ionic species (halides, oxide, etc.) only count as ionic context
    when they appear as bare single-element fragments, not when embedded
    in organic molecules (O in sucrose is not oxide O2-)
  - Known charged formulae in the lookup table also count
  """
  for f in fragments:
    if len(f.elements) == 1:
      sym = next(iter(f.elements))
      # Bare single element: check both metals and ionic species
      if sym in _METALS or sym in _ALWAYS_IONIC:
        return True
    else:
      # Multi-element fragment: only metals indicate ionic context
      for sym in f.elements:
        if sym in _METALS:
          return True
    # Known charged formula in lookup table
    key = f.formula_string
    if key in FORMULA_CHARGES and FORMULA_CHARGES[key] != 0:
      return True
    # Charged fragment the user has vouched for
    if f.charge and f.charge_confidence in ('user', 'user_lookup'):
      return True
  return False


def infer_charges(fragments: list[MoietyFragment],
                  user_lookup: dict = None) -> list[MoietyFragment]:
  """
  Run charge inference on a list of MoietyFragments.
  Modifies fragments in place (charge, charge_confidence).
  Returns the same list.

  Inference order:
    1. Already has a charge (parsed from string) -- leave it
    2. User lookup table ({formula_string: charge}, see user_db.py)
    3. Exact formula lookup
    4. Single-element lookup (with ambiguity flag)
    5. Charge balance (if exactly one unknown remains AND ionic context exists)
    6. If no ionic context at all -- assume neutral for unknowns
    7. Give up -- leave as None for user

  Note: without a metal or known ion present, unknown fragments are assumed
  neutral ('assumed_neutral') rather than left as None, since purely organic
  structures are almost always neutral.
  """
  for f in fragments:
    if f.charge is not None:
      # Already known (parsed from input string)
      if f.charge_confidence == 'unknown':
        f.charge_confidence = 'parsed'
      continue

    if user_lookup and f.formula_string in user_lookup:
      f.charge = user_lookup[f.formula_string]
      f.charge_confidence = 'user_lookup'
      continue

    charge = _lookup_exact(f)
    if charge is not None:
      f.charge = charge
      f.charge_confidence = 'lookup'
      continue

    charge = _lookup_element(f)
    if charge is not None:
      f.charge = charge
      f.charge_confidence = (
          'element_ambiguous' if _element_guess_is_ambiguous(f)
          else 'element_guess'
      )
      continue

    # Leave as None -- may be resolved by balance below

  # One final pass: solve by balance if exactly one unknown
  _solve_unknown(fragments)

  # If no ionic context, assume remaining unknowns are neutral
  if not _has_ionic_context(fragments):
    for f in fragments:
      if f.charge is None:
        f.charge = 0
        f.charge_confidence = 'assumed_neutral'

  return fragments


def balance_summary(fragments: list[MoietyFragment]) -> dict:
  """
  Return a summary dict for console/GUI display:
    known_sum   : sum of (mult * charge) for known fragments
    n_unknown   : number of fragments with charge still None
    balanced    : True if known_sum == 0 and n_unknown == 0
  """
  known_sum = _charge_balance(fragments)
  n_unknown = sum(1 for f in fragments if f.charge is None)
  return {
      'known_sum': known_sum,
      'n_unknown': n_unknown,
      'balanced': known_sum == 0 and n_unknown == 0,
  }


# ---------------------------------------------------------------------------
# Normalise lookup table keys at import time
# Keys above are written in human-readable order for clarity.
# Re-key through the canonical element ordering so they match formula_string.
# ---------------------------------------------------------------------------

def _normalise_key(formula_str: str) -> str:
  from .parser import _parse_element_string, _element_order
  elements, _ = _parse_element_string(formula_str)
  int_elements = {sym: int(v) for sym, v in elements.items()}
  parts = []
  for sym in _element_order(int_elements):
    count = int_elements[sym]
    parts.append(sym if count == 1 else f"{sym}{count}")
  return ' '.join(parts)


FORMULA_CHARGES = {_normalise_key(k): v for k, v in FORMULA_CHARGES.items()}
NEUTRAL_FORMULAE = {_normalise_key(k) for k in NEUTRAL_FORMULAE}


# ---------------------------------------------------------------------------
# Chemical reasonableness checking
# ---------------------------------------------------------------------------
#
# Only two things are reliably checkable without connectivity information:
#
# 1. Unambiguous ions (Cl-, Br-, OH-, etc.) -- if balance assigns them
#    a charge other than their known value, the metal charge is wrong.
#
# 2. Ambiguous metals (Fe, Cu, Mn...) -- already flagged as
#    'element_ambiguous' by infer_charges(); check_reasonableness()
#    reinforces that flag when the balance result looks odd.
#
# Multi-element ligand rules have been deliberately omitted: without
# connectivity we cannot distinguish coordination mode, and the formula
# protonation state is already correctly handled by charge balance.
# ---------------------------------------------------------------------------

_UNAMBIGUOUS_IONS = {
    _normalise_key(k): v
    for k, v in {
        'F': -1, 'Cl': -1, 'Br': -1, 'I': -1,
        'O': -2, 'S': -2,
        'N3': -1, 'C N': -1, 'N C S': -1,
        'O H': -1,
        'N H4': +1, 'Na': +1, 'K': +1, 'Rb': +1, 'Cs': +1,
        'Ca': +2, 'Mg': +2, 'Ba': +2, 'Sr': +2,
    }.items()
}


def check_reasonableness(fragments):
  """
  Check fragments for chemical reasonableness after charge inference.
  Sets charge_confidence = 'balance_suspect' and adds a
  charge_suspect_reason attribute where problems are found.

  Checks performed:
    1. Unambiguous ions solved by balance with wrong charge
       -> flag the ion AND the ambiguous metal fragments
    2. (Future: bond-distance-based metal oxidation state check)

  Returns the same list.
  """
  for f in fragments:
    if f.charge_confidence != 'balance':
      continue
    key = f.formula_string
    expected = _UNAMBIGUOUS_IONS.get(key)
    if expected is not None and f.charge != expected:
      f.charge_confidence = 'balance_suspect'
      f.charge_suspect_reason = (
          f"balance gives {f.charge:+d} but {key} is always "
          f"{expected:+d} -- the metal oxidation state is likely wrong"
      )
      # Flag ambiguous metal fragments as the likely culprit
      for other in fragments:
        if other is f:
          continue
        if other.charge_confidence in ('element_ambiguous', 'element_guess'):
          other.charge_confidence = 'element_ambiguous'
          other.charge_suspect_reason = getattr(
              other, 'charge_suspect_reason',
              f"metal charge may be wrong (see {key} above)"
          )

  return fragments


# ---------------------------------------------------------------------------
# Mixed-valence suggestions
# ---------------------------------------------------------------------------

def suggest_mixed_valence(fragments, target_charge):
  """
  For ambiguous metal fragments where the current charge assignment
  doesn't balance, suggest alternative oxidation state combinations
  that would bring the total closer to target_charge.

  fragments     : list[MoietyFragment] -- the full fragment list
  target_charge : the charge the metal fragments need to sum to
                  (i.e. -known_nonmetal_sum)

  Returns a list of suggestion strings, or [] if nothing useful found.
  """
  # Collect ambiguous metal fragments
  ambiguous = [
      f for f in fragments
      if f.charge_confidence in ('element_ambiguous', 'element_guess')
      and len(f.elements) == 1
  ]
  if not ambiguous:
    return []

  suggestions = []

  for f in ambiguous:
    sym = next(iter(f.elements))
    candidates = ELEMENT_CHARGES.get(sym, [])
    if len(candidates) < 2:
      continue
    n = f.multiplicity

    # Try all combinations of oxidation states for n atoms of this metal
    # that sum to target_charge contribution from this metal
    # (simple case: all same oxidation state)
    for q in candidates:
      if q != f.charge:
        total = q * n
        suggestions.append(
            f"  - All {n}x {sym} as {q:+d}: "
            f"{n}({sym} {abs(q)}{'+-'[q<0]})"
            f"  [contribution: {total:+d}]"
        )

    # Mixed valence: try pairs of oxidation states (only if n >= 2)
    if n >= 2 and len(candidates) >= 2:
      for i, q1 in enumerate(candidates):
        for q2 in candidates[i+1:]:
          # n1*q1 + n2*q2 = target_charge, n1+n2 = n
          # n1*q1 + (n-n1)*q2 = target_charge
          # n1*(q1-q2) = target_charge - n*q2
          denom = q1 - q2
          if denom == 0:
            continue
          num = target_charge - n * q2
          if num % denom != 0:
            continue
          n1 = num // denom
          n2 = n - n1
          if n1 <= 0 or n2 <= 0:
            continue
          total = n1 * q1 + n2 * q2
          suggestion = f"  - Mixed valence: "
          parts = []
          if n1 == 1:
            parts.append(f"({sym} {abs(q1)}{'+-'[q1<0]})")
          else:
            parts.append(f"{n1}({sym} {abs(q1)}{'+-'[q1<0]})")
          if n2 == 1:
            parts.append(f"({sym} {abs(q2)}{'+-'[q2<0]})")
          else:
            parts.append(f"{n2}({sym} {abs(q2)}{'+-'[q2<0]})")
          suggestion += ", ".join(parts)
          suggestion += f"  [contribution: {total:+d}]"
          suggestions.append(suggestion)

  return suggestions