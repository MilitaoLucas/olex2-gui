# NoSpherA2

When ticked, **non-spherical form factors**  will be used in the refinement of the structure.

n^<font color='red'>**This is a new and highly experimental procedure, which requires intensive computing ressources. We do not accept any liability for the correctess of the results at this point. They must not be publsihed until further testing is done!**</font>^n

<br>
<br>

There are three steps to this procedure:

* The molecular wavefunction is obtained for your input model using Quantum Mechanical calculations using either TONTO (shipped) or ORCA (Versions 4.1.0 and up). Untested interfaces for Gaussian of various versions are present but not maintained. Other programs will be supported in the future.
<br>
* The atomic non-spherical form factors are extracted from the molecular wavefunction by Hirshfeld partitioning of the atoms in the molecule.
<br>
* olex2.refine now uses these non-spherical form factors for the next refinement cycles. All normal commands for your refinement can be used, including restraints and contraints.
<br>
At this point, a new model will be obtained, and this **will** require the re-calculation of the molecular wavefunction -- and the above three steps need to be repeated until there is no more change and the model is completely settled.

### Update Table
After ticking the 'NoSpherA2' box, the option **Update Table** will appear. The default method to calculate the wavefunction is **TONTO** and other programs (currently only **ORCA** and **Gaussian** [HIGHLY UNTESTED]) will appear if these are properly installed and Olex2 knows about them --> Settings). Once a program has been chosen, please also adjust the Extras according to your needs.


# NoSpherA2 Extras
This tool provides all the settings required for the calculation of the molecular wavefunction.

## Basis
This specifies the basis set for the calculation of the theoretical density and wavefunction. The default basis set is **def2-SVP**. **STO-3G** is recommended only for test purposes.
The **def2**- and **cc-** series of basis sets is only defined for atoms up to Kr. Afterword ECPs woudl be needed to use these basis sets, whcih are by the natrue of the method not compatible. 
Then the **x2c**-basis sets are usefull, as they are defined up to Rn without any ECPs.
It is **highly** recommended to run basic first iterations using single valence basis sets and finish the structure with a higher basis.
If you really do not plan on using your computer you can use TZVPP, but these calculations will take extremely long and are more for benchmark and polishing.

## Method
The default method used for the calculation of the theoretical MOs/Density is **Hartee-Fock**. **B3LYP** may be superior in some cases (especially for the treatment of hydrogen  atoms), but tends to be unstable inside Tonto in some cases. Both can be sued in ORCA.

## CPU
The number of CPUs to use during the waverfunction calculation. It is usually a good idea to *not* use *all* of them -- unless you don't want to use the computer for anything else while it runs NoSpherA2! Olex2 will be locked during the calculation to prevent inconsitencies of files.

## Memory
The maximum memory that NoSpherA2 is allowed to use. This must not exceed the capabilities of the computer. If ORCA is used the memory needs per core are calcualted automatically, this input is the **total** memory.

## Charge
The charge of the molecule used for the wavefunction calculation. This **must** be properly assigned.

## Multiplicity
The multiplicity (2S+1) of the wavefunction, where S is the total spin angular momentum of the configuration. E.g. a closed shell wavefunction in it's ground-state usually has multiplicity 1, one unpaired electron has multiplicity 2. Must be positive above 0.

## H Aniso
Refine hydrogen atoms anisotrpically. Make sure they are not restricted by AFIX commands to obtain reasonable results.

## Use Relativistics
Use DKH2 relativistic Hamiltonian. This should only be used with x2c-family basis sets. But for them it is highly recommended.

## Keep Wavefunction
Select to keep a copy of the current wavefunction in the folder you are working. Backups of former wavefunctions are kept inside the olex2 folder in that directory.

## HAR
Continue calculations until final convergence is achieved over a full cycle of WFN and Least Squares refinement. Criteria as per definiton of HAR in tonto. This will need much more time!

## Cluster Radius (For Tonto)
If Tonto is used for a wavefunction calculation a clsuter of **explicit charges** calcualted in a self consistent procedure is used to mimic the crystal field for the wavefunction calculation. This option defines the radius until no further charges are included.

## Complete Cluster (For Tonto)
In case of a molecular structure this switch will try to complete the molecules for the charges calcualtion bsaed on distances of atoms. If the refined structrue is a network compound where no molecular boundary can easily be found (e.g. there is no way to grow the structure without having dangling bonds) this procedure will fail in a sense, that the computer will run out of memory. Therefore this option is highly recommended for molecular crystals but crucial to be deactivated for network compounds.

## DIIS Conv. (For Tonto)
This option defines the convergence criterion the wavefunction calculation needs to achieve in order to be considered converged. A lower value will finish faster but drastically increases the chance for unreasonable wavefunctions, especially in complicated calculations.

## SCF Conv. Thresh. (For ORCA)
This option allows you to adjust the convergence criteria for your SCF in ORCA. NormalSCF for default calculations, Tight or very Tight for very precise high level calculations. Extreme is basically the numerical limit of the computer and strongly discouraged, as practically unreachable for big (>3 atoms) systems.

## SCF Conv. Strategy (For ORCA)
Selects which mechanism to use for the SCF to converge to the minmum. Refers to the stepsize in applying calculated gradients fo the wavefunction.

## Grouped Parts (For disordered structures)
Since there might be different regions in your molecules containing disorder modelling you need to specify which disorders form a group for the calculation of Wavefunctions. A Group in this sense refers to PARTs, that resemble the same functional space. E.g. a disorder of a sodium atom with other singly charged ions around this position form a group (Let's say PARTs 1, 2 and 3 are PARTs describing three possibilities of this disorder), where these different PARTs are not interacting within the same molecular input structure, while at a second position there is a carboxylate in a disordered state, where one of the PARTs interacts with this disordered ion (PART 4), while the second PART (Nr. 5 in this case) does not.<br>
Groups are given by syntax: 1-4,9,10;5-7;8 (Group1=[1,2,3,4,9,10] Group2=[5,6,7] Group3=[8])<br>
For the given example a reasonable grouping would be: 1-3;4,5 <br>
This would mean 1-3 are not to be interacting with each other, but each of them both with 4 and 5, respectively, leading to calcualtions:<br>
PART 1 & 4<br>
PART 1 & 5<br>
PART 2 & 4<br>
PART 2 & 5<br>
PART 3 & 4<br>
PART 3 & 5<br>
<br>
It is easily understandible that having interactions between PART 1 and 2 in this example would be highly unphysical, which is why definition of disorder groups is crucial for occurances of disorder at more than one position.<br>
<br>
<font color='red'>**IMPORTANT: Superposition of two atoms with partial occupation freely refined without assignment to PARTs will lead to SEVERE problems during the wavefunction calcualtion, as there will be two atoms at 0 separation. Most likeley the SCF code will give up, but will NEVER give reasonable results!**</font>


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
This specifies the basis set for the calculation of the theoretical density and wavefunction. The default basis set is **def2-SVP**. **STO-3G** is recommended only for test purposes. x2c-family of basis sets is available up to Rn, the others only to Kr.

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