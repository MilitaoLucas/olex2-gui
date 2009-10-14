# replicate Olex2 internal functions accessed through olx.py

import os
import shutil
import subprocess

def Alert(*args, **kwds):
  return 'Y'

def BaseDir():
  return basedir

def StrDir():
  return '%s/tmp/.olex' %regression_dir

def DataDir():
  return ''

def Exec(command):
  subprocess.call('%s/%s' %(basedir, command.replace("'", '')))

def FileName(FileFull=''):
  return filename

def FilePath(FileFull=''):
  return '%s/tmp' %regression_dir

def FileFull():
  return '%s/tmp/%s.%s' %(regression_dir, filename, fileext)

def file_Copy(copy_from, copy_to):
  assert os.path.isfile(copy_from)
  shutil.copyfile(copy_from, copy_to)

def file_GetName(filename):
  return os.path.basename(filename)

def file_Which(filename):
  return filename

def HasGUI():
  return has_gui

def HKLSrc(filefull=None):
  if filefull is None:
    return '%s/tmp/%s.hkl' %(regression_dir, filename)

def Lst(item):
  return 'n/a'

def IsFileType(fileType):
  return fileType == 'cif'

def IsPluginInstalled(plugin_name):
  if plugin_name == 'plugin-CProfile':
    return 'false'
  else:
    return 'true'

def LSM():
  if phil_handler.get_validated_param('snum.refinement.method') == 'CGLS':
    return 'CGLS'
  else:
    return 'L.S.'

def User(filepath):
  os.chdir(filepath.strip("'"))

def xf_au_GetAtomCount():
  return 54

def xf_GetFormula():
  return 'C16 H16 N4 O4 F6 S2 Co1'

def xf_au_IsPeak(i):
  return True

def Atreap(*args, **kwds):
  pass

def CreateBitmap(*args, **kwds):
  pass

def DeleteBitmap(*args, **kwds):
  pass

def Cursor(*args, **kwds):
  pass

def File(*args, **kwds):
  pass

def Name(*args, **kwds):
  pass

def Reset(*args, **kwds):
  pass

def Stop(*args, **kwds):
  pass

def WaitFor(*args, **kwds):
  pass

def _setup_phil_handler():
  import phil_interface
  import iotbx.phil
  master_phil = iotbx.phil.parse(
    file_name="../../../params.phil",
    converter_registry=phil_interface.converter_registry)
  return phil_interface.phil_handler(master_phil=master_phil)

phil_handler = _setup_phil_handler()
regression_dir = os.getcwd()
basedir = os.path.abspath('../../..')
filename = 'Co110'
fileext = 'res'
has_gui='true'
