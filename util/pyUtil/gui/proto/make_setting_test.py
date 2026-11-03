"""
gui/proto/make_setting_test.py

Make test data for proto's setting transformation: a copy of an ins/hkl
pair re-expressed in another setting of the same lattice. The ins keeps
no atoms (a data set waiting to be solved); the hkl indices are transformed.

From util/pyUtil/gui:

    python -m proto.make_setting_test <ins> <hkl> <out_dir> <basis> [tag]

basis gives the new axes in terms of the old ones, e.g.
    a,b,c-a      P21/c -> P21/n (monoclinic, b unique)
    b,c,a        cyclic axis permutation (e.g. orthorhombic)
The determinant must be +1 (keeps the handedness).

Test: solve and refine the original, spy.proto.add(); then load the copy
and run spy.proto.find() -- it should be listed as a 'setting' match.
"""

import math
import os
import re
import sys

from . import transform as T


def parse_basis(text):
  """'a,b,c-a' -> 3x3 integer rows (new axes in terms of old ones)."""
  rows = []
  for part in text.replace(' ', '').lower().split(','):
    row = [0, 0, 0]
    for sign, num, ax in re.findall(r'([+-]?)(\d*)([abc])', part):
      v = int(num) if num else 1
      row['abc'.index(ax)] += -v if sign == '-' else v
    rows.append(row)
  if len(rows) != 3:
    raise ValueError("basis needs three axes, e.g. a,b,c-a")
  return rows


def _det(m):
  return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
          - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
          + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def _metric(cell):
  a, b, c = cell[:3]
  al, be, ga = (math.radians(x) for x in cell[3:])
  return [[a * a, a * b * math.cos(ga), a * c * math.cos(be)],
          [a * b * math.cos(ga), b * b, b * c * math.cos(al)],
          [a * c * math.cos(be), b * c * math.cos(al), c * c]]


def new_cell(cell, basis):
  g = T._mul(T._mul(basis, _metric(cell)), T._transpose(basis))
  a, b, c = (math.sqrt(g[i][i]) for i in range(3))
  return (a, b, c,
          math.degrees(math.acos(g[1][2] / (b * c))),
          math.degrees(math.acos(g[0][2] / (a * c))),
          math.degrees(math.acos(g[0][1] / (a * b))))


def coordinate_operator(basis):
  """x' = R x for basis rows B: R = (B^-1)^T, as a 9-tuple of floats."""
  inv = T._inverse([[T.Fraction(x) for x in row] for row in basis])
  return tuple(float(x) for row in T._transpose(inv) for x in row)


def transform_ins(text, basis):
  r9 = coordinate_operator(basis)
  out = []
  for physical, logical in T._logical_lines(text):
    tok = logical.split()
    key = logical[:4].upper()
    if key == 'CELL':
      cell = new_cell([float(x) for x in tok[2:8]], basis)
      out.append("CELL %s %s" % (tok[1], ' '.join('%.4f' % x for x in cell)))
    elif key == 'ZERR':
      # esds of the new cell are not derived -- a plausible placeholder
      out.append("ZERR %s 0.001 0.001 0.001 0.01 0.01 0.01" % tok[1])
    elif key == 'LATT':
      if abs(int(tok[1])) != 1:
        raise ValueError("only primitive lattices (LATT +-1) are supported")
      out.append(logical)
    elif key == 'SYMM':
      out.append("SYMM " + T.transform_symop(logical[4:].strip(), r9, (0, 0, 0)))
    elif T._parse_atom(logical) is not None:
      continue                           # data set to solve: no atoms
    else:
      out.extend(physical)
  return '\n'.join(out) + '\n'


def transform_hkl(text, basis):
  """h' = B h for every reflection until the 0 0 0 terminator."""
  out, done = [], False
  for line in text.splitlines():
    if done or len(line) < 12:
      out.append(line)
      continue
    h = [int(line[i:i + 4]) for i in (0, 4, 8)]
    if h == [0, 0, 0]:
      done = True
      out.append(line)
      continue
    hn = [sum(basis[i][k] * h[k] for k in range(3)) for i in range(3)]
    out.append("%4d%4d%4d%s" % (hn[0], hn[1], hn[2], line[12:]))
  return '\n'.join(out) + '\n'


def main(argv):
  if len(argv) not in (4, 5):
    print(__doc__)
    return 1
  ins, hkl, out_dir, basis_text = argv[:4]
  basis = parse_basis(basis_text)
  if _det(basis) != 1:
    print("basis %s has determinant %s -- need +1" % (basis_text, _det(basis)))
    return 1
  name = os.path.splitext(os.path.basename(ins))[0]
  tag = argv[4] if len(argv) == 5 else re.sub(r'[^a-z0-9]+', '', basis_text.lower())
  os.makedirs(out_dir, exist_ok=True)
  stem = os.path.join(out_dir, "%s_%s" % (name, tag))
  with open(ins) as fh:
    new_ins = transform_ins(fh.read(), basis)
  with open(hkl) as fh:
    new_hkl = transform_hkl(fh.read(), basis)
  with open(stem + '.ins', 'w') as fh:
    fh.write(new_ins)
  with open(stem + '.hkl', 'w') as fh:
    fh.write(new_hkl)
  print("wrote %s.ins / .hkl" % stem)
  for line in new_ins.splitlines():
    if line[:4].upper() in ('CELL', 'LATT', 'SYMM'):
      print("  " + line)
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
