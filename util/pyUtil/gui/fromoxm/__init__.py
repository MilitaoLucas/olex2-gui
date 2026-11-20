"""spy.from_oxm(name[, part, part ...]): take things from a saved model (.oxm).

A picture made by hand (grown, planes, lines, style, view) and saved with
'save model Frag1b' can be repeated on any model of the same compound in the
same setting:

  spy.from_oxm(Frag1b)                  everything (= all)
  spy.from_oxm(Frag1b,grow)             the same atoms with the same symmetry
                                        operators, the same atoms hidden
  spy.from_oxm(Frag1b,grow,view)        ... and the same orientation, centre, zoom
  parts: grow, view, styles, planes, lines, all

  styles  the colours saved with the model (atoms, bonds, planes, lines), set
          live on the same objects here; the style is never reloaded, so the
          atoms' draw style (ellipsoids) and the scene's colours stay
  planes  'mpln' on the same atoms, with their names when every plane has one
  lines   'line' with the same names; an end that sat on an atom sits on the
          same atom (and symmetry operator) of this model
  labels  not possible yet: Olex2 has no command to place a label where it
          was dragged ('load model' does it, but only for the very same file)

Atoms are matched by POSITION, not by name: an atom of this model is the
sample's atom when it is on that atom's place or a symmetry equivalent of it,
within a margin (0.5 A; 'margin=0.3' to change), and of the same element.  An
atom held at another equivalent position is moved there first (sgen -m).
Atoms that carry other names than in the sample are listed, and Olex2 asks
whether to take the sample's names; options:

  names      take the sample's names without asking (alone: only that)
  keepnames  never ask
  keepstyle  keep the colours of the style in use (no 'styles', also not with all)
  bylabel    match by label instead of by position (as before 2026-11-14)
  margin=x   the margin in Angstrom

The name is looked up next to the structure (.oxm added); a full path works too.
"""
import os

from ._core import (DEFAULT_MARGIN, PARTS, SampleError, cell_differences, commands,
                    match_atoms, parse, positions_after, read_model, rename_commands,
                    renamed)

OPTIONS = ('names', 'keepnames', 'bylabel', 'keepstyle')


def _path(name):
  from olexFunctions import OV
  name = str(name or '').strip().strip('"\'')
  if not name:
    return None
  if not name.lower().endswith('.oxm'):
    name += '.oxm'
  if os.path.isabs(name):
    return name
  return os.path.join(OV.FilePath() or '', name)


def _atoms():
  """[(label, fractional, type)] of the asymmetric unit now, Q-peaks left out."""
  import olx
  out = []
  for i in range(int(olx.xf.au.GetAtomCount())):
    t = str(olx.xf.au.GetAtomType(i))
    if t.upper() == 'Q':
      continue
    crd = tuple(float(v) for v in str(olx.xf.au.GetAtomCrd(i)).replace(',', ' ').split())
    out.append((str(olx.xf.au.GetAtomName(i)), crd, t))
  return out


def _cell():
  import olx
  out = {}
  for k in ('a', 'b', 'c', 'alpha', 'beta', 'gamma'):
    out[k] = float(str(olx.xf.uc.CellEx(k)).split('(')[0])
  return out


def _arguments(args):
  """(parts, options, margin) from the spy arguments."""
  asked, margin = set(), DEFAULT_MARGIN
  for a in args:
    for p in str(a).replace('|', ',').split(','):
      p = p.strip().lower()
      if p.startswith('margin='):
        try:
          margin = float(p.split('=', 1)[1])
        except ValueError:
          print("from_oxm: '%s' is not a margin in Angstrom; %.2f used" % (p, margin))
      elif p:
        asked.add(p)
  options = asked & set(OPTIONS)
  asked -= options
  if 'style' in asked:
    asked.add('styles')
  if 'labels' in asked:
    print("from_oxm: labels cannot be placed by command yet (no Olex2 command for a "
          "dragged label); left out")
  unknown = asked - set(PARTS) - {'style', 'labels', 'all'}
  if unknown:
    print("from_oxm: unknown part(s) %s; use %s or all"
          % (', '.join(sorted(unknown)), ', '.join(PARTS)))
  if 'all' in asked or not (asked - {'labels'}):
    parts = set() if (not asked and options == {'names'}) else set(PARTS)
  else:
    parts = asked & set(PARTS)
  if 'keepstyle' in options:
    parts.discard('styles')  # the colours of the style in use stay
  return parts, options, margin


def _live_entries():
  """{(entry name, primitive)} of the style Olex2 shows now (saved to a
  temporary file and read; saving does not change anything), or None."""
  import olex
  import tempfile
  from ._core import style_materials
  live = os.path.join(tempfile.gettempdir(),
                      'olex2_from_oxm_%d.glds' % os.getpid()).replace('\\', '/')
  try:
    if os.path.isfile(live):
      os.remove(live)
    olex.m('save style "%s"' % live)
    if not os.path.isfile(live):
      return None
    with open(live, encoding='utf-8-sig', errors='replace') as f:
      return set((n, p) for n, p, _ in style_materials(f.read()))
  except (OSError, ValueError, AttributeError) as err:
    print("from_oxm: could not read Olex2's style: %s" % err)
    return None
  finally:
    if os.path.isfile(live):
      os.remove(live)


def _apply_materials(sample_style, oxm_name):
  """The sample's colours on what exists here, live ('SetMaterial'): the style
  is never reloaded, so the draw style of the atoms (ellipsoids ...) and
  everything else stays.  Entries this model has no object or style for are
  reported (their shape, e.g. a line's PMask, cannot be set this way)."""
  import olex
  from ._core import style_materials
  wanted = style_materials(sample_style)
  live = _live_entries()
  if live is None:
    print("from_oxm: Olex2 did not save its style; colours not taken")
    return
  done, absent = 0, set()
  for name, pname, mat in wanted:
    if (name, pname) in live:
      olex.m('SetMaterial "%s.%s" %s' % (name, pname, mat))
      done += 1
    else:
      absent.add(name)
  print("from_oxm: %d colours taken from %s" % (done, oxm_name))
  if absent:
    print("from_oxm: no such object here, colours not taken: %s"
          % ' '.join(sorted(absent)))


def _ask_names(todo, oxm_name):
  """Ask whether the sample's names are to be used.  True for yes."""
  import olx
  shown = ', '.join('%s -> %s' % p for p in todo[:12])
  if len(todo) > 12:
    shown += ', ... (%d more)' % (len(todo) - 12)
  msg = ("%d atoms have other names here than in %s:\n%s\n\n"
         "Use the names from the oxm file?" % (len(todo), oxm_name, shown))
  try:
    return olx.Alert("Names from %s" % oxm_name, msg, "YN", False) == 'Y'
  except Exception as err:
    print("from_oxm: could not ask (%s); names kept, use the part 'names'" % err)
    return False


def from_oxm(name='', *args):
  """spy.from_oxm(name[, part ...]): see the module text."""
  import olex
  from olexFunctions import OV
  path = _path(name)
  if not path:
    print("Usage: spy.from_oxm(name[, %s|all][, names|keepnames|bylabel|margin=0.5])"
          % '|'.join(PARTS))
    return
  if not os.path.isfile(path):
    print("from_oxm: no file %s" % path)
    return
  parts, options, margin = _arguments(args)
  try:
    sample = parse(read_model(path))
  except (SampleError, OSError, ValueError) as err:
    print("from_oxm: %s" % err)
    return
  try:
    cell = _cell()
    diffs = cell_differences(sample['cell'], cell)
    atoms = _atoms()
  except (ValueError, AttributeError) as err:
    print("from_oxm: could not read the model now: %s" % err)
    return
  if diffs:
    print("from_oxm: the cell differs from the sample's (%s); going on anyway"
          % ', '.join(diffs))
  oxm_name = os.path.basename(path)

  # which atom is which: by position (default) or by label
  pairs = None
  if 'bylabel' not in options:
    pairs, lost, extra = match_atoms(sample, atoms, cell, margin)
    moved = [c for c, move, _ in pairs.values() if move]
    print("from_oxm: %d of %d atoms of %s found here by position (margin %.2f A)%s"
          % (len(pairs), len(sample['au']), oxm_name, margin,
             '; %d at another equivalent position, moved' % len(moved) if moved else ''))
    if lost:
      print("from_oxm: not found here: %s" % ' '.join(lost))
    todo = renamed(pairs)
    if todo:
      use = 'names' in options or (
        'keepnames' not in options and _ask_names(todo, oxm_name))
      if use:
        cmds = rename_commands(pairs, [a[0] for a in atoms])
        for c in cmds:
          olex.m(c)
        print("from_oxm: %d atoms renamed as in %s" % (len(todo), oxm_name))
        # the model's atoms now carry the sample's names
        pairs = dict((s, (s, move, d)) for s, (_, move, d) in pairs.items())
        atoms = _atoms()
      else:
        print("from_oxm: %d atoms keep their own names (%s); "
              "spy.from_oxm(%s,names) takes the sample's"
              % (len(todo), ', '.join('%s=%s' % (c, s) for c, s in todo[:6]) +
                 (' ...' if len(todo) > 6 else ''), os.path.splitext(oxm_name)[0]))
  if not parts:
    return

  current = None
  if 'lines' in parts and sample.get('lines'):
    if pairs is not None:
      current = positions_after(pairs, atoms)
    else:
      current = dict((l.upper(), f) for l, f, _ in atoms)
  # everything but the style first: the planes and lines it may colour must exist
  cmds, missing = commands(sample, [a[0] for a in atoms], parts - {'styles'},
                           current=current, current_cell=cell, pairs=pairs)
  if missing and pairs is None:
    print("from_oxm: not in this model, left out: %s" % ' '.join(missing))
  olex.m('freeze true')
  try:
    for c in cmds:
      olex.m(c)
    if 'styles' in parts and sample.get('style'):
      _apply_materials(sample['style'], oxm_name)
  finally:
    olex.m('freeze false')
  print("from_oxm: %s: %s" % (oxm_name, ', '.join(p for p in PARTS if p in parts)))


# --- the panel (View > Symmetry Generation > Experimental Growing) --------------
# Settings in user.fromoxm: file, parts, names (ask|names|keepnames), margin.

def choose():
  """spy.gui.fromoxm.choose(): pick the saved model with a file dialog."""
  import gui
  import olx
  from olexFunctions import OV
  start = os.path.dirname(OV.GetParam('user.fromoxm.file', '') or '') or OV.FilePath()
  f = gui.FileOpen('Saved model to take the picture from', '*.oxm', start)
  if f and str(f) != 'None' and os.path.isfile(str(f)):
    OV.SetParam('user.fromoxm.file', str(f))
    olx.html.Update()


def run(names_only=''):
  """spy.gui.fromoxm.run([names]): from_oxm with the panel's settings; 'names'
  only gives the atoms the sample's names."""
  from olexFunctions import OV
  path = OV.GetParam('user.fromoxm.file', '') or ''
  if not path:
    print("Experimental Growing: choose a saved model (.oxm) first")
    return
  args = []
  if str(names_only).lower() in ('names', 'true', '1'):
    args.append('names')
  else:
    args.append(str(OV.GetParam('user.fromoxm.parts', 'all') or 'all'))
    names = str(OV.GetParam('user.fromoxm.names', 'ask') or 'ask')
    if names in ('names', 'keepnames'):
      args.append(names)
    if str(OV.GetParam('user.fromoxm.style', 'oxm') or 'oxm') == 'current':
      args.append('keepstyle')
  margin = OV.GetParam('user.fromoxm.margin', DEFAULT_MARGIN)
  args.append('margin=%s' % (margin or DEFAULT_MARGIN))
  from_oxm(path, *args)


def file_label():
  """The chosen file's name for the panel, or a hint."""
  from olexFunctions import OV
  path = OV.GetParam('user.fromoxm.file', '') or ''
  return os.path.basename(path) if path else 'none chosen'


try:
  from olexFunctions import OV
  OV.registerFunction(from_oxm, False)
  OV.registerFunction(choose, False, 'gui.fromoxm')
  OV.registerFunction(run, False, 'gui.fromoxm')
  OV.registerFunction(file_label, False, 'gui.fromoxm')
except ImportError:
  pass
