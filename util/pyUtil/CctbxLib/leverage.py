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
import sys

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
             ": %.2f. Obs: %.3f, Calc: %.3f" %(val, self.observations.data[Ts_[i][0]]/scale_factor,
                                          result.observables()[Ts_[i][0]]))
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

class flack_leverage(object):
  def __init__(self, connectivity_table=None):
    import numpy as np
    import scipy.linalg as scla
    from cctbx_olex_adapter import OlexCctbxAdapter, OlexCctbxMasks
    from cctbx.xray import observations
    from cctbx import sgtbx
    from smtbx.refinement import constraints
    from smtbx.refinement import least_squares
    from scitbx.lstbx import normal_eqns_solving

    adaptor = OlexCctbxAdapter()
    if adaptor.exti is None:
      adaptor.exti = xray.dummy_extinction_correction()
    else:
      adaptor,exti.grad = False

    #!! read the FAB !!
    f_mask = flex.complex_double()

    obs_ = adaptor.observations
    assert obs_.fo_sq.anomalous_flag()
    xray_structure = adaptor.xray_structure()
    flags = xray_structure.scatterer_flags()
    for sc in xray_structure.scatterers():
      f = xray.scatterer_flags()
      f.set_use_u_aniso(sc.flags.use_u_aniso())
      f.set_use_u_iso(sc.flags.use_u_iso())
      f.set_use_fp_fdp(True)
      sc.flags = f

    twin_fractions = obs_.twin_fractions
    twin_components = obs_.merohedral_components
    for tw in twin_fractions: tw.grad = False
    for tc in twin_components: tc.grad = False

    it = xray.twin_component(sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1)), 0.2, True)
    twin_components += (it,)
    obs = observations.customized_copy(obs_, twin_fractions, twin_components)
    # reparameterisation needs all fractions
    twin_fractions += twin_components
    connectivity_table = adaptor.connectivity_table
    reparametrisation = constraints.reparametrisation(
      xray_structure, [], connectivity_table,
      twin_fractions=twin_fractions,
      extinction=adaptor.exti
    )
    normal_eqns = least_squares.crystallographic_ls(obs,
      reparametrisation)

    def args(scale_factor, weighting_scheme):
      args = (normal_eqns,
              normal_eqns.observations,
              f_mask,
              weighting_scheme,
              scale_factor,
              normal_eqns.one_h_linearisation,
              normal_eqns.reparametrisation.jacobian_transpose_matching_grad_fc(),
              adaptor.exti)
      return args

    scale_factor = float(olx.xf.rm.OSF())
    scale_factor *= scale_factor
###################
    cycles = normal_eqns_solving.naive_iterations(
      normal_eqns, n_max_iterations=10,
      gradient_threshold=1e-7,
      step_threshold=1e-4)

    normal_eqns.reset()

    result = ext.build_design_matrix(
      *args(scale_factor=scale_factor, weighting_scheme=sigma_weighting()))
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
    Ts = []
    maxT = 0
    for j in xrange(0, t_mat.shape[1]):
      Ts_ = [(xn, x) for xn, x in enumerate(t_mat[:,j])]
      Ts_.sort(key=lambda x: x[1],reverse=True)
      if Ts_[0][1] > maxT:
        maxT = Ts_[0][1] 
      Ts.append((j, Ts_[:100]))

    for j, Ts_ in Ts:
      print("For Flack")
      for i in xrange(0,100):
        val = Ts_[i][1]*100/maxT
        print(str(normal_eqns.observations.indices[Ts_[i][0]]) + \
               ": %.2f. Obs: %.3f, Calc: %.3f" %(val, normal_eqns.observations.data[Ts_[i][0]]/scale_factor,
                                            result.observables()[Ts_[i][0]]))
#############################
    self.flack_x = it.value
    self.sigma_x = math.sqrt(normal_eqns.covariance_matrix(
      jacobian_transpose=reparametrisation.jacobian_transpose_matching(
        reparametrisation.mapping_to_grad_fc_independent_scalars))[0])
    self.show()


  def show(self, out=None):
    from libtbx.utils\
      import format_float_with_standard_uncertainty as format_float_with_su
    if out is None: out = sys.stdout
    print >> out, "Flack x: %s" %format_float_with_su(self.flack_x, self.sigma_x)


leverage_obj = Leverage()
olex.registerFunction(leverage_obj.calculate, False, "leverage")
olex.registerFunction(leverage_obj.calculate_for, False, "leverage")
olex.registerFunction(flack_leverage, False, "leverage")