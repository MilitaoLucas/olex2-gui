# cctbx_controller.py

#import wingdbstub
from my_refine_util import *
import math
import scitbx.lbfgs
from smtbx.refinement.minimization import lbfgs
from cctbx import miller
from cctbx import statistics
from cctbx import uctbx
from cctbx import geometry_restraints
from iotbx.shelx import builders
from smtbx.refinement.manager import manager

class empty: pass

class my_lbfgs(lbfgs):
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
  f_sq_obs.set_observation_type(None)
  #f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
  merging = f_sq_obs.merge_equivalents()
  merging.show_summary()
  f_sq_obs = f_sq_obs.average_bijvoet_mates()
  #f_sq_obs = merging.array()
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

def sys_absent_intensity_distribution(reflections):
  f_obs = reflections.f_obs
  f_sq_obs = reflections.f_sq_obs
  return statistics.sys_absent_intensity_distribution(f_sq_obs).xy_plot_info()


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

shelx_restraints = {
  'DFIX': {'class': geometry_restraints.bond_sym_proxy,
           'kwds': ('i_seqs','distance_ideal','weight','rt_mx_ji')},
  'DANG': {'class': geometry_restraints.bond_sym_proxy,
           'kwds': ('i_seqs','distance_ideal','weight','rt_mx_ji')},
  'FLAT': {'class': geometry_restraints.planarity_proxy,
           'kwds': ('i_seqs','weights')},
}

def create_cctbx_xray_structure(cell, spacegroup, atom_iter, restraint_iterator=None):
  """ cell is a 6-uple, spacegroup a string and atom_iter yields tuples (label, xyz, u, element_type) """
  builder = builders.restrained_crystal_structure_builder()
  
  unit_cell = uctbx.unit_cell(cell)
  builder.make_crystal_symmetry(cell, spacegroup)
  builder.make_structure()
  u_star = shelx_adp_converter(builder.crystal_symmetry)
  for label, xyz, u, elt in atom_iter:
    if len(u) != 1:
      a = xray.scatterer(label, xyz, u_star(*u))
      behaviour_of_variable = [0,0,0,1,0,0,0,0,0]
    else:
      a = xray.scatterer(label, xyz,u[0])
      behaviour_of_variable = [0,0,0,1,0]
    builder.add_scatterer(a, behaviour_of_variable)
    #a.flags.set_grad_site(True)
    #if a.flags.use_u_iso() == True:
      #a.flags.set_grad_u_iso(True)
      #a.flags.set_grad_u_aniso(False)
    #if a.flags.use_u_aniso()== True:
      #a.flags.set_grad_u_aniso(True)
      #a.flags.set_grad_u_iso(False)
    #xs.add_scatterer(a)

  for restraint_type, kwds in restraint_iterator:
    restraint_dict = shelx_restraints.get(restraint_type.upper())
    restraint_class = restraint_dict['class']
    if restraint_dict is not None:
      restraint_kwds = {}
      keys = restraint_dict['kwds']
      restraint_kwds.setdefault('i_seqs',kwds['i_seqs'])
      for target_value in ('distance_ideal','angle_ideal'):
        if target_value in keys:
          restraint_kwds.setdefault(target_value, kwds['value'])
      if 'weights' in keys:
        restraint_kwds.setdefault('weights',[kwds['weight']]*len(kwds['i_seqs']))
      else:
        restraint_kwds.setdefault('weight',kwds['weight'])
      if 'rt_mx_ji' in keys:
        sym_ops = []
        for sym_op in kwds['sym_ops']:
          if sym_op is not None:
            rot_mx = []
            for j in range(3):
              rot_mx += list(sym_op[j])
            trans_mx = sym_op[3]
            sym_ops.append(sgtbx.rt_mx(rot_mx, trans_mx))
          else:
            sym_ops.append(None)
        if sym_ops.count(None) == 2:
          rt_mx_ji = sgtbx.rt_mx() # unit matrix
        elif sym_ops.count(None) == 1:
          rt_mx_ji = sym_ops[1]
          if rt_mx_ji is None:
            rt_mx_ji = sym_ops[0]
            restraint_kwds['i_seqs'].reverse()
        else:
          rt_mx_ji_1 = sym_ops[0]
          rt_mx_ji_2 = sym_ops[1]
          rt_mx_ji_inv = rt_mx_ji_1.inverse()
          rt_mx_ji = rt_mx_ji_inv.multiply(rt_mx_ji_2)
        restraint_kwds['rt_mx_ji'] = rt_mx_ji
      builder.add_restraint(restraint_class, restraint_kwds)
  builder.finish_restraints()
  return builder

class refinement(manager):
  def __init__(self,
               f_obs = None,
               f_sq_obs = None,
               xray_structure = None,
               geometry_restraints_manager=None,
               geometry_restraints_flags=None,
               lambda_= None,
               max_cycles=50,
               max_peaks=30,
               verbose=1,
               log=None):
    manager.__init__(self,
                     f_obs=f_obs,
                     f_sq_obs=f_sq_obs,
                     xray_structure=xray_structure,
                     geometry_restraints_manager=geometry_restraints_manager,
                     geometry_restraints_flags=geometry_restraints_flags,
                     lambda_=lambda_,
                     max_cycles=max_cycles,
                     max_peaks=max_peaks,
                     verbose=verbose,
                     log=log)

  def get_difference_map(self, resolution=0.2):
    return self.f_obs_minus_f_calc_map(resolution).real_map()

  def fourier_map(self):
    fmap = self.f_obs.structure_factors_from_scatterers(
      xray_structure=self.xray_structure,
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
    for q,h in zip(peaks.sites(), peaks.heights()):
      yield q,h
