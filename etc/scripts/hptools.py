import os
import glob
import olx
import olex
import time

from olexFunctions import OlexFunctions
OV = OlexFunctions()

from ImageTools import ImageTools
IT = ImageTools()

import olex_core

import OlexVFS


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

class HealthOfStructure():
  def __init__(self):
    self.hkl_stats = {}
    phil_file = "%s\etc\CIF\diagnostics.phil" %(OV.BaseDir())
    olx.phil_handler.adopt_phil(phil_file=phil_file)

  def run_HealthOfStructure(self):
    self.hkl_stats = olex_core.GetHklStat()
    self.make_HOS_html()
    
  def make_HOS_html(self):
    txt = "<tr><table width='100%%'><tr>"
    l = ['MeanIOverSigma','Rint']
    for item in l:
      bg_colour = self.get_bg_colour(item)
      display = OV.GetParam('diagnostics.hkl.%s.display' %item)
      value_format = OV.GetParam('diagnostics.hkl.%s.value_format' %item)
      value = self.hkl_stats[item]
      if "%" in value_format:
        value_format = value_format.replace('%','f%%')
        value = value * 100
      value_format = "%." + value_format
      value = value_format %value
      txt += '''
  <td bgcolor=%s align='center' width='%s%%'><font color='#ffffff'>
    %s: <b>%s</b>
  </font></td>
'''%(bg_colour, 100/len(l), display, value)
      
    txt += "</tr></table></tr>"
    txt = txt.decode('utf-8')
    OV.write_to_olex("hos.htm" , txt)
    
  def get_bg_colour(self, item):
    op = OV.GetParam('diagnostics.hkl.%s.op' %item)
    val = self.hkl_stats[item]
    for i in xrange(4):
      i += 1
      if op == "greater":
        if val >= OV.GetParam('diagnostics.hkl.%s.grade%s' %(item, i)):
          break
      elif op == 'smaller':
        if val <= OV.GetParam('diagnostics.hkl.%s.grade%s' %(item, i)):
          break
      
    if i == 1:
      retVal = '#3dbe10'
    elif i == 2:
      retVal = '#b4be10'
    elif i == 3:
      retVal = '#d6a113'
    elif i == 4:
      retVal = '#d62613'
      
    return retVal
    
HealthOfStructure_instance = HealthOfStructure()
OV.registerFunction(HealthOfStructure_instance.run_HealthOfStructure)
  