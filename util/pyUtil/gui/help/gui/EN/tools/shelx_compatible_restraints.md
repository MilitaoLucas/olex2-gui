# Shelx Restraints
These are SHELX restraints. All of these will also apply to a refinement with olex2.refine. Click the **go** button to apply the restraint to the selected atom(s).


# DFIX
Usage: **DFIX d s[0.02] atom pair(s)**<br>
Restrains a distance **d** between pairs of atoms to a given value in &Aring; within an estimated standard deviation of &plusmn; **s** (default 0.02 &Aring;)
<br>
<br>

**Example:** &nbsp; *DFIX 1.54 0.01 C1 C2 C2 C3 C3 C4*<br>
Restrains the C-C bond distances of neighboring carbons in a butyl group to be 1.54 &plusmn; 0.01 &Aring;, i.e., between 1.53 and 1.55 &Aring;.
![0.3 n-butane](images/butane.jpg)


# DANG
Usage: **DANG d s[0.04] atom pairs**<br>
Restrains the "1,3 distance" or "angle distance" (distances between two atoms bound to a third, central atom) to a value **d**, within an estimated standard deviation of &plusmn; **s** (default 0.04 &Aring;).
<br>
<br>

**Example:** &nbsp; *DANG  1.33 0.02 H1 H2*<br>
Restrains the H-H distance in a water molecule to be 1.33 &plusmn; 0.02 &Aring;.


# SADI
Usage: **SADI s[0.02] atom pairs**
<br>
<br>

Restrains bond lengths between given atom pairs to the same distance within an estimated standard deviation of &plusmn; **s** (default 0.02 &Aring;).
<br>
<br>

**Example:** &nbsp; *SADI 0.005&nbsp;&nbsp;C1 F1&nbsp;&nbsp;&nbsp;C1 F2&nbsp;&nbsp;&nbsp;C1 F3*<br>
Restrains a CF<sub>3</sub> group to have the same C-F distances (within &plusmn;0.005 &Aring;).


# CHIV
Usage: **CHIV V[0] s[0.1] atomnames**
<br>
<br>

Restrains the "chiral volume" of the named atoms to a volume **V** &Aring;<sup>3</sup> within &plusmn; **s** &Aring;. The "chiral volume" is the volume of the parallelepiped formed using as its edges the three shortest bonds from the named atom to exactly three other non-hydrogen atoms. 


# FLAT
Usage: **FLAT s[0.1] four or more atoms**
<br>
<br>

Restrains the named atoms to lie in a plane.
<br>
<br>

**Example:** &nbsp; *FLAT C1 C2 C3 C4 C5 C6 C7*<br>
Restrains the seven carbon atoms of a toluene molecule to lie in a plane.


# DELU
Usage: **DELU s1[0.01] s2[0.01] atomnames**
<br>
<br>

Applies a "rigid-bond" restraint to the bonds in the list of named atoms. For adjacent atoms, this restrains the components of the anisotropic displacement parameters in the direction of the bond to be equal within &plusmn; **s1** &Aring;. A similar restraint is applied to 1,3 distances using **s2**.


# SIMU
Usage: **SIMU s[0.04] st[0.08] dmax[2.0] atomnames**
<br>
<br>

Named atoms closer than **dmax** are restrained to have the same Uij components (anisotropic displacement parameters, ADPs) within &plusmn; **s** &Aring;.
<br>
<br>

**Example:** &nbsp; *SIMU C1 C2 C3 O1*<br>
Restrains the ADPs of the atoms of an acetone molecule to be similar.


# ISOR
Usage: **ISOR s[0.1] st[0.2] atomnames**
<br>
<br>

Restrains the Uij components of the named atoms to isotropic values within &plusmn; **s** (&plusmn; **st** for terminal or isolated atoms). This restrained atoms will have approximately spherical ADPs. Useful for preventing atoms from having grossly misshapen ADPs or becoming non-positive definite (NPD), but not to be used indiscriminately.
<br>
<br>

**Example:** &nbsp; *ISOR C5 C6*<br>
This will restrain the ADPs of atoms C5 and C6 to appear approximately spherical.


# RIGU
Usage: **RIGU s1[0.004] s2[0.004] atomnames**
<br>
<br>

Applies enhanced "rigid-bond" (see **DELU** above) restraints to bonds between adjacent atoms and to 1,3 distances with e.s.d.'s **s1** and **s2**, respectively.
<br>
<br>

**Example:** &nbsp; *RIGU C1 Cl1 Cl2*<br>
Applies enhanced rigid-bond restraints to a dichloromethane molecule.