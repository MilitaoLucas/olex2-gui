import os
import sys
import olx
import olex
import subprocess
import shutil

from olexFunctions import OlexFunctions
OV = OlexFunctions()


class Job(object):
  def __init__(self, parent, name):
    self.parent = parent
    self.status = 0
    self.name = name
    full_dir = os.path.join(parent.jobs_dir, self.name)
    if not os.path.exists(full_dir):
      os.mkdir(full_dir)
    self.date = os.path.getctime(full_dir)
    self.result_fn = os.path.join(full_dir, name) + ".accurate.cif"
    self.error_fn = os.path.join(full_dir, name) + ".err"
    self.out_fn = os.path.join(full_dir, name) + ".out"
    self.completed = os.path.exists(self.result_fn)
    initialised = False

  def save(self):
    with open(os.path.join(self.parent.jobs_dir, self.name, "job.options"), "w") as f:
      for k, v in HARt.options.iteritems():
        val = olx.GetVar(k, None)
        if val is not None:
          f.write("%s: %s\n" %(k, val))

  def load(self):
    full_dir = os.pardir.join(parent.jobs_dir, self.name)
    options_fn = os.path.join(full_dir, "job.options")
    if os.path.exists(options_fn):
      self.date = os.path.getctime(full_dir)
      try:
        with open(options_fn, "r") as f:
          for l in f:
            l = l.strip()
            if not l or ':' not in l: continue
            toks = l.split(':')
            olx.SetVar(toks[0], toks[1])
        return True
      except:
        return False
    return False

  def launch(self):
    if olx.xf.latt.IsGrown() == 'true':
      if olx.Alert("Please confirm",\
"""This is a grown structure. If you have created a cluster of molecules, make sure
that the structure you see on the screen obeys the crystallographic symmetry.
If this is not the case, the HAR will not work properly. Continue?""", "YN", False) == 'N':
        return
    elif olx.xf.au.GetZprime() != '1':
      olx.Alert("Please confirm",\
"""This is a  Z' < 1 structure. You have to complete all molecules before you run HARt.""",
     "O", False)
      return
    model_file_name = os.path.join(self.parent.jobs_dir, self.name, self.name) + ".cif"
    olx.Kill("$Q")
    #olx.Grow()
    olx.File(model_file_name)

    self.save()
    args = [self.parent.exe, model_file_name,
            "-basis-dir", self.parent.basis_dir,
             "-shelx-f2", olx.HKLSrc()]
    #print ' '.join(args)
    for k,v in HARt.options.iteritems():
      val = olx.GetVar(k, None)
      if len(v) == 2:
        if val is not None:
          args.append('-' + v[1])
          args.append(val)
      elif k == 'settings.tonto.HAR.hydrogens':
        if k == 'positions only':
          args.append("-h-adps")
          args.append("f")
        elif k == 'positions+Uiso':
          args.append("-h-iso")
          args.append("t")
        else:
          args.append("-h-adps")
          args.append("t")
        pass
    args.append ("pause")
    subprocess.Popen(args)


class HARt(object):
  options = {
    "settings.tonto.HAR.basis.name": ("def2-SVP", "basis"),
    "settings.tonto.HAR.method": ("rks", "scf"),
    "settings.tonto.HAR.hydrogens": ("positions+Uaniso",),
    "settings.tonto.HAR.extinction.refine": ("False", "extinction"),
    "settings.tonto.HAR.convergence.value": ("0.0001", "dtol"),
    "settings.tonto.HAR.cluster.radius": ("8", "cluster-radius"),
    "settings.tonto.HAR.intensity_threshold.value": ("3", "fos"),
  }

  def __init__(self):
    self.jobs_dir = os.path.join(olx.DataDir(), "jobs")
    if not os.path.exists(self.jobs_dir):
      os.mkdir(self.jobs_dir)
    self.jobs = []
    if sys.platform[:3] == 'win':
      self.exe = olx.file.Which("hart.exe")
    else:
      self.exe = olx.file.Which("hart")
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

  def set_defaults(self):
    for k,v in self.options.iteritems():
      olx.SetVar(k, v[0])

  def launch(self):
    if not self.basis_list_str:
      print("Could not locate usable HARt installation")
      return
    j = Job(self, olx.FileName())
    j.launch()
    olx.html.Update()


  def getBasisListStr(self):
    return self.basis_list_str

  def list_jobs(self):
    import time
    self.jobs = []
    for j in os.listdir(self.jobs_dir):
      fp  = os.path.join(self.jobs_dir, j)
      jof = os.path.join(fp, "job.options")
      if os.path.isdir(fp) and os.path.exists(jof):
        self.jobs.append(Job(self, j))
    sorted(self.jobs, key=lambda s: s.date)
    rv = "<b>Recent jobs</b> (<a href=\"spy.tonto.HAR.view_all()\">View all jobs</a>)<br>"
    rv += "<table><tr><th>Job name</th><th>Timestamp</th><th>Status</th><th>Error</th></tr>"
    status_running = "<font color='orange'>Running</font>"
    status_completed = "<font color='green'>Completed</font>"
    status_error = "<font color='red'>Error!</font>"
    for i in range(min(5, len(self.jobs))):
      error = "--"
      if os.path.exists(self.jobs[i].error_fn):
        _ = open(self.jobs[i].error_fn).read().strip()
        if not _:
          error = "--"
        else:
          error = "<a href='exec -o getvar(defeditor) %s'>Error File</a>" %self.jobs[i].error_fn

      ct = time.strftime("%Y/%m/%d %H:%M", time.gmtime(self.jobs[i].date))
      if not self.jobs[i].completed:
        status = "<a href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_running)
        rv += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %(self.jobs[i].name, ct, status, error)
      else:
        if os.path.exists(self.jobs[i].result_fn):
          status = "<a href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_completed)
        else:
          status = "<a href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_error)
        rv += "<tr><td><a href='reap \"%s\"'>%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>" %\
        (self.jobs[i].result_fn, self.jobs[i].name, ct, status, error)
    return rv + "</table>"

  def view_all(self):
    olx.Shell(self.jobs_dir)

  def available(self):
    return os.path.exists(self.exe)


x = HARt()
OV.registerFunction(x.available, False, "tonto.HAR")
OV.registerFunction(x.list_jobs, False, "tonto.HAR")
OV.registerFunction(x.view_all, False, "tonto.HAR")
OV.registerFunction(x.launch, False, "tonto.HAR")
OV.registerFunction(x.getBasisListStr, False, "tonto.HAR")
