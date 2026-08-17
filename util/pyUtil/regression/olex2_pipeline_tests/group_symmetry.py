"""Space group handling: changing it, standardising the setting, testing it.

Several of these rewrite the structure rather than report on it - SGE replaced
sucrose's 45 atoms with 26 and wrote a fresh ins, hkl and cif - so every case
takes its own copy of the sample and says what it expected to change.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, atom_count,
                            real_atom_count, space_group, deleted,
                            r1_of_last_refinement, clear_r1, has_hkl)


def register(suite):
  suite.run("symmetry", "the space group is reported", t_report, suite)
  suite.run("symmetry", "changesg P1 drops the symmetry", t_changesg, suite)
  suite.run("symmetry", "standardise moves without losing atoms", t_std, suite)
  suite.run("symmetry", "addse adds a symmetry element", t_addse, suite)
  suite.run("symmetry", "changing the group and back is reversible",
            t_round_trip, suite)
  suite.run("symmetry", "symmetry queries are accepted", t_queries, suite)


def _sucrose(suite):
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  return folder


def _sg():
  """The space group symbol, with the html subscripting taken back out."""
  s = str(space_group() or "")
  for a, b in (("<sub>", ""), ("</sub>", ""), ("<i>", ""), ("</i>", "")):
    s = s.replace(a, b)
  return s.strip()


def t_report(suite):
  _sucrose(suite)
  sg = _sg()
  if not sg:
    raise AssertionError("no space group symbol")
  n = int(olx.xf.au.GetCellSymm()) if str(olx.xf.au.GetCellSymm()).isdigit() \
    else None
  return "%s%s" % (sg, "" if n is None else " (%s)" % n)


def t_changesg(suite):
  """Going to P1 has to change the symbol, and keep the atoms.

  sucrose is P2(1) with 45 atoms in the asymmetric unit; in P1 it is still 45,
  because the asymmetric unit of the *model* is what is held, not the cell
  contents. What must change is the symbol.
  """
  _sucrose(suite)
  before, n_before = _sg(), real_atom_count()
  if before.upper() in ("P1", "P 1"):
    raise SkipTest("the sample is already P1")
  macro("changesg P1")
  after, n_after = _sg(), real_atom_count()
  if after == before:
    raise AssertionError("changesg P1 left the space group at %s" % before)
  if after.replace(" ", "").upper() != "P1":
    raise AssertionError("changesg P1 gave %r" % after)
  if n_after == 0:
    raise AssertionError("changesg P1 emptied the model")
  return "%s (%d atoms) -> %s (%d atoms)" % (before, n_before, after, n_after)


def t_std(suite):
  """Standardising the setting moves atoms and keeps every one of them."""
  _sucrose(suite)
  before, n_before = _coords(), real_atom_count()
  macro("standardise")
  after, n_after = _coords(), real_atom_count()
  if n_after != n_before:
    raise AssertionError("standardise went from %d to %d atoms"
                         % (n_before, n_after))
  if after == before:
    raise SkipTest("the sample is already in the standard setting")
  moved = sum(1 for a, b in zip(before, after) if a != b)
  return "%d of %d atoms moved, none lost" % (moved, n_after)


def t_addse(suite):
  """Adding a symmetry element changes the group the model is held in."""
  _sucrose(suite)
  before = _sg()
  if olex.m("addse -1") == 0:
    raise SkipTest("addse -1 was refused for this structure")
  after = _sg()
  if after == before:
    raise AssertionError("addse -1 left the space group at %s" % before)
  return "%s -> %s" % (before, after)


def t_round_trip(suite):
  """Changing the space group and changing back must restore the structure.

  Note what is *not* asserted here. Going to P1 does not expand the cell
  contents - the asymmetric unit stays at 45 atoms, so in P1 the cell holds
  half of what P2(1) held and R1 goes from 0.028 to 0.41. That is Olex2 being
  right, and an earlier version of this case called it a failure.

  What has to hold is reversibility: back in the original group, with the same
  data, the refinement has to return to where it started.
  """
  folder = _sucrose(suite)
  if not has_hkl(folder):
    raise SkipTest("no hkl with the sucrose sample")
  OV.SetParam('snum.refinement.program', 'olex2.refine')
  OV.SetParam('snum.refinement.method', 'Gauss-Newton')
  OV.SetParam('snum.refinement.max_cycles', 3)
  original = _sg()
  if original.upper().replace(" ", "") == "P1":
    raise SkipTest("the sample is already P1")
  clear_r1()
  macro("spy.refine.do_refine")
  r_before = r1_of_last_refinement()

  macro("changesg P1")
  if _sg().replace(" ", "").upper() != "P1":
    raise AssertionError("changesg P1 gave %r" % _sg())
  macro("changesg %s" % original)
  restored = _sg()
  if restored != original:
    raise AssertionError("changing back gave %r, started at %r"
                         % (restored, original))
  clear_r1()
  macro("spy.refine.do_refine")
  r_after = r1_of_last_refinement()
  if abs(r_after - r_before) > 0.01:
    raise AssertionError("R1 %.4f before the round trip, %.4f after"
                         % (r_before, r_after))
  return "%s -> P1 -> %s, R1 %.4f -> %.4f" % (original, restored,
                                              r_before, r_after)


def t_queries(suite):
  """Symmetry queries must answer rather than refuse."""
  _sucrose(suite)
  label = None
  for i in range(int(atom_count())):
    if not deleted(i):
      label = olx.xf.au.GetAtomName(i)
      break
  refused = []
  for name, args in (("TestSymm", ()), ("Degen", (label,)), ("SGInfo", ()),
                     ("LstSymm", ())):
    fn = getattr(olx, name, None)
    if fn is None:
      refused.append("%s (not exported)" % name)
      continue
    try:
      v = fn(*args)
    except Exception as e:
      refused.append("%s raised %s" % (name, str(e).split("\n")[0][:40]))
      continue
    if isinstance(v, int) and not isinstance(v, bool) and v == 0:
      refused.append("%s returned 0" % name)
  if refused:
    raise AssertionError("; ".join(refused))
  return "4 accepted"


def _coords():
  return tuple(str(olx.xf.au.GetAtomCrd(i)) for i in range(int(atom_count()))
               if not deleted(i))
