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
    self.hold_idle = False
    self.fonts = {'Notes': '#olex2.fnt:frb_12', 'Default': '1;10;-13;0;0;0;400;0;0;0;0;3;2;1;34;Arial'}


W = World()


def _f(expr):
  """olex.f: the console's input line, or a function call, recorded with the macros."""
  if expr == 'console.Command()':
    return W.typed
  W.cmds.append(expr)
  return ''


def _schedule(*args):
  """olx.Schedule: recorded; a job without an interval ('when idle') runs at
  once, as Olex2 runs it as soon as the key or command is done, unless
  W.hold_idle (to see what a callback does by itself)."""
  W.scheduled.append(args)
  if len(args) == 1 and args[0] == 'spy.gui.demo.show_pending()' and not W.hold_idle:
    demo.show_pending()


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
    Schedule=_schedule, GetFont=lambda name: W.fonts[name],
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
    demo._state['pending_scheduled'] = False
    W.params['gui.console_offset'] = 0  # no indent: posted text as given; see test_indent

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

  def test_a_load_puts_the_demo_text_back(self):
    olx = sys.modules['olx']
    olx.FileChangeListeners = []
    demo.mode('on')
    demo.mode('on')  # no second listener
    self.assertEqual(olx.FileChangeListeners, [demo.after_load])
    demo.show('reap sucrose.res')
    del W.cmds[:], W.scheduled[:]
    for l in olx.FileChangeListeners:  # Olex2 has posted its title and path
      l('structure')
    self.assertEqual(W.cmds[0], 'Clear')
    posted = [c for c in W.cmds if c.startswith('Post:')]
    self.assertEqual([p.rstrip() for p in posted], ['Post:reap sucrose.res'])
    self.assertGreater(len(posted[0]), 60)  # full width again
    self.assertIn((1, 'spy.gui.demo.after_load()'), W.scheduled)
    demo.hide(demo._state['serial'])
    del W.cmds[:], W.scheduled[:]
    demo.after_load()  # time is up: just an empty box, no path
    self.assertEqual(W.cmds[0], 'Clear')
    self.assertFalse([c for c in W.cmds if c.startswith('Post:')])
    self.assertEqual(W.scheduled, [])
    demo.mode('off')
    del W.cmds[:]
    demo.after_load('structure')  # off: Olex2's own box stays
    self.assertEqual(W.cmds, [])

  def test_demo_colours_and_back_to_the_skins(self):
    W.mats = {}
    olx = sys.modules['olx']
    olx.SetMaterial = lambda name, m: W.mats.__setitem__(name, m)
    W.params.update({'gui.infobox_text': 'skin-text', 'gui.infobox_plane': 'skin-plane'})
    demo.mode('on')  # no demo colours: the skin's text, and no box (opacity 0)
    self.assertEqual(W.mats, {'InfoBox.Text': 'skin-text', 'InfoBox.Plane': '3077;0;0'})
    W.params['user.demo.background_opacity'] = 1
    demo.restyle()  # opaque, no colour of its own: the skin's box
    self.assertEqual(W.mats['InfoBox.Plane'], 'skin-plane')
    W.params.update({'user.demo.text_colour': '#ff0000', 'user.demo.background_colour': '#000',
                     'user.demo.background_opacity': 0.5})
    demo.restyle()
    self.assertEqual(W.mats['InfoBox.Text'], '2053;%d;%d' % ((255 << 24) | 255, (255 << 24) | 255))
    # half transparent: the transparency flag 0x400 too, else Olex2 ignores the alpha
    self.assertEqual(W.mats['InfoBox.Plane'], '3077;%d;%d' % (128 << 24, 128 << 24))
    self.assertIsNotNone(demo._state['notes_font'])
    self.assertEqual(demo._state['notes_font'], '#olex2.fnt:frb_12')  # not the demo font
    demo.mode('off')
    self.assertEqual(W.mats, {'InfoBox.Text': 'skin-text', 'InfoBox.Plane': 'skin-plane'})

  def test_exit_switches_it_off(self):
    demo.mode('on')
    del W.cmds[:]
    demo.on_exit()
    self.assertFalse(demo._state['on'])
    self.assertIn("SetFont Notes '#olex2.fnt:frb_12'", W.cmds)
    del W.cmds[:]
    demo.on_exit()  # already off: nothing
    self.assertEqual(W.cmds, [])

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

  def test_key_probe_registers_and_prints(self):
    import contextlib
    import io
    demo.probe_keys('on')
    self.assertEqual(len(W.callbacks.get('onkey', [])), 1)
    self.assertEqual(len(W.callbacks.get('onaccel', [])), 1)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
      self.assertEqual(W.callbacks['onaccel'][0]('Ctrl+G'), '')
    self.assertIn("onaccel: 'Ctrl+G'", out.getvalue())
    demo.probe_keys()  # toggle: off
    self.assertEqual(W.callbacks['onkey'], [])
    self.assertEqual(W.callbacks['onaccel'], [])

  def test_key_labels(self):
    k = demo.key_label
    self.assertEqual(k('a'), ('char', 'a'))
    self.assertEqual(k('Ctrl+P'), ('key', 'Ctrl+P'))
    self.assertEqual(k('ctrl + shift + g'), ('key', 'ctrl+shift+g'))
    self.assertEqual(k('65'), ('char', 'a'))             # wx code, no Shift
    self.assertEqual(k('65 4'), ('char', 'A'))           # Shift
    self.assertEqual(k('80,2'), ('key', 'Ctrl+P'))       # Ctrl
    self.assertEqual(k('49'), ('char', '1'))
    self.assertEqual(k('8'), ('char', '8'))              # one character: the character
    self.assertEqual(k('8 0'), ('edit', 'Backspace'))    # code and flags
    self.assertEqual(k('13'), ('edit', 'Enter'))
    self.assertEqual(k('Escape'), ('edit', 'Esc'))
    self.assertEqual(k('341'), ('key', 'F2'))
    self.assertEqual(k('317 2'), ('key', 'Ctrl+Down'))
    self.assertEqual(k('something odd'), ('unknown', 'something odd'))

  def test_unreadable_keys_are_not_shown(self):
    demo.mode('on')
    on_key, on_accel = W.callbacks['onkey'][0], W.callbacks['onaccel'][0]
    on_key('f')
    shown = demo._state['text']
    on_key('<odd 13 thing>')
    on_accel('<odd>')
    self.assertEqual(demo._state['text'], shown)
    self.assertEqual(demo._state['typing'], 'f')
    self.assertFalse(demo._state['accel_seen'])
    self.assertEqual(demo._state['unknown_keys'][-2:],
                     [('onkey', '<odd 13 thing>'), ('onaccel', '<odd>')])
    demo.mode('off')

  def test_indent_and_leading_spaces(self):
    W.params.update({'gui.console_offset': 32, 'user.demo.font_size': 24})  # 32 px / (0.35 * 32 px)
    demo.show(' |>> fuse')
    posted = [c for c in W.cmds if c.startswith('Post:')][-1]
    self.assertTrue(posted.startswith('Post:    |>> fuse'), repr(posted))  # 3 for the indent + 1
    demo.show('   ')  # nothing to show
    self.assertEqual(demo._state['text'], '    |>> fuse')

  def test_keys_build_the_command_line_and_shortcuts_show(self):
    demo.mode('on')
    self.assertEqual(len(W.callbacks.get('onkey', [])), 1)
    on_key, on_accel = W.callbacks['onkey'][0], W.callbacks['onaccel'][0]
    for c in 'fuss':
      on_key(c)
    on_key('Backspace')
    self.assertEqual(demo._state['typing'], 'fus')
    self.assertEqual(demo._state['text'], demo.prefix() + 'fus')
    on_accel('Ctrl+P')
    self.assertEqual(demo._state['text'], '|Ctrl+P')
    self.assertTrue(demo._state['accel_seen'])
    on_key('Enter')
    self.assertEqual(demo._state['typing'], '')
    demo.mode('off')
    self.assertEqual(W.callbacks['onkey'], [])
    self.assertEqual(W.callbacks['onaccel'], [])
    self.assertEqual(on_key('x'), '')  # off: ignored
    self.assertEqual(demo._state['typing'], '')


  def test_control_characters(self):
    k = demo.key_label
    self.assertEqual(k('\b'), ('edit', 'Backspace'))
    self.assertEqual(k('\x7f'), ('edit', 'Backspace'))
    self.assertEqual(k('\r'), ('edit', 'Enter'))
    self.assertEqual(k('\x1b'), ('edit', 'Esc'))
    self.assertEqual(k('\x10'), ('key', 'Ctrl+P'))
    demo.mode('on')
    on_key = W.callbacks['onkey'][0]
    for c in 'fuse':
      on_key(c)
    on_key('\b')
    self.assertEqual(demo._state['typing'], 'fus')
    for _ in range(3):
      on_key('\b')
    self.assertEqual(demo._state['typing'], '')
    self.assertEqual(demo._state['text'].strip(), demo.prefix().strip())  # last letter gone
    on_key('\r')
    self.assertEqual(demo._state['typing'], '')
    demo.mode('off')

  def test_text_is_posted_before_the_box_is_drawn_and_freeze_is_released(self):
    olx = sys.modules['olx']
    calls = []
    olx.Freeze = lambda state: calls.append('Freeze %s' % state)
    olx.Refresh = lambda: calls.append('Refresh()')
    real_m = sys.modules['olex'].m
    sys.modules['olex'].m = lambda cmd: calls.append(cmd) or real_m(cmd)
    try:
      demo.show('|>> fuse')
      posted = [i for i, c in enumerate(W.cmds) if c.startswith('Post:')]
      self.assertTrue(posted)
      self.assertLess(posted[0], W.cmds.index('ShowWindow info true'))
      # nothing shown before the text is in the box
      # both toggles frozen; unfrozen with the box shown; then a refresh
      self.assertEqual(calls, ['ShowWindow info true', 'Freeze true', 'ShowWindow info',
                               'ShowWindow info', 'Freeze false', 'Refresh()'])
      # an error while frozen: the display is unfrozen all the same
      del calls[:]
      sys.modules['olex'].m = lambda cmd: (_ for _ in ()).throw(RuntimeError('boom')) \
        if cmd == 'ShowWindow info' and 'Freeze true' in calls and 'Freeze false' not in calls \
        else calls.append(cmd)
      with self.assertRaises(RuntimeError):
        demo._redraw()
      self.assertEqual(calls[-1], 'Freeze false')
    finally:
      sys.modules['olex'].m = real_m
      del olx.Freeze, olx.Refresh


  def test_key_callbacks_do_not_draw_while_the_key_is_on_its_way(self):
    """Drawing in the callback let the next key overtake ('refine' -> 'erfin'):
    the callbacks only note the text; one idle job draws it."""
    demo.mode('on')
    on_key, on_accel = W.callbacks['onkey'][0], W.callbacks['onaccel'][0]
    W.hold_idle = True
    del W.cmds[:]
    del W.scheduled[:]
    for c in 'refine':
      on_key(c)
    on_accel('Ctrl+P')
    self.assertEqual(W.cmds, [])  # nothing drawn, no macro run
    self.assertEqual(W.scheduled, [('spy.gui.demo.show_pending()',)])  # one idle job
    W.hold_idle = False
    demo.show_pending()
    self.assertEqual(demo._state['typing'], 'refine')
    self.assertEqual(demo._state['text'], '|Ctrl+P')  # the newest text
    self.assertFalse(demo._state['pending_scheduled'])
    demo.mode('off')

if __name__ == '__main__':
  unittest.main()
