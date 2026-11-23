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


# --- where image text sits -------------------------------------------------------
# PIL draws text from the font's ascender line, and every font puts that line
# at its own height above the capitals: Noto Sans' capitals sit 11% of the
# font size lower than Signika's.  The image layouts were made with Signika,
# so text in another font is moved up by the difference between the middles
# of the capitals, read from the font file itself: no font needs calibrating.
# Writing systems are measured separately (capital H, Greek Eta, Cyrillic En,
# an ideograph, alef), as a fallback font may set them differently.
#
# A fine adjustment, in percent of the font size, can be added per font file:
# <stem>.font.json {"shift_percent": 2.5} (positive: up), in DataDir/fonts or
# beside the font file.  It scales with the font size and travels with the font.
#
# Layout must not depend on the ink of the string being drawn either (Greek
# beta and gamma, or 'g' and 'p', reach below the baseline and made such text
# jump): baseline_px(), line_px() and middle_px() give string-independent
# measures.

MEASURE_SIZE = 1000
# Signika-Regular at 1000 px: ascender line to cap top / baseline / bottom of 'g'
REFERENCE = {'top': 0.253, 'bottom': 0.944, 'ascent': 0.940, 'descender': 1.161}
REFERENCE_MIDDLE = (REFERENCE['top'] + REFERENCE['bottom']) / 2

SCRIPT_CHARS = (('latin', 'H'), ('greek', 'Η'), ('cyrillic', 'Н'),
                ('cjk', '中'), ('arabic', 'ا'))
DESCENDER_CHARS = 'gpy'

_metrics = {}
_adjusts = {}


def script_of(text):
  """The writing system a text is measured by: the first letter outside Latin."""
  for c in text or '':
    o = ord(c)
    if o < 0x370 or c.isspace():
      continue
    if o <= 0x3FF or 0x1F00 <= o <= 0x1FFF:
      return 'greek'
    if o <= 0x52F:
      return 'cyrillic'
    if 0x600 <= o <= 0x6FF or 0x750 <= o <= 0x77F or 0xFB50 <= o <= 0xFEFF:
      return 'arabic'
    if o >= 0x2E80:
      return 'cjk'
  return 'latin'


def _codepoints(path):
  try:
    from fontTools.ttLib import TTFont
  except ImportError:
    return None  # cannot tell: every character is taken as present
  font = TTFont(path, lazy=True, fontNumber=0)
  try:
    return set(font.getBestCmap() or ())
  finally:
    font.close()


def _ink(font, text):
  """(top, bottom) of the ink of text, from the point PIL draws it at."""
  if hasattr(font, 'getbbox'):  # Pillow >= 8
    box = font.getbbox(text)
    return (box[1], box[3]) if box and box[3] > box[1] else None
  box = font.getmask(text).getbbox()  # Pillow 7: mask box plus the ink offset
  if not box:
    return None
  dy = font.getoffset(text)[1]
  return box[1] + dy, box[3] + dy


def measure(path):
  """Metrics of a font file as fractions of its size: 'ascent', 'descent',
  'descender' (bottom of g, p, y) and per writing system (top, bottom) of
  its reference glyph; None when the file cannot be read."""
  from PIL import ImageFont
  font = ImageFont.truetype(path, MEASURE_SIZE)
  s = float(MEASURE_SIZE)
  ascent, descent = font.getmetrics()
  m = {'ascent': ascent / s, 'descent': descent / s}
  try:
    cmap = _codepoints(path)
  except Exception as err:
    print("Cannot read the characters of %s: %s" % (path, err))
    cmap = None
  for script, ch in SCRIPT_CHARS:
    if cmap is not None and ord(ch) not in cmap:
      continue
    ink = _ink(font, ch)
    if ink:
      m[script] = (ink[0] / s, ink[1] / s)
  ink = _ink(font, DESCENDER_CHARS)
  m['descender'] = ink[1] / s if ink else (ascent + descent) / s
  return m


def metrics(path):
  """measure(path), kept while the file is unchanged."""
  if not path:
    return None
  key = os.path.normcase(os.path.abspath(path))
  try:
    mtime = os.path.getmtime(path)
  except OSError:
    return None
  hit = _metrics.get(key)
  if hit and hit[0] == mtime:
    return hit[1]
  try:
    m = measure(path)
  except (OSError, ValueError) as err:
    print("Cannot measure the font %s: %s" % (path, err))
    m = None
  _metrics[key] = (mtime, m)
  return m


def _font_path(font):
  return getattr(font, 'path', None) if font is not None else None


def _box(m, text):
  """(top, bottom) of the reference glyph of the text's writing system."""
  return m.get(script_of(text)) or m.get('latin')


def auto_fraction(path, text=''):
  """How far (fraction of the font size) text in this font file is moved up
  so that its capitals sit where Signika's do."""
  m = metrics(path)
  if not m:
    return 0.0
  box = _box(m, text)
  if box:
    middle = (box[0] + box[1]) / 2
  else:  # no reference glyph: scale Signika's middle by the ascent
    middle = REFERENCE_MIDDLE * m['ascent'] / REFERENCE['ascent']
  return middle - REFERENCE_MIDDLE


# --- fine adjustment per font file, in percent ------------------------------------

def _stem(path):
  return os.path.splitext(os.path.basename(path))[0]


def adjust_path(stem):
  """Where the fine adjustment of a font file is written: DataDir/fonts."""
  from olexFunctions import OV
  return os.path.join(OV.DataDir(), 'fonts', stem + '.font.json')


def _read_adjust(path):
  import json
  try:
    mtime = os.path.getmtime(path)
  except OSError:
    return None
  hit = _adjusts.get(path)
  if hit and hit[0] == mtime:
    return hit[1]
  value = None
  try:
    with open(path, encoding='utf-8') as f:
      value = float(json.load(f).get('shift_percent', 0) or 0)
  except (OSError, ValueError, TypeError, AttributeError) as err:
    print("Cannot read %s: %s" % (path, err))
  _adjusts[path] = (mtime, value)
  return value


def manual_percent(font_path):
  """The fine adjustment of a font file (percent of the size, up)."""
  if not font_path:
    return 0.0
  migrate_offsets()
  stem = _stem(font_path)
  for p in (adjust_path(stem), os.path.join(os.path.dirname(font_path), stem + '.font.json')):
    v = _read_adjust(p)
    if v is not None:
      return v
  return 0.0


def set_manual_percent(stems, value):
  """Fine adjustment of these font files (by stem), percent up; 0 or None removes it."""
  import json
  for stem in stems:
    path = adjust_path(stem)
    if value:
      os.makedirs(os.path.dirname(path), exist_ok=True)
      with open(path, 'w', encoding='utf-8') as f:
        json.dump({'shift_percent': round(float(value), 2)}, f, indent=1)
    elif os.path.exists(path):
      os.remove(path)
    _adjusts.pop(path, None)


# --- pixels for a PIL font ----------------------------------------------------------

def shift_px(font, text=''):
  """Pixels text in this PIL font is moved up: automatic plus fine adjustment."""
  path = _font_path(font)
  if not path:
    return 0.0
  size = getattr(font, 'size', 0) or 0
  return (auto_fraction(path, text) + manual_percent(path) / 100.0) * size


def fine_px(font):
  """Pixels up from the fine adjustment alone (text centred by middle_px)."""
  path = _font_path(font)
  if not path:
    return 0.0
  return manual_percent(path) / 100.0 * (getattr(font, 'size', 0) or 0)


def _metric_px(font, name, fallback):
  m = metrics(_font_path(font))
  size = getattr(font, 'size', 0) or 0
  if m and size:
    return m[name] * size if name in m else fallback(m) * size
  ascent, descent = font.getmetrics()
  return {'ascent': ascent, 'descender': ascent + descent}.get(name, ascent)


def baseline_px(font):
  """Drawing point to baseline: what text without descenders measures high."""
  return _metric_px(font, 'ascent', lambda m: m['ascent'])


def line_px(font):
  """Drawing point to the bottom of g, p, y: one line of text, whatever it says."""
  return _metric_px(font, 'descender', lambda m: m['ascent'] + m['descent'])


def middle_px(font, text=''):
  """Drawing point to the middle of the capitals: draw at y - middle_px to centre on y."""
  m = metrics(_font_path(font))
  size = getattr(font, 'size', 0) or 0
  box = _box(m, text) if m else None
  if box and size:
    return (box[0] + box[1]) / 2 * size
  return baseline_px(font) / 2


# --- the pixel offsets of before (DataDir/fonts/font_offsets.json) ------------------
# These were pixels at any font size; they become percent of MIGRATE_SIZE, the
# usual image font size, less what is now worked out automatically.

MIGRATE_SIZE = 14
_migrated = []


def offsets_path():
  from olexFunctions import OV
  return os.path.join(OV.DataDir(), 'fonts', 'font_offsets.json')


def migrate_offsets():
  """Turn font_offsets.json into fine adjustments once (kept as .old)."""
  if _migrated:
    return
  _migrated.append(True)
  import json
  path = offsets_path()
  if not os.path.exists(path):
    return
  try:
    with open(path, encoding='utf-8') as f:
      data = json.load(f)
  except (OSError, ValueError) as err:
    print("Cannot read %s: %s" % (path, err))
    return
  done = []
  for stem, px in data.items():
    font_path = None
    for d in font_dirs():
      for ext in EXTS:
        p = os.path.join(d, stem + ext)
        if os.path.isfile(p):
          font_path = font_path or p
    try:
      px = float(px)
    except (TypeError, ValueError):
      continue
    auto = auto_fraction(font_path) if font_path else 0.0
    percent = round((px / MIGRATE_SIZE - auto) * 100, 1)
    if abs(percent) >= 0.5 and not os.path.exists(adjust_path(stem)):
      set_manual_percent([stem], percent)
      done.append('%s %+g%%' % (stem, percent))
  os.replace(path, path + '.old')
  print("Font shifts are now worked out from the font files; what was set by hand "
        "is kept as percent of the font size: %s" % (', '.join(done) or 'nothing left'))


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
