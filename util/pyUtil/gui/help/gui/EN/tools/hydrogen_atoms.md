# HFIX Quickmodes
This tool tab contains common constraints relevant to hydrogen atom placement. Hover over each little symbol to display the ShelX constraint that will be applied to the selected atom(s). When one of the symbols is clicked, Olex2 will enter a mode for the application of that particular constraint. Click on the atom(s) to which the constraint is to be applied, then press '<c>ESC</c>' to exit the mode. It is also possible simply to type the code for the constraint after selecting an atom.


# Toolbar Hydrogen_2
This tool tab provides methods of adding H atoms to the structure with custom X-H bond distances.

## A, D, and HFIX
Type the desired AFIX code into the **A** box, the desired X-H bond length (in &Aring;) into the **D** box, and click **HFIX**. This will enter a mode in which this constraint is applied to any atom(s) clicked (hydrogen atoms will be placed geometrically on the clicked atoms). Press '<c>ESC</c>' to exit the mode.

## H 'Improve'
This feature is taken straight from the syntax of the crystallography graphics program XP. The distances provided in the **HIMP** drop-down menu are typical X-H bond distances observed by neutron diffraction. Selecting a bond distance from this menu enters a mode for assigning this bond distance to X-H bonds. Alternatively, typing a value into the **HIMP** box and pressing '<c> TAB</c>' also enters the mode. Once in the mode, clicking a hydrogen atom will move it along its X-H bond axis to the distance specified in the **HIMP** box.

| `himp 0.983` | This will set all X-H bonds in the structure to 0.983 &Aring;. |


# Toolbar Hydrogen_3
## Add Hydrogen
Clicking this link will place hydrogen atoms geometrically throughout the structure and constrain them according to their respective environments (sp<sup>2</sup>, sp<sup>3</sup>, etc.). To refine any hydrogen atom positions freely, select the atom(s) to which the hydrogens are bonded, type '<c> AFIX 0</c>', then refine again.

## H Labels
Will display the names of all atoms, including hydrogen atoms.

| `labels -h -l` | Show all atom names, including hydrogen atom names. |

## No H Labels
Displays the names of all non-hydrogen atoms.

| `labels -l` | Show all non-hydrogen atom names. |

## Show AFIX
Displays the *AFIX* code (if any) on each hydrogen atom in the structure.

| `labels -h -a` | This shows the *AFIX* constraint code for each hydrogen in the structure. |

## FREE ALL H
Removes all *AFIX* constraints from all hydrogen atoms, and also frees their Uiso values, so that they can be freely refined.

## Hide Q
Hides all electron density peaks (Q peaks) on the screen.


# HTAB Slider
The '<c>htab</c>' instruction provides an analysis of hydrogen bonding in the structure. It can only be used when the asymmetric unit alone is on the screen, but hydrogen bonds to symmetry-equivalent atoms will be shown. The list of hydrogen bonds matching the criteria set by the sliders below is printed in the graphics window.

## Distance
This slider specifies the maximum D-A distance (in &Aring;) for a D-H&middot;&middot;&middot;A interaction in the structure to be counted as a hydrogen bond.

## Angle
This slider specifies the minimum D-H-A angle (in degrees) for a D-H&middot;&middot;&middot;A interaction in the structure to be counted as a hydrogen bond.


# Hydrogen Bond Slider
Slide this indicator to the right to enter a mode showing potential hydrogen bonding interactions at increasingly longer distances. Clicking on any of the broken-line "bonds" growing from an atom will display the portion of the structure to which that atom is hydrogen bonded. Press '<c>ESC</c>' to exit the mode.