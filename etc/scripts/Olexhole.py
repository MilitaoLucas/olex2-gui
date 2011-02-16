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
! first cards which must be quoted
! (note that HOLE is case insensitive (except file names)
coord  01_1grm_single.pdb       ! Co-ordinates in pdb format
radius ~/hole2/rad/simple.rad   ! Use simple AMBER vdw radii
                                ! n.b. can use ~ in hole
!
! now optional cards
sphpdb example.sph              ! pdb format output of hole sphere centre info
                                ! (for use in sph_process program)
endrad 5.                       ! This is the pore radius that is taken
                                ! as an end
"""

'''
To run type spy.Olexhole() in Olex2
'''

def Olexhole(endrad="3"):
  print "This script converts the current model and creates a non_ortho_surface_area input dat, runs non_ortho_surface_area and reports the result"
  # We can assume that the INS name and information can come from Olex2
  probetypes = {
    'n2' : '3.4',
    'he' : '1',
    'co2' : '3.2'
  }
  run_inc = 0
  base_path = os.getcwd()
  while True:
    if(os.path.exists('%s//hole2_run%s'%(base_path, run_inc))):
      print "Failed to make hole2_run%s directory, as already present - incrementing"%run_inc
      run_inc = run_inc+1
    else:
      os.mkdir('%s//hole2_run%s'%(base_path, run_inc))
      hole2_path = "%s//hole2_run%s"%(base_path, run_inc)
      break
    
  Olex2holeIn = OV.FileName()
  holeCompatCell = (olx.xf_au_GetCell().split(','))
  brokensym = list(olx.xf_au_GetCellSymm())
  OlexZ = int(olx.xf_au_GetZ())
  AtomPairs = olx.xf_GetFormula().split()
  CellV = float(olx.xf_au_GetCellVolume())
  
  #Olex2 commands here!
  OV.cmd("isot")
  OV.cmd("pack -1 1 -1 1 -1 1")
  #OV.cmd("grow")
  OV.cmd("grow -w")
  OV.File("%s/olex_%s.pdb"%(hole2_path, Olex2holeIn))
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
  print "Job name", Olex2holeIn
  print "Unit Cell", holeCompatCell
  print "Olex2 Formula", olx.xf_GetFormula()
  print "Atom Count", olx.xf_au_GetAtomCount()
  print "Mw", olx.xf_au_GetWeight()
  print "New formula using Z", OlexZ
  print "Cell voume", CellV
#  print "Calculated density", CalDen
  print "RAddiiii?", olex_core.GetVdWRadii()
  print "Probes", probetypes
  for element in olex_core.GetVdWRadii():
    print "Element: ",element, "Radii: ", olex_core.GetVdWRadii()[element], "Diameter: ", 2*olex_core.GetVdWRadii()[element]

# Write the hole input file
# This is primative will need to add features such as patterson on and off
  holeINS= open("%s/%s.inp"%(hole2_path, Olex2holeIn), 'w')
  holeINS.write("coord  atoms_%s.pdb\n"%(Olex2holeIn)) #! file containing the framework coordinates
  holeINS.write("radius atoms_%s.rad\n"%(Olex2holeIn)) #! file containing the atom types and diameters
  holeINS.write("sphpdb atoms_%s.sph\n"%(Olex2holeIn)) #! pdb format output of hole sphere centre info
  #holeINS.write("%s\n"%(probetypes[probe])) #! probe size in A
  holeINS.write("endrad %s\n"%(endrad)) #! number of trial insertion
  holeINS.close()
 
  ATOMSINS= open("%s/atoms_%s.rad"%(hole2_path, Olex2holeIn), 'w')
  ATOMSINS.write("remark: van der Waals radii: from Olex2\n")
  ATOMSINS.write("remark: Default radii source: http://www.ccdc.cam.ac.uk/products/csd/radii\n")
  ATOMSINS.write("remark: similar to bondi but smaller H radii\n")
  for element in olex_core.GetVdWRadii():
    ATOMSINS.write("VDWR %s ??? %.2f\n"%(element.ljust(4,'?'), olex_core.GetVdWRadii()[element])) #! file containing the atom types and diameters
  ATOMSINS.close()
  
  holePDB= open("%s/atoms_%s.pdb"%(hole2_path, Olex2holeIn), 'w')
  rawPDB= open("%s/olex_%s.pdb"%(hole2_path, Olex2holeIn), 'r')
  # The following 3 lines are for testing purposes
  #holePDB.write("         1         2         3         4         5         6         7         8\n")
  #holePDB.write("12345678901234567890123456789012345678901234567890123456789012345678901234567890\n")
  #holePDB.write("ATOM      1  N   VAL A   1      -0.576  40.146  64.303  1.00 36.56           N\n")
  for line in rawPDB:
    if 'ATOM' in line:
      split_line = line.rsplit()
      # This gives us an ouput compatible with hole2 although not strictly correct pdb formating
      holePDB.write("%-6.6s%5.5s  %-3.3s %3.3s  %4.4s    %8.8s%8.8s%8.8s%6.6s%6.6s          %2.2s\n"
                    %(split_line[0], 
                      split_line[1], 
                      split_line[2],
                      split_line[3],
                      split_line[4],
                      split_line[5], 
                      split_line[6], 
                      split_line[7], 
                      split_line[8], 
                      split_line[9], 
                      split_line[10]
                    ))
    else:
      holePDB.write(line)
  holePDB.close()
  rawPDB.close()
  
# All this need error control
  try:
    print "Running hole calculation now"
    command = "hole < %s/%s.inp > %s/%s_hole.log "%(hole2_path, Olex2holeIn, hole2_path, Olex2holeIn)
    os.system(command)
    #hole_result = olx.Exec(command)
    print "Finished calculation"
  except:
    print "hole calculation failed to run"
    return
  try:
    hole_result_file = open("%s/%s_hole.log"%(hole2_path, Olex2holeIn), 'r')
    print "Reviewing Log File to Window:"
    for hole_line in hole_result_file:
      print hole_line.rstrip("\n")
    hole_result_file.close()
  except IOError: 
    print "Failed to open file"
    print "You can read this file by typing:"
    print "edit %s/%s_hole.log"%(hole2_path, Olex2holeIn)
    return
  try:
    print "Running hole conversion for dots....."
    command = "sph_process -dotden 15 -color %s/atoms_%s.sph %s/atoms_%s.qpt > %s/%s_sph_process_1_.log"%(
      hole2_path, 
      Olex2holeIn, 
      hole2_path, 
      Olex2holeIn,
      hole2_path,
      Olex2holeIn)
    print "Running command: ", command
    os.system(command)
    print "Finished conversion part 1"
  except:
    print "hole conversion 1 failed to run"
    return
  """
    try:
      hole_result_file = open("%s_sph_process_1_.log"%(Olex2holeIn), 'r')
      print "Successfully opened file", hole_result_file
      for hole_line in hole_result_file:
        print hole_line
      hole_result_file.close()
    except IOError: 
      print "Failed to open file"
      print "You can read this file by typing:"
      print "edit %s_sph_process_1_.log"%(Olex2holeIn)
      return
  """  
  try:
    print "Running hole conversion for surface...."
    command = "sph_process -sos -dotden 15 -color %s/atoms_%s.sph %s/atoms_%s.sos > %s/%s_sph_process_2_.log"%(
      hole2_path,
      Olex2holeIn,
      hole2_path,
      Olex2holeIn,
      hole2_path,
      Olex2holeIn)
    print "Running command: ", command
    os.system(command)
    print "Finished conversion part 2"
    print "If you want TUBES then run"
    print "sos_triangle -s < atoms_%s.sos > atoms_%s.vmd_tri"%(Olex2holeIn, Olex2holeIn)
    print "from %s"%hole2_path
    print "Now run 'qpt_conv' with option D to generate files for VMD"
  except:
    print "hole conversion 2 failed to run"
    return
  """
    try:
      hole_result_file = open("%s_sph_process_2_.log"%(Olex2holeIn), 'r')
      print "Successfully opened file", hole_result_file
      for hole_line in hole_result_file:
        print hole_line
      hole_result_file.close()
    except IOError: 
      print "Failed to open file"
      print "You can read this file by typing:"
      print "edit %s_sph_process_2_.log"%(Olex2holeIn)
      return
  """  
OV.registerFunction(Olexhole)
