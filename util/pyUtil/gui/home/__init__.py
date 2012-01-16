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
    for i in xrange(0, cnt):
      if i > 0 and (i%3) == 0:
        html += "</tr><tr>"
      if i == current:
        html += "<td>" + olx.xf.DataName(i) + "&nbsp;(*)</td>"
      else:
        html += "<td><a href='reap filename().cif#" + str(i) + "'>"\
           + olx.xf.DataName(i) + "</a></td>"
    return html + "</tr></table>"

class FolderView:
  root = None
  class node:
    name = None
    parent = None
    content = []
    def __init__(self, name):
      self.name = name
    def __str__(self):
      return name
    def expand(self):
      for entry in os.listdir(name):
        full_name = os.path.join(name,entry)
        if os.path.isdir(full_name):
          dr = node(full_name)
          dr.expand()
          if len(dr.content):
            content.append(dr)
        else:
          self.content.append(node(full_name))


  def list(self, folder):
    root = node(folder)
    root.expand()

  def generateHtml(self):
    print root
    return root

mds = MultipleDataset()
olex.registerFunction(mds.check, False, "gui.home.multiple_dataset")
olex.registerFunction(mds.generateHtml, False, "gui.home.multiple_dataset")

fv = FolderView()
olex.registerFunction(fv.generateHtml, False, "gui.home.folder_view")
