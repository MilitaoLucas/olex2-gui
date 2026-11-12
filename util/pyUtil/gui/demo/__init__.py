"""Demo mode: every command typed in the console is shown large in Olex2's
info box (ShowWindow info), for presentations and screen recordings.

  spy.gui.demo.mode([on|off])   switch it (no argument: toggle)
  spy.gui.demo.show(text)       show any text the same way

Display: the info box (core TGlTextBox, library 'info_box': Clear, PostText,
Fit; its font is the scene font 'Notes').  While demo mode is on, 'Notes' is
the console's font ('Default') at demo.font_size points; switching off
puts the old font back.  A command stays demo.seconds, then the box gets
the file information back that Olex2 normally shows there.

Which command was typed: Olex2 has no event for it, and its log carries every
command, also those the GUI and scheduled jobs issue.  But on Enter the
console hands its line to processMacro(cmd, "Console") and clears it only
afterwards, so in the 'onlog' callback a logged line equal to the input line
(console.Command()) is the typed command.  No polling (an earlier version
re-scheduled itself 'when idle' and froze Olex2).
Demo mode is not kept: Olex2 always starts with it off.
"""
import os
import sys

import olex
import olx
from olexFunctions import OV

from gui import toolphil

toolphil.load(__file__, 'demo')  # gui/demo/demo.phil (user.demo), values in DataDir/user.phil

# shown before typed commands (demo.prefix): the console's '>>' and a
# pipe, which reaches below the baseline, so every line's box has the same depth
PROMPT = '|>> '


def prefix():
  p = OV.GetParam('user.demo.prefix')
  return PROMPT if p is None else str(p)

_state = {'on': False, 'typed': '', 'serial': 0, 'shown': False, 'notes_font': None}


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
  # posting does not redraw, nor does olx.Refresh(): ShowWindow with ONE
  # argument toggles and then draws (core macShowWindow), so toggle twice
  olex.m('ShowWindow info')
  olex.m('ShowWindow info')


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


def _use_console_font(on):
  """The info box in the console's font at demo.font_size, or its own again."""
  try:
    if on:
      _state['notes_font'] = olx.GetFont('Notes')
      size = int(OV.GetParam('user.demo.font_size', 34) or 34)
      olex.m('SetFont Notes %s -ps=%i' % (_quoted(olx.GetFont('Default')), size))
    elif _state['notes_font']:
      olex.m('SetFont Notes %s' % _quoted(_state['notes_font']))
      _state['notes_font'] = None
  except (AttributeError, RuntimeError) as err:
    _report("set the info box font", err)


# a space in the console font, as a part of its point size (an estimate:
# Olex2 cannot say how wide a text is)
SPACE_WIDTH = 0.35
DESCENDER = ''  # a trailing comma did not help (2026-11-12)


def _full_width(text):
  """text padded with spaces so that the shaded box reaches across the 3D
  view: the box is as wide as its text, and Fit() only shrinks it."""
  try:
    width = int(olx.GetWindowSize('gl').split(',')[2])
  except (AttributeError, RuntimeError, ValueError, IndexError) as err:
    _report("read the window width", err)
    return text
  size = int(OV.GetParam('user.demo.font_size', 34) or 34) * 96 / 72.0  # points -> px
  spaces = int(width / (SPACE_WIDTH * size)) - int(len(text) * 0.6)
  # the box is as tall as the ink: a comma at the far end (past the window's
  # edge, or small at it) gives every line the same depth below the baseline
  return text + ' ' * max(0, spaces) + DESCENDER


def show(text):
  """spy.gui.demo.show(text): text in the info box for demo.seconds; a
  newer text replaces it."""
  text = str(text).strip()
  if not text:
    return
  olex.m('ShowWindow info true')
  _post([_full_width(text)])
  _state['serial'] += 1
  _state['shown'] = True
  seconds = max(1, int(OV.GetParam('user.demo.seconds', 7) or 7))
  olx.Schedule(seconds, 'spy.gui.demo.hide(%i)' % _state['serial'])


def hide(serial=None):
  """Clear the info box; with serial, only if nothing newer came since."""
  if serial is not None and int(serial) != _state['serial']:
    return
  if _state['shown']:
    _post([])
    _state['shown'] = False


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
      _pending('%s%s' % (prefix(), typed))
      return
    if not typed:
      key = shortcuts().get(line)
      if key:  # nothing typed, a shortcut's macro ran: show the keys
        _pending('|%s   %s' % (key, line))
        return


def _pending(text):
  # shown at once: a 1 s Schedule here made a long delay after Return
  show(text)


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


def show_pending():
  text = _state.pop('pending', '')
  if text and _state['on']:
    show(text)


def mode(state=''):
  """spy.gui.demo.mode([on|off]): typed commands shown large in the info box."""
  state = str(state).lower()
  on = (not _state['on']) if state in ('', 'toggle') else state in ('on', 'true', '1')
  if on == _state['on']:
    return
  _state['on'] = on
  if on:
    _use_console_font(True)
    _scan_session_log()
    OV.registerCallback('onlog', on_log)
    show('Demo mode')
  else:
    OV.unregisterCallback('onlog', on_log)
    _state['serial'] += 1  # a hide still scheduled does nothing
    _post(_file_lines())
    _state['shown'] = False
    _use_console_font(False)
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
