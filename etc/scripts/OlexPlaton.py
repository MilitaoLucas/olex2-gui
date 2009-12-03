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

def OlexPlaton(platonflag="help"):
  print "You are running flag: %s"%(platonflag)

  # OS Checking
  if sys.platform[:3] == 'lin':
    # Risky but assuming that this is a debroglie version of platon
    tickornot = '-'
  elif sys.platform[:3] == 'win':
    # Windows
    tickornot = '-o -'
  elif sys.platform[:3] == 'dar':
    # Mac assuming like windows
    tickornot = '-o -'
    
  if platonflag == "help": # If no options given then we print all the possible commands out LOL
    print " 'a' - ORTEP/ADP [PLOT ADP]"
    print " 'b' - CSD-Search [CALC GEOM CSD]"
    print " 'c' - Calc Mode [CALC]"
    print " 'd' - DELABS [CALC DELABS]"
    print " 'e' - MULABS"
    print " 'f' - HFIX"
    print " 'g' - GenRes-filter [CALC GEOM SHELX]"
    print " 'h' - HKL-CALC [ASYM GENERATE]"
    print " 'i' - Patterson PLOT"
    print " 'j' - GenSPF-filter [CALC GEOM EUCLID]"
    print " 'k' - HELENA"
    print " 'l' - ASYM VIEW"
    print " 'm' - ADDSYM (MISSYM) [CALC ADDSYM]"
    print " 'n' - ADDSYM SHELX"
    print " 'o' - Menu Off"
    print " 'p' - PLUTON Mode"
    print " 'q' - SQUEEZE [CALC SQUEEZE]"
    print " 'r' - RENAME (RES)"
    print " 's' - SYSTEM-S"
    print " 't' - TABLE Mode [TABLE]"
    print " 'u' - Validation Mode [VALIDATION]"
    print " 'v' - SOLV Mode [CALC SOLV]"
    print " 'w' - Difference Map Plot"
    print " 'x' - Fo-Map PLOT"
    print " 'y' - SQUEEZE-Map PLOT"
    print " 'z' - WRITE IDENT"
    print " 'A' - PLATON/ANIS"
    print " 'C' - GENERATE CIF for current data set (e.g. .spf or .res)"
    print " 'F' - SILENT NQA SYSTEM-S PATH (FILTER)"
    print " 'I' - AUTOFIT 2 MOLECULES"
    print " 'K' - CALC KPI"
    print " 'L' - TWINROTMAT (INTERACTIVE)"
    print " 'M' - TWINROTMAT (FILTER MODE)"
    print " 'N' - 'ADDSYM EQUAL SHELX' MODE"
    print " 'O' - PLOT ADP (PostScript)"
    print " 'P' - Powder Pattern from Iobs"
    print " 'Q' - Powder Pattern from Icalc"
    print " 'R' - Auto Renumber and Write SHELX.res"
    print " 'S' - CIF2RES + FCF2HKL filter"
    print " 'T' - TwinRotMat"
    print " 'U' - CIF-VALIDATION (without VALIDATION DOC)"
    print " 'V' - FCF-VALIDATION (LAUE)"
    print " 'W' - FCF-VALIDATION (BIJVOET)"
    print " 'X' - Stripped SHELXS86 (Direct Methods Only) Mode"
    print " 'Y' - Native Structure Tidy (Parthe & Gelato) Mode"
    return

    
  platon_result = os.popen("platon %s%s %s.ins "%(tickornot, platonflag, OV.FileName())).read() # This pipes our new .sir file into sir using sirversion can use 92/97 etc
  print "Platon Said: ", platon_result
  platon_extension = platon_result.split(":")[-1].split(".")[-1].split("\n")[0]
  print "The file extension is: ", platon_extension, " filename is: ", "%s.%s"%(OV.FileName(), platon_extension)
  try:
    platon_result_file = open("%s.%s"%(OV.FileName(), platon_extension), 'r')
    print "Successfully opened file", platon_result_file
    for platon_line in platon_result_file:
      print platon_line
    platon_result_file.close()
  except IOError: 
    print "Failed to open file"
  print "You can read this file by typing edit %s"%(platon_extension)

OV.registerFunction(OlexPlaton)
