# NoSpherA2

## Literature

* Jayatilaka & Dittrich., Acta Cryst. 2008, A64, 383
&nbsp; URL[http://scripts.iucr.org/cgi-bin/paper?s0108767308005709,PAPER]

* Capelli et al., IUCrJ. 2014, 1, 361
&nbsp; URL[http://journals.iucr.org/m/issues/2014/05/00/fc5002/index.html,PAPER]

* Kleemiss et al., Chem. Sci., 2021, 12, 1675
&nbsp; URL[https://pubs.rsc.org/en/content/articlehtml/2021/sc/d0sc05526c,PAPER]

When ticked, **non-spherical form factors**  will be used in the refinement of the structure.

n^<font color='red'>**This is a new and highly experimental procedure inside Olex2, which requires intensive computing ressources. Testing was performed using ORCA and Tonto as .tsc sources.**</font>^n

<br>
<br>

For **Hirshfeld Atom Refinement** There are three steps to this procedure:
<ol>
<li>The molecular wavefunction is obtained for your input model using Quantum Mechanical calculations using:</li>
  <ul>
    <li>TONTO (shipped)</li>
    <li>ORCA (Versions 4.1.0 and up, obtainable from URL[https://orcaforum.kofo.mpg.de/index.php,WEB])</li>
    <li>pySCF</li>
    <li>Gaussian of various versions (implemented but not maintained)</li>
  </ul>
<li>The atomic non-spherical form factors are extracted from the molecular wavefunction by Hirshfeld partitioning of the atoms in the molecule.</li>
<li>olex2.refine now uses these non-spherical form factors for the next refinement cycles. All normal commands for your refinement can be used, including restraints and contraints.</li>
</ol>
<br>
<br>
At this point, a new model will be obtained, and this **will** require the re-calculation of the molecular wavefunction -- and the above three steps need to be repeated until there is no more change and the model is completely settled. This process can be autmoatized by using the **Iterative** switch. Otherwise this procedure is called a *rigid body fit*.
<br>
If you want to use more CPUs make sure the proper MPI Installation is found on your computer. For Windows user install MS-MPI of at least Version 10, for Linux Users openMPI version 4 or up is required. MacOS users please refer to homebrew and install apropiate versions of openMPI. The mpiexec(.exe) is needed to be found in the PATH, either through Settings or Environment Variables.
<br>
A recommended strategy for efficient refinements using ORCA is:
<ol>
  <li>PBE/SVP and Normal Grids</li>
  <li>PBE/TZVPP and Normal Grids</li>
  <li>PBE/TZVPP and High Grids</li>
</ol>
In case you want to make sure it is the best possible fit you can try finishing up with meta or hybrid functionals. In case of all atoms lighter than Kr it is best to use def2- familiy of basis sets. In case of any heavy element or significant relativistic effects use x2c- with relativistics on.

### Update Table
After ticking the 'NoSpherA2' box, the option **Update Table** will appear. The default method to calculate the wavefunction is **Tonto**. The most benchmarked and recommended software is **ORCA**. Other softwares, as long as installed, include **pySCF** and **Psi4** (pySCF will require WSL-Ubuntu on windows) and there is also an option to use **Gaussian** [HIGHLY UNTESTED]. A present **.wfn** file can also be used but **must** agree to the geometry currtly used in Olex2. These options will appear, depending on whether they are properly installed and Olex2 knows about them -> Settings and PATH). Once a program has been chosen, please also adjust the Extras according to your needs if you do not want to use minimal settings.<br>If Update Table is deactivated a Dropdown of all found .tsc files in the current folder is given to be used for refinement, without updating the files.


# NoSpherA2 Quick Buttons
Depending on the molecule (Organic, lighter heavy elements, heavy metals), different set of defaults settings are required. And within these sets, there are different levels, too. Of course, you can also change any of the settings from the tools provided in the rest of this options panel.

## Test
These settings allow for a quick NoSpherA2 test run of your structure. You can quickly see what happens and eliminate basic errors before getting into the other, more time-consuming runs

## Work
This is where you will work on your structure. With these settings you can evaluate whether constraints or restraints are necessary, for example.

## Final
When you are happy with everything being ok, you can then run your final NoSpherA2 job, which can take a long time, since it will run until everything is completely settled.

# NoSpherA2 Options
This tool provides all the settings required for the calculation of the .tsc file.


# NoSpherA2 Options 1

## Basis
This specifies the basis set for the calculation of the theoretical density and wavefunction. The default basis set is **def2-SVP**. **STO-3G** is recommended only for test purposes.
The **def2**- and **cc-** series of basis sets is only defined for atoms up to Kr. Afterword ECPs (Effective core potentials) would be needed to use these basis sets, which are by the nature of the method not compatible. 
Then the **x2c**-basis sets are usefull, as they are defined up to Rn without any ECPs.
It is **highly** recommended to run basic first iterations using single valence basis sets and finish the structure with a higher basis.

## Method
The default method used for the calculation of the theoretical MOs/Density is **Hartee-Fock**. **B3LYP** may be superior in some cases (especially for the treatment of hydrogen  atoms), but tends to be unstable inside Tonto in some cases. Both can be used in ORCA and are perfectly fine here.

## CPUs
The number of CPUs to use during the waverfunction calculation. It is usually a good idea to *not* use *all* of them -- unless you don't want to use the computer for anything else while it runs NoSpherA2! Olex2 will be locked during the calculation to prevent inconsitencies of files. Mostly copying files etc needs overhead CPU capacity, so please leave 1 CPU for these kinds of things. Also note: It is not recommended to run jobs in a Dropbox Folder... They tend to break.

## Memory
The maximum memory that NoSpherA2 is allowed to use. This **must not** exceed the capabilities of the computer. If ORCA is used the memory needs per core are calcualted automatically, this input is the **total** memory.

# NoSpherA2 Options 2

## Charge
The charge of the molecule used for the wavefunction calculation. This **must** be properly assigned.

## Multiplicity
The multiplicity (2*S*+1) of the wavefunction, where S is the total spin angular momentum of the configuration. E.g. a closed shell wavefunction in it's ground-state usually has multiplicity 1, one unpaired electron has multiplicity 2. Must be positive above 0.

## HAR // Iterative
Continue calculations until final convergence is achieved over a full cycle of WFN and Least Squares refinement. Criteria as per definiton of HAR in tonto. This will need much more time. But in case you use ORCA the last wavefunction is used as initial guess, which will save a lot of time on the consecutive steps.

## Max Cycles
This defines a criteria for the abortion of HAR, if convergence is not achieved. Maybe restraints or better parameters, resolution cutoffs or other improvements to your model might help with convergence.

## Update .tsc & .wfn
This button will only generate a new .tsc and .wfn file, without running a least squares refinement. This is usefull after a converged model was found to get the most up-to-date wavefunction for property plotting or to test things before submitting a bigger calculation.

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