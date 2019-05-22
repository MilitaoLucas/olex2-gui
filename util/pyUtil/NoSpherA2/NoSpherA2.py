
from olexFunctions import OlexFunctions
OV = OlexFunctions()

import os
import sys
import htmlTools
import olex
import olx
import olex_core
import gui


import time
debug = bool(OV.GetParam("olex2.debug", False))

if OV.HasGUI():
  get_template = gui.tools.TemplateProvider.get_template

instance_path = OV.DataDir()

try:
  from_outside = False
  p_path = os.path.dirname(os.path.abspath(__file__))
except:
  from_outside = True
  p_path = os.path.dirname(os.path.abspath("__file__"))

l = open(os.path.join(p_path, 'def.txt')).readlines()
d = {}
for line in l:
  line = line.strip()
  if not line or line.startswith("#"):
    continue
  d[line.split("=")[0].strip()] = line.split("=")[1].strip()

p_name = d['p_name']
p_htm = d['p_htm']
p_img = eval(d['p_img'])
p_scope = d['p_scope']

OV.SetVar('HARp_plugin_path', p_path)

from PluginTools import PluginTools as PT

from gui.images import GuiImages
GI=GuiImages()

class NoSpherA2(PT):
  def __init__(self):
    super(NoSpherA2, self).__init__()
    self.p_name = p_name
    self.p_path = p_path
    self.p_scope = p_scope
    self.p_htm = p_htm
    self.p_img = p_img
    self.deal_with_phil(operation='read')
    self.print_version_date()
    self.jobs = []
    self.parallel = False
    self.softwares = ""
    self.wfn_2_fchk = ""


    if not from_outside:
      self.setup_gui()

    self.setup_har_executables()
    self.setup_g03_executables()
    self.setup_g09_executables()
    self.setup_g16_executables()
    self.setup_orca_executables()
    self.setup_wfn_2_fchk()

    if os.path.exists(self.exe):
      self.basis_dir = os.path.join(os.path.split(self.exe)[0], "basis_sets").replace("\\", "/")
      if os.path.exists(self.basis_dir):
        basis_list = os.listdir(self.basis_dir)
        basis_list.sort()
        self.basis_list_str = ';'.join(basis_list)
      else:
        self.basis_list_str = None
    else:
      self.basis_list_str = None
      self.basis_dir = None

  def setup_har_executables(self):
    self.exe = None
    exe_pre = "hart"
    self.exe_pre = exe_pre

    if sys.platform[:3] == 'win':
      mpiloc = os.path.join(self.p_path, "mpiexec.exe")
      if os.path.exists(mpiloc):
        self.mpiexec = mpiloc
      else: 
        self.mpiexec = olx.file.Which("mpiexec.exe")

      _ = os.path.join(self.p_path, "%s_mpi.exe" %exe_pre)
      if os.path.exists(_):
        self.mpi_har = _
      else:
        self.mpi_har = olx.file.Which("%s_mpi.exe" %exe_pre)

      _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
      if os.path.exists(_):
        self.exe = _
      else:
        self.exe = olx.file.Which("%s.exe" %exe_pre)

    else:
      mpiloc = os.path.join(self.p_path, "mpiexec")
      if os.path.exists(mpiloc):
        self.mpiexec = mpiloc
      else: 
        self.mpiexec = olx.file.Which("openmpi/bin/mpiexec")
      self.mpihome = self.mpiexec[:-11]
      if 'LD_LIBRARY_PATH' in os.environ:
        if self.mpihome + 'lib' not in os.environ['LD_LIBRARY_PATH']:
          os.environ['LD_LIBRARY_PATH'] = self.mpihome + 'lib:' + self.mpihome + 'lib/openmpi' + os.environ['LD_LIBRARY_PATH']
      else:
        os.environ['LD_LIBRARY_PATH'] = self.mpihome + 'lib:' + self.mpihome + 'lib/openmpi'
      if 'LD_RUN_PATH' in os.environ:
        if self.mpihome + 'lib/openmpi' not in os.environ['LD_RUN_PATH']:
          os.environ['LD_RUN_PATH'] = self.mpihome + 'lib/openmpi' + os.environ['LD_RUN_PATH']
      else:
        os.environ['LD_RUN_PATH'] = self.mpihome + 'lib/openmpi'

      _ = os.path.join(self.p_path[:-16], "%s_mpi" %exe_pre)
      if os.path.exists(_):
        self.mpi_har = _
      else:
        self.mpi_har = olx.file.Which("%s_mpi" %exe_pre)

      _ = os.path.join(self.p_path[:-16], "%s" %exe_pre)
      if os.path.exists(_):
        self.exe = _
      else:
        self.exe = olx.file.Which("%s" %exe_pre)   

    if os.path.exists(self.mpiexec) and os.path.exists(self.mpi_har):
      self.parallel = True
      if "Tonto" not in self.softwares:
        self.softwares = self.softwares + ";Tonto"
      import multiprocessing
      max_cpu = multiprocessing.cpu_count()
      self.max_cpu = max_cpu
      cpu_list = ['1',]
      for n in range(1,max_cpu):
        cpu_list.append(str(n+1))
        self.cpu_list_str = ';'.join(cpu_list)
    else:
      if "Tonto" not in self.softwares:
        self.softwares = self.softwares + ";Tonto"
      print """
      No MPI implementation found in PATH!"""
      self.cpu_list_str = '1'

  def launch(self):

    self.jobs_dir = os.path.join(olx.FilePath(),"olex2","Wfn_job")
    if not os.path.exists(self.jobs_dir):
      os.mkdir(self.jobs_dir)

    calculate = OV.GetParam('snum.refinement.cctbx.nsff.tsc.Calculate')
    if not calculate:
      return
    if not self.basis_list_str:
      print("Could not locate usable HARt executable")
      return

    self.setup_har_executables()

    job = Job(self, olx.FileName())

    wfn_code = OV.GetParam('snum.refinement.cctbx.nsff.tsc.source')
    if wfn_code.lower().endswith(".fchk"):
      OV.SetParam('snum.refinement.cctbx.nsff.tsc.fchk_file',olx.FileName() + ".fchk")
    elif wfn_code == "Tonto":
      pass
    else:
      OV.SetParam('snum.refinement.cctbx.nsff.tsc.fchk_file',olx.FileName() + ".fchk")
      self.wfn() # Produces Fchk file in all cases that are not fchk or tonto directly

    job.launch()
    olx.html.Update()
    combine_sfs(force=True)
    if OV.GetParam('snum.refinement.cctbx.nsff.tsc.h_aniso') == True:
      olex.m("anis -h")
    OV.SetParam('snum.refinement.cctbx.nsff.tsc.Calculate',False)
    olx.html.Update()

  def wfn(self):
    if not self.basis_list_str:
      print("Could not locate usable HARt executable")
      return


    wfn_object = wfn_Job(self,olx.FileName())
    software = OV.GetParam('snum.refinement.cctbx.nsff.tsc.source')
    if software == "ORCA":
      wfn_object.write_orca_input()
    elif software == "Gaussian03":
      wfn_object.write_gX_input()
    elif software == "Gaussian09":
      wfn_object.write_gX_input()
    elif software == "Gaussian16":
      wfn_object.write_gX_input()

    wfn_object.run()

  def setup_wfn_2_fchk(self):
    exe_pre ="Wfn_2_Fchk"
    if sys.platform[:3] == 'win':
      _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
      if os.path.exists(_):
        self.wfn_2_fchk = _
      else:
        self.wfn_2_fchk = olx.file.Which("%s.exe" %exe_pre)
    else:
      _ = os.path.join(self.p_path, "%s" %exe_pre)
      if os.path.exists(_):
        self.wfn_2_fchk = _
      else:
        self.wfn_2_fchk = olx.file.Which("%s" %exe_pre)

  def setup_g09_executables(self):
    self.g09_exe = ""
    exe_pre = "g09"
    self.g09_exe_pre = exe_pre

    if sys.platform[:3] == 'win':
      _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
      if os.path.exists(_):
        self.g09_exe = _
      else:
        self.g09_exe = olx.file.Which("%s.exe" %exe_pre)

    else:
      _ = os.path.join(self.p_path, "%s" %exe_pre)
      if os.path.exists(_):
        self.g09_exe = _
      else:
        self.g09_exe = olx.file.Which("%s" %exe_pre)   
    if os.path.exists(self.g09_exe):
      if "Gaussian09" not in self.softwares:
        self.softwares = self.softwares + ";Gaussian09"

  def setup_g03_executables(self):
    self.g03_exe = ""
    exe_pre = "g03"
    self.g03_exe_pre = exe_pre

    if sys.platform[:3] == 'win':
      _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
      if os.path.exists(_):
        self.g03_exe = _
      else:
        self.g03_exe = olx.file.Which("%s.exe" %exe_pre)

    else:
      _ = os.path.join(self.p_path, "%s" %exe_pre)
      if os.path.exists(_):
        self.g03_exe = _
      else:
        self.g03_exe = olx.file.Which("%s" %exe_pre) 
    if os.path.exists(self.g03_exe):
      if "Gaussian03" not in self.softwares:
        self.softwares = self.softwares + ";Gaussian03"

  def setup_g16_executables(self):
    self.g16_exe = ""
    exe_pre = "g16"
    self.g16_exe_pre = exe_pre

    if sys.platform[:3] == 'win':
      _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
      if os.path.exists(_):
        self.g16_exe = _
      else:
        self.g16_exe = olx.file.Which("%s.exe" %exe_pre)

    else:
      _ = os.path.join(self.p_path, "%s" %exe_pre)
      if os.path.exists(_):
        self.g16_exe = _
      else:
        self.g16_exe = olx.file.Which("%s" %exe_pre) 
    if os.path.exists(self.g16_exe):
      if "Gaussian16" not in self.softwares:
        self.softwares = self.softwares + ";Gaussian16"

  def setup_orca_executables(self):
    self.orca_exe = ""
    exe_pre = "orca"
    self.orca_exe_pre = exe_pre

    if sys.platform[:3] == 'win':
      _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
      if os.path.exists(_):
        self.orca_exe = _
      else:
        self.orca_exe = olx.file.Which("%s.exe" %exe_pre)

    else:
      _ = os.path.join(self.p_path, "%s" %exe_pre)
      if os.path.exists(_):
        self.orca_exe = _
      else:
        self.orca_exe = olx.file.Which("%s" %exe_pre) 
    if os.path.exists(self.orca_exe):
      OV.SetParam('snum.refinement.cctbx.nsff.ncpus',"ORCA")
      if "ORCA" not in self.softwares:
        self.softwares = self.softwares + ";ORCA"

  def getBasisListStr(self):
    return self.basis_list_str

  def getCPUListStr(self):
    return self.cpu_list_str

  def getwfn_softwares(self):
    return self.softwares + ";"

  def available(self):
    return os.path.exists(self.exe)

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

  def __init__(self, parent, name):
    self.parent = parent
    self.status = 0
    self.name = name
    self.parallel = parent.parallel
    if self.name.endswith('_HAR'):
      self.name = self.name[:-4]
    elif self.name.endswith('_input'):
      self.name = self.name[:-6]
    full_dir = olx.FilePath()
    self.full_dir = full_dir

    if not os.path.exists(full_dir):
      return
    self.date = os.path.getctime(full_dir)
    self.log_fn = os.path.join(full_dir, name) + ".log"
    self.fchk_fn = os.path.join(full_dir, name) + ".fchk"
    self.completed = os.path.exists(self.fchk_fn)
    initialised = False

    import shutil
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

  def write_gX_input(self):
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    olx.Kill("$Q")
    olx.File(coordinates_fn)
    xyz = open(coordinates_fn,"r")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".com"
    com = open(self.input_fn,"w")
    basis_name = OV.GetParam("snum.refinement.cctbx.nsff.tsc.basis_name")
    basis_set_fn = os.path.join(self.parent.basis_dir,OV.GetParam("snum.refinement.cctbx.nsff.tsc.basis_name"))
    basis = open(basis_set_fn,"r")
    chk_destination = "%chk=" + self.name + ".chk"
    if OV.GetParam('snum.refinement.cctbx.nsff.ncpus') != '1':
      cpu = "%nproc=" + OV.GetParam('snum.refinement.cctbx.nsff.ncpus')
    else:
      cpu = "%nproc=1"
    mem = "%mem=" + OV.GetParam('snum.refinement.cctbx.nsff.mem') + "GB"
    if OV.GetParam('snum.refinement.cctbx.nsff.tsc.method') == "rhf":
      control = "# rhf/gen NoSymm 6D 10F IOp(3/32=2) formcheck"
    else:
      control = "# b3lyp/gen NoSymm 6D 10F IOp(3/32=2) formcheck"
    com.write(cpu + '\n')
    com.write(mem + '\n')
    com.write(control + '\n')
    com.write(" \n")
    title = "Wavefunction calculation for " + self.name + " on a level of theory of " + OV.GetParam('snum.refinement.cctbx.nsff.method') + "/" + OV.GetParam("snum.refinement.cctbx.tsc.basis_name")
    com.write(title + '\n')
    com.write(" " + '\n')
    charge = OV.GetParam('snum.refinement.cctbx.nsff.tsc.charge')
    com.write(charge + " 1" + '\n')
    atom_list = []
    i = 0
    for line in xyz:
      i = i+1
      if i > 2:
        atom = line.split()
        com.write(line)
        if not atom[0] in atom_list:
          atom_list.append(atom[0])
    xyz.close()
    com.write(" \n")
    for i in range(0,len(atom_list)):
      atom_type = atom_list[i] + " 0\n"
      com.write(atom_type)
      temp_atom = atom_list[i].lower() + ":" + basis_name.lower()
      basis.seek(0,0)
      while True:
        line = basis.readline()
        if line[0] == "!":
          continue
        if "keys=" in line:
          key_line = line.split(" ")
          type = key_line[key_line.index("keys=")+2]
        if temp_atom in line.lower():
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
    com.write(" ")
    com.close()

  def write_orca_input(self):
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    olx.Kill("$Q")
    olx.File(coordinates_fn,p=8)
    xyz = open(coordinates_fn,"r")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".inp"
    inp = open(self.input_fn,"w")
    basis_name = OV.GetParam('snum.refinement.cctbx.nsff.tsc.basis_name')
    print("basis_name: " + basis_name)
    print("basis_dir: " + self.parent.basis_dir)
    basis_set_fn = os.path.join(self.parent.basis_dir,basis_name)
    basis = open(basis_set_fn,"r")
    if OV.GetParam('snum.refinement.cctbx.nsff.ncpus') != '1':
      cpu = "nprocs " + OV.GetParam('snum.refinement.cctbx.nsff.ncpus')
    else:
      cpu = "nprocs 1"
    mem = OV.GetParam('snum.refinement.cctbx.nsff.mem')
    mem_value = int(mem) * 1000 / int(OV.GetParam('snum.refinement.cctbx.nsff.ncpus')) 
    mem = "%maxcore " + str(mem_value)
    if OV.GetParam('snum.refinement.cctbx.nsff.tsc.method') == "rhf":
      control = "!rhf 3-21G TightSCF Grid4 AIM"
    else:
      control = "!B3LYP 3-21G TightSCF Grid4 AIM"
    charge = OV.GetParam('snum.refinement.cctbx.nsff.tsc.charge')
    inp.write(control + '\n' + "%pal\n" + cpu + '\n' + "end\n" + mem + '\n' + "%coords\n        CTyp xyz\n        charge " + charge + "\n        mult 1\n        units angs\n        coords\n")
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
    inp.write("   end\nend\n%basis\n")
    for i in range(0,len(atom_list)):
      atom_type = "newgto " +atom_list[i] + '\n'
      inp.write(atom_type)
      temp_atom = atom_list[i].lower() + ":" + basis_name.lower()
      basis.seek(0,0)
      while True:
        line = basis.readline()
        if line[0] == "!":
          continue
        if "keys=" in line:
          key_line = line.split(" ")
          type = key_line[key_line.index("keys=")+2]
        if temp_atom in line.lower():
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
    inp.close()

  def run(self):
    args = []
    basis_name = OV.GetParam('snum.refinement.cctbx.nsff.tsc.basis_name')
    software = OV.GetParam('snum.refinement.cctbx.nsff.tsc.source')
    fchk_exe = ""
    if software == "ORCA":
      fchk_exe = self.parent.orca_exe
      input_fn = self.name + ".inp"
    elif software == "Gaussian03":
      fchk_exe = self.parent.g03_exe
      input_fn = self.name + ".com"
    elif software == "Gaussian09":
      fchk_exe = self.parent.g09_exe
      input_fn = self.name + ".com"
    elif software == "Gaussian16":
      fchk_exe = self.parent.g16_exe
      input_fn = self.name + ".com"
    args.append(fchk_exe)
    args.append(input_fn)
    if software == "ORCA":
#      args.append(">")
#      args.append(self.name + ".log")
      if os.path.exists(self.name + ".gbw"):
        os.remove(self.name + ".gbw")
    os.environ['fchk_cmd'] = '+&-'.join(args)
    os.environ['fchk_file'] = self.name
    os.environ['fchk_dir'] = self.full_dir

    import subprocess
    import time
    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      return
    p = subprocess.Popen([pyl,
                          os.path.join(p_path, "fchk-launch.py")])
    while p.poll() is None:
      time.sleep(3)

    import shutil
    if("g03" in args[0]):
      shutil.move("Test.FChk",self.name+".fchk")
      shutil.move(self.name + ".log",self.name+"_g03.log")
    if("g09" in args[0]):
      shutil.move("Test.FChk",self.name+".fchk")
      shutil.move(self.name + ".log",self.name+"_g09.log")
    if("g16" in args[0]):
      shutil.move("Test.FChk",self.name+".fchk")
      shutil.move(self.name + ".log",self.name+"_g16.log")
    if("orca" in args[0]):
      shutil.move(self.name + ".log",self.name+"_orca.log")
      move_args = []
      basis_dir = self.parent.basis_dir
      move_args.append(self.parent.wfn_2_fchk)
      move_args.append("-wfn")
      move_args.append(self.name+".wfn")
      move_args.append("-b")
      move_args.append(basis_name)
      move_args.append("-d")
      if sys.platform[:3] == 'win':
        move_args.append(basis_dir.replace("/","\\"))
      else:
        move_args.append(basis_dir)
      logname = self.name + "_wfn2fchk.log"
      log = open(logname,'w')
      os.chdir(self.full_dir)
      m = subprocess.Popen(move_args, stdout=log)
      while m.poll() is None:
        time.sleep(1)
      log.close()


class Job(object):
  origin_folder = " "
  is_copied_back = False
  date = None
  out_fn = None
  error_fn = None
  result_fn = None
  analysis_fn = None
  completed = None
  full_dir = None
  wait = "false"

  def __init__(self, parent, name):
    self.parent = parent
    self.status = 0
    self.name = name
    self.parallel = parent.parallel
    if self.name.endswith('_HAR'):
      self.name = self.name[:-4]
    elif self.name.endswith('_input'):
      self.name = self.name[:-6]
    full_dir = parent.jobs_dir
    self.full_dir = full_dir

    if not os.path.exists(full_dir):
      return
    self.date = os.path.getctime(full_dir)
    self.result_fn = os.path.join(full_dir, name) + ".archive.cif"
    self.error_fn = os.path.join(full_dir, name) + ".err"
    self.out_fn = os.path.join(full_dir, name) + ".out"
    self.dump_fn = os.path.join(full_dir, "hart.exe.stackdump")
    self.analysis_fn = os.path.join(full_dir, "stdout.fit_analysis")
    self.completed = os.path.exists(self.result_fn)
    initialised = False

  def launch(self):
    import shutil

    # Check if job folder already exists and (if needed) make the backup folders
    if os.path.exists(self.full_dir):
      self.backup = os.path.join(self.full_dir, "backup")
      i = 1
      while (os.path.exists(self.backup + "_%d"%i)):
        i = i + 1
      self.backup = self.backup + "_%d"%i
      os.mkdir(self.backup)
      try:
        files = (file for file in os.listdir(self.full_dir)
                 if os.path.isfile(os.path.join(self.full_dir, file)))
        for f in files:
          f_work = os.path.join(self.full_dir,f)
          f_dest = os.path.join(self.backup,f)
          shutil.move(f_work,f_dest)
      except:
        pass
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

    model_file_name = os.path.join(self.full_dir, self.name) + ".cif"
    olx.Kill("$Q")
    olx.File(model_file_name)

    data_file_name = os.path.join(self.full_dir, self.name) + ".hkl"
    if not os.path.exists(data_file_name):
      from cctbx_olex_adapter import OlexCctbxAdapter
      from iotbx.shelx import hklf
      cctbx_adaptor = OlexCctbxAdapter()
      with open(data_file_name, "w") as out:
        f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_filtered
        for j, h in enumerate(f_sq_obs.indices()):
          s = f_sq_obs.sigmas()[j]
          if s <= 0: f_sq_obs.sigmas()[j] = 0.01
          i = f_sq_obs.data()[j]
          if i < 0: f_sq_obs.data()[j] = 0
        f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)

    # We are asking to just get form factors to disk
    fchk_source = OV.GetParam('snum.refinement.cctbx.nsff.tsc.source')
    if fchk_source == "Tonto":
      # We want these from a wavefunction calculation using TONTO """

      args = [self.name+".cif",
              "-basis-dir", self.parent.basis_dir,
              "-shelx-f2", self.name+".hkl"
              ,"-scf", OV.GetParam('snum.refinement.cctbx.nsff.tsc.method')
              ,"-basis", OV.GetParam('snum.refinement.cctbx.nsff.tsc.basis_name')
              ,"-cluster-radius", str(OV.GetParam('snum.refinement.cctbx.nsff.tsc.cluster_radius'))
              ]
      clustergrow = OV.GetParam('snum.refinement.cctbx.nsff.tsc.cluster_grow')
      if clustergrow == False:
        args.append("-complete-mol")
        args.append("f")

    else:
      # We want these from supplied fchk file """
      fchk_file = OV.GetParam('snum.refinement.cctbx.nsff.tsc.fchk_file')
      shutil.copy(fchk_file,os.path.join(self.full_dir,self.name+".fchk"))
      args = [self.name+".cif",
              "-shelx-f2", self.name+".hkl ",
              "-fchk", fchk_file]    

    if OV.GetParam('snum.refinement.cctbx.nsff.ncpus') != '1':
      args = [self.parent.mpiexec, "-np", OV.GetParam('snum.refinement.cctbx.nsff.ncpus'), self.parent.mpi_har] + args
    else:
      args = [self.parent.exe] + args

    if OV.GetParam('snum.refinement.cctbx.nsff.tsc.charge') != '0':
      args.append("-charge")
      args.append(OV.GetParam('snum.refinement.cctbx.nsff.tsc.charge'))
    disp = olx.GetVar("settings.tonto.HAR.dispersion", None)
    if 'true' == disp:
      import olexex
      from cctbx.eltbx import henke
      olex_refinement_model = OV.GetRefinementModel(False)
      sfac = olex_refinement_model.get('sfac')
      fp_fdps = {}
      wavelength = olex_refinement_model['exptl']['radiation']
      if sfac is not None:
        for element, sfac_dict in sfac.iteritems():
          custom_fp_fdps.setdefault(element, sfac_dict['fpfdp'])
      asu = olex_refinement_model['aunit']
      for residue in asu['residues']:
        for atom in residue['atoms']:
          element_type = atom['type']
          if element_type not in fp_fdps:
            fpfdp = henke.table(str(element_type)).at_angstrom(wavelength).as_complex()
            fp_fdps[element_type] = (fpfdp.real, fpfdp.imag)
      disp_arg = " ".join(["%s %s %s" %(k, v[0], v[1]) for k,v in fp_fdps.iteritems()])
      args.append("-dispersion")
      args.append('%s' %disp_arg)

    self.result_fn = os.path.join(self.full_dir, self.name) + ".archive.cif"
    self.error_fn = os.path.join(self.full_dir, self.name) + ".err"
    self.out_fn = os.path.join(self.full_dir, self.name) + ".out"
    self.dump_fn = os.path.join(self.full_dir, "hart.exe.stackdump")
    self.analysis_fn = os.path.join(self.full_dir, "stdout.fit_analysis")
    os.environ['hart_cmd'] = '+&-'.join(args)
    os.environ['hart_file'] = self.name
    os.environ['hart_dir'] = self.full_dir
    OV.SetParam('snum.refinement.cctbx.nsff.name',self.name)
    OV.SetParam('snum.refinement.cctbx.nsff.dir',self.full_dir)
    OV.SetParam('snum.refinement.cctbx.nsff.cmd', args)


    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      return
    import subprocess
    p = subprocess.Popen([pyl,
                          os.path.join(p_path, "HARt-launch.py")])
    while p.poll() is None:
      time.sleep(3)

def combine_sfs(force=False):
  import glob
  import math

  if debug:
    t_beg = time.time()
  sfc_dir = OV.GetParam('snum.refinement.cctbx.nsff.dir')
  sfc_name = OV.GetParam('snum.refinement.cctbx.nsff.name')
  tsc_modular = OV.GetParam('snum.refinement.cctbx.nsff.tsc.modular')
  tsc_source = OV.GetParam('snum.refinement.cctbx.nsff.tsc.source')
  tsc_file = OV.GetParam('snum.refinement.cctbx.nsff.tsc.file')

  if not force:
    if tsc_file.endswith(".tsc"):
      return

  if not sfc_dir:
    return
  _mod = ""
  if not tsc_modular == "direct":
    _mod = "_%s"%tsc_modular
  tsc_fn = os.path.join(sfc_dir, sfc_name + _mod + "_" + tsc_source + ".tsc")
  tsc_dst = os.path.join(OV.FilePath(), sfc_name + _mod + "_" + tsc_source + ".tsc")

  if tsc_file == "Check for new":
    if os.path.exists(tsc_fn) and os.path.exists(tsc_dst):
      if "%0.f" %os.path.getctime(tsc_fn) == "%0.f" %os.path.getctime(tsc_dst):
        print ("No new .tsc files")
        olx.html.SetValue('SNUM_REFINEMENT_NSFF_TSC_FILE',  os.path.basename(tsc_dst))
        return
      else:
        print ("Creating newer %s file" %tsc_dst)

      t =  time.ctime(os.path.getmtime(tsc_dst))
      OV.write_to_olex("%s_tsc_file_info"%OV.FileName() , t)

  if os.path.exists(tsc_dst):
    backup = os.path.join(OV.FilePath(), "tsc_backup")
    if not os.path.exists(backup):
      os.mkdir(backup)
    i = 1
    while (os.path.exists(os.path.join(backup,sfc_name + _mod + "_" + tsc_source + ".tsc") + "_%d"%i)):
      i = i + 1
    try:
      from shutil import move
      move(tsc_dst,os.path.join(backup,sfc_name + _mod + "_" + tsc_source + ".tsc") + "_%d"%i)
    except:
      pass

  p = os.path.join(sfc_dir, "*,ascii")
  g = glob.glob(p)
  d = {}
  if not g:
    return False

  if debug:
    t1 = time.time()
  for file_p in g:
    if "SFs_key,ascii" in file_p:
      sfs_fp = file_p
      continue
    elif "Symops,ascii" in file_p:
      symops_fp = file_p
      continue
    name = os.path.basename(file_p).split("_")[0]
    d.setdefault(name,{})
    values = open(file_p,'r').read().splitlines()
    sfc_l = []
    for line in values:
      if tsc_modular == "modulus":
        _ = line.split()
        a = float(_[0])
        b = float(_[1])
        v = math.sqrt(a*a + b*b)
        sfc_l.append("%.6f" %v)
      elif tsc_modular == "absolute":
        _ = line.split()
        a = abs(float(_[0]))
        b = abs(float(_[1]))
        sfc_l.append(",".join(["%.5f" %a, "%.5f" %b]))
      elif tsc_modular == "direct":
        _ = line.split()
        a = float(_[0])
        b = float(_[1])
        sfc_l.append(",".join(["%.5f" %a, "%.5f" %b]))

    d[name].setdefault('sfc', sfc_l)
    d[name].setdefault('name', name)

  sym = open(symops_fp,'r').read().splitlines()
  sym_l = []
  ll = []
  for line in sym:
    if line:
      li = line.split()
      for val in li:
        ll.append(str(int(float((val)))))
    else:
      sym_l.append(" ".join(ll))
      ll = []

  if debug:
    print ("Time for reading and processing the separate files: %.2f" %(time.time() - t1))

  #hkl_fn = os.path.join(OV.FilePath(), OV.FileName() + ".hkl")
  hkl_fn = "SFs_key,ascii"
  hkl = open(sfs_fp, 'r').read().splitlines()
  hkl_l = []  
  for line in hkl:
    hkl_l.append(" ".join(line.split()[0:3]))
  d.setdefault('hkl', hkl_l)

  values_l = []
  values_l.append(d['hkl'])
  scatterers_l = []
  for item in d:
    if item == "hkl":
      continue
    scatterers_l.append(d[item]['name'])
    values_l.append(d[item]['sfc'])
  tsc_l = zip(*values_l)

  ol = []
  _d = {'anomalous':'false',
        'title': OV.FileName(),
        'symmops': ";".join(sym_l),
        'scatterers': " ".join(scatterers_l),
        }
  ol.append('TITLE: %(title)s'%_d)
  ol.append('SYMM: %(symmops)s'%_d)
  ol.append('AD ACCOUNTED: %(anomalous)s'%_d)
  ol.append('SCATTERERS: %(scatterers)s'%_d)
  ol.append('QM Info:')
  software = OV.GetParam('snum.refinement.cctbx.nsff.tsc.source')
  method = OV.GetVar('settings.tonto.HAR.method')
  basis_set = OV.GetVar('settings.tonto.HAR.basis.name')
  charge = OV.GetParam('snum.refinement.cctbx.nsff.tsc.charge')
  date = str(os.path.getctime(os.path.join(sfc_dir,"SFs_key,ascii")))
  ol.append('   SOFTWARE:  %s'%software)
  ol.append('   METHOD:    %s'%method)
  ol.append('   BASIS SET: %s'%basis_set)
  ol.append('   CHARGE:    %s'%charge)
  ol.append('   DATE:      %s'%date)

  ol.append("data:")

  for line in tsc_l:
    ol.append(" ".join(line))

  t = "\n".join(ol)
  with open(tsc_fn, 'w') as wFile:
    wFile.write(t)

  from shutil import copyfile
  copyfile(tsc_fn, tsc_dst)
  try:
    OV.SetParam('snum.refinement.cctbx.nsff.tsc.file', tsc_dst)
    olx.html.SetValue('SNUM_REFINEMENT_NSFF_TSC_FILE', os.path.basename(tsc_dst))
  except:
    pass
  olx.html.Update()
  if debug:
    print("Total time: %.2f"%(time.time() - t_beg))
  return True

OV.registerFunction(combine_sfs,True,'har')

NoSpherA2_instance = NoSpherA2()
OV.registerFunction(NoSpherA2_instance.available, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.launch, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getBasisListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getCPUListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getwfn_softwares, False, "NoSpherA2")
#print "OK."