# bruker_saint_listing.py

class reader:
  def __init__(self, path):
    """Reads the *m._ls merging listing file with the given path.

    Returns a dictionary of cif items found in the *m._ls file."""

    self._cifItems = {}
    rFile = open(path, 'r')
    lines = [line.strip() for line in rFile]
    rFile.close()
    two_theta_min = 0
    two_theta_max = 0
    used = 0
    for i, li in enumerate(lines):
      if li[:5] == "SAINT":
        self._cifItems.setdefault("prog_version", li[6:].strip())
      elif "Reflection Summary:" in li:
        info = lines[i+3].split()
        two_theta_min = float(info[-2].strip())
        two_theta_max = float(info[-1].strip())
        used = info[-5].strip()
        worst = info[-4].strip()
        best = info[-3].strip()
      elif "Range of reflections used:" in li:
        info = lines[i+2].split()
        two_theta_min = float(info[-2].strip())
        two_theta_max = float(info[-1].strip())
        best = info[1].strip()
        worst = info[0].strip()
      elif "Orientation least squares, component" in li:
        u = li.split("(")[1].strip()
        used = u.split()[0].strip()

    self._cifItems.setdefault("_cell_measurement_theta_min", "%.3f" %(two_theta_min/2))
    self._cifItems.setdefault("_cell_measurement_theta_max", "%.3f" %(two_theta_max/2))
    self._cifItems.setdefault("_cell_measurement_reflns_used", "%s" %(used))

  def cifItems(self):
    return self._cifItems
