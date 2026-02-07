import glob
import os

from olexFunctions import OV
def ov_register(func=None, flag=False, scope=None):
    """
    Register a function with OV.registerFunction in a flexible way.

    Usage:
      - As a plain call:
          ov_register(func)                       # flag=False, scope=<current file name>
          ov_register(func, False, "NoSpherA2")
      - As a decorator:
          @ov_register
          def f(...): ...
          @ov_register(False, "NoSpherA2")
          def g(...): ...
    """

    if scope is None:
        # import inspect
        # caller_file = inspect.stack()[1].filename
        # caller_mod = os.path.splitext(os.path.basename(caller_file))[0]
        scope = "NoSpherA2"

    def _decorate(f):
        OV.registerFunction(f, flag, scope)
        return f

    if callable(func):
        return _decorate(func)
    return _decorate

def find_basis_file(basis_name: str, json: bool = True):
    basis_dir = os.path.join(OV.BaseDir(), "basis_sets")
    if json:
        basis_list = [os.path.basename(i) for i in glob.glob(os.path.join(basis_dir, "*.json"))]
    else:
        basis_list = [i for i in os.listdir(basis_dir) if os.path.isfile(os.path.join(basis_dir, i)) and not i.endswith(".json")]

    for i in basis_list:
        if i.replace(".json", "").lower() == basis_name.lower():
            return os.path.join(basis_dir, i)

    raise FileNotFoundError("Couldn't find the basis file")