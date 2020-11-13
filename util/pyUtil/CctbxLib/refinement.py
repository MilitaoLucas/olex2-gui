from __future__ import division

import math, os, sys
from cctbx_olex_adapter import OlexCctbxAdapter, OlexCctbxMasks, rt_mx_from_olx
import cctbx_olex_adapter as COA
import boost.python
ext = boost.python.import_ext("smtbx_refinement_least_squares_ext")

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import olx
import olex
import olex_core

from cctbx.array_family import flex
from cctbx import maptbx, miller, sgtbx, uctbx, xray, crystal

import iotbx.cif.model

from libtbx import easy_pickle, utils

from scitbx.lstbx import normal_eqns_solving

from smtbx.refinement import least_squares
from smtbx.refinement import restraints
from smtbx.refinement import constraints
from smtbx.refinement.constraints import geometrical
from smtbx.refinement.constraints import adp, fpfdp
from smtbx.refinement.constraints import site
from smtbx.refinement.constraints import occupancy
from smtbx.refinement.constraints import rigid
import smtbx.utils

import numpy
import scipy.linalg

import olex2_normal_equations
from my_refine_util import hydrogen_atom_constraints_customisation

# try to initialise openblas
try:
  import fast_linalg
  from fast_linalg import env
  if not env.initialised:
    if sys.platform[:3] == "win":
      ob_path = olx.BaseDir()
      files = [x for x in os.listdir(ob_path) if 'openblas' in x and '.dll' in x]
    else:
      ob_path = os.path.join(olx.BaseDir(), 'lib')
      files = [x for x in os.listdir(ob_path) if 'openblas' in x and ('.so' in x or '.dylib' in x)]
    if files:
      env.initialise(os.path.join(ob_path, files[0]).encode("utf-8"))
      if env.initialised:
        print("Successfully initialised SciPy OpenBlas:")
        print(env.build_config)
except Exception as e:
  print("Could not initialise OpenBlas: %s" %e)

class FullMatrixRefine(OlexCctbxAdapter):
  solvers = {
    'Gauss-Newton': normal_eqns_solving.naive_iterations_with_damping_and_shift_limit,
    #'Levenberg-Marquardt': normal_eqns_solving.levenberg_marquardt_iterations,
    'Levenberg-Marquardt': olex2_normal_equations.levenberg_marquardt_iterations,
    'NSFF': normal_eqns_solving.levenberg_marquardt_iterations
  }
  solvers_default_method = 'Levenberg-Marquardt'

  def __init__(self, max_cycles=None, max_peaks=5, verbose=False, on_completion=None, weighting=None):
    OlexCctbxAdapter.__init__(self)
    self.interrupted = False
    self.max_cycles = max_cycles
    self.max_peaks = max_peaks
    self.verbose = verbose
    sys.stdout.refresh = False
    self.scale_factor = None
    self.failure = False
    self.log = open(OV.file_ChangeExt(OV.FileFull(), 'log'), 'w')
    self.flack = None
    self.on_completion = on_completion
    # set the secondary CH2 treatment
    self.refine_secondary_xh2_angle = False
    self.idealise_secondary_xh2_angle = False
    self.use_tsc = False
    sec_ch2_treatment = OV.GetParam('snum.smtbx.secondary_ch2_angle')
    if sec_ch2_treatment == 'idealise':
      self.idealise_secondary_xh2_angle = True
    elif sec_ch2_treatment == 'refine':
      self.refine_secondary_xh2_angle = True
    self.weighting = weighting
    if self.weighting is None:
      weight = self.olx_atoms.model['weight']
      params = dict(a=0.1, b=0,
                    #c=0, d=0, e=0, f=1./3,
                    )
      for param, value in zip(params.keys()[:min(2,len(weight))], weight):
        params[param] = value
      self.weighting = least_squares.mainstream_shelx_weighting(**params)


  def run(self, build_only=False,
          table_file_name = None,
          normal_equations_class=olex2_normal_equations.normal_eqns):
    """ If build_only is True - this method initialises and returns the normal
     equations object
    """
    try:
      from fast_linalg import env
      max_threads = int(OV.GetVar("refine.max_threads", 0))
      if max_threads == 0:
        max_threads = env.physical_cores
      if max_threads is not None:
        ext.build_normal_equations.available_threads = max_threads
        env.threads = max_threads
    except:
      pass
    print("Using %s threads" %ext.build_normal_equations.available_threads)
    OV.SetVar('stop_current_process', False) #reset any interrupt before starting.
    self.use_tsc = table_file_name is not None
    self.reflections.show_summary(log=self.log)
    self.f_mask = None
    if OV.GetParam("snum.refinement.use_solvent_mask"):
      modified_hkl_path = "%s/%s-mask.hkl" %(OV.FilePath(), OV.FileName())
      original_hklsrc = OV.GetParam('snum.masks.original_hklsrc')
      if OV.HKLSrc() == modified_hkl_path and original_hklsrc is not None:
        # change back to original hklsrc
        OV.HKLSrc(original_hklsrc)
        # we need to reinitialise reflections
        self.initialise_reflections()
      if not OV.GetParam("snum.refinement.recompute_mask_before_refinement"):
        self.f_mask = self.load_mask()
      if not self.f_mask:
        OlexCctbxMasks()
        if olx.current_mask.flood_fill.n_voids() > 0:
          self.f_mask = olx.current_mask.f_mask()
      if self.f_mask:
        fo_sq = self.reflections.f_sq_obs_filtered
        if not fo_sq.space_group().is_centric():
          self.f_mask = self.f_mask.generate_bijvoet_mates()
        self.f_mask = self.f_mask.common_set(fo_sq)
        if self.f_mask.size() != fo_sq.size():
          print("The mask is out of date. Please update.")
          self.failure = True
          return
    restraints_manager = self.restraints_manager()
    #put shared parameter constraints first - to allow proper bookkeeping of
    #overrided parameters (U, sites)
    self.fixed_distances = {}
    self.fixed_angles = {}
    self.constraints = self.setup_shared_parameters_constraints() + self.constraints
    self.constraints += self.setup_rigid_body_constraints(
      self.olx_atoms.afix_iterator())
    self.constraints += self.setup_geometrical_constraints(
      self.olx_atoms.afix_iterator())
    self.n_constraints = len(self.constraints)

    temp = self.olx_atoms.exptl['temperature']
    if temp < -274: temp = 20
    #set up extinction correction if defined
    exti = OV.GetExtinction()
    if exti is not None:
      self.extinction = xray.shelx_extinction_correction(
        self.xray_structure().unit_cell(), self.wavelength, exti)
      self.extinction.grad = True
      self.extinction.expression = r'Fc^*^=kFc[1+0.001xFc^2^\l^3^/sin(2\q)]^-1/4^'
    else:
      self.extinction = xray.dummy_extinction_correction()
      self.extinction.expression = ''
    self.reparametrisation = constraints.reparametrisation(
      structure=self.xray_structure(),
      constraints=self.constraints,
      connectivity_table=self.connectivity_table,
      twin_fractions=self.get_twin_fractions(),
      temperature=temp,
      extinction = self.extinction,
      directions=self.directions
    )
    self.reparametrisation.fixed_distances.update(self.fixed_distances)
    self.reparametrisation.fixed_angles.update(self.fixed_angles)

    #===========================================================================
    # for l,p in self.reparametrisation.fixed_distances.iteritems():
    #  label = ""
    #  for a in l:
    #    label += "-%s" %self.olx_atoms._atoms[a]['label']
    #  print label
    # for l,p in self.reparametrisation.fixed_angles.iteritems():
    #  label = ""
    #  for a in l:
    #    label += "-%s" %self.olx_atoms._atoms[a]['label']
    #  print label
    #===========================================================================

    #self.reflections.f_sq_obs_filtered = self.reflections.f_sq_obs_filtered.sort(
    #  by_value="resolution")
    self.normal_eqns = normal_equations_class(
      self.observations,
      self.reparametrisation,
      self.olx_atoms,
      table_file_name=table_file_name,
      f_mask=self.f_mask,
      restraints_manager=restraints_manager,
      weighting_scheme=self.weighting,
      log=self.log,
      may_parallelise=True
    )
    self.normal_eqns.shared_param_constraints = self.shared_param_constraints
    self.normal_eqns.shared_rotated_adps = self.shared_rotated_adps
    if build_only:
      return self.normal_eqns
    method = OV.GetParam('snum.refinement.method')
    iterations = FullMatrixRefine.solvers.get(method)
    if iterations == None:
      method = solvers_default_method
      iterations = FullMatrixRefine.solvers.get(method)
      print("WARNING: unsupported method: '%s' is replaced by '%s'"\
        %(method, solvers_default_method))
    assert iterations is not None
    fcf_only = OV.GetParam('snum.NoSpherA2.make_fcf_only')
    try:
      damping = OV.GetDampingParams()
      self.data_to_parameter_watch()
      if not fcf_only:
        self.print_table_header()
        self.print_table_header(self.log)

      class refinementWrapper(iterations):
        def __init__(self, parent, *args, **kwds):
          parent.cycles = self
          super(iterations, self).__init__(*args, **kwds)

      try:
        if(method=='Levenberg-Marquardt'):
#          normal_eqns_solving.levenberg_marquardt_iterations.tau=1e-4
          refinementWrapper(self, self.normal_eqns,
              n_max_iterations=self.max_cycles,
              track_all=True,
              gradient_threshold=None,
              step_threshold=None,
              tau = 1e-6,
              convergence_as_shift_over_esd=1e-3,
              )
        else:
          refinementWrapper(self, self.normal_eqns,
              n_max_iterations=self.max_cycles,
              track_all=True,
              damping_value=damping[0],
              max_shift_over_esd=damping[1],
              convergence_as_shift_over_esd=1e-3,
              gradient_threshold=None,
              step_threshold=None)

      except RuntimeError as e:
        if str(e) == 'external_interrupt':
          print("Refinement interrupted")
          self.interrupted = True
        else:
          raise e

      self.scale_factor = self.cycles.scale_factor_history[-1]
      self.covariance_matrix_and_annotations=self.normal_eqns.covariance_matrix_and_annotations()
      self.twin_covariance_matrix = self.normal_eqns.covariance_matrix(
        jacobian_transpose=self.reparametrisation.jacobian_transpose_matching(
          self.reparametrisation.mapping_to_grad_fc_independent_scalars))
      fcf_stuff = '-' in olx.Ins('MORE')
      if fcf_stuff:
        self.export_var_covar(self.covariance_matrix_and_annotations)
      self.r1 = self.normal_eqns.r1_factor(cutoff_factor=2)
      self.r1_all_data = self.normal_eqns.r1_factor()
      try:
        self.check_flack()
        if self.flack:
          OV.SetParam('snum.refinement.flack_str', self.flack)
        else:
          OV.SetParam('snum.refinement.flack_str', "")
      except:
        OV.SetParam('snum.refinement.flack_str', "")
        print("Failed to evaluate Flack parameter")
      #extract SU on BASF and extinction
      diag = self.twin_covariance_matrix.matrix_packed_u_diagonal()
      dlen = len(diag)
      if self.reparametrisation.extinction.grad:
        #extinction is the last parameter after the twin fractions
        su = math.sqrt(diag[dlen-1])
        OV.SetExtinction(self.reparametrisation.extinction.value, su)
        dlen -= 1
      try:
        for i in xrange(dlen):
          olx.xf.rm.BASF(i, olx.xf.rm.BASF(i), math.sqrt(diag[i]))
      except:
        pass
    except RuntimeError as e:
      if str(e).startswith("cctbx::adptbx::debye_waller_factor_exp: max_arg exceeded"):
        print("Refinement failed to converge")
      elif "SCITBX_ASSERT(!cholesky.failure) failure" in str(e):
        print("Cholesky failure")
        i = str(e).rfind(' ')
        index = int(str(e)[i:])
        if index > 0:
          param_name = ""
          n_components = len(self.reparametrisation.component_annotations)
          if index >= n_components:
            param_name = "Scalar Parameter"
          else:
            param_name = self.reparametrisation.component_annotations[index]
          print("the leading minor of order %i for %s is not positive definite"\
           %(index, param_name))
      else:
        print("Refinement failed")
        import traceback
        traceback.print_exc()
      self.failure = True
    else:
      fo_minus_fc = self.f_obs_minus_f_calc_map(0.4)
      fo_minus_fc.apply_volume_scaling()
      self.diff_stats = fo_minus_fc.statistics()
      self.post_peaks(fo_minus_fc, max_peaks=self.max_peaks)
      if not fcf_only:
        self.show_summary()
        self.show_comprehensive_summary(log=self.log)
      block_name = OV.FileName().replace(' ', '')
      cif = iotbx.cif.model.cif()
      cif[block_name] = self.as_cif_block()
      acta = olx.Ins("ACTA").strip()
      if acta != "n/a":
        with open(OV.file_ChangeExt(OV.FileFull(), 'cif'), 'w') as f:
          print >> f, cif
        inc_hkl = acta and "NOHKL" != acta.split()[-1].upper()
        if not OV.GetParam('snum.refinement.cifmerge_after_refinement', False):
          olx.CifMerge(f=inc_hkl, u=True)

      self.output_fcf()
      new_weighting = self.weighting.optimise_parameters(
        self.normal_eqns.observations.fo_sq,
        self.normal_eqns.fc_sq,
        self.normal_eqns.scale_factor(),
        self.reparametrisation.n_independents)
      OV.SetParam(
        'snum.refinement.suggested_weight', "%s %s" %(new_weighting.a, new_weighting.b))
      if self.on_completion:
        self.on_completion(cif[block_name])
      if olx.HasGUI() == 'true':
        olx.UpdateQPeakTable()
    finally:
      sys.stdout.refresh = True
      self.log.close()

  def data_to_parameter_watch(self):
    #parameters = self.normal_eqns.n_parameters
    parameters = self.reparametrisation.n_independents + 1
    data_all = self.reflections.f_sq_obs_filtered.size()
    data = self.reflections.f_sq_obs_merged.size()
    dpr = "%.2f" %(data/parameters)
    OV.SetParam('snum.refinement.data_parameter_ratio', dpr)
    OV.SetParam('snum.refinement.parameters', parameters)
    print("Data/Parameter ratio = %s" %dpr)

  def print_table_header(self, log=None):
    if log is None: log = sys.stdout
    #restraints = self.normal_eqns.n_restraints
    #if not restraints:
      #restraints = "n/a"
    #print >>log, "Parameters: %s, Data: %s, Constraints: %s, Restraints: %s"\
     #%(self.normal_eqns.n_parameters, self.normal_eqns.observations.data.all()[0], self.n_constraints, restraints)
    print >>log, "  -------  --------  --------  --------  --------------------  --------------------  --------------------"
    print >>log, "   Cycle      R1       wR_2      GooF          Shift/esd            Shift xyx               Shift U      "
    print >>log, "  -------  --------  --------  --------  --------------------  --------------------  --------------------"

  def get_twin_fractions(self):
    rv = None
    if self.twin_fractions is not None:
      rv = self.twin_fractions
    if self.twin_components is not None:
      if rv is None:
        rv = self.twin_components
      else:
        rv += self.twin_components
    return rv

  def check_flack(self):
    if (not self.xray_structure().space_group().is_centric()
        and self.normal_eqns.observations.fo_sq.anomalous_flag()):
      if (self.twin_components is not None and len(self.twin_components)
          and self.twin_components[0].twin_law == sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1))):
        if self.twin_components[0].grad:
          flack = self.twin_components[0].value
          su = math.sqrt(self.twin_covariance_matrix.matrix_packed_u_diagonal()[0])
          self.flack = utils.format_float_with_standard_uncertainty(flack, su)
      else:
        if self.observations.merohedral_components or self.observations.twin_fractions:
          if self.use_tsc:
            obs_ = self.get_fo_sq_fc(one_h_function=\
              self.normal_eqns.one_h_linearisation)[0].as_xray_observations()
          else:
            obs_ = self.get_fo_sq_fc()[0].as_xray_observations()
        else:
          obs_ = self.observations
        from smtbx import absolute_structure
        flack = absolute_structure.flack_analysis(
          self.normal_eqns.xray_structure,
          obs_,
          self.extinction,
          connectivity_table=self.connectivity_table
        )
        self.flack = utils.format_float_with_standard_uncertainty(
          flack.flack_x, flack.sigma_x)

  def get_radiation_type(self):
    from cctbx.eltbx import wavelengths
    for x in wavelengths.characteristic_iterator():
      if abs(self.wavelength-x.as_angstrom()) < 1e-4:
        l = x.label()
        if len(l) == 2:
          return l + " K\\a"
        return "%s K\\%s~%s~" %(l[:2], l[2].lower(), l[3])
    return 'synchrotron'

  def wR2_factor(self, cutoff_factor=None):
    fo_sq = self.normal_eqns.observations.fo_sq
    if cutoff_factor is not None:
      strong = fo_sq.data() >= cutoff_factor*fo_sq.sigmas()
      fo_sq = fo_sq.select(strong)
      fc_sq = self.normal_eqns.fc_sq.select(strong)
      wght = self.normal_eqns.weights.select(strong)
    else:
      strong = None
      wght = self.normal_eqns.weights
      fc_sq = self.normal_eqns.fc_sq
    fc_sq = fc_sq.data()
    fo_sq = fo_sq.data()
    fc_sq *= self.normal_eqns.scale_factor()
    w_diff_sq = wght*flex.pow2((fo_sq-fc_sq))
    w_diff_sq_sum = flex.sum(w_diff_sq)
    wR2 = w_diff_sq_sum/flex.sum(wght*flex.pow2(fo_sq))
    wR2 = math.sqrt(wR2)
    # this way the disagreeable reflections calculated in Shelx
#    w_diff_sq_av = w_diff_sq_sum/len(w_diff_sq)
#    w_diff_sq /= w_diff_sq_av
#    w_diff = flex.sqrt(w_diff_sq)
#    disagreeable = w_diff >= 4
#    d_diff = w_diff.select(disagreeable)
#    if strong:
#      d_idx = self.normal_eqns.observations.indices.select(strong)
#    else:
#      d_idx = self.normal_eqns.observations.indices
#    d_idx = d_idx.select(disagreeable)
#    for i, d in enumerate(d_diff):
#      print d_idx[i], d
    return wR2

  def as_cif_block(self):
    def format_type_count(type, count):
      if round(count, 1) == round(count):
        return "%s%.0f" %(type, count)
      elif abs(round(count, 2) - round(count)) in (0.25, 0.33):
        return "%s%.2f" %(type, count)
      else:
        return "%s%.1f" %(type, count)
    unit_cell_content = self.xray_structure().unit_cell_content()
    formatted_type_count_pairs = []
    count = unit_cell_content.pop('C', None)
    if count is not None:
      formatted_type_count_pairs.append(format_type_count('C', count))
      count = unit_cell_content.pop('H', None)
      if count is not None:
        formatted_type_count_pairs.append(format_type_count('H', count))
    types = unit_cell_content.keys()
    types.sort()
    for type in types:
      formatted_type_count_pairs.append(
        format_type_count(type, unit_cell_content[type]))

    completeness_refs = refinement_refs = self.normal_eqns.observations.fo_sq
    if self.hklf_code == 5:
      completeness_refs = completeness_refs.select(self.normal_eqns.observations.measured_scale_indices == 1)
      completeness_refs = completeness_refs.merge_equivalents(algorithm="shelx").array().map_to_asu()
    two_theta_full = olx.Ins('acta')
    try:
      two_theta_full = float(two_theta_full)
    except ValueError:
      two_theta_full = math.asin(self.wavelength*0.6)*360/math.pi
    two_theta_full_set = uctbx.d_star_sq_as_two_theta(
      uctbx.d_as_d_star_sq(completeness_refs.d_max_min()[1]), self.wavelength, deg=True)
    if two_theta_full_set < two_theta_full:
      two_theta_full = two_theta_full_set
    ref_subset = completeness_refs.resolution_filter(
      d_min=uctbx.two_theta_as_d(two_theta_full, self.wavelength, deg=True))
    completeness_full = ref_subset.completeness(as_non_anomalous_array=True)
    completeness_theta_max = completeness_refs.completeness(as_non_anomalous_array=True)
    if completeness_refs.anomalous_flag():
      completeness_full_a = ref_subset.completeness()
      completeness_theta_max_a = completeness_refs.completeness()
    else:
    # not sure why we need to duplicate these in the CIF but for now some
    # things rely on to it!
      completeness_full_a, completeness_theta_max_a = completeness_full, completeness_theta_max
    #OV.SetParam("snum.refinement.max_shift_over_esd", None)
    #OV.SetParam("snum.refinement.max_shift_over_esd_atom", None)

    shifts = self.normal_eqns.get_shifts()
    try:
      max_shift_idx = 0
      for i, s in enumerate(shifts):
        if (shifts[max_shift_idx] < s):
          max_shift_idx = i
      #print("Largest shift/esd is %.4f for %s" %(
            #shifts[max_shift_idx],
            #self.covariance_matrix_and_annotations.annotations[max_shift_idx]))
      #OV.SetParam("snum.refinement.max_shift_over_esd",
        #shifts[max_shift_idx])
      #OV.SetParam("snum.refinement.max_shift_over_esd_atom",
        #self.covariance_matrix_and_annotations.annotations[max_shift_idx].split('.')[0])
    except:
      pass
    # cell parameters and errors
    cell_params = self.olx_atoms.getCell()
    cell_errors = self.olx_atoms.getCellErrors()
    acta_stuff = olx.Ins('ACTA') != "n/a"
    xs = self.xray_structure()
    if not acta_stuff:
      from iotbx.cif import model
      cif_block = model.block()
    else:
      from scitbx import matrix
      cell_vcv = flex.pow2(matrix.diag(cell_errors).as_flex_double_matrix())
      cif_block = xs.as_cif_block(
        format="coreCIF",
        covariance_matrix=self.covariance_matrix_and_annotations.matrix,
        cell_covariance_matrix=cell_vcv.matrix_symmetric_as_packed_u())


      for i in range(3):
        for j in range(i+1,3):
          if (cell_params[i] == cell_params[j] and
              cell_errors[i] == cell_errors[j] and
              cell_params[i+3] == 90 and
              cell_errors[i+3] == 0 and
              cell_params[j+3] == 90 and
              cell_errors[j+3] == 0):
            cell_vcv[i,j] = math.pow(cell_errors[i],2)
            cell_vcv[j,i] = math.pow(cell_errors[i],2)
      # geometry loops
      cell_vcv = cell_vcv.matrix_symmetric_as_packed_u()
      connectivity_full = self.reparametrisation.connectivity_table
      bond_h = '$H' in olx.Ins('bond').upper()
      distances = iotbx.cif.geometry.distances_as_cif_loop(
        connectivity_full.pair_asu_table,
        site_labels=xs.scatterers().extract_labels(),
        sites_frac=xs.sites_frac(),
        covariance_matrix=self.covariance_matrix_and_annotations.matrix,
        cell_covariance_matrix=cell_vcv,
        parameter_map=xs.parameter_map(),
        include_bonds_to_hydrogen=bond_h,
        fixed_distances=self.reparametrisation.fixed_distances)
      angles = iotbx.cif.geometry.angles_as_cif_loop(
        connectivity_full.pair_asu_table,
        site_labels=xs.scatterers().extract_labels(),
        sites_frac=xs.sites_frac(),
        covariance_matrix=self.covariance_matrix_and_annotations.matrix,
        cell_covariance_matrix=cell_vcv,
        parameter_map=xs.parameter_map(),
        include_bonds_to_hydrogen=bond_h,
        fixed_angles=self.reparametrisation.fixed_angles,
        conformer_indices=self.reparametrisation.connectivity_table.conformer_indices)
      cif_block.add_loop(distances.loop)
      cif_block.add_loop(angles.loop)
      equivs = self.olx_atoms.model['equivalents']
      confs = [i for i in self.olx_atoms.model['info_tables'] if i['type'] == 'CONF']
      if len(confs): #fix me!
        all_conf = None
        angles = []
        angle_defs = []
        for conf in confs:
          atoms = conf['atoms']
          if not atoms:
            all_conf = OV.dict_obj(conf)
            continue
          seqs = []
          rt_mxs = []
          for atom in atoms:
            if atom[1] > -1:
              rt_mxs.append(rt_mx_from_olx(equivs[atom[1]]))
            else:
              rt_mxs.append(sgtbx.rt_mx())
            seqs.append(atom[0])
          angle_defs.append(crystal.dihedral_angle_def(seqs, rt_mxs))
        if all_conf:
          max_d = 1.7
          max_angle = 170
          if len(all_conf.args) > 0:
            max_d = all_conf.args[0]
          if len(all_conf.args) > 1:
            max_angle = all_conf.args[1]
          angles += crystal.calculate_dihedrals(
            pair_asu_table=connectivity_full.pair_asu_table,
            sites_frac=xs.sites_frac(),
            covariance_matrix=self.covariance_matrix_and_annotations.matrix,
            cell_covariance_matrix=cell_vcv,
            parameter_map=xs.parameter_map(),
            conformer_indices=self.reparametrisation.connectivity_table.conformer_indices,
            max_d=max_d,
            max_angle=max_angle)
        if len(angle_defs):
          defined_angles = crystal.calculate_dihedrals(
            pair_asu_table=connectivity_full.pair_asu_table,
            sites_frac=xs.sites_frac(),
            dihedral_defs=angle_defs,
            covariance_matrix=self.covariance_matrix_and_annotations.matrix,
            cell_covariance_matrix=cell_vcv,
            parameter_map=xs.parameter_map())
          if all_conf:
            for a in defined_angles:
              if a not in angles:
                angles.append(a)
          else:
            angles = defined_angles
        space_group_info = sgtbx.space_group_info(group=xs.space_group())
        cif_dihedrals = iotbx.cif.geometry.dihedral_angles_as_cif_loop(
          angles,
          space_group_info=space_group_info,
          site_labels=xs.scatterers().extract_labels(),
          include_bonds_to_hydrogen=False)
        cif_block.add_loop(cif_dihedrals.loop)
      htabs = [i for i in self.olx_atoms.model['info_tables'] if i['type'] == 'HTAB']
      hbonds = []
      for htab in htabs:
        atoms = htab['atoms']
        rt_mx = None
        if atoms[1][1] > -1:
          rt_mx = rt_mx_from_olx(equivs[atoms[1][1]])
        hbonds.append(
          iotbx.cif.geometry.hbond(atoms[0][0], atoms[1][0], rt_mx=rt_mx))
      if len(hbonds):
        max_da_distance=float(OV.GetParam('snum.cif.htab_max_d', 2.9))
        min_dha_angle=float(OV.GetParam('snum.cif.htab_min_angle', 120))
        hbonds_loop = iotbx.cif.geometry.hbonds_as_cif_loop(
          hbonds,
          connectivity_full.pair_asu_table,
          site_labels=xs.scatterers().extract_labels(),
          sites_frac=xs.sites_frac(),
          min_dha_angle=min_dha_angle,
          max_da_distance=max_da_distance,
          covariance_matrix=self.covariance_matrix_and_annotations.matrix,
          cell_covariance_matrix=cell_vcv,
          parameter_map=xs.parameter_map(),
          fixed_distances=self.reparametrisation.fixed_distances,
          fixed_angles=self.reparametrisation.fixed_angles)
        cif_block.add_loop(hbonds_loop.loop)
      self.restraints_manager().add_to_cif_block(cif_block, xs)

    # cctbx could make e.g. 1.001(1) become 1.0010(10), so use Olex2 values for cell
    cif_block['_cell_length_a'] = olx.xf.uc.CellEx('a')
    cif_block['_cell_length_b'] = olx.xf.uc.CellEx('b')
    cif_block['_cell_length_c'] = olx.xf.uc.CellEx('c')
    cif_block['_cell_angle_alpha'] = olx.xf.uc.CellEx('alpha')
    cif_block['_cell_angle_beta'] = olx.xf.uc.CellEx('beta')
    cif_block['_cell_angle_gamma'] = olx.xf.uc.CellEx('gamma')
    cif_block['_cell_volume'] = olx.xf.uc.VolumeEx()
    if not self.f_mask:
      cif_block['_chemical_formula_sum'] = olx.xf.au.GetFormula()
      cif_block['_chemical_formula_moiety'] = olx.xf.latt.GetMoiety()
    else:
      _ = OV.GetParam('snum.masks.user_sum_formula')
      if _:
        olx.xf.SetFormula(_)
        cif_block['_chemical_formula_sum'] = _

      _ = OV.GetParam('snum.masks.user_sum_formula')
      if _:
        cif_block['_chemical_formula_moiety'] = _

    cif_block['_chemical_formula_weight'] = olx.xf.GetMass()
    cif_block['_exptl_absorpt_coefficient_mu'] = olx.xf.GetMu()
    cif_block['_exptl_crystal_density_diffrn'] = olx.xf.GetDensity()
    cif_block['_exptl_crystal_F_000'] = olx.xf.GetF000()

    write_fcf = False
    acta = olx.Ins("ACTA").strip()
    if OV.GetParam('user.cif.finalise') != 'Exclude':
      if not acta:
        write_fcf = True
      elif acta.upper() != "n/a" and "NOHKL" not in acta.upper():
        write_fcf = True
    if write_fcf:
      fcf_cif, fmt_str = self.create_fcf_content(list_code=4, add_weights=True, fixed_format=False)

      import StringIO
      f = StringIO.StringIO()
      fcf_cif.show(out=f,loop_format_strings={'_refln':fmt_str})
      cif_block['_iucr_refine_fcf_details'] = f.getvalue()

    fo2 = self.reflections.f_sq_obs
    merging = self.reflections.merging
    min_d_star_sq, max_d_star_sq = refinement_refs.min_max_d_star_sq()
    (h_min, k_min, l_min), (h_max, k_max, l_max) = fo2.min_max_indices()
    fmt = "%.4f"
    # following two should go as we print the same info for up to 3 times!!
    cif_block['_diffrn_measured_fraction_theta_full'] = fmt % completeness_full
    cif_block['_diffrn_measured_fraction_theta_max'] = fmt % completeness_theta_max
    cif_block['_diffrn_reflns_Laue_measured_fraction_full'] = fmt % completeness_full
    cif_block['_diffrn_reflns_Laue_measured_fraction_max'] = fmt % completeness_theta_max
    if completeness_full_a is not None:
      cif_block['_diffrn_reflns_point_group_measured_fraction_full'] = fmt % completeness_full_a
      cif_block['_diffrn_reflns_point_group_measured_fraction_max'] = fmt % completeness_theta_max_a

    cif_block['_diffrn_radiation_wavelength'] = self.wavelength
    cif_block['_diffrn_radiation_type'] = self.get_radiation_type()
    if self.hklf_code == 5:
      cif_block['_diffrn_reflns_number'] = refinement_refs.size()
    else:
      cif_block['_diffrn_reflns_number'] = fo2.eliminate_sys_absent().size()
    if merging is not None:
      cif_block['_diffrn_reflns_av_R_equivalents'] = "%.4f" %merging.r_int()
      cif_block['_diffrn_reflns_av_unetI/netI'] = "%.4f" %merging.r_sigma()
    cif_block['_diffrn_reflns_limit_h_min'] = h_min
    cif_block['_diffrn_reflns_limit_h_max'] = h_max
    cif_block['_diffrn_reflns_limit_k_min'] = k_min
    cif_block['_diffrn_reflns_limit_k_max'] = k_max
    cif_block['_diffrn_reflns_limit_l_min'] = l_min
    cif_block['_diffrn_reflns_limit_l_max'] = l_max
    cif_block['_diffrn_reflns_theta_min'] = "%.2f" %(
      0.5 * uctbx.d_star_sq_as_two_theta(min_d_star_sq, self.wavelength, deg=True))
    cif_block['_diffrn_reflns_theta_max'] = "%.2f" %(
      0.5 * uctbx.d_star_sq_as_two_theta(max_d_star_sq, self.wavelength, deg=True))
    cif_block['_diffrn_reflns_theta_full'] = fmt % (two_theta_full/2)
    #
    cif_block['_refine_diff_density_max'] = fmt % self.diff_stats.max()
    cif_block['_refine_diff_density_min'] = fmt % self.diff_stats.min()
    cif_block['_refine_diff_density_rms'] = fmt % math.sqrt(self.diff_stats.mean_sq())
    d_max, d_min = self.reflections.f_sq_obs_filtered.d_max_min()
    if self.flack is not None:
        cif_block['_refine_ls_abs_structure_details'] = \
                 'Flack, H. D. (1983). Acta Cryst. A39, 876-881.'
        cif_block['_refine_ls_abs_structure_Flack'] = self.flack
    cif_block['_refine_ls_d_res_high'] = fmt % d_min
    cif_block['_refine_ls_d_res_low'] = fmt % d_max
    if self.extinction.expression:
      cif_block['_refine_ls_extinction_expression'] = self.extinction.expression
      cif_block['_refine_ls_extinction_coef'] = olx.xf.rm.Exti()
    cif_block['_refine_ls_goodness_of_fit_ref'] = fmt % self.normal_eqns.goof()
    #cif_block['_refine_ls_hydrogen_treatment'] =
    cif_block['_refine_ls_matrix_type'] = 'full'
    cif_block['_refine_ls_number_constraints'] = self.n_constraints
    # add the OSF!
    cif_block['_refine_ls_number_parameters'] = self.reparametrisation.n_independents + 1
    cif_block['_refine_ls_number_reflns'] = self.reflections.f_sq_obs_filtered.size()
    # need to take the origin fixing restraint into the account!
    n_restraints = self.normal_eqns.n_restraints +\
      len(self.normal_eqns.origin_fixing_restraint.singular_directions)
    cif_block['_refine_ls_number_restraints'] = n_restraints
    cif_block['_refine_ls_R_factor_all'] = fmt % self.r1_all_data[0]
    cif_block['_refine_ls_R_factor_gt'] = fmt % self.r1[0]
    cif_block['_refine_ls_restrained_S_all'] = fmt % self.normal_eqns.restrained_goof()
    cif_block['_refine_ls_shift/su_max'] = "%.4f" % flex.max(shifts)
    cif_block['_refine_ls_shift/su_mean'] = "%.4f" % flex.mean(shifts)
    cif_block['_refine_ls_structure_factor_coef'] = 'Fsqd'
    cif_block['_refine_ls_weighting_details'] = str(
      self.normal_eqns.weighting_scheme)
    cif_block['_refine_ls_weighting_scheme'] = 'calc'
    cif_block['_refine_ls_wR_factor_ref'] = fmt % self.normal_eqns.wR2()
    cif_block['_refine_ls_wR_factor_gt'] = fmt % self.wR2_factor(2)
    (h_min, k_min, l_min), (h_max, k_max, l_max) = refinement_refs.min_max_indices()
    if (refinement_refs.space_group().is_centric() or
        not refinement_refs.anomalous_flag()):
      cif_block['_reflns_Friedel_coverage'] = '0.0'
    else:
      cif_block['_reflns_Friedel_coverage'] = "%.3f" %(
        refinement_refs.n_bijvoet_pairs()/
        refinement_refs.complete_set().n_bijvoet_pairs())
    cif_block['_reflns_limit_h_min'] = h_min
    cif_block['_reflns_limit_h_max'] = h_max
    cif_block['_reflns_limit_k_min'] = k_min
    cif_block['_reflns_limit_k_max'] = k_max
    cif_block['_reflns_limit_l_min'] = l_min
    cif_block['_reflns_limit_l_max'] = l_max
    cif_block['_reflns_number_gt'] = (
      refinement_refs.data() > 2 * refinement_refs.sigmas()).count(True)
    cif_block['_reflns_number_total'] = refinement_refs.size()
    cif_block['_reflns_threshold_expression'] = 'I>=2u(I)' # XXX is this correct?
    use_aspherical = OV.GetParam('snum.NoSpherA2.use_aspherical')
    if self.use_tsc and use_aspherical == True:
      tsc_file_name = os.path.join(OV.GetParam('snum.NoSpherA2.dir'),OV.GetParam('snum.NoSpherA2.file'))
      if os.path.exists(tsc_file_name):
        tsc = open(tsc_file_name, 'r').readlines()
        cif_block_found = False
        tsc_info = """;\n"""
        for line in tsc:
          if "CIF:" in line:
            cif_block_found = True
            continue
          if ":CIF" in line:
            break
          if cif_block_found == True:
            tsc_info = tsc_info + line
        if not cif_block_found:
          details_text = """Refinement using NoSpherA2, an implementation of
 NOn-SPHERical Atom-form-factors in Olex2.
Please cite:
F. Kleemiss et al. DOI 10.1039/D0SC05526C - 2020
NoSpherA2 implementation of HAR makes use of
 tailor-made aspherical atomic form factors calculated
on-the-fly from a Hirshfeld-partitioned electron density (ED) - not from
spherical-atom form factors.

The ED is calculated from a gaussian basis set single determinant SCF
wavefunction - either Hartree-Fock or DFT using selected funtionals
 - for a fragment of the crystal.
This fregment can be embedded in an electrostatic crystal field by employing cluster charges.
The following options were used:
"""
          software = OV.GetParam('snum.NoSpherA2.source')
          details_text = details_text + "   SOFTWARE:       %s\n"%software
          if software != "DISCAMB":
            method = OV.GetParam('snum.NoSpherA2.method')
            basis_set = OV.GetParam('snum.NoSpherA2.basis_name')
            charge = OV.GetParam('snum.NoSpherA2.charge')
            mult = OV.GetParam('snum.NoSpherA2.multiplicity')
            relativistic = OV.GetParam('snum.NoSpherA2.Relativistic')
            partitioning = OV.GetParam('snum.NoSpherA2.wfn2fchk_SF')
            accuracy = OV.GetParam('snum.NoSpherA2.becke_accuracy')
            if partitioning == True:
              details_text = details_text + "   PARTITIONING:   NoSpherA2\n"
              details_text = details_text + "   INT ACCURACY:   %s\n"%accuracy
            else:
              details_text = details_text + "   PARTITIONING:   Tonto\n"
            details_text = details_text + "   METHOD:         %s\n"%method
            details_text = details_text + "   BASIS SET:      %s\n"%basis_set
            details_text = details_text + "   CHARGE:         %s\n"%charge
            details_text = details_text + "   MULTIPLICITY:   %s\n"%mult
            if relativistic == True:
              details_text = details_text + "   RELATIVISTIC:   DKH2\n"
            if software == "Tonto":
              radius = OV.GetParam('snum.NoSpherA2.cluster_radius')
              details_text = details_text + "   CLUSTER RADIUS: %s\n"%radius
          tsc_file_name = os.path.join(OV.GetParam('snum.NoSpherA2.dir'),OV.GetParam('snum.NoSpherA2.file'))
          if os.path.exists(tsc_file_name):
            f_time = os.path.getctime(tsc_file_name)
          else:
            f_time = os.path.getctime(file)
          import datetime
          f_date = datetime.datetime.fromtimestamp(f_time).strftime('%Y-%m-%d_%H-%M-%S')
          details_text = details_text + "   DATE:           %s\n"%f_date
          tsc_info = tsc_info + details_text
        tsc_info = tsc_info + ";\n"
        cif_block['_refine_special_details'] = tsc_info
        if acta_stuff:
          # remove IAM scatterer reference
          for sl in ['a', 'b']:
            for sn in range(1,5):
              cif_block.pop('_atom_type_scat_Cromer_Mann_%s%s' %(sl, sn))
          cif_block.pop('_atom_type_scat_Cromer_Mann_c')
          for i in range(cif_block['_atom_type_scat_source'].size()):
            cif_block['_atom_type_scat_source'][i] = "NoSpherA2: Chem.Sci. 2021, DOI:10.1039/D0SC05526C"
    def sort_key(key, *args):
      if key.startswith('_space_group_symop') or key.startswith('_symmetry_equiv'):
        return -1
      elif key.startswith('_atom_type'):
        return 0
      elif key.startswith('_geom_bond'):
        return '_geom_0'
      elif key.startswith('_geom_angle'):
        return '_geom_1'
      else:
        return key
    cif_block.sort(key=sort_key)
    return cif_block

  def create_fcf_content(self, list_code=None, add_weights=False, fixed_format=True):
    anomalous_flag = list_code < 0 and not self.xray_structure().space_group().is_centric()
    list_code = abs(list_code)
    if list_code == 4:
      fc_sq = self.normal_eqns.fc_sq.sort(by_value="packed_indices")
      fo_sq = self.normal_eqns.observations.fo_sq.sort(by_value="packed_indices")
      fo_sq = fo_sq.customized_copy(
        data=fo_sq.data()*(1/self.scale_factor),
        sigmas=fo_sq.sigmas()*(1/self.scale_factor))

      mas_as_cif_block = iotbx.cif.miller_arrays_as_cif_block(
        fc_sq, array_type='calc', format="coreCIF")
      mas_as_cif_block.add_miller_array(fo_sq, array_type='meas')

      if add_weights:
        weights = self.normal_eqns.weights
        _refln_F_squared_weight = fc_sq.array(data=weights*len(weights)*100/sum(weights))
        mas_as_cif_block.add_miller_array(
          _refln_F_squared_weight, column_name='_refln_F_squared_weight')
        if fixed_format:
          fmt_str="%4i"*3 + "%12.2f"*2 + "%10.2f"*2 + " %s"
        else:
          fmt_str = "%i %i %i %.3f %.3f %.3f %.3f %s"
      else:
        if fixed_format:
          fmt_str="%4i"*3 + "%12.2f"*2 + "%10.2f" + " %s"
        else:
          fmt_str = "%i %i %i %.3f %.3f %.3f %s"

      _refln_include_status = fc_sq.array(data=flex.std_string(fc_sq.size(), 'o'))
      mas_as_cif_block.add_miller_array(
        _refln_include_status, column_name='_refln_observed_status') # checkCIF only accepts this one

    elif list_code == 3:
      if self.hklf_code == 5:
        fo_sq, fc = self.get_fo_sq_fc(one_h_function=self.normal_eqns.one_h_linearisation)
        fo_sq = fo_sq.customized_copy(
          data=fo_sq.data()*(1/self.scale_factor),
          sigmas=fo_sq.sigmas()*(1/self.scale_factor),
          anomalous_flag=anomalous_flag)
        fo = fo_sq.as_amplitude_array().sort(by_value="packed_indices")
      else:
        fc = self.normal_eqns.f_calc.customized_copy(anomalous_flag=anomalous_flag)
        fo_sq = self.normal_eqns.observations.fo_sq.customized_copy(
          data=self.normal_eqns.observations.fo_sq.data()*(1/self.scale_factor),
          sigmas=self.normal_eqns.observations.fo_sq.sigmas()*(1/self.scale_factor),
          anomalous_flag=anomalous_flag)
        fo_sq = fo_sq.eliminate_sys_absent().merge_equivalents(algorithm="shelx").array()
        fo = fo_sq.as_amplitude_array().sort(by_value="packed_indices")
        fc, fo = fc.map_to_asu().common_sets(fo)
      if fo_sq.space_group().is_origin_centric():
        for i in xrange(0, fc.size()):
          fc.data()[i] = complex(math.copysign(abs(fc.data()[i]), fc.data()[i].real), 0.0)
      mas_as_cif_block = iotbx.cif.miller_arrays_as_cif_block(
        fo, array_type='meas', format="coreCIF")
      mas_as_cif_block.add_miller_array(
        fc, column_names=['_refln_A_calc', '_refln_B_calc'])
      if fixed_format:
        fmt_str="%4i"*3 + "%12.4f"*4
      else:
        fmt_str = "%i %i %i %f %f %f %f"
    elif list_code == 6:
      if self.hklf_code == 5:
        if self.use_tsc:
          fo_sq, fc = self.get_fo_sq_fc(one_h_function=self.normal_eqns.one_h_linearisation)
        else:
          fo_sq, fc = self.get_fo_sq_fc()
        fo_sq = fo_sq.customized_copy(
          data=fo_sq.data()*(1/self.scale_factor),
          sigmas=fo_sq.sigmas()*(1/self.scale_factor),
          anomalous_flag=anomalous_flag)
      else:
        fc = self.normal_eqns.f_calc.customized_copy(anomalous_flag=anomalous_flag)
        fo_sq = self.normal_eqns.observations.fo_sq.customized_copy(
          data=self.normal_eqns.observations.fo_sq.data()*(1/self.scale_factor),
          sigmas=self.normal_eqns.observations.fo_sq.sigmas()*(1/self.scale_factor),
          anomalous_flag=anomalous_flag)
        fc = fc.sort(by_value="packed_indices")
        fo_sq = fo_sq.sort(by_value="packed_indices")
        #fc, fo_sq = fo_sq.common_sets(fc)
      mas_as_cif_block = iotbx.cif.miller_arrays_as_cif_block(
        fo_sq, column_names=['_refln_F_squared_meas', '_refln_F_squared_sigma'],
        format="coreCIF")
      mas_as_cif_block.add_miller_array(
        fc, column_names=['_refln_F_calc', '_refln_phase_calc'])
      fmt_str = "%i %i %i %.3f %.3f %.3f %.3f"
    else:
      print("LIST code %i not supported" %list_code)
      return None, None
    # cctbx could make e.g. 1.001(1) become 1.0010(10), so use Olex2 values for cell

    cif = iotbx.cif.model.cif()
    cif_block = iotbx.cif.model.block()
    cif_block['_computing_structure_refinement'] = OV.get_cif_item('_computing_structure_refinement')
    cif_block['_shelx_refln_list_code'] = list_code
    cif_block.update(mas_as_cif_block.cif_block)

    cif_block['_cell_length_a'] = olx.xf.uc.CellEx('a')
    cif_block['_cell_length_b'] = olx.xf.uc.CellEx('b')
    cif_block['_cell_length_c'] = olx.xf.uc.CellEx('c')
    cif_block['_cell_angle_alpha'] = olx.xf.uc.CellEx('alpha')
    cif_block['_cell_angle_beta'] = olx.xf.uc.CellEx('beta')
    cif_block['_cell_angle_gamma'] = olx.xf.uc.CellEx('gamma')
    cif_block['_cell_volume'] = olx.xf.uc.VolumeEx()
    cif[OV.FileName().replace(' ', '')] = cif_block

    return cif, fmt_str

  def output_fcf(self):
    try: list_code = int(olx.Ins('list'))
    except: return

    fcf_cif, fmt_str = self.create_fcf_content(list_code)
    if not fcf_cif:
      print("Unsupported list (fcf) format")
      return
    with open(OV.file_ChangeExt(OV.FileFull(), 'fcf'), 'w') as f:
      fcf_cif.show(out=f, loop_format_strings={'_refln':fmt_str})

  def setup_shared_parameters_constraints(self):
    constraints = []
    constraints_itr = self.olx_atoms.constraints_iterator()
    for constraint_type, kwds in constraints_itr:
      if constraint_type == "adp":
        current = adp.shared_u(kwds["i_seqs"])
        constraints.append(current)
      elif constraint_type == "site":
        current = site.shared_site(kwds["i_seqs"])
        constraints.append(current)

    directions = self.olx_atoms.model.get('olex2.direction', ())
    self.directions = [d for d in directions]

    shared_rotated_adp = self.olx_atoms.model.get('olex2.constraint.rotated_adp', ())
    self.shared_rotated_adps = []
    for c in shared_rotated_adp:
      current = adp.shared_rotated_u(c[0], c[1], c[2], c[3], c[4])
      constraints.append(current)
      self.shared_rotated_adps.append(current)

    self.shared_param_constraints = []
    vars = self.olx_atoms.model['variables']['variables']
    equations = self.olx_atoms.model['variables']['equations']

    idslist = []
    if(len(equations)>0):
      # number of free variables
      FvarNum=0
      while OV.GetFVar(FvarNum) is not None:
        FvarNum+=1

      # Building matrix of equations
      lineareq = numpy.zeros((0,FvarNum))
      rowheader = {}
      nextfree = -1
      ignored = False
      idslist = []
      for equation in equations:
        ignored = False
        row = numpy.zeros((FvarNum))
        for variable in equation['variables']:
          label = "%s %d %d"%(variable[0]['references'][-1]['name'],
                              variable[0]['references'][-1]['id'],
                              variable[0]['references'][-1]['index'])
          if(variable[0]['references'][-1]['index']==4):
            if(label not in rowheader):
              nextfree+=1
              rowheader[label]=nextfree
              idslist += [variable[0]['references'][-1]['id']]
              key=nextfree
            else:
              key=rowheader[label]
            row[key]=variable[1]
          else:
            ignored = True
        row[FvarNum-1]=equation['value']
        if(not ignored):
          lineareq=numpy.append(lineareq, [row], axis=0)

      # LU decomposition to find incompatible or redundant constraints
      l,u = scipy.linalg.lu(lineareq, permute_l=True)

      if numpy.shape(u)[0] > 1:
        previous = u[-2,:]
        for row in numpy.flipud(u):
          if(numpy.all(row[0:-1]==0.0) and row[-1]!=0):
            raise Exception("One or more equations are not independent")
          if(numpy.all(row[0:-1]==previous[0:-1]) and row[-1]!=previous[-1]):
            raise Exception("One or more equations are not independent")
          previous = row

      # setting up constraints
      for row in numpy.flipud(u):
        if(numpy.all(row==0.0)):
          raise Exception("One or more equations are not independent")
        else:
          a = numpy.copy(row[:-1])
          current = occupancy.occupancy_affine_constraint(idslist, a, row[-1])
          #a = ((row[-3], row[-2]), row[-1])
          #current = occupancy.occupancy_pair_affine_constraint(idslist[-2:], a)
          constraints.append(current)

    for i, var in enumerate(vars):
      refs = var['references']
      as_var = []
      as_var_minus_one = []
      eadp = []
      for ref in refs:
        if(ref['id'] not in idslist):
          if ref['index'] == 4 and ref['relation'] == "var":
            as_var.append((ref['id'], ref['k']))
          if ref['index'] == 4 and ref['relation'] == "one_minus_var":
            as_var_minus_one.append((ref['id'], ref['k']))
        if ref['index'] == 5 and ref['relation'] == "var":
          eadp.append(ref['id'])
      if (len(as_var) + len(as_var_minus_one)) > 0:
        if len(eadp) != 0:
          print("Invalid variable use - mixes occupancy and U")
          continue
        current = occupancy.dependent_occupancy(as_var, as_var_minus_one)
        constraints.append(current)
        if len(as_var) > 0:
          scale = as_var[0][1]
          as_var = True
        else:
          as_var = False
          scale = as_var_minus_one[0][1]
        self.shared_param_constraints.append((i, current, 1./scale, as_var))
      elif len(eadp) > 1:
        current = adp.shared_u(eadp)
        constraints.append(current)
        self.shared_param_constraints.append((i, current, 1, True))

    same_groups = self.olx_atoms.model.get('olex2.constraint.same_group', ())
    for sg in same_groups:
      constraints.append(rigid.same_group(sg))
    fps = {}
    fdps = {}
    for idx, xs in enumerate(self._xray_structure.scatterers()):
      if xs.flags.grad_fp():
        fpl = fps.get(xs.scattering_type)
        if fpl is None:
          fps[xs.scattering_type] = [idx]
        else:
          fpl.append(idx)
      if xs.flags.grad_fdp():
        fdpl = fdps.get(xs.scattering_type)
        if fdpl is None:
          fdps[xs.scattering_type] = [idx]
        else:
          fdpl.append(idx)
    for t, l in fps.iteritems():
      if len(l) > 1:
        constraints.append(fpfdp.shared_fp(l))
    for t, l in fdps.iteritems():
      if len(l) > 1:
        constraints.append(fpfdp.shared_fdp(l))
    return constraints

  def fix_rigid_group_params(self, pivot_neighbour, pivot, group, sizable):
    ##fix angles
    if pivot_neighbour is not None:
     for a in group:
       self.fixed_angles.setdefault((pivot_neighbour, pivot, a), 1)

    if pivot is not None:
     for i, a in enumerate(group):
       for j in xrange(i+1, len(group)):
         self.fixed_angles.setdefault((a, pivot, group[j]), 1)

    for a in group:
      ns = self.olx_atoms._atoms[a]['neighbours']
      for i, b in enumerate(ns):
        if b not in group: continue
        for j in xrange(i+1, len(ns)):
          if ns[j] not in group: continue
          self.fixed_angles.setdefault((a, b, ns[j]), 1)

    if not sizable:
      group = list(group)
      if pivot is not None:
        group.append(pivot)
      for a in group:
        ns = self.olx_atoms._atoms[a]['neighbours']
        for b in ns:
          if b not in group: continue
          self.fixed_distances.setdefault((a, b), 1)

  def setup_rigid_body_constraints(self, afix_iter):
    rigid_body_constraints = []
    rigid_body = {
      # m:    type       , number of dependent
      5:  ("Cp"          , 4),
      6:  ("Ph"          , 5),
      7:  ("Ph"          , 5),
      10: ("Cp*"         , 9),
      11: ("Naphthalene" , 9),
    }
    scatterers = self.xray_structure().scatterers()
    uc = self.xray_structure().unit_cell()
    for m, n, pivot, dependent, pivot_neighbours, bond_length in afix_iter:
      # pivot_neighbours excludes dependent atoms
      if len(dependent) == 0: continue
      info = rigid_body.get(m)  # this is needed for idealisation of the geometry
      if info != None and info[1] == len(dependent):
        lengths = None
        if bond_length != 0: lengths = (bond_length,)
        i_f = rigid.idealised_fragment()
        frag = i_f.generate_fragment(info[0], lengths=lengths)
        frag_sc = [pivot,]
        for i in dependent: frag_sc.append(i)
        sites = [uc.orthogonalize(scatterers[i].site) for i in frag_sc]
        new_crd = i_f.fit(frag, sites)
        for i, crd in enumerate(new_crd):
          scatterers[frag_sc[i]].site = uc.fractionalize(crd)
      if m == 0 or m in rigid_body:
        current = None
        if n in(6, 9):
          current = rigid.rigid_rotatable_expandable_group(
            pivot, dependent, n == 9, True)
        elif n in (3,4,7,8):
          if n in (3,4):
            current = rigid.rigid_riding_expandable_group(
              pivot, dependent, n == 4)
          elif len(pivot_neighbours) < 1:
            print("Invalid rigid group for " + scatterers[pivot].label)
          else:
            neighbour = pivot_neighbours[0]
            for n in pivot_neighbours[1:]:
              if type(n) != tuple:
                neighbour = n
                break
            if type(neighbour) == tuple:
              olx.Echo("Could not create rigid rotating group based on '%s' " %(
                        scatterers[pivot].label) +
                       "because the pivot base is symmetry generated, creating " +
                       "rigid riding group instead - use 'compaq -a' to avoid "+
                       "this warning", m="warning")
              current = rigid.rigid_riding_expandable_group(
                pivot, dependent, False)
            else:
              current = rigid.rigid_pivoted_rotatable_group(
                pivot, neighbour, dependent,
                sizeable=n in (4,8),  #nm 4 never coming here from the above
                rotatable=n in (7,8))

        if current and current not in rigid_body_constraints:
          rigid_body_constraints.append(current)
          sizable = (n==4 or n==8 or n== 9)
          if pivot_neighbours:
            self.fix_rigid_group_params(pivot_neighbours[0], pivot, dependent, sizable)
          else:
            self.fix_rigid_group_params(None, pivot, dependent, sizable)

    return rigid_body_constraints

  def setup_geometrical_constraints(self, afix_iter=None):
    geometrical_constraints = []
    constraints = {
      # AFIX mn : some of them use a pivot whose position is given wrt
      #           the first constrained scatterer site
      # m:    type                                    , pivot position
      1:  ("tertiary_xh_site"                        , -1),
      2:  ("secondary_xh2_sites"                     , -1),
      3:  ("staggered_terminal_tetrahedral_xh3_sites", -1),
      4:  ("secondary_planar_xh_site"                , -1),
      8:  ("staggered_terminal_tetrahedral_xh_site"  , -1),
      9:  ("terminal_planar_xh2_sites"               , -1),
      13: ("terminal_tetrahedral_xh3_sites"          , -1),
      14: ("terminal_tetrahedral_xh_site"            , -1),
      15: ("polyhedral_bh_site"                      , -1),
      16: ("terminal_linear_ch_site"                 , -1),
    }

    for m, n, pivot, dependent, pivot_neighbours, bond_length in afix_iter:
      if len(dependent) == 0: continue
      info = constraints.get(m)
      if info is not None:
        constraint_name = info[0]
        constraint_type = getattr(
          geometrical.hydrogens, constraint_name)
        rotating = n in (7, 8)
        stretching = n in (4, 8)
        if bond_length == 0:
          bond_length = None
        kwds = {
          'rotating' : rotating,
          'stretching' : stretching,
          'bond_length' : bond_length,
          'pivot' : pivot,
          'constrained_site_indices':dependent
          }
        if m == 2:
          if self.idealise_secondary_xh2_angle:
            kwds['angle'] = 109.47*math.pi/180
          elif self.refine_secondary_xh2_angle:
            kwds['flapping'] = True
        current = constraint_type(**kwds)
        # overrdide the default h-atom placement as it is hard to adjust cctbx
        # connectivity to match Olex2's
        current.add_to = hydrogen_atom_constraints_customisation(
          current, self.olx_atoms.atoms()).add_to
        geometrical_constraints.append(current)

    return geometrical_constraints

  def export_var_covar(self, matrix):
    with open(os.path.join(OV.FilePath(),OV.FileName()+".npy"), "wb") as wFile:
      wFile.write("VCOV\n")
      wFile.write(" ".join(matrix.annotations) + "\n")
      numpy.save(wFile, matrix.matrix.as_numpy_array())

  def f_obs_minus_f_calc_map(self, resolution):
    scale_factor = self.scale_factor
    detwin = self.twin_components is not None\
        and self.twin_components[0].twin_law != sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1))
    if detwin or self.hklf_code == 5:
      if self.use_tsc:
        fo2, f_calc = self.get_fo_sq_fc(one_h_function=self.normal_eqns.one_h_linearisation)
      else:
        fo2, f_calc = self.get_fo_sq_fc()
      if self.f_mask:
        from smtbx import masks
        fo2 = masks.modified_intensities(fo2, f_calc, self.f_mask)
    else:
      fo2 = self.normal_eqns.observations.fo_sq
      f_calc = self.normal_eqns.f_calc
    f_obs = fo2.f_sq_as_f()
    if scale_factor is None:
      k = f_obs.scale_factor(f_calc)
    else:
      k = math.sqrt(scale_factor)
    f_obs_minus_f_calc = f_obs.f_obs_minus_f_calc(1./k, f_calc)
    return f_obs_minus_f_calc.fft_map(
      symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
      resolution_factor=resolution,
    )

  def post_peaks(self, fft_map, max_peaks=5):
    from itertools import izip
    ####
    if False:
      import olex_xgrid
      grid = fft_map.real_map()
      gridding = grid.accessor()
      type = isinstance(grid, flex.int)
      olex_xgrid.Import(
        gridding.all(), gridding.focus(), grid.copy_to_byte_str(), type)
      olex_xgrid.SetMinMax(flex.min(grid), flex.max(grid))
      olex_xgrid.SetVisible(True)
      olex_xgrid.InitSurface(True)
    ###
    #have to get more peaks than max_peaks - cctbx often returns peaks on the atoms
    peaks = fft_map.peak_search(
      parameters=maptbx.peak_search_parameters(
        peak_search_level=3,
        interpolate=False,
        peak_cutoff=-1,
        min_distance_sym_equiv=1.0,
        max_clusters=max_peaks+len(self.xray_structure().scatterers())),
      verify_symmetry=False
      ).all()
    i = 0
    olx.Kill('$Q', au=True) #HP-JUL18 -- Why kill the peaks? -- cause otherwise they accumulate! #HP4/9/18
    for xyz, height in izip(peaks.sites(), peaks.heights()):
      if i < 3:
        a = olx.xf.uc.Closest(*xyz).split(',')
        pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A^3, %.3f A away from %s" %(
            i+1, xyz[0], xyz[1], xyz[2], height, float(a[1]), a[0])
        if self.verbose or i == 0:
          print(pi)
        self.log.write(pi + '\n')
      id = olx.xf.au.NewAtom("%.2f" %(height), *xyz)
      if id != '-1':
        olx.xf.au.SetAtomU(id, "0.06")
        i = i+1
      if i == 100 or i >= max_peaks:
        break
    if OV.HasGUI():
      basis = olx.gl.Basis()
      frozen = olx.Freeze(True)
    olx.xf.EndUpdate(True) #clear LST
    olx.Compaq(q=True)
    if OV.HasGUI():
      olx.gl.Basis(basis)
      olx.Freeze(frozen)
      OV.Refresh()

  def show_summary(self, log=None):
    import sys

    _ = self.cycles.n_iterations
    plural = "S"
    if _ == 1:
      plural = ""

    if log is None: log = sys.stdout

    pad = 2 - len(str(self.cycles.n_iterations))
    print >> log, "\n  ++++++++++++++++++++++++++++++++++++++++++++++++%s+++ After %i CYCLE%s +++" %(pad*"+", self.cycles.n_iterations, plural)
    #print >> log, " +"
    print >> log, "  +  R1:       %.4f for %i reflections I >= 2u(I)" %self.r1
    print >> log, "  +  R1 (all): %.4f for %i reflections" %self.r1_all_data

    print >> log, "  +  wR2:      %.4f, GooF:  %.4f" % (
      self.normal_eqns.wR2(),
      self.normal_eqns.goof()
    )

    print >> log, "  +  Diff:     max=%.2f, min=%.2f" %(
      self.diff_stats.max(),
      self.diff_stats.min()
    )

    if(self.cycles.n_iterations>0):
      max_shift_site = self.normal_eqns.max_shift_site()
      max_shift_u = self.normal_eqns.max_shift_u()
      max_shift_esd = self.normal_eqns.max_shift_esd
      max_shift_esd_item = self.normal_eqns.max_shift_esd_item
      print >> log, "  +  Shifts:   xyz: %.4f for %s, U: %.4f for %s, Max/esd = %.4f for %s" %(
      max_shift_site[0],
      max_shift_site[1].label,
      max_shift_u[0],
      max_shift_u[1].label,
      max_shift_esd,
      max_shift_esd_item
      )
    else:
      max_shift_site = 99
      max_shift_u = 99
      max_shift_esd = 99
      max_shift_esd_item = 99
      print >> log, "NO CYCLES!"

    pad = 9 - len(str(self.n_constraints)) - len(str(self.normal_eqns.n_restraints)) - len(str(self.normal_eqns.n_parameters))
    print >> log, "  ++++++++++++ %i Constraints | %i Restraints | %i Parameters +++++++++%s"\
      %(self.n_constraints, self.normal_eqns.n_restraints, self.normal_eqns.n_parameters, "+"*pad)


    OV.SetParam("snum.refinement.max_shift_over_esd",
      max_shift_esd)
    OV.SetParam('snum.refinement.max_peak', self.diff_stats.max())
    OV.SetParam('snum.refinement.max_hole', self.diff_stats.min())
    OV.SetParam('snum.refinement.goof', "%.4f" %self.normal_eqns.goof())

  def get_disagreeable_reflections(self, show_in_console=False):
    fo2 = self.normal_eqns.observations.fo_sq\
      .customized_copy(sigmas=flex.sqrt(1/self.normal_eqns.weights))\
      .apply_scaling(factor=1/self.normal_eqns.scale_factor())

    if show_in_console:
      result = fo2.show_disagreeable_reflections(self.normal_eqns.fc_sq, out=log)
    else:
      result = fo2.disagreeable_reflections(self.normal_eqns.fc_sq)

    bad_refs = []
    for i in xrange(result.fo_sq.size()):
      sig = math.fabs(
        result.fo_sq.data()[i]-result.fc_sq.data()[i])/result.delta_f_sq_over_sigma[i]
      bad_refs.append((
        result.indices[i][0], result.indices[i][1], result.indices[i][2],
        result.fo_sq.data()[i], result.fc_sq.data()[i], sig))
    olex_core.SetBadReflections(bad_refs.__iter__())

  def show_comprehensive_summary(self, log=None):
    import sys
    if log is None: log = sys.stdout
    self.show_summary(log)
    standard_uncertainties = self.twin_covariance_matrix.matrix_packed_u_diagonal()
    if self.twin_components is not None and len(self.twin_components):
      print >> log
      print >> log, "Twin summary:"
      print >> log, "twin_law  fraction  standard_uncertainty"
      for i, twin in enumerate(self.twin_components):
        if twin.grad:
          print >> log, "%-9s %-9.4f %.4f" %(
            twin.twin_law.as_hkl(), twin.value, math.sqrt(standard_uncertainties[i]))
    print >> log
    print >> log, "Disagreeable reflections:"
    self.get_disagreeable_reflections()

