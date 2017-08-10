# Select Atoms 
Selects the atom types listed. 

## Exclusive  
Selects only the types that are clicked on. 

## Additive
Adds the clicked types to the selection.

## Command Line Examples   
Command: `sel $c` (Selects all C atoms)

Command: `sel -u` (Deselects everything)

Command: `sel c1` (Selects C1)

Command: `sel $c $n` (Selects all C and N atoms) 

# Selections 
XXX

## Invert
Inverts the current selection.

Command: `sel -i`

## Deselect
Deselects (unselects) the all selected atoms.

Command: `sel -u` 

## Delete
Deletes all selected atoms. Same as pressing the 'Delete' key. Undo with `Ctrl`+`Z`.

Command: `kill sel` 

## Previous Selection
Re-select all atoms of the previous selection. 

Command: `selback` 

# Select Criteria 
To select all atoms for which Uiso is within user defined parameters. 

# Select Rings 
Select all rings of the specified type (for example) C6, C5N, C5, C5O within the structure. You can type your own ring criteria in the box. 
