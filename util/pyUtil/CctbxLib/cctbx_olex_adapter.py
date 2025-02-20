import os, sys
import olx
import OlexVFS
import time
import math
from io import StringIO

from PeriodicTable import PeriodicTable
from functools import reduce
try:
  olx.current_hklsrc
except:
  olx.current_hklsrc = None
  olx.current_hklsrc_mtime = None
  olx.current_reflections = None
  olx.current_mask = None
  olx.current_space_group = None
  olx.current_observations = None

import olex
import olex_core

import time
import cctbx_controller as cctbx_controller
from cctbx import maptbx, miller, uctbx
from libtbx import easy_pickle, utils

from olexFunctions import OV
from scitbx.math import distributions

from History import hist

global twin_laws_d
twin_laws_d = {}

from scitbx.math import continued_fraction
from boost_adaptbx.boost import rational
from cctbx import sgtbx, xray
from cctbx.array_family import flex
import smtbx.utils

import numpy
import itertools
import operator
import fractions


def rt_mx_from_olx(olx_input):
  from libtbx.utils import flat_list
  return sgtbx.rt_mx(flat_list(olx_input[:-1]), olx_input[-1])

class twin_domains:
  def __init__(self, twin_axis, space, twin_law, twin_fraction, angle, fom, hklf5):
    self.space = space
    self.twin_axis = twin_axis
    self.twin_law = twin_law
    self.twin_fraction = twin_fraction
    self.angle = angle
    self.fom = fom
    self.hklf5 = hklf5


class OlexCctbxAdapter(object):
  def __init__(self, do_filter=True):
    import olexex
    if OV.HasGUI():
      sys.stdout.refresh = True
    self._xray_structure = None
    self._restraints_manager = None
    self.olx_atoms = olexex.OlexRefinementModel()
    self.wavelength = self.olx_atoms.exptl.get('radiation', 0.71073)
    self.reflections = None
    self.observations = None
    twinning=self.olx_atoms.model.get('twin')
    self.twin_fractions = None
    self.hklf_code = self.olx_atoms.model['hklf']['value']
    if twinning is not None:
      twin_fractions = flex.double(twinning['basf'])
      twin_law = sgtbx.rot_mx([int(float(twinning['matrix'][j][i])*1000)
                  for i in range(3) for j in range(3)], 1000)
      twin_multiplicity = twinning.get('n', 2)
      twin_laws = [twin_law]
      if twin_multiplicity > 2 or abs(twin_multiplicity) > 4:
        n = twin_multiplicity
        if twin_multiplicity < 0: n /= 2
        for i in range(n-2):
          twin_laws.append(twin_laws[-1].multiply(twin_law))
      if twin_multiplicity < 0:
        inv = sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1))
        twin_laws.append(inv)
        for law in twin_laws[:-1]:
          twin_laws.append(law.multiply(inv))
      if len(twin_fractions) == 0:
        # perfect twinning
        # SHELX manual pages 7-6/7
        n = abs(twin_multiplicity)
        twin_fractions = flex.double([1/n]*(n-1))
        grad_twin_fractions = [False] * (n-1)
      else:
        grad_twin_fractions = [True] * len(twin_fractions)
      if self.hklf_code == 5:
        batch_cnt = len(twin_fractions)-len(twin_laws)
        assert batch_cnt > 0
        self.twin_fractions = tuple(
          [ xray.twin_fraction(twin_fractions[i],True)
            for i in range(batch_cnt)])
        self.twin_components = tuple(
          [xray.twin_component(law, fraction, grad)
           for law, fraction, grad in zip(
             twin_laws, twin_fractions[batch_cnt:], grad_twin_fractions)])
      else:
        assert len(twin_fractions) == abs(twin_multiplicity) - 1
        assert len(twin_fractions) == len(twin_laws)
        self.twin_components = tuple(
          [xray.twin_component(law, fraction, grad)
           for law, fraction, grad in zip(
             twin_laws, twin_fractions, grad_twin_fractions)])
    else:
      olx_tw_f = self.olx_atoms.model['hklf'].get('basf',None)
      if self.hklf_code == 5 and olx_tw_f is not None:
        twin_fractions = flex.double(olx_tw_f)
        self.twin_fractions = tuple(
          [ xray.twin_fraction(fraction,True)
            for fraction in twin_fractions])
      self.twin_components = None

    self.exti = self.olx_atoms.model.get('exti', None)
    self.swat = self.olx_atoms.model.get('swat', None)
    self.initialise_reflections(doFilter=do_filter)
    from connectivity_table import connectivity_table
    self.connectivity_table = connectivity_table(self.xray_structure(), self.olx_atoms)

  def __del__(self):
    #sys.stdout.refresh = False
    return

  def xray_structure(self, construct_restraints=False, shared_parameters=None,
                     space_group=None):
    if space_group is None:
      space_group = self.space_group
    if self._xray_structure is None or construct_restraints:
      if construct_restraints:
        restraints_iter=self.olx_atoms.restraints_iterator(
          self.connectivity_table.pair_sym_table,
          shared_parameters=shared_parameters)
        same_iter = self.olx_atoms.same_iterator()
      else:
        restraints_iter = None
        same_iter = None
      create_cctbx_xray_structure = cctbx_controller.create_cctbx_xray_structure(
        self.cell,
        space_group,
        self.olx_atoms.iterator(use_charges=True),
        restraints_iter=restraints_iter,
        constraints_iter=None, #self.olx_atoms.constraints_iterator()
        same_iter=same_iter
      )
      if construct_restraints:
        from smtbx.refinement import restraints
        proxies = create_cctbx_xray_structure.restraint_proxies()
        kwds = dict([(key+"_proxies", value) for key, value in proxies.items()])
        self._restraints_manager = restraints.manager(**kwds)
        self.constraints = create_cctbx_xray_structure.builder.constraints
      self._xray_structure = create_cctbx_xray_structure.structure()
      table = OV.GetParam("snum.smtbx.atomic_form_factor_table")
      null_disp = table == "electron" or table == "neutron"
      sfac = self.olx_atoms.model.get('sfac')
      custom_gaussians = {}
      custom_fp_fdps = {}
      inelastic_table = None
      #  default for DISP first
      if self.reflections._merge < 4:
        from cctbx.eltbx import wavelengths
        inelastic_table = OV.GetParam("snum.smtbx.inelastic_form_factor_table")
        if inelastic_table != "brennan":
          try:
            self._xray_structure.set_inelastic_form_factors(
              self.wavelength, inelastic_table)
          except Exception as e:
            if OV.IsDebugging():
              print("Failed to retrieve some inelastic scattering factors")
              print(e)
          for sc in self._xray_structure.scatterers():
            if null_disp:
              custom_fp_fdps.setdefault(sc.scattering_type, (0.0, 0.0))
            else:
              custom_fp_fdps.setdefault(sc.scattering_type, (sc.fp, sc.fdp))
        else:
          try:
            from brennan import brennan
            br = brennan()
            for sc in self._xray_structure.scatterers():
              if null_disp:
                custom_fp_fdps.setdefault(sc.scattering_type, (0.0, 0.0))
              else:
                scattering_type = 'H' if sc.scattering_type =='D' else sc.scattering_type
                fp_fdp = br.at_angstrom(self.wavelength, scattering_type)
                sc.fp, sc.fdp = fp_fdp
                custom_fp_fdps.setdefault(sc.scattering_type, (fp_fdp[0], fp_fdp[1]))
          except Exception as exc:
            print("Error: Brennan & Cowan failed (%s), switching to Sasaki!" %str(exc))
            inelastic_table = "sasaki"
            try:
              self._xray_structure.set_inelastic_form_factors(
                        self.wavelength, inelastic_table)
            except Exception as e:
              if OV.IsDebugging():
                print("Failed to retrieve some inelastic scattering factors")
                print(e)
            for sc in self._xray_structure.scatterers():
              if null_disp:
                custom_fp_fdps.setdefault(sc.scattering_type, (0.0, 0.0))
              else:
                custom_fp_fdps.setdefault(sc.scattering_type, (sc.fp, sc.fdp))
      if sfac is not None:
        from cctbx import eltbx
        for element, sfac_dict in sfac.items():
          if len(element) > 1:
            element = element.upper()[0] + element.lower()[1:]
          if 'gaussian' in sfac_dict:
            custom_gaussians.setdefault(element, eltbx.xray_scattering.gaussian(
              sfac_dict['gaussian'][0],
              [-b for b in sfac_dict['gaussian'][1]],
              sfac_dict['gaussian'][2]))
          custom_fp_fdps[element] = sfac_dict['fpfdp']
      if null_disp == True:
        inelastic_table = "custom"
      self._xray_structure.set_custom_inelastic_form_factors(
        custom_fp_fdps, source=inelastic_table)
      if table == "electron" and OV.GetParam("snum.smtbx.electron_table_name") == "Peng-1996":
        if OV.GetParam("snum.refinement.program").startswith("olex2.refine"):
          custom_gaussians = {}
          print("Custom gaussians will not be used for the refinement! Using 5-Gaussian Peng-1996")
      self._xray_structure.scattering_type_registry(
        custom_dict=custom_gaussians,
        table=str(table),
        d_min=self.reflections.f_sq_obs.d_min())
    # init disp
    for i, disp in self.olx_atoms.disp_iterator():
      sc = self._xray_structure.scatterers()[i]
      sc.fp, sc.fdp = disp
      sc.flags.set_grad_fp(True)
      sc.flags.set_grad_fdp(True)

    return self._xray_structure

  def restraints_manager(self):
    if self._restraints_manager is None:
      self.xray_structure(construct_restraints=True)
    return self._restraints_manager

  def initialise_reflections(self, force=False, verbose=False, doFilter=True):
    self.cell = self.olx_atoms.getCell()
    self.space_group = "hall: "+str(olx.xf.au.GetCellSymm("hall"))
    hklf_matrix = utils.flat_list(self.olx_atoms.model['hklf']['matrix'])
    mx = [ continued_fraction.from_real(e, eps=1e-3).as_rational()
           for e in hklf_matrix ]
    den = reduce(rational.lcm, [ r.denominator() for r in mx ])
    nums = [ r.numerator()*(den//r.denominator()) for r in mx ]
    hklf_matrix = sgtbx.rot_mx(nums, den)
    reflections = olx.HKLSrc()
    if reflections:
      mtime = os.path.getmtime(reflections)
    else:
      mtime = time.time()
    merge_code = self.olx_atoms.model.get('merge')
    if (force or
        reflections != olx.current_hklsrc or
        mtime != olx.current_hklsrc_mtime or
        olx.current_reflections.hklf_code != self.hklf_code or
        (olx.current_reflections is not None and merge_code != olx.current_reflections._merge) or
        (olx.current_reflections is not None and
          (hklf_matrix != olx.current_reflections.hklf_matrix
            or self.space_group != olx.current_space_group))):
      olx.current_hklsrc = reflections
      olx.current_hklsrc_mtime = mtime
      olx.current_space_group = self.space_group
      olx.current_reflections = cctbx_controller.reflections(
        self.cell, self.space_group, reflections,
        hklf_code=self.hklf_code,
        hklf_matrix=hklf_matrix,
        merge_code=merge_code)
      olx.current_observations = None
    if olx.current_reflections and doFilter:
      self.reflections = olx.current_reflections
      self.observations = olx.current_observations
      if self.observations is not None:
        if not self.update_twinning(self.observations.ref_twin_fractions,
                                    self.observations.ref_twin_components):
          self.observations = None
        else:
          self.twin_fractions = self.observations.ref_twin_fractions
          self.twin_components = self.observations.ref_twin_components
    else:
      olx.current_reflections = cctbx_controller.reflections(
        self.cell, self.space_group, reflections,
        hklf_code=self.hklf_code,
        hklf_matrix=hklf_matrix,
        merge_code=merge_code)
      self.reflections = olx.current_reflections

    omit = self.olx_atoms.model['omit']
    shel = self.olx_atoms.model.get('shel', None)
    update = False
    if merge_code is None or merge_code != self.reflections._merge:
      self.reflections.merge(merge=merge_code)
      update = True
    if force or omit is None or omit != self.reflections._omit or shel != self.reflections._shel:
      update = True

    if update or self.observations is None:
      self.reflections.filter(omit, shel, self.olx_atoms.exptl['radiation'], doFilter=doFilter)
      self.observations = self.reflections.get_observations(
        self.twin_fractions, self.twin_components)
      olx.current_observations = self.observations

    if verbose:
      self.reflections.show_summary()

  def f_calc(self, miller_set,
             apply_extinction_correction=True,
             apply_twin_law=True,
             ignore_inversion_twin=False,
             one_h_function=None,
             algorithm="direct",
             twin_data=True):
    assert self.xray_structure().scatterers().size() > 0, "n_scatterers > 0"
    if not miller_set:
        miller_set_ = self.observations.unique_mapped_miller_set
    else:
      miller_set_ = miller_set
    if (ignore_inversion_twin
        and self.twin_components is not None
        and self.twin_components[0].twin_law.as_double() == sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1)).as_double()):
      apply_twin_law = False
    if (apply_twin_law
        and self.twin_components is not None):
      twin_sets = []
      #twin_component = self.twin_components[0]
      for twin_component in self.twin_components:
        twinning = cctbx_controller.hemihedral_twinning(
          twin_component.twin_law.as_double(), miller_set_)
        twin_sets.append(twinning.twin_complete_set)
      if len(twin_sets) > 1:
        twin_set = miller.union_of_sets(twin_sets)
      else:
        twin_set = twin_sets[0]
      if one_h_function:
        data = []
        for mi in twin_set.indices():
          one_h_function.evaluate(mi)
          data.append(one_h_function.f_calc)
        fc = twin_set.array(data=flex.complex_double(data))
      else:
        fc = twin_set.structure_factors_from_scatterers(
          self.xray_structure(), algorithm=algorithm).f_calc()
      if twin_data:
        assert len(twin_sets) == 1
        value = twin_component.value
        if value < 0: value = 0
        elif value > 1: value = 1
        twinned_fc2 = twinning.twin_with_twin_fraction(
          fc.as_intensity_array(), value)
        if miller_set:
          fc = twinned_fc2.f_sq_as_f().phase_transfer(fc).common_set(miller_set)
        else:
          fc = twinned_fc2.f_sq_as_f().phase_transfer(fc)
    else:
      if one_h_function:
        data = []
        for mi in miller_set_.indices():
          one_h_function.evaluate(mi)
          data.append(one_h_function.f_calc)
        fc = miller_set_.array(data=flex.complex_double(data), sigmas=None)
      else:
        fc = miller_set_.structure_factors_from_scatterers(
          self.xray_structure(), algorithm=algorithm).f_calc()
    if apply_extinction_correction and self.exti is not None:
      fc = fc.apply_shelxl_extinction_correction(self.exti, self.wavelength)
    return fc

  def get_one_h_function(self, table_file_name):
    return get_one_h_function(self.xray_structure(), table_file_name)

  def get_shelxl_weighting(self):
    from smtbx.refinement import least_squares
    weight = self.olx_atoms.model['weight']
    params = dict(a=0.1, b=0,
                  #c=0, d=0, e=0, f=1./3,
                  )
    for param, value in zip(list(params.keys())[:min(2, len(weight))], weight):
      params[param] = value
    return least_squares.mainstream_shelx_weighting(**params)

  def compute_weights(self, fo2, fc):
    weight = self.olx_atoms.model['weight']
    params = [0.1, 0, 0, 0, 0, 1./3]
    for i, v in enumerate(weight):
      params[i] = v
    weighting = xray.weighting_schemes.shelx_weighting(*params,
      wavelength=self.wavelength)
    #scale_factor = fo2.scale_factor(fc)
    scale_factor = OV.GetOSF()
    weighting.observed = fo2
    weighting.compute(fc, scale_factor)
    return weighting.weights

  def load_mask(self):
    fab_path = os.path.splitext(OV.HKLSrc())[0] + ".fab"
    if os.path.exists(fab_path):
      with open(fab_path) as fab:
        indices = []
        data = []
        for l in fab.readlines():
          fields = l.split()
          if len(fields) < 5:
            break
          try:
            idx = (int(fields[0]), int(fields[1]), int(fields[2]))
            if idx == (0,0,0):
              break
            indices.append(idx)
            data.append(complex(float(fields[3]), float(fields[4])))
          except:
            pass
      miller_set = miller.set(
        crystal_symmetry=self.xray_structure().crystal_symmetry(),
        indices=flex.miller_index(indices)).auto_anomalous()
      return miller.array(miller_set=miller_set, data=flex.complex_double(data)).map_to_asu()
    mask_fn = os.path.join(OV.StrDir(), OV.FileName())+"-f_mask.pickle"
    if os.path.exists(mask_fn):
      return easy_pickle.load(mask_fn)
    import olex_core
    mask = olex_core.GetMask()
    if mask is None:
      return None
    miller_set = miller.set(
      crystal_symmetry=self.xray_structure().crystal_symmetry(),
      indices=flex.miller_index(mask[0])).auto_anomalous()
    return miller.array(miller_set=miller_set, data=flex.complex_double(mask[1])).map_to_asu()

  def get_fo_sq_fc(self, one_h_function=None, filtered=True, merge=True):
    if filtered:
      fo2 = self.reflections.f_sq_obs_filtered
    else:
      fo2 = self.reflections.f_sq_obs_merged
    miller_set = None
    if one_h_function:
      try:
        fc = self.f_calc(miller_set, self.exti is not None, True, False,
                       one_h_function=one_h_function, twin_data=False)
      except Exception as e:
        print("Error during calculation of F_calcs: %s"%(str(e)))
        return None, None
    else:
      fc = self.f_calc(miller_set, self.exti is not None, True,
       ignore_inversion_twin=False,
       twin_data=False)
    obs = self.observations.detwin(
      fo2.crystal_symmetry().space_group(),
      fo2.anomalous_flag(),
      fc.indices(),
      fc.as_intensity_array().data())
    fo2 = miller.array(
        miller_set=miller.set(
          crystal_symmetry=fo2.crystal_symmetry(),
          indices=obs.indices,
          anomalous_flag=fo2.anomalous_flag()),
        data=obs.data,
        sigmas=obs.sigmas).set_observation_type(fo2)
    if self.hklf_code < 5 or merge:
      fo2 = fo2.merge_equivalents(algorithm="shelx").array().map_to_asu()
      fc = fc.common_set(fo2)
      if fc.size() != fo2.size():
        fo2 = fo2.common_set(fc)
    else:
      lt = miller.lookup_tensor(fc.indices(), fc.space_group(), fc.anomalous_flag())
      fc_data_ = fc.data()
      fc_data = []
      for h in fo2.indices():
        fc_data.append(fc_data_[lt.find_hkl(h)])
      fc = miller.array(
          miller_set=miller.set(
            crystal_symmetry=fc.crystal_symmetry(),
            indices=fo2.indices(),
            anomalous_flag=fc.anomalous_flag()),
          data=flex.complex_double(fc_data))\
            .set_observation_type(fo2)
    return (fo2, fc)

  def update_twinning(self, tw_f, tw_c):
    if self.twin_fractions is not None:
      if tw_f is None or len(tw_f) != len(self.twin_fractions):
        return False
      for i,f in enumerate(self.twin_fractions):
        tw_f[i].value = f.value
    elif tw_f is not None:
      return False

    if self.twin_components is not None:
      if tw_c is None or len(tw_c) != len(self.twin_components):
        return False
      for i,f in enumerate(self.twin_components):
        if f.twin_law != tw_c[i].twin_law:
          return False
        tw_c[i].value = f.value
    elif tw_c is not None:
      return False
    return True

def write_fab(f_mask, fab_path=None):
  if not fab_path:
    fab_path = os.path.splitext(OV.HKLSrc())[0] + ".fab"
  with open(fab_path, "w") as f:
    for i,h in enumerate(f_mask.indices()):
      line = "%d %d %d " %h + "%.4f %.4f" % (f_mask.data()[i].real, f_mask.data()[i].imag)
      print(line, file=f)
    print("0 0 0 0.0 0.0", file=f)

from smtbx import absolute_structure

class hooft_analysis(absolute_structure.hooft_analysis):
  def __init__(self, olex2_adaptor=None, probability_plot_slope=None, use_fcf=False):
    self.olex2_adaptor = olex2_adaptor
    if self.olex2_adaptor is None:
      self.olex2_adaptor = OlexCctbxAdapter()
    self.reflections = self.olex2_adaptor.reflections
    if probability_plot_slope is not None:
      probability_plot_slope = float(probability_plot_slope)
    if use_fcf:
      fcf_path = OV.file_ChangeExt(OV.FileFull(), "fcf")
      if not os.path.exists(fcf_path):
        print("No fcf file is present")
        return
      reflections = list(miller.array.from_cif(file_path=str(fcf_path)).values())[0]
      try:
        fo2 = reflections['_refln_F_squared_meas']
        fc2 = reflections['_refln_F_squared_calc']
      except:
        print('Unsupported format, _refln_F_squared_meas and " +\
        "_refln_F_squared_calc is expected')
        return
      fc = fc2.f_sq_as_f().phase_transfer(flex.double(fc2.size(), 0))
      if self.hklf_code == 5:
        fo2 = fo2.merge_equivalents(algorithm="shelx").array().map_to_asu()
        fc = fc.common_set(fo2)
      scale = 1
    else:
      fo2, fc = self.olex2_adaptor.get_fo_sq_fc()
      weights = self.olex2_adaptor.compute_weights(fo2, fc)
      scale = fo2.scale_factor(fc, weights=weights)
    if not fo2.anomalous_flag():
      print("No Bijvoet pairs")
      return
    absolute_structure.hooft_analysis.__init__(
      self, fo2, fc, probability_plot_slope=probability_plot_slope, scale_factor=scale)

OV.registerFunction(hooft_analysis)

class students_t_hooft_analysis(OlexCctbxAdapter, absolute_structure.students_t_hooft_analysis):
  def __init__(self, nu=None, use_fcf=False):
    OlexCctbxAdapter.__init__(self)
    if use_fcf:
      fcf_path = OV.file_ChangeExt(OV.FileFull(), "fcf")
      if not os.path.exists(fcf_path):
        print("No fcf file is present")
        return
      reflections = miller.array.from_cif(file_path=str(fcf_path))
      fo2 = reflections['_refln_F_squared_meas']
      fc2 = reflections['_refln_F_squared_calc']
      fc = fc2.f_sq_as_f().phase_transfer(flex.double(fc2.size(), 0))
      scale = 1
    else:
      fo2 = self.reflections.f_sq_obs_filtered
      fc = self.f_calc(miller_set=fo2, ignore_inversion_twin=True)
      weights = self.compute_weights(fo2, fc)
      scale = fo2.scale_factor(fc, weights=weights)
    if not fo2.anomalous_flag():
      print("No Bijvoet pairs")
      return
    analysis = absolute_structure.hooft_analysis(fo2, fc, scale_factor=scale)
    bijvoet_diff_plot = absolute_structure.bijvoet_differences_probability_plot(
      analysis)
    if nu is not None:
      nu = float(nu)
    else:
      nu = absolute_structure.maximise_students_t_correlation_coefficient(
        bijvoet_diff_plot.y, 1, 300)
    distribution = distributions.students_t_distribution(nu)
    observed_deviations = bijvoet_diff_plot.y
    expected_deviations = distribution.quantiles(observed_deviations.size())
    fit = flex.linear_regression(
      expected_deviations[5:-5], observed_deviations[5:-5])
    self.slope = fit.slope()
    print("Student's t nu: %.1f" %nu)
    absolute_structure.students_t_hooft_analysis.__init__(
      self, fo2, fc, nu, scale_factor=scale, probability_plot_slope=self.slope)

OV.registerFunction(students_t_hooft_analysis)


class OlexCctbxSolve(OlexCctbxAdapter):
  def __init__(self):
    OlexCctbxAdapter.__init__(self)
    self.peak_normaliser = 1200 #fudge factor to get cctbx peaks on the same scale as shelx peaks

  def runChargeFlippingSolution(self, verbose="highly", solving_interval=60):
    import time
    t1 = time.time()
    from smtbx.ab_initio import charge_flipping

    from libtbx import group_args

    t2 = time.time()
    print('imports took %0.3f ms' %((t2-t1)*1000.0))
    # Get the reflections from the specified path
    f_obs = self.reflections.f_obs
    data = self.reflections.f_sq_obs

    # merge them (essential!!)
    merging = f_obs.merge_equivalents()
    f_obs = merging.array()
    f_obs.show_summary()

    # charge flipping iterations
    flipping = charge_flipping.weak_reflection_improved_iterator(delta=None)

    params = OV.Params().programs.solution.smtbx.cf
    extra = group_args(
      max_attempts_to_get_phase_transition\
        = params.max_attempts_to_get_phase_transition,
      max_attempts_to_get_sharp_correlation_map \
        = params.max_attempts_to_get_sharp_correlation_map,
      max_solving_iterations=params.max_solving_iterations)
    if params.amplitude_type == 'E':
      formula = {}
      for element in str(olx.xf.GetFormula('list')).split(','):
        element_type, n = element.split(':')
        formula.setdefault(element_type, float(n))
      extra.normalisations_for = lambda f: f.amplitude_normalisations(formula)
    elif params.amplitude_type == 'quasi-E':
      extra.normalisations_for = charge_flipping.amplitude_quasi_normalisations

    solving = charge_flipping.solving_iterator(
      flipping,
      f_obs,
      yield_during_delta_guessing=True,
      yield_solving_interval=solving_interval,
      **extra.__dict__
    )
    charge_flipping_loop(solving, verbose=verbose)
    # play with the solutions
    expected_peaks = f_obs.unit_cell().volume()/18.6/len(f_obs.space_group())
    expected_peaks *= 1.3
    if solving.f_calc_solutions:
      # actually only the supposedly best one
      f_calc, shift, cc_peak_height = solving.f_calc_solutions[0]
      fft_map = f_calc.fft_map(
        symmetry_flags=maptbx.use_space_group_symmetry)
      fft_map.apply_volume_scaling()
      # search and print Fourier peaks
      peaks = fft_map.peak_search(
        parameters=maptbx.peak_search_parameters(
          min_distance_sym_equiv=1.0,
          max_clusters=expected_peaks,),
        verify_symmetry=False
        ).all()
      for xyz, height in zip(peaks.sites(), peaks.heights()):
        if not xyz:
          have_solution = False
          break
        else:
          self.post_single_peak(xyz, height)
      have_solution = True
    else: have_solution = False
    return have_solution

  def post_single_peak(self, xyz, height, cutoff=1.0):
#    if height/self.peak_normaliser < cutoff:
#      return
#    sp = (height/self.peak_normaliser)
    sp = height #hp
    id = olx.xf.au.NewAtom("%.2f" %(sp), *xyz)
    if id != '-1':
      olx.xf.au.SetAtomU(id, "0.06")

class OlexCctbxMasks(OlexCctbxAdapter):

  def __init__(self, recompute=True, show=False):
    OlexCctbxAdapter.__init__(self)
    from cctbx import miller
    from smtbx import masks
    from cctbx.masks import flood_fill
    from libtbx.utils import time_log

    OV.CreateBitmap("working")

    self.time_total = time_log("total time").start()

    self.params = OV.Params().snum.masks

    if recompute in ('false', 'False'): recompute = False
    map_type = self.params.type
    filepath = OV.StrDir()
    pickle_path = '%s/%s-%s.pickle' %(filepath, OV.FileName(), map_type)
    if os.path.exists(pickle_path) and not recompute:
      data = easy_pickle.load(pickle_path)
      crystal_gridding = maptbx.crystal_gridding(
        unit_cell=self.xray_structure().unit_cell(),
        space_group_info=self.xray_structure().space_group_info(),
        d_min=self.reflections.f_sq_obs_filtered.d_min(),
        resolution_factor=self.params.resolution_factor,
        symmetry_flags=sgtbx.search_symmetry_flags(
          use_space_group_symmetry=True))
    else: data = None

    if recompute or data is None:
      # remove modified hkl (for shelxl) if we are recomputing the mask
      # and change back to original hklsrc
      modified_hkl_path = "%s/%s-mask.hkl" %(OV.FilePath(), OV.FileName())
      if os.path.exists(modified_hkl_path):
        os.remove(modified_hkl_path)
        original_hklsrc = OV.GetParam('snum.masks.original_hklsrc')
        if OV.HKLSrc() == modified_hkl_path and original_hklsrc is not None:
          OV.HKLSrc(original_hklsrc)
          OV.UpdateHtml()
          # we need to reinitialise reflections
          self.initialise_reflections()
      xs = self.xray_structure()
      fo_sq = self.reflections.f_sq_obs_merged.average_bijvoet_mates()
      use_set_completion = OV.GetParam('snum.masks.use_set_completion')
      mask = masks.mask(xs, fo_sq, use_set_completion=use_set_completion)
      self.time_compute = time_log("computation of mask").start()
      mask.compute(solvent_radius=self.params.solvent_radius,
                   shrink_truncation_radius=self.params.shrink_truncation_radius,
                   resolution_factor=self.params.resolution_factor,
                   atom_radii_table=olex_core.GetVdWRadii(),
                   use_space_group_symmetry=True)
      self.time_compute.stop()
      self.time_f_mask = time_log("f_mask calculation").start()
      self.structure_factors(mask)
      self.time_f_mask.stop()
      olx.current_mask = mask
      if mask.flood_fill.n_voids() > 0:
        write_fab(mask.f_mask())
      out = StringIO()
      fo2 = self.reflections.f_sq_obs
      fo2.show_comprehensive_summary(f=out)
      print(file=out)
      mask.show_summary(log=out)
      from iotbx.cif import model
      cif_block = model.block()
      #merging = self.reflections.merging
      #min_d_star_sq, max_d_star_sq = fo2.min_max_d_star_sq()
      #(h_min, k_min, l_min), (h_max, k_max, l_max) = fo2.min_max_indices()
      with open('%s/%s-mask.log' %(OV.FilePath(), OV.FileName()),'w') as f:
        print(out.getvalue(), file=f)
      print(out.getvalue())
      cif_block['_smtbx_masks_void_probe_radius'] = self.params.solvent_radius
      cif_block['_smtbx_masks_void_truncation_radius'] = self.params.shrink_truncation_radius

      mdict = mask.as_cif_block()
      _ = None
      try:
        _ = olx.cif_model[OV.ModelSrc()].get('_smtbx_masks_void_content')
        if _:
          if not _.is_trivial_1d():
            cif_block['_smtbx_masks_void_content'] = _
      except:
        pass

      if _ and '_smtbx_masks_void_content' in list(mdict.keys()) and len(_) == len(mdict['_smtbx_masks_void_content']):
        mdict['_smtbx_masks_void_content'] = _

      cif_block.update(mdict)
      cif = model.cif()
      data_name = OV.FileName().replace(' ', '')
      cif[data_name] = cif_block

      mask_cif_path = os.path.splitext(OV.HKLSrc())[0] + ".sqf"
      with open(mask_cif_path, 'w') as f:
        print(cif, file=f)
      OV.SetParam('snum.masks.update_cif', True)
      data = None
    else:
      mask = olx.current_mask
    if self.params.type == "mask":
      if data: output_data = data
      else: output_data = mask.mask.data
    else:
      if not data:
        crystal_gridding = mask.crystal_gridding
        if self.params.type == "f_mask":
          data = mask.f_mask()
        elif self.params.type == "f_model":
          data = mask.f_model()
      if not data:
        print('Empty mask')
        return
      model_map = miller.fft_map(crystal_gridding, data)
      output_data = model_map.apply_volume_scaling().real_map()
    self.time_write_grid = time_log("write grid").start()
    if OV.HasGUI() and show:
      write_grid_to_olex(output_data)
    self.time_write_grid.stop()

  def structure_factors(self, mask, max_cycles=100):
    """P. van der Sluis and A. L. Spek, Acta Cryst. (1990). A46, 194-201."""
    from scitbx.math import approx_equal_relatively
    from libtbx.utils import xfrange
    from smtbx.structure_factors import direct
    assert mask.mask is not None
    if mask.n_voids() == 0: return
    if mask.use_set_completion:
      f_calc_set = mask.complete_set
    else:
      f_calc_set = mask.fo2.set()
    use_tsc = OV.IsNoSpherA2()
    if use_tsc == True:
      table_name = str(OV.GetParam("snum.NoSpherA2.file"))
      xray_structure = mask.xray_structure
      one_h = direct.f_calc_modulus_squared(
        xray_structure, table_file_name=table_name)
      mask.f_calc = self.f_calc(f_calc_set, one_h_function=one_h)
    else:
      mask.f_calc = f_calc_set.structure_factors_from_scatterers(
        mask.xray_structure, algorithm="direct").f_calc()
    f_obs = mask.f_obs()
    mask.scale_factor = flex.sum(f_obs.data())/flex.sum(
      flex.abs(mask.f_calc.data()))
    f_obs_minus_f_calc = f_obs.f_obs_minus_f_calc(
      1/mask.scale_factor, mask.f_calc)
    mask.fft_scale = mask.xray_structure.unit_cell().volume()\
        / mask.crystal_gridding.n_grid_points()
    epsilon_for_min_residual = 2
    grid_points_per_void = mask.flood_fill.grid_points_per_void()
    n_solvent_grid_points = mask.n_solvent_grid_points()
    prev_x = mask.n_voids() * [0]
    mask._electron_counts_per_void = mask.n_voids() * [0]
    grid_scale = mask.crystal_gridding.n_grid_points() /\
      (mask.crystal_gridding.n_grid_points() - n_solvent_grid_points)
    for i in range(max_cycles):
      mask.diff_map = miller.fft_map(mask.crystal_gridding, f_obs_minus_f_calc)
      mask.diff_map.apply_volume_scaling()
      #stats = mask.diff_map.statistics()
      masked_diff_map = mask.diff_map.real_map_unpadded().set_selected(
        mask.mask.data.as_double() == 0, 0)
      mask.f_000 = 0
      for j in range(mask.n_voids()):
        # exclude voids with negative electron counts from the masked map
        # set the electron density in those areas to be zero
        selection = mask.mask.data == j+2
        if mask.exclude_void_flags[j]:
          masked_diff_map.set_selected(selection, 0)
          continue
        diff_map_ = masked_diff_map.deep_copy().set_selected(~selection, 0)
        f_000 = flex.sum(diff_map_) * mask.fft_scale
        f_000_s = f_000 * grid_scale
        if i > 0:
          if f_000_s - prev_x[j] < 0.1:
            if f_000_s < 0:
              masked_diff_map.set_selected(selection, 0)
              mask.exclude_void_flags[j] = True
              mask._electron_counts_per_void[j] = 0
              n_solvent_grid_points -= grid_points_per_void[j]
              grid_scale = mask.crystal_gridding.n_grid_points() /\
                (mask.crystal_gridding.n_grid_points() - n_solvent_grid_points)
            prev_x[j] = f_000_s
            continue
        mask.f_000 += f_000
        prev_x[j] = f_000_s
        if OV.IsEDData():
          mask._electron_counts_per_void[j] = f_000_s * 3.324943664
        else:
          mask._electron_counts_per_void[j] = f_000_s

      #mask.f_000 = flex.sum(masked_diff_map) * mask.fft_scale
      f_000_s = mask.f_000 * grid_scale
      if (mask.f_000_s is not None and
          approx_equal_relatively(mask.f_000_s, f_000_s, 0.001)):
        mask.f_000_s = f_000_s
        break # we have reached convergence
      else:
        mask.f_000_s = f_000_s
      masked_diff_map.add_selected(
        mask.mask.data.as_double() > 0,
        mask.f_000_s/mask.xray_structure.unit_cell().volume())
      mask._f_mask = f_obs.structure_factors_from_map(map=masked_diff_map)
      mask._f_mask *= mask.fft_scale
      scales = []
      residuals = []
      min_residual = 1000
      for epsilon in xfrange(epsilon_for_min_residual, 0.9, -0.2):
        f_model_ = mask.f_model(epsilon=epsilon)
        scale = flex.sum(f_obs.data())/flex.sum(flex.abs(f_model_.data()))
        scaled_fobs_abs = 1/scale * flex.abs(f_obs.data())
        residual = flex.sum(
          flex.abs(scaled_fobs_abs- flex.abs(f_model_.data())))\
           / flex.sum(scaled_fobs_abs)
        scales.append(scale)
        residuals.append(residual)
        min_residual = min(min_residual, residual)
        if min_residual == residual:
          scale_for_min_residual = scale
          epsilon_for_min_residual = epsilon
      mask.scale_factor = scale_for_min_residual
      f_model = mask.f_model(epsilon=epsilon_for_min_residual)
      f_obs = mask.f_obs()
      f_obs_minus_f_calc = f_obs.phase_transfer(f_model).f_obs_minus_f_calc(
        1/mask.scale_factor, mask.f_calc)
    #make sure sum matches the summary
    mask.f_000_s = 0
    for j in range(mask.n_voids()):
      mask._electron_counts_per_void[j] = round(mask._electron_counts_per_void[j], 1)
      mask.f_000_s += mask._electron_counts_per_void[j]
    return mask._f_mask


  def __del__(self):
    OV.DeleteBitmap("working")

OV.registerFunction(OlexCctbxMasks)

def charge_flipping_loop(solving, verbose=True):
  HasGUI = OV.HasGUI()
  plot = None
  timing = True
  if timing:
    t0 = time.time()
  if HasGUI and OV.GetParam('snum.solution.graphical_output'):
    import Analysis
    plot = Analysis.ChargeFlippingPlot()
  OV.SetVar('stop_current_process',False)

  previous_state = None
  for flipping in solving:
    if OV.FindValue('stop_current_process',False):
      break
    if solving.state is solving.guessing_delta:
      # Guessing a value of delta leading to subsequent good convergence
      if verbose:
        if previous_state is solving.solving:
          print("** Restarting (no phase transition) **")
        elif previous_state is solving.evaluating:
          print("** Restarting (no sharp correlation map) **")
      if verbose == "highly":
        if previous_state is not solving.guessing_delta:
          print("Guessing delta...")
          print("%10s | %10s | %10s | %10s | %10s | %10s | %10s"
                 % ('delta', 'delta/sig', 'R', 'F000',
                    'c_tot', 'c_flip', 'c_tot/c_flip'))
          print("-"*90)
        rho = flipping.rho_map
        c_tot = rho.c_tot()
        c_flip = rho.c_flip(flipping.delta)
        # to compare with superflip output
        c_tot *= flipping.fft_scale; c_flip *= flipping.fft_scale
        print("%10.4f | %10.4f | %10.3f | %10.3f | %10.1f | %10.1f | %10.2f"\
              % (flipping.delta, flipping.delta/rho.sigma(),
                 flipping.r1_factor(), flipping.f_000,
                 c_tot, c_flip, c_tot/c_flip))

    elif solving.state is solving.solving:
      # main charge flipping loop to solve the structure
      if verbose=="highly":
        if previous_state is not solving.solving:
          print()
          print("Solving...")
          print("with delta=%.4f" % flipping.delta)
          print()
          print("%5s | %10s | %10s" % ('#', 'F000', 'skewness'))
          print('-'*33)
        print("%5i | %10.1f | %10.3f" % (solving.iteration_index,
                                         flipping.f_000,
                                         flipping.rho_map.skewness()))

    elif solving.state is solving.polishing:
      if verbose == 'highly':
        print()
        print("Polishing")
    elif solving.state is solving.finished:
      break

    if plot is not None: plot.run_charge_flipping_graph(flipping, solving, previous_state)
    previous_state = solving.state

  if timing:
    print("Total Time: %.2f s" %(time.time() - t0))


def write_grid_to_olex(grid):
  import olex_xgrid
  gridding = grid.accessor()
  type = isinstance(grid, flex.int)
  olex_xgrid.Import(
    gridding.all(), gridding.focus(), grid.copy_to_byte_str(), type)
  olex_xgrid.SetMinMax(flex.min(grid), flex.max(grid))
  olex_xgrid.SetVisible(True)
  olex_xgrid.InitSurface(True)


class as_pdb_file(OlexCctbxAdapter):
  def __init__(self, filepath=None,
      remark=None, remarks=[], fractional_coordinates=False, resname=None):
    if not filepath:
      filepath = OV.file_ChangeExt(OV.FileFull(), 'pdb')
    OlexCctbxAdapter.__init__(self)
    fractional_coordinates = fractional_coordinates in (True, 'True', 'true')
    with open(filepath, 'w') as f:
      print(self.xray_structure().as_pdb_file(
        remark=remark,
        remarks=remarks,
        fractional_coordinates=fractional_coordinates,
        resname=resname), file=f)

OV.registerMacro(as_pdb_file, """\
filepath&;remark&;remarks&;fractional_coordinates-(False)&;resname""")

class symmetry_search(OlexCctbxAdapter):
  def __init__(self):
    OlexCctbxAdapter.__init__(self)
    from cctbx import symmetry_search
    xs = self.xray_structure()
    xs_p1 = xs.expand_to_p1()
    fo_sq = self.reflections.f_sq_obs.customized_copy(
      anomalous_flag=False).expand_to_p1().merge_equivalents().array()
    fo_in_p1 = fo_sq.as_amplitude_array()
    fc_in_p1 = fo_in_p1.structure_factors_from_scatterers(
      xray_structure=xs_p1,
      algorithm="direct").f_calc()
    fo_complex_in_p1 = fo_in_p1.phase_transfer(fc_in_p1).customized_copy(
      sigmas=None)
    #sf_symm = symmetry_search.structure_factor_symmetry(fo_complex_in_p1)
    fc_in_p1 = miller.build_set(
      crystal_symmetry=xs_p1,
      anomalous_flag=False,d_min=fo_sq.d_min()
      ).structure_factors_from_scatterers(
        xray_structure=xs_p1,
        algorithm="direct").f_calc()
    sf_symm = symmetry_search.structure_factor_symmetry(fc_in_p1)
    print(sf_symm)
    sf_symm.space_group_info.show_summary()

OV.registerFunction(symmetry_search)

def calcsolv(solvent_radius=None, grid_step=None):
  # This routine called with spy.calsolv() will calculate the solvent accessible area

  # If values have been set in PHIL, these will be used.

  l = ['grid', 'probe']
  for item in l:
    val = OV.GetParam('snum.calcsolv.%s' %item)
    if val:
      if item == 'probe':
        if not solvent_radius:
          solvent_radius = val
        else:
          OV.SetParam('snum.calcsolv.%s'%item,solvent_radius)
          if OV.IsControl('SET_SNUM_CALCSOLV_PROBE'):
            olx.html.SetValue('SET_SNUM_CALCSOLV_PROBE', solvent_radius)

      elif item == 'grid':
        if not grid_step:
          grid_step = val
        else:
          OV.SetParam('snum.calcsolv.%s'%item,grid_step)
          if OV.IsControl('SET_SNUM_CALCSOLV_Grid'):
            olx.html.SetValue('SET_SNUM_CALCSOLV_GRID', grid_step)
    else:
      if item == 'probe':
        if not solvent_radius:
          solvent_radius = 1.2
      elif item == 'grid':
        if not solvent_radius:
          solvent_radius = 0.2

  from smtbx.masks import solvent_accessible_volume
  import olexex
  # Used to build the xray_structure by getting information from the olex2 refinement model
  olx_atoms = olexex.OlexRefinementModel()
  unit_cell = olx_atoms.getCell()
  constraints_iter=None
  space_group = "hall: "+str(olx.xf.au.GetCellSymm("hall"))

  # Creating the xray_structure part
  create_cctbx_xray_structure = cctbx_controller.create_cctbx_xray_structure(
    unit_cell,
    space_group,
    olx_atoms.iterator(),
    restraints_iter=None,
    constraints_iter=None
  )

  # This needs to be done I don't know why but otherwise smtbx farts
  # I tried using the xray_structure inside this file (see line 105 but appears to need hkl file?
  xray_structure = create_cctbx_xray_structure.structure()
  shrink_truncation_radius = solvent_radius = float(solvent_radius) # Angstrom - this could be passed during call?
  grid_step=float(grid_step)# Angstrom - a smaller number or variable passed during call?
  result = solvent_accessible_volume(
    xray_structure,
    solvent_radius,
    shrink_truncation_radius,
    grid_step=grid_step,
    atom_radii_table=olex_core.GetVdWRadii(),
    use_space_group_symmetry=True) # faster for high symmetry)
  result.show_summary()

  return result

OV.registerFunction(calcsolv)

def generate_sf_table():
  class SF_TableGenerator(OlexCctbxAdapter):
    def __init__(self):
      OlexCctbxAdapter.__init__(self)
      self.generate()

    def generate(self):
      from smtbx.structure_factors import direct
      miller_set = self.reflections.f_sq_obs_merged
      if (self.twin_components is not None
          and self.twin_components[0].value > 0):
        twin_component = self.twin_components[0]
        twinning = cctbx_controller.hemihedral_twinning(
          twin_component.twin_law.as_double(), miller_set)
        miller_set = twinning.twin_complete_set
      table_file_name = os.path.join(OV.FilePath(), OV.FileName()) + ".tsc"
      direct.generate_isc_table_file(table_file_name,
                                     self.xray_structure(),
                                     miller_set.indices())
  SF_TableGenerator()

OV.registerFunction(generate_sf_table, False, "test")

def generate_DISP(table_name_, wavelength=None, elements=None):
  import olx
  import olexex

  from cctbx.eltbx import attenuation_coefficient as attc
  if not elements:
    rm = olexex.OlexRefinementModel()
    elements = rm.get_unique_types(use_charges=True)
  table_name = table_name_.lower()
  # user dir first
  anom_dirs = [os.path.join(olx.DataDir(), "anom"),
    os.path.join(olx.BaseDir(), "etc", "anom")]
  if not wavelength:
    wavelength = olx.xf.exptl.Radiation()
  wavelength = float(wavelength)
  if wavelength < 0.1:
    generate_ED_SFAC(table_name_)
    return "OK" #instruct Olex2 to skip any further actions
  afile = None
  for d in anom_dirs:
    if not os.path.exists(d):
      continue
    for af in os.listdir(d):
      try:
        fw = float(af)
        if abs(wavelength-fw) < 0.01:
          afile = os.path.join(d, af)
          break
      except:
        pass
    if afile:
      break
  rv = []
  if afile and "auto" == table_name:
    with open(afile, 'r') as disp:
      for l in disp.readlines():
        l = l.strip()
        if not l or l.startswith('#'):
          continue
        ts = [x.strip() for x in l.split(',')]
        if ts[1] not in elements:
          continue
        val = "%s,%s,%s" %(ts[1],
          ts[3].split(':')[1].strip(),
          ts[4].split(':')[1].strip())
        if len(ts) > 5: #mu
          val += ",%s" %(ts[5].split(':')[1].strip())
        rv.append(val)
    return ';'.join(rv)

  if "sasaki" == table_name:
    from cctbx.eltbx import sasaki
    tables = sasaki
  elif "henke" == table_name:
    from cctbx.eltbx import henke
    tables = henke
  elif "brennan" == table_name or "auto" == table_name:
    from brennan import brennan
    tables = brennan()
  else:
    print("Invalid table name %s, resetting to Brennan & Cowan" % table_name_)
    from brennan import brennan
    tables = brennan()
  try:
    for e in elements:
      e = str(e)
      try:
        table = tables.table(e)
        f = table.at_angstrom(wavelength)
        #m_table = attc.get_table(nist_elements.atomic_number(e))
        rv.append(e + ',' + ','.join((str(f.fp()), str(f.fdp()))))
      except ValueError:
        rv.append(e + ',0.0, 0.0')
  except:
    from cctbx.eltbx import sasaki
    tables = sasaki
    rv = []
    print("ERROR: Previous table failed! Switching to Sasaki!")
    for e in elements:
      e = str(e)
      try:
        table = tables.table(e)
        f = table.at_angstrom(wavelength)
        #m_table = attc.get_table(nist_elements.atomic_number(e))
        rv.append(e + ',' + ','.join((str(f.fp()), str(f.fdp()))))
      except ValueError:
        rv.append(e + ',0.0, 0.0')
  return ';'.join(rv)

OV.registerFunction(generate_DISP, False, "sfac")

def make_DISP_Table():
  """
  builds a html table of Anom Disp correction values for a given element
  """
  element = OV.GetVar('anom_disp_el')
  if element == '':
    element = element_list().split(";")[0]
    OV.SetVar('anom_disp_el', element)
  from cctbx.eltbx import sasaki
  tables_S = sasaki
  from cctbx.eltbx import henke
  tables_H = henke
  from brennan import brennan
  tables_B = brennan()
  def row(rowdata, color='white', color2="black"):
    """
    creates a table row for the restraints list.
    :type rowdata: list
    """
    td = []
    for num, item in enumerate(rowdata):
      if num == 0:
        td.append(r"""<td width='30%' align='left' {0} ><b><font color={1}> {2} </font></b></td>""".format("bgcolor={}".format(color), color2, item))
      else:
        float(item)
        td.append(r"""<td width='23%' align='center' {0} ><b><font color={1}> {2:.3f} </font></b></td>""".format("bgcolor={}".format(color), color2, item))
    if not td:
      row = "<tr> No disp data given. </tr>"
    else:
      row = "<tr> {} </tr>".format(''.join(td))
    return row
  e = str(element)
  table = []
  import olexex
  rm = olexex.OlexRefinementModel()
  atoms = rm.atoms()
  refined_disp = []
  for a in atoms:
    if 'disp' in a:
      fp, fdp = a['disp']
      refined_disp.append((a['label'], fp, fdp))
  empty_data = """
  <b>There may be no Disp data or an error occured.</b>
  """
  try:
    table_B = tables_B.table(e)
    table_H = tables_H.table(e)
    wavelength = olx.xf.exptl.Radiation()
    wavelength = float(wavelength)
    try:
      f_B = table_B.at_angstrom(wavelength)
      f_H = table_H.at_angstrom(wavelength)

      table.append(row(["Henke", f_H.fp(), f_H.fdp(), tables_B.convert_fdp_to_mu(wavelength, f_H.fdp(), e)]))
      table.append(row(["Brennan & Cowan", f_B.fp(), f_B.fdp(), f_B.mu]))
      if e != 'H':
        table_S = tables_S.table(e)
        f_S = table_S.at_angstrom(wavelength)
        table.append(row(["Sasaki", f_S.fp(), f_S.fdp(), tables_B.convert_fdp_to_mu(wavelength, f_S.fdp(), e)]))
      else:
        table.append(row(["Sasaki", 0, 0, tables_B.convert_fdp_to_mu(wavelength, 0, element)]))
      for entry in refined_disp:
        if e in entry[0]:
          table.append(row([entry[0] + " Refined", entry[1], entry[2], tables_B.convert_fdp_to_mu(wavelength, entry[2], e)], 'orange', 'white'))
    except:
      print(f"Error getting value of Brennan & Cowan for {e}")
      f_H = table_H.at_angstrom(wavelength)

      table.append(row(["Henke", f_H.fp(), f_H.fdp()]))
      table.append(row(["Brennan & Cowan"]))
      if e != 'H':
        table_S = tables_S.table(e)
        f_S = table_S.at_angstrom(wavelength)
        table.append(row(["Sasaki", f_S.fp(), f_S.fdp()]))
      else:
        table.append(row(["Sasaki", 0, 0]))
      for entry in refined_disp:
        if e in entry[0]:
          table.append(row([entry[0] + " Refined", entry[1], entry[2]], 'orange', 'white'))

  except:
    return empty_data
  html = r"""
    <tr>
       <td width='30%'align='left'><b>Table </b></td>
       <td width='23%'align='center'><b>f' [e]</b></td>
       <td width='23%'align='center'><b>f'' [e]</b></td>
       <td width='23%'align='center'><b>mu [barns]</b></td>
    </tr>
    {0}
    """.format('\n'.join(table))
  if not table:
    return empty_data
  return html

OV.registerFunction(make_DISP_Table, False, "disp")

def element_list():
  import olexex
  rm = olexex.OlexRefinementModel()
  elements = rm.get_unique_types(use_charges=True)
  elements = list(elements)
  elements.sort()
  r = ""
  for e in elements:
    r += "{};".format(e)
  OV.SetVar('anom_disp_el', r.split(";")[0])
  return r
OV.registerFunction(element_list, False, "disp")

def get_R_cov_Z_from_SFAC_file(table_file_name):
  rv = {}
  with open(table_file_name, 'r') as sfac:
    for l in sfac.readlines():
      l = l.strip()
      if not l or l.startswith('#'):
        continue
      toks = l.split()
      if len(toks) != 16:
        continue
      # normalise case
      toks[1] = toks[1].upper()
      if len(toks[1]) > 1:
        toks[1] = toks[1][0] + toks[1][1].lower()
      rv[toks[1]] = toks[-2:]
  return rv

def convert_UCLA(ucla_in, sfac_out):
  src_tab = os.path.join(olx.BaseDir(), "etc", "ED", "SFAC_Peng_1999.txt")
  RZ = get_R_cov_Z_from_SFAC_file(src_tab)
  with open(ucla_in, "r") as inp:
    with open(sfac_out, "w") as out:
      for l in inp.readlines():
        if l.startswith('#'):
          out.write(l)
          continue
        l = l.strip()
        if not l: continue
        toks = l.split(',')
        if len(toks) < 14: continue
        sfac = "SFAC" + " %s"*9
        sfac = sfac %(toks[0],
          toks[2], toks[7], toks[3], toks[8],
          toks[4], toks[9], toks[5], toks[10])
        sfac += " 0 0 0 0"
        rz_key = toks[0]
        if '-' in toks[0]:
          rz_key = toks[0].split('-')[0]
        elif toks[0].endswith('+'):
          if len(toks[0]) == 3:
            rz_key = toks[0][0:1]
          if len(toks[0]) == 4:
            rz_key = toks[0][0:2]
        rz = RZ.get(rz_key, None)
        if rz is None:
          print("Could not locate covalent radius and Z for " + toks[0])
          rz = [1, toks[1]]
        sfac = sfac + " %s %s" %(rz[0], rz[1])
        out.write(sfac + '\n')
OV.registerFunction(convert_UCLA, False, "sfac")

def read_SFAC_table(table_file_name):
  rv = {}
  with open(table_file_name, 'r') as disp:
    for l in disp.readlines():
      l = l.strip()
      if not l or l.startswith('#'):
        continue
      toks = l.split()
      if len(toks) != 16:
        continue
      el = toks[1]
      if el.endswith('+'):
        el = el[0:len(el)-2] + '+' + el[-2]
      if el.endswith('1'): # Olex2 convention
        el = el[0:-1]
      toks[1] = el[0].upper() + el[1:]
      rv[el.lower()] = toks
  return rv

def generate_ED_SFAC(table_file_name=None, force = False):
  import olexex
  rm = olexex.OlexRefinementModel()
  sfac = rm.model.get('sfac')
  if sfac:
    sfac_elms = set([x.lower() for x in sfac.keys()])
  else:
    sfac_elms = set()
  elms = set([x.lower() for x in rm.get_unique_types(use_charges=True)])
  elms |= set([ec.split(':')[0].lower() for ec in olx.xf.GetFormula('list').split(',')])
  if sfac and len(elms) == len(sfac_elms) and elms.issubset(sfac_elms) and not force:
    return
  def_table_file_name = os.path.join(olx.BaseDir(), "etc", "ED", "SFAC_Peng_1999.txt")
  custom_table_file_name = os.path.join(olx.DataDir(), "ED", "SFAC.txt")
  if not table_file_name or table_file_name == "auto":
    tn = OV.GetParam("snum.smtbx.electron_table_name")
    if tn == "Custom":
      if os.path.exists(custom_table_file_name):
        table_file_name = custom_table_file_name
      else:
        table_file_name = def_table_file_name
    else:
      if tn == "Peng-1996":
        return
      if tn=="None" or tn == "Peng-1999":
        table_file_name = "SFAC_Peng_1999.txt"
      elif tn == "UCLA-2022":
        table_file_name = "SFAC_UCLA_2022.txt"
      elif tn == "CAP-2022":
        table_file_name = "SFAC_CAP_2022.txt"
  if table_file_name != custom_table_file_name:
    table_file_name = os.path.join(olx.BaseDir(), "etc", "ED", table_file_name)

  sfac_toks = []
  sfacs = read_SFAC_table(table_file_name)
  if not force:
    elms = elms.difference(sfac_elms)
  if elms or force:
    print("Updating SFAC using: %s" %table_file_name)
  for elm in elms:
    sfac = sfacs.get(elm, None)
    elmt = None
    if sfac is None:
      if '+' in elm:
        elmt = elm.split('+')[0]
      elif '-' in elm:
        elmt = elm.split('-')[0]
      else:
        print("Failed to locate SFAC for " + elm)
        continue
      sfac = sfacs.get(elmt, None)
    if sfac is None:
      print("Failed to locate SFAC for " + elm)
    else:
      if elmt is None:
        sfac_toks.append(sfac)
      else:
        sf = [sfac[0]]
        sf.append(elm[0].upper() + elm[1:])
        sf.extend(sfac[2:])
        sfac_toks.append(sf)

  for st in sfac_toks:
    olx.AddIns(*st)

OV.registerFunction(generate_ED_SFAC, False, "sfac")

def generate_DISP_all(table_name_, wavelength=None):
  from cctbx.eltbx.chemical_elements import proper_caps_list
  elements = proper_caps_list()
  table_name = table_name_.lower()
  if not wavelength:
    wavelength = olx.xf.exptl.Radiation()
  wavelength = float(wavelength)
  if "sasaki" == table_name:
    from cctbx.eltbx import sasaki
    tables = sasaki
  elif "henke" == table_name:
    from cctbx.eltbx import henke
    tables = henke
  elif "brennan" == table_name:
    from brennan import brennan
    tables = brennan()
  else:
    raise Exception("Invalid table name")
  with open("disp.lst",'w') as file:
    for e in elements:
      e = str(e)
      try:
        table = tables.table(e)
        f = table.at_angstrom(wavelength)
        file.write("%-4s %8.4f %8.4f\n" %(e, f.fp(), f.fdp()))
      except Exception as e:
        pass

OV.registerFunction(generate_DISP_all, False, "sfac")

def set_ED_tables(tables_name):
  OV.SetParam('snum.smtbx.electron_table_name', tables_name)
  from cctbx_olex_adapter import generate_ED_SFAC
  generate_ED_SFAC(force=True)
  ref = "Custom"
  if tables_name == 'Peng-1999':
    ref = "Peng, L.M. (1999) Micron 30, 625-648"
  elif tables_name == 'UCLA-2022':
    ref = "UCLA (2022) https://srv.mbi.ucla.edu/faes/data"
  elif tables_name == 'CAP-2022':
    ref = "CAP prior to 43.51a"
  OV.set_cif_item('_diffrn_oxdiff_scatteringfactors_ed', ref)
OV.registerFunction(set_ED_tables, False, "sfac")

def get_one_h_function(xray_structure, table_file_name):
  from smtbx.structure_factors import direct
  from smtbx_refinement_least_squares_ext import f_calc_function_default
  try:
    return f_calc_function_default(direct.f_calc_modulus_squared(
      xray_structure, table_file_name=table_file_name))
  except Exception as e:
    e_str = str(e)
    if "stoks.size() == scatterer" in e_str:
      print("Number of atoms in model and table are not matching!")
    elif "Error during building of normal equations using OpenMP" in e_str:
      print("OpenMP Error during Normal Equation build-up, likely missing reflection in .tsc file")
    raise e

def fdp_to_mu(element, fdp, wavelength=None):
  from brennan import  brennan
  tables = brennan()
  if not wavelength:
    wavelength = olx.xf.exptl.Radiation()
  wavelength = float(wavelength)
  return tables.convert_fdp_to_mu(wavelength, float(fdp), element)
OV.registerFunction(fdp_to_mu, False, "disp")

def calculate_brennan_mu():
  from brennan import  brennan
  tables = brennan()
  formula = olx.xf.GetFormula('list')
  wavelength = float(olx.xf.exptl.Radiation())
  mu = 0
  for ec in formula.split(','):
    e,c = ec.split(':')
    mu += tables.get_mu_at_angstrom(wavelength, e) * float(c)
  return mu * float(olx.xf.au.GetZprime())/ (10*float(olx.xf.au.GetAUVolume()))
OV.registerFunction(calculate_brennan_mu, False, "disp")


