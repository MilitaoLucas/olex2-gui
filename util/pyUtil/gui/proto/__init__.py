try:
  import olex
except ImportError:
  # Outside Olex2 (unit tests): only db and cells are usable
  olex = None

if olex is not None:
  from . import proto
