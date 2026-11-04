"""
gui/symdisorder/__init__.py

Symmetry Disorder Display: pictures of grown structures with a group disordered
by symmetry. One row of two buttons, gui/snippets/snippet-symdisorder.htm, that can
be included in any tool. Help: symdisorder.help.md

Pure-Python helpers live in _core.py and are testable without Olex2.

Public API (registered with Olex2 as spy.gui.symdisorder.*)
-----------------------------------------------------------
    complete_complex()
    group_other_orientation()
"""

from __future__ import annotations
import math
import re
from ._core import colour_orientations, is_metal
from ._core import complete_complex as _complete_complex


# ===========================================================================
# One orientation of a symmetry-disordered group, for pictures
# ===========================================================================
# sel() and sel(a) print one numbering of the C1_$n names, while sel and info
# read names with another, so a printed name does not lead back to its atom.
# Each name always selects the same atom, though, so the atom behind every name
# is found by selecting it and reading crd(). Most numbers may lead nowhere, and
# after grow, fuse or kill the printed ones often do, so all of them are tried.
# The a.u. copy of an atom has no name of its own: its bare label selects all copies.

_ORIENTATION_GROUP = 'dp1'  # has a predefined material, see gui/skin


def _sel_names(olex) -> list:
  """sel() as a list. It also lists both end atoms of each selected bond."""
  return olex.f('sel()').split()


def _select_only(olex, names: list) -> None:
  olex.m('sel -u')
  if names:
    olex.m('sel ' + ' '.join(names))


def _read_grown_model(olex, olx) -> dict:
  """
    Read the grown structure through the selection. Clears the selection.

    Returns atoms ({key: (label, xyz)}), bonds (set of key pairs), name_of
    ({key: name that selects it}) and printed_of ({key: name sel() prints}).
    """
  olex.m('sel -u')
  olex.m('sel atoms where xatom.bai.z > 0')
  every = _sel_names(olex)
  olex.m('sel -u')

  # every copy of each label, from the info table
  atoms = {}
  labels = sorted({name.split('_')[0] for name in every})
  for label in labels:
    for line in olx.Info(label, f=True, p=6).splitlines():
      t = line.split()
      if len(t) > 4 and t[0] == label:
        atoms[len(atoms)] = (label, tuple(float(v) for v in t[2:5]))

  # All but the a.u. copy can be reached, which ends the search for that label. The
  # number that selects an atom can be above every printed one, so go well past them.
  top = 2 * max([int(n) for n in re.findall(r'\$(\d+)', ' '.join(every))], default=0) + 50
  selects, printed = {}, {}
  for label in labels:
    wanted = max(sum(1 for a in atoms.values() if a[0] == label) - 1, 1)
    reached = set()
    for name in [label] + [f'{label}_${n}' for n in range(1, top + 1)]:
      if len(reached) >= wanted:
        break
      _select_only(olex, [name])
      got = _sel_names(olex)
      if len(got) == 1:
        xyz = tuple(float(v) for v in olex.f('crd()').split())
        selects[name] = xyz
        printed[got[0]] = xyz
        reached.add(xyz)

  def key_at(xyz, label=None):
    for key, (atom_label, atom_xyz) in atoms.items():
      if (label is None or atom_label == label) and math.dist(xyz, atom_xyz) < 0.01:
        return key
    return None

  name_of = {}
  for name, xyz in selects.items():
    key = key_at(xyz, name.split('_')[0])
    if key is not None:
      name_of[key] = name

  # the one copy no name reaches is the a.u. atom, which prints as the bare label
  for label in {a[0] for a in atoms.values()}:
    left = [k for k, a in atoms.items() if a[0] == label and k not in name_of]
    if len(left) == 1:
      printed[label] = atoms[left[0]][1]
  printed_of = {}
  for name, xyz in printed.items():
    key = key_at(xyz, name.split('_')[0])
    if key is not None:
      printed_of[key] = name

  # the bonds as Olex2 has them (FREE etc. honoured): walk out from each atom
  bonds = set()
  for key, name in name_of.items():
    _select_only(olex, [name])
    olex.m('sel atom bonds -a')
    olex.m('sel bond atoms -a')
    for neighbour in _sel_names(olex):
      if neighbour in printed:
        other = key_at(printed[neighbour])
        if other is not None and other != key:
          bonds.add(frozenset((key, other)))
  olex.m('sel -u')
  return {'atoms': atoms, 'bonds': bonds, 'name_of': name_of,
          'printed_of': printed_of, 'key_at': key_at}


def group_other_orientation() -> None:
  """
    For a picture of a grown structure with symmetry-disordered groups: from
    one selected atom of a disordered group, find the clash-free orientation it
    belongs to and put the other orientation, with its bonds, in group dp1.
    Changes only the selection and the group, not the model.
    """
  try:
    import olex
    import olx
    seed = _sel_names(olex)
    if len(seed) != 1:
      print(f"[symdisorder] Select exactly one atom of a disordered group first (selected: {len(seed)})")
      return
    seed_xyz = tuple(float(v) for v in olex.f('crd()').split())

    model = _read_grown_model(olex, olx)
    atoms, name_of = model['atoms'], model['name_of']
    if not model['bonds']:
      print("[symdisorder] Could not read the bonds of the structure")
      return
    colours, labels, n_sets, n_clashes = colour_orientations(atoms, model['bonds'])
    if colours is None:
      print("[symdisorder] The contacts contradict each other: no clash-free split exists")
      return
    seed_key = model['key_at'](seed_xyz)
    if seed_key not in colours:
      found = ' '.join(sorted(labels)) or 'none found'
      print(f"[symdisorder] The selected atom is not part of the disorder (disordered atoms: {found})")
      return
    if n_sets != 1:
      print(f"[symdisorder] Found {n_sets} independent sets of atoms: one selected atom cannot decide them all")
      return

    chosen = [k for k, c in colours.items() if c == colours[seed_key]]
    other = [k for k, c in colours.items() if c != colours[seed_key]]
    no_name = [k for k in colours if k not in name_of]
    if len({colours[k] for k in no_name}) > 1:
      print("[symdisorder] The asymmetric unit atoms fall in both orientations: this case is not handled")
      return

    # An a.u. atom can only be selected together with its copies: if the chosen
    # orientation holds it, select the other one directly, otherwise select the
    # chosen one with everything ordered, and invert.
    if any(k in chosen for k in no_name):
      _select_only(olex, [name_of[k] for k in other])
      olex.m('sel bonds where xbond.a.selected==true||xbond.b.selected==true')
    else:
      ordered = sorted({a[0] for a in atoms.values()} - labels)
      _select_only(olex, [name_of[k] for k in chosen] + ordered)
      olex.m('sel bonds where xbond.a.selected==true&&xbond.b.selected==true')
      olex.m('sel -i')

    got = set(_sel_names(olex))
    printed_of = model['printed_of']
    missing = [k for k in other if printed_of.get(k) not in got]
    wrong = [k for k in chosen if printed_of.get(k) in got]
    if missing or wrong:
      print(f"[symdisorder] Selection check failed ({len(missing)} atoms missing, {len(wrong)} of the "
            f"chosen orientation included), no group made. If {_ORIENTATION_GROUP} exists already, "
            "reload the structure first.")
      olex.m('sel -u')
      return
    olex.m(f'group -n={_ORIENTATION_GROUP}')
    olex.m('sel -u')
    print(f"[symdisorder] Group {_ORIENTATION_GROUP} holds the other orientation ({len(other)} atoms); "
          f"{len(atoms) - len(other)} atoms stay as they were ({n_clashes} clashes resolved)")
  except Exception as e:
    print(f"[symdisorder] group_other_orientation failed: {e}")


def complete_complex() -> None:
  """
    Show one metal with its ligands complete and no other metal: from the
    asymmetric unit, generate exactly those atoms. Uses the selected metal, or
    the first one in the asymmetric unit. Changes the display, not the model.
    """
  try:
    import olex
    import olx
    import olex_core
    atoms = []
    for i in range(int(olx.xf.au.GetAtomCount())):
      element = olx.xf.au.GetAtomType(i)
      if olx.xf.au.IsAtomDeleted(i).lower() == 'true' or element == 'Q':
        continue
      crd = tuple(float(v) for v in olx.xf.au.GetAtomCrd(i).replace(',', ' ').split())
      atoms.append((olx.xf.au.GetAtomlabel(i), element, crd))
    metals = [n for n, a in enumerate(atoms) if is_metal(a[1])]
    if not metals:
      print("[symdisorder] There is no metal in the asymmetric unit")
      return
    selected = {name.split('_')[0] for name in _sel_names(olex)}
    wanted = [n for n in metals if atoms[n][0] in selected]
    metal = (wanted or metals)[0]

    radii = {}
    for label, element, _ in atoms:
      if element not in radii:
        rows = [line.split() for line in olx.Info(label, f=True, p=3).splitlines()]
        radii[element] = next(float(t[-2]) for t in rows if len(t) > 4 and t[0] == label)

    ops = [(tuple(tuple(row[:3]) for row in m), tuple(row[3] for row in m))
           for m in olex_core.SGInfo()['MatricesAll']]
    identity = (((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0.0, 0.0, 0.0))
    if identity not in ops:
      ops.insert(0, identity)
    cell = tuple(float(v) for v in olx.xf.au.GetCell().replace(',', ' ').split())
    codes, strays = _complete_complex(cell, atoms, ops, metal, radii)

    olex.m('sel -u')
    olex.m('fuse')
    for code, labels in codes.items():
      olx.Sgen(*labels, code)

    olex.m('sel atoms where xatom.bai.z > 0')
    shown = len(_sel_names(olex))
    olex.m('sel -u')
    expected = len(atoms) + sum(len(labels) for labels in codes.values())
    print(f"[symdisorder] {atoms[metal][0]} with complete ligands: {shown} atoms shown, {expected} expected")
    if strays:
      print("[symdisorder] Asymmetric unit atoms outside this complex are still shown: " + ' '.join(strays))
  except Exception as e:
    print(f"[symdisorder] complete_complex failed: {e}")


# ===========================================================================
# Olex2 registration
# ===========================================================================

try:
  from olexFunctions import OV
  OV.registerFunction(complete_complex,        False, 'gui.symdisorder')
  OV.registerFunction(group_other_orientation, False, 'gui.symdisorder')
except ImportError:
  pass
