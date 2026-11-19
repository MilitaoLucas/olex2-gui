"""Text colours of the 3D view: the kinds of console output and the labels.

The colours are gui parameters (gui.params: gui.console_colours.*,
gui.label_colours.*), so a skin can set them and the designer's choices are
kept in the theme overlay.  None leaves Olex2's own colour (console) or the
colour of the 3D style (labels).

Olex2 knows them as materials, set with SetMaterial:
  Console.Text            typed commands and ordinary output
  execout                 output of programs Olex2 runs (SHELXL ...)
  error, exception        error lines, program faults
  helptxt, helpcmd        help text, command names in the help
  Labels.Text             labels of all atoms, cell, axes (in the style)
  PLabels.Text            single atom labels (in the style)
Info and warning lines are orange and fixed in the core (mainform.cpp):
SetMaterial has no name for them.

apply() runs from gui.skin.SetMaterials after a skin load, and from the
designer after every change.  Loading a 3D style brings the style's label
colours back; apply() again lays these over it.
"""
import sys

# (param under gui., material name, material flags, Olex2's own material or None)
SLOTS = (
  ('console_colours.text', 'Console.Text', 2053, None),  # None: gui.infobox_text
  # own colours with flags 2053 like Console.Text: with flags 1 the text is
  # lit by the 3D lights and white comes out dark grey
  ('console_colours.output', 'execout', 2053, '1;65535'),
  ('console_colours.error', 'error', 2053, '1;32767'),
  ('console_colours.exception', 'exception', 2053, '1;255'),
  ('console_colours.help', 'helptxt', 2053, '1;16776960'),
  ('console_colours.help_command', 'helpcmd', 2053, '1;65535'),
  # labels: emissive (IdentityDraw + ambient + emission, 2305).  The styles'
  # own 2049 is ambient only, so the scene's ambient light scales the colour
  # and white comes out dark grey; emission shows the colour as chosen
  ('label_colours.all', 'Labels.Text', 2305, None),  # None: the style's
  ('label_colours.atoms', 'PLabels.Text', 2305, None),
  # the atom legend's text (collection AtomLegend) follows the atom labels
  ('label_colours.atoms', 'AtomLegend.Text', 2305, None),
)
# material flags (Olex2 TGlMaterial)
AMBIENT_F, EMISSION_F = 0x1, 0x100
# full materials chosen in Olex2's material dialog, by param: theme overlay
# section; they win over the plain colour of the same param
MATERIALS = 'text_materials'
# the same slots for a light 3D background (gui.console_colours_light.*,
# gui.label_colours_light.*); unset, the plain value is used on light too
LIGHT = dict((s[0], s[0].replace('_colours.', '_colours_light.', 1)) for s in SLOTS)
PARAMS = tuple(sorted(set(s[0] for s in SLOTS))) + tuple(sorted(set(LIGHT.values())))


def to_hex(value):
  """'#rrggbb' from a colour parameter (object with .hexadecimal or text), or None."""
  if value is None:
    return None
  v = getattr(value, 'hexadecimal', value)
  v = str(v).strip().strip("'\"").lower()
  if v in ('', 'none'):
    return None
  if not v.startswith('#'):
    v = '#' + v
  if len(v) != 7:
    return None
  try:
    int(v[1:], 16)
  except ValueError:
    return None
  return v


def material(hex_colour, flags):
  """An Olex2 material string with this colour: colours are 0xAABBGGRR."""
  r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
  c = (255 << 24) | (b << 16) | (g << 8) | r
  # one value per colour flag set, in bit order; with emission the colour is
  # the emission and the ambient is black, so the lights add nothing
  black = 255 << 24
  values = []
  for bit in range(10):
    if flags & (1 << bit):
      emissive_ambient = (1 << bit) == AMBIENT_F and flags & EMISSION_F
      values.append(black if emissive_ambient else c)
  return ';'.join([str(flags)] + [str(v) for v in values])


def colour_of_material(m):
  """'#rrggbb' a material string shows: its emission if it has one, else its
  first (ambient) colour; None if it cannot be read."""
  try:
    parts = str(m).split(';')
    flags = int(parts[0])
    bits = [b for b in range(10) if flags & (1 << b)]
    if not bits:
      return None
    pick = bits.index(8) if flags & EMISSION_F else 0
    v = int(parts[1 + pick]) & 0xFFFFFF
  except (ValueError, IndexError):
    return None
  r, g, b = v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF
  return '#%02x%02x%02x' % (r, g, b)


def slot_of(param):
  """(material name, flags, own) of the first slot of a param or its light
  variant, None if unknown."""
  base = dict((v, k) for k, v in LIGHT.items()).get(param, param)
  for p, name, flags, own in SLOTS:
    if p == base:
      return name, flags, own
  return None


def stored_material(param):
  from . import overlay
  return overlay.section(MATERIALS).get(param) or None


def set_material(param, m):
  """Keep a full material for this param (None forgets it)."""
  from . import overlay
  s = overlay.section(MATERIALS)
  if m:
    s[param] = str(m)
  else:
    s.pop(param, None)
  overlay.set_section(MATERIALS, s)


def material_of(param, flags):
  """The material string a param stands for: a stored full material, else
  its colour; None if neither is set."""
  m = stored_material(param)
  if m:
    return m
  c = colour_of(param)
  return material(c, flags) if c else None


def colour_of(param):
  from olexFunctions import OV
  return to_hex(OV.GetParam('gui.%s' % param))


def _luminance(hex_colour):
  r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
  return 0.299 * r + 0.587 * g + 0.114 * b


def gradient_shown():
  """Whether Olex2 shows the gradient now (state gradbg, toggled by F4)."""
  import olx
  return str(olx.CheckState('gradbg')).lower() == 'true'


def background_is_light():
  """Whether the 3D background is light, from what is shown now: the gradient's
  corners when the gradient is on (F4), else the plain colour (F2 swaps it)."""
  from . import background
  if gradient_shown():
    corners = [to_hex(c) for c in (background.settings().get('gradient') or [])]
    corners = [c for c in corners if c]
    if corners:
      return sum(_luminance(c) for c in corners) / len(corners) >= 128
  c = background.current_colour()
  return bool(c) and _luminance(c) >= 128


def text_colours_update():
  """spy.gui.theme.text_colours_update(): set the console and label colours for
  the background shown now; F2 and F4 call it after switching."""
  apply(restore=True)


def effective(param, light=None):
  """The colour a slot shows now: its light variant on a light background,
  when one is set."""
  if light is None:
    light = background_is_light()
  if light:
    c = colour_of(LIGHT[param])
    if c:
      return c
  return colour_of(param)


def text_colours_probe():
  """spy.gui.theme.text_colours_probe(): print how the background brightness is
  decided and which colour each slot gets (read-only)."""
  import olx
  from . import background
  s = background.settings()
  print("recorded background: %s" % s)
  try:
    print("ClearColor: %s -> %s" % (olx.gl.lm.ClearColor(), background.current_colour()))
  except Exception as err:
    print("ClearColor not readable: %s" % err)
  try:
    print("gradient shown (gradbg): %s" % gradient_shown())
  except Exception as err:
    print("gradbg not readable: %s" % err)
  light = background_is_light()
  print("background counted as: %s" % ('light' if light else 'dark'))
  for param, name, flags, own in SLOTS:
    print("  %-28s dark=%-8s light=%-8s -> %s" % (
      name, colour_of(param), colour_of(LIGHT[param]), effective(param, light)))


def apply(restore=False):
  """Set the materials of all slots that have a colour.  With restore, the
  console slots without one go back to Olex2's own colours."""
  import olx
  from olexFunctions import OV
  try:
    light = background_is_light()
  except Exception as err:
    print("Theme: could not tell the background brightness: %s" % err)
    if hasattr(sys, '_wing_debugger'):
      raise
    light = False
  for param, name, flags, own in SLOTS:
    m = (light and material_of(LIGHT[param], flags)) or material_of(param, flags)
    try:
      if m:
        olx.SetMaterial(name, m)
      elif restore and param.startswith('console_colours.'):
        olx.SetMaterial(name, own or OV.GetParam('gui.infobox_text'))
    except Exception as err:
      print("Theme: could not set the colour of %s: %s" % (name, err))
      if hasattr(sys, '_wing_debugger'):
        raise
