# Images
Olex2 can export images of a structure in a variety of formats, with many options available in this tool tab. Atoms are also labelled using the tools here.

## File name and format
Enter a name for the image file here or use the default file name provided. Options for dealing with duplicate picture file names are specified here as well. The **Default** file format for saved images is **bitmap**, but other formats may be selected from this drop-down menu.

## Atomic Labels
This attaches customisable labels to individual atoms in the structure. These labels are distinct from the ordinary names given to atoms during refinement or defined with the **Naming** tool tab under **Refine**. The **selected** button only labels those atoms highlighted in the graphics window, **non-H** labels all non-hydrogen atoms, and **hetero** labels all atoms other than carbon and hydrogen. To label *all* atoms, type '<c>sel atoms</c>' at the command line to select all atoms and click the **selected** button.

## Symmetry label and Style
The **Symmetry label** drop-down menu offers several options for attaching a descriptive suffix to the labels of atoms related by symmetry to those in the asymmetric unit. The **Style** drop-down menu allows the user to select from a couple of different options for formatting that portion of the atomic label which follows the element symbol.

## Moving and Deleting Labels
Hold down the '<c>Shift</c>' key and drag a label with the left mouse button to move it. To delete a label, first make sure no atoms, bonds, etc. are highlighted (hit ''<c>Esc<c>' to deselect all). Left-click the label(s) to be deleted and hit the '<c>Delete</c>' key. To select all labels, click on any one label and then press '<c>CTRL+A</c>'. To delete all atomic labels, click the **DELETE all labels** link.

## Label Colour and Label Box
To alter the colour and appearance of atomic labels, click the **Choose the label colour** link to open a menu for customising a label's colour properties. Click the **Label Box** link to customise the properties of the bounding box enclosing each atomic label.


[comment]: < The help text given below for "Align and Lock" is the same as in quick_drawing_styles.md. >


## Align and Lock
### View and Plane
Clicking on one of these links will orient and centre the structure within the display window, which can be useful before creating images. **View** centres and orients a structure on the screen using an algorithm involving the calculation of the structure's principal axes of inertia. **Plane** calculates a mean plane through the entire structure, orients the structure on the screen perpendicular to this plane, and centres the structure on the screen. Neither of these methods changes the zoom level. Typing '<c>mpln -r<c>' displays the mean plane and prints its equation in the output window. To delete the plane, click on it and press '<c>Delete</c>'.
<br>
<br>

A couple of other helpful line commands for realigning the structure on the screen are:

| `center` | Centres the structure without changing orientation or zoom level |

| `compaq -a` | Also centres the structure without changing orientation but does resize the structure to fit within the display area. |

Note: The atom legend can be moved to any desired location on the screen, e.g., closer to the structure, by holding down the '<c>Shift</c>' key and dragging it with the mouse. The legend display can also be switched off or on with the '<c>legend</c>' line command. To reset the legend (e.g., if it has disappeared), type '<c>legend -r</c>'.

### Lock
When working with images, it is sometimes helpful to lock out certain mouse functions to avoid accidentally changing the orientation or zoom. The zoom, rotation, and translation functions may be individually locked by ticking the appropriate box. For example, if only the **Translation** box is ticked, the structure will remain in a fixed location on the screen, but it will still be possible to rotate it or to zoom in and out. All three functions may be locked simultaneously by ticking the **Lock all** box. 


# Bitmap Images
Olex2 can produce bitmap images of structures in a variety of formats, with no limit on the image file size. All images produced are in the RGB colour space. If CMYK images are required, e.g., for publication, a separate RGB-to-CMYK conversion tool will be needed. Many such image conversion tools are available on the internet, where an uploaded RGB file is received back as a CMYK file.


# Bitmap Image Attributes
## File Format
Select a format, such as .png or .jpg, for the image file from this drop-down menu. The default format is .png (recommended), which involves lossless compression of images and results in relatively small files.

## Transparency
It is possible to set the background for the structure to be transparent, but this will cause purely white parts of the structure also to become transparent. To work around this, set the background of the image to some colour that does not occur in the structure (pink is usually a good choice). Then, convert all pixels of that colour to a transparent background using PowerPoint or other graphics software. There are many ways to achieve a transparent background using professional image processing software.

## Make Image
Click the **Go!** button to save an image of the structure in the current working folder. The image will not contain any displayed text besides atomic labels and the legend. However, the current background will be part of the image. To change to a plain white background, press '<c>F2</c>' once or twice.


# Bitmap Image Attributes1
## Resolution
Set the image resolution in DPI from the drop-down menu or type in a custom value.

## Width
Set the image width in inches or centimetres from the drop-down value or enter a custom width into this box. The image width in pixels will be automatically adjusted, depending on the resolution selected.

## Size
Select a value from the **Size (px)** drop-down menu to specify the image width in pixels. The width of the image will automatically be adjusted depending on the resolution selected. It is also possible to type in a custom value into the **Size (px)** box. If the value is 100 or greater, it is interpreted as the width of the image in pixels; if it is less than 100, it is interpreted as a percentage of the display size. Thus, entering 1000 in the **Size (px)** box will generate an image 1000 pixels wide, but entering 85 will generate an image with a size 0.85 times the display area. There is no limit on the size of the bitmap file created.

| `pict molecule.png 300` | Creates a PNG image file called **molecule.png** in the working folder with a width of 300 pixels. |


# Bitmap Image Trim
## Trim
Ticking this box adds the specified padding and border to the image. Custom values can be entered in all the drop-down menus described below.

### Padding
Adds a white padding around the image of the specified percent thickness.

### Border
Adds to the image a border of the thickness specified in the **Border (%)** drop-down menu and of the colour specified by the hexadecimal code in the **Colour** dropdown menu. The color corresponding to the hexadecimal code is displayed in the square box next to the **Colour** menu.


[comment]: < Help text for "Add Fog" is now taken from quick_drawing_styles.md. >


# Bitmap Atom Label Fonts
Note: This section pertains to user-defined atom labels created in the **Images** tool tab above, *not* to atom names generated during refinement or defined using the **Naming** tool tab under **Refine**.
<br>
<br>

Set the fonts for atom labels and bond labels here. Click the **Atom Label Font (Olex2)** link to change the settings of the default Olex2 font used for atom labels. To use a system-supplied font such as Courier or Arial for labels instead of the built-in Olex2 font, click the adjacent **(System Font)** link and select the desired font from the menu that appears. Similarly, click **Bond Label Font (Olex2)** to change the settings of the default Olex2 font used for bond labels, and on its adjacent **(System Font)** link to use a system-supplied fonts for bond labels.


# Postscript Images
Some would argue that there is no better way to represent a crystal structure on paper than a clear black-and-white ORTEP drawing. Such drawings can be made using Olex2. There are very many different options for generating ORTEP-style drawings. Many of these can be set from this GUI, but for more exotic options, please consult the Olex2 manual in the **Start** tool tab under **Home**.


# PS Row 1
Tick the **Coloured Atoms** and **Coloured Bonds** boxes to show atom outlines and bonds, respectively, in colour. If the **Filled Atoms** box is ticked, all coloured atoms will be drawn filled with their respective colours. Tick the **Pers** box for a perspective view of the structure.
<br>
<br>

Once all the PostScript graphics options are set, click the **Go!** button to create a .ps image file in the working folder.


# PS Row 2
Set the atom outline and octant line widths from these drop-down menus.


# PS Row 3
Specify the number of sections into which each octant face is to be divided and the width of the octant divider lines using the drop-down menus here.


# PS Row 4
Set the width of bonds to hydrogen atoms here as a fraction of the normal bond width. The width of all other bonds is controlled with the **Bond r** slider in the **Quick Drawing Styles** tool tab under **View**, or with the '<c>brad</c>' line command.


# PS Row 5
The thickness of the font and the font size used for atom and bond labels are set from these drop-down menus. A greater font thickness will make the font appear more bold.


# PS Row 6
Adjust the size of the bond font using this drop-down menu.


# PS Row 7
By default, hydrogen atoms placed in riding positions and displayed as uniform spheres will not have octants cut out. Carbon atoms will also not have octants cut out because of the **-$C** instruction included by default on this line. All other atoms will be displayed with cut-out octants by default. Select the **+$C** option from this drop-down menu to show carbons with octants cut out as well.


# Povray Images
It is possible to export a structure in the popular POVRAY format as a 3D object. POVRAY is capable of generating sophisticated images with rendered shadows and backgrounds, as well as 3D animations, but this requires in-depth knowledge of POVRAY techniques. There are no options here, as Olex2 merely creates a .pov image file for further elaboration with POVRAY tools.

| `pictPR filename.pov` | Saves the POVRAY output file 'filename.pov'. |


# PR row 1
Click the **Go!** button to create a POVRAY image in the current working folder.


# Image Series
Creates a series of bitmap images of the structure rotating about the *x*, *y*, or *z* axis.


# IS row 1
Click the **GO** button to create a series of still images of the rotating structure. The images, numbered 000, 001, 002, etc. will be stored in a folder called **movie** in the current working folder. The images can be concatenated in sequence to create an animation of the structure rotating.


# IS row 2
The **Rotation around Axis** box specifies the axis of rotation (**1** = *x*, **2** = *y*, and **3** = *z*). **Degree** specifies the number of degrees by which the structure is to be rotated before each subsequent image in the series is captured.


# IS row 3
**Number of Frames** specifies the number of still images to be captured, and **Size** determines the size of each image in the series.