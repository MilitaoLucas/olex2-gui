"""
Tests for gui/proto/db.py -- run from util/pyUtil/gui:

    python -m unittest proto.test_db
"""

import os
import shutil
import sqlite3
import tempfile
import unittest

from . import db


def _entry(**kw):
  e = {
      'name': 'test', 'formula': 'C6 H6', 'space_group': 'P21/c',
      'cell_a': 10.0, 'cell_b': 11.0, 'cell_c': 12.0,
      'cell_alpha': 90.0, 'cell_beta': 100.0, 'cell_gamma': 90.0,
      'cell_volume': 1300.0, 'ins': 'TITL test\nCELL 0.71073 10 11 12 90 100 90\nEND\n',
  }
  e.update(kw)
  return e


class DbTest(unittest.TestCase):

  def setUp(self):
    self.tmp = tempfile.mkdtemp()
    self.path = os.path.join(self.tmp, 'gui', 'proto', 'proto.sqlite')

  def tearDown(self):
    shutil.rmtree(self.tmp)

  def test_missing_without_create_is_none(self):
    self.assertIsNone(db.connect(self.path))
    self.assertFalse(os.path.exists(self.path))

  def test_create_makes_folder_and_empty_table(self):
    con = db.connect(self.path, create=True)
    self.assertTrue(os.path.exists(self.path))
    self.assertEqual(db.entries(con), [])
    con.close()

  def test_add_get_remove(self):
    con = db.connect(self.path, create=True)
    i = db.add(con, _entry(comment='first'))
    rows = db.entries(con)
    self.assertEqual(len(rows), 1)
    self.assertEqual(rows[0]['comment'], 'first')
    self.assertIsNotNone(rows[0]['added'])
    self.assertIn('CELL', db.get_model(con, i))
    self.assertTrue(db.remove(con, i))
    self.assertFalse(db.remove(con, i))
    con.close()

  def test_duplicate_found_by_hash(self):
    con = db.connect(self.path, create=True)
    e = _entry()
    i = db.add(con, e)
    # line endings / trailing blanks don't make a different model
    same = e['ins'].replace('\n', '  \r\n')
    self.assertEqual(db.find_by_hash(con, db.model_hash(same))['id'], i)
    con.close()

  def test_volume_prefilter_allows_centring(self):
    con = db.connect(self.path, create=True)
    db.add(con, _entry(name='P', cell_volume=1000.0))
    db.add(con, _entry(name='C', cell_volume=2000.0))   # 2 lattice points
    db.add(con, _entry(name='far', cell_volume=1500.0))
    names = {e['name'] for e in db.entries(con, volume=1000.0, rel_tol=0.05)}
    self.assertEqual(names, {'P', 'C'})
    con.close()

  def test_legacy_schema_is_upgraded(self):
    os.makedirs(os.path.dirname(self.path))
    con = sqlite3.connect(self.path)
    con.execute("""CREATE TABLE proto (id integer PRIMARY KEY, name text NOT NULL,
            formula text NOT NULL, space_group text NOT NULL, cell_a float NOT NULL,
            cell_b float NOT NULL, cell_c float NOT NULL, cell_alpha float NOT NULL,
            cell_beta float NOT NULL, cell_gamma float NOT NULL,
            cell_volume float NOT NULL, class text, ins text NOT NULL)""")
    con.execute("INSERT INTO proto (name, formula, space_group, cell_a, cell_b, cell_c,"
                " cell_alpha, cell_beta, cell_gamma, cell_volume, class, ins)"
                " VALUES ('old','C','P1',1,1,1,90,90,90,1,'x','TITL')")
    con.commit()
    con.close()

    # read-only use works on the old schema...
    con = db.connect(self.path)
    rows = db.entries(con)
    self.assertEqual(rows[0]['name'], 'old')
    self.assertIsNone(rows[0]['red_a'])
    self.assertIsNone(db.find_by_hash(con, 'abc'))
    con.close()

    # ...and opening for writing adds the new columns
    con = db.connect(self.path, create=True)
    db.set_reduced_cell(con, rows[0]['id'], (1, 1, 1, 90, 90, 90))
    self.assertEqual(db.entries(con)[0]['red_a'], 1)
    con.close()


if __name__ == '__main__':
  unittest.main()
