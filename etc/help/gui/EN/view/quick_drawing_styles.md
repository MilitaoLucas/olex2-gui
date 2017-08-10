# Quick Drawing Styles 
This tool allows you to quickly select from a number of preset drawing styles. If no atoms are selected, then the new style will apply to all atoms, otherwise it will apply only to the current selection.

## Balls & Sticks
Atoms are shown as spheres. The size of the sphere depends on the radius of the atom type represented by the sphere. 

Command: `pers`

## Ellipsoids 
Aniosotropic atoms are shown as ellipsoids. Isotropic atoms are shown as spheres, who'se size depends on the value of the Uiso of the individual atom represented by the sphere. 

Command: `telp n` where default n = 50%

## Wireframe
The structure is shown as a wireframe.

Command: `proj`

## Sphere Packing
Atoms are represented as space-filling spheres.

Command: `sfil`

## Tubes
Atoms are represented as connected tubes.

Command: `tubes`

## Default Style
All display settings are reset to the default values.

Command: `default`

## Polyhedra
Shows the structure in a polyhedral representation.

Command: `mask atoms 37`

# Atom Styles 
The visual style of the atom display can be customised. Clicking on the link will display a periodic table, from where you can start customising your styles.

## About Styles and Scenes
There are two types of style sheets in Olex2 - one deals with the atom objects (styles) and the other deals with the lighting and background settings (scene). Both have to be carefully tuned to each other in order to get good results. To load or save a style or scene, right-click on the background and then follow the relevant links. 

## Modify an Atom Style
Right-click on the atom, then select 'Graphics>Draw Styles'. The form you will see is quite complex, and you will have to experiment with it until you are familiar with what you can do. 

## Anisotropic Atoms
By default, the periodic table will open showing anisotropic atoms. Anisotropic atoms consist of the 'sphere' and the 'rims' - the visual properties of which can be set separately (see the drop-down box in the top right-hand corner of the 'Draw Styles' form). 

## Isotropic Atoms
When you see the periodic table, type the word 'pers' - and you will see a sphere representation of the atoms. You can now modify the settings for the isotropic view of atoms. 

# Bonds
XXX

# Graphical objects
Here are a number of functions one can use to help with arrangement of molecules:
## Cell
Toggles between showing the unit cell OFF/ON.

## Base
Toggles between showing the basis vectors OFF/ON.

## Box Function 1
XXX

## Box Function 2
Draws a box around your mocecule.

## Align
### View
This shows the suggested best view of the molecule.

### Plane
Shows the mean square plane of the molecule.

### Locking Functions
These boxes can be ticked in order to stop the system from rotating, zooming or translating the molecule. You can also choose to lock them all or lock separate components.

# Add Fog
These functions can add a fade to your molecule or the background in order to see the molecule better.
