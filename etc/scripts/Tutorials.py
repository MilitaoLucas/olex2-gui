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
  def __init__(self, name='default_auto_tutorial', reading_speed=0.06):
    self.interactive = True
    self.bg_colour = IT.decimalColorToHTMLcolor(OV.GetParam('gui.skin.clearcolor'))
    self.font_size = 20
    self.highlight_colour = OV.GetParam('gui.html.highlight_colour').hexadecimal

    try:
      self.bg_colour = IT.decimalColorToHTMLcolor(int(olx.gl_lm_ClearColor()))
      self.font_colour = '#ffffff'
      self.font_colour_code = '#aaaaff'
      self.font_colour_bold = '#aaaaff'
    except:
      self.bg_colour = '#ffffff'
      self.font_colour = '#000000'
      self.font_colour_code = '#000088'
      self.font_colour_bold = '#444444'

    self.name = name
    self.reading_speed = reading_speed

  def run_autodemo(self, name):
    if name:
      self.name = name
    have_hover = OV.GetParam('olex2.hover_buttons')
    OV.SetParam('olex2.hover_buttons', True)
    
    ## First read in the commands that preceeds all tutorials
    rFile = open("%s/etc/tutorials/all_tutorials_preamble.txt" %OV.BaseDir(),'r')
    items = rFile.readlines()
    rFile.close()

    ## Then read in the actual tutorial
    rFile = open("%s/etc/tutorials/%s.txt" %(OV.BaseDir(),self.name),'r')
    items = items + rFile.readlines()
    rFile.close()
    
    olx.Clear()
    please_exit = False
    if not self.interactive:
      self.txt = "Press Return to advance this tutorial!"
      bitmap = self.make_tutbox_image()
      olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
      olx.SetMaterial("%s.Plane 2053;2131693327;2131693327"%bitmap)
      olx.DeleteBitmap(bitmap)
      olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
      time.sleep(2)
    for item in items:
      if please_exit:
        olex.m('rota 1 2 3 0 0')
        break
      item = item.strip()
      if not item:
        continue
      if item.startswith('#'):
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

      cmd_type = item.split(":")[0]
      cmd_content = item.split(":")[1]
      sleep = 0
      if cmd_type == "s":
        sleep = cmd_content

      if cmd_type == 'p':
        self.txt = "%s" %(cmd_content)
        if self.interactive:
          #OV.UpdateHtml()
          #OV.Refresh()
          res = self.make_tutbox_popup()
          if res == 0:
            olexex.switch_tab_for_tutorials('home')
            olex.m('ofiledel 0')
            please_exit = True
        else:
          olx.DeleteBitmap(bitmap)
          bitmap = self.make_tutbox_image()
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
          if "element" in control:
            new_image = "up=%son.png" %control
            olx.html_SetImage(control_name,new_image)
          elif control.endswith('_bg'):
            cmd = 'html.setBG(%s,%s)' %(control.rstrip('_bg'), self.highlight_colour)
            olex.m(cmd)
          else:
            OV.SetParam('gui.image_highlight',control)
            OV.UpdateHtml()
          OV.Refresh()
          time.sleep(0.1)

          if "element" in control:
            new_image = "up=%soff.png" %control
            olx.html_SetImage(control_name,new_image)
          elif control.endswith('_bg'):
            cmd = 'html.setBG(%s,%s)' %(control.rstrip('_bg'), '#fffffe')
            olex.m(cmd)
          else:
            OV.SetParam('gui.image_highlight',None)
            OV.UpdateHtml()
          OV.Refresh()
          if i != n-1:
            time.sleep(0.1)
      #time.sleep(sleep)
      #olx.Wait(int(sleep * 1000))

      if cmd_type == 'c':
        olex.m(cmd_content)
    if not self.interactive:
      bitmap = self.make_tutbox_image("Done", font_colour=self.font_colour)
      olx.DeleteBitmap(bitmap)
      olx.CreateBitmap('-r %s %s' %(bitmap, bitmap))
      time.sleep(1)
      olx.DeleteBitmap(bitmap)
    OV.SetParam('olex2.hover_buttons', have_hover)


  def make_tutbox_image(self):
    txt = self.txt
    IM = IT.make_simple_text_to_image(512, 64, txt, font_size=self.font_size, bg_colour=self.bg_colour, font_colour=self.font_colour)
    IM.save("autotut.png")
    OlexVFS.save_image_to_olex(IM, "autotut.png", 0)
    return "autotut.png"

  def make_tutbox_popup(self):
    txt = self.txt
    have_image = self.make_tutbox_image()
    pop_name = "AutoTutorial"

    self.format_txt()

    d = {}
    d.setdefault('pop_name',pop_name)
    d.setdefault('bg_colour',self.bg_colour)
    d['bg_colour'] = self.bg_colour
    d.setdefault('font_colour',self.font_colour)
    d.setdefault('txt', self.txt)

    if OV.IsControl('%s'%pop_name):
      olx.html_ShowModal(pop_name)
    else:
      rFile = open("%s/etc/gui/blocks/templates/pop_tutorials.htm" %OV.BaseDir(),'r')
      txt = rFile.read() %d
      rFile.close()

      txt = txt.decode('utf-8')
      OV.write_to_olex("%s.htm" %pop_name.lower(), txt)
      boxWidth = 200
      boxHeight = 300
      x = OV.GetHtmlPanelX() - boxWidth - 40
      y = 70
      olx.Popup(pop_name, '%s.htm' %pop_name.lower(), "-s -t='%s' -w=%i -h=%i -x=%i -y=%i" %(pop_name, boxWidth, boxHeight, x, y))
      olx.html_SetFocus(pop_name + '.TUTORIAL_NEXT')
      res = olx.html_ShowModal(pop_name)
      res = int(res)

      return res


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


AutoDemo_istance = AutoDemo()
OV.registerFunction(AutoDemo_istance.run_autodemo)
