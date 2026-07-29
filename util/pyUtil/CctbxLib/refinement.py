import math, os, sys
from cctbx_olex_adapter import OlexCctbxAdapter, OlexCctbxMasks, rt_mx_from_olx
import cctbx_olex_adapter as COA
from boost_adaptbx.boost import python
ext = python.import_ext("smtbx_refinement_least_squares_ext")
constraints_ext = python.import_ext("smtbx_refinement_constraints_ext")

from olexFunctions import OV
from variableFunctions import nsa2_get_param

import olx
import olex
import olex_core
import gui

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

debug = OV.IsDebugging()


class FullMatrixRefine(OlexCctbxAdapter):
  solvers = {
    #'Gauss-Newton': normal_eqns_solving.naive_iterations_with_damping_and_shift_limit,
    'Gauss-Newton': olex2_normal_equations.naive_iterations_with_damping_and_shift_limit,
    #'Levenberg-Marquardt': normal_eqns_solving.levenberg_marquardt_iterations,
    'Levenberg-Marquardt': olex2_normal_equations.levenberg_marquardt_iterations,
    'NSFF': normal_eqns_solving.levenberg_marquardt_iterations,
    'FullCG': olex2_normal_equations.scipy_iterations,
    'L-BFGS-B': olex2_normal_equations.scipy_iterations,
    'Newton-CG': olex2_normal_equations.scipy_iterations,
    'SLSQP': olex2_normal_equations.scipy_iterations,
    'CGLS-J': olex2_normal_equations.cgls_iterations,
  }
  solvers_default_method = 'Gauss-Newton'
  # Methods solved by scipy.optimize.minimize, mapping the Olex2 name onto the
  # scipy one. FullCG is scipy's 'CG', nonlinear conjugate gradient, which is a
  # different thing from ShelXL's CGLS (conjugate gradients on the linearised
  # problem, method 'CGLS-J' above).
  scipy_methods = {
    'FullCG': 'CG',
    'L-BFGS-B': 'L-BFGS-B',
    'Newton-CG': 'Newton-CG',
    'SLSQP': 'SLSQP',
  }

  def __init__(self, max_cycles=None, max_peaks=5, verbose=False, on_completion=None, weighting=None):
    olx.stopwatch.run(OlexCctbxAdapter.__init__ , self)
    # try to initialise openblas
    OV.init_fast_linalg()
    self.interrupted = False
    self.max_cycles = max_cycles
    self.max_peaks = max_peaks
    self.verbose = verbose
    sys.stdout.refresh = False
    self.scale_factor = None
    # None unless a full-matrix step produced them; CGLS without ESD leaves
    # them None, and the CIF and reports fall back to no uncertainties
    self.covariance_matrix_and_annotations = None
    self.twin_covariance_matrix = None
    self.failure = False
    self.objective_only = False
    self.log = open(OV.file_ChangeExt(OV.FileFull(), 'log'), 'w')
    self.hooft = None
    self.hooft_str = ""
    self.on_completion = on_completion
    # set the secondary CH2 treatment
    self.refine_secondary_xh2_angle = False
    self.idealise_secondary_xh2_angle = False
    self.use_tsc = False
    self.table_file_name = None
    self.flack_reflections_used = None
    sec_ch2_treatment = OV.GetParam('snum.smtbx.secondary_ch2_angle')
    if sec_ch2_treatment == 'idealise':
      self.idealise_secondary_xh2_angle = True
    elif sec_ch2_treatment == 'refine':
      self.refine_secondary_xh2_angle = True
    self.weighting = weighting
    if self.weighting is None:
      weighting_choice = OV.GetParam('snum.refinement.weighting_scheme')
      if weighting_choice == 'shelx' or weighting_choice == "default":
        self.weighting = self.get_shelxl_weighting()
      elif weighting_choice == 'new_shelx':
        self.weighting = self.get_new_shelxl_weighting()
      elif weighting_choice == 'unity':
        self.weighting = self.get_unit_weighting()
      elif weighting_choice == 'sigma':
        self.weighting = self.get_sigma_weighting()
      elif weighting_choice == 'stl':
        self.weighting = self.get_sin_theta_over_lambda_weighting()
      else:
        print("WARNING: unsupported weighting scheme: '%s' is replaced by 'shelx'"\
            %weighting_choice)
        self.weighting = self.get_shelxl_weighting()

  def run(self,
          build_only=False, #return normal normal equations object
          table_file_name = None,
          normal_equations_class_builder=olex2_normal_equations.normal_equation_class,
          ed_refinement=None,
          reparametrisation_only=False #returns self.reparametrisation
          ):
    """ If build_only is True - this method initialises and returns the normal
     equations object.
     If reparametrisation_only is True - only constructs and returns the reparametrisation object
    """
    self.ed_refinement = ed_refinement
    self.table_file_name = table_file_name
    stopwatch = olx.stopwatch
    open_blas_tn = 1
    try:
      stopwatch.start("Initialising")
      from fast_linalg import env
      if env.initialised:
        open_blas_tn = env.threads
      # refine.max_threads is set and reset by AC
      thread_n = int(OV.GetVar("refine.max_threads", "0"))
      if thread_n == 0:
        thread_n = OV.GetThreadN()
      ext.build_normal_equations.available_threads = thread_n
    except:
      pass
    if not (reparametrisation_only or build_only):
      optimiser = OV.GetParam('snum.refinement.method')
      if optimiser in FullMatrixRefine.scipy_methods:
        optimiser += " via scipy.optimize.minimize"
      print("Optimiser: %s. Using %s refinement and %s OpenBlas threads. "
        "Using OpenMP: %s." %(
        optimiser,
        ext.build_normal_equations.available_threads,
        open_blas_tn,
        OV.GetParam("user.refinement.use_openmp")))
    fcf_only = nsa2_get_param('make_fcf_only')
    OV.SetVar('stop_current_process', False) #reset any interrupt before starting.
    self.normal_equations_class = normal_equations_class_builder()
    self.use_tsc = table_file_name is not None
    self.reflections.show_summary(log=self.log)
    self.f_mask = None
    self.fo_sq_fc = None
    self.fo_sq_fc_key = None
    if OV.GetParam("snum.refinement.use_solvent_mask") and not reparametrisation_only:
      #OV.SetVar('current_mask_sqf', "")
      ### If the original filename already ends in _sq (i.e. the files come from outside Olex2, things get very confusing. Maybe one way of dealing with it is to leave the original files all untouched, and rename sNum to the filename without the _sq bit, alongside with the HKLSrc(). But will metadata get lost? Should all files get copied/renamed?
      #fn = OV.HKLSrc()
      #nfn = fn.replace("_sq.hkl", '.hkl')
      #if "_sq.hkl" in fn:
        #olx.file.Copy(fn, nfn)
        #OV.HKLSrc(nfn)
        #olex.m(f"file {OV.file_ChangeExt(nfn, 'res')}")
        #olex.m(f"reap {OV.file_ChangeExt(nfn, 'res')}")
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
        _ = OV.GetParam("snum.refinement.recompute_mask_before_refinement_prg")
        if _ == "Platon":
          olex.m("spy.OlexPlaton(q,.ins)")
          self.f_mask = self.load_mask()
          gui.tools.GetMaskInfo.sort_out_masking_hkl()
          if not self.f_mask:
            self.failure = True
            return
        else:
          stopwatch.run(OlexCctbxMasks)
          gui.tools.GetMaskInfo.sort_out_masking_hkl()
          if olx.current_mask.flood_fill.n_voids() > 0:
            self.f_mask = olx.current_mask.f_mask()
      if self.f_mask:
        fo_sq = self.reflections.f_sq_obs_filtered
        if not fo_sq.space_group().is_centric() and fo_sq.anomalous_flag():
          self.f_mask = self.f_mask.generate_bijvoet_mates()
    shared_parameter_constraints, fix_occupancy_for, sump_proxies =\
      self.setup_shared_parameters_constraints()
    # pre-build structure taking shared parameters into account
    self.xray_structure(construct_restraints=True,
      shared_parameters=shared_parameter_constraints)
    # some of the SUMP got reduced to fixed occupancy
    if fix_occupancy_for:
      msg = "Consider updating your model - occupancy has got reduced for:"
      for sc_i, occu in fix_occupancy_for:
        sc = self.xray_structure().scatterers()[sc_i]
        sc.flags.set_grad_occupancy(False)
        sc.occupancy = occu
        msg += " %s.occu=%.3f" %(sc.label, occu)
      print(msg)
    restraints_manager = self.restraints_manager()
    restraints_manager.sump_proxies = sump_proxies
    self._add_npd_restraint(restraints_manager)
    #put shared parameter constraints first - to allow proper bookkeeping of
    #overrided parameters (U, sites)
    stopwatch.start("Setting up constraints")
    self.fixed_distances = {}
    self.fixed_angles = {}
    self.constraints = shared_parameter_constraints + self.constraints
    self.constraints += self.setup_rigid_body_constraints(
      self.olx_atoms.afix_iterator())
    self.constraints += self.setup_geometrical_constraints(
      self.olx_atoms.afix_iterator())

    # NoMoRe constraint — built from snum params, same as any other constraint
    self._nomore_constraint = None
    if OV.GetParam('snum.NoMoRe.enabled', False):
      try:
        from NoMoRe.nomore import build_constraint
        nomore_c = build_constraint()
        if nomore_c is not None:
          self.constraints.append(nomore_c)
          self._nomore_constraint = nomore_c
      except Exception as e:
        print(f'NoMoRe constraint skipped: {e}')

    self.n_constraints = len(self.constraints)

    self.temp = self.olx_atoms.exptl['temperature']
    if self.temp < -274: self.temp = 20
    self.fc_correction = None
    #set up Fc  correction if defined
    if ed_refinement:
      msg = "ED refinement"
      msg_l = len(msg)
      #if self.exti is not None and not OV.GetACI().EDI.get_stored_param_bool("refinement.refine.exti"):
      if self.exti is not None and not OV.GetHeaderParamBool('ED.refinement.refine.exti'):
        self.exti = None
        msg +=", ignoring EXTI"
      if self.swat is not None:
        self.swat = None
        msg +=", ignoring SWAT"
      if len(msg) != msg_l and not(reparametrisation_only or build_only) and debug:
        print(msg)
      self.fc_correction = xray.dummy_fc_correction()
      self.fc_correction.expression = ''
      #disable weights auto-update
      OV.SetParam('snum.refinement.update_weight', False)
    if self.exti is not None:
      self.fc_correction = xray.shelx_extinction_correction(
        self.xray_structure().unit_cell(), self.wavelength, self.exti)
      self.fc_correction.grad = True
      self.fc_correction.expression = r'Fc^*^=kFc[1+0.001xFc^2^\l^3^/sin(2\q)]^-1/4^'
    elif self.swat is not None:
      self.fc_correction = xray.shelx_SWAT_correction(
        self.xray_structure().unit_cell(), self.swat[0], self.swat[1])
      self.fc_correction.grad = True
      self.fc_correction.expression = r'Fc^*^=kFc[1-g*exp(-8*\p^2^ U (sin(\q)/\l)^2^]^2^'
    else:
      self.fc_correction = xray.dummy_fc_correction()
      self.fc_correction.expression = ''

    stopwatch.start("Building reparametrisation")
    self.reparametrisation = constraints.reparametrisation(
      structure=self.xray_structure(),
      constraints=self.constraints,
      connectivity_table=self.connectivity_table,
      twin_fractions=self.get_twin_fractions(),
      temperature=self.temp,
      fc_correction=self.fc_correction,
      directions=self.directions
    )
    self.reparametrisation.fixed_distances.update(self.fixed_distances)
    self.reparametrisation.fixed_angles.update(self.fixed_angles)

    self.std_obserations = None
    if ed_refinement:
      try:
        OV.GetACI().EDI.setup_refinement(self,
         reparametrisation_only=reparametrisation_only,
         table_file_name=table_file_name)
      except Exception as e:
        olx.Echo(str(e), m="error")
        self.failure = True
        return
    elif len(self.reparametrisation.mapping_to_grad_fc_all) == 0 and self.max_cycles != 0:
      if not (reparametrisation_only or build_only):
        olx.Echo("Nothing to refine!", m="error")
      self.failure = True
      return
    if reparametrisation_only:
      return self.reparametrisation

    use_openmp = OV.GetParam("user.refinement.use_openmp")
    max_mem = int(OV.GetParam("user.refinement.openmp_mem"))
    if table_file_name is not None:
      for i,atom in enumerate(self.olx_atoms._atoms):
        self.xray_structure().scatterers()[i].set_part(atom['part'])
    stopwatch.start("Initialising normal equations")
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
    self.normal_eqns = self.normal_equations_class(
      self.observations,
      self,
      self.olx_atoms,
      table_file_name=table_file_name,
      f_mask=self.f_mask,
      restraints_manager=restraints_manager,
      weighting_scheme=self.weighting,
      log=self.log,
      may_parallelise=ext.build_normal_equations.available_threads > 1,
      use_openmp=use_openmp,
      max_memory=max_mem,
      std_observations=self.std_obserations
    )
    self.normal_eqns.shared_param_constraints = self.shared_param_constraints
    self.normal_eqns.shared_rotated_adps = self.shared_rotated_adps
    self.normal_eqns.shared_rotating_adps = self.shared_rotating_adps
    if build_only:
      return self.normal_eqns
    stopwatch.start("Refinement")
    method = OV.GetParam('snum.refinement.method')
    iterations_class = FullMatrixRefine.solvers.get(method)
    if iterations_class == None:
      method = FullMatrixRefine.solvers_default_method
      iterations_class = FullMatrixRefine.solvers.get(method)
      print("WARNING: unsupported method: '%s' is replaced by '%s'"\
        %(method, FullMatrixRefine.solvers_default_method))
    assert iterations_class is not None
    if fcf_only:
      self.max_cycles = 0
    try:
      damping = OV.GetDampingParams()
      if not fcf_only:
        self.print_table_header()
        self.print_table_header(self.log)
      try:
        convergence_as_shift_over_esd = OV.GetVar('convergence_as_shift_over_esd', 1e-3)
        if(method=='Levenberg-Marquardt'):
#          normal_eqns_solving.levenberg_marquardt_iterations.tau=1e-4
          self.get_refinement_wrapper(iterations_class)(self, self.normal_eqns,
              n_max_iterations=self.max_cycles,
              track_all=True,
              gradient_threshold=None,
              step_threshold=None,
              tau = 1e-6,
              convergence_as_shift_over_esd=convergence_as_shift_over_esd,
              )
        elif method == 'CGLS-J':
          # 'auto' is how a phil choice spells "pick on what fits"
          mode = OV.GetParam('snum.refinement.cgls.mode')
          if mode == 'auto':
            mode = None
          self.get_refinement_wrapper(iterations_class)(self, self.normal_eqns,
              n_max_iterations=self.max_cycles,
              cg_tolerance=OV.GetParam('snum.refinement.cgls.tolerance'),
              max_cg_iterations=OV.GetParam(
                'snum.refinement.cgls.max_cg_iterations'),
              mode=mode,
              # The "Max. Memory (MB)" box: the budget the design matrix must
              # fit within to be stored, which is the fast mode.
              max_design_matrix_memory=max_mem,
              # The keyword is compute_standard_uncertainties, not
              # standard_uncertainties: the class mixes in a method of the
              # latter name (scale_shifts calls it), which a bool would shadow.
              # The phil name is unchanged.
              compute_standard_uncertainties=OV.GetParam(
                'snum.refinement.cgls.standard_uncertainties'),
              single_precision_design_matrix=OV.GetParam(
                'snum.refinement.cgls.single_precision_design_matrix'),
              # DAMP means here what it means for Gauss-Newton
              damping_value=damping[0],
              max_shift_over_esd=damping[1],
              convergence_as_shift_over_esd=convergence_as_shift_over_esd,
              gradient_threshold=None,
              step_threshold=None)
        elif method in FullMatrixRefine.scipy_methods:
          # 'none' is how a phil choice spells no preconditioning
          preconditioning = OV.GetParam(
            'snum.refinement.scipy.preconditioning')
          if preconditioning == 'none':
            preconditioning = None
          # track_all is deliberately not passed: it journals the gradient and
          # the step at every build of the normal equations, of which there are
          # many per cycle here rather than one.
          self.get_refinement_wrapper(iterations_class)(self, self.normal_eqns,
              method=FullMatrixRefine.scipy_methods[method],
              n_max_iterations=self.max_cycles,
              max_evaluations=OV.GetParam(
                'snum.refinement.scipy.max_evaluations'),
              g_tolerance=OV.GetParam('snum.refinement.scipy.g_tolerance'),
              f_tolerance=OV.GetParam('snum.refinement.scipy.f_tolerance'),
              preconditioning=preconditioning,
              convergence_as_shift_over_esd=convergence_as_shift_over_esd,
              gradient_threshold=None,
              step_threshold=None)
        else:
          self.get_refinement_wrapper(iterations_class)(self, self.normal_eqns,
              n_max_iterations=self.max_cycles,
              track_all=True,
              damping_value=damping[0],
              max_shift_over_esd=damping[1],
              convergence_as_shift_over_esd=convergence_as_shift_over_esd,
              gradient_threshold=None,
              step_threshold=None)

      except RuntimeError as e:
        str_e = str(e)
        if 'external_interrupt' in str_e:
          print("Refinement interrupted")
          self.interrupted = True
          self.failure = True # the object is unusable
          return
        elif "is an empty array" in str_e:
          print("There is nothing to refine.")
          self.failure = True
          return
        elif use_openmp and "normal_equations.h" in str_e and "Not implemented" in str_e:
          olx.Echo("Please restart Olex2 to fully enable OpenMP!", m="warning")
          self.failure = True
          return
        else:
          raise e
      stopwatch.start("Analysis")
      self.r1 = self.normal_eqns.r1_factor(cutoff_factor=2)
      self.r1_all_data = self.normal_eqns.r1_factor()
      if len(self.reparametrisation.mapping_to_grad_fc_all) == 0:
        self.objective_only = True
        stopwatch.start("FFT")
        fo_minus_fc = self.f_obs_minus_f_calc_map(0.3)
        fo_minus_fc.apply_volume_scaling()
        self.diff_stats = fo_minus_fc.statistics()
        self.post_peaks(fo_minus_fc, max_peaks=self.max_peaks)
        if not fcf_only:
          self.show_summary()
          self.show_comprehensive_summary(log=self.log)
        else:
          return
        stopwatch.start("CIF")
        block_name = OV.FileName().replace(' ', '')
        if self.on_completion:
          cif = iotbx.cif.model.cif()
          cif[block_name] = self.as_cif_block()
          stopwatch.start("on_completion")
          self.on_completion(cif[block_name])
        return
      # get the final shifts
      stopwatch.run(self.normal_eqns.analyse_shifts)
      if getattr(self.cycles, 'compute_standard_uncertainties', True):
        self.scale_factor = self.cycles.scale_factor_history[-1]
        self.covariance_matrix_and_annotations=self.normal_eqns.covariance_matrix_and_annotations()
        self.twin_covariance_matrix = self.normal_eqns.covariance_matrix(
          jacobian_transpose=self.reparametrisation.jacobian_transpose_matching(
            self.reparametrisation.mapping_to_grad_fc_independent_scalars))
        fcf_stuff = '-' in olx.Ins('MORE')
        if fcf_stuff:
          self.export_var_covar(self.covariance_matrix_and_annotations)
        try:
          stopwatch.run(self.check_hooft)
        except Exception as e:
          print("Failed to evaluate Hooft parameter")
          if OV.IsDebugging():
            sys.stderr.formatExceptionInfo()
        if not OV.IsEDData():
          OV.SetParam('snum.refinement.hooft_str', self.hooft_str)
        #extract SU on BASF and extinction
        stopwatch.start("Extracting scalars")
        diag = self.twin_covariance_matrix.matrix_packed_u_diagonal()
        dlen = len(diag)
        if self.reparametrisation.thickness and self.reparametrisation.thickness.grad:
          dlen -= 1
        if self.reparametrisation.fc_correction and self.reparametrisation.fc_correction.grad:
          if isinstance(self.reparametrisation.fc_correction, xray.shelx_extinction_correction):
            su = math.sqrt(diag[dlen-1])
            OV.SetExtinction(self.reparametrisation.fc_correction.value, su)
            dlen -= 1
          elif isinstance(self.reparametrisation.fc_correction, xray.shelx_SWAT_correction):
            e_g = math.sqrt(diag[dlen-2])
            e_U = math.sqrt(diag[dlen-1])
            OV.SetSWAT(self.reparametrisation.fc_correction.g,
              self.reparametrisation.fc_correction.U,
            e_g, e_U)
            dlen -= 2
        try:
          for i in range(dlen):
            olx.xf.rm.BASF(i, olx.xf.rm.BASF(i), math.sqrt(diag[i]))
        except:
          pass
        if self._nomore_constraint is not None:
          try:
            from NoMoRe.nomore import save_scales
            save_scales(self._nomore_constraint)
          except Exception as e:
            print(f'NoMoRe: could not save scales: {e}')
      else:
        # CGLS asked not to compute standard uncertainties: no normal matrix
        # stands, so there is no covariance, as SHELXL's CGLS leaves it. The
        # refined model, R factors and difference map are unaffected, and the
        # CIF is written without uncertainties.
        self.scale_factor = self.normal_eqns.scale_factor()
    except RuntimeError as e:
      e_string = str(e)
      if e_string.startswith("cctbx::adptbx::debye_waller_factor_exp: max_arg exceeded"):
        print("Refinement failed to converge")
      elif "SCITBX_ASSERT(!cholesky.failure) failure" in e_string:
        print("Cholesky failure")
        i = str(e).rfind(' ')
        index = int(str(e)[i:])
        if index >= 0:
          # the index is a row of the normal matrix, i.e. an independent
          # parameter; translate it to the crystallographic parameter it stands
          # for. component_annotations lists grad_Fc components instead, of which
          # there are more once constraints reduce the model, so indexing it
          # with a normal-matrix row names the wrong parameter.
          try:
            annotations = self._independent_parameter_annotations()
          except Exception:
            annotations = list(self.reparametrisation.component_annotations)
          if index >= len(annotations):
            param_name = "Scalar Parameter"
          else:
            param_name = annotations[index]
          print("the leading minor of order %i for %s is not positive definite"\
           %(index, param_name))
          print("This parameter is not determined by the data. Look for a "
                "restraint or constraint involving it, or an atom that should "
                "not be refined freely.")
        if OV.IsDebugging():
          try:
            self._dump_refinement_diagnostics(e_string, offending_index=index)
          except Exception as de:
            print("could not dump diagnostics: %s" % de)
      elif "SMTBX_ASSERT(l != mi_lookup.end()) failure" in e_string:
        lines = e_string.split("\n")
        indices = lines[1].split("(")[2].split(")")[0].split(',')
        olx.Echo("Did not find values for reflection (%s,%s,%s) in scattering table!"%(indices[0],indices[1],indices[2]), m="error")
        olx.Echo("Try recalculating the .tsc file!", m="error")
      else:
        print("Refinement failed")
        import traceback
        traceback.print_exc()
        # any parameter index the error carries, named. cctbx reports these as
        # bare numbers, which say nothing about which atom is at fault.
        try:
          for described in self._annotate_parameter_indices(e_string):
            print("  %s" % described)
        except Exception:
          pass
        if OV.IsDebugging():
          try:
            self._dump_refinement_diagnostics(e_string)
          except Exception as de:
            print("could not dump diagnostics: %s" % de)
      self.failure = True
    else:
      stopwatch.start("FFT")
      fo_minus_fc = self.f_obs_minus_f_calc_map(0.3)
      fo_minus_fc.apply_volume_scaling()
      self.diff_stats = fo_minus_fc.statistics()
      self.post_peaks(fo_minus_fc, max_peaks=self.max_peaks)
      if not fcf_only:
        self.show_summary()
        self.show_comprehensive_summary(log=self.log)
      else:
        return
      stopwatch.start("CIF")
      block_name = OV.FileName().replace(' ', '')
      cif = iotbx.cif.model.cif()
      cif[block_name] = self.as_cif_block()
      acta = olx.Ins("ACTA").strip()
      if acta != "n/a":
        with open(OV.file_ChangeExt(OV.FileFull(), 'cif'), 'w') as f:
          print(cif, file=f)
        inc_hkl = acta and "NOHKL" != acta.split()[-1].upper()
        if not OV.GetParam('snum.refinement.cifmerge_after_refinement', False):
          olx.CifMerge(f=inc_hkl, u=True)
      stopwatch.start("FCF & weights")
      self.output_fcf(cif[block_name].get('_iucr_refine_fcf_details', None))
      new_weighting = self.weighting.optimise_parameters(
        self.normal_eqns.observations.fo_sq,
        self.normal_eqns.fc_sq,
        self.normal_eqns.scale_factor(),
        self.reparametrisation.n_independents)
      if not OV.IsEDRefinement():
        OV.SetParam(
          'snum.refinement.suggested_weight', "%s %s" %(new_weighting.a, new_weighting.b))
      if self.on_completion:
        stopwatch.start("on_completion")
        self.on_completion(cif[block_name])
      if olx.HasGUI() == 'true':
        olx.UpdateQPeakTable()
    finally:
      sys.stdout.refresh = True
      self.log.close()

  def _add_npd_restraint(self, restraints_manager):
    """ SHELXL's XNPD as a restraint: keep anisotropic ADPs positive-definite.

    Applied when the .ins carries an XNPD instruction, like any other ShelX
    instruction. Adds the smtbx npd_adp restraint to every anisotropic atom
    being refined; it works for any refinement method.
    """
    if olx.Ins("XNPD").strip() == "n/a":
      return
    from cctbx import adp_restraints
    s_target = OV.GetParam('snum.refinement.cgls.npd_s_target')
    sigma = OV.GetParam('snum.refinement.cgls.npd_sigma')
    weight = 1.0/(sigma*sigma)
    proxies = adp_restraints.shared_npd_adp_proxy()
    for i_seq, sc in enumerate(self.xray_structure().scatterers()):
      if sc.flags.use_u_aniso() and sc.flags.grad_u_aniso():
        proxies.append(adp_restraints.npd_adp_proxy(
          i_seqs=(i_seq,), weight=weight, s_target=s_target))
    if proxies.size():
      restraints_manager.npd_adp_proxies = proxies
      print("XNPD: restraining %d anisotropic atoms positive-definite"
            % proxies.size())

  def _dump_refinement_diagnostics(self, error_string, offending_index=None):
    """ Dump everything needed to work on a refinement failure offline.

    Called only in debug mode (OV.IsDebugging()). A singular normal matrix -- a
    Cholesky failure -- is almost always a restraint or constraint that leaves a
    parameter or a direction undetermined. These files let that be found without
    an attached debugger:

      <name>.refine_debug.json                 error, the offending parameter,
                                               every restraint, constraint and
                                               scatterer, and the annotations
      <name>.refine_debug.normal_matrix_u.npy  the packed upper triangle of the
                                               normal matrix that failed Cholesky
      <name>.refine_debug.gradient.npy         the right hand side

    Load the matrix with numpy and unpack the upper triangle: a zero or negative
    pivot, or the eigenvector of the near-zero eigenvalue, is the undetermined
    direction, and the restraints and constraints in the JSON are where an
    over-determination usually hides. parameter_annotations names each row -- so
    the eigenvector's largest components read straight off as parameter names.

    parameter_annotations is aligned with the matrix (row i is
    parameter_annotations[i]), translated from the grad_Fc components through the
    reparametrisation by _independent_parameter_annotations. The raw grad_Fc list
    is kept alongside as grad_fc_component_annotations for reference.

    Everything is best-effort: a failure to serialise one part must not stop the
    rest, since the point is to salvage what can be salvaged from a broken run.
    """
    import json
    try:
      base = OV.file_ChangeExt(OV.FileFull(), '') + ".refine_debug"
    except Exception:
      base = "refine_debug"
    try:
      labels = list(self.xray_structure().scatterers().extract_labels())
    except Exception:
      labels = []
    try:
      grad_fc_annotations = list(self.reparametrisation.component_annotations)
    except Exception:
      grad_fc_annotations = []
    # aligned with the normal matrix and gradient: row i is matrix_annotations[i]
    try:
      matrix_annotations = self._independent_parameter_annotations()
    except Exception as e:
      matrix_annotations = []
      print("could not map Cholesky rows to parameters: %s" % e)

    diag = {'error': error_string,
            'n_matrix_parameters': len(matrix_annotations) or None,
            'n_grad_fc_components': len(grad_fc_annotations)}
    if offending_index is not None:
      diag['offending_index'] = int(offending_index)
      diag['offending_parameter'] = (
        matrix_annotations[offending_index]
        if 0 <= offending_index < len(matrix_annotations)
        else "out of range")
    # row i of the normal matrix and gradient is this parameter
    diag['parameter_annotations'] = matrix_annotations
    # the raw grad_Fc component list, for reference
    diag['grad_fc_component_annotations'] = grad_fc_annotations
    for key, fn in (('restraints', lambda: self._serialise_restraints(labels)),
                    ('constraints', self._serialise_constraints),
                    ('scatterers', self._serialise_scatterers)):
      try:
        diag[key] = fn()
      except Exception as e:
        diag[key] = "could not serialise: %s" % e
    try:
      with open(base + ".json", 'w') as f:
        json.dump(diag, f, indent=2, default=str)
      print("Refinement diagnostics: wrote %s.json" % base)
    except Exception as e:
      print("Refinement diagnostics: could not write %s.json: %s" % (base, e))

    try:
      import numpy
    except Exception:
      numpy = None
    if numpy is not None:
      # the accessor may live on the normal equations object or on an ls it
      # wraps, depending on the refinement method, so try each
      candidates = [self.normal_eqns,
                    getattr(self.normal_eqns, 'non_linear_ls', None),
                    getattr(self.normal_eqns, 'actual', None)]
      def first(method):
        for obj in candidates:
          fn = getattr(obj, method, None)
          if fn is not None:
            return fn()
        raise AttributeError(method)
      for suffix, method in (("normal_matrix_u", "normal_matrix_packed_u"),
                             ("gradient", "opposite_of_gradient")):
        try:
          numpy.save(base + "." + suffix + ".npy", first(method).as_numpy_array())
          print("Refinement diagnostics: wrote %s.%s.npy" % (base, suffix))
        except Exception as e:
          print("Refinement diagnostics: could not write %s (%s)" % (suffix, e))

  def _serialise_restraints(self, labels):
    """ Every restraint proxy on the manager, as atom labels, weight and any
    target it carries. """
    out = {}
    rm = self.restraints_manager
    if rm is None:
      return out
    for name in dir(rm):
      if not name.endswith('_proxies'):
        continue
      proxies = getattr(rm, name, None)
      if proxies is None:
        continue
      try:
        out[name] = [self._proxy_to_dict(p, labels) for p in proxies]
      except Exception as e:
        out[name] = "could not serialise: %s" % e
    return out

  def _proxy_to_dict(self, proxy, labels):
    d = {}
    i_seqs = getattr(proxy, 'i_seqs', None)
    if i_seqs is None:
      i_seqs = getattr(proxy, 'i_seq', None)
    if i_seqs is not None:
      try:
        d['atoms'] = [labels[int(i)] if 0 <= int(i) < len(labels) else int(i)
                      for i in i_seqs]
      except TypeError:
        d['atoms'] = labels[int(i_seqs)] if 0 <= int(i_seqs) < len(labels) \
          else int(i_seqs)
    for attr in ('weight', 'distance_ideal', 'angle_ideal', 'u_eq_ideal',
                 's_target', 'delta', 'sigma'):
      v = getattr(proxy, attr, None)
      if v is not None:
        try:
          d[attr] = float(v)
        except (TypeError, ValueError):
          pass
    return d

  def _serialise_constraints(self):
    """ The constraints, by type and description. component_annotations above
    already show how each parameter is reparametrised; this lists the objects
    that did it. """
    out = []
    for c in (self.constraints or []):
      out.append({'type': type(c).__name__, 'description': str(c)})
    return out

  def _serialise_scatterers(self):
    out = []
    xs = self.xray_structure()
    for sc in xs.scatterers():
      f = sc.flags
      out.append({
        'label': sc.label,
        'type': sc.scattering_type,
        'site': tuple(sc.site),
        'occupancy': sc.occupancy,
        'u_iso': sc.u_iso if f.use_u_iso() else None,
        'u_star': tuple(sc.u_star) if f.use_u_aniso() else None,
        'grad': {'site': f.grad_site(), 'u_iso': f.grad_u_iso(),
                 'u_aniso': f.grad_u_aniso(), 'occupancy': f.grad_occupancy()},
      })
    return out

  def _annotate_parameter_indices(self, message):
    """ Name the parameters any indices in a cctbx error message refer to.

    cctbx reports a failing parameter as a bare number -- a row of the normal
    matrix, e.g. "failure in index: 417" from a Cholesky decomposition -- which
    on its own says nothing about which atom is at fault. This finds those
    indices and names them through _independent_parameter_annotations.

    Returns a list of description strings, empty when the message carries no
    index or none of them is in range. Conservative on purpose: only indices
    written as "index: N" or "index N" are taken, since an arbitrary number in
    an error message is not a parameter and a confidently wrong atom name is
    worse than none.
    """
    import re
    try:
      annotations = self._independent_parameter_annotations()
    except Exception:
      return []
    out = []
    for match in re.finditer(r'index[:\s]+(\d+)', message, re.I):
      index = int(match.group(1))
      if 0 <= index < len(annotations):
        out.append("index %d is %s" % (index, annotations[index]))
      else:
        out.append("index %d is out of range (%d parameters), most likely a "
                   "scalar parameter such as the scale factor, an extinction "
                   "or a twin fraction" % (index, len(annotations)))
    return out

  def _independent_parameter_annotations(self):
    """ A name for each independent parameter -- each row of the normal matrix
    and the Cholesky decomposition -- as the crystallographic parameter it
    stands for.

    reparametrisation.component_annotations names the grad_Fc components (the
    scatterer parameters), of which there are more than there are independent
    parameters once constraints reduce the model. The mapping between the two is
    jacobian_transpose_matching_grad_fc, which here is a selection: each
    independent parameter picks out the one grad_Fc component it equals (weight
    1), and a handful of scalar parameters (scale, extinction, twin fractions,
    at the end) pick out none. A shared parameter picks out more than one, and
    those are joined. This is what turns a bare Cholesky index into 'HD1a_52.uiso'
    rather than a number.
    """
    # cached: the walk below is over every column of the jacobian, and both the
    # error message and the diagnostic dump ask for it
    cached = getattr(self, '_independent_annotations_cache', None)
    if cached is not None:
      return cached
    rp = self.reparametrisation
    component = list(rp.component_annotations)
    jt = rp.jacobian_transpose_matching_grad_fc()
    drives = [[] for _ in range(jt.n_rows)]
    for j in range(jt.n_cols):
      if j >= len(component):
        continue
      for i, v in jt.col(j):
        drives[i].append((v, component[j]))
    out = []
    for lst in drives:
      if not lst:
        out.append("scalar parameter")
        continue
      # The parameter the row equals has weight 1 (its identity in grad_Fc); the
      # rest are what it drives through a constraint. Weight, not magnitude,
      # tells them apart: a riding-U derivative carries a large metric factor, so
      # sorting by size would bury the identity behind it.
      identity = [n for w, n in lst if abs(abs(w) - 1.0) < 1e-4]
      driven = [n for w, n in lst if abs(abs(w) - 1.0) >= 1e-4]
      if identity:
        head, tail = identity[0], identity[1:] + driven
        out.append(head if not tail else "%s (with %s)" % (head, ", ".join(tail)))
      else:
        # no identity: a constraint parameter (e.g. a rotation) with no grad_Fc
        # component of its own, named by what it moves
        moved = [n for _, n in sorted(lst, key=lambda t: -abs(t[0]))]
        out.append("constraint parameter for %s" % ", ".join(moved))
    self._independent_annotations_cache = out
    return out

  def data_to_parameter_watch(self):
    parameters = self.reparametrisation.n_independents
    try:
      data = self.normal_eqns.r1_factor()[1]
    except:
      data = self.reflections.f_sq_obs_merged.size()
    OV.SetDataParamN(data, parameters)
    try:
      retVal = f"{self.normal_eqns.r1_factor()[1]} (all) | {self.normal_eqns.r1_factor(2)[1]} (I >= 2u(I)g) | {self.normal_eqns.r1_factor(5)[1]} (I >= 5u(I)) [hkl: {self.reflections.f_sq_obs_merged.size()}]"
      return retVal
    except:
     pass


  def print_table_header(self, log=None):
    if log is None: log = sys.stdout
    #restraints = self.normal_eqns.n_restraints
    #if not restraints:
      #restraints = "n/a"
    #print >>log, "Parameters: %s, Data: %s, Constraints: %s, Restraints: %s"\
     # %(self.normal_eqns.n_parameters, self.normal_eqns.observations.data.all()[0], self.n_constraints, restraints)
    ref_method = OV.GetParam("snum.refinement.method")
    header = "   Cycle      R1       wR_2      GooF          Shift/esd            Shift xyz               Shift U      "
    hr = "  -------  --------  --------  --------  --------------------  --------------------  --------------------"
    if ref_method == "Levenberg-Marquardt":
      header += "     Mu of LM      "
      hr +=   "  --------------"
    elif ref_method in FullMatrixRefine.scipy_methods:
      header += "  Evaluations "
      hr +=   "  ------------"
    elif ref_method == 'CGLS-J':
      header += "   CG iters   "
      hr +=   "  ------------"
    # Name the optimiser right above its own table, so that a log holding
    # several runs cannot leave it in doubt which one produced which. The
    # console has had this already, from the line naming the thread counts, so
    # only the log file needs it here.
    if log is not sys.stdout:
      if ref_method in FullMatrixRefine.scipy_methods:
        print("Optimiser: %s via scipy.optimize.minimize" % ref_method,
              file=log)
      elif ref_method == 'CGLS-J':
        print("Optimiser: conjugate gradient least squares. Shift/esd is "
              "approximated from the block diagonal during the run; the "
              "values reported at the end are from the full matrix.", file=log)
      else:
        print("Optimiser: %s" % ref_method, file=log)
    print(hr, file=log)
    print(header, file=log)
    print(hr, file=log)

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

  def calc_flack(self):
    self.flack_reflections_used = None
    if (not self.xray_structure().space_group().is_centric()
        and self.normal_eqns.observations.fo_sq.anomalous_flag()):
      if self.is_inversion_twin():
        if self.twin_components[0].grad:
          flack = self.twin_components[0].value
          su = math.sqrt(self.twin_covariance_matrix.matrix_packed_u_diagonal()[0])
          self.flack_reflections_used = self.normal_eqns.observations.fo_sq.size()
          return utils.format_float_with_standard_uncertainty(flack, su)
      flack_str = self._calc_flack_one_parameter_fixed_model()
      if flack_str is not None:
        return flack_str
      return "N/A"

  def _calc_flack_one_parameter_fixed_model(self):
    """
    Fixed-model one-parameter Flack solve with refinement OSF:
      I_model(h) = k * ((1-x) * I_calc(h) + x * I_calc(-h)),
    where k is the scale/OSF from the refinement. All model parameters stay
    fixed and only x is solved.
    """
    try:
      if self.xray_structure().space_group().is_centric():
        return None
      obs = self.normal_eqns.observations.fo_sq
      if not obs.anomalous_flag():
        return None

      fc_sq = self.normal_eqns.fc_sq.common_set(obs)
      obs = obs.common_set(fc_sq)
      weights = None
      try:
        weights = self.normal_eqns.weights.common_set(obs)
      except Exception:
        pass

      lt = miller.lookup_tensor(
        obs.indices(), obs.space_group(), obs.anomalous_flag())

      # Use the refinement scale (OSF) as fixed k in the one-parameter model.
      k = self.scale_factor
      if k is None:
        try:
          k = self.normal_eqns.scale_factor()
        except Exception:
          k = OV.GetOSF()
      if k is None or abs(k) < 1e-12:
        return None

      num = 0.0
      den = 0.0
      n_used = 0

      obs_data = obs.data()
      fc_data = fc_sq.data()
      if weights is not None:
        w_data = weights.data()
      else:
        sigmas = obs.sigmas()
        w_data = None if sigmas is None else flex.double([1.0/(s*s) if s > 0 else 0.0 for s in sigmas])

      for i, h in enumerate(obs.indices()):
        mate_i = lt.find_hkl((-h[0], -h[1], -h[2]))
        if mate_i < 0:
          continue
        a = float(fc_data[i])
        b = float(fc_data[mate_i])
        d = k * (b - a)
        if abs(d) < 1e-12:
          continue
        y = float(obs_data[i])
        if w_data is not None:
          w = float(w_data[i])
          if w <= 0:
            continue
        else:
          w = 1.0
        num += w * (y - k * a) * d
        den += w * d * d
        n_used += 1

      if den <= 0 or n_used < 10:
        return None

      x = num / den
      su = math.sqrt(1.0 / den)
      self.flack_reflections_used = n_used
      return utils.format_float_with_standard_uncertainty(x, su)
    except Exception:
      return None

  def check_hooft(self):
    if OV.IsEDData():
      return
    if (not self.xray_structure().space_group().is_centric()
        and self.normal_eqns.observations.fo_sq.anomalous_flag()):
      from cctbx_olex_adapter import hooft_analysis
      try:
        self.hooft = hooft_analysis(self)
        self.hooft_str = utils.format_float_with_standard_uncertainty(
          self.hooft.hooft_y, self.hooft.sigma_y)
      except Exception as e:
        self.hooft = None
        self.hooft_str = "N/A"
        if OV.IsDebugging():
          sys.stderr.formatExceptionInfo()
      # people still would want to see this...
      try:
        flack = self.calc_flack()
        if self.flack_reflections_used is not None:
          print("Flack reflections used: %s" % self.flack_reflections_used)
        OV.SetParam('snum.refinement.flack_str', flack)
      except Exception as e:
        print("Failed to evaluate Flack parameter")
        if OV.IsDebugging():
          sys.stderr.formatExceptionInfo()

  def get_radiation_type(self):
    radiation_type = self.olx_atoms.exptl.get("radiation_type", "xray")
    if radiation_type != "xray":
      return radiation_type
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
    types = list(unit_cell_content.keys())
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
    try: #TOF
      two_theta_full_set = uctbx.d_star_sq_as_two_theta(
        uctbx.d_as_d_star_sq(completeness_refs.d_max_min()[1]), self.wavelength, deg=True)
    except Exception as e:
      two_theta_full_set = 180
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

    # cell parameters and errors
    cell_params = self.olx_atoms.getCell()
    cell_errors = self.olx_atoms.getCellErrors()
    acta_stuff = olx.Ins('ACTA') != "n/a"
    xs = self.xray_structure()
    site_labels = xs.scatterers().extract_labels()
    if (not acta_stuff or self.objective_only
        or self.covariance_matrix_and_annotations is None):
      from iotbx.cif import model
      cif_block = model.block()
    else:
      from scitbx import matrix
      cell_vcv = flex.pow2(matrix.diag(cell_errors).as_flex_double_matrix())
      cif_block = xs.as_cif_block(
        format="coreCIF",
        covariance_matrix=self.covariance_matrix_and_annotations.matrix,
        cell_covariance_matrix=cell_vcv.matrix_symmetric_as_packed_u())
      # do not use change of basis!
      if '(' in cif_block['_space_group_name_Hall']:
        sg_sym = sgtbx.space_group_symbols(xs.space_group().type().lookup_symbol())
        cif_block['_space_group_name_Hall'] = sg_sym.hall()
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
      bond_h = olx.Ins('bond $h') == 'true'
      distances = iotbx.cif.geometry.distances_as_cif_loop(
        connectivity_full.pair_asu_table,
        site_labels=site_labels,
        sites_frac=xs.sites_frac(),
        covariance_matrix=self.covariance_matrix_and_annotations.matrix,
        cell_covariance_matrix=cell_vcv,
        parameter_map=xs.parameter_map(),
        include_bonds_to_hydrogen=bond_h,
        fixed_distances=self.reparametrisation.fixed_distances)
      angles = iotbx.cif.geometry.angles_as_cif_loop(
        connectivity_full.pair_asu_table,
        site_labels=site_labels,
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
      if len(confs):
        all_conf = None
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
        max_d = 1.9
        max_angle = 170
        if all_conf:
          if len(all_conf.args) > 0:
            max_d = all_conf.args[0]
          if len(all_conf.args) > 1:
            max_angle = all_conf.args[1]
        angles = crystal.calculate_dihedrals(
          pair_asu_table=connectivity_full.pair_asu_table,
          sites_frac=xs.sites_frac(),
          dihedral_defs=angle_defs,
          generate_all=all_conf is not None,
          covariance_matrix=self.covariance_matrix_and_annotations.matrix,
          cell_covariance_matrix=cell_vcv,
          parameter_map=xs.parameter_map(),
          conformer_indices=self.reparametrisation.connectivity_table.conformer_indices,
          max_d=max_d,
          max_angle=max_angle)
        space_group_info = sgtbx.space_group_info(group=xs.space_group())
        cif_dihedrals = iotbx.cif.geometry.dihedral_angles_as_cif_loop(
          angles,
          space_group_info=space_group_info,
          site_labels=site_labels,
          include_bonds_to_hydrogen=False)
        cif_block.add_loop(cif_dihedrals.loop)
      htabs = [i for i in self.olx_atoms.model['info_tables'] if i['type'] == 'HTAB']
      hbonds = []
      max_da_d = 0
      for htab in htabs:
        sites_frac = xs.sites_frac()
        atoms = htab['atoms']
        rt_mx = None
        site_d = sites_frac[atoms[0][0]]
        site_a = sites_frac[atoms[1][0]]
        if atoms[1][1] > -1:
          rt_mx = rt_mx_from_olx(equivs[atoms[1][1]])
          site_a = rt_mx * site_a
        da_d = xs.unit_cell().distance(site_d, site_a)
        if da_d > max_da_d:
          max_da_d = da_d
        hbonds.append(
          iotbx.cif.geometry.hbond(atoms[0][0], atoms[1][0], rt_mx=rt_mx))
      if len(hbonds):
        max_da_distance=float(OV.GetParam('snum.cif.htab_max_d'))
        if max_da_distance < max_da_d:
          olx.Echo("Overriding max D-A distance for reporting from %.2fA to %.2fA" %(max_da_distance, max_da_d), m="warning")
          max_da_distance = max_da_d
        min_dha_angle=float(OV.GetParam('snum.cif.htab_min_angle'))
        hbonds_loop = iotbx.cif.geometry.hbonds_as_cif_loop(
          hbonds,
          connectivity_full.pair_asu_table,
          site_labels=site_labels,
          sites_frac=sites_frac,
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
      cif_block['_chemical_formula_sum'] = olx.xf.GetFormula()
    cif_block['_chemical_formula_weight'] = olx.xf.GetMass()
    try:
      cif_block['_exptl_absorpt_coefficient_mu'] = olx.xf.GetMu()
    except:
      olx.Echo("Failed to compute IT/NIST mu", m="warning")
      cif_block['_exptl_absorpt_coefficient_mu'] = '?'
    cif_block['_exptl_crystal_density_diffrn'] = olx.xf.GetDensity()
    cif_block['_exptl_crystal_F_000'] = olx.xf.GetF000()

    write_fcf = False
    acta = olx.Ins("ACTA").strip()
    if OV.GetParam('user.cif.finalise') != 'Exclude' and not self.objective_only:
      if not acta:
        write_fcf = True
      elif acta != "n/a" and "NOHKL" not in acta.upper():
        write_fcf = True
    if write_fcf:
      #list_code = 8 if self.twin_components is not None and\
      #     not self.reparametrisation.fc_correction.grad else 4
      list_code = 4
      fcf_cif, fmt_str = self.create_fcf_content(list_code=list_code,
        add_weights=True, fixed_format=False)

      import io
      f = io.StringIO()
      fcf_cif.show(out=f,loop_format_strings={'_refln':fmt_str})
      cif_block['_iucr_refine_fcf_details'] = f.getvalue()

    fo2 = self.reflections.f_sq_obs
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

    cif_block['_diffrn_radiation_wavelength'] = "%.5f" %self.wavelength
    cif_block['_diffrn_radiation_type'] = self.get_radiation_type()
    if self.hklf_code == 5:
      cif_block['_diffrn_reflns_number'] = refinement_refs.size()
    else:
      cif_block['_diffrn_reflns_number'] = fo2.eliminate_sys_absent().size()

    merging = self.reflections.merging
    if self.hklf_code == 2:
      merging = self.get_hklf2_merging_stats()
      cif_block['_diffrn_reflns_av_R_equivalents'] = "%.4f" %merging.r_int()
      cif_block['_diffrn_reflns_av_unetI/netI'] = "%.4f" %merging.r_sigma()
    elif merging is not None:
      cif_block['_diffrn_reflns_av_R_equivalents'] = "%.4f" %merging.r_int()
      cif_block['_diffrn_reflns_av_unetI/netI'] = "%.4f" %merging.r_sigma()
    elif self.hklf_code == 5:
      if self.use_tsc:
        fo2, f_calc = self.get_fo_sq_fc(one_h_function=self.normal_eqns.one_h_linearisation)
      else:
        fo2, f_calc = self.get_fo_sq_fc()
      merging = fo2.merge_equivalents(algorithm="shelx")
      cif_block['_diffrn_reflns_av_R_equivalents'] = "?"
      cif_block['_diffrn_reflns_av_unetI/netI'] = "%.4f" %merging.r_sigma()

    cif_block['_diffrn_reflns_limit_h_min'] = h_min
    cif_block['_diffrn_reflns_limit_h_max'] = h_max
    cif_block['_diffrn_reflns_limit_k_min'] = k_min
    cif_block['_diffrn_reflns_limit_k_max'] = k_max
    cif_block['_diffrn_reflns_limit_l_min'] = l_min
    cif_block['_diffrn_reflns_limit_l_max'] = l_max
    cif_block['_diffrn_reflns_theta_min'] = "%.2f" %(
      0.5 * uctbx.d_star_sq_as_two_theta(min_d_star_sq, self.wavelength, deg=True))
    try:
      cif_block['_diffrn_reflns_theta_max'] = "%.2f" %(
        0.5 * uctbx.d_star_sq_as_two_theta(max_d_star_sq, self.wavelength, deg=True))
    except:
      cif_block['_diffrn_reflns_theta_max'] = 90
    cif_block['_diffrn_reflns_theta_full'] = fmt % (two_theta_full/2)
    #
    map_type = "potential" if OV.IsEDData() else "density"
    cif_block[f'_refine_diff_{map_type}_max'] = fmt % self.diff_stats.max()
    cif_block[f'_refine_diff_{map_type}_min'] = fmt % self.diff_stats.min()
    cif_block[f'_refine_diff_{map_type}_rms'] = fmt % math.sqrt(self.diff_stats.mean_sq())
    d_max, d_min = self.reflections.f_sq_obs_filtered.d_max_min()
    flack_str = OV.GetParam("snum.refinement.flack_str")
    if self.is_inversion_twin() and flack_str:
        cif_block['_refine_ls_abs_structure_details'] = \
                 'Refined as an inversion twin.'
        cif_block['_refine_ls_abs_structure_Flack'] = flack_str
    elif self.hooft is not None:
        cif_block['_refine_ls_abs_structure_details'] = \
                 'Hooft, R.W.W., Straver, L.H., Spek, A.L. (2010). J. Appl. Cryst., 43, 665-668.'
        cif_block['_refine_ls_abs_structure_Flack'] = self.hooft_str
    cif_block['_refine_ls_d_res_high'] = fmt % d_min
    cif_block['_refine_ls_d_res_low'] = fmt % d_max
    if self.reparametrisation.fc_correction.expression:
      cif_block['_refine_ls_extinction_expression'] = self.reparametrisation.fc_correction.expression
      if isinstance(self.reparametrisation.fc_correction, xray.shelx_extinction_correction):
        cif_block['_refine_ls_extinction_coef'] = olx.xf.rm.Exti()
      elif isinstance(self.reparametrisation.fc_correction, xray.shelx_SWAT_correction):
        cif_block['_refine_ls_extinction_coef'] = fmt % self.reparametrisation.fc_correction.g +\
           '' + fmt % self.reparametrisation.fc_correction.U
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
    if not self.objective_only:
      self.normal_eqns.analyse_shifts()
      cif_block['_refine_ls_shift/su_max'] = "%.4f" % self.normal_eqns.max_shift_esd
      cif_block['_refine_ls_shift/su_mean'] = "%.4f" % self.normal_eqns.mean_shift_esd
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
    use_aspherical = OV.IsNoSpherA2()

    ## Florian's new fcf iucr loop
    if OV.GetParam('user.refinement.refln_loop') == True:
      f_obs_sq, f_calc = self.get_fcf_data(False,False)
      weights = self.normal_eqns.weights
      f_sq_weight = f_obs_sq.array(data=weights*len(weights)*100/sum(weights))
      include_status = f_obs_sq.array(data=flex.std_string(f_calc.size(), 'o'))
      refln_loop = iotbx.cif.miller_arrays_as_cif_block(f_calc.as_intensity_array(), array_type='calc', format="coreCIF")
      refln_loop.add_miller_array(f_obs_sq, array_type='meas')
      refln_loop.add_miller_array(f_sq_weight, column_name='_refln_F_squared_weight')
      refln_loop.add_miller_array(f_obs_sq.f_sq_as_f(), array_type="meas")
      refln_loop.add_miller_array(f_calc, column_names=['_refln_A_calc','_refln_B_calc'])
      refln_loop.add_miller_array(f_calc, array_type='calc')

      if OV.GetParam('user.refinement.diagnostics'):
        write_diagnostics_stuff(f_calc)

      if OV.GetParam("snum.refinement.use_solvent_mask"):
        from cctbx_olex_adapter import OlexCctbxAdapter
        cctbx_adapter = OlexCctbxAdapter()
        f_mask = cctbx_adapter.load_mask()
        if not f_mask:
          from cctbx_olex_adapter import OlexCctbxMasks
          OlexCctbxMasks()
          if olx.current_mask.flood_fill.n_voids() > 0:
            f_mask = olx.current_mask.f_mask()
        if f_mask:
          if not f_obs_sq.space_group().is_centric() and f_obs_sq.anomalous_flag():
            f_mask = f_mask.generate_bijvoet_mates()
          f_mask = f_mask.common_set(f_obs_sq)
        refln_loop.add_miller_array(f_mask, column_names=['_refln_A_mask','_refln_B_mask'])
      refln_loop.add_miller_array(f_calc.d_spacings(), column_name="_refln_d_spacing")
      refln_loop.add_miller_array(include_status, column_name="_refln_observed_status")

      cif_block.add_loop(refln_loop.refln_loop)
      ## END Florian's new fcf iucr loop


    if self.use_tsc and use_aspherical == True:
      import aaff
      aaff.get_refinement_details(cif_block, acta_stuff)
    elif OV.IsEDRefinement():
      OV.GetACI().EDI.get_refinement_details(cif_block, acta_stuff)
    def sort_key(key, *args):
      if key.startswith('_space_group_symop') or key.startswith('_symmetry_equiv'):
        return "a"
      elif key.startswith('_atom_type'):
        return "b"
      elif key.startswith('_geom_bond'):
        return '_geom_0'
      elif key.startswith('_geom_angle'):
        return '_geom_1'
      elif key == "_iucr_refine_fcf_details":
        return "z"
      else:
        return key
    cif_block.sort(key=sort_key)
    return cif_block

  #moves EXTI from Fc_sq to Fo_sq and scales Fo_sq if requested
  def  transfer_exti(self, exti, wavelength, fo_sq, fc_sq, do_scale=True):
    #return fo_sq, fc_sq
    sin_2_theta = fc_sq.unit_cell().sin_two_theta(fc_sq.indices(), wavelength)
    correction = 0.001 * exti * fc_sq.data() * math.pow(wavelength, 3) / sin_2_theta
    # recover original Fc_sq
    fc_sq_original = fc_sq.data()*(correction + flex.pow(flex.pow(correction, 2) + 4, 0.5))/2
    #compute original correction to apply to Fo_sq
    correction = 0.001 * exti * fc_sq_original * math.pow(wavelength, 3) / sin_2_theta
    correction += 1
    correction = flex.pow(correction, 0.5)
    if do_scale:
      correction /= self.scale_factor
    # #test fc_sq = fc_sq_original/correction
    # test_v = fc_sq_original / correction
    # for i, fc_sq_v in enumerate(fc_sq.data()):
    #   if abs(fc_sq_v - test_v[i]) > 1e-8:
    #     raise Exception("Assert!")
    #   fc_m = fc_sq_original[i]*self.fc_correction.compute(
    #     wavelength, fc_sq.indices()[i], fc_sq_original[i], False)
    #   if abs(fc_sq_v - fc_m) > 1e-8:
    #     raise Exception("Assert!")
    # #end test
    fc_sq_ = fc_sq.customized_copy(data=fc_sq_original)
    fo_sq_ = fo_sq.customized_copy(
        data=fo_sq.data()*correction,
        sigmas=fo_sq.sigmas()*correction)
    return fo_sq_, fc_sq_

  #moves EXTI and scales from Fc_sq to Fo_sq
  def  transfer_exti_scale_hklf2(self, exti, wavelengths, fo_sq, fc_sq):
    if exti:
      uc = fc_sq.unit_cell()
      sin_t_sq = uc.d_star_sq(fc_sq.indices()) * flex.pow(wavelengths, 2) * 0.25
      sin_2t = 2*flex.pow(flex.abs(sin_t_sq*(1-sin_t_sq)), 0.5)
      correction = 0.001 * exti * fc_sq.data() * flex.pow(wavelengths, 3) / sin_2t
      # recover original Fc_sq
      fc_sq_original = fc_sq.data()*(correction + flex.pow(flex.pow(correction, 2) + 4, 0.5))/2
      #compute original correction to apply to Fo_sq
      correction = 0.001 * exti * fc_sq_original * flex.pow(wavelengths, 3) / sin_2t
      correction += 1
      correction = flex.pow(correction, 0.5)
      # #test fc_sq = fc_sq_original/correction
      # test_v = fc_sq_original / correction
      # for i, fc_sq_v in enumerate(fc_sq.data()):
      #   if abs(fc_sq_v - test_v[i]) > 1e-8:
      #     raise Exception("Assert!")
      #   fc_m = fc_sq_original[i]*self.fc_correction.compute(wavelengths[i],
      #     fc_sq.indices()[i], fc_sq_original[i], False)
      #   if abs(fc_sq_v - fc_m) > 1e-8:
      #     raise Exception("Assert!")
      # #end test
      fc_sq_ = fc_sq.customized_copy(data=fc_sq_original)
      data=fo_sq.data()*correction
      sigmas=fo_sq.sigmas()*correction

      if len(self.observations.measured_scale_indices) > 0:
        data = flex.double([I / self.observations.scale(i) for i, I in enumerate(data)])
        sigmas = flex.double([s / self.observations.scale(i) for i, s in enumerate(sigmas)])

      fo_sq_ = fo_sq.customized_copy(data=data, sigmas=sigmas)

    elif len(self.observations.measured_scale_indices) > 0:
      fc_sq_ = fc_sq
      data = flex.double([I / self.observations.scale(i) for i, I in enumerate(fo_sq.data())])
      sigmas = flex.double([s / self.observations.scale(i) for i, s in enumerate(fo_sq.sigmas())])
      fo_sq_ = fo_sq.customized_copy(data=data, sigmas=sigmas)

    return fo_sq_, fc_sq_

  #moves SWAT from Fc_sq to Fo_sq
  def  transfer_swat(self, g, U, fo_sq, fc_sq):
    #stol_sqs = fc_sq.unit_cell().stol_sq(fc_sq.indices())
    #correction = flex.double([1 - g*math.exp(-8*math.pi**2*U*stol_sq) for stol_sq in stol_sqs])
    #correction = flex.pow(correction, 2.0)
    correction = flex.double([self.fc_correction.compute(h, 0, False) for h in fc_sq.indices()])
    # # #test
    # for i, fc_sq_v in enumerate(fc_sq.data()):
    #   fc_k =self.fc_correction.compute(fc_sq.indices()[i], 0, False)
    #   if abs(correction[i] - fc_k) > 1e-3:
    #     raise Exception("Assert!")
    # # #end test
    fc_sq_ = fc_sq.customized_copy(data=fc_sq.data() / correction)
    fo_sq_ = fo_sq.customized_copy(
        data=fo_sq.data()/correction,
        sigmas=fo_sq.sigmas()/correction)
    return fo_sq_, fc_sq_

  # complete_detwin also DISABLES MASK
  def get_fcf_data(self, anomalous_flag, use_fc_sq=False, complete_detwin=False):
    if self.hklf_code == 5 or\
      (self.twin_components and (not self.is_inversion_twin() or complete_detwin)):
      merge = self.hklf_code < 5
      if self.use_tsc:
        fo_sq, fc = self.get_fo_sq_fc(one_h_function=self.normal_eqns.one_h_linearisation,
          merge=merge, complete=complete_detwin)
      else:
        fo_sq, fc = self.get_fo_sq_fc(merge=merge, complete=complete_detwin)
      if self.f_mask and not complete_detwin:
        f_mask = self.f_mask.expand_to_p1()
        f_mask = f_mask.common_set(fc)
        fc = fc.array(data=fc.data()+f_mask.data())
      fo_sq = fo_sq.customized_copy(
        data=fo_sq.data()*(1/self.scale_factor),
        sigmas=fo_sq.sigmas()*(1/self.scale_factor),
        anomalous_flag=anomalous_flag)
      if use_fc_sq:
        fc = fc.as_intensity_array()
      return fo_sq, fc
    else:
      if use_fc_sq:
        fc = self.normal_eqns.fc_sq.customized_copy(anomalous_flag=anomalous_flag)
      else:
        fc = self.normal_eqns.f_calc.customized_copy(anomalous_flag=anomalous_flag)
      fo_sq = self.normal_eqns.observations.fo_sq.customized_copy(
        data=self.normal_eqns.observations.fo_sq.data()*(1/self.scale_factor),
        sigmas=self.normal_eqns.observations.fo_sq.sigmas()*(1/self.scale_factor),
        anomalous_flag=anomalous_flag)
      fc = fc.sort(by_value="packed_indices")
      fo_sq = fo_sq.sort(by_value="packed_indices")
      return fo_sq, fc

  def create_fcf_content(self, list_code, add_weights=False, fixed_format=True):
    anomalous_flag = list_code < 0 and not self.xray_structure().space_group().is_centric()
    list_code = abs(list_code)
    # list 4 data should match the refinement - not detwinned set!!
    if list_code == 4:
      weights = self.normal_eqns.weights
      fc_sq = self.normal_eqns.fc_sq
      fo_sq = self.normal_eqns.observations.fo_sq
      if (self.exti is not None or self.swat is not None) and\
          type(self.fc_correction) is not xray.dummy_fc_correction:
        if self.exti is not None:
          if self.hklf_code == 2:
            fo_sq, fc_sq = self.transfer_exti_scale_hklf2(
              self.fc_correction.value, self.normal_eqns.observations.wavelengths,
                fo_sq, fc_sq)
          else:
            fo_sq, fc_sq = self.transfer_exti(
              self.fc_correction.value, self.wavelength, fo_sq, fc_sq,
              do_scale=False)
        # elif self.swat is not None: # swat should not be transferred...
        #   #fo_sq, fc_sq = self.transfer_swat(self.swat[0], self.swat[1], fo_sq, fc_sq)
        #   pass
        weights = self.compute_weights(fo_sq, fc=fc_sq.as_amplitude_array(), reset_scale_factor=True)
        scale = flex.sum(weights * fo_sq.data() *fc_sq.data()) \
            / flex.sum(weights * flex.pow2(fc_sq.data()))

        fo_sq = self.normal_eqns.observations.fo_sq.customized_copy(
          data=fo_sq.data()*(1/scale),
          sigmas=fo_sq.sigmas()*(1/scale),
          anomalous_flag=anomalous_flag)
      else:
        fo_sq = self.normal_eqns.observations.fo_sq.customized_copy(
          data=fo_sq.data()*(1/self.scale_factor),
          sigmas=fo_sq.sigmas()*(1/self.scale_factor),
          anomalous_flag=anomalous_flag)

      mas_as_cif_block = iotbx.cif.miller_arrays_as_cif_block(
        fc_sq, array_type='calc', format="coreCIF")
      mas_as_cif_block.add_miller_array(fo_sq, array_type='meas')

      if add_weights:
        if weights is None:
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
      if OV.IsEDRefinement():
        fmt_str = fmt_str.replace("f", "g")
      _refln_include_status = fc_sq.array(data=flex.std_string(fc_sq.size(), 'o'))
      mas_as_cif_block.add_miller_array(
        _refln_include_status, column_name='_refln_observed_status') # checkCIF only accepts this one

    elif list_code == 3:
      fo_sq, fc = self.get_fcf_data(anomalous_flag)
      fo = fo_sq.as_amplitude_array().sort(by_value="packed_indices")
      if fo_sq.space_group().is_origin_centric():
        for i in range(0, fc.size()):
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
      fo_sq, fc = self.get_fcf_data(anomalous_flag)
      mas_as_cif_block = iotbx.cif.miller_arrays_as_cif_block(
        fo_sq, column_names=['_refln_F_squared_meas', '_refln_F_squared_sigma'],
        format="coreCIF")
      mas_as_cif_block.add_miller_array(
        fc, column_names=['_refln_F_calc', '_refln_phase_calc'])
      fmt_str = "%i %i %i %.3f %.3f %.3f %.3f"
    elif list_code == 8:
      olx.Echo("Warning: experimental LIST 8", m="warning")
      fo_sq, fc = self.get_fcf_data(anomalous_flag, complete_detwin=True)
      #fc = fc.customized_copy(data=fc.data()*self.scale_factor**0.5)
      mas_as_cif_block = iotbx.cif.miller_arrays_as_cif_block(
        fo_sq, column_names=['_refln_F_squared_meas', '_refln_F_squared_sigma'],
        format="coreCIF")
      mas_as_cif_block.add_miller_array(
        fc, column_names=['_refln_F_squared_calc', '_refln_phase_calc'])
      weights = self.compute_weights(fo_sq, fc)
      _refln_weight = fc.array(data=weights*len(weights)*100/sum(weights))
      mas_as_cif_block.add_miller_array(
        fc.d_spacings(), column_name='_refln_d_spacing')
      mas_as_cif_block.add_miller_array(
        _refln_weight, column_name='_shelx_refinement_sigma')
      fmt_str = "%i %i %i %.3f %.3f %.3f %.3f %.3f %.3f"
    else:
      print("LIST code %i not supported" %list_code)
      return None, None
    # cctbx could make e.g. 1.001(1) become 1.0010(10), so use Olex2 values for cell

    cif = iotbx.cif.model.cif()
    cif_block = iotbx.cif.model.block()
    cif_block['_computing_structure_refinement'] = OV.get_refienment_program_refrerence()
    cif_block['_shelx_refln_list_code'] = list_code
    cif_block.update(mas_as_cif_block.cif_block)

    cif_block['_cell_length_a'] = olx.xf.uc.CellEx('a')
    cif_block['_cell_length_b'] = olx.xf.uc.CellEx('b')
    cif_block['_cell_length_c'] = olx.xf.uc.CellEx('c')
    cif_block['_cell_angle_alpha'] = olx.xf.uc.CellEx('alpha')
    cif_block['_cell_angle_beta'] = olx.xf.uc.CellEx('beta')
    cif_block['_cell_angle_gamma'] = olx.xf.uc.CellEx('gamma')
    cif_block['_cell_volume'] = olx.xf.uc.VolumeEx()
    #cif_block['_shelx_F_squared_multiplier'] = "%.3f" %(multiplier)
    dn = OV.GetParam("snum.cif.dataname", None)
    if not dn:
      dn = OV.FileName().replace(' ', '')
    cif[dn] = cif_block

    return cif, fmt_str

  def output_fcf(self, fcf_l4_content=None):
    try: list_code = int(olx.Ins('list'))
    except: return
    if OV.IsEDRefinement() and list_code != 4:
      olx.Echo("Only LIST 4 is currently supported for the ED refinement", m="warning")
      return
    if fcf_l4_content and list_code == 4:
      fcf_content = fcf_l4_content
    else:
      import io
      f = io.StringIO()
      fcf_cif, fmt_str = self.create_fcf_content(list_code, fixed_format=False)
      if not fcf_cif:
        print("Unsupported list (FCF) format")
        return
      fcf_cif.show(out=f, loop_format_strings={'_refln':fmt_str})
      fcf_content = f.getvalue()
    with open(OV.file_ChangeExt(OV.FileFull(), 'fcf'), 'w') as f:
      f.write(fcf_content)

  def setup_shared_parameters_constraints(self):
    shared_adps = {}
    shared_sites = {}
    constraints = []
    sump_proxies = None
    constraints_itr = self.olx_atoms.constraints_iterator()
    for constraint_type, kwds in constraints_itr:
      i_seqs = kwds["i_seqs"]
      if constraint_type == "adp":
        skip = False
        for i in i_seqs[1:]:
          if i_seqs[0] in shared_adps:
            skip = True
            break
          shared_adps[i] = i_seqs[0]
        if skip:
          print("Cyclic U constraint located for: %s" \
            %(self.olx_atoms.atoms()[i_seqs[0]]['label'],))
          continue
      elif constraint_type == "site":
        skip = False
        for i in i_seqs[1:]:
          if i_seqs[0] in shared_sites:
            skip = True
            break
          shared_sites[i] = i_seqs[0]
        if skip:
          print("Cyclic site constraint located for: %s" \
            %(self.olx_atoms.atoms()[i_seqs[0]]['label'],))
          continue
    # merge constrains, adp
    reverse_map = {}
    for k,v in shared_adps.items():
      if v not in reverse_map:
        reverse_map[v] = set()
      reverse_map[v].add(k)
    for k,v in reverse_map.items():
      current = adp.shared_u([k] + list(v))
      constraints.append(current)
    # site
    reverse_map = {}
    for k,v in shared_sites.items():
      if v not in reverse_map:
        reverse_map[v] = set()
      reverse_map[v].add(k)
    for k,v in reverse_map.items():
      current = site.shared_site([k] + list(v))
      constraints.append(current)

    directions = self.olx_atoms.model.get('olex2.direction', ())
    self.directions = [d for d in directions]

    shared_rotated_adp = self.olx_atoms.model.get('olex2.constraint.rotated_adp', ())
    self.shared_rotated_adps = []
    for c in shared_rotated_adp:
      current = adp.shared_rotated_u(c[0], c[1], c[2], c[3], c[4])
      constraints.append(current)
      self.shared_rotated_adps.append(current)

    shared_rotating_adp = self.olx_atoms.model.get('olex2.constraint.rotating_adp', ())
    self.shared_rotating_adps = []
    for c in shared_rotating_adp:
      current = adp.shared_rotating_u(*c)
      constraints.append(current)
      self.shared_rotating_adps.append(current)

    self.shared_param_constraints = []
    scatterers = self.xray_structure().scatterers()
    vars = self.olx_atoms.model['variables']['variables']
    equations = self.olx_atoms.model['variables']['equations']
    fix_occupancy_for = []

    dependent_occu = {}
    #dependent_occupancy will refine only the occupancy of the first scatterer
    for i, var in enumerate(vars):
      refs = var['references']
      as_var = []
      as_var_minus_one = []
      eadp = []
      for ref in refs:
        if ref['index'] == 4 and 'var' in ref['relation']:
          id, k = ref['id'], ref['k']
          k /= scatterers[id].weight_without_occupancy()
          if ref['relation'] == "var":
            as_var.append((id, k))
          elif ref['relation'] == "one_minus_var":
            as_var_minus_one.append((id, k))
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
          dependent_occu[as_var[0][0]] = current
          is_as_var = True
        else:
          scale = as_var_minus_one[0][1]
          dependent_occu[as_var_minus_one[0][0]] = current
          is_as_var = False
        self.shared_param_constraints.append((i, current, 1./scale, is_as_var))
      elif len(eadp) > 1:
        current = adp.shared_u(eadp)
        constraints.append(current)
        self.shared_param_constraints.append((i, current, 1, True))

    if(len(equations)>0):
      from cctbx import other_restraints
      sump_proxies = other_restraints.shared_sump_proxy()
      for equation in equations:
        i_seqs, coefficients = [], []
        labels, all_i_seqs, group_sizes = [], [], []
        for variable in equation['variables']:
          id_found = False
          group_size = 0
          for r in variable[0]['references']:
            if(ref['index'] != 4): #occupancy
              continue
            group_size += 1
            sc_id = r['id']
            all_i_seqs.append(sc_id)
            if not id_found and sc_id in dependent_occu:
              ref = r
              id_found = True
          if not group_size:  continue
          group_sizes.append(group_size)
          labels.append("Var_%s" %(vars.index(variable[0])+1))
          if not id_found:
            ref = variable[0]['references'][-1]
          sc_id = ref['id']
          i_seqs.append(sc_id)
          k = variable[1]*scatterers[sc_id].weight_without_occupancy()/\
            ref['k']
          coefficients.append(k)
        weight = 1/math.pow(equation['sigma'],2)
        p = other_restraints.sump_proxy(i_seqs, coefficients, weight, equation['value'],
                                        labels, all_i_seqs, group_sizes)
        sump_proxies.append(p)
      if 'constraint' == OV.GetParam('snum.smtbx.sump'):
        FvarNum = len(vars)
        idslist = []
        # Building matrix of equations
        lineareq = numpy.zeros((0,FvarNum))
        rowheader = {}
        nextfree = -1
        for proxy in sump_proxies:
          row = numpy.zeros((FvarNum))
          for i, i_seq in enumerate(proxy.i_seqs):
            if(i_seq not in rowheader):
              nextfree+=1
              rowheader[i_seq]=nextfree
              idslist.append(i_seq)
              key=nextfree
            else:
              key=rowheader[i_seq]
            row[key]=proxy.coefficients[i]
          row[FvarNum-1]=proxy.target
          lineareq=numpy.append(lineareq, [row], axis=0)
        sump_proxies = None
        # LU decomposition to find incompatible or redundant constraints
        l,u = scipy.linalg.lu(lineareq, permute_l=True)

        if numpy.shape(u)[0] > 1:
          previous = u[-2,:]
          for row in numpy.flipud(u):
            if((numpy.all(row[0:-1]==0.0) and row[-1]!=0) or\
              (numpy.all(row[0:-1]==previous[0:-1]) and row[-1]!=previous[-1])):
              raise Exception("One or more equations are not independent")
            previous = row

        # setting up constraints
        for row in numpy.flipud(u):
          nn_cnt = 0
          nn_idx = -1
          a = numpy.copy(row[:-1])
          for idx, v in enumerate(a):
            if v != 0.0:
              nn_cnt+=1
              nn_idx = idx
          if(nn_cnt == 0):
            raise Exception("One or more equations are not independent")
          else:
            if nn_cnt == 1: # reduced
              fix_occupancy_for.append((idslist[nn_idx], row[-1]/a[nn_idx]))
            else:
              current = occupancy.occupancy_affine_constraint(idslist, a, row[-1])
              constraints.append(current)
              #sort order of creation
              if idslist[0] in dependent_occu:
                dep_occu = dependent_occu[idslist[0]]
                constraints.remove(dep_occu)
                constraints.append(dep_occu)

    same_groups = self.olx_atoms.model.get('olex2.constraint.same_group', ())
    for sg in same_groups:
      constraints.append(rigid.same_group(sg))
    same_disp = self.olx_atoms.model.get('olex2.constraint.same_disp', ())
    for sd in same_disp:
      constraints.append(fpfdp.shared_fp(sd))
      constraints.append(fpfdp.shared_fdp(sd))
    return constraints, fix_occupancy_for, sump_proxies

  def fix_rigid_group_params(self, pivot_neighbour, pivot, group, sizable):
    ##fix angles
    if pivot_neighbour is not None:
      for a in group:
        self.fixed_angles.setdefault((pivot_neighbour, pivot, a), 1)

    if pivot is not None:
      for i, a in enumerate(group):
        for j in range(i + 1, len(group)):
          self.fixed_angles.setdefault((a, pivot, group[j]), 1)

    for a in group:
      ns = self.olx_atoms._atoms[a]['neighbours']
      for i, b in enumerate(ns):
        if b not in group: continue
        for j in range(i+1, len(ns)):
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
    output_afix = []
    output_rigid = []
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
      if not (m == 0 or m in rigid_body): continue
      valid = True
      if not scatterers[pivot].flags.grad_site():
        valid = False
      if valid:
        # check for fixed coordinates
        for i_sc in dependent:
          sc = scatterers[i_sc]
          if not sc.flags.grad_site():
            valid = False
            break
      if not valid:
        if not output_afix:
          output_afix.append("Skipping conflicting AFIX for: ")
        output_afix.append(f"{scatterers[pivot].label} ")
        #print("Skipping conflicting AFIX for %s (refinement.py)" %scatterers[pivot].label)
        continue

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

      current = None
      if n in(6, 9):
        current = rigid.rigid_rotatable_expandable_group(
          pivot, dependent, n == 9, True)
      elif n in (3,4,7,8):
        if n in (3,4):
          current = rigid.rigid_riding_expandable_group(
            pivot, dependent, n == 4)
        elif len(pivot_neighbours) < 1:
          if not output_rigid:
            output_rigid.append("Invalid rigid group for: ")
          output_rigid.append(f"{scatterers[pivot].label} ")
          #print("Invalid rigid group for " + scatterers[pivot].label)
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
    if output_afix:
      print(f"{' '.join(output_afix)}")
    if output_rigid:
      print(f"{' '.join(output_rigid)}")

    return rigid_body_constraints

  def setup_geometrical_constraints(self, afix_iter=None):
    output_afix = []
    geometrical_constraints = []
    constraints = {
      # AFIX mn :
      # m:    type                                    , max # of pivot neigbours
      1:  ("tertiary_xh_site"                        , 3),
      2:  ("secondary_xh2_sites"                     , 2),
      3:  ("staggered_terminal_tetrahedral_xh3_sites", 1),
      4:  ("secondary_planar_xh_site"                , 2),
      8:  ("staggered_terminal_tetrahedral_xh_site"  , 1),
      9:  ("terminal_planar_xh2_sites"               , 1),
      12: ("terminal_tetrahedral_xh6_sites"          , 1),
      13: ("terminal_tetrahedral_xh3_sites"          , 1),
      14: ("terminal_tetrahedral_xh_site"            , 1),
      15: ("polyhedral_bh_site"                      , 5),
      16: ("terminal_linear_ch_site"                 , 1),
    }
    scatterers = self.xray_structure().scatterers()
    for m, n, pivot, dependent, pivot_neighbours, bond_length in afix_iter:
      if len(dependent) == 0: continue
      info = constraints.get(m)
      if info is not None:
        constraint_name = info[0]
        constraint_type = getattr(
          geometrical.hydrogens, constraint_name)
        rotating = n in (7, 8)
        stretching = n in (4, 8)
        valid = True
        if not scatterers[pivot].flags.grad_site() and n not in(4, 7, 8):
          valid = False
        if valid:
          # check for fixed coordinates
          for i_sc in dependent:
            sc = scatterers[i_sc]
            if not sc.flags.grad_site():
              valid = False
              break
        if not valid:
          if not output_afix:
            output_afix.append("Skipping conflicting AFIX for: ")
          output_afix.append(f"{scatterers[pivot].label} ")
          #print("Skipping conflicting AFIX for %s" %scatterers[pivot].label)
          continue
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
          current, self.olx_atoms.atoms(), info[1]).add_to
        geometrical_constraints.append(current)

    if output_afix:
      print(f"{' '.join(output_afix)}")

    return geometrical_constraints

  def export_var_covar(self, matrix):
    with open(os.path.join(OV.FilePath(),OV.FileName()+".npy"), "wb") as wFile:
      wFile.write(b"VCOV\n")
      wFile.write((" ".join(matrix.annotations) + "\n").encode())
      numpy.save(wFile, matrix.matrix.as_numpy_array())

  def f_obs_minus_f_calc_map(self, resolution):
    scale_factor = self.scale_factor
    k = OV.GetOSF() if scale_factor is None else math.sqrt(scale_factor)
    fo2 = self.normal_eqns.observations.fo_sq
    f_calc = self.normal_eqns.f_calc
    detwin = self.twin_components is not None\
        and self.twin_components[0].twin_law != sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1))
    rescale = False
    if detwin or self.hklf_code == 5:
      if self.use_tsc:
        fo2, f_calc = self.get_fo_sq_fc(one_h_function=self.normal_eqns.one_h_linearisation,
                                        complete=False)
      else:
        fo2, f_calc = self.get_fo_sq_fc(complete=False)
      if self.hklf_code == 5:
        fo2 = fo2.customized_copy(space_group_info=sgtbx.space_group_info(self.space_group))
        fo2 = fo2.merge_equivalents(algorithm="shelx").array().map_to_asu()
        f_calc = f_calc.customized_copy(crystal_symmetry=fo2.crystal_symmetry())
        f_calc = f_calc.common_set(fo2)
        if self.f_mask:
          f_mask = self.f_mask.common_set(f_calc)
          f_calc = f_calc.array(data=f_calc.data()+f_mask.data())
        rescale = True
    elif self.hklf_code == 2:
      fo2, fc_sq = self.transfer_exti_scale_hklf2(
        None if not self.fc_correction.grad else self.fc_correction.value,
        self.normal_eqns.observations.wavelengths,
        self.normal_eqns.observations.fo_sq,
        self.normal_eqns.f_calc.as_intensity_array())
      fo2 = fo2.customized_copy(space_group_info=sgtbx.space_group_info(self.space_group))
      fo2 = fo2.merge_equivalents(algorithm="shelx").array().map_to_asu()
      f_calc = self.f_calc(fo2, apply_extinction_correction=False, twin_data=False)
      rescale = True
    if rescale:
      fc_sq = f_calc.as_intensity_array()
      weights = self.compute_weights(fo2, f_calc, fc2_data=fc_sq.data(), reset_scale_factor=True)
      scale = flex.sum(weights * fo2.data() * fc_sq.data()) \
              / flex.sum(weights * flex.pow2(fc_sq.data()))
      k = scale ** 0.5
    #https://www.science.org/doi/suppl/10.1126/science.aak9652/suppl_file/aak9652-palatinus-sm.pdf, p7
    if OV.IsEDRefinement():
      fo2 = fo2.merge_equivalents(algorithm="shelx").array().map_to_asu()
      f_obs = fo2.f_sq_as_f()
      # scale Fc back from Ug
      f_calc = f_calc.map_to_asu().common_set(f_obs)
      f_calc =  f_calc.customized_copy(data=f_calc.data()/OV.GetACI().EDI.get_Fc2Ug())
      f_calc_sq = f_calc.as_intensity_array()

      new_data = []
      #merge the dynamic intensities and match to f_obs
      dyn_I = self.normal_eqns.fc_sq.merge_equivalents(algorithm="shelx")\
        .array().map_to_asu().common_set(f_obs)
      for i in range(f_obs.size()):
        mfc = math.sqrt(dyn_I.data()[i])
        if mfc == 0:
          s = 1
        else:
          s = abs(f_calc.data()[i])/mfc
        fo = f_obs.data()[i] * s
        new_data.append(fo)
      f_obs = f_obs.customized_copy(data=flex.double(new_data))
      fo2 = f_obs.as_intensity_array()

      weights = self.compute_weights(fo2, f_calc, fc2_data=f_calc_sq.data(), reset_scale_factor=True)
      scale = flex.sum(weights * fo2.data() * f_calc_sq.data()) \
              / flex.sum(weights * flex.pow2(f_calc_sq.data()))
      f_obs_minus_f_calc = f_obs.f_obs_minus_f_calc(1. / scale**0.5, f_calc)
    else: # non-ED
      f_obs = fo2.f_sq_as_f()
      f_obs_minus_f_calc = f_obs.f_obs_minus_f_calc(1. / k, f_calc)

    if OV.IsEDData():
      #https://journals.iucr.org/a/issues/2020/01/00/ae5072/index.html
      scaling_factor = 3.324943664 # scales from A-2 to eA-1
      f_obs_minus_f_calc = f_obs_minus_f_calc.apply_scaling(factor=scaling_factor)
    if debug:
      print("%d Reflections for Fourier Analysis" % f_obs_minus_f_calc.size())
    temp = f_obs_minus_f_calc.fft_map(
      symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
      resolution_factor=1,
      grid_step=resolution,
    )
    if debug:
      print(f"Size of Fourier grid: {temp.n_real()[0]:d} x {temp.n_real()[1]:d} x {temp.n_real()[2]:d}")
    return temp

  def post_peaks(self, fft_map, max_peaks=5):

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
    parameters=maptbx.peak_search_parameters(
      peak_search_level=3,
      interpolate=False,
      peak_cutoff=-1,
      min_distance_sym_equiv=1.0,
      max_clusters=max_peaks+len(self.xray_structure().scatterers()))
    peaks = fft_map.peak_search(parameters=parameters,verify_symmetry=False).all()
    fmap = olx.Ins("FMAP")
    if fmap.startswith('-'):
      peaks.p_sites = [s for s in peaks.sites()]
      peaks.p_heights = [p for p in peaks.heights()]

      fft_map = fft_map.apply_scaling(-1)
      n_peaks = fft_map.peak_search(parameters=parameters,verify_symmetry=False).all()
      peaks.p_sites += n_peaks.sites()
      peaks.p_heights += [-x for x in n_peaks.heights()]
      peaks.p_sites, peaks.p_heights = zip(*sorted(zip(peaks.p_sites, peaks.p_heights), key=lambda x: -abs(x[1])))
    else:
      peaks.p_sites = peaks.sites()
      peaks.p_heights = peaks.heights()
    i = 0
    olx.Kill('$Q', au=True) #HP-JUL18 -- Why kill the peaks? -- cause otherwise they accumulate! #HP4/9/18
    for xyz, height in zip(peaks.p_sites, peaks.p_heights):
      if i < 3:
        a = olx.xf.uc.Closest(*xyz).split(',')
        if OV.IsEDData():
          pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A, %.3f A away from %s" % (
            i + 1, xyz[0], xyz[1], xyz[2], height, float(a[1]), a[0])
        else:
          pi = "Peak %s = (%.3f, %.3f, %.3f), Height = %.3f e/A^3, %.3f A away from %s" % (
            i + 1, xyz[0], xyz[1], xyz[2], height, float(a[1]), a[0])
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
    _ = self.cycles.n_iterations
    plural = "S"
    if _ == 1:
      plural = ""

    if log is None: log = sys.stdout

    last = OV.GetParam('snum.refinement.last_R1')
    try:
      last =  f"{last:.4f}"
    except:
      last = last
    print_l = []
    pad = 2 - len(str(self.cycles.n_iterations))
    print_l.append(f"  ++++++++++++++++++++++++++++++++++++++++++++++++{pad*'+'}++++++ After {self.cycles.n_iterations} CYCLE{plural} +++")
    print_l.append(f"  +  R1:       {self.r1[0]:.4f} for {self.r1[1]} reflections I >= 2u(I). Last R1: {last}")
    print_l.append("  +  R1 (all): %.4f for %i reflections" %self.r1_all_data)
    print_l.append("  +  wR2:      %.4f, GooF:  %.4f" % (
      self.normal_eqns.wR2(),
      self.normal_eqns.goof()
    ))

    # The solvers describe themselves; for the scipy ones that includes which
    # minimiser was used, how many evaluations of the objective it took and,
    # if it did not simply converge, what stopped it.
    optimiser = str(self.cycles)
    n_evaluations = getattr(self.cycles, 'n_evaluations', None)
    if n_evaluations is not None:
      optimiser += ", %i evaluations" % n_evaluations
    stop_reason = getattr(self.cycles, 'stop_reason', None)
    if stop_reason:
      optimiser += ", stopped because %s" % stop_reason
    # "Method:   " keeps the value in the same column as the rows around it
    print_l.append("  +  Method:   %s" % optimiser)

    print_l.append("  +  Diff:     max=%.2f, min=%.2f, RMS=%.2f" % (
      self.diff_stats.max(),
      self.diff_stats.min(),
      self.diff_stats.sigma()
    ))

    if(self.cycles.n_iterations>0):
      max_shift_site = self.normal_eqns.max_shift_site()
      max_shift_u = self.normal_eqns.max_shift_u()
      max_shift_esd = self.normal_eqns.max_shift_esd
      max_shift_esd_item = self.normal_eqns.max_shift_esd_item
      print_l.append("  +  Shifts:   xyz: %.4f for %s, U: %.4f for %s, Max/esd = %.4f for %s" %(
        max_shift_site[0],
        max_shift_site[1].label,
        max_shift_u[0],
        max_shift_u[1].label,
        max_shift_esd,
        max_shift_esd_item
        ))
    else:
      shifts = ["n/a", "n/a"]
      if not self.objective_only:
        self.normal_eqns.analyse_shifts()
        max_shift_esd = self.normal_eqns.max_shift_esd
        shifts = ["%.4f" %self.normal_eqns.max_shift_esd,
                  self.normal_eqns.max_shift_esd_item]
      print_l.append("  +  Shifts:   Max/esd = %s for %s" %(
        shifts[0],shifts[1]))
    print_l.append(f"  +  Data:     {self.data_to_parameter_watch()}")
    pad = 9 - len(str(self.n_constraints)) - len(str(self.normal_eqns.n_restraints))\
      - len(str(self.normal_eqns.n_parameters))
    n_restraints = self.normal_eqns.n_restraints +\
      len(self.normal_eqns.origin_fixing_restraint.singular_directions)
    print_l.append(f"  ++++++++++++ {self.n_constraints} Constraints | {n_restraints} Restraints | {self.normal_eqns.n_parameters} Parameters +++++++++++++{'+'*pad}")
    print('\n'.join(print_l), file=log)

    if not self.objective_only:
      OV.SetParam("snum.refinement.max_shift_over_esd", max_shift_esd)
    else:
      OV.SetParam("snum.refinement.max_shift_over_esd", None)
    OV.SetParam('snum.refinement.max_peak', self.diff_stats.max())
    OV.SetParam('snum.refinement.max_hole', self.diff_stats.min())
    OV.SetParam('snum.refinement.res_rms', self.diff_stats.sigma())
    OV.SetParam('snum.refinement.goof', "%.4f" %self.normal_eqns.goof())

  def get_disagreeable_reflections(self, show_in_console=False):
    fo2 = self.normal_eqns.observations.fo_sq\
      .customized_copy(sigmas=flex.sqrt(1/self.normal_eqns.weights))\
      .apply_scaling(factor=1/self.normal_eqns.scale_factor())

    if show_in_console:
      result = fo2.show_disagreeable_reflections(self.normal_eqns.fc_sq, out=sys.stdout)
    else:
      result = fo2.disagreeable_reflections(self.normal_eqns.fc_sq)

    bad_refs = []
    for i in range(result.fo_sq.size()):
      sig = math.fabs(
        result.fo_sq.data()[i]-result.fc_sq.data()[i])/result.delta_f_sq_over_sigma[i]
      bad_refs.append((
        result.indices[i][0], result.indices[i][1], result.indices[i][2],
        result.fo_sq.data()[i], result.fc_sq.data()[i], sig))
    olex_core.SetBadReflections(bad_refs.__iter__(), not OV.IsEDRefinement())

  def show_comprehensive_summary(self, log=None):
    if log is None: log = sys.stdout
    self.show_summary(log)
    if not self.objective_only:
      # twin_covariance_matrix is None when no uncertainties were computed
      # (CGLS without ESD), in which case there is no twin summary to print
      if (self.twin_components is not None and len(self.twin_components)
          and self.twin_covariance_matrix is not None):
        standard_uncertainties = \
          self.twin_covariance_matrix.matrix_packed_u_diagonal()
        print(file=log)
        print("Twin summary:", file=log)
        print("twin_law  fraction  standard_uncertainty", file=log)
        for i, twin in enumerate(self.twin_components):
          if twin.grad:
            print("%-9s %-9.4f %.4f" %(
              twin.twin_law.as_hkl(), twin.value, math.sqrt(standard_uncertainties[i])), file=log)
    print(file=log)
    print("Disagreeable reflections:", file=log)
    self.get_disagreeable_reflections()

  def get_hklf2_merging_stats(self):
    if self.hklf_code != 2:
      return None
    one_h_function = None
    if self.use_tsc:
      one_h_function = self.normal_eqns.one_h_linearisation
    fo2, f_calc = self.get_fo_sq_fc(one_h_function=one_h_function,
      filtered=False, merge=False)
    return fo2.merge_equivalents(algorithm="shelx")

  def _fo_sq_fc_cache_table_signature(self, table_file_name):
    if not table_file_name:
      return None
    table_file_name = os.path.normcase(os.path.abspath(table_file_name))
    try:
      stat = os.stat(table_file_name)
      return (table_file_name, stat.st_mtime_ns, stat.st_size)
    except OSError:
      return (table_file_name, None, None)

  def _fo_sq_fc_cache_key(self, one_h_function, filtered, merge, complete):
    current_table_file_name = None
    try:
      current_table_file_name = str(nsa2_get_param("file")).lstrip().rstrip()
    except Exception:
      pass
    return (
      id(one_h_function) if one_h_function is not None else None,
      bool(self.use_tsc),
      bool(OV.IsNoSpherA2()),
      self._fo_sq_fc_cache_table_signature(self.table_file_name),
      self._fo_sq_fc_cache_table_signature(current_table_file_name),
      filtered,
      merge,
      complete)

  def get_fo_sq_fc(self, one_h_function=None, filtered=True, merge=True, complete=False):
    cache_key = self._fo_sq_fc_cache_key(one_h_function, filtered, merge, complete)
    if self.fo_sq_fc is None or self.fo_sq_fc_key != cache_key:
      self.fo_sq_fc = super().get_fo_sq_fc(one_h_function=one_h_function,
        filtered=filtered, merge=merge, complete=complete)
      self.fo_sq_fc_key = cache_key
    return self.fo_sq_fc

  def get_refinement_wrapper(self, iterations_class):
    class refinementWrapper(iterations_class):
      def __init__(self, parent, normal_eqs, *args, **kwds):
        self.parent = parent
        parent.cycles = self
        normal_eqs.iterations_object = self
        super(iterations_class, self).__init__(normal_eqs, *args, **kwds)
      def do(self):
        objective_only = len(self.parent.reparametrisation.mapping_to_grad_fc_all) == 0
        if objective_only and self.n_max_iterations != 0:
          olx.Echo("Nothing to refine, performing L.S. 0", m="warning")
          self.n_max_iterations = 0
        if self.n_max_iterations == 0:
          self.n_iterations = 0
          self.non_linear_ls.build_up(objective_only=objective_only)
          if not objective_only:
            self.non_linear_ls.solve()
            self.analyse_shifts()
        else: # super(iterations_class, self) somehow does not work here - calls iterations.do()
          iterations_class.do(self)
      @property
      def interrupted(self):
        return self.parent.interrupted
      @interrupted.setter
      def interrupted(self, val):
        self.parent.interrupted = val

    return refinementWrapper

def write_diagnostics_stuff(f_calc):
  txt = ""
  name = str(OV.GetUserInput(0, "Save the F_calcs with this name", txt))
  if name and name != 'None':
    d = {}
    import pickle
    method = OV.GetParam('snum.refinement.ED.method', 'kinematic')
    a = f_calc.expand_to_p1()
    indices = a.indices()
    b = a.as_amplitude_array().data().as_numpy_array()
    d.setdefault('values', b)
    d.setdefault('indices', indices)
    d.setdefault('method', method)
    d.setdefault('structure', OV.FileName())
    out = open( '%s.pickle' %name, 'wb')
    pickle.dump(d, out)
    out.close()

