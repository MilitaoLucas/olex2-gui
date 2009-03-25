# variableFunctions.py

import os
try:
  import cPickle as pickle # faster C reimplementation of pickle module
except ImportError:
  import pickle # fall back on Python version
import olex
import userDictionaries
import ExternalPrgParameters

import CifInfo
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import variableDefinitions
from variables import *

initialisingVariables = False

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
    for varName, value in variables.items():
      if not OV.IsVar(varName):
        OV.SetVar(varName,value)
      if 'gui' in varName:
        vvdItems.gui.setdefault(varName)
        
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
  oldValue = OV.FindValue("snum_user_input_variables")
  if oldValue == 'None':
    newValue = variable
  elif variable in oldValue:
    newValue = oldValue
  else:
    newValue = oldValue + ";" + variable
  OV.SetVar("snum_user_input_variables", newValue)
  return ""
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
