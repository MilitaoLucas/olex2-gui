import os
import sys
import shutil
import re
import sets
from numpy import *

# For Olex2
try:
  import olex
  import olx
  import olex_core
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  inOlex = 1
except:
  inOlex = -1
  pass

import subprocess
import math
from operator import itemgetter, attrgetter
import collections
from itertools import izip
from pyx import *



""" 1 Calculate powder pattern from HKL file
"""

def merge(i2Theta):
  k = itemgetter('start', 'end')
  for i, grp in itertools.groupby(i2Theta, key=k):
    lst = list(grp)
    if len(lst) > 2:
      print lst
      #item = mergepings(lst)
    else:
      item = lst[0]
    emitping(i, item)
  return


def degrees_to_radians(d):
  return d * math.pi / 180

def hklgen(cella, cellb, cellc, alpha, beta, gamma, wavelength, filename, max2theta):
  """
  Uses A. Labail hklgen code, tweaked, to generate a powder pattern
  """

  brokensym = list(olx.xf_au_GetCellSymm())
  SirCompatSymmSetting = brokensym.pop(0)
  SirCompatSymmOpps = []
  while len(brokensym) > 0:
    print brokensym
    print SirCompatSymmOpps
    if brokensym[0] == '-':
      print "true for -"
      SirCompatSymmOpps.append(" "+brokensym.pop(0))
      SirCompatSymmOpps.append(brokensym.pop(0))
      continue
    elif brokensym[0] in "a b c d n m":
      print "true for letter"
      SirCompatSymmOpps.append(" "+brokensym.pop(0))
      continue
    elif brokensym[0] in "1":
      print "true for number"
      SirCompatSymmOpps.append(brokensym.pop(0))
      continue
    elif brokensym[0] in "2 3 4 6 8 9":
      print "true for number"
      SirCompatSymmOpps.append(" "+brokensym.pop(0))
      continue
    elif brokensym[0] in "/":
      print "true for number"
      SirCompatSymmOpps.append(" "+brokensym.pop(0))
      continue
    print brokensym
    print SirCompatSymmOpps
  print ''.join(SirCompatSymmOpps)

  # Write HKL dat input
  # format is:
  # Line 1 : Title (Format 80A4)
  # Line 2 : Wavelength (Free Format)
  # Line 3 : Space group (put some blanks time to time :-)
  # Line 4 : a, b, c, alpha, beta, gamma  (Free Format)
  # Line 5 : 2-theta max (Free Format)  
  whklgen= open("%s.dat"%(filename), 'w')
  whklgen.write("Olex2 HKLGEN Input for Sample %s\r\n"%filename)
  whklgen.write("%s\r\n"%(wavelength))
  whklgen.write("%s%s\r\n"%(SirCompatSymmSetting, "".join(SirCompatSymmOpps)))
  whklgen.write("%4.4f %4.4f %4.4f %4.4f %4.4f %4.4f\r\n"%(cella, cellb, cellc, alpha, beta, gamma)) 
  whklgen.write("%s\r\n"%(max2theta))
  whklgen.close()
  
  # All this need error control
  try:
    print "Running hklgen calculation now"
    olx.Exec("hklgen %s"%filename)
    print "Finished calculation"
  except:
    print "hklgen calculation failed to run"
    return

def graph_it(filename):

  g = graph.graphxy(width=8,
                    x=graph.axis.linear(min=0, max=60),
                    y=graph.axis.linear(min=0, max=2000))
  g.plot(graph.data.file("%s.csv"%filename, x=1, y=2), [graph.style.line()])
  #g.writeEPSfile("%s"%filename)
  g.writePDFfile("%s"%filename)
  
  """
  from pyx import *
  
  g = graph.graphxy(width=8,
                    x=graph.axis.linear(min=0, max=2),
                    y=graph.axis.linear(min=0, max=2),
                    key=graph.key.key(pos="br", dist=0.1))
  g.plot([graph.data.function("x(y)=y**4", title=r"$x = y^4$"),
          graph.data.function("x(y)=y**2", title=r"$x = y^2$"),
          graph.data.function("x(y)=y", title=r"$x = y$"),
          graph.data.function("y(x)=x**2", title=r"$y = x^2$"),
          graph.data.function("y(x)=x**4", title=r"$y = x^4$")],
         [graph.style.line([color.gradient.Rainbow])])
  g.writeEPSfile("change")
  g.writePDFfile("change")
  0.710174
  """
  return

def LazyOlex(ops='0', pdf='n', wavelength=0.710174, max2theta=60):
  min2theta = 1 
  max2theta = 60
  steps = 0.01
  points = int((max2theta - min2theta) / steps)
  if inOlex > 0:
    cella = float(olx.xf_au_GetCell().split(',')[0])
    cellb = float(olx.xf_au_GetCell().split(',')[1])
    cellc = float(olx.xf_au_GetCell().split(',')[2])
    alpha = float(olx.xf_au_GetCell().split(',')[3])
    beta = float(olx.xf_au_GetCell().split(',')[4])
    gamma = float(olx.xf_au_GetCell().split(',')[5])
    ralpha = degrees_to_radians(float(olx.xf_au_GetCell().split(',')[3]))
    rbeta = degrees_to_radians(float(olx.xf_au_GetCell().split(',')[4]))
    rgamma = degrees_to_radians(float(olx.xf_au_GetCell().split(',')[5]))
    #wavelength = float(olx.xf_exptl_Radiation())
    filename = OV.FileName() #"/home/xray/olextrunk/etc/scripts/sucrose" #OV.FileName()
  else:
    # For now assuming test data but could be read from ins file. sucrose
    cella = 7.783 
    cellb = 8.7364 
    cellc = 10.9002
    ralpha = degrees_to_radians(90.00)
    rbeta = degrees_to_radians(102.984)
    rgamma = degrees_to_radians(90.00)
    #wavelength = radiation
    filename = "/home/xray/olextrunk/etc/scripts/sucrose"
  if (ops == '0'):
    print "You can: "
    print "1) Run hklgen"
    print "2) Run hkl2powder"
    return
  elif (ops == '1'):
    hklgen(cella, cellb, cellc, alpha, beta, gamma, wavelength, filename, max2theta)
    return
  elif (ops == '2'):
    print "Converting HKL to powder"
  else:
    print "That option %s is not available at the moment"%ops
    return

  print "Calculating Powder Pattern This Is Slow - Sorry"
  print "Using Wavelength: ", wavelength

  
  # Set up some variables
  iHKL = []
  i = 0

  # Read in the hkl file
  try:
    rHKL = open("%s.hkl"%filename, 'r')
    print "Openning HKL for Analysis"
  except OSError, why:
    rHKL.close()
    errors.extend(("failed to open file", str(why)))
  for line in rHKL:
    # Shelx HKL file uses 0.0 0.0 0.0 0.000 as a EOF type marker reflections below this are ignored in the refinement
    if (int(line.rstrip()[0:4]) == 0.0) and (int(line.rstrip()[4:8]) == 0.0) and (int(line.rstrip()[8:12]) == 0.0):
      #print "skip this line", i, "h ", int(line.rstrip()[0:4]), "k ", int(line.rstrip()[4:8]), "l ", int(line.rstrip()[8:12])
      i+=1
      continue
    iHKL.append({'H' : int(line.rstrip()[0:4]), 'K' : int(line.rstrip()[4:8]), 'L' : int(line.rstrip()[8:12]), 'Fsqd' : float(line.rstrip()[12:20]), 'D' : '', '2Theta' : ''})
    i+=1
  rHKL.close()
  print "Closing HKL"
  # See what we have
  #print "1st : ", iHKL[0]
  #print "last: ", iHKL[-1]
  
  # From here we are doing the maths
  dsqTop = (1 - math.cos(ralpha)**2 - math.cos(rbeta)**2 - math.cos(rgamma)**2) + (2 * math.cos(ralpha) * math.cos(rbeta) * math.cos(rgamma))
  Ast2 =((math.sin(ralpha)/cella)**2) * (1/dsqTop)
  Bst2 =((math.sin(rbeta)/cellb)**2) * (1/dsqTop)
  Cst2 =((math.sin(rgamma)/cellc)**2) * (1/dsqTop)
  twoBstCst = (2/(cellb*cellc))*((math.cos(rbeta)*math.cos(rgamma)-math.cos(ralpha))/dsqTop)
  twoAstCst = (2/(cella*cellc))*((math.cos(rgamma) * math.cos(ralpha) - math.cos(rbeta))/dsqTop)
  twoAstBst = (2/(cella*cellb))*((math.cos(rbeta)*math.cos(ralpha)-math.cos(rgamma))/dsqTop)
  i = 0
  i2Theta = []
  for i in range(len(iHKL)):
    h = iHKL[i]['H']
    k = iHKL[i]['K']
    l = iHKL[i]['L']
    d = 1.0 / (math.sqrt(h**2 * Ast2 + k**2 * Bst2 + l**2 * Cst2 + h * k * twoAstBst + k * l * twoBstCst + h * l * twoAstCst))
    twotheta = 2 *(math.degrees(math.asin((wavelength / (2 * d)))))
    iHKL[i]['D'] = d
    iHKL[i]['2Theta'] = twotheta
    #i2Theta = {twotheta : abs(iHKL[i]['Fsqd'])}
    i2Theta.append([round(twotheta, 2),abs(iHKL[i]['Fsqd'])])
    i+=1
  print "Starting Writing Out Powder File"
  ordered_list = []
  i2ThetaS = []
  i2ThetaSj = []
  i2ThetaSf = []
  sorted(iHKL, key=itemgetter('2Theta'), reverse=False)
  wFileC = open("%s.csv"%filename, 'w')
  i2ThetaS = sorted(i2Theta, key=itemgetter(0), reverse=False)
  n = 0

  for j,t in i2ThetaS:
    i2ThetaSj.append(j)
    i2ThetaSf.append(t)

  mergeDict = {}
  count = 0
  merid = []
  for Sj, Sf in izip(i2ThetaSj, i2ThetaSf):
      key = (Sj)
      try:
        # if this (row, col) location already has data, merge var1's
        mergeDict[key][0] = Sf
        #print "Current: ", mergeDict[key][0], "New", Sf, "Count: ", count
        count += 1
        merid.append(mergeDict[key][0])
        #print merid
      except KeyError:
        #print "unique"
        if count == 0:
          oldkey = key
        if count+1 == len(merid) and count > 0:
          #print "No fucking clue", key, oldkey, mean(merid), min(merid), max(merid), mergeDict[oldkey][0]
          mergeDict[oldkey][0] = mean(merid)
          oldkey = key
        count = 0
        merid = []
        mergeDict[key] = [Sf]
        merid.append(mergeDict[key][0])

  print "**************"
  #print mergeDict

  for j in range(min2theta, points):
    twotheta = j * steps
    if twotheta in mergeDict:
      newFsqd = mergeDict[twotheta][0]
      #print "match ", twotheta, newFsqd
    else:
      newFsqd = 0.0
    wFileC.write("%.2f,%4.4f\n"%
       (twotheta,
        abs(float(newFsqd))
        )
       )
    #print twotheta, newFsqd
  wFileC.close()
  print "Finished Writing Out Powder File"
  
  if (pdf == 'y') or (pdf == 'Y'):
    print "creating pdf graph"
    graph_it(filename)
    
    # Stage 1 create Lazy P input file basically an INS with ATOM instead of LABEL SFAC
    # Note allow for wavelength in the input
    # Stage 2 run lazyc
    # Stage 3 run lazyp
    # Stage 4 use Olex2 graph plotting software to plot the graph
    # Stage 5 allow reading of other powder patterns into plot
    # Done
    # Not quite as I want to also have in here routines for different powder pattern generation methods
    # Such as using Platon (both HKL and Simulated)
    # Such as using HKL
    # Such as from unit cell and/or spacegroup

if inOlex > 0:    
  OV.registerFunction(LazyOlex)
else:
  LazyOlex()
  

"""
C               L  A  Z  Y    P  U  L  V  E  R  I  X                  C DESC0004
C                    ( 1 DEC.  1977  )                                C DESC0007
C     A PROGRAMME TO CALCULATE THEORETICAL X-RAY AND NEUTRON          C DESC0010
C                DIFFRACTION POWDER PATTERNS                          C DESC0011
C A U T H O R S                                                       C DESC0015
C                                                                     C DESC0016
C        KLAUS YVON, WOLFGANG JEITSCHKO  AND  ERWIN PARTHE            C DESC0017
C                                                                     C DESC0018
C        ADDRESS                                                      C DESC0019
C        LABORATOIRE DE CRISTALLOGRAPHIE AUX RAYONS-X                 C DESC0020
C        UNIVERSITE DE GENEVE                                         C DESC0021
C        24 QUAI ERNEST ANSERMET                                      C DESC0022
C        CH 1211 GENEVA 4  SWITZERLAND                                C DESC0023
C                                                                     C DESC0024
C        TELEPHONE    (022) 21 93 55                                  C DESC0025

C D E S C R I P T I O N OF THE PROGRAMME (FOR A SUPPLEMENTARY         C DESC0029
C                  DESCRIPTION SEE J.APPL.CRYST. (1977), 10, P 73-74) C DESC0030
C                                                                     C DESC0031
C        LAZY PULVERIX CONSISTS OF TWO PROGRAMMES                     C DESC0032
C                  LAZY      DECODES THE INPUT DATA AND PREPARES      C DESC0033
C                            THE DATA FILE FOR PULVERIX ON UNIT ILU.  C DESC0034
C                  PULVERIX  READS THE INPUT FILE ON UNIT ILU AND     C DESC0035
C                            CALCULATES THE POWDER PATTERN.           C DESC0036
C                  THE PROGRAMMES USE TWO SCRATCH UNITS (ILU,ILV)     C DESC0037
C                                                                     C DESC0038
C                  THE LOGICAL UNIT NUMBERS, THE PROGRAM LIMITATIONS  C DESC0039
C                       AND THE DEFAULT OPTIONS ARE MARKED IN THE     C DESC0040
C                       BEGINNING OF THE SOURCE DECKS.                C DESC0041
C                                                                     C DESC0042
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC DESC0043
C                                                                     C DESC0044
C C A R D  SUMMARY                                                    C DESC0045
C                                                                     C DESC0046
C        GENERAL REMARKS                                              C DESC0047
C                                                                     C DESC0048
C          CALCULATIONS FOR SEVERAL STRUCTURES MAY BE DONE IN ONE RUN,C DESC0049
C        THE ORDER IN WHICH THE DATA CARDS ARE GIVEN WITHIN A SET IS  C DESC0050
C        NOT IMPORTANT. WHEN READING THE DATA CARDS, THE PROGRAMME    C DESC0051
C        IDENTIFIES THE KIND OF DATA CARD BY LABELS IN COLUMNS 1-6    C DESC0052
C         (E.G.  TITLE, CONDIT, CELL, SPCGRP ETC.)                    C DESC0053
C        ONE END CARD MUST TERMINATE EACH SET AND ONE FINISH CARD     C DESC0054
C        MUST FOLLOW THE LAST END CARD.                               C DESC0055
C                                                                     C DESC0056
C        THE FORMAT OF THE TITLE-, CELL-, LATICE-, SYMTRY-, SPCGRP-,  C DESC0057
C        ATOM-, END- AND FINISH- CARD  IS COMPATIBLE WITH THE         C DESC0058
C        CORRESPONDING FORMAT  OF THE X-RAY 76 PROGRAMME SYSTEM,      C DESC0059
C        EXCEPT SMALL DIFFERENCES IN CERTAIN PRESCRIPTIONS (SEE CELL- C DESC0060
C        AND ATOM- CARD)                                              C DESC0061
C        THE MINIMUM OF INPUT CARDS MUST CONTAIN A TITLE-, CELL-,     C DESC0062
C        SPCGRP-, ATOM-, END- AND FINISH-CARD.                        C DESC0063
C        THE SPCGRP-CARD MAY BE REPLACED BY LATICE AND SYMTRY CARDS   C DESC0064
C          AND VICE VERSA.                                            C DESC0065

"""
"""
C                                                                     C DESC0066
C                                                                     C DESC0067
C *********************                                               C DESC0068
C * T I T L E  CARD   *       TITLE                                   C DESC0069
C *********************                                               C DESC0070
C                                                                     C DESC0071
C   FORMAT(A2,A3,1X,17A4)                                             C DESC0072
C   COLS                                                              C DESC0073
C   1- 5  TITLE     PUNCH CARD LABEL *TITLE*                          C DESC0074
C   7-74  COMPND    ANY ALPHANUMERIC INFORMATION  (FOR INSTANCE THE   C DESC0075
C                   NAME OF THE SUBSTANCE)                            C DESC0076
C                                                                     C DESC0077
C *********************                                               C DESC0078
C * C O N D I T  CARD *       EXPERIMENTAL CONDITIONS                 C DESC0079
C *********************                                               C DESC0080
C                                                                     C DESC0081
C   FORMAT(3A2,4X,A4,F6.0,2F5.0,1X,A1,I2,A2,1X,A1)                    C DESC0082
C   COLS                                                              C DESC0083
C   1- 6  CONDIT    PUNCH CARD LABEL  *CONDIT*                        C DESC0084
C  11-14  SYMWL     SYMBOL FOR WAVELENGTH                             C DESC0085
C                             ADJUST TO THE LEFT OF THE FIELD.        C DESC0086
C                             EXAMPLE                                 C DESC0087
C                             CUA1 = COPPER K ALPHA1 RADIATION.       C DESC0088
C                             THE LIST OF ALLOWED SYMBOLS IS GIVEN AT C DESC0089
C                             THE END OF THIS DESCRIPTION.            C DESC0090
C                             WAVELENGTHS FOR WHICH NO SYMBOL EXIST   C DESC0091
C                             MUST BE GIVEN EXPLICITLY IN COLS 15-20. C DESC0092
C                             IF LEFT BLANK CU K ALPHA RADIATION IS   C DESC0093
C                                                     ASSUMED.        C DESC0094
C                             NEUTRON DIFFRACTION                     C DESC0095
C                             LEAVE COLUMNS 11-14 BLANK AND GIVE      C DESC0096
C                             VALUE OF WAVELENGTH IN COLUMNS 15-20.   C DESC0097
C  15-20  WL        WAVELENGTH IN ANGSTROM                            C DESC0098
C                             NEED NOT BE GIVEN IF SYMWL IS SPECIFIED C DESC0099
C  21-25  TL        LOWER THETA -LIMIT OF CALCULATION                 C DESC0100
C  26-30  TH        UPPER THETA -LIMIT OF CALCULATION                 C DESC0101
C                             IF LEFT BLANK  TL=0 AND TH=89 DEGREES.  C DESC0102
C                             FOR GUINIER CAMERAS TH IS 45 DEGREES    C DESC0103
C     32  NORM      TABULAR REPRESENTATION OF THE POWDER PATTERN.     C DESC0104
C                             BLANK   INTENSITIES NORMALIZED TO 1000  C DESC0105
C                             A       INTENSITIES NOT NORMALIZED      C DESC0106
C                             N       NO TABULAR REPRESENTATION OF    C DESC0107
C                                     THE POWDER PATTERN              C DESC0108
C  33-34  IMAGE     GRAPHIC REPRESENTATION OF THE POWDER PATTERN.     C DESC0109
C                             BLANK    NO GRAPHIC OUTPUT              C DESC0110
C                             INTEGER  GRAPHIC OUTPUT OF INTENSITIES  C DESC0111
C                                      IN STEPS OF 1/(2*INTEGER) OF   C DESC0112
C                                      THETA                          C DESC0113
C			      -1       GRAPHIC OUTPUT OF INTENSITIES  C
C				       MADE ON BENSON PLOTTER	      C
C  35-36  SYMLP     EXPERIMENTAL TECHNIQUE                            C DESC0114
C                             BLANK DEBYE-SCHERRER OR POWDER-         C DESC0115
C                                   DIFFRACTOMETER                    C DESC0116
C                             NE    NEUTRON DIFFRACTION               C DESC0117
C                             GN    GUINIER-DE WOLFF CAMERA           C DESC0118
C                             GH    GUINIER-HAEGG CAMERA              C DESC0119
C                                   THE FORMULAE FOR THE LORENTZ -    C DESC0120
C                                   POLARISATION FACTORS ARE GIVEN    C DESC0121
C                                   AT THE END OF THIS DESCRIPTION.   C DESC0122
C                              1    NO LP-FACTOR CORRECTION APPLIED   C DESC0123
C     38  IANO      CORRECTION FOR ANOMALOUS DISPERSION (X RAYS ONLY) C DESC0124
C                             BLANK   CORRECTION IS MADE              C DESC0125
C                             N       NO CORRECTION IS MADE.          C DESC0126
C								      C
C     39-47    U    ONLY IF IMAGE=-1 ABOVE. FOR CALCULATION OF THE    C
C     48-56    V    HALFWIDTHS OF THE PEAKS IN THE BENSON PLOT.	      C
C     57-65    W    HALFWIDTH=(U*(TAN(THETA))**2+V*TAN(THETA)+W.)**0.5C
C		    ENTER THESE PARAMETERS SO AS TO YIELD THE VALUE   C
C                   OF THE  HALFWIDTH IN 2THETA AND 0.01 DEGREES.     C DESC0127
C	            (TYPICAL D1A WL=1.9,U=1590,V=-4320,W=3850)	      C
C  N O T E S        IT IS RECOMMENDED TO COMPUTE ALL STRUCTURES       C DESC0128
C                   WITH NEUTRAL ATOMS. IF FORMFACTORS FOR IONIZED    C DESC0129
C                   ATOMS ARE USED THE PROGRAMME WILL NOT MAKE        C DESC0130
C                   DISPERSION CORRECTIONS.  NO DISPERSION CORREC-    C DESC0131
C                   TION WILL BE MADE FOR NEUTRON DIFFRACTION.        C DESC0132
C                                                                     C DESC0133
C                   IF NO CONDIT CARD IS GIVEN, COPPER RADIATION AND  C DESC0134
C                   DEBYE-SCHERRER TECHNIQUE IS ASSUMED, CORRECTION   C DESC0135
C                   FOR ANOMALOUS DISPERSION WILL BE MADE AND A       C DESC0136
C                   COMPLETE POWDER PATTERN WILL BE CALCULATED.       C DESC0137
C                                                                     C DESC0138
C                                                                     C DESC0139
C *********************                                               C DESC0140
C * C E L L  CARD     *       LATTICE CONSTANTS                       C DESC0141
C *********************                                               C DESC0142
C                                                                     C DESC0143
C   FORMAT(3A2,7X,3F8.0,3F9.0)                                        C DESC0144
C   COLS                                                              C DESC0145
C   1- 4  CELL      PUNCH CARD LABEL *CELL*                           C DESC0146
C  14-21  A         LATTICE PARAMETERS IN ANGSTROM AND DEGREES        C DESC0147
C  22-29  B                   CUBIC        OMIT B,C,ALPHA,BETA,GAMMA  C DESC0148
C  30-37  C                   HEXAGONAL    OMIT B,ALPHA,BETA,         C DESC0149
C                                                AND SET GAMMA=120.   C DESC0150
C                             RHOMBOHEDRAL SEE NOTE BELOW             C DESC0151
C  38-46  ALPHA               TETRAGONAL   OMIT B,ALPHA,BETA,GAMMA    C DESC0152
C  47-55  BETA                ORTHORHOMBIC OMIT ALPHA,BETA,GAMMA      C DESC0153
C  56-64  GAMMA               MONOCLINIC   OMIT ALPHA,GAMMA           C DESC0154
C                                                                     C DESC0155
C          W A R N I N G  THE PRESCRIPTIONS FOR OMITTING REDUNDANT    C DESC0156
C                    PARAMETERS MAY NOT BE COMPATIBLE WITH THE X-RAY  C DESC0157
C                    SYSTEM.                                          C DESC0158
C          N O T E   RHOMBOHEDRAL SHOULD BE CALCULATED WITH HEXAGONAL C DESC0159
C                    AXES. IF RHOMBOHEDRAL AXES ARE DESIRED THE STRUC-C DESC0160
C                    TURE MUST BE DESCRIBED IN THE TRICLINIC SYSTEM.  C DESC0161
C                                                                     C DESC0162
C *********************                                               C DESC0163
C * L A T I C E  CARD *       SYMMETRY CENTER AND BRAVAIS LATTICE     C DESC0164
C *********************                                               C DESC0165
C                                                                     C DESC0166
C                   THIS CARD MAY BE REPLACED BY A SPCGRP CARD        C DESC0167
C                                                                     C DESC0168
C   FORMAT(3A2,2X,A1,2X,A1)                                           C DESC0169
C   COLS                                                              C DESC0170
C   1- 6  LATICE    PUNCH CARD LABEL  *LATICE*                        C DESC0171
C      9  ISYMCE    CENTER OF SYMMETRY AT ORIGIN                      C DESC0172
C                             C   YES (CENTRIC)                       C DESC0173
C                             A   NO (ACENTRIC)                       C DESC0174
C                                                                     C DESC0175
C     12  SYMBR     BRAVAIS LATTICE INDICATOR                         C DESC0176
C                             P   PRIMITIVE                           C DESC0177
C                             I   BODY CENTERED                       C DESC0178
C                             R   RHOMBOHEDRAL                        C DESC0179
C                             F   FACE CENTERED                       C DESC0180
C                             A   A CENTERED                          C DESC0181
C                             B   B CENTERED                          C DESC0182
C                             C   C CENTERED                          C DESC0183
C                             BLANK   PRIMITIVE                       C DESC0184
C                                                                     C DESC0185
C   N O T E S       TRIGONAL CASE                                     C DESC0186
C                       P SPACE GROUPS   GIVE HEXAGONAL LATTICE       C DESC0187
C                                        CONSTANTS AND SET SYMBR=P    C DESC0188
C                       R SPACE GROUPS   (1) HEXAGONAL CELL           C DESC0189
C                                            SET SYMBR=R. THE PRO-    C DESC0190
C                                            GRAMME ASSUMES THE STAN- C DESC0191
C                                            DARD (OBVERSE) SETTING.  C DESC0192
C                                        (2) RHOMBOHEDRAL CELL        C DESC0193
C                                            SET SYMBR=P AND GIVE A,B C DESC0194
C                                            C AND ANGLES EXPLICITLY  C DESC0195
C                                            ON CELL CARD.            C DESC0196
C                                            (TRICLINIC DESCRIPTION)  C DESC0197
C                                                                     C DESC0198
C                   IF NO LATICE CARD IS GIVEN, A NON CENTROSYMMETRIC C DESC0199
C                   STRUCTURE AND A PRIMITIVE LATTICE IS ASSUMED.     C DESC0200
C                                                                     C DESC0201
C *********************                                               C DESC0202
C * S Y M T R Y  CARD *       EQUIVALENT POINT POSITIONS              C DESC0203
C *********************                                               C DESC0204
C                                                                     C DESC0205
C                   THESE CARDS MAY BE REPLACED BY A SPCGRP CARD      C DESC0206
C                                                                     C DESC0207
C   FORMAT(3A2,45A1)                                                  C DESC0208
C   COLS                                                              C DESC0209
C   1- 6  SYMTRY    PUNCH CARD LABEL  *SYMTRY*                        C DESC0210
C   7-51  IPOS      EQUIVALENT POSITION CODED IN VERBATIM FORM.       C DESC0211
C                             INCLUDE ONE CARD FOR EACH POSITION.     C DESC0212
C                                                                     C DESC0213
C                             RULES FOR CODING                        C DESC0214
C                             COORDINATES ARE SEPARATED BY COMMAS,    C DESC0215
C                             FRACTIONS ARE WRITTEN AS TWO INTEGERS   C DESC0216
C                                       SEPARATED BY A SLASH.         C DESC0217
C                             BLANK SPACES ARE IGNORED.               C DESC0218
C                                                                     C DESC0219
C                             EXAMPLE     SPACE GROUP P 21/C          C DESC0220
C                                 SYMTRY  X, Y, Z                     C DESC0221
C                                 SYMTRY  X,1/2-Y,1/2+Z               C DESC0222
C                                                                     C DESC0223
C     N O T E S               IF ISYMCE=C THEN ONLY ONE OF ANY TWO    C DESC0224
C                             CENTROSYMMETRIC POSITIONS NEED TO BE    C DESC0225
C                             GIVEN.  IF SYMBR= I,R,F,A,B OR C, ONLY  C DESC0226
C                             ONE OF THE POSITIONS RELATED BY CEN-    C DESC0227
C                                 TERING NEEDS TO BE GIVEN            C DESC0228
C                                                                     C DESC0229
C                             IF NO SYMTRY CARD IS GIVEN, X,Y,Z IS    C DESC0230
C                             AUTOMATICALLY ASSUMED, HOWEVER IF       C DESC0231
C                             SYMTRY  CARDS ARE GIVEN THEN THE        C DESC0232
C                             X,Y,Z POSITION MUST BE INCLUDED.        C DESC0233
C                                                                     C DESC0234
C                                                                     C DESC0235
C *********************                                               C DESC0236
C * S P C G R P  CARD *       SPACE GROUP                             C DESC0237
C *********************                                               C DESC0238
C                                                                     C DESC0239
C   FORMAT(3A2,35A1)                                                  C DESC0240
C                             THIS CARD MAY REPLACE LATICE AND SYMTRY C DESC0241
C                             CARDS.                                  C DESC0242
C   COLS                                                              C DESC0243
C   1- 6  SPCGRP    PUNCH CARD LABEL *SPCGRP*                         C DESC0244
C   8-17  IPOS      HERMANN MAUGUIN SYMBOL FOR THE SPACE GROUP.       C DESC0245
C                   ADJUST TO THE LEFT OF THE FIELD                   C DESC0246
C                                                                     C DESC0247
C                             RULES FOR CODING                        C DESC0248
C                                                                     C DESC0249
C                             SYMMETRY OPERATORS ARE SEPARATED BY A   C DESC0250
C                                 SLASH OR BY A BLANK.                C DESC0251
C                             THE BAR OPERATION IS CODED AS MINUS *-* C DESC0252
C                             SCREW AXES ARE GIVEN BY TWO INTEGERS    C DESC0253
C                                 THAT ARE NOT SEPARATED BY A BLANK.  C DESC0254
C                             EXAMPLES                                C DESC0255
C                               P B C N, P 21/C, P -3                 C DESC0256
C                                                                     C DESC0257
C                             THE LIST OF ALLOWED SYMBOLS IS GIVEN AT C DESC0258
C                             THE END OF THIS DESCRIPTION.            C DESC0259
C    W A R N I N G            FOR ALL OTHER SYMBOLS THE PROGRAMME     C DESC0260
C                             MAY GENERATE WRONG EQUIPOINTS WITHOUT   C DESC0261
C                             ERROR MESSAGES.                         C DESC0262
C                             FOR NON STANDARD SPACE GROUP SETTINGS   C DESC0263
C                             SYMTRY- AND LATICE- CARDS MUST BE USED. C DESC0264
C    N O T E S                                                        C DESC0265
C     FOR CENTROSYMMETRIC GROUPS, THE PROGRAMME ASSUMES THE SETTING   C DESC0266
C     HAVING THE CENTRE AT THE ORIGIN.                                C DESC0267
C     FOR R-SPACE GROUPS THE HEXAGONAL SETTING IS ASSUMED.            C DESC0268
C     R-SPACE GROUPS WITH  RHOMBOHEDRAL AXES MUST BE SIMULATED USING  C DESC0269
C     LATICE- AND SYMTRY-CARDS CORRESPONDING TO A TRICLINIC           C DESC0270
C     DESCRIPTION.                                                    C DESC0271
C                                                                     C DESC0272
C *********************                                               C DESC0273
C * A T O M  CARD     *       ATOM IDENTIFIER AND COORDINATES         C DESC0274
C *********************                                               C DESC0275
C                             USE ONE ATOM CARD FOR EACH ATOM IN      C DESC0276
C                             THE ASYMMETRIC UNIT.                    C DESC0277
C  FORMAT(3A2,1X,A4,A2,3F8.0,F6.0,F5.0)                               C DESC0278
C   COLS                                                              C DESC0279
C   1- 4  ATOM      PUNCH CARD LABEL  *ATOM*                          C DESC0280
C   8-11  ELEMT     SYMBOL OF ELEMENT AND IONISATION STATE            C DESC0281
C                             ADJUST TO THE LEFT OF THE FIELD.        C DESC0282
C                             EXAMPLES                                C DESC0283
C                                 CA   SYMBOL FOR CALCIUM(NEUTRAL)    C DESC0284
C                                 CA2+ SYMBOL FOR CALCIUM(IONIZED)    C DESC0285
C                             ONLY SYMBOLS LISTED IN THE TABLE FOR    C DESC0286
C                                 ATOM IDENTIFICATION AT THE END OF   C DESC0287
C                                 THIS DESCRIPTION CAN BE GIVEN.      C DESC0288
C  12-13  IDE      SEQUENCE NUMBER OR ATOM LABEL. (MAY BE LEFT BLANK) C DESC0289
C                             IT IS CONVENIENT TO NUMBER OR LABEL     C DESC0290
C                             ATOMS OF THE SAME TYPE.                 C DESC0291
C                                                                     C DESC0292
C  14-21  X        X COORDINATE                                       C DESC0293
C  22-29  Y        Y COORDINATE                                       C DESC0294
C  30-37  Z        Z COORDINATE                                       C DESC0295
C                             ONLY COORDINATES BETWEEN -1.AND+1. ARE  C DESC0296
C                                 ALLOWED                             C DESC0297
C                             FRACTIONS MAY BE GIVEN AS INTEGERS      C DESC0298
C                                 SEPARATED BY A SLASH                C DESC0299
C                             EXAMPLE                                 C DESC0300
C                                 ATOM   H    1/3     2/3    0.512    C DESC0301
C                                 IS EQUIVALENT TO                    C DESC0302
C                                 ATOM   H    .33333 .666667 0.512    C DESC0303
C  38-43  BTEMP    DEBYE-WALLER FACTOR                                C DESC0304
C                   IF LEFT BLANK  NO TEMPERATURE FACTOR CORRECTION   C DESC0305
C                   WILL BE MADE.                                     C DESC0306
C  44-48  FOCCU    OCCUPATION FACTOR                                  C DESC0307
C                   THIS FACTOR IS USUALLY 1 (=FULL OCCUPANCY OF THE  C DESC0308
C                   SITE) BUT IT MAY BE SMALLER IN DISORDERED STRUC-  C DESC0309
C                   TURES.IF LEFT BLANK FULL OCCUPANCY WILL BE ASSUMEDC DESC0310
C                                                                     C DESC0311
C   W A R N I N G   THE ATOM IDENTIFICATION  (COLS 8 - 13) OF THE     C DESC0312
C                   X-RAY SYSTEM MAY NOT BE COMPATIBLE WITH THE       C DESC0313
C                   PRESENT PRESCRIPTIONS.                            C DESC0314
C                                                                     C DESC0315
C                                                                     C DESC0316
C *********************                                               C DESC0317
C * E N D  CARD       *       TERMINATES EACH SET OF DATA CARDS       C DESC0318
C *********************                                               C DESC0319
C   COLS                                                              C DESC0320
C   1- 3  END       PUNCH CARD LABEL *END*                            C DESC0321
C                                                                     C DESC0322
C                                                                     C DESC0323
C                                                                     C DESC0324
C *********************                                               C DESC0325
C * F I N I S H CARD  *       TERMINATES THE RUN                      C DESC0326
C *********************                                               C DESC0327
C   COLS                                                              C DESC0328
C   1- 6  FINISH    PUNCH CARD LABEL *FINISH*                         C DESC0329
C                                                                     C DESC0330
C   N O T E  THIS CARD MUST COME AFTER THE LAST END CARD.             C DESC0331
C             IT INITIATES EXECUTION OF THE PROGRAMME.                C DESC0332
C                                                                     C DESC0333
C                                                                     C DESC0334
C                                                                     C DESC0335
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC DESC0336
C                                                                     C DESC0337
C L I S T  OF ALLOWED  S Y M B O L S                                  C DESC0338
C                                                                     C DESC0339
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC DESC0340
C                                                                     C DESC0341
C W A V E L E N G T H S    (VARIABLE *SYMWL* ON CONDIT CARD)          C DESC0342
C                                                                     C DESC0343
C  THE LINES CONTAIN THE SYMBOLS FOR K ALPHA1, K ALPHA2 AND           C DESC0344
C  THE WEIGHTED AVERAGE OF THE K ALPHA RADIATION FOR CHROMIUM, IRON,  C DESC0345
C  COPPER, MOLYBDENUM AND SILVER.                                     C DESC0346
C  THE WAVELENGTHS IN ANGSTROM ARE GIVEN IN PARENTHESES               C DESC0347
C                                                                     C DESC0348
C  CRA1 (2.28970)    CRA2 (2.29361)    CR (2.2909)                    C DESC0349
C  FEA1 (1.93604)    FEA2 (1.93998)    FE (1.9373)                    C DESC0350
C  CUA1 (1.54056)    CUA2 (1.54439)    CU (1.5418)                    C DESC0351
C  MOA1 (0.70930)    MOA2 (0.71359)    MO (0.7107)                    C DESC0352
C  AGA1 (0.55941)    AGA2 (0.56380)    AG (0.5608)                    C DESC0353
C                                                                     C DESC0354
C A T O M  IDENTIFICATION   (VARIABLE *ELEMT* ON ATOM CARD)           C DESC0355
C                                                                     C DESC0356
C   THE ATOM SYMBOLS ARE USED TO RETRIEVE THE SCATTERING FACTORS FOR  C DESC0357
C   X RAYS  AND THE NUCLEAR (BUT NOT THE MAGNETIC) SCATTERING FACTORS C DESC0358
C   FOR NEUTRONS.                                                     C DESC0359
C   DO  N O T  INCLUDE THE ASTERISK PRECEEDING AN ATOM SYMBOL.        C DESC0360
C   THIS ASTERISK INDICATES ATOM IDENTIFIERS THAT ARE ALLOWED FOR     C DESC0361
C   BOTH X-RAY AND NEUTRON DIFFRACTION. ALL OTHER SYMBOLS ARE         C DESC0362
C   ALLOWED FOR X-RAY DIFFRACTION ONLY.                               C DESC0363
C   ATOM SYMBOLS FOLLOWED BY A POINT HAVE A SPECIAL MEANING (SEE      C DESC0364
C   BELOW)                                                            C DESC0365
C                                                                     C DESC0366
C   IN CASE OF X RAY DIFFRACTION USE NEUTRAL ATOMS UNLESS YOU         C DESC0367
C   KNOW EXACTLY WHAT YOU WANT TO CALCULATE.                          C DESC0368
C                                                                     C DESC0369
C  *AC    *C     *DY    *HE     LU3+   NP4+  *PU     SI.    TM3+      C DESC0370
C   AC3+   C.     DY3+  *HF    *MG     NP6+   PU3+   SI4+  *U         C DESC0371
C  *AG    *CA            HF4+   MG2+          PU4+  *SM     U3+       C DESC0372
C   AG1+   CA2+  *ER    *HG    *MN    *O      PU6+   SM3+   U4+       C DESC0373
C   AG2+  *CD     ER3+   HG1+   MN2+   O1-          *SN     U6+       C DESC0374
C  *AL     CD2+  *EU     HG2+   MN3+   O2-.   RA     SN2+             C DESC0375
C   AL3+  *CE     EU2+  *HO     MN4+  *OS     RA2+   SN4+  *V         C DESC0376
C  *AM     CE3+   EU3+   HO3+  *MO     OS4+  *RB    *SR     V2+       C DESC0377
C  *AR     CE4+                 MO3+          RB1+   SR2+   V3+       C DESC0378
C  *AS     CF    *F     *I      MO5+  *P     *RE            V5+       C DESC0379
C   AT    *CL     F1-    I1-    MO6+  *PA    *RH    *TA               C DESC0380
C  *AU     CL1-  *FE    *IN           *PB     RH3+   TA5+  *W         C DESC0381
C   AU1+  *CM     FE2+   IN3+  *N      PB2+   RH4+  *TB     W6+       C DESC0382
C   AU3+  *CO     FE3+  *IR    *NA     PB4+   RN     TB3+             C DESC0383
C          CO2+   FR     IR3+   NA1+  *PD    *RU    *TC    *XE        C DESC0384
C  *B      CO3+          IR4+  *NB     PD2+   RU3+  *TE               C DESC0385
C  *BA    *CR    *GA            NB3+   PD4+   RU4+  *TH    *Y         C DESC0386
C   BA2+   CR2+   GA3+  *K      NB5+   PM            TH4+   Y3+       C DESC0387
C  *BE     CR3+  *GD     K1+   *ND     PM3+  *S     *TI    *YB        C DESC0388
C   BE2+  *CS     GD3+  *KR     ND3+   PO    *SB     TI2+   YB2+      C DESC0389
C  *BI     CS1+  *GE           *NE    *PR     SB3+   TI3+   YB3+      C DESC0390
C   BI3+  *CU     GE4+  *LA    *NI     PR3+   SB5+   TI4+             C DESC0391
C   BI5+   CU1+          LA3+   NI2+   PR4+  *SC    *TL    *ZN        C DESC0392
C   BK     CU2+  *H     *LI     NI3+  *PT     SC3+   TL1+   ZN2+      C DESC0393
C  *BR            H.     LI1+  *NP     PT2+  *SE     TL3+  *ZR        C DESC0394
C   BR1-   D.     H1-   *LU     NP3+   PT4+  *SI    *TM     ZR4+      C DESC0395
C                                                                     C DESC0396
C   SYMBOLS WITH SPECIAL MEANING                                      C DESC0397
C                                                                     C DESC0398
C   H.    HYDROGEN HF SCATTERING FACTOR                               C DESC0399
C   C.    CARBON   HF SCATTERING FACTOR                               C DESC0400
C   SI.   SILICON  HF SCATTERING FACTOR                               C DESC0401
C   D.    DEUTERIUM (FOR NEUTRON DIFFRACTION O N L Y)                 C DESC0402
C   O2-.  TAKEN FROM ACTA CRYST. VOL.19, P.486(1965).                 C DESC0403
C                                                                     C DESC0404
C                                                                     C DESC0405
C S P A C E  G R O U P  SYMBOLS  (VARIABLE *IPOS* ON SPCGRP- CARD)    C DESC0406
C                                                                     C DESC0407
C                                                                     C DESC0408
C    DO  N O T INCLUDE THE STAR  PRECEEDING SOME OF THE SYMBOLS.      C DESC0409
C    THE STAR INDICATES CENTROSYMMETRIC SPACE GROUPS WHICH HAVE       C DESC0410
C    BEEN DESCRIBED WITH SEVERAL SETTINGS. THE PROGRAMME GENERATES    C DESC0411
C    ONLY THE SETTING WITH THE CENTRE OF SYMMETRY AT THE ORIGIN OF    C DESC0412
C    THE UNIT CELL.                                                   C DESC0413
C                                                                     C DESC0414
C                                                                     C DESC0415
C   W A R N I N G     A SYMBOL THAT DOES NOT FIGURE IN THIS LIST      C DESC0416
C                       MAY YIELD WRONG EQUIPOINTS.                   C DESC0417
C                                                                     C DESC0418
C   TRICLINIC                                                         C DESC0419
C    P 1          P -1                                                C DESC0420
C                                                                     C DESC0421
C                                                                     C DESC0422
C   MONOCLINIC                                                        C DESC0423
C                                                                     C DESC0424
C    P 2          P 21         C 2          P M          P C          C DESC0425
C    C M          C C          P 2/M        P 21/M       C 2/M        C DESC0426
C    P 2/C        P 21/C       C 2/C                                  C DESC0427
C                                                                     C DESC0428
C    THE POINT POSITIONS GENERATED FROM THESE SYMBOLS CORRESPOND TO   C DESC0429
C    THE MONOCLINIC SETTING WITH B AS UNIQUE AXIS (ALPHA=GAMMA=90.)   C DESC0430
C                                                                     C DESC0431
C   ORTHORHOMBIC                                                      C DESC0432
C                                                                     C DESC0433
C    P 2 2 2      P 2 2 21     P 21 21 2    P 21 21 21   C 2 2 21     C DESC0434
C    C 2 2 2      F 2 2 2      I 2 2 2      I 21 21 21   P M M 2      C DESC0435
C    P M C 21     P C C 2      P M A 2      P C A 21     P N C 2      C DESC0436
C    P M N 21     P B A 2      P N A 21     P N N 2      C M M 2      C DESC0437
C    C M C 21     C C C 2      A M M 2      A B M 2      A M A 2      C DESC0438
C    A B A 2      F M M 2      F D D 2      I M M 2      I B A 2      C DESC0439
C    I M A 2      P M M M     *P N N N      P C C M     *P B A N      C DESC0440
C    P M M A      P N N A      P M N A      P C C A      P B A M      C DESC0441
C    P C C N      P B C M      P N N M     *P M M N      P B C N      C DESC0442
C    P B C A      P N M A      C M C M      C M C A      C M M M      C DESC0443
C    C C C M      C M M A     *C C C A      F M M M     *F D D D      C DESC0444
C    I M M M      I B A M      I B C A      I M M A                   C DESC0445
C                                                                     C DESC0446
C                                                                     C DESC0447
C   TETRAGONAL                                                        C DESC0448
C                                                                     C DESC0449
C    P 4          P 41         P 42         P 43         I 4          C DESC0450
C    I 41         P -4         I -4         P 4/M        P 42/M       C DESC0451
C   *P 4/N       *P 42/N       I 4/M       *I 41/A       P 4 2 2      C DESC0452
C    P 4 21 2     P 41 2 2     P 41 21 2    P 42 2 2     P 42 21 2    C DESC0453
C    P 43 2 2     P 43 21 2    I 4 2 2      I 41 2 2     P 4 M M      C DESC0454
C    P 4 B M      P 42 C M     P 42 N M     P 4 C C      P 4 N C      C DESC0455
C    P 42 M C     P 42 B C     I 4 M M      I 4 C M      I 41 M D     C DESC0456
C    I 41 C D     P -4 2 M     P -4 2 C     P -4 21 M    P -4 21 C    C DESC0457
C    I -4 M 2     P -4 C 2     P -4 B 2     P -4 N 2     P -4 M 2     C DESC0458
C    I -4 C 2     P -4 2 M     I -4 2 D     P 4/M M M    P 4/M C C    C DESC0459
C   *P 4/N B M   *P 4/N N C    P 4/M B M    P 4/M N C   *P 4/N M M    C DESC0460
C   *P 4/N C C    P 42/M M C   P 42/M C M  *P 42/N B C  *P 42/N N M   C DESC0461
C    P 42/M B C   P 42/M N M  *P 42/N M C  *P 42/N C M   I 4/M M M    C DESC0462
C    I 4/M C M   *I 41/A M D  *I 41/A C D                             C DESC0463
C                                                                     C DESC0464
C                                                                     C DESC0465
C   TRIGONAL                                                          C DESC0466
C                                                                     C DESC0467
C    P 3          P 31         P 32         R 3          P -3         C DESC0468
C    R -3         P 3 1 2      P 3 2 1      P 31 1 2     P 31 2 1     C DESC0469
C    P 32 1 2     P 32 2 1     R 3 2        P 3 M 1      P 3 1 M      C DESC0470
C    P 3 C 1      P 3 1 C      R 3 M        R 3 C        P -3 1 M     C DESC0471
C    P -3 1 C     P -3 M 1     P -3 C 1     R -3 M       R -3 C       C DESC0472
C                                                                     C DESC0473
C    ALL R-SPACE GROUPS REFER TO THE HEXAGONAL SETTING                C DESC0474
C                                                                     C DESC0475
C   HEXAGONAL                                                         C DESC0476
C                                                                     C DESC0477
C    P 6          P 61         P 65         P 62         P 64         C DESC0478
C    P 63         P -6         P 6/M        P 63/M       P 6 2 2      C DESC0479
C    P 61 2 2     P 65 2 2     P 62 2 2     P 64 2 2     P 63 2 2     C DESC0480
C    P 6 M M      P 6 C C      P 63 C M     P 63 M C     P -6 M 2     C DESC0481
C    P -6 C 2     P -6 2 M     P -6 2 C     P 6/M M M    P 6/M C C    C DESC0482
C    P 63/M C M   P 63/M M C                                          C DESC0483
C                                                                     C DESC0484
C                                                                     C DESC0485
C   CUBIC                                                             C DESC0486
C                                                                     C DESC0487
C    P 2 3        F 2 3        I 2 3        P 21 3       I 21 3       C DESC0488
C    P M 3       *P N 3        F M 3       *F D 3        I M 3        C DESC0489
C    P A 3        I A 3        P 4 3 2      P 42 3 2     F 4 3 2      C DESC0490
C    F 41 3 2     I 4 3 2      P 43 3 2     P 41 3 2     I 41 3 2     C DESC0491
C    P -4 3 M     F -4 3 M     I -4 3 M     P -4 3 N     F -4 3 C     C DESC0492
C    I -4 3 D     P M 3 M     *P N 3 N      P M 3 N     *P N 3 M      C DESC0493
C    F M 3 M      F M 3 C     *F D 3 M     *F D 3 C      I M 3 M      C DESC0494
C    I A 3 D                                                          C DESC0495
C                                                                     C DESC0496
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC DESC0497
C                                                                     C DESC0498
C F O R M U L A E  FOR  THE LORENTZ - POLARISATION FACTORS            C DESC0499
C                                                                     C DESC0500
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC DESC0501
C                                                                     C DESC0502
C   DEBYE-SCHERRER TECHNIQUE                                          C DESC0503
C                                                                     C DESC0504
C   L = 1./(SIN(THETA)**2*COS(THETA))                                 C DESC0505
C                                                                     C DESC0506
C   P = (1.+ COS(2*THETA)**2)/2.                                      C DESC0507
C                                                                     C DESC0508
C   GUINIER  TECHNIQUE                                                C DESC0509
C                                                                     C DESC0510
C   L = 1./(SIN(THETA)**2*COS(THETA)*COS(2*THETA-BETA))               C DESC0511
C       BETA = ANGLE BETWEEN THE NORMAL TO THE SPECIMEN AND THE       C DESC0512
C              DIRECTION OF THE INCIDENT BEAM.                        C DESC0513
C                                                                     C DESC0514
C   P = ( 1.+ COS(2*THETA)**2*COS(2*ALPHA)**2)/(1+COS(2*ALPHA)**2)    C DESC0515
C       ALPHA = DIFFRACTION ANGLE OF MONOCHROMATOR.                   C DESC0516
C                                                                     C DESC0517
C   NOTE     ALPHA AND BETA DEPEND ON THE GEOMETRY OF THE GUINIER -   C DESC0518
C            CAMERA AND THE D SPACING OF THE REFLECTING PLANES OF     C DESC0519
C            THE MONOCHROMATOR CRYSTAL. FOR GUINIER CAMERAS OTHER     C DESC0520
C            THAN GUINIER-DE WOLFF OR GUINIER-HAEGG  OR FOR MONO-     C DESC0521
C            CHROMATOR CRYSTALS OTHER THAN QUARTZ CHANGES IN THE      C DESC0522
C            PROGRAMME HAVE TO BE MADE. ( SEE  * REMARKS FOR ADAPTING C DESC0523
C            THE PROGRAMME *  IN THE SOURCE DECK OF PULVERIX.)        C DESC0524
C                                                                     C DESC0525
"""
"""
TITLE Cu3B2O6  ICSD-Data                                                      
CONDIT        2.33    0.0 35.0   2NE
TITLE         Cu15(B2O5)2(BO3)6O2 [P1 ] Behm H   38 (1982) P. 
CELL          3.353   19.665  19.627    88.77    69.71    69.24
SPCGRP P -1
ATOM   CU  1 0.00000 0.00000 0.00000 0.00000 1.00000
ATOM   CU  2 0.06710 0.03284 0.17352 0.00000 1.00000
ATOM   CU  3 0.94440 0.04031 0.56932 0.00000 1.00000
ATOM   CU  4 0.98100 0.09290 0.69999 0.00000 1.00000
ATOM   CU  5 0.09120 0.17187 0.21122 0.00000 1.00000
ATOM   CU  6 0.06420 0.21743 0.37772 0.00000 1.00000
ATOM   CU  7 0.08620 0.20253 0.55858 0.00000 1.00000
ATOM   CU  8 0.90080 0.22389 0.82850 0.00000 1.00000
ATOM   CU  9 0.89250 0.18373 0.96812 0.00000 1.00000
ATOM   CU  A 0.86920 0.30911 0.09916 0.00000 1.00000
ATOM   CU  B 0.08250 0.38819 0.35001 0.00000 1.00000
ATOM   CU  C 0.13340 0.34898 0.60150 0.00000 1.00000
ATOM   CU  D 0.13460 0.37585 0.77133 0.00000 1.00000
ATOM   CU  E 0.86250 0.44019 0.04234 0.00000 1.00000
ATOM   CU  F 0.90200 0.44300 0.21237 0.00000 1.00000
ATOM   CU  G 0.00000 0.50000 0.50000 0.00000 1.00000
ATOM   O   1 -0.0000 0.09850 0.02020 0.00000 1.00000
ATOM   O   2 0.01800 0.02060 0.90070 0.00000 1.00000
ATOM   O   3 0.95800 0.12670 0.14200 0.00000 1.00000
ATOM   O   4 0.02000 0.52350 0.05550 0.00000 1.00000
ATOM   O   5 0.18600 0.07740 0.24730 0.00000 1.00000
ATOM   O   6  0.15300 0.04430 0.46610 0.00000 1.00000
ATOM   O   7  0.85100 0.00970 0.66610 0.00000 1.00000
ATOM   O   8  0.14500 0.11140 0.59930 0.00000 1.00000
ATOM   O   9  0.04700 0.17890 0.73230 0.00000 1.00000
ATOM   O   A  0.86300 0.06220 0.79860 0.00000 1.00000
ATOM   O   B  0.02200 0.26760 0.17970 0.00000 1.00000
ATOM   O   C  0.18700 0.22880 0.27810 0.00000 1.00000
ATOM   O   D  0.08000 0.11280 0.36690 0.00000 1.00000
ATOM   O   E  0.00300 0.17490 0.47040 0.00000 1.00000
ATOM   O   F  0.17400 0.29980 0.39780 0.00000 1.00000
ATOM   O   G  0.00500 0.30920 0.52690 0.00000 1.00000
ATOM   O   H  0.21200 0.25040 0.63200 0.00000 1.00000
ATOM   O   I  0.78800 0.15050 0.88850 0.00000 1.00000
ATOM   O   K  0.98800 0.29330 0.75940 0.00000 1.00000
ATOM   O   L  0.83800 0.26950 0.91930 0.00000 1.00000
ATOM   O   M  0.00400 0.21110 0.05160 0.00000 1.00000
ATOM   O   N  0.79400 0.35420 0.00920 0.00000 1.00000
ATOM   O   O  0.74200 0.40780 0.13660 0.00000 1.00000
ATOM   O   P  0.95900 0.35820 0.26790 0.00000 1.00000
ATOM   O   Q  0.00100 0.47640 0.30750 0.00000 1.00000
ATOM   O   R  0.06100 0.40970 0.45030 0.00000 1.00000
ATOM   O   S  0.27200 0.39270 0.67390 0.00000 1.00000
ATOM   O   T  0.04300 0.45300 0.58600 0.00000 1.00000
ATOM   O   U  0.99800 0.37290 0.88170 0.00000 1.00000
ATOM   O   V  0.22900 0.45620 0.81260 0.00000 1.00000
ATOM   B   1  0.99500 0.14420 0.07370 0.00000 1.00000
ATOM   B   2  0.05400 0.28960 0.24210 0.00000 1.00000
ATOM   B   3  0.13400 0.05740 0.31540 0.00000 1.00000
ATOM   B   4  0.07300 0.10880 0.43880 0.00000 1.00000
ATOM   B   5  0.07500 0.33970 0.46420 0.00000 1.00000
ATOM   B   6  0.09200 0.24050 0.70380 0.00000 1.00000
ATOM   B   7  0.89600 0.08000 0.86240 0.00000 1.00000
ATOM   B   8  0.88200 0.33110 0.94030 0.00000 1.00000
ATOM   B   9  0.10200 0.46170 0.65070 0.00000 1.00000
ATOM   B   A  0.07900 0.43940 0.88180 0.00000 1.00000
END
FINISH
"""

