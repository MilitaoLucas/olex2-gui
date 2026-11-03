# Rotate
Using these tools, a structure on the screen can be rotated in a more fine-grained and repeatable way than with the mouse.

## Rotate about the *x*, *y*, or *z* axis
Enter the degrees of rotation into a **Rotate** box and click on one of the buttons on either side of the box to rotate the structure once in the negative or positive direction. Selecting *x* rotates the structure from bottom to top on the screen, *y* rotates from left to right and *z* rotates within the plane of the screen. 
<br>
<br>

Using the '<c>rota</c>' line command, even finer rotations by fractions of degrees are possible. Use '1' to stand for *x*, '2' for *y*, and '3' for *z* in the '<c>rota</c>' command, e.g.,

| `rota  1  13.4` | Rotate the structure around the *x* axis by 13.4&deg;. |

| `rota  2  -10.2` | Rotate the structure around the *y* axis by -10.2&deg;. |


# Animate
## Auto Rotation
Ticking a box in this tool tab continuously rotates the structure on the screen about the specified axis. A structure can be rotated simultaneously about more than one axis, and the speed of rotation can be set using the slider bar.
<br>
<br>

Clicking on *a*, *b*, or *c* resets the view to look down the chosen axis.


# Zoom
This slider enables zooming in or out on the structure displayed on the screen. The zoom can also be adjusted by holding down the right mouse button and moving the mouse. Click the **Reset** link or type '<c>gl.zoom</c>' at the command prompt to return to a normal zoom level.
