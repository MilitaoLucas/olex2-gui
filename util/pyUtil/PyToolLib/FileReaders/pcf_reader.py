# pcf_reader.py
class pcf_reader:
  def __init__(self, path):
    self.path = path
    self.ignore = set(["?", "'?'", ".", "'.'"])
    self.items = set([
      "_symmetry_cell_setting",
      "_symmetry_space_group_name_H-M",
      #"_cell_measurement_temperature",
      "_exptl_crystal_description",
      "_exptl_crystal_colour",
      "_exptl_crystal_size_min",
      "_exptl_crystal_size_mid",
      "_exptl_crystal_size_max",
      "_exptl_crystal_density_meas",
      "_exptl_crystal_density_method",
      "_exptl_absorpt_correction_type",
      "_diffrn_radiation_monochromator",
      #"_diffrn_source",
      #"_diffrn_radiation_type",
      "_diffrn_measurement_device_type",
      "_diffrn_measurement_method",
      "_diffrn_detector_area_resol_mean",
      "_diffrn_standards_number",
      "_diffrn_standards_interval_count",
      #"_diffrn_standards_decay_%",
      "_cell_measurement_reflns_used",
      "_cell_measurement_theta_min",
      "_cell_measurement_theta_max",
      #"_diffrn_ambient_temperature",
      "_exptl_crystal_face",
    ])


  def read_pcf(self):
    try:
      import iotbx.cif
      with open(self.path, 'rb') as f:
        pcf = {}
        cif_block = iotbx.cif.reader(file_object=f).model()
        dn = list(cif_block.keys())[0]
        cif_block = cif_block[dn]
        for i in self.items:
          val = cif_block.get(i, ".")
          if isinstance(val, str):
            if val in self.ignore:
              continue
            val = self.value_exceptions(i, val)
          pcf[i] = val
        return pcf
    except Exception as e:
      return self.read_pcf_old()

  def read_pcf_old(self):
    """Reads the .pcf file with the given path.
    Returns a dictionary of cif items found in the .pcf file."""

    lines = open(self.path, 'r').readlines()
    pcf = {}
    for line in lines:
      toks = line.strip().split()
      if len(toks) < 2: continue
      if toks[0] in self.items:
        val = ' '.join(toks[1:])
        if val in self.ignore: continue
        val = self.value_exceptions(toks[0], val)
        pcf.setdefault(toks[0], val)
    self.pcf_d = pcf
    return pcf

  def value_exceptions(self, item, value):
    ## In some Bruker p4p files the default here is 0, which is rubbish
    if item == "_exptl_crystal_density_meas":
      if str(value) == str(0): value = "."
    return value

if __name__ == '__main__':
  a = pcf_reader('C:/datasets/Richard 4th year project/Crystals/06rjg003/work/rjg003_m.pcf')
  info = a.read_pcf()
  print()
