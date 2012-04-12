import olex
import olx
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
    current = int(olx.xf.CurrentData())
    cnt = int(olx.xf.DataCount())
    counter = -1
    for i in xrange(0, cnt):
      if olx.xf.DataName(i) == "global":
        continue
      counter += 1
      if i > 0 and (counter%4) == 0:
        html += "</tr><tr width=100%>"
      if i == current:
        html += "<td align='center' width='25%'>Structure <b>" + olx.xf.DataName(i) + "&nbsp;(*)</b></td>"
      else:
        html += "<td align='center' width='25%'><a href='reap filename().cif#" + str(i) + "'>Structure "\
           + olx.xf.DataName(i) + "</a></td>"
    return html + "</tr></table>"

mds = MultipleDataset()
olex.registerFunction(mds.check, False, "gui.home.multiple_dataset")
olex.registerFunction(mds.generateHtml, False, "gui.home.multiple_dataset")
