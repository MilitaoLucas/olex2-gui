#!/usr/bin/python

""" Olex 2 distro management """
# these to specify to create separate zip files
plugins = ('mysql', 'cctbx-win', 'brukersaint', 'ODSkin', 'BNSkin', 'STOESkin', 'HPSkin', 'Batch', 'Pysvn', 'Crypto', 'AutoChem') 
# file name aliases
web_for_working = {'olex2.exe': 'olex2.dll', 'launch.exe': 'olex2.exe'}
# alterations for binary files : name (properties...)
alterations = {
  'olex2.exe': ('olex-install', 'olex-update'), 
  'olex2c.exe': ('olex-install', 'olex-update'),
  'launch.exe': ('olex-install', 'olex-update'),
  'Python26.zip': ('olex-install', 'olex-update', 'action:extract'),
  #'python25.dll': ('olex-install', 'olex-update'),
  #'msvcr71.dll': ('olex-install', 'olex-update'),
  'splash.jpg': ('olex-install', 'olex-update'),
  'acidb.db': ('olex-install', 'olex-update'),
  'installer.exe': ('olex-top',), #mind the comma!
  'Microsoft.VC90.CRT/Microsoft.VC90.CRT.manifest': ('olex-install', 'olex-update'),
  'Microsoft.VC90.CRT/msvcm90.dll': ('olex-install', 'olex-update'),
  'Microsoft.VC90.CRT/msvcp90.dll': ('olex-install', 'olex-update'),
  'Microsoft.VC90.CRT/msvcr90.dll': ('olex-install', 'olex-update'),
  'etc/Fonts/olex2.fnt': ('olex-install', 'olex-update'),
  'etc/gui/fonts/Vera.ttf': ('olex-install', 'olex-update'),
  'etc/gui/fonts/VeraBd.ttf': ('olex-install', 'olex-update'),
  'etc/gui/fonts/VeraBI.ttf': ('olex-install', 'olex-update'),
  'etc/gui/fonts/VeraIt.ttf': ('olex-install', 'olex-update'),
  'etc/gui/fonts/VeraSe.ttf': ('olex-install', 'olex-update'),
  'etc/gui/fonts/VeraSeBd.ttf': ('olex-install', 'olex-update'),
  'olex2-mac.zip': ('olex-port', 'port-mac', 'action:extract'),
  'olex2-suse101x32.zip': ('olex2-suse101x32.zip', 'olex-port', 'port-suse101x32', 'action:extract'),
}
# special zip files {zip_name: (destination_dir, properties_to_set) }
zip_files = {
  'cctbx_winxp.zip': ('/util/pyUtil/CctbxLib/cctbx_win', 'cctbx-win'),
  'Python26.zip': ( '/Python26', 'olex-install', 'olex-update', 'action:extract'),
}
altered_files = set([])
altered_dirs = set([])

import os.path
from optparse import OptionParser
import pysvn
import cStringIO
import zipfile
import shutil
import itertools
import re
import time

working_for_web = dict(zip(web_for_working.values(),
                           web_for_working.keys()))

def translate_working_to_web(path):
  name = os.path.basename(path)
  name = web_for_working.get(name, name)
  return os.path.join(os.path.dirname(path), name)

def filter_out_directories(seq):
  return [ p for p in seq if not os.path.isdir(p) ]

def destination(working_path, sub_web_directory=None):
  dst = web_directory
  if sub_web_directory is not None:
    dst += '/' + sub_web_directory
  return translate_working_to_web(
    working_path.replace(working_directory, dst))

def zip_destination(working_path):
  return translate_working_to_web(
    working_path.replace(working_directory + '/', ''))

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
parser.add_option('--test',
		  dest='test',
		  action='store_true',
		  help='whether to use the normal or the test web directory')
parser.add_option('--alpha',
		  dest='alpha',
		  action='store_true',
		  help='whether to use the normal or the alpha web directory')
parser.add_option('-f', '--file',
		  dest='update_file',
                  default='',
		  action='store',
		  help='whether to use update any particular file only')
option, args = parser.parse_args()

working_directory = os.path.expanduser(option.working_directory
				       or 'e:/tmp/test-svn')
if not os.path.isdir(working_directory):
  print "ERROR: '%s' is not a directory" % working_directory
  parser.print_help()

web_directory = os.path.expanduser(option.web_directory
				   or 'e:/tmp/web')
bin_directory = os.path.expanduser(option.bin_directory
                                   or 'e:/tmp/bin-test')
if not os.path.isdir(bin_directory):
  print "ERROR: '%s' is not a directory" % bin_directory
  parser.print_help()
  #os.abort()
  
if option.test: web_directory += '-test'
elif option.alpha: web_directory += '-alpha'
if not os.path.isdir(os.path.dirname(web_directory)):
  print "ERROR: '%s' is not a directory" % working_directory
  parser.print_help()

# remove the files from the repository: helps to find collisions
for val, key in alterations.iteritems():
  fn = working_directory + '/' + val
  if os.path.exists(fn):
    os.unlink(fn) 
    print "Binary distribution file removed: " + fn

client = pysvn.Client()

try:
  if option.update_file:
    filepath = option.update_file
    print 'Updating %s only...' %filepath
    n = client.update(working_directory + filepath)
    revision_number = n[0].number
    print "SVN Revision Number %i" %revision_number
  elif True:  #debugging can set it to false to leave the folder intact
    n = client.update(working_directory)
    revision_number = n[0].number
    print "SVN Revision Number %i" %revision_number
    wFile = open("%s/version.txt" %working_directory, 'w')
    wFile.write("SVN Revision No. %s" %revision_number)
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
files_for_zips = {}
for zip_name, args in zip_files.items():
  files_for_zips.setdefault(
    zip_name,
    [working_directory + zip_files[zip_name][0] + '/' + name
     for name in zipfile.ZipFile(bin_directory + '/' + zip_name).namelist()
     if not name.endswith('/')]) 

cctbx_directory = working_directory + '/util/pyUtil/CctbxLib/cctbx_win'
cctbx_zip_file = zipfile.ZipFile('%s/cctbx_winxp.zip'
                                 % bin_directory)
files_for_plugin['cctbx-win'].extend([ cctbx_directory + '/' + name 
                                   for name in cctbx_zip_file.namelist() 
                                   if not name.endswith('/') ])

# process binary files, new folders might get created, so the call is before creating dirs
for val, key in alterations.iteritems():
  fn = working_directory + '/' + val
  if os.path.exists(fn):
    print "File exist both on the svn and in the binary folder '" + fn + "' skipping..."
    continue
  if not os.path.exists(bin_directory + '/' + val):
    print "Specified binary file does not exist '" + val + "' skipping..."
    os._exit(1)
  for i in range(0, len(key)):
    if key[i] == 'olex-update' or key[i] == 'olex-port':
      update_files.append(fn)
    elif key[i] == 'olex-install':
      installer_files.append(fn)
    elif key[i] == 'olex-top':
      top_files.append(fn)
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
for files_dict in [files_for_plugin, files_for_zips]:
  directories_to_create.update(dict(
    [ (os.path.dirname(destination(p, 'update')), 1)
      for p in itertools.chain(update_files, *files_dict.values()) ]))
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

for zip_name, files in files_for_zips.items():
  zip_file = zipfile.ZipFile(bin_directory + '/' + zip_name)
  destination_directory = working_directory + zip_files[zip_name][0] + '/'
  for f in files:
    name = destination(f, 'update')
    f1 = open(name, 'wb')
    f_zip = f.replace(destination_directory, '')
    f1.write(zip_file.read(f_zip))
    f1.close()
    t = time.mktime(zip_file.getinfo(f_zip).date_time + (0,1,-1))
    os.utime(name, (t,t))

# create the index file
def info(web_file_name, working_file_name):
  stats = os.stat(web_file_name)
  stats = (stats.st_mtime, stats.st_size)
  #override the svn properties with the ones defined above
  normalised_fn = working_file_name.replace('\\', '/')
  if normalised_fn in altered_files:
    normalised_fn = normalised_fn.replace(working_directory + '/', '')    
    props = alterations.get(normalised_fn)
  else:    
    try:
      props = client.proplist(working_file_name)
      if props:
        props = tuple([ k for k in props[0][1].keys() if 'svn:' not in k ])
      else:
        props = ()
    except:
      if 'cctbx' in working_file_name:
        props = ('plugin-cctbx-win',)
      else:
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
  return "%i,%i,{%s}" % (stats+(props,))

def create_index(index_file_name, only_prop=None):
  idx_file = open(index_file_name, 'w')
  for dir_path, dir_names, file_names in os.walk(update_directory):
    dir_names[:] = [ d for d in dir_names if not d.startswith('.') ]
    file_names[:] = [ d for d in file_names if not d.startswith('.') or d == ".version" ]
    dir_path = dir_path.replace('\\', '/')    
    d = update_directory_pat.sub('', dir_path)
    indents = "\t"*d.count('/')
    working_dir_path = os.path.join(os.path.normpath(working_directory), d)
    if d:
      stats, props = info(dir_path, working_dir_path)
      if props is None: 
        dir_names[:] = []
        file_names[:] = []
        continue
      print >> idx_file, indents + os.path.basename(d)
      print >> idx_file, indents + format_info(stats, props)
      indents += '\t'
    for f in file_names:
      stats, props = info(os.path.join(dir_path, f),
                          os.path.join(working_dir_path,
                                       working_for_web.get(f,f)))
      if props is None: continue
      if only_prop is not None and only_prop not in props: continue
      print >> idx_file, indents + f
      print >> idx_file, indents + format_info(stats, props)
  idx_file.close()

create_index(update_directory + '/index.ind')
zip_index_file_name = update_directory + '/zindex.ind'
create_index(zip_index_file_name, only_prop='olex-install')

# create the zip archives
olex2_zip = zipfile.ZipFile(web_directory + '/olex2.zip',
                            mode='w', compression=zipfile.ZIP_DEFLATED)
for f in installer_files:
  olex2_zip.write(f, zip_destination(f))
olex2_zip.write(zip_index_file_name, 'index.ind')
olex2_zip.close()

for plugin, files in files_for_plugin.items():
  plugin_zip = zipfile.ZipFile(web_directory + '/' + plugin + '.zip', 'w')
  for f in files:
    if plugin == 'cctbx-win' and not os.path.exists(f):
      f_zip = f.replace(cctbx_directory + '/', '')
      f_zip_info = cctbx_zip_file.getinfo(f_zip)
      f_zip_info.filename = zip_destination(f)
      plugin_zip.writestr(
	f_zip_info,
	cctbx_zip_file.read(f_zip))
    else:
      plugin_zip.write(destination(f,'update'),
		       zip_destination(f))
  plugin_zip.close()
