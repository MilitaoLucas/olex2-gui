# sadabs.py
# should this be abs_reader.py

class reader(object):
  def __init__(self, path):
    """Reads the .abs file with the given path. Able to read
    both sadabs and twinabs file formats.

    Returns a dictionary of cif items found in the .abs file."""

    self._cifItems = {}
    self._twin_cifItems = {}
    lines = open(path, 'r').readlines()
    for line in lines:
      try:
        if "SADABS" in line:
          #print "SADABS File Type"
          abs_type = "SADABS"
          self._cifItems.setdefault("abs_type", "SADABS")
          break
        if "TWINABS" in line:
          #print "TWINABS File Type"
          abs_type = "TWINABS"
          self._twin_cifItems.setdefault("abs_type", "TWINABS")
          break
      except:
        print "This is a new type of abs file I do not recognise"
        break
    if abs_type == "SADABS":
      self._cifItems.setdefault("_exptl_absorpt_correction_type", "multi-scan")
      for i in xrange(0, len(lines)):
        line = lines[i]
        try:
          if "SADABS" in line:
            txt = line.split('-')
            if 'Bruker' in txt[1] and len(txt) == 3:
              txt = txt[2].strip()
            else:
              txt = txt[1].strip()
            self._cifItems.setdefault("prog_version", "%s" %txt) ############################
          elif "Effective data to parameter ratio" in line: ############################
            txt = line.split('=')
            txt = txt[1].strip()
            self._cifItems.setdefault("parameter_ratio", "%s" %txt) ############################
          elif "(selected reflections only, before parameter refinement)" in line: ############################
            txt = line.split('=')
            self._cifItems.setdefault("R_name", txt[0].strip())
            txt = txt[1].strip()
            txt = txt.split('(')
            self._cifItems.setdefault("Rint_before", "%s" %txt[0].strip()) ############################
            i += 2 # Cycle  wR2(incid)  wR2(diffr)  Mean wt.
            while i < len(lines) and lines[i].strip():
              i += 1
            i -= 1 #last cycle
            self._cifItems.setdefault("Rint_after", lines[i].split()[1].strip())

          elif "Ratio of minimum" in line or "Minimum and maximum apparent transmission" in line:
            txt = line.split(':')
            self._cifItems.setdefault("ratiominmax", "%.4f" %float(txt[1].strip()))
            self._cifItems.setdefault("_exptl_absorpt_correction_T_min", txt[1].strip())
          elif "Estimated minimum" in line :
            txt = line.split(':')
            txt = txt[1].strip()
            txt = txt.split(" ")
            min = txt[0].strip()
            max = txt[2].strip()
            ratio = float(min)/float(max)
            self._cifItems.setdefault("_exptl_absorpt_correction_T_min", min)
            self._cifItems.setdefault("_exptl_absorpt_correction_T_max", max)
            self._cifItems.setdefault("ratiominmax", "%.4f" %ratio)
          elif line.strip().startswith("Lambda"):
            txt = line.split('=')
            self._cifItems.setdefault("lambda_correction", "%s" %txt[1].strip())
        except Exception, e:
          import traceback
          traceback.print_exc()
          pass
      self._cifItems.setdefault("lambda_correction", "Not present")

    elif abs_type == "TWINABS":
      self._cifItems.setdefault("_exptl_absorpt_correction_type", "multi-scan")
      for i in xrange(0, len(lines)):
        line = lines[i].strip()
        try:
          if "TWINABS" in line:
            txt = line.split('-')
            if 'Bruker AXS' in txt[1] and len(txt) == 3:
              txt = txt[2].strip()
              txt = txt.split(' ')[1]
            else:
              raise Exception('Unsupported program version: ' + txt[-1].strip())
            self._twin_cifItems.setdefault("prog_version", "%s" %txt)
            self._twin_cifItems.setdefault("lambda_correction", "Not present")
          elif "mul" in line:
            txt = line.split('file')
            txt = txt[1].strip()
            self._twin_cifItems.setdefault("integration_file", "%s" %txt)
          elif "twin components present" in line:
            txt = line.split('twin')
            txt = txt[0].strip()
            number_twin_components = int(txt)
            self._twin_cifItems.setdefault("number_twin_components", "%s" %txt)
          elif "Parameter refinement for twin component" in line:
            txt = line.split(' ')[-1]
            txt = txt.strip()
            twin_component = int(txt)
            self._twin_cifItems.setdefault("%i"%twin_component,{})
          elif "Refinement of a single parameter set" in line:
            i = i+1
            txt = lines[i].strip().split(' ')[-1]
            txt = txt.strip()
            twin_component = int(txt)
            self._twin_cifItems.setdefault("%i"%twin_component,{})
          elif "Effective data to parameter ratio" in line:
            txt = line.split('=')
            txt = txt[1].strip()
            self._twin_cifItems["%s"%twin_component].setdefault("parameter_ratio", "%s" %txt)
          elif "(selected reflections only, before parameter refinement)" in line:
            txt = line.split('=')
            self._twin_cifItems["%s"%twin_component].setdefault("R_name", txt[0].strip())
            txt = txt[1].strip()
            txt = txt.split('(')
            self._twin_cifItems["%s"%twin_component].setdefault("Rint_before", "%s" %txt[0].strip())
            i += 2 # Cycle  wR2(incid)  wR2(diffr)  Mean wt.
            while i < len(lines) and lines[i].strip():
              i += 1
            i -= 1 #last cycle
            self._twin_cifItems["%s"%twin_component].setdefault("Rint_after",
              lines[i].split()[1].strip())
          elif line[:16] == "Ratio of minimum":
            txt = line.split(':')
            self._twin_cifItems["%s"%twin_component].setdefault("ratiominmax", txt[1].strip())
            self._twin_cifItems["%s"%twin_component].setdefault(
              "_exptl_absorpt_correction_T_min", txt[1].strip())
          elif "involving domain" in line :
            txt = line.split(' ')
            twin_component = txt[-1]
          elif "Minimum and maximum" in line :
            txt = line.split(':')
            txt = txt[1].strip()
            txt = txt.split(" ")
            min = txt[0].strip()
            max = txt[2].strip()
            ratio = float(min)/float(max)
            self._twin_cifItems.setdefault(twin_component,{})
            self._twin_cifItems["%s"%twin_component].setdefault("_exptl_absorpt_correction_T_min", "%s" %min)
            self._twin_cifItems["%s"%twin_component].setdefault("_exptl_absorpt_correction_T_max", "%s" %max)
            self._twin_cifItems["%s"%twin_component].setdefault("ratiominmax", "%.4f" %ratio)
          elif "Rint =" in line and "I > 3sigma(I)" in line:
            txt = line.split('=')[1].split()
            self._twin_cifItems.setdefault("Rint_3sig", txt[0].strip())
            self._twin_cifItems.setdefault("Rint_3sig_refnum", txt[3].strip())
          elif "Rint =" in line and "I > 3sigma(I)" not in line:
            txt = line.split('=')[1].split()
            self._twin_cifItems.setdefault("Rint", txt[0].strip())
            self._twin_cifItems.setdefault("Rint_refnum", txt[3].strip())
          if "HKLF 5" in line:
            break
        except (RuntimeError, TypeError, NameError):
          print "there was an error"
          pass


  def cifItems(self):
    return self._cifItems
  def twin_cifItems(self):
    return self._twin_cifItems

def abs_type(path):
  rfile = open(path, 'r')
  lines = {}
  i = 0
  abs_type = None

  for line in rfile:
    lines[i] = line.strip()
    #lines[i] = string.strip(line)
    i+=1
  rfile.close()
  i=0
  for line in lines:
    try:
      if "SADABS" in lines[i]:
        abs_type = "SADABS"
        return abs_type
      if "TWINABS" in lines[i]:
        abs_type = "TWINABS"
        return abs_type
    except:
      print "This is a new type of abs file I do not recognise"
      return abs_type
    i+= 1
  i = 0
  return abs_type

if __name__ == '__main__':
  a = reader('/media/data2/DLS/MJR0747/refinement/mjr0747abs.abs')
  #a = reader('/home/xray/olexsvn/abs-test/cycle2.abs')
  #b = reader('/home/xray/olexsvn/abs-test/MJR0602.abs')
  info_cif = a.cifItems()
  info_twin = a.twin_cifItems()
  #info_sad = b.cifItems()
  print info_cif
  print info_twin
  #print info_sad