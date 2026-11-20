"""
gui/symsnap/__init__.py

Symmetry Snap: make selected atoms that are *nearly* symmetry-equivalent
exactly so, so that growing does not give slightly diverging copies.

  - Atoms of one element whose symmetry images lie within tol of each other
    are merged into the first of them (a.u. order): mean position, summed
    occupancy, the others deleted. Example: two half H atoms of a water on a
    2-fold axis, each nearly the image of the other, become one full H.
  - Every resulting atom close to a special position (its own image within
    tol) is moved onto it; the occupancy is kept.

The changed atoms are taken out of AFIX groups (afix 0), as a group built for
the old atoms no longer fits.

Pure-Python logic is in _core.py, testable without Olex2.

Public API (registered with Olex2 as spy.gui.symsnap.*)
-------------------------------------------------------
    snap(tol=0.5, dry=false)   on the selected atoms; dry: only report
"""

from __future__ import annotations
from ._core import DEFAULT_TOLERANCE, merge_plan

_TAG = "[symsnap]"


def _floats(text) -> tuple:
  return tuple(float(v) for v in str(text).replace(',', ' ').split())


def _selected_au_atoms(olex, olx) -> list:
  """Selected atoms as a.u. records, in a.u. order; a grown copy counts as its a.u. atom."""
  chosen = {name.split('_')[0] for name in olex.f('sel()').split()}
  atoms = []
  for i in range(int(olx.xf.au.GetAtomCount())):
    if olx.xf.au.IsAtomDeleted(i).lower() == 'true':
      continue
    label = olx.xf.au.GetAtomName(i)
    if label not in chosen:
      continue
    atoms.append({'id': i, 'label': label, 'element': olx.xf.au.GetAtomType(i),
                  'xyz': _floats(olx.xf.au.GetAtomCrd(i)),
                  'occu': float(olx.xf.au.GetAtomOccu(i)),
                  'afix': int(str(olx.xf.au.GetAtomAfix(i)) or 0)})
  return atoms


def _describe(step) -> str:
  what = f"{step['keep']}"
  if step['remove']:
    what += " + " + " + ".join(step['remove']) + f" -> {step['keep']}"
  site = "general position" if step['site'] == 1 else f"special position (site order {step['site']})"
  xyz = " ".join("%.6f" % v for v in step['xyz'])
  text = (f"{what}: {xyz}, occupancy {step['occu']:.4f}, {site}; "
          f"moved {step['moved']:.3f} A, members within {step['spread']:.3f} A")
  if step['overfull']:
    text += f"  WARNING: occupancy is above a full site ({1.0 / step['site']:.4f})"
  return text


def snap(tol=DEFAULT_TOLERANCE, dry=False) -> None:
  """
    Make the selected near-symmetry-equivalent atoms exactly equivalent.
    tol: A between an atom and a symmetry image that counts as the same.
    dry: true only prints what would be done.
    """
  try:
    import olex
    import olx
    import olex_core
    tol = float(tol)
    dry = str(dry).strip().lower() in ('true', '1', 'yes')
    atoms = _selected_au_atoms(olex, olx)
    if not atoms:
      print(f"{_TAG} Select the atoms to snap first (e.g. the two H atoms of a water)")
      return

    cell = _floats(olx.xf.au.GetCell())
    ops = [(tuple(tuple(row[:3]) for row in m), tuple(row[3] for row in m))
           for m in olex_core.SGInfo()['MatricesAll']]
    plan = merge_plan(cell, ops,
                      [(a['label'], a['element'], a['xyz'], a['occu']) for a in atoms], tol)
    if not plan:
      print(f"{_TAG} Nothing to do: no two selected atoms are within {tol} A of a symmetry "
            f"image of each other, and none is that close to a special position")
      return

    print(f"{_TAG} {'Would change' if dry else 'Changing'} (tolerance {tol} A):")
    for step in plan:
      print("  " + _describe(step))
    if dry:
      return

    by_label = {a['label']: a for a in atoms}
    in_afix = []
    for step in plan:
      kept = by_label[step['keep']]
      olx.xf.au.SetAtomCrd(kept['id'], *step['xyz'])
      olx.xf.au.SetAtomOccu(kept['id'], step['occu'])
      if any(by_label[label]['afix'] for label in [step['keep']] + step['remove']):
        in_afix.append(step['keep'])
    olx.xf.EndUpdate()

    removed = [label for step in plan for label in step['remove']]
    if removed:
      olex.m('kill ' + ' '.join(removed))
    if in_afix:
      olex.m('afix 0 ' + ' '.join(in_afix))
      print(f"{_TAG} Taken out of their AFIX group: {' '.join(in_afix)}")
    olx.Refresh()
    print(f"{_TAG} Done. Refine to settle; restraints (DFIX/DANG) as needed.")
  except Exception as e:
    print(f"{_TAG} snap failed: {e}")


# ===========================================================================
# Olex2 registration
# ===========================================================================

try:
  from olexFunctions import OV
  OV.registerFunction(snap, False, 'gui.symsnap')
except ImportError:
  pass
