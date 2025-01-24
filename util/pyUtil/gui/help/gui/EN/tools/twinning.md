# Twinning-help
# Twinning
These tools provide methods of determining whether a structure is twinned, and if so, to calculate the twin law. The first two buttons on this row are for searching for twin laws, while the third button is to determine whether a structure is twinned.

## Find 2-fold
Clicking **Find 2-fold** initiates a rapid search for 2-fold twin laws applicable to the structure. If a viable twin law is found, the corresponding transformation matrix will be printed in the output window. For example, suppose a 2-fold twin law is found with the following transformation matrix:
<br>
<br>

-1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0
<br>
0 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; -1 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0
<br>
2/3 &nbsp;&nbsp;&nbsp;&nbsp; 0 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1
<br>
<br>

The twin law search will also suggest a *BASF* (batch scale factor, or fractional contribution of one of the twin components). If the suggested *BASF* is 0.204, entering the following two statements in the .ins file will take into account the observed twinning during subsequent refinement:
<br>
<br>

TWIN -1 0 0&nbsp;&nbsp;&nbsp;0 -1 0&nbsp;&nbsp;&nbsp;0.667 0 1&nbsp;&nbsp;&nbsp;2
<br>
BASF 0.204
<br>
<br>

(The 2 at the end of the *TWIN* instruction is to specify a two-component twin.)

## Find all Twinning
This searches for *all* twin laws applicable to the structure, not just the common 2-fold twin laws. If any are found, the corresponding transformation matrix and *BASF* will be printed at the bottom of this tool tab.

## Cumulative Plot
**Cumulative Plot** opens the cumulative intensity distribution plot for the experimentally observed reflections. If the data points in the plot lie mostly along the bottom (red) line, the structure is very likely twinned.


# General
This row contains the general settings that will be applied to all methods of searching for twin laws.

## Extended
When this box is ticked, any twin law searches will be run in "extended" mode, i.e., more exhaustive (and therefore more time-consuming) searches will be performed. If no twin laws are found with this box unticked, then repeating the search with the box ticked may find a twin law missed by a normal search.

## Min. Laws
The minimum number of viable twin laws to return. Setting a low number in this box speeds up the search, as the search terminates once the specified number of twin laws is found. However, they may be inferior to other applicable laws that may have been missed by setting **Min. Laws** too low. If the twin laws initially returned do not properly account for the twinning in the structure, increase this number and repeat the search.

## Threshold for all searches
This threshold is the separation below which two points in reciprocal space (i.e., reflections) are considered to overlap. A larger value will suggest more potential twin laws for consideration, but may return laws that do not accurately describe the twinning in the structure; a smaller threshold will return fewer, more accurate laws.

# Spherical Angle Axis
This tool tab offers two further ways to search for twin laws: **Spherical** and **Angle-Axis**.
<br>
<br>

The **Spherical** search method directly uses strong reflections, and the potential points they could map to on a sphere, to calculate viable twin laws for the structure. It is in general a faster search which searches less space whilst finding more laws, and is not restricted by the angle of rotation of the twin law. **Spherical** searching is strongly affected by the minimum law number, so if this search method yields poor results, increase **Min. Laws** and repeat the search.
<br>
<br>

The **Angle-Axis** search method, on the other hand, searches step-by-step for rotational twin laws by considering potential twin axes and rotations about them. Axes are taken from integer points in both direct and reciprocal space.
<br>
<br>

To try the first search method, first select the number of bad reflections to evaluate and then click **Spherical**. Specify **Max Index** and **Rot. Fract'n**, and click **Angle-Axis** to try the second.

## Bad Refl'ns
Specify the number of bad reflections to use in the **Spherical** twin law search method. These are taken from the list in the **Bad Reflections** tool tab under the **Info** tab.

## Spherical
Click this button to initiate a **Spherical** search for applicable twin laws.

## Max index
This variable specifies the highest value of *h*, *k*, or *l* to use when searching for twin laws by the **Angle-Axis** method. A higher **Max Index** will find more twin laws, but the search will take longer.

## Rot. Fract'n
The rotation fraction *n* governs the angle 360&deg;/<i>n</i>, which is the step size of rotation about each axis during an **Angle-Axis** search. Increasing this variable will lead to finer steps and thereby to more twin laws.

## Angle-Axis
Click this button to initiate an **Angle-Axis** search for applicable twin laws.


[comment]: < Help text for "hkl file" is now taken from refine.md. >


# Set HKLF5 Reflection File
The HKLF5 file format is used exclusively for twinned structures, but is not always necessary if the structure is twinned. It is similar to the ordinary HKLF4 file format, but contains an additional data column identifying the twin component to which each reflection belongs. A file of this type *is* required for non-merohedral twinning, when the reciprocal lattices of the twin components cannot be exactly superimposed on one another.