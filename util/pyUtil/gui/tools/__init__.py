import olex
import olx
import olexex
import os
import sys
import OlexVFS
from olexFunctions import OV

debug = OV.IsDebugging()
timer = debug
import glob
global have_found_python_error
have_found_python_error = False

global last_formula
last_formula = ""

global last_element_html
last_element_html = ""

global current_sNum
current_sNum = ""

global custom_scripts_d
custom_scripts_d = {}

haveGUI = OV.HasGUI()

import olexex
import gui
import shutil

import re

import time
import math
global regex_l

regex_l = {}

global cache
cache = {}


gui_green = OV.GetParam('gui.green')
gui_orange = OV.GetParam('gui.orange')
gui_red = OV.GetParam('gui.red')
gui_grey = OV.GetParam('gui.grey')
gui_yellow = OV.GetParam('gui.dark_yellow')

import subprocess


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
      s = prefix + self.name
      s += "\n%s" % (self.full_name)
      if self.content:
        prefix += '\t'
        for c in self.content:
          s += '\n%s%s' % (prefix, c.toStr(prefix))
      return s

    def expand(self, mask, fname=""):
      self.content = []
      if not fname:
        fname = self.name
      for i in os.listdir(fname):
        dn = os.path.normpath(fname + '/' + i)
        if os.path.isdir(dn) and i != '.olex' and i != 'olex2':
          dr = FolderView.node(i, dn)
          dr.expand(mask, dn)
          if len(dr.content):
            self.content.append(dr)
        else:
          if(os.path.splitext(i)[1] in mask):
            self.content.append(FolderView.node(i, dn))

  def list(self, mask=".ins;.res;.cif;.oxm"):
    r = OV.GetParam('user.folder_view_root')
    if not r:
      r = "."
    try:
      f = olx.ChooseDir('Select folder', '%s' % r)
    except RuntimeError:
      f = None
    if f:
      self.root = FolderView.node(f)
      self.root.expand(mask=set(mask.split(';')))
      OV.UpdateHtml()

  def generateHtml(self):
    import OlexVFS
    if not self.root:
      return "&nbsp;"
    OV.SetParam('user.folder_view_root', self.root.name)
    data = self.root.toStr()
    OlexVFS.write_to_olex('folder_view.data', data.encode('utf-8'))
    return "<input type='tree' manage noroot src='folder_view.data' name='fvt'" +\
           " onselect='spy.gui.tools.folder_view.loadStructure(html.GetValue(~name~))'" +\
           " height=200 width=" + str(int(olx.html.ClientWidth('self')) - 50) + ">"

  def loadStructure(self, v):
    if os.path.isfile(v):
      olex.m("reap '%s'" % v)


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
    olx.SetVar('start_where', False)


olex.registerFunction(start_where, False, "gui.tools")


def flash_def_button(control, wait, n):
  highlight_c = OV.GetParam('gui.html.highlight_colour', '##ff0000')
  off_colour = OV.GetParam('gui.action_colour')

  for i in range(n):
    olx.html.SetBG(control, highlight_c)
    OV.Refresh()
    olx.Wait(wait)
    olx.html.SetBG(control, off_colour)
    OV.Refresh()
    olx.Wait(wait)


def flash_gui_control(control, wait=300):
  ''' Flashes a control on the GUI in order to highlight it's position '''
  highlight_c = OV.GetParam('gui.html.highlight_colour', '##ff0000')
  if ';' in control:
    n = int(control.split(';')[1])
    control = control.split(';')[0]
  else:
    n = 2

  if 'DEFBTN' in control:
      flash_def_button(control, wait, n)
      return

  control_name = "IMG_%s" % control.upper()
  if '@' in control:
    print("@ in control")
    control_image = control.lower().split('@')[0]
  else:
    control_image = control

  if not olx.fs.Exists("%son.png" % control_image):
    print("This image %s does not exist. So I can't make it blink" % control_image)
    return

  for i in range(n):
    if "element" in control:
      new_image = "up=%son.png" % control_image
      olx.html.SetImage(control_name, new_image)
    elif control.endswith('_bg'):
      cmd = 'html.setBG(%s,%s)' % (control_image.rstrip('_bg'), highlight_c)
      olex.m(cmd)
    else:
      new_image = "up=%soff.png" % control_image
      olx.html.SetImage(control_name, new_image)
    OV.Refresh()
    olx.Wait(wait)

    if "element" in control:
      new_image = "up=%soff.png" % control
      olx.html.SetImage(control_name, new_image)
    elif control.endswith('_bg'):
      cmd = 'html.setBG(%s,%s)' % (control.rstrip('_bg'), '#fffff')
      olex.m(cmd)
    elif 'cbtn' in control:
      new_image = "up=%son.png" % control_image
      olx.html.SetImage(control_name, new_image)
    else:
      new_image = "up=%shighlight.png" % control_image
      olx.html.SetImage(control_name, new_image)
    OV.Refresh()
    olx.Wait(wait)

  if not control.endswith('_bg'):
    new_image = "up=%soff.png" % control_image
    olx.html.SetImage(control_name, new_image)


olex.registerFunction(flash_gui_control, False, "gui.tools")


def make_single_gui_image(img_txt="", img_type='h2', force=False):
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
    image = TI.make_timage(item_type=alias, item=img_txt, state=state, titleCase=False, force=force)
    name = "%s-%s%s.png" % (img_type, img_txt.lower(), state)
    OlexVFS.save_image_to_olex(image, name, 0)


def inject_into_tool(tool, t, where, befaf='before'):
  import OlexVFS
  txt = OlexVFS.read_from_olex('%s/%s' % (OV.BaseDir(), tool))
  if befaf == 'before':
    txt = txt.replace(where, "%s%s" % (t, where))
  else:
    txt = txt.replace(where, "%s%s" % (where, t))
  OlexVFS.write_to_olex('%s/%s' % (OV.BaseDir(), tool), txt)


def __inject_into_tool(tool, t, where, befaf='before'):
  import OlexVFS
  txt = OlexVFS.read_from_olex('%s/%s' % (OV.BaseDir(), tool))
  if befaf == 'before':
    txt = txt.replace(where, "%s%s" % (t, where))
  else:
    txt = txt.replace(where, "%s%s" % (where, t))
  OlexVFS.write_to_olex('%s%s' % (OV.BaseDir(), tool), u, txt)


def add_tool_to_index(scope="", link="", path="", location="", before="", filetype="", level="h2", state="2", image="", onclick=""):
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
    location = OV.GetParam('%s.gui.location' % scope)
  if not before:
    before = OV.GetParam('%s.gui.before' % scope)
  if not location:
    return

  _ = r"%s/%s" % (OV.BaseDir(), location)
  if os.path.exists(_):
    file_to_write_to = _
  else:
    file_to_write_to = r'%s/etc/gui/blocks/index-%s.htm' % (OV.BaseDir().replace(r"//", "/"), location)
  if not os.path.exists(file_to_write_to):
    print("This location does not exist: %s" % file_to_write_to)
    file_to_write_to = '%s/etc/gui/blocks/index-%s.htm' % (OV.BaseDir().replace(r"//", "/"), "tools")
    before = "top"

  file_to_write_to = file_to_write_to.replace(r"//", "/")
  txt = OlexVFS.read_from_olex(file_to_write_to).decode()

  if onclick:
    OlexVFS.write_to_olex('%s/%s.htm' % (path, link), "")

  if not filetype:
    t = r'''
<!-- #include %s-%s-%s-%s "'%s/%s.htm'";gui\blocks\tool-off.htm;image=%s;onclick=%s;%s; -->''' % (level, location, scope, link, path, link, image, onclick, state)
  else:
    t = r'''
<!-- #includeif IsFileType('%s') %s-%s-%s-%s %s/%s.htm;gui\blocks\tool-off.htm;image=%s;onclick=%s;%s; -->''' % (filetype, level, location, scope, link, path, link, image, onclick, state)

  index_text = ""
  if t not in txt:
    if before.lower() == "top":
      u = "%s\n%s" % (t, txt)
    elif before not in txt or before.lower() == "end":
      u = "%s\n%s" % (txt, t)
    else:
      u = ""
      for line in txt.strip().split("\r\n"):
        if not line:
          continue
        li = line
        if r"<!-- #include" not in line:
          li = ""
        if "%s-%s" % (location, before) in line:
          u += "%s\n%s\n" % (t, li)
        elif before in line:
          u += "%s\n%s\n" % (t, li)
        else:
          u += "%s\n" % line.strip()
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
  logfile = "%s/PythonError.log" % OV.DataDir()
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
    ''' % (logfile)
  else:
    return ""


OV.registerFunction(checkErrLogFile, True, 'gui.tools')


def checkPlaton():
  retVal = '''
  $spy.MakeHoverButton('toolbar-platon', "platon")
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


OV.registerFunction(checkPlaton, True, 'gui.tools')


def MakeElementButtonsFromFormula(action='mode', scope=""):
  # Produces buttons for all atom types currently present in the model. Action 'mode' will go to 'change atom type' mode, action 'select' will simply select the atom types in question

  if debug:
    # print "--- Making Element Formulae"
    t1 = time.time()

  from PilTools import TI
  global last_formula
  global last_element_html
  model_formula = olexex.OlexRefinementModel().currentFormula()
  mf = ["%s:%s" % (x, model_formula[x]) for x in model_formula.keys()]
  mf.sort()

  formula = olx.xf.GetFormula('list')
  if mf == last_formula:
    if olx.fs.Exists("btn-elementHoff.png") == "true":
      return last_element_html

#  from PilTools import ButtonMaker
#  icon_size = OV.GetParam('gui.skin.icon_size')
  totalcount = 0
  btn_dict = {}
  if not formula:
    return
  f = formula.split(',')

  Z_prime = float(olx.xf.au.GetZprime())
  Z = float(olx.xf.au.GetZ())
  html = ""

  isSame = True
  formula_l = []
  for element in f:
    symbol = element.split(':')[0]
    max_ele = float(element.split(':')[1])
    max_ele = round(max_ele, 2)
    present = round(model_formula.get(symbol, 0), 2)

    if symbol != "H":
      totalcount += max_ele

    max_ele = max_ele * Z_prime
    c = ""
    if present < max_ele:
      bgcolour = (250, 250, 250)
      c = 'b'
      isSame = False
    elif present == max_ele:
      bgcolour = (210, 255, 210)
      c = 'g'
    else:
      bgcolour = (255, 210, 210)
      c = 'r'
      isSame = False

    if c:
      img_name = "btn-element%s_%s" % (symbol, c)

    name = "btn-element%s#%s" % (symbol, action)
    if action == "mode":
      target = OV.TranslatePhrase('change_element-target')
      command = 'spy.ElementButtonStates(%s)' % symbol
      namelower = 'btn-element%s' % (name)
    if action == "select":
      target = OV.TranslatePhrase('change_element-target')
      command = 'spy.ElementButtonSelectStates(%s)' % symbol
      namelower = 'btn-element%s' % (name)

    d = {}
    d.setdefault('name', name)
    d.setdefault('scope', scope)
    d.setdefault('img_name', img_name)
    d.setdefault('symbol', symbol)
    d.setdefault('cmds', command)
    d.setdefault('target', target + symbol)
    d.setdefault('bgcolor', OV.GetParam('gui.html.table_firstcol_colour'))

    control = "IMG_%s" % name.upper()
    if debug:
      pass
      # print "  EB1(%s): %.5f" %(control,(time.time() - t1))
    if olx.fs.Exists("%s.png" % img_name) != "true":
      TI.make_element_buttons(symbol)

    if OV.IsControl(control):
      olx.html.SetImage(control, "up=%soff.png,down=%son.png,hover=%shover.png" % (img_name, img_name, img_name))

    html += '''
<input
  name=IMG_BTN-ELEMENT%(symbol)s@%(scope)s
  type="button"
  image="up=%(img_name)soff.png,down=%(img_name)son.png,hover=%(img_name)shover.png"
  hint="%(target)s"
  onclick="%(cmds)s"
  bgcolor=%(bgcolor)s
>
''' % d

  if action == "mode":
    d['namelower'] = 'Table'
    html += '''
  <input
    name=IMG_BTN-ELEMENT...%(scope)s
    type="button"
    image="up=%(namelower)soff.png,down=%(namelower)son.png,hover=%(namelower)shover.png"
    hint="Chose Element from the periodic table"
    onclick="spy.ElementButtonStates('')"
    bgcolor=%(bgcolor)s
  >
  ''' % d


#  OV.write_to_olex('element_buttons.htm', html, 0)

  im_name = 'IMG_BTN-ELEMENT%s' % symbol
  OV.SetImage(im_name, name)

  if isSame:
    OV.SetImage("IMG_TOOLBAR-REFRESH", "up=toolbar-blank.png,down=toolbar-blank.png,hover=toolbar-blank.png")
  else:
    OV.SetImage("IMG_TOOLBAR-REFRESH", "up=toolbar-refresh.png,down=toolbar-refresh.png,hover=toolbar-refresh.png")

  olexex.SetAtomicVolumeInSnumPhil(totalcount)
  last_element_html = html
  f.sort()
  last_formula = f
  return html


def ElementButtonStates(symbol):
  if not symbol:
    e = olx.ChooseElement()
    if not e:
      return
    symbol = e
  if OV.GetParam('olex2.full_mode') == 'name -t=%s' % symbol:
    olex.m('mode off')
  else:
    if olex.f('Sel()') == '':
      olex.m('mode name -t=%s' % symbol)
    else:
      olex.m('name sel %s' % symbol)
      olex.m('sel -u')


global sel_element
global sel_list
sel_element = ""
sel_list = []


def ElementButtonSelectStates(symbol):
  global sel_element
  global sel_list
  control = "IMG_BTN-ELEMENT%s" % symbol
  img_name = "btn-element%s" % (symbol)

  if sel_element == symbol or symbol in sel_list:
    olex.m('sel $%s -u' % symbol)
    sel_element = ""
    sel_list.remove(symbol)
    onoff = "off"
  else:
    olex.m('sel $%s' % symbol)
    sel_element = symbol
    sel_list.append(symbol)
    onoff = "on"
  if OV.IsControl(control):
    OV.SetImage(control, "up=%s%s.png,hover=%son.png" % (img_name, onoff, img_name))


if haveGUI:
  OV.registerFunction(ElementButtonStates)
  OV.registerFunction(ElementButtonSelectStates)
  OV.registerFunction(MakeElementButtonsFromFormula)


def add_mask_content(i, which):
  is_CIF = (olx.IsFileType('cif') == 'true')
  i = int(i)
  global current_sNum
  bases = ['smtbx', 'squeeze']
  base = bases[0]
  current_sNum = OV.ModelSrc()
  contents = olx.cif_model[current_sNum].get('_%s_masks_void_%s' % (base, which))
  if not contents:
    base = bases[1]
    contents = olx.cif_model[current_sNum].get('_%s_masks_void_%s' % (base, which))
    if not contents:
      if is_CIF:
        contents = olx.Cif('_%s_void_nr' % base).split(",")
  user_value = str(OV.GetUserInput(0, "Edit Mask %s for Void No %s" % (which, i), contents[i - 1]))
  idx = i - 1
  _ = list(contents)
  _[idx] = user_value
  olx.cif_model[current_sNum]['_%s_masks_void_content' % base] = _
  OV.UpdateHtml()


OV.registerFunction(add_mask_content)


def copy_mask_infro_from_comment():
  pass


def get_mask_info_old():

  global current_sNum
  import gui
  current_sNum = OV.ModelSrc()
  header_row = gui.tools.TemplateProvider.get_template('mask_output_table_header', force=debug)
  d = {}
  bases = ['smtbx_masks', 'platon_squeeze']
  base = bases[0]
  is_CIF = (olx.IsFileType('cif') == 'true')

  numbers = olx.cif_model[current_sNum].get('_%s_void_nr' % base, None)

  if numbers == ['n/a']:
    return "no mask info"

  if not numbers:
    base = bases[1]
    numbers = olx.cif_model[current_sNum].get('_%s_void_nr' % base)
    if not numbers:
      if is_CIF:
        numbers = olx.Cif('_%s_void_nr' % base).split(",")
        if not numbers:
          return "No mask information"
      else:
        return "No mask information"

  if is_CIF:
    volumes = olx.Cif('_%s_void_volume' % base).split(",")
    electrons = olx.Cif('_%s_void_count_electrons' % base).split(",")
    contents = olx.Cif('_%s_void_content' % base).split(",")
    details = olx.Cif('_%s_details' % base).split(",")

  else:
    volumes = olx.cif_model[current_sNum].get('_%s_void_volume' % base)
    electrons = olx.cif_model[current_sNum].get('_%s_void_count_electrons' % base)
    contents = olx.cif_model[current_sNum].get('_%s_void_content' % base)
    details = olx.cif_model[current_sNum].get('_%s_details' % base)

  t = "<table>"
  t += gui.tools.TemplateProvider.get_template('mask_output_table_header', force=debug)

  for number, volume, electron, content in zip(numbers, volumes, electrons, contents):
    d = {}
    d['number'] = number
    d['electron'] = electron
    d['volume'] = volume
    content = content.strip("'")

    if volume == "n/a":
      return

    if float(volume) < 20:
      continue
    if float(electron) != 0:
      v_over_e = float(volume) / float(electron)
      if v_over_e < 3:
        v_over_e_html = "<font color='red'><b>%.2f</b></font>" % v_over_e
      elif v_over_e > 7:
        v_over_e_html = "<font color='red'><b>%.2f</b></font>" % v_over_e
      else:
        v_over_e_html = "<font color='green'><b>%.2f</b></font>" % v_over_e
    else:
      v_over_e_html = "n/a"

    d['v_over_e'] = v_over_e_html

    content = '%s <a target="Please enter the contents that are present in this void. After re-caluclating the mask, this information will get lost, so please enter it once all solvent masking work has been done." href="spy.add_mask_content(%s,content)">(Edit)</a>' % (content, number)
    details = '<a href="spy.add_mask_content(%s,detail)"> (Edit)</a>' % (number)
    d['content'] = content
    d['details'] = details

    t += gui.tools.TemplateProvider.get_template('mask_output_table_row', force=debug) % d
#  t += "<tr><td>%(details)s</td></tr></table>" %d
  t += "</table>"
  return t


OV.registerFunction(get_mask_info_old, False, 'gui.tools')


def is_masked_moiety_in_formula(txt_formula):
  isSame = False
  if len(txt_formula) > 100:
    return "Too Much Stuff"
  present = olx.xf.au.GetFormula()
  regex = re.compile(r"(?P<ele>[a-zA-Z]) (\s|\b)", re.X | re.M | re.S)
  txt_formula = regex.sub(r'\g<ele>1 ', txt_formula).strip()
  present = regex.sub(r'\g<ele>1 ', present).strip()
  present_l = present.split()
  txt_formula_l = txt_formula.split()
  present_l.sort()
  txt_formula_l.sort()
  isSame = False
  if present_l == txt_formula_l:
    isSame = True
  return isSame


olex.registerFunction(is_masked_moiety_in_formula, False, "gui.tools.is_masked_moiety_in_formula")


def makeFormulaForsNumInfo():
  global current_sNum
  if timer:
    t1 = time.time()

  txt_formula = olx.xf.GetFormula('', 3)
  # if OV.GetVar("makeFormulaForsNumInfo", "") == txt_formula and not OV.GetParam("snum.refinement.use_solvent_mask"):
    # if debug:
      ###print("Formula sNum (2): %.5f" %(time.time() - t1))
    # return OV.GetVar("makeFormulaForsNumInfo_retVal")
  # else:
    #OV.SetVar("makeFormulaForsNumInfo", txt_formula)

  if olx.FileName() == "Periodic Table":
    return "Periodic Table"
  colour = ""

  isSame = gui.tools.is_masked_moiety_in_formula(txt_formula)
  # I don't know why this was here -- it might bite back!
    # if current_sNum != OV.FileName():
      ##current_sNum = OV.FileName()

  l = ['3333', '6667']
  for item in l:
    if item in txt_formula:
      colour = OV.GetParam('gui.red').hexadecimal
  if not colour:
    colour = OV.GetParam('gui.html.formula_colour').hexadecimal
  font_size = OV.GetParam('gui.html.formula_size')
  panelwidth = int(olx.html.ClientWidth('self'))
  q = len(txt_formula) / (panelwidth - (0.60 * panelwidth))
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

  html_formula = olx.xf.GetFormula('html', 1).replace("</sub>", "<font size='2'></font></sub>")
  formula_string = "<font size=%s color=%s>%s</font>" % (font_size, colour, html_formula)
  d = {}
  d.setdefault('cmds', "fixunit xf.au.GetZprime()>>spy.MakeElementButtonsFromFormula()>>html.Update")

  if OV.GetParam("snum.refinement.use_solvent_mask"):
    if isSame:
      img_name = 'toolbar-mask_same'
      OV.SetImage("IMG_TOOLBAR-REFRESH", "up=toolbar-mask_same.png,down=toolbar-mask_same.png,hover=toolbar-mask_same.png")
      d.setdefault('target', "A solvent mask has been used, but your sum formula only shows what is in your model. Please make sure include what has been masked in the formula!")
      d['cmds'] = "html.ItemState * 0 tab* 2 tab-work 1 logo1 1 index-work* 1 info-title 1>>html.ItemState cbtn* 1 cbtn-refine 2 *settings 0 refine-settings 1"

    else:
      img_name = 'toolbar-mask_ok'
      OV.SetImage("IMG_TOOLBAR-REFRESH", "up=toolbar-mask_ok.png,down=toolbar-mask_ok.png,hover=toolbar-mask_ok.png")
      d.setdefault('target', "A solvent mask has been used, and therefore the formula should differ from what is in the model. Nothing to do!")

  else:
    if not isSame:
      img_name = 'toolbar-refresh'
      OV.SetImage("IMG_TOOLBAR-REFRESH", "up=toolbar-refresh.png,down=toolbar-refresh.png,hover=toolbar-refresh.png")
      d.setdefault('target', "Update Formula with current model")
    else:
      img_name = 'toolbar-blank'
      OV.SetImage("IMG_TOOLBAR-REFRESH", "up=blank.png,down=blank.png,hover=blank.png")
      formula = olx.xf.au.GetFormula()
      d.setdefault('target', "Everything is up-to-date")

  d.setdefault('img_name', img_name)
  d.setdefault('bgcolor', OV.GetParam('gui.html.table_firstcol_colour'))
  refresh_button = '''
  <input
    name=IMG_TOOLBAR-REFRESH
    type="button"
    image="up=%(img_name)soff.png,down=%(img_name)son.png,hover=%(img_name)shover.png"
    hint="%(target)s"
    onclick="%(cmds)s"
    bgcolor="%(bgcolor)s"
  >''' % d

  update = '<table border="0" cellpadding="0" cellspacing="0"><tr><td>%s</td><td>%s</td></tr></table>' % (formula_string, refresh_button)
  #fn = "%s_snumformula.htm" %OV.ModelSrc()
  fn = "snumformula.htm"
  OV.write_to_olex(fn, update)
  # if debug:
    ##print("Formula sNum (2): %.5f" %(time.time() - t1))
  retVal = "<!-- #include snumformula %s;1 -->" % fn
  OV.SetVar("makeFormulaForsNumInfo_retVal", retVal)
  return retVal


OV.registerFunction(makeFormulaForsNumInfo)


def make_cell_dimensions_display():
  t1 = time.time()

  global current_sNum
  # if OV.FileName() == current_sNum:
    # return "<!-- #include celldimensiondisplay celldimensiondisplay.htm;1 -->"

  l = ['a', 'b', 'c', 'alpha', 'beta', 'gamma']
  d = {}
  for x in l:
    val = olx.xf.uc.CellEx(x)
    if "90.0" in val and "(" in val or '90(' in val and not "." in val:
      help_txt = "Help from File does not exist. Apologies."
      help = '''
$spy.MakeHoverButton('btn-info@cell@%s',"spy.make_help_box -name=cell-not-quite-90 -popout='False' -helpTxt='%s'")''' % (x, help_txt)
      _ = os.path.join(OV.BaseDir(), "etc", "gui", "help", "cell_angle_not_quite_90.htm")
      if os.path.exists(_):
        help_txt = open(_, 'r').read()
      href = "spy.make_help_box -name=cell-angle-not-quite-90 -popout=False -helpTxt='%s'" % help_txt
      val = '<a href="%s"><font color="%s"><b>%s</b></font></a>' % (href, OV.GetParam('gui.red').hexadecimal, val)
    d[x] = val

  d['volume'] = olx.xf.uc.VolumeEx()
  d['Z'] = olx.xf.au.GetZ()
  d['Zprime'] = olx.xf.au.GetZprime()

  t = gui.tools.TemplateProvider.get_template('snum_cell_display', force=debug) % d
  OV.write_to_olex('celldimensiondisplay.htm', t)
  # if debug:
    # print "Cell: %.5f" %(time.time() - t1)
  return "<!-- #include celldimensiondisplay celldimensiondisplay.htm;1 -->"


OV.registerFunction(make_cell_dimensions_display, True, "gui.tools")


def weightGuiDisplay_new():
  if olx.IsFileType('ires').lower() == 'false':
    return ''
  longest = 0
  retVal = ""
  current_weight = olx.Ins('weight')
  if current_weight == "n/a":
    return ""
  current_weight = current_weight.split()
  if len(current_weight) == 1:
    current_weight = [current_weight[0], '0']
  length_current = len(current_weight)
  suggested_weight = OV.GetParam('snum.refinement.suggested_weight')
  if suggested_weight is None:
    suggested_weight = []
  if len(suggested_weight) < length_current:
    for i in range(length_current - len(suggested_weight)):
      suggested_weight.append(0)
  if suggested_weight:
    for curr, sugg in zip(current_weight, suggested_weight):
      curr = float(curr)
      if curr - curr * 0.01 <= sugg <= curr + curr * 0.01:
        colour = gui_green
      elif curr - curr * 0.1 < sugg < curr + curr * 0.1:
        colour = gui_orange
      else:
        colour = gui_red
      sign = "&#9650;"
      if curr - sugg == 0:
        sign = ""
        sugg = 0
      elif curr - sugg > 0:
        sign = "&#9660;"
      retVal += "%.3f&nbsp;<font color='%s'><b>%s </b></font>&nbsp;|&nbsp;" % (curr, colour, sign)
    html_scheme = retVal.strip("|&nbsp;")
  else:
    html_scheme = current_weight

  wght_str = ""
  for i in suggested_weight:
    wght_str += " %.3f" % i
  txt_tick_the_box = OV.TranslatePhrase("Tick the box to automatically update")
  html = "%s" % html_scheme
  return html


OV.registerFunction(weightGuiDisplay_new, True, "gui.tools")


def weightGuiDisplay():
  if olx.IsFileType('ires').lower() == 'false':
    return ''
  html_scheme = ""
  tol_green, tol_orange = 0.01, 0.1
  current_weight = olx.Ins('weight')
  if current_weight == "n/a":
    return ""
  current_weight = current_weight.split()
  if len(current_weight) == 1:
    current_weight = [current_weight[0], '0']
  length_current = len(current_weight)
  suggested_weight = OV.GetParam('snum.refinement.suggested_weight')
  if suggested_weight is None:
    suggested_weight = []
  if len(suggested_weight) < length_current:
    for i in range(length_current - len(suggested_weight)):
      suggested_weight.append(0)
  if suggested_weight:
    d = {}
    i = 0
    for curr, sugg in zip(current_weight, suggested_weight):
      i += 1
      curr = float(curr)
      if curr < 1:
        prec = 3
      elif curr < 10:
        prec = 2
      elif curr < 100:
        prec = 1
      else:
        prec = 0

      if sugg >= curr * (1 - tol_green) and sugg <= curr * (1 + tol_green):
        colour = gui_green
      elif sugg >= curr * (1 - tol_orange) and sugg <= curr * (1 + tol_orange):
        colour = gui_orange
      else:
        colour = gui_red

      _ = "%%.%sf" % prec
      curr = (_ % curr).lstrip('0')
      sugg = (_ % sugg).lstrip('0')

      dd = {'curr_%i' % i: curr,
            'sugg_%i' % i: sugg,
            'col_%i' % i: colour,
            }
      d.update(dd)
      if html_scheme:
        html_scheme += "|&nbsp;"
      html_scheme += "<font color='%s'>%s(%s)</font>" % (colour, curr, sugg)
  else:
    html_scheme = current_weight
  html_scheme = "<b>%s</b>" % html_scheme

  txt_tick_the_box = OV.TranslatePhrase("Tick the box to automatically update")
  txt_Weight = OV.TranslatePhrase("Weight")
  html = '''
    <a target="%s" href="UpdateWght>>html.Update">%s</a>
    ''' % ("Update Weighting Scheme", html_scheme)

  weight_display = gui.tools.TemplateProvider.get_template('weight_button', force=debug) % d
  return weight_display


OV.registerFunction(weightGuiDisplay, True, "gui.tools")


def number_non_hydrogen_atoms():
  return sum(atom['occu'][0] for atom in self.atoms() if atom['type'] not in ('H', 'Q'))


def getExpectedPeaks():
  orm = olexex.OlexRefinementModel()
  return orm.getExpectedPeaks()


def make_exti_swat_gui():
  html = ""
  exti = olx.xf.rm.Exti()
  if exti and exti != "n/a":
    html = gui.tools.TemplateProvider.get_template('exti_gui', force=debug)
  else:
    swat = olx.xf.rm.SWAT()
    if swat and swat != "n/a":
      html = gui.tools.TemplateProvider.get_template('swat_gui', force=debug)
  if not html:
    html = gui.tools.TemplateProvider.get_template('exti_or_swat_gui', force=debug)
  return html


OV.registerFunction(make_exti_swat_gui, True, "gui.tools")


def refine_swat():
  retVal = ""
  _ = olx.xf.rm.SWAT()
  if "n/a" not in _.lower() and _ != '0':
    if " " in _:
      l = _.split(" ")
    else:
      l = [_]
    for item in l:
      if "(" in item:
        _ = item.split('(')
        swat = _[0]
        esd = _[1].rstrip(')')
        #swat_f = float(swat)
        #_ = len(swat) - len(esd) -2
        #esd_f = float("0.%s%s" %(_*"0", esd))
        #esd = "(%s)"
      else:
        swat = round(float(item), 3)
        esd = ""
        OV.SetParam('snum.refinement.refine_swat', 1)
        OV.SetParam('snum.refinement.refine_swat_tickbox', True)
      if esd:
        retVal += "%s(%s) " % (swat, esd)
      else:
        retVal += "%s " % (swat)
  else:
    OV.SetParam('snum.refinement.refine_swat', 0)
    OV.SetParam('snum.refinement.refine_swat_tickbox', False)
  return retVal


OV.registerFunction(refine_swat, True, "gui.tools")


def refine_extinction():

  retVal = ""
  _ = olx.xf.rm.Exti()

  if "n/a" not in _.lower() and _ != '0':
    if "(" in _:
      _ = _.split('(')
      exti = _[0]
      esd = _[1].rstrip(')')
      exti_f = float(exti)
      _ = len(exti) - len(esd) - 2
      esd_f = float("0.%s%s" % (_ * "0", esd))
    else:
      exti = _
      esd = ""
      OV.SetParam('snum.refinement.refine_extinction', 1)
      OV.SetParam('snum.refinement.refine_extinction_tickbox', True)
    retVal = "%s(%s)" % (exti, esd)
  else:
    OV.SetParam('snum.refinement.refine_extinction', 0)
    OV.SetParam('snum.refinement.refine_extinction_tickbox', False)
  return retVal

  # The stuff below needs careful thinking about. For now, revert back to simple on/off operation. Sorry Guys!

  # snmum.refine_extinction 0: DO NOT refine extinction AGAIN
  # snmum.refine_extinction 1: Try and refine extinction
  # snmum.refine_extinction 2: Refine in any case

  # if getExpectedPeaks() > 2:
    # OV.SetParam('snum.refinement.refine_extinction',1)
    # return "Not Tested"

  #retVal = "n/a"
  #_ = olx.xf.rm.Exti()
  # if "n/a" not in _.lower() and _ != '0':
    #_ = _.split('(')
    #exti = _[0]
    #esd = _[1].rstrip(')')
    #exti_f = float(exti)
    #_ = len(exti) - len(esd) -2
    #esd_f = float("0.%s%s" %(_*"0", esd))

    #_ = OV.GetParam('snum.refinement.refine_extinction',1)
    # if _ == 3:
      #retVal = "%s(%s)"%(exti,esd)
      #retVal += "<font color=%s><b>*&nbsp;</b></font>" %gui_green
    # if _ == 0:
      # OV.SetParam('snum.refinement.refine_extinction_tickbox',False)
      #retVal="not refined<font color=%s><b>*&nbsp;</b></font>" %gui_red
    # else:
      #OV.SetParam('snum.refinement.refine_extinction_tickbox', True)

      # if exti_f/esd_f < 2:
        # print "Extinction was refined to %s(%s). From now on, it will no longer be refined, unless you tick the box in the refinement settings" %(exti, esd)
        # OV.SetParam('snum.refinement.refine_extinction',1)
        #olex.m("DelIns EXTI")
        #retVal = "%s(%s)"%(exti,esd)
      # else:
        #retVal = "%s(%s)"%(exti,esd)
  # else:
    # if OV.GetParam('snum.refinement.refine_extinction_tickbox'):
      #olex.m("AddIns EXTI")

  # return retVal


OV.registerFunction(refine_extinction, True, "gui.tools")


def deal_with_gui_phil(action):
  skin_name = OV.GetParam('gui.skin.name', 'default')
  skin_extension = OV.GetParam('gui.skin.extension', None)

  gui_phil_path = "%s/gui.phil" % (OV.DataDir())
  if action == 'load':
    OV.SetHtmlFontSize()
    OV.SetHtmlFontSizeControls()
    olx.gui_phil_handler.reset_scope('gui')
    gui_skin_phil_path = "%s/etc/skins/%s.phil" % (OV.BaseDir(), skin_name)
    if not os.path.isfile(gui_skin_phil_path):
      gui_skin_phil_path = "%s/gui.params" % (OV.BaseDir())
    if os.path.isfile(gui_skin_phil_path):
      gui_skin_phil = open(gui_skin_phil_path, 'r', encoding="utf-8").read()
      olx.gui_phil_handler.update(phil_string=gui_skin_phil)

    if skin_extension:
      gui_skin_phil_path = "%s/etc/skins/%s.phil" % (OV.BaseDir(), skin_extension)
      if os.path.isfile(gui_skin_phil_path):
        gui_skin_phil = open(gui_skin_phil_path, 'r', encoding="utf-8").read()
        olx.gui_phil_handler.update(phil_string=gui_skin_phil)
  else:
    olx.gui_phil_handler.save_param_file(
      file_name=gui_phil_path, scope_name='gui', diff_only=True)


def get_regex_l(src_file, base=None):
  global regex_l
  if not src_file:
    return False

  # if not src_file in regex_l:
  re_l = []
  l = None
  try:
    l = gui.file_open(src_file, base=base, readlines=True)
  except:
    l = open(src_file, 'r').readlines()
  if not l:
    return None
  for item in l:
    item = item.strip()
    if item.startswith('#') or not item:
      continue
    item_l = item.split("::")
    find = item_l[0].strip().strip("%%")
    replace = item_l[1].strip()
    re_l.append((find, replace))
  regex_l.setdefault('%s' % src_file, re_l)
  return regex_l[src_file]


def run_regular_expressions(txt, src_file=None, re_l=None, specific="", base=None):
  try:
    global regex_l
    if not re_l:
      re_l = get_regex_l(src_file, base=base)

    if timer:
      t_timer = time.time()
    for pair in re_l:
      if specific:
        if pair[0] != specific:
          continue
      regex = re.compile(r"%s" % pair[0], re.X | re.M | re.S | re.U)
      replace = pair[1].strip("'")
      replace = pair[1].strip('"')
      try:
        txt = regex.sub(r"%s" % replace, txt)
      except Exception as err:
        print(err)
    if timer:
      print_timer(tt, t_timer, pad="    ", sep="..")
  except Exception:
    if debug:
      PrintException()
  finally:
    return txt


class LogListen():
  def __init__(self):
    self.printed = []
    OV.registerCallback("onlog", self.onListen)

  def onListen(self, txt):
    self.printed.append(txt)

  def endListen(self):
    OV.unregisterCallback("onlog", self.onListen)
    l = []
    for item in self.printed:
      item = item.split('\r\n')
      for tem in item:
        if type(tem) == str:
          l.append(tem)
        else:
          for em in tem:
            l.append(em)
    return l


class Templates():
  def __init__(self):
    self.templates = {}
    self.get_all_templates()

  def get_template(self, name=None, force=debug, path=None, mask="*.*", marker='{-}', base=None, template_file=None):
    '''
    Returns a particular template from the Template.templates dictionary. If it doesn't exist, then it will try and get it, and return a 'not found' string if this does not succeed.
    -- if force==True, then the template will be reloaded
    -- if path is provided, then this location will also be searched.
    '''
    if not name:
      self.get_all_templates(path=path, mask=mask, marker=marker, template_file=template_file)
      return

    retVal = self.templates.get(name, None)
    if not retVal or force:
      self.get_all_templates(path=path, mask=mask, marker=marker, template_file=template_file)
      retVal = self.templates.get(name, None)
    # if not retVal:
      #import OlexVFS
      #path = os.path.join(path, name)
      #path = path.replace("\\","/")
      #retVal = OlexVFS.read_from_olex(path)
    if not retVal:
      return "Template <b>%s</b> has not been found." % name
    else:
      return retVal

  def get_all_templates(self, template_file=None, path=None, mask="*.*", marker='{-}'):
    '''
    Parses the path for template files.
    '''

    if template_file:
      g = []
      if not os.path.exists(template_file):
        template_file = os.path.join(path, template_file)
      g.append(template_file)

    else:
      if not path:
        path = os.path.join(OV.BaseDir(), 'util', 'pyUtil', 'gui', 'templates')
      if path[-4:-3] != ".":  # i.e. a specific template file has been provided
        g = glob.glob("%s%s%s" % (path, os.sep, mask))
      else:
        g = [path]
      _ = os.path.join(OV.DataDir(), 'custom_templates.html')
      if os.path.exists(_):
        g.append(_)

    for f_path in g:
      include = ["txt", "html", "htm"]
      ext = f_path.split(".")[-1:][0]
      if ext:
        if ext not in include:
          continue
      fc = gui.file_open(f_path, mode='r', base=path)
      if not fc:
        continue
      if not self._extract_templates_from_text(fc, marker=marker):
        name = os.path.basename(os.path.normpath(f_path))
        self.templates[name] = fc
    # for name in self.templates:
      #OlexVFS.write_to_olex(name, self.templates[name])

  def _extract_templates_from_text(self, t, marker):
    mark = marker.split('-')
    regex = re.compile(r't:(.*?)\%s(.*?)\%s' % (mark[0], mark[1]), re.DOTALL)
    m = regex.findall(t)
    if m:
      for item in m:
        name = item[0]
        content = item[1]
        self.templates[name] = content
      return True
    else:
      return False


TemplateProvider = Templates()


def get_diagnostics_colour(scope, item, val, number_only=False):
  grade_1_colour = OV.GetParam('gui.skin.diagnostics.colour_grade1').hexadecimal
  grade_2_colour = OV.GetParam('gui.skin.diagnostics.colour_grade2').hexadecimal
  grade_3_colour = OV.GetParam('gui.skin.diagnostics.colour_grade3').hexadecimal
  grade_4_colour = OV.GetParam('gui.skin.diagnostics.colour_grade4').hexadecimal

  try:
    val = float(val)
    if "shift" in item:
      if val < 0:
        val = -val
  except:
    val = 0

  mindfac = 1
  # if item == 'MinD':
    #mindfac = float(olx.xf.exptl.Radiation())/0.71

  op = OV.get_diag('%s.%s.op' % (scope, item))
  if op == "between":
    soll = OV.get_diag('%s.%s.soll' % (scope, item))
  for i in range(4):
    i += 1
    if op == "greater":
      if val >= OV.get_diag('%s.%s.grade%s' % (scope, item, i)) * mindfac:
        break
    elif op == 'smaller':
      if val <= OV.get_diag('%s.%s.grade%s' % (scope, item, i)) * mindfac:
        break
    elif op == 'between':
      if val - (OV.get_diag('%s.%s.grade%s' % (scope, item, i))) * mindfac <= soll <= val + (OV.get_diag('%s.%s.grade%s' % (scope, item, i))) * mindfac:
        break

  if number_only:
    return i

  if i == 1:
    retVal = grade_1_colour
  elif i == 2:
    retVal = grade_2_colour
  elif i == 3:
    retVal = grade_3_colour
  elif i == 4:
    retVal = grade_4_colour

  return retVal


def get_battery_image(colour, colourize=True):
  from PIL import Image, ImageDraw
  from ImageTools import IT as IT
  name = "battery_%s.png" % colour
  if OlexVFS.exists(name):
    return name
  d_col = {'green': gui_green,
           'yellow': gui_yellow,
           'orange': gui_orange,
           'red': gui_red}
  max_dots = 4
  d_dots = {'green': 4,
            'yellow': 3,
            'orange': 2,
            'red': 1}

  n_dots = d_dots[colour]

  src_battery = os.path.join(OV.BaseDir(), "etc", "gui", "images", "src", "battery_rgb.png")

  IM_battery = Image.open(src_battery)

  bg = Image.new('RGBA', IM_battery.size, OV.GetParam('gui.html.table_bg_colour').rgb)
  im = Image.alpha_composite(bg, IM_battery)
  draw = ImageDraw.Draw(im)
  width, height = bg.size

  col = d_col[colour].rgb
  top_gap = int(height * 0.11)
  bot_gap = int(height * 0.04)
  gaps = int(height * 0.06)

  avail_height = height - top_gap - bot_gap - gaps * (max_dots + 1)
  boxHeight = int(avail_height / max_dots)
  boxWidth = int(width * 0.6)
  for dot in range(n_dots):
    i = max_dots - dot
    top = height - bot_gap - (boxHeight + gaps) * (dot + 1)
    left = int((width - boxWidth) / 2)
    box = (left, top, boxWidth + left, boxHeight + top)
    draw.rectangle(box, fill=col)
  new_width = 18
  new_height = int(im.size[1] / im.size[0] * 18)
  IM = im.resize((new_width, new_height), Image.ANTIALIAS)
  OlexVFS.save_image_to_olex(IM, name, 0)
  return name


def get_data_number():
  try:
    import olex_core
    hkl_stats = olex_core.GetHklStat()
    data = OV.GetParam('snum.refinement.data', None)
    if not data:
      data = hkl_stats.get('DataCount', None)
    if not data:
      try:
        data = int(olx.Cif('_reflns_number_gt'))
      except:
        return data
    if OV.GetParam('user.diagnostics.refinement.dpr.halve_for_non_centro'):
      if not olex_core.SGInfo()['Centrosymmetric']:
        data = int(data / 2)
    return data
  except Exception as err:
    print("An error occured: %s" % err)


def get_Z_prime_from_fraction(string):
  val = string
  if "/" in val:
    _ = val.split("/")
    val = int(_[0]) / int(_[1])
  olx.xf.au.SetZprime(val)


olex.registerFunction(get_Z_prime_from_fraction, False, "gui")


def get_parameter_number():
  parameters = OV.GetParam('snum.refinement.parameters', None)
  if not parameters:
    try:
      parameters = int(olx.Cif('_refine_ls_number_parameters'))
    except:
      pass
  return parameters


def GetDPRInfo():
  hklsrc = OV.HKLSrc()
  retVal = ""
  data = get_data_number()
  parameters = get_parameter_number()
  dpr = None
  if data and parameters:
    dpr = data / parameters

  if dpr:
    if dpr in cache:
      return cache[dpr]

  else:
    return

  dpr_col_number = gui.tools.get_diagnostics_colour('refinement', 'dpr', dpr, number_only=True)
  text_output = ["Data/Parameter ratio is very good",
                 "Data/Parameter ratio is adequate",
                 "Data/Parameter ratio is low",
                 "Data/Parameter ratio is VERY LOW"]
  colour_txt = ["green",
                "yellow",
                "orange",
                "red"]

  idx = 4 - dpr_col_number
  colour = colour_txt[idx]
  name = "battery_%s.png" % colour
  if not OlexVFS.exists(name):
    try:
      name = get_battery_image(colour)
    except:
      name = os.path.join(OV.BaseDir(), "etc", "gui", "images", "src", "battery_%s.png" % colour)
  image = """
  <input
  name="BATTERY-EDIT"
  type="button"
  align="center"
  image="%s"
  hint="%s"
  >
  """ % (name, text_output[idx])

  image = """
  <a target="%s" href="echo '%s'"><zimg src="%s"></a>
  """ % (text_output[idx], text_output[idx], name)

  if dpr <= 10:
    disp_dpr = "%.2f" % dpr
  else:
    disp_dpr = "%.1f" % dpr

  d = {
    'dpr': disp_dpr,
    'image': image,
  }

  t = """
  <table border="0" cellpadding="0" cellspacing="0" align='center'>
    <tr align='center'>
      <td align='center'>
        %(image)s
      </td>
    </tr>
    <tr>
      <td align='center'>
        <font size='-1'>
          <b>&nbsp;&nbsp;%(dpr)s&nbsp;</b>
        </font>
      </td>
    </tr>
  </table>
  """ % d
  retVal = t
  cache[dpr] = t
  return retVal


OV.registerFunction(GetDPRInfo)


def _get_R_values():
  R1 = 'n/a'
  wR2 = 'n/a'

  if olx.IsFileType('cif') == "true":
    R1 = olx.Cif('_refine_ls_R_factor_gt')
    wR2 = olx.Cif('_refine_ls_wR_factor_ref')

  else:
    R1 = OV.GetParam('snum.refinement.last_R1')
    wR2 = OV.GetParam('snum.refinement.last_wR2')
    if not R1 or R1 == 'n/a' or not wR2 or wR2 == 'n/a':
      R1 = olex.f('Ins(R1)')
      wR2 = olex.f('Ins(wR2)')
    if not R1 or R1 == 'n/a' or not wR2 or wR2 == 'n/a':
      import History
      try:
        _ = History.tree.active_node
      except:
        return R1, wR2
      if _ is not None:
        if _.R1:
          R1 = _.R1
        if _.wR2:
          wR2 = _.wR2
      else:
        try:
          look = olex.f('IsVar(snum_refinement_last_R1)')
          if look == "true":
            R1 = olex.f('GetVar(snum_refinement_last_R1)')
          else:
            if olx.IsFileType('cif') == "true":
              R1 = olx.Cif('_refine_ls_R_factor_gt')
            else:
              R1 = olex.f('Lst(R1)')
        except:
          return R1, wR2
  return R1, wR2


def GetRInfo(txt="", d_format='html'):
  if not OV.HasGUI():
    return
  R1, wR2 = _get_R_values()
  if R1 == cache.get('R1', None) and wR2 == cache.get('wR2', None) and 'GetRInfo' in cache:
    if d_format == 'html':
      return cache.get('GetRInfo', 'XXX')
  return FormatRInfo(R1, wR2, d_format)


OV.registerFunction(GetRInfo)


def FormatRInfo(R1, wR2, d_format):
  cache['R1'] = R1
  cache['wR2'] = wR2
  font_size_R1 = olx.GetVar('HtmlFontSizeExtraLarge')
  font_size_wR2 = olx.GetVar('HtmlFontSizeMedium')
  if 'html' in d_format:
    try:
      if R1 == "n/a":
        col_R1 = gui.tools.get_diagnostics_colour('refinement', 'R1', 100)
      else:
        R1 = float(R1)
        col_R1 = gui.tools.get_diagnostics_colour('refinement', 'R1', R1)
        R1 = "%.2f" % (R1 * 100)
      if wR2 == "n/a":
        col_wR2 = gui.tools.get_diagnostics_colour('refinement', 'wR2', 100)
      else:
        wR2 = float(wR2)
        col_wR2 = gui.tools.get_diagnostics_colour('refinement', 'wR2', wR2)
        wR2 = "%.2f" % (wR2 * 100)

      d = {
        'R1': R1,
        'wR2': wR2,
        'font_size_R1': font_size_R1,
        'font_size_wR2': font_size_wR2,
        'font_size_label': str(int(font_size_wR2) - 1),
        'font_colour_R1': col_R1,
        'font_colour_wR2': col_wR2,
        'grey': gui_grey
      }

      if 'report' in d_format:
        t = gett('R_factor_display_report') % d
      else:
        t = gett('R_factor_display') % d
    except:
      disp = R1
      if not R1:
        disp = "No R factors!"
      t = "<td colspan='2' align='center' rowspan='2' align='right'><font size='%s' color='%s'><b>%s</b></font></td>" % (font_size_wR2, gui_grey, disp)
    finally:
      retVal = t

  elif d_format == 'float':
    try:
      t = float(R1)
    except:
      t = 0
    finally:
      retVal = t
  cache['GetRInfo'] = retVal
  return retVal


def launchWithoutConsole(command, args):
  """Launches 'command' windowless and waits until finished"""
  startupinfo = subprocess.STARTUPINFO()
  startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
  return subprocess.Popen([command] + args, startupinfo=startupinfo).wait()


def resize_pdf(f_in, setting='printer'):
  if ".pdf" in f_in:
    small_file = f_in.split(".")[0] + "_small" + f_in.split(".")[1]
    big_file = f_in
  else:
    small_file = f_in + "_small.pdf"
    big_file = f_in + ".pdf"

  options = "-sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/%s -dNOPAUSE -dQUIET -dBATCH -sOutputFile=%s %s" % (setting, small_file, big_file)
  cmd = r'"C:\Program Files\gs\gs9.06\bin\gswin64" ' + options
  os.system(cmd)


OV.registerFunction(resize_pdf, False, 'gui.tools')

gett = TemplateProvider.get_template


def make_input_html_tool(scope, tool):
  fn = "%s_%s_tool.htm" % (scope, tool)
  if OlexVFS.exists(fn) and not debug:
    return fn
  name = "%s_%s" % (scope.upper(), tool.upper())
  d = {'scope': scope,
       'tool': tool,
       'image': tool,
       'name': name,
       'onclick': "", }
  OlexVFS.write_to_olex(fn, gett('input_html_tool') % d)
  return fn


OV.registerFunction(make_input_html_tool, False, 'gui.tools')


def scrub(cmd):
  log = gui.tools.LogListen()
  olex.m(cmd)
  return log.endListen()


from .GetMaskInfo import get_mask_info

global twinlawsfromhklsrc
twinlawsfromhklsrc = {}


def get_twin_law_from_hklf5():
  try:
    global twinlawsfromhklsrc
    src = OV.HKLSrc()
    if src not in twinlawsfromhklsrc:
      cmd = "HKLF5 -e '%s'" % src
      res = scrub(cmd)
      if "HKLF5 file is expected" in " ".join(res):
        htm = "This is not an HKLF5 format hkl file."
      elif "negative batch numbers" in " ".join(res):
        htm = "This is not an HKLF5 format hkl file (no negative batch numbers)."
      else:
        htm = "<b>Batch %s </b>: " % res[2][-1]
        htm += " | ".join([res[4], res[6], res[8]])

      twinlawsfromhklsrc.setdefault(src, htm)
    return twinlawsfromhklsrc[src]
  except:
    return "ERR: Please check 'tools.get_twin_law_from_hklf5'"


OV.registerFunction(get_twin_law_from_hklf5, False, 'tools')


def hklf_5_to_4(filename):
  '''
  Creates a hklf4 file corresponding to the first component of the structure

  This function will only retrieve component 1.

  Need to seperate double-lines based on basf which is harder - making seperate function (Laura Midgely)
  '''

  hklf4name = "%s_hklf4.hkl" % filename
  hklf4 = open(hklf4name, "w")
  # put in a thing to note 'you seem to have positive numbers which correlate to things not in the first component - maybe try with basfs'.
  base_file = open("%s.hkl" % filename, "r")
  for line in base_file:
    line = line.rstrip()
    right = line[-2:]
    if (right == " 1" or right == "-1"):
      hklf4.write(line[:-2] + "\n")
  base_file.close()
  hklf4.close()
  print("done. HKLF4 base file at %s" % hklf4name)
  return


OV.registerFunction(hklf_5_to_4, False, 'tools')


def record_commands():
  res = scrub()


def show_nsff():
  retVal = False
  if OV.have_nsff():
    retVal = True
  return retVal


OV.registerFunction(show_nsff, False, 'tools')


class DisorderDisplayTools(object):
  def __init__(self):
    self.unique_selection = ""
    ##self.haveHighlights = False
    OV.registerFunction(self.hasDisorder, False, 'gui.tools')
    OV.registerFunction(self.show_unique_only, False, 'gui.tools')
    OV.registerFunction(self.make_unique, False, 'gui.tools')
    OV.registerFunction(self.sel_part, False, 'gui.tools')
    OV.registerFunction(self.make_disorder_quicktools, False, 'gui.tools')
    OV.registerFunction(self.set_part_display, False, 'gui.tools')

  def hasDisorder(self, num_return=False):
    retVal = False
    olx_atoms = olexex.OlexRefinementModel()
    parts = olx_atoms.disorder_parts()
    if parts:
      sp = set(parts)
      if len(sp) == 1 and 0 in sp:
        if not num_return:
          retVal = False
      else:
        retVal = True
    if num_return:
      _ = {True: 1, False: 0}
      return _[retVal]
    else:
      return retVal

  def show_unique_only(self):
    if OV.GetParam('user.parts.keep_unique') == True:
      self.make_unique(add_to=True)
      if self.unique_selection:
        olex.m('Sel -u')
        olx.Uniq()
        olx.Sel(self.unique_selection)
        olx.Uniq()

  def make_unique(self, add_to=False):
    if not self.unique_selection:
      add_to = True
    if add_to:
      olex.m('sel -a')
    _ = " ".join(scrub('Sel'))
    _ = _.replace('Sel', ' ')
    while "  " in _:
      _ = _.replace("  ", " ").strip()

    _l = _.split()
    if _:
      if add_to and self.unique_selection:
        _l += self.unique_selection.split()
        _l = list(set(_l))
      unique_selection = " ".join(_l)

    olx.Sel(self.unique_selection)
    olx.Uniq()

  def sel_part(self, part, sel_bonds=True):
    select = OV.GetParam('user.parts.select')
    if not select:
      return
    else:
      olex.m("sel part %s" % part)
      if sel_bonds:
        olex.m("sel bonds where xbond.a.selected==true||xbond.b.selected==true")

  def make_disorder_quicktools(self, scope='main', show_options=True):
    import olexex

    if 'scope' in scope:
      scope = scope.split('scope=')[1]
    parts = set(olexex.OlexRefinementModel().disorder_parts())
    select = OV.GetParam('user.parts.select')
    display = OV.GetParam('user.parts.display')
    parts_display = ""
    sel = ""
    d = {}
    for item in parts:
      _ = None
      if item == 0:
        continue
      else:
        d['part'] = item
      d['parts'] = item
      d['scope'] = scope
      d['show_options'] = show_options
      if select:
        sel = ">>sel part %s" % item
      parts_display += gui.tools.TemplateProvider.get_template('part_0_and_n', force=debug) % d

    dd = {'parts_display': parts_display, 'scope': scope, 'show_options': show_options}
    return self.load_disorder_tool_template(dd)

  def load_disorder_tool_template(self, d):
    if d['show_options']:
      retVal = gui.tools.TemplateProvider.get_template('disorder_quicktool', force=debug) % d
    else:
      retVal = gui.tools.TemplateProvider.get_template('disorder_quicktool_no_options', force=debug) % d
    return retVal

  # def clear_higlights(self):
    # if self.haveHighlights:
      #olex.m("sel %s"%self.haveHighlights)
      #olex.m("mask 48")
      # olex.m("Individualise")
      #self.haveHighlights = False

  def set_part_display(self, parts, part):
    self.show_unique_only()
    olex.m("ShowP 0 %s -v=spy.GetParam(user.parts.keep_unique)" % parts)
    if OV.GetParam('user.parts.select'):
      olex.m('sel part %s' % parts)
      olex.m('sel atom bonds -a')


DisorderDisplayTools_instance = DisorderDisplayTools()


def get_custom_scripts_combo(phil_scope):
  global custom_scripts_d
  if not custom_scripts_d:
    get_custom_scripts()

  _ = "%s.classes.filter" % phil_scope
  filter_s = OV.GetParam(_.lower(), None)

  control = phil_scope + "_SCRIPTS"

  if OV.IsControl(control):
    filter_s = olx.html.GetValue(control + "_FILTER")
  scopes = []
  t_l = []
  for script in custom_scripts_d:
    scope = custom_scripts_d[script].get('scope')
    if scope not in scopes:
      scopes.append(scope)
    if filter_s != 'ALL':
      if not scope == filter_s:
        continue
    t_l.append(script)

  s_l = ";".join(scopes)

  t_l.sort()
  return ";".join(t_l)


OV.registerFunction(get_custom_scripts_combo, False, 'gui.tools')


def get_custom_scripts(file_name, globule, scope):
  global custom_scripts_d
  import gui
  dev_mode = OV.GetParam("olex2.dev_mode", False)
  gui_t = "<b>%s</b>: Please select a script from the above choices." % scope
  OV.write_to_olex("%s_SCRIPT_GUI.htm" % scope, gui_t)

  with open(file_name, 'r') as rFile:
    _ = rFile.readlines()
  for line in _:
    line = line.rstrip()
    if line:
      if line.startswith("s:"):
        script = line[2:]
        script_s = scope + ":" + line[2:]
        if "<-" in script:
          script = script.split("<-")[1]
        try:
          if '.' in script:
            toks = script.split('.')
            script_src = globule[toks[0]]
            script_obj = getattr(script_src, toks[1])
          else:
            script_obj = globule[script]
          custom_scripts_d.setdefault(script, {})
          custom_scripts_d[script].setdefault('obj', script_obj)
        except:
          print("Could not obtain script object %s for %s" % (script, script_s))
          if debug:
            sys.stderr.formatExceptionInfo()
          continue
        try:
          custom_scripts_d[script].setdefault('docstring', script_obj.__doc__)
        except:
          print("Could not evaluate script docstring for %s" % script)
        custom_scripts_d[script].setdefault('display', script_s)
        custom_scripts_d[script].setdefault('scope', scope)
        try:
          gui_t = gui.tools.TemplateProvider.get_template(script + "_gui", template_file=file_name, force=dev_mode)
          custom_scripts_d[script].setdefault('gui', gui_t)
          custom_scripts_d[script]['gui'] = gui_t
        except:
          print("Could not create gui for script %s" % script)


def set_custom_gui(f, scope):
  global custom_scripts_d
  f in custom_scripts_d
  try:
    doc = custom_scripts_d[f].get('docstring')
    gui_t = custom_scripts_d[f].get('gui')
    if "has not been found" in gui_t:
      gui_t = "<b>%s</b>: %s" % (scope, doc)
    OV.write_to_olex("%s_SCRIPT_GUI.htm" % scope, gui_t)
    OV.SetVar("active_custom_function_%s" % scope, f)
  except:
    _ = "--> %s is missing" % f


  #olx.html.SetValue("INFO_DOCSTRING_%s" %scope, _)
OV.registerFunction(set_custom_gui, False, 'gui.tools')


def run_custom_script(*args):
  global custom_scripts_d
  script = args[0]
  # This doesn't work unless these scripts are standalone (as they used to be) so now calling with spy.
  # if script in custom_scripts_d:
    # custom_scripts_d[script]['obj']()
  olex.m("spy.%s()" % script)


OV.registerFunction(run_custom_script, False, 'gui.tools')


def find_movie_folder(directory=None, directory_l=None):
  from gui import report
  if not directory:
    directory = OV.FilePath()
  if not directory_l:
    directory_l = os.path.normpath(OV.FileFull()).split(os.path.sep)
  if not directory or not directory_l:
    return
  name = OV.FileName()
  extension = "*.jpg"
  i = 1
  while not os.path.exists(directory + os.sep + "movie"):
    directory = os.sep.join(directory_l[:-(i)])
    i += 1
    if i == 5:
      return None, None
  directory = directory + os.sep + "movie"
  if OV.FileName() not in directory:
    print("Crystal images found, but crystal name not in path!")
  l = report.sort_images_with_integer_names(OV.ListFiles(os.path.join(directory, "*.jpg")))
  if not l:
    OV.SetParam("snum.metacif.list_crystal_images_files", "")
    return None, None
  OV.SetParam("snum.metacif.list_crystal_images_files", (l))
  OV.SetParam('snum.report.crystal_image', l[0])
  return l[0], l


OV.registerFunction(find_movie_folder, False, 'gui.tools')


def load_res_from_cif():
  reapfile = "%s%s" % (olx.xf.DataName(olx.xf.CurrentData()), ".res")
  if not os.path.exists(reapfile):
    olex.m("export")
  olex.m("reap %s" % reapfile)


OV.registerFunction(load_res_from_cif, False, 'gui.tools')

def set_style_and_scene(style=None, scene=None, src_dir=None, ):
  if not src_dir or "etc/styles" in src_dir:
    src_dir = OV.GetParam('user.def_style_scene_src_dir')
    if "etc/styles" in src_dir:
      dst_dir = os.path.join(OV.DataDir(), 'styles')
      copy_directory(src_dir, dst_dir)
      src_dir = dst_dir

  if not style:
    style = OV.GetParam('user.def_style')
  if not scene:
    scene = OV.GetParam('user.def_scene')
  OV.SetParam('user.def_style', style)
  OV.SetParam('user.def_scene', scene)
  OV.SetParam('user.def_style_scene_src_dir', src_dir)
  olex.m('grad false')
  style_p = os.path.join(src_dir, style + ".glds")
  scene_p = os.path.join(src_dir, scene + ".glsp")

  olex.m("load style %s" % style_p)
  olex.m("load scene %s" % scene_p)


OV.registerFunction(set_style_and_scene, False, 'gui.tools')


def load_periodic_table():
  olex.m('Freeze True')
  olx.Atreap(os.path.join(OV.DataDir(), 'samples', 'Periodic Table', 'Periodic Table.cif'))
  olex.m("mask bonds 0")
  olex.m("rota 2 180")
  olex.m("rota 3 90")
  olex.m("legend false")
  olex.m('Freeze False')


OV.registerFunction(load_periodic_table, False, 'gui.tools')


def load_matplotlib():
  try:
    import matplotlib.pyplot as plt
    return plt
  except Exception as err:
    if "No module named" in repr(err):
      selection = olx.Alert("matplotlib not found",
                            """Error: No working matplotlib installation found!.
Do you want to install this now?""", "YN", False)
      if selection == 'Y':
        if sys.platform[:3] == 'win':
          from olexex import GetHttpFile
          import zipfile
          from zipfile import ZipFile
          import platform
          architecture = platform.architecture()[0]
          arch = '32'
          if not architecture:
            pass
          elif architecture == '64bit':
            arch = '64'
          fn = "site-packages-x%s.zip" %arch
          fn = GetHttpFile("http://www2.olex2.org/olex2-distro/",
                            fn,
                            os.path.join(OV.DataDir(), "tmp"))
          if not fn:
            raise Exception("matplotlib is required by this functionality!")
          with ZipFile(fn) as zip:
            zip.extractall(path=OV.DataDir())
          os.remove(fn)
        else:
          olex.m("pip matplotlib==3.5.1")
        import matplotlib.pyplot as plt
        return plt
      else:
        return None
    else:
      print("Failed to initialise matplotlib: %s" %str(err))
      return None



def plot_xy_xy(xy=[], filename='test.png', title="", marker_size='5', graphing="matplotlib"):

  import numpy as np

  xs = np.array(xy[0][:])
  y_l = []
  for i in range(len(xy) -1):
    y_l.append(np.array(xy[i+1][:]))

  if graphing == 'matplotlib':

    #import matplotlib.pyplot as plt
    import numpy as np
    plt = load_matplotlib()
    plt.style.use('seaborn-whitegrid')
    if not plt:
      return

    # Create some mock data
    t = np.arange(0.01, 10.0, 0.01)
    t = xs
    data1 = y_l[0]
    data2 = y_l[1]
    data3 = y_l[2]
    data4 = y_l[3]

    fig, ax1 = plt.subplots()
    fig, ax2 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('N Beams')
    ax1.set_ylabel('thickness', color=color)
    ax1.plot(t, data1, 'x',  color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    color = 'tab:red'
    ax2.set_xlabel('N Beams')
    ax2.set_ylabel('thickness', color=color)
    ax2.plot(t, data2, 'o', color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    ax3 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax4 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax3.set_ylabel('R_1', color=color)  # we already handled the x-label with ax1
    ax3.plot(t, data3, 'x', color=color)
    ax3.tick_params(axis='y', labelcolor=color)

    ax4.set_ylabel('R_1', color=color)  # we already handled the x-label with ax1
    ax4.plot(t, data4, 'o', color=color)
    ax4.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    p = os.path.join(OV.FilePath(), filename)
    plt.savefig(p, bbox_inches='tight', pad_inches=0.3)
    olx.Shell(p)


def plot_xy(xs, ys, labels=None, filename='test.png', title="", marker_size='6', graphing="matplotlib", colours=None, x_type='float'):
  plot_params = OV.Params().user.graphs.matplotlib


  if not colours:
    colours = {"0":{"0":'tab:red', "1":'tab:red'},
               "1":{"0":'darkgreen', "1":'darkgreen'}
               }
  if not labels:
    labels=[{'x-label': "",
            'y-label': "",
            "series":["", ""]},
            {'x-label': "",
            'y-label': "",
            "series":["", ""]},
            ]

  import numpy as np

  if x_type == 'float':
    xs = np.array([float(x) for x in xs])
  else:
    xs = np.array(xs)



  y_ll = []
  y_l = []


  if len(ys) == 0:
    y_l.append(np.array([float(x) for x in ys[0]]))
    y_ll.append(y_l)
  else:
    for block in ys:
      y_l = []
      for data in block:
        y_l.append(np.array([float(x) for x in data]))
      y_ll.append(y_l)

  if graphing == 'matplotlib':
    plt = load_matplotlib()
    if not plt:
      return
    plt.style.use('seaborn-whitegrid')
    plt.grid(True)
    colour = 'grey'
    ax_colour='black'

    plt.title(title)
    plt.grid(False)
    fig, ax1 = plt.subplots()

    i = 0
    for y_l in y_ll:
      if i == 0:
        j = 0
        for ys in y_l:
          if len(y_ll) > 1:
            ax_colour = colours[str(i)][str(j)]
          try:
            colour = colours[str(i)][str(j)]
          except:
            colour = colour
          if j == 0:
            marker = "o"
            color = colour
          else:
            marker = "x"
          try:
            label = labels[i]['series'][j]
          except:
            label = ""
          ax1.plot(xs,
                  ys,
                  marker,
                  color=colour,
                  markersize=marker_size,
                  linewidth=1,
                  label=label,
                  markerfacecolor='white',
                  markeredgecolor=colour,
                  markeredgewidth=1,
                  )
          ax1.tick_params(axis='y', labelcolor=ax_colour)
          ax1.grid(False)
          if labels:
            ax1.set_xlabel(labels[i]['x-label'])
            ax1.set_ylabel(labels[i]['y-label'])
          j += 1
      if i == 1:
        ax2 = ax1.twinx()
        j = 0
        for ys in y_l:
          if len(y_ll) > 1:
            ax_colour = colours[str(i)][str(j)]
          try:
            colour = colours[str(i)][str(j)]
          except:
            colour = colour
          if j == 0:
            marker = "o"
            color = colour
          else:
            marker = "x"
            color = colours
          try:
            label = labels[i]['series'][j]
          except:
            label = ""
          ax2.plot(xs,
                  ys,
                  marker,
                  color=colour,
                  markersize=marker_size,
                  linewidth=1,
                  label=labels[i]['series'][j],
                  markerfacecolor='white',
                  markeredgecolor=colour,
                  markeredgewidth=1)
          ax2.tick_params(axis='y', labelcolor=ax_colour)
          ax2.grid(False)
          if labels:
            ax2.set_xlabel(labels[i]['x-label'])
            ax2.set_ylabel(labels[i]['y-label'])
          j += 1
      i += 1

    loc = "%s %s %s" %(plot_params.legend_in_out,  plot_params.legend_vertical, plot_params.legend_horizontal)
    loc = loc.strip()

    ax1.set_title(title)
    lines2, labels2 = ax1.get_legend_handles_labels()
    if len(y_ll) > 1:
      lines3, labels3 = ax2.get_legend_handles_labels()
      ax1.legend(lines2 + lines3, labels2 + labels3, loc=loc, bbox_to_anchor=(1, 0.25))
    else:
      ax1.legend(lines2, labels2 , loc=loc, bbox_to_anchor=(1, 0.25))

    p = os.path.join(OV.FilePath(), filename)
    plt.savefig(p, bbox_inches='tight', pad_inches=0.3)
    #olx.Shell(p)
    plt.close()
    return p

  elif graphing == 'plotly':
    import plotly
    print(plotly.__version__)  # version >1.9.4 required
    from plotly.graph_objs import Scatter, Layout
    import plotly.graph_objs as go

    y_title = "Fred"

    data = []
    raw_1 = go.Scatter(
      x=xs,
      y=ys,
      mode='markers',
      marker=dict(size=4,
                  ),
      name='XS_YS'
    )
    data.append(raw_1)

    layout = go.Layout(
      # annotations=[annotation],
      title=title,
      titlefont=dict(
          family='Bahnschrift',
          size=28,
          color='#7f7f7f'
      ),
        xaxis=dict(
            title='Normalised Intensity',
            tickfont=dict(
                family='Bahnschrift',
                size=18,
                color='#7f7f7f'
            ),
            titlefont=dict(
                family='Bahnschrift',
                size=28,
                color='#7f7f7f'
            )
        ),
        yaxis=dict(
            title=y_title,
            tickfont=dict(
                family='Bahnschrift',
                size=18,
                color='#7f7f7f'
            ),
            titlefont=dict(
                family='Bahnschrift',
                size=28,
                color='#7f7f7f'
            )
        )
    )

    fig = go.Figure(data=data, layout=layout)
    p = plotly.offline.plot(fig, filename=filename + '.html')


def is_outlier(points, thresh=3.5):
  import numpy as np
  """
  Returns a boolean array with True if points are outliers and False
  otherwise.

  Parameters:
  -----------
      points : An numobservations by numdimensions array of observations
      thresh : The modified z-score to use as a threshold. Observations with
          a modified z-score (based on the median absolute deviation) greater
          than this value will be classified as outliers.

  Returns:
  --------
      mask : A numobservations-length boolean array.

  References:
  ----------
      Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
      Handle Outliers", The ASQC Basic References in Quality Control:
      Statistical Techniques, Edward F. Mykytka, Ph.D., Editor.
  """
  if len(points.shape) == 1:
    points = points[:, None]
  median = np.median(points, axis=0)
  diff = np.sum((points - median)**2, axis=-1)
  diff = np.sqrt(diff)
  med_abs_deviation = np.median(diff)

  modified_z_score = 0.6745 * diff / med_abs_deviation

  return modified_z_score > thresh


def _clean_scrub(scrub):
  t = " ".join(scrub).strip()
  while "  " in t:
    t = t.replace("  ", " ")
  return t


def get_polyhedra_tau():
  # A very basic implementation of the Geometry Index, currently only for 4-coordinate atoms. https://en.wikipedia.org/wiki/Geometry_index

  cmd = "sel"
  _ = gui.tools.scrub(cmd)[1:]
  t = _clean_scrub(_)
  if not t:
    print("Please select one central atom (usually a metal) or the bonds of interest")
    return
  if not " " in t:
    central_atom = t
    cmd = "sel bonds where '((xbond.a.selected==true) || (xbond.b.selected==true))'"
    olex.m(cmd)
    cmd = "sel bond atoms -u"
    olex.m(cmd)
    cmd = "sel"
    t = _clean_scrub(gui.tools.scrub(cmd)[1:])
  l = t.split()
  l = list(dict.fromkeys(l))
  if l[0] != central_atom:
    l.remove(central_atom)
    l.insert(0, central_atom)

  angles = []
  order = int(len(l) - 1)

  if order == 4:
    ks = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
  elif order == 5:
      ks = [(1, 2), (1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5), (3, 4), (3, 5), (4, 5)]
  else:
    print("Sorry, only 4-coordinate or 5-coordinate Geometry indices are currently implemented")
    return

  for pair in ks:
    cmd = "sel -u"
    olex.m(cmd)
    for idx in pair:
      cmd = "sel  %s %s" % (l[0], l[idx])
      olex.m(cmd)
      cmd = "sel atom bonds"
    olex.m(cmd)
    cmd = "sel atoms -u"
    olex.m(cmd)
    cmd = "sel"
    _ = gui.tools.scrub(cmd)[1:]
    angle = float(_[3].split(":")[1].split("(")[1].split(")")[0])
    angles.append(angle)

  cmd = "sel -u"
  olex.m(cmd)

  angles.sort(reverse=True)
  for item in angles:
    print(item)

  if order == 4:
    tau = -0.00709 * float(angles[0]) - 0.00709 * float(angles[1]) + 2.55
    tau_prime = -0.00399 * float(angles[0]) - 0.01019 * float(angles[1]) + 2.55
    print(">>> tau = %.4f <<<" % tau)
    print("When tau4 is close to 0 the geometry is similar to square planar, while if tau4 is close to 1 then the geometry is similar to tetrahedral.")
    print(">>> tau' = %.4f <<<" % tau_prime)
    print("Extreme values of tau4 and tau4′ denote exactly the same geometries, however tau4′ is always less or equal to tau4 so the deviation from ideal tetrahedral geometry is more visible. If for tetrahedral complex the value of tau4′ parameter is low, then one should check if there are some additional interactions within coordination sphere.")
  elif order == 5:
    tau5 = -0.01667 * float(angles[0]) + 0.01667 * float(angles[1])
    print(">>> tau5 = %.4f <<<" % tau5)
    print("When tau5 is close to 0 the geometry is similar to square pyramidal, while if tau5 is close to 1 the geometry is similar to trigonal bipyramidal")
  print("Source: https://en.wikipedia.org/wiki/Geometry_index")


OV.registerFunction(get_polyhedra_tau, False, "tools")


def label_rsa():
  import olx
  import olexex
  olex.m("rsa")
  args = []
  for a in olexex.OlexRefinementModel()._atoms:
    rsa = a.get('rsa', None)
    if rsa:
      args.append("%s=%s*%s" % (a['label'], a['label'], rsa))
  if args:
    olx.Label(*args, a=True)


OV.registerFunction(label_rsa, False, "tools")

def set_data_parameter_stats_display(target):
  parameters = get_refinement_stats('Parameters')
  #reflections_all = get_refinement_stats('Reflections_all')
  #data_count = get_refinement_stats('DataCount')
  if OV.IsControl(target):
    olx.html.SetLabel(target, f"Parameters: {parameters}")
OV.registerFunction(set_data_parameter_stats_display, False, "tools")
    
def get_refinement_stats(which):
  try:
    stats = olx.xf.RefinementInfo()
    d1 = dict(x.split("=") for x in stats.split(";"))
    d2 = olex_core.GetHklStat()
    d = {**d1, **d2}
    return d.get(which, "n/a")
  except:
    return ("...")

def copy_directory(src, dst):
  try:
    shutil.copytree(src, dst)
    print(f"Directory copied from {src} to {dst}")
  except OSError as e:
    print(f"Error: {e}")


