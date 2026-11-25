"""Themes: the look of Olex2 as one named thing, usable without the
ThemeBuilder plugin.

A theme is a folder with theme.json (format 1):

  {"name", "description", "author", "version",
   "base":  {skin, extension, icon_set, parts_palette, gl_fonts, named, gui},
   "light": {style, scene, background, text_materials, gui},
   "dark":  {...the same...}}

'base' is what both looks share (fonts, icons, sizes, the skin family);
'light' and 'dark' are what makes each look (colours, 3D style and scene,
background).  A theme may have one look only.  Fonts, pictures and styles a
theme brings live in its folder (fonts/, styles/, pictures/), once.

Where themes are, the first one of a name wins:
  Olex2Data/themes/<name>/theme.json   installed (downloaded, or own)
  Olex2Data/themes/<name>.theme        saved by ThemeBuilder before 2026-11-25:
                                       one look, the flat dictionary
  BaseDir/etc/themes/<name>/theme.json shipped with Olex2 (Classic)

Three choices, each the user's own (user.theme in user.phil): the theme
(name), its look (light|dark) and the size (scale, see scale.py; part of the
screen, not of a theme).  Applying writes the composed look to the theme
overlay (overlay.py), so it is there at the next start without this module.

spy.gui.theme.use(name), spy.gui.theme.look(light|dark|toggle),
spy.gui.theme.size(factor), spy.gui.theme.theme_items() for the Settings row.
"""
import copy
import json
import os
import sys

FORMAT = 1
FILE = 'theme.json'
LOOKS = ('light', 'dark')
# keys of the flat dictionary that belong to a look, not to the base
LOOK_KEYS = ('style', 'scene', 'background', 'text_materials')


def _report(what, err):
  print("Themes: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


# --- reading (no Olex2 needed) ----------------------------------------------

def read_package(path):
  """theme.json at path as a dictionary, None if it cannot be read."""
  try:
    with open(path, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except (OSError, ValueError) as err:
    _report("read %s" % path, err)
    return None
  if not isinstance(data, dict) or not any(isinstance(data.get(k), dict) for k in LOOKS):
    print("Themes: %s has neither a light nor a dark look" % path)
    return None
  return data


def _luminance(hex_colour):
  c = str(hex_colour or '').lstrip('#')
  if len(c) < 6:
    return None
  try:
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
  except ValueError:
    return None
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def legacy_look(flat):
  """'dark' or 'light' for a theme saved as one flat dictionary: its
  gui.appearance, else the brightness of its panel background."""
  gui = flat.get('gui') or {}
  appearance = str(gui.get('appearance', '')).lower()
  if appearance in LOOKS:
    return appearance
  lum = _luminance(gui.get('html.bg_colour'))
  if lum is not None:
    return 'dark' if lum < 0.5 else 'light'
  # no panel colour of its own: the skin's (moderndark, flexokidark...)
  return 'dark' if 'dark' in str(flat.get('skin') or '').lower() else 'light'


def from_flat(flat, name=None):
  """A flat (ThemeBuilder) theme as a package with one look."""
  flat = copy.deepcopy(flat)
  look = legacy_look(flat)
  base = {k: v for k, v in flat.items() if k not in LOOK_KEYS + ('gui', 'description', 'author')}
  base['gui'] = {}
  part = {k: flat[k] for k in LOOK_KEYS if k in flat}
  part['gui'] = flat.get('gui') or {}
  return {'format': FORMAT, 'name': name, 'description': flat.get('description', ''),
          'author': flat.get('author', ''), 'base': base, look: part}


def looks_of(package):
  return [k for k in LOOKS if isinstance(package.get(k), dict)]


def compose(package, look):
  """The flat dictionary of one look (base laid under the look; the gui
  values merged key by key), None if the theme has no such look."""
  part = package.get(look)
  if not isinstance(part, dict):
    return None
  flat = copy.deepcopy(package.get('base') or {})
  gui = dict(flat.get('gui') or {})
  for k, v in part.items():
    if k == 'gui':
      gui.update(v or {})
    else:
      flat[k] = copy.deepcopy(v)
  flat['gui'] = gui
  flat.setdefault('skin', 'default')
  flat.setdefault('extension', '')
  return flat


LOOK_SUFFIXES = {'_dark': 'dark', '_light': 'light'}


def flat_name_and_look(stem):
  """'CLASSIC_DARK' -> ('CLASSIC', 'dark'); 'HP02' -> ('HP02', None): old
  ThemeBuilder files saved one look each, the dark one often as <name>_DARK."""
  low = stem.lower()
  for suffix, look in LOOK_SUFFIXES.items():
    if low.endswith(suffix) and len(stem) > len(suffix):
      return stem[:-len(suffix)], look
  return stem, None


def scan(folders):
  """{name: {'name', 'looks', 'path', 'dir', 'kind', 'description'}} for the
  themes in folders.  kind: 'package' (a folder with theme.json) or 'flat'
  (old .theme files: <name>.theme, and <name>_DARK / _LIGHT.theme as the
  other look of the same theme; 'paths' gives each look's file).  Names are
  compared ignoring case: a package beats old files of the same name (the
  shipped Classic replaces CLASSIC + CLASSIC_DARK), and between packages or
  between files the first folder wins."""
  packages, flats = {}, {}
  for folder in folders:
    if not folder or not os.path.isdir(folder):
      continue
    for entry in sorted(os.listdir(folder), key=str.lower):
      if entry.startswith('_') or entry.startswith('.'):
        continue
      full = os.path.join(folder, entry)
      if os.path.isdir(full) and os.path.isfile(os.path.join(full, FILE)):
        data = read_package(os.path.join(full, FILE))
        if data is None:
          continue
        name = data.get('name') or entry
        packages.setdefault(name.lower(), {
          'name': name, 'looks': looks_of(data), 'path': os.path.join(full, FILE), 'dir': full,
          'kind': 'package', 'description': data.get('description', '')})
      elif entry.lower().endswith('.theme') and os.path.isfile(full):
        try:
          with open(full, 'r', encoding='utf-8') as f:
            flat = json.load(f)
        except (OSError, ValueError) as err:
          _report("read %s" % full, err)
          continue
        name, look = flat_name_and_look(entry[:-len('.theme')])
        look = look or legacy_look(flat)
        group = flats.setdefault(name.lower(), {
          'name': name, 'looks': [], 'paths': {}, 'path': full, 'dir': folder,
          'kind': 'flat', 'description': flat.get('description', '')})
        if look not in group['paths']:
          group['paths'][look] = full
          group['looks'] = [k for k in LOOKS if k in group['paths']]
  found = {}
  for key, entry in list(packages.items()) + list(flats.items()):
    if key not in found:
      found[key] = entry
  return {e['name']: e for e in found.values()}


def find(themes, name):
  """The entry for name, ignoring case; None if there is none."""
  if not name:
    return None
  if name in themes:
    return themes[name]
  low = name.lower()
  for n, entry in themes.items():
    if n.lower() == low:
      return entry
  # an old choice like CLASSIC_DARK: the theme it is a look of
  base, _ = flat_name_and_look(name)
  return find(themes, base) if base != name else None


def load(entry):
  """The package of a scanned entry (old .theme files joined into one)."""
  if entry['kind'] == 'package':
    return read_package(entry['path'])
  package = None
  for look, path in entry['paths'].items():
    try:
      with open(path, 'r', encoding='utf-8') as f:
        flat = json.load(f)
    except (OSError, ValueError) as err:
      _report("read %s" % path, err)
      continue
    one = from_flat(flat, entry['name'])
    if package is None:
      package = {k: v for k, v in one.items() if k not in LOOKS}
      package['base'] = {}  # each file is a whole look: the two may use different skins
    package[look] = compose(one, legacy_look(flat))
  return package


def pick_look(wanted, looks):
  """The look to show: the wanted one if the theme has it, else the one it has."""
  if wanted in looks:
    return wanted
  return looks[0] if looks else None


# --- in Olex2 -----------------------------------------------------------------

def user_dir():
  from olexFunctions import OV
  return os.path.join(os.path.dirname(os.path.normpath(OV.DataDir())), 'themes')


def shipped_dir():
  from olexFunctions import OV
  return os.path.join(OV.BaseDir(), 'etc', 'themes')


def available():
  return scan([user_dir(), shipped_dir()])


def current():
  """(theme name or None, look) as chosen by the user."""
  from olexFunctions import OV
  name = OV.GetParam('user.theme.name')
  look = OV.GetParam('user.theme.look') or 'light'
  return (None if name in (None, '', 'None') else name), look


def _skin_exists(skin):
  from olexFunctions import OV
  return skin == 'default' or os.path.isfile(os.path.join(OV.BaseDir(), 'etc', 'skins', skin + '.phil'))


def _style_path(kind, name, theme_dir, shipped):
  """A style (.glds) or scene (.glsp): the theme's own first, then the user's
  styles folder, then etc/styles; a shipped theme takes etc/styles first."""
  from olexFunctions import OV
  ext = {'style': '.glds', 'scene': '.glsp'}[kind]
  own = [os.path.join(theme_dir, 'styles')] if theme_dir else []
  user = os.path.join(OV.DataDir(), 'styles')
  etc = os.path.join(OV.BaseDir(), 'etc', 'styles')
  for d in (own + [etc, user] if shipped else own + [user, etc]):
    p = os.path.join(d, name + ext)
    if os.path.isfile(p):
      return p
  return None


def apply_flat(data, name, theme_dir=None, shipped=False):
  """Show a composed look (the flat dictionary).  True if applied."""
  import olex
  import olx
  from olexFunctions import OV
  from gui.theme import overlay, icons, background, glcolours
  skin = data.get('skin') or 'default'
  if not _skin_exists(skin):
    print("The theme '%s' needs the skin '%s', which is not installed" % (name, skin))
    return False
  overlay.replace(skin, data.get('gui', {}), name, data.get('background'),
                  {'named': data.get('named') or {},
                   'text_materials': data.get('text_materials') or {}})
  if data.get('icon_set') in icons.SETS:
    OV.SetParam('user.icon_set', data['icon_set'])
  ext = data.get('extension') or ''
  olex.m('skin %s' % ('%s_%s' % (skin, ext) if ext else skin))
  icons.rebuild()
  for kind in ('style', 'scene'):
    if not data.get(kind):
      continue
    p = _style_path(kind, data[kind], theme_dir, shipped)
    if not p:
      print("The theme '%s' wants the %s '%s', which was not found" % (name, kind, data[kind]))
      continue
    if kind == 'scene':
      olex.m('grad false')  # a scene brings its own background
    olex.m('load %s "%s"' % (kind, p))
    OV.SetParam('user.def_%s' % kind, data[kind])
  if not data.get('gl_fonts'):  # the console and label fonts of the skin, as at a start
    from gui.skin import set_gl_fonts
    set_gl_fonts()
  # after the skin and the scene, which both set a background of their own
  background.apply(base_dir=theme_dir)
  for slot, font in (data.get('gl_fonts') or {}).items():  # after the scene's fonts
    if font:
      olx.SetFont(slot, font)
  glcolours.apply(restore=True)  # after the style, which has label colours
  if data.get('parts_palette'):
    from gui.disorder import set_palette
    set_palette(data['parts_palette'])
  try:  # the designer's named objects and atom colours, if it is installed
    import themebuilder_atoms
  except ImportError:
    themebuilder_atoms = None
  if themebuilder_atoms is not None:
    themebuilder_atoms.reapply()
  return True


def use(name=None, look=None):
  """spy.gui.theme.use([name][, light|dark]): show a theme in the chosen (or
  the given) look; the choice is kept for this user.  True if applied."""
  from olexFunctions import OV
  import olex
  cur_name, cur_look = current()
  name = name or cur_name
  look = look or cur_look
  if name == SERVER_MORE:  # 'More from the server': read the list, show it
    server_index(refresh=True)
    return False
  if name and name.startswith(SERVER_PREFIX):  # a theme from the server
    name = install(name[len(SERVER_PREFIX):])
    if not name:
      return False
  themes = available()
  entry = find(themes, name)
  if entry is None:
    print("No theme called '%s' (%s)" % (name, ', '.join(sorted(themes)) or 'none installed'))
    return False
  name = entry['name']  # as the theme spells it (CLASSIC -> Classic)
  package = load(entry)
  if package is None:
    return False
  shown = pick_look(look, looks_of(package))
  if shown != look:
    print("The theme '%s' has no %s look; it is shown %s." % (name, look, shown))
  flat = compose(package, shown)
  shipped = os.path.normcase(os.path.normpath(entry['dir'])).startswith(
    os.path.normcase(os.path.normpath(shipped_dir())))
  if not apply_flat(flat, name, entry['dir'] if entry['kind'] == 'package' else None, shipped):
    return False
  OV.SetParam('user.theme.name', name)
  OV.SetParam('user.theme.look', look)  # the wish stays, also if this theme lacks it
  olex.m('spy.SaveUserParams()')
  return True


def look(which='toggle'):
  """spy.gui.theme.look(light|dark|toggle): the other look of the theme in use."""
  name, cur = current()
  which = (which or 'toggle').lower()
  if which == 'toggle':
    which = 'dark' if cur == 'light' else 'light'
  if which not in LOOKS:
    print("A look is light or dark, not '%s'" % which)
    return False
  if not name:  # no theme chosen yet: the shipped one
    name = 'Classic'
  return use(name, which)


def size(factor):
  """spy.gui.theme.size(factor): the size of the whole GUI for this user
  (1.0 to 2.0 in steps), shown at once."""
  import olex
  from olexFunctions import OV
  from gui.theme import scale
  scale.set_factor(factor)
  skin = OV.GetParam('gui.skin.name', 'default') or 'default'
  ext = OV.GetParam('gui.skin.extension', '') or ''
  olex.m('skin %s' % ('%s_%s' % (skin, ext) if ext else skin))
  return True


def theme_items():
  """Combo items for the Settings row: installed and shipped themes, then the
  server's themes not installed here (once the list was read this session),
  then 'More from the server'.  No brackets in labels: Olex2 evaluates them."""
  names = sorted(available(), key=str.lower)
  items = list(names)
  have = {n.lower() for n in names}
  for t in (_server_cache.get('themes') or []):
    if t['name'].lower() not in have:
      items.append('%s - download<-%s%s' % (t['name'], SERVER_PREFIX, t['name']))
  items.append('More from the server<-%s' % SERVER_MORE)
  return ';'.join(i.replace(';', ',') for i in items)


# --- the theme server -----------------------------------------------------------
# A folder on the web with olex2-themes.json ({"format": 1, "themes": [{"name",
# "file", "looks", "version", "description", "author", "size"}]}) and the zips
# (a theme folder, theme.json at the top).  Made by olex2_dev_bits/themes/
# build_themes.py.  Read only when asked ('More from the server').

DEFAULT_SERVER = 'https://secure.opencryst.org/samples/themes'
INDEX = 'olex2-themes.json'
SERVER_PREFIX = 'server:'
SERVER_MORE = 'server-list'
TIMEOUT = 10
# what a theme zip may hold; anything else is left out
ALLOWED = ('.json', '.glds', '.glsp', '.ttf', '.otf', '.png', '.jpg', '.jpeg', '.txt', '.md', '')
_server_cache = {}


def server_url():
  from olexFunctions import OV
  return (OV.GetParam('user.theme.server') or DEFAULT_SERVER).rstrip('/')


def _network_allowed():
  from olexFunctions import OV
  return str(OV.GetParam('olex2.network', True)).lower() not in ('false', '0')


def _fetch(url):
  try:
    from HttpTools import make_url_call
    res = make_url_call(url, None, http_timeout=TIMEOUT)  # by name: r7898 added headers before it
  except ImportError:  # outside Olex2
    from urllib.request import urlopen
    res = urlopen(url, None, timeout=TIMEOUT)
  try:
    return res.read()
  finally:
    res.close()


def parse_index(data):
  """The themes listed in olex2-themes.json (bytes or str); [] if unreadable."""
  try:
    if isinstance(data, bytes):
      data = data.decode('utf-8')
    index = json.loads(data)
  except (ValueError, UnicodeDecodeError) as err:
    _report("read the server's theme list", err)
    return []
  out = []
  for t in (index.get('themes') if isinstance(index, dict) else None) or []:
    if isinstance(t, dict) and t.get('name') and str(t.get('file', '')).lower().endswith('.zip'):
      name = str(t['name'])
      if '/' in name or '\\' in name or name.startswith('.') or name.startswith('_'):
        continue
      out.append({'name': name, 'file': str(t['file']), 'looks': t.get('looks') or [],
                  'version': t.get('version', ''), 'description': t.get('description', '')})
  return out


def server_index(refresh=False):
  """The server's themes, read once per session (refresh: again)."""
  if refresh or 'themes' not in _server_cache:
    if not _network_allowed():
      print("Network operations are switched off (Settings): no themes from the server.")
      _server_cache['themes'] = []
      return []
    try:
      _server_cache['themes'] = parse_index(_fetch('%s/%s' % (server_url(), INDEX)))
    except Exception as err:  # no network, server down: say so, keep working
      _report("reach the theme server %s" % server_url(), err)
      _server_cache['themes'] = []
    n = len(_server_cache['themes'])
    print("Theme server: %d theme%s" % (n, '' if n == 1 else 's'))
  return _server_cache['themes']


def safe_members(names):
  """The zip member names that may be unpacked: plain relative paths of
  allowed kinds (no '..', no absolute paths, no drive letters)."""
  ok = []
  for n in names:
    if n.endswith('/'):
      continue
    parts = n.replace('\\', '/').split('/')
    if n.startswith('/') or ':' in n or any(p in ('', '.', '..') for p in parts):
      continue
    if os.path.splitext(n)[1].lower() not in ALLOWED:
      continue
    ok.append(n)
  return ok


def unpack(zip_bytes, dest):
  """Unpack a theme zip into dest (replaced); True if it held a theme.json."""
  import io
  import tempfile
  import zipfile
  try:
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
  except zipfile.BadZipFile as err:
    _report("open the theme zip", err)
    return False
  members = safe_members(z.namelist())
  if FILE not in members:
    print("The theme zip has no %s at its top" % FILE)
    return False
  parent = os.path.dirname(dest)
  os.makedirs(parent, exist_ok=True)
  tmp = tempfile.mkdtemp(prefix='_new_', dir=parent)
  try:
    for n in members:
      target = os.path.join(tmp, *n.split('/'))
      os.makedirs(os.path.dirname(target), exist_ok=True)
      with z.open(n) as src, open(target, 'wb') as out:
        out.write(src.read())
    if read_package(os.path.join(tmp, FILE)) is None:
      return False
    if os.path.isdir(dest):
      import shutil
      shutil.rmtree(dest)
    os.replace(tmp, dest)
    tmp = None
    return True
  finally:
    if tmp and os.path.isdir(tmp):
      import shutil
      shutil.rmtree(tmp, ignore_errors=True)


def install(name):
  """Download a server theme into Olex2Data/themes/<name>; its name, or None."""
  t = next((t for t in server_index() if t['name'].lower() == str(name).lower()), None)
  if t is None:
    print("The theme server has no theme '%s'" % name)
    return None
  url = '%s/%s' % (server_url(), t['file'])
  try:
    data = _fetch(url)
  except Exception as err:
    _report("download %s" % url, err)
    return None
  if not unpack(data, os.path.join(user_dir(), t['name'])):
    return None
  print("Theme '%s' installed in %s" % (t['name'], user_dir()))
  return t['name']


def current_name():
  """The theme in use for the Settings combo; Classic before any was chosen."""
  entry = find(available(), current()[0] or 'Classic')
  return entry['name'] if entry else 'Classic'


def has_look(which):
  """'true' if the theme in use has that look (for the Settings buttons)."""
  name, _ = current()
  entry = find(available(), name or 'Classic')
  return 'true' if entry and which in entry['looks'] else 'false'


def register():
  from olexFunctions import OV
  for f in (use, look, size, theme_items, has_look, current_name):
    OV.registerFunction(f, False, 'gui.theme')
