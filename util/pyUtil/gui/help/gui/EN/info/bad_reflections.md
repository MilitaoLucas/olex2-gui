# bad reflections target
Tools for dealing with reflections that do not fit well.


# OMIT REFLECTIONS
The **OMIT** button applies an *OMIT* instruction in the instruction file to all reflections for which |Error/esd| is greater than the value specified in the box (default 10).
<br>
<br>

Clicking the **ClearOMITs** button will delete ALL *OMIT* instructions, and all previously omitted reflections will be made available again for refinement, except those that are omitted with a general *OMIT* instruction, e.g., *OMIT -3 52*.


# Bad Reflections Sorting
If this box is ticked, bad reflections will be sorted in order of decreasing |Error/esd| once another cycle of refinement is carried out. If, on the other hand, the box is not ticked, bad reflections will be sorted in order from largest positive Error/esd to largest negative Error/esd in the next refinement cycle.


# Bad Reflections
This panel contains the reflections determined by the refinement program to have the largest values of |Error/esd|.

## Omit all equivalents of a reflection
Exclude an individual reflection (and all its equivalents) by pressing the **OMIT** link next to it in the list. This will insert the appropriate *OMIT* command in the instruction file.


# Exclude hkl
Conditions for specific groups of reflections to be excluded can be set here.

## Standard Mode (OR)
When the **Exclude:** link is clicked, all reflections satisfying the specified conditions on *h*, *k*, OR *l* will be omitted from the next refinement cycle.

## AND Mode
When the **AND** box is ticked, the conditions specified for *h*, *k*, AND *l* must be fulfilled for a reflection to be omitted from the refinement when the **Exclude:** link is clicked.

## Reset
Clicking the **Reset** link clears all currently set exclusion conditions on *h*, *k*, and *l*.


# Edit reflections
It is also possible to omit a particular reflection (e.g., because it was obscured by the beam stop). To do so, click the **Edit Reflections** link to open a file listing all the bad reflections. Adding a "-" symbol (minus sign) in front of a particular reflection moves it to the bottom of the hkl file (after the "0 0 0" instruction), which instructs the refinement program to ignore it. Replacing the "-" symbol in front of an omitted reflection in this file with a "+" symbol will again include the reflection in the next refinement cycle.