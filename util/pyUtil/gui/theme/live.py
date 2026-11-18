"""Keep skin-dependent values current.

Many modules read skin colours into module variables when they are imported
(green = OV.GetParam('gui.green')), and ImageTools defines its fonts when it is
created.  Both happen before a skin is applied and never again, so a skin
could not change the status line, the battery or the image fonts.

A module now puts those reads into a function and registers it:

    def _skin_colours():
      global green, red
      green = OV.GetParam('gui.green')
      red = OV.GetParam('gui.red')
    on_skin_change(_skin_colours)        # also runs it once, now

gui.skin.Skin.change_skin calls skin_loaded() after the skin's parameters are
in place and before the GUI images are drawn: every registered function runs
again, and the image fonts are defined anew.

Kept free of other theme imports: modules register while Olex2 is starting.
"""
import functools
import sys

_readers = []


def _report(what, err):
  print("Theme: could not refresh %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def on_skin_change(fn):
  """Register fn, a function that reads skin values, and run it once now."""
  if fn not in _readers:
    _readers.append(fn)
  fn()
  return fn


def refresh_fonts():
  """ImageTools resolves DefaultFont (gui.default_font_name, ..._bold) and its
  own colours only in getOlexVariables, and keeps the gui params it was made
  with; renew both for the shared IT and the toolbar's TI."""
  from olexFunctions import OV
  from ImageTools import IT
  IT.getOlexVariables()
  IT.params = OV.GuiParams()
  from PilTools import TI
  TI.params = OV.GuiParams()


_vfs_calls = []
_replaying = [False]


def survives_vfs_clear(fn):
  """Decorator for what plugins do once at start-up to the virtual file system
  (index entries, header images).  change_skin clears that file system, so the
  calls are remembered, in order, and made again by restore_vfs()."""
  @functools.wraps(fn)
  def wrapper(*args, **kwargs):
    if _replaying[0]:  # called from a remembered call, or from the replay
      return fn(*args, **kwargs)
    call = (fn, args, kwargs)
    if call not in _vfs_calls:
      _vfs_calls.append(call)
    _replaying[0] = True
    try:
      return fn(*args, **kwargs)
    finally:
      _replaying[0] = False
  return wrapper


def restore_vfs():
  """After olx.fs.Clear and the redraw: make the remembered calls again."""
  _replaying[0] = True
  try:
    for fn, args, kwargs in list(_vfs_calls):
      try:
        fn(*args, **kwargs)
      except Exception as err:
        _report("%s%s" % (fn.__name__, args or kwargs), err)
  finally:
    _replaying[0] = False


def skin_loaded():
  """After a skin's parameters are loaded: re-read every registered value."""
  for fn in list(_readers):
    try:
      fn()
    except Exception as err:
      _report("%s.%s" % (fn.__module__, fn.__name__), err)
  try:
    refresh_fonts()
  except Exception as err:
    _report("the image fonts", err)
