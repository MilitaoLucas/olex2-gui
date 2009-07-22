# variableFunctions.py

import os
try:
  import cPickle as pickle # faster C reimplementation of pickle module
except ImportError:
  import pickle # fall back on Python version
import olex
import olx
import userDictionaries
import ExternalPrgParameters

import CifInfo
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import variableDefinitions
from variables import *

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
    
class userVVD:
  def __init__(self):
    self.alert = {}
    self.refinement = {}
    self.solution = {}
    self.auto = {}
    
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
    global user_vvdItems
    user_vvdItems = userVVD()
    
    variables = {
      'FileName':'none',
      'FilePath':'none',
    }
    if OV.HasGUI():
      variables.update(variableDefinitions.guiVariables())
      variables.update(variableDefinitions.olex2Variables())
    for varName, value in variables.items():
      if not OV.IsVar(varName):
        OV.SetVar(varName,value)
      if 'gui' in varName:
        vvdItems.gui.setdefault(varName)
      if 'olex2' in varName:
        vvdItems.olex2.setdefault(varName)
        
    #if OV.IsVar('startup'):
      #olex.m('reap getVar(startup)')
        
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
      
    samples = os.listdir(svn_samples_directory)
    for sample in samples:
      if not os.path.exists('%s/%s' %(user_samples_directory,sample)):
        try:
          from shutil import copytree
          dirname1 = '%s/%s' %(svn_samples_directory,sample)
          dirname2 = '%s/%s' %(user_samples_directory,sample)
          copytree(dirname1,dirname2)
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
    variables = {
      'rename':Variable(False),
      'FileName':OV.FileName(),
      'FilePath':OV.FilePath(),
      'stop_current_process':Variable(False),
    }
    
    variables.update(variableDefinitions.snumVariables())
    variables.update(variableDefinitions.userVariables())
    
    for varName, value in variables.items():
      OV.SetVar(varName,value)
      if varName[0:4] == 'user':
        if 'auto' in varName:
          user_vvdItems.auto.setdefault(varName)
        elif 'refinement' in varName:
          user_vvdItems.refinement.setdefault(varName)
        elif 'solution' in varName:
          user_vvdItems.solution.setdefault(varName)
        elif 'alert' in varName:
          user_vvdItems.alert.setdefault(varName)
          
      elif '_auto_' in varName:
        vvdItems.auto.setdefault(varName)
      elif 'refinement' in varName:
        vvdItems.refinement.setdefault(varName)
      elif 'dimas' in varName:
        vvdItems.dimas.setdefault(varName)
      elif 'metacif' in varName:
        vvdItems.metacif.setdefault(varName)
      elif 'history' in varName:
        vvdItems.history.setdefault(varName)
      elif 'report' in varName:
        vvdItems.report.setdefault(varName)
      elif 'solution' in varName:
        vvdItems.solution.setdefault(varName)
      elif 'olex2' in varName:
        vvdItems.olex2.setdefault(varName)
        
    if not OV.IsVar('snum_cctbx_map_type'):
      OV.SetVar('snum_cctbx_map_type','--')
    if not OV.IsVar('snum_cctbx_map_resolution'):
      OV.SetVar('snum_cctbx_map_resolution','0.2') 
      
    CifInfo.metacifFiles = CifInfo.MetacifFiles()
    
    defaultSolutionPrg, defaultSolutionMethod = getDefaultPrgMethod('Solution')
    defaultRefinementPrg, defaultRefinementMethod = getDefaultPrgMethod('Refinement')
    
    OV.SetVar('snum_solution_program', defaultSolutionPrg)
    OV.SetVar('snum_solution_method', defaultSolutionMethod)
    OV.SetVar('snum_refinement_program', defaultRefinementPrg)
    OV.SetVar('snum_refinement_method', defaultRefinementMethod)
    
  initialisingVariables = False
    
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

def updateUserVVD(parameter='auto'):
  global vvdItems
  if parameter == 'user':
    vvd = getVVD('refinement')
    vvd.update(getVVD('solution'))
  #elif parameter == 'auto':
    #vvd = getVVD('auto')
  elif parameter == ('alert'):
    vvd = {}
  else:
    vvd = getVVD(parameter)
  userVVD = getVVD('user_%s' %parameter)
  for item in userVVD.keys():
    snum_name = item.replace('user','snum')
    if vvd.has_key(snum_name):
      userVVD[item] = vvd[snum_name]
      
  for item,value in userVVD.items():
    OV.SetVar(item,value)
  
  userDefaultVVDPath = '%s/vvd_default.pickle' %OV.DataDir()
  retVVD = unPickle(userDefaultVVDPath)
  if not retVVD:
    retVVD = {}
  retVVD.update(userVVD)
  return retVVD

def save_user_parameters(parameters='auto'):
  result = pickleVVD('user_%s' %parameters)
  if result != "Failed":
    print "The current %s settings have been saved for this user" %parameters
  return result
OV.registerFunction(save_user_parameters)

def Pickle(item,path):
  if "none/.olex" in path:
    return
  pFile = open(path, 'w')
  pickle.dump(item, pFile)
  pFile.close()
  #p = pickle.dumps(item)
  #pFile = open(path, 'w')
  #pFile.write(p)
  #pFile.close()
  
def unPickle(path):
  try:
    pFile = open(path, 'r')
    data = pickle.load(pFile)
    pFile.close()
  except IOError:
    data = None
  return data
  
def pickleVVD(vvd, path=None):
  if OV.FileName() != 'none':
    if type(vvd) == dict and path is not None:
      pass # save given vvd in the given path
    #elif vvd in ('user', 'user_refinement', 'user_solution', 'alert', 'auto'):
    elif 'user' in vvd:
      vvd = vvd.split('_')[-1]
      try:
        vvd = updateUserVVD(vvd)
      except AttributeError:
        return "Failed"
      path = '%s/vvd_default.pickle' %OV.DataDir()
    elif vvd == 'structure':
      vvd = getVVD('structure')
      path = r"%s/.olex/%s.vvd" %(OV.FindValue('FilePath'),OV.FindValue('FileName'))
    else:
      vvdName = vvd
      try:
        vvd = getVVD(vvd)
      except AttributeError, error_message:
        return "Failed"
      if not path:
        path = r"%s/.olex/%s.vvd" %(OV.FindValue('FilePath'),vvdName)
      #path = r"%s/.olex/%s.vvd" %(OV.FindValue('FilePath'),OV.FindValue('FileName'))
    Pickle(vvd,path)
  return "Done"
OV.registerFunction(pickleVVD)

def unpickle_single_VVD(path):
  dictionary = unPickle(path)
  for var, value in dictionary.items():
    OV.SetVar(var, value)
    
def UnpickleVVD():
  """Loads the saved values to the VVD and sets the values of all variables in Olex2"""
  pFile = None
  structureVVDPath = r"%s/.olex/%s.vvd" %(OV.FilePath(),OV.FileName())
  # Changed pickle file name from 'vvd.pickle' to 'OV.FileName().vvd'
  oldPicklePath = r"%s/.olex/vvd.pickle" %OV.FilePath()
  userDefaultVVDPath = '%s/vvd_default.pickle' %OV.DataDir()
  
  vvd = {}
  # Set default values for all variables
  for item in ('refinement','dimas','metacif','history','solution','report','workflow'):
    dict = getattr(vvdItems,item)
    for var, value in dict.items():
      vvd[var] = value
      
  if os.path.exists(userDefaultVVDPath):  # Load user-level default values
    snumDefaultVVD = {}
    userDefaultFile = open(userDefaultVVDPath)
    userDefaultVVD = pickle.load(userDefaultFile)
    if userDefaultVVD.has_key('refinement'):
      userDefaultVVD = convertVVD(userDefaultVVD,'user')
    for item, value in userDefaultVVD.items():
      if 'alert' in item:
        snumDefaultVVD.setdefault(item, value)
      else:
        snumDefaultVVD.setdefault(item.replace('user','snum'), value)
    vvd.update(snumDefaultVVD)
    
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
    structureVVD = {}
    
  if structureVVD.has_key('refinement'):  # Convert old-format VVD
    structureVVD = convertVVD(structureVVD,'structure')
    
  vvd.update(structureVVD)
  
  ref_prg = vvd.pop('snum_refinement_program')
  ref_method = vvd.pop('snum_refinement_method')
  sol_prg = vvd.pop('snum_solution_program')
  sol_method = vvd.pop('snum_solution_method')
  max_cycles = vvd.pop('snum_refinement_max_cycles')
  max_peaks = vvd.pop('snum_refinement_max_peaks')
  
  for variable, value in vvd.items():  # Set values of all variables in Olex2
    try:
      if value != None:
        OV.SetVar(variable,value)
    except TypeError, message:
      continue
    
  if ref_prg: OV.SetVar('snum_refinement_program',ref_prg)
  if sol_prg: OV.SetVar('snum_solution_program',sol_prg)
  #if ref_method: OV.SetVar('snum_refinement_method',ref_method)
  #if sol_method: OV.SetVar('snum_solution_method',sol_method)
  
  return ""
OV.registerFunction(UnpickleVVD)

def convertVVD(vvd,whichVVD):
  oldVVD = vvd
  for dictionary in oldVVD:
    for item in oldVVD[dictionary]:
      try:
        value = oldVVD[dictionary][item]
        if value != None:
          OV.SetVar('%s' %item, value)
      except:
        continue
      
  newVVD = getVVD(whichVVD)
  if whichVVD == 'structure':
    pickleVVD(newVVD)
  elif whichVVD == 'user':
    pickleVVD('user')
  return newVVD

def AddVariableToUserInputList(variable):
  """Adds the name of the variable to a list of user-edited variables."""
  variable_list = OV.GetParam("snum.metacif.user_input_variables")
  variable = str(variable) # get rid of unicode
  if variable_list is None:
    variable_list = variable
    OV.SetParam("snum.metacif.user_input_variables", variable_list)
  elif variable_list is not None and variable not in variable_list:
    variable_list.append(variable)
    variable_list = ' '.join('"%s"' %var for var in variable_list)
    OV.SetParam("snum.metacif.user_input_variables", variable_list)
OV.registerFunction(AddVariableToUserInputList)

def SwitchAllAlertsOn():
  alerts = ['user_alert_delete_history',
            'user_alert_overwrite_history']
  for item in alerts:
    OV.SetVar(item,'Y')
  return ''
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
  if structureVVD.has_key('refinement'):  # Convert old-format VVD
    structureVVD = convertVVD(structureVVD,'structure')

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
  user_phil_file = "%s/params.phil" %OV.DataDir()
  if os.path.isfile(user_phil_file):
    return iotbx.phil.parse(file_name=user_phil_file)
  else:
    return None

def LoadParams():
  master_phil = iotbx.phil.parse(
    file_name="%s/params.phil" %OV.BaseDir())
  solutionPrg, solutionMethod = getDefaultPrgMethod('Solution')
  refinementPrg, refinementMethod = getDefaultPrgMethod('Refinement')
  programs_phil =iotbx.phil.parse("""
snum {
  refinement.program = "%s"
  refinement.method = "%s"
  solution.program = "%s"
  solution.method = "%s"
}
""" %(refinementPrg, refinementMethod, solutionPrg, solutionMethod))
  sources = [programs_phil]
  user_phil = get_user_phil()
  if user_phil is not None:
    sources.append(user_phil)
  working_phil = master_phil.fetch(sources=sources)
  phil_handler = phil_interface.phil_handler(master_phil=working_phil)
  olx.phil_handler = phil_handler
OV.registerFunction(LoadParams)

def LoadStructureParams():
  olx.phil_handler = olx.phil_handler.copy()
  snum_phil = """
snum {
  report.title = "%s"
  report.image = "%s/screenshot.png"
  }
""" %(OV.FileName(), OV.FilePath())
  olx.phil_handler.update(snum_phil)
  structure_phil_path = "%s/.olex/%s.phil" %(OV.FilePath(), OV.FileName())
  if os.path.isfile(structure_phil_path):
    structure_phil_file = open(structure_phil_path, 'r')
    structure_phil = structure_phil_file.read()
    structure_phil_file.close()
  else:
    # check if old-style vvd file is present
    structure_phil = VVD_to_phil()
    if structure_phil is None:
      return
  olx.phil_handler.update(structure_phil)
  #olx.phil_handler.get_phil_help_string('snum.refinement.max_cycles')
OV.registerFunction(LoadStructureParams)

def SaveStructureParams():
  if OV.FileName() != 'none':
    structure_phil_file = "%s/.olex/%s.phil" %(OV.FilePath(), OV.FileName())
    olx.phil_handler.save_param_file(file_name=structure_phil_file, diff_only=True)
OV.registerFunction(SaveStructureParams)

OV.registerFunction(OV.GetParam)
OV.registerFunction(OV.SetParam)
