"""
gui/moiety/user_db.py

Persistent table of fragment charges supplied by the user in the moiety
tab. Used as an extra lookup by infer_charges() (confidence 'user_lookup'),
so ligands/counter-ions a chemist has assigned once are recognised again.

Stored as CSV (formula,charge) in  DataDir()/gui/moiety/user_charges.csv,
keyed by MoietyFragment.formula_string, e.g.  "C2 H6 N,1".

Single-element fragments are never stored: a metal's oxidation state is
specific to one structure, not a property of the element.
"""

from __future__ import annotations

import csv
import os

_FILE_NAME = 'user_charges.csv'

_cache = None        # {formula: charge}
_cache_mtime = None  # mtime of the file when _cache was read


def _path():
    """Full path of the user charge table, or None outside Olex2."""
    try:
        from olexFunctions import OV
    except ImportError:
        return None
    return os.path.join(OV.DataDir(), 'gui', 'moiety', _FILE_NAME)


def is_storable(formula: str) -> bool:
    """Only multi-element fragments go into the table (see module doc)."""
    return len(formula.split()) > 1


def load() -> dict:
    """Return {formula: charge}; empty if the file doesn't exist yet."""
    global _cache, _cache_mtime
    path = _path()
    if not path or not os.path.exists(path):
        return {}
    mtime = os.path.getmtime(path)
    if _cache is not None and mtime == _cache_mtime:
        return dict(_cache)
    table = {}
    try:
        with open(path, newline='', encoding='utf-8') as fh:
            for row in csv.reader(fh):
                if len(row) < 2 or not row[0].strip() or row[0].startswith('#'):
                    continue
                try:
                    table[row[0].strip()] = int(row[1])
                except ValueError:
                    print(f"[moiety] Ignoring bad line in {path}: {row}")
    except OSError as e:
        print(f"[moiety] Could not read user charges from {path}: {e}")
        return {}
    _cache, _cache_mtime = table, mtime
    return dict(table)


def _save(table: dict) -> None:
    global _cache, _cache_mtime
    path = _path()
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', newline='', encoding='utf-8') as fh:
            fh.write('# Moiety charges supplied by the user in Olex2: formula,charge\n')
            writer = csv.writer(fh)
            for formula in sorted(table):
                writer.writerow([formula, table[formula]])
    except OSError as e:
        print(f"[moiety] Could not save user charges to {path}: {e}")
        return
    _cache, _cache_mtime = dict(table), os.path.getmtime(path)


def store(formula: str, charge: int) -> None:
    """Remember `charge` for `formula` (ignored for single elements)."""
    if not is_storable(formula):
        return
    table = load()
    if table.get(formula) != charge:
        table[formula] = charge
        _save(table)


def forget(formula: str) -> None:
    """Remove `formula` from the table, if present."""
    table = load()
    if table.pop(formula, None) is not None:
        _save(table)
