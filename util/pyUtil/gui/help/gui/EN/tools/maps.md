# Map View
## Available Display Modes
The **plane**, **contour**, **surface**, **wire**, and **points** options shown under the **View** drop-down menu are different viewing styles available for displaying maps and masks in Olex2.

### plane, contour, contour+plane
These three views show an interactive 2D slice of a map, i.e., a display of a parameter such as the calculated electron density, in the plane of the screen. The structure can be rotated, moved or zoomed while the map is displayed, and the 2D slice will change accordingly as different portions of the structure pass through the plane.

### Colours
Select the number of colours in the colour scale of a 2D map display in **plane** and **contour+plane** modes from this drop-down menu.

### surface, wire, points
These three views show a 3D display of a parameter, such as the calculated electron density, overlaid on the structure. If there is insufficient electron density, however, only the 2D display will the shown. If the computer struggles to display these maps, first adjust the display levels in the **points** view, then select **wire** or **surface**, since the latter are more computationally demanding graphics displays. 
<br>
<br>

In the **surface**, **wire**, and **points** display modes, positive values of electron density are shown in green and negative values (holes) in red, providing a very powerful tool for checking the validity of a structure during refinement. Thus, for example, if the **diff** (difference between Fobs and Fcalc) map for a structure is displayed in the **wire** view and a hydrogen atom is encased in a red blob, with a green blob nearby, then that hydrogen should probably be moved to the position of the green blob if the new position is chemically reasonable. A useful keyboard shortcut to display the **diff** map is '<c>CTRL+M</c>'.

### Extended
Ticking this box will extend the map display out from one unit cell to 27 adjacent unit cells, a 3 x 3 x 3 stack. This is very useful for viewing the shapes, sizes, and distribution of voids in the structure.

### Edit
Click this button to edit the colour properties of the various map surfaces.


# 2D Map Contours
This slider selects either the maximum number of contour lines (for the **contour** and **contour+plane** view) or the number of colours (for the **plane** and **contour+plane** views). In **contour** view, regions of positive electron density are displayed as solid lines, whilst regions of negative electron density (holes) are displayed as dashed lines. A contour map will be included in any PostScript drawing created whilst the map is displayed.
<br>
<br>

~Hint:~ If symmetrical maps around 0 are desired, then select, e.g., 21 contours, giving 10 above 0, 10 below 0 and one for the 0 level itself. 


# 2D Map Scale
This option sets the maximum and minimum of the electron density in a map. Clicking **Automatic** (the default setting) will adjust the map display so that the minimum and maximum on the map legend match the minimum and maximum electron density in the *current* map slice. **Static**, on the other hand, leaves these minimum and maximum values fixed at the *global* minimum and maximum, respectively, no matter what slice is currently shown.


# 2D Static Map Scale
## Min
Use this slider to define the minimum value of the parameter displayed on the map. The slider adjusts the minimum in quarter-integer values but also accepts manual input in the text box next to it.

## Step
This slider defines the step size between two adjacent contours/colours. As with **Min**, this slider has pre-defined slider values (difference 0.02), but a specific value can also be typed into the text box.


# 2D Map Position and Size
## Depth
This slider controls the depth of the map plane "into" the screen. More negative values of **Depth** move the map further into the screen until the map is "behind" the model. More positive values move the map further out of the screen until the map is "in front" of the model. Different parts of the structure will move through the 2D slice as **Depth** is changed. Alternatively, to move the map perpendicular to the screen (i.e., into or out of the screen), hold down the '<c>SHIFT</c>' key while dragging the left mouse button in the map area. A little care must be taken to drag in an area of the map itself, not on the structure.
<br>
<br>

Select three or more atoms and click on the **Depth** button to align the map with the mean plane through the selected atoms. The mean plane will also be displayed; to remove it, left-click on it and press '<c>Delete<c>'.

## Size
The **Size** slider controls the size of the plotted map. Larger values will actually *decrease* the size of the map on the screen, but will *increase* the map resolution. The visible area of the map can also be adjusted by holding down the '<c>CTRL</c>' key whilst dragging the right mouse button in the map area.


# Map 3D
The **Level** slider adjusts the level of detail desired in the displayed map. A value can also be entered into the box next to the slider. If the level is set high, only the most prominent features (i.e., biggest electron density peaks and holes) will be shown. If the level is low, on the other hand, many more peaks and holes will be displayed. Below a certain cutoff level, however, the features of the map become so overwhelmed by the noise in the data that the map becomes overcrowded and meaningless, besides being slow to display. To avoid this, the level will be locked at and below the cutoff level.


# Electron Density
This tool tab is for displaying various electron density maps. The specific parameter to be mapped is selected from the **Map** drop-down menu.

## Map
Select from the drop-down menu the type of map to display.

### diff
Will display the difference map, Fobs-Fcalc. Make sure to select **surface**, **wire**, or **points** from the **View** drop-down menu under the **Maps** tool tab (accessed through **Map Settings** in this tool tab) for this map to be displayed correctly. The corresponding line command is '<c>CalcFourier -diff -r=0.1 -m</c>' or simply '<c>CTRL+M</c>'. This is an extremely important tool for checking the validity of a model. Red regions of the map represent areas of missing electron density and green regions represent areas of excess electron density.

### fcalc
Will display a map of the calculated electron density (Fcalc).

### 2Fo-Fc
Will display the map of 2Fobs-Fcalc.

### fobs
Will display a map of the observed or experimentally measured electron density (Fobs).

### fcfmc
Will display the FCF Fc-Fc map.

## Source
Select from this drop-down menu a data source to be used in constructing the map.

## Res/&Aring;
Type in the desired resolution (in &Aring;) for the map.

## Mask
If the **Mask** box is ticked, all electron density features (peaks or holes) near the structure on the screen will be displayed. If the box is left unticked, only electron density features within the unit cell will be displayed.

## Show/Hide Map
Toggles the display of the map on the screen.


# Calculate Voids
Calculates the voids and channels in the structure, if present. This calculation uses the Olex2 internal libraries. For further information, type '<c>help calcvoid</c>' or click the button below.

| `help calcvoid` | Help entry for the '<c>calcvoid</c>' command. |

## Resolution/&Aring;
Specify the resolution of the void map here, in &Aring;.

## Distance/&Aring;
Specify any additional distance (in &Aring;) from the van der Waals surface at which the void space is to be calculated.

## Precise
Tick this box for a more precise calculation of the voids in the structure.

## Show/Hide Void
Toggles the display of the voids on the screen. A list of voids (if any) in the structure is also printed in the graphics window. When the **Extended** option at the top of this tool tab is checked, the voids are displayed in a 3 x 3 x 3 stack of adjacent unit cells, which can be helpful in visualizing void shapes.


# Calculate Solvent Accessible Voids
This checks for the presence of voids in the structure large enough to hold a solvent. This calculation is based on the smtbx/cctbx Olex2 libraries, and provides an alternative algorithm to '<c>calcvoid</c>' above for detecting voids in the structure. No map is produced, but a list of voids is printed in the graphics window.

## Probe/&Aring;
This adjusts the size (in &Aring) of a spherical "probe" that rolls about the structure, fitting into gaps and mapping out any cavities that may be present. A smaller sphere would fit into smaller gaps and therefore return a larger void size.

## Grid/&Aring;
This governs the resolution of the solvent void map. If the grid is set too high, the calculation will take a very long time, without producing a much improved map.

## Show Info
A list of solvent-accessible voids (if any) in the structure is printed in the graphics window.


# Masks
The **Masks** tool tab offers an alternative to the well-known ~SQUEEZE~ routine in ~Platon~ for dealing with disordered solvent. Search online for "modelling solvent disorder" for more information. This sort of approach should only be used as a last resort when the solvent cannot be identified or modelled because of the severity of the disorder. Every effort should first be made to identify and model the solvent using the **Disorder Tools** in the **Work** tab and **FragmentDB** in the **Tools** tab. If refinement has been attempted using both ShelXL and olex2.refine, when the option appears to select either an olex or fcf file, ensure that the file from the last cycle of refinement is used.
<br>
<br>

See B. Rees et al., Acta Cryst. D61, 2005, 1299-1301 for more details on the algorithm used in this calculation.

## Reflection File
Select a .hkl file for use in the calculation of the mask.

## Use set completion
If low angle reflections are missing (even one is sometimes enough), the electron count in a cavity may be underestimated. If this option is selected, missing reflections are filled in and allowed to "float" throughout the Fourier transform iterations, resulting in more accurate estimates of the true electron count.

## Show/Hide Void
Toggles the display of the voids on the screen. A list of voids (if any) in the structure is also printed in the graphics window. When the **Extended** option at the top of this tool tab is checked, the voids are displayed in a 3 x 3 x 3 stack of adjacent unit cells, which can be helpful in visualizing void shapes.

## Map
Select **mask** from the **Map** drop-down menu to view the solvent-accessible voids in the structure. Selecting **f\_mask** displays the Fourier transform of the solvent contribution to the structure factors. Lastly, selecting **f\_model** displays the Fourier transform of the sum of contributions to the structure factors of both the solvent region and the ordered part of the structure.

## Grid/&Aring;
The **Grid** parameter is the resolution of the map, in &Aring;. The entire structure, both atoms and solvent void regions, is divided into grid points given by this resolution in order to calculate the mask.

## Solvent R in &Aring;
All grid points at a distance greater than the sum of the van der Waals radius of an atom in the structure and **Solvent R** are initially set to be inside the solvent void region. The default value is 1.2 &Aring;, which is large enough to avoid displaying voids in which no atom could fit.

## Shrink truncation R in &Aring;
After **Solvent R** above has been used to determine the solvent void region, all grid points outside this region are tested to see if they fall within a distance **Shrink truncation R** of the region. If this is the case, they are added to the solvent void region. **Shrink truncation R** is generally very close, or equal, to **Solvent R**. The process involving **Shrink truncation R** essentially results in a more close-fitting mask of the solvent void region.


[comment]: < The text below is legacy help documentation that doesn't seem to be used anywhere. >


# masks-help

### Select Volume
A box with moveable sides will appear. Left-click on the coloured areas and then move the sides while pressing the **SHIFT** key. The map will be calculated only inside the defined box. You can delete the box by right-clicking on it and select 'Hide'.
