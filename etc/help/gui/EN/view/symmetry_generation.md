# Symmetry Tools 
Tools for growing your structure, changing the composition/location of the asymmetric unit and viewing the basis vectors and cell. 

## Symmetry Tools 1 
The tools in this row are useful for re-organising parts of a structure if there is more than one moiety present in the structure.

### Move Near 
  1. Select the atom to which you want to move another moiety close to.
  2. Activate the mode by clicking on the 'Move Near' button.
  3. Click on on atom of each moiety that you wish to move close to the previously selected atom
  
Command: `mode move`

### Copy Near 
  1. Select the atom to which you want to copy another moiety close to.
  2. Activate the mode by clicking on the 'Copy Near' button.
  3. Click on on atom of each moiety that you wish to copy close to the previously selected atom
  
Command: `mode move -c`

### Assemble
In cases where parts of your structure have become fragmented or 'disjointed', this command will re-assemble the fragments. 

Commands: `compaq`  `compaq -a` 

## Symmetry Tools 2 
Tools in this row will achieve centering of the moieties in a stucture. 

### Centre on Cell 
All moieties in the structure will be centred on the cell. 

Command: `move` 

### Centre on Largest Part  
All moieties in the structure will be centred on the largest moiety. 

Command: `move`

## Symmetry Tools 3 
These tool switch symmetry related items on the screen on and off. 

### Show Basis  
Displays/Hides the basis vectors of this structure 

Command: `basis`

### Show Cell  
Displays/Hides a drawing of the unit cell 

Command: `cell` 

### Quality
Changes the quality setting in which atoms are drawn. A lower quality can be useful if the computer struggles with larger structures.

Commands: `qual -l qual -m qual -h`

## Symmetry Tools 4 

### Fuse 
Display the asymmetric unit of the structure only. All symmetry generated atoms will be removed. 

Command: `fuse` 

### Grow All 
All symmetry equivalent atoms that are required to show the 'complete' structure will be generated. Of course, in the case of polymeric structures, this is somewhat arbitrary, and more controlled growing conditions will need to be employed. 

Command: `grow` 

# Growing 
Olex2 shows the asymmetric unit by default. The tools combinded here in three drop-down boxes are very powerful, and will allow you to 'assemble' your structure in exactly the way you want it to be. In Olex2 you can keep refining your structure without 'destroying' the assembly you have created.

## Grow

### Grow All
All 'missing' connected symmetry equivalent atoms will be generated. 

Command: `grow`

### Shells
This will grow atoms shell-by-shell from the currently displayed image. 

Command: `grow -s`

### Complete
This will generate all missing symmetry equivalent atoms of an already grown structure, independent of whether these are bound to the main fragment or not. In other words: all solvent molecules and counter-ion will be generated according to what is already shown. 

Command: `grow -w`

### Asym. Unit
Removes all symmetry equivalent atoms and displays the asymmetric unit. 

Command: `fuse`

### Complete shown growing bonds
If you are in a growing mode, then clickable growing bonds will be shown. All of these can be grown with this command:

Command: `grow -b`

## Mode Grow
Similar to grow, but now this command will be executed only after you click on an object. When you enter a growing mode, clickable 'growing bonds' will sprout from atoms where the kind of growing you have asked for is applicable. 

Command: `mode grow`

There are various modifiers for this command: 

### Short Contacts
Will show these growable 'bonds' to those atoms where 'short interactions' exist. 

Command: `mode grow -s` 

### Selection
Will show growable 'bonds' to other occurances of the currently selected atoms.

Command: `mode grow -r` 

Van der Waals Radii
Will show growable 'bonds' to other occurances of the currently selected atoms that are at least the indicated distance away from the selected atom. 

Command: `mode grow -v 2.0`

### Move
when you click on growable bonds the symmetry equivalent atom will be moved to the new position. This is really useful when you are trying to assemble a meaningful asymmetric unit for extended structures (polymers). 

Command: `mode grow -a`

### Shells
This will grow atoms shell-by-shell from the currently displayed image. 

Command: `grow -s`

## Assemble
This tool does not strictly belong to the 'growing' family of tools, but it is frequently used together with the growing tools. It allows you to re-arrange the asymmetric unit contents into a different configuration. 

### Broken Fragments
Sometimes, your structure may become 'broken' - parts that should be bonded are shown as separate fragments. This tool will bring them back together. 

Command: `compaq -a`

### Atom-to-Atom
Similar to the 'Broken Fragments' tool, but a different algorithm is used. 

Command: `compaq -c` 

### Metal Last
In this tool, metal ions are taken out of the equation at first (which is very useful when trying to assemble a ligand!) and then the metal ion is placed at the shortest possible distance. 

Command: `compaq -m`

### Q-Peaks
This will move all electron density peaks as closely to existing atoms as possible. 

Command: `compaq -q` 

# Packing
Packing options to display the packing of your structure. 

## Pack Close Contact 
Use the slider bar to set the distance from atoms that you want clickable growing options to be displayed. 

## Pack Radius 
Move the slider to adjust the radius around the original molecule where symmetry equivalent molecules should be shown. 

## Pack to limits

### Pack to limit
Packs the structure within the limits defined for a, b and c.

### Fill Unit Cell
Displays all atoms within the unit cell.

### Complete Fragments
Completes any fragments that are only partially displayed as a result of the various packing options. 
