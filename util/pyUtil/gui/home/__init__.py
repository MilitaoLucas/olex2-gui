import olex
import olx
import OlexVFS
import os

from olexFunctions import OlexFunctions
OV = OlexFunctions()

global CURR_CIF_FILE_NAME
CURR_CIF_FILE_NAME = None

global CURR_CIF_FILE_LIST
CURR_CIF_FILE_LIST = []

def BGColorForValue(value):
  if value == '' or value == '?':
    return "#FFDCDC"
  return OV.GetParam('gui.html.input_bg_colour')


class MultipleDataset:
  def check(self):
    if CURR_CIF_FILE_NAME:
      return True
    if olx.IsFileType('cif') == 'false':
      return False
    if int(olx.xf.DataCount()) <= 1:
      return False
    return True

  def generateHtml(self,make_always=False):
    global CURR_CIF_FILE_NAME
    current = None
    html = '<table border="0" VALIGN="center" width="100%" cellpadding="1" cellspacing="0" bgcolor="$GetVar(HtmlTableRowBgColour)"><tr>'
    if not CURR_CIF_FILE_NAME:
      if olx.IsFileType('cif') == 'true':
        CURR_CIF_FILE_NAME = OV.FileFull()
        current = int(olx.xf.CurrentData())
      
    if not CURR_CIF_FILE_LIST:
      cnt = int(olx.xf.DataCount())
      for i in xrange(0, cnt):
        if olx.IsFileType('cif') == 'true':
          if olx.xf.DataName(i) == "global" or not olx.xf.DataName(i):
            cnt -= 1
            continue
        display = ""
        if olx.IsFileType('cif') == 'true':
          name = olx.xf.DataName(i)
        else:
          name = OV.FileName()
        if len(name) > 15:
          display = "%s..%s" %(name[:6], name[-6:])
        else:
          display = name
        current = 0
        CURR_CIF_FILE_LIST.append((i, name, display))
    else:
      cnt = len(CURR_CIF_FILE_LIST)
      for i in xrange(0, cnt):
        if OV.ModelSrc() in CURR_CIF_FILE_LIST[i]:
          current = i
          break

    for i in xrange(0, cnt):
      name = CURR_CIF_FILE_LIST[i][1]
      display = CURR_CIF_FILE_LIST[i][2]

      if (cnt%3) == 0:
        td_width='33'
      elif (cnt%4) == 0:
        td_width='25'
      elif (cnt%2) == 0:
        td_width='50'
      else:
        td_width='25'

      if i > 0 and (cnt%4) == 0:
        html += "</tr><tr width=100%>"
      if i == current:
        bgcolour=OV.GetVar('HtmlBgColour')
        if OV.FileExt() == "cif":
          action = "refine"
          highlight = olx.GetVar('HtmlHighlightColour')
          display = "Refine %s" %display
        else:
          action = 'reap %s#'%(CURR_CIF_FILE_NAME) + str(i+1)
          highlight = OV.GetParam('gui.green')
          display = "CIF %s" %display
      else:
        action = 'reap %s#'%(CURR_CIF_FILE_NAME) + str(i+1)
        highlight = olx.GetVar('linkButton.bgcolor')
      html += '''
    $+
      html.Snippet(GetVar(default_link),
      "value=%s",
      "name=%s",
      "onclick=%s",
      "bgcolor=%s",
      )
    $-''' %(display, name, action, highlight)

    html + "</tr></table>"
    name = 'multicif.htm'
    OlexVFS.write_to_olex(name, html)
    return "<!-- #include multicif %s;1; -->" %name

mds = MultipleDataset()
olex.registerFunction(mds.check, False, "gui.home.multiple_dataset")
olex.registerFunction(mds.generateHtml, False, "gui.home.multiple_dataset")
