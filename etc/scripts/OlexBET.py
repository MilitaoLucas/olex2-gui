import os
import sys
import shutil
import re
import olex
import olx
import olex_core
from olexFunctions import OlexFunctions
OV = OlexFunctions()
"""
UFF.atoms
IRMOF1.xyz
3.681
5000
25.83200 25.83200 25.83200
90. 90.  90.
0.59



! file containing the atom types and diameters
! file containing the framework coordinates
! probe size in A
! number of trial insertion
! length of unit cell a, b, c in A
! unit cell angles alpha, beta, gamma
! crystal density in g / cm3
    'n2' : '3.681',
"""

'''
To run type spy.OlexBET() in Olex2
'''

def OlexBET(probe="N2", trials="5000"):
  print("This script converts the current model and creates a non_ortho_surface_area input dat, runs non_ortho_surface_area and reports the result")
  # We can assume that the INS name and information can come from Olex2
  # These probe values are from the AIC group standards KS uses 3.4 and 3.2 for N2 and CO2
  """probetypes = {
    'n2' : '3.64',
    'me' : '3.24',
    'co2' : '3.4',
    'h2' : '2.84'
  }"""
  
  # These probe types come from:
  # Hirschfelder, C. F.; Curtiss, C. F.; Bird, R. B. Molecular Theory of Gases and Liquids; Wiley: New York, 1954; p 1110
  # They are the constants defined by viscosity data and are from the 80 to 300 K temperature range result set.
  probetypes = {
    # Light Gases
    'He' : '2.576',
    'H2': '2.968',
    'D2' : '2.948',
    # Noble Gases
    'Ne' : '2.789',
    'Ar' : '3.418',
    'Kr' : '3.61',
    'Xe' : '4.055',
    # Simple Polyatomic Gases
    'Air' : '3.617',
    'N2' : '3.681',
    'O2' : '3.433',
    'CO' : '3.590',
    'CO2' : '3.996',
    'NO' : '3.470',
    'N2O' : '3.879',
    'CH4' : '3.822',
    'CCl4' : '5.881',
    'SO2' : '4.290',
    'F2' : '3.653',
    'Cl2' : '4.115',
    'Br2' : '4.268',
    'I2' : '4.982',
    # Other Inorganic Vapours
    'HCl' : '3.305',
    'HI' : '4.123',
    'AsH3' : '4.06',
    'HgI2' : '5.625',
    'HgBr2' : '5.414',
    'SnBr4' : '6.666',
    'SnCl4' : '4.540',
    'Hg' : '2.898',
    # Hydrocarbons
    'C2H2' : '4.221',
    'C2H4' : '4.232',
    'C2H6' : '4.418',
    'C3H8' : '5.061',
    'nC4H10' : '4.997',
    'iC4H10' : '5.341',
    'nC5H12' : '5.769',
    'nC6H14' : '5.909',
    'nC8H18' : '7.451',
    'nC9H20' : '8.448',
    'chexane' : '6.093',
    'C6H6' : '5.270',
    # Other Organic Vapours
    'CH3OH' : '3.585',
    'C2H5OH' : '4.455',
    'CH3Cl' : '3.375',
    'CH2Cl2' : '4.759',
    'CHCl3' : '5.430',
    'C2N2' : '4.38',
    'COS' : '4.13',
    'CS2' : '4.438',
    # Common Names
    'DCM' : '4.759',
    'Me' : '3.822',
    'ksn' : '3.2',
    'ksc' : '3.4'
  }
  
  run_inc = 0
  base_path = OV.FilePath()
  Olex2BETIn_start = OV.FileFull()
  print(OV.FilePath())
  while True:
    if(os.path.exists('%s/BET_run_%2.2d'%(base_path, run_inc))):
      print("Failed to make BET_run_%2.2d directory, as already present - incrementing"%run_inc)
      run_inc = run_inc+1
    else:
      os.mkdir('%s/BET_run_%2.2d'%(base_path, run_inc))
      BET_path = "%s/BET_run_%2.2d"%(base_path, run_inc)
      break
  
  Olex2BETIn = OV.FileName()
  BETCompatCell = (olx.xf.au.GetCell().split(','))
  brokensym = list(olx.xf.au.GetCellSymm())
  OlexZ = int(olx.xf.au.GetZ())
  AtomPairs = olx.xf.GetFormula().split()
  CellV = float(olx.xf.au.GetCellVolume())
  
  # Olex2 internal commands here
  OV.cmd("pack cell")
  OV.File("%s/atoms_%s.xyz"%(BET_path, Olex2BETIn))
  OV.AtReap("%s/atoms_%s.xyz"%(BET_path, Olex2BETIn))
  CalDen = ((float(olx.xf.au.GetWeight()))/(CellV*0.60225))
  
  # Back to starting model
  OV.AtReap(Olex2BETIn_start)
  
  # General stuff for the user to see in Olex2
  print("Job name", Olex2BETIn)
  print("Unit Cell", BETCompatCell)
  print("Olex2 Formula", olx.xf.GetFormula())
  print("Atom Count", olx.xf.au.GetAtomCount())
  print("Mw", olx.xf.au.GetWeight())
  print("New formula using Z", OlexZ)
  print("Cell voume", CellV)
  print("Calculated density", CalDen)
  print("RAddiiii?", olex_core.GetVdWRadii())
  print("Probe Used", probe, " : ", probetypes[probe])
  for element in olex_core.GetVdWRadii():
    print("Element: %2.2s Radii: %2.2f Diameter: %2.2f"%(element, olex_core.GetVdWRadii()[element], 2*olex_core.GetVdWRadii()[element]))

# Write the BET input file
# This is primative will need to add features such as patterson on and off
  BETINS= open("%s/%s.dat"%(BET_path, Olex2BETIn), 'w')
  BETINS.write("%s/atoms_%s.atoms\n"%(BET_path, Olex2BETIn)) #! file containing the atom types and diameters
  BETINS.write("%s/atoms_%s.xyz\n"%(BET_path, Olex2BETIn)) #! file containing the framework coordinates
  BETINS.write("%s\n"%(probetypes[probe])) #! probe size in A
  BETINS.write("%s\n"%(trials)) #! number of trial insertion
  BETINS.write("%s %s %s\n"%(BETCompatCell[0], BETCompatCell[1], BETCompatCell[2])) #! length of unit cell a, b, c in A
  BETINS.write("%s %s %s\n"%(BETCompatCell[3], BETCompatCell[4], BETCompatCell[5])) #! unit cell angles alpha, beta, gamma
  BETINS.write("%s\n"%(CalDen)) #! crystal density in g / cm3
  BETINS.close()

  ATOMSINS= open("%s/atoms_%s.atoms"%(BET_path, Olex2BETIn), 'w')
  for element in olex_core.GetVdWRadii():
    ATOMSINS.write("%2.2s %2.2f\n"%(element, 2*olex_core.GetVdWRadii()[element])) #! file containing the atom types and diameters
  ATOMSINS.write("EOF")
  ATOMSINS.close()

  
# All this need error control
  try:
    print("Running BET calculation now")
    content = os.popen("nonorthoSA.exe < %s/%s.dat > %s/%s_BET.log"%(BET_path, Olex2BETIn, BET_path, Olex2BETIn)).read() # This pipes our new .dat file into nonortho
    #BET_result = olx.Exec("nonorthoSA.exe < %s.dat > %s_BET.log"%(Olex2BETIn, Olex2BETIn))
    print("Finished calculation")
  except:
    print("BET calculation failed to run")
    return
  try:
    BET_result_file = open("%s/%s_BET.log"%(BET_path, Olex2BETIn), 'r')
    print("Reviewing Log File to Window:")
    for BET_line in BET_result_file:
      print(BET_line.rstrip("\n"))
    BET_result_file.close()
  except IOError: 
    print("Failed to open file")
    print("You can read this file by typing:")
    print("edit %s/%s_BET.log"%(BET_path, Olex2BETIn))
    return
  #print content # Output from pipe need proper error control here

OV.registerFunction(OlexBET)
