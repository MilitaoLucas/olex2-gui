from Method import Method_refinement, Method_solution
import phil_interface
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import olx
import olex

class Method_cctbx_refinement(Method_refinement):
  flack = None
  version = "(default)"

  def __init__(self, phil_object):
    import os
    super(Method_cctbx_refinement, self).__init__(phil_object)
    _ = os.environ.get('OLEX2_CCTBX_DIR')
    if _ is not None:
      self.version = _
    self.original_method = None
    
  def pre_refinement(self, RunPrgObject):
    RunPrgObject.make_unique_names = True
    self.cycles = OV.GetParam('snum.refinement.max_cycles')

    if RunPrgObject.params.snum.refinement.method == "NSFF":
      OV.SetParam('snum.refinement.method', 'Gauss-Newton')
      self.original_method = "NSFF"

    Method_refinement.pre_refinement(self, RunPrgObject)
    
    
  def do_run(self, RunPrgObject):
    import time
    import os
    from refinement import FullMatrixRefine
    from smtbx.refinement.constraints import InvalidConstraint
    import gui

    timer = debug = bool(OV.GetParam('olex2.debug',False))
    self.failure = True
    print '\n+++ STARTING olex2.refine +++++ %s' %self.version

    gui.set_notification("Using <b>spherical</b> form factors")
    table_file_name = None
    if RunPrgObject.params.snum.refinement.method == "NSFF":
      #self.method = self.RPD.programs[self.program.name].methods['Levenberg-Marquardt']

      table_file_name = OV.GetParam('snum.refinement.cctbx.nsff.tsc.file')
      if not os.path.exists(table_file_name):
        table_file_name = None
      else:
        table_file_name = table_file_name.encode("utf-8")
        print("Warning: using tabulated atomic form factors")
        gui.set_notification("Using <font color='red'><b>tabulated</b></font> form factors from <b>%s</b>" %os.path.basename(table_file_name))
    verbose = OV.GetParam('olex2.verbose')
    cctbx = FullMatrixRefine(
      max_cycles=RunPrgObject.params.snum.refinement.max_cycles,
      max_peaks=RunPrgObject.params.snum.refinement.max_peaks,
      verbose=verbose,
      on_completion=self.writeRefinementInfoForGui)
    try:
      if timer:
        t1 = time.time()
      cctbx.run(table_file_name=table_file_name)
      if timer:
        print "-- do_run(): %.3f" %(time.time() - t1)
      if timer:
        t1 = time.time()
      self.flack = cctbx.flack
      if timer:
        print "-- cctbx.flack: %.3f" %(time.time() - t1)

    except InvalidConstraint, e:
      print e
    except NotImplementedError, e:
      print e
    else:
      self.failure = cctbx.failure
      if not self.failure:
        OV.SetVar('cctbx_R1',cctbx.r1[0])
        OV.SetVar('cctbx_wR2',cctbx.wR2_factor())
        OV.File('%s.res' %OV.FileName())
    finally:
      #print '+++ FINISHED olex2.refine ++++++++++++++++++++++++++++++++++++\n'
      OV.DeleteBitmap('refine')
      self.interrupted = cctbx.interrupted

  def getFlack(self):
    return self.flack

  def post_refinement(self, RunPrgObject):
    OV.SetParam('snum.refinement.max_cycles',self.cycles)
    self.writeRefinementInfoIntoRes(self.cif)
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
    if self.original_method == "NSFF":
      OV.SetParam('snum.refinement.method', 'NSFF')

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
    print '+++ STARTING olex2.solve ++++++++++++++++++++++++++++++++++++'
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

  def post_solution(self, RunPrgObject):
    if OV.GetParam('user.solution.run_auto_vss'):
      RunPrgObject.please_run_auto_vss = True

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


gauss_newton_phil = phil_interface.parse("""
name = 'Gauss-Newton'
  .type=str
""")


levenberg_marquardt_phil = phil_interface.parse("""
name = 'Levenberg-Marquardt'
  .type=str
""")

NSFF_phil = phil_interface.parse("""
name = 'NSFF'
  .type=str
""")
