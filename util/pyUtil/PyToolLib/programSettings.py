# programSettings.py

import ExternalPrgParameters
SPD, RPD = ExternalPrgParameters.defineExternalPrograms()

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import olx
import olex_core
import OlexVFS
import htmlTools

def doProgramSettings(programName, methodName, postSolution=False):
  if not OV.IsFileType('ires'):
    return
  if programName in SPD.programs:
    program = SPD.programs[programName]
    prgtype = 'solution'
  elif programName in RPD.programs:
    program = RPD.programs[programName]
    prgtype = 'refinement'
  else:
    return
  method = program.methods[methodName]
  method.calculate_defaults()
  if not postSolution:
    method.getValuesFromFile()
  if prgtype == 'refinement':
    method.addInstructions()
  if OV.HasGUI():
    makeProgramSettingsGUI(program, method, prgtype)
  return ''

OV.registerFunction(doProgramSettings)

def makeProgramSettingsGUI(program, method, prgtype):
  if prgtype == 'solution':
    wFilePath = 'solution-settings-h3-solution-settings-extra.htm'
  else:
    wFilePath = 'refinement-settings-h3-refinement-settings-extra.htm'
    
  authors = program.author
  reference = program.reference
  help = OV.TranslatePhrase(method.help)
  
  max_colspan = 6
  txt = r"""
<!-- #include tool-h3 gui\blocks\tool-h3.htm;image=#image;colspan=4;1; -->
    <table border="0" VALIGN='center' style="border-collapse: collapse" width="100%%" cellpadding="1" cellspacing="1" bgcolor="$getVar(gui_html_table_bg_colour)">
"""

  txt += ''.join([makeArgumentsHTML(arg) for arg in method.args])

  txt += r'''
<tr>
  <td valign="center" width="2" bgcolor="$getVar(gui_html_table_firstcol_colour)"></td>
  <td colspan="%s">
    %s - %s
  </td>
</tr>
<tr>
  <td valign="center" width="2" bgcolor="$getVar(gui_html_table_firstcol_colour)"></td>
  %s
</tr>
</table>
''' %(max_colspan, authors, reference, method.extraHtml())
  
  OlexVFS.write_to_olex(wFilePath, txt)
  return

def makeArgumentsHTML(dictionary):
  txt = ''
  first_col = htmlTools.make_table_first_col()
  txt += first_col
  help = htmlTools.make_help_href(make_help=(dictionary['name'], 'true'))
  
  argName = dictionary['name']
  
  tick_box_d = {'height':16, 'width':16}
  tick_box_d.setdefault('ctrl_name', 'SET_SETTINGS_%s' %dictionary['name'].upper())
  tick_box_d.setdefault('state', '$spy.CheckBoxValue(settings_%s)' %argName)
  tick_box_d.setdefault('value', '')
  tick_box_d.setdefault('oncheck', 'SetVar(settings_%s,GetState(SET_SETTINGS_%s))>>spy.addInstruction(%s)' %(argName,argName,argName))
  tick_box_d.setdefault('onuncheck', 'SetVar(settings_%s,GetState(SET_SETTINGS_%s))>>DelIns %s' %(argName,argName,tick_box_d['ctrl_name']))
  tick_box_html = htmlTools.make_tick_box_input(tick_box_d)
  
  txt += '''
  <td colspan=5 valign='center' bgcolor='$GetVar(gui_html_table_firstcol_colour)'>
    <b>%s</b> %s
  </td>
  <td valign='center' align='right' bgcolor='$GetVar(gui_html_table_firstcol_colour)'>
    %s
  </td>
</tr>
%s
''' %(argName, help, tick_box_html, first_col)
  
  count = 0
  for value in dictionary['values']:
    count += 1
    d = {'height':17, 'width':32}
    name = value[0]
    varName = 'settings_%s_%s' %(dictionary['name'].lower(), name.lower())
    d.setdefault('ctrl_name', 'SET_%s' %varName.upper())
    
    onchange = 'spy.addInstruction(%s)>>SetVar(%s,GetValue(SET_%s))' %(argName,varName,varName.upper())
    if name == 'nls':
      maxCycles_onchange = '%s>>spy.SetParam(snum.refinement.max_cycles,GetValue(SET_SETTINGS_%s_NLS))>>updatehtml' %(onchange,argName.upper())
      d.setdefault('onleave', maxCycles_onchange)
    elif name == 'npeaks':
      maxPeaks_onchange = '%s>>spy.SetParam(snum.refinement.max_peaks,GetValue(SET_SETTINGS_%s_NPEAKS))>>updatehtml' %(onchange,argName.upper())
      d.setdefault('onleave', maxPeaks_onchange)
    else:
      d.setdefault('onleave', onchange)
    d.setdefault('value', 'GetVar(%s)' %(varName))
    d.setdefault('label', '')
    inputBox = htmlTools.make_input_text_box(d)
    if count == 7:
      txt += '</tr><tr>'
      txt += first_col
    txt += '''
<td valign='bottom' align='left' width='40' colspan="1">
  %s
  <br>
  %s
</td>''' %(name, inputBox)
  
  txt += '</tr>'
  
  return txt

def make_ondown(dictionary):
  args = ''.join([' GetValue(SET_SETTINGS_%s)' %item[0].upper() for item in dictionary['values']])
  txt = 'Addins %s%s' %(dictionary['name'], args)
  return txt

def addInstruction(instruction):
  if OV.FindValue('settings_%s' %instruction) != 'true':
    return
  program = RPD.programs[OV.GetParam('snum.refinement.program')]
  method = program.methods[OV.GetParam('snum.refinement.method')]
  
  for arg in method.args:
    if arg['name'] == instruction:
      break
    
  argName = '%s' %arg['name']
  addins = '%s' %argName
  
  for value in arg['values']:
    value = OV.FindValue('settings_%s_%s' %(argName, value[0]))
    if not value:
      break
    addins += ' %s' %value
    
  OV.DelIns(argName)
  OV.AddIns(addins)
OV.registerFunction(addInstruction)

def onMaxCyclesChange(max_cycles):
  if not OV.IsFileType('ires'):
    return
  try:
    prg = RPD.programs[OV.GetParam('snum.refinement.program')]
    method = prg.methods[OV.GetParam('snum.refinement.method')]
  except KeyError:
    return
  
  for arg in method.args:
    for item in ['L.S.', 'CGLS']:
      if arg['name'] == item:
        OV.SetVar('settings_%s_nls' %item, max_cycles)
        ctrl_name = 'SET_SETTINGS_%s_NLS' %item.upper()
        if OV.HasGUI() and OV.IsControl(ctrl_name):
          olx.SetValue(ctrl_name, max_cycles)
        addInstruction(item)
        return
OV.registerFunction(OV.SetMaxCycles)

def onMaxPeaksChange(max_peaks):
  if not OV.IsFileType('ires'):
    return
  try:
    prg = RPD.programs[OV.GetParam('snum.refinement.program')]
    method = prg.methods[OV.GetParam('snum.refinement.method')]
  except KeyError:
    return
  
  item = 'PLAN'
  for arg in method.args:
    if arg['name'] == item:
      OV.SetVar('settings_%s_npeaks' %item, max_peaks)
      ctrl_name = 'SET_SETTINGS_%s_NPEAKS' %item.upper()
      if OV.HasGUI() and OV.IsControl(ctrl_name):
        olx.SetValue(ctrl_name, max_peaks)
      addInstruction(item)
      return
OV.registerFunction(OV.SetMaxPeaks)

def stopShelxd():
  try:
    file = open(ExternalPrgParameters.stop_path, 'w')
    file.close()
  except AttributeError:
    pass
  return
OV.registerFunction(stopShelxd)
