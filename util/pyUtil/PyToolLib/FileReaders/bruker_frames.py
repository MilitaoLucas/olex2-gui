  # bruker_frames.py

class reader:
  def __init__(self, path):
    self._cifItems = {}
    self._saint_cfg = {}

    rFile = open(path, 'r')
    value = ""
    previousHeader = ""
    header_d = {}
    data = rFile.read()
    m = 0
    while "............................" not in data[m:m+80]:
      try:
        n = m + 8
        header = data[m:n]
        m = n
        n = m + 72
        value = data[m:n]
        m = n

        header = header.strip(':').strip()
        value = value.strip()
        if header == "":
          break
        if header != previousHeader:
          header_d.setdefault(header,value)
        else:
          header_d[header] += " %s" %value
        previousHeader = header

      except:
        break

    a = header_d['CSIZE'].split('|')
    a.sort()
    size = []
    for i in a:
      try:
        float(i)
        size.append(i)
      except:
        pass

    matrix = header_d['MATRIX'].split()

    self._cifItems['_diffrn_source_voltage'] = "%.0f" %float(header_d['SOURCEK'])
    self._cifItems['_diffrn_source_current'] = "%.0f" %float(header_d['SOURCEM'])
    #self._cifItems['_diffrn_refln_scan_width'] = "%.2f" %float(header_d['RANGE'])
    self._cifItems['time'] = "%.2f" %float(header_d['CUMULAT'])
    self._cifItems['formula'] = "%s" %(header_d['CHEM'])
    self._cifItems['_diffrn_radiation_monochromator'] = header_d['FILTER']
    self._cifItems['_diffrn_radiation_wavelength'] = "%f" %float(header_d['WAVELEN'].split()[0])
    self._cifItems['_exptl_crystal_description'] = "%s" %(header_d['MORPH'])
    self._cifItems['_exptl_crystal_colour'] = "%s" %(header_d['CCOLOR'])
    if len(size) == 3:
      self._cifItems['_exptl_crystal_size_min'] = "%s" %(size[0])
      self._cifItems['_exptl_crystal_size_mid'] = "%s" %(size[1])
      self._cifItems['_exptl_crystal_size_max'] = "%s" %(size[2])
    self._cifItems['_diffrn_orient_matrix_UB_11'] = "%f" %float(matrix[0])
    self._cifItems['_diffrn_orient_matrix_UB_12'] = "%f" %float(matrix[1])
    self._cifItems['_diffrn_orient_matrix_UB_13'] = "%f" %float(matrix[2])
    self._cifItems['_diffrn_orient_matrix_UB_21'] = "%f" %float(matrix[3])
    self._cifItems['_diffrn_orient_matrix_UB_22'] = "%f" %float(matrix[4])
    self._cifItems['_diffrn_orient_matrix_UB_23'] = "%f" %float(matrix[5])
    self._cifItems['_diffrn_orient_matrix_UB_31'] = "%f" %float(matrix[6])
    self._cifItems['_diffrn_orient_matrix_UB_32'] = "%f" %float(matrix[7])
    self._cifItems['_diffrn_orient_matrix_UB_33'] = "%f" %float(matrix[8])

    ccdparam = header_d['CCDPARM'].split()
    self._saint_cfg.setdefault("READNOISE", ccdparam[0])
    self._saint_cfg.setdefault("EPERADU", ccdparam[1])
    self._saint_cfg.setdefault("EPERPHOTON", ccdparam[2])

    ccdparam = header_d['DETTYPE'].split()
    if ccdparam[0] == "CCD-PXL-L6000":
      self._saint_cfg.setdefault("PIXPERCM", ccdparam[1])
      self._saint_cfg.setdefault("CM_TO_GRID", ccdparam[2])
      self._saint_cfg.setdefault("BRASS_SPACING", ccdparam[4])
      self._saint_cfg.setdefault("D_ATTENUATION", "31.1977")
      self._cifItems.setdefault("_diffrn_measurement_device_type", "BRUKER SMART CCD 6000")
      self._cifItems.setdefault("_diffrn_detector_area_resol_mean", "8")

    if ccdparam[0] == "CCD-PXL":
      self._saint_cfg.setdefault("PIXPERCM", 81.920)
      self._saint_cfg.setdefault("CM_TO_GRID", 0.800)
      self._saint_cfg.setdefault("BRASS_SPACING", 0.2540)
      self._cifItems.setdefault("_diffrn_measurement_device_type", "BRUKER SMART CCD 1000")
      self._cifItems.setdefault("_diffrn_detector_area_resol_mean", "8")

  def cifItems(self):
    return self._cifItems

  def saint_cfg(self):
    return self._saint_cfg

if __name__ == '__main__':
  a = BrukerFrame('C:/datasets/08srv071/frm071_1.001')
  print a.cifItems()
  print a.saint_cfg()
