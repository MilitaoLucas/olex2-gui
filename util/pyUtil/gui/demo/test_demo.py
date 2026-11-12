"""gui.demo with Olex2 stubbed: only typed commands are shown in the info box,
newer ones replace older ones, the file information comes back after its time,
the info box font is the console's while on and its own again when off."""
import importlib.util
import os
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
import tempfile  # noqa: E402
TMP = tempfile.mkdtemp()


class World:
  """What the stubs record and answer."""

  def __init__(self):
    self.cmds, self.scheduled = [], []
    self.callbacks, self.params = {}, {}
    self.typed = ''
    self.fonts = {'Notes': '#olex2.fnt:frb_12', 'Default': '1;10;-13;0;0;0;400;0;0;0;0;3;2;1;34;Arial'}


W = World()


def _f(expr):
  """olex.f: the console's input line, or a function call, recorded with the macros."""
  if expr == 'console.Command()':
    return W.typed
  W.cmds.append(expr)
  return ''


def _install():
  class OV:
    @staticmethod
    def GetParam(k, d=None):
      return W.params.get(k, d)

    registerFunction = staticmethod(lambda *a: None)

    @staticmethod
    def registerCallback(event, fn):
      W.callbacks.setdefault(event, []).append(fn)

    @staticmethod
    def unregisterCallback(event, fn):
      W.callbacks.get(event, []).remove(fn)

    FileFull = staticmethod(lambda: 'C:/data/sucrose/sucrose.res')
    DataDir = staticmethod(lambda: TMP)  # no logs folder: nothing to scan
    BaseDir = staticmethod(lambda: TMP)  # no settings.xld

  sys.modules['olexFunctions'] = types.SimpleNamespace(OV=OV)
  # gui.toolphil: the tool's own phil (gui/demo/demo.phil); here just recorded
  toolphil = types.SimpleNamespace(
    load=lambda f, scope: W.cmds.append('load %s' % scope),
    set=lambda scope, name, value: (W.params.__setitem__('user.%s.%s' % (scope, name), value),
                                    W.cmds.append('save %s' % scope)))
  gui = types.ModuleType('gui')
  gui.toolphil = toolphil
  sys.modules['gui'] = gui
  sys.modules['gui.toolphil'] = toolphil
  # through lambdas: setUp gives W new lists
  sys.modules['olex'] = types.SimpleNamespace(
    m=lambda cmd: W.cmds.append(cmd), f=_f)
  sys.modules['olx'] = types.SimpleNamespace(
    Schedule=lambda *a: W.scheduled.append(a), GetFont=lambda name: W.fonts[name],
    IsFileLoaded=lambda: 'true', GetWindowSize=lambda which='': '0,0,1400,900',
    info_box=types.SimpleNamespace(Clear=lambda: W.cmds.append('Clear'),
                                   PostText=lambda t: W.cmds.append('Post:' + t),
                                   Fit=lambda: W.cmds.append('Fit')))


_install()
spec = importlib.util.spec_from_file_location('demo', os.path.join(HERE, '__init__.py'))
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class DemoTest(unittest.TestCase):
  def setUp(self):
    W.__init__()
    demo._state.update(on=False, typed='', serial=0, shown=False, notes_font=None)
    demo._state.pop('pending', None)

  def log(self, text):
    for fn in list(W.callbacks.get('onlog', [])):
      fn(text)

  def test_on_uses_the_console_font_and_off_restores_it(self):
    W.params['user.demo.font_size'] = 30
    demo.mode('on')
    self.assertIn("SetFont Notes '%s' -ps=30" % W.fonts['Default'], W.cmds)
    self.assertIn('Post:Demo mode', [c.rstrip(' ,') for c in W.cmds])
    del W.cmds[:]
    demo.mode('off')
    self.assertIn("SetFont Notes '#olex2.fnt:frb_12'", W.cmds)
    self.assertIn('Post:sucrose.res', W.cmds)  # the file is back
    self.assertEqual(W.callbacks['onlog'], [])

  def test_only_what_is_in_the_input_line_is_shown(self):
    demo.mode('on')
    del W.cmds[:], W.scheduled[:]
    W.typed = 'gro'  # half typed while the GUI and timers run their own commands
    self.log('spy.TimerPlus._track_mouse_activity()\nsel -u')
    self.assertEqual(W.scheduled, [])
    self.assertFalse([c for c in W.cmds if c.startswith('Post:')])
    W.typed = 'grow -w'  # Enter: the line is still there while it runs
    self.log('grow -w')  # shown at once, no waiting
    # functions, with brackets: as macros they do nothing; then a redraw, or
    # the text shows only after the next click
    # padded with spaces so the shading spans the whole width; no Fit
    posted = [c for c in W.cmds if c.startswith('Post:|>> grow -w')][-1]
    self.assertGreater(len(posted), 60)
    self.assertEqual(posted.rstrip(), 'Post:|>> grow -w')
    self.assertEqual(W.cmds[-2:], ['ShowWindow info', 'ShowWindow info'])
    self.assertNotIn('Fit', W.cmds)
    # cleared after 7 s (the default), once
    self.assertIn((7, 'spy.gui.demo.hide(%i)' % demo._state['serial']), W.scheduled)

  def test_nothing_is_scheduled_to_poll(self):
    demo.mode('on')
    self.assertFalse([s for s in W.scheduled if 'tick' in str(s)])

  def test_a_newer_command_wins_and_old_timers_do_nothing(self):
    demo.mode('on')
    first = demo._state['serial']
    demo.show('fuse')
    del W.cmds[:]
    demo.hide(first)
    self.assertEqual(W.cmds, [])  # 'fuse' stays
    demo.hide(demo._state['serial'])
    self.assertEqual(W.cmds[0], 'Clear')  # just cleared
    self.assertFalse([c for c in W.cmds if c.startswith('Post:')])

  def test_quotes_and_commas_in_a_command(self):
    demo.mode('on')
    demo.show("echo 'a b'")
    self.assertIn("Post:echo 'a b'", [c.rstrip(' ,') for c in W.cmds])
    demo.show('sel C1,C2 $C')  # raw string: commas and $ untouched
    self.assertIn('Post:sel C1,C2 $C', [c.rstrip(' ,') for c in W.cmds])

  def test_shortcuts_show_their_keys(self):
    demo._shortcuts.clear()
    demo._shortcuts.update({'_read': True, 'sel -u': 'Ctrl+U'})
    demo.mode('on')
    del W.scheduled[:]
    self.log("CreateShortcut Alt+L 'spy.gui.theme.legend_place()'")
    self.log('spy.gui.theme.legend_place()')  # nothing typed: a shortcut ran
    self.assertIn('Post:|Alt+L   spy.gui.theme.legend_place()', [c.rstrip(' ,') for c in W.cmds])
    W.typed = 'sel'  # while typing, a shortcut macro the GUI runs is not shown
    del W.scheduled[:]
    self.log('sel -u')
    self.assertEqual(W.scheduled, [])

  def test_settings_are_the_tools_own(self):
    demo.set('prefix', '> ')
    self.assertEqual(W.params['user.demo.prefix'], '> ')
    self.assertEqual(W.cmds[-1], 'save demo')
    demo.mode('on')
    W.typed = 'fuse'
    self.log('fuse')
    self.assertIn('Post:> fuse', [c.rstrip(' ,') for c in W.cmds])

  def test_an_unreadable_input_line_switches_it_off(self):
    demo.mode('on')
    real = sys.modules['olex'].f
    def f(expr):
      if expr == 'console.Command()':
        raise RuntimeError('no such function')
      return _f(expr)
    sys.modules['olex'].f = f
    try:
      self.log('fuse')
    finally:
      sys.modules['olex'].f = real
    self.assertFalse(demo._state['on'])


if __name__ == '__main__':
  unittest.main()
