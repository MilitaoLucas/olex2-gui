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
import math

import olex
import olex_core
import olx
class Leverage(object):
  def __init__(self):
    pass

  def calculate(self, threshold=0.01):
    from refinement import FullMatrixRefine
    dmb = FullMatrixRefine().run(build_only=True)
    calculate(dmb, float(threshold), None)

  def calculate_for(self, params=""):
    from refinement import FullMatrixRefine
    dmb = FullMatrixRefine().run(build_only=True)
    calculate(dmb, None, params.split(' '))

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
        annotations_1.append("BASF %s" %basf_n)
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

def calculate(self, threshold, params):
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
  scale_factor = self.initial_scale_factor
  if scale_factor is None: # we haven't got one from previous refinement
    result = ext.build_normal_equations(
      *args(scale_factor=None, weighting_scheme=sigma_weighting()))
    scale_factor = self.scale_factor()

  self.reset()
  result = ext.build_design_matrix(*args(scale_factor,
                                            self.weighting_scheme))
  ds_mat = result.design_matrix()
  ds_mat = ds_mat.as_numpy_array()
  for r in xrange(0, ds_mat.shape[0]):
    ds_mat[r,:] *= math.sqrt(result.weights()[r])
  #self.weights = scla.block_diag([math.sqrt(x) for x in result.weights()])
  Z_mat = ds_mat #self.weights*ds_mat
  Zi_mat = scla.inv(Z_mat.T.dot(Z_mat))
  Pp_mat = Z_mat.dot(Zi_mat).dot(Z_mat.T)
  t_mat = Z_mat.dot(Zi_mat)
  t_mat = t_mat**2
  for i in xrange(0, t_mat.shape[0]):
    t_mat[i,:] /= (1+Pp_mat[i][i])
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
    Ts.append((j, Ts_[:5]))

  olx.Freeze(True)
  for j, Ts_ in Ts:
    print("For " + labels[j])
    for i in xrange(0,5):
      val = Ts_[i][1]*100/maxT
      print(str(self.observations.indices[Ts_[i][0]]) + \
             ": %s. Obs: %s, Calc: %s" %(val, self.observations.data[Ts_[i][0]],
                                          result.observables()[Ts_[i][0]]*scale_factor))
  olx.Freeze(False)

  self.f_calc = self.observations.fo_sq.array(
    data=result.f_calc(), sigmas=None)
  self.fc_sq = self.observations.fo_sq.array(
    data=result.observables(), sigmas=None)\
      .set_observation_type_xray_intensity()
  self.objective_data_only = self.objective()
  if False and self.restraints_manager is not None:
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
olex.registerFunction(leverage_obj.calculate, False, "leverage")
olex.registerFunction(leverage_obj.calculate_for, False, "leverage")