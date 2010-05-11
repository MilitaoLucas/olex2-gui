#!/usr/bin/python

""" Olex 2 distro management """
# these to specify to created separate zip files
plugins = ('MySQL', 'Batch', 'Crypto', 'ODAC', 'Headless', 'Olex2Portal') 
#available ports
# alteartions for binary files : name (properties...), olex-port MUST be specified for non-portable files
mac_port_name = 'port-mac-intel-py26'
mac_port_zip_name = 'mac-intel-py26.zip'
mac_port_prefix = 'olex2.app/Contents/MacOS/'

suse_port_name = 'port-suse101x32-py26'
suse_port_zip_name = 'suse101x32-py26.zip'
suse_port_prefix = 'olex2/'

win_port_name = 'port-win32-portable'
win_sse2_port_name = 'port-win32'
win_sse2_port_zip_name = 'olex2.zip'
win_sse2_port_prefix = None

win64_port_name = 'port-win64'
win64_port_zip_name = 'olex2-x64.zip'
win64_port_prefix = None

win_sse_port_name = 'port-win32-sse'
win_sse_port_zip_name = 'olex2-sse.zip'
win_sse_port_prefix = None

portable_zip_name = 'portable-gui.zip'
portable_prefix = None
# iteratable list of zips and prefixes
distro_zips = (
  (mac_port_zip_name, mac_port_prefix), 
  (suse_port_zip_name, suse_port_prefix), 
  (win_sse_port_zip_name, win_sse_port_prefix),
  (win_sse2_port_zip_name, win_sse2_port_prefix),
  (win64_port_zip_name, win64_port_prefix),
  (portable_zip_name, portable_prefix)
)

external_files = {
  #windows installer files
  'installer.exe': ('olex-top',), #mind the comma!
  'installer_64.exe': ('olex-top',),
  #mac
  'olex2-mac.zip': ('olex-port', mac_port_name, 'action:extract', 'action:delete'),
  'unirun-mac.zip': ('olex-port', mac_port_name, 'action:extract', 'action:delete'),
  'cctbx-mac.zip': ('olex-port', mac_port_name, 'action:extract', 'action:delete'),
  'python26-mac.zip': ('olex-port', mac_port_name, 'action:extract', 'action:delete'),
  #linux
  'olex2-suse101x32.zip': ('olex-port', suse_port_name, 'action:extract', 'action:delete'),
  'unirun-suse101x32.zip': ('olex-port', suse_port_name, 'action:extract', 'action:delete'),
  'cctbx-suse101x32.zip': ('olex-port', suse_port_name, 'action:extract', 'action:delete'),
  'python26-suse101x32.zip': ('olex-port', suse_port_name, 'action:extract', 'action:delete'),
  'lib-suse101x32.zip': ('olex-port', suse_port_name, 'action:extract', 'action:delete'),
  #windows 
  'launch_exe.zip': ('olex-port', win_port_name,  'action:extract', 'action:delete'),
  'python26.zip': ('olex-port', win_port_name, 'action:extract', 'action:delete'),
  #SSE2
  'cctbx.zip': ('olex-port', win_sse2_port_name, 'action:extract', 'action:delete'),
  'olex2_exe.zip': ('olex-port', win_sse2_port_name, 'action:extract', 'action:delete'),
  #windows SSE vc SSE2
  'cctbx_sse.zip': ('olex-port', win_sse_port_name, 'action:extract', 'action:delete'),
  'olex2_exe_sse.zip': ('olex-port', win_sse_port_name, 'action:extract', 'action:delete'),
  #windows 64
  'launch_exe_64.zip': ('olex-port', win64_port_name, 'action:extract', 'action:delete'),
  'python26_64.zip': ('olex-port', win64_port_name, 'action:extract', 'action:delete'),
  'cctbx_64.zip': ('olex-port', win64_port_name, 'action:extract', 'action:delete'),
  'olex2_exe_64.zip': ('olex-port', win64_port_name, 'action:extract', 'action:delete'),
  #portables
  'olex2_fonts.zip': ('olex-update', 'action:extract', 'action:delete'),
  'fonts.zip': ('olex-update', 'action:extract', 'action:delete'),
  'acidb.zip': ('olex-update', 'action:extract', 'action:delete'),
  'splash.jpg': ('olex-install', 'olex-update'),
  'version.txt': ('olex-install', 'olex-update'),
  'dictionary.txt': ('olex-install', 'olex-update'),
  'odac_update.txt': ('olex-install', 'olex-update'),
  #plugins, no solution for portable plugins yet
  'olex2c.exe': ('olex-port', 'plugin-Headless')
}
# special zip files (must have relevant structure), must exist ABOVE as well!!
#if the associated value is false - the file is non-portable and will not end up in the portable-gui.zip
portable_zip_files = \
set(  ['olex2_fonts.zip',
       'fonts.zip',
       'acidb.zip'
      ]
   )
win_sse2_zip_files = \
set(  ['cctbx.zip',      #cctbx/cctb_sources,...
      'python26.zip',    #Pyhton26/..., ..., + python26.dll!!!
      'launch_exe.zip',  #olex2.exe
      'olex2_exe.zip'   #olex2.dll, it will be veryfied first of all
      ]    
   ) | portable_zip_files
win_sse_zip_files = \
set(  ['cctbx_sse.zip',    #cctbx/cctb_sources,...
      'python26.zip',      #Pyhton26/..., ..., + python26.dll!!!
      'launch_exe.zip',    #olex2.exe
      'olex2_exe_sse.zip'  #olex2.dll
      ]    
   ) | portable_zip_files
win64_zip_files = \
set(  ['cctbx_64.zip',     #cctbx/cctb_sources,...
      'python26_64.zip',   #Pyhton26/..., ..., + python26.dll!!!
      'olex2_exe_64.zip',  #olex2.dll
      'launch_exe_64.zip'  #olex2.exe
      ]    
   ) | portable_zip_files
mac_zip_files = \
set(  ['cctbx-mac.zip',  #cctbx/cctb_sources,...
      'python26-mac.zip',#Pyhton26/..., ..., + python26 dlls
      'olex2-mac.zip',    #olex2 executable
      'unirun-mac.zip'
      ]    
   ) | portable_zip_files

suse_zip_files = \
set(  ['cctbx-suse101x32.zip',  #cctbx/cctb_sources,...
      'python26-suse101x32.zip',#Pyhton26/..., ..., + python26 dlls
      'lib-suse101x32.zip',     #lib/dlls
      'olex2-suse101x32.zip',    #olex2 executable
      'unirun-suse101x32.zip'
      ]    
   ) | portable_zip_files
# a set of all zip files...
all_zip_files = win_sse2_zip_files | win_sse_zip_files | win64_zip_files | mac_zip_files | suse_zip_files

altered_files = set([])
altered_dirs = set([])

import os.path
import sys
from optparse import OptionParser
import pysvn
import cStringIO
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
parser.add_option('--revert',
		  dest='revert',
		  action='store_true',
		  help='whether to revert vs promoting a distribution')
parser.add_option('-f', '--file',
		  dest='update_file',
                  default='',
		  action='store',
		  help='whether to use update any particluare file only')
option, args = parser.parse_args()
	
working_directory = os.path.expanduser(option.working_directory
				       or 'e:/tmp/test-svn')
if not os.path.isdir(working_directory):
  print "ERROR: '%s' is not a directory" % working_directory
  parser.print_help()

web_directory = os.path.expanduser(option.web_directory
				   or 'e:/tmp/1.0')
bin_directory = os.path.expanduser(option.bin_directory
                                   or 'e:/tmp/bin_dir')
if not os.path.isdir(bin_directory):
  print "ERROR: '%s' is not a directory" % bin_directory
  parser.print_help()
  #os.abort()

# update tags file, the web_dir is transformed to correct form when creating olex2.tag file
def update_tags_file(dir):
  up_dir = '/'.join(dir.split('/')[:-1])
  tags = os.listdir(up_dir)
  tags_file = open(up_dir + '/tags.txt', 'w')
  for dir in tags:
    if dir != '.' and os.path.isdir(up_dir+'/'+dir):
      if not os.path.exists(up_dir+'/'+dir+'/olex2.tag'):
        print 'Skipping invalid TAG folder: ' + dir
        continue
      print >> tags_file, dir
  tags_file.close()
  
def is_distro_uptodate(src, dest):
  if not os.path.exists(src) or not os.path.exists(dest):
    return False
  src_mt = os.path.getmtime(src)
  dest_mt = os.path.getmtime(dest)
  return src_mt - dest_mt < 5 # 5 seconds
  
def promote_distro(src, dest, forward=True):
  if not os.path.exists(src):
    print "Source distribution does not exist, exiting..."
    sys.exit(0)
  if os.path.exists(dest): 
    if forward:
      if is_distro_uptodate(src, dest):
        print 'Destination repository is newer than the source one or up-to-date, exiting'
        sys.exit(0)
    else:
      if is_distro_uptodate(dest, src):
        print 'Destination repository is older than the source one or up-to-date, exiting'
        sys.exit(0)
    shutil.rmtree(dest)
    shutil.copytree(src, dest)
  else:
    shutil.copytree(src, dest)
  # update the tag files...
  dest = dest.replace('\\','/')
  if dest.endswith('/'):  dest = dest[:-1]
  tag_file_name = dest+'/'+'olex2.tag'
  tag_file = open(tag_file_name, 'w+b')
  print >> tag_file, dest.split('/')[-1]
  tag_file.close()
  #end creating the tag file
  for zipfi in distro_zips:
    print 'Updating ' + zipfi[0] + '...'
    src_zfile = zipfile.ZipFile(dest + '/' + zipfi[0], mode='r', compression=zipfile.ZIP_DEFLATED)
    dest_zfile = zipfile.ZipFile(dest + '/' + zipfi[0] + '_', mode='w', compression=zipfile.ZIP_DEFLATED)
    prefix = zipfi[1]
    if not prefix:  prefix = ''
    zip_tag_name = prefix + 'olex2.tag'
    for zi in src_zfile.infolist():
      if zi.filename == zip_tag_name:
        dest_zfile.write(tag_file_name, zip_tag_name) 
      else:  
        dest_zfile.writestr(zi, src_zfile.read(zi.filename)) 
    src_zfile.close()
    dest_zfile.close()
    os.remove(dest + '/' + zipfi[0]);
    os.rename(dest + '/' + zipfi[0] + '_', dest + '/' + zipfi[0])
  update_tags_file(src)
  sys.exit(0)
# do the promotion of alpha->beta->release, only alpha can be re-released
if option.beta:
  if option.revert:
    print 'Reverting release distro to beta'
    promote_distro(web_directory, web_directory + '-beta')
  else:
    print 'Promoting alpha distro to beta'
    promote_distro(web_directory + '-alpha', web_directory + '-beta')
elif option.alpha: 
  if option.revert:
    print 'Reverting beta distro to alpha'
    promote_distro(web_directory+ '-beta', web_directory + '-alpha', forward=False)
  else:
    web_directory += '-alpha'
    print 'Creating alpha distro...'
else:
  if not is_distro_uptodate(web_directory + '-alpha', web_directory + '-beta'):
    print 'Beta distro is not up-to-date, aborting'
    sys.exit(0)
  print 'Promoting beta distro to release'
  promote_distro(web_directory + '-beta', web_directory)
  
if not os.path.isdir(os.path.dirname(web_directory)):
  print "ERROR: '%s' is not a directory" % working_directory
  parser.print_help()

# remove the files from the repository: helps to find collisions
for val, key in external_files.iteritems():
  fn = working_directory + '/' + val
  if os.path.exists(fn):
    os.unlink(fn) 
    print "Binary distribution file removed: " + fn

# create olex2_exe.zip from olex2.exe, if exists...
if os.path.exists(bin_directory + '/olex2.exe'):
  print "Updating olex2_exe.zip file..."
  olex2_exe_zip = zipfile.ZipFile(bin_directory + '/olex2_exe.zip',
                            mode='w', compression=zipfile.ZIP_DEFLATED)
  olex2_exe_zip.write(bin_directory + '/olex2.exe', 'olex2.dll')
  olex2_exe_zip.close()
  os.remove(bin_directory + '/olex2.exe')
#validate the olex2_exe.zip file

olex2_exe_zip = zipfile.ZipFile(bin_directory + '/olex2_exe.zip', 'r')
if 'olex2.dll' not in olex2_exe_zip.namelist():
  print 'olex2_exe file should contain olex2.dll file, aborting...'
  olex2_exe_zip.close()
  sys.exit(1)
olex2_exe_zip.close()
#end executable zip file validation and creation
  
client = pysvn.Client()

try:
  if option.update_file:
    filepath = option.update_file
    print 'Updating %s only...' %filepath
    n = client.update(working_directory + filepath)
    revision_number = n[0].number
    print "SVN Revision Number %i" %revision_number
  elif True:  #defuging can set it to false to leave the folder in tact
    n = client.update(working_directory)
    revision_number = n[0].number
    print "SVN Revision Number %i" %revision_number
    nv_line = "SVN Revision No. %s" %revision_number
    same_version = False
    if os.path.exists(bin_directory + '/version.txt'):
      ev_file = open(bin_directory + '/version.txt', 'rb')
      ev_line = ev_file.readline()
      same_version = (ev_line == nv_line)
    if not same_version:
      wFile = open("%s/version.txt" %bin_directory, 'w')
      wFile.write(nv_line)
      wFile.close()
#  revnum = pysvn.Revision( pysvn.opt_revision_kind.working )
#  print revnum.number
except pysvn.ClientError, err:
  if str(err).find('locked'):
    client.cleanup(working_directory)
    if option.update_file:
      client.update(working_directory + '/' + option.update_file)
    else:
      client.update(working_directory)
  else:
    print "ERROR: %s" % err
    parser.print_help()
  
# gather files and put them in different groups
top_files = filter_out_directories(
  client.propget('olex-top', working_directory, recurse=True).keys())

update_files = filter_out_directories(
  client.propget('olex-update', working_directory, recurse=True).keys()) +\
filter_out_directories(
  client.propget('olex-port', working_directory, recurse=True).keys())

installer_files = filter_out_directories(
  client.propget('olex-install', working_directory, recurse=True).keys())
files_for_plugin = dict(
  [ (plugin,
     filter_out_directories(
       client.propget('plugin-%s'%plugin, working_directory,
		      recurse=True).keys())
     )
     for plugin in plugins ])

# process binary files, new folders might get created, so the call is before creating dirs
for val, key in external_files.iteritems():
  fn = working_directory + '/' + val
  if os.path.exists(fn):
    print "File exist both on the svn and in the binary folder '" + fn + "' skipping..."
    continue
  if not os.path.exists(bin_directory + '/' + val):
    print "Specified binary file does not exist '" + val + "' aborting..."
    os._exit(1)
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
  shutil.copy2( bin_directory + '/' + val, working_directory + '/' + val);
  altered_files.add(fn)

# create web directory structure (top + update)
shutil.rmtree(web_directory, ignore_errors=True)
directories_to_create = {web_directory: 1}
directories_to_create.update(dict(
  [ (os.path.dirname(destination(p, 'update')), 1) 
    for p in itertools.chain(update_files, *files_for_plugin.values()) ]))
directories_to_create = directories_to_create.keys()
directories_to_create.sort()
for d in directories_to_create:
  os.makedirs(d)
update_directory = web_directory + '/update'
update_directory_pat = re.compile(update_directory + '/?')
    
# copy files into the web directory
for f in top_files:
  shutil.copy2(f, destination(f))
for f in itertools.chain(update_files, 
			 *[ files_for_plugin[x] for x in files_for_plugin
                            if x != 'cctbx-win' ]):
  if os.path.exists(f):  
    shutil.copy2(f, destination(f, 'update'))
  else:
    print "Invalid file '" + f + "' skipping"

# create the index file
def info(web_file_name, working_file_name):
  stats = os.stat(web_file_name)
  if os.path.isfile(web_file_name):
    _file = file(web_file_name, "rb")
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
        props = tuple([ k for k in props[0][1].keys() if 'svn:' not in k ])
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
    for item in self.items.itervalues():
      cnt += item.ItemCount()
    return cnt;
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
      print >> idx_file, indent + self.name
      print >> idx_file, indent + format_info(self.stats, self.props)
      indent += '\t'
    for item in self.items.itervalues():
      item.SaveToFile(idx_file, indent)
  
def fileter_installer_file(only_prop=None, port_props = None, portable=False, enforce_only_prop=False):
  portable_files = set([])  
  for f in installer_files:
    stats, props = info(f, f)
    if props is None: continue
    prop_set = set(props)
    if portable and external_files.has_key(f):
      if 'olex-port' in props and (port_props is None or len(port_props&prop_set) == 0):
          continue
    elif (enforce_only_prop or f not in all_zip_files) and ((only_prop is not None) and (only_prop not in prop_set)): 
      continue
    if portable:
      portable_files.add(f)
  return portable_files
  
def create_index(index_file_name, only_prop=None, port_props = None, portable=False, enforce_only_prop=False):
  portable_files = set([])  
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
      if portable and external_files.has_key(f):
        if 'olex-port' in props and (port_props is None or len(port_props&prop_set) == 0):
            continue
      elif (enforce_only_prop or f not in all_zip_files) and ((only_prop is not None) and (only_prop not in prop_set)): 
        continue
      if portable:
        portable_files.add(normalised_root_dir + f)
      if d:      
        toks = d.split('/')
      else:
        toks = []
      toks.append(f);
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
olex2_tag_file = open(olex2_tag_file_name, 'w+b')
print >> olex2_tag_file, web_directory.split('/')[-1]
olex2_tag_file.close()
#end creating the tag file
####################################################################################################
# create portable distro
def create_portable_distro(port_props, zip_name, port_zips, prefix, extra_files):
  port_files = create_index(zip_index_file_name, only_prop='olex-install', port_props=port_props, portable=True)
  inst_files = fileter_installer_file(only_prop='olex-install', port_props=port_props, portable=True)
  print 'Creating portable zip: ' + zip_name
  dest_zip = zipfile.ZipFile(web_directory + '/' + zip_name,
                              mode='w', compression=zipfile.ZIP_DEFLATED)
  for f in inst_files:
    dest_zip.write(f, zip_destination(f, prefix))
  if prefix is None:  prefix = ''
  dest_zip.write(zip_index_file_name, prefix + 'index.ind')
  dest_zip.write(olex2_tag_file_name, prefix + 'olex2.tag')
  #process zip files - just extract - to add to the zip file 
  for zip_name in port_zips:
    print 'Appending ' + zip_name + '...'
    src_zip = zipfile.ZipFile(bin_directory + '/' + zip_name, 'r')
    for zip_info in src_zip.infolist():
      zi = zipfile.ZipInfo(prefix + zip_info.filename)
      zi.date_time = zip_info.date_time;
      zi.compress_type = zipfile.ZIP_DEFLATED
      zi.external_attr = 0775 << 16L # it is NEEDED on Linux and Mac
      dest_zip.writestr(zi, src_zip.read(zip_info.filename) )
    src_zip.close()
  if extra_files:
    for k,v in extra_files.iteritems():
      dest_zip.write(k, v)
  dest_zip.close()
  return
####################################################################################################
create_portable_distro(
  port_props=None, 
  zip_name=portable_zip_name, 
  port_zips=portable_zip_files, 
  prefix=portable_prefix,
  extra_files = None
)
create_portable_distro(
  port_props=set([win_sse2_port_name,win_port_name]), 
  zip_name=win_sse2_port_zip_name, 
  port_zips=win_sse2_zip_files, 
  prefix=win_sse2_port_prefix,
  extra_files = 
  {
    bin_directory + '/vcredist_x86.exe' : 'vcredist_x86.exe'
  }
)
create_portable_distro(
  port_props=set([win_sse_port_name,win_port_name]), 
  zip_name=win_sse_port_zip_name, 
  port_zips=win_sse_zip_files, 
  prefix=win_sse_port_prefix,
  extra_files = 
  {
    bin_directory + '/vcredist_x86.exe' : 'vcredist_x86.exe'
  }
)
create_portable_distro(
  port_props=set([win64_port_name]), 
  zip_name=win64_port_zip_name, 
  port_zips=win64_zip_files, 
  prefix=win64_port_prefix,
  extra_files = 
  {
    bin_directory + '/vcredist_x64.exe' : 'vcredist_x64.exe'
  }
)
create_portable_distro(
  port_props=set([suse_port_name]), 
  zip_name=suse_port_zip_name, 
  port_zips=suse_zip_files, 
  prefix=suse_port_prefix,
  extra_files = 
  {
    bin_directory + '/suse-distro/start' : 'olex2/start',
    bin_directory + '/suse-distro/usettings.dat' : 'olex2/usettings.dat'
  }
)
create_portable_distro(
  port_props=set([mac_port_name]), 
  zip_name=mac_port_zip_name, 
  port_zips=mac_zip_files, 
  prefix=mac_port_prefix,
  extra_files = 
  {
    bin_directory + '/mac-distro/start' : 'start',
    bin_directory + '/mac-distro/Info.plist' : 'olex2.app/Contents/Info.plist',
    bin_directory + '/mac-distro/PkgInfo' : 'olex2.app/Contents/PkgInfo',
    bin_directory + '/mac-distro/usettings.dat' : 'olex2.app/Contents/MacOS/usettings.dat'
  }
)

#create plugin zips with indexes
plugin_index_file_name = update_directory + 'plugin.ind'
for plugin, files in files_for_plugin.items():
  plugin_zip = zipfile.ZipFile(web_directory + '/' + plugin + '.zip', 'w', compression=zipfile.ZIP_DEFLATED)
  for f in files:
    plugin_zip.write(destination(f,'update'), zip_destination(f))
  create_index(zip_index_file_name, only_prop='plugin-'+plugin, enforce_only_prop=True)
  plugin_zip.write(zip_index_file_name, 'index.ind')  
  plugin_zip.close()
if os.path.exists(plugin_index_file_name):
  os.remove(plugin_index_file_name)
#end of the plugin zips creation

#delete the temporary index file
os.unlink(zip_index_file_name)

update_tags_file(web_directory)

print 'Done'

if __name__ == '__main__':
  import sys
  sys.argv.append('--beta')
