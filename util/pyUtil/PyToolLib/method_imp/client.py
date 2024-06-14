from Method import Method_refinement, Method_solution
import phil_interface
from olexFunctions import OV

import olx
import olex
import os

import subprocess, socket, time

class Method_client_refinement(Method_refinement):
  def __init__(self):
    phil_object = phil_interface.parse("""
      name = 'Remote refinement execution'
      .type=str""")

    super(Method_client_refinement, self).__init__(phil_object)

  def send_cmd(self, host, port, cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      try:
        s.connect((host, port))
        s.sendall(cmd)
        return s.recv(1024)
      except ConnectionRefusedError as ex:
        return None

  def pre_refinement(self, RunPrgObject):
    Method_refinement.pre_refinement(self, RunPrgObject)
    host = OV.GetParam("user.Server.host")
    port = OV.GetParam("user.Server.port")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      try:
        s.connect((host, port))
        s.sendall(b"status\n")
        data = s.recv(1024).decode("utf-8").rstrip('\n')
        print(f"Received {data}")
        while data == "busy":
          time.sleep(0.5)
          s.sendall(b"status\n")
          data = s.recv(1024).decode("utf-8").rstrip('\n')
          print(f"Received {data}")

        if data == "ready":
          print("Using Olex2 server on %s" %port)
      except ConnectionRefusedError as ex:
        print("Launching Olex2 server...")
        cd = os.curdir
        os.chdir(olx.BaseDir())
        my_env = os.environ.copy()
        if "OLEX2_ATTACHED_WITH_PYDEBUGGER" in my_env:
          del my_env["OLEX2_ATTACHED_WITH_PYDEBUGGER"]
        subprocess.Popen([os.path.join(olx.BaseDir(), "olex2c.dll"), "server", str(port)],
                        env=my_env)
        os.chdir(cd)

  def read_log_markup(self, log, marker):
    rv = []
    txt = log.readline()
    while txt:
      txt = txt.rstrip("\n\r")
      if txt == marker:
        break
      else:
        rv.append(txt)
      txt = log.readline()
    return rv

  def read_log(self, log):
    while True:
      out = log.readline()
      if not out:
        break
      out = out.rstrip("\r\n")
      if out:
        if out.startswith(">>>") and out.endswith("<<<"):
          marker = out[3:-3]
          txt = self.read_log_markup(log, f"<<<{marker}>>>")
          if marker == "info":
            continue
          if marker in ("error", "warning", "exception"):
            olx.Echo('\n'.join(txt), m="error")
          else:
            print('\n'.join(txt))
        else:
          print(out)

  def do_run(self, RunPrgObject):
    host = OV.GetParam("user.Server.host")
    port = OV.GetParam("user.Server.port")
    log_fn = os.path.join(OV.StrDir(), "olex2.refine_srv.log")
    inp_fn = os.path.join(RunPrgObject.filePath, RunPrgObject.original_filename)
    cmds = ["run:",
            "xlog:%s" %log_fn,
            #"spy.DebugInVSC",
            "SetVar olex2.remote_mode true",
            "spy.SetParam user.refinement.client_mode False",
            "SetOlex2RefinementListener(True)",
            "reap '%s.ins' -no_save=true" %inp_fn,
            "spy.ac.diagnose",
            "refine",
            #"spy.saveHistory",
            "@close",
            ]
    data = self.send_cmd(host=host, port=port, cmd='\n'.join(cmds).encode()).decode("utf-8").rstrip('\n')
    print(f"Received {data}")
    data = "busy"
    with open(log_fn, "r") as log:
      while data == "busy":
        self.read_log(log)
        time.sleep(0.5)
        data = self.send_cmd(host=host, port=port, cmd=b"status\n")
        olx.Refresh()
        if data is None:
          break
        data = data.decode("utf-8").rstrip('\n')
      self.read_log(log)

  def post_refinement(self, RunPrgObject):
    from variableFunctions import set_params_from_ires
    set_params_from_ires()
    OV.SetVar('cctbx_R1', OV.GetParam('snum.refinement.last_R1', -1))
    OV.SetVar('cctbx_wR2', OV.GetParam('snum.refinement.last_wR2', -1))

  def writeRefinementInfoForGui(self, cif):
    pass

  def runAfterProcess(self, RPO):
    res_file = os.path.join(RPO.filePath, RPO.curr_file)+".res"
    if os.path.exists(res_file):
      olex.f("run(@reap '%s'>>spy.loadHistory>>html.Update)" %res_file)
