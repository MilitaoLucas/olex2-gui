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

  txt += ''.join([makeArgumentsHTML(program.name, method.name, arg) for arg in method.args])

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

def makeArgumentsHTML(program, method, dictionary):
  txt = '<tr>'
  first_col = htmlTools.make_table_first_col()
  txt += first_col
  help = htmlTools.make_help_href(dictionary['name'], 'true')
  
  argName = dictionary['name']
  name = argName.replace('.','')
  
  if dictionary['optional']:
    tick_box_d = {'height':16, 'width':16}
    tick_box_d.setdefault('ctrl_name', 'SET_SETTINGS_%s' %name.upper())
    tick_box_d.setdefault('state', '$spy.CheckBoxValue(settings_%s)' %name)
    tick_box_d.setdefault('value', '')
    tick_box_d.setdefault('oncheck', 'SetVar(settings_%s,GetState(SET_SETTINGS_%s))>>spy.addInstruction(%s,%s,%s)' %(name,name,program, method, name))
    tick_box_d.setdefault('onuncheck', 'SetVar(settings_%s,GetState(SET_SETTINGS_%s))>>DelIns %s' %(name,name,argName))
    tick_box_html = htmlTools.make_tick_box_input(tick_box_d)
  else:
    tick_box_html = ''
  txt += '''
  <td colspan=5 valign='center' bgcolor='$GetVar(gui_html_table_firstcol_colour)'>
    <b>%s</b> %s
  </td>
  <td valign='center' align='right' bgcolor='$GetVar(gui_html_table_firstcol_colour)'>
    %s
  </td>
</tr>
<tr>
%s
''' %(argName, help, tick_box_html, first_col)
  
  count = 0
  for value in dictionary['values']:
    count += 1
    d = {'height':17, 'width':32}
    varName = 'settings_%s_%s' %(name.lower(), value[0].lower())
    d.setdefault('ctrl_name', 'SET_%s' %varName.upper())
    
    onchange = 'spy.addInstruction(%s,%s,%s)>>SetVar(%s,GetValue(SET_%s))' %(program, method, name,varName,varName.upper())
    if value[0] == 'nls':
      maxCycles_onchange = '%s>>spy.SetParam(snum.refinement.max_cycles,GetValue(SET_SETTINGS_%s_NLS))>>updatehtml' %(onchange,name.upper())
      d.setdefault('onleave', maxCycles_onchange)
    elif value[0] == 'npeaks':
      maxPeaks_onchange = '%s>>spy.SetParam(snum.refinement.max_peaks,GetValue(SET_SETTINGS_%s_NPEAKS))>>updatehtml' %(onchange,name.upper())
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
</td>''' %(value[0], inputBox)
  
  txt += '</tr>'
  
  return txt

def make_ondown(dictionary):
  args = ''.join([' GetValue(SET_SETTINGS_%s)' %item[0].upper() for item in dictionary['values']])
  txt = 'Addins %s%s' %(dictionary['name'], args)
  return txt

def addInstruction(program, method, instruction):
  program = RPD.programs.get(program, SPD.programs.get(program))
  assert program is not None
  method = program.methods[method]
  
  for arg in method.args:
    if arg['name'].replace('.','') == instruction:
      break

  if arg['optional'] and OV.FindValue('settings_%s' %instruction) != 'true':
    return

  argName = '%s' %arg['name']
  addins = '%s' %argName
  
  for value in arg['values']:
    val = OV.FindValue('settings_%s_%s' %(instruction, value[0]))
    if not val:
      break
    addins += ' %s' %val

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
    for item in ['LS', 'CGLS']:
      if arg['name'].replace('.','') == item:
        OV.SetVar('settings_%s_nls' %item, max_cycles)
        ctrl_name = 'SET_SETTINGS_%s_NLS' %item.upper()
        if OV.HasGUI() and OV.IsControl(ctrl_name):
          olx.SetValue(ctrl_name, max_cycles)
        addInstruction(prg.name, method.name, item)
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
      addInstruction(prg.name, method.name, item)
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
