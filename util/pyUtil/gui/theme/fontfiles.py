"""Font files of the theme, made usable by the operating system.

Image areas are drawn by PIL straight from a font file.  The console, the
labels of the 3D view and the panel text are drawn by the operating system,
which only knows installed fonts.  register() hands every font file in
DataDir/fonts and etc/gui/fonts to Windows for this process only
(AddFontResourceEx with FR_PRIVATE): nothing is installed, nothing outlives
Olex2, and the fonts can then be named like any installed font.

Other platforms: not done yet (macOS would need CTFontManagerRegisterFontsForURL).
"""
import os
import sys

EXTS = ('.ttf', '.otf')
FR_PRIVATE = 0x10

_registered = set()


def font_dirs():
  from olexFunctions import OV
  return [os.path.join(OV.DataDir(), 'fonts'), os.path.join(OV.BaseDir(), 'etc', 'gui', 'fonts')]


def supported():
  return sys.platform.startswith('win')


def register_file(path):
  """Make one font file known to the OS for this process; True on success."""
  key = os.path.normcase(os.path.abspath(path))
  if key in _registered:
    return True
  if not supported():
    return False
  import ctypes
  n = ctypes.windll.gdi32.AddFontResourceExW(ctypes.c_wchar_p(path), FR_PRIVATE, None)
  if not n:
    print("Windows did not take the font file '%s'" % path)
    return False
  _registered.add(key)
  return True


# --- vertical shift per font file ----------------------------------------------
# Fonts sit differently on their baseline; image text in a font is moved up by
# this many pixels (negative: down).  Kept beside the font files by stem.

_offsets = {'mtime': None, 'data': {}}


def offsets_path():
  from olexFunctions import OV
  return os.path.join(OV.DataDir(), 'fonts', 'font_offsets.json')


def offsets():
  import json
  path = offsets_path()
  try:
    mtime = os.path.getmtime(path)
  except OSError:
    _offsets.update(mtime=None, data={})
    return {}
  if mtime != _offsets['mtime']:
    try:
      with open(path, encoding='utf-8') as f:
        data = json.load(f)
      _offsets.update(mtime=mtime, data=dict((k, float(v)) for k, v in data.items()))
    except (OSError, ValueError, TypeError, AttributeError) as err:
      print("Cannot read %s: %s" % (path, err))
      _offsets.update(mtime=mtime, data={})
  return _offsets['data']


def set_offsets(stems, value):
  """Shift these font files (by stem) up by value px; 0 or None removes it."""
  import json
  data = dict(offsets())
  for stem in stems:
    if value:
      data[stem] = float(value)
    else:
      data.pop(stem, None)
  path = offsets_path()
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1, sort_keys=True)
  _offsets['mtime'] = None


def offset_for_key(font_key):
  """The shift of an image font key ('DefaultFont', 'DefaultFont Bold' or a file stem)."""
  data = offsets()
  if not data or not font_key:
    return 0.0
  if font_key in ('DefaultFont', 'DefaultFont Bold'):
    from olexFunctions import OV
    param = 'gui.default_font_name' + ('_bold' if font_key.endswith('Bold') else '')
    font_key = os.path.splitext(str(OV.GetParam(param, '') or ''))[0]
  return data.get(font_key, 0.0)


def register():
  """Register every font file of the font folders; returns how many are known."""
  if not supported():
    return 0
  for d in font_dirs():
    if not os.path.isdir(d):
      continue
    for fn in os.listdir(d):
      if os.path.splitext(fn)[1].lower() in EXTS:
        try:
          register_file(os.path.join(d, fn))
        except Exception as err:
          print("Cannot register the font '%s': %s" % (fn, err))
          if hasattr(sys, '_wing_debugger'):
            raise
  return len(_registered)
