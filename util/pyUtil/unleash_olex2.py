#!/usr/bin/python
from __future__ import print_function
""" Olex 2 distro management """
import threading

if __name__ == '__main__':
  import sys
  if len(sys.argv) == 1:
    sys.argv.append('--web_directory=' + "D:/tmp/www/1.5")
    sys.argv.append('--working_directory=' + "D:/tmp/test-gui-trunk")
    sys.argv.append('--bin_directory=' + "D:/devel/bin_dir-1.5")
    #sys.argv.append('--platform' + "=win32")
    sys.argv.append('--beta')

# plugin properties name-platform-architecture, like Headless-win-32
# Headless - portables
# win - portable to windows disregarding the architecture
# 32 - runs only on 32 bit

#available ports
# alteartions for binary files : name (properties...), olex-port MUST be specified for non-portable files
mac64_port_name = 'port-mac64'
mac64_port_zip_name = 'olex2-mac64-intel.zip'
mac64_port_prefix = 'olex2.app/Contents/MacOS/'

linux64_port_name = 'port-linux64'
linux64_port_zip_name = 'olex2-linux64.zip'
linux64_port_prefix = 'olex2/'

win32_port_name = 'port-win32-portable'
win32_sse2_port_name = 'port-win32'
win32_sse2_port_zip_name = 'olex2-win32.zip'
win32_sse2_port_prefix = None

win64_port_name = 'port-win64'
win64_port_zip_name = 'olex2-win64.zip'
win64_port_prefix = None

portable_zip_name = 'portable-gui.zip'
portable_prefix = None
# iteratable list of zips and prefixes
distro_zips = (
  (mac64_port_zip_name, mac64_port_prefix),
  (linux64_port_zip_name, linux64_port_prefix),
  (win32_sse2_port_zip_name, win32_sse2_port_prefix),
  (win64_port_zip_name, win64_port_prefix),
  (portable_zip_name, portable_prefix)
)

external_files = {
  #mac64
  'olex2-mac64.zip': ('olex-port', mac64_port_name, 'action:extract', 'action:delete'),
  'unirun-mac64.zip': ('olex-port', mac64_port_name, 'action:extract', 'action:delete'),
  'cctbx-mac64.zip': ('olex-port', mac64_port_name, 'action:extract', 'action:delete'),
  'lib-mac64.zip': ('olex-port', mac64_port_name,  'action:extract', 'action:delete'),
  'hart-mac64.zip': ('olex-port', mac64_port_name,  'action:extract', 'action:delete'),
  #linux64
  'olex2-linux64.zip': ('olex-port', linux64_port_name, 'action:extract', 'action:delete'),
  'unirun-linux64.zip': ('olex-port', linux64_port_name, 'action:extract', 'action:delete'),
  'cctbx-linux64.zip': ('olex-port', linux64_port_name, 'action:extract', 'action:delete'),
  'lib-linux64.zip': ('olex-port', linux64_port_name, 'action:extract', 'action:delete'),
  'hart-lin64.zip': ('olex-port', linux64_port_name, 'action:extract', 'action:delete'),
  #windows
  'launch-win32.zip': ('olex-port', win32_port_name,  'action:extract', 'action:delete'),
  'python38-win32.zip': ('olex-port', win32_port_name, 'action:extract', 'action:delete'),
  #SSE2
  'cctbx-win32-sse2.zip': ('olex-port', win32_sse2_port_name, 'action:extract', 'action:delete'),
  'olex2-win32-sse2.zip': ('olex-port', win32_sse2_port_name, 'action:extract', 'action:delete'),
  #windows 64
  'launch-win64.zip': ('olex-port', win64_port_name, 'action:extract', 'action:delete'),
  'python38-win64.zip': ('olex-port', win64_port_name, 'action:extract', 'action:delete'),
  'cctbx-win64.zip': ('olex-port', win64_port_name, 'action:extract', 'action:delete'),
  'olex2-win64.zip': ('olex-port', win64_port_name, 'action:extract', 'action:delete'),
  #portables
  'olex2_fonts.zip': ('olex-update', 'action:extract', 'action:delete'),
  'fonts.zip': ('olex-update', 'action:extract', 'action:delete'),
  'help.zip': ('olex-update', 'action:extract', 'action:delete'),
  'sample_data.zip': ('olex-update', 'action:extract', 'action:delete'),
  'FragmentDB.zip':('olex-update', 'action:extract', 'action:delete'), #HP 13/02/19
  'RPAC.zip':('olex-update', 'action:extract', 'action:delete'), #HP 08/03/19
  'acidb.zip': ('olex-update', 'action:extract', 'action:delete'),
  'splash.jpg': ('olex-install', 'olex-update'),
  #'splash.png': ('olex-install', 'olex-update'),
  'version.txt': ('olex-install', 'olex-update'),
  'dictionary.txt': ('olex-install', 'olex-update'),
  'odac_update.txt': ('olex-install', 'olex-update'),
  'licence.rtf': ('olex-install', 'olex-update'),
  'documentation.zip': ('olex-update', 'action:extract', 'action:delete'),
  'textures.zip': ('olex-update', 'action:extract', 'action:delete'),
  'ac5.zip': ('olex-update', 'action:extract', 'action:delete'),
  #plugins
  #'olex2c-win32.zip': ('olex-port', 'plugin-Headless-win-32', 'action:extract', 'action:delete'),
  #'olex2c-win64.zip': ('olex-port', 'plugin-Headless-win-64', 'action:extract', 'action:delete'),
  'plgl-mac64.zip': ('olex-port', mac64_port_name, 'action:extract', 'action:delete'),
  'plgl-linux64.zip': ('olex-port', linux64_port_name, 'action:extract', 'action:delete'),
  'plgl-win32-sse2.zip': ('olex-port', win32_sse2_port_name, 'action:extract', 'action:delete'),
  'plgl-win64.zip': ('olex-port', win64_port_name, 'action:extract', 'action:delete'),

  'hart-win64.zip': ('olex-port', win64_port_name,
              'action:extract', 'action:delete'),

  'hart-win32.zip': ('olex-port', win32_sse2_port_name,
               win32_sse2_port_name,
              'action:extract', 'action:delete'),

}
# special zip files (must have relevant structure), must exist ABOVE as well!!
#if the associated value is false - the file is non-portable and will not end up in the portable-gui.zip
portable_zip_files = \
set(  ['olex2_fonts.zip',
       'fonts.zip',
       'acidb.zip',
       'documentation.zip',
       'textures.zip',
       'ac5.zip',
       'help.zip',
       'sample_data.zip',
       'FragmentDB.zip', #HP 13/02/19
       'RPAC.zip' #HP 08/03/19
      ]
   )
win32_sse2_zip_files = \
set(  ['cctbx-win32-sse2.zip',      #cctbx/cctb_sources,...
      'python38-win32.zip',    #Pyhton38/..., ..., + python38.dll!!!
      'launch-win32.zip',  #olex2.exe
      'plgl-win32-sse2.zip',
      'olex2-win32-sse2.zip',   #olex2.dll, it will be veryfied first of all
      'hart-win32.zip'
      ]
   ) | portable_zip_files
win64_zip_files = \
set(  ['cctbx-win64.zip',     #cctbx/cctb_sources,...
      'python38-win64.zip',   #Pyhton38/..., ..., + python38.dll!!!
      'plgl-win64.zip',
      'olex2-win64.zip',  #olex2.dll
      'launch-win64.zip',  #olex2.exe
      'hart-win64.zip'
      ]
   ) | portable_zip_files
mac64_zip_files = \
set(  ['cctbx-mac64.zip',  #cctbx/cctb_sources,...
      'olex2-mac64.zip',    #olex2 executable
      'unirun-mac64.zip',
      'plgl-mac64.zip',
      'lib-mac64.zip',
      'hart-mac64.zip',
      ]
   ) | portable_zip_files
linux64_zip_files = \
set(  ['cctbx-linux64.zip',  #cctbx/cctb_sources,...
      'lib-linux64.zip',     #lib/dlls
      'olex2-linux64.zip',    #olex2 executable
      'plgl-linux64.zip',
      'unirun-linux64.zip',
      'hart-lin64.zip'
      ]
   ) | portable_zip_files

# a set of all zip files...
all_zip_files = win32_sse2_zip_files | win64_zip_files\
              | mac64_zip_files | linux64_zip_files


altered_files = set([])
altered_dirs = set([])

import os.path
import sys
from optparse import OptionParser
import pysvn
import io
import zipfile
import shutil
import itertools
import re
import time
import hashlib

def translate_working_to_web(path):
  name = os.path.basename(path)
  return os.path.join(os.path.dirname(path), name)

def filter_out_directories(seq):
  return [ p for p in seq if not os.path.isdir(p) ]

def destination(working_path, sub_web_directory=None):
  dst = web_directory
  if sub_web_directory is not None:
    dst += '/' + sub_web_directory
  return translate_working_to_web(
    working_path.replace(working_directory, dst))

def zip_destination(working_path, prefix=None):
  if prefix:
    return prefix + translate_working_to_web(working_path.replace(working_directory + '/', ''))
  return translate_working_to_web(working_path.replace(working_directory + '/', ''))

parser = OptionParser(usage='unleash_olex2.py [options]')
parser.add_option('--web_directory',
      dest='web_directory',
      help='the path to the directory that Apache will expose'
          'the distro from')
parser.add_option('--working_directory',
      dest='working_directory',
      help='the path to the svn working directory to build'
          'the distro from')
parser.add_option('--bin_directory',
      dest='bin_directory',
      help='the path where the binary files, not icnlcuded to svn reside')
parser.add_option('--beta',
      dest='beta',
      action='store_true',
      help='whether to use the normal or the tag-beta web directory')
parser.add_option('--alpha',
      dest='alpha',
      action='store_true',
      help='whether to use the normal or the tag-alpha web directory')
parser.add_option('--dev',
      dest='dev',
      action='store_true',
      help='whether to use the normal or the tag-dev web directory')
parser.add_option('--revert',
      dest='revert',
      action='store_true',
      help='whether to revert vs promoting a distribution')
parser.add_option('-f', '--file',
      dest='update_file',
                  default='',
      action='store',
      help='whether to use update any particluare file only')
parser.add_option('-p', '--platform',
      dest='release_platform',
      default='win32-sse,win32,win64,mac64,lin64',
      action='store',
      help='modify the platform list to release')

option = parser.parse_args()[0]

working_directory = os.path.expanduser(option.working_directory)
if not os.path.isdir(working_directory):
  print("ERROR: '%s' is not a directory" % working_directory)
  parser.print_help()

web_directory = os.path.expanduser(option.web_directory)
bin_directory = os.path.expanduser(option.bin_directory)
current_release_tag = "1.5"
if option.dev:
  current_release_tag += "-dev"
elif option.alpha:
  current_release_tag += "-alpha"
elif option.beta:
  current_release_tag += "-beta"

if not os.path.isdir(bin_directory):
  print("ERROR: '%s' is not a directory" % bin_directory)
  parser.print_help()
  sys.exit(1)

# update tags file, the web_dir is transformed to correct form when creating olex2.tag file
def update_tags_file(dir):
  up_dir = '/'.join(dir.split('/')[:-1])
  #tags = os.listdir(up_dir)
  tags = ['1.5-alpha', '1.3', '1.2', '1.3-beta', '1.3-alpha', '1.1', '1.0']
  tags_file = open(up_dir + '/tags.txt', 'w')
  for dir in tags:
    if dir != '.' and os.path.isdir(up_dir+'/'+dir):
      if not os.path.exists(up_dir+'/'+dir+'/olex2.tag'):
        print('Skipping invalid TAG folder: ' + dir)
        continue
      print(dir, file=tags_file)
  tags_file.close()

def is_distro_uptodate(src, dest):
  if not os.path.exists(src) or not os.path.exists(dest):
    return False
  src_mt = os.path.getmtime(src)
  dest_mt = os.path.getmtime(dest)
  return src_mt - dest_mt < 5 # 5 seconds

def run_threads(threads, thread_n=None):
  if thread_n is None:
    import multiprocessing
    thread_n = max(1, multiprocessing.cpu_count()-1)
  while threads:
    started = []
    for i in range (thread_n):
      if len(threads) <= i:
        break
      threads[i].start()
      started.append(threads[i])
    if not started:
      break
    threads = [t for t in threads if t not in started]
    for t in started:
      t.join()

def process_zip_1(dest, splash_file, zipfi, tag_file_name):
  full_zn = dest + '/' + zipfi[0]
  if os.path.exists(full_zn):
    print('Updating ' + zipfi[0] + '...')
  else:
    print('Skipping ' + zipfi[0] + '...')
    return
  src_zfile = zipfile.ZipFile(full_zn, mode='r', compression=zipfile.ZIP_DEFLATED)
  dest_zfile = zipfile.ZipFile(full_zn + '_', mode='w', compression=zipfile.ZIP_DEFLATED)
  prefix = zipfi[1]
  if not prefix:  prefix = ''
  zip_tag_name = prefix + 'olex2.tag'
  zip_splash_name = prefix + 'splash.jpg'
  for zi in src_zfile.infolist():
    if zi.filename == zip_tag_name:
      dest_zfile.write(tag_file_name, zip_tag_name)
    elif zi.filename == zip_splash_name:
      dest_zfile.write(splash_file, zip_splash_name)
    else:
      dest_zfile.writestr(zi, src_zfile.read(zi.filename))
  src_zfile.close()
  dest_zfile.close()
  os.remove(full_zn)
  os.rename(full_zn + '_', full_zn)

def promote_distro(src, dest, forward=True):
  if not os.path.exists(src):
    print("Source distribution does not exist, exiting...")
    sys.exit(0)
  if os.path.exists(dest):
    if forward:
      if is_distro_uptodate(src, dest):
        print('Destination repository is newer than the source one or up-to-date, exiting')
        sys.exit(0)
    else:
      if is_distro_uptodate(dest, src):
        print('Destination repository is older than the source one or up-to-date, exiting')
        sys.exit(0)
    shutil.rmtree(dest)
    shutil.copytree(src, dest)
  else:
    shutil.copytree(src, dest)
  # update the tag files...
  dest = dest.replace('\\','/')
  if dest.endswith('/'):  dest = dest[:-1]
  tag_file_name = dest+'/'+'olex2.tag'
  with open(tag_file_name, 'w+') as tag_file:
    print(current_release_tag, file=tag_file)
  splash_file = os.path.join(bin_directory, "splash-" + current_release_tag + ".png")
  if os.path.exists(splash_file):
    dest_splash_file = os.path.join(dest, "update", "splash.jpg")
    shutil.copy2(splash_file, dest_splash_file)
  #end creating the tag file
  threads = []
  for zipfi in distro_zips:
    t = threading.Thread(target=process_zip_1,
      kwargs={
        "dest": dest,
        "zipfi": zipfi,
        "splash_file": splash_file,
        "tag_file_name": tag_file_name
        }
      )
    threads.append(t)

  run_threads(threads)

  update_tags_file(src)
  sys.exit(0)
# do the promotion of alpha->beta->release, only alpha can be re-released

if option.beta:
  if option.revert:
    print('Reverting release distro to beta')
    promote_distro(web_directory, web_directory + '-beta')
  else:
    print('Promoting alpha distro to beta')
    promote_distro(web_directory + '-alpha', web_directory + '-beta')
elif option.alpha:
  if option.revert:
    print('Reverting beta distro to alpha')
    promote_distro(web_directory+ '-beta', web_directory + '-alpha', forward=False)
  else:
    web_directory += '-alpha'
    print('Creating alpha distro...')
elif option.dev:
  web_directory += '-dev'
  print('Creating dev distro...')
else:
  if not is_distro_uptodate(web_directory + '-alpha', web_directory + '-beta'):
    print('Beta distro is not up-to-date, aborting')
    sys.exit(0)
  print('Promoting beta distro to release')
  promote_distro(web_directory + '-beta', web_directory)

# remove the files from the repository: helps to find collisions
for val, key in external_files.items():
  fn = working_directory + '/' + val
  if os.path.exists(fn):
    os.unlink(fn)
    print("Binary distribution file removed: " + fn)

# create olex2_exe.zip from olex2.exe, if exists...
if os.path.exists(bin_directory + '/olex2.exe'):
  print("Updating olex2_exe.zip file...")
  olex2_exe_zip = zipfile.ZipFile(bin_directory + '/olex2_exe.zip',
                            mode='w', compression=zipfile.ZIP_DEFLATED)
  olex2_exe_zip.write(bin_directory + '/olex2.exe', 'olex2.dll')
  olex2_exe_zip.close()
  os.remove(bin_directory + '/olex2.exe')

client = pysvn.Client()

platforms = {
  "win32-sse": False,
  "win32": True,
  "win64": True,
  "mac64": True,
  "lin64": True,
}
try:
  if option.release_platform:
    toks = option.release_platform.split(',')
    for k,v in platforms.items():
      platforms[k] = False
    for t in toks:
      platforms[t] = True

  if option.update_file:
    filepath = option.update_file
    print('Updating %s only...' %filepath)
    n = client.update(working_directory + filepath)
    revision_number = n[0].number
    print("SVN Revision Number %i" %revision_number)
  elif True:  #defuging can set it to false to leave the folder in tact
    n = client.update(working_directory)
    revision_number = n[0].number
    print("SVN Revision Number %i" %revision_number)
    nv_line = "SVN Revision No. %s" %revision_number
    same_version = False
    if os.path.exists(bin_directory + '/version.txt'):
      ev_file = open(bin_directory + '/version.txt', 'rb')
      ev_line = ev_file.readline()
      same_version = (ev_line == nv_line)
    if not same_version:
      with open("%s/version.txt" %bin_directory, 'w') as wFile:
        wFile.write(nv_line)
#  revnum = pysvn.Revision( pysvn.opt_revision_kind.working )
#  print revnum.number
except Exception as err:
  if 'locked' in str(err):
    client.cleanup(working_directory)
    if option.update_file:
      client.update(working_directory + '/' + option.update_file)
    else:
      client.update(working_directory)
  else:
    print("ERROR: %s" % err)
    parser.print_help()
    #sys.exit(1)

# gather files and put them in different groups
top_files = filter_out_directories(
  list(client.propget('olex-top', working_directory, recurse=True).keys()))

update_files = filter_out_directories(
  list(client.propget('olex-update', working_directory, recurse=True).keys())) +\
filter_out_directories(
  list(client.propget('olex-port', working_directory, recurse=True).keys()))

#evaluate available properties for plugins
plugin_props = set()
for f, ps in client.proplist(working_directory,  recurse=True):
  for p in ps:
    if p.startswith('plugin-'):
      plugin_props.add(p[7:])
for f, ps in external_files.items():
  for p in ps:
    if p.startswith('plugin-'):
      plugin_props.add(p[7:])
#end of the plugin property evaluation

installer_files = filter_out_directories(
  list(client.propget('olex-install', working_directory, recurse=True).keys()))
files_for_plugin = dict(
  [ (plugin,
     filter_out_directories(
       list(client.propget('plugin-%s'%plugin, working_directory,
          recurse=True).keys()))
     )
     for plugin in plugin_props ])

# process binary files, new folders might get created, so the call is before creating dirs
for val, key in external_files.items():
  fn = working_directory + '/' + val
  if os.path.exists(fn):
    print("File exist both on the svn and in the binary folder '" + fn + "' skipping...")
    continue
  if not os.path.exists(bin_directory + '/' + val):
    if option.dev:
      if len(key) > 0 and key[0] == 'olex-port' and not key[1].startswith('port-win'):
        continue
    print("Specified binary file does not exist '" + val + "' check...")
    continue
  for i in range(0, len(key)):
    if key[i] == 'olex-update' or key[i] == 'olex-port':
      update_files.append(fn)
    elif key[i] == 'olex-install':
      installer_files.append(fn)
    elif key[i] == 'olex-top':
      top_files.append(fn)
    elif key[i].startswith('plugin-'):
      if not files_for_plugin[key[i][7:]]:
        files_for_plugin[key[i][7:]] = []
      files_for_plugin[key[i][7:]].append(fn)

  dest_dir = '/'.join((working_directory + '/' + val).split('/')[:-1])
  if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)
  # also remember the folders contaning the files
  alt_dir = working_directory
  alt_dirs = val.split('/')[:-1]
  for dir in alt_dirs:
    alt_dir = alt_dir + '/' + dir
    altered_dirs.add(alt_dir)
  # end of the folder remembering, copy2 copies the stat as well
  shutil.copy2(bin_directory + '/' + val, working_directory + '/' + val);
  altered_files.add(fn)

# create web directory structure (top + update)
shutil.rmtree(web_directory, ignore_errors=True)
directories_to_create = {web_directory: 1}
directories_to_create.update(dict(
  [ (os.path.dirname(destination(p, 'update')), 1)
    for p in itertools.chain(update_files, *list(files_for_plugin.values())) ]))
directories_to_create = list(directories_to_create.keys())
directories_to_create.sort()
for d in directories_to_create:
  os.makedirs(d)
update_directory = web_directory + '/update'
update_directory_pat = re.compile(update_directory + '/?')

#copy the splash
splash_file = os.path.join(bin_directory, "splash-" + current_release_tag + ".png")
def_splash_file = os.path.join(working_directory, "splash.jpg")
if os.path.exists(splash_file):
  shutil.copy2(splash_file, def_splash_file)

# copy files into the web directory
for f in top_files:
  shutil.copy2(f, destination(f))
for f in itertools.chain(update_files,
      *[ files_for_plugin[x] for x in files_for_plugin
                            if x != 'cctbx-win' ]):
  if os.path.exists(f):
    shutil.copy2(f, destination(f, 'update'))
  else:
    print("Invalid file '" + f + "' skipping")


# create the index file
def info(web_file_name, working_file_name):
  stats = os.stat(web_file_name)
  if os.path.isfile(web_file_name):
    _file = open(web_file_name, "rb")
    stats = (stats.st_mtime, stats.st_size, hashlib.md5(_file.read()).hexdigest())
  else:
    stats = (stats.st_mtime, stats.st_size, 'dir')

  #override the svn properties with the ones defined above
  normalised_fn = working_file_name.replace('\\', '/')
  if normalised_fn in altered_files:
    normalised_fn = normalised_fn.replace(working_directory + '/', '')
    props = external_files.get(normalised_fn)
  else:
    try:
      props = client.proplist(working_file_name)
      if props:
        props = tuple([ k for k in list(props[0][1].keys()) if 'svn:' not in k ])
      else:
        props = ()
    except:
      if normalised_fn in altered_dirs:
        props = ()
      else:
        props = None
  return (stats, props)

def format_info(stats, props):
  if props:
    props = ';'.join(props)
  else:
    props = ''
  return "%i,%i,%s,{%s}" % (stats+(props,))

###############################################################################################
#index file management
class IndexEntry:
  def __init__(self, parent, name, props, stats, folder):
    self.name = name
    self.parent = parent
    self.props = props
    self.stats = stats
    self.folder = folder
    self.items = {}
  def ItemCount(self):
    if not self.folder:
      return 1
    cnt = 0
    for item in self.items.values():
      cnt += item.ItemCount()
    return cnt
  def IsValid(self):
    if self.folder and self.ItemCount() == 0:
      return False
    return True
  def FromStrList(self, toks, props, stat, folder):
    item = self
    for token in toks:
      if token in item.items:
        item = item.items[token]
      else:
        item.items[token] = IndexEntry(item, token, props, stat, folder)
  def SaveToFile(self, idx_file, indent=''):
    if not self.IsValid():
      return
    if self.parent:
      print(indent + self.name, file=idx_file)
      print(indent + format_info(self.stats, self.props), file=idx_file)
      indent += '\t'
    for item in self.items.values():
      item.SaveToFile(idx_file, indent)

def filter_installer_file(only_prop=None, port_props = None, portable=False, enforce_only_prop=False):
  portable_files = set([])
  for f in installer_files:
    stats, props = info(f, f)
    if props is None: continue
    prop_set = set(props)
    if portable and f in external_files:
      if 'olex-port' in props and (port_props is None or len(port_props&prop_set) == 0):
          continue
    elif (enforce_only_prop or f not in all_zip_files) and ((only_prop is not None) and (only_prop not in prop_set)):
      continue
    if portable:
      portable_files.add(f)
  return portable_files

def create_index(index_file_name, only_prop=None, port_props = None, portable=False, enforce_only_prop=False):
  portable_files = set([])
  if only_prop is None: only_prop = ''
  only_props = set(only_prop.split(';'))
  idx_file = open(index_file_name, 'w')
  root_entry = IndexEntry(None, -1, None, None, True)
  for dir_path, dir_names, file_names in os.walk(update_directory):
    dir_names[:] = [ d for d in dir_names if not d.startswith('.') ]
    file_names[:] = [ d for d in file_names if not d.startswith('.') ]
    dir_path = dir_path.replace('\\', '/')
    d = update_directory_pat.sub('', dir_path)

    working_dir_path = os.path.join(os.path.normpath(working_directory), d)
    if d:
      stats, props = info(dir_path, working_dir_path)
      if props is None:
        dir_names[:] = []
        file_names[:] = []
        continue
      root_entry.FromStrList(d.split('/'), props, stats, True)
    normalised_root_dir = working_dir_path.replace('\\', '/')
    if normalised_root_dir[-1] != '/':
      normalised_root_dir += '/'
    for f in file_names:
      stats, props = info(os.path.join(dir_path, f),
                          os.path.join(working_dir_path, f))
      if props is None: continue
      prop_set = set(props)
      #skip non-portable files if required
      #this will tackle translated file names, like 'launch.exe' -> 'olex2.exe'
      if portable and f in external_files:
        if 'olex-port' in props and (port_props is None or len(port_props&prop_set) == 0):
            continue
      elif (enforce_only_prop or f not in all_zip_files) and\
           (only_prop and len(only_props&prop_set) == 0):
        continue
      if portable:
        portable_files.add(normalised_root_dir + f)
      if d:
        toks = d.split('/')
      else:
        toks = []
      toks.append(f)
      root_entry.FromStrList(toks, props, stats, False)
  root_entry.SaveToFile(idx_file)
  idx_file.close()
  return portable_files
#####################################################################################################
#end of index management procedures
#create a global index file
zip_index_file_name = update_directory + '/zindex.ind'
create_index(update_directory + '/index.ind')
#create olex2.tag file
web_directory = web_directory.replace('\\','/')
if web_directory.endswith('/'):
  web_directory = web_directory[:-1]
olex2_tag_file_name = web_directory+'/'+'olex2.tag'
with open(olex2_tag_file_name, 'w+') as olex2_tag_file :
  print(web_directory.split('/')[-1], file=olex2_tag_file)
#end creating the tag file
####################################################################################################
# create portable distro
def create_portable_distro(port_props, zip_name, port_zips, prefix, extra_files):
  create_index(zip_index_file_name, only_prop='olex-install', port_props=port_props, portable=True)
  inst_files = filter_installer_file(only_prop='olex-install', port_props=port_props, portable=True)
  print('Creating portable zip: ' + zip_name)
  dest_zip = zipfile.ZipFile(web_directory + '/' + zip_name,
                              mode='w', compression=zipfile.ZIP_DEFLATED)
  for f in inst_files:
    dest_zip.write(f, zip_destination(f, prefix))
  if prefix is None:  prefix = ''
  dest_zip.write(zip_index_file_name, prefix + 'index.ind')
  dest_zip.write(olex2_tag_file_name, prefix + 'olex2.tag')
  #process zip files - just extract - to add to the zip file
  for zip_name in port_zips:
    print('Appending ' + zip_name + '...')
    src_zip = zipfile.ZipFile(bin_directory + '/' + zip_name, 'r')
    for zip_info in src_zip.infolist():
      zi = zipfile.ZipInfo(prefix + zip_info.filename)
      zi.date_time = zip_info.date_time
      zi.compress_type = zipfile.ZIP_DEFLATED
      zi.external_attr = 0o775 << 16 # it is NEEDED on Linux and Mac
      dest_zip.writestr(zi, src_zip.read(zip_info.filename) )
    src_zip.close()
  if extra_files:
    for k,v in extra_files.items():
      dest_zip.write(k, v)
  dest_zip.close()
  return

threads = []
####################################################################################################
if platforms.get("win32"):
  t = threading.Thread(target=create_portable_distro,
    kwargs={
      "port_props": set([win32_sse2_port_name,win32_port_name]),
      "zip_name": win32_sse2_port_zip_name,
      "port_zips": win32_sse2_zip_files,
      "prefix": win32_sse2_port_prefix,
      "extra_files":
      {
        bin_directory + '/VC_redist.x86.exe' : 'vcredist_x86.exe'
      }
    }
  )
  threads.append(t)
if platforms.get("win64"):
  t = threading.Thread(target=create_portable_distro,
    kwargs={
      "port_props": set([win64_port_name]),
      "zip_name": win64_port_zip_name,
      "port_zips": win64_zip_files,
      "prefix": win64_port_prefix,
      "extra_files":
      {
        bin_directory + '/VC_redist.x64.exe' : 'vcredist_x64.exe'
      }
    }
  )
  threads.append(t)
#create linux and mac distro only in releases
if platforms.get("lin64"):
  t = threading.Thread(target=create_portable_distro,
    kwargs={
      "port_props": set([linux64_port_name]),
      "zip_name": linux64_port_zip_name,
      "port_zips": linux64_zip_files,
      "prefix": linux64_port_prefix,
      "extra_files":
      {
        bin_directory + '/linux-distro/start' : 'olex2/start',
        bin_directory + '/linux-distro/usettings64.dat' : 'olex2/usettings.dat'
      }
    }
  )
  threads.append(t)
if platforms.get("mac64"):
  t = threading.Thread(target=create_portable_distro,
    kwargs={
      "port_props": set([mac64_port_name]),
      "zip_name": mac64_port_zip_name,
      "port_zips": mac64_zip_files,
      "prefix": mac64_port_prefix,
      "extra_files":
      {
        bin_directory + '/mac-distro/Info.plist' : 'olex2.app/Contents/Info.plist',
        bin_directory + '/mac-distro/PkgInfo' : 'olex2.app/Contents/PkgInfo',
        bin_directory + '/mac-distro/usettings64.dat' : 'olex2.app/Contents/MacOS/usettings.dat',
        bin_directory + '/mac-distro/olex2.icns' : 'olex2.app/Contents/Resources/olex2.icns'
      }
    }
  )
  threads.append(t)

run_threads(threads)

#init plugin relations
plugins_to_del = set()
for p1, f1 in list(files_for_plugin.items()):
  p1_toks = p1.split('-')
  for p2, f2 in list(files_for_plugin.items()):
    p2_toks = p2.split('-')
    if len(p2_toks) <= len(p1_toks): continue
    matches = True
    for i in range(len(p1_toks)):
      if p2_toks[i] != p1_toks[i]:
        matches = False
        break
    if not matches: continue
    f2 += f1
    plugins_to_del.add(p1)
for p in plugins_to_del:
  del files_for_plugin[p]
#create plugin zips with indexes
plugin_index_file_name = update_directory + 'plugin.ind'
for plugin, files in list(files_for_plugin.items()):
  plugin_zip = zipfile.ZipFile(web_directory + '/' + plugin + '.zip', 'w', compression=zipfile.ZIP_DEFLATED)
  for f in files:
    plugin_zip.write(destination(f,'update'), zip_destination(f))

  props = []
  p_toks = plugin.split('-')
  while len(p_toks) != 0:
    props.append('plugin-'+'-'.join(p_toks))
    del p_toks[len(p_toks)-1]
  create_index(zip_index_file_name, only_prop=';'.join(props), enforce_only_prop=True)
  plugin_zip.write(zip_index_file_name, 'index.ind')
  plugin_zip.close()
if os.path.exists(plugin_index_file_name):
  os.remove(plugin_index_file_name)
#end of the plugin zips creation

#delete the temporary index file
os.unlink(zip_index_file_name)

update_tags_file(web_directory)

print('Done')