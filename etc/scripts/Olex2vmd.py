import os
import sys
import shutil
import re
import olex
import olx
import olex_core
from olexFunctions import OlexFunctions
OV = OlexFunctions()

def Olex2vmd():
  print("This script converts the current model and creates a vmd compatible pdb")
  # We can assume that the INS name and information can come from Olex2
  # The modified pdb which uses the same process as for hole2 seems to produce pdb files where all the bonding
  # is fine in vmd the default output from Olex2 does not
  
  # This basically creates a new folder everytime the command is run
  run_inc = 0
  base_path = OV.FilePath()
  print(OV.FilePath())
  while True:
    if(os.path.exists('%s/vmd_run_%2.2d'%(base_path, run_inc))):
      print("Failed to make vmd_run_%2.2d directory, as already present - incrementing"%run_inc)
      run_inc = run_inc+1
    else:
      os.mkdir('%s/vmd_run_%2.2d'%(base_path, run_inc))
      hole2_path = "%s/vmd_run_%2.2d"%(base_path, run_inc)
      break
    
  Olex2holeIn = OV.FileName()
  #Olex2 commands here!
  #OV.cmd("isot") # This is currently turned off as it can break the model if from an oxm file?
  OV.File("%s/olex_%s.pdb"%(hole2_path, Olex2holeIn)) # Olex2 format pdb file of whatever is selected/present
 
  # General stuff for the user to see in Olex2
  print("Job name: ", Olex2holeIn)
 
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
  
OV.registerFunction(Olex2vmd)
