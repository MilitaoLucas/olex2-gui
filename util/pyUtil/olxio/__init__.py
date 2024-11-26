import sys, os
import olex

class FileId(object):
  """ a simple object to compare files size and timestamp
  """
  name = ""
  mk_time = 0
  size = 0
  def __init__(self):
    pass

  def __init__(self, fn):
    self.name = fn
    self.mk_time = os.stat(fn).st_mtime
    self.size = os.path.getsize(fn)

  def __eq__(self, o: object) -> bool:
    if o is None: return False
    return self.name == o.name and self.mk_time == o.mk_time and self.size == o.size

  def ok(self) -> bool:
    return self.mk_time != 0 and len(self.name) > 0

class StreamRedirection:
  def __init__(self, stream, basedir, datadir, is_redirecting=True):
    self.redirected = stream
    self.basedir = basedir
    self.datadir = datadir
    self.is_redirecting = is_redirecting
    self.isErrorStream = (stream==sys.stderr)
    self.graph=False

    if self.isErrorStream:
      self.errFile = open(os.path.join(self.datadir, "PythonError.log"), 'w', encoding="utf8")
      self.version = olex.f("GetCompilationInfo()")
      try:
        self.GUIversion = open(os.path.join(self.basedir, "version.txt"), 'r').readline()
      except:
        self.GUIversion = "unknown"
      self.errFile.write("================= PYTHON ERROR ================= Olex2 Version %s -- %s\n\n" %(self.version, self.GUIversion))

  def write(self, Str):
    if self.is_redirecting:
      if self.isErrorStream:
        self.errFile.write(Str)
        self.errFile.flush()
      olex.post( '\'' + Str + '\'')
      if self.graph!=False:
        self.graph(Str)
    else:
      self.redirected.write(Str)

  def flush(self):
    pass

  def formatExceptionInfo(self, maxTBlevel=5):
    import traceback
    import inspect
    import tokenize
    from olexFunctions import OV
    traceback.print_exc()
    tb = sys.exc_info()[2]
    if OV.HasGUI():
      olex.m("Cursor")
    if tb is not None:
      while tb.tb_next is not None: tb = tb.tb_next
      frame = tb.tb_frame
      def reader():
        try:
          yield inspect.getsource(frame)
        except:
          print(">>>>> ERROR (formatExceptionInfo)")
      args = {}
      try:
        for ttype, token, start, end, line in inspect.tokenize.generate_tokens(reader().__next__):
          if ttype == tokenize.NAME and token in frame.f_locals:
            args[token] = frame.f_locals[token]
        if args:
          sys.stderr.write('Key variable values:\n')
          for var,val in list(args.items()):
            sys.stderr.write('\t%s = %s\n' % (var, repr(val)))
      except inspect.tokenize.TokenError:
        pass
