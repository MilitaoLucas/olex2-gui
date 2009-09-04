# cctbx_controller.py

from my_refine_util import *
import math
import scitbx.lbfgs
from cctbx import miller
from cctbx import statistics
from smtbx.refinement import minimization
from cctbx import uctbx
from iotbx.shelx import builders
from smtbx.refinement.manager import manager

class empty: pass

class my_lbfgs(minimization.lbfgs):
  def __init__(self, delegate, **kwds):
    self.callback_after_step = delegate
    super(my_lbfgs, self).__init__(**kwds)


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

def wilson_statistics(model, reflections, n_bins=10):
  from cctbx import sgtbx

  p1_space_group = sgtbx.space_group_info(symbol="P 1").group()
  reflections_per_bin=200
  verbose=False

  asu_contents = {}

  for scatterer in model.scatterers():
    if scatterer.scattering_type in asu_contents.keys():
      asu_contents[scatterer.scattering_type] += 1
    else:
      asu_contents.setdefault(scatterer.scattering_type, 1)

  if not asu_contents:
    asu_volume = model.unit_cell().volume()/float(model.space_group().order_z())
    number_carbons = asu_volume/18.0
    asu_contents.setdefault('C', number_carbons)

  f_obs=reflections.f_obs
  f_obs.space_group = p1_space_group

  f_sq_obs = reflections.f_sq_obs
  merging = f_sq_obs.merge_equivalents()
  merging.show_summary()
  f_sq_obs = f_sq_obs.average_bijvoet_mates()
  f_obs = f_sq_obs.f_sq_as_f()
  f_obs.setup_binner(
    #d_min=f_obs.d_min(),
    #d_max=f_obs.d_max_min()[0],
    #auto_binning=True,
    #reflections_per_bin=reflections_per_bin,
    n_bins=n_bins)
  if (0 or verbose):
    f_obs.binner().show_summary()
  wp = statistics.wilson_plot(f_obs, asu_contents, e_statistics=True)
  if (0 or verbose):
    print "wilson_k, wilson_b:", 1/wp.wilson_intensity_scale_factor, wp.wilson_b
  return wp

def completeness_statistics(reflections, wavelength, reflections_per_bin=20, verbose=False):
  f_obs=reflections.f_obs
  f_sq_obs = reflections.f_sq_obs_filtered
  f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
  f_obs = f_sq_obs.f_sq_as_f()
  f_obs.setup_binner(
    reflections_per_bin=reflections_per_bin,
    auto_binning=True)
  if (0 or verbose):
    f_obs.binner().show_summary()
  missing_set = f_obs.complete_set().lone_set(f_obs).sort()
  plot = statistics.completeness_plot(f_obs)
  plot.x = uctbx.d_star_sq_as_two_theta(
    1./flex.pow2(flex.double(plot.x)), wavelength,deg=True)
  plot.missing_set = missing_set
  if missing_set.size() > 0:
    print "Missing data:"
    print "  h  k  l  two theta"
  else:
    print "No missing data"
  for indices, two_theta in zip(
    missing_set.indices(), missing_set.two_theta(wavelength=wavelength, deg=True).data()):
    print ("(%2i %2i %2i)  ") %indices + ("%8.2f") %two_theta
  return plot

def cumulative_intensity_distribution(reflections, n_bins=20, verbose=False):
  f_obs=reflections.f_obs
  f_sq_obs = reflections.f_sq_obs
  f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
  f_obs = f_sq_obs.f_sq_as_f()
  f_obs.setup_binner(
    n_bins=n_bins
  )
  if (0 or verbose):
    f_obs.binner().show_summary()
  return statistics.cumulative_intensity_distribution(f_obs).xy_plot_info()

def sys_absent_intensity_distribution(reflections):
  f_obs = reflections.f_obs
  f_sq_obs = reflections.f_sq_obs
  return statistics.sys_absent_intensity_distribution(f_sq_obs).xy_plot_info()

def f_obs_vs_f_calc(model, reflections):
  assert model.scatterers().size() > 0, "model.scatterers().size() > 0"
  f_obs_merged = reflections.f_sq_obs_merged.f_sq_as_f()
  sf = xray.structure_factors.from_scatterers(miller_set=f_obs_merged,cos_sin_table=True)
  f_calc_merged = sf(model,f_obs_merged).f_calc()

  f_obs_filtered = f_obs_merged.common_set(reflections.f_sq_obs_filtered)
  f_calc_filtered = f_calc_merged.common_set(f_obs_filtered)
  f_obs_omitted = f_obs_merged.lone_set(f_obs_filtered)
  f_calc_omitted = f_calc_merged.lone_set(f_calc_filtered)

  ls_function = xray.unified_least_squares_residual(f_obs_filtered)
  ls = ls_function(f_calc_filtered, compute_derivatives=False)
  k = ls.scale_factor()
  fc = flex.abs(f_calc_filtered.data())
  fc *= k
  fo = flex.abs(f_obs_filtered.data())

  fit = flex.linear_regression(fc, fo)
  fit.show_summary()

  plot = empty()
  plot.indices = f_obs_filtered.indices()
  plot.f_obs = fo
  plot.f_calc = fc
  plot.f_obs_omitted = flex.abs(f_obs_omitted.data())
  plot.f_calc_omitted = flex.abs(f_calc_omitted.data()) * k
  plot.indices_omitted = f_obs_omitted.indices()
  plot.fit_slope = fit.slope()
  plot.fit_y_intercept = fit.y_intercept()
  plot.xLegend = "F calc"
  plot.yLegend = "F obs"
  return plot

def powder_plot(model, reflection, n_bins=500):
  f_obs = reflections.f_obs.merge_equivalents().array()
  f_obs = f_obs.eliminate_sys_absent().average_bijvoet_mates()
  sf = xray.structure_factors.from_scatterers(miller_set=f_obs,cos_sin_table=True)
  f_calc = sf(model,f_obs).f_calc()
  f_obs.setup_binner(
    n_bins=n_bins)



class reflections(object):
  def __init__(self,  cell, spacegroup, reflection_file):
    """ reflections is the filename holding the reflections """
    cs = crystal.symmetry(cell, spacegroup)
    reflections_server = reflection_file_utils.reflection_file_server(
      crystal_symmetry = cs,
      reflection_files = [
        reflection_file_reader.any_reflection_file('hklf4=%s' %reflection_file)
      ]
    )
    self.crystal_symmetry = cs
    self.f_sq_obs = reflections_server.get_miller_arrays(None)[0]
    self.f_obs = self.f_sq_obs.f_sq_as_f()
    self.omit = None
    self.merg = None
    self.f_sq_obs_merged = None
    self.f_sq_obs_filtered = None

  def merge(self, merg):
    self.merg = merg
    self.f_sq_obs_merged = self.f_sq_obs
    self.f_sq_obs_merged = self.f_sq_obs_merged.eliminate_sys_absent().average_bijvoet_mates()

  def filter(self, omit, wavelength):
    self.omit = omit
    two_theta = omit['2theta']
    s = omit['s']
    hkl = omit.get('hkl')
    f_sq_obs_filtered = self.f_sq_obs_merged.resolution_filter(
      d_min=uctbx.two_theta_as_d(two_theta, wavelength, deg=True))
    if hkl is not None:
      f_sq_obs_filtered = f_sq_obs_filtered.indices_filter(
        indices=flex.miller_index(hkl))
    self.f_sq_obs_filtered = f_sq_obs_filtered

def create_cctbx_xray_structure(cell, spacegroup, atom_iter, restraint_iterator=None):
  """ cell is a 6-uple, spacegroup a string and atom_iter yields tuples (label, xyz, u, element_type) """
  builder = builders.crystal_structure_builder()
  unit_cell = uctbx.unit_cell(cell)
  builder.make_crystal_symmetry(cell, spacegroup)
  builder.make_structure()
  u_star = shelx_adp_converter(builder.crystal_symmetry)
  for label, site, occupancy, u, scattering_type in atom_iter:
    if len(u) != 1:
      a = xray.scatterer(label=label,
                         site=site,
                         u=u_star(*u),
                         occupancy=occupancy,
                         scattering_type=scattering_type)
      behaviour_of_variable = [0,0,0,1,0,0,0,0,0]
    else:
      a = xray.scatterer(label=label,
                         site=site,
                         u=u[0],
                         occupancy=occupancy,
                         scattering_type=scattering_type)
      behaviour_of_variable = [0,0,0,1,0]
    builder.add_scatterer(a, behaviour_of_variable)
  return builder.structure

class refinement(manager):
  def __init__(self,
               f_obs=None,
               f_sq_obs=None,
               xray_structure=None,
               wavelength=None,
               max_sites_pre_cycles=20,
               max_cycles=40,
               max_peaks=30,
               verbose=1,
               log=None):
    manager.__init__(self,
                     f_obs=f_obs,
                     f_sq_obs=f_sq_obs,
                     xray_structure=xray_structure,
                     lambda_=wavelength,
                     max_cycles=max_cycles,
                     max_peaks=max_peaks,
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
    fc2 = flex.norm(f_calc.data())
    fo2 = f_sq_obs.data()
    wfo2 = 1./flex.pow2(f_sq_obs.sigmas())
    K2 = flex.mean_weighted(fo2*fc2, wfo2)/flex.mean_weighted(fc2*fc2, wfo2)
    K2 = math.sqrt(K2)
    f_obs_minus_f_calc = f_obs.f_obs_minus_f_calc(1./K2, f_calc)
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
