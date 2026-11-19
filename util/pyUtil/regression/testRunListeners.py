"""RunPrg.ListenerManager: one start and one end per refinement or solution.

Only the ListenerManager class is taken from PyToolLib/RunPrg.py; the rest
of RunPrg needs a running Olex2. Run from this folder:
  python -m unittest testRunListeners
"""
import ast
import os
import sys
import unittest
from contextlib import contextmanager

HERE = os.path.dirname(os.path.abspath(__file__))
RUNPRG = os.path.join(os.path.dirname(HERE), 'PyToolLib', 'RunPrg.py')


def load_listener_manager():
  with open(RUNPRG, encoding='utf-8') as f:
    tree = ast.parse(f.read(), RUNPRG)
  node = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ListenerManager'][0]
  ns = {'contextmanager': contextmanager, 'sys': sys, '__name__': 'RunPrg'}
  exec(compile(ast.Module(body=[node], type_ignores=[]), RUNPRG, 'exec'), ns)
  return ns['ListenerManager']


ListenerManager = load_listener_manager()


class Recorder(object):
  def __init__(self, lm):
    self.events = []
    lm.register_listener(self.onStart, 'onStart')
    lm.register_listener(self.onEnd, 'onEnd')

  def onStart(self, caller):
    self.events.append(('start', caller))

  def onEnd(self, caller):
    self.events.append(('end', caller))


class Prg(object):
  """Stands in for RunPrg: startRun/endRun around each program step, and
  run() as a whole run, like RunRefinementPrg.run / RunSolutionPrg.run."""
  def __init__(self, lm):
    self.lm = lm

  def startRun(self):
    self.lm.startRun(self)

  def endRun(self):
    self.lm.endRun(self)

  def run(self, body):
    with self.lm.whole_run(self):
      return body(self)


class ListenerManagerTests(unittest.TestCase):

  def setUp(self):
    self.lm = ListenerManager()
    self.rec = Recorder(self.lm)
    self.prg = Prg(self.lm)

  def test_flag_for_plugins(self):
    self.assertTrue(ListenerManager.whole_runs)

  def test_steps_inside_a_run_are_announced_once(self):
    # a NoSpherA2 refinement: one startRun/endRun per refinement step
    def har(prg):
      for _ in range(3):
        prg.startRun()
        prg.endRun()
    self.prg.run(har)
    self.assertEqual(self.rec.events, [('start', self.prg), ('end', self.prg)])

  def test_start_without_end_is_ended(self):
    # a solution that returns after startRun without endRun
    self.prg.run(lambda prg: prg.startRun())
    self.assertEqual([e for e, c in self.rec.events], ['start', 'end'])
    self.prg.run(lambda prg: None)
    self.assertEqual([e for e, c in self.rec.events], ['start', 'end'] * 2)

  def test_a_run_that_raises_is_ended(self):
    def crash(prg):
      raise RuntimeError('crashed')
    with self.assertRaises(RuntimeError):
      self.prg.run(crash)
    self.assertEqual([e for e, c in self.rec.events], ['start', 'end'])
    self.assertIsNone(self.lm._current_run)

  def test_nested_whole_run_is_part_of_the_outer_one(self):
    inner = Prg(self.lm)
    self.prg.run(lambda prg: inner.run(lambda p: None))
    self.assertEqual(self.rec.events, [('start', self.prg), ('end', self.prg)])

  def test_calls_outside_a_whole_run_are_passed_on(self):
    self.prg.startRun()
    self.prg.endRun()
    self.assertEqual([e for e, c in self.rec.events], ['start', 'end'])

  def test_failing_listener_is_reported_and_others_still_run(self):
    def broken(caller):
      raise ValueError('listener bug')
    self.lm.onStart_listeners.insert(0, broken)
    import io
    from contextlib import redirect_stderr
    err = io.StringIO()
    with redirect_stderr(err):
      result = self.prg.run(lambda prg: 'done')
    self.assertEqual(result, 'done')
    self.assertIn('listener bug', err.getvalue())
    self.assertEqual([e for e, c in self.rec.events], ['start', 'end'])

  def test_registering_again_replaces(self):
    newer = Recorder(self.lm)  # same class: e.g. after a module reload
    self.assertEqual(len(self.lm.onStart_listeners), 1)
    self.prg.run(lambda prg: None)
    self.assertEqual(self.rec.events, [])
    self.assertEqual(len(newer.events), 2)

  def test_unregister(self):
    self.assertTrue(self.lm.unregister_listener(self.rec.onStart, 'onStart'))
    self.assertFalse(self.lm.unregister_listener(self.rec.onStart, 'onStart'))
    self.prg.run(lambda prg: None)
    self.assertEqual([e for e, c in self.rec.events], ['end'])

  def test_unknown_event_is_an_error(self):
    with self.assertRaises(ValueError):
      self.lm.register_listener(self.rec.onStart, 'onstart')


if __name__ == '__main__':
  unittest.main()
