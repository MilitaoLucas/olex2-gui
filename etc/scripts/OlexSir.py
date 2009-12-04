import os
import sys
import shutil
import re
import olex
import olx
from olexFunctions import OlexFunctions
OV = OlexFunctions()

'''
To run this example script, type spy.example("Hello") in Olex2
'''

def OlexSir(ManAtomContents="C 20 H 20 O 10"):
  print "This script takes an exsiting file and pushes it into SIR"
  # Experimenting with patterson function but having issues using the partial command to work?
  patterson = 0

  # We can assume that the INS name and information can come from Olex2
  # In fact probably won't need this as I only need Cell, SpaceGroup, Content (SFAC/UNIT), reflection)
  """
  SIR97 - Altomare A., Burla M.C., Camalli M., Cascarano G.L., Giacovazzo C. , Guagliardi A., Moliterni A.G.G., Polidori G.,Spagna R. (1999) J. Appl. Cryst. 32, 115-119.

  %Data
  Cell a b c alpha, beta, gamma
  SpaceGroup NAME
  Content ATOM Number
  Reflections filename.hkl
  %Continue
  """
  
  sirversion = 97
  #names = OV.FileName()
  Olex2SirIn = OV.FileName()
  SirCompatCell = ''.join(olx.xf_au_GetCell().split(','))
  SirCompatSymm = ' '.join(re.split("([A-Za-z])", olx.xf_au_GetCellSymm()))
  AtomContents = ' '.join(re.split("([A-Za-z]*)",olx.xf_GetFormula()))
  snuff = re.split("([A-Za-z]*)",olx.xf_GetFormula())
  OlexZ = int(olx.xf_au_GetZ())
  NumPeaks = int(OlexZ) * int(olx.xf_au_GetAtomCount())
  CellV = float(olx.xf_au_GetCellVolume())
  if ManAtomContents != "C 20 H 20 O 10":
    print "Using user input formula", ManAtomContents
    AtomContents = ManAtomContents
  
  print "Job name", Olex2SirIn
  print "Unit Cell", SirCompatCell
  print "Olex2 Symmetry:Sir Symmetry", olx.xf_au_GetCellSymm(), ':', SirCompatSymm
  print "Olex2 Formula", olx.xf_GetFormula()
  print "Sir Friendly Formula", AtomContents
  print "New formula using Z", OlexZ
  print "Number of atoms to look for", NumPeaks, 'or', float(CellV/18.0)

# There is an issue with ever decreasing returns from Olex2 and SIR.
# Basically Olex2 is updating the SFAC from SIR results this then is being posted back to if you try again
# NET result is you end up with NO ATOMS!

# Creating our SIR file
# This is primative will need to add features such as patterson on and off
  SIRINS = open("%s.sir"%(Olex2SirIn), 'w')
  SIRINS.write("%%Structure sir%s\n"%(sirversion))
  SIRINS.write("%Initialize\n")
  SIRINS.write("%Data\n")
  SIRINS.write("\tCell %s\n"%(SirCompatCell))
  SIRINS.write("\tSpaceGroup %s\n"%(SirCompatSymm))
  SIRINS.write("\tContent %s\n"%(AtomContents))
  SIRINS.write("\tReflections %s.hkl\n"%(Olex2SirIn))
  if patterson > 0:
    SIRINS.write("%Patterson\n")
    SIRINS.write("\tF**2\n")
    SIRINS.write("\tPEAKS %s\n"%(int(CellV/18.0)))
  else:
    SIRINS.write("%Continue\n%SHELX\n%END")
  SIRINS.close()
  
# All this need error control
  content = os.popen("sir%s %s.sir "%(sirversion, Olex2SirIn)).read() # This pipes our new .sir file into sir using sirversion can use 92/97 etc
  print content # Output from pipe need proper error control here
  if patterson > 0:
    SIRINS = open("%s.sir"%(Olex2SirIn), 'w')
    SIRINS.write("%%Structure sir%s\n"%(sirversion))
    SIRINS.write("%Initialize\n")
    SIRINS.write("%Data\n")
    SIRINS.write("\tCell %s\n"%(SirCompatCell))
    SIRINS.write("\tSpaceGroup %s\n"%(SirCompatSymm))
    SIRINS.write("\tContent %s\n"%(AtomContents))
    SIRINS.write("\tReflections %s.hkl\n"%(Olex2SirIn))
    SIRINS.write("%NORMAL\n")
    SIRINS.write("\tPARTIAL\n")
    SIROUT = open("%s.out"%(Olex2SirIn), 'r')
    counter = 0
    heavy = re.split("([A-Za-z]*)",AtomContents)[-2]
    print "Heavy = ", heavy
    for sirline in SIROUT:
      #print sirline
      if '  peak  height' in sirline:
        break
    for sirline in SIROUT:
      SIRINS.write("\t%s"%re.sub("^    [1-3]       [0-9]", "%s"%(heavy), sirline))
      if counter > 1:
        break
      counter = counter + 1
    SIRINS.write("%Continue\n%SHELX\n%END")
    SIRINS.close()
    content = os.popen("sir%s %s.sir "%(sirversion, Olex2SirIn)).read() # This pipes our new .sir file into sir using sirversion can use 92/97 etc
    print content # Output from pipe need proper error control here
# File generated from SIR - name controlled by the Structure line in .sir file - made sir to prevent overwrite of INS

  src = "sir%s.ins"%sirversion
  
# We are going to push our sir result into our res file
  dst = Olex2SirIn + '.res'

# This works fine in Linux not certain in windows?
  shutil.copy2(src, dst)

# Get Olex2 to reload the res file and update our display
  olx.Atreap(dst)

OV.registerFunction(OlexSir)


