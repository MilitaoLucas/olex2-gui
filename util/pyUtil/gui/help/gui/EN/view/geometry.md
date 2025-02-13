# Geometry
Tools to analyse various geometrical parameters of a structure may be found here.


# Mean Plane and Best Line
## Calculate Mean Plane
Select three or more atoms through which to construct a plane, then click this button or type '<c>mpln sel</c>'. A best-fit plane through the selected atoms will be displayed along with the centroid of the plane. The output contains the equation for the plane and the hkl direction of the plane normal, as well as the RMS deviation (in &Aring;) of the atomic positions from the plane. All symmetry-equivalent planes will automatically be added to any other fragments on the screen. To delete a plane, click on it and press '<c>Delete</c>' (or hide it by right-clicking on the plane and choosing **Hide** from the **Graphics** submenu that appears). If all displayed planes are to be deleted, type '<c>sel planes</c>' to select them all before pressing '<c>Delete</c>'.

## Calculate Best Line
Select two or more atoms through which a best-fit line is to be drawn. Clicking this button will calculate the best-fit line through the atoms and display it in a similar manner to a bond.


# Distances and Angles
## Distances and Angles
Displays the interatomic distance (for two selected atoms), the angle (for three selected atoms) or the torsion angle and tetrahedron volume (for four selected atoms) in the output window.

Note: For accurate e.s.d. values to be displayed for these parameters, a refinement must first be carried out with the **Refine and Save e.s.d. Info** button.

## Refine and Save e.s.d. Info
Carries out a refinement to save the information needed to display accurate e.s.d. information for parameters such as bond lengths and bond angles.


# Analyse Interactions
Analyse non-bonding interactions in a structure.

## &pi;-&pi; Interactions
Searches for &pi;-&pi; interactions in the structure; if any are found, the relevant geometric parameters (e.g., the distance between the centroids of adjacent aromatic rings) are printed in the output window.

## Hydrogen Bonds
Finds and displays any hydrogen bonds in the structure. The equivalent line command is '<c>htab -g</c>'. In both cases, a table is printed in the output window.
<br>
<br>

Another useful command for analysing nonbonding interactions is '<c>htab -t</c>'. For example, '<c>htab -t=Br,I</c>' would cause any Br---I halogen bonds in the structure to be displayed. 