# Experimental Growing

**Experimental.** Repeat the picture of a saved model on the structure you have open:
the same grown atoms with the same symmetry operators, the same hidden atoms, the same
view, and optionally the drawing style, the planes and the lines.

Typical use: you have grown and arranged a structure by hand and saved it with
*save model Frag1b* (a file *Frag1b.oxm* next to the structure). After the next
refinement, or for another data set of the same compound in the same cell, choose
*Frag1b.oxm* here and press *Go!* -- the picture comes back in one step.

**Atoms are matched by position, not by name.** An atom here is the sample's atom when
it sits on the same place or on a symmetry equivalent of it (all operators of the space
group, lattice translations included), within a margin, and is of the same element. So
the labels may differ between the two models. An atom that this model holds at another
equivalent position is moved there first, so that growing gives the same picture.

If atoms have other names here than in the saved model, Olex2 lists them and asks
whether to use the names from the oxm file (see *Other names*).

The same from the console: *spy.from_oxm(Frag1b)*, *spy.from_oxm(Frag1b,grow,view)*,
*spy.from_oxm(Frag1b,names)*.

## Not possible yet

- **Label positions**: Olex2 has no command to put a label where it was dragged.
  *load model* restores them, but only on the very file that was saved.
- **Plane names** are kept under a code of their atoms; they come back only when every
  plane in the file has a name.

# Experimental Growing Sample

The saved model (*.oxm*) to take the picture from. Save one with *save model name*
in the console (it goes next to the structure), or use the model saved next to every
bitmap image (an image *x.png* has *x.oxm* beside it).

The cell should be the same as this model's (a warning is printed when it differs by
more than 2 % or 1 degree); the space group is taken from the saved model.

# Experimental Growing What

What to take from the saved model:

- **all**: everything below.
- **grow**: back to the asymmetric unit (*fuse*), then the same atoms with the same
  symmetry operators; atoms hidden in the sample are hidden here too (where an atom
  has only one copy). Q-peaks are left out: they belong to one refinement.
- **view**: orientation, centre and zoom.
- **styles**: the colours saved with the model -- atoms, bonds, planes and lines -- set
  on the same objects here. The style is not reloaded, so ellipsoids, sizes and
  everything else stay as they are; the console, background, legend and other parts of
  the scene keep the theme's colours. A line or plane whose kind of drawing is new here
  (e.g. a line with balls) gets its colours, but its shape only from a style that
  already has it.
- **planes**: the planes (*mpln*) on the same atoms, defined before growing, so every
  grown copy gets its plane.
- **lines**: the lines (*line*) with their names; a line end that sat on an atom sits on
  the same atom (and symmetry copy) of this model, other ends stay where they were.

**Go!** takes them.

# Experimental Growing Style

**Colours**: whose colours the atoms, bonds, planes and lines get.

- **oxm**: the colours saved with the model, set on the same objects here (with *Take*
  all or styles).
- **current**: the colours of the style in use stay; nothing is taken from the oxm,
  even with *Take* all.

Either way the style is not reloaded: ellipsoids, sizes and the scene (console,
background, legend) stay as they are.

On the console: *spy.from_oxm(Frag1b,keepstyle)*.

# Experimental Growing Names

**Other names**: what happens when atoms have other names here than in the saved model.

- **ask**: Olex2 lists them (*C1 -> C00B, ...*) and asks whether to use the names from
  the oxm file.
- **names**: take the names from the oxm file without asking.
- **keepnames**: keep this model's names; the console lists the differences.

Renaming goes through temporary names, so names that are swapped between atoms do not
get in each other's way; hydrogen atoms are named last.

**Names only** gives the atoms the names they have in the saved model and does nothing
else -- useful on its own to bring a new refinement into line with an earlier one.

**margin**: how far (Angstrom) an atom may be from the sample's position to count as
the same atom. 0.5 suits two refinements of the same data; take less when atoms of the
same element are close together, more for a different data set at another
temperature.
