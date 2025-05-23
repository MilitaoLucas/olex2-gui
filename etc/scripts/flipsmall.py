#!/usr/bin/python2
import re
import os
import sys
import string
import fileinput
from os.path import join
version = "010713"
"""
=====================================================================
           Submit charge flipping phasing procedure
           -----------------------------------------

 Charge Flipping for ab initio small-molecule structure determination
          A van der Lee, C.Dumas & L. Palatinus   (python version february 08th,  2010)
          corrected bug in "forcesymmetry=yes" processing ins symcards.
          20-01-11: corrected bug for Olex2 processing
          16-03-11: added keyword 'p1' for triclinic structure solution for metrically non-triclinic lattices
          11-07-11: preparation symcards.tmp for forcesymmetry=yes completely rewritten
          26-07-11: cleanup was not done correctly in case of non-convergence
          21-02-12: global definition of guirun,implementation of aar-runs
          02-04-12: corrected bug voor aar-runs; implementation of sigma cut-off for convergence mode decision
          05-09-12: implemented mem option (only for sflipversion > 270812)
          25-10-12: better import for hkl file, some vendors attach extra lines after last record (sometimes 0 0 0)
          27-06-13: corrected bug in processing command line parameters in olex2-run
          27-06-13: slightly changed meaning of forcesymmetry and p1 keywords:
                    Forcesymmetry=yes, p1=no Superflip uses and applies the symmetry found in
                    .ins file (even if there is no symmetry, thus P1). This corresponds to derivesymmetry yes
                    Forcesymmetry=no p1=no corresponds to Superflip's derivesymmetry use; it applies
                    for the output .res file the symmetry found in the resulting electron density map
                    Forcesymmetry=yes, p1=yes is equivalent to Forcesymmetry=yes, p1=no (p1 keyword does not have effect)
                    Forcesymmetry=no p1=yes: merging is not done (only friedels), but symmetry as found in
                    electron density map is applied
          01-07-13: platon executable removed
 prepares input file for SUPERFLIP and EDMA program  (L. Palatinus)


--------------------------------------------------------------------

 Input files:
-------------
       Shelx type INS file with cell info and scattering factor types
            (space group symmetry is NOT read)
 IMPORTANT: the cell parameters should be constrained to their lattice symmetry
            with only a very small tolerance
       Shelx type HKL file with the same generic name as the INS file

 output file:
--------------
       Shelx-type RES-file with atomic coordinates and symmetry information

==================================================================
"""


def process_command_line_arg(s, flip_keywords, files):
    # help
    if (len(s) == 1) or (s[-1] == '-h') or (s[-1] == '--help'):
        sys.stdout.write("""
###############
Some guidelines
###############

""")
        if olexrun:
            sys.stdout.write("""
use: spy.flipsmall(data.ins)
 or: spy.flipsmall()  -- ins-file loaded by Olex2 is taken
 or: spy.flipsmall(data.ins maxcycles=30000)
 or: spy.flipsmall(data.ins,ked=1.1)
""")
        else:
            sys.stdout.write("""
use: %s data.ins
 or: %s data.ins  maxcycles=30000
""" % (s[0], s[0]))
        sys.stdout.write("""
where:
data.ins is input shelx-file with only cell info and scattering type info, optionally space group info

optional:
trial=5          ...... number of repeated trials (default 1)
normalize=no     ...... locally normalize the data (default yes)
maxcycl=30000    ...... maximum number of cycles per trial (default 10000)
forcesymmetry=yes...... use symmetry from shelx-file, that should obviously be present (default no)
p1=no            ...... with p1=yes the data are averaged in P1 instead of the Laue symmetry
                 ...... note: all symmetry information in the shelx file is ignored (default no)
weak=0.1         ...... fraction of reflections considered to be weak (default 0.2)
ked=1.3          ...... user-defined flip-threshold delta=ked*sigma(map) (default: delta=auto)
superposition=yes...... start with minimal superposition map (default no)
aar=no           ...... use the aar charge flipping algorithm (default no)
aarreso=1.0      ...... within the aar algorithm, the resolution limit under which reflections are considered to be missing (default=1.0)
mem=no           ...... do a map improvement using MEM (default no)
edmacontinue=no  ...... continue if convergence is not detected (default no)
comments=yes     ...... have intermediate stops to check results (default=yes)
cleanup=yes      ...... remove all intermediate files, keep only .res (default=yes)

""")
        print('Start again')
        return False

# Process command line arguments
    insfile_defined = False
    for i in range(1, len(s)):
        if ".ins" in s[i]:
            if os.path.isfile(s[i]):
                files['insin'] = s[i]
                files['base'] = os.path.splitext(files['insin'])[0]
                files['hklin'] = files['base']+".hkl"
                if not os.path.isfile(files['hklin']):
                    print("%s does not exist" % files['hklin'])
                    sys.exit(1)
                files['inflip'] = files['base']+".inflip"
                files['m81'] = files['base']+".m81"
                files['fliplog'] = files['base']+".sflog"
                insfile_defined = True
            else:
                print("%s does not exist" % s[i])
                return False

        for k, v in list(flip_keywords.items()):
            if k+"=" in s[i]:
                flip_keywords[k] = s[i].split("=")[1]

    if not insfile_defined:
        if olexrun:
            print("There should be at least the name of an existing ins-file as command line argument.\nTry again or do 'spy.flipsmall(--help)' to get help.")
        else:
            print("There should be at least the name of an existing ins-file as command line argument.\nTry again or do 'flipsmall.py --help' to get help.")
        return False

    if (flip_keywords['superposition'] == "yes"):
        flip_keywords['forcesymmetry'] = "yes"

    if (flip_keywords['aar'] == "yes"):
        flip_keywords['forcesymmetry'] = "yes"
        flip_keywords['normalize'] = "yes"

    if (flip_keywords['normalize'] == "yes"):
        flip_keywords['biso'] = 0.0
        if flip_keywords['aar'] == "no":
            flip_keywords['normalize'] = "local"
        else:
            flip_keywords['normalize'] = "atoms"

    if (flip_keywords['forcesymmetry'] == "no"):
        flip_keywords['derivesymmetry'] = "use"
    else:
        flip_keywords['derivesymmetry'] = "yes"

    if olexrun:
        flip_keywords['logging'] = "no"
        flip_keywords['comments'] = "no"

    exe['SF'] = flip_keywords['sflipversion']

#    if  ( flip_keywords['aar'] == "yes" ):
    determine_IoversigmaI()

    if (flip_keywords['logging'] == "yes"):
        log = open('/home/vdlee/unix/python/log.txt', "a")

    return True


def determine_IoversigmaI():
    sumsigma = 0.0
    sumI = 0.0
    nref = 0
    nrefneg = 0
    for line in fileinput.input(files['hklin']):
        h = line[0:4]
        k = line[4:8]
        l = line[8:12]
        try:
            ih = int(h)
            ik = int(k)
            il = int(l)
        except:  # for sure the end of the reflection data
            break
        if (ih == 0) and (ik == 0) and (il == 0):
            pass
        else:
            l2 = line[20:28]
            l1 = line[12:20]
            if l2.replace(".", "", 1).replace(" ", "").replace("-", "").isdigit() and l1.replace(".", "", 1).replace(" ", "").replace("-", "").isdigit():
                if float(l1) > 0.0:
                    nref += 1
                    sumsigma += float(line[20:28])
                    sumI += abs(float(line[12:20]))
                else:
                    nrefneg += 1
            else:
                print((l1, l2))
    fileinput.close()

    flip_keywords["isigi"] = sumI/sumsigma
    flip_keywords["nref"] = nref + nrefneg
#    exit()
    return

def process_insfile(flip_keywords, files, derived_info):
    nsymm = 0
    nsfac = 0
    derived_info['latt'] = 0
    for line in fileinput.input(files['insin']):
        if "CELL" in line:
            derived_info['cell'] = " ".join(line.split()[2:])
            derived_info['wavelength'] = line.split()[1]
        if "LATT" in line:
            derived_info['latt'] = int(line.split()[1])
        if "SYMM" in line:
            nsymm = nsymm + 1
        if "SFAC" in line:
            nsfac = nsfac + 1
        if "ZERR" in line:
            derived_info['zerr'] = line.split()[1]
            derived_info['cellesd'] = " ".join(line.split()[2:])

# Determine crystal system from lattice metrics
    c = derived_info['cell'].split()
    delta = 0.001
    derived_info["crsyst"] = "tric"
    c = list(map(float, c))
    if (abs(c[3] - 90.00)/90.00 < delta) and (abs(c[4]-90.00) / 90.00 < delta) and (abs(c[5]-90.00) / 90.00 < delta) \
        and (abs((c[0]-c[1]) / c[0]) < delta) and (abs((c[0]-c[2]) / c[0]) < delta) \
            and (abs((c[1]-c[2]) / c[0]) < delta):
        derived_info['crsyst'] = 'cubi'
        derived_info['flipcell'] = str(
            c[0])+" "+str(c[0])+" "+str(c[0])+" 90.00 90.00 90.00"
    if (abs(c[3] - 90.00)/90.00 < delta) and (abs(c[4]-90.00) / 90.00 < delta) and (abs(c[5]-90.00) / 90.00 < delta) \
        and (abs((c[0]-c[1]) / c[0]) < delta) and (abs((c[0]-c[2]) / c[0]) > delta) \
            and (abs((c[1]-c[2]) / c[0]) > delta):
        derived_info['crsyst'] = 'tetr'
        derived_info['flipcell'] = str(
            c[0])+" "+str(c[0])+" "+str(c[2])+" 90.00 90.00 90.00"
    if (abs(c[3] - 90.00)/90.00 < delta) and (abs(c[4]-90.00) / 90.00 < delta) and (abs(c[5]-90.00) / 90.00 < delta) \
        and (abs((c[0]-c[1]) / c[0]) > delta) and (abs((c[0]-c[2]) / c[0]) > delta) \
            and (abs((c[1]-c[2]) / c[0]) > delta):
        derived_info['crsyst'] = 'orth'
        derived_info['flipcell'] = str(
            c[0])+" "+str(c[1])+" "+str(c[2])+" 90.00 90.00 90.00"
    if (abs(c[3] - 90.00)/90.00 < delta) and (abs(c[4]-90.00) / 90.00 < delta) and (abs(c[5]-120.00) / 120.00 < delta) \
            and (abs((c[0]-c[1]) / c[0]) < delta):
        derived_info['crsyst'] = 'trig'
        derived_info['flipcell'] = str(
            c[0])+" "+str(c[0])+" "+str(c[2])+" 90.00 90.00 120.00"
    if (abs(c[3] - 90.00)/90.00 < delta) and (abs(c[4]-90.00) / 90.00 > delta) and (abs(c[5]-90.00) / 90.00 < delta):
        derived_info['crsyst'] = 'mono'
        derived_info['flipcell'] = str(
            c[0])+" "+str(c[1])+" "+str(c[2])+" 90.00 "+str(c[4])+" 90.00"
    if (derived_info["crsyst"] == "tric"):
        derived_info['flipcell'] = str(
            c[0])+" "+str(c[1])+" "+str(c[2])+" "+str(c[3])+" "+str(c[4])+" "+str(c[5])

# Process symmetry information from .ins-file if this is to be used and put this is temporary symcards.tmp file
    if os.path.isfile("symcards.tmp"):
        os.remove("symcards.tmp")
    if (flip_keywords['forcesymmetry'] == "yes"):
        # 27-06-2013 the following was intended to treat the case where the user had 'forgotten' to put in space
        # group information, but this is not likely to occur, so with forcesymmetry=yes alone and p1=no without
        # symmetry information the structure will be solved in p1 even if the symmetry s metrically higher
        #        if ( nsymm == 0 ) and not (derived_info["crsyst"]=="tric") and flip_keywords['p1'] == "no":
        #           print " No symmetry information available "
        #           print " Calculation continues, but forcesymmetry is set to no"
        #           flip_keywords['forcesymmetry'] = "no"
        #           if ( flip_keywords['comments'] == 'yes' ): raw_input(" Press <RETURN> to continue")
        #        else:
        symcards = open("symcards.tmp", "w")
        print("symmetry", file=symcards)
        print("x1 x2 x3", file=symcards)
        if flip_keywords['p1'] == "no":
            if (derived_info['latt'] > 0):
                print(" -x1 -x2 -x3", file=symcards)
            for line in fileinput.input(files['insin']):
                if "SYMM" in line:
                    line = line.replace("SYMM", "").upper().split(',')
                    for k in range(len(line)):
                        line[k] = line[k].replace(" ", "")
                        line[k] = line[k].replace("\n", "")
                        line[k] = line[k].replace("X", "x1")
                        line[k] = line[k].replace("Y", "x2")
                        line[k] = line[k].replace("Z", "x3")
                        if ".5" in line[k] and "0.5" not in line[k]:
                            line[k] = line[k].replace(".5", "0.5")
                        if ".25" in line[k] and "0.25" not in line[k]:
                            line[k] = line[k].replace(".25", "0.25")
                        if ".75" in line[k] and "0.75" not in line[k]:
                            line[k] = line[k].replace(".75", "0.75")
                        if ".33" in line[k] and "0.33" not in line[k]:
                            line[k] = line[k].replace(".33", "0.33")
                        if ".66" in line[k] and "0.66" not in line[k]:
                            line[k] = line[k].replace(".66", "0.66")
                        if ".83" in line[k] and "0.83" not in line[k]:
                            line[k] = line[k].replace(".83", "0.83")
                    print(" ".join(line), file=symcards)
                    if (derived_info['latt'] > 0):
                        invline = []
                        for symop in line:
                            symopinv = ""
                            for k in range(len(symop)):
                                if (k == 0 and symop[0] == "x"):
                                    symopinv = symopinv + "-x"
                                if (k == 0 and symop[0] != "x" and symop[0] != "+" and symop[0] != "-"):
                                    symopinv = symopinv + symop[k]
                                if (symop[k] == "+"):
                                    symopinv = symopinv + "-"
                                if (symop[k] == "-"):
                                    symopinv = symopinv + "+"
                                if (k > 0 and symop[k] != "-" and symop[k] != "+"):
                                    symopinv = symopinv + symop[k]
                            invline.append(symopinv)
                        print(" ".join(invline), file=symcards)
        print("endsymmetry", file=symcards)
        symcards.close()

# Build symcards.tmp from crystal system info
    if (flip_keywords['forcesymmetry'] == "no") and (flip_keywords['p1'] == "no"):
        symcards = open("symcards.tmp", "w")
        symcards.write("symmetry\nx y z\n")
        if (flip_keywords['merge'] == "yes"):
            if (derived_info['crsyst'] == 'tric'):
                symcards.write("-x -y -z\n")
                flip_keywords['SG'] = '2'
            if (derived_info['crsyst'] == 'mono'):
                symcards.write("-x y -z\n")
                flip_keywords['SG'] = '3'
            if (derived_info['crsyst'] == 'orth'):
                symcards.write("-x -y z\n-x y -z\nx -y -z\n")
                flip_keywords['SG'] = '16'
            if (derived_info['crsyst'] == 'tetr'):
                symcards.write("-x -y z\n-y x z\ny -x z\n")
                flip_keywords['SG'] = '75'
            if (derived_info['crsyst'] == 'trig'):
                symcards.write("-y x-y z\n-x+y -x z\n")
                flip_keywords['SG'] = '143'
            if (derived_info['crsyst'] == 'cubi'):
                symcards.write(
                    "-x -y z\n-x y -z\nx -y -z\nz x y\nz -x -y\n-z -x y\n-z x -y\ny z x\n-y z -x\ny -z -x\n-y -z x\n")
                flip_keywords['SG'] = '195'
        else:
            symcards.write("-x -y -z\n")
            SG = '2'
        symcards.write("endsymmetry\n")
        symcards.close()

    if (flip_keywords['forcesymmetry'] == "no") and (flip_keywords['p1'] == "yes"):
        symcards = open("symcards.tmp", "w")
        symcards.write("symmetry\nx y z\n")
        symcards.write("endsymmetry\n")
        symcards.close()
        flip_keywords['SG'] = "as in import file"

# Write lattice cards
    symcards = open("symcards.tmp", "a")
    symcards.write("centers\n0.0000 0.0000 0.0000\n")
    if (abs(derived_info['latt']) == 2):
        symcards.write("0.5000 0.5000 0.5000\n")
    if (abs(derived_info['latt']) == 3):
        symcards.write(
            "0.666666667 0.33333333 0.333333333\n0.33333333 0.666666667 0.666666667\n")
    if (abs(derived_info['latt']) == 4):
        symcards.write(
            "0.5000 0.5000 0.0000\n0.5000 0.0000 0.5000\n0.0000 0.5000 0.5000\n")
    if (abs(derived_info['latt']) == 5):
        symcards.write("0.0000 0.5000 0.5000\n")
    if (abs(derived_info['latt']) == 6):
        symcards.write("0.5000 0.0000 0.5000\n")
    if (abs(derived_info['latt']) == 7):
        symcards.write("0.5000 0.5000 0.0000\n")
    symcards.write("endcenters\n")
    symcards.close()

# sometimes there is lattice info, in that case 'missing' should be zero, the default, otherwise set to other defaults
    if (derived_info['latt'] != 0):
        if (flip_keywords['normalize'] == "no"):
            flip_keywords['missing'] = "float 0.4"
        else:
            if flip_keywords['normalize'] == "local":
                flip_keywords['missing'] = "bound 0.4 4"
            else:
                flip_keywords['missing'] = "float 1.0"

# Process SFAC info (is a bit complicated, since there are two styles in Shelx-files
# there can be two types of SFAC cards in .ins file; second character of element need to be lower-case
    if (nsfac == 1):
        for line in fileinput.input(files['insin']):
            if "SFAC" in line:
                multi = re.search('=$', line)
                sfacline = line.split()[1:]
    else:
        multi = 'yes'
    if (nsfac > 1) or (multi == 'yes'):
        sfacline = ''
        for line in fileinput.input(files['insin']):
            if "SFAC" in line:
                sfacline = sfacline+' '+line.split()[1]
        sfacline = sfacline.split()
    if (nsfac == 1) and (multi):
        del sfacline[1:]
    derived_info['sfac'] = ''
    for k in sfacline:
        if (len(k) > 1):
            derived_info['sfac'] = derived_info['sfac'] + \
                ' '+k.replace(k[1], k[1].lower())
        else:
            derived_info['sfac'] = derived_info['sfac']+' '+k
    derived_info['sfac'] = derived_info['sfac'].lstrip()
    if flip_keywords['aar'] == "yes":
        elements = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr',
                    'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr',
                    'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La',
                    'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os',
                    'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U']
        print(derived_info['sfac'])
        lst = derived_info['sfac'].split(" ")
        y = []
        for l in range(len(lst)):
            y.append(elements.index(lst[l]))
        y.sort()
        derived_info['heaviest_element'] = elements[y[-1]]



def check_executables(exe):
    for k, v in list(exe.items()):
        if (find_executable(v) == None):
            print(
                "%s executable not found, check whether it is installed and in the path." % v)
            return False
    return True


def generate_superflip_file(flip_keywords, files, derived_info):
    # Generate Superflip .inflip file and write some info to the screen
    print("""
============================================================================
!                  Ab initio Charge Flipping procedure                     !
!                      for small-molecule structures                       !
!                                                                          !
!          script written by: A. van der Lee, C. Dumas & L. Palatinus      !
!  CF and map interpretation calculations by : L. Palatinus & G. Chapuis   !
!       Palatinus, L. & Chapuis, G.(2007): J. Appl. Cryst. 40, 786-790     !
!              http://superspace.fzu.cz/superflip                         !
!                                                                          !
!                          python-script-version %s                    !
============================================================================
    """ % version)

    print("""
-------------------  Crystal data --------------------
import file              .......  %s
hkl-file                 .......  %s
unit cell parameters     .......  %s
crystal system           .......  %s
merging space group      .......  %s

----------------  CF parameters used  -----------------
flip threshold            ......  %s
weak threshold            ......  %s
Biso                      ......  %s
maximum cycles / trial    ......  %s
normalize                 ......  %s
number of trials          ......  %s
superposition             ......  %s
aar                       ......  %s
aarreso                   ......  %s
mem                       ......  %s
----------------------------------------------------

    """ % (files['insin'], files['hklin'], derived_info['flipcell'], derived_info['crsyst'], flip_keywords['SG'], flip_keywords['ked'], flip_keywords['weak'], flip_keywords['biso'],
           flip_keywords['maxcycl'], flip_keywords['normalize'], flip_keywords['trial'], flip_keywords['superposition'],
           flip_keywords['aar'], flip_keywords['aarreso'], flip_keywords['mem']))
    print("<I/sig(I)> = %s (%s reflections)" %
          (flip_keywords['isigi'], flip_keywords['nref']))
    if (flip_keywords['comments'] == 'yes'):
        input("\n Press <RETURN> to continue\n")

# Now generate inflip file
    f = open(files['inflip'], "w")
    g = open("symcards.tmp", "r")

    f.write("""
#=============================================
#   Ab initio phasing by Charge Flipping
#
#                   SUPERFLIP
#
#=============================================
title    ab initio Phasing by Charge Flipping

# Basic crystallographic information
cell             %s
""" % derived_info['flipcell'])

    f.writelines(g.readlines())

    f.write("""

voxel            AUTO
terminal         %s

# Keywords influencing the CF algorithm
weakratio        %s
biso             %s
normalize        %s
missing          %s
maxcycles        %s
repeatmode       %s

# Output density map
searchsymmetry   average
derivesymmetry   %s
outputfile       %s

# Input reflections

dataformat       %s
""" % (flip_keywords['terminal'], flip_keywords['weak'], flip_keywords['biso'], flip_keywords['normalize'],
        flip_keywords['missing'], flip_keywords['maxcycl'], flip_keywords['trial'],
        flip_keywords['derivesymmetry'], files['m81'], flip_keywords['dataformat']))

    if (flip_keywords['ked'] != "auto"):
        f.write("""

delta %s sigma

         """ % flip_keywords['ked'])

    if (flip_keywords['superposition'] == "yes"):
        f.write("""

modelfile superposition 0.05
convergencemode symmetry 60

         """)

    if (flip_keywords['aar'] == "yes"):
        if flip_keywords['isigi'] > 3.00:
            convergencemode = "convergencemode symmetry 60"
        else:
            convergencemode = "convergencemode normal 0.8"

        f.write("""

%s
perform general 0.5 1.0 1.0 0.0 0.0 0.0
resunits d
composition %s
reslimit %s
           """ % (convergencemode, derived_info["heaviest_element"], flip_keywords["aarreso"]))

    if (flip_keywords['mem'] == "yes"):

        f.write("""

mem yes
           """)

    if (flip_keywords['dataformat'] == "shelx"):
        f.write("""
fbegin           %s
endf""" % files['hklin'])

    f.close()
    g.close()


def analyze_superflip_logfile(flip_keywords, files, derived_info):
    #
    # Just a small note: in order to get a specific line number fileinpu.filelineno is used, then
    # the the first line starts with number 1; however with readlines it starts with zero.
    # In the next block the line before 'Last run from" is needed, thus the filelineno has to be
    # decremented with 2 instead of 1 (however: it depends a bit on how the lines are processed)
    #
    # Analyse the log-file
    derived_info['itlino'] = []
    if flip_keywords['mem'] == "yes":
        goback = 8
    else:
        goback = 2
    for line in fileinput.input(files['fliplog']):
        if "Last run from" in line:
            cev = fileinput.filelineno()-goback
        if "Number of successes" in line:
            nsuccess = int(line.split()[4])
        if "# Iteration #" in line:
            derived_info['itlino'].append(fileinput.filelineno()-1)
    try:
        cev
        nsuccess
    except NameError:
        # x doesn't exist, do something
        print("\n Note from Flipsmall:\n Not all required information could be found in Superflip's logfile.\n Did Superflip report a problem?")
        return False
    derived_info['itlino'].append(fileinput.filelineno()-1)
    bestresults = open(files['fliplog'], 'r').readlines()[cev].strip()
    if (bestresults[0:3] == ""):
        bestresults = open(files['fliplog'], 'r').readlines()[cev-2].strip()
    derived_info['bestrun'] = int(bestresults.split()[0])
    derived_info['spgr'] = bestresults.split()[4]
    phisym = float(bestresults.split()[3])

    if (flip_keywords['logging'] == "yes"):
        log.write("\
%12s: %12s %12s\n" % (files['base'], derived_info['spgr'], phisym))

    print("""


            =====================================================
                         ANALYSIS OF THE RESULTS
            =====================================================


    """)

# Interpret the results from the log-file
    if (phisym > 25.0) and (nsuccess == 0):
        print("")
        print("            ***  No convergence detected  ***")
        print("")
        if (flip_keywords['edmacontinue'] == "no"):
            print("              * you can try another time")
            print("")
            print(" normal exit")
            return False
        else:
            print("              * continue anyhow")
            print("")
    if (phisym < 25.0) and (nsuccess > 0):
        print("")
        print("            ***     Convergence detected  and low PhiSym ***")
        print("            ***         Structure is probably solved     ***")
        print("")
        print("                     PhiSym = %s" % abs(phisym/100.0))
        print("")
        print("            ***      Spacegroup proposed: %s ****" %
              derived_info['spgr'])
    if (phisym < 25.0) and (nsuccess == 0):
        print("")
        print("            ***  No Convergence detected  but low PhiSym ***")
        print("            ***      Structure is probably solved        ***")
        print("")
        print("                     PhiSym = %s" % abs(phisym/100.0))
        print("")
        print("            ***      Spacegroup proposed: %s ****" %
              derived_info['spgr'])
    if (phisym > 25.0) and (nsuccess > 0):
        print("")
        print("            ***    Convergence detected  but high PhiSym ***")
        print("            ***      Structure may be solved (P1?)       ***")
        print("")
        print("                     PhiSym = %s" % abs(phisym/100.0))
        print("")
        print("            ***      Spacegroup proposed: %s ****" %
              derived_info['spgr'])
    if (flip_keywords['forcesymmetry'] == 'yes'):
        print("")
        print("               Check whether Superflip's spacegroup is the same as  ")
        print("               yours in the input-file. If not,")
        print("               you may consider to use forcesymmetry=no or          ")
        print("              to use in your input (ins)file the space group       ")
        print("                          proposed by Superflip                     ")
        print("             Note that the resulting structure is possibly wrong ")
        print("")
        derived_info['spgr'] = "spacegroup from ins-file"

    if (flip_keywords['comments'] == "yes"):
        input(" Press <RETURN> to continue")
    return True


def generate_edma_file(flip_keywords, files, derived_info):
    # Create EDMA file:
    files['edmain'] = files['base']+'_edma.inflip'
    files['edmaout'] = files['base']+'_structure.ins'

    h = open(files['edmain'], "w")
    g = open("symcards.tmp", "r")
    h.write("""
#=============================================
#              Map interpretation
#
#                     EDMA
#
#=============================================
title    CF solution in %s

# Basic crystallographic information
cell             %s

""" % (derived_info['spgr'], derived_info['flipcell']))

# Process symmetry information, either the input info or that from the best run in the log-file
    if (flip_keywords['forcesymmetry'] == "yes"):
        g.seek(0)
        h.writelines(g.readlines())
    else:
        h.write("symmetry\n")
        cevcent = 0
        cevsym = 0
        for n, line in enumerate(fileinput.FileInput(files['fliplog'])):
            if (n > derived_info['itlino'][derived_info['bestrun']-1]) and (n < derived_info['itlino'][derived_info['bestrun']]):
                if ' Centering vectors' in line:
                    cevcent = n+1
                if ' Symmetry operations:' in line:
                    cevsym = n+1
        for n, line in enumerate(fileinput.FileInput(files['fliplog'])):
            if (n >= cevsym):
                if (line.strip() == ''):
                    break
                else:
                    h.write(" ".join(line.strip().split()[1:])+'\n')
        h.write("\
endsymmetry\n\
centers\n")
        if (cevcent != 0):
            for n, line in enumerate(fileinput.FileInput(files['fliplog'])):
                if (n >= cevcent) and (cevcent != 0):
                    if 'Symmetry operations' in line:
                        break
                    else:
                        a = line.split()
                        if (len(a) > 0):
                            if (a[0] == '0.333') or (a[0] == '0.667'):
                                for k in a:
                                    if (k == '0.333'):
                                        h.write('0.33333333 ')
                                    if (k == '0.667'):
                                        h.write('0.66666667 ')
                                h.write('\n')
                            else:
                                h.write(" ".join(line.strip().split()[0:])+'\n')
        else:
            h.write('0.000 0.000 0.000\n')
        h.write('endcenters\n')

    h.write("""

# EDMA-specific keywords
inputfile %s
outputbase %s
export %s
numberofatoms  0
composition %s
maxima all
fullcell no
scale fractional
plimit    1.5 sigma
centerofcharge yes
chlimit  0.25
""" % (files['m81'], files['base'], files['edmaout'], derived_info['sfac']))
    h.close()
    g.close()


def cleanup(files):
    # rename the EDMA ins-file to a res file

    nsymm = 0
    zerrfound = 0
    for line in fileinput.input(files['edmaout']):
        if "LATT" in line:
            latt = int(line.split()[1])
        if "SYMM" in line:
            nsymm = nsymm + 1
        if "ZERR" in line:
            derived_info['zerr'] = line.split()[1]
            zerrfound = 1

    if (zerrfound == 0):
        nsymm = nsymm + 1
        if (latt < 0):
            mult = 1
        else:
            mult = 2

        if (abs(latt) == 1):
            derived_info['zerr'] = str(nsymm*mult)
        if ((abs(latt) == 2) or (abs(latt) == 5) or (abs(latt) == 6) or (abs(latt) == 7)):
            derived_info['zerr'] = str(nsymm*mult*2)
        if (abs(latt) == 3):
            derived_info['zerr'] = str(nsymm*mult*3)
        if (abs(latt) == 4):
            derived_info['zerr'] = str(nsymm*mult*4)

    for line in fileinput.input(files['edmaout'], inplace=1):
        if (not "END" in line) and (not "CELL" in line):
            print(line[:-1])
        if "FVAR" in line:
            print("L.S. 4\nWGHT 0.1\nFMAP 2\nPLAN 25\nBOND")
        if "END" in line:
            print("HKLF 4\nEND")
        if "TITL" in line:
            print(
                "CELL " + derived_info['wavelength'] + " " + derived_info['cell'])
            print("ZERR " + derived_info['zerr'] +
                  " " + derived_info['cellesd'])

    if os.path.isfile(files['base']+'.res'):
        os.remove(files['base']+'.res')
    os.rename(files['edmaout'], files['base']+'.res')
    print("""

          Use %s for subsequent refinement

    """ % (files['base'] + '.res'))

    remove_files(files)
    return


def remove_files(files):
    if (flip_keywords['cleanup'] == 'yes'):
        if os.path.isfile(files['base']+'.coo'):
            os.remove(files['base']+'.coo')
        if os.path.isfile(files['m81']):
            os.remove(files['m81'])
        if os.path.isfile(files['edmain']):
            os.remove(files['edmain'])
        if os.path.isfile(files['edmaout']):
            os.remove(files['edmaout'])
        if os.path.isfile(files['inflip']):
            os.remove(files['inflip'])
        if os.path.isfile(files['fliplog']):
            os.remove(files['fliplog'])
        if os.path.isfile('symcards.tmp'):
            os.remove('symcards.tmp')
        return


def find_executable(executable, path=None):
    """Try to find 'executable' in the directories listed in 'path' (a
    string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH']).  Returns the complete filename or None if not
    found
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    extlist = ['']
    if os.name == 'os2':
        (base, ext) = os.path.splitext(executable)
        # executable files on OS/2 can have an arbitrary extension, but
        # .exe is automatically appended if no dot is present in the name
        if not ext:
            executable = executable + ".exe"
    elif sys.platform == 'win32':
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (base, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
    for ext in extlist:
        execname = executable + ext
#        print execname
        if os.path.isfile(execname):
            return execname
        else:
            for p in paths:
                f = os.path.join(p, execname)
                if os.path.isfile(f):
                    return f
    else:
        return None

def flipsmall(*args):

    if (len(args) == 1) and (not olexrun) and (not guirun):
        print("There should be at least the name of an existing ins-file as command line argument.\nTry again or do 'flipsmall.py --help' to get help.")
        return False
    args = list(args)
    helpasked = False
    for i in range(0, len(args)):
        if "-h" in args[i] or "--help" in args[i]:
            helpasked = True
    if olexrun:
        # check whether commas or spaces are used as separators, for olexrun it should be commas; replace simply all spaces by commas
        if len(args) > 1:
            temp = ','.join(args)
        else:
            if len(args) == 1:
                args[0] = args[0].replace(' ', ',')
                temp = str(args[0])
            else:
                temp = ''
#       print args
        args = temp.split(',')
        insertins = True
        for i in range(0, len(args)):
            if ".ins" in args[i]:
                insertins = False
        if not helpasked:
            if OV.FileName() == 'none' and insertins:
                print("There should be at least the name of an existing ins-file as command line argument.\nOr the .ins file should be preloaded in Olex2.\nCheck whether you have loaded a file in Olex2, probably not.\nTry again or do 'spy.flipsmall(--help)' to get help.")
                return False
            else:
                insin = OV.FileName() + '.ins'
                args.insert(0, 'flipsmall')
# take ins file which is loaded already in Olex, but if specified on the command line take that one
                if insertins:
                    args.insert(1, insin)
    if not helpasked:
        print('Starting flipsmall procedure for ' + args[1] + '.')
    q = process_command_line_arg(args, flip_keywords, files)
    if not q:
        return False
    q = check_executables(exe)
    if not q:
        return False

    process_insfile(flip_keywords, files, derived_info)
    generate_superflip_file(flip_keywords, files, derived_info)

    ################## RUN SUPERFLIP #########################################
    if not olexrun:
        status = os.system(exe['SF']+' '+files['inflip'])
    else:
        olex.m('exec ' + exe['SF']+' ' + files['inflip'])
        olex.m('waitfor process')
    ##########################################################################

    if not os.path.isfile(files['m81']):
        print("Superflip has not created an .m81 electron density file. Quitting...")
        return False
    q = analyze_superflip_logfile(flip_keywords, files, derived_info)
    if not q:
        remove_files(files)
        return False
    generate_edma_file(flip_keywords, files, derived_info)

    ###################### RUN EDMA #######################################
    if not olexrun:
        status = os.system(exe['EDMA']+' '+files['edmain'])
    else:
        olex.m('exec -q ' + exe['EDMA']+' ' + files['edmain'])
        olex.m('waitfor process')
    cleanup(files)
    if olexrun:
        olx.Atreap(files['base']+'.res')
#       olex.m('reap ' + args[1].split('.')[0] + '.res')
#       print "assemble"
        olex.m('compaq -a')
#       print OV.HasGUI()
    #######################################################################

    print('Finishing flipsmall procedure')
    print("""\n
 ========================
 Flipsmall version %s""" % version)

    return


def flip(fargs=[]):
    global guirun
    guirun = False
    if fargs[0] == "guirun":
        guirun = True
    if not olexrun:
        comlineargs = tuple(fargs)
        flipsmall(*comlineargs)
    if not guirun:
        sys.exit(0)
    else:
        return


global flip_keywords, derived_info, files, exe, olexrun
# the main keywords
flip_keywords = dict(weak=0.20, biso=2.5, maxcycl=10000, comments="yes", edmacontinue="no",
                     normalize="yes", merge="yes", forcesymmetry="no", trial="1", SG="1", missing="zero",
                     derivesymmetry="use", dataformat="shelx", cleanup="yes", terminal='yes', logging='no', superposition='no',
                     sflipversion='superflip', ked='auto', p1='no', aar='no', mem='no', isigi=0.00, aarreso=1.0, nref=0)
# calculated and extracted info, from ins-file and logfile
derived_info = dict(crsyst='tric', cell="9.0 9.0 9.0 90.0 90.0 90.0", flipcell="9.0 9.0 9.0 90.0 90.0 90.0",
                    cellesd="0.0 0.0 0.0 0.0 0.0 0.0", wavelength="0.71073", sfac="C H O N",
                    latt=1, spgr='P1', zerr='1', itlino=[], bestrun=1, heaviest_element="C")
# file names in use
files = dict(base='name', insin='name.ins', hklin='name.hkl', m81='name.m81', inflip='name.inflip',
             fliplog='name.sflog', edmain='name_edma.inflip', edmaout='name_structure.ins')
# the external executables
exe = dict(SF="~/unix/bin/superflip", EDMA="EDMA")
try:
    import olex
    import olx
    from olexFunctions import OlexFunctions
    OV = OlexFunctions()
    olexrun = True
    OV.registerFunction(flipsmall)
except:
    olexrun = False

if __name__ == "__main__":
    flip(sys.argv)

