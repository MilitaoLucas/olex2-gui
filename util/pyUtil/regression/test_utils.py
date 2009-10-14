import glob
import os
import shutil
import sys

def set_up_paths():
  basedir = os.path.abspath('../../../')
  sys.path.append("%s" %basedir)
  sys.path.append("%s/etc/scripts" %basedir)
  sys.path.append("%s/util/pyUtil" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib" %basedir)
  sys.path.append("%s/util/pyUtil/PyToolLib/FileReaders" %basedir)
  sys.path.append("%s/util/pyUtil/CctbxLib" %basedir)
  sys.path.append("%s/util/pyUtil/regression" %basedir)
  sys.path.append("%s/util/pyUtil/regression/dummy_olex_files" %basedir)

set_up_paths()

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
