import glob
import os
import shutil
import sys
import tempfile
import unittest

def setup_paths():
  basedir = os.path.abspath('../../../')
  sys.path.append("%s" %basedir)
  sys.path.append("%s/etc/scripts" %basedir)
  sys.path.append("%s/util/pyUtil" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib/FileReaders" %basedir)
  sys.path.append("%s/util/pyUtil/CctbxLib" %basedir)
  sys.path.append("%s/util/pyUtil/regression" %basedir)
  sys.path.append("%s/util/pyUtil/regression/dummy_olex_files" %basedir)
  os.environ['PATH'] += ';%s' %basedir

def setup_phil_handler():
  import phil_interface
  import iotbx.phil
  master_phil = iotbx.phil.parse(
    file_name="../../../params.phil",
    converter_registry=phil_interface.converter_registry)
  return phil_interface.phil_handler(master_phil=master_phil)

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
    variableFunctions.InitialiseVariables('startup')

  def tearDown(self):
    if os.path.isdir(self.tmp):
      shutil.rmtree(self.tmp)
