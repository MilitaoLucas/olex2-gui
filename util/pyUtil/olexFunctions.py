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

from decors import gui_only

import time

try:
  olx.olex2_tag
except:
  olx.olex2_tag = None
  olx.olex2_svn_version = None

gui_encoding = olx.app.OptValue('gui.encoding')

HasGUI = olx.HasGUI() == 'true'

class SilentException(Exception):
  def __init__(self, cause):
    self.cause = cause

class OlexFunctions(guiFunctions.GuiFunctions):
  def __init__(self):
    if HasGUI:
      import olex_gui
      self.olex_gui = olex_gui
    self.paramStack = ParamStack()

  def GetValue(self, control_name):
    retVal = olx.html.GetValue(control_name)
    return retVal

  def SetVar(self,variable,value):
    try:
      olex_core.SetVar(variable,value)
    except Exception as ex:
      print("Variable %s could not be set with value %s" %(variable,value), file=sys.stderr)
      sys.stderr.formatExceptionInfo()

  def GetVar(self,variable,def_val=""):
    try:
      return olex_core.FindValue(variable, def_val)
    except Exception as ex:
      print("Variable %s could not be retrieved" %(variable), file=sys.stderr)
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
      if not handler.param_exists(variable):
        olx.structure_params[variable] = value
        return
      if value == '': value = None
      elif value in ('Auto','auto','None','none',None):
        pass
      elif isinstance(value, str):
        value = "'%s'" %value.replace("'", "\\'").replace('$', '\\$')
      elif type(value) in (list, set):
        value = ' '.join("'%s'" %v.replace("'", "\\'") for v in value)
      elif "date_" in variable:
        try:
          if type(value) is str:
            pattern = '%d-%m-%Y'
            value = int(time.mktime(time.strptime(value, pattern)))
        except:
          pass
      else:
        value = "'%s'"  %str(value)
      handler.update_single_param(str(variable), value)
    except Exception as ex:
      print("Variable %s could not be set with value %s" %(variable,value), file=sys.stderr)
      sys.stderr.formatExceptionInfo()

  def GetCifMergeFilesList(self):
    return self.standardizeListOfPaths(OV.GetParam('snum.report.merge_these_cifs'))

  def GetHeaderParam(self, param, default=None, src=None):
    if src == None:
      src =  self.GetRefinementModel(False)['Generic']
    if src is None:
      return default
    toks = param.split(".")
    for i, t in enumerate(toks):
      if (i+1) == len(toks):
        if t == 'value':
          return src.get('value', default)
        if t == 'fields':
          return src.get('fields', default)
        else:
          return src['fields'].get(t, default)
      src = src.get(t)
      if src is None:
        return default
    return default

  def GetParam(self, variable, default=None, get_list=False):
    retVal = default
    try:
      if variable.startswith('gui'):
        if olx.gui_phil_handler == None:
          return default
        handler = olx.gui_phil_handler
      else:
        handler = olx.phil_handler
      if variable in olx.structure_params:
        return olx.structure_params[variable]

      retVal = handler.get_validated_param(variable)

      do_replace = True
      if type(retVal) == str and "()" in retVal:
        base = retVal.split('()')
        try:
          _ = getattr(OV, base[0])
          path = _()
          if os.path.exists(path):
            retVal = os.path.join(path, base[1][1:])
          do_replace = False
        except:
          pass

      if retVal is not None:
        if do_replace:
          if isinstance(retVal, bytes):
            retVal = str(retVal, 'utf-8').replace('\\$', '$')
          elif isinstance(retVal, str):
            retVal = retVal.replace('\\$', '$')
          elif isinstance(retVal, list) and len(retVal) > 0 and isinstance(retVal[0], str):
            retVal = [x.replace('\\$', '$') for x in retVal]
      else:
        retVal = default
    except Exception as ex:
      print("Variable %s could not be found" %(variable), file=sys.stderr)
      sys.stderr.formatExceptionInfo()
    return retVal

  @gui_only()
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
      olx.html.SetValue('SLIDE_BZOOM', value/10)
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
      try:
        tem = olx.cif_model[data_name].get(key, default)
      except KeyError:
        return default
#      print "Accessing %s" %key
      if tem is None or tem == default:
        return default
      if isinstance(tem, str):
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
        except Exception as ex:
          print(ex)
    return default

  def update_crystal_size(self):
    vals = [self.get_cif_item('_exptl_crystal_size_min'),
            self.get_cif_item('_exptl_crystal_size_mid'),
            self.get_cif_item('_exptl_crystal_size_max')]
    valid = True
    for x in vals:
      if x in (None, '?', '.', ''):
        valid = False
        break
    if valid:
      olx.xf.exptl.Size("%sx%sx%s" %(vals[0], vals[1], vals[2]))

  def set_cif_item(self, key, value):
    if olx.cif_model is not None:
      try:
        value.encode('ascii')
      except:
        print("Please use only ASCII characters")
        return
      data_name = self.ModelSrc().replace(' ', '')
      data_block = olx.cif_model[data_name]
      if isinstance(value, str):
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
    elif key.startswith('_exptl_crystal_size'):
      self.update_crystal_size()


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
    except Exception as ex:
      print("Program %s could not be set" %(program), file=sys.stderr)
      sys.stderr.formatExceptionInfo()

  def set_refinement_program(self, program, method=None, scope='snum'):
    try:
      import olexex
      self.SetParam('%s.refinement.program' %scope, program)
      olexex.onRefinementProgramChange(program, method, scope)
    except Exception as ex:
      print("Program %s could not be set" %(program), file=sys.stderr)
      sys.stderr.formatExceptionInfo()

  def get_refienment_program_refrerence(self, pname=None):
    try:
      import ExternalPrgParameters
      if pname is None:
        pname = self.GetParam('snum.refinement.program')
      prg = ExternalPrgParameters.defineExternalPrograms()[1].programs[pname]
      version = self.GetProgramVersionByName(pname)
      if pname.lower().startswith("shelx") or pname.lower().startswith('x'):
        pname = pname.upper()
      return "%s %s (%s)" %(pname, version, prg.brief_reference)
    except:
      return '?'

  def have_nsff(self):
    retVal = False
    if not OV.GetParam('user.refinement.hide_nsff') and OV.GetParam('snum.refinement.program').startswith("olex2.refine"):
      retVal = True
    return retVal

  def SetMaxCycles(self, max_cycles):
    try:
      import programSettings
      self.SetParam('snum.refinement.max_cycles', max_cycles)
      programSettings.onMaxCyclesChange(max_cycles)
    except Exception as ex:
      print("Could not set max cycles to %s" %(max_cycles), file=sys.stderr)
      sys.stderr.formatExceptionInfo()

  def SetMaxPeaks(self, max_peaks):
    ctrl_name = 'SET_SNUM_REFINEMENT_MAX_PEAKS'
    try:
      max_peaks = int(max_peaks)
    except:
      return
    self.SetParam('snum.refinement.manual_q_peak_override', max_peaks)
    auto_peaks = OV.GetVar('auto_q', None)
    if not auto_peaks:
      import olexex
      auto_peaks = olexex.get_auto_q_peaks()

    if not max_peaks:
      OV.SetParam('snum.refinement.manual_q_peak_override', 0)
      max_peaks = auto_peaks
      if OV.IsControl(ctrl_name):
        olx.html.SetBG(ctrl_name,OV.GetParam('gui.green').hexadecimal)
        olx.html.SetFG(ctrl_name,'#ffffff')
        olx.html.SetValue(ctrl_name,0)

    if max_peaks != 0 and auto_peaks != max_peaks:
      OV.SetParam('snum.refinement.manual_q_peak_override', max_peaks)
      if OV.IsControl(ctrl_name):
        olx.html.SetBG(ctrl_name,OV.GetParam('gui.red').hexadecimal)
        olx.html.SetFG(ctrl_name, '#ffffff')
        olx.html.SetValue(ctrl_name,max_peaks)

    try:
      import programSettings
      old_value = self.GetParam('snum.refinement.max_peaks')
      if old_value is not None:
        max_peaks = int(max_peaks)
        if max_peaks > 0:
          max_peaks = int(math.copysign(max_peaks, old_value)) # keep sign of old value
      self.SetParam('snum.refinement.max_peaks', max_peaks)
      programSettings.onMaxPeaksChange(max_peaks)
    except Exception as ex:
      print("Could not set max peaks to %s" %(max_peaks), file=sys.stderr)
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
    default = [0.7/1000, 15]
    try:
      v = olx.Ins('DAMP').split()
      if len(v) > 0:
        default[0] = float(v[0])/1000
      if len(v) > 1:
        default[1] = float(v[1])
      return default
    except:
      return default

  def SetExtinction(self, v, e=None):
    try:
      if e:
        olx.xf.rm.Exti(v, e)
      else:
        olx.xf.rm.Exti(v)
      return True
    except:
      return False

  def SetSWAT(self, g, U, e_g=None, e_U=None):
    try:
      if e_g and e_U:
        olx.xf.rm.SWAT(g, U, e_g, e_U)
      else:
        olx.xf.rm.SWAT(g, U)
      return True
    except:
      return False

  def FindValue(self,variable,default=''):
    try:
      retVal = olex_core.FindValue(variable, default)
    except SystemError as ex:
      print("System error with variable %s" %(variable), file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retVal = ''
    except Exception as ex:
      print("Variable %s could not be found" %(variable), file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retVal = ''
    return retVal

  def IsFileType(self, fileType):
    return olx.IsFileType(fileType) == 'true'

  def FindObject(self,variable):
    try:
      retVal = olex_core.FindObject(variable)
    except Exception as ex:
      print("An object for variable %s could not be found" %(variable), file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retVal = None
    return retVal

  def IsVar(self,variable):
    try:
      retVal = olex_core.IsVar(variable)
    except Exception as ex:
      print("An error occured whilst trying to find variable %s" %(variable), file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retVal = False
    return retVal

  def Translate(self,text):
    try:
      retStr = olex_core.Translate(text)
    except Exception as ex:
      print("An error occured whilst translating %s" %(text), file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  def TranslatePhrase(self,text):
    try:
      retStr = olx.GetVar(text, olx.TranslatePhrase(text))
    except Exception as ex:
      print("An error occured whilst translating %s" %(text), file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  def CurrentLanguageEncoding(self):
    try:
      retStr = olx.CurrentLanguageEncoding()
    except Exception as ex:
      print("An error occured whilst trying to determine the current language encoding", file=sys.stderr)
      sys.stderr.formatExceptionInfo()
      retStr = None
    return retStr

  def CifMerge(self, filepath, update_atoms_loop=None, report=True):
    try:
      olex2_refine = (OV.GetParam('snum.refinement.program', '').startswith("olex2.refine"))
      finalise = self.GetParam('user.cif.finalise', 'Ignore')
      ires = olx.IsFileType('IRES') == 'true'
      finalise_value = None
      if finalise == 'Include':
        finalise_value = True
      elif finalise == 'Exclude':
        finalise_value = False
      elif olex2_refine and ires:
        acta = olx.Ins("ACTA").strip()
        if acta and "NOHKL" == acta.split()[-1].upper():
          finalise_value = False
        else:
          finalise_value = True

      if update_atoms_loop is None:
        update_atoms_loop = olex2_refine
      #create FAB if needed
      if ires and olx.Ins("ABIN") != 'n/a':
        fab_path = os.path.splitext(OV.HKLSrc())[0] + ".fab"
        if not os.path.exists(fab_path):
          try:
            import cctbx_olex_adapter as COA
            from cctbx_olex_adapter import OlexCctbxAdapter
            mask = COA.OlexCctbxAdapter().load_mask()
            if mask:
              COA.write_fab(mask, fab_path)
          except Exception as e:
            print("Failed to create FAB file: %s" %str(e))
      opts = {'u': update_atoms_loop,
              'f': finalise_value,
              'rtab': self.GetParam('snum.cif.report_rtabs'),
              'vars': self.GetParam('snum.cif.report_vars'),
              'dn': self.GetParam('snum.cif.dataname'),
              }
      if type(filepath) == list:
        olx.CifMerge(*filepath, **opts)
      else:
        olx.CifMerge(filepath, **opts)
      if report:
        pass
        #print "Refinement CIF file has been merged with the meta-data cif file"
    except Exception as ex:
      print("An error occurred whilst trying to find merge cif files", file=sys.stderr)
      sys.stderr.formatExceptionInfo()

  def reset_file_in_OFS(self,fileName,txt=" ",copyToDisk = False):
    try:
      import OlexVFS
      OlexVFS.write_to_olex(fileName, txt)
      if copyToDisk:
        wFile = open("%s/%s" %(self.DataDir(),fileName),'wb')
        wFile.write(txt)
        wFile.close()
    except Exception as ex:
      print("An error occurred whilst trying to write to the VFS", file=sys.stderr)
      sys.stderr.formatExceptionInfo()

  def write_to_olex(self,fileName,text,copyToDisk = False):
    try:
      import OlexVFS
      OlexVFS.write_to_olex(fileName, text)
      if copyToDisk:
        wFile = open("%s/%s" %(self.DataDir(),fileName),'w')
        wFile.write(text)
        wFile.close()
    except Exception as ex:
      print("An error occurred whilst trying to write to the VFS", file=sys.stderr)
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
      path = '"%s"' %path
    olex.m('reap %s' %path)

  def AtReap(self, path):
    path = path.strip("'")
    path = path.strip('"')
    path = '"%s"' %path
    olex.m('@reap %s' %path)
    if OV.HasGUI():
      olex.m('spy.run_skin sNumTitle')
      OV.UpdateHtml()

  def Reset(self):
    olx.Reset()

  @gui_only()
  def htmlUpdate(self):
    olex.m("html.Update")

  @gui_only()
  def htmlPanelWidth(self):
    olex.m("HtmlPanelWidth")

  def reloadStructureAtreap(self, path, file, fader=True, sg_changed = False, update_gui=True):
    if not self.HasGUI():
      olex.m("@reap \"%s\"" %(r"%s/%s.res" %(path, file)))
      return
    fader = self.FindValue('gui_use_fader')
    try:
      if OV.HasGUI():
        if fader == 'true':
          olex.m("atreap_fader -b \"%s\"" %(r"%s/%s.res" %(path, file)))
        else:
          olex.m("atreap_no_fader -b \"%s\"" %(r"%s/%s.res" %(path, file)))
        import gui
        olex.m('spy.run_skin sNumTitle')
        if update_gui:
          OV.UpdateHtml()
    except Exception as ex:
      print("An error occured whilst trying to reload %s/%s" %(path, file), file=sys.stderr)
      sys.stderr.formatExceptionInfo()

  def file_ChangeExt(self, path, newExt):
    try:
      newPath = olx.file.ChangeExt(path, newExt)
    except Exception as ex:
      print("An error occured", file=sys.stderr)
      sys.stderr.formatExceptionInfo()
    return newPath

  def File(self, filename=None, append_refinement_info=False, save_params=False):
    if filename is not None:
      olx.File(filename)
    else:
      olx.File()
    if save_params:
      from variableFunctions import SaveStructureParams
      SaveStructureParams()

    if append_refinement_info and olx.FileExt().lower() == 'res':
      saved_file = olx.FileFull()
      ri = olx.xf.RefinementInfo()
      if not ri: return
      ri = ri.split(";")
      out_strings = [
        "  REM The information below was added by Olex2.",
        "REM +++ Tabular Listing of Refinement Information +++"
      ]
      for i in ri:
        if not i: continue
        out_strings.append("REM %s = %s" %tuple(i.split('=')))
      with open(saved_file, "a") as out:
        out.write('\n')
        out.write('\n  '.join(out_strings))
        out.write('\n')


  def timer_wrap(self,f,*args, **kwds):
    import time
    t0 = time.time()
    retVal = ''
    try:
      retVal = f(*args, **kwds)
    except Exception as ex:
      sys.stderr.write("An error occurred running the function/macro %s\n" %(f.__name__))
      sys.stderr.formatExceptionInfo()
    finally:
      t1 = time.time()
      print("Time take for the function %s is %s" %(f.__name__,(t1-t0)))
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

  def unregisterCallback(self,event,function,profiling=False):
    g = self.func_wrap(function)
    g.__name__ = function.__name__
    olex.unregisterCallback(event,function,profiling)

  def func_wrap(self,f):
    def func(*args, **kwds):
      retVal = ''
      try:
        retVal = f(*args, **kwds)
      except SilentException:
        pass
      except Exception as ex:
        sys.stderr.write("An error occurred running the function/macro %s\n" %(f.__name__))
        sys.stderr.formatExceptionInfo()
      finally:
        return retVal
    return func

  if False:  ## Change this to True to print out information about all the function calls
    def func_wrap(self,f):
      def func(*args, **kwds):
        print(f)
        print(f.__code__)
        print()
        try:
          retVal = f(*args, **kwds)
        except Exception as ex:
          sys.stderr.write("An error occurred running the function/macro %s\n" %(f.__name__))
          sys.stderr.formatExceptionInfo()
          retVal = ''
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
        except Exception as ex:
          print("An error occurred running the function/macro %s" %(f.__name__), file=sys.stderr)
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
    if os.sep != '/':
      path = path.replace('/', os.sep)
    else:
      path = path.replace('\\', os.sep)
    return path

  def standardizeListOfPaths(self, list_of_paths):
    retList = []
    for path in list_of_paths:
      retList.append(self.standardizePath(path))
    return retList

  def evaluate_function(self, func):
    a = getattr(self, func)
    return a()

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

  def HasCif(self):
    if olx.cif_model is not None:
      data_name = self.ModelSrc().replace(' ', '')
      if data_name in olx.cif_model:
        return True
    return False

  def ModelSrc(self, force_cif_data=False):
    try: #remove later!!HP
      model_src = olx.xf.rm.ModelSrc()
      if not model_src:
        i = int(olx.xf.CurrentData())
        if i != 0 or force_cif_data:
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
    except Exception as err:
      print("Printing error %s" %err)
      return "Error"

  def HKLSrc(self, new_HKLSrc=''):
    if new_HKLSrc:
      return olx.HKLSrc(new_HKLSrc)
    else:
      return olx.HKLSrc()

  def StrDir(self):
    try:
      return olx.StrDir()
    except:
      return None

  def GetFormula(self):
    return olx.xf.GetFormula()

  def GetCellVolume(self):
    return olx.xf.au.GetCellVolume()

  def AddIns(self, instruction, quiet=False):
    olx.AddIns(*instruction.split(), q=quiet)

  def DelIns(self, instruction):
    olx.DelIns(instruction)

  def HasGUI(self):
    return HasGUI

  def IsDebugging(self):
    return self.GetParam("olex2.debug", False)

  def IsNoSpherA2(self):
    return self.GetParam("snum.NoSpherA2.use_aspherical") and\
      self.GetParam("snum.refinement.program") == "olex2.refine"

  def get_diag(self, param):
    v = None
    if OV.IsEDData():
      v = OV.GetParam("user.diagnostics_ed.%s" %param)
    if not v:
      v = OV.GetParam("user.diagnostics.%s" %param)
    return v

    #v = OV.GetParam(f"user.diagnostics_ed.{param}") if OV.IsEDData() else OV.GetParam(f"user.diagnostics.{param}")


  def IsEDData(self):
    try:
      return float(olx.xf.exptl.Radiation()) < 0.1
    except:
      return False

  def IsEDRefinement(self):
    return self.IsEDData() and\
      self.GetHeaderParam("ED.refinement.method", "Kinematic") != "Kinematic" and\
      self.GetParam("snum.refinement.program").startswith("olex2.refine")

  def IsRemoteMode(self):
    return 'true' == olx.GetVar('olex2.remote_mode', 'false')

  def IsClientMode(self):
    return self.GetParam('user.refinement.client_mode', False)

  def GetThreadN(self):
    v = self.GetParam('user.refinement.thread_n')
    if v.endswith("%"):
      v = int(v[:-1])
      if v < 0:
        v = 75
      v = os.cpu_count() * v / 100
      if v < 1:
        v = 1
      return int(v)
    else:
      v = int(v)
      if v <= 0:
        v = max(1, int(os.cpu_count() *3/4))
      return v

  def GetACI(self):
    import AC7 as ac
    return ac.get_aci()

  def ListParts(self):
    import olexex
    parts = set(olexex.OlexRefinementModel().disorder_parts())
    if len(parts) == 1:
      return None
    else:
      return parts

  def PrintMaskHKLWarning(self, message):
    if not self.GetVar("mask.warning_printed", False):
      print(message)
      self.SetVar("mask.warning_printed", True)
    pass

  def ResetMaskHKLWarning(self):
    self.SetVar("mask.warning_printed", False)

  def StoreParameter(self, var="", save=False):
    val = self.FindValue(var)
    if val:
      val = "'%s'" %val
      olex.m('storeparam %s %s %s' %(var, val, save))

  def isInterruptSet(self):
    if OV.GetVar('stop_current_process'):
      OV.SetVar('stop_current_process', False)
      return True
    return False

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

  def GetProgramVersionByName(self, name, returnFlag=False):
    version = ""
    name = name.lower()
    if "shelxl" in name:
      version = olx.Lst('version')
    elif "xt" in name:
      try:
        marker = "_computing_structure_solution"
        with open(self.HKLSrc(), "r") as hkl:
          for line in hkl:
            if line.startswith(marker):
              version = line[len(marker):].strip().strip("'")
              if returnFlag:
                return (version, True)
              return version
      except:
        pass
    elif "olex2" in name:
      version=self.GetTag()
    elif "cctbx" in name:
      version=self.GetTag() + "(ccbtx)"
    elif "smtbx" in name:
      version=self.GetTag() + "(smtbx)"
    if returnFlag:
      return (version, False)
    return version

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

  def GetBaseTag(self):
    return self.GetTag().split('-')[0]

  def ListFiles(self, dir_name, mask=None):
    import glob
    rv = []
    cd = os.getcwd()
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
      import gui
      x,y = gui.GetBoxPosition(width, height)
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

  def runCommands(self,cmds):
    """
    This function takes a list of Olex2 commands and will execute these sequentially.
    """

    if type(cmds) is str:
      cmd = cmds.split(">>")
      cmd = ">>".join(cmd)
    else:
      cmd = ">>".join(cmds)
    try:
      olx.Run(cmd)
    except Exception as err:
      print(err)


  def canNetwork(self, show_msg=True):
    if not OV.GetParam("olex2.network"):
      if show_msg:
        print("Network communication disabled, aborting")
      return False
    return True

  def getPYLPath(self):
    pyl = os.path.join(olx.BaseDir(), "pyl")
    if sys.platform[:3] == 'win':
      pyl += '.exe'
    else:
      if not self.GetParam("olex2.check_executable.pyl", True):
        return pyl
      import stat
      if not (os.stat(pyl)[stat.ST_MODE] & stat.S_IXUSR):
        print("The pyl is not executable, trying to fix")
        try:
          os.chmod(pyl, stat.S_IXUSR)
          self.SetParam("olex2.check_executable.pyl", False)
        except:
          print("Failed to make pyl executable. Please fix manually.")
          return None
    return pyl

  def GetChoices(self, variable):
    _ = olx.phil_handler.get_values_by_name(variable)
    _ = _[0].strip("*")
    return _.split()

  def createFileLock(self, fileName):
    lockName = olx.file.ChangeExt(fileName, "lock")
    if sys.platform[:3] == 'win':
      import olex_core
      lock =  olex_core.CreateLock(lockName, 5000)
      if lock is None:
        raise IOError("Failed to acquire file lock!")
      return lock
    cnt = 0
    while os.path.exists(lockName):
      try:
        os.remove(lockName)
      except:
        cnt += 1
        if cnt > 5:
          raise IOError("Failed to remove the lock file: %s" %lockName)
        time.sleep(1)
    return (lockName, open(lockName, "w+"))

  def deleteFileLock(self, lock):
    if sys.platform[:3] == 'win':
      import olex_core
      return olex_core.DeleteLock(lock)
    lock[1].close()
    os.remove(lock[0])

  def init_fast_linalg(self):
    try:
      import fast_linalg
      from fast_linalg import env
      if not env.initialised:
        if sys.platform[:3] == "win":
          ob_path = olx.BaseDir()
          files = [x for x in os.listdir(ob_path) if 'openblas' in x and '.dll' in x]
        else:
          ob_path = os.path.join(olx.BaseDir(), 'lib')
          files = [x for x in os.listdir(ob_path) if 'openblas' in x and ('.so' in x or '.dylib' in x)]
        if files:
          env.initialise(os.path.join(ob_path, files[0]))
          if env.initialised:
            print("Successfully initialised OpenBlas from %s:" %files[0])
            print(env.build_config)
            return True
    except Exception as e:
      print("Could not initialise OpenBlas: %s" %e)
      return False

  #https://stackoverflow.com/questions/1305532/convert-nested-python-dict-to-object
  # constructs an object from dict
  def dict_obj(self, d):
    class d_o:
      def __init__(self, **entries):
        self.__dict__.update(entries)
    return d_o(**d)

  #Somehow on localised Linux Unicode does not work
  # may be wrongly assembled Python?
  def correct_rendered_text(self, t):
    if gui_encoding:
      return t.encode(gui_encoding)
    return t

  def writeShelxFinFile(self):
    shelx_dir = os.path.join(self.StrDir(), "temp")
    if os.path.exists(shelx_dir):
      open(os.path.join(shelx_dir,
        self.FileName().replace(' ', '').lower()) + ".fin", 'w')\
      .close()

  def get_bool_from_any(self, val):
    return val in [True, 'true', 'True']

  def describe_refinement(self):
    edr = self.IsEDRefinement()
    nsf = self.GetParam("snum.NoSpherA2.use_aspherical")
    name = ""
    if edr or nsf: #only olex2.refine
      name = "Dyn-" + self.GetACI().EDI.get_method_name()
    else:
      rp = self.GetParam("snum.refinement.program")
      name += rp
    if self.GetParam("snum.refinement.use_solvent_mask"):
      name += "-mask"
    if nsf:
      name += "-NSF"

    r1 = self.GetParam('snum.refinement.last_R1')
    if r1 is not None:
      name += "-R-%.2f" %(float(r1)*100)
      wr2 = self.GetParam('snum.refinement.last_wR2')
      if wr2 is not None:
        name += "(%.2f)" %(float(wr2)*100)

    return name

  def update_HklSrc(self, lines: list, new_value: str):
    for i in range(len(lines)):
      if not lines[i].startswith("REM <HklSrc"):
        continue
      st = i
      while lines[i].startswith("REM") and not lines[i].strip().endswith(">"):
        if i >= len(lines):
          break
        del lines[i]
      lines[st] = "REM <HklSrc \".\\\\%s\">" %new_value
      return

def GetParam(variable, default=None):
  # A wrapper for the function spy.GetParam() as exposed to the GUI.
  return OV.GetParam_as_string(variable, default)

def GetFormattedCompilationInfo():
  t = "<font size='2'><table width='100%%' cellpadding='0' cellspacing='0'>"
  d = {}
  raw = olx.GetCompilationInfo('full')
  l = raw.split()
  if "svn" in raw:
    d['Date'] = l[0].rstrip(",")
    d['SVN'] = l[1].split(".")[1].rstrip(",")
    d['MSC'] = l[2].rstrip(",")
    d['OS'] = l[4].rstrip(",")
    d['Python'] = l[6].rstrip(",")
    d['wxWidgets'] = l[8].rstrip(",")
    d['Vendor'] = " ".join(l[10:]).rstrip(",")
    t += "<tr><td><b>Date</b>: %(Date)s, <b>SVN</b>: %(SVN)s,  <b>Compiler</b>: %(MSC)s</td></tr>" %d
    t += "<tr><td><b>Python</b>: %(Python)s, <b>wxWidgets</b>: %(wxWidgets)s,  <b>OS</b>: %(OS)s</td></tr>" %d
  else:
    d['Date'] = " ".join(l[0:3]).rstrip(",")
    d['MSC'] = l[4].rstrip(",")
    d['OS'] = l[6].rstrip(",")
    d['Python'] = l[8].rstrip(",")
    d['wxWidgets'] = l[10].rstrip(",")
    d['Vendor'] = " ".join(l[12:]).rstrip(",")
    t += "<tr><td><b>Date</b>: %(Date)s, <b>Compiler</b>: %(MSC)s</td></tr>" %d
    t += "<tr><td><b>Python</b>: %(Python)s, <b>wxWidgets</b>: %(wxWidgets)s,  <b>OS</b>: %(OS)s</td></tr>" %d
  t += "</table></font>"
  return t

# helper class to preserve user settings
class ParamStack():
  programs = []
  params = []
  def __init__(self):
      pass

  def push(self, param_name, value=None, set_none=False):
    self.params.append((param_name, OV.GetParam(param_name)))
    if value or set_none:
      OV.SetParam(param_name, value)

  def pop(self, number=1):
    if len(self.params) < number:
      raise("Push setting in before popping out")
    for i in range(0, number):
      v = self.params.pop()
      OV.SetParam(v[0], v[1])

  def push_program(self, name, program_name=None, method_name=None, scope="snum"):
    if len(self.programs) > 10:
      raise("Please check that you have popped all the settings, you pushed in, out!")
    prg_param = "%s.%s.program" %(scope, name)
    mtd_param = "%s.%s.method" %(scope, name)
    self.programs.append(
      (prg_param, OV.GetParam(prg_param),
       mtd_param, OV.GetParam(mtd_param)))
    if program_name:
      OV.SetParam(prg_param, program_name)
    if method_name:
      OV.SetParam(mtd_param, method_name)

  def pop_program(self, number=1):
    if len(self.programs) < number:
      raise("Push setting in before popping out")
    for i in range(0, number):
      v = self.programs.pop()
      OV.SetParam(v[0], v[1])
      OV.SetParam(v[2], v[3])

OV = OlexFunctions()
OV.registerFunction(GetFormattedCompilationInfo)
OV.registerFunction(GetParam)
OV.registerFunction(OV.GetChoices)
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
OV.registerFunction(OV.HasCif)
OV.registerFunction(OV.GetCifMergeFilesList)
OV.registerFunction(OV.runCommands)
OV.registerFunction(OV.IsPluginInstalled)
OV.registerFunction(OV.GetTag)
OV.registerFunction(OV.GetBaseTag)
OV.registerFunction(OV.set_refinement_program)
OV.registerFunction(OV.set_solution_program)
OV.registerFunction(OV.IsEDData)
OV.registerFunction(OV.get_diag)
OV.registerFunction(OV.SetMaxCycles)
OV.registerFunction(OV.SetMaxPeaks)
