"""Writing the model to every format Olex2 registers, and reading it back.

The round trip is the assertion: write, load the file that was written, and
require the atoms to survive. A writer that drops a column and a writer that
works look identical until something reads the result.

Two of these formats carry no atoms at all - p4p and crs are cell files, from
the diffractometer rather than from a refinement - so they are checked for the
cell instead. Asserting atoms on them would report correct behaviour as a bug.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import (macro, SkipTest, load, model_in, atom_count,
                            deleted, real_atom_count, space_group)

# formats that carry the structure, so the atoms have to survive a round trip
WITH_ATOMS = ["res", "ins", "xyz", "mol", "cif", "pdb"]

# formats that carry the cell and no atoms
CELL_ONLY = ["p4p", "crs"]


def register(suite):
  for ext in WITH_ATOMS:
    suite.run("formats", "round trip through .%s" % ext,
              t_round_trip, suite, ext)
  for ext in CELL_ONLY:
    suite.run("formats", ".%s carries the cell" % ext, t_cell_only, suite, ext)
  suite.run("formats", "an unwritable format is refused, not silent",
            t_refused, suite, "mas")


def _sucrose(suite):
  folder = suite.sample("sucrose")
  load(model_in(folder))
  macro("user '%s'" % folder.replace("\\", "/"))
  return folder


def _atoms():
  """Model atoms as (label, type): neither deleted nor Q peaks.

  Q peaks have to be excluded or the comparison is between different things.
  A res keeps them - it is the output of a refinement - while an ins and a cif
  drop them, because an ins is the *input* to the next one and a peak is not
  part of the model. sucrose went "50 written, 45 read back" on both, which is
  both formats behaving correctly.
  """
  out = []
  for i in range(int(atom_count())):
    if deleted(i):
      continue
    if str(olx.xf.au.IsPeak(i)).lower() in ("true", "1"):
      continue
    out.append((str(olx.xf.au.GetAtomName(i)).upper(),
                str(olx.xf.au.GetAtomType(i))))
  return out


def _cell():
  return [float(olx.Cell(x)) for x in ("a", "b", "c", "alpha", "beta", "gamma")]


def t_round_trip(suite, ext):
  folder = _sucrose(suite)
  before = _atoms()
  cell_before = _cell()
  out = os.path.join(folder, "rt." + ext).replace("\\", "/")
  if olex.m("file '%s'" % out) == 0:
    raise AssertionError("writing .%s was refused" % ext)
  if not os.path.exists(out):
    raise AssertionError("nothing was written to rt.%s" % ext)
  size = os.path.getsize(out)
  if size == 0:
    raise AssertionError("rt.%s is empty" % ext)

  macro("@reap '%s'" % out)
  after = _atoms()
  if len(after) != len(before):
    raise AssertionError(".%s: %d atoms written, %d read back"
                         % (ext, len(before), len(after)))
  # the types have to survive even where the labels do not: xyz carries
  # elements rather than crystallographic labels
  t_before = sorted(t for _, t in before)
  t_after = sorted(t for _, t in after)
  if t_before != t_after:
    raise AssertionError(".%s changed the composition" % ext)

  note = ""
  if ext not in ("xyz", "mol"):
    # formats that carry a cell have to carry it correctly
    cell_after = _cell()
    worst = max(abs(a - b) for a, b in zip(cell_before, cell_after))
    if worst > 0.01:
      raise AssertionError(".%s changed the cell by %.4f" % (ext, worst))
    note = ", cell within %.4f" % worst
  return "%d atoms, %d bytes%s" % (len(after), size, note)


def t_cell_only(suite, ext):
  """A cell file has to carry the cell, and is not expected to carry atoms."""
  folder = _sucrose(suite)
  cell_before = _cell()
  out = os.path.join(folder, "cellonly." + ext).replace("\\", "/")
  if olex.m("file '%s'" % out) == 0:
    raise AssertionError("writing .%s was refused" % ext)
  if not os.path.exists(out) or os.path.getsize(out) == 0:
    raise AssertionError("nothing was written to cellonly.%s" % ext)
  text = open(out, "r", errors="ignore").read()
  # match on the numbers, not on their formatting - p4p writes 7.772741 where
  # a "%.3f" comparison looks for 7.773 and finds nothing
  numbers = []
  for tok in text.replace(",", " ").split():
    try:
      numbers.append(float(tok))
    except ValueError:
      continue
  missing = [a for a in cell_before[:3]
             if not any(abs(a - n) < 0.01 for n in numbers)]
  if missing:
    raise AssertionError(".%s does not carry the cell lengths %s"
                         % (ext, ", ".join("%.4f" % m for m in missing)))
  return "%d bytes, cell lengths present" % os.path.getsize(out)


def t_refused(suite, ext):
  """A format Olex2 cannot write must say so rather than write nothing.

  .mas is registered as a readable format but writing it returns 0 and leaves
  no file. That is a clear refusal, which is what this asserts - the failure
  worth catching is a writer that returns 1 and writes nothing.
  """
  folder = _sucrose(suite)
  out = os.path.join(folder, "refused." + ext).replace("\\", "/")
  rv = olex.m("file '%s'" % out)
  wrote = os.path.exists(out) and os.path.getsize(out) > 0
  if rv != 0 and not wrote:
    raise AssertionError(".%s reported success and wrote nothing" % ext)
  if wrote:
    return ".%s is writable after all, %d bytes" % (ext, os.path.getsize(out))
  return ".%s refused, and wrote nothing" % ext
