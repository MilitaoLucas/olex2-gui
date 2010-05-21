# ires_reader.py



class reader:
  def __init__(self, file_object):
    self._values = {}
    #values = {}
    #rFile = open(self.path, 'r')
    data = file_object.readlines()
    
    for line in data:
      if 'REM R1 = ' in line:
        r1 = line.replace('  ', ' ').split('REM R1 = ')[1].split(' ')[0]
        self._values['R1'] = r1
    
    if not self._values.has_key('R1'):
      self._values['R1'] = 'n/a'
      
  def values(self):
    return self._values


if __name__ == '__main__':
  #a = InsRes(r'C:\Documents and Settings\Richard\Application Data\Olex2\samples\sucrose\sucrose.res')
  a = reader(r'C:\Documents and Settings\Richard\Application Data\Olex2\samples\sucrose\sucrose.ins')
  values = a.readInsOrRes()
  print values['R1']
