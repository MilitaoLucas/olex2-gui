import os
import sys
import olex
import olx
import olex_core
import gui
import shutil
import time

from olexFunctions import OV
debug = OV.IsDebugging()

# Local imports for NoSpherA2 functions
from utilities import *
from hybrid_GUI import make_hybrid_GUI
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
      
    else:
      if "Tonto" not in self.softwares:
        self.softwares = self.softwares + ";Tonto"
      print("No MPI implementation found in PATH!\nTonto, ORCA and other software relying on it will only have 1 CPU available!\n")

  def tidy_wfn_jobs_folder(self, part=None):
    if part == None:
      backup = os.path.join(self.jobs_dir, "backup")
      to_backup = self.jobs_dir
      wfn_job_dir = self.jobs_dir
    else:
      backup = os.path.join(self.jobs_dir, "Part_%d" % part, "backup")
      to_backup = os.path.join(self.jobs_dir, "Part_%d" % part)
      wfn_job_dir = os.path.join(self.jobs_dir, "Part_%d" % part)
    if os.path.exists(to_backup):
      l = 1
      while (os.path.exists(backup + "_%d" % l)):
        l = l + 1
      backup = backup + "_%d" % l
      os.mkdir(backup)
    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')

    if os.path.exists(os.path.join(self.jobs_dir,olx.FileName()+".hkl")):
      run = None
      if Full_HAR == True:
        run = OV.GetVar('Run_number')
      if os.path.exists(wfn_job_dir):
        files = (file for file in os.listdir(wfn_job_dir)
              if os.path.isfile(os.path.join(wfn_job_dir, file)))
        for f in files:
          f_work = os.path.join(wfn_job_dir, f)
          f_dest = os.path.join(backup, f)
          if Full_HAR == True:
            if run > 0:
              if self.wfn_code == "Tonto":
                if "restricted" not in f:
                  shutil.move(f_work, f_dest)
              elif self.wfn_code == "ORCA":
                if ".gbw" not in f:
                  shutil.move(f_work, f_dest)
                else:
                  shutil.move(os.path.join(wfn_job_dir, f), os.path.join(wfn_job_dir, self.name + "2.gbw"))
              elif self.wfn_code == "ORCA 5.0":
                if ".gbw" not in f:
                  shutil.move(f_work, f_dest)
                else:
                  shutil.move(os.path.join(wfn_job_dir, f), os.path.join(wfn_job_dir, self.name + "2.gbw"))
              elif "Gaussian" in self.wfn_code:
                if ".chk" not in f:
                  shutil.move(f_work, f_dest)
              elif "ELMOdb" in self.wfn_code:
                if ".wfx" not in f:
                  shutil.move(f_work, f_dest)
              elif "pySCF" in self.wfn_code:
                if ".chk" not in f:
                  shutil.move(f_work, f_dest)
              else:
                  shutil.move(f_work, f_dest)
            else:
              shutil.move(f_work, f_dest)
          else:
            shutil.move(f_work, f_dest)

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

    # This checks ne multiplicity and Number of electrons
    if (wfn_code != "DISCAMB") and (wfn_code != "Thakkar IAM") and (olx.xf.latt.IsGrown() != 'true') and is_disordered() == False:
      ne, adapter = calculate_number_of_electrons()
      heavy = False
      for sc in adapter.xray_structure().scatterers():
        if sc.electron_count() > 36:
          heavy = True
      if heavy and ("x2c" not in basis) and ("jorge" not in basis) and ("ECP" not in basis) \
        and ("STO" not in basis) and ("3-21" not in basis):
        print("Atoms with Z > 36 require jorge, ECP or x2c basis sets!")
        OV.SetVar('NoSpherA2-Error', "Heavy Atom but no heavy atom basis set!")
        return False      
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

    # Now check whetehr and do some history file handlings
    tsc_exists = False
    f_time = None
    if OV.GetParam('snum.NoSpherA2.no_backup') == False:
      backup_endings = [".wfn", ".wfx", ".molden", ".gbw", ".fchk", ".tscb", ".tsc", ".wfnlog"]
      for file in os.listdir(olx.FilePath()):
        if file.endswith(".tsc"):
          tsc_exists = True
          f_time = os.path.getmtime(file)
        if file.endswith(".tscb"):
          tsc_exists = True
          f_time = os.path.getmtime(file)
      if tsc_exists and not any(x in wfn_code for x in [".wfn", ".wfx", ".molden", ".gbw", ".fchk"]):
        import datetime
        timestamp_dir = os.path.join(self.history_dir,olx.FileName() + "_" + datetime.datetime.fromtimestamp(f_time).strftime('%Y-%m-%d_%H-%M-%S'))
        if not os.path.exists(timestamp_dir):
          os.mkdir(timestamp_dir)
        for file in os.listdir('.'):
          if any(file.endswith(x) for x in backup_endings):
            shutil.move(os.path.join(olx.FilePath(),file),os.path.join(timestamp_dir,file))

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
      parts, groups = deal_with_parts()
      nr_parts = len(parts)

    if nr_parts > 1:
      wfn_files = []
      need_to_combine = False
      need_to_partition = False
      if ".wfn" in wfn_code:
        print("Calcualtion from wfn with disorder not possible, sorry!\n")
        return
      groups_counter = 0
      olex.m("CifCreate_4NoSpherA2")
      shutil.move(self.name + ".cif_NoSpherA2", os.path.join(self.jobs_dir, self.name + ".cif"))
      if wfn_code == "fragHAR":
        # Special case for fragHAR, which will handle the CIF and partitioning itself.
        try:
          self.wfn(folder=self.jobs_dir, xyz=False)
          return
        except NameError as error:
          print ("Aborted due to: ",error)
          OV.SetVar('NoSpherA2-Error',error)
          return False        
      #olx.File(os.path.join(self.jobs_dir, "%s.cif" % (self.name)))
      for i in range(nr_parts):
        if parts[i] == 0:
          groups_counter+=1
          continue
        # Check if job folder already exists and (if needed) make the backup folders
        self.tidy_wfn_jobs_folder(parts[i])
        wfn_job_dir = os.path.join(self.jobs_dir, "Part_%d" % parts[i])
        if wfn_code.lower().endswith(".fchk"):
          raise NameError('Disorder is not possible with precalculated fchks!')
        try:
          os.mkdir(wfn_job_dir)
        except:
          pass
        atom_loop_reached = False
        out_cif = open(os.path.join(wfn_job_dir, "%s.cif" % (OV.ModelSrc())), "w")
        with open(os.path.join(self.jobs_dir, "%s.cif" % (OV.ModelSrc())), "r") as incif:
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
          #DISCMAB is used
          discamb(os.path.join(OV.FilePath(), wfn_job_dir), self.name, self.discamb_exe)
          shutil.copy(os.path.join(wfn_job_dir, self.name + ".tsc"), self.name + "_part_" + str(parts[i]) + ".tsc")
          shutil.copy(os.path.join(wfn_job_dir, "discamb2tsc.log"), os.path.join(self.jobs_dir, "discamb2tsc.log"))
          need_to_combine = True
        elif wfn_code == "Hybrid":
          # We are in Hybrid mode
          hybrid_part_wfn_code = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d"%(parts[i]))
          if hybrid_part_wfn_code == "DISCAMB":
            groups.pop(i-groups_counter)
            groups_counter+=1
            discamb(os.path.join(OV.FilePath(), wfn_job_dir), self.name, self.discamb_exe)
            shutil.copy(os.path.join(wfn_job_dir, self.name + ".tsc"), self.name + "_part_" + str(parts[i]) + ".tsc")
            shutil.copy(os.path.join(wfn_job_dir, "discamb2tsc.log"), os.path.join(self.jobs_dir, "discamb2tsc.log"))
            need_to_combine = True
          else:
            need_to_partition = True
            shutil.move("%s_part_%s.xyz" % (self.name, parts[i]), os.path.join(wfn_job_dir, "%s.xyz" % (self.name)))
            try:
              self.wfn(folder=wfn_job_dir, xyz=False, part=parts[i])
            except NameError as error:
              print ("Aborted due to: ",error)
              OV.SetVar('NoSpherA2-Error',error)
              return False         
            path_base = os.path.join(OV.FilePath(), wfn_job_dir, self.name)
            if os.path.exists(path_base + ".gbw"):
              wfn_fn = path_base + ".gbw"
            elif os.path.exists(path_base+".wfx"):
              wfn_fn = path_base + ".wfx"
            elif os.path.exists(path_base+".fchk"):
              wfn_fn = path_base + ".fchk"
            elif os.path.exists(path_base+".wfn"):
              wfn_fn = path_base + ".wfn"
            elif hybrid_part_wfn_code == "Thakkar IAM":
              wfn_fn = path_base + ".xyz"
              try:
                shutil.copy(os.path.join(wfn_job_dir, "%s.xyz" % (self.name)), "%s_part%s.xyz" % (self.name, parts[i]))
              except:
                pass
            else:
              return False
            wfn_fn = None
            #groups[i-groups_counter].append(0)
            #groups[i-groups_counter].append(parts[i])
            for file in os.listdir(wfn_job_dir):
              temp = None
              if file.endswith(".wfn"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfn"
              elif file.endswith(".wfx"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfx"
                if (wfn_fn == None or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".fchk")):
                  wfn_fn = temp
              elif file.endswith(".gbw"):
                temp = os.path.splitext(file)[0] + "_part%d" % parts[i] + ".gbw"
                if (wfn_fn == None or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".wfx") or wfn_fn.endswith(".fchk")):
                  wfn_fn = temp
              elif file.endswith(".ffn"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".ffn"
              elif file.endswith(".fchk"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".fchk"
                if (wfn_fn == None or wfn_fn.endswith(".wfn")):
                  wfn_fn = temp
              if temp != None:
                shutil.move(file, temp)
            if hybrid_part_wfn_code == "Thakkar IAM" and wfn_fn == None:
              wfn_fn = "%s_part%s.xyz" % (self.name, parts[i])
            wfn_files.append(wfn_fn)
        else:
          # Neither Hybrid nor DISCAMB are used, so ORCA; g16; pySCF etc
          need_to_partition = True
          if wfn_code != "Tonto":
            shutil.move("%s_part_%s.xyz" % (self.name, parts[i]), os.path.join(wfn_job_dir, "%s.xyz" % (self.name)))
            if wfn_code == "ELMOdb":
              mutation = OV.GetParam('snum.NoSpherA2.ELMOdb.mutation')
              pdb_name = job.name + ".pdb"
              if mutation == True:
                pdb_name += "_mut"+str(parts[i])
              if os.path.exists(os.path.join(OV.FilePath(),pdb_name)):
                shutil.copy(os.path.join(OV.FilePath(), pdb_name), os.path.join(wfn_job_dir, self.name + ".pdb"))
              else:
                OV.SetVar('NoSpherA2-Error',"ELMOdb")
                if mutation == True:
                  raise NameError('No pdb_name file available for mutation!')
                else:
                  raise NameError('No pdb file available! Make sure the name of the pdb file is the same as the name of your ins file!')
            OV.SetParam('snum.NoSpherA2.fchk_file', self.name + ".fchk")
            try:
              self.wfn(folder=wfn_job_dir, xyz=False, part=parts[i])  # Produces Fchk file in all cases that are not fchk or tonto directly
            except NameError as error:
              print ("Aborted due to: ",error)
              OV.SetVar('NoSpherA2-Error',error)
              return False
          if experimental_SF == False or wfn_code == "Tonto":
            job = Job(self, self.name)
            try:
              job.launch(wfn_job_dir)
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
            wfn_fn = os.path.join(OV.FilePath(), wfn_job_dir, self.name + ".xyz")
          else:
            wfn_fn = None
            path_base = os.path.join(OV.FilePath(), wfn_job_dir, self.name)
            if os.path.exists(path_base + ".wfx"):
              if (wfn_fn == None or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".fchk")):
                wfn_fn = path_base + ".wfx"
            elif os.path.exists(path_base + ".fchk"):
              if (wfn_fn == None): 
                wfn_fn = path_base + ".fchk"
            elif os.path.exists(path_base + ".wfn"):
              wfn_fn = path_base + ".wfn"
            elif os.path.exists(path_base + ".gbw"):
              if (wfn_fn == None or wfn_fn.endswith(".wfx") or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".fchk") and "5.0" in wfn_code):
                wfn_fn = path_base + ".gbw"
            elif os.path.exists(path_base + ".molden"):
              wfn_fn = path_base + ".molden"
            else:
              return False
          wfn_files.append(wfn_fn)
          endings = [".wfn", ".wfx", ".gbw", ".ffn", ".molden", ".fchk", ".wfnlog"]
          for file in os.listdir(os.getcwd()):
            if "_part" in file:
              continue
            temp = None
            if any(file.endswith(x) for x in endings):
              temp = os.path.splitext(file)[0] + "_part%d" % parts[i] + os.path.splitext(file)[1]
            if temp != None:
              shutil.move(file,temp)

      # End of loop over parts
      if need_to_partition == True:
        cif_fn = os.path.join(self.jobs_dir, self.name + ".cif")
        #hkl_fn = os.path.join(self.jobs_dir, self.name + ".hkl")
        cuqct_tsc(wfn_files, cif_fn, groups)
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
        if os.path.exists(self.name + ".tscb"):
          shutil.move(self.name + ".tscb", self.name + "_part_999.tscb")
        combine_tscs()

    else:
      # Check if job folder already exists and (if needed) make the backup folders
      self.tidy_wfn_jobs_folder()

      olex.m("CifCreate_4NoSpherA2")
      shutil.move(self.name + ".cif_NoSpherA2",os.path.join(self.jobs_dir, self.name + ".cif"))
      # Make a wavefunction (in case of tonto wfn code and tonto tsc file do it at the same time)

      if wfn_code == "DISCAMB":
        cif = str(os.path.join(self.jobs_dir, self.name + ".cif"))
        olx.File(cif)
        discamb(os.path.join(OV.FilePath(), self.jobs_dir), self.name, self.discamb_exe)
        shutil.copy(os.path.join(OV.FilePath(), self.jobs_dir, self.name + ".tsc"), self.name + ".tsc")
        OV.SetParam('snum.NoSpherA2.file', self.name + ".tsc")
      else:
        if wfn_code.lower().endswith(".wfn") or wfn_code.lower().endswith(".wfx") or \
           wfn_code.lower().endswith(".molden") or wfn_code.lower().endswith(".gbw"):
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
            if wfn_code.lower().endswith(".wfn") or wfn_code.lower().endswith(".wfx") or \
               wfn_code.lower().endswith(".molden") or wfn_code.lower().endswith(".gbw"):
              wfn_fn = wfn_code
              shutil.copy(wfn_code,os.path.join(os.path.join("olex2","Wfn_Job"),os.path.split(wfn_code)[1]))
            endings = [".fchk", ".wfn", ".ffn", ".wfx", ".molden"]
            if "5.0" in wfn_code:
              endings.append(".gbw")
            if wfn_code == "Thakkar IAM":
              wfn_fn = path_base + ".xyz"
            elif not any(os.path.exists(path_base + x) for x in endings):
              print("No usefull wavefunction found!")
              return False
            else:
              for e in endings:
                if os.path.exists(path_base + e):
                  wfn_fn = path_base + e
            #hkl_fn = path_base + ".hkl"
            cif_fn = path_base + ".cif"
            cuqct_tsc(wfn_fn, cif_fn, [-1000])
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

  def wfn(self, folder='', xyz=True, part=0):
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
      cif_file = os.path.join(folder, fn + ".cif")
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
          wfn_object.run(part, software_part, basis_part)
        except NameError as error:
          print("The following error occured during QM Calculation: ",error)
          OV.SetVar('NoSpherA2-Error',error)
          raise NameError('Unsuccesfull Wavefunction Calculation!')
    elif software != "Thakkar IAM":
      try:
        wfn_object.run(part)
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
    exe_pre = OV.GetParam('user.NoSpherA2.discamb_exe')

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
    source = OV.GetParam('snum.NoSpherA2.source')
    BL = self.basis_list_str.split(";")
    from cctbx_olex_adapter import OlexCctbxAdapter
    XRS = OlexCctbxAdapter().xray_structure()
    max_Z = 1
    from cctbx import eltbx
    elements = eltbx.tiny_pse
    for sc in XRS.scatterers():
      if sc.electron_count() > max_Z:
        max_Z = sc.electron_count()
    final_string = ""
    for basis in BL:
      if self.check_for_atom_in_basis_set(basis, XRS, elements):
        final_string += basis + ";"
    if source == "ORCA" or source == "ORCA 5.0" or source == "fragHAR" or source == "Hybrid":
      if max_Z <= 86 and max_Z > 36:
        return final_string + ";ECP-def2-SVP;ECP-def2-TZVP;ECP-def2-TZVPP;ECP-def2-QZVP;ECP-def2-QZVPP"
    return final_string

  def disable_relativistics(self):
    basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    if "DKH" in basis_name:
      return False
    if "x2c" in basis_name:
      return False
    else:
      return True

  def getCPUListStr(self):
    soft = OV.GetParam('snum.NoSpherA2.source')
    import multiprocessing
    max_cpu = multiprocessing.cpu_count()
    cpu_list = ['1',]
    for n in range(1, max_cpu):
      cpu_list.append(str(n + 1))
    # ORCA and Tonto rely on MPI, so only make it available if mpiexec is found
    if soft == "Tonto" or "ORCA" in soft or soft == "fragHAR":
      if not os.path.exists(self.mpiexec):
        return '1'
    # otherwise allow more CPUs
    return ';'.join(cpu_list)

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
      if parts and len(parts) > 1:
        return self.softwares + ";Hybrid;"
    return self.softwares + ";"

  def available(self):
    return os.path.exists(self.wfn_2_fchk)

  def check_for_atom_in_basis_set(self, name, x_ray_struct, elements):
    BD = self.basis_dir
    basis_file = os.path.join(BD, name)
    if not os.path.exists(basis_file):
      return False
    basis = open(basis_file, "r")
    atoms = []
    for sc in x_ray_struct.scatterers():
      Z = sc.electron_count()
      t = elements.table(Z).symbol() + ":" + name
      if not any(t == atom for atom in atoms):
        atoms.append(t)
    basis.seek(0, 0)
    found = 0
    while True:
      line = basis.readline()
      if not line:
        break  # Check whether we ran into EOF
      if line[0] == "!" or line == '':
        continue
      if any(temp_atom in line for temp_atom in atoms):
        found += 1
        if found == len(atoms):
          return True
        continue
    if found != len(atoms):
      return False  # If any atoms are missing this basis set is not OK
    return True  # Only true if all atom searches were succesfull

@run_with_bitmap('Running DISCAMB')
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

  wavelength = float(olx.xf.exptl.Radiation())
  if wavelength < 0.1:
    args.append("-ED")
    os.environ['discamb_cmd'] = '+&-'.join([discamb_exe, "-e"])
  else:
    os.environ['discamb_cmd'] = discamb_exe
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

def change_basisset(input):
  OV.SetParam('snum.NoSpherA2.basis_name',input)
  if "x2c" in input:
    OV.SetParam('snum.NoSpherA2.Relativistic',True)
  elif "DKH" in input:
    OV.SetParam('snum.NoSpherA2.Relativistic',True)
  else:
    OV.SetParam('snum.NoSpherA2.Relativistic',False)
OV.registerFunction(change_basisset,True,'NoSpherA2')

def get_functional_list(wfn_code=None):
  if wfn_code == None:
    wfn_code = OV.GetParam('snum.NoSpherA2.source')
  list = None
  if wfn_code == "Tonto" or wfn_code == "'Please Select'":
    list = "HF;B3LYP;"
  elif wfn_code == "pySCF":
    list = "HF;PBE;B3LYP;BLYP;M062X"
  elif wfn_code == "ORCA 5.0" or wfn_code == "fragHAR":
    list = "HF;BP;BP86;PWLDA;R2SCAN;TPSS;PBE;PBE0;M062X;B3LYP;BLYP;wB97;wB97X;"
  else:
    list = "HF;BP;BP86;PWLDA;TPSS;PBE;PBE0;M062X;B3LYP;BLYP;wB97;wB97X;"
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
    if input != "DISCAMB" and input != "Thakkar IAM":
      OV.SetParam('snum.NoSpherA2.h_aniso', True)
      ne, adapter = calculate_number_of_electrons()
      mult = int(OV.GetParam('snum.NoSpherA2.multiplicity'))
      if mult == 0:
        if (ne % 2 == 0):
          OV.SetParam('snum.NoSpherA2.multiplicity',1)
        elif (ne % 2 != 0):
          OV.SetParam('snum.NoSpherA2.multiplicity',2)
    else:
      OV.SetParam('snum.NoSpherA2.h_aniso', False)
      OV.SetParam('snum.NoSpherA2.h_afix', False)
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
  OV.SetParam('snum.NoSpherA2.mem', str(tf_mem))
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

NoSpherA2_instance = NoSpherA2()
OV.registerFunction(NoSpherA2_instance.available, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.launch, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.delete_f_calc_f_obs_one_h, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getBasisListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getCPUListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getwfn_softwares, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.disable_relativistics, False, "NoSpherA2")

def hybrid_GUI():
  t = make_hybrid_GUI(NoSpherA2_instance.getwfn_softwares())
  return t
OV.registerFunction(hybrid_GUI, False, "NoSpherA2")

def get_NoSpherA2_instance():
  return NoSpherA2_instance
#print "OK."
