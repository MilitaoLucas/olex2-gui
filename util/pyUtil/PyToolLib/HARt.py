import os
import sys
import olx
import olex
#import subprocess
import shutil
import time

from olexFunctions import OlexFunctions
OV = OlexFunctions()


class Job(object):
  def __init__(self, parent, name):
    self.parent = parent
    self.status = 0
    self.name = name
    full_dir = os.path.join(parent.jobs_dir, self.name)
    self.full_dir = full_dir
    if not os.path.exists(full_dir):
      return
    self.date = os.path.getctime(full_dir)
    self.result_fn = os.path.join(full_dir, name) + ".cryst-asymm-unit.cif"
    self.error_fn = os.path.join(full_dir, name) + ".err"
    self.out_fn = os.path.join(full_dir, name) + ".out"
    self.dump_fn = os.path.join(full_dir, "hart.exe.stackdump")
    self.analysis_fn = os.path.join(full_dir, "stdout.fit_analysis")
    self.completed = os.path.exists(self.result_fn)
    self.full_dir = full_dir
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

    if os.path.exists(self.full_dir):
      if olx.Alert("Please confirm",\
"""This directory already exists. All data will be deleted. Continue?""", "YN", False) == 'N':
        return
      import shutil
      try:
        shutil.rmtree(self.full_dir)
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

    model_file_name = os.path.join(self.parent.jobs_dir, self.name, self.name) + ".cif"
    olx.Kill("$Q")
    #olx.Grow()
    olx.File(model_file_name)

    data_file_name = os.path.join(self.parent.jobs_dir, self.name, self.name) + ".hkl"
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
    args = [self.parent.exe, self.name+".cif",
            "-basis-dir", self.parent.basis_dir,
             "-shelx-f2", self.name+".hkl"]
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

    os.environ['hart_cmd'] = '+&-'.join(args)
    os.environ['hart_file'] = self.name
    os.environ['hart_dir'] = self.full_dir
    from subprocess import Popen
    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      retur
    Popen([pyl,
           os.path.join(olx.BaseDir(), "util", "pyUtil", "PyToolLib", "HARt-launch.py")])


class HARt(object):
  options = {
    "settings.tonto.HAR.basis.name": ("def2-SVP", "basis"),
    "settings.tonto.HAR.method": ("rhf", "scf"),
    "settings.tonto.HAR.hydrogens": ("positions+Uaniso",),
    "settings.tonto.HAR.extinction.refine": ("False", "extinction"),
    "settings.tonto.HAR.convergence.value": ("0.0001", "dtol"),
    "settings.tonto.HAR.cluster.radius": ("0", "cluster-radius"),
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
    self.jobs = []
    for j in os.listdir(self.jobs_dir):
      fp  = os.path.join(self.jobs_dir, j)
      jof = os.path.join(fp, "job.options")
      if os.path.isdir(fp) and os.path.exists(jof):
        self.jobs.append(Job(self, j))
    sorted(self.jobs, key=lambda s: s.date)
    rv = "<b>Recent jobs</b> (<a href=\"spy.tonto.HAR.view_all()\">View all jobs</a>)<br>"
    rv += '''
    <table>
      <tr>
        <th width='30%' align='left'>Job name</th>
        <th width='19%' align='left'>Time</th>
        <th width='14%' align='center'>Status</th>
        <th width='12%' align='center'>ERR</th>
        <th width='12%' align='center'>DUMP</th>
        <th width='14%' align='center'>Analysis</th></tr>'''

    status_running = "<font color='%s'><b>Running</b></font>" %OV.GetParam('gui.orange')
    status_completed = "<font color='%s'><b>Finished</b></font>" %OV.GetParam('gui.green')
    status_error = "<font color='%s'><b>Error!</b></font>" %OV.GetParam('gui.red')
    status_stopped = "<font color='%s'><b>Stopped</b></font>" %OV.GetParam('gui.red')
    status_nostart = "<font color='%s'><b>No Start</b></font>" %OV.GetParam('gui.red')

    for i in range(len(self.jobs)):
      OUT_file = self.jobs[i].out_fn

      try:
        if not os.path.exists(OUT_file):
          status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_nostart)
        else:
          os.rename(OUT_file, "_.txt")
          os.rename("_.txt", OUT_file)
          status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_stopped)
      except:
        status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_running)

      error = "--"
      if os.path.exists(self.jobs[i].error_fn):
        _ = os.stat(self.jobs[i].error_fn).st_size == 0
        if _:
          error = "--"
        else:
          error = "<a target='Open .err file' href='exec -o getvar(defeditor) %s'>ERR</a>" %self.jobs[i].error_fn
          status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_error)

      dump = "--"
      if os.path.exists(self.jobs[i].dump_fn):
        dump = "<a target='Open .dump file' href='exec -o getvar(defeditor) %s'>DUMP</a>" %self.jobs[i].dump_fn
        status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_error)

      analysis = "--"
      if os.path.exists(self.jobs[i].analysis_fn):
        analysis = "<a target='Open analysis file' href='exec -o getvar(defeditor) %s>>spy.tonto.HAR.getAnalysisPlotData(%s)'>Open</a>" %(
          self.jobs[i].analysis_fn, self.jobs[i].analysis_fn)
        status = "<a target='Open .out file' href='exec -o getvar(defeditor) %s'>%s</a>" %(self.jobs[i].out_fn, status_completed)

      ct = time.strftime("%b %d %H:%M", time.localtime(self.jobs[i].date))

      if os.path.exists(self.jobs[i].result_fn):
        rv += "<tr><td><a href='reap \"%s\"'>%s</a></td><td>%s</td><td align='center'>%s</td><td align='center'>%s</td><td align='center'>%s</td><td align='center'>%s</td></tr>" %(self.jobs[i].result_fn, self.jobs[i].name, ct, status, error, dump, analysis)
      else:
        rv += "<tr><td>%s</td><td>%s</td><td align='center'>%s</td><td align='center'>%s</td><td align='center'>%s</td><td align='center'>%s</td></tr>" %(self.jobs[i].name, ct, status, error, dump, analysis)

    return rv + "</table>"

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
    (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','A1'),
    (r'Scatter plot of Delta F \= \(Fexp\-Fpred\) vs sin\(theta\)\/lambda \:\n\n(.*?)(?:\n\n|\Z)','A2'),
    (r'Scatter plot of F_z \= \(Fexp\-Fpred\)\/F_sigma vs Fexp \:\n\n(.*?)(?:\n\n|\Z)','A3'),
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


x = HARt()
OV.registerFunction(x.available, False, "tonto.HAR")
OV.registerFunction(x.list_jobs, False, "tonto.HAR")
OV.registerFunction(x.view_all, False, "tonto.HAR")
OV.registerFunction(x.launch, False, "tonto.HAR")
OV.registerFunction(x.getBasisListStr, False, "tonto.HAR")
OV.registerFunction(getAnalysisPlotData, False, "tonto.HAR")
OV.registerFunction(makePlotlyGraph, False, "tonto.HAR")
