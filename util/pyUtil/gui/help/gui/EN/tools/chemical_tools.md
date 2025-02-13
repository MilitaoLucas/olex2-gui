# Elemental Analysis
Elemental analysis, molar mass and simulated mass spectrum.

## Elemental Analysis: CHN
Click this button to calculate the expected values of a CHN analysis from the structure model. The molar mass (molecular weight) in g/mol and a full elemental analysis are also provided. The equivalent line command is '<c>calcCHN</c>'.

## Calculate Molecular Isotope Pattern: Mass Spec
Calculates a simulated molecular isotope pattern for the structure using the natural abundances of all isotopes. Equivalent to typing '<c>calcms</c>' at the command prompt. 


# Molecular Volume
Total molecular volume and polyhedral volume of individual atoms.

## Molecular Volume
Calculates the total molecular surface area in &Aring;<sup>2</sup> and molecular volume in &Aring;<sup>3</sup>. The line command is '<c> vvol</c>'.

## Calculate Polyhedral Volume
Calculates the volume of a polyhedron defined by the selected atom (line command '<c>calcvol</c>').


# R S Chirality Designations
These tools enable the analysis of chiral carbons in a structure.

## List R/S Designations of Chiral Carbons
Clicking this button prints a list of all the chiral carbons in the asymmetric unit along with the R/S configuration of each. The equivalent line command is '<c>rsa</c>'.

## Label Chiral Carbons as R/S
Click this button to label each chiral carbon on the screen with its respective R or S configuration.


# Bounding Box and Geometry Index
Display a rectangular bounding box or calculate a geometry index.

## Molecular Bounding Box
Click this button (or type '<c>wbox</c>') to display a rectangular box surrounding the structure on the screen. The structure will be shown in space-filling view, and the dimensions and volume of the box will be printed on the screen. To remove the box, right-click on it with the mouse and select **Hide**. To return to a ball-and-stick view of the structure, type '<c>pers</c>'.

## Geometry Index
For 4-coordinate and 5-coordinate geometries, this will calculate the **Geometry Index** of the central atom URL[https://en.wikipedia.org/wiki/Geometry_index,WIKIPEDIA]. The procedure and relevant citations can be found in the linked Wikipedia article.

### 4-coordinate
A parameter &tau;<sub>4</sub> is calculated from the bond angles about a selected tetracoordinate atom. This parameter provides a measure of whether the geometry around the selected atom is square planar (&tau;<sub>4</sub> = 0) or tetrahedral (&tau;<sub>4</sub> = 1).
<br>
<br>

An additional parameter &tau;<sub>4</sub>' is also calculated, which will always be less than or equal to &tau;<sub>4</sub>. The parameter &tau;<sub>4</sub>' is also 0 for square planar geometry and 1 for tetrahedral geometry. However, &tau;<sub>4</sub>' can be used to distinguish other forms besides the square planar and tetrahedral geometries, such as the seesaw geometry, for which &tau;<sub>4</sub> &asymp; 0.43 and &tau;<sub>4</sub>' &asymp; 0.24.

### 5-coordinate
A parameter &tau;<sub>5</sub> is calculated from the bond angles about a selected pentacoordinate atom, which measures whether the geometry around that atom is square pyramidal (&tau;<sub>5</sub> = 0) or trigonal bipyramidal (&tau;<sub>5</sub> = 1).



