# variableFunctions.py

import os
import shutil
import sys
try:
  import cPickle as pickle # faster C reimplementation of pickle module
except ImportError:
  import pickle # fall back on Python version
import olex
import olx
import userDictionaries
import ExternalPrgParameters
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import variableDefinitions
import olexex
from cStringIO import StringIO

initialisingVariables = False

import phil_interface

import iotbx.phil
import libtbx.phil.command_line

class VVD:
  def __init__(self):
    self.user = {}
    self.gui = {}
    self.history = {}
    self.refinement = {}
    self.metacif = {}
    self.dimas = {}
    self.report = {}
    self.solution = {}
    self.auto = {}
    self.workflow = {}
    self.olex2 = {}

def InitialiseVariables(arg):
  """Called on startup by macro.
  
  Initialises all the variables and objects needed in olex.
  Should only be called once, on startup.
  """
  
  global initialisingVariables
  initialisingVariables = True
  
  if arg == 'startup':
    global vvdItems
    vvdItems = VVD()
    
    variables = {
      'FileName':'none',
      'FilePath':'none',
    }
    if OV.HasGUI():
      variables.update(variableDefinitions.guiVariables())
    for varName, value in variables.items():
      if not OV.IsVar(varName):
        OV.SetVar(varName,value)
      if 'gui' in varName:
        vvdItems.gui.setdefault(varName)
      if 'olex2' in varName:
        vvdItems.olex2.setdefault(varName)
        
    OV.SetVar('cbtn_solve_on','false')
    OV.SetVar('cbtn_refine_on','false')
    OV.SetVar('cbtn_report_on','false')
    
    ## copy sample directory to datadir
    svn_samples_directory = '%s/sample_data' %OV.BaseDir()
    user_samples_directory = '%s/samples' %OV.DataDir()
    if os.path.exists(user_samples_directory):
      OV.SetVar('sample_dir',user_samples_directory)
    else: 
      os.mkdir(user_samples_directory)

    if sys.version_info[0] >= 2 and sys.version_info[1] >=6:
      ignore_patterns = shutil.ignore_patterns('*.svn')
    else:
      ignore_patterns = None # back compatiblity for python < 2.6

    samples = os.listdir(svn_samples_directory)
    for sample in samples:
      if sample == '.svn': continue
      if not os.path.exists('%s/%s' %(user_samples_directory,sample)):
        try:
          dirname1 = '%s/%s' %(svn_samples_directory,sample)
          dirname2 = '%s/%s' %(user_samples_directory,sample)
          if ignore_patterns is not None:
            shutil.copytree(dirname1, dirname2, ignore=ignore_patterns)
          else:
            shutil.copytree(dirname1, dirname2)
          OV.SetVar('sample_dir','%s/samples' %OV.DataDir())
        except:
          pass
      else:
        continue
       
    ## initialise userDictionaries objects
    if not userDictionaries.people:
      userDictionaries.People()
    if not userDictionaries.localList:
      userDictionaries.LocalList()
      
  elif arg == 'reap':
    """List of variables (usually structure-specific variables) to be initialised on reap."""
    
    ExternalPrgParameters.definedControls = [] # reset defined controls
    
  return ""
OV.registerFunction(InitialiseVariables)

def getOlex2VersionInfo():
  txt = 'Olex2, Durham University (compiled %s)' %OV.GetCompilationInfo()
  return txt

def getDefaultPrgMethod(prgType):
  import olexex
  defaultPrg = '?'
  defaultMethod = '?'
  if prgType == 'Refinement':
    availablePrgs = olexex.getRefinementPrgs().split(';')
    prgList = ('XL', 'ShelXL', 'XH', 'ShelXH', 'smtbx-refine')
    prgDict = olexex.RPD
  elif prgType == 'Solution':
    availablePrgs = olexex.getSolutionPrgs().split(';')
    prgList = ('XS', 'ShelXS', 'smtbx-solve', 'XM', 'ShelXD')
    prgDict = olexex.SPD
  for prg in prgList:
    if prg in availablePrgs:
      defaultPrg = prg
      program = prgDict.programs[prg]
      defaultMethod = olexex.sortDefaultMethod(program)
      break
  return defaultPrg, defaultMethod

def getVVD(what_do_i_want='structure'):
  """ if what_do_i_want is blank, will return the whole vvd """
  vvd = {}
  dictionary = {}
  if what_do_i_want == 'structure':
    listItems = ['refinement','dimas','metacif','history','report','solution','auto']
  elif what_do_i_want == 'user':
    listItems = ['refinement','solution']
  #elif what_do_i_want == 'auto' or what_do_i_want == 'snum_auto':
    #listItems = [what_do_i_want]
  elif what_do_i_want == 'alert':
    listItems = ['alert']
  else:
    listItems = [what_do_i_want]
    
  if listItems:
    for item in listItems:
      #if what_do_i_want in ('user','auto','alert'):
      if 'user' in what_do_i_want:
        dictionary = getattr(user_vvdItems,item.split('_')[-1])
      else:
        dictionary = getattr(vvdItems,item)
      for item in dictionary.keys():
        try:
          value = OV.FindValue(item)
          vvd[item] = value
        except:
          continue
  else:
    dictionary = getattr(vvdItems,what_do_i_want)
    for item in dictionary.keys():
      try:
        value = OV.FindValue(item)
        vvd[item] = value
      except:
        continue
  return vvd

def Pickle(item,path):
  if "none/.olex" in path:
    return
  pFile = open(path, 'w')
  pickle.dump(item, pFile)
  pFile.close()

def unPickle(path):
  try:
    pFile = open(path, 'r')
    data = pickle.load(pFile)
    pFile.close()
  except IOError:
    data = None
  return data

def AddVariableToUserInputList(variable):
  """Adds the name of the variable to a list of user-edited variables."""
  variable_list = OV.GetParam("snum.metacif.user_input_variables")
  variable = str(variable) # get rid of unicode
  if variable_list is None:
    variable_list = variable
    OV.SetParam("snum.metacif.user_input_variables", variable_list)
  elif variable_list is not None and variable not in variable_list:
    variable_list += ';%s' %variable
    OV.SetParam("snum.metacif.user_input_variables", variable_list)
OV.registerFunction(AddVariableToUserInputList)

def SwitchAllAlertsOn():
  alerts = ['user.alert_delete_history',
            'user.alert_overwrite_history']
  for item in alerts:
    OV.SetParam(item,'Y')
  SaveUserParams()
OV.registerFunction(SwitchAllAlertsOn)

def StoreParameters(type=""):
  if type:
    d = getVVD(type)
    for var, value in d.items():
      olex.m('storeparam %s %s' %(var, value))
  else:
    print "Please provide the type of variable you want to save (e.g. gui, snum)"
OV.registerFunction(StoreParameters)

def VVD_to_phil():
  phil_strings = []
  structureVVDPath = r"%s/.olex/%s.vvd" %(OV.FilePath(),OV.FileName())
  # Changed pickle file name from 'vvd.pickle' to 'OV.FileName().vvd'
  oldPicklePath = r"%s/.olex/vvd.pickle" %OV.FilePath()
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
  if structureVVD.has_key('refinement'):
    return

  for variable, value in structureVVD.items():  # Set values of all variables in Olex2
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

def get_user_phil():
  user_phil_file = "%s/user.phil" %OV.DataDir()
  if os.path.isfile(user_phil_file):
    return user_phil_file
  else:
    return None

def LoadParams():
  master_phil = phil_interface.parse(file_name="%s/params.phil" %OV.BaseDir())
  phil_handler = phil_interface.phil_handler(
    master_phil=master_phil,
    parse=phil_interface.parse)
  user_phil = get_user_phil()
  if user_phil:
    phil_handler.update(phil_file=user_phil)
  olx.phil_handler = phil_handler
OV.registerFunction(LoadParams)

def LoadStructureParams():
  ExternalPrgParameters.definedControls = [] # reset defined controls
  olx.phil_handler.reset_scope('snum', rebuild_index=False)
  solutionPrg, solutionMethod = getDefaultPrgMethod('Solution')
  refinementPrg, refinementMethod = getDefaultPrgMethod('Refinement')
  snum_phil = """
snum {
  refinement.program = "%s"
  refinement.method = "%s"
  solution.program = "%s"
  solution.method = "%s"
  report.title = "%s"
  image.ps.name = "%s"
  image.bitmap.name = "%s"
  report.image = "%s/screenshot.png"
  }
""" %(refinementPrg, refinementMethod, solutionPrg, solutionMethod, 
      OV.FileName(), OV.FileName(), OV.FileName(), OV.FilePath())
  olx.phil_handler.update(phil_string=snum_phil)
  structure_phil_path = "%s/.olex/%s.phil" %(OV.FilePath(), OV.FileName())
  if os.path.isfile(structure_phil_path):
    structure_phil_file = open(structure_phil_path, 'r')
    structure_phil = structure_phil_file.read()
    structure_phil_file.close()
    if """\"[\" \"[',\"""" in structure_phil:
      return # to get around any problems caused by bug that was fixed in r2585
  else:
    # check if old-style vvd file is present
    structure_phil = VVD_to_phil()
  if structure_phil is not None:
    olx.phil_handler.update(phil_string=structure_phil)
  solutionPrg = olx.phil_handler.get_validated_param('snum.solution.program')
  solutionMethod = olx.phil_handler.get_validated_param('snum.solution.method')
  refinementPrg = olx.phil_handler.get_validated_param('snum.refinement.program')
  refinementMethod = olx.phil_handler.get_validated_param('snum.refinement.method')
  if OV.IsFileType('ires'):
    if solutionMethod == 'Direct Methods' and olx.Ins('PATT') != 'n/a':
      solutionMethod = 'Patterson Method' # work-around for bug #48
    if refinementMethod == 'Least Squares' and olx.LSM() == 'CGLS':
      refinementMethod = 'CGLS' # work-around for bug #26
  olexex.onSolutionProgramChange(solutionPrg, solutionMethod)
  olexex.onRefinementProgramChange(refinementPrg, refinementMethod)
OV.registerFunction(LoadStructureParams)

def SaveStructureParams():
  if OV.FileName() != 'none':
    structure_phil_file = "%s/.olex/%s.phil" %(OV.FilePath(), OV.FileName())
    olx.phil_handler.save_param_file(
      file_name=structure_phil_file, scope_name='snum', diff_only=True)
OV.registerFunction(SaveStructureParams)

def SaveUserParams():
  user_phil_file = "%s/user.phil" %(OV.DataDir())
  olx.phil_handler.save_param_file(
    file_name=user_phil_file, scope_name='user', diff_only=True)
OV.registerFunction(SaveUserParams)

def EditParams(scope_name="", expert_level=0, attributes_level=0):
  try:
    output_phil = olx.phil_handler.get_scope_by_name(scope_name)
    original_name = output_phil.name
    output_phil.name = scope_name
  except KeyError:
    print '"%s" is not a valid scope name' %scope_name
  else:
    s = StringIO()
    output_phil.show(out=s, expert_level=expert_level, attributes_level=attributes_level)
    input_phil_string = OV.GetUserInput(0, "Edit parameters", s.getvalue())
    if input_phil_string is not None and not input_phil_string == s.getvalue():
      olx.phil_handler.update(phil_string=str(input_phil_string))
    else:
      # need to set scope name back to original since scope isn't rebuilt
      output_phil.name = original_name
OV.registerFunction(EditParams)

def ShowParams(expert_level=0, attributes_level=0):
  olx.phil_handler.working_phil.show(
    expert_level=int(expert_level), attributes_level=int(attributes_level))
OV.registerFunction(ShowParams)
