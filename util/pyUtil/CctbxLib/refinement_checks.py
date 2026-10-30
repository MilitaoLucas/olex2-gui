import olex, olx
from olexex import OlexRefinementModel
from scitbx.array_family import flex
import numpy as np

from olexFunctions import OV

class RefinementChecks(object):

  def __init__(self, cctbx):
    self.cctbx = cctbx
    self.refinement_has_failed = []

  def check_PDF(self, force=False):
    # check only - no map render, that is what made this slow in the GUI; `PDF` draws it on demand
    label_list = [sc.label for sc in self.cctbx.normal_eqns.xray_structure.scatterers() if sc.anharmonic_adp is not None]
    if label_list:
      from cubes_maps import PDF_map
      PDF_map(0.1, 1, True, True, True, True, False, False)
      problem = OV.GetVar("Negative_PDF")
      Kuhs = OV.GetVar("Kuhs_Rule")
      err_list = []
      if problem == True:
        err_list.append("Negative PDF found")
        if OV.HasGUI():  # show the offending map only when there is something to look at
          olex.m("PDF")
        if force == True:
          print("Making all anharmonic atoms harmonic again!")
          for label in label_list:
            print(label)
            olex.m("anis %s" % label)
      if Kuhs == True:
        err_list.append("Warning: Kuhs' rule not fulfilled")
      if err_list:
        self.refinement_has_failed.extend(err_list)

  def check_occu(self):
    scatterers = self.cctbx.normal_eqns.xray_structure.scatterers()
    wrong_occu = []
    for sc in scatterers:
      if sc.flags.grad_occupancy():
        if sc.occupancy < 0 or sc.occupancy > 1.0:
          wrong_occu.append(sc.label)
    if len(wrong_occu) != 0:
      if len(wrong_occu) == 1:
        self.refinement_has_failed.append(f"{wrong_occu[0]} has unreasonable Occupancy")
      else:
        _ =  ", ".join(wrong_occu)
        self.refinement_has_failed.append(f"{_} have unreasonable Occupancy")

  def check_disp(self):
    scatterers = self.cctbx.normal_eqns.xray_structure.scatterers()
    refined_disp = []
    for sc in scatterers:
      if sc.flags.grad_fp() or sc.flags.grad_fdp():
        fp, fdp = sc.fp, sc.fdp
        refined_disp.append((sc, fp, fdp))
    if refined_disp != []:
      wavelength = float(olx.xf.exptl.Radiation())
      from cctbx.eltbx import sasaki
      from cctbx.eltbx import henke
      from brennan import brennan
      tables = [sasaki, henke, brennan()]
      unreasonable_fp = []
      unreasonable_fdp = []
      for sc, fp, fdp in refined_disp:
        e = str(sc.element_symbol())
        table = []
        from cctbx_olex_adapter import resonant_table
        for t in tables:
          t = resonant_table(t, e)
          if t is not None:
            table.append(t)
        fp_min_max = [135.0, 0.0]
        fdp_min_max = [135.0, 0.0]
        fp_average = 0.0
        fdp_average = 0.0
        for t in table:
          temp = t.at_angstrom(wavelength)
          fp_average += temp.fp()
          fdp_average += temp.fdp()
          fp_min_max = [min(fp_min_max[0], temp.fp()), max(fp_min_max[1], temp.fp())]
          fdp_min_max = [min(fdp_min_max[0], temp.fdp()), max(fdp_min_max[1], temp.fdp())]
        fp_average /= len(table)
        fdp_average /= len(table)
        fpdiff = (fp_min_max[1] - fp_min_max[0])
        fdpdiff = (fdp_min_max[1] - fdp_min_max[0])
        if fp_average + 2 * fpdiff < fp or fp_average - 2 * fpdiff > fp:
          unreasonable_fp.append(sc.label)
        if fdp_average + 2 * fdpdiff < fdp or fdp_average - 2 * fdpdiff > fdp:
          unreasonable_fdp.append(sc.label)
      if len(unreasonable_fdp) != 0:
        if len(unreasonable_fdp) == 1:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: %s'>%s has strongly deviating f''</a>" % (OV.GetParam('gui.red'), unreasonable_fdp[0]))
        else:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: %s'>%s have strongly deviating f''</a>" % (OV.GetParam('gui.red'), unreasonable_fdp[0]))
      if len(unreasonable_fp) != 0:
        if len(unreasonable_fp) == 1:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: %s'>%s has strongly deviating f'</a>" % (OV.GetParam('gui.red'), unreasonable_fdp[0]))
        else:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: %s'>%s have strongly deviating f'</a>" % (OV.GetParam('gui.red'), ",".join(unreasonable_fp)))

  def check_table_coverage(self):
    """ Warn if the tabulated table did not cover the whole model.

    The atoms it missed were refined with spherical scattering factors, so part
    of the structure is modelled more crudely than the rest. The refinement
    itself succeeds, which is exactly why this has to be said out loud.
    """
    from cctbx_olex_adapter import get_table_fallback_atoms
    fallback = get_table_fallback_atoms()
    if not fallback:
      return
    if len(fallback) <= 6:
      which = ", ".join(fallback)
    else:
      which = "%s and %d more" % (", ".join(fallback[:6]), len(fallback) - 6)
    self.refinement_has_failed.append(
      "<font color='%s'><b>Not in .tsc, refined spherically: %s</b></font>"
      % (OV.GetParam('gui.red'), which))

  def check_aspherical(self):
    # things a HAR is expected to get right and a plain refine with a tsc silently does not
    if not OV.IsNoSpherA2():
      return
    import os
    from cctbx.eltbx import tiny_pse
    z_of = lambda symbol: tiny_pse.table(str(symbol).capitalize()).atomic_number()
    # etc/neutron.dist: "Z d" or "Z m1 m2 ... d", the same files NeutronHDist reads
    neutron = {}
    for fn in (os.path.join(olx.BaseDir(), "etc", "neutron.dist"), os.path.join(olx.app.SharedDir(), "etc", "neutron.dist")):
      if not os.path.exists(fn):
        continue
      for line in open(fn):
        toks = line.split('#')[0].split()
        if len(toks) < 2:
          continue
        for m in (toks[1:-1] or ["*"]):
          neutron[(int(toks[0]), m if m == "*" else int(m))] = float(toks[-1])
    RM = OlexRefinementModel()
    iam, other = [], []
    for m, n, pivot, dependent, pivot_neighbours, d in RM.afix_iterator():
      if n not in (3, 7):
        continue
      z = z_of(RM._atoms[pivot]['type'])
      expected = neutron.get((z, m), neutron.get((z, "*")))
      if expected is None:
        continue
      label = RM._atoms[pivot]['label']
      if d <= 0:
        iam.append(label)
      elif abs(d - expected) > 0.03:
        other.append("%s %.3f" % (label, d))
    if iam:
      self.refinement_has_failed.append("Riding H on %s at IAM default distances - run NeutronHDist or refine them" % ", ".join(iam))
    if other:
      self.refinement_has_failed.append("Riding H on %s at custom distances, not the neutron ones" % ", ".join(other))
    if not OV.GetParam('snum.refinement.update_weight'):
      self.refinement_has_failed.append("Weighting scheme is not updated - a spherical scheme fits aspherical Fc poorly")
    try:
      ratio = float(OV.GetParam('snum.refinement.data')) / float(OV.GetParam('snum.refinement.parameters'))
      if ratio < 10:
        self.refinement_has_failed.append("Only %.1f data per parameter - a HAR wants 10 or more" % ratio)
    except (TypeError, ValueError, ZeroDivisionError):
      pass

  def check_mu(self):
    try:
      mu = self.cctbx.normal_eqns.iterations_object.mu
      if mu > 1E1:
        self.refinement_has_failed.append("Mu of LM is very large!")
    except AttributeError:
      return

  def check_corr(self):
    try:
      from refinement import strong_correlations, riding_groups
      # the refinement worked this out already; asking the normal equations
      # again would multiply out the Jacobian a second time
      m_and_a = getattr(self.cctbx, 'covariance_matrix_and_annotations', None)
      if m_and_a is None:
        m_and_a = self.cctbx.normal_eqns.covariance_matrix_and_annotations()
      annotations = m_and_a.annotations
      found, strong_corr_count, _ = strong_correlations(m_and_a.matrix, 0.75,
        groups=riding_groups(self.cctbx.constraints,
          self.cctbx.reparametrisation.structure.scatterers(), annotations))

      print(f"List of correlations > 0.75 (riding H and proxy U pairs left out):\nThere are {strong_corr_count} strong correlations")
      print("==================================")
      for corr, i, j in sorted(found, key=lambda t: (t[1], t[2])):
          print(f" {annotations[i]:<10} v {annotations[j]:<10}: {corr:>6.3f}")
      print("==================================")

    except Exception as e:
      import traceback
      traceback.print_exc()
      print(f"Error reading vcv matrix for calculation of correlations {e}")
      return


