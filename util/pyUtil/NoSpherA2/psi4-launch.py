import os
#import sys
import time
#import subprocess
import shutil
#from olexFunctions import OV

fchk_dir = os.getenv("fchk_dir", "")
fchk_file = os.getenv("fchk_file", "")
if not os.path.exists(fchk_dir):
  print("Incorrect launching directory!")
  time.sleep(10)
  exit(1)
os.chdir(fchk_dir)
args = os.getenv("fchk_cmd", "").split('+&-')
print("Options: '" + ' '.join(args) + "'")

basis_name = args[0]
basis_set_fn = args[1]
ncpus = int(args[2])
mult = int(args[3])
charge = int(args[4])
mem = float(args[5])
method = args[6]

sfc_name = fchk_file
out_fn = os.path.join(fchk_dir, sfc_name + "_psi4.log")
if os.path.exists(out_fn):
  shutil.move(out_fn,out_fn+"_OLD")
coordinates_fn = os.path.join(fchk_dir, fchk_file) + ".xyz"
xyz = open(coordinates_fn,"r")
#basis = open(basis_set_fn,"r")
mem_value = float(mem) * 1024

print("Reading xyz from " + str(coordinates_fn))
geom = """
nocom
noreorient
"""
geom += "%d %d\n"%(charge,mult)
atom_list = []
i = 0
for line in xyz:
  i = i+1
  if i > 2:
    atom = line.split()
    geom+=line+"\n"
    if not atom[0] in atom_list:
      atom_list.append(atom[0])
xyz.close()

print("Trying to import Psi4 now")
import psi4
print("Imported psi4")

psi4.core.set_output_file(out_fn)

psi4.geometry(geom)
print("Created molecule")

#for i in range(0,len(atom_list)):
#  atom_type = "'" +atom_list[i] + "': ["
#  inp.write(atom_type)
#  temp_atom = atom_list[i] + ":" + basis_name
#  basis.seek(0,0)
#  while True:
#    line = basis.readline()
#    if line[0] == "!":
#      continue
#    if "keys=" in line:
#      key_line = line.split(" ")
#      type = key_line[key_line.index("keys=")+2]
#    if temp_atom in line:
#      break
#  line_run = basis.readline()
#  if "{"  in line_run:
#    line_run = basis.readline()
#  while (not "}" in line_run):
#    shell_line = line_run.split()
#    if type == "turbomole=":
#      n_primitives = shell_line[0]
#      shell_type = shell_line[1]
#    elif type == "gamess-us=":
#      n_primitives = shell_line[1]
#      shell_type = shell_line[0]
#    if shell_type.upper() == "S":
#      momentum = '0'
#    elif shell_type.upper() == "P":
#      momentum = '1'
#    elif shell_type.upper() == "D":
#      momentum = '2'
#    elif shell_type.upper() == "F":
#      momentum = '3'
#    inp.write("[%s,"%momentum)
#    for n in range(0,int(n_primitives)):
#      if type == "turbomole=":
#        number1, number2 = basis.readline().replace("D","E").split()
#        inp.write("\n                (" + number1 + ', ' + number2 + "),")
#      else:
#        number1, number2, number3 = basis.readline().replace("D","E").split()
#        inp.write("\n                (" + number2 + ', ' + number3 + "),")
#    inp.write("],\n")
#    line_run = basis.readline()
#  inp.write("],\n")
#basis.close()

psi4.set_num_threads(int(ncpus))
psi4.set_memory('%s MB'%mem_value)
psi4.set_options({'scf_type': 'DF',
'dft_pruning_scheme': 'treutler',
'dft_radial_points': 20,
'dft_spherical_points': 110,
'dft_basis_tolerance': 1E-10,
'dft_density_tolerance': 1.0E-8,
'ints_tolerance': 1.0E-8,
'df_basis_scf': 'def2-universal-jkfit',
})
E, wfn = psi4.energy('%s/%s'%(method,basis_name), return_wfn=True)
psi4.fchk(wfn, os.path.join(fchk_dir, sfc_name + ".fchk"))

print("Finished")
