"""
gui/moiety/__init__.py

Moiety formula parsing, charge inference, and IUCr-compliant formatting
for the Olex2 moiety editor GUI tool.

Public API (Python)
-------------------
    parse_moiety_string(s)      -> list[MoietyFragment]
    format_moiety_string(frags) -> str
    MoietyFragment              (dataclass)

Public API (Olex2 console / GUI)
---------------------------------
    spy.gui.moiety.report()     -> human-readable console report
    spy.gui.moiety.fragments()  -> JSON for GUI (later)

Typical usage
-------------
    import gui.moiety
    spy.gui.moiety.report()
"""

from .parser import parse_moiety_string, format_moiety_string, format_moiety_string_with_mask, MoietyFragment
from .charges import infer_charges, balance_summary, check_reasonableness, suggest_mixed_valence, as_number
from . import user_db

__all__ = [
    'parse_moiety_string',
    'format_moiety_string',
    'MoietyFragment',
    'infer_charges',
    'balance_summary',
    'check_reasonableness',
]

# ---------------------------------------------------------------------------
# Name -> formula resolver (from moieties.csv)
# ---------------------------------------------------------------------------

def _load_name_table():
    """
    Load moieties.csv from the same directory as this module.
    Returns dict of {lowercase_name: canonical_formula_string}.
    Silently returns {} if the file is missing.
    """
    import os, re
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'moieties.csv')
    if not os.path.exists(csv_path):
        return {}
    result = {}
    with open(csv_path, 'r') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#') or ';' not in line:
                continue
            nick, formula = line.split(';', 1)
            nick    = nick.strip().lower()
            formula = formula.strip()
            if not nick or not formula:
                continue
            # Normalise formula: insert spaces between digits and capitals
            formula = re.sub(r'([0-9])([A-Z])', r'\1 \2', formula).strip()
            # Validate through our parser — skip entries that don't parse
            try:
                frags = parse_moiety_string(formula)
                if frags:
                    result[nick] = frags[0].formula_string
            except Exception:
                pass
    return result


# Loaded once at import time
_NAME_TABLE = _load_name_table()


def _resolve_name(name):
    """
    Resolve a common name or abbreviation to a canonical formula string.
    Returns the formula string, or None if not found.
    Also accepts a formula string directly (returns it normalised).
    """
    name = name.strip()
    # Try as a name first
    hit = _NAME_TABLE.get(name.lower())
    if hit:
        return hit
    # Try parsing directly as a formula
    try:
        frags = parse_moiety_string(name)
        if frags:
            return frags[0].formula_string
    except Exception:
        pass
    return None


# Module-level state — persists for the Olex2 session
_current_fragments = []   # list[MoietyFragment]
_current_proposed = ''      # last proposed formula string
_current_needs_input = False  # whether apply() should prompt
_current_connected = ''     # last connected formula -- cache key


# ---------------------------------------------------------------------------
# Confidence labels for display
# ---------------------------------------------------------------------------

_CONFIDENCE_LABELS = {
    'lookup':            'lookup',
    'element_guess':     'element (unambiguous)',
    'element_ambiguous': 'element (ambiguous!)',
    'balance':           'charge balance',
    'parsed':            'from formula string',
    'user':              'user',
    'user_lookup':       'user lookup',
    'assumed_neutral':   'assumed neutral (no ionic context)',
    'balance_suspect':   'balance (SUSPECT -- verify!)',
    'unknown':           '???',
}


def _signed(n):
    """+2 / -1 / 0 -- no sign on zero."""
    return f"{n:+g}" if n else '0'


def _fmt_charge(charge, confidence):
    if charge is None:
        return '?', '???'
    sign = '+' if charge > 0 else ('' if charge == 0 else '-')
    mag = abs(charge)
    charge_str = '0' if mag == 0 else f"{mag}{sign}"
    conf_str = _CONFIDENCE_LABELS.get(confidence, confidence)
    return charge_str, conf_str


# ---------------------------------------------------------------------------
# Electron counting (lifted cleanly from GetMaskInfo.py)
# ---------------------------------------------------------------------------

def _electrons_from_formula(formula_string):
    """
    Count electrons and non-H atoms in a canonical formula string.
    Uses Olex2's PeriodicTable if available; falls back to a small
    built-in table for the most common elements.

    Returns (n_electrons, n_non_hydrogen) or (None, None) on failure.
    """
    # Built-in Z table for the most common elements — extended as needed
    _Z = {
        'H':1,  'He':2, 'Li':3,  'Be':4,  'B':5,   'C':6,   'N':7,
        'O':8,  'F':9,  'Ne':10, 'Na':11, 'Mg':12, 'Al':13, 'Si':14,
        'P':15, 'S':16, 'Cl':17, 'Ar':18, 'K':19,  'Ca':20, 'Sc':21,
        'Ti':22,'V':23, 'Cr':24, 'Mn':25, 'Fe':26, 'Co':27, 'Ni':28,
        'Cu':29,'Zn':30,'Ga':31, 'Ge':32, 'As':33, 'Se':34, 'Br':35,
        'Kr':36,'Rb':37,'Sr':38, 'Y':39,  'Zr':40, 'Nb':41, 'Mo':42,
        'Tc':43,'Ru':44,'Rh':45, 'Pd':46, 'Ag':47, 'Cd':48, 'In':49,
        'Sn':50,'Sb':51,'Te':52, 'I':53,  'Xe':54, 'Cs':55, 'Ba':56,
        'La':57,'Ce':58,'Pr':59, 'Nd':60, 'Pm':61, 'Sm':62, 'Eu':63,
        'Gd':64,'Tb':65,'Dy':66, 'Ho':67, 'Er':68, 'Tm':69, 'Yb':70,
        'Lu':71,'Hf':72,'Ta':73, 'W':74,  'Re':75, 'Os':76, 'Ir':77,
        'Pt':78,'Au':79,'Hg':80, 'Tl':81, 'Pb':82, 'Bi':83,
    }
    try:
        from PeriodicTable import PeriodicTable
        pt = PeriodicTable().PeriodicTable()
        use_pt = True
    except ImportError:
        use_pt = False

    n_e = 0
    n_non_h = 0
    try:
        tokens = formula_string.split()
        for token in tokens:
            # token is like 'C6', 'H4', 'O', 'Ca'
            sym = token.rstrip('0123456789')
            count_str = token[len(sym):]
            count = float(count_str) if count_str else 1.0
            if use_pt:
                z = int(pt[sym].get('Z', 0))
            else:
                z = _Z.get(sym, 0)
            n_e += z * count
            if sym != 'H':
                n_non_h += count
        return n_e, n_non_h
    except Exception:
        return None, None


# ---------------------------------------------------------------------------
# Mask data access
# ---------------------------------------------------------------------------

def _get_mask_info():
    """
    Retrieve solvent mask data from the current Olex2 model.

    Returns a dict with keys:
        base          : 'smtbx_masks' or 'platon_squeeze'
        total_electrons : total masked electrons (per formula unit)
        total_volume    : total void volume (A^3, per formula unit)
        n_voids         : number of distinct voids
        content         : list of user-assigned content strings (may be '?')
        factor          : Z/Z' normalisation factor used
    or None if no mask is present or data unavailable.
    """
    try:
        import olx
        from olexFunctions import OV
    except ImportError:
        return None

    # Determine which mask program was used
    try:
        prg = OV.GetParam(
            'snum.refinement.recompute_mask_before_refinement_prg', 'Olex2')
        base = 'platon_squeeze' if prg == 'Platon' else 'smtbx_masks'
    except Exception:
        base = 'smtbx_masks'

    sNum = OV.ModelSrc()

    # Get the CIF model
    try:
        cif_model = olx.cif_model
        if not cif_model or sNum not in cif_model:
            return None
        block = cif_model[sNum]
    except Exception:
        return None

    # Pull void data
    try:
        volumes   = block.get('_%s_void_volume' % base)
        electrons = block.get('_%s_void_count_electrons' % base)
        numbers   = block.get('_%s_void_nr' % base)
        contents  = block.get('_%s_void_content' % base, [])
    except Exception:
        return None

    if not electrons or not volumes:
        return None

    # Normalisation: the CIF mask fields (_smtbx_masks_void_count_electrons
    # etc.) always store values per unit cell, regardless of what the
    # mask GUI displays (which may be per ASU or per FU per user preference).
    # Divide by Z to convert cell values to per-formula-unit.
    try:
        Z      = float(olx.xf.au.GetZ())
        factor = max(1, round(Z))
    except Exception:
        factor = 1

    # Sum across all voids, skip tiny ones (< 15 A^3, same threshold as GetMaskInfo)
    total_e = 0.0
    total_v = 0.0
    n_voids = 0
    seen_volumes = set()

    try:
        for vol_s, elec_s in zip(volumes, electrons):
            vol  = float(vol_s)
            elec = float(elec_s)
            if vol < 15:
                continue
            # Deduplicate by volume (same logic as GetMaskInfo)
            vol_key = "%.0f" % round(vol, 0)
            if vol_key in seen_volumes:
                continue
            seen_volumes.add(vol_key)
            # Count multiplicity of this void
            mult = sum(
                1 for v in volumes
                if "%.0f" % round(float(v), 0) == vol_key
            )
            total_e += elec * mult
            total_v += vol  * mult
            n_voids += 1
    except Exception:
        return None

    if total_e == 0:
        return None

    # Convert to per-formula-unit
    total_e_fu = total_e / factor
    total_v_fu = total_v / factor

    return {
        'base':              base,
        'total_electrons':   total_e_fu,
        'total_volume':      total_v_fu,
        'n_voids':           n_voids,
        'content':           list(contents),
        'factor':            factor,   # = Z (always per-cell / Z = per-FU)
    }


# ---------------------------------------------------------------------------
# Core workflow
# ---------------------------------------------------------------------------

def _get_raw_moiety():
    """
    Get moiety strings from Olex2 using both disconnected and connected metal bonds.

    Returns (raw_disconnected, raw_connected).

    Disconnected (conn $M 0): metals appear as separate fragments — used for
    charge inference, since we need to see metal and ligands separately.

    Connected (conn $M default): chemically correct whole-molecule fragments —
    used for the reported formula.

    Note: conn $M resets to Olex2 defaults. If the user has set a custom metal
    connectivity, that will be lost. This is an acceptable trade-off since
    custom connectivity is rarely used in practice.
    """
    try:
        import olx
        olx.Conn('$M', '0')                    # disconnect all metals
        raw_disconnected = olx.xf.latt.GetMoiety()
        olx.Conn('$M')                           # restore defaults
        raw_connected = olx.xf.latt.GetMoiety()
        return raw_disconnected, raw_connected
    except Exception:
        return None, None


def _load_and_infer():
    """
    Get moiety strings, parse, infer charges. Updates module state.
    Returns (disconnected_fragments, raw_disconnected, raw_connected).
    """
    global _current_fragments, _current_proposed, _current_needs_input, _current_connected
    raw_disconnected, raw_connected = _get_raw_moiety()

    fragments = parse_moiety_string(raw_disconnected)
    infer_charges(fragments, user_db.load())
    check_reasonableness(fragments)
    _current_fragments = fragments
    _current_connected = raw_connected or ''
    return fragments, raw_disconnected, raw_connected



def _update_cif(formula):
    """
    Write a moiety formula string directly to _chemical_formula_moiety in the CIF.
    No dialog — the GUI tab is the UI for user review and editing.
    """
    try:
        import olex
        olex.m("spy.set_cif_item(_chemical_formula_moiety,'%s')" % formula)
        print("  _chemical_formula_moiety updated:")
        print("  ", formula)
    except Exception as e:
        print(f"  (could not update CIF: {e})")


# ---------------------------------------------------------------------------
# Mask content helper (used by both _report and tab.py)
# ---------------------------------------------------------------------------

def _build_masked_frags():
    """
    Parse the current mask content into MoietyFragment objects.
    Returns (masked_frags, unknown_masked).
    Used by both the console report and the GUI tab.

    Note: mask content strings (e.g. "1440 H2O") are per-cell values.
    We divide multiplicities by the Z factor to get per-formula-unit.
    """
    mask = None
    try:
        mask = _get_mask_info()
    except Exception:
        pass

    masked_frags = []
    unknown_masked = False

    if mask:
        content_strs = [c for c in mask['content']
                       if c and c.strip() not in ('', '?', "''")]
        if content_strs:
            mask_formula_parts = []
            for entry in content_strs:
                entry = entry.strip().strip("'")
                for item in entry.split(','):
                    item = item.strip()
                    if not item or item == '?':
                        unknown_masked = True
                        continue
                    mask_formula_parts.append(item)
            for part in mask_formula_parts:
                parts = part.split()
                try:
                    n = float(parts[0])
                    name_or_formula = ' '.join(parts[1:])
                except (ValueError, IndexError):
                    n = 1
                    name_or_formula = part
                # Divide by Z to convert per-cell content to per-formula-unit
                z_factor = mask.get('factor', 1) if mask else 1
                n = n / z_factor if z_factor > 1 else n
                formula = _resolve_name(name_or_formula)
                if formula is None:
                    print(f"    (could not resolve mask content: {repr(name_or_formula)})")
                    unknown_masked = True
                    continue
                try:
                    frags_parsed = parse_moiety_string(formula)
                    for fp in frags_parsed:
                        fp.multiplicity = max(1, round(fp.multiplicity * n))
                        infer_charges([fp], user_db.load())
                        masked_frags.append(fp)
                except Exception:
                    unknown_masked = True
        else:
            unknown_masked = True

    return masked_frags, unknown_masked


# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------

def _report(force_input=False):
    force_input = str(force_input).lower() in ('true', '1', 'yes')
    """
    spy.gui.moiety.report()
    spy.gui.moiety.report(True)   <- force the edit box regardless of confidence

    Prints a human-readable charge inference + mask balance report.

    Shows:
      - Disconnected moiety (metals separated) with inferred charges
      - Charge balance summary
      - Solvent mask data (if present)
      - Proposed _chemical_formula_moiety (connected, with charges and mask)
    """
    # Cache check: if the connected formula hasn't changed, the structure
    # hasn't changed -- leave the tab state intact and exit silently.
    _, raw_connected_check = _get_raw_moiety()
    if raw_connected_check and raw_connected_check == _current_connected and not force_input:
        return

    fragments, raw_disconnected, raw_connected = _load_and_infer()

    if not fragments:
        print("No moiety formula available -- is a structure loaded?")
        return

    b = balance_summary(fragments)

    print()
    print("  --- Charge inference (metals disconnected) ---")
    print()
    print(f"  {'n':>4}  {'Formula':<28}  {'Charge':>8}  Confidence")
    print(f"  {'-'*4}  {'-'*28}  {'-'*8}  {'-'*24}")

    for f in fragments:
        charge_str, conf_str = _fmt_charge(f.charge, f.charge_confidence)
        mult_str = f"{f.multiplicity}" if f.multiplicity > 1 else ' '
        if f.charge_confidence == 'element_ambiguous':
            warn = '  <-- ambiguous!'
        elif f.charge_confidence == 'balance_suspect':
            reason = getattr(f, 'charge_suspect_reason', '')
            warn = f'  <-- SUSPECT: {reason}' if reason else '  <-- SUSPECT'
        elif f._occupancy < 1.0:
            warn = f'  <-- partial occupancy ({f._occupancy:.3f}) -- round in edit box'
        else:
            warn = ''
        frac = '  <-- fractional counts in source' if f._had_fractions else ''
        print(f"  {mult_str:>4}  {f.formula_string:<28}  {charge_str:>8}  {conf_str}{warn}{frac}")

    print()

    known_sum = b['known_sum']
    n_unknown = b['n_unknown']

    if b['balanced']:
        print("  Ordered model charge:  0  [OK]")
    elif n_unknown > 0:
        sign = '+' if known_sum > 0 else ''
        print(f"  Ordered model charge:  {sign}{known_sum}  ({n_unknown} fragment(s) with unknown charge)")
        if known_sum != 0:
            print()
            print("  *** Known fragments already sum to a non-zero charge. ***")
            mag = abs(known_sum)
            sign_str = '-' if known_sum > 0 else '+'
            print(f"  Unknown fragment(s) must carry {sign_str}{mag} collectively to balance.")
            print(f"  - If these are neutral solvents, something else is missing")
            _examples = {
                1: ('Cl-, Br-, BF4-, PF6-', 'Na+, NH4+'),
                2: ('2(Cl-) or SO4 2-', '2(Na+) or Ca 2+'),
                3: ('3(Cl-) or PO4 3-', '3(Na+) or Al 3+'),
                4: ('4(Cl-) or 2(SO4 2-)', '4(Na+) or 2(Ca 2+)'),
            }
            if mag in _examples:
                anion_ex, cation_ex = _examples[mag]
                ex = anion_ex if known_sum > 0 else cation_ex
                print(f"  - Possible missing ion(s): {ex}")
            # Suggest mixed-valence alternatives for ambiguous metals
            # target: ambiguous metals need to contribute (known_sum corrected)
            # Currently they contribute their guessed charge; what else could work?
            metal_current = sum(
                f.count * (f.charge or 0) for f in fragments
                if f.charge_confidence in ('element_ambiguous', 'element_guess')
            )
            nonmetal_sum = known_sum - metal_current
            target_metal = -nonmetal_sum
            mv_suggestions = suggest_mixed_valence(fragments, target_metal)
            if mv_suggestions:
                print()
                print("  Mixed-valence alternatives for ambiguous metal(s):")
                for s in mv_suggestions:
                    print(s)
            print("  - Has something been masked? Check the solvent mask.")
    else:
        sign = '+' if known_sum > 0 else ''
        print(f"  Ordered model charge:  {sign}{known_sum}  [!!]  NOT BALANCED")
        print()
        print("  *** The overall charge is not zero, which cannot be correct. ***")
        print("  Suggestions:")
        print("  - Check the oxidation state of each metal ion")
        print("  - Check the charge of each ligand and counter-ion")
        # Suggest what might balance it
        residual = known_sum
        if residual != 0:
            sign_str = '-' if residual > 0 else '+'
            mag = abs(residual)
            if mag == 1:
                print(f"  - Missing: 1 singly charged {sign_str}1 ion (e.g. {'Cl-, Br-, BF4-' if residual > 0 else 'Na+, NH4+'})")
            elif mag == 2:
                print(f"  - Missing: 2x {sign_str}1 or 1x {sign_str}2 ion (e.g. {'2(Cl-) or SO4 2-' if residual > 0 else '2(Na+) or Ca 2+'})")
            elif mag == 3:
                print(f"  - Missing: 3x {sign_str}1 or 1x {sign_str}3 ion (e.g. {'3(Cl-) or PO4 3-' if residual > 0 else '3(Na+) or Al 3+'})")
            else:
                print(f"  - Missing charge of {sign_str}{mag} to balance")
        print("  - Has something been masked? Check the solvent mask electron count.")

    # -------------------------------------------------------------------
    # Solvent mask section — entirely optional, fails gracefully
    # -------------------------------------------------------------------
    mask = None
    try:
        mask = _get_mask_info()
    except Exception as e:
        print(f"  (mask info unavailable: {e})")

    if mask:
        print()
        print("  Solvent mask:")
        print(f"    Program:    {mask['base'].replace('_', ' ')}")
        print(f"    Voids:      {mask['n_voids']}  (per formula unit, volumes >= 15 A^3)")
        print(f"    Volume:     {mask['total_volume']:.0f} A^3")
        print(f"    Electrons:  {mask['total_electrons']:.0f} e-")

        # What charge does the mask content need to carry?
        required_mask_charge = -known_sum
        if required_mask_charge == 0:
            print(f"    Required mask charge:  0  (ordered model is already balanced)")
        else:
            sign = '+' if required_mask_charge > 0 else ''
            print(f"    Required mask charge:  {sign}{required_mask_charge}  (to balance ordered model)")

        # Electron count sanity check against known mask content
        content_strs = [c for c in mask['content'] if c and c.strip() not in ('', '?', "''")]
        if content_strs:
            print(f"    Assigned content:  {', '.join(content_strs)}")
            # Try to count electrons from assigned content
            total_assigned_e = 0.0
            ok = True
            for entry in content_strs:
                entry = entry.strip().strip("'")
                for item in entry.split(','):
                    item = item.strip()
                    if not item or item == '?':
                        ok = False
                        continue
                    # item is like "2 water" or "dmf" or "1.5 H2O"
                    parts = item.split()
                    if len(parts) >= 2:
                        try:
                            n = float(parts[0])
                            formula = ' '.join(parts[1:])
                        except ValueError:
                            n = 1.0
                            formula = item
                    else:
                        n = 1.0
                        formula = item
                    n_e, _ = _electrons_from_formula(formula)
                    if n_e is not None:
                        total_assigned_e += n_e * n
                    else:
                        ok = False
            if ok and total_assigned_e > 0:
                diff = mask['total_electrons'] - total_assigned_e
                pct  = abs(diff) / mask['total_electrons'] * 100 if mask['total_electrons'] else 0
                sign = '+' if diff > 0 else ''
                status = '[OK]' if pct <= 10 else '[!!]'
                print(f"    Electrons accounted for: {total_assigned_e:.0f} e-  "
                      f"(diff: {sign}{diff:.0f}, {pct:.0f}%)  {status}")
        else:
            print(f"    Assigned content:  (none -- assign in mask GUI)")

            # Helpful hint: electron count / 10 gives approximate non-H atoms
            n_e = mask['total_electrons']
            print(f"    Hint: ~{n_e/10:.1f} non-H atoms  or  ~{n_e/18:.1f} x H2O")

    # Build masked fragment list for the proposed formula
    masked_frags, unknown_masked = _build_masked_frags()

    # ------------------------------------------------------------------
    # Best-guess formula: apply top mixed-valence suggestion if it helps
    # ------------------------------------------------------------------

    # Try to find the single best metal assignment
    best_fragments = list(fragments)  # shallow copy for best-guess
    metal_current = sum(
        f.count * (f.charge or 0) for f in best_fragments
        if f.charge_confidence in ('element_ambiguous', 'element_guess')
    )
    nonmetal_known = sum(
        f.count * (f.charge or 0) for f in best_fragments
        if f.charge_confidence not in ('element_ambiguous', 'element_guess', 'unknown')
        and f.charge is not None
    )
    target_metal = -nonmetal_known

    import copy
    best_fragments = copy.deepcopy(fragments)
    mv = suggest_mixed_valence(best_fragments, target_metal)

    import re as _re
    # Apply the top suggestion to best_fragments so the balance line and
    # proposed formula reflect the best metal guess.
    ambig_metals = [f for f in best_fragments
                   if f.charge_confidence in ('element_ambiguous', 'element_guess')
                   and len(f.elements) == 1]
    if len(ambig_metals) == 1 and mv:
        # Prefer mixed-valence suggestion over uniform
        mv_suggestions = [s for s in mv if 'Mixed valence' in s]
        top = mv_suggestions[0] if mv_suggestions else mv[0]
        f = ambig_metals[0]
        sym = next(iter(f.elements))

        if mv_suggestions:
            # Mixed valence: split the fragment into two rows
            # Parse e.g. "(Cu 2+), 2(Cu 1+)  [contribution: +4]"
            # Extract individual parts before [contribution]
            parts_str = top.split('[contribution')[0].replace('- Mixed valence: ','').strip()
            # Parse each part: optional N then (SYM Q+/-)
            split_frags = []
            for part in parts_str.split(', '):
                part = part.strip()
                pm = _re.match(r'(\d+)?\(?(\w+)\s+([+-]?\d+)([+-])\)?', part)
                if pm:
                    n_part = int(pm.group(1)) if pm.group(1) else 1
                    q = int(pm.group(3)) * (1 if pm.group(4)=='+' else -1)
                    new_f = copy.deepcopy(f)
                    new_f.multiplicity = n_part
                    new_f.charge = q
                    new_f.charge_confidence = 'balance'
                    split_frags.append(new_f)
            if split_frags:
                # Replace the original fragment with the split ones
                idx = best_fragments.index(f)
                best_fragments[idx:idx+1] = split_frags
        else:
            # Uniform: all same oxidation state
            m = _re.search(r'contribution: ([+-]\d+)', top)
            if m:
                contribution = int(m.group(1))
                n = f.multiplicity
                if n > 0 and contribution % n == 0:
                    f.charge = contribution // n
                    f.charge_confidence = 'balance'

    # Build balance equation line
    print()
    print("  --- Charge balance ---")
    print()
    parts = []
    for f in best_fragments:
        sym = f.formula_string
        if f.multiplicity > 1:
            sym = f"{f.multiplicity}({sym})"
        if f.charge is not None:
            parts.append(f"{sym} {_signed(f.charge)}")
        else:
            parts.append(f"{sym} ?")
    total_known = as_number(sum(f.count * (f.charge or 0) for f in best_fragments
                                if f.charge is not None))
    n_still_unknown = sum(1 for f in best_fragments if f.charge is None)
    balance_str = "0  [OK]" if (total_known == 0 and n_still_unknown == 0) else (
        f"{_signed(total_known)} + ? from {n_still_unknown} unknown(s)" if n_still_unknown
        else f"{_signed(total_known)}  [!!]"
    )
    print("  " + "  +  ".join(parts))
    charges = []
    for f in best_fragments:
        if f.charge is not None:
            total = as_number(f.count * f.charge)
            charges.append(_signed(total))
        else:
            charges.append("?")
    print("  " + "  +  ".join(charges) + f"  =  {balance_str}")
    print()

    # Build proposed formula using best_fragments (best metal guess, unknowns as None)
    proposed = format_moiety_string_with_mask(best_fragments, masked_frags, unknown_masked)

    print("  --- Proposed _chemical_formula_moiety ---")
    print()
    print("  ", proposed)
    if raw_connected and raw_connected != raw_disconnected:
        print()
        print("  Connected formula (no charges, for reference):")
        print("  ", raw_connected)
    print()

    # Decide whether user input is needed
    needs_input = (
        force_input
        or n_unknown > 0
        or unknown_masked
        or any(f.charge_confidence == 'element_ambiguous' for f in fragments)
        or any(f.charge_confidence == 'balance_suspect' for f in fragments)
        or any(f._occupancy < 1.0 for f in fragments)
        or (masked_frags and any(f._occupancy < 1.0 for f in masked_frags))
    )

    # Store state for apply_candidate() in the GUI tab
    _current_proposed = proposed
    _current_needs_input = needs_input


def _apply_if_needed():
    """
    spy.gui.moiety._apply_if_needed()

    Second half of the two-call button sequence:
        spy.gui.moiety._report() >> spy.gui.moiety._apply_if_needed()

    Pops the edit box if needed (ambiguous charges, unknowns, partial
    occupancy), then writes to the CIF. If no ambiguity, writes directly.

    Must be called after _report() — uses stored _current_proposed and
    _current_needs_input state.
    """
    if not _current_proposed:
        print("  No formula to apply -- run _report() first.")
        return
    _update_cif(_current_proposed)


def _apply(force_input=False):
    force_input = str(force_input).lower() in ('true', '1', 'yes')
    """
    spy.gui.moiety._apply()
    spy.gui.moiety._apply(True)   <- always pop the edit box

    Console convenience: runs _report() then _apply_if_needed() in one call.
    Use the >> chained button calls in the GUI instead, to guarantee that
    print output appears before the dialog.
    """
    _report(force_input=force_input)
    _apply_if_needed()


# ---------------------------------------------------------------------------
# JSON fragments — for GUI use later
# ---------------------------------------------------------------------------

def _fragments():
    """
    spy.gui.moiety.fragments()
    JSON fragment list for the GUI panel.
    """
    import json
    fragments, _, _ = _load_and_infer()
    result = [
        {
            'id':                i,
            'multiplicity':      f.multiplicity,
            'formula':           f.formula_string,
            'charge':            f.charge,
            'charge_confidence': f.charge_confidence,
            'had_fractions':     f._had_fractions,
        }
        for i, f in enumerate(fragments)
    ]
    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# Olex2 registration
# ---------------------------------------------------------------------------

try:
    from olexFunctions import OV
except ImportError:
    # Running outside Olex2 (e.g. unit tests) -- nothing to register.
    OV = None

if OV is not None:
    OV.registerFunction(_report,          False, 'gui.moiety')
    OV.registerFunction(_apply_if_needed, False, 'gui.moiety')
    OV.registerFunction(_apply,           False, 'gui.moiety')
    OV.registerFunction(_fragments,       False, 'gui.moiety')
    # Tab functions -- imported here to avoid circular import at module level
    from .tab import (show_tab, select_candidate, apply_candidate,
                      set_charge, clear_user_charges)
    OV.registerFunction(show_tab,         False, 'gui.moiety')
    OV.registerFunction(select_candidate,  False, 'gui.moiety')
    OV.registerFunction(apply_candidate,  False, 'gui.moiety')
    OV.registerFunction(set_charge,       False, 'gui.moiety')
    OV.registerFunction(clear_user_charges, False, 'gui.moiety')
