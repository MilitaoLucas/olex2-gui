# cctbx_controller.py

#import wingdbstub
from my_refine_util import *
import math
import scitbx.lbfgs
from cctbx import miller
from cctbx import statistics

class empty: pass

class my_lbfgs(xray.minimization.lbfgs):
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
  #data.make_table()
  data.show()
  #data.table
  
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
  f_sq_obs.set_observation_type(None)
  #f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
  merging = f_sq_obs.merge_equivalents()
  merging.show_summary()
  f_sq_obs = f_sq_obs.average_bijvoet_mates()
  #f_sq_obs = merging.array()
  f_obs = f_sq_obs.f_sq_as_f()
  
  #structure_factors = f_obs.structure_factors_from_scatterers(model, algorithm="direct",
                                                              #cos_sin_table=True)
  
  f_obs.setup_binner(
    #d_min=f_obs.d_min(),
    #d_max=f_obs.d_max_min()[0],
    #auto_binning=True,
    #reflections_per_bin=reflections_per_bin,
    n_bins=n_bins)
  if (0 or verbose):
    f_obs.binner().show_summary()
    
  wp = statistics.wilson_plot(f_obs, asu_contents)
  if (0 or verbose):
    print "wilson_k, wilson_b:", 1/wp.wilson_intensity_scale_factor, wp.wilson_b
    
  return wp

def completeness_statistics(reflections, n_bins=20):  
  verbose = False
  f_obs=reflections.f_obs
  
  f_sq_obs = reflections.f_sq_obs
  f_sq_obs.set_observation_type(None)
  f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
  f_obs = f_sq_obs.f_sq_as_f()
  
  f_obs.setup_binner(
    #n_bins=n_bins
    auto_binning=True
  )
  if (0 or verbose):
    f_obs.binner().show_summary()
    
  return statistics.completeness_plot(f_obs)

def cumulative_intensity_distribution(model, reflections, n_bins=20):  
  verbose = False
  f_obs=reflections.f_obs
  
  f_sq_obs = reflections.f_sq_obs
  f_sq_obs.set_observation_type(None)
  f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
  f_obs = f_sq_obs.f_sq_as_f()
  
  f_obs.setup_binner(
    n_bins=n_bins
  )
  if (0 or verbose):
    f_obs.binner().show_summary()
    
  return statistics.cumulative_intensity_distribution(f_obs, hkl_conditions=(
    statistics.is_even,
    statistics.is_even,
    None)).xy_plot_info()

def f_obs_vs_f_calc(model, reflections):
  f_obs = reflections.f_obs
  sf = xray.structure_factors.from_scatterers(miller_set=f_obs,cos_sin_table=True)
  f_calc = sf(model,f_obs).f_calc()
  
  f_obs_sq = f_obs.f_as_f_sq()
  f_calc_sq = f_obs.f_as_f_sq()
  
  plot = empty()
  plot.f_obs_sq = f_obs_sq.data()
  plot.f_calc_sq = f_calc_sq.data()
  
  return plot
  
  
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


class refinement(object):
  def __init__(self, cell, spacegroup, atom_iter, reflections, max_cycles=10):
    """ cell is a 6-uple, spacegroup a string and atom_iter yields tuples (label, xyz, u) """
    self.cs = crystal.symmetry(cell, spacegroup)
    self.xs = xray.structure(self.cs.special_position_settings())
    self.max_cycles = max_cycles
    self.reflections = reflections
    u_star = shelx_adp_converter(self.cs)
    for label, xyz, u, elt in atom_iter:
      if len(u) != 1:
        a = xray.scatterer(label, xyz, u_star(*u))
#				a.flags.use_u_iso(True)
#				a.flags.use_u_aniso(False)
      else:
        a = xray.scatterer(label, xyz,u[0])
        #a.flags.use_u_iso(False)
        #a.flags.use_u_aniso(True)

      a.flags.set_grad_site(True)
      if a.flags.use_u_iso() == True:
        a.flags.set_grad_u_iso(True)
        a.flags.set_grad_u_aniso(False)
      if a.flags.use_u_aniso()== True:
        a.flags.set_grad_u_aniso(True)
        a.flags.set_grad_u_iso(False)
      self.xs.add_scatterer(a)

    from cctbx.eltbx import wavelengths, sasaki
    lambda_ = wavelengths.characteristic('Mo').as_angstrom()
    for sc in self.xs.scatterers():
      if sc.scattering_type in ('H','D'):continue
      fp_fdp = sasaki.table(sc.scattering_type).at_angstrom(lambda_)
      sc.fp = fp_fdp.fp()
      sc.fdp = fp_fdp.fdp()



  def on_cycle_finished(self, xs, minimiser):
    """ called after each iteration of the given minimiser, xs being
		the refined structure. It does nothing in this class. """

  def start(self):
    """ Start the refinement """
    #self.copy_cctbx_original_structure()
    self.filter_cctbx_reflections()
    self.xs0 = self.xs
    self.set_cctbx_refinement_flags()
    #self.get_cctbx_reflections()
    #self.filter_cctbx_reflections()
    self.setup_cctbx_refinement()
    self.start_cctbx_refinement()

  def iter_scatterers(self):
    """ an iterator over tuples (label, xyz, u) """
    for a in self.xs.scatterers():
      label = a.label
      xyz = a.site
      symbol = a.scattering_type
      if a.flags.use_u_iso(): 
        u = (a.u_iso,)
        u_eq = u[0]
      if a.flags.use_u_aniso(): 
        u_cif = adptbx.u_star_as_u_cart(self.xs.unit_cell(), a.u_star)
        u = u_cif
        u_eq = adptbx.u_star_as_u_iso(self.xs.unit_cell(), a.u_star)

      yield label, xyz, u, u_eq, symbol


  def cell(self):
    """ the cell as a 6-uple """
    cell = property(cell)

  #def space_group(self):
    #""" the space-group as a Hermann-Mauguin or whatever you like """
    #space_group = property(space_group)


  #def copy_cctbx_original_structure(self):
    #cs = self.cs
    #xs0 = xray.structure(
      #cs.special_position_settings(),
      #flex.xray_scatterer((self.scatterers)))
    #xs = xs0.deep_copy_scatterers()
    #self.xs0 = xs0
    #self.xs = xs

  def set_cctbx_refinement_flags(self):
    for a in self.xs.scatterers():
      a.flags.set_grad_site(True)
      if a.flags.use_u_iso() == True:
        a.flags.set_grad_u_iso(True)
        a.flags.set_grad_u_aniso(False)
      if a.flags.use_u_aniso()== True:
        a.flags.set_grad_u_aniso(True)
        a.flags.set_grad_u_iso(False)

  def filter_cctbx_reflections(self):
    #f_obs = reflections_server.get_miller_arrays(None)[0].f_sq_as_f()
    f_sq_obs = self.reflections.f_sq_obs # read the reflections from the file
    for i in xrange(f_sq_obs.size()):
      if f_sq_obs.data()[i] < -f_sq_obs.sigmas()[i]:
        f_sq_obs.data()[i] = -f_sq_obs.sigmas()[i]
    f_obs = f_sq_obs\
          .eliminate_sys_absent()\
          .as_non_anomalous_array()\
          .merge_equivalents()\
          .array().f_sq_as_f()

    self.f_obs = f_obs

  def setup_cctbx_refinement(self):
    ls = xray.least_squares_residual(self.f_obs)
    self.ls = ls

  def start_cctbx_refinement(self):

    minimisation = my_lbfgs(
      delegate=lambda mini: self.on_cycle_finished(self.xs, mini),
      target_functor=self.ls,
      xray_structure=self.xs,
      #structure_factor_algorithm="direct",
      cos_sin_table=True,
      lbfgs_termination_params = scitbx.lbfgs.termination_parameters(
        max_iterations=self.max_cycles),
      verbose=1
    )
    self.minimisation = minimisation

  def f_obs_minus_f_calc_map(self, resolution):
    f_obs=self.f_obs
    f_sq_obs = self.reflections.f_sq_obs
    f_sq_obs.set_observation_type(None)
    f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
    f_obs = f_sq_obs.f_sq_as_f()
    sf = xray.structure_factors.from_scatterers(
      miller_set=f_obs,
      cos_sin_table=True
    )
    f_calc = sf(self.xs, f_obs).f_calc()
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

  def get_difference_map(self, resolution=0.2):
    return self.f_obs_minus_f_calc_map(resolution).real_map()

  def fourier_map(self):
    fmap = self.f_obs.structure_factors_from_scatterers(
      xray_structure=self.xs,
      algorithm="direct").f_calc()
    grid = fmap.fft_map().real_map()
    return grid

  def get_f_obs_map(self, resolution=0.2):
    f_obs=self.f_obs
    structure_factors = xray.structure_factors.from_scatterers(
      miller_set=f_obs,
      cos_sin_table=True
    )
    minimisation = self.minimisation
    k = minimisation.target_result.scale_factor()
    f_calc = minimisation.f_calc
    f_obs = minimisation.target_functor.f_obs()
    f_obs_minus_f_calc = f_obs.f_obs_minus_f_calc(1./k, f_calc)
    fm = f_obs_minus_f_calc.fft_map(
      symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
    )
    fobs_map = f_obs.f_obs.fft_map(
      symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=True),
      resolution_factor=resolution,
    )
    grid = fobs_map.real_map()
    return grid


  def iter_peaks(self, resolution=0.2):
    peaks = self.f_obs_minus_f_calc_map(resolution).peak_search(
      parameters=maptbx.peak_search_parameters(
        peak_cutoff=1,
        min_distance_sym_equiv=1.0,
        max_clusters=30,
        ),
      verify_symmetry=False
      ).all()

    #self.difference_map_grid = m
    #rFile = open(r"C:\map.txt", 'w')
    #s = m.last()
    #rFile.write("%s %s %s " %(s[0], s[1], s[2]))
    #for i in range (s[0]):
      #for j in range (s[1]):
        #for k in range (s[2]):
          #rFile.write("%.2f " %(m[i,j,k]))


    #	peaks = fm.peak_search()
    for q,h in zip(peaks.sites(), peaks.heights()):
      yield q,h

  def r1(self):
    f_sq_obs = self.reflections.f_sq_obs
    merging = f_sq_obs.eliminate_sys_absent().merge_equivalents()
    #merging.show_summary()
    f_sq_obs = merging.array()
    f_obs = f_sq_obs.f_sq_as_f()
    strong = f_obs.data() > 4*f_obs.sigmas()
    f_obs = f_obs.select(strong)
    sf = xray.structure_factors.from_scatterers(
      miller_set=f_obs,
      cos_sin_table=True
    )
    f_calc = sf(self.xs, f_obs).f_calc()
    fc = flex.abs(f_calc.data())
    fo = f_obs.data()
    k = self.minimisation.target_result.scale_factor()
    return flex.sum(flex.abs(k*fc - fo)) / flex.sum(fo)


if __name__ == '__main__':
  def gen_atoms():
    yield (
      'O1', 
      (-0.137150, 0.839571, 0.535618),
      (0.03920, 0.02479, 0.02102, -0.00359, 0.00749, -0.01039)
    )
    yield (
      'O2',  
      (0.196475, 0.880847, 0.239105),
      (0.02834, 0.02192, 0.02851, 0.00028, 0.01033, 0.00035)
    )
    yield ( 
      'N',  
      (0.044615, 0.885818, 0.395317),
      (0.01980, 0.01662, 0.01889, -0.00091, 0.00100, -0.00129)
    )
    yield (
      'C1', 
      (-0.067890, 0.803554, 0.453464),
      (0.02227, 0.01714, 0.01979, 0.00072, -0.00183, -0.00264)
    )
    yield (
      'C2',  
      (0.101242, 0.823488, 0.303320),
      (0.01814, 0.01616, 0.02174, -0.00007, 0.00138, 0.00220)
    )
    yield (
      'C3',  
      (0.022664, 0.677112, 0.299133),
      (0.02161, 0.01547, 0.02287, -0.00148, 0.00112, 0.00028)
    )
    yield (
      'C4', 
      (-0.088420, 0.663297, 0.399782),
      (0.02982, 0.01551, 0.02078, 0.00046, 0.00045, -0.00241)
    )
  cell=(7.3500, 9.5410, 12.8420, 90.000, 90.000, 90.000)
  spacegroup="Pbca"
  r = refinement(cell, spacegroup,
                 atom_iter=gen_atoms(),
                 reflections=reflections(cell, spacegroup, '03srv209.hkl')
                 )
  from iotbx import shelx
  r.xs = shelx.from_ins.from_ins('/Users/luc/Developer/Seattle/TestStructures/03srv209.res')
  r.start()
  #r.get_difference_map()
  #for q,h in r.iter_peaks():
    #print h, q
  #print '********************'
  print r.r1()	

