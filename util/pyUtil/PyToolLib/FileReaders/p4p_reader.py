# p4p_reader.py

class p4p_reader:
  def __init__(self, path):
    self.path = path

  def read_p4p(self):
    """Reads the .p4p file with the given path.
    Returns a dictionary of cif items found in the p4p file."""

    cif = {}
    for li in open(self.path, 'r').readlines():
      li = li.strip()
      if not li:
        continue
      if li[:2] == "  ":
        continue
      l = li.split()
      key, val = l[0], l[1:]
      if key == "REF05":
        break
      elif key == "SOURCE" and len(val) == 7:
        try:
          cif["_diffrn_source_voltage"] = float(val[5])
          cif["_diffrn_source_current"] = float(val[6])
        except:
          pass
      elif key == "CCOLOR": 
        cif["_exptl_crystal_colour"] = val[0]
      elif key == "MORPH": 
        cif["_exptl_crystal_description"] = val[0]
      if len(cif) == 4:
        break

    if "_diffrn_source_voltage" in cif and "_diffrn_source_current" in cif:
      cif["_diffrn_source_power"] = (cif['_diffrn_source_voltage'] * cif['_diffrn_source_current'])/1000

    return cif

if __name__ == '__main__':
  a = p4p_reader('C:/datasets/08srv071/first.p4p')
  info = a.read_p4p()
  print()
