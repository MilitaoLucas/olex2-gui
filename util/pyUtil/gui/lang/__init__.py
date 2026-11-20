"""GUI translation: every etc/gui html file, translated as a whole into the VFS.

When the current language is not English, each etc/gui/**/*.htm file is read
(from the VFS, so plugin additions to index-*.htm are kept), translated with
core.translate_html against the language column of dictionary.txt, and
written back to the VFS under the same path.  Olex2 then renders the
translated copy - the same mechanism plugins use to add themselves to the
index files (gui.tools, persistence 0).

Runs once at import (startup); spy.gui.lang.apply() re-runs it, e.g. after
editing dictionary.txt or changing the language (English restores the
originals).  Image labels (headers, tabs) are translated separately by
PilTools.translate_label from the same dictionary.
"""
import os
import sys

import olx
import OlexVFS
from olexFunctions import OV

from . import core

_originals = {}   # VFS key -> bytes before translation
_written = {}     # VFS key -> bytes we wrote


def _gui_files():
  root = os.path.join(OV.BaseDir(), 'etc', 'gui')
  base = OV.BaseDir().replace('//', '/')
  for d, dirs, names in os.walk(root):
    for n in names:
      if n.lower().endswith(('.htm', '.html')):
        rel = os.path.relpath(os.path.join(d, n), root).replace('\\', '/')
        # the key form gui.tools uses for index-*.htm: '<BaseDir>/etc/gui/...'
        yield '%s/etc/gui/%s' % (base, rel), os.path.join(d, n)


def _current(key, path):
  data = OlexVFS.read_from_olex(key)
  if data is None:
    with open(path, 'rb') as f:
      data = f.read()
  return bytes(data)


def _decode(data):
  try:
    return data.decode('utf-8'), 'utf-8'
  except UnicodeDecodeError:
    return data.decode('latin-1'), 'latin-1'


def _restore():
  n = 0
  for key, data in list(_written.items()):
    try:
      if bytes(OlexVFS.read_from_olex(key) or b'') == data:
        OlexVFS.write_to_olex(key, _originals[key], 0)
        n += 1
    except Exception as err:
      print("Could not restore %s: %s" % (key, err))
      if hasattr(sys, '_wing_debugger'):
        raise
  _written.clear()
  return n


_table = {}
_applied = 'English'   # language the GUI html is in now


def translate_text(html):
  """Whole-string translation of html built at run time (Python panels):
  OlexVFS.html_filter while the GUI language is not English."""
  if not _table or not html:
    return html
  try:
    return core.translate_html(html, _table)[0]
  except Exception as err:
    print("Could not translate GUI html: %s" % err)
    if hasattr(sys, '_wing_debugger'):
      raise
    return html


def apply(update='true'):
  """Translate the GUI html into the current language (English: undo)."""
  global _table, _applied
  language = olx.CurrentLanguage() or 'English'
  _applied = language
  if language in ('', 'English'):
    _table = {}
    OlexVFS.html_filter = None
    n = _restore()
    if n:
      print("GUI html: %d files back to English" % n)
    return
  dictionary = os.path.join(OV.BaseDir(), 'dictionary.txt')
  try:
    table = core.load_dictionary(dictionary, language)
  except (OSError, KeyError) as err:
    print("No GUI translation for %s: %s" % (language, err))
    return
  _table = table
  OlexVFS.html_filter = translate_text
  files = strings = 0
  for key, path in _gui_files():
    try:
      cur = _current(key, path)
      # re-applying: start again from the untranslated text unless someone changed the file since
      src = _originals[key] if _written.get(key) == cur else cur
      text, enc = _decode(src)
      out, n = core.translate_html(text, table)
      if n:
        data = out.encode(enc)
        _originals[key] = src
        _written[key] = data
        OlexVFS.write_to_olex(key, data, 0)
        files += 1
        strings += n
      elif key in _written:
        OlexVFS.write_to_olex(key, src, 0)
        del _written[key]
    except Exception as err:
      print("Could not translate %s: %s" % (path, err))
      if hasattr(sys, '_wing_debugger'):
        raise
  print("GUI html in %s: %d strings in %d files (%d dictionary entries)" % (
    language, strings, files, len(table)))
  if str(update).lower() == 'true':
    olx.html.Update()


def apply_late():
  """Once, a second after startup: Olex2 may set the language only after the
  Python modules are imported."""
  if (olx.CurrentLanguage() or 'English') != _applied:
    apply(update='true')


OV.registerFunction(apply, False, 'gui.lang')
OV.registerFunction(apply_late, False, 'gui.lang')

try:
  if olx.CurrentLanguage() not in ('', 'English'):
    apply(update='false')
  olx.Schedule(1, 'spy.gui.lang.apply_late()')   # one-shot, not re-armed
except Exception as err:
  print("GUI translation at startup failed: %s" % err)
  if hasattr(sys, '_wing_debugger'):
    raise
