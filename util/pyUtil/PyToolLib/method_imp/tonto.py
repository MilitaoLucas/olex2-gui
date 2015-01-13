import os, sys
from Method import Method_refinement
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import olx
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
    else:
      self.basis_list = None

  def pre_refinement(self, RunPrgObject):
    Method_refinement.pre_refinement(self, RunPrgObject)
    file_name = olx.FileName()
    data_file_name = "data.%s.hkl" %file_name
    if not os.path.exists(data_file_name):
      from iotbx.shelx import hklf
      import StringIO
      from cctbx_olex_adapter import OlexCctbxAdapter
      cctbx_adaptor = OlexCctbxAdapter()
      with open(data_file_name, "w") as out:
        out.write("reflection_data= { keys= { h= k= l= i_exp= i_sigma= } data= {\n")
        hklf.miller_array_export_as_shelx_hklf(cctbx_adaptor.reflections.f_obs,
                                        out, True)
        out.seek(out.tell()-28)
        out.write("}\n}\nREVERT")
        out.truncate(out.tell())
    model_file_name = "model.%s.cif" %file_name
    if not os.path.exists(model_file_name):
      olx.File(model_file_name)

    inp_data = {
      "cif_name" : model_file_name,
      "cif_data_name" : file_name,
      "job_name" : file_name,
      "basis_dir_name" : self.base_dir + "basis_sets",
      "basis_name" : "DZP",
      "data_name": data_file_name
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
         thermal_smearing_model= stewart
         partition_model= gaussian
         optimise_extinction= NO
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
     convergence= 0.00001
     diis= { convergence_tolerance= 0.00001 }
   }
   scf ! << do this

   ! Set cluster-charge SCF for refinement
   scfdata= {
     kind=  rhf
     initial_density= restricted
     use_SC_cluster_charges= TRUE
     cluster_radius= 8 angstrom
     convergence= 0.00001
     diis= { convergence_tolerance= 0.00001 }
   }

   ! Do the refinement ...
   ! It repeatedly does SCF calculations
   refine_hirshfeld_atoms

   ! Clean up
   delete_scf_archives
}
""" %inp_data)



  def do_run(self, RunPrgObject):
    self.failure = True
    print 'STARTING Tonto HAR refinement'
    try:
      olx.Exec(RunPrgObject.program.name)
      olx.WaitFor('process')
    except Exception:
      sys.stdout.formatExceptionInfo()
    finally:
      OV.DeleteBitmap('refine')

  def post_refinement(self, RunPrgObject):
    self.writeRefinementInfoIntoRes(self.cif)

  def writeRefinementInfoForGui(self, cif):
    for key, value in cif.iteritems():
      if "." in value:
        try:
          cif[key] = "%.4f" %float(value)
        except:
          pass
    self.cif = cif

  def register(self):
    OV.registerFunction(self.getBasisListStr, False, 'tonto')

  def getBasisListStr(self):
    return self.basis_list_str

tonto_HAR_phil = phil_interface.parse("""
name = 'HAR'
  .type=str
""")
