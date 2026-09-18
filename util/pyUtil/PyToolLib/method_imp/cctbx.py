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
      # kept as str: the table readers and the cache signatures compare it
      # against the str nsa2 'file' parameter, and the C++ builder takes str
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

    `compaq -a` gathers the fragments, then rounds of: refine `tidy_cycles`,
    prune every atom whose U exceeds `tidy_uiso_factor` times the median U
    of the model (a noise peak has no density to hold it and its U runs
    away; the median follows the temperature and the data where a fixed
    expectation per element did not), gather the difference peaks, make the
    atoms over `tidy_anis_z` anisotropic. Once a
    round (not the first) prunes nothing the survivors are re-typed from the
    refined model and the fragments gathered again (noise peaks typed carbon steal scale from every real atom
    and read them all a Z too heavy), at most `tidy_passes` times. Stops once
    a round changes nothing. Never lets the tidy-up cost the user the
    solution. With `complete_after_tidy` the difference map is asked once for
    what is missing (`completeModel`) once the types are settled.
    """
    factor = OV.GetParam('snum.solution.tidy_uiso_factor') or 3.0
    cycles = OV.GetParam('snum.solution.tidy_cycles')
    cycles = 4 if cycles is None else int(cycles)
    passes = OV.GetParam('snum.solution.tidy_passes')
    passes = 4 if passes is None else int(passes)
    retype = OV.GetParam('snum.solution.retype_after_tidy')
    retype = retype is None or retype
    # ponytail: off by default; on 45 COD entries the additions were all
    # pruned again, the misses were wrong-SG or noise-displaced, not absent
    complete = bool(OV.GetParam('snum.solution.complete_after_tidy'))
    anis_z = OV.GetParam('snum.solution.tidy_anis_z')
    anis_z = 10 if anis_z is None else int(anis_z)
    from cctbx.eltbx import tiny_pse
    def heavy_z(t):
      try:
        return tiny_pse.table(t.capitalize()).atomic_number()
      except (RuntimeError, ValueError):
        return 0
    try:
      olex.m("compaq -a")
    except Exception as err:
      print("Could not assemble the fragments: %s" % err)
    if cycles <= 0:
      return
    try:
      from cctbx_olex_adapter import OlexCctbxSolve
      # ponytail: prune-only rounds do not count, the budget is for re-typing;
      # the first round never re-types, the noise is always still there
      for p in range(3*passes):
        # ponytail: the refine macro spends 1.2 s a round on GUI, html and
        # files around 0.3 s of least squares; the engine is called directly
        try:
          from refinement import FullMatrixRefine
          fmr = FullMatrixRefine(max_cycles=cycles, max_peaks=0)
          OV.SetParam('snum.refinement.flack_str', "")
          fmr.run()
          fmr.log.close()
          if fmr.failure:
            raise RuntimeError("refinement failed")
          # the macro's absolute-structure check, which a polar group needs
          flack = OV.GetParam('snum.refinement.flack_str') or ""
          hooft = getattr(fmr, 'hooft', None)
          if (flack and float(flack.split('(')[0]) > 0.8) or (hooft is not None
              and round(getattr(hooft, 'p2_false', 0) or 0, 3) == 1):
            olex.m('inv -f')
            print("The structure has been inverted (Flack %s)" % flack)
        except Exception as err:
          print("Direct refinement failed (%s), using the macro" % err)
          olex.m("refine %d" % cycles)
        us = []
        for i in range(int(olx.xf.au.GetAtomCount())):
          if olx.xf.au.IsAtomDeleted(i) == 'true' or \
             str(olx.xf.au.GetAtomType(i)) in ('Q', 'H'):
            continue
          try:
            us.append((float(olx.xf.au.GetAtomUiso(i)), i,
                       str(olx.xf.au.GetAtomName(i)),
                       str(olx.xf.au.GetAtomType(i))))
          except (TypeError, ValueError):
            pass
        us.sort()
        median = us[len(us)//2][0] if us else 0.0
        doomed = [n for u, i, n, t in us if u > factor*max(median, 0.005)]
        # ponytail: the heavy atoms go anisotropic once the noise is gone;
        # an isotropic Pd leaves a residual the light atoms then read
        heavy = sorted(set("$" + t for u, i, n, t in us if anis_z
                           and heavy_z(t) > anis_z))
        if doomed:
          olex.m("kill %s" % " ".join(doomed))
          print("Pruned %d peak(s) whose U exceeded %.1fx the median U %.3f "
                "after %d cycles (%d left): %s"
                % (len(doomed), factor, median, cycles, len(us) - len(doomed),
                   " ".join(doomed[:12]) + (" ..." if len(doomed) > 12 else "")))
        else:
          print("Every atom refined to within %.1fx the median U %.3f; "
                "nothing pruned" % (factor, median))
        olex.m("compaq -q")
        if heavy:
          olex.m("anis %s" % " ".join(heavy))
        if doomed or p == 0:
          continue
        # re-typed only once nothing was pruned: noise peaks typed carbon steal
        # scale from every real atom and read them all a Z too heavy
        if not retype or not OlexCctbxSolve().reassignAfterCleanup():
          # ponytail: one completion once the types are settled; what it adds
          # goes through the same refine, prune and re-typing as the rest
          if not complete or not OlexCctbxSolve().completeModel():
            break
          complete = False
          continue
        passes -= 1
        # ponytail: the prunes leave fragments scattered again; a second
        # assembly after the re-typing joins what the first round could not
        olex.m("compaq -a")
        if passes <= 0:
          olex.m("refine %d" % cycles)
          OlexCctbxSolve().printDoubt()
          break
      OV.File('%s.res' % OV.FileName())
      addsym = OV.GetParam('snum.solution.missed_symmetry_check')
      if addsym is None or addsym:
        OlexCctbxSolve().checkMissedSymmetry(getattr(
          getattr(self, 'cctbx_solver', None), 'solution_suggestions', None))
    except Exception as err:
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
      max_seconds = 120
        .type = float
        .caption = MAXS
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
