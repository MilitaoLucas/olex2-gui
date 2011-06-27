# programSettings.py

import ExternalPrgParameters
SPD, RPD = ExternalPrgParameters.SPD, ExternalPrgParameters.RPD

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
    <table border="0" VALIGN='center' style="border-collapse: collapse" width="100%%" cellpadding="1" cellspacing="1" bgcolor="$spy.GetParam(gui.html.table_bg_colour)">
"""

  txt += ''.join([makeArgumentsHTML(program, method, instruction)
                  for instruction in method.instructions()])

  txt += r'''
<tr>
  <td valign="center" width="2" bgcolor="$spy.GetParam(gui.html.table_firstcol_colour)"></td>
  <td colspan="%s">
    %s - %s
  </td>
</tr>
<tr>
  <td valign="center" width="2" bgcolor="$spy.GetParam(gui.html.table_firstcol_colour)"></td>
  %s
</tr>
</table>
''' %(max_colspan, authors, reference, method.extraHtml())
  
  OlexVFS.write_to_olex(wFilePath, txt)
  return

def makeArgumentsHTML(program, method, instruction):
  txt = '<tr>'
  first_col = htmlTools.make_table_first_col()
  txt += first_col
  if instruction.caption is not None:
    argName = instruction.caption
  else:
    argName = instruction.name
  help = htmlTools.make_help_href(argName, 'true')

  name = instruction.name

  if instruction.optional:
    tick_box_d = {'height':16, 'width':16}
    tick_box_d.setdefault('ctrl_name', 'SET_SETTINGS_%s' %name.upper())
    tick_box_d.setdefault('checked', '$GetVar(settings_%s)' %name)
    tick_box_d.setdefault('value', '')
    tick_box_d.setdefault('oncheck', 'SetVar(settings_%s,GetState(SET_SETTINGS_%s))>>spy.addInstruction(%s,%s,%s)' %(
      name, name, program.name, method.name, name))
    tick_box_d.setdefault('onuncheck', 'SetVar(settings_%s,GetState(SET_SETTINGS_%s))>>DelIns %s' %(
      name, name, argName))
    tick_box_html = htmlTools.make_tick_box_input(tick_box_d)
  else:
    tick_box_html = ''
  txt += '''
  <td colspan=5 valign='center' bgcolor='$spy.GetParam(gui.html.table_firstcol_colour)'>
    <b>%s</b> %s
  </td>
  <td valign='center' align='right' bgcolor='$spy.GetParam(gui.html.table_firstcol_colour)'>
    %s
  </td>
</tr>
<tr>
%s
''' %(argName, help, tick_box_html, first_col)

  options_gui = []
  count = 0
  for option in method.options(instruction.name):
    count += 1

    varName = 'settings_%s_%s' %(name.lower(), option.name)
    data_type = option.type.phil_type
    caption = option.caption
    if caption is None:
      caption = option.name
    value = 'GetVar(%s)' %(varName)
    if value is None:
      value = ''
    ctrl_name = 'SET_%s' %(varName.upper())
    onchange = 'SetVar(%s,GetValue(%s))>>spy.addInstruction(%s,%s,%s)' %(
      varName, ctrl_name, program.name, method.name, name)
    
    if "settings_cf" in varName:
      value = "$spy.GetParam('programs.solution.smtbx.cf.%s')" %(varName.lstrip('settings_cf'))
      onchange = "spy.SetParam('programs.solution.smtbx.cf.%s',GetValue(%s))" %(varName.lstrip('settings_cf'), ctrl_name)
    
    if option.name == 'nls':
      onchange = '%s>>spy.SetParam(snum.refinement.max_cycles,GetValue(SET_SETTINGS_%s_NLS))>>updatehtml' %(onchange, name.upper())
    elif option.name == 'npeaks':
      onchange = '%s>>spy.SetParam(snum.refinement.max_peaks,GetValue(SET_SETTINGS_%s_NPEAKS))>>updatehtml' %(onchange, name.upper())
    #if data_type == "int":
      #d = {'ctrl_name':ctrl_name,
           #'value':value,
           #'label':'%s ' %caption,
           #'onchange':onchange,
           #}
      #if option.type.value_max is not None:
        #d.setdefault('max', option.type.value_max)
      #else:
        #d.setdefault('max', '')
      #if option.type.value_min is not None:
        #d.setdefault('min', option.type.value_min)
      #else:
        #d.setdefault('min', '')
      #options_gui.append(htmlTools.make_spin_input(d))

    #elif data_type == "float":
    if data_type in ("float", "int"):
      d = {'ctrl_name':ctrl_name,
           'value':value,
           'label':'%s ' %caption,
           'onchange':onchange,
           }
      options_gui.append(htmlTools.make_input_text_box(d))

    elif data_type == "str":
      d = {'ctrl_name':ctrl_name,
           'value':value,
           'label':'%s ' %caption,
           'onchange':onchange,
           }
      options_gui.append(htmlTools.make_input_text_box(d))

    elif data_type == "bool":
      d = {'ctrl_name':ctrl_name,
           'value':'%s ' %caption,
           'checked':'%s' %value,
           'oncheck':'SetVar(%s,True)' %(varName),
           'onuncheck':'SetVar(%s,True)' %(varName),
           'width':80,
           'bgcolor':"",
           'fgcolor':"",
           }
      options_gui.append(htmlTools.make_tick_box_input(d))

    elif data_type == "choice":
      items_l = []
      for thing in option.words:
        items_l.append(thing.value.lstrip('*'))
      items = ";".join(items_l)
      d = {'ctrl_name':ctrl_name,
           'label':'%s ' %caption,
           'items':items,
           'value':option.extract(),
           'onchange':onchange,
           'width':'',
           }
      options_gui.append(htmlTools.make_combo_text_box(d))

    if count == 7:
      txt += '</tr><tr>'
      txt += first_col
    txt += '''
<td valign='bottom' align='left' width='40' colspan="1">
  %s
</td>''' %(options_gui[-1])

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

  for ins in method.instructions():
    if ins.name == instruction:
      break

  if ins.optional and \
     OV.FindValue('settings_%s' %instruction) not in (True, 'True', 'true'):
    return

  if ins.caption is not None:
    argName = ins.caption
  else:
    argName = ins.name
  addins = argName
  for option in method.options(ins.name):
    val = OV.FindValue('settings_%s_%s' %(ins.name, option.name))
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

  for instruction in method.instructions():
    for item in ['ls', 'cgls']:
      if instruction.name == item:
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

  for instruction in method.instructions():
    if instruction.name == 'plan':
      OV.SetVar('settings_plan_npeaks', max_peaks)
      ctrl_name = 'SET_SETTINGS_PLAN_NPEAKS'
      if OV.HasGUI() and OV.IsControl(ctrl_name):
        olx.SetValue(ctrl_name, max_peaks)
      addInstruction(prg.name, method.name, 'plan')
      return
OV.registerFunction(OV.SetMaxPeaks)

def stopShelx():
  """Writes the file name.fin to the directory in which shelx is run.
     This stops the refinement or solution after the current iteration
     (for shelxl and shelxd at least)"""
  try:
    file = open('%s/temp/%s.fin' %(
      OV.StrDir(), OV.FileName().replace(' ', '').lower()), 'w')
    file.close()
  except AttributeError:
    pass
  return
OV.registerFunction(stopShelx)
