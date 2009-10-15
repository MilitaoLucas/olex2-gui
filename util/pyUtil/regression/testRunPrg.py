import unittest
import os
import shutil
import sys
from StringIO import StringIO

import test_utils

import olexFunctions
OV = olexFunctions.OlexFunctions()

import olx
import RunPrg

class RunPrgTestCase(test_utils.TestCaseBase):

  def setUp(self):
    self.cwd = os.getcwd()
    test_utils.TestCaseBase.setUp(self)
    self.stdout = StringIO()
    sys.stdout = self.stdout
    olexFunctions.HasGUI = False

  def tearDown(self):
    os.chdir(self.cwd)
    test_utils.TestCaseBase.tearDown(self)
    olexFunctions.HasGUI = True # reset
    print self.stdout.getvalue()

  def test_refinement_shelxl(self):
    OV.SetParam('snum.refinement.program','ShelXL')
    OV.SetParam('snum.refinement.method','Least Squares')
    run = RunPrg.RunRefinementPrg()

  def test_solution_shelxs(self):
    shutil.copyfile('%s/Co110_patt.ins' %self.tmp, '%s/Co110.ins' %self.tmp)
    OV.SetParam('snum.solution.program', 'ShelXS')
    OV.SetParam('snum.solution.method', 'Patterson Method')
    run = RunPrg.RunSolutionPrg()

  #def test_solution_charge_flipping(self):
    #OV.SetParam('snum.solution.program', 'smtbx-solve')
    #OV.SetParam('snum.solution.method', 'Charge Flipping')
    #run = RunPrg.RunSolutionPrg()

def TestSuite():
  return unittest.TestLoader().loadTestsFromTestCase(RunPrgTestCase)

if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(TestSuite())
