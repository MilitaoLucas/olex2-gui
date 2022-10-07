# NoSpherA2
<font color='red'>**This is a new and highly experimental procedure in Olex2, requiring considerable computing resources. During testing, the ORCA and Tonto software packages were used for the calculation of non-spherical atomic form factors.**</font>
<br>
<br>

The acronym NoSpherA2 stands for Non-Spherical Atoms in Olex2. When this box is ticked, **non-spherical atomic form factors** (stored in a **.tsc** file) will be used during refinement. It is more sophisticated than the spherical independent atom model used in ordinary refinement, leading to significantly more accurate crystal structures, especially hydrogen atom positions. See **Literature** section below for more information and computational details.

## Literature
* Jayatilaka & Dittrich, Acta Cryst. 2008, A64, 383
&nbsp; URL[http://scripts.iucr.org/cgi-bin/paper?s0108767308005709,PAPER]

* Capelli et al., IUCr J. 2014, 1, 361
&nbsp; URL[http://journals.iucr.org/m/issues/2014/05/00/fc5002/index.html,PAPER]

* Kleemiss et al., Chem. Sci., 2021, 12, 1675
&nbsp; URL[https://pubs.rsc.org/en/content/articlehtml/2021/sc/d0sc05526c,PAPER]

## Hirshfeld Atom Refinement
The term **Hirshfeld Atom Refinement** (HAR), which is the principle underlying NoSpherA2, refers to X-ray crystal structure refinement using atomic electron density fragments derived from so-called Hirshfeld partitioning of the quantum mechanically calculated electron density of the whole structure. There are three steps to this procedure:
<ol>
<li>The molecular wavefunction is obtained for the input model using quantum mechanical calculations using:</li>
  <ul>
    <li>TONTO (shipped)</li>
    <li>ORCA (Versions 4.1.0 and up, obtainable from URL[https://orcaforum.kofo.mpg.de/index.php,WEB])</li>
    <li>pySCF</li>
    <li>Gaussian (various versions; implemented but not maintained)</li>
  </ul>
<li>The non-spherical atomic form factors are extracted from the molecular wavefunction by Hirshfeld partitioning of the atoms in the molecule.</li>
<li>olex2.refine uses these non-spherical form factors for the next refinement cycles. All normal commands for refinement can be used as usual, including restraints and contraints.</li>
</ol>
<br>
<br>

After the refinement cycles have completed, a new structure model will be obtained. This **will** require re-calculation of the molecular wavefunction before proceeding to further refinement because the geometry of the structure will have changed, affecting the electron density distribution. The three steps above need to be repeated until there is no more change and the model has completely settled. This process can be automated with the **Iterative** switch. This procedure is called *rigid body fitting*.
<br>
<br>
If multiple CPUs are to be used, the proper MPI must be installed. For Windows users, MS-MPI version 10 or higher is needed, while for Linux users, openMPI version 4 or higher is required. MacOS users will need to refer to Homebrew and install the appropriate versions of openMPI. The mpiexec(.exe) must be found in the PATH, either through Settings or Environment Variables.
<br>
<br>
Some recommended strategies for efficient refinement using ORCA are:
<ol>
  <li>PBE/SVP and Normal Grids</li>
  <li>PBE/TZVPP and Normal Grids</li>
  <li>PBE/TZVPP and High Grids</li>
</ol>

To ensure that the fit is optimal, it may be advantageous to try finishing up with meta or hybrid functionals. For atoms lighter than Kr it is best to use the **def2-** family of basis sets. If heavy elements are present, significant relativistic effects come into play, and it is recommended to use the **x2c-** family of basis sets and turn **Relativistics** on.

## Update Table
After ticking the 'NoSpherA2' box, the option **Update Table** will appear. The default method to calculate the wavefunction is the Quantum Mechanics software package **Tonto**, which is shipped with Olex2. The *recommended* software package is **ORCA**, which has been thoroughly benchmarked. Other software packages include **pySCF** and **Psi4**, which will need to be installed separately (pySCF will require WSL-Ubuntu on Windows). It is also possible to calculate wavefunctions with the widely used **Gaussian** software package, but this has not been tested thoroughly. These software options will appear automatically in Olex2 if the packages have been properly installed (check Settings and PATH). Once a Quantum Mechanics program has been chosen, the Extras have to be adjusted accordingly, in order not to use minimal settings. An imported **.wfn** file can also be used but care must be take to ensure that the geometry of the calculated structure **exactly** matches the geometry of the structure at the current stage of refinement in Olex2.
<br>
<br>

If **Update Table** is deactivated, a drop-down menu appears showing all .tsc files available in the current folder for refinement, without updating the files.


# NoSpherA2 Quick Buttons
Depending on whether the molecule contains only light atoms (e.g., organics), or contains any intermediate or heavy elements, different settings are required. Further, there are different levels of options within these settings, all of which can be adjusted in this options panel.

## Test
This allows for a quick test run of NoSpherA2 on a structure, to obtain a rapid assessment of what happens and eliminate basic errors before setting up more time-consuming runs.

## Work
This is where one works on a structure; with these settings, it is possible to evaluate, for example, whether constraints or restraints are necessary.

## Final
When all settings are finalized, a final NoSpherA2 job is run, which can take a long time, since it will continue until everything is completely settled.

# NoSpherA2 Options
All the settings required for the calculation of the .tsc file are found under this tool tab.


# NoSpherA2 Options 1

## Basis
This specifies the basis set for the calculation of the theoretical electron density and wavefunction. The basis sets in this drop-down menu are arranged in approximte order of size from small (top) to large (bottom). Smaller basis sets will yield rapid but approximate results, whereas calculations with the larger bases will be slower but more accurate. The default basis set is **def2-SVP**. The small basis **STO-3G** is recommended only for test purposes.
<br>
<br>

The **def2-** and **cc-** series of basis sets are only defined for atoms up to Kr. For atoms beyond Kr, ECPs (Effective Core Potentials) would be needed to use these basis sets, which are by the nature of the HAR method not compatible.
<br>
<br>

The **x2c-** basis sets are useful, as they are defined up to Rn without any ECPs. However, due to their size, calculations using the **x2c-** series are slow. It is **highly** recommended to run trial calculations using the smaller single valence basis sets mentioned above before proceeding to finalize the structure with a larger basis.

## Method
The default quantum mechanical method for the calculation of the theoretical wavefunction/electron density is **Hartee-Fock**. The density functional theory method **B3LYP** may be superior in some cases (especially for the treatment of hydrogen atoms), but tends to be unstable in Tonto in some cases. Both can be used in ORCA without such problems.

## CPUs
This specifies the number of CPUs to use during the wavefunction calculation. It is usually a good idea *not* to use *all* of them -- unless the computer is not used for anything else while it runs NoSpherA2! One CPU is needed for copying files and other such overhead tasks, so make sure one is available for these purposes. Olex2 will be locked during the calculation to prevent file inconsistencies. Also note: It is not recommended to run NoSpherA2 jobs in a Dropbox folder ... they tend to misbehave.

## Memory
The maximum memory that NoSpherA2 is allowed to use is entered here. This **must not** exceed the capabilities of the computer. If ORCA is used, the memory needs per core are calculated automatically; this input is the **total** memory used in the NoSpherA2 computations.

# NoSpherA2 Options 2

## Charge
The charge on the molecule or ion used in the wavefunction calculation. This **must** be properly assigned.

## Multiplicity
The multiplicity (2*S*+1) of the wavefunction, where *S* is the total spin angular momentum quantum number of the configuration. A closed-shell species, i.e., a molecule or ion with no unpaired electrons has *S* = 0, for a multiplicity of 1. Most organic molecules in their ground states fall into this category. However, a species with one unpaired electron (*S* = 1/2) will have a multiplicity of 2, a species with two unpaired electrons (*S* = 1/2 + 1/2 = 1) will have a multiplicity of 3, and so forth. It can be seen from the formula that the multiplicity has to be at least 1.

## Iterative
Check this box to continue full cycles of alternating wavefunction and least squares refinement calculations until final convergence is achieved. Convergence criteria are as defined in the options. This is a time-consuming option! If using ORCA, however, the last calculated wavefunction is used as the initial guess for the next calculation, which saves a lot of time in the consecutive steps.

## Max Cycles
This defines a criterion for the NoSpherA2 process to halt if convergence is not achieved. In such cases, it may be necessary to use restraints or constraints, better parameters, resolution cutoffs or other improvements to the model to achieve convergence.

## Update .tsc & .wfn
Clicking this button will only generate a new **.tsc** and **.wfn** file, without running a least squares refinement. This is useful after a converged model has been found, to get the most up-to-date wavefunction for property plotting or to test things before submitting a more time-consuming calculation.

# NoSpherA2 Options 3

## Integr.(ation) Accuracy
Select which accuracy level is requested for the integration of electron density. This affects time needed for calcualtion of .tsc files. Normal should be sufficient in all cases. Extreme is mainly for benchmark and test purposes. If you have high symmetry or very heavy elements and high resolution data it might improv results. Low can be used, if the number of electrons after integration is sill correct. Mostly fine for organic molecules. Please check in the log files, whether this is the case!

## Use Relativistics
Use DKH2 relativistic Hamiltonian. This should only be used with x2c-family basis sets. But for them it is highly recommended.

## H Aniso
Refine hydrogen atoms anisotrpically. Make sure they are not restricted by AFIX commands to obtain reasonable results.

## No Afix
Remove any AFIX constraints from the current model. Use with caution, but highly usefull for starting from IAM.

## DISP
Add DISP Instructuion to your .ins file based on sasaki table as implemented in olex2. DISP instructions are needed for correct maps and refinements in case of non metal-based wavelengths.

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

# NoSpherA2 Options Grouped Parts

## Grouped Parts (For disordered structures)
Since there might be different regions in your molecules containing disorder modelling you need to specify which disorders form a group for the calculation of Wavefunctions. A Group in this sense refers to PARTs, that resemble the same functional space. E.g. a disorder of a sodium atom with other singly charged ions around this position form a group (Let's say PARTs 1, 2 and 3 are PARTs describing three possibilities of this disorder), where these different PARTs are not interacting within the same molecular input structure, while at a second position there is a carboxylate in a disordered state, where one of the PARTs interacts with this disordered ion (PART 4), while the second PART (Nr. 5 in this case) does not.<br>
For the given example a reasonable grouping would be: 1-3;4,5 <br>
This would mean 1-3 are not to be interacting with each other, but each of them both with 4 and 5, respectively, leading to calcualtions:<br>
PART 1 & 4<br>
PART 1 & 5<br>
PART 2 & 4<br>
PART 2 & 5<br>
PART 3 & 4<br>
PART 3 & 5<br>
<br>
Groups are given by syntax: 1-4,9,10;5-7;8 (Group1=[1,2,3,4,9,10] Group2=[5,6,7] Group3=[8])<br>
<br>
It is easily understandible that having interactions between PART 1 and 2 in this example would be highly unphysical, which is why definition of disorder groups is crucial for occurances of disorder at more than one position.<br>
<br>
<font color='red'>**IMPORTANT: Superposition of two atoms with partial occupation freely refined without assignment to PARTs will lead to SEVERE problems during the wavefunction calcualtion, as there will be two atoms at 0 separation. Most likeley the SCF code will give up, but will NEVER give reasonable results!**</font>

# NoSpherA2 Properties
Utility for plotting and visualizing the results of NoSpherA2. Select desired reolustion of the grid to be calculated and properties to evaluate and click calcualte to start the beackground generation of grids. When done the calcualted fields will become available from the dropdown to show maps.<br>

# NoSpherA2 Properties Details
The reading of maps might take some time and olex might become irresponsive, please be patient.<br>
So far the calculation can only happen in the unit cell adn on the wavefunction in the folder. If you need an updated wavefunction (e.g. due to moved atoms or different spin state) hit the update tsc file button.<br>
n^<font color='red'>**The obtainable plots depend on your wavefunction calculated. Please make sure it is reasonbale. Also: If you use multiple CPUs the progress bar *might* behave in non-linear ways, this is due to the computations being executed in parallel and all CPUs being able to report progress. Some parts of the calculation might be faster than others.**</font>^n

## Lap
Laplacian of the electron density. This Grid shows regions of electron accumulation (negative values) and elecrton depletion (positive values), as it is the curvature of the density. Usefull to understand polrisation of bonds, position of lone-pairs etc.

## ELI
Calculates the Electron Localizability indicater. This function in summary describes the volume needed to find a different electron to the one at position <b>r</b>. This measure of localization very well correpsonods with chemically intuitive feautures like lone-pairs, bonds etc. The shape of isosurfaces is usually a nice indicator for bonding situations. In Olex2 the ELI-D of same spin electrons is used.<br>
A nice overview of all kinds of indicators developed by the original authors is given on this website:<br>
* URL[https://www.cpfs.mpg.de/2019352/eli,PAPER] &nbsp; 

## ELF
Calcuales the arbitrarily scaled Electron Localisation Function. This function is scaled between 0 and 1. There is no general rule how to select isovalues. Only included for legacy reasons. In general it is recommended to use ELI.

## ESP
Calculation of the total electrostatic potential. This is a complex caluclations, since the Potential V is an integral over the whole wavefunction:<br>
* <math>
	V<sub>tot</sub>(<b>r</b>) = V<sub>nuc</sub>(<b>r</b>) + V<sub>tot</sub>(<b>r</b>) = Σ<sub>A</sub> (Z<sub>A</sub> / |<b>r</b>-<b>R</b><sub>A</sub>|) - ∫ ρ(<b>r</b>') / |<b>r</b>-<b>r</b>'| <i>d<b>r</b>'</i>
</math> &nbsp; 
<br>This integral is the potential at each point in space due to all other electrons in the wavefunction, therefore the calculation of ESP does not scale with the thirs power of resolution of the grid, but rather the 9th power, which makes it really time consuming.<br>If you decide to cancel the job all cubes of the other calculations will be saved before starting ESP calculation, so you can restart only the ESP step.

## Res
Defines the resolution the calculated grid should have. Keep in mind that the complexity of teh calculation rises cubically.

## Calculate
Start the Calculaton of selected fields using NoSpherA2.

## Map
Selects which map is to be displayed. Only shows maps, which are already available. If there is none available try to calculate a new wavefunction of check for LIST 3 or 6 in the .ins file, as a fcf file with phases is needed.

## Toggle Map
Shows/Hides Map

## View

Selects what type of map is to be displayed. Choices include:<br>
  <ul>
    <li>plane - 2D</li>
    <li>plane + contour - 2D</li>
    <li>wire - 3D</li>
    <li>surface - 3D</li>
    <li>points - 3D</li>
  </ul>
  
## Edit Style
Edits the colour of the various map surfaces.

## Level
When a 3D map is displayed the slider bar enables you to adjust the detail shown in the map.

## Min
This will define the minimum value of your 2D map. The slider works in quarter-integer values but also accepts manual input in the text-box next to it.

## Step
This will define the step size of your 2D map between two contours/colours. As with **Min** this slider has pre-defined slider values (difference 0.02), but also manual input will work.

## Depth
This slider controls the depth of the plane "into" the screen. If the value is negative the map will go "behind" the model, positive will move it to the front.<br>
If you select atoms and click on the **Depth** button the map will be aligned so the map is in plane with these selected atoms.

## Size
Size will control the size of the plotted plane. Bigger values will decrease the visual size, but will increase the resultion of the map.