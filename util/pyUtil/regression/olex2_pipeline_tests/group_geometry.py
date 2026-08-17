"""Geometry and connectivity: coordinates, bonds, contacts, rings.

Most of these print their answer to the log and hand back a status, so the
cases assert on what changed in the model or on a value that can be checked
against something else. The coordinate case checks Olex2 against itself: the
same interatomic distance computed from the Cartesian coordinates and from the
fractional ones through the cell metric has to agree.
"""
from __future__ import absolute_import, division, print_function

import math
import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, atom_count,
                            deleted)

# Calls that report to the log and return a status. 1 is done, 0 is refused -
# which is how four entries in the api sweep turned out to be failing silently.
REPORTERS = ["Envi", "Bang", "AtomInfo", "Describe", "AnalyseModel"]


def register(suite):
  suite.run("geometry", "Crd and CCrd agree through the cell", t_coords, suite)
  suite.run("geometry", "htab finds hydrogen bonds", t_htab, suite)
  suite.run("geometry", "addbond and delbond reach the model", t_bonds, suite)
  suite.run("geometry", "VVol reports a volume", t_vvol, suite)
  suite.run("geometry", "reporting calls are accepted", t_reporters, suite)
  suite.run("geometry", "rrings and pipi are accepted", t_rings, suite)


def _sucrose(suite):
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  return folder


def _labels(kind=None):
  out = []
  for i in range(int(atom_count())):
    if deleted(i):
      continue
    if kind is None or olx.xf.au.GetAtomType(i) == kind:
      out.append(olx.xf.au.GetAtomName(i))
  return out


def _triple(s):
  return [float(x) for x in str(s).split()]


def _metric():
  """The cell metric tensor, from the cell Olex2 reports."""
  a, b, c = (float(olx.Cell(x)) for x in "abc")
  al, be, ga = (math.radians(float(olx.Cell(x))) for x in ("alpha", "beta", "gamma"))
  return [
    [a * a, a * b * math.cos(ga), a * c * math.cos(be)],
    [a * b * math.cos(ga), b * b, b * c * math.cos(al)],
    [a * c * math.cos(be), b * c * math.cos(al), c * c],
  ]


def t_coords(suite):
  """Cartesian and fractional coordinates have to describe the same atoms.

  Not a smoke test: the distance between two atoms is computed twice, once
  from Crd with Pythagoras and once from CCrd through the cell metric, and the
  two have to agree. That exercises Crd, CCrd and the cell together, and a
  wrong cell or a wrong convention shows up as a mismatch rather than as a
  plausible number nobody checked.
  """
  _sucrose(suite)
  labels = _labels("C")
  if len(labels) < 2:
    raise SkipTest("fewer than two carbons")
  a, b = labels[0], labels[1]
  ca, cb = _triple(olx.Crd(a)), _triple(olx.Crd(b))
  fa, fb = _triple(olx.CCrd(a)), _triple(olx.CCrd(b))
  if len(ca) != 3 or len(fa) != 3:
    raise AssertionError("Crd/CCrd did not give three numbers: %r / %r"
                         % (olx.Crd(a), olx.CCrd(a)))
  d_cart = math.sqrt(sum((x - y) ** 2 for x, y in zip(ca, cb)))
  df = [x - y for x, y in zip(fa, fb)]
  g = _metric()
  d_frac = math.sqrt(sum(df[i] * g[i][j] * df[j]
                         for i in range(3) for j in range(3)))
  if d_cart <= 0:
    raise AssertionError("%s and %s are at the same Cartesian point" % (a, b))
  # CCrd is printed to three decimals, so the fractional route is the coarser
  # of the two; 0.02 A is comfortably inside that and far outside a real error
  if abs(d_cart - d_frac) > 0.02:
    raise AssertionError("%s-%s is %.4f A from Crd and %.4f A from CCrd"
                         % (a, b, d_cart, d_frac))
  return "%s-%s %.3f A, both routes agree" % (a, b, d_cart)


def t_htab(suite):
  """HTAB is written for each hydrogen bond found, so they can be counted."""
  folder = _sucrose(suite)
  before = _count_ins(folder, "htab_a", "HTAB")
  macro("htab")
  after = _count_ins(folder, "htab_b", "HTAB")
  if after <= before:
    raise AssertionError("htab wrote %d HTAB, was %d" % (after, before))
  return "%d hydrogen bond(s)" % after


def t_bonds(suite):
  """A bond added by hand is a BIND, one removed is a FREE."""
  folder = _sucrose(suite)
  c, o = _labels("C"), _labels("O")
  if not c or not o:
    raise SkipTest("need a carbon and an oxygen")
  macro("addbond %s %s" % (c[0], o[0]))
  text = _ins(folder, "bond_a")
  if not _has(text, "BIND", c[0], o[0]):
    raise AssertionError("addbond wrote no BIND %s %s" % (c[0], o[0]))
  macro("delbond %s %s" % (c[0], c[1]))
  text = _ins(folder, "bond_b")
  if not _has(text, "FREE", c[0], c[1]):
    raise AssertionError("delbond wrote no FREE %s %s" % (c[0], c[1]))
  return "BIND %s %s and FREE %s %s" % (c[0], o[0], c[0], c[1])


def _has(text, key, *atoms):
  for line in text.splitlines():
    t = line.split()
    if t and t[0].upper() == key and all(a.upper() in
                                        [x.upper() for x in t[1:]] for a in atoms):
      return True
  return False


def _ins(folder, tag):
  out = os.path.join(folder, "%s.ins" % tag).replace("\\", "/")
  macro("file '%s'" % out)
  if not os.path.exists(out):
    raise AssertionError("file did not write %s" % out)
  return open(out, "r", errors="ignore").read()


def _count_ins(folder, tag, key):
  return sum(1 for line in _ins(folder, tag).splitlines()
             if line.split() and line.split()[0].upper() == key)


def t_vvol(suite):
  """The volume the model occupies, which has to be positive and below the cell."""
  _sucrose(suite)
  v = olx.VVol()
  try:
    vol = float(str(v).split()[0])
  except (ValueError, IndexError):
    raise AssertionError("VVol gave %r" % (v,))
  cell = float(olx.xf.au.GetCellVolume())
  if vol <= 0 or vol > cell:
    raise AssertionError("VVol %.2f against a cell of %.2f" % (vol, cell))
  return "%.2f of %.2f A^3" % (vol, cell)


def t_reporters(suite):
  """Calls that report to the log must at least not refuse."""
  _sucrose(suite)
  a = _labels("C")
  refused = []
  for name in REPORTERS:
    fn = getattr(olx, name, None)
    if fn is None:
      refused.append("%s (not exported)" % name)
      continue
    args = {"Envi": (a[0],), "Bang": (a[0], a[1], a[2]),
            "AtomInfo": (a[0],)}.get(name, ())
    try:
      v = fn(*args)
    except Exception as e:
      refused.append("%s raised %s" % (name, str(e).split("\n")[0][:40]))
      continue
    if isinstance(v, int) and not isinstance(v, bool) and v == 0:
      refused.append("%s returned 0" % name)
  if refused:
    raise AssertionError("; ".join(refused))
  return "%d accepted" % len(REPORTERS)


def t_rings(suite):
  """Ring and stacking analysis, which sucrose has rings for."""
  _sucrose(suite)
  for cmd in ("rrings C6", "pipi"):
    if olex.m(cmd) == 0:
      raise AssertionError("%r was refused" % cmd)
  return "rrings and pipi accepted"
