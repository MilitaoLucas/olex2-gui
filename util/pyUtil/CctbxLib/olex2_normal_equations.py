from __future__ import division
import sys

from scitbx.array_family import flex
from smtbx.refinement import least_squares
from smtbx.structure_factors import direct
from cctbx import adptbx

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import olx
import olex
import olex_core

class normal_eqns(least_squares.crystallographic_ls_class()):
  log = None

  def __init__(self, observations, reparametrisation, olx_atoms,
               table_file_name=None, **kwds):
    super(normal_eqns, self).__init__(
      observations, reparametrisation, initial_scale_factor=OV.GetOSF(),
       **kwds)
    if table_file_name:
      self.one_h_linearisation = direct.f_calc_modulus_squared(
        self.xray_structure, table_file_name=table_file_name)
    else:
      self.one_h_linearisation = direct.f_calc_modulus_squared(
        self.xray_structure, reflections=self.observations)

    self.olx_atoms = olx_atoms
    self.n_current_cycle = 0
    self.shifts_over_su = None

  def step_forward(self):
    try:
      a = self.cycles.shifts_over_su
    except:
      self.shifts_over_su = None
    self.n_current_cycle += 1
    self.xray_structure_pre_cycle = self.xray_structure.deep_copy_scatterers()
    super(normal_eqns, self).step_forward()
    self.show_cycle_summary(log=self.log)
    self.show_sorted_shifts(max_items=10, log=self.log)
    self.restraints_manager.show_sorted(
      self.xray_structure, f=self.log)
    self.show_cycle_summary()
    self.feed_olex()
    return self

  def step_backward(self):
    super(normal_eqns, self).step_backward()
    return self

  #compatibility...
  def get_shifts(self):
    try:
      return self.cycles.shifts_over_su
    except:
      if not self.shifts_over_su:
        shifts_over_su = flex.abs(self.step() /
          flex.sqrt(self.covariance_matrix().matrix_packed_u_diagonal()))
        jac_tr = self.reparametrisation.jacobian_transpose_matching_grad_fc()
        self.shifts_over_su = jac_tr.transpose() * shifts_over_su
    return self.shifts_over_su

  def show_cycle_summary(self, log=None):
    if log is None: log = sys.stdout
    # self.reparametrisation.n_independents + OSF
    max_shift_site = self.max_shift_site()
    OV.SetParam('snum.refinement.max_shift_site', max_shift_site[0])
    OV.SetParam('snum.refinement.max_shift_site_atom', max_shift_site[1].label)
    max_shift_u = self.max_shift_u()
    OV.SetParam('snum.refinement.max_shift_u', max_shift_u[0])
    OV.SetParam('snum.refinement.max_shift_u_atom', max_shift_u[1].label)

    shifts = self.get_shifts()
    max_shift_esd = 0
    max_shift_esd_item = "n/a"
    self.max_shift_esd = None
    self.max_shift_esd_item = None
    try:
      max_shift_idx = 0
      for i, s in enumerate(shifts):
        if (shifts[max_shift_idx] < s):
          max_shift_idx = i
      max_shift_esd = shifts[max_shift_idx]
      max_shift_esd_item = self.reparametrisation.component_annotations[max_shift_idx]
      self.max_shift_esd = max_shift_esd
      self.max_shift_esd_item = max_shift_esd_item

    except Exception as s:
      print s

    print_tabular = True

    if print_tabular:
      print >>log, "  % 5i    % 6.2f    % 6.2f    % 6.2f    % 8.2f %-11s  % 8.2e %-11s  % 8.2e %-11s" %(
        self.n_current_cycle,
        self.r1_factor(cutoff_factor=2)[0]*100,
        self.wR2()*100,
        self.goof(),
        max_shift_esd,
        '('+max_shift_esd_item+')',
        max_shift_site[0],
        '('+max_shift_site[1].label+')',
        max_shift_u[0],
        '('+max_shift_u[1].label+')',
      )

    else:
      print >> log, "wR2 = %.4f | GooF = %.4f for %i data and %i parameters" %(
        self.wR2(),
        self.goof(),
        self.observations.fo_sq.size(),
        self.reparametrisation.n_independents + 1,
      )

      print >> log, "Max shifts: ",

      print >> log, "Site: %.4f A for %s |" %(
        max_shift_site[0],
        max_shift_site[1].label
      ),
      print >> log, "dU = %.4f for %s" %(
        max_shift_u[0],
        max_shift_u[1].label,
      )


  def max_shift_site(self):
    return self.iter_shifts_sites(max_items=1).next()

  def max_shift_u(self):
    return self.iter_shifts_u(max_items=1).next()

  def max_shift_esd(self):
    self.get_shifts()
    return self.iter_shifts_u(max_items=1).next()


  def iter_shifts_sites(self, max_items=None):
    scatterers = self.xray_structure.scatterers()
    sites_shifts = self.xray_structure.sites_cart() -\
                 self.xray_structure_pre_cycle.sites_cart()
    distances = sites_shifts.norms()
    i_distances_sorted = flex.sort_permutation(data=distances, reverse=True)
    mean = flex.mean(distances)
    if max_items is not None:
      i_distances_sorted = i_distances_sorted[:max_items]
    for i_seq in iter(i_distances_sorted):
      yield distances[i_seq], scatterers[i_seq]

  def iter_shifts_u(self, max_items=None):
    scatterers = self.xray_structure.scatterers()
    adp_shifts = self.xray_structure.extract_u_cart_plus_u_iso() \
               - self.xray_structure_pre_cycle.extract_u_cart_plus_u_iso()
    norms = adp_shifts.norms()
    mean = flex.mean(norms)
    i_adp_shifts_sorted = flex.sort_permutation(data=norms, reverse=True)
    if max_items is not None:
      i_adp_shifts_sorted = i_adp_shifts_sorted[:max_items]
    for i_seq in iter(i_adp_shifts_sorted):
      yield norms[i_seq], scatterers[i_seq]

  def show_log(self, f=None):
    import sys
    if self.log is sys.stdout: return
    if f is None: f = sys.stdout
    print >> f, self.log.getvalue()

  def show_sorted_shifts(self, max_items=None, log=None):
    import sys
    if log is None: log = sys.stdout
    print >> log, "Sorted site shifts in Angstrom:"
    print >> log, "shift scatterer"
    n_not_shown = self.xray_structure.scatterers().size()
    for distance, scatterer in self.iter_shifts_sites(max_items=max_items):
      n_not_shown -= 1
      print >> log, "%5.3f %s" %(distance, scatterer.label)
      if round(distance, 3) == 0: break
    if n_not_shown != 0:
      print >> log, "... (remaining %d not shown)" % n_not_shown
    #
    print >> log, "Sorted adp shift norms:"
    print >> log, "dU scatterer"
    n_not_shown = self.xray_structure.scatterers().size()
    for norm, scatterer in self.iter_shifts_u(max_items=max_items):
      n_not_shown -= 1
      print >> log, "%5.3f %s" %(norm, scatterer.label)
      if round(norm, 3) == 0: break
    if n_not_shown != 0:
      print >> log, "... (remaining %d not shown)" % n_not_shown

  def show_shifts(self, log=None):
    import sys
    if log is None: log = sys.stdout
    site_symmetry_table = self.xray_structure.site_symmetry_table()
    i=0
    for i_sc, sc in enumerate(self.xray_structure.scatterers()):
      op = site_symmetry_table.get(i_sc)
      print >> log, "%-4s" % sc.label
      if sc.flags.grad_site():
        n = op.site_constraints().n_independent_params()
        if n != 0:
          print >> log, ("site:" + "%7.4f, "*(n-1) + "%7.4f")\
                % tuple(self.shifts[-1][i:i+n])
        i += n
      if sc.flags.grad_u_iso() and sc.flags.use_u_iso():
        if not(sc.flags.tan_u_iso() and sc.flags.param > 0):
          print >> log, "u_iso: %6.4f" % self.shifts[i]
          i += 1
      if sc.flags.grad_u_aniso() and sc.flags.use_u_aniso():
        n = op.adp_constraints().n_independent_params()
        print >> log, (("u_aniso:" + "%6.3f, "*(n-1) + "%6.3f")
                       % tuple(self.shifts[-1][i:i+n]))
        i += n
      if sc.flags.grad_occupancy():
        print >> log, "occ: %4.2f" % self.shifts[-1][i]
        i += 1
      if sc.flags.grad_fp():
        print >> log, "f': %6.4f" % self.shifts[-1][i]
        i += 1
      if sc.flags.grad_fdp():
        print >> log, "f'': %6.4f" % self.shifts[-1][i]
        i += 1
      print >> log

  def feed_olex(self):
    ## Feed Model
    u_atoms = []
    i = 1

    def iter_scatterers():
      n_equiv_positions = self.xray_structure.space_group().n_equivalent_positions()
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
               a.occupancy*(a.multiplicity()/n_equiv_positions),
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
    if self.twin_fractions is not None:
      idx = 0
      for fraction in self.twin_fractions:
        if fraction.grad:
          olx.xf.rm.BASF(idx, fraction.value)
          idx += 1
    #update EXTI
    if self.reparametrisation.extinction.grad:
      OV.SetExtinction(self.reparametrisation.extinction.value)
    for (i,r) in enumerate(self.shared_rotated_adps):
      if r.refine_angle:
        olx.xf.rm.UpdateCR('olex2.constraint.rotated_adp', i, r.angle.value*180/math.pi)
    olx.xf.EndUpdate()
    if OV.HasGUI():
      olx.Refresh()
    if OV.isInterruptSet():
      raise RuntimeError('external_interrupt')


from scitbx.lstbx import normal_eqns_solving
class levenberg_marquardt_iterations(normal_eqns_solving.iterations):

  tau = 1e-3
  convergence_as_shift_over_esd = 1e-5

  @property
  def mu(self):
    return self._mu

  @mu.setter
  def mu(self, value):
    self.mu_history.append(value)
    self._mu = value

  def check_shift_over_esd(self):
    return self.do_scale_shifts(1e16)

  def do(self):
    self.mu_history = flex.double()
    self.non_linear_ls.build_up()
    if self.has_gradient_converged_to_zero():
      return
    self.n_iterations = 0
    nu = 2
    a = self.non_linear_ls.normal_matrix_packed_u()
    self.mu = self.tau*flex.max(a.matrix_packed_u_diagonal())
    while self.n_iterations < self.n_max_iterations:
      a.matrix_packed_u_diagonal_add_in_place(self.mu)
      objective = self.non_linear_ls.objective()
      g = -self.non_linear_ls.opposite_of_gradient()
      self.non_linear_ls.solve()
      self.n_iterations += 1
      h = self.non_linear_ls.step()
      expected_decrease = 0.5*h.dot(self.mu*h - g)
      if OV.GetParam('snum.NoSpherA2.make_fcf_only') == True:
        return
      self.non_linear_ls.step_forward()
      if self.check_shift_over_esd():
        # not sure why but without this esds become very small!
        self.non_linear_ls.build_up()
        break
      self.non_linear_ls.build_up(objective_only=True)
      objective_new = self.non_linear_ls.objective()
      actual_decrease = objective - objective_new
      rho = actual_decrease/expected_decrease
      if rho > 0:
        self.mu *= max(1/3, 1 - (2*rho - 1)**3)
        nu = 2
      else:
        if self.n_iterations + 1 < self.n_max_iterations:
          self.non_linear_ls.step_backward()
        self.mu *= nu
        nu *= 2
      self.non_linear_ls.build_up()

  def __str__(self):
    return "Levenberg-Marquardt"


