import olex
import olx

def FileOpen(title, filter, location, default=''):
  res = olx.FileOpen(title, filter,location)
  if not res:
    return default
  return res

olex.registerFunction(FileOpen, False, "gui.dialog")
