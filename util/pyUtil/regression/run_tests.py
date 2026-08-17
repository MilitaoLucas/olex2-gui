"""The unit tests that run without Olex2.

These use the stubs in dummy_olex_files, so they cover what can be tested
without a program behind them - the file readers, the history, the run-program
wrapper. Anything that needs a real structure, macro or refinement is in
olex2_pipeline_tests, which runs inside olex2c instead.

  python run_tests.py

Exit code is non-zero if anything failed, so it can gate a commit.
"""
from __future__ import absolute_import, division, print_function

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "dummy_olex_files"))

import test_utils

# Imported by name rather than as a fixed list: a module that is not in the
# working copy used to take the whole suite down at import - testSkins did
# exactly that - and one missing test file should cost that file, not all of
# them.
_modules = ["testFileReaders", "testHistory", "testRunPrg", "testSkins"]


def TestSuite():
  suite = unittest.TestSuite()
  missing = []
  for name in _modules:
    try:
      mod = __import__(name)
    except Exception as e:
      # Any exception, not only ImportError: a module that reaches the GUI
      # fails on an attribute of a stub rather than on the import itself, and
      # one such module used to take the whole suite down with it.
      missing.append("%s: %s" % (name, e))
      continue
    suite.addTest(mod.TestSuite())
  if missing:
    print("\nNOT RUN - these need a real Olex2, not the stubs. They are"
          " covered by olex2_pipeline_tests instead:")
    for m in missing:
      print("  %s" % m)
    print("")
  return suite


if __name__ == '__main__':
  result = unittest.TextTestRunner(verbosity=2).run(TestSuite())
  sys.exit(0 if result.wasSuccessful() else 1)
