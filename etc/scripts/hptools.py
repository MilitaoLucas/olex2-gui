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
  interactive = True
  rFile = open("%s/etc/tutorials/%s.txt" %(OV.BaseDir(),name),'r')
  items = rFile.readlines()
  rFile.close()
  olx.Clear()
  please_exit = False
  if not interactive:
    bitmap = make_tutbox_image("Press Return to advance this tutorial!", font_colour='#44aa44')
    olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
    olx.SetMaterial("%s.Plane 2053;2131693327;2131693327"%bitmap)
    olx.DeleteBitmap(bitmap)
    olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
    time.sleep(2)
  for item in items:
    if please_exit:
      break
    item = item.strip()
    if not item:
      continue
    if item.startswith('#'):
      continue
    cmd_type = item.split(":")[0]
    cmd_content = item.split(":")[1]
    sleep = 0
    if cmd_type == "s":
      sleep = cmd_content
    
    if cmd_type == 'p':
      txt = "%s" %(cmd_content)
      #print(txt)
      if interactive:
        OV.UpdateHtml()
        OV.Refresh()
        res = make_tutbox_popup(txt)
        if res == 0:
          please_exit = True
      else:
        olx.DeleteBitmap(bitmap)
        bitmap = make_tutbox_image(txt)
        olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
        sleep = len(cmd_content) * reading_speed
        
      
    if cmd_type == 'c':
      txt = "%s: %s" %(cmd_type, cmd_content)
      txt = "%s" %(cmd_content)
      print(txt)

    if cmd_type == 'h':
      control = cmd_content
      if ';' in control:
        n = int(control.split(';')[1])
        control = control.split(';')[0]
      else:
        n = 2
      for i in xrange(n):
        control_name = "IMG_%s" %control.upper()
        OV.SetParam('gui.image_highlight',control)
        OV.UpdateHtml()
        OV.Refresh()
        time.sleep(0.3)
        OV.SetParam('gui.image_highlight',None)
        OV.UpdateHtml()
        OV.Refresh()
        time.sleep(0.3)
    #time.sleep(sleep)
    #olx.Wait(int(sleep * 1000))
      
    if cmd_type == 'c':
      olex.m(cmd_content)
  if not interactive:
    bitmap = make_tutbox_image("Done", font_colour="#44aa44")
    olx.DeleteBitmap(bitmap)
    olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
    time.sleep(1)
    olx.DeleteBitmap(bitmap)
      
OV.registerFunction(autodemo)

def make_tutbox_image(txt='txt', font_size=20, font_colour='#aa4444', bg_colour='#fff6bf'):
  IM = IT.make_simple_text_to_image(512, 64, txt, font_size=font_size, bg_colour=bg_colour, font_colour=font_colour)
  IM.save("autotut.png")
  OlexVFS.save_image_to_olex(IM, "autotut.png", 0)
  return "autotut.png"

#  control = 'IMG_TUTBOX'
#  use_image = 'autotut.png'
#  if OV.IsControl(control):
#    olx.html_SetImage('POP_%s_PRG_ANALYSIS' %self.program.program_type.upper(), self.image_location)
#  OV.SetImage(control,use_image)
  

def make_tutbox_popup(txt):
  have_image = make_tutbox_image(txt)
  pop_name = "Tutorial"
  if OV.IsControl('%s'%pop_name):
    olx.html_ShowModal(pop_name)
  else:
    txt='''
  <body link="$spy.GetParam(gui.html.link_colour)" bgcolor="$spy.GetParam(gui.html.bg_colour)">
  <font color=$spy.GetParam(gui.html.font_colour)  size=4 face="$spy.GetParam(gui.html.font_name)">
  <table border="0" VALIGN='center' style="border-collapse: collapse" width="100%%" cellpadding="1" cellspacing="1" bgcolor="$spy.GetParam(gui.html.table_bg_colour)">

  <tr align='right'>
    <td>
       <input 
         type="button" 
         bgcolor="$spy.GetParam(gui.html.input_bg_colour)" 
         valign='center' 
         width="60"  
         height="22"
         onclick="html.EndModal(%s,1)"
         value = "OK">
       <input 
         type="button" 
         bgcolor="$spy.GetParam(gui.html.input_bg_colour)" 
         valign='center' 
         width="60"  
         height="22"
         onclick="html.EndModal(%s,0)"
         value = "Cancel">
    </td>
  </tr>

  
  <tr bgcolor='#888888'>
    <td></td>
  </tr>
  
  <tr>
    <td><br><br>
    %s
    </td>
  </tr>
     </table>
     </font>
     </body>
     '''%(pop_name,pop_name,txt)
  
    OV.write_to_olex("%s.htm" %pop_name.lower(), txt)
    boxWidth = 300
    boxHeight = 500
    x = OV.GetHtmlPanelX() - boxWidth - 20
    y = 100
    olx.Popup(pop_name, '%s.htm' %pop_name.lower(), "-s -t='%s' -w=%i -h=%i -x=%i -y=%i" %(pop_name, boxWidth, boxHeight, x, y))
    res = olx.html_ShowModal(pop_name)
    res = int(res)
    return res


def tutbox(txt):
  have_image = make_tutbox_image(txt)
  name = 'Auto_Tutorial'
  if have_image:
    txt = '<zimg border="0" name="IMG_TUTBOX" src="autotut.png">'
  else:
    txt = txt
  wFilePath = r"%s.htm" %(name)
  txt = txt.replace(u'\xc5', 'angstrom')
  OV.write_to_olex(wFilePath, txt)

  boxWidth = 300
  boxHeight = 200
  x = 200
  y = 200
  olx.Popup(name, wFilePath, "-b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(name, boxWidth, boxHeight, x, y))
