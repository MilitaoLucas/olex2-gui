import sys
import olex
import olx
import os
import olexex
from History import *

from olexFunctions import OlexFunctions
OV = OlexFunctions()
import ExternalPrgParameters

class RunPrg(ArgumentParser):
  def __init__(self):
    super(RunPrg, self).__init__()
    self.demote = False
    self.SPD, self.RPD = ExternalPrgParameters.defineExternalPrograms()
    self.terminate = False
    self.tidy = False
    self.method = ""
    self.Ralpha = 0
    self.Nqual = 0
    self.CFOM = 0
    self.HasGUI = OV.HasGUI()
    self.make_unique_names = False
    self.shelx_files = r"%s/util/SHELX/" %self.basedir
    self.isAllQ = False #If all atoms are q-peaks, this will be assigned to True
    self.his_file = None
    
    self.demo_mode = OV.FindValue('autochem_demo_mode',False)
    self.broadcast_mode = OV.FindValue('broadcast_mode',False)
    if self.demo_mode:
      OV.demo_mode = True

    if self.HasGUI:
      from Analysis import PrgAnalysis
      self.PrgAnalysis = PrgAnalysis
      
      
      
    self.params = olx.phil_handler.get_python_object()
    #self.getVariables('auto')
    OV.SetVar('SlideQPeaksVal','0') # reset q peak slider to display all peaks
    if not self.filename:
      print "No structure loaded"
      return
    self.original_filename = self.filename
    olx.Stop('listen')

  def __del__(self):
    olx.phil_handler.update_from_python(self.params)

  def which_shelx(self, type="xl"):
    a = olexex.which_program(type)
    if a == "":
      OV.Alert("Error", "ShelX %s is not found on this system.\nPlease make sure that the ShelX executable files are either on the path or in the Olex2 installation directory." %type, "O") 
      OV.Cursor()
      self.terminate = True
    return a

  def doBroadcast(self):
    refinealias = "%s" %self.hkl_src_name
    refinealias = refinealias.replace(' ', '')
    refinealias = refinealias.lower()
    if "smtbx" not in self.program.name:
      ext = "res"
    else:
      ext = "res"
    copy_from = "%s/%s.%s" %(self.tempPath, refinealias, ext)
    copy_to = "%s/listen.res" %(self.datadir)
    if os.path.isfile(copy_from):
      if copy_from.lower() != copy_to.lower():
        olx.file_Copy(copy_from, copy_to)

  def doFileResInsMagic(self):
    extensions = ['res', 'lst', 'cif', 'fcf', 'mat', 'pdb']
    if self.broadcast_mode:
      self.doBroadcast()
    for ext in extensions:
      refinealias = "%s" %self.hkl_src_name
      refinealias = refinealias.replace(' ', '')
      refinealias = refinealias.lower()
      copy_from = "%s/%s.%s" %(self.tempPath, refinealias, ext)
      copy_to = "%s/%s.%s" %(self.filePath, self.original_filename, ext)
      if os.path.isfile(copy_from):
        if copy_from.lower() != copy_to.lower():
          olx.file_Copy(copy_from, copy_to)

  def doHistoryCreation(self, type="normal"):
    if type == "first":
      historyPath = "%s/%s.history" %(OV.StrDir(), OV.FileName())
      if not os.path.exists(historyPath):
        type = 'normal'
    if type != "normal":
      return

  def setupFiles(self):
    olx.User("'%s'" %OV.FilePath())
    self.filePath = OV.FilePath()
    self.fileName = OV.FileName()
    self.tempPath = "%s/.olex/temp" %OV.FilePath()
    if not os.path.exists(self.tempPath):
      os.mkdir(self.tempPath)
    
    ## clear temp folder to avoid problems
    old_temp_files = os.listdir(self.tempPath) 
    for file in old_temp_files:
      try:
        os.remove(r'%s/%s' %(self.tempPath,file))
      except OSError:
        continue
      
    try:
      self.hkl_src = OV.HKLSrc()
      if not os.path.exists(self.hkl_src):
        self.hkl_src = OV.file_ChangeExt(OV.FileFull(),'hkl')
        if os.path.exists(self.hkl_src):
          OV.HKLSrc(self.hkl_src)
        else:
          print "Please choose a reflection file"
          self.terminate = True
          return
    except:
      self.hkl_src = OV.file_ChangeExt(OV.FileFull(),'hkl')
    self.hkl_src_name = self.hkl_src.split("/")[-1].split(".")[0]
    self.curr_file = OV.FileName()
    refinealias = "%s" %self.hkl_src_name
    refinealias = refinealias.replace(' ', '')
    refinealias = refinealias.lower()
    copy_from = "%s" %(self.hkl_src)
    ## All files will be copied to the temp directory in lower case. This is to be compatible with the Linux incarnations of ShelX
    copy_to = "%s/%s.hkl" %(self.tempPath, refinealias)
    if not os.path.exists(copy_to):
      olx.file_Copy(copy_from, copy_to)
    copy_from = "%s/%s.ins" %(self.filePath, self.curr_file)
#    copy_from = copy_from.lower() # This breaks under Linux if the directory is also case sensitive
    copy_to = "%s/%s.ins" %(self.tempPath, refinealias)
    if not os.path.exists(copy_to):
      olx.file_Copy(copy_from, copy_to)

  def runCctbxAutoChem(self):
    from AutoChem import OlexSetupRefineCctbxAuto
    print 'STARTING cctbx refinement'
    OV.reloadStructureAtreap(self.filePath, self.curr_file)
    #olx.Atreap(r"%s" %(r"%s/%s.ins" %(self.filePath, self.curr_file)))
    cctbx = OlexSetupRefineCctbxAuto('refine', self.params.snum.refinement.max_cycles)
    try:
      cctbx.run()
    except Exception, err:
      print err
    OV.DeleteBitmap('refine')
    olex.f('GetVar(cctbx_R1)')

  def runAfterProcess(self):
    if 'smtbx' not in self.program.name:
      self.doFileResInsMagic()
      reflections = OV.HKLSrc() #BEWARE DRAGONS
      OV.reloadStructureAtreap(self.filePath, self.curr_file)
      OV.HKLSrc(reflections)
    else:
      if self.broadcast_mode:
        self.doBroadcast()
      lstFile = '%s/%s.lst' %(self.filePath, self.original_filename)
      if os.path.exists(lstFile):
        os.remove(lstFile)
      olx.DelIns("TREF")
      
    if self.params.snum.refinement.auto.max_peaks:
      max_peaks = olexex.OlexAtoms().getExpectedPeaks()
      if max_peaks <= 5:
        self.params.snum.refinement.auto.pruneQ = 0.5
        self.params.snum.refinement.auto.assignQ = 6.0
      else:
        self.params.snum.refinement.auto.pruneQ = 1.5
        self.params.snum.refinement.auto.assignQ = 2.0
    self.method.unregisterCallback()

  def getProgramMethod(self, fun):
    if fun == 'refine':
      prgType = 'refinement'
      prgDict = self.RPD
      prg = self.params.snum.refinement.program
      method = self.params.snum.refinement.method
    else:
      prgType = 'solution'
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

  def endRun(self):
    #OV.Cursor()
    OV.DeleteBitmap('%s' %self.bitmap)
    return self.his_file

class RunSolutionPrg(RunPrg):
  def __init__(self):
    RunPrg.__init__(self)
    self.getVariables('solution')
    self.program, self.method = self.getProgramMethod('solve')
    self.run()
    
  def run(self):
    if OV.IsFileType('cif'):
      OV.Reap('%s/%s.ins' %(self.filepath,self.filename))
    self.setupSolve()
    if self.terminate: return
    self.setupFiles()
    if self.terminate:
      self.endRun()
      return
    if self.params.snum.solution.graphical_output and self.HasGUI:
      self.method.observe(self)
    self.method.run(self)
    self.runAfterProcess()
    self.endRun()
    sys.stdout.refresh = False
    sys.stdout.graph = False
    olx.phil_handler.update_from_python(self.params)

  def runAfterProcess(self):
    RunPrg.runAfterProcess(self)
    self.method.post_solution(self)
    self.doHistoryCreation()
    
  def setupSolve(self):
    try:
      self.sg = olex.f(r'sg(%n)')
    except:
      self.sg = ""
    self.formula = olx.xf_GetFormula()
    self.bitmap = 'solve'
    if "smtbx" not in self.program.name:
      self.shelx = self.which_shelx(self.program)
    args = self.method.pre_solution(self)
    olx.Reset(args)
    
  def doHistoryCreation(self):
    self.params.snum.refinement.last_R1 = 'Solution'
    self.his_file = hist.create_history(solution=True)
    return self.his_file


class RunRefinementPrg(RunPrg):
  def __init__(self):
    RunPrg.__init__(self)
    #self.getVariables('refinement')
    self.program, self.method = self.getProgramMethod('refine')
    self.run()

  def run(self):
    olx.File("'%s/%s.ins'" %(OV.FilePath(),self.original_filename))
    self.setupRefine()
    if self.terminate: return
    self.setupFiles()
    if self.terminate:
      self.endRun()
      return
    if self.params.snum.refinement.graphical_output and self.HasGUI:
      self.method.observe(self)
    self.method.run(self)
    self.runAfterProcess()
    self.endRun()
    sys.stdout.refresh = False
    sys.stdout.graph = False

  def setupRefine(self):
    self.bitmap = 'refine'
    self.method.pre_refinement(self)
    self.shelx = self.which_shelx(self.program)
    if olx.LSM() == "CGLS": 
      olx.DelIns('ACTA')
    OV.File()

  def doAutoTidyBefore(self):
    olx.Clean('-npd -aq=0.1 -at')
    if self.params.snum.refinement.auto_assignQ:
      olx.Sel('atoms where xatom.peak>%s' %self.params.snum.refinement.auto_assignQ)
      olx.Name('sel C')
    if self.params.snum.refinement.auto_pruneU:
      i = 0
      uref = 0
      for i in xrange(int(olx.xf_au_GetAtomCount())):
        ueq = float(olx.xf_au_GetAtomUiso(i))
        if uref:
          if uref == ueq:
            continue
          else:
            olx.Sel('atoms where xatom.uiso>%s' %self.params.snum.refinement.auto_pruneU)
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
      olx.Compaq('-a')
      olx.Move()
    else:
      pass
      olx.Clean('-npd -aq=0.1 -at')

  def runAfterProcess(self):
    RunPrg.runAfterProcess(self)
    self.doHistoryCreation()
    if self.params.snum.refinement.auto.tidy:
      self.doAutoTidyAfter()
      OV.File()
  
  def doHistoryCreation(self):
    R1 = 0
    self.his_file = ""
    look = olex.f('IsVar(cctbx_R1)')
    if look == "true":
      R1 = float(olex.f('GetVar(cctbx_R1)'))
      olex.f('UnsetVar(cctbx_R1)')
    else:
      try:
        R1 = float(olx.Lst('R1'))
      except:
        R1 = False
        
    if R1:
      self.params.snum.refinement.last_R1 = str(R1)
      try:
        self.his_file = hist.create_history()
      except Exception, ex:
        print >> sys.stderr, "History could not be created"
        sys.stderr.formatExceptionInfo()
    else:
      R1 = "n/a"
      self.his_file = None
      print "The refinement has failed, no R value was returned by the refinement."
    self.R1 = R1
    return self.his_file, R1

OV.registerFunction(RunRefinementPrg)
OV.registerFunction(RunSolutionPrg)
