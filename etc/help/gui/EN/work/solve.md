# Solution Program 
Select the program you want to use for Structure Solution. 

## Choice of Programs 
Olex2 can make use of many structure solution programs such as ShelXS, ShelXD, olex2.solve, SuperFlip, Sir2011, Sir2008.
If these programs are installed in a standard way on your system, Olex2 will find them and they will appear automatically as a choice in the drop-down menu. 

# Solution Method 
Select the method you want to use for Structure Solution. 

## Choice of Methods 
Some solution programs have various methods of structure solution available. Olex2 knows about these and you can choose the method you wish to use from the drop-down menu.

# Set Reflection File 
The reflection file contains all the data that were collected during the x-ray diffraction experiment in a condensed form. 

## hkl  
The standard format for a reflection file is the 'hkl' file. From this drop-down menu, you can choose which file you want to refine your model against. There is no need to rename anything - just choose the file and then press refine. 

# Chemical Formula 
The expected chemical composition for the structure. The presence of heavy atoms in the expected composition when they are not actually present in the structure can adversely affect some structure solution programs and vice-versa. 

# Z 
Z denotes the number of fomula units in the UNIT CELL.

## What is this about? 
For molecular compounds this number is easy to see - just count the number of full molecules in the unit cell. For continuous solids and structures that need to be 'grown' it is not always easy to determine this number.
**Note**: Z' (Z prime) is related to this, and denotes the number of formula units in the asymmetric unit. 

# Space Group 
Usually, you will have determined the space group during data processing. 

## Suggest SG 
Olex2 can also determine the space group. Press the 'Suggest SG' link and the most likely choices will appear in the drop-down box on the right. You can type 'text' to see the full output of the data analysis.
You can also type any space group into the box - when leaving the box, your structure will be set up ready to solve in that new space group. 

Command: `sg`

# Solution Settings Extra 
XXX
