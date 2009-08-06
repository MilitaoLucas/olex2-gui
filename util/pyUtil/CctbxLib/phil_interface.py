import os, sys, string
import cStringIO
import iotbx.phil
import libtbx.phil
from libtbx.phil import scope_extract_attribute_error

#
# Begin temporary cut-and-paste from libtbx.phil
#

class _check_value_base(object):

  def _check_value(self, value, path_producer, words=None):
    def where_str():
      if (words is None): return ""
      return words[0].where_str()
    if (self.value_min is not None and value < self.value_min):
      raise RuntimeError(
        "%s element is less than the minimum allowed value:"
        " %s < %s%s"
          % (path_producer(), self._value_as_str(value=value),
             self._value_as_str(value=self.value_min), where_str()))
    if (self.value_max is not None and value > self.value_max):
      raise RuntimeError(
        "%s element is greater than the maximum allowed value:"
        " %s > %s%s"
          % (path_producer(), self._value_as_str(value=value),
             self._value_as_str(value=self.value_max), where_str()))

class number_converters_base(_check_value_base):

  def __init__(self,
      value_min=None,
      value_max=None):
    if (value_min is not None and value_max is not None):
      assert value_min <= value_max
    self.value_min = value_min
    self.value_max = value_max

  def __str__(self):
    kwds = []
    if (self.value_min is not None):
      kwds.append("value_min=" + self._value_as_str(value=self.value_min))
    if (self.value_max is not None):
      kwds.append("value_max=" + self._value_as_str(value=self.value_max))
    if (len(kwds) != 0):
      return self.phil_type + "(" + ", ".join(kwds) + ")"
    return self.phil_type

  def from_words(self, words, master):
    path = master.full_path()
    value = self._value_from_words(words=words, path=master.full_path())
    if (value is None or value is libtbx.phil.Auto): return value
    self._check_value(
      value=value, path_producer=master.full_path, words=words)
    return value

  def as_words(self, python_object, master):
    if (python_object is None):
      return [libtbx.phil.tokenizer.word(value="None")]
    if (python_object is libtbx.phil.Auto):
      return [libtbx.phil.tokenizer.word(value="Auto")]
    return [libtbx.phil.tokenizer.word(value=self._value_as_str(value=python_object))]

class int_converters(number_converters_base):

  phil_type = "int"

  def _value_from_words(self, words, path):
    return libtbx.phil.int_from_words(words=words, path=path)

  def _value_as_str(self, value):
    return "%d" % value

class float_converters(number_converters_base):

  phil_type = "float"

  def _value_from_words(self, words, path):
    return libtbx.phil.float_from_words(words=words, path=path)

  def _value_as_str(self, value):
    return "%.10g" % value

converter_registry = libtbx.phil.extended_converter_registry(
  additional_converters=[float_converters,
                         int_converters],
  base_registry=iotbx.phil.default_converter_registry)

#
# End temporary cut-and-paste from libtbx.phil
#


#
# Main interface to Phil
# Shamefully borrowed from Phenix PhilInterface.py
#
class phil_handler(object):
  def __init__(self, master_phil, working_phil=None):
    
    self._full_path_index    = {}
    self._full_text_index    = {}
    self._phil_has_changed = False
    self._params_has_changed = False
    self._expert_level = 1

    self.master_phil = master_phil
    if working_phil is None:
      self.working_phil = self.master_phil.fetch()
    else:
      self.working_phil = self.master_phil.fetch(sources=[working_phil])
    self._build_index(collect_multiple=True)
    self._params = self.working_phil.extract()

  def adopt_phil(self, phil_object=None, phil_string=None, phil_file=None):
    assert [phil_object, phil_string, phil_file].count(None) == 2
    if phil_string:
      phil_object = iotbx.phil.parse(
        phil_string,
        converter_registry=converter_registry)
    elif phil_file:
      phil_object = iotbx.phil.parse(
        file_name=phil_file,
        converter_registry=converter_registry)
    if phil_object:
      for object in phil_object.objects:
        self.master_phil.adopt(object)
      self.working_phil = self.master_phil.fetch(sources=[self.working_phil])
      self._rebuild_index()
      self._params = self.working_phil.extract()

  def save_param_file(self, file_name, scope_name=None, sources=[], diff_only=False):
    if scope_name is not None:
      assert '.' not in scope_name # can only save top-level scopes
    if len(sources) > 0:
      for source in sources:
        self.merge_phil(phil_object=source, overwrite_params=False,
                        rebuild_index=False)
    final_phil = self.working_phil
    if len(sources) > 0:
      base_phil = self.working_phil
      final_phil = self.master_phil.fetch(sources=[base_phil]+sources)
    if diff_only:
      output_phil = self.master_phil.fetch_diff(source=final_phil)
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
    f = open(file_name, "w")
    output_phil.show(out=f)
    f.close()

  def get_diff(self):
    return self.master_phil.fetch_diff(source=self.working_phil)

  def show_diff(self, out=None):
    self.get_diff().show(out=out)

  def save_diff(self, file_name):
    f = open(file_name, "w")
    self.show_diff(f)
    f.close()

  def set_interface_level(self, expert_level):
    self._expert_level = int(expert_level)

  def copy(self, preserve_changes=False):
    working_phil = None
    if preserve_changes:
      working_phil = self.working_phil
    return phil_handler(master_phil=self.master_phil, working_phil=working_phil)

  def getRootScope (self) :
    return self.working_phil

  def get_scope_by_merged_name(self, merged_name):
    return self._full_path_index[merged_name]

  def get_scope_by_name(self, scope_name, phil_parent=None):
    if scope_name in self._full_path_index:
      indexed_phil_objects = self._full_path_index[scope_name]
      if isinstance(indexed_phil_objects, list) and phil_parent is not None:
        child_objects = []
        for object1 in indexed_phil_objects:
          for object2 in phil_parent.objects:
            if object1 is object2:
              child_objects.append(object1)
        return child_objects
      else:
        return indexed_phil_objects
    else:
      return None

  def get_validated_param(self, def_name):
    if self._params_has_changed:
      self.update_from_python(self._params)
      self._params_has_changed = False
    phil_objects = self.get_scope_by_name(def_name)
    if isinstance(phil_objects, list):
      vals = []
      for obj in phil_objects:
        python_value = obj.extract()
        phil_value = python_value.format()
        vals.append(phil_value)
      return vals
    elif phil_objects is not None:
      python_value = phil_objects.extract()
      return python_value

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

  def get_python_object(self, scope_name=None):
    if self._phil_has_changed or self._params is None:
      self._params = self.working_phil.extract()
      self._phil_has_changed = False
    if scope_name is not None:
      return self.get_scope_by_merged_name(scope_name).extract()
    else:
      return self._params

  def get_python_from_params(self, phil_object):
    try:
      new_phil = self.master_phil.fetch(source=phil_object)
    except Exception, e:
      pass
    else:
      return new_phil.extract()

  def get_python_from_file(self, phil_file):
    phil_object = iotbx.phil.parse(file_name=phil_file)
    return self.get_python_from_params(phil_object)

  def get_interface_level (self) :
    #if self._app is not None :
      #return self._app.expert_level
    #else :
      #return self._expert_level
    return self._expert_level

  def getStyle (self, scope_name=None) :
    return self.get_scope_style(scope_name)

  def get_scope_style (self, scope_name=None) :
    if scope_name in self.style :
      return self.style[scope_name]
    else :
      return phil_gui_style()

  def get_scope_phil (self, scope_name) :
    _phil_string = cStringIO.StringIO()
    scope_objects = self.get_scope_by_name(scope_name)
    if isinstance(scope_objects, list) :
      for phil_object in scope_objects :
        phil_object.show(out=_phil_string)
    else :
      scope_objects.show(out=_phil_string)
    return _phil_string.getvalue()

  def get_phil_help_string (self, phil_name) :
    if phil_name in self._full_text_index :
      (label, caption, help, is_def) = self._full_text_index[phil_name]
      return str(help)
    else :
      return None

  def set_param(self, def_name, value):
    scopes = def_name.split('.')
    parent_scope = self._params
    for scope_name in scopes:
      current_scope = getattr(
        parent_scope, scope_name, scope_extract_attribute_error)
      if not isinstance(current_scope, scope_extract_attribute_error):
        if isinstance(current_scope, libtbx.phil.scope_extract):
          parent_scope = current_scope
          continue
        else:
          parent_scope.__setattr__(scope_name, value)
    self._params_has_changed = True

  def search_phil_text (self, search_text, match_all=False, labels_only=True) :
    fields = search_text.split()
    for word in fields :
      # this allows matching of phil param paths
      if re.search("[^a-zA-Z\.\_]", word) is not None :
        raise Sorry("Invalid search string '%s'." % word)
    regex_list = [ re.compile(word, re.I) for word in fields ]
    matching_defs = []
    n_words = len(regex_list)
    for phil_name, phil_text in self._full_text_index.iteritems() :
      (label, caption, help, is_def) = phil_text
      if phil_name in self._hidden or not is_def :
        continue
      n_found = 0
      if labels_only :
        for regex in regex_list :
          if regex.search(label) is None :
            if match_all : break
            else :         continue
          n_found += 1
      else :
        for regex in regex_list :
          if (regex.search(label) is None and
              regex.search(phil_name) is None and
              regex.search(caption) is None and
              regex.search(help) is None) :
            if match_all : break
            else :         continue
          n_found += 1
      if (match_all and n_found == n_words) or n_found > 0 :
        matching_defs.append(phil_name)
    return matching_defs

  def reset(self, scope_name=None, scope_names=None):
    assert [scope_name, scope_names].count(None) < 2
    if scope_name is not None:
      scope_names = [scope_name]
    if scope_names is None:
      self = self.copy()
    else:
      for scope_name in scope_names:
        master = self.master_phil.get(scope_name)
        self.update(phil_object=master)

  def _build_index (self, collect_multiple=False) :
    path_index = {}
    multiple_scopes = {}
    multiple_defs = {}
    text_index = {}
    phil_scope = self.getRootScope()
    _index_phil_objects(phil_scope, path_index, text_index, multiple_scopes,
      multiple_defs, collect_multiple)
    self._full_path_index = path_index
    self._full_text_index = text_index
    if collect_multiple :
      self._multiple_scopes = multiple_scopes
      self._multiple_defs = multiple_defs

  def _rebuild_index (self) :
    path_index = {}
    phil_scope = self.getRootScope()
    _reindex_phil_objects(phil_scope, path_index)
    self._full_path_index = path_index

  def merge_phil(self, phil_object=None, phil_string=None, phil_file=None,
                 overwrite_params=True, rebuild_index=True):
    if phil_string:
      phil_object = iotbx.phil.parse(phil_string)
    elif phil_file:
      phil_object = iotbx.phil.parse(file_name=phil_file)
    if phil_object:
      old_phil = self.working_phil
      #if overwrite_params:
        #new_paths = 
      new_phil = self.master_phil.fetch(sources=[old_phil, phil_object])
      if new_phil is not None:
        self.working_phil = new_phil
        if rebuild_index:
          self._rebuild_index()
      else:
        pass
      self._phil_has_changed = True

  #def merge_param_file(self, file_name):
    #try:
      #phil_object = iotbx.phil.parse(file_name=file_name)
    #except Exception, e:
      #try

  def update(self, phil_object=None, phil_string=None, phil_file=None):
    assert [phil_object, phil_string, phil_file].count(None) == 2
    if phil_string:
      phil_object = iotbx.phil.parse(phil_string)
    elif phil_file:
      phil_object = iotbx.phil.parse(file_name=phil_file)
    if phil_object:
      try:
        new_phil = self.master_phil.fetch(source=phil_object)
      except Exception, e:
        print >> sys.stderr, "Error updating Phil"
        sys.stderr.formatExceptionInfo()
      else:
        self.merge_phil(phil_object=phil_object)

  def update_from_python(self, python_object):
    self.working_phil = self.master_phil.format(python_object=python_object)
    self._rebuild_index()

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

def _index_phil_objects (phil_object, path_index, text_index,
    multiple_scopes=None, multiple_defs=None, collect_multiple=True) :
  if phil_object.is_template < 0 :
    return
  full_path = phil_object.full_path()
  if phil_object.multiple == True :
    if collect_multiple :
      if phil_object.is_scope and multiple_scopes is not None:
        multiple_scopes[full_path] = True
      elif multiple_defs is not None :
        multiple_defs[full_path] = True
    if full_path in path_index :
      path_index[full_path].append(phil_object)
    else :
      path_index[full_path] = [phil_object]
  else :
    path_index[full_path] = phil_object
  label = get_standard_phil_label(phil_object)
  text_fields = (label, str(phil_object.caption), str(phil_object.help),
    phil_object.is_definition)
  text_index[full_path] = text_fields
  if phil_object.is_scope :
    for object in phil_object.objects :
      _index_phil_objects(object, path_index, text_index, multiple_scopes,
        multiple_defs, collect_multiple)

def _reindex_phil_objects (phil_object, path_index) :
  if phil_object.is_template < 0 :
    return
  full_path = phil_object.full_path()
  if phil_object.multiple == True :
    if full_path in path_index :
      path_index[full_path].append(phil_object)
    else :
      path_index[full_path] = [phil_object]
  else :
    path_index[full_path] = phil_object
  if phil_object.is_scope :
    for object in phil_object.objects :
      _reindex_phil_objects(object, path_index)

def get_all_path_names (phil_object, paths=None) :
  if paths is None :
    paths = []
  full_path = phil_object.full_path()
  if not full_path in paths :
    paths.append(full_path)
  if phil_object.is_scope :
    for object in phil_object.objects :
      get_all_path_names(object, paths)

def get_standard_phil_label (phil_object=None, phil_name=None, append="") :
  if phil_object is None and phil_name is None :
    raise Exception
  if phil_object is not None :
    if phil_object.short_caption is not None :
      return phil_object.short_caption + append
    elif phil_name is not None :
      return reformat_phil_name(phil_name)
    else :
      return reformat_phil_name(phil_object.name) + append
  else :
    return reformat_phil_name(phil_name)

def words_as_string (words, strip_quotes=False) :
  word_strings = []
  for word in words :
    word_strings.append(str(word))
  value_string = " ".join(word_strings)
  if strip_quotes :
    if value_string[0] == '\"' and value_string[-1] == '\"' :
      return value_string[1:-1]
  return value_string

def reformat_phil_name (phil_name) :
  try :
    _name = " ".join(str(phil_name).split("_"))
    name = string.upper(_name[0]) + _name[1:]
    return name
  except Exception :
    return ""
