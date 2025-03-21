try:
  import olex
  from olexFunctions import OV
  import variableFunctions as VF
except:
  from olexFunctions import OV
  import variableFunctions as VF


class ArgumentParser(object):

  def __init__(self, args=None, tool_arg=None):
    self.basedir = OV.BaseDir()
    self.filefull = OV.FileFull()
    self.filepath = OV.FilePath()
    self.filename = OV.FileName()
    self.datadir = OV.DataDir()
