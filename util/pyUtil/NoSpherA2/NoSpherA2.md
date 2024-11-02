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
This button is used when working on a structure with NoSpherA2; with these settings, it is possible to evaluate, for example, whether constraints or restraints are necessary.

## Final
When all settings are finalized, a final NoSpherA2 job is run by clicking this button. The final job can take a long time, since it is generally run with a large basis set and continues until everything is completely settled.

# NoSpherA2 Options
All the settings required for the calculation of the .tsc file are found under this tool tab.


# NoSpherA2 Options 1

## Basis
This specifies a basis set to be used for calculating the theoretical electron density and wavefunction. The basis sets in this drop-down menu are arranged in approximte order of size from small (top) to large (bottom). Smaller basis sets will yield rapid but approximate results, whereas calculations with the larger bases will be slower but more accurate. The default basis set is **def2-SVP**. The small basis **STO-3G** is recommended only for test purposes.
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
The multiplicity (2*S*+1) of the wavefunction, where *S* is the total spin angular momentum quantum number of the configuration. It is important to assign this multiplicity correctly. A closed-shell species, i.e., a molecule or ion with no unpaired electrons, has *S* = 0, for a multiplicity of 1. Most organic molecules in their ground states fall into this category. However, a species with one unpaired electron (*S* = 1/2) will have a multiplicity of 2, a species with two unpaired electrons (*S* = 1/2 + 1/2 = 1) will have a multiplicity of 3, and so forth. It can be seen from the formula that the multiplicity has to be at least 1.

## Iterative
Check this box to continue full cycles of alternating wavefunction and least squares refinement calculations until final convergence is achieved. Convergence criteria are as defined in the options. This is a time-consuming option! If using ORCA, however, the last calculated wavefunction is used as the initial guess for the next calculation, which saves a lot of time in the consecutive steps.

## Max Cycles
This defines a criterion for the NoSpherA2 process to halt if convergence is not achieved. In such cases, it may be necessary to use restraints or constraints, better parameters, resolution cutoffs or other improvements to the model to achieve convergence.

## Update .tsc & .wfn
Clicking this button will only generate a new **.tsc** and **.wfn** file, without running a least squares refinement. This is useful after a converged model has been found, to get the most up-to-date wavefunction for property plotting or to test things before submitting a more time-consuming calculation.

# NoSpherA2 Options 3

## Integr. Accuracy
Select the level of accuracy to be used for the integration of electron density. This affects the time needed for calculating .tsc files. **Normal** should generally be sufficient. **Extreme** is mainly for benchmarking and testing purposes; if you have high symmetry or very heavy elements and high resolution data it might improve results. **Low** can be used if the number of electrons after integration is still correct, and will usually suffice for organic molecules. However, always check that the number of electrons is correct in the log files!

## Use Relativistics
Use the DKH2 relativistic Hamiltonian (important when heavy elements are present in the structure). This option should only be used with **x2c-** family of basis sets, but for them it is highly recommended.

## H Aniso
Refine hydrogen atoms anisotropically. Make sure they are not restricted by AFIX commands to obtain reasonable results.

## No AFIX
Remove any AFIX constraints from the current model. Use with caution, but highly useful for starting from the independent atom model.

## DISP
Add a DISP instruction to your .ins file based on Sasaki tables of anomalous scattering factors as implemented in Olex2. DISP instructions are needed for correct maps and refinements in case of uncommon X-ray wavelengths (e.g., synchrotron radiation).

## Cluster *r* (For Tonto)
If Tonto is used for wavefunction calculations a cluster of **explicit charges** calculated in a self-consistent procedure is used to mimic the crystal field for the wavefunction calculation. This option defines the radius *r* beyond which no charges are included.

## Complete Cluster (For Tonto)
For refinement of molecular structures, this switch will try to complete molecular fragments for the charges calculation (see **Cluster r** above) based on reasonable interatomic distances. If the structure being refined is a network compound whose molecular boundary cannot be simply defined, i.e., there is no way to grow the structure without having dangling bonds, this procedure will fail when the computer runs out of memory. Therefore, this option is highly recommended for molecular crystals but must be turned off for network compounds.

## DIIS Conv. (For Tonto)
This option defines the convergence criterion for the wavefunction calculations. A lower value will cause the calculations to finish faster but will also drastically increase the likelihood of generating unreasonable wavefunctions, especially with complicated structures.

## SCF Conv. Thresh. (For ORCA)
This option sets the convergence criterion for the self-consistent field (SCF) wavefunction calculation in ORCA. Use **NormalSCF** for default calculations, and **Tight** or **Very Tight** for very precise high-level calculations. **Extreme** is basically the numerical limit of the computer; its use is strongly discouraged, as this convergence criterion is practically unreachable except for tiny systems (<3 atoms).

## SCF Conv. Strategy (For ORCA)
Selects the mechanism by which the SCF calculation converges to the energy minimum. Refers to the step size used in applying calculated gradients to the wavefunction.

## Dyn. Damp (For ORCA)
This Option allows ORCA to dynamically change the damping factor between calculation steps. This option can help in tricky cases when the wavefunction does not want to converge normally or might allow to go with an option "one up", that is Easy instead of NormalConv in some cases, sicne the damping factor will "breathe".

# NoSpherA2 Options Grouped Parts

## Grouped Parts (for disordered structures with PART instructions)
If the structure model contains disorder, it is necessary to specify which disordered atoms form a *group* in the wavefunction calculations. A group in this sense refers to PARTs, that resemble the same functional space. For example, consider disorder resulting from a sodium ion and two other singly charged ions in a certain position in the structure - these form a group. Let's say PARTs 1, 2 and 3 describe the three possibilities of this disorder. These different PARTs do not interact with one another in this molecular structure. Now suppose that at a second position in this structure there is a carboxylate in a disordered state consisting in turn of two PARTs, of which one (PART 4) interacts with these disordered ions, but the second (PART 5) does not.
<br>
Note: Groups are specified using the following syntax: 1-4,9,10;5-7;8 would mean Group1=[1,2,3,4,9,10], Group2=[5,6,7], and Group3=[8]).
<br>
<br>
For this example a reasonable grouping would be: 1-3;4,5. This means PARTS 1-3 do not interact with one other, but each of them interacts individually with both 4 and 5, leading to calculations:
<br>
<br>
PART 1 & 4<br>
PART 1 & 5<br>
PART 2 & 4<br>
PART 2 & 5<br>
PART 3 & 4<br>
PART 3 & 5<br>
<br>
In this example, interactions between PARTs 1 and 2 would be unphysical, each PART represents an ion occupying a position *by itself*.Thus, the correct definition of disorder groups is crucial for occurrences of disorder at one or more positions.
<br>
<br>
<font color='red'>**IMPORTANT: Superposition of two atoms with partial occupancy freely refined without assignment to PARTs will lead to SEVERE problems during the wavefunction calculation, as this will involves two overlapping atoms. In such cases, the SCF wavefunction calculation will most probably fail, but in any case, it will NEVER give reasonable results!**</font>

# NoSpherA2 Properties
The utilities in this tool tab are for plotting and visualizing the results of NoSpherA2. A calculated wavefunction must be present in the main work folder for the structure (all calculated .wfn files are stored within the olex2 folder). Select the desired resolution of the grid to be calculated and the properties to be evaluated, then click **Calculate** to start the background generation of grids. When done the calculated maps will become available from the **Plot** drop-down menu. Choose *wire* from the **View** drop-down menu and select the desired map from the **Plot** menu. It may be necessary to drag the **Level** slider to view the map.

# NoSpherA2 Properties Details
The calculation of maps can be time-consuming and Olex2 might become unresponsive, so please be patient.
<br>
<br>
So far the calculation can only happen in the unit cell and on the wavefunction in the folder. If an updated wavefunction is needed (e.g., due to moved atoms or a different spin state) click the **Update .tsc & .wfn** button.
<br>
<br>
n^<font color='red'>**The available plots depend on the calculated wavefunction, so it is critical that the wavefunction is reasonably accurate. If multiple CPUs are in use, the progress bar *might* behave in non-linear ways as all CPUs report progress while the computations are executed in parallel. Some parts of the calculation might be completed faster than others.**</font>^n

## Lap
Takes the Laplacian of the electron density. This map shows regions of electron accumulation (negative values) and electron depletion (positive values), as it is the calculated curvature of the electron density function. This may be used to gain insight into the polarisation of bonds, positions of lone-pairs, etc.

## ELI
Calculates the Electron Localizability Indicator. In brief, this estimates the volume needed to find a different electron from the one at position *r*. This measure of localization corresponds closely to chemically intuitive feautures such as lone-pairs and bonds. The shape of isosurfaces is usually a useful indicator of bonding. In Olex2 the ELI-D of same-spin electrons is used.<br>
A nice collection of papers about these types of indicators by the original authors is available at this website:<br>
* URL[https://www.cpfs.mpg.de/2019352/eli,PAPER] &nbsp; 

## ELF
Calculates the Electron Localisation Function, arbitrarily scaled between 0 and 1. There is no general rule for how to select isovalues. It is only included here for legacy reasons; in general, it is recommended to use ELI instead.

## ESP
Calculation of the total electrostatic potential. This is a complex calculation, since the potential *V* involves an integral over the whole wavefunction:<br>
* <math>
	V<sub>tot</sub>(<b>r</b>) = V<sub>nuc</sub>(<b>r</b>) + V<sub>tot</sub>(<b>r</b>) = Î£<sub>A</sub> (Z<sub>A</sub> / |<b>r</b>-<b>R</b><sub>A</sub>|) - âˆ« Ï�(<b>r</b>') / |<b>r</b>-<b>r</b>'| <i>d<b>r</b>'</i>
</math> &nbsp; 
<br>
The ESP represents the potential at each point in space due to all other electrons in the wavefunction. The calculation of the ESP does not scale with the third power of the grid resolution, but rather the 9th power, which makes it really time consuming.
<br>
<br>
If multiple maps, including ESP, are selected from this menu, the .cube output files of all other calculations are saved before the ESP calculation is started. Thus, if the job is cancelled during the ESP calculation, those output files will be available and it will only be necessary to restart the ESP calculation.

## Res
Defines the resolution of the grid used for map calculations. Note that the time required for a calculation grows cubically as resolution increases, so caution must be exercised when going to very high resolution.

## Calculate
Calculates the maps of the selected fields using NoSpherA2. Simply clicking this button does not display the calculated map - a map has to be selected for display from the **Plot** menu.

## Plot
Select a map to be displayed from this drop-down menu. Only maps that have already been calculated will be shown. If none are available, calculate a new wavefunction (or copy an existing .wfn file from the olex2 subfolder to the main working folder for the structure) and check for LIST 3 or 6 in the .ins file, as a .fcf file with phases is needed.

## Disable Map
Clears the map display.

## View
Selects the map display format. Choices include:<br>
  <ul>
    <li>plane - 2D</li>
    <li>contour + plane - 2D</li>
    <li>wire - 3D</li>
    <li>surface - 3D</li>
    <li>points - 3D</li>
  </ul>
The wire, surface, and points display are well-suited to many of the 3D types of maps calculated here (LAP, ELI, ESP, etc.).

## Edit Style
Click this button to edit the colours of the various map surfaces displayed.

## Level
When a 3D map is displayed, this slider bar adjusts the level of detail shown in the map. If no map is on the screen, move this slider to check whether the level setting is too low or too high. Specific values of the level can also be typed into the text box next to the slider.

## Min
This sets the minimum value of the displayed parameter on a 2D map (plane and contour + plane formats). The slider increments or decrements this minimum in quarter-integer steps, but a specific value can be entered manually in the text box next to it.

## Step
This defines the step size of a 2D map between two adjacent contours/colours. As with **Min**, this slider has pre-defined increments/decrements (0.02), but specific values of the step size can also be manually entered in the box next to the slider.

## Depth
This slider moves a displayed 2D map into or out of the screen. At very negative values of the depth, the map moves 'behind' the model (away from the viewer) and at very positive values the map moves in front of the model (towards the viewer).
<br>
<br>

Select three or more atoms and click the **Depth** button to display a map that lies in the mean plane (also displayed) through these atoms. To delete the mean plane itself, click on it and press the '<c>Delete</c>' key.

## Size
This slider controls the size of the plotted 2D map. Larger values decrease the size of the map on the screen, but increase the resolution of the map. Again, specific values of the map size can be manually entered in the text box next to the slider.