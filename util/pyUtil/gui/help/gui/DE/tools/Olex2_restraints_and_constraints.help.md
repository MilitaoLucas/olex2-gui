# Olex2 Restraints and Constraints
Eine Liste der Restraints und Constraints, die es nur in Olex2 gibt. Sie lassen sich mit dem Verfeinerungsprogramm olex2.refine verwenden.

## RRINGS
Restraint, der alle angegebenen Ringe (z.B. C6, C5N, SC4) regelmäßig macht, d.h. eben mit ähnlichen Atomabständen.

## TRIA
Restraint für drei Atome, sodass die Abstände vom zentralen Atom zu den beiden angegebenen gebundenen Atomen gleich sind. (Fügt einen Abstands-Restraint für die Atompaare und einen "Winkel"-Restraint für das Atomtripel hinzu.)

## ADPUEQ
Restraint, der die ADPs der ausgewählten Atome auf den angegebenen Ueq-Wert zieht. Ohne Wert werden die ausgewählten Atome auf gleiche ADPs gezogen.

## ADPVOL
Die Volumina der ADP-Ellipsoide der ausgewählten Atome werden per Restraint gleich gehalten.

## ANGLE
Restraint für einen Bindungswinkel. Drei Atome oder zwei Bindungen auswählen, um den Winkel festzulegen, dann mit '<c>restrain angle [Wert]</c>' auf [Wert] Grad festlegen.

## DIANG
Restraint für einen Diederwinkel (Torsionswinkel). Vier Atome oder drei Bindungen auswählen, um den Diederwinkel festzulegen, dann mit '<c>restrain dihedral [Wert]</c>' auf [Wert] Grad festlegen.
