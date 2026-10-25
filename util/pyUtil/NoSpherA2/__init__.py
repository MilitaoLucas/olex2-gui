from .NoSpherA2 import get_NoSpherA2_instance
from .utilities import is_disordered

# NSA2Folder: an optional tool in its own sub-folder (chips for the runs in
# olex2/NoSpherA2_history); switched on only when that folder is present
import os as _os
_nsa2folder = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "NSA2Folder")
if _os.path.isdir(_nsa2folder):
  import sys as _sys
  if _nsa2folder not in _sys.path:
    _sys.path.append(_nsa2folder)
  try:
    import nsa2_folder
  except Exception as _err:
    print("NSA2Folder could not be loaded: %s" % _err)
    if hasattr(_sys, '_wing_debugger'):
      raise
