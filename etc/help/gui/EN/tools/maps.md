# Xgrid 

## Available Display Modes

### contour, plane  
This is an interactive slice of the map in the plane of the screen. The molecule can be rotated and also zoomed through this plane. This is done by holding down the **SHIFT** key while dragging the left mouse key on the area of the map or using the depth slider. The visible area of the map can be adjusted with the size slider, or by holding down the **CTRL** key whilst dragging the right mouse key. Finally, the levels can be adjusted with the **SHIFT** key and right mouse key. In contour mode, the number of contours can be altered with the contours slider. Positive electron density is displayed as solid lines, whilst negative electron density (holes) are displayed as dashed lines. A contour map will be included in any postscript drawing created whilst the map is displayed.

### surface, wire, point  
These are all three dimensional displays of the electron density. However, the 3D display will only work if there is enough electron density to display, otherwise the 2D display will the shown. It is a good idea to start adjusting the levels in the points view, and only then to select wire or surface for a graphically more demanding display. Negative values of electron density (holes) will be displayed in a reddish colour. The extended mode will extend the grid to an array of 27 (3 x 3 x 3) unit cells.

### Extended 
Will extend the map display out from the unit cell.

### Edit Style 
Edits the colour of the various map surfaces.

### Select Volume  
A box with moveable sides will appear. Left-click on the coloured areas and then move the sides while pressing the **SHIFT** key. The map will be calculated only inside the defined box. You can delete the box by right-clicking on it and select 'Hide'.

### Level 
When a map is displayed the slider bar enables you to adjust the detail shown in the map. 

# Calculate Voids 
Calculates the voids and channels in the structure. This calculation is based on the Olex2 internal libraries, and help is available from `help calcvoid`

# Calculate Solvent Accessible Voids 
Calculates the solvent accessible voids. This calculation is based on the smtbx/cctbx Olex2 libraries. 

Command: `calcsolv`

Calculates voids that are large enough to contain solvent. Probe/Å adjusts the probe size (think of it as a 'sphere' rolling about the structure - a smaller sphere will fit into smaller gaps and therefore return a larger void than a larger sphere would). The Grid/Å is the resolution of the map that will be explored when calculating the voids. If the resolution is too high, the calculation might take a Very Long Time at not much benefit. Click on Void to toggle between displaying and not dis-playing solvent accessible voids. On the graphics screen the size of any solvent accessible voids that are found will be displayed. 

# Electron density
XXX

# Masks 
The Masks option serves as an alternative to SQUEEZE which is implemented in Platon !!!More Info Online!!!. These sorts of approaches should only be used when the solvent can't be identified or modelled, effort should be made to try and identify or model solvent. If refinement has been attempted using both ShelXL and olex2.refine the option to select either olex or an .fcf files, ensure that the file from the last cycle of refinement is used. 
