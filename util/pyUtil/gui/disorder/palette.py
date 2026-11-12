"""Colours for disorder PARTs: one for every part number, positive or negative.

Designed in OKLCH (perceptual lightness, chroma, hue), so equal steps look
equal, and checked in OKLab (distance(); the full printed check is
palette_tools/report.py in the DevTools plugin):

  - The parts of a pair (1/2, 3/4, ...) differ in hue *and* lightness, so they
    stay apart in grey print and for colour-blind viewers; 1/2, by far the most
    common, is the blue/amber pair that survives every kind of colour blindness.
  - No part looks like the atoms it sits next to: carbon grey, hydrogen white,
    nitrogen blue, oxygen red.
  - Negative parts (special positions) get quieter, earthier colours of their
    own, so -1 never reads as 1.
  - Beyond the designed ones, pairs continue round the hue circle by the golden
    angle, so any number of parts gets a colour.

Besides this 'contrast' palette there are tone-in-tone ones (TONES), chosen
with spy.gui.disorder.set_palette(name) and kept in user.parts.palette.

This is the only place part colours are defined (gui.params no longer holds
any).  No Olex2 imports: tested with tests/test_palette.py.
"""
import math

# (lightness, chroma, hue in degrees)
# Tuned with the DevTools palette report: every two of these are >= 0.10 apart in OKLab, every one
# >= 0.11 from C, H, N and O, and each pair stays apart for protan, deutan and
# tritan vision.  In a pair the lightness differs by >= 0.16, which is what
# colour-blind viewers still see.
DESIGNED = {
  1: (0.64, 0.13, 240),   # cerulean
  2: (0.80, 0.15, 75),    # amber
  3: (0.77, 0.15, 155),   # jade
  4: (0.56, 0.19, 355),   # raspberry
  5: (0.58, 0.14, 285),   # violet
  6: (0.80, 0.11, 195),   # sea teal
  7: (0.62, 0.14, 45),    # terracotta
  8: (0.87, 0.13, 115),   # pistachio
  -1: (0.42, 0.10, 318),  # plum: dark, so a special-position part never reads as 1 or 2
  -2: (0.70, 0.11, 110),  # olive
  -3: (0.46, 0.09, 150),  # forest   } found by a grid search: the pair furthest
  -4: (0.82, 0.09, 330),  # orchid   } from all the others and from C, H, N, O
}
GOLDEN = 137.508
# Olex2's element colours that parts most often sit next to
NEIGHBOURS = {'C': '#909090', 'H': '#ffffff', 'N': '#3050f8', 'O': '#ff0d0d'}

# Tone-in-tone palettes: one colour family.  A pair is one hue, dark and light
# (lightness differs by 0.30, so the pair holds for colour-blind viewers too);
# the next pair moves to a neighbouring hue of the same family.  Negative parts
# are the family's greys.  (pair hues, negative hues, chroma)
TONES = {
  'blues':  ((245, 215, 270, 195), (230, 255), 0.12),
  'greens': ((150, 125, 170, 105), (140, 115), 0.12),
  'warm':   ((45, 70, 25, 85), (55, 35), 0.12),
  'berry':  ((350, 320, 10, 300), (340, 310), 0.12),
  'earth':  ((60, 140, 30, 100), (80, 120), 0.07),
}
PALETTES = ('contrast',) + tuple(TONES)
DESCRIPTIONS = {
  'contrast': 'every pair a different colour family; best for telling many parts apart',
  'blues': 'tone in tone: cerulean, sky, indigo, teal',
  'greens': 'tone in tone: jade, moss, mint, olive',
  'warm': 'tone in tone: terracotta, amber, coral, ochre',
  'berry': 'tone in tone: raspberry, plum, rose, violet',
  'earth': 'tone in tone, quiet: sand, sage, clay, olive; good for print',
}
_current = ['contrast']


def use(name):
  """Choose the palette by name; an unknown name falls back to contrast."""
  _current[0] = name if name in PALETTES else 'contrast'
  return _current[0]


def current():
  return _current[0]


def _contrast(part):
  if part in DESIGNED:
    return DESIGNED[part]
  n = abs(part)
  pair = (n - 1) // 2
  second = n % 2 == 0
  hue = (240 + pair * GOLDEN + (180 if second else 0)) % 360
  if part < 0:
    return (0.78 if second else 0.58, 0.07, (hue + 40) % 360)
  return (0.80 if second else 0.64, 0.13, hue)


def _tone(part, spec):
  hues, negatives, chroma = spec
  n = abs(part)
  pair = (n - 1) // 2
  second = n % 2 == 0
  family = negatives if part < 0 else hues
  hue = family[pair % len(family)] + 12 * (pair // len(family))  # later rounds drift
  if part < 0:
    # the family's greys, told apart by lightness: deep, pale, mid, darkest
    L, C = NEGATIVE_STEPS[(n - 1) % len(NEGATIVE_STEPS)]
    return (L, C, hue % 360)
  return (0.80 if second else 0.50, chroma, hue % 360)


# (lightness, chroma) of -1, -2, -3, -4 in a tone-in-tone palette; mid keeps some
# chroma so it does not read as carbon grey
NEGATIVE_STEPS = ((0.36, 0.06), (0.90, 0.04), (0.72, 0.09), (0.26, 0.05))


def lch(part, name=None):
  """(L, C, h) of a part in a palette (the current one by default)."""
  name = name or _current[0]
  if name in TONES:
    return _tone(part, TONES[name])
  return _contrast(part)


def _to_linear(c):
  return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _to_srgb(c):
  return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _oklch_to_linear(L, C, h):
  a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
  l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
  m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
  s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
  return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
          -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
          -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def oklch_to_rgb(L, C, h):
  """(r, g, b) 0-255; a colour a screen cannot show keeps L and h and loses chroma."""
  lo, hi = 0.0, C
  rgb = _oklch_to_linear(L, 0, h)
  for _ in range(30):
    mid = (lo + hi) / 2
    trial = _oklch_to_linear(L, mid, h)
    if all(-1e-6 <= x <= 1 + 1e-6 for x in trial):
      lo, rgb = mid, trial
    else:
      hi = mid
  if all(-1e-6 <= x <= 1 + 1e-6 for x in _oklch_to_linear(L, C, h)):
    rgb = _oklch_to_linear(L, C, h)
  return tuple(int(round(255 * _to_srgb(min(1.0, max(0.0, x))))) for x in rgb)


def rgb(part, name=None):
  return oklch_to_rgb(*lch(part, name))


def html(part, name=None):
  return '#%02x%02x%02x' % rgb(part, name)


def contrast(a, b):
  """WCAG contrast ratio of two (r, g, b)."""
  def lum(c):
    r, g, b = (_to_linear(x / 255.0) for x in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
  hi, lo = sorted((lum(a), lum(b)), reverse=True)
  return (hi + 0.05) / (lo + 0.05)


DARK_TEXT, LIGHT_TEXT = (27, 27, 27), (255, 255, 255)


def text_colour(part):
  """Dark or white, whichever has more contrast on the part's button."""
  c = rgb(part)
  dark = contrast(c, DARK_TEXT) >= contrast(c, LIGHT_TEXT)
  return '#%02x%02x%02x' % (DARK_TEXT if dark else LIGHT_TEXT)


def _packed(r, g, b, a=255):
  """Olex2 colours are decimal 0xAABBGGRR."""
  return (a << 24) | (b << 16) | (g << 8) | r


def material(part):
  """An Olex2 material: ambient 0.85x and diffuse 0.90x the colour, a grey
  highlight so it never tints the part, as in the modern 3D styles."""
  r, g, b = rgb(part)
  amb = _packed(*(int(round(x * 0.85)) for x in (r, g, b)))
  dif = _packed(*(int(round(x * 0.90)) for x in (r, g, b)))
  spec = _packed(77, 77, 77)
  return '85;%d;%d;%d;16' % (amb, dif, spec)


def collection(part):
  """The Olex2 collection the part's atoms are put in: _p1, _p2 ...; -1 is _pm1,
  so the name stays a plain word and still matches _p*."""
  return '_pm%d' % -part if part < 0 else '_p%d' % part


def control(part):
  """The part's button name in the panel."""
  return 'm%d' % -part if part < 0 else str(part)


def order(parts):
  """Positive parts first, then negative ones, each by size."""
  return sorted(parts, key=lambda p: (p < 0, abs(p)))


# --- checking ---------------------------------------------------------------

def _oklab(rgb_):
  r, g, b = (_to_linear(x / 255.0) for x in rgb_)
  l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3.)
  m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3.)
  s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3.)
  return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
          1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
          0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


# Machado et al. 2009, full severity, on linear RGB
CVD = {
  'protan': ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216),
             (-0.003882, -0.048116, 1.051998)),
  'deutan': ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413),
             (-0.011820, 0.042940, 0.968881)),
  'tritan': ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602),
             (0.004733, 0.691367, 0.303900)),
}


def simulate(rgb_, kind):
  lin = [_to_linear(x / 255.0) for x in rgb_]
  out = [sum(row[i] * lin[i] for i in range(3)) for row in CVD[kind]]
  return tuple(int(round(255 * _to_srgb(min(1.0, max(0.0, x))))) for x in out)


def distance(a, b, kind=None):
  """OKLab distance of two (r, g, b), optionally as seen with a colour deficiency."""
  if kind:
    a, b = simulate(a, kind), simulate(b, kind)
  return math.dist(_oklab(a), _oklab(b))


def _hex_rgb(h):
  return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
