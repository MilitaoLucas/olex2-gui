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

Tab structure:
    [ Section: Charge inference ]
      Colour-coded fragment table (charges editable -> confidence 'user')
      Balance equation

    [ Section: Suggested formulae ]
      Dropdown of candidates (most likely first)
      Working for selected candidate (updates on dropdown change)

    [ Apply button ]
      Writes selected formula to _chemical_formula_moiety in CIF
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------

def build_candidates(fragments, raw_connected=None, masked_frags=None, unknown_masked=False):
  """
  Build the ordered list of candidate moiety formulae from the
  inferred fragments and mixed-valence suggestions.

  Returns list of dicts:
      label    : human-readable label for the dropdown
      formula  : IUCr moiety string
      working  : HTML string showing the working for this candidate
      balanced : bool
  """
  from .parser import format_moiety_string_with_mask
  from .charges import balance_summary, suggest_mixed_valence, ELEMENT_CHARGES
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
  best = copy.deepcopy(fragments)
  ambig = [f for f in best
           if f.charge_confidence in ('element_ambiguous', 'element_guess')
           and len(f.elements) == 1]

  if len(ambig) == 1 and mv:
    mv_suggestions = [s for s in mv if 'Mixed valence' in s]
    top = mv_suggestions[0] if mv_suggestions else mv[0]
    f = ambig[0]
    if mv_suggestions:
      # Split into two rows
      parts_str = top.split('[contribution')[0].replace('- Mixed valence: ', '').strip()
      split_frags = []
      for part in parts_str.split(', '):
        part = part.strip()
        pm = re.match(r'(\d+)?\(?(\w+)\s+([+-]?\d+)([+-])\)?', part)
        if pm:
          n_part = int(pm.group(1)) if pm.group(1) else 1
          q = int(pm.group(3)) * (1 if pm.group(4) == '+' else -1)
          new_f = copy.deepcopy(f)
          new_f.multiplicity = n_part
          new_f.charge = q
          new_f.charge_confidence = 'balance'
          split_frags.append(new_f)
      if split_frags:
        idx = best.index(f)
        best[idx:idx+1] = split_frags
    else:
      m = re.search(r'contribution: ([+-]\d+)', top)
      if m:
        contribution = int(m.group(1))
        n = f.multiplicity
        if n > 0 and contribution % n == 0:
          f.charge = contribution // n
          f.charge_confidence = 'balance'

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

def _working_html(candidate: dict, colors: dict) -> str:
  """Generate the working section HTML for one candidate."""
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
  parts.append(he.charge_table(frag_dicts, colors,
                               edit_spy='spy.gui.moiety.set_charge'))
  if _user_charges:
    parts.append(
        "<a href='spy.gui.moiety.clear_user_charges()>>html.update()'>"
        "<font color='" + colors['secondary'] + "'>"
        "<small>Clear user-supplied charges</small></font></a>"
    )

  frag_eq = [{'mult': float(f.count), 'formula': f.formula_string, 'charge': f.charge}
             for f in frags]
  parts.append(he.balance_equation(frag_eq, colors))

  formula = candidate['formula']
  parts.append(
      "<br><font color='" + colors['secondary'] + "'><small>Formula:</small></font><br>"
      "<font color='" + colors['highlight'] + "'>" + formula + "</font>"
  )

  return '\n'.join(parts)


def _header_with_help(title, colors):
  """Section header with the 'i' button for this tool (help: moiety.help.md)."""
  try:
    from gui.htmltools import elements as he
  except ImportError:
    from htmltools import elements as he
  header = f"<font color='{colors['highlight']}' size='3'><b>{title}</b></font>"
  button = ("$spy.MakeHoverButton('btn-info@Moiety-Formula',"
            "\"spy.make_help_box -name='Moiety-Formula' -popout='False'\")")
  return he.tool_row_two_col(header, button, left_width='90%', right_width='10%')


def build_tab_html(fragments, raw_connected,
                   masked_frags=None, unknown_masked=False,
                   selected_idx: int = 0) -> str:
  """
  Build the complete moiety tab HTML content.
  Returns an HTML string ready to write to OlexFS.
  """
  try:
    from gui.htmltools import elements as he, page
  except ImportError:
    from htmltools import elements as he, page

  colors = he.get_colors()
  candidates = build_candidates(fragments, raw_connected, masked_frags, unknown_masked)

  # Only store candidates if this is a fresh build (not a dropdown change)
  # to avoid resetting _selected_idx back to 0
  if selected_idx == 0:
    _store_candidates(candidates)
  else:
    global _candidates
    _candidates = candidates

  pb = page.PageBuilder(font_step=_FONT_STEP)

  # --- Section: Connected formula for reference ---
  if raw_connected:
    sec = colors['secondary']
    pb.add(he.tool_row(
        f"<font color='{sec}'><small>Connected formula: {raw_connected}</small></font>"
    ))

  # --- Section: Candidate dropdown ---
  pb.add(_header_with_help('Suggested moiety formulae', colors))

  items = ';'.join(c['label'] for c in candidates)
  current = candidates[selected_idx]['label'] if candidates else ''

  pb.add(he.tool_row(
      he.dropdown(
          name='moiety_candidate',
          items_expr=items,
          value_expr=current,
          onchange=(
              'spy.gui.moiety.select_candidate(html.GetValue(~name~))'
              '>>html.update()'
          ),
      )
  ))

  # --- Section: Working for selected candidate ---
  pb.add(he.section_header('Working', colors))

  if candidates:
    working = _working_html(candidates[selected_idx], colors)
    pb.add(he.tool_row(working))
  else:
    pb.add(he.tool_row(
        f"<font color='{colors['error']}'>No formula available -- load a structure first.</font>"
    ))

  # --- Apply button ---
  pb.add(he.divider())
  pb.add(he.tool_row(
      he.action_button(
          name='moiety_apply',
          label='Apply to CIF',
          onclick='spy.gui.moiety.apply_candidate()>>html.update()',
          color=colors['green'],
          colors=colors,
      )
  ))

  global _cached_html
  _cached_html = pb.build()
  return _cached_html


# ---------------------------------------------------------------------------
# Module-level candidate state (persists within Olex2 session)
# ---------------------------------------------------------------------------

_FONT_STEP = 1       # text one size larger than the Olex2 default

_candidates = []
_selected_idx = 0
_cached_html = ''
_tab_connected = ''  # connected formula when tab was last built
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
    from gui.moiety import _get_raw_moiety
  except ImportError:
    from moiety import _get_raw_moiety

  raw_disconnected, raw_connected = _get_raw_moiety()
  if not raw_disconnected:
    _write_to_olexfs('moiety-content.htm', '<td>No structure loaded.</td>')
    return ''

  # If structure unchanged since last build, leave tab as-is
  # (preserves dropdown selection and user charges through GUI reloads)
  if raw_connected and raw_connected == _tab_connected:
    return ''

  # A different structure -- user charges belonged to the old one
  _user_charges.clear()
  _rebuild(raw_disconnected, raw_connected)
  return ''


def _rebuild(raw_disconnected, raw_connected, selected_idx: int = 0):
  """Parse, infer charges (honouring user charges), and rewrite the tab."""
  global _tab_connected, _selected_idx
  try:
    from gui.moiety.parser import parse_moiety_string
    from gui.moiety.charges import infer_charges, check_reasonableness
    from gui.moiety import _build_masked_frags, user_db
    from gui.htmltools import elements as he
  except ImportError:
    from moiety.parser import parse_moiety_string
    from moiety.charges import infer_charges, check_reasonableness
    from moiety import _build_masked_frags, user_db
    from htmltools import elements as he

  fragments = parse_moiety_string(raw_disconnected)
  # User charges go in first: infer_charges keeps charges that are
  # already set, and balance can then solve a remaining single unknown.
  for f in fragments:
    if f.formula_string in _user_charges:
      f.charge = _user_charges[f.formula_string]
      f.charge_confidence = 'user'
  infer_charges(fragments, user_db.load())
  check_reasonableness(fragments)

  masked_frags, unknown_masked = _build_masked_frags()

  html = build_tab_html(
      fragments, raw_connected,
      masked_frags=masked_frags,
      unknown_masked=unknown_masked,
  )
  # The candidate list may have shrunk (e.g. a user charge on a metal
  # removes the oxidation-state alternatives) -- keep selection if valid.
  if 0 < selected_idx < len(_candidates):
    _selected_idx = selected_idx
    html = _build_html_from_candidates(
        _candidates, raw_connected, _selected_idx, he.get_colors())
  _tab_connected = raw_connected or ''
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
    from gui.moiety import _get_raw_moiety
  except ImportError:
    from moiety import _get_raw_moiety
  raw_disconnected, raw_connected = _get_raw_moiety()
  if raw_disconnected:
    _rebuild(raw_disconnected, raw_connected, _selected_idx)


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
  print(f"[moiety.tab] Attempting to write {filename!r} ({len(content)} chars)")
  try:
    from olexFunctions import OV
    print(f"[moiety.tab] OV imported: {OV}")
    OV.write_to_olex(filename, content)
    print(f"[moiety.tab] Write succeeded")
  except Exception as e:
    import traceback
    print(f"[moiety.tab] Could not write {filename!r} to OlexFS: {e}")
    traceback.print_exc()




def _build_html_from_candidates(candidates, raw_connected, selected_idx, colors):
  """Build tab HTML from an existing candidate list without rebuilding candidates."""
  try:
    from gui.htmltools import elements as he, page
  except ImportError:
    from htmltools import elements as he, page

  pb = page.PageBuilder(font_step=_FONT_STEP)
  if raw_connected:
    sec = colors['secondary']
    pb.add(he.tool_row(
        f"<font color='{sec}'><small>Connected formula: {raw_connected}</small></font>"
    ))
  pb.add(_header_with_help('Suggested moiety formulae', colors))
  items = ';'.join(c['label'] for c in candidates)
  pb.add(he.tool_row(
      he.dropdown(
          name='moiety_candidate',
          items_expr=items,
          value_expr=candidates[selected_idx]['label'],
          onchange=(
              'spy.gui.moiety.select_candidate(html.GetValue(~name~))'
              '>>html.update()'
          ),
      )
  ))
  pb.add(he.section_header('Working', colors))
  pb.add(he.tool_row(_working_html(candidates[selected_idx], colors)))
  pb.add(he.divider())
  pb.add(he.tool_row(
      he.action_button(
          name='moiety_apply',
          label='Apply to CIF',
          onclick='spy.gui.moiety.apply_candidate()>>html.update()',
          color=colors['green'],
          colors=colors,
      )
  ))
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