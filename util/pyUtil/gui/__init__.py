import olex
import olx

def FileOpen(title, filter, location, default=''):
  res = olx.FileOpen(title, filter,location)
  if not res:
    return default
  return res

olex.registerFunction(FileOpen, False, "gui.dialog")

def About():
  sz = [int(i) for i in olx.GetWindowSize().split(',')]
  w = int(olx.ClientWidth('self'))
  h = int(olx.ClientHeight('self'))
  sw = 400+2*15+10
  sh = 249+2*15+150
  olx.Popup("about '%s/etc/gui/help/about.htm' -x=%d -y=%d -w=%d -h=%d"
            %(olx.BaseDir(),
              sz[0] + w/2 + sw/2,
              sz[1] + h/2 - sh/2,
              sw,
              sh))

olex.registerFunction(About, False, "gui")
