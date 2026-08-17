import glob
import os
import shutil
import sys
import tempfile
import unittest

def setup_paths():
  """The run directory on sys.path, as Olex2 puts it there at startup.

  Derived from this file rather than from the working directory, so the suite
  runs from anywhere; it used to be os.path.abspath('../../../'), which meant
  it only worked when invoked from its own directory.

  Every package directory under util/pyUtil is added rather than a fixed list.
  The list had gone stale - misc/ holds ins_header, which olexFunctions
  imports, so importing OV failed outright - and it would go stale again on
  the next directory anyone adds.
  """
  here = os.path.dirname(os.path.abspath(__file__))
  basedir = os.path.abspath(os.path.join(here, "..", "..", ".."))
  py_util = os.path.join(basedir, "util", "pyUtil")
  paths = [basedir,
           os.path.join(basedir, "etc", "scripts"),
           py_util,
           os.path.join(py_util, "PyToolLib", "FileReaders"),
           here,
           os.path.join(here, "dummy_olex_files")]
  if os.path.isdir(py_util):
    for name in sorted(os.listdir(py_util)):
      d = os.path.join(py_util, name)
      if os.path.isdir(d) and not name.startswith((".", "__")):
        paths.append(d)
  for p in paths:
    if p not in sys.path:
      sys.path.append(p)
  os.environ['PATH'] += ';%s' %basedir
  return basedir

def setup_phil_handler():
  """As variableFunctions builds it at startup.

  phil_interface.converter_registry is long gone - the registry moved inside
  phil_interface.parse - and the file was read relative to the working
  directory, so the suite only ran from one place. Both are why this had
  stopped working.
  """
  import phil_interface
  master_phil = phil_interface.parse(
    file_name=os.path.join(olx.BaseDir(), "params.phil"))
  return phil_interface.phil_handler(master_phil=master_phil,
                                     parse=phil_interface.parse)

setup_paths()
import path_utils
path_utils.setup_cctbx()
import olx
olx.phil_handler = setup_phil_handler()

from olexFunctions import OV
import variableFunctions

class TestCaseBase(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.mkdtemp()
    olx.tmp_dir = self.tmp
    for g in glob.glob('%s/sample_data/Co110/Co110.*' %OV.BaseDir()):
      shutil.copy(g, self.tmp)
    for f in os.listdir('test_files'):
      if os.path.isfile('test_files/%s' %f):
        shutil.copy('test_files/%s' %f, self.tmp)
    os.mkdir('%s/.olex' %self.tmp)
    # variableFunctions.InitialiseVariables('startup') used to be called here.
    # It no longer exists anywhere in the tree - the phil handler set up above
    # is what it did - and calling it raised AttributeError before any test in
    # this case could run.

  def tearDown(self):
    if os.path.isdir(self.tmp):
      shutil.rmtree(self.tmp)
