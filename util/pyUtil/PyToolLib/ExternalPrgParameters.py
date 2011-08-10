# ExternalPrgParameters.py
# -*- coding: latin-1 -*-

import os, sys
import olx
import olex
import olex_core
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import phil_interface
import libtbx.utils

definedControls = []

class ExternalProgramDictionary(object):
  def __init__(self):
    self.programs = {}
    self.counter = 0

  def addProgram(self, program):
    program.order = self.counter
    self.programs.setdefault(program.name, program)
    self.counter += 1

  def __contains__(self, name):
    if type(name) == str:
      return name in self.programs
    else:
      return name in self.programs.values()

  def __iter__(self):
    return self.programs.itervalues()


class Program(object):
  def __init__(self, name, program_type, author, reference, execs=None, versions=None):
    self.name = name
    self.program_type = program_type
    self.author = author
    self.reference = reference
    self.execs = execs
    self.versions = versions
    self.methods = {}
    self.counter = 0

  def __contains__(self, name):
    if type(name) == str:
      return name in self.methods
    else:
      return name in self.methods.values()

  def __iter__(self):
    return self.methods.itervalues()

  def addMethod(self, method):
    method.order = self.counter
    self.methods.setdefault(method.name, method)
    self.counter += 1


class Method(object):
  failure = False

  def __init__(self, phil_object):
    self.phil_index = phil_interface.phil_handler(phil_object)
    params = self.phil_index.params
    self.name = params.name
    #self.options = params.options
    self.help = '%s-help' %(self.name.lower().replace(' ', '-'))
    self.info = '%s-info' %(self.name.lower().replace(' ', '-'))
    self.observer = None

  def html_gui(self):
    pass

  def run(self, RunPrgObject):
    """Must be redefined in subclass.

    It is from within this method that the external program will be run.
    """
    assert 0, 'run must be defined!'

  def instructions(self):
    scope = self.phil_index.get_scope_by_name('instructions')
    if scope is None:
      return []
    return (object for object in scope.active_objects())

  def options(self, name):
    return (arg for arg in
            self.phil_index.get_scope_by_name('instructions.%s.values' %name)
            .active_objects())

  def calculate_defaults(self):
    """Defines controls in Olex2 for each argument in self.args
    """
    for instruction in self.instructions():
      params = instruction.extract()
      default = params.default
      name = instruction.name
      global definedControls
      varName = "settings_%s" %name
      ctrl_name = 'SET_%s' %varName.upper()
      if ctrl_name not in definedControls:
        OV.SetVar(varName, default) # Define checkbox
        definedControls.append(ctrl_name)
        for option in self.options(name):
          value = option.extract()
          if value is None:
            value = ''
          OV.SetVar('%s_%s' %(varName, option.name), value) # Define text box for each value

  def getValuesFromFile(self):
    """Gets the value of all arguments in self.args that are present in the
    .ins file and sets the value of the GUI input boxes to reflect this.
    """
    for instruction in self.instructions():
      params = instruction.extract()
      default = params.default
      varName = "settings_%s" %instruction.name
      if instruction.name == 'temp':
        ins = olx.xf_exptl_Temperature()
      else:
        if instruction.caption is not None:
          ins = olx.Ins(instruction.caption)
        else:
          ins = olx.Ins(instruction.name)
      if ins != 'n/a':
        OV.SetVar(varName, True)
        ins = ins.split()
        count = 0
        for option in self.options(instruction.name):
          try:
            val = ins[count]
            OV.SetVar('%s_%s' %(varName, option.name), val)
            if option.name == 'nls':
              OV.SetParam('snum.refinement.max_cycles', val)
            elif option.name == 'npeaks':
              OV.SetParam('snum.refinement.max_peaks', val)
          except IndexError:
            OV.SetVar('%s_%s' %(varName, option.name), '')
          count += 1
      else:
        if not default:
          OV.SetVar(varName, False)
        if instruction.name in ('ls', 'cgls'):
          val = OV.GetParam('snum.refinement.max_cycles')
          OV.SetVar('%s_nls' %varName, val)
        elif instruction.name == 'plan':
          val = OV.GetParam('snum.refinement.max_peaks')
          OV.SetVar('%s_npeaks' %varName, val)

  def getArgs(self):
    """Gets the value of all the arguments in self.args from Olex2.
    """
    args = []
    for instruction in self.instructions():
      if OV.FindValue('settings_%s' %instruction.name) in (True, 'True', 'true'):
        # Check if the argument is selected in the GUI
        if instruction.caption is not None:
          arg = instruction.caption
        else:
          arg = instruction.name
        for option in self.options(instruction.name):
          try:
            value = OV.FindValue('settings_%s_%s' %(instruction.name, option.name))
            if not isinstance(value, int) and not isinstance(value, float):
              if ('(' in value and ')' in value):
                value = value
              elif '.' in value:
                value = float(value)
              else:
                value = int(value)
            arg += ' %s' %value
          except ValueError:
            break
        args.append(arg)
    return args

  def extraHtml(self):
    """This can be redefined in a subclass to define extra HTML that is to be
    added to the program settings panel.
    """
    return ''

  def observe(self, RunPrgObject):
    pass

  def unregisterCallback(self):
    if self.observer is not None:
      OV.unregisterCallback("procout", self.observer.observe)


class Method_solution(Method):
  def __init__(self, phil_object):
    Method.__init__(self, phil_object)
    self.atom_sites_solution = self.phil_index.params.atom_sites_solution

  def pre_solution(self, RunPrgObject):
    """Prepares the arguments required to reset the structure before running the
    structure solution program.
    """
    args = '\n'.join(self.getArgs()).upper()
    #if not args:
      #args = self.cmd
    if not RunPrgObject.formula or RunPrgObject.formula == "None":
      RunPrgObject.formula = RunPrgObject.params.snum.refinement.original_formula

    formula = getFormulaAsDict(RunPrgObject.formula)
    if sum(formula.values()) == 0:
      if OV.HasGUI():
        cell_volume = float(olx.xf_au_GetCellVolume())
        Z = float(olx.xf_au_GetZ())
        guess_C = int(cell_volume/Z/18)
        f = OV.GetUserInput(1,'Invalid formula','Enter correct formula...')
        if f and f!= 'Enter correct formula...':
          try:
            olx.xf_SetFormula(f)
            RunPrgObject.formula = olx.xf_GetFormula()
          except RuntimeError:
            formula['C'] = guess_C
            RunPrgObject.formula = ' '.join('%s%s' %(type,count) for type,count in formula.items())
            olx.xf_SetFormula(RunPrgObject.formula)
        else:
          formula['C'] = guess_C
          RunPrgObject.formula = ' '.join('%s%s' %(type,count) for type,count in formula.items())
          olx.xf_SetFormula(RunPrgObject.formula)
      else:
        print "Formula is invalid"
    if 'D' in formula.keys():
      D_count = formula.pop('D')
      formula['H'] = formula.get('H',0) + D_count
      text_formula = ' '.join('%s%s' %(type,count) for type,count in formula.items())
      RunPrgObject.formula = text_formula
    if RunPrgObject.formula != "None":
      args += " -c='%s' " % RunPrgObject.formula
    if RunPrgObject.sg:
      args += "-s=%s " % RunPrgObject.sg
    return args

  def post_solution(self, RunPrgObject):
    """Things to be done after running the solution program.
    """
    if RunPrgObject.HasGUI:
      #olx.ShowQ('a true')
      #olx.ShowQ('b true')
      #olx.Compaq('-a')
      olx.ShowStr("true")
    self.auto = True


class Method_refinement(Method):

  def getFlack(self):
    return None

  def addInstructions(self):
    """Adds instructions to the .ins file so that the file reflects what is selected in the GUI.
    """
    for arg in self.getArgs():
      argName = arg.split()[0]
      olx.DelIns(argName)
      OV.AddIns(arg)

  def pre_refinement(self, RunPrgObject):
    RunPrgObject.isAllQ = True
    for i in xrange(int(olx.xf_au_GetAtomCount())):
      ret = olx.xf_au_IsPeak(i)
      if ret == "false":
        RunPrgObject.isAllQ = False
        break
    if RunPrgObject.isAllQ:
      print "Please provide some atoms to refine"
      RunPrgObject.terminate = True
      return

    if RunPrgObject.params.snum.refinement.auto.tidy:
      RunPrgObject.doAutoTidyBefore()
    if RunPrgObject.params.snum.refinement.update_weight:
      suggested_weight = OV.GetParam('snum.refinement.suggested_weight')
      if suggested_weight is not None:
        olx.UpdateWght(*suggested_weight)
    if RunPrgObject.make_unique_names:
      pass
      #olx.Sel('-a')
      #olx.Name('sel 1 -c')
    if RunPrgObject.params.snum.auto_hydrogen_naming:
      olx.FixHL()
    
    wave_length = float(olx.xf_exptl_Radiation())
    if round(wave_length, 2) == round(0.71073,2) or round(wave_length, 2) == round(1.5414, 2) or round(wave_length, 2)  == round(0.56053, 2):
      pass
    else:
      print "Using non-standard wavelegnth (%f) calculating DISP and adding\n"%wave_length
      olx.GenDisp()

  def post_refinement(self, RunPrgObject):
    pass
  
class Method_shelx(Method):

  def run(self, RunPrgObject):
    """Runs any SHELX refinement/solution program
    """
    print 'STARTING SHELX %s with %s' %(
      RunPrgObject.program.program_type, self.name)
    prgName = olx.file_GetName(RunPrgObject.shelx)
    #olex.m("User '%s'" %RunPrgObject.tempPath)
    olx.User("'%s'" %RunPrgObject.tempPath)
    xl_ins_filename = RunPrgObject.shelx_alias
# This is an ugly fix - but good start
    if 'shelxs86' in prgName:
      print 'STARTING SHELX86 modifications'
      import fileinput, string, sys
      for line in fileinput.input(xl_ins_filename.lower()+'.ins',inplace=1):
        if 'REM' in line:
          continue
        sys.stdout.write(line)
# This is super ugly but what can I do?
# This really be a function rather than a separate file but I can not get it to work yet?
    if prgName in ('shelxl', 'xl', 'shelxl_ifc', 'XLMP' ):
      names = xl_ins_filename.lower()+'.ins'
    if prgName in ('shelxs', 'xs', 'shelxs86'):
      import fileinput, string, sys
      for line in fileinput.input(xl_ins_filename.lower()+'.ins',inplace=1):
        if 'DISP' in line:
          continue
        sys.stdout.write(line)
    command = "%s '%s'" % (prgName, xl_ins_filename.lower()) #This is correct!!!!!!
    #sys.stdout.graph = RunPrgObject.Graph()
    if not RunPrgObject.params.snum.shelx_output:
      command = "-q " + command
    success = olx.Exec(command)
    if not success:
      raise RuntimeError(
        'you may be using an outdated version of %s' %(prgName))
    olx.WaitFor('process') # uncomment me!
    olex.m("User '%s'" %RunPrgObject.filePath)
    #olx.User("'%s'" %RunPrgObject.filePath)


class Method_shelx_solution(Method_shelx, Method_solution):
  """Inherits methods specific to shelx solution programs
  """

  def observe(self, RunPrgObject):
    import Analysis
    self.observer = Analysis.ShelXS_graph(RunPrgObject.program, RunPrgObject.method)
    OV.registerCallback("procout", self.observer.observe)


class Method_shelx_refinement(Method_shelx, Method_refinement):
  """Inherits methods specific to shelx refinement programs
  """

  def __init__(self, phil_object):
    Method.__init__(self, phil_object)
    
  def pre_refinement(self, RunPrgObject):
    if OV.GetParam("snum.refinement.use_solvent_mask"):
      import cctbx_olex_adapter
      from smtbx import masks
      from libtbx import easy_pickle
      #from iotbx.shelx import hklf
      filepath = OV.StrDir()
      modified_intensities = None
      modified_hkl_path = "%s/%s-mask.hkl" %(OV.FilePath(), OV.FileName())
      f_mask, f_model = None, None
      if not OV.HKLSrc() == modified_hkl_path:
        OV.SetParam('snum.masks.original_hklsrc', OV.HKLSrc())
      if OV.GetParam("snum.refinement.recompute_mask_before_refinement"):
        if OV.HKLSrc() == modified_hkl_path:
          raise Exception("You can't calculate a mask on an already masked file!")
        cctbx_olex_adapter.OlexCctbxMasks()
        if olx.current_mask.flood_fill.n_voids() > 0:
          f_mask = olx.current_mask.f_mask()
          f_model = olx.current_mask.f_model()
      elif os.path.exists(modified_hkl_path):
        OV.HKLSrc(modified_hkl_path)
      elif os.path.exists("%s/%s-f_mask.pickle" %(filepath, OV.FileName())):
        f_mask = easy_pickle.load("%s/%s-f_mask.pickle" %(filepath, OV.FileName()))
        f_model = easy_pickle.load("%s/%s-f_model.pickle" %(filepath, OV.FileName()))
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
        modified_intensities = masks.modified_intensities(fo2, f_model, f_mask)
      if modified_intensities is not None:
        file_out = open(modified_hkl_path, 'w')
        modified_intensities.export_as_shelx_hklf(file_out,
          normalise_if_format_overflow=True)
        file_out.close()
        OV.HKLSrc(modified_hkl_path)
      #else:
        #print "No mask present"
    Method_refinement.pre_refinement(self, RunPrgObject)

  def post_refinement(self, RunPrgObject):
    before_mask = OV.GetParam('snum.masks.original_hklsrc')
    if before_mask:
      OV.SetParam('snum.masks.original_hklsrc',None)
      if OV.HKLSrc() != before_mask:
        OV.HKLSrc(before_mask)
        OV.File()
    suggested_weight = olx.Ins('weight1')
    if suggested_weight != 'n/a':
      if len(suggested_weight.split()) == 1:
        suggested_weight += ' 0'
      OV.SetParam('snum.refinement.suggested_weight', suggested_weight)

  def observe(self, RunPrgObject):
    import Analysis
    self.observer = Analysis.ShelXL_graph(RunPrgObject.program, RunPrgObject.method)
    OV.registerCallback("procout", self.observer.observe)

  def getFlack(self):
    flack = olx.Lst('flack')
    if flack == "n/a":
      flack = None
    return flack


class Method_shelx_direct_methods(Method_shelx_solution):

  def post_solution(self, RunPrgObject):
    Method_shelx_solution.post_solution(self, RunPrgObject)
    self.get_XS_TREF_solution_indicators(RunPrgObject)

  def get_XS_TREF_solution_indicators(self, RunPrgObject):
    """Gets the TREF solution indicators from the .lst file and prints values in Olex2.
    """
    import lst_reader
    lstPath = "%s/%s.lst" %(OV.FilePath(), OV.FileName())
    lstValues = lst_reader.reader(path=lstPath).values()

    RunPrgObject.Ralpha = lstValues.get('Ralpha','')
    RunPrgObject.Nqual = lstValues.get('Nqual','')
    RunPrgObject.CFOM = lstValues.get('CFOM','')

    print RunPrgObject.Ralpha, RunPrgObject.Nqual, RunPrgObject.CFOM


class Method_shelxd(Method_shelx_solution):

  def calculate_defaults(self):
    """Defines controls in Olex2 for each argument in self.args and then calculates
    sensible default values for PLOP and FIND based on the cell volume.
    """
    Method.calculate_defaults(self) # Define controls in Olex2
    #volume = float(olex.f("Cell(volume)"))
    volume = float(olx.xf_au_GetCellVolume())
    n = int(volume/18) * 0.7
    nmin = int(n * 0.8)
    nmid = int(n * 1.2)
    nmax = int(n * 1.4)

    try:
      OV.SetVar('settings_find_na', nmin)
      OV.SetVar('settings_plop_a', nmin)
      OV.SetVar('settings_plop_b', nmid)
      OV.SetVar('settings_plop_c', nmax)
    except:
      pass

  def extraHtml(self):
    """Makes the HTML for a button to interrupt ShelXD.
    """
    import htmlTools
    button_d = {
      'name':'STOP_DUAL_SPACE',
      'value':'STOP',
      'width':50,
      'height':28,
      'onclick':'spy.stopShelx()',
    }
    button_html = htmlTools.make_input_button(button_d)
    html = '''
  </tr>
  <tr>
    %s
  <td>
    %s
  </td>
  ''' %(htmlTools.make_table_first_col(), button_html)
    return html

  def pre_solution(self, RunPrgObject):
    args = Method_shelx_solution.pre_solution(self, RunPrgObject)
    volume = float(olx.xf_au_GetCellVolume())
    n = int(volume/18) * 0.7
    nmin = int(n * 0.8)
    nmax = int(n * 1.2)
    nmaxx = int(n * 1.4)
    if 'FIND' not in args:
      args += 'FIND %i\n' %nmin
    if 'PLOP' not in args:
      args += 'PLOP %i %i %i\n' %(nmin, nmax, nmaxx)
    if 'MIND' not in args:
      args += 'MIND 1 -0.1\n'
    if 'NTRY' not in args:
      args += 'NTRY 100\n'
    return args

  def run(self, RunPrgObject):
    """Makes Olex listen to the temporary directory before running the executable
    so that intermediate solutions will be displayed onscreen.
    """
    listen_file = '%s/%s.res' %(RunPrgObject.tempPath,RunPrgObject.hkl_src_name)
    OV.Listen(listen_file)
    Method_shelx_solution.run(self, RunPrgObject)

  def post_solution(self, RunPrgObject):
    """Stops listening to the temporary directory
    """
    olex.m("stop listen")
    Method_shelx_solution.post_solution(self, RunPrgObject)
    for i in xrange(int(olx.xf_au_GetAtomCount())):
      olx.xf_au_SetAtomU(i, "0.06")

class Method_cctbx_refinement(Method_refinement):

  flack = None

  def pre_refinement(self, RunPrgObject):
    RunPrgObject.make_unique_names = True
    Method_refinement.pre_refinement(self, RunPrgObject)

  def run(self, RunPrgObject):
    from refinement import FullMatrixRefine
    from smtbx.refinement.constraints import InvalidConstraint
    self.failure = True
    print 'STARTING cctbx refinement'
    verbose = OV.GetParam('olex2.verbose')
    cctbx = FullMatrixRefine(
      max_cycles=RunPrgObject.params.snum.refinement.max_cycles,
      max_peaks=RunPrgObject.params.snum.refinement.max_peaks,
      verbose=verbose, on_completion=self.writeRefinementInfoForGui)
    try:
      cctbx.run()
      self.flack = cctbx.flack
    except InvalidConstraint, e:
      print e
    except NotImplementedError, e:
      print e
    else:
      self.failure = cctbx.failure
      if not self.failure:
        OV.SetVar('cctbx_R1',cctbx.r1[0])
        OV.File('%s.res' %OV.FileName())
    finally:
      OV.DeleteBitmap('refine')

  def getFlack(self):
    return self.flack
  
  def writeRefinementInfoForGui(self, cif):
    for key, value in cif.iteritems():
      if "." in value:
        try:
          cif[key] = "%.4f" %float(value)
        except:
          pass
    f = open("%s/etc/CIF/olex2refinedata.html" %OV.BaseDir())
    t = f.read() %cif
    OV.write_to_olex('refinedata.htm',t)  


class Method_cctbx_ChargeFlip(Method_solution):

  def run(self, RunPrgObject):
    from cctbx_olex_adapter import OlexCctbxSolve
    import traceback
    print 'STARTING cctbx Charge Flip'
    RunPrgObject.solve = True
    cctbx = OlexCctbxSolve()

    #solving_interval = int(float(self.getArgs().split()[1]))
    solving_interval = self.phil_index.params.flipping_interval

    formula_l = olx.xf_GetFormula('list')
    formula_l = formula_l.split(",")
    formula_d = {}
    for item in formula_l:
      item = item.split(":")
      formula_d.setdefault(item[0], {'count':float(item[1])})
    try:
      have_solution = cctbx.runChargeFlippingSolution(solving_interval=solving_interval)
      if not have_solution:
        print "*** No solution found ***"
    except Exception, err:
      print err
      traceback.print_exc()
    try:
      olx.Freeze(True)
      olx.xf_EndUpdate()
      olx.Compaq('-a')
      olx.Move()
    finally:
      olx.Freeze(False)
    #olx.VSS(True)
    #olex.m("sel -a")
    #olex.m("name sel 1")
    OV.DeleteBitmap('solve')
    file = r"%s/%s.res" %(olx.FilePath(), RunPrgObject.fileName)
    olx.xf_SaveSolution(file)
    olx.Atreap(file)

class Method_SIR(Method_solution):

  def run(self, RunPrgObject):
    from olexsir import Sir

    print 'STARTING %s %s with %s' %(
      RunPrgObject.program.name,
      RunPrgObject.program.program_type, self.name)
    RunPrgObject.solve = True
    sirversion = RunPrgObject.program.versions
    sirfile = "%s.sir"%(OV.FileName())
    filename = OV.FileName()
    Z = float(olx.xf_au_GetZ())
    cell = ''.join(olx.xf_au_GetCell().split(','))
    hklfile = OV.HKLSrc().split('/')[-1]
    contents = ''
    for item in olx.xf_GetFormula('list').split(","):
        item = item.split(":")
        item[1] = int(float(item[1]) * Z)
        contents += "%s %i " %(item[0], item[1])

    oxs = Sir()
    (data, inv, phase) = oxs.getDirectives()

    filein = open(olx.FileFull(),'r')
    filedata = filein.readlines()
    filein.close()
    esd = []
    for line in filedata:
      if 'zerr ' in line.lower():
        esd = line.split()
    
    if len(esd) > 2:
        del esd[1]
        del esd[0]
        try:
            oxs.setDirectives(errors = ' '.join(esd))
        except TypeError:
            pass

    oxs.setDirectives(cell=cell, SPACEGROUP=olx.xf_au_GetCellSymm(),
            Format='(3i4,2f8.0)', contents=contents, Reflections=hklfile)

    opts = {}
    for instruction in self.instructions():
        if OV.FindValue('settings_%s' %instruction.name) in (True, 'True', 'true'):
            if instruction.name not in ('Gui', 'Data', 'Phase', 'Misc'):
                opts[instruction.name] = True
            for option in self.options(instruction.name):
                value = OV.FindValue('settings_%s_%s'%(instruction.name, option.name))
                if value not in ('', 'None', None):
                    if option.name in ('Fvalues', 'RELAX'):
                        value = str(value)
                        opts[value] = True
                    else:
                        opts[option.name] = value

    if self.name in 'Direct Methods':
        oxs.setDirectives(Tangent=True)
    elif self.name in 'Patterson Method':
        oxs.setDirectives(Patterson=True)

    oxs.setDirectives(**opts)

    if OV.FindValue('settings_Gui') in (True, 'True', 'true'):
        oxs.Gui = True
        print 'Starting with GUI'
    else:
        oxs.Gui = False
        print 'Starting without GUI'

    if oxs.write(filename, data, inv, phase):
        oxs.Exec(sirfile, sirversion)
        OV.DeleteBitmap('solve')
        file = r"'%s/%s.res'" %(olx.FilePath(), OV.FileName())
        olx.Atreap(file)
    else:
        print 'No *.sir File!'

def defineExternalPrograms():
  # define solution methods

  direct_methods = Method_shelx_direct_methods(direct_methods_phil)
  patterson = Method_shelx_solution(patterson_phil)
  dual_space = Method_shelxd(dual_space_phil)
  charge_flipping = Method_cctbx_ChargeFlip(charge_flipping_phil)
  sir2008_dm = Method_SIR(sir_dm_phil)
  sir2008_patt = Method_SIR(sir_patt_phil)

  # define refinement methods
  least_squares = Method_shelx_refinement(least_squares_phil)
  cgls = Method_shelx_refinement(cgls_phil)
  gauss_newton = Method_cctbx_refinement(gauss_newton_phil)
  levenberg_marquardt = Method_cctbx_refinement(levenberg_marquardt_phil)

  # define solution programs
  ShelXS = Program(
    name='ShelXS',
    program_type='solution',
    author="G.M.Sheldrick",
    reference="SHELXS, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["shelxs.exe", "shelxs"])
  ShelXS86 = Program(
    name='ShelXS86',
    program_type='solution',
    author="G.M.Sheldrick",
    reference="ShelXS86, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["shelxs86.exe", "shelxs86"])
  XS = Program(
    name='XS',
    program_type='solution',
    author="G.M.Sheldrick/Bruker",
    reference="XS, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["xs.exe", "xs"])
  ShelXD = Program(
    name='ShelXD',
    program_type='solution',
    author="G.M.Sheldrick",
    reference="SHELXD, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["shelxd.exe", "shelxd"])
  XM = Program(
    name='XM',
    program_type='solution',
    author="G.M.Sheldrick/Bruker",
    reference="XM, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["xm.exe", "xm"])
  smtbx_solve = Program(
    name='olex2.solve',
    program_type='solution',
    author="Luc Bourhis",
    reference="olex2.solve (L.J. Bourhis, O.V. Dolomanov, R.J. Gildea, J.A.K. Howard,\nH. Puschmann, in preparation, 2011)")
  SIR2008 = Program(
    name='SIR2008',
    program_type='solution',
    author="Maria C. Burla, Rocco Caliandro, Mercedes Camalli, Benedetta Carrozzini, Giovanni Luca Cascarano, Liberato De Caro, Carmelo Giacovazzo, Giampiero Polidori, Dritan Siliqi, Riccardo Spagna",
    reference="J. Appl. Cryst. (2007). 40, 609-613",
    versions = '2008',
    execs=["sir2008.exe", "sir2008"])

  ShelXS.addMethod(direct_methods)
  ShelXS.addMethod(patterson)
  ShelXS86.addMethod(direct_methods)
  ShelXS86.addMethod(patterson)
  XS.addMethod(direct_methods)
  XS.addMethod(patterson)
  ShelXD.addMethod(dual_space)
  XM.addMethod(dual_space)
  smtbx_solve.addMethod(charge_flipping)
  SIR2008.addMethod(sir2008_dm)
  SIR2008.addMethod(sir2008_patt)

  # define refinement programs
  ShelXL = Program(
    name='ShelXL',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference="SHELXL, G.M. Sheldrick, Acta Cryst.\n2008). A64, 112-122",
    execs=["shelxl.exe", "shelxl"])
  XL = Program(
    name='XL',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference="XL, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["xl.exe", "xl"])
  XLMP = Program(
    name='XLMP',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference="XLMP, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["xlmp.exe", "xlmp"])
  ShelXH = Program(
    name='ShelXH',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference="SHELXH, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["shelxh.exe", "shelxh"])
  XH = Program(
    name='XH',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference="XH, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["xh.exe", "xh"])
  ShelXL_ifc = Program(
    name='ShelXL_ifc',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference="SHELXL, G.M. Sheldrick, Acta Cryst.\n(2008). A64, 112-122",
    execs=["shelxl_ifc"])
  smtbx_refine = Program(
    name='olex2.refine',
    program_type='refinement',
    author="L.J. Bourhis, O.V. Dolomanov, R.J. Gildea",
    reference="olex2.refine (L.J. Bourhis, O.V. Dolomanov, R.J. Gildea, J.A.K. Howard,\nH. Puschmann, in preparation, 2011)")

  for prg in (ShelXL, XL, XLMP, ShelXH, XH, ShelXL_ifc):
    for method in (least_squares, cgls):
      prg.addMethod(method)
  smtbx_refine.addMethod(gauss_newton)
  smtbx_refine.addMethod(levenberg_marquardt)

  SPD = ExternalProgramDictionary()
  for prg in (ShelXS, ShelXS86, XS, ShelXD, XM, smtbx_solve, SIR2008):
    SPD.addProgram(prg)

  RPD = ExternalProgramDictionary()
  for prg in (ShelXL, XL, XLMP, ShelXH, XH, ShelXL_ifc, smtbx_refine):
    RPD.addProgram(prg)

  return SPD, RPD


def getFormulaAsDict(formula):
  formula = formula.split()
  d = {}
  for item in formula:
    try:
      d.setdefault(item[:1],float(item[1:]))
    except ValueError:
      try:
        d.setdefault(item[:2],float(item[2:]))
      except ValueError:
        if len(item) == 1:
          d.setdefault(item[:1],1.0)
        else:
          d.setdefault(item[:2],1.0)
    except IndexError:
      if len(item) == 1:
        d.setdefault(item[:1],1.0)
      else:
        d.setdefault(item[:2],1.0)
    except Exception, ex:
      print >> sys.stderr, "An error occured in the function getFormulaAsDict.\nFormula: %s, item: %s" %(formula, item)
      sys.stderr.formatExceptionInfo()
  return d

sir_dm_phil = phil_interface.parse("""
name = 'Direct Methods'
  .type=str
atom_sites_solution=other
  .type=str
instructions {
  Gui 
  .optional=True
  {
    values {}
    default=True
      .type=bool
    }
  Data 
  .optional=True
  {
    values {
        Fvalues = *FOSQUARED FOBS
          .type = choice
          .caption = 'F\xc2\xb2/Fo\n'
        RHOMAX = 0.25
          .type = float
        RESMAX = None
          .type = float
        BFACTOR = None
          .type = float
          .caption = 'BFAC'
        SFACTORS = None
          .type = str
          .caption = 'SFAC'
    }
    default=True
      .type=bool
    }
  Phase
  .optional=True
    {
      values {
        SIZE=*None xs s m l xl xxl
          .type = choice
        ITERATION=None
          .type = int
        CYCLE=None
          .type = int
        FRAGMENT=None
          .type = str
          .caption = 'FRAG'
        RESIDUAL=None
          .type = float
          .caption = 'R %'
          }
      default=False
        .type=bool
      }
  Misc
  .optional=True
    {
      values {
        RELAX=*None RELAX UNRELAX
          .type = choice
        NREFLECTION = None
          .type = float
          .caption = 'NREF'
        RECORD = None
          .type = int
        EXPAND = None
          .type = float
        GMIN = None
          .type = float
          }
      default=False
        .type=bool
      }
  Tangent
  .optional=True
  {
    values {
        STRIAL=None
          .type = int
          .caption = 'STRIAL     '
        TRIAL=None
          .type = int
    }
    default=False
      .type=bool
    }
  Cochran 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nquartets 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nolsq 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nosigma 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Electrons 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  }
""")

sir_patt_phil = phil_interface.parse("""
name = 'Patterson Method'
  .type=str
atom_sites_solution=other
  .type=str
instructions {
  Gui 
  .optional=True
  {
    values {}
    default=True
      .type=bool
    }
  Data 
  .optional=True
  {
    values {
        Fvalues = *FOSQUARED FOBS
          .type = choice
          .caption = 'F\xc2\xb2/Fo\n'
        RHOMAX = 0.25
          .type = float
        RESMAX = None
          .type = float
        BFACTOR = None
          .type = float
          .caption = 'BFAC'
        SFACTORS = None
          .type = str
          .caption = 'SFAC'
    }
    default=True
      .type=bool
    }
  Phase
  .optional=True
    {
      values {
        SIZE=*None xs s m l xl xxl
          .type = choice
        ITERATION=None
          .type = int
        CYCLE=None
          .type = int
        FRAGMENT=None
          .type = str
          .caption = 'FRAG'
        RESIDUAL=None
          .type = float
          .caption = 'R %'
          }
      default=False
        .type=bool
      }
  Misc
  .optional=True
    {
      values {
        RELAX=*None RELAX UNRELAX
          .type = choice
        NREFLECTION = None
          .type = float
          .caption = 'NREF'
        RECORD = None
          .type = int
        EXPAND = None
          .type = float
        GMIN = None
          .type = float
          }
      default=False
        .type=bool
      }
  Patterson
  .optional=True
  {
    values {
        PEAKS=None
          .type = int
    }
    default=False
      .type=bool
    }
  Cochran 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nquartets 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nolsq 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Nosigma 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  Electrons 
  .optional=True
  {
    values {}
    default=False
      .type=bool
    }
  }
""")

shelxs_phil = phil_interface.parse("""
esel
  .optional=True
{
  values {
    Emin=1.2
      .type=float
    Emax=5
      .type=float
    dU=0.05
      .type=float
    renorm=.7
      .type=float
    axis=0
      .type=int
  }
  default=False
    .type=bool
}
egen
  .optional=True
{
  values {
    d_min=None
      .type=float
    d_max=None
      .type=float
  }
  default=False
    .type=bool
}
grid
  .optional=True
{
  values {
    sl=None
      .type=float
    sa=None
      .type=float
    sd=None
      .type=float
    dl=None
      .type=float
    da=None
      .type=float
    dd=None
      .type=float
  }
  default=False
    .type=bool
}
""")

direct_methods_phil = phil_interface.parse("""
name = 'Direct Methods'
  .type=str
atom_sites_solution=direct
  .type=str
instructions {
  tref {
    values {
      np = 500
        .type=int
      nE = None
        .type=int
      kapscal = None
        .type=float
      ntan = None
        .type=int
      wn = None
        .type=float
    }
    default = True
      .type=bool
  }
  init
    .optional=True
  {
    values {
      nn=None
        .type=int
      nf=None
        .type=int
      s_plus=0.8
        .type=float
      s_minus=0.2
        .type=float
      wr=0.2
        .type=float
    }
    default = False
      .type=bool
  }
  phan
    .optional=True
  {
    values {
      steps = 10
        .type=int
      cool = 0.9
        .type=float
      Boltz = None
        .type=float
      ns = None
        .type=int
      mtpr = 40
        .type=int
      mnqr = 10
        .type=int
    }
    default = False
      .type=bool
  }
  include scope ExternalPrgParameters.shelxs_phil
}
""", process_includes=True)

patterson_phil = phil_interface.parse("""
name = 'Patterson Method'
  .type=str
atom_sites_solution=heavy
  .type=str
instructions {
  patt {
    values {
      nv=None
        .type=int
      dmin=None
        .type=float
      resl=None
        .type=float
      Nsup=None
        .type=int
      Zmin=None
        .type=int
      maxat=None
        .type=int
    }
    default=True
      .type=bool
  }
  vect
    .optional=True
  {
    values {
      X=None
        .type=float
      Y=None
        .type=float
      Z=None
        .type=float
    }
    default=False
      .type=bool
  }
  include scope ExternalPrgParameters.shelxs_phil
}
""", process_includes=True)

dual_space_phil = phil_interface.parse("""
name='Dual Space'
  .type=str
atom_sites_solution=dual
  .type=str
instructions {
  ntry
    .optional=True
  {
    values {
      ntry=100
        .type=int
    }
    default=True
      .type=bool
  }
  find
    .optional=True
  {
    values {
      na=0
        .type=int
      ncy=None
        .type=int
    }
    default=True
      .type=bool
  }
  mind
    .optional=True
  {
    values {
      mdis=1.0
        .type=float
      mdeq=2.2
        .type=float
    }
    default=True
      .type=bool
  }
  plop
    .optional=True
  {
    values {
      a=None
        .type=int
        .caption=1
      b=None
        .type=int
        .caption=2
      c=None
        .type=int
        .caption=3
      d=None
        .type=int
        .caption=4
      e=None
        .type=int
        .caption=5
      f=None
        .type=int
        .caption=6
      g=None
        .type=int
        .caption=7
      h=None
        .type=int
        .caption=8
      i=None
        .type=int
        .caption=9
      j=None
        .type=int
        .caption=10
    }
    default=True
      .type=bool
  }
}
""")

  #{'name':'SHEL', 'values':['dmax:', 'dmin:0']},
  #{'name':'PATS', 'values':['+np or -dis:100', 'npt:', 'nf:5']},
  #{'name':'GROP', 'values':['nor:99', 'E<sub>g</sub>:1.5', 'd<sub>g</sub>:1.2', 'ntr:99']},
  #{'name':'PSMF', 'values':['pres:3.0', 'psfac:0.34']},
  #{'name':'FRES', 'values':['res:3.0',]},
  #{'name':'ESEL', 'values':['Emin:', 'dlim:1.0']},
  #{'name':'SHEL', 'values':['dmax:', 'dmin:0']},
  #{'name':'PATS', 'values':['+np or -dis:100', 'npt:', 'nf:5']},
  #{'name':'GROP', 'values':['nor:99', 'E<sub>g</sub>:1.5', 'd<sub>g</sub>:1.2', 'ntr:99']},
  #{'name':'PSMF', 'values':['pres:3.0', 'psfac:0.34']},
  #{'name':'FRES', 'values':['res:3.0',]},

  #{'name':'DSUL', 'values':['nss:0',]},
  #{'name':'TANG', 'values':['ftan:0.9', 'fex:0.4']},
  #{'name':'NTPR', 'values':['ntpr:100',]},
  #{'name':'SKIP', 'values':['min2:0.5',]},
  #{'name':'WEED', 'values':['fr:0.3',]},
  #{'name':'CCWT', 'values':['g:0.1',]},
  #{'name':'TEST', 'values':['CCmin:', 'delCC:']},
  #{'name':'KEEP', 'values':['nh:0',]},
  #{'name':'PREJ', 'values':['max:3', 'dsp:-0.01', 'mf:1']},
  #{'name':'SEED', 'values':['nrand:0',]},
  #{'name':'MOVE', 'values':['dx:0', 'dy:0', 'dz:0', 'sign:1']},

charge_flipping_phil = phil_interface.parse("""
name = 'Charge Flipping'
  .type=str
atom_sites_solution=other
  .type=str
flipping_interval=60
  .type=int
instructions {
  cf {
    values {
      amplitude_type = F E *quasi-E
        .type = choice
        .caption = AMPT
      max_attempts_to_get_phase_transition = 5
        .type = int
        .caption = MAPT
      max_attempts_to_get_sharp_correlation_map = 5
        .type = int
        .caption = MACM
      max_solving_iterations = 500
        .type = int
        .caption = MASI
        }
    default=True
      .type=bool
    }
  }
""")

shelxl_phil = phil_interface.parse("""
plan
  .optional=True
{
  values {
    npeaks=20
      .type=int
    d1=None
      .type=float
    d2=None
      .type=float
  }
  default=True
    .type=bool
}
fmap
  .optional=True
{
  values {
    code=2
      .type=int
    axis=None
      .type=int(value_min=1, value_max=3)
    nl=53
      .type=int
  }
  default=True
    .type=bool
}
temp
  .optional=True
{
  values {
    T=None
      .type=int
  }
  default=False
    .type=bool
}
""")

least_squares_phil = phil_interface.parse("""
name = 'Least Squares'
  .type=str
instructions {
  ls
    .caption = 'L.S.'
  {
    name='L.S.'
      .type=str
    values {
      nls=4
        .type=int
      nrf=0
        .type=int
      nextra=0
        .type=int
      maxvec=511
        .type=int
    }
    default=True
      .type=bool
  }
  include scope ExternalPrgParameters.shelxl_phil
  acta
    .optional=True
  {
    values {
      two_theta_full=None
        .caption=2thetafull
        .type=float
    }
    default=False
      .type=bool
  }
}
""", process_includes=True)

cgls_phil = phil_interface.parse("""
name = CGLS
  .type=str
instructions {
  cgls {
    values {
      nls=4
        .type=int
      nrf=0
        .type=int
      nextra=0
        .type=int
      maxvec=511
        .type=int
    }
    default=True
      .type=bool
  }
  include scope ExternalPrgParameters.shelxl_phil
}
""", process_includes=True)

gauss_newton_phil = phil_interface.parse("""
name = 'Gauss-Newton'
  .type=str
""")

levenberg_marquardt_phil = phil_interface.parse("""
name = 'Levenberg-Marquardt'
  .type=str
""")

SPD, RPD = defineExternalPrograms()

if __name__ == '__main__':
  SPD, RPD = defineExternalPrograms()
