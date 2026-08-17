"""Reflection-data macros, checked against the data they produce.

The hkl is the one input a refinement cannot be right without, and most of
these macros rewrite it in place. So each case works on its own copy of the
sample and counts reflections in the file afterwards - `olex.m` returning 1
says nothing about whether a merge merged anything.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, has_hkl,
                            r1_of_last_refinement, clear_r1)


def register(suite):
  suite.run("hkl", "HKLF reports the data format", t_hklf, suite)
  suite.run("hkl", "hklmerge merges to unique reflections", t_merge, suite)
  suite.run("hkl", "omit and shel reach the model", t_omit_shel, suite)
  suite.run("hkl", "wilson writes its statistics", t_wilson, suite)
  suite.run("hkl", "hklbrush writes a brushed file", t_brush, suite)
  suite.run("hkl", "a merged file still refines", t_refine_after_merge, suite)


def _sucrose(suite):
  folder = suite.sample("sucrose")
  if not has_hkl(folder):
    raise SkipTest("no hkl with the sucrose sample")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  return folder


def n_reflections(path):
  """Reflections in a SHELX hkl: h k l F sigma, terminated by 0 0 0."""
  n = 0
  for line in open(path, "r", errors="ignore"):
    t = line.split()
    if len(t) < 5:
      continue
    try:
      h, k, l = int(t[0]), int(t[1]), int(t[2])
    except ValueError:
      continue
    if h == 0 and k == 0 and l == 0:
      break
    n += 1
  return n


def t_hklf(suite):
  _sucrose(suite)
  v = str(olx.HKLF()).strip()
  if v not in ("3", "4", "5", "6"):
    raise AssertionError("HKLF reported %r, which is not a SHELX format" % v)
  return "HKLF %s" % v


def t_merge(suite):
  """Merging must actually reduce the file to unique reflections.

  sucrose goes 13368 -> 2578 here. A merge that returns 1 and leaves the file
  alone looks identical in the log, which is why the count is the assertion.
  """
  _sucrose(suite)
  src = olx.HKLSrc()
  if not os.path.exists(src):
    raise SkipTest("HKLSrc names no file")
  before = n_reflections(src)
  macro("hklmerge")
  after = n_reflections(olx.HKLSrc())
  if after >= before:
    raise AssertionError("hklmerge left %d reflections, was %d" % (after, before))
  if after == 0:
    raise AssertionError("hklmerge emptied the file")
  return "%d -> %d reflections" % (before, after)


def t_omit_shel(suite):
  """OMIT and SHEL are model instructions, so the written ins carries them."""
  folder = _sucrose(suite)
  macro("omit 2 3 4")
  macro("shel 10 0.8")
  out = os.path.join(folder, "hkl_chk.ins").replace("\\", "/")
  macro("file '%s'" % out)
  text = open(out, "r", errors="ignore").read().upper()
  missing = [k for k in ("OMIT 2 3 4", "SHEL 10 0.8") if k not in text]
  if missing:
    raise AssertionError("not written: %s" % ", ".join(missing))
  return "OMIT and SHEL written"


def t_wilson(suite):
  """Wilson statistics, which the macro writes beside the structure."""
  folder = _sucrose(suite)
  before = _csvs(folder)
  olx.Wilson()
  new = _csvs(folder) - before
  if not new:
    raise AssertionError("wilson wrote no statistics file")
  path = sorted(new)[0]
  rows = sum(1 for line in open(path, "r", errors="ignore") if line.strip())
  if rows < 2:
    raise AssertionError("%s has %d row(s)" % (os.path.basename(path), rows))
  return "%s, %d rows" % (os.path.basename(path), rows)


def _csvs(folder):
  found = set()
  for root, dirs, files in os.walk(folder):
    for f in files:
      if f.lower().endswith(".csv"):
        found.add(os.path.join(root, f))
  return found


def t_brush(suite):
  folder = _sucrose(suite)
  macro("hklbrush")
  brushed = os.path.join(folder, "brushed.hkl")
  if not os.path.exists(brushed):
    raise AssertionError("hklbrush wrote no brushed.hkl")
  n = n_reflections(brushed)
  if n == 0:
    raise AssertionError("brushed.hkl carries no reflections")
  return "brushed.hkl, %d reflections" % n


def t_refine_after_merge(suite):
  """The point of merging is to refine against the result."""
  _sucrose(suite)
  OV.SetParam('snum.refinement.program', 'olex2.refine')
  OV.SetParam('snum.refinement.method', 'Gauss-Newton')
  OV.SetParam('snum.refinement.max_cycles', 3)
  macro("hklmerge")
  clear_r1()
  macro("spy.refine.do_refine")
  r1 = r1_of_last_refinement()
  if r1 > 0.10:
    raise AssertionError("R1 %.4f after merging" % r1)
  return "R1 %.4f on merged data" % r1
