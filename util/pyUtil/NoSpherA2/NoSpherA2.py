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

from olexFunctions import OV
debug = OV.IsDebugging()

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
    self.wfn_job_dir = os.path.join(p_path,"olex2","Wfn_job")
    self.history_dir = os.path.join(p_path,"olex2","NoSpherA2_history")
    self.f_calc = None
    self.f_obs_sq = None
    self.one_h_linearisation = None
    self.reflection_date = None

    if not from_outside:
      self.setup_gui()

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
      print("No Hart executable found!")
    check_for_matching_fcf()
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

  def launch(self):
    OV.SetVar('NoSpherA2-Error',"None")
    wfn_code = OV.GetParam('snum.NoSpherA2.source')
    basis = OV.GetParam('snum.NoSpherA2.basis_name')
    update = OV.GetParam('snum.NoSpherA2.Calculate')
    if "Please S" in wfn_code and update == True:
      olx.Alert("No tsc generator selected",\
"""Error: No generator for tsc files selected.
Please select one of the generators from the drop-down menu.""", "O", False)
      OV.SetVar('NoSpherA2-Error',"TSC Generator unselected")
      return
    self.jobs_dir = os.path.join("olex2","Wfn_job")
    self.history_dir = os.path.join("olex2","NoSpherA2_history")
    if not os.path.exists(self.jobs_dir):
      os.mkdir(self.jobs_dir)
    if not os.path.exists(self.history_dir):
      os.mkdir(self.history_dir)

    if not update:
      return
    if not self.basis_list_str:
      print("Could not locate usable HARt executable")
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
          if file.endswith(".tsc"):
            shutil.move(os.path.join(olx.FilePath(),file),os.path.join(timestamp_dir,file))
          if file.endswith(".wfn") and ("wfn" not in wfn_code):
            shutil.move(os.path.join(olx.FilePath(),file),os.path.join(timestamp_dir,file))
          if file.endswith(".wfx"):
            shutil.move(os.path.join(olx.FilePath(),file),os.path.join(timestamp_dir,file))
          if file.endswith(".ffn"):
            shutil.move(os.path.join(olx.FilePath(),file),os.path.join(timestamp_dir,file))
          if file.endswith(".fchk"):
            shutil.move(os.path.join(olx.FilePath(),file),os.path.join(timestamp_dir,file))

    olex.m("CifCreate")

    parts = OV.ListParts()
    if parts != None:
      parts = list(parts)
    experimental_SF = OV.GetParam('snum.NoSpherA2.wfn2fchk_SF')

    nr_parts = None
    groups = None
    if not parts:
      nr_parts = 1
    elif len(parts) > 1:
      olx.Kill("$Q")
      cif = None
      if wfn_code == "Tonto":
        cif = True
      elif wfn_code == "DISCAMB":
        cif = True
      else:
        cif = False
      fn = os.path.join(self.jobs_dir ,"%s.cif" %(OV.ModelSrc()))
      olx.File(fn)
      parts, groups = deal_with_parts()
      nr_parts = len(parts)

    job = Job(self, olx.FileName())
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
        self.backup = os.path.join(self.jobs_dir, "Part_%d"%parts[i],"backup")
        to_backup = os.path.join(self.jobs_dir,"Part_%d"%parts[i])
        if os.path.exists(to_backup):
          l = 1
          while (os.path.exists(self.backup + "_%d"%l)):
            l = l + 1
          self.backup = self.backup + "_%d"%l
          os.mkdir(self.backup)
        Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
        self.wfn_job_dir = os.path.join(self.jobs_dir,"Part_%d"%parts[i])
        if os.path.exists(os.path.join(self.jobs_dir,olx.FileName()+".hkl")):
          os.remove(os.path.join(self.jobs_dir,olx.FileName()+".hkl"))
          run = None
          if Full_HAR == True:
            run = OV.GetVar('Run_number')
          files = (file for file in os.listdir(self.wfn_job_dir)
                  if os.path.isfile(os.path.join(self.wfn_job_dir, file)))
          for f in files:
            if Full_HAR == True:
              if run > 0:
                if wfn_code == "Tonto":
                  if "restricted" not in f:
                    f_work = os.path.join(self.wfn_job_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                elif wfn_code == "ORCA":
                  if ".gbw" not in f:
                    f_work = os.path.join(self.wfn_job_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                  else:
                    shutil.move(os.path.join(self.wfn_job_dir,f),os.path.join(self.wfn_job_dir,job.name+"2.gbw"))
                elif wfn_code == "ORCA 5.0":
                  if ".gbw" not in f:
                    f_work = os.path.join(self.wfn_job_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                  else:
                    shutil.move(os.path.join(self.wfn_job_dir,f),os.path.join(self.wfn_job_dir,job.name+"2.gbw"))
                elif "Gaussian" in wfn_code:
                  if ".chk" not in f:
                    f_work = os.path.join(self.wfn_job_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                elif "ELMOdb" in wfn_code:
                  if ".wfx" not in f:
                    f_work = os.path.join(self.wfn_job_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                elif "pySCF" in wfn_code:
                  if ".chk" not in f:
                    f_work = os.path.join(self.wfn_job_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                else:
                    f_work = os.path.join(self.wfn_job_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
              else:
                f_work = os.path.join(self.wfn_job_dir,f)
                f_dest = os.path.join(self.backup,f)
                shutil.move(f_work,f_dest)
            else:
              f_work = os.path.join(self.wfn_job_dir,f)
              f_dest = os.path.join(self.backup,f)
              shutil.move(f_work,f_dest)
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
          discamb(os.path.join(OV.FilePath(),self.wfn_job_dir), job.name, self.discamb_exe)
          shutil.copy(os.path.join(self.wfn_job_dir,job.name+".tsc"),job.name+"_part_"+str(parts[i])+".tsc")
          shutil.copy(os.path.join(self.wfn_job_dir,"discamb2tsc.log"),os.path.join(self.jobs_dir,"discamb2tsc.log"))
          need_to_combine = True
        elif wfn_code == "Hybrid":
          hybrid_part_wfn_code = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d"%(parts[i]))
          if hybrid_part_wfn_code == "DISCAMB":
            groups.pop(i-groups_counter)
            groups_counter+=1
            discamb(os.path.join(OV.FilePath(),self.wfn_job_dir), job.name, self.discamb_exe)
            shutil.copy(os.path.join(self.wfn_job_dir,job.name+".tsc"),job.name+"_part_"+str(parts[i])+".tsc")
            shutil.copy(os.path.join(self.wfn_job_dir,"discamb2tsc.log"),os.path.join(self.jobs_dir,"discamb2tsc.log"))
            need_to_combine = True
          else:
            need_to_partition = True
            shutil.move("%s_part_%s.xyz" %(OV.ModelSrc(), parts[i]),os.path.join(self.wfn_job_dir,"%s.xyz"%(OV.ModelSrc())))
            try:
              self.wfn(folder=self.wfn_job_dir,xyz=False,part=parts[i])
            except NameError as error:
              print ("Aborted due to: ",error)
              OV.SetVar('NoSpherA2-Error',error)
              return False         
            path_base = os.path.join(OV.FilePath(),self.wfn_job_dir, job.name)
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
              if file.endswith(".wfn"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfn"
                shutil.move(file,temp)
              elif file.endswith(".wfx"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfx"
                shutil.move(file,temp)
                if (wfn_fn == None or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".fchk")): wfn_fn = temp
              elif file.endswith(".ffn"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".ffn"
                shutil.move(file,temp)
              elif file.endswith(".fchk"):
                temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".fchk"
                shutil.move(file,temp)
                if (wfn_fn == None or wfn_fn.endswith(".wfn")): wfn_fn = temp
            wfn_files.append(wfn_fn)
        else:
          need_to_partition = True
          if wfn_code != "Tonto":
            shutil.move("%s_part_%s.xyz" %(OV.ModelSrc(), parts[i]),os.path.join(self.wfn_job_dir,"%s.xyz"%(OV.ModelSrc())))
            if wfn_code == "ELMOdb":
              mutation = OV.GetParam('snum.NoSpherA2.ELMOdb.mutation')
              pdb_name = job.name + ".pdb"
              if mutation == True:
                pdb_name += "_mut"+str(parts[i])
              if os.path.exists(os.path.join(OV.FilePath(),pdb_name)):
                shutil.copy(os.path.join(OV.FilePath(),pdb_name),os.path.join(self.wfn_job_dir,job.name + ".pdb"))
              else:
                OV.SetVar('NoSpherA2-Error',"ELMOdb")
                if mutation == True:
                  raise NameError('No pdb_name file available for mutation!')
                else:
                  raise NameError('No pdb file available! Make sure the name of the pdb file is the same as the name of your ins file!')
            OV.SetParam('snum.NoSpherA2.fchk_file',olx.FileName() + ".fchk")
            try:
              self.wfn(folder=self.wfn_job_dir,xyz=False,part=parts[i]) # Produces Fchk file in all cases that are not fchk or tonto directly
            except NameError as error:
              print ("Aborted due to: ",error)
              OV.SetVar('NoSpherA2-Error',error)
              return False
          if experimental_SF == False or wfn_code == "Tonto":
            try:
              job.launch(self.wfn_job_dir)
            except NameError as error:
              print ("Aborted due to: ", error)
              OV.SetVar('NoSpherA2-Error',error)
              return False
            if 'Error in' in open(os.path.join(job.full_dir, job.name+".err")).read():
              OV.SetVar('NoSpherA2-Error',"StructrueFactor")
              return False
            olx.html.Update()
            shutil.copy(os.path.join(job.full_dir, job.name+".tsc"),job.name+"_part_"+str(parts[i])+".tsc")
          elif wfn_code == "Thakkar IAM":
            wfn_fn = os.path.join(OV.FilePath(),self.wfn_job_dir, job.name+".xyz")
          else:
            wfn_fn = None
            path_base = os.path.join(OV.FilePath(),self.wfn_job_dir, job.name)
            if os.path.exists(path_base+".wfx"):
              wfn_fn = path_base+".wfx"
            elif os.path.exists(path_base+".fchk"):
              wfn_fn = path_base+".fchk"
            elif os.path.exists(path_base+".wfn"):
              wfn_fn = path_base+".wfn"
            else:
              return False
          for file in os.listdir(os.getcwd()):
            if file.endswith(".wfn"):
              temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfn"
              shutil.move(file,temp)
            elif file.endswith(".wfx"):
              temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".wfx"
              shutil.move(file,temp)
              if (wfn_fn == None or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".fchk")): 
                wfn_fn = temp
            elif file.endswith(".ffn"):
              temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".ffn"
              shutil.move(file,temp)
            elif file.endswith(".fchk"):
              temp = os.path.splitext(file)[0] + "_part%d"%parts[i] + ".fchk"
              shutil.move(file,temp)
              if (wfn_fn == None): 
                wfn_fn = temp
          wfn_files.append(wfn_fn)
      if need_to_partition == True:
        cif_fn = os.path.join(OV.FilePath(),job.name+".cif")
        hkl_fn = os.path.join(self.jobs_dir,job.name+".hkl")
        combined_NoSpherA2_tsc(cif_fn,hkl_fn,groups,wfn_files)
        shutil.move("experimental.tsc",job.name+".tsc")
        OV.SetParam('snum.NoSpherA2.file',job.name+".tsc")
      if need_to_combine == True:
        #Too lazy to properly do it...
        if os.path.exists(job.name+".tsc"):
          shutil.move(job.name+".tsc",job.name+"_part_999.tsc")
        combine_tscs()
      
    else:
      # Check if job folder already exists and (if needed) make the backup folders
      self.backup = os.path.join(self.jobs_dir, "backup")
      if os.path.exists(os.path.join(self.jobs_dir,olx.FileName()+".hkl")):
        Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
        run = None
        if Full_HAR == True:
          run = OV.GetVar('Run_number')
        i = 1
        while (os.path.exists(self.backup + "_%d"%i)):
          i = i + 1
        self.backup = self.backup + "_%d"%i
        os.mkdir(self.backup)
        try:
          if wfn_code == "ORCA":
            if os.path.exists(os.path.join(self.jobs_dir,job.name+"2.gbw")):
              os.remove(os.path.join(self.jobs_dir,job.name+"2.gbw"))
          if wfn_code == "ORCA 5.0":
            if os.path.exists(os.path.join(self.jobs_dir,job.name+"2.gbw")):
              os.remove(os.path.join(self.jobs_dir,job.name+"2.gbw"))
          files = (file for file in os.listdir(self.jobs_dir)
                  if os.path.isfile(os.path.join(self.jobs_dir, file)))
          for f in files:
            if Full_HAR == True:
              if run > 0:
                if wfn_code == "Tonto":
                  if "restricted" not in f:
                    f_work = os.path.join(self.jobs_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                elif wfn_code == "ORCA":
                  if ".gbw" not in f:
                    f_work = os.path.join(self.jobs_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                  else:
                    shutil.move(os.path.join(self.jobs_dir,f),os.path.join(self.jobs_dir,job.name+"2.gbw"))
                elif wfn_code == "ORCA 5.0":
                  if ".gbw" not in f:
                    f_work = os.path.join(self.jobs_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                  else:
                    shutil.move(os.path.join(self.jobs_dir,f),os.path.join(self.jobs_dir,job.name+"2.gbw"))
                elif "Gaussian" in wfn_code:
                  if ".chk" not in f:
                    f_work = os.path.join(self.jobs_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                elif "ELMOdb" in wfn_code:
                  if ".wfx" not in f:
                    f_work = os.path.join(self.wfn_job_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                elif "pySCF" in wfn_code:
                  if ".chk" not in f:
                    f_work = os.path.join(self.wfn_job_dir,f)
                    f_dest = os.path.join(self.backup,f)
                    shutil.move(f_work,f_dest)
                else:
                  f_work = os.path.join(self.jobs_dir,f)
                  f_dest = os.path.join(self.backup,f)
                  shutil.move(f_work,f_dest)
              else:
                f_work = os.path.join(self.jobs_dir,f)
                f_dest = os.path.join(self.backup,f)
                shutil.move(f_work,f_dest)
            else:
              f_work = os.path.join(self.jobs_dir,f)
              f_dest = os.path.join(self.backup,f)
              shutil.move(f_work,f_dest)
        except:
          pass

      # Make a wavefunction (in case of tonto wfn code and tonto tsc file do it at the same time)

      if wfn_code == "DISCAMB":
        cif = str(os.path.join(job.full_dir, job.name+".cif"))
        olx.File(cif)
        discamb(os.path.join(OV.FilePath(),job.full_dir), olx.FileName(), self.discamb_exe)
        shutil.copy(os.path.join(OV.FilePath(),job.full_dir,job.name+".tsc"),job.name+".tsc")
        OV.SetParam('snum.NoSpherA2.file',job.name+".tsc")
      else:
        if wfn_code.lower().endswith(".wfn"):
          pass
        elif wfn_code == "Tonto":
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
            if os.path.exists(os.path.join(OV.FilePath(),job.name + ".pdb")):
              shutil.copy(os.path.join(OV.FilePath(),job.name + ".pdb"),os.path.join(job.full_dir,job.name + ".pdb"))
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
            path_base = os.path.join(OV.FilePath(),job.full_dir, job.name)
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
            cif_fn = os.path.join(OV.FilePath(),job.name+".cif")
            cuqct_tsc(wfn_fn,hkl_fn,cif_fn,[-1000])
            shutil.move("experimental.tsc",job.name+".tsc")
            OV.SetParam('snum.NoSpherA2.file',job.name+".tsc")

        elif wfn_code != "Tonto":
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
    
    wfn_object = wfn_Job(self,olx.FileName(),dir=folder)
    software = OV.GetParam('snum.NoSpherA2.source')
    if software == "fragHAR":
      from .fragHAR import run_frag_HAR_wfn
      main_folder = OV.FilePath()
      res_file = os.path.join(main_folder,olx.FileName()+".res")
      cif_file = os.path.join(main_folder,olx.FileName()+".cif")
      qS_file = os.path.join(main_folder,olx.FileName()+".qS")
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
          wfn_object.run(part,software_part,basis_part)
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
    exe_pre = "discamb2tsc"

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
        self.discamb_exe = olx.file.Which("%s" %exe_pre)
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

  def __init__(self, parent, name, dir):
    self.parent = parent
    self.status = 0
    self.name = name
    self.parallel = parent.parallel
#    self.ubuntu_exe = parent.ubuntu_exe
    if self.name.endswith('_HAR'):
      self.name = self.name[:-4]
    elif self.name.endswith('_input'):
      self.name = self.name[:-6]
    full_dir = '.'
    self.full_dir = full_dir
    if dir != '':
      self.full_dir = dir
      full_dir = dir

    if not os.path.exists(full_dir):
      return
    self.date = os.path.getctime(full_dir)
    self.log_fn = os.path.join(full_dir, name) + ".log"
    self.fchk_fn = os.path.join(full_dir, name) + ".fchk"
    self.completed = os.path.exists(self.fchk_fn)
    initialised = False

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
        com.write(line)
        if not atom[0] in atom_list:
          atom_list.append(atom[0])
    xyz.close()
    com.write(" \n")
    for i in range(0,len(atom_list)):
      atom_type = atom_list[i] + " 0\n"
      com.write(atom_type)
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

  def write_orca_crystal_input(self,xyz):
    def write_grids_5(method,grid):
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
    coordinates_fn1 = os.path.join(self.full_dir, "asu") + ".xyz"
    olx.Kill("$Q")
    if xyz:
      olx.File(coordinates_fn1,p=10)
    olx.File(os.path.join(self.full_dir, self.name + ".cif"))
    xyz1 = open(coordinates_fn1,"r")
    coordinates_fn2 = os.path.join(self.full_dir, self.name) + ".xyz"
    radius = OV.GetParam("snum.NoSpherA2.ORCA_CRYSTAL_QMMM_RADIUS")
    olex.m("pack %s -c"%radius)
    if xyz:
      olx.File(coordinates_fn2,p=10)
    xyz2 = open(coordinates_fn2,"r")
    olex.m("fuse")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".inp"
    inp = open(self.input_fn,"w")
    basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    basis_set_fn = os.path.join(self.parent.basis_dir,basis_name)
    basis = open(basis_set_fn,"r")
    ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
    if OV.GetParam('snum.NoSpherA2.ncpus') != '1':
      cpu = "nprocs " + ncpus
    else:
      cpu = "nprocs 1"
    mem = OV.GetParam('snum.NoSpherA2.mem')
    mem_value = float(mem) * 1024 / int(ncpus)
    mem = "%maxcore " + str(mem_value)
    qmmmtype = OV.GetParam("snum.NoSpherA2.ORCA_CRYSTAL_QMMM_TYPE")
    control = "! NoPop MiniPrint 3-21G AIM "
    if qmmmtype == "Mol":
      control += "MOL-CRYSTAL-QMMM "
    else:
      control += "IONIC-CRYSTAL-QMMM "
    method = OV.GetParam('snum.NoSpherA2.method')
    grid = OV.GetParam('snum.NoSpherA2.becke_accuracy')
    if method == "HF":
      control += "rhf "
      grids = ""
    else:
      SCNL = OV.GetParam('snum.NoSpherA2.ORCA_SCNL')
      if SCNL == True:
        if method != "wB97" and method != "wB97X":
          control += method + ' SCNL '
        else:
          control += method + '-V SCNL '
      else:
        control += method + ' '
      software = OV.GetParam("snum.NoSpherA2.source")
      if software == "ORCA 5.0":
        grids = write_grids_5(method,grid)
      else:
        print("MOL-CRYSTAL-QMMM only works from ORCA 5.0 upwards")
    convergence = OV.GetParam('snum.NoSpherA2.ORCA_SCF_Conv')
    if convergence == "NoSpherA2SCF":
      conv = " LooseSCF"
    else:
      conv = convergence
    control = control + grids + ' ' + conv + ' ' + OV.GetParam('snum.NoSpherA2.ORCA_SCF_Strategy')
    relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
    if method == "BP86" or method == "PBE" or method == "PWLDA":
      if relativistic == True:
        control = control + " DKH2 SARC/J RI RIJCOSX"
      else:
        control = control + " def2/J RI RIJCOSX"
    else:
      if relativistic == True:
        control = control + " DKH2 SARC/J RIJCOSX"
      else:
        control = control + " def2/J RIJCOSX"
    Solvation = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
    if Solvation != "Vacuum" and Solvation != None:
      control += " CPCM("+Solvation+") "
    charge = OV.GetParam('snum.NoSpherA2.charge')
    mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    inp.write(control + '\n' + "%pal\n" + cpu + '\n' + "end\n" + mem + '\n' + "%coords\n        CTyp xyz\n        charge " + charge + "\n        mult " + mult + "\n        units angs\n        coords\n")
    atom_list = []
    i = 0
    for line in xyz2:
      i = i+1
      if i > 2:
        atom = line.split()
        inp.write(line)
        if not atom[0] in atom_list:
          atom_list.append(atom[0])
    inp.write("   end\nend\n%basis\n")
    for i in range(0,len(atom_list)):
      atom_type = "newgto " +atom_list[i] + '\n'
      inp.write(atom_type)
      temp_atom = atom_list[i] + ":" + basis_name
      basis.seek(0,0)
      while True:
        line = basis.readline()
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
    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
    conv = OV.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_CONV')
    hflayer = OV.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_HF_LAYERS')
    inp.write("%qmmm\n  Conv_Charges true\n")
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
    inp.write("  QMAtoms {%s } end\n"%qm_atoms)
    inp.write("  Conv_Charges_MaxNCycles 30\n  Conv_Charge_UseQMCoreOnly true\n  Conv_Charges_ConvThresh %f\n  HFLayers %d\nend"%(float(conv),hflayer))
    run = None
    if Full_HAR == True:
      run = OV.GetVar('Run_number')
      if run > 1:
        inp.write("%scf\n   Guess MORead\n   MOInp \""+self.name+"2.gbw\"\nend\n")
    inp.close()

  def write_orca_input(self,xyz,basis_name=None,method=None,relativistic=None,charge=None,mult=None,strategy=None,convergence=None,part=None):
    def write_grids_4(method,grid):
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

    def write_grids_5(method,grid):
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
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    if xyz:
      self.write_xyz_file()
    xyz = open(coordinates_fn,"r")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".inp"
    inp = open(self.input_fn,"w")
    if basis_name == None:
      basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    basis_set_fn = os.path.join(self.parent.basis_dir,basis_name)
    basis = open(basis_set_fn,"r")
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
    control = "! NoPop MiniPrint 3-21G AIM "

    grid = OV.GetParam('snum.NoSpherA2.becke_accuracy')
    if method == "HF":
      control += "rhf "
      grids = ""
    else:
      software = OV.GetParam("snum.NoSpherA2.source")
      if software == "Hybrid":
        software = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d"%part)
      elif software == "fragHAR":
        software = "ORCA 5.0"
      if software == "ORCA 5.0":
        SCNL = OV.GetParam('snum.NoSpherA2.ORCA_SCNL')
        if SCNL == True:
          if method != "wB97" and method != "wB97X":
            control += method + ' SCNL '
          else:
            control += method + '-V SCNL '
        else:
          control += method + ' '
        grids = write_grids_5(method,grid)
      else:
        control += method + ' '
        grids = write_grids_4(method,grid)
    if convergence == None:
      convergence = OV.GetParam('snum.NoSpherA2.ORCA_SCF_Conv')
    if convergence == "NoSpherA2SCF":
      conv = "LooseSCF"
    else:
      conv = convergence
    if strategy == None:
      strategy = OV.GetParam('snum.NoSpherA2.ORCA_SCF_Strategy')
    control = control + grids + conv + ' ' + strategy
    if relativistic == None:
      relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
    if method == "BP86" or method == "PBE" or method == "PWLDA":
      if relativistic == True:
        t = OV.GetParam('snum.NoSpherA2.ORCA_Relativistic')
        if t == "DKH2":
          control = control + " DKH2 SARC/J RI"
        elif t == "ZORA":
          control = control + " ZORA SARC/J RI"
        elif t == "ZORA/RI":
          control = control + " ZORA/RI SARC/J RI"
        else:
          control = control + " IORA/RI SARC/J RI"
      else:
        control = control + " def2/J RI"
    else:
      if relativistic == True:
        t = OV.GetParam('snum.NoSpherA2.ORCA_Relativistic')
        if t == "DKH2":
          control = control + " DKH2 SARC/J RIJCOSX"
        elif t == "ZORA":
          control = control + " ZORA SARC/J RIJCOSX"
        elif t == "ZORA/RI":
          control = control + " ZORA/RI SARC/J RIJCOSX"
        else:
          control = control + " IORA/RI SARC/J RIJCOSX"
      else:
        control = control + " def2/J RIJCOSX"
    Solvation = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
    if Solvation != "Vacuum" and Solvation != None:
      control += " CPCM("+Solvation+") "
    if charge == None:
      charge = OV.GetParam('snum.NoSpherA2.charge')
    if mult == None:
      mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    inp.write(control + '\n' + "%pal\n" + cpu + '\n' + "end\n" + mem + '\n' + "%coords\n        CTyp xyz\n        charge " + charge + "\n        mult " + mult + "\n        units angs\n        coords\n")
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
      temp_atom = atom_list[i] + ":" + basis_name
      basis.seek(0,0)
      while True:
        line = basis.readline()
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
    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
    run = None
    if Full_HAR == True:
      run = OV.GetVar('Run_number')
      source = OV.GetParam('snum.NoSpherA2.source')
      if source == "Hybrid":
        run = 0
      if run > 1:
        inp.write("%scf\n   Guess MORead\n   MOInp \""+self.name+"2.gbw\"")
        if convergence == "NoSpherA2SCF":
          inp.write("\n   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4")        
      else:
        if convergence == "NoSpherA2SCF":
          inp.write("%scf\n   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4")
      if run > 1 or convergence == "NoSpherA2SCF":
        inp.write("\nend\n")
    else:
      if convergence == "NoSpherA2SCF":
        inp.write("%scf\n   TolE 3E-5\n   TolErr 1E-4\n   Thresh 1E-9\n   TolG 3E-4\n   TolX 3E-4\nend\n")      
    inp.close()

  def write_psi4_input(self,xyz):
    if xyz:
      self.write_xyz_file()

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
        inp.write("mf.xc = 'M06X2X,M06X2C'\n")
      elif method == "PBE0":
        inp.write("mf.xc = 'PBE0'\n")
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

  def run(self,part=0,software=None,basis_name=None):
    args = []
    if basis_name == None:
      basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    if software == None:
      software = OV.GetParam('snum.NoSpherA2.source')

    gui.get_default_notification(
          txt="Calculating Wavefunction for <font color=$GetVar(gui.green_text)><b>%s</b></font> using <font color=#000000><b>%s</b></font>..."%(self.name,software),
          txt_col='black_text')
    python_script = "fchk-launch.py"

    if software == "ORCA":
      args.append(self.parent.orca_exe)
      input_fn = self.name + ".inp"
      args.append(input_fn)
    if software == "ORCA 5.0" or software == "fragHAR":
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
      elif self.ubuntu_exe == None:
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

    os.environ['fchk_cmd'] = '+&-'.join(args)
    os.environ['fchk_file'] = self.name
    os.environ['fchk_dir'] = os.path.join(OV.FilePath(),self.full_dir)

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
                            startupinfo=startinfo)
    else:
      pyl = OV.getPYLPath()
      if not pyl:
        print("A problem with pyl is encountered, aborting.")
        return
      p = subprocess.Popen([pyl,
                            os.path.join(p_path, python_script)])

    out_fn = None
    path = self.full_dir
    nr = 0
    if sys.platform[:3] == 'win':
      nr = 2
    #if part != 0:
    #  path = os.path.join(path,"Part_"+str(part))
    if software =="Psi4":
      out_fn = os.path.join(path,self.name + "_psi4.log")
    else:
      if "orca" in args[0]:
        out_fn = os.path.join(path,self.name + "_orca.log")
      elif "elmo" in args[nr]:
        out_fn = os.path.join(path,self.name + ".out")
      elif "python" in args[nr]:
        out_fn = os.path.join(path,self.name + "_pyscf.log")
      if "ubuntu" in args[0]:
        print("Starting Ubuntu for wavefunction calculation, please be patient for start")
      if out_fn == None:
        if "ubuntu" in args[0]:
          out_fn = os.path.join(path,self.name + "_pyscf.log")
        else:
          out_fn = os.path.join(path,self.name + ".log")

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
        time.sleep(0.5)

    print("\nWavefunction calculation ended!")

    if software == "ORCA" or software == "ORCA 5.0":
      if '****ORCA TERMINATED NORMALLY****' in open(os.path.join(self.full_dir, self.name+"_orca.log")).read():
        pass
      else:
        OV.SetVar('NoSpherA2-Error',"ORCA")
        with open(os.path.join(self.full_dir, self.name+"_orca.log")) as file:
          lines = file.readlines()
        for line in lines:
          if "Error" in line:
            print(line)
        raise NameError('Orca did not terminate normally!')
    elif "Gaussian" in software:
      if 'Normal termination of Gaussian' in open(os.path.join(self.full_dir, self.name+".log")).read():
        pass
      else:
        OV.SetVar('NoSpherA2-Error',"Gaussian")
        raise NameError('Gaussian did not terminate normally!')
    elif software == "ELMOdb":
      print(os.path.join(self.full_dir, self.name+".out"))
      if 'CONGRATULATIONS: THE ELMO-TRANSFERs ENDED GRACEFULLY!!!' in open(os.path.join(self.full_dir, self.name+".out")).read():
        pass
      else:
        OV.SetVar('NoSpherA2-Error',"ELMOdb")
        with open(os.path.join(self.full_dir, self.name+".out")) as file:
          lines = file.readlines()
        for line in lines:
          if "Error" in line:
            print(line)
        raise NameError('ELMOdb did not terminate normally!')

    if("g03" in args[0]):
      shutil.move(os.path.join(self.full_dir,"Test.FChk"),os.path.join(self.full_dir,self.name+".fchk"))
      shutil.move(os.path.join(self.full_dir,self.name + ".log"),os.path.join(self.full_dir,self.name+"_g03.log"))
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfx"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfx"), self.name+".wfx")
    elif("g09" in args[0]):
      shutil.move(os.path.join(self.full_dir,"Test.FChk"),os.path.join(self.full_dir,self.name+".fchk"))
      shutil.move(os.path.join(self.full_dir,self.name + ".log"),os.path.join(self.full_dir,self.name+"_g09.log"))
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfx"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfx"), self.name+".wfx")
    elif("g16" in args[0]):
      shutil.move(os.path.join(self.full_dir,"Test.FChk"),os.path.join(self.full_dir,self.name+".fchk"))
      shutil.move(os.path.join(self.full_dir,self.name + ".log"),os.path.join(self.full_dir,self.name+"_g16.log"))
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfx"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfx"), self.name+".wfx")
    elif("orca" in args[0]):
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfx"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfx"), self.name+".wfx")
    elif("elmodb" in args[0]):
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfx"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfx"), self.name+".wfx")
    elif(software == "Psi4"):
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".fchk"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".fchk"), self.name+".fchk")
    elif software == "pySCF":
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")

    experimental_SF = OV.GetParam('snum.NoSpherA2.wfn2fchk_SF')

    if (experimental_SF == False) and ("g" not in args[0]):
      move_args = []
      basis_dir = self.parent.basis_dir
      mult = str(OV.GetParam('snum.NoSpherA2.multiplicity'))
      move_args.append(self.parent.wfn_2_fchk)
      move_args.append("-wfn")
      move_args.append(self.name+".wfn")
      move_args.append("-mult")
      move_args.append(mult)
      move_args.append("-b")
      move_args.append(basis_name)
      move_args.append("-d")
      if sys.platform[:3] == 'win':
        move_args.append(basis_dir.replace("/","\\"))
      else:
        move_args.append(basis_dir+'/')
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
      if os.path.exists(self.name+".fchk"):
        shutil.copy(self.name+".fchk",os.path.join(self.full_dir, self.name+".fchk"))
      else:
        OV.SetVar('NoSpherA2-Error',"NoFchk")
        raise NameError("No fchk generated!")
      shutil.move("NoSpherA2.log",os.path.join(self.full_dir, self.name+"_NoSpherA2.log"))

def multi_CIF_NoSpherA2_tsc(cif_fns,hkl_fn,groups,wfn_files):
  folder = OV.FilePath()
  gui.get_default_notification(
        txt="Calculating .tsc file from Wavefunction <b>%s</b>..."%os.path.basename(wfn_files[0]),
        txt_col='black_text')
  ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
  if os.path.isfile(os.path.join(folder, "NoSpherA2.log")):
    shutil.move(os.path.join(folder, "NoSpherA2.log"), os.path.join(folder, "NoSpherA2.log_org"))
  args = []
  wfn_2_fchk = OV.GetVar("Wfn2Fchk")
  args.append(wfn_2_fchk)
  if not os.path.exists(hkl_fn):
    from cctbx_olex_adapter import OlexCctbxAdapter
    cctbx_adaptor = OlexCctbxAdapter()
    with open(hkl_fn, "w") as out:
      f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_merged
      f_sq_obs = f_sq_obs.complete_array(d_min_tolerance=0.01, d_min=f_sq_obs.d_max_min()[1], d_max=f_sq_obs.d_max_min()[0], new_data_value=-1, new_sigmas_value=-1)
      f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
  args.append("-hkl")
  args.append(hkl_fn)
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
  olex_refinement_model = OV.GetRefinementModel(False)
  curr_law = None

  try:
    src = OV.HKLSrc()
    cmd = "HKLF5 -e %s" %src
    res = scrub(cmd)
    if "HKLF5 file is expected" in " ".join(res):
      pass
    elif "negative batch numbers" in " ".join(res):
      pass
    else:
      curr_law = []
      for i in res[4].split():
        curr_law.append(i)
      for i in res[6].split():
        curr_law.append(i)
      for i in res[8].split():
        curr_law.append(i)
      curr_law = tuple(curr_law)
      args.append("-twin")
      for i in curr_law:
        args.append(str(int(i)))
  except:
    print("I think this is not an HKLF5...")

  if 'twin' in olex_refinement_model:
    c = olex_refinement_model['twin']['matrix']
    curr_law = []
    for row in c:
      for el in row:
        curr_law.append(el)
    curr_law = tuple(curr_law)
    args.append("-twin")
    for i in curr_law:
      args.append(str(float(i)))

  args.append("-cmtc")
  if len(wfn_files) != len(groups):
    print("Insonstiant size of parameters! ERROR!")
    return
  for i in range(len(wfn_files)):
    args.append(wfn_files[i])
    args.append(cif_fns[i])
    for j in range(len(groups[i])):
      groups[i][j] = str(groups[i][j])
    args.append(','.join(groups[i]))

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
    time.sleep(1)
    tries += 1
    if tries >= 5:
      if "python" in args[2] and tries <=10:
        continue
      print("Failed to locate the output file")
      OV.SetVar('NoSpherA2-Error',"NoSpherA2-Output not found!")
      raise NameError('NoSpherA2-Output not found!')

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

def combined_NoSpherA2_tsc(cif_fn,hkl_fn,groups,wfn_files):
  folder = OV.FilePath()
  gui.get_default_notification(
        txt="Calculating .tsc file from Wavefunction <b>%s</b>..."%os.path.basename(wfn_files[0]),
        txt_col='black_text')
  ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
  if os.path.isfile(os.path.join(folder, "NoSpherA2.log")):
    shutil.move(os.path.join(folder, "NoSpherA2.log"), os.path.join(folder, "NoSpherA2.log_org"))
  args = []
  wfn_2_fchk = OV.GetVar("Wfn2Fchk")
  args.append(wfn_2_fchk)
  if not os.path.exists(hkl_fn):
    from cctbx_olex_adapter import OlexCctbxAdapter
    #from iotbx.shelx import hklf
    cctbx_adaptor = OlexCctbxAdapter()
    with open(hkl_fn, "w") as out:
      f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_merged
      f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
  args.append("-hkl")
  args.append(hkl_fn)
  args.append("-cif")
  args.append(cif_fn)
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
  olex_refinement_model = OV.GetRefinementModel(False)
  curr_law = None

  try:
    src = OV.HKLSrc()
    cmd = "HKLF5 -e %s" %src
    res = scrub(cmd)
    if "HKLF5 file is expected" in " ".join(res):
      pass
    elif "negative batch numbers" in " ".join(res):
      pass
    else:
      curr_law = []
      for i in res[4].split():
        curr_law.append(i)
      for i in res[6].split():
        curr_law.append(i)
      for i in res[8].split():
        curr_law.append(i)
      curr_law = tuple(curr_law)
      args.append("-twin")
      for i in curr_law:
        args.append(str(float(i)))
  except:
    print("I think this is not an HKLF5...")

  if 'twin' in olex_refinement_model:
    c = olex_refinement_model['twin']['matrix']
    curr_law = []
    for row in c:
      for el in row:
        curr_law.append(el)
    curr_law = tuple(curr_law)
    args.append("-twin")
    for i in curr_law:
      args.append(str(float(i)))

  args.append("-mtc")
  if len(wfn_files) != len(groups):
    print("Insonstiant size of parameters! ERROR!")
    return
  for i in range(len(wfn_files)):
    args.append(wfn_files[i])
    for j in range(len(groups[i])):
      groups[i][j] = str(groups[i][j])
    args.append(','.join(groups[i]))

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
    time.sleep(1)
    tries += 1
    if tries >= 5:
      if "python" in args[2] and tries <=10:
        continue
      print("Failed to locate the output file")
      OV.SetVar('NoSpherA2-Error',"NoSpherA2-Output not found!")
      raise NameError('NoSpherA2-Output not found!')

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

def cuqct_tsc(wfn_file, hkl_file, cif, groups, save_k_pts=False, read_k_pts=False):
  folder = OV.FilePath()
  gui.get_default_notification(
        txt="Calculating .tsc file from Wavefunction <b>%s</b>..."%os.path.basename(wfn_file),
        txt_col='black_text')
  ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
  if os.path.isfile(os.path.join(folder, "NoSpherA2.log")):
    shutil.move(os.path.join(folder, "NoSpherA2.log"), os.path.join(folder, "NoSpherA2.log_org"))
  args = []
  wfn_2_fchk = OV.GetVar("Wfn2Fchk")
  args.append(wfn_2_fchk)
  args.append("-wfn")
  args.append(wfn_file)
  if not os.path.exists(hkl_file):
    from cctbx_olex_adapter import OlexCctbxAdapter
    cctbx_adaptor = OlexCctbxAdapter()
    with open(hkl_file, "w") as out:
      f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_merged
      f_sq_obs = f_sq_obs.complete_array(d_min_tolerance=0.01, d_min=f_sq_obs.d_max_min()[1], d_max=f_sq_obs.d_max_min()[0], new_data_value=-1, new_sigmas_value=-1)
      f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
  args.append("-hkl")
  args.append(hkl_file)
  args.append("-cif")
  args.append(cif)
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
  if(groups[0] != -1000):
    args.append('-group')
    for i in range(len(groups)):
      args.append(groups[i])
  if(save_k_pts):
    args.append('-skpts')
  if(read_k_pts):
    args.append('-rkpts')
  olex_refinement_model = OV.GetRefinementModel(False)
  curr_law = None

  # are only integral twin laws supported here? could use a more comprehensive
  # reporting then if non-integral occurs.
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
    time.sleep(1)
    tries += 1
    if tries >= 5:
      if "python" in args[2] and tries <=10:
        continue
      print("Failed to locate the output file")
      OV.SetVar('NoSpherA2-Error',"NoSpherA2-Output not found!")
      raise NameError('NoSpherA2-Output not found!')

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
  cif = os.path.join(folder,name+".cif")
#  move_args.append(cif)
#  move_args.append(hkl_file)
  if not os.path.exists(hkl_file):
    from cctbx_olex_adapter import OlexCctbxAdapter
    from iotbx.shelx import hklf
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
    initialised = False

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
      from iotbx.shelx import hklf
      cctbx_adaptor = OlexCctbxAdapter()
      with open(data_file_name, "w") as out:
        f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_filtered
        f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)

    # We are asking to just get form factors to disk
    fchk_source = OV.GetParam('snum.NoSpherA2.source')
    if fchk_source == "Tonto":
      # We want these from a wavefunction calculation using TONTO """

      run = OV.GetVar('Run_number')

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
    f_time = os.path.getctime(file)
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

def get_ntail_list():
  # for tailor made residues in ELMOdb
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    ntail_list = ['1',]
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if maxtail == 1:
      ntail_list_str = "1;"
    else:
      for n in range(1,maxtail):
        ntail_list.append(str(n+1))
        ntail_list_str = ';'.join(ntail_list)
    return ntail_list_str
OV.registerFunction(get_ntail_list,True,'NoSpherA2')

def get_resname():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    resnames = OV.GetParam('snum.NoSpherA2.ELMOdb.str_resname')
    resnames = resnames.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(resnames) < maxtail:
      diff = maxtail - len(resnames)
      for i in range(diff):
        resnames.append('???')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return resnames[n]
OV.registerFunction(get_resname,True,'NoSpherA2')

def get_nat():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    nat = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nat')
    nat = nat.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(nat) < maxtail:
      diff = maxtail - len(nat)
      for i in range(diff):
        nat.append('0')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return nat[n]
OV.registerFunction(get_nat,True,'NoSpherA2')

def get_nfrag():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    nfrag = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nfrag')
    nfrag = nfrag.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(nfrag) < maxtail:
      diff = maxtail - len(nfrag)
      for i in range(diff):
        nfrag.append('1')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return nfrag[n]
OV.registerFunction(get_nfrag,True,'NoSpherA2')

def get_ncltd():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    ncltd = OV.GetParam('snum.NoSpherA2.ELMOdb.str_ncltd')
    ncltd = ncltd.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(ncltd) < maxtail:
      diff = maxtail - len(ncltd)
      for i in range(diff):
        ncltd.append(False)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return ncltd[n]
OV.registerFunction(get_ncltd,True,'NoSpherA2')

def get_specac():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    specac = OV.GetParam('snum.NoSpherA2.ELMOdb.str_specac')
    specac = specac.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(specac) < maxtail:
      diff = maxtail - len(specac)
      for i in range(diff):
        specac.append(False)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return specac[n]
OV.registerFunction(get_specac,True,'NoSpherA2')

def get_exbsinp():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    exbsinp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_exbsinp')
    exbsinp = exbsinp.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(exbsinp) < maxtail:
      diff = maxtail - len(exbsinp)
      for i in range(diff):
        exbsinp.append('')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return exbsinp[n]
OV.registerFunction(get_exbsinp,True,'NoSpherA2')

def get_fraginp():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    fraginp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_fraginp')
    fraginp = fraginp.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(fraginp) < maxtail:
      diff = maxtail - len(fraginp)
      for i in range(diff):
        fraginp.append('0')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return fraginp[n]
OV.registerFunction(get_fraginp,True,'NoSpherA2')

def change_resname(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    resnames = OV.GetParam('snum.NoSpherA2.ELMOdb.str_resname')
    resnames = resnames.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(resnames) < maxtail:
      diff = maxtail - len(resnames)
      for i in range(diff):
        resnames.append([])
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    resnames[n] = input
    str_resname = resnames
    str_resname = ";".join([str(i) for i in resnames])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_resname', str_resname)
    return resnames[n]
OV.registerFunction(change_resname,True,'NoSpherA2')

def change_nat(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    nat = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nat')
    nat = nat.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(nat) < maxtail:
      diff = maxtail - len(nat)
      for i in range(diff):
        nat.append(0)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    nat[n] = input
    str_nat = nat
    str_nat = ";".join([str(i) for i in nat])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_nat', str_nat)
    return nat[n]
OV.registerFunction(change_nat,True,'NoSpherA2')

def change_nfrag(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    nfrag = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nfrag')
    nfrag = nfrag.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(nfrag) < maxtail:
      diff = maxtail - len(nfrag)
      for i in range(diff):
        nfrag.append(1)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    nfrag[n] = input
    str_nfrag = nfrag
    str_nfrag = ";".join([str(i) for i in nfrag])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_nfrag', str_nfrag)
    return nfrag[n]
OV.registerFunction(change_nfrag,True,'NoSpherA2')

def change_ncltd(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    ncltd = OV.GetParam('snum.NoSpherA2.ELMOdb.str_ncltd')
    ncltd = ncltd.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(ncltd) < maxtail:
      diff = maxtail - len(ncltd)
      for i in range(diff):
        ncltd.append(False)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    ncltd[n] = input
    str_ncltd = ncltd
    str_ncltd = ";".join([str(i) for i in ncltd])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_ncltd', str_ncltd)
    return ncltd[n]
OV.registerFunction(change_ncltd,True,'NoSpherA2')

def change_specac(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    specac = OV.GetParam('snum.NoSpherA2.ELMOdb.str_specac')
    specac = specac.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(specac) < maxtail:
      diff = maxtail - len(specac)
      for i in range(diff):
        specac.append(False)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    specac[n] = input
    str_specac = specac
    str_specac = ";".join([str(i) for i in specac])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_specac', str_specac)
    return specac[n]
OV.registerFunction(change_specac,True,'NoSpherA2')

def change_exbsinp(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    exbsinp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_exbsinp')
    exbsinp = exbsinp.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(exbsinp) < maxtail:
      diff = maxtail - len(exbsinp)
      for i in range(diff):
        exbsinp.append(0)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    exbsinp[n] = input
    str_exbsinp = exbsinp
    str_exbsinp = ";".join([str(i) for i in exbsinp])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_exbsinp', str_exbsinp)
    return exbsinp[n]
OV.registerFunction(change_exbsinp,True,'NoSpherA2')

def change_fraginp(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    fraginp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_fraginp')
    fraginp = fraginp.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(fraginp) < maxtail:
      diff = maxtail - len(fraginp)
      for i in range(diff):
        fraginp.append(0)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    fraginp[n] = input
    str_fraginp = fraginp
    str_fraginp = ";".join([str(i) for i in fraginp])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_fraginp', str_fraginp)
    return fraginp[n]
OV.registerFunction(change_fraginp,True,'NoSpherA2')

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

def get_nmo():
  if os.path.isfile(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn")) == False:
    return -1
  wfn = open(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn"))
  line = ""
  while "MOL ORBITAL" not in line:
    line = wfn.readline()
  values = line.split()
  return values[1]

def get_ncen():
  if os.path.isfile(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn")) == False:
    return -1
  wfn = open(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn"))
  line = ""
  while "MOL ORBITAL" not in line:
    line = wfn.readline()
  values = line.split()
  return values[6]

OV.registerFunction(get_nmo,True,'NoSpherA2')
OV.registerFunction(get_ncen,True,'NoSpherA2')

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
      out, err = child.communicate()
      rc = child.returncode
      if rc == 0:
        OV.SetParam('user.NoSpherA2.has_pyscf',True)
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
      out, err = child.communicate()
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

def write_symmetry_file(debug=False):
  import olx
  from cctbx import crystal
  cs = crystal.symmetry(space_group_symbol="hall: "+str(olx.xf.au.GetCellSymm("hall")))
  if(debug == True):
    print(cs.space_group().n_smx())
  symops = []
  with open("symmetry.file",'w') as symm_file:
    for rt in cs.space_group().smx(False):
      if(debug == True):
        print(rt)
      A=[[[] for i in range(3)] for i in range(3)]
      xyz = ["x","y","z"]
      input = str(rt).split(",")
      def get_multiplier(input,target):
        if input == None:
          raise NameError("nonesense symmetry input!")
        if target == None:
          raise NameError("nonesense target input!")
        index = input.find(target)
        if index == -1:
          return 0
        else:
          if input[index-1]=="-":
            return -1
          else:
            return 1
      for i in range(3):
        for j in range(3):
          A[j][i] = get_multiplier(input[i],xyz[j])
          symm_file.write(str(A[j][i]))
          symm_file.write(" ")
      symops.append(A)
      if len(symops) != cs.space_group().n_smx():
        symm_file.write("\n")
  if (debug == True):
    print(symops)
OV.registerFunction(write_symmetry_file,True,'NoSpherA2')

def calculate_cubes():
  if is_disordered == True:
    print("Disordered structures not implemented!")
    return

  wfn2fchk = OV.GetVar("Wfn2Fchk")
  args = []

  args.append(wfn2fchk)
  cpus = OV.GetParam('snum.NoSpherA2.ncpus')
  args.append("-cpus")
  args.append(cpus)
  args.append("-wfn")
  if os.path.exists(OV.ModelSrc() + ".wfx"):
    args.append(OV.ModelSrc() + ".wfx")
  else:
    args.append(OV.ModelSrc() + ".wfn")
  Lap = OV.GetParam('snum.NoSpherA2.Property_Lap')
  Eli = OV.GetParam('snum.NoSpherA2.Property_Eli')
  Elf = OV.GetParam('snum.NoSpherA2.Property_Elf')
  RDG = OV.GetParam('snum.NoSpherA2.Property_RDG')
  ESP = OV.GetParam('snum.NoSpherA2.Property_ESP')
  MO  = OV.GetParam('snum.NoSpherA2.Property_MO')
  ATOM = OV.GetParam('snum.NoSpherA2.Property_ATOM')
  DEF = OV.GetParam('snum.NoSpherA2.Property_DEF')
  all_MOs = OV.GetParam('snum.NoSpherA2.Property_all_MOs')
  if Lap == True:
    args.append("-lap")
  if Eli == True:
    args.append("-eli")
  if Elf == True:
    args.append("-elf")
  if RDG == True:
    args.append("-rdg")
  if ESP == True:
    args.append("-esp")
  if OV.GetParam('snum.NoSpherA2.wfn2fchk_debug') == True:
    args.append("-v")

  if MO == True:
    args.append("-MO")
    if all_MOs == True:
      args.append("all")
    else:
      args.append(str(int(OV.GetParam('snum.NoSpherA2.Property_MO_number'))-1))

  if ATOM == True:
    args.append("-HDEF")

  if DEF == True:
    args.append("-def")

  radius = OV.GetParam('snum.NoSpherA2.map_radius')
  res = OV.GetParam('snum.NoSpherA2.map_resolution')
  args.append("-resolution")
  args.append(res)
  args.append("-radius")
  args.append(radius)
  args.append("-cif")
  args.append(OV.ModelSrc() + ".cif")

  os.environ['cube_cmd'] = '+&-'.join(args)
  os.environ['cube_file'] = OV.ModelSrc()
  os.environ['cube_dir'] = OV.FilePath()

  import subprocess
  pyl = OV.getPYLPath()
  if not pyl:
    print("A problem with pyl is encountered, aborting.")
    return
  p = subprocess.Popen([pyl, os.path.join(p_path, "cube-launch.py")])

OV.registerFunction(calculate_cubes,True,'NoSpherA2')

def get_map_types():
  name = OV.ModelSrc()
  folder = OV.FilePath()
  list = ";Residual<-diff;Deformation<-fcfmc;2Fo-Fc<-tomc;Fobs<-fobs;Fcalc<-fcalc;"
  if os.path.isfile(os.path.join(folder,name+"_eli.cube")):
    list += "ELI-D;"
  if os.path.isfile(os.path.join(folder,name+"_lap.cube")):
    list += "Laplacian;"
  if os.path.isfile(os.path.join(folder,name+"_elf.cube")):
    list += "ELF;"
  if os.path.isfile(os.path.join(folder,name+"_esp.cube")):
    list += "ESP;"
  if os.path.isfile(os.path.join(folder,name+"_rdg.cube")):
    list += "RDG;"
  if os.path.isfile(os.path.join(folder,name+"_def.cube")):
    list += "Stat. Def.;"
  if os.path.isfile(os.path.join(folder,name+"_rdg.cube")) and os.path.isfile(os.path.join(folder,name+"_signed_rho.cube")):
    list += "NCI;"
  if os.path.isfile(os.path.join(folder,name+"_rho.cube")) and os.path.isfile(os.path.join(folder,name+"_esp.cube")):
    list += "Rho + ESP;"
  nmo = get_nmo()
  if nmo != -1:
    exists = False
    for i in range(int(nmo)+1):
      if os.path.isfile(os.path.join(folder,name+"_MO_"+str(i)+".cube")):
        exists = True
    if exists == True:
      list += "MO;"
  ncen = get_ncen()
  if ncen != -1:
    exists = False
    for i in range(int(ncen)+1):
      if os.path.isfile(os.path.join(folder,name+"_HDEF_"+str(i)+".cube")):
        exists = True
    if exists == True:
      list += "HDEF;"
  if list == "":
    return "None;"
  return list
OV.registerFunction(get_map_types,True,'NoSpherA2')

def change_map():
  Type = OV.GetParam('snum.NoSpherA2.map_type')
  if Type == "None" or Type == "":
    return
  name = OV.ModelSrc()
  if Type == "ELI-D":
    plot_cube(name+"_eli.cube",None)
  elif Type == "Laplacian":
    plot_cube(name+"_lap.cube",None)
  elif Type == "ELF":
    plot_cube(name+"_elf.cube",None)
  elif Type == "ESP":
    plot_cube(name+"_esp.cube",None)
  elif Type == "Stat. Def.":
    plot_cube(name+"_def.cube",None)
  elif Type == "NCI":
    OV.SetParam('snum.NoSpherA2.map_scale_name',"RGB")
    plot_cube(name+"_rdg.cube",name+"_signed_rho.cube")
  elif Type == "RDG":
    plot_cube(name+"_rdg.cube",None)
  elif Type == "Rho + ESP":
    OV.SetParam('snum.NoSpherA2.map_scale_name',"BWR")
    plot_cube(name+"_rho.cube",name+"_esp.cube")
  elif Type == "fcfmc" or Type == "diff" or Type == "tomc" or Type == "fobs" or Type == "fcalc":
    OV.SetVar('map_slider_scale',-50)
    OV.SetParam('snum.map.type',Type)
    show_fft_map(float(OV.GetParam('snum.NoSpherA2.map_resolution')),map_type=Type)
    minimal = float(olx.xgrid.GetMin())
    maximal = float(olx.xgrid.GetMax())
    if -minimal > maximal:
      maximal = -minimal
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',maximal*50)
    olex.m("html.Update()")
  elif Type == "MO":
    number = int(OV.GetParam('snum.NoSpherA2.Property_MO_number')) -1
    plot_cube(name+"_MO_"+str(number)+".cube",None)
  elif Type == "HDEF":
    number = int(OV.GetParam('snum.NoSpherA2.Property_ATOM_number')) -1
    plot_cube(name+"_HDEF_"+str(number)+".cube",None)
  else:
    print("Sorry, no map type available or selected map type not correct!")
    return
OV.registerFunction(change_map,True,'NoSpherA2')

def change_pointsize():
  PS = OV.GetParam('snum.NoSpherA2.gl_pointsize')
  olex.m('gl.PointSize ' + PS)
OV.registerFunction(change_pointsize,True,'NoSpherA2')


def plot_cube(name,color_cube):
  import olex_xgrid
  if not os.path.isfile(name):
    print("Cube file does not exist!")
    return
  olex.m("html.Update()")
  with open(name) as cub:
    cube = cub.readlines()

  run = 0
  na = 0
  x_size = 0
  y_size = 0
  z_size = 0
  x_run = 0
  y_run = 0
  z_run = 0
  data = None

  min = 100000
  max = 0

  for line in cube:
    run += 1
    if (run==3):
      values = line.split()
      na = int(values[0])
    if (run==4):
      values = line.split()
      x_size = int(values[0])
    if (run==5):
      values = line.split()
      y_size = int(values[0])
    if (run==6):
      values = line.split()
      z_size = int(values[0])
      data = [[[float(0.0) for k in range(z_size)] for j in range(y_size)] for i in range(x_size)]
    if (run > na + 6):
      values = line.split()
      for i in range(len(values)):
        data[x_run][y_run][z_run] = float(values[i])
        if data[x_run][y_run][z_run] > max:
          max = data[x_run][y_run][z_run]
        if data[x_run][y_run][z_run] < min:
          min = data[x_run][y_run][z_run]
        z_run += 1
        if z_run == z_size:
          y_run += 1
          z_run = 0
          if y_run == y_size:
            x_run += 1
            y_run = 0
        if x_run > x_size:
          print("ERROR! Mismatched indices while reading!")
          return

  cube = None

  make_colorfull = (color_cube != None)
  if make_colorfull == True:
    with open(color_cube) as cub:
      cube2 = cub.readlines()

    run = 0
    na2 = 0
    x_size2 = 0
    y_size2 = 0
    z_size2 = 0
    x_run = 0
    y_run = 0
    z_run = 0
    data2 = None

    for line in cube2:
      run += 1
      if (run==3):
        values = line.split()
        na2 = int(values[0])
      if (run==4):
        values = line.split()
        x_size2 = int(values[0])
      if (run==5):
        values = line.split()
        y_size2 = int(values[0])
      if (run==6):
        values = line.split()
        z_size2 = int(values[0])
        data2 = [[[float(0.0) for k in range(z_size2)] for j in range(y_size2)] for i in range(x_size2)]
      if (run > na + 6):
        values = line.split()
        for i in range(len(values)):
          data2[x_run][y_run][z_run] = float(values[i])
          z_run += 1
          if z_run == z_size2:
            y_run += 1
            z_run = 0
            if y_run == y_size2:
              x_run += 1
              y_run = 0
          if x_run > x_size2:
            print("ERROR! Mismatched indices while reading!")
            return

    cube2 = None
    values = None
    z_run = None
    y_run = None
    x_run = None
    na = None
    na2 = None
    line = None
    run = None
    olex_xgrid.Init(x_size,y_size,z_size,True)

    def interpolate(x,y,z):
      #trilinear interpolation between the points... sorry for the mess
      x_1 = x/x_size
      y_1 = y/y_size
      z_1 = z/z_size
      x_2 = x_1 * x_size2
      y_2 = y_1 * y_size2
      z_2 = z_1 * z_size2
      ix2 = int(x_2)
      iy2 = int(y_2)
      iz2 = int(z_2)
      ix21 = ix2 + 1
      iy21 = iy2 + 1
      iz21 = iz2 + 1
      a_0 = data2[ix2][iy2][iz2]*ix21*iy21*iz21 - data2[ix2][iy2][iz21]*ix21*iy21*iz2 - data2[ix2][iy21][iz2]*ix21*iy2*iz21 + data2[ix2][iy21][iz21]*ix21*iy2*iz2 - data2[ix21][iy2][iz2]*ix2*iy21*iz21 + data2[ix21][iy2][iz21]*ix2*iy21*iz2 + data2[ix21][iy21][iz2]*ix2*iy2*iz21 - data2[ix21][iy21][iz21]*ix2*iy2*iz2
      a_1 = - data2[ix2][iy2][iz2]*iy21*iz21 + data2[ix2][iy2][iz21]*iy21*iz2 + data2[ix2][iy21][iz2]*iy2*iz21 - data2[ix2][iy21][iz21]*iy2*iz2 + data2[ix21][iy2][iz2]*iy21*iz21 - data2[ix21][iy2][iz21]*iy21*iz2 - data2[ix21][iy21][iz2]*iy2*iz21 + data2[ix21][iy21][iz21]*iy2*iz2
      a_2 = - data2[ix2][iy2][iz2]*ix21*iz21 + data2[ix2][iy2][iz21]*ix21*iz2 + data2[ix2][iy21][iz2]*ix2*iz21 - data2[ix2][iy21][iz21]*ix2*iz2 + data2[ix21][iy2][iz2]*ix21*iz21 - data2[ix21][iy2][iz21]*ix21*iz2 - data2[ix21][iy21][iz2]*ix2*iz21 + data2[ix21][iy21][iz21]*ix2*iz2
      a_3 = - data2[ix2][iy2][iz2]*ix21*iy21 + data2[ix2][iy2][iz21]*ix21*iy2 + data2[ix2][iy21][iz2]*ix2*iy21 - data2[ix2][iy21][iz21]*ix2*iy2 + data2[ix21][iy2][iz2]*ix21*iy21 - data2[ix21][iy2][iz21]*ix21*iy2 - data2[ix21][iy21][iz2]*ix2*iy21 + data2[ix21][iy21][iz21]*ix2*iy2
      a_4 = data2[ix2][iy2][iz2]*iz21 - data2[ix2][iy2][iz21]*iz2 - data2[ix2][iy21][iz2]*iz21 + data2[ix2][iy2][iz21]*iz2 - data2[ix21][iy2][iz2]*iz21 + data2[ix21][iy2][iz21]*iz2 + data2[ix21][iy21][iz2]*iz21 - data2[ix21][iy21][iz21]*iz2
      a_5 = data2[ix2][iy2][iz2]*iy21 - data2[ix2][iy2][iz21]*iy2 - data2[ix2][iy21][iz2]*iy21 + data2[ix2][iy2][iz21]*iy2 - data2[ix21][iy2][iz2]*iy21 + data2[ix21][iy2][iz21]*iy2 + data2[ix21][iy21][iz2]*iy21 - data2[ix21][iy21][iz21]*iy2
      a_6 = data2[ix2][iy2][iz2]*ix21 - data2[ix2][iy2][iz21]*ix2 - data2[ix2][iy21][iz2]*ix21 + data2[ix2][iy2][iz21]*ix2 - data2[ix21][iy2][iz2]*ix21 + data2[ix21][iy2][iz21]*ix2 + data2[ix21][iy21][iz2]*ix21 - data2[ix21][iy21][iz21]*ix2
      a_7 = -(data2[ix2][iy2][iz2] - data2[ix2][iy2][iz21] - data2[ix2][iy21][iz2] + data2[ix2][iy2][iz21] - data2[ix21][iy2][iz2] + data2[ix21][iy2][iz21] + data2[ix21][iy21][iz2] - data2[ix21][iy21][iz21])

      return a_0 + a_1 * ix2 + a_2 * iy2 + a_3 * z_2 + a_4 * x_2 * y_2 + a_5 * x_2 * z_2 + a_6 * y_2 * z_2 + a_7 * x_2 * y_2 * z_2


    value = [[[float(0.0) for k in range(z_size)] for j in range(y_size)] for i in range(x_size)]
    i=None
    if x_size == x_size2 and y_size == y_size2 and z_size == z_size2:
      for x in range(x_size):
        for y in range(y_size):
          for z in range(z_size):
            value[x][y][z] = data2[x][y][z]
    else:
      print("Interpolating...")
      #from dask import delayed
      #from multiprocessing import Pool
      #nproc = int(OV.GetParam("snum.NoSpherA2.ncpus"))
      #pool = Pool(processes=nproc)
      for x in range(x_size):
        for y in range(y_size):
          for z in range(z_size):
            res = interpolate(x,y,z)
            value[x][y][z] = res
    data2 = None
    for x in range(x_size):
      for y in range(y_size):
        for z in range(z_size):
          colour = int(get_color(value[x][y][z]))
          olex_xgrid.SetValue(x,y,z,data[x][y][z],colour)
  else:
    olex_xgrid.Init(x_size,y_size,z_size)
    for x in range(x_size):
      for y in range(y_size):
        for z in range(z_size):
          olex_xgrid.SetValue(x,y,z,data[x][y][z])
  data = None
  Type = OV.GetParam('snum.NoSpherA2.map_type')
  if Type == "Laplacian":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',40)
    OV.SetVar('map_slider_scale',40)
  elif Type == "ELI-D":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',60)
    OV.SetVar('map_slider_scale',20)
  elif Type == "ELF":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',40)
    OV.SetVar('map_slider_scale',40)
  elif Type == "ESP":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',50)
  elif Type == "NCI":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  elif Type == "RDG":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  elif Type == "Rho + ESP":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  elif Type == "MO":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  elif Type == "HDEF":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  elif Type == "Stat. Def.":
    OV.SetVar('map_min',0)
    OV.SetVar('map_max',50)
    OV.SetVar('map_slider_scale',100)
  olex_xgrid.SetMinMax(min, max)
  olex_xgrid.SetVisible(True)
  olex_xgrid.InitSurface(True,1)
  iso = float((abs(min)+abs(max))*2/3)
  olex_xgrid.SetSurfaceScale(iso)
  OV.SetParam('snum.xgrid.scale',"{:.3f}".format(iso))

OV.registerFunction(plot_cube,True,'NoSpherA2')

def plot_cube_single(name):
  import olex_xgrid
  if not os.path.isfile(name):
    print("Cube file does not exist!")
    return
  olex.m("html.Update()")
  with open(name) as cub:
    cube = cub.readlines()

  run = 0
  na = 0
  x_size = 0
  y_size = 0
  z_size = 0
  x_run = 0
  y_run = 0
  z_run = 0
  data = None

  min = 100000
  max = 0

  for line in cube:
    run += 1
    if (run==3):
      values = line.split()
      na = int(values[0])
    if (run==4):
      values = line.split()
      x_size = int(values[0])
    if (run==5):
      values = line.split()
      y_size = int(values[0])
    if (run==6):
      values = line.split()
      z_size = int(values[0])
      data = [[[float(0.0) for k in range(z_size)] for j in range(y_size)] for i in range(x_size)]
    if (run > na + 6):
      values = line.split()
      for i in range(len(values)):
        data[x_run][y_run][z_run] = float(values[i])
        if data[x_run][y_run][z_run] > max:
          max = data[x_run][y_run][z_run]
        if data[x_run][y_run][z_run] < min:
          min = data[x_run][y_run][z_run]
        z_run += 1
        if z_run == z_size:
          y_run += 1
          z_run = 0
          if y_run == y_size:
            x_run += 1
            y_run = 0
        if x_run > x_size:
          print("ERROR! Mismatched indices while reading!")
          return

  cube = None

  olex_xgrid.Init(x_size,y_size,z_size)
  for x in range(x_size):
    for y in range(y_size):
      for z in range(z_size):
        olex_xgrid.SetValue(x,y,z,data[x][y][z])
  data = None
  OV.SetVar('map_min',0)
  OV.SetVar('map_max',40)
  OV.SetVar('map_slider_scale',100)
  olex_xgrid.SetMinMax(min, max)
  olex_xgrid.SetVisible(True)
  olex_xgrid.InitSurface(True,1)
  iso = float((abs(min)+abs(max))*2/3)
  olex_xgrid.SetSurfaceScale(iso)
  OV.SetParam('snum.xgrid.scale',"{:.3f}".format(iso))

OV.registerFunction(plot_cube_single,True,'NoSpherA2')

def plot_map_cube(map_type,resolution):
  olex.m('CalcFourier -fcf -%s -r=%s'%(map_type,resolution))
  import olex_xgrid
  import math

  temp = olex_xgrid.GetSize()
  size = [int(temp[0]),int(temp[1]),int(temp[2])]
  name = OV.ModelSrc()

  n_atoms = int(olx.xf.au.GetAtomCount())
  positions = [[float(0.0) for k in range(3)] for l in range(n_atoms)]
  cm = [[float(0.0) for k in range(3)] for l in range(3)]
  cm_inv = [[float(0.0) for k in range(3)] for l in range(3)]
  temp = olx.xf.au.GetCell().split(',')
  cell = [float(temp[0]),float(temp[1]),float(temp[2]),float(temp[3]),float(temp[4]),float(temp[5])]
  a2b = 0.52917749
  fac = 0.0174532925199432944444444444444

  types = ["Q","H","He","Li","Be","B","C","N","O","F","Ne","Na","Mg","Al","Si","P","S","Cl","Ar","K","Ca","Sc","Ti","V","Cr","Mn","Fe","Co","Ni","Cu","Zn","Ga","Ge","As","Se","Br","Kr","Rb","Sr","Y","Zr","Nb","Mo","Tc","Ru","Rh","Pd","Ag","Cd","In","Sn","Sb","Te","I","Xe","Cs","Ba","La","Ce","Pr","Nd","Pm","Sm","Eu","Gd","Tb","Dy","Ho","Er","Tm","Yb","Lu","Hf","Ta","W","Re","Os","Ir","Pt","Au","Hg","Tl","Pb","Bi","Po","At","Rn","Fr","Ra","Ac","Th","Pa","U","Np","Pu","Am","Cm","Bk","Cf","Es","Fm","Md","No","Lr"]

  ca = math.cos(fac * cell[3])
  cb = math.cos(fac * cell[4])
  cg = math.cos(fac * cell[5])
  sg = math.sin(fac * cell[5])
  cm[0][0] = cell[0] / a2b
  cm[0][1] = cell[1] * cg / a2b
  cm[1][1] = cell[1] * sg / a2b
  cm[0][2] = cell[2] * cb / a2b
  cm[1][2] = (cell[2] * (ca - cb * cg) / sg) / a2b
  cm[2][2] = float(olx.xf.au.GetCellVolume())/(cell[0] * cell[1] * sg * a2b)

  cm_inv[0][0] = 1/cm[0][0] / a2b
  cm_inv[1][1] = 1/cm[1][1] / a2b
  cm_inv[2][2] = 1/cm[2][2] / a2b
  cm_inv[0][1] = -cm[0][1]/(cm[0][0]*cm[1][1]) / a2b
  cm_inv[0][2] = ((cm[0][1]*cm[1][2])-(cm[0][2]*cm[1][1]))/(cm[0][0]*cm[1][1]*cm[2][2]) / a2b
  cm_inv[1][2] = -cm[1][2]/(cm[1][1]*cm[2][2]) / a2b
  cm_inv[1][0] = cm[0][1]/(cm[0][0]*cm[1][1]) /a2b
  cm_inv[2][0] = (-cm[0][1]*cm[1][2]+cm[0][2]*cm[1][1])/(cm[0][0]*cm[1][1]*cm[2][2]) /a2b
  cm_inv[2][1] = cm[1][2]/(cm[1][1]*cm[2][2]) /a2b

  cmnorm = [
    math.sqrt(cm_inv[0][0]*cm_inv[0][0] + cm_inv[0][1]*cm_inv[0][1] + cm_inv[0][2]*cm_inv[0][2]),
    math.sqrt(cm_inv[1][0]*cm_inv[1][0] + cm_inv[1][1]*cm_inv[1][1] + cm_inv[1][2]*cm_inv[2][2]),
    math.sqrt(cm_inv[2][0]*cm_inv[2][0] + cm_inv[2][1]*cm_inv[2][1] + cm_inv[2][2]*cm_inv[2][2])]

  for a in range(n_atoms):
    pos = olx.xf.au.Orthogonalise(olx.xf.au.GetAtomCrd(a)).split(',')

    positions[a] = [
      (float(pos[0])*cm_inv[0][0]+float(pos[1])*cm_inv[0][1]+float(pos[2])*cm_inv[0][2])/cmnorm[0],
      (float(pos[0])*cm_inv[1][0]+float(pos[1])*cm_inv[1][1]+float(pos[2])*cm_inv[1][2])/cmnorm[1],
      (float(pos[0])*cm_inv[2][0]+float(pos[1])*cm_inv[2][1]+float(pos[2])*cm_inv[2][2])/cmnorm[2]]

  print ("start writing a %4d x %4d x %4d cube"%(size[0],size[1],size[2]))

  with open("%s_%s.cube"%(name,map_type),'w') as cube:
    cube.write("Fcalc fourier synthesis map created by Olex2\n")
    cube.write("Model name: %s\n"%name)
    #Origin of cube
    cube.write("%6d %12.8f %12.8f %12.8f\n"%(n_atoms,0.0,0.0,0.0))
    # need to write vectors!
    cube.write("%6d %12.8f %12.8f %12.8f\n"%(size[0],cm[0][0]/(size[0]-1),cm[0][1]/(size[0]-1),cm[0][2]/(size[0]-1)))
    cube.write("%6d %12.8f %12.8f %12.8f\n"%(size[1],cm[1][0]/(size[1]-1),cm[1][1]/(size[1]-1),cm[1][2]/(size[1]-1)))
    cube.write("%6d %12.8f %12.8f %12.8f\n"%(size[2],cm[2][0]/(size[2]-1),cm[2][1]/(size[2]-1),cm[2][2]/(size[2]-1)))
    for i in range(n_atoms):
      atom_type = olx.xf.au.GetAtomType(i)
      charge = 200
      for j in range(104):
        if types[j] == atom_type:
          charge = j
          break
      if charge == 200:
        print("ATOM NOT FOUND!")
      cube.write("%6d %6d.00000 %12.8f %12.8f %12.8f\n"%(charge,charge,positions[i][0]/a2b,positions[i][1]/a2b,positions[i][2]/a2b))
    for x in range(size[0]):
      for y in range(size[1]):
        string = ""
        for z in range(size[2]):
          value = olex_xgrid.GetValue(x,y,z)
          string += ("%15.7e"%value)
          if (z+1) % 6 == 0 and (z+1) != size[2]:
            string += '\n'
        if (y != (size[1] - 1)):
          string += '\n'
        cube.write(string)
      if(x != (size[0] -1)):
        cube.write('\n')

    cube.close()

  print("Saved Fourier map successfully")

OV.registerFunction(plot_map_cube,True,'NoSpherA2')

def get_color(value):
  a = 127
  b = 0
  g = 0
  r = 0
  scale_min = OV.GetParam('snum.NoSpherA2.map_scale_min')
  scale_max = OV.GetParam('snum.NoSpherA2.map_scale_max')
  scale = OV.GetParam('snum.NoSpherA2.map_scale_name') #BWR = Blue White Red; RGB = Red Green Blue
  x = 0
  if value <= float(scale_min):
    x = 0
  elif value >= float(scale_max):
    x = 1
  else:
    x = (value - float(scale_min)) / (float(scale_max) - float (scale_min))
  if scale == "RWB":
    x = 1 - x
    scale = "BWR"
  if scale == "RGB":
    x = 1 - x
    scale = "BGR"
  if scale == "BWR":
    if x <= 0.5:
      h = 2 * x
      b = 255
      g = int(255 * h)
      r = int(255 * h)
    else:
      h = -2*x + 2
      b = int(255 * h)
      g = int(255 * h)
      r = 255
  elif scale == "BGR":
    if x <= 0.5:
      h = 2*x
      b = int(255*1-h)
      g = int(255* h)
      r = 0
    elif x > 0.5:
      b = 0
      g = int(255 * (-2 * x + 2))
      r = int(255 * ( 2 * x - 1))
  rgba = (127 << 24) | (b << 16) | (g << 8) | r
  if value == "0.00101":
    print(rgba)
  return rgba
OV.registerFunction(get_color,True,'NoSpherA2')

def is_colored():
  Type = OV.GetParam('snum.NoSpherA2.map_type')
  if Type == "NCI":
    return True
  elif Type == "Rho + ESP":
    return True
  else:
    return False
OV.registerFunction(is_colored,True,'NoSpherA2')

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

def plot_fft_map(fft_map):
  import olex_xgrid
  data = fft_map.real_map_unpadded()
  gridding = data.accessor()
  from cctbx.array_family import flex
  type = isinstance(data, flex.int)
  olex_xgrid.Import(
    gridding.all(), gridding.focus(), data.copy_to_byte_str(), type)
  statistics = fft_map.statistics()
  min_v = statistics.min()
  max_v = statistics.max()
  sigma = statistics.sigma()
  data = None
  olex_xgrid.SetMinMax(min_v, max_v)
  olex_xgrid.SetVisible(True)
  olex_xgrid.InitSurface(True,1)
  iso = float(-(abs(min_v)+abs(max_v))*1/3)
  olex_xgrid.SetSurfaceScale(iso)
  #OV.SetParam('snum.xgrid.scale',"{:.3f}".format(iso))
  print("Map max val %.3f min val %.3f RMS: %.3f"%(max_v,min_v,sigma))
  print("Map size: %d x %d x %d"%(fft_map.n_real()[0],fft_map.n_real()[1],fft_map.n_real()[2]))

OV.registerFunction(plot_fft_map,True,'NoSpherA2')

def plot_fft_map_cube(fft_map,map_name):
  import math

  temp = fft_map.n_real()
  size = [int(temp[0]),int(temp[1]),int(temp[2])]
  name = OV.ModelSrc()

  n_atoms = int(olx.xf.au.GetAtomCount())
  positions = [[float(0.0) for k in range(3)] for l in range(n_atoms)]
  cm = [[float(0.0) for k in range(3)] for l in range(3)]
  cm_inv = [[float(0.0) for k in range(3)] for l in range(3)]
  temp = olx.xf.au.GetCell().split(',')
  cell = [float(temp[0]),float(temp[1]),float(temp[2]),float(temp[3]),float(temp[4]),float(temp[5])]
  a2b = 0.52917749
  fac = 0.0174532925199432944444444444444

  types = ["Q","H","He","Li","Be","B","C","N","O","F","Ne","Na","Mg","Al","Si","P","S","Cl","Ar","K","Ca","Sc","Ti","V","Cr","Mn","Fe","Co","Ni","Cu","Zn","Ga","Ge","As","Se","Br","Kr","Rb","Sr","Y","Zr","Nb","Mo","Tc","Ru","Rh","Pd","Ag","Cd","In","Sn","Sb","Te","I","Xe","Cs","Ba","La","Ce","Pr","Nd","Pm","Sm","Eu","Gd","Tb","Dy","Ho","Er","Tm","Yb","Lu","Hf","Ta","W","Re","Os","Ir","Pt","Au","Hg","Tl","Pb","Bi","Po","At","Rn","Fr","Ra","Ac","Th","Pa","U","Np","Pu","Am","Cm","Bk","Cf","Es","Fm","Md","No","Lr"]

  ca = math.cos(fac * cell[3])
  cb = math.cos(fac * cell[4])
  cg = math.cos(fac * cell[5])
  sg = math.sin(fac * cell[5])
  cm[0][0] = cell[0] / a2b
  cm[0][1] = cell[1] * cg / a2b
  cm[1][1] = cell[1] * sg / a2b
  cm[0][2] = cell[2] * cb / a2b
  cm[1][2] = (cell[2] * (ca - cb * cg) / sg) / a2b
  cm[2][2] = float(olx.xf.au.GetCellVolume())/(cell[0] * cell[1] * sg * a2b)

  cm_inv[0][0] = 1/cm[0][0] / a2b
  cm_inv[1][1] = 1/cm[1][1] / a2b
  cm_inv[2][2] = 1/cm[2][2] / a2b
  cm_inv[0][1] = -cm[0][1]/(cm[0][0]*cm[1][1]) / a2b
  cm_inv[0][2] = ((cm[0][1]*cm[1][2])-(cm[0][2]*cm[1][1]))/(cm[0][0]*cm[1][1]*cm[2][2]) / a2b
  cm_inv[1][2] = -cm[1][2]/(cm[1][1]*cm[2][2]) / a2b
  cm_inv[1][0] = cm[0][1]/(cm[0][0]*cm[1][1]) /a2b
  cm_inv[2][0] = (-cm[0][1]*cm[1][2]+cm[0][2]*cm[1][1])/(cm[0][0]*cm[1][1]*cm[2][2]) /a2b
  cm_inv[2][1] = cm[1][2]/(cm[1][1]*cm[2][2]) /a2b

  cmnorm = [
    math.sqrt(cm_inv[0][0]*cm_inv[0][0] + cm_inv[0][1]*cm_inv[0][1] + cm_inv[0][2]*cm_inv[0][2]),
    math.sqrt(cm_inv[1][0]*cm_inv[1][0] + cm_inv[1][1]*cm_inv[1][1] + cm_inv[1][2]*cm_inv[2][2]),
    math.sqrt(cm_inv[2][0]*cm_inv[2][0] + cm_inv[2][1]*cm_inv[2][1] + cm_inv[2][2]*cm_inv[2][2])]

  for a in range(n_atoms):
    pos = olx.xf.au.Orthogonalise(olx.xf.au.GetAtomCrd(a)).split(',')

    positions[a] = [
      (float(pos[0])*cm_inv[0][0]+float(pos[1])*cm_inv[0][1]+float(pos[2])*cm_inv[0][2])/cmnorm[0],
      (float(pos[0])*cm_inv[1][0]+float(pos[1])*cm_inv[1][1]+float(pos[2])*cm_inv[1][2])/cmnorm[1],
      (float(pos[0])*cm_inv[2][0]+float(pos[1])*cm_inv[2][1]+float(pos[2])*cm_inv[2][2])/cmnorm[2]]

  print ("start writing a %4d x %4d x %4d cube"%(size[0],size[1],size[2]))
  values = fft_map.real_map_unpadded()

  with open("%s_%s.cube"%(name,map_name),'w') as cube:
    cube.write("Fourier synthesis map created by Olex2\n")
    cube.write("Model name: %s\n"%name)
    #Origin of cube
    cube.write("%6d %12.8f %12.8f %12.8f\n"%(n_atoms,0.0,0.0,0.0))
    # need to write vectors!
    cube.write("%6d %12.8f %12.8f %12.8f\n"%(size[0],cm[0][0]/(size[0]-1),cm[0][1]/(size[0]-1),cm[0][2]/(size[0]-1)))
    cube.write("%6d %12.8f %12.8f %12.8f\n"%(size[1],cm[1][0]/(size[1]-1),cm[1][1]/(size[1]-1),cm[1][2]/(size[1]-1)))
    cube.write("%6d %12.8f %12.8f %12.8f\n"%(size[2],cm[2][0]/(size[2]-1),cm[2][1]/(size[2]-1),cm[2][2]/(size[2]-1)))
    for i in range(n_atoms):
      atom_type = olx.xf.au.GetAtomType(i)
      charge = 200
      for j in range(104):
        if types[j] == atom_type:
          charge = j
          break
      if charge == 200:
        print("ATOM NOT FOUND!")
      cube.write("%6d %6d.00000 %12.8f %12.8f %12.8f\n"%(charge,charge,positions[i][0]/a2b,positions[i][1]/a2b,positions[i][2]/a2b))
    for x in range(size[0]):
      for y in range(size[1]):
        string = ""
        for z in range(size[2]):
          #value = fft_map.real_map_unpadded()[(x*size[1]+y)*size[2]+z]
          string += ("%15.7e"%values[(x*size[1]+y)*size[2]+z])
          if (z+1) % 6 == 0 and (z+1) != size[2]:
            string += '\n'
        if (y != (size[1] - 1)):
          string += '\n'
        cube.write(string)
      if(x != (size[0] -1)):
        cube.write('\n')

    cube.close()

  print("Saved Fourier map successfully")

def residual_map(resolution=0.1,return_map=False,print_peaks=False):
  from cctbx_olex_adapter import OlexCctbxAdapter
  cctbx_adapter = OlexCctbxAdapter()
  xray_structure = cctbx_adapter.xray_structure()
  use_tsc = OV.GetParam('snum.NoSpherA2.use_aspherical')
  if use_tsc == True:
    table_name = str(OV.GetParam("snum.NoSpherA2.file"))
    time = os.path.getmtime(table_name)
    if NoSpherA2_instance.reflection_date is None or time < NoSpherA2_instance.reflection_date:
      print("Calculating Structure Factors from files...")
      from smtbx.structure_factors import direct
      one_h = direct.f_calc_modulus_squared(
        xray_structure, table_file_name=table_name)
      f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
      NoSpherA2_instance.set_f_calc_obs_sq_one_h_linearisation(f_calc, f_sq_obs, one_h)
    else:
      f_sq_obs, f_calc = NoSpherA2_instance.f_obs_sq, NoSpherA2_instance.f_calc
  else:
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()
  if OV.GetParam("snum.refinement.use_solvent_mask"):
    f_mask = cctbx_adapter.load_mask()
    if not f_mask:
      from cctbx_olex_adapter import OlexCctbxMasks
      OlexCctbxMasks()
      if olx.current_mask.flood_fill.n_voids() > 0:
        f_mask = olx.current_mask.f_mask()      
    if f_mask:
      if not f_sq_obs.space_group().is_centric() and f_sq_obs.anomalous_flag():
        f_mask = f_mask.generate_bijvoet_mates()
      f_mask = f_mask.common_set(f_sq_obs)
      f_obs = f_sq_obs.f_sq_as_f()
      f_calc = f_calc.array(data=(f_calc.data() + f_mask.data()))
      k = math.sqrt(OV.GetOSF())
      f_diff = f_obs.f_obs_minus_f_calc(1.0/k, f_calc)
  else:
    f_obs = f_sq_obs.f_sq_as_f()
    k = math.sqrt(OV.GetOSF())
    f_diff = f_obs.f_obs_minus_f_calc(1.0/k, f_calc)
  from cctbx import sgtbx
  f_diff = f_diff.expand_to_p1()
  print("Using %d reflections for Fourier synthesis"%f_diff.size())
  diff_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                            resolution_factor=1,grid_step=float(resolution)).apply_volume_scaling()
  if print_peaks == True or print_peaks == "True":
    from cctbx import maptbx
    max_peaks=10
    peaks = diff_map.peak_search(
      parameters=maptbx.peak_search_parameters(
        peak_search_level=2,
        interpolate=False,
        min_distance_sym_equiv=1.0,
        max_clusters=max_peaks+len(xray_structure.scatterers())),
      verify_symmetry=True
      ).all()
    i = 0
    olx.Kill('$Q', au=True) #HP-JUL18 -- Why kill the peaks? -- cause otherwise they accumulate! #HP4/9/18
    for xyz, height in zip(peaks.sites(), peaks.heights()):
      if i < max_peaks:
        a = olx.xf.uc.Closest(*xyz).split(',')
        pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A^3, %.3f A away from %s" %(
            i+1, xyz[0], xyz[1], xyz[2], height, float(a[1]), a[0])
        print(pi)
      id = olx.xf.au.NewAtom("%.2f" %(height), *xyz)
      if id != '-1':
        olx.xf.au.SetAtomU(id, "0.06")
        i = i+1
      if i == 100 or i >= max_peaks:
        break
    if OV.HasGUI():
      basis = olx.gl.Basis()
      frozen = olx.Freeze(True)
    olx.xf.EndUpdate(True) #clear LST
    olx.Compaq(q=True)
    if OV.HasGUI():
      olx.gl.Basis(basis)
      olx.Freeze(frozen)
      OV.Refresh()
  if return_map==True:
    return diff_map
  plot_fft_map_cube(diff_map,"diff")

OV.registerFunction(residual_map, False, "NoSpherA2")

def tomc_map(resolution=0.1,return_map=False, use_f000=False):
  from cctbx_olex_adapter import OlexCctbxAdapter
  cctbx_adapter = OlexCctbxAdapter()
  use_tsc = OV.GetParam('snum.NoSpherA2.use_aspherical')
  if use_tsc == True:
    table_name = str(OV.GetParam("snum.NoSpherA2.file"))
    time = os.path.getmtime(table_name)
    if NoSpherA2_instance.reflection_date is None or time < NoSpherA2_instance.reflection_date:
      from smtbx.structure_factors import direct
      xray_structure = cctbx_adapter.xray_structure()
      one_h = direct.f_calc_modulus_squared(
                       xray_structure, table_file_name=table_name)
      f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
      NoSpherA2_instance.set_f_calc_obs_sq_one_h_linearisation(f_calc, f_sq_obs, one_h)
    else:
      f_sq_obs, f_calc = NoSpherA2_instance.f_obs_sq, NoSpherA2_instance.f_calc
  else:
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()
  if OV.GetParam("snum.refinement.use_solvent_mask"):
    f_mask = cctbx_adapter.load_mask()
    if not f_mask:
      from cctbx_olex_adapter import OlexCctbxMasks
      OlexCctbxMasks()
      if olx.current_mask.flood_fill.n_voids() > 0:
        f_mask = olx.current_mask.f_mask()      
    if f_mask:
      if not f_sq_obs.space_group().is_centric() and f_sq_obs.anomalous_flag():
        f_mask = f_mask.generate_bijvoet_mates()
      f_mask = f_mask.common_set(f_sq_obs)
      f_obs = f_sq_obs.f_sq_as_f()
      f_calc = f_calc.array(data=(f_calc.data() + f_mask.data()))
      k = math.sqrt(OV.GetOSF())
      f_diff = f_obs.f_obs_minus_f_calc(2.0/k, f_calc)
  else:
    f_obs = f_sq_obs.f_sq_as_f()
    k = math.sqrt(OV.GetOSF())
    f_diff = f_obs.f_obs_minus_f_calc(2.0/k, f_calc)
  from cctbx import sgtbx
  f_diff = f_diff.expand_to_p1()
  if use_f000 == True or use_f000 == "True":
    f000 = float(olx.xf.GetF000())
    tomc_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1,grid_step=float(resolution),
                              f_000=f000).apply_volume_scaling()
  else:
    tomc_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1,grid_step=float(resolution)).apply_volume_scaling()
  if return_map==True:
    return tomc_map
  plot_fft_map_cube(tomc_map,"tomc")

OV.registerFunction(tomc_map, False, "NoSpherA2")

def deformation_map(resolution=0.1, return_map=False):
  use_tsc = OV.GetParam('snum.NoSpherA2.use_aspherical')
  if use_tsc == False:
    print("ERROR! Deformation is only available when using a .tsc file!")
    return
  from cctbx_olex_adapter import OlexCctbxAdapter
  cctbx_adapter = OlexCctbxAdapter()
  table_name = str(OV.GetParam("snum.NoSpherA2.file"))
  time = os.path.getmtime(table_name)
  if NoSpherA2_instance.reflection_date is None or time < NoSpherA2_instance.reflection_date:
    from smtbx.structure_factors import direct
    xray_structure = cctbx_adapter.xray_structure()
    one_h = direct.f_calc_modulus_squared(
        xray_structure, table_file_name=table_name)
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
    NoSpherA2_instance.set_f_calc_obs_sq_one_h_linearisation(f_calc, f_sq_obs, one_h)
  else:
    f_sq_obs, f_calc = NoSpherA2_instance.f_obs_sq, NoSpherA2_instance.f_calc
  f_sq_obs, f_calc_spher = cctbx_adapter.get_fo_sq_fc()
  f_diff = f_calc.f_obs_minus_f_calc(1, f_calc_spher)
  from cctbx import sgtbx
  f_diff = f_diff.expand_to_p1()
  def_map = f_diff.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                           resolution_factor=1,grid_step=float(resolution)).apply_volume_scaling()
  if return_map==True:
    return def_map
  plot_fft_map_cube(def_map,"deform")

OV.registerFunction(deformation_map, False, "NoSpherA2")

def obs_map(resolution=0.1, return_map=False, use_f000=False):
  from cctbx_olex_adapter import OlexCctbxAdapter
  cctbx_adapter = OlexCctbxAdapter()
  use_tsc = OV.GetParam('snum.NoSpherA2.use_aspherical')
  if use_tsc == True:
    table_name = str(OV.GetParam("snum.NoSpherA2.file"))
    time = os.path.getmtime(table_name)
    if NoSpherA2_instance.reflection_date is None or time < NoSpherA2_instance.reflection_date:
      from smtbx.structure_factors import direct
      xray_structure = cctbx_adapter.xray_structure()
      one_h = direct.f_calc_modulus_squared(
        xray_structure, table_file_name=table_name)
      f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
      NoSpherA2_instance.set_f_calc_obs_sq_one_h_linearisation(f_calc, f_sq_obs, one_h)
    else:
      f_sq_obs, f_calc = NoSpherA2_instance.f_obs_sq, NoSpherA2_instance.f_calc
  else:
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()
  f_obs = f_sq_obs.f_sq_as_f()
  k = math.sqrt(OV.GetOSF())
  f_obs.apply_scaling(factor=1./k)
  f_obs = f_obs.phase_transfer(f_calc)
  from cctbx import sgtbx
  if use_f000 == True or use_f000 == "True":
    f000 = float(olx.xf.GetF000())
    obs_map = f_obs.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1,
                              grid_step=float(resolution),
                              f_000=f000).apply_volume_scaling()
  else:
    obs_map = f_obs.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1,grid_step=float(resolution)).apply_volume_scaling()
  if return_map==True:
    return obs_map
  plot_fft_map_cube(obs_map,"obs")

OV.registerFunction(obs_map, False, "NoSpherA2")

def calc_map(resolution=0.1,return_map=False, use_f000=False):
  from cctbx_olex_adapter import OlexCctbxAdapter
  cctbx_adapter = OlexCctbxAdapter()
  use_tsc = OV.GetParam('snum.NoSpherA2.use_aspherical')
  if use_tsc == True:
    table_name = str(OV.GetParam("snum.NoSpherA2.file"))
    time = os.path.getmtime(table_name)
    if NoSpherA2_instance.reflection_date is None or time < NoSpherA2_instance.reflection_date:
      from smtbx.structure_factors import direct
      xray_structure = cctbx_adapter.xray_structure()
      one_h = direct.f_calc_modulus_squared(
        xray_structure, table_file_name=table_name)
      f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc(one_h_function=one_h)
      NoSpherA2_instance.set_f_calc_obs_sq_one_h_linearisation(f_calc, f_sq_obs, one_h)
    else:
      f_sq_obs, f_calc = NoSpherA2_instance.f_obs_sq, NoSpherA2_instance.f_calc
  else:
    f_sq_obs, f_calc = cctbx_adapter.get_fo_sq_fc()
  from cctbx import sgtbx
  if use_f000 == True or use_f000 == "True":
    f000 = float(olx.xf.GetF000())
    calc_map = f_calc.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1, grid_step=float(resolution),
                              f_000=f000).apply_volume_scaling()
  else:
    calc_map = f_calc.fft_map(symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
                              resolution_factor=1, grid_step=float(resolution)).apply_volume_scaling()
  if return_map==True:
    return calc_map
  plot_fft_map_cube(calc_map,"calc")

OV.registerFunction(calc_map, False, "NoSpherA2")

def show_fft_map(resolution=0.1,map_type="diff",use_f000=False,print_peaks=False):
  if map_type == "diff":
    plot_fft_map(residual_map(resolution, return_map=True,print_peaks=print_peaks))
  elif map_type == "fcfmc":
    plot_fft_map(deformation_map(resolution, return_map=True))
  elif map_type == "obs":
    plot_fft_map(obs_map(resolution,return_map=True,use_f000=use_f000))
  elif map_type == "calc":
    plot_fft_map(calc_map(resolution,return_map=True,use_f000=use_f000))
  elif map_type == "tomc":
    plot_fft_map(tomc_map(resolution,return_map=True,use_f000=use_f000))

OV.registerFunction(show_fft_map, False, "NoSpherA2")

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
#print "OK."
