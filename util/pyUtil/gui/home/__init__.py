import olex
import olx
import OlexVFS
import os
from olexFunctions import OV

def BGColorForValue(value):
  if value == '' or value == '?':
    return "#FFDCDC"
  return OV.GetParam('gui.html.input_bg_colour')


class MultipleDataset:
  def __init__(self):
    pass

  def check(self):
    if olx.IsFileType('cif') != 'true':
      return False
    cnt = int(olx.xf.DataCount())
    useful = 0
    for i in range(cnt):
      if olx.xf.DataName(i) == "global" or not olx.xf.DataName(i):
        continue
      useful += 1
    return useful > 1

  def list_datasets(self, sort_key):
    rv = []
    cnt = int(olx.xf.DataCount())
    sort = 0
    for i in range(0, cnt):
      if olx.IsFileType('cif') == 'true':
        if olx.xf.DataName(i) == "global" or not olx.xf.DataName(i):
          rv.append((i, name, display, sort, False))
          continue
      display = ""
      if olx.IsFileType('cif') == 'true':
        name = olx.xf.DataName(i)
        sort = olx.Cif('%s#%i' % (sort_key, i))
        if sort == "n/a":
          sort = name
      if len(name) > 15:
        display = "%s..%s" % (name[:6], name[-6:])
      else:
        display = name
      rv.append((i, name, display, sort, True))
    return rv

  def generateHtml(self, make_always=False, sort_key='_database_code_depnum_ccdc_archive'):
    if olx.IsFileType('cif') != 'true':
      return ""

    current = int(olx.xf.CurrentData())
    file_name = olx.FileFull()
    html = '<table border="0" VALIGN="center" width="100%" cellpadding="1" cellspacing="0" bgcolor="$GetVar(HtmlTableRowBgColour)"><tr>'
    datasets = self.list_datasets(sort_key=sort_key)

    shown_cnt = 0
    for index, name, display, sk, do_show in datasets:
      if not do_show:
        continue
      shown_cnt += 1
      fg = OV.GetVar('linkButton.fgcolor')
      if shown_cnt > 1 and ((shown_cnt-1) % 4) == 0:
        html += "</tr><tr width=100%>"
      if index == current:
        bgcolour = OV.GetVar('HtmlBgColour')
        if OV.FileExt() == "cif":
          reapfile = "%s%s" % (olx.xf.DataName(current), ".res")
          if not os.path.exists(reapfile):
            action = "export>>reap '%s'" % reapfile
            display = "*EXP/LOAD*"
            highlight = olx.GetVar('HtmlHighlightColour')
          else:
            highlight = olx.GetVar('gui.blue')
            fg = '#ffffff'
            display = "*LOAD RES*"
        else:
          highlight = OV.GetParam('gui.green')
          fg = '#ffffff'
          display = "CIF %s" % display
      else:
        action = 'reap \'%s#%s\'' % (file_name, index)
        highlight = olx.GetVar('linkButton.bgcolor')
      action = 'reap \'%s#%s\'' % (file_name, index)
      name = name.replace("(", "_").replace(")", "_")
      display = display.replace("(", "_").replace(")", "_").replace("_0m_a", ".").replace("_auto", ".")
      html += '''
    $+
      html.Snippet(GetVar(default_link),
      "value=%s",
      "name=%s",
      "onclick=%s",
      "bgcolor=%s",
      "fgcolor=%s",
      )
    $-''' % (display, name, action, highlight, fg)

    html += "</tr></table>"
    name = "%s" % ('multicif.htm')
    OlexVFS.write_to_olex(name, html)
    return "<!-- #include multicif %s;1; -->" % name


mds = MultipleDataset()
olex.registerFunction(mds.check, False, "gui.home.multiple_dataset")
olex.registerFunction(mds.generateHtml, False, "gui.home.multiple_dataset")
