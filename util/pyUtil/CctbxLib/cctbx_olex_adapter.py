from __future__ import division

import os, sys
import olx
import OlexVFS
import time
import math

from PeriodicTable import PeriodicTable
import olexex
try:
  olx.current_hklsrc
except:
  olx.current_hklsrc = None
  olx.current_hklsrc_mtime = None
  olx.current_reflections = None
  olx.current_mask = None

import olex
import olex_core

import time
import cctbx_controller as cctbx_controller
from cctbx import maptbx, miller, uctbx
from libtbx import easy_pickle, utils

from olexFunctions import OlexFunctions
OV = OlexFunctions()

from History import hist

from RunPrg import RunRefinementPrg

global twin_laws_d
twin_laws_d = {}

from cctbx import adptbx, sgtbx, xray
from cctbx.array_family import flex

from smtbx.refinement import restraints

class OlexCctbxAdapter(object):
  def __init__(self):
    if OV.HasGUI():
      sys.stdout.refresh = True
    self._xray_structure = None
    self._restraints_manager = None
    self.olx_atoms = olexex.OlexRefinementModel()
    self.wavelength = self.olx_atoms.exptl.get('radiation', 0.71073)
    self.reflections = None
    twinning=self.olx_atoms.model.get('twin')
    if twinning is not None:
      self.twin_fraction = twinning['basf'][0]
      self.twin_law = [twinning['matrix'][j][i]
                       for i in range(3) for j in range(3)]
      twin_multiplicity = twinning.get('n', 2)
      if twin_multiplicity != 2:
        print "warning: only hemihedral twinning is currently supported"
    else:
      self.twin_law, self.twin_fraction = None, None
    try:
      self.exti = float(olx.Ins('exti'))
    except:
      self.exti = None
    self.initialise_reflections()

  def __del__(self):
    sys.stdout.refresh = False

  def xray_structure(self, construct_restraints=False):
    if self._xray_structure is None or construct_restraints:
      if construct_restraints: restraints_iter=self.olx_atoms.restraints_iterator()
      else: restraints_iter = None
      create_cctbx_xray_structure = cctbx_controller.create_cctbx_xray_structure(
        self.cell,
        self.space_group,
        self.olx_atoms.iterator(),
        restraints_iter=restraints_iter)
      if construct_restraints:
        proxies = create_cctbx_xray_structure.restraint_proxies()
        kwds = dict([(key+"_proxies", value) for key, value in proxies.iteritems()])
        self._restraints_manager = restraints.manager(**kwds)
      self._xray_structure = create_cctbx_xray_structure.structure()

      table = ("n_gaussian", "it1992", "wk1995")[0]
      self._xray_structure.scattering_type_registry(
        table=table, d_min=self.reflections.f_sq_obs.d_min())
      if self.reflections._merge < 4:
        from cctbx.eltbx import wavelengths
        self._xray_structure.set_inelastic_form_factors(self.wavelength, "sasaki")
    return self._xray_structure

  def restraints_manager(self):
    if self._restraints_manager is None:
      self.xray_structure(construct_restraints=True)
    return self._restraints_manager

  def initialise_reflections(self, force=False, verbose=False):
    self.cell = self.olx_atoms.getCell()
    self.space_group = str(olx.xf_au_GetCellSymm())
    hklf_matrix = utils.flat_list(self.olx_atoms.model['hklf']['matrix'])
    hklf_matrix = sgtbx.rt_mx(
      sgtbx.rot_mx([int(i) for i in hklf_matrix]).transpose())
    reflections = olx.HKLSrc()
    mtime = os.path.getmtime(reflections)
    if (force or
        reflections != olx.current_hklsrc or
        mtime != olx.current_hklsrc_mtime or
        (olx.current_reflections is not None
         and hklf_matrix != olx.current_reflections.hklf_matrix)):
      olx.current_hklsrc = reflections
      olx.current_hklsrc_mtime = mtime
      olx.current_reflections = cctbx_controller.reflections(
        self.cell, self.space_group, reflections, hklf_matrix)
    if olx.current_reflections:
      self.reflections = olx.current_reflections
    else:
      olx.current_reflections = cctbx_controller.reflections(
        self.cell, self.space_group, reflections, hklf_matrix)
      self.reflections = olx.current_reflections
    merge = self.olx_atoms.model.get('merge')
    omit = self.olx_atoms.model['omit']
    if force or merge is None or merge != self.reflections._merge:
      self.reflections.merge(merge=merge)
      self.reflections.filter(omit, self.olx_atoms.exptl['radiation'])
    if force or omit is None or omit != self.reflections._omit:
      self.reflections.filter(omit, self.olx_atoms.exptl['radiation'])
    if verbose:
      self.reflections.show_summary()

  def f_calc(self, miller_set,
             apply_extinction_correction=True,
             apply_twin_law=True,
             algorithm="direct"):
    assert self.xray_structure().scatterers().size() > 0, "n_scatterers > 0"
    if apply_twin_law and self.twin_law is not None:
      twinning = cctbx_controller.hemihedral_twinning(self.twin_law, miller_set)
      twin_set = twinning.twin_complete_set
      fc = twin_set.structure_factors_from_scatterers(
        self.xray_structure(), algorithm=algorithm).f_calc()
      twinned_fc2 = twinning.twin_with_twin_fraction(
        fc.as_intensity_array(),
        self.twin_fraction)
      fc = twinned_fc2.f_sq_as_f().phase_transfer(fc).common_set(miller_set)
    else:
      fc = miller_set.structure_factors_from_scatterers(
        self.xray_structure(), algorithm=algorithm).f_calc()
    if apply_extinction_correction and self.exti is not None:
      fc = fc.apply_shelxl_extinction_correction(self.exti, self.wavelength)
    return fc

  def compute_weights(self, fo2, fc):
    weight = self.olx_atoms.model['weight']
    params = dict(a=0.1, b=0, c=0, d=0, e=0, f=1./3)
    for param, value in zip(params.keys()[:len(weight)], weight):
      params[param] = value
    weighting = xray.weighting_schemes.shelx_weighting(**params)
    scale_factor = fo2.scale_factor(fc)
    weighting.observed = fo2
    weighting.compute(fc, scale_factor)
    return weighting.weights

from smtbx import absolute_structure

class hooft_analysis(OlexCctbxAdapter, absolute_structure.hooft_analysis):
  def __init__(self, scale=None):
    OlexCctbxAdapter.__init__(self)
    if scale is not None:
      self.scale = float(scale)
    else: self.scale=None
    fo2 = self.reflections.f_sq_obs_filtered
    if not fo2.anomalous_flag():
      print "No Bijvoet pairs"
      return
    fc = self.f_calc(miller_set=fo2)
    weights = self.compute_weights(fo2, fc)
    scale = fo2.scale_factor(fc, weights=weights)
    absolute_structure.hooft_analysis.__init__(self, fo2, fc, scale)
    self.show()

OV.registerFunction(hooft_analysis)


class FullMatrixRefine(OlexCctbxAdapter):
  def __init__(self, max_cycles=None, max_peaks=5, verbose=False):
    OlexCctbxAdapter.__init__(self)
    self.max_cycles = max_cycles
    self.max_peaks = max_peaks
    self.verbose = verbose
    sys.stdout.refresh = False
    self.scale_factor = None
    self.failure = False

  def run(self):
    from smtbx.refinement import least_squares
    from smtbx.refinement import constraints
    from smtbx.utils import connectivity_table
    wavelength = self.olx_atoms.exptl.get('radiation', 0.71073)

    filepath = OV.StrDir()
    self.f_mask = None
    if OV.GetParam("snum.refinement.use_solvent_mask"):
      modified_hkl_path = "%s/%s-mask.hkl" %(OV.FilePath(), OV.FileName())
      original_hklsrc = OV.GetParam('snum.masks.original_hklsrc')
      if OV.HKLSrc() == modified_hkl_path and original_hklsrc is not None:
        # change back to original hklsrc
        OV.HKLSrc(original_hklsrc)
        # we need to reinitialise reflections
        self.initialise_reflections()
      if OV.GetParam("snum.refinement.recompute_mask_before_refinement"):
        OlexCctbxMasks()
        if olx.current_mask.flood_fill.n_voids() > 0:
          self.f_mask = olx.current_mask.f_mask()
      elif os.path.exists("%s/%s-f_mask.pickle" %(filepath, OV.FileName())):
        self.f_mask = easy_pickle.load("%s/%s-f_mask.pickle" %(filepath, OV.FileName()))
      if self.f_mask is None:
        print "No mask present"
    restraints_manager = self.restraints_manager()
    geometrical_constraints = self.setup_geometrical_constraints(
      self.olx_atoms.afix_iterator())
    shelx_parts = flex.int(self.olx_atoms.disorder_parts())
    conformer_indices = shelx_parts.deep_copy().set_selected(shelx_parts < 0, 0)
    sym_excl_indices = flex.abs(
      shelx_parts.deep_copy().set_selected(shelx_parts > 0, 0))
    connectivity_table = connectivity_table(
      self.xray_structure(),
      conformer_indices=flex.size_t(list(conformer_indices)),
      sym_excl_indices=flex.size_t(list(sym_excl_indices)))
    import smtbx.refinement.restraints
    self.reparametrisation = constraints.reparametrisation(
      structure=self.xray_structure(),
      geometrical_constraints=geometrical_constraints,
      connectivity_table=connectivity_table)
    self.normal_eqns = least_squares.normal_equations(
      self.xray_structure(), self.reflections.f_sq_obs_filtered,
      f_mask=self.f_mask,
      reparametrisation=self.reparametrisation,
      restraints_manager=restraints_manager,
      weighting_scheme="default")
    objectives = []
    scales = []
    try:
      for i in range (self.max_cycles):
        self.xray_structure_pre_cycle = self.xray_structure().deep_copy_scatterers()
        self.normal_eqns.build_up()
        objectives.append(self.normal_eqns.objective)
        scales.append(self.normal_eqns.scale_factor)
        self.normal_eqns.solve_and_apply_shifts()
        self.shifts = self.normal_eqns.shifts
        self.show_sorted_shifts(max_items=2)
        self.feed_olex()
        self.scale_factor = scales[-1]
      self.export_var_covar(self.normal_eqns.covariance_matrix_and_annotations())
    except RuntimeError, e:
      if str(e).startswith("cctbx::adptbx::debye_waller_factor_exp: max_arg exceeded"):
        print "Refinement failed to converge"
      elif "SCITBX_ASSERT(!chol.failure) failure" in str(e):
        print "Cholesky failure"
      else:
        print "Refinement failed"
        print e
      self.failure = True
    else:
      fo_minus_fc = self.f_obs_minus_f_calc_map(0.4)
      fo_minus_fc.apply_volume_scaling()
      self.diff_stats = fo_minus_fc.statistics()
      self.post_peaks(fo_minus_fc, max_peaks=self.max_peaks)
      self.restraints_manager().show_sorted(self.xray_structure())
      self.show_summary()
    finally:
      sys.stdout.refresh = True

  def as_cif_block(self):
    cif_block = self.xray_structure().as_cif_block()
    fmt = "%.6f"
    d_max, d_min = self.reflections.f_sq_obs_filtered.d_max_min()
    cif_block['_refine_diff_density_max'] = fmt % self.diff_stats.max()
    cif_block['_refine_diff_density_min'] = fmt % self.diff_stats.min()
    cif_block['_refine_diff_density_rms'] = fmt % math.sqrt(self.diff_stats.mean_sq())
    cif_block['_refine_ls_d_res_high'] = fmt % d_min
    cif_block['_refine_ls_d_res_low'] = fmt % d_max
    cif_block['_reflns_threshold_expression'] = 'I>4u(I)' # XXX is this correct?
    #wR2, GooF = self.wR2_and_GooF()
    #cif_block['_refine_ls_goodness_of_fit_all'] = GooF
    #cif_block['_refine_ls_hydrogen_treatment'] =
    cif_block['_refine_ls_matrix_type'] = 'full'
    #cif_block['_refine_ls_number_constraints'] =
    cif_block['_refine_ls_number_parameters'] = self.reparametrisation.n_independent_params
    cif_block['_refine_ls_number_reflns'] = self.reflections.f_sq_obs_filtered.size()
    #cif['_refine_ls_number_restraints' =
    cif_block['_refine_ls_R_factor_all'] = fmt % self.R1(all_data=True)[0]
    cif_block['_refine_ls_R_factor_gt'] = fmt % self.R1()[0]
    #cif_block['_refine_ls_restrained_S_all'] = # check whether GooF is correct (restraints)
    #cif_block['_refine_ls_shift/su_max'] =
    #cif_block['_refine_ls_shift/su_mean'] =
    cif_block['_refine_ls_structure_factor_coef'] = 'Fsqd'
    #cif_block['_refine_ls_weighting_details'] =
    cif_block['_refine_ls_weighting_scheme'] = 'calc'
    #cif_block['_refine_ls_wR_factor_all'] = wR2
    return cif_block

  def setup_geometrical_constraints(self, afix_iter=None):
    geometrical_constraints = []
    from smtbx.refinement.constraints import geometrical_hydrogens
    constraints = {
      # AFIX mn : some of them use a pivot whose position is given wrt
      #           the first constrained scatterer site
      # m:    type                                    , pivot position
      1:  ("tertiary_ch_site"                        , -1),
      2:  ("secondary_ch2_sites"                     , -1),
      3:  ("staggered_terminal_tetrahedral_xh3_sites", -1),
      4:  ("secondary_planar_xh_site"                , -1),
      8:  ("staggered_terminal_tetrahedral_xh_site"  , -1),
      9:  ("terminal_planar_xh2_sites"               , -1),
      13: ("terminal_tetrahedral_xh3_sites"          , -1),
      14: ("terminal_tetrahedral_xh_site"            , -1),
      15: ("polyhedral_bh_site"                      , -1),
      16: ("terminal_linear_ch_site"                 , -1),
    }

    xs = self.xray_structure()
    for m, n, pivot, dependent, pivot_neighbours, bond_length in afix_iter:
      if len(dependent) == 0: continue
      info = constraints.get(m)
      if info is not None:
        constraint_name = info[0]
        constraint_type = getattr(
          geometrical_hydrogens, constraint_name)
        rotating = n in (7, 8)
        stretching = n in (4, 8)
        if bond_length == 0:
          bond_length = None
        current = constraint_type(
          rotating=rotating,
          stretching=stretching,
          bond_length=bond_length,
          pivot=pivot,
          constrained_site_indices=dependent)
        geometrical_constraints.append(current)
    return geometrical_constraints

  def export_var_covar(self, matrix):
    wFile = open("%s/%s.vcov" %(OV.FilePath(),OV.FileName()),'wb')
    wFile.write("VCOV\n")
    wFile.write(" ".join(matrix[1]) + "\n")
    for item in matrix[0]:
      wFile.write(str(item) + " ")
    wFile.close()

  def feed_olex(self):
    ## Feed Model
    u_total  = 0
    u_atoms = []
    i = 1

    def iter_scatterers():
      for a in self.xray_structure().scatterers():
        label = a.label
        xyz = a.site
        symbol = a.scattering_type
        if a.flags.use_u_iso():
          u = (a.u_iso,)
          u_eq = u[0]
        if a.flags.use_u_aniso():
          u_cif = adptbx.u_star_as_u_cart(self.xray_structure().unit_cell(), a.u_star)
          u = u_cif
          u_eq = adptbx.u_star_as_u_iso(self.xray_structure().unit_cell(), a.u_star)
        yield label, xyz, u, u_eq, a.occupancy, symbol, a.flags

    for name, xyz, u, ueq, occu, symbol, flags in iter_scatterers():
      if len(u) == 6:
        u_trans = (u[0], u[1], u[2], u[5], u[4], u[3])
      else:
        u_trans = u

      id = self.olx_atoms.id_for_name[name]
      olx.xf_au_SetAtomCrd(id, *xyz)
      olx.xf_au_SetAtomU(id, *u_trans)
      olx.xf_au_SetAtomOccu(id, occu)
      if not flags.grad_site():
        olx.Fix('xyz', name)
      if not (flags.grad_u_iso() or flags.grad_u_aniso()):
        olx.Fix('Uiso', name)
      if not flags.grad_occupancy():
        olx.Fix('occu', occu, name)
      u_total += u[0]
      u_average = u_total/i
    #olx.Sel('-u')
    olx.xf_EndUpdate()

  def f_model(self, miller_set):
    f_model = miller_set.structure_factors_from_scatterers(
      self.xray_structure(),
      algorithm="direct",
      cos_sin_table=True).f_calc()
    if self.f_mask is not None:
      f_model, f_mask = f_model.common_sets(self.f_mask)
      f_model = miller.array(miller_set=miller_set,
                             data=(f_model.data() + f_mask.data()))
    return f_model

  def f_obs_minus_f_calc_map(self, resolution):
    import math
    f_sq_obs = self.reflections.f_sq_obs_filtered
    f_sq_obs = f_sq_obs.eliminate_sys_absent().average_bijvoet_mates()
    f_obs = f_sq_obs.f_sq_as_f()
    f_calc = self.f_model(f_obs)
    if self.scale_factor is None:
      k = f_obs.scale_factor(f_calc)
    else:
      k = math.sqrt(self.scale_factor)
    f_obs_minus_f_calc = f_obs.f_obs_minus_f_calc(1./k, f_calc)
    return f_obs_minus_f_calc.fft_map(
      symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
      resolution_factor=resolution,
    )

  def post_peaks(self, fft_map, max_peaks=5):
    from cctbx import maptbx
    from  libtbx.itertbx import izip
    peaks = fft_map.peak_search(
      parameters=maptbx.peak_search_parameters(
        peak_search_level=3,
        interpolate=False,
        min_distance_sym_equiv=1.0,
        max_clusters=max_peaks),
      verify_symmetry=False
      ).all()
    i = 0
    for xyz, height in izip(peaks.sites(), peaks.heights()):
      if i < 3:
        if self.verbose: print "Position of peak %s = %s, Height = %s" %(i, xyz, height)
      i += 1
      id = olx.xf_au_NewAtom("%.2f" %(height), *xyz)
      if id != '-1':
        olx.xf_au_SetAtomU(id, "0.06")
      if i == 100:
        break
    olx.xf_EndUpdate()
    olx.Compaq('-q')
    OV.Refresh()

  def R1(self, all_data=False):
    f_obs = self.reflections.f_sq_obs_filtered.f_sq_as_f()
    if not all_data:
      strong = f_obs.data() > 4*f_obs.sigmas()
      f_obs = f_obs.select(strong)
    R1 = f_obs.r1_factor(
      self.f_model(f_obs), scale_factor=math.sqrt(self.scale_factor))
    return R1, f_obs.size()


  def show_summary(self):
    print "R1 (all data): %.3f for %i unique reflections" % self.R1(all_data=True)
    print "R1: %.3f for %i reflections" % self.R1()
    print "wR2, GooF: ", self.normal_eqns.wR2(), self.normal_eqns.goof()

  def iter_shifts_sites(self, max_items=None):
    scatterers = self.xray_structure().scatterers()
    sites_shifts = self.xray_structure().sites_cart() - self.xray_structure_pre_cycle.sites_cart()
    distances = sites_shifts.norms()
    i_distances_sorted = flex.sort_permutation(data=distances, reverse=True)
    mean = flex.mean(distances)
    if max_items is not None:
      i_distances_sorted = i_distances_sorted[:max_items]
    for i_seq in iter(i_distances_sorted):
      yield distances[i_seq], scatterers[i_seq]

  def iter_shifts_u(self, max_items=None):
    scatterers = self.xray_structure().scatterers()
    adp_shifts = self.xray_structure().extract_u_cart_plus_u_iso() \
               - self.xray_structure_pre_cycle.extract_u_cart_plus_u_iso()
    norms = adp_shifts.norms()
    mean = flex.mean(norms)
    i_adp_shifts_sorted = flex.sort_permutation(data=norms, reverse=True)
    if max_items is not None:
      i_adp_shifts_sorted = i_adp_shifts_sorted[:max_items]
    for i_seq in iter(i_adp_shifts_sorted):
      yield norms[i_seq], scatterers[i_seq]

  def show_log(self, f=None):
    import sys
    if self.log is sys.stdout: return
    if f is None: f = sys.stdout
    print >> f, self.log.getvalue()

  def show_sorted_shifts(self, max_items=None, log=None):
    import sys
    if log is None: log = sys.stdout
    print >> log, "Sorted site shifts in Angstrom:"
    print >> log, "shift scatterer"
    n_not_shown = self.xray_structure().scatterers().size()
    for distance, scatterer in self.iter_shifts_sites(max_items=max_items):
      n_not_shown -= 1
      print >> log, "%5.3f %s" %(distance, scatterer.label)
      if round(distance, 3) == 0: break
    if n_not_shown != 0:
      print >> log, "... (remaining %d not shown)" % n_not_shown
    #
    print >> log, "Sorted adp shift norms:"
    print >> log, "dU scatterer"
    n_not_shown = self.xray_structure().scatterers().size()
    for norm, scatterer in self.iter_shifts_u(max_items=max_items):
      n_not_shown -= 1
      print >> log, "%5.3f %s" %(norm, scatterer.label)
      if round(norm, 3) == 0: break
    if n_not_shown != 0:
      print >> log, "... (remaining %d not shown)" % n_not_shown

  def show_shifts(self, log=None):
    import sys
    if log is None: log = sys.stdout
    site_symmetry_table = self.xray_structure().site_symmetry_table()
    i=0
    for i_sc, sc in enumerate(self.xray_structure().scatterers()):
      op = site_symmetry_table.get(i_sc)
      print >> log, "%-4s" % sc.label
      if sc.flags.grad_site():
        n = op.site_constraints().n_independent_params()
        if n != 0:
          print >> log, ("site:" + "%7.4f, "*(n-1) + "%7.4f")\
                % tuple(self.shifts[i:i+n])
        i += n
      if sc.flags.grad_u_iso() and sc.flags.use_u_iso():
        if not(sc.flags.tan_u_iso() and sc.flags.param > 0):
          print >> log, "u_iso: %6.4f" % self.shifts[i]
          i += 1
      if sc.flags.grad_u_aniso() and sc.flags.use_u_aniso():
        n = op.adp_constraints().n_independent_params()
        print >> log, (("u_aniso:" + "%6.3f, "*(n-1) + "%6.3f")
                       % tuple(self.shifts[i:i+n]))
        i += n
      if sc.flags.grad_occupancy():
        print >> log, "occ: %4.2f" % self.shifts[i]
        i += 1
      if sc.flags.grad_fp():
        print >> log, "f': %6.4f" % self.shifts[i]
        i += 1
      if sc.flags.grad_fdp():
        print >> log, "f'': %6.4f" % self.shifts[i]
        i += 1
      print >> log

class OlexCctbxSolve(OlexCctbxAdapter):
  def __init__(self):
    OlexCctbxAdapter.__init__(self)
    self.peak_normaliser = 1200 #fudge factor to get cctbx peaks on the same scale as shelx peaks

  def runChargeFlippingSolution(self, verbose="highly", solving_interval=60):
    import time
    t1 = time.time()
    from smtbx.ab_initio import charge_flipping
    from cctbx import maptbx
    from  libtbx.itertbx import izip
    from libtbx import group_args

    t2 = time.time()
    print 'imports took %0.3f ms' %((t2-t1)*1000.0)
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
      for element in str(olx.xf_GetFormula('list')).split(','):
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
      # search and print Fourier peaks
      peaks = fft_map.peak_search(
        parameters=maptbx.peak_search_parameters(
          min_distance_sym_equiv=1.0,
          max_clusters=expected_peaks,),
        verify_symmetry=False
        ).all()
      for xyz, height in izip(peaks.sites(), peaks.heights()):
        if not xyz:
          have_solution = False
          break
        else:
          self.post_single_peak(xyz, height)
      have_solution = True

      olex.m('Compaq -a')
      olex.m('move')

    else: have_solution = False
    return have_solution

  def post_single_peak(self, xyz, height, cutoff=1.0):
    if height/self.peak_normaliser < cutoff:
      return
    sp = (height/self.peak_normaliser)

    id = olx.xf_au_NewAtom("%.2f" %(sp), *xyz)
    if id != '-1':
      olx.xf_au_SetAtomU(id, "0.06")

class OlexCctbxMasks(OlexCctbxAdapter):

  def __init__(self, recompute=True):
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
    if os.path.exists(pickle_path):
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
      mask = masks.mask(xs, fo_sq)
      self.time_compute = time_log("computation of mask").start()
      mask.compute(solvent_radius=self.params.solvent_radius,
                   shrink_truncation_radius=self.params.shrink_truncation_radius,
                   resolution_factor=self.params.resolution_factor,
                   atom_radii_table=olex_core.GetVdWRadii(),
                   use_space_group_symmetry=True)
      self.time_compute.stop()
      self.time_f_mask = time_log("f_mask calculation").start()
      f_mask = mask.structure_factors()
      self.time_f_mask.stop()
      olx.current_mask = mask
      if mask.flood_fill.n_voids() > 0:
        easy_pickle.dump(
          '%s/%s-mask.pickle' %(filepath, OV.FileName()), mask.mask.data)
        easy_pickle.dump(
          '%s/%s-f_mask.pickle' %(filepath, OV.FileName()), mask.f_mask())
        easy_pickle.dump(
          '%s/%s-f_model.pickle' %(filepath, OV.FileName()), mask.f_model())
      mask.show_summary()
      from iotbx.cif import model
      cif_block = model.block()
      fo2 = self.reflections.f_sq_obs
      hklstat = olex_core.GetHklStat()
      merging = self.reflections.merging
      min_d_star_sq, max_d_star_sq = fo2.min_max_d_star_sq()
      fo2 = self.reflections.f_sq_obs
      fo2.show_comprehensive_summary()
      h_min, k_min, l_min = hklstat['MinIndexes']
      h_max, k_max, l_max = hklstat['MaxIndexes']
      cif_block['_diffrn_reflns_number'] = fo2.size()
      cif_block['_diffrn_reflns_av_R_equivalents'] = "%.4f" %merging.r_int()
      cif_block['_diffrn_reflns_av_sigmaI/netI'] = "%.4f" %merging.r_sigma()
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
      cif_block.update(mask.as_cif_block())
      cif = model.cif()
      data_name = OV.FileName().replace(' ', '')
      cif[data_name] = cif_block
      f = open('%s/%s-mask.cif' %(filepath, OV.FileName()),'wb')
      print >> f, cif
      f.close()
      OV.SetParam('snum.masks.update_cif', True)
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
      model_map = miller.fft_map(crystal_gridding, data)
      output_data = model_map.apply_volume_scaling().real_map()
    self.time_write_grid = time_log("write grid").start()
    if OV.HasGUI():
      write_grid_to_olex(output_data)
    self.time_write_grid.stop()

  def __del__(self):
    OV.DeleteBitmap("working")

OV.registerFunction(OlexCctbxMasks)

class OlexCctbxTwinLaws(OlexCctbxAdapter):

  def __init__(self):
    OlexCctbxAdapter.__init__(self)

    from PilTools import MatrixMaker
    global twin_laws_d
    a = MatrixMaker()
    twin_laws = cctbx_controller.twin_laws(self.reflections)
    r_list = []
    l = 0
    self.twin_law_gui_txt = ""
    if not twin_laws:
      print "There are no possible twin laws"
      html = "<tr><td></td><td>"
      html += "<b>%There are no possible Twin Laws%</b>"
      OV.write_to_olex('twinning-result.htm', html, False)
      OV.htmlReload()
      return

    lawcount = 0
    self.twin_laws_d = {}
    law_txt = ""
    self.run_backup_shelx()
    twin_double_laws = []
    for twin_law in twin_laws:
      law_double = twin_law.as_double_array()
      twin_double_laws.append(law_double)
    twin_double_laws.append((1, 0, 0, 0, 1, 0, 0, 0, 1))
    for twin_law in twin_double_laws:
      lawcount += 1
      self.twin_laws_d.setdefault(lawcount, {})
      self.twin_law_gui_txt = ""
      r, basf, f_data, history = self.run_twin_ref_shelx(twin_law)
      try:
        float(r)
      except:
        r = 0.99
      r_list.append((r, lawcount, basf))
      name = "law%i" %lawcount
      font_color = "#444444"
      if basf == "n/a":
        font_color_basf = "blue"
      elif float(basf) < 0.1:
        font_color_basf = "red"
        basf = "%.2f" %float(basf)
      else:
        font_color_basf = "green"
        basf = "%.2f" %float(basf)

      txt = [{'txt':"R=%.2f%%" %(float(r)*100),
              'font_colour':font_color},
             {'txt':"basf=%s" %str(basf),
              'font_colour':font_color_basf}]
      states = ['on', 'off']
      for state in states:
        image_name, img  = a.make_3x3_matrix_image(name, twin_law, txt, state)

      #law_txt += "<zimg src=%s>" %image_name
      law_straight = ""
      for x in xrange(9):
        law_straight += " %s" %(law_double)[x]

      self.twin_laws_d[lawcount] = {'number':lawcount,
                                    'law':twin_law,
                                    'law_double':law_double,
                                    'law_straight':law_straight,
                                    'R1':r,
                                    'BASF':basf,
                                    'law_image':img,
                                    'law_txt':law_txt,
                                    'law_image_name':image_name,
                                    'name':name,
                                    'ins_file':f_data,
                                    'history':history,
                                    }
#      href = 'spy.on_twin_image_click(%s)'
#      href = 'spy.revert_history -solution="%s" -refinement="%s"' %(history_solution, history_refinement)
#      law_txt = "<a href='%s'><zimg src=%s></a>&nbsp;" %(href, image_name)
#      self.twin_law_gui_txt += "%s" %(law_txt)
#      self.make_gui()
      l += 1
    #r_list.sort()
    law_txt = ""
    self.twin_law_gui_txt = ""
    i = 0
    html = "<tr><td></td><td>"
    for r, run, basf in r_list:
      i += 1
      image_name = self.twin_laws_d[run].get('law_image_name', "XX")
      use_image = "%son.png" %image_name
      img_src = "%s.png" %image_name
      name = self.twin_laws_d[run].get('name', "XX")
      #href = 'spy.on_twin_image_click(%s)'
      href = 'spy.revert_history(%s)>>spy.reset_twin_law_img()>>HtmlReload' %(self.twin_laws_d[i].get('history'))
      law_txt = "<a href='%s'><zimg src=%s></a>&nbsp;" %(href, image_name)
      self.twin_law_gui_txt += "%s" %(law_txt)
      control = "IMG_%s" %image_name.upper()

      html += '''
<a href='%s' target='Apply this twin law'><zimg name='%s' border="0" src="%s"></a>&nbsp;
    ''' %(href, control, img_src)
    html += "</td></tr>"
    OV.write_to_olex('twinning-result.htm', html, False)
    OV.CopyVFSFile(use_image, "%s.png" %image_name,2)
    #OV.Refresh()
    #if OV.IsControl(control):
    #  OV.SetImage(control,use_image)
    OV.HtmlReload()
    twin_laws_d = self.twin_laws_d
#    self.make_gui()

  def run_backup_shelx(self):
    self.filename = olx.FileName()
    olx.DelIns("TWIN")
    olx.DelIns("BASF")
    olx.File("notwin.ins")

  def run_twin_ref_shelx(self, law):
    law_ins = ' '.join(str(int(i)) for i in law[:9])
    print "Testing: %s" %law_ins
    olx.Atreap("-b notwin.ins")
    olx.User("'%s'" %olx.FilePath())
    if law != (1, 0, 0, 0, 1, 0, 0, 0, 1):
      OV.AddIns("TWIN %s" %law_ins)
      OV.AddIns("BASF %s" %"0.5")
    else:
      OV.DelIns("TWIN")
      OV.DelIns("BASF")

    curr_prg = OV.GetParam('snum.refinement.program')
    curr_method = OV.GetParam('snum.refinement.method')
    curr_cycles = OV.GetParam('snum.refinement.max_cycles')
    OV.SetMaxCycles(1)
    if curr_prg != 'smtbx-refine':
      OV.set_refinement_program(curr_prg, 'CGLS')
    olx.File("%s.ins" %self.filename)
    rFile = open(olx.FileFull(), 'r')
    f_data = rFile.readlines()

    OV.SetParam('snum.skip_history','True')

    a = RunRefinementPrg()
    self.R1 = a.R1
    his_file = a.his_file

    OV.SetMaxCycles(curr_cycles)
    OV.set_refinement_program(curr_prg, curr_method)

    OV.SetParam('snum.skip_history','False')
    r = olx.Lst("R1")
    olex_refinement_model = OV.GetRefinementModel(False)
    if olex_refinement_model.has_key('twin'):
      basf = olex_refinement_model['twin']['basf'][0]
    else:
      basf = "n/a"

    return self.R1, basf, f_data, his_file

  def twinning_gui_def(self):
    if not self.twin_law_gui_txt:
      lines = ['search_for_twin_laws']
      tools = ['search_for_twin_laws_t1']
    else:
      lines = ['search_for_twin_laws', 'twin_laws']
      tools = ['search_for_twin_laws_t1', 'twin_laws']

    tbx = {"twinning":
           {"category":'tools',
            'tbx_li':lines
            }
           }

    tbx_li = {'search_for_twin_laws':{"category":'analysis',
                                      'image':'cctbx',
                                      'tools':['search_for_twin_laws_t1']
                                      },
              'twin_laws':{"category":'analysis',
                           'image':'cctbx',
                           'tools':['twin_laws']
                           }
              }

    tools = {'search_for_twin_laws_t1':{'category':'analysis',
                                        'display':"%Search for Twin Laws%",
                                        'colspan':1,
                                        'hrefs':['spy.OlexCctbxTwinLaws()']
                                        },
             'twin_laws':
             {'category':'analysis',
              'colspan':1,
              'before':self.twin_law_gui_txt,
              }
             }
    return {"tbx":tbx,"tbx_li":tbx_li,"tools":tools}

  def make_gui(self):
    gui = self.twinning_gui_def()
    from GuiTools import MakeGuiTools
    a = MakeGuiTools(tool_fun="single", tool_param=gui)
    a.run()
    OV.UpdateHtml()
OV.registerFunction(OlexCctbxTwinLaws)


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
          print "** Restarting (no phase transition) **"
        elif previous_state is solving.evaluating:
          print "** Restarting (no sharp correlation map) **"
      if verbose == "highly":
        if previous_state is not solving.guessing_delta:
          print "Guessing delta..."
          print ("%10s | %10s | %10s | %10s | %10s | %10s | %10s"
                 % ('delta', 'delta/sig', 'R', 'F000',
                    'c_tot', 'c_flip', 'c_tot/c_flip'))
          print "-"*90
        rho = flipping.rho_map
        c_tot = rho.c_tot()
        c_flip = rho.c_flip(flipping.delta)
        # to compare with superflip output
        c_tot *= flipping.fft_scale; c_flip *= flipping.fft_scale
        print "%10.4f | %10.4f | %10.3f | %10.3f | %10.1f | %10.1f | %10.2f"\
              % (flipping.delta, flipping.delta/rho.sigma(),
                 flipping.r1_factor(), flipping.f_000,
                 c_tot, c_flip, c_tot/c_flip)

    elif solving.state is solving.solving:
      # main charge flipping loop to solve the structure
      if verbose=="highly":
        if previous_state is not solving.solving:
          print
          print "Solving..."
          print "with delta=%.4f" % flipping.delta
          print
          print "%5s | %10s | %10s" % ('#', 'F000', 'skewness')
          print '-'*33
        print "%5i | %10.1f | %10.3f" % (solving.iteration_index,
                                         flipping.f_000,
                                         flipping.rho_map.skewness())

    elif solving.state is solving.polishing:
      if verbose == 'highly':
        print
        print "Polishing"
    elif solving.state is solving.finished:
      break

    if plot is not None: plot.run_charge_flipping_graph(flipping, solving, previous_state)
    previous_state = solving.state

  if timing:
    print "Total Time: %.2f s" %(time.time() - t0)

def on_twin_image_click(run_number):
  # arguments is a list
  # options is a dictionary
  a = OlexCctbxTwinLaws()
  file_data = a.twin_laws_d[int(run_number)].get("ins_file")
  wFile = open(olx.FileFull(), 'w')
  wFile.writelines(file_data)
  wFile.close()
  olx.Atreap(olx.FileFull())
  OV.UpdateHtml()
OV.registerFunction(on_twin_image_click)

def reset_twin_law_img():
  global twin_laws_d
  olex_refinement_model = OV.GetRefinementModel(False)
  if olex_refinement_model.has_key('twin'):
    c = olex_refinement_model['twin']['matrix']
    curr_law = []
    for row in c:
      for el in row:
        curr_law.append(el)
    for i in xrange(3):
      curr_law.append(0.0)
    curr_law = tuple(curr_law)

  else:
    curr_law = (1, 0, 0, 0, 1, 0, 0, 0, 1)
  for law in twin_laws_d:
    name = twin_laws_d[law]['name']
    matrix = twin_laws_d[law]['law']
    if curr_law == matrix:
      OV.CopyVFSFile("%son.png" %name, "%s.png" %name,2)
    else:
      OV.CopyVFSFile("%soff.png" %name, "%s.png" %name,2)
  OV.HtmlReload()
OV.registerFunction(reset_twin_law_img)


def write_grid_to_olex(grid):
  import olex_xgrid
  gridding = grid.accessor()
  n_real = gridding.focus()
  olex_xgrid.Init(*n_real)
  for i in range(n_real[0]):
    for j in range(n_real[1]):
      for k in range(n_real[2]):
        olex_xgrid.SetValue(i,j,k, grid[i,j,k])
  olex_xgrid.SetMinMax(flex.min(grid), flex.max(grid))
  olex_xgrid.SetVisible(True)
  olex_xgrid.InitSurface(True)


class as_pdb_file(OlexCctbxAdapter):
  def __init__(self, args):
    OlexCctbxAdapter.__init__(self)
    filepath = args.get('filepath', OV.file_ChangeExt(OV.FileFull(), 'pdb'))
    f = open(filepath, 'wb')
    fractional_coordinates = \
                           args.get('fractional_coordinates')in (True, 'True', 'true')
    print >> f, self.xray_structure().as_pdb_file(
      remark=args.get('remark'),
      remarks=args.get('remarks', []),
      fractional_coordinates=fractional_coordinates,
      resname=args.get('resname'))

OV.registerMacro(as_pdb_file, """\
filepath&;remark&;remarks&;fractional_coordinates-(False)&;resname""")
