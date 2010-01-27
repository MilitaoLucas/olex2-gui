# guiFunctions.py

import sys
import olx
import olex
if olx.HasGUI() == 'true': import olex_gui

class GuiFunctions(object):

  def GetUserInput(self, arg, title, contentText):
    """If first argument is 1 (number one) brings up one line input box, anything else brings up a multiline input."""
    try:
      retStr = olex_gui.GetUserInput(arg,title,contentText)
    except Exception, ex:
      print >> sys.stderr, "An error occured"
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  def Alert(self, title, text, buttons=None, tickboxText=None):
    try:
      retStr = olx.Alert(title, text, buttons, tickboxText)
    except Exception, ex:
      print >> sys.stderr, "An error occured"
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr
  
  def IsControl(self, ctrl_name):
    try:
      return bool(olex_gui.IsControl(ctrl_name))
    except Exception, ex:
      print >> sys.stderr, "An error occured."
      sys.stderr.formatExceptionInfo()
      
  def TranslatePhrase(self, text):
    try:
      retStr = olx.TranslatePhrase(text)
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst translating %s" %(text)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr
  
  def UpdateHtml(self):
    olx.UpdateHtml()
    
  def HtmlReload(self):
    olx.HtmlReload()
    
  def HtmlLoad(self, path):
    olx.html_Load(path)
    
  def HtmlDefineControl(self, d):
    olx.html_DefineControl('%(name)s %(type)s -v=%(value)s -i=%(items)s' %d)
    
  def Cursor(self, state="", text=""):
    if state:
      olx.Cursor(state, text)
    else:
      olx.Cursor()
      
  def Refresh(self):
    olx.Refresh()
      
  def CreateBitmap(self, bitmap):
    olx.CreateBitmap("-r %s %s" %(bitmap, bitmap))
    
  def DeleteBitmap(self, bitmap):
    olx.DeleteBitmap('%s' %bitmap)
    
  def Listen(self, listenFile):
    pass
    #olx.Listen(listenFile)

  def SetGrad(self, f=None):
    from ImageTools import ImageTools
    IT = ImageTools()
    l = ['top_right', 'top_left', 'bottom_right', 'bottom_left']
    v = []
    for i in xrange(4):
      val = OV.GetParam('gui.grad_%s' %(l[i]))
      if not val:
        val = "#ffffff"
      val = IT.hex2dec(val)
      v.append(val)
    olex.m("Grad %i %i %i %i" %(v[0], v[1], v[2], v[3]))
    
  def GetFormulaDisplay(self):
    str = ""
    s = olx.xf_GetFormula('list')
    l = s.split(',')
    for item in l:
      item = item.split(":")
      ele = item[0]
      num = item[1]
      if "." in num:
        num = float(num)
        num = "%.2f" %num
      if num == "1": num = ""
      str+="%s<sub>%s</sub>" %(ele, num)
    return str

  def GetHtmlPanelwidth(self):
    return olx.HtmlPanelWidth()

  def setItemstate(self, txt):
    olex.m("itemstate %s" %txt)

  def SetImage(self, zimg_name, image_file):
    if self.olex_gui.IsControl(zimg_name):
      olx.html_SetImage(zimg_name,image_file)

  def setDisplayQuality(self, q=None):
    if not q:
      q = self.GetParam('snum.display_quality')
      if not q:
        q = 2
    try:
      q = int(q)
      d = {1:'l', 2:'m', 3:'h'}
      q = d.get(q,2)
    except:
      pass
    olx.Qual("-%s" %q)

a = GuiFunctions()
olex.registerMacro(a.SetGrad, 'f')
olex.registerFunction(a.GetFormulaDisplay)

class NoGuiFunctions(object):
  def GetUserInput(self,arg,title,contentText):
    print '%s:' %title
    print contentText
    return contentText
  
  def Alert(self, title, text, buttons=None, tickboxText=None):
    return ''
  
  def UpdateHtml(self):
    return ''
  
  def HtmlReload(self):
    return ''
  
  def HtmlLoad(self, path):
    return ''
    
  def HtmlDefineControl(self, d):
    return ''

  def Cursor(self, state=None, text=None):
    return ''
  
  def CreateBitmap(self, bitmap):
    return ''
  
  def DeleteBitmap(self, bitmap):
    return ''
  
  def Listen(self, listenFile):
    return ''
  
  def TranslatePhrase(self,text):
    return ''
  
  def Refresh(self):
    return ''
