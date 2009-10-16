# lst_reader.py

class reader:
  def __init__(self, path=None, file_object=None):
    self._values = {}
    found = False
    i = 0
    
    assert [path, file_object].count(None) == 1
    if path is not None:
      rFile = open(path, 'r')
      data = rFile.readlines()
      rFile.close()
    else:
      data = file_object.readlines()
    lines = data

    header = []
    program = None
    method = None
    version = None
    """    
    while 1:
      line = lines[i].strip()
      if i != 0 and '+++++++' in lines[i-1] and '+' in line:
  	header.append(line.strip('+').strip())
	program = header[0].split('-')[0].strip()
        self._values.setdefault('program', program)
      elif header and '+++++++' not in line and len(line.strip('+').strip()) > 0:
      	print "next", line
        header.append(line.strip('+').strip())
      elif header and '+++++++' in line:
        break
      i += 1
      """
    for i in range(1, 15):
      line = lines[i].strip()
#      print "Line = :", i, " ", line
      if i != 0 and '+++++++' not in lines and '+' in line and len(line.strip('+').strip()) > 0:
#        print "clasue 1", line
        header.append(line.strip('+').strip())
#      elif header and '+++++++' not in line and len(line.strip('+').strip()) > 0:
#        print "calause 2", line
#        header.append(line.strip('+').strip())
      i += 1
#    print "The header is: ", header
    program = header[0].split('-')[0].strip()
    self._values.setdefault('program', program)
#    print "header = ", header
#    print "Program = ", program  
    if program in ('SHELXL', 'SHELXH'):
      version = header[1].split('Release')[-1].strip()
    elif program == 'SHELXS' and len(header) > 2:
      version = header[1].split('Release')[-1].strip()
    elif program == 'SHELXS' and len(header) == 2:
      version = '86'
    else:
      version = header[0].split(' - ')[-1].strip()
    if version: self._values.setdefault('version', version)
#    print "Version is: ", version
    
    solution = False
    refinement = False
    if 'SOLUTION' in header[0] or 'DIRECT METHODS' in header[0]:
      solution = True
      if 'XS' in header[0]:
        program = 'XS'
      elif 'XM' in header[0]:
        program = 'XM'
    elif 'REFINEMENT' in header[0]:
      refinement = True
      if 'XL' in header[0]:
        program = 'XL'
        
        
    ## Determine program method
    while True:
      line = lines[i].strip()
      if refinement:
        args = {'L.S.':'Least Squares', 'CGLS':'CGLS'}
      elif solution:
        args = {'TREF':'Direct Methods', 'PATT':'Patterson Method', 'NTRY':'Dual Space'}
      for item in args.items():
        if item[0] in line:
          method = item[1]
          
      if method: 
        self._values.setdefault('method', method)
        break
      else: i += 1
      if i >= len(lines):
        #print "Oooops, trying to go beyond the end of file here!"
        return
      
    if refinement:
      try:
        while True:
          line = data[i]        
          if 'Final Structure Factor' in line:
            break
          else:
            i += 1
        while True:
          line = data[i]
          i += 1
          if 'R1 =' in line:
            self._values['R1'] = line.split()[2]
          elif 'wR2 =' in line:
            if self._values.has_key('R1'):
              self._values['wR2'] = line.split()[2].strip(',')
              break
          else:
            continue
      except IndexError:
        self._values['R1'] = 'n/a'
        self._values['wR2'] = 'n/a'
    elif solution:
      self._values['R1'] = 'n/a'
      self._values['wR2'] = 'n/a'
      i = 0
      for line in lines:
        i += 1
        if "Ralpha" in line and "Nqual" in line and "CFOM" in line:
          found_best = False
          l = lines[i:]
          for line in l:
            if '*' in line:
              try:
                li = line.split()
                Ralpha = float(li[1])
                Nqual = float(li[2])
                CFOM = float(li[5].strip('*'))
                self._values['Ralpha'] = Ralpha
                self._values['Nqual'] = Nqual
                self._values['CFOM'] = CFOM
                break
              except:
                continue
  def values(self):
    return self._values

if __name__ == '__main__':
  a = reader(open(r'C:\Users\Richard\AppData\Roaming\Olex2u\samples\sucrose\sucrose.lst'))
  print a.values()
