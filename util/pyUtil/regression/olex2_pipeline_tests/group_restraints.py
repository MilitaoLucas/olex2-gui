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
  for name, build in DEGENERATE:
    suite.run("restraints", "degenerate %s is survivable" % name,
              t_degenerate, name, build)


def _degenerate_structure(sites):
  """A P1 box with the given Cartesian sites, all coordinates refinable."""
  from cctbx import crystal, xray
  cs = crystal.symmetry(unit_cell=(50, 50, 50, 90, 90, 90),
                        space_group_symbol="P1")
  xs = xray.structure(crystal_symmetry=cs)
  for i, s in enumerate(sites):
    sc = xray.scatterer(label="C%d" % i, scattering_type="C",
                        site=[c / 50.0 for c in s])
    sc.flags.set_grad_site(True)
    xs.add_scatterer(sc)
  return xs


def _row(xs, **proxies):
  from cctbx import geometry_restraints as geom
  from smtbx.refinement import restraints as smtbx_restraints
  mgr = smtbx_restraints.manager(**proxies)
  eqns = mgr.build_linearised_eqns(xs, xs.parameter_map())
  return list(eqns.design_matrix.as_dense_matrix())


def _coplanar_chirality():
  from cctbx import geometry_restraints as geom
  xs = _degenerate_structure([(0, 0, 0), (1., 0, 0), (0, 1., 0), (0, 0, 0)])
  p = geom.chirality_proxy((0, 1, 2, 3), volume_ideal=0., both_signs=False,
                           weight=100)
  return _row(xs, chirality_proxies=geom.shared_chirality_proxy([p]))


def _collinear_dihedral():
  from cctbx import geometry_restraints as geom
  xs = _degenerate_structure([(0, 1e-8, 0), (0, 0, 0), (1., 0, 0),
                              (1., 1e-8, 0.5)])
  p = geom.dihedral_proxy((0, 1, 2, 3), angle_ideal=0., weight=100)
  return _row(xs, dihedral_proxies=geom.shared_dihedral_proxy([p]))


def _coincident_sadi():
  from cctbx import geometry_restraints as geom
  xs = _degenerate_structure([(0, 0, 0), (1.5, 0, 0), (5., 0, 0), (5., 0, 0)])
  p = geom.bond_similarity_proxy(i_seqs=[(0, 1), (2, 3)], weights=(1., 1.))
  return _row(xs, bond_similarity_proxies=
              geom.shared_bond_similarity_proxy([p]))


# Geometries that used to poison the normal matrix, with the ceiling a healthy
# row is allowed to reach. A chirality restraint on coplanar sites divided 0
# by 0; a SADI pair on one point divided by a zero length; a dihedral about an
# axis its terminal atom sits on returned a row 1e8 times everything else.
DEGENERATE = [
  ("coplanar chirality (FLAT)", _coplanar_chirality),
  ("collinear dihedral", _collinear_dihedral),
  ("coincident SADI pair", _coincident_sadi),
]
MAX_HEALTHY_ROW = 1e6


def t_degenerate(name, build):
  """A degenerate restraint must give a usable row or none, never a poisoned one.

  This asks the cctbx that Olex2 actually loads, not the one in the source
  tree - the fixes live in compiled extensions, and the bundle under
  rundir-py3/cctbx is not version controlled, so a rebuild from an older
  source silently takes them away again. That is the regression worth
  catching, and it is why this builds the row directly instead of refining:
  the check costs milliseconds and still fails if the deployed binary is old.
  """
  try:
    row = build()
  except ImportError as e:
    raise SkipTest("cctbx is not importable here: %s" % e)
  nan = [v for v in row if v != v]
  inf = [v for v in row if v == v and abs(v) == float("inf")]
  if nan:
    raise AssertionError("%d NaN in the design matrix - this cctbx predates "
                         "the fix" % len(nan))
  if inf:
    raise AssertionError("%d inf in the design matrix" % len(inf))
  biggest = max((abs(v) for v in row), default=0.0)
  if biggest > MAX_HEALTHY_ROW:
    raise AssertionError(
      "largest entry %.3g, which the normal matrix cannot carry" % biggest)
  return "no NaN, largest entry %.3g" % biggest


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
