
import olex_core
from decors import return_str
import olx
from olexFunctions import OV
"""
typical content of defaults:
  param_defaults = {
    'refinement.beam_n': (10, 'aced.user.defaults.starting.n_beams'),
    'thickness.value': (400, 'aced.user.defaults.starting.thickness'),
    'thickness.grad': True,
  }

"""
class OlxInsHeader:
  param_defaults = {
  }

  def register(self, name: str, default):
    self.param_defaults[name] = default

  def register_dict(self, params: dict):
    self.param_defaults.update(params)

  def set_stored_param(self, param, value):
    olex_core.SetStoredParam(param, value)

  def _get_param_default(self, param, default):
    rv = self.param_defaults.get(param, default)
    if isinstance(rv, tuple):
      return OV.GetParam(rv[1], rv[0])
    return rv

  @return_str(skip_types=set([dict,list,set]))
  def get_stored_param(self, param, default=None, src=None):
    p = olex_core.FindStoredParam(param)
    if not p:
      return self._get_param_default(param, default)
    return p

  def get_stored_param_bool(self, param, default=None) -> bool:
    rv = self.get_stored_param(param, default)
    if rv and rv.lower() == 'true':
      return True
    return False

  def stored_param_exists(self, param):
    return olex_core.HasStoredParam(param)

  def delete_stored_param(self, param):
    return olex_core.DeleteStoredParam(param)

  def print_params(self):
    print(self.param_defaults)

ins_header = OlxInsHeader()

OV.registerFunction(ins_header.register, False, "ins_header")
OV.registerFunction(ins_header.set_stored_param, False, "ins_header")
OV.registerFunction(ins_header.get_stored_param, False, "ins_header")
OV.registerFunction(ins_header.get_stored_param_bool, False, "ins_header")
OV.registerFunction(ins_header.delete_stored_param, False, "ins_header")
OV.registerFunction(ins_header.stored_param_exists, False, "ins_header")
