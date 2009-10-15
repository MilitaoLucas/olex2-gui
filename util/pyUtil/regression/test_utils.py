import glob
import os
import shutil
import sys

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

from olexFunctions import OlexFunctions
OV = OlexFunctions()

def copy_to_tmp():
  clean_up()
  os.mkdir('tmp')
  for g in glob.glob('%s/sample_data/Co110/Co110.*' %OV.BaseDir()):
    shutil.copy(g, 'tmp')
  for f in os.listdir('test_files'):
    if os.path.isfile('test_files/%s' %f):
      shutil.copy('test_files/%s' %f, 'tmp')
  os.mkdir('tmp/.olex')

def clean_up():
  if os.path.isdir('tmp'):
    shutil.rmtree('tmp')
