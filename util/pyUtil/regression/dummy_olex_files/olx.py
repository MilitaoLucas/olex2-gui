"""Stand-in for the olx module the running Olex2 provides.

The file previously held the three bytes 'Non' - a truncated 'None' - so
`import olx` raised NameError and every test in this directory failed before
it started.

Anything the tests reach for answers as an empty string rather than raising:
these tests are about the readers and the history, and a module that has to
enumerate every olx call it might meet would go stale on the first new one.
A test that needs a real answer should set it, as the readers' tests do with
tmp_dir.
"""
import os
import tempfile

# where writeImage and the file readers put their scratch files
tmp_dir = tempfile.gettempdir()

# <rundir>/util/pyUtil/regression/dummy_olex_files -> <rundir>
_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "..", "..", ".."))
basedir = _root
datadir = _root


def BaseDir():
  """The run directory.

  Answered rather than left to the catch-all below: path_utils.setup_cctbx
  builds the cctbx paths from it, and an empty string makes them relative to
  whatever the caller's working directory happens to be - which then fails on
  a chdir into 'cctbx\\cctbx_build'.
  """
  return _root


def DataDir():
  return _root


class _Anything(object):
  """Callable, and callable through any attribute of itself.

  It also answers as an empty value - iterable, sized, falsy, and empty as a
  string - because callers do `x in olx.Something()` and `for i in ...` on
  whatever they get back. Raising there produces an error inside an exception
  handler, which is what buried the real cause the first time.
  """

  def __init__(self, name="olx"):
    self._name = name

  def __call__(self, *args, **kwds):
    return ""

  def __getattr__(self, item):
    return _Anything("%s.%s" % (self._name, item))

  def __iter__(self):
    return iter(())

  def __contains__(self, item):
    return False

  def __len__(self):
    return 0

  def __bool__(self):
    return False

  __nonzero__ = __bool__

  def __str__(self):
    return ""

  def __repr__(self):
    return "<dummy %s>" % self._name


def __getattr__(name):
  # module level, so it is only reached for names not defined above
  if name.startswith("__"):
    raise AttributeError(name)
  return _Anything("olx." + name)
