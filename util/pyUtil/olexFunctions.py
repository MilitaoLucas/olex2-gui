# olexFunctions.py

import math
import os
import sys
import olx
import olex
import olex_core
import cProfile
from subprocess import *
import guiFunctions

HasGUI = olx.HasGUI() == 'true'
if HasGUI:
  inheritFunctions = guiFunctions.GuiFunctions
else:
  inheritFunctions = guiFunctions.NoGuiFunctions

class OlexFunctions(inheritFunctions):
  def __init__(self):
    if HasGUI:
      import olex_gui
      self.olex_gui = olex_gui

  def GetValue(self, control_name):
    retVal = olx.GetValue(control_name)
    return retVal

  def SetVar(self,variable,value):
    try:
      olex_core.SetVar(variable,value)
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be set with value %s" %(variable,value)
      sys.stderr.formatExceptionInfo()

  def SetParam(self,variable,value):
    try:
      if variable.startswith('gui'):
        handler = olx.gui_phil_handler
      else:
        handler = olx.phil_handler
      if value == '': value = None
      elif value in ('Auto','auto','None','none',None):
        value = value
      elif type(value) in (str,unicode) and "'" in value:
        value = "'%s'" %value.replace("'", "\\'")
      elif type(value) in (list, set):
        value = ' '.join("'%s'" %v.replace("'", "\\'") for v in value)
      else:
        value = unicode(value)
        value = value.encode('utf-8')
        value = "'%s'" %str(value)
      handler.update_single_param(str(variable), value)
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be set with value %s" %(variable,value)
      sys.stderr.formatExceptionInfo()

  def GetParam(self,variable):
    try:
      if variable.startswith('gui'):
        handler = olx.gui_phil_handler
      else:
        handler = olx.phil_handler
      retVal = handler.get_validated_param(variable)
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be found" %(variable)
      sys.stderr.formatExceptionInfo()
      retVal = ''
    return retVal

  def GetParam_as_string(self,variable):
    retVal = self.GetParam(variable)
    if retVal is None:
      return ''
    else:
      return str(retVal)

  def Params(self):
    if hasattr(olx, 'phil_handler'):
      return olx.phil_handler.get_python_object()
    else:
      return None

  def get_cif_item(self, key, default=None):
    if olx.cif_model is not None:
      data_name = self.FileName().replace(' ', '')
      if data_name not in olx.cif_model:
        import CifInfo
        CifInfo.ExtractCifInfo()
      return olx.cif_model[data_name].get(key, default)
    else:
      return default

  def set_cif_item(self, key, value):
    data_name = self.FileName().replace(' ', '')
    if olx.cif_model is not None:
      if isinstance(value, basestring) and value.strip() == '': value = '?'
      olx.cif_model[data_name][key] = value
    user_modified = self.GetParam('snum.metacif.user_modified')
    if user_modified is None: user_modified = []
    if key not in user_modified:
      user_modified.append(key)
    self.SetParam('snum.metacif.user_modified', user_modified)
    if key == '_diffrn_ambient_temperature':
      value = str(value)
      if value not in ('?', '.'):
        if 'K' not in value: value += ' K'
        olx.xf_exptl_Temperature(value)

  def GuiParams(self):
    if hasattr(olx, 'gui_phil_handler'):
      return olx.gui_phil_handler.get_python_object().gui
    else:
      return None

  def set_solution_program(self, program, method=None, scope='snum'):
    try:
      import olexex
      self.SetParam('%s.solution.program' %scope, program)
      olexex.onSolutionProgramChange(program, method,scope)
    except Exception, ex:
      print >> sys.stderr, "Program %s could not be set" %(program)
      sys.stderr.formatExceptionInfo()

  def set_refinement_program(self, program, method=None, scope='snum'):
    try:
      import olexex
      self.SetParam('%s.refinement.program' %scope, program)
      olexex.onRefinementProgramChange(program, method, scope)
    except Exception, ex:
      print >> sys.stderr, "Program %s could not be set" %(program)
      sys.stderr.formatExceptionInfo()

  def SetMaxCycles(self, max_cycles):
    try:
      import programSettings
      self.SetParam('snum.refinement.max_cycles', max_cycles)
      programSettings.onMaxCyclesChange(max_cycles)
    except Exception, ex:
      print >> sys.stderr, "Could not set max cycles to %s" %(max_cycles)
      sys.stderr.formatExceptionInfo()

  def SetMaxPeaks(self, max_peaks):
    try:
      int(max_peaks)
    except:
      return
    try:
      import programSettings
      old_value = self.GetParam('snum.refinement.max_peaks')
      if old_value is not None:
        max_peaks = int(max_peaks)
        if max_peaks > 0:
          max_peaks = int(math.copysign(max_peaks, old_value)) # keep sign of old value
      self.SetParam('snum.refinement.max_peaks', max_peaks)
      programSettings.onMaxPeaksChange(max_peaks)
    except Exception, ex:
      print >> sys.stderr, "Could not set max peaks to %s" %(max_peaks)
      sys.stderr.formatExceptionInfo()

  def FindValue(self,variable,default=u''):
    try:
      retVal = olex_core.FindValue(variable, default)
    except SystemError, ex:
      print >> sys.stderr, "System error with variable %s" %(variable)
      sys.stderr.formatExceptionInfo()
      retVal = ''
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be found" %(variable)
      sys.stderr.formatExceptionInfo()
      retVal = ''
    return retVal

  def IsFileType(self, fileType):
    return olx.IsFileType(fileType) == 'true'

  def FindObject(self,variable):
    try:
      retVal = olex_core.FindObject(variable)
    except Exception, ex:
      print >> sys.stderr, "An object for variable %s could not be found" %(variable)
      sys.stderr.formatExceptionInfo()
      retVal = None
    return retVal

  def IsVar(self,variable):
    try:
      retVal = olex_core.IsVar(variable)
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst trying to find variable %s" %(variable)
      sys.stderr.formatExceptionInfo()
      retVal = False
    return retVal

  def Translate(self,text):
    try:
      retStr = olex_core.Translate(text)
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst translating %s" %(text)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  def TranslatePhrase(self,text):
    try:
      retStr = olx.TranslatePhrase(text)
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst translating %s" %(text)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr


  def CurrentLanguageEncoding(self):
    try:
      retStr = olx.CurrentLanguageEncoding()
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst trying to determine the current language encoding"
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  def CifMerge(self, filepath):
    try:
      olx.CifMerge('"%s"' %filepath)
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst trying to find merge cif files"
      sys.stderr.formatExceptionInfo()

  def reset_file_in_OFS(self,fileName,txt=" ",copyToDisk = False):
    try:
      import OlexVFS
      OlexVFS.write_to_olex(fileName, txt)
      if copyToDisk:
        wFile = open("%s/%s" %(self.DataDir(),fileName),'w')
        wFile.write(txt)
        wFile.close()
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst trying to write to the VFS"
      sys.stderr.formatExceptionInfo()

  def write_to_olex(self,fileName,text,copyToDisk = False):
    text = text.encode('utf-8')
    try:
      import OlexVFS
      OlexVFS.write_to_olex(fileName, text)
      if copyToDisk:
        wFile = open("%s/%s" %(self.DataDir(),fileName),'w')
        wFile.write(text)
        wFile.close()
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst trying to write to the VFS"
      sys.stderr.formatExceptionInfo()

  def external_edit(self,filePath):
    try:
      olex.m("external_edit %s" %filePath)
    except:
      pass

  def Reap(self, path):
    if path.startswith("'") or path.startswith('"'):
      pass
    else:
      path = '"%s"'
    return olex.m('reap %s' %path)

  def AtReap(self, path):
    path = path.strip("'")
    path = path.strip('"')
    path = '"%s"' %path
    return olex.m('@reap %s' %path)

  def Reset(self):
    olx.Reset()

  def htmlUpdate(self):
    olex.m("UpdateHtml")

  def htmlReload(self):
    olex.m("html.Reload")

  def reloadStructureAtreap(self, path, file, fader=True):
    fader = self.FindValue('gui_use_fader')
    #print "AtReap %s/%s" %(path, file)
    try:
      if fader == 'true':
        olex.m(r"atreap_fader -b '%s'" %(r"%s/%s.res" %(path, file)))
      else:
        olex.m(r"atreap_no_fader -b '%s'" %(r"%s/%s.res" %(path, file)))

    except Exception, ex:
      print >> sys.stderr, "An error occured whilst trying to reload %s/%s" %(path, file)
      sys.stderr.formatExceptionInfo()

  def file_ChangeExt(self, path, newExt):
    try:
      newPath = olx.file_ChangeExt(path, newExt)
    except Exception, ex:
      print >> sys.stderr, "An error occured"
      sys.stderr.formatExceptionInfo()
    return self.standardizePath(newPath)

  def File(self):
    olx.File()

  def timer_wrap(self,f,*args, **kwds):
    try:
      import time
      t0 = time.time()
      retVal = f(*args, **kwds)
      t1 = time.time()
      print "Time take for the function %s is %s" %(f.__name__,(t1-t0))
    except Exception, ex:
      print >> sys.stderr, "An error occured running the function/macro %s" %(f.__name__)
      sys.stderr.formatExceptionInfo()
      retVal = ''
    return retVal

  def registerFunction(self,function,profiling=False):
    g = self.func_wrap(function)
    g.__name__ = function.__name__
    olex.registerFunction(g,profiling)

  def unregisterFunction(self,function,profiling=False):
    g = self.func_wrap(function)
    g.__name__ = function.__name__
    olex_core.unregisterFunction(g,profiling)

  def registerMacro(self,function,options,profiling=False):
    g = self.func_wrap(function)
    g.__name__ = function.__name__
    olex.registerMacro(g,options,profiling)

  def unregisterMacro(self,function,options,profiling=False):
    g = self.func_wrap(function)
    g.__name__ = function.__name__
    olex_core.unregisterMacro(g,options,profiling)

  def registerCallback(self,event,function,profiling=False):
    g = self.func_wrap(function)
    g.__name__ = function.__name__
    olex.registerCallback(event,function,profiling)
    #olex.registerCallback(event,function)

  def unregisterCallback(self,event,function,profiling=False):
    g = self.func_wrap(function)
    g.__name__ = function.__name__
    olex.unregisterCallback(event,function,profiling)
    #olex.registerCallback(event,function)

  def func_wrap(self,f):
    def func(*args, **kwds):
      try:
        retVal = f(*args, **kwds)
      except Exception, ex:
        print >> sys.stderr, "An error occured running the function/macro %s" %(f.__name__)
        sys.stderr.formatExceptionInfo()
        retVal = ''
      return retVal
    return func

  if False:  ## Change this to True to print out information about all the function calls
    def func_wrap(self,f):
      def func(*args, **kwds):
        #a = f
        print f
        print f.func_code
        print
        try:
          retVal = f(*args, **kwds)
        except Exception, ex:
          print >> sys.stderr, "An error occured running the function/macro %s" %(f.__name__)
          sys.stderr.formatExceptionInfo()
          retVal = ''
        #retVal = a.runcall(f, *args, **kwds)
        return retVal
      return func

  def IsPluginInstalled(self,plugin):
    return olx.IsPluginInstalled(plugin) == 'true'

  if olx.IsPluginInstalled('plugin-CProfile') == 'true':
    #import cProfile
    outFile = open('%s/profile.txt' %olx.DataDir(), 'w')
    outFile.close()

    def cprofile_wrap(self,f):
      import pstats
      def func(*args, **kwds):
        a = cProfile.Profile()
        try:
          retVal = a.runcall(f, *args, **kwds)
        except Exception, ex:
          print >> sys.stderr, "An error occured running the function/macro %s" %(f.__name__)
          sys.stderr.formatExceptionInfo()
          retVal = ''
        #retVal = cProfile.runctx('f(*args, **kwds)', {'f':f, 'args':args, 'kwds':kwds}, {}, filename="olex.prof")
        olex_output = sys.stdout
        outFile = open('%s/profile.txt' %self.DataDir(), 'a')
        sys.stdout = outFile
        pstats.Stats(a).sort_stats('time').print_stats()
        #a.print_stats(sort=1)
        #import pstats
        #p = pstats.Stats("olex.prof")
        #p.strip_dirs().sort_stats().print_stats(20)
        outFile.close()
        sys.stdout = olex_output
        return retVal
      return func

    func_wrap = cprofile_wrap

  def Lst(self,string):
    return olx.Lst(string)

  def standardizePath(self, path):
    return path.replace('\\','/')

  def standardizeListOfPaths(self, list_of_paths):
    retList = []
    for path in list_of_paths:
      retList.append(self.standardizePath(path))
    return retList

  def BaseDir(self):
    path = olx.BaseDir()
    return self.standardizePath(path)

  def DataDir(self):
    path = olx.DataDir()
    return self.standardizePath(path)

  def FileDrive(self,FileDrive=None):
    if FileDrive is not None:
      path = olx.FileDrive(FileDrive)
    else:
      path = olx.FileDrive()
    return self.standardizePath(path)

  def FileExt(self,FileExt=None):
    if FileExt is not None:
      path = olx.FileExt(FileExt)
    else:
      path = olx.FileExt()
    return self.standardizePath(path)

  def FileFull(self):
    path = olx.FileFull()
    return self.standardizePath(path)

  def FileName(self,FileName=None):
    if FileName is not None:
      path = olx.FileName(FileName)
    else:
      path = olx.FileName()
    return self.standardizePath(path)

  def FilePath(self,FilePath=None):
    if FilePath is not None:
      path = olx.FilePath(FilePath)
    else:
      path = olx.FilePath()
    return self.standardizePath(path)

  def olex_function(self, str):
    try:
      retval = olex.f(str)
      return retval
    except Exception, err:
      print "Printing error %s" %err
      return "Error"

  def HKLSrc(self, new_HKLSrc=None):
    if new_HKLSrc:
      return olx.HKLSrc(new_HKLSrc)
    else:
      path = olx.HKLSrc()
      return self.standardizePath(path)

  def StrDir(self):
    path = olx.StrDir()
    return self.standardizePath(path)

  def GetFormula(self):
    return olx.xf_GetFormula()

  def GetCellVolume(self):
    return olx.xf_au_GetCell()

  def AddIns(self, instruction):
    olx.AddIns(instruction)

  def DelIns(self, instruction):
    olx.DelIns(instruction)

  def HasGUI(self):
    return HasGUI

  def StoreParameter(self, var="", save=False):
    val = self.FindValue(var)
    if val:
      val = "'%s'" %val
      olex.m('storeparam %s %s %s' %(var, val, save))

  def GetCompilationInfo(self):
    return olx.GetCompilationInfo()

  def XfAuGetValue(self, var=""):
    try:
      val = olex.f("xf.au.Get%s()" %var)
    except:
      val = "n/a"
    return val

  def CopyVFSFile(self, copy_from, copy_to, isPersistent=0):
    f = olex.readImage(copy_from)
    assert f is not None
    olex.writeImage(copy_to, f, isPersistent)
    return ""

  def cmd(self, command):
    olex.m(command)
    return ""

  def GetRefinementModel(self,calculate_connectivity=False):
    return olex_core.GetRefinementModel(calculate_connectivity)

  def GetCurrentSelection(self,calculate_connectivity=False):
    res = olx.Info()
    return res

  def GetTag(self):
    try:
      rFile = open("%s/olex2.tag" %self.BaseDir(),'r')
      tag = rFile.readline().rstrip("\n")
      return tag
    except:
      tag = None

  def GetKeyname(self):
    import glob
    g = glob.glob(r"%s/*.%s" %(key_directory, "priv"))
    for item in g:
      keyname = item.split("\\")[-1:][0]
      return keyname.split(".")[0]

  def GetUserComputerName(self):
    import os
    return os.getenv('USERNAME'), os.getenv('COMPUTERNAME')

  def GetSVNVersion(self):
    path = "%s/version.txt" %self.BaseDir()
    try:
      rFile = open(path, 'r')
      line = rFile.read()
      version = int(line.split()[-1])
    except:
      version = 1
    return version

  def GetMacAddress(self):
    mac = self.GetParam('olex2.mac_address')
    retVal = []
    if mac == "":
      macs = olx.GetMAC('full')
      macs = macs.split(";")
      for mac in macs:
        if "virtual" in mac.lower():
          continue
        else:
          retVal.append(mac.split("=")[1])
    #mac=['XX-24-E8-00-37-08','00-24-E8-00-37-08']  testing with a bogous mac address
    else:
      retVal.append(mac)
    return retVal

  def GetComputername(self):
    return os.getenv('COMPUTERNAME')

  def GetUsername(self):
    return os.getenv('USERNAME')

  def setAllMainToolbarTabButtons(self):
    import olexex
    olexex.setAllMainToolbarTabButtons()


def GetParam(variable):
  # A wrapper for the function spy.GetParam() as exposed to the GUI.
  p = OV.GetParam_as_string(variable)
  try:
    p = p.decode('utf-8')
  except:
    pass
  return p

OV = OlexFunctions()
OV.registerFunction(GetParam)
OV.registerFunction(OV.SetParam)
OV.registerFunction(OV.set_cif_item)
OV.registerFunction(OV.get_cif_item)
OV.registerFunction(OV.CopyVFSFile)
