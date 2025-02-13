# Symmetry Tools
This tool tab features a set of buttons for changing the appearance/location of the asymmetric unit; expanding ("growing") a structure on the screen; viewing the basis vectors and unit cell; and other similar tasks.


# symmetry tools 1
The tools in this row are useful for reorganising parts of a structure containing more than one moiety.

## Move Near
This is useful for moving moieties of a structure close to a particular atom of interest.
<br>
<br>

  1. Click on an atom near which another moiety is to be moved.
  2. Activate the mode by clicking on the **Move Near** button (or typing '<c>mode move</c>').
  3. Click on an atom of each moiety that is to be moved close to the initially selected atom.

| `mode move` | |

## Copy Near
This is a slightly different method for collecting moieties of a structure close to a particular atom of interest.
<br>
<br>

  1. Click on an atom near which another moiety is to be copied.
  2. Activate the mode by clicking on the **Copy Near** button (or typing '<c>mode move -c</c>').
  3. Click on an atom of each moiety that is to be copied close to the initially selected atom.

| `mode move -c` | |

## Assemble
| `compaq` | This command brings the various fragments of a structure as close together as possible on the screen. |

| `compaq -a` | Brings fragments of a structure together as above, but also assembles any "broken" fragments. |


# symmetry tools 2
These buttons centre the moieties in a structure in different ways.

## Centre on Cell
| `move` | All moieties in the structure will be centred within the cell. |

## Centre on Largest Part
| `move` | All moieties in the structure will be centred on the largest moiety. |


# symmetry tools 3
These tools toggle the display of symmetry-related items on the screen.

## Show Basis
| `basis` | Displays/Hides the basis vectors of this structure. |

## Show Cell
| `cell` | Displays/Hides the edges of the unit cell. |

## Quality
Use the slider to change the quality of the display graphics from low (far left) to medium (middle) to high (far right). A lower quality setting may be useful if the computer struggles to display large structures.

| `qual -l` , `qual -m` , `qual -h` | Changes the quality of the display graphics to low, medium, or high. |


# symmetry tools 4
These two important commands contract and expand the extent of the structure displayed on the screen.

## Fuse
| `fuse` | Display the asymmetric unit of the structure only. All symmetry-generated atoms will be removed. This is a command of fundamental importance. |

## Grow All
| `grow` | All symmetry-equivalent atoms required to show the "complete" structure will be displayed. In the case of polymeric structures, this is somewhat arbitrary, and more clearly defined '<c>grow</c>' commands may need to be issued to display the structure as desired. See the **Growing** tool tab help for more options. |


[comment]: < Help text for "Growing" is now taken from toolbox_work.md. >


# Packing
This tool tab provides methods of visualizing the 3D packing of a structure.


# Expand Short Contacts
Use this slider bar to define the minimum distance for interatomic "short contacts" such as hydrogen bonds or halogen bonds. As the slider moves to the right, more clickable "bonds" will be shown from atoms meeting the contact criterion. Alternatively, a number can be entered in the box next to the slider. Clicking on one of these "bonds" expands the display of the structure in the direction of the bond.


# Pack Radius
Move the slider to the right to show all symmetry-equivalent fragments around the current structure within the specified radius. It is also possible to type a number into the box adjacent to the slider.


# Pack Limits
This packs one or more unit cells to the limits specified, including fractional limits.

## Pack to limits
Displays all fragments of the structure within the limits defined for unit cell edges *a*, *b* and *c*. The numbers in the box are multiples of the edge lengths.

## Fill Unit Cell
Displays only those atoms lying within the unit cell.

## Complete Fragments
Completes any fragments that are only partially displayed as a result of the various packing options. This is often useful after the **Fill Unit Cell** command.