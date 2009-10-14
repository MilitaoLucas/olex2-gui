# sadabs.py

class reader(object):
  def __init__(self, path):
    """Reads the .abs file with the given path.
    
    Returns a dictionary of cif items found in the .abs file."""
    
    self._cifItems = {}
    rfile = open(path, 'r')
    lines = {}
    
    i = 0
    for line in rfile:
      lines[i] = line.strip()
      #lines[i] = string.strip(line)
      i+=1 
    i = 0
    for line in lines:
      try:
#	print lines[i]
        if "SADABS" in lines[i]:
          txt = lines[i].split('-')
          if 'Bruker' in txt[1] and len(txt) == 3:
            txt = txt[2].strip()
          else:
            #txt = string.split(lines[i], '-')
            txt = txt[1].strip()
          self._cifItems.setdefault("prog_version", "%s" %txt)
        if lines[i][:33] == "Effective data to parameter ratio":
          txt = lines[i].split('=')
          txt = txt[1].strip()
          #print txt
          self._cifItems.setdefault("parameter_ratio", "%s" %txt)
        # txt = lines[i+2]
        # txt = lines[i+2].split()
          #txt = string.split(lines[i+2])
        if "(selected reflections only, before parameter refinement)" in lines[i]:
#	print "wR2(int) Before =", lines[i]
          txt = lines[i].split('=')
          txt = txt[1].strip()
          txt = txt.split('(')
          self._cifItems.setdefault("Rint_before", "%s" %txt[0].strip())
        if "(selected reflections only, after parameter refinement)" in lines[i]:
          txt = lines[i].split('=')
          txt = txt[1].strip()
          txt = txt.split('(')
          self._cifItems.setdefault("Rint_after", "%s" %txt[0].strip())
        if lines[i][:16] == "Ratio of minimum":
          txt = lines[i].split(':')
          #txt = string.split(lines[i], ":")
          self._cifItems.setdefault("ratiominmax", "%s" %txt[1].strip())
          self._cifItems.setdefault("_exptl_absorpt_correction_T_min", "%s" %txt[1].strip())
        if "Estimated minimum" in lines[i] :
          txt = lines[i].split(':')
          txt = txt[1].strip()
          txt = txt.split(" ")
          min = txt[0].strip()
          max = txt[2].strip()
          ratio = float(min)/float(max)
          self._cifItems.setdefault("_exptl_absorpt_correction_T_min", "%s" %min)
          self._cifItems.setdefault("_exptl_absorpt_correction_T_max", "%s" %max)
          self._cifItems.setdefault("ratiominmax", "%s" %ratio)
        if self._cifItems.get("prog_version") == '2008/1':
          self._cifItems.setdefault("lambda_correction", "Not present")
        else:
          if lines[i][:6] == "Lambda":
            txt = lines[i].split('=')
            #txt = string.split(lines[i], "=")
            self._cifItems.setdefault("lambda_correction", "%s" %txt[1].strip())
      except:
        #i += 1
        pass
      i += 1

    self._cifItems.setdefault("_exptl_absorpt_correction_T_max", "%s" %("1"))
    self._cifItems.setdefault("_exptl_absorpt_correction_type", "multi-scan")
    
  def cifItems(self):
    return self._cifItems

if __name__ == '__main__':
  a = Sadabs('sad_.abs')
  info = a.cifItems()
