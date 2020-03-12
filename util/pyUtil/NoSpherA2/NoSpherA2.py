from olexFunctions import OlexFunctions
OV = OlexFunctions()

import os
import sys
import htmlTools
import olex
import olx
import olex_core
import gui


import shutil
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
    self.wfn_job_dir = os.path.join(p_path,"olex2","Wfn_job")
    self.history_dir = os.path.join(p_path,"olex2","NoSpherA2_history")


    if not from_outside:
      self.setup_gui()

    self.setup_har_executables()
    self.setup_pyscf()
    self.setup_discamb()
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
      print("No Hart executable found!")
    check_for_matching_fcf()

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
      print "No MPI implementation found in PATH!\n"
      self.cpu_list_str = '1'

  def launch(self):
    OV.SetVar('NoSpherA2-Error',"None")
    wfn_code = OV.GetParam('snum.NoSpherA2.source')
    if wfn_code == "Please Select...":
      olx.Alert("No tsc generator selected",\
"""Error: No generator for tsc files selected. 
Please select one of the generators from the drop-down menu.""", "O", False)
      return
    self.jobs_dir = os.path.join("olex2","Wfn_job")
    self.history_dir = os.path.join("olex2","NoSpherA2_history")
    if not os.path.exists(self.jobs_dir):
      os.mkdir(self.jobs_dir)
    if not os.path.exists(self.history_dir):
      os.mkdir(self.history_dir)

    calculate = OV.GetParam('snum.NoSpherA2.Calculate')
    if not calculate:
      return
    if not self.basis_list_str:
      print("Could not locate usable HARt executable")
      return
      
    tsc_exists = False
    f_time = None
    
    if (wfn_code != "DICAMB") and (olx.xf.latt.IsGrown() != 'true'):
      from cctbx_olex_adapter import OlexCctbxAdapter
      ne = 0
      for sc in OlexCctbxAdapter().xray_structure().scatterers():
        ne += sc.electron_count()
      Z = olx.xf.au.GetZ()
      mult = int(OV.GetParam('snum.NoSpherA2.multiplicity'))
      if (ne % 2 == 0) and (mult % 2 == 0):
        print "Error! Multiplicity and number of electrons is even. This is imposible!\n"
        OV.SetVar('NoSpherA2-Error',"Multiplicity")
        return False
      elif (ne % 2 == 1) and (mult % 2 == 1):
        print "Error! Multiplicity and number of electrons is uneven. This is imposible!\n"
        OV.SetVar('NoSpherA2-Error',"Multiplicity")
        return False
        
    for file in os.listdir(olx.FilePath()):
      if file.endswith(".tsc"):
        tsc_exists = True
        f_time = os.path.getmtime(file)
    if tsc_exists:
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
      

    self.setup_har_executables()
    
    parts = OV.ListParts()
    if parts != None:
      parts = list(parts)
    experimental_SF = OV.GetParam('snum.NoSpherA2.wfn2fchk_SF')
    
    disorder_groups = None
    nr_parts = None 
    if not parts:
      nr_parts = 1
    elif len(parts) > 1:
      cif = None
      if wfn_code == "Tonto":
        cif = True
      elif wfn_code == "DISCAMB":
        cif = True
      else:
        cif = False
      deal_with_parts(cif)
      nr_parts = len(parts)
        
    job = Job(self, olx.FileName())
    if nr_parts > 1:
      for i in range(nr_parts):
        if parts[i] == 0:
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
        if os.path.exists(os.path.join(self.wfn_job_dir,olx.FileName()+".hkl")): 
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
                elif "Gaussian" in wfn_code:
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
        with open("%s_part_%s.cif" %(OV.ModelSrc(), parts[i]),"r") as incif:
          for line in incif:
            if "_atom_site_disorder_group" in line:
              atom_loop_reached = True
              out_cif.write(line)
            elif atom_loop_reached == True:
              if line != '\n':
                temp = line.split(' ')
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
        else:
          if wfn_code != "Tonto":
            shutil.move("%s_part_%s.xyz" %(OV.ModelSrc(), parts[i]),os.path.join(self.wfn_job_dir,"%s.xyz"%(OV.ModelSrc())))
            OV.SetParam('snum.NoSpherA2.fchk_file',olx.FileName() + ".fchk")
            try:
              self.wfn(folder=self.wfn_job_dir,xyz=False) # Produces Fchk file in all cases that are not fchk or tonto directly
            except NameError as error:
              print "Aborted due to: ",error
              OV.SetVar('NoSpherA2-Error',error)
              return False
          if experimental_SF == False or wfn_code == "Tonto":
            try:
              job.launch(self.wfn_job_dir)
            except NameError as error:
              print "Aborted due to: ", error
              OV.SetVar('NoSpherA2-Error',error)
              return False
            if 'Error in' in open(os.path.join(job.full_dir, job.name+".err")).read():
              OV.SetVar('NoSpherA2-Error',"StructrueFactor")
              return False
            olx.html.Update()
            #combine_sfs(force=True,part=i)
            shutil.copy(os.path.join(job.full_dir, job.name+".tsc"),job.name+"_part_"+str(parts[i])+".tsc")
          else:
            wfn_fn = os.path.join(OV.FilePath(),self.wfn_job_dir, job.name+".wfn")
            hkl_fn = os.path.join(OV.FilePath(),self.wfn_job_dir, job.name+".hkl")
            cif_fn = os.path.join(OV.FilePath(),job.name+".cif")
            asym_fn = os.path.join(OV.FilePath(),self.wfn_job_dir, job.name+".cif")
            cuqct_tsc(wfn_fn,hkl_fn,cif_fn,asym_fn)
            shutil.copy("experimental.tsc",job.name+"_part_"+str(parts[i])+".tsc")
            shutil.move("wfn_2_fchk.log",os.path.join(OV.FilePath(),self.wfn_job_dir,"wfn_2_fchk_part_"+str(parts[i])+".log"))
          for file in os.listdir('.'):
            if file.endswith(".wfn"):
              shutil.move(file,file + "_part%d"%parts[i])
            if file.endswith(".wfx"):
              shutil.move(file,file + "_part%d"%parts[i])
            if file.endswith(".ffn"):
              shutil.move(file,file + "_part%d"%parts[i])
            if file.endswith(".fchk"):
              shutil.move(file,file + "_part%d"%parts[i])
      print "Writing combined tsc file\n"
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
                elif "Gaussian" in wfn_code:
                  if ".chk" not in f:
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
          cif = str(os.path.join(job.full_dir, job.name+".cif"))
          olx.File(cif)
          OV.SetParam('snum.NoSpherA2.fchk_file',olx.FileName() + ".fchk")
        elif wfn_code == "Tonto":
          success = True
          try:
            job.launch()
          except NameError as error:
            print "Aborted due to: ", error
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
            OV.SetVar('NoSpherA2-Error',"Tonro")
            return False
          olx.html.Update()
          if (experimental_SF == False):
            shutil.copy(os.path.join(job.full_dir, job.name+".tsc"),job.name+".tsc")
            OV.SetParam('snum.NoSpherA2.file',job.name+".tsc")
        else:
          #OV.SetParam('snum.NoSpherA2.fchk_file',olx.FileName() + ".fchk")
          if wfn_code.lower().endswith(".wfn"):
            pass
          else:
            try:
              self.wfn(folder=self.jobs_dir) # Produces Fchk file in all cases that are not fchk or tonto directly
            except NameError as error:
              print "Aborted due to: ",error
              OV.SetVar('NoSpherA2-Error',error)
              return False
      
        # make the tsc file
        
        if (experimental_SF == True):
          if wfn_code.lower().endswith(".wfn"):
            wfn_fn = os.path.join(OV.FilePath(), job.name+".wfn")
          else:
            wfn_fn = os.path.join(OV.FilePath(),job.full_dir, job.name+".wfn")
          hkl_fn = os.path.join(OV.FilePath(),job.full_dir, job.name+".hkl")
          cif_fn = os.path.join(OV.FilePath(),job.name+".cif")
          wfn_cif_fn = os.path.join(OV.FilePath(),job.full_dir, job.name+".cif")
          olx.Kill("$Q")
          olx.File(wfn_cif_fn)
          cuqct_tsc(wfn_fn,hkl_fn,cif_fn,wfn_cif_fn)
          OV.SetParam('snum.NoSpherA2.file',"experimental.tsc")
          
        elif wfn_code != "Tonto":
          success = True
          try:
            job.launch()
          except NameError as error:
            print "Aborted due to: ", error
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

    if OV.GetParam('snum.NoSpherA2.h_aniso') == True:
      olex.m("anis -h")
    if OV.GetParam('snum.NoSpherA2.h_afix') == True:
      olex.m("sel $h")
      olex.m("Afix 0")
    olex.m('delins list')
    olex.m('addins LIST -3')
    add_disp = OV.GetParam('snum.NoSpherA2.add_disp')
    if add_disp is True:
      olex.m('gendisp -source=sasaki')
    #add_info_to_tsc()

  def wfn(self,folder='',xyz=True):
    if not self.basis_list_str:
      print("Could not locate usable HARt executable")
      return

    wfn_object = wfn_Job(self,olx.FileName(),dir=folder)
    software = OV.GetParam('snum.NoSpherA2.source')
    if software == "ORCA":
      wfn_object.write_orca_input(xyz)
    elif software == "Gaussian03":
      wfn_object.write_gX_input(xyz)
    elif software == "Gaussian09":
      wfn_object.write_gX_input(xyz)
    elif software == "Gaussian16":
      wfn_object.write_gX_input(xyz)
    elif software == "pySCF":
      wfn_object.write_pyscf_script(xyz)

    try:
      wfn_object.run()
    except NameError as error:
      print "The follwing error occured druing QM Calculation: ",error
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
      _ = os.path.join(self.p_path, "%s" %exe_pre)
      if os.path.exists(_):
        self.wfn_2_fchk = _
      else:
        self.wfn_2_fchk = olx.file.Which("%s" %exe_pre)
    OV.SetVar("Wfn2Fchk",self.wfn_2_fchk)
    
  def setup_pyscf(self):
    if OV.GetParam('user.NoSpherA2.use_pyscf') == True:
      if sys.platform[:3] == 'win':
        self.ubuntu_exe = olx.file.Which("ubuntu.exe")
      else:
        self.ubuntu_exe = None
      self.has_pyscf = OV.GetParam('user.NoSpherA2.has_pyscf')
      if self.has_pyscf == False:
        if self.ubuntu_exe != None and os.path.exists(self.ubuntu_exe):
          import subprocess
          pyscf_check = None
          try:
            child = subprocess.Popen([self.ubuntu_exe,'run',"python -c 'import pyscf' && echo $?"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = child.communicate()
            rc = child.returncode
            if rc == 0:
              pyscf_check = True
              OV.SetParam('user.NoSpherA2.has_pyscf',True) 
          except:
            pass
          if pyscf_check == True:
            self.has_pyscf = True
          else:
            print ("To use pySCF please install pySCF and pip in your ubuntu environment:\nsudo apt update\nsudo apt install python python-numpy python-scipy python-h5py python-pip\nsudo -H pip install pyscf")
        elif self.ubuntu_exe == None :
          import subprocess
          try:
            child = subprocess.Popen(['python',  "-c 'import pyscf' && echo $?"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = child.communicate()
            rc = child.returncode
            if rc == 0:
              pyscf_check = True
              OV.SetParam('user.NoSpherA2.has_pyscf',True) 
          except:
            pass
          if pyscf_check == True:
            self.has_pyscf = True
          else:
            print ("To use pySCF please install pySCF in your ubuntu environment:\nsudo apt update\nsudo apt install python python-numpy python-scipy python-h5py python-pip\nsudo -H pip install pyscf")
        else:
          if sys.platform[:3] == 'win':
            print ("To use pySCF please install the ubuntu and linux subprocess framework for windows 10 and afterwords run:\nsudo apt update\nsudo apt install python python-numpy python-scipy python-h5py python-pip\nsudo -H pip install pyscf")
          else:
            print ("To use pySCF please install python, pip and pyscf\n")
      if self.has_pyscf == True:
        if "pySCF" not in self.softwares:
          self.softwares = self.softwares + ";pySCF"

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
        self.softwares = self.softwares + ";ORCA"
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

  def write_gX_input(self,xyz):
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    olx.Kill("$Q")
    if xyz:
      olx.File(coordinates_fn,p=10)
    xyz = open(coordinates_fn,"r")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".com"
    com = open(self.input_fn,"w")
    method = None
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
    if OV.GetParam('snum.NoSpherA2.method') == "HF":
      control += "rhf"
      method = "RHF"
    else:
      control += method
      method = OV.GetParam('snum.NoSpherA2.method')
    cxontrol += "/gen NoSymm 6D 10F IOp(3/32=2) formcheck output=wfn"
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
    charge = OV.GetParam('snum.NoSpherA2.charge')
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
    com.write(" \n./%s.wfn\n\n" %self.name)
    com.close()

  def write_orca_input(self,xyz):
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    olx.Kill("$Q")
    if xyz:
      olx.File(coordinates_fn,p=10)
    xyz = open(coordinates_fn,"r")
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
    control = "! NoPop NoFinalGrid 3-21G AIM "
    method = OV.GetParam('snum.NoSpherA2.method')
    grid = OV.GetParam('snum.NoSpherA2.becke_accuracy')
    if method == "HF":
      control += "rhf "
    else:
      control += method + ' '
      if method == "M062X":
        if grid == "Normal":
          control += "Grid6 "
        elif grid == "Low":
          control += "Grid5 "
        elif grid == "High":
          control += "Grid7 "
        elif grid == "Max":
          control += "Grid7 "
      else:
        if grid == "Low":
          control += "Grid1 "
        elif grid == "High":
          control += "Grid4 "
        elif grid == "Max":
          control += "Grid7 "
    control = control + OV.GetParam('snum.NoSpherA2.ORCA_SCF_Conv') + ' ' + OV.GetParam('snum.NoSpherA2.ORCA_SCF_Strategy')
    relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
    if method == "BP86" or method == "PBE":
      if relativistic == True:
        control = control + " DKH2 SARC/J RI"
      else:
        control = control + " def2/J RI"
    else:
      if relativistic == True:
        control = control + " DKH2 SARC/J RIJCOSX"
      else:
        control = control + " def2/J RIJCOSX"
      if grid == "Normal":
        control += "NoFinalGridX "
      elif grid == "Low":
        control += "GridX2 NoFinalGridX "
      elif grid == "High":
        control += "GridX5 NoFinalGridX "
      elif grid == "Max":
        control += "GridX9 NoFinalGridX "
    charge = OV.GetParam('snum.NoSpherA2.charge')
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
      if run > 1:
        inp.write("%scf\n   Guess MORead\n   MOInp \""+self.name+"2.gbw\"\nend\n")
    inp.close()
    
  def write_pyscf_script(self,xyz):
    coordinates_fn = os.path.join(self.full_dir, self.name) + ".xyz"
    olx.Kill("$Q")
    if xyz:
      olx.File(coordinates_fn,p=10)
    xyz = open(coordinates_fn,"r")
    self.input_fn = os.path.join(self.full_dir, self.name) + ".py"
    inp = open(self.input_fn,"w")
    basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    basis_set_fn = os.path.join(self.parent.basis_dir,basis_name)
    basis = open(basis_set_fn,"r")
    ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
    charge = OV.GetParam('snum.NoSpherA2.charge')
    mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    mem = OV.GetParam('snum.NoSpherA2.mem')
    mem_value = float(mem) * 1024
    if OV.GetParam('snum.NoSpherA2.pySCF_PBC') == False:
      inp.write("#!/usr/bin/env python\n\nfrom pyscf import gto, scf, dft, lib\n")
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
      inp.write("''',\n  verbose = 5,\n)\nmol.output = '%s_pyscf.log'\n"%self.name)
      inp.write("mol.charge = %s\n"%charge)
      inp.write("mol.spin = %s\n"%str(int(mult)-1))
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
      if OV.GetParam('snum.NoSpherA2.method') == "rhf":
        model_line = "scf.RHF(mol)"
      else:
        model_line = "dft.RKS(mol)"
      if OV.GetParam('snum.NoSpherA2.Relativistic') == True:
        model_line += ".x2c()"
      #inp.write("mf = sgx.sgx_fit(%s)\n"%model_line)
      inp.write("mf = %s\n"%model_line)
      if OV.GetParam('snum.NoSpherA2.method') == "rks":
        #inp.write("mf.xc = 'b3lyp'\nmf.with_df.dfj = True\n")
        inp.write("mf.xc = 'b3lyp'\nmf = mf.density_fit()\nmf.with_df.auxbasis = 'weigend'\n")
      inp.write("mf.kernel()\nwith open('%s.wfn', 'w') as f1:\n  from pyscf.tools import wfn_format\n  wfn_format.write_mo(f1,mol,mf.mo_coeff, mo_energy=mf.mo_energy, mo_occ=mf.mo_occ)\n"%self.name)
      inp.close()
    else:
      from cctbx_olex_adapter import OlexCctbxAdapter
      cctbx_adaptor = OlexCctbxAdapter()
      uc = cctbx_adaptor.reflections.f_obs.unit_cell()
      cm = uc.metrical_matrix()
      from math import sqrt
      inp.write("#!/usr/bin/env python\n\nfrom pyscf.pbc import gto, scf, dft\nfrom pyscf import lib\n")
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
      inp.write("''',\n  verbose = 5,\n)\ncell.output = '%s_pyscf.log'\n"%self.name)
      inp.write("cell.a = '''%.5f %.5f %.5f\n            %.5f %.5f %.5f\n            %.5f %.5f %.5f'''\n"%(sqrt(cm[0]),sqrt(cm[3]),sqrt(cm[4]),sqrt(cm[3]),sqrt(cm[1]),sqrt(cm[5]),sqrt(cm[4]),sqrt(cm[5]),sqrt(cm[2])))
      inp.write("cell.charge = %s\n"%charge)
      inp.write("cell.spin = %s\n"%str(int(mult)-1))
      inp.write("cell.max_memory = %s\n"%str(mem_value))
      inp.write("cell.precision = 1.0e-09\ncell.exp_to_discard = 0.1\n")
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
      inp.write("\n}\ncell.build()\n")
      
      model_line = None
      if OV.GetParam('snum.NoSpherA2.method') == "HF":
        model_line = "scf.RHF(cell)"
      else:
        model_line = "dft.RKS(cell)"
      #inp.write("mf = sgx.sgx_fit(%s)\n"%model_line)
      inp.write("cf = %s\n"%model_line)
      if OV.GetParam('snum.NoSpherA2.method') != "HF":
        #inp.write("mf.xc = 'b3lyp'\nmf.with_df.dfj = True\n")
        inp.write("cf.xc = 'b3lyp'\ncf = cf.mix_density_fit()\ncf.with_df.auxbasis = 'weigend'\n")
      inp.write("cf.kernel()\nwith open('%s.wfn', 'w') as f1:\n  from pyscf.tools import wfn_format\n  wfn_format.write_mo(f1,cell,cf.mo_coeff, mo_energy=cf.mo_energy, mo_occ=cf.mo_occ)\n"%self.name)
      inp.close()

  def run(self):
    args = []
    basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
    software = OV.GetParam('snum.NoSpherA2.source')
    fchk_exe = ""
    if software == "ORCA":
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
    elif software == "pySCF":
      input_fn = self.name + ".py"
      if self.parent.ubuntu_exe != None and os.path.exists(self.parent.ubuntu_exe):
        args.append(self.parent.ubuntu_exe)
        args.append('run')
        args.append("python %s"%input_fn)
      elif self.ubuntu_exe == None:
        args.append('python')
        args.append(input_fn)

    os.environ['fchk_cmd'] = '+&-'.join(args)
    os.environ['fchk_file'] = self.name
    os.environ['fchk_dir'] = os.path.join(OV.FilePath(),self.full_dir)

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

    if software == "ORCA":
      if '****ORCA TERMINATED NORMALLY****' in open(os.path.join(self.full_dir, self.name+"_orca.log")).read():
        pass
      else:
        OV.SetVar('NoSpherA2-Error',"ORCA")
        raise NameError('Orca did not terminate normally!')
    elif "Gaussian" in software:
      if 'Normal termination of Gaussian' in open(os.path.join(self.full_dir, self.name+".log")).read():
        pass
      else:
        OV.SetVar('NoSpherA2-Error',"Gaussian")
        raise NameError('Gaussian did not terminate normally!')
      
    if("g03" in args[0]):
      shutil.move(os.path.join(self.full_dir,"Test.FChk"),os.path.join(self.full_dir,self.name+".fchk"))
      shutil.move(os.path.join(self.full_dir,self.name + ".log"),os.path.join(self.full_dir,self.name+"_g03.log"))
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")
    elif("g09" in args[0]):
      shutil.move(os.path.join(self.full_dir,"Test.FChk"),os.path.join(self.full_dir,self.name+".fchk"))
      shutil.move(os.path.join(self.full_dir,self.name + ".log"),os.path.join(self.full_dir,self.name+"_g09.log"))
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")
    elif("g16" in args[0]):
      shutil.move(os.path.join(self.full_dir,"Test.FChk"),os.path.join(self.full_dir,self.name+".fchk"))
      shutil.move(os.path.join(self.full_dir,self.name + ".log"),os.path.join(self.full_dir,self.name+"_g16.log"))
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")
    elif("orca" in args[0]):
      #shutil.move(os.path.join(self.full_dir,self.name + ".log"),os.path.join(self.full_dir,self.name+"_orca.log"))
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfn"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfn"), self.name+".wfn")
      if (os.path.isfile(os.path.join(self.full_dir,self.name + ".wfx"))):
        shutil.copy(os.path.join(self.full_dir,self.name + ".wfx"), self.name+".wfx")
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
      with open("wfn_2_fchk.log", "r") as log:
        x = log.read()
        if x:
          print x
      if os.path.exists(self.name+".fchk"):
        shutil.copy(self.name+".fchk",os.path.join(self.full_dir, self.name+".fchk"))
      else:
        OV.SetVar('NoSpherA2-Error',"NoFchk")
        raise NameError("No fchk generated!")
      shutil.move("wfn_2_fchk.log",os.path.join(self.full_dir, self.name+"_wfn2fchk.log"))

def cuqct_tsc(wfn_file, hkl_file, cif, wfn_cif):
  folder = OV.FilePath()
  ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
  if os.path.isfile(os.path.join(folder, "wfn_2_fchk.log")):
    shutil.move(os.path.join(folder, "wfn_2_fchk.log"), os.path.join(folder, "wfn_2_fchk.log_org"))
  move_args = []
  wfn_2_fchk = OV.GetVar("Wfn2Fchk")
  move_args.append(wfn_2_fchk)
  move_args.append("-wfn")
  move_args.append(wfn_file)
  if not os.path.exists(hkl_file):
    from cctbx_olex_adapter import OlexCctbxAdapter
    from iotbx.shelx import hklf
    cctbx_adaptor = OlexCctbxAdapter()
    with open(hkl_file, "w") as out:
      f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_filtered
      f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
  move_args.append("-hkl")
  move_args.append(hkl_file)
  move_args.append("-cif")
  move_args.append(cif)
  move_args.append("-asym_cif")
  move_args.append(wfn_cif)
  if (ncpus > 1):
    move_args.append('-cpus')
    move_args.append(ncpus)
  if (OV.GetParam('snum.NoSpherA2.wfn2fchk_debug') == True):
    move_args.append('-v')
  if (OV.GetParam('snum.NoSpherA2.becke_accuracy') != "Normal"):
    move_args.append('-acc')
    if (OV.GetParam('snum.NoSpherA2.becke_accuracy') == "Low"):
      move_args.append('1')
    elif (OV.GetParam('snum.NoSpherA2.becke_accuracy') == "High"):
      move_args.append('3')
    elif (OV.GetParam('snum.NoSpherA2.becke_accuracy') == "Max"):
      move_args.append('4')
  os.environ['cuqct_cmd'] = '+&-'.join(move_args)
  os.environ['cuqct_dir'] = folder
  pyl = OV.getPYLPath()
  if not pyl:
    print("A problem with pyl is encountered, aborting.")
    return
  import subprocess
  p = subprocess.Popen([pyl,
                        os.path.join(p_path, "cuqct-launch.py")])
  while p.poll() is None:
    time.sleep(5)
    olx.html.Update()

def discamb(folder, name, discamb_exe):
  move_args = []
  move_args.append(discamb_exe)
  hkl_file = os.path.join(folder,name+".hkl")
  cif = os.path.join(folder,name+".cif")
  move_args.append(cif)
  move_args.append(hkl_file)
  if not os.path.exists(hkl_file):
    from cctbx_olex_adapter import OlexCctbxAdapter
    from iotbx.shelx import hklf
    cctbx_adaptor = OlexCctbxAdapter()
    with open(hkl_file, "w") as out:
      f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_filtered
      f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)

  os.environ['discamb_cmd'] = '+&-'.join(move_args)
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
#      if(run > 1):
#        args.append("-restart-scf")
#        args.append("t")
        

    else:
      # We want these from supplied fchk file """
      fchk_file = OV.GetParam('snum.NoSpherA2.fchk_file')
#      shutil.copy(fchk_file,os.path.join(self.full_dir,self.name+".fchk"))
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
    
    if fchk_source == "Tonto" and OV.GetParam('snum.NoSpherA2.keep_wfn') == True:
      if os.path.exists(os.path.join(self.full_dir,self.name+".wfn")):
        shutil.copy(os.path.join(self.full_dir,self.name+".wfn"), self.name+".wfn")
      else:
        print "WFN File not found!"
        OV.SetVar('NoSpherA2-Error',"NoWFN")
        raise NameError("No WFN found!")
      move_args = []
      basis_dir = self.parent.basis_dir
      basis_name = OV.GetParam("snum.NoSpherA2.basis_name")
      method = OV.GetParam("snum.NoSpherA2.method")
      move_args.append(self.parent.wfn_2_fchk)
      move_args.append("-wfn")
      move_args.append(os.path.join(self.full_dir,self.name+".wfn"))
      move_args.append("-b")
      move_args.append(basis_name)
      move_args.append("-d")
      if sys.platform[:3] == 'win':
        move_args.append(basis_dir.replace("/","\\"))
      else:
        move_args.append(basis_dir+'/')
      move_args.append("-method")
      move_args.append(method)
      logname = "wfn_2_fchk.log"
      m = subprocess.Popen(move_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
      while m.poll() is None:
        time.sleep(1)
      shutil.move(logname,os.path.join(self.full_dir,self.name+"_wfn2fchk.log"))
      if os.path.exists(os.path.join(self.full_dir,self.name+".fchk")):
        shutil.copy(os.path.join(self.full_dir,self.name+".fchk"), self.name+".fchk")
      else:
        raise NameError("No fchk generated!")

def add_info_to_tsc():
  tsc_fn = os.path.join(OV.GetParam('snum.NoSpherA2.dir'),OV.GetParam('snum.NoSpherA2.file'))
  if not os.path.isfile(tsc_fn):
    print "Error finding tsc File!\n"
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
Please cite:\n\nF. Kleemiss, H. Puschmann, O. Dolomanov, S.Grabowsky - to be published - 2020
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
  data_block = False
  for line in tsc:
    if ("CIF:" not in line) and ("DATA:" not in line) and ("data:" not in line):
      write_file.write(line)
    elif "CIF:" in line:
      cif_block_present = True
      write_file.write(line)
    elif ("DATA:" in line):
      data_block = True
      if cif_block_present == False:
        write_file.write(details_text)
        write_file.write(line)
      else:
        write_file.write(line)
    elif ("data:" in line):
      data_block = True
      if cif_block_present == False:
        write_file.write(details_text)
        write_file.write(line)
      else:
        print "CIF BLOCK is there"
        write_file.write(line)
  write_file.close()
        
OV.registerFunction(add_info_to_tsc,True,'NoSpherA2')

def combine_tscs():
  import glob
  import math
  
  parts = list(OV.ListParts())
  nr_parts = len(parts)

  if debug:
    t_beg = time.time()
  sfc_name = OV.ModelSrc()
  tsc_modular = OV.GetParam('snum.NoSpherA2.modular')
  tsc_source = OV.GetParam('snum.NoSpherA2.source')
  tsc_file = OV.GetParam('snum.NoSpherA2.file')
  
  if tsc_source.lower().endswith("fchk"):
    tsc_source = os.path.basename(tsc_source)

  _mod = ""
  if not tsc_modular == "direct":
    _mod = "_%s"%tsc_modular
   
  tsc_dst = os.path.join(OV.FilePath(), sfc_name + _mod + "_total.tsc")
  if os.path.exists(tsc_dst):
    backup = os.path.join(OV.FilePath(), "tsc_backup")
    if not os.path.exists(backup):
      os.mkdir(backup)
    i = 1
    while (os.path.exists(os.path.join(backup,sfc_name + _mod + ".tsc") + "_%d"%i)):
      i = i + 1
    try:
      shutil.move(tsc_dst,os.path.join(backup,sfc_name + _mod + ".tsc") + "_%d"%i)
    except:
      pass
      
  d = {}
  sfs_fp = None
  symops_fp = None
  nr_atoms = 0
  atom_list = []
  nr_data_lines = 0
    
  for part in range(int(nr_parts)):
    if part == 0:
      continue
    print "Working on Part %d of %d\n"%(parts[part],int(nr_parts)-1)
    #print "looking for: "+os.path.join(OV.FilePath(), sfc_name + _mod + "_part_%d.tsc"%parts[part])
    tsc_fn = os.path.join(OV.FilePath(), sfc_name + _mod + "_part_%d.tsc"%parts[part])
    if not os.path.isfile(tsc_fn):
      print "Error finding tsc Files!\n"
      return False

    if debug:
      t1 = time.time()
    
    with open(tsc_fn) as f:
      tsc = f.readlines()
    part_atom_list = None
    values = []
    header = []
    data = False
    for line in tsc:
      if data == False:
        header.append(line.replace('\n',''))
      if 'SCATTERERS' in line:
        part_atom_list = line[12: ].replace('\n','').split(' ')
        #print part_atom_list
      elif 'data:' in line:
        data = True
        continue
      elif 'DATA:' in line:
        data = True
        continue
      if data == True:
        values.append(line)
        if part == 1:
          nr_data_lines += 1
      
    for atom in range(len(part_atom_list)):
      name = part_atom_list[atom]
      if name in atom_list:
        continue
      else:
        nr_atoms += 1
        #print "Appending: %s\n"%name
        atom_list.append(name)
      d.setdefault(name,{})
      sfc_l = []
      hkl_l = []
 
      for line in range(len(values)):
        digest = values[line].split(" ")
        if atom == 0 and part == 1:
          hkl_l.append([digest[0],digest[1],digest[2]])
        if tsc_modular == "modulus":
          _ = digest[2+atom].split(",")
          a = float(_[0])
          b = float(_[1])
          v = math.sqrt(a*a + b*b)
          sfc_l.append("%.6f" %v)
        elif tsc_modular == "absolute":
          _ = digest[2+atom].split(",")
          a = abs(float(_[0]))
          b = abs(float(_[1]))
          sfc_l.append(",".join(["%.5f" %a, "%.5f" %b]))
        elif tsc_modular == "direct":
          sfc_l.append(digest[3+atom].replace('\n',''))
      if atom == 0:
        d.setdefault('hkl', hkl_l)
      d[name].setdefault('sfc', sfc_l)

  if debug:
    print ("Time for reading and processing the separate files: %.2f" %(time.time() - t1))

  value_lines = []
  for i in range(nr_data_lines):
    temp_string = ""
    for j in range(3):
      temp_string += d['hkl'][i][j]+' '
    for j in range(nr_atoms):
      temp_string += d[atom_list[j]]['sfc'][i]+' '
    value_lines.append(temp_string)

  ol = []
  _d = {'anomalous':'false',
        'title': OV.FileName(),
        'scatterers': " ".join(atom_list),
        'software': OV.GetParam('snum.NoSpherA2.source'),
        'method': OV.GetParam('snum.NoSpherA2.method'),
        'basis_set': OV.GetParam('snum.NoSpherA2.basis_name'),
        'charge': OV.GetParam('snum.NoSpherA2.charge'),
        'mult': OV.GetParam('snum.NoSpherA2.multiplicity'),
        'relativistic': OV.GetParam('snum.NoSpherA2.Relativistic'),
        'radius': OV.GetParam('snum.NoSpherA2.cluster_radius'),
        'DIIS': OV.GetParam('snum.NoSpherA2.DIIS')
        }
  for i in range(len(header)):
    if 'SCATTERERS' in header[i]:
      ol.append('SCATTERERS: %(scatterers)s'%_d)
    elif 'SOFTWARE' in header[i]:
      ol.append('   SOFTWARE:       %(software)s'%_d)
    elif 'BASIS SET' in header[i]:
      ol.append('   BASIS SET:      %(basis_set)s'%_d)
    elif 'DATA:' in header[i]:
      f_time = os.path.getctime(os.path.join(OV.FilePath(),sfc_name + _mod + "_part_1.tsc"))
      import datetime
      f_date = datetime.datetime.fromtimestamp(f_time).strftime('%Y-%m-%d_%H-%M-%S')
      ol.append('   DATE:           %s'%f_date)
      ol.append('   PARTS:          %d'%(int(nr_parts)-1))
      if tsc_source == "Tonto":
        ol.append('   CLUSTER RADIUS: %(radius)s'%_d)
        ol.append('   DIIS CONV.:     %(DIIS)s'%_d)
      ol.append('DATA:\n')
    else:
      ol.append(header[i].replace('\n',''))

  t = "\n".join(ol)
  with open(tsc_dst, 'w') as wFile:
    wFile.write(t)
    for line in value_lines:
      wFile.write(line+'\n')

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

def deal_with_parts(cif=True):
  parts = OV.ListParts()
  olx.Kill("$Q")
  if not parts:
    return
  for part in parts:
    if part == 0:
      continue
    olex.m("showp 0 %s" %part)
    if cif == False:
      fn = "%s_part_%s.xyz" %(OV.ModelSrc(), part)
      olx.File(fn,p=8)
    fn = "%s_part_%s.cif" %(OV.ModelSrc(), part)
    olx.File(fn)
  olex.m("showp")
OV.registerFunction(deal_with_parts,True,'NoSpherA2')

def check_for_matching_fcf():
  p = os.path.dirname(OV.GetParam('snum.NoSpherA2.file'))
  name = OV.ModelSrc()
  fcf = os.path.join(p,name + '.fcf')
  if os.path.exists(fcf) and os.path.exists(fcf):
    OV.SetVar('have_valid_nosphera2_fcf', True)
    return True
  else:
    OV.SetVar('have_valid_nosphera2_fcf', False)
    return False
OV.registerFunction(check_for_matching_fcf,True,'NoSpherA2')

def read_disorder_groups():
  input = OV.GetParam('snum.NoSpherA2.Disorder_Groups')
  if input == None:
    return []
  groups = input.split(';')
  from array import array
  result = []
  for i in range(len(groups)):
    result.append([])
    for part in groups[i].split(','):
      if '-' in part:
        a, b = part.split('-')
        a, b = int(a), int(b)
        result[i].extend(range(a,b+1))
      else:
        a = int(part)
        result[i].append(a) 
#    print result[i]
#  print result
  return result
OV.registerFunction(read_disorder_groups,True,'NoSpherA2')

def is_disordered():
  parts = OV.ListParts()
  
  nr_parts = None 
  if not parts:
    return False
  else:
    return True
OV.registerFunction(is_disordered,True,'NoSpherA2')

def change_basisset(input):
  OV.SetParam('snum.NoSpherA2.basis_name',input)
  if "x2c" in input:
    OV.SetParam('snum.NoSpherA2.Relativistic',True)
  else:
    OV.SetParam('snum.NoSpherA2.Relativistic',False)
OV.registerFunction(change_basisset,True,'NoSpherA2')

def get_functional_list():
  wfn_code = OV.GetParam('snum.NoSpherA2.source')
  list = None
  if wfn_code == "Tonto" or wfn_code == "pySCF":
    list = "HF;B3LYP;"
  else:
    list = "HF;BP86;PBE;PBE0;M062X;B3LYP;wB97;wB97X;"
  return list
OV.registerFunction(get_functional_list,True,'NoSpherA2')

def change_tsc_generator(input):
  if input == "Get ORCA":
    import webbrowser
    webbrowser.open('https://orcaforum.kofo.mpg.de/index.php', new=2)
  elif input == "Get DISCAMB":
    import webbrowser
    webbrowser.open('http://4xeden.uw.edu.pl/software/discamb/', new=2)
  else:
    OV.SetParam('snum.NoSpherA2.source',input)
    if input != "DICAMB":
      F000 = olx.xf.GetF000()
      Z = olx.xf.au.GetZ()
      nr_electrons= int(float(F000) / float(Z))
      mult = int(OV.GetParam('snum.NoSpherA2.multiplicity'))
      if (nr_electrons % 2 == 0) and (mult %2 == 0):
        OV.SetParam('snum.NoSpherA2.multiplicity',1)
      elif (nr_electrons % 2 != 0) and (mult %2 != 0):
        OV.SetParam('snum.NoSpherA2.multiplicity',2)
OV.registerFunction(change_tsc_generator,True,'NoSpherA2')

def write_symmetry_file(debug=False):
  import olx
  from cctbx import crystal
  cs = crystal.symmetry(space_group_symbol="hall: "+str(olx.xf.au.GetCellSymm("hall")))
  if(debug == True):
    print cs.space_group().n_smx()
  symops = []
  with open("symmetry.file",'w') as symm_file:
    for rt in cs.space_group().smx(False):
      if(debug == True):
        print rt
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
    print symops
OV.registerFunction(write_symmetry_file,True,'NoSpherA2')
    

def set_default_cpu_and_mem():
  import math
  import multiprocessing
  parallel = OV.GetVar("Parallel")
  max_cpu = multiprocessing.cpu_count()
  current_cpus = OV.GetParam('snum.NoSpherA2.ncpus')
  if not parallel:
    OV.SetParam('snum.NoSpherA2.ncpus',1)
    return
  if (max_cpu == 1): 
    OV.SetParam('snum.NoSpherA2.ncpus',1)
    return
  elif (current_cpus != "1"):
    return
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
  OV.SetParam('snum.NoSpherA2.ncpus',str(int(tf_cpu)))
  OV.SetParam('snum.NoSpherA2.mem',str(tf_mem))
OV.registerFunction(set_default_cpu_and_mem,True,'NoSpherA2')

NoSpherA2_instance = NoSpherA2()
OV.registerFunction(NoSpherA2_instance.available, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.launch, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getBasisListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getCPUListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getwfn_softwares, False, "NoSpherA2")
#print "OK."