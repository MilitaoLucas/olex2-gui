import os

class FileId(object):
  """ a simple object to compare files size and timestamp
  """
  name = ""
  mk_time = 0
  size = 0
  def __init__(self):
    pass

  def __init__(self, fn):
    self.name = fn
    self.mk_time = os.stat(fn).st_mtime
    self.size = os.path.getsize(fn)

  def __eq__(self, o: object) -> bool:
    if o is None: return False
    return self.name == o.name and self.mk_time == o.mk_time and self.size == o.size

  def ok(self) -> bool:
    return self.mk_time != 0 and len(self.name) > 0
