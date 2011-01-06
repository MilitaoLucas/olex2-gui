#-*- coding:utf8 -*-

"""
Various generic tools for creating and using HTML.
"""
import os
import sys
import olx
import olex

import time
#import sys
#sys.path.append(r".\src")

from olexFunctions import OlexFunctions
OV = OlexFunctions()

active_mode = None
last_mode = None
current_tooltip_number = 0
HaveModeBox = False

global formula
global formula_string
formula = ""
formula_string = ""


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
        box_d.setdefault('ctrl_name', "SET_%s" %str.upper(box_d['varName']).replace('.','_'))
        box_d.setdefault('bgcolor','spy.bgcolor(%s)' %box_d['ctrl_name'])
        if box_d['varName'].startswith('_'): # treat cif items differently
          box_d.setdefault('value', '$spy.get_cif_item(%(varName)s,?)' %box_d)
          box_d.setdefault('onchange',"spy.set_cif_item(%(varName)s,GetValue(%(ctrl_name)s))>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %box_d)
          box_d.setdefault('onleave',"spy.set_cif_item(%(varName)s,GetValue(%(ctrl_name)s))>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %box_d)
        else:
          box_d.setdefault('value', '$spy.GetParam(%(varName)s)' %box_d)
          box_d.setdefault('onchange',"spy.SetParam(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %box_d)
          box_d.setdefault('onleave',"spy.SetParam(%(varName)s,GetValue(%(ctrl_name)s))>>spy.AddVariableToUserInputList(%(varName)s)>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %box_d)
        boxText += makeHtmlInputBox(box_d)
    if boxText:
      row_d.setdefault('input',boxText)
    else:
      input_d.setdefault('ctrl_name', "SET_%s" %str.upper(input_d['varName']).replace('.','_'))
      if input_d.has_key('onchange'):
        input_d.setdefault('onleave',input_d['onchange'])
      elif input_d.has_key('onleave'):
        input_d.setdefault('onchange',input_d['onleave'])
      if input_d['varName'].startswith('_'): # treat cif items differently
        input_d.setdefault('value', '$spy.get_cif_item(%(varName)s,?)' %input_d)
        input_d.setdefault('onchange',"spy.set_cif_item(%(varName)s,GetValue(%(ctrl_name)s))>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %input_d)
        input_d.setdefault('onleave',"spy.set_cif_item(%(varName)s,GetValue(%(ctrl_name)s))>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)" %input_d)
      else:
        input_d.setdefault('value', '$spy.GetParam(%(varName)s)' %input_d)
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
  dictionary.setdefault('fieldWidth','30%%')
  dictionary.setdefault('fieldVALIGN','center')
  dictionary.setdefault('fieldALIGN','left')

  if 'chooseFile' in dictionary.keys():
    chooseFile_dict = dictionary['chooseFile']
    if 'file_type' in chooseFile_dict.keys():
      href = "spy.set_source_file(%(file_type)s,FileOpen('%(caption)s','%(filter)s','%(folder)s'))>>updatehtml" %chooseFile_dict
    else:
      href = "%(function)sFileOpen('%(caption)s','%(filter)s','%(folder)s'))>>updatehtml" %chooseFile_dict
      pass
    chooseFileText = '''
    <td>
      <a href="%s">
        <zimg border="0" src="toolbar-open.png">
      </a>
    </td>
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
                  <b>
                    %(itemName)s
                  </b>
                </td>
                """ %field_d
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
  </tr>
''' %dictionary

  else:
    htmlTableRowText = '''
  <tr VALIGN="%(trVALIGN)s" ALIGN="%(trALIGN)s" NAME="%(ctrl_name)s">
    <td VALIGN="%(fieldVALIGN)s" ALIGN="%(fieldALIGN)s" width="%(fieldWidth)s" colspan=2>
      <b>
        %(itemName)s
      </b>
    </td>
      <td VALIGN="center" colspan=2>
        <font %(font)s>
          %(input)s
        </font>
    </td>
    %(chooseFile)s
  </tr>
''' %dictionary

  return htmlTableRowText

def make_edit_link(name, box_type):
  editLink = ""
  if OV.IsPluginInstalled('Olex2Portal'):
    if OV.GetParam('olex2.is_logged_on'):
      editLink = '''
      <tr>
      <td align='right'>
      <a href='spy.EditHelpItem(%s-%s)'>
        <b>
          &#187;
        </b>
        Edit
      </a>
      </td>
      </tr>
      ''' %(name, box_type)
  return editLink


def make_gui_edit_link(name):
  editLink = ""
  name = name.replace("\\", "/")
  if OV.IsPluginInstalled('Olex2Portal') and OV.GetParam('olex2.is_logged_on'):
    if "index" in name:
      editLink ='''
      <hr>
      <a href='spy.EditGuiItem(%s)'>
        Edit INDEX File
      </a>
      ''' %(name)
    else:
      editLink = '''
      <a href='spy.EditGuiItem(%s)'>
        Edit
      </a>
      ''' %(name)

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
#  titleTxt = title
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
  <a href="spy.make_help_box -name='%s' -popout=True>>htmlhome">
    <zimg border='0' src='popout.png'>
  </a>
  <a href=htmlhome><zimg border='0' src='return.png'>
  </a>
''' %name

  else:
    str = ""
    return_items = ""

  str += r'''
%s
<!-- #include tool-top gui/blocks/help-top.htm;image=blank;1; -->
<tr VALIGN='center' NAME=%s bgcolor="$spy.GetParam(gui.html.table_firstcol_colour)">
  <td colspan=1 width="2" bgcolor="$spy.GetParam(gui.html.table_firstcol_colour)">
  </td>
  <td>
    <font size='+2'>
      <b>
        %s
      </b>
    </font>
  </td>
</tr>
<tr>
  <td valign='top' width="2" bgcolor="$spy.GetParam(gui.html.table_firstcol_colour)">
  </td>
  <td>
    <font size='+1'>
      %s
    </font>
  </td>
</tr>
<tr>
  <td colspan=1 width="2" bgcolor="$spy.GetParam(gui.html.table_firstcol_colour)">
  </td>
  <td align='right'>
    %s
  </td>
</tr>
</tr>
</table>
<table>
%s
</table>

</font>
''' %(banner_include, name, titleTxt, helpTxt, return_items, editLink)
  wFilePath = r"%s-%s.htm" %(name, box_type)
  #str = unicode(str)#
  str = str.replace(u'\xc5', 'angstrom')
  OV.write_to_olex(wFilePath, str)

  if box_type == 'help':
    boxWidth = OV.GetParam('gui.help_box.width')
    length = len(helpTxt)
    boxHeight = int(length/(boxWidth/OV.GetParam('gui.help_box.height_factor'))) + OV.GetParam('gui.help_box.height_constant')
    if boxHeight > OV.GetParam('gui.help_box.height_max'):
      boxHeight = OV.GetParam('gui.help_box.height_max')

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
       <tr>
         %s
         <td colspan="%s" bgcolor="$spy.GetParam(gui.html.highlight_colour)">
          <b>
            &nbsp;%s
          </b>
         </td>
       </tr>
       ''' %(first_col, colspan, txt)
  return html
OV.registerFunction(make_warning_html)

def make_table_first_col(help_name=None, popout=False, help_image='large'):
  if help_name is None:
    help = ""
  else:
    help = make_help_href(help_name, popout, image=help_image)
  html ='''
<td valign='top' width='2' align='center' bgcolor='$spy.GetParam(gui.html.table_firstcol_colour)'>
  %s
</td>
''' %help
  return html

def make_help_href(name, popout, image='normal'):
  help = '''
  $spy.MakeHoverButton(btn-info@%s,spy.make_help_box -name='%s' -popout='%s')
  ''' %(name, name, popout)
  
  return help

def make_input_text_box(d):
  name = d.get('ctrl_name')
  dic = {'height':'$spy.GetParam(gui.html.input_height)',
         'bgcolor':'$spy.GetParam(gui.html.input_bg_colour)',
         'value':'$spy.GetParam(%(varName)s)',
         'width':'45',
         'onchange':'',
         'label':name,
         'onleave':'',
         'data':'',
         'manage':'',
     }
  dic.update(d)

  html = '''
<input
       bgcolor="$spy.GetParam(gui.html.input_bg_colour)"
       type="text"
       name="%(ctrl_name)s"
       value="%(value)s"
       width="%(width)s"
       height="%(height)s"
       label="%(label)s"
       onchange="%(onchange)s"
       onleave="%(onleave)s"
       %(manage)s
       data="%(data)s"
>''' %dic
  return html


def make_combo_text_box(d):
  name = d.get('ctrl_name')
  dic = {'height':"$spy.GetParam(gui.html.combo_height)",
         'bgcolor':'$spy.GetParam(gui.html.input_bg_colour)',
         'value':'$spy.GetParam(%(varName)s)',
         'label':'',
         'valign':'center',
         'halign':'left',
         'width':'70',
         'onchange':'',
         'onleave':'',
         'data':'',
         'manage':'manage',
         'readonly':'',
     }
  dic.update(d)

  html = '''
<input
       bgcolor="$spy.GetParam(gui.html.input_bg_colour)"
       type="combo"
       name="%(ctrl_name)s"
       value="%(value)s"
       halign="%(halign)s"
       valign="%(valign)s"
       items="%(items)s"
       width="%(width)s"
       height="%(height)s"
       label="%(label)s"
       onleave="%(onleave)s"
       onchange="%(onchange)s"
       %(manage)s
       data="%(data)s"
       readonly="%(readonly)s"
>''' %dic
  return html



def make_tick_box_input(d):
  name = d.get('ctrl_name')
  dic = {'height':'$spy.GetParam(gui.html.checkbox_height)',
         'bgcolor':'$spy.GetParam(gui.html.table_bg_colour)',
         'fgcolor':'$spy.GetParam(gui.html.font_colour)',
         'value':'$spy.GetParam(%(varName)s)',
         'width':'$spy.GetParam(gui.html.checkbox_height)',
         'onchange':'',
         'value':'%s '%name,
         'oncheck':'',
         'onuncheck':'',
         'data':'',
         'manage':'',
         'state':'',
     }
  dic.update(d)
  if dic.has_key('checked'):
    dic['checked'] = "checked='%s'" %dic.get('checked')
  else:
    dic.setdefault('checked','')


  html = """
<input
  type="checkbox"
  width="%(width)s"
  height="%(height)s"
  name="%(ctrl_name)s"
  bgcolor="%(bgcolor)s"
  fgcolor="%(fgcolor)s"
  %(state)s
  %(checked)s
  oncheck="%(oncheck)s"
  onuncheck="%(onuncheck)s"
  value="%(value)s"
  %(manage)s
  data="%(data)s"
  >
""" %dic
  return html

def make_spin_input(d):
  name = d.get('ctrl_name')
  dic = {'width':'12',
         'height':'$spy.GetParam(gui.html.spin_height)',
         'bgcolor':'$spy.GetParam(gui.html.input_bg_colour)',
         'value':'$spy.GetParam(%(varName)s)',
         'max':'99',
         'min':'0',
         'width':'45',
         'onchange':'',
         'label':"%s: " %name,
         'valign':'center',
         'halign':'left',
         'manage':'manage',
     }
  dic.update(d)
  html = """
<input
  label="%(label)s"
  valign="%(valign)s"
  halign="%(halign)s"
  type="spin"
  name="%(ctrl_name)s"
  width="%(width)s"
  height="%(height)s"
  max="%(max)s"
  min="%(min)s"
  bgcolor="%(bgcolor)s"
  value="%(value)s"
  onchange="%(onchange)s"
  manage="%(manage)s"
  >""" %dic
  return html

def make_input_button(d):
  dic = {'ondown':'',
         'onup':'',
         'onclick':'',
         'hint':'',
         'height':"$spy.GetParam(gui.html.button_height)",
         'bgcolor':"$spy.GetParam(gui.html.input_bg_colour)",
         'valign':'center',
         'halign':'left'
         }
  dic.update(d)
  html = '''
<input
  bgcolor="%(bgcolor)s"
  type="button"
  name="%(name)s_BUTTON"
  value="%(value)s"
  width="%(width)s"
  height="%(height)s"
  valign="%(valign)s"
  halign="%(halign)s"
  hint="%(hint)s"
  flat
''' %dic
  if dic['onclick']:
    html += '''
  onclick="%(onclick)s"
>
''' %dic
  elif dic['ondown'] or dic['onup']:
    html += '''
  ondown="%(ondown)s"
  onup="%(onup)s"
  >
''' %dic
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
#      string = regex.sub(r"\g<left><font color='$spy.GetParam(gui.html.highlight_colour)'><b>\g<txt></b></font>\g<right>", string)
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
  string = regex.sub(r"<font color='$spy.GetParam(gui.html.highlight_colour)'><b>\1</b></font>&nbsp;", string)

  ## find all occurances of strings between <<..>>. These are keys to pressthe headers for tip of the day.
  regex = re.compile(r"<< (.*?)  >>", re.X)
  string = regex.sub(r"<b><code>\1</code></b>", string)

  ## find all occurances of strings between n^..^n. These are the notes.
  regex = re.compile(r"n \^ (.*?)  \^ n", re.X)
  string = regex.sub(r"<table width='%s' border='0' cellpadding='0' cellspacing='1'><tr bgcolor=#efefef><td><font size=-1><b>Note: </b>\1</font></td></tr></table>", string)

  ## find all occurances of strings between l[]. These are links to help or tutorial popup boxes.
  regex = re.compile(r"l\[\s*(?P<linktext>.*?)\s*,\s*(?P<linkurl>.*?)\s*\,\s*(?P<linktype>.*?)\s*\]", re.X)
  string = regex.sub(r"<font size=+1 color='$spy.GetParam(gui.html.highlight_colour)'>&#187;</font><a target='Go to \g<linktext>' href='spy.make_help_box -name=\g<linkurl> -type=\g<linktype>'><b>\g<linktext></b></a>", string)

  ## find all occurances of strings between gui[]. These are links make something happen on the GUI.
  regex = re.compile(r"gui\[\s*(?P<linktext>.*?)\s*,\s*(?P<linkurl>.*?)\s*\,\s*(?P<linktype>.*?)\s*\]", re.X)
  string = regex.sub(r"<font size=+1 color='$spy.GetParam(gui.html.highlight_colour)'>&#187;</font><a target='Show Me' href='\g<linkurl>'><b>\g<linktext></b></a>", string)


  ## find all occurances of strings between XX. These are command line entities.
  width = int(OV.GetHtmlPanelwidth()) - 10
  regex = re.compile(r"  XX (.*?)( [^\XX\XX]* ) XX ", re.X)
  m = regex.findall(string)
  code_bg_colour = OV.GetParam('gui.html.code.bg_colour').hexadecimal
  code_fg_colour = OV.GetParam('gui.html.code.fg_colour').hexadecimal
  html_tag = OV.GetParam('gui.html.code.html_tag')
  if m:
    s = regex.sub(r"<table width='%s' border='0' cellpadding='0' cellspacing='1'><tr bgcolor='%s'><td><a href='\2'><b><font size='2' color='%s'><%s>>>\2</%s></font></a></td></tr></table>" %(width,code_bg_colour, code_fg_colour, html_tag, html_tag), string)

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
    s = regex.sub(r"<tr bgcolor='$spy.GetParam(gui.html.table_firstcol_colour)'><td><b>\2</b></td></tr><tr><td>", string)
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

def reg_command(self, string):
  regex = re.compile(r"  ~ (.*?)( [^\~\~]* ) ~ ", re.X)
  m = regex.findall(string)
  colour = OV.FindValue('gui_html_highlight_colour')
  if m:
    s = regex.sub(r'''
    <br>
    <br>
    <b>
    <font color=%s>
      \2
    </font>
    </b>
    <br>
    ''' %colour, string)
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
</style>
""" %css
  return styleHTML
OV.registerFunction(getStyles)

def getPrintStyles(fileName):
  cssPath = '%s/etc/CIF/styles/%s.css' %(OV.BaseDir(),fileName)
  if not os.path.exists(cssPath): return ''
  css = open(cssPath,'r').read()
  styleHTML = """
<style type="text/css" media="print">
<!--
%s
-->
</style>
""" %css
  return styleHTML
OV.registerFunction(getPrintStyles)

def getStylesList():
  styles = os.listdir("%s/etc/CIF/styles" %OV.BaseDir())
  exclude = ("rsc.css", "thesis.css", "custom.css")
  stylesList = ";".join(style[:-4] for style in styles
                        if style not in exclude and style.endswith('.css'))
  return 'default;' + stylesList
OV.registerFunction(getStylesList)

def getTemplatesList():
  templates = os.listdir("%s/etc/CIF/styles" %OV.BaseDir())
  exclude = ("footer.htm")
  templatesList = ";".join(template[:-4] for template in templates
                        if template not in exclude and template.endswith('.htm'))
  return templatesList
OV.registerFunction(getTemplatesList)



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

def makeHtmlBottomPop(args, pb_height = 50, y = 0):
  global HaveModeBox
  panel_diff = OV.GetParam('gui.htmlpanelwidth_margin_adjust')
  txt = args.get('txt',None)
  name = args.get('name',"test")
  replace_str = args.get('replace',None)
  modequalifiers = args.get('modequalifiers',None)

  import OlexVFS
  from ImageTools import ImageTools
  IM = ImageTools()
  metric = getPopBoxPosition()
  if not txt:
    txt = get_template(name)
    txt = txt.replace(r"<MODENAME>",replace_str.upper())
    txt = txt.replace(r"<MODEQUALIFIERS>",modequalifiers.upper())
  pop_html = name
  pop_name = name
  htm_location = "%s.htm" %pop_html
  OlexVFS.write_to_olex(htm_location,txt)
  width = OV.GetParam('gui.htmlpanelwidth') - panel_diff
  x = metric[0] + 10
  if not y:
    y = metric[1] - pb_height - 8
  pstr = "popup %s '%s' -t='%s' -w=%s -h=%s -x=%s  -y=%s" %(pop_name, htm_location, pop_name, width, pb_height, x, y)

  if HaveModeBox:
    OV.cmd(pstr)
  else:
    OV.cmd(pstr)
    olx.html_SetBorders(pop_name,0)
    OV.cmd(pstr)
    olx.html_SetBorders(pop_name,0)
    olx.html_Reload(pop_name)
    HaveModeBox = True

OV.registerMacro(makeHtmlBottomPop, 'txt-Text to display&;name-Name of the Bottom html popupbox')

def OnModeChange(*args):
  global active_mode
  global last_mode
  debug = OV.GetParam("olex2.debug")
  d = {
    'movesel':'button-move_near',
    'movesel -c=':'button-copy_near',
    'grow':'button-grow_mode',
    'split -r=EADP':'button_full-move_atoms_or_model_disorder',
    'split':'button_full-move_atoms_or_model_disorder',
    'name':'button_small-name',
    'fixu':'button-fix_u',
    'fixxyz':'button-fix_xyz',
    'hfix':'button_small-hfix',
    'occu':'button-set_occu',
    'off':None
  }


  name = 'mode'
  mode = ""
  i = 0
  mode_disp = ""
  args = args[0].split()
  modes_with_other_stuff_l = ["grow", "name"]
  modequalifiers = ""
  for item in args:
    for m in modes_with_other_stuff_l:
      if m in item:
        item = m
    i += 1
    mode = mode + " " + item
    if i < 2:
      mode_disp += " " + item
    if i >= 2:
      modequalifiers += item
  modequalifiers = modequalifiers.strip("=")
  mode = mode.strip()
  mode_disp = mode_disp.strip()
  mode_short = mode_disp

  if 'name -t=' in mode:
    element = mode.split('=')[1]
    if element:
      active_mode = 'btn-element%s' %element
    else:
      return

  elif 'name' in mode:
    active_mode = 'button_small-name'
  elif 'grow' in mode:
    active_mode = 'button-grow_mode'
  elif 'hfix' in mode:
    active_mode = 'button_small-hfix'
    mode_short = 'hfix'
  else:
    active_mode = d.get(mode, None)

#  mode_disp = "%s" %mode

  if last_mode == active_mode:
    mode = 'off'

  if not active_mode:
    active_mode = d.get(mode_disp, None)


  if mode == 'off':
    OV.SetParam('olex2.in_mode',None)
    OV.cmd("html.hide pop_%s" %name)
    if not last_mode: return
    control = "IMG_%s" %last_mode.upper()
    if OV.IsControl(control):
      OV.SetImage(control,"up=%soff.png" %last_mode)
      OV.SetImage(control,"hover=%shover.png" %last_mode)
    OV.cmd("html.hide pop_%s" %name)
    last_mode = None
    OV.SetParam('olex2.in_mode',None)
    OV.SetParam('olex2.short_mode',None)
    OV.SetParam('olex2.full_mode',None)
  else:
    OV.SetParam('olex2.in_mode',mode.split("=")[0])
    OV.SetParam('olex2.full_mode',mode)
    makeHtmlBottomPop({'replace':mode_disp, 'name':'pop_mode', 'modequalifiers':modequalifiers}, pb_height=50)
    if active_mode:
      control = "IMG_%s" %active_mode.upper()
      if OV.IsControl(control):
        OV.SetImage(control,"up=%son.png" %active_mode)
        OV.SetImage(control,"hover=%son.png" %active_mode)
    if last_mode:
      use_image = "%soff.png" %last_mode
      control = "IMG_%s" %last_mode.upper()
      if OV.IsControl(control):
        OV.SetImage(control,"up=%son.png" %active_mode)
        OV.SetImage(control,"hover=%son.png" %active_mode)

    last_mode = active_mode
    OV.SetParam('olex2.in_mode',mode.split("=")[0])
    OV.SetParam('olex2.short_mode',mode_short)
    last_mode = active_mode
  OV.Refresh()


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
  img_base = d.get(name)

  if not img_base:
    return False

  state = olx.CheckState(name)
  if state == "true":
    use_image= "up=%son.png" %img_base
    hover_image = "hover=%son.png" %img_base
  else:
    use_image = "up=%soff.png" %img_base
    hover_image = "hover=%shover.png" %img_base
  OV.SetImage("IMG_%s" %img_base.upper(),use_image)
  OV.SetImage("IMG_%s" %img_base.upper(),hover_image)
  OV.Refresh()
  return True

OV.registerCallback('statechange',OnStateChange)

def _check_modes_and_states(name):
  ## Modes
  d = {
    'button-move_near':'movesel',
    'button-copy_near':'movesel -c=',
    'button-grow_mode':'grow',
    'button_full-move_atoms_or_model_disorder':'split -r=EADP',
    'button_full-move_atoms_or_model_disorder':'split',
    'button_small-name':'name',
    'button-fix_u':'fixu',
    'button-fix_xyz':'fixxyz',
    'button-set_occu':'occu',
    'button_small-hfix':'hfix',
  }
  if name in d:
    if 'near' in name:
      mode = OV.GetParam('olex2.full_mode')
    else:
      mode = OV.GetParam('olex2.short_mode')
      if mode:
        if 'hfix' in mode: mode = "hfix"
    if mode == d.get(name):
      return True
  ##States
  d = {
    'button-show_basis':'basisvis',
    'button-show_cell':'cellvis',
    'button-tooltips':'htmlttvis',
    'button-help':'helpvis',
  }
  if name in d:
    state = olx.CheckState(d.get(name))
    if state == 'true':
      return True

  ## Hand-crafted buttons
  if name == 'button_full-move_atoms_or_model_disorder':
    if OV.GetParam('olex2.in_mode') == 'split -r':
      return True
  buttons = ['button_full-electron_density_map', 'button_small-map']
  if name in buttons:
    if OV.GetParam('olex2.eden_vis') == True:
      return True
  buttons = ['button_small-void']
  if name in buttons:
    if OV.GetParam('olex2.void_vis') == True:
      return True
  buttons = ['button_small-mask']
  if name in buttons:
    if OV.GetParam('olex2.mask_vis') == True:
      return True
  return False


def MakeHoverButton(name, cmds, onoff = "off", btn_bg='table_firstcol_colour'):
  hover_buttons = OV.GetParam('olex2.hover_buttons')
  on = _check_modes_and_states(name)
      
  if on:
    txt = MakeHoverButtonOn(name, cmds, btn_bg)
  else:
    txt = MakeHoverButtonOff(name, cmds, btn_bg)
  return txt
  
OV.registerFunction(MakeHoverButton)

def MakeHoverButtonOff(name, cmds, btn_bg='table_firstcol_colour'):
  hover_buttons = OV.GetParam('olex2.hover_buttons')
  click_console_feedback = False
  n = name.split("-")
  d = {'bgcolor': OV.GetParam('gui.html.%s' %btn_bg)}
  target=n[1]
  if '@' in name:
    tool_img = name.split('@')[0]
  else:
    tool_img = name.lower()
  d.setdefault('tool_img', tool_img)
  d.setdefault('namelower', name.lower())
  d.setdefault('nameupper', name.upper())
  #d.setdefault('bt', n[0])
  #d.setdefault('bn', n[1])
  #d.setdefault('BT', n[0].upper())
  #d.setdefault('BN', n[1].upper())
  d.setdefault('cmds', cmds.replace("\(","("))
  d.setdefault('target', OV.TranslatePhrase("%s-target" %target))
  if click_console_feedback:
    d.setdefault('feedback',">>echo '%(target)s: OK'" %target)
  else:
    d.setdefault('feedback',"")
  on = "on"
  off = "off"
  hover = "hover"
  down = "off"
  
  if OV.GetParam('gui.image_highlight') == name:
    on = "highlight"
    off = "highlight"
  if not hover_buttons:
    on = "on"
    off = "off"
    hover = "off"
  d.setdefault('on', on)
  d.setdefault('off', off)
  d.setdefault('down', down)
  d.setdefault('hover', hover)
  txt = '''
<input
  name=IMG_%(nameupper)s
  type="button"
  image="up=%(tool_img)s%(off)s.png,down=%(tool_img)s%(down)s.png,hover=%(tool_img)s%(hover)s.png",disable=%(tool_img)sdisable.png"
  hint="%(target)s"
  onclick="%(cmds)s%(feedback)s"
  bgcolor=%(bgcolor)s
>
'''%d
  return txt
OV.registerFunction(MakeHoverButtonOff)


def MakeHoverButtonOn(name,cmds,btn_bg='table_firstcol_colour'):
  hover_buttons = OV.GetParam('olex2.hover_buttons')
  click_console_feedback = False
  n = name.split("-")
  d = {'bgcolor': OV.GetParam('gui.html.%s' %btn_bg)}
  target=n[1]
  if '@' in name:
    tool_img = name.split('@')[0]
  else:
    tool_img = name.lower()
  d.setdefault('tool_img', tool_img)
  d.setdefault('namelower', name.lower())
  d.setdefault('nameupper', name.upper())
  d.setdefault('cmds', cmds.replace("\(","("))
  d.setdefault('target', OV.TranslatePhrase("%s-target" %target))
  if click_console_feedback:
    d.setdefault('feedback',">>echo '%(target)s: OK'" %target)
  else:
    d.setdefault('feedback',"")
  on = "on"
  off = "off"
  hover = "hoveron"
  down = "on"
  
  if OV.GetParam('gui.image_highlight') == name:
    on = "highlight"
    off = "highlight"
  if not hover_buttons:
    on = "on"
    off = "off"
    hover = "on"
  d.setdefault('on', on)
  d.setdefault('off', off)
  d.setdefault('down', down)
  d.setdefault('hover', hover)
  
  txt = '''
<input
  name=IMG_%(nameupper)s
  type="button"
  image="up=%(tool_img)s%(on)s.png,down=%(tool_img)s%(down)s.png,hover=%(tool_img)s%(hover)s.png",disable=%(tool_img)sdisable.png"
  hint="%(target)s"
  onclick="%(cmds)s%(feedback)s"
  bgcolor=%(bgcolor)s
>
'''%d
  return txt
OV.registerFunction(MakeHoverButtonOn)


def MakeActiveGuiButton(name,cmds,toolname=""):
  n = name.split("-")
  d = {}
  if toolname:
    target=toolname.lower()
  else:
    target=n[1]
  d.setdefault('bt', n[0])
  d.setdefault('bn', n[1])
  d.setdefault('BT', n[0].upper())
  d.setdefault('BN', n[1].upper())
  d.setdefault('cmds', cmds.replace("\(","("))
  d.setdefault('target', OV.TranslatePhrase("%s-target" %target))
  d.setdefault('toolname', toolname)
  txt = '''
    <a href="spy.InActionButton(%(bt)s-%(bn)s,on,%(toolname)s)>>refresh>>%(cmds)s>>echo '%(target)s: OK'>>spy.InActionButton(%(bt)s-%(bn)s,off,%(toolname)s)" target="%(target)s">
      <zimg name=IMG_%(BT)s-%(BN)s%(toolname)s border="0" src="%(bt)s-%(bn)s.png">
    </a>
    '''%d
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
    txt += '''
  </td>
</tr>
%s''' %make_edit_link("tip", "%i" %i)

  elif number == "+1":
    i = current_tooltip_number + 1
    txt = OV.TranslatePhrase("tip-%i" %i)
    if "tip-" in txt:
      i = 1
      txt = OV.TranslatePhrase("tip-%i" %i)
    txt += '''
  </td>
</tr>
%s''' %make_edit_link("tip", "%i" %i)

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
      txt += '''
      <b>
        %i.
      </b>
      <a href='spy.GetTip(%i)>>html.Reload'>%s</a>
      <br>''' %(i, i,t)
    txt = txt.rstrip("<br>")
    i = 0
  else:
    i = int(number)
    txt = OV.TranslatePhrase("tip-%i" %i)
    txt += '''
  </td>
</tr>
%s''' %make_edit_link("tip", "%i" %i)
  current_tooltip_number = i

  txt, d = format_help(txt)
  if number == "list":
    txt = txt.replace("&nbsp;","")


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
  global formula
  global formula_string
  
  if olx.FileName() == "Periodic Table":
    return "Periodic Table"
  else:
    colour = ""
    txt_formula = olx.xf_GetFormula()
    if txt_formula == formula:
      return formula_string
    formula = txt_formula
    l = ['3333', '6667']
    for item in l:
      if item in txt_formula:
        colour = OV.GetParam('gui.red').hexadecimal
    if not colour:
      colour = OV.GetParam('gui.html.font_colour')
    html_formula = olx.xf_GetFormula('html',1)
    formula_string = "<font size='4' color=%s>%s</font>" %(colour, html_formula)
    return formula_string
OV.registerFunction(makeFormulaForsNumInfo)

def setDisplayQuality(q=None):
  OV.setDisplayQuality(q)
OV.registerFunction(setDisplayQuality)

def include_block(path):
  f = open('%s/etc/%s' %(OV.BaseDir(),path),'r')
  txt = f.read()
  f.close()
  return txt
