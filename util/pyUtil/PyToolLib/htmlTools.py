#-*- coding:utf8 -*-

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

global current_tooltip_number
current_tooltip_number = 0

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
    row_d.setdefault('ctrl_name', "SET_%s" %str.upper(input_d['varName']).replace('.','_'))
    
    boxText = ''
    for box in ['box1','box2','box3']:
      if box in input_d.keys():
        box_d = input_d[box]
        box_d.setdefault('value', '$spy.GetParam(%s)' %box_d['varName'])
        box_d.setdefault('ctrl_name', "SET_%s" %str.upper(box_d['varName']).replace('.','_'))
        box_d.setdefault('bgcolor','spy.bgcolor(%s)' %box_d['ctrl_name'])
        box_d.setdefault('onchange',"spy.SetParam(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %box_d)
        box_d.setdefault('onleave',"spy.SetParam(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %box_d)
        boxText += makeHtmlInputBox(box_d)
    if boxText:
      row_d.setdefault('input',boxText)
    else:
      input_d.setdefault('value', '$spy.GetParam(%s)' %input_d['varName'])
      input_d.setdefault('ctrl_name', "SET_%s" %str.upper(input_d['varName']).replace('.','_'))
      input_d.setdefault('onchange',"spy.SetParam(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %input_d)
      input_d.setdefault('onleave',"spy.SetParam(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %input_d)
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
      href = "spy.SetParam(%(var)s,FileOpen('%(caption)s','%(filter)s','%(folder)s'))>>updatehtml" %chooseFile_dict
    else:
      href = "%(function)sFileOpen('%(caption)s','%(filter)s','%(folder)s'))>>updatehtml" %chooseFile_dict
      pass
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

def make_edit_link(name, box_type):
  editLink = ""
  if OV.IsPluginInstalled('Olex2Portal'):
    if OV.GetParam('olex2.is_online'):
      editLink = "<a href='spy.EditHelpItem(%s-%s)'>Edit</a>" %(name, box_type)
  return editLink


def make_gui_edit_link(name):
  editLink = ""
  if OV.IsPluginInstalled('Olex2Portal'):
    editLink = "<a href='spy.EditGuiItem(%s)'>Edit</a>" %(name)
  return editLink
OV.registerFunction(make_gui_edit_link)


def make_help_box(args):
  d = {}
  name = args.get('name', None)
  name = getGenericSwitchName(name)
  popout = args.get('popout', False)
  box_type = args.get('type', 'help')
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
  if box_type == "tutorial":
    titleTxt = titleTxt.title()
    t = titleTxt.split("_")
    if len(t) > 1:
      titleTxt = "%s: %s" %(t[0], t[1])
    
  helpTxt = OV.TranslatePhrase("%s-%s" %(help_src, box_type))
  helpTxt = helpTxt.replace("\r", "")
  helpTxt, d = format_help(helpTxt)
  d.setdefault('next',name)
  d.setdefault('previous',name)
  
  editLink = make_edit_link(name, box_type)
  
  if box_type != "help":
    banner_include = "<zimg border='0' src='banner_%s.png' usemap='map_tutorial'>" %box_type
    banner_include += """
    
<map name="map_tutorial">
<!-- Button PREVIOUS -->
    <area shape="rect" usemap="#map_setup"
      coords="290,0,340,60" 
      href='spy.make_help_box -name=%(previous)s -type=tutorial' target='%%previous%%: %(previous)s'>

<!-- Button NEXT-->
    <area shape="rect" 
      coords="340,0,400,60" 
      href='spy.make_help_box -name=%(next)s -type=tutorial' target='%%next%%: %(next)s'>
</map>    
    """ %d
    
  else:
    banner_include = ""

  
  if not popout:
    str = r'''
<!-- #include help-%s gui\%s.htm;gui\blocks\tool-off.htm;image=%s;onclick=;1; -->
''' %(name, name, name)
    
    return_items = r'''
<a href="spy.make_help_box -name='%s' -popout=True>>htmlhome"><zimg border='0' src='popout.png'></a>
<a href=htmlhome><zimg border='0' src='return.png'></a>''' %name
    
  else:
    str = ""
    return_items = ""
    
  str += r'''
%s
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
</td></tr>
%s
<!-- #include tool-footer gui/blocks/tool-footer.htm;1; -->
''' %(banner_include, name, titleTxt, helpTxt, return_items, editLink)
  wFilePath = r"%s-%s.htm" %(name, box_type)
  #str = unicode(str)#
  str = str.replace(u'\xc5', 'angstrom')
  OV.write_to_olex(wFilePath, str)
  
  if box_type == 'help':
    boxWidth = 450
    length = len(helpTxt)
    #boxHeight = int(length/2.8)
    boxHeight = int(length/(boxWidth/120)) + 100
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
        
  else:
    ws = olx.GetWindowSize('gl')
    ws = ws.split(',')
    x = int(ws[0])
    y = int(ws[1]) + 50
    boxWidth = int(400)
    boxHeight = int(ws[3]) - 80
    
  if popout:
    if box_type == 'tutorial':
      pop_name = "Tutorial"
      name = "Tutorial"
    else:
      pop_name = "%s-%s"%(name, box_type)
    olx.Popup(pop_name, wFilePath, "-b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(name, boxWidth, boxHeight, x, y))
    olx.html_SetBorders(pop_name,5)
#    olx.Popup(pop_name, wFilePath, "-b=tc -t='%s' -w=%i -d='echo' -h=%i -x=%i -y=%i" %(name, boxWidth, boxHeight, x, y))
#    olx.html_SetBorders(pop_name,5)
  else:
    olx.html_Load(wFilePath) 
#  popup '%1-tbxh' 'basedir()/etc/gui/help/%1.htm' -b=tc -t='%1' -w=%3 -h=%2 -x=%4 -y=%5"> 
OV.registerMacro(make_help_box, 'name-Name of the Box&;popout-True/False&;type-Type of Box (help or tutorial)')


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

def make_help_href(make_help, image='normal'):
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
  value='$spy.GetParam(%(varName)s)'
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
  d = {}  # initialise a dictionary, which will be used to store metadata.
  
  ## find all occurances of strings between **..**. These should be comma separated things to highlight.
  regex = re.compile(r"\*\* (.*?)  \*\*", re.X)
  l = regex.findall(string)
  if l:
    l = l[0].split(",")
    string = regex.sub(r"", string)
  
    for item in l:
      regex = re.compile(r"((?P<left>\W) (?P<txt>%s) (?P<right>\W))" %item, re.X)
#      string = regex.sub(r"\g<left><font color='$getVar(gui_html_highlight_colour)'><b>\g<txt></b></font>\g<right>", string)
      string = regex.sub(r"\g<left><b>\g<txt></b>\g<right>", string)

  ## find all occurances of strings between {{..}}. This will be translated into a dictionary and returned with the string.
  regex = re.compile(r"\{\{ (.*?)  \}\}", re.X)
  dt = regex.findall(string)
  if dt:
    string = regex.sub(r"", string)
    dt = dt[0]
    dt = dt.replace(",", "','")
    dt = dt.replace(":", "':'")
    dt = "{'%s'}" %dt
    d = eval(dt)
      
      
  ## find all occurances of <lb> and replace this with a line-break in a table.
  regex = re.compile(r"<lb>", re.X)
  string = regex.sub(r"</td></tr><tr><td>", string)

  ## find all occurances of '->' and replace this with an arrow.
  regex = re.compile(r"->", re.X)
  string = regex.sub(r"<b>&rarr;</b>", string)
  
  ## find all occurances of strings between t^..^t. These are the headers for tip of the day.
  regex = re.compile(r"t \^ (.*?)  \^ t", re.X)
  string = regex.sub(r"<font color='$getVar(gui_html_highlight_colour)'><b>\1</b></font>&nbsp;", string)

  ## find all occurances of strings between <<..>>. These are keys to pressthe headers for tip of the day.
  regex = re.compile(r"<< (.*?)  >>", re.X)
  string = regex.sub(r"<b><code>\1</code></b>", string)
  
  ## find all occurances of strings between n^..^n. These are the notes.
  regex = re.compile(r"n \^ (.*?)  \^ n", re.X)
  string = regex.sub(r"<table width='%s' border='0' cellpadding='2' cellspacing='4'><tr bgcolor=#efefef><td><font size=-1><b>Note: </b>\1</font></td></tr></table>", string)
  
  ## find all occurances of strings between l[]. These are links to help or tutorial popup boxes.
  regex = re.compile(r"l\[\s*(?P<linktext>.*?)\s*,\s*(?P<linkurl>.*?)\s*\,\s*(?P<linktype>.*?)\s*\]", re.X)
  string = regex.sub(r"<font size=+1 color='$getVar(gui_html_highlight_colour)'>&#187;</font><a target='Go to \g<linktext>' href='spy.make_help_box -name=\g<linkurl> -type=\g<linktype>'><b>\g<linktext></b></a>", string)

  ## find all occurances of strings between gui[]. These are links make something happen on the GUI.
  regex = re.compile(r"gui\[\s*(?P<linktext>.*?)\s*,\s*(?P<linkurl>.*?)\s*\,\s*(?P<linktype>.*?)\s*\]", re.X)
  string = regex.sub(r"<font size=+1 color='$getVar(gui_html_highlight_colour)'>&#187;</font><a target='Show Me' href='\g<linkurl>'><b>\g<linktext></b></a>", string)
  
  
  ## find all occurances of strings between XX. These are command line entities.
  width = int(OV.GetHtmlPanelwidth()) - 10
  regex = re.compile(r"  XX (.*?)( [^\XX\XX]* ) XX ", re.X)
  m = regex.findall(string)
  colour = "#888888"
  if m:
    s = regex.sub(r"<table width='%s' border='0' cellpadding='0' cellspacing='4'><tr bgcolor='$getVar(gui_html_code_bg_colour)'><td><a href='\2'><b><font size='2' color='%s'><code>>>\2</code></font></b></a></td></tr></table>" %(width, colour), string)

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
    s = regex.sub(r"<table border='0'>\2</table>", string)
  else:
    s = string
    
  return s, d

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
  if olx.GetValue(ctrl_name) in ('?',''):
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
  if value in ('?',''):
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

def getStylesList():
  styles = os.listdir("%s/etc/CIF/styles" %OV.BaseDir())
  exclude = ("rsc.css", "thesis.css", "custom.css")
  stylesList = ";".join(style[:-4] for style in styles
                        if style not in exclude and style.endswith('.css'))
  return "default;" + stylesList
OV.registerFunction(getStylesList)


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
  debug = OV.GetParam("olex2.debug")
  d = {
    'move sel':'button-move_near',
    'move sel -c=':'button-copy_near',    
    'grow':'button-grow_mode',
    'split -r=EADP':'button_full-move_atoms_or_model_disorder',
    'split':'button_full-move_atoms_or_model_disorder',
    'name':'button_small-name',
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
  if not active_mode:
    active_mode = d.get(mode_disp, None)
    
  
  
  if mode == 'off':
    OV.SetParam('olex2.in_mode',False)
    OV.cmd("html.hide pop_%s" %name)
    if not last_mode: return
    use_image = "%soff.png" %last_mode
    OV.SetImage("IMG_%s" %last_mode.upper(),use_image)
    copy_to = "%s.png" %last_mode
    OV.CopyVFSFile(use_image, copy_to,2)
    OV.cmd("html.hide pop_%s" %name)
    last_mode = None
    OV.SetParam('olex2.in_mode',False)
    OV.SetParam('olex2.short_mode',False)
  else:
    OV.SetParam('olex2.in_mode',mode.split("=")[0])
    makeHtmlBottomPop({'replace':mode_disp, 'name':'pop_mode'}, pb_height=50)
    if active_mode:
      use_image= "%son.png" %active_mode
      OV.SetImage("IMG_%s" %active_mode.upper(),use_image)
      copy_to = "%s.png" %active_mode
      OV.CopyVFSFile(use_image, copy_to,1)
    if last_mode:
      use_image = "%soff.png" %last_mode
      OV.SetImage("IMG_%s" %last_mode.upper(),use_image)
      copy_to = "%s.png" %last_mode
      OV.CopyVFSFile(use_image, copy_to,2)
      
    last_mode = active_mode
    OV.SetParam('olex2.in_mode',mode.split("=")[0])
    OV.SetParam('olex2.short_mode',mode_disp)
    last_mode = active_mode
  
  
  
##  if active_mode == last_mode:
##    active_mode = None
  
  ## Deal with button images
  #if not active_mode: 
    #if not last_mode: return
    #use_image = "%soff.png" %last_mode
    #OV.SetImage("IMG_%s" %last_mode.upper(),use_image)
    #copy_to = "%s.png" %last_mode
    #OV.CopyVFSFile(use_image, copy_to,2)
    #OV.cmd("html.hide pop_%s" %name)
    #last_mode = None
  #else:
    #if last_mode:
      #use_image = "%soff.png" %last_mode
      #OV.SetImage("IMG_%s" %last_mode.upper(),use_image)
      #copy_to = "%s.png" %last_mode
      #OV.CopyVFSFile(use_image, copy_to,2)
      #if active_mode == last_mode:
        #last_mode = None
        #active_mode = None
        #OV.SetVar('olex2_in_mode','False')
        #OV.cmd("html.hide pop_%s" %name)

    #if active_mode:
      #use_image= "%son.png" %active_mode
      #OV.SetImage("IMG_%s" %active_mode.upper(),use_image)
      #copy_to = "%s.png" %active_mode
      #OV.CopyVFSFile(use_image, copy_to,1)
      #last_mode = active_mode
      #OV.SetVar('olex2_in_mode',mode.split("=")[0])
    
OV.registerCallback('modechange',OnModeChange)


def OnStateChange(*args):
  name = args[0]
  state = args[1]
  d = {
    'basisvis':'button-show_basis',
    'cellvis':'button-show_cell',    
    'htmlttvis':'button-tooltips',    
    'helpvis':'button-help',
    
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
  
OV.registerCallback('statechange',OnStateChange)


def MakeActiveGuiButton(name,cmds,toolname=""):
  n = name.split("-")
  d = {}
  d.setdefault('bt', n[0])
  d.setdefault('bn', n[1])
  d.setdefault('BT', n[0].upper())
  d.setdefault('BN', n[1].upper())
  d.setdefault('cmds', cmds.replace("\(","("))
  d.setdefault('target', OV.TranslatePhrase("%s-target" %n[1]))
  d.setdefault('toolname', toolname)
  txt = '''
<a href="spy.InActionButton(%(bt)s-%(bn)s,on,%(toolname)s)>>refresh>>%(cmds)s>>echo '%(target)s: OK'>>spy.InActionButton(%(bt)s-%(bn)s,off,%(toolname)s)" 
target="%(target)s">
<zimg name=IMG_%(BT)s-%(BN)s%(toolname)s border="0" src="%(bt)s-%(bn)s.png"> 
</a> '''%d
  return txt
OV.registerFunction(MakeActiveGuiButton)




def InActionButton(name,state,toolname=""):
  
  if state == "on":
    use_image= "%son.png" %name
    OV.SetImage("IMG_%s%s" %(name.upper().lstrip(".PNG"),toolname),use_image)
    
  if state == "off":
    use_image= "%soff.png" %name
    OV.SetImage("IMG_%s%s" %(name.upper().lstrip(".PNG"),toolname), use_image)
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
  OV.SetParam('snum.refinement.banner_slide', i)
  
  ist += d.get('itemstate',0)
  cmds += d.get('cmd',"").split(">>")
  
  OV.setItemstate(ist)

  for cmd in cmds:
    OV.cmd(cmd)
  
OV.registerFunction(doBanner)


def getTip(number=0): ##if number = 0: get random tip, if number = "+1" get next tip, otherwise get the named tip
  from random import randint
  global current_tooltip_number
  max_i = 20
  if number == '0':
    txt = "tip-0"
    j = 0
    while "tip-" in txt:
      j += 1
      i = randint (1,max_i)
      if i == current_tooltip_number: continue
      txt = OV.TranslatePhrase("tip-%i" %i)
      if j > max_i * 2: break
    #txt += "</td></tr><tr><td align='right'>%s</td></tr>" %make_edit_link("tip", "%i" %i)
    txt += "</td></tr><b>&#187;</b>%s" %make_edit_link("tip", "%i" %i)

  elif number == "+1":
    i = current_tooltip_number + 1
    txt = OV.TranslatePhrase("tip-%i" %i)
    if "tip-" in txt:
      i = 1
      txt = OV.TranslatePhrase("tip-%i" %i)
    #txt += "</td></tr><tr><td align='right'>%s</td></tr>" %make_edit_link("tip", "%i" %i)
    txt += "</td></tr><b>&#187;</b>%s" %make_edit_link("tip", "%i" %i)
  elif number == "list":
    txt = ""
    for i in xrange(max_i):
      if i == 0: continue
      t = OV.TranslatePhrase("tip-%i" %i)
      if "tip-" in t:
        break
      t = t.split("^t")[0]
      t += "^t"
      t = t.strip()
      txt += "<b>%i.</b> <a href='spy.GetTip(%i)>>html.Reload'>%s</a><br>" %(i, i,t)
    txt = txt.rstrip("<br>")
  else:
    i = int(number)
    txt = OV.TranslatePhrase("tip-%i" %i)
    txt += "</td></tr><tr><td align='right'>%s</td></tr>" %make_edit_link("tip", "%i" %i)
  current_tooltip_number = i

#  txt = txt.encode('utf-8')
#  txt = unicode(txt, 'utf-8')
#  txt = unicode(txt, 'utf-8')
  
  #import array
  #txt = array.array.fromstring(txt).tostring()
  #txt = txt.encode('raw')
  
  txt, d = format_help(txt)
  
  OV.SetVar("current_tooltip_number",i)
  OV.write_to_olex("tip-of-the-day-content.htm", txt.encode('utf-8'))
  return True
OV.registerFunction(getTip)

##TO GO!
#def getNextTip():
  #global current_tooltip_number
  #next = current_tooltip_number + 1
  #txt = OV.TranslatePhrase("tip-%i" %i)
  #if "tip-" in txt:
    #i = 1
    #txt = OV.TranslatePhrase("tip-%i" %i)
    #txt += " | <font size=1>This is Tip %i</font>" %i
  #current_tooltip_number = i  
  #OV.write_to_olex("tip-of-the-day.htm", txt)
  #return True

def getGenericSwitchName(name):
  remove_l = ['work-', 'view-', 'info-', 'tools-', 'aio-', 'home-']
  str = ""
  name_full = name
  na = name.split("-")
  if len(na) > 1:
    for remove in remove_l:
      if name.startswith(remove):
        name = name.split(remove,1)[1]
        break
  return name
OV.registerFunction(getGenericSwitchName)

def getGenericSwitchNameTranslation(name):
  name = getGenericSwitchName(name)
  if name:
    text = OV.TranslatePhrase(getGenericSwitchName(name))
  else:
    text = "No text!"
  return text
OV.registerFunction(getGenericSwitchNameTranslation)

def makeFormulaForsNumInfo():
  if olx.FileName() == "Periodic Table":
    return "Periodic Table"
  else:
    return olx.xf_GetFormula('html',2)
OV.registerFunction(makeFormulaForsNumInfo)

def reset_file_in_OFS(fileName):
  OV.reset_file_in_OFS(fileName)
  return True
OV.registerFunction(reset_file_in_OFS)
