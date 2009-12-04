import os
import sys
import zipfile
import shutil
import hashlib

repository_folder = 'e:/svn/olex2-sf/trunk/'
tmp_folder = 'e:/tmp/'
putty_location = r'"C:\Program Files (x86)\PuTTY\pscp.exe"'
zip_names = {'SSE':'olex2_exe_sse.zip', 'SSE2': 'olex2_exe.zip', 'None' : 'olex2_exe_64.zip' }
dest_names_olex2 = {
  'SSE': repository_folder + 'build/scons/msvc-9.0/release-32bit/py' + sys.version[:3] + '-' + 'SSE/exe/olex2.exe', 
  'SSE2': repository_folder + 'build/scons/msvc-9.0/release-32bit/py' + sys.version[:3] + '-' + 'SSE2/exe/olex2.exe',
  'None': repository_folder + 'build/scons/msvc-9.0/release-64bit/py' + sys.version[:3] + '/exe/olex2.exe'
}
dest_names_olex2c = {
  'SSE': repository_folder + 'build/scons/msvc-9.0/release-32bit/py' + sys.version[:3] + '-' + 'SSE/exe/olex2c.exe', 
  'SSE2': repository_folder + 'build/scons/msvc-9.0/release-32bit/py' + sys.version[:3] + '-' + 'SSE2/exe/olex2c.exe',
  'None': repository_folder + 'build/scons/msvc-9.0/release-64bit/py' + sys.version[:3] + '/exe/olex2c.exe'
}
win_dest_names = {'32bit': repository_folder + 'winrun/build/scons/msvc-9.0/release-32bit/py' + sys.version[:3] + '/exe/', 
                 '64bit': repository_folder + 'winrun/build/scons/msvc-9.0/release-64bit/py' + sys.version[:3] + '/exe/'
                }
py_dir = {'32bit': r'C:\Python26', '64bit' : r'C:\Python262x64'}
wx_dir = {'32bit': r'E:\wxWidgets-2.8.9', '64bit' : r'E:\wxWidgets-2.8.9-x64'}
file_suffix = {'32bit' : '', '64bit' : '_64'}
def compile(sse, _platform):
  try:
    cwd = os.getcwd()
    os.chdir(repository_folder)
    if os.system( py_dir[_platform] + '/Scripts/scons -j8 --olx_sse=' + sse + ' --wxdir=' + wx_dir[_platform]) != 0:
      print 'Scons returned non zero...'
      return False
    print 'Creating ' +  zip_names[sse] + ':'
    print dest_names_olex2[sse]
    print 'As olex2.dll'
    if not os.path.exists(dest_names_olex2[sse]):
      print 'Could not locate the file...'
      return False
    dest_zip = zipfile.ZipFile(tmp_folder + zip_names[sse],
                              mode='w', compression=zipfile.ZIP_DEFLATED)
    dest_zip.write(dest_names_olex2[sse], 'olex2.dll')
    dest_zip.close()
    return True
  finally:
    os.chdir(cwd)
def win_compile(_platform):
  try:
    cwd = os.getcwd()
    os.chdir(repository_folder+'winrun/')
    if os.system(py_dir[_platform] + '/Scripts/scons -j8') != 0:
      print 'Scons returned non zero...'
      return False
    if not os.path.exists(win_dest_names[_platform] + 'installer.exe'):
      print 'Could not locate the file \'' + win_dest_names[_platform] + 'installer.exe\''
      return False
    shutil.copyfile(win_dest_names[_platform] + 'installer.exe', tmp_folder + 'installer' + file_suffix[_platform] + '.exe');
    if not os.path.exists(win_dest_names[_platform] + 'launch.exe'):
      print 'Could not locate the file \'' + win_dest_names[_platform] + 'launch.exe\''
      return False
    dest_zip = zipfile.ZipFile(tmp_folder + 'launch_exe'+file_suffix[_platform] + '.zip',
                              mode='w', compression=zipfile.ZIP_DEFLATED)
    dest_zip.write(win_dest_names[_platform] + 'launch.exe', 'olex2.exe')
    dest_zip.close()
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
  if not win_compile('32bit'):
    print 'Compilation failed. Aborting...'
    sys.exit(1)
  if not win_compile('64bit'):
    print 'Compilation failed. Aborting...'
    sys.exit(1)
  shutil.copy2(dest_names_olex2c['SSE'], tmp_folder + 'olex2c.exe')
  _files = [
    tmp_folder + zip_names['SSE'],
    tmp_folder + zip_names['SSE2'],
    tmp_folder + zip_names['None'],
    tmp_folder + 'installer' + file_suffix['32bit'] + '.exe',
    tmp_folder + 'installer' + file_suffix['64bit'] + '.exe',
    tmp_folder + 'launch_exe' + file_suffix['32bit'] + '.zip',
    tmp_folder + 'launch_exe' + file_suffix['64bit'] + '.zip',
    tmp_folder + 'olex2c.exe'
  ]
  files = []
  for f in _files:
    md5_prev = ''
    if os.path.exists(f+'.md5'):
      md5_file = file(f+'.md5', 'rb')
      md5_prev = md5_file.readline()
      md5_file.close()
    md5_hash = hashlib.md5(file(f, 'rb').read()).hexdigest()
    if md5_prev != md5_hash:
      files.append(f)
      md5_file = file(f+'.md5', 'wb')
      md5_file.write(md5_hash)
      md5_file.close()
  
  up_str = putty_location
  for f in files:
    up_str += ' ' + f
  up_str += ' oleg@dimas.dur.ac.uk:/var/distro/bin_dir/'
  if len(files) != 0:
    if os.system(up_str) != 0:
      print 'Upload has failed...'
    else:
      print 'Done...'
  else:
    print 'All files are the same as the last time uploaded'
  