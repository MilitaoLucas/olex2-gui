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
  olx.current_cell = None
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
      if self.hklf_code == 2 or self.hklf_code >= 5:
        # With a batch-scaled format the BASF list holds the batch scale
        # factors first and the twin component fractions after them, so what is
        # left over once each twin law has taken its fraction is the batch
        # count.
        batch_cnt = len(twin_fractions)-len(twin_laws)
        # HKLF 5 already names the twin component of every reflection in the
        # file, and miller.array.as_xray_observations refuses twin components
        # alongside those batch numbers outright -- the two are competing
        # descriptions of the same thing. So a TWIN matrix cannot be combined
        # with it, whatever the BASF count, and saying so here is worth more
        # than the assertion deeper in cctbx that would say it otherwise.
        assert self.hklf_code < 5, \
          "a TWIN matrix cannot be used with HKLF %d: the file already " \
          "identifies each reflection's twin component. Either drop the TWIN " \
          "card and keep BASF, which is how HKLF %d expresses twinning, or " \
          "keep TWIN and use HKLF 4 data." %(self.hklf_code, self.hklf_code)
        # Zero batches is a model in its own right -- one TWIN law, one BASF,
        # and no batch scaling at all -- and is left with no twin fractions,
        # exactly as a refinement without a batch-scaled format would be. Fewer
        # BASF than laws is not a model, so that is refused with a message
        # saying which two numbers disagree.
        assert batch_cnt >= 0, \
          "%d BASF given for %d twin law(s): each law needs a fraction, and " \
          "any BASF beyond that are batch scale factors" \
          %(len(twin_fractions), len(twin_laws))
        if batch_cnt > 0:
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
      if (self.hklf_code == 2 or self.hklf_code >= 5) and olx_tw_f is not None:
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
      # The part tells two disorder components apart, and a tabulated
      # scattering table is keyed on it: an entry written for PART 2 is never
      # matched to a scatterer claiming to be in PART 0. Set it here, on the
      # structure every consumer shares, rather than in the refinement alone --
      # a map calculated straight after a refinement failed on exactly that.
      atoms = self.olx_atoms._atoms
      scatterers = self._xray_structure.scatterers()
      if len(atoms) == scatterers.size():
        for i, atom in enumerate(atoms):
          scatterers[i].set_part(atom['part'])
      else:
        print("Warning: %d atoms against %d scatterers, so disorder parts were "
              "left unset; a tabulated scattering table will not match."
              % (len(atoms), scatterers.size()))
      if self.olx_atoms.exptl.get("radiation_type", "xray") == "neutrons":
        OV.SetParam("snum.smtbx.atomic_form_factor_table", "neutron")
      table = OV.GetParam("snum.smtbx.atomic_form_factor_table")
      null_disp = table == "electron" or table == "neutron"
      # Deuterium is the same electron cloud as hydrogen, so it scatters X-rays
      # and electrons identically and neither table carries an entry for it --
      # scattering_type_registry asserts instead. Only the neutron table tells
      # them apart, the scattering lengths there being genuinely different.
      # A joint X-ray/neutron deposition brings this in: 5MON has 593 D.
      # The dispersion lookup below already does the same mapping.
      if table != "neutron":
        n_d = 0
        for sc in scatterers:
          if sc.scattering_type == 'D':
            sc.scattering_type = 'H'
            n_d += 1
        if n_d:
          print("%d deuterium atom(s) scattering as hydrogen for the %s table"
                % (n_d, table))
      sfac = self.olx_atoms.model.get('sfac')
      custom_gaussians = {}
      custom_fp_fdps = {}
      resonant_table = None
      #  default for DISP first
      if self.reflections._merge < 4:
        resonant_table = OV.GetParam("snum.smtbx.resonant_form_factor_table")
        if resonant_table != "brennan":
          try:
            if str(resonant_table) == 'Auto':
              resonant_table = 'Custom'
            self._xray_structure.set_inelastic_form_factors(
              self.wavelength, resonant_table)
          except Exception as e:
            if OV.IsDebugging():
              print("Failed to retrieve some resonant scattering factors")
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
            resonant_table = "sasaki"
            try:
              self._xray_structure.set_inelastic_form_factors(
                        self.wavelength, resonant_table)
            except Exception as e:
              if OV.IsDebugging():
                print("Failed to retrieve some resonant scattering factors")
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
        resonant_table = "custom"
      self._xray_structure.set_custom_inelastic_form_factors(
        custom_fp_fdps, source=resonant_table)
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
            or self.space_group != olx.current_space_group
            # the GUI silently takes the cell from the hkl file's trailing ins
            # block (tasks.cpp, use_hkl_cell); a reflection set built on the
            # old cell keeps stale d-spacings
            or self.cell != getattr(olx, 'current_cell', None)))):
      olx.current_hklsrc = reflections
      olx.current_hklsrc_mtime = mtime
      olx.current_space_group = self.space_group
      olx.current_cell = self.cell
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
    _shel = self.reflections._get_shel(omit, shel, self.wavelength)
    update = False
    if merge_code is None or merge_code != self.reflections._merge:
      self.reflections.merge(merge=merge_code)
      update = True
    if force or omit is None or omit != self.reflections._omit or _shel != self.reflections._shel:
      update = True

    if update or self.observations is None:
      self.reflections.filter(omit, shel, self.olx_atoms.exptl['radiation'], doFilter=doFilter)
      # The test set comes out here, before the observations are built, so
      # every solver refines against the work set without any of them knowing
      # there is a test set at all - the alternative is teaching each mode
      # separately and having one of them quietly not do it.
      self.free_flags = None
      self.f_sq_obs_free = None
      if OV.GetParam('snum.refinement.use_free_set'):
        import free_set
        fo_sq = self.reflections.f_sq_obs_filtered
        self.free_flags = free_set.flags_for(fo_sq)
        if self.free_flags is not None:
          self.f_sq_obs_free = fo_sq.select(self.free_flags)
          self.reflections.f_sq_obs_filtered = fo_sq.select(~self.free_flags)
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
    def evaluate_one_h_many(one_h_function, indices):
      evaluate_many = getattr(one_h_function, "evaluate_many", None)
      if evaluate_many is not None:
        return evaluate_many(indices)
      data = []
      data_append = data.append
      evaluate = one_h_function.evaluate
      for mi in indices:
        evaluate(mi)
        data_append(one_h_function.f_calc)
      return flex.complex_double(data)

    assert self.xray_structure().scatterers().size() > 0, "n_scatterers > 0"
    if not miller_set:
        miller_set_ = self.observations.unique_mapped_miller_set
    else:
      miller_set_ = miller_set
    if ignore_inversion_twin and self.is_inversion_twin():
      apply_twin_law = False
    if apply_twin_law and self.twin_components:
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
        fc = twin_set.array(
          data=evaluate_one_h_many(one_h_function, twin_set.indices()))
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
        fc = miller_set_.array(
          data=evaluate_one_h_many(one_h_function, miller_set_.indices()),
          sigmas=None)
      else:
        xs = self.xray_structure()
        if miller_set_.space_group_number() == 1 and\
           self.xray_structure().space_group() != miller_set_.space_group():
           #xs = xs.deep_copy()
           xs = xs.expand_to_p1()
        fc = miller_set_.structure_factors_from_scatterers(
          xs, algorithm=algorithm).f_calc()
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

  def get_new_shelxl_weighting(self):
    from smtbx.refinement import least_squares
    weight = self.olx_atoms.model['weight']
    params = dict(a=0.1, b=0,
                  #c=0, d=0, e=0, f=1./3,
                  )
    for param, value in zip(list(params.keys())[:min(2, len(weight))], weight):
      params[param] = value
    return least_squares.new_shelx_weighting(**params)

  def get_unit_weighting(self):
    from smtbx.refinement import least_squares
    return least_squares.unit_weighting()

  def get_sigma_weighting(self):
    from smtbx.refinement import least_squares
    return least_squares.sigma_weighting()

  def get_sin_theta_over_lambda_weighting(self):
    from smtbx.refinement import least_squares
    weight = self.olx_atoms.model['weight']
    params = dict(unit_cell = self._xray_structure._unit_cell, a=weight[0] if len(weight) > 0 else 0.1)
    return least_squares.stl_weighting(**params)

  def compute_weights(self, fo2, fc, fc2_data=None, reset_scale_factor = False):
    weight = self.olx_atoms.model['weight']
    params = [0.1, 0, 0, 0, 0, 1./3]
    for i, v in enumerate(weight):
      params[i] = v

    if reset_scale_factor:
      # this requires complex numbers
      #scale_factor = fo2.scale_factor(fc)
      if fc2_data is None:
        if fc.is_complex_array():
          fc2_data = flex.norm(fc.data())
        else:
          fc2_data = flex.pow2(fc.data())
      scale_factor = flex.sum(fo2.data()*fc2_data) / flex.sum(flex.pow2(fc2_data))
    else:
      scale_factor = OV.GetOSF()
    if OV.GetParam("snum.refinement.program").startswith("olex2.refine"):
      scheme = OV.GetParam("snum.refinement.weighting_scheme", "shelx")
      if scheme == "shelx":
        weighting = self.get_shelxl_weighting()
      elif scheme.lower() == "default":
        weighting = self.get_shelxl_weighting()
      elif scheme == "new_shelx":
        weighting = self.get_new_shelxl_weighting()
      elif scheme == "unit":
        weighting = self.get_unit_weighting()
      elif scheme == "sigma":
        weighting = self.get_sigma_weighting()
      elif scheme == "sin_theta_over_lambda":
        weighting = self.get_sin_theta_over_lambda_weighting()
      elif scheme == "stl":
        weighting = self.get_sin_theta_over_lambda_weighting()
      else:
        print("Unknown weighting scheme %s, using shelx!" %scheme)
        weighting = self.get_shelxl_weighting()
      if fc2_data is None:
        fc2_data = fc.as_intensity_array().data()
      indices = fo2.indices()
      fo2_d = fo2.data()
      sigmas = fo2.sigmas()
      weights = flex.double(fo2.size(), 1.0)
      for i in range(fo2.size()):
        weights[i] = weighting.compute(fo2_d[i], sigmas[i], fc2_data[i], indices[i], scale_factor)
      return weights
    else:
      weighting = xray.weighting_schemes.shelx_weighting(*params,
        wavelength=self.wavelength)
      weighting.observed = fo2
      weighting.compute(fc, scale_factor)
      return weighting.weights

  def load_mask(self):
    import gui
    prg = OV.GetParam('snum.refinement.recompute_mask_before_refinement_prg', "Olex2")
    _ =  os.path.splitext(OV.HKLSrc())[0]
    indices = []
    data = []
    fab_path = f"{_}.fab"
    if os.path.exists(fab_path):
      OV.SetVar('masking_dte', time.ctime(os.path.getmtime(fab_path)))
      OV.SetVar('masking_src', os.path.basename(fab_path))
      lines, fab_path, prg = gui.tools.GetMaskInfo.get_and_check_mask_origin(fab_path, prg)
      if not lines:
        return
      for l in lines:
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

  # complete - detwins the whole index range rather than just measured refs, used in masking
  def get_fo_sq_fc(self, one_h_function=None, filtered=True, merge=True, complete=False,
                   return_scale_indices=False):
    scale_indices = None
    if filtered:
      fo2 = self.reflections.f_sq_obs_filtered
      if self.hklf_code in (2, 5):
        scale_indices = self.reflections.batch_numbers
    else:
      fo2 = self.reflections.f_sq_obs_merged
      if self.hklf_code in (2, 5) and self.reflections.batch_numbers_array is not None:
        scale_indices = self.reflections.batch_numbers_array.data()
    miller_set = None
    if one_h_function:
      try:
        fc = self.f_calc(miller_set, self.exti is not None, True, False,
                       one_h_function=one_h_function, twin_data=False)
      except Exception as e:
        print("Error during calculation of F_calcs: %s"%(str(e)))
        return None, None
    else:
      fc = self.f_calc(miller_set,
       apply_extinction_correction=self.exti is not None,
       ignore_inversion_twin=False,
       apply_twin_law=True,
       twin_data=False)
    dtw = self.observations.detwin(
      fo2.crystal_symmetry().space_group(),
      fo2.anomalous_flag(),
      fc.indices(),
      fc.as_intensity_array().data(), complete)
    fo2 = miller.array(
        miller_set=miller.set(
          crystal_symmetry=fo2.crystal_symmetry(),
          indices=dtw.indices,
          anomalous_flag=fo2.anomalous_flag()),
        data=dtw.data,
        sigmas=dtw.sigmas).set_observation_type(fo2)
    if merge:
      fo2 = fo2.merge_equivalents(algorithm="shelx").array().map_to_asu()
      fc = fc.common_set(fo2)
      if fc.size() != fo2.size():
        fo2 = fo2.common_set(fc)
      scale_indices = None
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
      if scale_indices is not None and scale_indices.size() != fo2.size():
        scale_indices = None
    if return_scale_indices:
      return (fo2, fc, scale_indices)
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

  def is_inversion_twin_ex(self):
    """
    Returns  a tuple if the first twin component is an inversion and if it is
    being refined
    """
    if not self.twin_components:
      return (False, False)
    return (self.twin_components[0].twin_law.as_double() ==\
        sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1)).as_double(),
        self.twin_components[0].grad)

  def is_inversion_twin(self):
    """
    Checks if the first twin component is an inversion
    """
    return self.is_inversion_twin_ex()[0]

def write_fab(f_mask, fab_path=None):
  import shutil
  import gui
  if not fab_path:
    fab_path = os.path.splitext(OV.HKLSrc())[0] + ".fab"
  if os.path.exists(fab_path):
    ## if there is already a fab file of this name, but it doesn't originate from the current masking program, then get it out of the way and make a backup.
    prg = OV.GetParam('snum.refinement.recompute_mask_before_refinement_prg', "Olex2")
    lines = gui.tools.GetMaskInfo.get_and_check_mask_origin(fab_path, prg)

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
        olx.Echo("No fcf file is present", m="error")
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
      if self.olex2_adaptor.hklf_code == 5:
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


# **What the solution knew, kept for the tidy-up to reuse.**
#
# `tidy_solution` runs from `RunPrg` after the solving run has finished, on a
# *new* `OlexCctbxSolve`, so anything stored on the instance is gone by then.
# The alternative -- recomputing the density from a map after the refinement --
# is the decision that stalled this feature: the solution map no longer matches
# the moved atoms, and an Fo/2Fo-Fc map from the tidy-up refinement has its Fc
# contaminated by the very assignment being corrected.
#
# Recording the *integrated densities* sidesteps it. They are a property of the
# solution map at a point, so they are as valid after the refinement as before,
# while `element_assignment.assign` refits its carbon scale over whatever sites
# survive -- which is precisely the part cleanup improves.
#
# Keyed by atom name because that is what survives the `.res` round trip,
# `compaq`, `refine` and `kill`. Positions do not: the atoms move 0.1-0.24 A in
# the refinement and `compaq` moves whole fragments between symmetry images.
_SOLUTION_EVIDENCE = {}


_GEOMETRY_MODEL = {}


def _geometry_model(path):
  """ The geometry-aid model, loaded once per Olex2 session.

  `geometry_aid.Model(path)` decompresses a 4.4 MB npz holding a 100 x 42,042
  float64 PCA matrix -- 33.6 MB once expanded -- and it measured **0.139 s**,
  against 0.030 s for the projection it exists to perform and 0.008 s for the
  three dense layers after it. Rebuilding it per call was affordable while
  there was one call per solve. Auto-Solve now makes two, before and after the
  tidy-up, so it is worth keeping.

  Keyed on the file's modification time as well as its path: a developer
  dropping in a retrained model mid-session must get the new one, and a stale
  classifier would be invisible in every number it produced.
  """
  from smtbx.ab_initio import geometry_aid
  try:
    key = (path, os.path.getmtime(path))
  except OSError:
    key = (path, None)
  if key not in _GEOMETRY_MODEL:
    _GEOMETRY_MODEL.clear()
    _GEOMETRY_MODEL[key] = geometry_aid.Model(path)
  return _GEOMETRY_MODEL[key]


def _remember_density_evidence(densities, sites, allowed):
  """ Hold the densities until the peaks have names; see `_SOLUTION_EVIDENCE`. """
  _SOLUTION_EVIDENCE.clear()
  _SOLUTION_EVIDENCE["densities"] = list(densities)
  _SOLUTION_EVIDENCE["allowed"] = set(allowed or ())
  _SOLUTION_EVIDENCE["names"] = {}


def _name_density_evidence(index, name):
  """ Attach the Olex2 name a posted peak was given to its density. """
  if name and "names" in _SOLUTION_EVIDENCE:
    _SOLUTION_EVIDENCE["names"][str(name)] = index


class OlexCctbxSolve(OlexCctbxAdapter):
  def __init__(self):
    OlexCctbxAdapter.__init__(self)
    self.peak_normaliser = 1200 #fudge factor to get cctbx peaks on the same scale as shelx peaks

  def runChargeFlippingSolution(self, verbose="highly", solving_interval=60,
                                mode="classic"):
    """ Solve. `mode` selects which of the two solution methods is running.

    `classic` is the original single charge-flipping run, unchanged, and is
    what the `Charge Flipping` method calls. `auto` is the multi-attempt
    pipeline -- ranked trials, a space-group shortlist and element types --
    and is what `Auto-Solve` calls.

    Defaulting to `classic` is deliberate: anything already calling this
    without the argument gets the behaviour it has always had.
    """
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
    #
    # **Drop the anomalous flag before merging.** Olex2 hands over an array
    # with `Anomalous flag: True`, so merging keeps Friedel opposites apart.
    # Every number this pipeline was tuned and measured against was produced
    # from non-anomalous arrays (`cod_data.read_f_sq` builds them with
    # `anomalous_flag=False`), and charge flipping works from |F| assuming
    # Friedel's law in any case. Leaving it set means the GUI runs a different
    # input convention from the one all the measurements describe -- a
    # divergence no harness could ever have shown, because the harness is what
    # defined the convention.
    if f_obs.anomalous_flag():
      f_obs = f_obs.as_non_anomalous_array()
    merging = f_obs.merge_equivalents()
    f_obs = merging.array()
    f_obs.show_summary()

    params = OV.Params().programs.solution.smtbx.cf
    extra = group_args(
      max_attempts_to_get_phase_transition\
        = params.max_attempts_to_get_phase_transition,
      max_attempts_to_get_sharp_correlation_map \
        = params.max_attempts_to_get_sharp_correlation_map,
      max_solving_iterations=params.max_solving_iterations)
    formula = {}
    for element in str(olx.xf.GetFormula('list')).split(','):
      element_type, n = element.split(':')
      formula.setdefault(element_type, float(n))
    if params.amplitude_type == 'E':
      extra.normalisations_for = lambda f: f.amplitude_normalisations(formula)
    elif params.amplitude_type == 'quasi-E':
      def quasi(f):
        try:
          return charge_flipping.amplitude_quasi_normalisations(f)
        except AssertionError:
          # ponytail: the binned means extrapolate under zero on a few hundred
          # reflections (2222909: 311); the formula's Wilson E instead
          print("quasi-E normalisation failed on %d reflections; using E from "
                "the formula" % f.size())
          return f.amplitude_normalisations(formula)
      extra.normalisations_for = quasi

    # Set on every run so a previous run's table can never be shown beside a
    # new solution.
    self.solution_suggestions = None
    self.solution_f_obs = f_obs

    # **The method decides the mode, not the parameters.** The two solution
    # methods share this adapter and one phil namespace, so resolving "am I the
    # classic one?" from a parameter value would make the answer depend on
    # whichever settings page was touched last. `Charge Flipping` must behave
    # exactly as it always has for existing users and scripts, whatever the
    # pipeline's knobs happen to say.
    if mode == "classic":
      n_trials, want_groups, want_elements = 1, False, False
    else:
      n_trials = max(1, int(getattr(params, 'n_trials', 8)))
      want_groups = bool(getattr(params, 'suggest_space_groups', True))
      want_elements = bool(getattr(params, 'assign_elements', True))
    self.assign_elements_wanted = want_elements

    if n_trials > 1:
      f_calc = self.multiTrialSolution(f_obs, params, extra, n_trials, verbose)
      if want_groups:
        self.solution_suggestions = self.suggestSpaceGroups(f_obs)
    else:
      # The original single run, kept reachable so that the previous behaviour
      # is still available and comparable: it is not the same as one trial of
      # the multi-trial driver, because the solving iterator restarts itself up
      # to max_attempts_* times here and exactly once there.
      flipping = charge_flipping.weak_reflection_improved_iterator(
        delta=None,
        weak_reflection_fraction=getattr(params, 'weak_reflection_fraction',
                                         0.2))
      solving = charge_flipping.solving_iterator(
        flipping,
        f_obs,
        yield_during_delta_guessing=True,
        yield_solving_interval=solving_interval,
        **extra.__dict__
      )
      charge_flipping_loop(solving, verbose=verbose)
      f_calc = (solving.f_calc_solutions[0][0]
                if solving.f_calc_solutions else None)

    # play with the solutions
    expected_peaks = f_obs.unit_cell().volume()/18.6/len(f_obs.space_group())
    expected_peaks *= 1.3
    if f_calc is not None:
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
      # Propose an element for each peak, if asked. Falls back to the old
      # unnamed-peak behaviour on any failure -- a solution the user can refine
      # by hand beats no solution because the labelling stage broke.
      elements = None
      if getattr(self, 'assign_elements_wanted', False):
        elements = self.assignElementTypes(f_calc, fft_map, peaks.sites())

      numbered = {}
      for i, (xyz, height) in enumerate(zip(peaks.sites(), peaks.heights())):
        if not xyz:
          have_solution = False
          break
        else:
          element = None
          if elements is not None and i < len(elements):
            element = elements[i]
            numbered[element] = numbered.get(element, 0) + 1
          name = self.post_single_peak(xyz, height, element=element,
                                       number=numbered.get(element))
          _name_density_evidence(i, name)
      have_solution = True
    else: have_solution = False
    return have_solution

  def startingUiso(self, element, u_carbon=0.06):
    """ A starting displacement parameter appropriate to the element.

    Every peak used to be seeded at 0.06 regardless of what it was. That is
    right for carbon and badly wrong for a heavy atom: mean-square displacement
    goes as 1/(m omega^2), so a heavier atom genuinely vibrates less, and
    palladium belongs near 0.02. Starting it at 0.06 leaves the refinement to
    walk it all the way down -- which is exactly what was seen on the first
    real structure, where `Pd.uiso` was the worst-behaved parameter in the
    model at -35 sigma on cycle 1 and still -18 by cycle 4.

    `u_carbon * sqrt(M_C / M)` reproduces the usual spread closely enough to
    start from: C 0.060, O 0.052, Cl 0.035, Fe 0.028, Pd 0.020, Pt 0.015.

    Capped, because the same formula sends hydrogen to 0.21. Hydrogen is not
    placed from peaks here, but a formula that can return nonsense for an
    element someone might later pass is a trap worth closing now.
    """
    import math
    try:
      from cctbx.eltbx import tiny_pse
      mass = tiny_pse.table(str(element)).weight()
    except Exception:
      return u_carbon
    if not mass or mass <= 0:
      return u_carbon
    return max(0.005, min(0.08, u_carbon*math.sqrt(12.011/mass)))

  def expectedElements(self):
    """ The element symbols the user has declared for this crystal, as a set.

    Only the identities are taken. The **counts are deliberately ignored**: a
    user typing one atom of each element is normal practice -- it is all
    SHELXT needs -- and every attempt to lean on the numbers has measured
    worse than not asking, so this must work when the formula is qualitative.

    Empty set when there is no formula, which the caller treats as "any
    element is possible" rather than as an error.
    """
    try:
      raw = str(olx.xf.GetFormula('list'))
    except Exception:
      return set()
    out = set()
    for part in raw.split(','):
      symbol = part.split(':')[0].strip()
      if symbol:
        out.add(symbol.capitalize())
    return out

  def geometryProposals(self, unit_cell, space_group, sites):
    """ The classifier's ranked elements per site, from local geometry alone.

    Split out of `assignElementTypes` because the re-typing that happens after
    the tidy-up needs exactly this and nothing else: **SOAP is computed from
    coordinates, so the geometry half needs no map.** That is what makes
    re-typing after cleanup cheap enough to do at all -- the density half can
    be replayed from the integrated densities recorded at solve time, and only
    this has to be recomputed.

    Returns `(proposals, model)` or `None`. Raises nothing the caller has to
    handle beyond a None: a labelling failure must not cost a solution.

    Cost, measured on node1 6 August: **0.90 s**, of which the NoSpherA2
    process is 0.88 and everything else -- the 40 MB descriptor round trip, the
    PCA projection, the network -- is 0.02. The cost is *fixed*: one atom and
    120 atoms both take 0.9 s, because it is process startup rather than work.
    Anything that wants this faster has to stop launching a process, not make
    the arithmetic cheaper.
    """
    import os
    import subprocess
    import tempfile
    from smtbx.ab_initio import assemble, geometry_aid

    # shipped by the NoSpherA2 distribution zip (etc/ merges into Olex2's), not SVN
    model_path = os.path.join(OV.BaseDir(), "etc", "geometry_aid_model.npz")
    exe = os.path.join(OV.BaseDir(), "NoSpherA2.exe")
    if not (os.path.exists(model_path) and os.path.exists(exe)):
      print("Geometry model or NoSpherA2 not found; using density only")
      return None

    built = assemble.assemble(unit_cell, space_group, sites)
    work = tempfile.mkdtemp(prefix="olex_elements_")
    xyz_path = os.path.join(work, "peaks.xyz")
    with open(xyz_path, "w") as f:
      f.write(assemble.as_xyz(unit_cell, built.sites,
                              ["C"]*built.sites.size(), title="peaks"))
    # **No console window, and capture what it says.** This runs from the GUI,
    # and `check_call` pops a black console box on Windows for as long as
    # NoSpherA2 takes. Same idiom as `gui/help.convert_md_to_html_pandoc`.
    #
    # Capturing rather than inheriting stdout also keeps NoSpherA2's chatter out
    # of the Olex2 log, and means a failure can say *why* instead of raising a
    # bare CalledProcessError with the reason on a console that has already
    # closed.
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    proc = subprocess.run(
      [exe, "-wfn", xyz_path, "-calc_featomic_descriptor"],
      cwd=work, capture_output=True, text=True, creationflags=flags)
    if proc.returncode != 0:
      tail = [x for x in ((proc.stderr or "") + "\n"
                          + (proc.stdout or "")).splitlines() if x.strip()]
      raise RuntimeError("NoSpherA2 exited %d: %s"
                         % (proc.returncode, " | ".join(tail[-4:])
                            or "no output"))
    import numpy
    values = numpy.load(os.path.join(work, "descriptor.npy"))
    model = _geometry_model(model_path)
    n = min(sites.size(), values.shape[0])
    return model.top_k(values[:n], k=len(model.classes)), model

  def assignElementTypes(self, f_calc, fft_map, sites):
    """ An element per peak: integrated density, then local geometry.

    Charge flipping returns unlabelled maxima and Olex2 has always called them
    all carbon, which is the difference between "a structure appeared" and "a
    structure I can refine". Two independent signals are combined:

      density   how many electrons sit at the peak. Good at heavy-versus-light,
                poor exactly where chemistry matters -- C, N and O differ by one
                electron and overlap at ordinary resolution.
      geometry  a SOAP description of the atom's surroundings, put through the
                geometry-aid classifier. A carbonyl oxygen and a ring carbon
                have nearly the same density and completely different
                neighbourhoods.

    Measured over **1,162,153 atoms of 44,568 structures**: density alone
    0.635, geometry alone 0.692, the two combined 0.717, with the right element
    among the classifier's top three 0.924. Nothing moved by more than 0.006
    from the earlier 11,692-atom figures across a hundredfold more atoms, which
    says more than the third decimal does. Weak per element and worth knowing
    before trusting a label: B 0.09, I 0.11, P 0.16, Si 0.23 -- C, N and O
    carry the average.

    **Two preconditions, both learned the hard way.** The molecule is assembled
    first (`assemble.py`), because an atom whose bonded neighbours sit in a
    different symmetry image has an almost empty environment inside the 3.5 A
    cutoff and its descriptor is meaningless rather than merely noisy. And the
    .xyz handed to the descriptor is **all carbon**, because the shipped model
    was trained that way; feeding it the density assignment scored oxygen at
    0.05 against 0.44.

    Returns a list of element symbols aligned with `sites`, or None -- in which
    case the caller keeps the old unnamed peaks. Never raises: a labelling
    failure must not cost the user their solution.
    """
    import os
    import subprocess
    import tempfile

    try:
      from smtbx.ab_initio import assemble, element_assignment, geometry_aid
    except ImportError as e:
      print("Element assignment unavailable: %s" % e)
      return None

    # **Restrict the candidates to what the user says is in the crystal.**
    # Without this the table is the whole of COMMON_ELEMENTS and the density
    # call is free to answer Ru or Si in a Pd/Fe/Cl/P/S/C structure -- which is
    # exactly what it did on the first real run, and a wrong Z wrecks the
    # residual map far more visibly than a wrong position would. Knowing that
    # only C, N, O and S are possible removes most of the ambiguity for free,
    # and the composition is something the user has already typed.
    allowed = self.expectedElements()
    if allowed:
      print("Element assignment restricted to: %s" % ", ".join(sorted(allowed)))
    else:
      print("No composition given, so any element may be proposed")

    try:
      densities = element_assignment.integrated_densities(fft_map, sites)
      assigned = element_assignment.assign(f_calc.unit_cell(), sites,
                                           densities,
                                           elements=sorted(allowed) or None,
                                           space_group=f_calc.space_group(),
                                           formula_zs=self.expectedZs() or None)
      print("Density scale from %s" % assigned.scale_from)
      calls = assigned.assignments
      by_density = [a.element for a in calls]

      # **Keep the integrated densities, not the conclusions.** The tidy-up is
      # about to delete peaks, and `element_assignment.assign` fits its carbon
      # scale over whichever sites it is given -- so once the spurious peaks are
      # gone the same densities give a *better* scale and different calls. The
      # densities themselves do not change, which is what lets the whole density
      # half be replayed after cleanup without ever touching a map again.
      _remember_density_evidence(densities, sites, allowed)

      got = self.geometryProposals(f_calc.unit_cell(), f_calc.space_group(),
                                   sites)
      if got is None:
        return by_density
      proposals, model = got
      n = min(len(calls), len(proposals))
      merged = geometry_aid.combine(calls[:n], proposals[:n])
      out = [m.element for m in merged]
      # The classifier ranks over *its own* trained classes, which have nothing
      # to do with this crystal's composition, so the merge can reintroduce an
      # element the user never declared even when the density call was
      # restricted. Anything outside the declared set falls back to the density
      # answer, which is already constrained.
      if allowed:
        overruled = 0
        for i, sym in enumerate(out):
          if sym not in allowed:
            out[i] = by_density[i]
            overruled += 1
        if overruled:
          print("  %d geometry proposal(s) outside the given composition, "
                "reverted to the density call" % overruled)
      # Peaks beyond what assembly covered keep their density call.
      out.extend(by_density[n:])

      changed = sum(1 for a, b in zip(by_density, out) if a != b)
      print("Element assignment: %d peaks, %d where geometry changed the "
            "density call" % (len(out), changed))
      return out
    except Exception as e:
      # **Fall back to the density call, not to nothing.** `by_density` was
      # computed above and is a complete answer on its own -- measured 0.635
      # correct over 1,162,153 atoms, against 0.717 for density plus geometry.
      # Losing it because the geometry half failed throws away two thirds of
      # the value and leaves the user retyping every label by hand, which is
      # exactly the state this feature exists to fix.
      #
      # The geometry half fails for mundane reasons: the shipped NoSpherA2.exe
      # hard-codes older SOAP hyperparameters and emits 16,500 features where
      # every trained model expects 42,042, so it refuses -- correctly, since a
      # descriptor of the wrong length would give confident nonsense.
      names = locals().get("by_density")
      if names:
        print("Geometry step unavailable (%s: %s); using the density call only"
              % (type(e).__name__, e))
        return names
      print("Element assignment failed (%s: %s); leaving peaks unnamed"
            % (type(e).__name__, e))
      return None

  def refinedElectronCounts(self, xs):
    """ An electron count per atom of the refined model.

    Fo and Fc maps on one grid, both phased by the model and integrated in the
    same sphere about each site: the ratio times the modelled Z is what the
    data say sits there, the thermal smearing and series termination
    cancelling per site. Divided by its median over the better-behaved half
    of the atoms so the scale, the missing hydrogens and the noise peaks do
    not move every atom together. None where the model has no
    element (a Q peak).
    """
    from cctbx import maptbx, miller
    from cctbx.array_family import flex
    from cctbx.eltbx import tiny_pse
    from smtbx.ab_initio import element_assignment
    f_obs = self.reflections.f_sq_obs_merged.average_bijvoet_mates().f_sq_as_f()
    f_calc = f_obs.structure_factors_from_scatterers(xray_structure=xs).f_calc()
    fc = flex.abs(f_calc.data())
    k = flex.sum(f_obs.data()*fc)/flex.sum(fc*fc)
    gridding = maptbx.crystal_gridding(
      unit_cell=xs.unit_cell(), space_group_info=xs.space_group_info(),
      d_min=f_obs.d_min(), resolution_factor=1/3.,
      symmetry_flags=maptbx.use_space_group_symmetry)
    def integrate(data):
      m = miller.fft_map(gridding, miller.array(miller_set=f_calc, data=data))
      m.apply_volume_scaling()
      return element_assignment.integrated_densities(m, xs.sites_frac())
    eo = integrate(flex.polar(f_obs.data()/k, flex.arg(f_calc.data())))
    ec = integrate(f_calc.data())
    ratio = [o/c if c > 0 else None for o, c in zip(eo, ec)]
    # ponytail: the median over the low-U half only; noise peaks (high U, no
    # density) sit low and would drag the median under the real atoms
    u = list(xs.extract_u_iso_or_u_equiv())
    u_mid = sorted(u)[len(u)//2] if u else 0.0
    good = sorted(r for r, ui in zip(ratio, u) if r is not None and ui <= u_mid)
    norm = good[len(good)//2] if good else 1.0
    # ponytail: a model typed a Z too light everywhere is self-consistent
    # under the median (11 O read as C, 2211782); the formula counts, where
    # the user gave real ones, pin the middle half of the Z distribution
    have, want = [], self.expectedZs()
    for s in xs.scatterers():
      try:
        have.append(tiny_pse.table(s.scattering_type.strip().capitalize()).atomic_number())
      except (RuntimeError, ValueError):
        pass
    def mid(v):
      v = sorted(v)
      v = v[len(v)//4:len(v) - len(v)//4] or v
      return sum(v)/float(len(v)) if v else 0.0
    # ponytail: rank-based, so it only holds when the model and the formula
    # count about the same atoms (2223999: 9 modelled against 21 declared
    # read Mo and K as O); the window is the knob
    if want and 0.75 <= len(want)/float(len(have) or 1) <= 1.33 and mid(have) > 0:
      print("Formula anchor: model mid-Z %.1f, formula %.1f, scale x%.2f"
            % (mid(have), mid(want), mid(have)/mid(want)))
      norm *= mid(have)/mid(want)
    out = []
    for s, r in zip(xs.scatterers(), ratio):
      try:
        z = tiny_pse.table(s.scattering_type.strip().capitalize()).atomic_number()
      except (RuntimeError, ValueError):
        z = 0
      out.append(z*r/norm if r is not None and z > 0 else None)
    return out

  def expectedZs(self):
    """ One Z per non-H atom of the declared formula; empty when the counts
    look qualitative (one of each), which SHELXT users type. """
    from cctbx.eltbx import tiny_pse
    out, ns = [], []
    try:
      for part in str(olx.xf.GetFormula('list')).split(','):
        e, n = part.split(':')
        e = e.strip().capitalize()
        if e not in ("H", "D"):
          ns.append(int(round(float(n))))
          out += [tiny_pse.table(e).atomic_number()]*ns[-1]
    except Exception:
      return []
    return out if len(ns) > 1 and max(ns) > 1 or len(ns) == 1 else []

  def completeModel(self):
    """ Add what the difference map of the refined model says is missing.

    smtbx.ab_initio.model_completion: rounds of Fo-Fc on the refined model,
    peaks over its sigma cut at bond distance to the model become carbon
    atoms, then a refine and a prune of what it added. Returns the number
    of atoms posted; never raises.
    """
    import re
    try:
      from smtbx.ab_initio import model_completion
      xs = self.xray_structure()
      f_obs = self.reflections.f_sq_obs_merged.average_bijvoet_mates().f_sq_as_f()
      scat = [s for s in xs.scatterers()
              if s.scattering_type.strip().capitalize() not in ("Q", "H", "D")]
      sites = [s.site for s in scat]
      calls = [s.scattering_type.strip().capitalize() for s in scat]
      new_sites, new_calls, n = model_completion.complete(f_obs, xs, sites, calls)
      if n <= 0:
        print("Difference map completion: nothing to add")
        return 0
      used = [int(m.group(1)) for m in
              (re.match(r"C(\d+)$", str(s.label)) for s in xs.scatterers()) if m]
      next_no = max(used or [0]) + 1
      posted = []
      for k, site in enumerate(list(new_sites)[len(sites):]):
        name = self.post_single_peak(site, 0, element="C", number=next_no + k)
        if name:
          posted.append(name)
      print("Difference map completion added %d atom(s): %s"
            % (len(posted), " ".join(posted)))
      return len(posted)
    except Exception as e:
      import traceback
      print("Difference map completion did not run (%s: %s)"
            % (type(e).__name__, e))
      if OV.IsDebugging():
        traceback.print_exc()
      return 0

  def printDoubt(self):
    """ The atoms whose type the last re-typing did not settle: every other
    allowed element that kept over a tenth of the arbitration weight. """
    rows = getattr(type(self), "doubt", None)
    if not rows:
      return
    print("Types with a runner-up over 10 %:")
    for name, alt in rows:
      print("  %s: %s" % (name, " | ".join("%s (%.0f %%)" % (e, 100*p)
                                            for e, p in alt)))

  def reassignAfterCleanup(self):
    """ Re-type the refined model from what the data say sits at each site.

    Density evidence is taken fresh from the refined model rather than from
    the solution's peaks: an atom typed too light shows the surplus in the Fo
    map, one typed too heavy a deficit, and a correctly typed atom reads its
    own Z. An atom that reads its own Z is left alone, whatever the geometry
    classifier thinks; the others are arbitrated between a Gaussian in Z
    about the estimate and the classifier's posterior (floored so that a
    class the classifier never saw still gets the density's vote), over
    the declared composition. Returns {label: (old, new)} for the labels changed; never
    raises.
    """
    import math
    from cctbx.array_family import flex
    from cctbx.eltbx import tiny_pse

    allowed = set(_SOLUTION_EVIDENCE.get("allowed") or self.expectedElements())
    # a hydrogen is never what a peak with too little density is
    allowed -= set(("H", "D"))
    try:
      xs = self.xray_structure()
      z_of = [(e, tiny_pse.table(e).atomic_number()) for e in sorted(allowed)]
      # ponytail: a mistyped atom mis-reads its correction (1.6x over a Z away,
      # under once its U has collapsed), so it is re-typed to the nearest Z and
      # read again until it settles; the last two reads averaged, which puts a
      # site hopping between two neighbours in between (four sites measured)
      work, reads = xs.deep_copy_scatterers(), []
      for it in range(4):
        reads.append(self.refinedElectronCounts(work))
        moved = False
        for s, z in zip(work.scatterers(), reads[-1]):
          e = min(z_of, key=lambda ez: abs(ez[1] - z))[0] if z else None
          if e and e != s.scattering_type.strip().capitalize():
            s.scattering_type, moved = e, True
        if not moved:
          break
        work.discard_scattering_type_registry()
      names, sites, z_est, us = [], flex.vec3_double(), [], []
      u_all = xs.extract_u_iso_or_u_equiv()
      u_med = sorted(u_all)[len(u_all)//2] if len(u_all) else 0.0
      for s, z, w, u in zip(xs.scatterers(), reads[-1],
                            reads[-2 if len(reads) > 1 else -1], u_all):
        z = (z + w)/2 if z and w else z
        if z is None:
          continue
        names.append(str(s.label))
        sites.append(s.site)
        z_est.append(z)
        us.append(u)
      if not names:
        return {}
      got = self.geometryProposals(xs.unit_cell(), xs.space_group(), sites)
      proposals = got[0] if got else []
      current = dict((str(s.label), s.scattering_type.strip().capitalize())
                     for s in xs.scatterers())
      changed, doubt = {}, []
      for j, (name, z, u) in enumerate(zip(names, z_est, us)):
        now = current[name]
        z_now = tiny_pse.table(now).atomic_number()
        heavier = [ez for ez in z_of if ez[1] > z_now]
        top = dict(proposals[j]) if j < len(proposals) else {}
        sigma = max(0.35, 0.04*z)
        score = dict((e, math.exp(-0.5*((z - ez)/sigma)**2)
                      * max(top.get(e, 0.0), 0.05)**0.5) for e, ez in z_of)
        tot = sum(score.values()) or 1.0
        # ponytail: a missing heavy atom reads far under its Z (Mo typed O read
        # 18) or its collapsed U absorbs the surplus and it reads its own Z (Ru
        # typed Cl at a fifth of the median U): either steps to the next
        # heavier element, the next round refines it and reads again
        # ponytail: a model whose median U sits under 0.01 is degenerate (the
        # wrong space group doubles every atom) and every U reads collapsed
        if heavier and (z > 1.5*z_now or 0.01 < u_med and u < 0.3*u_med):
          changed[name] = (now, min(heavier, key=lambda ez: ez[1])[0])
        # ponytail: a read within 0.3 of the own Z is left alone; a true N
        # typed C reads 6.4-6.9 and so do some carbons, so in that band the
        # Gaussian is flat over a Z and the geometry posterior decides
        elif abs(z - z_now) >= max(0.3, 0.03*z):
          best = max(score, key=score.get)
          if best != now:
            changed[name] = (now, best)
        final = changed.get(name, (now, now))[1]
        alt = [(e, p/tot) for e, p in sorted(score.items(), key=lambda ep: -ep[1])
               if e != final and p/tot >= 0.1]
        if alt:
          doubt.append((name, alt))
      type(self).doubt = doubt
      if not changed:
        print("Re-typed %d atoms after cleanup; no label changed" % len(names))
        self.printDoubt()
        return changed
      groups = {}
      for name, (old, new) in changed.items():
        groups.setdefault(new, []).append(name)
      for symbol, group in sorted(groups.items()):
        olex.m("sel %s" % " ".join(group))
        olex.m("name sel %s" % symbol)
        olex.m("sel -u")
      print("Re-typed %d atoms after cleanup; %d label(s) changed: %s"
            % (len(names), len(changed),
               ", ".join("%s %s->%s" % (n, o, w)
                         for n, (o, w) in sorted(changed.items()))))
      return changed
    except Exception as e:
      import traceback
      print("Re-typing after cleanup did not run (%s: %s); the labels are "
            "unchanged" % (type(e).__name__, e))
      if OV.IsDebugging():
        traceback.print_exc()
      return {}

  def multiTrialSolution(self, f_obs, params, extra, n_trials, verbose):
    """ Charge flipping from several random starts, keeping the best.

    The solving iterator already restarts itself when an attempt fails, but
    discards every restart and reports only the attempt that finally worked --
    so which random start it happened to get decides the answer. Here each
    attempt gets its own seed and is kept, and the one with the highest
    correlation peak height wins. Measured on real data this roughly doubles
    how often a structure solves, for a few seconds more.
    """
    from smtbx.ab_initio import multi_trial

    def olex_loop(solving, verbose=True, out=None):
      # Olex2's own loop, so that the progress plot and the stop button behave
      # exactly as they do for a single run.
      charge_flipping_loop(solving, verbose=verbose)
      return not OV.FindValue('stop_current_process', False)

    def progress(i_trial, n_trials, result):
      if result.error is not None:
        print("Trial %i/%i failed: %s" % (i_trial + 1, n_trials, result.error))
      elif result.cc_peak_height is not None:
        print("Trial %i/%i: correlation %.3f"
              % (i_trial + 1, n_trials, result.cc_peak_height))
      else:
        print("Trial %i/%i: no solution" % (i_trial + 1, n_trials))
      return not OV.FindValue('stop_current_process', False)

    result = multi_trial.solve(
      f_obs,
      n_trials=n_trials,
      weak_reflection_fraction=getattr(params, 'weak_reflection_fraction', 0.3),
      normalisations_for=getattr(extra, 'normalisations_for', None),
      max_solving_iterations=extra.max_solving_iterations,
      loop=olex_loop,
      callback=progress,
      verbose=verbose)
    multi_trial.show(result)
    # Kept for the space-group suggestions: every entry in f_calc_solutions has
    # had the currently assumed space group imposed on it, so the unsymmetrised
    # P1 structure factors are the only form that still carries what the data
    # alone said -- which is what a symmetry search has to be given.
    self.multi_trial_result = result
    return result.f_calc

  def suggestSpaceGroups(self, f_obs, n_suggestions=3):
    """ A short ranked list of candidate space groups for the P1 solution.

    Offering the best few *solutions* would be close to worthless -- measured,
    it is worth under one percentage point, because the solution is not what
    fails. Offering the best few *space groups* is worth several, because a
    structure that solves correctly and is then placed in the wrong group is
    the single commonest way this pipeline loses: on a uniform sample of the
    Crystallography Open Database, 149 structures did that for every 16 that
    failed the other way round.
    """
    from smtbx.ab_initio import space_group_suggest

    result = getattr(self, 'multi_trial_result', None)
    if result is None or result.f_calc_in_p1 is None:
      return None

    # Use the Laue class of whatever space group is currently set. That is not
    # a guess: the Laue class comes out of data reduction, from R_int over
    # unmerged symmetry equivalents, long before anyone tries to solve -- so by
    # the time this runs the user already knows it even if the full space group
    # is still open. Measured over 1395 structures it is worth 16 points of
    # top-3 space-group recovery (0.871 with it against 0.711 without), and it
    # is free.
    #
    # Skipped when the current group is P1, which usually means "nothing
    # determined yet" rather than "triclinic": deriving a Laue class of -1 from
    # it would restrict the shortlist to P1 and P-1 and throw away the answer.
    # In that case the candidates come from the solution map instead.
    laue = None
    try:
      current = f_obs.space_group()
      if current.order_z() > 1:
        from cctbx import sgtbx
        laue = sgtbx.space_group_info(
          group=current.build_derived_laue_group())
    except Exception:
      laue = None

    try:
      suggestion = space_group_suggest.suggest(
        f_obs, result.f_calc_in_p1, laue_group_info=laue,
        n_suggestions=n_suggestions)
    except Exception as e:
      print("Space-group suggestions unavailable: %s" % e)
      return None
    suggestion.cc_peak_height = result.cc_peak_height
    self._rerankByRefinedR1(f_obs, suggestion, result)
    space_group_suggest.show(suggestion)
    return suggestion

  def _rerankByRefinedR1(self, f_obs, suggestion, result):
    """ Re-order the shortlist by actually solving in each candidate.

    Everything `suggest` ranks on reads the **P1** solution, which is the same
    for every candidate, so none of it can separate the shortlist. The three
    solutions are the only evidence that differs, and refined free-R1 over them
    is worth +0.0097 GOAL on the completed COD screen (CI [+0.0076, +0.0120])
    once R1 is allowed to argue by magnitude and not only by rank -- see
    `composite.SG_R1_MARGIN`.

    **This is the expensive block**: it solves once per shortlisted group
    instead of not at all, so it is linear in `composite.N_SHORTLIST` (3). Set
    `SMTBX_SG_R1_RANK=0` to skip it and get exactly the previous ordering.

    Degrades to a no-op on any failure. The shortlist as `suggest` left it is a
    usable answer, and a re-ranking that raises must never be worse than not
    having tried.
    """
    import os

    if os.environ.get("SMTBX_SG_R1_RANK", "1") in ("", "0", "false", "False"):
      return
    entries = getattr(suggestion, "suggestions", None)
    if not entries or len(entries) < 2:
      return
    try:
      from smtbx.ab_initio import composite

      # The same cell-only estimate the peak search uses below. It reads the
      # unit cell and nothing else -- an atom count taken from the deposited
      # model is exactly the number a user does not have.
      n_heavy = max(1, int(f_obs.unit_cell().volume()
                           / 18.6/len(f_obs.space_group())))
      ranked = composite.choose_space_group(
        f_obs, entries, result.f_calc_in_p1, n_heavy)
      if not ranked:
        return

      # Map back to the caller's own objects. Matched by identity, because
      # `choose_space_group` carries `s.space_group_info` straight through --
      # matching on the symbol instead would merge two settings of one group.
      by_info = {}
      for e in entries:
        by_info.setdefault(id(e.space_group_info), []).append(e)
      order, seen = [], set()
      for r in ranked:
        for e in by_info.get(id(r["space_group_info"]), []):
          if id(e) not in seen:
            seen.add(id(e))
            e.r1 = r.get("r1")
            order.append(e)
            break
      # Candidates past N_SHORTLIST were never solved; they keep their order
      # behind the ones that were.
      for e in entries:
        if id(e) not in seen:
          order.append(e)
      if len(order) == len(entries):
        suggestion.suggestions = order
    except Exception as e:
      print("R1 re-ranking skipped: %s" % e)

  def settingNote(self, space_group_info):
    """ Say so when a suggested group is not in its reference setting.

    SHELXT reports this in its own `Orientation` column and reorients the cell
    when it helps; we generate the alternative settings as candidates already --
    `_settings_compatible_with` iterates settings rather than the 230 group
    numbers, because they differ in exactly which reflections are absent -- but
    we never told the user which one they ended up in.

    It is not a rare corner. Measured 6 August 2026 over Florian's 92 real
    structures, **26 (28%) are in a non-reference setting**:

        17  P 1 21/n 1  ->  P 1 21/c 1
         3  P c a b     ->  P b c a
         2  P 2 21 21   ->  P 21 21 2
         1  I 1 2/a 1   ->  C 1 2/c 1,  P n a b -> P b c n,
            P 1 2/n 1   ->  P 1 2/c 1,  P n a a -> P c c n

    **This reports and does not change anything**, which is the whole point.
    Those 17 monoclinic cases are not errors: P2(1)/n is chosen deliberately
    over P2(1)/c because it gives a beta angle nearer 90 degrees, it is what
    the community publishes, and silently "correcting" it would be wrong. The
    orthorhombic ones are axis-order differences, where the conventional
    setting usually is wanted -- but that is the user's call, not ours, and
    applying it means transforming the cell, the atoms and the reflections
    together rather than relabelling the group.

    Returns a short string, or None when the setting is already conventional.
    """
    try:
      if space_group_info.is_reference_setting():
        return None
      reference = space_group_info.reference_setting()
      cb_op = space_group_info.change_of_basis_op_to_reference_setting()
      by = cb_op.as_hkl()
    except Exception:
      return None
    system = space_group_info.group().crystal_system()
    if system == "Monoclinic":
      advice = ("this is the usual choice for such a cell and is normally "
                "kept; the conventional equivalent would be")
    else:
      advice = "the conventional setting of the same group is"
    return ("%s is a non-standard setting -- %s %s, reached by %s"
            % (space_group_info, advice, reference, by))

  def writeSuggestions(self, f_obs, result, max_files=3):
    """ One .res per suggested space group, written out for the user to pick.

    Deliberately the same mechanism the other solution route in Olex2 uses: files are
    written into temp/ and the table below links to them, so nothing in the
    user's model changes until they click a suggestion. Driving the model
    directly for each candidate would mean changing the space group and
    replacing the atoms three times before the user has chosen anything, and
    leaving it on whichever candidate happened to be last.

    Returns a list of (suggestion, res_path, n_peaks), best first.
    """
    import os
    from cctbx import maptbx, xray
    from cctbx.array_family import flex
    from iotbx.shelx import writer
    from smtbx.ab_initio import charge_flipping
    from smtbx.ab_initio import solve as ab_initio_solve  # noqa: F401

    out = []
    temp_dir = os.path.join(OV.StrDir(), "temp")
    if not os.path.exists(temp_dir):
      os.makedirs(temp_dir)

    # `result` is the suggestion object from space_group_suggest.suggest, which
    # carries candidates and evidence but no structure factors -- the solution
    # lives on the multi-trial result. Reading result.f_calc here was simply
    # wrong and raised AttributeError on the first real structure that produced
    # a shortlist.
    # Say which setting each candidate is in before the user picks one. The
    # `.res` files below are written in whatever setting the candidate came
    # from, so a user who chooses the second suggestion can end up in a
    # different setting from the first without anything having said so.
    for suggestion in getattr(result, 'suggestions', [])[:max_files]:
      note = self.settingNote(suggestion.space_group_info)
      if note:
        print("  " + note)

    solving = getattr(self, 'multi_trial_result', None)
    f_calc_in_p1 = getattr(solving, 'f_calc_in_p1', None) if solving else None
    if f_calc_in_p1 is None:
      return out

    for i, suggestion in enumerate(result.suggestions[:max_files]):
      sgi = suggestion.space_group_info
      # **Place the P1 solution; do not re-solve.** Re-solving in the group is
      # worth 37 points *for the answer the user keeps*, and the main solve
      # above already did it for the group actually chosen. These files are
      # previews of the alternatives, and `place_in` is a translation search
      # rather than a fresh solve -- which is what makes switching suggestions
      # feel instant instead of costing another eight trials per candidate.
      #
      # Measured on the first real GUI run: re-solving here took **148 s** of a
      # 167 s total, and then failed on all three candidates with "Maximum
      # number of attempts exceeded", so the user waited two and a half minutes
      # to be shown nothing. The shortlist is worthless if producing it costs
      # more than the solve.
      #
      # Wrapped per candidate: one candidate that cannot be placed must not
      # take the other two down with it.
      #
      # **Take the first symmetrisation, do not enumerate them all.**
      # `solve.place_in` calls `list()` on `f_calc_symmetrisations`, which on
      # this structure produced **403** candidates in 23.7 s per group. The
      # generator already yields best-first -- the first has cc_peak 0.9746,
      # which is the maximum over all 403 -- so `next()` returns the identical
      # answer in **0.06 s**. Three candidates: 71 s becomes 0.2 s.
      #
      # Done here rather than in `smtbx.ab_initio.solve` on purpose: that
      # module is watched by `code_stamp`, and editing it mid-run would change
      # the stamp of a benchmark that is measuring right now.
      try:
        f_obs_g = f_obs.customized_copy(
          space_group_info=sgi).merge_equivalents().array()
        best = next(iter(charge_flipping.f_calc_symmetrisations(
          f_obs_g, f_calc_in_p1, min_cc_peak_height=0.0)), None)
        f_calc = best[0] if best is not None else None
      except Exception as e:
        print("  cannot place the solution in %s (%s)" % (sgi, e))
        continue
      if f_calc is None:
        continue
      fft_map = f_calc.fft_map(symmetry_flags=maptbx.use_space_group_symmetry)
      fft_map.apply_volume_scaling()
      expected = 1.3*f_obs.unit_cell().volume()/18.6/len(f_calc.space_group())
      peaks = fft_map.peak_search(
        parameters=maptbx.peak_search_parameters(
          min_distance_sym_equiv=1.0, max_clusters=int(expected)),
        verify_symmetry=False).all()
      if peaks.sites().size() == 0:
        continue

      # Peaks are unlabelled, so every one becomes a carbon. Naming them and
      # guessing elements is a separate problem, and putting a wrong element in
      # the file would be a claim this pipeline has not earned.
      structure = xray.structure(
        crystal_symmetry=f_calc.crystal_symmetry().customized_copy(
          space_group_info=sgi))
      for j, site in enumerate(peaks.sites()):
        structure.add_scatterer(
          xray.scatterer(label="C%i" % (j + 1), site=site, u=0.06))

      path = os.path.join(temp_dir, "%s_sg%i.res" % (OV.FileName(), i + 1))
      try:
        with open(path, "w") as f:
          # **`full_matrix_least_squares_cycles` is not optional.**
          # `iotbx.shelx.writer.generator` asserts that at most one of the two
          # cycle arguments is None, so passing *neither* fails -- and it fails
          # as a bare `AssertionError` carrying no message, which printed as
          # "Could not write suggestion P 21 21 21: " with nothing after the
          # colon and cost an hour to trace. 4 matches the `L.S. 4` these files
          # are written with.
          #
          # **`sort_scatterers=False`.** The default sort raises
          # `TypeError: '<' not supported between instances of 'scatterer' and
          # 'scatterer'` -- `scatterer` never gained an ordering under Python 3,
          # so the writer's tidy-up cannot run at all here. The ordering is
          # cosmetic for a preview file the user is going to load and refine
          # anyway, and these peaks are already in descending height order,
          # which is more useful than by element.
          # The writer emits `TITL <title> in <space group>` itself, so a
          # title that already names the group comes out doubled:
          # "TITL 2016333 in P 21 21 21 in P 21 21 21".
          for line in writer.generator(
              structure,
              title=OV.FileName(),
              full_matrix_least_squares_cycles=4,
              sort_scatterers=False):
            f.write(line)
      except Exception as e:
        # A centric group in a non-origin-centric setting trips the *other*
        # assertion in the writer. Skip that candidate rather than lose the
        # whole table. Report the type as well as the text: this one is
        # message-less, so "%s" alone renders as nothing at all.
        print("Could not write suggestion %s: %s: %s"
              % (sgi, type(e).__name__, e or "(no message)"))
        continue
      out.append((suggestion, path, peaks.sites().size()))
    return out

  def suggestionsTableHtml(self, written, result):
    """ The solution chooser: one row per candidate, space group clickable.

    Same template and the same click action as the existing chooser
    (`method_imp/shelx.py::Method_shelxt.post_solution`), so the two solution
    routes present themselves identically and a user does not have to learn a
    second idiom.

    The columns differ because the evidence differs. There is deliberately
    **no R1 column here**, because it was measured to be
    actively misleading for choosing a space group: the solution is a P1
    solution, so imposing symmetry can only worsen the fit and R1 always
    favours the lowest-symmetry candidate whatever the truth. Showing it would
    invite exactly the wrong choice.

    **And no "Evidence" column.** `suggestion.reason` is a sentence, not a
    cell -- "25 predicted absences, 99% of them missing from the data (merged
    file, so they cannot be measured); centrosymmetry agrees with <|E^2-1|>" --
    and putting it in a table stretched every other column into uselessness.
    The evidence is already there in numeric form: `Absences` is the count
    with the judging test's percentage and `Centro` is the agreement. The prose still
    goes to the log, where there is room for it.

    Uses its own five-column template rather than ShelXT's `xt_output_table`,
    which is fixed at six cells and shared -- narrowing that one would have
    silently reshaped the ShelXT chooser too.
    """
    import gui.tools

    s_blank = gui.tools.TemplateProvider.get_template(
      'sg_output_table', force=OV.IsDebugging())
    header = {
      'td1': "<b>Correlation</b>", 'td2': "<b>Absences</b>",
      'td3': "<b>Centro</b>", 'td4': "<b>Peaks</b>",
      'td5': "<b>Space group</b>"}
    s = s_blank % header

    hkl_src = olx.file.ChangeExt(OV.FileFull(), 'hkl')
    for suggestion, path, n_peaks in written:
      sgi = suggestion.space_group_info
      link = ('<a href="file.copy(\'%s\',\'%s.res\')>>reap \'%s\'">%s</a>'
              % (path, OV.FileName(), OV.FileFull(), str(sgi)))
      # The same evidence the log prose gives: how many absences the group
      # predicts and what the test that judged it found.
      if suggestion.judged_by == "intensity":
        absences = "%d at %.0f%% I" % (suggestion.n_predicted_absent,
                                       100*suggestion.absence_ratio)
      elif suggestion.judged_by == "coverage":
        absences = "%d, %.0f%% missing" % (suggestion.n_coverage_absent,
                                           100*suggestion.coverage_margin)
      else:
        absences = "---"
      if suggestion.centric_agrees is None:
        centro = "---"
      elif suggestion.centric_agrees:
        centro = "<font color='green'>yes</font>"
      else:
        centro = "<font color='red'>no</font>"
      s += s_blank % {
        'td1': "%.3f" % (result.cc_peak_height or float('nan')),
        'td2': absences,
        'td3': centro,
        'td4': "%d" % n_peaks,
        'td5': "<b>%s</b>" % link}
      # The prose reason is not dropped, only moved: it is a sentence and
      # belongs in the log, where `space_group_suggest.show` already prints it.
    # No .hkl is copied alongside: the reflection file is the
    # user's own and is unchanged by which space group they pick. Only the
    # model file differs between candidates.
    return s

  def post_single_peak(self, xyz, height, cutoff=1.0, element=None,
                       number=None):
#    if height/self.peak_normaliser < cutoff:
#      return
#    sp = (height/self.peak_normaliser)
    sp = height #hp
    # A named peak becomes a typed atom; an unnamed one stays a Q peak with its
    # height as the label, which is the behaviour this has always had. The
    # number makes the label unique now: NewAtom("O") for every oxygen leaves
    # ten atoms called O until the file is written, and a name recorded then
    # finds one of them afterwards.
    label = "%.2f" % sp if not element else (
      "%s%d" % (element, number) if number else element)
    id = olx.xf.au.NewAtom(label, *xyz)
    if id != '-1':
      # Seeded per element rather than at a flat 0.06: see `startingUiso`.
      # An unnamed Q peak has no element to scale by and keeps the old value.
      u = self.startingUiso(element) if element else 0.06
      olx.xf.au.SetAtomU(id, "%.4f" % u)
      # The name is the key the tidy-up uses to find this peak again.
      try:
        return str(olx.xf.au.GetAtomName(id))
      except Exception:
        return None
    return None

class OlexCctbxFlipSolvent(OlexCctbxAdapter):
  """Recover the solvent density by charge flipping inside the region.

  The atomic model is the fixed channel and only the solvent region is free, so
  nothing here can move an atom or absorb residual through one. Flipping
  enforces positivity by changing the sign of weak density rather than by
  fitting anything, which is what makes it a weaker absorber of model error
  than the difference-map mask.

  Presents f_mask() and n_voids() like the other mask programs.
  """

  def __init__(self, recompute=True, show=False):
    OlexCctbxAdapter.__init__(self)
    from cctbx import miller
    from cctbx.array_family import flex
    from smtbx import masks
    import math

    OV.CreateBitmap("working")
    try:
      self.params = OV.Params().snum.masks
      xs = self.xray_structure()
      fo_sq = self.reflections.f_sq_obs_merged.average_bijvoet_mates()

      m = masks.mask(xs, fo_sq)
      m.compute(
        solvent_radius=getattr(self.params, 'flat_solvent_radius', 1.1),
        shrink_truncation_radius=getattr(self.params, 'flat_shrink_radius', 0.9),
        resolution_factor=self.params.resolution_factor,
        ignore_hydrogen_atoms=bool(getattr(
          self.params, 'flat_ignore_hydrogens', True)))
      self.flood_fill = m.flood_fill
      self.mask = m
      if m.n_voids() == 0:
        print("Flip solvent: no solvent-accessible region")
        self._f_mask = None
        olx.current_mask = self
        return

      region = (m.mask.data.as_1d() >= 2).as_double()
      region.reshape(m.mask.data.accessor())
      f_obs = fo_sq.f_sq_as_f()
      f_calc = fo_sq.structure_factors_from_scatterers(
        xray_structure=xs, algorithm="direct").f_calc()
      fft_scale = xs.unit_cell().volume()/region.size()

      n_cycles = int(getattr(self.params, 'flip_cycles', 12))
      delta_sigma = float(getattr(self.params, 'flip_threshold_sigma', 0.4))
      f_mask = flex.complex_double(f_calc.data().size(), 0)
      r_last = None
      for cycle in range(n_cycles):
        total = f_calc.data() + f_mask
        modulus = flex.abs(total)
        denom = flex.sum(modulus*modulus)
        scale = flex.sum(f_obs.data()*modulus)/denom if denom > 0 else 1.0
        # the residual amplitude, phased by the current model
        amplitudes = f_obs.data()/scale - modulus
        phases = flex.arg(total)
        negative = amplitudes < 0
        ph = phases.deep_copy()
        ph.set_selected(negative, ph.select(negative) + math.pi)
        coefficients = miller.array(
          miller_set=f_calc,
          data=flex.polar(flex.abs(amplitudes), ph))
        rho = miller.fft_map(m.crystal_gridding, coefficients)
        rho.apply_volume_scaling()
        rho_s = rho.real_map_unpadded()*region
        # charge flipping proper: weak density changes sign, strong is kept.
        # The threshold is in sigma of the region so it follows the data rather
        # than being an absolute number of electrons.
        inside = rho_s.as_1d().select(region.as_1d() > 0)
        sigma = flex.mean_sq(inside)**0.5 if inside.size() else 0.0
        delta = delta_sigma*sigma
        weak = rho_s.as_1d() < delta
        flipped = rho_s.as_1d().deep_copy()
        flipped.set_selected(weak, -flipped.select(weak))
        flipped.reshape(rho_s.accessor())
        flipped = flipped*region
        f_mask = f_obs.structure_factors_from_map(map=flipped).data()*fft_scale
        r = flex.sum(flex.abs(f_obs.data()/scale
                              - flex.abs(f_calc.data() + f_mask))) \
            / flex.sum(f_obs.data()/scale)
        r_last = r
      self._f_mask = f_obs.customized_copy(data=f_mask)
      electrons = flex.sum(flipped)*fft_scale
      print("Flip solvent: %d cycles, threshold %.2f sigma, %d void(s), "
            "%.0f electrons in the region, R %.4f"
            % (n_cycles, delta_sigma, m.n_voids(), electrons, r_last))
      with open('%s/%s-mask.log' %(OV.FilePath(), OV.FileName()), 'w') as f:
        print("Solvent by charge flipping in the region", file=f)
        print("cycles %d" % n_cycles, file=f)
        print("threshold %.3f sigma" % delta_sigma, file=f)
        print("electrons %.1f" % electrons, file=f)
        print("R after flipping %.4f" % r_last, file=f)
      olx.current_mask = self
    finally:
      OV.DeleteBitmap("working")

  def f_mask(self):
    return self._f_mask

  def n_voids(self):
    return self.flood_fill.n_voids()

OV.registerFunction(OlexCctbxFlipSolvent)


class OlexCctbxFlatSolvent(OlexCctbxAdapter):
  """A flat two-parameter bulk solvent, as macromolecular programs use.

  f_model = f_calc + k_sol * exp(-B_sol s^2/4) * FT(solvent region)

  The region comes from the atoms alone, never from the data, and only k_sol
  and B_sol are fitted. That is the whole difference from OlexCctbxMasks, which
  reads the solvent density out of the difference map and so has enough freedom
  to absorb the model's residual.

  Measured on ten proteins, fitted on the working reflections and scored on the
  free ones: this gains 13.3% in R_free in the lowest shell and 0.0% in the
  outer third, where the difference-map mask gains 1.2% and *loses* 14.8%. It
  also recovers k_sol between 0.30 and 0.50 e/A^3 against liquid water at
  0.334, unprompted.

  Presents f_mask() and flood_fill like OlexCctbxMasks so that the refinement
  dispatch can treat the three programs alike.
  """

  def __init__(self, recompute=True, show=False):
    OlexCctbxAdapter.__init__(self)
    from cctbx.array_family import flex
    from smtbx import masks

    OV.CreateBitmap("working")
    try:
      self.params = OV.Params().snum.masks
      xs = self.xray_structure()
      fo_sq = self.reflections.f_sq_obs_merged.average_bijvoet_mates()

      m = masks.mask(xs, fo_sq)
      # macromolecular geometry, not the difference-map mask's: probe 1.1
      # against 1.2, shrink 0.9 against 1.2, and hydrogens left out. The
      # first comparison used Olex2's small-molecule values for both arms,
      # which handicapped this one - the shrink radius in particular eats
      # more of the region, and a protein's thousands of hydrogens shrink
      # and roughen it further.
      m.compute(
        solvent_radius=getattr(self.params, 'flat_solvent_radius', 1.1),
        shrink_truncation_radius=getattr(
          self.params, 'flat_shrink_radius', 0.9),
        resolution_factor=self.params.resolution_factor,
        ignore_hydrogen_atoms=bool(getattr(
          self.params, 'flat_ignore_hydrogens', True)))
      self.flood_fill = m.flood_fill
      self.crystal_gridding = m.crystal_gridding
      self.mask = m
      if m.n_voids() == 0:
        print("Flat solvent: no solvent-accessible region, nothing to add")
        self._f_mask = None
        olx.current_mask = self
        return

      region = (m.mask.data.as_1d() >= 2).as_double()
      region.reshape(m.mask.data.accessor())
      self.region_scale = xs.unit_cell().volume()/region.size()
      self.region = region

      f_obs = fo_sq.f_sq_as_f()
      f_calc = fo_sq.structure_factors_from_scatterers(
        xray_structure=xs, algorithm="direct").f_calc()
      f_solv = fo_sq.set().structure_factors_from_map(map=region)
      f_solv = f_solv.data()*self.region_scale
      ss = fo_sq.sin_theta_over_lambda_sq().data()

      k_lo, k_hi, k_n = self.params.flat_k_sol_range
      b_lo, b_hi, b_n = self.params.flat_b_sol_range
      best = None
      for i in range(int(k_n)):
        k_sol = k_lo + (k_hi - k_lo)*i/max(1, int(k_n) - 1)
        for j in range(int(b_n)):
          b_sol = b_lo + (b_hi - b_lo)*j/max(1, int(b_n) - 1)
          trial = flex.abs(f_calc.data() + k_sol*flex.exp(-b_sol*ss)*f_solv)
          denom = flex.sum(trial*trial)
          scale = flex.sum(f_obs.data()*trial)/denom if denom > 0 else 1.0
          r = flex.sum(flex.abs(f_obs.data() - scale*trial)) \
              / flex.sum(f_obs.data())
          if best is None or r < best[0]:
            best = (r, k_sol, b_sol)
      self.r_fit, self.k_sol, self.b_sol = best
      self._f_mask = f_obs.customized_copy(
        data=self.k_sol*flex.exp(-self.b_sol*ss)*f_solv)

      volume = m.n_solvent_grid_points()/m.mask.data.size() \
          * xs.unit_cell().volume()
      print("Flat solvent: k_sol %.2f e/A^3, B_sol %.0f A^2, %d void(s), "
            "%.0f A^3 (%.1f%% of the cell), R %.4f"
            % (self.k_sol, self.b_sol, m.n_voids(), volume,
               100.0*m.n_solvent_grid_points()/m.mask.data.size(), self.r_fit))
      with open('%s/%s-mask.log' %(OV.FilePath(), OV.FileName()), 'w') as f:
        print("Flat two-parameter bulk solvent", file=f)
        print("k_sol %.4f e/A^3" % self.k_sol, file=f)
        print("B_sol %.2f A^2" % self.b_sol, file=f)
        print("solvent volume %.1f A^3" % volume, file=f)
        print("R after fitting %.4f" % self.r_fit, file=f)
      olx.current_mask = self
    finally:
      OV.DeleteBitmap("working")

  def f_mask(self):
    return self._f_mask

  def n_voids(self):
    return self.flood_fill.n_voids()

OV.registerFunction(OlexCctbxFlatSolvent)


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
      # set before compute() so structure_factors sees it; getattr because the
      # cctbx bundle here is refreshed separately from this working copy
      if hasattr(mask, 'boundary_smearing'):
        mask.boundary_smearing = getattr(
          self.params, 'boundary_smearing', 0) or 0
        if mask.boundary_smearing:
          print("Mask boundary smeared over %.2f x the %.2f A solvent radius"
                % (mask.boundary_smearing, self.params.solvent_radius))
      else:
        print("This cctbx has no mask boundary smearing; refresh the bundle")
      # the occupancy correction lives in smtbx.masks, so an older bundle
      # simply will not have it and the flag is skipped rather than set
      if hasattr(mask, 'occupancy_weighting'):
        mask.occupancy_weighting = bool(
          getattr(self.params, 'occupancy_weighting', False))
        if mask.occupancy_weighting:
          print("Mask gives back solvent excluded by partial occupancy")
      if hasattr(mask, 'bias_correction'):
        mask.bias_correction = bool(
          getattr(self.params, 'bias_correction', False))
        if mask.bias_correction:
          print("Difference map weighted by sigma_A: m*Fo - D*Fc")
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
      self.check_mask_is_solvent(mask, log=out)
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

  def check_mask_is_solvent(self, mask, log):
    """Two sanity checks on the mask that need no known answer.

    Both catch the same failure - a mask that is fitting something other than
    solvent - and both work on real data, where the solvent content is exactly
    what nobody knows.

    Liquid water is 0.334 e/A^3, and disordered solvent in a channel is that at
    most, usually well under it. Above it the region is not holding solvent.

    Disordered solvent also scatters at low angle alone, so f_mask surviving in
    the outer half of the data means the region is holding something that is
    not disordered solvent. That is either ordered solvent, which is real and
    should be kept, or the model's own error coming through the region cut,
    which should not. The two look the same here and only a refinement tells
    them apart - on a 0.48 A protein, band limiting the map at 3 A cost the
    whole benefit of the mask, so the content there was doing real work.
    Reported rather than acted on for that reason; solvent_d_min is the
    control, and it has to be chosen per structure.
    """
    water = 0.334
    if mask.n_voids() == 0 or not mask.solvent_accessible_volume: return
    rho = sum(mask.electron_counts_per_void())/mask.solvent_accessible_volume
    print("Mean density in the solvent region = %.3f e/A^3 (%.2f x liquid "
          "water)" % (rho, rho/water), file=log)
    if rho > water:
      print("  ** denser than liquid water, so this is not solvent alone",
            file=log)
    f_mask = mask.f_mask()
    if f_mask is None: return
    f_calc = mask.f_calc.common_set(f_mask)
    f_mask = f_mask.common_set(f_calc)
    if f_mask.size() == 0: return
    d = f_calc.d_spacings().data()
    cut = flex.sorted(d)[int(0.5*(d.size() - 1))]
    sel = d < cut
    denominator = flex.mean(flex.abs(f_calc.select(sel).data()))
    if denominator <= 0: return
    hi = 100*flex.mean(flex.abs(f_mask.select(sel).data()))/denominator
    print("f_mask beyond %.2f A = %.1f%% of f_calc there" % (cut, hi), file=log)
    if hi > 5:
      print("  ** disordered solvent cannot scatter there, so the region holds "
            "ordered solvent or the model's error. snum.masks.solvent_d_min "
            "limits it - check wR2 and GooF, not R1, before keeping the limit",
            file=log)

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
    one_h = None
    if OV.IsNoSpherA2():
      from variableFunctions import nsa2_get_param
      table_name = str(nsa2_get_param("file"))
      table_name = table_name.lstrip().rstrip()
      xray_structure = mask.xray_structure
      one_h = direct.f_calc_modulus_squared(
        xray_structure, scatterer_contribution=get_table_contribution(
          xray_structure, table_name))
    #if self.hklf_code >= 5 or self.twin_components:
    if self.hklf_code >= 5:
      mask.use_set_completion = False
      mask.scale_factor = OV.GetOSF()
      fo2 = self.reflections.f_sq_obs
      miller_set = miller.set(
        crystal_symmetry=fo2.crystal_symmetry(),
        indices=fo2.indices(),
        anomalous_flag=fo2.anomalous_flag())\
          .unique_under_symmetry().map_to_asu()
      fc = self.f_calc(miller_set, self.exti is not None, True, False,
                      one_h_function=one_h, twin_data=False)
      obs = fo2.as_xray_observations(
        scale_indices=self.reflections.batch_numbers_array.data(),
        twin_fractions=self.twin_fractions,
        twin_components=self.twin_components)
      dtw = obs.detwin(
        fo2.crystal_symmetry().space_group(),
        fo2.anomalous_flag(),
        fc.indices(),
        fc.as_intensity_array().data(), True)
      fo2 = miller.array(
          miller_set=miller.set(
            crystal_symmetry=mask.xray_structure.crystal_symmetry(),
            indices=dtw.indices,
            anomalous_flag=fo2.anomalous_flag()),
          data=dtw.data,
          sigmas=dtw.sigmas).set_observation_type(fo2)
      fo2 = fo2.merge_equivalents(algorithm="shelx").array()\
        .average_bijvoet_mates().map_to_asu()
      fc = fc.customized_copy(crystal_symmetry=fo2.crystal_symmetry())
      fc = fc.common_set(fo2)
      if fc.size() != fo2.size():
        fo2 = fo2.common_set(fc)

      mask.fo2, mask.f_calc = fo2, fc
    else:
      mask.f_calc = self.f_calc(f_calc_set, one_h_function=one_h)
      mask.scale_factor = None

    f_obs = mask.f_obs()
    if mask.scale_factor is None:
      mask.scale_factor = flex.sum(f_obs.data())/flex.sum(
        flex.abs(mask.f_calc.data()))
    # through the mask, so that bias_correction reaches both sites. getattr
    # because the cctbx bundle here is refreshed separately from this copy.
    coeffs = getattr(mask, '_difference_coefficients', None)
    if coeffs is None:
      coeffs = lambda fo, fc: fo.f_obs_minus_f_calc(1/mask.scale_factor, fc)
    f_obs_minus_f_calc = coeffs(f_obs, mask.f_calc)
    mask.fft_scale = mask.xray_structure.unit_cell().volume()\
        / mask.crystal_gridding.n_grid_points()
    epsilon_for_min_residual = 2
    mask._electron_counts_per_void = mask.n_voids() * [0]
    # once, the mask being fixed through the iteration. getattr so an older
    # cctbx bundle still runs, with the hard edge it has always had.
    if hasattr(mask, 'solvent_weight_map'):
      solvent_weight = mask.solvent_weight_map()
    else:
      solvent_weight = mask.mask.data.as_double()
      solvent_weight.set_selected(solvent_weight > 0, 1.)
    # F(000) is not measured, so the difference map has zero mean over the
    # cell and the region integrates to Q(1 - <w>) instead of Q. The bundled
    # cctbx solves for that level, and for the clamp when it is on, in one
    # step; without it, fall back to dividing the factor out afterwards, which
    # is the same thing whenever nothing is clamped.
    level_and_clamp = getattr(mask, '_level_and_clamp', None)
    n_grid = mask.crystal_gridding.n_grid_points()
    grid_scale = n_grid/(n_grid - mask.n_solvent_grid_points())
    solvent_d_min = getattr(self.params, 'solvent_d_min', None) or None
    if solvent_d_min is not None:
      print("Solvent sought in data beyond %.1f A only" % solvent_d_min)
    for i in range(max_cycles):
      coefficients = f_obs_minus_f_calc
      if solvent_d_min is not None:
        coefficients = coefficients.resolution_filter(d_min=solvent_d_min)
      mask.diff_map = miller.fft_map(mask.crystal_gridding, coefficients)
      mask.diff_map.apply_volume_scaling()
      # multiplied by the weight, not cut by a selection, so boundary_smearing
      # rounds the edge. This method is a second copy of van der Sluis and
      # Spek, kept here because the mask needs Olex2's f_calc (NoSpherA2
      # tables), so the same change in smtbx.masks does nothing for Olex2 and
      # both have to carry it.
      masked_diff_map = mask.diff_map.real_map_unpadded()*solvent_weight
      if level_and_clamp is not None:
        masked_diff_map, f_000_s = level_and_clamp(
          masked_diff_map, solvent_weight, mask.diff_map.statistics().sigma())
      else:
        f_000_s = flex.sum(masked_diff_map)*mask.fft_scale*grid_scale
        masked_diff_map.add_selected(
          mask.mask.data.as_double() > 0,
          f_000_s/mask.xray_structure.unit_cell().volume())
      for j in range(mask.n_voids()):
        # read off the levelled map: before the level is restored every void
        # still carries its share of the missing F(000), and a void would then
        # be discarded for holding less than that share rather than nothing
        selection = mask.mask.data == j+2
        if mask.exclude_void_flags[j]:
          masked_diff_map.set_selected(selection, 0)
          continue
        diff_map_ = masked_diff_map.deep_copy().set_selected(~selection, 0)
        electrons = flex.sum(diff_map_) * mask.fft_scale
        if electrons < 0:
          masked_diff_map.set_selected(selection, 0)
          mask.exclude_void_flags[j] = True
          f_000_s -= electrons
          electrons = 0
        if OV.IsEDData():
          electrons *= 3.324943664
        mask._electron_counts_per_void[j] = electrons
      mask.f_000 = flex.sum(masked_diff_map) * mask.fft_scale
      previous_f_000_s = mask.f_000_s
      mask.f_000_s = f_000_s
      mask._masked_diff_map = masked_diff_map
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
      # tested last, so that the map, f_mask and the count the object reports
      # all come from one and the same cycle
      if (previous_f_000_s is not None and
          approx_equal_relatively(previous_f_000_s, f_000_s, 0.001)):
        break
      f_model = mask.f_model(epsilon=epsilon_for_min_residual)
      f_obs = mask.f_obs()
      f_obs_minus_f_calc = coeffs(f_obs.phase_transfer(f_model), mask.f_calc)
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
          OV.SetControlValue('SET_SNUM_CALCSOLV_PROBE', solvent_radius)

      elif item == 'grid':
        if not grid_step:
          grid_step = val
        else:
          OV.SetParam('snum.calcsolv.%s'%item,grid_step)
          OV.SetControlValue('SET_SNUM_CALCSOLV_GRID', grid_step)
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
    sfac_elms = set([x.lower() for x in sfac.keys() if 'gaussian' in sfac[x]])
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

# The last table read, as (key, contribution, uncovered). A refinement, the map
# that follows it and every reflection statistic each ask for the same file, and
# reading one costs time and memory proportional to its size. Only one is kept:
# tables are large, and it is the file just used that gets asked for again.
_cached_table = [None, None, []]


def _table_cache_key(xray_structure, table_file_name):
  """ What has to match for a table already read to be usable again.

  Everything the table is built from has to be in here, because a stale table
  is not a slow answer but a wrong one: the columns would be put on the wrong
  atoms and every number downstream would look perfectly plausible. So the key
  covers the file, and each thing build() consumes --

    - the element and the part of every scatterer, in order, which is what the
      entries are matched on;
    - the labels too, which nothing matches on but which catch an edit the
      rest would miss;
    - the cell, which the matching measures distances in;
    - the space group and with it the anomalous flag, which the reflection
      lookup is built from.

  Coordinates are left out on purpose: they move every cycle, and a structure
  that has refined still wants the same table. That is the one thing here
  allowed to change.
  """
  stat = os.stat(table_file_name)
  scatterers = xray_structure.scatterers()
  space_group = xray_structure.space_group()
  return (os.path.normcase(os.path.abspath(table_file_name)),
          stat.st_mtime_ns, stat.st_size,
          tuple((sc.label, sc.scattering_type, sc.get_part())
                for sc in scatterers),
          tuple(xray_structure.unit_cell().parameters()),
          str(space_group.type().hall_symbol()),
          bool(space_group.is_origin_centric()))


# The file state (path, mtime, size) whose provenance was last reported on.
# Hashing a table is proportional to its size and tables reach gigabytes, so the
# question is asked once per version of a file rather than once per use.
_table_provenance_checked = [None]


def _table_name_for_log(table_file_name):
  """ The table's file name as it can be printed wherever the log is going.

  Inside Olex2 a print is handed to olex.post as str and nothing here encodes
  it, but a headless run writes to a real stream, and one in a single-byte
  code page raises on a name it cannot spell -- a folder named in Chinese on a
  Western Windows. A warning about a table must not be what stops a refinement,
  so the name is made spellable and the unspellable characters escaped.
  """
  import sys
  name = os.path.basename(table_file_name)
  encoding = getattr(sys.stdout, 'encoding', None)
  if encoding:
    try:
      name.encode(encoding)
    except (UnicodeEncodeError, LookupError):
      name = name.encode(encoding, 'backslashreplace').decode(encoding)
  return name


def check_table_readable(table_file_name):
  """ Read the table's scatterer block, and nothing else, to find out whether
  the table can be framed at all.

  The reader downstream cannot report this. An id block read at the wrong record
  width -- the marker named an 8-byte record before 29 July 2026 and a 16-byte
  one after -- is not rejected, it is misframed, and what comes back is a table
  matching no atom rather than an error. That reads as a modelling problem,
  which is how it was reported to us. One row per atom is affordable in front of
  every use, so it is checked here, where every use passes.
  """
  from tsc_scatterer_resync import read_scatterers, ScattererResolutionError
  try:
    return read_scatterers(table_file_name)
  except ScattererResolutionError:
    raise
  except (OSError, ValueError, IndexError, UnicodeDecodeError) as error:
    raise ScattererResolutionError(
      "%s cannot be read as a scattering table: %s" % (
        _table_name_for_log(table_file_name), error))


def _report_table_provenance(table_file_name):
  """ Say, in the log, when the table about to be read is not the one the model
  recorded, or came from somewhere the model does not know.

  A refinement asks this itself and stops on the answer. Everything else that
  reads a table asked nothing, and a map is where that matters most: a table
  belonging to another model draws residual density which somebody then models
  as an atom. Here it warns rather than refuses - a map is a diagnostic, and it
  is the refinement that must not proceed.
  """
  try:
    from variableFunctions import nsa2_get_param
    from NoSpherA2.utilities import nsa2_validate_tsc_file_integrity,       nsa2_check_tsc_origin_known
    current = str(nsa2_get_param('file') or '').strip()
    if not current or os.path.basename(current) != os.path.basename(table_file_name):
      return
    stat = os.stat(table_file_name)
    state = (os.path.normcase(os.path.abspath(table_file_name)),
             stat.st_mtime_ns, stat.st_size)
    if _table_provenance_checked[0] == state:
      return
    _table_provenance_checked[0] = state
    # acknowledge=False: a mismatch is forgiven by being seen once, and that one
    # warning belongs to the refinement, which is what offers to proceed on it
    is_valid, stored_hash, current_hash, reason =       nsa2_validate_tsc_file_integrity(acknowledge=False)
    if not is_valid:
      if reason == 'mismatch':
        print("WARNING: %s does not match the hash stored with this structure"
              " (%s... on disk, %s... recorded)." % (
                _table_name_for_log(table_file_name), current_hash[:16],
                stored_hash[:16]))
        print("  It was replaced, restored or written for another model, so what"
              " is drawn from it may not belong to this structure.")
      else:
        print("WARNING: the scattering table could not be validated: %s" % reason)
    origin_known, origin = nsa2_check_tsc_origin_known()
    if not origin_known:
      print("WARNING: the origin of %s is %s - nothing records how it was"
            " calculated." % (_table_name_for_log(table_file_name),
                              origin if origin else '(empty)'))
  except Exception as error:
    # provenance is a report, not a gate: a structure carrying no NoSpherA2
    # metadata must still be able to draw a map
    print("Note: could not check the provenance of the scattering table: %s" % error)


def get_table_contribution(xray_structure, table_file_name):
  """ The tabulated table for this structure, read afresh only if it has to be.
  """
  from smtbx.structure_factors import direct
  check_table_readable(table_file_name)
  _report_table_provenance(table_file_name)
  try:
    key = _table_cache_key(xray_structure, table_file_name)
  except OSError:
    key = None
  if key is not None and _cached_table[0] == key:
    return _cached_table[1]
  # a table need not name every atom in the model. Rather than refuse it, the
  # atoms it misses get ordinary spherical form factors -- which is a weaker
  # model for those atoms, so it is reported rather than done quietly.
  contribution = direct.ext.table_based_scatterer_contribution.\
    build_with_fallback(
      xray_structure.unit_cell(),
      xray_structure.scatterers(),
      table_file_name,
      xray_structure.space_group(),
      not xray_structure.space_group().is_origin_centric(),
      xray_structure.scattering_type_registry())
  scatterers = xray_structure.scatterers()
  fallback = [scatterers[i].label
              for i in contribution.scatterers_not_in_table()]
  if fallback:
    _report_table_fallback(table_file_name, fallback, scatterers.size())
    # Not cached. The spherical half of a partially tabulated contribution
    # reads the scatterers as it goes, so that fp, fdp and the rest follow the
    # refinement -- which means it is tied to the scatterer array it was built
    # from. A later refinement builds a new one, and reusing this would quietly
    # serve values from the previous structure. Re-reading the file each time
    # is the cost of that, and a table which does not cover the model is the
    # exceptional case.
    key = None
  # replace rather than accumulate: holding two tables at once is costly
  _cached_table[0], _cached_table[1], _cached_table[2] = \
    key, contribution, fallback
  return contribution


def _report_table_fallback(table_file_name, fallback, n_scatterers):
  """ Say, in the log, which atoms the table did not cover. """
  print("")
  print("WARNING: %s covers %d of %d atoms." % (
    _table_name_for_log(table_file_name), n_scatterers - len(fallback),
    n_scatterers))
  print("  These atoms are refined with spherical scattering factors"
        " instead:")
  for i in range(0, len(fallback), 10):
    print("    " + " ".join(fallback[i:i + 10]))
  print("  Re-run NoSpherA2 over the whole model to tabulate them all.")
  print("")


def note_table_not_used():
  """ This refinement used no table: drop the one held.

  The cache is meant to survive a refinement, because the map and the
  statistics that follow one ask for the same file again. A refinement that
  consults no table at all is the other thing entirely -- the model has been
  switched back to spherical scattering factors, and nothing after it is going
  to want that table either, so holding it costs memory for nothing.

  This also clears the coverage report, which is what stops the atoms a
  previous table failed to cover from being named again after a refinement
  that never looked at one.
  """
  forget_cached_table()


def get_table_fallback_atoms():
  """ The atoms the table last read did not cover, by label.

  Empty when the table covered the whole model, which is the normal case, and
  empty when no table is held at all.
  """
  return list(_cached_table[2])


def forget_cached_table():
  """ Drop the cached table, freeing it.

  Nothing needs to call this for correctness -- a table that no longer suits
  the structure is not reused, it is replaced. It is here for memory: the one
  table held stays until another is read.
  """
  had = _cached_table[0] is not None
  _cached_table[0], _cached_table[1], _cached_table[2] = None, None, []
  return had
OV.registerFunction(forget_cached_table, False, "sfac")


def get_one_h_function(xray_structure, table_file_name):
  from smtbx.structure_factors import direct
  from smtbx_refinement_least_squares_ext import f_calc_function_default
  try:
    return f_calc_function_default(direct.f_calc_modulus_squared(
      xray_structure, scatterer_contribution=get_table_contribution(
        xray_structure, table_file_name)))
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


