"""Tidy free variables: merge those that say the same thing, drop unused ones.

Two occupancy variables are the same when their values agree within TOL, or
when one is the other's complement (0.8 and 0.2: only the order of the parts
differs).  In a merge the lower number stays; a complement swaps the sign of
its references, so '81' becomes '-21' and '-81' becomes '21'.

Works on the text of a .res/.ins and imports nothing from Olex2.  A variable
used anywhere but in an occupancy (a coordinate, a U, DFIX, SUMP, AFIX ...) is
left alone and keeps its number.
"""
import collections
import math
import re

TOL = 0.03

# SHELXL instructions; anything else with enough numbers is an atom
KEYWORDS = set("""ABIN ACTA AFIX ANIS ANSC ANSR BASF BIND BLOC BOND BUMP CELL CGLS CHIV CONF
CONN DAMP DANG DEFS DELU DFIX DISP EADP END EQIV EXTI EXYZ FEND FLAT FMAP FRAG FREE FVAR GRID
HFIX HKLF HTAB ISOR LATT LAUE LIST L.S. MERG MOLE MORE MOVE MPLA NCSY NEUT OMIT PART PLAN PRIG
REM RESI RIGU RTAB SADI SAME SFAC SHEL SIMU SIZE SPEC STIR SUMP SWAT SYMM TEMP TITL TWIN TWST
UNIT WGHT WIGL WPDB XNPD ZERR""".split())
# instructions whose numbers may hold a free variable, and the first such number
# (AFIX 43 and HFIX 23 start with a code that only looks like one)
REFERENCING = {'DFIX': 1, 'DANG': 1, 'CHIV': 1, 'AFIX': 2, 'HFIX': 2}

Plan = collections.namedtuple('Plan', 'merges unused locked mapping values')


def decode(code):
  """(variable, p) of a SHELXL parameter code, or None if it uses no variable."""
  a = round(abs(code), 5)
  m = int(math.ceil((a - 5) / 10))
  if m < 2:
    return None
  return m, round(a - 10 * m, 5)


def encode(code, new, flip):
  """The code with its variable renumbered and, for a complement, its sign swapped."""
  _, p = decode(code)
  sign = 1 if code > 0 else -1
  return (-sign if flip else sign) * (10 * new + p)


def _oriented(numbers, values):
  """(lowest number, [(other number, is_complement), ...])."""
  keep = numbers[0]
  vk = values[keep]
  return keep, [(n, abs(values[n] - (1 - vk)) < abs(values[n] - vk)) for n in numbers[1:]]


def groups(values, tol=TOL):
  """Variables that say the same thing, from {number: value}:
  [(kept number, [(other number, is_complement), ...]), ...].  A group spans at
  most tol, so a long chain of near neighbours is not merged end to end."""
  items = sorted((min(v, 1 - v), n) for n, v in values.items() if 0 < v < 1)
  found, current = [], []

  def close():
    if len(current) > 1:
      found.append(_oriented(sorted(n for _, n in current), values))

  for folded, n in items:
    if current and folded - current[0][0] > tol:
      close()
      current = []
    current.append((folded, n))
  close()
  return sorted(found)


def _number(token):
  try:
    return float(token)
  except ValueError:
    return None


def _cards(lines):
  """Index lists of the physical lines of each card, up to HKLF or END."""
  cards, i = [], 0
  while i < len(lines):
    card = [i]
    while lines[i].rstrip().endswith('=') and i + 1 < len(lines):
      i += 1
      card.append(i)
    cards.append(card)
    word = lines[card[0]].split()[:1]
    if word and word[0].upper() in ('HKLF', 'END'):
      break
    i += 1
  return cards


def _tokens(lines, card):
  text = ' '.join(lines[i].rstrip().rstrip('=') for i in card)
  return text.split('!')[0].split()


def _is_atom(tokens):
  if len(tokens) < 6 or tokens[0].split('_')[0].upper() in KEYWORDS:
    return False
  return tokens[1].isdigit() and all(_number(t) is not None for t in tokens[2:6])


def _read(lines):
  """(values, variables used as occupancy, variables used otherwise)."""
  values, occupancy, other = {}, set(), set()
  number = 1

  def note(code, where):
    used = decode(code) if code is not None else None
    if used:
      where.add(used[0])

  for card in _cards(lines):
    tokens = _tokens(lines, card)
    if not tokens:
      continue
    word = tokens[0].split('_')[0].upper()
    if word == 'FVAR':
      for t in tokens[1:]:
        values[number] = float(t)
        number += 1
    elif word == 'PART':
      if len(tokens) > 2:
        note(_number(tokens[2]), occupancy)
    elif word == 'SUMP':
      for t in tokens[4::2]:
        other.add(int(float(t)))
    elif word in REFERENCING:
      for t in tokens[REFERENCING[word]:]:
        note(_number(t), other)
    elif _is_atom(tokens):
      note(float(tokens[5]), occupancy)
      for t in tokens[2:5] + tokens[6:]:
        note(_number(t), other)
  return values, occupancy, other


def _sorted_out(lines):
  """(all values, usable for merging, unused, used outside occupancies)."""
  values, occupancy, other = _read(lines)
  free = dict((n, v) for n, v in values.items() if n > 1)
  usable = dict((n, v) for n, v in free.items() if n in occupancy and n not in other)
  unused = sorted(n for n in free if n not in occupancy and n not in other)
  return values, usable, unused, sorted(other & set(free))


def plan(text, tol=TOL, include=None):
  """What needs doing to this .res text, or None if nothing does.  With include,
  a set of variable numbers, only those are merged: within each group the ones
  included merge with each other, and the rest stay as they are."""
  lines = text.splitlines(True)
  values, usable, unused, locked = _sorted_out(lines)
  free = dict((n, v) for n, v in values.items() if n > 1)
  found = groups(usable, tol)
  if include is not None:
    chosen = [[n for n in [keep] + [o for o, _ in others] if n in include]
              for keep, others in found]
    found = [_oriented(c, usable) for c in chosen if len(c) > 1]
  if not found and not unused:
    return None

  gone = dict((n, (keep, flip)) for keep, others in found for n, flip in others)
  merged = {}
  merges = []
  for keep, others in found:
    oriented = [free[keep]] + [1 - free[n] if flip else free[n] for n, flip in others]
    merged[keep] = sum(oriented) / len(oriented)
    merges.append((keep, others, merged[keep]))

  numbers = dict((n, n) for n in locked)
  taken, candidate = set(locked), 2
  for n in sorted(usable):
    if n in gone:
      continue
    while candidate in taken:
      candidate += 1
    numbers[n] = candidate
    taken.add(candidate)

  mapping = dict((n, (new, False)) for n, new in numbers.items())
  for n, (keep, flip) in gone.items():
    mapping[n] = (numbers[keep], flip)

  new_values = {1: values[1]}
  for n, new in numbers.items():
    new_values[new] = merged.get(n, free[n])
  last = max(new_values)
  return Plan(merges, unused, locked, mapping,
              [new_values.get(i, 0.5) for i in range(1, last + 1)])


def describe(p):
  """The plan in words, one line per change."""
  out = []
  for keep, others, value in p.merges:
    new = p.mapping[keep][0]
    parts = ['FV %d' % keep] + ['1 - FV %d' % n if flip else 'FV %d' % n for n, flip in others]
    out.append('%s are one variable: FV %d = %.3f' % (', '.join(parts), new, value))
  if p.unused:
    out.append('Not used by any atom, removed: %s' % ', '.join('FV %d' % n for n in p.unused))
  moved = [(n, new) for n, (new, _) in sorted(p.mapping.items())
           if n != new and n not in [o for _, others, _ in p.merges for o, _ in others]]
  if moved:
    out.append('Renumbered: %s' % ', '.join('FV %d to %d' % m for m in moved))
  if p.locked:
    out.append('Left alone, used outside occupancies: %s'
               % ', '.join('FV %d' % n for n in p.locked))
  return out


def locations(text):
  """{variable: {'residues', 'parts', 'atoms', 'first'}}: where each occupancy
  variable is used, to help decide whether two disorders belong together."""
  lines = text.splitlines(True)
  out = {}
  residue, part = '', '0'
  for card in _cards(lines):
    tokens = _tokens(lines, card)
    if not tokens:
      continue
    word = tokens[0].split('_')[0].upper()
    if word == 'RESI':
      residue = ' '.join(tokens[1:])
    elif word == 'PART':
      part = tokens[1] if len(tokens) > 1 else '0'
    elif _is_atom(tokens):
      used = decode(float(tokens[5]))
      if used:
        d = out.setdefault(used[0], {'residues': [], 'parts': [], 'atoms': 0, 'first': tokens[0]})
        d['atoms'] += 1
        if residue and residue not in d['residues']:
          d['residues'].append(residue)
        if part not in d['parts']:
          d['parts'].append(part)
  return out


def where(loc):
  """A location from locations() in words."""
  if not loc:
    return ''
  bits = []
  if loc['residues']:
    bits.append('%s %s' % ('residue' if len(loc['residues']) == 1 else 'residues',
                           ', '.join(loc['residues'])))
  bits.append('PART %s' % '/'.join(loc['parts']))
  bits.append('%d atoms from %s' % (loc['atoms'], loc['first']))
  return ', '.join(bits)


def tick_name(number):
  return 'FV_TICK_%d' % number


def choices(text, tol=TOL):
  """([(kept number, others), ...], unused numbers, values) for the dialog."""
  values, usable, unused, _ = _sorted_out(text.splitlines(True))
  return groups(usable, tol), unused, values


def page(text, form, p, tol=TOL):
  """The dialog: a tick for every variable that could be merged.  form is
  gui.db.form, passed in so that this module needs nothing from Olex2."""
  found, unused, values = choices(text, tol)
  places = locations(text)
  sections = []
  for i, (keep, others) in enumerate(found):
    rows = []
    for n in [keep] + [o for o, _ in others]:
      v = values[n]
      flipped = dict(others).get(n, False)
      shown = '%.3f' % v + (' &nbsp;(1 - %.3f)' % (1 - v) if flipped else '')
      rows.append(form.row(
        form.checkbox(tick_name(n), p, checked=True) + ' FV %d' % n,
        '%s &nbsp; <font color="%s">%s</font>' % (shown, p['muted'], where(places.get(n))),
        p, label_width='20%'))
    sections.append(form.section('Group %d' % (i + 1), rows, p) + form.spacer())
  body = ''.join(sections)
  if unused:
    body += form.section('Removed', [form.hint(
      'Not used by any atom: %s' % ', '.join('FV %d' % n for n in unused), p)], p) + form.spacer()
  body += form.buttons(
    [form.button('Cancel', 'spy.gui.sanitise_FVARs_close(False)', p)],
    [form.button('Merge ticked', 'spy.gui.sanitise_FVARs_close(True)', p, primary=True, width=120)])
  return form.page('Sanitise free variables', body, p, intro=(
    'Ticked variables in a group become one; a complement swaps the order of its parts. '
    'Similar values do not prove that two disorders are linked, so untick any that are '
    'independent. To merge a group as two separate pairs, tick one pair now and press '
    'Sanitise again for the other.'))


def _replace_token(line, index, new):
  spans = list(re.finditer(r'\S+', line))
  span = spans[index]
  return line[:span.start()] + new + line[span.end():]


def _fvar_lines(values, newline):
  rows = [values[i:i + 7] for i in range(0, len(values), 7)]
  return ['FVAR    ' + ''.join('%10.5f' % v for v in row) + newline for row in rows]


def apply(text, p):
  """The .res text with the plan carried out."""
  lines = text.splitlines(True)
  newline = '\r\n' if lines and lines[0].endswith('\r\n') else '\n'
  out = list(lines)
  fvar_done = False

  def remap(token):
    """The token with its variable replaced, or None if it stays as it is."""
    code = float(token)
    used = decode(code)
    if not used or used[0] not in p.mapping:
      return None
    new, flip = p.mapping[used[0]]
    changed = encode(code, new, flip)
    if changed == code:
      return None
    return '%.5f' % changed if '.' in token else '%g' % changed

  for card in _cards(lines):
    tokens = _tokens(lines, card)
    if not tokens:
      continue
    word = tokens[0].split('_')[0].upper()
    first = card[0]
    if word == 'FVAR':
      out[first] = '' if fvar_done else ''.join(_fvar_lines(p.values, newline))
      for i in card[1:]:
        out[i] = ''
      fvar_done = True
    elif word == 'PART' and len(tokens) > 2 and _number(tokens[2]) is not None:
      new = remap(tokens[2])
      if new:
        out[first] = _replace_token(lines[first], 2, new)
    elif word not in KEYWORDS and _is_atom(tokens):
      new = remap(tokens[5])
      if new:
        out[first] = _replace_token(lines[first], 5, new)
  return ''.join(out)
