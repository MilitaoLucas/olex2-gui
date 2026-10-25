# Loads NSA2Folder (or reloads it after a change). In Olex2:
#   py.run basedir()/util/pyUtil/NoSpherA2/NSA2Folder/start.py
import importlib
import os
import sys

import olex

_p = os.path.join(olex.f("BaseDir()"), "util", "pyUtil", "NoSpherA2", "NSA2Folder")
if _p not in sys.path:
  sys.path.append(_p)

if "nsa2_folder" in sys.modules:
  importlib.reload(sys.modules["nsa2_runs"])
  importlib.reload(sys.modules["nsa2_folder"])
else:
  import nsa2_folder
