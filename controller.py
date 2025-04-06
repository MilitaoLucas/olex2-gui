import os, sys
import subprocess, socket, time

basedir = os.path.split(os.path.abspath(__file__))[0]
os.environ["PYTHONHOME"] = os.path.join(basedir, "Python38")
#!!
os.environ["OLEX2_CCTBX_DIR"] = r"D:\devel\cctbx\cctbx_latest\build_win64_py38"

WARNING = '\033[93m'
start_port = 8889
class HeadlessController(object):
  def __init__(self, str_name):
    self.host = "localhost"
    self.port = start_port
    self.debug = False
    self.share = True
    self.str_path, self.str_name = os.path.split(str_name)
    self.str_dir = os.path.join(self.str_path, "olex2")

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

  def pre_refinement(self):
    import uuid
    self.job_id = uuid.uuid4().hex
    try:
        reserve_ = ("reserve:%s\n" %self.job_id).encode()
        port = self.port
        data = self.send_cmd(self.host, self.port, reserve_, handle=False)\
          .decode("utf-8").rstrip('\n')
        print(f"Received {data}")
        while data == "busy":
          if not self.share:
            port += 1
            data = self.send_cmd(self.host, self.port, reserve_, handle=False)\
              .decode("utf-8").rstrip('\n')
            continue
          time.sleep(1)
          data = self.send_cmd(self.host, self.port, reserve_, handle=True)\
            .decode("utf-8").rstrip('\n')
        if data == "ready":
          print("Using Olex2 server on %s" %port)
          self.port = port
    except ConnectionRefusedError as ex:
      if self.host != "localhost":
        raise Exception("No running server found!")
      print("Launching Olex2 server...")
      cd = os.curdir

      my_env = os.environ.copy()
      if "OLEX2_ATTACHED_WITH_PYDEBUGGER" in my_env and self.debug != "Wing":
        del my_env["OLEX2_ATTACHED_WITH_PYDEBUGGER"]
      headless_name = "olex2c"
      if sys.platform[:3] == 'win':
        headless_name += ".dll"
      elif sys.platform == 'darwin':
        headless_name += "_exe"
      subprocess.Popen(
        [os.path.join(basedir, headless_name), "server", str(self.port), self.job_id],
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
            print(WARNING + '\n'.join(txt))
          else:
            print('\n'.join(txt))
        else:
          print(out)

  def do_run(self, command):
    self.pre_refinement()
    log_fn = os.path.join(self.str_dir, "olex2.refine_srv.log")
    if os.path.exists(log_fn):
      os.remove(log_fn)
    inp_fn = os.path.join(self.str_path, self.str_name)
    cmds = ["run:%s" %self.job_id,
            "xlog:%s" %log_fn,
            "spy.DebugInVSC" if self.debug=="VSC" else "",
            "SetVar server.job_id " + self.job_id,
            "SetVar olex2.remote_mode true",
            "spy.LoadParams 'user,olex2'",
            "spy.SetParam user.refinement.client_mode False",
            "SetOlex2RefinementListener(True)",
            "reap '%s' -no_save=true" %inp_fn,
            "spy.ac.diagnose",
            command,
            #"spy.saveHistory",
            "@close",
            ]
    attempt = 1
    while attempt < 3:
      data = self.send_cmd(host=self.host, port=self.port, cmd='\n'.join(cmds).encode())
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
        data = self.send_cmd(host=self.host, port=self.port, cmd=b"status\n")
        if data is None:
          break
        data = data.decode("utf-8").rstrip('\n')
      self.read_log(log)

if __name__ == '__main__':
  if len(sys.argv) < 2 or (sys.argv[1] == "/?" or sys.argv[1] == "/h"):
    print("Olex2c command line controller")
    print("Available commands: solve, refine, stop")
    sys.exit(0)

  cmd = sys.argv[1]
  if cmd == "stop":
    print("Shutting down the server(s)")
    import socket
    port = start_port
    while True:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
          s.connect(("localhost", port))
          s.sendall(b"stop\n")
          port += 1
        except:
          break
    sys.exit(0)

  if len(sys.argv) < 3:
    print("Please provide a structure to process")
    sys.exit(1)
  c = HeadlessController(sys.argv[2])
  c.do_run(sys.argv[1])
