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

