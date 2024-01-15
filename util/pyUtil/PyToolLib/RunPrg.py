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
    import _ac6util
    file_lock = OV.createFileLock(os.path.join(self.filePath, self.original_filename))
    try:
      extensions = ['res', 'lst', 'cif', 'fcf', 'mat', 'pdb', 'lxt']
      if "xt" in self.program.name.lower():
        extensions.append('hkl')
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
          digests = None
          if copy_from.endswith(".hkl"):
            digests = OV.get_AC_digests()
            digests = _ac6util.onHKLChange(OV.HKLSrc(), copy_from, digests[0], digests[1])
          shutil.copyfile(copy_from, copy_to)
          if digests:
            digests = digests.split(',')
            OV.set_cif_item("_diffrn_oxdiff_ac3_digest_hkl", digests[0])
            if len(digests) > 1:
              OV.set_cif_item("_diffrn_oxdiff_ac6_digest_hkl_ed", digests[1])
            from CifInfo import SaveCifInfo
            SaveCifInfo()
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
    if 'olex2' not in self.program.name:
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
    if 'olex2' in self.program.name:
      return
    if olx.xf.GetIncludedFiles():
      files = [(os.path.join(self.filePath, x),os.path.join(self.tempPath, x))
        for x in olx.xf.GetIncludedFiles().split('\n')]
    else:
      files = []
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
    if OV.HasGUI():
      if self.refinement_has_failed:
        bg = red
        fg = white
        msg = " | ".join(self.refinement_has_failed)
        if "warning" in msg.lower():
          bg = orange
        gui.set_notification("%s;%s;%s" % (msg, bg, fg))
      elif OV.GetParam('snum.NoSpherA2.use_aspherical') == False:
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
          self.make_fcf()
        else:
          result = self.deal_with_AAFF()
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
    if self.program.name == 'olex2.refine':
      if OV.GetParam('snum.refinement.check_PDF'):
        try:
          self.check_PDF(force=self.params.snum.refinement.auto.remove_anharm)
        except Exception as e:
          print("Could not check PDF: %s" % e)
      self.check_disp()
      self.check_occu()
      self.check_mu() #This is the L-M mu!

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

  def check_PDF(self, force=False):
    RM = OlexRefinementModel()
    any_have_anh = False
    label_list = []
    for i, atom in enumerate(RM._atoms):
      anh_adp = atom.get('anharmonic_adp')
      if anh_adp == None:
        continue
      any_have_anh = True
      label_list.append(atom['label'])
    if any_have_anh == True:
      olex.m("PDF")
      problem = OV.GetVar("Negative_PDF")
      Kuhs = OV.GetVar("Kuhs_Rule")
      err_list = []
      if problem == True:
        err_list.append("Negative PDF found")
        if force == True:
          print("Making all anharmonic atoms hamrnoic again!")
          for label in label_list:
            print(label)
            olex.m("anis %s" % label)
      if Kuhs == True:
        err_list.append("Kuhs' rule not fulfilled")
      if err_list:
        self.refinement_has_failed.extend(err_list)

  def check_occu(self):
    scatterers = self.cctbx.normal_eqns.xray_structure.scatterers()
    wrong_occu = []
    for sc in scatterers:
      if sc.flags.grad_occupancy():
        if sc.occupancy < 0 or sc.occupancy > 1.0:
          wrong_occu.append(sc.label)
    if len(wrong_occu) != 0:
      if len(wrong_occu) == 1:    
        self.refinement_has_failed.append(f"{wrong_occu[0]} has unreasonable Occupancy")
      else:
        _ =  ",".join(wrong_occu)
        self.refinement_has_failed.append(f"{_} have unreasonable Occupancy")

  def check_disp(self):
    scatterers = self.cctbx.normal_eqns.xray_structure.scatterers()
    refined_disp = []
    for sc in scatterers:
      if sc.flags.grad_fp() or sc.flags.grad_fdp():
        fp, fdp = sc.fp, sc.fdp
        refined_disp.append((sc, fp, fdp))
    if refined_disp != []:
      wavelength = float(olx.xf.exptl.Radiation())
      from cctbx.eltbx import sasaki
      from cctbx.eltbx import henke
      from brennan import brennan
      tables = [sasaki, henke, brennan()]
      unreasonable_fp = []
      unreasonable_fdp = []
      for sc, fp, fdp in refined_disp:
        e = str(sc.element_symbol())
        table = []
        for t in tables:
          table.append(t.table(e))
        fp_min_max = [135.0, 0.0]
        fdp_min_max = [135.0, 0.0]
        fp_average = 0.0
        fdp_average = 0.0
        for t in table:
          temp = t.at_angstrom(wavelength)
          fp_average += temp.fp()
          fdp_average += temp.fdp()
          fp_min_max = [min(fp_min_max[0], temp.fp()), max(fp_min_max[1], temp.fp())]
          fdp_min_max = [min(fdp_min_max[0], temp.fdp()), max(fdp_min_max[1], temp.fdp())]
        fp_average /= len(tables)
        fdp_average /= len(tables)
        fpdiff = (fp_min_max[1] - fp_min_max[0])
        fdpdiff = (fdp_min_max[1] - fdp_min_max[0])
        if fp_average + 2 * fpdiff < fp or fp_average - 2 * fpdiff > fp:
          unreasonable_fp.append(sc.label)
        if fdp_average + 2 * fdpdiff < fdp or fdp_average - 2 * fdpdiff > fdp:
          unreasonable_fdp.append(sc.label)
      if len(unreasonable_fdp) != 0:
        if len(unreasonable_fdp) == 1:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: white'>%s has strongly deviating f''</a>" % unreasonable_fdp[0])
        else:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: white'>%s have strongly deviating f''</a>" % ",".join(unreasonable_fdp))
      if len(unreasonable_fp) != 0:
        if len(unreasonable_fp) == 1:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: white'>%s has strongly deviating f'</a>" % unreasonable_fp[0])
        else:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: white'>%s have strongly deviating f'</a>" % ",".join(unreasonable_fp))

  def check_mu(self):
    try:
      mu = self.cctbx.normal_eqns.iterations_object.mu
      if mu > 1E1:
        self.refinement_has_failed.append("Mu of LM is very large!")
    except AttributeError:
      return

  def make_fcf(self):
    from refinement import FullMatrixRefine
    table = str(OV.GetParam('snum.NoSpherA2.file'))
    self.startRun()
    try:
      self.setupRefine()
      OV.File("%s/%s.ins" %(OV.FilePath(),self.original_filename))
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
    HAR_log = None
    try:
      from cctbx import adptbx

      Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
      old_model = OlexRefinementModel()
      converged = False
      run = 0
      HAR_log = open("%s/%s.NoSpherA2" %(OV.FilePath(),self.original_filename),"w")
      HAR_log.write("NoSpherA2 in Olex2 for structure %s\n\n" %(OV.ModelSrc()))
      import datetime
      HAR_log.write("Refinement startet at: ")
      HAR_log.write(str(datetime.datetime.now())+"\n")
      HAR_log.write("Cycle     SCF Energy    Max shift:  xyz/ESD     Label   Uij/ESD       Label   Max/ESD       Label    R1    wR2\n"+"*" * 110 + "\n")
      HAR_log.write("{:3d}".format(run))
      energy = None
      source = OV.GetParam('snum.NoSpherA2.source')
      if "Please S" in source:
        olx.Alert("No tsc generator selected",\
  """Error: No generator for tsc files selected.
  Please select one of the generators from the drop-down menu.""", "O", False)
        OV.SetVar('NoSpherA2-Error',"TSC Generator unselected")
        return
      if energy == None:
        HAR_log.write("{:^24}".format(" "))
      else:
        HAR_log.write("{:^24.10f}".format(energy))
      HAR_log.write("{:>70}".format(" "))
      r1_old = OV.GetParam('snum.refinement.last_R1')
      wr2_old = OV.GetParam('snum.refinement.last_wR2')
      if r1_old != "n/a" and r1_old != None:
        HAR_log.write("{:>6.2f}".format(float(r1_old) * 100))
      else:
        HAR_log.write("{:>6}".format("N/A"))
      if wr2_old != "n/a" and wr2_old != None:
        HAR_log.write("{:>7.2f}".format(float(wr2_old) * 100))
      else:
        HAR_log.write("{:>7}".format("N/A"))
      HAR_log.write("\n")
      HAR_log.flush()

      max_cycles = int(OV.GetParam('snum.NoSpherA2.Max_HAR_Cycles'))
      calculate = OV.GetParam('snum.NoSpherA2.Calculate')
      if calculate == True:
        if OV.GetParam('snum.NoSpherA2.h_aniso') == True:
          olx.Anis("$H", h=True)
        if OV.GetParam('snum.NoSpherA2.h_afix') == True:
          olex.m("Afix 0 $H")
      add_disp = OV.GetParam('snum.NoSpherA2.add_disp')
      if add_disp is True:
        olex.m('gendisp -source=brennan -force')

      while converged == False:
        run += 1
        HAR_log.write("{:3d}".format(run))

        old_model = OlexRefinementModel()
        OV.SetVar('Run_number', run)
        self.refinement_has_failed = []

        #Calculate Wavefunction
        try:
          from NoSpherA2.NoSpherA2 import NoSpherA2_instance as nsp2
          v = nsp2.launch()
          if v == False:
            print("Error during NoSpherA2! Abnormal Ending of program!")
            HAR_log.close()
            return False
        except NameError as error:
          print("Error during NoSpherA2:")
          print(error)
          RunRefinementPrg.running = None
          RunRefinementPrg.Terminate = True
          HAR_log.close()
          return False
        Error_Status = OV.GetVar('NoSpherA2-Error')
        if Error_Status != "None":
          print("Error in NoSpherA2: %s" %Error_Status)
          return False
        tsc_exists = False
        wfn_file = None
        for file in os.listdir(olx.FilePath()):
          if file == os.path.basename(OV.GetParam('snum.NoSpherA2.file')):
            tsc_exists = True
          elif file.endswith(".wfn"):
            wfn_file = file
          elif file.endswith(".wfx"):
            wfn_file = file
          elif file.endswith(".gbw"):
            wfn_file = file
          elif file.endswith(".tscb"):
            tsc_exists = True
        if tsc_exists == False:
          print("Error during NoSpherA2: No .tsc file found")
          RunRefinementPrg.running = None
          HAR_log.close()
          return False

        # get energy from wfn file
        #TODO Check if WFN is new, otherwise skip this!
        energy = None
        if source == "fragHAR" or source == "Hybdrid" or source == "DISCAMB" or "MATTS" in source or "hakkar" in source:
          HAR_log.write("{:24}".format(" "))
        else:
          if (wfn_file != None) and (calculate == True):
            if ".gbw" not in wfn_file:
              with open(wfn_file, "rb") as f:
                f.seek(-2000, os.SEEK_END)
                fread = f.readlines()[-1].decode()
                if "THE VIRIAL" in fread:
                  source = OV.GetParam('snum.NoSpherA2.source')
                  if "Gaussian" in source:
                    energy = float(fread.split()[3])
                  elif "ORCA" in source:
                    energy = float(fread.split()[4])
                  elif "pySCF" in source:
                    energy = float(fread.split()[4])
                  elif ".wfn" in source:
                    energy = float(fread[17:38])
                  elif "Tonto" in source:
                    energy = float(fread.split()[4])
                  else:
                    energy = 0.0
            if energy is not None:
              HAR_log.write("{:^24.10f}".format(energy))
            else:
              HAR_log.write("{:24}".format(" "))
            fread = None
          else:
            HAR_log.write("{:24}".format(" "))

        if OV.GetParam('snum.NoSpherA2.run_refine') == True:
          # Run Least-Squares
          self.startRun()
          try:
            self.setupRefine()
            OV.File("%s/%s.ins" %(OV.FilePath(),self.original_filename))
            self.setupFiles()
          except Exception as err:
            sys.stderr.formatExceptionInfo()
            print(err)
            self.endRun()
            HAR_log.close()
            return False
          if self.terminate:
            self.endRun()
            return
          if self.params.snum.refinement.graphical_output and self.HasGUI:
            self.method.observe(self)
          try:
            RunPrg.run(self)
            f_obs_sq,f_calc = self.cctbx.get_fo_sq_fc(self.cctbx.normal_eqns.one_h_linearisation)
            if f_obs_sq != None and f_calc != None:
              nsp2.set_f_calc_obs_sq_one_h_linearisation(f_calc,f_obs_sq,self.cctbx.normal_eqns.one_h_linearisation)            
          except Exception as e:
            e_str = str(e)
            if ("stoks.size() == scatterer" in e_str):
              print("Insufficient number of scatterers in .tsc file!\nDid you forget to recalculate after adding or deleting atoms?")
            elif ("Error during building of normal equations using OpenMP" in e_str):
              print("Error initializing OpenMP refinement, try disabling it!")
            elif  ("fsci != sc_map.end()" in e_str):
              print("An Atom was not found in the .tsc file!\nHave you renamed some and not recalcualted the tsc file?")
            return
        else:
          break
        new_model=OlexRefinementModel()
        class results():
          def __init__(self):
            self.max_dxyz = 0
            self.max_duij = 0
            self.label_uij = None
            self.label_xyz = None
            self.r1 = 0
            self.wr2 = 0
            self.max_overall = 0
            self.label_overall = None
          def update_xyz(self, dxyz, label):
            if dxyz > self.max_dxyz:
              self.max_dxyz = dxyz
              self.label_xyz = label
              if dxyz > self.max_overall:
                self.max_overall = dxyz
                self.label_overall = label
          def update_uij(self, duij, label):
            if duij > self.max_duij:
              self.max_duij = duij
              self.label_uij = label
              if duij > self.max_overall:
                self.max_overall = duij
                self.label_overall = label
          def update_overall(self, d, label):
            if d > self.max_overall:
              self.max_overall = d
              self.label_overall = label

        try:
          jac_tr = self.cctbx.normal_eqns.reparametrisation.jacobian_transpose_matching_grad_fc()
          from scitbx.array_family import flex
          cov_matrix = flex.abs(flex.sqrt(self.cctbx.normal_eqns.covariance_matrix().matrix_packed_u_diagonal()))
          esds = jac_tr.transpose() * flex.double(cov_matrix)
          jac_tr = None
          annotations = self.cctbx.normal_eqns.reparametrisation.component_annotations
        except:
          HAR_log.close()
          print ("Could not obtain cctbx object and calculate ESDs!\n")
          return False
        from NoSpherA2.utilities import run_with_bitmap
        @run_with_bitmap('Analyzing shifts')
        def analyze_shifts(results):
          try:
            matrix_run = 0
            matrix_size = len(esds)
            uc = self.cctbx.normal_eqns.xray_structure.unit_cell()
            for i, atom in enumerate(new_model._atoms):
              xyz = atom['crd'][0]
              xyz2 = old_model._atoms[i]['crd'][0]
              assert matrix_run + 2 < matrix_size, "Inconsistent size of annotations and expected parameters!"
              if ".x" in annotations[matrix_run]:
                for x in range(3):
                  # if parameter is fixed and therefore has 0 esd
                  if esds[matrix_run] > 0:
                    res = abs(xyz[x] - xyz2[x]) / esds[matrix_run]
                    if res > results.max_dxyz:
                      results.update_xyz(res, annotations[matrix_run])
                  matrix_run += 1
              has_adp_new = atom.get('adp')
              has_adp_old = old_model._atoms[i].get('adp')
              has_anh_new = atom.get('anharmonic_adp')
              has_anh_old = old_model._atoms[i].get('anharmonic_adp')
              if has_adp_new != None and has_adp_old != None:
                assert matrix_run + 5 < matrix_size, "Inconsistent size of annotations and expected parameters!"
                adp = atom['adp'][0]
                adp = (adp[0], adp[1], adp[2], adp[5], adp[4], adp[3])
                adp2 = old_model._atoms[i]['adp'][0]
                adp2 = (adp2[0], adp2[1], adp2[2], adp2[5], adp2[4], adp2[3])
                adp = adptbx.u_cart_as_u_cif(uc, adp)
                adp2 = adptbx.u_cart_as_u_cif(uc, adp2)
                adp_esds = (esds[matrix_run],
                            esds[matrix_run + 1],
                            esds[matrix_run + 2],
                            esds[matrix_run + 3],
                            esds[matrix_run + 4],
                            esds[matrix_run + 5])
                adp_esds = adptbx.u_star_as_u_cif(uc, adp_esds)
                for u in range(6):
                  # if parameter is fixed and therefore has 0 esd
                  if adp_esds[u] > 0:
                    res = abs(adp[u] - adp2[u]) / adp_esds[u]
                    if res > results.max_duij:
                      results.update_uij(res, annotations[matrix_run + u])
                matrix_run += 6
                if matrix_run < len(annotations):
                  if has_anh_new != None and has_anh_old != None:
                    assert matrix_run + 24 < matrix_size, "Inconsistent size of annotations and expected parameters!"
                    adp_C = atom['anharmonic_adp']['C']
                    adp2_C = old_model._atoms[i]['anharmonic_adp']['C']
                    adp_esds_C = (esds[matrix_run:matrix_run + 10])
                    adp_D = atom['anharmonic_adp']['D']
                    adp2_D = old_model._atoms[i]['anharmonic_adp']['D']
                    adp_esds_D = (esds[matrix_run + 10:matrix_run + 25])
                    for u in range(10):
                      # if parameter is fixed and therefore has 0 esd
                      if adp_esds_C[u] > 0:
                        res = abs(adp_C[u] - adp2_C[u]) / adp_esds_C[u]
                        if res > results.max_overall:
                          results.update_overall(res, annotations[matrix_run + u])
                    for u in range(14):
                      # if parameter is fixed and therefore has 0 esd
                      if adp_esds_D[u] > 0:
                        res = abs(adp_D[u] - adp2_D[u]) / adp_esds_D[u]
                        if res > results.max_overall:
                          results.update_overall(res, annotations[matrix_run + u + 10])
                    matrix_run += 25
              elif has_adp_new != None and has_adp_old == None:
                assert matrix_run + 5 < matrix_size, "Inconsistent size of annotations and expected parameters!"
                adp = atom['uiso'][0]
                adp2 = adptbx.u_cart_as_u_cif(uc, new_model._atoms[i]['adp'][0])
                adp_esds = (esds[matrix_run], esds[matrix_run + 1], esds[matrix_run + 2], esds[matrix_run + 3], esds[matrix_run + 4], esds[matrix_run + 5])
                adp_esds = adptbx.u_star_as_u_cif(uc, adp_esds)
                for u in range(6):
                  if esds[matrix_run] > 0:
                    res = abs(adp - adp2[u]) / adp_esds[u]
                    if res > results.max_duij:
                      results.update_uij(res, annotations[matrix_run])
                matrix_run += 6
                if matrix_run < len(annotations):
                  if ".C111" in annotations[matrix_run]:
                    matrix_run += 25
              elif has_adp_old == None and has_adp_new == None:
                if (i != len(new_model._atoms) - 1):
                  assert matrix_run < matrix_size, "Inconsistent size of annotations and expected parameters!"
                adp = atom['uiso'][0]
                adp2 = old_model._atoms[i]['uiso'][0]
                adp_esd = esds[matrix_run]
                if esds[matrix_run] > 0:
                  res = abs(adp - adp2) / adp_esd
                  if res > results.max_duij:
                    results.update_uij(res, annotations[matrix_run])
                matrix_run += 1
              if matrix_run < len(annotations):
                if 'occ' in annotations[matrix_run]:
                  matrix_run += 1
            HAR_log.write("{:>16.4f}".format(results.max_dxyz))
            if results.label_xyz != None:
              HAR_log.write("{:>10}".format(results.label_xyz))
            else:
              HAR_log.write("{:>10}".format("N/A"))

            HAR_log.write("{:>10.4f}".format(results.max_duij))
            if results.label_uij != None:
              HAR_log.write("{:>12}".format(results.label_uij))
            else:
              HAR_log.write("{:>12}".format("N/A"))

            HAR_log.write("{:>10.4f}".format(results.max_overall))
            if results.label_overall != None:
              HAR_log.write("{:>12}".format(results.label_overall))
            else:
              HAR_log.write("{:>12}".format("N/A"))

            results.r1 = OV.GetParam('snum.refinement.last_R1')
            results.wr2 = OV.GetParam('snum.refinement.last_wR2')

            HAR_log.write("{:>6.2f}".format(float(results.r1) * 100))
            HAR_log.write("{:>7.2f}".format(float(results.wr2) * 100))

            HAR_log.write("\n")
            HAR_log.flush()
          except Exception as e:
            HAR_log.write("!!!ERROR!!!\n")
            HAR_log.close()
            print("Error during analysis of shifts!")
            raise e

        r = results()
        analyze_shifts(r)
        if calculate == False:
          converged = True
          break
        elif Full_HAR == False:
          converged = True
          break
        elif (r.max_overall <= 0.01):
          converged = True
          break
        elif run == max_cycles:
          break
        elif r1_old != "n/a":
          if (float(r.r1) > float(r1_old) + 0.1) and (run > 1):
            HAR_log.write("      !! R1 increased by more than 0.1, aborting before things explode !!\n")
            self.refinement_has_failed.append("Error: R1 is not behaving nicely! Stopping!")
            break
        else:
          r1_old = r.r1
          wr2_old = r.wr2
    except Exception as e :
      if HAR_log != None:
        HAR_log.close()
      raise e

    # Done with the while !Converged
    OV.SetParam('snum.NoSpherA2.Calculate',False)
    if converged == False:
      HAR_log.write(" !!! WARNING: UNCONVERGED MODEL! PLEASE INCREASE MAX_CYCLE OR CHECK FOR MISTAKES !!!\n")
      self.refinement_has_failed.append("Warning: Unconverged Model!")
    if "DISCAMB" in source or "MATTS" in source:
      unknown_sources = False
      fn = os.path.join("olex2","Wfn_job","discambMATTS2tsc.log")
      if not os.path.exists(fn):
        fn = os.path.join("olex2","Wfn_job","discamb2tsc.log")
      if not os.path.exists(fn):
        HAR_log.write("                   !!! WARNING: No output file found! !!!\n")
        self.refinement_has_failed.append("Output file not found!")
      else:
        with open(fn) as discamb_log:
          for i in discamb_log.readlines():
            if "unassigned atom types" in i:
              unknown_sources = True
            if unknown_sources == True:
              HAR_log.write(i)
      if unknown_sources == True:
        HAR_log.write("                   !!! WARNING: Unassigned Atom Types! !!!\n")
        self.refinement_has_failed.append("Unassigned Atom Types!")
    HAR_log.write("*" * 110 + "\n")
    HAR_log.write("Residual density Max:{:+8.3f}\n".format(OV.GetParam('snum.refinement.max_peak')))
    HAR_log.write("Residual density Min:{:+8.3f}\n".format(OV.GetParam('snum.refinement.max_hole')))
    HAR_log.write("Residual density RMS:{:+8.3f}\n".format(OV.GetParam('snum.refinement.res_rms')))
    HAR_log.write("Goodness of Fit:     {:8.4f}\n".format(OV.GetParam('snum.refinement.goof')))
    HAR_log.write("Refinement finished at: ")
    HAR_log.write(str(datetime.datetime.now()))
    HAR_log.write("\n")

    precise = OV.GetParam('snum.NoSpherA2.precise_output')
    if precise == True:
      olex.m("spy.NoSpherA2.write_precise_model_file()")

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