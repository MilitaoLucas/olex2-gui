"""pTB pre-refinement, the calculation log and the PRE-REFINEMENT line of the CIF.

The pre-refine checkbox runs the first cycles of a NoSpherA2 refinement with
pTB and hands over to the selected program. What has to hold:

  - pTB runs the asked number of cycles, then the selected program; the source
    ends on that program's table, PTB_PREREFINE_DONE says what pTB preceded
  - once done, pre-refine is skipped until the box is ticked again
  - the R1 guard stops the pTB cycles, puts the selected program back as the
    source and switches pre-refine off
  - a table-only run (run_refine off) never runs pTB
  - the CIF names pTB only while the calculation log shows that nothing but
    the table's level of theory refined after the last pTB cycles, whether
    those came from the checkbox or from pTB chosen as the source

The follow-up program is OCC (compiled into NoSpherA2) with r2SCAN/6-31G, so the
group needs no external QM program besides pTB; a hybrid functional costs OCC
about nine minutes per sucrose table on four cores, r2SCAN well under one.
Every case starts from a fresh copy of sucrose.

  OLEX2_TEST_GROUPS=ptb_prerefine
  OLEX2_TEST_NCPUS, OLEX2_TEST_MEM   as for nsa2_matrix
"""
from __future__ import absolute_import, division, print_function

import os

import olx
import olex
from olexFunctions import OV

from variableFunctions import nsa2_get_param, nsa2_set_param

from pipeline_tests import SkipTest, clear_r1
from group_nosphera2 import _refine_capturing, _reason
import group_nsa2_matrix as M

SAMPLE = "sucrose"
PRE_LINE = "PRE-REFINEMENT:"


def register(suite):
  suite.run("ptb_pre", "backends enabled", M.t_enable)
  suite.run("ptb_pre", "CIF rule read from the log", t_log_rule, suite)
  suite.run("ptb_pre", "pre-refine, repeat, level change", t_prerefine, suite)
  suite.run("ptb_pre", "R1 guard", t_guard, suite)
  suite.run("ptb_pre", "table only runs no pTB", t_table_only, suite)
  suite.run("ptb_pre", "pTB as the source, then OCC", t_ptb_source, suite)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _ptb():
  from NoSpherA2.NoSpherA2 import NoSpherA2_instance as nsp2
  if not nsp2.ptb_exe:
    raise SkipTest("no pTB executable")
  return M._available("pTB")


def _occ(suite):
  ptb = _ptb()
  occ = M._available("OCC")
  folder, r_sph = M._prepare(suite, SAMPLE)
  M._set_aspherical(SAMPLE, occ)
  nsa2_set_param('method', 'r2SCAN')
  nsa2_set_param('basis_name', '6-31G')
  return folder, occ, ptb


def _arm(cycles):
  nsa2_set_param('PTB_PREREFINE', True)
  nsa2_set_param('PTB_PREREFINE_CYCLES', str(cycles))
  nsa2_set_param('PTB_PREREFINE_DONE', '')


def _log(folder):
  path = os.path.join(folder, "olex2", "%s_calculation_log.txt" % OV.FileName())
  if not os.path.exists(path):
    raise AssertionError("no calculation log at %s" % path)
  with open(path, encoding="utf-8", errors="ignore") as f:
    return f.read()


def _last_run(folder):
  return _log(folder).split("=== NoSpherA2 refinement:")[-1]


def _sources(block):
  """the source column of every refined cycle row in one log block"""
  rows = []
  for line in block.splitlines():
    s = line.split()
    if len(s) > 2 and s[0].isdigit() and "(table" not in line:
      rows.append(s[1])
  return rows


def _cif():
  """(_olex2_refine_details, _refine_special_details) for the current table"""
  import aaff
  c = {}
  aaff.get_refinement_details(c, False)
  return str(c.get('_olex2_refine_details')), str(c.get('_refine_special_details'))


def _first_pre(details):
  lines = [l.strip() for l in str(details).splitlines() if PRE_LINE in l]
  return lines[0] if lines else None


def _pre_line():
  """the PRE-REFINEMENT line of the CIF the last run wrote, which must match the one built after it"""
  details, special = _cif()
  if "SOFTWARE:" not in details:
    raise AssertionError("no NoSpherA2 details in the CIF at all")
  line = _first_pre(details)
  if line and PRE_LINE not in special:
    raise AssertionError("PRE-REFINEMENT in _olex2_refine_details but not in _refine_special_details")
  # olex2.refine builds the CIF inside the last cycle, before the log has that cycle's row
  if _run_cif is None:
    raise AssertionError("the run built no CIF block")
  if _first_pre(_run_cif) != line:
    raise AssertionError("the run's CIF says %r, built afterwards %r" % (_first_pre(_run_cif), line))
  return line


_run_cif = None


def _run(folder, what):
  """refine, keeping the _olex2_refine_details of the last CIF block the refinement built"""
  global _run_cif
  import aaff
  # the marker of an earlier run must not stand in for this one
  for f in os.listdir(folder):
    if f.endswith(".NoSpherA2"):
      os.remove(os.path.join(folder, f))
  clear_r1()
  real, built = aaff.get_refinement_details, []
  def spy(cif_block, acta_stuff):
    real(cif_block, acta_stuff)
    built.append(str(cif_block['_olex2_refine_details']) if '_olex2_refine_details' in cif_block else "")
  aaff.get_refinement_details = spy
  try:
    said = _refine_capturing()
  finally:
    aaff.get_refinement_details = real
  _run_cif = built[-1] if built else None
  if "Refinement finished at" not in M._har_log_text(folder):
    raise AssertionError("%s did not finish%s" % (what, _reason(said)))
  return said


def _expect(line, text):
  if line is None or text not in line:
    raise AssertionError("expected %r in the CIF, got %r" % (text, line))


# ---------------------------------------------------------------------------
# cases
# ---------------------------------------------------------------------------

def t_log_rule(suite):
  """ptb_before_level against hand-written logs: no calculation"""
  from NoSpherA2 import calc_log
  folder = M.sample_copy(suite, SAMPLE)
  M._load_model(folder, M._model_file(folder))
  os.makedirs(os.path.join(folder, "olex2"), exist_ok=True)
  path = os.path.join(folder, "olex2", "%s_calculation_log.txt" % OV.FileName())

  def block(source, method, basis, rows, generator=None):
    s = "\n=== NoSpherA2 refinement: x ===\nsettings (%s, from cycle 1):\n" % source
    if generator:
      s += "  generator = %s\n" % generator
    if method:
      s += "  method = %s\n  basis_name = %s\n" % (method, basis)
    s += "  cycle  source  wfn+tsc\n"
    s += "".join("  %5d  %s  1 s  1 s  0.1  C1.x  3.0  7.0\n" % (i + 1, source) for i in range(rows))
    return s + "result = finished\n=== end ===\n"

  ptb = block("pTB", None, None, 2)
  occ = block("OCC", "r2SCAN", "def2-SVP", 1)
  # what the checkbox writes: one entry, a second settings block when OCC takes over
  one = ptb.replace("result = finished\n=== end ===\n", "") \
        + "settings (OCC, from cycle 3):\n  method = r2SCAN\n  basis_name = def2-SVP\n  cycle  source  wfn+tsc\n" \
        + "      3  OCC  1 s  1 s  0.1  C1.x  3.0  7.0\nresult = finished\n=== end ===\n"
  cases = [
    ("pTB then OCC", ptb + occ, (2, 1)),
    ("pre-refine, one entry", one, (2, 1)),
    ("pTB then ORCA", ptb + block("ORCA 6.1", "r2SCAN", "def2-SVP", 1), None),
    ("then OCC again", ptb + occ + occ, (2, 2)),
    ("then a refinement on the finished table", ptb + occ + block("sucrose.tscb", "r2SCAN", "def2-SVP", 1, "OCC"), (2, 2)),
    ("then another basis", ptb + occ + block("OCC", "r2SCAN", "6-31G", 1), None),
    ("pTB last", occ + ptb, None),
    ("never pTB", occ, None),
    ("table only after pTB", ptb + occ.replace("C1.x  3.0  7.0", "(table only, no refinement)"), None),
  ]
  bad = []
  try:
    for name, text, want in cases:
      with open(path, "w", encoding="utf-8") as f:
        f.write(text)
      got = calc_log.ptb_before_level("OCC", "r2SCAN", "def2-SVP", {})
      if got != want:
        bad.append("%s: %r, expected %r" % (name, got, want))
  finally:
    os.remove(path)
  # inside a refinement cycle that cycle is not logged yet, but refines with this table
  # a pTB cycle in progress (Hybrid keeps its source) is not one
  cycling = [
    ("in the cycle after pTB", ptb, False, (2, 1)),
    ("in the second cycle after pTB", ptb + occ, False, (2, 2)),
    ("in a cycle after another basis", ptb + block("OCC", "r2SCAN", "6-31G", 1), False, None),
    ("in a cycle, never pTB", occ, False, None),
    ("in a pTB cycle", ptb, True, None),
  ]
  calc_log._entry = calc_log._Refinement("OCC")
  try:
    for name, text, pre, want in cycling:
      calc_log.cycle_start(pre)
      with open(path, "w", encoding="utf-8") as f:
        f.write(text)
      got = calc_log.ptb_before_level("OCC", "r2SCAN", "def2-SVP", {})
      if got != want:
        bad.append("%s: %r, expected %r" % (name, got, want))
  finally:
    calc_log._entry = None
    os.remove(path)
  if calc_log.has_log():
    bad.append("has_log() true after the log was removed")
  if bad:
    raise AssertionError("; ".join(bad))
  return "%d logs" % (len(cases) + len(cycling))


def t_prerefine(suite):
  folder, occ, ptb = _occ(suite)
  _arm(1)
  _run(folder, "pre-refine + OCC")
  rows = _sources(_last_run(folder))
  if rows != ["pTB", occ.strip()]:
    raise AssertionError("cycles ran as %s, expected pTB then %s" % (rows, occ.strip()))
  done = str(nsa2_get_param('PTB_PREREFINE_DONE'))
  if not done.startswith("1 pTB cycle before %s/" % occ.strip()):
    raise AssertionError("PTB_PREREFINE_DONE = %r" % done)
  if nsa2_get_param('source').strip() != nsa2_get_param('file').strip():
    raise AssertionError("source %r is not the table %r" % (nsa2_get_param('source'), nsa2_get_param('file')))
  _expect(_pre_line(), "1 pTB cycle before %s/r2SCAN, followed by only 1 refinement cycle" % occ.strip())
  # once done, a new run with the box still on must not go back to pTB
  nsa2_set_param('source', occ)
  nsa2_set_param('PTB_PREREFINE', True)
  _run(folder, "second OCC run")
  block = _last_run(folder)
  if "pTB" in _sources(block) or "skipped, already done" not in block:
    raise AssertionError("pTB ran again although it was done")
  line = _pre_line()
  _expect(line, "1 pTB cycle before %s/r2SCAN" % occ.strip())
  if "followed by only 1" in line:
    raise AssertionError("still says only 1 cycle followed after two: %r" % line)
  # another basis is another level of theory, but the model still went through pTB: the line stays, once
  nsa2_set_param('source', occ)
  nsa2_set_param('basis_name', '3-21G')
  _run(folder, "OCC 3-21G run")
  _expect(_pre_line(), "1 pTB cycle before %s/r2SCAN" % occ.strip())
  if _cif()[1].count(PRE_LINE) != 1:
    raise AssertionError("PRE-REFINEMENT not exactly once in _refine_special_details: %r" % _cif()[1])
  return "pTB -> OCC, skipped on repeat, claim kept once after 3-21G"


def t_guard(suite):
  folder, occ, ptb = _occ(suite)
  _arm(2)
  # a starting R1 of 0.001 makes any pTB R1 a rise of more than 10 %
  OV.SetParam('snum.refinement.last_R1', 0.001)
  said = _refine_capturing()
  block = _last_run(folder)
  if "STOPPED by the R1 guard" not in block:
    raise AssertionError("guard did not stop the run%s" % _reason(said))
  if _sources(block) != ["pTB"]:
    raise AssertionError("cycles ran as %s, expected one pTB cycle" % _sources(block))
  if nsa2_get_param('source').strip() != occ.strip():
    raise AssertionError("source %r, expected %s back" % (nsa2_get_param('source'), occ.strip()))
  if str(nsa2_get_param('PTB_PREREFINE')).strip().lower() in ('true', '1') or str(nsa2_get_param('PTB_PREREFINE_DONE') or '').strip():
    raise AssertionError("pre-refine still on or marked done after the guard")
  return "stopped after pTB cycle 1, %s restored, pre-refine off" % occ.strip()


def t_table_only(suite):
  folder, occ, ptb = _occ(suite)
  _arm(1)
  nsa2_set_param('run_refine', False)
  said = _refine_capturing()
  block = _last_run(folder)
  if "pTB pre-refinement = off" not in block or _sources(block):
    raise AssertionError("table-only run ran pTB or refined%s" % _reason(said))
  from NoSpherA2.utilities import nsa2_read_settings_header
  table = os.path.join(folder, nsa2_get_param('file').strip())
  rec = nsa2_read_settings_header(table) or {}
  if str(rec.get('SOURCE', '')).strip() != occ.strip():
    raise AssertionError("table %s made by %r, expected %s" % (os.path.basename(table), rec.get('SOURCE'), occ.strip()))
  return "%s table, no pTB" % occ.strip()


def t_ptb_source(suite):
  folder, occ, ptb = _occ(suite)
  nsa2_set_param('PTB_PREREFINE', False)
  nsa2_set_param('PTB_PREREFINE_DONE', '')
  nsa2_set_param('source', ptb)
  _run(folder, "pTB refinement")
  if _pre_line() is not None:
    raise AssertionError("a pTB table claims a pre-refinement")
  nsa2_set_param('source', occ)
  _run(folder, "OCC refinement")
  _expect(_pre_line(), "1 pTB cycle before %s/r2SCAN, followed by only 1 refinement cycle" % occ.strip())
  return "pTB, then %s: claimed" % occ.strip()
