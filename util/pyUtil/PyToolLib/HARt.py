import os
import sys
import olx
import olex

from olexFunctions import OlexFunctions
OV = OlexFunctions()


class Job(object):
  def __init__(self, parent, folder):
    self.parent = parent
    self.folder = folder
    self.status = 0
    self.name = ""
    self.options = {}
    for k,v in HARt.options.iteritems():
      self.options[k] = olx.GetVar(k, v)

  def save(self):
    with open(os.path.join(self.folder, self.folder, "options.txt"), "w") as f:
      for k, v in self.options:
        f.writeln("%s: %s" %(k, v))


class HARt(object):
  options = {
    "settings.tonto.HAR.basis.name": "def2-SVP",
    "settings.tonto.HAR.method": "rks",
    "settings.tonto.HAR.hydrogens": "positions+Uaniso",
    "settings.tonto.HAR.extinction.refine": "True",
    "settings.tonto.HAR.convergence.value": "0.0001",
    "settings.tonto.HAR.cluster.radius": "8",
    "settings.tonto.HAR.intensity_threshold.value": "3",
  }

  def __init__(self):
    self.job_dir = os.path.join(olx.DataDir(), "jobs")
    if sys.platform[:3] == 'win':
      self.exe = olx.file.Which("har.exe")
    else:
      self.exe = olx.file.Which("har")
    self.set_defaults()

  def set_defaults(self):
    for k,v in self.options.iteritems():
      olx.SetVar(k, v)

  def launch(self):
    pass

  def list_jobs(self):
    jobs = []
    for j in os.listdir(self.job_dir):
      if os.path.isdir(j):
        jobs.append(j)

    rv = "<table>"
    for i in range(5):
      rv += "<tr><td>XX</td><td>some time</td></tr>"
    return rv + "</table>"

  def view_all(self):
    olx.Shell(self.job_dir)

  def available(self):
    return os.path.exists(self.exe)


x = HARt()
OV.registerFunction(x.available, False, "tonto.HAR")
OV.registerFunction(x.list_jobs, False, "tonto.HAR")
OV.registerFunction(x.view_all, False, "tonto.HAR")
OV.registerFunction(x.launch, False, "tonto.HAR")
