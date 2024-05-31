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

from olexFunctions import OV, SilentException

debug = OV.IsDebugging()
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
      e_str = str(e)
      if ("stoks.size() == scatterer" not in e_str)\
        and ("Error during building of normal equations using OpenMP" not in e_str)\
        and ("fsci != sc_map.end()" not in e_str):
        sys.stdout.formatExceptionInfo()
      else:
        print("Error!: ")
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
    OV.paramStack.push('snum.refinement.max_cycles')
    OV.paramStack.push('snum.refinement.max_peaks')
    olx.Freeze(True)
    try:
      olex.m('compaq')
      olex.m('compaq -a')
      olx.VSS(True)
      olex.m('compaq')
      olex.m('refine 2 10')
      olex.m('compaq')
      olx.ATA()
      olex.m('refine 2 10')
    finally:
      olx.Freeze(False)
      OV.paramStack.pop(2)

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
      extensions = ['res', 'lst', 'cif', 'fcf', 'mat', 'pdb', 'lxt']
      if "xt" in self.program.name.lower():
        extensions.append('hkl')
      if "srv" in self.program.name.lower():
        extensions.append('npy')
        extensions.append('log')
      if self.broadcast_mode:
        self.doBroadcast()
      for ext in extensions:
        if timer:
          t = time.time()
        if "xt" in self.program.name.lower() and ext != 'lst' and ext != 'lxt':
          copy_from = "%s/%s_a.%s" %(self.tempPath, self.shelx_alias, ext)
        else:
          copy_from = "%s/%s.%s" %(self.tempPath, self.shelx_alias, ext)
        copy_to = "%s/%s.%s" %(self.filePath, self.original_filename, ext)
        if os.path.isfile(copy_from) and\
          copy_from.lower() != copy_to.lower(): # could this ever be true??
          shutil.copyfile(copy_from, copy_to)
        if timer:
          pass
          #print "---- copying %s: %.3f" %(copy_from, time.time() -t)
    finally:
      OV.deleteFileLock(file_lock)

  def doHistoryCreation(self, type="normal"):
    return

  def setupFiles(self):
    olx.User("%s" %OV.FilePath())
    self.filePath = OV.FilePath()
    self.fileName = OV.FileName()
    self.tempPath = os.path.join(OV.StrDir(), "temp")

    ## clear temp folder to avoid problems
    if os.path.exists(self.tempPath):
      if self.program.name != "olex2.refine":
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
    if self.program.name == "olex2.refine":
      return

    if not os.path.exists(self.tempPath):
      os.mkdir(self.tempPath)

    if olx.xf.GetIncludedFiles():
      files = [(os.path.join(self.filePath, x),os.path.join(self.tempPath, x))
        for x in olx.xf.GetIncludedFiles().split('\n')]
    else:
      files = []
    if "srv" in self.program.name.lower():
      files.append((os.path.join(self.filePath, self.curr_file) + ".cif_od",
        os.path.join(self.tempPath, self.shelx_alias) + ".cif_od"))
      files.append((os.path.join(self.filePath, self.curr_file) + "_dyn.cif_cap",
        os.path.join(self.tempPath, self.shelx_alias) + "_dyn.cif_cap"))
      # create snum phil with current settings
      str_dir = os.path.join(self.tempPath, "olex2")
      if not os.path.exists(str_dir):
        os.mkdir(str_dir)
      olx.phil_handler.save_param_file(
        file_name=os.path.join(str_dir, self.shelx_alias) + ".phil",
        scope_name='snum', diff_only=True)

      model_src = OV.ModelSrc(force_cif_data=True)
      metacif_path = os.path.join(OV.StrDir(), model_src) + ".metacif"
      if os.path.exists(metacif_path):
        files.append((metacif_path,
          os.path.join(str_dir, self.shelx_alias) + ".metacif"))


    files.append((self.hkl_src,
      os.path.join(self.tempPath, self.shelx_alias) + ".hkl"))
    files.append((os.path.join(self.filePath, self.curr_file) + ".ins",
      os.path.join(self.tempPath, self.shelx_alias) + ".ins"))
    files.append((os.path.splitext(self.hkl_src)[0] + ".fab",
      os.path.join(self.tempPath, self.curr_file) + ".fab"))
    for f in files:
      if os.path.exists(f[0]) and not os.path.exists(f[1]):
        shutil.copyfile(f[0], f[1])

  def runAfterProcess(self):
    if self.program.name != "olex2.refine":
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
          if "Y" not in r: # N/C
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
    if OV.isRemoteMode():
      return None
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
    self.refinement_has_failed = []

    OV.registerCallback("procout", self.refinement_observer)
    self.run()
    OV.unregisterCallback("procout", self.refinement_observer)
    if self.refinement_has_failed:
      bg = red
      fg = white
      msg = " | ".join(self.refinement_has_failed)
      if "warning" in msg.lower():
        bg = orange
      gui.set_notification("%s;%s;%s" % (msg, bg, fg))
    elif 'srv' in self.program.name:
      rc_fn = os.path.join(self.tempPath, "olex2", "refinement.check")
      if os.path.exists(rc_fn):
        gui.set_notification(open(rc_fn, "r").read())
    elif not OV.IsNoSpherA2():
      gui.get_default_notification(txt="Refinement Finished",
        txt_col='green_text')
    else:
      gui.get_default_notification(
        txt="Refinement Finished<br>Please Cite NoSpherA2: DOI 10.1039/D0SC05526C",
          txt_col='green_text')

  def reset_params(self):
    OV.SetParam('snum.refinement.hooft_str', "")
    OV.SetParam('snum.refinement.flack_str', "")
    OV.SetParam('snum.refinement.parson_str', "")

  def run(self):
    if RunRefinementPrg.running:
      print("Already running. Please wait...")
      return False
    RunRefinementPrg.running = self
    self.reset_params()
    use_aspherical = OV.IsNoSpherA2()
    result = False
    try:
      if use_aspherical == True:
        make_fcf_only = OV.GetParam('snum.NoSpherA2.make_fcf_only')
        if make_fcf_only == True:
          from aaff import make_fcf
          result = make_fcf(self)
        else:
          result = self.method.deal_with_AAFF(self)
      else:
        self.startRun()
        try:
          self.setupRefine()
          OV.File("%s/%s.ins" %(OV.FilePath(),self.original_filename))
          self.setupFiles()
        except Exception as err:
          sys.stderr.formatExceptionInfo()
          self.endRun()
          return False
        if self.terminate:
          self.endRun()
          return
        if self.params.snum.refinement.graphical_output and self.HasGUI:
          self.method.observe(self)
        RunPrg.run(self)
    except Exception as err:
      sys.stderr.formatExceptionInfo()
      self.terminate = True
    finally:
      if result == False:
        self.terminate = True
        if use_aspherical == True:
          self.refinement_has_failed.append("Error during NoSpherA2")
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
      for i in range(int(olx.xf.au.GetAtomCount())):
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
    if self.terminate:
      return
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
    if OV.GetParam('snum.refinement.check_absolute_structure_after_refinement') and\
      not OV.IsEDRefinement():
      try:
        self.isInversionNeeded(force=self.params.snum.refinement.auto.invert)
      except Exception as e:
        print("Could not determine whether structure inversion is needed: %s" % e)
    if self.program.name == "olex2.refine":
      from refinement_checks import RefinementChecks
      rc = RefinementChecks(self.cctbx)
      if OV.GetParam('snum.refinement.check_PDF'):
        try:
          rc.check_PDF(force=self.params.snum.refinement.auto.remove_anharm)
        except Exception as e:
          print("Could not check PDF: %s" % e)
      rc.check_disp()
      rc.check_occu()
      rc.check_mu() #This is the L-M mu!
      self.refinement_has_failed = rc.refinement_has_failed

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
      self.refinement_has_failed.append("Hydrogens")
    elif "REFINEMNET UNSTABLE" in msg:
      self.refinement_has_failed.append("Unstable")
    elif "???????" in msg:
      self.refinement_has_failed.append("ShelXL Crashed!")
    elif "** " in msg:
      import re
      regex = re.compile(r"\*\*(.*?)\*\*")
      m = regex.findall(msg)
      if m:
        self.refinement_has_failed.append(m[0].strip())

  def doHistoryCreation(self):
    R1 = 0
    self.his_file = ""
    wR2 = 0
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
      if not (self.params.snum.init.skip_routine or OV.IsRemoteMode()):
        try:
          self.his_file = hist.create_history()
        except Exception as ex:
          sys.stderr.write("History could not be created\n")
          if debug:
            sys.stderr.formatExceptionInfo()
      else:
        print("Skipping History")
      self.R1 = R1
      self.wR2 = wR2
    else:
      self.R1 = self.wR2 = "n/a"
      self.his_file = None
      print("The refinement has failed, no R value was returned by the refinement")
    return self.his_file, self.R1

  def isInversionNeeded(self, force=False):
    if self.params.snum.init.skip_routine:
      print ("Skipping absolute structure validation")
      return
    if olex_core.SGInfo()['Centrosymmetric'] == 1: return
    from libtbx.utils import format_float_with_standard_uncertainty
    from cctbx import sgtbx
    if debug:
      print("Checking absolute structure...")
    inversion_needed = False
    possible_racemic_twin = False
    inversion_warning = "WARNING: Structure should be inverted (inv -f), unless there is a good reason not to do so."
    racemic_twin_warning = "WARNING: Structure may be an inversion twin"
    output = []
    flack = OV.GetParam('snum.refinement.flack_str')
    # check if the nversion twin refinement...
    if not flack:
      from cctbx.array_family import flex
      rm = olexex.OlexRefinementModel()
      twinning = rm.model.get('twin')
      if twinning is not None:
        twin_law = sgtbx.rot_mx([int(twinning['matrix'][j][i])
                    for i in range(3) for j in range(3)])
        if twin_law.as_double() == sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1)):
          flack = olx.xf.rm.BASF(0)
          OV.SetParam('snum.refinement.flack_str', flack)

    parson = OV.GetParam('snum.refinement.parson_str')

    hooft = self.method.getHooft()
    if hooft and hasattr(hooft, 'p3_racemic_twin'):
      if (hooft.p3_racemic_twin is not None and
          round(hooft.p3_racemic_twin, 3) == 1):
        possible_racemic_twin = True
      elif hooft.p2_false is not None and round(hooft.p2_false, 3) == 1:
        inversion_needed = True
      s = format_float_with_standard_uncertainty(
        hooft.hooft_y, hooft.sigma_y)
      output.append("Hooft y: %s" %s)
    elif flack or parson:
      value = parson
      if not value:
        value = flack
      fs = value.split("(")
      val = float(fs[0])
      if val != 0:
        error = float(fs[1][:-1])
        temp = val
        while abs(temp) < 1.0:
          temp *= 10
          error /= 10
        if val > 0.8 and val-error > 0.5:
          inversion_needed = True
    if parson:
      output.append("Parson's q: %s" %parson)
    if flack:
      output.append("Flack x: %s" %flack)

    print(', '.join(output))

    if force and inversion_needed:
      olex.m('Inv -f')
      OV.File('%s.res' %OV.FileName())
      OV.SetParam('snum.refinement.auto.invert',False)
      print("The Structure has been inverted")
    elif inversion_needed:
      print(inversion_warning)
    if possible_racemic_twin:
      if (hooft.olex2_adaptor.twin_components is not None and
          hooft.olex2_adaptor.twin_components[0].twin_law.as_double() != sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1))):
        print(racemic_twin_warning)

def AnalyseRefinementSource():
  file_name = OV.ModelSrc()
  ins_file_name = olx.file.ChangeExt(file_name, 'ins')
  res_file_name = olx.file.ChangeExt(file_name, 'res')
  hkl_file_name = olx.file.ChangeExt(file_name, 'hkl')
  if olx.IsFileType('cif') == 'true':
    if os.path.exists(ins_file_name) or os.path.exists(res_file_name):
      olex.m('reap "%s"' %ins_file_name)
      hkl_file_name = os.path.join(os.getcwd(), hkl_file_name)
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
  if os.path.exists(res) and os.path.exists(fcf):
    diff = abs(os.path.getmtime(fcf) - os.path.getmtime(res))
    # modified within 10 seconds
    if diff < 10:
      return False
    else:
      os.remove(fcf)
      print("Deleted stale fcf: %s (%ss old)" %(fcf, int(diff)))
      if OV.HasGUI():
        import gui
        gui.set_notification("Stale<font color=$GetVar(gui.red)><b>fcf file</b></font>has been deleted.")
      return True