# olexFunctions.py

import os
import sys
import olx
import olex
import olex_core
import OlexVFS
import cProfile
from subprocess import *
import guiFunctions

if olx.HasGUI() == 'true':
  inheritFunctions = guiFunctions.GuiFunctions
else:
  inheritFunctions = guiFunctions.NoGuiFunctions
  
class OlexFunctions(inheritFunctions):
  def __init__(self):
    self._HasGUI = olx.HasGUI()
    if self._HasGUI != "false":
      import olex_gui
      self.olex_gui = olex_gui

  def SetVar(self,variable,value):
    try:
      olex_core.SetVar(variable,value)
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be set with value %s" %(variable,value)
      sys.stderr.formatExceptionInfo()

  def SetParam(self,variable,value):
    try:
      if value in ('Auto','auto'):
        phil_string="%s=%s" %(variable, value)
      elif type(value) in (str,unicode) and "'" in value:
        phil_string = "%s='%s'" %(variable, value.replace("'", "\\'"))
      else:
        phil_string = "%s='%s'" %(variable, value)
      olx.phil_handler.update(phil_string=str(phil_string))
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be set with value %s" %(variable,value)
      sys.stderr.formatExceptionInfo()

  def SetParams(self, variable_value_pairs):
    try:
      phil_strings = []
      for variable, value in variable_value_pairs:
        if value in ('Auto','auto'):
          phil_strings.append("%s=%s" %(variable, value))
        elif type(value) in (str,unicode) and "'" in value:
          phil_strings.append("%s='%s'" %(variable, value.replace("'", "\\'")))
        else:
          phil_strings.append("%s='%s'" %(variable, value))
      #phil_string = '\n'.join(["%s='%s'" %(variable, value) for variable, value in variable_value_pairs])
      phil_string = '\n'.join(phil_strings)
      olx.phil_handler.update(phil_string=str(phil_string))
    except Exception, ex:
      print >> sys.stderr, "Variables could not be set with value"
      sys.stderr.formatExceptionInfo()

  def GetParam(self,variable):
    try:
      retVal = olx.phil_handler.get_validated_param(variable)
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be found" %(variable)
      sys.stderr.formatExceptionInfo()
      retVal = ''
    return retVal
  
  def GetParam_as_string(self,variable):
    return str(self.GetParam(variable))

  def Params(self):
    if hasattr(olx, 'phil_handler'):
      return olx.phil_handler.get_python_object()
    else:
      return None

  def SetSolutionProgram(self, program, method=None):
    try:
      import olexex
      self.SetParam('snum.solution.program', program)
      olexex.onSolutionProgramChange(program, method)
    except Exception, ex:
      print >> sys.stderr, "Program %s could not be set" %(program)
      sys.stderr.formatExceptionInfo()

  def SetRefinementProgram(self, program, method=None):
    try:
      import olexex
      self.SetParam('snum.refinement.program', program)
      olexex.onRefinementProgramChange(program, method)
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
      import programSettings
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
    isFileType = olx.IsFileType(fileType)
    if isFileType == 'true':
      return True
    else:
      return False
  
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
  
  def CifMerge(self,file):
    try:
      olx.CifMerge(file)
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst trying to find merge cif files"
      sys.stderr.formatExceptionInfo()
      
  def reset_file_in_OFS(self,fileName,txt=" ",copyToDisk = False):
    try:
      OlexVFS.write_to_olex(fileName, txt)
      if copyToDisk:
        wFile = open("%s/%s" %(self.DataDir(),fileName),'w')
        wFile.write(txt)
        wFile.close()
    except Exception, ex:
      print >> sys.stderr, "An error occured whilst trying to write to the VFS"
      sys.stderr.formatExceptionInfo()
      
  def write_to_olex(self,fileName,text,copyToDisk = False):
    try:
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
    return newPath
  
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
  
  def FileDrive(self,FileFull=''):
    path = olx.FileDrive(FileFull)
    return self.standardizePath(path)

  def FileExt(self,FileFull=''):
    path = olx.FileExt(FileFull)
    return self.standardizePath(path)  
  
  def FileFull(self):
    path = olx.FileFull()
    return self.standardizePath(path)
  
  def FileName(self,FileFull=''):
    path = olx.FileName(FileFull)
    return self.standardizePath(path)
  
  def FilePath(self,FileFull=''):
    path = olx.FilePath(FileFull)
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
    return self._HasGUI == 'true'
  
  def StoreParameter(self, var="", save=False):
    val = self.FindValue(var)
    if val:
      val = "'%s'" %val
      olex.m('storeparam %s %s %s' %(var, val, save))
    
  def GetCompilationInfo(self):
    return olx.GetCompilationInfo()
  
  def GetHtmlPanelwidth(self):
    return olx.HtmlPanelWidth()

  def XfAuGetValue(self, var=""):
    try:
      val = olex.f("xf.au.Get%s()" %var)
    except:
      val = "n/a"
    return val

  def CopyVFSFile(self, copy_from, copy_to, isPersistent=0):
    f = olex.readImage(copy_from)
    #assert f is not None
    olex.writeImage(copy_to, f, isPersistent)
    return ""

  def SetImage(self, zimg_name, image_file):
    if self.olex_gui.IsControl(zimg_name):
      olx.html_SetImage(zimg_name,image_file)
    else:
      try:
        olx.html_SetImage(zimg_name,image_file)
      except:
        print "Failure!"

  def cmd(self, command):
    olex.m(command)
    return ""
  
  def setItemstate(self, txt):
    olex.m("itemstate %s" %txt)

  def GetRefinementModel(self,calculate_connectivity=False):
    return olex_core.GetRefinementModel(calculate_connectivity)
  
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
    if mac == "":
      mac = olx.GetMAC()
      mac = mac.split(";")
      mac = mac[0]
      self.SetParam('olex2.mac_address',mac)
    return mac   
  
  def GetComputername(self):
    return os.getenv('COMPUTERNAME')
  
  def GetUsername(self):
    return os.getenv('USERNAME')

  def Refresh(self):
    olx.Refresh()
  
  
OV = OlexFunctions()