"""
gui/help/help_index.py

Builds and reads the help index: help ID -> HTML, compiled from help
markdown files. Plain Python (no Olex2 imports), so the release script
can build the index too:

    python util/pyUtil/gui/help/help_index.py <Olex2 BaseDir>
    python util/pyUtil/gui/help/help_index.py <Olex2 BaseDir> --check
        (list the 'i' buttons in the GUI files that have no help)

Help files
----------
Only files named  *.help.md  are help. They live anywhere under
util/pyUtil -- next to the code they describe (e.g.
gui/moiety/moiety.help.md) or in the central gui/help/gui/EN tree. READMEs
and other notes are plain .md files and never become help.

Each top-level heading starts one help entry; its ID is the heading in
upper case with spaces as underscores ("# Moiety" -> MOIETY, which the
'i' button of tool h3-moiety looks up). Images are referenced relative to
the help file (![0.5 caption](images/x.png): optional leading number = width
as a fraction of the help box) and should sit next to it.

An entry whose heading ends in "-target" (e.g. "# start-target") is raw
text, not markdown -- kept from the original format. Text before the first
heading (YAML front matter, [comment]: <...> lines) is ignored.

Index
-----
help_index.json next to this file:
    {"version": 1,
     "entries": {ID: {"html": ..., "src": path relative to BaseDir}},
     "files": {path relative to BaseDir: mtime}}
Image tags are stored as markers {{HELPIMG|src|width_fraction|alt}} with
src relative to BaseDir; they are turned into HTML when shown (the width
depends on the window), see gui.help.
"""

import json
import os
import re
import sys

HELP_SUFFIX = '.help.md'

# Help files from before the *.help.md convention (relative to util/pyUtil),
# mostly in modules / plugins maintained elsewhere. They are compiled like
# *.help.md; remove an entry once its file has been renamed.
LEGACY_HELP_FILES = (
  'AC7/AC.md',
  'AC7d/AC.md',
  'ACED/ACED.md',
  'ACEDd/ACED.md',
  'ACED7d/ACED.md',
  'FragmentDB/fragmentdb.md',
  'NoSpherA2/NoSpherA2.md',
  'NoSpherA2/harp.md',
  'PluginLib/plugin-DrawPlus/drawplus.md',
  'PluginLib/plugin-SISYPHOS/sisyphos.md',
)
INDEX_NAME = 'help_index.json'
INDEX_VERSION = 1
SKIP_DIRS = {'.git', '.svn', '__pycache__'}

_here = os.path.dirname(os.path.abspath(__file__))


def _markdown2():
  try:
    from . import markdown2
  except ImportError:          # run as a script
    if _here not in sys.path:
      sys.path.insert(0, _here)
    import markdown2
  return markdown2


def legacy_help_files(base_dir, under=None):
  """The LEGACY_HELP_FILES that exist (only those below `under` if given)."""
  root = os.path.join(base_dir, 'util', 'pyUtil')
  out = []
  for rel in LEGACY_HELP_FILES:
    p = os.path.normpath(os.path.join(root, rel))
    if os.path.isfile(p) and (under is None or
        os.path.normcase(p).startswith(os.path.normcase(os.path.normpath(under)) + os.sep)):
      out.append(p)
  return out


def find_help_files(root, all_md=False):
  """Help files under root (*.help.md; every *.md with all_md=True)."""
  out = []
  for folder, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('_')]
    for f in files:
      if f.endswith(HELP_SUFFIX) or (all_md and f.endswith('.md')):
        out.append(os.path.join(folder, f))
  return sorted(out)


def help_id(heading):
  return heading.strip().lstrip('#').strip().replace(' ', '_').upper()


_IMG = re.compile(r'<img[^>]*\bsrc="([^"]+)"[^>]*\balt="([^"]*)"[^>]*>')


def _image_markers(html, md_dir, base_dir):
  """<img> -> {{HELPIMG|src rel. to base_dir|width fraction|alt}}."""
  def repl(m):
    src, alt = m.group(1), m.group(2)
    width = 1.0
    first = alt.split(' ', 1)
    if len(first) == 2:
      try:
        width = float(first[0])
        alt = first[1]
      except ValueError:
        pass
    path = os.path.normpath(os.path.join(md_dir, src))
    rel = os.path.relpath(path, base_dir).replace(os.sep, '/')
    return '{{HELPIMG|%s|%s|%s}}' % (rel, width, alt.replace('|', ' '))
  return _IMG.sub(repl, html)


def parse_help_file(path, base_dir):
  """[(ID, html)] for one help file."""
  md = _markdown2()
  with open(path, encoding='utf8', errors='ignore') as f:
    text = f.read()
  md_dir = os.path.dirname(path)
  # protect sub-headings, then split on top-level headings
  text = text.replace('####', '@@@@').replace('###', '@@@').replace('##', '@@')
  out = []
  # chunk 0 is whatever precedes the first heading (YAML front matter,
  # [comment] lines, ...): a preamble, never a help entry
  for item in ('\n' + text).split('\n#')[1:]:
    item = item.strip()
    if not item:
      continue
    lines = item.split('\n')
    hid = help_id(lines[0])
    if not hid:
      continue
    body = '\n'.join(lines[1:])
    if '-target\n' in item:
      html = item.split('-target\n', 1)[1].strip()
    else:
      body = body.replace('@@@@', '####').replace('@@@', '###').replace('@@', '##').replace('|', '||')
      html = md.markdown(body, extras=['wiki-tables', 'fenced-code-blocks'])
      html = _image_markers(html, md_dir, base_dir)
      html = html.replace('\\$', '$').replace('$', '\\$').replace('\\$spy', '$spy')
    html = html.strip().replace('<p>', '').replace('</p>', '')
    html = html.replace('<table><tbody><tr><td>',
                        "<table width='100%%'><tbody><tr><td width='25%%'>")
    out.append((hid, html))
  return out


def build(paths, base_dir, entries=None, files=None):
  """
  Add the help in `paths` to entries/files (new dicts if None).
  Returns (entries, files, duplicates): duplicates lists
  (ID, earlier src, later src) -- the later one wins.
  """
  entries = {} if entries is None else entries
  files = {} if files is None else files
  duplicates = []
  for path in paths:
    rel = os.path.relpath(path, base_dir).replace(os.sep, '/')
    # entries from an earlier version of this file are replaced
    for hid in [k for k, v in entries.items() if v['src'] == rel]:
      del entries[hid]
    for hid, html in parse_help_file(path, base_dir):
      if hid in entries and entries[hid]['src'] != rel:
        duplicates.append((hid, entries[hid]['src'], rel))
      entries[hid] = {'html': html, 'src': rel}
    files[rel] = os.path.getmtime(path)
  return entries, files, duplicates


def build_index(base_dir):
  """Index of all *.help.md under util/pyUtil of an Olex2 BaseDir."""
  root = os.path.join(base_dir, 'util', 'pyUtil')
  paths = find_help_files(root) + legacy_help_files(base_dir)
  entries, files, dups = build(paths, base_dir)
  return {'version': INDEX_VERSION, 'entries': entries, 'files': files}, dups


def write_index(index, path):
  tmp = path + '.tmp'
  with open(tmp, 'w', encoding='utf8') as f:
    json.dump(index, f, indent=0, sort_keys=True, ensure_ascii=False)
  os.replace(tmp, path)


def read_index(path):
  """The index at path, or None if missing / another version."""
  try:
    with open(path, encoding='utf8') as f:
      index = json.load(f)
  except (OSError, ValueError):
    return None
  if index.get('version') != INDEX_VERSION:
    return None
  return index


# ---------------------------------------------------------------------------
# Which 'i' buttons have no help?
# ---------------------------------------------------------------------------

_BUTTON_EXT = re.compile(r'help_ext=([^;>]+?)\s*;([^>]*)')
_BUTTON_H3 = re.compile(r'tool-h3[^;]*;image=(h3-[^;#]+);([^>]*)')
_TAB_PREFIXES = ('work-', 'view-', 'info-', 'tools-', 'aio-', 'home-')


def lookup_ids(name, scope=None):
  """The IDs the help box tries for a button name (as gui.help does)."""
  for pre in _TAB_PREFIXES:
    if name.startswith(pre):
      name = name[len(pre):]
      break
  hid = name.replace('h3-', '').upper().replace('-', '_').replace(' ', '_')
  hid = re.sub(r'_?%\(N\)S$', '_1', hid)      # numbered rows made at run time
  out = ['%s_%s' % (scope.upper(), hid)] if scope else []
  out.append(hid)
  m = re.match(r'^(.*)_\d+$', hid)
  if m:
    out.append(m.group(1))
  return out


def check_buttons(base_dir, entries):
  """{gui file: [IDs]} of 'i' buttons in etc/gui and util/pyUtil without help."""
  missing = {}
  for root in (os.path.join(base_dir, 'etc', 'gui'), os.path.join(base_dir, 'util', 'pyUtil')):
    for folder, dirs, files in os.walk(root):
      dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('_')]
      for f in files:
        if not f.endswith(('.htm', '.html')):
          continue
        path = os.path.join(folder, f)
        with open(path, encoding='utf8', errors='ignore') as fh:
          text = fh.read()
        for m in list(_BUTTON_EXT.finditer(text)) + list(_BUTTON_H3.finditer(text)):
          name = m.group(1).strip().strip("'\"")
          if name.startswith('#'):
            continue
          scope = re.search(r'scope=(\w+)', m.group(2).split('-->')[0])
          ids = lookup_ids(name, scope.group(1) if scope else None)
          if not any(i in entries for i in ids):
            rel = os.path.relpath(path, base_dir)
            if ids[0] not in missing.setdefault(rel, []):
              missing[rel].append(ids[0])
  return missing


def main(argv):
  check = '--check' in argv
  argv = [a for a in argv if a != '--check']
  if len(argv) != 1:
    print(__doc__)
    return 1
  base_dir = os.path.abspath(argv[0])
  index, dups = build_index(base_dir)
  if check:
    missing = check_buttons(base_dir, index['entries'])
    print("'i' buttons without help: %i" % sum(len(v) for v in missing.values()))
    for rel in sorted(missing):
      print("  %s: %s" % (rel, ', '.join(missing[rel])))
    return 0
  out = os.path.join(base_dir, 'util', 'pyUtil', 'gui', 'help', INDEX_NAME)
  write_index(index, out)
  print("help index: %i entries from %i files -> %s" % (
    len(index['entries']), len(index['files']), out))
  for hid, a, b in dups:
    print("  duplicate help ID %s: %s overridden by %s" % (hid, a, b))
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
