"""Whole-text translation of Olex2 GUI html, no Olex2 imports (testable outside).

The rule: a piece of visible text is translated only when the WHOLE piece
(text between two tags, or a whole hint/title/alt/label attribute, or the
value of a button, or a literal value=/hint=/label=/title= argument of
html.Snippet) is a dictionary key.  Everything else - tags, comments and
#include lines, $func(...) calls, $+ ... $- macro blocks, scripts - is copied
byte for byte.  Keys match without regard to case and entities; an ALL-CAPS
original gets an ALL-CAPS translation.
"""
import html
import re

CALL = re.compile(r'\$[A-Za-z_][\w.]*\(')
WORD = re.compile('[A-Za-z]{2}')
ENTITY = re.compile(r'&#?\w+;')
TAG_START = re.compile(r'<[A-Za-z/!]')
ATTR = re.compile(r'''(\s)(hint|title|alt|label|value)(\s*=\s*)("([^"]*)"|'([^']*)')''', re.I)
SNIPPET_ARG = re.compile(r'"(value|hint|label|title)=([^"]*)"', re.I)
MARKER = re.compile(r'%([A-Za-z][^%<>"\n]{0,60})%')


def key_of(s):
  """The lookup form of a string: entities decoded, whitespace collapsed, lower case."""
  return ' '.join(html.unescape(s).replace('\xa0', ' ').split()).lower()


def load_dictionary(path, language):
  """{key_of(text): translation} from Olex2's dictionary.txt for one language
  column.  Both the OlexID and the English column are keys (OlexID wins);
  '.' or empty cells and rows spread over several lines are skipped."""
  with open(path, encoding='utf-8-sig') as f:
    lines = f.read().splitlines()
  if not lines:
    return {}
  header = lines[0].split('\t')
  if language not in header:
    raise KeyError('no %r column in %s' % (language, path))
  col = header.index(language)
  table = {}
  for line in lines[2:]:
    f = line.split('\t')
    if len(f) <= col:
      continue
    tr = f[col].strip()
    if tr in ('', '.'):
      continue
    for k in (f[1], f[0]):   # OlexID last, so it wins
      k = key_of(k)
      if k and WORD.search(k) and k != key_of(tr):
        table[k] = tr
  return table


def _ascii(s):
  # translations are html already (may hold &pi; etc.); only non-ASCII becomes &#NNN;
  return s.encode('ascii', 'xmlcharrefreplace').decode('ascii')


def _upper(s):
  return ''.join(p if ENTITY.fullmatch(p) else p.upper() for p in re.split(r'(&#?\w+;)', s))


def lookup(text, table):
  """The translation of one whole string, or None."""
  core = text.strip()
  # stray directives, markers (<--ANCHOR-->) and unexpanded calls ($spy.#name...) are never text
  if not core or not WORD.search(core) or '#include' in core or '<' in core \
     or re.search(r'\$[A-Za-z_]', core):
    return None
  tr = table.get(key_of(core))
  if tr is None and '%' in core:
    # '%Contact% %Author%', 'CCDC %Number%': the whole label first; else Olex2
    # still translates the %...% pieces one by one
    plain = MARKER.sub(r'\1', core)
    if plain != core:
      tr = table.get(key_of(plain))
  if tr is None:
    return None
  if core.isupper():
    tr = _upper(tr)
  return _ascii(tr)


def _replace_text(run, table):
  tr = lookup(run, table)
  if tr is None:
    return run, 0
  lead = run[:len(run) - len(run.lstrip())]
  trail = run[len(run.rstrip()):]
  return lead + tr + trail, 1


def _end_of_call(s, i):
  """s[i] starts '$name(': index just past the matching ')' (quotes respected)."""
  j = s.index('(', i) + 1
  depth, quote = 1, None
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
  return j


def _end_of_tag(s, i):
  """s[i] == '<': index just past the closing '>' (quotes and $calls respected)."""
  j = i + 1
  quote = None
  while j < len(s):
    c = s[j]
    if quote:
      if c == quote:
        quote = None
    elif c in '\'"':
      quote = c
    elif c == '$' and CALL.match(s, j):
      j = _end_of_call(s, j)
      continue
    elif c == '>':
      return j + 1
    j += 1
  return len(s)


def _translate_tag(tag, table):
  is_button = re.match(r'<input\b', tag, re.I) and re.search(r'''type\s*=\s*["']?button''', tag, re.I)
  n = [0]

  def attr(m):
    name = m.group(2).lower()
    if name == 'value' and not is_button:
      return m.group(0)
    val = m.group(5) if m.group(5) is not None else m.group(6)
    tr = lookup(val, table)
    if tr is None or tr == val.strip():
      return m.group(0)
    q ='"' if m.group(5) is not None else "'"
    tr = tr.replace(q, '&quot;' if q == '"' else '&#39;')
    n[0] += 1
    return '%s%s%s%s%s%s' % (m.group(1), m.group(2), m.group(3), q, tr, q)

  return ATTR.sub(attr, tag), n[0]


def _translate_snippet_args(block, table):
  n = [0]

  def arg(m):
    v = m.group(2)
    inner, q = v, ''
    if len(v) > 1 and v[0] == v[-1] and v[0] == "'":
      inner, q = v[1:-1], "'"
    if '(' in inner or inner.startswith(('spy.', 'GetVar', '$', '#')):
      return m.group(0)
    tr = lookup(inner, table)
    if tr is None or tr == inner.strip():
      return m.group(0)
    # quotes would end the argument; the sources have plain commas in hints.
    # A value holding an entity goes in single quotes, as the sources do
    # ("value='&mu; Plot'")
    tr = ''.join(p if ENTITY.fullmatch(p) else
                 p.replace('"', '&quot;').replace("'", '&#39;').replace(';', '&#59;')
                 for p in re.split(r'(&#?\w+;)', tr))
    if ';' in tr:
      q = "'"
    n[0] += 1
    return '"%s=%s%s%s"' % (m.group(1), q, tr, q)

  return SNIPPET_ARG.sub(arg, block), n[0]


def translate_html(src, table):
  """(translated text, number of replacements).  With no replacements the
  result is src itself."""
  if not table:
    return src, 0
  out = []
  count = 0
  text_start = 0
  i = 0
  n = len(src)

  def flush(upto):
    nonlocal count
    if upto > text_start:
      t, c = _replace_text(src[text_start:upto], table)
      out.append(t)
      count += c

  while i < n:
    c = src[i]
    if c == '<':
      if src.startswith('<!--', i):
        end = src.find('-->', i + 4)
        end = n if end < 0 else end + 3
        flush(i)
        out.append(src[i:end])
      elif TAG_START.match(src, i):
        end = _end_of_tag(src, i)
        flush(i)
        tag = src[i:end]
        name = re.match(r'<\s*([A-Za-z]+)', tag)
        name = name.group(1).lower() if name else ''
        if name in ('script', 'style'):
          close = re.compile(r'</\s*%s\s*>' % name, re.I).search(src, end)
          end = n if not close else close.end()
          out.append(src[i:end])
        else:
          t, k = _translate_tag(tag, table)
          out.append(t)
          count += k
      else:
        i += 1
        continue
      i = text_start = end
    elif c == '$':
      if src.startswith('$+', i):
        end = src.find('$-', i + 2)
        end = n if end < 0 else end + 2
        flush(i)
        t, k = _translate_snippet_args(src[i:end], table)
        out.append(t)
        count += k
        i = text_start = end
      elif CALL.match(src, i):
        end = _end_of_call(src, i)
        flush(i)
        out.append(src[i:end])
        i = text_start = end
      else:
        i += 1
    else:
      i += 1
  flush(n)
  if not count:
    return src, 0
  return ''.join(out), count
