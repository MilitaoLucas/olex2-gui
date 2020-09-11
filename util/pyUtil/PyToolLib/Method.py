import phil_interface
import olx
from olexFunctions import OlexFunctions
OV = OlexFunctions()


definedControls = []

class Method(object):
  command_line_options = None
  failure = False
  running = False

  def __init__(self, phil_object):
    self.phil_index = phil_interface.phil_handler(phil_object)
    params = self.phil_index.params
    self.name = params.name
    try:
      self.display = params.display
    except:
      self.display = params.name
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
    debug = bool(OV.GetParam('olex2.debug',False))
    timer = debug
    import time
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
      if timer:
        t1 = time.time()
      self.do_run(RunPrgObject)
      if timer:
        print("-- self.do_run(RunPrgObject): %.3f" %(time.time() - t1))
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

    formula = self.getFormulaAsDict(RunPrgObject.formula)
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
        print("Formula is invalid")
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

  def getFormulaAsDict(self, formula):
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
      except Exception:
        sys.stderr.write("An error occurred in the function getFormulaAsDict."+\
          "\nFormula: %s, item: %s\n" %(formula, item))
        sys.stderr.formatExceptionInfo()
    return d

class Method_refinement(Method):

  def getFlack(self):
    return None

  def addInstructions(self):
    """Adds instructions to the .ins file so that the file reflects what is selected in the GUI.
    """
    for arg in self.getArgs():
      argName = arg.split()[0]
      if olx.Ins(argName) != "n/a":
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
      print("Please provide some atoms to refine")
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
    if RunPrgObject.params.user.auto_insert_user_ins:
      for i in RunPrgObject.params.user.auto_insert_user_ins.split(','):
        i = i.strip().upper()
        if i.startswith('MORE'):
          if olx.Ins('MORE') == "n/a":
            OV.AddIns(i)
        elif i.startswith('BOND'):
          bond = olx.Ins('BOND')
          if bond == "n/a" or not bond:
            if (int(olx.xf.au.GetAtomCount('H')) > 0):
              OV.AddIns("BOND $H", quiet=True)
        elif i.startswith('ACTA'):
          if olx.Ins('ACTA') == "n/a":
            if olx.GetVar('refinement_acta', None) != "No ACTA":
              OV.AddIns("ACTA")
        elif i.startswith("CONF"):
          if olx.Ins("CONF") == "n/a":
            OV.AddIns('CONF')
        else:
          olx.AddIns(i, q=True)

    if RunPrgObject.make_unique_names:
      pass
      #olx.Sel('-a')
      #olx.Name('sel 1 -c')
    if OV.GetParam('snum.auto_hydrogen_naming'):
      olx.FixHL()
    wave_length = float(olx.xf.exptl.Radiation())
    if round(wave_length, 2) == round(0.71073,2) or\
       round(wave_length, 2) == round(1.5414, 2):
      pass
    else:
      olx.GenDisp(source='auto')

  def post_refinement(self, RunPrgObject):
    pass

  def writeRefinementInfoIntoRes(self, d, file_name=None):
    ''' Expects a dictionary containing the relevant items with cif identifiers as keys '''
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
    if not file_name:
      file_name = '%s/%s.res' %(OV.FilePath(), OV.FileName())
    file_lock = OV.createFileLock(file_name)
    try:
      with open(file_name, 'a') as wFile:
        wFile.write(txt)
    finally:
      OV.deleteFileLock(file_lock)
