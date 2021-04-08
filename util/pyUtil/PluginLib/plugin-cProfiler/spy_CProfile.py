# spy_CProfile.py
import sys
from olexFunctions import OV
import cProfile

class Spy(object):
  def __init__(self, tool, fun, param):
    self.basedir = ''
    self.tool = tool
    self.fun = fun
    self.param = param

  def run(self):
    g = OV.cprofile_wrap(self.spy_run)
    g()

  def spy_run(self):
    try:
      from pyTools import pyTools
      t = pyTools(self.tool, self.fun, self.param)
      t.run()
    except Exception as ex:
      basedir = OV.BaseDir()
      rFile = open(r"%s/version.txt" %basedir)
      version = rFile.readline()
      print("===================================== Gui SVN Version: %s -- Olex Compilation Date: %s" %(version, OV.GetCompilationInfo()), file=sys.stderr)
      print("A Python Error has occured.", file=sys.stderr)
      print("Tool: %s, Function: %s, Parameters: %s", file=sys.stderr)
      sys.stderr.formatExceptionInfo()
