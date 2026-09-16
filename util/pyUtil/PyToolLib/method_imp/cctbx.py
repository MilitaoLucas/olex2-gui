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
      html = f"olex2.refine using __spherical__ form factors "
      OV.SetVar('gui_notification', html)
      import gui
      gui.set_notification()
      use_aspherical = OV.IsNoSpherA2()
    else:
      self.table_file_name = os.path.join(OV.FilePath(), OV.FileName() + '.tsc')
      if not os.path.exists(self.table_file_name):
        self.table_file_name = None
    if use_aspherical == True:
      self.method = OV.GetParam('snum.refinement.method')
      from variableFunctions import nsa2_get_param
      self.table_file_name = nsa2_get_param('file')
      if self.table_file_name:
        html = f"olex2.refine using __non-spherical__ form factors from __{os.path.basename(self.table_file_name)}__ "
      else:
        html = f"olex2.refine using __non-spherical__ form factors (file not found)"
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
      self.hooft = cctbx.hooft
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
      self.objective_only = cctbx.objective_only

  def post_refinement(self, RunPrgObject):
    OV.SetParam('snum.refinement.max_cycles', self.cycles)
    if not self.objective_only:
      self.writeRefinementInfoIntoRes(self.cif)
    self.cif.setdefault('_refine_ls_abs_structure_Flack', "n/a")
    self.cif.setdefault('_refine_ls_shift/su_max', "n/a")
    self.cif.setdefault('_refine_ls_shift/su_mean', "n/a")

    map_type = "potential" if OV.IsEDData() else "density"

    txt = f'''
    R1_all=%(_refine_ls_R_factor_all)s;
    R1_gt = %(_refine_ls_R_factor_gt)s;
    wR_ref = %(_refine_ls_wR_factor_ref)s;
    GOOF = %(_refine_ls_goodness_of_fit_ref)s;
    Shift_max = %(_refine_ls_shift/su_max)s;
    Shift_mean = %(_refine_ls_shift/su_mean)s;
    Reflections_all = %(_reflns_number_total)s;
    Reflections_gt = %(_reflns_number_gt)s;
    Parameters = %(_refine_ls_number_parameters)s;
    Hole = %(_refine_diff_{map_type}_min)s;
    Peak = %(_refine_diff_{map_type}_max)s;
    Flack = %(_refine_ls_abs_structure_Flack)s;
    ''' % self.cif

    try:
      olx.xf.RefinementInfo(txt %self.cif)
    except:
      pass

  def writeRefinementInfoForGui(self, cif):
    #for key, value in cif.items():
    #  if "." in value:
    #    try:
    #      cif[key] = "%.4f" %float(value)
    #    except:
    #      pass
    if "_refine_ls_shift/su_max" in cif:
      with open("%s/etc/CIF/olex2refinedata.html" %OV.BaseDir()) as f:
        t = f.read()
        if OV.IsEDData():
          t = t.replace("_diff_density_", "_diff_potential_")
        t = t % cif
        OV.write_to_olex('refinedata.htm',t)
    self.cif = cif

  def deal_with_AAFF(self, RunPrgObject):
    from aaff import deal_with_AAFF
    return deal_with_AAFF(RunPrgObject)

  def extraHtml(self):
    html = "<!-- #include olex2.refine-extra gui/tools/olex2.refine-extra.htm;1 -->"
    return html


class Method_cctbx_ChargeFlip(Method_solution):
  """ The original single charge-flipping run.

  **Behaviour here is frozen on purpose.** Existing users, scripts and the
  other developers' workflows all reach structure solution through this
  method, so it keeps doing exactly one run and keeping the first result. The
  multi-attempt pipeline is a separate method (`Method_cctbx_AutoSolve`) with
  its own name in the GUI, rather than a mode of this one -- a method that
  quietly does something different depending on a setting is the harder thing
  to review, to script against and to explain.
  """

  # Which branch of the shared adapter to take. Subclass and change this.
  solve_mode = "classic"

  # Tidy-up applied to the loaded model after solving. **Empty here on
  # purpose**: `Charge Flipping` must leave the structure exactly as it always
  # has, so nothing is assembled, refined or pruned behind the user's back.
  tidy_after_solve = False

  def do_run(self, RunPrgObject):
    from cctbx_olex_adapter import OlexCctbxSolve
    import traceback
    print('+++ STARTING olex2.solve ++++++++++++++++++++++++++++++++++++')
    RunPrgObject.solve = True
    cctbx = OlexCctbxSolve()
    # Kept so post_solution can reach the space-group suggestions this run
    # produced; they are computed during solving and would otherwise be lost
    # when this method returns.
    self.cctbx_solver = cctbx

    #solving_interval = int(float(self.getArgs().split()[1]))
    solving_interval = self.phil_index.params.flipping_interval

    formula_l = olx.xf.GetFormula('list')
    formula_l = formula_l.split(",")
    formula_d = {}
    for item in formula_l:
      item = item.split(":")
      formula_d.setdefault(item[0], {'count':float(item[1])})
    try:
      have_solution = cctbx.runChargeFlippingSolution(
        solving_interval=solving_interval, mode=self.solve_mode)
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
    # Harmless for the classic method: it never sets `solution_suggestions`,
    # so this returns immediately.
    self.show_space_group_suggestions(RunPrgObject)
    if self.tidy_after_solve:
      # **Deferred, not called here.** `post_solution` runs while
      # `RunPrg.running` is still True, so `refine` is refused with "Already
      # running. Please wait..." -- and refused without raising, so the prune
      # then read every U as the 0.06 it was seeded with and removed nothing.
      # RunPrg invokes this once the run is finished.
      RunPrgObject.please_tidy_solution = self.tidy_solution

  def tidy_solution(self):
    """ Make the solution look like chemistry, then drop what will not refine.

    Two steps, in this order, because the second depends on the first.

    **Assemble.** Charge flipping places peaks anywhere in the cell, so the
    fragments come out scattered across symmetry images and the model looks
    shattered even when the phasing is right. `compaq -a` gathers them into
    connected molecules -- the same thing a crystallographer does by hand
    immediately after solving.

    **Refine briefly, then prune by ADP.** The peak search deliberately
    over-picks (`1.3 x V/18.6/order`, so ~42 peaks where the deposited model
    has 31 atoms), and the surplus is noise. A real atom settles to a sensible
    displacement parameter in a few cycles; a noise peak has no density to hold
    it and its U runs away. So a short refinement separates them far better
    than peak height does, which is Florian's observation and the reason this
    is worth the seconds it costs.

    Reuses Olex2's own idiom rather than inventing one --
    `RunPrg.doAutoTidyBefore/After` prunes with exactly this pair of calls.
    """
    factor = OV.GetParam('snum.solution.tidy_uiso_factor') or 3.0
    cycles = OV.GetParam('snum.solution.tidy_cycles')
    cycles = 4 if cycles is None else int(cycles)
    try:
      olex.m("compaq -a")
    except Exception as err:
      print("Could not assemble the fragments: %s" % err)
    if cycles <= 0:
      return
    try:
      olex.m("refine %d" % cycles)
      # **Count after the refinement, not before it.** olex2.refine runs a
      # Fourier analysis and adds the difference peaks it finds to the model,
      # so an atom count taken before the refinement is compared against a
      # larger, different thing afterwards -- which reported "Pruned -22
      # peak(s)" on the first real run, having actually removed several.
      before = int(olx.xf.au.GetAtomCount())

      # **Judge U against what that element should have, not against one
      # number.** A flat threshold is confounded by element: palladium belongs
      # near 0.02 and carbon near 0.06, so any single cutoff is simultaneously
      # too tight for the light atoms and far too loose for the heavy ones. The
      # ratio is the signal -- a peak that is not an atom has no density to
      # hold it and its U runs away from the element's expectation whatever
      # that expectation was.
      from cctbx_olex_adapter import OlexCctbxSolve
      expected_for = OlexCctbxSolve().startingUiso
      doomed = []
      for i in range(int(olx.xf.au.GetAtomCount())):
        if olx.xf.au.IsAtomDeleted(i) == 'true':
          continue
        symbol = str(olx.xf.au.GetAtomType(i))
        if symbol == 'Q':
          continue                      # unassigned peaks are not ours to judge
        try:
          u = float(olx.xf.au.GetAtomUiso(i))
        except (TypeError, ValueError):
          continue
        if u > factor*expected_for(symbol):
          doomed.append(str(olx.xf.au.GetAtomName(i)))
      if doomed:
        olex.m("kill %s" % " ".join(doomed))
      after = int(olx.xf.au.GetAtomCount())
      if doomed:
        print("Pruned %d peak(s) whose U exceeded %.1fx the value expected "
              "for their element after %d cycles (%d left): %s"
              % (len(doomed), factor, cycles, after,
                 " ".join(doomed[:12]) + (" ..." if len(doomed) > 12 else "")))
      else:
        print("Every atom refined to within %.1fx its expected U; "
              "nothing pruned" % factor)

      # **Gather the difference peaks last, once the model is settled.**
      # The refinement's Fourier analysis adds its peaks wherever symmetry puts
      # them, so they arrive scattered across images exactly as the solved
      # fragments did -- and pruning has just changed which atoms they should
      # sit near. `-q` moves the Q peaks to the structure, so what is left to
      # interpret is next to the molecule rather than a cell away from it.
      #
      # After the kill, not before: moving peaks toward atoms that are about to
      # be deleted would place them against the wrong neighbours.
      olex.m("compaq -q")

      # **Re-type last, on the cleaned model.** Florian's point: the peaks that
      # are not atoms sit in the real atoms' descriptor neighbourhoods and in
      # the carbon-scale fit, so they corrupt the typing of what is around them.
      # Doing it here rather than at solve time is worth +0.05 (n=137) and
      # +0.03 (n=126, independent) as an oracle bound.
      #
      # After `compaq -q`, not before: the descriptor is a description of an
      # atom's surroundings, so it has to be computed once the fragments are
      # where they belong and the doomed peaks are gone.
      retype = OV.GetParam('snum.solution.retype_after_tidy')
      if retype is None or retype:
        OlexCctbxSolve().reassignAfterCleanup()
    except Exception as err:
      # Never let the tidy-up cost the user their solution: the structure is
      # already saved and loaded by this point.
      import traceback
      print("Post-solution tidy-up failed: %s" % err)
      if OV.IsDebugging():
        traceback.print_exc()

  def show_space_group_suggestions(self, RunPrgObject):
    """ The solution chooser, when the solver produced candidates.

    Presented exactly as the existing solution table is
    (`method_imp/shelx.py`) -- same template, same click-to-load action -- so
    the two solution routes look and behave alike.
    Silent when there is nothing to choose between: a one-row chooser is noise.
    """
    if not OV.HasGUI():
      return
    cctbx = getattr(self, 'cctbx_solver', None)
    suggestions = getattr(cctbx, 'solution_suggestions', None) if cctbx else None
    if not suggestions or len(suggestions.suggestions) < 2:
      return
    try:
      written = cctbx.writeSuggestions(cctbx.solution_f_obs, suggestions)
      if len(written) < 2:
        return
      RunPrgObject.post_prg_output_html_message = \
        cctbx.suggestionsTableHtml(written, suggestions)
    except Exception as err:
      import traceback
      print("Could not show space-group suggestions: %s" % err)
      if OV.IsDebugging():
        traceback.print_exc()

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
      weak_reflection_fraction = 0.2
        .type = float
        .caption = WRFR
        }
    default=True
      .type=bool
    }
  }
""")


class Method_cctbx_AutoSolve(Method_cctbx_ChargeFlip):
  """ Charge flipping run several times, ranked, with the space group and the
  element types worked out rather than assumed.

  Everything the classic method does, plus the three things a user has to do
  by hand today:

    * **several attempts instead of one.** Charge flipping starts from random
      phases, so a single run is one draw. Eight ranked attempts take solution
      success from 0.739 to 0.863 on 10,099 development structures.
    * **the space group is decided, and three are offered.** Given the Laue
      class, the best suggestion is right 0.878 of the time against 0.725 for
      the old route, and the right group is among the three offered 0.954 of
      the time. Offering three is the honest presentation: of 17 crystals in
      our archive refined twice, every disagreement between crystallographers
      was centrosymmetry, mirror-versus-glide or an axis convention -- the
      same places this fails.
    * **peaks come back with proposed elements** instead of all as carbon.

  Separate from `Charge Flipping` rather than a switch inside it, so that
  method keeps behaving exactly as it always has.
  """

  solve_mode = "auto"

  # Assemble the fragments and drop the peaks that will not refine. On here
  # and off for `Charge Flipping`, which is the whole point of the split.
  tidy_after_solve = True


auto_solve_phil = phil_interface.parse("""
name = 'Auto-Solve'
  .type=str
display = 'Auto-Solve'
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
      weak_reflection_fraction = 0.2
        .type = float
        .caption = WRFR
      n_trials = 8
        .type = int
        .caption = NTRI
      suggest_space_groups = True
        .type = bool
        .caption = SGSG
      assign_elements = True
        .type = bool
        .caption = ASEL
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

# Driven by scipy.optimize.minimize rather than by solving the normal
# equations for a step. Adding another is one more of these plus the name in
# params.phil, in FullMatrixRefine.solvers and in FullMatrixRefine.
# scipy_methods; which arguments and tolerances the method takes is settled in
# scitbx.lstbx.scipy_iterations.supported_methods.

# scipy's 'CG': nonlinear conjugate gradient, a first-order method working on
# the full problem and relinearising it at every step. Distinct from CGLS-J,
# which iterates conjugate gradients on the linearised least-squares system
# (one linearisation per cycle), and from Newton-CG, which uses second
# derivatives. The internal name stays FullCG so saved settings still resolve;
# only the label shown to the user says which CG this is.
conjugate_gradient_phil = phil_interface.parse("""
name = 'FullCG'
  .type=str
display = 'NL-CG'
  .type=str
""")

lbfgsb_phil = phil_interface.parse("""
name = 'L-BFGS-B'
  .type=str
display = 'L-BFGS'
  .type=str
""")

newton_cg_phil = phil_interface.parse("""
name = 'Newton-CG'
  .type=str
display = 'Newt-CG'
  .type=str
""")

# Sequential least squares programming: builds a quadratic model of the
# objective and solves it subject to linearised constraints. First order, so it
# costs what L-BFGS costs per evaluation rather than what Newton-CG does.
slsqp_phil = phil_interface.parse("""
name = 'SLSQP'
  .type=str
display = 'SLSQP'
  .type=str
""")

# Not a scipy method: conjugate gradients on the linearised problem, one
# linearisation per cycle, the normal matrix never formed. The J marks it as
# the variant which stores the design matrix, as against a matrix-free one.
cgls_j_phil = phil_interface.parse("""
name = 'CGLS-J'
  .type=str
display = 'CGLS-J'
  .type=str
""")

# The two maximum-likelihood targets. They are not steps of their own: both
# take the CGLS-J step and change what is being minimised, from weighted least
# squares on F^2 to the Rice likelihood on amplitudes (MLF) or its convolution
# with the measurement error on intensities (MLI). They appear here rather
# than as a switch because the target is the thing a user is choosing between,
# and because the likelihood is worth having only below about one reflection
# per parameter - which is why they are offered on polymers.
mlf_phil = phil_interface.parse("""
name = 'MLF'
  .type=str
display = 'ML - F'
  .type=str
""")

mli_phil = phil_interface.parse("""
name = 'MLI'
  .type=str
display = 'ML - I'
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
