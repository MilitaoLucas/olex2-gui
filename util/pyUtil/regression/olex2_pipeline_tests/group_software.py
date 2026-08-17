"""What NoSpherA2 offers has to follow what is on PATH.

`setup_software` resolves an executable and either offers the program or, for
the ones registered with get=True, offers a "Get <name>" line instead. That is
the only thing standing between a user and a dropdown entry that launches
something which is not installed - or, worse, an installed program that is
never offered.

These cases drive it directly: take a program that is installed, remove its
directory from PATH, re-run its setup, and require the offer to change. Then
put PATH back and require it to change back. Nothing is stubbed; it is the
real resolver and the real setup code.

The instance is a singleton shared with the rest of the suite, so every case
restores both PATH and the software list on the way out.
"""
from __future__ import absolute_import, division, print_function

import os
import shutil

import olx
import olex
from olexFunctions import OV

from pipeline_tests import SkipTest

# label as offered -> executable looked for, and whether a missing one is
# supposed to produce a "Get <label>" line. From setup_software and the
# setup_* methods in NoSpherA2.py.
BACKENDS = [
  ("ORCA",           "orca",              True,  "setup_orca_executables"),
  ("xTB",            "xtb",               True,  "setup_xtb_executables"),
  ("discambMATTS",   "discambMATTS2tsc",  True,  "setup_discamb"),
  ("pTB",            "ptb",               False, "setup_ptb_executables"),
]


def register(suite):
  suite.run("software", "what is offered matches what is on PATH",
            t_offered_matches_path)
  for label, exe, gets, setup in BACKENDS:
    suite.run("software", "%s follows PATH" % label,
              t_follows_path, label, exe, gets, setup)
  suite.run("software", "the two PATH resolvers agree", t_resolvers_agree)


def _nsp2():
  try:
    from NoSpherA2.NoSpherA2 import NoSpherA2_instance
  except ImportError:
    raise SkipTest("NoSpherA2 is not loaded")
  return NoSpherA2_instance


def _which(exe):
  """The resolver NoSpherA2's setup_software uses."""
  name = exe + (".exe" if os.name == "nt" else "")
  return str(olx.file.Which(name, current_dir=False) or "")


def _offers(text, label):
  """Whether a list offers the program itself, and whether it offers a Get."""
  entries = [e.strip() for e in str(text).split(";") if e.strip()]
  has = any(e == label or (e.startswith(label) and not e.startswith("Get "))
            for e in entries)
  get = any(e == "Get " + label for e in entries)
  return has, get


def t_offered_matches_path():
  """Every backend is offered if and only if its executable resolves."""
  nsp2 = _nsp2()
  listed = str(nsp2.softwares)
  wrong = []
  for label, exe, gets, _ in BACKENDS:
    found = bool(_which(exe))
    has, get = _offers(listed, label)
    if found and not has:
      wrong.append("%s is on PATH but not offered" % label)
    if not found and has:
      wrong.append("%s is offered but not on PATH" % label)
    if not found and gets and not get:
      wrong.append("%s is missing and there is no 'Get %s'" % (label, label))
  if wrong:
    raise AssertionError("; ".join(wrong))
  return "%d backends agree with PATH" % len(BACKENDS)


def t_follows_path(label, exe, gets, setup):
  """Removing the program from PATH has to change what is offered.

  This is the case that matters: it proves the offer is computed from PATH
  rather than baked in, in both directions. A list that never changes would
  pass an "is it offered" check on a machine where everything happens to be
  installed.
  """
  nsp2 = _nsp2()
  fn = getattr(nsp2, setup, None)
  if fn is None:
    raise SkipTest("%s is not a method on the NoSpherA2 instance" % setup)
  found = _which(exe)
  if not found:
    # still worth asserting the missing case, which is the state here
    saved = nsp2.softwares
    try:
      nsp2.softwares = ""
      fn()
      has, get = _offers(nsp2.softwares, label)
      if has:
        raise AssertionError("%s is offered with nothing on PATH" % label)
      if gets and not get:
        raise AssertionError("%s is missing and no 'Get %s' was offered (%r)"
                             % (label, label, nsp2.softwares))
    finally:
      nsp2.softwares = saved
    return "not installed; offered as 'Get %s'" % label if gets else \
      "not installed and not offered"

  d = os.path.dirname(found)
  saved_path, saved_soft = os.environ["PATH"], nsp2.softwares
  try:
    kept = [p for p in saved_path.split(os.pathsep)
            if p and os.path.normcase(os.path.normpath(p))
            != os.path.normcase(os.path.normpath(d))]
    os.environ["PATH"] = os.pathsep.join(kept)
    still = _which(exe)
    if still:
      # olx.file.Which searches the Olex2 base directory as well as PATH, so a
      # program shipped beside olex2 cannot be hidden by editing PATH. That is
      # not a failure of anything - it is why discambMATTS2tsc is found here
      # while shutil.which returns None for it.
      where = "the base directory" if os.path.normcase(os.path.dirname(still)) \
        == os.path.normcase(str(olx.BaseDir()).rstrip("\\/")) else still
      raise SkipTest("%s is still resolved from %s with %s off PATH"
                     % (exe, where, d))
    nsp2.softwares = ""
    fn()
    has, get = _offers(nsp2.softwares, label)
    if has:
      raise AssertionError("%s is still offered with %s off PATH"
                           % (label, exe))
    if gets and not get:
      raise AssertionError("%s went off PATH and no 'Get %s' appeared (%r)"
                           % (label, label, nsp2.softwares))

    os.environ["PATH"] = saved_path
    nsp2.softwares = ""
    fn()
    has_back, get_back = _offers(nsp2.softwares, label)
    if not has_back:
      raise AssertionError("%s did not come back when PATH was restored (%r)"
                           % (label, nsp2.softwares))
    if get_back:
      raise AssertionError("%s is installed and still offered as 'Get %s'"
                           % (label, label))
  finally:
    os.environ["PATH"] = saved_path
    nsp2.softwares = saved_soft
  return "off PATH -> %s, back on -> offered" % ("Get " + label if gets
                                                 else "not offered")


def t_resolvers_agree():
  """The two PATH resolvers in use must find the same file.

  setup_software goes through olx.file.Which; setup_orca_executables used
  shutil.which. They search differently - olx.file.Which also looks in the
  Olex2 base directory, which is how discambMATTS2tsc is found here when it is
  not on PATH at all - so the same name can resolve to different files.

  On this machine they happen to agree for every installed backend, so this
  case is a guard against the two drifting apart rather than a reproduction of
  a live fault. Worth keeping: a machine with two installations of the same
  program is exactly where it would bite, and the symptom would be a version
  label describing a different binary from the one the job runs.
  """
  disagree = []
  for label, exe, _, _ in BACKENDS:
    name = exe + (".exe" if os.name == "nt" else "")
    a = _which(exe)
    b = shutil.which(name) or ""
    if not a or not b:
      continue
    if os.path.normcase(os.path.normpath(a)) != os.path.normcase(os.path.normpath(b)):
      disagree.append("%s: olx.file.Which %s, shutil.which %s" % (label, a, b))
  if disagree:
    raise AssertionError("; ".join(disagree))
  return "both resolvers agree for every installed backend"
