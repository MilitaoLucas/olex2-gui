import boost.python
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

import olex
import olex_core
import olx

class leverage_normal_eqns(least_squares.crystallographic_ls_class()):
  log = None
  def __init__(self, observations, reparametrisation, olx_atoms, table_file_name=None, **kwds):
    super(leverage_normal_eqns, self).__init__(
      observations, reparametrisation, initial_scale_factor=math.pow(float(olx.xf.rm.OSF()), 2), **kwds)
    if table_file_name:
      self.one_h_linearisation = direct.f_calc_modulus_squared(
        self.xray_structure, table_file_name=table_file_name)
    else:
      self.one_h_linearisation = direct.f_calc_modulus_squared(
        self.xray_structure, reflections=self.observations)


class Leverage(object):
  def __init__(self):
    pass

  def for_flack(self, max_reflections=5, output_to=None):
    from refinement import FullMatrixRefine
    from cctbx import sgtbx
    from cctbx.xray import observations
    from scitbx.lstbx import normal_eqns_solving

    fmr = FullMatrixRefine()
    obs = None
    refine = True
    # BASF 1 in already?
    if fmr.twin_components is not None and len(fmr.twin_components):
      if fmr.twin_components[0].twin_law == sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1)):
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
        fc.as_intensity_array().data())
      obs.fo_sq = fo2

    if refine:
      it = xray.twin_component(sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1)), 0.2, True)
      fmr.observations = observations.customized_copy(obs, [], (it,))
      fmr.twin_components = (it,)
      fmr.twin_fractions = ()

    normal_eqns = fmr.run(build_only=True, normal_equations_class=leverage_normal_eqns)

# need to refine if invertion twin has been added
    if refine:
      from libtbx import utils
      def args(scale_factor, weighting_scheme):
        args = (normal_eqns,
                normal_eqns.observations,
                fmr.f_mask,
                weighting_scheme,
                scale_factor,
                normal_eqns.one_h_linearisation,
                normal_eqns.reparametrisation.jacobian_transpose_matching_grad_fc(),
                fmr.exti)
        return args

      scale_factor = float(olx.xf.rm.OSF())
      scale_factor *= scale_factor
      print("Refining the structure...")
      cycles = normal_eqns_solving.naive_iterations(
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
    calculate(dmb, None, params.split(' '), max_reflections=max_reflections, output_to=output_to)

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
  if self.reparametrisation.extinction is not None and self.reparametrisation.extinction.grad:
    annotations_1.append("EXTI")
  Jt = self.reparametrisation.jacobian_transpose_matching_grad_fc()
  for j in xrange(0, n_params):
    label = []
    for k in xrange(0, Jt.n_cols):
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

  if self.f_mask is not None:
    f_mask = self.f_mask.data()
  else:
    f_mask = flex.complex_double()

  extinction_correction = self.reparametrisation.extinction
  if extinction_correction is None:
    extinction_correction = xray.dummy_extinction_correction()

  def args(scale_factor, weighting_scheme):
    args = (self,
            self.observations,
            f_mask,
            weighting_scheme,
            scale_factor,
            self.one_h_linearisation,
            self.reparametrisation.jacobian_transpose_matching_grad_fc(),
            extinction_correction)
    return args

  self.reparametrisation.linearise()
  self.reparametrisation.store()
  scale_factor = float(olx.xf.rm.OSF())
  scale_factor *= scale_factor
  result = ext.build_design_matrix(*args(scale_factor,
                                            self.weighting_scheme))
  ds_mat = result.design_matrix()
  ds_mat = ds_mat.as_numpy_array()
  for r in xrange(0, ds_mat.shape[0]):
    ds_mat[r,:] *= math.sqrt(result.weights()[r])
  #self.weights = scla.block_diag([math.sqrt(x) for x in result.weights()])
  Z_mat = ds_mat #self.weights*ds_mat
  Zi_mat = scla.inv(Z_mat.T.dot(Z_mat))
  #https://stackoverflow.com/questions/14758283/is-there-a-numpy-scipy-dot-product-calculating-only-the-diagonal-entries-of-the
  Pp_mat_d = (Z_mat.dot(Zi_mat) * Z_mat).sum(-1)
  t_mat = Z_mat.dot(Zi_mat)
  t_mat = t_mat**2
  for i in xrange(0, t_mat.shape[0]):
    t_mat[i,:] /= (1+Pp_mat_d[i])
  if threshold is not None:
    maxT = np.amax(t_mat)
  else:
    maxT = 0
  Ts = []
  labels = parameter_labels(self, n_params=ds_mat.shape[1])
  for j in xrange(0, t_mat.shape[1]):
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
  fm_header = "#%3s%4s%4s%8s%10s%10s\n"

  try:  
    if olx.HasGUI() == 'true':
      olx.Freeze(True)
    if not output_to:
      output_to = sys.stdout
      fm_hkl = "%4i%4i%4i%8.2f%10.3f%10.3f\n"
    else:
      fm_hkl = "%i %i %i %.2f %.3f %.3f\n"
    output_to.write(fm_header %("H", "K", "L", "V", "Fo_sq", "Fc_sq"))
    for j, Ts_ in Ts:
      output_to.write("#%s\n" %(labels[j]))
      for i in xrange(0, len(Ts_)):
        idx = self.observations.indices[Ts_[i][0]]
        val = Ts_[i][1]*100/maxT
        output_to.write(fm_hkl %(idx[0], idx[1], idx[2],\
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
