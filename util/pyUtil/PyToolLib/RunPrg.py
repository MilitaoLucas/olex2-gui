# RunPrg.py
# $LastChangedDate$
# $LastChangedRevision$
# $LastChangedBy$
# $Id$
# $HeadURL$
import sys
import olex
import olx
import os
import pickle
import olexex
import FileSystem as FS
from History import *
import OlexVFS

from olexFunctions import OlexFunctions
OV = OlexFunctions()
import variableFunctions
import ExternalPrgParameters

class RunPrg(ArgumentParser):
  def __init__(self, fun=None, param=None):
    super(RunPrg, self).__init__(fun, param)
    self.fun = fun
    self.param = param

    self.demote = False
    self.SPD, self.RPD = ExternalPrgParameters.defineExternalPrograms()
    self.terminate = False
    self.tidy = False
    self.refine = False
    self.solve = False
    self.method = ""
    self.Ralpha = 0
    self.Nqual = 0
    self.CFOM = 0
    self.HasGUI = OV.HasGUI()
    self.make_unique_names = False
    self.shelx_files = r"%s/util/SHELX/" %OV.BaseDir()
    self.isAllQ = False #If all atoms are q-peaks, this will be assigned to True
    self.his_file = None
    
    self.demo_mode = OV.FindValue('autochem_demo_mode',False)
    self.broadcast_mode = OV.FindValue('broadcast_mode',False)
    if self.demo_mode:
      OV.demo_mode = True

    if self.param:
      p = self.param.split(';')
      if 't' in p:
        self.tidy = True
      if p[0]!='None' and p[0]!='-1':
        try:
          mc = int(p[0])
          OV.SetVar('snum_refinement_max_cycles',mc)
        except:
          pass
      if p[1]!='None' and p[1]!='-1':
        try:
          mp = int(p[1])
          OV.SetVar('snum_refinement_max_peaks',mp)
        except:
          pass

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
      ext = "ins"
    copy_from = "%s/%s.%s" %(self.tempPath, refinealias, ext)
    copy_to = "%s/listen.res" %(self.datadir)
    if os.path.isfile(copy_from):
      if copy_from.lower() != copy_to.lower():
        olx.file_Copy(copy_from, copy_to)
 
  def doFileResInsMagic(self):
    extensions = ['res', 'lst', 'cif', 'fcf', 'mat']
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
    
    if self.solve:
      OV.SetVar('snum_refinement_last_R1', 'Solution')
      self.his_file = hist.create_history(solution=True)
      return self.his_file
    
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
      OV.SetVar('snum_refinement_last_R1', R1)
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
  
  def doAutoTidyBefore(self):
    olx.Clean('-npd -aq=0.1 -at')
    if self.snum_refinement_auto_assignQ:
      olx.Sel('atoms where xatom.peak>%s' %self.snum_refinement_auto_assignQ)
      olx.Name('sel C')
    if self.snum_refinement_auto_pruneU:
      i = 0
      uref = 0
      for i in xrange(int(olx.xf_au_GetAtomCount())):
        ueq = float(olx.xf_au_GetAtomUiso(i))
        if uref:
          if uref == ueq:
            continue
          else:
            olx.Sel('atoms where xatom.uiso>%s' %self.snum_refinement_auto_pruneU)
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
    olx.Clean('-npd -aq=0.1 -at')
    if self.tidy:
      olx.Sel('atoms where xatom.uiso>0.07')
      olx.Sel('atoms where xatom.peak<2&&xatom.peak>0')
      olx.Kill('sel')
    if self.isAllQ:
      olx.Sel('atoms where xatom.uiso>0.07')
      olx.Kill('sel')
    if self.snum_refinement_auto_pruneQ:
      olx.Sel('atoms where xatom.peak<%.3f&&xatom.peak>0' %float(self.snum_refinement_auto_pruneQ))
      olx.Kill('sel')
      #olx.ShowQ('a true') # uncomment me!
      #olx.ShowQ('b true') # uncomment me!
    if self.snum_refinement_auto_pruneU:
      olx.Sel('atoms where xatom.uiso>%s' %self.snum_refinement_auto_pruneU)
      olx.Kill('sel')
    if self.snum_refinement_auto_assignQ:
      olx.Sel('atoms where xatom.peak>%s' %self.snum_refinement_auto_assignQ)
      olx.Name('sel C')
      olx.Sel('-u')
    if self.snum_refinement_auto_assemble == True:
      olx.Compaq('-a')
      olx.Move()
    else:
      pass
      olx.Clean('-npd -aq=0.1 -at')
    
  def post_refinement(self):
    if self.snum_refinement_auto_tidy:
      self.doAutoTidyAfter()
      OV.File()

  def setupRefine(self):
    self.refine = True
    self.bitmap = 'refine'
    self.method.pre_refinement(self)
    self.shelx = self.which_shelx(self.program)
    if olx.LSM() == "CGLS": 
      olx.DelIns('ACTA')
    OV.File()

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

  def setupSolve(self):
    try:
      self.sg = olex.f(r'sg(%n)')
    except:
      self.sg = ""
    self.formula = olx.xf_GetFormula()
    self.solve = True
    self.bitmap = 'solve'
    if "smtbx" not in self.program.name:
      self.shelx = self.which_shelx(self.program)
    args = self.method.pre_solution(self)
    olx.Reset(args)

  def runCctbxAutoChem(self):
    from AutoChem import OlexSetupRefineCctbxAuto
    print 'STARTING cctbx refinement'
    OV.reloadStructureAtreap(self.filePath, self.curr_file)
    #olx.Atreap(r"%s" %(r"%s/%s.ins" %(self.filePath, self.curr_file)))
    cctbx = OlexSetupRefineCctbxAuto('refine', self.snum_refinement_max_cycles)
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
      
    if OV.FindValue('snum_refinement_auto_max_peaks'):
      max_peaks = olexex.OlexAtoms().getExpectedPeaks()
      if max_peaks <= 5:
        OV.SetVar('snum_refinement_auto_pruneQ', 0.5)
        OV.SetVar('snum_refinement_auto_assignQ', 6.0)
      else:
        OV.SetVar('snum_refinement_auto_pruneQ', 1.5)
        OV.SetVar('snum_refinement_auto_assignQ', 2.0)
        
    if self.refine:
      self.doHistoryCreation()
      self.post_refinement()
    elif self.solve:
      self.method.post_solution(self)
      self.doHistoryCreation()
    OV.Cursor()
    OV.DeleteBitmap('%s' %self.bitmap)
      
  def run(self):
    OV.SetVar('SlideQPeaksVal','0') # reset q peak slider to display all peaks
    self.getVariables('solution')
    self.getVariables('auto')
    self.getVariables('refinement')
    if not OV.FileName():
      print "No structure loaded"
      return
    self.original_filename = OV.FileName()
    fun = self.fun
    #olx.Sel('-u') # uncomment me!
    olx.Stop('listen')
    
    self.program, self.method = self.getProgramMethod(fun)
    if not self.program or not self.method:
      return
    if fun == 'REFINE':
      olx.File("'%s/%s.ins'" %(OV.FilePath(),self.original_filename))
      self.setupRefine()
    elif fun == 'SOLVE':
      if OV.IsFileType('cif'):
        OV.Reap('%s/%s.ins' %(self.filepath,self.filename))
      self.setupSolve()
    
    if self.terminate: return
    
    OV.CreateBitmap('-r %s %s' %(self.bitmap, self.bitmap))
    self.setupFiles()
    if not self.terminate:
      if OV.FindValue("snum_refinement_graphical_output"):
        if fun == "REFINE":
          if self.HasGUI:
            from Analysis import ShelXAnalysis
            SXA = ShelXAnalysis()
            SXA.observe_shex_l()
      self.method.run(self)
    else: 
      self.endRun()
      return
    
    self.runAfterProcess()
    self.endRun()
    
    sys.stdout.refresh = False
    sys.stdout.graph = False
    
  def getProgramMethod(self, fun):
    if fun == 'REFINE':
      prgType = 'refinement'
      prgDict = self.RPD
      prg = self.snum_refinement_program
      method = self.snum_refinement_method
    else:
      prgType = 'solution'
      prgDict = self.SPD
      prg = self.snum_solution_program
      method = self.snum_solution_method
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
    OV.Cursor()
    OV.DeleteBitmap('%s' %self.bitmap)
    return self.his_file
    
  def Graph(self):
    from Analysis import XYPlot
    a = XYPlot(function=None, param=None)
    a.initialise(self.program, self.method)
    return a
