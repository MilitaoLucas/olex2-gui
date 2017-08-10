# Naming 
This GUI can be used for naming atoms in a molecule. However, in some cases it might be better to use the command line to name atoms more efficiently.

## Using The GUI
After pressing the 'GO' button, you will be in a mode. That means, that something will happen to all subsequently clicked atoms. In this case:

### Start
The clicked atom will be named with the Current atom type (unless 'Type' is set to something else) and numbered starting from the number that is entered in this box.

### Suffix
A suffix will be given to the atom, with all other settings in place.

### Type
The atom type of the atom will be changed as well as all other settings will be applied.
**Note**: When you are in a mode, the mouse pointer changes. In some modes it simply becomes a hand-symbol, but in other cases the pointer will tell you what will happen if you click on an atom.

## Using the Command Line

Command: `name sel type` - Will change all currently selected atoms into the new type.

Command: `name sel integer` - Will renumber all currently selected atoms in the order of which they were selected starting from.

# Automatic Hydrogen Naming 
Olex2 will keep track of the naming of hydrogen atoms automatically. This feature can be switched off by unticking the 'Automatic Hydrogen Naming' box. 

# Match Naming 

If you have a structure with two or more matching moieties, you only need to name one of these. Olex2 will then match this naming scheme to the other molecule.This is important in structures with Z' larger than 1 and also in structures where a metal is coordinated to more than one ligand of the same type. In this case you will need to set the maximum number of bonds for the central metal ion to 0 (right-click, then Bonds).
Select **any one atom** of the correctly named molecule, and then select **any one atom** of the *other* molecule.

## Add a suffix
Enter a suffix character into the box, then click the link.This will transfer the naming scheme of the first molecule to the second molecule with the suffix letter you have chosen.

Command: `match sel -n=suffix`

## Replace a suffix
Instead of merely adding a suffix, you can also replace the first character of the original naming scheme with another character. This is useful, for example, if you wish to name all atoms in one ligand like C101, C102, C102 ... and corresponding atoms in the other ligand like C201, C202, C203 ...

Command: `suffix'>match sel -n=$suffix`

## Replace last character
Equally, the last character of an atom name can be replaced:

Command: `suffix'>match sel -n=-suffix`

There is no GUI for these replacements, you will have to type the lines above from the command line. 
