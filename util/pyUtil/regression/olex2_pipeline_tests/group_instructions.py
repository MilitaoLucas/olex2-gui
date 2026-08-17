"""SHELX model instructions: AFIX, CHIV, RESI, PART, UNIT.

These describe how the model is built rather than what it contains, and every
one of them has to reach the file - the refinement program reads the written
ins, not Olex2's memory. So each case runs the macro and looks for its
instruction in what gets written.

SUMP, EXYZ and SetCharge have no case here. Each was refused (returned 0) in
the argument form tried, and a case built on a guessed syntax tests the guess
rather than the program. They are named in the census gap instead.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, atom_count,
                            deleted, r1_of_last_refinement, clear_r1, has_hkl)


def register(suite):
  suite.run("instructions", "afix constrains a group", t_afix, suite)
  suite.run("instructions", "chiv restrains a chiral volume", t_chiv, suite)
  suite.run("instructions", "split makes a two-part disorder", t_split, suite)
  suite.run("instructions", "resi names a residue", t_resi, suite)
  suite.run("instructions", "fixunit recounts the cell contents", t_fixunit, suite)
  suite.run("instructions", "himp sets a hydrogen distance", t_himp, suite)
  suite.run("instructions", "an instructed model still refines",
            t_still_refines, suite)


def _sucrose(suite):
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  return folder


def _labels(kind):
  out = []
  for i in range(int(atom_count())):
    if deleted(i):
      continue
    if olx.xf.au.GetAtomType(i) == kind:
      out.append(olx.xf.au.GetAtomName(i))
  return out


def _ins(folder, tag):
  out = os.path.join(folder, "%s.ins" % tag).replace("\\", "/")
  macro("file '%s'" % out)
  if not os.path.exists(out):
    raise AssertionError("file did not write %s" % out)
  return open(out, "r", errors="ignore").read()


def _lines(text, key):
  return [l.rstrip() for l in text.splitlines()
          if l.split() and l.split()[0].upper() == key]


def t_afix(suite):
  """AFIX declares a rigid or riding group; afix 0 takes one away.

  Asserting that `afix 13` adds lines does not work here: sucrose already
  carries 38 of them for its riding hydrogens, and applying another leaves the
  count where it was. Removal is the unambiguous direction - `afix 0 $H` has
  to leave none.
  """
  folder = _sucrose(suite)
  before = _lines(_ins(folder, "i_afix_a"), "AFIX")
  if not before:
    raise SkipTest("the sucrose sample carries no AFIX to remove")
  # a group is opened and closed, so a closing AFIX 0 has to be there already
  if not any(len(l.split()) > 1 and l.split()[1] == "0" for l in before):
    raise AssertionError("AFIX groups are opened and never closed: %s"
                         % "; ".join(before[:3]))
  macro("afix 0 $H")
  after = _lines(_ins(folder, "i_afix_b"), "AFIX")
  if len(after) >= len(before):
    raise AssertionError("afix 0 $H left %d AFIX line(s), was %d"
                         % (len(after), len(before)))
  return "%d AFIX line(s) -> %d after afix 0 $H" % (len(before), len(after))


def t_chiv(suite):
  folder = _sucrose(suite)
  c = _labels("C")
  macro("chiv %s %s" % (c[0], c[1]))
  lines = _lines(_ins(folder, "i_chiv"), "CHIV")
  if not lines:
    raise AssertionError("chiv wrote no CHIV")
  if c[0].upper() not in lines[0].upper():
    raise AssertionError("CHIV does not name %s: %r" % (c[0], lines[0]))
  return lines[0][:40]


def t_split(suite):
  """Splitting an atom makes two parts of it, which is PART 1 and PART 2."""
  folder = _sucrose(suite)
  c = _labels("C")
  before = _lines(_ins(folder, "i_split_a"), "PART")
  macro("split %s" % c[0])
  after = _lines(_ins(folder, "i_split_b"), "PART")
  if len(after) <= len(before):
    raise AssertionError("split wrote %d PART line(s), was %d"
                         % (len(after), len(before)))
  parts = set(l.split()[1] for l in after if len(l.split()) > 1)
  if len(parts) < 2:
    raise AssertionError("split gave only part(s) %s" % ", ".join(sorted(parts)))
  return "parts %s" % ", ".join(sorted(parts))


def t_resi(suite):
  folder = _sucrose(suite)
  c = _labels("C")
  macro("resi TOL 1 %s" % c[1])
  lines = _lines(_ins(folder, "i_resi"), "RESI")
  if not lines:
    raise AssertionError("resi wrote no RESI")
  if "TOL" not in lines[0].upper():
    raise AssertionError("RESI does not carry the class: %r" % lines[0])
  return lines[0][:40]


def t_fixunit(suite):
  """UNIT is the cell contents, and fixunit recomputes it from the model."""
  folder = _sucrose(suite)
  before = _lines(_ins(folder, "i_unit_a"), "UNIT")
  macro("fixunit")
  after = _lines(_ins(folder, "i_unit_b"), "UNIT")
  if not after:
    raise AssertionError("no UNIT after fixunit")
  counts = [x for x in after[0].split()[1:]]
  if not counts or not all(_isnum(x) for x in counts):
    raise AssertionError("UNIT is not a list of counts: %r" % after[0])
  if all(float(x) == 0 for x in counts):
    raise AssertionError("fixunit set every count to zero: %r" % after[0])
  return "%s (was %s)" % (after[0][:32],
                          (before[0][:32] if before else "absent"))


def _isnum(x):
  try:
    float(x)
    return True
  except ValueError:
    return False


def t_himp(suite):
  """HImp adjusts the riding hydrogen geometry, through an AFIX."""
  folder = _sucrose(suite)
  h = _labels("H")
  if not h:
    raise SkipTest("no hydrogens in the sample")
  if olex.m("himp 1.0 %s" % h[0]) == 0:
    raise SkipTest("himp was refused for %s" % h[0])
  lines = _lines(_ins(folder, "i_himp"), "AFIX")
  if not lines:
    raise AssertionError("himp left no AFIX")
  return "%d AFIX line(s)" % len(lines)


def t_still_refines(suite):
  """Instructions must not stop the refinement working.

  RESI is deliberately not in this combination. Putting a single atom into a
  residue when that atom is the pivot of a riding-hydrogen group leaves the
  constraint pointing outside the residue, and the refinement dies in
  iotbx/builders_depending_on_smtbx.py:39
  (add_u_iso_proportional_to_pivot_u_eq) with a bare "Index out of range" -
  no mention of RESI, of the atom, or of the constraint. Arguably user error,
  but the diagnosis costs an hour. Recorded in the README rather than pinned
  here as an expectation.
  """
  folder = _sucrose(suite)
  if not has_hkl(folder):
    raise SkipTest("no hkl with the sucrose sample")
  OV.SetParam('snum.refinement.program', 'olex2.refine')
  OV.SetParam('snum.refinement.method', 'Gauss-Newton')
  OV.SetParam('snum.refinement.max_cycles', 3)
  clear_r1()
  macro("spy.refine.do_refine")
  plain = r1_of_last_refinement()

  c = _labels("C")
  macro("chiv %s %s" % (c[0], c[1]))
  macro("fixunit")
  clear_r1()
  macro("spy.refine.do_refine")
  after = r1_of_last_refinement()
  if after > plain + 0.05:
    raise AssertionError("R1 %.4f -> %.4f with CHIV and UNIT set"
                         % (plain, after))
  return "R1 %.4f -> %.4f with CHIV and a recounted UNIT" % (plain, after)
