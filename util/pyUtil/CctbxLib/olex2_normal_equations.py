import sys
import time

from scitbx.array_family import flex
from smtbx.refinement import least_squares
from smtbx.structure_factors import direct
from cctbx import adptbx, xray
from smtbx_refinement_least_squares_ext import *

import math
from olexFunctions import OV

import olx
import olex
import olex_core

# need this pattern to use 'dynamic' base
def normal_equation_class():
  def get_base_class():
    """ Whichever accumulator cctbx picks, OpenMP or not.

    This used to force the BLAS 2 accumulator whenever OpenMP was on, because
    the OpenMP accumulation was only implemented for that one and asking for
    BLAS 3 threw. It is implemented for both now, and forcing BLAS 2 is an
    expensive thing to do: on a structure of a few thousand parameters the
    difference between the two accumulators is the best part of an order of
    magnitude, far more than OpenMP itself is worth.
    """
    return least_squares.crystallographic_ls_class()

  class normal_eqns(get_base_class()):
    log = None
    std_observations = None
    step_info = {}

    def __init__(self, observations, refinement, olx_atoms,
                table_file_name=None, **kwds):
      super(normal_eqns, self).__init__(
        observations, refinement.reparametrisation, initial_scale_factor=OV.GetOSF(),
        **kwds)
      # both branches, or the radial f'/f'' correction would quietly do nothing
      # for exactly the refinements it is most likely to be used on
      disp_correction = getattr(refinement, 'dispersion_radial', None)
      if table_file_name:
        try:
          from cctbx_olex_adapter import get_table_contribution
          one_h_linearisation = direct.f_calc_modulus_squared(
            self.xray_structure,
            scatterer_contribution=get_table_contribution(
              self.xray_structure, table_file_name),
            disp_correction=disp_correction)
        except Exception as e:
          e_str = str(e)
          if "stoks.size() == scatterer" in e_str:
            print("Number of atoms in model and table are not matching!")
          elif "Error during building of normal equations using OpenMP" in e_str:
            print("OpenMP Error during Normal Equation build-up, likely missing reflection in .tsc file")
          raise e
      else:
        try:
          from cctbx_olex_adapter import note_table_not_used
          note_table_not_used()
        except ImportError:
          pass
        one_h_linearisation = direct.f_calc_modulus_squared(
          self.xray_structure, reflections=self.observations,
          disp_correction=disp_correction)
      self.refinement = refinement
      self.one_h_linearisation = f_calc_function_default(one_h_linearisation)
      self.f_mask_data = None
      if self.f_mask is None:
        self.f_mask_data = MaskData(flex.complex_double())
      else:
        self.f_mask_data = MaskData(self.observations,
                                    self.xray_structure.space_group(),
                                    self.observations.fo_sq.anomalous_flag(),
                                    self.f_mask.indices(),
                                    self.f_mask.data())
      self.olx_atoms = olx_atoms
      self.n_current_cycle = 0

    def begin_cycle(self):
      """ Note where the structure stands, so shifts can be reported against it.
      """
      self.n_current_cycle += 1
      self.xray_structure_pre_cycle = self.xray_structure.deep_copy_scatterers()

    def end_cycle(self):
      """ Report the cycle and hand the structure back to Olex2. """
      self.show_cycle_summary(log=self.log)
      self.show_sorted_shifts(max_items=10, log=self.log)
      self.restraints_manager.show_sorted(
        self.xray_structure, f=self.log)
      self.show_cycle_summary()
      self.feed_olex()

    def step_forward(self):
      # Gauss-Newton and Levenberg-Marquardt move once per cycle, so the whole
      # of a cycle happens here. The scipy minimisers move many times per cycle
      # and call begin_cycle and end_cycle themselves, so that Olex2 is fed once
      # per iteration rather than once per evaluation of the objective.
      self.begin_cycle()
      super(normal_eqns, self).step_forward()
      self.end_cycle()
      return self

    def step_backward(self):
      super(normal_eqns, self).step_backward()
      return self

    def analyse_shifts(self):
      self.max_shift_esd = None
      self.max_shift_esd_item = None
      self.mean_shift_esd = None
      try:
        self.iterations_object.analyse_shifts()
        self.mean_shift_esd = self.iterations_object.mean_ls_shift_over_su
        self.max_shift_esd = self.iterations_object.max_ls_shift_over_su
        self.max_shift_esd_item = self.iterations_object.max_shift_for
      except Exception as s:
        print(s)

    def show_cycle_summary(self, log=None):
      if log is None: log = sys.stdout
      # self.reparametrisation.n_independents + OSF
      max_shift_site = self.max_shift_site()
      OV.SetParam('snum.refinement.max_shift_site', max_shift_site[0])
      OV.SetParam('snum.refinement.max_shift_site_atom', max_shift_site[1].label)
      max_shift_u = self.max_shift_u()
      OV.SetParam('snum.refinement.max_shift_u', max_shift_u[0])
      OV.SetParam('snum.refinement.max_shift_u_atom', max_shift_u[1].label)
      self.analyse_shifts()
      print_tabular = True
      # store step info
      self.step_info['_refine_ls_shift/su_mean'] = self.mean_shift_esd
      self.step_info['_refine_ls_shift/su_max'] = self.max_shift_esd
      self.step_info['_refine_ls_R_factor_all'] = self.r1_factor()[0]
      R1_4sig = self.r1_factor(cutoff_factor=2)[0]
      self.step_info['_refine_ls_R_factor_gt'] = R1_4sig
      self.step_info['_refine_ls_wR_factor_ref'] = self.wR2()
      self.step_info['_refine_ls_goodness_of_fit_ref'] = self.goof()

      OV.SetParam('snum.refinement.last_R1', "%.4f" %self.step_info['_refine_ls_R_factor_gt'])
      OV.SetParam('snum.refinement.last_wR2', "%.4f" %self.step_info['_refine_ls_wR_factor_ref'])

      #if OV.IsControl('R1_GUI'):
        #OV.SetControlValue('R1_GUI', f"{R1_4sig * 100:.2f}%")

      if print_tabular:
        header = "  % 5i    % 6.2f    % 6.2f    % 6.2f    % 8.3f %-11s  % 8.2e %-11s  % 8.2e %-11s"
        params = (self.n_current_cycle,
            R1_4sig * 100,
            self.wR2() * 100,
            self.goof(),
            self.max_shift_esd,
            '(' + self.max_shift_esd_item + ')',
            max_shift_site[0],
            '(' + max_shift_site[1].label + ')',
            max_shift_u[0],
            '(' + max_shift_u[1].label + ')',
        )
        if hasattr(self.iterations_object,'mu'):
          header += "  % 8.2e"
          params += (self.iterations_object.mu,)
        # a scipy minimiser evaluates the objective many times per cycle, and
        # how many is the thing to watch: each costs about one Gauss-Newton
        # cycle, so it is what its speed comes down to
        if hasattr(self.iterations_object, 'n_evaluations'):
          header += "  % 8i"
          params += (self.iterations_object.n_evaluations,)
        # conjugate gradient least squares reports the conjugate gradient
        # iterations it has spent, which are what its cost comes down to
        if hasattr(self.iterations_object, 'n_cg_iterations'):
          header += "  % 8i"
          params += (self.iterations_object.n_cg_iterations,)
        print(header %params, file=log)

      else:
        print("wR2 = %.4f | GooF = %.4f for %i data and %i parameters" %(
          self.wR2(),
          self.goof(),
          self.observations.fo_sq.size(),
          self.reparametrisation.n_independents + 1,
        ), file=log)

        print("Max shifts: ", end=' ', file=log)

        print("Site: %.4f A for %s |" %(
          max_shift_site[0],
          max_shift_site[1].label
        ), end=' ', file=log)
        print("dU = %.4f for %s" %(
          max_shift_u[0],
          max_shift_u[1].label,
        ), file=log)

    def max_shift_site(self):
      return next(self.iter_shifts_sites(max_items=1))

    def max_shift_u(self):
      return next(self.iter_shifts_u(max_items=1))

    def max_shift_esd(self):
      self.get_shifts()
      return next(self.iter_shifts_u(max_items=1))


    def iter_shifts_sites(self, max_items=None):
      scatterers = self.xray_structure.scatterers()
      sites_shifts = self.xray_structure.sites_cart() -\
                  self.xray_structure_pre_cycle.sites_cart()
      distances = sites_shifts.norms()
      i_distances_sorted = flex.sort_permutation(data=distances, reverse=True)
      if max_items is not None:
        i_distances_sorted = i_distances_sorted[:max_items]
      for i_seq in iter(i_distances_sorted):
        yield distances[i_seq], scatterers[i_seq]

    def iter_shifts_u(self, max_items=None):
      scatterers = self.xray_structure.scatterers()
      adp_shifts = self.xray_structure.extract_u_cart_plus_u_iso() \
                - self.xray_structure_pre_cycle.extract_u_cart_plus_u_iso()
      norms = adp_shifts.norms()
      i_adp_shifts_sorted = flex.sort_permutation(data=norms, reverse=True)
      if max_items is not None:
        i_adp_shifts_sorted = i_adp_shifts_sorted[:max_items]
      for i_seq in iter(i_adp_shifts_sorted):
        yield norms[i_seq], scatterers[i_seq]

    def show_log(self, f=None):
      import sys
      if self.log is sys.stdout: return
      if f is None: f = sys.stdout
      print(self.log.getvalue(), file=f)

    def show_sorted_shifts(self, max_items=None, log=None):
      import sys
      if log is None: log = sys.stdout
      print("Sorted site shifts in Angstrom:", file=log)
      print("shift scatterer", file=log)
      n_not_shown = self.xray_structure.scatterers().size()
      for distance, scatterer in self.iter_shifts_sites(max_items=max_items):
        n_not_shown -= 1
        print("%5.3f %s" %(distance, scatterer.label), file=log)
        if round(distance, 3) == 0: break
      if n_not_shown != 0:
        print("... (remaining %d not shown)" % n_not_shown, file=log)
      #
      print("Sorted adp shift norms:", file=log)
      print("dU scatterer", file=log)
      n_not_shown = self.xray_structure.scatterers().size()
      for norm, scatterer in self.iter_shifts_u(max_items=max_items):
        n_not_shown -= 1
        print("%5.3f %s" %(norm, scatterer.label), file=log)
        if round(norm, 3) == 0: break
      if n_not_shown != 0:
        print("... (remaining %d not shown)" % n_not_shown, file=log)

    def show_shifts(self, log=None):
      import sys
      if log is None: log = sys.stdout
      site_symmetry_table = self.xray_structure.site_symmetry_table()
      i=0
      for i_sc, sc in enumerate(self.xray_structure.scatterers()):
        op = site_symmetry_table.get(i_sc)
        print("%-4s" % sc.label, file=log)
        if sc.flags.grad_site():
          n = op.site_constraints().n_independent_params()
          if n != 0:
            print(("site:" + "%7.4f, "*(n-1) + "%7.4f")\
                  % tuple(self.shifts[-1][i:i+n]), file=log)
          i += n
        if sc.flags.grad_u_iso() and sc.flags.use_u_iso():
          if not(sc.flags.tan_u_iso() and sc.flags.param > 0):
            print("u_iso: %6.4f" % self.shifts[i], file=log)
            i += 1
        if sc.flags.grad_u_aniso() and sc.flags.use_u_aniso():
          n = op.adp_constraints().n_independent_params()
          print((("u_aniso:" + "%6.3f, "*(n-1) + "%6.3f")
                        % tuple(self.shifts[-1][i:i+n])), file=log)
          i += n
        if sc.flags.grad_occupancy():
          print("occ: %4.2f" % self.shifts[-1][i], file=log)
          i += 1
        if sc.flags.grad_fp():
          print("f': %6.4f" % self.shifts[-1][i], file=log)
          i += 1
        if sc.flags.grad_fdp():
          print("f'': %6.4f" % self.shifts[-1][i], file=log)
          i += 1
        print(file=log)

    def feed_olex(self):
      ## Feed Model
      def iter_scatterers():
        for a in self.xray_structure.scatterers():
          label = a.label
          xyz = a.site
          symbol = a.scattering_type
          if a.flags.use_u_iso():
            u = (a.u_iso,)
            u_eq = u[0]
          if a.flags.use_u_aniso():
            u_cif = adptbx.u_star_as_u_cart(self.xray_structure.unit_cell(), a.u_star)
            u = u_cif
            if len(u) == 6:
              u = [u[0], u[1], u[2], u[5], u[4], u[3]]
              if a.is_anharmonic_adp():
                u += a.anharmonic_adp.data()
            u_eq = adptbx.u_star_as_u_iso(self.xray_structure.unit_cell(), a.u_star)
          yield (label, xyz, u, u_eq,
                a.occupancy*a.weight_without_occupancy(),
                symbol, a.flags, a)
      this_atom_id = 0
      for name, xyz, u, ueq, occu, symbol, flags, a in iter_scatterers():
        id = self.olx_atoms.atom_ids[this_atom_id]
        this_atom_id += 1
        olx.xf.au.SetAtomCrd(id, *xyz)
        olx.xf.au.SetAtomU(id, *u)
        olx.xf.au.SetAtomOccu(id, occu)
        if flags.grad_fp():
          olx.xf.au.SetAtomDisp(id, a.fp, a.fdp)
      #update OSF
      OV.SetOSF(self.scale_factor())
      #update FVars
      for var in self.shared_param_constraints:
        if var[3]:
          OV.SetFVar(var[0], var[1].value.value*var[2])
        else:
          OV.SetFVar(var[0], 1.0-var[1].value.value*var[2])
      #update BASF
      self.update_BASF()
      #update EXTI
      if self.reparametrisation.fc_correction and self.reparametrisation.fc_correction.grad:
        if isinstance(self.reparametrisation.fc_correction, xray.shelx_extinction_correction):
          OV.SetExtinction(self.reparametrisation.fc_correction.value)
        elif isinstance(self.reparametrisation.fc_correction, xray.shelx_SWAT_correction):
          OV.SetSWAT(self.reparametrisation.fc_correction.g,
            self.reparametrisation.fc_correction.U)
      for (i,r) in enumerate(self.shared_rotated_adps):
        if r.refine_angle:
          olx.xf.rm.UpdateCR('olex2.constraint.rotated_adp', i, r.angle.value*180/math.pi)
      for (i,r) in enumerate(self.shared_rotating_adps):
        if r.refine_angle:
          olx.xf.rm.UpdateCR('olex2.constraint.rotating_adp', i, r.scale.value,
            r.alpha.value*180/math.pi, r.beta.value*180/math.pi, r.gamma.value*180/math.pi)
      self.complete_update()
      olx.xf.EndUpdate()
      if OV.HasGUI():
        olx.Refresh()
      if OV.isInterruptSet():
        self.iterations_object.n_iterations = self.iterations_object.n_max_iterations
        self.iterations_object.interrupted = True
    # interface functions - do not delete
    def complete_update(self):
      pass
    def on_completion(self):
      pass
    def update_BASF(self):
      if not self.twin_fractions:
        return
      idx = 0
      for fraction in self.twin_fractions:
        if fraction.grad:
          olx.xf.rm.BASF(idx, fraction.value)
          idx += 1

  return normal_eqns

from scitbx.lstbx import normal_eqns_solving

class iterations_with_shift_analysis(normal_eqns_solving.iterations):
  convergence_as_shift_over_esd = 1e-3
  max_ls_shift_over_su = None
  iteration_listeners = []

  def shifts_to_analyse(self):
    """ The shifts whose size is to be reported.

    For the solvers here that is the step about to be taken, which is what the
    normal equations were just solved for. A solver which does not move along
    that step reports the shifts it actually applied instead.
    """
    return self.non_linear_ls.step()

  def standard_uncertainties(self):
    """ The s.u. of the independent parameters.

    This is the expensive half of the shift analysis: it solves the normal
    equations, which costs a Cholesky decomposition and, since solving consumes
    the normal matrix, obliges anything still needing the normal equations to
    build them again.
    """
    return flex.sqrt(
      self.non_linear_ls.covariance_matrix().matrix_packed_u_diagonal())

  def analyse_shifts(self, limit_shift_over_su=None):
    if self.max_ls_shift_over_su is not None:
      return
    x = self.shifts_to_analyse()
    ls_shifts_over_su = x/self.standard_uncertainties()
    max_shift_i = 0
    s_sum = 0
    for i,s in enumerate(ls_shifts_over_su):
      s_sum += abs(s)
      if abs(ls_shifts_over_su[max_shift_i]) < abs(s):
        max_shift_i = i
    #max shift for the LS
    self.mean_ls_shift_over_su = s_sum/len(ls_shifts_over_su)
    self.max_ls_shift_over_su = ls_shifts_over_su[max_shift_i]
    r = self.non_linear_ls.actual.reparametrisation
    J = r.jacobian_transpose_matching_grad_fc().transpose()
    spc = 0
    for ip in r.independent_scalar_parameters:
      spc += ip.n_param
    if max_shift_i >= J.n_cols-spc:
      if r.thickness is not None and r.thickness.grad_index == max_shift_i:
        self.max_shift_for = "EDT"
      elif r.fc_correction and r.fc_correction.grad and\
           max_shift_i >= r.fc_correction.grad_index and\
           max_shift_i < r.fc_correction.grad_index + r.fc_correction.n_param:
        self.max_shift_for = "EXTI/SWAT"
      else:
        self.max_shift_for = "BASF%s" %(max_shift_i - (J.n_cols - spc) + 1)
    else:
      for e in J.col(max_shift_i):
        self.max_shift_for = r.component_annotations[e[0]]
        break
    #self.shifts_over_su = J * self.ls_shifts_over_su
    #self.max_shift_over_su = flex.max(self.shifts_over_su)
    if abs(self.max_ls_shift_over_su) < self.convergence_as_shift_over_esd:
      return True
    if limit_shift_over_su is not None and abs(self.max_ls_shift_over_su) > limit_shift_over_su:
      shift_scale = limit_shift_over_su/self.max_ls_shift_over_su
      x *= abs(shift_scale)
    return False

  def reset_shifts(self):
    self.max_ls_shift_over_su = None
    self.max_shift_for = None

  def on_cycle_completion(self, iteration, n_iterations):
    for l in iterations_with_shift_analysis.iteration_listeners:
      l(iteration, n_iterations)

class naive_iterations_with_damping_and_shift_limit(
    normal_eqns_solving.naive_iterations_with_damping,
    iterations_with_shift_analysis):
  max_shift_over_esd = 15

  def do(self):
    self.n_iterations = 0
    timer = OV.IsDebugging()
    start_t = time.time()
    while self.n_iterations < self.n_max_iterations:
      t1 = time.time()
      self.reset_shifts()
      self.non_linear_ls.actual.xray_structure.wavelength = self.parent.wavelength
      self.non_linear_ls.build_up()
      t2 = time.time()
      if self.has_gradient_converged_to_zero(): break
      self.do_damping(self.damping_value)
      self.non_linear_ls.solve()
      if self.had_too_small_a_step() or self.analyse_shifts(self.max_shift_over_esd):
        break
      self.non_linear_ls.step_forward()
      if timer:
        print("-- " + "{:10.5f}".format(t2-t1) + " for reset+build_up")
        print("-- " + "{:10.5f}".format(time.time()-t2) + " for damping+ls_solve+step_forward")
      self.on_cycle_completion(self.n_iterations, self.n_max_iterations)
      self.n_iterations += 1
    self.non_linear_ls.on_completion()
    if timer:
      print("Timing for building-up: %.3fs, iterations: %.3fs" %(
        self.non_linear_ls.normal_equations_building_time, time.time()-start_t))

  def __str__(self):
    return "Gauss-Newton with damping and shift scaling"


from smtbx.refinement import cgls, minimisers


class cgls_iterations(iterations_with_shift_analysis, cgls.cgls_iterations):
  """ Refine by conjugate gradient least squares.

  A cycle is one linearisation followed by conjugate gradients on it, so it
  counts as a refinement cycle in the same sense a Gauss-Newton cycle does, and
  the two are directly comparable. The normal matrix is never formed; the
  design matrix is, which is what limits this to structures of up to a thousand
  parameters or so, beyond which Gauss-Newton is faster again.
  """

  def begin_cycle(self):
    self.non_linear_ls.actual.begin_cycle()

  def end_cycle(self):
    self.reset_shifts()
    self.non_linear_ls.actual.end_cycle()
    self.on_cycle_completion(self.n_iterations, self.n_max_iterations)

  def had_small_enough_shifts(self, step, ls):
    """ Converged on the same criterion Gauss-Newton uses here.

    The base class compares the step against the size of the parameter vector,
    having no s.u. to hand. Olex2 does have an estimate of them by this point,
    end_cycle having just worked the shift/su out for the table, so the same
    threshold as every other solver in this file can be applied and the methods
    stay comparable. It is an estimate from the block diagonal and so errs
    towards saying not-yet-converged, which is the right way to err.
    """
    if self.max_ls_shift_over_su is None:
      return cgls.cgls_iterations.had_small_enough_shifts(self, step, ls)
    return abs(self.max_ls_shift_over_su) < self.convergence_as_shift_over_esd

  # SHELXL's DAMP, second argument, and the same default the Gauss-Newton path
  # here uses. Olex2 reads both from the .ins file and hands them over.
  max_shift_over_esd = 15

  def scale_shifts(self, step, problem, ls):
    """ Hold the largest shift/su to max_shift_over_esd, as DAMP asks.

    The s.u. are the block diagonal estimate the shift/su column of the table
    already rests on. They understate the true ones, correlations between atoms
    being ignored, so this errs towards limiting a step which did not need it,
    which is the safe direction for a damping instruction.
    """
    if not self.max_shift_over_esd:
      return step
    su = self.standard_uncertainties()
    if su is None or su.size() != step.size():
      return step
    shifts_over_su = step/su
    largest = flex.max(flex.abs(shifts_over_su))
    if largest > self.max_shift_over_esd:
      step = step*(self.max_shift_over_esd/largest)
    return step

  def shifts_to_analyse(self):
    """ The shifts this cycle applied, which conjugate gradients produced
    rather than the normal equations.
    """
    if getattr(self, 'latest_step', None) is None:
      return flex.double(self.non_linear_ls.actual.n_parameters, 0)
    return self.latest_step

  def standard_uncertainties(self):
    """ Estimated from the block diagonal of the normal matrix.

    There is no covariance matrix to be had here, that being the whole point,
    so the shift/su column of a CGLS cycle rests on the preconditioner's
    blocks: each atom's own parameters against each other, and the correlations
    between atoms ignored. That understates the s.u. and so overstates
    shift/su, which is the safe direction for something being read as a
    convergence indicator. The values which reach the CIF are not these: the
    run ends with an ordinary build and solve, and refinement.py takes them
    from that.
    """
    problem = getattr(self, 'latest_problem', None)
    if problem is None:
      return iterations_with_shift_analysis.standard_uncertainties(self)
    variances = flex.double(problem.n_parameters, 0)
    for indices, inverse in self.latest_preconditioner:
      for j, i in enumerate(indices):
        variances[int(i)] = inverse[j, j]
    variances /= problem.sum_w_yo_sq
    variances *= self.non_linear_ls.actual.restrained_goof()**2
    variances.set_selected(variances <= 0, 1e-30)
    return flex.sqrt(variances)

  def __str__(self):
    # which of the three ways the system was held is not a detail: it decides
    # how much memory the run wanted and how it spent its time, and auto may
    # have chosen differently from one structure to the next
    described = {'stored': 'stored design matrix',
                 'normal_matrix': 'normal matrix',
                 'matrix_free': 'recomputed design matrix'}
    mode = getattr(self, 'chosen_mode', None)
    if mode is None:
      return "conjugate gradient least squares"
    return ("conjugate gradient least squares, %s"
            % described.get(mode, mode))


class scipy_iterations(iterations_with_shift_analysis,
                       minimisers.crystallographic_scipy_iterations):
  """ Refine with one of the minimisers of scipy.optimize.

  Unlike Gauss-Newton and Levenberg-Marquardt, these move the structure several
  times per iteration -- a line search or a trust region tries points and
  discards most of them -- so a cycle here is one iteration of the minimiser
  and not one move of the structure. Olex2 is fed, and a row printed, once per
  cycle; the number of objective evaluations that took is reported alongside,
  each of them costing about what one Gauss-Newton cycle costs.
  """

  # Working out shift/su every cycle would about double what a cycle costs: it
  # solves the normal equations, and because solving consumes the normal matrix
  # the next evaluation has to build them again, which is as much again as the
  # evaluation itself. The s.u. barely move from one cycle to the next, so they
  # are recomputed only every so often and reused in between. The shifts
  # themselves stay exact; only the scale they are measured against is allowed
  # to age, and the value which reaches the CIF is the one from the cycle where
  # the refinement has settled anyway.
  su_refresh_interval = 5

  def do(self):
    self.p_cycle_start = None
    self.cached_su = None
    self.cached_su_cycle = 0
    self.non_linear_ls.actual.begin_cycle()
    minimisers.crystallographic_scipy_iterations.do(self)

  def standard_uncertainties(self):
    if (self.cached_su is None
        or self.n_iterations - self.cached_su_cycle
           >= self.su_refresh_interval):
      self.cached_su = \
        iterations_with_shift_analysis.standard_uncertainties(self)
      self.cached_su_cycle = self.n_iterations
      # solving for them has taken the normal matrix away
      self.invalidate_evaluation()
    return self.cached_su

  def shifts_to_analyse(self):
    """ The shifts applied since the cycle began, in units of the parameters.

    There is no step from the normal equations to report here, the minimiser
    having chosen where to go by itself.
    """
    if getattr(self, 'p_cycle_start', None) is None:
      # No cycle has completed. Either this is an L.S. 0, where the refinement
      # wrapper has built and solved the normal equations without ever calling
      # do(), and the step they give is what would be reported for
      # Gauss-Newton too; or the run stopped before its first cycle was over,
      # and nothing was applied at all.
      if self.non_linear_ls.step_equations().solved:
        return iterations_with_shift_analysis.shifts_to_analyse(self)
      return flex.double(self.non_linear_ls.opposite_of_gradient().size(), 0)
    shifts = self.p_model - self.p_cycle_start
    if self.parameter_scale is not None:
      shifts /= self.parameter_scale
    return shifts

  def on_iteration_completion(self):
    # What gets reported and handed back to Olex2 must be the point the
    # minimiser accepted, not whichever trial point it last happened to try.
    # This usually costs nothing, the two being the same point.
    self.build_at(self.p_accepted)
    normal_eqns = self.non_linear_ls.actual
    # end_cycle reports the cycle, which may or may not solve the normal
    # equations for fresh s.u.; standard_uncertainties invalidates the
    # evaluation itself on the cycles where it does
    normal_eqns.end_cycle()
    self.reset_shifts()
    self.p_cycle_start = self.p_model.deep_copy()
    normal_eqns.begin_cycle()
    self.on_cycle_completion(self.n_iterations, self.n_max_iterations)

  def __str__(self):
    return "%s via scipy.optimize.minimize" % self.method


class levenberg_marquardt_iterations(iterations_with_shift_analysis):
  tau = 1e-3

  @property
  def mu(self):
    return self._mu

  @mu.setter
  def mu(self, value):
    self.mu_history.append(value)
    self._mu = value

  def do_naive(self):
    normal_eqns_solving.naive_iterations_with_damping_and_shift_limit.do(self)
    self.non_linear_ls.build_up()

  def do(self):
    self.mu_history = flex.double()
    self.non_linear_ls.build_up()
    if self.has_gradient_converged_to_zero() or self.n_max_iterations == 0:
      return
    start_t = time.time()
    self.n_iterations = 0
    nu = 2
    a = self.non_linear_ls.normal_matrix_packed_u()
    self.mu = self.tau*flex.max(a.matrix_packed_u_diagonal())
    while self.n_iterations < self.n_max_iterations:
      self.reset_shifts()
      a.matrix_packed_u_diagonal_add_in_place(self.mu)
      objective = self.non_linear_ls.objective()
      g = -self.non_linear_ls.opposite_of_gradient()
      self.non_linear_ls.solve()
      if self.had_too_small_a_step() or self.analyse_shifts(15):
        break
      h = self.non_linear_ls.step()
      expected_decrease = 0.5*h.dot(self.mu*h - g)
      self.non_linear_ls.step_forward()
      self.on_cycle_completion(self.n_iterations, self.n_max_iterations)
      self.n_iterations += 1
      self.non_linear_ls.build_up(objective_only=True)
      objective_new = self.non_linear_ls.objective()
      actual_decrease = objective - objective_new
      rho = actual_decrease/expected_decrease
      if rho > 0:
        if self.has_gradient_converged_to_zero(): break
        self.mu *= max(1/3, 1 - (2*rho - 1)**3)
        nu = 2
        if OV.IsDebugging():
          print("Updating mu to %.3e and applying shifts" %self.mu)
      else:
        if self.mu < 1e16:
          self.non_linear_ls.step_backward()
          self.mu *= nu
          nu *= 2
          if OV.IsDebugging():
            print("Increasing mu to %.3e and recalculating" % self.mu)
          else:
            print("Refinement did not improve, no shifts applied!")
        elif OV.IsDebugging():
          print("Mu is too big, skip increase")
      self.non_linear_ls.build_up()
    # get proper s.u.
    self.non_linear_ls.build_up()
    self.non_linear_ls.on_completion()
    if OV.IsDebugging():
      print("Timing for building-up: %.3fs, iterations: %.3fs" %(
        self.non_linear_ls.normal_equations_building_time, time.time()-start_t))

  def __str__(self):
    return "Levenberg-Marquardt"

