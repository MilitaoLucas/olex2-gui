import time, inspect

class evt_reg(object):
  def __init__(self, manager, evt, parent=None, scope=False):
    self.manager = manager
    self.event = evt
    self.parent = parent
    self.level = 0
    if parent:
      self.level = parent.level + 1
    self.begin = time.time()
    self.end = None
    self.events = []
    self.scope = scope

  def log(self):
    if self.end is None:
      self.end = time.time()
      if self.events and self.events[-1].end is None:
        self.events[-1].end = self.end
    elif self.events:
      if self.events[-1].end is None:
        self.events[-1].end = self.end
      elif self.events[-1].end > self.end:
        self.end = self.events[-1].end
    padding = " " * self.level
    print("%s%.3fs: %s" %(padding, (self.end - self.begin), self.event))
    for e in self.events:
      e.log()

  def stop(self):
    if self.end is None:
      self.end = time.time()
    if self.events and self.events[-1].end is None:
      self.events[-1].stop()
    if self.parent:
      self.manager.current = self.parent

  def start(self, evt_, scope=False):
    if not self.scope:
      return self.parent.start(evt_, scope)
    if self.events:
      self.events[-1].stop()
    evt = evt_reg(self.manager, evt_, self, scope=scope)
    self.events.append(evt)
    self.manager.current = evt
    return evt

  def run(self, func, *args, **kwds):
    evt = self.start(func.__qualname__ , scope=True)
    try:
      return func(*args, **kwds)
    finally:
      evt.end = time.time()
      if not self.scope:
        self.stop()
      else:
        self.end = time.time()
      self.manager.current = self

  def root(self):
    x = self.parent
    while x:
      if x.parent is None:
        return x
      x = x.parent

class olxtm(object):
  def __init__(self, active=True):
    self.st = time.time()
    self.root = evt_reg(self, "= T I M I N G S ============================================", scope=True)
    self.current = self.root
    self.silent = not active
    self.active = active

  def start(self, evt=None, scope=False):
    if not self.active: return
    if not evt:
      try:
        evt = inspect.stack()[0][3]
      except:
        evt = "ROOT"
    return self.current.start(evt, scope=scope)

  def start_scope(self, evt=None):
    return self.start(evt, scope=True)

  def stop(self):
    if not self.active: return
    self.current.stop()

  def run(self, func, *args, **kwds):
    if not self.active:
      return func(*args, **kwds)
    return self.current.run(func, *args, **kwds)

  def exec(self, txt):
    evt = self.start(txt)
    try:
      exec(txt)
    finally:
      if evt is not None: #not active
        evt.stop()

  def log(self):
    if self.silent:
      return
    self.root.log()
