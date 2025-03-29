import boost_adaptbx.boost as boost
from warnings import catch_warnings
ext = boost.python.import_ext("smtbx_refinement_least_squares_ext")
from smtbx_refinement_least_squares_ext import *


import smtbx.refinement.weighting_schemes # import dependency
from cctbx import xray
from libtbx import adopt_optional_init_args
from scitbx import linalg
from scitbx.lstbx import normal_eqns
from scitbx.array_family import flex
from smtbx.structure_factors import direct
from smtbx.refinement.restraints import origin_fixing_restraints
from smtbx.refinement import least_squares
import math
import sys

from olexFunctions import OV

import olex
import olex_core
import olx

def leverage_normal_eqns_builder():
  def get_base_class():
    OpenMP = OV.GetParam('user.refinement.use_openmp')
    if OpenMP == True:
      from scitbx.lstbx import normal_eqns
      return least_squares.crystallographic_ls_class(
        normal_eqns.non_linear_ls_with_separable_scale_factor_BLAS_2)
    return least_squares.crystallographic_ls_class()

  class leverage_normal_eqns(get_base_class()):
    log = None
    std_reparametrisation = None
    std_observations = None

    def __init__(self, observations, refinement, olx_atoms, table_file_name=None, **kwds):
      super(leverage_normal_eqns, self).__init__(
        observations, refinement.reparametrisation, initial_scale_factor=OV.GetOSF(), **kwds)
      if table_file_name:
        one_h_linearisation = direct.f_calc_modulus_squared(
          self.xray_structure, table_file_name=table_file_name)
      else:
        one_h_linearisation = direct.f_calc_modulus_squared(
          self.xray_structure, reflections=self.observations)
      self.one_h_linearisation = f_calc_function_default(one_h_linearisation)

  return leverage_normal_eqns

class Leverage(object):
  def __init__(self):
    pass

  def for_flack(self, max_reflections=5, output_to=None):
    from refinement import FullMatrixRefine

    fmr = FullMatrixRefine()
    if fmr.xray_structure().space_group().is_centric():
      print("Centric space group - nothing to do")
      return

    from cctbx import sgtbx
    from cctbx.xray import observations
    from scitbx.lstbx import normal_eqns_solving

    obs = None
    refine = True
    # BASF 1 in already?
    if fmr.twin_components is not None and len(fmr.twin_components):
      if fmr.twin_components[0].twin_law.as_double() == sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1)).as_double():
        obs = fmr.observations
        refine = False
    elif fmr.twin_fractions and len(fmr.twin_fractions):
      pass
    else:
      obs = fmr.observations

    if not obs:
      fo2 = fmr.reflections.f_sq_obs_filtered
      fc = fmr.f_calc(None, fmr.exti is not None, True, True)
      obs = fmr.observations.detwin(
        fo2.crystal_symmetry().space_group(),
        fo2.anomalous_flag(),
        fc.indices(),
        fc.as_intensity_array().data(), False)
      obs.fo_sq = fo2

    if refine:
      it = xray.twin_component(sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1)), 0.2, True)
      fmr.observations = observations.customized_copy(obs, obs.fo_sq.crystal_symmetry().space_group(), [], (it,))
      fmr.twin_components = (it,)
      fmr.twin_fractions = ()

    normal_eqns = fmr.run(build_only=True, normal_equations_class_builder=leverage_normal_eqns_builder)

# need to refine if invertion twin has been added
    if refine:
      from libtbx import utils
      print("Refining the structure...")
      normal_eqns_solving.naive_iterations(
        normal_eqns, n_max_iterations=10,
        gradient_threshold=1e-7,
        step_threshold=1e-4)
      flack = fmr.twin_components[0].value
      t_vcv = normal_eqns.covariance_matrix(
        jacobian_transpose=fmr.reparametrisation.jacobian_transpose_matching(
          fmr.reparametrisation.mapping_to_grad_fc_independent_scalars))
      su = math.sqrt(t_vcv.matrix_packed_u_diagonal()[0])
      flack = utils.format_float_with_standard_uncertainty(flack, su)
      print("Flack parameter has been refined to: %s" %flack)
      normal_eqns.reset()
# end of the structure refinement
    calculate(normal_eqns, None, ["BASF1"], max_reflections=max_reflections, output_to=output_to)

  def calculate(self, threshold=0.01, max_reflections=5):
    from refinement import FullMatrixRefine
    dmb = FullMatrixRefine().run(build_only=True)
    calculate(dmb, float(threshold), None, max_reflections=max_reflections, output_to=None)

  def calculate_for(self, params, max_reflections=5, output_to=None):
    from refinement import FullMatrixRefine
    dmb = FullMatrixRefine().run(build_only=True)
    calculate(dmb, None, params.decode().split(' '), max_reflections=max_reflections, output_to=output_to)

  # figure out the crystallographic parameter labels
def parameter_labels(self, n_params):
  annotations = [x for x in self.reparametrisation.component_annotations]
  annotations_1 = []
  labels = []
  ann_1_idx = 0
  if self.reparametrisation.twin_fractions is not None:
    basf_n = 1
    for fraction in self.reparametrisation.twin_fractions:
      if fraction.grad:
        annotations_1.append("BASF%s" %basf_n)
        basf_n += 1
  if self.reparametrisation.fc_correction is not None and self.reparametrisation.fc_correction.grad:
    if isinstance(self.reparametrisation.fc_correction, xray.shelx_extinction_correction):
      annotations_1.append("EXTI")
    else:
      annotations_1.append("SWAT.U")
      annotations_1.append("SWAT.G")
  if self.reparametrisation.thickness is not None and self.reparametrisation.thickness.grad:
    annotations_1.append("Thickness")

  Jt = self.reparametrisation.jacobian_transpose_matching_grad_fc()
  for j in range(0, n_params):
    label = []
    for k in range(0, Jt.n_cols):
      if Jt[(j,k)]:
        label.append("%s" %(annotations[k]))
    if len(label) == 0:
      label.append(annotations_1[ann_1_idx])
      ann_1_idx += 1
    labels.append(", ".join(label))
  return labels

def calculate(self, threshold, params, max_reflections, output_to):
  max_reflections = int(max_reflections)
  import numpy as np
  import scipy.linalg as scla

  if self.f_mask is None:
    f_mask_data = MaskData(flex.complex_double())
  else:
    f_mask_data = MaskData(self.observations, self.xray_structure.space_group(),
      self.observations.fo_sq.anomalous_flag(), self.f_mask.data())

  fc_correction = self.reparametrisation.fc_correction
  if fc_correction is None:
    fc_correction = xray.dummy_fc_correction()

  def args(scale_factor, weighting_scheme):
    args = (self,
            self.observations,
            f_mask_data,
            weighting_scheme,
            scale_factor,
            self.one_h_linearisation,
            self.reparametrisation.jacobian_transpose_matching_grad_fc(),
            fc_correction)
    return args

  self.reparametrisation.linearise()
  self.reparametrisation.store()
  scale_factor = float(olx.xf.rm.OSF())
  scale_factor *= scale_factor
  result = ext.build_design_matrix(*args(scale_factor,
                                         self.weighting_scheme))
  ds_mat = result.design_matrix()
  ds_mat = ds_mat.as_numpy_array()
  for r in range(0, ds_mat.shape[0]):
    ds_mat[r,:] *= math.sqrt(result.weights()[r])
  #self.weights = scla.block_diag([math.sqrt(x) for x in result.weights()])
  Z_mat = ds_mat #self.weights*ds_mat
  Zi_mat = scla.inv(Z_mat.T.dot(Z_mat))
  #https://stackoverflow.com/questions/14758283/is-there-a-numpy-scipy-dot-product-calculating-only-the-diagonal-entries-of-the
  Pp_mat_d = (Z_mat.dot(Zi_mat) * Z_mat).sum(-1)
  t_mat = Z_mat.dot(Zi_mat)
  t_mat = t_mat**2
  for i in range(0, t_mat.shape[0]):
    t_mat[i,:] /= (1+Pp_mat_d[i])
  if threshold is not None:
    maxT = np.amax(t_mat)
  else:
    maxT = 0
  Ts = []
  labels = parameter_labels(self, n_params=ds_mat.shape[1])
  for j in range(0, t_mat.shape[1]):
    if threshold is not None:
      if np.amax(t_mat[:,j])/maxT < threshold:
        continue
    if params:
      skip = True
      for pn in params:
        if pn in labels[j]:
          skip = False
          break
      if skip:
        continue
    Ts_ = [(xn, x) for xn, x in enumerate(t_mat[:,j])]
    Ts_.sort(key=lambda x: x[1],reverse=True)
    if Ts_[0][1] > maxT:
      maxT = Ts_[0][1]
    Ts.append((j, Ts_[:min(max_reflections, len(Ts_))]))
  fm_header = "#%3s%4s%4s%10s%10s%10s%10s\n"

  try:
    if olx.HasGUI() == 'true':
      olx.Freeze(True)
    if not output_to:
      output_to = sys.stdout
      fm_hkl = "%4i%4i%4i%10.4f%10.4f%10.4f%10.4f\n"
    else:
      fm_hkl = "%i %i %i %.4f %.4f %.4f %.4f\n"
    output_to.write(fm_header %("H", "K", "L", "d-spacing", "V", "Fo_sq", "Fc_sq"))
    for j, Ts_ in Ts:
      output_to.write("#%s\n" %(labels[j]))
      for i in range(0, len(Ts_)):
        idx = self.observations.indices[Ts_[i][0]]
        val = Ts_[i][1]*100/maxT
        output_to.write(fm_hkl %(idx[0], idx[1], idx[2],\
          self.xray_structure.unit_cell().d(idx),\
          val, self.observations.data[Ts_[i][0]]/scale_factor, result.observables()[Ts_[i][0]]))
  finally:
    if olx.HasGUI() == 'true':
      olx.Freeze(False)
  if False:
    self.f_calc = self.observations.fo_sq.array(
      data=result.f_calc(), sigmas=None)
    self.fc_sq = self.observations.fo_sq.array(
      data=result.observables(), sigmas=None)\
        .set_observation_type_xray_intensity()
    self.objective_data_only = self.objective()
    if self.restraints_manager is not None:
      if self.restraints_normalisation_factor is None:
        self.restraints_normalisation_factor \
            = 2 * self.objective_data_only/(ds_mat.shape[0]-ds_mat.shape[1])
      linearised_eqns = self.restraints_manager.build_linearised_eqns(
        self.xray_structure, self.reparametrisation.parameter_map())
      jacobian = \
        self.reparametrisation.jacobian_transpose_matching(
          self.reparametrisation.mapping_to_grad_fc_all).transpose()
      self.reduced_problem().add_equations(
        linearised_eqns.deltas,
        linearised_eqns.design_matrix * jacobian,
        linearised_eqns.weights * self.restraints_normalisation_factor)
      self.n_restraints = linearised_eqns.n_restraints()
      self.chi_sq_data_and_restraints = self.chi_sq()
    if False: #not objective_only:
      self.origin_fixing_restraint.add_to(
        self.step_equations(),
        self.reparametrisation.jacobian_transpose_matching_grad_fc(),
        self.reparametrisation.asu_scatterer_parameters)

leverage_obj = Leverage()
olex.registerMacro(leverage_obj.calculate, "max_reflections", False, "leverage")
olex.registerMacro(leverage_obj.calculate_for, "max_reflections", False, "leverage")
olex.registerFunction(leverage_obj.for_flack, False, "leverage")
