from Method import Method_refinement, Method_solution
import phil_interface
from olexFunctions import OV
import olx
import olex
import os

class Method_cctbx_refinement(Method_refinement):
  flack = None
  version = "(default)"

  def __init__(self, phil_object):
    super(Method_cctbx_refinement, self).__init__(phil_object)
    _ = os.environ.get('OLEX2_CCTBX_DIR')
    if _ is not None:
      self.version = _

  def pre_refinement(self, RunPrgObject):
    RunPrgObject.make_unique_names = True
    self.cycles = OV.GetParam('snum.refinement.max_cycles')
    self.table_file_name = None
    use_aspherical = False
    hide_nsff = OV.GetParam('user.refinement.hide_nsff')
    if not hide_nsff:
      html = "Using <font color=$GetVar(gui.blue)><b>spherical </b></font>form factors"
      OV.SetVar('gui_notification', html)
      use_aspherical = OV.IsNoSpherA2()
    else:
      self.table_file_name = os.path.join(OV.FilePath(), OV.FileName() + '.tsc')
      if not os.path.exists(self.table_file_name):
        self.table_file_name = None
    if use_aspherical == True:
      self.method = OV.GetParam('snum.refinement.method')
      self.table_file_name = OV.GetParam('snum.NoSpherA2.file')
      html = "smtbx.refine using <font color=$GetVar(gui.green_text)><b>tabulated </b></font>Form Factors from <b>%s</b>" %os.path.basename(self.table_file_name)
      OV.SetVar('gui_notification', html)
      if not os.path.exists(self.table_file_name):
        self.table_file_name = None
    if self.table_file_name:
      self.table_file_name = self.table_file_name.encode("utf-8")
      OV.SetParam('snum.auto_hydrogen_naming', False)
      print("Using tabulated atomic form factors")

    fin_fn = os.path.join(OV.StrDir(), OV.FileName()) + ".fin"
    if os.path.exists(fin_fn):
      os.remove(fin_fn)

    Method_refinement.pre_refinement(self, RunPrgObject)


  def do_run(self, RunPrgObject):
    from refinement import FullMatrixRefine
    from smtbx.refinement.constraints import InvalidConstraint

    self.failure = True
    print('\n+++ STARTING olex2.refine +++++ %s' %self.version)

    verbose = OV.GetParam('olex2.verbose')

    RunPrgObject.cctbx = cctbx = FullMatrixRefine(
      max_cycles=RunPrgObject.params.snum.refinement.max_cycles,
      max_peaks=RunPrgObject.params.snum.refinement.max_peaks,
      verbose=verbose,
      on_completion=self.writeRefinementInfoForGui)
    try:
      olx.SetOlex2RefinementListener(True)
      olx.stopwatch.run(cctbx.run, table_file_name=self.table_file_name,
        ed_refinement=OV.IsEDRefinement())
    except InvalidConstraint as e:
      print(e)
    except NotImplementedError as e:
      print(e)
    else:
      self.failure = cctbx.failure
      if not self.failure:
        OV.SetVar('cctbx_R1',cctbx.r1[0])
        OV.SetVar('cctbx_wR2',cctbx.wR2_factor())
        OV.File('%s.res' %OV.FileName())
      # happens in the case of external interrupt
      elif cctbx.failure and OV.IsRemoteMode():
        try :
          if cctbx.cycles.n_iterations > 0:
            olx.Echo(
"""Saving model after %s cycles, some details will be unavailable.
The original model is in the INS file.""" %cctbx.cycles.n_iterations, m="warning")
            from collections import defaultdict
            self.cif = defaultdict(str)
            self.cif.update(cctbx.cycles.non_linear_ls.step_info)
            OV.File('%s.res' %OV.FileName())
            self.post_refinement(RunPrgObject=RunPrgObject)
        except AttributeError:
          pass
    finally:
      #print '+++ FINISHED olex2.refine ++++++++++++++++++++++++++++++++++++\n'
      olx.SetOlex2RefinementListener(False)
      OV.DeleteBitmap('refine')
      self.interrupted = cctbx.interrupted

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

  def writeRefinementInfoForGui(self, cif):
    #for key, value in cif.items():
    #  if "." in value:
    #    try:
    #      cif[key] = "%.4f" %float(value)
    #    except:
    #      pass
    f = open("%s/etc/CIF/olex2refinedata.html" %OV.BaseDir())
    t = f.read() %cif
    f.close()
    OV.write_to_olex('refinedata.htm',t)
    self.cif = cif

  def deal_with_AAFF(self, RunPrgObject):
    from aaff import deal_with_AAFF
    return deal_with_AAFF(RunPrgObject)

  def extraHtml(self):
    html = "<!-- #include olex2.refine-extra gui/tools/olex2.refine-extra.htm;1 -->"
    return html


class Method_cctbx_ChargeFlip(Method_solution):

  def do_run(self, RunPrgObject):
    from cctbx_olex_adapter import OlexCctbxSolve
    import traceback
    print('+++ STARTING olex2.solve ++++++++++++++++++++++++++++++++++++')
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
        print("*** No solution found ***")
    except Exception as err:
      print(err)
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
display = 'Charge Flipping'
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
display = 'G-N'
  .type=str
""")

levenberg_marquardt_phil = phil_interface.parse("""
name = 'Levenberg-Marquardt'
  .type=str
display = 'L-M'
  .type=str

""")

NSFF_phil = phil_interface.parse("""
name = 'NSFF'
  .type=str
display = 'NSFF'
  .type=str
""")

##########################################################################
# this is how a refinement thread could look like

# from threading import Thread
# from threads import ThreadEx
# from threads import ThreadRegistry
# class RefinementThread(ThreadEx):
#   instance = None
#   def RefinementThread(self):
#     ThreadRegistry().register(RefinementThread)
#     Thread.__init__(self)
#     RefinementThread.instance = self

#   def init(self, cctbx, table_file_name):
#     self.cctbx = cctbx
#     self.table_file_name = table_file_name
#     return self

#   def run(self):
#     import olex_core
#     try:
#       olex_core.IncRunningThreadsCount()
#       def EndUpdate(clear_meta=False):
#         olx.Schedule("xf.EndUpdate %s" %clear_meta)
#       def Compaq(**opts):
#         co = ""
#         for k,v in opts.items():
#           co += " -%s=%s" %(k, v)
#         olx.Schedule("compaq %s" %co)

#       self.EndUpdate_ = olx.xf.EndUpdate
#       self.Compaq_ = olx.Compaq
#       olx.xf.EndUpdate = EndUpdate
#       olx.Compaq = Compaq
#       self.cctbx.run(table_file_name=self.table_file_name,
#         ed_refinement=OV.IsEDRefinement())
#     finally:
#       olex_core.DecRunningThreadsCount()
#       olx.xf.EndUpdate = self.EndUpdate_
#       olx.Compaq = self.Compaq_
#       if OV.HasGUI():
#         import olex_gui
#         olex_gui.StopWaiting()
