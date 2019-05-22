# Hirshfeld Atom Refinement
 The <b>H</b>irshfeld <b>A</b>tom <b>R</b>efinement employs aspherical atomic scattering factors calculated from a theoretical density. This approach allows for an accurate localization of hydrogen atoms, an accurate determination of non-hydrogen ADPs and an anisotropic refinement of hydrogen atoms. It is being developed by Prof. Dylan Jayatilaka at the University of Western Australia in Perth in
 conjunction with Prof. Simon Grabowsky at the University of Bremen.

## Literature

* Jayatilaka & Dittrich., Acta Cryst. 2008, A64, 383
&nbsp; URL[http://scripts.iucr.org/cgi-bin/paper?s0108767308005709,PAPER]

* Capelli et al., IUCrJ. 2014, 1, 361
&nbsp; URL[http://journals.iucr.org/m/issues/2014/05/00/fc5002/index.html,PAPER]

* Fugel et al., IUCrJ. 2018, 5, 32
&nbsp; URL[http://journals.iucr.org/m/issues/2018/01/00/lc5093/lc5093.pdf,PAPER]

## Videos
From time to time we will make small videos, which will introduce HAR and explain the features. A slightly older overview video is available on our YouTube channel: URL[https://youtu.be/bjdSJWZa1gM,YOUTUBE]

# Basis Sets and Method

## Basis
This specifies the basis set for the calculation of the theoretical density and wavefunction. The default basis set is **def2-SVP**. **STO-3G** is recommended only for test purposes.

## Method
The default method used for the calculation of the theoretical density is **Restricted Hartee-Fock**. **Restricted Kohn-Sham** may be superior in some cases (especially for the treatment of hydrogen  atoms), but tends to be unstable in some cases.

# Hydrogen_Treatment

## Refine Hydrogen
This option specifies how hydrogen atoms are treated in HAR. Hydrogens can be refined anisotropically, isotropically, only positions, or kept fixed.

## Dispersion
Enable this feature if you want to treat dispersion in you structure. Be aware that this feature is still in progress, so errors might occur. If that is the case rerun without dispersion correction.

## Auto-Grow
This will try to grow your structure if your Z' is smaller than 1. If your structure has a non integer Z' please try to grow it using the Olex2 grow tools, which can be accessed from HAR Extra, as well.

## Initial IAM
Enable/Disable a final cycle of IAM refinement prior to the start of HARt. This is highly recommended, since you should only start into HARt with a converged geometry after normal IAM refinement. If this causes trouble or leads to wrong geometries you can disable it.

# Cluster Radius and Significance

## Cluster Radius
Defines a radius around the asymmetric unit, in which implicit point charges and dipoles are used to mimmic the crystal effect. Minimal HAR is 0, reasonable values go to 8 Angstrom.

## Complete Cluster
In a normal case like a molecular structure this will make sure the cluster charges which are generated resemble the full molecule and leveled charges. If you want to refine a network compound (like a salt or bridged ions) where molecular boundaries are difficult to detect you might encounter errors. If that is the case try to turn this off.

## F/sig threshold
Defines the significance criteria for data to be used in the refinement. Default value is 3, should not be too big.

# Running HAR Jobs
Launch HAR jobs as a separate process. Olex2 can be closed and the process will continue to run. Please note, that HAR jobs can take a **very** long time -- from a few **hours** to a few **weeks**!

HAR refinements are run as 'jobs': they are submitted to the system as an independent process. At the moment, Olex2 does not automatically monitor the progress of these jobs, but we provide a few tools here to help with this.


# List HAR Jobs

## Job Name
Once the job is finished, the name will be displayed as a link. Clicking on this link will open the finished HAR structure.

## Timestamp
The time when the job was submitted.

## Status
Olex2 tries to 'guess' the status of the job from the files it finds in the folder. This is a temporary measure.

## Error
If the HAR refinement produces an error file, a link to this file will appear.

## Input
If you want to compare input and output geometry click this button to open the input CIF file used for teh refinement.

## Analysis
This opens the result output file of the HAR refinement. If the plotly extension is installed, graphs of e.g. the QQ Plot, agreement statustics etc. contained in these files will be generated and shown in the browser.

# HAR Extras
These tools can be used to grow the structure before running the calculation or see maps after the refinement.

# HAR Maps
These options can be used to make basic maps to analyse the results.
For advanced Map options use the Maps Tool.

## Type
Select the Type of map you want to see: Residual density, Fcalc, Fobs or Defomartion Density (HAR-IAM)

## Isovalue
Select the isovalue for the selected map. Try different values to see different features fo your model and experiment. Also consider clicking nalysis-link after your HAR for statistics on your refinement.