import olex, olex_core
from decors import return_str
"""
typical content of defaults:
  param_defaults = {
    'refinement.beam_n': (10, 'aced.user.defaults.starting.n_beams'),
    'thickness.value': (400, 'aced.user.defaults.starting.thickness'),
    'thickness.grad': True,
  }
  Allows to resolve parameters in the folowing sequence:
  param  in the INS header? - use it, else get the default
    default has phil entry? - use it
      use the param_default value
        no default in the register? - use the function default
"""

class OlxInsHeader:
  def __init__(self):
    self.defaults = {}
    self.set = self.set_

  def register(self, name: str, default):
    self.defaults[name] = default
    #avoid confusing Python in skip_types=set()

  def register_dict(self, params: dict, scope=None):
    if not scope:
      self.defaults.update(params)
    else:
      for k,v in params.items():
        self.defaults[f"{scope}.{k}"] = v

  def set_(self, param, value):
    olex_core.SetStoredParam(param, str(value))

  def _get_default(self, param, default):
    from olexFunctions import OV
    rv = self.defaults.get(param, default)
    if isinstance(rv, tuple):
      return OV.GetParam(rv[1], rv[0])
    return rv

  @return_str(skip_types=set([dict,list,set]))
  def get(self, param, default=None, src=None):
    """ Special params are ".value" and ".fields". Th first return the item value,
    the second - a dict of all fields. The item value is tyucally encoded like
    <item "value">
    """
    p = olex_core.FindStoredParam(param)
    if not p:
      return self._get_default(param, default)
    return p

  def get_bool(self, param, default=None) -> bool:
    rv = self.get(param, default)
    if rv and rv.lower() == 'true':
      return True
    return False

  def exists(self, param):
    return olex_core.HasStoredParam(param)

  def delete(self, param):
    return olex_core.DeleteStoredParam(param)

  def print(self, scope=None):
    prefix = f"{scope}." if scope else None
    for k, v in self.defaults.items():
      if prefix and not k.startwith(prefix):
        continue
      print(f"{k}: {v}")

ins_header = OlxInsHeader()

class OlxInsHeaderScope():
  def __init__(self, scope:str):
    self.scope = scope

  def exists(self, param:str):
    return ins_header.exists(f"{self.scope}.{param}")

  def get(self, param:str, default=None):
    return ins_header.get(f"{self.scope}.{param}", default=default)

  def get_bool(self, param:str, default=None):
    return ins_header.get_bool(f"{self.scope}.{param}", default=default)

  def set(self, param:str, value):
    return ins_header.set(f"{self.scope}.{param}", str(value))

  def delete(self, param:str):
    return ins_header.delete(f"{self.scope}.{param}")

  def print(self):
    ins_header.print(self.scope)

#mainly for testing
olex.registerFunction(ins_header.register, False, "ins_header")
olex.registerFunction(ins_header.exists, False, "ins_header")
olex.registerFunction(ins_header.get, False, "ins_header")
olex.registerFunction(ins_header.get_bool, False, "ins_header")
olex.registerFunction(ins_header.set_, False, "ins_header")
olex.registerFunction(ins_header.delete, False, "ins_header")
olex.registerFunction(ins_header.print, False, "ins_header")
