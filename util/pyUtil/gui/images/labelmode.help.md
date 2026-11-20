# Experimental Labels

**Experimental.** Atom and bond labels that behave on screen like the rest of the
structure, and print in a real font in saved images.

In **Vector** mode Olex2 draws the labels with its vector font: they zoom with the
structure and keep the place you dragged them to. Olex2's own vector labels are thin,
so when an image is made (Bitmap Images, Ctrl+P) they are left out of the picture and
drawn again in a proper TrueType font, at the same place and size.

In vector mode the **Trim** of Bitmap Images works from the geometry instead of the
pixels: it takes in every drawn atom (grown copies too, hidden ones not), the atom
legend, the labels and the perspective, and it works on gradient and picture
backgrounds. In **Normal** mode everything is as Olex2 always did it.

The rows below: label mode, vector font sizes, printed size and calibration,
perspective. Each has its own help.

## When something looks wrong

- The printed labels are **too big or too small**: press *Calibrate* once (labels
  shown), then adjust *Printed size*.
- The labels are **in the wrong place under perspective**: set the perspective in this
  panel, not with *gl.Perspective*; Olex2 cannot be asked for it.
- The image is **not trimmed**: the console shows one line per image, starting with
  *Trim:* -- how many atoms, the box of the atoms, the legend, the labels and the final
  box. A legend far from the structure makes the box big.

# Experimental Labels Mode

**Normal**: labels as Olex2 always drew them; images as before.

**Vector**: the label fonts become Olex2's vector font (*@12* for atoms, *@7* for bonds
by default, see *Vector size*). Labels zoom with the structure; images draw them in a
TrueType font.

Switching back to Normal brings back the fonts used before vector mode. If those were
lost (before 2026-11-14 the mode was not saved), the fonts of the scene in use are
taken, and failing that Olex2's default.

The Bitmap Images panel sets label fonts of its own when it is opened; in vector mode
the vector fonts are put back straight away.

The same from the console: `spy.gui.images.label_mode(normal)` or
*spy.gui.images.label_mode(vector)*.

# Experimental Labels Sizes

The size of the vector font for atom labels and for bond labels (*@12* is Olex2's
vector font at 12). The change is applied at once and kept. Atom labels at *@10* to
*@12* suit most pictures; the smaller sizes are for crowded structures.

The numbers are not point sizes: vector labels zoom with the structure, so how big
they come out in an image depends on the zoom and the image size.

Olex2 draws vector labels relative to the size of the whole scene: when the structure
is grown, the labels get bigger compared with the atoms. The printed labels follow
this once the labels have been calibrated (see *Printed size*).

# Experimental Labels Print

**Printed size**: the TrueType labels in the image against Olex2's printed vector
labels. 1.18 (the default) makes them about a fifth bigger; Olex2 prints its own vector
labels a little bigger than it shows them on screen. Tick *Compare* to see both and
judge the factor.

**Calibrate** measures how big Olex2 draws the labels and where they start: switch
to vector mode, show some labels, then press it. Olex2 renders the window once with
the labels in magenta, finds them in the picture and fits their size and offset.
Dragged labels need no calibration: how far a drag moves a label is taken from
Olex2's own code. The console reports how many labels it matched. Calibrate once
after this update: from then on the size is right for grown structures too.

After a calibration, try *Printed size* 1.0 first.

`spy.gui.images.label_calibrate()`

# Experimental Labels Both

**Compare** (off by default): images made in vector mode keep Olex2's own thin vector
labels under the printed TrueType ones. Use it to check the size and place of the
printed labels; leave it off for real pictures.

With it off, Olex2's labels are left out of the picture: their font is made tiny for
the moment of the picture and put back afterwards, so dragged labels stay where they
are.

# Experimental Labels Perspective

The perspective angle of the 3D view (off, or 10 to 60 degrees).

Olex2 cannot be asked whether perspective is on, so the trim and the printed labels
only know the perspective set here (or with *spy.gui.images.perspective(30)*). A
perspective set with *gl.Perspective* in the console is not seen. It is not kept over
a restart, as in Olex2 itself.

`spy.gui.images.perspective(off)`
