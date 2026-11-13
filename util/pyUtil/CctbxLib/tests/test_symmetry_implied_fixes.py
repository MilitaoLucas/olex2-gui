"""A fix on a Uij (or x/y/z) that the site symmetry already determines must not
freeze the atom's whole ADP (or site) in olex2.refine.

Needs cctbx, so run it under the Olex2/libtbx interpreter, not plain python:

    call <cctbx build>/setpaths.bat && libtbx.python tests/test_symmetry_implied_fixes.py

Case: E:/temp/anharm (13 Nov 2026), C2/c with Br1 on the 2-fold axis. The CIF
import fixed the symmetry-zero U12/U23 (no s.u.), iotbx.builders then turned
off grad_u_aniso for the whole atom, and the anharmonic tensor - variable only
with grad_u_aniso - stayed at 0 however strong the residual density.
"""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules.setdefault('olexFunctions', types.SimpleNamespace(OV=None))  # no Olex2 here

from cctbx import crystal
import cctbx_controller as cc

CELL = (12.3612, 11.8063, 7.122, 90, 99.506, 90)
SG = "hall: -C 2yc"
BR1 = (0.5, 0.916043, 0.75)
U = (0.0854, 0.04516, 0.1275, 0.0, 0.02837, 0.0)  # U11 U22 U33 U23 U13 U12
U12, U23, U11 = 11, 9, 6  # catom_var_name_*


def test_implied_indices():
  cs = crystal.symmetry(unit_cell=CELL, space_group_symbol=SG)
  # 2-fold along b: x and z, U12 and U23 follow from the rest
  assert cc.symmetry_implied_variables(cs, BR1) == {1, 3, 9, 11}
  assert cc.symmetry_implied_variables(cs, (0.1, 0.2, 0.3)) == set()


def _grad_u_aniso(fixed):
  atoms = [("Br1", BR1, 0.5, U, None, None, "Br",
            [{'index': i} for i in fixed] or None)]
  xs = cc.create_cctbx_xray_structure(CELL, SG, iter(atoms)).structure()
  return xs.scatterers()[0].flags.grad_u_aniso()


def test_builder_flags():
  assert _grad_u_aniso([U12, U23])           # symmetry-implied: still refined
  assert not _grad_u_aniso([U12, U23, U11])  # a real fix still fixes the ADP
  assert _grad_u_aniso([])


if __name__ == '__main__':
  test_implied_indices()
  test_builder_flags()
  print("OK")
