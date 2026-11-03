"""
twin_details.py

Describe a twin law as a rotation, for the CIF item _twin_special_details:

  Twin law (TWIN 0 0 1 0 -1 0 1 0 0 2): component 2 rotated by 180\\%
  around [0.71 0.00 0.71] (reciprocal) or [0.71 0.00 0.71] (direct).

(\\% is the CIF code for the degree sign; the metacif only takes ASCII.)

The TWIN matrix M acts on the indices of component 1 to give those of the
other component. With B the reciprocal orthogonalisation matrix of the
cell, R = B M B^-1 is the same operation in Cartesian space; its angle
comes from the trace, its axis from the eigenvector with eigenvalue 1,
expressed in reciprocal (A^T x) and direct (A^-1 x) lattice coordinates.
For a pseudo-merohedral twin R is not exactly orthogonal, so the nearest
rotation (polar decomposition) is used.

HKLF 5 data (non-merohedral twins) have no TWIN matrix. There, overlapping
reflections are written as groups -- one line per component, component
number = |batch|, negative batch numbers for all but the last line -- so
each group containing components 1 and k gives a pair (h1, hk) with
hk ~ g M_k h1, g any Laue symmetry operator (programs list the other
component's indices as arbitrary equivalents). M_k is fitted over all
pairs and described in the same way. Indices of a non-merohedral
component are rounded to integers in the file, so the fitted law is an
average, not exact.

Limitation: a small-angle non-merohedral twin (a few degrees, as found by
data reduction) cannot be described from HKLF 5 data -- only reflections
whose indices coincide overlap, so the indices say "identity" and the
angle comes only from the orientation matrices. Such laws (< MIN_ANGLE)
are not reported.

The pure functions need no Olex2; update_metacif() is the Olex2 hook,
called from CifInfo.MergeCif before the metacif is written.
"""

import math
import os

PREFIX = "Twin law ("        # every generated text starts with this
CIF_KEY = '_twin_special_details'


# ---------------------------------------------------------------------------
# 3x3 helpers (lists of rows)
# ---------------------------------------------------------------------------

def _mul(a, b):
  return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _t(a):
  return [[a[j][i] for j in range(3)] for i in range(3)]


def _det(m):
  return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
          - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
          + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def _inv(m):
  d = _det(m)
  return [[(m[(j + 1) % 3][(i + 1) % 3] * m[(j + 2) % 3][(i + 2) % 3]
            - m[(j + 1) % 3][(i + 2) % 3] * m[(j + 2) % 3][(i + 1) % 3]) / d
           for j in range(3)] for i in range(3)]


def _apply(m, v):
  return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def orthogonalisation(cell):
  """A: columns are a, b, c in Cartesian coordinates (a along x)."""
  a, b, c = cell[:3]
  al, be, ga = (math.radians(x) for x in cell[3:])
  ax = [a, 0.0, 0.0]
  bx = [b * math.cos(ga), b * math.sin(ga), 0.0]
  cx = c * math.cos(be)
  cy = c * (math.cos(al) - math.cos(be) * math.cos(ga)) / math.sin(ga)
  cz = math.sqrt(max(c * c - cx * cx - cy * cy, 0.0))
  return _t([ax, bx, [cx, cy, cz]])


def nearest_rotation(m, iterations=50):
  """Orthogonal polar factor of m: Q <- (Q + Q^-T) / 2 until converged."""
  q = [row[:] for row in m]
  for _ in range(iterations):
    qn = [[(q[i][j] + x) / 2 for j, x in enumerate(row)] for i, row in enumerate(_t(_inv(q)))]
    if max(abs(qn[i][j] - q[i][j]) for i in range(3) for j in range(3)) < 1e-14:
      return qn
    q = qn
  return q


def _unit(v):
  n = math.sqrt(sum(x * x for x in v))
  v = [x / n for x in v]
  # deterministic sign: first non-negligible component positive
  for x in v:
    if abs(x) > 1e-6:
      return v if x > 0 else [-y for y in v]
  return v


def rotation_of(matrix, cell):
  """
  (angle in degrees, reciprocal axis, direct axis, proper) for the twin
  matrix acting on hkl. proper is False when det(M) < 0: the rotation is
  then that of -M, i.e. the law is a rotation combined with inversion.
  """
  A = orthogonalisation(cell)
  B = _t(_inv(A))
  r = _mul(_mul(B, matrix), _inv(B))
  q = nearest_rotation(r)
  proper = _det(q) > 0
  if not proper:
    q = [[-x for x in row] for row in q]
  cos_t = max(-1.0, min(1.0, (q[0][0] + q[1][1] + q[2][2] - 1) / 2))
  angle = math.degrees(math.acos(cos_t))
  if angle < 1e-6:
    return 0.0, None, None, proper
  if angle > 179.9:
    # sin ~ 0: the axis is the largest column of (Q + I)
    cols = [[q[i][j] + (1 if i == j else 0) for i in range(3)] for j in range(3)]
    axis = max(cols, key=lambda v: sum(x * x for x in v))
  else:
    axis = [q[2][1] - q[1][2], q[0][2] - q[2][0], q[1][0] - q[0][1]]
  return angle, _unit(_apply(_t(A), axis)), _unit(_apply(_inv(A), axis)), proper


def parse_twin(twin_args):
  """'0 0 1 0 -1 0 1 0 0 2' -> (3x3 matrix, n). n defaults to 2."""
  tok = [float(x) for x in str(twin_args).split()]
  if len(tok) < 9:
    raise ValueError("TWIN needs 9 matrix elements, got %r" % twin_args)
  m = [tok[0:3], tok[3:6], tok[6:9]]
  n = int(tok[9]) if len(tok) > 9 else 2
  return m, n


def _fmt_vec(v):
  return ' '.join('%.2f' % (0.0 if abs(x) < 0.005 else x) for x in v)


def _fmt_angle(angle):
  """Whole degrees when within 0.05 deg of an integer, else one decimal."""
  if abs(angle - round(angle)) < 0.05:
    return '%i' % round(angle)
  return '%.1f' % angle


def _is_inversion(m):
  return all(abs(m[i][j] - (-1 if i == j else 0)) < 1e-6 for i in range(3) for j in range(3))


def _component_phrase(comp, matrix, cell):
  angle, recip, direct, proper = rotation_of(matrix, cell)
  if recip is None:
    return "component %i is identical to component 1" % comp
  s = "component %i rotated by %s\\%% around [%s] (reciprocal) or [%s] (direct)" % (
    comp, _fmt_angle(angle), _fmt_vec(recip), _fmt_vec(direct))
  if not proper:
    s += ", combined with inversion"
  return s


def describe(twin_args, cell):
  """
  Text for _twin_special_details from the TWIN arguments and the cell, or
  None for a pure inversion twin (already reported as such by olex2.refine).
  """
  m, n = parse_twin(twin_args)
  if _is_inversion(m):
    return None
  card = ' '.join(('%g' % x) for row in m for x in row) + ' %i' % n
  parts = []
  power = m
  n_rot = abs(n) // 2 if n < 0 else abs(n)   # TWIN -N: N/2 laws + inversion partners
  for comp in range(2, max(n_rot, 2) + 1):
    parts.append(_component_phrase(comp, power, cell))
    power = _mul(power, m)
  text = "%sTWIN %s): %s." % (PREFIX, card, "; ".join(parts))
  if n < 0:
    text += " Each component is also present as its inversion partner."
  return text


# ---------------------------------------------------------------------------
# HKLF 5
# ---------------------------------------------------------------------------

def _hkl_line(line):
  """(h, k, l, batch) of an HKLF 5 line, or None (fixed 3I4,2F8,I4 format)."""
  try:
    h, k, l = int(line[0:4]), int(line[4:8]), int(line[8:12])
    batch = int(line[28:32]) if len(line) >= 29 and line[28:32].strip() else 1
  except ValueError:
    tok = line.split()
    if len(tok) < 6:
      return None
    try:
      h, k, l, batch = int(tok[0]), int(tok[1]), int(tok[2]), int(tok[5])
    except ValueError:
      return None
  return h, k, l, batch


def overlap_groups(lines):
  """
  Yield {component: (h, k, l)} for each overlap group (two or more lines)
  of an HKLF 5 file, up to the 0 0 0 terminator.
  """
  group = {}
  for line in lines:
    r = _hkl_line(line)
    if r is None:
      continue
    h, k, l, batch = r
    if (h, k, l) == (0, 0, 0):
      break
    group[abs(batch)] = (h, k, l)
    if batch > 0:
      if len(group) > 1:
        yield group
      group = {}


IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
FRIEDEL = (IDENTITY, ((-1, 0, 0), (0, -1, 0), (0, 0, -1)))
MAX_RMS = 0.5       # index residual above which a fitted law is not trusted
MIN_ANGLE = 0.5     # deg: smaller rotations can't be determined from indices


def with_friedel(ops):
  """ops (3x3 nested tuples) closed under -1: intensities always obey it."""
  out = [tuple(tuple(x for x in row) for row in g) for g in ops]
  for g in list(out):
    neg = tuple(tuple(-x for x in row) for row in g)
    if neg not in out:
      out.append(neg)
  return out


def _solve3(h1s, hks):
  """M with M h1_i = hk_i for three independent h1 (columns)."""
  a = _t([list(map(float, h)) for h in h1s])
  b = _t([list(map(float, h)) for h in hks])
  return _mul(b, _inv(a))


def _dist2(m, h1, hk):
  p = _apply(m, h1)
  return sum((x - y) ** 2 for x, y in zip(p, hk))


def _best_equivalent(m, h1, hk, ops):
  """The symmetry equivalent g hk closest to M h1, and its squared distance."""
  best = None
  for g in ops:
    e = _apply(g, hk)
    d = _dist2(m, h1, e)
    if best is None or d < best[1]:
      best = (e, d)
  return best


def _independent_triple(pairs):
  """Three pairs whose h1 are as independent as possible (greedy)."""
  p0 = pairs[0]
  def cross(u, v):
    return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
  p1 = max(pairs, key=lambda p: sum(x * x for x in cross(p0[0], p[0])))
  c = cross(p0[0], p1[0])
  p2 = max(pairs, key=lambda p: abs(sum(x * y for x, y in zip(c, p[0]))))
  if abs(_det([p0[0], p1[0], p2[0]])) < 1e-9:
    return None
  return p0, p1, p2


def _fit_one(pairs, ops):
  """
  Fit M with h_k ~ g M h_1, g from ops chosen per pair. The indices of the
  other component may be listed as any symmetry equivalent, so:
    1. try every choice of g on three independent pairs and solve exactly;
       keep the M that explains a sample of all pairs best;
    2. give each pair its best g for that M and refit by least squares.
  Returns (M, rms) or None.
  """
  sample = pairs[::max(1, len(pairs) // 40)]
  triple = _independent_triple(sample)
  if triple is None:
    return None
  search_ops = ops if len(ops) ** 3 <= 4096 else FRIEDEL
  best = None
  for g0 in search_ops:
    for g1 in search_ops:
      for g2 in search_ops:
        try:
          m = _solve3([p[0] for p in triple],
                      [_apply(g, p[1]) for g, p in zip((g0, g1, g2), triple)])
        except ZeroDivisionError:
          continue
        err = sum(_best_equivalent(m, h1, hk, ops)[1] for h1, hk in sample)
        if best is None or err < best[1]:
          best = (m, err)
        if best[1] < 1e-9:      # exact (merohedral) law: no need to go on
          break
      if best is not None and best[1] < 1e-9:
        break
    if best is not None and best[1] < 1e-9:
      break
  if best is None:
    return None
  m = best[0]
  for _ in range(2):
    xy = [[0.0] * 3 for _ in range(3)]
    xx = [[0.0] * 3 for _ in range(3)]
    for h1, hk in pairs:
      e = _best_equivalent(m, h1, hk, ops)[0]
      for i in range(3):
        for j in range(3):
          xy[i][j] += e[i] * h1[j]
          xx[i][j] += h1[i] * h1[j]
    m = _mul(xy, _inv(xx))
  sq = sum(_best_equivalent(m, h1, hk, ops)[1] for h1, hk in pairs)
  return m, math.sqrt(sq / len(pairs))


def canonical_law(m, cell, ops):
  """
  Among the equivalent laws g M (g in ops), the most natural description
  of the same twin: a twofold rotation if there is one (the usual way of
  stating a (pseudo-)merohedral twin law), otherwise the proper rotation
  with the smallest angle (e.g. a few degrees for a non-merohedral twin).
  """
  best = None
  for g in ops:
    gm = _mul([list(r) for r in g], m)
    if _det(gm) < 0:
      continue
    angle = rotation_of(gm, cell)[0]
    score = (0 if abs(angle - 180) < 0.5 else 1, angle)
    if best is None or score < best[1]:
      best = (gm, score)
  return best[0] if best else m


def _smallest_angle(m, cell, ops):
  """Smallest rotation angle among the proper equivalents g M."""
  angles = [rotation_of(gm, cell)[0] for gm in
            (_mul([list(r) for r in g], m) for g in ops) if _det(gm) > 0]
  return min(angles) if angles else 180.0


def fit_laws(groups, transform=None, laue_ops=None):
  """
  {component k: (M_k, number of pairs, rms index residual)} from the overlap
  groups, with h_k ~ M_k h_1 up to the Laue symmetry `laue_ops` (3x3
  integer matrices acting on hkl as columns; default: Friedel only).
  `transform` is the HKLF matrix (3x3, rows), applied to every index first.
  """
  ops = with_friedel(laue_ops or FRIEDEL)
  per_comp = {}
  for g in groups:
    if 1 not in g:
      continue
    h1 = list(g[1])
    if transform:
      h1 = _apply(transform, h1)
    for comp, hk in g.items():
      if comp == 1:
        continue
      hk = list(hk)
      if transform:
        hk = _apply(transform, hk)
      per_comp.setdefault(comp, []).append((h1, hk))
  laws = {}
  for comp, pairs in per_comp.items():
    if len(pairs) < 3:
      continue
    fit = _fit_one(pairs, ops)
    if fit is not None:
      laws[comp] = (fit[0], len(pairs), fit[1])
  return laws


def describe_hklf5(laws, cell, laue_ops=None):
  """
  Text for _twin_special_details from fit_laws() results, or None if there
  is no law or one doesn't fit the data well enough to be reported.
  """
  if not laws:
    return None
  bad = [comp for comp in laws if laws[comp][2] > MAX_RMS]
  if bad:
    print("Twin law of component(s) %s does not fit the HKLF 5 overlaps "
          "(rms index residual %s) -- _twin_special_details not generated." % (
            ', '.join(map(str, bad)), ', '.join('%.2f' % laws[c][2] for c in bad)))
    return None
  ops = with_friedel(laue_ops or FRIEDEL)
  canon = {comp: canonical_law(laws[comp][0], cell, ops) for comp in laws}
  # a law equal (within MIN_ANGLE) to a symmetry operator of the crystal
  # carries no twin information -- check every equivalent, not just the
  # one chosen for the description
  small = [comp for comp in laws if _smallest_angle(laws[comp][0], cell, ops) < MIN_ANGLE]
  if small:
    print("Twin law of component(s) %s is a rotation of less than %s deg -- it "
          "can't be determined from HKLF 5 indices (only coinciding reflections "
          "overlap); take it from the data reduction. _twin_special_details "
          "not generated." % (', '.join(map(str, small)), MIN_ANGLE))
    return None
  parts = [_component_phrase(comp, canon[comp], cell) for comp in sorted(laws)]
  n = sum(laws[comp][1] for comp in laws)
  return "%sHKLF 5, derived from %i overlapping reflections): %s." % (
    PREFIX, n, "; ".join(parts))


_hklf5_cache = {}   # (path, mtime, size, hklf args, cell) -> text


def describe_hklf5_file(path, cell, hklf_args='', laue_ops=None):
  """describe_hklf5() for an HKLF 5 file; cached until the file changes."""
  st = os.stat(path)
  key = (path, st.st_mtime, st.st_size, hklf_args, tuple(cell),
         tuple(map(tuple, laue_ops or ())))
  if key not in _hklf5_cache:
    tok = str(hklf_args).split()
    transform = None
    if len(tok) >= 11:            # HKLF 5 s r11 ... r33
      v = [float(x) for x in tok[2:11]]
      transform = [v[0:3], v[3:6], v[6:9]]
    with open(path) as fh:
      laws = fit_laws(overlap_groups(fh), transform, laue_ops)
    _hklf5_cache.clear()
    _hklf5_cache[key] = describe_hklf5(laws, cell, laue_ops)
  return _hklf5_cache[key]


# ---------------------------------------------------------------------------
# Olex2 hook
# ---------------------------------------------------------------------------

def laue_ops_for(space_group):
  """Laue group rotations of `space_group` acting on hkl as columns (cctbx)."""
  from cctbx import sgtbx
  laue = sgtbx.space_group_info(str(space_group)).group().build_derived_laue_group()
  ops = []
  # smx() leaves out the inversion half of a centric group unless asked --
  # without -1 the description can't pick a proper rotation (2026-10-01:
  # a real HKLF 5 law came out "..., combined with inversion")
  for smx in laue.smx(with_inversion=laue.is_centric()):
    den = smx.r().den()
    r = [x // den for x in smx.r().num()]   # acts on coordinates; on hkl (h' = h R) -> R^T
    ops.append(((r[0], r[3], r[6]), (r[1], r[4], r[7]), (r[2], r[5], r[8])))
  return with_friedel(ops)    # a Laue group always contains -1


def twinning_from_model(rm):
  """
  (twin_args, hklf_args) from Olex2's refinement model
  (OV.GetRefinementModel(False)). TWIN and HKLF are parsed into the model,
  not kept as plain instructions -- olx.Ins('TWIN') does not return them.
    twin_args : 'm11 ... m33 n' (TWIN card form) or None
    hklf_args : 'code 1 r11 ... r33' (HKLF card form, scale 1) or ''
  """
  twin_args = None
  twin = rm.get('twin')
  if twin and twin.get('matrix'):
    flat = [float(x) for row in twin['matrix'] for x in row]
    twin_args = ' '.join('%g' % x for x in flat) + ' %i' % int(twin.get('n', 2))
  hklf = rm.get('hklf') or {}
  hklf_args = ''
  if 'value' in hklf:
    hklf_args = str(int(hklf['value']))
    if hklf.get('matrix'):
      hklf_args += ' 1 ' + ' '.join('%g' % float(x) for row in hklf['matrix'] for x in row)
  return twin_args, hklf_args


def is_twinned():
  """True for a TWIN instruction or HKLF 5 data in the loaded structure."""
  from olexFunctions import OV
  twin_args, hklf_args = twinning_from_model(OV.GetRefinementModel(False))
  return bool(twin_args) or hklf_args.split()[:1] == ['5']


def gui_fields():
  """
  The _twin_special_details field for a Report > Diffraction table
  (htmlTools.makeHtmlTable entries), pre-filled by update_metacif(); empty
  for a structure that is not twinned and has no text in the item. Used by
  htmlMaker and by ReportPlus, which replaces htmlMaker's generator.
  """
  from olexFunctions import OV
  try:
    update_metacif()
    twinned = is_twinned()
  except Exception as e:
    import sys
    print("Could not describe the twin law: %s" % e)
    if hasattr(sys, '_wing_debugger'):
      raise
    twinned = False
  if not twinned and OV.get_cif_item(CIF_KEY, '?') in ('?', '.', ''):
    return ()
  return ({'varName': CIF_KEY,
           'itemName': '%Twin Special Details%',
           'multiline': 'multiline'},)


def update_metacif():
  """
  Put a generated _twin_special_details into the metacif of the loaded
  structure -- only if the item is empty or holds text generated here
  earlier (recognised by PREFIX); user-written text is never touched. If
  the structure is no longer twinned, earlier generated text is removed.
  """
  import olx
  from olexFunctions import OV
  # get_cif_item builds the structure's block in olx.cif_model if needed
  OV.get_cif_item(CIF_KEY, '?')
  data_name = OV.ModelSrc().replace(' ', '')
  if olx.cif_model is None or data_name not in olx.cif_model:
    return
  block = olx.cif_model[data_name]
  current = str(block.get(CIF_KEY, '?') or '?').strip()
  ours = current in ('?', '.', '') or current.startswith(PREFIX)
  if not ours:
    return
  twin, hklf = twinning_from_model(OV.GetRefinementModel(False))
  cell = [float(x) for x in olx.xf.au.GetCell().split(',')]
  text = None
  if twin:
    text = describe(twin, cell)
  elif hklf.split()[:1] == ['5']:
    hkl = OV.HKLSrc()
    if hkl and os.path.exists(hkl):
      laue = laue_ops_for(olx.xf.au.GetCellSymm())
      text = describe_hklf5_file(hkl, cell, hklf, laue)
  if text:
    block[CIF_KEY] = text
  elif current.startswith(PREFIX):
    block[CIF_KEY] = '?'
