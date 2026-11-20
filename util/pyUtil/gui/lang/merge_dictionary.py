"""Merge a translation table (English<TAB>translation) into Olex2's dictionary.txt.

  python merge_dictionary.py [table.tsv] [Language] [dictionary.txt]

Defaults: de_core.tsv, German, <Olex2 root>/dictionary.txt.
- a key already in the dictionary (OlexID or English column, ignoring case)
  gets the translation only where its cell is '.' or empty; a different
  existing translation is kept and listed as a conflict;
- new keys are appended as rows OlexID = English = key, '.' elsewhere.
Only the touched lines change; the rest of the file (BOM, multi-line rows)
is kept as it is.  The previous file is saved as dictionary.txt.bak; the
file before the first merge stays in dictionary.txt.orig (never overwritten).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import key_of  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))


def read_table(path):
  pairs = []
  with open(path, encoding='utf-8') as f:
    for line in f:
      line = line.rstrip('\r\n')
      if not line or line.startswith('#') or '\t' not in line:
        continue
      en, tr = line.split('\t', 1)
      if en.strip() and tr.strip():  # identical pairs only override existing rows
        pairs.append((en.strip(), tr.strip()))
  return pairs


def merge(table_path, language, dict_path, overwrite=False):
  with open(dict_path, 'rb') as f:
    raw = f.read()
  bom = raw.startswith(b'\xef\xbb\xbf')
  text = raw[3:].decode('utf-8') if bom else raw.decode('utf-8')
  nl = '\r\n' if '\r\n' in text else '\n'
  lines = text.split(nl)
  header = lines[0].split('\t')
  col = header.index(language)
  width = len(header)
  index = {}
  for i, line in enumerate(lines[2:], 2):
    f = line.split('\t')
    if len(f) > col:
      for k in {key_of(f[1]), key_of(f[0])}:
        index.setdefault(k, []).append(i)
  filled, added, kept, conflicts = 0, 0, 0, []
  new_rows = []
  for en, tr in read_table(table_path):
    k = key_of(en)
    rows = index.get(k)
    # every row whose OlexID or English text is the key (e.g. 'Chemical Tools'
    # and 'chemical-tools' with English 'Chemical Tools')
    for i in rows or ():
      f = lines[i].split('	')
      cell = f[col].strip()
      if cell in ('', '.'):
        f[col] = tr
        lines[i] = '	'.join(f)
        filled += 1
      elif key_of(cell) == key_of(tr):
        kept += 1
      else:
        conflicts.append((en, cell, tr))
        if overwrite:
          f[col] = tr
          lines[i] = '	'.join(f)
    if rows is None and key_of(en) != key_of(tr):
      row = ['.'] * width
      row[0] = row[1] = en
      row[col] = tr
      new_rows.append('	'.join(row))
      index[k] = []
      added += 1
  while lines and lines[-1] == '':
    lines.pop()
  lines.extend(new_rows)
  out = nl.join(lines) + nl
  if not os.path.exists(dict_path + '.orig'):   # the state before any merge, kept
    shutil.copy2(dict_path, dict_path + '.orig')
  shutil.copy2(dict_path, dict_path + '.bak')
  with open(dict_path, 'wb') as f:
    f.write((b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8'))
  print('%s: %d filled, %d added, %d already the same, %d conflicts (%s)'
        % (language, filled, added, kept, len(conflicts),
           'replaced by the table' if overwrite else 'kept the existing text'))
  for en, cell, tr in conflicts:
    print('  %s\n    dictionary: %s\n    table:      %s' % (en, cell, tr))


if __name__ == '__main__':
  a = [x for x in sys.argv[1:] if x != '--overwrite']
  merge(a[0] if a else os.path.join(HERE, 'de_core.tsv'),
        a[1] if len(a) > 1 else 'German',
        a[2] if len(a) > 2 else os.path.join(ROOT, 'dictionary.txt'),
        overwrite='--overwrite' in sys.argv)
