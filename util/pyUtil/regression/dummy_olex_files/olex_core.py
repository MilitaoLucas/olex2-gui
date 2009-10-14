# replicate Olex2 internal functions accessed through olex_core.py

def IsVar(variable):
  return False

def FindValue(variable, default=u''):
  if default:
    return default
  pass

def SetVar(*args, **kwds):
  pass
