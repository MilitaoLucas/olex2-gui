import os
import sys
import platform
import zipfile
import shutil
from optparse import OptionParser

parser = OptionParser(usage='cctbx_upload.py [options]')
parser.add_option('--trunk',
		  dest='trunk',
                  action='store_true',
		  help='specifies where the upload goes to. By default the files'
		       ' are uploaded to the release branch. If this options is'
                       ' set to True, the upload will go to the development server')
option, args = parser.parse_args()

if option.trunk:
  destination = 'distro@www2.olex2.org:/var/distro/bin_dir_next/'
else:
  destination = 'distro@dimas.dur.ac.uk:/var/distro/bin_dir/'

tmp_folder = '~/tmp/cctbx/'
if sys.platform[:3] == 'win':
  if platform.architecture()[0] == '64bit':
    upload_cmd = r'"C:\Program Files (x86)\PuTTY\pscp.exe"'
  else:
    upload_cmd = r'"C:\Program Files\PuTTY\pscp.exe"'
else:
  upload_cmd = 'scp'

build_def = {
  'linux2-32bit':
    (('~/cctbx-build/cctbx_build/', '~/cctbx-build/cctbx_sources/',
      '~/tmp/cctbx/', 'cctbx-linux32.zip', '-j4'),),
  'linux2-64bit':
    (('~/build/svn/cctbx/cctbx_build/', '~/cctbx-build/cctbx_sources/',
      '~/tmp/cctbx/', 'cctbx-linux64.zip', '-j4'),),
  'darwin-32bit':
    (('~/cctbx-build/cctbx_build/', '~/cctbx-build/cctbx_sources/',
      '~/tmp/cctbx/', 'cctbx-mac32.zip', '-j2'),),
  'darwin-64bit':
    (('~/cctbx-build/cctbx_build/', '~/cctbx-build/cctbx_sources/',
      '~/tmp/cctbx/', 'cctbx-mac64.zip', '-j2'),),

  'win32-32bit':
    (('e:/cctbx/build_32_sse2/', 'e:/cctbx/cctbx_sources/',
      'e:/tmp/cctbx/', 'cctbx-win32-sse2.zip', '-j6'),
     ('e:/cctbx/build_32_sse/', 'e:/cctbx/cctbx_sources/',
      'e:/tmp/cctbx/', 'cctbx-win32-sse.zip', '-j6')),
  'win32-64bit':
    [('e:/cctbx/build_64/', 'e:/cctbx/cctbx_sources/',
      'e:/tmp/cctbx/', 'cctbx-win64.zip', '-j6')],
}
# build ALL win on win64
build_def['win32-64bit'] += build_def['win32-32bit']

def compile(_platform):
  cwd = os.getcwd()
  zip_names = []
  try:
    bd = build_def[_platform]
    for d in bd:
      build_dir = os.path.expanduser(d[0])
      src_dir = os.path.expanduser(d[1])
      tmp_dir = os.path.expanduser(d[2])
      bin_dir = build_dir+'bin/'
      os.chdir(build_dir)
      if os.system(bin_dir + 'libtbx.scons ' + d[4]) != 0:
        print 'Scons returned non zero...'
        return False
      bundle_dir = tmp_dir + 'bundle'
      if os.path.exists(bundle_dir):
        shutil.rmtree(bundle_dir)
      os.mkdir(bundle_dir)
      os.chdir(bundle_dir)
      if os.system(bin_dir+'python ' + src_dir + 'libtbx/bundle/copy_all.py cctbx') != 0:
        print 'Failed to create a distribution...'
        return False

      zip_name = tmp_dir + d[3]
      print 'Creating ' +  zip_name + ':'
      root_dir_len = len(bundle_dir.replace('\\', '/') + '/')
      dest_zip = zipfile.ZipFile(zip_name,
                                mode='w', compression=zipfile.ZIP_DEFLATED)
      for dir_path, dir_names, file_names in os.walk(bundle_dir):
        dir_path = dir_path.replace('\\', '/')
        for f in file_names:
          dest_zip.write(dir_path+'/'+f, 'cctbx/' + dir_path[root_dir_len:] + '/' + f)
      dest_zip.close()
      os.chdir(cwd)
      zip_names.append(zip_name)
      shutil.rmtree(bundle_dir)
    return zip_names
  finally:
    os.chdir(cwd)

if __name__ == '__main__':
  plat = sys.platform + '-' + platform.architecture()[0]
  print 'Compiling for: ' + plat
  zip_names = compile(plat)
  if len(zip_names) == 0:
    print 'Compilation failed. Aborting...'
    sys.exit(1)

  up_str = upload_cmd
  for f in zip_names: up_str += ' ' + f
  up_str = up_str +  ' ' + destination
  print 'Uploading; ' + up_str
  sys.exit(0)
  if os.system(up_str) != 0:
    print 'Upload has failed...'
  else:
    print 'Done...'
