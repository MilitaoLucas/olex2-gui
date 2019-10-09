# guiFunctions.py

import sys
import olx
import olex
if olx.HasGUI() == 'true': import olex_gui

class GuiFunctions(object):

  def GetUserInput(self, arg, title, contentText):
    """If first argument is 1 (number one) brings up one line input box, anything else brings up a multiline input."""
    try:
      import olexex
      retStr = olexex.FixMACQuotes(olex_gui.GetUserInput(arg,title,contentText))
    except Exception, ex:
      print >> sys.stderr, "An error occurred"
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  def Alert(self, title, text, buttons=None, tickboxText=None):
    '''
    Opens an alert window. 
    :param title: Window title in the title bar
    :param text: Text content to display in the window.
    :param buttons: String with different possible flags. 
                    Flags can be mixed like'YNHR': 
    'YNCO' yes,no,cancel,ok  -> Text on the buttons
    'XHEIQ-icon' exclamation,hand,eror,information,question 
                  --> Icon beside the window text. 
    'R-show' checkbox --> show a checkbox
    :param tickboxText: checkbox message
    :return retStr: returns blooean values of the buttons.
    '''
    try:
      retStr = olx.Alert(title, text, buttons, tickboxText)
    except Exception, ex:
      print >> sys.stderr, "An error occurred"
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  def IsControl(self, ctrl_name):
    try:
      return bool(olex_gui.IsControl(ctrl_name))
    except Exception, ex:
      print >> sys.stderr, "An error occurred."
      sys.stderr.formatExceptionInfo()

  def TranslatePhrase(self, text):
    try:
      retStr = olx.TranslatePhrase(text)
    except Exception, ex:
      print >> sys.stderr, "An error occurred whilst translating %s" %(text)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  def UpdateHtml(self, html_name=''):
    olx.html.Update(html_name)

  def HtmlLoad(self, path):
    olx.html.Load(path)

  def HtmlDefineControl(self, d):
    olx.html.DefineControl('%(name)s %(type)s -v=%(value)s -i=%(items)s' %d)

  def Cursor(self, state="", text=""):
    if state:
      olx.Cursor(state, text)
    else:
      olx.Cursor()

  def Refresh(self):
    olx.Refresh()

  def CreateBitmap(self, bitmap):
    olx.CreateBitmap(bitmap, bitmap, r=True)

  def DeleteBitmap(self, bitmap):
    olx.DeleteBitmap('%s' %bitmap)

  def Listen(self, listenFile):
    pass
    #olx.Listen(listenFile)

  def SetGrad(self, f=None):
    from ImageTools import IT
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
    rv = ""
    s = olx.xf.GetFormula('list')
    l = s.split(',')
    for item in l:
      item = item.split(":")
      ele = item[0]
      num = item[1]
      if "." in num:
        num = float(num)
        num = "%.2f" %num
      if num == "1": num = ""
      rv+="%s<sub>%s</sub>" %(ele, num)
    return rv

  def GetHtmlPanelwidth(self):
    return olx.HtmlPanelWidth()

  def setItemstate(self, txt):
    olx.html.ItemState(*tuple(txt.split()))

  def SetImage(self, zimg_name, image_file):
    if self.olex_gui.IsControl(zimg_name):
      olx.html.SetImage(zimg_name,image_file)

  def setDisplayQuality(self, q=None):
    if not q:
      q = self.GetParam('snum.display_quality')
      if not q:
        q = 2
    olx.Qual(q)

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
