from iotbx.scalepack.merge import scale_intensities_if_necessary
from smtbx.refinement import least_squares
from cctbx_olex_adapter import OlexCctbxAdapter, rt_mx_from_olx
from cctbx import miller
from cctbx.array_family import flex
import math
from olexFunctions import OV


class TestUtils():
  def __init__(self):
    pass
  def calc_R_as_function_of_BASF(self, start=0, end = 1.0, update_scale=False):
    start, end = float(start), float(end)
    update_scale = bool(update_scale)
    coa = OlexCctbxAdapter()
    weight = coa.olx_atoms.model['weight']
    params = dict(a=0.1, b=0,
                  #c=0, d=0, e=0, f=1./3,
                  )
    for param, value in zip(list(params.keys())[:min(2,len(weight))], weight):
      params[param] = value
    weighting = least_squares.mainstream_shelx_weighting(**params)
    fo2 = coa.reflections.f_sq_obs_filtered

    if coa.twin_components and len(coa.twin_components) == 1:
      twc = coa.twin_components[0]
    elif coa.twin_fractions and len(coa.twin_fractions) == 1:
      twc = coa.twin_fractions[0]
    else:
      print("One BASF parameter is expected, aborting")
      return
    indices = set()
    for i, m in enumerate(coa.observations.indices):
      indices.add(m)
      itr = coa.observations.iterator(i)
      while itr.has_next():
        indices.add(itr.next().h)

    miller_set = miller.set(
      crystal_symmetry=coa.xray_structure().crystal_symmetry(),
        indices=flex.miller_index(list(indices))).auto_anomalous().map_to_asu()
    fc = coa.f_calc(miller_set,
      coa.exti is not None,
      False,
      ignore_inversion_twin=False,
      twin_data=False)

    print("BASF->wR2")
    for v in range(0, 100):
      twc.value = start + (end-start)*v/100
      o_tw = coa.observations.twin(
        fo2.crystal_symmetry().space_group(),
        fo2.anomalous_flag(),
        fc.indices(),
        fc.as_intensity_array().data())

      if update_scale:
        den = flex.sum(o_tw.data*o_tw.data)
        scale_factor = flex.sum(fo2.data()*o_tw.data)/den
      else:
        scale_factor = OV.GetOSF()

      wght = []
      for i, fo_sq in enumerate(fo2.data()):
        wght.append(weighting(fo_sq, fo2.sigmas()[i], o_tw.data[i], scale_factor))
      wght = flex.double(wght)
      w_diff_sq = wght*flex.pow2((fo2.data()-o_tw.data*scale_factor))
      w_diff_sq_sum = flex.sum(w_diff_sq)
      wR2 = w_diff_sq_sum/flex.sum(wght*flex.pow2(fo2.data()))
      wR2 = math.sqrt(wR2)
      print("%.4f\t%.8e" %(twc.value, wR2))

utils = TestUtils()
OV.registerFunction(utils.calc_R_as_function_of_BASF, False, "test")
