from __future__ import division

import os, sys
import olx
import OlexVFS
import time

from my_refine_util import *
from PeriodicTable import PeriodicTable
import olexex
try:
  olx.current_reflection_filename
except:
  olx.current_reflection_filename = None
  olx.current_reflections = None
  olx.current_mask = None

import olex

import time
import cctbx_controller as cctbx_controller
from cctbx import maptbx, miller, uctbx
from libtbx import easy_pickle

from olexFunctions import OlexFunctions
OV = OlexFunctions()

from History import hist


class OlexCctbxAdapter(object):
  def __init__(self):
    if OV.HasGUI():
      sys.stdout.refresh = True
    self._xray_structure = None
    self.olx_atoms = olexex.OlexRefinementModel()
    self.wavelength = self.olx_atoms.exptl.get('radiation', 0.71073)
    self.reflections = None
    self.initialise_reflections()

  def __del__(self):
    sys.stdout.refresh = False

  def xray_structure(self):
    if self._xray_structure is None:
      self._xray_structure = cctbx_controller.create_cctbx_xray_structure(
        self.cell,
        self.space_group,
        self.olx_atoms.iterator(),
        restraint_iterator=self.olx_atoms.restraint_iterator())
    return self._xray_structure

  def initialise_reflections(self, force=False, verbose=False):
    self.cell = self.olx_atoms.getCell()
    self.space_group = str(olx.xf_au_GetCellSymm())
    reflections = olx.HKLSrc()
    if force or reflections != olx.current_reflection_filename:
      olx.current_reflection_filename = reflections
      olx.current_reflections = cctbx_controller.reflections(self.cell, self.space_group, reflections)
    if olx.current_reflections:
      self.reflections = olx.current_reflections
    else:
      olx.current_reflections = cctbx_controller.reflections(self.cell, self.space_group, reflections)
      self.reflections = olx.current_reflections
    merge = self.olx_atoms.model.get('merge')
    if force or merge is None or merge != self.reflections._merge:
      self.reflections.merge(merge=merge)
    omit = self.olx_atoms.model['omit']
    if force or omit is None or omit != self.reflections._omit:
      self.reflections.filter(omit, self.olx_atoms.exptl['radiation'])
    if verbose:
      self.reflections.show_summary()

class OlexCctbxRefine(OlexCctbxAdapter):
  def __init__(self, max_cycles=None, max_peaks=None, verbose=False):
    OlexCctbxAdapter.__init__(self)
    self.verbose = verbose
    self.log = open('%s/%s.log' %(OV.FilePath(), OV.FileName()),'w')
    PT = PeriodicTable()
    self.pt = PT.PeriodicTable()
    self.olx = olx
    self.cycle = 0
    self.tidy = False
    self.auto = False
    self.debug = False
    self.film = False
    self.max_cycles = max_cycles
    self.max_peaks = max_peaks
    self.do_refinement = True
    if OV.HasGUI() and OV.GetParam('snum.refinement.graphical_output'):
      import Analysis
      self.plot = Analysis.smtbx_refine_graph()
    else: self.plot = None

  def run(self):
    t0 = time.time()
    print "++++ Refining using the CCTBX with a maximum of %i cycles++++" %self.max_cycles
    self.refine_with_cctbx()
    asu_mappings = self.xray_structure().asu_mappings(buffer_thickness=3.5)
    #
    scatterers = self.xray_structure().scatterers()
    scattering_types = scatterers.extract_scattering_types()
    pair_asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
    pair_asu_table.add_covalent_pairs(
      scattering_types, exclude_scattering_types=flex.std_string(("H","D")))
    pair_sym_table = pair_asu_table.extract_pair_sym_table()

    print >> self.log, "\nConnectivity table"
    pair_sym_table.show(site_labels=scatterers.extract_labels(), f=self.log)
    print >> self.log, "\nBond lengths"
    self.xray_structure().show_distances(pair_asu_table=pair_asu_table, out=self.log)
    print >> self.log, "\nBond angles"
    self.xray_structure().show_angles(pair_asu_table=pair_asu_table, out=self.log)
    #
    self.post_peaks(self.refinement.f_obs_minus_f_calc_map(0.4))
    self.log.close()

    #cctbxmap_resolution = 0.4
    #cctbxmap_type = OV.FindValue('snum_cctbx_map_type', None)
    #if cctbxmap_type == "--":
      #cctbxmap_type = None
    #else:
      #cctbxmap_resolution = float(OV.FindValue('snum_cctbxmap_resolution'))
    #if cctbxmap_type and cctbxmap_type !='None':
      #self.write_grid_file(cctbxmap_type, cctbxmap_resolution)

    print "++++ Finished in %.3f s" %(time.time() - t0)
    print "Done."

  def refine_with_cctbx(self):
    wavelength = self.olx_atoms.exptl.get('radiation', 0.71073)
    weight = self.olx_atoms.model['weight']
    params = dict(a=0.1, b=0, c=0, d=0, e=0, f=1./3)
    for param, value in zip(params.keys()[:len(weight)], weight):
      params[param] = value
    weighting = xray.weighting_schemes.shelx_weighting(**params)
    self.reflections.show_summary(log=self.log)
    self.refinement = cctbx_controller.refinement(
      f_sq_obs=self.reflections.f_sq_obs_merged,
      xray_structure=self.xray_structure(),
      wavelength=wavelength,
      max_cycles=self.max_cycles,
      max_peaks=self.max_peaks,
      log=self.log,
      weighting=weighting,
    )
    self.refinement.on_cycle_finished = self.feed_olex
    self.refinement.start()
    self.R1 = self.refinement.R1()[0]
    self.wR2, self.GooF = self.refinement.wR2_and_GooF(
      self.refinement.minimisation.minimizer)
    self.update_refinement_info("Starting...")

  def feed_olex(self, structure, minimisation, minimiser):
    self.auto = False
    self.cycle += 1
    #msg = "Refinement Cycle: %i" %(self.cycle)
    self.refinement.show_cycle_summary(minimiser)
    #print msg

    #self.update_refinement_info(msg=msg)
    minimisation.show_sorted_shifts(max_items=10, log=self.log)
    max_shift_site, max_shift_site_scatterer = minimisation.iter_shifts_sites(max_items=1).next()
    print "Max. shift: %.3f %s" %(max_shift_site, max_shift_site_scatterer.label)
    if not minimisation.pre_minimisation:
      max_shift_u, max_shift_u_scatterer = minimisation.iter_shifts_u(max_items=1).next()
      print "Max. dU: %.3f %s" %(max_shift_u, max_shift_u_scatterer.label)
    if self.plot is not None:
      self.plot.observe(max_shift_site, max_shift_site_scatterer)
    if self.film:
      n = str(self.cycle)
      if int(n) < 10:
        n = "0%s" %n
      olx.Picta(r"%s0%s.bmp 1" %(self.film, n))
    reset_refinement = False
    ## Feed Model
    u_total  = 0
    u_atoms = []
    i = 1
    for name, xyz, u, ueq, symbol in self.refinement.iter_scatterers():
      if len(u) == 6:
        u_trans = (u[0], u[1], u[2], u[5], u[4], u[3])
      else:
        u_trans = u
      id = self.olx_atoms.id_for_name[name]
      olx.xf_au_SetAtomCrd(id, *xyz)
      olx.xf_au_SetAtomU(id, *u_trans)
      u_total += u[0]
      if self.tidy:
        if u[0] > 0.09:
          olx.Name("%s Q" %name)
      u_average = u_total/i

    if reset_refinement:
      raise Exception("Atoms with SillyU Deleted")

    if self.auto:
      for name, xyz, u, symbol in self.refinement.iter_scatterers():
        if symbol == 'H': continue
        id = self.olx_atoms.id_for_name[name]
        selbst_currently_present = curr_formula.get(symbol, 0)
        #print name, u[0]
        if u[0] < u_average * 0.8:
#          print "  ------> PROMOTE?"
          promote_to = element_d[symbol].get('+1', symbol)
          currently_present = curr_formula.get(promote_to, 0)
          max_possible = element_d[promote_to].get('max_number')
          if self.debug: olx.Sel(name)
          if self.debug: print "Promote %s to a %s. There are %.2f present, and  %.2f are allowed" %(name, promote_to, currently_present, max_possible),
          if currently_present < max_possible:
            olx.xf_au_SetAtomlabel(id, promote_to)
            curr_formula[promote_to] = currently_present + 1
            curr_formula[symbol] = selbst_currently_present - 1
            if self.debug: print " OK"
          else:
            if self.debug: print " X"
        if u[0] > u_average * 1.5:
#          print "  DEMOTE? <-------"
          #reset_refinement = True
          demote_to = element_d[symbol].get('-1', symbol)
          currently_present = curr_formula.get(demote_to, 0)
          max_possible = element_d[demote_to].get('max_number')
          if self.debug: olx.Sel(name)
          if self.debug: print "Demote %s to a %s. There are %.2f present, and %.2f are allowed" %(name, demote_to, currently_present, max_possible),
          if curr_formula.get(demote_to, 0) < element_d[demote_to].get('max_number'):
            olx.xf_au_SetAtomlabel(id, demote_to)
            curr_formula[demote_to] = currently_present + 1
            curr_formula[symbol] = selbst_currently_present - 1
            if self.debug: print "OK"
          else:
            if self.debug: print " X"
    #olx.Sel('-u')
    olx.xf_EndUpdate()
    if reset_refinement:
      raise Exception("Atoms promoted")

  def post_peaks(self, fft_map):
    from cctbx import maptbx
    from  libtbx.itertbx import izip
    fft_map.apply_volume_scaling()
    peaks = fft_map.peak_search(
      parameters=maptbx.peak_search_parameters(
        peak_search_level=3,
        interpolate=False,
        #peak_cutoff=0.1,
        min_distance_sym_equiv=1.0,
        max_clusters=30),
      verify_symmetry=False
      ).all()
    #peaks = self.refinement.peak_search()
    #peaks.show_sorted()
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

  def update_refinement_info(self, msg="Unknown"):
    import htmlMaker
    R1, n_reflections = self.refinement.R1()
    R1_all_data, n_reflections_unique = self.refinement.R1(all_data=True)
    wR2 = self.wR2
    GooF = self.GooF
    #htmlMaker.make_refinement_data_html(R1=R1,
                                        #n_reflections=n_reflections,
                                        #R1_all_data=R1_all_data,
                                        #n_reflections_unique=n_reflections_unique,
                                        #wR2=wR2,
                                        #GooF=GooF)
    txt = "Last refinement with <b>smtbx-refine</b>: No refinement info available yet.<br>Status: %s" %msg
    OlexVFS.write_to_olex('refinedata.htm', txt)

  def write_grid_file(self, type, resolution):
    import olex_xgrid
    if type == "DIFF":
      m = self.refinement.get_difference_map(resolution)
    elif type == "FOBS":
      m = self.refinement.get_f_obs_map(resolution)
    else:
      return
    s = m.last()
    olex_xgrid.Init(s[0], s[1], s[2])
    for i in range (s[0]-1):
      for j in range (s[1]-1):
        for k in range (s[2]-1):
          olex_xgrid.SetValue( i,j,k,m[i,j,k])
    olex_xgrid.InitSurface(True)

class FullMatrixRefine(OlexCctbxRefine):
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
    wavelength = self.olx_atoms.exptl.get('radiation', 0.71073)

    filepath = OV.StrDir()
    self.f_mask = None
    if OV.GetParam("snum.refinement.use_solvent_mask"):
      modified_hkl_path = "%s/%s_modified.hkl" %(OV.FilePath(), OV.FileName())
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
      elif os.path.exists("%s/f_mask.pickle" %filepath):
        self.f_mask = easy_pickle.load("%s/f_mask.pickle" %filepath)
      if self.f_mask is None:
        print "No mask present"
    normal_eqns = least_squares.normal_equations(
      self.xray_structure(), self.reflections.f_sq_obs_filtered,
      f_mask=self.f_mask,
      weighting_scheme="default")
    objectives = []
    scales = []
    try:
      for i in range (self.max_cycles):
        normal_eqns.build_up()
        objectives.append(normal_eqns.objective)
        scales.append(normal_eqns.scale_factor)
        normal_eqns.solve_and_apply_shifts()
        shifts = normal_eqns.shifts
        self.feed_olex()
        self.scale_factor = scales[-1]
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
      self.post_peaks(self.f_obs_minus_f_calc_map(0.4), max_peaks=self.max_peaks)
    finally:
      sys.stdout.refresh = True

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
        yield label, xyz, u, u_eq, symbol

    for name, xyz, u, ueq, symbol in iter_scatterers():
      if len(u) == 6:
        u_trans = (u[0], u[1], u[2], u[5], u[4], u[3])
      else:
        u_trans = u

      id = self.olx_atoms.id_for_name[name]
      olx.xf_au_SetAtomCrd(id, *xyz)
      olx.xf_au_SetAtomU(id, *u_trans)
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
    fft_map.apply_volume_scaling()
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

  def calculate_residuals(self, f_obs):
    f_calc = self.f_model(f_obs)
    ls_function = xray.unified_least_squares_residual(f_obs)
    ls = ls_function(f_calc, compute_derivatives=False)
    k = ls.scale_factor()
    fc = flex.abs(f_calc.data())
    fo = flex.abs(f_obs.data())
    return flex.abs(k*fc - fo)

  def R1(self, all_data=False):
    f_obs = self.reflections.f_sq_obs_filtered.f_sq_as_f()
    if not all_data:
      strong = f_obs.data() > 4*f_obs.sigmas()
      f_obs = f_obs.select(strong)
    R1 = flex.sum(self.calculate_residuals(f_obs)) / flex.sum(f_obs.data())
    return R1, f_obs.size()

  def wR2_and_GooF(self):
    f_sq_obs = self.reflections.f_sq_obs_merged
    f_calc = self.f_model(f_sq_obs)
    ls_function = xray.unified_least_squares_residual(
      f_sq_obs,
      #weighting=xray.weighting_schemes.shelx_weighting()
      weighting=self.weighting
    )
    ls = ls_function(f_calc, compute_derivatives=False)
    weights = ls_function.weighting().weights
    k = ls.scale_factor()
    f_sq_calc = f_calc.norm()
    fc_sq = f_sq_calc.data()
    fo_sq = f_sq_obs.data()
    wR2 = math.sqrt(flex.sum(weights * flex.pow2(fo_sq - k * fc_sq)) /
                    flex.sum(weights * flex.pow2(fo_sq)))
    GooF = math.sqrt(flex.sum(weights * flex.pow2(fo_sq - k * fc_sq)) /
                     (fo_sq.size() - minimizer.n()))
    return wR2, GooF

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
    pickle_path = '%s/%s.pickle' %(filepath, map_type)
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
      modified_hkl_path = "%s/%s_modified.hkl" %(OV.FilePath(), OV.FileName())
      if os.path.exists(modified_hkl_path):
        os.remove(modified_hkl_path)
        original_hklsrc = OV.GetParam('snum.masks.original_hklsrc')
        if OV.HKLSrc() == modified_hkl_path and original_hklsrc is not None:
          OV.HKLSrc(original_hklsrc)
          OV.UpdateHtml()
          # we need to reinitialise reflections
          self.initialise_reflections()
      xs = self.xray_structure()
      fo_sq = self.reflections.f_sq_obs_filtered.average_bijvoet_mates()
      mask = masks.mask(xs, fo_sq)
      self.time_compute = time_log("computation of mask").start()
      mask.compute(solvent_radius=self.params.solvent_radius,
                   shrink_truncation_radius=self.params.shrink_truncation_radius,
                   resolution_factor=self.params.resolution_factor,
                   atom_radii_table={'C':1.70, 'B':1.63, 'N':1.55, 'O':1.52},
                   use_space_group_symmetry=True)
      self.time_compute.stop()
      self.time_f_mask = time_log("f_mask calculation").start()
      f_mask = mask.structure_factors()
      self.time_f_mask.stop()
      olx.current_mask = mask
      if mask.flood_fill.n_voids() > 0:
        easy_pickle.dump('%s/mask.pickle' %filepath, mask.mask.data)
        easy_pickle.dump('%s/f_mask.pickle' %filepath, mask.f_mask())
        easy_pickle.dump('%s/f_model.pickle' %filepath, mask.f_model())
      mask.show_summary()
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
    if mask.flood_fill.n_voids() > 0 and OV.HasGUI():
      write_grid_to_olex(output_data)
    self.time_write_grid.stop()

  def __del__(self):
    OV.DeleteBitmap("working")

OV.registerFunction(OlexCctbxMasks)

class OlexCctbxGraphs(OlexCctbxAdapter):
  def __init__(self, graph, *args, **kwds):
    OlexCctbxAdapter.__init__(self)
    if self.reflections is None:
      raise RuntimeError, "There was an error reading the reflection file."
    self.graph = graph

    bitmap = 'working'
    OV.CreateBitmap(bitmap)

    try:
      if graph == "wilson":
        self.xy_plot = cctbx_controller.wilson_statistics(self.xray_structure(), self.reflections, **kwds)

      elif graph == "completeness":
        self.xy_plot = cctbx_controller.completeness_statistics(self.reflections, self.wavelength, **kwds)

      elif graph == "cumulative":
        self.xy_plot = cctbx_controller.cumulative_intensity_distribution(self.reflections, **kwds)

      elif graph == "f_obs_f_calc":
        twinning = self.olx_atoms.model.get('twin')
        self.xy_plot = cctbx_controller.f_obs_vs_f_calc(self.xray_structure(), self.reflections, twinning=twinning, **kwds)

      elif graph == "f_obs_over_f_calc":
        self.xy_plot = cctbx_controller.f_obs_over_f_calc(self.xray_structure(), self.reflections, self.wavelength, **kwds)

      elif graph == "sys_absent":
        self.xy_plot = cctbx_controller.sys_absent_intensity_distribution(self.reflections)

      elif graph == "normal_probability":
        weight = self.olx_atoms.model['weight']
        params = dict(a=0.1, b=0, c=0, d=0, e=0, f=1./3)
        for param, value in zip(params.keys()[:len(weight)], weight):
          params[param] = value
        weighting = xray.weighting_schemes.shelx_weighting(**params)
        self.xy_plot = cctbx_controller.normal_probability_plot(
          self.xray_structure(), self.reflections, weighting,
          #distribution=cctbx_controller.distributions.students_t_distribution(5),
          ).xy_plot_info()
    except Exception, err:
      raise Exception, err
    finally:
      OV.DeleteBitmap(bitmap)

class OlexCctbxTwinLaws(OlexCctbxAdapter):

  def __init__(self):
    OlexCctbxAdapter.__init__(self)
    self.run()

  def run(self):
    from PilTools import MatrixMaker
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
      image_name, img  = a.make_3x3_matrix_image(name, twin_law, txt)
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
      name = self.twin_laws_d[run].get('name', "XX")
      href = 'spy.on_twin_image_click(%s)'
      href = 'spy.revert_history(%s)>>HtmlReload' %(self.twin_laws_d[i].get('history'))
      law_txt = "<a href='%s'><zimg src=%s></a>&nbsp;" %(href, image_name)
      self.twin_law_gui_txt += "%s" %(law_txt)

      html += '''
<a href='%s' target='Apply this twin law'><zimg border="0" src="%s"></a>&nbsp;
    ''' %(href, image_name)
    html += "</td></tr>"
    OV.write_to_olex('twinning-result.htm', html, False)
    OV.htmlReload()
#    self.make_gui()

  def run_backup_shelx(self):
    self.filename = olx.FileName()
    olx.DelIns("TWIN")
    olx.DelIns("BASF")
    olx.File("notwin.ins")

  def run_twin_ref_shelx(self, law):
    print "Testing: %s" %str(law)
    law_ins = ""
    for i in xrange(9):
      law_ins += " %s" %str(law[i])
    olx.Atreap("-b notwin.ins")
    olx.User("'%s'" %olx.FilePath())
    if law != (1, 0, 0, 0, 1, 0, 0, 0, 1):
      OV.AddIns("TWIN %s" %law_ins)
      OV.AddIns("BASF %s" %"0.5")
    olx.LS('CGLS 1')
    olx.File("%s.ins" %self.filename)
    rFile = open(olx.FileFull(), 'r')
    f_data = rFile.readlines()
    #prg = OV.GetParam('snum.refinement.program') ## This currently only works with SHELX
    prg = "ShelXL"
    try:
      olx.Exec(r"%s '%s'" %(prg, olx.FileName()))
    except:
      prg = "XL"
      olx.Exec(r"%s '%s'" %(prg, olx.FileName()))

    olx.WaitFor('process')
    olx.Atreap(r"-b %s/%s.res" %(olx.FilePath(), olx.FileName()))
    r = olx.Lst("R1")
    basf = olx.Lst("BASF")
    if r != 0:
      res = hist.create_history()
#      history_refinement = res.split(";")[1]
#      history_solution = res.split(";")[0]
    return r, basf, f_data, res

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
