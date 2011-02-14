from __future__ import division

from cctbx_olex_adapter import OlexCctbxAdapter

from olexFunctions import OlexFunctions
OV = OlexFunctions()

from cctbx import statistics
from cctbx.array_family import flex
from cctbx import uctbx

import math

class empty: pass


class OlexCctbxGraphs(OlexCctbxAdapter):
  def __init__(self, graph, *args, **kwds):
    OlexCctbxAdapter.__init__(self)
    if self.reflections is None:
      raise RuntimeError, "There was an error reading the reflection file."
    self.graph = graph
    twinning=self.olx_atoms.model.get('twin')

    bitmap = 'working'
    OV.CreateBitmap(bitmap)

    try:
      if graph == "wilson":
        self.xy_plot = wilson_statistics(self.xray_structure(), self.reflections, **kwds)

      elif graph == "completeness":
        self.xy_plot = completeness_statistics(self.reflections, self.wavelength, **kwds)

      elif graph == "cumulative":
        self.xy_plot = cumulative_intensity_distribution(self.reflections, **kwds)

      elif graph == "sys_absent":
        self.xy_plot = sys_absent_intensity_distribution(self.reflections)

    except Exception, err:
      raise Exception, err
    finally:
      OV.DeleteBitmap(bitmap)


class r1_factor_vs_resolution(OlexCctbxAdapter):
  def __init__(self, n_bins=10, resolution_as="two_theta"):
    OlexCctbxAdapter.__init__(self)
    self.resolution_as = resolution_as
    fo2 = self.reflections.f_sq_obs_filtered
    fo = fo2.f_sq_as_f()
    fc = self.f_calc(miller_set=fo)
    weights = self.compute_weights(fo2, fc)
    scale_factor = fo2.scale_factor(fc, weights=weights)
    fo.setup_binner(n_bins=n_bins)
    self.info = fo.info()
    self.binned_data = fo.r1_factor(fc, scale_factor=math.sqrt(scale_factor), use_binning=True)
    self.binned_data.show()

  def xy_plot_info(self):
    r = empty()
    r.title = "R1 factor vs resolution"
    if (self.info is not None):
      r.title += ": " + str(self.info)
    d_star_sq = self.binned_data.binner.bin_centers(2)
    if self.resolution_as == "two_theta":
      resolution = uctbx.d_star_sq_as_two_theta(
        d_star_sq, self.wavelength, deg=True)
    elif self.resolution_as == "d_spacing":
      resolution = uctbx.d_star_sq_as_d(d_star_sq)
    elif self.resolution_as == "d_star_sq":
      resolution = d_star_sq
    elif self.resolution_as == "stol":
      resolution = uctbx.d_star_sq_as_stol(d_star_sq)
    elif self.resolution_as == "stol_sq":
      resolution = uctbx.d_star_sq_as_stol_sq(d_star_sq)
    r.x = resolution
    r.y = self.binned_data.data[1:-1]
    r.xLegend = self.resolution_as
    r.yLegend = "R1 factor"
    return r


class scale_factor_vs_resolution(OlexCctbxAdapter):
  def __init__(self, n_bins=10, resolution_as="two_theta", normalize=True):
    OlexCctbxAdapter.__init__(self)
    self.resolution_as = resolution_as
    fo2 = self.reflections.f_sq_obs_filtered
    fo2.setup_binner(n_bins=n_bins)
    self.info = fo2.info()
    fc = self.f_calc(miller_set=fo2)
    weights = self.compute_weights(fo2, fc)
    self.binned_data = fo2.scale_factor(
      fc, weights=weights, use_binning=True)
    if normalize:
      k = fo2.scale_factor(fc, weights=weights)
      for i_bin in self.binned_data.binner.range_used():
        self.binned_data.data[i_bin] /= k
    self.binned_data.show()

  def xy_plot_info(self):
    r = empty()
    r.title = "Scale factor vs resolution"
    if (self.info is not None):
      r.title += ": " + str(self.info)
    d_star_sq = self.binned_data.binner.bin_centers(2)
    if self.resolution_as == "two_theta":
      resolution = uctbx.d_star_sq_as_two_theta(
        d_star_sq, self.wavelength, deg=True)
    elif self.resolution_as == "d_spacing":
      resolution = uctbx.d_star_sq_as_d(d_star_sq)
    elif self.resolution_as == "d_star_sq":
      resolution = d_star_sq
    elif self.resolution_as == "stol":
      resolution = uctbx.d_star_sq_as_stol(d_star_sq)
    elif self.resolution_as == "stol_sq":
      resolution = uctbx.d_star_sq_as_stol_sq(d_star_sq)
    r.x = resolution
    r.y = self.binned_data.data[1:-1]
    r.xLegend = self.resolution_as
    r.yLegend = "Scale factor"
    return r


class f_obs_vs_f_calc(OlexCctbxAdapter):
  def __init__(self, batch_number=None):
    OlexCctbxAdapter.__init__(self)
    if [batch_number, self.reflections.batch_numbers].count(None) == 0:
      assert batch_number <= flex.max(self.reflections.batch_numbers.data()), "batch_number <= max(batch_numbers)"
      selection = (self.reflections.batch_numbers.data() == batch_number)
      f_sq_obs = self.reflections.f_sq_obs.select(selection)
      merging = self.reflections.merge(f_sq_obs)
      f_obs_merged = merging.array().f_sq_as_f()
      f_obs_filtered = merging.array().f_sq_as_f()
    else:
      f_obs_merged = self.reflections.f_sq_obs_merged.f_sq_as_f()
      f_obs_filtered = f_obs_merged.common_set(self.reflections.f_sq_obs_filtered)

    f_calc_merged = self.f_calc(miller_set=f_obs_merged)
    f_calc_filtered = f_calc_merged.common_set(f_obs_filtered)
    f_obs_omitted = f_obs_merged.lone_set(f_obs_filtered)
    f_calc_omitted = f_calc_merged.common_set(
      f_obs_merged).lone_set(f_calc_filtered)

    weights = self.compute_weights(
      self.reflections.f_sq_obs_filtered, f_calc_filtered)
    k = math.sqrt(self.reflections.f_sq_obs_filtered.scale_factor(
      f_calc_filtered, weights=weights))
    fo = flex.abs(f_obs_filtered.data())
    fc = flex.abs(f_calc_filtered.data())
    fc *= k
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
    self.xy_plot = plot


class f_obs_over_f_calc(OlexCctbxAdapter):
  def __init__(self,
               binning=False,
               n_bins=None,
               resolution_as="two_theta"):
    OlexCctbxAdapter.__init__(self)
    f_sq_obs_filtered = self.reflections.f_sq_obs_filtered
    f_obs_filtered = f_sq_obs_filtered.f_sq_as_f()
    f_calc_filtered = self.f_calc(miller_set=f_obs_filtered)

    weights = self.compute_weights(f_sq_obs_filtered, f_calc_filtered)
    k = math.sqrt(
      f_sq_obs_filtered.scale_factor(f_calc_filtered, weights=weights))
    if binning == True:
      assert n_bins is not None
      binner = f_obs_filtered.setup_binner(n_bins=n_bins)
      f_calc_filtered = f_calc_filtered.as_amplitude_array()
      f_calc_filtered.use_binning(binner)
      sum_fo = flex.double(f_obs_filtered.sum(use_binning=True).data[1:-1])
      sum_fc = flex.double(f_calc_filtered.sum(use_binning=True).data[1:-1])
      fo_over_fc = sum_fo/(sum_fc*k)
      d_star_sq = binner.bin_centers(2)
    else:
      fc = flex.abs(f_calc_filtered.data())
      fc *= k
      fo = flex.abs(f_obs_filtered.data())
      fo_over_fc = fo/fc
      d_star_sq = f_calc_filtered.d_star_sq().data()
    if resolution_as == "two_theta":
      resolution = uctbx.d_star_sq_as_two_theta(
        d_star_sq, self.wavelength, deg=True)
    elif resolution_as == "d_spacing":
      resolution = uctbx.d_star_sq_as_d(d_star_sq)
    elif resolution_as == "d_star_sq":
      resolution = d_star_sq
    elif resolution_as == "stol":
      resolution = uctbx.d_star_sq_as_stol(d_star_sq)
    elif resolution_as == "stol_sq":
      resolution = uctbx.d_star_sq_as_stol_sq(d_star_sq)
    plot = empty()
    plot.indices = f_obs_filtered.indices()
    plot.f_obs_over_f_calc = fo_over_fc
    plot.resolution = resolution
    plot.xLegend = resolution_as
    if binning == True:
      plot.yLegend = "Sum|Fo| / Sum|Fc|"
    else:
      plot.yLegend = "F obs/F calc"
    self.xy_plot = plot


class normal_probability_plot(OlexCctbxAdapter):
  def __init__(self,
               distribution=None):
    OlexCctbxAdapter.__init__(self)
    from scitbx.math import distributions
    f_sq_obs = self.reflections.f_sq_obs_filtered
    f_obs = f_sq_obs.f_sq_as_f()
    f_calc = self.f_calc(miller_set=f_obs)
    f_sq_calc = f_calc.as_intensity_array()
    if distribution is None:
      distribution = distributions.normal_distribution()
    self.info = None
    weights = self.compute_weights(f_sq_obs, f_calc)
    #
    scale_factor = f_sq_obs.scale_factor(f_calc, weights=weights)
    observed_deviations = flex.sqrt(weights) * (
      f_sq_obs.data() - scale_factor * f_sq_calc.data())
    selection = flex.sort_permutation(observed_deviations)
    self.x = distribution.quantiles(f_sq_obs.size())
    self.y = observed_deviations.select(selection)
    self.indices = f_sq_obs.indices().select(selection)
    fit = flex.linear_regression(self.x[5:-5], self.y[5:-5])
    corr = flex.linear_correlation(self.x[5:-5], self.y[5:-5])
    fit.show_summary()
    assert fit.is_well_defined()
    self.fit_y_intercept = fit.y_intercept()
    self.fit_slope = fit.slope()
    self.correlation = corr.coefficient()
    print "coefficient: %f" %self.correlation

  def xy_plot_info(self):
    r = empty()
    r.title = "Normal probability plot"
    if (self.info != 0):
      r.title += ": " + str(self.info)
    r.x = self.x
    r.y = self.y
    r.indices = self.indices
    r.fit_slope = self.fit_slope
    r.fit_y_intercept = self.fit_y_intercept
    r.xLegend = "Expected deviations"
    r.yLegend = "Observed deviations"
    return r


class bijvoet_differences_NPP:
  def __init__(self, hooft_analysis=None, use_students_t=False,
               scale=None, use_fcf=False):
    from smtbx import absolute_structure
    self.have_bijvoet_pairs = False
    if hooft_analysis is None:
      import cctbx_olex_adapter
      if use_students_t:
        hooft_analysis = cctbx_olex_adapter.students_t_hooft_analysis(
          use_fcf=use_fcf)
      else:
        hooft_analysis = cctbx_olex_adapter.hooft_analysis(use_fcf=use_fcf)
      if not hasattr(hooft_analysis, 'delta_fo2'):
        return
      hooft_analysis.show()
    self.have_bijvoet_pairs = True
    self.plot = absolute_structure.bijvoet_differences_probability_plot(
      hooft_analysis, use_students_t_distribution=use_students_t)
    self.plot.show()

  def xy_plot_info(self):
    if not self.have_bijvoet_pairs: return None
    r = empty()
    r.title = "Bijvoet difference normal probability plot"
    r.x = self.plot.x
    r.y = self.plot.y
    r.indices = self.plot.delta_fc2.indices()
    r.fit_slope = self.plot.fit.slope()
    r.fit_y_intercept = self.plot.fit.y_intercept()
    r.xLegend = "Expected deviations"
    r.yLegend = "Observed deviations"
    return r


class bijvoet_differences_scatter_plot(OlexCctbxAdapter):
  def __init__(self, hooft_analysis=None, use_students_t=False):
    OlexCctbxAdapter.__init__(self)
    self.info = None
    self.have_bijvoet_pairs = False
    if hooft_analysis is None:
      import cctbx_olex_adapter
      if use_students_t:
        hooft_analysis = cctbx_olex_adapter.students_t_hooft_analysis()
      else:
        hooft_analysis = cctbx_olex_adapter.hooft_analysis()
      if not hasattr(hooft_analysis, 'delta_fo2'):
        return
      hooft_analysis.show()
    self.have_bijvoet_pairs = True
    cutoff_factor = 0.12
    selection = (flex.abs(hooft_analysis.delta_fo2.data()) > cutoff_factor
                 * hooft_analysis.delta_fo2.sigmas())
    self.delta_fo2 = hooft_analysis.delta_fo2.select(selection)
    self.delta_fc2 = hooft_analysis.delta_fc2.select(selection)
    self.delta_fo2, minus_fo2 =\
        self.delta_fo2.generate_bijvoet_mates().hemispheres_acentrics()
    self.delta_fc2, minus_fc2 =\
        self.delta_fc2.generate_bijvoet_mates().hemispheres_acentrics()
    # we want to plot both hemispheres
    self.delta_fo2.indices().extend(minus_fo2.indices())
    self.delta_fo2.data().extend(minus_fo2.data() * -1)
    self.delta_fo2.sigmas().extend(minus_fo2.sigmas())
    self.delta_fc2.indices().extend(minus_fc2.indices())
    self.delta_fc2.data().extend(minus_fc2.data() * -1)
    self.indices = self.delta_fo2.indices()

  def xy_plot_info(self):
    if not self.have_bijvoet_pairs: return None
    r = empty()
    r.title = "Bijvoet differences scatter plot"
    if (self.info != 0):
      r.title += ": " + str(self.info)
    r.x = self.delta_fc2.data()
    r.y = self.delta_fo2.data()
    fit = flex.linear_regression(r.x, r.y)
    r.fit_slope = fit.slope()
    r.fit_y_intercept = fit.y_intercept()
    r.indices = self.indices
    r.xLegend = "delta Fc2"
    r.yLegend = "delta Fo2"
    r.sigmas = self.delta_fo2.sigmas()
    return r

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

class completeness_statistics(object):
  def __init__(self, reflections, wavelength=None, reflections_per_bin=20,
               bin_range_as="two_theta", verbose=False):
    assert bin_range_as in ["d_spacing", "d_star_sq", "two_theta", "stol", "stol_sq"]
    f_obs=reflections.f_obs
    f_sq_obs = reflections.f_sq_obs_merged
    f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
    f_obs = f_sq_obs.f_sq_as_f()
    binner = f_obs.complete_set().setup_binner(
      reflections_per_bin=reflections_per_bin,
      auto_binning=True)
    f_obs.use_binning(binner)
    if (0 or verbose):
      f_obs.binner().show_summary()
    missing_set = f_obs.complete_set().lone_set(f_obs).sort()
    self.info = f_obs.info()
    self.completeness = f_obs.completeness(use_binning=True)
    binner = self.completeness.binner
    data = self.completeness.data
    self.x = binner.bin_centers(2)
    self.y = data[1:-1]
    #
    if bin_range_as == "two_theta":
      assert wavelength is not None
      self.x = uctbx.d_star_sq_as_two_theta(self.x, wavelength,deg=True)
      resolutions = missing_set.two_theta(wavelength=wavelength, deg=True).data()
    elif bin_range_as == "d_spacing":
      self.x = uctbx.d_star_sq_as_d(self.x)
      resolutions = missing_set.d_spacings().data()
    elif bin_range_as == "d_star_sq":
      resolutions = missing_set.d_star_sq().data()
    elif bin_range_as == "stol":
      self.x = uctbx.d_star_sq_as_stol(self.x)
      resolutions = flex.sqrt(missing_set.sin_theta_over_lambda_sq().data())
    elif bin_range_as == "stol_sq":
      self.x = uctbx.d_star_sq_as_stol_sq(self.x)
      resolutions = missing_set.sin_theta_over_lambda_sq().data()
    self.missing_set = missing_set
    if missing_set.size() > 0:
      print "Missing data:"
      print "  h  k  l  %s" %bin_range_as
    else:
      print "No missing data"
    for indices, resolution in zip(missing_set.indices(), resolutions):
      print ("(%2i %2i %2i)  ") %indices + ("%8.2f") %resolution

def cumulative_intensity_distribution(reflections,
                                      n_bins=20,
                                      verbose=False):
  f_obs=reflections.f_sq_obs_merged.f_sq_as_f()
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
