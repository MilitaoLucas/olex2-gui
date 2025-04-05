# guiFunctions.py

import sys
import olx
import olex
from decors import gui_only
if olx.HasGUI() == 'true': import olex_gui

class GuiFunctions(object):
  @gui_only()
  def GetUserInput(self, arg, title, contentText):
    """If first argument is 1 (number one) brings up one line input box, anything else brings up a multiline input."""
    try:
      import olexex
      retStr = olexex.FixMACQuotes(olex_gui.GetUserInput(arg,title,contentText))
    except Exception as ex:
      print("An error occurred", file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  @gui_only()
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
    except Exception as ex:
      print("An error occurred", file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  @gui_only()
  def IsHtmlItem(self, name):
    return olx.html.IsItem(name) == 'true'

  @gui_only()
  def IsControl(self, ctrl_name):
    try:
      return bool(olex_gui.IsControl(ctrl_name))
    except Exception as ex:
      print("An error occurred.", file=sys.stderr)
      sys.stderr.formatExceptionInfo()

  @gui_only()
  def SetControlBG(self, ctrl_name, val):
    if self.IsControl(ctrl_name):
      olx.html.SetBG(ctrl_name, val)

  @gui_only()
  def SetControlFG(self, ctrl_name, val):
    if self.IsControl(ctrl_name):
      olx.html.SetFG(ctrl_name, val)

  @gui_only()
  def SetControlValue(self, ctrl_name, val):
    if self.IsControl(ctrl_name):
      olx.html.SetValue(ctrl_name, val)

  @gui_only()
  def SetControlLabel(self, ctrl_name, val):
    if self.IsControl(ctrl_name):
      olx.html.SetLabel(ctrl_name, val)

  @gui_only()
  def SetControlItems(self, ctrl_name, items, val=None):
    if self.IsControl(ctrl_name):
      olx.html.SetItems(ctrl_name, items)
      if val is not None:
        olx.html.SetValue(ctrl_name, val)

  @gui_only()
  def SetControlState(self, ctrl_name, val):
    if self.IsControl(ctrl_name):
      olx.html.SetState(ctrl_name, val)

  @gui_only()
  def SetControlEnabled(self, ctrl_name, val):
    if self.IsControl(ctrl_name):
      olx.html.SetEnabled(ctrl_name, val)

  @gui_only()
  def TranslatePhrase(self, text):
    try:
      retStr = olx.TranslatePhrase(text)
    except Exception as ex:
      print("An error occurred whilst translating %s" %(text), file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  @gui_only()
  def UpdateHtml(self, html_name='', force=False):
    olx.html.Update(html_name)

  @gui_only()
  def HtmlLoad(self, path):
    olx.html.Load(path)

  @gui_only()
  def HtmlDefineControl(self, d):
    olx.html.DefineControl('%(name)s %(type)s -v=%(value)s -i=%(items)s' %d)

  @gui_only()
  def Cursor(self, state="", text=""):
    if state:
      olx.Cursor(state, text)
    else:
      olx.Cursor()

  @gui_only()
  def Refresh(self):
    olx.Refresh()

  @gui_only()
  def CreateBitmap(self, bitmap):
    olx.CreateBitmap(bitmap, bitmap, r=True)

  @gui_only()
  def DeleteBitmap(self, bitmap):
    olx.DeleteBitmap('%s' %bitmap)

  @gui_only()
  def Listen(self, listenFile):
    pass
    #olx.Listen(listenFile)

  @gui_only()
  def SetGrad(self, f=None):
    from ImageTools import IT
    l = ['top_right', 'top_left', 'bottom_right', 'bottom_left']
    v = []
    for i in range(4):
      val = OV.GetParam('gui.grad_%s' %(l[i]))
      if not val:
        val = "#ffffff"
      val = IT.hex2dec(val)
      v.append(val)
    olex.m("Grad %i %i %i %i" %(v[0], v[1], v[2], v[3]))

  @gui_only()
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

  @gui_only()
  def GetHtmlPanelwidth(self):
    return olx.HtmlPanelWidth()

  @gui_only()
  def setItemstate(self, txt):
    olx.html.ItemState(*tuple(txt.split()))

  @gui_only()
  def SetImage(self, zimg_name, image_file):
    if self.olex_gui.IsControl(zimg_name):
      olx.html.SetImage(zimg_name,image_file)

  @gui_only()
  def setDisplayQuality(self, q=None):
    if not q:
      q = self.GetParam('snum.display_quality')
      if not q:
        q = 2
    olx.Qual(q)

a = GuiFunctions()
olex.registerMacro(a.SetGrad, 'f')
olex.registerFunction(a.GetFormulaDisplay)