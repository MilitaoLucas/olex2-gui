[comment]: < Help for the Symmetry Disorder Display row (gui/snippets/snippet-symdisorder.htm). Compiled into the help index by gui/help/help_index.py. >

# Symmetry Disorder Display
For pictures of structures in which a group is disordered by symmetry, for example a ring lying across a mirror plane. There is then only one set of atoms in the asymmetric unit, with no PARTs to choose from, and growing the structure shows every orientation at once. These two tools show one complete metal centre, and separate one consistent orientation from the other, so that it can be drawn differently.

They change what is displayed, not the model: nothing here affects the refinement.

## Making a picture
1. Click **Complete Complex**.
2. Click any atom of a disordered group, in the orientation you want to keep.
3. Click **Group Other Orientation**.

The other orientation now has its own look, from the material of the group *dp1*.

## Complete Complex
Shows one metal with all of its ligands whole, and no other metal, however the structure was grown before: bridging rings are complete on the far side, and the metal beyond them is left out. It uses the selected metal, or else the first one in the asymmetric unit.

Olex2 first returns to the asymmetric unit (*fuse*), and then generates just the atoms needed.

## Group Other Orientation
Select exactly one atom of a disordered group. The orientation of that atom stays as it is. The other orientation goes into the group *dp1*, together with its bonds. Everything else, including the atoms shared by both orientations, is left as it was.

To keep the other orientation instead, reload the structure and select one of its atoms.

## Which atoms belong together
Copies of the same atom that are too close without being bonded (H...H under 1.5 A, other atoms under 1.75 A) cannot be present together, while bonded atoms belong together. Where neighbouring groups touch in this way, for example through their hydrogen atoms, choosing an orientation for one group decides the others too, so one selected atom is enough.

## If it does not work
| **Select exactly one atom** | Selecting a bond also counts as more than one atom. |

| **Not part of the disorder** | The selected atom has no clashing copies. Select an atom of the disordered group. |

| **Independent sets** | Some groups do not touch, so one atom cannot decide them all. Click **Complete Complex** first. |

| **Contacts contradict each other** | No split without a clash exists for this structure at these distances. |

| **Selection check failed** | Most likely *dp1* exists already: reload the structure and try again. |

| **Atoms outside this complex** | Atoms of the asymmetric unit that do not belong to this metal stay visible after **Complete Complex**. |
