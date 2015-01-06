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

global RPD
RPD = {}
global SPD
SPD = {}
global managed_references
managed_references = set()

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
  def __init__(self, name, program_type, author, reference, brief_reference,
               execs=None,
               versions=None, phil_entry_name=None):
    self.name = name
    self.program_type = program_type
    self.author = author
    self.reference = reference
    self.brief_reference = brief_reference
    self.execs = execs
    self.versions = versions
    self.methods = {}
    self.counter = 0
    self.phil_entry_name = phil_entry_name

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
  command_line_options = None
  failure = False
  running = False

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

  def do_run(self, RunPrgObject):
    """Must be redefined in subclass.

    It is from within this method that the external program will be run.
    """
    assert 0, 'do_run must be defined!'

  def run(self, RunPrgObject):
    if Method.running:
      return False
    Method.running = True
    try:
      if RunPrgObject.program.phil_entry_name:
        name = "snum.%s.%s.command_line" %(
          RunPrgObject.program.program_type, RunPrgObject.program.phil_entry_name)
        self.command_line_options = OV.GetParam(name, None)
      else:
        self.command_line_options = None
      self.do_run(RunPrgObject)
      return True
    finally:
      Method.running = False

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
        ins = olx.xf.exptl.Temperature()
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
        if instruction.name.endswith('command_line'): continue
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
                pass
              elif '.' in value:
                value = float(value)
              else:
                value = int(value)
          except ValueError:
            pass
          arg += ' %s' %value
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
        cell_volume = float(olx.xf.au.GetCellVolume())
        Z = float(olx.xf.au.GetZ())
        guess_C = int(cell_volume/Z/18)
        f = OV.GetUserInput(1,'Invalid formula','Enter correct formula...')
        if f and f!= 'Enter correct formula...':
          try:
            olx.xf.SetFormula(f)
            RunPrgObject.formula = olx.xf.GetFormula()
          except RuntimeError:
            formula['C'] = guess_C
            RunPrgObject.formula = ' '.join('%s%s' %(type,count) for type,count in formula.items())
            olx.xf.SetFormula(RunPrgObject.formula)
        else:
          formula['C'] = guess_C
          RunPrgObject.formula = ' '.join('%s%s' %(type,count) for type,count in formula.items())
          olx.xf.SetFormula(RunPrgObject.formula)
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
    if self.name == 'Structure Expansion':
      args += "-atoms"
    return args

  def post_solution(self, RunPrgObject):
    """Things to be done after running the solution program.
    """
    # TREF sticks if used as TREF 2000
    olx.DelIns('TREF')
    if RunPrgObject.HasGUI:
      olx.Compaq(a=True)
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
    for i in xrange(int(olx.xf.au.GetAtomCount())):
      ret = olx.xf.au.IsPeak(i)
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
      current_R1 = OV.GetParam('snum.current_r1')
      if current_R1 < OV.GetParam('snum.refinement.update_weight_maxR1'):
        suggested_weight = OV.GetParam('snum.refinement.suggested_weight')
        if suggested_weight is not None:
          olx.UpdateWght(*suggested_weight)

    if RunPrgObject.params.user.auto_insert_acta_stuff:
      radiation = olx.xf.exptl.Radiation()

      # Check whether these are present. If so, do nothing.
      more = olx.Ins('MORE')
      if more == "n/a":
        OV.AddIns("MORE -1")
      bond = olx.Ins('BOND')
      if bond == "n/a" or not bond:
        OV.AddIns("BOND $H", quiet=True)
      acta= olx.Ins('ACTA')
      if acta == "n/a":
        if radiation == "0.71073":
          OV.AddIns("ACTA 52")
      OV.AddIns('CONF', quiet=True)

    if RunPrgObject.make_unique_names:
      pass
      #olx.Sel('-a')
      #olx.Name('sel 1 -c')
    if RunPrgObject.params.snum.auto_hydrogen_naming:
      olx.FixHL()

    wave_length = float(olx.xf.exptl.Radiation())
    if round(wave_length, 2) == round(0.71073,2) or round(wave_length, 2) == round(1.5414, 2) or round(wave_length, 2)  == round(0.56053, 2):
      pass
    else:
      print "Using non-standard wavelength (%f) calculating DISP and adding\n"%wave_length
      olx.GenDisp()

  def post_refinement(self, RunPrgObject):
    pass

class Method_shelx(Method):

  def do_run(self, RunPrgObject):
    """Runs any SHELX refinement/solution program
    """
    print 'STARTING SHELX %s with %s' %(
      RunPrgObject.program.program_type, self.name)
    prgName = olx.file.GetName(RunPrgObject.shelx)
    #olex.m("User '%s'" %RunPrgObject.tempPath)
    olx.User("%s" %RunPrgObject.tempPath)
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
    if prgName in ('shelxs', 'xs', 'shelxs86', 'shelxs13'):
      import fileinput, string, sys
      for line in fileinput.input(xl_ins_filename.lower()+'.ins',inplace=1):
        if 'DISP' in line:
          continue
        sys.stdout.write(line)
    commands = [xl_ins_filename.lower()]  #This is correct!!!!!!
    #sys.stdout.graph = RunPrgObject.Graph()
    if self.command_line_options:
      commands += self.command_line_options.split()
    success = olx.Exec(prgName, *commands, q=(not RunPrgObject.params.snum.shelx_output))
    if not success:
      raise RuntimeError(
        'you may be using an outdated version of %s' %(prgName))
    olx.WaitFor('process') # uncomment me!

    additions = ['', '_a', '_b', '_c', '_d', '_e']
    self.failure = True
    for add in additions:
      p = "%s%s.res" %(xl_ins_filename, add)
      if os.path.exists(p):
        if os.path.getsize(p) != 0:
          self.failure = False
          break
    olx.User(RunPrgObject.filePath)


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
    self.cif = {}

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
    self.gather_refinement_information()
    writeRefinementInfoIntoRes(self.cif)
    params = {
      'snum.refinement.max_peak' : 'peak',
      'snum.refinement.max_hole' : 'hole',
      'snum.refinement.max_shift_site' : 'max_shift',
      'snum.refinement.max_shift_site_atom' : 'max_shift_object',
      'snum.refinement.max_shift_over_esd' : 'max_shift/esd',
      'snum.refinement.max_shift_over_esd_atom' : 'max_shift/esd_object',
      'snum.refinement.max_shift_u' : 'max_dU',
      'snum.refinement.max_shift_u_atom' : 'max_dU_object',
      'snum.refinement.flack_str' : 'flack',
      'snum.refinement.goof' : "s",
    }
    for k,v in params.iteritems():
      v = olx.Lst(v)
      if v == 'n/a':  v = 0
      OV.SetParam(k, v)

  def gather_refinement_information(self):
    cif = {}
    cif.setdefault('_refine_ls_R_factor_all', olx.Lst('R1all'))
    cif.setdefault('_refine_ls_R_factor_gt', olx.Lst('R1'))
    cif.setdefault('_refine_ls_wR_factor_ref', olx.Lst('wR2'))
    cif.setdefault('_refine_ls_goodness_of_fit_ref', olx.Lst('s'))
    cif.setdefault('_refine_ls_shift/su_max', olx.Lst('max_shift/esd'))
    cif.setdefault('_refine_ls_shift/su_mean', olx.Lst('mean_shift/esd'))
    cif.setdefault('_reflns_number_total', olx.Lst('ref_total'))
    cif.setdefault('_reflns_number_gt', olx.Lst('ref_4sig'))
    cif.setdefault('_refine_ls_number_parameters', olx.Lst('params_n'))
    cif.setdefault('_refine_ls_number_restraints', olx.Lst('restraints_n'))
    cif.setdefault('_refine_ls_abs_structure_Flack', olx.Lst('flack'))
    cif.setdefault('_refine_diff_density_max', olx.Lst('peak'))
    cif.setdefault('_refine_diff_density_min', olx.Lst('hole'))
    self.cif = cif

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
    lstPath = "%s/%s.lst" %(OV.FilePath(), OV.FileName())
    if os.path.exists(lstPath):
      import lst_reader
      lstValues = lst_reader.reader(path=lstPath).values()

      RunPrgObject.Ralpha = lstValues.get('Ralpha','')
      RunPrgObject.Nqual = lstValues.get('Nqual','')
      RunPrgObject.CFOM = lstValues.get('CFOM','')


class Method_shelxd(Method_shelx_solution):

  def calculate_defaults(self):
    """Defines controls in Olex2 for each argument in self.args and then calculates
    sensible default values for PLOP and FIND based on the cell volume.
    """
    Method.calculate_defaults(self) # Define controls in Olex2
    #volume = float(olex.f("Cell(volume)"))
    volume = float(olx.xf.au.GetCellVolume())
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
      'onclick':r'spy.stopShelx()',
    }
    button_html = htmlTools.make_input_button(button_d)
    html = '''
  <tr>%s<td>%s</td></tr>
  ''' %(htmlTools.make_table_first_col(), button_html)
    return html

  def pre_solution(self, RunPrgObject):
    args = Method_shelx_solution.pre_solution(self, RunPrgObject)
    volume = float(olx.xf.au.GetCellVolume())
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

  def do_run(self, RunPrgObject):
    """Makes Olex listen to the temporary directory before running the executable
    so that intermediate solutions will be displayed onscreen.
    """
    listen_file = '%s/%s.res' %(RunPrgObject.tempPath,RunPrgObject.hkl_src_name)
    OV.Listen(listen_file)
    Method_shelx_solution.do_run(self, RunPrgObject)

  def post_solution(self, RunPrgObject):
    """Stops listening to the temporary directory
    """
    olex.m("stop listen")
    Method_shelx_solution.post_solution(self, RunPrgObject)
    for i in xrange(int(olx.xf.au.GetAtomCount())):
      olx.xf.au.SetAtomU(i, "0.06")

class Method_cctbx_refinement(Method_refinement):

  flack = None

  def pre_refinement(self, RunPrgObject):
    RunPrgObject.make_unique_names = True
    Method_refinement.pre_refinement(self, RunPrgObject)

  def do_run(self, RunPrgObject):
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

  def post_refinement(self, RunPrgObject):
    writeRefinementInfoIntoRes(self.cif)
    txt = '''
    R1_all=%(_refine_ls_R_factor_all)s;
    R1_gt = %(_refine_ls_R_factor_gt)s;
    wR_ref = %(_refine_ls_wR_factor_ref)s;
    GOOF = %(_refine_ls_goodness_of_fit_ref)s;
    Shift_max = %(_refine_ls_shift/su_max)s;
    Shift_mean = %(_refine_ls_shift/su_mean)s;
    Reflections_all = %(_reflns_number_total)s;
    Reflections_gt = %(_reflns_number_gt)s;
    Parameters = %(_refine_ls_number_parameters)s;
    Hole = %(_refine_diff_density_min)s;
    Peak = %(_refine_diff_density_max)s;
    Flack = %(_refine_ls_abs_structure_Flack)s;
    ''' %self.cif
    try:
      olx.xf.RefinementInfo(txt)
    except:
      pass

  def writeRefinementInfoForGui(self, cif):
    for key, value in cif.iteritems():
      if "." in value:
        try:
          cif[key] = "%.4f" %float(value)
        except:
          pass
    f = open("%s/etc/CIF/olex2refinedata.html" %OV.BaseDir())
    t = f.read() %cif
    f.close()
    OV.write_to_olex('refinedata.htm',t)
    self.cif = cif



class Method_cctbx_ChargeFlip(Method_solution):

  def do_run(self, RunPrgObject):
    from cctbx_olex_adapter import OlexCctbxSolve
    import traceback
    print 'STARTING cctbx Charge Flip'
    RunPrgObject.solve = True
    cctbx = OlexCctbxSolve()

    #solving_interval = int(float(self.getArgs().split()[1]))
    solving_interval = self.phil_index.params.flipping_interval

    formula_l = olx.xf.GetFormula('list')
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
    if OV.HasGUI():
      try:
        olx.Freeze(True)
        olx.xf.EndUpdate()
        olx.Move()
      finally:
        olx.Freeze(False)
    #olx.VSS(True)
    #olex.m("sel -a")
    #olex.m("name sel 1")
    OV.DeleteBitmap('solve')
    file_name = r"%s/%s.res" %(olx.FilePath(), RunPrgObject.fileName)
    olx.xf.SaveSolution(file_name)
    olx.Atreap('"%s"' %file_name)

class Method_Superflip(Method_solution):

  def __init__(self, phil_object):
    Method_solution.__init__(self, phil_object)
    self.to_cleanup = []
    prefix = "settings.superflip"
    defaults = {
      'repeatmode' : 'never',
      'repeatmode.trials' : '1',
      'max_cycles' : '10000',
      'fastfft' : 'false',
      'data.normalize': 'local',
      'data.nresshells': '100',
      'data.weakratio': '0.2',
      'resolution.limit': 'false',
      'resolution.units': 'd',
      'resolution.high': '100',
      'resolution.low': '0',
      'data.missing.process': 'bound',
      'data.missing.rlim': '0.4',
      'data.missing.ubound': '4',
      'convergence.mode': 'normal',
      'convergence.threshold': '0.8',
      'delta.method': 'auto',
      'delta.value': '1.3',
      'convergence.polish': 'true',
      'convergence.polish.cycles': '5',
      'symmetry.derive': 'use',
      'symmetry.search': 'average',
      'cleanup': 'true',
      'use_centering' : 'true'
    }
    for k,v in defaults.iteritems():
      olx.SetVar("%s.%s" %(prefix,k), v)


  def pre_solution(self, RunPrgObject):
    pass

  def create_input(self):
    self.derive_symmetry = olx.GetVar('settings.superflip.symmetry.search') != 'no' and\
          olx.GetVar('settings.superflip.symmetry.derive') == 'use'
    input = []
    input.append('title ' + olx.Title())
    sg = olx.xf.au.GetCellSymm()
    sg_info = olex_core.SGInfo(sg, False)
    if not self.derive_symmetry:
      cellp = olx.xf.au.GetCell().split(',')
      system = sg_info['System']
      if system == 'Monoclinic':
        axis = sg_info['Axis']
        if axis == 'a':
          cellp[4] = cellp[5] = '90'
        elif axis == 'b':
          cellp[3] = cellp[5] = '90'
        elif axis == 'c':
          cellp[3] = cellp[4] =  '90'
      elif system == 'Cubic' or system == 'Tetragonal' or system == 'Orthorhombic':
        cellp[3] = cellp[4] = cellp[5] = '90'
        if system == 'Cubic':
          cellp[0] = cellp[1] = cellp[2]
        elif system == 'Tetragonal':
          cellp[0] = cellp[1]
      elif system == 'Hexagonal' or system == 'Trigonal':
        cellp[3] = cellp[4] = '90'
        cellp[5] = '120'
      input.append('cell ' + ' '.join(cellp))
    else:
      input.append('cell ' + olx.xf.au.GetCell().replace(',', ' '))
    input.append('lambda %s' %olx.xf.exptl.Radiation())

    input.append('symmetry')
    if self.derive_symmetry:
      input.append("+X +Y +Z")
    else:
      for i in sg_info['MatricesAll']:
        input.append(olex_core.MatrixToString(i))
    input.append('endsymmetry')

    input.append('centers')
    input.append("0 0 0")
    if (not self.derive_symmetry) or (olx.GetVar('settings.superflip.use_centering') == 'true'):
      for i in sg_info['Lattice']['Translations']:
        input.append("%s %s %s" %i)
    input.append('endcenters')


    v = olx.GetVar('settings.superflip.repeatmode')
    if v == 'trials':
      input.append("repeatmode %s" %olx.GetVar('settings.superflip.repeatmode.trials'))
    else:
      input.append("repeatmode %s" %v)
    input.append('maxcycles %s'\
                   %olx.GetVar('settings.superflip.max_cycles'))
    if olx.GetVar('settings.superflip.fastfft') == 'true':
      input.append('fastfft yes')
    else:
      input.append('fastfft no')
    input.append('voxel AUTO')
    input.append('weakratio %s' %olx.GetVar('settings.superflip.data.weakratio'))
    v = olx.GetVar('settings.superflip.data.missing.process')
    if v == 'zero':
      input.append("missing zero")
    elif v == 'float':
      input.append("missing float %s" %olx.GetVar('settings.superflip.data.missing.rlim'))
    else:
      input.append("missing %s %s %s"  %(v,
                                       olx.GetVar('settings.superflip.data.missing.rlim'),
                                       olx.GetVar('settings.superflip.data.missing.ubound')))

    if olx.GetVar('settings.superflip.resolution.limit') == 'true':
      input.append('resunit %s' %olx.GetVar('settings.superflip.resolution.units'))
      input.append('reslimit %s %s' %(olx.GetVar('settings.superflip.resolution.high'),
                                      olx.GetVar('settings.superflip.resolution.low')))

    v =  olx.GetVar('settings.superflip.data.normalize')
    input.append('normalise %s' %v)
    if v == 'local':
      input.append('nresshells %s' %olx.GetVar('settings.superflip.data.nresshells'))

    input.append("convergencemode %s %s" %(
      olx.GetVar('settings.superflip.convergence.mode'),
      olx.GetVar('settings.superflip.convergence.threshold'))
      )

    v = olx.GetVar('settings.superflip.convergence.polish')
    if v == 'true':
      input.append('polish yes %s' %olx.GetVar('settings.superflip.convergence.polish.cycles'))
    else:
      input.append('polish no')

    self.file_name = olx.FileName()
    input.append('searchsymmetry %s' %olx.GetVar('settings.superflip.symmetry.search'))
    input.append('derivesymmetry %s' %olx.GetVar('settings.superflip.symmetry.derive'))
    input.append('outputfile %s.m81' %self.file_name)
    #setup edma
    input.append('inputfile %s.m81' %self.file_name)
    input.append('export %s.ins' %self.file_name)
    input.append('composition %s' %olx.xf.GetFormula('unit'))
    input.append('maxima all')
    input.append('plimit 1.5 sigma')
    input.append('chlimit 0.25')
    input.append('scale fractional')
    input.append('centerofcharge yes')
    input.append('fullcell no')
    input.append('numberofatoms guess')
    input.append('dataformat shelx')
    input.append('fbegin %s' %olx.file.GetName(olx.HKLSrc()))
    input.append('endf')
    self.input_file_name = os.path.normpath("%s.sfi" %(self.file_name))
    try:
      input_file = file(self.input_file_name, 'w+')
      input_file.write('\n'.join(input))
      input_file.close()
      self.to_cleanup.append(self.input_file_name)
      self.to_cleanup.append("%s.m81" %self.file_name)
      self.to_cleanup.append("%s.sflog" %self.file_name)
      self.to_cleanup.append(".coo")
    except:
      raise
    return ""

  def do_run(self, RunPrgObject):
    self.create_input()
    if olx.Exec("superflip", self.input_file_name):
      olx.WaitFor("process")
      if olx.Exec("edma", self.input_file_name):
        olx.WaitFor("process")
        ZERR = 'ZERR %s %s' %(olx.xf.au.GetZ(),
                            olx.xf.au.GetCell('esd').replace(',', ' '))
        if OV.HasGUI():
          freeze_status = olx.Freeze()
          olx.Freeze(True)
        try:
          olx.Atreap("%s.ins" %self.file_name)
          if self.derive_symmetry:
            log_file_name = "%s.sflog" %self.file_name
            if os.path.exists(log_file_name):
              log_file = file(log_file_name, "r")
              for l in log_file:
                if "Hall symbol:" in l:
                  l = l.strip()
                  hall_symbol = l.split(':')[1]
                  olx.ChangeSG("%s" %hall_symbol)
                  break
              log_file.close()
              if OV.HasGUI():
                olex.m("spy.run_skin sNumTitle")
            else:
              print("Could not locate the SF log file, aborting symmetry processing")
          olx.Compaq(a=True)
          olx.AddIns("%s" %ZERR)
          olx.File("%s.res" %self.file_name)
        finally:
          if OV.HasGUI():
            olx.Freeze(freeze_status)

  def post_solution(self, RunPrgObject):
    if olx.GetVar('settings.superflip.cleanup') == 'true':
      for f in self.to_cleanup:
        if os.path.exists(f):
          try:
            os.remove(f)
          except:
            print("Failed to remove: %s" %f)

class Method_SIR(Method_solution):

  def do_run(self, RunPrgObject):
    from olexsir import Sir

    print 'STARTING %s %s with %s' %(
      RunPrgObject.program.name,
      RunPrgObject.program.program_type, self.name)
    RunPrgObject.solve = True
    sirversion = RunPrgObject.program.versions
    sirfile = "%s.sir"%(OV.FileName())
    filename = OV.FileName()
    Z = float(olx.xf.au.GetZ())
    cell = ''.join(olx.xf.au.GetCell().split(','))
    hklfile = OV.HKLSrc().split(os.sep)[-1]
    contents = ''
    for item in olx.xf.GetFormula('list').split(","):
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

    oxs.setDirectives(cell=cell, SPACEGROUP=olx.xf.au.GetCellSymm(),
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
      if RunPrgObject.program.name in 'SIR2002' or RunPrgObject.program.name in 'SIR97':
        oxs.setDirectives(Tangent=None)
      else:
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
        resfile = r"%s/%s.res" %(olx.FilePath(), OV.FileName())
        if os.path.exists(resfile):
          os.remove(resfile)
        oxs.Exec(sirfile, sirversion)
        OV.DeleteBitmap('solve')
        if not os.path.exists(resfile):
          self.sort_out_sir2011_res_file()
#        olx.Atreap(resfile) #No need to reap, it will be reaped anyway!
    else:
        print 'No *.sir File!'

  def sort_out_sir2011_res_file(self):
    import glob
    import shutil
    g = glob.glob(r"%s/*.%s" %(OV.FilePath(), "res"))
    for item in g:
      f = item.split(".res")[0]
      f = "%s.res" %f[:-3]
      shutil.copyfile(item, f)
      os.remove(item)

def defineExternalPrograms():
  # define solution methods
  direct_methods = Method_shelx_direct_methods(direct_methods_phil)
  patterson = Method_shelx_solution(patterson_phil)
  texp = Method_shelx_solution(texp_phil)
  dual_space = Method_shelxd(dual_space_phil)
  charge_flipping = Method_cctbx_ChargeFlip(charge_flipping_phil)
  sir97_dm = Method_SIR(sir_dm_phil)
  sir97_patt = Method_SIR(sir_patt_phil)
  sir2002_dm = Method_SIR(sir_dm_phil)
  sir2002_patt = Method_SIR(sir_patt_phil)
  sir2004_dm = Method_SIR(sir_dm_phil)
  sir2004_patt = Method_SIR(sir_patt_phil)
  sir2008_dm = Method_SIR(sir_dm_phil)
  sir2008_patt = Method_SIR(sir_patt_phil)
  sir2011_dm = Method_SIR(sir_dm_phil)
  sir2011_patt = Method_SIR(sir_patt_phil)
  superflip_cf = Method_Superflip(superflip_cf_phil)

  # define refinement methods
  least_squares = Method_shelx_refinement(get_LS_phil())
  cgls = Method_shelx_refinement(get_CGLS_phil())
  gauss_newton = Method_cctbx_refinement(gauss_newton_phil)
  levenberg_marquardt = Method_cctbx_refinement(levenberg_marquardt_phil)

  # define solution programs


  ShelXS = Program(
    name='ShelXS',
    program_type='solution',
    author="G.M.Sheldrick",
    reference="Sheldrick, G.M. (2008). Acta Cryst. A64, 112-122.",
    brief_reference="Sheldrick, 2008",
    execs=["shelxs.exe", "shelxs"],
    phil_entry_name="ShelXS")
  ShelXS97 = Program(
    name='ShelXS-1997',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxs97.exe", "shelxs97"])
  ShelXS86 = Program(
    name='ShelXS-1986',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxs86.exe", "shelxs86"])
  XS = Program(
    name='XS',
    program_type='solution',
    author="G.M.Sheldrick/Bruker",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xs.exe", "xs"],
    phil_entry_name="XS")
  XT = Program(
    name='XT',
    program_type='solution',
    author="G.M.Sheldrick/Bruker",
    reference="Sheldrick, G.M. (2015). Acta Cryst. A71, 3-8.",
    brief_reference="Sheldrick, 2015",
    execs=["xt.exe", "xt"],
    phil_entry_name="XT")
  ShelXT = Program(
    name='ShelXT',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=XT.reference,
    brief_reference=XT.brief_reference,
    execs=["shelxt.exe", "shelxt"],
    phil_entry_name="ShelXT")
  ShelXD = Program(
    name='ShelXD',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxd.exe", "shelxd"],
    phil_entry_name="ShelXD")
  ShelXD97 = Program(
    name='ShelXD-1997',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxd97.exe", "shelxd97"])
  XM = Program(
    name='XM',
    program_type='solution',
    author="G.M.Sheldrick/Bruker",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xm.exe", "xm"],
    phil_entry_name="XM")
  smtbx_solve = Program(
    name='olex2.solve',
    program_type='solution',
    author="Luc Bourhis et al",
    reference="""Bourhis, L.J., Dolomanov, O.V., Gildea, R.J., Howard, J.A.K., Puschmann, H.
 (2015). Acta Cryst. A71, 59-75.""",
    brief_reference="Bourhis et al., 2015",
    )

  SIR97 = Program(
    name='SIR97',
    program_type='solution',
    author="Maria C. Burla, Rocco Caliandro, Mercedes Camalli, Benedetta Carrozzini,"+
        "Giovanni Luca Cascarano, Liberato De Caro, Carmelo Giacovazzo, Giampiero Polidori,"+
        "Dritan Siliqi, Riccardo Spagna",
    reference="""Burla, M.C., Caliandro, R., Camalli, M., Carrozzini, B., Cascarano, G.L.,
 De Caro, L., Giacovazzo, C., Polidori, G., Siliqi, D., Spagna, R.
 (2007). J. Appl. Cryst. 40, 609-613.""",
    brief_reference="Burla et al.,  2007",
    versions = '97',
    execs=["sir97.exe", "sir97"])
  SIR2002 = Program(
    name='SIR2002',
    program_type='solution',
    author=SIR97.author,
    reference=SIR97.reference,
    brief_reference=SIR97.brief_reference,
    versions = '2002',
    execs=["sir2002.exe", "sir2002"])
  SIR2004 = Program(
    name='SIR2004',
    program_type='solution',
    author=SIR97.author,
    reference=SIR97.reference,
    brief_reference=SIR97.brief_reference,
    versions = '2004',
    execs=["sir2004.exe", "sir2004"])
  SIR2008 = Program(
    name='SIR2008',
    program_type='solution',
    author=SIR97.author,
    reference=SIR97.reference,
    brief_reference=SIR97.brief_reference,
    versions = '2008',
    execs=["sir2008.exe", "sir2008"])
  SIR2011 = Program(
    name='SIR2011',
    program_type='solution',
    author=SIR97.author,
    reference=SIR97.reference,
    brief_reference=SIR97.brief_reference,
    versions = '2011',
    execs=["sir2011.exe", "sir2011"])
  Superflip = Program(
    name='Superflip',
    program_type='solution',
    author="A van der Lee, C.Dumas & L. Palatinus",
    reference="""Palatinus, L. & Chapuis, G. (2007). J. Appl. Cryst., 40, 786-790;
Palatinus, L. & van der Lee, A. (2008). J. Appl. Cryst. 41, 975-984;
Palatinus, L., Prathapa, S. J. & van Smaalen, S. (2012). J. Appl. Cryst. 45,
 575-580.""",
    brief_reference="""Palatinus & Chapuis, 2007;Palatinus & van der Lee, 2008;
Palatinus et al., 2012""",
    versions='260711',
    execs=["superflip.exe", "superflip"])

  ShelXS.addMethod(direct_methods)
  ShelXS.addMethod(patterson)
  ShelXS.addMethod(texp)
  ShelXS97.addMethod(direct_methods)
  ShelXS97.addMethod(patterson)
  ShelXS97.addMethod(texp)
  ShelXS86.addMethod(direct_methods)
  ShelXS86.addMethod(patterson)
  ShelXS86.addMethod(texp)
  XS.addMethod(direct_methods)
  XS.addMethod(patterson)
  XS.addMethod(texp)
  XT.addMethod(direct_methods)
  ShelXT.addMethod(direct_methods)
  ShelXD.addMethod(dual_space)
  ShelXD97.addMethod(dual_space)
  XM.addMethod(dual_space)
  smtbx_solve.addMethod(charge_flipping)
  SIR97.addMethod(sir97_dm)
  SIR97.addMethod(sir97_patt)
  SIR2002.addMethod(sir2002_dm)
  SIR2002.addMethod(sir2002_patt)
  SIR2004.addMethod(sir2004_dm)
  SIR2004.addMethod(sir2004_patt)
  SIR2008.addMethod(sir2008_dm)
  SIR2008.addMethod(sir2008_patt)
  SIR2011.addMethod(sir2011_dm)
  SIR2011.addMethod(sir2011_patt)
  Superflip.addMethod(superflip_cf)

  # define refinement programs
  ShelXL = Program(
    name='ShelXL',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxl.exe", "shelxl"],
    phil_entry_name="ShelXL")
  ShelXL97 = Program(
    name='ShelXL-1997',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxl97.exe", "shelxl97"],
    phil_entry_name="ShelXL97")
  XL = Program(
    name='XL',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xl.exe", "xl"],
    phil_entry_name="ShelXL97")
  XLMP = Program(
    name='XLMP',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xlmp.exe", "xlmp"],
    phil_entry_name="XLMP")
  ShelXH97 = Program(
    name='ShelXH-1997',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxh.exe", "shelxh"],
    phil_entry_name="ShelXL97")
  XH = Program(
    name='XH',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xh.exe", "xh"],
    phil_entry_name="ShelXL97")
  ShelXL_ifc = Program(
    name='ShelXL_ifc',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxl_ifc"],
    phil_entry_name="ShelXL97")
  smtbx_refine = Program(
    name='olex2.refine',
    program_type='refinement',
    author="L.J. Bourhis, O.V. Dolomanov, R.J. Gildea",
    reference=smtbx_solve.reference,
    brief_reference=smtbx_solve.brief_reference,
  )

  RPD = ExternalProgramDictionary()
  for prg in (ShelXL, ShelXL97, XL, XLMP, ShelXH97, XH, ShelXL_ifc):
    prg.addMethod(least_squares)
    prg.addMethod(cgls)
    RPD.addProgram(prg)

  smtbx_refine.addMethod(gauss_newton)
  smtbx_refine.addMethod(levenberg_marquardt)
  RPD.addProgram(smtbx_refine)

  SPD = ExternalProgramDictionary()
  for prg in (ShelXS, ShelXS97, ShelXS86, XS, XT, ShelXT, ShelXD, ShelXD97, XM,
              smtbx_solve, SIR97, SIR2002, SIR2004, SIR2008, SIR2011, Superflip):
    SPD.addProgram(prg)


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
atom_sites_solution=direct
  .type=str
instructions {
  Gui
  .optional=True
  {
    values {}
    default=False
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
atom_sites_solution=heavy
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
command_line
  .optional=False
  .caption='Command line'
{
  values {
    Options=''
      .type=str
  }
  default=True
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

#TEXP na [#] nH [0] Ek [1.5]
texp_phil = phil_interface.parse("""
name = 'Structure Expansion'
  .type=str
atom_sites_solution=heavy
  .type=str
instructions {
  texp {
    values {
      na=1
        .type=int
      nH=1
        .type=int
      Ek=1.5
        .type=float
    }
    default=True
      .type=bool
  }
  tref
  .optional=True
  {
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
    default=False
      .type=bool
  }
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
  command_line
    .optional=False
    .caption='Command line'
  {
    values {
      Options=''
        .type=str
    }
    default=True
      .type=bool
  }
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
  command_line
    .optional=False
    .caption='Command line'
  {
    values {
      Options=''
        .type=str
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


superflip_cf_phil = phil_interface.parse("""
name = 'Charge Flipping'
  .type=str
atom_sites_solution=iterative
  .type=str
  instructions {

  execution
    .optional=False
  {
    values {
      repeatmode= *never nosuccess always trials
        .type=choice
      trials = 1
        .type=int
      maxcycl=10000
        .type=int
      fastfft=False
        .type=bool
      cleanup=True
        .type=bool
    }
    default=True
      .type=bool
  }
  data
    .optional=False
  {
    values {
      normalize=*no wilson local
        .type=choice
      nresshells=100
        .type=int
      weakratio=0.2
        .type=float
    }
    default=True
      .type=bool
  }


  missing
    .optional=True
  {
    values {
      value=zero *float bound boundum
        .type=choice
      resolution_limit=0.4
        .type=float
      uper_bound=4
        .type=float
    }
    default=False
      .type=bool
  }

  resolution
    .optional=True
  {
    values {
      resunit=*d sthl
        .type=choice
      reslimit_high=100
        .type=int
      reslimit_low=0
        .type=int
    }
    default=False
      .type=bool
  }

  convergence
    .optional=False
  {
    values {
      mode=*threshhold normal rvalue charge peakiness
        .type=choice
      threshold=0.8
        .type=float
    }
    default=True
      .type=bool
  }

  delta
    .optional=False
  {
    values {
      value=*AUTO Number
        .type=choice
      Number=1.3
        .type=float
      of=static dynamic *sigma
        .type=choice
    }
    default=True
      .type=bool
  }

  output
    .optional=False
  {
    values {
      derivesymmetry=False
        .type=bool
      limit=25
        .type=float
      polish=True
        .type=bool
      cycles=5
        .type=int
    }
    default=False
      .type=bool
  }
  }

""")

charge_flipping_phil = phil_interface.parse("""
name = 'Charge Flipping'
  .type=str
atom_sites_solution=iterative
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
command_line
  .optional=False
  .caption='Command line'
{
  values {
    Options=''
      .type=str
  }
  default=True
    .type=bool
}
""")

def get_LS_phil():
  return phil_interface.parse("""
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

def get_CGLS_phil():
  return phil_interface.parse("""
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


def writeRefinementInfoIntoRes(d):
  ''' Expects a ditionary containing the relevant items with cif identifiers as keyes '''
  d.setdefault('_refine_ls_abs_structure_Flack', "n/a")
  txt = '''
REM The information below was added by Olex2.
REM
REM R1 = %(_refine_ls_R_factor_gt)s for %(_reflns_number_gt)s Fo > 4sig(Fo) and %(_refine_ls_R_factor_all)s for all %(_reflns_number_total)s data
REM %(_refine_ls_number_parameters)s parameters refined using %(_refine_ls_number_restraints)s restraints
REM Highest difference peak %(_refine_diff_density_max)s, deepest hole %(_refine_diff_density_min)s
REM Mean Shift %(_refine_ls_shift/su_mean)s, Max Shift %(_refine_ls_shift/su_max)s.

REM +++ Tabular Listing of Refinement Information +++
REM R1_all = %(_refine_ls_R_factor_all)s
REM R1_gt = %(_refine_ls_R_factor_gt)s
REM wR_ref = %(_refine_ls_wR_factor_ref)s
REM GOOF = %(_refine_ls_goodness_of_fit_ref)s
REM Shift_max = %(_refine_ls_shift/su_max)s
REM Shift_mean = %(_refine_ls_shift/su_mean)s
REM Reflections_all = %(_reflns_number_total)s
REM Reflections_gt = %(_reflns_number_gt)s
REM Parameters = %(_refine_ls_number_parameters)s
REM Hole = %(_refine_diff_density_min)s
REM Peak = %(_refine_diff_density_max)s
REM Flack = %(_refine_ls_abs_structure_Flack)s

''' %d

  wFile = open('%s/%s.res' %(OV.FilePath(), OV.FileName()), 'a')
  wFile.write(txt)
  wFile.close()

def get_program_dictionaries(cRPD=None, cSPD=None):
  global SPD
  global RPD

  if not cRPD or not cSPD:
    if RPD and SPD:
      return SPD, RPD
    else:
      SPD, RPD =  defineExternalPrograms()
  return SPD, RPD

def get_managed_reference_set():
  global managed_references
  if managed_references: return managed_references
  sd, rd = get_program_dictionaries()
  rl = []
  for p in sd: rl.append(p.reference)
  for p in rd: rl.append(p.reference)
  managed_references = set([''.join(x.replace('\r', '').split()) for x in rl])
  return managed_references

def get_known(kind):
  sd, rd = get_program_dictionaries()
  if kind == 'solution':
    src = sd
  else:
    src = rd
  rv = []
  for p in src:
    rv.append(p.name)
  return ';'.join(rv)

olex.registerFunction(get_known, False, "programs")

if __name__ == '__main__':
  SPD, RPD = defineExternalPrograms()
