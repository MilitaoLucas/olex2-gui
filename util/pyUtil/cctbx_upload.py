import os
import sys
import zipfile
import shutil
import hashlib

repository_folder = 'e:/cctbx/'
build_folders = {
  'SSE' : 'build_32_sse',
  'SSE2' : 'build_32_sse2',
  'None' : 'build_64',
}

tmp_folder = 'e:/tmp/cctbx/'
upload_cmd = r'"C:\Program Files (x86)\PuTTY\pscp.exe"'

zip_names = {'SSE':'cctbx_sse.zip', 'SSE2': 'cctbx.zip', 'None' : 'cctbx_64.zip' }

def compile(sse, _platform):
  try:
    cwd = os.getcwd()
    bin_dir = repository_folder+build_folders[sse]+'/bin/'
    os.chdir(repository_folder+build_folders[sse]+'/')
    if os.system(bin_dir + 'libtbx.scons -j8') != 0:
      print 'Scons returned non zero...'
      return False
    bundle_dir = tmp_folder + 'bundle'
    if os.path.exists(bundle_dir):
      shutil.rmtree(bundle_dir)
    os.mkdir(bundle_dir)
    os.chdir(bundle_dir)
    if os.system(bin_dir+'python ' + repository_folder + 'cctbx_sources/libtbx/bundle/copy_all.py cctbx') != 0:
      print 'Failed to create a distribution...'
      return False
    
    print 'Creating ' +  tmp_folder+zip_names[sse] + ':'
    root_dir_len = len(bundle_dir.replace('\\', '/') + '/')
    dest_zip = zipfile.ZipFile(tmp_folder + zip_names[sse],
                              mode='w', compression=zipfile.ZIP_DEFLATED)
    for dir_path, dir_names, file_names in os.walk(bundle_dir):
      dir_path = dir_path.replace('\\', '/')
      for f in file_names:
        dest_zip.write(dir_path+'/'+f, 'cctbx/' + dir_path[root_dir_len:] + '/' + f)
    dest_zip.close()
    os.chdir(cwd)
    shutil.rmtree(bundle_dir)
    return True
  finally:
    os.chdir(cwd)

if __name__ == '__main__':
  if not compile('SSE2', '32bit'):
    print 'Compilation failed. Aborting...'
    sys.exit(1)
  if not compile('SSE', '32bit'):
    print 'Compilation failed. Aborting...'
    sys.exit(1)
  if not compile('None', '64bit'):
    print 'Compilation failed. Aborting...'
    sys.exit(1)
  files = [
    tmp_folder + zip_names['SSE'],
    tmp_folder + zip_names['SSE2'],
    tmp_folder + zip_names['None'],
  ]
  up_str = upload_cmd
  for f in files:
    up_str += ' ' + f
  up_str += ' distro@dimas.dur.ac.uk:/var/distro/bin_dir/'
  if os.system(up_str) != 0:
    print 'Upload has failed...'
  else:
    print 'Done...'
  