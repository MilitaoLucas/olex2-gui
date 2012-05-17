import unittest
import glob
import os
import shutil

import test_utils

from libtbx.test_utils import show_diff

import History
from History import hist

from olexFunctions import OlexFunctions
OV = OlexFunctions()

class HistoryTestCase(test_utils.TestCaseBase):

  def test_create_history(self):
    # post-solution
    shutil.copyfile('test_files/Co110_patt.lst', '%s/Co110.lst' %self.tmp)
    OV.SetParam('snum.solution.program', 'ShelXS')
    OV.SetParam('snum.solution.method', 'Patterson Method')
    OV.SetParam('snum.refinement.sg', 'P-1')
    History.tree = History.HistoryTree() # reset history
    tree = History.tree
    self.assertTrue(hist.is_empty())
    self.assertEqual(tree.current_refinement, None)
    self.assertEqual(tree.current_solution, None)
    hist.create_history(solution=True)
    self.assertEqual(tree.current_refinement, 'solution')
    self.assertEqual(tree.current_solution, 'Solution 01')
    self.assertEqual(tree.name, OV.FileName())
    self.assertTrue(os.path.isfile('%s/.olex/originals/Co110.res' %OV.FilePath()))
    self.assertFalse(hist.is_empty())
    branch = tree.historyTree[tree.current_solution]
    self.assertEqual(branch.solution_program, 'ShelXS')
    self.assertEqual(branch.solution_method, 'Patterson Method')
    self.assertEqual(str(branch.spaceGroup), 'P -1')
    leaf = branch.historyBranch[tree.current_refinement]
    self.assertEqual(leaf.refinement_program, None)
    self.assertEqual(leaf.refinement_method, None)
    self.assertEqual(leaf.solution_program, 'ShelXS')
    self.assertEqual(leaf.solution_method, 'Patterson Method')
    self.assertEqual(leaf.program_version, 'SHELXTL Ver. 6.12 W95/98/NT/2000/ME')
    self.assertEqual(leaf.R1, 'n/a')
    self.assertEqual(leaf.wR2, 'n/a')
    self.assertEqual(History.decompressFile(leaf.res),
                     open('%s/Co110.res' %self.tmp).read())
    self.assertEqual(History.decompressFile(leaf.lst),
                     open('%s/Co110.lst' %self.tmp).read())
    # post-refinement
    shutil.copyfile('test_files/Co110_shelxl.lst', '%s/Co110.lst' %self.tmp)
    OV.SetParam('snum.refinement.program', 'ShelXL')
    OV.SetParam('snum.refinement.method', 'Least Squares')
    hist.create_history()
    self.assertEqual(tree.current_refinement, 'refinement_02')
    self.assertEqual(tree.current_solution, 'Solution 01')
    branch = tree.historyTree[tree.current_solution]
    leaf = branch.historyBranch[tree.current_refinement]
    self.assertEqual(leaf.refinement_program, 'ShelXL')
    self.assertEqual(leaf.refinement_method, 'Least Squares')
    self.assertEqual(leaf.solution_program, None)
    self.assertEqual(leaf.solution_method, None)
    self.assertEqual(leaf.program_version, 'SHELXTL Ver. 6.12 W95/98/NT/2000/ME')
    self.assertEqual(leaf.R1, 0.0312)
    self.assertEqual(leaf.wR2, 0.0819)
    self.assertEqual(History.decompressFile(leaf.res),
                     open('%s/Co110.res' %self.tmp).read())
    self.assertEqual(History.decompressFile(leaf.lst),
                     open('%s/Co110.lst' %self.tmp).read())
    self.assertTrue(os.path.isfile('%s/VFS/history-info.htm' %self.tmp))
    history_bars_html = open('%s/VFS/history-info.htm' %self.tmp).read()
    self.assertFalse(show_diff(history_bars_html, """\
<zimg border=0 src=vscale.png>
<a href='spy.revert_history -solution="html.GetValue(SET_HISTORY_CURRENT_SOLUTION)" -refinement=solution>>html.Update' target=Solution><zimg border=0 width='7' src=vbar-sol.png></a>
<a href='spy.revert_history -solution="html.GetValue(SET_HISTORY_CURRENT_SOLUTION)" -refinement="refinement_02">>html.Update' target='R1: 3.12%25, Refinement: ShelXL - Least Squares'><zimg border=0 width='7' src=vbar-31.png></a>
<br>
 <b>P -1</b> -  ShelXS - Patterson Method"""))
    # test save/load
    hist.saveHistory()
    self.assertTrue(os.path.isfile('%s/.olex/Co110.history' %self.tmp))
    History.tree = History.HistoryTree() # reset history
    hist.loadHistory()
    tree = History.tree
    self.assertEqual(tree.current_refinement, 'refinement_02')
    self.assertEqual(tree.current_solution, 'Solution 01')
    self.assertEqual(tree.name, 'Co110')
    # test reset
    hist.resetHistory()
    # test delete
    hist.create_history(solution=True)
    self.assertEqual(History.tree.current_solution,'Solution 02')
    hist.delete_history('Solution 02')
    self.assertEqual(History.tree.current_solution,'Solution 01')
    # test revert

def TestSuite():
  return unittest.TestLoader().loadTestsFromTestCase(HistoryTestCase)

if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(TestSuite())
