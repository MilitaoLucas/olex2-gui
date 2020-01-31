# programSettings.py
import os

import ExternalPrgParameters
SPD, RPD = ExternalPrgParameters.get_program_dictionaries()

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import olx
import olex_core
import OlexVFS

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
    wFilePath = 'solution-settings-extra.htm'
  else:
    wFilePath = 'refinement-settings-extra.htm'

  authors = program.author
  reference = program.reference
  help = OV.TranslatePhrase(method.help)

  txt = r"""<!-- #include tool-h3 gui\blocks\tool-h3.htm;image=#image;colspan=1;1; -->
  <table border="0" VALIGN='center' width="100%%" cellpadding="1" cellspacing="1" bgcolor="$GetVar('HtmlTableBgColour')">
"""
  if program.name.lower().startswith("superflip"):
    txt += file(os.path.normpath("%s/etc/gui/tools/superflip.htm" %olx.BaseDir()), "r").read()
  elif program.name.lower().startswith("tonto"):
    txt += file(os.path.normpath("%s/etc/gui/tools/tonto.htm" %olx.BaseDir()), "r").read()
  else:
    txt += ''.join([makeArgumentsHTML(program, method, instruction)
                    for instruction in method.instructions()])
  txt += r'''
<tr>
  <td valign="center" width="%s" bgcolor="$GetVar(HtmlTableFirstcolColour)"></td>
  <td>%s - %s</td>
</tr>
%s
</table>
''' %(OV.GetParam('gui.html.table_firstcol_width'), authors, reference, method.extraHtml())

  OlexVFS.write_to_olex(wFilePath, txt)
  return

def makeArgumentsHTML(program, method, instruction):
  import htmlTools
  first_col1 = htmlTools.make_table_first_col(help_name="%s" %instruction.name)
  first_col = htmlTools.make_table_first_col()
  first_col_width = OV.GetParam('gui.html.table_firstcol_width')
  if instruction.caption is not None:
    argName = instruction.caption
  else:
    argName = instruction.name
#  help = htmlTools.make_help_href(argName, 'true')
  help = "++"

  name = instruction.name

  if instruction.optional:
    tick_box_d = {'height':16, 'width':16}
    tick_box_d.setdefault('ctrl_name', 'SET_SETTINGS_%s' %name.upper())
    tick_box_d.setdefault('checked', '$GetVar(settings_%s)' %name)
    tick_box_d.setdefault('value', '')
    tick_box_d.setdefault('oncheck', "SetVar('settings_%s',html.GetState('SET_SETTINGS_%s'))>>spy.addInstruction('%s','%s','%s')" %(
      name, name, program.name, method.name, name))
    tick_box_d.setdefault('onuncheck', "SetVar('settings_%s',html.GetState('SET_SETTINGS_%s'))>>DelIns %s" %(
      name, name, argName))
    tick_box_html = htmlTools.make_tick_box_input(tick_box_d)
  else:
    tick_box_html = ''

  argName = argName.upper().replace(' ', '&nbsp;')
  txt = '''<tr>%s
  <td valign='center' align='left' bgcolor="$GetVar('HtmlTableFirstcolColour')">
    <b>%s&nbsp;%s</b>
  </td>
</tr>
''' %(first_col1, argName, tick_box_html)

  count = 0
  row_txt = ""
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

    if instruction.name != 'command_line':
      onchange = "SetVar('%s',html.GetValue('%s'))>>spy.addInstruction('%s','%s','%s')" %(
        varName, ctrl_name, program.name, method.name, name)
    else:
      if not program.phil_entry_name:
        assert 0, 'incompatible phil entries'
      param = "snum.%s.%s.command_line" %(program.program_type, program.phil_entry_name)
      onchange = "spy.SetParam('%s',html.GetValue('SET_SETTINGS_%s_OPTIONS'))" %(
        param, name.upper())
      value = "spy.GetParam('%s', '')" %(param)

    if "settings_cf" in varName:
      value = "$spy.GetParam('programs.solution.smtbx.cf.%s')" %(varName.lstrip('settings_cf'))
      onchange = "spy.SetParam('programs.solution.smtbx.cf.%s',html.GetValue('%s'))" %(varName.lstrip('settings_cf'), ctrl_name)

    if option.name == 'nls':
      onchange = "%s>>spy.SetParam('snum.refinement.max_cycles',html.GetValue('SET_SETTINGS_%s_NLS'))>>html.Update" %(onchange, name.upper())
    elif option.name == 'npeaks':
      onchange = "%s>>spy.SetParam('snum.refinement.max_peaks',html.GetValue('SET_SETTINGS_%s_NPEAKS'))>>html.Update" %(onchange, name.upper())
    input_txt = ""
    if data_type in ("float", "int"):
      d = {'ctrl_name':ctrl_name,
           'value':value,
           'label':'%s ' %caption,
           'onleave':onchange,
           'width':'100%',
           }
      input_txt = htmlTools.make_input_text_box(d)

    elif data_type == "str":
      d = {'ctrl_name':ctrl_name,
           'value':value,
           'label':'%s ' %caption,
           'onleave':onchange,
           'width':'100%',
           }
      input_txt = htmlTools.make_input_text_box(d)

    elif data_type == "bool":
      d = {'ctrl_name':ctrl_name,
           'value':'%s ' %caption,
           'checked':'%s' %value,
           'oncheck':"SetVar('%s','True')" %(varName),
           'onuncheck':"SetVar('%s','False')" %(varName),
           'width':'100%',
           'bgcolor':"",
           'fgcolor':"",
           }
      input_txt = htmlTools.make_tick_box_input(d)

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
           'width':'100%',
           }
      input_txt = htmlTools.make_combo_text_box(d)

    row_txt += '''<td valign='bottom' align='left'>%s</td>''' %input_txt

  txt ='''%s<tr>%s<td><table width='100%%'><tr>%s</tr></table></td></tr>''' \
    %(txt, first_col, row_txt)
  return txt

def make_ondown(dictionary):
  args = ''.join([" html.GetValue('SET_SETTINGS_%s')" %item[0].upper() for item in dictionary['values']])
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
          olx.html.SetValue(ctrl_name, max_cycles)
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
        olx.html.SetValue(ctrl_name, max_peaks)
        OV.SetParam('snum.refinement.max_peaks', max_peaks)
      addInstruction(prg.name, method.name, 'plan')
      return
OV.registerFunction(OV.SetMaxPeaks)

def stopProcess():
  """Writes the file name.fin to the directory in which shelx is run.
     This stops the refinement or solution after the current iteration
     (for shelxl and shelxd at least)"""
  OV.SetVar("stop_current_process", True)
  try:
    open(os.path.join(OV.StrDir(), "temp",
                      OV.FileName().replace(' ', '').lower()) + ".fin", 'w')\
      .close()
  except AttributeError:
    pass
  
  try:
    import RunPrg
    if RunPrg.RunPrg.running:
      RunPrg.RunPrg.running.interrupted = True
  except:
    pass

  return
OV.registerFunction(stopProcess)
