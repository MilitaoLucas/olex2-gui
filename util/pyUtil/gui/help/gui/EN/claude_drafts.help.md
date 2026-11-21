[comment]: < Help for 'i' buttons that had none (help_index.py --check), written by Claude from the GUI files and the code they call, 2026-11-20. Every entry is a draft: review it, then move it into the topic file and remove the draft line. >

# Olex2 Constraints Restraints
*Draft by Claude, written from the code - not yet reviewed.*

Restraints that Olex2 itself provides on top of the SHELX ones. Choose one from the **Olex2 Name** box (**RRINGS** or **TRIA**): Olex2 builds the restraint for the current selection and shows its settings in the rows below.

## RRINGS
Restrains the rings of the selection to be regular: equal 1,2 and 1,3 distances in each ring.

## TRIA
Restrains a three-atom group by its two distances and the angle between them.


# Anomalous Dispersion
*Draft by Claude, written from the code - not yet reviewed.*

Choose an element in the box, then:

## &mu; Plot
Plots the absorption coefficient &mu; of that element against the X-ray wavelength.

## Anomalous Dispersion Plot
Plots the anomalous scattering terms f' and f'' of that element against the wavelength, so you can see how close your radiation is to an absorption edge.


# Disp2
*Draft by Claude, written from the code - not yet reviewed.*

The table of the anomalous dispersion values (f', f'') used for the elements of the current structure at the current wavelength. The link below the table is the paper the values and the refinement of these terms are based on.


# Peanut
*Draft by Claude, written from the code - not yet reviewed.*

Draws the mean-square displacement surfaces of the atoms ("peanuts") instead of ellipsoids. They show the displacement in each direction directly and make non-positive-definite or anharmonic displacements easy to see.

## Type
**rmsd** draws the root-mean-square displacement, **msd** the mean-square displacement.

## Quality
Smoothness of the drawn surfaces (1 to 7); higher is smoother and slower.

## Scale
Enlarges the surfaces by this factor.

## Show Peanuts / Hide Peanuts
Shows the surfaces (atoms are shrunk and bonds made thin while they are shown) or removes them and restores the previous atom and bond sizes.

## Show Diff / Hide Diff
Compares the displacements of the current model with those of another CIF (a file dialog asks for it) and shows the difference.


# CCDC Deposition Options
*Draft by Claude, written from the code - not yet reviewed.*

How the structure is sent to the CCDC: **Request CSD Number** deposits it and returns a CSD number for a publication; **Publish as CSD Communications** publishes the structure directly in the CSD without a journal article. The text box takes a note for the CCDC staff. **OK** sends the deposition.


# Fourier Maps
*Draft by Claude, written from the code - not yet reviewed.*

Electron density maps calculated from the current model and reflection data (observed, difference and other map types), with their display options. The map is drawn in the structure view; see the rows below for the map type, resolution and how it is drawn.


# Multiple Structure CIF
*Draft by Claude, written from the code - not yet reviewed.*

The current CIF contains several datasets (data blocks). Each one is shown as a button; click one to make it the current structure. The highlighted button is the dataset shown now.


# GUI Side
*Draft by Claude, written from the code - not yet reviewed.*

Moves the Olex2 panel to the other side of the window (left or right of the structure view).


# GUI Icons
*Draft by Claude, written from the code - not yet reviewed.*

The icon set of the panel buttons: **Classic** (the original Olex2 icons) or **Flat** (plain icons drawn in the colours of the current theme). **Designer...** (only when the theme designer is installed) opens the theme designer.


# GUI File Type Mark
*Draft by Claude, written from the code - not yet reviewed.*

How the structure title bar shows which kind of file is open (e.g. ins/res or cif): **Stripes** draws a striped band in the title, **Colour** colours the whole title as before.


# Auto Save View
*Draft by Claude, written from the code - not yet reviewed.*

## Save View
When ticked, the current view (orientation and zoom) is saved when you leave a structure and restored the next time it is opened.

## Load last
When ticked, Olex2 opens the structure you had open last when it starts.


# Modules Update Notification
*Draft by Claude, written from the code - not yet reviewed.*

When ticked, Olex2 shows a dialogue when updates for installed extension modules are available. Untick it to update modules only by hand.


# WSL Mode
*Draft by Claude, written from the code - not yet reviewed.*

Windows only: runs external programs that need Linux (e.g. some quantum-chemistry back ends) through the Windows Subsystem for Linux and a Conda environment. Olex2 must be restarted for the change to take effect.


# Z
*Draft by Claude, written from the code - not yet reviewed.*

**Z** is the number of formula units in the unit cell and **Z'** the number in the asymmetric unit. Both can be typed in; Z' also accepts a fraction such as 1/2. **Atomic Vol.** is the volume per non-hydrogen atom of the current model, a quick check of whether the formula and Z fit the cell (about 18 &Aring;&sup3; per atom is typical for organic structures).


# FixFree
*Draft by Claude, written from the code - not yet reviewed.*

Quick changes to what is refined. Each link first clears the selection.

| **Fix all** | Fixes coordinates, ADPs and occupancies of all atoms (`fix xyz,adp,occu`). If occupancies are linked to free variables, Olex2 asks whether to clear those links. |

| **AFIX** | Deletes all hydrogen atoms and adds them again geometrically (`kill $H` then `HAdd`). |

| **Free XYZ** | Frees all coordinates (`free xyz`). |

| **Free ADP** | Frees the ADPs of all non-hydrogen atoms. |

| **Clear HFIX** | Removes the AFIX constraints of all hydrogen atoms (`afix 0`). |

| **Free H ADP** | Frees the Uiso of all hydrogen atoms. |


# Modelling and Disorder Tools
*Draft by Claude, written from the code - not yet reviewed.*

Tools for modelling disorder: linking PARTs and occupancies, fitting and splitting groups, free variables, and the symmetry disorder display. Each row has its own help.


# Auto Settings
*Draft by Claude, written from the code - not yet reviewed.*

Settings of the automatic solution/refinement procedure. There are no settings yet.


# Refinement List
*Draft by Claude, written from the code - not yet reviewed.*

## List
The LIST instruction: what the refinement writes to the .fcf file. **None** removes the instruction; **3**, **4** and **6** write the corresponding SHELX LIST format (for ED refinements only LIST 4); **Other** leaves an instruction that was set by hand.

## Threads
How many processor threads the refinement uses.


# Space Group Determination
*Draft by Claude, written from the code - not yet reviewed.*

The space group of the current structure. Pick a different one from the list to reset the structure to that space group (with the formula above). **Find with... Olex2** runs Olex2's own space group determination and fills the list with its suggestions; **ZSGH** (when installed) uses ZSGH instead.


# OpenBlas
*Draft by Claude, written from the code - not yet reviewed.*

The number of threads the OpenBlas linear algebra library uses in olex2.refine. A restart of Olex2 is required, and the setting has no effect when the environment variable OPENBLAS_NUM_THREADS is set. **Use Hyperthr.** counts hyperthreading cores as well.


# R Free
*Draft by Claude, written from the code - not yet reviewed.*

Keeps a set of reflections out of the refinement to calculate R<sub>free</sub>, an unbiased check of the model.

## R<sub>free</sub> set
When ticked, a test set is excluded from the refinement.

## Fraction
The fraction of reflections in the test set.

## R<sub>free</sub> shells
Takes the test set in resolution shells rather than at random (the number of shells).


# ML Options
*Draft by Claude, written from the code - not yet reviewed.*

Only for the maximum-likelihood refinement methods (MLF, MLI).

## ML - free set
The fraction of reflections kept out to estimate the likelihood parameters.

## ML - refl/bin
The number of free reflections per resolution bin used for these estimates.


# Terminate ED
*Draft by Claude, written from the code - not yet reviewed.*

Further settings of olex2.refine.

## CH<sub>2</sub>
How the H-C-H angle of CH<sub>2</sub> groups is treated: idealised, refined, or as SHELXL does it.

## SUMP
Whether SUMP conditions are applied as exact constraints or as restraints.

## Weighting Scheme
The weighting scheme of the refinement: the default, SHELX, new SHELX, unit weights, 1/&sigma;&sup2; or one depending on sin&theta;/&lambda;.

## Resonant form factor table
The table of anomalous scattering factors f', f'' (Henke, Sasaki or Brennan; **Auto** chooses). Changing it recalculates the DISP values.

## Break ED refinement ASAP
For electron diffraction refinements: stops a running dynamical refinement as soon as possible.


# Extract
*Draft by Claude, written from the code - not yet reviewed.*

Only for CIF files. If the CIF contains the reflection data (and usually the res file), the links extract them into .hkl and .res files, so that the structure can be refined again; one link also opens the folder, another opens the extracted structure. Otherwise it says that the hkl file exists already or that no hkl data are embedded.


# ED
*Draft by Claude, written from the code - not yet reviewed.*

Electron scattering factors for electron diffraction data.

## ED SFAC
The table of electron scattering factors (Peng 1999, UCLA 2022 or CAP 2022, all as four-Gaussian fits).

## Update SFAC
Writes the SFAC instructions for the elements of the structure from the chosen table.


# Modulation
*Draft by Claude, written from the code - not yet reviewed.*

Incommensurately modulated structures ((3+1)D). Shown only when the reflection data are an .hklm file. The structure in the view is the average structure; here you set the modulation vector **q**, choose the superspace group from a ranked list of candidates, refine the modulation waves, and animate the modulated structure or write a movie of it.


# CIF Part HTAB
*Draft by Claude, written from the code - not yet reviewed.*

Hydrogen bonds for the CIF. **Max D-A** is the longest donor-acceptor distance and **Min D-H-A angle** the smallest angle accepted. **HTAB** replaces all HTAB instructions with the hydrogen bonds found with these limits, so that the next refinement lists them in the CIF; tick **Display** to show them in the structure view.


# Rigaku XPlain
*Draft by Claude, written from the code - not yet reviewed.*

Runs Rigaku's XPlain program for the space group determination of the current data. After a run, the second link opens its output in the text editor.


# BreakOnConvergency
*Draft by Claude, written from the code - not yet reviewed.*

SHELXL only: when ticked, the refinement stops as soon as the largest shift/esd drops below the value given, instead of always running all cycles.


# SFEXECUTION
*Draft by Claude, written from the code - not yet reviewed.*

How Superflip (charge flipping) runs.

## Repeat mode
Whether Superflip starts again with new random phases: **never**, if it did not converge (**nosuccess**), **always**, or a given number of **trials** (the number in the box).

## Max cycles
The largest number of charge-flipping cycles per run.

## Fast FFT
Uses a faster Fourier transform (when the grid allows it).


# SFDATA
*Draft by Claude, written from the code - not yet reviewed.*

How Superflip treats the reflection data.

## Normalise
Normalises the structure factors: **no**, by a **wilson** plot, or **local**ly in resolution shells.

## Number of resolution shells
The shells used for the local normalisation.

## Weak ratio
The fraction of reflections treated as weak (their phases are shifted rather than flipped).

## Limit resolution
Uses only the data up to the given resolution.


# SFMISSINGDATA
*Draft by Claude, written from the code - not yet reviewed.*

How Superflip treats reflections that were not measured.

## Method
**float**: their amplitudes float freely; **bound** / **boundsum**: they float, limited by an upper bound.

## Resolution limit
Missing reflections are added up to this resolution.

## Upper bound
The upper bound for their amplitudes.


# SFCONVERGENCE
*Draft by Claude, written from the code - not yet reviewed.*

When Superflip counts a run as converged.

## Value
The quantity watched: **normal**, the R value, the charge, or the peakiness of the density.

## Threshold value
The value of that quantity that counts as converged.

## Delta / Delta value
The threshold below which density is flipped: chosen automatically, or the value given.


# SFOUTPUT
*Draft by Claude, written from the code - not yet reviewed.*

What Superflip does with its result.

## Derive symmetry
Derives the space group from the density: **yes**, **no**, or **use** it for the result.

## Search symmetry
How symmetry is searched in the density: **no**, by an origin **shift**, or by **average**-ing symmetry-related density.

## Cleanup
Deletes Superflip's temporary files afterwards.

## Use current cell centering
Passes the centring of the current cell to Superflip.


# TONTO
*Draft by Claude, written from the code - not yet reviewed.*

Settings of the Tonto program for refinements with non-spherical (Hirshfeld) scattering factors: the **Basis** set and the quantum-chemical **Method** (restricted Hartree-Fock or Kohn-Sham), the **Thermal smearing model** and the **Partition model** of the electron density.


# ZSGH
*Draft by Claude, written from the code - not yet reviewed.*

Runs ZSGH for the space group determination of the current data (shown only when ZSGH is installed).


# Solvent Masking info
*Draft by Claude, written from the code - not yet reviewed.*

The voids found by the solvent mask. Each row is one void: its number, volume V (&Aring;&sup3;), the number of electrons e<sup>-</sup> found in it, the ratios V/e<sup>-</sup> and the volume per atom, the suggested content (based on the setting shown in the header) with its electron count, and the multiplicity m.
