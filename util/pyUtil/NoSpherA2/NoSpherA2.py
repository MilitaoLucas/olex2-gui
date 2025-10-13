import os
import sys
import olex
import olx
#import olex_core
import gui
import shutil
import time
import subprocess

from olexFunctions import OV
from PluginTools import PluginTools as PT

# Local imports for NoSpherA2 functions
from utilities import calculate_number_of_electrons, deal_with_parts, is_disordered, cuqct_tsc, combine_tscs
from decors import run_with_bitmap
from hybrid_GUI import make_hybrid_GUI
from wsl_conda import WSLAdapter, CondaAdapter
import Wfn_Job
#including these two here to register functions, ignoring F401 for unused imports
import ELMO # noqa: F401
import cubes_maps # noqa: F401
import xharpy
import pyscf
import psi4

if OV.HasGUI():
  get_template = gui.tools.TemplateProvider.get_template

try:
  from_outside = False
  p_path = os.path.dirname(os.path.abspath(__file__))
except Exception as e:
  from_outside = True
  p_path = os.path.dirname(os.path.abspath("__file__"))

d = {}
for line in open(os.path.join(p_path, 'def.txt')).readlines():
  line = line.strip()
  if not line or line.startswith("#"):
    continue
  d[line.split("=")[0].strip()] = line.split("=")[1].strip()

p_name = d['p_name']
p_htm = d['p_htm']
p_img = eval(d['p_img'])
p_scope = d['p_scope']

class NoSpherA2(PT):
  def __init__(self):
    olx.stopwatch.start("NoSpherA2.__init__()")
    super(NoSpherA2, self).__init__()
    olx.stopwatch.start("HARt tools")
#Block to make the old HARt Tools placeholder
    self.p_htm = "harp"
    self.p_name = "HARp"
    self.p_img = p_img
    self.p_scope = "harp"

    if not from_outside:
      self.setup_gui()
#revert back to the original NoSpherA2 values
    olx.stopwatch.start("Initial variables  & Phil")
    self.p_name = p_name
    self.p_path = p_path
    self.p_scope = p_scope
    self.p_htm = p_htm
    self.deal_with_phil(operation='read')
    self.print_version_date()
    print("")
    self.parallel = False
    self.softwares = ""
    self.NoSpherA2 = ""
    self.WSLAdapter = None
    #self.f_calc = None
    #self.f_obs_sq = None
    #self.one_h_linearisation = None
    #self.reflection_date = None
    self.jobs_dir = os.path.join("olex2","Wfn_job")
    self.history_dir = os.path.join("olex2","NoSpherA2_history")
    self.xharpy_adapter = None
    self.pyscf_adapter = None
    import platform
    if platform.architecture()[0] != "64bit":
      print ("-- Warning: Detected 32bit Olex2, NoSpherA2 only works on 64 bit OS.")

    file_search_probes = {
        "ubuntu": ["ubuntu", "ubuntu2404", "ubuntu2204", "ubuntu2004", "ubuntu1804"],
        "Gaussian09": ["g09"],
        "Gaussian03": ["g03"],
        "Gaussian16": ["g16"],
    }
    
    def probe_file(file, names):
        ret = ""
        for name in names:
            ret = self.setup_software(file, name[0])
            if ret != "" and ret is not None:
                break
        setattr(self,f"{file}_exe", ret)

#   Attempts to find all known types of software to be used during NoSpherA2 runs
    olx.stopwatch.start("Interfaced executables")

    calls = {
        'wsl_conda': self.setup_WSL_softwares,
        'NSA2': self.setup_NoSpherA2,
        'har_exe': self.setup_har_executables,
        'discamb_exe': self.setup_discamb,
        'elmodb_exe': self.setup_elmodb,
        'orca_exe': self.setup_orca_executables,
        'xtb_exe': self.setup_xtb_executables,
        'ptb_exe': self.setup_ptb_executables,
    }
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=min(8, len(calls))) as ex:
      futures = {}
      for name, func in calls.items():
        futures[ex.submit(func)] = ("call", name)
      for name, files in file_search_probes.items():
        futures[ex.submit(probe_file, name, files)] = ("probe", f"{name}_exe")
      for fut in as_completed(futures):
        kind, name = futures[fut]
        try:
            res = fut.result()
        except Exception as e:
            print(f"Error setting up {name}: {e}")
            res = e

    olx.stopwatch.start("basis sets")
    if os.path.exists(self.NoSpherA2):
      self.basis_dir = os.path.join(os.path.split(self.NoSpherA2)[0], "basis_sets").replace("\\", "/")
      if os.path.exists(self.basis_dir):
        basis_list = os.listdir(self.basis_dir)
        basis_list.sort()
        self.basis_list_str = ';'.join(basis_list)
      else:
        self.basis_list_str = None
    else:
      self.basis_list_str = None
      self.basis_dir = None
      print("-- No NoSpherA2 executable found!")
    print(" ")

  def setup_WSL_softwares(self):
    try:
      self.WSLAdapter = WSLAdapter()
      if self.WSLAdapter.get_wsl_distro_list() == []:
        print("-- There seems to be a problem with the distro recognition!")
        print("-- Please check your WSL installation and make sure you have at least one distro installed.\nYou can install one using the Microsoft Store or 'wsl --install Ubuntu'.")
        raise RuntimeError("No WSL adapter available, hence no Conda support!")
      if self.WSLAdapter.is_windows and not self.WSLAdapter.is_wsl:
        print("-- WSL is not available, xharpy and pyscf will not be available!")
        self.WSLAdapter = None
      else:
        self.conda_adapter = CondaAdapter(self.WSLAdapter)
        if not self.conda_adapter.have_conda:
          sel = olx.Alert("Conda not available",\
"""Error: Conda is not available.
Do you want me to install conda for you?""", "YN", False)
          if sel == "Y":
            print("-- Installing micromamba using the official installation script...")
            try:
              exports = """
export MAMBA_ROOT_PREFIX="${HOME}/.micromamba" &&
export BIN_FOLDER="${HOME}/.local/bin" &&
export INIT_YES="yes" &&
export CONDA_FORGE_YES="yes" &&
export PREFIX_LOCATION="${HOME}/.micromamba" &&"""
              result = self.WSLAdapter.call_command(f"{exports} curl -L micro.mamba.pm/install.sh | bash -s -- -b")
              if result.returncode != 0:
                print("-- Failed to install micromamba.")
                raise subprocess.CalledProcessError(result.returncode, "micromamba installation")
              result = self.WSLAdapter.call_command("${HOME}/.local/bin/micromamba shell init -s bash")
              if result.returncode != 0:
                print("-- Failed to initialize micromamba shell.")
                raise subprocess.CalledProcessError(result.returncode, "micromamba shell init")
              else:
                print("-- Micromamba installed successfully.")
                print("-- Please restart Olex2 to use it.")
            except subprocess.CalledProcessError as e:
              print(f"-- Error installing micromamba: {e}")
              print("-- Please install conda manually and restart Olex2.")
          else:
            print("-- Conda is not available, xharpy and pyscf will not be available!")
          self.conda_adapter = None
        else:
          print("-- Available conda envs:", self.conda_adapter.get_available_conda_envs())
          #olx.stopwatch.start("xharpy exe")
          self.setup_xharpy()
          #olx.stopwatch.start("pyscf exe")
          self.setup_pyscf()
          #olx.stopwatch.start("psi4 exe")
          self.setup_psi4()
    except Exception as e:
      print(f"-- Error setting up WSL Adapter: {e}")
      self.WSLAdapter = None
      self.conda_adapter = None

  #def set_f_obs_sq(self, f_obs_sq):
  #  self.f_obs_sq = f_obs_sq

  #def set_one_h_linearization(self, one_h_linarization):
  #  self.one_h_linearisation = one_h_linarization

  #def set_f_calc_obs_sq_one_h_linearisation(self,f_calc,f_obs_sq,one_h_linarization):
  #  self.f_calc = f_calc
  #  self.f_obs_sq = f_obs_sq
  #  self.one_h_linearisation = one_h_linarization
  #  file_name = OV.GetParam("snum.NoSpherA2.file")
  #  time = os.path.getmtime(file_name)
  #  self.reflection_date = time

  #def delete_f_calc_f_obs_one_h(self):
  #  self.f_calc = None
  #  self.f_obs_sq = None
  #  self.one_h_linearisation = None
  #  self.reflection_date = None

  def setup_har_executables(self):
    self.mpiexec = self.setup_software(None, "mpiexec")
    self.mpi_har = self.setup_software(None, "hart_mpi")
    self.exe = self.setup_software(None, "hart")
    if sys.platform[:3] != 'win':
      self.mpihome = self.mpiexec[:-11]
      if 'LD_LIBRARY_PATH' in os.environ:
        if self.mpihome + 'lib' not in os.environ['LD_LIBRARY_PATH']:
          os.environ['LD_LIBRARY_PATH'] = self.mpihome + 'lib:' + self.mpihome + 'lib/openmpi:' + os.environ['LD_LIBRARY_PATH']
      else:
        os.environ['LD_LIBRARY_PATH'] = self.mpihome + 'lib:' + self.mpihome + 'lib/openmpi'
      if 'LD_RUN_PATH' in os.environ:
        if self.mpihome + 'lib/openmpi' not in os.environ['LD_RUN_PATH']:
          os.environ['LD_RUN_PATH'] = self.mpihome + 'lib/openmpi:' + os.environ['LD_RUN_PATH']
      else:
        os.environ['LD_RUN_PATH'] = self.mpihome + 'lib/openmpi'

    if os.path.exists(self.mpiexec) and os.path.exists(self.mpi_har):
      self.parallel = True
      OV.SetVar("Parallel",True)
      if "Tonto" not in self.softwares:
        self.softwares = self.softwares + ";Tonto"

    else:
      if "Tonto" not in self.softwares:
        self.softwares = self.softwares + ";Tonto"
      print("-- No MPI implementation found in PATH!\n-- Tonto, ORCA and other software relying on it will only have 1 CPU available!\n")

  def tidy_wfn_jobs_folder(self):
    backup = os.path.join(self.jobs_dir, "backup")
    to_backup = self.jobs_dir
    wfn_job_dir = self.jobs_dir
    if os.path.exists(to_backup):
      _l = 1
      while (os.path.exists(f"{backup}_{_l}")):
        _l += 1
      backup += f"_{_l}"

    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
    run = None
    if Full_HAR:
      run = OV.GetVar('Run_number')
    if os.path.exists(wfn_job_dir):
      files = list(file for file in os.listdir(wfn_job_dir)
            if "backup_" not in file)
      if len(files) != 0:
        os.mkdir(backup)
      for f in files:
        f_work = os.path.join(wfn_job_dir, f)
        f_dest = os.path.join(backup, f)
        if Full_HAR:
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
            elif self.wfn_code == "ORCA 6.0" or self.wfn_code == "ORCA 6.1":
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

  def wipe_wfn_jobs_folder(self):
    print(f"Deleting {self.jobs_dir}... ")
    if os.path.exists(self.jobs_dir):
      shutil.rmtree(self.jobs_dir)
    print(" ... done!")

  def launch(self) -> bool:
    OV.SetVar('NoSpherA2-Error',"None")
    wfn_code = OV.GetParam('snum.NoSpherA2.source')
    self.wfn_code = wfn_code
    self.name = olx.FileName()
    basis = OV.GetParam('snum.NoSpherA2.basis_name')
    update = OV.GetParam('snum.NoSpherA2.Calculate')
    experimental_SF = OV.GetParam('snum.NoSpherA2.NoSpherA2_SF')
    if "Please S" in wfn_code and update:
      olx.Alert("No tsc generator selected",\
"""Error: No generator for tsc files selected.
Please select one of the generators from the drop-down menu.""", "O", False)
      OV.SetVar('NoSpherA2-Error',"TSC Generator unselected")
      return False
    if not os.path.exists(self.jobs_dir):
      os.mkdir(self.jobs_dir)
    if not os.path.exists(self.history_dir):
      os.mkdir(self.history_dir)

    if not update:
      return True
    if self.NoSpherA2 == "":
      print("Could not locate usable NoSpherA2 executable")
      return False

    # This checks ne multiplicity and Number of electrons
    if (wfn_code != OV.GetParam('user.NoSpherA2.discamb_exe')) and (wfn_code != "Thakkar IAM") and (olx.xf.latt.IsGrown() != 'true') and not is_disordered():
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

    # Now check whether and do some history file handlings
    tsc_exists = False
    f_time = None
    if not OV.GetParam('snum.NoSpherA2.no_backup'):
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
    if parts is not None:
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
      elif wfn_code == OV.GetParam('user.NoSpherA2.discamb_exe'):
        cif = True
      parts, groups = deal_with_parts()
      nr_parts = len(parts)

    if nr_parts > 1:
      wfn_files = []
      need_to_combine = False
      need_to_partition = False
      if ".wfn" in wfn_code or ".wfx" in wfn_code or ".gbw" in wfn_code or ".fchk" in wfn_code or ".molden" in wfn_code:
        print("Calculation from wavefunction file with disorder not possible, sorry!\n")
        return False
      groups_counter = 0
      # Check if job folder already exists and (if needed) make the backup folders
      self.tidy_wfn_jobs_folder()
      olex.m("CifCreate_4NoSpherA2")
      shutil.move(self.name + ".cif_NoSpherA2", os.path.join(self.jobs_dir, self.name + ".cif"))
      if wfn_code == "fragHAR":
        # Special case for fragHAR, which will handle the CIF and partitioning itself.
        try:
          self.wfn(folder=self.jobs_dir, xyz=False)
          return True
        except NameError as error:
          print ("Aborted due to: ",error)
          OV.SetVar('NoSpherA2-Error',error)
          return False
      for i in range(nr_parts):
        if parts[i] == 0:
          groups_counter+=1
          continue
        wfn_job_dir = os.path.join(self.jobs_dir, "Part_%d" % parts[i])
        if wfn_code.lower().endswith(".fchk"):
          raise NameError('Disorder is not possible with precalculated fchks!')
        try:
          os.mkdir(wfn_job_dir)
        except FileExistsError:
          # If the folder already exists, we will just use it
          print("Folder %s already exists, using it." % wfn_job_dir)
        except Exception as error:
          print ("Aborted due to: ",error)
          OV.SetVar('NoSpherA2-Error',error)
          return False
        atom_loop_reached = False
        out_cif = open(os.path.join(wfn_job_dir, "%s.cif" % (OV.ModelSrc())), "w")
        with open(os.path.join(self.jobs_dir, "%s.cif" % (OV.ModelSrc())), "r") as incif:
          for line in incif:
            if "_atom_site_disorder_group" in line:
              atom_loop_reached = True
              out_cif.write(line)
            elif atom_loop_reached:
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
        if wfn_code == OV.GetParam('user.NoSpherA2.discamb_exe'):
          #DISCMAB is used
          discamb(os.path.join(OV.FilePath(), wfn_job_dir), self.name, self.discamb_exe)
          shutil.copy(os.path.join(wfn_job_dir, self.name + ".tsc"), self.name + "_part_" + str(parts[i]) + ".tsc")
          shutil.copy(os.path.join(wfn_job_dir, "discambMATTS2tsc.log"), os.path.join(self.jobs_dir, "discamb2tsc.log"))
          need_to_combine = True
        elif wfn_code == "XHARPy":
          try:
            self.xharpy_adapter.calculate_tsc_cli(os.path.join(wfn_job_dir, "%s.cif" % (OV.ModelSrc())))
            shutil.copy(f"{self.name}.tsc", os.path.join(wfn_job_dir, self.name + ".tsc"))
            shutil.move(f"{self.name}.tsc", os.path.join(OV.FilePath(), self.name + "_part_" + str(parts[i]) + ".tsc"))
          except Exception as error:
            print ("Aborted due to: ",error)
            OV.SetVar('NoSpherA2-Error',error)
            return False
          need_to_combine = True
        elif wfn_code == "Hybrid":
          # We are in Hybrid mode
          hybrid_part_wfn_code = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d"%(parts[i]))
          if hybrid_part_wfn_code == OV.GetParam('user.NoSpherA2.discamb_exe'):
            groups.pop(i-groups_counter)
            groups_counter+=1
            discamb(os.path.join(OV.FilePath(), wfn_job_dir), self.name, self.discamb_exe)
            shutil.copy(os.path.join(wfn_job_dir, self.name + ".tsc"), self.name + "_part_" + str(parts[i]) + ".tsc")
            shutil.copy(os.path.join(wfn_job_dir, "discambMATTS2tsc.log"), os.path.join(self.jobs_dir, "discamb2tsc.log"))
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
            if hybrid_part_wfn_code == "Thakkar IAM":
              wfn_fn = path_base + ".xyz"
              try:
                shutil.copy(os.path.join(wfn_job_dir, "%s.xyz" % (self.name)), "%s.xyz" % self.name)
              except Exception as error:
                print ("Aborted due to: ",error)
                pass
            wfn_fn = None
            # groups[i-groups_counter].append(0)
            # groups[i-groups_counter].append(parts[i])
            endings = [".gbw", ".ffn", ".molden", ".fchk", ".xtb", ".xyz", ".wfn", ".wfx"]
            for file in os.listdir(os.getcwd()):
              if "_part" in file:
                continue
              temp = None
              if any(file.endswith(x) for x in endings):
                temp = os.path.splitext(file)[0] + "_part%d" % parts[i] + os.path.splitext(file)[1]
              if temp is not None:
                shutil.move(file, temp)
                wfn_files.append(temp)
                break
        else:
          # Neither Hybrid nor DISCAMB are used, so ORCA; g16; pySCF etc
          need_to_partition = True
          if wfn_code != "Tonto":
            shutil.move("%s_part_%s.xyz" % (self.name, parts[i]), os.path.join(wfn_job_dir, "%s.xyz" % (self.name)))
            if wfn_code == "ELMOdb":
              mutation = OV.GetParam('snum.NoSpherA2.ELMOdb.mutation')
              pdb_name = job.name + ".pdb"
              if mutation:
                pdb_name += "_mut" + str(parts[i])
              if os.path.exists(os.path.join(OV.FilePath(), pdb_name)):
                shutil.copy(os.path.join(OV.FilePath(), pdb_name), os.path.join(wfn_job_dir, self.name + ".pdb"))
              else:
                OV.SetVar('NoSpherA2-Error',"ELMOdb")
                if mutation:
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
          if (not experimental_SF) or wfn_code == "Tonto":
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
            if OV.HasGUI():
              olx.html.Update()
            shutil.copy(os.path.join(job.full_dir, self.name + ".tsc"), self.name + "_part_" + str(parts[i]) + ".tsc")
          elif wfn_code == "Thakkar IAM" or wfn_code == "SALTED":
            wfn_fn = os.path.join(OV.FilePath(), wfn_job_dir, self.name + ".xyz")
          else:
            wfn_fn = None
            path_base = os.path.join(OV.FilePath(), wfn_job_dir, self.name)
            if os.path.exists(path_base + ".wfx"):
              if (wfn_fn is None or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".fchk")):
                wfn_fn = path_base + ".wfx"
            elif os.path.exists(path_base + ".fchk"):
              if (wfn_fn is None):
                wfn_fn = path_base + ".fchk"
            elif os.path.exists(path_base + ".wfn"):
              wfn_fn = path_base + ".wfn"
            elif os.path.exists(path_base + ".gbw"):
              if (wfn_fn is None or wfn_fn.endswith(".wfx") or wfn_fn.endswith(".wfn") or wfn_fn.endswith(".fchk") and Wfn_Job.is_orca_new()):
                wfn_fn = path_base + ".gbw"
            elif os.path.exists(path_base + ".molden"):
              wfn_fn = path_base + ".molden"
            elif os.path.exists(path_base + ".xtb"):
              wfn_fn = path_base + ".xtb"
            elif os.path.exists(path_base + ".xyz"):
              wfn_fn = path_base + ".xyz"
            else:
              return False
          wfn_files.append(wfn_fn)
          endings = [".wfn", ".wfx", ".gbw", ".ffn", ".molden", ".fchk", ".wfnlog", ".xtb", ".xyz"]
          for file in os.listdir(os.getcwd()):
            if "_part" in file:
              continue
            temp = None
            if any(file.endswith(x) for x in endings):
              temp = os.path.splitext(file)[0] + "_part%d" % parts[i] + os.path.splitext(file)[1]
            if temp is not None:
              shutil.move(file,temp)

      # End of loop over parts
      if need_to_partition:
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
      if need_to_combine:
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

      if wfn_code == OV.GetParam('user.NoSpherA2.discamb_exe'):
        cif = str(os.path.join(self.jobs_dir, self.name + ".cif"))
        olx.File(cif)
        discamb(os.path.join(OV.FilePath(), self.jobs_dir), self.name, self.discamb_exe)
        shutil.copy(os.path.join(OV.FilePath(), self.jobs_dir, self.name + ".tsc"), self.name + ".tsc")
        OV.SetParam('snum.NoSpherA2.file', self.name + ".tsc")
      elif wfn_code == "XHARPy":
          self.xharpy_adapter.calculate_tsc_cli(f"{os.path.join(self.jobs_dir, self.name)}.cif")
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
          if 'Error in' in open(job.error_fn).read():
            success = False
            with open(job.error_fn) as file:
              for i in file.readlines():
                if 'Error in' in i:
                  print(i)
            OV.SetVar('NoSpherA2-Error',"StructureFactor")
            return False
          if success:
            OV.SetVar('NoSpherA2-Error',"Tonto")
            return False
          if OV.HasGUI():
            olx.html.Update()
          if not experimental_SF:
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

        if experimental_SF:
          if wfn_code != "fragHAR" and wfn_code != "SALTED":
            path_base = os.path.join(self.jobs_dir, self.name)
            if wfn_code.lower().endswith(".wfn") or wfn_code.lower().endswith(".wfx") or \
               wfn_code.lower().endswith(".molden") or wfn_code.lower().endswith(".gbw"):
              wfn_fn = wfn_code
            else:
              endings = [".fchk", ".wfn", ".ffn", ".wfx", ".molden", ".xtb"]
              if Wfn_Job.is_orca_new():
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

          elif wfn_code == "SALTED":
            path_base = os.path.join(self.jobs_dir, self.name)
            cif_fn = path_base + ".cif"
            wfn_fn = path_base + ".xyz"
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
          if not success:
            OV.SetVar('NoSpherA2-Error',"Tonto")
            return False
          if OV.HasGUI():
            olx.html.Update()
          shutil.copy(os.path.join(job.full_dir, job.name+".tsc"),job.name+".tsc")
          OV.SetParam('snum.NoSpherA2.file',job.name+".tsc")
    # add_info_to_tsc()
    if not OV.GetParam('snum.NoSpherA2.full_HAR'):
      OV.SetParam('snum.NoSpherA2.Calculate', False)
    
    return True

  def wfn(self, folder='', xyz=True, part=0):
    if not self.basis_list_str:
      print("Could not locate usable HARt executable")
      return
    software = OV.GetParam('snum.NoSpherA2.source')
    wfn_object = Wfn_Job.wfn_Job(self, olx.FileName(), folder, software)
    if software == "fragHAR":
      from .fragHAR import run_frag_HAR_wfn
      main_folder = OV.FilePath()
      fn = olx.FileName()
      res_file = os.path.join(main_folder, fn + ".res")
      cif_file = os.path.join(folder, fn + ".cif")
      qS_file = os.path.join(main_folder, fn + ".qS")
      run_frag_HAR_wfn(res_file, cif_file, qS_file, wfn_object, part)
      return
    elif software == "Hybrid":
      software_part = OV.GetParam("snum.NoSpherA2.Hybrid.software_Part%d" % part)
      basis_part = OV.GetParam("snum.NoSpherA2.Hybrid.basis_name_Part%d" % part)
      method_part = OV.GetParam("snum.NoSpherA2.Hybrid.method_Part%d" % part)
      relativistc = OV.GetParam("snum.NoSpherA2.Hybrid.Relativistic_Part%d" % part)
      charge = OV.GetParam("snum.NoSpherA2.Hybrid.charge_Part%d" % part)
      mult = OV.GetParam("snum.NoSpherA2.Hybrid.multiplicity_Part%d" % part)
      conv = OV.GetParam("snum.NoSpherA2.Hybrid.ORCA_SCF_Conv_Part%d" % part)
      strategy = OV.GetParam("snum.NoSpherA2.Hybrid.ORCA_SCF_Strategy_Part%d" % part)
      damping = OV.GetParam("snum.NoSpherA2.Hybrid.pySCF_Damping_Part%d" % part)
      wfn_object.software = software_part
      if software_part == "ELMOdb":
        print("ELMO not yet fully implemented for Hybrid!!! Sorry!!")
        return False
      elif software_part == "Psi4":
        print("Psi4 not yet fully implemented for Hybrid!!! Sorry!!")
        return False
      wfn_object.write_input(xyz, basis_part, method_part, relativistc, charge, mult, strategy, conv, part, damping)
    else:
      wfn_object.write_input(xyz)
    if software == "Hybrid":
      if software_part != "Thakkar IAM" and software_part != "SALTED":
        try:
          wfn_object.run(part, software_part, basis_part)
        except NameError as error:
          print("The following error occured during QM Calculation: ",error)
          OV.SetVar('NoSpherA2-Error',error)
          raise NameError('Unsuccesfull Wavefunction Calculation!')
    elif software != "Thakkar IAM" and software != "SALTED":
      try:
        wfn_object.run(part)
      except NameError as error:
        print("The following error occured during QM Calculation: ",error)
        OV.SetVar('NoSpherA2-Error',error)
        raise NameError('Unsuccesfull Wavefunction Calculation!')

  def setup_NoSpherA2(self):
    self.NoSpherA2 = self.setup_software(None, "NoSpherA2")
    print("-- NoSpherA2 executable is:", self.NoSpherA2)
    if self.NoSpherA2 == "" or self.NoSpherA2 is None:
      print ("-- ERROR!!!! No NoSpherA2 executable found! THIS WILL NOT WORK!")
      OV.SetVar('NoSpherA2-Error',"None")
      raise NameError('No NoSpherA2 Executable')
    self.softwares += ";Thakkar IAM"
    OV.SetVar("NoSpherA2", self.NoSpherA2)

  def setup_pyscf(self):
    try:
      self.pyscf_adapter = pyscf.pyscf(self.WSLAdapter, self.conda_adapter)
      self.pyscf_adapter.conda_adapter.set_conda_env_name('pyscf')
      self.softwares += ";pySCF" if "pySCF" not in self.softwares else ""
    except Exception as e:
      print("-- Error setting up pySCF:", e)
      self.pyscf_adapter = None
      if "Get pySCF" not in self.softwares:
        self.softwares += ";Get pySCF"
        
  def setup_psi4(self):
    try:
      self.psi4_adapter = psi4.psi4(self.WSLAdapter, self.conda_adapter)
      self.psi4_adapter.conda_adapter.set_conda_env_name('psi4')
      self.softwares += ";Psi4" if "Psi4" not in self.softwares else ""
    except Exception as e:
      print("-- Error setting up Psi4:", e)
      self.psi4_adapter = None
      if "Get Psi4" not in self.softwares:
        self.softwares += ";Get Psi4"

  def setup_elmodb(self):
    self.elmodb_exe = self.setup_software("ELMOdb", "elmodb")
    self.elmodb_lib = ""
    lib_name = "LIBRARIES_AND_BASIS-SETS/"
    self.elmodb_lib_name = lib_name
    _ = os.path.join(self.p_path, "%s" %lib_name)
    if os.path.exists(_):
      self.elmodb_lib = _
    else:
      self.elmodb_lib = olx.file.Which("%s" % lib_name)

  def setup_software(self, name, exe_pre:str, get = False):
    # Determine platform-specific executable name
    exe_name = exe_pre + (".exe" if sys.platform.startswith("win") else "")
    # search PATH
    exe_path = shutil.which(exe_name)
    # Update software list if requested and executable exists
    if name and exe_path:
        if name not in self.softwares:
            self.softwares = f"{self.softwares};{name}" if self.softwares else name
    elif get and exe_path is None:
        # If the executable is not found, add the "Get" to the software list
        if "Get " + name not in self.softwares:
            self.softwares = f"{self.softwares};Get {name}"

    return exe_path or ""

  def setup_orca_executables(self):
    # search PATH
    self.orca_exe = shutil.which("orca" + (".exe" if sys.platform.startswith("win") else ""))
    if self.orca_exe and os.path.exists(self.orca_exe):
      try:
        import subprocess
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        p = subprocess.run(['orca', '-v'], capture_output=True, text=True, creationflags=creationflags)
        idx = p.stdout.index("Version")
        result = p.stdout[idx:idx + 50].split('\n')[0].split()[1]
        print("-- ORCA VERSION: ", result)  # print the version
        OV.SetParam('NoSpherA2.ORCA_Version', result.split(".")[0])
        OV.SetParam('NoSpherA2.ORCA_Version_Minor', result.split(".")[1])
      except Exception as e:
        print("-- Failed to evaluate ORCA version", e)
      Orca_Vers = OV.GetParam('NoSpherA2.ORCA_Version')
      Orca_Vers_Minor = OV.GetParam('NoSpherA2.ORCA_Version_Minor')
      if "ORCA" not in self.softwares:
        if Orca_Vers == "4":
          orca_string = "ORCA"
        elif Orca_Vers == "5":
          orca_string = "ORCA 5.0"
        else:
          orca_string = f"ORCA {Orca_Vers}.{Orca_Vers_Minor}"
        self.softwares = self.softwares + ";" + orca_string
        OV.SetParam('snum.NoSpherA2.source', orca_string)
    else:
      self.softwares = f"{self.softwares};Get ORCA"

  def setup_xtb_executables(self):
    if not OV.IsDebugging():
      return
    self.xtb_exe = self.setup_software("xTB", "xtb", True)

  def setup_ptb_executables(self):
    if not OV.IsDebugging():
      return
    self.ptb_exe = self.setup_software("pTB", "ptb")

  def setup_discamb(self):
    self.discamb_exe = self.setup_software(OV.GetParam('user.NoSpherA2.discamb_exe'), OV.GetParam('user.NoSpherA2.discamb_exe'))
    if not os.path.exists(self.discamb_exe):
      self.discamb_exe = self.setup_software("discambMATTS", "discambMATTS2tsc", True)

  def setup_xharpy(self):
    try:
      self.xharpy_adapter = xharpy.xharpy(g_WSLAdapter=self.WSLAdapter, g_CondaAdapter=self.conda_adapter)
      self.xharpy_adapter.conda_adapter.set_conda_env_name('xharpy')
      self.softwares += ";XHARPy" if "XHARPy" not in self.softwares else ""
    except Exception as e:
      print("-- XHARPy setup failed:", e)
      self.xharpy_adapter = None
      self.softwares += ";Get XHARPy" if "Get XHARPy" not in self.softwares else ""

  def get_distro_list(self):
    list = self.WSLAdapter.get_wsl_distro_list()
    cleaned_list = ["Select Distro to use<-None"]
    for item in list:
      cleaned_item = item.strip().replace('\00','')
      if cleaned_item:
        cleaned_item = cleaned_item.replace("(",'').replace(")",'').replace("* ",'').strip()
        if cleaned_item != "":
          cleaned_list.append(cleaned_item)
    return ";".join(cleaned_list)

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
      if OV.GetParam("snum.NoSpherA2.basis_adv"): 
        final_string += basis + ";"                                                                                                                                                                                       
      elif self.check_for_atom_in_basis_set(basis, XRS, elements):
        final_string += basis + ";"
    if source == "ORCA" or source == "ORCA 5.0" or source == "fragHAR" or source == "Hybrid" or source == "ORCA 6.0" or source == "ORCA 6.1":
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
    hyperthreading = OV.GetParam('user.refinement.has_HT')
    if not hyperthreading:
      max_cpu /= 2
    for n in range(1, int(max_cpu)):
      cpu_list.append(str(n + 1))
    # ORCA and Tonto rely on MPI, so only make it available if mpiexec is found
    if soft == "Tonto" or "ORCA" in soft or soft == "fragHAR":
      if not os.path.exists(self.mpiexec):
        return '1'
    # otherwise allow more CPUs
    return ';'.join(cpu_list)

  def get_SALTED_model_locations(self):
    old = OV.GetParam('user.NoSpherA2.salted_models_list')
    return old

  def getwfn_softwares(self):
    parts = OV.ListParts()
    if parts is not None:
      parts = list(parts)
    if OV.IsDebugging():
      if not parts:
        return self.softwares + ";fragHAR;SALTED;"
      elif len(parts) > 1:
        return self.softwares + ";Hybrid;fragHAR;SALTED;"
      else:
        return self.softwares + ";fragHAR;SALTED;"
    else:
      if parts and len(parts) > 1:
        return self.softwares + ";Hybrid;"
    return self.softwares + ";"

  def available(self):
    return os.path.exists(self.NoSpherA2)

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
    #args.append("-ED")
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
    OV.htmlUpdate()

class Job(object):
  out_fn = None
  error_fn = None
  full_dir = None

  def __init__(self, parent, name):
    self.parent = parent
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
    self.error_fn = os.path.join(full_dir, name) + ".err"
    self.out_fn = os.path.join(full_dir, name) + ".out"
    #initialised = False

  def launch(self,wfn_dir=''):

    if wfn_dir == '':
      model_file_name = os.path.join(self.full_dir, self.name) + "_tonto.cif"
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

      args = [self.name+"_tonto.cif",
              "-basis-dir", self.parent.basis_dir,
              "-shelx-f2", self.name+".hkl"
              ,"-basis", OV.GetParam('snum.NoSpherA2.basis_name')
              ,"-cluster-radius", str(OV.GetParam('snum.NoSpherA2.cluster_radius'))
              ,"-dtol", OV.GetParam('snum.NoSpherA2.DIIS')
              ]
      method = OV.GetParam('snum.NoSpherA2.method')
      args.append("-scf")
      if method == "HF":
        args.append("rhf")
      else:
        args.append("rks")
      if not OV.GetParam('snum.NoSpherA2.cluster_grow'):
        args.append("-complete-mol")
        args.append("f")

      if OV.GetParam('snum.NoSpherA2.Relativistic'):
        args.append("-dkh")
        args.append("t")
    elif fchk_source == "SALTED":
      salted_model_dir = OV.GetParam('snum.NoSpherA2.selected_salted_model')
      args = ["-SALTED",salted_model_dir, "-cif" ,data_file_name+".cif", "-xyz", data_file_name+".xyz", "-dmin", ]
    else:
      # We want these from supplied fchk file """
      fchk_file = OV.GetParam('snum.NoSpherA2.fchk_file')
      args = [self.name+"_tonto.cif",
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
    if not OV.GetParam('snum.NoSpherA2.keep_wfn'):
      args.append("-wfn")
      args.append("f")
    if OV.GetParam('snum.NoSpherA2.NoSpherA2_SF'):
      args.append("-scf-only")
      args.append("t")

    self.result_fn = os.path.join(self.full_dir, self.name) + ".archive.cif"
    self.error_fn = os.path.join(self.full_dir, self.name) + "_tonto.err"
    self.out_fn = os.path.join(self.full_dir, self.name) + "_tonto.out"
    self.wfn_name = os.path.join(self.full_dir, self.name) + "_tonto.ffn"
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
    tries = 0
    while tries < 20:
      if os.path.exists(self.out_fn):
        break
      tries += 1
      time.sleep(0.5)
    if not os.path.exists(self.out_fn):
      OV.SetVar('NoSpherA2-Error',"Tonto")
      raise NameError("Tonto Error! No output file!")
    else:
      with open(self.out_fn, "r") as stdout:
        while p.poll() is None:
          x = None
          try:
            x = stdout.read()
          except:
            pass
          if x:
            print(x, end='')
          time.sleep(0.5)

    if 'Error in' in open(self.error_fn).read():
      OV.SetVar('NoSpherA2-Error',"TontoError")
      raise NameError("Tonto Error!")
    if 'Wall-clock time taken for job' in open(self.out_fn).read():
      pass
    else:
      OV.SetVar('NoSpherA2-Error',"Tonto")
      raise NameError("Tonto unsuccessfull!")
    shutil.move(self.wfn_name, os.path.join(self.full_dir, self.name) + ".ffn")

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
  if software != OV.GetParam('user.NoSpherA2.discamb_exe'):
    method = OV.GetParam('snum.NoSpherA2.method')
    basis_set = OV.GetParam('snum.NoSpherA2.basis_name')
    charge = OV.GetParam('snum.NoSpherA2.charge')
    mult = OV.GetParam('snum.NoSpherA2.multiplicity')
    relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
    partitioning = OV.GetParam('snum.NoSpherA2.NoSpherA2_SF')
    accuracy = OV.GetParam('snum.NoSpherA2.becke_accuracy')
    if partitioning:
      details_text += "   PARTITIONING:   NoSpherA2\n"
      details_text += "   INT ACCURACY:   %s\n"%accuracy
    else:
      details_text += "   PARTITIONING:   Tonto\n"
    details_text += "   METHOD:         %s\n"%method
    details_text += "   BASIS SET:      %s\n"%basis_set
    details_text += "   CHARGE:         %s\n"%charge
    details_text += "   MULTIPLICITY:   %s\n"%mult
    if relativistic:
      details_text += "   RELATIVISTIC:   DKH2\n"
    if software == "Tonto":
      radius = OV.GetParam('snum.NoSpherA2.cluster_radius')
      details_text += "   CLUSTER RADIUS: %s\n"%radius
  tsc_file_name = os.path.join(OV.GetParam('snum.NoSpherA2.dir'),OV.GetParam('snum.NoSpherA2.file'))
  if os.path.exists(tsc_file_name):
    f_time = os.path.getctime(tsc_file_name)
  else:
    f_time = None
  import datetime
  f_date = datetime.datetime.fromtimestamp(f_time).strftime('%Y-%m-%d_%H-%M-%S')
  details_text += "   DATE:           %s\n"%f_date
  details_text += ":CIF"
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
      if not cif_block_present:
        write_file.write(details_text)
        write_file.write(line)
      else:
        write_file.write(line)
    elif ("data:" in line):
      #data_block = True
      if not cif_block_present:
        write_file.write(details_text)
        write_file.write(line)
      else:
        print("CIF BLOCK is there")
        write_file.write(line)
  write_file.close()

OV.registerFunction(add_info_to_tsc,False,'NoSpherA2')

def change_basisset(input):
  OV.SetParam('snum.NoSpherA2.basis_name',input)
  if "x2c" in input:
    OV.SetParam('snum.NoSpherA2.Relativistic', True)
    if OV.HasGUI():
      olx.html.SetState('NoSpherA2_ORCA_Relativistics@refine', 'True')
      olx.html.SetEnabled('NoSpherA2_ORCA_Relativistics@refine', 'True')
  elif "DKH" in input:
    OV.SetParam('snum.NoSpherA2.Relativistic', True)
    if OV.HasGUI():
      olx.html.SetState('NoSpherA2_ORCA_Relativistics@refine', 'True')
      olx.html.SetEnabled('NoSpherA2_ORCA_Relativistics@refine', 'True')
  else:
    OV.SetParam('snum.NoSpherA2.Relativistic', False)
    if OV.HasGUI():
      olx.html.SetState('NoSpherA2_ORCA_Relativistics@refine', 'False')
      olx.html.SetEnabled('NoSpherA2_ORCA_Relativistics@refine', 'False')
OV.registerFunction(change_basisset,False,'NoSpherA2')

def get_functional_list(wfn_code=None):
  if wfn_code is None:
    wfn_code = OV.GetParam('snum.NoSpherA2.source')
  list = None
  if wfn_code == "Tonto" or wfn_code == "'Please Select'":
    list = "HF;B3LYP;"
  elif wfn_code == "pySCF":
    list = "HF;PBE;B3LYP;BLYP;M062X;R2SCAN;PBE0"
  elif wfn_code == "ORCA 5.0" or wfn_code == "fragHAR":
    list = "HF;BP;BP86;PWLDA;r2SCAN;B3PW91;TPSS;PBE;PBE0;M062X;B3LYP;BLYP;wB97;wB97X;wB97X-V;DSD-BLYP"
  elif wfn_code == "ORCA 6.0" or wfn_code == "ORCA 6.1":
    list = "HF;BP;BP86;PWLDA;r2SCAN;B3PW91;PBE;PBE0;M062X;B3LYP;BLYP;wr2SCAN;wB97X-V;DSD-BLYP;TPSSh;r2SCAN0"
  elif wfn_code == "xTB":
    list = "GFN1;GFN2"
  elif wfn_code == "XHARPy":
    list = "PBE;SCAN;LDA;revPBE"
  else:
    list = "HF;BP;BP86;PWLDA;TPSS;PBE;PBE0;M062X;B3LYP;BLYP;wB97;wB97X;"
  return list
OV.registerFunction(get_functional_list,False,'NoSpherA2')

def change_tsc_generator(input):
  if input == "Get ORCA":
    olx.Shell("https://orcaforum.kofo.mpg.de/index.php")
  elif input == "Get discambMATTS":
    olx.Shell("http://4xeden.uw.edu.pl/software/discamb/")
  elif input == "Get xTB":
    olx.Shell("https://github.com/grimme-lab/xtb")
  elif input == "Get pySCF":
    wsl_adapter = NoSpherA2_instance.WSLAdapter
    olex2_folder = OV.BaseDir()
    if wsl_adapter.is_wsl:
      res = olx.Alert("Please confirm", """Do you want to automatically install pySCF using conda?
This will use conda/micromamba to install a virtual environment with pySCF in your user folder!
OlexSys and the Olex2-Team do not take any responsibility for damage done to your installation from this action.""", "YCQ")
      if res != "Y":
        print("User did not confirm the installation of pySCF, aborting.")
        return
      distros = wsl_adapter.get_wsl_distro_list()
      if len(distros) == 0 and not wsl_adapter.is_windows:
        olx.Alert("No WSL Distros found", """Please install a WSL Distro first!
For example using 'wsl --install' in a PowerShell prompt.""", "O", False)
        return
      distro = OV.GetParam('snum.NoSpherA2.distro', "Ubuntu")
      if distro == "Select Distro to use<-None" and wsl_adapter.is_windows:
        print("No WSL Distro selected.")
        print("Available Distros: ", distros)
        print("Please select a WSL Distro using spy.SetParam(snum.NoSpherA2.distro, <distro_name>).")
        return
      elif wsl_adapter.is_windows:
        print("Installing pySCF in WSL Distro: ", distro)
      print("This will take a while, please be patient.")
      wsl_adapter.call_command("bash -i -c 'micromamba create -y -n pyscf pyscf python=3.12 -c conda-forge'")
      NoSpherA2_instance.softwares.replace("Get pySCF", "pySCF")
      OV.SetParam('snum.NoSpherA2.source', "pySCF")
      olex.m("html.Update()")
  elif input == "Get XHARPy":
    wsl_adapter = NoSpherA2_instance.WSLAdapter
    olex2_folder = OV.BaseDir()
    if wsl_adapter.is_wsl:
      script = os.path.join(olex2_folder, "util", "pyUtil", "NoSpherA2", "installation_scripts", "XHARPy.sh")
      res = olx.Alert("Please confirm", f"""Do you want to automatically install XHARPy using the script in {script}?
This will use conda/micromamba to install a virtual environemnt with XHARPy in your user folder!
Please make sure that you understand the implications of this script.
On windows this will use WSL to install XHARPy, so you need to have a WSL Distro installed and configured.
OlexSys and the Olex2-Team do not take any responsibility for damage done to your installation from executing scripts.""", "YCQ")
      if res != "Y":
        print("User did not confirm the installation of XHARPy, aborting.")
        return
      distros = wsl_adapter.get_wsl_distro_list()
      if len(distros) == 0:
        olx.Alert("No WSL Distros found", """Please install a WSL Distro first!
For example using 'wsl --install' in a PowerShell prompt.""", "O", False)
        return
      distro = OV.GetParam('snum.NoSpherA2.distro')
      if distro == "Select Distro to use<-None" and wsl_adapter.is_windows:
        print("No WSL Distro selected.")
        print("Available Distros: ", distros)
        print("Please select a WSL Distro using spy.SetParam(snum.NoSpherA2.distro, <distro_name>).")
        return
      wsl_adapter.copy_from_possible_wsl(script, "~/XHARPy.sh")
      print("Installing XHARPy in WSL Distro: ", distro)
      print("This will take a while, please be patient.")
      wsl_adapter.call_command("bash -i -c '~/XHARPy.sh -y'")
      NoSpherA2_instance.softwares.replace("Get XHARPy", "XHARPy")
      OV.SetParam('snum.NoSpherA2.source', "XHARPy")
      olex.m("html.Update()")

  elif input == "Get Psi4":
    wsl_adapter = NoSpherA2_instance.WSLAdapter
    olex2_folder = OV.BaseDir()
    if wsl_adapter.is_wsl:
      res = olx.Alert("Please confirm", """Do you want to automatically install Psi4 using conda?
This will use conda/micromamba to install a virtual environment with Psi4 in your user folder!
OlexSys and the Olex2-Team do not take any responsibility for damage done to your installation from this action.""", "YCQ")
      if res != "Y":
        print("User did not confirm the installation of Psi4, aborting.")
        return
      distros = wsl_adapter.get_wsl_distro_list()
      if len(distros) == 0 and not wsl_adapter.is_windows:
        olx.Alert("No WSL Distros found", """Please install a WSL Distro first!
For example using 'wsl --install' in a PowerShell prompt.""", "O", False)
        return
      distro = OV.GetParam('snum.NoSpherA2.distro', "Ubuntu")
      if distro == "Select Distro to use<-None" and wsl_adapter.is_windows:
        print("No WSL Distro selected.")
        print("Available Distros: ", distros)
        print("Please select a WSL Distro using spy.SetParam(snum.NoSpherA2.distro, <distro_name>).")
        return
      elif wsl_adapter.is_windows:
        print("Installing Psi4 in WSL Distro: ", distro)
      print("This will take a while, please be patient.")
      wsl_adapter.call_command("bash -i -c 'micromamba create -y -n psi4 psi4 python=3.12 -c conda-forge/label/libint_dev -c conda-forge'")
      NoSpherA2_instance.softwares.replace("Get Psi4", "Psi4")
      OV.SetParam('snum.NoSpherA2.source', "Psi4")
      olex.m("html.Update()")
  else:
    OV.SetParam('snum.NoSpherA2.source',input)
    _ = olx.html.GetItemState('h3-NoSpherA2-extras')
    if _ == "0":
      OV.setItemstate("h3-NoSpherA2-extras 2")
      OV.setItemstate("h3-NoSpherA2-extras 1")  # This is a hack to force the update of the GUI without doing all of html
    if input != OV.GetParam('user.NoSpherA2.discamb_exe') and input != "Thakkar IAM":
      ne, adapter = calculate_number_of_electrons()
      mult = int(OV.GetParam('snum.NoSpherA2.multiplicity'))
      if mult == 0:
        if (ne % 2 == 0):
          OV.SetParam('snum.NoSpherA2.multiplicity',1)
        elif (ne % 2 != 0):
          OV.SetParam('snum.NoSpherA2.multiplicity',2)
OV.registerFunction(change_tsc_generator,False,'NoSpherA2')

def set_default_cpu_and_mem():
  import math
  import multiprocessing
  parallel = OV.GetVar("Parallel")
  max_cpu = multiprocessing.cpu_count()
  hyperthreading = OV.GetParam('user.refinement.has_HT')
  if not hyperthreading:
    max_cpu /= 2
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
  if not update:
    OV.SetParam('snum.NoSpherA2.ncpus',str(int(tf_cpu)))
  OV.SetParam('snum.NoSpherA2.mem', str(tf_mem))
OV.registerFunction(set_default_cpu_and_mem,False,'NoSpherA2')

def toggle_GUI():
  if OV.IsNoSpherA2():
    OV.SetParam('snum.NoSpherA2.use_aspherical', False)
    OV.SetParam('snum.NoSpherA2.Calculate',False)
  else:
    OV.SetParam('snum.NoSpherA2.use_aspherical', True)
    set_default_cpu_and_mem()
  if OV.HasGUI():
    olx.html.Update()
OV.registerFunction(toggle_GUI,False,'NoSpherA2')

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

def run_psi4():
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
#OV.registerFunction(psi4, False, "NoSpherA2")

NoSpherA2_instance = NoSpherA2()
OV.registerFunction(NoSpherA2_instance.available, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.launch, False, "NoSpherA2")
#OV.registerFunction(NoSpherA2_instance.delete_f_calc_f_obs_one_h, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getBasisListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getCPUListStr, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.get_SALTED_model_locations, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.getwfn_softwares, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.disable_relativistics, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.wipe_wfn_jobs_folder, False, "NoSpherA2")
OV.registerFunction(NoSpherA2_instance.get_distro_list, False, "NoSpherA2")

def hybrid_GUI():
  t = make_hybrid_GUI(NoSpherA2_instance.getwfn_softwares())
  return t
OV.registerFunction(hybrid_GUI, False, "NoSpherA2")

def get_NoSpherA2_instance():
  return NoSpherA2_instance
#print "OK."
