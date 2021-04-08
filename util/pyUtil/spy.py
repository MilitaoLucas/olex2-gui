# spy.py
import sys
from olexFunctions import OV

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
    except Exception as ex:
      basedir = OV.BaseDir()
      rFile = open(r"%s/version.txt" %basedir)
      version = rFile.readline()
      rFile.close()
      print("===================================== Gui SVN Version: %s -- Olex Compilation Date: %s" %(version, OV.GetCompilationInfo()), file=sys.stderr)
      print("A Python Error has occured.", file=sys.stderr)
      print("Tool: %s, Function: %s, Parameters: %s", file=sys.stderr)
      sys.stderr.formatExceptionInfo()

if __name__ == "__main__":
  tool = OV.FindValue("tool")
  fun = OV.FindValue("fun")
  param = OV.FindValue("param")
  try:
    if OV.IsPluginInstalled('plugin-CProfile'):
      sys.path.append("%s/util/pyUtil/PluginLib/plugin-CProfiler" %(OV.BaseDir()))
      import spy_CProfile
      a = spy_CProfile.Spy(tool, fun, param)
    else:
      a = Spy(tool, fun, param)
    print("Running an old-style spy tool: %s" %tool)  
    print("You should not be seeing this line. If you do, please let us know immediately")
    a.run()
  except Exception as ex:
    print("There was an outer problem", file=sys.stderr)
    sys.stderr.formatExceptionInfo()
