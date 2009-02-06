from libtbx.bundle import copy_all
from libtbx.command_line import bundle_as_exe
import shutil
import os

def run():
  copy_all.run('cctbx')
  bundle_as_exe.run(['cctbx', 'winxp'])
  shutil.rmtree('cctbx_sources')
  shutil.rmtree('cctbx_build')
  os.remove('autorun')

if __name__ == '__main__':
  run()