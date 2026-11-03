"""
gui/proto/db.py

SQLite storage for the proto structure library. Pure Python (no Olex2
imports) so it can be tested outside Olex2.

One table, `proto`. The first columns are those of the original AC7 sponge
database, so old databases (e.g. AC7/sponge/sponge.sqlite) can be read as
they are; newer columns are added in place by ensure_schema() when a
database is opened for writing.

    ins       the stored model (a complete SHELX res/ins text)
    red_*     reduced (Niggli, primitive) cell, used for matching; NULL for
              legacy rows -- computed on the fly by the matcher then
"""

from __future__ import annotations

import datetime
import hashlib
import os
import sqlite3

SCHEMA_VERSION = 2

_CREATE = """
CREATE TABLE IF NOT EXISTS proto (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL,
  path        TEXT,
  formula     TEXT NOT NULL,
  space_group TEXT NOT NULL,
  cell_a      REAL NOT NULL,
  cell_b      REAL NOT NULL,
  cell_c      REAL NOT NULL,
  cell_alpha  REAL NOT NULL,
  cell_beta   REAL NOT NULL,
  cell_gamma  REAL NOT NULL,
  cell_volume REAL NOT NULL,
  class       TEXT,
  ins         TEXT NOT NULL,
  comment     TEXT,
  red_a       REAL,
  red_b       REAL,
  red_c       REAL,
  red_alpha   REAL,
  red_beta    REAL,
  red_gamma   REAL,
  r1          REAL,
  added       TEXT,
  hash        TEXT
)"""

# Columns added after the original AC7 schema: name -> SQL type
_ADDED_COLUMNS = {
    'path': 'TEXT', 'comment': 'TEXT',
    'red_a': 'REAL', 'red_b': 'REAL', 'red_c': 'REAL',
    'red_alpha': 'REAL', 'red_beta': 'REAL', 'red_gamma': 'REAL',
    'r1': 'REAL', 'added': 'TEXT', 'hash': 'TEXT',
}

CELL_KEYS = ('cell_a', 'cell_b', 'cell_c', 'cell_alpha', 'cell_beta', 'cell_gamma')
RED_KEYS = ('red_a', 'red_b', 'red_c', 'red_alpha', 'red_beta', 'red_gamma')


def model_hash(text: str) -> str:
  """Hash of the model text, ignoring line endings and trailing blanks."""
  norm = '\n'.join(line.rstrip() for line in text.strip().splitlines())
  return hashlib.sha1(norm.encode('utf-8')).hexdigest()


def connect(path: str, create: bool = False):
  """
  Open the database at `path`. With create=True the folder, file and
  table are created and the schema brought up to date; otherwise a
  missing file gives None.
  """
  if not create and not os.path.exists(path):
    return None
  if create:
    folder = os.path.dirname(path)
    if folder:
      os.makedirs(folder, exist_ok=True)
  con = sqlite3.connect(path)
  con.row_factory = sqlite3.Row
  if create:
    ensure_schema(con)
  return con


def ensure_schema(con) -> None:
  """Create the table, or add columns missing from an older database."""
  con.execute(_CREATE)
  have = {row[1] for row in con.execute("PRAGMA table_info(proto)")}
  for col, typ in _ADDED_COLUMNS.items():
    if col not in have:
      con.execute(f"ALTER TABLE proto ADD COLUMN {col} {typ}")
  con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
  con.commit()


def find_by_hash(con, h: str):
  have = {row[1] for row in con.execute("PRAGMA table_info(proto)")}
  if 'hash' not in have:
    return None
  return con.execute("SELECT id, name FROM proto WHERE hash = ?", (h,)).fetchone()


def add(con, entry: dict) -> int:
  """
  Insert one structure. `entry` needs name, formula, space_group, the six
  cell_* values, cell_volume and ins; everything else is optional.
  `hash` and `added` are filled in when absent. Returns the new id.
  """
  e = dict(entry)
  e.setdefault('hash', model_hash(e['ins']))
  e.setdefault('added', datetime.datetime.now().isoformat(timespec='seconds'))
  cols = [c for c in e if c != 'id']
  sql = "INSERT INTO proto (%s) VALUES (%s)" % (
      ', '.join(cols), ', '.join('?' * len(cols)))
  cur = con.execute(sql, [e[c] for c in cols])
  con.commit()
  return cur.lastrowid


def remove(con, entry_id: int) -> bool:
  cur = con.execute("DELETE FROM proto WHERE id = ?", (int(entry_id),))
  con.commit()
  return cur.rowcount > 0


def set_reduced_cell(con, entry_id: int, red) -> None:
  """Store a reduced cell computed for a (legacy) row."""
  con.execute(
      "UPDATE proto SET %s WHERE id = ?" % ', '.join(f"{k} = ?" for k in RED_KEYS),
      list(red) + [int(entry_id)])
  con.commit()


def entries(con, volume: float = None, rel_tol: float = None, with_model: bool = False):
  """
  Return rows as dicts. With `volume` and `rel_tol`, only rows whose
  reduced-cell volume could match (|V - v| <= rel_tol * v) are returned;
  this is a cheap pre-filter -- the real comparison is done in cells.py.
  Volumes of primitive and centred cells differ, so callers pass the
  volume per lattice point when comparing reduced cells; rows are
  filtered on their stored full-cell volume divided by every possible
  centring multiplicity (1, 2, 3, 4) to stay conservative.
  """
  have = {row[1] for row in con.execute("PRAGMA table_info(proto)")}
  cols = [c for c in ('id', 'name', 'path', 'formula', 'space_group') + CELL_KEYS +
          ('cell_volume', 'class', 'comment') + RED_KEYS + ('r1', 'added')
          if c in have]
  if with_model:
    cols.append('ins')
  sql = "SELECT %s FROM proto" % ', '.join(cols)
  out = []
  for row in con.execute(sql):
    d = {c: row[c] for c in cols}
    for c in ('comment', 'r1', 'added', 'path') + RED_KEYS:
      d.setdefault(c, None)
    if volume is not None and rel_tol is not None:
      v = d['cell_volume']
      if not any(abs(v / m - volume) <= rel_tol * volume for m in (1, 2, 3, 4)):
        continue
    out.append(d)
  return out


def get_model(con, entry_id: int):
  row = con.execute("SELECT ins FROM proto WHERE id = ?", (int(entry_id),)).fetchone()
  return row['ins'] if row else None
