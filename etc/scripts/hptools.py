import os
import glob
import olx
import olex
import time

from olexFunctions import OlexFunctions
OV = OlexFunctions()


def bulk_copy_files (mask="hklres", path_from=r"Z:", path_to=r"C:\DS\Data",overwrite=True,lowercase=True):
  import FileSystem as FS
  
  
  path_from = OV.standardizePath(path_from)
  path_to = OV.standardizePath(path_to)
  folders = []
  p1 = os.listdir(path_from)
  for item in p1:
    folders.append(OV.standardizePath("%s/%s" %(path_from, item)))
    try:
      p2 = os.listdir("%s/%s" %(path_from, item))
      for tem in p2:
        folders.append(OV.standardizePath("%s/%s/%s" %(path_from, item, tem)))
    except:
      continue
      
  
    
  
  #for item in items:
    ##folders.append(OV.standardizePath(item.path._str))
    #path = item.path._str
    #if os.path.isdir(path):
      #folders.append(item.path._str)
   
    ##itemPath = '/'.join([path_from,item])
    ##if os.path.isdir(itemPath):
    ##folders.append(OV.standardizePath(itemPath))
      
  masks = []
  if "*" in mask:
    masks.append(mask)
  else:
    if "hkl" in mask:
      masks.append("*.hkl")
    if "ins" in mask:
      masks.append("*.ins")
    if "res" in mask:
      masks.append("*.res")
    if "lst" in mask:
      masks.append("*.lst")
      
  for folder in folders:
    print repr(folder)
    for mask in masks:
      g = glob.glob("%s/%s" %(folder,mask))
      new_folder = folder.replace(path_from,path_to)
      for file in g:
        if not os.path.exists(new_folder):
          os.makedirs(new_folder)
        try:
          FS.Node("%s" %file.lower()).copy_file((file.replace(path_from,path_to)),overwrite=overwrite)
        except:
          pass
    
  
OV.registerFunction(bulk_copy_files)


def autodemo(name='test', reading_speed=0.02):
  
  rFile = open("%s/etc/tutorials/%s.txt" %(OV.BaseDir(),name),'r')
  items = rFile.readlines()
  rFile.close()
  olx.Clear()
  for item in items:
    item = item.strip()
    cmd_type = item.split(":")[0]
    cmd_content = item.split(":")[1]
    sleep = 0
    if cmd_type == "s":
      sleep = cmd_content
    
    if cmd_type == 'p' or cmd_type == 'c':
      print "%s: %s" %(cmd_type, cmd_content)
      olx.Refresh()
      sleep = len(cmd_content) * reading_speed
    
    time.sleep(sleep)  
      
    if cmd_type == 'c':
      olex.m(cmd_content)
OV.registerFunction(autodemo)
