from Method import Method_refinement, Method_solution
import phil_interface
from olexFunctions import OV
import olx
import olex
import os

def fill_from_map():
  """ Carbon on the Fo-Fc peaks of the refined, re-typed model that sit at a
  bond length from it: 1.25-1.65 A from a light atom, 1.8-2.6 A from one past
  Ar (a donor on a metal). Sigma is the map's median absolute deviation, which
  the missing atoms cannot inflate. The additions go through the tidy-up's own
  refine, prune and re-typing. Returns the number added; never raises. """
  try:
    import numpy as np
    from cctbx import maptbx
    from cctbx.array_family import flex
    from cctbx.eltbx import tiny_pse
    from cctbx_olex_adapter import OlexCctbxSolve
    sigma_cut = OV.GetParam('snum.solution.map_fill_sigma') or 7.0
    s = OlexCctbxSolve()
    xs = s.xray_structure()
    fo = s.reflections.f_sq_obs_merged.average_bijvoet_mates().f_sq_as_f()
    fo = fo.select(fo.data() > 0)
    fc = xs.structure_factors(d_min=fo.d_min(), algorithm='fft').f_calc()
    fo, fc = fo.common_sets(fc.average_bijvoet_mates() if fc.anomalous_flag() else fc)
    afc = abs(fc).data()
    k = flex.sum(fo.data()*afc)/flex.sum(afc*afc)
    fft = fo.customized_copy(data=fo.data()/k - afc).phase_transfer(fc).fft_map(
      symmetry_flags=maptbx.use_space_group_symmetry, resolution_factor=1/3.)
    fft.apply_volume_scaling()
    a = fft.real_map_unpadded().as_1d().as_numpy_array()
    sig = 1.4826*float(np.median(np.abs(a - np.median(a))))
    sc = [x for x in xs.scatterers() if x.scattering_type.strip() not in ('H', 'D', 'Q')]
    if sig <= 0 or len(sc) < 4:
      return 0
    def z(t):
      try:
        return tiny_pse.table(t.strip().capitalize()).atomic_number()
      except (RuntimeError, ValueError):
        return 0
    ops = list(xs.space_group().all_ops())
    M = np.array(xs.unit_cell().orthogonalization_matrix()).reshape(3, 3).T
    X = np.array([op*x.site for x in sc for op in ops], dtype=float)
    H = np.array([z(x.scattering_type) for x in sc for op in ops])
    # bond windows by the neighbour's row; a peak under 1.25 A (C=O, C#N, N-O)
    # must be half as strong again, an unmodelled H sits at 0.8-1.0 A
    # (100 COD cases: 91 of 282 missed atoms on 6-sigma peaks fell outside
    # 1.25-1.65 A, at 1.1-1.25 A from C/N/O and 1.7-1.9 A from Si/P/Cl)
    def bonded(d, zj, h):
      if zj > 18:
        return 1.8 <= d <= 2.6
      if zj > 10:
        return 1.45 <= d <= 2.1
      return 1.25 <= d <= 1.65 or 1.1 <= d < 1.25 and h >= 1.5*sigma_cut*sig
    pk = fft.peak_search(parameters=maptbx.peak_search_parameters(
      peak_search_level=1, interpolate=True, min_distance_sym_equiv=0.7),
      verify_symmetry=False).all(max_clusters=max(40, len(sc)))
    def near(p, Y):
      d = Y - p
      d -= np.round(d)
      d = np.sqrt(((d @ M)**2).sum(axis=1))
      j = int(d.argmin())
      return float(d[j]), j
    # ponytail: at most a quarter of the model per round, strongest first, and
    # never past 1.25x the 18 A^3-per-atom fill of the asymmetric unit
    # (cod_7711810: 26 atoms where 20 belong, the fill took it to 34)
    room = int(1.25*xs.unit_cell().volume()/len(ops)/18.0) - len(sc)
    # a full cell still takes one peak half as strong again a round: the rule
    # is 18 A^3 an atom, dense inorganics run under it (cod_2217672: N at 13 sigma)
    new, cap = [], min(max(4, len(sc)//4), room) if room > 0 else 1
    for p, h in zip(pk.sites(), pk.heights()):
      if h < (sigma_cut if room > 0 else 1.5*sigma_cut)*sig or len(new) >= cap:
        break
      p = np.array(p)
      d, j = near(p, X)
      if not bonded(d, H[j], h):
        continue
      if new and near(p, np.array([op*q for q in new for op in ops]))[0] < 1.1:
        continue
      new.append(tuple(p))
    if not new:
      return 0
    import re
    used = [int(m.group(1)) for m in
            (re.match(r"C(\d+)$", str(x.label)) for x in xs.scatterers()) if m]
    nxt = max(used or [0]) + 1
    names = [s.post_single_peak(p, 0, element="C", number=nxt + i)
             for i, p in enumerate(new)]
    print("Map fill added %d carbon(s) over %.1f sigma: %s"
          % (len(new), sigma_cut, " ".join(n for n in names if n)))
    return [n for n in names if n] or len(new)
  except Exception as err:
    print("Map fill did not run (%s: %s)" % (type(err).__name__, err))
    return 0

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
      # shown once by RunPrg.run, after the aspherical branch below has replaced it
      OV.SetVar('gui_notification', html)
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
  multi-attempt pipeline is a separate method (`Method_cctbx_Flint`) with
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
    """ `_tidy_origins`, then `flint_levers.final_levers` (`final_levers`):
    the final model pruned and completed, each change kept only when it passes
    a significance test, the model as it was otherwise.
    """
    self._tidy_origins()
    if OV.GetParam('snum.solution.final_levers') in (None, True):
      from flint_levers import final_levers
      final_levers()
    # after the levers, which leave a twinned model alone
    if OV.GetParam('snum.solution.twin_lever') in (None, True):
      try:
        from flint_levers import twin_lever
        twin_lever()
      except Exception as err:
        print('Twin lever failed: %s' % err)

  def _tidy_origins(self):
    """ `_tidy`, then again from each near-tied origin while R1 stays high.

    A heavy atom on a pseudo-centre leaves several origins that cc and R1 of
    the map cannot separate (cod_7023630, Np in P-1, chose the wrong one by
    R1 0.249 against 0.253); only the completed light atoms tell them apart.
    The model with the lowest R1 is kept.
    """
    self._tidy()
    cut = OV.GetParam('snum.solution.origin_retry_r1')
    cut = 0.05 if cut is None else float(cut)
    tcut = OV.GetParam('snum.solution.tangent_retry_r1')
    tcut = 0.15 if tcut is None else float(tcut)
    solver = getattr(self, 'cctbx_solver', None)
    alts = list(getattr(solver, 'origin_alternates', None) or []) if cut > 0 else []
    tangent = tcut > 0 and getattr(solver, 'chosen_f_calc', None) is not None
    if not alts and not tangent:
      return
    import shutil
    res = '%s.res' % OV.FileName()
    shutil.copyfile(res, res + '.pre')
    def final_r1(k):
      try:
        from refinement import FullMatrixRefine
        fmr = FullMatrixRefine(max_cycles=4, max_peaks=0)
        fmr.run()
        fmr.log.close()
        r1 = None if fmr.failure else fmr.r1[0]
      except Exception as err:
        print("Could not refine origin %d: %s" % (k, err))
        r1 = None
      OV.File(res)
      shutil.copyfile(res, res + '.o%d' % k)
      return r1, res + '.o%d' % k
    fmt = lambda r: "-" if r is None else "%.3f" % r
    def attempt(k, fc, what):
      try:
        names = [str(olx.xf.au.GetAtomName(i))
                 for i in range(int(olx.xf.au.GetAtomCount()))
                 if olx.xf.au.IsAtomDeleted(i) != 'true']
        if names:
          olex.m("kill %s" % " ".join(names))
        if not solver.placeSolution(fc):
          return None
        if OV.HasGUI():
          olx.xf.EndUpdate()
        olx.xf.SaveSolution(res)
        olx.Atreap('"%s"' % res)
        print("%s %d: completing it too (R1 %s so far)" % (what, k + 1, fmt(best[0])))
        self._tidy()
        r = final_r1(k)
        print("%s %d ends at R1 %s" % (what, k + 1, fmt(r[0])))
        return r
      except Exception as err:
        print("%s %d failed: %s" % (what, k + 1, err))
    best, tried = final_r1(0), 0
    def run(starts, what, k0):
      nonlocal best, tried
      for k, fc in enumerate(starts, k0):
        if best[0] is not None and best[0] <= cut:
          break
        r, tried = attempt(k, fc, what), tried + 1
        if r and r[0] is not None and (best[0] is None or r[0] < best[0]):
          best = r
    run(alts, "Origin", 1)
    if tangent and (best[0] is None or best[0] > tcut):
      # ponytail: 512 tangent starts cost 15-60 s, so only for what still fails
      try:
        starts = solver.tangentAlternates(skip=alts)
      except Exception as err:
        print("Tangent formula failed: %s" % err)
        starts = []
      run(starts, "Tangent start", len(alts) + 1)
    if not tried:
      shutil.copyfile(res + '.pre', res)
      from flint_levers import reap; reap(res)
      return
    shutil.copyfile(best[1], res)
    from flint_levers import reap; reap(res)
    print("Kept origin %d, R1 %s" % (int(best[1].rsplit('.o', 1)[1]) + 1, fmt(best[0])))

  def _tidy(self):
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
    # rounds of fill_from_map once the types are settled
    fills = OV.GetParam('snum.solution.map_fill_rounds')
    fills = 5 if fills is None else int(fills)
    fills0 = fills
    # a fill is kept only if the next refinement brings R1 under this fraction
    # of what it was; a carbon on a complete model barely moves it
    gain = OV.GetParam('snum.solution.map_fill_gain') or 1.0
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
      import shutil
      # a prune that sends R1 up took real atoms (an over-typed heavy atom runs
      # its U up like a noise peak), and the rounds after it strip the model:
      # the model before it comes back and pruning drops to light atoms, then
      # stops (cod_7706715: 80 atoms R1 0.13 -> 7 atoms R1 0.51)
      res = '%s.res' % OV.FileName()
      snap, mode, last, done, base, extra = None, 2, None, False, 0.0, False
      keep, pending = set(), set()
      # ponytail: prune-only rounds do not count, the budget is for re-typing;
      # the first round never re-types, the noise is always still there
      # a map fill buys its own rounds; nothing else gets more than before
      p, left = -1, 3*passes + 1
      while left > 0:
        p, left, r1 = p + 1, left - 1, None
        # ponytail: the refine macro spends 1.2 s a round on GUI, html and
        # files around 0.3 s of least squares; the engine is called directly
        try:
          from refinement import FullMatrixRefine
          fmr = FullMatrixRefine(max_cycles=cycles, max_peaks=0)
          # no .oxl per round: the next round overwrites it and the kill/anis
          # below change the model after it anyway; rsa() in its chirality
          # section is seconds a call on polymeric inorganics. Flack/Hooft
          # come from run().
          fmr.write_oxl = lambda cif_block=None: None
          OV.SetParam('snum.refinement.flack_str', "")
          fmr.run()
          fmr.log.close()
          if fmr.failure:
            raise RuntimeError("refinement failed")
          r1 = fmr.r1[0]
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
        if last == "map fill" and snap and r1 is not None:
          print("Map fill R1 %.4f -> %.4f" % (snap[0], r1))
        if snap and r1 is not None and (r1 > snap[0] + max(0.03, 0.25*snap[0])
                                        or last == "map fill" and r1 > gain*snap[0]):
          # ponytail: a re-typing that moves many atoms is not converged after
          # one round (cod_1557785: Ti 32 -> 8 was restored, pass 3 kept it and
          # typed 26 more atoms right); it gets one more round before the check
          if last == "re-typing" and not extra:
            extra = True
            continue
          shutil.copyfile(snap[1], res)
          from flint_levers import reap; reap(res)
          print("The %s sent R1 %.3f -> %.3f; the model before it is restored"
                % (last, snap[0], r1))
          if last != "prune":
            # a restored re-typing still gets its fills; it used to stop here
            # first (36 of 170 cases, cand9 arm 5 Oct 2026)
            if last == "re-typing" and fills > 0:
              done, snap, left = True, None, max(left, 1)
              continue
            break
          mode -= 1
          print("Pruning %s" % ("light atoms only" if mode else "off"))
          snap = None
          continue
        # a fill atom that took R1 down 3 % gets twice the U limit: the prune took
        # C20 (U 0.088) five times over (cod_1559310, R1 0.132 -> 0.111), but a
        # batch also carries noise at U 0.55 / 0.91 (cod_2207415, cod_8107302)
        if last == "map fill" and snap and r1 is not None and r1 < 0.97*snap[0]:
          keep |= pending
        if done:
          # the re-typing budget ran out with types still moving: the fill
          # still runs, and gets one refine, prune and re-typing of its own
          if fills > 0 and r1 is not None:
            OV.File(res)
            shutil.copyfile(res, res[:-4] + '.tidy.res')
            snap = (r1, res[:-4] + '.tidy.res')
            added = fill_from_map()
            if added:
              pending = set(added) if isinstance(added, list) else set()
              fills, last, done, passes = fills - 1, "map fill", False, 1
              left += 3
              continue
            fills = 0
          OlexCctbxSolve().printDoubt()
          break
        snap = None
        if r1 is not None:
          OV.File(res)
          shutil.copyfile(res, res[:-4] + '.tidy.res')
          snap = (r1, res[:-4] + '.tidy.res')
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
        # the reference never falls: a prune takes the top of the U list, the
        # median of the rest is lower and the next round took real carbon at
        # 3x of it (0.033 -> 0.023 -> 0.016, a Gd among them)
        median = base = max(base, us[len(us)//2][0] if us else 0.0)
        # carbon-free only: the threshold never drops under 0.06 there, since the
        # median collapses when a heavy atom is typed light; on organics the same
        # floor kept noise and cost 7 % more mistyped atoms (21 Sep 2026)
        floor = 0.0 if 'C' in [e.split(':')[0] for e in olx.xf.GetFormula('list').split(',')] else 0.02
        doomed = [n for u, i, n, t in us if u > factor*max(median, floor)*(2 if n in keep else 1)
                  and (mode == 2 or mode == 1 and heavy_z(t) <= 8)]
        # ponytail: the heavy atoms go anisotropic once the noise is gone;
        # an isotropic Pd leaves a residual the light atoms then read
        heavy = sorted(set("$" + t for u, i, n, t in us if anis_z
                           and heavy_z(t) > anis_z))
        last = "prune"
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
        # the fill waits for settled types, but prune and re-typing churn can
        # spend the budget first: the last rounds give it its turn (cod_7233829)
        if not retype or left <= 5 and fills == fills0 or not OlexCctbxSolve().reassignAfterCleanup():
          # ponytail: one completion once the types are settled; what it adds
          # goes through the same refine, prune and re-typing as the rest
          added = fills > 0 and fill_from_map()
          if added:
            pending = set(added) if isinstance(added, list) else set()
            fills, last, left = fills - 1, "map fill", left + 3
            continue
          if not complete or not OlexCctbxSolve().completeModel():
            break
          complete, last = False, "completion"
          continue
        passes -= 1
        last, extra = "re-typing", False
        # ponytail: the prunes leave fragments scattered again; a second
        # assembly after the re-typing joins what the first round could not
        olex.m("compaq -a")
        # the last re-typing is refined and checked like every other change
        done = passes <= 0
      # ponytail: the graph re-typer (cand11) has the last word on the types;
      # what it renames is refined once and goes through the blown-U check
      if retype and OlexCctbxSolve().gnnRetype():
        try:
          from refinement import FullMatrixRefine
          fmr = FullMatrixRefine(max_cycles=cycles, max_peaks=0)
          fmr.run()
          fmr.log.close()
        except Exception as err:
          print("Refinement after the graph re-typing failed: %s" % err)
      # a U that refined non-positive-definite (often on a special position)
      # is written with fields of 10 and more, which SHELX reads as free
      # variables (cod_4519371: O20 U22 38.1), as is a coordinate that ran
      # away (cod_2020523: C9 at 10, 10, 20); such atoms go isotropic at the
      # model median and are refined once more, and what is still blown goes
      from cctbx import adptbx
      def blown():
        b = []
        for i in range(int(olx.xf.au.GetAtomCount())):
          if olx.xf.au.IsAtomDeleted(i) == 'true' or \
             str(olx.xf.au.GetAtomType(i)) in ('Q', 'H'):
            continue
          u = [float(x) for x in str(olx.xf.au.GetAtomU(i)).split(',')]
          x = [float(c) for c in str(olx.xf.au.GetAtomCrd(i)).split(',')]
          if max(map(abs, x)) >= 5 or not 0 < u[0] < 1 or len(u) == 6 and (max(map(abs, u)) >= 1 or
              not adptbx.is_positive_definite((u[0], u[1], u[2], u[5], u[4], u[3]))):
            b.append((i, str(olx.xf.au.GetAtomName(i)), len(u) == 6))
        return b
      try:
        bad = blown()
      except Exception as err:
        bad = []
        print("Could not check the ADPs: %s" % err)
      if bad:
        for i, n, aniso in bad:
          if aniso:
            olex.m("isot %s" % n)
          olx.xf.au.SetAtomU(i, "%.4f" % (base or 0.05))
        print("Made %d atom(s) with a blown U isotropic: %s"
              % (len(bad), " ".join(n for i, n, a in bad)))
        try:
          from refinement import FullMatrixRefine
          fmr = FullMatrixRefine(max_cycles=cycles, max_peaks=0)
          fmr.run()
          fmr.log.close()
        except Exception as err:
          print("Refinement after the isotropic reset failed: %s" % err)
        bad = blown()
        if bad:
          olex.m("kill %s" % " ".join(n for i, n, a in bad))
          print("Removed %d atom(s) whose U is still blown" % len(bad))
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


class Method_cctbx_Flint(Method_cctbx_ChargeFlip):
  """ FLINT - FLipping, INterpretation, Typing.

  Charge flipping run several times, ranked, with the space group and the
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

  def tidy_solution(self):
    super().tidy_solution()
    # modulated data (spy.modulation.load): rank the superspace groups of the group FLINT settled on
    try:
      import Modulation
      Modulation.after_solve()
    except Exception as e:
      print("modulation: superspace candidates skipped: %s" % e)


flint_phil = phil_interface.parse("""
name = 'FLINT'
  .type=str
display = 'FLINT'
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
      threads = 0
        .type = int
        .caption = THRD
      suggest_space_groups = True
        .type = bool
        .caption = SGSG
      assign_elements = True
        .type = bool
        .caption = ASEL
      start_in_p1 = False
        .type = bool
        .caption = P1ST
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
