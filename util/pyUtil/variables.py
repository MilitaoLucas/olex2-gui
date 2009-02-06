# variables.py

class Variable(object):
  def __init__(self,defaultValue,constraint=None,valType=None, onChange=None):
    """The value of the variable object is set to the defaultValue.
    
    If only defaultValue is specified, self.type is set to the type of the
    defaultValue.  valType can be specified if self.type is required to be
    different to that of defaultValue.
    If constraint object is specified, it must have a validate() method which
    raises an ValueError if the conditions of the constraint are not met.
    If specified, an onChange method must have no arguments.
    """
    
    self.default = defaultValue
    if valType:
      self.type = valType
    else:
      self.type = type(defaultValue)
    self.constraint = constraint
    self._value = defaultValue
    self.onChange = onChange
  
  def setValue(self,value):
    """Takes a value of type int, float, boolean or string and sets the value of
    the variable object.
    
    The type of the new value must be the same as the type of the default value
    or valType given when the variable was declared.
    If variable object has a contraint, the validate() method of the constraint 
    will be called to validate the new value.
    If the variable object has been assigned an onChange() method, this will be
    then be called.
    """
    
    val = None
    try:
      if self.type == int or self.type == float:
        if value != '?' and value != '.' and value != 'n/a' and value != None:
          val = float(value)
          if self.type == int:
            val = int(val)
        else:
          val = value
      elif self.type == bool:
        if value == True or value == False:
          val = value
        elif value == 'false' or value == 'False':
          val = False
        elif value == 'true' or value == 'True':
          val = True
        else:
          raise ValueError,"The value must be True or False"
      else:
        val = str(value)
      if self.constraint and val != self.default:
        self.constraint.validate(val)
      self._value = val
    except ValueError, extraInfo:
      #print extraInfo
      pass
    if self.onChange:
      self.onChange()
    
  def getValue(self):
    if self._value == None:
      return '?'
    return self._value
  
  value = property(getValue, setValue, None, None)
  
class Range(object):
  def __init__(self,min=None,max=None):
    """Provide min and/or max values"""
    self.min = min
    self.max = max
    
  def validate(self, value):
    """Will raise a ValueError if the value is not within the specified range."""
    if value != '?' and value != '.':
      if self.min != None and (value < self.min):
        raise ValueError, "The value must be greater than or equal to %s" %self.min
      if self.max != None and (value > self.max):
        raise ValueError, "The value must be less than or equal to %s" %self.max
  
class PermittedValues(object):
  def __init__(self,list):
    """Provide a list of permitted values"""
    self.permittedValues = list
  
  def validate(self,value):
    """Will raise a ValueError if the value is not within the given list of values."""
    if self.permittedValues and value.strip('\'') not in self.permittedValues:
      raise ValueError, '"%s" is not a permitted value' %value
    
if __name__ == '__main__':
  a = Variable(2.0,Range(min=0.0))
  a.value = 3
  a.value = -4
  a.value = 'string'