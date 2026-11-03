"""
gui/proto/proto.py

Proto: a library of solved structures that can 'solve' new data sets.

When a structure is finished, add it to the library; a later data set of
the same compound (same lattice) can then be solved straight from the
library instead of running a solution program.

The library is  DataDir()/gui/proto/proto.sqlite  (param proto.library).
It always exists -- it is created, empty, when this module is loaded.
Further databases listed in proto.extra_dbs are searched as well but
never written to.

Functions
---------
    spy.proto.add([comment], [class], [name])
                              add the loaded (refined) structure to the library
    spy.proto.find()          list library structures matching the loaded data
    spy.proto.apply([N])      use match N (default 1) of the last find as the solution
    spy.proto.solve()         find, and apply the best match
    spy.proto.library()       list everything in the library
    spy.proto.remove(ID)      remove library entry ID
    spy.proto.check()         number of applicable matches (for the GUI)

Matching compares reduced (Niggli) cells, so a match is found whatever
setting the data are in. Kinds of match:
    same      same space group and setting -- the model is used as stored
    setting   same space group in another setting/axis choice -- the model
              is transformed into the current setting (transform.py)
    other     same lattice, different space group -- listed, not applicable

The functions in the "AC7 compatibility" section keep the original API
used by AC7's sponge module (database from proto.db_location/db_name).
"""

import os
import re
import sys

import olex
import olx
from olexFunctions import OV

from . import db
from . import cells
from . import transform

_KIND_ORDER = {'same': 0, 'setting': 1, 'other': 2}

p_path = os.path.dirname(os.path.abspath(__file__))

_last_matches = []   # result of the last find(), for apply(N)
_applied_file = None  # file loaded by the last apply() -- switching between
                      # proto hits there needs no 'replace atoms?' prompt


def _deal_with_phil(operation='read'):
  user_phil_file = os.path.join(OV.DataDir(), "proto_user.phil")
  phil_file = os.path.join(p_path, "proto.phil")
  if operation == "read":
    phil = open(phil_file, 'r').read()
    olx.phil_handler.adopt_phil(phil_string=phil)
    if os.path.exists(user_phil_file):
      olx.phil_handler.update(phil_file=user_phil_file)
  elif operation == "save":
    phil_files = [user_phil_file]
    for phil in phil_files:
      olx.phil_handler.save_param_file(
        file_name=phil, scope_name='proto', diff_only=True)


def _resolve_path(p):
  """Expand a leading 'DataDir()' / 'BaseDir()' in a path param."""
  p = str(p).strip()
  m = re.match(r'^(\w+)\(\)[/\\]?(.*)$', p)
  if m:
    base = getattr(OV, m.group(1))()
    p = os.path.join(base, m.group(2))
  return os.path.normpath(p)


def library_path():
  return _resolve_path(OV.GetParam('proto.library'))


def _sources():
  """[(label, path, writable)] -- the library first, then extra_dbs."""
  out = [('library', library_path(), True)]
  extra = OV.GetParam('proto.extra_dbs') or ''
  for p in str(extra).split(';'):
    if p.strip():
      path = _resolve_path(p)
      out.append((os.path.splitext(os.path.basename(path))[0], path, False))
  return out


def ensure_library():
  """Create the (empty) library if it doesn't exist yet."""
  path = library_path()
  try:
    con = db.connect(path, create=True)
    con.close()
  except Exception as e:
    print("proto: could not create the structure library %s: %s" % (path, e))
    if hasattr(sys, '_wing_debugger'):
      raise


# ---------------------------------------------------------------------------
# The loaded structure
# ---------------------------------------------------------------------------

def _current():
  """Cell, space group, formula and reduced cell of the loaded structure."""
  cell = tuple(float(x) for x in olx.xf.au.GetCell().split(','))
  sg = olx.xf.au.GetCellSymm()
  return {
    'cell': cell,
    'space_group': sg,
    'formula': olx.xf.au.GetFormula(),
    'volume': float(olx.xf.au.GetCellVolume()),
    'reduced': cells.reduced_cell(cell, sg),
    'p_volume': cells.primitive_volume(cell, sg),
  }


def _model_file():
  """The file holding the current model: the loaded res/ins, else name.res."""
  f = OV.FileFull()
  if os.path.splitext(f)[1].lower() in ('.res', '.ins'):
    return f
  f = os.path.join(OV.FilePath(), OV.FileName() + '.res')
  return f if os.path.exists(f) else None


def _elements(formula):
  return set(re.findall(r'[A-Z][a-z]?', formula or ''))


def _float_or_none(v):
  try:
    return float(v)
  except (TypeError, ValueError):
    return None


# ---------------------------------------------------------------------------
# Library operations
# ---------------------------------------------------------------------------

def add(comment='', p_class='', name=''):
  """Add the loaded structure to the library."""
  model_file = _model_file()
  if not model_file:
    print("proto: no res/ins file for the loaded structure -- nothing added.")
    return None
  with open(model_file, 'r') as fh:
    model = fh.read()

  path = library_path()
  con = db.connect(path, create=True)
  try:
    h = db.model_hash(model)
    dup = db.find_by_hash(con, h)
    if dup:
      print("proto: this model is already in the library (#%s, %s)." % (dup['id'], dup['name']))
      return dup['id']

    cur = _current()
    entry = {
      'name': name or OV.FileName(),
      'path': model_file,
      'formula': cur['formula'],
      'space_group': cur['space_group'],
      'cell_volume': cur['volume'],
      'class': p_class or None,
      'comment': comment or None,
      'r1': _float_or_none(OV.GetParam('snum.refinement.last_R1')),
      'ins': model,
      'hash': h,
    }
    entry.update(zip(db.CELL_KEYS, cur['cell']))
    entry.update(zip(db.RED_KEYS, cur['reduced']))
    new_id = db.add(con, entry)
  finally:
    con.close()
  print("proto: added %s (%s, %s) to the library as #%s." % (
    entry['name'], entry['space_group'], entry['formula'], new_id))
  return new_id


def find():
  """spy.proto.find() -- print the library structures matching the loaded data."""
  _find()
  return ''


def _find(verbose=True):
  """
  Search all sources for structures matching the loaded data.
  Returns the matches, best first; also kept for apply(N).
  """
  global _last_matches
  cur = _current()
  rel_tol = float(OV.GetParam('proto.length_tolerance')) / 100
  angle_tol = float(OV.GetParam('proto.angle_tolerance'))
  cur_elements = _elements(cur['formula'])

  matches = []
  for label, path, writable in _sources():
    con = db.connect(path, create=writable)
    if con is None:
      print("proto: database not found: %s" % path)
      continue
    try:
      # volume window: 3x the length tolerance covers the volume change
      for e in db.entries(con, cur['p_volume'], 3 * rel_tol):
        try:
          m = cells.compare(cur, e, rel_tol, angle_tol)
        except (RuntimeError, ValueError) as ex:
          print("proto: skipping %s #%s (%s): %s" % (label, e['id'], e['name'], ex))
          continue
        if not m:
          continue
        if m['kind'] == 'setting':
          m['op'] = _setting_op(cur, e, rel_tol, angle_tol)
          if m['op'] is None:
            m['kind'] = 'other'
        if writable and e['red_a'] is None:
          db.set_reduced_cell(con, e['id'], m['reduced'])
        el = _elements(e['formula'])
        union = cur_elements | el
        m.update(e)
        m['source'] = label
        m['source_path'] = path
        m['element_match'] = len(cur_elements & el) / len(union) if union else 0.0
        matches.append(m)
    finally:
      con.close()

  matches.sort(key=lambda m: (_KIND_ORDER[m['kind']], -m['element_match'],
                              m['dl'] + m['da'] / 100))
  _last_matches = matches
  if verbose:
    _print_matches(cur, matches)
  return matches


def _print_matches(cur, matches):
  print("proto: %s  %s  (reduced %s)" % (
    cur['space_group'],
    ' '.join('%.3f' % x for x in cur['cell'][:3]) + ' ' +
    ' '.join('%.2f' % x for x in cur['cell'][3:]),
    ' '.join('%.2f' % x for x in cur['reduced'])))
  if not matches:
    print("  no matching structure in the library.")
    return
  print("  %-3s %-8s %-10s %-14s %-6s %-6s %s" % (
    '#', 'match', 'SG', 'cell dev', 'elem', 'R1', 'name  [source]  comment'))
  for i, m in enumerate(matches, 1):
    r1 = '%.2f%%' % (m['r1'] * 100 if m['r1'] < 1 else m['r1']) if m['r1'] is not None else '-'
    print("  %-3i %-8s %-10s %-14s %-6s %-6s %s  [%s]  %s" % (
      i, m['kind'], m['space_group'],
      '%.1f%% %.1f deg' % (m['dl'] * 100, m['da']),
      '%.0f%%' % (m['element_match'] * 100), r1,
      m['name'], m['source'], m['comment'] or ''))
  if matches[0]['kind'] in ('same', 'setting'):
    print("  spy.proto.apply(1) uses #1 as the solution.")
  else:
    print("  These have the same lattice but a different space group -- "
          "none can be applied.")


def _entry_cell(e):
  return tuple(e[k] for k in db.CELL_KEYS)


def _setting_op(cur, e, rel_tol, angle_tol):
  """Change-of-basis operator stored setting -> current, or None."""
  try:
    return cells.setting_transform(cur['cell'], cur['space_group'],
                                   _entry_cell(e), e['space_group'],
                                   rel_tol, angle_tol)
  except (RuntimeError, ValueError) as ex:
    print("proto: no setting transformation for #%s (%s): %s" % (e['id'], e['name'], ex))
    return None


def check():
  """Number of directly applicable library matches (for the GUI)."""
  try:
    return sum(1 for m in _find(verbose=False) if m['kind'] in ('same', 'setting'))
  except Exception as e:
    print("proto: library check failed: %s" % e)
    if hasattr(sys, '_wing_debugger'):
      raise
    return 0


def _current_instructions():
  """
  {KEY: [lines]} for TITL, CELL, ZERR, HKLF (first line each) and the
  symmetry (all LATT and SYMM lines, under 'SYMM') of the loaded res/ins;
  empty if a cif (or nothing) is loaded.
  """
  cur_file = OV.FileFull()
  out = {}
  if os.path.splitext(cur_file)[1].lower() not in ('.res', '.ins') or not os.path.exists(cur_file):
    return out
  with open(cur_file, 'r') as fh:
    for line in fh:
      line = line.rstrip('\r\n')
      key = line[:4].upper()
      if key in ('TITL', 'CELL', 'ZERR', 'HKLF') and key not in out:
        out[key] = [line]
      elif key in ('LATT', 'SYMM'):
        out.setdefault('SYMM', []).append(line)
  return out


def _model_for_setting(model, m):
  """
  The stored model transformed into the current setting, with the loaded
  file's TITL, CELL, ZERR, symmetry and HKLF. None if that's not possible.
  """
  cur = _current_instructions()
  if 'CELL' not in cur:
    print("proto: a res/ins file must be loaded to use a match in another setting.")
    return None
  cur.setdefault('SYMM', [])   # P-1 without LATT: no symmetry lines at all
  r9, t = cells.operator_parts(m['op'])
  new_cell = tuple(float(x) for x in olx.xf.au.GetCell().split(','))
  print("proto: transforming #%s from %s into the current setting (%s)." % (
    m['id'], m['space_group'], m['op'].as_xyz()))
  return transform.transform_model(model, r9, t, _entry_cell(m), new_cell, replace=cur)


def _model_for_current(model):
  """
  The stored model with the loaded file's TITL, CELL, ZERR and HKLF lines,
  so it refers to the current data.
  """
  keep = {k: v[0] for k, v in _current_instructions().items() if k != 'SYMM'}
  out = []
  for line in model.splitlines():
    key = line[:4].upper()
    if key in keep:
      line = keep[key]
    elif key == 'CELL':
      # no CELL in the loaded file (e.g. a cif): the current cell with
      # the stored wavelength
      wl = line.split()[1] if len(line.split()) > 1 else '0.71073'
      line = 'CELL %s %s' % (wl, ' '.join(olx.xf.au.GetCell().split(',')))
    out.append(line)
  return '\n'.join(out) + '\n'


def apply(n=1):
  """Use match n (1-based) of the last find() as the solution."""
  global _applied_file
  try:
    n = int(n)
  except ValueError:
    print("proto: spy.proto.apply(N) needs a match number, got %r." % n)
    return False
  if not _last_matches:
    print("proto: no matches -- run spy.proto.find() first.")
    return False
  if not 1 <= n <= len(_last_matches):
    print("proto: there are only %i matches." % len(_last_matches))
    return False
  m = _last_matches[n - 1]
  if m['kind'] == 'other':
    print("proto: #%i (%s) is in a different space group (%s) -- "
          "it can't be applied." % (n, m['name'], m['space_group']))
    return False

  if int(olx.xf.au.GetAtomCount()) and OV.HasGUI() and OV.FileFull() != _applied_file:
    if olx.Alert("Proto", "The current structure already has atoms.\n"
                 "Replace them with the library model %s?" % m['name'],
                 "YN", False) != 'Y':
      return False

  con = db.connect(m['source_path'])
  if con is None:
    print("proto: database not found: %s" % m['source_path'])
    return False
  try:
    model = db.get_model(con, m['id'])
  finally:
    con.close()
  if m['kind'] == 'setting':
    text = _model_for_setting(model, m)
    if text is None:
      return False
  else:
    text = _model_for_current(model)
  _load_solution(text)
  _applied_file = OV.FileFull()
  print("proto: solved from %s #%s (%s)." % (m['source'], m['id'], m['name']))
  _print_alternatives(n)
  return True


def _print_alternatives(n):
  """After applying match n: how to use the other applicable matches."""
  others = [(i, m) for i, m in enumerate(_last_matches, 1)
            if i != n and m['kind'] in ('same', 'setting')]
  if not others:
    return
  print("proto: other matches -- each is applied as a new solution in the history:")
  for i, m in others:
    print("  spy.proto.apply(%i)  %-8s %s  %s" % (i, m['kind'], m['name'], m['comment'] or ''))


def _load_solution(text):
  """Load `text` as name.res and record it as a solution in the history."""
  path, name = OV.FilePath(), OV.FileName()
  hkl_src = OV.HKLSrc()
  with open(os.path.join(path, name + '.res'), 'w') as fh:
    fh.write(text)
  OV.reloadStructureAtreap(path, name, update_gui=False)
  if hkl_src:
    OV.HKLSrc(hkl_src)
  OV.SetParam('snum.refinement.last_R1', 'Solution')
  OV.SetParam('snum.refinement.last_wR2', 'Solution')
  from History import hist
  hist.create_history(solution=True)
  if OV.HasGUI():
    OV.UpdateHtml()


def solve():
  """Find and apply the best match. Returns True if a model was applied."""
  matches = _find()
  if matches and matches[0]['kind'] in ('same', 'setting'):
    return apply(1)
  return False


def library():
  """List everything in the library."""
  path = library_path()
  con = db.connect(path, create=True)
  try:
    rows = db.entries(con)
  finally:
    con.close()
  print("proto library: %s  (%i structures)" % (path, len(rows)))
  for e in rows:
    print("  #%-4s %-10s %-24s %s  %s" % (
      e['id'], e['space_group'], e['formula'], e['name'], e['comment'] or ''))
  return ''


def remove(entry_id):
  con = db.connect(library_path(), create=True)
  try:
    ok = db.remove(con, entry_id)
  finally:
    con.close()
  print("proto: %s #%s." % ('removed' if ok else 'there is no entry', entry_id))
  return ok


# ---------------------------------------------------------------------------
# AC7 compatibility (sponge): original API, database from db_location/db_name
# ---------------------------------------------------------------------------

def db_connect():
  db_path = os.path.join(_resolve_path(OV.GetParam('proto.db_location', None)),
                         OV.GetParam('proto.db_name', None))
  con = db.connect(db_path)
  if con is None:
    print("There is no proto db at %s" % db_path)
    return None
  print("Connected to %s." % db_path)
  return con


def cp(number):
  number = int(number)
  cmd = "split -r=SAME -p1=%i -p2=%i -s1=A -s2=B" % (number, number + 1)
  olex.m(cmd)


def cleanup_proto_disorder(min_occu=0.03):
  import gui
  cmd = "sel atoms where occu < %s" % min_occu
  olex.m(cmd)
  cmd = "sel"
  atoms = []
  _ = gui.tools.scrub(cmd)[1:]
  for item in _:
    if not item:
      continue
    if "Angle" in item:
      item = item.split("Angle")[0]
    if item:
      atoms.extend(item.split())

  olex.m("kill %s" % " ".join(atoms))

  atoms = [w.replace('B', 'C') for w in atoms]
  atoms = [w.replace('A', 'B') for w in atoms]
  atoms = [w.replace('C', 'A') for w in atoms]

  olex.m("sel %s" % " ".join(atoms))
  olex.m("PART 0 11")


def solve_with_proto(new_ins, sg=None):
  """Replace the loaded ins by `new_ins` (keeping CELL/ZERR) and load it."""
  ins_fn = OV.FileFull()
  with open(ins_fn, 'r') as fh:
    ins = fh.readlines()
  CELL = ZERR = None
  for line in ins:
    if line.startswith("CELL"):
      CELL = line.rstrip('\r\n')
    elif line.startswith("ZERR"):
      ZERR = line.rstrip('\r\n')
    if CELL and ZERR:
      break
  t = ""
  for line in new_ins.split("\n"):
    if line.startswith("CELL") and CELL:
      line = CELL
    elif line.startswith("ZERR") and ZERR:
      line = ZERR
    t += line + "\n"
  with open(ins_fn, 'w') as fh:
    fh.write(t)
  print("< Switching to %s >" % ins_fn)
  olx.Atreap(ins_fn)


def find_in_proto(volume=None, tol=None, group=None, sg=None):
  if not volume:
    volume = olx.xf.au.GetCellVolume()
  formula = olx.xf.au.GetFormula()
  space_group = olx.xf.au.GetCellSymm()

  if not tol:
    tol = OV.GetParam('proto.tolerance')
  if not group:
    group = OV.GetParam('proto.class')
    if not group:
      group = "auto"
    if group == "auto":
      if "I" in formula:
        group = "ZnI"
      elif "Br" in formula:
        group = "ZnBr"
      elif "Cl" in formula:
        group = "ZnCl"
      else:
        group = ""
    elif group == "any":
      group = ""

  if not sg:
    sg = OV.GetParam('proto.sg')
    if not sg:
      sg = "auto"
    if sg == "auto":
      sg = space_group
    elif sg == "any":
      sg = ""

  retVal = []
  con = db_connect()
  if con is None:
    return retVal
  tol_abs = int(float(volume) * int(tol) / 100)
  sql = "SELECT id, name, ins, space_group, class, cell_volume FROM proto " \
        "WHERE abs(cell_volume-?) <= ?"
  args = [float(volume), tol_abs]
  if group:
    sql += " AND class = ?"
    args.append(group)
  if sg:
    sql += " AND space_group = ?"
    args.append(sg)
  try:
    res = con.execute(sql, args).fetchall()
  finally:
    con.close()
  print("= PROTO with Class: %s, SG: %s, V: %.1f (+/- %s%%) ================" % (group, sg, float(volume), tol))
  if res:
    for r in res:
      msg = "%s | %s | %.0f A^3: %s" % (r[3], r[4], r[5], r[1])
      print(msg)
      retVal.append((r[2], msg, sg))
  else:
    print("Nothing found in proto!")
  print("= END PROTO ================\n")
  return retVal


def add_to_proto(p_class):
  """AC7: add the loaded structure to the db_location/db_name database."""
  db_path = os.path.join(_resolve_path(OV.GetParam('proto.db_location', None)),
                         OV.GetParam('proto.db_name', None))
  model_file = os.path.join(OV.FilePath(), OV.FileName() + ".ins")
  with open(model_file, 'r') as fh:
    model = fh.read()
  cur = _current()
  entry = {
    'name': OV.FileName(),
    'path': model_file,
    'formula': cur['formula'],
    'space_group': cur['space_group'],
    'cell_volume': cur['volume'],
    'class': p_class,
    'ins': model,
  }
  entry.update(zip(db.CELL_KEYS, cur['cell']))
  entry.update(zip(db.RED_KEYS, cur['reduced']))
  con = db.connect(db_path, create=True)
  try:
    db.add(con, entry)
  finally:
    con.close()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_deal_with_phil("read")
ensure_library()

OV.registerFunction(add, False, 'proto')
OV.registerFunction(check, False, 'proto')
OV.registerFunction(find, False, 'proto')
OV.registerFunction(apply, False, 'proto')
OV.registerFunction(solve, False, 'proto')
OV.registerFunction(library, False, 'proto')
OV.registerFunction(remove, False, 'proto')

OV.registerFunction(cp, False, 'proto')
OV.registerFunction(add_to_proto, False, 'proto')
OV.registerFunction(find_in_proto, False, 'proto')
OV.registerFunction(solve_with_proto, False, 'proto')
OV.registerFunction(cleanup_proto_disorder, False, 'proto')
