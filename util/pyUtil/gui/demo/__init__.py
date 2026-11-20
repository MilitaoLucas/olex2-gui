"""Demo mode: every command typed in the console is shown large in Olex2's
info box (ShowWindow info), for presentations and screen recordings.

  spy.gui.demo.mode([on|off])   switch it (no argument: toggle)
  spy.gui.demo.show(text)       show any text the same way

Display: the info box (core TGlTextBox, library 'info_box': Clear, PostText,
Fit; its font is the scene font 'Notes').  While demo mode is on, 'Notes' is
demo.font (a system font; by default the platform's monospace font) at
demo.font_size points; switching off puts the old font back.  A command stays demo.seconds, then the box gets
the file information back that Olex2 normally shows there.

Which command was typed: Olex2 has no event for it, and its log carries every
command, also those the GUI and scheduled jobs issue.  But on Enter the
console hands its line to processMacro(cmd, "Console") and clears it only
afterwards, so in the 'onlog' callback a logged line equal to the input line
(console.Command()) is the typed command.  No polling (an earlier version
re-scheduled itself 'when idle' and froze Olex2).
Demo mode is not kept: Olex2 always starts with it off.

Keys (demo.keys, Olex2 builds from 2026-11-20): the 'onkey' callback shows
the command line while it is typed, 'onaccel' shows shortcuts (Ctrl+P ...).
Their argument's form was not known when this was written: key_label() reads
the likely ones; anything else is not shown (spy.gui.demo.probe_keys prints
the raw values; the last unreadable ones are in _state['unknown_keys']).
"""
import os
import sys

import olex
import olx
from olexFunctions import OV

from gui import toolphil

toolphil.load(__file__, 'demo')  # gui/demo/demo.phil (user.demo), values in DataDir/user.phil

# shown before typed commands and keys (demo.prefix)
PROMPT = ' '
FONT_SIZE = 24


def prefix():
  p = OV.GetParam('user.demo.prefix')
  return PROMPT if p is None else str(p)


def _font_size():
  try:
    return int(OV.GetParam('user.demo.font_size', FONT_SIZE) or FONT_SIZE)
  except (TypeError, ValueError) as err:
    _report("read font_size", err)
    return FONT_SIZE

_state = {'on': False, 'typed': '', 'serial': 0, 'shown': False, 'notes_font': None,
          'typing': '', 'accel_seen': False, 'keys': False}


def _report(what, err):
  print("Demo mode: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def _quoted(text):
  """text as one macro argument: quotes it, avoiding the quote it contains."""
  return ("'%s'" % text) if "'" not in text else ('"%s"' % text.replace('"', "'"))


# --- the info box ------------------------------------------------------------

def _post(lines):
  """Replace the info box's text.  info_box.* are FUNCTIONS (Oleg, via the
  user, 2026-11-12): info_box.Clear(), info_box.PostText(string); called as
  macros ('info_box.Clear') they silently do nothing."""
  box = getattr(olx, 'info_box', None)
  if box is not None:
    # straight from Python: the text is not parsed, so $, quotes, commas stay
    box.Clear()
    for line in lines:
      box.PostText(line)
  else:
    olex.f('info_box.Clear()')
    for line in lines:
      olex.f('info_box.PostText(%s)' % _quoted(line.replace('$', '\\$')))
  # no info_box.Fit(): it shrinks the shaded box to the text; left alone the
  # box spans the whole width of the 3D view, as Olex2 lays it out
  _redraw()


def _redraw():
  """Draw the info box with its new text, shown.  Posting does not redraw,
  nor does olx.Refresh() alone.  ShowWindow with ONE argument toggles and
  then draws (core macShowWindow): toggling twice redraws, but the frame
  with the box hidden flickers.  So both toggles happen with drawing frozen
  (olx.Freeze, builds from 2026-11-20), and only then is it unfrozen, with
  the box shown: unfreezing drew a frame when it came between the toggles
  (the flicker survived that order), and olx.Refresh() after it draws in
  case unfreezing does not.  demo.redraw=refresh: the Refresh macro only."""
  if str(OV.GetParam('user.demo.redraw', 'toggle')).lower() == 'refresh':
    olex.m('Refresh')
    return
  olex.m('ShowWindow info true')
  freeze = getattr(olx, 'Freeze', None)
  frozen = False
  try:
    if freeze is not None:
      try:
        freeze('true')
        frozen = True
      except Exception as err:
        _report("freeze the display", err)
    olex.m('ShowWindow info')
    olex.m('ShowWindow info')
  finally:
    if frozen:  # never leave the display frozen
      freeze('false')
  if frozen:
    try:
      olx.Refresh()
    except Exception as err:
      _report("refresh the display", err)


def _file_lines():
  """What Olex2 itself shows in the info box: the folder and the file."""
  try:
    if olx.IsFileLoaded() != 'true':
      return ['No file is loaded']
    full = OV.FileFull()
    return [os.path.dirname(full), os.path.basename(full)]
  except (AttributeError, RuntimeError) as err:
    _report("read the file name", err)
    return []


# a system font as wxWidgets describes it (as the theme package writes them):
# version;points;-pixels;0;0;0;weight;italic;0;0;0;3;2;1;34;face
_SYSTEM_FONT = '1;%d;%d;0;0;0;400;0;0;0;0;3;2;1;34;%s'
MONOSPACE = {'win': 'Consolas', 'darwin': 'Menlo'}  # anything else: Linux


def _font_face():
  """demo.font: a system font's face name; empty for the platform's
  monospace font; 'console' for the console's own (Olex2) font."""
  face = str(OV.GetParam('user.demo.font') or '').strip()
  if face in ('', 'None'):
    for key, name in MONOSPACE.items():
      if sys.platform.startswith(key):
        return name
    return 'DejaVu Sans Mono'
  return face


def _use_console_font(on):
  """The info box in demo.font at demo.font_size, or its own font again.
  olx.SetFont, not the SetFont macro: that splits face names with spaces."""
  try:
    if on:
      if _state['notes_font'] is None:  # not again on a restyle: keep Olex2's own
        _state['notes_font'] = olx.GetFont('Notes')
      size = _font_size()
      face = _font_face()
      if face.lower() == 'console':
        # the console's font scaled up (an Olex2 font such as frb_12 is bold)
        olex.m('SetFont Notes %s -ps=%i' % (_quoted(olx.GetFont('Default')), size))
      else:
        olx.SetFont('Notes', _SYSTEM_FONT % (size, -int(round(size * 96 / 72.0)), face))
    elif _state['notes_font']:
      olx.SetFont('Notes', _state['notes_font'])
      _state['notes_font'] = None
  except (AttributeError, RuntimeError) as err:
    _report("set the info box font", err)


# the info box's materials (set by gui.skin from gui.infobox_text/_plane);
# flags 2053: identity draw, ambient and diffuse, both the same colour
_MATERIALS = (('InfoBox.Text', 'text_colour', 'gui.infobox_text', 1.0),
              ('InfoBox.Plane', 'background_colour', 'gui.infobox_plane', None))


TRANSPARENT = 0x400  # sglmTransparent: without it Olex2 ignores the alpha


def _material(hex_colour, alpha=1.0):
  """'#rrggbb' -> Olex2 material '2053;c;c' (colours are 0xAABBGGRR); below
  full opacity with the transparency flag, '3077;c;c', as the styles have."""
  h = str(hex_colour).strip().lstrip('#')
  if len(h) == 3:
    h = ''.join(c * 2 for c in h)
  r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
  a = max(0, min(255, int(round(float(alpha) * 255))))
  c = (a << 24) | (b << 16) | (g << 8) | r
  return '%d;%d;%d' % (2053 | (TRANSPARENT if a < 255 else 0), c, c)


def _opacity():
  try:
    v = OV.GetParam('user.demo.background_opacity', 0)
    return max(0.0, min(1.0, float(0 if v is None else v)))
  except (TypeError, ValueError) as err:
    _report("read background_opacity", err)
    return 0.0


def _use_demo_colours(on):
  """The info box in demo.text_colour / demo.background_colour (with
  demo.background_opacity), or the skin's colours again.  An empty colour
  leaves the skin's; opacity 0 (the default) leaves no box at all, so that
  nothing large flickers while keys are shown."""
  for name, key, skin_param, alpha in _MATERIALS:
    try:
      colour = OV.GetParam('user.demo.%s' % key) if on else None
      own = colour and str(colour).strip() not in ('None', '')
      if on and alpha is None and _opacity() == 0:
        olx.SetMaterial(name, _material(colour if own else '#000000', 0))
      elif own:
        if alpha is None:
          alpha = _opacity()
        olx.SetMaterial(name, _material(colour, alpha))
      else:
        olx.SetMaterial(name, OV.GetParam(skin_param))
    except (AttributeError, RuntimeError, ValueError, IndexError) as err:
      _report("set the info box colour (%s = %s)" % (key, OV.GetParam('user.demo.%s' % key)), err)


def restyle():
  """spy.gui.demo.restyle(): the demo settings again (after editing them)."""
  if not _state['on']:
    return
  _use_console_font(True)
  _use_demo_colours(True)
  if _state['shown'] and _state.get('text'):
    _post([_full_width(_state['text'])])


# a space in the console font, as a part of its point size (an estimate:
# Olex2 cannot say how wide a text is)
SPACE_WIDTH = 0.35
# Olex2 sizes a line by its ink, so 'demo' and 'ppp' sit at different heights.
# A '|' reaches above the ascenders and below the descenders: at the end of
# the padding, past the right edge of the 3D view (OVERSHOOT), it gives every
# line the same height without being seen.  (A comma, 2026-11-12, did not:
# it is neither tall nor as deep as a 'p'.)
DESCENDER = '|'
OVERSHOOT = 1.3  # the padding reaches this many window widths


def _full_width(text):
  """text padded with spaces so that the shaded box reaches across the 3D
  view: the box is as wide as its text, and Fit() only shrinks it."""
  try:
    width = int(olx.GetWindowSize('gl').split(',')[2])
  except (AttributeError, RuntimeError, ValueError, IndexError) as err:
    _report("read the window width", err)
    return text
  size = _font_size() * 96 / 72.0  # points -> px
  spaces = int(OVERSHOOT * width / (SPACE_WIDTH * size)) - int(len(text) * 0.6)
  # DESCENDER at the far end, off screen: the same line height for every text
  return text + ' ' * max(0, spaces) + DESCENDER


def _indent():
  """Spaces for the console's text indent (gui.console_offset, pixels) at the
  demo font size, so the demo text starts where the console text does."""
  try:
    offset = float(OV.GetParam('gui.console_offset', 10) or 0)
    size = _font_size() * 96 / 72.0  # points -> px
    return ' ' * max(0, int(round(offset / (SPACE_WIDTH * size))))
  except (TypeError, ValueError) as err:
    _report("read the console indent", err)
    return ''


def show(text):
  """spy.gui.demo.show(text): text in the info box for demo.seconds; a
  newer text replaces it.  Leading spaces (in demo.prefix too) are kept, after
  the console's indent."""
  text = str(text).rstrip()
  if not text.strip():
    return
  text = _indent() + text
  # the text first, then the box shown and drawn once (_post): showing it
  # first drew the old, taller text, and the line jumped up a notch
  _post([_full_width(text)])
  _state['serial'] += 1
  _state['shown'] = True
  _state['text'] = text
  seconds = max(1, int(OV.GetParam('user.demo.seconds', 7) or 7))
  olx.Schedule(seconds, 'spy.gui.demo.hide(%i)' % _state['serial'])


def hide(serial=None):
  """Clear the info box; with serial, only if nothing newer came since."""
  if serial is not None and int(serial) != _state['serial']:
    return
  if _state['shown']:
    _post([])
    _state['shown'] = False


def after_load(*args):
  """A structure was loaded: Olex2 has written its own title and file path
  into the info box (in the demo font, not full width).  Put the demo text
  back, or clear the box.  Called from olx.FileChangeListeners and once more
  a second later, in case Olex2 posts again after the listeners ran."""
  if not _state['on']:
    return
  if args and args[0] != 'structure':
    return
  if _state['shown'] and _state.get('text'):
    _post([_full_width(_state['text'])])
  else:
    _post([])
  if args:  # from the listener: once more, after Olex2 is done loading
    olx.Schedule(1, 'spy.gui.demo.after_load()')


def _listen_to_loads():
  listeners = getattr(olx, 'FileChangeListeners', None)
  if listeners is None:
    olx.FileChangeListeners = [after_load]
  elif after_load not in listeners:
    listeners.append(after_load)


def on_exit():
  """Olex2 is closing: demo mode off, so that the info box and its font are
  Olex2's own again before Olex2 keeps them for the next start."""
  if _state['on']:
    mode('off')


# --- watching the console ----------------------------------------------------

def on_log(text):
  """The log callback.  On Enter the console hands its line to processMacro
  and clears it only afterwards (TMainForm::Dispatch, ID_COMMAND), so while a
  typed command is being logged it is still in the input line: a logged line
  equal to console.Command() is the command just typed.  No polling."""
  if not _state['on']:
    return
  try:
    typed = str(olex.f('console.Command()') or '').strip()
  except Exception as err:  # unknown in a running Olex2: stop and say why
    print("Demo mode: cannot read the console's input line (%s); switched off" % err)
    mode('off')
    return
  for line in str(text).splitlines():
    line = line.strip()
    _learn_shortcut(line)
    if typed and line == typed:
      _state['typing'] = ''
      _pending('%s%s' % (prefix(), typed))
      return
    if not typed and not _state['accel_seen']:  # real shortcut events beat the guess
      key = shortcuts().get(line)
      if key:  # nothing typed, a shortcut's macro ran: show the keys
        _pending('%s%s   %s' % (prefix(), key, line))
        return


def _pending(text):
  """Show text ('' clears the box) once Olex2 is idle, not here: the
  callbacks run while a key is on its way to the console, and drawing here
  (olx.Refresh lets waiting events run) let the next key overtake it, so
  'refine' was typed as 'erfin'.  One idle job at a time; keys that come
  before it runs only change the text it will show.  (A 1 s Schedule was
  too slow; Schedule without an interval runs when Olex2 is idle.)"""
  _state['pending'] = text
  if not _state.get('pending_scheduled'):
    _state['pending_scheduled'] = True
    try:
      olx.Schedule('spy.gui.demo.show_pending()')
    except Exception as err:
      _state['pending_scheduled'] = False
      _report("schedule the demo text", err)


# --- keyboard shortcuts ----------------------------------------------------

_shortcuts = {}


def shortcuts():
  """{macro: key} from settings.xld (<shortcut key="Ctrl+G" macro="mode grow">)
  and from CreateShortcut lines seen in the log (plugins add theirs at start)."""
  if not _shortcuts.get('_read'):
    import re
    try:
      with open(os.path.join(OV.BaseDir(), 'settings.xld'), encoding='utf-8', errors='replace') as f:
        for key, macro in re.findall(r'<shortcut\s+key="([^"]+)"\s+macro="([^"]*)"', f.read()):
          _shortcuts[macro.strip()] = key
    except OSError as err:
      _report("read the shortcuts in settings.xld", err)
    _shortcuts['_read'] = True
  return _shortcuts


def _scan_session_log():
  """Shortcuts plugins created at start, before demo mode listened: from the
  newest log file in DataDir/logs."""
  d = os.path.join(OV.DataDir(), 'logs')
  try:
    logs = sorted((os.path.join(d, f) for f in os.listdir(d) if f.endswith('.log')),
                  key=os.path.getmtime)
    if logs:
      with open(logs[-1], encoding='utf-8', errors='replace') as f:
        for line in f:
          _learn_shortcut(line.strip())
  except OSError as err:
    _report("read the session log", err)


def _learn_shortcut(line):
  """'CreateShortcut Ctrl+J 'spy.drawplus.follow_me'' in the log: remember it."""
  if line.lower().startswith('createshortcut '):
    parts = line.split(None, 2)
    if len(parts) == 3:
      shortcuts()[parts[2].strip().strip('\'"')] = parts[1]


# --- key events (Olex2 build of 2026-11-20: callbacks 'onkey' and 'onaccel') --
# Oleg's example registers one function for both and returns "".  What the
# argument holds was not seen yet, so key_label() reads the likely forms: a
# character, a name such as 'Ctrl+P', or wxWidgets key code and modifier
# flags as numbers.  Anything else is not shown: in brackets it appeared on
# Return and in input prompts.  probe_keys prints the raw values.

# wxWidgets key codes (wx/defs.h, 3.x) and modifier flags (wxMOD_*)
WXK_NAMES = {8: 'Backspace', 9: 'Tab', 13: 'Enter', 27: 'Esc', 32: 'Space', 127: 'Del',
             312: 'End', 313: 'Home', 314: 'Left', 315: 'Up', 316: 'Right', 317: 'Down',
             322: 'Insert', 366: 'PageUp', 367: 'PageDown', 370: 'Enter'}
# keys that change the console's input line (completion, history, cursor):
# the mirror shows the line again instead of the key's name
LINE_KEYS = ('Tab', 'Up', 'Down', 'Left', 'Right', 'Home', 'End', 'Del', 'Insert')
WXK_NAMES.update((340 + i, 'F%i' % (i + 1)) for i in range(24))
MODIFIERS = ((2, 'Ctrl'), (1, 'Alt'), (4, 'Shift'), (8, 'Win'))
MODIFIER_NAMES = ('ctrl', 'alt', 'shift', 'cmd', 'win', 'meta')


def key_label(arg):
  """(kind, text) for a key event's argument:
    ('char', 'a')       a character for the command line
    ('edit', 'Backspace'|'Enter'|'Esc')
    ('key', 'Ctrl+P')   a key press to show
    ('unknown', raw)    not readable: not shown
  """
  s = str(arg if arg is not None else '')
  if len(s) == 1 and s in CONTROL_CHARS:  # as a character event gives them
    return CONTROL_CHARS[s]
  if len(s) == 1 and 1 <= ord(s) <= 26:  # Ctrl+A .. Ctrl+Z as characters
    return 'key', 'Ctrl+%s' % chr(ord(s) + 64)
  if len(s) == 1 and s.isprintable():
    return 'char', s
  t = s.strip()
  if '+' in t and t.split('+')[0].strip().lower() in MODIFIER_NAMES:
    return 'key', '+'.join(p.strip() for p in t.split('+'))
  parts = [p for p in t.replace(',', ' ').replace(';', ' ').split() if p]
  if parts and all(p.lstrip('-').isdigit() for p in parts) and len(parts) <= 3:
    code = int(parts[0])
    flags = int(parts[1]) if len(parts) > 1 else 0
    mods = [name for bit, name in MODIFIERS if flags & bit]
    if code in (8, 13, 27, 370) and not mods:
      return 'edit', WXK_NAMES[code]
    if 32 <= code < 127 and not [m for m in mods if m != 'Shift']:
      c = chr(code)
      return 'char', c if 'Shift' in mods or not c.isalpha() else c.lower()
    name = WXK_NAMES.get(code) or (chr(code).upper() if 32 < code < 127 else str(code))
    return 'key', '+'.join(mods + [name])
  edit = EDIT_NAMES.get(t.lower())
  if edit:
    return 'edit', edit
  return 'unknown', t


CONTROL_CHARS = {'\b': ('edit', 'Backspace'), '\x7f': ('edit', 'Backspace'),
                 '\r': ('edit', 'Enter'), '\n': ('edit', 'Enter'),
                 '\x1b': ('edit', 'Esc'), '\t': ('key', 'Tab')}
EDIT_NAMES = {'backspace': 'Backspace', 'back': 'Backspace', 'enter': 'Enter',
              'return': 'Enter', 'esc': 'Esc', 'escape': 'Esc'}


def _unknown(kind, arg_str):
  """A key event key_label cannot read: not shown (it appeared as [..] on
  Return and in input prompts); the last few kept for a look."""
  seen = _state.setdefault('unknown_keys', [])
  seen.append((kind, arg_str))
  del seen[:-20]


LINE = object()  # _pending: show the console's input line as it is then


def on_key(arg_str):
  """The 'onkey' callback: the command line as it is typed.  The mirror
  shows the console's own input line once Olex2 is idle (show_pending), not
  a line put together from the keys: keys the console does not insert (PgUp
  came as ';') would pile up, and Tab completion would be missed."""
  if not _state['on']:
    return ""
  try:
    kind, text = key_label(arg_str)
    if kind == 'unknown':
      _unknown('onkey', arg_str)
      return ""
    line = _state['typing']  # kept only for when the input line cannot be read
    if kind == 'char':
      _state['typing'] = line + text
    elif kind == 'edit':
      if text == 'Backspace':
        _state['typing'] = line[:-1]
      else:  # Enter: on_log shows the whole command; Esc: dropped
        _state['typing'] = ''
        return ""
    elif text in LINE_KEYS:
      pass
    else:
      _pending('%s%s' % (prefix(), text))
      return ""
    _pending(LINE)
  except Exception as err:
    _report("show the key '%s'" % arg_str, err)
  return ""


def _input_line():
  """The console's input line; the line put together from the keys if Olex2
  cannot say."""
  try:
    return str(olex.f('console.Command()') or '')
  except Exception as err:
    _report("read the console's input line", err)
    return _state['typing']


def on_accel(arg_str):
  """The 'onaccel' callback: a keyboard shortcut was used.  From the first
  one on, on_log stops guessing shortcuts from the log."""
  if not _state['on']:
    return ""
  try:
    kind, text = key_label(arg_str)
    if kind == 'unknown':
      _unknown('onaccel', arg_str)
      return ""
    _state['accel_seen'] = True
    _pending('%s%s' % (prefix(), text))
  except Exception as err:
    _report("show the shortcut '%s'" % arg_str, err)
  return ""


def _listen_to_keys(on):
  for name, callback in (('onkey', on_key), ('onaccel', on_accel)):
    try:
      if on:
        OV.registerCallback(name, callback)
      else:
        OV.unregisterCallback(name, callback)
    except Exception as err:  # an Olex2 without these callbacks
      _report("%s the '%s' callback" % ('register' if on else 'unregister', name), err)

def _probe(kind):
  def callback(arg_str):
    print('%s: %r' % (kind, arg_str))
    return ""
  callback.__name__ = 'probe_%s' % kind
  return callback


_probes = {'onkey': _probe('onkey'), 'onaccel': _probe('onaccel')}


def probe_keys(state=''):
  """spy.gui.demo.probe_keys([on|off]): print what Olex2 passes to the
  'onkey' and 'onaccel' callbacks (no argument: toggle)."""
  state = str(state).lower()
  on = (not _state.get('probing')) if state in ('', 'toggle') else state in ('on', 'true', '1')
  if on == bool(_state.get('probing')):
    return
  for name, callback in _probes.items():
    if on:
      OV.registerCallback(name, callback)
    else:
      OV.unregisterCallback(name, callback)
  _state['probing'] = on
  print('Key probe %s' % ('on: press keys and shortcuts, then probe_keys off' if on else 'off'))


def show_pending():
  """spy.gui.demo.show_pending(): the idle job of _pending."""
  _state['pending_scheduled'] = False
  if 'pending' not in _state:
    return
  text = _state.pop('pending')
  if not _state['on']:
    return
  if text is LINE:
    # also when Backspace emptied the line: the bare prompt replaces the last
    # letter (with no prompt at all, the box is cleared)
    text = '%s%s' % (prefix(), _input_line())
  if text.strip():
    show(text)
  else:
    hide()


def mode(state=''):
  """spy.gui.demo.mode([on|off]): typed commands shown large in the info box."""
  state = str(state).lower()
  on = (not _state['on']) if state in ('', 'toggle') else state in ('on', 'true', '1')
  if on == _state['on']:
    return
  _state['on'] = on
  if on:
    _use_console_font(True)
    _use_demo_colours(True)
    _scan_session_log()
    OV.registerCallback('onlog', on_log)
    _state['typing'] = ''
    _state['accel_seen'] = False
    _state['keys'] = bool(OV.GetParam('user.demo.keys', True))
    if _state['keys']:
      _listen_to_keys(True)
    _listen_to_loads()
    show('Demo mode')
  else:
    OV.unregisterCallback('onlog', on_log)
    if _state['keys']:
      _listen_to_keys(False)
      _state['keys'] = False
    _state['serial'] += 1  # a hide still scheduled does nothing
    _post(_file_lines())
    _state['shown'] = False
    _use_console_font(False)
    _use_demo_colours(False)
    olex.m('ShowWindow info %s'
           % ('false' if str(OV.GetParam('user.show_info', 1)) in ('0', 'False') else 'true'))
  print("Demo mode %s" % ('on: typed commands are shown in the info box' if on else 'off'))


def set(name, value):
  """spy.gui.demo.set(name, value): change a setting of gui/demo/demo.phil
  (seconds, font_size, prefix) and keep it (saved with the user settings, DataDir/user.phil)."""
  toolphil.set('demo', name, value)


OV.registerFunction(mode, False, 'gui.demo')
OV.registerFunction(set, False, 'gui.demo')
OV.registerFunction(show, False, 'gui.demo')
OV.registerFunction(hide, False, 'gui.demo')
OV.registerFunction(show_pending, False, 'gui.demo')
OV.registerFunction(after_load, False, 'gui.demo')
OV.registerFunction(restyle, False, 'gui.demo')
OV.registerFunction(probe_keys, False, 'gui.demo')
