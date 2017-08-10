# bad-reflections-target
Tools for dealing with reflections that do not fit well

# OMIT REFLECTIONS
The 'OMIT' button allows you to omit all reflections where |Error/esd| > than <value> in the box. The 'Clear omits' clears **all** omits -- all previously omitted reflections will be back for refinement (except those that are omitted with a general OMIT, e.g. 'OMIT -3 52')

# SORT BAD REFLECTIONS
No entry

# LIST BAD REFLECTIONS
**A list of those reflections that have been flagged by the refinement program ShelXL will be shown in this panel.**

## Omit all equivalents of a reflection
You may choose to omit a reflection totally by pressing the OMIT link. This will insert the appropriate OMIT instruction.

## Omit a particular instance of a reflection
You can also choose to omit a particular reflection (e.g. because it was under the beam-stop). To do so, click the <a href=edithkl>Edit Reflections</a> link at the bottom of the list of bad reflections. This will bring up a window with all the reflections in your reflection file, grouped by equivalent reflections. By adding the minus symbol '-' in front of a particular reflections, this reflection will be moved to the bottom of the .hkl file (after the '0 0 0' instruction, which tells the refinement program to ignore it.

# EXCLUDE BY H K AND L
Conditions for reflections to be excluded can be set here

## Standard Mode (OR)
This will exclude all reflections where h, k, and l fulfill the conditions you specify independently

## AND Mode
When the 'AND' tickbox is ticked, the conditions you specify for h, k and l have to be fulfilled simultanesoulsy in the same reflection

# SHOW HKL FILE
No entry

# Edit Reflections
This will display your hkl data sorted by the 'worst fitting' reflections. The Each equivalent occurance of this reflection is shown separately and you can 'omit' just that occurance from the refinment, rather than omit the entire reflection (Olex2 will move it to the end of the file, past the '0 0 0' line). This is particularly useful if you would otherwise omit an entire important reflections.
Please put the '-' character in the front of a reflection you wish to omit and remove this character if from an 'omitted' reflection in order to include it in the refinement again.
