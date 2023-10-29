import olex
import olx
import OlexVFS
import os
from olexFunctions import OV

#global CURR_CIF_FILE_NAME
#CURR_CIF_FILE_NAME = None

#global CURR_CIF_FILE_LIST
#CURR_CIF_FILE_LIST = []

#global CURR_CIF_FILE_FOLDER
#CURR_CIF_FILE_FOLDER = None


def BGColorForValue(value):
  if value == '' or value == '?':
    return "#FFDCDC"
  return OV.GetParam('gui.html.input_bg_colour')


class MultipleDataset:
  def __init__(self):
    #self.CURR_CIF_FILE_NAME = CURR_CIF_FILE_NAME
    #self.CURR_CIF_FILE_FOLDER = CURR_CIF_FILE_FOLDER
    #self.CURR_CIF_FILE_LIST = CURR_CIF_FILE_LIST
    self.CURR_CIF_FILE_NAME = None
    self.CURR_CIF_FILE_FOLDER = None
    self.CURR_CIF_FILE_LIST = []

  def check(self):
    # if self.CURR_CIF_FILE_FOLDER:
      # if self.CURR_CIF_FILE_FOLDER != OV.FilePath():
        # return False
    # if self.CURR_CIF_FILE_NAME:
      ###self.CURR_CIF_FILE_NAME = CURR_CIF_FILE_NAME
      # return True
    if olx.IsFileType('cif') == 'false':
      if not any(OV.ModelSrc() in item for item in self.CURR_CIF_FILE_LIST):
        return False
    else:
      if int(olx.xf.DataCount()) <= 1:
        return False
    return True

  def generateHtml(self, make_always=False, sort_key='_database_code_depnum_ccdc_archive'):
    #global CURR_CIF_FILE_NAME
    #global CURR_CIF_FILE_LIST
    #global CURR_CIF_FILE_FOLDER
    current = None
    html = '<table border="0" VALIGN="center" width="100%" cellpadding="1" cellspacing="0" bgcolor="$GetVar(HtmlTableRowBgColour)"><tr>'

    if olx.IsFileType('cif') == 'true':
      if self.CURR_CIF_FILE_NAME != OV.FileFull():
        self.CURR_CIF_FILE_NAME = None
        self.CURR_CIF_FILE_LIST = []
    else:
      if not any(OV.ModelSrc() in item for item in self.CURR_CIF_FILE_LIST):
        self.CURR_CIF_FILE_LIST = []

    if not self.CURR_CIF_FILE_FOLDER or self.CURR_CIF_FILE_FOLDER != OV.FilePath():
      self.CURR_CIF_FILE_FOLDER = OV.FilePath()

    if not self.CURR_CIF_FILE_NAME or self.CURR_CIF_FILE_NAME != OV.FileName():
      if olx.IsFileType('cif') == 'true':
        self.CURR_CIF_FILE_NAME = OV.FileFull()
        current = int(olx.xf.CurrentData())

    if not self.CURR_CIF_FILE_LIST:
      cnt = int(olx.xf.DataCount())
      sort = 0
      for i in range(0, cnt):
        if olx.IsFileType('cif') == 'true':
          if olx.xf.DataName(i) == "global" or not olx.xf.DataName(i):
            cnt -= 1
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
        current = 0
        self.CURR_CIF_FILE_LIST.append((i, name, display, sort))
    else:
      cnt = len(self.CURR_CIF_FILE_LIST)
      for i in range(0, cnt):
        if OV.ModelSrc() in self.CURR_CIF_FILE_LIST[i]:
          current = i
          break

    if (cnt % 3) == 0:
      td_width = '33'
    elif (cnt % 4) == 0:
      td_width = '25'
    elif (cnt % 2) == 0:
      td_width = '50'
    else:
      td_width = '25'

    self.CURR_CIF_FILE_LIST = sorted(self.CURR_CIF_FILE_LIST, key=lambda x: x[3])
    for i in range(0, cnt):
      fg = OV.GetVar('linkButton.fgcolor')
      index = self.CURR_CIF_FILE_LIST[i][0]
      name = self.CURR_CIF_FILE_LIST[i][1]
      display = self.CURR_CIF_FILE_LIST[i][2]
      if i > 0 and (i % 4) == 0:
        html += "</tr><tr width=100%>"
      if i == current:
        bgcolour = OV.GetVar('HtmlBgColour')
        if OV.FileExt() == "cif":
          reapfile = "%s%s" % (olx.xf.DataName(olx.xf.CurrentData()), ".res")
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
          if not self.CURR_CIF_FILE_NAME:
            _ = OV.FileName() + ".cif"
          else: _ = (self.CURR_CIF_FILE_NAME) + str(index)
          action = 'reap %s#' % _
          highlight = OV.GetParam('gui.green')
          fg = '#ffffff'
          display = "CIF %s" % display
      else:
        action = 'reap \'%s#' % (self.CURR_CIF_FILE_NAME) + str(index) + "'"
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
    #name = "%s_%s" %(os.path.split(CURR_CIF_FILE_NAME)[1].replace(' ', '_'), 'multicif.htm')
    name = "%s_%s" % (self.CURR_CIF_FILE_NAME, 'multicif.htm')
    OlexVFS.write_to_olex(name, html)
    return "<!-- #include multicif %s;1; -->" % name


mds = MultipleDataset()
olex.registerFunction(mds.check, False, "gui.home.multiple_dataset")
olex.registerFunction(mds.generateHtml, False, "gui.home.multiple_dataset")
