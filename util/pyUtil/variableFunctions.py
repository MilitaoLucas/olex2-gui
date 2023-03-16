import os
import shutil
import sys
try:
  import pickle as pickle # faster C reimplementation of pickle module
except ImportError:
  import pickle # fall back on Python version
import olex
import olx
import userDictionaries
import ExternalPrgParameters
from olexFunctions import OV
from io import StringIO

import phil_interface

import iotbx.phil
import libtbx.phil.command_line


def getOlex2VersionInfo():
  txt = 'Olex2, OlexSys Ltd (compiled %s)' %OV.GetCompilationInfo()
  return txt

def getDefaultPrgMethod(prgType):
  import olexex
#  defaultPrg = '?'
#  defaultMethod = '?'
  if prgType == 'Refinement':
    prg = OV.GetParam('snum.refinement.default_program')
    method = OV.GetParam('snum.refinement.default_method')
    if prg and method:
      return prg, method
    else:
      availablePrgs = olexex.get_refinement_programs().split(';')
      prgList = ('olex2.refine', 'XL', 'ShelXL', 'XH', 'ShelXH')
      prgDict = olexex.RPD
  elif prgType == 'Solution':
    prg = OV.GetParam('snum.solution.default_program')
    method = OV.GetParam('snum.solution.default_method')
    if prg and method:
      return prg, method
    else:
      availablePrgs = olexex.get_solution_programs().split(';')
      prgList = ('olex2.solve', 'XS', 'ShelXS', 'XM', 'ShelXD', 'Superflip')
      prgDict = olexex.SPD
  for prg in prgList:
    if prg in availablePrgs:
      defaultPrg = prg
      program = prgDict.programs[prg]
      defaultMethod = olexex.sortDefaultMethod(program)
      break
  return defaultPrg, defaultMethod

def Pickle(item,path):
  if "none/.olex" in path:
    return
  pFile = open(path, 'wb')
  pickle.dump(item, pFile)
  pFile.close()

def unPickle(path):
  pFile = None
  try:
    pFile = open(path, 'rb')
    data = pickle.load(pFile, encoding='latin1')
  except Exception as e:
    print(e)
    # compatibility for files that were not saved in mode 'wb'
    if pFile is not None:
      pFile.close()
      pFile = None
    pFile = open(path, 'r', encoding='latin1')
    data = pickle.load(pFile)
  finally:
    if pFile is not None:
      pFile.close()
  #except IOError:
    #data = None
  return data

def AddVariableToUserInputList(variable):
  """Adds the name of the variable to a list of user-edited variables."""
  val = OV.GetParam(variable,None)
  if not val:
    RemoveVariableFromUserInputList(variable)
    return
  variable_list = OV.GetParam("snum.metacif.user_input_variables")
  variable = str(variable) # get rid of unicode
  if variable_list is None:
    variable_list = variable
    OV.SetParam("snum.metacif.user_input_variables", variable_list)
  elif variable_list is not None and variable not in variable_list:
    variable_list += ';%s' %variable
    OV.SetParam("snum.metacif.user_input_variables", variable_list)
OV.registerFunction(AddVariableToUserInputList)

def RemoveVariableFromUserInputList(variable):
  """Remove the name of the variable from the list of user-edited variables."""
  variable_list = OV.GetParam("snum.metacif.user_input_variables")
  variable = str(variable) # get rid of unicode
  if variable_list is None:
    pass
  elif variable_list is not None and variable in variable_list:
    variable_list = variable_list.replace(';%s' %variable,'')
    OV.SetParam("snum.metacif.user_input_variables", variable_list)
OV.registerFunction(RemoveVariableFromUserInputList)

def SwitchAllAlertsOn():
  alerts = ['user.alert_delete_history',
            'user.alert_uninstall_plugin',
            'user.alert_solve_anyway',
            'user.alert_overwrite_history',]
  for item in alerts:
    OV.SetParam(item,'Y')
  SaveUserParams()
OV.registerFunction(SwitchAllAlertsOn)

def VVD_to_phil():
  phil_strings = []
  structureVVDPath = r"%s/%s.vvd" %(OV.StrDir(),OV.FileName())
  # Changed pickle file name from 'vvd.pickle' to 'OV.FileName().vvd'
  oldPicklePath = r"%s/vvd.pickle" %OV.StrDir()
  #snum_scopes = ('refinement','dimas','metacif','history','solution','report','workflow')
  snum_scopes = ('refinement','metacif','history','solution','report')

  if os.path.exists(structureVVDPath):  # Load structure-level stored values
    structureFile = open(structureVVDPath)
    structureVVD = pickle.load(structureFile)
    structureFile.close()
  elif os.path.exists(oldPicklePath):
    # get vvd from old pickle file, save it to new file and then remove old file
    oldFile = open(oldPicklePath)
    structureVVD = pickle.load(oldFile)
    pickleVVD(structureVVD)
    oldFile.close()
    os.remove(oldPicklePath)
    structureFile = open(structureVVDPath)
    structureVVD = pickle.load(structureFile)
  else:
    return
  if 'refinement' in structureVVD:
    return

  for variable, value in list(structureVVD.items()):  # Set values of all variables in Olex2
    variable_name = variable[5:] # remove "snum_" from beginning of name
    for scope in snum_scopes:
      if variable_name.startswith(scope):
        variable_name = variable_name.replace('%s_' %scope, '%s.' %scope).replace('-','_')
        if 'auto_' in variable_name:
          variable_name = variable_name.replace('auto_','auto.')
        if value not in ('?','--','.'): # XXX
          phil_strings.append('snum.%s="%s"' %(variable_name, value))
        break
  return '\n'.join(phil_strings)

def get_phil_file_path(which):
  user_phil_file = os.path.join(OV.DataDir(), '%s.phil' %which)
  if os.path.exists(user_phil_file):
    return user_phil_file
  else:
    return None

def LoadParams():
  # snum params

  master_phil = phil_interface.parse(file_name="%s/params.phil" %OV.BaseDir())
  phil_handler = phil_interface.phil_handler(
    master_phil=master_phil,
    parse=phil_interface.parse)

  scopes = ['olex2', 'user', 'custom', 'snum']
  for scope in scopes:
    phil_p = get_phil_file_path(scope)
    if phil_p and os.path.exists(phil_p):
      try:
        phil_handler.update(phil_file=phil_p)
      except:
        print("Failed to read %s.phil" %scope)
        try:
          os.rename(phil_p, phil_p + ".bad")
        except:
          pass
  olx.phil_handler = phil_handler

  # GUI Phil
  if OV.HasGUI() or True:
    try:
      master_gui_phil = phil_interface.parse(file_name="%s/gui.params" %OV.BaseDir())
      gui_phil_handler = phil_interface.phil_handler(
        master_phil=master_gui_phil,
        parse=phil_interface.parse)
      olx.gui_phil_handler = gui_phil_handler
    except Exception as e:
      print("Failed to read gui.phil")
      try:
        os.rename(phil_p, phil_p + ".bad")
      except:
        pass
OV.registerFunction(LoadParams)

def LoadStructureParams():
  import olexex
  ExternalPrgParameters.definedControls = [] # reset defined controls
  olx.current_mask = None
  # read current setting - to use for the new structures
  solutionPrg = OV.GetParam('user.solution.default_program')
  solutionMethod = OV.GetParam('user.solution.default_method')
  if not solutionPrg:
    solutionPrg = olx.phil_handler.get_validated_param('snum.solution.program')
    solutionMethod = olx.phil_handler.get_validated_param('snum.solution.method')
  refinementPrg = OV.GetParam('user.refinement.default_program')
  refinementMethod = OV.GetParam('user.refinement.default_method')
  if not refinementPrg:
    refinementPrg = olx.phil_handler.get_validated_param('snum.refinement.program')
    refinementMethod = olx.phil_handler.get_validated_param('snum.refinement.method')
  olx.phil_handler.reset_scope('snum', rebuild_index=True)
  model_src = OV.ModelSrc()
  structure_phil_path = "%s/%s.phil" %(OV.StrDir(), model_src)
  if os.path.isfile(structure_phil_path):
    structure_phil = open(structure_phil_path, 'r', encoding="utf-8").read()
    if """\"[\" \"[',\"""" in structure_phil:
      return # to get around any problems caused by bug that was fixed in r2585
  else:
    # check if old-style vvd file is present
    structure_phil = VVD_to_phil()
  if structure_phil is not None:
    # XXX Backwards compatibility 2010-04-08
    structure_phil = structure_phil\
      .replace('smtbx-refine', 'olex2.refine')\
      .replace('smtbx-solve', 'olex2.solve')

    olx.phil_handler.update(phil_string=structure_phil)
    solutionPrg = OV.getCompatibleProgramName(
      olx.phil_handler.get_validated_param('snum.solution.program'))
    solutionMethod = olx.phil_handler.get_validated_param('snum.solution.method')
    refinementPrg = OV.getCompatibleProgramName(
      olx.phil_handler.get_validated_param('snum.refinement.program'))
    refinementMethod = olx.phil_handler.get_validated_param('snum.refinement.method')
  #
  # Start backwards compatibility  2010-06-18
  #
  StrDir = OV.StrDir()
  olx.cif_model = None #reset the cif model, #399
  metacif_path = os.path.join(OV.StrDir(), model_src + ".metacif")
  if StrDir and not os.path.isfile(metacif_path) and structure_phil is not None:
    from iotbx.cif import model
    master_phil = phil_interface.parse(
      file_name=os.path.join(OV.BaseDir(), "metacif.phil"))
    user_phil = phil_interface.parse(structure_phil)
    diff = master_phil.fetch_diff(source=user_phil)
    active_objects = diff.active_objects()
    def name_value_pairs(active_objects):
      result = []
      for object in active_objects:
        if object.is_scope:
          result += name_value_pairs(object.master_active_objects())
        elif object.is_definition:
          result.append(("_%s" %(object.name), object.extract()))
      return result
    cif_items = name_value_pairs(diff.get('snum.metacif').master_active_objects())
    if cif_items:
      cif_block = model.block()
      for key, value in cif_items:
        cif_block[key] = value
      cif_model = model.cif({model_src: cif_block})
      with open(metacif_path, 'w') as f:
        print(cif_model, file=f)
  #
  # End backwards compatibility
  #
  import CifInfo
  CifInfo.reloadMetadata()
  if OV.IsFileType('ires'):
    if solutionMethod == 'Direct Methods' and olx.Ins('PATT') != 'n/a':
      solutionMethod = 'Patterson Method' # work-around for bug #48
    if refinementMethod == 'Least Squares' and olx.LSM() == 'CGLS':
      refinementMethod = 'CGLS' # work-around for bug #26
    params = {
      'R1_gt': 'snum.refinement.last_R1',
      'wR_ref': 'snum.refinement.last_wR2',
      'Peak': 'snum.refinement.max_peak',
      'Hole': 'snum.refinement.max_hole',
      'Shift_max': 'snum.refinement.max_shift_over_esd',
      'Flack': 'snum.refinement.hooft_str',
      'GOOF': 'snum.refinement.goof',
    }
    for p in olx.xf.RefinementInfo().split(';'):
      t = p.split('=')
      if len(t) != 2 or t[0] not in params or t[1].lower() == 'n/a': continue
      OV.SetParam(params[t[0]], t[1])

  olexex.onSolutionProgramChange(solutionPrg, solutionMethod)
  olexex.onRefinementProgramChange(refinementPrg, refinementMethod)

OV.registerFunction(LoadStructureParams)

def SaveStructureParams():
  if OV.FileName() != 'none':
    structure_phil_file = "%s/%s.phil" %(OV.StrDir(), OV.ModelSrc())
    olx.phil_handler.save_param_file(
      file_name=structure_phil_file, scope_name='snum', diff_only=True)
    auto_save_view = OV.GetParam('user.auto_save_view', False)
    if auto_save_view and olx.IsFileType('oxm') != 'true':
      oxvf = os.path.join(OV.StrDir(), OV.ModelSrc() + '.oxv')
      olex.m("save gview '%s'" %oxvf)
OV.registerFunction(SaveStructureParams)

def OnStructureLoaded(previous):
  if olx.IsFileLoaded() == 'false' or not OV.StrDir():
    return
  auto_save_view = OV.GetParam('user.auto_save_view', False)
  if auto_save_view and olx.IsFileType('oxm') != 'true':
    oxvf = os.path.join(OV.StrDir(), OV.ModelSrc() + '.oxv')
    if os.path.exists(oxvf):
      olex.m("load gview '%s'" %oxvf)
  mf_name = "%s%s%s.metacif" %(OV.StrDir(), os.path.sep, OV.ModelSrc(force_cif_data=True))
  cif_name = "%s%s%s.cif" % (OV.FilePath(), os.path.sep, OV.FileName())
  if not os.path.exists(mf_name) and os.path.exists(cif_name):
    if olx.IsFileType('cif') == 'true':
      cif_name = cif_name + "#" + olx.xf.CurrentData()
    olx.CifExtract(cif_name, mf_name)

  LoadStructureParams()

  # set default ED params if needed
  if OV.IsEDData():
    sft = OV.GetParam("snum.smtbx.atomic_form_factor_table")
    ed_table = OV.GetParam("snum.smtbx.electron_table_name")
    if "electron" != sft or (not ed_table or ed_table == 'None'):
      OV.SetParam("snum.smtbx.atomic_form_factor_table", "electron")
      OV.SetParam("snum.smtbx.electron_table_name", "Peng-1999")

  # Disable this altogether until it works properly.
  #if olx.IsFileType('oxm') == 'false':
    #import gui.skin
    #gui.skin.change_bond_colour()

  if previous != OV.FileFull() and olx.FileExt() != "cif":
    import History
    History.hist.loadHistory()
    OV.ResetMaskHKLWarning()
  if olx.IsFileType('ires') == 'true':
    OV.SetParam("snum.refinement.use_solvent_mask", olx.Ins("ABIN") != "n/a")
    call_listener('structure')

OV.registerFunction(OnStructureLoaded)

def OnHKLChange(hkl):
  olx.HKLSrc(hkl)
  OV.SetParam('snum.current_process_diagnostics', 'data')
  olex.m("spy.make_HOS('True')")
  OV.ResetMaskHKLWarning()
  call_listener('hkl')
OV.registerFunction(OnHKLChange)

def call_listener(filetype):
  try:
    for l in olx.FileChangeListeners:
      try:
        l(filetype)
      except:
        pass
  except:
    pass

def SavesNumParams():
  snum_phil_file = os.path.join(OV.DataDir(), "snum.phil")
  olx.phil_handler.save_param_file(
    file_name=snum_phil_file, scope_name='snum', diff_only=True)
OV.registerFunction(SavesNumParams)

def SaveGuiParams():
  gui_phil_file = os.path.join(OV.DataDir(), "gui.phil")
  olx.gui_phil_handler.save_param_file(
    file_name=gui_phil_file, scope_name='gui', diff_only=True)
OV.registerFunction(SaveGuiParams)

def SaveUserParams():
  user_phil_file = os.path.join(OV.DataDir(), "user.phil")
  olx.phil_handler.save_param_file(
    file_name=user_phil_file, scope_name='user', diff_only=True)
OV.registerFunction(SaveUserParams)

def SaveOlex2Params():
  olex2_phil_file = os.path.join(OV.DataDir(), "olex2.phil")
  olx.phil_handler.save_param_file(
    file_name=olex2_phil_file, scope_name='olex2', diff_only=True)
OV.registerFunction(SaveOlex2Params)

def EditParams(scope_name="", expert_level=0, attributes_level=0):
  expert_level = int(expert_level)
  if scope_name.startswith("gui"):
    handler = olx.gui_phil_handler
  else:
    handler = olx.phil_handler
  try:
    output_phil = handler.get_scope_by_name(scope_name)
    original_name = output_phil.name
    output_phil.name = scope_name
  except KeyError:
    print('"%s" is not a valid scope name' %scope_name)
  else:
    s = StringIO()
    output_phil.show(out=s, expert_level=expert_level, attributes_level=attributes_level)
    input_phil_string = OV.GetUserInput(0, "Edit parameters", s.getvalue())
    if input_phil_string is not None and not input_phil_string == s.getvalue():
      handler.update(phil_string=input_phil_string)
    else:
      # need to set scope name back to original since scope isn't rebuilt
      output_phil.name = original_name
OV.registerFunction(EditParams)

def ShowParams(expert_level=0, attributes_level=0):
  olx.phil_handler.working_phil.show(
    expert_level=int(expert_level), attributes_level=int(attributes_level))
OV.registerFunction(ShowParams)
