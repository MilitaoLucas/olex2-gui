"""Enlarge the whole GUI by one factor: gui.skin.scale (theme value 'skin.scale').

High-resolution monitors make the classic panel a slim bar: a wider panel
(`panel N`) only widens the images, their heights, the text in them and the
controls stay.  A scale of 1.5 multiplies every size value of the loaded skin
(and its extension and the designer's overlay): panel width, image heights,
fonts and offsets, control heights, the HTML font sizes (in wxHTML steps).
The images are still drawn from scratch, so nothing is resampled.

Fixed steps only (STEPS).  The scale is kept in the overlay (overlay.py), so a
saved theme carries it and the other overlay values stay at 100 %: the
designer always works on unscaled values.

deal_with_gui_phil (gui/skin) calls with_scaled(): the scaled values are one
more phil text after the overlay.  Working them out needs the merged values,
so the first load of a combination is done twice; the text is remembered per
combination, so the per-plugin reloads at start-up cost nothing extra and
phil_handler.reset_scope_and_update keeps its own shortcut.

Kept free of other theme imports: it is read while Olex2 is starting.
"""
import fnmatch
import math
import re
import sys

STEPS = (1.0, 1.25, 1.5, 1.75, 2.0)

# gui parameters multiplied by the scale (fnmatch patterns on the full name)
SIZE_PATTERNS = (
  'gui.htmlpanelwidth',
  # not gui.htmlpanelwidth_margin_adjust: the page margins, border and
  # scrollbar it allows for do not grow (scaled, the sNum title fell short)
  'gui.skin.icon_size',
  'gui.html.icon_size',
  'gui.html.input_height',
  'gui.html.checkbox_height',
  'gui.html.checkbox_width',
  'gui.html.checkbox_width_2',
  'gui.html.combo_width_2',
  'gui.html.combo_height',
  'gui.html.spin_height',
  'gui.html.table_firstcol_width',
  'gui.battery_width',
  'gui.timage.font_size',
  'gui.timage.*.height',
  'gui.timage.*.width',
  'gui.timage.*.font_size',
  'gui.timage.*.top',
  'gui.timage.*.left',
  'gui.timage.*.corner_rad',
  'gui.timage.*.gap',
  'gui.timage.*.vline',
  'gui.timage.*.dot_size',
  'gui.timage.*.dot_pad',
  'gui.timage.*.dot_left',
  'gui.timage.*.info_circle',
  'gui.timage.*.width_adjust',
  'gui.timage.*.filefullinfo_size',
  'gui.timage.*.type_band_height',
  'gui.timage.*.type_band_period',
  'gui.css.*.font_size',
  'gui.css.*.line_height',
  'gui.buttons.*.width',
)

# image decorations with a size in pixels: "bar:top:4", "buttonmark:11"
ARROW_PATTERN = 'gui.timage.*.arrows'
_ARROW_SIZE = re.compile(r'(bar:\w+:|buttonmark:)(\d+)')

# wxHTML <font size=N>: steps, not pixels.  A step is roughly 1.2 times, so
# 1.25 -> +1, 1.5 -> +2, 1.75 -> +3, 2.0 -> +4.  A first guess: judge in Olex2.
HTML_FONT_SIZES = (
  'gui.html.font_size',
  'gui.html.font_size_controls',
  'gui.html.font_size_large',
  'gui.html.font_size_extra_large',
  'gui.html.font_size_medium',
  'gui.html.formula_size',
)

# console text (system font '1;pt;-px;...;Face' or Olex2 font '#olex2.fnt:frb_12');
# not the 3D labels, which are part of the picture
FONTS = ('gui.console_font',)
# Olex2's own fonts (etc/Fonts/olex2.fnt) come in these sizes only
OLEX2_FONT_SIZES = (8, 28)

# the centred text in the panel images sat low after rounding at some steps
# (gui.timage.text_nudge, screen pixels up; 1.25x seen 2026-11-25); a value
# a skin or theme sets itself is left alone
TEXT_NUDGE = {1.25: 1}

# panel widths at which the HTML text gets one step larger or smaller
# (gui/skin export_parameters): moved with the panel, so the steps above are
# not added twice
STEP_WIDTHS = 'gui.font_size_steps'

_memo = {}


def _report(what, err):
  print("Theme scale: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def snap(value):
  """The nearest of STEPS; 1.0 for anything that is not a number."""
  try:
    value = float(value)
  except (TypeError, ValueError):
    return 1.0
  return min(STEPS, key=lambda s: abs(s - value))


def html_steps(factor):
  return int(round(math.log(factor) / math.log(1.2)))


def suggested(ppi):
  """The step closest to the screen's pixels per inch over 96."""
  try:
    return snap(float(ppi) / 96.0)
  except (TypeError, ValueError, ZeroDivisionError):
    return 1.0


def _is_size(name):
  return any(fnmatch.fnmatchcase(name, p) for p in SIZE_PATTERNS)


def _times(value, factor):
  if isinstance(value, bool):
    return None
  if isinstance(value, int):
    return int(round(value * factor))
  if isinstance(value, float):
    return round(value * factor, 3)
  return None


def scale_font(font, factor):
  """A console font description at factor times its size; None if it has no
  size that can be read."""
  if not isinstance(font, str):
    return None
  parts = font.split(';')
  if len(parts) >= 16 and parts[0] == '1':  # wx native font description
    try:
      pt = max(1, int(round(int(parts[1]) * factor)))
    except ValueError:
      return None
    parts[1] = str(pt)
    parts[2] = str(-int(round(pt * 96 / 72.0)))
    return ';'.join(parts)
  m = re.search(r'_(\d+)$', font)
  if m:
    lo, hi = OLEX2_FONT_SIZES
    pt = min(hi, max(lo, int(round(int(m.group(1)) * factor))))
    return font[:m.start()] + '_%i' % pt
  return None


def scaled_values(pairs, factor):
  """{name without 'gui.': value} for the (name, value) pairs of the gui scope
  that change at this scale."""
  out = {}
  if factor == 1.0:
    return out
  steps = html_steps(factor)
  for name, value in pairs:
    if value is None:
      continue
    new = None
    if name in HTML_FONT_SIZES:
      if isinstance(value, int) and not isinstance(value, bool):
        new = value + steps
    elif name == STEP_WIDTHS:
      try:
        new = [str(int(round(int(w) * factor))) for w in value]
      except (TypeError, ValueError):
        new = None
    elif name in FONTS:
      new = scale_font(value, factor)
    elif fnmatch.fnmatchcase(name, ARROW_PATTERN):
      if isinstance(value, str):
        new = _ARROW_SIZE.sub(
          lambda m: '%s%d' % (m.group(1), int(round(int(m.group(2)) * factor))), value)
        if new == value:
          new = None
    elif _is_size(name):
      new = _times(value, factor)
    if new is not None and new != value:
      out[name[len('gui.'):]] = new
  nudge = TEXT_NUDGE.get(factor)
  if nudge and not dict(pairs).get('gui.timage.text_nudge'):
    out['timage.text_nudge'] = nudge
  return out


def factor_for(skin_name):
  """The scale of this screen, snapped to STEPS: user.theme.scale (per user,
  not part of a theme).  A scale the theme overlay kept before that
  (skin.scale, 2026-11-25) still counts while the user setting is 1.0."""
  from olexFunctions import OV
  try:
    own = snap(OV.GetParam('user.theme.scale', 1.0))
  except Exception as err:  # user scope not read yet at a very early load
    _report("read user.theme.scale", err)
    own = 1.0
  if own != 1.0:
    return own
  from gui.theme import overlay
  return snap(overlay.value_for(skin_name, 'skin.scale', 1.0))


def current():
  """The scale in use now, for windows that size themselves (popups)."""
  from olexFunctions import OV
  return factor_for(OV.GetParam('gui.skin.name', 'default'))


def set_factor(factor):
  """Keep the scale for this user (saved with the user settings) and drop an
  old one from the theme overlay.  The skin must be loaded again to show it."""
  from olexFunctions import OV
  from gui.theme import overlay
  factor = snap(factor)
  OV.SetParam('user.theme.scale', factor)
  if 'skin.scale' in overlay.values():
    overlay.remove('skin.scale')
  try:
    import olex
    olex.m('spy.SaveUserParams()')
  except Exception as err:
    _report("save the user settings", err)
  return factor


def with_scaled(handler, skin_name, phil_strings):
  """phil_strings plus the scaled values as one more phil text (unchanged at 1.0)."""
  factor = factor_for(skin_name)
  if factor == 1.0:
    return phil_strings
  key = (factor, tuple(phil_strings))
  text = _memo.get(key)
  if text is None:
    from gui.theme import overlay
    try:
      handler.reset_scope_and_update('gui', phil_strings)
      text = overlay.phil_text(scaled_values(handler.name_value_pairs('gui'), factor))
    except Exception as err:
      _report("scale the GUI by %s" % factor, err)
      return phil_strings
    if len(_memo) > 8:
      _memo.clear()
    _memo[key] = text
  return list(phil_strings) + [text]


def scale_probe():
  """spy.gui.theme.scale_probe(): read-only; what the scale is and whether the
  header images in the VFS were drawn at it.  Prints, changes nothing."""
  import io
  import olx
  import OlexVFS
  from olexFunctions import OV
  from gui.theme import overlay
  skin = OV.GetParam('gui.skin.name', 'default') or 'default'
  lines = ["skin %s_%s, overlay skin %s, overlay skin.scale %s -> factor %s" % (
             skin, OV.GetParam('gui.skin.extension', ''), overlay._load().get('skin'),
             overlay.values().get('skin.scale'), factor_for(skin)),
           "gui.skin.scale %s, htmlpanelwidth %s, margin %s" % (
             OV.GetParam('gui.skin.scale'), OV.GetParam('gui.htmlpanelwidth'),
             OV.GetParam('gui.htmlpanelwidth_margin_adjust')),
           "heights: tab %s, h3 %s, cbtn %s, snumtitle %s, hos %s" % tuple(
             OV.GetParam('gui.timage.%s.height' % t) for t in ('tab', 'h3', 'cbtn', 'snumtitle', 'hos')),
           "html.font_size %s, console_font %s" % (
             OV.GetParam('gui.html.font_size'), OV.GetParam('gui.console_font'))]
  try:
    import ImageTools
    lines.append("ClientWidth %s, IT.skin_width %s" % (olx.html.ClientWidth('self'),
                                                       ImageTools.IT.skin_width))
  except Exception as err:
    lines.append("widths: %s" % err)
  try:
    from gui import skin as gskin
    from gui.tools import _timage_key
    import ImageTools
    now = _timage_key('global.odb', '%s %s' % (ImageTools.IT.skin_width, ImageTools.IT.skin_width_table)) or ''
    stored = OlexVFS.read_from_olex('gui_image_key.txt') or b''
    lines.append("image key: stored==now %s, startup==now %s, stored==startup %s" % (
      stored == now.encode(), (gskin.gui_image_key or '') == now,
      stored == (gskin.gui_image_key or '').encode()))
  except Exception as err:
    lines.append("image key: %s" % err)
  from PIL import Image
  for name in ('tab-home.png', 'tab-work.png', 'tab-view.png', 'sNumTitle.png'):
    try:
      if olx.fs.Exists(name) != 'true':
        continue
      im = Image.open(io.BytesIO(OlexVFS.read_from_olex(name)))
      lines.append("%s: %s x %s" % (name, im.size[0], im.size[1]))
    except Exception as err:
      lines.append("%s: %s" % (name, err))
  print('\n'.join(lines))


def click_probe(name='refine'):
  """spy.gui.theme.click_probe([solve|refine|draw|report]): how long opening
  and closing that settings panel takes, and the page functions that run on
  the way.  Opens and closes the panel once each; prints, changes nothing else."""
  import time
  import olx
  from olexFunctions import OV
  name = name.lower()
  lines = []

  def timed(label, f, n=1):
    t = time.perf_counter()
    try:
      for _ in range(n):
        f()
    except Exception as err:  # a probe: report and go on
      lines.append("%-34s failed: %s" % (label, err))
      return
    lines.append("%-34s %7.1f ms" % (label, (time.perf_counter() - t) * 1000.0 / n))

  try:
    was_open = OV.GetItemState('%s-settings' % name)
  except RuntimeError:  # not on the page shown (another tab)
    print("Open the Work tab first: '%s-settings' is not on the page shown" % name)
    return
  timed('open  %s settings' % name, lambda: (
    OV.SetItemState('cbtn* 1 cbtn-%s 2 *settings 0 %s-settings 1' % (name, name)), olx.Refresh()))
  timed('close %s settings' % name, lambda: (
    OV.SetItemState('cbtn* 1 cbtn-%s 1 *settings 0' % name), olx.Refresh()))
  import gui.tools as gt
  for fname in ('weightGuiDisplay', 'make_exti_swat_gui', 'refine_extinction', 'GetRInfo',
                'GetDPRInfo', 'make_cell_dimensions_display', 'makeFormulaForsNumInfo'):
    f = getattr(gt, fname, None)
    if f:
      timed(fname, f, 3)
  timed('html.Update (whole panel)', lambda: olx.html.Update())
  if str(was_open) in ('1', 'true', 'True'):
    OV.SetItemState('cbtn* 1 cbtn-%s 2 *settings 0 %s-settings 1' % (name, name))
  print('\n'.join(lines))


def page_profile(name='refine', rows=30):
  """spy.gui.theme.page_profile([refine|solve|draw|report]): one redraw of the
  panel with that settings section open, under the Python profiler.  Prints
  the total, the Python share and the slowest functions; opens the section,
  puts the previous state back afterwards."""
  import cProfile
  import io
  import pstats
  import time
  import olx
  from olexFunctions import OV
  name = name.lower()
  try:
    was_open = str(OV.GetItemState('%s-settings' % name)) in ('1', 'true', 'True')
  except RuntimeError:  # not on the page shown (another tab): open Work first
    print("Open the Work tab first: '%s-settings' is not on the page shown" % name)
    return
  OV.SetItemState('cbtn* 1 cbtn-%s 2 *settings 0 %s-settings 1' % (name, name))
  prof = cProfile.Profile()
  t = time.perf_counter()
  prof.enable()
  try:
    olx.html.Update()
  finally:
    prof.disable()
  total = (time.perf_counter() - t) * 1000.0
  if not was_open:
    OV.SetItemState('cbtn* 1 cbtn-%s 1 *settings 0' % name)
  st = pstats.Stats(prof, stream=io.StringIO())
  python_ms = sum(v[2] for v in st.stats.values()) * 1000.0  # own time of every function
  print("html.Update with %s settings open: %.0f ms, of which Python %.0f ms" % (name, total, python_ms))
  out = io.StringIO()
  st.stream = out
  st.sort_stats('cumulative').print_stats(int(rows))
  st.sort_stats('tottime').print_stats(15)
  # keep only the table lines, with short paths
  for line in out.getvalue().splitlines():
    line = line.replace(chr(92), '/')
    if 'pyUtil/' in line:
      line = line.split('pyUtil/')[0][:46] + line.split('pyUtil/', 1)[1]
    if line.strip():
      print(line)
