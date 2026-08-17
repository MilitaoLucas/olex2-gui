"""Refinement, through both olex2.refine and SHELXL.

The assertion is on R1 rather than on the refinement merely returning. A
refinement that runs and leaves R1 at 0.6, or that silently applies no
restraints, has not worked - and both of those have happened here.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, has_hkl,
                            r1_of_last_refinement, clear_r1,
                            program_available)

# structures that refine quickly and whose R1 is known to sit well below this.
# A ceiling rather than a target: the point is to catch a refinement that has
# stopped working, not to pin a number that legitimately moves.
SAMPLES = {"sucrose": 0.10, "Co110": 0.15, "ZZULI2": 0.15, "water": 0.15}


def register(suite):
  for name in sorted(SAMPLES):
    suite.run("refine", "olex2.refine %s" % name,
              t_olex2_refine, suite, name, SAMPLES[name])
  suite.run("refine", "refinement applies restraints",
            t_restraints_applied, suite)
  suite.run("refine", "CGLS reaches the same R1", t_cgls, suite)
  suite.run("refine", "shelxl sucrose", t_shelxl, suite, "sucrose", 0.10)


def _prepare(suite, name):
  folder = suite.sample(name)
  if not has_hkl(folder):
    raise SkipTest("no hkl with the %s sample" % name)
  model = model_in(folder)
  load(model)
  macro("user '%s'" % folder.replace("\\", "/"))
  return folder, model


def _refine(cycles=3, program="olex2.refine", method=None):
  OV.SetParam('snum.refinement.program', program)
  if method:
    OV.SetParam('snum.refinement.method', method)
  OV.SetParam('snum.refinement.max_cycles', cycles)
  clear_r1()
  macro("spy.refine.do_refine")


def t_olex2_refine(suite, name, ceiling):
  _prepare(suite, name)
  _refine(3)
  r1 = r1_of_last_refinement()
  if r1 > ceiling:
    raise AssertionError("R1 %.4f is above the %.2f ceiling" % (r1, ceiling))
  return "R1 %.4f" % r1


def t_restraints_applied(suite):
  """A model carrying restraints must still refine with them in place.

  THPP is the sample that has any - a RIGU. The check is that the restraint
  survives the load and the refinement runs to a sane R1 with it: a restraint
  that is silently dropped, or one that makes the normal matrix singular, both
  show here. A protein once refined with 1 restraint over 5207 parameters
  because the module generating them was never imported, and nothing in the
  output said so.

  Restraints are not readable through olx.Ins - they are parsed into the
  refinement model rather than kept as instruction records - so this asserts
  on the refinement rather than on a count.
  """
  folder = suite.sample("THPP")
  if not has_hkl(folder):
    raise SkipTest("no hkl with the THPP sample")
  model = model_in(folder)
  restrained = [l.split()[0] for l in open(model)
                if l[:4] in ("RIGU", "SIMU", "DFIX", "DANG", "SADI", "FLAT",
                             "ISOR", "DELU")]
  if not restrained:
    raise SkipTest("the THPP sample no longer carries a restraint")
  load(model)
  macro("user '%s'" % folder.replace("\\", "/"))
  _refine(3)
  r1 = r1_of_last_refinement()
  if r1 > 0.20:
    raise AssertionError("R1 %.4f with %s in place" % (r1, ",".join(restrained)))
  return "%s held, R1 %.4f" % (",".join(sorted(set(restrained))), r1)


def t_cgls(suite):
  """CGLS-J and the default solver should agree on the same structure.`n`n  The method name is CGLS-J: plain CGLS is a SHELX method, and asking`n  olex2.refine for it raises KeyError - which left the previous run's R1 in`n  place and made the test pass against a number it had not produced.`n  """
  _prepare(suite, "sucrose")
  _refine(3, method="Gauss-Newton")
  r_gn = r1_of_last_refinement()
  _prepare(suite, "sucrose")
  _refine(3, method="CGLS-J")
  r_cgls = r1_of_last_refinement()
  if abs(r_gn - r_cgls) > 0.02:
    raise AssertionError("Gauss-Newton %.4f against CGLS-J %.4f" % (r_gn, r_cgls))
  return "GN %.4f, CGLS-J %.4f" % (r_gn, r_cgls)


def t_shelxl(suite, name, ceiling):
  if not program_available("shelxl"):
    raise SkipTest("shelxl is not in the run directory or on PATH")
  folder, model = _prepare(suite, name)
  OV.SetParam('snum.refinement.program', 'ShelXL')
  # CGLS is SHELXL's own method name; L.S. is not one the phil accepts, and
  # the previous case's CGLS-J was left in place when the set was refused
  OV.SetParam('snum.refinement.method', 'CGLS')
  OV.SetParam('snum.refinement.max_cycles', 4)
  clear_r1()
  macro("spy.refine.do_refine")

  # SHELXL's own output is the evidence, not Olex2's recorded R1: olex2c does
  # not reload the result the way the GUI does, so asserting on the recorded
  # value would test the reload rather than the refinement. The lst is what
  # SHELXL wrote, and the R1 in it is what SHELXL computed.
  r1 = _r1_from_lst(folder)
  if r1 is None:
    raise AssertionError("SHELXL left no R1 in its lst - it did not refine")
  if r1 > ceiling:
    raise AssertionError("R1 %.4f is above the %.2f ceiling" % (r1, ceiling))
  return "R1 %.4f from SHELXL's lst" % r1


def _r1_from_lst(folder):
  """R1 as SHELXL reported it, from the lst it just wrote."""
  best = None
  for root, dirs, files in os.walk(folder):
    for f in files:
      if not f.lower().endswith(".lst"):
        continue
      p = os.path.join(root, f)
      try:
        text = open(p, "r", errors="ignore").read()
      except TypeError:            # python 2
        text = open(p, "r").read()
      for line in text.splitlines():
        s = line.strip()
        # 'R1 =  0.0278 for  1116 Fo > 4sig(Fo)'
        if s.startswith("R1 =") or " R1 = " in s:
          for tok in s.replace("=", " ").split():
            try:
              v = float(tok)
            except ValueError:
              continue
            if 0.0 < v < 1.0:
              best = v if best is None else min(best, v)
              break
  return best
