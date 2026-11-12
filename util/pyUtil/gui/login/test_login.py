"""gui.login.logic on an in-memory people database with the real schema."""
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logic

SCHEMA = """
CREATE TABLE affiliation (
  id INTEGER NOT NULL, name TEXT, department TEXT, address TEXT, city TEXT,
  postcode TEXT, country TEXT, PRIMARY KEY(id));
CREATE TABLE person (
  id INTEGER NOT NULL, affiliationid INTEGER NOT NULL,
  firstname TEXT, middlename TEXT, lastname TEXT,
  email TEXT, phone TEXT, orchid_id TEXT, add_author integer,
  PRIMARY KEY(id),
  FOREIGN KEY(affiliationid) REFERENCES affiliation(id) ON DELETE CASCADE);
"""


class LoginTest(unittest.TestCase):
  def setUp(self):
    self.conn = sqlite3.connect(':memory:')
    self.conn.executescript(SCHEMA)
    self.conn.execute("INSERT INTO affiliation (id, name) VALUES (1, 'Durham University')")
    for pid, email in ((1, 'Horst@OlexSys.org '), (2, 'twin@x.org'), (3, 'twin@x.org'), (4, '')):
      self.conn.execute("INSERT INTO person (id, affiliationid, lastname, email) VALUES (?, 1, 'P', ?)",
                        (pid, email))
    self.conn.commit()

  def test_found_by_email_ignoring_case_and_spaces(self):
    self.assertEqual(logic.find_user(self.conn, ' horst@olexsys.org'), (1, 'found'))

  def test_missing_duplicate_and_no_email(self):
    self.assertEqual(logic.find_user(self.conn, 'new@x.org'), (None, 'missing'))
    self.assertEqual(logic.find_user(self.conn, 'twin@x.org'), (None, 'duplicate'))
    self.assertEqual(logic.find_user(self.conn, ''), (None, 'no_email'))
    self.assertEqual(logic.find_user(self.conn, None), (None, 'no_email'))

  def test_email_check(self):
    self.assertTrue(logic.valid_email('a.b@uni.ac.uk'))
    for bad in ('', 'a@b', 'ab.c', 'a b@c.org', '@c.org', 'a@.org'):
      self.assertFalse(logic.valid_email(bad), bad)

  def test_add_user_to_an_existing_affiliation(self):
    pid = logic.add_user(self.conn, 'New@X.org', ' Ada ', 'Lovelace', affiliation_id='1')
    row = self.conn.execute("SELECT affiliationid, firstname, lastname, email, add_author"
                            " FROM person WHERE id = ?", (pid,)).fetchone()
    self.assertEqual(row, (1, 'Ada', 'Lovelace', 'new@x.org', 0))
    self.assertEqual(logic.find_user(self.conn, 'new@x.org'), (pid, 'found'))

  def test_a_new_affiliation_is_added_once(self):
    logic.add_user(self.conn, 'a@x.org', 'A', 'B', affiliation_name='Oxford')
    logic.add_user(self.conn, 'c@x.org', 'C', 'D', affiliation_name=' oxford ')
    self.assertEqual(self.conn.execute("SELECT count(*) FROM affiliation WHERE name = 'Oxford'").fetchone()[0], 1)

  def test_a_typed_name_of_a_known_affiliation_is_reused(self):
    pid = logic.add_user(self.conn, 'a@x.org', 'A', 'B', affiliation_name='durham university')
    self.assertEqual(self.conn.execute("SELECT affiliationid FROM person WHERE id = ?", (pid,)).fetchone()[0], 1)

  def test_a_known_email_is_not_added_twice(self):
    self.assertEqual(logic.add_user(self.conn, 'horst@olexsys.org', 'H', 'P', affiliation_id=1), 1)
    self.assertEqual(self.conn.execute("SELECT count(*) FROM person").fetchone()[0], 4)

  def test_refusals_change_nothing(self):
    for kwargs, text in (
        (dict(email='bad', firstname='A', lastname='B', affiliation_id=1), 'valid email'),
        (dict(email='a@x.org', firstname='', lastname='B', affiliation_id=1), 'first and last'),
        (dict(email='a@x.org', firstname='A', lastname='B'), 'institution'),
        (dict(email='twin@x.org', firstname='A', lastname='B', affiliation_id=1), 'Several people')):
      with self.assertRaises(ValueError) as cm:
        logic.add_user(self.conn, **kwargs)
      self.assertIn(text, str(cm.exception))
    self.assertEqual(self.conn.execute("SELECT count(*) FROM person").fetchone()[0], 4)
    self.assertEqual(self.conn.execute("SELECT count(*) FROM affiliation").fetchone()[0], 1)

  def test_people_items_skip_nameless_people(self):
    self.conn.execute("UPDATE person SET firstname = 'Horst', lastname = 'Puschmann' WHERE id = 1")
    self.conn.execute("UPDATE person SET lastname = '' WHERE id = 4")
    items = dict(logic.people_items(self.conn))
    self.assertEqual(items[1], 'Puschmann, Horst - Horst@OlexSys.org')
    self.assertNotIn(4, items)

  def test_person_fields(self):
    self.assertEqual(logic.person_fields(self.conn, 2)['email'], 'twin@x.org')
    self.assertEqual(logic.person_fields(self.conn, '1')['affiliation'], '1')
    self.assertIsNone(logic.person_fields(self.conn, 99))

  def test_claiming_a_listed_person_with_a_new_email(self):
    self.assertEqual(logic.claim_person(self.conn, 1, 'Horst@Gmail.com'), 1)
    self.assertEqual(logic.find_user(self.conn, 'horst@gmail.com'), (1, 'found'))
    self.assertEqual(logic.claim_person(self.conn, '4', 'nobody@x.org'), 4)
    self.assertEqual(logic.find_user(self.conn, 'nobody@x.org'), (4, 'found'))

  def test_claiming_keeps_an_equal_email_as_written(self):
    logic.claim_person(self.conn, 1, 'horst@olexsys.org')
    self.assertEqual(self.conn.execute("SELECT email FROM person WHERE id = 1").fetchone()[0],
                     'Horst@OlexSys.org ')

  def test_claiming_someone_elses_email_is_refused(self):
    for pid, email, text in ((1, 'twin@x.org', 'someone else'), (99, 'a@x.org', 'no longer'),
                             (1, 'bad', 'valid email')):
      with self.assertRaises(ValueError) as cm:
        logic.claim_person(self.conn, pid, email)
      self.assertIn(text, str(cm.exception))
    self.assertEqual(logic.find_user(self.conn, 'horst@olexsys.org'), (1, 'found'))

  def test_operator_and_contact_fill_only_empty_values(self):
    self.assertEqual(logic.operator_changes(7, 'Doe, J.', None, "''"),
                     {'operator': '7', 'contact': 'Doe, J.'})
    self.assertEqual(logic.operator_changes(7, 'Doe, J.', '3', '?'), {'contact': 'Doe, J.'})
    self.assertEqual(logic.operator_changes(7, 'Doe, J.', 'None', 'Roe, R.'), {'operator': '7'})
    self.assertEqual(logic.operator_changes(7, 'Doe, J.', '3', 'Roe, R.'), {})

  def test_no_user_no_changes(self):
    self.assertEqual(logic.operator_changes(None, '', None, ''), {})

  def test_cif_without_model_is_external(self):
    self.assertEqual(logic.external_cif_names(['abc', 'abc_sq'], ['abc.cif', 'abc.fcf']),
                     ['abc', 'abc_sq'])
    self.assertEqual(logic.external_cif_names(['abc', None], ['abc.cif']), ['abc'])

  def test_cif_with_model_is_not_external(self):
    self.assertEqual(logic.external_cif_names(['abc', 'blk'], ['abc.cif', 'ABC.RES']), [])
    self.assertEqual(logic.external_cif_names(['abc', 'blk'], ['abc.cif', 'blk.ins']), [])


if __name__ == '__main__':
  unittest.main()
