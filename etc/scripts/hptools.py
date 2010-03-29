import os
import glob
import olx
import olex
import time

from olexFunctions import OlexFunctions
OV = OlexFunctions()

from ImageTools import ImageTools
IT = ImageTools()

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


def autodemo(name='default_auto_tutorial', reading_speed=0.06):
  
  rFile = open("%s/etc/tutorials/%s.txt" %(OV.BaseDir(),name),'r')
  items = rFile.readlines()
  rFile.close()
  olx.Clear()
  bitmap = make_tutbox_image("Welcome", font_colour='#44aa44')
  olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
  olx.SetMaterial("%s.Plane 2053;2131693327;2131693327"%bitmap)
  olx.DeleteBitmap(bitmap)
  olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
  time.sleep(2)
  for item in items:
    item = item.strip()
    cmd_type = item.split(":")[0]
    cmd_content = item.split(":")[1]
    sleep = 0
    if cmd_type == "s":
      sleep = cmd_content
    
    if cmd_type == 'p':
      txt = "%s" %(cmd_content)
      print(txt)
      olx.DeleteBitmap(bitmap)
      bitmap = make_tutbox_image(txt)
      olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
      sleep = len(cmd_content) * reading_speed
      
    if cmd_type == 'c':
      txt = "%s: %s" %(cmd_type, cmd_content)
      print(txt)

    if cmd_type == 'h':
      control = cmd_content
      #types = ['cbtn', 'tab']
      #for t in types:
        #if t in control:
          #control_img = control
          #break
        #else:
          #control_img = "h2-%s" %control
      for i in xrange(3):
        use_image = r"%s-highlight.png" %control
        OV.SetImage(control,use_image)
        OV.Refresh()
        time.sleep(0.2)
        use_image = r"%s-on.png" %control
        OV.SetImage(control,use_image)
        OV.Refresh()
        time.sleep(0.2)
    #time.sleep(sleep)
    olx.Wait(int(sleep * 1000))
      
    if cmd_type == 'c':
      olex.m(cmd_content)

  bitmap = make_tutbox_image("Done", font_colour="#44aa44")
  olx.DeleteBitmap(bitmap)
  olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
  time.sleep(1)
  olx.DeleteBitmap(bitmap)
      
OV.registerFunction(autodemo)

def make_tutbox_image(txt='txt', font_size=20, font_colour='#aa4444', bg_colour='#fff6bf'):
  IM = IT.make_simple_text_to_image(512, 64, txt, font_size=font_size, bg_colour=bg_colour, font_colour=font_colour)
  IM.save("autotut.png")
  OlexVFS.save_image_to_olex(IM, "autotut", 0)
  return "autotut"

#  control = 'IMG_TUTBOX'
#  use_image = 'autotut.png'
#  if OV.IsControl(control):
#    olx.html_SetImage('POP_%s_PRG_ANALYSIS' %self.program.program_type.upper(), self.image_location)
#  OV.SetImage(control,use_image)
  

def tutbox(txt):
  make_tutbox_image(txt)
  name = 'Auto_Tutorial'
  txt = '<zimg border="0" name="IMG_TUTBOX" src="autotut.png">'
  wFilePath = r"%s.htm" %(name)
  txt = txt.replace(u'\xc5', 'angstrom')
  OV.write_to_olex(wFilePath, txt)

  boxWidth = 300
  boxHeight = 200
  x = 200
  y = 200
  olx.Popup(name, wFilePath, "-b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(name, boxWidth, boxHeight, x, y))
