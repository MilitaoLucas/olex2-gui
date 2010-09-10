# cctbx_controller.py

from my_refine_util import *
import math
import sys
import scitbx.lbfgs
from cctbx import miller
from smtbx.refinement import minimization
from cctbx import uctbx
from iotbx.shelx import builders
from smtbx.refinement.minimization import lbfgs
from cctbx.eltbx import sasaki
from cctbx import adptbx
from cctbx.array_family import flex
from cctbx import xray


def reflection_statistics(unit_cell, space_group, hkl):
  import iotbx.command_line.reflection_statistics
  iotbx.command_line.reflection_statistics.run([ ("--unit-cell=" + "%f "*6) % unit_cell,
                                                 "--space-group=%s" % space_group,
                                                 "hklf4=%s.hkl" % hkl ])

def twin_laws(reflections):
  import iotbx.command_line.reflection_statistics
  a = iotbx.command_line.reflection_statistics.array_cache(reflections.f_obs, 10, 3)
  twin_laws = a.possible_twin_laws()
  return twin_laws

def test_i_over_sigma_and_completeness(reflections, n_bins=20):
  from mmtbx.scaling.data_statistics import i_over_sigma_and_completeness
  data = i_over_sigma_and_completeness(reflections.f_obs)
  data.show()

def test_statistics(reflections):
  import iotbx.command_line.reflection_statistics
  a = iotbx.command_line.reflection_statistics.array_cache(reflections.f_obs, 10, 3)
  a.show_completeness()


class hemihedral_twinning(object):
  def __init__(self, twin_law, miller_set):
    self.twin_law=twin_law
    twin_completion = xray.twin_completion(
      miller_set.indices(),
      miller_set.space_group(),
      miller_set.anomalous_flag(),
      self.twin_law)
    self.twin_complete_set = miller.set(
      crystal_symmetry=miller_set.crystal_symmetry(),
      indices=twin_completion.twin_complete(),
      anomalous_flag=miller_set.anomalous_flag()).map_to_asu()

  def twin_with_twin_fraction(self, f_sq, twin_fraction):
    detwinner = xray.hemihedral_detwinner(
      hkl_obs=f_sq.indices(),
      hkl_calc=self.twin_complete_set.indices(),
      space_group=f_sq.space_group(),
      anomalous_flag=f_sq.anomalous_flag(),
      twin_law=self.twin_law)
    sigmas = f_sq.sigmas()
    if sigmas is None: sigmas = flex.double()
    twinned_i, twinned_s = detwinner.twin_with_twin_fraction(
      f_sq.data(),
      sigmas,
      twin_fraction=twin_fraction)
    if sigmas is not None: sigmas = twinned_s
    return f_sq.customized_copy(data=twinned_i, sigmas=sigmas)

class reflections(object):
  def __init__(self,  cell, spacegroup, reflection_file, hklf_matrix=None):
    """ reflections is the filename holding the reflections """
    cs = crystal.symmetry(cell, spacegroup)
    reflections_server = reflection_file_utils.reflection_file_server(
      crystal_symmetry = cs,
      reflection_files = [
        reflection_file_reader.any_reflection_file(
          'hklf4=%s' %reflection_file, strict=False)
      ]
    )
    self.crystal_symmetry = cs
    miller_arrays = reflections_server.get_miller_arrays(None)
    self.f_sq_obs = miller_arrays[0]
    if hklf_matrix is not None and not hklf_matrix.is_unit_mx():
      cb_op = sgtbx.change_of_basis_op(hklf_matrix).inverse()
      self.f_sq_obs = self.f_sq_obs.change_basis(cb_op).customized_copy(
        crystal_symmetry=cs)
    self.f_obs = self.f_sq_obs.f_sq_as_f()
    if len(miller_arrays) > 1:
      self.batch_numbers = miller_arrays[1]
    else:
      self.batch_numbers = None
    self._omit = None
    self._merge = None
    self.merging = None
    self.hklf_matrix = hklf_matrix
    self.f_sq_obs_merged = None
    self.f_sq_obs_filtered = None

  def merge(self, observations=None, merge=None):
    if merge is None:
      merge = 2
    self._merge = merge
    if observations is None:
      obs = self.f_sq_obs
    else:
      obs = observations
    obs_merged = obs.eliminate_sys_absent()
    self.n_sys_absent = obs.size() - obs_merged.size()
    if merge > 2:
      obs_merged = obs_merged.customized_copy(anomalous_flag=False)
    merging = obs_merged.merge_equivalents()
    obs_merged = merging.array()
    if observations is None:
      self.merging = merging
      self.f_sq_obs_merged = obs_merged
    else:
      return merging

  def filter(self, omit, wavelength):
    self._omit = omit
    two_theta = omit['2theta']
    self.d_min=uctbx.two_theta_as_d(two_theta, wavelength, deg=True)
    s = omit['s']
    hkl = omit.get('hkl')
    f_sq_obs_filtered = self.f_sq_obs_merged.resolution_filter(d_min=self.d_min)
    self.n_filtered_by_resolution = self.f_sq_obs_merged.size() - f_sq_obs_filtered.size()
    if hkl is not None:
      f_sq_obs_filtered = f_sq_obs_filtered.select_indices(
        indices=flex.miller_index(hkl), map_indices_to_asu=True, negate=True)
    self.f_sq_obs_filtered = f_sq_obs_filtered

  def show_summary(self, log=None):
    if log is None:
      log = sys.stdout
    if self._merge is None:
      self.merge()
    print >> log, "Merging summary:"
    print >> log, "Total reflections: %i" %self.f_sq_obs.size()
    print >> log, "Unique reflections: %i" %self.f_sq_obs_merged.size()
    print >> log, "Systematic Absences: %i removed" %self.n_sys_absent
    print >> log, "R(int): %f" %self.merging.r_int()
    print >> log, "R(sigma): %f" %self.merging.r_sigma()
    self.merging.show_summary(out=log)
    if self.f_sq_obs_filtered is not None:
      print >> log, "d min: %f" %self.d_min
      print >> log, "n reflections filtered by resolution: %i" %(self.n_filtered_by_resolution)
      print >> log, "n reflections filtered by hkl: %i" %(
        self.f_sq_obs_merged.size() - self.n_filtered_by_resolution - self.f_sq_obs_filtered.size())

def create_cctbx_xray_structure(cell, spacegroup, atom_iter, restraint_iterator=None):
  """ cell is a 6-uple, spacegroup a string and atom_iter yields tuples (label, xyz, u, element_type) """
  builder = builders.crystal_structure_builder()
  unit_cell = uctbx.unit_cell(cell)
  builder.make_crystal_symmetry(cell, spacegroup)
  builder.make_structure()
  u_star = shelx_adp_converter(builder.crystal_symmetry)
  for label, site, occupancy, u, scattering_type, fixed_vars in atom_iter:
    behaviour_of_variable = [0]*12
    if fixed_vars is not None:
      for var in fixed_vars:
        behaviour_of_variable[var['index']] = 1
    if len(u) != 1:
      a = xray.scatterer(label=label,
                         site=site,
                         u=u_star(*u),
                         occupancy=occupancy,
                         scattering_type=scattering_type)
      behaviour_of_variable.pop(5)
      #behaviour_of_variable = [0,0,0,1,0,0,0,0,0]
    else:
      a = xray.scatterer(label=label,
                         site=site,
                         u=u[0],
                         occupancy=occupancy,
                         scattering_type=scattering_type)
      #behaviour_of_variable = [0,0,0,1,0]
      behaviour_of_variable = behaviour_of_variable[:6]
    behaviour_of_variable.pop(0)
    builder.add_scatterer(a, behaviour_of_variable)
  return builder.structure


class manager(object):
  def __init__(self,
               f_obs=None,
               f_sq_obs=None,
               xray_structure=None,
               restraints_manager=None,
               geometry_restraints_flags=None,
               adp_restraints_flags=None,
               lambda_=None,
               max_sites_pre_cycles=20,
               max_cycles=40,
               max_peaks=30,
               weighting=None,
               verbose=1,
               log=None):
    assert [f_obs,f_sq_obs].count(None) == 1
    assert lambda_ is not None
    assert xray_structure is not None
    if f_obs:
      self.refinement_type = xray.amplitude
      f_obs.set_observation_type_xray_amplitude()
      self.f_obs = f_obs
      self.f_sq_obs = f_obs.f_as_f_sq()
    else:
      self.refinement_type = xray.intensity
      f_sq_obs.set_observation_type_xray_intensity()
      self.f_sq_obs = f_sq_obs
      self.f_obs = f_sq_obs.f_sq_as_f()
    assert self.f_sq_obs.is_real_array()
    self.xray_structure = xray_structure
    self.xs_0 = xray_structure
    self.restraints_manager = restraints_manager
    self.geometry_restraints_flags = geometry_restraints_flags
    self.adp_restraints_flags = adp_restraints_flags
    self.max_sites_pre_cycles = max_sites_pre_cycles
    self.max_cycles = max_cycles
    self.max_peaks = max_peaks
    self.verbose = verbose
    self.log = log
    self.minimisation = None
    self.weighting = weighting

    for sc in self.xray_structure.scatterers():
      if sc.scattering_type in ('H','D'):continue
      fp_fdp = sasaki.table(sc.scattering_type).at_angstrom(lambda_)
      sc.fp = fp_fdp.fp()
      sc.fdp = fp_fdp.fdp()

  def start(self):
    """ Start the refinement """
    self.filter_reflections()
    #self.xs0 = self.xs
    self.set_refinement_flags()
    self.setup_refinement()
    self.start_refinement()

  def filter_reflections(self):
    f_sq_obs = self.f_sq_obs
    for i in xrange(f_sq_obs.size()):
      if f_sq_obs.data()[i] < -f_sq_obs.sigmas()[i]:
        f_sq_obs.data()[i] = -f_sq_obs.sigmas()[i]
    f_obs = f_sq_obs.f_sq_as_f()
    self.f_sq_obs = f_sq_obs
    self.f_obs = f_obs

  def set_refinement_flags(self,
                           state=False,
                           grad_u_iso_iselection=None,
                           grad_u_aniso_iselection=None,
                           grad_sites_iselection=None):
    scatterers = self.xray_structure.scatterers()
    scatterers.flags_set_grads(state=state)
    if not state:
      if grad_u_iso_iselection is None:
        grad_u_iso_iselection = scatterers.extract_use_u_iso().iselection()
      if grad_u_aniso_iselection is None:
        grad_u_aniso_iselection = scatterers.extract_use_u_aniso().iselection()
      if grad_sites_iselection is None:
        grad_sites_iselection = flex.bool(self.xray_structure.scatterers().size(), True).iselection()
      scatterers.flags_set_grad_u_iso(grad_u_iso_iselection)
      scatterers.flags_set_grad_u_aniso(grad_u_aniso_iselection)
      scatterers.flags_set_grad_site(grad_sites_iselection)

  def setup_refinement(self):
    if self.refinement_type is xray.intensity:
      ls = xray.unified_least_squares_residual(self.f_sq_obs,
                                               weighting=self.weighting)
    else:
      ls = xray.unified_least_squares_residual(self.f_obs)
    self.ls = ls

  def start_refinement(self):
    minimisation = my_lbfgs(
      delegate=lambda minimisation, minimiser: self.on_cycle_finished(self.xray_structure, minimisation, minimiser),
      target_functor=self.ls,
      xray_structure=self.xray_structure,
      #restraints_manager=self.restraints_manager,
      #geometry_restraints_flags=self.geometry_restraints_flags,
      #adp_restraints_flags=self.adp_restraints_flags,
      cos_sin_table=True,
      lbfgs_sites_pre_minimisation_termination_params=scitbx.lbfgs.termination_parameters(
        max_iterations=self.max_sites_pre_cycles),
      lbfgs_termination_params = scitbx.lbfgs.termination_parameters(
        max_iterations=self.max_cycles),
      verbose=self.verbose,
      log=self.log,
    )
    self.minimisation = minimisation

  def on_cycle_finished(self, xs, minimisation, minimiser):
    """ called after each iteration of the given minimiser, xs being
    the refined structure. """
    self.show_cycle_summary(minimiser)

  def show_cycle_summary(self, minimizer):
    if self.verbose:
      print "Refinement Cycle: %i" %(minimizer.iter())
      print "wR2 = %.4f and GooF = %.4f for" %self.wR2_and_GooF(minimizer),
      print "%i parameters" %minimizer.n()

  def show_final_summary(self):
    """ only to be called after minimisation has finished. """
    assert self.minimisation is not None
    if self.verbose:
      print "R1 = %.4f for %i Fo > 4sig(Fo)" %self.R1(),
      print "and %.4f for all %i data" %(self.R1(all_data=True))
      print "wR2 = %.4f and " \
            "GooF = %.4f for" %self.wR2_and_GooF(self.minimisation.minimizer),
      print "%i parameters" %self.minimisation.minimizer.n()

  def iter_scatterers(self):
    """ an iterator over tuples (label, xyz, u, u_eq, symbol) """
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
        u_eq = adptbx.u_star_as_u_iso(self.xray_structure.unit_cell(), a.u_star)
      yield label, xyz, u, u_eq, symbol

  def calculate_residuals(self, f_obs):
    sf = xray.structure_factors.from_scatterers(
      miller_set=f_obs,
      cos_sin_table=True
    )
    f_calc = sf(self.xray_structure, f_obs).f_calc()
    ls_function = xray.unified_least_squares_residual(f_obs)
    ls = ls_function(f_calc, compute_derivatives=False)
    k = ls.scale_factor()
    fc = flex.abs(f_calc.data())
    fo = flex.abs(f_obs.data())
    return flex.abs(k*fc - fo)

  def R1(self, all_data=False):
    f_obs = self.f_obs
    if not all_data:
      strong = f_obs.data() > 4*f_obs.sigmas()
      f_obs = f_obs.select(strong)
    R1 = flex.sum(self.calculate_residuals(f_obs)) / flex.sum(f_obs.data())
    return R1, f_obs.size()

  def wR2_and_GooF(self, minimizer):
    f_sq_obs = self.f_sq_obs
    sf = xray.structure_factors.from_scatterers(
      miller_set=f_sq_obs,
      cos_sin_table=True
    )
    f_calc = sf(self.xray_structure, f_sq_obs).f_calc()
    ls_function = xray.unified_least_squares_residual(
      f_sq_obs,
      weighting=self.weighting
    )
    ls = ls_function(f_calc, compute_derivatives=False)
    weights = ls_function.weighting().weights
    k = ls.scale_factor()
    f_sq_calc = f_calc.norm()
    fc_sq = f_sq_calc.data()
    fo_sq = f_sq_obs.data()
    wR2 = math.sqrt(flex.sum(weights * flex.pow2(fo_sq - k * fc_sq)) /
                    flex.sum(weights * flex.pow2(fo_sq)))
    GooF = math.sqrt(flex.sum(weights * flex.pow2(fo_sq - k * fc_sq)) /
                     (fo_sq.size() - minimizer.n()))
    return wR2, GooF

class my_lbfgs(lbfgs):
  def __init__(self, delegate, **kwds):
    #self.callback_after_step = delegate
    self.delegate = delegate
    super(my_lbfgs, self).__init__(**kwds)

  def callback_after_step(self, minimser):
    self.delegate(self, minimser)


class refinement(manager):
  def __init__(self,
               f_obs=None,
               f_sq_obs=None,
               xray_structure=None,
               wavelength=None,
               max_sites_pre_cycles=20,
               max_cycles=40,
               max_peaks=30,
               weighting=None,
               verbose=1,
               log=None):
    manager.__init__(self,
                     f_obs=f_obs,
                     f_sq_obs=f_sq_obs,
                     xray_structure=xray_structure,
                     lambda_=wavelength,
                     max_cycles=max_cycles,
                     max_peaks=max_peaks,
                     weighting=weighting,
                     verbose=verbose,
                     log=log)

  def f_obs_minus_f_calc_map(self, resolution):
    f_obs=self.f_obs
    f_sq_obs = self.f_sq_obs
    f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
    f_obs = f_sq_obs.f_sq_as_f()
    sf = xray.structure_factors.from_scatterers(
      miller_set=f_obs,
      cos_sin_table=True
    )
    f_calc = sf(self.xray_structure, f_obs).f_calc()
    #fc2 = flex.norm(f_calc.data())
    #fo2 = f_sq_obs.data()
    #wfo2 = 1./flex.pow2(f_sq_obs.sigmas())
    #K2 = flex.mean_weighted(fo2*fc2, wfo2)/flex.mean_weighted(fc2*fc2, wfo2)
    #K2 = math.sqrt(K2)
    #f_obs_minus_f_calc = f_obs.f_obs_minus_f_calc(1./K2, f_calc)
    k = f_obs.scale_factor(f_calc)
    f_obs_minus_f_calc = f_obs.f_obs_minus_f_calc(1./k, f_calc)
    return f_obs_minus_f_calc.fft_map(
      symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
      resolution_factor=resolution,
    )

  #def peak_search(self):
    #sf = xray.structure_factors.from_scatterers(
      #miller_set=self.f_obs,
      #cos_sin_table=True
    #)
    #f_calc = sf(self.xray_structure, self.f_obs).f_calc()
    #f_o_minus_f_c = self.f_obs.f_obs_minus_f_calc(
      #f_obs_factor=1/self.minimisation.target_result.scale_factor(),
      #f_calc=f_calc)
    #fft_map = f_o_minus_f_c.fft_map(
      #symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=True))
    #if 0: ##display map
      #from crys3d import wx_map_viewer
      #wx_map_viewer.display(title=structure_label,
                            #fft_map=fft_map)
    #search_parameters = maptbx.peak_search_parameters(
      #peak_search_level=3,
      #interpolate=True,
      #min_distance_sym_equiv=1.,
      #max_clusters=5)
    #return fft_map.peak_search(search_parameters).all()
