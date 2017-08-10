# Refinement Program
Apart from its own refinement engine (olex2.refine), Olex2 also supports all variants of ShelXL. Depending on the refinement package, different refinement methods are available.

## olex2.refine
Our own refinement engine. It supports all ShelXL instructions, plus a number of new restraints and constraints that are not available from ShelXL. You can switch between this engine and ShelXL, and Olex2 will not 'forget' the special instructions that are available only in olex2.refine, but of course ShelXL won't heed them.

## ShelXL-20XX
Since 2012, modern versions of ShelXL have been released by George Sheldrick. Please make sure that you check regularly whether you have the latest version of the ShelX programs installed -- these are the **only versions** that should be used. In fact, you can use any version you wish, as long as it is on the path and is called 'shelxl'. Our recommendation is to make yourself a folder on the root of one of your drives called 'CrystallographyPrograms' and then put that folder 'on the PATH'. Any (known) executable you place in that folder will be recognised by Olex2 and you will be able to use it from within Olex2

# Set Reflection File
The reflection file contains all the data that were collected during the x-ray diffraction experiment in a condensed form.

## hkl
The standard format for a reflection file is the 'hkl' file. From this drop-down menu, you can choose which file you want to refine your model against. There is no need to rename anything - just choose the file and then press refine.

# Refinement Max Cycles
Some refinement programs (e.g. SHELXL) will continue refining up to a maximum number of cycles. Here you can set this number. olex.refine will go up to the maximum number, but might stop beforehand if the refinement is settled.

## From the Command Line
You can simply type, for example:`refine 4 5` meaning that 4 cycles of refinement will be carried out and that you will be shown 5 residual electron density peaks once the refinement has finished. The values will be remembered for future refinements.

# Weighting Scheme
A weighting scheme should be applied to your data. This is usually done when your model is finished. All refinement programs will suggest a suitable weighting scheme. By clicking on the coloured line you will apply these suggestions. By ticking the box, Olex2 will automatically update to the suggested values after each cycle.

Command: `weight`

# Extinction Correction
Extinction affects the intensity of reflections and can result in systematically absent reflections being observed under special conditions. This parameter is designed to account for the intensity changes associated with extinction, the method used is a compromise to cover primary and secondary extinction. In general this should not be included until all of the non-hydrogen atoms have been located.

# Refinement Masks
In some structures, solvent disorder can be so severe that modelling this disorder using atomic sites (i.e. partially occupied atoms) is neither possible nor sensible. In these cases, it is better to not even attempt to model the 'affected area' - but to simply leave the measured electron density in place. This technique requires the calculation of the area that should be 'taken out of the refinement' - and defining *that* depends on the current structure.

## Defining the volume to be masked

### Use solvent mask
Include in the refinement a solvent contribution to the structure factors as the discrete Fourier transform of the electron density in the solvent area. The solvent mask can be calculated and displayed under Tools > Maps > Masks. When used with smtbx-refine, the solvent contribution is added internally to that calculated from the ordered part, whilst with SHELXL the solvent contribution is subtracted from the observed data before passing a modified hkl file to the external refinement program.

### Recompute mask before refinement
When ticked, the solvent mask will be recomputed before the start of the refinement. This can lead to an improved solvent mask, particularly if the ordered part of the structure was poorly converged before the initial mask search.

# Refinement Settings Extra
XXX
