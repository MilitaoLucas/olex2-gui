# olexFunctions.py

import os
import sys
import olx
import olex
import olex_core
import OlexVFS

import cProfile

import guiFunctions

if olx.HasGUI() == 'true':
  inheritFunctions = guiFunctions.GuiFunctions
else:
  inheritFunctions = guiFunctions.NoGuiFunctions
  
class OlexFunctions(inheritFunctions):
  def __init__(self):
    self._HasGUI = olx.HasGUI()
    pass
    #self.demo_mode = self.FindValue('autochem_demo_mode',False)
    #self.no_input_mode = self.FindValue('autochem_no_input_mode',False)
 
  
  def SetVar(self,variable,value):
    try:
      #if value is not None:
      if value:
        olex_core.SetVar(variable,value)
      else:
        #print "Can't set variable to None"
        olex_core.SetVar(variable,value) # get rid of this line, just for testing
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be set with value %s" %(variable,value)
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
      
  def write_to_olex(self,fileName,text):
    try:
      OlexVFS.write_to_olex(fileName, text)
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
    
  def Reset(self):
    olx.Reset()
    
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
    if plugin == 'plugin-cctbx':
      if olx.IsPluginInstalled('plugin-cctbx') == 'true'\
         and not olx.IsPluginInstalled('plugin-cctbx-win') == 'true'\
         and not os.environ.has_key('OLEX2_CCTBX_DIR'):
        return False
      elif os.environ.has_key('OLEX2_CCTBX_DIR') and os.path.isdir(os.environ.get('OLEX2_CCTBX_DIR')):
        return True
      elif sys.platform.startswith('win'):
        plugin = 'plugin-cctbx-win'
        
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
  
  def XfAuGetValue(self, var=""):
    try:
      val = olex.f("xf.au.Get%s()" %var)
    except:
      val = "n/a"
    return val
  
  
OV = OlexFunctions()