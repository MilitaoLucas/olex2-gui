[comment]: < Help for the Symmetry Disorder Display row (gui/snippets/snippet-symdisorder.htm). Compiled into the help index by gui/help/help_index.py. >

# Symmetry Disorder Display
For pictures of structures in which a group is disordered by symmetry, for example a ring lying across a mirror plane. There is then only one set of atoms in the asymmetric unit, with no PARTs to choose from, and growing the structure shows every orientation at once. These two tools complete the fragments on screen, and separate one consistent orientation from the other, so that it can be drawn differently.

They change what is displayed, not the model: nothing here affects the refinement.

## Making a picture
1. Grow the structure as you want it (or not at all), then click **Complete Fragments**.
2. Click any atom of a disordered group, in the orientation you want to keep. With several molecules, each disordered on its own, click one atom in each.
3. Click **Group Other Orientation**.

The other orientation now has its own look, from the material of the group *dp1*.

## Complete Fragments
Completes every fragment on screen, however the structure was grown: exactly the missing atoms are added, nothing else, and nothing is removed. A molecule on a special position becomes whole. With only the asymmetric unit shown, this shows its fragments complete.

A metal is never added: bridging ligands are complete on the far side, and the metal beyond them is left out.

Olex2 first returns to the asymmetric unit (*fuse*), and then generates just the atoms needed.

## Group Other Orientation
Select one atom of a disordered group. The orientation of that atom stays as it is. The other orientation goes into the group *dp1*, together with its bonds. Everything else, including the atoms shared by both orientations, is left as it was.

Where several groups are disordered independently, for example in a packing picture with no close contacts between molecules, select one atom in each: nothing in the structure decides between their orientations.

To keep the other orientation instead, reload the structure and select one of its atoms.

## Which atoms belong together
Copies of the same atom that are too close without being bonded (H...H under 1.5 A, other atoms under 1.75 A) cannot be present together, while bonded atoms belong together, so the rest of a group follows the atoms that clash. An atom bonded to both orientations, such as the one the group hangs on, is shared. Where neighbouring groups touch in this way, for example through their hydrogen atoms, choosing an orientation for one group decides the others too, so one selected atom is enough.

## If it does not work
| **Select one atom of each disordered group** | Nothing is selected. |

| **Not part of the disorder** | A selected atom has no clashing copies, or a bond is selected. Select atoms of the disordered groups only. |

| **Independent disordered groups** | Some groups do not touch, so one atom cannot decide them all. Select one atom in each. |

| **Different orientations of the same group** | Two selected atoms ask for both orientations of one group. |

| **Contacts contradict each other** | No split without a clash exists for this structure at these distances. |

| **Selection check failed** | Most likely *dp1* exists already: reload the structure and try again. |

| **Bonds lead on without end** | The structure is a network (a polymer) rather than separate fragments, so it cannot be completed. Nothing is changed. |
