import os
import glob
import olx
import olex
import olexex
import time

from olexFunctions import OlexFunctions
OV = OlexFunctions()

from ImageTools import ImageTools
IT = ImageTools()

import OlexVFS

class AutoDemo():
  def __init__(self, name='default_auto_tutorial', reading_speed=2):
    self.interactive = True
    self.font_size = 20

    self.name = name
    self.reading_speed = reading_speed
    self.pop_name = "QuickTutorial"
    self.items = []
    self.item_counter = 0
    self.have_box_already = False
    self.user_structure = None
    self.bitmap = None
    self.stop_tutorial = False

  def set_box_bg_colour(self):
    self.highlight_colour = OV.GetParam('gui.html.highlight_colour').hexadecimal
    c = olx.gl.lm.ClearColor()
    if "," in c:
      c = c.split(',')
      c = (float(c[0])*255, float(c[1])*255, float(c[2])*255)
      c = IT.RGBToHTMLColor(c)
    else:
      c = IT.decimalColorToHTMLcolor(int(olx.gl.lm.ClearColor()))
    
    if c != "#ffffff":
      self.font_colour = '#ffffff'
      self.font_colour_code = '#aaaaff'
      self.font_colour_bold = '#aaaaff'
    else:
      self.font_colour = '#000000'
      self.font_colour_code = '#000088'
      self.font_colour_bold = '#444444'

    if type(c) is long:
      c = IT.decimalColorToHTMLcolor(int(olx.gl.lm.ClearColor()))
    
    self.bg_colour = c
    self.button_bar_colour = IT.RGBToHTMLColor(IT.adjust_colour(self.bg_colour, luminosity=0.8))
    
  def read_tutorial_definitions(self):
    ## First read in the commands that preceeds all tutorials
    rFile = open("%s/etc/tutorials/all_tutorials_preamble.txt" %OV.BaseDir(),'r')
    self.items = rFile.readlines()
    rFile.close()

    ## Then read in the actual tutorial
    rFile = open("%s/etc/tutorials/%s.txt" %(OV.BaseDir(),self.name),'r')
    self.items = self.items + rFile.readlines()
    rFile.close()

    rFile = open("%s/etc/tutorials/all_tutorials_end.txt" %OV.BaseDir(),'r')
    self.items = self.items + rFile.readlines()
    rFile.close()

  def run_demo_loop(self):
    self.items = []
    self.item_counter = 0
    self.read_tutorial_definitions()
    self.set_box_bg_colour()
    self.interactive = False
    for item in self.items:
      #if OV.FindValue('stop_current_process'):
      if OV.GetParam('olex2.stop_current_process'):
        print "AutoTutorial Interrupted!"
        #OV.SetVar('stop_current_process',False)
        OV.SetParam('olex2.stop_current_process',False)
        self.end_tutorial()
        return
      self.get_demo_item()
      self.run_demo_item()
    self.interactive = True
    self.end_tutorial()
    
  def run_autodemo(self, name, other_popup_name=""):

    try:
      self.user_structure = OV.FileFull()
      self.set_box_bg_colour()
      self.items = []
      self.item_counter = 0
      if other_popup_name and olx.IsPopup(other_popup_name):
        olx.html.Hide(other_popup_name)
      
      if name:
        self.name = name
      
      self.read_tutorial_definitions()
  
      olx.Clear()
      
      self.get_demo_item()
      cmd_type = self.run_demo_item()
      
      
    except Exception, err:
      print "+++ ERROR IN TUTORIALS: %s" %err
      self.end_tutorial()
    
    #please_exit = False
    #if not self.interactive:
      #self.txt = "Press Return to advance this tutorial!"
      #bitmap = self.make_tutbox_image()
      #olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
      #olx.SetMaterial("%s.Plane 2053;2131693327;2131693327"%bitmap)
      #olx.DeleteBitmap(bitmap)
      #olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
      #time.sleep(2)
    #self.item_counter = 0
    #item = ""

    #if not self.interactive:
      #bitmap = self.make_tutbox_image("Done", font_colour=self.font_colour)
      #olx.DeleteBitmap(bitmap)
      #olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
      #time.sleep(1)
      #olx.DeleteBitmap(bitmap)
    #OV.SetParam('olex2.hover_buttons', have_hover)

  def next_demo_item(self):
    #self.item_counter += 1
    self.get_demo_item()
    self.run_demo_item()

  def cancel_demo_item(self):
    olx.html.Hide(self.pop_name)
    self.end_tutorial()
    
  def back_demo_item(self):
    found_p = 2
    while found_p:
      self.item_counter -= 1
      if self.items[self.item_counter].startswith("p:"):
        found_p -= 1
        self.item_counter -= 1
    self.get_demo_item()
    self.run_demo_item()

  def make_tutbox_image(self):
    txt = self.cmd_content
    IM = IT.make_simple_text_to_image(512, 64, txt, font_size=self.font_size, bg_colour=self.bg_colour, font_colour=self.font_colour)
    IM.save("autotut.png")
    OlexVFS.save_image_to_olex(IM, "autotut.png", 0)
    return "autotut.png"

  def make_tutbox_popup(self):
    txt = self.txt
    have_image = self.make_tutbox_image()

    self.format_txt()

    d = {}
    d.setdefault('pop_name',self.pop_name)
    d.setdefault('bg_colour',self.bg_colour)
    d['bg_colour'] = self.bg_colour
    d['button_bar_colour'] = self.button_bar_colour
    d.setdefault('font_colour',self.font_colour)
    d.setdefault('txt', self.txt)

    if OV.IsControl('%s'%self.pop_name):
      pass
      #olx.html.ShowModal(self.pop_name)
    else:
      if self.interactive:
        rFile = open("%s/etc/gui/blocks/templates/pop_tutorials.htm" %OV.BaseDir(),'r')
      else:
        rFile = open("%s/etc/gui/blocks/templates/pop_tutorials_loop.htm" %OV.BaseDir(),'r')
      txt = rFile.read() %d
      rFile.close()

      txt = txt.decode('utf-8')
      OV.write_to_olex("%s.htm" %self.pop_name.lower(), txt)
      boxWidth = 350
      boxHeight = 220
      x = OV.GetHtmlPanelX() - boxWidth - 40
      y = 70
      if self.have_box_already:
        olx.Popup(self.pop_name, '%s.htm' %self.pop_name.lower(), "-t='%s'" %(self.pop_name,))
      else:
        if self.interactive:
          olx.Popup(self.pop_name, '%s.htm' %self.pop_name.lower(), "-b=t -t='%s' -w=%i -h=%i -x=%i -y=%i" %(self.pop_name, boxWidth, boxHeight, x, y))
          olx.html.SetFocus(self.pop_name + '.TUTORIAL_NEXT')
        else:
          boxWidth = 400
          boxHeight = 250
          x = OV.GetHtmlPanelX() - boxWidth - 40
          y = 75
          olx.Popup(self.pop_name, '%s.htm' %self.pop_name.lower(), "-t='%s' -w=%i -h=%i -x=%i -y=%i" %(self.pop_name, boxWidth, boxHeight, x, y))
        self.have_box_already = True
        #olx.html.Show(self.pop_name)
      OV.Refresh()
      if not self.interactive:
        sleep = len(self.cmd_content) * self.reading_speed
        olx.Wait(sleep)


      return

  def end_tutorial(self):
    OV.SetParam('olex2.stop_current_process',False)
    olx.Freeze(False)
    olx.Echo('Tutorial Ended or Interrupted')
    olx.gl.Stereo('normal')
    olx.OFileDel(0)
    olx.Fuse()
    if self.user_structure:
      OV.AtReap(self.user_structure)
    #self.have_box_already = False

  def tutbox(self):
    txt = self.txt
    have_image = self.make_tutbox_image()
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

  def format_txt(self):
    txt = self.txt
    txt = txt.replace('<b>','<b><font color=%s>' %self.font_colour_bold)
    txt = txt.replace('</b>','</font></b>')
    txt = txt.replace('<c>','<b><code><font color=%s>' %self.font_colour_code)
    txt = txt.replace('</c>','</font></code></b>')
    self.txt = txt

  def stop_tutorial(self):
    self.stop_tutorial = True
    
  def get_demo_item(self):
    retItem = None
    while not retItem:
      item = self.items[self.item_counter]
      self.item_counter += 1
      item = item.strip()
      if not item:
        continue
      if item.startswith('#'):
        continue
      if item == "END":
        self.item_counter = 0
        start_again = True
        continue
      if item == "BEGIN":
        continue
      if item.startswith('\xef\xbb\xbf'):
        continue
      if item.startswith('set:'):
        var = item.split('set:')[1].split('=')[0]
        val = item.split('=')[1]
        if "." in val:
          if 'colour' in val:
            val = OV.GetParam(val).hexadecimal
          else:
            val = OV.GetParam(val)
        setattr(self, var, val)
        continue
      
      retItem = item
    self.cmd_type = item.split(":")[0]
    self.cmd_content = item.split(":")[1]
  
    
    
  def run_demo_item(self):
    cmd_type = self.cmd_type
    cmd_content = self.cmd_content
    if cmd_type == "s":
      sleep = cmd_content

    if cmd_type == 'p':
      self.txt = "%s" %(cmd_content)
      if self.interactive:
        res = self.make_tutbox_popup()#
      else:
        res = self.make_tutbox_popup()#
#        if self.bitmap:
#          olx.DeleteBitmap(self.bitmap)
#        self.bitmap = self.make_tutbox_image()
#        olx.CreateBitmap('-r %s %s' %(self.bitmap, self.bitmap))
#        sleep = len(self.cmd_content) * self.reading_speed


    if cmd_type == 'c':
      if not self.interactive:
        if cmd_content == "text":
          return
      txt = "%s: %s" %(cmd_type, cmd_content)
      txt = "%s" %(cmd_content)
      #print(txt)

    if cmd_type == 'h':
      control = cmd_content
      
      if ';' in control:
        n = int(control.split(';')[1])
        control = control.split(';')[0]
      else:
        n = 2

      control_name = "IMG_%s" %control.upper()
      if '@' in control:
#        print "@ in control"
        control_image = control.lower().split('@')[0]
      else:
        control_image = control
      for i in xrange(n):
        if "element" in control:
          new_image = "up=%son.png" %control_image
          olx.html.SetImage(control_name,new_image)
        elif control.endswith('_bg'):
          cmd = 'html.setBG(%s,%s)' %(control_image.rstrip('_bg'), self.highlight_colour)
          olex.m(cmd)
        else:
          new_image = "up=%soff.png" %control_image
          olx.html.SetImage(control_name,new_image)
        OV.Refresh()
        olx.Wait(300)
  
        if "element" in control:
          new_image = "up=%soff.png" %control
          olx.html.SetImage(control_name,new_image)
        elif control.endswith('_bg'):
          cmd = 'html.setBG(%s,%s)' %(control.rstrip('_bg'), '#fffffe')
          olex.m(cmd)
        else:
          new_image = "up=%shighlight.png" %control_image
          olx.html.SetImage(control_name,new_image)
        OV.Refresh()
        olx.Wait(300)

      if not control.endswith('_bg'):
        new_image = "up=%soff.png" %control_image
        olx.html.SetImage(control_name,new_image)

    if cmd_type == 'c':
      olex.m(cmd_content)
      
    if cmd_type != 'p':
      self.get_demo_item()
      self.run_demo_item()
      
    OV.Refresh()

  
AutoDemo_istance = AutoDemo()
OV.registerFunction(AutoDemo_istance.run_autodemo,False,'demo')
OV.registerFunction(AutoDemo_istance.run_demo_loop,False,'demo')
OV.registerFunction(AutoDemo_istance.next_demo_item,False,'demo')
OV.registerFunction(AutoDemo_istance.back_demo_item,False,'demo')
OV.registerFunction(AutoDemo_istance.cancel_demo_item,False,'demo')
