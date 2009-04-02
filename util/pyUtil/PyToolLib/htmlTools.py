"""
Various generic tools for creating and using HTML.
"""
import os
import sys
import olx

import time
#import sys
#sys.path.append(r".\src")

from olexFunctions import OlexFunctions
OV = OlexFunctions()

global active_mode
active_mode = None

global last_mode
last_mode = None


def makeHtmlTable(list):
  """ Pass a list of dictionaries, with one dictionary for each table row.
  
  In each dictionary set at least the 'varName':(the name of the variable) and 'itemName':(the text to go in the first column).
  If you require a combo box set 'items':(a semi-colon separated list of items).
  If you want a multiline box set 'multiline':'multiline'.
  If you want more than one input box in a row, set 'varName' and 'itemName' plus anything else under a sub-dictionary called 'box1',
  'box2','box3'.
  If you wish to change any of the defaults such as bgcolor, height, width, etc., these can be set in the dictionary to be passed.
  """
  text = ''
  for input_d in list:
    row_d = {}
    row_d.setdefault('itemName',input_d['itemName'])
    row_d.setdefault('ctrl_name', "SET_%s" %str.upper(input_d['varName']))
    
    boxText = ''
    for box in ['box1','box2','box3']:
      if box in input_d.keys():
        box_d = input_d[box]
        box_d.setdefault('value', 'GetVar(%s)' %box_d['varName'])
        box_d.setdefault('ctrl_name', "SET_%s" %str.upper(box_d['varName']))
        box_d.setdefault('bgcolor','spy.bgcolor(%s)' %box_d['ctrl_name'])
        box_d.setdefault('onchange',"spy.ChangeMetaCif(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %box_d)
        box_d.setdefault('onleave',"spy.ChangeMetaCif(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %box_d)
        boxText += makeHtmlInputBox(box_d)
    if boxText:
      row_d.setdefault('input',boxText)
    else:
      input_d.setdefault('value', 'GetVar(%s)' %input_d['varName'])
      input_d.setdefault('ctrl_name', "SET_%s" %str.upper(input_d['varName']))
      input_d.setdefault('onchange',"spy.ChangeMetaCif(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %input_d)
      input_d.setdefault('onleave',"spy.ChangeMetaCif(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %input_d)
      input_d.setdefault('bgcolor','spy.bgcolor(%s)' %input_d['ctrl_name'])
      row_d.setdefault('input',makeHtmlInputBox(input_d))
      row_d.update(input_d)
      
    text += makeHtmlTableRow(row_d)

  return OV.Translate(text)

def makeHtmlInputBox(inputDictionary):
  if inputDictionary.has_key('items'):
    inputDictionary.setdefault('type','combo')
    inputDictionary.setdefault('readonly','readonly')
    
  if inputDictionary.has_key('multiline'):
    inputDictionary.setdefault('height','35')
    
  dictionary = {
    'width':'55%%',
    'height':'18',
    'onchange':'',
    'onleave':'',
    'items':'',
    'multiline':'',
    'type':'text',
    'readonly':'',
    'manage':'',
    'data':'',
    'label':'',
    'bgcolor':'',
  }
  dictionary.update(inputDictionary)
  
  htmlInputBoxText = '''
<input 
type="%(type)s"
%(multiline)s
width="%(width)s"  
height="%(height)s" 
name="%(ctrl_name)s"
value="%(value)s" 
items="%(items)s" 
label="%(label)s"
onchange="%(onchange)s"
onleave="%(onleave)s"
%(readonly)s
bgcolor="%(bgcolor)s"
>
'''%dictionary
  
  return htmlInputBoxText

def makeHtmlTableRow(dictionary):
  dictionary.setdefault('font', 'size="2"')
  dictionary.setdefault('trVALIGN','center')
  dictionary.setdefault('trALIGN','left')
  dictionary.setdefault('fieldWidth','40%%')
  dictionary.setdefault('fieldVALIGN','center')
  dictionary.setdefault('fieldALIGN','left')
  
  if 'chooseFile' in dictionary.keys():
    chooseFile_dict = dictionary['chooseFile']
    if 'var' in chooseFile_dict.keys():
      href = "SetVar(%(var)s,FileOpen('%(caption)s','%(filter)s','%(folder)s'))>>updatehtml" %chooseFile_dict
    else:
      href = "%(function)sFileOpen('%(caption)s','%(filter)s','%(folder)s'))>>updatehtml" %chooseFile_dict
      pass
    #chooseFileText = '''
#<tr>
  #<a href="SetVar(%(var)s,FileOpen('%(caption)s','%(filter)s','%(folder)s'))>>updatehtml">
    #<zimg border="0" src="gui/images/toolbar-open.png">
  #</a>
#</tr>
#''' %chooseFile_dict
    chooseFileText = '''
    <tr>
    <a href="%s">
    <zimg border="0" src="gui/images/toolbar-open.png">
    </a>
    </tr>
    ''' %href
    dictionary['chooseFile'] = chooseFileText
  else:
    dictionary.setdefault('chooseFile','')
    
  FieldText = ''
  for field in ['field1','field2']:
    if field in dictionary.keys():
      field_d = dictionary[field]
      field_d.setdefault('itemName', '')
      field_d.setdefault('fieldVALIGN','center')
      field_d.setdefault('fieldALIGN','left')
      field_d.setdefault('fieldWidth','20%%')
      field_d.setdefault('font','size="2"')
      FieldText += """
                <td VALIGN="%(fieldVALIGN)s" ALIGN="%(fieldALIGN)s" width="%(fieldWidth)s" colspan=1>
                <b>%(itemName)s</b>
                </td>""" %field_d
  if FieldText:
    dictionary.setdefault('fieldText',FieldText)
    
    htmlTableRowText = '''
<tr VALIGN="%(trVALIGN)s" ALIGN="%(trALIGN)s" NAME="%(ctrl_name)s">
                     %(fieldText)s  
                     <td VALIGN="center" colspan=2>
                     <font %(font)s> 
                     %(input)s
                     </font>
                     </td>
                     %(chooseFile)s
</tr>''' %dictionary

  else:	
    htmlTableRowText = '''
<tr VALIGN="%(trVALIGN)s" ALIGN="%(trALIGN)s" NAME="%(ctrl_name)s">
                     <td VALIGN="%(fieldVALIGN)s" ALIGN="%(fieldALIGN)s" width="%(fieldWidth)s" colspan=2>
                     <b>%(itemName)s</b>	
                     </td>   
                     <td VALIGN="center" colspan=2>
                     <font %(font)s> 
                     %(input)s
                     </font>
                     </td>
                     %(chooseFile)s
</tr>''' %dictionary

  return htmlTableRowText

def make_help_box(args):
  str = ""
  name = args.get('name', None)
  popout = args.get('popout', False)
  if popout == 'false':
    popout = False
  else:
    popout = True
    
  if not name:
    return
  if "-h3-" in name:
    t = name.split("-h3-")
    help_src = t[1]
    title = help_src.replace("-", " ")
    
  elif "-" in name:
    title = name.replace("-", " ")
    help_src = name
  else:
    title = name
    help_src = name
  titleTxt = OV.TranslatePhrase("%s" %title)
  titleTxt = titleTxt.title()
  helpTxt = OV.TranslatePhrase("%s-help" %help_src)
  helpTxt = helpTxt.replace("\r", "")
  helpTxt = format_help(helpTxt)
  
  if not popout:
    str += r'''
<zimg border='0' src='olex_help_logo.png'>
<!-- #include help-%s gui\%s.htm;gui\blocks\tool-off.htm;image=%s;onclick=;1; -->
''' %(name, name, name)
    
    return_items = r'''
<a href="spy.make_help_box -name='%s' -popout=True>>htmlhome"><zimg border='0' src='popout.png'></a>
<a href=htmlhome><zimg border='0' src='return.png'></a>''' %name
    
  else:
    str = ""
    return_items = ""
    
  str += r'''
<!-- #include tool-top gui/blocks/help-top.htm;image=blank;1; -->
<tr VALIGN='center' NAME=%s bgcolor="$getVar(gui_html_table_firstcol_colour)">
      <td colspan=1 width="2" bgcolor="$getVar(gui_html_table_firstcol_colour)"></td>
      <td>
      <font size='+2'>
      <b>	
      %s
      </b>
      </font>
      </td>
</tr>
<tr>
      <td valign='top' width="2" bgcolor="$getVar(gui_html_table_firstcol_colour)"></td>
      <td>	
      <font size='+1'>
      %s
      </font>
      </td>
</tr>
<tr>
<td colspan=1 width="2" bgcolor="$getVar(gui_html_table_firstcol_colour)"></td>
<td align='right'>
%s
</tr></td>
<!-- #include tool-footer gui/blocks/tool-footer.htm;1; -->
''' %(name, titleTxt, helpTxt, return_items)
  wFilePath = r"%s-help.htm" %name
  #str = unicode(str)#
  str = str.replace(u'\xc5', 'angstrom')
  OV.write_to_olex(wFilePath, str)
  boxWidth = 320
  length = len(helpTxt)
  #boxHeight = int(length/2.8)
  boxHeight = int(length/2.9) + 100
  if boxHeight > 500:
    boxHeight = 500
  #boxHeight = 800
  
  x = 10
  y = 50
  mouse = True
  if mouse:
    mouseX = int(olx.GetMouseX())
    mouseY = int(olx.GetMouseY())
    y = mouseY
    if mouseX > 300:
      x = mouseX + 10 - boxWidth
    else:
      x = mouseX - 10
  if popout:
    pop_name = "%s-help"% name
    olx.Popup(pop_name, wFilePath, "-b=tc -t='%s' -w=%i -d='echo' -h=%i -x=%i -y=%i" %(name, boxWidth, boxHeight, x, y))
    olx.html_SetBorders(pop_name,5)
    olx.Popup(pop_name, wFilePath, "-b=tc -t='%s' -w=%i -d='echo' -h=%i -x=%i -y=%i" %(name, boxWidth, boxHeight, x, y))
    olx.html_SetBorders(pop_name,5)
  else:
    olx.html_Load(wFilePath) 
#  popup '%1-tbxh' 'basedir()/etc/gui/help/%1.htm' -b=tc -t='%1' -w=%3 -h=%2 -x=%4 -y=%5"> 
OV.registerMacro(make_help_box, 'name-Name of the Help Box&;popout-True/False')

def make_warning_html(colspan):
  txt = "htmltool-warning"
  txt = OV.TranslatePhrase(txt)
  first_col = make_table_first_col() 
  html = '''
       %s
       <td colspan="%s" bgcolor="$getVar(gui_html_highlight_colour)">
       <b>&nbsp;%s</b>
       </td>
       </tr>''' %(first_col, colspan, txt)
  return html
OV.registerFunction(make_warning_html)

def make_table_first_col(make_help=False, help_image='large'):
  if not make_help:
    help = ""
  else:
    help = make_help_href(make_help, image=help_image)
  html ='''
<tr>
<td valign='top' width='2' align='center' bgcolor='$getVar(gui_html_table_firstcol_colour)'>
%s
</td>
''' %help
  return html

def make_help_href(make_help, image='small'):
  if image == 'small':
    image = 'info_tiny_fc.png'
  else:
    image = 'info.png'
  help='''
<a href="spy.make_help_box -name='%s' -popout='%s'" target="Help me with this">
<zimg border="0" src="%s">
</a>''' %(make_help[0], make_help[1], image)
  return help

def make_input_text_box(d):
  d.setdefault('data', '')
  d.setdefault('manage', '')
  d.setdefault('value', '')
  d.setdefault('label', '')
  d.setdefault('onleave', '')
  html = '''
<input
       bgcolor="$getVar(gui_html_input_bg_colour)"
       type="text"
       name="%(ctrl_name)s"
       value="%(value)s"
       width="%(width)s"
       height="%(height)s"
       label="%(label)s"
       onleave="%(onleave)s"
       %(manage)s
       data="%(data)s"
>''' %d
  return html

def make_tick_box_input(d):
  d.setdefault('manage', '')
  d.setdefault('data', '')
  html = """
<input
  type='checkbox'
  bgcolor='GetVar(gui_html_input_bg_colour)'
  width='%(width)s'
  height='%(height)s'
  name='%(ctrl_name)s'
  %(state)s
  oncheck='%(oncheck)s'
  onuncheck='%(onuncheck)s'
  %(value)s
  value=''
  %(manage)s
  data='%(data)s'
  >&nbsp;
""" %d
  return html

def make_spin_input(d):
  html = """
<input
  type='spin'
  name='%(ctrl_name)s'
  width='%(width)s'
  height='%(height)s'
  max='%(max)s'
  bgcolor='GetVar(gui_html_input_bg_colour)'
  value='GetVar(%(varName)s)'
  onchange='%(onchange)s'
  >""" %d
  return html

def make_input_button(d):
  d.setdefault('ondown', '')
  d.setdefault('onup', '')
  d.setdefault('onclick', '')
  d.setdefault('hint','')
  html = '''
<input 
  bgcolor="$getVar(gui_html_input_bg_colour)" 
  type="button" 
  name="%(name)s_BUTTON" 
  value="%(value)s" 
  width="%(width)s" 
  height="%(height)s"
  hint="%(hint)s"
  flat
''' %d
  if d['onclick']:
    html += '''
  onclick="%(onclick)s"
>
''' %d
  elif d['ondown'] or d['onup']:
    html += '''
  ondown="%(ondown)s"
  onup="%(onup)s"
  >
''' %d
  else:
    html += '\n>\n'
  return html

def format_help(string):
  import re
  

  ## find all occurances of strings between XX. These are command line entities.
  regex = re.compile(r"  XX (.*?)( [^\XX\XX]* ) XX ", re.X)
  m = regex.findall(string)
  colour = OV.FindValue('gui_grey')
  colour = "#aaaaaa"
  if m:
    #s = regex.sub(r"<tr bgcolor='$getVar(gui_html_table_firstcol_colour)><td><b><font color='%s'>\2</font></b> " %colour, string)
    s = regex.sub(r"<tr bgcolor='#ffffee'><td><b><font size='2' color='%s'>>>\2</font></b></td></tr>" %colour, string)

  else:
    s = string
  string = s
  
  ## find all occurances of strings between ~. These are the entries for the table.
  regex = re.compile(r"  ~ (.*?)( [^\~\~]* ) ~ ", re.X)
  m = regex.findall(string)
  colour = OV.FindValue('gui_html_highlight_colour')
  if m:
    s = regex.sub(r"<tr><td><b><font color='%s'>\2</font></b> " %colour, string)
  else:
    s = string
    
  ## find all occurances of strings between@. These are the table headers.
  string = s
  regex = re.compile(r"  @ (.*?)( [^\@\@]* ) @ ", re.X)
  m = regex.findall(string)
  colour = "#232323"
  if m:
    s = regex.sub(r"<tr bgcolor='$getVar(gui_html_table_firstcol_colour)'><td><b>\2</b></td></tr><tr><td>", string)
  else:
    s = string
    
  ## find all occurances of strings between &. These are the tables.
  string = s
  #regex = re.compile(r"  (&&) (.*?)( [^\&\&]* ) (&&) ", re.X)
  regex = re.compile(r"  (&&) (.*?) (&&) ", re.X)
  #regex = re.compile(r"  & (.*?)( [^\&\&]* ) & ", re.X)
  m = regex.findall(string)
  if m:
    s = regex.sub(r"<table>\2</table>", string)
  else:
    s = string
    
  return s

def reg_glossary(self, string):
  regex = re.compile(r"  \[ g \s (.*? \w+); ( [^\[\]]* ) \] ", re.X)  
  m = regex.findall(string)
  glossary_to_insert = []
  if m:
    link = r"list_table_items?catID=&entry=&table=category&itemss=glossary#" 
    s = regex.sub(r"<a href='%s\2'>\1</a>" %link, string)
  else:
    s = string
  if m:
    for item in m:
      glossary_to_insert.append(item[1].replace(" ", "_"))
      
  regex = re.compile(r"  \[ l \s (.*? \w+); ( [^\[\]]* ) \] ", re.X)  
  m = regex.findall(s)
  if m:
    t = regex.sub(r"<a href='\2'>\1</a>", s)
  else:
    t = s
    
  return t, glossary_to_insert

def reg_command(self, string):
  regex = re.compile(r"  ~ (.*?)( [^\~\~]* ) ~ ", re.X)  
  m = regex.findall(string)
  colour = OV.FindValue('gui_html_highlight_colour')
  if m:
    s = regex.sub(r"<br><br><b><font color=%s>\2</font></b><br>" %colour, string)
  else:
    s = string
  return s

def changeBoxColour(ctrl_name,colour):
  if olx.GetValue(ctrl_name) == '?':
    olx.html_SetBG(ctrl_name,colour)
  else:
    olx.html_SetBG(ctrl_name,OV.FindValue('gui_html_input_bg_colour'))
  return ''
OV.registerFunction(changeBoxColour)


def switchButton(name,state):
  if state == 'off':
    copy_from = "%soff.png" %name
    copy_to = "%s.png" %name
    OV.CopyVFSFile(copy_from, copy_to)
  else:
    copy_from = "%son.png" %name
    copy_to = "%s.png" %name
    OV.CopyVFSFile(copy_from, copy_to)
  OV.htmlReload()
  return ""
OV.registerFunction(switchButton)



def bgcolor(ctrl_name):
  value = olx.GetValue(ctrl_name)
  if value == '?':
    colour = 'rgb(255,220,220)'
  else:
    colour = OV.FindValue('gui_html_input_bg_colour')
  return colour
OV.registerFunction(bgcolor)

def getStyles(fileName):
  cssPath = '%s/etc/CIF/styles/%s.css' %(OV.BaseDir(),fileName)
  if not os.path.exists(cssPath): return ''
  css = open(cssPath,'r').read()
  styleHTML = """
<style type="text/css">
<!--
%s
-->
</style>""" %css
  return styleHTML
OV.registerFunction(getStyles)


def getPopBoxPosition():
  ws = olx.GetWindowSize('html')
  ws = ws.split(",")
  WS = olx.GetWindowSize('main-cs', ws[0], int(ws[3]))
  WS = WS.split(",")
  sX = int(WS[0])
  sY = int(WS[1]) -2
  sTop = int(ws[1])
  return (sX, sY, sTop)

def get_template(name):
  template = r"%s/etc/gui/blocks/templates/%s.htm" %(olx.BaseDir(),name)
  if os.path.exists(template):
    rFile = open(template, 'r')
    str = rFile.read()
    return str
  else:
    return None

def makeHtmlBottomPop(args, pb_height = 50, y = 0, panel_diff = 22):
  txt = args.get('txt',None)
  name = args.get('name',"test")
  replace_str = args.get('replace',None)
  
  import OlexVFS
  from ImageTools import ImageTools
  IM = ImageTools()
  metric = getPopBoxPosition()
  if not txt:
    txt = get_template(name)
    txt = txt.replace(r"<MODENAME>",replace_str.upper())
  pop_html = name
  pop_name = name
  htm_location = "%s.htm" %pop_html
  OlexVFS.write_to_olex(htm_location,txt)
  width = int(IM.gui_htmlpanelwidth) - panel_diff
  x = metric[0] + 10
  if not y:
    y = metric[1] - pb_height - 8
  pstr = "popup %s '%s' -t='%s' -w=%s -h=%s -x=%s  -y=%s" %(pop_name, htm_location, pop_name, width, pb_height, x, y)
  OV.cmd(pstr)
  olx.html_SetBorders(pop_name,0)
  OV.cmd(pstr)
  olx.html_SetBorders(pop_name,0)
  olx.html_Reload(pop_name)
OV.registerMacro(makeHtmlBottomPop, 'txt-Text to display&;name-Name of the Bottom html popupbox')
  
def OnModeChange(*args):
  global active_mode
  global last_mode
  debug = OV.FindValue("olex2_debug",False)
  d = {
    'move sel':'button-move_near',
    'move sel -c=':'button-copy_near',    
    'grow':'button-grow_mode',
    'split -r=EADP':'button_full-move_atoms_or_model_disorder',
    'name':'button_small-naming',
    'off':None
  }
  name = 'mode'
  mode = ""
  i = 0
  mode_disp = ""
  args = args[0].split()
  for item in args:
    i += 1
    mode = mode + " " + item
    if i < 2:
      mode_disp += " " + item
  mode = mode.strip()
  mode_disp = mode_disp.strip()
  
  active_mode = d.get(mode, None)
#  if active_mode == last_mode:
#    active_mode = None

  # Deal with button images
  if not active_mode: 
    if not last_mode: return
    use_image = "%soff.png" %last_mode
    OV.SetImage("IMG_%s" %last_mode.upper(),use_image)
    copy_to = "%s.png" %last_mode
    OV.CopyVFSFile(use_image, copy_to,2)
    OV.cmd("html.hide pop_%s" %name)
  else:
    if last_mode:
      use_image = "%soff.png" %last_mode
      OV.SetImage("IMG_%s" %last_mode.upper(),use_image)
      copy_to = "%s.png" %last_mode
      OV.CopyVFSFile(use_image, copy_to,2)
      OV.cmd("html.hide pop_%s" %name)
      if active_mode == last_mode:
        last_mode = None
        active_mode = None
    if active_mode:
      use_image= "%son.png" %active_mode
      OV.SetImage("IMG_%s" %active_mode.upper(),use_image)
      copy_to = "%s.png" %active_mode
      OV.CopyVFSFile(use_image, copy_to,2)
      makeHtmlBottomPop({'replace':mode_disp, 'name':'pop_mode'}, pb_height=50)
      last_mode = active_mode
OV.registerCallback('modechange',OnModeChange)


def SetStateImage(name):
  d = {
    'basisvis':'button-show_basis',
    'cellvis':'button-show_cell',    
  }
  img_base = d.get(name, None)

  if not img_base:
    return False
  
  state = olx.CheckState(name)
  if state == "true":
    use_image= "%son.png" %img_base
    OV.SetImage("IMG_%s" %img_base.upper(),use_image)
    copy_to = "%s.png" %img_base
    OV.CopyVFSFile(use_image, copy_to,2)
  if state == "false":
    use_image = "%soff.png" %img_base
    OV.SetImage("IMG_%s" %img_base.upper(),use_image)
    copy_to = "%s.png" %img_base
    OV.CopyVFSFile(use_image, copy_to,2)
  return True
OV.registerFunction(SetStateImage)
    


def InActionButton(name,state):
  
  if state == "on":
    use_image= "%son.png" %name
    OV.SetImage("IMG_%s" %name.upper(),use_image)
    
  if state == "off":
    use_image= "%soff.png" %name
    OV.SetImage("IMG_%s" %name.upper(),use_image)
  return True

OV.registerFunction(InActionButton)
  
  
def PopProgram(txt="Fred"):
  name = "pop_prg_analysis"
  makeHtmlBottomPop({'txt':txt, 'name':name}, pb_height=225)
  
def PopBanner(txt='<zimg src="banner.png">'):
  name = "pop_banner"
  makeHtmlBottomPop({'txt':txt, 'name':name}, pb_height=65, y = 130,panel_diff=22)
OV.registerFunction(PopBanner)
  
  
def doBanner(i):
  i = int(i)
  #olx.html_SetImage("BANNER_IMAGE","banner_%i.png" %i)
  OV.CopyVFSFile("banner_%i.png" %i, "banner.png")
  OV.CopyVFSFile("banner_%i.htm" %i, "banner.htm")
  offset = 10
  target = 2
  ist = ""
  cmds = []
  ist += "aio-* 0 "
  
  d = olx.banner_slide.get(i,0)
  if not d:
    i = i + 1
    d = olx.banner_slide.get(i,0)
  if not d:
    i = i -2
    d = olx.banner_slide.get(i,0)
  if not d:
#    print i, "Nothing"
    return

#  print i, d.get('name')
  OV.SetVar('snum_refinement_banner_slide', i)
  
  ist += d.get('itemstate',0)
  cmds += d.get('cmd',"").split(">>")
  
  OV.setItemstate(ist)

  for cmd in cmds:
    OV.cmd(cmd)
  
OV.registerFunction(doBanner)



