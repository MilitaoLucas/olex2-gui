# spy_CProfile.py
import sys
from olexFunctions import OlexFunctions
OV = OlexFunctions()
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
    except Exception, ex:
      basedir = OV.BaseDir()
      rFile = open(r"%s/version.txt" %basedir)
      version = rFile.readline()
      print >> sys.stderr, "===================================== Gui SVN Version: %s -- Olex Compilation Date: %s" %(version, OV.GetCompilationInfo())
      print >> sys.stderr, "A Python Error has occured."
      print >> sys.stderr, "Tool: %s, Function: %s, Parameters: %s"
      sys.stderr.formatExceptionInfo()
