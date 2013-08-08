from __future__ import division
import olex
import olx
import os

global formula
global formula_string

formula = ""
formula_string = ""

from olexFunctions import OlexFunctions
OV = OlexFunctions()

global have_found_python_error
have_found_python_error= False




class FolderView:
  root = None
  class node:
    name = None
    full_name = None
    parent = None
    content = None

    def __init__(self, name, full_name=None):
      self.name = name
      if full_name:
        self.full_name = full_name
      else:
        self.full_name = name

    def toStr(self, prefix=""):
      s = prefix+self.name
      s += "\n%s" %(self.full_name)
      if self.content:
        prefix += '\t'
        for c in self.content:
          s += '\n%s%s' %(prefix,c.toStr(prefix))
      return s

    def expand(self, mask, fname=""):
      self.content = []
      if not fname:
        fname = self.name
      for i in os.listdir(fname):
        dn = os.path.normpath(fname + '/' + i)
        if os.path.isdir(dn) and i != '.olex':
          dr = FolderView.node(i, dn)
          dr.expand(mask, dn)
          if len(dr.content):
            self.content.append(dr)
        else:
          if( os.path.splitext(i)[1] in mask):
            self.content.append(FolderView.node(i, dn))


  def list(self, mask=".ins;.res;.cif;.oxm"):
    r = OV.GetParam('user.folder_view_root')
    if not r:
      r = "."
    f = olx.ChooseDir('Select folder', '%s' %r)
    if f:
      self.root = FolderView.node(f)
      self.root.expand(mask=set(mask.split(';')))
      olx.html.Update()

  def generateHtml(self):
    import OlexVFS
    if not self.root:
      return "&nbsp;"
    OV.SetParam('user.folder_view_root', self.root.name)
    data = self.root.toStr()
    OlexVFS.write_to_olex('folder_view.data', data.encode('utf-8'))
    return "<input type='tree' manage noroot src='folder_view.data' name='fvt'"+\
           " onselect='spy.gui.tools.folder_view.loadStructure(html.GetValue(~name~))'"+\
           " height=200 width=" + str(int(olx.html.ClientWidth('self'))-50) + ">"

  def loadStructure(self, v):
    if os.path.isfile(v):
      olex.m("reap '%s'" %v)

fv = FolderView()
olex.registerFunction(fv.list, False, "gui.tools.folder_view")
olex.registerFunction(fv.generateHtml, False, "gui.tools.folder_view")
olex.registerFunction(fv.loadStructure, False, "gui.tools.folder_view")



def start_where():
  if olx.IsFileLoaded() == "false":
    return
  from gui import SwitchPanel
#  if olx.xf.au.GetAtomCount() == "0" and olx.IsFileType('ires') == "true":
#    SwitchPanel('work')
#    flash_gui_control('btn-solve')
#    print "Use 'Solve' button in tab 'Work' to solve the structure."
#    return

  if olx.IsVar('start_where') == 'false':
    where = OV.GetParam('user.start_where').lower()
    SwitchPanel(where)
    olx.SetVar('start_where',False)

olex.registerFunction(start_where, False, "gui.tools")


def flash_gui_control(control):
  ''' Flashes a control on the GUI in order to highlight it's position '''
  if ';' in control:
    n = int(control.split(';')[1])
    control = control.split(';')[0]
  else:
    n = 2

  control_name = "IMG_%s" %control.upper()
  if '@' in control:
    print "@ in control"
    control_image = control.lower().split('@')[0]
  else:
    control_image = control
  for i in xrange(n):
    if "element" in control:
      new_image = "up=%son.png" %control_image
      olx.html.SetImage(control_name,new_image)
    elif control.endswith('_bg'):
      cmd = 'html.setBG(%s,%s)' %(control_image.rstrip('_bg'), OV.GetParam('gui.html.highlight_colour','##ff0000'))
      olex.m(cmd)
    else:
      new_image = "up=%soff.png" %control_image
      olx.html.SetImage(control_name,new_image)
    OV.Refresh()
    olx.Wait(300)

    if "element" in control:
      new_image = "up=%soff.png" %control
      olx.html.SetImage(control_name,new_image)
    elif control.endswith('_bg'):
      cmd = 'html.setBG(%s,%s)' %(control.rstrip('_bg'), '#fffffe')
      olex.m(cmd)
    else:
      new_image = "up=%shighlight.png" %control_image
      olx.html.SetImage(control_name,new_image)
    OV.Refresh()
    olx.Wait(300)

  if not control.endswith('_bg'):
    new_image = "up=%soff.png" %control_image
    olx.html.SetImage(control_name,new_image)

olex.registerFunction(flash_gui_control, False, "gui.tools")

def make_single_gui_image(img_txt="", img_type='h2'):
  from PilTools import timage
  import OlexVFS
  timage = timage()
  states = ["on", "off", "highlight", "", "hover", "hoveron"]
  alias = img_type
  for state in states:
    if img_type == "h2":
      alias = "h1"
    elif img_type == "h1":
      alias = img_type
      img_type = "h2"
    image = timage.make_timage(item_type=alias, item=img_txt, state=state, titleCase=False)
    name = "%s-%s%s.png" %(img_type, img_txt.lower(), state)
    OlexVFS.save_image_to_olex(image, name, 0)


def inject_into_tool(tool, t, where,befaf='before'):
  import OlexVFS
  txt = OlexVFS.read_from_olex('%s/%s' %(OV.BaseDir(),tool))
  if befaf == 'before':
    txt = txt.replace(where, "%s%s" %(t, where))
  else:
    txt = txt.replace(where, "%s%s" %(where, t))
  OlexVFS.write_to_olex('%s%s' %(OV.BaseDir(), tool), u, txt)


def add_tool_to_index(scope="", link="", path="", location="", before="", filetype="", level="h2"):
  import OlexVFS
  if not OV.HasGUI:
    return

  if not scope:
    return

  if not link:
    return

  if not path:
    return

  ''' Automatically add a link to GUI to an Olex2 index file. '''
  if not location:
    location = OV.GetParam('%s.gui.location' %scope)
  if not before:
    before = OV.GetParam('%s.gui.before' %scope)
  if not location:
    return
  txt = OlexVFS.read_from_olex('%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir(), location))

  if not filetype:
    t = r'''
<!-- #include %s-%s-%s-%s %s/%s.htm;gui\blocks\tool-off.htm;image=%s;onclick=;2; -->''' %(level, location, scope, link, path, link, link)
  else:
    t = r'''
<!-- #includeif IsFileType('%s') %s-%s-%s-%s %s/%s.htm;gui\blocks\tool-off.htm;image=%s;onclick=;2; -->''' %(filetype, level, location, scope, link, path, link, link)


  index_text = ""
  if t not in txt:
    if before not in txt or before.lower() == "end":
      u = "%s\n%s" %(txt, t)
    else:
      u = ""
      for line in txt.strip().split("\r\n"):
        if not line:
          continue
        if "%s-%s" %(location, before) in line:
          u += "%s\n%s\n" %(t, line)
        else:
          u += "%s\n" %line.strip()
    OlexVFS.write_to_olex('%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir(), location), u, 0)
    index_text = u
  else:
    if run:
      OlexVFS.write_to_olex('%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir(), location), t, 0)
    else:
      if not index_text:
        text = txt
      else:
        text = index_text
      OlexVFS.write_to_olex('%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir(), location), text, 0)

  make_single_gui_image(link, img_type=level)

def checkErrLogFile():
  logfile = "%s/PythonError.log" %OV.DataDir()
  logfile = logfile.replace("\\\\", "\\")
  global have_found_python_error
  if not have_found_python_error:
    f = open(logfile, 'r')
    if len(f.readlines()) > 0:
      have_found_python_error = True
    f.close()
  if have_found_python_error:
    return '''
    <a href='external_edit "%s"'>
    <zimg border='0' src='toolbar-stop.png'></a>
    '''%(logfile)
  else: return ""
OV.registerFunction(checkErrLogFile,True,'gui.tools')

def checkPlaton():
  have_platon = olx.file.Which('platon.exe')
  if have_platon:
    return '''
    <a href='platon' target='Open Platon'>
    <zimg border='0' src='toolbar-platon.png'></a>
    '''
  else: return ""
OV.registerFunction(checkPlaton,True,'gui.tools')

def makeFormulaForsNumInfo():
  global formula
  global formula_string

  if olx.FileName() == "Periodic Table":
    return "Periodic Table"
  else:
    colour = ""
    txt_formula = olx.xf.GetFormula()
    if txt_formula == formula:
      return formula_string
    formula = txt_formula
    l = ['3333', '6667']
    for item in l:
      if item in txt_formula:
        colour = OV.GetParam('gui.red').hexadecimal
    if not colour:
      colour = OV.GetParam('gui.html.formula_colour').hexadecimal
    font_size = OV.GetParam('gui.html.formula_size')

    panelwidth = int(olx.html.ClientWidth('self'))
    
    q = len(txt_formula)/(panelwidth - (0.6*panelwidth))
#    print len(txt_formula), q
    if q > 0.26:
      font_size -= 4
    elif q > 0.23:
      font_size -= 3
    elif q > 0.20:
      font_size -= 2
    elif q > 0.16:
      font_size -= 1
    if font_size < 1:
      font_size = 1
    html_formula = olx.xf.GetFormula('html',1)
    formula_string = "<font size=%s color=%s>%s</font>" %(font_size, colour, html_formula)
    return formula_string
OV.registerFunction(makeFormulaForsNumInfo)

