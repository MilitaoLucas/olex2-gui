"""Restraints for a protein, applied inside Olex2.

The decisions live in protein_prep, which knows nothing about Olex2 so that
the same plan can be checked headlessly. This module only reads the model out
of Olex2 and puts the instructions back in.

Measured on 1IEE, lysozyme at 0.94 A, 1490 atoms, two cycles of CGLS-J from
the deposited coordinates:

  nothing              Umax 0.61 -> 17.6, Umin -52, CA rmsd 1.34 A,
                       26 of 129 residues lose their secondary structure
  restraints           Umax -> 2534, but CA rmsd 0.060 and 1 residue moved
  restraints + DAMP    Umax -> 1.10, Umin -0.011, CA rmsd 0.055, none moved

So the geometry restraints hold the fold and the damping holds the ADPs, and
both are needed: an undamped first step over thirteen thousand parameters is
long enough to take the ADPs negative even when the positions are held.
"""
import olex
import olx
from olexFunctions import OV

import protein_prep


def _residues():
  """The loaded structure as protein_prep.Residue objects.

  Atom names come from the model's own residue table rather than from parsing
  labels, and the disorder part comes with them: an alternate conformer is the
  same atom in another state, and grouping the two in one ADP restraint
  divides by the distance between them, which for a conformer that barely
  moved is zero and produces a silent NaN.
  """
  import olex_core
  out = []
  model = olex_core.GetRefinementModel(False)
  for r in model['aunit']['residues']:
    number = r.get('number')
    if number is None:
      continue        # the catch-all residue, holding atoms outside any RESI
    atoms, parts, part_labels = {}, {}, {}
    for a in r['atoms']:
      label = a['label']
      name = (label.split('_')[0] if '_' in label else label).upper()
      part = int(a.get('part', 0) or 0)
      # every conformer's copy: atoms keeps one label per name, which the
      # geometry table needs, but a SADI between parts has to name both
      part_labels[(name, part)] = label
      if name in atoms:
        continue
      atoms[name] = label
      parts[name] = part
    if atoms:
      out.append(protein_prep.Residue(
        number, r.get('chainId', ''), r.get('class', ''), atoms, parts,
        part_labels))
  return out


def restrain(adp=True, geometry=True, damp=True, apply=True):
  """Generate the restraints and, unless asked not to, add them.

  Returns the instruction list, so it can be inspected or written out without
  touching the model.
  """
  adp = OV.get_bool_from_any(adp)
  geometry = OV.get_bool_from_any(geometry)
  damp = OV.get_bool_from_any(damp)
  apply = OV.get_bool_from_any(apply)

  residues = _residues()
  if not residues:
    olx.Echo("No residues in this structure, so nothing to restrain.",
             m="warning")
    return []

  plan = protein_prep.plan_restraints(residues, adp=adp, geometry=geometry)
  ins = protein_prep.as_shelx(plan, damp=(10, 10) if damp else None)

  if apply:
    for line in ins:
      olex.m("AddIns %s" % line)

  counts = plan.counts()
  olx.Echo("Restraints for %d residues: %s"
           % (len(residues),
              ", ".join("%d %s" % (v, k) for k, v in sorted(counts.items())
                        if v)))
  if plan.unknown_classes:
    olx.Echo("  no geometry table for: %s (left unrestrained)"
             % " ".join(sorted(plan.unknown_classes)))
  if plan.chain_breaks:
    olx.Echo("  %d chain break(s); nothing is restrained across them"
             % len(plan.chain_breaks))
  if damp:
    olx.Echo("  DAMP 10 10: without it the first step takes the ADPs "
             "negative even with the geometry held")
  if any(line.startswith("XNPD") for line in ins):
    olx.Echo("  XNPD: anisotropic ADPs restrained positive definite. At "
             "atomic resolution a few atoms have U near 0.007 and refine "
             "straight through zero, after which no structure factor can "
             "be computed.")
  return ins


olex.registerFunction(restrain, False, 'protein')
