# Quick Drawing Styles
# cell-target
Draw unit cell


# base-target
Display basis vectors


# Quick Drawing Styles
A number of preset drawing styles can be selected using the buttons in this tool tab. The new style will be applied only to the current selection. If no atoms are selected, the style will be applied to all atoms.

## Balls & Sticks
| `pers` | Atoms are shown as perfect spheres. The size of the sphere depends on the atomic radius of the element represented by the sphere. |

## Ellipsoids
| `telp 50` (n = 50 is the default ) | Anisotropic atoms are shown as ellipsoids. Isotropic atoms are shown as spheres, whose size depends on the Uiso value of the individual atom represented by the sphere. |

## Ellipsoids with hydrogen
Anisotropic atoms are shown as ellipsoids, and hydrogen atoms are shown as spheres with radii proportional to their respective Uiso values.

## Wireframe
| `proj` | The structure model is shown as a wireframe. |

## Sphere Packing
| `sfil` | Atoms are represented as space-filling spheres. |

## Tubes
| `tubes` | The entire model is represented as a set of connected tubes. |

## Polyhedra
| `mask atoms 37` | Shows the structure in a polyhedral representation. |

## Def
| `default` | All display settings are reset to their default values. |

## Light
A display style showing carbon atoms in a light color against a dark background.


[comment]: < Help text for "Atom r" and "Bond r" is now taken from settings.md. >


# Graphical objects
Several of tools are provided here to enhance the visualisation of a structure.

## Cell
Toggles the display of the unit cell on or off.

Note: If the structure is not contained within the displayed unit cell, type '<c>move</c>' to relocate it within the cell.

## Base
Toggles the display of basis vectors.

## Box Function 1
Toggles the display of a translucent box of the same size and shape as the unit cell. The box can be moved and rotated independent of the structure or the unit cell.

## Box Function 2
Select two or more atoms. Clicking this button will toggle the display of a rectangular parallelepiped enclosing those atoms. This box can also be rotated and moved independent of the structure or the unit cell.


[comment]: < The help text given below for "Align and Lock" is the same as in images.md. >


# Align and Lock

## View and Plane
Clicking on one of these links will orient and centre the structure within the display window, which can be useful before creating images. **View** centres and orients a structure on the screen using an algorithm involving the calculation of the structure's principal axes of inertia. **Plane** calculates a mean plane through the entire structure, orients the structure on the screen perpendicular to this plane, and centres the structure on the screen. Neither of these methods changes the zoom level. Typing '<c>mpln -r<c>' displays the mean plane and prints its equation in the output window. To delete the plane, click on it and press '<c>Delete</c>'.
<br>
<br>

A couple of other helpful line commands for realigning the structure on the screen are:

| `center` | Centres the structure without changing orientation or zoom level |

| `compaq -a` | Also centres the structure without changing orientation but does resize the structure to fit within the display area. |

## Lock
When working with images, it is sometimes helpful to lock out certain mouse functions to avoid accidentally changing the orientation or zoom. The zoom, rotation, and translation functions may be individually locked by ticking the appropriate box. For example, if only the **Translation** box is ticked, the structure will remain in a fixed location on the screen, but it will still be possible to rotate it or to zoom in and out. All three functions may be locked simultaneously by ticking the **Lock all** box. 

# Legend Settings
The default position of the legend (the atom types are represented by a sphere) can be set to be top/bottom and left/right -- and the padding from the edge of the display area can also be set.

Note: The atom legend can be moved to any desired location on the screen, e.g., closer to the structure, by holding down the '<c>Shift</c>' key and dragging it with the mouse. The legend display can also be switched off or on with the '<c>legend</c>' line command. To reset the legend (e.g., if it has disappeared), type '<c>legend -r</c>'.

# Add Fog
An artificial "fog" can be applied to the display by clicking the **Add Fog** button. This may be helpful, for example, to emphasise the 3D nature of the structure or to highlight its front-facing portion. The **Front** and **Back** sliders govern the thickness of the "fog". Click **Clear Fog** to remove the fog from the display.


[comment]: < The text below is legacy help documentation that doesn't seem to be used anywhere. >


# Atom Styles
The visual style of the atom display can be customised. Clicking on the link will display a Periodic Table, from where you can start customising your styles.

## About Styles and Scenes
There are two types of style sheets in Olex2 - one deals with the atom objects (styles) and the other deals with the lighting and background settings (scene). Both have to be carefully tuned to each other in order to get good results. To load or save a style or scene, right-click on the background and then follow the relevant links.

## Modify an Atom Style
Right-click on the atom, then select 'Graphics>Draw Styles'. The form you will see is quite complex, and you will have to experiment with it until you are familiar with what you can do.

## Anisotropic Atoms
By default, the periodic table will open showing anisotropic atoms. Anisotropic atoms consist of the 'sphere' and the 'rims' - the visual properties of which can be set separately (see the drop-down box in the top right-hand corner of the 'Draw Styles' form).

## Isotropic Atoms
When you see the periodic table, type the word 'pers' - and you will see a sphere representation of the atoms. You can now modify the settings for the isotropic view of atoms.

# Bonds
TBI
