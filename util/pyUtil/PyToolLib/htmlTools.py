#-*- coding:utf8 -*-

"""
Various generic tools for creating and using HTML.
"""
import os
import sys
import olx
import olex
import olexex

import time
from datetime import date
#import sys
#sys.path.append(r".\src")

from olexFunctions import OlexFunctions
OV = OlexFunctions()

last_mode = None
last_mode_options = None
current_tooltip_number = 0
HaveModeBox = False

global formula
global formula_string
formula = ""
formula_string = ""

global tutorial_box_initialised
tutorial_box_initialised = False

global time_add
time_add = 0


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

    if input_d['varName'] == "InfoLine":
      pass


    boxText = ''
    for box in ['box1','box2','box3']:
      if box in input_d.keys():
        box_d = input_d[box]
        box_d.setdefault('ctrl_name', "SET_%s" %str.upper(box_d['varName']).replace('.','_'))
        box_d.setdefault('bgcolor',"spy.bgcolor('~name~')")
        if box_d['varName'].startswith('_'): # treat cif items differently
          box_d.setdefault('value', "spy.get_cif_item('%(varName)s','?','gui')" %box_d)
          box_d.setdefault('onchange',"spy.set_cif_item('%(varName)s',html.GetValue('~name~'))>>spy.changeBoxColour('%(ctrl_name)s','#FFDCDC')" %box_d)
        else:
          box_d.setdefault('value', "spy.GetParam('%(varName)s')" %box_d)
          box_d.setdefault('onchange',"spy.SetParam('%(varName)s',html.GetValue('~name~'))>>spy.AddVariableToUserInputList('%(varName)s')>>spy.changeBoxColour('~name~','#FFDCDC')" %box_d)
        boxText += makeHtmlInputBox(box_d)
    if boxText:
      row_d.setdefault('input',boxText)
    else:
      input_d.setdefault('ctrl_name', "SET_%s" %str.upper(input_d['varName']).replace('.','_'))
      if input_d['varName'].startswith('_'): # treat cif items differently
        input_d.setdefault('value', "spy.get_cif_item('%(varName)s','?','gui')" %input_d)
        input_d.setdefault('onchange',"spy.set_cif_item('%(varName)s',html.GetValue('~name~'))>>spy.changeBoxColour('~name~','#FFDCDC')" %input_d)
      elif input_d['varName'] == 'snum.report.date_collected': # treat date fields differently
        try:
          cd = float(OV.GetParam('snum.report.date_collected'))
          cd = date.fromtimestamp(cd)
          time_str = cd.strftime("%d-%m-%Y")
          input_d.setdefault('value', "'%s'" %time_str)
        except:
          input_d.setdefault('value', "'%s'" %OV.GetParam('snum.report.date_collected'))
        input_d.setdefault('onchange',"spy.SetParam('%(varName)s',html.GetValue('~name~'))>>spy.AddVariableToUserInputList('%(varName)s')>>spy.changeBoxColour('~name~','#FFDCDC')" %input_d)
      else:
        input_d.setdefault('value', "spy.GetParam('%(varName)s')" %input_d)
        input_d.setdefault('onchange',"spy.SetParam('%(varName)s',html.GetValue('~name~'))>>spy.AddVariableToUserInputList('%(varName)s')>>spy.changeBoxColour('~name~','#FFDCDC')" %input_d)
      input_d.setdefault('bgcolor',"spy.bgcolor('~name~')")
      row_d.setdefault('input',makeHtmlInputBox(input_d))
      row_d.update(input_d)

    text += makeHtmlTableRow(row_d)

  return OV.Translate(text)

def makeHtmlInputBox(inputDictionary):
  if inputDictionary.has_key('items'):
    inputDictionary.setdefault('type','combo')
    inputDictionary.setdefault('readonly','readonly')
  else:
    if inputDictionary.get('onchange', None) and not inputDictionary.get('onleave'):
      inputDictionary['onleave'] = inputDictionary['onchange']
      del inputDictionary['onchange']

  if inputDictionary.has_key('multiline'):
    inputDictionary.setdefault('height','35')

  dictionary = {
    'width':'95%%',
    'height':"$GetVar('HtmlInputHeight')",
    'onchange':'',
    'onleave':'',
    'items':'',
    'multiline':'',
    'type':'text',
    'readonly':'',
    'manage':'',
    'data':'',
    'label':'',
    'valign':'center',
    'bgcolor':'',
  }
  dictionary.update(inputDictionary)
  htmlInputBoxText = '''
<font size="$GetVar('HtmlFontSizeControls')">
<input
type="%(type)s"
%(multiline)s
width="%(width)s"
height="%(height)s"
name="%(ctrl_name)s"
value="%(value)s"
items="%(items)s"
label="%(label)s"
valign="%(valign)s"
onchange="%(onchange)s"
onleave="%(onleave)s"
%(readonly)s
bgcolor="%(bgcolor)s"
>
</font>
'''%dictionary

  return htmlInputBoxText

def makeHtmlTableRow(dictionary):
  dictionary.setdefault('font', "size='%s'" %olx.GetVar('HtmlGuiFontSize'))
  dictionary.setdefault('trVALIGN','center')
  dictionary.setdefault('trALIGN','left')
  dictionary.setdefault('fieldWidth','30%%')
  dictionary.setdefault('fieldVALIGN','center')
  dictionary.setdefault('fieldALIGN','left')
  dictionary.setdefault('first_col_width', OV.GetParam('gui.html.table_firstcol_width'))
  dictionary.setdefault('first_col_colour', OV.GetParam('gui.html.table_firstcol_colour'))
  #dictionary.setdefault('first_column', '<td width="%(first_col_width)s" bgcolor="%(first_col_colour)s"></td>' %dictionary)
  dictionary.setdefault('first_column', '')

  href_1 = ""
  href_2 = ""
  if 'chooseFile' in dictionary.keys():
    chooseFile_dict = dictionary['chooseFile']
    if 'file_type' in chooseFile_dict.keys():
      href = "spy.set_source_file(%(file_type)s,FileOpen('%(caption)s','%(filter)s','%(folder)s'))>>html.Update" %chooseFile_dict
    else:
      href = "%(function)sFileOpen('%(caption)s','%(filter)s','%(folder)s'))>>html.Update" %chooseFile_dict
      pass
    chooseFileText = '''
    <td>
      <a href="%s">
        <zimg border="0" src="toolbar-open.png">
      </a>
    </td>
    ''' %href
    href_1 = '<a href="%s">' %href
    href_2 = '</a>'
    dictionary['chooseFile'] = ""
    #dictionary.setdefault('chooseFile','')

  else:
    dictionary.setdefault('chooseFile','')
  dictionary['href_1'] = href_1
  dictionary['href_2'] = href_2

  FieldText = ''
  count=0
  for field in ['field1','field2']:
    if field in dictionary.keys():
      count += 1
      field_d = dictionary[field]
      field_d.setdefault('itemName', '')
      field_d.setdefault('fieldVALIGN','center')
      field_d.setdefault('fieldALIGN','left')
      if field == 'field1':
        field_d.setdefault('fieldWidth','30%%')
      else:
        field_d.setdefault('fieldWidth','70%%')
      field_d.setdefault('href_1',href_1)
      field_d.setdefault('href_2',href_2)

      field_d.setdefault('font','color=%s' %OV.GetParam('gui.html.table_firstcol_colour'))
      field_d.setdefault('first_col_width', OV.GetParam('gui.html.table_firstcol_width'))
      FieldText += """
                <td VALIGN="%(fieldVALIGN)s" ALIGN="%(fieldALIGN)s" width="%(fieldWidth)s">
                  <b>%(itemName)s</b>
                </td>
                """ %field_d
  if count == 2:
    FieldText = "<td><table cellpadding='0' cellspacing='0' width='100%%'><tr>%s</tr></table></td>" %FieldText

  if FieldText:
    dictionary.setdefault('fieldText',FieldText)

    htmlTableRowText = '''
  <tr NAME="%(ctrl_name)s">
    %(fieldText)s
    <td valign="center" align="right">%(input)s</td>
    %(chooseFile)s
  </tr>
''' %dictionary

  else:

    htmlTableRowText = '''
  <tr NAME="%(ctrl_name)s">
  %(first_column)s
    <td VALIGN="%(fieldVALIGN)s" ALIGN="%(fieldALIGN)s" width="%(fieldWidth)s">
      <b>
        %(href_1)s
          %(itemName)s
        %(href_2)s
      </b>
    </td>
    <td align="right" width="70%%%%">
      %(input)s
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
  global tutorial_box_initialised
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

  if "h3-" in name:
    t = name.split("h3-")
    help_src = name
    title = t[1].replace("-", " ")

  elif "-" in name:
    title = name.replace("-", " ").title()
    help_src = name
  else:
    title = name
    help_src = name
  titleTxt = OV.TranslatePhrase("%s" %title).title()
#  titleTxt = title
  if box_type == "tutorial":
    titleTxt = titleTxt.title()
    t = titleTxt.split("_")
    if len(t) > 1:
      titleTxt = "%s: %s" %(t[0], t[1])

  title = title.title()
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
    txt = ""
    return_items = ""

  txt = get_template('pop_help')

  txt = txt %(banner_include, name, titleTxt, helpTxt, return_items, editLink)
  wFilePath = r"%s-%s.htm" %(name, box_type)
  wFilePath = wFilePath.replace(" ", "_")
  #from ImageTools import ImageTools
  #IT = ImageTools()
  #txt = IT.get_unicode_characters(txt)
  OV.write_to_olex(wFilePath, txt)

  if box_type == 'help':
    boxWidth = OV.GetParam('gui.help_box.width')
    length = len(helpTxt)
    tr = helpTxt.count('<tr')

    boxHeight = int(length/(boxWidth/OV.GetParam('gui.help_box.height_factor'))) + int(OV.GetParam('gui.help_box.height_constant') * (tr+2))
    if boxHeight > OV.GetParam('gui.help_box.height_max'):
      boxHeight = OV.GetParam('gui.help_box.height_max')
    if boxHeight < 150:
      boxHeight = 150

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
    if box_type == 'tutorial' and tutorial_box_initialised:
      pass
    else:
      ws = olx.GetWindowSize('gl')
      ws = ws.split(',')
      x = int(ws[0])
      y = int(ws[1]) + 50
      boxWidth = int(400)
      boxHeight = int(ws[3]) - 120

  if popout:
    if box_type == 'tutorial':
      pop_name = "Tutorial"
      name = "Tutorial"
    else:
      pop_name = "%s-%s"%(name, box_type)
    if box_type == 'tutorial' and tutorial_box_initialised:
      olx.Popup(tutorial_box_initialised, wFilePath)
    else:
      pop_name = pop_name.replace(" ", "_")
      title = 'Olex2 Help'
      olx.Popup(pop_name, wFilePath, "-b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(title, boxWidth, boxHeight, x, y))
      olx.html.SetBorders(pop_name,5)
      if box_type == 'tutorial':
        tutorial_box_initialised = pop_name

  else:
    olx.html.Load(wFilePath)
#  popup '%1-tbxh' 'basedir()/etc/gui/help/%1.htm' -b=tc -t='%1' -w=%3 -h=%2 -x=%4 -y=%5">
OV.registerMacro(make_help_box, 'name-Name of the Box&;popout-True/False&;type-Type of Box (help or tutorial)')


def make_warning_html(colspan):
  txt = "htmltool-warning"
  txt = OV.TranslatePhrase(txt)
  first_col = make_table_first_col()
  html = '''
       <tr>
         %s
         <td colspan="%s" bgcolor="$GetVar('HtmlHighlightColour')">
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
<td valign='top' align='center' bgcolor="$GetVar('HtmlTableFirstcolColour')">
  %s
</td>
''' %help
  return html

def make_html_opening():
  html = '''
  <html>
  <body link=$GetVar(HtmlLinkColour) bgcolor="$GetVar('HtmlBgColour')">
  <font color="$GetVar('HtmlFontColour')" size="$GetVar('HtmlGuiFontSize')" face="$GetVar('HtmlFontName')">
<p> '''
  return html

def make_html_closing():
  html = '''
  </font></body></html>
  '''
  return html

def make_help_href(name, popout, image='normal'):
  help = '''
  $spy.MakeHoverButton("btn-info@%s","spy.make_help_box -name='%s' -popout='%s'")
  ''' %(name, name, popout)

  return help

def make_input_text_box(d):
  name = d.get('ctrl_name')
  dic = {'height':"$GetVar('HtmlInputHeight')",
         'bgcolor':"$GetVar('HtmlInputBgColour')",
         'value':"$spy.GetParam('%(varName)s')",
         'width':'45',
         'onchange':'',
         'onleave':'',
         'label':name,
         'valign':'center',
         'data':'',
         'manage':'',
     }
  dic.update(d)

  html = '''
<font size="$GetVar('HtmlFontSizeControls')">
<input
       bgcolor="$GetVar('HtmlInputBgColour')"
       type="text"
       name="%(ctrl_name)s"
       value="%(value)s"
       width="%(width)s"
       height="%(height)s"
       label="%(label)s"
       valign="%(valign)s"
       onchange="%(onchange)s"
       onleave="%(onleave)s"
       %(manage)s
       data="%(data)s"
>
</font>''' %dic
  return html


def make_combo_text_box(d):
  name = d.get('ctrl_name')
  dic = {'height':"$GetVar('HtmlComboHeight')",
         'bgcolor':"$GetVar('HtmlInputBgColour')",
         'value':"$spy.GetParam('%(varName)s')",
         'label':'',
         'valign':'center',
         'halign':'left',
         'width':'70',
         'onchange':'',
         'data':'',
         'manage':'manage',
         'readonly':'',
     }
  dic.update(d)

  if dic.has_key('readonly'):
    if dic['readonly']:
      dic['readonly'] = "readonly"
    else:
      dic['readonly'] = ""

    html = '''
<font size="$GetVar('HtmlFontSizeControls')">
<input
       bgcolor="$GetVar('HtmlInputBgColour')"
       type="combo"
       name="%(ctrl_name)s"
       value="%(value)s"
       halign="%(halign)s"
       valign="%(valign)s"
       items="%(items)s"
       width="%(width)s"
       height="%(height)s"
       label="%(label)s"
       onchange="%(onchange)s"
       %(manage)s
       data="%(data)s"
       %(readonly)s
>
</font>''' %dic
  return html



def make_tick_box_input(d):
  name = d.get('ctrl_name')
  dic = {'height':"$GetVar('HtmlCheckboxHeight')",
         'bgcolor':"$GetVar('HtmlTableBgColour')",
         'fgcolor':"$GetVar('HtmlFontColour')",
         'value':"$spy.GetParam('%(varName)s')",
         'width':"$GetVar('HtmlCheckboxWidth')",
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
<font size="$GetVar('HtmlFontSizeControls')">
<input
  type="checkbox"
  width="%(width)s"
  height="%(height)s"
  name="%(ctrl_name)s"
  value="%(value)s"
  bgcolor="%(bgcolor)s"
  fgcolor="%(fgcolor)s"
  %(state)s
  %(checked)s
  oncheck="%(oncheck)s"
  onuncheck="%(onuncheck)s"
  valign="center"
  %(manage)s
  data="%(data)s"
  >
  </font>
""" %dic
  return html

def make_spin_input(d):
  name = d.get('ctrl_name')
  dic = {'width':'12',
         'height':"$GetVar('HtmlSpinHeight')",
         'bgcolor':"$GetVar('HtmlInputBgColour')",
         'value':"$spy.GetParam('%(varName)s')",
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
<font size="$GetVar('HtmlFontSizeControls')">
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
  >
  </font>""" %dic
  return html

def make_input_button(d):
  dic = {'ondown':'',
         'onup':'',
         'onclick':'',
         'hint':'',
         'height':"$GetVar('HtmlButtonHeight')",
         'bgcolor':"$GetVar('HtmlInputBgColour')",
         'valign':'center',
         'halign':'left'
         }
  dic.update(d)
  html = '''
<font size="$GetVar('HtmlFontSizeControls')">
<input
  bgcolor="%(bgcolor)s"
  type="button"
  name="%(name)s_BUTTON"
  value="%(value)s"
  width="%(width)s"
  height="%(height)s"
  hint="%(hint)s"
  flat
''' %dic
  if dic['onclick']:
    html += '''
  onclick="%(onclick)s"
>
</font>
''' %dic
  elif dic['ondown'] or dic['onup']:
    html += '''
  ondown="%(ondown)s"
  onup="%(onup)s"
  >
  </font>
''' %dic
  else:
    html += '\n></font>\n'
  return html

def format_help(string):
  import re
  d = {}  # initialise a dictionary, which will be used to store metadata.

  ## find all occurences of strings between **..**. These should be comma separated things to highlight.
  regex = re.compile(r"\*\* (.*?)  \*\*", re.X)
  l = regex.findall(string)
  if l:
    l = l[0].split(",")
    string = regex.sub(r"", string)

    for item in l:
      regex = re.compile(r"((?P<left>\W) (?P<txt>%s) (?P<right>\W))" %item, re.X)
#      string = regex.sub(r"\g<left><font color='$GetVar(HtmlHighlightColour)'><b>\g<txt></b></font>\g<right>", string)
      string = regex.sub(r"\g<left><b>\g<txt></b>\g<right>", string)

  ## find all occurences of strings between {{..}}. This will be translated into a dictionary and returned with the string.
  regex = re.compile(r"\{\{ (.*?)  \}\}", re.X)
  dt = regex.findall(string)
  if dt:
    string = regex.sub(r"", string)
    dt = dt[0]
    dt = dt.replace(",", "','")
    dt = dt.replace(":", "':'")
    dt = "{'%s'}" %dt
    d = eval(dt)


  ## find all occurences of <lb> and replace this with a line-break in a table.
  regex = re.compile(r"<lb>", re.X)
  string = regex.sub(r"</td></tr><tr><td>", string)

  ## find all occurences of '->' and replace this with an arrow.
  regex = re.compile(r"->", re.X)
  string = regex.sub(r"<b>&rarr;</b>", string)

  ## find all occurences of strings between t^..^t. These are the headers for tip of the day.
  regex = re.compile(r"t \^ (.*?)  \^ t", re.X)
  string = regex.sub(r"<font color='$GetVar(HtmlHighlightColour)'><b>\1</b></font>&nbsp;", string)

  ## find all occurences of strings between <<..>>. These are keys to pressthe headers for tip of the day.
  regex = re.compile(r"<< (.*?)  >>", re.X)
  string = regex.sub(r"<b><code>\1</code></b>", string)

  ## find all occurences of strings between n^..^n. These are the notes.
  regex = re.compile(r"n \^ (.*?)  \^ n", re.X)
  string = regex.sub(r"<table width='%s' border='0' cellpadding='0' cellspacing='1'><tr bgcolor=#efefef><td><font size=-1><b>Note: </b>\1</font></td></tr></table>", string)

  ### find all occurences of strings between TT..TT. These are keys to pressthe headers for tip of the day.
  #regex = re.compile(r"TT (.*?)  TT", re.X)
  #string = regex.sub(r"<tr><td align='right'><a href='spy.run_autodemo(\1)'><zimg src=tutorial.png></a></td></tr>", string)

  ## find all occurences of strings between TT..TT. These are keys to pressthe headers for tip of the day.
  regex = re.compile(r"TT (.*?)  TT", re.X)
  sx = string
  string = regex.sub(r"<tr><td align='right'>$spy.MakeHoverButton('button-tutorial','spy.demo.run_autodemo(1)')</td></tr>", string)
  string = string.replace(r"\\\\",r"\\")

  ## find all occurences of strings between l[]. These are links to help or tutorial popup boxes.
  regex = re.compile(r"l\[\s*(?P<linktext>.*?)\s*,\s*(?P<linkurl>.*?)\s*\,\s*(?P<linktype>.*?)\s*\]", re.X)
  string = regex.sub(r"<font size=+1 color=\"$GetVar('HtmlHighlightColour')\">&#187;</font><a target='Go to \g<linktext>' href='spy.make_help_box -name=\g<linkurl> -type=\g<linktype>'><b>\g<linktext></b></a>", string)

  ## find all occurences of strings between URL[]. These are links to help or tutorial popup boxes.
  regex = re.compile(r"URL\[\s*(?P<URL>.*?)]", re.X)
  string = regex.sub(r"<tr><td bgcolor='#205c90' align='right'><b><a href='shell \g<URL>'><font color='#ffffff'>More Info Online</font></a></b></td></tr>" , string)

  ## find all occurences of strings between gui[]. These are links make something happen on the GUI.
  regex = re.compile(r"gui\[\s*(?P<linktext>.*?)\s*,\s*(?P<linkurl>.*?)\s*\,\s*(?P<linktype>.*?)\s*\]", re.X)
  string = regex.sub(r"<font size=+1 color='$GetVar(HtmlHighlightColour)'>&#187;</font><a target='Show Me' href='\g<linkurl>'><b>\g<linktext></b></a>", string)


  ## find all occurences of strings between XX. These are command line entities.
  width = int(OV.GetHtmlPanelwidth()) - 10
  regex = re.compile(r"  XX (.*?)( [^\XX\XX]* ) XX ", re.X)
  m = regex.findall(string)
  code_bg_colour = OV.GetParam('gui.html.code.bg_colour').hexadecimal
  code_fg_colour = OV.GetParam('gui.html.code.fg_colour').hexadecimal
  html_tag = OV.GetParam('gui.html.code.html_tag')
  if m:
    #s = regex.sub(r"<table width='%s' border='0' cellpadding='0' cellspacing='1'><tr bgcolor='%s'><td><a href='\2'><b><font size='2' color='%s'><%s>>>\2</%s></font></a></td></tr></table>" %(width,code_bg_colour, code_fg_colour, html_tag, html_tag), string)

    s = regex.sub(r" <font color='%s'>[&nbsp;<a href='\2'><b><%s>\2</%s></a>&nbsp;]</font>" %( code_fg_colour, html_tag, html_tag), string)


  else:
    s = string
  string = s

  ## find all occurences of strings between ~. These are the entries for the table.
  regex = re.compile(r"  ~ (.*?)( [^\~\~]* ) ~ ", re.X)
  m = regex.findall(string)
  colour = OV.GetParam('gui.html.highlight_colour').hexadecimal
  if m:
    s = regex.sub(r"<tr><td><b><font color='%s'>\2</font></b> " %colour, string)
  else:
    s = string

  ## find all occurences of strings between@. These are the table headers.
  string = s
  regex = re.compile(r"  @ (.*?)( [^\@\@]* ) @ ", re.X)
  m = regex.findall(string)
  colour = "#232323"
  if m:
    s = regex.sub(r"<tr bgcolor=\"$GetVar('HtmlTableFirstcolColour')\"><td colspan='4'><b>\2</b></td></tr><tr><td>", string)
  else:
    s = string

  ## find all occurences of strings between &. These are the tables.
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
  colour = OV.GetParam('gui.html.highlight_colour')
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
  if olx.html.GetValue(ctrl_name) in ('?',''):
    olx.html.SetBG(ctrl_name,colour)
  else:
    olx.html.SetBG(ctrl_name,OV.FindValue('gui_html_input_bg_colour'))
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
  OV.UpdateHtml()
  return ""
OV.registerFunction(switchButton)



def bgcolor(ctrl_name):
  value = olx.html.GetValue(ctrl_name)
  if value in ('?',''):
    colour = "#FFDCDC"
  else:
    #colour = '#ff0000'
    colour = OV.GetParam('gui.html.input_bg_colour').hexadecimal
  return colour
OV.registerFunction(bgcolor)

def getStyles(style_name):
  if not style_name:
    style_name = OV.GetParam('user.report_style')
  if not os.path.exists(style_name):
    style_name = '%s/etc/CIF/%s' %(OV.BaseDir(),style_name)
  if not os.path.exists(style_name):
    style_name = '%s/etc/CIF/styles/default.css' %OV.BaseDir()

  css = open(style_name,'r').read()
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
  exclude = set(("rsc.css", "thesis.css", "custom.css"))
  stylesList = ";".join("styles/%s" %style for style in styles\
    if style.endswith('.css') and style not in exclude)
  return stylesList
OV.registerFunction(getStylesList)

def getTemplatesList():
  templates = os.listdir("%s/etc/CIF/templates" %OV.BaseDir())
  exclude = ("footer.htm")
  templatesList = ";".join("templates/%s.htm" %template[:-4] for template in templates
                        if template not in exclude and template.endswith('.htm') or template.endswith('.rtf'))
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
    rFile.close()
    return str
  else:
    return None

def makeHtmlBottomPop(args, pb_height = 50, y = 0):
  global HaveModeBox
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
  txt = "$run(focus)\n" + txt
  pop_html = name
  pop_name = name
  htm_location = "%s.htm" %pop_html
  OlexVFS.write_to_olex(htm_location,txt)
  width = int(olx.html.ClientWidth('self'))
  x = metric[0]
  if not y:
    y = metric[1] - pb_height
  pstr = "popup %s '%s' -t='%s' -w=%s -h=%s -x=%s  -y=%s" %(
    pop_name, htm_location, pop_name, width, pb_height, x, y)

  if HaveModeBox:
    OV.cmd(pstr)
  else:
    OV.cmd(pstr)
    olx.html.SetBorders(pop_name,0)
    OV.cmd(pstr)
    olx.html.SetBorders(pop_name,0)
    OV.UpdateHtml(pop_name)
    HaveModeBox = True

OV.registerMacro(makeHtmlBottomPop, 'txt-Text to display&;name-Name of the Bottom html popupbox')

def OnModeChange(*args):
  global last_mode, last_mode_options
  debug = OV.GetParam("olex2.debug")
  d = {
    'movesel':'button-move_near',
    'movesel -c=':'button-copy_near',
    'grow':'button-grow_mode',
    'split -r=EADP':'button_full-move_atoms_or_model_disorder',
    'split':'button_full-move_atoms_or_model_disorder',
    'fit':'button_full-fit_group',
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

  if last_mode == active_mode and last_mode is not None and\
     modequalifiers == last_mode_options:
    return

  if not active_mode:
    active_mode = d.get(mode_disp, None)

  if mode == 'off':
    OV.SetParam('olex2.in_mode',None)
    OV.cmd("html.hide pop_%s" %name)
    if not last_mode: return
    control = "IMG_%s" %last_mode.upper()
    if OV.IsControl(control):
      OV.SetImage(control,"up=%soff.png,hover=%shover.png" %(last_mode,last_mode))
    OV.cmd("html.hide pop_%s" %name)
    last_mode = None
    last_mode_options = None
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
        OV.SetImage(control,"up=%son.png,hover=%son.png" %(active_mode,active_mode))
    if last_mode:
      control = "IMG_%s" %last_mode.upper()
      if OV.IsControl(control):
        OV.SetImage(control,"up=%soff.png,hover=%shover.png" %(last_mode,last_mode))

    last_mode = active_mode
    last_mode_options = modequalifiers
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

  buttons = ['btn-solve']
  if name in buttons:
    if OV.GetParam('olex2.solving') == True:
      return True
  buttons = ['btn-refine']
  if name in buttons:
    if OV.GetParam('olex2.refining') == True:
      return True
  buttons = ['btn-report']
  if name in buttons:
    if OV.GetParam('olex2.reporting') == True:
      return True

  return False


def MakeHoverButton(name, cmds, onoff = "off", btn_bg='table_firstcol_colour'):
  #global time_add
  #t = time.time()
  hover_buttons = OV.GetParam('olex2.hover_buttons')
  on = _check_modes_and_states(name)

  if on:
    txt = MakeHoverButtonOn(name, cmds, btn_bg)
  else:
    txt = MakeHoverButtonOff(name, cmds, btn_bg)
  #diff = (time.time() - t)
  #time_add += diff
  #print "MakeHoverButtons took %.6fs (%.4f)" %(diff, time_add)
  return txt

OV.registerFunction(MakeHoverButton)

def MakeHoverButtonOff(name, cmds, btn_bg='table_firstcol_colour'):
  if "None" in name:
    return ""
  hover_buttons = OV.GetParam('olex2.hover_buttons')
  click_console_feedback = False
  n = name.split("-")
  d = {'bgcolor': OV.GetParam('gui.html.%s' %btn_bg)}
  if len(n) > 1:
    target=n[1]
  else:
    target="Not Defined"
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
<font size='$GetVar(HtmlFontSizeControls)'>
<input
  name="IMG_%(nameupper)s"
  type="button"
  image="up=%(tool_img)s%(off)s.png,down=%(tool_img)s%(down)s.png,hover=%(tool_img)s%(hover)s.png"
  hint="%(target)s"
  onclick="%(cmds)s%(feedback)s"
  bgcolor="%(bgcolor)s"
>
</font>
'''%d
  return txt
OV.registerFunction(MakeHoverButtonOff)


def MakeHoverButtonOn(name,cmds,btn_bg='table_firstcol_colour'):
  if "None" in name:
    return ""
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
<font size='$GetVar(HtmlFontSizeControls)'>
<input
  name="IMG_%(nameupper)s"
  type="button"
  image="up=%(tool_img)s%(on)s.png,down=%(tool_img)s%(down)s.png,hover=%(tool_img)s%(hover)s.png"
  hint="%(target)s"
  onclick="%(cmds)s%(feedback)s"
  bgcolor="%(bgcolor)s"
>
</font>
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
  #olx.html.SetImage("BANNER_IMAGE","banner_%i.png" %i)
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

  ist += d.get('html.ItemState',0)
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
      <a href='spy.GetTip(%i)>>html.Update'>%s</a>
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
  try:
    txt = txt.encode('utf-8')
  except:
    print("Can't decode %s" %txt)
  OV.write_to_olex("tip-of-the-day-content.htm", txt)
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
    html_formula = olx.xf.GetFormula('html',1)
    formula_string = "<font size=%s color=%s>%s</font>" %(font_size, colour, html_formula)
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
