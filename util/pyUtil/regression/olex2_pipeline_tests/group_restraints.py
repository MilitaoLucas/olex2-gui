"""Restraint and constraint macros, checked by what reaches the model.

Restraints are not readable through `olx.Ins` - they are parsed into the
refinement model rather than kept as instruction records - so each case writes
the model out and looks for its instruction in the file, which is what the next
program reads, and then refines to prove the model still solves with it.

This matters more than it looks. A protein once refined with 1 restraint over
5207 parameters because the module that generates them was never imported, and
nothing in the output said so. A restraint that is silently dropped and one
that is applied produce the same log.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, atom_count,
                            deleted, r1_of_last_refinement, clear_r1)

# instruction -> how to call it on a couple of atoms of the given type
# SADI takes pairs - two atoms is one distance and there is nothing to make
# equal, so it is dropped rather than written and the case would fail on a
# correct Olex2. SAME needs two matching fragments, which this sample has no
# pair of, so it has no case here.
CASES = [
  ("DFIX", "dfix 1.5 %s %s", 2, "C"),
  ("DANG", "dang 2.4 %s %s", 2, "C"),
  ("SADI", "sadi %s %s %s %s", 4, "C"),
  ("SIMU", "simu %s %s", 2, "C"),
  ("RIGU", "rigu %s %s", 2, "C"),
  ("DELU", "delu %s %s", 2, "C"),
  ("ISOR", "isor %s %s", 2, "C"),
  ("EADP", "eadp %s %s", 2, "C"),
  ("FLAT", "flat %s %s %s %s", 4, "C"),
]


def register(suite):
  for name, template, n, kind in CASES:
    suite.run("restraints", "%s reaches the model" % name,
              t_restraint, suite, name, template, n, kind)
  suite.run("restraints", "a restrained model still refines",
            t_refines_with_restraints, suite)


def _atoms(kind, n):
  out = []
  for i in range(int(atom_count())):
    if deleted(i) or olx.xf.au.GetAtomType(i) != kind:
      continue
    out.append(olx.xf.au.GetAtomName(i))
    if len(out) == n:
      return out
  raise SkipTest("fewer than %d %s atoms" % (n, kind))


def _write(folder, tag):
  out = os.path.join(folder, "%s.ins" % tag).replace("\\", "/")
  macro("file '%s'" % out)
  if not os.path.exists(out):
    raise AssertionError("file did not write %s" % out)
  return open(out, "r", errors="ignore").read()


def t_restraint(suite, name, template, n, kind):
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  before = _count(_write(folder, "r_before_%s" % name), name)
  macro(template % tuple(_atoms(kind, n)))
  after = _count(_write(folder, "r_after_%s" % name), name)
  if after <= before:
    raise AssertionError("%s: %d in the ins before, %d after"
                         % (name, before, after))
  return "%d -> %d %s line(s)" % (before, after, name)


def _count(text, name):
  return sum(1 for line in text.splitlines()
             if line.split() and line.split()[0].upper() == name.upper())


def t_refines_with_restraints(suite):
  """Adding restraints must not stop the refinement converging.

  A restraint that makes the normal matrix singular fails here, which is how
  a coplanar FLAT was caught: it became a chirality restraint with zero
  volume, its gradient scaling divided by zero, and the Cholesky decomposition
  failed naming an unrelated atom.
  """
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  OV.SetParam('snum.refinement.program', 'olex2.refine')
  OV.SetParam('snum.refinement.method', 'Gauss-Newton')
  OV.SetParam('snum.refinement.max_cycles', 3)

  clear_r1()
  macro("spy.refine.do_refine")
  plain = r1_of_last_refinement()

  c = _atoms("C", 4)
  macro("dfix 1.5 %s %s" % (c[0], c[1]))
  macro("sadi %s %s %s %s" % tuple(c))
  macro("rigu %s %s" % (c[0], c[1]))
  macro("flat %s %s %s %s" % tuple(c))
  clear_r1()
  macro("spy.refine.do_refine")
  restrained = r1_of_last_refinement()

  if restrained > plain + 0.05:
    raise AssertionError("R1 went %.4f -> %.4f with four restraints"
                         % (plain, restrained))
  return "R1 %.4f -> %.4f with DFIX, SADI, RIGU and FLAT" % (plain, restrained)
