import sys
import time
import olex

class Stats:
  instance = None

  def __init__(self):
    self.tasks = {}
    Stats.instance = self

  def add(self, evt, time):
    if evt not in self.tasks:
      self.tasks[evt] = [0, 0]
    counter = self.tasks[evt]
    counter[0] += 1
    counter[1] += time

  def summary(self):
    total = 0
    for k,v in self.tasks.items():
      print("Task '%s' was executed %s times and consumed %.3f seconds" %(k, v[0], v[1]))
      total += v[1]
    try:
      import olex_gui
      print("Idle time took: %.3f seconds" %(olex_gui.GetIdleTime()))
    except:
      pass
    print("Total time consumed: %.3f seconds" %(total))

def stats():
  if Stats.instance is None:
    Stats()
  return Stats.instance

def start(evt):
  return (evt, time.clock())

def finish(token):
  stats().add(token[0], time.clock()-token[1])

def record(evt, time):
  stats().add(evt, time)

def summary():
  stats().summary()

olex.registerFunction(summary, False, "TimeWatch")
