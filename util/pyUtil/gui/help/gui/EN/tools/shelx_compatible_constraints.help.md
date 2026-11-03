# Shelx Constraints
These are ShelX constraints. All of these will also apply to a refinement with olex2.refine.

## AFIX
The **AFIX** instruction is for placing hydrogen atoms in idealized (riding) positions.

## EXYZ
The **EXYZ** instruction is for specifying that two or more atoms share the same *x*, *y*, and *z* coordinates.

## EADP
Specifies that the same anisotropic displacement parameters are to be used for two or more atoms, e.g., the three fluorines of a CF<sub>3</sub> group.


# AFIX
*AFIX* instructions are for placing hydrogen atoms in idealized (riding) positions in a structure.

## Syntax of the AFIX command
Usage: **AFIX mn d[number] sof[11] U[10.08]**
<br>
<br>
From the ShelX manual:<br>
"AFIX applies constraints and/or generates idealized coordinates for all atoms until the next AFIX instruction is read. The digits mn of the AFIX code control two logically quite separate operations. m refers to geometrical operations which are performed before the first refinement cycle (hydrogen atoms are idealized before every cycle), and n sets up constraints which are applied throughout the least-squares refinement. n is always a single digit; m may be two, one or zero digits (the last corresponds to m = 0)." <br>
<br>
For more details, refer to the URL[https://shelx.uni-goettingen.de/shelxl_html.php, ShelX Manual].

## Number drop-down menus
In this row, the first two drop-down menus *after* the constraint menu refer to m and n, respectively, in the *AFIX* command.

## clear
Select any atom(s) to which an *AFIX* command has been applied. Clicking **clear** will remove the *AFIX* command.

## de
Click **de** to enter a mode in which all *AFIX* instructions being applied to the structure are displayed. Also in this mode, the *AFIX* command currently specified in this tool tab can be applied to individual atoms by clicking on them.

## go
Click **go** to apply the *AFIX* command currently specified in this tool tab.


# EXYZ
Usage: **EXYZ atomnames**
<br>
<br>

This command imposes the same *x*, *y*, and *z* coordinates on all the named atoms (used when two or more elements share the same site in a structure, as commonly occurs in minerals). Often combined with *EADP*. The coordinates (and possibly free variable references as well) are taken from the first named atom in the list. An atom must not appear in more than one *EXYZ* instruction.


# EADP
Usage: **EADP atomnames**
<br>
<br>

From the ShelX manual:<br>
"The same isotropic or anisotropic displacement parameters are used for all the named atoms. The displacement parameters (and possibly free variable references) are taken from the first atom in the atom list that is linked to other atoms by EADP. The actual values, free variable references etc. given for the Uij of the other atoms are ignored. The atoms involved must either be all isotropic or all anisotropic. 'Opposite' fluorines of PF<sub>6 </sub> or disordered -CF<sub>3 </sub> groups are good candidates for EADP, e.g.
<br>
<br>

EADP F11 F14<br>
EADP F12 F15<br>
EADP F13 F16<br>
C1 .......<br>
PART 1<br>
F11 ...... 21 ......<br>
F12 ...... 21 ......<br>
F13 ...... 21 ......<br>
PART 2<br>
F14 ...... -21 ......<br>
F15 ...... -21 ......<br>
F16 ...... -21 ......<br>
PART 0
<br>
<br>

EADP applies an (exact) *constraint*. The SIMU instruction *restrains* the Uij components of neighboring atoms to be approximately equal with an appropriate (usually fairly large) esd."
<br>
<br>

For more details, refer to the URL[https://shelx.uni-goettingen.de/shelxl_html.php, ShelX Manual].