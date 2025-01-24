# Select-Atoms-help
# Select Atoms
This menu provides several methods of selecting or deselecting atoms with varying degrees of specificity. Press '<c>ESC</c>' at any time to deselect everything.

## Exclusive
Selects only atoms of the element clicked.

## Additive
Adds all atoms of the element clicked to the selection.

## Command Line Examples

| `sel $c` | Selects all C atoms. |

| `sel -u` | Deselects (unselects) everything. |

| `sel c1` | Selects atom C1. |

| `sel $c $n` | Selects all C and N atoms. |


# Selections
Once atoms and/or bonds are selected, the following links can be clicked to perform specific actions:

## Invert
|`sel -i`| Inverts the current selection, i.e., all atoms and bonds *not* not currently selected will be selected instead. |

## Deselect
|`sel -u`| Deselects (unselects) all selected atoms. |

## Delete
|`kill sel`| Deletes all selected atoms; the same as pressing the '<c>Delete</c>' key. Undo the deletion with '<c>CTRL+Z</c>'. |

## Previous Selection
|`selback`| Re-select all atoms previously selected. |


# Select-Criteria-help
# Select Criteria
To select atoms on the basis of their Uiso values, choose the **>**, **<**, or **=** operator from the drop-down menu and enter a Uiso value in the box. Then click **Select** to select only those atoms meeting the specified criterion.


# Select-Rings-help
# Select Rings
Select all rings of the specified type, e.g., C6, C5N, C5, or C5O, within the structure. It is possible to specify other rings by typing them directly into the drop-down menu, e.g., C3N2 will find all five-membered rings consisting of three carbons and two nitrogens (imidazoles and pyrazoles). Click outside the menu to highlight the specified ring. (The **Phenyl** and **Pyridine** links are provided for convenience.)
