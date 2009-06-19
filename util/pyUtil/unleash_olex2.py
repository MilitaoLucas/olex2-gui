#!/usr/bin/python

""" Olex 2 distro management """
# these to specify to created separate zip files
plugins = ('MySQL', 'brukersaint', 'ODSkin', 'BNSkin', 'STOESkin', 'HPSkin', 'Batch', 'HotshotProfiler', 'Pysvn', 'Crypto', 'AutoChem') 
# file name aliases
web_for_working = {'olex2.exe': 'olex2.dll', 'launch.exe': 'olex2.exe'}
# alteartions for binary files : name (properties...), olex-port MUST be specified for non-portable files
alterations = {'launch.exe': ('olex-install', 'olex-update', 'olex-port', 'port-win32'),
               'splash.jpg': ('olex-install', 'olex-update'),
               'version.txt': ('olex-install', 'olex-update'),
               'installer.exe': ('olex-top',), #mind the comma!
               'olex2-mac.zip': ('olex-port', 'port-mac-intel-py26', 'action:extract', 'action:delete'),
               'olex2-suse101x32.zip': ('olex-port', 'port-suse101x32-py26', 'action:extract', 'action:delete'),
               'cctbx.zip': ('olex-port', 'port-win32', 'action:extract', 'action:delete'),
               'python26.zip': ('olex-port', 'port-win32', 'action:extract', 'action:delete'),
               'msvcrt.zip': ('olex-port', 'port-win32', 'action:extract', 'action:delete'),
               'fonts.zip': ('olex-update', 'action:extract', 'action:delete'),
               'olex2_fonts.zip': ('olex-update', 'action:extract', 'action:delete'),
               'acidb.zip': ('olex-update', 'action:extract', 'action:delete'),
               'olex2_exe.zip': ('olex-port', 'port-win32', 'action:extract', 'action:delete')
               }
# special zip files (must have relevelnt structire), must exist ABOVE as well!!
#if the associated value is false - the file is non-portable and will not end up in the portable-gui.zip
zip_files = \
set(  ['cctbx.zip',       #cctbx/cctb_sources,...
      'python26.zip',    #Pyhton26/..., ..., + python26.dll!!!
      'msvcrt.zip',      #Microsoft.VCxx.CRT/Microsoft.VCxx.CRT.manifest, ..
      'fonts.zip',       #etc/gui/fonts/VeraBd.ttf, ...
      'olex2_fonts.zip', #etc/Fonts.olex2.fnt, ...
      'acidb.zip',       #acidb.zip
      'olex2_exe.zip'    #olex2.dll, it will be veryfied first of all
      ]    
   )
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
parser.add_option('--beta',
		  dest='beta',
		  action='store_true',
		  help='whether to use the normal or the tag-beta web directory')
parser.add_option('--alpha',
		  dest='alpha',
		  action='store_true',
		  help='whether to use the normal or the tag-alpha web directory')
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
				   or 'e:/tmp/web')
bin_directory = os.path.expanduser(option.bin_directory
                                   or 'e:/tmp/bin-test')
if not os.path.isdir(bin_directory):
  print "ERROR: '%s' is not a directory" % bin_directory
  parser.print_help()
  #os.abort()
  
if option.beta: web_directory += '-beta'
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

#validate the executable zip file
olex2_exe_zip = zipfile.ZipFile(bin_directory + '/' + 'olex2_exe.zip', 'r')
if 'olex2.dll' not in olex2_exe_zip.namelist():
  print 'olex2_exe file should contain olex2.dll file, aborting...'
  olex2_exe_zip.close()
  sys.exit(1)
olex2_exe_zip.close()
#end executable zip file validation
  
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
    wFile = open("%s/version.txt" %bin_directory, 'w')
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

# process binary files, new folders might get created, so the call is before creating dirs
for val, key in alterations.iteritems():
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

def create_index(index_file_name, only_prop=None, portable=False):
  portable_files = set([])  
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
    normalised_root_dir = working_dir_path.replace('\\', '/')
    if normalised_root_dir[-1] != '/':
      normalised_root_dir += '/'
    for f in file_names:
      stats, props = info(os.path.join(dir_path, f),
                          os.path.join(working_dir_path,
                                       working_for_web.get(f,f)))
      if props is None: continue
      #skip non-portable files if required
      #this will tackle translated file names, like 'launch.exe' -> 'olex2.exe'
      if portable and alterations.has_key(working_for_web.get(f,f)):
        if 'olex-port' in props:
          continue
      elif f not in zip_files and (only_prop is not None and only_prop not in props): 
        continue
      if portable:
        portable_files.add(normalised_root_dir + f)
      print >> idx_file, indents + f
      print >> idx_file, indents + format_info(stats, props)
      
  idx_file.close()
  return portable_files

create_index(update_directory + '/index.ind')
zip_index_file_name = update_directory + '/zindex.ind'
create_index(zip_index_file_name, only_prop='olex-install')

# create the zip archives
olex2_zip = zipfile.ZipFile(web_directory + '/olex2.zip',
                            mode='w', compression=zipfile.ZIP_DEFLATED)
for f in installer_files:
  olex2_zip.write(f, zip_destination(f))
olex2_zip.write(zip_index_file_name, 'index.ind')

#process zip files - just extract - to add to the zip file 
for zip_name in zip_files:
  zip_file = zipfile.ZipFile(bin_directory + '/' + zip_name, 'r')
  for zip_info in zip_file.infolist():
    olex2_zip.writestr( zip_info.filename, zip_file.read(zip_info.filename) )

olex2_zip.close()

portable_files = create_index(zip_index_file_name, only_prop='olex-install', portable=True)

# create the zip archives for portable GUI
portable_gui_zip = zipfile.ZipFile(web_directory + '/portable-gui.zip',
                            mode='w', compression=zipfile.ZIP_DEFLATED)
for f in installer_files:
  if f not in portable_files:
    continue
  portable_gui_zip.write(f, zip_destination(f))
portable_gui_zip.write(zip_index_file_name, 'index.ind')
#process zip files - just extract - to add to the zip file 
for zip_name in zip_files:
  if 'olex-port' in alterations[zip_name]:
    print 'Skipping non-portable zip file: ' + zip_name
    continue
  zip_file = zipfile.ZipFile(bin_directory + '/' + zip_name, 'r')
  for zip_info in zip_file.infolist():
    portable_gui_zip.writestr( zip_info.filename, zip_file.read(zip_info.filename) )

portable_gui_zip.close()
#delete the temporary index file
os.unlink(zip_index_file_name)

for plugin, files in files_for_plugin.items():
  plugin_zip = zipfile.ZipFile(web_directory + '/' + plugin + '.zip', 'w')
  plugin_zip.write(destination(f,'update'), zip_destination(f))
  plugin_zip.close()

# update tags file
web_directory = web_directory.replace('\\','/')
if web_directory.endswith('/'):
  web_directory = web_directory[:-1]
up_dir = '/'.join(web_directory.split('/')[:-1])
tags = os.listdir(up_dir)
tags_file = open(up_dir + '/tags.txt', 'w')
for dir in tags:
  if dir != '.' and os.path.isdir(up_dir+'/'+dir):
    print >> tags_file, dir
tags_file.close()
#
  
if __name__ == '__main__':
  import sys
  sys.argv.append('--beta')
