"""What the user chose in the designer, laid over the skin.

Loading a skin resets the whole gui scope, and that happens at every start and
once more for every plugin (PluginTools -> deal_with_gui_phil).  Whatever only
lives in the gui scope is gone by then, so choices are kept here, in
DataDir/theme_overlay.json, and deal_with_gui_phil adds them as one more phil
text after the skin and its size extension.

The values belong to one skin: 'skin moderndark' at the command line shows that
skin as it was made.  The designer moves them along when it changes the skin.

Keys are gui parameters without the 'gui.' prefix: 'timage.h1.font_name'.

Kept free of other theme imports: it is read while Olex2 is starting.
"""
import json
import os
import sys

_data = None


def _empty():
  # theme: the saved theme in use, None once something changed;
  # base: the saved theme last chosen or saved, kept through changes
  # background: the 3D background (background.py), not a gui parameter
  return {'skin': None, 'theme': None, 'base': None, 'gui': {}, 'background': {}}


def _path():
  from olexFunctions import OV
  return os.path.join(OV.DataDir(), 'theme_overlay.json')


def _report(what, err):
  print("Theme: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def _load():
  global _data
  if _data is not None:
    return _data
  _data = _empty()
  path = _path()
  if os.path.isfile(path):
    try:
      with open(path, 'r', encoding='utf-8') as f:
        _data.update(json.load(f))
    except (OSError, ValueError) as err:
      _data = _empty()
      _report("read %s" % path, err)
  return _data


def _save():
  try:
    with open(_path(), 'w', encoding='utf-8') as f:
      json.dump(_load(), f, indent=1, sort_keys=True)
  except OSError as err:
    _report("write %s" % _path(), err)


def _literal(value):
  if isinstance(value, (bool, int, float)):
    return str(value)
  return "'%s'" % str(value).replace("'", "")


def phil_text(values):
  """{'timage.h1.font_name': 'x'} as a gui { ... } block, '' when empty."""
  if not values:
    return ''
  tree = {}
  for key, value in values.items():
    node = tree
    parts = key.split('.')
    for part in parts[:-1]:
      node = node.setdefault(part, {})
    node[parts[-1]] = value

  def show(node, indent):
    lines = []
    for name in sorted(node):
      if isinstance(node[name], dict):
        lines += ['%s%s {' % (indent, name)] + show(node[name], indent + '  ') + [indent + '}']
      else:
        lines.append('%s%s = %s' % (indent, name, _literal(node[name])))
    return lines

  return '\n'.join(['gui {'] + show(tree, '  ') + ['}'])


def phil_for(skin_name):
  """The phil text to lay over this skin, '' if the values belong to another."""
  d = _load()
  return phil_text(d['gui']) if d['skin'] == skin_name else ''


def values():
  return dict(_load()['gui'])


def theme():
  """The name of the saved theme in use, None once something has changed."""
  return _load()['theme']


def base():
  """The saved theme last chosen or saved, also after changes; None if none."""
  d = _load()
  return d.get('base') or d['theme']


def mark_changed():
  d = _load()
  if d['theme'] is not None:
    d['theme'] = None
    _save()


def set_param(key, value):
  """Set gui.<key> now and keep it over restarts; None forgets it."""
  from olexFunctions import OV
  OV.SetParam('gui.%s' % key, value)
  d = _load()
  d['skin'] = OV.GetParam('gui.skin.name', 'default') or 'default'
  d['theme'] = None
  if value is None:
    d['gui'].pop(key, None)
  else:
    d['gui'][key] = value
  _save()


def remove(*keys):
  """Forget these keys; the next skin load brings back the skin's values."""
  d = _load()
  for key in keys:
    d['gui'].pop(key, None)
  d['theme'] = None
  _save()


def retag(skin_name):
  """The values now belong to this skin."""
  d = _load()
  d['skin'] = skin_name
  d['theme'] = None
  _save()


def replace(skin_name, gui_values, theme_name=None, background=None, sections=None):
  """Take over the values of a saved theme; sections are further designer
  settings by key (section())."""
  global _data
  _data = {'skin': skin_name, 'theme': theme_name, 'base': theme_name, 'gui': dict(gui_values),
           'background': dict(background or {})}
  for key, value in (sections or {}).items():
    _data[key] = dict(value or {})
  _save()


def background():
  """The 3D background settings (background.py); {} for Olex2's own."""
  return dict(_load().get('background') or {})


def set_background(values):
  """Keep the 3D background settings; marks the look as changed."""
  d = _load()
  d['background'] = dict(values)
  d['theme'] = None
  _save()


def section(key):
  """Further settings of the designer kept here by key (e.g. 'named': the
  named 3D objects); {} if none."""
  return dict(_load().get(key) or {})


def set_section(key, values):
  """Keep one section; marks the look as changed."""
  d = _load()
  d[key] = dict(values)
  d['theme'] = None
  _save()
