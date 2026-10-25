import datetime
import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import nsa2_runs as R

ORCA_LOG = """
                                 * O   R   C   A *
                         Program Version 6.1.0  -  RELEASE   -
                                       INPUT FILE
|  1> ! NoPop MiniPrint 3-21G r2SCAN DefGrid1 def2/J RIJCOSX CPCM(Water)
|  6> %coords
|  8>   charge -1
|  9>   mult 2
FINAL SINGLE POINT ENERGY     -10.5
FINAL SINGLE POINT ENERGY     -12.25
"""
PTB_LOG = """
       |                 P T B                      |
       Version 3.7, 08. Mar 2024
 nalpha           68
 nbeta            68
 nopen             0
"""
PTB_HEADER = ["origin: pTB", "source: pTB", "method: B3LYP", "basis_name: def2-SVP",
              "charge: 0", "multiplicity: 1", "ORCA_USE_CRYSTAL_QMMM: True"]


def _table(path, header, body):
  with open(path, "wb") as f:
    f.write(b"\t  SCATTERER_IDS\n")
    for h in header:
      f.write(("NSA2_%s\n" % h).encode())
    f.write(b"SOURCE_LABELS: O1 C1\n" + body)


class Base(unittest.TestCase):
  name = "s"

  def setUp(self):
    self.dir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, self.dir)

  def add_run(self, when, header, log, wfn_ext, body):
    stamp = when.strftime("%Y-%m-%d_%H-%M-%S")
    d = os.path.join(R.history_root(self.dir), "%s_%s" % (self.name, stamp))
    os.makedirs(d)
    self._write(d, header, log, wfn_ext, body, when)
    return d

  def add_live(self, when, header, log, wfn_ext, body):
    self._write(self.dir, header, log, wfn_ext, body, when)

  def _write(self, d, header, log, wfn_ext, body, when):
    t = time.mktime(when.timetuple())
    _table(os.path.join(d, self.name + ".tscb"), header, body)
    with open(os.path.join(d, self.name + ".wfnlog"), "w") as f:
      f.write(log)
    with open(os.path.join(d, self.name + wfn_ext), "wb") as f:
      f.write(body * 2)
    for e in (".tscb", ".wfnlog", wfn_ext):
      os.utime(os.path.join(d, self.name + e), (t, t))


class TestReading(Base):

  def test_header(self):
    p = os.path.join(self.dir, "t.tscb")
    _table(p, PTB_HEADER, b"\x00\x01binary NSA2_fake: no")
    h = R.read_table_header(p)
    self.assertEqual(h["source"], "pTB")
    self.assertEqual(h["ORCA_USE_CRYSTAL_QMMM"], "True")
    self.assertNotIn("fake", h)

  def test_orca_log(self):
    p = os.path.join(self.dir, "o.wfnlog")
    with open(p, "w") as f:
      f.write(ORCA_LOG)
    info = R.read_wfnlog(p)
    self.assertEqual(info["program"], "ORCA")
    self.assertEqual(info["version"], "6.1.0")
    self.assertEqual(info["method"], "r2SCAN")
    self.assertEqual(info["basis_name"], "3-21G")
    self.assertEqual(info["charge"], "-1")
    self.assertEqual(info["multiplicity"], "2")
    self.assertEqual(info["energy"], "-12.25")

  def test_ptb_log(self):
    p = os.path.join(self.dir, "p.wfnlog")
    with open(p, "w") as f:
      f.write(PTB_LOG)
    info = R.read_wfnlog(p)
    self.assertEqual(info["program"], "pTB")
    self.assertEqual(info["version"], "3.7")
    self.assertEqual(info["multiplicity"], "1")

  def test_program_name(self):
    self.assertEqual(R.program_name("ORCA 6.1"), "ORCA")
    self.assertEqual(R.program_name("discambMATTS2021"), "DiSCaMB")
    self.assertEqual(R.program_name(""), "")


class TestScan(Base):

  def setUp(self):
    super(TestScan, self).setUp()
    t0 = datetime.datetime(2026, 7, 1, 9, 2, 18)
    self.add_run(t0, [], ORCA_LOG, ".gbw", b"orca")
    t1 = datetime.datetime(2026, 10, 20, 14, 23, 56)
    for i in range(3):
      self.add_run(t1 + datetime.timedelta(seconds=14 * i), PTB_HEADER, PTB_LOG,
                   ".xtb", b"ptb%d" % i)
    self.live_time = t1 + datetime.timedelta(seconds=200)
    self.add_live(self.live_time, PTB_HEADER, PTB_LOG, ".xtb", b"ptbL")

  def test_scan_and_group(self):
    runs = R.scan(self.dir, self.name)
    self.assertEqual(len(runs), 5)
    self.assertEqual(runs[0]["program"], "ORCA")
    self.assertFalse(runs[0]["header"])
    self.assertEqual(runs[0]["basis_name"], "3-21G")
    # pTB: the header's B3LYP/def2-SVP is the GUI's, not what ran
    self.assertEqual(runs[1]["method"], "")
    self.assertEqual(runs[1]["basis_name"], "")
    self.assertTrue(runs[1]["qmmm"])
    self.assertTrue(runs[-1].get("live"))
    self.assertEqual([len(g) for g in R.group(runs)], [1, 3, 1])

  def test_switch_and_back(self):
    runs = R.scan(self.dir, self.name)
    table = R.switch_to(self.dir, self.name, runs[0])
    self.assertEqual(os.path.basename(table), "s.tscb")
    self.assertTrue(os.path.exists(os.path.join(self.dir, "s.gbw")))
    self.assertFalse(os.path.exists(os.path.join(self.dir, "s.xtb")))
    # the live run went into the history, named as NoSpherA2 would name it
    live_dir = os.path.join(R.history_root(self.dir),
                            "s_" + self.live_time.strftime("%Y-%m-%d_%H-%M-%S"))
    self.assertTrue(os.path.exists(os.path.join(live_dir, "s.xtb")))
    runs = R.scan(self.dir, self.name)
    self.assertEqual(len(runs), 5)
    self.assertFalse(any(r.get("live") for r in runs))
    self.assertEqual(R.active_index(runs, self.dir, self.name), 0)
    # switching on: the copies of run 0 are removed, nothing is lost
    R.switch_to(self.dir, self.name, runs[2])
    runs = R.scan(self.dir, self.name)
    self.assertEqual(len(runs), 5)
    self.assertEqual(R.active_index(runs, self.dir, self.name), 2)
    self.assertEqual(sorted(os.listdir(runs[0]["folder"])), ["s.gbw", "s.tscb", "s.wfnlog"])
    self.assertFalse(os.path.exists(os.path.join(self.dir, "s.gbw")))

  def test_relabelled_table_is_still_the_run(self):
    """Olex2 rewrites a table it takes up (labels to the current model): the
    run switched to is still known by its logs, and switching away keeps the
    history's original table."""
    runs = R.scan(self.dir, self.name)
    original = open(os.path.join(runs[0]["folder"], "s.tscb"), "rb").read()
    table = R.switch_to(self.dir, self.name, runs[0])
    _table(table, [], b"relabelled, longer than before")
    runs = R.scan(self.dir, self.name)
    self.assertEqual(len(runs), 5)
    self.assertFalse(any(r.get("live") for r in runs))
    self.assertEqual(R.active_index(runs, self.dir, self.name), 0)
    R.switch_to(self.dir, self.name, runs[1])
    runs = R.scan(self.dir, self.name)
    self.assertEqual(len(runs), 5)
    self.assertEqual(open(os.path.join(runs[0]["folder"], "s.tscb"), "rb").read(), original)

  def test_rearchived_copy_shown_once(self):
    """NoSpherA2 archives a switched-to run (relabelled table, new time) into
    a new folder: the same logs, so one chip."""
    runs = R.scan(self.dir, self.name)
    R.switch_to(self.dir, self.name, runs[0])
    dup = os.path.join(R.history_root(self.dir), "s_2026-10-25_07-17-41")
    os.makedirs(dup)
    for f in os.listdir(self.dir):
      if R.belongs(f, "s"):
        shutil.move(os.path.join(self.dir, f), os.path.join(dup, f))
    self.assertEqual(len(R.scan(self.dir, self.name)), 5)


class TestDisorder(Base):
  """Disorder: one wavefunction and log per part, <name>_part<N>.ext."""

  def add_parts(self, d, when, wfn_ext, body):
    t = time.mktime(when.timetuple())
    for p in (1, 2):
      for e, text in ((".wfnlog", PTB_LOG.encode()), (wfn_ext, body)):
        f = os.path.join(d, "%s_part%d%s" % (self.name, p, e))
        with open(f, "wb") as fh:
          fh.write(text)
        os.utime(f, (t, t))

  def setUp(self):
    super(TestDisorder, self).setUp()
    t0 = datetime.datetime(2026, 10, 24, 6, 24, 40)
    d = os.path.join(R.history_root(self.dir), "s_2026-10-24_06-24-40")
    os.makedirs(d)
    _table(os.path.join(d, "s.tscb"), [], b"old")
    self.add_parts(d, t0, ".gbw", b"orca")
    self.live_time = datetime.datetime(2026, 10, 25, 7, 9, 0)
    _table(os.path.join(self.dir, "s.tscb"), [], b"new")
    t = time.mktime(self.live_time.timetuple())
    os.utime(os.path.join(self.dir, "s.tscb"), (t, t))
    self.add_parts(self.dir, self.live_time, ".xtb", b"ptb")

  def test_belongs(self):
    self.assertTrue(R.belongs("s_part2.xtb", "s"))
    self.assertTrue(R.belongs("s.tscb", "s"))
    self.assertFalse(R.belongs("s_partly.xtb", "s"))
    self.assertFalse(R.belongs("s2.tscb", "s"))

  def test_parts_read(self):
    runs = R.scan(self.dir, self.name)
    self.assertEqual([r["parts"] for r in runs], [2, 2])
    self.assertEqual([r["program"] for r in runs], ["pTB", "pTB"])

  def test_switch_moves_part_files(self):
    runs = R.scan(self.dir, self.name)
    R.switch_to(self.dir, self.name, runs[0])
    top = sorted(f for f in os.listdir(self.dir) if R.belongs(f, "s"))
    self.assertEqual(top, ["s.tscb", "s_part1.gbw", "s_part1.wfnlog",
                           "s_part2.gbw", "s_part2.wfnlog"])
    live_dir = os.path.join(R.history_root(self.dir),
                            "s_" + self.live_time.strftime("%Y-%m-%d_%H-%M-%S"))
    self.assertEqual(sorted(os.listdir(live_dir)),
                     ["s.tscb", "s_part1.wfnlog", "s_part1.xtb",
                      "s_part2.wfnlog", "s_part2.xtb"])


if __name__ == "__main__":
  unittest.main()
