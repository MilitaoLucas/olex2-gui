import os, sys, string
import io
import libtbx.phil
import libtbx.phil.interface
from libtbx.phil.interface import index
from libtbx.phil import scope_extract_attribute_error
from libtbx.phil import Auto

from libtbx.phil import tokenizer

def rgb2hex(rgb):
  """return the hexadecimal string representation of an rgb colour"""
  return '#%02x%02x%02x' % rgb

def hex2rgb(value):
  """return the rgb tuple representation of a hexadecimal colour"""
  value = value.lstrip('#')
  lv = len(value)
  return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))

html_colours = {
  'aqua':'#00ffff',
  'cyan':'#00ffff',
  'black':'#000000',
  'blue':'#0000ff',
  'fuchsia':'#ff00ff',
  'magenta':'#ff00ff',
  'grey':'#808080',
  'green':'#008000',
  'lime':'#00ff00',
  'maroon':'#800000',
  'navy':'#000080',
  'olive':'#808000',
  'purple':'#800080',
  'red':'#ff0000',
  'silver':'#c0c0c0',
  'teal':'#008080',
  'white':'#ffffff',
  'yellow':'#ffff00'
}

class colour(object):
  def __init__(self, colour_str=None, rgb=None, hexadecimal=None):
    assert [colour_str, rgb, hexadecimal].count(None) == 2
    if colour_str is not None:
      try:
        rgb = tuple(int(i)for i in colour_str.strip('()').split(','))
      except ValueError:
        hexadecimal = html_colours.get(colour_str.lower())
        if hexadecimal is None:
          hexadecimal = colour_str
    if rgb is not None:
      hexadecimal = rgb2hex(rgb)
    elif hexadecimal is not None:
      rgb = hex2rgb(hexadecimal)
    self.rgb = rgb
    self.hexadecimal=hexadecimal

  def __str__(self):
    return self.hexadecimal

class colour_converters(object):

  phil_type = "colour"

  def __str__(self): return self.phil_type

  def from_words(self, words, master):
    s = libtbx.phil.str_from_words(words=words)
    if (s is None): return None
    if (s is Auto): return Auto
    return colour(colour_str=s)

  def as_words(self, python_object, master):
    if (python_object is None):
      return [tokenizer.word(value="None")]
    if (python_object is Auto):
      return [tokenizer.word(value="Auto")]
    return [tokenizer.word(value=str(python_object.hexadecimal))]

default_converter_registry = libtbx.phil.extended_converter_registry(
  additional_converters=[colour_converters],
  base_registry=libtbx.phil.default_converter_registry)

# Parsed-file cache: unpickling a parsed tree is ~10x faster than tokenizing and parsing
# it again (params.phil: 51 -> 6 ms on x64, ~1 s saved on an A53). One slot per file
# name, keyed by the file's bytes, the parser sources' stat and the python version, so
# any change re-parses. Off outside Olex2 (no olx) unless parse_cache_dir is set.
# Definition strings (plugin phils, the method_imp constants, skin phils) are cached too,
# one slot per content: parse(cache=True), or by default from module level.
# ponytail: a changed string leaves its old slot behind; prune by age if the dir grows.
try:  # set at import: method_imp parses its constants before LoadParams runs
  import olx
  parse_cache_dir = os.path.join(olx.DataDir(), "phil_cache")
except Exception:
  parse_cache_dir = None
_parse_sig = None

def _cached_parse(file_name, input_string=None, process_includes=False):
  import hashlib, pickle
  global _parse_sig
  if _parse_sig is None:
    d = os.path.dirname(libtbx.phil.__file__)
    st = [os.stat(p) for p in (os.path.join(d, "__init__.py"), os.path.join(d, "parser.py"),
                               os.path.join(d, "tokenizer.py"), __file__)]
    _parse_sig = repr((sys.version, [(s.st_size, s.st_mtime_ns) for s in st]))
  if input_string is None:
    with open(file_name, "rb") as f:
      data = f.read()
  else:
    data = input_string.encode("utf-8")
  key = hashlib.sha1(("%s\0%s\0%s\0" % (_parse_sig, file_name, process_includes)).encode("utf-8")
                     + data).hexdigest().encode()
  slot = os.path.join(parse_cache_dir, (hashlib.sha1(file_name.encode("utf-8")).hexdigest()[:20]
    if input_string is None else "s" + key[:20].decode()) + ".pkl")
  try:
    with open(slot, "rb") as f:
      if f.readline().rstrip() == key:
        return pickle.load(f)
  except Exception:
    pass
  result = libtbx.phil.parse(input_string=input_string, file_name=file_name,
    converter_registry=default_converter_registry, process_includes=process_includes)
  try:
    os.makedirs(parse_cache_dir, exist_ok=True)
    tmp = "%s.%d.tmp" % (slot, os.getpid())
    with open(tmp, "wb") as f:
      f.write(key + b"\n")
      pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, slot)
  except Exception:
    pass
  return result

def parse(
      input_string=None,
      source_info=None,
      file_name=None,
      converter_registry=None,
      process_includes=False,
      cache=None):
  if parse_cache_dir and source_info is None and converter_registry is None:
    if file_name and input_string is None and not process_includes:
      return _cached_parse(file_name)
    # included scopes are not in the key
    if (input_string and file_name is None
        and not (process_includes and "include" in input_string)
        and (cache or cache is None and sys._getframe(1).f_code.co_name == "<module>")):
      return _cached_parse(None, input_string, process_includes)
  if (converter_registry is None):
    converter_registry = default_converter_registry
  return libtbx.phil.parse(
    input_string=input_string,
    source_info=source_info,
    file_name=file_name,
    converter_registry=converter_registry,
    process_includes=process_includes)

#
# Main interface to Phil
#
def _merge_objects(self, object):
  for obj in object.objects:
    matching = None
    for tobj in self.objects:
      if tobj.name == obj.name:
        matching = tobj
        break
    if matching:
      try:
        if matching.is_scope:
          matching._merge_objects(obj)
        else:
          tobj.words = obj.words
      except Exception as e:
        print(e)
    else:
      if obj.is_scope:
        obj.change_primary_parent_scope(self)
      else:
        obj.primary_parent_scope = self
      self.objects.append(obj)

def _replace_object(self, object):
  for i, tobj in enumerate(self.objects):
    if tobj.name == object.name:
      self.objects[i] = object
      return

# Scoped re-fetch: adopt_phil/merge_phil/reset_scope fetch again only the scopes a phil
# names and keep every other scope as is, instead of fetching (and extract_format-ing)
# the whole tree. That is ~250 ms per call on an A53 and start-up makes ~10 of them.
# The result is identical as long as the kept scopes are in extract_format form, which
# phil_handler._fmt tracks.
def _refetch(master, working, source, merge, path=(), whole=None):
  """working with only the sub-scopes that source names fetched again from master,
  or None when this level has to be fetched whole. merge: source is also a value
  source and the fetched parts get extract_format (merge_phil), else source only
  says which scopes gained definitions (adopt_phil). The paths fetched whole go to whole."""
  named = {}
  for o in source.objects:
    if (not o.is_scope and not merge) or o.is_disabled or o.is_template:
      return None
    named.setdefault(o.name, []).append(o)
  objects = list(working.objects)
  appended = False
  for name, sos in named.items():
    mos = [o for o in master.objects if o.name == name]
    wis = [i for i, o in enumerate(objects) if o.name == name]
    if len(mos) != 1 or len(wis) > 1:
      return None
    mo = mos[0]
    if not all(s.is_scope for s in sos):
      # a definition (snum.current_process_diagnostics): as scope.fetch does it, the last
      # of the working one and the source ones wins
      if (not all(s.is_definition for s in sos) or not mo.is_definition or mo.multiple
          or mo.is_disabled or mo.alias is not None or mo.deprecated or len(wis) != 1
          or objects[wis[0]].is_disabled):
        return None
      for s in [objects[wis[0]]] + sos:
        r = mo.fetch(source=s)
      objects[wis[0]] = r.extract_format()
      whole.append(path + (name,))
      continue
    if not mo.is_scope or mo.multiple or mo.is_disabled or mo.alias is not None:
      return None
    # 'user.a.b = 1' lines parse to one scope each, so a name can come several times
    so = sos[0] if len(sos) == 1 else sos[0].customized_copy(
      objects=[x for s in sos for x in s.objects])
    r = None
    if wis:
      wo = objects[wis[0]]
      if wo.is_disabled:
        return None
      r = _refetch(mo, wo, so, merge, path + (name,), whole)
    if r is None:
      r = mo.fetch(sources=([wo] if wis else []) + (sos if merge else []))
      if merge:
        r = r.extract_format()
      whole.append(path + (name,))
    if wis:
      objects[wis[0]] = r
    else:
      objects.append(r)
      appended = True
  if appended and [o.name for o in objects] != [o.name for o in master.master_active_objects()]:
    return None
  return working.customized_copy(objects=objects)

def _format_at(scope, path, done=()):
  """scope with the sub-scope at path in extract_format form, None if path is not one scope.
  done: paths below path that already are in that form (see _format_except)"""
  if not path:
    return _format_except(scope, done)
  objects = list(scope.objects)
  i = [k for k, o in enumerate(objects) if o.name == path[0]]
  if len(i) > 1:
    # a name master has twice (params.phil: user.solution): extract joins the copies, so
    # each is formatted from the group's joint extract; formatting all of user instead
    # was ~50 ms of every structure load on an A53
    g = [objects[k] for k in i]
    if any(o.multiple or o.is_template or o.is_disabled for o in g):
      return scope.extract_format()
    ex = scope.customized_copy(objects=g).extract().__phil_get__(path[0])
    for k in i:
      objects[k] = objects[k].format(ex)
    return scope.customized_copy(objects=objects)
  if len(i) != 1 or not objects[i[0]].is_scope:
    return None
  r = _format_at(objects[i[0]], path[1:], done)
  if r is None:
    return None
  objects[i[0]] = r
  return scope.customized_copy(objects=objects)

def _format_except(scope, done):
  """scope.extract_format(), formatting again only what is not under the paths in done
  (already in that form: a structure phil re-fetches snum.refinement etc. right after
  reset_scope('snum'), and formatting all of snum again was 0.3 s of a load on an A53).
  scope.format(scope.extract()) is the children's extract_format, one by one, as long as
  they are unique, plain (not multiple, template or disabled) objects; otherwise whole."""
  if not done:
    return scope.extract_format()
  if () in done:
    return scope
  objects = scope.objects
  if len({o.name for o in objects}) != len(objects) or any(
      o.multiple or o.is_template or o.is_disabled for o in objects):
    return scope.extract_format()
  return scope.customized_copy(objects=[
    _format_except(o, [d[1:] for d in done if d[0] == o.name]) if o.is_scope
    else o if (o.name,) in done else o.extract_format() for o in objects])

def _copy_tree(o):
  """o with every scope and definition copied (words lists shared: nothing edits them in place)"""
  c = o.copy()
  if o.is_scope:
    c.objects = [_copy_tree(x) for x in o.objects]
  return c

# ponytail: keeps master definitions replaced by adopt_phil alive; a few thousand at most
_default_cache = {}

def _default_words(mo):
  """master definition mo's words as written and in extract_format form (working is in that
  form: '3' for 3.0, 0.25 for 1/4, quotes dropped); either is the default to fetch_diff,
  which formats both sides. 103 of the 126 snum definitions a save hands it were these"""
  c = _default_cache.get(id(mo))
  if c is None or c[0] is not mo:
    r = [[(w.value, w.quote_token) for w in mo.words]]
    if not any("$" in w.value for w in mo.words):
      try:
        r.append([(w.value, w.quote_token) for w in mo.extract_format().words])
      except Exception:
        pass
    c = _default_cache[id(mo)] = (mo, r)
  return c[1]

def _drop_defaults(master, working):
  """(master, working) cut to what fetch_diff can report: working without the definitions
  whose words equal master's (fetch_diff drops those anyway, only after looking each up
  and converting it: 1.5 s of History per refine on an A53) and the scopes that leaves
  empty; master without the names working no longer has (fetch_diff walks every master
  scope, source or not: 0.1 s of every structure load). None if master uses aliases,
  which match sources under other names."""
  named = {}
  for o in master.objects:
    if o.alias is not None:
      return None
    named.setdefault(o.name, []).append(o)
  objects, cut = [], {}
  for o in working.objects:
    mo = named.get(o.name, ())
    sub = None # master's o cut down, None for all of it
    if len(mo) == 1 and not mo[0].multiple and not o.multiple and o.is_scope == mo[0].is_scope:
      if o.is_scope:
        r = _drop_defaults(mo[0], o)
        if r is None:
          return None
        if not r[1].objects:
          continue
        sub, o = r
      elif (not any("$" in w.value for w in o.words)
            and [(w.value, w.quote_token) for w in o.words] in _default_words(mo[0])):
        continue
    cut[o.name] = sub if o.name not in cut else None
    objects.append(o)
  return (master.customized_copy(objects=[o if cut[o.name] is None else cut[o.name]
                                          for o in master.objects if o.name in cut]),
          working.customized_copy(objects=objects))


class phil_handler(index):
  # (working_phil, paths of scopes in it that may not be in extract_format form) or None
  # when that is unknown; anything that sets working_phil without updating it makes the
  # next adopt/merge a full fetch
  _fmt = None
  _reload = None
  _reset_cache = None  # {scope name: (master scope, its fetch in extract_format form)}

  def setup_phil(self, working_phil, fetch_new=False):
    # a fresh fetch is master form everywhere, so the first merge (user.phil at start-up)
    # can take the scoped path and only extract_format the scopes it does not touch
    fresh = working_phil is None or fetch_new
    if fresh:
      working_phil = self.master_phil.fetch(**({} if working_phil is None else {"source": working_phil}))
    # build_index sets short_caption in place on every object it labels. A merge used to
    # replace them all by master's copies; the scoped one keeps the scopes it does not
    # touch, so take the labels off again (the index keeps its own copy of them)
    bare = []
    if fresh:
      todo = [working_phil]
      while todo:
        o = todo.pop()
        if o.short_caption is None:
          bare.append(o)
        if o.is_scope:
          todo.extend(o.objects)
    index.setup_phil(self, working_phil)
    for o in bare:
      o.short_caption = None
    objects = self.working_phil.objects
    if (fresh and all(o.is_scope for o in objects)
        and len({o.name for o in objects}) == len(objects)):
      self._fmt = (self.working_phil, [(o.name,) for o in objects])

  def adopt_phil(self, phil_object=None, phil_string=None, phil_file=None, merge_definitions=True):
    assert [phil_object, phil_string, phil_file].count(None) == 2
    if phil_string:
      phil_object = self.parse(phil_string, process_includes=True,
                               **({"cache": True} if self.parse is parse else {}))
    elif phil_file:
      phil_object = libtbx.phil.parse(file_name=phil_file, process_includes=True)
    if phil_object:
      self._reset_cache = None
      if not merge_definitions:
        for object in phil_object.objects:
          self.master_phil.adopt(object)
          self.master_phil.unique()
      else:
        libtbx.phil.scope._merge_objects = _merge_objects
        self.master_phil._merge_objects(phil_object)
      fmt, whole, w = self._fmt, [], None
      if merge_definitions and fmt is not None and fmt[0] is self.working_phil:
        w = _refetch(self.master_phil, self.working_phil, phil_object, False, whole=whole)
      if w is None:
        self.working_phil = self.master_phil.fetch(sources=[self.working_phil])
        self._fmt = None
      else:
        self.working_phil = w
        self._fmt = (w, fmt[1] + whole)
      self.rebuild_index()
      self.params = self.working_phil.extract()



  def save_param_file(self, file_name, scope_name=None, sources=[], diff_only=False,
                      out_stream=None):
    if scope_name is not None:
      assert '.' not in scope_name # can only save top-level scopes
    assert not(file_name and out_stream)
    if scope_name is not None and diff_only and len(sources) == 0:
      # History nodes and the structure .phil save one scope's diff: fetch that
      # scope alone the way fetch_diff of the root would, not every top-level
      # scope only to keep one
      for m in self.master_phil.master_active_objects():
        if m.name == scope_name and m.is_scope and not m.multiple:
          src = self.working_phil.get(path=scope_name, with_substitution=False,
                                      alias_path=m.alias_path())
          output_phil = m.fetch(sources=src.active_objects(), diff=True)
          if len(output_phil.objects) == 0:
            f = open(file_name, "w")
            f.close()
            return # diff is empty -> write empty file
          if out_stream:
            output_phil.show(out=out_stream)
          else:
            with open(file_name, "w", encoding="utf-8") as f:
              output_phil.show(out=f)
          return
    if len(sources) > 0:
      for source in sources:
        self.merge_phil(phil_object=source, overwrite_params=False,
                        rebuild_index=False)
    final_phil = self.working_phil
    if len(sources) > 0:
      base_phil = self.working_phil
      final_phil = self.master_phil.fetch(sources=[base_phil]+sources)
    if diff_only:
      master_phil = self.master_phil
      if scope_name is not None:
        # diff only the scope being saved: same text, 2-5x faster (History does this every refine)
        master_phil = master_phil.customized_copy(
          objects=[o for o in master_phil.objects if o.name == scope_name])
        final_phil = final_phil.customized_copy(
          objects=[o for o in final_phil.objects if o.name == scope_name])
      pruned = _drop_defaults(master_phil, final_phil)
      output_phil = (master_phil.fetch_diff(source=final_phil) if pruned is None
                     else pruned[0].fetch_diff(source=pruned[1]))
    else:
      output_phil = final_phil
    if scope_name is not None:
      scope_output_phil = None
      for scope in output_phil.master_active_objects():
        if scope.name == scope_name:
          scope_output_phil = scope
          break
      if scope_output_phil is None:
        f = open(file_name, "w")
        f.close()
        return # diff is empty -> write empty file
      else:
        output_phil = scope_output_phil
    if out_stream:
      output_phil.show(out=out_stream)
    else:
      with open(file_name, "w", encoding="utf-8") as f:
        output_phil.show(out=f)

  def show_diff(self, out=None):
    self.get_diff().show(out=out)

  def getRootScope (self) :
    return self.working_phil

  def get_values_by_name(self, def_name):
    if not def_name:
      return None
    values = []
    phil_objects = self.get_scope_by_name(def_name)
    if isinstance(phil_objects, list):
      for obj in phil_objects:
        if obj.is_definition:
          values.append(words_as_string(obj.words))
    else:
      values = [words_as_string(phil_objects.words)]
    return values

  def get_value_by_name(self, def_name):
    values = self.get_values_by_name(def_name)
    if len(values) > 0:
      return values[0]
    else:
      return None

  def get_python_from_params (self, phil_object):
    return self.get_python_from_other(phil_object=phil_object)

  def set_param(self, def_name, value):
    scopes = def_name.split('.')
    parent_scope = self.params
    for scope_name in scopes:
      current_scope = getattr(
        parent_scope, scope_name, scope_extract_attribute_error)
      if not isinstance(current_scope, scope_extract_attribute_error):
        if isinstance(current_scope, libtbx.phil.scope_extract):
          parent_scope = current_scope
          continue
        else:
          parent_scope.__setattr__(scope_name, value)
    self._phil_has_changed = True

  def reset_scope (self, phil_scope_name, rebuild_index=True) :
    fmt, old = self._fmt, self.working_phil
    mos = [o for o in self.master_phil.objects if o.name == phil_scope_name]
    wis = [i for i, o in enumerate(old.objects) if o.name == phil_scope_name]
    if (fmt is not None and fmt[0] is old and len(mos) == 1 and len(wis) == 1
        and mos[0].is_scope and not mos[0].multiple and not mos[0].is_disabled):
      # the reset scope in extract_format form is the same every time until adopt_phil
      # grows master_phil, so format it once (0.4 s of every structure load on an A53)
      # and hand out copies: working objects get attributes rebound in place
      c = (self._reset_cache or {}).get(phil_scope_name)
      if c is None or c[0] is not mos[0]:
        c = (mos[0], mos[0].fetch(sources=[]).extract_format())
        self._reset_cache = dict(self._reset_cache or {}, **{phil_scope_name: c})
      objects = list(old.objects)
      objects[wis[0]] = _copy_tree(c[1])
      self.working_phil = old.customized_copy(objects=objects)
      self._fmt = (self.working_phil, [p for p in fmt[1] if p[0] != phil_scope_name])
    else:
      index.reset_scope(self, phil_scope_name)
      if fmt is not None and fmt[0] is old:
        self._fmt = (self.working_phil, fmt[1] + [(phil_scope_name,)])
    if rebuild_index:
      self.rebuild_index()

  def reset_scope_and_update(self, phil_scope_name, phil_strings):
    """reset_scope + update() with each string. Start-up does this once per plugin with
    the same skin phil; when nothing touched the tree since the same call built it, the
    result would be that tree again, so only the bookkeeping is redone. Every write of
    working_phil replaces it (adopt also does when it grows master_phil), except
    update_single_param, which _fmt records."""
    key = (phil_scope_name, tuple(phil_strings))
    r, w, fmt = self._reload, self.working_phil, self._fmt
    if (r is not None and r[0] == key and r[1] is w and fmt is not None
        and fmt[0] is w and not fmt[1]):
      self.rebuild_index()
      self._phil_has_changed = True
      return
    self.reset_scope(phil_scope_name)
    for s in phil_strings:
      if s:  # skin files: cached like definitions
        self.update(phil_object=self.parse(s, **({"cache": True} if self.parse is parse else {})))
    self._reload = (key, self.working_phil)

  def reset(self, scope_name=None, scope_names=None):
    print("Use reset_scope() instead of this function.")
    self.reset_scope(scope_name)

  def merge_phil(self, phil_object=None, phil_string=None, phil_file=None,
                 overwrite_params=True, rebuild_index=True, merge_definitions=True):
    #XXX don't override this function?
    if phil_string:
      phil_object = self.parse(phil_string)
    elif phil_file:
      phil_object = self.parse(file_name=phil_file)
    if phil_object:
      #self.master_phil.merge_names(
      old_phil = self.working_phil
      fmt, whole, new_phil = self._fmt, [], None
      if fmt is not None and fmt[0] is old_phil and () not in fmt[1]:
        new_phil = _refetch(self.master_phil, old_phil, phil_object, True, whole=whole)
        for p in fmt[1]:
          if new_phil is not None and not any(p[:len(w)] == w for w in whole):
            new_phil = _format_at(new_phil, p, [w[len(p):] for w in whole if w[:len(p)] == p])
            whole.append(p) # formatted now: a repeat (every SetParam records one) is skipped
      if new_phil is None:
        new_phil = self.master_phil.fetch(sources=[old_phil, phil_object])
        if new_phil is not None:
          new_phil = new_phil.extract_format()
      if new_phil is not None:
        self.working_phil = new_phil
        self._fmt = (new_phil, [])
        if rebuild_index:
          self.rebuild_index()
      else:
        pass
      self._phil_has_changed = True

  def update(self, phil_object=None, phil_string=None, phil_file=None):
    assert [phil_object, phil_string, phil_file].count(None) == 2
    if phil_string:
      phil_object = self.parse(phil_string)
    elif phil_file:
      phil_object = self.parse(file_name=phil_file)
    if phil_object:
      try:
        self.merge_phil(phil_object=phil_object)
      except Exception as e:
        print("Error updating Phil", file=sys.stderr)
        sys.stderr.formatExceptionInfo()

  # SetParam walked the master and working trees on every call (0.8 ms, 30k
  # calls in a FLINT run); what a name resolves to changes only when a tree is
  # replaced, which every reshaping path does, so it is cached per pair of roots
  def _defs(self, name):
    c = self.__dict__.get('_defs_cache')
    if c is None or c[0] is not self.master_phil or c[1] is not self.working_phil:
      c = self._defs_cache = (self.master_phil, self.working_phil, {})
    d = c[2].get(name)
    if d is None:
      d = c[2][name] = (self.master_phil.get_without_substitution(name),
                        self.working_phil.get_without_substitution(name))
    return d

  def param_exists(self, name):
    return len(self._defs(name)[0]) > 0

  def update_single_param(self, name, value):
    new_phil_object = self.parse("%s=%s" %(name,value))
    wos = new_phil_object.get_without_substitution(name)
    mwos, wdefs = self._defs(name)
    if not mwos:
      raise libtbx.phil.Sorry(f"Undefined keyword: {name}")
    for master_defintion, working_definition in zip(mwos, wdefs):
      assert working_definition.is_definition
      for new_definition in wos:
        if working_definition.name == new_definition.name:
          proxy = master_defintion.validate(str(value))
          if proxy.error_message is None:
            working_definition.words = master_defintion.fetch_value(new_definition).words
            if self._fmt is not None:
              self._fmt[1].append(tuple(name.split('.')[:-1]))
            self._phil_has_changed = True
          else:
            raise libtbx.phil.Sorry(proxy.error_message)

  def name_value_pairs(self, scope_name=None):
    if scope_name is not None:
      scope = self.get_scope_by_name(scope_name)
    else:
      scope = self.getRootScope()
    active_objects = scope.master_active_objects()
    return self._name_value_pairs_impl(scope_name, active_objects)

  def _name_value_pairs_impl(self, scope_name, active_objects):
    result = []
    for object in active_objects:
      if object.is_scope:
        result += self._name_value_pairs_impl(
          "%s.%s" %(scope_name,object.name), object.master_active_objects())
      elif object.is_definition:
        result.append(("%s.%s" %(scope_name,object.name), object.extract()))
      else:
        pass
    return result

def words_as_string (words, strip_quotes=False) :
  word_strings = []
  for word in words :
    word_strings.append(str(word))
  value_string = " ".join(word_strings)
  if strip_quotes :
    if value_string[0] == '\"' and value_string[-1] == '\"' :
      return value_string[1:-1]
  return value_string

def coerce_value(e):
  from olexFunctions import OV
  if "as an integer expression" in e:
    _ = e.split("Error interpreting ")[1].split(" ")[0].split("=")
  try:
    OV.SetParam(_[0], int(float(_[1].strip('"').strip("'"))))
  except:
    print("Please make sure that this value for %s is an integer, and not a text string or a float." %(_[0]))
