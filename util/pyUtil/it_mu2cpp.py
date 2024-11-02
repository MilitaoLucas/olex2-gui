import os
"""
from cctbx.eltbx import tiny_pse
print("element_map = {")
for t in tiny_pse.table_iterator():
  print("'%s': '%s'," %(t.name(), t.symbol()))
print("}")
"""
element_map = {
'hydrogen': 'H','deuterium': 'D','helium': 'He','lithium': 'Li','beryllium': 'Be','boron': 'B','carbon': 'C',
'nitrogen': 'N','oxygen': 'O','fluorine': 'F','neon': 'Ne','sodium': 'Na','magnesium': 'Mg','aluminium': 'Al',
'silicon': 'Si','phosphorus': 'P','sulphur': 'S','chlorine': 'Cl','argon': 'Ar','potassium': 'K','calcium': 'Ca',
'scandium': 'Sc','titanium': 'Ti','vanadium': 'V','chromium': 'Cr','manganese': 'Mn','iron': 'Fe','cobalt': 'Co',
'nickel': 'Ni','copper': 'Cu','zinc': 'Zn','gallium': 'Ga','germanium': 'Ge','arsenic': 'As','selenium': 'Se',
'bromine': 'Br','krypton': 'Kr','rubidium': 'Rb','strontium': 'Sr','yttrium': 'Y','zirconium': 'Zr','niobium': 'Nb',
'molybdenum': 'Mo','technetium': 'Tc','ruthenium': 'Ru','rhodium': 'Rh','palladium': 'Pd','silver': 'Ag','cadmium': 'Cd',
'indium': 'In','tin': 'Sn','antimony': 'Sb','tellurium': 'Te','iodine': 'I','xenon': 'Xe','caesium': 'Cs','barium': 'Ba',
'lanthanum': 'La','cerium': 'Ce','praseodymium': 'Pr','neodymium': 'Nd','promethium': 'Pm','samarium': 'Sm','europium': 'Eu',
'gadolinium': 'Gd','terbium': 'Tb','dysprosium': 'Dy','holmium': 'Ho','erbium': 'Er','thulium': 'Tm','ytterbium': 'Yb',
'lutetium': 'Lu','hafnium': 'Hf','tantalum': 'Ta','tungsten': 'W','rhenium': 'Re','osmium': 'Os','iridium': 'Ir',
'platinum': 'Pt','gold': 'Au','mercury': 'Hg','thallium': 'Tl','lead': 'Pb','bismuth': 'Bi','polonium': 'Po',
'astatine': 'At','radon': 'Rn','francium': 'Fr','radium': 'Ra','actinium': 'Ac','thorium': 'Th','protactinium': 'Pa',
'uranium': 'U','neptunium': 'Np','plutonium': 'Pu','americium': 'Am','curium': 'Cm','berkelium': 'Bk',
'californium': 'Cf','einsteinium': 'Es','fermium': 'Fm','mendelevium': 'Md','nobelium': 'No','lawrencium': 'Lr',
}
elm_data = {}
energy = []
def read_it():
  r_lines = 0
  with open("d:/devel/tmp/IT-4.2.4.2.txt", "r") as inp:
    lines = inp.readlines()
    elm_idx = {}
    i = -1
    while i < len(lines):
      i += 1
      if i >= len(lines):
        break
      toks = lines[i].strip().split('\t')
      if not toks:
        break
      if toks[0] == "Radiation":
        r_lines += 1
        i += 1
        for j, elm in enumerate(lines[i].strip().split('\t')):
          elm_data[elm] = []
          elm_idx[j] = elm
        continue
      if r_lines ==1:
        energy.append(float(toks[1]))
      for ti, t in enumerate(toks[2:]):
        elm_data[elm_idx[ti]].append(float(t))

nist_data = {}
def read_nist():
  nist_folder = r"D:\devel\svn\olex2-sf\Data\x-ray mass attenuation coefficients"
  for n,e in element_map.items():
    nist_file = os.path.join(nist_folder, e + ".txt")
    if not os.path.exists(nist_file):
      continue
    elm_data = []
    nist_data[e] = elm_data

    with open(nist_file, "r") as inp:
      lines = inp.readlines()
      for l in lines:
        l = l.strip()
        if not l:
          break
        toks = l.split()
        start = 1 if len(toks) == 4 else 0
        elm_data.append((float(toks[start]), float(toks[start+1])))

read_it()
read_nist()
#merge
all_data = {}
def merge_all():
  for it_e, it_d in elm_data.items():
    if it_e == "Sulfur":
      it_e = "Sulphur"
    e = element_map[it_e.lower()]
    it_data = []
    all_data[e] = it_data
    for i, v in enumerate(it_d):
      it_data.append((energy[i], v))
    if e in nist_data:
      it_data += nist_data[e]
    it_data.sort(key=lambda x: x[0])

merge_all()

#print(all_data['Pu'])
header =\
"""
/******************************************************************************
* Copyright (c) 2004-2024 O. Dolomanov, OlexSys                               *
*                                                                             *
* This file is part of the OlexSys Development Framework.                     *
*                                                                             *
* This source file is distributed under the terms of the licence located in   *
* the root folder.                                                            *
******************************************************************************/"""
header_cont = []
cpp_cont = []
data_files = {}
for e, data in all_data.items():
  header_cont.append("extern const cm_Absorption_Coefficient _cm_absorpc_%s[];" %e)
  cpp_cont.append('  entries.Add("%s", _cm_absorpc_%s);' %(e, e))
  data_file = ['#include "../absorpc.h"']
  data_file.append('const cm_Absorption_Coefficient XlibObject(_cm_absorpc_%s)[] = {' %(e))
  for v in data:
    data_file.append("  {%.3e, %.3g}," %(v))

  data_file.append("  {0, 0}")
  data_file.append("};")
  data_files[e] = data_file

out_dir = "d:/devel/tmp/absorption"
for e, fdata in data_files.items():
  data_file_name = os.path.join(out_dir, "absorpc_" + e + ".cpp")
  with open(data_file_name, "w") as out:
    out.write(header + "\n")
    out.write('\n'.join(fdata))
cpp_file_name = os.path.join(out_dir, "cpp.cpp")
with open(cpp_file_name, "w") as out:
  out.writelines('\n'.join(cpp_cont))

hpp_file_name = os.path.join(out_dir, "cpp.hpp")
with open(hpp_file_name, "w") as out:
  out.write('\n'.join(header_cont))
