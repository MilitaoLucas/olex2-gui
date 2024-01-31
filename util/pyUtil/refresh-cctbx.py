import os
import sys
import platform
import zipfile
import shutil
from optparse import OptionParser

parser = OptionParser(usage='cctbx_refesh.py [options]')
parser.add_option('--build',
		dest='build',
        action='store',
		help='specifies build to use - [release], debug')
option, args = parser.parse_args()

debug = option.build == "debug"

if debug:
    build_def = {
    'win32-32bit': [('d:/devel/cctbx/cctbx_latest/build_win32_py38d/',
       'd:/devel/cctbx/cctbx_latest/modules/cctbx_project/',
       'd:/devel/rundir-py3/cctbx/','-j10')],
    'win32-64bit': [('d:/devel/cctbx/cctbx_latest/build_win64_py38d/',
      'd:/devel/cctbx/cctbx_latest/modules/cctbx_project/',
      'd:/devel/rundir-py3/cctbx/','-j10')],
    }
else:
    build_def = {
    'win32-32bit': [('d:/devel/cctbx/cctbx_latest/build_win32_py38/',
      'd:/devel/cctbx/cctbx_latest/modules/cctbx_project/',
      'd:/devel/rundir-py3x32/cctbx/','-j10')],
    'win32-64bit': [('d:/devel/cctbx/cctbx_latest/build_win64_py38/',
      'd:/devel/cctbx/cctbx_latest/modules/cctbx_project/',
      'd:/devel/rundir-py3/cctbx/','-j10')],
    }

def update(_platform):
  cwd = os.getcwd()
  try:
    bd = build_def[_platform]
    for d in bd:
      build_dir = os.path.expanduser(d[0])
      src_dir = os.path.expanduser(d[1])
      dest_dir = os.path.expanduser(d[2])
      bin_dir = build_dir+'bin/'
      os.chdir(build_dir)
      if os.system(bin_dir + 'libtbx.scons ' + d[3]) != 0:
        print('Scons returned non zero...')
        return False
      if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
      os.mkdir(dest_dir)
      os.chdir(dest_dir)
      if os.system(bin_dir+'libtbx.python ' + src_dir + 'libtbx/bundle/copy_all.py cctbx') != 0:
        print('Failed to create a distribution...')
        return False
      return True
  finally:
    os.chdir(cwd)

if __name__ == '__main__':
  os.system("cls")
  plat = sys.platform + '-' + platform.architecture()[0]
  print('Updating for: ' + plat)
  if update(plat):
    print('Done...')
  else:
    print('Failed...')

