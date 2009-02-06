# sadabs.py

class Sadabs:
  def __init__(self, path):
    self.path = path
    
  def read_sad(self):
    """Reads the .abs file with the given path.
    
    Returns a dictionary of cif items found in the .abs file."""
    
    sad = {}
    rfile = open(self.path, 'r')
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
          sad.setdefault("prog_version", "%s" %txt)
        if lines[i][:33] == "Effective data to parameter ratio":
          txt = lines[i].split('=')
          txt = txt[1].strip()
          #print txt
          sad.setdefault("parameter_ratio", "%s" %txt)
        # txt = lines[i+2]
        # txt = lines[i+2].split()
          #txt = string.split(lines[i+2])
        if "(selected reflections only, before parameter refinement)" in lines[i]:
#	print "wR2(int) Before =", lines[i]
          txt = lines[i].split('=')
          txt = txt[1].strip()
          txt = txt.split('(')
          sad.setdefault("Rint_before", "%s" %txt[0].strip())
        if "(selected reflections only, after parameter refinement)" in lines[i]:
          txt = lines[i].split('=')
          txt = txt[1].strip()
          txt = txt.split('(')
          sad.setdefault("Rint_after", "%s" %txt[0].strip())
        if lines[i][:16] == "Ratio of minimum":
          txt = lines[i].split(':')
          #txt = string.split(lines[i], ":")
          sad.setdefault("ratiominmax", "%s" %txt[1].strip())
          sad.setdefault("_exptl_absorpt_correction_T_min", "%s" %txt[1].strip())
        if "Estimated minimum" in lines[i] :
          txt = lines[i].split(':')
          txt = txt[1].strip()
          txt = txt.split(" ")
          min = txt[0].strip()
          max = txt[2].strip()
          ratio = float(min)/float(max)
          sad.setdefault("_exptl_absorpt_correction_T_min", "%s" %min)
          sad.setdefault("_exptl_absorpt_correction_T_max", "%s" %max)
          sad.setdefault("ratiominmax", "%s" %ratio)
        if sad.get("prog_version") == '2008/1':
          sad.setdefault("lambda_correction", "Not present")
        else:
          if lines[i][:6] == "Lambda":
            txt = lines[i].split('=')
            #txt = string.split(lines[i], "=")
            sad.setdefault("lambda_correction", "%s" %txt[1].strip())
      except:
        #i += 1
        pass
      i += 1
#   print sad

    sad.setdefault("_exptl_absorpt_correction_T_max", "%s" %("1"))
    sad.setdefault("_exptl_absorpt_correction_type", "multi-scan")
    self.sad_d = sad
#   print sad
    return sad
  
if __name__ == '__main__':
  a = Sadabs('sad_.abs')
  info = a.read_sad()