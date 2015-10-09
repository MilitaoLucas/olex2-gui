from __future__ import division
import olex
import olx
import os
import sys
import OlexVFS
from olexFunctions import OlexFunctions
OV = OlexFunctions()

global have_found_python_error
have_found_python_error= False

global last_formula
last_formula = ""

global current_sNum
current_sNum = ""

haveGUI = OV.HasGUI()

import olexex

import re

import time

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
    try:
      f = olx.ChooseDir('Select folder', '%s' %r)
    except RuntimeError:
      f = None
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


def flash_gui_control(control, wait=300):
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

  if not olx.fs.Exists("%son.png" %control_image):
    print "This image %s does not exist. So I can't make it blink" %control_image
    return

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
    olx.Wait(wait)

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
    olx.Wait(wait)

  if not control.endswith('_bg'):
    new_image = "up=%soff.png" %control_image
    olx.html.SetImage(control_name,new_image)

olex.registerFunction(flash_gui_control, False, "gui.tools")

def make_single_gui_image(img_txt="", img_type='h2'):
  import PilTools
  import OlexVFS
  TI = PilTools.TI
  states = ["on", "off", "highlight", "", "hover", "hoveron"]
  alias = img_type
  for state in states:
    if img_type == "h2":
      alias = "h1"
    elif img_type == "h1":
      alias = img_type
      img_type = "h2"
    image = TI.make_timage(item_type=alias, item=img_txt, state=state, titleCase=False)
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


def add_tool_to_index(scope="", link="", path="", location="", before="", filetype="", level="h2", state="2"):
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

  _ = r"%s/%s" %(OV.BaseDir(), location)
  if os.path.exists(_):
    file_to_write_to = _
  else:
    file_to_write_to = r'%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir().replace(r"//","/"), location)
  if not os.path.exists(file_to_write_to):
    print "This location does not exist: %s" %file_to_write_to
    file_to_write_to = '%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir().replace(r"//","/"), "tools")
    before = "top"

  file_to_write_to = file_to_write_to.replace(r"//","/")
  txt = OlexVFS.read_from_olex(file_to_write_to)


  if not filetype:
    t = r'''
<!-- #include %s-%s-%s-%s %s/%s.htm;gui\blocks\tool-off.htm;image=%s;onclick=;2; -->''' %(level, location, scope, link, path, link, link)
  else:
    t = r'''
<!-- #includeif IsFileType('%s') %s-%s-%s-%s %s/%s.htm;gui\blocks\tool-off.htm;image=%s;onclick=;2; -->''' %(filetype, level, location, scope, link, path, link, link)


  index_text = ""
  if t not in txt:
    if before.lower() == "top":
      u = "%s\n%s" %(t, txt)
    elif before not in txt or before.lower() == "end":
      u = "%s\n%s" %(txt, t)
    else:
      u = ""
      for line in txt.strip().split("\r\n"):
        if not line:
          continue
        li = line
        if r"<!-- #include" not in line: li = ""
        if "%s-%s" %(location, before) in line:
          u += "%s\n%s\n" %(t, li)
        elif before in line:
          u += "%s\n%s\n" %(t, li)
        else:
          u += "%s\n" %line.strip()
    OlexVFS.write_to_olex(file_to_write_to, u, 0)
    index_text = u
  else:
    if run:
      OlexVFS.write_to_olex(file_to_write_to, t, 0)
    else:
      if not index_text:
        text = txt
      else:
        text = index_text
      OlexVFS.write_to_olex(file_to_write_to, text, 0)

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
  retVal = '''
  <a href='platon' target='Open Platon'>
  <zimg border='0' src='toolbar-platon.png'></a>
  '''
  try:
    if olx.GetVar("HavePlaton") == "True":
      return retVal
    else:
      return ""
  except:
    pass
  prg_name = "platon"
  if sys.platform[:3] == "win":
    prg_name += ".exe"
  have_platon = olx.file.Which(prg_name)
  if have_platon:
    olx.SetVar("HavePlaton", True)
    return retVal
  else:
    olx.SetVar("HavePlaton", False)
    return ""
OV.registerFunction(checkPlaton,True,'gui.tools')


def MakeElementButtonsFromFormula(action='mode', scope = ""):
  ## Produces buttons for all atom types currently present in the model. Action 'mode' will go to 'change atom type' mode, action 'select' will simply select the atom types in question

  t1 = time.time()

  from PilTools import TI
  global last_formula

  current_formula = olexex.OlexRefinementModel().currentFormula()

  #if current_formula == last_formula:
    #return

#  from PilTools import ButtonMaker
#  icon_size = OV.GetParam('gui.skin.icon_size')
  totalcount = 0
  btn_dict = {}
  f = olx.xf.GetFormula('list')
  if not f:
    return
  f = f.split(',')

  Z_prime = float(olx.xf.au.GetZprime())
  Z = float(olx.xf.au.GetZ())
  html = ""

  isSame = True


  for element in f:
    symbol = element.split(':')[0]
    max = float(element.split(':')[1])
    max = round(max, 2)
    present = round(current_formula.get(symbol,0),2)
    if symbol != "H":
      totalcount += max

    max = max*Z_prime
    c = ""
    if present < max:
      bgcolour = (250,250,250)
      c = 'b'
      isSame = False
    elif present ==  max:
      bgcolour = (210,255,210)
      c = 'g'
    else:
      bgcolour = (255,210,210)
      c = 'r'
      isSame = False

    if c:
      img_name = "btn-element%s_%s" %(symbol, c)

    name = "btn-element%s#%s" %(symbol,action)
    if action == "mode":
      target = OV.TranslatePhrase('change_element-target')
      command = 'spy.ElementButtonStates(%s)' %symbol
      namelower = 'btn-element%s' %(name)
    if action == "select":
      target = OV.TranslatePhrase('change_element-target')
      command = 'spy.ElementButtonSelectStates(%s)' %symbol
      namelower = 'btn-element%s' %(name)

    d = {}
    d.setdefault('name', name)
    d.setdefault('scope', scope)
    d.setdefault('img_name', img_name)
    d.setdefault('symbol', symbol)
    d.setdefault('cmds', command)
    d.setdefault('target', target + symbol)
    d.setdefault('bgcolor', OV.GetParam('gui.html.table_firstcol_colour'))

    control = "IMG_%s" %name.upper()
    #print
    #print "  EB1: %.5f" %(time.time() - t1)
    if olx.fs.Exists("%s.png" %img_name) != "true":
      TI.make_element_buttons(symbol)

    if OV.IsControl(control):
      olx.html.SetImage(control,"up=%soff.png,down=%son.png,hover=%shover.png" %(img_name,img_name,img_name))

    html += '''
<input
  name=IMG_BTN-ELEMENT%(symbol)s@%(scope)s
  type="button"
  image="up=%(img_name)soff.png,down=%(img_name)son.png,hover=%(img_name)shover.png"
  hint="%(target)s"
  onclick="%(cmds)s"
  bgcolor=%(bgcolor)s
>
''' %d

  if action == "mode":
    d['namelower'] = 'Table'
    html +=  '''
  <input
    name=IMG_BTN-ELEMENT...%(scope)s
    type="button"
    image="up=%(namelower)soff.png,down=%(namelower)son.png,hover=%(namelower)shover.png"
    hint="Chose Element from the periodic table"
    onclick="spy.ElementButtonStates('')"
    bgcolor=%(bgcolor)s
  >
  ''' %d

  if current_formula != last_formula:
    last_formula = current_formula

#  OV.write_to_olex('element_buttons.htm', html, 0)

  im_name='IMG_BTN-ELEMENT%s' %symbol
  OV.SetImage(im_name, name)

  if isSame:
    OV.SetImage("IMG_TOOLBAR-REFRESH","up=toolbar-blank.png,down=toolbar-blank.png,hover=toolbar-blank.png")
  else:
    OV.SetImage("IMG_TOOLBAR-REFRESH","up=toolbar-refresh.png,down=toolbar-refresh.png,hover=toolbar-refresh.png")

  olexex.SetAtomicVolumeInSnumPhil(totalcount)
  return html

def ElementButtonStates(symbol):
  if not symbol:
    e = olx.ChooseElement()
    if not e:  return
    symbol = e
  if OV.GetParam('olex2.full_mode') == 'name -t=%s' %symbol:
    olex.m('mode off')
  else:
    if olex.f('Sel()') == '':
      olex.m('mode name -t=%s' %symbol)
    else:
      olex.m('name sel %s' %symbol)
      olex.m('sel -u')

global sel_element
global sel_list
sel_element = ""
sel_list = []

def ElementButtonSelectStates(symbol):
  global sel_element
  global sel_list
  control = "IMG_BTN-ELEMENT%s" %symbol
  img_name = "btn-element%s" %(symbol)

  if sel_element == symbol or symbol in sel_list:
    olex.m('sel $%s -u' %symbol)
    sel_element = ""
    sel_list.remove(symbol)
    onoff = "off"
  else:
    olex.m('sel $%s' %symbol)
    sel_element = symbol
    sel_list.append(symbol)
    onoff = "on"
  if OV.IsControl(control):
    OV.SetImage(control,"up=%s%s.png,hover=%son.png" %(img_name,onoff, img_name))

if haveGUI:
  OV.registerFunction(ElementButtonStates)
  OV.registerFunction(ElementButtonSelectStates)
  OV.registerFunction(MakeElementButtonsFromFormula)


def makeFormulaForsNumInfo():
  global current_sNum
  t1 = time.time()

  if olx.FileName() == "Periodic Table":
    return "Periodic Table"

  isSame = False
  colour = ""
  txt_formula = olx.xf.GetFormula('', 3)
  if len(txt_formula) > 100:
    return "Too Much Stuff"
  present = olx.xf.au.GetFormula()
  regex = re.compile(r"(?P<ele>[a-zA-Z]) (\s|\b)", re.X|re.M|re.S)
  txt_formula = regex.sub(r'\g<ele>1 ',txt_formula).strip()
  present = regex.sub(r'\g<ele>1 ',present).strip()
  if present == txt_formula:
    isSame = True
    if current_sNum != OV.FileName():
      current_sNum = OV.FileName()

  l = ['3333', '6667']
  for item in l:
    if item in txt_formula:
      colour = OV.GetParam('gui.red').hexadecimal
  if not colour:
    colour = OV.GetParam('gui.html.formula_colour').hexadecimal
  font_size = OV.GetParam('gui.html.formula_size')
  panelwidth = int(olx.html.ClientWidth('self'))
  q = len(txt_formula)/(panelwidth - (0.6*panelwidth))
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

  if not isSame:
    img_name = 'toolbar-refresh'
    OV.SetImage("IMG_TOOLBAR-REFRESH","up=toolbar-refresh.png,down=toolbar-refresh.png,hover=toolbar-refresh.png")
  else:
    img_name = 'toolbar-blank'
    OV.SetImage("IMG_TOOLBAR-REFRESH","up=blank.png,down=blank.png,hover=blank.png")
    formula = present

  html_formula = olx.xf.GetFormula('html',1)
  formula_string = "<font size=%s color=%s>%s</font>" %(font_size, colour, html_formula)

  d = {}
  d.setdefault('img_name', img_name)
  d.setdefault('cmds', "fixunit xf.au.GetZprime()>>spy.MakeElementButtonsFromFormula()>>html.Update")
  d.setdefault('target', "Update Formula with current model")
  d.setdefault('bgcolor', OV.GetParam('gui.html.table_firstcol_colour'))
  refresh_button = '''
  <input
    name=IMG_TOOLBAR-REFRESH
    type="button"
    image="up=%(img_name)soff.png,down=%(img_name)son.png,hover=%(img_name)shover.png"
    hint="%(target)s"
    onclick="%(cmds)s"
    bgcolor=%(bgcolor)s
  >''' %d

  update = '<table border="0" cellpadding="0" cellspacing="0"><tr><td>%s</td><td>%s</td></tr></table>'%(formula_string, refresh_button)
  OV.write_to_olex('snumformula.htm', update)
  #print "Formula sNum (2): %.5f" %(time.time() - t1)

  return "<!-- #include snumformula snumformula.htm;1 -->"
OV.registerFunction(makeFormulaForsNumInfo)


def make_cell_dimensions_display():
  t1 = time.time()

  global current_sNum
  #if OV.FileName() == current_sNum:
    #return "<!-- #include celldimensiondisplay celldimensiondisplay.htm;1 -->"

  l = ['a', 'b', 'c', 'alpha', 'beta', 'gamma']
  d = {}
  for x in l:
    val = olx.xf.uc.CellEx(x)
    if "90.0" in val and "(" in val or '90(' in val and not "." in val:
      help_txt = "Help from File does not exist. Apologies."
      help = '''
$spy.MakeHoverButton('btn-info@cell@%s',"spy.make_help_box -name=cell-not-quite-90 -popout='False' -helpTxt='%s'")''' %(x, help_txt)
      _ = os.sep.join([OV.BaseDir(), "etc", "gui", "help", "cell_angle_not_quite_90.htm"])
      if os.path.exists(_):
        help_txt = open(_,'r').read()
      href = "spy.make_help_box -name=cell-angle-not-quite-90 -popout=False -helpTxt='%s'" %help_txt
      val = '<a href="%s"><font color="%s"><b>%s</b></font></a>' %(href, OV.GetParam('gui.red').hexadecimal, val)
    d[x] = val

  d['volume'] = olx.xf.uc.VolumeEx()
  d['Z'] = olx.xf.au.GetZ()
  d['Zprime'] = olx.xf.au.GetZprime()

  t = '''
  <tr bgcolor=$GetVar(HtmlTableBgColour)>
    <td width='33%%'>
      &nbsp;<b>a</b> = %(a)s
    </td>

    <td width='34%%'>
      &nbsp;<b>&alpha;</b> = %(alpha)s&deg;
    </td>

    <td width='33%%'>
      &nbsp;<b>Z</b> = %(Z)s
    </td>
  </tr>

  <tr align='left' bgcolor=$GetVar(HtmlTableBgColour)>

    <td width='33%%'>
      &nbsp;<b>b</b> = %(b)s
    </td>

    <td width='34%%'>
      &nbsp;<b>&beta;</b> = %(beta)s&deg;
    </td>

    <td width='33%%'>
      &nbsp;<b>Z'</b> = %(Zprime)s
    </td>
  </tr>

  <tr align='left' bgcolor=$GetVar(HtmlTableBgColour)>
    <td width='34%%' >
      &nbsp;<b>c</b> = %(c)s
    </td>
    <td width='33%%'>
      &nbsp;<b>&gamma;</b> = %(gamma)s&deg;
    </td>
    <td width='33%%'>
      &nbsp;<b>V</b> = %(volume)s
    </td>
  </tr>
  ''' %d
  OV.write_to_olex('celldimensiondisplay.htm', t)
  #print "Cell: %.5f" %(time.time() - t1)
  return "<!-- #include celldimensiondisplay celldimensiondisplay.htm;1 -->"

OV.registerFunction(make_cell_dimensions_display,True,"gui.tools")



def hasDisorder():
  olx_atoms = olexex.OlexRefinementModel()
  parts = olx_atoms.disorder_parts()
  if not parts:
    return False
  else:
    sp = set(parts)
    if len(sp) == 1 and 0 in sp:
      return False
    else:
      return True
OV.registerFunction(hasDisorder,False,'gui.tools')

def sel_part(part,sel_bonds=True):
  select = OV.GetParam('user.parts.select')
  if not select:
    return
  else:
    olex.m("sel part %s" %part)
    if sel_bonds:
      olex.m("sel bonds where xbond.a.selected==true||xbond.b.selected==true")
OV.registerFunction(sel_part,False,'gui.tools')

def make_disorder_quicktools(scope='main'):
  import olexex
  parts = set(olexex.OlexRefinementModel().disorder_parts())
  select = OV.GetParam('user.parts.select')
  parts_display = ""
  sel = ""
  for item in parts:
    if select:
      sel = ">>sel part %s" %item
    if item == 0:
      continue
    if item == 1 or item == 2:
      parts_display += "<a href='ShowP 0 %s -v=spy.GetParam(user.parts.keep_unique)>>spy.gui.tools.sel_part(%s)'><b>PART %s</b></a> | " %(item, item, item)
    else:
      parts_display += "<a href='ShowP 0 %s -v=spy.GetParam(user.parts.keep_unique)>>spy.gui.tools.sel_part(%s)'><b>%s</b></a> | " %(item, item, item)

  checkbox_unique = '''
    <font size=$GetVar(HtmlFontSizeControls)>
  <input
    type='checkbox'
    bgcolor="GetVar('HtmlTableBgColour')"
    name='KEEP_UNIQUE@%s'
    checked="spy.GetParam('user.parts.keep_unique')"
    oncheck="spy.SetParam('user.parts.keep_unique','true')>>uniq"
    onuncheck="spy.SetParam('user.parts.keep_unique','false')"
    target="Keep showing single fragments when switching the PART view"
    onclick=""
    value=''
  >
  </font>'''%scope


  checkbox_sel = '''
    <font size=$GetVar(HtmlFontSizeControls)>
  <input
    type='checkbox'
    bgcolor="GetVar('HtmlTableBgColour')"
    name='SELECT_PARTS@%s'
    checked="spy.GetParam('user.parts.select')"
    oncheck="spy.SetParam('user.parts.select','true')"
    onuncheck="spy.SetParam('user.parts.select','false')"
    target="Auto-Select PARTS"
    onclick=""
    value=''
  >
  </font>'''%scope


  txt = r'''
  <td width='23%%'>
    <b>Show PART 0 AND</b>
  </td>
  <td width='38%%' align='left'>
  %s
    <a href='ShowP'><b>All</b></a>
  </td>

  <td width='4%%' align='right'>
  Sel
  </td>

  <td width='4%%' align='right'>
  %s
  </td>

  <td width='5%%' align='right'>
  Unique
  </td>

  <td width='4%%' align='right'>
  %s
  </td>

  <td width='20%%' align='right'>
  <font size="$GetVar('HtmlFontSizeControls')">
  <input
    type='combo'
    width='100%%'
    height="$GetVar('HtmlInputHeight')"
    name='set_label_content_disorder@%s'
    value='Labels'
    items="Occupancy<-o;Chem Occ.<-co;PART No<-p;Link-Code<-v;Labels<-l"
    bgcolor="$GetVar('HtmlInputBgColour')"
    onchange="spy.ChooseLabelContent(html.GetValue('~name~'))"
    readonly='readonly'
  >
  </font>
  </td>
  ''' %(parts_display, checkbox_sel, checkbox_unique, scope)
  return txt
OV.registerFunction(make_disorder_quicktools,False,'gui.tools')

def deal_with_gui_phil(action):
  skin_name = OV.GetParam('gui.skin.name', 'default')
  skin_extension = OV.GetParam('gui.skin.extension', None)

  gui_phil_path = "%s/gui.phil" %(OV.DataDir())
  if action == 'load':
    OV.SetHtmlFontSize()
    OV.SetHtmlFontSizeControls()
    olx.gui_phil_handler.reset_scope('gui')
    gui_skin_phil_path = "%s/etc/skins/%s.phil" %(OV.BaseDir(), skin_name)
    if not os.path.isfile(gui_skin_phil_path):
      gui_skin_phil_path = "%s/gui.params" %(OV.BaseDir())
    if os.path.isfile(gui_skin_phil_path):
      gui_skin_phil_file = open(gui_skin_phil_path, 'r')
      gui_skin_phil = gui_skin_phil_file.read()
      gui_skin_phil_file.close()
      olx.gui_phil_handler.update(phil_string=gui_skin_phil)

    if skin_extension:
      gui_skin_phil_path = "%s/etc/skins/%s.phil" %(OV.BaseDir(), skin_extension)
      if os.path.isfile(gui_skin_phil_path):
        gui_skin_phil_file = open(gui_skin_phil_path, 'r')
        gui_skin_phil = gui_skin_phil_file.read()
        gui_skin_phil_file.close()
        olx.gui_phil_handler.update(phil_string=gui_skin_phil)
  else:
    olx.gui_phil_handler.save_param_file(
      file_name=gui_phil_path, scope_name='gui', diff_only=True)


def run_regular_expressions(txt, re_l, specific = ""):
  for pair in re_l:
    if specific:
      if pair[0] != specific:
        continue
    regex = re.compile(r"%s" %pair[0], re.X|re.M|re.S)
    replace = pair[1].strip("'")
    replace = pair[1].strip('"')
    txt = regex.sub(r"%s" %replace, txt)
  return txt
