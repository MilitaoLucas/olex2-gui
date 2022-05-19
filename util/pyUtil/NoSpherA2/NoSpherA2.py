import os
import sys
import htmlTools
import olex
import olx
import olex_core
import gui
import shutil
import time
import math
import OlexVFS
from PIL import ImageDraw, Image
from ImageTools import IT

from olexFunctions import OV
debug = OV.IsDebugging()

#Local imports for NoSpherA2 functions
import Wfn_Job
import ELMO
import cubes_maps

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

from PluginTools import PluginTools as PT

from gui.images import GuiImages
GI=GuiImages()

def scrub(cmd):
  log = gui.tools.LogListen()
  olex.m(cmd)
  return log.endListen()

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
    self.f_calc = None
    self.f_obs_sq = None
    self.one_h_linearisation = None
    self.reflection_date = None
    self.jobs_dir = os.path.join("olex2","Wfn_job")
    self.history_dir = os.path.join("olex2","NoSpherA2_history")

    if not from_outside:
      self.setup_gui()

#   Attempts to find all known types of software to be used during NoSpherA2 runs
    self.setup_har_executables()
    self.setup_pyscf()
    self.setup_discamb()
    self.setup_elmodb()
    self.setup_psi4()
    self.setup_g03_executables()
    self.setup_g09_executables()
    self.setup_g16_executables()
    self.setup_orca_executables()
    self.setup_wfn_2_fchk()

    import platform
    if platform.architecture()[0] != "64bit":
      print ("Warning: Detected 32bit Olex2, NoSpherA2 only works on 64 bit OS.")

    if os.path.exists(self.wfn_2_fchk):
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
      print("No NoSpherA2 executable found!")
    print(" ")
    
  def set_f_calc(self, f_calc):
    self.f_calc = f_calc
    
  def set_f_obs_sq(self, f_obs_sq):
    self.f_obs_sq = f_obs_sq
    
  def set_one_h_linearization(self, one_h_linarization):
    self.one_h_linearisation = one_h_linarization
    
  def set_f_calc_obs_sq_one_h_linearisation(self,f_calc,f_obs_sq,one_h_linarization):
    self.f_calc = f_calc
    self.f_obs_sq = f_obs_sq
    self.one_h_linearisation = one_h_linarization
    file_name = OV.GetParam("snum.NoSpherA2.file")
    time = os.path.getmtime(file_name)
    self.reflection_date = time
  
  def delete_f_calc_f_obs_one_h(self):
    self.f_calc = None
    self.f_obs_sq = None
    self.one_h_linearisation = None
    self.reflection_date = None

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
        self.mpiexec = olx.file.Which("mpiexec")
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
      OV.SetVar("Parallel",True)
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
      print("No MPI implementation found in PATH!\n")
      self.cpu_list_str = '1'

  def tidy_wfn_jobs_folder(self, part=None):
    if part == None:
      self.backup = os.path.join(self.jobs_dir, "backup")
      to_backup = self.jobs_dir
      self.wfn_job_dir = self.jobs_dir
    else:
      self.backup = os.path.join(self.jobs_dir, "Part_%d" % part, "backup")
      to_backup = os.path.join(self.jobs_dir, "Part_%d" % part)
      self.wfn_job_dir = os.path.join(self.jobs_dir, "Part_%d" % part)
    if os.path.exists(to_backup):
      l = 1
      while (os.path.exists(self.backup + "_%d"%l)):
        l = l + 1
      self.backup = self.backup + "_%d"%l
      os.mkdir(self.backup)
    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')

    if os.path.exists(os.path.join(self.jobs_dir,olx.FileName()+".hkl")):
      run = None
      if Full_HAR == True:
        run = OV.GetVar('Run_number')
      files = (file for file in os.listdir(self.wfn_job_dir)
              if os.path.isfile(os.path.join(self.wfn_job_dir, file)))
      for f in files:
        f_work = os.path.join(self.wfn_job_dir,f)
        f_dest = os.path.join(self.backup,f)
        if Full_HAR == True:
          if run > 0:
            if self.wfn_code == "Tonto":
              if "restricted" not in f:
                shutil.move(f_work,f_dest)
            elif self.wfn_code == "ORCA":
              if ".gbw" not in f:
                shutil.move(f_work, f_dest)
              else:
                shutil.move(os.path.join(self.wfn_job_dir, f), os.path.join(self.wfn_job_dir, self.name + "2.gbw"))
            elif self.wfn_code == "ORCA 5.0":
              if ".gbw" not in f:
                shutil.move(f_work,f_dest)
              else:
                shutil.move(os.path.join(self.wfn_job_dir, f), os.path.join(self.wfn_job_dir, self.name + "2.gbw"))
            elif "Gaussian" in self.wfn_code:
              if ".chk" not in f:
                shutil.move(f_work,f_dest)
            elif "ELMOdb" in self.wfn_code:
              if ".wfx" not in f:
                shutil.move(f_work,f_dest)
            elif "pySCF" in self.wfn_code:
              if ".chk" not in f:
                shutil.move(f_work,f_dest)
            else:
                shutil.move(f_work,f_dest)
          else:
            shutil.move(f_work,f_dest)
        else:
          shutil.move(f_work,f_dest)    
  def launch(self):
    OV.SetVar('NoSpherA2-Error',"None")
    wfn_code = OV.GetParam('snum.NoSpherA2.source')
    self.wfn_code = wfn_code
    self.name = olx.FileName()
    basis = OV.GetParam('snum.NoSpherA2.basis_name')
    update = OV.GetParam('snum.NoSpherA2.Calculate')
    experimental_SF = OV.GetParam('snum.NoSpherA2.wfn2fchk_SF')
    if "Please S" in wfn_code and update == True:
      olx.Alert("No tsc generator selected",\
"""Error: No generator for tsc files selected.
Please select one of the generators from the drop-down menu.""", "O", False)
      OV.SetVar('NoSpherA2-Error',"TSC Generator unselected")
      return
    if not os.path.exists(self.jobs_dir):
      os.mkdir(self.jobs_dir)
    if not os.path.exists(self.history_dir):
      os.mkdir(self.history_dir)

    if not update:
      return
    if self.wfn_2_fchk == "":
      print("Could not locate usable NoSpherA2 executable")
      return

    tsc_exists = False
    f_time = None

    if (wfn_code != "DISCAMB") and (olx.xf.latt.IsGrown() != 'true') and is_disordered() == False:
      from cctbx_olex_adapter import OlexCctbxAdapter
      ne = -int(OV.GetParam('snum.NoSpherA2.charge'))
      for sc in OlexCctbxAdapter().xray_structure().scatterers():
        Z = sc.electron_count()
        if (Z > 36) and ("x2c" not in basis) and ("jorge" not in basis):
          print("Atoms with Z > 36 require x2c basis sets!")
          OV.SetVar('NoSpherA2-Error',"Heavy Atom but no heavy atom basis set!")
          return False
        ne += Z
      mult = int(OV.GetParam('snum.NoSpherA2.multiplicity'))
      if (ne % 2 == 0) and (mult % 2 == 0):
        print ("Error! Multiplicity and number of electrons is even. This is impossible!\n")
        OV.SetVar('NoSpherA2-Error',"Multiplicity")
        return False
      elif (ne % 2 == 1) and (mult % 2 == 1):
        print ("Error! Multiplicity and number of electrons is uneven. This is impossible!\n")
        OV.SetVar('NoSpherA2-Error',"Multiplicity")
        return False
      if (wfn_code == "ELMOdb") and (mult > 1):
        print ("Error! Multiplicity is not 1. This is currently not supported in ELMOdb. Consider using QM/ELMO instead!\n")
        OV.SetVar('NoSpherA2-Error',"Multiplicity")
        return False


    if OV.GetParam('snum.NoSpherA2.no_backup') == False:
      for file in os.listdir(olx.FilePath()):
        if file.endswith(".tsc"):
          tsc_exists = True
          f_time = os.path.getmtime(file)
      if tsc_exists and ".wfn" not in wfn_code:
        import datetime
        timestamp_dir = os.path.join(self.history_dir,olx.FileName() + "_" + datetime.datetime.fromtimestamp(f_time).strftime('%Y-%m-%d_%H-%M-%S'))
        if not os.path.exists(timestamp_dir):
          os.mkdir(timestamp_dir)
        for file in os.listdir('.'):
          if file.endswith(".tsc") or (file.endswith(".wfn") and ("wfn" not in wfn_code)) or file.endswith(".wfx") or file.endswith(".ffn") or file.endswith(".fchk"):
            shutil.move(os.path.join(olx.FilePath(),file),os.path.join(timestamp_dir,file))

    olex.m("CifCreate")

    parts = OV.ListParts()
    if parts != None:
      parts = list(parts)

    nr_parts = None
    groups = None
    if not parts:
      nr_parts = 1
    elif len(parts) > 1:
      olx.Kill("$Q")
      cif = False
      if wfn_code == "Tonto":
        cif = True
      elif wfn_code == "DISCAMB":
        cif = True
      olx.File(os.path.join(self.jobs_dir, "%s.cif" % (self.name)))
      parts, groups = deal_with_parts()
      nr_parts = len(parts)

    if nr_parts > 1:
      #groups = []
      #for x in range(nr_parts):
      #  if (parts[x] != 0): 
      #    groups.append([])
      wfn_files = []
      need_to_combine = False
      need_to_partition = False
      if ".wfn" in wfn_code:
        print("Calcualtion from wfn with disorder not possible, sorry!\n")
        return
      groups_counter = 0
      for i in range(nr_parts):
        if parts[i] == 0:
          groups_counter+=1
          continue
        # Check if job folder already exists and (if needed) make the backup folders
        self.tidy_wfn_jobs_folder(parts[i])
        if wfn_code.lower().endswith(".fchk"):
          raise NameError('Disorder is not possible with precalculated fchks!')
        try:
          os.mkdir(self.wfn_job_dir)
        except:
          pass
        atom_loop_reached = False
        out_cif = open(os.path.join(self.wfn_job_dir,"%s.cif"%(OV.ModelSrc())),"w")
        with open(os.path.join(OV.FilePath(),"%s.cif" %(OV.ModelSrc())),"r") as incif:
          for line in incif:
            if "_atom_site_disorder_group" in line:
              atom_loop_reached = True
              out_cif.write(line)
            elif atom_loop_reached == True:
              if line != '\n':
                temp = line.split(' ')
                if (temp[11].replace('\n','') in groups[i-groups_counter]) or (temp[11]==".\n"):
                  out_cif.write("%s %s %s %s %s %s %s %s 1 . 1 .\n" %(temp[0], temp[1], temp[2], temp[3], temp[4], temp[5], temp[6], temp[7]))
              else:
                atom_loop_reached = False
                out_cif.write('\n')
            else:
              out_cif.write(line)

        out_cif.close()
        if wfn_code == "DISCAMB":
          discamb(os.path.join(OV.FilePath(), self.wfn_job_dir), self.name, self.discamb_exe)
          shutil.copy(os.path.join(self.wfn_job_dir, self.name + ".tsc"), self.name + "_part_" + str(parts[i]) + ".tsc")
          shutil.copy(os.path.join(self.wfn_job_dir, "discamb2tsc.log"), os.path.join(self.jobs_dir, "discamb2tsc.log"))
          need_to_combine = True
        elif wfn_code == "Hybrid":
          hybrid_part_wfn_code = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d"%(parts[i]))
          if hybrid_part_wfn_code == "DISCAMB":
            groups.pop(i-groups_counter)
            groups_counter+=1
            discamb(os.path.join(OV.FilePath(), self.wfn_job_dir), self.name, self.discamb_exe)
            shutil.copy(os.path.join(self.wfn_job_dir, self.name + ".tsc"), self.name + "_part_" + str(parts[i]) + ".tsc")
            shutil.copy(os.path.join(self.wfn_job_dir, "discamb2tsc.log"), os.path.join(self.jobs_dir, "discamb2tsc.log"))
            need_to_combine = True
          else:
            need_to_partition = True
            shutil.move("%s_part_%s.xyz" % (self.name, parts[i]), os.path.join(self.wfn_job_dir, "%s.xyz" % (self.name)))
            try:
              self.wfn(folder=self.wfn_job_dir,xyz=False,part=parts[i])
            except NameError as error:
              print ("Aborted due to: ",error)
              OV.SetVar('NoSpherA2-Error',error)
              return False         
            path_base = os.path.join(OV.FilePath(), self.wfn_job_dir, self.name)
            if os.path.exists(path_base+".wfx"):
              wfn_fn = path_base+".wfx"
            elif os.path.exists(path_base+".fchk"):
              wfn_fn = path_base+".fchk"
            elif os.path.exists(path_base+".wfn"):
              wfn_fn = path_base+".wfn"
            else:
              return False
            wfn_fn = None
            #groups[i-groups_counter].append(0)
            #groups[i-groups_counter].append(parts[i])
            for file in os.listdir(self.wfn_job_dir):
              temp = None
              if file.endswith(".wfn"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfn"
              elif file.endswith(".wfx"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfx"
                if (wfn_fn == None or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".fchk")): wfn_fn = temp
              elif file.endswith(".ffn"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".ffn"
              elif file.endswith(".fchk"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".fchk"
                if (wfn_fn == None or wfn_fn.endswith(".wfn")): wfn_fn = temp
              if temp != None:
                shutil.move(file,temp)
            wfn_files.append(wfn_fn)
        else:
          need_to_partition = True
          if wfn_code != "Tonto":
            shutil.move("%s_part_%s.xyz" % (self.name, parts[i]), os.path.join(self.wfn_job_dir, "%s.xyz" % (self.name)))
            if wfn_code == "ELMOdb":
              mutation = OV.GetParam('snum.NoSpherA2.ELMOdb.mutation')
              pdb_name = job.name + ".pdb"
              if mutation == True:
                pdb_name += "_mut"+str(parts[i])
              if os.path.exists(os.path.join(OV.FilePath(),pdb_name)):
                shutil.copy(os.path.join(OV.FilePath(), pdb_name), os.path.join(self.wfn_job_dir, self.name + ".pdb"))
              else:
                OV.SetVar('NoSpherA2-Error',"ELMOdb")
                if mutation == True:
                  raise NameError('No pdb_name file available for mutation!')
                else:
                  raise NameError('No pdb file available! Make sure the name of the pdb file is the same as the name of your ins file!')
            OV.SetParam('snum.NoSpherA2.fchk_file', self.name + ".fchk")
            try:
              self.wfn(folder=self.wfn_job_dir,xyz=False,part=parts[i]) # Produces Fchk file in all cases that are not fchk or tonto directly
            except NameError as error:
              print ("Aborted due to: ",error)
              OV.SetVar('NoSpherA2-Error',error)
              return False
          if experimental_SF == False or wfn_code == "Tonto":
            job = Job(self, self.name)
            try:
              job.launch(self.wfn_job_dir)
            except NameError as error:
              print ("Aborted due to: ", error)
              OV.SetVar('NoSpherA2-Error',error)
              return False
            if 'Error in' in open(os.path.join(job.full_dir, job.name+".err")).read():
              OV.SetVar('NoSpherA2-Error', "StructureFactor")
              return False
            olx.html.Update()
            shutil.copy(os.path.join(job.full_dir, self.name + ".tsc"), self.name + "_part_" + str(parts[i]) + ".tsc")
          elif wfn_code == "Thakkar IAM":
            wfn_fn = os.path.join(OV.FilePath(), self.wfn_job_dir, self.name + ".xyz")
          elif wfn_code == "fragHAR":
            return
          else:
            wfn_fn = None
            path_base = os.path.join(OV.FilePath(), self.wfn_job_dir, self.name)
            if os.path.exists(path_base+".wfx"):
              wfn_fn = path_base+".wfx"
            elif os.path.exists(path_base+".fchk"):
              wfn_fn = path_base+".fchk"
            elif os.path.exists(path_base+".wfn"):
              wfn_fn = path_base+".wfn"
            else:
              return False
          for file in os.listdir(os.getcwd()):
            temp = None
            if file.endswith(".wfn"):
              temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfn"
            elif file.endswith(".wfx"):
              temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfx"
              if (wfn_fn == None or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".fchk")): wfn_fn = temp
            elif file.endswith(".ffn"):
              temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".ffn"
            elif file.endswith(".fchk"):
              temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".fchk"
              if (wfn_fn == None): 
                wfn_fn = temp
            if temp != None:
              shutil.move(file,temp)
          wfn_files.append(wfn_fn)
      if need_to_partition == True:
        cif_fn = os.path.join(OV.FilePath(), self.name + ".cif")
        hkl_fn = os.path.join(self.jobs_dir, self.name + ".hkl")
        run_with_bitmap("Partitioning", cuqct_tsc, wfn_files, hkl_fn, cif_fn, groups)
        if os.path.exists("experimental.tsc"):
          shutil.move("experimental.tsc", self.name + ".tsc")
        if os.path.exists("experimental.tscb"):
          shutil.move("experimental.tscb", self.name + ".tscb")
          OV.SetParam('snum.NoSpherA2.file', self.name + ".tscb")
        else:
          OV.SetParam('snum.NoSpherA2.file', self.name + ".tsc")
      if need_to_combine == True:
        #Too lazy to properly do it...
        if os.path.exists(self.name + ".tsc"):
          shutil.move(self.name + ".tsc", self.name + "_part_999.tsc")
        combine_tscs()
      
    else:
      # Check if job folder already exists and (if needed) make the backup folders
      self.tidy_wfn_jobs_folder()

      # Make a wavefunction (in case of tonto wfn code and tonto tsc file do it at the same time)

      if wfn_code == "DISCAMB":
        cif = str(os.path.join(self.jobs_dir, self.name + ".cif"))
        olx.File(cif)
        discamb(os.path.join(OV.FilePath(), self.jobs_dir), self.name, self.discamb_exe)
        shutil.copy(os.path.join(OV.FilePath(), self.jobs_dir, self.name + ".tsc"), self.name + ".tsc")
        OV.SetParam('snum.NoSpherA2.file', self.name + ".tsc")
      else:
        if wfn_code.lower().endswith(".wfn"):
          pass
        elif wfn_code == "Tonto":
          job = Job(self, self.name)
          success = True
          try:
            job.launch()
          except NameError as error:
            print("Aborted due to: ", error)
            success = False
          if 'Error in' in open(os.path.join(job.full_dir, job.name+".err")).read():
            success = False
            with open(os.path.join(job.full_dir, job.name+".err")) as file:
              for i in file.readlines():
                if 'Error in' in i:
                  print(i)
            OV.SetVar('NoSpherA2-Error',"StructureFactor")
            return False
          if success == False:
            OV.SetVar('NoSpherA2-Error',"Tonto")
            return False
          olx.html.Update()
          if (experimental_SF == False):
            shutil.copy(os.path.join(job.full_dir, job.name+".tsc"),job.name+".tsc")
            OV.SetParam('snum.NoSpherA2.file',job.name+".tsc")
        else:
          if wfn_code == "ELMOdb":
            # copy the pdb
            if os.path.exists(os.path.join(OV.FilePath(), self.name + ".pdb")):
              shutil.copy(os.path.join(OV.FilePath(), self.name + ".pdb"), os.path.join(self.jobs_dir, self.name + ".pdb"))
            else:
              OV.SetVar('NoSpherA2-Error',"ELMOdb")
              raise NameError('No pdb file available! Make sure the name of the pdb file is the same as the name of your ins file!')
          try:
            self.wfn(folder=self.jobs_dir) # Produces Fchk file in all cases that are not fchk or tonto directly
          except NameError as error:
            print("Aborted due to: ",error)
            OV.SetVar('NoSpherA2-Error',error)
            return False

        # make the tsc file

        if (experimental_SF == True):
          if wfn_code != "fragHAR":
            path_base = os.path.join(self.jobs_dir, self.name)
            if wfn_code.lower().endswith(".wfn"):
              wfn_fn = wfn_code
            elif os.path.exists(path_base+".wfx"):
              wfn_fn = path_base+".wfx"
            elif os.path.exists(path_base+".fchk"):
              wfn_fn = path_base+".fchk"
            elif os.path.exists(path_base+".wfn"):
              wfn_fn = path_base+".wfn"
            elif wfn_code == "Thakkar IAM":
              wfn_fn = path_base+".xyz"
            else:
              return False
            hkl_fn = path_base+".hkl"
            cif_fn = os.path.join(OV.FilePath(), self.name + ".cif")
            run_with_bitmap("Partitioning", cuqct_tsc, wfn_fn, hkl_fn, cif_fn, [-1000])
            if os.path.exists("experimental.tsc"):
              shutil.move("experimental.tsc", self.name + ".tsc")
            if os.path.exists("experimental.tscb"):
              shutil.move("experimental.tscb", self.name + ".tscb")
              OV.SetParam('snum.NoSpherA2.file', self.name + ".tscb")
            else:
              OV.SetParam('snum.NoSpherA2.file', self.name + ".tsc")

        elif wfn_code != "Tonto":
          job = Job(self, self.name)
          success = True
          try:
            job.launch()
          except NameError as error:
            print("Aborted due to: ", error)
            success = False
          if 'Error in' in open(os.path.join(job.full_dir, job.name+".err")).read():
            success = False
            with open(os.path.join(job.full_dir, job.name+".err")) as file:
              for i in file.readlines():
                if 'Error in' in i:
                  print(i)
            OV.SetVar('NoSpherA2-Error',"StructureFactor")
            return False
          if success == False:
            OV.SetVar('NoSpherA2-Error',"Tonto")
            return False
          olx.html.Update()
          shutil.copy(os.path.join(job.full_dir, job.name+".tsc"),job.name+".tsc")
          OV.SetParam('snum.NoSpherA2.file',job.name+".tsc")
    #add_info_to_tsc()

  def wfn(self,folder='',xyz=True,part=0):
    if not self.basis_list_str:
      print("Could not locate usable HARt executable")
      return
    wfn_object = Wfn_Job.wfn_Job(self, olx.FileName(), dir=folder)
    software = OV.GetParam('snum.NoSpherA2.source')
    if software == "fragHAR":
      from .fragHAR import run_frag_HAR_wfn
      main_folder = OV.FilePath()
      fn = olx.FileName()
      res_file = os.path.join(main_folder, fn + ".res")
      cif_file = os.path.join(main_folder, fn + ".cif")
      qS_file = os.path.join(main_folder, fn + ".qS")
      run_frag_HAR_wfn(res_file, cif_file, qS_file, wfn_object, part)
      return
    elif software == "ORCA":
      wfn_object.write_orca_input(xyz)
    elif software == "ORCA 5.0":
      embedding = OV.GetParam('snum.NoSpherA2.ORCA_USE_CRYSTAL_QMMM')
      if embedding == True:
        wfn_object.write_orca_crystal_input(xyz)
      else:
        wfn_object.write_orca_input(xyz)
    elif software == "Gaussian03":
      wfn_object.write_gX_input(xyz)
    elif software == "Gaussian09":
      wfn_object.write_gX_input(xyz)
    elif software == "Gaussian16":
      wfn_object.write_gX_input(xyz)
    elif software == "pySCF":
      wfn_object.write_pyscf_script(xyz)
    elif software == "ELMOdb":
      wfn_object.write_elmodb_input(xyz)
    elif software == "Psi4":
      wfn_object.write_psi4_input(xyz)
    elif software == "Thakkar IAM":
      wfn_object.write_xyz_file()
    elif software == "Hybrid":
      software_part = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d"%part)
      basis_part = OV.GetParam("snum.NoSpherA2.Hybrid.basis_name_Part%d"%part)
      method_part = OV.GetParam("snum.NoSpherA2.Hybrid.method_Part%d"%part)
      relativistc = OV.GetParam("snum.NoSpherA2.Hybrid.Relativistic_Part%d"%part)
      charge = OV.GetParam("snum.NoSpherA2.Hybrid.charge_Part%d"%part)
      mult = OV.GetParam("snum.NoSpherA2.Hybrid.mult_Part%d"%part)
      conv = OV.GetParam("snum.NoSpherA2.Hybrid.ORCA_SCF_Conv_Part%d"%part)
      strategy = OV.GetParam("snum.NoSpherA2.Hybrid.ORCA_SCF_Strategy_Part%d"%part)
      damping = OV.GetParam("snum.NoSpherA2.Hybrid.pySCF_Damping_Part%d"%part)
      if software_part == "ORCA":
        wfn_object.write_orca_input(xyz,basis_part,method_part,relativistc,charge,mult,strategy,conv,part)
      elif software_part == "ORCA 5.0":
        wfn_object.write_orca_input(xyz,basis_part,method_part,relativistc,charge,mult,strategy,conv,part)
      elif software_part == "Gaussian03":
        wfn_object.write_gX_input(xyz,basis_part,method_part,relativistc,charge,mult,part)
      elif software_part == "Gaussian09":
        wfn_object.write_gX_input(xyz,basis_part,method_part,relativistc,charge,mult,part)
      elif software_part == "Gaussian16":
        wfn_object.write_gX_input(xyz,basis_part,method_part,relativistc,charge,mult,part)
      elif software_part == "pySCF":
        wfn_object.write_pyscf_script(xyz,basis_part,method_part,relativistc,charge,mult,damping,part)
      elif software_part == "ELMOdb":
        print("ELMO not yet fully implemented for Hybrid!!! Sorry!!")
        return False
      elif software_part == "Psi4":
        print("Psi4 not yet fully implemented for Hybrid!!! Sorry!!")
        return False
      elif software_part == "Thakkar IAM":
        wfn_object.write_xyz_file()
    if software == "Hybrid":
      if software_part != "Thakkar IAM":
        try:
          run_with_bitmap("Calculating WFN ",wfn_object.run,part,software_part,basis_part)
        except NameError as error:
          print("The following error occured during QM Calculation: ",error)
          OV.SetVar('NoSpherA2-Error',error)
          raise NameError('Unsuccesfull Wavefunction Calculation!')
    elif software != "Thakkar IAM":
      try:
        run_with_bitmap("Calculating WFN ",wfn_object.run,part)
      except NameError as error:
        print("The following error occured during QM Calculation: ",error)
        OV.SetVar('NoSpherA2-Error',error)
        raise NameError('Unsuccesfull Wavefunction Calculation!')      

  def setup_wfn_2_fchk(self):
    exe_pre ="NoSpherA2"
    if sys.platform[:3] == 'win':
      _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
      if os.path.exists(_):
        self.wfn_2_fchk = _
      else:
        self.wfn_2_fchk = olx.file.Which("%s.exe" %exe_pre)
    else:
      base_dir = OV.BaseDir()
      if os.path.exists(os.path.join(base_dir,exe_pre)):
        self.wfn_2_fchk = os.path.join(base_dir,exe_pre)
      else:
        _ = os.path.join(self.p_path, "%s" %exe_pre)
        if os.path.exists(_):
          self.wfn_2_fchk = _
        else:
          self.wfn_2_fchk = olx.file.Which("%s" %exe_pre)
      print ("NoSpherA2 executable is:")
      print (self.wfn_2_fchk)
    if self.wfn_2_fchk == "":
      print ("ERROR!!!! No NoSpherA2 executable found! THIS WILL NOT WORK!")
      OV.SetVar('NoSpherA2-Error',"None")
      raise NameError('No NoSpherA2 Executable')
    if OV.IsDebugging():
      self.softwares += ";Thakkar IAM" #### Hidden until publsihed
    OV.SetVar("Wfn2Fchk",self.wfn_2_fchk)

  def setup_pyscf(self):
    self.has_pyscf = OV.GetParam('user.NoSpherA2.has_pyscf')
    if self.has_pyscf == False:
      if "Get pySCF" not in self.softwares:
        self.softwares = self.softwares + ";Get pySCF"
    if self.has_pyscf == True:
      if "pySCF" not in self.softwares:
        self.softwares = self.softwares + ";pySCF"

  def setup_psi4(self):
    import importlib
    test = importlib.util.find_spec("psi4")
    found = test is not None
    if(found):
      self.softwares += ";Psi4"

  def setup_elmodb(self):
    self.elmodb_exe = ""
    exe_pre = "elmodb"
    self.elmodb_exe_pre = exe_pre

    if sys.platform[:3] == 'win':
      self.ubuntu_exe = olx.file.Which("ubuntu.exe")
      _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
      if os.path.exists(_):
        self.elmodb_exe = _
      else:
        self.elmodb_exe = olx.file.Which("%s.exe" %exe_pre)

    else:
      self.ubuntu_exe = None
      _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
      if os.path.exists(_):
        self.elmodb_exe = _
      else:
        self.elmodb_exe = olx.file.Which("%s.exe" %exe_pre)
    if os.path.exists(self.elmodb_exe):
      if "ELMOdb" not in self.softwares:
        self.softwares = self.softwares + ";ELMOdb"

    self.elmodb_lib = ""
    lib_name = "LIBRARIES_AND_BASIS-SETS/"
    self.elmodb_lib_name = lib_name
    _ = os.path.join(self.p_path, "%s" %lib_name)
    if os.path.exists(_):
      self.elmodb_lib = _
    else:
      self.elmodb_lib = olx.file.Which("%s" %lib_name)

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
      OV.SetParam('snum.NoSpherA2.source',"ORCA")
      if "ORCA" not in self.softwares:
        self.softwares = self.softwares + ";ORCA;ORCA 5.0"
    else:
      self.softwares = self.softwares + ";Get ORCA"

  def setup_discamb(self):
    self.discamb_exe = ""
    exe_pre = "discamb2tsc"

    if sys.platform[:3] == 'win':
      _ = os.path.join(self.p_path, "%s.exe" % exe_pre)
      if os.path.exists(_):
        self.discamb_exe = _
      else:
        self.discamb_exe = olx.file.Which("%s.exe" % exe_pre)

    else:
      _ = os.path.join(self.p_path, "%s" % exe_pre)
      if os.path.exists(_):
        self.discamb_exe = _
      else:
        self.discamb_exe = olx.file.Which("%s" % exe_pre)
    if os.path.exists(self.discamb_exe):
      if "DISCAMB" not in self.softwares:
        self.softwares = self.softwares + ";DISCAMB"
    else:
      exe_pre = "discambMATTS2tsc"
      if sys.platform[:3] == 'win':
        _ = os.path.join(self.p_path, "%s.exe" %exe_pre)
        if os.path.exists(_):
          self.discamb_exe = _
        else:
          self.discamb_exe = olx.file.Which("%s.exe" %exe_pre)
  
      else:
        _ = os.path.join(self.p_path, "%s" %exe_pre)
        if os.path.exists(_):
          self.discamb_exe = _
        else:
          self.discamb_exe = olx.file.Which("%s" % exe_pre)
      if os.path.exists(self.discamb_exe):
        if "DISCAMB" not in self.softwares:
          self.softwares = self.softwares + ";DISCAMB"
      else:
        if OV.GetParam('user.NoSpherA2.enable_discamb') == True:
          self.softwares = self.softwares + ";Get DISCAMB"

  def getBasisListStr(self):
    return self.basis_list_str

  def getCPUListStr(self):
    return self.cpu_list_str

  def getwfn_softwares(self):
    parts = OV.ListParts()
    if parts != None:
      parts = list(parts)
    if OV.IsDebugging():
      if not parts:
        return self.softwares + ";fragHAR;"
      elif len(parts) > 1:
        return self.softwares + ";Hybrid;fragHAR;"
      else:
        return self.softwares + ";fragHAR;"
    else:
      return self.softwares + ";"

  def available(self):
    return os.path.exists(self.wfn_2_fchk)

def cuqct_tsc(wfn_file, hkl_file, cif, groups, save_k_pts=False, read_k_pts=False):
  folder = OV.FilePath()
  if type([]) != type(wfn_file):
    gui.get_default_notification(
        txt="Calculating .tsc file from Wavefunction <b>%s</b>..."%os.path.basename(wfn_file),
        txt_col='black_text')
  ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
  if os.path.isfile(os.path.join(folder, "NoSpherA2.log")):
    shutil.move(os.path.join(folder, "NoSpherA2.log"), os.path.join(folder, "NoSpherA2.log_org"))
  args = []
  wfn_2_fchk = OV.GetVar("Wfn2Fchk")
  args.append(wfn_2_fchk)
  if not os.path.exists(hkl_file):
    from cctbx_olex_adapter import OlexCctbxAdapter
    cctbx_adaptor = OlexCctbxAdapter()
    with open(hkl_file, "w") as out:
      f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_merged
      f_sq_obs = f_sq_obs.complete_array(d_min_tolerance=0.01, d_min=f_sq_obs.d_max_min()[1], d_max=f_sq_obs.d_max_min()[0], new_data_value=-1, new_sigmas_value=-1)
      f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
  args.append("-hkl")
  args.append(hkl_file)
  if (int(ncpus) > 1):
    args.append('-cpus')
    args.append(ncpus)
  if (OV.GetParam('snum.NoSpherA2.wfn2fchk_debug') == True):
    args.append('-v')
  if (OV.GetParam('snum.NoSpherA2.wfn2fchk_ED') == True):
    args.append('-ED')
  if (OV.GetParam('snum.NoSpherA2.becke_accuracy') != "Normal"):
    args.append('-acc')
    if (OV.GetParam('snum.NoSpherA2.becke_accuracy') == "Low"):
      args.append('1')
    elif (OV.GetParam('snum.NoSpherA2.becke_accuracy') == "High"):
      args.append('3')
    elif (OV.GetParam('snum.NoSpherA2.becke_accuracy') == "Max"):
      args.append('4')
  if(save_k_pts):
    args.append('-skpts')
  if(read_k_pts):
    args.append('-rkpts')
  olex_refinement_model = OV.GetRefinementModel(False)

  if olex_refinement_model['hklf']['value'] >= 5:
    try:
      src = OV.HKLSrc()
      cmd = "HKLF5 -e '%s'" %src
      res = scrub(cmd)
      if "HKLF5 file is expected" in " ".join(res):
        pass
      elif "negative batch numbers" in " ".join(res):
        pass
      else:
        args.append("-twin")
        for i in res[4].split() + res[6].split() + res[8].split():
          args.append(str(float(i)))
    except:
      print("There is a problem with the HKLF5 file...")
  elif 'twin' in olex_refinement_model:
    c = olex_refinement_model['twin']['matrix']
    args.append("-twin")
    for row in c:
      for el in row:
        args.append(str(float(el)))
  
  if type([]) == type(wfn_file):
    if type([]) == type(cif):
      args.append("-cmtc")
      if len(wfn_file) != len(groups) or len(wfn_file) != len(groups):
        print("Insonstiant size of parameters! ERROR!")
        return
      for i in range(len(wfn_file)):
        args.append(wfn_file[i])
        args.append(cif[i])
        for j in range(len(groups[i])):
          groups[i][j] = str(groups[i][j])
        args.append(','.join(groups[i]))
    else:
      args.append("-cif")
      args.append(cif)
      args.append("-mtc")
      if len(wfn_file) != len(groups):
        print("Insonstiant size of parameters! ERROR!")
        return
      for i in range(len(wfn_file)):
        args.append(wfn_file[i])
        for j in range(len(groups[i])):
          groups[i][j] = str(groups[i][j])
        args.append(','.join(groups[i]))      
  else:
    args.append("-wfn")
    args.append(wfn_file)  
    args.append("-cif")
    args.append(cif)
    if(groups[0] != -1000):
      args.append('-group')
      for i in range(len(groups)):
        args.append(groups[i])    

  os.environ['cuqct_cmd'] = '+&-'.join(args)
  os.environ['cuqct_dir'] = folder
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
                          os.path.join(p_path, "cuqct-launch.py")],
                          startupinfo=startinfo)
  else:
    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      return
    p = subprocess.Popen([pyl,
                          os.path.join(p_path, "cuqct-launch.py")])

  out_fn = "NoSpherA2.log"

  tries = 0
  while not os.path.exists(out_fn):
    if p.poll() is None:
      time.sleep(1)
      tries += 1
      if tries >= 5:
        if "python" in args[2] and tries <=10:
          continue
        print("Failed to locate the output file")
        OV.SetVar('NoSpherA2-Error',"NoSpherA2-Output not found!")
        raise NameError('NoSpherA2-Output not found!')
    else:
      print("process ended before the output file was found")
      OV.SetVar('NoSpherA2-Error',"NoSpherA2 ended unexpectedly!")
      raise NameError('NoSpherA2 ended unexpectedly!')

  with open(out_fn, "rU") as stdout:
    while p.poll() is None:
      x = stdout.read()
      if x:
        print(x,end='')
        olx.xf.EndUpdate()
        if OV.HasGUI():
          olx.Refresh()
      else:
        olx.xf.EndUpdate()
        if OV.HasGUI():
          olx.Refresh()
      time.sleep(0.1)

  sucess = False
  with open(out_fn,"r") as f:
    l = f.readlines()
    if "Writing tsc file...  ... done!\n" in l or "Writing tsc file...\n" in l:
      sucess = True
  
  if sucess == True:
    print("\n.tsc calculation ended!")
  else:
    print ("\nERROR during tsc calculation!")
    raise NameError('NoSpherA2-Output not complete!')

def discamb(folder, name, discamb_exe):
  move_args = []
  move_args.append(discamb_exe)
  hkl_file = os.path.join(folder,name+".hkl")
#  cif = os.path.join(folder,name+".cif")
#  move_args.append(cif)
#  move_args.append(hkl_file)
  if not os.path.exists(hkl_file):
    from cctbx_olex_adapter import OlexCctbxAdapter
#    from iotbx.shelx import hklf
    cctbx_adaptor = OlexCctbxAdapter()
    with open(hkl_file, "w") as out:
      f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_filtered
      f_sq_obs = f_sq_obs.complete_array(d_min_tolerance=0.01, d_min=f_sq_obs.d_max_min()[1], d_max=f_sq_obs.d_max_min()[0], new_data_value=-1, new_sigmas_value=-1)
      f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)

  os.environ['discamb_cmd'] = discamb_exe#'+&-'.join(move_args)
  os.environ['discamb_file'] = folder
  pyl = OV.getPYLPath()
  if not pyl:
    print("A problem with pyl is encountered, aborting.")
    return
  import subprocess
  p = subprocess.Popen([pyl,
                        os.path.join(p_path, "discamb-launch.py")])
  while p.poll() is None:
    time.sleep(5)
    olx.html.Update()

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
    self.full_dir = os.path.join(OV.FilePath(),full_dir)

    if not os.path.exists(full_dir):
      return
    self.date = os.path.getctime(full_dir)
    self.result_fn = os.path.join(full_dir, name) + ".archive.cif"
    self.error_fn = os.path.join(full_dir, name) + ".err"
    self.out_fn = os.path.join(full_dir, name) + ".out"
    self.dump_fn = os.path.join(full_dir, "hart.exe.stackdump")
    self.analysis_fn = os.path.join(full_dir, "stdout.fit_analysis")
    self.completed = os.path.exists(self.result_fn)
    #initialised = False

  def launch(self,wfn_dir=''):
    self.origin_folder = OV.FilePath()

    if wfn_dir == '':
      model_file_name = os.path.join(self.full_dir, self.name) + ".cif"
      olx.Kill("$Q")
      olx.File(model_file_name,p=10)
    else:
      self.full_dir = wfn_dir

    data_file_name = os.path.join(self.full_dir, self.name) + ".hkl"
    if not os.path.exists(data_file_name):
      from cctbx_olex_adapter import OlexCctbxAdapter
#      from iotbx.shelx import hklf
      cctbx_adaptor = OlexCctbxAdapter()
      with open(data_file_name, "w") as out:
        f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_filtered
        f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)

    # We are asking to just get form factors to disk
    fchk_source = OV.GetParam('snum.NoSpherA2.source')
    if fchk_source == "Tonto":
      # We want these from a wavefunction calculation using TONTO """

     # run = OV.GetVar('Run_number')

      args = [self.name+".cif",
              "-basis-dir", self.parent.basis_dir,
              "-shelx-f2", self.name+".hkl"
              ,"-basis", OV.GetParam('snum.NoSpherA2.basis_name')
              ,"-cluster-radius", str(OV.GetParam('snum.NoSpherA2.cluster_radius'))
              ,"-dtol", OV.GetParam('snum.NoSpherA2.DIIS')
              ]
      method = OV.GetParam('snum.NoSpherA2.method')
      if method == "HF":
        args.append("-scf")
        args.append("rhf")
      else:
        args.append("-scf")
        args.append("rks")
      clustergrow = OV.GetParam('snum.NoSpherA2.cluster_grow')
      if clustergrow == False:
        args.append("-complete-mol")
        args.append("f")

      rel = OV.GetParam('snum.NoSpherA2.Relativistic')
      if rel == True:
        args.append("-dkh")
        args.append("t")
    else:
      # We want these from supplied fchk file """
      fchk_file = OV.GetParam('snum.NoSpherA2.fchk_file')
      args = [self.name+".cif",
              "-shelx-f2", self.name+".hkl ",
              "-fchk", fchk_file]

    if OV.GetParam('snum.NoSpherA2.ncpus') != '1':
      args = [self.parent.mpiexec, "-np", OV.GetParam('snum.NoSpherA2.ncpus'), self.parent.mpi_har] + args
    else:
      args = [self.parent.exe] + args

    if OV.GetParam('snum.NoSpherA2.charge') != '0':
      args.append("-charge")
      args.append(OV.GetParam('snum.NoSpherA2.charge'))
    if OV.GetParam('snum.NoSpherA2.multiplicity') != '1':
      multiplicity = OV.GetParam('snum.NoSpherA2.multiplicity')
      if multiplicity == '0':
        OV.SetVar('NoSpherA2-Error',"Multiplicity0")
        raise NameError('Multiplicity of 0 is meaningless!')
      args.append("-mult")
      args.append(multiplicity)
    if OV.GetParam('snum.NoSpherA2.keep_wfn') == False:
      args.append("-wfn")
      args.append("f")
    if OV.GetParam('snum.NoSpherA2.wfn2fchk_SF') == True:
      args.append("-scf-only")
      args.append("t")
    disp = olx.GetVar("settings.tonto.HAR.dispersion", None)
    if 'true' == disp:
      import olexex
      from cctbx.eltbx import henke
      olex_refinement_model = OV.GetRefinementModel(False)
      sfac = olex_refinement_model.get('sfac')
      fp_fdps = {}
      wavelength = olex_refinement_model['exptl']['radiation']
      if sfac is not None:
        for element, sfac_dict in sfac.items():
          custom_fp_fdps.setdefault(element, sfac_dict['fpfdp'])
      asu = olex_refinement_model['aunit']
      for residue in asu['residues']:
        for atom in residue['atoms']:
          element_type = atom['type']
          if element_type not in fp_fdps:
            fpfdp = henke.table(str(element_type)).at_angstrom(wavelength).as_complex()
            fp_fdps[element_type] = (fpfdp.real, fpfdp.imag)
      disp_arg = " ".join(["%s %s %s" %(k, data2[0], data2[1]) for k,v in fp_fdps.items()])
      args.append("-dispersion")
      args.append('%s' %disp_arg)

    self.result_fn = os.path.join(self.full_dir, self.name) + ".archive.cif"
    self.error_fn = os.path.join(self.full_dir, self.name) + ".err"
    self.out_fn = os.path.join(self.full_dir, self.name) + ".out"
    self.dump_fn = os.path.join(self.full_dir, "hart.exe.stackdump")
    self.analysis_fn = os.path.join(self.full_dir, "stdout.fit_analysis")
    os.environ['hart_cmd'] = '+&-'.join(args)
    os.environ['hart_file'] = self.name
    os.environ['hart_dir'] = os.path.join(OV.FilePath(),self.full_dir)
    OV.SetParam('snum.NoSpherA2.name',self.name)
    OV.SetParam('snum.NoSpherA2.dir',self.full_dir)
    OV.SetParam('snum.NoSpherA2.cmd',args)

    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      return
    import subprocess
    p = subprocess.Popen([pyl,
                          os.path.join(p_path, "HARt-launch.py")])
    while p.poll() is None:
      time.sleep(3)

    if 'Error in' in open(os.path.join(self.full_dir,self.name+".err")).read():
      OV.SetVar('NoSpherA2-Error',"TontoError")
      raise NameError("Tonto Error!")
    if 'Wall-clock time taken for job' in open(os.path.join(self.full_dir,self.name+".out")).read():
      pass
    else:
      OV.SetVar('NoSpherA2-Error',"Tonto")
      raise NameError("Tonto unsuccessfull!")

def add_info_to_tsc():
  tsc_fn = os.path.join(OV.GetParam('snum.NoSpherA2.dir'),OV.GetParam('snum.NoSpherA2.file'))
  if not os.path.isfile(tsc_fn):
    print("Error finding tsc File!\n")
    return False
  with open(tsc_fn) as f:
    tsc = f.readlines()

  import shutil
  try:
    shutil.move(tsc_fn,tsc_fn+"_old")
  except:
    pass
  write_file = open(tsc_fn,"w")

  details_text = """CIF:
Refinement using NoSpherA2, an implementation of NOn-SPHERical Atom-form-factors in Olex2.
Please cite:\n\nF. Kleemiss, H. Puschmann, O. Dolomanov, S.Grabowsky Chem. Sci. 2021
NoSpherA2 implementation of HAR makes use of tailor-made aspherical atomic form factors calculated
on-the-fly from a Hirshfeld-partitioned electron density (ED) - not from
spherical-atom form factors.

The ED is calculated from a gaussian basis set single determinant SCF
wavefunction - either Hartree-Fock or DFT using selected funtionals - for a fragment of the crystal.
This fregment can be embedded in an electrostatic crystal field by employing cluster charges.
The following options were used:
"""
  software = OV.GetParam('snum.NoSpherA2.source')
  details_text = details_text + "   SOFTWARE:       %s\n"%software
  if software != "DISCAMB":
    method = OV.GetParam('snum.NoSpherA2.method')
    basis_set = OV.GetParam('snum.NoSpherA2.basis_name')
    charge = OV.GetParam('snum.NoSpherA2.charge')
    mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
    partitioning = OV.GetParam('snum.NoSpherA2.wfn2fchk_SF')
    accuracy = OV.GetParam('snum.NoSpherA2.becke_accuracy')
    if partitioning == True:
      details_text = details_text + "   PARTITIONING:   NoSpherA2\n"
      details_text = details_text + "   INT ACCURACY:   %s\n"%accuracy
    else:
      details_text = details_text + "   PARTITIONING:   Tonto\n"
    details_text = details_text + "   METHOD:         %s\n"%method
    details_text = details_text + "   BASIS SET:      %s\n"%basis_set
    details_text = details_text + "   CHARGE:         %s\n"%charge
    details_text = details_text + "   MULTIPLICITY:   %s\n"%mult
    if relativistic == True:
      details_text = details_text + "   RELATIVISTIC:   DKH2\n"
    if software == "Tonto":
      radius = OV.GetParam('snum.NoSpherA2.cluster_radius')
      details_text = details_text + "   CLUSTER RADIUS: %s\n"%radius
  tsc_file_name = os.path.join(OV.GetParam('snum.NoSpherA2.dir'),OV.GetParam('snum.NoSpherA2.file'))
  if os.path.exists(tsc_file_name):
    f_time = os.path.getctime(tsc_file_name)
  else:
    f_time = None
  import datetime
  f_date = datetime.datetime.fromtimestamp(f_time).strftime('%Y-%m-%d_%H-%M-%S')
  details_text = details_text + "   DATE:           %s\n"%f_date
  details_text = details_text + ":CIF"
  details_text += str(hash(details_text)) + '\n'
  cif_block_present = False
  #data_block = False
  for line in tsc:
    if ("CIF:" not in line) and ("DATA:" not in line) and ("data:" not in line):
      write_file.write(line)
    elif "CIF:" in line:
      cif_block_present = True
      write_file.write(line)
    elif ("DATA:" in line):
      #data_block = True
      if cif_block_present == False:
        write_file.write(details_text)
        write_file.write(line)
      else:
        write_file.write(line)
    elif ("data:" in line):
      #data_block = True
      if cif_block_present == False:
        write_file.write(details_text)
        write_file.write(line)
      else:
        print("CIF BLOCK is there")
        write_file.write(line)
  write_file.close()

OV.registerFunction(add_info_to_tsc,True,'NoSpherA2')

def combine_tscs(match_phrase="_part_", no_check=False):
  gui.get_default_notification(txt="Combining .tsc files", txt_col='black_text')
  args = []
  NSP2_exe = OV.GetVar("Wfn2Fchk")
  args.append(NSP2_exe)
  if (no_check):
    args.append("-merge_nocheck")
  else:
    args.append("-merge")

  print("Combinging the .tsc files of disorder parts... Please wait...")

  if debug:
    t_beg = time.time()
  sfc_name = OV.ModelSrc()

  tsc_dst = os.path.join(OV.FilePath(), sfc_name + "_total.tsc")
  if os.path.exists(tsc_dst):
    backup = os.path.join(OV.FilePath(), "tsc_backup")
    if not os.path.exists(backup):
      os.mkdir(backup)
    i = 1
    while (os.path.exists(os.path.join(backup,sfc_name + ".tsc") + "_%d"%i)):
      i = i + 1
    try:
      shutil.move(tsc_dst,os.path.join(backup,sfc_name + ".tsc") + "_%d"%i)
    except:
      pass

  if match_phrase != "":
    from os import walk
    _, _, filenames = next(walk(OV.FilePath()))
    for f in filenames:
      if match_phrase in f and ".tsc" in f:
        args.append(os.path.join(OV.FilePath(), f))
  else:
    print("ERROR! Please make sure threre is a match phrase to look for tscs!")
    return False
  startinfo = None

  from subprocess import Popen, PIPE
  from sys import stdout
  if sys.platform[:3] == 'win':
    from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW, SW_HIDE
    startinfo = STARTUPINFO()
    startinfo.dwFlags |= STARTF_USESHOWWINDOW
    startinfo.wShowWindow = SW_HIDE

  if startinfo == None:
    with Popen(args, stdout=PIPE) as p:
      for c in iter(lambda: p.stdout.read(1), b''):
        string = c.decode()
        stdout.write(string)
        stdout.flush()
        if '\r' in string or '\n' in string:
          olx.xf.EndUpdate()
          if OV.HasGUI():
            olx.Refresh()
  else:
    with Popen(args, stdout=PIPE, startupinfo=startinfo) as p:
      for c in iter(lambda: p.stdout.read(1), b''):
        string = c.decode()
        stdout.write(string)
        stdout.flush()
        if '\r' in string or '\n' in string:
          olx.xf.EndUpdate()
          if OV.HasGUI():
            olx.Refresh()

  tsc_dst = os.path.join(OV.FilePath(),sfc_name + "_total.tsc")
  shutil.move(os.path.join(OV.FilePath(),"combined.tsc"),tsc_dst)

  try:
    OV.SetParam('snum.NoSpherA2.file', tsc_dst)
    olx.html.SetValue('SNUM_REFINEMENT_NSFF_TSC_FILE', os.path.basename(tsc_dst))
  except:
    pass
  olx.html.Update()
  if debug:
    print("Total time: %.2f"%(time.time() - t_beg))
  return True

OV.registerFunction(combine_tscs,True,'NoSpherA2')

def deal_with_parts():
  parts = OV.ListParts()
  if not parts:
    return
  grouped_parts = read_disorder_groups()
  if grouped_parts == []:
    groups = []
    for part in parts:
      if part == 0:
        continue
      groups.append(["0",str(part)])
      olex.m("showp 0 %s" %part)
      fn = "%s_part_%s.xyz" %(OV.ModelSrc(), part)
      olx.File(fn,p=8)
    olex.m("showp")
    return list(parts), groups
  else:
    result = []
    groups = []
    longest = 0
    for i in range(len(grouped_parts)):
      if len(grouped_parts[i]) > longest:
        longest = i
    
    for i in range(len(grouped_parts[longest])):
      command = "showp 0"
      groups.append(["0"])
      result.append(i+1)
      for j in range(len(grouped_parts)):
        if i >= len(grouped_parts[j]):
          command += " %d"%grouped_parts[j][0]
          groups[i].append(str(grouped_parts[j][0]))
        else:
          command += " %d"%grouped_parts[j][i]
          groups[i].append(str(grouped_parts[j][i]))
      olex.m(command)
      fn = "%s_part_%s.xyz" %(OV.ModelSrc(), i+1)
      olx.File(fn,p=8)
    #I will return only a simpel sequence which maps onto the calculations to be done
    olex.m("showp")
    return result, groups
OV.registerFunction(deal_with_parts,True,'NoSpherA2')

def check_for_matching_fcf():
  p = OV.FilePath()
  name = OV.ModelSrc()
  fcf = os.path.join(p,name + '.fcf')
  if os.path.exists(fcf):
    return True
  else:
    return False
OV.registerFunction(check_for_matching_fcf,True,'NoSpherA2')

def check_for_matching_wfn():
  p = OV.FilePath()
  name = OV.ModelSrc()
  wfn = os.path.join(p,name + '.wfn')
  if os.path.exists(wfn):
    return True
  else:
    return False
OV.registerFunction(check_for_matching_wfn,True,'NoSpherA2')

def read_disorder_groups():
  inp = OV.GetParam('snum.NoSpherA2.Disorder_Groups')
  if inp == None or inp == "":
    return []
  groups = inp.split(';')
  result = []
  for i in range(len(groups)):
    result.append([])
    for part in groups[i].split(','):
      if '-' in part:
        if len(part) > 2:
          a, b = part.split('-')
          result[i].extend(list(range(int(a),int(b)+1)))
        else:
          result[i].append(int(part))
      else:
        result[i].append(int(part))
#    print result[i]
#  print result
  return result
OV.registerFunction(read_disorder_groups,True,'NoSpherA2')

def is_disordered():
  parts = OV.ListParts()
  if not parts:
    return False
  else:
    return True
OV.registerFunction(is_disordered,True,'NoSpherA2')

def change_basisset(input):
  OV.SetParam('snum.NoSpherA2.basis_name',input)
  if "x2c" in input:
    OV.SetParam('snum.NoSpherA2.Relativistic',True)
  elif "DKH" in input:
    OV.SetParam('snum.NoSpherA2.Relativistic',True)
  else:
    OV.SetParam('snum.NoSpherA2.Relativistic',False)
OV.registerFunction(change_basisset,True,'NoSpherA2')

def get_functional_list():
  wfn_code = OV.GetParam('snum.NoSpherA2.source')
  list = None
  if wfn_code == "Tonto" or wfn_code == "'Please Select'":
    list = "HF;B3LYP;"
  elif wfn_code == "pySCF":
    list = "HF;PBE;B3LYP;BLYP;M062X"
  else:
    list = "HF;BP;BP86;PWLDA;R2SCAN;TPSS;PBE;PBE0;M062X;B3LYP;BLYP;wB97;wB97X;XTB1;XTB2;"
  return list
OV.registerFunction(get_functional_list,True,'NoSpherA2')

def check_for_pyscf(loud=True):
  ubuntu_exe = None
  if sys.platform[:3] == 'win':
    ubuntu_exe = olx.file.Which("ubuntu.exe")
  else:
    ubuntu_exe = None
  if ubuntu_exe != None and os.path.exists(ubuntu_exe):
    import subprocess
    try:
      child = subprocess.Popen([ubuntu_exe,'run',"python -c 'import pyscf' && echo $?"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
      child.communicate()
      rc = child.returncode
      if rc == 0:
        OV.SetParam('user.NoSpherA2.has_pyscf', True)
        nsp2 = get_NoSpherA2_instance()
        nsp2.softwares = nsp2.softwares.replace(";Get pySCF", ";pySCF")
        olex.m("html.Update()")
        return True
    except:
      pass
    if loud == True:
      print ("To use pySCF please install pySCF and pip in your ubuntu environment:\nsudo apt update\nsudo apt install python python-numpy python-scipy python-h5py python-pip\nsudo -H pip install pyscf")
    return False
  elif ubuntu_exe == None :
    import subprocess
    try:
      child = subprocess.Popen(['python',  "-c 'import pyscf' && echo $?"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
      child.communicate()
      rc = child.returncode
      if rc == 0:
        OV.SetParam('user.NoSpherA2.has_pyscf',True)
        return True
    except:
      pass
    if loud == True:
      print ("To use pySCF please install pySCF in your python environment:\nsudo apt update\nsudo apt install python python-numpy python-scipy python-h5py python-pip\nsudo -H pip install pyscf")
    return False
  else:
    if sys.platform[:3] == 'win':
      if loud == True:
        print ("To use pySCF please install the ubuntu and linux subprocess framework for windows 10 and afterwords run:\nsudo apt update\nsudo apt install python python-numpy python-scipy python-h5py python-pip\nsudo -H pip install pyscf")
    else:
      if loud == True:
        print ("To use pySCF please install python, pip and pyscf\n")
    return False

def change_tsc_generator(input):
  if input == "Get ORCA":
    olx.Shell("https://orcaforum.kofo.mpg.de/index.php")
  elif input == "Get DISCAMB":
    olx.Shell("http://4xeden.uw.edu.pl/software/discamb/")
  elif input == "Get pySCF":
    result = check_for_pyscf(False)
    if result == False:
      selection = olx.Alert("No working pySCF installation found!",\
"""Error: No working pySCF installation found!.
Do you want to have a guide how to install pySCF?""", "YN", False)
      if selection == 'Y':
        win = (sys.platform[:3] == 'win')
        if win:
          cont = False
          tries = 0
          ubuntu_exe = None
          wsl = olx.file.Which("wsl.exe")
#Check for WSL
          if wsl == None or os.path.exists(wsl) == False:
            olx.Alert("Could not find Windows Subsystem for Linux",\
"""pySCF requires Ubuntu to be installed on your system.
This requires the Windows Subsystem for Linux.
It can be enabled in the settings of Windows.
1) Open Settings
2) Click on Apps
3) Under the "Related settings" section, click the Programs and Features option.
4) Click the Turn Windows features on or off option from the left pane.
5) Check the Windows Subsystem for Linux option.
6) Click the OK button
7) Click the 'Restart Now' button
Your computer will restart and next time you select "Get pySCF the next
step of installation will be shown if the installation was succesfull""", "O", False)
            return

#Check for Ubuntu installation
          ubuntu_exe = olx.file.Which("ubuntu.exe")
          if ubuntu_exe == None or os.path.exists(ubuntu_exe) == False:
            olx.Alert("Please install Ubuntu",\
"""pySCF requires Ubuntu to be installed on your system.
It is reletively easy to do that.
You can go to the Microsoft store and install it by searching for 'ubuntu' in clicking the install button.
Once it is downloaded click the 'Launch' button and set up a username and password.
After this setup is completed you can close the Ubuntu window and continue with this guide.
Please do this now and klick 'Ok' once everything is done!""", "O", False)
            while not cont:
              ubuntu_exe = olx.file.Which("ubuntu.exe")
              if os.path.exists(ubuntu_exe) == False:
                tries += 1
                if tries == 4:
                  print ("Something seems wrong, aborting installation guide after 3 unsuccesfull attempts!")
                  return
                olx.Alert("Could not find Ubuntu",\
"""pySCF requires Ubuntu to be installed on your system.
It is reletively easy to do that.
You can go to the Microsoft store and install it by searching for 'ubuntu' in clicking the install button.
Once it is downloaded click the 'Launch' button and set up a username and password.
After this setup is completed you can close the Ubuntu window and continue with this guide.
Please do this now and klick 'Ok' once everything is done!""", "O", False)
              else:
                cont = True
                break

#Check for pySCF
          cont = False
          tries = 0
          test = check_for_pyscf(False)
          if test == False:
            while not cont:
              tries += 1
              if tries == 4:
                print ("Something seems wrong, aborting installation guide after 3 unsuccesfull attempts!")
                return
              olx.Alert("Please install Python and pySCF in Ubuntu",\
"""Almost done! Now we need to install Python and pySCF in your Ubuntu environment.
Please open a Ubuntu terminal by starting Ubuntu.
To do so you can use the Win+R shortcut and type 'ubuntu' or select it from the start menu.
This will start a terminal in Ubuntu.
There please type the following commands, each line followed by the Enter key:
> sudo apt update
     Ubuntu will ask for you password that you gave when setting up the installation
> sudo apt install python3 python3-pip python-is-python3
> sudo -H pip3 install pyscf
Please do this now and klick 'Ok' once everything is done!""", "O", False)
              cont = check_for_pyscf(False)
              if cont == True:
                print ("PySCF installed sucessfully!")
                selection = olx.Alert("Do you want to restart now?",\
          """PySCF installed sucessfully!
          Do you want to restart Olex2 now to load the new settings?""", "YN", False)
                if selection == 'Y':
                  olex.m('restart')
          else:
            olx.Alert("Installation sucessful",\
"""Installation Sucessfull!
In order to load the new functionality Olex2 will need to restart!
Once you click 'Ok' Olex2 will do so automatically!""", "O", False)
            print ("PySCF installed sucessfully!")
            olex.m('restart')

        else:
            olx.Alert("Please install pySCF",\
"""Please install pySCF in your python distribution.
On Ubuntu this can be done by typing in a command line:
1) sudo apt install python-pip
2) sudo pip install pyscf
if that worked try to execute the following in a terminal:
python -c 'import pyscf'
If that does not throw an error message you were succesfull.""", "O", False)

  else:
    OV.SetParam('snum.NoSpherA2.source',input)
    if input != "DISCAMB":
      OV.SetParam('snum.NoSpherA2.h_aniso',True)
      F000 = olx.xf.GetF000()
      Z = olx.xf.au.GetZ()
      nr_electrons= int(float(F000) / float(Z))
      mult = int(OV.GetParam('snum.NoSpherA2.multiplicity'))
      if mult == 0:
        if (nr_electrons % 2 == 0):
          OV.SetParam('snum.NoSpherA2.multiplicity',1)
        elif (nr_electrons % 2 != 0):
          OV.SetParam('snum.NoSpherA2.multiplicity',2)
    else:
      OV.SetParam('snum.NoSpherA2.h_aniso',False)
OV.registerFunction(change_tsc_generator,True,'NoSpherA2')

def set_default_cpu_and_mem():
  import math
  import multiprocessing
  parallel = OV.GetVar("Parallel")
  max_cpu = multiprocessing.cpu_count()
  current_cpus = OV.GetParam('snum.NoSpherA2.ncpus')
  update = False
  if not parallel:
    OV.SetParam('snum.NoSpherA2.ncpus',1)
    return
  if (max_cpu == 1):
    OV.SetParam('snum.NoSpherA2.ncpus',1)
    return
  elif (current_cpus != "1"):
    update = True
  mem_gib = None
  if sys.platform[:3] == 'win':
    import ctypes

    class MEMORYSTATUSEX(ctypes.Structure):
      _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
      ]

      def __init__(self):
        # have to initialize this to the size of MEMORYSTATUSEX
        self.dwLength = ctypes.sizeof(self)
        super(MEMORYSTATUSEX, self).__init__()

    stat = MEMORYSTATUSEX()
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    mem_gib = math.floor(stat.ullAvailPhys / (1024**3))
  else:
    import os
    mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')  # e.g. 4015976448
    mem_gib = mem_bytes/(1024.**3)  # e.g. 3.74
  tf_mem = math.floor(mem_gib/4*30)/10
  tf_cpu = math.floor(max_cpu/4*3)
  if update == False:
    OV.SetParam('snum.NoSpherA2.ncpus',str(int(tf_cpu)))
  OV.SetParam('snum.NoSpherA2.mem',str(tf_mem))
OV.registerFunction(set_default_cpu_and_mem,True,'NoSpherA2')

def toggle_GUI():
  use = OV.GetParam('snum.NoSpherA2.use_aspherical')
  if use == True:
    OV.SetParam('snum.NoSpherA2.use_aspherical', False)
    OV.SetParam('snum.NoSpherA2.Calculate',False)
  else:
    OV.SetParam('snum.NoSpherA2.use_aspherical', True)
    set_default_cpu_and_mem()
  olex.m("html.Update()")
OV.registerFunction(toggle_GUI,True,'NoSpherA2')

def sample_folder(input_name):
  import shutil
  job_folder = os.path.join(OV.DataDir(), "HAR_samples", input_name)
  if not os.path.exists(os.path.join(OV.DataDir(), "HAR_samples")):
    os.mkdir(os.path.join(OV.DataDir(), "HAR_samples"))
  sample_file = os.path.join(p_path, "samples", input_name + ".cif")
  i = 1
  while (os.path.exists(job_folder + "_%d"%i)):
    i = i + 1
  job_folder = job_folder + "_%d"%i
  os.mkdir(job_folder)
  shutil.copy(sample_file, job_folder)
  load_input_cif="reap '%s.cif'" %os.path.join(job_folder, input_name)
  olex.m(load_input_cif)
OV.registerFunction(sample_folder, False, "NoSpherA2")

def org_min():
  OV.SetParam('snum.NoSpherA2.basis_name',"3-21G")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"SloppySCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"EasyConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.01")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.6")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(org_min, False, "NoSpherA2")
def org_small():
  OV.SetParam('snum.NoSpherA2.basis_name',"cc-pVDZ")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"NoSpherA2SCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"EasyConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.6")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(org_small, False, "NoSpherA2")
def org_final():
  OV.SetParam('snum.NoSpherA2.basis_name',"cc-pVTZ")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Normal")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"StrongSCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"EasyConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.0001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.6")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',True)
  olex.m("html.Update()")
OV.registerFunction(org_final, False, "NoSpherA2")

def light_min():
  OV.SetParam('snum.NoSpherA2.basis_name',"3-21G")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"SloppySCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.01")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(light_min, False, "NoSpherA2")
def light_small():
  OV.SetParam('snum.NoSpherA2.basis_name',"def2-SVP")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"NoSpherA2SCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(light_small, False, "NoSpherA2")
def light_final():
  OV.SetParam('snum.NoSpherA2.basis_name',"def2-TZVP")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Normal")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"StrongSCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.0001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',True)
  olex.m("html.Update()")
OV.registerFunction(light_final, False, "NoSpherA2")

def heavy_min():
  OV.SetParam('snum.NoSpherA2.basis_name',"x2c-SVP")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"SloppySCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.01")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',True)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(heavy_min, False, "NoSpherA2")
def heavy_small():
  OV.SetParam('snum.NoSpherA2.basis_name',"jorge-DZP-DKH")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"NoSpherA2SCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',True)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(heavy_small, False, "NoSpherA2")
def heavy_final():
  OV.SetParam('snum.NoSpherA2.basis_name',"x2c-TZVP")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Normal")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"StrongSCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.0001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',True)
  OV.SetParam('snum.NoSpherA2.full_HAR',True)
  olex.m("html.Update()")
OV.registerFunction(heavy_final, False, "NoSpherA2")

def psi4():
  import psi4
  geom = """
nocom
noreorient
O  2.7063023580 5.1528084960 8.7720795339
O  3.3917574233 4.6987620000 6.5946475188
O  3.3951198906 7.3446337920 8.3358309397
O  3.5584508738 5.4011996640 11.3644823059
H  3.9006607840 4.8830494080 11.1073486405
O  0.0777075174 4.3750162080 8.1552339725
H  -0.8348749233 5.0153560800 7.5389177106
O  0.5790341980 6.1209060960 10.2647039402
H  0.5199558750 5.2261571520 9.6673365980
O  5.9710316304 7.3284116160 10.8122112756
H  7.0596333792 6.6514410240 10.7672208236
O  5.8122422037 6.1015441440 7.1287106485
H  4.6869574832 6.3973808160 6.7212559436
O  4.5348713625 3.4297692000 4.4283307918
H  4.4649589816 4.3055922720 4.3947732076
O  0.6221059176 1.6562318400 7.3208463434
H  0.0542246615 1.4387151360 8.4539705735
O  3.4196014307 1.0813039680 6.8952895978
H  2.6365932773 0.2366170080 7.1116672067
C  2.2907529119 5.0602723200 7.4142147637
H  1.9724426610 6.0465980640 7.0040077017
C  3.6799020526 6.5094533760 10.5130512350
H  3.4079286655 7.4494674240 11.1040669840
C  2.7674469766 6.5041332000 9.2667627857
C  5.0653480467 6.7215626880 9.9006517889
H  5.4745713694 5.7394233120 9.5440098297
C  2.8085932626 2.3223876480 6.6235472679
H  2.4041473554 2.3378248800 5.5971298038
C  1.1531809098 4.0439442720 7.2764910508
H  0.7962560402 4.0444675680 6.2010604590
C  1.6368850964 2.6190964800 7.5673940202
H  2.0163570849 2.5153966560 8.6195354368
C  4.7613582222 7.6483199040 8.7213726480
H  4.7945236343 8.7079943040 9.0026423677
C  1.3504633130 7.0304817600 9.5008189958
H  0.8884059681 7.2729422400 8.4842465012
H  1.4228497713 8.0140165920 9.9861865776
C  3.9116136622 3.3699390240 6.7894297108
H  4.3812157993 3.2453073600 7.8100248811
C  5.0179353755 3.1993445280 5.7475567032
H  5.3801952506 2.1660093600 5.8059913608
H  5.8953563191 3.9488788320 5.9985504952
C  5.6803463582 7.4588867520 7.5271672631
H  6.6956267802 7.8106288800 7.8564973715
H  5.3388863094 8.1423113280 6.6742541538
"""
  sfc_name = OV.ModelSrc()
  out = os.path.join(OV.FilePath(), sfc_name + "_psi4.log")
  psi4.core.set_output_file(out)
  psi4.geometry(geom)
  psi4.set_num_threads(6)
  psi4.set_memory('15000 MB')
  psi4.set_options({'scf_type': 'DF',
  'dft_pruning_scheme': 'treutler',
  'dft_radial_points': 20,
  'dft_spherical_points': 110,
  'dft_basis_tolerance': 1E-10,
  'dft_density_tolerance': 1.0E-8,
  'ints_tolerance': 1.0E-8,
  'df_basis_scf': 'def2-universal-jkfit',
  })
  E, wfn = psi4.energy('pbe/cc-pVDZ', return_wfn=True)
  psi4.fchk(wfn, os.path.join(OV.FilePath(), sfc_name + ".fchk"))
  return None
OV.registerFunction(psi4, False, "NoSpherA2")

def make_quick_button_gui():
  import olexex
  from ImageTools import IT

  max_Z, heaviest_element_in_formula = olexex.FindZOfHeaviestAtomInFormula()
  d = {}
  if max_Z < 10:
    d.setdefault('type', 'org')
    d.setdefault('description', 'Organic Molecule (Z &lt; 10) ')
  elif max_Z < 36:
    d.setdefault('type', 'light')
    d.setdefault('description', 'Light metal (Z &lt; 35) ')
  else:
    d.setdefault('type', 'heavy')
    d.setdefault('description', 'Heavy metal (Z  &gt; 35) ')

  buttons = ""
  base_col = OV.GetParam("gui.action_colour")
  for item in [("min", IT.adjust_colour(base_col, luminosity=1.0, as_format='hex'), "Test"),
               ("small", IT.adjust_colour(base_col, luminosity=0.9, as_format='hex'), "Work"),
               ("final", IT.adjust_colour(base_col, luminosity=0.8, as_format='hex'), "Final")]:
    d["qual"]=item[0]
    d["col"]=item[1]
    d["value"]=item[2]
    buttons += '''
    <td width="20%%">
      <input
        type="button"
        name="nosphera2_quick_button_%(type)s_%(qual)s"
        value="%(value)s"
        height="GetVar(HtmlComboHeight)"
        onclick="spy.SetParam('snum.NoSpherA2.Calculate',True)>>spy.NoSpherA2.%(type)s_%(qual)s()"
        bgcolor="%(col)s"
        fgcolor="#ffffff"
        fit="false"
        flat="GetVar(linkButton.flat)"
        hint=""
        disabled="false"
        custom="GetVar(custom_button)"
      >
    </td>''' % d

  d["buttons"]=buttons

  t='''
<td width="40%%" align='left'>
<b>%(description)s</b>
</td>
%(buttons)s
''' % d
  return t

def run_with_bitmap(text, function, *args, **kwargs):
  custom_bitmap(text)
  OV.CreateBitmap(text)
  try:
    function(*args, **kwargs)
  except Exception as e:
    OV.DeleteBitmap(text)
    raise e
  OV.DeleteBitmap(text)

def custom_bitmap(text):
  bitmap_font = "DefaultFont"
  bitmap = {
    text:{'label':text,
              'name':text,
              'color':'#ff4444',
              'size':(len(text)*12, 32),
              'font_colour':"#ffffff",
              }
              }
  map = bitmap[text]
  colour = map.get('color', '#ffffff')
  name = map.get('name','untitled')
  txt = map.get('label', '')
  size = map.get('size')
  image = Image.new('RGB', size, colour)
  draw = ImageDraw.Draw(image)
  IT.write_text_to_draw(draw,
                             txt,
                             top_left = (5, -1),
                             font_name=bitmap_font,
                             font_size=24,
                             font_colour = map.get('font_colour', '#000000')
                           )
  OlexVFS.save_image_to_olex(image, name, 2)


NoSpherA2_instance = NoSpherA2()
OV.registerFunction(NoSpherA2_instance.available, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.launch, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.delete_f_calc_f_obs_one_h, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getBasisListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getCPUListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getwfn_softwares, False, "NoSpherA2")
OV.registerFunction(make_quick_button_gui, False, "NoSpherA2")

def hybrid_GUI():
  from .hybrid_GUI import make_hybrid_GUI
  t = make_hybrid_GUI(NoSpherA2_instance.getwfn_softwares())
  return t
OV.registerFunction(hybrid_GUI, False, "NoSpherA2")

def get_NoSpherA2_instance():
  return NoSpherA2_instance
#print "OK."
