# spy.py
import sys
import olex
import olx
from olexFunctions import OlexFunctions
OV = OlexFunctions()

class SpyException:
  def __init__(self, spy_exception):
    self.spy_exception = spy_exception
  def __str__(self):
    return "Failure: (SPY exception '%s')" % ((self.spy_exception))

class Spy(object):
  def __init__(self, tool, fun, param):
    self.basedir = ''
    self.tool = tool
    self.fun = fun
    self.param = param

  def run(self):
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

if __name__ == "__main__":
  tool = OV.FindValue("tool")
  fun = OV.FindValue("fun")
  param = OV.FindValue("param")
  try:
    #if olx.IsPluginInstalled('plugin-HotshotProfiler') == 'true':
      #sys.path.append("%s/util/pyUtil/PluginLib/plugin-HotshotProfiler" %(olx.BaseDir()))
      #import spy_HotshotProfiler
      #a = spy_HotshotProfiler.Spy(tool, fun, param)
    if olx.IsPluginInstalled('plugin-CProfile') == 'true':
      sys.path.append("%s/util/pyUtil/PluginLib/plugin-CProfiler" %(olx.BaseDir()))
      import spy_CProfile
      a = spy_CProfile.Spy(tool, fun, param)
    else:
      a = Spy(tool, fun, param)
    a.run()
  except Exception, ex:
    print >> sys.stderr, "There was an outer problem"
    sys.stderr.formatExceptionInfo()
