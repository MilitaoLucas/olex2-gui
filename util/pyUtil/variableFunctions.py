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

def _build_nsa2_phil_type_map():
  """Parse NoSpherA2.phil and return {snum_key: type_str} for all defined params."""
  import re
  phil_file = os.path.join(os.path.dirname(__file__), 'NoSpherA2', 'NoSpherA2.phil')
  type_map = {}
  try:
    with open(phil_file, 'r') as f:
      lines = f.readlines()
  except IOError:
    return type_map
  scope_stack = []
  current_key = None
  for line in lines:
    stripped = line.strip()
    m = re.match(r'^(\w+)\s*\{', stripped)
    if m:
      scope_stack.append(m.group(1))
      current_key = None
      continue
    if stripped == '}':
      if scope_stack:
        scope_stack.pop()
      current_key = None
      continue
    if stripped.startswith('.'):
      m = re.match(r'^\.type\s*=\s*(\w+)', stripped)
      if m and current_key is not None:
        type_name = m.group(1)
        if type_name == 'choice':
          type_name = 'str'
        full_key = '.'.join(scope_stack + [current_key])
        type_map[full_key] = type_name
        current_key = None
      continue
    m = re.match(r'^(\w+)\s*=', stripped)
    if m:
      current_key = m.group(1)
  return type_map

_NSA2_PHIL_TYPE_MAP = None

def _nsa2_get_type(snum_key):
  """Return the phil type string ('bool','int','float','str') for a snum.* key."""
  global _NSA2_PHIL_TYPE_MAP
  if _NSA2_PHIL_TYPE_MAP is None:
    _NSA2_PHIL_TYPE_MAP = _build_nsa2_phil_type_map()
  return _NSA2_PHIL_TYPE_MAP.get(snum_key, 'str')

def _nsa2_cast_value(snum_key, value):
  """Cast *value* to the Python type declared in the phil definition for *snum_key*."""
  if value is None or not isinstance(value, str):
    return value  # Already typed or missing — leave as-is.
  type_name = _nsa2_get_type(snum_key)
  if type_name == 'bool':
    return value.strip().lower() in ('true', '1', 'yes')
  if type_name == 'int':
    try:
      return int(value)
    except (ValueError, TypeError):
      return value
  if type_name == 'float':
    try:
      return float(value)
    except (ValueError, TypeError):
      return value
  return value  # str (default)

def _nsa2_header_key_from_param(key):
  """Map snum.NoSpherA2.* params to canonical NoSpherA2 Header paths."""
  suffix = key[len('snum.NoSpherA2.'):]
  explicit_map = {
    'file': 'NoSpherA2.table_of_form_factors.file',
    'file_origin': 'NoSpherA2.table_of_form_factors.origin',
    'file_hash': 'NoSpherA2.electron_density_generator.file_hash',
    'selected_salted_model': 'NoSpherA2.electron_density_generator.salted.model',
  }
  partitioning_keys = {
    'NoSpherA2_SF',
    'NoSpherA2_Partition',
    'becke_accuracy',
    'auxiliary_basis',
    'auxiliary_basis_beta',
    'NoSpherA2_ECP',
    'NoSpherA2_debug',
    'NoSpherA2_ED',
  }
  generator_keys = {
    'method',
    'basis_name',
    'charge',
    'multiplicity',
    'Relativistic',
    'ncpus',
    'mem',
    'source',
    'Thakkar_Cations',
    'Thakkar_Anions',
    'cluster_radius',
    'cluster_grow',
    'DIIS',
    'full_HAR',
    'temperature',
    'basis_adv',
    'basis_adv_string',
    'fchk_file',
    'distro',
    'OCC_df_basis',
    'PTB_use_purify',
    'muliplicity',
  }

  if suffix in explicit_map:
    return explicit_map[suffix]
  if suffix in partitioning_keys:
    return 'NoSpherA2.partitioning.%s' % suffix
  if suffix in generator_keys:
    return 'NoSpherA2.electron_density_generator.%s' % suffix
  if suffix.startswith(('ORCA_', 'pySCF_', 'ELMOdb.', 'xharpy.', 'frag_HAR.')):
    return 'NoSpherA2.electron_density_generator.%s' % suffix
  return 'NoSpherA2.%s' % suffix


def _nsa2_normalize_param_key(key):
  """Normalize NoSpherA2 keys to snum.NoSpherA2.* form.

  Accepted shorthand examples:
  - method -> snum.NoSpherA2.method
  - NoSpherA2.method -> snum.NoSpherA2.method
  - snum.NoSpherA2.method -> unchanged
  """
  key = str(key)
  if key.startswith('snum.NoSpherA2.'):
    return key
  if key.startswith('NoSpherA2.'):
    return 'snum.%s' % key
  if '.' not in key:
    return 'snum.NoSpherA2.%s' % key
  if key.startswith(('user.', 'olex2.', 'snum.')):
    return key
  return 'snum.NoSpherA2.%s' % key


def _nsa2_should_persist_to_header(key):
  """Return False for NoSpherA2 UI/runtime-only keys that should not go to .ins."""
  if not key.startswith('snum.NoSpherA2.'):
    return False
  suffix = key[len('snum.NoSpherA2.'):]
  if suffix.startswith('map.'):
    return False
  if suffix.startswith('Property'):
    return False
  return True

def nsa2_get_param(key, default=None):
  """Global accessor exposed as spy.nsa2_get_param for HTML/UI conditions.

  Returns values cast to the Python type declared in the phil definition
  (bool, int, float, or str).  Values retrieved from the structure Header are
  always strings, so they are cast here; values from the phil handler are
  already typed and are returned unchanged.
  """
  key = _nsa2_normalize_param_key(key)
  if key.startswith('snum.NoSpherA2.'):
    header_key = _nsa2_header_key_from_param(key)
    if not _nsa2_should_persist_to_header(key):
      # Clean up legacy persisted values for phil-only/runtime keys.
      OV.ClearHeaderParam(header_key)
      return OV.GetParam(key, default)
    v = OV.GetHeaderParam(header_key, None)
    # Treat empty header strings as missing so we can still resolve live params.
    if v not in (None, ''):
      return _nsa2_cast_value(key, v)
    v = OV.GetParam(key, default)
    # Persist any actually used NoSpherA2 value into Header for this structure,
    # including defaults that were consumed through this accessor.
    if v not in (None, ''):
      OV.SetHeaderParam(header_key, v)
    else:
      OV.ClearHeaderParam(header_key)
    return _nsa2_cast_value(key, v)
  return OV.GetParam(key, default)

def nsa2_set_param(key, value):
  """Global setter exposed as spy.nsa2_set_param for HTML/UI controls."""
  key = _nsa2_normalize_param_key(key)
  if key.startswith('snum.NoSpherA2.'):
    header_key = _nsa2_header_key_from_param(key)
    if _nsa2_should_persist_to_header(key):
      if value in (None, ''):
        OV.ClearHeaderParam(header_key)
      else:
        OV.SetHeaderParam(header_key, value)
    else:
      # Ensure old persisted values are removed for phil-only/runtime keys.
      OV.ClearHeaderParam(header_key)
  OV.SetParam(key, value)

OV.registerFunction(nsa2_get_param)
OV.registerFunction(nsa2_set_param)
OV.registerFunction(nsa2_get_param, False, 'NoSpherA2')
OV.registerFunction(nsa2_set_param, False, 'NoSpherA2')

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

def LoadParams(scopes=None, extensions=None):
  if not scopes:
    scopes = ['olex2', 'user', 'custom', 'snum']
  elif str == type(scopes):
    scopes = scopes.split(",")

  # snum params
  try:
    phil_handler = olx.phil_handler
  except AttributeError:
    master_phil = phil_interface.parse(file_name="%s/params.phil" %OV.BaseDir())
    phil_handler = phil_interface.phil_handler(
      master_phil=master_phil,
      parse=phil_interface.parse)
    if extensions:
      for phf in extensions:
        fp  = os.path.join(OV.BaseDir(), phf)
        if not os.path.exists(fp):
          continue
        phil_handler.adopt_phil(phil_file=fp)
      phil_handler.rebuild_index()

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

def set_params_from_ires():
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
  # update max peaks/cycles in snum
  peaks = olx.Ins("plan")
  if peaks != "n/a":
    OV.SetParam('snum.refinement.max_peaks', peaks.split()[0])
  cycles = olx.Ins(olx.LSM())
  if cycles != "n/a":
    OV.SetParam('snum.refinement.max_cycles', cycles.split()[0])

def LoadStructureParams():
  import olexex
  ExternalPrgParameters.definedControls = [] # reset defined controls
  olx.current_mask = None
  olx.structure_params = {}
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
    set_params_from_ires()

  olexex.onSolutionProgramChange(solutionPrg, solutionMethod)
  olexex.onRefinementProgramChange(refinementPrg, refinementMethod)

OV.registerFunction(LoadStructureParams)

def SaveStructureParams(no_save='false'):
  if OV.FileName() != 'none' and no_save != 'true':
    structure_phil_file = os.path.join(OV.StrDir(), OV.ModelSrc()) + ".phil"
    olx.phil_handler.save_param_file(
      file_name=structure_phil_file, scope_name='snum', diff_only=True)
    auto_save_view = OV.GetParam('user.auto_save_view', False)
    if auto_save_view and olx.IsFileType('oxm') != 'true':
      oxvf = os.path.join(OV.StrDir(), OV.ModelSrc() + '.oxv')
      olex.m("save gview '%s'" %oxvf)
OV.registerMacro(SaveStructureParams, "no_save")

def OnStructureLoaded(previous):
  if olx.IsFileLoaded() == 'false' or not OV.StrDir():
    return
  auto_save_view = OV.GetParam('user.auto_save_view', False)

  OV.DelVar(olx.var_name_par_files)
  OV.DelVar(olx.var_name_param_N)

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
  if olx.FileExt().lower() in ('cif', 'oxm'):
    import History
    History.tree = None
  elif previous != OV.FileFull() or OV.IsClientMode():
    import History
    History.hist.loadHistory()
    OV.ResetMaskHKLWarning()
  if olx.IsFileType('ires') == 'true':
    OV.SetParam("snum.refinement.use_solvent_mask", olx.Ins("ABIN") != "n/a")
    call_listener('structure')
  elif olx.IsFileType('cif'):
    call_listener('structure')
    if olx.GetVar("cif_uses_masks", 'false') == 'true':
      OV.SetParam("snum.refinement.use_solvent_mask", True)

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

def SaveScopeParams(scope: str, file_name: str):
  olx.phil_handler.save_param_file(
    file_name=file_name, scope_name=scope, diff_only=True)
OV.registerFunction(SaveScopeParams)

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

