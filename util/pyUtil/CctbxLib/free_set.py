"""The reflections held out of refinement, and R_free computed on them.

A test set is only worth having if it is the same one the depositors used --
an R_free computed on reflections we chose ourselves cannot be compared with a
published value, because the model has already seen them. So the deposited set
is preferred wherever it exists, and generating one is the fallback.

PdbFetch writes '<name>.free' beside the hkl when an entry carries
_refln.status, as a plain list of indices. Nothing read it until now.

Used by every refinement mode: the flags are built once in FullMatrixRefine
and the work set is what reaches the normal equations, whichever solver runs.
"""
import os

from cctbx.array_family import flex
from olexFunctions import OV
import olx


def _deposited_path():
  """The .free beside the current structure, or None."""
  try:
    base = os.path.join(olx.FilePath(), olx.FileName())
  except Exception:
    return None
  p = base + ".free"
  return p if os.path.isfile(p) else None


def load_deposited(fo_sq, path=None):
  """Flags aligned to fo_sq from the deposited list, or None if there is none.

  Matched on the Miller index rather than on position: the file is written
  from the deposition and fo_sq has been merged, filtered and possibly
  re-sorted since, so the two orders have no reason to agree.

  Returns None rather than an empty selection when nothing matches, so a
  mismatched file is not silently taken for "no reflections held out".
  """
  if path is None:
    path = _deposited_path()
  if not path:
    return None
  held = set()
  try:
    with open(path) as f:
      for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
          continue
        t = line.split()
        if len(t) >= 3:
          held.add((int(t[0]), int(t[1]), int(t[2])))
  except Exception as e:
    print("Could not read %s: %s" % (path, e))
    return None
  if not held:
    return None
  # the file lists the asymmetric unit as deposited; fo_sq may hold either
  # member of a Friedel pair, so both are accepted
  flags = flex.bool(fo_sq.indices().size(), False)
  n = 0
  for i, h in enumerate(fo_sq.indices()):
    if h in held or (-h[0], -h[1], -h[2]) in held:
      flags[i] = True
      n += 1
  if n == 0:
    print("%s lists %d reflections, none of which are in the data - ignored"
          % (os.path.basename(path), len(held)))
    return None
  print("Free set: %d of %d reflections, as deposited" % (n, flags.size()))
  return flags


def _index_hash(h, seed):
  """A value per Miller index, from the index alone.

  The whole draw has to be a pure function of the data, or the test set
  changes between runs and every R_free is computed on different reflections.
  The global flex generator is not used: seeding it would disturb every other
  consumer in the process and the seed cannot be read back to restore it.
  """
  x = (h[0]*73856093) ^ (h[1]*19349663) ^ (h[2]*83492791) ^ seed
  x &= 0xffffffff
  x ^= (x >> 13)
  x = (x*1274126177) & 0xffffffff
  return x ^ (x >> 16)


def stratified_flags(fo_sq, fraction, n_shells=None):
  """The same fraction out of every resolution shell.

  Drawn uniformly over the whole data set, a test set is not uniform in
  resolution: the outer shells hold most of the reflections but the weakest
  of them, and the inner shells are so sparse that a 5% draw can take a
  disproportionate bite. R_free then carries more noise than it should
  exactly where the model is least constrained. Binning first and drawing the
  fraction from each bin fixes the composition without changing the size.

  Shells are equal in reflection count rather than in d-spacing, so each
  contributes the same number and none is too small to draw from.
  """
  if n_shells is None:
    n_shells = OV.GetParam('snum.refinement.free_shells')
  n_shells = max(1, int(n_shells or 1))
  n = fo_sq.indices().size()
  if n == 0:
    return None
  uc = fo_sq.unit_cell().parameters()
  seed = hash((fo_sq.space_group().type().number(),
               tuple(round(p, 4) for p in uc), n)) & 0x7fffffff

  # by resolution, highest d first, so shell 0 is the innermost
  d = fo_sq.d_spacings().data()
  order = flex.sort_permutation(d, reverse=True)
  flags = flex.bool(n, False)
  indices = fo_sq.indices()
  taken = 0
  for s in range(n_shells):
    lo = (s*n)//n_shells
    hi = ((s + 1)*n)//n_shells
    if hi <= lo:
      continue
    shell = order[lo:hi]
    # the fraction of this shell, chosen by the index hash so the result is
    # the same on every run
    want = int(round((hi - lo)*fraction))
    if want <= 0:
      continue
    keyed = sorted(shell, key=lambda i: _index_hash(indices[i], seed))
    for i in keyed[:want]:
      flags[i] = True
    taken += want
  if taken == 0:
    return None
  return flags


def flags_for(fo_sq, fraction=None, n_shells=None):
  """The test set for this structure: deposited if there is one, else drawn.

  A drawn set is reproducible from the data alone, so it survives a reload
  without being stored.
  """
  flags = load_deposited(fo_sq)
  if flags is not None:
    return flags
  if fraction is None:
    fraction = OV.GetParam('snum.refinement.free_fraction')
  fraction = float(fraction or 0)
  if fraction <= 0:
    return None
  if n_shells is None:
    n_shells = OV.GetParam('snum.refinement.free_shells')
  flags = stratified_flags(fo_sq, fraction, n_shells)
  if flags is None:
    return None
  print("Free set: %d of %d reflections, %.0f%% from each of %d resolution "
        "shells" % (flags.count(True), flags.size(), fraction*100,
                    max(1, int(n_shells or 1))))
  # printed rather than assumed: a set that is 5% of the data overall can
  # still be 1% of the innermost shell, which is where it matters most
  if OV.GetParam('snum.refinement.free_shell_report'):
    print("    d range        refl    free")
    for d_hi, d_lo, n, n_free in shell_report(fo_sq, flags, 10):
      print("    %6.2f-%5.2f  %7d  %6d  %5.2f%%"
            % (d_hi, d_lo, n, n_free, 100.0*n_free/n))
  return flags


def shell_report(fo_sq, flags, n_shells=10):
  """How the test set is spread over resolution, as a check on the draw.

  Worth printing once rather than trusting the selection: a set that is 5% of
  the data overall can still be 1% of the innermost shell.
  """
  n = fo_sq.indices().size()
  if n == 0 or flags is None:
    return []
  d = fo_sq.d_spacings().data()
  order = flex.sort_permutation(d, reverse=True)
  rows = []
  for s in range(max(1, int(n_shells))):
    lo = (s*n)//n_shells
    hi = ((s + 1)*n)//n_shells
    if hi <= lo:
      continue
    shell = order[lo:hi]
    n_free = sum(1 for i in shell if flags[i])
    rows.append((d[shell[0]], d[shell[len(shell) - 1]], hi - lo, n_free))
  return rows


def r1(fo_sq, f_calc, selection=None):
  """R1 = sum||Fo|-|Fc|| / sum|Fo| over a subset, on amplitudes.

  fo_sq is intensities and f_calc is complex, so both are taken to amplitudes
  first; the scale is refitted on the subset because the refinement's scale
  was fitted on the work set and applying it unchanged to the test set would
  fold a scale error into R_free.
  """
  if selection is not None:
    fo_sq = fo_sq.select(selection)
    f_calc = f_calc.select(selection)
  if fo_sq.size() == 0:
    return None
  fo = flex.sqrt(flex.abs(fo_sq.data()))
  fc = flex.abs(f_calc.data())
  den = flex.sum(fo)
  if den <= 0:
    return None
  k = flex.sum(fo*fc)/flex.sum(fc*fc) if flex.sum(fc*fc) > 0 else 1.0
  return flex.sum(flex.abs(fo - k*fc))/den
