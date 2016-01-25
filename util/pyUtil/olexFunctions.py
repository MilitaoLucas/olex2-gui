# olexFunctions.py

import math
import os
import sys
import olx
import olex
import olex_core
import OlexVFS
import cProfile
from subprocess import *
import guiFunctions

import socket
import pickle

import time

try:
  olx.olex2_tag
except:
  olx.olex2_tag = None
  olx.olex2_svn_version = None


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
    retVal = olx.html.GetValue(control_name)
    return retVal

  def SetVar(self,variable,value):
    try:
      olex_core.SetVar(variable,value)
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be set with value %s" %(variable,value)
      sys.stderr.formatExceptionInfo()

  def _replace_object(self, scope, object):
    for i, tobj in enumerate(scope.objects):
      if tobj.name == object.name:
        scope.objects[i] = object
        return

  def SetParam(self,variable,value):
    '''
    Set an olex parameter. Date will converted to d-m-Y
    '''
    try:
      if variable.startswith('gui'):
        handler = olx.gui_phil_handler
      else:
        handler = olx.phil_handler
      if value == '': value = None
      elif value in ('Auto','auto','None','none',None):
        pass
      elif isinstance(value, basestring):
        value = "'%s'" %unicode(value).replace("'", "\\'").replace('$', '\\$').encode('utf-8')
      elif type(value) in (list, set):
        value = ' '.join("'%s'" %v.replace("'", "\\'") for v in value)
      elif "date_" in variable:
        try:
          if type(value) is unicode:
            pattern = '%d-%m-%Y'
            value = int(time.mktime(time.strptime(value, pattern)))
        except:
          pass
      else:
        value = "'%s'"  %unicode(value).encode('utf-8')
      handler.update_single_param(str(variable), value)
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be set with value %s" %(variable,value)
      sys.stderr.formatExceptionInfo()

  def GetParam(self,variable, default=None, get_list=False):
    retVal = default
    try:
      if variable.startswith('gui'):
        if not HasGUI:
          return default
        handler = olx.gui_phil_handler
      else:
        handler = olx.phil_handler

      retVal = handler.get_validated_param(variable)

      #if not get_list:
        #retVal = handler.get_validated_param(variable)
      #else:
        #retVal = handler.get_values_by_name(variable)

      if retVal is not None:
        if isinstance(retVal, str):
          retVal = retVal.decode('utf-8').replace('\\$', '$')
        elif isinstance(retVal, unicode):
          retVal = retVal.replace('\\$', '$')
      else:
        retVal = default
    except Exception, ex:
      print >> sys.stderr, "Variable %s could not be found" %(variable)
      sys.stderr.formatExceptionInfo()
    return retVal

  def HtmlGetValue(self, control, default=None):
    '''
    returns the value of a html control.
    returns provided default value if control is empty.

    :param control: html control element
    :param default: returned value if olx.html.GetValue() returns false
    '''
    val = olx.html.GetValue(control)
    retVal = default
    if val:
      retVal = val
    return retVal

  def set_bond_thicknes(self, control, default=100):
    '''
    sets the molecule bond thickness. Invalid values e.g. too small, too large or
    containing characters are reset to default.
    The bond radius slider SLIDE_BRAD is set to the value simultaneously.
    '''
    value = olx.html.GetValue(control)
    default = float(default)
    if value:
      try:
        value = int(value)
      except ValueError:
        print('This is not a valid bond radius value.')
        value = default
      value = float(value)
      if value > 600:
        value = default
        olx.html.SetValue('BRADValue', int(value))
      if value < 10 or value == 0:
        value = 10.0
      OV.SetParam('user.bonds.thickness', value)
      olx.html.SetValue('SLIDE_BRAD', value/10)
      OV.cmd('brad {}'.format(value/100))
    else:
      return


  def GetParam_as_string(self,variable, default=None):
    retVal = self.GetParam(variable, default)
    if retVal is None:
      return ''
    else:
      return "%s" %retVal

  def Params(self):
    if hasattr(olx, 'phil_handler'):
      return olx.phil_handler.get_python_object()
    else:
      return None

  def get_txt_from_vfs(self, item):
    _ = item
    return OlexVFS.read_from_olex(_)

  def get_cif_item(self, key, default="", output_format=False):
    if olx.cif_model is not None:
      data_name = self.ModelSrc().replace(' ', '')
      if data_name not in olx.cif_model:
        import CifInfo
        CifInfo.ExtractCifInfo()
      tem = olx.cif_model[data_name].get(key, default)
      if tem is None: return default
      retVal = default
      if type(tem) == str:
        if output_format == 'html':
          tem = tem.replace(';\n','')
          tem = tem.replace('\n;','')
          tem = tem.replace('\n','<br>')
        if output_format == 'gui':
          tem = tem.replace(';\n','')
          tem = tem.replace('\n;','')
          tem = tem.replace('\n\n','')
          tem = tem.rstrip('\n')
          tem = tem.lstrip('\n')
        return tem
      else:
        try:
          return ", ".join([bit for bit in tem])
        except Exception, ex:
          print ex
      return retVal
    else:
      return default

  def set_cif_item(self, key, value):
    if olx.cif_model is not None:
      data_name = self.ModelSrc().replace(' ', '')
      data_block = olx.cif_model[data_name]
      if isinstance(value, basestring):
        value = value.strip()
        if value == '': value = '?'
        data_block[key] = value
      else:
        data_block[key] = value
    user_modified = self.GetParam('snum.metacif.user_modified')
    if user_modified is None: user_modified = []
    if key not in user_modified:
      user_modified.append(key)
      self.SetParam('snum.metacif.user_modified', user_modified)
    if key == '_diffrn_ambient_temperature':
      value = str(value)
      if value not in ('?', '.'):
        if 'K' not in value: value += ' K'
        olx.xf.exptl.Temperature(value)


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

  def GetOSF(self):
    try:
      a = float(olx.xf.rm.OSF())
      if a == 0: #value previously unset
        return None
      return a*a
    except:
      return None

  def SetOSF(self, v):
    try:
      olx.xf.rm.OSF(math.sqrt(v))
      return True
    except:
      return False

  def GetFVar(self, i):
    try:
      return float(olx.xf.rm.FVar(i))
    except:
      return None

  def SetFVar(self, i, v):
    try:
      olx.xf.rm.FVar(i, v)
      return True
    except:
      return False

  def GetDampingParams(self):
    default = (0.7/1000, 15)
    try:
      v = olx.Ins('DAMP').split()
      if len(v) != 2:
        return default
      return (float(v[0])/1000, float(v[1]))
    except:
      return default

  def GetExtinction(self):
    try:
      ev = olx.xf.rm.Exti()
      if '(' in ev:
        return float(ev.split('(')[0])
      return float(ev)
    except:
      return None

  def SetExtinction(self, v, e=None):
    try:
      if e:
        olx.xf.rm.Exti(v, e)
      else:
        olx.xf.rm.Exti(v)
      return True
    except:
      return False

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

  def CifMerge(self, filepath, update_atoms_loop=None, report=True):
    try:
      cmd = ''
      if filepath:
        cmd = '%s' %filepath
      if update_atoms_loop is None:
        update_atoms_loop = (OV.GetParam('snum.refinement.program', '') == 'olex2.refine')
      finalise = self.GetParam('user.cif.finalise', 'Ignore')
      finalise_value = None
      if finalise == 'Include':
        finalise_value = True
      elif finalise == 'Exclude':
        finalise_value = False
      if type(filepath) == list:
        olx.CifMerge(*filepath, f=finalise_value, u=update_atoms_loop)
      else:
        olx.CifMerge(filepath, f=finalise_value, u=update_atoms_loop)
      if report:
        print "Refinement CIF file has been merged with the meta-data cif file"
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
    try:
      text = text.encode('utf-8')
    except:
      text = text.decode('utf-8')
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
    olex.m('reap %s' %path)

  def AtReap(self, path):
    path = path.strip("'")
    path = path.strip('"')
    path = '"%s"' %path
    olex.m('@reap %s' %path)
    if OV.HasGUI():
      olex.m('spy.run_skin sNumTitle')
      olx.html.Update()

  def Reset(self):
    olx.Reset()

  def htmlUpdate(self):
    olex.m("html.Update")

  def htmlPanelWidth(self):
    olex.m("HtmlPanelWidth")

  def reloadStructureAtreap(self, path, file, fader=True, sg_changed = False, update_gui=True):
    if not self.HasGUI():
      olex.m("@reap \"%s\"" %(r"%s/%s.res" %(path, file)))
      return
    fader = self.FindValue('gui_use_fader')
    #print "AtReap %s/%s" %(path, file)
    try:
      if OV.HasGUI():
        if fader == 'true':
          olex.m("atreap_fader -b \"%s\"" %(r"%s/%s.res" %(path, file)))
        else:
          olex.m("atreap_no_fader -b \"%s\"" %(r"%s/%s.res" %(path, file)))
        import gui
        olex.m('spy.run_skin sNumTitle')
        if update_gui:
          olx.html.Update()


    except Exception, ex:
      print >> sys.stderr, "An error occured whilst trying to reload %s/%s" %(path, file)
      sys.stderr.formatExceptionInfo()

  def file_ChangeExt(self, path, newExt):
    try:
      newPath = olx.file.ChangeExt(path, newExt)
    except Exception, ex:
      print >> sys.stderr, "An error occured"
      sys.stderr.formatExceptionInfo()
    return newPath

  def File(self, filename=None):
    if filename is not None:
      olx.File("\"%s\"" %filename)
    else:
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

  def registerFunction(self,function,profiling=False,namespace=""):
    g = self.func_wrap(function)
    g.__name__ = function.__name__
    olex.registerFunction(g,profiling,namespace)

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
        print >> sys.stderr, "An error occurred running the function/macro %s" %(f.__name__)
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
          print >> sys.stderr, "An error occurred running the function/macro %s" %(f.__name__)
          sys.stderr.formatExceptionInfo()
          retVal = ''
        #retVal = a.runcall(f, *args, **kwds)
        return retVal
      return func

  def IsPluginInstalled(self,plugin):
    return olx.IsPluginInstalled(plugin) == 'true'

  if olx.IsPluginInstalled('plugin-CProfile') == 'true':
    #import cProfile
    #outFile = open('%s/profile.txt' %olx.DataDir(), 'w')
    #outFile.close()

    def cprofile_wrap(self,f):
      import pstats
      def func(*args, **kwds):
        a = cProfile.Profile()
        try:
          retVal = a.runcall(f, *args, **kwds)
        except Exception, ex:
          print >> sys.stderr, "An error occurred running the function/macro %s" %(f.__name__)
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
    path = path.replace('\\','/')
    if path.startswith("/") and "//" not in path:
      path = "/" + path
    if os.sep != '/':
      path = path.replace('/', os.sep)
    return path

  def standardizeListOfPaths(self, list_of_paths):
    retList = []
    for path in list_of_paths:
      retList.append(self.standardizePath(path))
    return retList

  def BaseDir(self):
    return olx.BaseDir()

  def DataDir(self):
    return olx.DataDir()

  def FileDrive(self,FileDrive=None):
    if FileDrive is not None:
      path = olx.FileDrive(FileDrive)
    else:
      path = olx.FileDrive()
    return path

  def FileExt(self,FileExt=None):
    if FileExt is not None:
      path = olx.FileExt(FileExt)
    else:
      path = olx.FileExt()
    return path

  def FileFull(self):
    return olx.FileFull()

  def FileName(self,FileName=None):
    if FileName is not None:
      path = olx.FileName(FileName)
    else:
      path = olx.FileName()
    return path

  def ModelSrc(self):
    try: #remove later!!HP
      model_src = olx.xf.rm.ModelSrc()
      if not model_src:
        i = int(olx.xf.CurrentData())
        if i != 0:
          return olx.xf.DataName(i)
        else:
          return self.FileName()
    except:
      return self.FileName()
    return model_src

  def FilePath(self,FilePath=None):
    if FilePath is not None:
      path = olx.FilePath(FilePath)
    else:
      path = olx.FilePath()
    return path

  def olex_function(self, str):
    try:
      retval = olex.f(str)
      return retval
    except Exception, err:
      print "Printing error %s" %err
      return "Error"

  def HKLSrc(self, new_HKLSrc=''):
    if new_HKLSrc:
      return olx.HKLSrc(new_HKLSrc)
    else:
      return olx.HKLSrc()

  def StrDir(self):
    return olx.StrDir()

  def GetFormula(self):
    return olx.xf.GetFormula()

  def GetCellVolume(self):
    return olx.xf.au.GetCell()

  def AddIns(self, instruction, quiet=False):
    olx.AddIns(*instruction.split(), q=quiet)

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
    if olx.olex2_tag:
      return olx.olex2_tag
    try:
      rFile = open("%s/olex2.tag" %self.BaseDir(),'r')
      tag = rFile.readline().rstrip("\n")
      rFile.close()
      olx.olex2_tag = tag
    except:
      pass
    return olx.olex2_tag

  def GetKeyname(self):
    import glob
    g = glob.glob(r"%s/*.%s" %(key_directory, "priv"))
    for item in g:
      keyname = item.split("\\")[-1:][0]
      return keyname.split(".")[0]

  def ListFiles(self, dir_name, mask=None):
    import glob
    rv = []
    cd = os.getcwdu()
    try:
      dir_name = os.path.normpath(dir_name)
      if not mask:
        h, t = os.path.split(dir_name)
        if h:
          os.chdir(h)
        else:
          h = ''
        for i in glob.glob(t):
          rv.append(os.path.join(h, i))
      else:
        os.chdir(dir_name)
        masks = mask.split(';')
        for m in masks:
          for i in glob.glob("*.%s" %(m)):
            rv.append(os.path.join(dir_name, i))
      return rv
    except:
      return []
    finally:
      os.chdir(cd)

  def GetUserComputerName(self):
    import os
    return os.getenv('USERNAME'), os.getenv('COMPUTERNAME')

  def GetSVNVersion(self):
    if olx.olex2_svn_version:
      return olx.olex2_svn_version
    path = "%s/version.txt" %self.BaseDir()
    try:
      rFile = open(path, 'r')
      line = rFile.read()
      rFile.close()
      olx.olex2_svn_version = int(line.split()[-1])
    except:
      olx.olex2_svn_version = 1
    return olx.olex2_svn_version

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

  def SetHtmlFontSize(self):
    size = OV.GetParam('gui.html.font_size')
    #if sys.platform[:3] != 'win':
      #size += 1
    #elif sys.platform[:3] == 'win':
      #size = 6
    OV.SetVar('HtmlGuiFontSize', size)
    return size

  def SetHtmlFontSizeControls(self):
    size = OV.GetParam('gui.html.font_size_controls')
    if sys.platform[:3] != 'win':
      size += 1
    #elif sys.platform[:3] == 'win':
      #size = 2
    OV.SetVar('HtmlFontSizeControls', size)
    return size


  def GetHtmlPanelX(self):
    screen_width = int(olx.GetWindowSize().split(',')[2])
    html_panelwidth = int(olx.html.ClientWidth('self'))
    htmlPanelX = screen_width - html_panelwidth
    return htmlPanelX

  def setAllMainToolbarTabButtons(self):
    import olexex
    olexex.setAllMainToolbarTabButtons()

  def GetCrystalData(self):
    crystal_data_file = olex.m("cif2doc crystal_data.htm -n=%s_crystal_data.htm" %OV.FileName())
    rFile = open('%s_crystal_data.htm' %OV.FileName(),'r')
    crystal_data = rFile.read()
    rFile.close()
    return crystal_data

  def makeGeneralHtmlPop(self, phil_path, htm='htm', number_of_lines=0):
    pop_name=OV.GetParam('%s.name' %phil_path)
    htm=OV.GetParam('%s.%s' %(phil_path,htm))
    width=OV.GetParam('%s.width' %phil_path)
    height=OV.GetParam('%s.height' %phil_path)
    auto_height_constant=OV.GetParam('%s.auto_height_constant' %phil_path)
    auto_height_line=OV.GetParam('%s.auto_height_line' %phil_path)
    position=OV.GetParam('%s.position' %phil_path)
    x=OV.GetParam('%s.x' %phil_path)
    y=OV.GetParam('%s.y' %phil_path)
    border=OV.GetParam('%s.border' %phil_path)
    if x is None: x = 0
    if y is None: y = 0
    htm = r"%s%s" %(OV.BaseDir(), htm)
    htm = os.path.normpath(htm.replace('\\', '/'))
    if not os.path.exists(htm):
      OV.write_to_olex('generalPop.htm',htm)
      htm = 'generalPop.htm'
      t = htm
    else:
      t = open(htm,'r').read()
    if height == "automatic":
      number_of_lines = t.count("<br>")
      number_of_lines += t.count("<tr>")
      if phil_path == 'olex2.ccdc.pop':
        number_of_lines += OV.get_cif_item('_publ_contact_author_address').count("\n")
      height = number_of_lines * auto_height_line + auto_height_constant
      #print "Number of lines: %s; Height: %s" %(number_of_lines, height)
    if position == "center":
      ws = olx.GetWindowSize('gl')
      ws = [int(i) for i in ws.split(",")]
      if width < ws[2]:
        x = int(ws[2])/2 - width/2
      else: x = 0
      if height < ws[3]:
        y = int(ws[3])/2 - height/2
      else:
        y = 0
    pstr = "popup '%s' '%s' -t='%s' -w=%s -h=%s -x=%s -y=%s" %(pop_name, htm, pop_name, width+border*2 +10, height+border*2, x, y)
    OV.cmd(pstr)
    olx.html.SetBorders(pop_name,border)
    OV.cmd(pstr)
    olx.html.SetBorders(pop_name,border)

  def getCompatibleProgramName(self, name):
    prgs = {'ShelXS-2013' : 'ShelXS',
            'ShelXS86' : 'ShelXS',
            'smtbx-solve' : 'olex2.solve',
            'ShelXL-2013' : 'ShelXL',
            'ShelXL-2012' : 'ShelXL',
            'ShelXLMP-2012' : 'ShelXL',
            'smtbx-refine' : 'olex2.refine'
            }
    return prgs.get(name, name)

  def canNetwork(self, show_msg=True):
    if not OV.GetParam("olex2.network"):
      if show_msg:
        print("Network communication disabled, aborting")
      return False
    return True

def GetParam(variable, default=None):
  # A wrapper for the function spy.GetParam() as exposed to the GUI.
  return OV.GetParam_as_string(variable, default)

OV = OlexFunctions()
OV.registerFunction(GetParam)
OV.registerFunction(OV.SetParam)
OV.registerFunction(OV.HtmlGetValue)
OV.registerFunction(OV.set_bond_thicknes)
OV.registerFunction(OV.set_cif_item)
OV.registerFunction(OV.get_cif_item)
OV.registerFunction(OV.write_to_olex)
OV.registerFunction(OV.CopyVFSFile)
OV.registerFunction(OV.SetHtmlFontSize,False,'gui')
OV.registerFunction(OV.SetHtmlFontSizeControls,False,'gui')
OV.registerFunction(OV.ModelSrc)