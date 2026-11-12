"""Settings of a gui tool in a phil file of its own, next to its code.

A tool folder (gui/<tool>/) holds <tool>.phil with its settings INSIDE the
user scope:

  user {
    demo {
      seconds = 7
        .type = int
    }
  }

so nothing is added to the shared params.phil, and the user's changes are
saved with all other user settings (spy.SaveUserParams -> DataDir/user.phil).
Olex2 reads user.phil at start-up, before the tool adopts its definitions,
which drops the tool's saved values then: load() therefore applies user.phil
once more after adopting (verified with the real phil handler, 2026-11-12).

  from gui import toolphil
  toolphil.load(__file__, 'demo')    # at import
  OV.GetParam('user.demo.seconds')
  toolphil.set('demo', 'seconds', 5) # set and save
"""
import os
import sys

import olex
import olx
from olexFunctions import OV


def _report(what, err):
  print("Tool settings: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def user_file():
  return os.path.join(OV.DataDir(), 'user.phil')


def load(module_file, tool):
  """Adopt <tool folder>/<tool>.phil, then the user's saved values again.
  True if the definitions were adopted."""
  path = os.path.join(os.path.dirname(os.path.abspath(module_file)), '%s.phil' % tool)
  try:
    with open(path, encoding='utf-8') as f:
      olx.phil_handler.adopt_phil(phil_string=f.read())
  except (OSError, AttributeError, RuntimeError) as err:
    _report("read %s" % path, err)
    return False
  if os.path.exists(user_file()):
    olx.phil_handler.update(phil_file=user_file())
  return True


def set(tool, name, value):
  """Set user.<tool>.<name> and save the user settings."""
  OV.SetParam('user.%s.%s' % (tool, name), value)
  olex.m('spy.SaveUserParams()')
