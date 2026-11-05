"""
gui/moiety/tab.py

Moiety formula editor GUI tab.

Generates the dynamic HTML content for the moiety tab using
gui.htmltools primitives. Writes to OlexFS as 'moiety-content.htm'
which is #included by the static moiety_tab.htm skeleton.

Spy functions registered here:
    spy.gui.moiety.show_tab()              -- build and show the tab
    spy.gui.moiety.select_candidate(idx)   -- dropdown selection changed
    spy.gui.moiety.apply_candidate(idx)    -- Apply button clicked
    spy.gui.moiety.set_charge(row, value)  -- charge edited in the table
    spy.gui.moiety.clear_user_charges()    -- undo this session's charge edits

Charges typed into the table are also saved in the user charge table
(user_db.py), so the same fragment is recognised in later structures
('user lookup').

Tab structure, one table in the style of the Solvent Mask output:
    Dropdown of candidates (most likely first; includes the grown
      structure as displayed, if that gives a different formula)
    For the selected candidate (updates on dropdown change):
      Colour-coded fragment rows (charges editable -> confidence 'user')
      Balance equation
      The formula and the Apply button (writes it to
        _chemical_formula_moiety in CIF)
      The grown structure, if that is not the candidate selected
    Connected formula for reference
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------

def build_candidates(fragments, raw_connected=None, masked_frags=None,
                     unknown_masked=False, grown_frags=None):
  """
  Build the ordered list of candidate moiety formulae from the
  inferred fragments and mixed-valence suggestions.

  Returns list of dicts:
      label    : human-readable label for the dropdown
      formula  : IUCr moiety string
      working  : HTML string showing the working for this candidate
      balanced : bool

  grown_frags: fragments of the grown structure as displayed, if any. They
  take the charges of the best guess, and get a candidate of their own when
  their formula differs from it.
  """
  from .parser import format_moiety_string_with_mask, same_moiety
  from .charges import (balance_summary, best_guess, suggest_mixed_valence,
                        total_charge_text, copy_charges, ELEMENT_CHARGES)
  import copy, re

  candidates = []

  # --- Compute base values ---
  nonmetal_known = sum(
      f.count * (f.charge or 0) for f in fragments
      if f.charge_confidence not in ('element_ambiguous', 'element_guess', 'unknown')
      and f.charge is not None
  )
  target_metal = -nonmetal_known
  mv = suggest_mixed_valence(fragments, target_metal)

  # --- Candidate 1: best guess (mixed-valence applied if available) ---
  best = best_guess(fragments)

  b = balance_summary(best)
  best_formula = format_moiety_string_with_mask(best, masked_frags or [], unknown_masked)
  candidates.append({
      'label':    f"Best guess {'[balanced]' if b['balanced'] else '[check charges]'}",
      'formula':  best_formula,
      'frags':    best,
      'balanced': b['balanced'],
  })

  # --- Additional candidates: uniform oxidation states for ambiguous metals ---
  for mv_line in mv:
    if 'Mixed valence' in mv_line:
      continue   # already covered in best guess
    m = re.search(r'All (\d+)x (\w+) as ([+-]\d+)', mv_line)
    if not m:
      continue
    n, sym, q_str = int(m.group(1)), m.group(2), int(m.group(3))
    alt = copy.deepcopy(fragments)
    for f in alt:
      if f.formula_string == sym and f.charge_confidence in ('element_ambiguous', 'element_guess'):
        f.charge = q_str
        f.charge_confidence = 'balance'
    b_alt = balance_summary(alt)
    alt_formula = format_moiety_string_with_mask(alt, masked_frags or [], unknown_masked)
    candidates.append({
        'label':    f"All {n}x {sym} as {q_str:+d} {'[balanced]' if b_alt['balanced'] else '[unbalanced]'}",
        'formula':  alt_formula,
        'frags':    alt,
        'balanced': b_alt['balanced'],
    })

  # --- The grown structure, as displayed ---
  if grown_frags:
    copy_charges(grown_frags, best)
    grown_formula = format_moiety_string_with_mask(
        grown_frags, masked_frags or [], unknown_masked)
    if not same_moiety(grown_formula, best_formula):
      b_grown = balance_summary(grown_frags)
      candidates.append({
          'label':    f"Grown structure as displayed {'[balanced]' if b_grown['balanced'] else '[check charges]'}",
          'formula':  grown_formula,
          'frags':    grown_frags,
          'balanced': b_grown['balanced'],
          'note':     f"[Charge: {total_charge_text(grown_frags)}]",
      })

  # --- Always include: connected formula with no charges ---
  raw_frags = copy.deepcopy(fragments)
  for f in raw_frags:
    f.charge = None
  # Use raw_connected if available -- it's the whole-molecule formula
  no_charge = raw_connected if raw_connected else format_moiety_string_with_mask(raw_frags, masked_frags or [], unknown_masked)
  candidates.append({
      'label':   'No charges (use as-is)',
      'formula':  no_charge,
      'frags':    raw_frags,
      'balanced': False,
  })

  return candidates


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def _span_row(content, colors):
  """A row across the whole table of the tab."""
  try:
    from gui.htmltools import elements as he
  except ImportError:
    from htmltools import elements as he
  return he.span_row(content, colors, he.CHARGE_COLUMNS)


def _working_html(candidate: dict, colors: dict) -> str:
  """The table rows for one candidate: fragments, balance, formula."""
  try:
    from gui.htmltools import elements as he
  except ImportError:
    from htmltools import elements as he

  frags = candidate['frags']
  frag_dicts = [
      {
          'mult':       f.multiplicity,
          'formula':    f.formula_string,
          'charge':     f.charge,
          'confidence': f.charge_confidence,
          'warn':       getattr(f, 'charge_suspect_reason', ''),
          'occupancy':  f._occupancy,
      }
      for f in frags
  ]

  parts = []
  parts.append(he.charge_rows(frag_dicts, colors,
                              edit_spy='spy.gui.moiety.set_charge'))

  frag_eq = [{'mult': float(f.count), 'formula': f.formula_string, 'charge': f.charge}
             for f in frags]
  parts.append(_span_row(he.balance_equation(frag_eq, colors), colors))

  if _user_charges:
    parts.append(_span_row(
        "<a href='spy.gui.moiety.clear_user_charges()>>html.update()'>"
        "<font color='" + colors['secondary'] + "'>"
        "<small>Clear user-supplied charges</small></font></a>", colors))

  formula = candidate['formula']
  note = candidate.get('note')
  if note:
    formula += " " + note
  parts.append(_span_row(he.text_and_button(
      "<b>Formula:&nbsp;" + formula + "&nbsp;</b>",
      he.go_button(
          name='moiety_apply',
          label='Apply to CIF',
          onclick='spy.gui.moiety.apply_candidate()>>html.update()',
          td_width='22%',
      )), colors))

  # The grown structure stays in view, whichever candidate is selected
  grown = [c for c in _candidates if c.get('note')]
  if grown and grown[0] is not candidate:
    parts.append(_span_row(
        "<b>Grown structure as displayed:&nbsp;</b>"
        + grown[0]['formula'] + " " + grown[0]['note'], colors))

  return '\n'.join(parts)


def build_tab_html(fragments, raw_connected,
                   masked_frags=None, unknown_masked=False,
                   selected_idx: int = 0, grown_frags=None) -> str:
  """
  Build the complete moiety tab HTML content.
  Returns an HTML string ready to write to OlexFS.
  """
  try:
    from gui.htmltools import elements as he
  except ImportError:
    from htmltools import elements as he

  candidates = build_candidates(fragments, raw_connected, masked_frags,
                                unknown_masked, grown_frags)

  # Only store candidates if this is a fresh build (not a dropdown change)
  # to avoid resetting _selected_idx back to 0
  if selected_idx == 0:
    _store_candidates(candidates)
  else:
    global _candidates
    _candidates = candidates

  global _cached_html
  _cached_html = _build_html_from_candidates(
      candidates, raw_connected, selected_idx, he.get_colors())
  return _cached_html


# ---------------------------------------------------------------------------
# Module-level candidate state (persists within Olex2 session)
# ---------------------------------------------------------------------------

_FONT_STEP = 0       # the Olex2 default text size, as in the Solvent Mask table

_candidates = []
_selected_idx = 0
_cached_html = ''
_tab_connected = ''  # connected formula when tab was last built
_tab_grown = None    # grown structure's moiety string when tab was last built
_user_charges = {}   # formula_string -> charge supplied by the user


def _store_candidates(candidates):
  global _candidates, _selected_idx
  _candidates = candidates
  _selected_idx = 0


def get_candidates():
  return _candidates


def get_selected_idx():
  return _selected_idx


# ---------------------------------------------------------------------------
# Spy functions
# ---------------------------------------------------------------------------

def show_tab():
  """
  spy.gui.moiety.show_tab()

  Run inference and write the moiety tab HTML to OlexFS.
  Leaves the tab untouched if the structure hasn't changed.
  """
  try:
    from gui.moiety import _get_raw_moiety, _get_grown_moiety
  except ImportError:
    from moiety import _get_raw_moiety, _get_grown_moiety

  raw_disconnected, raw_connected = _get_raw_moiety()
  if not raw_disconnected:
    _write_to_olexfs('moiety-content.htm', '<td>No structure loaded.</td>')
    return ''

  # If structure unchanged since last build, leave tab as-is
  # (preserves dropdown selection and user charges through GUI reloads)
  grown_raw = _get_grown_moiety()
  same_structure = bool(raw_connected) and raw_connected == _tab_connected
  if same_structure and grown_raw == _tab_grown:
    return ''

  # A different structure -- user charges belonged to the old one
  if not same_structure:
    _user_charges.clear()
  _rebuild(raw_disconnected, raw_connected, grown_raw=grown_raw)
  return ''


def _rebuild(raw_disconnected, raw_connected, selected_idx: int = 0, grown_raw=None):
  """Parse, infer charges (honouring user charges), and rewrite the tab."""
  global _tab_connected, _tab_grown, _selected_idx
  try:
    from gui.moiety.charges import infer_charges, check_reasonableness
    from gui.moiety import _build_masked_frags, _parse_with_user_charges, user_db
    from gui.htmltools import elements as he
  except ImportError:
    from moiety.charges import infer_charges, check_reasonableness
    from moiety import _build_masked_frags, _parse_with_user_charges, user_db
    from htmltools import elements as he

  # User charges go in first: infer_charges keeps charges that are
  # already set, and balance can then solve a remaining single unknown.
  fragments = _parse_with_user_charges(raw_disconnected)
  infer_charges(fragments, user_db.load())
  check_reasonableness(fragments)
  # Nothing is inferred for the grown structure: build_candidates gives it the
  # charges determined above. Only a part of a fragment can need a user charge.
  grown_frags = _parse_with_user_charges(grown_raw) if grown_raw else None

  masked_frags, unknown_masked = _build_masked_frags()

  html = build_tab_html(
      fragments, raw_connected,
      masked_frags=masked_frags,
      unknown_masked=unknown_masked,
      grown_frags=grown_frags,
  )
  # The candidate list may have shrunk (e.g. a user charge on a metal
  # removes the oxidation-state alternatives) -- keep selection if valid.
  if 0 < selected_idx < len(_candidates):
    _selected_idx = selected_idx
    html = _build_html_from_candidates(
        _candidates, raw_connected, _selected_idx, he.get_colors())
  _tab_connected = raw_connected or ''
  _tab_grown = grown_raw
  _write_to_olexfs('moiety-content.htm', html)


def _parse_charge(text):
  """
  Parse a charge typed by the user: '2+', '+2', '2-', '-2', '2', '0', '+'.
  Returns int, or None for '' / '?' (meaning: drop the user charge).
  Raises ValueError for anything else.
  """
  t = str(text).strip().replace(' ', '')
  if t in ('', '?'):
    return None
  if t in ('+', '-'):
    return 1 if t == '+' else -1
  if t[-1] in '+-' and t[:-1].isdigit():
    n = int(t[:-1])
    return n if t[-1] == '+' else -n
  return int(t)


def _rebuild_current():
  try:
    from gui.moiety import _get_raw_moiety, _get_grown_moiety
  except ImportError:
    from moiety import _get_raw_moiety, _get_grown_moiety
  raw_disconnected, raw_connected = _get_raw_moiety()
  if raw_disconnected:
    _rebuild(raw_disconnected, raw_connected, _selected_idx,
             grown_raw=_get_grown_moiety())


def set_charge(row, value):
  """
  spy.gui.moiety.set_charge(row, value)

  Called when a charge is edited in the table. `row` indexes the
  fragment rows of the selected candidate. The charge is stored per
  formula, so it applies to every fragment with that formula, and is
  saved to the user charge table (not for single elements). '?' or an
  empty value removes the user charge, including the saved entry.
  """
  try:
    from gui.moiety import user_db
  except ImportError:
    from moiety import user_db

  if not _candidates:
    return ''
  frags = _candidates[_selected_idx]['frags']
  try:
    frag = frags[int(row)]
  except (ValueError, IndexError):
    print(f"[moiety] Invalid charge row: {row!r}")
    return ''
  try:
    charge = _parse_charge(value)
  except ValueError:
    print(f"[moiety] Could not read charge {value!r} for {frag.formula_string} "
          f"-- use e.g. 2+, -1 or 0 ('?' to reset)")
    return ''

  key = frag.formula_string
  if charge is None:
    if key not in _user_charges and frag.charge_confidence != 'user_lookup':
      return ''
    _user_charges.pop(key, None)
    user_db.forget(key)
  else:
    # Leaving the box unedited must not turn an inferred charge into 'user'
    if key not in _user_charges and charge == frag.charge:
      return ''
    if _user_charges.get(key) == charge:
      return ''
    _user_charges[key] = charge
    user_db.store(key, charge)
  _rebuild_current()
  return ''


def clear_user_charges():
  """
  spy.gui.moiety.clear_user_charges()

  Undo this session's charge edits: drop them and their saved entries.
  Entries saved for earlier structures stay in the user charge table.
  """
  try:
    from gui.moiety import user_db
  except ImportError:
    from moiety import user_db
  if _user_charges:
    for key in _user_charges:
      user_db.forget(key)
    _user_charges.clear()
    _rebuild_current()
  return ''


def _write_to_olexfs(filename: str, content: str) -> None:
  """Write HTML content to OlexFS."""
  try:
    from olexFunctions import OV
    OV.write_to_olex(filename, content)
  except Exception as e:
    import traceback
    print(f"[moiety] Could not write {filename!r} to OlexFS: {e}")
    traceback.print_exc()




def _build_html_from_candidates(candidates, raw_connected, selected_idx, colors):
  """Build tab HTML from an existing candidate list without rebuilding candidates."""
  try:
    from gui.htmltools import elements as he, page
  except ImportError:
    from htmltools import elements as he, page

  dropdown = he.dropdown(
      name='moiety_candidate',
      items_expr=';'.join(c['label'] for c in candidates),
      value_expr=candidates[selected_idx]['label'],
      onchange=(
          'spy.gui.moiety.select_candidate(html.GetValue(~name~))'
          '>>html.update()'
      ),
  )
  rows = [
      _span_row(he.side_by_side("<b>Suggested&nbsp;formula&nbsp;</b>", dropdown, '30%'), colors),
      _working_html(candidates[selected_idx], colors),
  ]
  if raw_connected:
    rows.append(_span_row(
        f"<font color='{colors['secondary']}'><small>"
        f"Connected formula: {raw_connected}</small></font>", colors))

  pb = page.PageBuilder(font_step=_FONT_STEP)
  pb.add(he.tool_row_help(he.framed_table('\n'.join(rows)), 'Moiety-Formula'))
  return pb.build()


def select_candidate(label: str):
  """
  spy.gui.moiety.select_candidate(label)

  Called when the dropdown changes. Updates _selected_idx and
  rewrites the working section.
  """
  global _selected_idx

  for i, c in enumerate(_candidates):
    if c['label'] == label:
      _selected_idx = i
      break

  if not _candidates:
    return

  # Use existing candidates -- do NOT rebuild, that resets _selected_idx to 0
  try:
    from gui.moiety import _get_raw_moiety
    from gui.htmltools import elements as he
  except ImportError:
    from moiety import _get_raw_moiety
    from htmltools import elements as he

  _, raw_connected = _get_raw_moiety()
  colors = he.get_colors()
  html = _build_html_from_candidates(_candidates, raw_connected, _selected_idx, colors)
  _write_to_olexfs('moiety-content.htm', html)
  return ''


def apply_candidate():
  """
  spy.gui.moiety.apply_candidate()

  Write the currently selected candidate formula to the CIF.
  """
  if not _candidates:
    print("[moiety] No candidates available -- run show_tab() first.")
    return

  formula = _candidates[_selected_idx]['formula']
  try:
    import olex
    olex.m("spy.set_cif_item(_chemical_formula_moiety,'%s')" % formula)
    print("  _chemical_formula_moiety updated:")
    print(" ", formula)
  except Exception as e:
    print(f"  (could not update CIF: {e})")