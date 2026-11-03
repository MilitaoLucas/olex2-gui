# Olex2 Restraints and Constraints
This is a list of restraints and constraints specific to Olex2. These can be invoked when using the olex2.refine refinement engine.

## RRINGS
Restrains all provided rings (e.g., C6, C5N, SC4) to be regular, i.e., flat with all interatomic distances similar.

## TRIA
Restrains three atoms so that the distance between the central atom and the two specified bound atoms is the same. (Adds a distance restraint for the atom pairs and an "angle" restraint for the atom triplet.)

## ADPUEQ
Restrains the ADPs of the selected atoms to the Ueq value provided. If no value is provided, the selected atoms will be restrained to be the same.

## ADPVOL
The volumes of the ADP ellipsoids of the selected atoms will be restrained to be the same.

## ANGLE
Applies a restraint to a bond angle. Select three atoms or two bonds to define an angle, then restrain the angle by typing '<c>restrain angle [value]</c>' to [value] in degrees.

## DIANG
Restrains a dihedral (torsion) angle. Select four atoms or three bonds to define a dihedral angle, then restrain the dihedral angle by typing '<c>restrain dihedral [value]</c>' to [value] in degrees.