# bruker_smart.py

class reader:
  def __init__(self, path):
    """Reads the smart.ini file with the given path.

    Returns a dictionary of cif items found in the smart.ini file."""
    self._cifItems = {}
    special_details = {}

    rfile = open(path, 'r')
    lines = {}

    i = 0
    for line in rfile:
      lines[i] = line.strip()
      i += 1

    i = 0
    for line in lines:
      try:
        if lines[i][:6] == "PGMNAM":
          self._cifItems.setdefault("prog_version", lines[i][-6:])

        if lines[i][:9] == "/DISTANCE":
          txt = lines[i].split('=')
          special_details.setdefault("distance", float(txt[1]))

        elif lines[i] == "[HEMISPHERE ARRAY]":
          txt = "begin"
          j = 0
          while txt != "" and txt[0:1] != "[":
            i += 1
            j += 1
            if j == 1:
              txt = lines[i].split()
              special_details.setdefault("scantime", txt[-1:][0])
              special_details.setdefault("scanwidth", txt[-3:-2][0])
            txt = lines[i]
          special_details.setdefault("scans", j)
        elif lines[i][:11] == "/WAVELENGTH":
          txt = lines[i].split('=')
          special_details.setdefault("wavelength", float(txt[1]))
        elif lines[i][:7] == "/TARGET":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_diffrn_source_target", txt[1])
        elif lines[i][:3] == "/KV":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_diffrn_source_voltage", float(txt[1]))
        elif lines[i][:3] == "/MA":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_diffrn_source_current", float(txt[1]))
        elif lines[i][:14] == "/MONOCHROMATOR":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_diffrn_radiation_monochromator", txt[1])
        elif lines[i][:8] == "/FORMULA":
          txt = lines[i].split('=')
          self._cifItems.setdefault("formula", txt[1])
        elif lines[i][:6] == "/MORPH":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_exptl_crystal_description", txt[1])
        elif lines[i][:5] == "/CCOL":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_exptl_crystal_colour", txt[1])
        elif lines[i][:6] == "/CSIZ1":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_exptl_crystal_size_min", float(txt[1]))
        elif lines[i][:6] == "/CSIZ2":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_exptl_crystal_size_mid", float(txt[1]))
        elif lines[i][:6] == "/CSIZ3":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_exptl_crystal_size_max", float(txt[1]))
        elif lines[i][:5] == "/TEMP":
          txt = lines[i].split('=')
          self._cifItems.setdefault("_diffrn_ambient_temperature", txt[1])

      except:
        pass
      i += 1

    if self._cifItems.has_key('_diffrn_source_voltage') and self._cifItems.has_key('_diffrn_source_current'):
      self._cifItems.setdefault('_diffrn_source_power', (self._cifItems['_diffrn_source_voltage'] * self._cifItems['_diffrn_source_current'])/1000)
    self._cifItems.setdefault('_exptl_special_details', self.prepare_exptl_special_details(special_details))

  def prepare_exptl_special_details(self, smart):
    """Prepares the text for the _exptl_special_details cif item using details obtained from the smart.ini file."""

    txt = """
 The data collection nominally covered a full sphere of reciprocal space by
 a combination of %(scans)i sets of \\w scans each set at different \\f and/or
 2\\q angles and each scan (%(scantime)s s exposure) covering %(scanwidth)s\ degrees in \\w.
 The crystal to detector distance was %(distance)s cm.
"""%smart
    exptl_special_details = "\n;%s;\n" %txt
    return exptl_special_details

  def cifItems(self):
    return self._cifItems

if __name__ == '__main__':
  a = reader('C:/datasets/08srv071/smart.ini')
  print a.cifItems()