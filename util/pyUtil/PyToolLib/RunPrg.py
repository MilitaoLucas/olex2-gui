import sys
import olex
import olx
import olex_core
import os
import olexex
import OlexVFS
import gui


from ArgumentParser import ArgumentParser
from History import hist

from olexex import OlexRefinementModel

from olexFunctions import OlexFunctions, SilentException
OV = OlexFunctions()
debug = bool(OV.GetParam('olex2.debug',False))
timer = debug

green = OV.GetParam('gui.green')
red = OV.GetParam('gui.red')
orange = OV.GetParam('gui.orange')
white = "#ffffff"
black = "#000000"
table = OV.GetVar('HtmlTableFirstcolColour')
import ExternalPrgParameters

from CifInfo import MergeCif
import TimeWatch
import time

import shutil

# The listeners expect a function

class ListenerManager(object):
  def __init__(self):
    self.onStart_listeners = []
    self.onEnd_listeners = []
  def register_listener(self, listener,event):
    if event == "onEnd":
      for l in self.onEnd_listeners:
        if type(l.__self__) == type(listener.__self__):
          return False
      self.onEnd_listeners.append(listener)
    elif event == "onStart":
      for l in self.onStart_listeners:
        if type(l.__self__) == type(listener.__self__):
          return False
      self.onStart_listeners.append(listener)

  def startRun(self, caller):
    for item in self.onStart_listeners:
      item(caller)

  def endRun(self, caller):
    for item in self.onEnd_listeners:
      item(caller)

LM = ListenerManager()

class RunPrg(ArgumentParser):
  running = None

  def __init__(self):
    super(RunPrg, self).__init__()
    self.demote = False
    self.SPD, self.RPD = ExternalPrgParameters.get_program_dictionaries()
    self.terminate = False
    self.interrupted = False
    self.tidy = False
    self.method = None
    self.Ralpha = 0
    self.Nqual = 0
    self.CFOM = 0
    self.HasGUI = OV.HasGUI()
    self.make_unique_names = False
    self.shelx_files = r"%s/util/SHELX/" %self.basedir
    self.isAllQ = False #If all atoms are q-peaks, this will be assigned to True
    self.his_file = None
    self.please_run_auto_vss = False
    self.demo_mode = OV.FindValue('autochem_demo_mode',False)
    self.broadcast_mode = OV.FindValue('broadcast_mode',False)

    if self.demo_mode:
      OV.demo_mode = True

    if self.HasGUI:
      from Analysis import PrgAnalysis
      self.PrgAnalysis = PrgAnalysis

    OV.registerFunction(self.run_auto_vss,False,'runprg')

    self.params = olx.phil_handler.get_python_object()
    OV.SetVar('SlideQPeaksVal','0') # reset q peak slider to display all peaks
    if not self.filename:
      print("No structure loaded")
      return
    self.original_filename = self.filename
    olx.Stop('listen')
    self.shelx_alias = OV.FileName().replace(' ', '').lower()
    os.environ['FORT_BUFFERED'] = 'TRUE'
    self.post_prg_output_html_message = ""

  def __del__(self):
    if self.method is not None and \
       hasattr(self.method, "unregisterCallback") and \
       callable(self.method.unregisterCallback):
      self.method.unregisterCallback()

  def run(self):
    import time
    import gui

    gui.set_notification(OV.GetVar('gui_notification'))
    OV.SetVar('gui_notification', "Refining...;%s;%s" %(green,white))
    if RunPrg.running:
      OV.SetVar('gui_notification', "Already running. Please wait...")
      print("Already running. Please wait...")
      return
    RunPrg.running = self
    caught_exception = None
    try:
      token = TimeWatch.start("Running %s" %self.program.name)
      if timer:
        t1 = time.time()
      res = self.method.run(self)
      if timer:
        print("REFINEMENT: %.3f" %(time.time() - t1))
      if not res:
        return False
      if not self.method.failure:
        if timer:
          t1 = time.time()
        self.runAfterProcess()
        if timer:
          print("runAfterProcess: %.3f" %(time.time() - t1))
      if timer:
        t1 = time.time()
    except Exception as e:
      sys.stdout.formatExceptionInfo()
      caught_exception = e
    finally:
      self.endRun()
      TimeWatch.finish(token)
      sys.stdout.refresh = False
      sys.stdout.graph = False
      if timer:
        print("endRun: %.3f" %(time.time() - t1))
      RunPrg.running = False

      if self.please_run_auto_vss:
        self.run_auto_vss()
      if caught_exception:
        raise SilentException(caught_exception)

  def run_auto_vss(self):
    olx.Freeze(True)
    olex.m('compaq')
    olex.m('compaq -a')
    olx.VSS(True)
    olex.m('compaq')
    olex.m('refine 2 10')
    olex.m('compaq')
    olx.ATA()
    olex.m('refine 2 10')
    olx.Freeze(False)

  def which_shelx(self, type="xl"):
    a = olexex.which_program(type)
    if a == "":
      OV.Alert("Error", "ShelX %s is not found on this system.\nPlease make sure that the ShelX executable files can be found on system PATH." %type, "O")
      OV.Cursor()
      self.terminate = True
    return a

  def doBroadcast(self):
    ext = "res"
    copy_from = "%s/%s.%s" %(self.tempPath, self.shelx_alias, ext)
    copy_to = "%s/listen.res" %(self.datadir)
    if os.path.isfile(copy_from):
      if copy_from.lower() != copy_to.lower():
        shutil.copyfile(copy_from, copy_to)

  def doFileResInsMagic(self):
    file_lock = OV.createFileLock(os.path.join(self.filePath, self.original_filename))
    try:
      extensions = ['res', 'lst', 'cif', 'fcf', 'mat', 'pdb']
      if "xt" in self.program.name.lower():
        extensions.append('hkl')
      if self.broadcast_mode:
        self.doBroadcast()
      for ext in extensions:
        if timer:
          t = time.time()
        if "xt" in self.program.name.lower() and ext != 'lst':
          copy_from = "%s/%s_a.%s" %(self.tempPath, self.shelx_alias, ext)
        else:
          copy_from = "%s/%s.%s" %(self.tempPath, self.shelx_alias, ext)
        copy_to = "%s/%s.%s" %(self.filePath, self.original_filename, ext)
        if os.path.isfile(copy_from):
          if copy_from.lower() != copy_to.lower():
            shutil.copyfile(copy_from, copy_to)
        if timer:
          pass
          #print "---- copying %s: %.3f" %(copy_from, time.time() -t)
    finally:
      OV.deleteFileLock(file_lock)

  def doHistoryCreation(self, type="normal"):
    if type == "first":
      historyPath = "%s/%s.history" %(OV.StrDir(), OV.FileName())
      if not os.path.exists(historyPath):
        type = 'normal'
    if type != "normal":
      return

  def setupFiles(self):
    olx.User("%s" %OV.FilePath())
    self.filePath = OV.FilePath()
    self.fileName = OV.FileName()
    self.tempPath = "%s/temp" %OV.StrDir()
    if not os.path.exists(self.tempPath):
      os.mkdir(self.tempPath)

    ## clear temp folder to avoid problems
    old_temp_files = os.listdir(self.tempPath)
    for file_n in old_temp_files:
      try:
        if "_.res" or "_.hkl" not in file_n:
          os.remove(r'%s/%s' %(self.tempPath,file_n))
      except OSError:
        continue

    self.hkl_src = OV.HKLSrc()
    if not os.path.exists(self.hkl_src):
      self.hkl_src = os.path.splitext(OV.FileFull())[0] + '.hkl'
      if os.path.exists(self.hkl_src):
        OV.HKLSrc(self.hkl_src)
        print("HKL Source Filename reset to default file!")
      else:
        raise Exception("Please choose a reflection file")
    self.hkl_src_name = os.path.splitext(os.path.basename(self.hkl_src))[0]
    self.curr_file = OV.FileName()
    copy_from = "%s" %(self.hkl_src)
    ## All files will be copied to the temp directory in lower case. This is to be compatible with the Linux incarnations of ShelX
    copy_to = "%s%s%s.hkl" %(self.tempPath, os.sep, self.shelx_alias)
    if not os.path.exists(copy_to):
      shutil.copyfile(copy_from, copy_to)
    copy_from = "%s%s%s.ins" %(self.filePath, os.sep, self.curr_file)
    copy_to = "%s%s%s.ins" %(self.tempPath, os.sep, self.shelx_alias)
    if not os.path.exists(copy_to):
      shutil.copyfile(copy_from, copy_to)
    #fab file...
    copy_from = ".".join(OV.HKLSrc().split(".")[:-1]) + ".fab"
    copy_to = os.path.join(self.tempPath, self.shelx_alias) + ".fab"
    if os.path.exists(copy_from) and not os.path.exists(copy_to):
      shutil.copyfile(copy_from, copy_to)

  def runCctbxAutoChem(self):
    from AutoChem import OlexSetupRefineCctbxAuto
    print('+++ STARTING olex2.refine ++++++++++++++++++++++++++++++++++++')
    OV.reloadStructureAtreap(self.filePath, self.curr_file)
    cctbx = OlexSetupRefineCctbxAuto('refine', self.params.snum.refinement.max_cycles)
    try:
      cctbx.run()
    except Exception as err:
      print(err)
    olex.f('GetVar(cctbx_R1)')
    print('+++ END olex2.refine +++++++++++++++++++++++++++++++++++++++++')

  def runAfterProcess(self):
    if 'olex2' not in self.program.name:
      if timer:
        t = time.time()
      self.doFileResInsMagic()
      if timer:
        print("--- doFilseResInsMagic: %.3f" %(time.time() - t))

      if timer:
        t = time.time()
      if self.HasGUI:
        olx.Freeze(True)
      OV.reloadStructureAtreap(self.filePath, self.curr_file, update_gui=False)
      if self.HasGUI:
        olx.Freeze(False)
      if timer:
        print("--- reloadStructureAtreap: %.3f" %(time.time() - t))

      # XT changes the HKL file - so it *will* match the file name
      if 'xt' not in self.program.name.lower():
        OV.HKLSrc(self.hkl_src)

    else:
      if self.broadcast_mode:
        if timer:
          t = time.time()
        self.doBroadcast()
        if timer:
          print("--- doBroacast: %.3f" %(time.time() - t))

      lstFile = '%s/%s.lst' %(self.filePath, self.original_filename)
      if os.path.exists(lstFile):
        os.remove(lstFile)
      olx.DelIns("TREF")

    if self.params.snum.refinement.auto.max_peaks:
      max_peaks = olexex.OlexRefinementModel().getExpectedPeaks()
      if max_peaks <= 5:
        self.params.snum.refinement.auto.pruneQ = 0.5
        self.params.snum.refinement.auto.assignQ = 6.0
        OV.SetParam('snum.refinement.auto.pruneQ', 0.5)
        OV.SetParam('snum.refinement.auto.assignQ', 6.0)
      else:
        self.params.snum.refinement.auto.pruneQ = 1.5
        self.params.snum.refinement.auto.assignQ = 2.0
        OV.SetParam('snum.refinement.auto.pruneQ', 1.5)
        OV.SetParam('snum.refinement.auto.assignQ', 2.0)

  def getProgramMethod(self, fun):
    if fun == 'refine':
      self.prgType = prgType = 'refinement'
      prgDict = self.RPD
      prg = self.params.snum.refinement.program
      method = self.params.snum.refinement.method
    else:
      self.prgType = prgType = 'solution'
      prgDict = self.SPD
      prg = self.params.snum.solution.program
      method = self.params.snum.solution.method
    try:
      program = prgDict.programs[prg]
    except KeyError:
      raise Exception("Please choose a valid %s program" %prgType)
    try:
      prgMethod = program.methods[method]
    except KeyError:
      raise Exception("Please choose a valid method for the %s program %s" %(prgType, prg))
    return program, prgMethod

  def startRun(self):
    OV.CreateBitmap('%s' %self.bitmap)
    LM.startRun(self)

  def endRun(self):
    self.method.unregisterCallback()
    OV.DeleteBitmap('%s' %self.bitmap)
    OV.Cursor()
    LM.endRun(self)

  def post_prg_html(self):
    if not OV.HasGUI():
      return
    import gui.tools
    debug = bool(OV.GetParam('olex2.debug',False))

    typ = self.prgType.lower()

    if typ=='refinement':
      return

    extra_msg = ""
    if typ == "refinement":
      extra_msg = "$spy.MakeHoverButton('small-Assign@refinement','ATA(1)')"
    elif typ == "solution" and self.program.name.lower() != "shelxt":
      extra_msg = gui.tools.TemplateProvider.get_template('run_auto_vss_box', force=debug)

    message = "<td>%s</td><td align='right'>%s</td>" %(self.post_prg_output_html_message, extra_msg)

    d = {
      'program_output_type':"PROGRAM_OUTPUT_%s" %self.prgType.upper(),
      'program_output_name':self.program.name,
      'program_output_content': message
    }

    t = gui.tools.TemplateProvider.get_template('program_output', force=debug)%d
    f_name = OV.FileName() + "_%s_output.html" %self.prgType
    OlexVFS.write_to_olex(f_name, t)
#    olx.html.Update()

class RunSolutionPrg(RunPrg):
  def __init__(self):
    RunPrg.__init__(self)
    self.bitmap = 'solve'
    self.program, self.method = self.getProgramMethod('solve')
    self.run()

  def run(self):
    if int(olx.xf.au.GetAtomCount()) != 0:
      if OV.HasGUI():
        if OV.GetParam('user.alert_solve_anyway') == 'Y':
          r = OV.Alert("Solve", "Are you sure you want to solve this again?",
            'YNIR', "(Don't show this warning again)")
          if "R" in r:
            OV.SetParam('user.alert_solve_anyway', 'N')
          if "N" in r:
            self.terminate = True
            return

    OV.SetParam('snum.refinement.data_parameter_ratio', 0)
    OV.SetParam('snum.NoSpherA2.use_aspherical', False)
    self.startRun()
    OV.SetParam('snum.refinement.auto.invert',True)
    if OV.IsFileType('cif'):
      OV.Reap('%s/%s.ins' %(self.filepath,self.filename))
    self.setupSolve()
    if self.terminate: return
    self.setupFiles()
    if self.terminate:
      self.endRun()
      self.endHook()
      return
    if self.params.snum.solution.graphical_output and self.HasGUI:
      self.method.observe(self)
    RunPrg.run(self)

  def runAfterProcess(self):
    olx.UpdateWght(0.1)
    OV.SetParam('snum.refinement.suggested_weight','0.1 0')
    OV.SetParam('snum.refinement.update_weight', False)
    RunPrg.runAfterProcess(self)
    self.method.post_solution(self)
    self.post_prg_html()
    self.doHistoryCreation()
    OV.SetParam('snum.current_process_diagnostics','solution')

  def setupSolve(self):
    try:
      self.sg = '\'' + olex.f(r'sg(%n)') + '\''
    except:
      self.sg = ""
    self.formula = olx.xf.GetFormula()
    if not self.formula:
      if self.HasGUI:
        import olex_gui
        r = olex_gui.GetUserInput(1, "Please enter the structure composition", "")
        if not r:
          self.terminate = True
          return
        self.formula = r
      else:
        print('Please provide the structure composition')
        self.terminate = True
    if "olex2" not in self.program.name:
      self.shelx = self.which_shelx(self.program)
    args = self.method.pre_solution(self)
    if args:
      olex.m('reset ' + args)
    else:
      olx.Reset()

  def doHistoryCreation(self):
    OV.SetParam('snum.refinement.last_R1', 'Solution')
    OV.SetParam('snum.refinement.last_wR2', 'Solution')
    self.his_file = hist.create_history(solution=True)
    OV.SetParam('snum.solution.current_history', self.his_file)
    return self.his_file


class RunRefinementPrg(RunPrg):
  running = None
  def __init__(self):
    RunPrg.__init__(self)
    self.bitmap = 'refine'
    self.program, self.method = self.getProgramMethod('refine')
    if self.program is None or self.method is None:
      return

    self.refinement_observer_timer = 0
    self.refinement_has_failed = None

    OV.registerCallback("procout", self.refinement_observer)
    self.run()
    OV.unregisterCallback("procout", self.refinement_observer)
    if OV.HasGUI():
      if self.refinement_has_failed:
        bg = red
        fg = white
        if "warning" in self.refinement_has_failed.lower():
          bg = orange
        gui.set_notification("%s;%s;%s" %(self.refinement_has_failed,bg,fg))
      elif OV.GetParam('snum.NoSpherA2.use_aspherical') == False:
        gui.get_default_notification(txt="Refinement Finished",
          txt_col='green_text')
      else:
        gui.get_default_notification(
          txt="Refinement Finished<br>Please Cite NoSpherA2: DOI 10.1039/D0SC05526C",
          txt_col='green_text')

  def run(self):
    if RunRefinementPrg.running:
      print("Already running. Please wait...")
      return False
    RunRefinementPrg.running = self
    use_aspherical = OV.GetParam('snum.NoSpherA2.use_aspherical')
    calculate_aspherical = OV.GetParam('snum.NoSpherA2.Calculate')
    result = False
    try:
      if use_aspherical == True:
        make_fcf_only = OV.GetParam('snum.NoSpherA2.make_fcf_only')
        if make_fcf_only == True:
          self.make_fcf()
        else:
          result = self.deal_with_AAFF()
      else:
        self.startRun()
        try:
          self.setupRefine()
          OV.File(u"%s/%s.ins" %(OV.FilePath(),self.original_filename))
          self.setupFiles()
        except Exception as err:
          sys.stderr.formatExceptionInfo()
          print(err)
          self.endRun()
          return False
        if self.terminate:
          self.endRun()
          return
        if self.params.snum.refinement.graphical_output and self.HasGUI:
          self.method.observe(self)
        RunPrg.run(self)
    except:
      self.terminate = True
    finally:
      if result == False:
        self.terminate = True
        if use_aspherical == True:
          if self.refinement_has_failed != None:
            self.refinement_has_failed = self.refinement_has_failed + " and Error during NoSpherA2!"
          else:
            self.refinement_has_failed = "Error during NoSpherA2 causing an exception!"
      RunRefinementPrg.running = None


  def setupRefine(self):
    self.method.pre_refinement(self)
    self.shelx = self.which_shelx(self.program)
    if self.params.snum.refinement.auto.assignQ:
      _ = olexex.get_auto_q_peaks()
      self.params.snum.refinement.max_peaks = _
      OV.SetParam('snum.refinement.max_peaks', _)
      import programSettings
      programSettings.onMaxPeaksChange(_)
    if olx.LSM().upper() == "CGLS" and olx.Ins("ACTA") != "n/a":
      olx.DelIns("ACTA")

  def doAutoTidyBefore(self):
    olx.Clean('-npd -aq=0.1 -at')
    if self.params.snum.refinement.auto.assignQ:
      olx.Sel('atoms where xatom.peak>%s' %self.params.snum.refinement.auto.assignQ)
      olx.Name('sel C')
    if self.params.snum.refinement.auto.pruneU:
      i = 0
      uref = 0
      for i in xrange(int(olx.xf.au.GetAtomCount())):
        ueq = float(olx.xf.au.GetAtomUiso(i))
        if uref:
          if uref == ueq:
            continue
          else:
            olx.Sel('atoms where xatom.uiso>%s' %self.params.snum.refinement.auto.pruneU)
            olx.Kill('sel')
            break
        else:
          uref = ueq
    try:
      pass
      olx.Clean('-npd -aq=0.1 -at')
    except:
      pass

  def doAutoTidyAfter(self):
    auto = self.params.snum.refinement.auto
    olx.Clean('-npd -aq=0.1 -at')
    if self.tidy:
      olx.Sel('atoms where xatom.uiso>0.07')
      olx.Sel('atoms where xatom.peak<2&&xatom.peak>0')
      olx.Kill('sel')
    if self.isAllQ:
      olx.Sel('atoms where xatom.uiso>0.07')
      olx.Kill('sel')
    if auto.pruneQ:
      olx.Sel('atoms where xatom.peak<%.3f&&xatom.peak>0' %float(auto.pruneQ))
      olx.Kill('sel')
      #olx.ShowQ('a true') # uncomment me!
      #olx.ShowQ('b true') # uncomment me!
    if auto.pruneU:
      olx.Sel('atoms where xatom.uiso>%s' %auto.pruneU)
      olx.Kill('sel')
    if auto.assignQ:
      olx.Sel('atoms where xatom.peak>%s' %auto.assignQ)
      olx.Name('sel C')
      olx.Sel('-u')
    if auto.assemble == True:
      olx.Compaq(a=True)
      olx.Move()
    else:
      pass
      olx.Clean('-npd -aq=0.1 -at')

  def runAfterProcess(self):
    RunPrg.runAfterProcess(self)
    if timer:
      t = time.time()
    self.method.post_refinement(self)
    if timer:
      print("-- self.method.post_refinement(self): %.3f" %(time.time()-t))

    delete_stale_fcf()

    if timer:
      t = time.time()
    self.post_prg_html()
    self.doHistoryCreation()
    if timer:
      print("-- self.method.post_refinement(self): %3f" %(time.time()-t))

    if self.R1 == 'n/a':
      return

    if self.params.snum.refinement.auto.tidy:
      self.doAutoTidyAfter()
      OV.File()
    if OV.GetParam('snum.refinement.check_absolute_structure_after_refinement'):
      try:
        self.isInversionNeeded(force=self.params.snum.refinement.auto.invert)
      except Exception as e:
        print("Could not determine whether structure inversion is needed: %s" %e)
    OV.SetParam('snum.init.skip_routine', False)
    OV.SetParam('snum.current_process_diagnostics','refinement')

    if timer:
      t = time.time()
    if self.params.snum.refinement.cifmerge_after_refinement:
      try:
        MergeCif(edit=False, force_create=False, evaluate_conflicts=False)
      except Exception as e:
        if debug:
          sys.stdout.formatExceptionInfo()
        print("Failed in CifMerge: '%s'" %str(e))
    if timer:
      print("-- MergeCif: %.3f" %(time.time()-t))


  def refinement_observer(self, msg):
    if self.refinement_observer_timer == 0:
      self.refinement_observer_timer = time.time()
    #if time.time() - self.refinement_observer_timer  < 2:
      #return
    if "BAD AFIX CONNECTIVITY" in msg or "ATOM FOR AFIX" in msg:
      self.refinement_has_failed = "Hydrogens"
    elif "REFINEMNET UNSTABLE" in msg:
      self.refinement_has_failed = "Unstable"
    elif "???????" in msg:
      self.refinement_has_failed = "ShelXL Crashed!"
    elif "** " in msg:
      import re
      regex = re.compile(r"\*\*(.*?)\*\*")
      m = regex.findall(msg)
      if m:
        self.refinement_has_failed = m[0].strip()


  def doHistoryCreation(self):
    R1 = 0
    self.his_file = ""

    if olx.IsVar('cctbx_R1') == 'true':
      R1 = float(olx.GetVar('cctbx_R1'))
      olx.UnsetVar('cctbx_R1')
      wR2 = float(olx.GetVar('cctbx_wR2'))
      olx.UnsetVar('cctbx_wR2')

    else:
      try:
        R1 = float(olx.Lst('R1'))
        wR2 = float(olx.Lst('wR2'))
      except:
        pass

    if R1:
      OV.SetParam('snum.refinement.last_R1', str(R1))
      OV.SetParam('snum.refinement.last_wR2',wR2)
      if not self.params.snum.init.skip_routine:
        try:
          self.his_file = hist.create_history()
        except Exception as ex:
          sys.stderr.write("History could not be created\n")
          if debug:
            sys.stderr.formatExceptionInfo()
      else:
        print ("Skipping History")
      self.R1 = R1
      self.wR2 = wR2
    else:
      self.R1 = self.wR2 = "n/a"
      self.his_file = None
      print("The refinement has failed, no R value was returned by the refinement")
    OV.SetParam('snum.refinement.current_history', self.his_file)
    return self.his_file, self.R1

  def isInversionNeeded(self, force=False):
    if self.params.snum.init.skip_routine:
      print ("Skipping absolute structure validation")
      return
    if olex_core.SGInfo()['Centrosymmetric'] == 1: return
    from cctbx_olex_adapter import hooft_analysis
    from libtbx.utils import format_float_with_standard_uncertainty
    from cctbx import sgtbx
    from libtbx.utils import Sorry
    if debug:
      print("Checking absolute structure...")
    inversion_needed = False
    possible_racemic_twin = False
    inversion_warning = "WARNING: Structure should be inverted (inv -f), unless there is a good reason not to do so."
    racemic_twin_warning = "WARNING: Structure may be an inversion twin"
    flack = self.method.getFlack()

    hooft_display = flack_display = ""

    try:
      hooft = hooft_analysis()
    except Sorry as e:
      print(e)
    else:
      if hooft.reflections.f_sq_obs_filtered.anomalous_flag():
        s = format_float_with_standard_uncertainty(
          hooft.hooft_y, hooft.sigma_y)
        hooft_display = "Hooft y: %s" %s
        OV.SetParam('snum.refinement.hooft_str', s)
        if (hooft.p3_racemic_twin is not None and
            round(hooft.p3_racemic_twin, 3) == 1):
          possible_racemic_twin = True
        elif hooft.p2_false is not None and round(hooft.p2_false, 3) == 1:
          inversion_needed = True
      else:
        OV.SetParam('snum.refinement.hooft_str', None)

    if flack:
      flack_display = "Flack x: %s" %flack
      fs = flack.split("(")
      flack_val = float(fs[0])
      if flack_val > 0.8:
        inversion_needed = True

    print("%s, %s" %(hooft_display, flack_display))

    if force and inversion_needed:
      olex.m('Inv -f')
      OV.File('%s.res' %OV.FileName())
      OV.SetParam('snum.refinement.auto.invert',False)
      print("The Structure has been inverted")
    elif inversion_needed:
      print(inversion_warning)
    if possible_racemic_twin:
      if (hooft.twin_components is not None and
          hooft.twin_components[0].twin_law != sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1))):
        print(racemic_twin_warning)
    if not inversion_needed and not possible_racemic_twin:
      #print "OK"
      pass

  def mask_and_fab(self):
    if not OV.GetParam("snum.refinement.use_solvent_mask"):
      return None

    import cctbx_olex_adapter
    #from iotbx.shelx import hklf
    modified_hkl_path = "%s/%s-mask.hkl" %(OV.FilePath(), OV.FileName())
    if OV.HKLSrc():
      fab_path = ".".join(OV.HKLSrc().split(".")[:-1]) + ".fab"
    method = "smbtx"
    if "_sqeeze" in fab_path:
      method="SQUEEZE"
    f_mask, f_model = None, None
    # backward compatibility - just in case
    if not OV.HKLSrc() == modified_hkl_path:
      olx.SetVar('snum.masks.original_hklsrc', OV.HKLSrc())
    else:
      olx.SetVar('snum.masks.original_hklsrc', '')
    if OV.GetParam("snum.refinement.recompute_mask_before_refinement") or not os.path.exists(fab_path):
      if OV.HKLSrc() == modified_hkl_path:
        _ = "You can't calculate a mask on an already masked file!"
        OlexVFS.write_to_olex('mask_notification.htm',_)
        raise Exception(_)
      if method == "SQUEEZE":
        olex.m("spy.OlexPlaton(q)")
        return
      cctbx_olex_adapter.OlexCctbxMasks()
      if olx.current_mask.flood_fill.n_voids() > 0:
        f_mask = olx.current_mask.f_mask()
        f_model = olx.current_mask.f_model()
      else:
        _ = "There are no voids!"
        print(_)
        OV.SetParam("snum.refinement.use_solvent_mask", False)
        olex.m('delins ABIN')
        OlexVFS.write_to_olex('mask_notification.htm',_,1)

    if f_mask is not None:
      cctbx_adapter = cctbx_olex_adapter.OlexCctbxAdapter()
      fo2 = cctbx_adapter.reflections.f_sq_obs_filtered
      if f_mask.size() < fo2.size():
        f_model = f_model.generate_bijvoet_mates().customized_copy(
          anomalous_flag=fo2.anomalous_flag()).common_set(fo2)
        f_mask = f_mask.generate_bijvoet_mates().customized_copy(
          anomalous_flag=fo2.anomalous_flag()).common_set(fo2)
      elif f_mask.size() > fo2.size():
        # this could happen with omit instruction
        f_mask = f_mask.common_set(fo2)
        f_model = f_model.common_set(fo2)
        if f_mask.size() != fo2.size():
          raise RuntimeError("f_mask array doesn't match hkl file")
    if f_mask is not None:
      with open(fab_path, "w") as f:
        for i,h in enumerate(f_mask.indices()):
          line = "%d %d %d " %h + "%.4f %.4f" % (f_mask.data()[i].real, f_mask.data()[i].imag)
          print >> f, line
        print >> f, "0 0 0 0.0 0.0"
      return f_mask

  def make_fcf(self):
    from refinement import FullMatrixRefine
    table = str(OV.GetParam('snum.NoSpherA2.file'))
    self.startRun()
    try:
      self.setupRefine()
      OV.File(u"%s/%s.ins" %(OV.FilePath(),self.original_filename))
      self.setupFiles()
    except Exception as err:
      sys.stderr.formatExceptionInfo()
      print(err)
      self.endRun()
      return False
    if self.terminate:
      self.endRun()
      return
    if self.params.snum.refinement.graphical_output and self.HasGUI:
      self.method.observe(self)
    FM = FullMatrixRefine(
          max_cycles=0,
          max_peaks=1)
    ne = FM.run(False,table)

    fcf_cif, fmt_str = FM.create_fcf_content(list_code = 6)
    with open(OV.file_ChangeExt(OV.FileFull(), 'fcf'), 'w') as f:
      fcf_cif.show(out=f, loop_format_strings={'_refln':fmt_str})
    return

  def deal_with_AAFF(self):
    from cctbx import adptbx

    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
    old_model = OlexRefinementModel()
    converged = False
    run = 0
    HAR_log = open("%s/%s.NoSpherA2" %(OV.FilePath(),self.original_filename),"w")
    HAR_log.write("NoSpherA2 in Olex2 for structure %s\n" %(OV.ModelSrc()))
    HAR_log.write("\n")
    import datetime
    HAR_log.write("Refinement startet at: ")
    HAR_log.write(str(datetime.datetime.now()))
    HAR_log.write("\n")
    HAR_log.write("Cycle     SCF Energy    Max shift:  xyz/ESD   Label   Uij/ESD     Label    R1    wR2\n")
    HAR_log.write("************************************************************************************\n")

    HAR_log.write("{:3d}".format(run))
    energy = None
    for file in os.listdir(olx.FilePath()):
      if file.endswith(".wfn"):
        with open(file) as f:
          fread = f.readlines()
          for line in fread:
            if "THE VIRIAL" in line:
              source = OV.GetParam('snum.NoSpherA2.source')
              if "Gaussian" in source:
                try:
                  energy = float(line.split()[3])
                except:
                  energy = None
              else:
                try:
                  energy = float(line.split()[4])
                except:
                  energy = None
    if energy == None:
      HAR_log.write("{:^24.10}".format(" "))
    else:
      HAR_log.write("{:^24.10f}".format(energy))
    HAR_log.write("{:>44.4}".format(" "))
    r1_old  = OV.GetParam('snum.refinement.last_R1')
    wr2_old = OV.GetParam('snum.refinement.last_wR2')
    if r1_old != "n/a":
      HAR_log.write("{:>6.2f}".format(float(r1_old)*100))
    else:
      HAR_log.write("{:>6}".format("N/A"))
    if wr2_old != "n/a":
      HAR_log.write("{:>7.2f}".format(float(wr2_old)*100))
    else:
      HAR_log.write("{:>7}".format("N/A"))
    HAR_log.write("\n")
    HAR_log.flush()

    max_cycles = int(OV.GetParam('snum.NoSpherA2.Max_HAR_Cycles'))
    calculate = OV.GetParam('snum.NoSpherA2.Calculate')
    source = OV.GetParam('snum.NoSpherA2.source')
    if calculate == True:
      if OV.GetParam('snum.NoSpherA2.h_aniso') == True:
        olx.Anis("$H", h=True)
      if OV.GetParam('snum.NoSpherA2.h_afix') == True:
        olex.m("Afix 0 $H")
    olex.m('delins list')
    olex.m('addins LIST -6')
    add_disp = OV.GetParam('snum.NoSpherA2.add_disp')
    if add_disp is True:
      olex.m('gendisp -source=sasaki')

    while converged == False:
      run += 1
      HAR_log.write("{:3d}".format(run))

      old_model = OlexRefinementModel()
      OV.SetVar('Run_number',run)

      #Calculate Wavefunction
      try:
        from NoSpherA2.NoSpherA2 import NoSpherA2_instance as nsp2
        nsp2.launch()
      except NameError as error:
        print("Error during NoSpherA2:")
        print(error)
        RunRefinementPrg.running = None
        RunRefinementPrg.Terminate = True
        return False
      Error_Status = OV.GetVar('NoSpherA2-Error')
      if Error_Status != "None":
        print("Error in NoSpherA2: %s" %Error_Status)
        return False
      dir = olx.FilePath()
      tsc_exists = False
      wfn_file = None
      for file in os.listdir(olx.FilePath()):
        if file.endswith(".tsc"):
          tsc_exists = True
        elif file.endswith(".wfn"):
          wfn_file = file
      if tsc_exists == False:
        print("Error during NoSpherA2")
        RunRefinementPrg.running = None
        return False

      # get energy from wfn file
      energy = None
      if (wfn_file != None) and (calculate == True):
        with open(wfn_file) as f:
          fread = f.readlines()
          for line in fread:
            if "THE VIRIAL" in line:
              source = OV.GetParam('snum.NoSpherA2.source')
              if "Gaussian" in source:
                energy = float(line.split()[3])
              elif "ORCA" in source:
                energy = float(line.split()[4])
              elif "pySCF" in source:
                energy = float(line.split()[4])
              elif ".wfn" in source:
                energy = 0.0
              elif "Tonto" in source:
                energy = float(line.split()[4])
              else:
                energy = 0.0
        if energy is not None:
          HAR_log.write("{:^24.10f}".format(energy))
        fread = None
      else:
        HAR_log.write("{:24}".format(" "))

      if OV.GetParam('snum.NoSpherA2.run_refine') == True:
        # Run Least-Squares
        self.startRun()
        try:
          self.setupRefine()
          OV.File(u"%s/%s.ins" %(OV.FilePath(),self.original_filename))
          self.setupFiles()
        except Exception as err:
          sys.stderr.formatExceptionInfo()
          print(err)
          self.endRun()
          return False
        if self.terminate:
          self.endRun()
          return
        if self.params.snum.refinement.graphical_output and self.HasGUI:
          self.method.observe(self)
        RunPrg.run(self)
      else:
        break

      new_model=OlexRefinementModel()

      max_dxyz = 0
      max_duij = 0
      max_shift_atom_xyz = 0
      matrix_run_max_shift_xyz = 0
      max_shift_atom_uij = 0
      matrix_run_max_shift_uij = 0

      try:
        jac_tr = self.cctbx.normal_eqns.reparametrisation.jacobian_transpose_matching_grad_fc()
        from scitbx.array_family import flex
        cov_matrix = flex.abs(flex.sqrt(self.cctbx.normal_eqns.covariance_matrix().matrix_packed_u_diagonal()))
        esds = jac_tr.transpose() * flex.double(cov_matrix)
        jac_tr = None
        annotations = self.cctbx.normal_eqns.reparametrisation.component_annotations
      except:
        print ("Could not obtain cctbx object and calculate ESDs!\n")
        return False
      matrix_run = 0
      label_uij = None
      label_xyz = None
      for i, atom in enumerate(new_model._atoms):
        xyz = atom['crd'][0]
        xyz2 = old_model._atoms[i]['crd'][0]
        for x in range(3):
          # if parameter is fixed and therefore has 0 esd
          if esds[matrix_run] > 0:
            if abs(xyz[x] - xyz2[x])/esds[matrix_run] > max_dxyz:
              max_dxyz = abs(xyz[x] - xyz2[x])/esds[matrix_run]
              label_xyz = annotations[matrix_run]
              max_shift_atom_xyz = abs(xyz[x] - xyz2[x])
              matrix_run_max_shift_xyz = matrix_run
          matrix_run += 1
        has_adp_new = new_model._atoms[i].get('adp')
        has_adp_old = old_model._atoms[i].get('adp')
        if has_adp_new != None and has_adp_old != None:
          adp = atom['adp'][0]
          adp2 = old_model._atoms[i]['adp'][0]
          adp = adptbx.u_cart_as_u_cif(self.cctbx.normal_eqns.xray_structure.unit_cell(), adp)
          adp2 = adptbx.u_cart_as_u_cif(self.cctbx.normal_eqns.xray_structure.unit_cell(), adp2)
          adp_esds = (esds[matrix_run],esds[matrix_run+1],esds[matrix_run+2],esds[matrix_run+3],esds[matrix_run+4],esds[matrix_run+5])
          adp_esds = adptbx.u_star_as_u_cif(self.cctbx.normal_eqns.xray_structure.unit_cell(), adp_esds)
          for u in range(6):
            # if parameter is fixed and therefore has 0 esd
            if esds[matrix_run] > 0:
              if abs(adp[u] - adp2[u])/adp_esds[u] > max_duij:
                max_duij = abs(adp[u] - adp2[u])/adp_esds[u]
                label_uij = annotations[matrix_run]
                max_shift_atom_uij = abs(adp[u] - adp2[u])
                matrix_run_max_shift_uij = matrix_run
            matrix_run += 1
          if matrix_run < len(annotations):
            if "C111" in annotations[matrix_run]:
              matrix_run += 25
        elif has_adp_new != None:
          matrix_run += 6
        elif has_adp_old == None:
          adp = atom['uiso'][0]
          adp2 = old_model._atoms[i]['uiso'][0]
          adp_esd = esds[matrix_run]
          if esds[matrix_run] > 0:
            if abs(adp - adp2)/adp_esd > max_duij:
              max_duij = abs(adp - adp2)/adp_esd
              label_uij = annotations[matrix_run]
              max_shift_atom_uij = abs(adp - adp2)
              matrix_run_max_shift_uij = matrix_run
          matrix_run += 1
        if matrix_run < len(annotations):
          if 'occ' in annotations[matrix_run]:
            matrix_run += 1
      HAR_log.write("{:>16.4f}".format(max_dxyz))
      if label_xyz != None:
        HAR_log.write("{:>8}".format(label_xyz))
      else:
        HAR_log.write("{:>8}".format("N/A"))

      HAR_log.write("{:>10.4f}".format(max_duij))
      if label_uij != None:
        HAR_log.write("{:>10}".format(label_uij))
      else:
        HAR_log.write("{:>10}".format("N/A"))

      r1  = OV.GetParam('snum.refinement.last_R1')
      wr2 = OV.GetParam('snum.refinement.last_wR2')

      HAR_log.write("{:>6.2f}".format(float(r1)*100))
      HAR_log.write("{:>7.2f}".format(float(wr2)*100))

      HAR_log.write("\n")
      HAR_log.flush()


      if calculate == False:
        converged = True
        break
      elif Full_HAR == False:
        converged = True
        break
      elif (max_duij <= 0.01) and (max_dxyz <= 0.01):
        converged = True
        break
      elif run == max_cycles:
        break
      elif r1_old != "n/a":
        if (float(r1) > float(r1_old) + 0.1) and (run > 1):
          HAR_log.write("      !! R1 increased by more than 0.1, aborting before things explode !!\n")
          break
      else:
        r1_old = r1
        wr2_old = wr2

    # Done with the while !Converged
    OV.SetParam('snum.NoSpherA2.Calculate',False)
    if converged == False:
      HAR_log.write(" !!! WARNING: UNCONVERGED MODEL! PLEASE INCREASE MAX_CYCLE OR CHECK FOR MISTAKES IN INPUT !!!\n")
      self.refinement_has_failed= "Warning: Unconverged Model!"
    if "DISCAMB" in source:
      unknown_sources = False
      with open(os.path.join("olex2","Wfn_job","discamb2tsc.log")) as discamb_log:
        for i in discamb_log.readlines():
          if "unassigned atom types" in i:
            unknown_sources = True
          if unknown_sources == True:
            HAR_log.write(i)
      if unknown_sources == True:
        HAR_log.write("                   !!! WARNING: Unassigned Atom Types! !!!\n")
        if self.refinement_has_failed != None:
          self.refinement_has_failed = self.refinement_has_failed + " and unassigned Atom Types!"
        else:
          self.refinement_has_failed = "Unassigned Atom Types!"
    HAR_log.write("************************************************************************************\n")
    HAR_log.write("Residual density Max:{:+8.3f}\n".format(OV.GetParam('snum.refinement.max_peak')))
    HAR_log.write("Residual density Min:{:+8.3f}\n".format(OV.GetParam('snum.refinement.max_hole')))
    HAR_log.write("Goodness of Fit:     {:8.4f}\n".format(OV.GetParam('snum.refinement.goof')))
    HAR_log.write("Refinement finished at: ")
    HAR_log.write(str(datetime.datetime.now()))
    HAR_log.write("\n")

    precise = OV.GetParam('snum.NoSpherA2.precise_output')
    if precise == True:
      matrix_run = 0
      label_uij = None
      label_xyz = None
      old_model = OlexRefinementModel()
      HAR_log.write("\n\n\nPositions:\n")
      for i, atom in enumerate(old_model._atoms):
        xyz = atom['crd'][0]
        HAR_log.write("{:5}".format(atom['label'][0]))
        for x in range(3):
          HAR_log.write("{:12.8f}".format(xyz[x]))
        HAR_log.write("\n")
        HAR_log.write("{:5}".format(" "))
        for x in range(3):
          HAR_log.write("{:12.8f}".format(esds[matrix_run]))
          matrix_run += 1
        has_adp_old = old_model._atoms[i].get('adp')
        if has_adp_old != None:
          matrix_run += 6
        else:
          matrix_run += 1
        HAR_log.write("\n")
      matrix_run = 0
      HAR_log.write("\n\nADPs      (11)        (22)        (33)        (23)        (13)        (12)\n")
      for i, atom in enumerate(old_model._atoms):
        has_adp = old_model._atoms[i].get('adp')
        HAR_log.write("{:5}".format(atom['label'][0]))
        if has_adp != None:
          adp = atom['adp'][0]
          adp = adptbx.u_cart_as_u_cif(self.cctbx.normal_eqns.xray_structure.unit_cell(), adp)
          matrix_run += 3
          for u in range(6):
            HAR_log.write("{:12.8f}".format(adp[u]))
          HAR_log.write("\n")
          HAR_log.write("{:5}".format(" "))
          adp_esds = (esds[matrix_run],esds[matrix_run+1],esds[matrix_run+2],esds[matrix_run+3],esds[matrix_run+4],esds[matrix_run+5])
          adp_esds = adptbx.u_star_as_u_cif(self.cctbx.normal_eqns.xray_structure.unit_cell(), adp_esds)
          for u in range(6):
            HAR_log.write("{:12.8f}".format(adp_esds[u]))
          matrix_run += 6
        else:
          HAR_log.write(" Isotropic atom")
          matrix_run += 4
        HAR_log.write("\n")

    HAR_log.flush()
    HAR_log.close()

    with open("%s/%s.NoSpherA2" %(OV.FilePath(),self.original_filename), 'r') as f:
      print(f.read())
    return True

def AnalyseRefinementSource():
  file_name = OV.ModelSrc()
  ins_file_name = olx.file.ChangeExt(file_name, 'ins')
  res_file_name = olx.file.ChangeExt(file_name, 'res')
  hkl_file_name = olx.file.ChangeExt(file_name, 'hkl')
  if olx.IsFileType('cif') == 'true':
    if os.path.exists(ins_file_name) or os.path.exists(res_file_name):
      olex.m('reap "%s"' %ins_file_name)
      hkl_file_name = os.path.join(os.getcwdu(), hkl_file_name)
      if os.path.exists(hkl_file_name):
        olx.HKLSrc(hkl_file_name)
        return True
      else:
        return False
    fn = os.path.normpath("%s/%s" %(olx.FilePath(), olx.xf.DataName(olx.xf.CurrentData())))
    ins_file_name = fn + '.ins'
    res_file_name = fn + '.res'
    hkl_file_name = fn + '.hkl'
    olex.m("export '%s'" %hkl_file_name)
    if os.path.exists(res_file_name):
      olex.m('reap "%s"' %res_file_name)
      print('Loaded RES file extracted from CIF')
    else:
      OV.File("%s" %ins_file_name)
      olex.m('reap "%s"' %ins_file_name)
      olex.m("free xyz,Uiso")
      print('Loaded INS file generated from CIF')
    if os.path.exists(hkl_file_name):
      olx.HKLSrc(hkl_file_name)
    else:
      print('HKL file is not in the CIF')
      return False
  return True

OV.registerFunction(AnalyseRefinementSource)
OV.registerFunction(RunRefinementPrg)
OV.registerFunction(RunSolutionPrg)

def delete_stale_fcf():
  fcf = os.path.join(OV.FilePath(), OV.FileName() + '.fcf')
  res = os.path.join(OV.FilePath(), OV.FileName() + '.res')
  if os.path.exists(fcf) and os.path.exists(fcf):
    if round(os.path.getmtime(fcf)*0.1) == round(os.path.getmtime(res)*0.1):
      return True
    else:
      print ("Deleting stale fcf: %s" %fcf)
      os.remove(fcf)
      if OV.HasGUI():
        import gui
        gui.set_notification("Stale<font color=$GetVar(gui.red)><b>fcf file</b></font>has been deleted.")