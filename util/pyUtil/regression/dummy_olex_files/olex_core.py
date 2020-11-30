# replicate Olex2 internal functions accessed through olex_core.py

def IsVar(variable):
  return variable in _variables

def FindValue(variable, default=''):
  return _variables.get(variable, '')

def SetVar(variable, value):
  _variables[variable] = value

def Translate(txt):
  return txt
  
_variables = {}
