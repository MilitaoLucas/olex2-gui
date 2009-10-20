import unittest

import test_utils

import testFileReaders
import testHistory
import testRunPrg
import testSkins

def TestSuite():
  all_tests = unittest.TestSuite([
    testFileReaders.TestSuite(),
    testHistory.TestSuite(),
    testRunPrg.TestSuite(),
    testSkins.TestSuite(),
  ])
  return all_tests

if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(TestSuite())
