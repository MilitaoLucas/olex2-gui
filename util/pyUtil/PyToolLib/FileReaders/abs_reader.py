# sadabs.py
# should this be abs_reader.py

class reader(object):
  def __init__(self, path):
    """Reads the .abs file with the given path. Able to read
    both sadabs and twinabs file formats.
    
    Returns a dictionary of cif items found in the .abs file."""
    
    self._cifItems = {}
    self._twin_cifItems = {}
    rfile = open(path, 'r')
    lines = {}
    i = 0
    abs_type = None
    for line in rfile:
      lines[i] = line.strip()
      #lines[i] = string.strip(line)
      i+=1
    i=0

    for line in lines:
      try:
        if "SADABS" in lines[i]:
          print "SADABS File Type"
          abs_type = "SADABS"
          self._cifItems.setdefault("abs_type", "SADABS")
          break
        if "TWINABS" in lines[i]:
          print "TWINABS File Type"
          abs_type = "TWINABS"
          self._twin_cifItems.setdefault("abs_type", "TWINABS")
          break
      except:
        print "This is a new type of abs file I do not recognise"
        break
      i+= 1
    i = 0
    if abs_type == "SADABS":
      print "Running SADABS parser"
      print "PATH", path
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
            self._cifItems.setdefault("prog_version", "%s" %txt) ############################
          if lines[i][:33] == "Effective data to parameter ratio": ############################
            txt = lines[i].split('=')
            txt = txt[1].strip()
            #print txt
            self._cifItems.setdefault("parameter_ratio", "%s" %txt) ############################
          # txt = lines[i+2]
          # txt = lines[i+2].split()
            #txt = string.split(lines[i+2])
          if "(selected reflections only, before parameter refinement)" in lines[i]: ############################
  #	print "wR2(int) Before =", lines[i]
            txt = lines[i].split('=')
            txt = txt[1].strip()
            txt = txt.split('(')
            self._cifItems.setdefault("Rint_before", "%s" %txt[0].strip()) ############################
          if "(selected reflections only, after parameter refinement)" in lines[i]: ############################
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
    elif abs_type == "TWINABS":
      print "Running TWINABS parser"
      print "PATH", path
      for line in lines:
        #print "line = ", line, lines[line]
        try:
  #	print lines[line]
          if "TWINABS" in lines[line]:
            txt = lines[line].split('-')
            if 'Bruker' in txt[1] and len(txt) == 3:
              txt = txt[2].strip()
              txt = txt.split(' ')[1]
            else:
              #txt = string.split(lines[line], '-')
              txt = txt[1].strip()
              txt = txt.split(' ')[1]
            self._twin_cifItems.setdefault("prog_version", "%s" %txt)
            self._twin_cifItems.setdefault("lambda_correction", "Not present")
            continue
          if "mul" in lines[line]:
            txt = lines[line].split('file')
            txt = txt[1].strip()
            #print "Integration file", txt
            self._twin_cifItems.setdefault("integration_file", "%s" %txt)
            continue
          if "twin components present" in lines[line]:
            txt = lines[line].split('twin')
            txt = txt[0].strip()
            print "Total twin components", txt
            number_twin_components = int(txt)
            self._twin_cifItems.setdefault("number_twin_components", "%s" %txt)
            continue
          if "Parameter refinement for twin component" in lines[line]:
            txt = lines[line].split(' ')[-1]
            txt = txt.strip()
            twin_component = int(txt)
            #print "twin component", txt, twin_component
            self._twin_cifItems.setdefault("%i"%twin_component,{})
            #print "check components", twin_component, self._twin_cifItems
            continue
          if "Effective data to parameter ratio" in lines[line]:
            txt = lines[line].split('=')
            txt = txt[1].strip()
            #print "Effective paramter ratio", twin_component, txt
            self._twin_cifItems["%s"%twin_component].setdefault("parameter_ratio", "%s" %txt)
            #print "check parameter_ratio", self._twin_cifItems
            continue
          if "(selected reflections only, before parameter refinement)" in lines[line]:
            txt = lines[line].split('=')
            txt = txt[1].strip()
            txt = txt.split('(')
            self._twin_cifItems["%s"%twin_component].setdefault("Rint_before", "%s" %txt[0].strip())
            #print "check Rint_before", twin_component, self._twin_cifItems
            continue
          if "(selected reflections only, after parameter refinement)" in lines[line]:
            txt = lines[line].split('=')
            txt = txt[1].strip()
            txt = txt.split('(')
            self._twin_cifItems["%s"%twin_component].setdefault("Rint_after", "%s" %txt[0].strip())
            #print "check Rint_after", twin_component, self._twin_cifItems
            continue
          if lines[line][:16] == "Ratio of minimum":
            txt = lines[line].split(':')
            #txt = string.split(lines[line], ":")
            self._twin_cifItems["%s"%twin_component].setdefault("ratiominmax", "%s" %txt[1].strip())
            self._twin_cifItems["%s"%twin_component].setdefault("_exptl_absorpt_correction_T_min", "%s" %txt[1].strip())            
            #print "check ratiominmax, exptl Tmin", twin_component, self._twin_cifItems
            continue
          if "involving domain" in lines[line] :
            txt = lines[line].split(' ')
            twin_component = txt[-1]
            #print twin_component
          if "Minimum and maximum" in lines[line] :
            txt = lines[line].split(':')
            txt = txt[1].strip()
            txt = txt.split(" ")
            min = txt[0].strip()
            max = txt[2].strip()
            ratio = float(min)/float(max)
            self._twin_cifItems["%s"%twin_component].setdefault("_exptl_absorpt_correction_T_min", "%s" %min)
            self._twin_cifItems["%s"%twin_component].setdefault("_exptl_absorpt_correction_T_max", "%s" %max)
            self._twin_cifItems["%s"%twin_component].setdefault("ratiominmax", "%s" %ratio)
            #print "check ratiominmax, exptl Tmin", twin_component, self._twin_cifItems
          if "HKLF 5" in lines[line]:
            break
        except (RuntimeError, TypeError, NameError):
          print "there was an error"
          pass
      #print "twin info ", self._twin_cifItems
      
    self._twin_cifItems.setdefault("_exptl_absorpt_correction_T_max", "%s" %("1"))
    self._twin_cifItems.setdefault("_exptl_absorpt_correction_type", "multi-scan")

    
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
  a = reader('/home/xray/olexsvn/abs-test/cycle2.abs')
  #b = reader('/home/xray/olexsvn/abs-test/MJR0602.abs')
  info_cif = a.cifItems()
  info_twin = a.twin_cifItems()
  #info_sad = b.cifItems()
  print info_cif
  print info_twin
  #print info_sad
