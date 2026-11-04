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
  suite.run("cif", "an N-Beam refinement cites its paper", t_ed_nbeam_citation, suite)


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
  # output_fcf writes nothing without a LIST, and the sample has none
  macro("AddIns LIST 4")
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
  # the refinement writes its cif only with ACTA, which the sample does not
  # carry (the GUI adds it from user.auto_insert_user_ins when set there)
  macro("AddIns ACTA")
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


def t_ed_nbeam_citation(suite):
  """The N-Beam paper: in the CIF while dynamical, and a link in the notification.

  The state is forced, because a real N-Beam refinement needs the licensed
  plugin and ED data; what is tested is what follows from that state.
  """
  import CifInfo
  import RunPrg
  folder = _sucrose(suite)
  doi = CifInfo.ED_NBEAM_DOI
  def references():
    CifInfo.ExtractCifInfo(run=True)
    return OV.get_cif_item('_publ_section_references', '')
  is_ed, run, base_run = OV.IsEDRefinement, RunPrg.RunRefinementPrg.run, RunPrg.RunPrg.run
  try:
    OV.IsEDRefinement = lambda: False
    if doi in references():
      raise AssertionError("a kinematic refinement cites the N-Beam paper")
    OV.IsEDRefinement = lambda: True
    refs = references()
    if refs.count(doi) != 1:
      raise AssertionError("expected the N-Beam paper once in: %s" % refs)
    if "Pr\\'ochniak" not in refs:
      raise AssertionError("the author's accent is lost: %s" % refs)
    # an entry typed otherwise (say without the accent, with pages) gives way to the current text
    OV.set_cif_item('_publ_section_references', refs.replace(
      "doi:%s" % doi, "1-12").replace("Pr\\'ochniak", "Prochniak"))
    refs = references()
    if refs.count("ochniak") != 1 or doi not in refs or "Pr\\'ochniak" not in refs:
      raise AssertionError("the old entry was not replaced: %s" % refs)
    OV.IsEDRefinement = lambda: False
    if "ochniak" in references():
      raise AssertionError("the N-Beam paper stayed after going kinematic")

    OV.IsEDRefinement = lambda: True
    RunPrg.RunRefinementPrg.run = lambda self: None
    RunPrg.RunRefinementPrg()
    with open(os.path.join(OV.StrDir(), "refinement.check")) as f:
      note = f.read()
    if "Please cite our <a href='shell https://doi.org/%s'>N-Beam paper</a>" % doi not in note:
      raise AssertionError("no link to the paper in the notification: %s" % note)
    OV.IsEDRefinement = lambda: False
    RunPrg.RunRefinementPrg()
    with open(os.path.join(OV.StrDir(), "refinement.check")) as f:
      note = f.read()
    if doi in note:
      raise AssertionError("a kinematic refinement's notification cites the paper: %s" % note)

    # advice on a refinement that finished keeps the citation; an error does not get one
    OV.IsEDRefinement = lambda: True
    for failed_note, cited in (("Warning: advice", True), ("Error: stopped", False)):
      RunPrg.RunRefinementPrg.run = lambda self: self.refinement_has_failed.append(failed_note)
      RunPrg.RunRefinementPrg()
      with open(os.path.join(OV.StrDir(), "refinement.check")) as f:
        note = f.read()
      if (failed_note not in note) or (("N-Beam paper" in note) != cited):
        raise AssertionError("with the note '%s' the notification reads: %s" % (failed_note, note))

    # a crash is a failure in the notification, not "finished" with a citation
    RunPrg.RunRefinementPrg.run = run
    def crash(self):
      raise RuntimeError("crash for the test")
    RunPrg.RunPrg.run = crash
    RunPrg.RunRefinementPrg()
    with open(os.path.join(OV.StrDir(), "refinement.check")) as f:
      note = f.read()
    if "Refinement failed" not in note or "cite" in note:
      raise AssertionError("a crashed refinement's notification: %s" % note)
  finally:
    OV.IsEDRefinement = is_ed
    RunPrg.RunRefinementPrg.run = run
    RunPrg.RunPrg.run = base_run
    references()
  return "added, replaced, dropped; notification links %s" % doi
