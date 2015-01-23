import os, sys
from Method import Method_refinement
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import olx
import olex
import phil_interface

class Method_tonto_HAR(Method_refinement):

  def __init__(self, phil):
    super(Method_tonto_HAR, self).__init__(phil)
    self.base_dir = olx.file.Which('tonto.exe')
    if not self.base_dir:
      self.base_dir = olx.file.Which('tonto')
    if self.base_dir:
      self.base_dir = os.path.split(self.base_dir)[0] + os.path.sep
      self.basis_list = os.listdir(self.base_dir + "basis_sets")
      self.basis_list.sort()
      self.basis_list_str = ';'.join(self.basis_list)
      self.register()
      self.set_defaults()
    else:
      self.basis_list = None

  def pre_refinement(self, RunPrgObject):
    Method_refinement.pre_refinement(self, RunPrgObject)
    self.file_name = olx.FileName()
    data_file_name = "tonto.%s.hkl" %self.file_name
    if not os.path.exists(data_file_name):
      from iotbx.shelx import hklf
      import StringIO
      from cctbx_olex_adapter import OlexCctbxAdapter
      cctbx_adaptor = OlexCctbxAdapter()
      with open(data_file_name, "w") as out:
        out.write("reflection_data= { keys= { h= k= l= i_exp= i_sigma= } data= {\n")
        hklf.miller_array_export_as_shelx_hklf(cctbx_adaptor.reflections.f_sq_obs,
                                        out, True)
        out.seek(out.tell()-28)
        out.write("}\n}\nREVERT")
        out.truncate(out.tell())
    model_file_name = "tonto.%s.cif" %self.file_name
    olx.Kill("$Q")
    olx.Grow()
    olx.File(model_file_name)
    self.result_file = "tonto.%s_%s.accurate.cif" %(self.file_name, self.file_name)
    inp_data = {
      "cif_name" : model_file_name,
      "cif_data_name" : self.file_name,
      "job_name" : self.file_name,
      "basis_dir_name" : self.base_dir + "basis_sets",
      "data_name": data_file_name,
      "basis_name" : olx.GetVar('settings.tonto.basis.name'),
      "method" : olx.GetVar('settings.tonto.method'),
      "thermal_smearing_model" : olx.GetVar('settings.tonto.thermal_smearing_model'),
      "partition_model" : olx.GetVar('settings.tonto.partition_model'),
      "optimise_scale" : olx.GetVar('settings.tonto.optimise_scale'),
      "optimise_extinction" : olx.GetVar('settings.tonto.optimise_extinction'),
      "correct_dispersion" : olx.GetVar('settings.tonto.correct_dispersion'),
      "convergence" : olx.GetVar('settings.tonto.convergence.value'),
      "convergence_tolerance" : olx.GetVar('settings.tonto.convergence.tolerance'),
      "refine_h_u_iso" : olx.GetVar('settings.tonto.refine_h_u_iso'),
      "refine_positions_only" : olx.GetVar('settings.tonto.refine_positions_only'),
      }
    with open("stdin", "w") as inp:
      inp.write("""
{
   name= %(job_name)s
   charge= 0
   multiplicity= 1
   cif= {
      file_name=  %(cif_name)s
      data_block_name= %(cif_data_name)s
   }
   process_cif
   basis_directory= %(basis_dir_name)s
   basis_name= %(basis_name)s
   crystal= {
     xray_data= {
       refine_h_u_iso= %(refine_h_u_iso)s
       refine_positions_only= %(refine_positions_only)s
       thermal_smearing_model= %(thermal_smearing_model)s
       partition_model= %(partition_model)s
       optimise_extinction= %(optimise_extinction)s
       correct_dispersion = %(correct_dispersion)s
       REDIRECT %(data_name)s
     }
   }
   becke_grid = {
     set_defaults
     accuracy= high
   }
   scfdata= {
     kind = rhf
     initial_density= promolecule
     convergence= %(convergence)s
     diis= { convergence_tolerance= %(convergence_tolerance)s }
   }
   scf ! << do this

   ! Set cluster-charge SCF for refinement
   scfdata= {
     kind=  rhf
     initial_density= restricted
     use_SC_cluster_charges= TRUE
     cluster_radius= 8 angstrom
     convergence= %(convergence)s
     diis= { convergence_tolerance= %(convergence_tolerance)s }
   }

   ! Do the refinement ...
   ! It repeatedly does SCF calculations
   refine_hirshfeld_atoms

   ! Clean up
   delete_scf_archives
}
""" %inp_data)


  def do_run(self, RunPrgObject):
    self.failure = False
    print 'STARTING Tonto HAR refinement'
    try:
      import CifInfo
      olx.Exec("%s" %RunPrgObject.program.name)
      olx.Refresh()
      olx.WaitFor('process')
      hkl_src = olx.HKLSrc()
      cif_file = "%s.cif" %self.file_name
      if os.path.exists(cif_file):
        os.remove(cif_file)
      os.rename(self.result_file, cif_file)
      olx.Atreap(cif_file)
      olx.HKLSrc(hkl_src)
      params = {
        '_refine_diff_density_max' : 'snum.refinement.max_peak',
        '_refine_diff_density_min' : 'snum.refinement.max_hole',
        '_refine_ls_shift/su_max': 'snum.refinement.max_shift_over_esd',
        '_refine_ls_goodness_of_fit_ref': 'snum.refinement.goof',
      }
      cif_set = set([
      '_refine_ls_R_factor_all', '_refine_ls_R_factor_gt',
       '_refine_ls_wR_factor_ref', '_refine_ls_goodness_of_fit_ref',
       '_refine_ls_shift/su_max', '_refine_ls_shift/su_mean',
       '_reflns_number_total', '_reflns_number_gt', '_refine_ls_number_parameters',
       '_refine_ls_number_restraints', '_refine_ls_abs_structure_Flack',
       '_refine_diff_density_max', '_refine_diff_density_min'
       ])

      for k,v in params.iteritems():
        kv = olx.Cif(k)
        if kv != 'n/a':
          OV.SetParam(v, kv)
      cif = {}
      for k in cif_set:
        cif[k] = olx.Cif(k)
      olx.SetVar('tonto_R1', cif['_refine_ls_R_factor_gt'])
      olx.Free("Uiso,XYZ")
      res_file = "%s.res" %self.file_name
      olx.File(res_file)
      self.writeRefinementInfoIntoRes(cif, file_name=res_file)
      #olex.m("reap '%s'" %res_file)
      if os.path.exists("stdout"):
        try:
          print open("stdout", 'r').read()
        except:
          pass
    except Exception:
      sys.stdout.formatExceptionInfo()
    finally:
      OV.DeleteBitmap('refine')

  def post_refinement(self, RunPrgObject):
    pass

  def register(self):
    OV.registerFunction(self.getBasisListStr, False, 'tonto')

  def getBasisListStr(self):
    return self.basis_list_str

  def set_defaults(self):
    olx.SetVar('settings.tonto.method', 'rhf')
    olx.SetVar('settings.tonto.basis.name', 'DZP')
    olx.SetVar('settings.tonto.thermal_smearing_model', 'hirshfeld')
    olx.SetVar('settings.tonto.partition_model', 'mulliken')
    olx.SetVar('settings.tonto.optimise_extinction', 'false')
    olx.SetVar('settings.tonto.correct_dispersion', 'false')
    olx.SetVar('settings.tonto.optimise_scale', 'true')
    olx.SetVar('settings.tonto.convergence.value', '0.00001')
    olx.SetVar('settings.tonto.convergence.tolerance', '0.00001')
    olx.SetVar('settings.tonto.refine_h_u_iso', 'false')
    olx.SetVar('settings.tonto.refine_positions_only', 'false')

tonto_HAR_phil = phil_interface.parse("""
name = 'HAR'
  .type=str
""")
