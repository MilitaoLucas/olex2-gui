import sys
import olex
import olx
import olex_core
import os
import olexex
import OlexVFS

from ArgumentParser import ArgumentParser
from History import hist

from olexFunctions import OlexFunctions
OV = OlexFunctions()
debug = bool(OV.GetParam('olex2.debug',False))
timer = debug

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
  running = False

  def __init__(self):
    super(RunPrg, self).__init__()
    self.demote = False
    self.SPD, self.RPD = ExternalPrgParameters.get_program_dictionaries()
    self.terminate = False
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
      print "No structure loaded"
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

    if RunPrg.running:
      print("Already running. Please wait...")
      return
    RunPrg.running = True
    try:
      token = TimeWatch.start("Running %s" %self.program.name)
      if timer:
        t1 = time.time()
      res = self.method.run(self)
      if timer:
        print "REFINEMENT: %.3f" %(time.time() - t1)
      if res == False:
        return False
      if not self.method.failure:
        if timer:
          t1 = time.time()
        self.runAfterProcess()
        if timer:
          print "runAfterProcess: %.3f" %(time.time() - t1)
      if timer:
        t1 = time.time()
      self.endRun()
      if timer:
        print "endRun: %.3f" %(time.time() - t1)

      TimeWatch.finish(token)
      sys.stdout.refresh = False
      sys.stdout.graph = False
    finally:
      if self.HasGUI:
        pass
        #olx.html.Update()
      RunPrg.running = False

      if self.please_run_auto_vss:
        self.run_auto_vss()

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
    if "smtbx" not in self.program.name:
      ext = "res"
    else:
      ext = "res"
    copy_from = "%s/%s.%s" %(self.tempPath, self.shelx_alias, ext)
    copy_to = "%s/listen.res" %(self.datadir)
    if os.path.isfile(copy_from):
      if copy_from.lower() != copy_to.lower():
        shutil.copyfile(copy_from, copy_to)

  def doFileResInsMagic(self):
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
        print "---- copying %s: %.3f" %(copy_from, time.time() -t)
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
    self.tempPath = "%s/.olex/temp" %OV.FilePath()
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
        print "HKL Source Filename reset to default file!"
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
#    copy_from = "%s%s%s.fab" %(self.filePath, os.sep, self.curr_file)
    copy_from = ".".join(OV.HKLSrc().split(".")[:-1]) + ".fab"
    copy_to = "%s%s%s.fab" %(self.tempPath, os.sep, self.shelx_alias)
    if os.path.exists(copy_from):
      if not os.path.exists(copy_to):
        shutil.copyfile(copy_from, copy_to)

  def runCctbxAutoChem(self):
    from AutoChem import OlexSetupRefineCctbxAuto
    print '+++ STARTING olex2.refine ++++++++++++++++++++++++++++++++++++'
    OV.reloadStructureAtreap(self.filePath, self.curr_file)
    #olx.Atreap(r"%s" %(r"%s/%s.ins" %(self.filePath, self.curr_file)))
    cctbx = OlexSetupRefineCctbxAuto('refine', self.params.snum.refinement.max_cycles)
    try:
      cctbx.run()
    except Exception, err:
      print err
    olex.f('GetVar(cctbx_R1)')
    print '+++ END olex2.refine +++++++++++++++++++++++++++++++++++++++++'

  def runAfterProcess(self):
    #olex.m("spy.run_skin sNumTitle")
    if 'olex2' not in self.program.name:
      if timer:
        t = time.time()
      self.doFileResInsMagic()
      if timer:
        print "--- doFilseResInsMagic: %.3f" %(time.time() - t)

      if timer:
        t = time.time()
      if self.HasGUI:
        olx.Freeze(True)
      OV.reloadStructureAtreap(self.filePath, self.curr_file, update_gui=False)
      if self.HasGUI:
        olx.Freeze(False)
      if timer:
        print "--- reloadStructureAtreap: %.3f" %(time.time() - t)

      # XT changes the HKL file - so it *will* match the file name
      if 'xt' not in self.program.name.lower():
        OV.HKLSrc(self.hkl_src)

    else:
      if self.broadcast_mode:
        if timer:
          t = time.time()
        self.doBroadcast()
        if timer:
          print "--- doBroacast: %.3f" %(time.time() - t)

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
      print "Please choose a valid %s program" %prgType
      return None, None
    try:
      prgMethod = program.methods[method]
    except KeyError:
      print "Please choose a valid method for the %s program %s" %(prgType, prg)
      return None, None
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
        print 'Please provide the structure composition'
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
  running = False
  def __init__(self):
    RunPrg.__init__(self)
    self.bitmap = 'refine'
    self.program, self.method = self.getProgramMethod('refine')
    if self.program is None or self.method is None:
      return
    self.run()

  def run(self):
    if RunRefinementPrg.running:
      print("Already running. Please wait...")
      return False
    RunRefinementPrg.running = True
    try:
      self.startRun()
      OV.File(u"%s/%s.ins" %(OV.FilePath(),self.original_filename))
      try:
        self.setupRefine()
        self.setupFiles()
      except Exception, err:
        sys.stderr.formatExceptionInfo()

        print err
        self.endRun()
        return False
      if self.terminate:
        self.endRun()
        return
      if self.params.snum.refinement.graphical_output and self.HasGUI:
        self.method.observe(self)
      RunPrg.run(self)
    finally:
      RunRefinementPrg.running = False


  def setupRefine(self):
    self.method.pre_refinement(self)
    self.shelx = self.which_shelx(self.program)
    if olx.LSM().upper() == "CGLS":
      olx.DelIns('ACTA')
    OV.File()

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
      print "-- self.method.post_refinement(self): %.3f" %(time.time()-t)

    if timer:
      t = time.time()
    self.post_prg_html()
    self.doHistoryCreation()
    if timer:
      print "-- self.method.post_refinement(self): %3f" %(time.time()-t)

    if self.R1 == 'n/a':
      return
    if self.params.snum.refinement.auto.tidy:
      self.doAutoTidyAfter()
      OV.File()
    if OV.GetParam('snum.refinement.check_absolute_structure_after_refinement'):
      try:
        self.isInversionNeeded(force=self.params.snum.refinement.auto.invert)
      except Exception, e:
        print "Could not determine whether structure inversion is needed: %s" %e
    OV.SetParam('snum.current_process_diagnostics','refinement')

    if timer:
      t = time.time()
    if self.params.snum.refinement.cifmerge_after_refinement:
      try:
        MergeCif(edit=False, force_create=False, evaluate_conflicts=False)
      except Exception, e:
        print("Failed in CifMerge: '%s'" %str(e))
    if timer:
      print "-- MergeCif: %.3f" %(time.time()-t)

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
        except Exception, ex:
          print >> sys.stderr, "History could not be created"
          sys.stderr.formatExceptionInfo()
      else:
        print ("Skipping History")
    else:
      R1 = "n/a"
      self.his_file = None
      print "The refinement has failed, no R value was returned by the refinement."
    self.R1 = R1
    self.wR2 = wR2
    OV.SetParam('snum.refinement.current_history', self.his_file)
    return self.his_file, R1

  def isInversionNeeded(self, force=False):
    if self.params.snum.init.skip_routine:
      print ("Skipping absolute structure validation")
      return
    if olex_core.SGInfo()['Centrosymmetric'] == 1: return
    from cctbx_olex_adapter import hooft_analysis
    from libtbx.utils import format_float_with_standard_uncertainty
    from cctbx import sgtbx
    from libtbx.utils import Sorry
    print "Checking absolute structure..."
    inversion_needed = False
    possible_racemic_twin = False
    inversion_warning = "WARNING: Structure should be inverted (inv -f), unless there is a good reason not to do so."
    racemic_twin_warning = "WARNING: Structure may be an inversion twin"
    flack = self.method.getFlack()

    try:
      hooft = hooft_analysis()
    except Sorry, e:
      print e
    else:
      if hooft.reflections.f_sq_obs_filtered.anomalous_flag():
        s = format_float_with_standard_uncertainty(
          hooft.hooft_y, hooft.sigma_y)
        print "Hooft y: %s" %s
        OV.SetParam('snum.refinement.hooft_str', s)
        if (hooft.p3_racemic_twin is not None and
            round(hooft.p3_racemic_twin, 3) == 1):
          possible_racemic_twin = True
        elif hooft.p2_false is not None and round(hooft.p2_false, 3) == 1:
          inversion_needed = True
      else:
        OV.SetParam('snum.refinement.hooft_str', None)

    if flack:
      print "Flack x: %s" %flack
      fs = flack.split("(")
      flack_val = float(fs[0])
      if len(fs) > 1:
        flack_esd = float(fs[1].strip(")"))
      else:
        flack_esd = None
      if flack_val > 0.8:
        inversion_needed = True
    if force and inversion_needed:
      olex.m('Inv -f')
      OV.File('%s.res' %OV.FileName())
      OV.SetParam('snum.refinement.auto.invert',False)
      print "The Structure has been inverted"
    elif inversion_needed:
      print inversion_warning
    if possible_racemic_twin:
      if (hooft.twin_components is not None and
          hooft.twin_components[0].twin_law != sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1))):
        print racemic_twin_warning
    if not inversion_needed and not possible_racemic_twin:
      #print "OK"
      pass


def AnalyseRefinementSource():
  file_name = OV.ModelSrc()
  ins_file_name = olx.file.ChangeExt(file_name, 'ins')
  res_file_name = olx.file.ChangeExt(file_name, 'res')
  hkl_file_name = olx.file.ChangeExt(file_name, 'hkl')
  if olx.IsFileType('cif') == 'true':
    if os.path.exists(ins_file_name) or os.path.exists(res_file_name):
      olex.m('reap "%s"' %ins_file_name)
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

