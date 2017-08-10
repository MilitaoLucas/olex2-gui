# Fragment Library 
This link will open in your default internet browser. Fragments contained in this library can be copied and pasted straight from the web into Olex2.

## Pasted fragments  
These will appear in a strange green colour, and you can then anchor them onto electron density peaks by first clicking on an atom in the imported fragment and then on the corresponding Q-peak. Repeat this progress with another atom/Q pair until a reasonable match is achieved.

## Exit matching mode  
Press `Esc` repeatedly, or press the `Esc` link in the orange mode box to get out of this matching mode. 

# Link Selected 
**Two** Selected atoms will be 'linked' in the refinement.

## Occupancies 
The occupancies will be linked such that the individual occupancies add up to unity. 

Command: `fvar sel` 

## Parts and Occupancies   
The occupancies will be linked such that the individual occupancies add up to unity, and the selected atoms will be added to Parts.

Commands: `part -p=2 -lo sel`

**Note**: the -p parameter determines the number of parts that should be assigned. -lo stands for 'link occupancy'.

# Link Constraints 
Link Parts, Occupancies and apply either and EADP constraint or ISOR restraint to selected atoms.

# Link Parts 1 
Assign selected atoms to the part number selected. 

# Link Parts 2 
XXX

# Show Parts
If your structure contains atoms that have been assigned to parts, then it is sometimes useful to look only at atoms belonging to the same part. 

Command: `showP 1` Will show only atoms belonging to Part 1.

Command: `showP 0 2` Will only show atoms that don't belong to a Part and those that belong to Part 2. 

Command: `showP 0` Will show all atoms. 

