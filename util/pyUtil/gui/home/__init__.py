import olex
import olx
import OlexVFS
import os

from olexFunctions import OlexFunctions
OV = OlexFunctions()

def BGColorForValue(value):
  if value == '' or value == '?':
    return "#FFDCDC"
  return OV.GetParam('gui.html.input_bg_colour')


class MultipleDataset:
  def check(self):
    if olx.IsFileType('cif') == 'false':
      return False
    if int(olx.xf.DataCount()) <= 1:
      return False
    return True

  def generateHtml(self):
    html = "<table width='100%'><tr>"
    if olx.IsFileType('cif') == 'true':
      current = int(olx.xf.CurrentData())
    else:
      current = 1
    cnt = int(olx.xf.DataCount())
    counter = -1
    for i in xrange(0, cnt):
      if olx.IsFileType('cif') == 'true':
        if olx.xf.DataName(i) == "global" or not olx.xf.DataName(i):
          continue
      counter += 1
      display = ""
      if olx.IsFileType('cif') == 'true':
        name = olx.xf.DataName(i)
      else:
        name = OV.FileName()
#      if len(name) < 3:
#        display = "Structure %s" %name
      if len(name) > 15:
        display = "%s..%s" %(name[:6], name[-6:])
      else:
        display = name
      if i > 0 and (counter%4) == 0:
        html += "</tr><tr width=100%>"
      if i == current:
        html += "<td align='center' width='25%'><b>" + display + "&nbsp;(*)</b></td>"
      else:
        action = 'reap filename().cif#' + str(i)
        #html += "<td align='center' width='25%'><a href='reap filename().cif#" + str(i) + "'>"\
           #+ display + "</a></td>"
        html += '''
    $+
      html.Snippet(GetVar(default_link),
      "value='%s'",
      "onclick=%s"
      )
    $-''' %(display, action)

    html + "</tr></table>"
    name = 'multicif.htm'
    OlexVFS.write_to_olex(name, html)
    return "<!-- #include multicif %s;1; -->" %name

mds = MultipleDataset()
olex.registerFunction(mds.check, False, "gui.home.multiple_dataset")
olex.registerFunction(mds.generateHtml, False, "gui.home.multiple_dataset")
