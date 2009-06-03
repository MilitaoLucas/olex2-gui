# ExternalPrgParameters.py
# -*- coding: latin-1 -*-

import sys
import olx
import olex
import olex_core
from olexFunctions import OlexFunctions
OV = OlexFunctions()

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
  def __init__(self, name, author, reference, execs=None, versions=None):
    self.name = name
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
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    self.name = name
    self.cmd = cmd
    self.args = args
    self.help = '%s-help' %(self.name.lower().replace(' ', '-'))
    self.info = '%s-info' %(self.name.lower().replace(' ', '-'))
    self.atom_sites_solution = atom_sites_solution
    
  def html_gui(self):
    pass
  
  def run(self, RunPrgObject):
    """Must be redefined in subclass.
    
    It is from within this method that the external program will be run.
    """
    assert 0, 'run must be defined!'
    
  def calculate_defaults(self):
    """Defines controls in Olex2 for each argument in self.args
    """
    for arg in self.args:
      default = arg['default']
      
      global definedControls
      ctrl_name = 'SET_SETTINGS_%s' %arg['name'].upper()
      if ctrl_name not in definedControls:
        OV.SetVar('settings_%s' %arg['name'], default) # Define checkbox
        definedControls.append(ctrl_name)
        for value in arg['values']:
          OV.SetVar('settings_%s_%s' %(arg['name'], value[0]), value[1]) # Define text box for each value
      
  def getValuesFromFile(self):
    """Gets the value of all arguments in self.args that are present in the
    .ins file and sets the value of the GUI input boxes to reflect this.
    """
    for arg in self.args:
      ins = olx.Ins(arg['name'])
      if ins != 'n/a':
        OV.SetVar('settings_%s' %arg['name'], 'true')
        ins = ins.split()
        count = 0
        for value in arg['values']:
          try:
            val = ins[count]
            OV.SetVar('settings_%s_%s' %(arg['name'], value[0]), val)
            if value[0] == 'nls':
              OV.SetVar('snum_refinement_max_cycles', val)
            elif value[0] == 'npeaks':
              OV.SetVar('snum_refinement_max_peaks', val)
          except IndexError:
            break
          count += 1
      else:
        if arg['default'] != 'true':
          OV.SetVar('settings_%s' %arg['name'], 'false')
        if arg['name'] in ('L.S.', 'CGLS'):
          val = OV.FindValue('snum_refinement_max_cycles')
          OV.SetVar('settings_%s_nls' %arg['name'], val)
        elif arg['name'] == 'PLAN':
          val = OV.FindValue('snum_refinement_max_peaks')
          OV.SetVar('settings_%s_npeaks' %arg['name'], val)
          
  def extraHtml(self):
    """This can be redefined in a subclass to define extra HTML that is to be
    added to the program settings panel.
    """
    return ''
  
  
class Method_solution(Method):
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    Method.__init__(self, name, cmd, args, atom_sites_solution)
  
  def pre_solution(self, RunPrgObject):
    """Prepares the arguments required to reset the structure before running the
    structure solution program.
    """
    args = self.getArgs()
    if not args:
      args = self.cmd
    if not RunPrgObject.formula or RunPrgObject.formula == "None":
      RunPrgObject.formula = RunPrgObject.snum_refinement_original_formula
      
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
  
  
  
  def getArgs(self):
    """Gets the value of all the arguments in self.args from Olex2.
    """
    args = ''
    for arg in self.args:
      if OV.FindValue('settings_%s' %arg['name']) == 'true': # Check if the argument is selected in the GUI
        args += arg['name']
        for item in arg['values']:
          name = item[0]
          try:
            value = float(OV.FindValue('settings_%s_%s' %(arg['name'], name)))
            args += ' %s' %value
          except ValueError:
            break
        args += '\n'
    return args
  
  def post_solution(self, RunPrgObject):
    """Things to be done after running the solution program.
    """
    if RunPrgObject.HasGUI:
      olx.ShowQ('a true')
      olx.ShowQ('b true')
      olx.Compaq('-a')
      olx.ShowStr("true")
    self.auto = True
    
  
class Method_refinement(Method):
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    Method.__init__(self, name, cmd, args, atom_sites_solution)
    
  def addInstructions(self):
    """Adds instructions to the .ins file so that the file reflects what is selected in the GUI.
    """
    for arg in self.args:
      if OV.FindValue('settings_%s' %arg['name']) == 'true': # Check if the argument is selected in the GUI
        args = arg['name']
        for item in arg['values']:
          name = item[0]
          try:
            value = float(OV.FindValue('settings_%s_%s' %(arg['name'], name)))
            args += ' %s' %value
          except ValueError:
            break
        olx.DelIns(arg['name'])  # uncomment me!
        #olx.AddIns(args)
        OV.AddIns(args)
  
  def pre_refinement(self, RunPrgObject):
    for i in xrange(int(olx.xf_au_GetAtomCount())):
      ret = olx.xf_au_IsPeak(i)
      if ret == "false":
        RunPrgObject.isAllQ = False
        break
      else:
        RunPrgObject.isAllQ = True
    if RunPrgObject.isAllQ:
      olx.Name('$Q C')
      RunPrgObject.make_unique_names = True
      #OV.File()
      return
    
    if RunPrgObject.snum_refinement_auto_tidy:
      RunPrgObject.doAutoTidyBefore()
    if RunPrgObject.snum_refinement_update_weight:
      olx.UpdateWght()
    if RunPrgObject.make_unique_names:
      olx.Sel('-a')
      olx.Name('sel 1 -c')
    if OV.FindValue('snum_auto_hydrogen_naming') == 'checked': # uncomment me!
      olx.FixHL() # uncomment me!
      
    #OV.File()

  
class Method_shelx(Method):
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    Method.__init__(self, name, cmd, args, atom_sites_solution)
  
  def run(self, RunPrgObject):
    """Runs any SHELX refinement/solution program
    """
    print 'STARTING SHELX refinement/solution with %s' %self.name
    prgName = olx.file_GetName(RunPrgObject.shelx)
    #olex.m("User '%s'" %RunPrgObject.tempPath)
    olx.User("'%s'" %RunPrgObject.tempPath)
    xl_ins_filename = RunPrgObject.hkl_src_name
    command = "%s '%s'" % (prgName, xl_ins_filename.lower()) #This is correct!!!!!!
    #sys.stdout.graph = RunPrgObject.Graph()
    if not OV.FindValue('snum_shelx_output'):
      command = "-q " + command
    olx.Exec(command)
    olx.WaitFor('process') # uncomment me!
    #olex.m("User '%s'" %RunPrgObject.filePath)
    olx.User("'%s'" %RunPrgObject.filePath)
    
 

class Method_shelx_solution(Method_shelx, Method_solution):
  """Inherits methods specific to shelx solution programs
  """
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    Method_shelx.__init__(self, name, cmd, args, atom_sites_solution)
  
  
class Method_shelx_refinement(Method_shelx, Method_refinement):
  """Inherits methods specific to shelx refinement programs
  """
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    Method_shelx.__init__(self, name, cmd, args, atom_sites_solution)
  
  def pre_refinement(self, RunPrgObject):
    _diffrn_ambient_temperature = OV.FindValue('snum_metacif_diffrn_ambient_temperature')
    if '(' in _diffrn_ambient_temperature:
      _diffrn_ambient_temperature = _diffrn_ambient_temperature.split('(')[0]
    if 'K' in _diffrn_ambient_temperature:
      _diffrn_ambient_temperature = _diffrn_ambient_temperature.split('K')[0]
    try:
      _diffrn_ambient_temperature = float(_diffrn_ambient_temperature)
      _diffrn_ambient_temperature = _diffrn_ambient_temperature - 273.15
      OV.DelIns('TEMP')
      OV.AddIns('TEMP %s' %_diffrn_ambient_temperature)
    except:
      pass
    Method_refinement.pre_refinement(self, RunPrgObject)


class Method_shelx_direct_methods(Method_shelx_solution):
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    Method_shelx_solution.__init__(self, name, cmd, args, atom_sites_solution)
    
  def post_solution(self, RunPrgObject):
    Method_shelx_solution.post_solution(self, RunPrgObject)
    self.get_XS_TREF_solution_indicators(RunPrgObject)
    
  def get_XS_TREF_solution_indicators(self, RunPrgObject):
    """Gets the TREF solution indicators from the .lst file and prints values in Olex2.
    """
    import lst_reader
    lstPath = "%s/%s.lst" %(OV.FilePath(), OV.FileName())
    lstValues = lst_reader.reader(open(lstPath)).values()
    
    RunPrgObject.Ralpha = lstValues.get('Ralpha','')
    RunPrgObject.Nqual = lstValues.get('Nqual','')
    RunPrgObject.CFOM = lstValues.get('CFOM','')
    
    print RunPrgObject.Ralpha, RunPrgObject.Nqual, RunPrgObject.CFOM
  
  
class Method_shelxd(Method_shelx_solution):
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    Method_shelx_solution.__init__(self, name, cmd, args, atom_sites_solution)
    
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
      OV.SetVar('settings_plop_1', nmin)
      OV.SetVar('settings_plop_2', nmid)
      OV.SetVar('settings_plop_3', nmax)
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
      'onclick':'spy.stopShelxd()',
    }
    button_html = htmlTools.make_input_button(button_d)
    html = '''
  </tr>
  <tr>
  <td>
    %s
  </td>
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
    global stop_path
    stop_path = '%s/temp/%s.fin' %(olx.StrDir(), OV.FileName())
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
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    Method_refinement.__init__(self, name, cmd, args, atom_sites_solution)
    
  def run(self, RunPrgObject):
    from cctbx_olex_adapter import OlexCctbxRefine
    print 'STARTING cctbx refinement'
    verbose = OV.FindValue('olex2_verbose',False)
    cctbx = OlexCctbxRefine(
      max_cycles=RunPrgObject.snum_refinement_max_cycles,
      verbose=verbose)
    cctbx.run()
    OV.DeleteBitmap('refine')

class Method_cctbx_ChargeFlip(Method_solution):
  def __init__(self, name, cmd, args, atom_sites_solution=None):
    Method_solution.__init__(self, name, cmd, args, atom_sites_solution)
    
  def run(self, RunPrgObject):
    from cctbx_olex_adapter import OlexCctbxSolve
    print 'STARTING cctbx Charge Flip'
    RunPrgObject.solve = True
    cctbx = OlexCctbxSolve()

    solving_interval = int(float(self.getArgs().split()[1]))

    formula_l = olx.xf_GetFormula('list')
    formula_l = formula_l.split(",")
    formula_d = {}
    for item in formula_l:
      item = item.split(":")
      formula_d.setdefault(item[0], {'count':float(item[1])})
    try:
      for xyz, height in cctbx.runChargeFlippingSolution('%s/%s.hkl' %(RunPrgObject.tempPath,RunPrgObject.hkl_src_name.lower()), solving_interval=solving_interval):
        cctbx.post_single_peak(xyz, height, auto_assign=False)
    except Exception, err:
      print err
      #cctbx.post_single_peak(xyz, height)
    olx.xf_EndUpdate()
    olx.Compaq('-a')
    olex.m("sel -a")
    olex.m("fix occu sel")
    #olx.VSS(True)
    #olex.m("sel -a")
    #olex.m("name sel 1")
    OV.DeleteBitmap('solve')
    file = r"'%s/%s.res'" %(olx.FilePath(), RunPrgObject.fileName)
    olx.xf_SaveSolution(file)
    olx.Atreap(file)
    
def defineExternalPrograms():
  # define solution methods
  direct_methods = Method_shelx_direct_methods(
    name='Direct Methods',
    cmd='TREF',
    args=(
      dict(name='TREF', 
           values=[['np', 100], ['nE', ''], ['kapscal', ''], ['ntan', ''], ['wn', '']],
           default='true',
           ),
      dict(name='INIT',
           values=[['nn', ''], ['nf', ''], ['s+', 0.8], ['s-', 0.2], ['wr', 0.2]],
           default='false',
           ),
      dict(name='PHAN',
           values=[['steps', 10], ['cool', 0.9], ['Boltz', ''], ['ns', ''], ['mtpr', 40], ['mngr', 10]],
           default='false',
           ),
      dict(name='ESEL',
           values=[['Emin', 1.2], ['Emax', 5], ['dU', .005], ['renorm', .7], ['axis', 0]],
           default='false',
           ),
      dict(name='EGEN',
           values=[['d_min', ''], ['d_max', '']],
           default='false',
           ),
      dict(name='GRID',
           values=[['sl',''], ['sa', ''], ['sd', ''], ['dl', ''], ['da', ''], ['dd', '']],
           default='false',
           ),
      #dict(name='PLAN',
           #values=[['npeaks', ''], ['d1', 0.5], ['d2', 1.5]],
           #default='false',
           #),
      ),
    atom_sites_solution='direct',
  )
  patterson = Method_shelx_solution(
    name='Patterson Method',
    cmd='PATT',
    args=(
      dict(name='PATT',
           values=[['nv', ''], ['dmin', ''], ['resl', ''], ['Nsup', ''], ['Zmin', ''], ['maxat', '']],
           default='true',
           ),
      dict(name='VECT',
           values=[['X', ''], ['Y', ''], ['Z', '']],
           default='false',
           ),
      dict(name='ESEL',
           values=[['Emin', 1.2], ['Emax', 5], ['dU', .005], ['renorm', .7], ['axis', 0]],
           default='false',
           ),
      dict(name='EGEN',
           values=[['d_min', ''], ['d_max', '']],
           default='false',
           ),
      dict(name='GRID',
           values=[['sl',''], ['sa', ''], ['sd', ''], ['dl', ''], ['da', ''], ['dd', '']],
           default='false',
           ),
      #dict(name='PLAN',
           #values=[['npeaks', ''], ['d1', 0.5], ['d2', 1.5]],
           #default='false',
           #),
      ),
    atom_sites_solution='heavy'
  )
  dual_space = Method_shelxd(
    name='Dual Space',
    cmd='',
    args = (
      dict(name='NTRY',
           values=[['ntry', 100]],
           default='true',
           ),
      dict(name='FIND',
           values=[['na', 0], ['ncy', '']],
           default='true',
           ),
      dict(name='MIND',
           values=[['mdis', 1.0], ['mdeq', 2.2]],
           default='true',
           ),
      dict(name='PLOP',
           values=[['1', ''], ['2', ''], ['3', ''], ['4', ''], ['5', ''], ['6', ''], ['7', ''], ['8', ''], ['9', ''], ['10', '']],
           default='true',
           ),
    ),
    #{'name':'SHEL', 'values':['dmax:', 'dmin:0']},
    #{'name':'PATS', 'values':['+np or -dis:100', 'npt:', 'nf:5']},
    #{'name':'GROP', 'values':['nor:99', 'E<sub>g</sub>:1.5', 'd<sub>g</sub>:1.2', 'ntr:99']},
    #{'name':'PSMF', 'values':['pres:3.0', 'psfac:0.34']},
    #{'name':'FRES', 'values':['res:3.0',]},
    #{'name':'ESEL', 'values':['Emin:', 'dlim:1.0']},
    
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
    atom_sites_solution='dual'
  )
  charge_flipping = Method_cctbx_ChargeFlip(
    name='Charge Flipping', 
    cmd='FLIP',
    args=(
      dict(name='FLIP',
           values=[['interval', 60]],
           default='true',
           ),
   ),
    atom_sites_solution='other'
  )
  
  # define refinement methods
  least_squares = Method_shelx_refinement(
    name='Least Squares', 
    cmd='L.S.', 
    args=(
      {'name':'L.S.',
       'values':[['nls', 4], ['nrf', ''], ['nextra', ''], ['maxvec', 511]],
       'default':'true',
       },
      {'name':'PLAN',
       'values':[['npeaks', 20], ['d1', ''], ['d2', '']],
       'default':'true',
       },
      {'name':'FMAP',
       'values':[['code', 2], ['axis', ''], ['n1', 53]],
       'default':'true',
       },
      {'name':'ACTA',
       'values':[['2thetafull', '']],
       'default':'false',
       },
   ),
  )

  cgls = Method_shelx_refinement(
    name='CGLS',
    cmd='CGLS',
    args=(
      {'name':'CGLS',
       'values':[['nls', 4], ['nrf', ''], ['nextra', ''], ['maxvec', 511]],
       'default':'true',
       },
      {'name':'PLAN',
       'values':[['npeaks', 20], ['d1', ''], ['d2', '']],
       'default':'true',
       },
      {'name':'FMAP',
       'values':[['code', 2], ['axis', ''], ['n1', 53]],
       'default':'true',
       },
   ),
  )

  lbgfs = Method_cctbx_refinement(
    name='LBFGS', 
    cmd='LBFGS', 
    #args = (
      #{'arg':'maxTry', 'value':20, 'name':'Maximum Refinement Iterations', 'varName': 'snum_refinement_max_cycles', 'help':'cycles-help'},
      #{'arg':'maxPeaks', 'value':20, 'name':'Number of Residual Peaks', 'varName': 'snum_refinement_max_peaks', 'help':'plan-help'},
    #)
    args = {}
  )

  
  # define solution programs
  ShelXS = Program(
    name='ShelXS',
    author="G.M.Sheldrick",
    reference="SHELXS-97 (Sheldrick, 1990)", 
    execs=["shelxs.exe", "shelxs"]
  )
  
  XS = Program(
    name='XS',
    author="G.M.Sheldrick/Bruker", 
    reference="SHELXS-97 (Sheldrick, 1990)/Bruker",
    execs=["xs.exe", "xs"]
  )
  
  ShelXD = Program(
    name='ShelXD', 
    author="G.M.Sheldrick", 
    reference="University of G&#246;ttingen", 
    execs=["shelxd.exe", "shelxd"]
  )
  
  XM = Program(
    name='XM', 
    author="G.M.Sheldrick/Bruker", 
    reference="University of G&#246;ttingen/Bruker", 
    execs=["xm.exe", "xm"]
  )
  
  smtbx_solve = Program(
    name='smtbx-solve', 
    author="Luc Bourhis, Ralf Grosse-Kunstleve", 
    reference="smtbx-flip (Bourhis, 2008)",
    execs=None
  )
  
  ShelXS.addMethod(direct_methods)
  ShelXS.addMethod(patterson)
  XS.addMethod(direct_methods)
  XS.addMethod(patterson)
  ShelXD.addMethod(dual_space)
  XM.addMethod(dual_space)
  smtbx_solve.addMethod(charge_flipping)
  
  # define refinement programs
  ShelXL = Program('ShelXL', "G.M.Sheldrick", "University of G&#246;ttingen", ["shelxl.exe", "shelxl"])
  XL = Program('XL', "G.M.Sheldrick", "University of G&#246;ttingen/Bruker", ["xl.exe", "xl"])
  XLMP = Program('XLMP', "G.M.Sheldrick", "University of G&#246;ttingen/Bruker", ["xlmp.exe", "xlmp"])
  ShelXH = Program('ShelXH', "G.M.Sheldrick", "University of G&#246;ttingen", ["shelxh.exe", "shelxh"])
  XH = Program('XH', "G.M.Sheldrick", "University of G&#246;ttingen/Bruker", ["xh.exe", "xh"])
  ShelXL_ifc = Program('ShelXL_ifc', "G.M.Sheldrick", "University of G&#246;ttingen", ["shelxl_ifc"])
  smtbx_refine = Program('smtbx-refine', "L.J. Bourhis, R.W. Grosse-Kunstleve", "smtbx-refine (Bourhis, 2008)")
  
  for prg in (ShelXL, XL, XLMP, ShelXH, XH, ShelXL_ifc):
    for method in (least_squares, cgls):
      prg.addMethod(method)
  smtbx_refine.addMethod(lbgfs)
  
  SPD = ExternalProgramDictionary()
  for prg in (ShelXS, XS, ShelXD, XM, smtbx_solve):
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
  
if __name__ == '__main__':
  SPD, RPD = defineExternalPrograms()