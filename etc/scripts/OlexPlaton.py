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

def OlexPlaton(platonflag=" "):
  print "You are running flag: %s" %platonflag

  platon_result = os.popen("platon -%s %s.ins "%(platonflag, OV.FileName())).read() # This pipes our new .sir file into sir using sirversion can use 92/97 etc
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
"""
Platon functions from CMDLINE
function HelpPlaton() {
echo "usage: platon [option] [file]"
echo "PLATON is a versatile SHELX97 compatible multipurpose crystallographic tool."
echo ""
echo "Available options:"
echo " '--help' - This Help"
echo " '--documentation' - Documentation of platon (open browser)"
echo ""
echo " '-' - No data from file Read (Switch to I/O window)"
echo " '-a' - ORTEP/ADP [PLOT ADP]"
echo " '-b' - CSD-Search [CALC GEOM CSD]"
echo " '-c' - Calc Mode [CALC]"
echo " '-d' - DELABS [CALC DELABS]"
echo " '-e' - MULABS"
echo " '-f' - HFIX"
echo " '-g' - GenRes-filter [CALC GEOM SHELX]"
echo " '-h' - HKL-CALC [ASYM GENERATE]"
echo " '-i' - Patterson PLOT"
echo " '-j' - GenSPF-filter [CALC GEOM EUCLID]"
echo " '-k' - HELENA"
echo " '-l' - ASYM VIEW"
echo " '-m' - ADDSYM (MISSYM) [CALC ADDSYM]"
echo " '-n' - ADDSYM SHELX"
echo " '-o' - Menu Off"
echo " '-p' - PLUTON Mode"
echo " '-q' - SQUEEZE [CALC SQUEEZE]"
echo " '-r' - RENAME (RES)"
echo " '-s' - SYSTEM-S"
echo " '-t' - TABLE Mode [TABLE]"
echo " '-u' - Validation Mode [VALIDATION]"
echo " '-v' - SOLV Mode [CALC SOLV]"
echo " '-w' - Difference Map Plot"
echo " '-x' - Fo-Map PLOT"
echo " '-y' - SQUEEZE-Map PLOT"
echo " '-z' - WRITE IDENT"
echo " '-A' - PLATON/ANIS"
echo " '-C' - GENERATE CIF for current data set (e.g. .spf or .res)"
echo " '-F' - SILENT NQA SYSTEM-S PATH (FILTER)"
echo " '-I' - AUTOFIT 2 MOLECULES"
echo " '-K' - CALC KPI"
echo " '-L' - TWINROTMAT (INTERACTIVE)"
echo " '-M' - TWINROTMAT (FILTER MODE)"
echo " '-N' - 'ADDSYM EQUAL SHELX' MODE"
echo " '-O' - PLOT ADP (PostScript)"
echo " '-P' - Powder Pattern from Iobs"
echo " '-Q' - Powder Pattern from Icalc"
echo " '-R' - Auto Renumber and Write SHELX.res"
echo " '-S' - CIF2RES + FCF2HKL filter"
echo " '-T' - TwinRotMat"
echo " '-U' - CIF-VALIDATION (without VALIDATION DOC)"
echo " '-V' - FCF-VALIDATION (LAUE)"
echo " '-W' - FCF-VALIDATION (BIJVOET)"
echo " '-X' - Stripped SHELXS86 (Direct Methods Only) Mode"
echo " '-Y' - Native Structure Tidy (Parthe & Gelato) Mode"
"""
OV.registerFunction(OlexPlaton)
