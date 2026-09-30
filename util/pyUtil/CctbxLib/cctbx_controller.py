# cctbx_controller.py

from my_refine_util import *
import math
import os
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


def read_hkl_arrays(cs, f_hklf_code, reflection_file):
  """ The hklf reader raises on the first line it cannot parse. 21 whole-COD hkl
  files carry a res or cif block after the data with no 0 0 0 line in front of
  it (1547410, 1555711), so on a read error the reflections up to the first
  non-reflection line are re-read from a terminated temporary copy (24 Sep 2026). """
  def read(path):
    server = reflection_file_utils.reflection_file_server(
      crystal_symmetry=cs,
      reflection_files=[reflection_file_reader.any_reflection_file(
        'hklf%s=%s' % (f_hklf_code, path), strict=False)])
    return server.get_miller_arrays(None)
  arrays = None
  try:
    arrays = read(reflection_file)
    # a blank line ends the read: a bare CR between the lines (1518723: CR CR
    # LF endings) after the first reflection, an empty line inside the data
    # (1543653: 639 of 24089 read)
    e = RuntimeError("%d reflection(s) read" % arrays[0].size())
  except Exception as ex:   # Sorry from any_reflection_file, RuntimeError from the parser
    e = ex
  import tempfile
  kept = []
  with open(reflection_file, errors="replace") as f:
    for line in f:
      line = line.rstrip("\r\n")
      if not line.strip():
        continue
      # 3I4 columns first: a negative intensity in F8.3 glues itself to l
      # (4348671: "  52-209.106"), so a whitespace split misreads it
      try:
        h = [int(line[4 * i:4 * i + 4]) for i in range(3)]
        t = line[12:].split()
        rest = [float(t[0]), float(t[1])] + [int(x) for x in t[2:3]]
      except (ValueError, IndexError):
        try:
          t = line.split()
          h = [int(x) for x in t[:3]]
          rest = [float(t[3]), float(t[4])] + [int(x) for x in t[5:6]]
        except (ValueError, IndexError):
          break
      if h == [0, 0, 0]:
        break
      f8 = lambda x: ("%8.2f" % x) if len("%8.2f" % x) <= 8 else ("%8.0f" % x)[:8]
      kept.append("%4d%4d%4d" % tuple(h) + f8(rest[0]) + f8(rest[1])
                  + ("%4d" % rest[2] if len(rest) > 2 else ""))
  if arrays is not None and arrays[0].size() + 1 >= len(kept):
    return arrays
  if len(kept) < 2:
    raise e
  print("%s: %s; using the %d reflections before the first non-reflection line"
        % (os.path.basename(reflection_file), str(e).strip().splitlines()[-1], len(kept)))
  fd, tmp = tempfile.mkstemp(suffix=".hkl")
  with os.fdopen(fd, "w") as f:
    f.write("\n".join(kept) + "\n   0   0   0    0.00    0.00\n")
  try:
    return read(tmp)
  finally:
    os.remove(tmp)

def apply_hklf_matrix(array, hklf_matrix, cs):
  """ h' = M h, as THklFile applies the HKLF matrix. A reflection whose
  transformed index is not integral (a superstructure reflection under a 0.5
  entry) is dropped, as SHELXL drops it. The symmetry stays the ins's:
  change_basis also re-based the space group and threw on 0.5 entries and on a
  det-3 rhombohedral matrix, 28 whole-COD cases (1546007, 4345975; 24 Sep 2026). """
  m = hklf_matrix.as_double()
  keep = flex.bool()
  new = flex.miller_index()
  for h in array.indices():
    t = [m[3 * i] * h[0] + m[3 * i + 1] * h[1] + m[3 * i + 2] * h[2] for i in range(3)]
    r = [int(round(x)) for x in t]
    ok = max(abs(x - y) for x, y in zip(t, r)) < 1e-3
    keep.append(ok)
    if ok:
      new.append(tuple(r))
  info = array.info()
  array = array.select(keep).customized_copy(indices=new, crystal_symmetry=cs)
  return array.set_info(info)

class reflections(object):
  """ reflections is the filename holding the reflections """
  def __init__(self,  cell, spacegroup, reflection_file, hklf_code, hklf_matrix=None, merge_code=2):
    if merge_code != 0:
      cs = crystal.symmetry(cell, spacegroup)
    else:
      cs = crystal.symmetry(cell, "P1")
    self.space_group = spacegroup
    #do we read amplitudes or intensisty?
    f_hklf_code = hklf_code
    if f_hklf_code != 3:
      f_hklf_code = 4
    if reflection_file:
      miller_arrays = read_hkl_arrays(cs, f_hklf_code, reflection_file)
      if hklf_matrix is not None and not hklf_matrix.is_unit_mx():
        miller_arrays = [apply_hklf_matrix(a, hklf_matrix, cs) for a in miller_arrays]
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
      self.f_sq_obs = self.f_obs.f_as_f_sq()
    else:
      self.f_sq_obs = miller_arrays[0]
      self.f_obs = self.f_sq_obs.f_sq_as_f()
    if hklf_code == 5 and len(miller_arrays) <= 1:
      raise RuntimeError("HKLF5 file format requires batch numbers")
    if hklf_code == 2 and len(miller_arrays) <= 2:
      raise RuntimeError("HKLF2 file format requires batch numbers and wavelengths")
    self.wavelengths = None
    if len(miller_arrays) > 1:
      self.batch_numbers_array = miller_arrays[1]
      if hklf_code == 2 and len(miller_arrays) > 2:
        self.wavelengths = miller_arrays[2]
    else:
      self.batch_numbers_array = None
    if hklf_code == 4 and self.batch_numbers_array is not None:
      # An HKLF 5 file read as HKLF 4 (no BASF, see OlexCctbxAdapter.__init__):
      # a negative batch number marks a component that overlaps the next row,
      # and that row is the last component of the same overlapped reflection.
      # Neither is a single-reflection intensity, so both are dropped, as is
      # every other domain (batch 2, 3, ...): its scale is the missing BASF
      # (2023214, 4085534: batch-2 rows at an unknown scale gave R1 0.49).
      b = self.batch_numbers_array.data()
      if (b < 0).count(True):
        # A group's last row carries the summed intensity under that domain's
        # index, which is what a twinned crystal hands a solution anyway, so
        # overlapped groups are kept whichever domain closes them: 4341100 had
        # 23910 -1/2 pairs and no single row, 4346533 kept 405 of 17573 when
        # the -2/1 groups' batch-1 rows were dropped (24 Sep 2026).
        keep = b == 1
        for i in range(b.size()):
          if b[i] < 0 and i + 1 < b.size():
            keep[i + 1] = b[i + 1] > 0
        self.f_sq_obs = self.f_sq_obs.select(keep)
        self.f_obs = self.f_sq_obs.f_sq_as_f()
        self.batch_numbers_array = self.batch_numbers_array.select(keep)
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
    if self.hklf_code in (2,5):
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

  def _get_shel(self, omit, shel, wavelength):
    _shel = shel
    two_theta = omit['2theta']
    d_min = uctbx.two_theta_as_d(two_theta, wavelength, deg=True)
    if _shel is None:
      _shel = {'high' : -1, 'low': -1}
      if two_theta != 180:
        _shel['high'] = d_min
    else:
      if _shel['high'] > _shel['low']:
        _shel = {'high' : _shel['low'], 'low': _shel['high']}
      # SHELXL applies both, so the stricter high-resolution limit wins
      if two_theta != 180:
        _shel['high'] = max(_shel['high'], d_min)
    return _shel

  def filter(self, omit, shel, wavelength, doFilter=True):
    if not doFilter:
      self.f_sq_obs_filtered = self.f_sq_obs_merged
      if self.hklf_code in (2,5):
        self.batch_numbers = self.batch_numbers_array.data()
      return
    self._omit = omit
    two_theta = omit['2theta']
    if shel and two_theta != 180:
      import olx
      olx.Echo("Warning - mixing SHEL and OMIT. Using low resolution limit from SHEL and the stricter high resolution limit of the two",
               m="warning")
    self.d_min = uctbx.two_theta_as_d(two_theta, wavelength, deg=True)
    self._shel = self._get_shel(omit, shel, wavelength)
    hkl = omit.get('hkl')
    f_sq_obs_filtered = self.f_sq_obs_merged.treat_negative_amplitudes_shelx(omit['s'])
    if hkl is None:
      hkl = ()
    if self.hklf_code >= 5 or self.merge_code == 0:
      anomalous_flag = True
    else:
      anomalous_flag = f_sq_obs_filtered.anomalous_flag()

    omit_map = miller.lookup_tensor(flex.miller_index(hkl),
      f_sq_obs_filtered.crystal_symmetry().space_group(), anomalous_flag)
    filter = observations.filter(
      f_sq_obs_filtered.unit_cell(),
      sgtbx.space_group(self.space_group[6:]),
      omit_map,
      float(self._shel['high']),
      float(self._shel['low']),
      omit['s']*0.5
    )
    if self.hklf_code in (2,5):
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
    if self.wavelengths:
      f_sq_obs_filtered.wavelengths = self.wavelengths.select(filter_res.selection)
    if self.hklf_code in (2,5):
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
      try:
        print("R(sigma): %f" %self.merging.r_sigma(), file=log)
      except ZeroDivisionError:  # intensities summing to zero (4348671, 4349736)
        print("R(sigma): n/a", file=log)
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
    elif self.wavelengths:
      rv = self.f_sq_obs_filtered.as_xray_observations(
        scale_indices=self.batch_numbers,
        twin_fractions=twin_fractions,
        wavelengths=self.f_sq_obs_filtered.wavelengths)
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
