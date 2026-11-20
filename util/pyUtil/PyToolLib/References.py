"""Olex2's references: every work Olex2 cites, defined once in etc/CIF/references.bib.

  import References
  References.cif('shelxl')      # 'Sheldrick, G.M. (2015). Acta Cryst. C71, 3-8.'
  References.brief('olex2')     # 'Dolomanov et al., 2009'
  References.doi('nosphera2')   # '10.1039/D0SC05526C'
  References.identify(text)     # ['shelxl', ...]: the works a piece of CIF text cites

identify() is how an existing CIF's _publ_section_references is read: a work is
recognised by its DOI, or by first author + year + volume and pages, whatever the
wording, line breaks or accents -- so an entry written by an older Olex2, typed by
hand or published since it was 'in press' is still the same work.

Plain Python, no Olex2 needed: the reference list lives next to this file's tree
(etc/CIF), and Olex2's base dir is used when it is known.

The shipped list is extended by the user's DataDir()/CIF/custom_references.bib,
as custom_settings.xld extends settings.xld (the shipped folder is not writable
for most users; DataDir is).  There, a new key adds a work, and a key of the
shipped list changes the fields given and keeps the others:

  @article{nbeam,
    pages = {1-12},
  }
"""
import os
import re
import textwrap
import unicodedata

_BIB_NAME = os.path.join('etc', 'CIF', 'references.bib')
_CUSTOM_NAME = os.path.join('CIF', 'custom_references.bib')
_cache = {}


def _bib_path():
  try:
    from olexFunctions import OV
    p = os.path.join(OV.BaseDir(), _BIB_NAME)
    if os.path.exists(p):
      return p
  except Exception:
    pass  # outside Olex2 (tests): the source tree
  here = os.path.dirname(os.path.abspath(__file__))
  return os.path.normpath(os.path.join(here, '..', '..', '..', _BIB_NAME))


def norm(text):
  """letters and digits only, lower case, accents dropped ('Pr\\'ochniak', 'Próchniak' -> 'prochniak')"""
  text = unicodedata.normalize('NFKD', str(text))
  return re.sub(r'[^a-z0-9]', '', text.lower())


def _strip_braces(text):
  """BibTeX braces off: {SHELX} -> SHELX, Pr{\\'o}chniak -> Pr\\'ochniak (the CIF code stays)"""
  return text.replace('{', '').replace('}', '')


class Reference(object):
  def __init__(self, kind, key, fields):
    self.kind = kind
    self.key = key
    self.fields = fields
    self.authors, self.et_al = self._authors(fields.get('author', ''))

  def __getattr__(self, name):
    if name.startswith('_') or name in ('kind', 'key', 'fields', 'authors', 'et_al'):
      raise AttributeError(name)
    return _strip_braces(self.fields.get(name, ''))

  @staticmethod
  def _authors(text):
    names = [n.strip() for n in re.split(r'\s+and\s+', _strip_braces(text).strip()) if n.strip()]
    et_al = bool(names) and names[-1] == 'others'
    if et_al:
      names = names[:-1]
    out = []
    for n in names:
      if ',' in n:
        surname, initials = [x.strip() for x in n.split(',', 1)]
      else:  # 'G.M. Sheldrick'
        parts = n.split()
        surname, initials = parts[-1], ' '.join(parts[:-1])
      out.append((surname, initials))
    return out, et_al

  @property
  def surnames(self):
    return [s for s, _ in self.authors]

  def brief(self):
    """'Sheldrick, 2015', 'Palatinus & Chapuis, 2007', 'Dolomanov et al., 2009'"""
    s = self.surnames
    if not s:
      who = self.title
    elif len(s) == 1 and not self.et_al:
      who = s[0]
    elif len(s) == 2 and not self.et_al:
      who = "%s & %s" % tuple(s)
    else:
      who = "%s et al." % s[0]
    return "%s, %s" % (who, self.year) if self.year else who

  def author_text(self):
    """IUCr: 'Palatinus, L., Prathapa, S.J. & van Smaalen, S.'; 'Sun, Q. et al.'"""
    names = ["%s, %s" % (s, i) if i else s for s, i in self.authors]
    if self.et_al:
      return "%s et al." % ", ".join(names)
    if len(names) > 1:
      return "%s & %s" % (", ".join(names[:-1]), names[-1])
    return "".join(names)

  def cif(self, width=80):
    """the entry for _publ_section_references"""
    who = self.author_text()
    when = " (%s)." % self.year if self.year else ""
    if self.kind == 'article':
      where = self.journal
      if self.note.lower() == 'in press':
        where += ", in press"
      else:
        if self.volume:
          where += " %s" % self.volume
        if self.pages:
          where += ", %s" % self.pages
        elif self.doi:
          where += ", doi:%s" % self.doi
      text = "%s%s %s." % (who, when, where)
    else:
      bits = [b for b in (self.title, self.publisher, self.address, self.url, self.note) if b]
      text = "%s%s %s." % (who, when, ", ".join(bits))
    text = re.sub(r'\.\.$', '.', text)
    if not width:
      return text
    return "\n".join(textwrap.wrap(text, width, break_on_hyphens=False, break_long_words=False))

  def markers(self):
    """groups of normalised strings; a text cites this work when every string of a group occurs in it"""
    groups = []
    if self.doi:
      groups.append((norm(self.doi),))
    if self.surnames and self.year and (self.volume or self.pages):
      groups.append((norm(self.surnames[0]), norm(self.year), norm(self.volume + self.pages)))
    for g in self.fields.get('markers', '').split('|'):
      g = tuple(norm(m) for m in g.split(';') if norm(m))
      if g:
        groups.append(g)
    return groups

  def programs(self):
    """the program names (field 'programs') this work is cited for"""
    return [p.strip() for p in self.fields.get('programs', '').split(';') if p.strip()]

  def __repr__(self):
    return "<Reference %s: %s>" % (self.key, self.brief())


def parse(text):
  """{key: Reference} from BibTeX text (one level of nested braces in values)"""
  refs = {}
  for m in re.finditer(r'@(\w+)\s*\{\s*([^,\s]+)\s*,', text):
    kind, key = m.group(1).lower(), m.group(2)
    if kind in ('comment', 'preamble', 'string'):
      continue
    i, depth = m.end(), 1
    while i < len(text) and depth:
      depth += {'{': 1, '}': -1}.get(text[i], 0)
      i += 1
    body = text[m.end():i - 1]
    fields = {}
    pos = 0
    fm = re.compile(r'\s*(\w+)\s*=\s*')
    while True:
      f = fm.match(body, pos)
      if not f:
        break
      name, j = f.group(1).lower(), f.end()
      if j < len(body) and body[j] == '{':
        d, k = 1, j + 1
        while k < len(body) and d:
          d += {'{': 1, '}': -1}.get(body[k], 0)
          k += 1
        value = body[j + 1:k - 1]
      else:
        k = body.find(',', j)
        k = len(body) if k < 0 else k
        value = body[j:k].strip().strip('"')
      fields[name] = " ".join(value.split())
      pos = k
      c = re.compile(r'\s*,?').match(body, pos)
      pos = c.end()
    if key in refs:
      raise ValueError("references.bib: the key %s is used twice" % key)
    refs[key] = Reference(kind, key, fields)
  return refs


def custom_path():
  """DataDir()/CIF/custom_references.bib; None outside Olex2"""
  try:
    from olexFunctions import OV
    return os.path.join(OV.DataDir(), _CUSTOM_NAME)
  except Exception:
    return None  # outside Olex2 (tests): the shipped list alone


def _mtime(path):
  try:
    return os.path.getmtime(path) if path else None
  except OSError:
    return None


def _read(path):
  with open(path, 'rb') as f:
    raw = f.read()
  try:
    return raw.decode('utf-8')
  except UnicodeDecodeError:  # saved by an editor in the Windows code page
    return raw.decode('latin-1')


def extend(refs, custom):
  """refs with the entries of `custom` ({key: Reference}): new keys added, known
  ones with the fields given replaced"""
  out = dict(refs)
  for key, r in custom.items():
    if key in out:
      fields = dict(out[key].fields)
      fields.update(r.fields)
      out[key] = Reference(r.kind, key, fields)
    else:
      out[key] = r
  return out


def all_references(path=None, custom=None):
  """{key: Reference}: the shipped list extended by the user's
  custom_references.bib; read again when either file changes"""
  path = path or _bib_path()
  custom = custom if custom is not None else custom_path()
  stamps = (_mtime(path), _mtime(custom))
  if stamps[0] is None:
    print("Olex2's reference list %s is missing: no references in the CIF" % path)
    return {}
  hit = _cache.get((path, custom))
  if hit and hit[0] == stamps:
    return hit[1]
  refs = parse(_read(path))
  if stamps[1] is not None:
    # the user's file never stops a CIF from being written: a mistake in it is
    # reported, and the shipped list is used alone
    try:
      refs = extend(refs, parse(_read(custom)))
    except Exception as err:
      print("Your reference list %s is not used: %s" % (custom, err))
  _cache[(path, custom)] = (stamps, refs)
  return refs


def get(key):
  """the Reference, or None (a key that is not in the list is a programming error: say so)"""
  r = all_references().get(key)
  if r is None and all_references():
    print("Olex2 references: there is no '%s' in references.bib" % key)
  return r


def cif(key, width=80):
  r = get(key)
  return r.cif(width) if r else ""


def brief(key):
  r = get(key)
  return r.brief() if r else ""


def doi(key):
  r = get(key)
  return r.doi if r else ""


def identify(text, refs=None):
  """keys of the works `text` cites, in list order; [] for text that cites none of them"""
  refs = refs if refs is not None else all_references()
  t = norm(text)
  if not t:
    return []
  return [k for k, r in refs.items() if any(all(m in t for m in g) for g in r.markers())]


def for_software(text, refs=None):
  """keys of the works cited for the programs `text` names (e.g. the _computing_*
  items: 'SHELXL-2019/2 (Sheldrick, 2019)' -> ['shelxl']), in list order.

  A name counts as a whole word in any case; where names overlap the longest
  wins, so 'SHELXL-97' is the 2008 paper only and 'ShelXle' is no 'SHELXL'."""
  refs = refs if refs is not None else all_references()
  text = str(text or '')
  hits = []  # (start, end, key)
  for key, r in refs.items():
    for name in r.programs():
      pat = r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])' % r'\s*'.join(re.escape(w) for w in name.split())
      hits += [(m.start(), m.end(), key) for m in re.finditer(pat, text, re.I)]
  found = set()
  for s, e, key in hits:
    if not any(s2 <= s and e <= e2 and (e2 - s2) > (e - s) for s2, e2, _ in hits):
      found.add(key)
  return [k for k in refs if k in found]


def merge_references(current, cited, managed):
  """the new _publ_section_references

  current: what the CIF has; cited: keys of the works this structure cites now;
  managed: keys Olex2 decides on (programs, methods): cited while used, dropped
  when not.  A work of the list in the CIF in any wording (older Olex2, typed by
  hand, in press since published) is written in its current form; text that
  is no work of the list is kept as it is."""
  keys = list(cited)
  kept = []
  for chunk in re.split(r'\n\s*\n', current.replace('\r', '')):
    if not chunk.strip():
      continue
    # an entry may hold several works ('a; b; c', as Superflip's once did)
    for part in (re.split(r';\s*\n', chunk) if ';' in chunk else [chunk]):
      found = identify(part)
      if not found:
        kept.append(part.strip().rstrip(';'))
      keys += [k for k in found if k not in managed]
  texts, seen = [], set()
  for t in [cif(k) for k in keys] + kept:
    n = ''.join(t.split())
    if t and n not in seen:
      seen.add(n)
      texts.append(t)
  return '\n\n'.join(sorted(texts))


_CUSTOM_TEMPLATE = """% Your additions to Olex2's reference list (etc/CIF/references.bib).
%
% A new key adds a work; a key of the shipped list changes only the fields
% given here.  Format and fields: see the head of etc/CIF/references.bib.
% A mistake in this file is reported in the console, and the shipped list is
% used alone until it is fixed.
%
% Example: the page numbers of a paper the shipped list has as 'doi only'
%
% @article{nbeam,
%   pages = {1-12},
% }
"""


def edit_custom():
  """open DataDir()/CIF/custom_references.bib in the editor, made with an
  explanation first when there is none"""
  p = custom_path()
  if not p:
    return
  if not os.path.exists(p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
      f.write(_CUSTOM_TEMPLATE)
    print("Created %s" % p)
  import olex
  olex.m('exec -o getvar(defeditor) "%s"' % p)


try:
  from olexFunctions import OV
  OV.registerFunction(edit_custom, False, 'references')
except Exception:
  pass  # outside Olex2 (tests)
