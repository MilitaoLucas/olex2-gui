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
"""

'''
To run type spy.OlexBET() in Olex2
'''

def OlexBET(probe="n2", trials="5000"):
  print "This script converts the current model and creates a non_ortho_surface_area input dat, runs non_ortho_surface_area and reports the result"
  # We can assume that the INS name and information can come from Olex2
  probetypes = {
    'n2' : '3.681',
    'he' : '1',
    'co2' : '1'
  }

  Olex2BETIn = OV.FileName()
  BETCompatCell = (olx.xf_au_GetCell().split(','))
  brokensym = list(olx.xf_au_GetCellSymm())
  OlexZ = int(olx.xf_au_GetZ())
  AtomPairs = olx.xf_GetFormula().split()
  CellV = float(olx.xf_au_GetCellVolume())
  OV.cmd("pack cell")
  OV.File("atoms_%s.xyz"%(Olex2BETIn))
  OV.AtReap("atoms_%s.xyz"%(Olex2BETIn))
  CalDen = ((float(olx.xf_au_GetWeight())*OlexZ)/(CellV*0.60225))
  print AtomPairs
  AtomGroups = []
  CorrectedAtoms = []
  for atom in AtomPairs:
    AtomGroups.append(re.split("([A-Za-z]*)",atom)[1:3])
  print AtomGroups
  for j in range(0, len(AtomGroups)):
    print AtomGroups[j][0], AtomGroups[j][1]
    CorrectedAtoms.append("%s %s"%(AtomGroups[j][0], (AtomGroups[j][1])))
  AtomContents = ' '.join(CorrectedAtoms)
  print AtomContents
  print "ETF", AtomContents
  #AtomContents = ' '.join(re.split("([A-Za-z]*)",olx.xf_GetFormula()))
  snuff = re.split("([A-Za-z]*)",olx.xf_GetFormula())

  # General stuff for the user to see in Olex2
  print "Job name", Olex2BETIn
  print "Unit Cell", BETCompatCell
  print "Olex2 Formula", olx.xf_GetFormula()
  print "Atom Count", olx.xf_au_GetAtomCount()
  print "Mw", olx.xf_au_GetWeight()
  print "New formula using Z", OlexZ
  print "Cell voume", CellV
  print "Calculated density", CalDen
  print "RAddiiii?", olex_core.GetVdWRadii()
  print "Probes", probetypes
  for element in olex_core.GetVdWRadii():
    print "Element: ",element, "Radii: ", olex_core.GetVdWRadii()[element], "Diameter: ", 2*olex_core.GetVdWRadii()[element]

# Write the BET input file
# This is primative will need to add features such as patterson on and off
  BETINS= open("%s.dat"%(Olex2BETIn), 'w')
  BETINS.write("atoms_%s.atoms\n"%(Olex2BETIn)) #! file containing the atom types and diameters
  BETINS.write("atoms_%s.xyz\n"%(Olex2BETIn)) #! file containing the framework coordinates
  BETINS.write("%s\n"%(probetypes[probe])) #! probe size in A
  BETINS.write("%s\n"%(trials)) #! number of trial insertion
  BETINS.write("%s %s %s\n"%(BETCompatCell[0], BETCompatCell[1], BETCompatCell[2])) #! length of unit cell a, b, c in A
  BETINS.write("%s %s %s\n"%(BETCompatCell[3], BETCompatCell[4], BETCompatCell[5])) #! unit cell angles alpha, beta, gamma
  BETINS.write("%s\n"%(CalDen)) #! crystal density in g / cm3
  BETINS.close()

  ATOMSINS= open("atoms_%s.atoms"%(Olex2BETIn), 'w')
  for element in olex_core.GetVdWRadii():
    ATOMSINS.write("%s %s\n"%(element, 2*olex_core.GetVdWRadii()[element])) #! file containing the atom types and diameters
  ATOMSINS.write("EOF")
  ATOMSINS.close()

  
# All this need error control
  try:
    print "Running BET calculation now"
    content = os.popen("nonorthoSA.exe < %s.dat > %s_BET.log"%(Olex2BETIn, Olex2BETIn)).read() # This pipes our new .dat file into nonortho
    #BET_result = olx.Exec("nonorthoSA.exe < %s.dat > %s_BET.log"%(Olex2BETIn, Olex2BETIn))
    print "Finished calculation"
  except:
    print "BET calculation failed to run"
    return
  #print content # Output from pipe need proper error control here

OV.registerFunction(OlexBET)
