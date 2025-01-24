# settings-target
The main settings for Olex2.


# Atom Settings
Some attributes of how atoms are displayed in Olex2 can be modified within a specific style.

## Atom Radius
This slider changes the radius of the selected atoms (in *Ball and Stick*, or '<c>pers</c>' mode). Clicking on **Set** will make this the default radius. The atom radius can be set manually with the '<c>arad</c>' and '<c>azoom</c>' line commands, as described below.

### arad
This parameter affects the radius of the selected atoms (or all atoms, if none are selected) in *Ball and Stick* ('<c>pers</c>') mode only. Typically, the radius in '<c>pers</c>' mode is taken from a definition file (and is different for different elements). **arad** overrides these settings. A typical value for H atoms would be:

| `arad 0.2` | Sets the radius of the selected atoms(s) to a value of 0.2. |

### azoom
This *zooms* the displayed atom sizes regardless of whether the atoms are shown in *Ball and Stick* ('<c>pers</c>') or *Ellipsoid* ('<c>telp</c>') modes. This value is given in percent, and scales the selected atoms.

| `azoom 120` | Scales the selected atom(s) to 120 percent of normal size. |

| `azoom 100` | Scales the selected atom(s) to normal size. |

In the '<c>azoom</c>' command, "100" shows the original atom size; larger/smaller values vary the display accordingly.

Note: This setting can play havoc with the ORTEP "50 percent probability' convention. In order to ensure that all atoms are shown with the standard probability, use:

| `telp 50` | Sets the ADP display to the 50 percent probability level. |

The size of the ellipsoids displayed in the screen can be modified by using a different probability level, e.g., to decrease the size slightly from the default value, use:

| `telp 30` | Sets the ADP display to the 30 percent probability level. |


# Bond Settings

## Bond Width
Change the radius of the selected bonds. Clicking on **Set** will make this the default radius. Please note that this will change the radius of *all bonds of the same type*.

| `individualise` | To set the radius of a single occurrence of a bond, select the bond and type this command first, then change the radius to the desired value. |

## Style
Choose an overall style setting for all atoms from the drop-down menu.

## Bond Colour
Choose the colour of the bonds here. The default is *elements*: half the bond will be the colour of one atom and the other half the colour of the other atom. Other options may be chosen from the drop-down menu.

# Background
A choice of different backgrounds is available for Olex2. Depending on the context, sometimes a dark background works better than a light one, and sometimes a graduated background is best. It is possible to switch quickly between them.

## Solid Colour/White
**F2** will toggle between the solid coloured background (as defined in the scene settings, accessed by right-clicking in the display area and selecting *Draw style*, then *Scene Properties...*) and thee solid white background.

## Graduated Background
**F4** toggles between the solid background and the graduated background.

| `grad` | Sets the colour of the four corners of the graduated background. Double click in each coloured box to set the color of each corner. |

Note: With **grad -p=filename.png** it is possible to set a background picture. This can be very useful, e.g., to compare two different views of a single structure or to compare two different structures side by side on the screen: 

1. First, create a picture of first view of the structure by typing **pict 3.png 3** in the console (use a larger/smaller number for a higher/lower resolution picture; type **help pict** for more information on the pict command). This will create a file called "3.png" in the current working folder. (To find this folder, type **user** at the console prompt.) 

2. Next, move/rotate the view of the structure, or open a new structure, then type **grad -p=3.png**. The first picture (3.png in this example) will be displayed as a static screen background to the currently active structure, which can still be moved or rotated as normal. 

3. To remove the picture from the background and return to the normal gradient background type **grad -p**.


# GUI Width
The width of the GUI (i.e., the panel containing all the Olex2 tool tabs and commands; see image below) can be adjusted to any desired value.

![0.6 The Olex2 GUI](images/gui.jpg)

<br>
<br>

Click one of the built-in links (**Default**, **Narrow**, or **Wide**), or enter an arbitrary value. The font size of the items on the GUI will adjust automatically.

## Value < 1
| `panel 0.33` | If the value entered in the box is less than 1, the GUI width will be set to that fraction of the total width. For example, entering **0.33** will divide the display so that the GUI takes up 1/3 of the width and the structure takes up 2/3. |

## Value > 100
| `panel 520` | If the value entered in the box is greater than 100, the absolute width of the GUI will be set to that value, in pixels. |


# Swap HTML Panel
Clicking this button switches the position of the GUI between the right and left sides of the Olex2 window.


# GUI Links
Set whether some of the links on the GUI are displayed as buttons or as hyperlinks.


# Tooltips
If selected, tooltips will be shown when hovering over items in the GUI.


# Legend
If this box is ticked, a pictogram of all current atom types appears in the main window. With the left mouse button and the SHIFT key pressed, this legend can be moved to any position.

| `legend` | Switch the legend display on or off. |

| `legend -r` | Resets the legend display. Very useful for making an inadvertently moved or deleted legend reappear at the top left of the structure display area. |


# Info Bar
| `showwindow info` | If selected, more information on a structure is shown in a narrow bar along the top of the display area. |


# Reset Alerts
All hidden alerts will be reset.


# Console Lines
In order to avoid too much clutter on the GUI, we have decided to provide the console output behind the molecule. Here the number of lines of output can be set to any convenient value. The commands:

| `lines 10` | Will set the console to only show 10 lines. A different number of lines can be chosen. |

| `lines -1` | Will show all lines of output in the display area. |


# Auto MORE
Keywords entered here control the output of refinement, e.g., **MORE -1** dictates the amount of refinement information to be written to the .lst output file; **CONF** generates a table of torsion angles; **BOND DOLLARH** produces bond length and bond angle information (including bonds to H atoms); and **ACTA** writes a CIF file to the current working folder.


# Save View
If checked, drawing settings such as styles and backgrounds will be saved with the structure. This is somewhat experimental; if things go wrong, it may be necessary to reload the chosen style for that particular structure.
<br>
<br>

When this box is **not** checked, then a structure will be loaded with the same style as the previous structure.


# Start Olex2 In
On startup, Olex2 will open the tab selected from this drop-down menu. This takes effect the next time Olex2 is restarted.


# Solo Mode
When opening a new tool, all other open tools will automatically be closed.


# Modules Update
If updates to extension modules are availabe, a pop-up box will appear whenever Olex2 is started. This can be switched off here.


# Unit Cell Style
The unit cell can be displayed in different ways. First, to make the cell visible:

| `cell` | Switches the unit cell display on. |

## Cylinder
The unit cell box will be made out of cylinders (i.e., 3D objects).

## Lines
The unit cell box will be composed of simple lines.

## Width
This sets the thickness of the cylinders or lines.

## Colour
Right-click on either the cylinders or lines, then choose **Draw Styles**. For the lines, there is only a single object to modify; for the cylinders, the little spheres in the corners as well as the cylinders themselves can be modified independently.


# User Database
Olex2 supports a database of people and their institutions. Set the location of this sqlite database here (a restart is required). The database can also be managed from here.


# Enable Network
If this box is not ticked, Olex2 will not communicate with the internet at all, except for checking for updates on startup.


# Debug Mode
This setting is for developers only. The switch is to be left *off* by ordinary users.


# PATH
Semicolon-separated strings entered in this box will be added to the **System Path** as new values *before* any existing folders. This means that any crystallographic software in the folders listed here will be found by Olex2 *first* and therefore will be used.


# OpenMP
This tool allows for multiprocessing during refinement with olex2.refine using the OpenMP API.

Note: This feature is still under development and may be unstable.
