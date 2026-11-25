"""The split buttons Solve and Refine (cbtn style 'tab'): while a solution or
refinement runs, the left part (btn-solve, btn-refine) shows its 'highlight'
image, whose top bar has the highlight colour (PilTools make_arrows); at the
end the resting images come back.

Listens to RunPrg's run events (LM, onStart/onEnd); only swaps the image of a
control that is on the page.
"""
import sys

from olexFunctions import OV

BUTTONS = {'solution': 'btn-solve', 'refinement': 'btn-refine'}


def _report(what, err):
  print("Run mark: could not %s: %s" % (what, err))
  if hasattr(sys, '_wing_debugger'):
    raise err


def _button(caller):
  if OV.GetParam('gui.timage.cbtn.style', 'arrows') != 'tab':
    return None
  return BUTTONS.get(getattr(caller, 'prgType', None))


def _show(name, images):
  control = 'IMG_%s' % name.upper()
  if not OV.IsControl(control):
    return
  OV.SetImage(control, images, check=False)
  OV.Refresh()


def on_start(caller):
  name = _button(caller)
  if name:
    try:
      _show(name, 'up=%shighlight.png,down=%shighlight.png,hover=%shighlight.png' % (name, name, name))
    except Exception as err:  # never let the mark stop a run
      _report("mark the run on %s" % name, err)


def on_end(caller):
  name = _button(caller)
  if name:
    try:
      _show(name, 'up=%soff.png,down=%soff.png,hover=%shover.png' % (name, name, name))
    except Exception as err:
      _report("unmark %s" % name, err)


def register():
  try:
    from RunPrg import LM
  except ImportError as err:  # no RunPrg (olex2c without the GUI tools)
    _report("find the run events", err)
    return
  LM.register_listener(on_start, 'onStart')
  LM.register_listener(on_end, 'onEnd')
