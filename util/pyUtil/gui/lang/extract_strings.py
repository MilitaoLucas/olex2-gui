"""Collect the translatable strings of the Olex2 GUI from the html sources.

Run outside Olex2:  python extract_strings.py [olex2_root] [out.tsv]

Scans etc/gui and the html/template files under util/pyUtil (*.htm, *.html,
gui template files with t:name{...} blocks).  What a whole-text-node
dictionary lookup would see:

  text    text between tags
  hint/title/alt/label   those attributes
  button  value= of <input type="button">

$func(...) calls, <!-- comments --> (incl. #include lines), <script>/<style>
are removed; %...% translation markers are unwrapped.  A string that still
contains a placeholder ($call, %(x)s, #word) is 'mixed': it cannot match a
dictionary key at runtime as it stands.

Output TSV: kind, mixed(0/1), file count, first file, string
"""
import os
import re
import sys
from html.parser import HTMLParser

SKIP_DIRS = {'__pycache__', 'regression', '.svn', '.hg', '.git'}
EXTS = ('.htm', '.html')
WORD = re.compile('[A-Za-z]{2}')
PLACEHOLDER = re.compile(r'\x00|%\([A-Za-z_]\w*\)[sdrf]|#[A-Za-z_]\w*')
CALL = re.compile(r'\$[A-Za-z_][\w.]*\(')
SNIPPET_ARG = re.compile(r'"(value|hint|label|title)=([^"]*)"', re.I)


def strip_calls(s):
  """Replace $name(...) (balanced parens, quotes respected) with \\x00."""
  out = []
  i = 0
  while True:
    m = CALL.search(s, i)
    if not m:
      out.append(s[i:])
      return ''.join(out)
    out.append(s[i:m.start()])
    j = m.end()
    depth = 1
    quote = None
    while j < len(s) and depth:
      c = s[j]
      if quote:
        if c == quote:
          quote = None
      elif c in '\'"':
        quote = c
      elif c == '(':
        depth += 1
      elif c == ')':
        depth -= 1
      j += 1
    out.append('\x00')
    i = j


def norm(s):
  s = s.replace('%%', '%')
  s = re.sub(r'%([A-Za-z][^%<>"\n]{0,60})%', r'\1', s)  # %Phrase% -> Phrase
  return ' '.join(s.replace('\xa0', ' ').split())


class Collect(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self, convert_charrefs=True)
    self.skip = 0
    self.found = []  # (kind, string)

  def handle_starttag(self, tag, attrs):
    if tag in ('script', 'style'):
      self.skip += 1
    a = dict((k, v) for k, v in attrs if v)
    for k in ('hint', 'title', 'alt', 'label'):
      if k in a:
        self.found.append((k, a[k]))
    if tag == 'input' and a.get('type', '').lower() == 'button' and 'value' in a:
      self.found.append(('button', a['value']))

  handle_startendtag = handle_starttag

  def handle_endtag(self, tag):
    if tag in ('script', 'style') and self.skip:
      self.skip -= 1

  def handle_data(self, data):
    if not self.skip:
      self.found.append(('text', data))


def chunks(path, txt):
  """The html pieces of a file: t:name{...} blocks that contain a tag, or the whole file."""
  if re.search(r'^\s*t:[\w-]+\s*\{', txt, re.M):
    for m in re.finditer(r'^\s*t:([\w-]+)\s*\{(.*?)^\s*\}', txt, re.M | re.S):
      if '<' in m.group(2):
        yield m.group(2)
  else:
    yield txt


def scan_file(path):
  with open(path, 'rb') as f:
    raw = f.read()
  try:
    txt = raw.decode('utf-8')
  except UnicodeDecodeError:
    txt = raw.decode('latin-1')
  res = []
  for chunk in chunks(path, txt):
    # html.Snippet("...", "value=Label", "hint=Tooltip", ...): literal label/hint arguments
    for m in SNIPPET_ARG.finditer(chunk):
      k, v = m.group(1).lower(), m.group(2).strip()
      if len(v) > 1 and v[0] == v[-1] and v[0] in '\'"':
        v = v[1:-1]
      if '(' in v or v.startswith(('spy.', 'GetVar', '$', '#')) or not WORD.search(v):
        continue
      res.append(('snippet-' + k, norm(v)))
    # header/tab images: label = image name with '-' -> ' ' (PilTools.translate_label)
    for m in re.finditer(r'#include(?:if)?\b[^\n]*?\bimage=([^;#$\s]+)', chunk):
      v = re.sub(r'^h[123]-', '', m.group(1)).replace('-', ' ').replace('_', ' ').strip()
      if WORD.search(v):
        res.append(('image', v))
    chunk = re.sub(r'\$\+.*?\$-', ' ', chunk, flags=re.S)       # $+ macro block $-
    chunk = re.sub(r'<!--\s*#(include|includeif|ignoreif)\b[^\n]*', ' ', chunk)
    chunk = re.sub(r'#ignoreif\s*-->', ' ', chunk)
    chunk = re.sub(r'<!--.*?-->', ' ', chunk, flags=re.S)
    chunk = strip_calls(chunk)
    p = Collect()
    try:
      p.feed(chunk)
      p.close()
    except Exception as err:
      print('parse error %s: %s' % (path, err), file=sys.stderr)
    for kind, s in p.found:
      s = norm(s)
      if not WORD.search(PLACEHOLDER.sub('', s)):
        continue
      res.append((kind, s))
  return res


def is_template_file(path):
  # TemplateProvider files: any extension, t:name{ blocks
  try:
    with open(path, 'rb') as f:
      head = f.read(4096)
  except OSError:
    return False
  return re.search(rb'^\s*t:[\w-]+\s*\{', head, re.M) is not None


def files(root):
  for top in ('etc/gui', 'util/pyUtil'):
    for d, dirs, names in os.walk(os.path.join(root, top)):
      dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
      for n in names:
        p = os.path.join(d, n)
        low = n.lower()
        if low.endswith(EXTS) or (low.endswith('.txt') and 'templates' in d.replace('\\', '/')
                                  and is_template_file(p)):
          yield p


def main():
  root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                         os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
  out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), 'catalogue_en.tsv')
  seen = {}  # (kind, s) -> [files]
  nfiles = 0
  for p in files(root):
    nfiles += 1
    rel = os.path.relpath(p, root).replace('\\', '/')
    for kind, s in scan_file(p):
      lst = seen.setdefault((kind, s), [])
      if rel not in lst:
        lst.append(rel)
  rows = []
  for (kind, s), fl in seen.items():
    mixed = 1 if PLACEHOLDER.search(s) else 0
    rows.append((kind, mixed, len(fl), fl[0], s.replace('\x00', '$()')))
  rows.sort(key=lambda r: (r[1], r[4].lower(), r[0]))
  with open(out, 'w', encoding='utf-8') as f:
    f.write('kind\tmixed\tfiles\tfirst_file\tstring\n')
    for r in rows:
      f.write('%s\t%d\t%d\t%s\t%s\n' % r)
  plain = set(r[4] for r in rows if not r[1])
  kinds = {}
  for r in rows:
    kinds[r[0]] = kinds.get(r[0], 0) + 1
  print('%d files scanned, %d rows (%s), %d distinct plain strings, %d mixed -> %s' % (
    nfiles, len(rows), ', '.join('%s %d' % kv for kv in sorted(kinds.items())),
    len(plain), sum(r[1] for r in rows), out))


if __name__ == '__main__':
  main()
