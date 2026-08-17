"""Macros and functions, exercised against a real loaded structure.

These are the calls the rest of Olex2 and every script are built on. They are
cheap, so they run first: if the model cannot be loaded or the cell cannot be
read, nothing further in the suite means anything.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, atom_count, space_group,
                            real_atom_count, deleted)


def register(suite):
  folder = suite.sample("sucrose")
  model = model_in(folder)
  suite.run("macros", "load a structure", t_load, model)
  suite.run("macros", "cell and space group", t_cell)
  suite.run("macros", "atom count and labels", t_atoms)
  suite.run("macros", "Ins reads an instruction", t_ins)
  suite.run("macros", "AddIns and DelIns", t_add_del_ins)
  suite.run("macros", "HKLSrc points at the data", t_hklsrc)
  suite.run("macros", "file writes a readable model", t_file_roundtrip, suite)
  suite.run("macros", "phil get and set round trip", t_phil)
  suite.run("macros", "atom references resolve", t_atom_refs)
  suite.run("macros", "HAdd puts the hydrogens back", t_hadd, suite)
  suite.run("macros", "CifCreate writes a cif", t_cif_create, suite)
  suite.run("macros", "solvent mask runs", t_mask, suite)


def t_load(model):
  n = load(model)
  return "%d atoms" % n


def t_cell():
  a = float(olx.Cell('a'))
  v = float(olx.xf.au.GetCellVolume())
  sg = space_group()
  if a <= 0 or v <= 0:
    raise AssertionError("cell a=%r volume=%r" % (a, v))
  if not sg:
    raise AssertionError("no space group name")
  return "a=%.4f V=%.1f %s" % (a, v, sg)


def t_atoms():
  n = int(atom_count())
  if n <= 0:
    raise AssertionError("no atoms")
  label = olx.xf.au.GetAtomName(0)
  if not label:
    raise AssertionError("atom 0 has no label")
  t = olx.xf.au.GetAtomType(0)
  return "%d atoms, first %s (%s)" % (n, label, t)


def t_ins():
  # every SHELX model has a cell, so this is present or the reader is wrong
  # WGHT rather than CELL: the cell is a header record, not an instruction
  v = olx.Ins("WGHT")
  if not v or v == "n/a":
    raise AssertionError("Ins('WGHT') gave %r" % v)
  return "WGHT -> %s" % v.split()[0]


def t_add_del_ins():
  """AddIns then DelIns must leave the model as it was found."""
  before = olx.Ins("ACTA")
  macro("AddIns ACTA")
  after = olx.Ins("ACTA")
  if after == "n/a":
    raise AssertionError("AddIns ACTA did not take")
  macro("DelIns ACTA")
  end = olx.Ins("ACTA")
  if end != "n/a":
    raise AssertionError("DelIns ACTA left %r" % end)
  return "added and removed (was %r)" % before


def t_hklsrc():
  src = olx.HKLSrc()
  if not src:
    raise SkipTest("no reflection file attached to this sample")
  if not os.path.exists(src):
    raise AssertionError("HKLSrc names a file that is not there: %s" % src)
  return os.path.basename(src)


def t_file_roundtrip(suite):
  """Write the model out and read it back; the atom count must survive."""
  n_before = real_atom_count()
  out = os.path.join(suite.scratch, "roundtrip.ins").replace("\\", "/")
  macro("file '%s'" % out)
  if not os.path.exists(out):
    raise AssertionError("file did not write %s" % out)
  macro("@reap '%s'" % out)
  n_after = real_atom_count()
  if n_after != n_before:
    raise AssertionError("%d atoms written, %d read back" % (n_before, n_after))
  return "%d real atoms survived" % n_after


def t_phil():
  key = "snum.refinement.max_cycles"
  old = OV.GetParam(key)
  OV.SetParam(key, 7)
  got = OV.GetParam(key)
  OV.SetParam(key, old)
  if int(got) != 7:
    raise AssertionError("set %s to 7 and read back %r" % (key, got))
  return "%s set and restored (was %r)" % (key, old)


def t_atom_refs():
  """The atom reference grammar the macros share."""
  n = int(atom_count())
  name = olx.xf.au.GetAtomName(0)
  # through the macro layer: olx has no Sel of its own. The point is that the
  # reference grammar parses and the call does not raise
  macro("sel atoms %s" % name)
  macro("sel -u")
  return "%d atoms, referenced %s" % (n, name)


def _n_hydrogens():
  # deleted atoms keep their index and their type, so they have to be excluded
  # explicitly or `kill $H` looks like it did nothing
  return sum(1 for i in range(int(atom_count()))
             if olx.xf.au.GetAtomType(i) == "H" and not deleted(i))


def t_hadd(suite):
  """Remove the hydrogens and let Olex2 place them again.

  This is connectivity, geometry and the AFIX machinery in one call, and it is
  what every structure goes through. Counting them back is the assertion: a
  HAdd that runs and places none leaves a model that refines to nonsense.
  """
  load(model_in(suite.sample("sucrose")))
  n_before = _n_hydrogens()
  if not n_before:
    raise SkipTest("the sucrose sample carries no hydrogens to remove")
  macro("kill $H")
  if _n_hydrogens():
    raise AssertionError("kill $H left %d hydrogens" % _n_hydrogens())
  macro("HAdd")
  n_after = _n_hydrogens()
  if n_after < n_before:
    raise AssertionError("%d hydrogens removed, %d placed back"
                         % (n_before, n_after))
  return "%d removed, %d placed" % (n_before, n_after)


def t_cif_create(suite):
  """The cif Olex2 writes must carry the cell it was asked about."""
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  macro("CifCreate")
  cif = os.path.join(folder, olx.FileName() + ".cif")
  if not os.path.exists(cif):
    raise AssertionError("CifCreate wrote no %s" % os.path.basename(cif))
  text = open(cif, "r", errors="ignore").read()
  for item in ("_cell_length_a", "_space_group_name_H-M_alt", "_atom_site_label"):
    if item not in text:
      raise AssertionError("the cif has no %s" % item)
  return "%s, %d bytes" % (os.path.basename(cif), len(text))


def t_mask(suite):
  """The solvent mask, which protein refinement depends on.

  Sucrose has no solvent to find, so asserting on the .sqf would assert on
  there being voids - and "no voids" and "never ran" would look the same. The
  mask object itself is the effect: OlexCctbxMasks leaves it on olx, so a run
  that did not happen has none.
  """
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  olx.current_mask = None
  macro("spy.OlexCctbxMasks()")
  mask = getattr(olx, "current_mask", None)
  if mask is None:
    raise AssertionError("the mask calculation left no mask")
  n = mask.flood_fill.n_voids()
  return "%d void(s) found" % n
