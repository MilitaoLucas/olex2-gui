"""
gui/proto/transform.py

Re-express a stored SHELX model in another setting of the same lattice.
Pure Python (no Olex2 / cctbx imports) so it can be tested outside Olex2;
the change-of-basis operator itself comes from cells.setting_transform().

The operator maps stored fractional coordinates onto current ones:

    x_new = R x_old + t

and anisotropic displacement parameters transform as the covariance of
the fractional coordinates:  U*_new = R U*_old R^T, with U*_ij =
U_ij a*_i a*_j (SHELX/CIF U_ij, a*_i reciprocal cell lengths).

Only atom lines (and EQIV operators, via a callback) are changed; all
other instructions -- restraints, AFIX, PART, FVAR, ... -- are kept.
"""

from __future__ import annotations

import math
import re
from fractions import Fraction

# SHELXL instructions: a line starting with one of these is never an atom
KEYWORDS = {
    'TITL', 'CELL', 'ZERR', 'LATT', 'SYMM', 'SFAC', 'DISP', 'UNIT', 'LAUE',
    'REM', 'MORE', 'TIME', 'END', 'HKLF', 'OMIT', 'SHEL', 'BASF', 'TWIN',
    'EXTI', 'SWAT', 'HOPE', 'MERG', 'SPEC', 'RESI', 'MOVE', 'ANIS', 'AFIX',
    'HFIX', 'FRAG', 'FEND', 'EXYZ', 'EADP', 'EQIV', 'CONN', 'PART', 'BIND',
    'FREE', 'DFIX', 'DANG', 'BUMP', 'SAME', 'SADI', 'CHIV', 'FLAT', 'DELU',
    'SIMU', 'DEFS', 'ISOR', 'NCSY', 'SUMP', 'L.S.', 'CGLS', 'BLOC', 'DAMP',
    'STIR', 'WGHT', 'FVAR', 'BOND', 'CONF', 'MPLA', 'RTAB', 'HTAB', 'LIST',
    'ACTA', 'SIZE', 'TEMP', 'WPDB', 'FMAP', 'GRID', 'PLAN', 'MOLE', 'ABIN',
    'ANSC', 'ANSR', 'NEUT', 'RIGU', 'TWST', 'PRIG', 'XNPD', 'WIGL', 'BEDE',
    'LONE', 'SHEL', 'STIR', 'DELU', 'EGEN', 'NOTR', 'POLY', 'FLAP', 'BUMP',
}


# ---------------------------------------------------------------------------
# Small linear algebra on 3x3 matrices given as 9-tuples (row major)
# ---------------------------------------------------------------------------

def _mat(m9):
  return [list(m9[0:3]), list(m9[3:6]), list(m9[6:9])]


def _mul(a, b):
  return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _transpose(a):
  return [[a[j][i] for j in range(3)] for i in range(3)]


def reciprocal_lengths(cell):
  """(a*, b*, c*) for cell = (a, b, c, alpha, beta, gamma) in degrees."""
  a, b, c = cell[:3]
  al, be, ga = (math.radians(x) for x in cell[3:])
  ca, cb, cg = math.cos(al), math.cos(be), math.cos(ga)
  sa, sb, sg = math.sin(al), math.sin(be), math.sin(ga)
  v = a * b * c * math.sqrt(1 - ca * ca - cb * cb - cg * cg + 2 * ca * cb * cg)
  return (b * c * sa / v, a * c * sb / v, a * b * sg / v)


def transform_u(u_shelx, r9, old_cell, new_cell):
  """
  Transform anisotropic U given in SHELX order (U11 U22 U33 U23 U13 U12).
  Returns the new six values in the same order.
  """
  u11, u22, u33, u23, u13, u12 = u_shelx
  ra = reciprocal_lengths(old_cell)
  u = [[u11, u12, u13], [u12, u22, u23], [u13, u23, u33]]
  ustar = [[u[i][j] * ra[i] * ra[j] for j in range(3)] for i in range(3)]
  r = _mat(r9)
  ustar_new = _mul(_mul(r, ustar), _transpose(r))
  rn = reciprocal_lengths(new_cell)
  un = [[ustar_new[i][j] / (rn[i] * rn[j]) for j in range(3)] for i in range(3)]
  return (un[0][0], un[1][1], un[2][2], un[1][2], un[0][2], un[0][1])


def transform_xyz(xyz, r9, t):
  r = _mat(r9)
  return tuple(sum(r[i][k] * xyz[k] for k in range(3)) + t[i] for i in range(3))


# ---------------------------------------------------------------------------
# Symmetry operators (EQIV), exact arithmetic
# ---------------------------------------------------------------------------

def _frac(v):
  return Fraction(v).limit_denominator(48)


def _inverse(m):
  """Inverse of a 3x3 matrix of Fractions."""
  (a, b, c), (d, e, f), (g, h, i) = m
  det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
  adj = [[e * i - f * h, c * h - b * i, b * f - c * e],
         [f * g - d * i, a * i - c * g, c * d - a * f],
         [d * h - e * g, b * g - a * h, a * e - b * d]]
  return [[x / det for x in row] for row in adj]


def parse_symop(op):
  """'-x+1, y, -z+1/2' (any case, decimals allowed) -> (3x3, 3) Fractions."""
  parts = [p.strip() for p in op.replace(' ', '').lower().split(',')]
  if len(parts) != 3:
    raise ValueError("not a symmetry operator: %r" % op)
  rot, trans = [], []
  for p in parts:
    row, const = [Fraction(0)] * 3, Fraction(0)
    for sign, num, var in re.findall(r'([+-]?)([0-9./]*)\*?([xyz]?)', p):
      if not num and not var:
        continue
      val = Fraction(num) if num else Fraction(1)
      if sign == '-':
        val = -val
      if var:
        row['xyz'.index(var)] += val
      else:
        const += val
    rot.append(row)
    trans.append(const)
  return rot, trans


def format_symop(rot, trans):
  out = []
  for row, const in zip(rot, trans):
    s = ''
    for coef, var in zip(row, 'xyz'):
      if coef == 0:
        continue
      sign = '-' if coef < 0 else '+'
      mag = abs(coef)
      s += sign + ('' if mag == 1 else '%s*' % mag) + var
    if const:
      s += ('-' if const < 0 else '+') + str(abs(const))
    out.append(s.lstrip('+') or '0')
  return ', '.join(out)


def transform_symop(op, r9, t):
  """
  A symmetry operator in the new setting: S' = C S C^-1, where
  C = (R, t) is the change-of-basis operator (old -> new).
  """
  s_r, s_t = parse_symop(op)
  r = [[_frac(x) for x in row] for row in _mat(r9)]
  tv = [_frac(x) for x in t]
  r_inv = _inverse(r)
  rot = _mul(_mul(r, s_r), r_inv)
  # translation: R s_t + t - (R S R^-1) t
  trans = [sum(r[i][k] * s_t[k] for k in range(3)) + tv[i]
           - sum(rot[i][k] * tv[k] for k in range(3)) for i in range(3)]
  return format_symop(rot, trans)


# ---------------------------------------------------------------------------
# SHELX text handling
# ---------------------------------------------------------------------------

def _logical_lines(text):
  """
  Yield (physical_lines, logical_text): SHELX continuation lines (a line
  ending in ' =') are joined into one logical line.
  """
  buf, parts = [], []
  for line in text.splitlines():
    buf.append(line)
    stripped = line.rstrip()
    if stripped.endswith('=') and not stripped.upper().startswith(('REM', 'TITL')):
      parts.append(stripped[:-1])
      continue
    parts.append(line)
    yield buf, ' '.join(p.strip() for p in parts)
    buf, parts = [], []
  if buf:
    yield buf, ' '.join(p.strip() for p in parts)


def _is_number(s):
  try:
    float(s)
    return True
  except ValueError:
    return False


def _parse_atom(logical):
  """
  (label, sfac, xyz, rest_tokens) if `logical` is an atom line, else None.
  rest_tokens are the tokens after x y z (sof, U or U11..U12).
  """
  tok = logical.split()
  if len(tok) < 5 or tok[0].upper() in KEYWORDS or not tok[0][0].isalpha():
    return None
  if not tok[1].lstrip('-').isdigit():
    return None
  if not all(_is_number(x) for x in tok[2:]):
    return None
  # xyz / +sof / +Uiso / +Uiso+peak height (Q peaks) / +sof+6 Uij
  if len(tok) not in (5, 6, 7, 8, 12):
    return None
  return tok[0], tok[1], tuple(float(x) for x in tok[2:5]), tok[5:]


def _free_coordinate(v):
  """SHELX coordinate codes: |v| > 5 means fixed (10 + x) etc. -- keep x."""
  if abs(v) > 5:
    return v - 10 * round(v / 10)
  return v


def _format_atom(label, sfac, xyz, rest):
  head = "%-5s %s %10.6f %10.6f %10.6f" % ((label, sfac) + tuple(xyz))
  if len(rest) <= 3:
    return [" ".join([head] + rest)]
  # sof + six U values: continuation line as SHELXL writes it
  sof, u = rest[0], [float(x) for x in rest[1:]]
  return ["%s %s %10.5f %10.5f =" % (head, sof, u[0], u[1]),
          "    %10.5f %10.5f %10.5f %10.5f" % tuple(u[2:])]


def transform_model(text, r9, t, old_cell, new_cell,
                    replace=None, drop=('LATT', 'SYMM'), eqiv=True):
  """
  Return `text` re-expressed in the new setting.

  r9, t     change-of-basis operator (old -> new), 9-tuple and 3-tuple
  replace   {KEY: [lines]}: the first line starting with KEY is replaced
            by these lines (e.g. the current CELL, ZERR, LATT+SYMM)
  drop      keys whose lines are removed (the old symmetry); a key in
            `replace` is put where its first line was
  eqiv      True: transform EQIV operators with the same operator
  """
  replace = dict(replace or {})
  done = set()
  out = []
  for physical, logical in _logical_lines(text):
    key = logical[:4].upper()
    if key in replace:
      if key not in done:
        out.extend(replace[key])
        done.add(key)
      continue
    if key in drop:
      continue
    if key == 'EQIV' and eqiv:
      tok = logical.split(None, 2)
      if len(tok) == 3:
        out.append("EQIV %s %s" % (tok[1], transform_symop(tok[2], r9, t)))
        continue
    atom = _parse_atom(logical)
    if atom is None:
      out.extend(physical)
      continue
    label, sfac, xyz, rest = atom
    xyz = transform_xyz(tuple(_free_coordinate(v) for v in xyz), r9, t)
    if len(rest) == 7:
      u = transform_u(tuple(float(x) for x in rest[1:]), r9, old_cell, new_cell)
      rest = [rest[0]] + ["%.5f" % x for x in u]
    out.extend(_format_atom(label, sfac, xyz, rest))
  # keys to replace that the stored model didn't have (e.g. no SYMM in
  # P-1): put them after CELL/ZERR, where SHELX expects the symmetry
  missing = [k for k in replace if k not in done]
  if missing:
    at = 1
    for i, l in enumerate(out):
      if l[:4].upper() in ('CELL', 'ZERR'):
        at = i + 1
    for k in missing:
      out[at:at] = replace[k]
      at += len(replace[k])
  return '\n'.join(out) + '\n'
