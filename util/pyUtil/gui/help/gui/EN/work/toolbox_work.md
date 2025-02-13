# toolbox work-target
A collection of useful tools
- Make all peaks Carbon
- Move Atoms
- Show/Hide Peaks
- Expand Short Contacts
- Peak Slider
- Disorder Tools

# change_element-target
Change atom types to&nbsp;


# anis-target
Make selected atoms anisotropic. If no atoms are selected, all atoms will be transformed.


# isot-target
Make selected atoms isotropic. If no atoms are selected, all atoms will be transformed.


# QC-target
Convert all Q peaks to C


# QH-target
Convert all Q peaks to H


# tidy-target
Tidy up your structure. Only recommended in early stages of refinement!


# killH-target
Deletes all H atoms from the model. Undo with CTRL+Z.


# Q-target
Toggle among three states: show Q peaks, show Q peaks with bonds, or hide Q peaks


# H-target
Toggle among three states: show hydrogens, show hydrogens with H-bonds, or hide hydrogens


# center-target
Center the structure on the screen and adjust the zoom level


# ok-target
Adjust the chemical formula to what is present in the model. The value of Z' will be taken into account, so check it!


# disorder tools-target
Tools for dealing with disordered structures


# peak & Uiso sliders-target
Sliding scales for Q peak and atom selection


# growing-target
Expand the structure on the screen


# finishing-target
Tools for quickly sorting atoms and making images


# Labels
It is possible to customise the labels in the model display. If a particular property is not applicable to any atom, there will be no label, e.g., if '<c>labels -o</c>' (see below) is typed and all atoms have occupancy 1, no atoms will be labelled.

| `help labels` | Print all options for the '<c>labels</c>' command. |

### Atom Names
| `labels -l` | All atom names of *non-hydrogen atoms* will be displayed next to the atoms. |

### Crystallographic Occupancy
| `labels -o` | This displays the crystallographic occupancy of any atoms which are not 100% occupied, i.e., whose occupancy is not 1. |

### Chemical Occupancy
| `labels -co` | Labels atoms with their "chemical occupancy" if less than 1. Basically the same as **Crystallographic Occupancy** above, but the occupancy values for atoms located on symmetry elements are not shown. |

### Parts
| `labels -p` | Displays PART numbers for any atoms not in PART 0. |

### Link-Code
| `labels -lo` | If there are atoms in the structure whose occupancies are linked, their link codes will be shown (FVAR 21/-21 in ShelXL language). |

### Fixed Parameters
| `labels -f` | Labels all atoms with fixed occupancy, regardless of the actual value of the occupancy. |

### Variables
| `labels -v` | Displays any atoms whose occupancy is linked to any variable. |

### AFIX Commands
| `labels -a -h` | This is useful to check the AFIX commands that are being applied to the structure. |

### Q-Peak Intensities
| `labels -qi` | Relative intensities of Q peaks will be displayed on the structure. |

### Ueq
| `labels -u` | Labels atoms with their Ueq values. |

### Label + residue rumber
| `labels -l -rn` | Displays both atom label and residue number. |

### Residue numbers
| `labels -rn` | Shows the residue number to which an atom belongs. |

### Residue class
| `labels -rc` | Shows the residue class to which an atom belongs. |

## Label H
Ticking this box will display labels on hydrogen atoms (unlabeled by default) *after* a selection is made from the **Labels** drop-down menu.

### H Atom Labels
| `labels -h -l` | This will label all atoms, including hydrogen atoms, and Q peaks with their atom name labels. |

## Hide
Press this button to hide atom or Q-peak labels. It will switch other types of labelling (e.g., occupancy, AFIX codes) off as well. Pressing '<c>F3</c>' toggles the display of atom and Q-peak labels on and off.


# Toolbar Model
This is a collection of three basic tools needed for model building.

## Assign Atom Types
Each element currently in the formula is represented by a small button.

### Using the GUI
| $spy.MakeElementButtonsFromFormula('mode') | All atoms present in the model are shown. The '...' button opens the Periodic Table if more elements need to be added. |

Clicking on an element button launches the atom type assignment mode for this particular element. In this mode, any atoms or Q peaks clicked are converted to that element. Pressing the '<c>ESC</c>' key exits the mode. Alternatively, selecting atoms first and then clicking an element button turns them all into that element. The buttons on this row will be red or blue if there is a mismatch between the number of atoms of that element in your model and those in the chemical formula. They turn green if the numbers agree.

### Using the Command Line
It is usually much more efficient to assign elements using the keyboard. Here are three frequently used commands:

| `name sel C` | Turns all selected atoms to carbons. |
| `mode name C` | Enter atom naming mode; once in the mode, all atoms clicked will turn to carbons. |
| `name \$Q C` | Turns all Q peaks to carbons. |

Note: If the box on this line is ticked, then a cycle of refinement will immediately be carried out when any of the following buttons is clicked:

## Add H - Geometrically Place Hydrogen Atoms
Clicking this button will cause Olex2 to place hydrogen atoms geometrically on any selected atom(s). If no atoms are selected, hydrogens will be placed on all possible atoms, to complete the structure.

| `hadd` | Adds hydrogen atoms to selected atoms (or to all atoms, if none are selected). |
| `hadd 137` | Will use specifed AFIX **if possible**. (137 adds three hydrogen atoms to a methyl group, for example.) |
| `hadd -137` | If the connectivity does not allow the addition of the specified AFIX atoms, it is still possible to place them in this way. *First* select the atom to which hydrogen atoms are to be added, then select a second atom to define a vector. |

## Make Atoms Anisotropic
Clicking the ellipsoid button makes the selected atoms anisotropic. If no atoms are selected, this change will be applied to all atoms.

| `anis` | All selected atoms will be refined **anisotropically** (ellipsoids will result). |

## Make Atoms Isotropic
Clicking the sphere button makes the selected atoms isotropic. If no atoms are selected, this change will be applied to all atoms.

| `isot` | All selected atoms will be refined **isotropically** (spheres will result). |


# Quicktools
This is a further selection of tools useful for model building.

## Change type and display of atoms
| `name \$Q C` | $spy.MakeHoverButton('toolbar-QC','name \$Q C') | This tool will change all displayed electron density peaks (Q peaks) to carbon atoms, regardless of peak height. |

| `name \$Q H` | $spy.MakeHoverButton('toolbar-QH','name \$Q H') | All visible Q peaks will be changed to hydrogens. |

| `clean` | $spy.MakeHoverButton('toolbar-tidy','clean') | Tidy the structure: small and geometrically impossible peaks will be removed; all remaining peaks will be changed to carbons. |

| `kill \$H` | $spy.MakeHoverButton('toolbar-killH','kill \$H')  | Deletes all selected hydrogen atoms from the structure. If no hydrogen atoms are selected, all will be deleted. Undo with '<c>CTRL+Z</c>'. |

| `showQ` | $spy.MakeHoverButton('toolbar-Q','showQ') | '<c>CTRL+Q</c>'. Toggle among three states: show electron density peaks, show them with bonds to nearby atoms, or hide them. |

| `showH` | $spy.MakeHoverButton('toolbar-H','showH') | '<c>CTRL+H</c>'. Toggle among three states: show H atoms, show them with H-bonds, or hide them. Hydrogen atoms remain in the model, regardless of their display. |

| `compaq>>compaq-a>>center` | $spy.MakeHoverButton('toolbar-center','compaq>>compaq -a>>center') | Fragments will be assembled and the structure will be centered on the screen. |

## Specifying the formula of the structure
| *Z*'= | Set the value of *Z*' here. (*Z*' is the number of formula units in the asymmetric unit.) For a molecular structure, *Z*' is typically 1. If there are two independent molecules on the screen, *Z*' must be set to 2. If the molecule sits on a symmetry element and has to be "grown" (i.e., expanded by symmetry operations - see **Growing** tool tab below) to be displayed in full, *Z*' will be smaller than 1, often 0.5. |

| `fixunit` | $spy.MakeHoverButton('toolbar-OK','fixunit') | Adjusts the sum formula to include only atoms currently present in the model, taking the value of *Z*' into account. |


# Electron Density Quick Maps
This tool tab provides options for the calculation of various electron density maps, which can be displayed in different 2D or 3D formats using the tools in this tab. However, when the **Level** setting (see **Maps** tool tab help) approaches zero, electron density maps become very messy and slow to display, so Olex2 does not display these regions.

## Available maps
### diff
Will display the difference map, Fobs-Fcalc. Make sure to select **surface**, **wire**, or **points** from the **View** drop-down menu under the **Maps** tool tab (accessed through **Map Settings** in this tool tab) for this map to be displayed correctly. The corresponding line command is '<c>CalcFourier -diff -r=0.1 -m</c>' or simply '<c>CTRL+M</c>'. This is an extremely important tool for checking the validity of a model. Red regions of the map represent areas of missing electron density and green regions represent areas of excess electron density. Both red and green regions will be very small in an accurate model of the structure.

### Fcalc
Will display the calculated electron density.

### 2Fo-Fc
Will display the map of 2Fobs-Fcalc.

### Fobs
Will display the observed electron density map.

### Deformation
Will display a deformation electron density map (deviations from spherical atom model).

### PDF
Will display a probability density function map for evaluating the quality of an anharmonic refinement.

## Show Map
Turns the display of the currently selected map on.

## Hide Map
Turns the display of the currently selected map off.

## Map Settings
This opens the **Maps** tool tab under **Tools** for further customising the map display.


# Disorder Tools
These are extremely useful commands for dealing with crystallographic disorder.


# PART Links
This is a selection of tools for displaying selected PARTs in the structure. The command-line equivalents are also very useful to know:

| `showp 0 1` | Shows all atoms in no particular PART (equivalently, in PART 0) and all atoms in PART 1. |

| `showp 0 2` | Shows all atoms in no particular PART (equivalently, in PART 0) and all atoms in PART 2. |

| `showp 1` | Shows only the atoms PART 1. |

| `showp` | Shows all atoms in all PARTs. |

| `sel part 1` | Selects all atoms in PART 1. |
<br>
<br>

If the **Sel** box is ticked when **0|1** or **0|2** is clicked, atoms in PART 1 or PART 2, respectively, will be selected in the display. If the **Unique** box is ticked, a list of unique atoms in the structure will be printed in the display output. Atoms will be marked with the parameter selected in the drop-down menu: **Occupancy** will indicate the occupancy of any partially occupied sites as a decimal number, **Chem Occ.** will display the chemical occupancy of each partially occupied site, **Link-Code** will display the link code for atoms whose occupancies are linked in ShelX format, **PART No** will show any non-zero PART numbers of atoms, and **Labels** will display atom labels.
<br>
<br>

The use of the **UP** arrow key to repeat recently issued commands is particularly useful here!


# Fit and Split Group
The *fit* and *split* tools operate on one or more selected atoms. To *fit* an atom (or group of atoms) is to move it to a desired location in the model. To *split* an atom (or group of atoms) is to divide it into two parts by creating a duplicate, which can then be moved to a desired location, e.g., to model disorder in the structure.

## Fit or Split One Atom
Left-click on an atom to highlight it. To *fit* the atom, click the **Fit** button. The color of the atom changes. Now hold down the '<c>SHIFT</c>' key and drag the atom with the left mouse button to any desired position. Press the '<c>ESC</c>' key to exit the **Fit/Split** mode. The *fitted* atom will remain in its new position.
<br>
<br>

To *split* the atom in two, click the **Split** button. The color of the atom changes as before, but dragging the atom with the '<c>SHIFT</c>' key pressed moves only ONE of the two atoms that were created by the **Split** command (the other atom can be moved with a separate **Fit** command, as above). The occupancies of the two atoms are linked, and the atoms will now have different PART numbers. Press the '<c>ESC</c>' key to exit the **Fit/Split** mode; the moved atom will remain in place.

## Fit or Split Two Atoms
Select two atoms, then click either the **Fit** or the **Split** button. **Split** will generate a duplicate pair, **Fit** will not. The color of the atoms changes. Drag the atoms with the mouse while pressing the '<c>SHIFT</c>' key to move them together as a group to any desired position.
<br>
<br>

To rotate the atoms about their midpoint instead of moving them, hold down the '<c>CTRL</c>' key while dragging with the mouse. Press '<c>ESC</c>' to exit the **Fit/Split** mode; the moved pair of atoms will remain in place.

## Fit or Split Three or more Atoms
Select three or more atoms, then click either the **Fit** or the **Split** button. As before, **Split** will generate a duplicate group, but **Fit** will not, and the atoms will change color. The entire group can be moved to any desired position by dragging it while holding down the '<c>SHIFT</c>' key (or rotated if the '<c>CTRL</c>' key is held down instead).
<br>
<br>

It is also possible to rotate the group about one of its bonds. First *activate* the bond about which you wish to rotate the group by *right-clicking* on it. Now, dragging the group while holding down the '<c>CTRL</c>' key rotates the group around this activated bond. Press '<c>ESC</c>' to exit this mode; any moved atoms will remain in their new positions.

## Split with SAME
This is one of the most powerful tools in Olex2. If a grouping of atoms is disordered, and one of the parts can be modelled (no matter how badly), the **Split** button with the **SAME** restraint will be very useful. (Typing '<c>mode fit -s same</c>' is equivalent to clicking the **Split** button with this restraint active.) Note that the **SAME** restraint is applied by default in Olex2 when splitting a group; other restraints may be selected from the drop-down menu. Everything will be restrained, so if the disorder *can* be modelled, the refinement process will sort it out automatically, though sometimes a large number of refinement cycles will be needed.

## Split with RIGU
As **Split with SAME**, except that the *RIGU* "rigid-bond" restraint is applied instead when splitting a group. See the **Shelx Compatible Restraints** tool tab help for more details on *RIGU*.

## Split with SAME, RIGU
As above, except that both *SAME* and *RIGU* restraints are applied when splitting a group.


[comment]: < Help text for "Show/Hide the list of restraints" is now taken from FragmentDB.md. >


# Peak & Uiso Sliders
This tool tab provides tools for selecting Q peaks and atoms according to their properties.


# Electron Density Peak Slider
This tool enables the selection of Q peaks by intensity.
<br>
<br>

Starting from the middle of the scale at 100, move the **Peaks** slider to the *left* to filter out the weakest Q peaks first, or to the *right* to filter out the strongest Q peaks first. Any commands issued after filtering will only apply to the remaining visible peaks. For example, the line command '<c>name $Q C</c>' will convert all visible Q peaks to carbons, and clicking **Select** or **Delete** will select or delete the peaks, respectively.


# Uiso Select Slider
This tool allows the selection of atoms according to their Uiso values.

## Slide to the RIGHT
Starting from the middle of the scale, move the Uiso slider to the *right* to select atoms whose Uiso value is *larger* than the value indicated next to the slider.

| `sel atoms where xatom.uiso < 0.02` | Selects all atoms whose Uiso value is less than 0.02. |

## Slide to the LEFT
Starting from the middle of the scale, move the Uiso slider to the **left** to select atoms whose Uiso value is SMALLER than the value indicated next to the slider.

| `sel atoms where xatom.uiso > 0.04` | Selects all atoms whose Uiso value is greater than 0.04. |


# Growing
Olex2 shows the asymmetric unit by default. This tool tab contains very powerful techniques for "assembling" a structure model on the screen exactly as desired. It is then possible to refine the model repeatedly in Olex2 without dismantling this assembly.


# Grow
## Growing
*Growing* here is used as a general term for adding atoms to the existing model on the screen in some systematic way, e.g., by adding symmetry-equivalent atoms to visualize an entire molecule when the asymmetric unit shows only part of the molecule because *Z*' < 1 for the structure.

### Grow All
| `grow` | Generates all "missing" connected symmetry-equivalent atoms. This will usually suffice to expand an asymmetric unit to show a complete molecule. |

### Shells
| `grow -s` | This adds atoms in concentric shells outward from the structure currently displayed on the screen. |

### Complete
| `grow -w` | Generates all missing symmetry-equivalent atoms of an already grown structure, whether bound to the main fragment or not. Thus, this command will display symmetry-equivalent solvent molecules and counter-ions not generated by a plain '<c>grow</c>' command. |

### Asymmetric Unit
| `fuse` | Removes all symmetry-equivalent atoms and displays the asymmetric unit. This is one of the most important line commands in Olex2. |

### Complete shown growing bonds
| `grow -b` | Shows growable "bonds" in a growing mode (see **Mode Grow** below). Click on any of these bonds to grow the structure. |

## Mode Grow
| `mode grow` | Similar to '<c>grow</c>', but now the '<c>grow</c>' command will be executed only when an object is clicked. Upon entering a growing mode, growable "bonds" will sprout from atoms satisfying the chosen growing conditions. |

There are various modifiers for this command:

### Short Contacts
| `mode grow -s` | Shows growable "bonds" to atoms involved in "short interactions" (e.g., hydrogen bonds) with the currently displayed structure. |

### Selection
| `mode grow -r` | Shows growable "bonds" to other occurrences of the currently selected atoms. |

### Van der Waals Radii
| `mode grow -v 2.0` | Shows growable "bonds" to other occurrences of the currently selected atoms that are at most 2.0 &Aring; away from the selected atom. |

### Move
| `mode grow -a` | When a growable "bond" is clicked, the symmetry-equivalent atom is moved to the new position. This is very useful when trying to assemble a meaningful asymmetric unit for extended structures (polymers). |

### Shells
| `mode grow shells` | Shows growable "bonds" that can be clicked to grow the structure outward in concentric shells. |

## Assemble
Strictly speaking, this tool does not belong to the **Grow** family of tools, but it is frequently used together with the growing tools. It is used to rearrange components of the asymmetric unit for a more compact or chemically sensible display of the model, often after a '<c>grow</c>' operation.

### Broken Fragments
| `compaq -a` | Sometimes, parts of a model may become "broken" - parts that should be bonded are shown as separate fragments. This tool will bring them back together. |

### Atom-to-Atom
| `compaq -c` | Similar to the **Broken Fragments** tool, but using a different reassembly algorithm. |

### Metal Last
| `compaq -m` | In this tool, metal ions are first taken out of the reassembly process (which is very useful when trying to assemble a ligand!), after which they are placed at the shortest possible distance to the other atoms in the structure. |

### Peaks
| `compaq -q` | This moves all electron density peaks as close to existing atoms as possible. |


# Finishing
The buttons in this tool tab are for convenient access to elementary versions of more powerful sorting and drawing tools found elsewhere in Olex2.


# QuickSort
The **Sort with Current Settings** button sorts the atoms in the model according to the options currently set under the **Sorting** tool tab. Clicking the pencil icon opens the **Sorting** tool tab, where the sort settings can be edited.


# QuickImages
The **Selected** button adds labels to selected atoms and bonds in the model. If nothing is selected, all atoms and bonds will be labelled. The **non-H** button adds labels to all non-hydrogen atoms, and the **No Labels** button removes all labels from the model. Clicking the **Go** button will create an image of the labelled model in the current working folder. To edit all image file options, open the **Images** tool tab by clicking the pencil icon next to the **Go** button.


[comment]: < The text below is legacy help documentation that doesn't seem to be used anywhere. >


# shift-move-target
Move Atoms
- Hold down SHIFT
- Move atoms with left mouse button
Split Atoms
- Click on an atom to split it

# FVAR Display

The Free Variables (FVAR) that are used in the refinement are displayed here. There is always at least one of these free variable, which is used internally for the overall scaling.
<br>
<br>

More free variable can be added, and are usually used for the 'linked' refinement of disordered parts. For example, if a group is disordered over two positions, then the total number of each atom in that group must be equal to 1. At the same time, all atoms in each group must have the same occupancy. The concept of the free variable can be used quite easily to achieve this: Let's say that all atoms in PART 1 have the occupancy of the value of FVAR 2, then all atoms in PART 2 must have an occupancy of (1 - FVAR 2). FVAR 2 is simply the second free variable in the list.
<br>
<br>

In most cases of disorder, only one such extra free variable will be needed. But sometimes it may be necessary that 2 or three extra ones are required.
<br>
<br>

NOTE: If values of free variable become similar, then this is a sign that too many of these have been used.

