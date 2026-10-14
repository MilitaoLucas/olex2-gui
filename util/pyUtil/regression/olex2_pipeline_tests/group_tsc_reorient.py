"""A table made before the model was moved by symmetry still fits afterwards.

move, compaq, sgen -m, transform and inv put atoms on a symmetry image of
their sites. The table's values are atom-centred, so a translation needs
nothing, but the rotation part turns each atom's density with it: the columns
of those atoms must become f(h.R) (tsc_scatterer_resync.reorient_moved_columns).
Before that, a refinement against such a table either stopped on the ids or
ran with the moved atoms spherical, and R1 rose by about the HAR-IAM gap.

Each case makes a table with one aspherical cycle, refines against the table
until it sits still, applies the operation and refines again. The R1 must come
back to the one before the move. One case also recomputes the table at the new
position: rotating must agree with recalculating.

  OLEX2_TEST_BACKENDS  the backend that makes the table, default pTB
"""
from __future__ import absolute_import, division, print_function

import hashlib
import os

import olx
from variableFunctions import nsa2_set_param

from pipeline_tests import macro, clear_r1, r1_of_last_refinement, _r1_raw
from group_nosphera2 import _refine_capturing
from group_nsa2_matrix import (_prepare, _set_aspherical, _defaults_for,
                               _available, _aspherical_run)

GROUP = "tsc_reorient"
SCREW = "transform -1 0 0 0 1 0 0 0 -1 0 0.5 0"         # -x,y+1/2,-z of P2(1)
C2C_INV = "transform -1 0 0 0 -1 0 0 0 -1 0.5 0.5 0"   # -x+1/2,-y+1/2,-z of C2/c
NOT_SYMMETRY = "transform 0 0 1 0 1 0 -1 0 0 0 0 0"    # a quarter turn P2(1) does not have


def register(suite):
  backend = (os.environ.get("OLEX2_TEST_BACKENDS", "") or "pTB").split(",")[0].strip()
  suite.run(GROUP, "2(1) screw, rotated = recalculated", t_screw, suite, backend)
  suite.run(GROUP, "inv -f in P2(1)", t_inversion, suite, backend)
  suite.run(GROUP, "inversion + C centring in C2/c", t_centric, suite, backend)
  suite.run(GROUP, "a rotation that is no symmetry is refused", t_refused, suite, backend)


def _table_ready(suite, sample, backend):
  """A table, chosen as the source, and a model refined against it to rest."""
  folder, r_sph = _prepare(suite, sample)
  source = _available(backend)
  _set_aspherical(sample, source)
  _defaults_for(backend)
  cycles, tsc, said = _aspherical_run(sample, backend, source, folder)
  table = os.path.basename(tsc)
  nsa2_set_param('source', table)
  nsa2_set_param('file', table)
  for _ in range(2):
    clear_r1()
    _refine_capturing()
  return folder, tsc, r1_of_last_refinement(), source


def _first_site():
  return [float(v) for v in olx.xf.au.GetAtomCrd(0).split(',')]


def _move(cmd):
  before = _first_site()
  macro(cmd)
  after = _first_site()
  if max(abs(a - b) for a, b in zip(before, after)) < 0.05:
    raise AssertionError("%r did not move the first atom" % cmd)


def _md5(path):
  with open(path, 'rb') as f:
    return hashlib.md5(f.read()).hexdigest()


def _refine_moved(cmd, tsc, r_before, tol):
  _move(cmd)
  clear_r1()
  said = _refine_capturing()
  if "rotated with them" not in said:
    raise AssertionError("no column was rotated after %r" % cmd)
  if not os.path.exists(tsc + ".bak"):
    raise AssertionError("the table before the rotation was not kept")
  r_after = r1_of_last_refinement()
  if abs(r_after - r_before) > tol:
    raise AssertionError("R1 %.5f after %r, %.5f before" % (r_after, cmd, r_before))
  return r_after


def _recalculated(sample, backend, source, folder, r_after):
  """R1 with a table made where the model now is: rotating must agree."""
  _set_aspherical(sample, source)
  _defaults_for(backend)
  _aspherical_run(sample, backend, source, folder)
  r_fresh = r1_of_last_refinement()
  if abs(r_fresh - r_after) > 2e-4:
    raise AssertionError("rotated table R1 %.5f, recalculated %.5f" % (r_after, r_fresh))
  return r_fresh


def t_screw(suite, backend):
  folder, tsc, r_before, source = _table_ready(suite, "sucrose", backend)
  r_after = _refine_moved(SCREW, tsc, r_before, 2e-4)
  r_fresh = _recalculated("sucrose", backend, source, folder, r_after)
  return "R1 %.5f before, %.5f rotated, %.5f recalculated" % (r_before, r_after, r_fresh)


def t_inversion(suite, backend):
  folder, tsc, r_before, source = _table_ready(suite, "sucrose", backend)
  # the other hand differs only through f'' of C and O
  r_after = _refine_moved("inv -f", tsc, r_before, 1e-3)
  r_fresh = _recalculated("sucrose", backend, source, folder, r_after)
  return "R1 %.5f before, %.5f after inv -f, %.5f recalculated" % (r_before, r_after, r_fresh)


def t_centric(suite, backend):
  folder, tsc, r_before, source = _table_ready(suite, "183", backend)
  r_after = _refine_moved(C2C_INV, tsc, r_before, 2e-4)
  return "R1 %.5f before, %.5f after -x+1/2,-y+1/2,-z" % (r_before, r_after)


def t_refused(suite, backend):
  folder, tsc, r_before, source = _table_ready(suite, "sucrose", backend)
  digest = _md5(tsc)
  _move(NOT_SYMMETRY)
  clear_r1()
  said = _refine_capturing()
  if "rotated with them" in said:
    raise AssertionError("a quarter turn was taken for a symmetry move")
  if _md5(tsc) != digest:
    raise AssertionError("the table was rewritten for a move that is no symmetry")
  if _r1_raw() is not None:
    raise AssertionError("the refinement ran against a table that no longer fits")
  return "refused, table untouched"
