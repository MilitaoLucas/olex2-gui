import olex, olx
from olexex import OlexRefinementModel

from olexFunctions import OV

class RefinementChecks(object):

  def __init__(self, cctbx):
    self.cctbx = cctbx
    self.refinement_has_failed = []

  def check_PDF(self, force=False):
    RM = OlexRefinementModel()
    any_have_anh = False
    label_list = []
    for i, atom in enumerate(RM._atoms):
      anh_adp = atom.get('anharmonic_adp')
      if anh_adp == None:
        continue
      any_have_anh = True
      label_list.append(atom['label'])
    if any_have_anh == True:
      if OV.HasGUI():
        olex.m("PDF")
      else:
        olex.m("spy.NoSpherA2.PDF_map(0.1,1,true,true,true,true,false,false)")
      problem = OV.GetVar("Negative_PDF")
      Kuhs = OV.GetVar("Kuhs_Rule")
      err_list = []
      if problem == True:
        err_list.append("Negative PDF found")
        if force == True:
          print("Making all anharmonic atoms hamrnoic again!")
          for label in label_list:
            print(label)
            olex.m("anis %s" % label)
      if Kuhs == True:
        err_list.append("Kuhs' rule not fulfilled")
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
        for t in tables:
          table.append(t.table(e))
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
        fp_average /= len(tables)
        fdp_average /= len(tables)
        fpdiff = (fp_min_max[1] - fp_min_max[0])
        fdpdiff = (fdp_min_max[1] - fdp_min_max[0])
        if fp_average + 2 * fpdiff < fp or fp_average - 2 * fpdiff > fp:
          unreasonable_fp.append(sc.label)
        if fdp_average + 2 * fdpdiff < fdp or fdp_average - 2 * fdpdiff > fdp:
          unreasonable_fdp.append(sc.label)
      if len(unreasonable_fdp) != 0:
        if len(unreasonable_fdp) == 1:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: white'>%s has strongly deviating f''</a>" % unreasonable_fdp[0])
        else:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: white'>%s have strongly deviating f''</a>" % ",".join(unreasonable_fdp))
      if len(unreasonable_fp) != 0:
        if len(unreasonable_fp) == 1:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: white'>%s has strongly deviating f'</a>" % unreasonable_fp[0])
        else:
          self.refinement_has_failed.append("<a href='spy.gui.SwitchTool(h2-info-anomalous-dispersion)>>spy.gui.tools.flash_gui_control(h2-Anomalous-Dispersion)' style='color: white'>%s have strongly deviating f'</a>" % ",".join(unreasonable_fp))

  def check_mu(self):
    try:
      mu = self.cctbx.normal_eqns.iterations_object.mu
      if mu > 1E1:
        self.refinement_has_failed.append("Mu of LM is very large!")
    except AttributeError:
      return
