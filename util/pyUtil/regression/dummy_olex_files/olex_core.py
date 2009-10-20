# replicate Olex2 internal functions accessed through olex_core.py

def IsVar(variable):
  return _variables.has_key(variable)

def FindValue(variable, default=u''):
  return _variables.get(variable, u'')

def SetVar(variable, value):
  _variables[variable] = value

def Translate(txt):
  return txt
  
_variables = {}
