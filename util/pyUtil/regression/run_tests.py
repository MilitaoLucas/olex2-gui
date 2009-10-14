import unittest

import testFileReaders
import testHistory
import testRunPrg
  
def TestSuite():
  all_tests = unittest.TestSuite([
    testFileReaders.TestSuite(),
    testHistory.TestSuite(),
    testRunPrg.TestSuite(),
  ])
  return all_tests

if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(TestSuite())
