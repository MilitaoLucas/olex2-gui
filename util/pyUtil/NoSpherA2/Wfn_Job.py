import os
import sys
import olex
import olx
import olex_core
import gui
import shutil
import time
import math

import subprocess

from olexFunctions import OV
from utilities import run_with_bitmap

try:
  from_outside = False
  p_path = os.path.dirname(os.path.abspath(__file__))
except:
  from_outside = True
  p_path = os.path.dirname(os.path.abspath("__file__"))

class wfn_Job(object):
  origin_folder = " "
  is_copied_back = False
  date = None
  input_fn = None
  log_fn = None
  fchk_fn = None
  completed = None
  full_dir = None
  exe_fn = None
  oftware = None

  def __init__(self, parent, name, _dir, software=None):
    self.parent = parent
    self.status = 0
    self.name = name
    full_dir = '.'
    self.full_dir = full_dir
    if _dir != '':
      self.full_dir = _dir
      full_dir = _dir
    self.software = software

    if not os.path.exists(full_dir):
      return
    self.date = os.path.getctime(full_dir)
    self.log_fn = os.path.join(full_dir, name) + ".log"
    self.fchk_fn = os.path.join(full_dir, name) + ".fchk"
    self.completed = os.path.exists(self.fchk_fn)

    try:
      os.mkdir(self.full_dir)
    except:
      pass
    tries = 0
    while not os.path.exists(self.full_dir) and tries < 5:
      try:
        os.mkdir(self.full_dir)
        break
      except:
        time.sleep(0.1)
        tries += 1
        pass
    time.sleep(0.1)
    self.origin_folder = OV.FilePath()

  def write_xyz_file(self):
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    olx.Kill("$Q")
    olx.File(coordinates_fn,p=10)
    
  def write_input(self, xyz=True, basis=None, method=None, relativistic=None, charge=None, mult=None, strategy=None, conv=None, part=None, damp=None):
    if self.software == "ORCA":
      self.write_orca_input(xyz, basis, method, relativistic, charge, mult, strategy, conv, part)
    elif self.software == "ORCA 5.0" or self.software == "ORCA 6.0":
      embedding = OV.GetParam('snum.NoSpherA2.ORCA_USE_CRYSTAL_QMMM')
      if embedding == True:
        self.write_orca_crystal_input(xyz)
      else:
        self.write_orca_input(xyz, basis, method, relativistic, charge, mult, strategy, conv, part)
    elif self.software == "Gaussian03" or self.software == "Gaussian09" or self.software == "Gaussian16":
      self.write_gX_input(xyz, basis, method, relativistic, charge, mult, part)
    elif self.software == "pySCF":
      self.write_pyscf_script(xyz, basis, method, relativistic, charge, mult, damp, part)
    elif self.software == "ELMOdb":
      self.write_elmodb_input(xyz)
    elif self.software == "Psi4":
      self.write_psi4_input(xyz)
    elif self.software == "Thakkar IAM" or self.software == "SALTED":
      self.write_xyz_file()
    elif self.software == "xTB":
      if xyz == True:
        self.write_xyz_file()
    elif self.software == "pTB":
      if xyz == True:
        self.write_xyz_file()

  def write_elmodb_input(self,xyz):
    if xyz:
      self.write_xyz_file()
    self.input_fn = os.path.join(self.full_dir, self.name) + ".inp"
    inp = open(self.input_fn,"w")
    basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    elmodb_libs = None
    if sys.platform[:3] == "win":
      temp = self.parent.elmodb_lib
      drive = temp[0].lower()
      folder = temp[2:]
      elmodb_libs = "/mnt/"+drive+folder.replace('\\' , r'/')
    else:
      elmodb_libs = self.parent.elmodb_lib
    inp.write(" $INPUT_METHOD" +  '\n' + "   job_title='"  + self.name + "'" + '\n' + "   iprint_level=0" + '\n')
    inp.write("   basis_set='"  + basis_name + "'" + '\n' +  "   xyz=.true." + '\n' +  "   wfx=.true." + '\n')
    inp.write("   lib_path='" + elmodb_libs + "'" + '\n')
    inp.write("   bset_path='" + elmodb_libs + "'" + '\n')
    inp.write(" $END" + '\n')
    inp.write(" " + '\n')
    inp.write(" $INPUT_STRUCTURE" +  '\n' + "   pdb_file='"  + self.name + ".pdb'" '\n' + "   xyz_file='"  + self.name + ".xyz'" + '\n')
    charge = OV.GetParam('snum.NoSpherA2.charge')
    if charge != '0':
      inp.write("   icharge=" + charge + '\n')
    ssbond = OV.GetParam('snum.NoSpherA2.ELMOdb.ssbond')
    if ssbond == True:
      nssbond = OV.GetParam('snum.NoSpherA2.ELMOdb.nssbond')
      inp.write("   nssbond=" + nssbond + '\n')
    cycl = OV.GetParam('snum.NoSpherA2.ELMOdb.cycl')
    if cycl == True:
      ncycl = OV.GetParam('snum.NoSpherA2.ELMOdb.ncycl')
      inp.write("   ncycl=" + ncycl + '\n')
    tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
    if tail == True:
      maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
      inp.write("   ntail=" + str(maxtail) + '\n')
      resnames = OV.GetParam('snum.NoSpherA2.ELMOdb.str_resname')
      resnames = resnames.split(';')
      nat = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nat')
      nat = nat.split(';')
      nfrag = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nfrag')
      nfrag = nfrag.split(';')
      ncltd = OV.GetParam('snum.NoSpherA2.ELMOdb.str_ncltd')
      ncltd = ncltd.split(';')
      specac = OV.GetParam('snum.NoSpherA2.ELMOdb.str_specac')
      specac = specac.split(';')
      exbsinp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_exbsinp')
      exbsinp = exbsinp.split(';')
      fraginp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_fraginp')
      fraginp = fraginp.split(';')
      if int(max(nfrag)) > 50:
        inp.write("   max_frtail=" + str(max(nfrag)) + '\n')
      if int(max(nat)) > 50:
        inp.write("   max_atail=" + str(max(nat)) + '\n')
    spect = OV.GetParam('snum.NoSpherA2.ELMOdb.spect')
    nspect = OV.GetParam('snum.NoSpherA2.ELMOdb.nspect')
    if spect == True:
      inp.write("   nspec=" + str(nspect) + '\n')
    inp.write(" $END" + '\n')
    inp.write(" " + '\n')

    if tail == True:
      # use default values if lists are too short
      if len(resnames) < maxtail:
        diff = maxtail - len(resnames)
        for i in range(diff):
          resnames.append('???')
      if len(nat) < maxtail:
        diff = maxtail - len(nat)
        for i in range(diff):
          nat.append('0')
      if len(nfrag) < maxtail:
        diff = maxtail - len(nfrag)
        for i in range(diff):
          nfrag.append('1')
      if len(ncltd) < maxtail:
        diff = maxtail - len(ncltd)
        for i in range(diff):
          ncltd.append(False)
      if len(specac) < maxtail:
        diff = maxtail - len(specac)
        for i in range(diff):
          specac.append(False)
      if len(exbsinp) < maxtail:
        diff = maxtail - len(exbsinp)
        for i in range(diff):
          exbsinp.append('')
      if len(fraginp) < maxtail:
        diff = maxtail - len(fraginp)
        for i in range(diff):
          fraginp.append('0')

      for i in range(0,maxtail):
        control = ""
        control = control + str(resnames[i])  + ' ' + str(nat[i]) + ' ' + str(nfrag[i]) + ' '
        if specac[i] == "True":
          control += ".t. "
        else:
          control += ".f. "
        if ncltd[i] == "True":
          control += ".t. "
        else:
          control += ".f. "
        inp.write('  ' + control + '\n' + ' ' + '\n' )
        if nat[i] != "0":
          inp.write( str(exbsinp[i]) + ' ' + '\n')
        inp.write(" " + '\n' + str(fraginp[i])+ '\n' + ' ' + '\n')
      if spect == True:
        inp.write(" " + '\n' + OV.GetParam('snum.NoSpherA2.ELMOdb.specinp') + '\n' + ' ' + '\n')
      if basis_name == "extrabasis":
        if os.path.exists(os.path.join(self.origin_folder,"extrabasis")):
          shutil.copy(os.path.join(self.origin_folder,"extrabasis"),os.path.join(self.full_dir,"extrabasis"))
        else:
          OV.SetVar('NoSpherA2-Error',"ELMOdb")
          raise NameError('No extrabasis file available!')
    if ssbond == True:
      inp.write(" " + '\n' + OV.GetParam('snum.NoSpherA2.ELMOdb.ssbondinp') + '\n' + ' ' + '\n')
    if cycl == True:
      inp.write(" " + '\n' + OV.GetParam('snum.NoSpherA2.ELMOdb.cyclinp') + '\n' + ' ' + '\n')
    inp.close()


  def write_gX_input(self,xyz,basis_name=None,method=None,relativistic=None,charge=None,mult=None,part=None):
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    if xyz:
      self.write_xyz_file()
    xyz = open(coordinates_fn,"r")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".com"
    com = open(self.input_fn,"w")
    if basis_name == None:
      basis_name = OV.GetParam("snum.NoSpherA2.basis_name")
    basis_set_fn = os.path.join(self.parent.basis_dir,OV.GetParam("snum.NoSpherA2.basis_name"))
    basis = open(basis_set_fn,"r")
    chk_destination = "%chk=./" + self.name + ".chk"
    if OV.GetParam('snum.NoSpherA2.ncpus') != '1':
      cpu = "%nproc=" + OV.GetParam('snum.NoSpherA2.ncpus')
    else:
      cpu = "%nproc=1"
    mem = "%mem=" + OV.GetParam('snum.NoSpherA2.mem') + "GB"
    control = "# "
    if method == None:
      method = OV.GetParam('snum.NoSpherA2.method')
    if method == "HF":
      control += "rhf"
      method = "RHF"
    else:
      if method == "PBE":
        control += "PBEPBE"
      else:
        control += method
    control += "/gen NoSymm 6D 10F IOp(3/32=2) formcheck output=wfx"
    if method == "BP86" or method == "PBE":
      control += " DensityFit "
    if relativistic == None:
      relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
    if relativistic == True:
      control = control + " Integral=DKH2"
    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
    run = None
    if Full_HAR == True:
      run = OV.GetVar('Run_number')
      if run > 1:
        control += " Guess=Read"
    com.write(chk_destination + '\n')
    com.write(cpu + '\n')
    com.write(mem + '\n')
    com.write(control + '\n')
    com.write(" \n")
    title = "Wavefunction calculation for " + self.name + " on a level of theory of " + method + "/" + basis_name
    com.write(title + '\n')
    com.write(" " + '\n')
    if charge == None:
      charge = OV.GetParam('snum.NoSpherA2.charge')
    if mult == None:
      mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    com.write(charge + " " + mult + '\n')
    atom_list = []
    i = 0
    for line in xyz:
      i = i+1
      if i > 2:
        atom = line.split()
        if atom[0] == "D":
          atom[0] = "H"
          line = line.replace("D", "H")
        if atom[0] == "T":
          atom[0] = "H"
          line = line.replace("T", "H")
        com.write(line)
        if not atom[0] in atom_list:
          atom_list.append(atom[0])
    xyz.close()
    com.write(" \n")
    for i in range(0, len(atom_list)):
      atom_type = atom_list[i] + " 0\n"
      com.write(atom_type)
      temp_atom = atom_list[i] + ":" + basis_name
      basis.seek(0,0)
      while True:
        line = basis.readline()
        if not line:
          raise RecursionError("Atom not found in the basis set!")
        if line[0] == "!":
          continue
        if "keys=" in line:
          key_line = line.split(" ")
          type = key_line[key_line.index("keys=")+2]
        if temp_atom in line:
          break
      line_run = basis.readline()
      if "{"  in line_run:
        line_run = basis.readline()
      while (not "}" in line_run):
        shell_line = line_run.split()
        if type == "turbomole=":
          n_primitives = shell_line[0]
          shell_type = shell_line[1]
        elif type == "gamess-us=":
          n_primitives = shell_line[1]
          shell_type = shell_line[0]
        shell_gaussian = "   " + shell_type.upper() + " " + n_primitives + " 1.0\n"
        com.write(shell_gaussian)
        for n in range(0,int(n_primitives)):
          if type == "turbomole=":
            com.write(basis.readline())
          else:
            temp_line = basis.readline()
            temp = temp_line.split()
            com.write(temp[1] + " " + temp[2] + '\n')
        line_run = basis.readline()
      com.write("****\n")
    basis.close()
    com.write(" \n./%s.wfx\n\n" %self.name)
    com.close()

  def write_grids_4(self, method, grid):
    res = ""
    if method == "M062X":
      if grid == "Normal":
        res += "Grid6 "
      elif grid == "Low":
        res += "Grid5 "
      elif grid == "High":
        res += "Grid7 "
      elif grid == "Max":
        res += "Grid7 "
    else:
      if grid == "Low":
        res += "Grid1 "
      elif grid == "High":
        res += "Grid4 "
      elif grid == "Max":
        res += "Grid7 "
    if method == "BP86" or method == "PBE" or method == "PWLDA":
      return res
    else:
      if grid == "Normal":
        res += " NoFinalGridX "
      elif grid == "Low":
        res += " GridX2 NoFinalGridX "
      elif grid == "High":
        res += " GridX5 NoFinalGridX "
      elif grid == "Max":
        res += " GridX9 NoFinalGridX "
      return res

  def write_grids_5(self, method, grid):
    res = ""
    if method == "M062X":
      if grid == "Normal":
        res += "DefGrid3 "
      elif grid == "Low":
        res += "DefGrid2 "
      elif grid == "High":
        res += "DefGrid3 "
      elif grid == "Max":
        res += "DefGrid3 "
    else:
      if grid == "Low":
        res += "DefGrid1 "
      elif grid == "High":
        res += "DefGrid2 "
      elif grid == "Max":
        res += "DefGrid3 "
    if method == "BP86" or method == "PBE" or method == "PWLDA":
      return res
    else:
      res += " NoFinalGridX "
      return res

  def write_orca_crystal_input(self,xyz):
    known_charges = {
      "Ca": 2.0,
      "F": -1.0,
      "Na": 1.0,
      "Cl": -1.0,
      "Mg": 2.0,
      "Br": -1.0,
      "K": 1.0,
      "Li": 1.0,
      "Be": 2.0,
      "O": -2.0
    }
    coordinates_fn1 = os.path.join(self.full_dir, "asu") + ".xyz"
    charge = OV.GetParam('snum.NoSpherA2.charge')
    mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    olx.Kill("$Q")
    if xyz:
      olx.File(coordinates_fn1, p=10)
    xyz1 = open(coordinates_fn1, "r")
    coordinates_fn2 = os.path.join(self.full_dir, self.name) + ".xyz"
    radius = OV.GetParam("snum.NoSpherA2.ORCA_CRYSTAL_QMMM_RADIUS")
    olex.m("XYZCluster_4NoSpherA2 %s"%radius)
    shutil.move(self.name + ".xyz", os.path.join(self.full_dir, self.name) + ".xyz")
    xyz2 = open(coordinates_fn2,"r")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".inp"
    inp = open(self.input_fn,"w")
    basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
    if OV.GetParam('snum.NoSpherA2.ncpus') != '1':
      cpu = "nprocs " + ncpus
    else:
      cpu = "nprocs 1"
    mem = OV.GetParam('snum.NoSpherA2.mem')
    mem_value = float(mem) * 1024 / int(ncpus)
    mem = "%maxcore " + str(mem_value)
    qmmmtype = OV.GetParam("snum.NoSpherA2.ORCA_CRYSTAL_QMMM_TYPE")
    control = "! NoPop MiniPrint 3-21G "
    ECP = False
    if "ECP" in basis_name:
      ECP = True
    if ECP == False:
      control += " 3-21G "
    else:
      control += basis_name.replace("ECP-", "") + ' '

    if qmmmtype == "Mol":
      control += "MOL-CRYSTAL-QMMM "
    else:
      control += "IONIC-CRYSTAL-QMMM "
    method = OV.GetParam('snum.NoSpherA2.method')
    grid = OV.GetParam('snum.NoSpherA2.becke_accuracy')
    mp2_block = ""
    if method == "HF":
      control += "rhf "
      grids = ""
    else:
      if mult != 1 and OV.GetParam("snum.NoSpherA2.ORCA_FORCE_ROKS") == True:
        control += " ROKS "
      SCNL = OV.GetParam('snum.NoSpherA2.ORCA_SCNL')
      if SCNL == True:
        if method != "wB97X":
          control += method + ' SCNL '
        else:
          control += method + '-V SCNL '
      else:
        if method == "DSD-BLYP":
          control += method + ' D3BJ def2-TZVPP/C '
          mp2_block += "%mp2 Density relaxed RI true end"
        else:
          control += method + ' '
      software = OV.GetParam("snum.NoSpherA2.source")
      if software == "ORCA 5.0" or software == "ORCA 6.0":
        grids = self.write_grids_5(method, grid)
      else:
        print("MOL-CRYSTAL-QMMM only works from ORCA 5.0 upwards")
    convergence = OV.GetParam('snum.NoSpherA2.ORCA_SCF_Conv')
    if convergence == "NoSpherA2SCF":
      conv = " LooseSCF"
    else:
      conv = convergence
    control += grids + ' ' + conv + ' ' + OV.GetParam('snum.NoSpherA2.ORCA_SCF_Strategy')
    relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
    if relativistic == True:
      control += " DKH2 SARC/J RIJCOSX"
    else:
      control += " def2/J RIJCOSX"
    Solvation = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
    if Solvation != "Vacuum" and Solvation != None:
      control += " CPCM("+Solvation+") "
    inp.write(control + '\n' + "%pal\n" + cpu + '\n' + "end\n" + mem + '\n' + "%coords\n        CTyp xyz\n        charge " + charge + "\n        mult " + mult + "\n        units angs\n        coords\n")
    atom_list = []
    i = 0
    for line in xyz2:
      i = i+1
      if i > 2:
        atom = line.split()
        if atom[0] == "D":
          atom[0] = "H"
          line = line.replace("D", "H")
        if atom[0] == "T":
          atom[0] = "H"
          line = line.replace("T", "H")
        inp.write(line)
        if not atom[0] in atom_list:
          atom_list.append(atom[0])
    inp.write("   end\nend\n")
    if mp2_block != "":
      inp.write(mp2_block+"\n")
    el_list = atom_list
    if ECP == False:
      basis_set_fn = os.path.join(self.parent.basis_dir,basis_name)
      basis = open(basis_set_fn,"r")
      inp.write("%basis\n")
      for i in range(0,len(atom_list)):
        atom_type = "newgto " +atom_list[i] + '\n'
        inp.write(atom_type)
        temp_atom = atom_list[i] + ":" + basis_name
        basis.seek(0,0)
        while True:
          line = basis.readline()
          if not line:
            raise RecursionError("Atom not found in the basis set!")
          if line == '':
            continue
          if line[0] == "!":
            continue
          if "keys=" in line:
            key_line = line.split(" ")
            type = key_line[key_line.index("keys=")+2]
          if temp_atom in line:
            break
        line_run = basis.readline()
        if "{"  in line_run:
          line_run = basis.readline()
        while (not "}" in line_run):
          shell_line = line_run.split()
          if type == "turbomole=":
            n_primitives = shell_line[0]
            shell_type = shell_line[1]
          elif type == "gamess-us=":
            n_primitives = shell_line[1]
            shell_type = shell_line[0]
          shell_gaussian = "    " + shell_type.upper() + "   " + n_primitives + "\n"
          inp.write(shell_gaussian)
          for n in range(0,int(n_primitives)):
            if type == "turbomole=":
              inp.write("  " + str(n+1) + "   " + basis.readline().replace("D","E"))
            else:
              inp.write(basis.readline().replace("D","E"))
          line_run = basis.readline()
        inp.write("end\n")
      basis.close()
      inp.write("end\n")
    conv = OV.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_CONV')
    hflayer = OV.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_HF_LAYERS')
    ecplayer = OV.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_ECP_LAYERS')
    inp.write("%qmmm\n")
    asu_lines = xyz1.readlines()
    natoms = int(asu_lines[0])
    xyz2.seek(0)
    all_lines = xyz2.readlines()
    atom_list = []
    i = 0
    for line in asu_lines:
      i += 1
      if i < 3:
        continue
      j = 0
      for line2 in all_lines:
        j += 1
        if j < 3:
          continue
        if line == line2:
          atom_list.append(j-3)
          break
    if len(atom_list) != natoms:
      print("Did not find all atoms in the big XYZ-file! Make sure the ASU is in included when running 'pack %f -c'"%radius)
      return
    inp.write("  NUnitCellAtoms %d\n"%natoms)
    qm_atoms = ""
    for atom in atom_list:
      qm_atoms += " %d"%atom
    inp.write("  QMAtoms {%s } end"%qm_atoms)
    params_filename = self.name + ".ORCAFF.prms"
    if qmmmtype == "Ion":
      inp.write("""
  Conv_Charges true
  Conv_Charges_MaxNCycles 30
  Conv_Charges_ConvThresh %f
  ECPLayers %d
  HFLayers %d
  HFLayerGTO "3-21G"
  Charge_Total 0
  EnforceTotalCharge true
  OuterPCLayers 1
  ORCAFFFilename "%s"
end"""%(float(conv),ecplayer,hflayer,params_filename))
    else:
      inp.write("  Conv_Charges_MaxNCycles 30\n  Conv_Charge_UseQMCoreOnly true\n  Conv_Charges_ConvThresh %f\n  HFLayers %d\nend" % (float(conv), hflayer))
    inp.close()
    if qmmmtype == "Ion":
      import subprocess
      mm_prep_args = []
      mm_prep_args.append(os.path.join(os.path.dirname(self.parent.orca_exe), "orca_mm"))
      if sys.platform[:3] == 'win':
        mm_prep_args[0] += ".exe"
      mm_prep_args.append("-makeff")
      mm_prep_args.append(self.name+".xyz")
      for t in el_list:
        mm_prep_args.append("-CEL")
        mm_prep_args.append(t)
        if t in known_charges:
          mm_prep_args.append(str(known_charges[t]))
        else:
          mm_prep_args.append("0.0")
      if sys.platform[:3] == 'win':
        startinfo = subprocess.STARTUPINFO()
        startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startinfo.wShowWindow = 7
        m = subprocess.Popen(mm_prep_args, cwd=self.full_dir,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             stdin=subprocess.PIPE,
                             startupinfo=startinfo)
      else:
        m = subprocess.Popen(mm_prep_args,
                             cwd=self.full_dir,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             stdin=subprocess.PIPE)
      while m.poll() is None:
        time.sleep(1)
      n = os.path.join(self.full_dir, self.name)
      if not os.path.exists(os.path.join(self.full_dir,params_filename)):
        OV.SetVar('NoSpherA2-Error', "NoORCAMMFile")
        raise NameError("No MM File for ORCA file generated!")

  def write_orca_input(self,xyz,basis_name=None,method=None,relativistic=None,charge=None,mult=None,strategy=None,convergence=None,part=None, efield=None):
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    software = OV.GetParam("snum.NoSpherA2.source")
    ECP = False
    if basis_name == None:
      basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    if "ECP" in basis_name:
      ECP = True
    if xyz:
      self.write_xyz_file()
    xyz = open(coordinates_fn,"r")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".inp"
    inp = open(self.input_fn,"w")
    if method == None:
      method = OV.GetParam('snum.NoSpherA2.method')
    ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
    if OV.GetParam('snum.NoSpherA2.ncpus') != '1':
      cpu = "nprocs " + ncpus
    else:
      cpu = "nprocs 1"
    mem = OV.GetParam('snum.NoSpherA2.mem')
    mem_value = float(mem) * 1024 / int(ncpus)
    mem = "%maxcore " + str(mem_value)
    control = "! NoPop MiniPrint "

    if ECP == False:
      control += "3-21G "
    else:
      control += basis_name.replace("ECP-", "") + ' '

    grid = OV.GetParam('snum.NoSpherA2.becke_accuracy')
    mp2_block = ""
    if method == "HF":
      if mult != 1 and OV.GetParam("snum.NoSpherA2.ORCA_FORCE_ROKS") == True:
        control += " ROHF "
      else:
        control += " rhf "
      grids = ""
    else:
      if mult != 1 and OV.GetParam("snum.NoSpherA2.ORCA_FORCE_ROKS") == True:
        control += " ROKS "
      if software == "Hybrid":
        software = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d"%part)
      elif software == "fragHAR":
        software = "ORCA 5.0"
      if software == "ORCA 5.0" or software == "ORCA 6.0":
        SCNL = OV.GetParam('snum.NoSpherA2.ORCA_SCNL')
        if SCNL == True:
          if method != "wB97X":
            control += method + ' SCNL '
          else:
            control += method + '-V SCNL '
        else:
          if method == "DSD-BLYP":
            control += method + ' D3BJ def2-TZVPP/C '
            mp2_block += "%mp2 Density relaxed RI true end"
          else:
            control += method + ' '
        grids = self.write_grids_5(method, grid)
      else:
        control += method + ' '
        grids = self.write_grids_4(method, grid)
    if convergence == None:
      convergence = OV.GetParam('snum.NoSpherA2.ORCA_SCF_Conv')
    if convergence == "NoSpherA2SCF":
      conv = "LooseSCF"
    else:
      conv = convergence
    if strategy == None:
      strategy = OV.GetParam('snum.NoSpherA2.ORCA_SCF_Strategy')
    control += grids + conv + ' ' + strategy
    if relativistic == None:
      relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
    if method == "BP86" or method == "PBE" or method == "PWLDA":
      if relativistic == True:
        t = OV.GetParam('snum.NoSpherA2.ORCA_Relativistic')
        if t == "DKH2":
          control += " DKH2 SARC/J RI"
        elif t == "ZORA":
          control += " ZORA SARC/J RI"
        elif t == "ZORA/RI":
          control += " ZORA/RI SARC/J RI"
        elif t == "IORA":
          control += " IORA SARC/J RI"
        else:
          control += " IORA/RI SARC/J RI"
      else:
        control += " def2/J RI"
    else:
      if relativistic == True:
        t = OV.GetParam('snum.NoSpherA2.ORCA_Relativistic')
        if t == "DKH2":
          control += " DKH2 SARC/J RIJCOSX"
        elif t == "ZORA":
          control += " ZORA SARC/J RIJCOSX"
        elif t == "IORA":
          control += " IORA SARC/J RIJCOSX"        
        elif t == "ZORA/RI":
          control += " ZORA/RI SARC/J RIJCOSX"
        elif t == "IORA/RI":
          control += " IORA/RI SARC/J RIJCOSX"
        else:
          print("============= Relativity kind not known! Will use ZORA! =================")
          control += " ZORA SARC/J RIJCOSX"
      else:
        control += " def2/J RIJCOSX"
    Solvation = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
    if Solvation != "Vacuum" and Solvation != None:
      control += " CPCM(" + Solvation + ") "
    GBW_file = OV.GetParam("snum.NoSpherA2.ORCA_USE_GBW")
    if "5.0" not in OV.GetParam("snum.NoSpherA2.source") and "6.0" not in OV.GetParam("snum.NoSpherA2.source"):
      GBW_file = False
    if GBW_file == False:
      control += " AIM "
    if charge == None:
      charge = OV.GetParam('snum.NoSpherA2.charge')
    if mult == None:
      mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    if mult == 0:
      mult = 1
    if "5.0" in software or "6.0" in software:
        inp.write(control + ' NOTRAH\n%pal\n' + cpu + '\nend\n' + mem + '\n%coords\n        CTyp xyz\n        charge ' + charge + "\n        mult " + mult + "\n        units angs\n        coords\n")
    else:
        inp.write(control + '\n%pal\n' + cpu + '\nend\n' + mem + '\n%coords\n        CTyp xyz\n        charge ' + charge + "\n        mult " + mult + "\n        units angs\n        coords\n")
    atom_list = []
    i = 0
    for line in xyz:
      i = i+1
      if i > 2:
        atom = line.split()
        if atom[0] == "D":
          atom[0] = "H"
          line = line.replace("D", "H")
        if atom[0] == "T":
          atom[0] = "H"
          line = line.replace("T", "H")
        inp.write(line)
        if not atom[0] in atom_list:
          atom_list.append(atom[0])
    xyz.close()
    inp.write("   end\nend\n")
    if mp2_block != "":
      inp.write(mp2_block+'\n')
    if ECP == False:
      basis_set_fn = os.path.join(self.parent.basis_dir, basis_name)
      basis = open(basis_set_fn,"r")
      inp.write("%basis\n")
      for i in range(0, len(atom_list)):
        atom_type = "newgto " + atom_list[i] + '\n'
        inp.write(atom_type)
        temp_atom = atom_list[i] + ":" + basis_name
        basis.seek(0, 0)
        while True:
          line = basis.readline()
          if not line:
            raise RecursionError("Atom not found in the basis set!")
          if line == '':
            continue
          if line[0] == "!":
            continue
          if "keys=" in line:
            key_line = line.split(" ")
            type = key_line[key_line.index("keys=") + 2]
          if temp_atom in line:
            break
        line_run = basis.readline()
        if "{" in line_run:
          line_run = basis.readline()
        while (not "}" in line_run):
          shell_line = line_run.split()
          if type == "turbomole=":
            n_primitives = shell_line[0]
            shell_type = shell_line[1]
          elif type == "gamess-us=":
            n_primitives = shell_line[1]
            shell_type = shell_line[0]
          shell_gaussian = "    " + shell_type.upper() + "   " + n_primitives + "\n"
          inp.write(shell_gaussian)
          for n in range(0, int(n_primitives)):
            if type == "turbomole=":
              inp.write("  " + str(n + 1) + "   " + basis.readline().replace("D", "E"))
            else:
              inp.write(basis.readline().replace("D", "E"))
          line_run = basis.readline()
        inp.write("end\n")
      basis.close()
      inp.write("end\n")
    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
    run = None
    damping = OV.GetParam('snum.NoSpherA2.ORCA_DAMP')
    scf_block = ""
    if damping:
      scf_block += "   CNVZerner true\n"
      if strategy == "SlowConv":
        scf_block += "   DampMax 0.9\n"
      elif strategy == "VerySlowConv":
        scf_block += "   DampMax 0.975\n"
      elif strategy == "NormalConv":
        scf_block += "   DampMax 0.8\n"
      elif strategy == "EasyConv":
        scf_block += "   DampMax 0.72\n"
    if not efield == None:
      amp = float(efield[1:])
      direction = efield[0]
      if direction == "x":
        scf_block += f"    EField {amp}, 0.0, 0.0"
      elif direction == "y":
        scf_block += f"    EField 0.0, {amp}, 0.0"
      elif direction == "z":
        scf_block += f"    EField 0.0, 0.0, {amp}"
      if direction != "0":
        scf_block += f"   Guess MORead\n   MOInp \"zero.gbw\"\n"
    if Full_HAR == True:
      run = OV.GetVar('Run_number')
      source = OV.GetParam('snum.NoSpherA2.source')
      if source == "Hybrid":
        run = 0
      if run > 1:
        if os.path.exists(os.path.join(self.full_dir, self.name + "2.gbw")):
          scf_block += f"   Guess MORead\n   MOInp \"{self.name}2.gbw\""
          if convergence == "NoSpherA2SCF":
            scf_block += "\n   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4"
        elif convergence == "NoSpherA2SCF":
          scf_block += "   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4"
      else:
        if convergence == "NoSpherA2SCF":
          scf_block += "   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4"
    else:
      if convergence == "NoSpherA2SCF":
        scf_block += "   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4"
    if scf_block != "":
      inp.write(f"%scf\n{scf_block}\nend\n")
    inp.close()

  def write_psi4_input(self,xyz):
    if xyz:
      self.write_xyz_file()
      coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
      pbc = OV.GetParam('snum.NoSpherA2.pySCF_PBC')
      if pbc == True:
        olex.m("pack cell")
      if xyz:
        self.write_xyz_file()
      xyz = open(coordinates_fn,"r")
      self.input_fn = os.path.join(self.full_dir, self.name) + ".py"
      inp = open(self.input_fn,"w")
      if basis_name == None:
        basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
      basis_set_fn = os.path.join(self.parent.basis_dir,basis_name)
      basis = open(basis_set_fn,"r")
      ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
      if charge == None:
        charge = int(OV.GetParam('snum.NoSpherA2.charge'))
      mem = OV.GetParam('snum.NoSpherA2.mem')
      mem_value = float(mem) * 1024
      if pbc == False:
        inp.write("#!/usr/bin/env python\n%s\n\nfrom pyscf import gto, scf, dft, lib\n"%fixed_wfn_function)
        inp.write("lib.num_threads(%s)\nmol = gto.M(\n  atom = '''"%ncpus)
        atom_list = []
        i = 0
        for line in xyz:
          i = i+1
          if i > 2:
            atom = line.split()
            inp.write(line)
            if not atom[0] in atom_list:
              atom_list.append(atom[0])
        xyz.close()
        inp.write("''',\n  verbose = 4,\n  charge = %d,\n  spin = %d\n)\nmol.output = '%s_pyscf.log'\n"%(int(charge),int(mult-1),self.name))
        inp.write("mol.max_memory = %s\n"%str(mem_value))
        inp.write("mol.basis = {")
        for i in range(0,len(atom_list)):
          atom_type = "'" +atom_list[i] + "': ["
          inp.write(atom_type)
          temp_atom = atom_list[i] + ":" + basis_name
          basis.seek(0,0)
          while True:
            line = basis.readline()
            if not line:
              raise RecursionError("Atom not found in the basis set!")
            if line[0] == "!":
              continue
            if "keys=" in line:
              key_line = line.split(" ")
              type = key_line[key_line.index("keys=")+2]
            if temp_atom in line:
              break
          line_run = basis.readline()
          if "{"  in line_run:
            line_run = basis.readline()
          while (not "}" in line_run):
            shell_line = line_run.split()
            if type == "turbomole=":
              n_primitives = shell_line[0]
              shell_type = shell_line[1]
            elif type == "gamess-us=":
              n_primitives = shell_line[1]
              shell_type = shell_line[0]
            if shell_type.upper() == "S":
              momentum = '0'
            elif shell_type.upper() == "P":
              momentum = '1'
            elif shell_type.upper() == "D":
              momentum = '2'
            elif shell_type.upper() == "F":
              momentum = '3'
            inp.write("[%s,"%momentum)
            for n in range(0,int(n_primitives)):
              if type == "turbomole=":
                number1, number2 = basis.readline().replace("D","E").split()
                inp.write("\n                (" + number1 + ', ' + number2 + "),")
              else:
                number1, number2, number3 = basis.readline().replace("D","E").split()
                inp.write("\n                (" + number2 + ', ' + number3 + "),")
            inp.write("],\n")
            line_run = basis.readline()
          inp.write("],\n")
        basis.close()
        inp.write("\n}\nmol.build()\n")

        model_line = None
        if method == None:
          method = OV.GetParam('snum.NoSpherA2.method')
        if method == "HF":
          if mult == 1:
            model_line = "scf.RHF(mol)"
          else:
            model_line = "scf.UHF(mol)"
        else:
          if mult == 1:
            model_line = "dft.RKS(mol)"
          else:
            model_line = "dft.UKS(mol)"

        if relativistic == None:
          relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
        if relativistic == True:
          model_line += ".x2c()"
        #inp.write("mf = sgx.sgx_fit(%s)\n"%model_line)
        inp.write("mf = %s\n"%model_line)
        if method == "B3LYP":
          #inp.write("mf.xc = 'b3lyp'\nmf.with_df.dfj = True\n")
          inp.write("mf.xc = 'b3lyp'\n")
        elif method == "PBE":
          inp.write("mf.xc = 'pbe,pbe'\n")
        elif method == "BLYP":
          inp.write("mf.xc = 'b88,lyp'\n")
        elif method == "M062X":
          inp.write("mf.xc = 'M062X'\n")
        elif method == "PBE0":
          inp.write("mf.xc = 'PBE0'\n")
        elif method == "R2SCAN":
          inp.write("mf.xc = 'R2SCAN'\n")
        grid_accuracy = OV.GetParam('snum.NoSpherA2.becke_accuracy')
        grid = None
        if grid_accuracy == "Low":
          grid = 0
        elif grid_accuracy == "Normal":
          grid = 0
        elif grid_accuracy == "High":
          grid = 3
        else:
          grid = 9
        rest = "mf = mf.density_fit()\n"
        if method != "HF":
          rest += "mf.grids.radi_method = dft.gauss_chebyshev\n"
        rest += "mf.grids.level = "+str(grid)+"\n"
        rest += """mf.with_df.auxbasis = 'def2-tzvp-jkfit'
  mf.diis_space = 19
  mf.conv_tol = 0.0033
  mf.conv_tol_grad = 1e-2
  mf.level_shift = 0.25"""
        if damp == None:
          damp = float(OV.GetParam('snum.NoSpherA2.pySCF_Damping'))
        rest += "\nmf.damp = %f\n"%damp
        rest += "mf.chkfile = '%s.chk'\n"%self.name
        Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
        run = None
        if Full_HAR == True:
          run = OV.GetVar('Run_number')
          if run > 1:
            rest += "mf.init_guess = 'chk'\n"
        solv = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
        if solv != "Vacuum":
          rest += "from pyscf import solvent\nmf = mf.ddCOSMO()\nmf.with_solvent.lebedev_order = 11\nmf.with_solvent.lmax = 5\nmf.with_solvent.grids.radi_method = dft.gauss_chebyshev\nmf.with_solvent.grids.level = %d\nmf.with_solvent.eps = %f\n"%(int(grid),float(solv_epsilon[solv]))
        rest +="""mf.kernel()
  print("Switching to SOSCF and shutting down damping & levelshift")
  mf.conv_tol = 1e-9
  mf.conv_tol_grad = 1e-5
  mf.level_shift = 0.0
  mf.damp = 0.0
  mf = scf.newton(mf)
  mf.kernel()"""
        rest += "\nwith open('%s.wfn', 'w') as f1:\n  write_wfn(f1,mol,mf.mo_coeff,mf.mo_energy,mf.mo_occ,mf.e_tot)"%self.name
        inp.write(rest)
        inp.close()


  def write_pyscf_script(self,xyz,basis_name=None,method=None,relativistic=None,charge=None,mult=None,damp=None,part=None):
    solv_epsilon = {
      "Water"                                  :78.3553,
      "Acetonitrile"                           :35.688 ,
      "Methanol"                               :32.613 ,
      "Ethanol"                                :24.852 ,
      "IsoQuinoline"                           :11.00  ,
      "Quinoline"                              :9.16   ,
      "Chloroform"                             :4.7113 ,
      "DiethylEther"                           :4.2400 ,
      "Dichloromethane"                        :8.93   ,
      "DiChloroEthane"                         :10.125 ,
      "CarbonTetraChloride"                    :2.2280 ,
      "Benzene"                                :2.2706 ,
      "Toluene"                                :2.3741 ,
      "ChloroBenzene"                          :5.6968 ,
      "NitroMethane"                           :36.562 ,
      "Heptane"                                :1.9113 ,
      "CycloHexane"                            :2.0165 ,
      "Aniline"                                :6.8882 ,
      "Acetone"                                :20.493 ,
      "TetraHydroFuran"                        :7.4257 ,
      "DiMethylSulfoxide"                      :46.826 ,
      "Argon"                                  :1.430  ,
      "Krypton"                                :1.519  ,
      "Xenon"                                  :1.706  ,
      "n-Octanol"                              :9.8629 ,
      "1,1,1-TriChloroEthane"                  :7.0826 ,
      "1,1,2-TriChloroEthane"                  :7.1937 ,
      "1,2,4-TriMethylBenzene"                 :2.3653 ,
      "1,2-DiBromoEthane"                      :4.9313 ,
      "1,2-EthaneDiol"                         :40.245 ,
      "1,4-Dioxane"                            :2.2099 ,
      "1-Bromo-2-MethylPropane"                :7.7792 ,
      "1-BromoOctane"                          :5.0244 ,
      "1-BromoPentane"                         :6.269  ,
      "1-BromoPropane"                         :8.0496 ,
      "1-Butanol"                              :17.332 ,
      "1-ChloroHexane"                         :5.9491 ,
      "1-ChloroPentane"                        :6.5022 ,
      "1-ChloroPropane"                        :8.3548 ,
      "1-Decanol"                              :7.5305 ,
      "1-FluoroOctane"                         :3.89   ,
      "1-Heptanol"                             :11.321 ,
      "1-Hexanol"                              :12.51  ,
      "1-Hexene"                               :2.0717 ,
      "1-Hexyne"                               :2.615  ,
      "1-IodoButane"                           :6.173  ,
      "1-IodoHexaDecane"                       :3.5338 ,
      "1-IodoPentane"                          :5.6973 ,
      "1-IodoPropane"                          :6.9626 ,
      "1-NitroPropane"                         :23.73  ,
      "1-Nonanol"                              :8.5991 ,
      "1-Pentanol"                             :15.13  ,
      "1-Pentene"                              :1.9905 ,
      "1-Propanol"                             :20.524 ,
      "2,2,2-TriFluoroEthanol"                 :26.726 ,
      "2,2,4-TriMethylPentane"                 :1.9358 ,
      "2,4-DiMethylPentane"                    :1.8939 ,
      "2,4-DiMethylPyridine"                   :9.4176 ,
      "2,6-DiMethylPyridine"                   :7.1735 ,
      "2-BromoPropane"                         :9.3610 ,
      "2-Butanol"                              :15.944 ,
      "2-ChloroButane"                         :8.3930 ,
      "2-Heptanone"                            :11.658 ,
      "2-Hexanone"                             :14.136 ,
      "2-MethoxyEthanol"                       :17.2   ,
      "2-Methyl-1-Propanol"                    :16.777 ,
      "2-Methyl-2-Propanol"                    :12.47  ,
      "2-MethylPentane"                        :1.89   ,
      "2-MethylPyridine"                       :9.9533 ,
      "2-NitroPropane"                         :25.654 ,
      "2-Octanone"                             :9.4678 ,
      "2-Pentanone"                            :15.200 ,
      "2-Propanol"                             :19.264 ,
      "2-Propen-1-ol"                          :19.011 ,
      "3-MethylPyridine"                       :11.645 ,
      "3-Pentanone"                            :16.78  ,
      "4-Heptanone"                            :12.257 ,
      "4-Methyl-2-Pentanone"                   :12.887 ,
      "4-MethylPyridine"                       :11.957 ,
      "5-Nonanone"                             :10.6   ,
      "AceticAcid"                             :6.2528 ,
      "AcetoPhenone"                           :17.44  ,
      "a-ChloroToluene"                        :6.7175 ,
      "Anisole"                                :4.2247 ,
      "Benzaldehyde"                           :18.220 ,
      "BenzoNitrile"                           :25.592 ,
      "BenzylAlcohol"                          :12.457 ,
      "BromoBenzene"                           :5.3954 ,
      "BromoEthane"                            :9.01   ,
      "Bromoform"                              :4.2488 ,
      "Butanal"                                :13.45  ,
      "ButanoicAcid"                           :2.9931 ,
      "Butanone"                               :18.246 ,
      "ButanoNitrile"                          :24.291 ,
      "ButylAmine"                             :4.6178 ,
      "ButylEthanoate"                         :4.9941 ,
      "CarbonDiSulfide"                        :2.6105 ,
      "Cis-1,2-DiMethylCycloHexane"            :2.06   ,
      "Cis-Decalin"                            :2.2139 ,
      "CycloHexanone"                          :15.619 ,
      "CycloPentane"                           :1.9608 ,
      "CycloPentanol"                          :16.989 ,
      "CycloPentanone"                         :13.58  ,
      "Decalin-mixture"                        :2.196  ,
      "DiBromomEthane"                         :7.2273 ,
      "DiButylEther"                           :3.0473 ,
      "DiEthylAmine"                           :3.5766 ,
      "DiEthylSulfide"                         :5.723  ,
      "DiIodoMethane"                          :5.32   ,
      "DiIsoPropylEther"                       :3.38   ,
      "DiMethylDiSulfide"                      :9.6    ,
      "DiPhenylEther"                          :3.73   ,
      "DiPropylAmine"                          :2.9112 ,
      "e-1,2-DiChloroEthene"                   :2.14   ,
      "e-2-Pentene"                            :2.051  ,
      "EthaneThiol"                            :6.667  ,
      "EthylBenzene"                           :2.4339 ,
      "EthylEthanoate"                         :5.9867 ,
      "EthylMethanoate"                        :8.3310 ,
      "EthylPhenylEther"                       :4.1797 ,
      "FluoroBenzene"                          :5.42   ,
      "Formamide"                              :108.94 ,
      "FormicAcid"                             :51.1   ,
      "HexanoicAcid"                           :2.6    ,
      "IodoBenzene"                            :4.5470 ,
      "IodoEthane"                             :7.6177 ,
      "IodoMethane"                            :6.8650 ,
      "IsoPropylBenzene"                       :2.3712 ,
      "m-Cresol"                               :12.44  ,
      "Mesitylene"                             :2.2650 ,
      "MethylBenzoate"                         :6.7367 ,
      "MethylButanoate"                        :5.5607 ,
      "MethylCycloHexane"                      :2.024  ,
      "MethylEthanoate"                        :6.8615 ,
      "MethylMethanoate"                       :8.8377 ,
      "MethylPropanoate"                       :6.0777 ,
      "m-Xylene"                               :2.3478 ,
      "n-ButylBenzene"                         :2.36   ,
      "n-Decane"                               :1.9846 ,
      "n-Dodecane"                             :2.0060 ,
      "n-Hexadecane"                           :2.0402 ,
      "n-Hexane"                               :1.8819 ,
      "NitroBenzene"                           :34.809 ,
      "NitroEthane"                            :28.29  ,
      "n-MethylAniline"                        :5.9600 ,
      "n-MethylFormamide-mixture"              :181.56 ,
      "n,n-DiMethylAcetamide"                  :37.781 ,
      "n,n-DiMethylFormamide"                  :37.219 ,
      "n-Nonane"                               :1.9605 ,
      "n-Octane"                               :1.9406 ,
      "n-Pentadecane"                          :2.0333 ,
      "n-Pentane"                              :1.8371 ,
      "n-Undecane"                             :1.9910 ,
      "o-ChloroToluene"                        :4.6331 ,
      "o-Cresol"                               :6.76   ,
      "o-DiChloroBenzene"                      :9.9949 ,
      "o-NitroToluene"                         :25.669 ,
      "o-Xylene"                               :2.5454 ,
      "Pentanal"                               :10.0   ,
      "PentanoicAcid"                          :2.6924 ,
      "PentylAmine"                            :4.2010 ,
      "PentylEthanoate"                        :4.7297 ,
      "PerFluoroBenzene"                       :2.029  ,
      "p-IsoPropylToluene"                     :2.2322 ,
      "Propanal"                               :18.5   ,
      "PropanoicAcid"                          :3.44   ,
      "PropanoNitrile"                         :29.324 ,
      "PropylAmine"                            :4.9912 ,
      "PropylEthanoate"                        :5.5205 ,
      "p-Xylene"                               :2.2705 ,
      "Pyridine"                               :12.978 ,
      "sec-ButylBenzene"                       :2.3446 ,
      "tert-ButylBenzene"                      :2.3447 ,
      "TetraChloroEthene"                      :2.268  ,
      "TetraHydroThiophene-s,s-dioxide"        :43.962 ,
      "Tetralin"                               :2.771  ,
      "Thiophene"                              :2.7270 ,
      "Thiophenol"                             :4.2728 ,
      "trans-Decalin"                          :2.1781 ,
      "TriButylPhosphate"                      :8.1781 ,
      "TriChloroEthene"                        :3.422  ,
      "TriEthylAmine"                          :2.3832 ,
      "Xylene-mixture"                         :2.3879 ,
      "z-1,2-DiChloroEthene"                   :9.2
    }

    if mult == None:
      mult = int(OV.GetParam('snum.NoSpherA2.multiplicity'))
    fixed_wfn_function = """
import numpy

TYPE_MAP = [
  [1],  # S
  [2, 3, 4],  # P
  [5, 8, 9, 6, 10, 7],  # D
  [11,14,15,17,20,18,12,16,19,13],  # F
  [21,24,25,30,33,31,26,34,35,28,22,27,32,29,23],  # G
  [56,55,54,53,52,51,50,49,48,47,46,45,44,43,42,41,40,39,38,37,36],  # H
]

def write_wfn(fout, mol, mo_coeff, mo_energy, mo_occ, tot_ener):
  from pyscf.x2c import x2c
  from pyscf import gto, lib
"""
    if mult != 1:
      fixed_wfn_function +="""  total_nmo = 0
  MO_offset = 0
  for s in range(2):
    for i in range(len(mo_occ[s])):
      if mo_occ[s][i] != 0:
        total_nmo += 1
  for s in range(2):
    temp_mol, ctr = x2c._uncontract_mol(mol, True, 0.)
    temp_mo_coeff = numpy.dot(ctr, mo_coeff[s])

    nmo = temp_mo_coeff.shape[1]
    mo_cart = []
    centers = []
    types = []
    exps = []
    p0 = 0
    for ib in range(temp_mol.nbas):
      ia = temp_mol.bas_atom(ib)
      l = temp_mol.bas_angular(ib)
      es = temp_mol.bas_exp(ib)
      c = temp_mol._libcint_ctr_coeff(ib)
      np, nc = c.shape
      nd = nc*(2*l+1)
      mosub = temp_mo_coeff[p0:p0+nd].reshape(-1,nc,nmo)
      c2s = gto.cart2sph(l)
      new_mosub = numpy.einsum('yki,cy,pk->pci', mosub, c2s, c)
      mo_cart.append(new_mosub.transpose(1,0,2).reshape(-1,nmo))

      for t in TYPE_MAP[l]:
          types.append([t]*np)
      ncart = temp_mol.bas_len_cart(ib)
      exps.extend([es]*ncart)
      centers.extend([ia+1]*(np*ncart))
      p0 += nd
    mo_cart = numpy.vstack(mo_cart)
    centers = numpy.hstack(centers)
    types = numpy.hstack(types)
    exps = numpy.hstack(exps)
    nprim, nmo = mo_cart.shape
    if s == 0:
      fout.write('From PySCF\\n')
      fout.write('GAUSSIAN %14d MOL ORBITALS %6d PRIMITIVES %8d NUCLEI\\n'%(total_nmo, mo_cart.shape[0], mol.natm))
      for ia in range(mol.natm):
        x, y, z = temp_mol.atom_coord(ia)
        fout.write('%3s%8d (CENTRE%3d) %12.8f%12.8f%12.8f  CHARGE = %4.1f\\n'%(mol.atom_pure_symbol(ia), ia+1, ia+1, x, y, z, mol.atom_charge(ia)))
      for i0, i1 in lib.prange(0, nprim, 20):
        fout.write('CENTRE ASSIGNMENTS  %s\\n'% ''.join('%3d'%x for x in centers[i0:i1]))
      for i0, i1 in lib.prange(0, nprim, 20):
        fout.write('TYPE ASSIGNMENTS    %s\\n'% ''.join('%3d'%x for x in types[i0:i1]))
      for i0, i1 in lib.prange(0, nprim, 5):
        fout.write('EXPONENTS  %s\\n'% ' '.join('%13.7E'%x for x in exps[i0:i1]))

    for k in range(nmo):
      if mo_occ[s][k] != 0.0:
        mo = mo_cart[:,k]
        fout.write('MO  %-12d          OCC NO = %12.8f ORB. ENERGY = %12.8f\\n'%(k+1+MO_offset, mo_occ[s][k], mo_energy[s][k]))
        if s == 0:
          MO_offset += 1
        for i0, i1 in lib.prange(0, nprim, 5):
          fout.write(' %s\\n' % ' '.join('%15.8E'%x for x in mo[i0:i1]))
    if s == 1:
      fout.write('END DATA\\n')
      fout.write(' THE SCF ENERGY =%20.12f THE VIRIAL(-V/T)=   0.00000000\\n'%tot_ener)"""
    else:
      fixed_wfn_function +="""  mol, ctr = x2c._uncontract_mol(mol, True, 0.)
  mo_coeff = numpy.dot(ctr, mo_coeff)

  nmo = mo_coeff.shape[1]
  mo_cart = []
  centers = []
  types = []
  exps = []
  p0 = 0
  for ib in range(mol.nbas):
    ia = mol.bas_atom(ib)
    l = mol.bas_angular(ib)
    es = mol.bas_exp(ib)
    c = mol._libcint_ctr_coeff(ib)
    np, nc = c.shape
    nd = nc*(2*l+1)
    mosub = mo_coeff[p0:p0+nd].reshape(-1,nc,nmo)
    c2s = gto.cart2sph(l)
    mosub = numpy.einsum('yki,cy,pk->pci', mosub, c2s, c)
    mo_cart.append(mosub.transpose(1,0,2).reshape(-1,nmo))

    for t in TYPE_MAP[l]:
        types.append([t]*np)
    ncart = mol.bas_len_cart(ib)
    exps.extend([es]*ncart)
    centers.extend([ia+1]*(np*ncart))
    p0 += nd
  mo_cart = numpy.vstack(mo_cart)
  centers = numpy.hstack(centers)
  types = numpy.hstack(types)
  exps = numpy.hstack(exps)
  nprim, nmo = mo_cart.shape

  fout.write('From PySCF\\n')
  fout.write('GAUSSIAN %14d MOL ORBITALS %6d PRIMITIVES %8d NUCLEI\\n'%(mo_cart.shape[1], mo_cart.shape[0], mol.natm))
  for ia in range(mol.natm):
    x, y, z = mol.atom_coord(ia)
    fout.write('%3s%8d (CENTRE%3d) %12.8f%12.8f%12.8f  CHARGE = %4.1f\\n'%(mol.atom_pure_symbol(ia), ia+1, ia+1, x, y, z, mol.atom_charge(ia)))
  for i0, i1 in lib.prange(0, nprim, 20):
    fout.write('CENTRE ASSIGNMENTS  %s\\n'% ''.join('%3d'%x for x in centers[i0:i1]))
  for i0, i1 in lib.prange(0, nprim, 20):
    fout.write('TYPE ASSIGNMENTS    %s\\n'% ''.join('%3d'%x for x in types[i0:i1]))
  for i0, i1 in lib.prange(0, nprim, 5):
    fout.write('EXPONENTS  %s\\n'% ' '.join('%13.7E'%x for x in exps[i0:i1]))

  for k in range(nmo):
      mo = mo_cart[:,k]
      fout.write('MO  %-12d          OCC NO = %12.8f ORB. ENERGY = %12.8f\\n'%(k+1, mo_occ[k], mo_energy[k]))
      for i0, i1 in lib.prange(0, nprim, 5):
        fout.write(' %s\\n' % ' '.join('%15.8E'%x for x in mo[i0:i1]))
  fout.write('END DATA\\n')
  fout.write(' THE SCF ENERGY =%20.12f THE VIRIAL(-V/T)=   0.00000000\\n'%tot_ener)"""
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    pbc = OV.GetParam('snum.NoSpherA2.pySCF_PBC')
    if pbc == True:
      olex.m("pack cell")
    if xyz:
      self.write_xyz_file()
    xyz = open(coordinates_fn,"r")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".py"
    inp = open(self.input_fn,"w")
    if basis_name == None:
      basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    basis_set_fn = os.path.join(self.parent.basis_dir,basis_name)
    basis = open(basis_set_fn,"r")
    ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
    if charge == None:
      charge = int(OV.GetParam('snum.NoSpherA2.charge'))
    mem = OV.GetParam('snum.NoSpherA2.mem')
    mem_value = float(mem) * 1024
    if pbc == False:
      inp.write("#!/usr/bin/env python\n%s\n\nfrom pyscf import gto, scf, dft, lib\n"%fixed_wfn_function)
      inp.write("lib.num_threads(%s)\nmol = gto.M(\n  atom = '''"%ncpus)
      atom_list = []
      i = 0
      for line in xyz:
        i = i+1
        if i > 2:
          atom = line.split()
          inp.write(line)
          if not atom[0] in atom_list:
            atom_list.append(atom[0])
      xyz.close()
      inp.write("''',\n  verbose = 4,\n  charge = %d,\n  spin = %d\n)\nmol.output = '%s_pyscf.log'\n"%(int(charge),int(mult-1),self.name))
      inp.write("mol.max_memory = %s\n"%str(mem_value))
      inp.write("mol.basis = {")
      for i in range(0,len(atom_list)):
        atom_type = "'" +atom_list[i] + "': ["
        inp.write(atom_type)
        temp_atom = atom_list[i] + ":" + basis_name
        basis.seek(0,0)
        while True:
          line = basis.readline()
          if not line:
            raise RecursionError("Atom not found in the basis set!")
          if line[0] == "!":
            continue
          if "keys=" in line:
            key_line = line.split(" ")
            type = key_line[key_line.index("keys=")+2]
          if temp_atom in line:
            break
        line_run = basis.readline()
        if "{"  in line_run:
          line_run = basis.readline()
        while (not "}" in line_run):
          shell_line = line_run.split()
          if type == "turbomole=":
            n_primitives = shell_line[0]
            shell_type = shell_line[1]
          elif type == "gamess-us=":
            n_primitives = shell_line[1]
            shell_type = shell_line[0]
          if shell_type.upper() == "S":
            momentum = '0'
          elif shell_type.upper() == "P":
            momentum = '1'
          elif shell_type.upper() == "D":
            momentum = '2'
          elif shell_type.upper() == "F":
            momentum = '3'
          inp.write("[%s,"%momentum)
          for n in range(0,int(n_primitives)):
            if type == "turbomole=":
              number1, number2 = basis.readline().replace("D","E").split()
              inp.write("\n                (" + number1 + ', ' + number2 + "),")
            else:
              number1, number2, number3 = basis.readline().replace("D","E").split()
              inp.write("\n                (" + number2 + ', ' + number3 + "),")
          inp.write("],\n")
          line_run = basis.readline()
        inp.write("],\n")
      basis.close()
      inp.write("\n}\nmol.build()\n")

      model_line = None
      if method == None:
        method = OV.GetParam('snum.NoSpherA2.method')
      if method == "HF":
        if mult == 1:
          model_line = "scf.RHF(mol)"
        else:
          model_line = "scf.UHF(mol)"
      else:
        if mult == 1:
          model_line = "dft.RKS(mol)"
        else:
          model_line = "dft.UKS(mol)"

      if relativistic == None:
        relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
      if relativistic == True:
        model_line += ".x2c()"
      #inp.write("mf = sgx.sgx_fit(%s)\n"%model_line)
      inp.write("mf = %s\n"%model_line)
      if method == "B3LYP":
        #inp.write("mf.xc = 'b3lyp'\nmf.with_df.dfj = True\n")
        inp.write("mf.xc = 'b3lyp'\n")
      elif method == "PBE":
        inp.write("mf.xc = 'pbe,pbe'\n")
      elif method == "BLYP":
        inp.write("mf.xc = 'b88,lyp'\n")
      elif method == "M062X":
        inp.write("mf.xc = 'M062X'\n")
      elif method == "PBE0":
        inp.write("mf.xc = 'PBE0'\n")
      elif method == "R2SCAN":
        inp.write("mf.xc = 'R2SCAN'\n")
      grid_accuracy = OV.GetParam('snum.NoSpherA2.becke_accuracy')
      grid = None
      if grid_accuracy == "Low":
        grid = 0
      elif grid_accuracy == "Normal":
        grid = 0
      elif grid_accuracy == "High":
        grid = 3
      else:
        grid = 9
      rest = "mf = mf.density_fit()\n"
      if method != "HF":
        rest += "mf.grids.radi_method = dft.gauss_chebyshev\n"
      rest += "mf.grids.level = "+str(grid)+"\n"
      rest += """mf.with_df.auxbasis = 'def2-tzvp-jkfit'
mf.diis_space = 19
mf.conv_tol = 0.0033
mf.conv_tol_grad = 1e-2
mf.level_shift = 0.25"""
      if damp == None:
        damp = float(OV.GetParam('snum.NoSpherA2.pySCF_Damping'))
      rest += "\nmf.damp = %f\n"%damp
      rest += "mf.chkfile = '%s.chk'\n"%self.name
      Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
      run = None
      if Full_HAR == True:
        run = OV.GetVar('Run_number')
        if run > 1:
          rest += "mf.init_guess = 'chk'\n"
      solv = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
      if solv != "Vacuum":
        rest += "from pyscf import solvent\nmf = mf.ddCOSMO()\nmf.with_solvent.lebedev_order = 11\nmf.with_solvent.lmax = 5\nmf.with_solvent.grids.radi_method = dft.gauss_chebyshev\nmf.with_solvent.grids.level = %d\nmf.with_solvent.eps = %f\n"%(int(grid),float(solv_epsilon[solv]))
      rest +="""mf.kernel()
print("Switching to SOSCF and shutting down damping & levelshift")
mf.conv_tol = 1e-9
mf.conv_tol_grad = 1e-5
mf.level_shift = 0.0
mf.damp = 0.0
mf = scf.newton(mf)
mf.kernel()"""
      rest += "\nwith open('%s.wfn', 'w') as f1:\n  write_wfn(f1,mol,mf.mo_coeff,mf.mo_energy,mf.mo_occ,mf.e_tot)"%self.name
      inp.write(rest)
      inp.close()
    else:
      from cctbx_olex_adapter import OlexCctbxAdapter
      cctbx_adaptor = OlexCctbxAdapter()
      uc = cctbx_adaptor.reflections.f_obs.unit_cell()
      cm = uc.metrical_matrix()
      from math import sqrt
      import numpy as np
      inp.write("#!/usr/bin/env python\n\nfrom pyscf.pbc import gto, scf, dft, df\nfrom pyscf import lib\n")
      inp.write("lib.num_threads(%s)\ncell = gto.M(\n  atom = '''"%ncpus)
      atom_list = []
      i = 0
      for line in xyz:
        i = i+1
        if i > 2:
          atom = line.split()
          inp.write(line)
          if not atom[0] in atom_list:
            atom_list.append(atom[0])
      xyz.close()
      print(cm)
      inp.write("''',\n  verbose = 5,\n)\ncell.output = '%s_pyscf.log'\n"%self.name)
      inp.write("cell.a = '''%.5f %.5f %.5f\n"%(np.sign(cm[0])*sqrt(abs(cm[0])),np.sign(cm[3])*sqrt(abs(cm[3])),np.sign(cm[4])*sqrt(abs(cm[4]))))
      inp.write("%.5f %.5f %.5f\n"%(np.sign(cm[3])*sqrt(abs(cm[3])),np.sign(cm[1])*sqrt(abs(cm[1])),np.sign(cm[5])*sqrt(abs(cm[5]))))
      inp.write("%.5f %.5f %.5f'''\n"%(np.sign(cm[4])*sqrt(abs(cm[4])),np.sign(cm[5])*sqrt(abs(cm[5])),np.sign(cm[2])*sqrt(abs(cm[2]))))
      inp.write("cell.charge = %s\n"%charge)
      inp.write("cell.spin = %s\n"%str(int(mult)-1))
      inp.write("cell.max_memory = %s\n"%str(mem_value))
      inp.write("cell.precision = 1.0e-06\ncell.exp_to_discard = 0.1\n")
      inp.write("cell.basis = {")
      for i in range(0,len(atom_list)):
        atom_type = "'" +atom_list[i] + "': ["
        inp.write(atom_type)
        temp_atom = atom_list[i] + ":" + basis_name
        basis.seek(0,0)
        while True:
          line = basis.readline()
          if line[0] == "!":
            continue
          if "keys=" in line:
            key_line = line.split(" ")
            type = key_line[key_line.index("keys=")+2]
          if temp_atom in line:
            break
        line_run = basis.readline()
        if "{"  in line_run:
          line_run = basis.readline()
        while (not "}" in line_run):
          shell_line = line_run.split()
          if type == "turbomole=":
            n_primitives = shell_line[0]
            shell_type = shell_line[1]
          elif type == "gamess-us=":
            n_primitives = shell_line[1]
            shell_type = shell_line[0]
          if shell_type.upper() == "S":
            momentum = '0'
          elif shell_type.upper() == "P":
            momentum = '1'
          elif shell_type.upper() == "D":
            momentum = '2'
          elif shell_type.upper() == "F":
            momentum = '3'
          inp.write("[%s,"%momentum)
          for n in range(0,int(n_primitives)):
            if type == "turbomole=":
              number1, number2 = basis.readline().replace("D","E").split()
              inp.write("\n                (" + number1 + ', ' + number2 + "),")
            else:
              number1, number2, number3 = basis.readline().replace("D","E").split()
              inp.write("\n                (" + number2 + ', ' + number3 + "),")
          inp.write("],\n")
          line_run = basis.readline()
        inp.write("],\n")
      basis.close()
      inp.write("\n}\ncell.build()\nnk=[1,1,1]\nkpts = cell.make_kpts(nk)\n")

      model_line = None
      if method == None:
        method = OV.GetParam('snum.NoSpherA2.method')
      if method == "HF":
        if mult == 1:
          model_line = "scf.KRHF(cell,kpts)"
        else:
          model_line = "scf.KUHF(cell,kpts)"
      else:
        if mult == 1:
          model_line = "dft.KRKS(cell,kpts)"
        else:
          model_line = "dft.KUKS(cell,kpts)"
      #inp.write("mf = sgx.sgx_fit(%s)\n"%model_line)
      inp.write("cf = %s\n"%model_line)
      if method == "B3LYP":
        #inp.write("mf.xc = 'b3lyp'\nmf.with_df.dfj = True\n")
        inp.write("cf.xc = 'b3lyp'\n")
      elif method == "PBE":
        inp.write("cf.xc = 'pbe,pbe'\n")
      elif method == "BLYP":
        inp.write("cf.xc = 'b88,lyp'\n")
      elif method == "M062X":
        inp.write("cf.xc = 'M06X2X,M06X2C'\n")
      elif method == "PBE0":
        inp.write("cf.xc = 'PBE0'\n")
      grid_accuracy = OV.GetParam('snum.NoSpherA2.becke_accuracy')
      grid = None
      if grid_accuracy == "Low":
        grid = 0
      elif grid_accuracy == "Normal":
        grid = 0
      elif grid_accuracy == "High":
        grid = 3
      else:
        grid = 9
      #rest = "cf = cf.mix_density_fit()\ncf.grids.radi_method = dft.gauss_chebyshev\ncf.grids.level = "+str(grid)+"\n"
      rest = "cf = cf.mix_density_fit()\ncf.grids.level = "+str(grid)+"\n"
      rest += """
cf.with_df.auxbasis = 'def2-universal-jkfit'
cf.diis_space = 10
cf.with_df.linear_dep_threshold = 1e-6
cf.with_df.mesh = [21,21,21]
cf.conv_tol = 0.0033
cf.conv_tol_grad = 1e-2
cf.level_shift = 0.25
cf.damp = 0.7
cf.kernel()
print("Switching to SOSCF and shutting down damping & levelshift")
cf.conv_tol = 1e-9
cf.conv_tol_grad = 1e-5
cf.level_shift = 0.0
cf.damp = 0.0
cf = scf.newton(cf)
ener = cf.kernel()"""
      rest += "\nwith open('%s.wfn', 'w') as f1:\n  write_wfn(f1,cell,cf.mo_coeff[0],cf.mo_energy[0],cf.mo_occ[0],ener)"%self.name
      inp.write(rest)
      #inp.write("cf = cf.mix_density_fit()\ncf.with_df.auxbasis = 'weigend'\ncf.kernel()\nwith open('%s.wfn', 'w') as f1:\n  from pyscf.tools import wfn_format\n  wfn_format.write_mo(f1,cell,cf.mo_coeff, mo_energy=cf.mo_energy, mo_occ=cf.mo_occ)\n"%self.name)
      inp.close()

  @run_with_bitmap('Calculating WFN')
  def run(self,part=0,software=None,basis_name=None, copy = True):
    args = []
    if basis_name == None:
      basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    if software == None:
      software = OV.GetParam('snum.NoSpherA2.source')

    gui.get_default_notification(
          txt="Calculating Wavefunction for <font color=$GetVar(gui.green_text)><b>%s</b></font> using <font color=#000000><b>%s</b></font>..."%(self.name,software),
          txt_col='black_text')
    if OV.HasGUI():
      olx.html.Update()
      olx.xf.EndUpdate()
      olex.m('refresh')
    python_script = "fchk-launch.py"

    if software == "ORCA":
      args.append(self.parent.orca_exe)
      input_fn = self.name + ".inp"
      args.append(input_fn)
    if software == "ORCA 5.0" or software == "fragHAR" or software == "ORCA 6.0":
      args.append(self.parent.orca_exe)
      input_fn = self.name + ".inp"
      args.append(input_fn)
    elif software == "Gaussian03":
      args.append(self.parent.g03_exe)
      input_fn = self.name + ".com"
      args.append(input_fn)
    elif software == "Gaussian09":
      args.append(self.parent.g09_exe)
      input_fn = self.name + ".com"
      args.append(input_fn)
    elif software == "Gaussian16":
      args.append(self.parent.g16_exe)
      input_fn = self.name + ".com"
      args.append(input_fn)
    elif software == "Psi4":
      basis_set_fn = os.path.join(OV.BaseDir(),"basis_sets",basis_name)
      ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
      mult = OV.GetParam('snum.NoSpherA2.multiplicity')
      charge = OV.GetParam('snum.NoSpherA2.charge')
      mem = OV.GetParam('snum.NoSpherA2.mem')
      method = OV.GetParam('snum.NoSpherA2.method')
      args.append(basis_name)
      args.append(basis_set_fn)
      args.append(ncpus)
      args.append(mult)
      args.append(charge)
      args.append(mem)
      args.append(method)
      python_script = "psi4-launch.py"
    elif software == "pySCF":
      input_fn = self.name + ".py"
      if self.parent.ubuntu_exe != None and os.path.exists(self.parent.ubuntu_exe):
        args.append(self.parent.ubuntu_exe)
        args.append('run')
        args.append("python %s"%input_fn)
      elif self.parent.ubuntu_exe == None:
        args.append('python')
        args.append(input_fn)
    elif software == "ELMOdb":
      if self.parent.ubuntu_exe != None and os.path.exists(self.parent.ubuntu_exe):
        args.append(self.parent.ubuntu_exe)
        args.append('run')
        temp = self.parent.elmodb_exe
        drive = temp[0].lower()
        folder = temp[2:]
        elmodb_exe = "/mnt/"+drive+folder.replace('\\' , r'/')
        args.append(elmodb_exe)
      elif self.parent.ubuntu_exe == None:
        args.append(self.parent.elmodb_exe)
      args.append("<")
      args.append(self.name + ".inp")
      args.append(">")
      args.append(self.name + ".out")
    elif software == "xTB":
      method = OV.GetParam('snum.NoSpherA2.method')
      args.append(self.parent.xtb_exe)
      if method == "GFN0":
        args.append("--gfn")
        args.append("0")
      elif method == "GFN1":
        args.append("--gfn")
        args.append("1")
      elif method == "GFN2":
        args.append("--gfn")
        args.append("2")
      elif method == "GFNFF":
        args.append("--gfnff")
      acc = OV.GetParam("snum.NoSpherA2.becke_accuracy")
      if acc == "Low":
        args.append("--acc")
        args.append("30")
      elif acc == "Normal":
        args.append("--acc")
        args.append("1")
      elif acc == "High":
        args.append("--acc")
        args.append("0.2")
      elif acc == "Max":
        args.append("--acc")
        args.append("0.1")
      temperature = OV.GetParam("snum.NoSpherA2.temperature")
      args.append("--etemp")
      args.append(str(temperature))
      args.append("--molden")
      args.append(self.name+".xyz")
      charge = OV.GetParam("snum.NoSpherA2.charge")
      args.append("--chrg")
      args.append(str(charge))
      mult = OV.GetParam("snum.NoSpherA2.multiplicity")
      if mult != 1:
        args.append("--uhf")
        args.append(str(int(mult)-1))
    elif software == "pTB":
      method = OV.GetParam('snum.NoSpherA2.method')
      charge = OV.GetParam("snum.NoSpherA2.charge")
      mult = OV.GetParam("snum.NoSpherA2.multiplicity")
      base = os.path.dirname(self.parent.ptb_exe)
      args.append(self.parent.ptb_exe)
      args.append(self.name+".xyz")
      args.append("-stda")
      args.append("-par")
      args.append(os.path.join(base, ".atompara"))
      args.append("-bas")
      args.append(os.path.join(base, ".basis_vDZP"))
      args.append("-chrg")
      args.append(str(charge))
      if mult != 1:
        args.append("-uhf")
        args.append(str(int(mult)-1))

    out_fn = None
    path = self.full_dir
    nr = 0
    if sys.platform[:3] == 'win':
      nr = 2
    # if part != 0:
    #  path = os.path.join(path,"Part_"+str(part))
    if software == "Psi4":
      out_fn = os.path.join(path, self.name + "_psi4.log")
    else:
      if "orca" in args[0]:
        out_fn = os.path.join(path, self.name + "_orca.log")
      elif software == "ELMOdb" and "elmo" in args[nr]:
        out_fn = os.path.join(path, self.name + ".out")
      elif software == "pySCF" and"python" in args[nr]:
        out_fn = os.path.join(path, self.name + "_pyscf.log")
      if "ubuntu" in args[0]:
        print("Starting Ubuntu for wavefunction calculation, please be patient for start")
      if out_fn == None:
        if "ubuntu" in args[0]:
          out_fn = os.path.join(path, self.name + "_pyscf.log")
        else:
          out_fn = os.path.join(path, self.name + ".log")

    os.environ['fchk_cmd'] = '+&-'.join(args)
    os.environ['fchk_file'] = self.name
    os.environ['fchk_dir'] = os.path.join(OV.FilePath(), self.full_dir)
    os.environ['fchk_out_fn'] = out_fn
    pidfile = os.path.join(path, "NoSpherA2.pidfile")

    if os.path.exists(out_fn):
      print("Moving file to old!")
      shutil.move(out_fn, out_fn + '_old')
    if os.path.exists(pidfile):
      os.remove(pidfile)

    import subprocess
    p = None
    if sys.platform[:3] == 'win':
      startinfo = subprocess.STARTUPINFO()
      startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
      startinfo.wShowWindow = 7
      pyl = OV.getPYLPath()
      if not pyl:
        print("A problem with pyl is encountered, aborting.")
        return
      p = subprocess.Popen([pyl,
                            os.path.join(p_path, python_script)],
                            startupinfo=startinfo
                           )
    else:
      pyl = OV.getPYLPath()
      if not pyl:
        print("A problem with pyl is encountered, aborting.")
        return
      p = subprocess.Popen([pyl,
                            os.path.join(p_path, python_script)])

    tries = 0
    time.sleep(0.5)
    while not os.path.exists(out_fn):
      time.sleep(1)
      tries += 1
      if tries >= 5:
        if "python" in args[nr] and tries <=10:
          continue
        print("Failed to locate the output file at "+str(out_fn))
        OV.SetVar('NoSpherA2-Error',"Wfn-Output not found!")
        raise NameError('Wfn-Output not found!')

    with open(out_fn, "r") as stdout:
      while p.poll() is None:
        x = None
        try:
          x = stdout.read()
        except:
          pass
        if x:
          print(x, end='')
        if OV.GetVar("stop_current_process"):
          try:
            #import signal
            #pid = None
            # with open(pidfile, "r") as pf:
            #  line = pf.read()
            #  pid = int(line)
            #os.kill(pid, signal.SIGABRT)
            #os.kill(pid, signal.SIGTERM)
            print("Calculation aborted by INTERRUPT!")
          except Exception as e:
            print(e)
            pass
          OV.SetVar("stop_current_process", False)
        else:
          time.sleep(0.5)

    print("\nWavefunction calculation ended!")
    wfnlog = os.path.join(OV.FilePath(), self.name + ".wfnlog")
    shutil.copy(out_fn, wfnlog, follow_symlinks=False)

    if software == "ORCA 6.0" or software == "ORCA 5.0":
      if '****ORCA TERMINATED NORMALLY****' in open(wfnlog).read():
        pass
      else:
        OV.SetVar('NoSpherA2-Error',"ORCA")
        with open(wfnlog) as file:
          lines = file.readlines()
        for line in lines:
          if "Error" in line:
            print(line)
        raise NameError('Orca did not terminate normally!')
    elif "Gaussian" in software:
      if 'Normal termination of Gaussian' in open(wfnlog).read():
        pass
      else:
        OV.SetVar('NoSpherA2-Error',"Gaussian")
        raise NameError('Gaussian did not terminate normally!')
    elif software == "ELMOdb":
      if 'CONGRATULATIONS: THE ELMO-TRANSFERs ENDED GRACEFULLY!!!' in open(wfnlog).read():
        pass
      else:
        OV.SetVar('NoSpherA2-Error',"ELMOdb")
        lines = open(wfnlog).readlines()
        for line in lines:
          if "Error" in line:
            print(line)
        raise NameError('ELMOdb did not terminate normally!')
    elif software == "pTB":
      if 'cpu  time for all' in open(wfnlog).read():
        pass
      else:
        OV.SetVar('NoSpherA2-Error',"pTB")
        lines = open(wfnlog).readlines()
        for line in lines:
          if "Error" in line:
            print(line)
        raise NameError('pTB did not terminate normally!')
    embedding = OV.GetParam('snum.NoSpherA2.ORCA_USE_CRYSTAL_QMMM')
    if ("ECP" in basis_name and "orca" in args[0]) or ("orca" in args[0] and embedding == True):
      molden_args = []
      molden_args.append(os.path.join(os.path.dirname(self.parent.orca_exe), "orca_2mkl"))
      if sys.platform[:3] == 'win':
        molden_args[0] += ".exe"
      molden_args.append(self.name)
      molden_args.append("-emolden")
      if sys.platform[:3] == 'win':
        startinfo = subprocess.STARTUPINFO()
        startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startinfo.wShowWindow = 7
        m = subprocess.Popen(molden_args, cwd=self.full_dir,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             stdin=subprocess.PIPE,
                             startupinfo=startinfo)
      else:
        m = subprocess.Popen(molden_args,
                             cwd=self.full_dir,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             stdin=subprocess.PIPE)
      while m.poll() is None:
        time.sleep(1)
      n = os.path.join(self.full_dir, self.name)
      if os.path.exists(n + ".molden.input"):
        shutil.move(n + ".molden.input", n + ".molden")
      else:
        OV.SetVar('NoSpherA2-Error', "NoMoldenFile")
        raise NameError("No molden file generated!")
    if copy == True:
      if("g03" in args[0]):
        shutil.move(os.path.join(self.full_dir,"Test.FChk"),os.path.join(self.full_dir,self.name+".fchk"))
        shutil.move(os.path.join(self.full_dir,self.name + ".log"),os.path.join(self.full_dir,self.name+"_g03.log"))
        if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
          shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")
        if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfx"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".wfx"), self.name + ".wfx")
      elif("g09" in args[0]):
        shutil.move(os.path.join(self.full_dir, "Test.FChk"), os.path.join(self.full_dir, self.name + ".fchk"))
        shutil.move(os.path.join(self.full_dir, self.name + ".log"), os.path.join(self.full_dir, self.name + "_g09.log"))
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".wfn"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".wfn"), self.name + ".wfn")
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".wfx"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".wfx"), self.name + ".wfx")
      elif("g16" in args[0]):
        shutil.move(os.path.join(self.full_dir, "Test.FChk"), os.path.join(self.full_dir, self.name + ".fchk"))
        shutil.move(os.path.join(self.full_dir, self.name + ".log"), os.path.join(self.full_dir, self.name + "_g16.log"))
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".wfn"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".wfn"), self.name + ".wfn")
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".wfx"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".wfx"), self.name + ".wfx")
      elif("orca" in args[0]):
        if software == "ORCA 5.0" or software == "ORCA 6.0":
          if (os.path.isfile(os.path.join(self.full_dir, self.name + ".gbw"))):
            shutil.copy(os.path.join(self.full_dir, self.name + ".gbw"), self.name + ".gbw")
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".wfn"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".wfn"), self.name + ".wfn")
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".wfx"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".wfx"), self.name + ".wfx")
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".molden"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".molden"), self.name + ".molden")
      elif("xtb" in args[0]):
        if (os.path.isfile(os.path.join(self.full_dir, "molden.input"))):
          shutil.copy(os.path.join(self.full_dir, "molden.input"), self.name + ".molden")
          shutil.move(os.path.join(self.full_dir, "molden.input"), os.path.join(self.full_dir, self.name + ".molden"))
      elif("ptb" in args[0]):
        if (os.path.isfile(os.path.join(self.full_dir, "wfn.xtb"))):
          shutil.copy(os.path.join(self.full_dir, "wfn.xtb"), self.name + ".xtb")
          shutil.move(os.path.join(self.full_dir, "wfn.xtb"), os.path.join(self.full_dir, self.name + ".xtb"))
      elif("elmodb" in args[0]):
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".wfx"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".wfx"), self.name + ".wfx")
      elif(software == "Psi4"):
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".fchk"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".fchk"), self.name + ".fchk")
      elif software == "pySCF":
        if (os.path.isfile(os.path.join(self.full_dir, self.name + ".wfn"))):
          shutil.copy(os.path.join(self.full_dir, self.name + ".wfn"), self.name + ".wfn")

      experimental_SF = OV.GetParam('snum.NoSpherA2.NoSpherA2_SF')

      if (experimental_SF == False) and ("g" not in args[0]):
        self.convert_to_fchk()
  @run_with_bitmap("Converting to .fchk")
  def convert_to_fchk(self):
    move_args = []
    basis_dir = self.parent.basis_dir
    move_args.append(self.parent.NoSpherA2)
    move_args.append("-wfn")
    move_args.append(self.name + ".wfn")
    move_args.append("-mult")
    move_args.append(OV.GetParam('snum.NoSpherA2.multiplicity'))
    move_args.append("-b")
    move_args.append(OV.GetParam('snum.NoSpherA2.basis_name'))
    move_args.append("-d")
    if sys.platform[:3] == 'win':
      move_args.append(basis_dir.replace("/", "\\"))
    else:
      move_args.append(basis_dir + '/')
    move_args.append("-method")
    method = OV.GetParam('snum.NoSpherA2.method')
    if method == "HF":
      move_args.append("rhf")
    else:
      move_args.append("rks")
    m = subprocess.Popen(move_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    while m.poll() is None:
      time.sleep(1)
    with open("NoSpherA2.log", "r") as log:
      x = log.read()
      if x:
        print(x)
    if os.path.exists(self.name + ".fchk"):
      shutil.copy(self.name + ".fchk", os.path.join(self.full_dir, self.name + ".fchk"))
    else:
      OV.SetVar('NoSpherA2-Error', "NoFchk")
      raise NameError("No fchk generated!")
    shutil.move("NoSpherA2.log", os.path.join(self.full_dir, self.name + "_fchk.log"))
