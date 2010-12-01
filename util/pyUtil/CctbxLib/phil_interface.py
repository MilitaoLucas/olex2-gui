import os, sys, string
import cStringIO
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
  return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

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

def parse(
      input_string=None,
      source_info=None,
      file_name=None,
      converter_registry=None,
      process_includes=False):
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
class phil_handler(index):

  def adopt_phil(self, phil_object=None, phil_string=None, phil_file=None):
    assert [phil_object, phil_string, phil_file].count(None) == 2
    if phil_string:
      phil_object = self.parse(phil_string)
    elif phil_file:
      phil_object = libtbx.phil.parse(file_name=phil_file)
    if phil_object:
      for object in phil_object.objects:
        self.master_phil.adopt(object)
      self.working_phil = self.master_phil.fetch(sources=[self.working_phil])
      self.rebuild_index()
      self.params = self.working_phil.extract()

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
    index.reset_scope(self, phil_scope_name)
    if rebuild_index:
      self.rebuild_index()

  def reset(self, scope_name=None, scope_names=None):
    print "Use reset_scope() instead of this function."
    self.reset_scope(scope_name)

  def merge_phil(self, phil_object=None, phil_string=None, phil_file=None,
                 overwrite_params=True, rebuild_index=True):
    #XXX don't override this function?
    if phil_string:
      phil_object = self.parse(phil_string)
    elif phil_file:
      phil_object = self.parse(file_name=phil_file)
    if phil_object:
      old_phil = self.working_phil
      new_phil = self.master_phil.fetch(sources=[old_phil, phil_object])
      if new_phil is not None:
        self.working_phil = new_phil.extract_format()
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
      except Exception, e:
        print >> sys.stderr, "Error updating Phil"
        sys.stderr.formatExceptionInfo()

  def update_single_param(self, name, value):
    new_phil_object = self.parse("%s=%s" %(name,value))
    for master_defintion, working_definition in zip(
          self.master_phil.get_without_substitution(name),
          self.working_phil.get_without_substitution(name)):
      assert working_definition.is_definition
      for new_definition in new_phil_object.get_without_substitution(name):
        if working_definition.name == new_definition.name:
          proxy = master_defintion.validate(str(value))
          if proxy.error_message is None:
            working_definition.words = master_defintion.fetch_value(new_definition).words
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
