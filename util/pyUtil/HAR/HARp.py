
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

class HARp(PT):
  def __init__(self):
    super(HARp, self).__init__()
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
    
    # END Generated =======================================
    options = {
      "settings.tonto.HAR.basis.name": ("x2c-SVPall", "basis"),
      "settings.tonto.HAR.method": ("rhf", "scf"),
      "settings.tonto.HAR.hydrogens": ("anisotropic",),
      "settings.tonto.HAR.extinction.refine": ("False", "extinction"),
      "settings.tonto.HAR.convergence.value": ("0.0001", "dtol"),
      "settings.tonto.HAR.cluster.radius": ("0", "cluster-radius"),
      "settings.tonto.HAR.intensity_threshold.value": ("3", "fos"),
      "settings.tonto.HAR.dispersion": ("false",),
      "settings.tonto.HAR.autorefine": ("true",),
      "settings.tonto.HAR.autogrow": ("true",),
      "settings.tonto.HAR.cluster-grow": ("true",),
    }
    self.options = options

    self.jobs_dir = OV.GetParam('%s.har_job_path' %self.p_scope)
   # self.jobs_dir = os.path.join(olx.DataDir(), "HAR_jobs")
    if not os.path.exists(self.jobs_dir):
      os.mkdir(self.jobs_dir)

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

    self.set_defaults()

  def sort_out_HA_options(self):
    # We are asking to just get form factors to disk
    #self.options["settings.tonto.HAR.ncpus"] = (self.max_cpu,)
    self.options["settings.tonto.HAR.autorefine"] = (False,)
    self.options["settings.tonto.HAR.autogrow"] = (False,)
    self.options["settings.tonto.HAR.cluster-grow"] = (False,)
    olx.SetVar("settings.tonto.HAR.autorefine", False) 
    #olx.SetVar("settings.tonto.HAR.ncpus", self.max_cpu) 
    tsc_source = OV.GetParam('snum.refinement.cctbx.nsff.tsc.source')
    
    if tsc_source == "Tonto":
      # We want these from a wavefunction calculation using TONTO """

      delete_ks = ["settings.tonto.HAR.hydrogens",
          "settings.tonto.HAR.extinction.refine",
          "settings.tonto.HAR.convergence.value",
          "settings.tonto.HAR.intensity_threshold.value",
          ]
    elif tsc_source.lower().endswith(".fchk"):
      # We want these from supplied fchk file """

      delete_ks = ["settings.tonto.HAR.basis.name", 
          "settings.tonto.HAR.method",
          "settings.tonto.HAR.hydrogens",
          "settings.tonto.HAR.extinction.refine",
          "settings.tonto.HAR.convergence.value",
          "settings.tonto.HAR.cluster.radius",
          "settings.tonto.HAR.dispersion",
          "settings.tonto.HAR.intensity_threshold.value",
          ]
    else:
      # We want to calculate a wavefunction on our own using the supllied code """
      
      delete_ks = ["settings.tonto.HAR.basis.name", 
          "settings.tonto.HAR.method",
          "settings.tonto.HAR.hydrogens",
          "settings.tonto.HAR.extinction.refine",
          "settings.tonto.HAR.convergence.value",
          "settings.tonto.HAR.cluster.radius",
          "settings.tonto.HAR.dispersion",
          "settings.tonto.HAR.intensity_threshold.value",
          ]
    for k in delete_ks:
      if self.options.has_key(k):
        self.options.pop(k)

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
      print """
      Number of CPUs Detected for parallel calculations: """ + str(max_cpu)
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


  def set_defaults(self):
    for k,v in self.options.iteritems():
      olx.SetVar(k, v[0])

  def launch(self, job_type):
    
    self.job_type = job_type
    calculate = OV.GetParam('snum.refinement.cctbx.nsff.tsc.Calculate')
    if not calculate:
      if self.job_type.lower() == "nsff":
        return
    if not self.basis_list_str:
      print("Could not locate usable HARt executable")
      return
    
    self.setup_har_executables()
    
    job = Job(self, olx.FileName())
    
    if self.job_type.lower() == "nsff":
      wfn_code = OV.GetParam('snum.refinement.cctbx.nsff.tsc.source')
      if wfn_code.lower().endswith(".fchk"):
        OV.SetParam('snum.refinement.cctbx.nsff.tsc.fchk_file',olx.FileName() + ".fchk")
      elif wfn_code == "Tonto":
        pass
      else:
        OV.SetParam('snum.refinement.cctbx.nsff.tsc.fchk_file',olx.FileName() + ".fchk")
        self.wfn() # Produces Fchk file in all cases that are not fchk or tonto directly
      self.sort_out_HA_options()
    
    job.launch()
    olx.html.Update()
    if self.job_type.lower() == "nsff":
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

  def list_jobs(self):
    import shutil
    d = {}
    self.jobs = []

    for j in os.listdir(self.jobs_dir):
      fp  = os.path.join(self.jobs_dir, j)
      jof = os.path.join(fp, "job.options")
      #check if job has an options file and append it to the jobs array
      new = True
      if os.path.isdir(fp) and os.path.exists(jof):
        for r in range(len(self.jobs)):
          if self.jobs[r].name == j:
            new = False
        if new:
          self.jobs.append(Job(self, j))
    #cross check, whether all jobs in the list are still valid files, if yes load the job
    for j in range(len(self.jobs)):
      if os.path.exists(os.path.join(self.jobs_dir, self.jobs[j].name,"job.options")):
        self.jobs[j].load_origin()

    sorted(self.jobs, key=lambda s: s.date)
    rv = get_template('table_header', path=p_path)

#    status_running = "<font color='%s'><b>Running</b></font>" %OV.GetParam('gui.orange')
    d['processing_gif_src'] = os.path.join(self.p_path, OV.GetParam('harp.processing_gif'))
    status_running = get_template('processing_gif')%d
    d['back_picture_src'] = os.path.join(self.p_path, OV.GetParam('harp.back_arrow'))
    load_input = "<table cellspacing='1' cellpadding='0' width='100%%'><tr><td align='center'><img src='%(back_picture_src)s', width='45%%'></td></tr></table>"%d

    status_completed = "<font color='%s'><b>Finished</b></font>" %OV.GetParam('gui.green')
    status_error = "<font color='%s'><b>Error!</b></font>" %OV.GetParam('gui.red')
    status_stopped = "<font color='%s'><b>Stopped</b></font>" %OV.GetParam('gui.red')
    status_nostart = "<font color='%s'><b>No Start</b></font>" %OV.GetParam('gui.red')

    is_anything_running = False
    for i in range(len(self.jobs)):
      OUT_file = self.jobs[i].out_fn
      if os.path.exists(os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_HAR.cif")):
        self.jobs[i].is_copied_back = True
      else:
        self.jobs[i].is_copied_back = False

      try:
        if not os.path.exists(OUT_file):
          olx.wait(500) #Why is this here?

          status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_nostart)
        else:
          os.rename(OUT_file, "_.txt")
          os.rename("_.txt", OUT_file)
          status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_stopped)
      except:
        status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_running)
        is_anything_running = True

      error = "--"
      if os.path.exists(os.path.join(self.jobs_dir, self.jobs[j].name,".err")):
        if 'Error in' in open(os.path.join(self.jobs_dir, self.jobs[j].name,".err")).read():
          _ = False
        else:
          _ = True
        if _:
          error = "--"
        else:
          error = "<a target='Open .err file' href='exec -o getvar(defeditor) %s'>ERR</a>" %self.jobs[i].error_fn
          status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_error)
      if self.jobs[i].is_copied_back:
        input_structure = os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_input.cif")
      else:
        input_structure = os.path.join(self.jobs[i].full_dir, self.jobs[i].name + ".cif")
      arrow = """<a target='Open input .cif file: %s' href='reap "%s"'>%s</a>""" %(input_structure, input_structure, load_input)

      analysis = "--"
      if os.path.exists(os.path.join(self.jobs[i].full_dir, "stdout._Delta_F_vs_stl")):
        try:
          analysis = "<a target='Open analysis file' href='exec -o getvar(defeditor) %s>>spy.tonto.HAR.getAnalysisPlotData(%s)'>Open</a>" %(
            self.jobs[i].analysis_fn, self.jobs[i].analysis_fn)
          if 'WARNING: refinement stopped: chi2 has increased.' in open(self.jobs[i].out_fn).read():
            error = "<a target='Open .err file' href='exec -o getvar(defeditor) %s'>Chi2</a>" %self.jobs[i].error_fn
            status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_error)
          elif 'Structure refinement converged.' in open(self.jobs[i].out_fn).read():
            status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_completed)
            if self.jobs[i].is_copied_back == False:
              try:
                shutil.copy(os.path.join(self.jobs[i].full_dir, self.jobs[i].name + ".cif"), os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_input.cif"))
                shutil.copy(os.path.join(self.jobs[i].full_dir, self.jobs[i].name + ".archive.cif"), os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_HAR.cif"))
                self.jobs[i].result_fn = os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_HAR.cif")
                shutil.copy(os.path.join(self.jobs[i].full_dir, self.jobs[i].name + ".archive.fcf"), os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_HAR.fcf"))
                shutil.copy(os.path.join(self.jobs[i].full_dir, self.jobs[i].name + ".archive.fco"), os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_HAR.fco"))
                shutil.copy(os.path.join(self.jobs[i].full_dir, self.jobs[i].name + ".out"), os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_HAR.out"))
                self.jobs[i].out_fn = os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + ".out")
#                shutil.copy(os.path.join(self.jobs[i].full_dir, "stdout.fit_analysis"), os.path.join(self.jobs[i].origin_folder, "stdout.fit_analysis"))
                self.jobs[i].analysis_fn = os.path.join(self.jobs[i].origin_folder, "stdout.fit_analysis")
                har_cif = os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_HAR.cif")
                if not os.path.exists(har_cif):
                  print "The file %s does not exist. It doesn't look like HAR has been run here." %har_cif
                  return
                iam_cif = os.path.join(self.jobs[i].origin_folder, self.jobs[i].name.rstrip("_HAR") + ".cif") 
                if not os.path.exists(iam_cif):
                  print "The file %s does not exist. It doesn't look a CIF file for the IAM refinement exists" %iam_cif
                  return
                
                hkl_stats = olex.core.GetHklStat()
                OV.set_cif_item('_diffrn_measured_fraction_theta_full', "%.3f" %hkl_stats.get('Completeness'))
                OV.set_cif_item('_diffrn_reflns_av_unetI/netI', "%.3f" %hkl_stats.get('MeanIOverSigma'))
                OV.set_cif_item('_diffrn_reflns_av_R_equivalents', "%.3f" %hkl_stats.get('Rint'))
                olex.m("cifmerge")
                olex.m("cifmerge '%s' '%s'" %(iam_cif, har_cif)) 
                self.jobs[i].is_copied_back = True
              except:
                print "Something went wrong during copying back the results of job %s" %self.jobs[i].name
                continue
            else:
              self.jobs[i].result_fn = os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + "_HAR.cif")
              self.jobs[i].out_fn = os.path.join(self.jobs[i].origin_folder, self.jobs[i].name + ".out")
              self.jobs[i].analysis_fn = os.path.join(self.jobs[i].origin_folder, "stdout.fit_analysis")
          else:
            error = "<a target='Open .err file' href='exec -o getvar(defeditor) %s'>Conv</a>" %self.jobs[i].error_fn
            status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_stopped)
        except:
          continue

      d['job_result_filename'] = self.jobs[i].result_fn
      d['job_result_name'] = self.jobs[i].name
      d['ct'] = time.strftime("%b %d %H:%M", time.localtime(self.jobs[i].date))
      d['status'] = status
      d['error'] = error
      d['arrow'] = arrow
      d['analysis'] = analysis
      del_file = self.jobs[i].full_dir
      d['delete'] = del_button = GI.get_action_button_html('delete', "spy.tonto.har.del_dir(%s)>>html.Update"%del_file, "Delete this HAR refinement")

      if os.path.exists(self.jobs[i].result_fn):
        d['link'] = '''
<input
  type="button"
  name="%(job_result_name)s"
  value="%(job_result_name)s"
  width="100%%"
  onclick="reap '%(job_result_filename)s'"
>''' %d
        #  onclick="reap '%(job_result_filename)s'>>calcFourier -diff -fcf -r=0.05 -m"


      else:
        d['processing_gif_src'] = os.path.join(self.p_path, OV.GetParam('harp.processing_gif'))
        d['link'] = get_template('processing_gif')%d
        d['link'] = get_template('processing_started')%d

      rv += get_template('job_line')%d
    rv += "</table>"
    rv += get_template('recent_jobs', path=p_path)
    if is_anything_running:
      self.auto_reload()

    return rv

  def auto_reload(self):
    interval = OV.GetParam('harp.check_output_interval',0)
    if interval:
      olx.Schedule(interval, 'html.Update')

  def view_all(self):
    olx.Shell(self.jobs_dir)

  def available(self):
    return os.path.exists(self.exe)

  def getAnalysisPlotData(input_f):
    f = open(input_f, 'r').read()
    d = {}
    import re

    regex_l = [
      (r'Labelled QQ plot\:\n\n(.*?)(?:\n\n|\Z)','QQ'),
      (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','Fz vs sin(theta)/lambda'),
      (r'Scatter plot of Delta F \= \(Fexp\-Fpred\) vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','Delta Fz vs sin(theta)/lambda'),
      (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs Fexp \:\n\n(.*?)(?:\n\n|\Z)','Fz vs Fexp'),
    ]


    for regex_t,name in regex_l:
      regex = re.compile(regex_t, re.DOTALL)
      xs = []
      ys = []
      text = []
      m=regex.findall(f)
      if m:
        mm = ""
        for _ in m:
          if len(_) < 10:
            continue
          else:
            mm = _
        if not mm:
          print "No Data"
          continue
        raw_data = mm.strip()
        raw_data = raw_data.split("\n")
        for pair in raw_data:
          pair = pair.strip()
          if not pair:
            continue
          xs.append(float(pair.split()[0].strip()))
          ys.append(float(pair.split()[1].strip()))
          try:
            text.append("%s %s %s" %(pair.split()[2], pair.split()[3], pair.split()[4]))
          except:
            text.append("")
        d[name] = {}
        d[name].setdefault('title', name)
        d[name].setdefault('xs', xs)
        d[name].setdefault('ys', ys)
        d[name].setdefault('text', text)
      else:
        print "Could not evaluate REGEX %s." %repr(regex_t)


    makePlotlyGraph(d)

  def makePlotlyGraph(d):

    try:
      import plotly
      print plotly.__version__  # version >1.9.4 required
      from plotly.graph_objs import Scatter, Layout
      import numpy as np
      import plotly.plotly as py
      import plotly.graph_objs as go
    except:
      print "Please install plot.ly for python!"
      return

    data = []
    print len(d)
    for trace in d:
      _ = go.Scatter(
        x = d[trace]['xs'],
        y = d[trace]['ys'],
        text = d[trace]['text'],
        mode = 'markers',
        name = d[trace]['title']
        )
      data.append(_)

      layout = go.Layout(
          title='HAR Result',
          xaxis=dict(
              title='x Axis',
              titlefont=dict(
                  family='Courier New, monospace',
                  size=18,
                  color='#7f7f7f'
              )
          ),
          yaxis=dict(
              title='y Axis',
              titlefont=dict(
                  family='Courier New, monospace',
                  size=18,
                  color='#7f7f7f'
              )
          )
      )


    fig = go.Figure(data=data, layout=layout)
    plot_url = plotly.offline.plot(fig, filename='basic-line')

def getAnalysisPlotData(input_f):
  f = open(input_f, 'r').read()
  d = {}
  import re

  regex_l = [
    (r'Labelled QQ plot\:\n\n(.*?)(?:\n\n|\Z)','QQ'),
    (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','Fz vs sin(theta)/lambda'),
    (r'Scatter plot of Delta F \= \(Fexp\-Fpred\) vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','Delta Fz vs sin(theta)/lambda'),
    (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs Fexp \:\n\n(.*?)(?:\n\n|\Z)','Fz vs Fexp'),
  ]


  for regex_t,name in regex_l:
    regex = re.compile(regex_t, re.DOTALL)
    xs = []
    ys = []
    text = []
    m=regex.findall(f)
    if m:
      mm = ""
      for _ in m:
        if len(_) < 10:
          continue
        else:
          mm = _
      if not mm:
        print "No Data"
        continue
      raw_data = mm.strip()
      raw_data = raw_data.split("\n")
      for pair in raw_data:
        pair = pair.strip()
        if not pair:
          continue
        xs.append(float(pair.split()[0].strip()))
        ys.append(float(pair.split()[1].strip()))
        try:
          text.append("%s %s %s" %(pair.split()[2], pair.split()[3], pair.split()[4]))
        except:
          text.append("")
      d[name] = {}
      d[name].setdefault('title', name)
      d[name].setdefault('xs', xs)
      d[name].setdefault('ys', ys)
      d[name].setdefault('text', text)
    else:
      print "Could not evaluate REGEX %s." %repr(regex_t)


  makePlotlyGraph(d)

def makePlotlyGraph(d):

  try:
    import plotly
    print plotly.__version__  # version >1.9.4 required
    from plotly.graph_objs import Scatter, Layout
    import numpy as np
    import plotly.plotly as py
    import plotly.graph_objs as go
  except:
    print "Please install plot.ly for python!"
    return

  data = []
  print len(d)
  for trace in d:
    _ = go.Scatter(
      x = d[trace]['xs'],
      y = d[trace]['ys'],
      text = d[trace]['text'],
      mode = 'markers',
      name = d[trace]['title']
      )
    data.append(_)

    layout = go.Layout(
        title='HAR Statistics',
        xaxis=dict(
            title='x Axis',
            titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        ),
        yaxis=dict(
            title='y Axis',
            titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        )
    )


  fig = go.Figure(data=data, layout=layout)
  plot_url = plotly.offline.plot(fig, filename='basic-line')

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
    basis_name = olx.GetVar("settings.tonto.HAR.basis.name")
    basis_set_fn = os.path.join(self.parent.basis_dir,olx.GetVar("settings.tonto.HAR.basis.name"))
    basis = open(basis_set_fn,"r")
    chk_destination = "%chk=" + self.name + ".chk"
    if OV.GetParam('snum.refinement.cctbx.nsff.ncpus') != '1':
      cpu = "%nproc=" + OV.GetParam('snum.refinement.cctbx.nsff.ncpus')
    else:
      cpu = "%nproc=1"
    mem = "%mem=" + OV.GetParam('snum.refinement.cctbx.nsff.mem') + "GB"
    if olx.GetVar("settings.tonto.HAR.method", None) == "rhf":
      control = "# rhf/gen NoSymm 6D 10F IOp(3/32=2) formcheck"
    else:
      control = "# b3lyp/gen NoSymm 6D 10F IOp(3/32=2) formcheck"
    com.write(cpu + '\n')
    com.write(mem + '\n')
    com.write(control + '\n')
    com.write(" \n")
    title = "Wavefunction calculation for " + self.name + " on a level of theory of " + olx.GetVar("settings.tonto.HAR.method", None) + "/" + olx.GetVar("settings.tonto.HAR.basis.name")
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
    basis_name = olx.GetVar("settings.tonto.HAR.basis.name")
    basis_set_fn = os.path.join(self.parent.basis_dir,olx.GetVar("settings.tonto.HAR.basis.name"))
    basis = open(basis_set_fn,"r")
    if OV.GetParam('snum.refinement.cctbx.nsff.ncpus') != '1':
      cpu = "nprocs " + OV.GetParam('snum.refinement.cctbx.nsff.ncpus')
    else:
      cpu = "nprocs 1"
    mem = OV.GetParam('snum.refinement.cctbx.nsff.mem')
    mem_value = int(mem) / int(OV.GetParam('snum.refinement.cctbx.nsff.ncpus')) * 1000
    mem = "%maxcore " + str(mem_value)
    if olx.GetVar("settings.tonto.HAR.method", None) == "rhf":
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
    basis_name = olx.GetVar("settings.tonto.HAR.basis.name")
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
      args.append(">")
      args.append(self.name + ".log")
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
    full_dir = os.path.join(parent.jobs_dir, self.name)
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

  def save(self):
    with open(os.path.join(self.full_dir, "job.options"), "w") as f:
      for k, v in HARp_instance.options.iteritems():
        val = olx.GetVar(k, None)
        if val is not None:
          f.write("%s:%s\n" %(k, val))
      f.write("origin_folder:%s" %self.origin_folder)

  def load(self):
    options_fn = os.path.join(self.full_dir, "job.options")
    if os.path.exists(options_fn):
      self.date = os.path.getctime(self.full_dir)
      try:
        with open(options_fn, "r") as f:
          for l in f:
            l = l.strip()
            if not l or ':' not in l: continue
            toks = l.split(':')
            if "origin_folder" != toks[0]:
              olx.SetVar(toks[0], toks[1])
            else:
              if sys.platform[:3] == 'win':
                self.origin_folder = toks[1] + ":" + toks[2]
              else:
                self.origin_folder = toks[1]
        return True
      except:
        return False
    return False

  def load_origin(self):
    options_fn = os.path.join(self.full_dir, "job.options")
    if os.path.exists(options_fn):
      self.date = os.path.getctime(self.full_dir)
      try:
        with open(options_fn, "r") as f:
          for l in f:
            l = l.strip()
            if not l or ':' not in l: continue
            toks = l.split(':')
            if "origin_folder" == toks[0]:
              if sys.platform[:3] == 'win':
                self.origin_folder = toks[1] + ":" + toks[2]
              else:
                self.origin_folder = toks[1]
            else: continue
        return True
      except:
        return False
    return False

  def launch(self):
    import shutil
    #check whether ACTA was set, so the cif contains all necessary information to be copied back and forth

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

#    if not olx.Ins('ACTA'):
#      olex.m('addins ACTA')
#      olex.m('refine')
    autogrow = olx.GetVar("settings.tonto.HAR.autogrow", None)
    if HARp_instance.job_type.lower() == "hart":
      if olx.xf.latt.IsGrown() == 'true':
        if olx.Alert("Please confirm",\
"""This is a grown structure. If you have created a cluster of molecules, make sure
that the structure you see on the screen obeys the crystallographic symmetry.
If this is not the case, the HAR will not work properly.
Make sure the cluster/moelcule is neutral and fully completed.

Continue?""", "YN", False) == 'N':
          return
      elif olx.xf.au.GetZprime() != '1' and autogrow == 'true':
        olex.m("kill $q")
        olx.Grow()
        olex.m("grow -w")
      elif olx.xf.au.GetZprime() < '1' and autogrow == 'false':
        if olx.Alert("Attention!",\
"""This appears to be a z' < 1 structure.
Autogrow is disabled and the structure is not grown.

This is HIGHLY unrecommendet!

Please complete the molecule in a way it forms a full chemical entity.
Benzene would need to contain one complete 6-membered ring to work,
otherwise the wavefunction can not be calculated properly!
Are you sure you want to continue with this structure?""", "YN", False) == 'N':
          return
      autorefine = olx.GetVar("settings.tonto.HAR.autorefine", None)
      if autorefine == 'true':
        olex.m("refine")
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
    self.save()

    if HARp_instance.job_type.lower() == "hart":
      args = [self.name+".cif",
              "-basis-dir", self.parent.basis_dir,
              "-shelx-f2", self.name+".hkl",
              "-hart", "t"
              ]

    else:
      # We are asking to just get form factors to disk
      fchk_source = OV.GetParam('snum.refinement.cctbx.nsff.tsc.source')
      if fchk_source == "Tonto":
        # We want these from a wavefunction calculation using TONTO """
  
        args = [self.name+".cif",
                "-basis-dir", self.parent.basis_dir,
                "-shelx-f2", self.name+".hkl"
                ]
  
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

    for k,v in HARp_instance.options.iteritems():
      val = olx.GetVar(k, None)

      if len(v) == 2:
        if val is not None:
          args.append('-' + v[1])
          args.append(val)
      elif k == 'settings.tonto.HAR.hydrogens':
        if val == 'positions only':
          args.append("-h-adps")
          args.append("f")
        elif val == 'isotropic':
          args.append("-h-adps")
          args.append("f")
          args.append("-h-iso")
          args.append("t")
        elif val == "anisotropic":
          args.append("-h-adps")
          args.append("t")
        elif val == "not":
          args.append("-h-adps")
          args.append("f")
          args.append("-h-pos")
          args.append("f")
        pass
    clustergrow = olx.GetVar("settings.tonto.HAR.cluster-grow", None)
    if clustergrow == 'false':
      args.append("-complete-mol")
      args.append("f")

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
    if not HARp_instance.job_type.lower() == "hart":
      import subprocess
      p = subprocess.Popen([pyl,
             os.path.join(p_path, "HARt-launch.py")])
      while p.poll() is None:
        time.sleep(3)
    else:
      from subprocess import Popen
      Popen([pyl,
        os.path.join(p_path, "HARt-launch.py")])
      
    
def deal_with_har_cif():
  ''' Tries to complete what it can from the existing IAM cif'''
  har_cif = os.path.join(OV.FilePath(), OV.FileName() + ".cif")
  if not os.path.exists(har_cif):
    print "The file %s does not exist. It doesn't look like HAR has been run here." %har_cif
    return
  iam_cif = os.path.join(OV.FilePath(), OV.FileName().rstrip("_HAR") + ".cif") 
  if not os.path.exists(iam_cif):
    print "The file %s does not exist. It doesn't look a CIF file for the IAM refinement exists" %iam_cif
    return
  
  hkl_stats = olex.core.GetHklStat()
  OV.set_cif_item('_diffrn_measured_fraction_theta_full', "%.3f" %hkl_stats.get('Completeness'))
  OV.set_cif_item('_diffrn_reflns_av_unetI/netI', "%.3f" %hkl_stats.get('MeanIOverSigma'))
  OV.set_cif_item('_diffrn_reflns_av_R_equivalents', "%.3f" %hkl_stats.get('Rint'))
  olex.m("cifmerge")
  olex.m("cifmerge '%s' '%s'" %(iam_cif, har_cif)) 
  
OV.registerFunction(deal_with_har_cif)
  
def del_dir(directory):
  import shutil
  shutil.rmtree(directory)

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

HARp_instance = HARp()
OV.registerFunction(HARp_instance.available, False, "tonto.HAR")
OV.registerFunction(HARp_instance.list_jobs, False, "tonto.HAR")
OV.registerFunction(HARp_instance.view_all, False, "tonto.HAR")
OV.registerFunction(HARp_instance.launch, False, "tonto.HAR")
OV.registerFunction(HARp_instance.wfn, False, "tonto.HAR")
OV.registerFunction(HARp_instance.getBasisListStr, False, "tonto.HAR")
OV.registerFunction(HARp_instance.getCPUListStr, False, "tonto.HAR")
OV.registerFunction(HARp_instance.getwfn_softwares, False, "tonto.HAR")
OV.registerFunction(getAnalysisPlotData, False, "tonto.HAR")
OV.registerFunction(makePlotlyGraph, False, "tonto.HAR")
OV.registerFunction(del_dir, False, "tonto.HAR")
OV.registerFunction(sample_folder, False, "tonto.HAR")
#print "OK."