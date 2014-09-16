from __future__ import division

import math, os, sys

from cctbx_olex_adapter import OlexCctbxAdapter, OlexCctbxMasks, rt_mx_from_olx

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import olx
import olex_core

from cctbx.array_family import flex
from cctbx import adptbx, maptbx, miller, sgtbx, uctbx, xray

import iotbx.cif.model

from libtbx import easy_pickle, utils

from scitbx.lstbx import normal_eqns_solving

from smtbx.refinement import restraints
from smtbx.refinement import least_squares
from smtbx.refinement import constraints
from smtbx.refinement.constraints import geometrical
from smtbx.refinement.constraints import adp
from smtbx.refinement.constraints import site
from smtbx.refinement.constraints import occupancy
from smtbx.refinement.constraints import rigid
import smtbx.utils

solvers = {
  'Gauss-Newton': normal_eqns_solving.naive_iterations_with_damping_and_shift_limit,
  'Levenberg-Marquardt': normal_eqns_solving.levenberg_marquardt_iterations
}
solvers_default_method = 'Gauss-Newton'

class olex2_normal_eqns(least_squares.crystallographic_ls):
  log = None

  def __init__(self, observations, reparametrisation, olx_atoms, **kwds):
    self.olx_atoms = olx_atoms
    least_squares.crystallographic_ls.__init__(
      self, observations, reparametrisation, initial_scale_factor=OV.GetOSF(), **kwds)

  def step_forward(self):
    self.xray_structure_pre_cycle = self.xray_structure.deep_copy_scatterers()
    least_squares.crystallographic_ls.step_forward(self)
    self.show_cycle_summary(log=self.log)
    self.show_sorted_shifts(max_items=10, log=self.log)
    self.restraints_manager.show_sorted(
      self.xray_structure, f=self.log)
    self.show_cycle_summary()
    self.feed_olex()
    return self

  def show_cycle_summary(self, log=None):
    if log is None: log = sys.stdout
    print >> log, "wR2 = %.4f for %i data and %i parameters" %(
      self.wR2(), self.observations.fo_sq.size(),
      self.reparametrisation.n_independents)
    print >> log, "GooF = %.4f" %(self.goof(),)
    max_shift_site = self.max_shift_site()
    OV.SetParam('snum.refinement.max_shift_site', max_shift_site[0])
    OV.SetParam('snum.refinement.max_shift_site_atom', max_shift_site[1].label)
    max_shift_u = self.max_shift_u()
    OV.SetParam('snum.refinement.max_shift_u', max_shift_u[0])
    OV.SetParam('snum.refinement.max_shift_u_atom', max_shift_u[1].label)
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

  def feed_olex(self):
    ## Feed Model
    u_atoms = []
    i = 1

    def iter_scatterers():
      n_equiv_positions = self.xray_structure.space_group().n_equivalent_positions()
      for a in self.xray_structure.scatterers():
        label = a.label
        xyz = a.site
        symbol = a.scattering_type
        if a.flags.use_u_iso():
          u = (a.u_iso,)
          u_eq = u[0]
        if a.flags.use_u_aniso():
          u_cif = adptbx.u_star_as_u_cart(self.xray_structure.unit_cell(), a.u_star)
          u = u_cif
          u_eq = adptbx.u_star_as_u_iso(self.xray_structure.unit_cell(), a.u_star)
        yield (label, xyz, u, u_eq,
               a.occupancy*(a.multiplicity()/n_equiv_positions),
               symbol, a.flags)
    this_atom_id = 0
    for name, xyz, u, ueq, occu, symbol, flags in iter_scatterers():
      if len(u) == 6:
        u_trans = (u[0], u[1], u[2], u[5], u[4], u[3])
      else:
        u_trans = u

      id = self.olx_atoms.atom_ids[this_atom_id]
      this_atom_id += 1
      olx.xf.au.SetAtomCrd(id, *xyz)
      olx.xf.au.SetAtomU(id, *u_trans)
      olx.xf.au.SetAtomOccu(id, occu)
    #update OSF
    OV.SetOSF(self.scale_factor())
    #update FVars
    for var in self.shared_param_constraints:
      if var[3]:
        OV.SetFVar(var[0], var[1].value.value*var[2])
      else:
        OV.SetFVar(var[0], 1.0-var[1].value.value*var[2])
    #update BASF
    if self.twin_fractions is not None:
      basf = [fraction.value
                      for fraction in self.twin_fractions
                      if fraction.grad]
      if basf: olx.AddIns('BASF', *basf)
    #update EXTI
    if self.reparametrisation.extinction.grad:
      OV.SetExtinction(self.reparametrisation.extinction.value)
    for (i,r) in enumerate(self.shared_rotated_adps):
      if r.refine_angle:
        olx.xf.rm.UpdateCR('olex2.constraint.rotated_adp', i, r.angle.value*180/math.pi)
    olx.xf.EndUpdate()


class FullMatrixRefine(OlexCctbxAdapter):
  def __init__(self, max_cycles=None, max_peaks=5, verbose=False, on_completion=None):
    OlexCctbxAdapter.__init__(self)
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
    sec_ch2_treatment = OV.GetParam('snum.smtbx.secondary_ch2_angle')
    if sec_ch2_treatment == 'idealise':
      self.idealise_secondary_xh2_angle = True
    elif sec_ch2_treatment == 'refine':
      self.refine_secondary_xh2_angle = True

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
      else:
        fo_sq = self.reflections.f_sq_obs_filtered
        if not fo_sq.space_group().is_centric():
          self.f_mask = self.f_mask.generate_bijvoet_mates()
        self.f_mask = self.f_mask.common_set(fo_sq)
    restraints_manager = self.restraints_manager()
    #put shared parameter constraints first - to allow proper bookeeping of
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
      self.extinction.expression = 'Fc^*^=kFc[1+0.001xFc^2^\l^3^/sin(2\q)]^-1/4^'
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

    weight = self.olx_atoms.model['weight']
    params = dict(a=0.1, b=0,
                  #c=0, d=0, e=0, f=1./3,
                  )
    for param, value in zip(params.keys()[:min(2,len(weight))], weight):
      params[param] = value
    weighting = least_squares.mainstream_shelx_weighting(**params)
    #self.reflections.f_sq_obs_filtered = self.reflections.f_sq_obs_filtered.sort(
    #  by_value="resolution")
    self.normal_eqns = olex2_normal_eqns(
      self.observations,
      self.reparametrisation,
      self.olx_atoms,
      f_mask=self.f_mask,
      restraints_manager=restraints_manager,
      weighting_scheme=weighting,
      log=self.log
    )
    self.normal_eqns.shared_param_constraints = self.shared_param_constraints
    self.normal_eqns.shared_rotated_adps = self.shared_rotated_adps
    method = OV.GetParam('snum.refinement.method')
    iterations = solvers.get(method)
    if iterations == None:
      method = solvers_default_method
      iterations = solvers.get(method)
      print "WARNING: unsupported method: '" + method + "' is replaced by '" +\
        solvers_default_method + "'"
    assert iterations is not None
    try:
      damping = OV.GetDampingParams()
      self.cycles = iterations(self.normal_eqns,
                               n_max_iterations=self.max_cycles,
                               track_all=True,
                               damping_value=damping[0],
                               max_shift_over_esd=damping[1],
                               convergence_as_shift_over_esd=1e-3,
                               gradient_threshold=1e-8,
                               step_threshold=1e-8)
                               #gradient_threshold=1e-5,
                               #step_threshold=1e-5)
      self.scale_factor = self.cycles.scale_factor_history[-1]
      self.covariance_matrix_and_annotations=self.normal_eqns.covariance_matrix_and_annotations()
      self.twin_covariance_matrix = self.normal_eqns.covariance_matrix(
        jacobian_transpose=self.reparametrisation.jacobian_transpose_matching(
          self.reparametrisation.mapping_to_grad_fc_independent_scalars))
      self.export_var_covar(self.covariance_matrix_and_annotations)
      self.r1 = self.normal_eqns.r1_factor(cutoff_factor=2)
      self.r1_all_data = self.normal_eqns.r1_factor()
      self.check_flack()
      if self.flack:
        OV.SetParam('snum.refinement.flack_str', self.flack)
      #extract SU on BASF and extinction
      diag = self.twin_covariance_matrix.matrix_packed_u_diagonal()
      dlen = len(diag)
      if self.reparametrisation.extinction.grad:
        #extinction is the last parameter after the twin fractions
        su = math.sqrt(diag[dlen-1])
        OV.SetExtinction(self.reparametrisation.extinction.value, su)
        dlen -= 1
      try: #remove me for new exe!
        for i in xrange(dlen):
          olx.xf.rm.BASF(i, olx.xf.rm.BASF(i), math.sqrt(diag[i]))
      except:
        pass
    except RuntimeError, e:
      if str(e).startswith("cctbx::adptbx::debye_waller_factor_exp: max_arg exceeded"):
        print "Refinement failed to converge"
      elif "SCITBX_ASSERT(!cholesky.failure) failure" in str(e):
        print "Cholesky failure"
      else:
        print "Refinement failed"
        import traceback
        traceback.print_exc()
      self.failure = True
    else:
      fo_minus_fc = self.f_obs_minus_f_calc_map(0.4)
      fo_minus_fc.apply_volume_scaling()
      self.diff_stats = fo_minus_fc.statistics()
      self.post_peaks(fo_minus_fc, max_peaks=self.max_peaks)
      self.show_summary()
      self.show_comprehensive_summary(log=self.log)
      block_name = OV.FileName().replace(' ', '')
      f = open(OV.file_ChangeExt(OV.FileFull(), 'cif'), 'w')
      cif = iotbx.cif.model.cif()
      cif[block_name] = self.as_cif_block()
      print >> f, cif
      f.close()
      if not OV.GetParam('snum.refinement.cifmerge_after_refinement', False):
        OV.CifMerge(None, True, False)
      self.output_fcf()
      new_weighting = weighting.optimise_parameters(
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
        from smtbx import absolute_structure
        flack = absolute_structure.flack_analysis(
          self.normal_eqns.xray_structure,
          self.observations,
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
    refinement_refs = self.normal_eqns.observations.fo_sq
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
      uctbx.d_as_d_star_sq(refinement_refs.d_max_min()[1]), self.wavelength, deg=True)
    completeness_full = refinement_refs.resolution_filter(
      d_min=uctbx.two_theta_as_d(two_theta_full, self.wavelength, deg=True)).completeness()
    completeness_theta_max = refinement_refs.completeness()
    OV.SetParam("snum.refinement.max_shift_over_esd", None)
    OV.SetParam("snum.refinement.max_shift_over_esd_atom", None)

    shifts_over_su = flex.abs(self.normal_eqns.step() /
      flex.sqrt(self.normal_eqns.covariance_matrix().matrix_packed_u_diagonal()))
    try:
      jac_tr = self.normal_eqns.reparametrisation.jacobian_transpose_matching_grad_fc()
      shifts = jac_tr.transpose() * shifts_over_su
      max_shift_idx = 0
      for i, s in enumerate(shifts):
        if (shifts[max_shift_idx] < s):
          max_shift_idx = i
      print("Largest shift/esd is %.4f for %s" %(
            shifts[max_shift_idx],
            self.covariance_matrix_and_annotations.annotations[max_shift_idx]))
      OV.SetParam("snum.refinement.max_shift_over_esd",
        shifts[max_shift_idx])
      OV.SetParam("snum.refinement.max_shift_over_esd_atom",
        self.covariance_matrix_and_annotations.annotations[max_shift_idx].split('.')[0])
    except:
      pass
    # cell parameters and errors
    cell_params = self.olx_atoms.getCell()
    cell_errors = self.olx_atoms.getCellErrors()
    from scitbx import matrix
    cell_vcv = flex.pow2(matrix.diag(cell_errors).as_flex_double_matrix())
    xs = self.xray_structure()
    cif_block = xs.as_cif_block(
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
    htabs = [i for i in self.olx_atoms.model['info_tables'] if i['type'] == 'HTAB']
    equivs = self.olx_atoms.model['equivalents']
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
    fmt = "%.4f"
    cif_block['_chemical_formula_moiety'] = olx.xf.latt.GetMoiety()
    cif_block['_chemical_formula_sum'] = olx.xf.au.GetFormula()
    cif_block['_chemical_formula_weight'] = olx.xf.au.GetWeight()
    cif_block['_exptl_absorpt_coefficient_mu'] = olx.xf.GetMu()
    cif_block['_exptl_crystal_density_diffrn'] = "%.4f" %xs.crystal_density()
    cif_block['_exptl_crystal_F_000'] \
             = "%.4f" %xs.f_000(include_inelastic_part=True)
    #
    fo2 = self.reflections.f_sq_obs
    merging = self.reflections.merging
    min_d_star_sq, max_d_star_sq = refinement_refs.min_max_d_star_sq()
    (h_min, k_min, l_min), (h_max, k_max, l_max) = fo2.min_max_indices()
    cif_block['_diffrn_measured_fraction_theta_full'] = fmt % completeness_full
    cif_block['_diffrn_measured_fraction_theta_max'] = fmt % completeness_theta_max
    cif_block['_diffrn_radiation_wavelength'] = self.wavelength
    cif_block['_diffrn_radiation_type'] = self.get_radiation_type()
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
    cif_block['_refine_ls_goodness_of_fit_ref'] = fmt % self.normal_eqns.goof()
    #cif_block['_refine_ls_hydrogen_treatment'] =
    cif_block['_refine_ls_matrix_type'] = 'full'
    cif_block['_refine_ls_number_constraints'] = self.n_constraints
    cif_block['_refine_ls_number_parameters'] = self.reparametrisation.n_independents
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

  def output_fcf(self):
    try: list_code = int(olx.Ins('list'))
    except: list_code = None
    if list_code is None: return
    cif = iotbx.cif.model.cif()
    if list_code == 4:
      fc_sq = self.normal_eqns.fc_sq.sort(by_value="packed_indices")
      fo_sq = self.normal_eqns.observations.fo_sq.sort(by_value="packed_indices")
      fo_sq = fo_sq.customized_copy(
        data=fo_sq.data()*(1/self.scale_factor),
        sigmas=fo_sq.sigmas()*(1/self.scale_factor))
      mas_as_cif_block = iotbx.cif.miller_arrays_as_cif_block(
        fc_sq, array_type='calc')
      mas_as_cif_block.add_miller_array(fo_sq, array_type='meas')
      _refln_include_status = fc_sq.array(data=flex.std_string(fc_sq.size(), 'o'))
      mas_as_cif_block.add_miller_array(
        #_refln_include_status, column_name='_refln_include_status')
        _refln_include_status, column_name='_refln_observed_status') # checkCIF only accepts this one
      fmt_str="%4i"*3 + "%12.2f"*2 + "%10.2f" + " %s"
    elif list_code == 3:
      if self.hklf_code == 5:
        fo_sq, fc = self.get_fo_sq_fc()
        fo = fo_sq.as_amplitude_array().sort(by_value="packed_indices")
      else:
        fc = self.normal_eqns.f_calc.customized_copy(anomalous_flag=False)
        fo_sq = self.normal_eqns.observations.fo_sq.customized_copy(
          data=self.normal_eqns.observations.fo_sq.data()*(1/self.scale_factor),
          sigmas=self.normal_eqns.observations.fo_sq.sigmas()*(1/self.scale_factor),
          anomalous_flag=False)
        fo_sq = fo_sq.eliminate_sys_absent().merge_equivalents(algorithm="shelx").array()
        fo = fo_sq.as_amplitude_array().sort(by_value="packed_indices")
        fc, fo = fc.map_to_asu().common_sets(fo)
      mas_as_cif_block = iotbx.cif.miller_arrays_as_cif_block(
        fo, array_type='meas')
      mas_as_cif_block.add_miller_array(
        fc, column_names=['_refln_A_calc', '_refln_B_calc'])
      fmt_str="%4i"*3 + "%12.4f"*4
    else:
      print "list code %i not supported" %list_code
      return
    # cctbx could make e.g. 1.001(1) become 1.0010(10), so use Olex2 values for cell
    cif_block = iotbx.cif.model.block()
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
    f = open(OV.file_ChangeExt(OV.FileFull(), 'fcf'), 'w')
    cif.show(out=f, loop_format_strings={'_refln':fmt_str})
    f.close()

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
    for i, var in enumerate(vars):
      refs = var['references']
      as_var = []
      as_var_minus_one = []
      eadp = []
      for ref in refs:
        if ref['index'] == 4 and ref['relation'] == "var":
          as_var.append((ref['id'], ref['k']))
        if ref['index'] == 4 and ref['relation'] == "one_minus_var":
          as_var_minus_one.append((ref['id'], ref['k']))
        if ref['index'] == 5 and ref['relation'] == "var":
          eadp.append(ref['id'])
      if (len(as_var) + len(as_var_minus_one)) != 0:
        if len(eadp) != 0:
          print "Invalid variable use - mixes occupancy and U"
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
          'bond_length' : bond_length,
          'constrained_site_indices':dependent
          }
        if m == 2:
          if self.idealise_secondary_xh2_angle:
            kwds['angle'] = 109.47*math.pi/180
          elif self.refine_secondary_xh2_angle:
            kwds['flapping'] = True
        current = constraint_type(**kwds)
        geometrical_constraints.append(current)

    return geometrical_constraints

  def export_var_covar(self, matrix):
    wFile = open("%s/%s.vcov" %(OV.FilePath(),OV.FileName()),'wb')
    wFile.write("VCOV\n")
    wFile.write(" ".join(matrix.annotations) + "\n")
    for item in matrix.matrix:
      wFile.write(str(item) + " ")
    wFile.close()

  def f_obs_minus_f_calc_map(self, resolution):
    scale_factor = self.scale_factor
    if self.hklf_code == 5:
      fo2, f_calc = self.get_fo_sq_fc()
    else:
      fo2 = self.normal_eqns.observations.fo_sq.average_bijvoet_mates()
      if( self.twin_components is not None
        and self.twin_components[0].twin_law != sgtbx.rot_mx((-1,0,0,0,-1,0,0,0,-1))):
        import cctbx_controller
        hemihedral_twinning = cctbx_controller.hemihedral_twinning(
          self.twin_components[0].twin_law.as_double(), miller_set=fo2)
        #fo2 = hemihedral_twinning.detwin_with_twin_fraction(
          #fo2, self.twin_components[0].twin_fraction)
        f_calc = hemihedral_twinning.twin_complete_set.structure_factors_from_scatterers(
          self.xray_structure()).f_calc()
        val = self.twin_components[0].value
        if val < 0:
          val = 0.001
        fo2 = hemihedral_twinning.detwin_with_model_data(
          fo2, f_calc, val)
        f_calc = f_calc.common_set(fo2)
      else:
        f_calc = self.normal_eqns.f_calc.average_bijvoet_mates()
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
    olx.Kill('$Q', '-au')
    for xyz, height in izip(peaks.sites(), peaks.heights()):
      if i < 3:
        if self.verbose: print "Position of peak %s = %s, Height = %s" %(i, xyz, height)
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
    if log is None: log = sys.stdout
    print >> log, str(self.cycles)
    print >> log, "Summary after %i cycles:" %self.cycles.n_iterations
    print >> log, "R1 (all data): %.4f for %i reflections" % self.r1_all_data
    print >> log, "R1: %.4f for %i reflections I >= 2u(I)" % self.r1
    print >> log, "wR2 = %.4f, GooF: %.4f" % (
      self.normal_eqns.wR2(), self.normal_eqns.goof())
    print >> log, "Difference map: max=%.2f, min=%.2f" %(
      self.diff_stats.max(), self.diff_stats.min())
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
    for i in range(result.fo_sq.size()):
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

