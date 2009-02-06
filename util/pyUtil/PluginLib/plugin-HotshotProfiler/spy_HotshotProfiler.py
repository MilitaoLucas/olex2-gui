# spy_HotshotProfiler.py

from spy import Spy
import sys
import hotshot, hotshot.stats
from olexFunctions import OlexFunctions
OV = OlexFunctions()

class Spy(object):
  def __init__(self, tool, fun, param):
    super(Spy, self).__init__(tool, fun, param)
    self.basedir = ''
    self.tool = tool
    self.fun = fun
    self.param = param

  def run(self):
    try:
      from pyTools import pyTools
      t = pyTools(self.tool, self.fun, self.param)
      prof = hotshot.Profile("c://test.prof")
      prof.runcall(t.run)
      prof.close()
      
      olex_output = sys.stdout
      outFile = open('%s/profile.txt' %OV.DataDir(), 'a')
      sys.stdout = outFile
      
      stats = hotshot.stats.load("c://test.prof")
      stats.strip_dirs()
      stats.sort_stats('time','calls')        
      stats.print_stats(20)
      outFile.close()
      sys.stdout = olex_output
      #olex.m('exec -o getvar(defeditor) %')tex
      #t.run()
      #OV.UpdateHtml()
    except Exception, ex:
      print >> sys.stderr, "There is an inner problem"
      sys.stderr.formatExceptionInfo()