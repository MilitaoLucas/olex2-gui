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
  datasets = None
  inc_txt = "<!-- #include multicif multicif.htm;1; -->"
  cif_name = None
  cif_mk_time = None

  def __init__(self):
    pass

  def check(self):
    if olx.IsFileType('cif') != 'true':
      return self.find_file_index() != None
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
      name = olx.xf.DataName(i)
      if name == "global" or not name:
        rv.append((i, name, "", "", False))
        continue
      display = ""
      sort = olx.Cif('%s#%i' % (sort_key, i))
      if sort == "n/a":
        sort = name
      if len(name) > 15:
        display = "%s..%s" % (name[:6], name[-6:])
      else:
        display = name
      rv.append((i, name, display, sort, True))
    return rv

  def find_file_index(self):
    if not self.datasets or not self.cif_name:
      return None
    cif_mk_time = os.path.getmtime(self.cif_name)
    if cif_mk_time != self.cif_mk_time:
      return None
    op = os.path.split(self.cif_name)[0]
    cp = os.path.split(olx.FileFull())[0]
    if op == cp:
      file_name = olx.FileName()
      for index, name, display, sk, do_show in self.datasets:
        if name == file_name:
          return  index
    return None

  def generateHtml(self, make_always=False, sort_key='_database_code_depnum_ccdc_archive'):
    current = None
    if olx.IsFileType('cif') != 'true':
      current = self.find_file_index()
      if current is None:
        self.cif_name, self.cif_mk_time, self.datasets = None, None, None
        return ""

    if current is None:
      current = int(olx.xf.CurrentData())
      self.datasets = self.list_datasets(sort_key=sort_key)
      self.datasets.sort(key=lambda x: x[3])
      self.cif_name = olx.FileFull()
      self.cif_mk_time = os.path.getmtime(self.cif_name)

    html = '<table border="0" VALIGN="center" width="100%" cellpadding="1" cellspacing="0" bgcolor="$GetVar(HtmlTableRowBgColour)"><tr>'

    shown_cnt = 0
    is_CIF = OV.FileExt() == "cif"

    for index, name, display, sk, do_show in self.datasets:
      if not do_show:
        continue
      shown_cnt += 1
      fg = OV.GetVar('linkButton.fgcolor')
      if shown_cnt > 1 and ((shown_cnt-1) % 4) == 0:
        html += "</tr><tr width=100%>"
      if index == current:
        if is_CIF:
          reapfile = os.path.join(olx.FilePath(), olx.xf.DataName(current)) + ".res"
          if not os.path.exists(reapfile):
            action = "export>>reap '%s'" % reapfile
            display = "*EXP/LOAD*"
            highlight = olx.GetVar('HtmlHighlightColour')
          else:
            action = "reap '%s'" % reapfile
            highlight = olx.GetVar('gui.blue')
            fg = '#ffffff'
            display = "*LOAD RES*"
        else:
          action = 'reap \'%s#%s\'' % (self.cif_name, index)
          highlight = OV.GetParam('gui.green')
          fg = '#ffffff'
          display = "CIF %s" % display
      else:
        action = 'reap \'%s#%s\'' % (self.cif_name, index)
        highlight = olx.GetVar('linkButton.bgcolor')
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
    OlexVFS.write_to_olex("multicif.htm", html)
    return self.inc_txt


mds = MultipleDataset()
olex.registerFunction(mds.check, False, "gui.home.multiple_dataset")
olex.registerFunction(mds.generateHtml, False, "gui.home.multiple_dataset")
