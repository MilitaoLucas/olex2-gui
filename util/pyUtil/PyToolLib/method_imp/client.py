from Method import Method_refinement, Method_solution
import phil_interface
from olexFunctions import OV

import olx
import olex
import os, sys

import subprocess, socket, time

class Method_client_refinement(Method_refinement):
  def __init__(self):
    phil_object = phil_interface.parse("""
      name = 'Remote refinement execution'
      .type=str""")

    super(Method_client_refinement, self).__init__(phil_object)

  def send_cmd(self, host, port, cmd, handle=True):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      try:
        s.connect((host, port))
        s.sendall(cmd)
        return s.recv(1024)
      except ConnectionRefusedError as ex:
        if handle:
          return None
        else:
          raise ex
      except OSError as ex: # socket closed?
        if handle:
          return None
        else:
          raise ex

  def pre_refinement(self, RunPrgObject):
    import uuid
    self.job_id = uuid.uuid4().hex
    Method_refinement.pre_refinement(self, RunPrgObject)
    host = OV.GetParam("user.Server.host")
    port = OV.GetParam("user.Server.port")
    debug = OV.GetParam("user.Server.debug")
    share = OV.GetParam("user.Server.shared_localhost")
    # flush settings
    from variableFunctions import SaveOlex2Params, SaveUserParams
    SaveOlex2Params()
    SaveUserParams()
    try:
        reserve_ = ("reserve:%s\n" %self.job_id).encode()
        data = self.send_cmd(host, port, reserve_, handle=False).decode("utf-8").rstrip('\n')
        print(f"Received {data}")
        bmp_created = False
        bmp_name = "Server is busy"
        while data == "busy":
          if not share:
            port += 1
            data = self.send_cmd(host, port, reserve_, handle=False).decode("utf-8").rstrip('\n')
            continue
          if not bmp_created:
            OV.CreateBitmap(bmp_name)
            bmp_created = True
          time.sleep(1)
          olx.Refresh()
          data = self.send_cmd(host, port, reserve_, handle=True).decode("utf-8").rstrip('\n')
        if bmp_created:
          OV.DeleteBitmap(bmp_name)
        if data == "ready":
          print("Using Olex2 server on %s" %port)
        OV.SetVar("server.port", str(port))
    except ConnectionRefusedError as ex:
      if host != "localhost":
        raise Exception("No running server found!")
      print("Launching Olex2 server...")
      cd = os.curdir

      os.chdir(olx.BaseDir())
      my_env = os.environ.copy()
      if "OLEX2_ATTACHED_WITH_PYDEBUGGER" in my_env and debug != "Wing":
        del my_env["OLEX2_ATTACHED_WITH_PYDEBUGGER"]
      headless_name = "olex2c"
      if sys.platform[:3] == 'win':
        headless_name += ".dll"
      elif sys.platform == 'darwin':
        headless_name += "_exe"
      subprocess.Popen(
        [os.path.join(olx.BaseDir(), headless_name), "server", str(port), self.job_id],
        env=my_env)
      os.chdir(cd)
      OV.SetVar("server.port", str(port))
      launched = OV.GetVar("launched_server.ports", "")
      if launched:
        launched += ",%s" %port
      else:
        launched = str(port)
      OV.SetVar("launched_server.ports", launched)

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
            olx.Echo('\n'.join(txt), m=marker)
          else:
            print('\n'.join(txt))
        else:
          print(out)

  def do_run(self, RunPrgObject):
    host = OV.GetParam("user.Server.host")
    port = int(OV.GetVar("server.port"))
    #port = OV.GetParam("user.Server.port")
    log_fn = os.path.join(OV.StrDir(), "olex2.refine_srv.log")
    if os.path.exists(log_fn):
      os.remove(log_fn)
    inp_fn = os.path.join(RunPrgObject.filePath, RunPrgObject.original_filename)
    debug = OV.GetParam("user.Server.debug")
    cmds = ["run:%s" %self.job_id,
            "xlog:%s" %log_fn,
            "spy.DebugInVSC" if debug=="VSC" else "",
            "SetVar server.job_id " + self.job_id,
            "SetVar olex2.remote_mode true",
            "spy.LoadParams 'user,olex2'",
            "spy.SetParam user.refinement.client_mode False",
            "SetOlex2RefinementListener(True)",
            "reap '%s.ins' -no_save=true" %inp_fn,
            "spy.ac.diagnose",
            "refine",
            #"spy.saveHistory",
            "@close",
            ]
    attempt = 1
    while attempt < 3:
      data = self.send_cmd(host=host, port=port, cmd='\n'.join(cmds).encode())
      if data is None:
        attempt += 1
        print("Attempt %s" %attempt)
        time.sleep(1)
        continue
      else:
        data = data.decode("utf-8").rstrip('\n')
        break
    if data is None:
      raise Exception("Failed to start the refinement")
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
