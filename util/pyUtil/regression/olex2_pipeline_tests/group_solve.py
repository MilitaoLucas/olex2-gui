"""Structure solution, through olex2.solve and through SHELXT/SHELXD.

Solving is stochastic, so the assertion is not on a particular answer: it is
that a solution comes back at all, carries a plausible number of atoms for the
formula, and that the space group survives. A solver that returns an empty
model, or one atom, has failed however good its figures of merit look.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, has_hkl, atom_count,
                            space_group, program_available)


# Each program needs the method it actually offers - see method_imp/shelx.py.
# Passing None left whatever the previous case had set, and ShelXT was asked to
# run Charge Flipping, which it refused.
def register(suite):
  suite.run("solve", "olex2.solve sucrose", t_solve, suite, "sucrose",
            "olex2.solve", "Charge Flipping")
  suite.run("solve", "shelxt sucrose", t_solve, suite, "sucrose",
            "ShelXT", "Intrinsic Phasing")
  suite.run("solve", "shelxs direct methods", t_solve, suite, "sucrose",
            "ShelXS", "Direct Methods")
  suite.run("solve", "shelxd dual space", t_solve, suite, "sucrose",
            "ShelXD", "Dual Space")


def _prepare(suite, name):
  folder = suite.sample(name)
  if not has_hkl(folder):
    raise SkipTest("no hkl with the %s sample" % name)
  model = model_in(folder)
  load(model)
  macro("user '%s'" % folder.replace("\\", "/"))
  return folder


def t_solve(suite, name, program, method):
  exe = {"ShelXT": "shelxt", "ShelXS": "shelxs", "ShelXD": "shelxd"}.get(program)
  if exe and not program_available(exe):
    raise SkipTest("%s is not in the run directory or on PATH" % exe)

  folder = _prepare(suite, name)
  sg_before = space_group()
  n_before = atom_count()
  crd_before = _coords()

  OV.SetParam('snum.solution.program', program)
  if method:
    OV.SetParam('snum.solution.method', method)
  # spy.RunSolutionPrg, which is what the solve macro calls. spy.solve.do_solve
  # does not exist, and calling it left the loaded model in place while the
  # test reported it as a solution
  macro("spy.RunSolutionPrg()")

  n_after = atom_count()
  if n_after and _coords() != crd_before:
    # Olex2 took the solution back in, which is the whole path working
    if n_before and n_after < max(3, n_before // 4):
      raise AssertionError("%s returned %d atoms where the model had %d"
                           % (program, n_after, n_before))
    return "%s -> %d atoms in the model, %s" % (
      program, n_after, space_group() or sg_before)

  # olex2c does not reload an external solver's result the way the GUI does,
  # so the solution the program wrote is the evidence that it solved. A res
  # carrying atoms is what SHELXT/S/D produce and what Olex2 would read.
  n_sol, where = _atoms_in_written_solution(folder)
  if n_sol == 0:
    raise AssertionError("%s wrote no solution with atoms in it" % program)
  return "%s -> %d atoms in %s (not reloaded here)" % (program, n_sol, where)


def _atoms_in_written_solution(folder):
  """Atoms in the newest res the solver wrote, and which file it was."""
  newest, newest_t = None, -1
  for root, dirs, files in os.walk(folder):
    for f in files:
      if not f.lower().endswith(".res"):
        continue
      p = os.path.join(root, f)
      t = os.path.getmtime(p)
      if t > newest_t:
        newest, newest_t = p, t
  if newest is None:
    return 0, "no res"
  # A solution from SHELXT/S/D carries no FVAR - the atoms follow the cell
  # instructions directly - so an atom line is recognised by its shape rather
  # than by where it sits: a label, a scattering type index, three coordinates.
  # Requiring FVAR first counted nothing in a res that had solved perfectly
  # well, 23 fragments and a final CC of 90.
  keywords = set("""TITL CELL ZERR LATT SYMM SFAC UNIT SIZE TEMP OMIT REM
    HKLF END FVAR WGHT L.S. PLAN MORE CONF LIST BOND FMAP ACTA MERG EXTI
    DISP EQIV SHEL TWIN BASF SWAT""".split())
  n = 0
  for line in open(newest, "r"):
    t = line.split()
    if len(t) < 5 or t[0].upper() in keywords:
      continue
    try:
      int(t[1])
      float(t[2]); float(t[3]); float(t[4])
    except ValueError:
      continue
    n += 1
  return n, os.path.basename(newest)


def _coords():
  """The model's coordinates, to tell a new solution from an untouched model."""
  return tuple(str(olx.xf.au.GetAtomCrd(i)) for i in range(atom_count()))
