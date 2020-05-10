import os
from cctbx import miller
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import easy_pickle
from cctbx.array_family import flex
from cctbx_olex_adapter import OlexCctbxAdapter, OlexCctbxMasks
from smtbx import masks
import cctbx_olex_adapter

class Worker(OlexCctbxAdapter):
  def run(self):
    filepath = OV.StrDir()
    if not os.path.exists("%s/%s-f_mask.pickle" %(filepath, OV.FileName())):
      print("Could not locate mask information")
      return
    modified_hkl_path = "%s/%s-mask.hkl" %(OV.FilePath(), OV.FileName())
    f_mask = easy_pickle.load("%s/%s-f_mask.pickle" %(filepath, OV.FileName()))
    f_model = easy_pickle.load("%s/%s-f_model.pickle" %(filepath, OV.FileName()))
    cctbx_adapter = cctbx_olex_adapter.OlexCctbxAdapter()
    fo2 = cctbx_adapter.reflections.f_sq_obs_filtered
    if f_mask.size() < fo2.size():
      f_model = f_model.generate_bijvoet_mates().customized_copy(
        anomalous_flag=fo2.anomalous_flag()).common_set(fo2)
      f_mask = f_mask.generate_bijvoet_mates().customized_copy(
        anomalous_flag=fo2.anomalous_flag()).common_set(fo2)
    elif f_mask.size() > fo2.size():
      f_mask = f_mask.common_set(fo2)
      f_model = f_model.common_set(fo2)
      if f_mask.size() != fo2.size():
        raise RuntimeError("f_mask array doesn't match hkl file")
    modified_intensities = masks.modified_intensities(fo2, f_model, f_mask)
    if modified_intensities is not None:
      with open(modified_hkl_path, 'w') as file_out:
        modified_intensities.export_as_shelx_hklf(file_out,
          normalise_if_format_overflow=True)
      print("Created the modified hkl file: %s" %modified_hkl_path)

Worker().run()