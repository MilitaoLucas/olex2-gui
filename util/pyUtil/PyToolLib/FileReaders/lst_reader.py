# lst_reader.py

class reader:
  def __init__(self,file_object):
    self._values = {}
    found = False
    i = 0
    
    data = file_object.readlines()
    lines = data

    #for line in lines:
      #line = line.strip()
      #if i != 0 and '+++++++++++' in lines[i-1] and line[0] == '+':
        #header = line.strip('+').split('-')
      #i += 1
      
    header = []
    program = None
    method = None
    version = None
    
    while 1:
      line = lines[i].strip()
      if i != 0 and '+++++++' in lines[i-1] and '+' in line:
        header.append(line.strip('+').strip())
        program = header[0].split('-')[0].strip()
        self._values.setdefault('program', program)
      elif header and '+++++++' not in line:
        header.append(line.strip('+').strip())
      elif header and '+++++++' in line:
        break
      i += 1
      
    if program in ('SHELXL', 'SHELXS', 'SHELXH'):
      version = header[1].split('Release')[-1].strip()
    else:
      version = header[0].split(' - ')[-1].strip()
    if version: self._values.setdefault('version', version)
    
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
      while not found:
        try:
          line = data[i]
        except IndexError:
          self._values['R1'] = 'n/a'
          self._values['wR2'] = 'n/a'
          break
        
        if 'Final Structure Factor' in line:
          found = True
        else:
          i += 1
          
      for x in range(50):
        line = data[i+x]
        if 'R1 =' in line:
          r1 = line.split()[2]
          self._values['R1'] = r1
        elif 'wR2 =' in line:
          wR2 = line.split()[2].strip(',')
          self._values['wR2'] = wR2
        else:
          continue
    elif solution:
      self._values['R1'] = 'n/a'
      self._values['wR2'] = 'n/a'
      i = 0
      for line in lines:
        i += 1
        if "Ralpha" and "Nqual" and "CFOM" in line:
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
  #a = Lst(r'\\crystal-02\home\d30m0u\Test folder\work\05srv267.lst')
  #a = Lst(r'C:\Documents and Settings\Richard\Application Data\Olex2\samples\sucrose\sucrose.lst')
  #a = Lst(r'\\crystal-02\home\d30m0u\problem.lst')
  #values = a.readLst()
  a = reader(open(r'C:\Documents and Settings\Richard\Application Data\Olex2\samples\sucrose\sucrose.lst'))
  print a.values()