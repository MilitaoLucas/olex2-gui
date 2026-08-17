"""The CIF the structure is published from, and the fcf beside it.

This is the end of the pipeline: whatever is wrong here is what a referee
sees. The cases check content rather than that a file appeared - a cif with no
_refine_ls_R_factor is not a refined structure's cif, however well formed.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, has_hkl,
                            clear_r1, r1_of_last_refinement)

# What a cif has to carry to describe a structure at all. Olex2 writes the
# current names, so it is _space_group_name_H-M_alt and not the superseded
# _symmetry_space_group_name_H-M.
REQUIRED = [
  "_cell_length_a", "_cell_length_b", "_cell_length_c",
  "_cell_angle_alpha", "_space_group_name_H-M_alt",
  "_atom_site_label", "_atom_site_fract_x",
]


def register(suite):
  suite.run("cif", "CifCreate writes a describable structure", t_create, suite)
  suite.run("cif", "ACTA makes the refinement write a cif and an fcf",
            t_acta, suite)
  suite.run("cif", "CifMerge keeps the cif readable", t_merge, suite)
  suite.run("cif", "the cif reports the refinement", t_reports_refinement, suite)


def _sucrose(suite):
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  return folder


def _cif_path(folder):
  return os.path.join(folder, olx.FileName() + ".cif")


def _read(path):
  if not os.path.exists(path):
    raise AssertionError("no %s" % os.path.basename(path))
  return open(path, "r", errors="ignore").read()


def _blocks(text):
  return [l.split()[0] for l in text.splitlines()
          if l.lower().startswith("data_")]


def t_create(suite):
  folder = _sucrose(suite)
  macro("CifCreate")
  text = _read(_cif_path(folder))
  missing = [k for k in REQUIRED if k not in text]
  if missing:
    raise AssertionError("the cif has no %s" % ", ".join(missing))
  blocks = _blocks(text)
  if not blocks:
    raise AssertionError("the cif has no data_ block")
  return "%s, %d item(s) required all present" % (blocks[0], len(REQUIRED))


def t_acta(suite):
  """ACTA is how a SHELX-style refinement is asked for publication output.

  The fcf comes from the refinement, not from FcfCreate - which returns 0 here
  and writes nothing. Asserting on FcfCreate would have tested the wrong call.
  """
  folder = _sucrose(suite)
  if not has_hkl(folder):
    raise SkipTest("no hkl with the sucrose sample")
  OV.SetParam('snum.refinement.program', 'olex2.refine')
  OV.SetParam('snum.refinement.method', 'Gauss-Newton')
  OV.SetParam('snum.refinement.max_cycles', 2)
  macro("AddIns ACTA")
  clear_r1()
  macro("spy.refine.do_refine")

  fcf = _newest(folder, ".fcf")
  if fcf is None:
    raise AssertionError("the refinement wrote no fcf with ACTA set")
  n = _fcf_reflections(fcf)
  if n == 0:
    raise AssertionError("%s carries no reflections" % os.path.basename(fcf))
  return "%s, %d reflections, R1 %.4f" % (os.path.basename(fcf), n,
                                          r1_of_last_refinement())


def _newest(folder, ext):
  best, best_t = None, -1
  for root, dirs, files in os.walk(folder):
    for f in files:
      if f.lower().endswith(ext):
        p = os.path.join(root, f)
        t = os.path.getmtime(p)
        if t > best_t:
          best, best_t = p, t
  return best


def _fcf_reflections(path):
  n = 0
  started = False
  for line in open(path, "r", errors="ignore"):
    t = line.split()
    if not started:
      # the loop header ends and the data begin at the first h k l line
      if len(t) >= 4:
        try:
          int(t[0]); int(t[1]); int(t[2]); float(t[3])
          started = True
          n += 1
        except ValueError:
          continue
      continue
    if len(t) >= 4:
      try:
        int(t[0]); int(t[1]); int(t[2]); float(t[3])
        n += 1
      except ValueError:
        continue
  return n


def t_merge(suite):
  """CifMerge folds the metadata in; the result still has to be a cif."""
  folder = _sucrose(suite)
  macro("CifCreate")
  before = _read(_cif_path(folder))
  macro("CifMerge")
  after = _read(_cif_path(folder))
  if not _blocks(after):
    raise AssertionError("after CifMerge the cif has no data_ block")
  missing = [k for k in REQUIRED if k not in after]
  if missing:
    raise AssertionError("CifMerge dropped %s" % ", ".join(missing))
  return "%d -> %d bytes, %d block(s)" % (len(before), len(after),
                                          len(_blocks(after)))


def t_reports_refinement(suite):
  """The refinement's own cif has to carry the refinement's numbers.

  Not CifCreate's. CifCreate writes a structure-only cif - cell, symmetry,
  atoms, about 8 kB - while the refinement writes the full one, about 120 kB,
  with the _refine_ls_* block in it. Calling CifCreate after refining
  overwrites the second with the first, which is how this test first
  "discovered" that Olex2 reports no R factor.
  """
  folder = _sucrose(suite)
  if not has_hkl(folder):
    raise SkipTest("no hkl with the sucrose sample")
  OV.SetParam('snum.refinement.program', 'olex2.refine')
  OV.SetParam('snum.refinement.method', 'Gauss-Newton')
  OV.SetParam('snum.refinement.max_cycles', 2)
  clear_r1()
  macro("spy.refine.do_refine")
  r1 = r1_of_last_refinement()
  text = _read(_cif_path(folder))
  wanted = ["_refine_ls_R_factor_gt", "_refine_ls_number_reflns",
            "_refine_ls_number_parameters"]
  missing = [k for k in wanted if k not in text]
  if missing:
    raise AssertionError("the cif does not report %s" % ", ".join(missing))
  # and the value has to be the refinement's, not a leftover
  reported = _value(text, "_refine_ls_R_factor_gt")
  if reported is None:
    raise AssertionError("_refine_ls_R_factor_gt has no value")
  if abs(reported - r1) > 0.005:
    raise AssertionError("the cif reports R1 %.4f, the refinement gave %.4f"
                         % (reported, r1))
  return "cif R1 %.4f matches the refinement" % reported


def _value(text, key):
  for line in text.splitlines():
    t = line.split()
    if len(t) >= 2 and t[0] == key:
      try:
        return float(t[1].split("(")[0])
      except ValueError:
        return None
  return None
