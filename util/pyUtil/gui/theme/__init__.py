"""Theme: how Olex2 looks -- icon set, theme overlay, redraw hooks.

The shipped part of the theme work.  The data stays in etc/ where Olex2 loads
it from: skins in etc/skins, 3D styles (.glds) and scenes (.glsp) in
etc/styles, icon sources in etc/gui/images/src.

  icons.py      classic/flat icon set: switching, painting, VFS images
  flaticons.py  the flat sprite format and colour roles (PIL only)
  overlay.py    values laid over the skin (DataDir/theme_overlay.json)
  live.py       hooks that survive skin changes and VFS clears

The theme designer is the ThemeBuilder plugin (plugin-ThemeBuilder); the icon
build script and the contributed styles are developer tools in the DevTools
plugin (plugin-DevTools, not shipped).
See README.md in this folder.
"""
from olexFunctions import OV

from . import icons
from . import snumtitle
from . import fontfiles
from . import glcolours

# theme font files usable by the console, 3D labels and panel text; before the
# first skin load sets those fonts
try:
  fontfiles.register()
except Exception as err:
  print("Theme font files not registered: %s" % err)
  import sys
  if hasattr(sys, '_wing_debugger'):
    raise


def designer(tab=''):
  """spy.gui.theme.designer([skin|fonts|view3d|atoms|lighting|icons|parts|themes]):
  open the theme designer of the ThemeBuilder plugin."""
  try:
    import themebuilder_design as d
  except ImportError as err:
    if err.name != 'themebuilder_design':
      raise
    print("The theme designer is part of the ThemeBuilder plugin, which is not installed.")
    return
  d.open_window(tab)


def has_designer():
  """spy.gui.theme.has_designer(): whether the ThemeBuilder plugin is installed
  (Olex2 puts an installed plugin's folder on sys.path)."""
  import importlib.util
  return importlib.util.find_spec('themebuilder_design') is not None


OV.registerFunction(icons.set_icon_set, False, 'gui.theme')
OV.registerFunction(snumtitle.set_file_type_mark, False, 'gui.theme')
OV.registerFunction(designer, False, 'gui.theme')
OV.registerFunction(has_designer, False, 'gui.theme')
OV.registerFunction(glcolours.text_colours_probe, False, 'gui.theme')
OV.registerFunction(glcolours.text_colours_update, False, 'gui.theme')
