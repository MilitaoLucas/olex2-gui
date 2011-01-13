from __future__ import division

import os, sys
import olx
import OlexVFS
import time
import math
from cStringIO import StringIO

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

from cctbx import sgtbx, xray
from cctbx.array_family import flex


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
      self.twin_law = [int(twinning['matrix'][j][i])
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
        restraints_iter=restraints_iter,
        constraints_iter=None #self.olx_atoms.constraints_iterator()
      )
      if construct_restraints:
        from smtbx.refinement import restraints
        proxies = create_cctbx_xray_structure.restraint_proxies()
        kwds = dict([(key+"_proxies", value) for key, value in proxies.iteritems()])
        self._restraints_manager = restraints.manager(**kwds)
        self.constraints = create_cctbx_xray_structure.builder.constraints
      self._xray_structure = create_cctbx_xray_structure.structure()

      table = ("n_gaussian", "it1992", "wk1995")[1]
      self._xray_structure.scattering_type_registry(
        table=table, d_min=self.reflections.f_sq_obs.d_min())
      if self.reflections._merge < 4:
        from cctbx.eltbx import wavelengths
        self._xray_structure.set_inelastic_form_factors(
          self.wavelength, ("sasaki", "henke")[0])
    return self._xray_structure

  def restraints_manager(self):
    if self._restraints_manager is None:
      self.xray_structure(construct_restraints=True)
    return self._restraints_manager

  def initialise_reflections(self, force=False, verbose=False):
    self.cell = self.olx_atoms.getCell()
    self.space_group = "hall: "+str(olx.xf_au_GetCellSymm("hall"))
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
             ignore_inversion_twin=False,
             algorithm="direct"):
    assert self.xray_structure().scatterers().size() > 0, "n_scatterers > 0"
    if ignore_inversion_twin and self.twin_law == [-1,0,0,0,-1,0,0,0,-1]:
      apply_twin_law = False
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
  def __init__(self, probability_plot_slope=None, use_fcf=False):
    OlexCctbxAdapter.__init__(self)
    if probability_plot_slope is not None:
      probability_plot_slope = float(probability_plot_slope)
    if use_fcf:
      fcf_path = OV.file_ChangeExt(OV.FileFull(), "fcf")
      if not os.path.exists(fcf_path):
        print "No fcf file is present"
        return
      reflections = miller.array.from_cif(file_path=fcf_path)
      fo2 = reflections['_refln_F_squared_meas']
      fc2 = reflections['_refln_F_squared_calc']
      fc = fc2.f_sq_as_f().phase_transfer(flex.double(fc2.size(), 0))
      scale = 1
    else:
      fo2 = self.reflections.f_sq_obs_filtered
      fc = self.f_calc(miller_set=fo2, ignore_inversion_twin=True)
      weights = self.compute_weights(fo2, fc)
      scale = fo2.scale_factor(fc, weights=weights)
    if not fo2.anomalous_flag():
      print "No Bijvoet pairs"
      return
    absolute_structure.hooft_analysis.__init__(
      self, fo2, fc, probability_plot_slope=probability_plot_slope, scale_factor=scale)
    self.show()

OV.registerFunction(hooft_analysis)

class students_t_hooft_analysis(OlexCctbxAdapter, absolute_structure.students_t_hooft_analysis):
  def __init__(self, nu=None, use_fcf=False):
    OlexCctbxAdapter.__init__(self)
    if use_fcf:
      fcf_path = OV.file_ChangeExt(OV.FileFull(), "fcf")
      if not os.path.exists(fcf_path):
        print "No fcf file is present"
        return
      reflections = miller.array.from_cif(file_path=fcf_path)
      fo2 = reflections['_refln_F_squared_meas']
      fc2 = reflections['_refln_F_squared_calc']
      fc = fc2.f_sq_as_f().phase_transfer(flex.double(fc2.size(), 0))
      scale = 1
    else:
      fo2 = self.reflections.f_sq_obs_filtered
      fc = self.f_calc(miller_set=fo2, ignore_inversion_twin=True)
      weights = self.compute_weights(fo2, fc)
      scale = fo2.scale_factor(fc, weights=weights)
    if not fo2.anomalous_flag():
      print "No Bijvoet pairs"
      return
    analysis = absolute_structure.hooft_analysis(fo2, fc, scale_factor=scale)
    bijvoet_diff_plot = absolute_structure.bijvoet_differences_probability_plot(analysis)
    if nu is not None:
      nu = float(nu)
    else:
      nu = absolute_structure.maximise_students_t_correlation_coefficient(
        bijvoet_diff_plot.y, 1, 101)
    print "Student's t nu: %.1f" %nu
    absolute_structure.students_t_hooft_analysis.__init__(
      self, fo2, fc, nu, scale_factor=scale)
    self.show()

OV.registerFunction(students_t_hooft_analysis)


class OlexCctbxSolve(OlexCctbxAdapter):
  def __init__(self):
    OlexCctbxAdapter.__init__(self)
    self.peak_normaliser = 1200 #fudge factor to get cctbx peaks on the same scale as shelx peaks

  def runChargeFlippingSolution(self, verbose="highly", solving_interval=60):
    import time
    t1 = time.time()
    from smtbx.ab_initio import charge_flipping
    from itertools import izip
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
      use_set_completion = OV.GetParam('snum.masks.use_set_completion')
      mask = masks.mask(xs, fo_sq, use_set_completion=use_set_completion)
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
      out = StringIO()
      fo2 = self.reflections.f_sq_obs
      fo2.show_comprehensive_summary(f=out)
      print >> out
      mask.show_summary(log=out)
      from iotbx.cif import model
      cif_block = model.block()
      hklstat = olex_core.GetHklStat()
      merging = self.reflections.merging
      min_d_star_sq, max_d_star_sq = fo2.min_max_d_star_sq()
      f = open('%s/%s-mask.log' %(OV.FilePath(), OV.FileName()),'wb')
      print >> f, out.getvalue()
      f.close()
      print out.getvalue()
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
  type = isinstance(grid, flex.int)
  olex_xgrid.Import(
    gridding.all(), gridding.focus(), grid.copy_to_byte_str(), type)
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
