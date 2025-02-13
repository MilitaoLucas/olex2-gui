# cctbx_controller.py

from my_refine_util import *
import math
import sys

from iotbx import builders, reflection_file_reader, reflection_file_utils
from cctbx.eltbx import sasaki
from cctbx import adptbx, crystal, miller, sgtbx, xray, uctbx
from cctbx.array_family import flex
from cctbx import xray
from smtbx.refinement.constraints import rigid
from cctbx.xray import observations

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

  def detwin_with_twin_fraction(self, f_sq, twin_fraction):
    detwinner = xray.hemihedral_detwinner(
      hkl_obs=f_sq.indices(),
      hkl_calc=self.twin_complete_set.indices(),
      space_group=f_sq.space_group(),
      anomalous_flag=f_sq.anomalous_flag(),
      twin_law=self.twin_law)
    sigmas = f_sq.sigmas()
    if sigmas is None: sigmas = flex.double()
    detwinned_i, detwinned_s = detwinner.detwin_with_twin_fraction(
      f_sq.data(),
      sigmas,
      twin_fraction=twin_fraction)
    if sigmas is not None: sigmas = detwinned_s
    return f_sq.customized_copy(data=detwinned_i, sigmas=sigmas)

  def detwin_with_model_data(self, f_sq, f_model, twin_fraction):
    assert f_model.is_complex_array()
    detwinner = xray.hemihedral_detwinner(
      hkl_obs=f_sq.indices(),
      hkl_calc=self.twin_complete_set.indices(),
      space_group=f_sq.space_group(),
      anomalous_flag=f_sq.anomalous_flag(),
      twin_law=self.twin_law)
    sigmas = f_sq.sigmas()
    if sigmas is None: sigmas = flex.double()
    detwinned_i, detwinned_s = detwinner.detwin_with_model_data(
      f_sq.data(),
      sigmas,
      f_model.data(),
      twin_fraction=twin_fraction)
    if sigmas is not None: sigmas = detwinned_s
    return f_sq.customized_copy(data=detwinned_i, sigmas=sigmas)


class reflections(object):
  """ reflections is the filename holding the reflections """
  def __init__(self,  cell, spacegroup, reflection_file, hklf_code, hklf_matrix=None, merge_code=2):
    if merge_code != 0 or hklf_code == 5:
      cs = crystal.symmetry(cell, spacegroup)
    else:
      cs = crystal.symmetry(cell, "P1")
    #do we read amplitudes or intensisty?
    f_hklf_code = hklf_code
    if f_hklf_code != 3:
      f_hklf_code = 4
    if reflection_file:
      reflections_server = reflection_file_utils.reflection_file_server(
        crystal_symmetry = cs,
        reflection_files = [
          reflection_file_reader.any_reflection_file(
            'hklf%s=%s' %(f_hklf_code, reflection_file), strict=False)
        ]
      )
      miller_arrays = reflections_server.get_miller_arrays(None)
    else:
      import olex_core
      from cctbx.xray import observation_types as obs_t
      refs = olex_core.GetReflections()
      hklf_matrix = None
      miller_set = miller.set(
        crystal_symmetry=cs,
        indices=flex.miller_index(refs[0])).auto_anomalous()
      miller_arrays = []
      base_array_info = miller.array_info(source_type="shelx_hklf")
      miller_arrays.append(
        miller.array(
          miller_set=miller_set,
          data=flex.double(refs[1]),
          sigmas=flex.double(refs[2])))
      miller_arrays[0].set_info(base_array_info.customized_copy(labels=["obs", "sigmas"]))
      miller_arrays[0].set_observation_type(obs_t.amplitude() if hklf_code == 3 else obs_t.intensity())
      if refs[3]:
        miller_arrays.append(
          miller.array(
            miller_set=miller_set,
            data=flex.int(refs[3])))
        miller_arrays[1].set_info(base_array_info.customized_copy(labels=["batch_numbers"]))

    self.crystal_symmetry = cs
    for array in miller_arrays:
      array.info().source = reflection_file.encode("utf-8")

    if hklf_code == 3:
      self.f_obs = miller_arrays[0]
      if hklf_matrix is not None and not hklf_matrix.is_unit_mx():
        r = sgtbx.rt_mx(hklf_matrix.new_denominator(24).transpose())
        cb_op = sgtbx.change_of_basis_op(r).inverse()
        self.f_obs = self.f_obs.change_basis(cb_op).customized_copy(
          crystal_symmetry=cs)
      self.f_sq_obs = self.f_obs.f_as_f_sq()
    else:
      self.f_sq_obs = miller_arrays[0]
      if hklf_matrix is not None and not hklf_matrix.is_unit_mx():
        r = sgtbx.rt_mx(hklf_matrix.new_denominator(24).transpose())
        cb_op = sgtbx.change_of_basis_op(r).inverse()
        self.f_sq_obs = self.f_sq_obs.change_basis(cb_op).customized_copy(
          crystal_symmetry=cs)
      self.f_obs = self.f_sq_obs.f_sq_as_f()
    if len(miller_arrays) > 1:
      self.batch_numbers_array = miller_arrays[1]
    else:
      if hklf_code == 5:
        raise RuntimeError("HKLF5 file format requires batch numbers")
      self.batch_numbers_array = None
    self._omit = None
    self._shel = None
    self._merge = None
    self.merging = None
    self.hklf_matrix = hklf_matrix
    self.f_sq_obs_merged = None
    self.f_sq_obs_filtered = None
    self.hklf_code = hklf_code
    self.merge_code = merge_code
    #self.observations = self.get_observations(twin_components, twin_fractions)

  def merge(self, observations=None, merge=None):
    if observations is None:
      obs = self.f_sq_obs
    else:
      obs = observations
    if self.hklf_code == 5:
      self.merging = None
      self.f_sq_obs_merged = obs
      self._merge = 0
      return obs
    if merge is None:
      merge = 2
    self._merge = merge
    obs_merged = obs.eliminate_sys_absent()
    self.n_sys_absent = obs.size() - obs_merged.size()
    if merge > 2:
      obs_merged = obs_merged.customized_copy(anomalous_flag=False)
    merging = obs_merged.merge_equivalents(algorithm="shelx")#algorithm="default")
    obs_merged = merging.array()
    if observations is None:
      self.merging = merging
      self.f_sq_obs_merged = obs_merged
    else:
      return merging

  def filter(self, omit, shel, wavelength, doFilter=True):
    if not doFilter:
      self.f_sq_obs_filtered = self.f_sq_obs_merged
      if self.hklf_code == 5:
        self.batch_numbers = self.batch_numbers_array.data()
      return
    self._omit = omit
    self._shel = shel
    two_theta = omit['2theta']
    if shel and two_theta != 180:
      import olx
      olx.Echo("Warning - mixing SHEL and OMIT. Using low resolution limit from SHEL and high resolution from OMIT",
               m="warning")
    self.d_min=uctbx.two_theta_as_d(two_theta, wavelength, deg=True)
    hkl = omit.get('hkl')
    f_sq_obs_filtered = self.f_sq_obs_merged.treat_negative_amplitudes_shelx(omit['s'])
    if hkl is None: hkl = ()
    if self._shel is None:
      self._shel = {'high' : self.d_min, 'low': -1}
    else:
      if self._shel['high'] > self._shel['low']:
        self._shel = {'high' : self._shel['low'], 'low': self._shel['high']}
      if two_theta != 180:
        self._shel['high'] = self.d_min

    if self.hklf_code >= 5 or self.merge_code == 0:
      anomalous_flag = True
    else:
      anomalous_flag = f_sq_obs_filtered.anomalous_flag()

    filter = observations.filter(
      f_sq_obs_filtered.unit_cell(),
      f_sq_obs_filtered.crystal_symmetry().space_group(),
      anomalous_flag,
      flex.miller_index(hkl),
      float(self._shel['high']),
      float(self._shel['low']),
      omit['s']*0.5
    )
    if self.hklf_code == 5:
      batch_numbers = self.batch_numbers_array.data()
    else:
      batch_numbers = flex.int(())
    filter_res = observations.filter_data(
      f_sq_obs_filtered.indices(),
      f_sq_obs_filtered.data(),
      f_sq_obs_filtered.sigmas(),
      batch_numbers,
      filter)
    f_sq_obs_filtered = f_sq_obs_filtered.select(filter_res.selection)
    if self.hklf_code == 5:
      self.batch_numbers = self.batch_numbers_array.select(
        filter_res.selection).data()
    self.n_filtered_by_resolution = filter_res.omitted_count
    self.n_sys_absent = filter_res.sys_abs_count
    self.f_sq_obs_filtered = f_sq_obs_filtered

  def show_summary(self, log=None):
    if log is None:
      log = sys.stdout
    if self._merge is None:
      self.merge()
    print("Merging summary:", file=log)
    print("Total reflections: %i" %self.f_sq_obs.size(), file=log)
    print("Unique reflections: %i" %self.f_sq_obs_merged.size(), file=log)
    print("Systematic Absences: %i removed" %self.n_sys_absent, file=log)
    if self.merging is not None:
      print("Inconsistent equivalents: %i" %self.merging.inconsistent_equivalents(), file=log)
      print("R(int): %f" %self.merging.r_int(), file=log)
      print("R(sigma): %f" %self.merging.r_sigma(), file=log)
      self.merging.show_summary(out=log)
    if self.f_sq_obs_filtered is not None:
      print("d min: %f" %self.d_min, file=log)
      print("n reflections filtered by resolution: %i" %(self.n_filtered_by_resolution), file=log)
      print("n reflections filtered by hkl: %i" %(
        self.f_sq_obs_merged.size() - self.n_filtered_by_resolution - self.f_sq_obs_filtered.size()), file=log)

  def get_observations(self, twin_fractions, twin_components):
    miller_set = miller.set(
      crystal_symmetry=self.f_sq_obs_filtered.crystal_symmetry(),
      indices=self.f_sq_obs_filtered.indices(),
      anomalous_flag=self.f_sq_obs_filtered.anomalous_flag())\
        .unique_under_symmetry().map_to_asu()
    if self.hklf_code == 5:
      rv = self.f_sq_obs_filtered.as_xray_observations(
        scale_indices=self.batch_numbers,
        twin_fractions=twin_fractions,
        twin_components=twin_components)
      self.f_sq_obs_filtered = rv.fo_sq
      self.batch_numbers = rv.measured_scale_indices
    else:
      rv = self.f_sq_obs_filtered.as_xray_observations(
        twin_components=twin_components)
    rv.unique_mapped_miller_set = miller_set
    return rv


class create_cctbx_xray_structure(object):

  def __init__(self, cell, spacegroup, atom_iter, restraints_iter=None,
                constraints_iter=None, same_iter=None):
    """ cell is a 6-uple, spacegroup a string and atom_iter yields tuples (label, xyz, u, element_type) """
    from cctbx import anharmonic
    builder = builders.weighted_constrained_restrained_crystal_structure_builder(
      min_distance_sym_equiv=0.2)
    builder.make_crystal_symmetry(cell, spacegroup)
    builder.make_structure()
    u_star = shelx_adp_converter(builder.crystal_symmetry)
    for label, site, occupancy, u, anharmonic_u, uiso_owner, scattering_type, fixed_vars in atom_iter:
      behaviour_of_variable = [True]*12
      if fixed_vars is not None:
        for var in fixed_vars:
          behaviour_of_variable[var['index']] = False
      if len(u) != 1:
        a = xray.scatterer(label=label,
                           site=site,
                           u=u_star(*u),
                           occupancy=occupancy,
                           scattering_type=scattering_type)
        if anharmonic_u:
          if 'D' in anharmonic_u:
            a.anharmonic_adp = anharmonic.gram_charlier(anharmonic_u['C'], anharmonic_u['D'])
          else:
            a.anharmonic_adp = anharmonic.gram_charlier(anharmonic_u['C'])
        behaviour_of_variable.pop(5)
      else:
        a = xray.scatterer(label=label,
                           site=site,
                           u=u[0],
                           occupancy=occupancy,
                           scattering_type=scattering_type)
        behaviour_of_variable = behaviour_of_variable[:6]
        if uiso_owner is not None:
          behaviour_of_variable[5] = False
          #behaviour_of_variable[5] = 1 # XXX temporary fix for riding u_iso's
      behaviour_of_variable.pop(0)
      builder.add_scatterer(a, behaviour_of_variable,
                            occupancy_includes_symmetry_factor=True)
      if uiso_owner is not None:
        builder.add_u_iso_proportional_to_pivot_u_eq(
          len(builder.structure.scatterers())-1,
          uiso_owner['id'], uiso_owner['k'])
    if restraints_iter is not None:
      for restraint_type, kwds in restraints_iter:
        try:
          builder.process_restraint(restraint_type, **kwds)
        except:
          print('Your version of cctbx is too old for the restraint %s'%restraint_type)
    if same_iter is not None:
      for restraint_type, kwds in same_iter:
        builder.process_restraint(restraint_type, **kwds)
    if constraints_iter is not None:
      for constraint_type, kwds in constraints_iter:
        builder.process_constraint(constraint_type, **kwds)
    self.builder = builder

  def structure(self):
    return self.builder.structure

  def restraint_proxies(self):
    return self.builder.proxies()
