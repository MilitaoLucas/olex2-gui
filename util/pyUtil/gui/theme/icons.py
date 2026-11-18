"""The icon set of the theme: classic (etc/gui/images/src/icons.png) or flat.

user.icon_set = classic|flat.  The flat icons are drawn as SVG in
etc/gui/images/src/icons/, built into icons_flat.png (build/build_icons.py) and
painted here in the skin colours (flaticons.py, gui.icons.* in gui.params).
Anything the flat set has not drawn yet comes from the classic set.

PilTools keeps the classic drawing and asks this module at four places:
  load()                          open_icon_source: read the sheet and palette
  toolbar_cell(key)               icon_items: the flat cell, or None for classic
  toolbar_border(border, state)   icon_items: the frame round an icon
  make_action_and_player_images() end of make_icon_items
"""
import os

import olex
import OlexVFS
from olexFunctions import OV
from PIL import Image

from . import flaticons

SETS = ('classic', 'flat')
# toolbar names that share one flat drawing
ALIASES = {'mask_same': 'mask', 'mask_ok': 'mask'}
# toolbar names whose colour carries a state, as role overrides: the solvent
# mask button is red while the formula ignores the masked content
# (gui.tools, toolbar-mask_same) and green when it is fine (toolbar-mask_ok).
# The classic set tints these with PilTools 'colourise'; a flat icon is
# painted in the colour instead (tinted() tells icon_items to skip that).
TINTS = {
  'mask_same': {'ink': 'red', 'acc': 'red', 'sec': 'red'},
  'mask_ok': {'ink': 'green', 'acc': 'green', 'sec': 'green'},
}

_sheet = None    # flaticons.IconSheet, or None with the classic set
_palette = None


def current():
  return OV.GetParam('user.icon_set', 'classic')


def sprite_path():
  return os.path.join(OV.BaseDir(), 'etc', 'gui', 'images', 'src', 'icons_flat.png')


def load():
  """Read the flat sheet and paint palette for the current set and skin."""
  global _sheet, _palette
  _sheet = _palette = None
  if current() != 'flat':
    return
  path = sprite_path()
  if not os.path.exists(path):
    print("Flat icon set not found (%s), using the classic icons" % path)
    return
  _sheet = flaticons.IconSheet(path)
  _palette = flaticons.palette_from_params(OV.GuiParams())


def flat_icon(key, state='off', size=None):
  """The flat icon 'key' as RGBA, or None if the flat set is off or lacks it."""
  overrides = dict(flaticons.STATE_OVERRIDES.get(state) or {})
  overrides.update(TINTS.get(key, {}))
  key = ALIASES.get(key, key)
  if not (_sheet and _sheet.has(key)):
    return None
  im = _sheet.icon(key, _palette, overrides)
  if size:
    im = im.resize(size, Image.LANCZOS)
  return im


def toolbar_cell(key):
  """64 px cell for PilTools.icon_items, or None to use the classic one."""
  return flat_icon(key) if key else None


def tinted(key):
  """True if the flat cell for 'key' already carries its state colour."""
  return key in TINTS and bool(_sheet) and _sheet.has(ALIASES.get(key, key))


def toolbar_border(border, state):
  """With the flat set and gui.icons.border off, the frame only shows the state."""
  if border and _sheet and not OV.GetParam('gui.icons.border', True):
    return state in ('hover', 'on', 'highlight', 'hoveron')
  return border


def make_action_and_player_images():
  """action-<which>_<state>.png (gui.images.get_action_button_html) and
  player-<which>.png (crystal image player) in the VFS, from the current set."""
  base = OV.BaseDir()
  action_dir = OV.GetParam("gui.GuiImages.action") or "%s/etc/gui/images/action" % base
  for which in ('up', 'down', 'delete', 'edit'):
    for state in ('off', 'on', 'hover'):
      im = flat_icon(which, state, size=(64, 64))
      if im is None:
        im = Image.open("%s/%s_%s.png" % (action_dir, which, state))
      OlexVFS.save_image_to_olex(im, "action-%s_%s.png" % (which, state), 2)
  size = int(OV.GetParam('gui.skin.icon_size'))
  for which in ('back', 'forward', 'play', 'stop'):
    im = flat_icon('player-%s' % which, size=(size, size))
    if im is None:
      im = Image.open("%s/etc/gui/images/player/%s.png" % (base, which))
    OlexVFS.save_image_to_olex(im, "player-%s.png" % which, 2)


def rebuild():
  """Redraw the toolbar, action and player icons after a set or colour change."""
  from PilTools import TI
  TI.params = OV.GuiParams()
  TI.basedir = OV.BaseDir()
  TI.no_need_to_refresh_image_type.pop('icons', None)
  TI.make_icon_items()
  olex.m('html.Update')


def set_icon_set(name=''):
  """spy.gui.theme.set_icon_set([classic|flat]): switch the toolbar and button
  icons; without an argument it toggles.  Kept in user.icon_set (the user scope
  survives a skin change, which resets the gui scope)."""
  if not name:
    name = 'flat' if current() == 'classic' else 'classic'
  if name not in SETS:
    print("Unknown icon set '%s': use 'classic' or 'flat'" % name)
    return
  OV.SetParam('user.icon_set', name)
  olex.m('spy.SaveUserParams()')
  rebuild()
  print("Icon set: %s" % name)
