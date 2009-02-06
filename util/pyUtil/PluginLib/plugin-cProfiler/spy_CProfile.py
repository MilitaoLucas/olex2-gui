# spy_CProfile.py

from spy import Spy
import sys
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import cProfile

class Spy(object):
  def __init__(self, tool, fun, param):
    super(Spy, self).__init__(tool, fun, param)
    self.basedir = ''
    self.tool = tool
    self.fun = fun
    self.param = param

  def run(self):
    g = OV.cprofile_wrap(self.spy_run)
    g()
    #g.__name__ = spy_run.__name__
    
    
  def spy_run(self):
    try:
      from pyTools import pyTools
      t = pyTools(self.tool, self.fun, self.param)
      t.run()
      #OV.UpdateHtml()
    except Exception, ex:
      basedir = olx.BaseDir()
      rFile = open(r"%s/version.txt" %basedir)
      version = rFile.readline()
      print >> sys.stderr, "===================================== Gui SVN Version: %s -- Olex Compilation Date: %s" %(version, olx.GetCompilationInfo())
      print >> sys.stderr, "A Python Error has occured."
      print >> sys.stderr, "Tool: %s, Function: %s, Parameters: %s"
      sys.stderr.formatExceptionInfo()