# solve-target
Solve the structure


# solve-settings-target
Open the solution settings


# Solution Program
If particular solution programs are installed in a standard way on the system, Olex2 will find them and they will appear automatically as a choice in the **Program** drop-down menu. If they don't appear, please make sure that the directory where they are installed is either on the **System Path**, or has been entered under **Home > Settings > Path**. Ilia Guzei's manual, linked in the **Start** tool tab under the **Home** tab, gives detailed instructions for the installation of solution programs.

## Choice of Programs
Olex2 can make use of many structure solution programs such as:

  - **ShelXT**
  - ShelXS
  - ShelXD
  - olex2.solve
  - SuperFlip
  - Sir2011
  - Sir2008

## Solution Method
Select the method to use for the selected structure solution program. This is only really relevant for **ShelXS** - all other programs only have one solution method!


[comment]: < Help text for "Reflections" is now taken from refine.md. >


# Chemical Formula
The expected chemical composition for the structure. The presence of heavy atoms in the expected composition when they are not actually present in the structure can adversely affect some structure solution programs. Likewise, omitting a heavy atom from the expected composition when one is actually present in the structure can also cause problems in structure solution.

## Z
*Z* denotes the number of formula units in the unit cell. For molecular compounds *Z* is the number of full molecules in the unit cell. For continuous solids and structures that need to be "grown" (see **View > Symmetry Generation > Growing**) it is less easy to determine *Z*, but it is generally the number of formula units in the unit cell.

## Z'
The closely related parameter *Z*' (*Z* prime) denotes the number of formula units in the asymmetric unit.


# Space-Group-help
# Space Group
The space group is usually determined during data acquisition and processing.

## Suggest SG
| `sg` | Olex2 can also determine the space group. Click **Suggest SG** and the most likely choices will appear in the drop-down menu on the right. Type 'text', if necessary, to open a text file containing the full output of the space group likelihood analysis. Select a space group from the drop-down menu before proceeding to refinement. |
<br>
<br>

It is also possible to type a space group directly into the menu box on this line. Click anywhere outside the box to ready the structure for solution in the specified space group.


# Solution Settings Extra
Some solution programs may have associated extra settings not available through the GUI; these extra settings may be specified here.

# CF
There are several variables whose settings can influence the Charge Flipping solution:
<br>
<br>

AMPT - Charge flipping can be done on F, E, or quasi-E.
<br>
<br>

MAPT - Maximum number of attempts to find a Phase Transition 
<br>
<br>

MACM - Maximum number of attempts to get a sharp Correlation Map 
<br>
<br>

MASI - Maximum number of Solving Iterations 