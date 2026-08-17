"""Broken models must fail with a diagnosis, not with an index.

Every case here builds a model that is wrong in a way a user can produce by
hand, runs the refinement, and requires the failure to name something the user
can act on. A wrong model failing is fine. A wrong model failing with "Index
out of range" costs an hour, and that was the state before these cases.

The one that started this: `resi TOL 1 C22` puts a single carbon into a
residue while the hydrogens riding on it stay outside. The constraint then
refers to a scatterer index that no longer exists, and the message was
"Index out of range" from iotbx/builders_depending_on_smtbx.py - naming
neither RESI, nor an atom, nor a constraint.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, atom_count,
                            deleted, has_hkl, clear_r1, r1_of_last_refinement)

# words that make a message actionable: they point at the model, not the code
USEFUL = ["resi", "afix", "constraint", "restraint", "atom", "scatterer",
          "riding", "renamed", "deleted", "ordering"]


def register(suite):
  suite.run("validation", "a split riding group is diagnosed",
            t_resi_splits_afix, suite)
  suite.run("validation", "a good model still refines cleanly",
            t_control, suite)


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


def _refine_capturing(folder):
  """Refine, and return everything it printed.

  The refinement catches its own exception and reports it by printing, so the
  message has to be taken off stdout - it is not raised, and it does not reach
  a log file that can be read back afterwards.
  """
  import io
  import sys
  OV.SetParam('snum.refinement.program', 'olex2.refine')
  OV.SetParam('snum.refinement.method', 'Gauss-Newton')
  OV.SetParam('snum.refinement.max_cycles', 3)
  clear_r1()
  buf = io.StringIO()
  real_out, real_err = sys.stdout, sys.stderr

  class tee(object):
    """Keep the run visible while capturing it - a silent run is unreadable."""
    def __init__(self, a, b):
      self.a, self.b = a, b

    def write(self, s):
      try:
        self.a.write(s)
      except Exception:
        pass
      self.b.write(s)

    def flush(self):
      try:
        self.a.flush()
      except Exception:
        pass

    def __getattr__(self, n):
      return getattr(self.a, n)

  sys.stdout, sys.stderr = tee(real_out, buf), tee(real_err, buf)
  try:
    macro("spy.refine.do_refine")
  finally:
    sys.stdout, sys.stderr = real_out, real_err
  return buf.getvalue()


def t_resi_splits_afix(suite):
  """Putting a riding group's pivot in a residue must be diagnosed."""
  folder = _sucrose(suite)
  if not has_hkl(folder):
    raise SkipTest("no hkl with the sucrose sample")
  c = _labels("C")
  if len(c) < 3:
    raise SkipTest("fewer than three carbons")

  # a healthy refinement first, so the failure below is the residue and not
  # something the sample brought with it
  clear_r1()
  macro("spy.refine.do_refine")
  if r1_of_last_refinement() > 0.10:
    raise SkipTest("the sample does not refine cleanly to begin with")

  macro("resi TOL 1 %s" % c[2])
  text = _refine_capturing(folder).lower()

  if "index out of range" in text and not any(w in text for w in USEFUL):
    raise AssertionError(
      "the refinement failed with a bare index error and named nothing "
      "actionable - the guard in builders_depending_on_smtbx is not in this "
      "cctbx")
  r1 = None
  try:
    r1 = r1_of_last_refinement()
  except Exception:
    pass
  if r1 is not None:
    # Olex2 coped with it, which is a fine outcome - the point is that it
    # either works or explains itself
    return "the split residue refined anyway, R1 %.4f" % r1
  named = [w for w in USEFUL if w in text]
  if not named:
    raise AssertionError("the refinement failed without naming anything "
                         "actionable")
  return "failed and named: %s" % ", ".join(sorted(named)[:4])


def t_control(suite):
  """The control: an untouched sample must refine without any of this."""
  folder = _sucrose(suite)
  if not has_hkl(folder):
    raise SkipTest("no hkl with the sucrose sample")
  clear_r1()
  OV.SetParam('snum.refinement.program', 'olex2.refine')
  OV.SetParam('snum.refinement.method', 'Gauss-Newton')
  OV.SetParam('snum.refinement.max_cycles', 3)
  macro("spy.refine.do_refine")
  r1 = r1_of_last_refinement()
  if r1 > 0.10:
    raise AssertionError("the control refinement gave R1 %.4f" % r1)
  return "R1 %.4f" % r1
