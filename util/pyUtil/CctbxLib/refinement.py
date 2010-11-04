from __future__ import division

import math, os, sys

from cctbx_olex_adapter import OlexCctbxAdapter, OlexCctbxMasks

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import olx
import olex_core

from cctbx.array_family import flex
from cctbx import adptbx, maptbx, miller, sgtbx, uctbx

import iotbx.cif.model

from libtbx import easy_pickle, utils

from scitbx.lstbx import normal_eqns_solving

from smtbx.refinement import restraints
from smtbx.refinement import least_squares
from smtbx.refinement import constraints
from smtbx.refinement.constraints import geometrical_hydrogens
import smtbx.utils


class iterations(normal_eqns_solving.naive_iterations):
  log = None

  def __init__(self, full_matrix_refine, **kwds):
    normal_eqns_solving.naive_iterations.__init__(
      self, full_matrix_refine.normal_eqns, **kwds)
    self.full_matrix_refine = full_matrix_refine
    self.xray_structure = full_matrix_refine.normal_eqns.xray_structure

  def next(self):
    self.xray_structure_pre_cycle = self.xray_structure.deep_copy_scatterers()
    normal_eqns_solving.naive_iterations.next(self)
    self.show_cycle_summary(log=self.log)
    self.show_sorted_shifts(max_items=10, log=self.log)
    self.normal_eqns.restraints_manager.show_sorted(
      self.xray_structure, f=self.log)
    self.show_cycle_summary()
    self.full_matrix_refine.feed_olex()
    return self

  def show_cycle_summary(self, log=None):
    if log is None: log = sys.stdout
    print >> log, "wR2 = %.4f for %i data and %i parameters" %(
      self.normal_eqns.wR2(), self.normal_eqns.fo_sq.size(),
      self.normal_eqns.reparametrisation.n_independent_params)
    print >> log, "GooF = %.4f" %(self.normal_eqns.goof(),)
    max_shift_site = self.max_shift_site()
    max_shift_u = self.max_shift_u()
    print >> log, "Max shift site: %.4f A for %s" %(
      max_shift_site[0], max_shift_site[1].label)
    print >> log, "Max dU: %.4f for %s" %(max_shift_u[0], max_shift_u[1].label)

  def max_shift_site(self):
    return self.iter_shifts_sites(max_items=1).next()

  def max_shift_u(self):
    return self.iter_shifts_u(max_items=1).next()

  def iter_shifts_sites(self, max_items=None):
    scatterers = self.xray_structure.scatterers()
    sites_shifts = self.xray_structure.sites_cart() -\
                 self.xray_structure_pre_cycle.sites_cart()
    distances = sites_shifts.norms()
    i_distances_sorted = flex.sort_permutation(data=distances, reverse=True)
    mean = flex.mean(distances)
    if max_items is not None:
      i_distances_sorted = i_distances_sorted[:max_items]
    for i_seq in iter(i_distances_sorted):
      yield distances[i_seq], scatterers[i_seq]

  def iter_shifts_u(self, max_items=None):
    scatterers = self.xray_structure.scatterers()
    adp_shifts = self.xray_structure.extract_u_cart_plus_u_iso() \
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
    n_not_shown = self.xray_structure.scatterers().size()
    for distance, scatterer in self.iter_shifts_sites(max_items=max_items):
      n_not_shown -= 1
      print >> log, "%5.3f %s" %(distance, scatterer.label)
      if round(distance, 3) == 0: break
    if n_not_shown != 0:
      print >> log, "... (remaining %d not shown)" % n_not_shown
    #
    print >> log, "Sorted adp shift norms:"
    print >> log, "dU scatterer"
    n_not_shown = self.xray_structure.scatterers().size()
    for norm, scatterer in self.iter_shifts_u(max_items=max_items):
      n_not_shown -= 1
      print >> log, "%5.3f %s" %(norm, scatterer.label)
      if round(norm, 3) == 0: break
    if n_not_shown != 0:
      print >> log, "... (remaining %d not shown)" % n_not_shown

  def show_shifts(self, log=None):
    import sys
    if log is None: log = sys.stdout
    site_symmetry_table = self.xray_structure.site_symmetry_table()
    i=0
    for i_sc, sc in enumerate(self.xray_structure.scatterers()):
      op = site_symmetry_table.get(i_sc)
      print >> log, "%-4s" % sc.label
      if sc.flags.grad_site():
        n = op.site_constraints().n_independent_params()
        if n != 0:
          print >> log, ("site:" + "%7.4f, "*(n-1) + "%7.4f")\
                % tuple(self.shifts[-1][i:i+n])
        i += n
      if sc.flags.grad_u_iso() and sc.flags.use_u_iso():
        if not(sc.flags.tan_u_iso() and sc.flags.param > 0):
          print >> log, "u_iso: %6.4f" % self.shifts[i]
          i += 1
      if sc.flags.grad_u_aniso() and sc.flags.use_u_aniso():
        n = op.adp_constraints().n_independent_params()
        print >> log, (("u_aniso:" + "%6.3f, "*(n-1) + "%6.3f")
                       % tuple(self.shifts[-1][i:i+n]))
        i += n
      if sc.flags.grad_occupancy():
        print >> log, "occ: %4.2f" % self.shifts[-1][i]
        i += 1
      if sc.flags.grad_fp():
        print >> log, "f': %6.4f" % self.shifts[-1][i]
        i += 1
      if sc.flags.grad_fdp():
        print >> log, "f'': %6.4f" % self.shifts[-1][i]
        i += 1
      print >> log


class FullMatrixRefine(OlexCctbxAdapter):
  def __init__(self, max_cycles=None, max_peaks=5, verbose=False):
    OlexCctbxAdapter.__init__(self)
    self.max_cycles = max_cycles
    self.max_peaks = max_peaks
    self.verbose = verbose
    sys.stdout.refresh = False
    self.scale_factor = None
    self.failure = False
    self.log = open(OV.file_ChangeExt(OV.FileFull(), 'log'), 'wb')

  def run(self):
    self.reflections.show_summary(log=self.log)

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
    self.constraints += self.setup_geometrical_constraints(
      self.olx_atoms.afix_iterator())
    self.n_constraints = len(self.constraints)
    shelx_parts = flex.int(self.olx_atoms.disorder_parts())
    conformer_indices = shelx_parts.deep_copy().set_selected(shelx_parts < 0, 0)
    sym_excl_indices = flex.abs(
      shelx_parts.deep_copy().set_selected(shelx_parts > 0, 0))
    connectivity_table = smtbx.utils.connectivity_table(
      self.xray_structure(),
      conformer_indices=flex.size_t(list(conformer_indices)),
      sym_excl_indices=flex.size_t(list(sym_excl_indices)))
    self.reparametrisation = constraints.reparametrisation(
      structure=self.xray_structure(),
      constraints=self.constraints,
      connectivity_table=connectivity_table,
      temperature=self.olx_atoms.exptl['temperature'])
    weight = self.olx_atoms.model['weight']
    params = dict(a=0.1, b=0,
                  #c=0, d=0, e=0, f=1./3,
                  )
    for param, value in zip(params.keys()[:min(2,len(weight))], weight):
      params[param] = value
    weighting = least_squares.mainstream_shelx_weighting(**params)
    self.normal_eqns = least_squares.normal_equations(
      self.reflections.f_sq_obs_filtered,
      f_mask=self.f_mask,
      reparametrisation=self.reparametrisation,
      restraints_manager=restraints_manager,
      weighting_scheme=weighting)
    self.cycles = iterations(self,
                             n_max_iterations=self.max_cycles,
                             log=self.log,
                             track_all=True)
    try:
      self.cycles.do(gradient_threshold=1e-5, shift_threshold=1e-5)
      self.scale_factor = self.cycles.scale_factors[-1]
      self.export_var_covar(self.normal_eqns.covariance_matrix_and_annotations())
      self.r1 = self.normal_eqns.r1_factor(cutoff_factor=2)
      self.r1_all_data = self.normal_eqns.r1_factor()
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
      f = open(OV.file_ChangeExt(OV.FileFull(), 'cif'), 'wb')
      cif = iotbx.cif.model.cif()
      cif[OV.FileName().replace(' ', '')] = self.as_cif_block()
      print >> f, cif
      f.close()
      new_weighting = weighting.optimise_parameters(
        self.normal_eqns.fo_sq,
        self.normal_eqns.f_calc,
        self.normal_eqns.scale_factor,
        self.reparametrisation.n_independent_params)
      OV.SetParam(
        'snum.refinement.suggested_weight', "%s %s" %(new_weighting.a, new_weighting.b))
    finally:
      sys.stdout.refresh = True
      self.log.close()

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

    two_theta_full = olx.Ins('acta')
    try: two_theta_full = float(two_theta_full)
    except ValueError: two_theta_full = uctbx.d_star_sq_as_two_theta(
      uctbx.d_as_d_star_sq(
        self.normal_eqns.fo_sq.d_max_min()[1]), self.wavelength, deg=True)
    completeness_full = self.normal_eqns.fo_sq.resolution_filter(
      d_min=uctbx.two_theta_as_d(two_theta_full, self.wavelength, deg=True)).completeness()

    shifts_over_su = flex.abs(
      self.normal_eqns.shifts /
      flex.sqrt(self.normal_eqns.covariance_matrix(independent_params=True)\
                .matrix_packed_u_diagonal()))
    xs = self.xray_structure()
    cif_block = xs.as_cif_block()
    fmt = "%.6f"
    #cif_block['_chemical_formula_sum'] = ' '.join(formatted_type_count_pairs)
    #cif_block['_chemical_formula_weight'] = '%.3f' % flex.sum(
      #xs.atomic_weights() * xs.scatterers().extract_occupancies())
    #
    fo2 = self.reflections.f_sq_obs
    hklstat = olex_core.GetHklStat()
    merging = self.reflections.merging
    min_d_star_sq, max_d_star_sq = fo2.min_max_d_star_sq()
    fo2 = self.reflections.f_sq_obs
    h_min, k_min, l_min = hklstat['MinIndexes']
    h_max, k_max, l_max = hklstat['MaxIndexes']
    cif_block['_diffrn_measured_fraction_theta_full'] = fmt % completeness_full
    cif_block['_diffrn_radiation_wavelength'] = self.wavelength
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
    cif_block['_diffrn_reflns_theta_full'] = two_theta_full/2
    #
    cif_block['_refine_diff_density_max'] = fmt % self.diff_stats.max()
    cif_block['_refine_diff_density_min'] = fmt % self.diff_stats.min()
    cif_block['_refine_diff_density_rms'] = fmt % math.sqrt(self.diff_stats.mean_sq())
    d_max, d_min = self.reflections.f_sq_obs_filtered.d_max_min()
    cif_block['_refine_ls_d_res_high'] = fmt % d_min
    cif_block['_refine_ls_d_res_low'] = fmt % d_max
    cif_block['_refine_ls_goodness_of_fit_ref'] = fmt % self.normal_eqns.goof()
    #cif_block['_refine_ls_hydrogen_treatment'] =
    cif_block['_refine_ls_matrix_type'] = 'full'
    cif_block['_refine_ls_number_constraints'] = self.n_constraints
    cif_block['_refine_ls_number_parameters'] = self.reparametrisation.n_independent_params
    cif_block['_refine_ls_number_reflns'] = self.reflections.f_sq_obs_filtered.size()
    cif_block['_refine_ls_number_restraints'] = self.normal_eqns.n_restraints
    cif_block['_refine_ls_R_factor_all'] = fmt % self.r1_all_data[0]
    cif_block['_refine_ls_R_factor_gt'] = fmt % self.r1[0]
    cif_block['_refine_ls_restrained_S_all'] = fmt % self.normal_eqns.restrained_goof()
    cif_block['_refine_ls_shift/su_max'] = "%.4f" % flex.max(shifts_over_su)
    cif_block['_refine_ls_shift/su_mean'] = "%.4f" % flex.mean(shifts_over_su)
    cif_block['_refine_ls_structure_factor_coef'] = 'Fsqd'
    cif_block['_refine_ls_weighting_details'] = str(
      self.normal_eqns.weighting_scheme)
    cif_block['_refine_ls_weighting_scheme'] = 'calc'
    cif_block['_refine_ls_wR_factor_ref'] = fmt % self.normal_eqns.wR2()
    cif_block['_reflns_number_gt'] = (
      self.normal_eqns.fo_sq.data() > 2 * self.normal_eqns.fo_sq.sigmas()).count(True)
    cif_block['_reflns_number_total'] = self.normal_eqns.fo_sq.size()
    cif_block['_reflns_threshold_expression'] = 'I>2u(I)' # XXX is this correct?
    return cif_block

  def setup_geometrical_constraints(self, afix_iter=None):
    geometrical_constraints = []
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
      n_equiv_positions = self.xray_structure().space_group().n_equivalent_positions()
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
        yield (label, xyz, u, u_eq,
               a.occupancy*(a.multiplicity()/n_equiv_positions),
               symbol, a.flags)

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
        olx.Fix('xyz', xyz, name)
      if not (flags.grad_u_iso() or flags.grad_u_aniso()):
        olx.Fix('Uiso', u, name)
      if not flags.grad_occupancy():
        olx.Fix('occu', occu, name)
      u_total += u[0]
      u_average = u_total/i
    #olx.Sel('-u')
    olx.xf_EndUpdate()

  def f_obs_minus_f_calc_map(self, resolution):
    fo2 = self.normal_eqns.fo_sq.average_bijvoet_mates()
    f_obs = fo2.f_sq_as_f()
    f_calc = self.normal_eqns.f_calc.average_bijvoet_mates()
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

  def show_summary(self):
    print "Summary after %i cycles:" %self.cycles.n_iterations
    print "R1 (all data): %.4f for %i reflections" % self.r1_all_data
    print "R1: %.4f for %i reflections I > 2u(I)" % self.r1
    print "wR2 = %.4f, GooF: %.4f" % (
      self.normal_eqns.wR2(), self.normal_eqns.goof())
