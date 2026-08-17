"""How much of Olex2's exposed surface this suite actually touches.

Twelve hand-written macro cases is not coverage of a program that exports
231 top-level names and 1665 callables to python. This group does two things
about that:

  - a census, so the number is printed on every run rather than guessed at;
  - a sweep over the information functions, calling each one against a loaded
    structure and requiring it to answer.

The sweep is a smoke test and is labelled as one: it asserts that a function
answers, not that the answer is right. That is worth having anyway - most of
these are read by the GUI, the cif writer or a script on every structure, and
a function that starts raising is a break whether or not anyone checked its
value. Where the value *is* checkable it is checked, in the groups that own
that behaviour.

The list is an allow list rather than a deny list. Enumerating everything and
excluding what looks dangerous gets `Abort`, `Exec` and `Run` called by
accident the first time somebody adds one; naming what is safe to call cannot.
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from pipeline_tests import macro, SkipTest, load, model_in

# Information functions: they answer about the loaded structure and change
# nothing. Grouped the way Olex2 groups them, so a gap is visible.
# Calls that take no argument. The ones that need one are not here - Lst, Env,
# FitCHN, TestHKLF, LS and SGS all do, and calling them bare is a usage error
# rather than a break. They failed silently in the sweep before it looked at
# the return value.
INFO = {
  "files": ["FileName", "FilePath", "FileExt", "FileFull", "FileDrive",
            "BaseDir", "DataDir", "StrDir", "IsFileLoaded", "HKLSrc"],
  "cell": ["CalcVol", "CalcMass", "CalcCHN", "CalcR", "MolInfo", "ADPInfo",
           "CalcAbs"],
  # SGE is deliberately absent: it is not an information call. It transforms
  # the structure - sucrose went from 45 atoms to 26 and it wrote a new ins,
  # hkl and cif - so leaving it in a sweep meant every later case in the area
  # ran against a structure the sweep had silently replaced.
  "symmetry": ["SG", "SGInfo", "LstSymm", "Degen"],
  "model": ["HAddCount", "LSM", "Title", "LstIns", "LstVar", "LstFun",
            "LstMac", "LstFS", "CalcVars"],
  "data": ["HklStat", "Wilson", "HKLF"],
  "app": ["GetCompilationInfo", "CurrentLanguageEncoding", "LogLevel",
          "HasGUI", "LastError"],
}

# Functions that need an argument, so the sweep passes a harmless one.
WITH_ARG = {
  "Cell": "a",
  "IsFileType": "ins",
  "IsPluginInstalled": "nosphera2",
  "IsVar": "olex2_tag",
  "GetEnv": "PATH",
  "StrCmp": None,          # two arguments, exercised in group_macros
}


def register(suite):
  suite.run("api", "census of the exposed surface", t_census, suite)
  for area in sorted(INFO):
    suite.run("api", "information functions: %s" % area,
              t_info_area, suite, area)


def _callables(obj, prefix="", out=None, depth=0):
  if out is None:
    out = set()
  if depth > 3:
    return out
  for n in dir(obj):
    if n.startswith("_"):
      continue
    try:
      v = getattr(obj, n)
    except Exception:
      continue
    full = prefix + "." + n if prefix else n
    if callable(v):
      out.add(full)
    elif hasattr(v, "__dict__"):
      _callables(v, full, out, depth + 1)
  return out


def _exercised():
  """Names this suite mentions, read out of its own sources.

  Approximate by construction - it counts a name that appears as olx.<Name>(
  or at the head of a macro() string. That is the right kind of approximate:
  it cannot claim coverage the sources do not contain, and it updates itself
  when a case is added.
  """
  import re
  here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
    else os.path.join(OV.BaseDir(), "util", "pyUtil", "regression",
                      "olex2_pipeline_tests")
  used = set()
  for f in sorted(os.listdir(here)):
    if not f.endswith(".py"):
      continue
    text = open(os.path.join(here, f), "r", errors="ignore").read()
    used.update(re.findall(r"olx\.((?:\w+\.)*\w+)\s*\(", text))
    for m in re.findall(r'macro\(\s*["\']([A-Za-z_][\w.]*)', text):
      used.add(m)
  # the sweep reaches its names through getattr, which no regex over the
  # source can see, so add them from the tables that drive it
  for area in INFO.values():
    used.update(area)
  used.update(WITH_ARG)
  return used


def t_census(suite):
  """Print the size of the surface and how much of it the suite mentions."""
  total = _callables(olx)
  top = set(n for n in total if "." not in n)
  used = _exercised()
  # compare case-insensitively: macros are called by name, not by spelling
  low = set(n.lower() for n in used)
  hit = set(n for n in top if n.lower() in low)
  pct = 100.0 * len(hit) / max(1, len(top))
  if len(top) < 100:
    raise AssertionError("only %d top-level names found - the olx module did "
                         "not build" % len(top))
  # write the gap out, so what is missing is a list to work through rather
  # than a percentage to feel bad about
  path = os.path.join(suite.scratch, "uncovered.txt")
  try:
    with open(path, "w") as f:
      f.write("untouched top-level olx names, %d of %d\n\n"
              % (len(top) - len(hit), len(top)))
      for n in sorted(top - hit):
        f.write(n + "\n")
  except Exception:
    path = "(not written)"
  return "%d of %d top-level (%.0f%%), %d callables in all; gap listed in %s" % (
    len(hit), len(top), pct, len(total), os.path.basename(path))


def t_info_area(suite, area):
  """Every information function in one area has to answer.

  "Answer" means more than "not raise". Most of these are macros behind a
  function name: they print to the log and hand back a status, 1 for done and
  0 for refused. Four of them - FitCHN, TestHKLF, LS, SGS - were being called
  without their required argument, logging `is provided with 0 arguments`, and
  counted as answered, because nothing was raised and nobody read the 0.
  """
  load(model_in(suite.sample("sucrose")))
  answered, missing, raised, refused = [], [], [], []
  for name in INFO[area]:
    fn = getattr(olx, name, None)
    if fn is None:
      missing.append(name)
      continue
    try:
      arg = WITH_ARG.get(name)
      v = fn(arg) if arg is not None else fn()
    except Exception as e:
      raised.append("%s: %s" % (name, str(e).strip().split("\n")[0][:60]))
      continue
    if isinstance(v, int) and not isinstance(v, bool) and v == 0:
      refused.append(name)
      continue
    answered.append(name)
  if raised:
    raise AssertionError("raised - %s" % "; ".join(raised))
  if missing:
    raise AssertionError("not exported: %s" % ", ".join(missing))
  if refused:
    raise AssertionError("returned 0, so refused: %s" % ", ".join(refused))
  return "%d answered" % len(answered)
