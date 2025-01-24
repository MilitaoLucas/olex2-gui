# Fragment Library
Clicking this link opens Ilia Guzei's *Idealized Molecular Geometry Library* (IMGL) in your default internet browser. Fragments contained in this library can be copied and pasted straight from the web site into Olex2. Simply copy the desired fragment atomic coordinates, including the *FRAG* and *FEND* lines, from the IMGL web site and paste them directly into the command line to insert the fragment into the structure. Detailed, step-by-step instructions, with examples, for this process are found in **Ilia Guzei's Manual** linked on the Olex2 **Home** tab. For more information on the *FRAG* command, consult the URL[https://shelx.uni-goettingen.de/shelxl_html.php, ShelX Manual].

Note: No constraints, restraints, or occupancies will be applied to the pasted fragment! These will have to be entered separately.

## Pasted fragments
The inserted fragments will appear in a slightly greenish colour on the screen while in the matching mode. Fragments can be matched to electron density peaks by first clicking on an atom in the imported fragment and then on the corresponding Q-peak, then repeating the process with other atom/Q pairs until the fragment is in the desired position and orientation.

## Exit matching mode
Press '<c>Esc</c>' repeatedly, click the **Esc** link in the orange mode box, or type '<c>mode off</c>' to exit the matching mode.


# Link Selected
Select two atoms to be "linked" in the refinement, as described below.

## Occupancies
Clicking **Occupancies** links the occupancies of the two atoms to one another so that the individual occupancies add up to unity. This is also accomplished by the '<c> fvar sel</c>' command.

## Parts and Occupancies
The occupancies will be linked such that the individual occupancies add up to unity, as above, and the selected atoms will be added to different PARTs as well. Equivalent to the line command '<c>part -p=2 -lo sel</c>'. Here, the "-p=2" switch dictates that the atoms should be assigned to two PARTs, and "-lo" stands for "link occupancy".


# Link Constraints
Link PARTs and occupancies of selected atoms, then apply either an *EADP* constraint or an *ISOR* restraint to them.


# Link Parts 1
Assign the selected atoms to the PART number in the scroll box at the end of this line.


# Link Parts 2
Assign the selected atoms to two PART numbers, in order.


# Show Parts
If a structure contains atoms that have been assigned to PARTs, then it is sometimes useful only to display atoms belonging to certain PARTs.

| `showP 0 1` | Will show only atoms belonging to PARTs 0 and 1. |

| `showP 0 2` | Will show only atoms belonging to PARTs 0 and 2. |

| `showP 0 -1` | Will show only atoms belonging to PARTs 0 and -1. |

| `showP 0 -2` | Will show only atoms belonging to PARTs 0 and -2. |

| `showP 1 2` | Will show only atoms belonging to PARTs 1 and 2. |

| `showP 1` | Will show only atoms belonging to PART 1. |

| `showP 2` | Will show only atoms belonging to PART 2. |

| `showP` | Will show all atoms in all PARTs. |


# Split Group
The tools on this line will fully *split* each of the next atom(s) clicked into two atoms.

## Split
When this button is clicked, Olex2 will enter a mode in which each atom clicked will generate two atoms (at the focal points of the ellipsoids). The occupancy of each *split* atom will be set initially to 0.5; one of the atoms will be in PART 1, the other in PART 2. After the splitting has occurred, the newly "generated" atoms can be moved to any desired location by holding the '<c>SHIFT</c>' key and dragging each one with the mouse. The line command for the **Split** tool is '<c>mode split</c>'. Press '<c>ESC</c>' to exit the mode.

## EADP
This will split the atom(s) as above, but will constrain the ADPs for both atoms to be the same. This is useful in early stages of refinement, but should probably be removed once the disorder model is nearly complete, preferably applying a *DELU* restraint instead. This corresponds to the line command '<c>mode split -r=EADP</c>'.

## ISOR
This will split the atom(s) as above, and apply an *ISOR* restraint to each of the two atoms. The equivalent line command is '<c>mode split -r=ISOR</c>'.

## SIMU
As above, but with a *SIMU* restraint. The line command for this function is '<c>mode split -r=SIMU</c>'.


[comment]: < Help text for "Fit and Split Group" is now taken from toolbox_work.md. >