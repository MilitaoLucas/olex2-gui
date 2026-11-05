"""Colours for the people-database windows (login form, Manage users and
sites), taken from the Help window's settings (gui.help.*) so they look the
same. form.py builds the pages with them.

wxWidgets draws the input boxes natively, so on a dark background they get
no visible border and may keep their own text colour. Two things help:
  - every input sits in a one-pixel table cell of the 'border' colour, a
    border drawn by the html instead of the control;
  - the boxes are a little lighter than the window, with 'input_fg' as text
    colour where the control accepts one.
"""

DEFAULTS = {'bg': '#222222', 'font': '#ffffff', 'title': '#ffffff',
            'highlight': '#ff8800', 'action': '#0080ff'}


def _hex(value):
  value = getattr(value, 'hexadecimal', value)
  value = str(value or '').strip().strip("'\"")
  if len(value) == 7 and value.startswith('#'):
    try:
      int(value[1:], 16)
      return value.lower()
    except ValueError:
      pass
  return None


def _rgb(colour):
  return [int(colour[i:i + 2], 16) for i in (1, 3, 5)]


def mix(colour, other, fraction):
  """colour moved 'fraction' (0..1) of the way towards other."""
  a, b = _rgb(colour), _rgb(other)
  return '#%02x%02x%02x' % tuple(int(round(x + (y - x) * fraction)) for x, y in zip(a, b))


def is_dark(colour):
  r, g, b = _rgb(colour)
  return 0.299 * r + 0.587 * g + 0.114 * b < 128


def palette(params=None):
  """All colours, from params {'bg': ..., 'font': ...}; missing or broken
  values fall back to the Help window's defaults."""
  p = dict(DEFAULTS)
  for key, value in (params or {}).items():
    value = _hex(value)
    if value:
      p[key] = value
  bg, font = p['bg'], p['font']
  towards = '#ffffff' if is_dark(bg) else '#000000'
  p.update({
    'panel': mix(bg, towards, 0.06),       # the boxes grouping the fields
    'group': mix(bg, towards, 0.14),       # their header rows
    'input_bg': mix(bg, towards, 0.12),
    'input_fg': font,
    'border': mix(bg, towards, 0.35),
    'muted': mix(font, bg, 0.35),          # hints under the fields
    'button_fg': '#ffffff',
  })
  return p


def _olex_params():
  from olexFunctions import OV
  params = {}
  for key, name in (('bg', 'gui.help.bg_colour'), ('font', 'gui.help.font_colour'),
                    ('title', 'gui.help.h1_colour'), ('highlight', 'gui.help.highlight_colour'),
                    ('action', 'gui.action_colour')):
    params[key] = OV.GetParam(name, None)
  return params


def current():
  """The palette for the current Olex2 settings."""
  return palette(_olex_params())
