import os, sys
import olex, olx
from olexex import OlexRefinementModel

from olexFunctions import OV
from RunPrg import RunPrg, RunRefinementPrg


def deal_with_AAFF(self: RunRefinementPrg):
  HAR_log = None
  try:
    from cctbx import adptbx
    Full_HAR = OV.GetParam('snum.NoSpherA2.full_HAR')
    old_model = OlexRefinementModel()
    converged = False
    run = 0
    HAR_log = open("%s/%s.NoSpherA2" %(OV.FilePath(),self.original_filename),"w")
    HAR_log.write("NoSpherA2 in Olex2 for structure %s\n\n" %(OV.ModelSrc()))
    import datetime
    HAR_log.write("Refinement startet at: ")
    HAR_log.write(str(datetime.datetime.now())+"\n")
    HAR_log.write("Cycle     SCF Energy    Max shift:  xyz/ESD     Label   Uij/ESD       Label   Max/ESD       Label    R1    wR2\n"+"*" * 110 + "\n")
    HAR_log.write("{:3d}".format(run))
    energy = None
    source = OV.GetParam('snum.NoSpherA2.source')
    update = OV.GetParam('snum.NoSpherA2.Calculate')
    if "Please S" in source and update:
      olx.Alert("No tsc generator selected",\
"""Error: No generator for tsc files selected.
Please select one of the generators from the drop-down menu.""", "O", False)
      OV.SetVar('NoSpherA2-Error',"TSC Generator unselected")
      return
    if energy == None:
      HAR_log.write("{:^24}".format("---"))
    else:
      HAR_log.write("{:^24.10f}".format(energy))
    HAR_log.write("{:>70}".format(" "))
    r1_old = OV.GetParam('snum.refinement.last_R1')
    wr2_old = OV.GetParam('snum.refinement.last_wR2')
    if r1_old != "n/a" and r1_old != None:
      HAR_log.write("{:>6.2f}".format(float(r1_old) * 100))
    else:
      HAR_log.write("{:>6}".format("N/A"))
    if wr2_old != "n/a" and wr2_old != None:
      HAR_log.write("{:>7.2f}".format(float(wr2_old) * 100))
    else:
      HAR_log.write("{:>7}".format("N/A"))
    HAR_log.write("\n")
    HAR_log.flush()
    max_cycles = int(OV.GetParam('snum.NoSpherA2.Max_HAR_Cycles'))
    calculate = OV.GetParam('snum.NoSpherA2.Calculate')
    if calculate == True:
      if OV.GetParam('snum.NoSpherA2.h_aniso') == True:
        olx.Anis("$D", h=True)
        olx.Anis("$H", h=True)
      if OV.GetParam('snum.NoSpherA2.h_afix') == True:
        olex.m("Afix 0 $H")
      else:
        print("Setting all AFIX H Atoms to Neutron distances")
        olex.m("NeutronHDist")
    while converged == False:
      run += 1
      HAR_log.write("{:3d}".format(run))
      old_model = OlexRefinementModel()
      OV.SetVar('Run_number', run)
      self.refinement_has_failed = []
      #Calculate Wavefunction
      try:
        from NoSpherA2.NoSpherA2 import NoSpherA2_instance as nsp2
        v = nsp2.launch()
        if v == False:
          print("Error during NoSpherA2! Abnormal Ending of program!")
          HAR_log.close()
          return False
      except NameError as error:
        print("Error during NoSpherA2:")
        print(error)
        RunRefinementPrg.running = None
        RunRefinementPrg.Terminate = True
        HAR_log.close()
        return False
      Error_Status = OV.GetVar('NoSpherA2-Error')
      if Error_Status != "None":
        print("Error in NoSpherA2: %s" %Error_Status)
        return False
      tsc_exists = False
      wfn_file = None
      for file in os.listdir(olx.FilePath()):
        if file == os.path.basename(OV.GetParam('snum.NoSpherA2.file')):
          tsc_exists = True
        elif file.endswith(".wfn"):
          wfn_file = file
        elif file.endswith(".wfx"):
          wfn_file = file
        elif file.endswith(".gbw"):
          wfn_file = file
        elif file.endswith(".tscb"):
          tsc_exists = True
      if tsc_exists == False:
        print("Error during NoSpherA2: No .tsc file found")
        RunRefinementPrg.running = None
        HAR_log.close()
        return False
      # get energy from wfn file
      #TODO Check if WFN is new, otherwise skip this!
      energy = None
      if source == "fragHAR" or source == "Hybdrid" or source == "DISCAMB" or "MATTS" in source or "hakkar" in source:
        HAR_log.write("{:^24}".format("---"))
      else:
        if (wfn_file != None) and (calculate == True):
          if ".gbw" not in wfn_file:
            with open(wfn_file, "rb") as f:
              f.seek(-2000, os.SEEK_END)
              fread = f.readlines()[-1].decode()
              if "THE VIRIAL" in fread:
                source = OV.GetParam('snum.NoSpherA2.source')
                if "Gaussian" in source:
                  energy = float(fread.split()[3])
                elif "ORCA" in source:
                  energy = float(fread.split()[4])
                elif "pySCF" in source:
                  energy = float(fread.split()[4])
                elif ".wfn" in source:
                  energy = float(fread[17:38])
                elif "Tonto" in source:
                  energy = float(fread.split()[4])
                else:
                  energy = 0.0
          if energy is not None:
            HAR_log.write("{:^24.10f}".format(energy))
          else:
            HAR_log.write("{:^24}".format("---"))
          fread = None
        else:
          HAR_log.write("{:^24}".format("---"))
      if OV.GetParam('snum.NoSpherA2.run_refine') == True:
        # Run Least-Squares
        self.startRun()
        try:
          self.setupRefine()
          OV.File("%s/%s.ins" %(OV.FilePath(),self.original_filename))
          self.setupFiles()
        except Exception as err:
          sys.stderr.formatExceptionInfo()
          print(err)
          self.endRun()
          HAR_log.close()
          return False
        if self.terminate:
          self.endRun()
          return
        if self.params.snum.refinement.graphical_output and self.HasGUI:
          self.method.observe(self)
        try:
          RunPrg.run(self)
          f_obs_sq,f_calc = self.cctbx.get_fo_sq_fc(self.cctbx.normal_eqns.one_h_linearisation)
          if f_obs_sq != None and f_calc != None:
            nsp2.set_f_calc_obs_sq_one_h_linearisation(f_calc,f_obs_sq,self.cctbx.normal_eqns.one_h_linearisation)
        except Exception as e:
          e_str = str(e)
          if ("stoks.size() == scatterer" in e_str):
            print("Insufficient number of scatterers in .tsc file!\nDid you forget to recalculate after adding or deleting atoms?")
          elif ("Error during building of normal equations using OpenMP" in e_str):
            print("Error initializing OpenMP refinement, try disabling it!")
          elif  ("fsci != sc_map.end()" in e_str):
            print("An Atom was not found in the .tsc file!\nHave you renamed some and not recalcualted the tsc file?")
          return
      else:
        break
      new_model=OlexRefinementModel()
      class results():
        def __init__(self):
          self.max_dxyz = 0
          self.max_duij = 0
          self.label_uij = None
          self.label_xyz = None
          self.r1 = 0
          self.wr2 = 0
          self.max_overall = 0
          self.label_overall = None
        def update_xyz(self, dxyz, label):
          if dxyz > self.max_dxyz:
            self.max_dxyz = dxyz
            self.label_xyz = label
            if dxyz > self.max_overall:
              self.max_overall = dxyz
              self.label_overall = label
        def update_uij(self, duij, label):
          if duij > self.max_duij:
            self.max_duij = duij
            self.label_uij = label
            if duij > self.max_overall:
              self.max_overall = duij
              self.label_overall = label
        def update_overall(self, d, label):
          if d > self.max_overall:
            self.max_overall = d
            self.label_overall = label
      try:
        jac_tr = self.cctbx.normal_eqns.reparametrisation.jacobian_transpose_matching_grad_fc()
        from scitbx.array_family import flex
        cov_matrix = flex.abs(flex.sqrt(self.cctbx.normal_eqns.covariance_matrix().matrix_packed_u_diagonal()))
        esds = jac_tr.transpose() * flex.double(cov_matrix)
        jac_tr = None
        annotations = self.cctbx.normal_eqns.reparametrisation.component_annotations
      except:
        HAR_log.close()
        print ("Could not obtain cctbx object and calculate ESDs!\n")
        return False
      from decors import run_with_bitmap
      @run_with_bitmap('Analyzing shifts', update_model_after=False)
      def analyze_shifts(results):
        try:
          uc = self.cctbx.normal_eqns.xray_structure.unit_cell()
          atoms_lookup = {}
          for i, atom in enumerate(new_model._atoms):
            atoms_lookup[atom['label']] = i
          matrix_run = 0
          while matrix_run < len(annotations):
            an = annotations[matrix_run]
            atom_idx = atoms_lookup[an.split('.')[0]]
            new_atom = new_model._atoms[atom_idx]
            old_atom = old_model._atoms[atom_idx]
            if '.occ' in an:
              matrix_run += 1
            elif '.x' in an:
              xyz = new_atom['crd'][0]
              xyz2 = old_atom['crd'][0]
              for x in range(3):
                # if parameter is fixed and therefore has 0 esd
                if esds[matrix_run] > 0:
                  res = abs(xyz[x] - xyz2[x]) / esds[matrix_run]
                  if res > results.max_dxyz:
                    results.update_xyz(res, annotations[matrix_run])
              matrix_run += 3
            elif '.uiso' in an:
              adp = new_atom['uiso'][0]
              adp2 = old_atom['uiso'][0]
              adp_esd = esds[matrix_run]
              if esds[matrix_run] > 0:
                res = abs(adp - adp2) / adp_esd
                if res > results.max_duij:
                  results.update_uij(res, annotations[matrix_run])
              matrix_run += 1
            elif 'fp' in an:
              new_disp = new_atom['disp'][0]
              old_disp = old_atom['disp'][0]
              disp_esd = esds[matrix_run]
              if disp_esd > 0:
                res = abs(new_disp - old_disp) / disp_esd
                if res > results.max_overall:
                  results.update_overall(res, annotations[matrix_run])
              matrix_run += 1
            elif 'fdp' in an:
              new_disp = new_atom['disp'][0]
              old_disp = old_atom['disp'][0]
              disp_esd = esds[matrix_run]
              if disp_esd > 0:
                res = abs(new_disp - old_disp) / disp_esd
                if res > results.max_overall:
                  results.update_overall(res, annotations[matrix_run])
              matrix_run += 1            
            elif '.u' in an:
              adp = new_atom['adp'][0]
              adp = (adp[0], adp[1], adp[2], adp[5], adp[4], adp[3])
              adp2 = old_atom['adp'][0]
              adp2 = (adp2[0], adp2[1], adp2[2], adp2[5], adp2[4], adp2[3])
              adp = adptbx.u_cart_as_u_cif(uc, adp)
              adp2 = adptbx.u_cart_as_u_cif(uc, adp2)
              adp_esds = (esds[matrix_run],
                          esds[matrix_run + 1],
                          esds[matrix_run + 2],
                          esds[matrix_run + 3],
                          esds[matrix_run + 4],
                          esds[matrix_run + 5])
              adp_esds = adptbx.u_star_as_u_cif(uc, adp_esds)
              for u in range(6):
                # if parameter is fixed and therefore has 0 esd
                if adp_esds[u] > 0:
                  res = abs(adp[u] - adp2[u]) / adp_esds[u]
                  if res > results.max_duij:
                    results.update_uij(res, annotations[matrix_run + u])
              matrix_run += 6
            elif '.C' in an or '.D' in an:
              order = new_atom['anharmonic_adp']['order']
              if order == 3:
                  size = 10
              elif order == 4:
                  size = 25
              else:
                  size = 0
              if order >= 3:
                adp_C = new_atom['anharmonic_adp']['C']
                adp2_C = old_atom['anharmonic_adp']['C']
                adp_esds_C = (esds[matrix_run:matrix_run + 10])
                for u in range(10):
                  # if parameter is fixed and therefore has 0 esd
                  if adp_esds_C[u] > 0:
                    res = abs(adp_C[u] - adp2_C[u]) / adp_esds_C[u]
                    if res > results.max_overall:
                      results.update_overall(res, annotations[matrix_run + u])
              if order >= 4:
                adp_D = new_atom['anharmonic_adp']['D']
                adp2_D = old_atom['anharmonic_adp']['D']
                adp_esds_D = (esds[matrix_run + 10:matrix_run + 25])
                for u in range(14):
                  # if parameter is fixed and therefore has 0 esd
                  if adp_esds_D[u] > 0:
                    res = abs(adp_D[u] - adp2_D[u]) / adp_esds_D[u]
                    if res > results.max_overall:
                      results.update_overall(res, annotations[matrix_run + u + 10])
              matrix_run += size

          HAR_log.write("{:>16.4f}".format(results.max_dxyz))
          if results.label_xyz != None:
            HAR_log.write("{:>10}".format(results.label_xyz))
          else:
            HAR_log.write("{:>10}".format("N/A"))
          HAR_log.write("{:>10.4f}".format(results.max_duij))
          if results.label_uij != None:
            HAR_log.write("{:>12}".format(results.label_uij))
          else:
            HAR_log.write("{:>12}".format("N/A"))
          HAR_log.write("{:>10.4f}".format(results.max_overall))
          if results.label_overall != None:
            HAR_log.write("{:>12}".format(results.label_overall))
          else:
            HAR_log.write("{:>12}".format("N/A"))
          results.r1 = OV.GetParam('snum.refinement.last_R1')
          results.wr2 = OV.GetParam('snum.refinement.last_wR2')
          HAR_log.write("{:>6.2f}".format(float(results.r1) * 100))
          HAR_log.write("{:>7.2f}".format(float(results.wr2) * 100))
          HAR_log.write("\n")
          HAR_log.flush()
        except Exception as e:
          HAR_log.write("!!!ERROR!!!\n")
          HAR_log.close()
          print("Error during analysis of shifts!")
          raise e
      r = results()
      analyze_shifts(r)
      if calculate == False:
        converged = True
        break
      elif Full_HAR == False:
        converged = True
        break
      elif (r.max_overall <= 0.01):
        converged = True
        break
      elif run == max_cycles:
        break
      elif r1_old != "n/a":
        if (float(r.r1) > float(r1_old) + 0.1) and (run > 1):
          HAR_log.write("      !! R1 increased by more than 0.1, aborting before things explode !!\n")
          self.refinement_has_failed.append("Error: R1 is not behaving nicely! Stopping!")
          break
      else:
        r1_old = r.r1
        wr2_old = r.wr2
  except Exception as e :
    if HAR_log != None:
      HAR_log.close()
    raise e
  # Done with the while !Converged
  OV.SetParam('snum.NoSpherA2.Calculate', False)
  ext_name = "h3-NoSpherA2-extras"
  if OV.IsHtmlItem(ext_name):
    olex.m(f"html.ItemState {ext_name} 2")
  if converged == False:
    HAR_log.write(" !!! WARNING: UNCONVERGED MODEL! PLEASE INCREASE MAX_CYCLE OR CHECK FOR MISTAKES !!!\n")
    self.refinement_has_failed.append("Warning: Unconverged Model!")
  if "DISCAMB" in source or "MATTS" in source:
    unknown_sources = False
    fn = os.path.join("olex2","Wfn_job","discambMATTS2tsc.log")
    if not os.path.exists(fn):
      fn = os.path.join("olex2","Wfn_job","discamb2tsc.log")
    if not os.path.exists(fn):
      HAR_log.write("                   !!! WARNING: No output file found! !!!\n")
      self.refinement_has_failed.append("Output file not found!")
    else:
      with open(fn) as discamb_log:
        for i in discamb_log.readlines():
          if "unassigned atom types" in i:
            unknown_sources = True
          if unknown_sources == True:
            HAR_log.write(i)
    if unknown_sources == True:
      HAR_log.write("                   !!! WARNING: Unassigned Atom Types! !!!\n")
      self.refinement_has_failed.append("Unassigned Atom Types!")
  HAR_log.write("*" * 110 + "\n")
  HAR_log.write("Residual density Max:{:+8.3f}\n".format(OV.GetParam('snum.refinement.max_peak')))
  HAR_log.write("Residual density Min:{:+8.3f}\n".format(OV.GetParam('snum.refinement.max_hole')))
  HAR_log.write("Residual density RMS:{:+8.3f}\n".format(OV.GetParam('snum.refinement.res_rms')))
  HAR_log.write("Goodness of Fit:     {:8.4f}\n".format(OV.GetParam('snum.refinement.goof')))
  HAR_log.write("Refinement finished at: ")
  HAR_log.write(str(datetime.datetime.now()))
  HAR_log.write("\n")
  precise = OV.GetParam('snum.NoSpherA2.precise_output')
  if precise == True:
    olex.m("spy.NoSpherA2.write_precise_model_file()")
  HAR_log.flush()
  HAR_log.close()
  with open("%s/%s.NoSpherA2" %(OV.FilePath(),self.original_filename), 'r') as f:
    print(f.read())
  return True

def make_fcf(self: RunRefinementPrg):
  from refinement import FullMatrixRefine
  table = str(OV.GetParam('snum.NoSpherA2.file'))
  self.startRun()
  try:
    self.setupRefine()
    OV.File("%s/%s.ins" %(OV.FilePath(),self.original_filename))
    self.setupFiles()
  except Exception as err:
    sys.stderr.formatExceptionInfo()
    print(err)
    self.endRun()
    return False
  if self.terminate:
    self.endRun()
    return False
  if self.params.snum.refinement.graphical_output and self.HasGUI:
    self.method.observe(self)
  FM = FullMatrixRefine(
        max_cycles=0,
        max_peaks=1)
  FM.run(False,table)

  fcf_cif, fmt_str = FM.create_fcf_content(list_code = 6)
  with open(OV.file_ChangeExt(OV.FileFull(), 'fcf'), 'w') as f:
    fcf_cif.show(out=f, loop_format_strings={'_refln':fmt_str})
  return True

def get_refinement_details(cif_block, acta_stuff):
  tsc_file_name = os.path.join(OV.GetParam('snum.NoSpherA2.dir'),OV.GetParam('snum.NoSpherA2.file'))
  if not os.path.exists(tsc_file_name):
    t = os.path.join(OV.FilePath(), OV.GetParam('snum.NoSpherA2.file'))
    if os.path.exists(t):
      tsc_file_name = t
      
  if os.path.exists(tsc_file_name):
    #tsc = open(tsc_file_name, 'r').readlines()
    #cif_block_found = False
    tsc_info = """;\n"""
    #for line in tsc:
    #  if "CIF:" in line:
    #    cif_block_found = True
    #    continue
    #  if ":CIF" in line:
    #    break
    #  if cif_block_found == True:
    #    tsc_info = tsc_info + line
    #if not cif_block_found:
    details_text = """Refinement using NoSpherA2, an implementation of
NOn-SPHERical Atom-form-factors in Olex2.
Please cite:
F. Kleemiss et al. Chem. Sci. DOI 10.1039/D0SC05526C - 2021
NoSpherA2 implementation of HAR makes use of
tailor-made aspherical atomic form factors calculated
on-the-fly from a Hirshfeld-partitioned electron density (ED) - not from
spherical-atom form factors.

The ED is calculated from a gaussian basis set single determinant SCF
wavefunction - either Hartree-Fock or DFT using selected funtionals
- for a fragment of the crystal.
This fragment can be embedded in an electrostatic crystal field by employing cluster charges
or modelled using implicit solvation models, depending on the software used.
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
      partitioning = OV.GetParam('snum.NoSpherA2.NoSpherA2_SF')
      accuracy = OV.GetParam('snum.NoSpherA2.becke_accuracy')
      if partitioning == True:
        details_text += "   PARTITIONING:   NoSpherA2\n"
        details_text += f"   INT ACCURACY:   {accuracy}\n"
      else:
        details_text += "   PARTITIONING:   Tonto\n"
      details_text += f"   METHOD:         {method}\n"
      details_text += f"   BASIS SET:      {basis_set}\n"
      details_text += f"   CHARGE:         {charge}\n"
      details_text += f"   MULTIPLICITY:   {mult}\n"
      solv = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
      if solv != "Vacuum":
        details_text += f"   SOLVATION:      {solv}\n"
      if relativistic == True:
        if "ORCA" in software:
          ORCA_Relativistic = OV.GetParam('snum.NoSpherA2.ORCA_Relativistic')
          details_text += f"   RELATIVISTIC:   {ORCA_Relativistic}\n"
        else:
          details_text += "   RELATIVISTIC:   DKH2\n"
      if software == "Tonto":
        radius = OV.GetParam('snum.NoSpherA2.cluster_radius')
        details_text += f"   CLUSTER RADIUS: {radius}\n"
        complete = OV.GetParam('snum.NoSpherA2.cluster_grow')
        details_text += f"   CLUSTER GROW:   {complete}\n"
    if os.path.exists(tsc_file_name):
      f_time = os.path.getctime(tsc_file_name)
    import datetime
    f_date = datetime.datetime.fromtimestamp(f_time).strftime('%Y-%m-%d_%H-%M-%S')
    details_text = details_text + "   DATE:           %s\n"%f_date
    tsc_info = tsc_info + details_text + ";\n"
    cif_block['_olex2_refine_details'] = tsc_info
    if acta_stuff:
      # remove IAM scatterer reference
      for sl in ['a', 'b']:
        for sn in range(1, 5):
          key = '_atom_type_scat_Cromer_Mann_%s%s' % (sl, sn)
          if key in cif_block:
            cif_block.pop(key)
      if '_atom_type_scat_Cromer_Mann_c' in cif_block:
        cif_block.pop('_atom_type_scat_Cromer_Mann_c')
      if '_atom_type_scat_source' in cif_block:
        for i in range(cif_block['_atom_type_scat_source'].size()):
          cif_block['_atom_type_scat_source'][i] = "NoSpherA2: Chem.Sci. 2021, DOI:10.1039/D0SC05526C"
