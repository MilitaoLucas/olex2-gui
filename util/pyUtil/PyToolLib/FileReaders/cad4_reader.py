# cad4_reader.py

class cad4_reader:
  def __init__(self, path):
    self.path = path

  def read_cad4(self):
    """Reads the .dat file with the given path.

    Returns a dictionary of cif items found in the .dat file."""

    cad = {}
    rfile = open(self.path, 'r')
    lines = {}

    i = 0
    for line in rfile:
      lines[i] = line.strip()
      i += 1
    i = 0
    for line in lines:
      try:
        if lines[i][:2] == "22":
          items = lines[i].split()
          txt = items[1]
          cad.setdefault("_diffrn_reflns_theta_min", "%s" %txt)
          txt = items[2]
          cad.setdefault("_diffrn_reflns_theta_max", "%s" %txt)
          txt = items[3]
          cad.setdefault("scan_width", "%s" %txt)
          txt = items[4]
          cad.setdefault("scan_broadening", "%s" %txt)
          txt = items[7]
          if txt == '0':
            txt = r'\w'
          elif txt == '6':
            txt = r'\\w/2\\t'
          else:
            txt = r"\\w/(%i/3)\\t" %int(txt)
          txt = "'%s scans'" %txt
          cad.setdefault("_diffrn_measurement_method", "%s" %txt)
        elif lines[i][:2] == "26":
          items = lines[i].split()
          txt = str(int(items[1])/60)
          cad.setdefault("_diffrn_standards_interval_time", "%s" %txt)
        elif lines[i][:2] == "27":
          cell_theta = []
          k = 1
          standard_no = 0
          while (lines[i+k])[:2] != "31":
            line = (lines[i+k])
            cell_theta.append(line.split("S")[2].strip())[:4]
            #cell_theta.append(string.strip(line.split("S")[2])[:4])
            if len(line.split(r"I")) > 1:
              standard_no+=1
            k+=1
          cell_theta.sort()
          txt = cell_theta[:1][0]
          cad.setdefault("_cell_measurement_theta_min", "%s" %txt)
          txt = cell_theta[-1:][0]
          cad.setdefault("_cell_measurement_theta_max", "%s" %txt)
          txt = standard_no
          cad.setdefault("_diffrn_standards_interval_count", "%s" %txt)


      except:
        i += 1
        pass
      i += 1
    #self.cad_d = cad
    return cad

if __name__ == '__main__':
  #a = pcf_reader('C:/datasets/Richard 4th year project/Crystals/06rjg003/work/rjg003_m.pcf')
  #info = a.read_pcf()
  print()
