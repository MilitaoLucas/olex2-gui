# Match 1
This is a set of tools for matching fragments in the same structure or in two different structures. Please consult the online documentation linked in the **Home** tab for more information.

## Match All Fragments
When the **Match All Fragments** link is clicked, Olex2 will automatically overlay any identical fragments currently displayed. These fragments may be in the same structure or in different structures (e.g., different CIF files) opened with the **Overlay Structure** tool below. The calculated RMS deviation for the matched fragments (overlaid with and without inversion) will be printed in the graphics window. The '<c>match</c>' command can also be typed into the command line.

## UnMatch
Click **UnMatch** to return to the unmatched fragments, or type '<c>fuse</c>'.


# Match 3
Select three atoms (say, A, B, and C) in the first fragment and then three atoms (say, X, Y, and Z) in the second fragment in the order they are to be matched (A to X, B to Y, and C to Z). Click **Match Selected Atoms** to overlay the fragments following the order of selection. To return to the unmatched structure click **UnMatch** or type '<c> fuse</c>'.


# Match 4
## Overlay Structure
Clicking this link allows a second structure to be loaded; the current structure and the newly loaded structure will appear side-by-side on the screen in the **Match** mode. In this mode, clicking on an atom in the original structure and on an atom in the new structure superimposes the two structures. This process of clicking alternately on atoms in the first and second structures can be repeated to improve the alignment of the two structures (a total of three pairs of atoms can be selected). The first pair of atoms selected is directly superimposed, selection of the second pair rotates a structure to minimize the distance between the atoms of the second pair, and selection of the third pair rotates a structure about the line formed by the first and second pair to minimize the distance between atoms of the third pair. The two overlaid structures will be shown with red and green bonds, so that they can be differentiated. Press '<c>Esc</c>' to exit the mode, and type '<c> fuse</c>' to return to normal bonds instead of red and green bonds in the structures.

## Mode Match
Clicking this link enters the **Match** mode in which fragments in a single structure (or in two separate structures) can be superimposed. See **Overlay Structure**, above, for a detailed explanation of the matching process.

## Remove Overlay
Removes the second structure that has been added through the **Overlay Structure** link.
