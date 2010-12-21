# cctbx_controller.py

from my_refine_util import *
import math
import sys
from cctbx import miller
from cctbx import uctbx
from iotbx import builders

from iotbx import reflection_file_reader, reflection_file_utils

from cctbx.eltbx import sasaki
from cctbx import adptbx, crystal, miller, sgtbx, xray
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
    hkl = omit.get('hkl')
    f_sq_obs_filtered = self.f_sq_obs_merged.resolution_filter(d_min=self.d_min)
    s = omit['s']
    if s < 0:
      weak_cutoff = 0.5 * s * f_sq_obs_filtered.sigmas()
      weak = f_sq_obs_filtered.data() < weak_cutoff
      f_sq_obs_filtered.data().set_selected(weak, weak_cutoff)
    elif s > 0:
      pass
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

class create_cctbx_xray_structure(object):

  def __init__(self, cell, spacegroup, atom_iter, restraints_iter=None, constraints_iter=None):
    """ cell is a 6-uple, spacegroup a string and atom_iter yields tuples (label, xyz, u, element_type) """
    import iotbx.constrained_parameters as _
    if restraints_iter is not None:
      builder = builders.weighted_constrained_restrained_crystal_structure_builder()
    else:
      builder = builders.crystal_structure_builder()
    unit_cell = uctbx.unit_cell(cell)
    builder.make_crystal_symmetry(cell, spacegroup)
    builder.make_structure()
    u_star = shelx_adp_converter(builder.crystal_symmetry)
    for label, site, occupancy, u, uiso_owner, scattering_type, fixed_vars in atom_iter:
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
      else:
        a = xray.scatterer(label=label,
                           site=site,
                           u=u[0],
                           occupancy=occupancy,
                           scattering_type=scattering_type)
        behaviour_of_variable = behaviour_of_variable[:6]
        if uiso_owner is not None:
          behaviour_of_variable[5] = (
            _.constant_times_u_eq, uiso_owner['k'], uiso_owner['id'])
          #behaviour_of_variable[5] = 1 # XXX temporary fix for riding u_iso's
      behaviour_of_variable.pop(0)
      builder.add_scatterer(a, behaviour_of_variable,
                            occupancy_includes_symmetry_factor=True)
    if restraints_iter is not None:
      for restraint_type, kwds in restraints_iter:
        builder.process_restraint(restraint_type, **kwds)
    if constraints_iter is not None:
      for constraint_type, kwds in constraints_iter:
        builder.process_constraint(constraint_type, **kwds)
    self.builder = builder

  def structure(self):
    return self.builder.structure

  def restraint_proxies(self):
    return self.builder.proxies()
