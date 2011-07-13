import olex
import olx

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
    if int(olx.xf_DataCount()) <= 1:
      return False
    return True
  
  def generateHtml(self):
    html = "<table width='100%'><tr>"
    current = int(olx.xf_CurrentData())
    cnt = int(olx.xf_DataCount())
    for i in xrange(0, cnt):
      if i > 0 and (i%3) == 0:
        html += "</tr><tr>"
      if i == current:
        html += "<td>" + olx.xf_DataName(i) + "&nbsp;(*)</td>"
      else:
        html += "<td><a href='reap filename().cif#" + str(i) + "'>"\
           + olx.xf_DataName(i) + "</a></td>"
    return html + "</tr></table>"
  
mds = MultipleDataset()
olex.registerFunction(mds.check, False, "gui.home.multiple_dataset")
olex.registerFunction(mds.generateHtml, False, "gui.home.multiple_dataset")
