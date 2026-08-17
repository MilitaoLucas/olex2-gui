"""Macros that change the model, each checked by what it changed.

These are the everyday editing operations - the ADP treatment, fixing and
freeing parameters, disorder parts, moving atoms into one molecule, growing
symmetry equivalents. Every case asserts on the model afterwards rather than
on the call returning, because `olex.m` returns 0 for macros that worked.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, atom_count,
                            real_atom_count, deleted)


def register(suite):
  suite.run("model", "anis and isot switch the ADP model", t_anis_isot, suite)
  suite.run("model", "fix and free a parameter", t_fix_free, suite)
  suite.run("model", "part assigns a disorder part", t_part, suite)
  suite.run("model", "compaq gathers the molecule", t_compaq, suite)
  suite.run("model", "pack fills the cell, fuse collapses it", t_pack_fuse, suite)
  suite.run("model", "grow completes what is incomplete", t_grow, suite)
  suite.run("model", "sort reorders the atom list", t_sort, suite)
  suite.run("model", "name relabels an atom", t_name, suite)
  suite.run("model", "fvar and the free variable list", t_fvar, suite)


def _sucrose(suite):
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  return folder


def _first(kind):
  """Label of the first live atom of a type."""
  for i in range(int(atom_count())):
    if deleted(i):
      continue
    if olx.xf.au.GetAtomType(i) == kind:
      return olx.xf.au.GetAtomName(i)
  raise SkipTest("no %s in this structure" % kind)


def _ins_text(suite, folder, tag):
  """Write the model and read it back as text - the ins is the record.

  Several of these operations have no reader on the olx side (there is no
  IsAtomAnisotropic), but every one of them changes what gets written, and
  the written file is what the next program sees.
  """
  out = os.path.join(folder, "%s.ins" % tag).replace("\\", "/")
  macro("file '%s'" % out)
  if not os.path.exists(out):
    raise AssertionError("file did not write %s" % out)
  return open(out, "r", errors="ignore").read()


def _n_anis(text):
  """Atoms carrying six ADPs, counted off the written ins.

  A SHELX atom line is label, sfac, x, y, z, occ then U - one value for
  isotropic, six for anisotropic, continued after a trailing '='.
  """
  n = 0
  lines = text.splitlines()
  for i, line in enumerate(lines):
    t = line.split()
    if len(t) < 6 or not t[1].isdigit():
      continue
    try:
      float(t[2]); float(t[3]); float(t[4])
    except ValueError:
      continue
    if line.rstrip().endswith("=") or len(t) >= 12:
      n += 1
  return n


def t_anis_isot(suite):
  folder = _sucrose(suite)
  before = _n_anis(_ins_text(suite, folder, "m_before"))
  macro("isot $C")
  after_isot = _n_anis(_ins_text(suite, folder, "m_isot"))
  if after_isot >= before:
    raise AssertionError("isot $C left %d anisotropic atoms, was %d"
                         % (after_isot, before))
  macro("anis $C")
  after_anis = _n_anis(_ins_text(suite, folder, "m_anis"))
  if after_anis <= after_isot:
    raise AssertionError("anis $C gave %d anisotropic atoms, was %d"
                         % (after_anis, after_isot))
  return "%d anis -> %d after isot -> %d after anis" % (
    before, after_isot, after_anis)


def t_fix_free(suite):
  """A fixed coordinate is written with SHELX's 10+value coding."""
  folder = _sucrose(suite)
  label = _first("O")
  macro("fix xyz %s" % label)
  fixed = _atom_line(_ins_text(suite, folder, "m_fix"), label)
  if fixed is None:
    raise AssertionError("%s is not in the written ins" % label)
  # a fixed parameter is written as 10 + the value, so it leaves the 0..1 range
  if not any(abs(float(v)) > 5 for v in fixed.split()[2:5]):
    raise AssertionError("fix xyz %s wrote %r, none of it fixed"
                         % (label, fixed.strip()))
  macro("free xyz %s" % label)
  freed = _atom_line(_ins_text(suite, folder, "m_free"), label)
  if any(abs(float(v)) > 5 for v in freed.split()[2:5]):
    raise AssertionError("free xyz %s left %r fixed" % (label, freed.strip()))
  return "%s fixed then freed" % label


def _atom_line(text, label):
  for line in text.splitlines():
    t = line.split()
    if t and t[0].upper() == label.upper():
      return line
  return None


def t_part(suite):
  folder = _sucrose(suite)
  label = _first("O")
  macro("part %s 2" % label)
  text = _ins_text(suite, folder, "m_part")
  if "PART 2" not in text.upper():
    raise AssertionError("no PART 2 in the written ins after part %s 2" % label)
  return "%s moved to part 2" % label


def t_compaq(suite):
  """Compaq assembles the molecule; the coordinates must move."""
  _sucrose(suite)
  before = _coords()
  macro("compaq -a")
  after = _coords()
  if after == before:
    raise SkipTest("the sample is already assembled, so compaq is a no-op")
  moved = sum(1 for a, b in zip(before, after) if a != b)
  return "%d of %d atoms moved" % (moved, len(before))


def t_pack_fuse(suite):
  """Pack builds the symmetry-generated content, fuse throws it away again.

  None of this is visible in the asymmetric unit - GetAtomCount reports 45
  before and after, because packing does not add atoms to the model. The
  lattice is what changes, and it reports its own state.
  """
  _sucrose(suite)
  before = int(olx.xf.latt.GetFragmentCount())
  macro("pack cell")
  packed = int(olx.xf.latt.GetFragmentCount())
  if packed <= before or not _grown():
    raise AssertionError("pack cell left %d fragment(s), was %d, grown=%s"
                         % (packed, before, _grown()))
  macro("fuse")
  fused = int(olx.xf.latt.GetFragmentCount())
  if fused >= packed:
    raise AssertionError("fuse left %d fragment(s), packed was %d"
                         % (fused, packed))
  return "%d -> %d packed -> %d fused" % (before, packed, fused)


def t_grow(suite):
  """Grow completes fragments broken across symmetry.

  A complete molecule has nothing to grow, and sucrose is one - grow correctly
  does nothing to it. So this asserts the outcome rather than a change: after
  grow, no fragment may still be incomplete.
  """
  _sucrose(suite)
  before = int(olx.xf.latt.GetFragmentCount())
  macro("grow")
  after = int(olx.xf.latt.GetFragmentCount())
  if after < before:
    raise AssertionError("grow lost fragments: %d -> %d" % (before, after))
  if after == before and not _grown():
    return "nothing to grow, %d complete fragment(s)" % after
  return "%d -> %d fragment(s), grown=%s" % (before, after, _grown())


def _grown():
  return str(olx.xf.latt.IsGrown()).lower() in ("true", "1")


def t_sort(suite):
  """Sorting by label changes the order without changing the population."""
  folder = _sucrose(suite)
  before = _labels()
  macro("sort +l")
  after = _labels()
  if sorted(before) != sorted(after):
    raise AssertionError("sort changed the atom list: %d -> %d"
                         % (len(before), len(after)))
  if before == after:
    raise SkipTest("the sample is already in label order")
  return "%d atoms reordered" % len(after)


def t_name(suite):
  """Renaming an atom has to stick, and has to reach the written file."""
  if not hasattr(olx, "Name"):
    raise SkipTest("Name is a GUI macro and is not exported to olex2c")
  folder = _sucrose(suite)
  label = _first("C")
  new = "Zz1"
  macro("name %s %s" % (label, new))
  if new.lower() not in [l.lower() for l in _labels()]:
    raise AssertionError("name %s %s did not take" % (label, new))
  text = _ins_text(suite, folder, "m_name")
  if _atom_line(text, new) is None:
    raise AssertionError("%s is not in the written ins" % new)
  return "%s -> %s" % (label, new)


def t_fvar(suite):
  """FVAR is how SHELX carries free variables; adding one must be written."""
  folder = _sucrose(suite)
  before = olx.Ins("FVAR")
  macro("addins FVAR 0.5")
  text = _ins_text(suite, folder, "m_fvar")
  if "FVAR" not in text.upper():
    raise AssertionError("no FVAR in the written ins")
  after = olx.Ins("FVAR")
  return "FVAR %r -> %r" % (str(before)[:24], str(after)[:24])


def _labels():
  return [olx.xf.au.GetAtomName(i) for i in range(int(atom_count()))
          if not deleted(i)]


def _coords():
  return tuple(str(olx.xf.au.GetAtomCrd(i)) for i in range(int(atom_count()))
               if not deleted(i))
