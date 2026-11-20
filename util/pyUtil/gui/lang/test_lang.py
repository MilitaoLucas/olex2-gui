"""Tests for gui/lang/core.py (no Olex2 needed)."""
import glob
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
GUI = os.path.join(ROOT, 'etc', 'gui')


def gui_files():
  return [p for p in glob.glob(os.path.join(GUI, '**', '*.htm*'), recursive=True)]


def read(p):
  raw = open(p, 'rb').read()
  try:
    return raw.decode('utf-8')
  except UnicodeDecodeError:
    return raw.decode('latin-1')


TABLE = {core.key_of(k): v for k, v in {
  'Refine': 'Verfeinern',
  'Hide Peanuts': 'Peanuts ausblenden',
  'Space Group:': 'Raumgruppe:',
  'Assign to part B': 'PART B zuweisen',
  'Level /eÅ': 'Niveau /eÅ',
  'Analyse &pi;-&pi; Interactions': '&pi;-&pi;-Wechselwirkungen analysieren',
  'Flack parameter:': 'Flack-Parameter:',
}.items()}


class TranslateTest(unittest.TestCase):

  def test_text_node(self):
    out, n = core.translate_html('<td>\n  Refine\n</td>', TABLE)
    self.assertEqual(out, '<td>\n  Verfeinern\n</td>')
    self.assertEqual(n, 1)

  def test_partial_text_untouched(self):
    src = '<b>Refine now</b><i>Refine</i>'
    self.assertEqual(core.translate_html(src, TABLE)[0], '<b>Refine now</b><i>Verfeinern</i>')

  def test_case_and_caps(self):
    self.assertEqual(core.translate_html('<b>REFINE</b>', TABLE)[0], '<b>VERFEINERN</b>')
    self.assertEqual(core.translate_html('<b>refine</b>', TABLE)[0], '<b>Verfeinern</b>')

  def test_entities_and_non_ascii(self):
    self.assertEqual(core.translate_html('<td>Level /e&Aring;</td>', TABLE)[0], '<td>Niveau /e&#197;</td>')
    out = core.translate_html('<td>Analyse &pi;-&pi; Interactions</td>', TABLE)[0]
    self.assertEqual(out, '<td>&pi;-&pi;-Wechselwirkungen analysieren</td>')

  def test_comments_calls_includes_kept(self):
    src = ('<!-- #include x gui\\x.htm;image=Refine;1; -->\n<!-- Refine -->'
           '$spy.MakeHoverButton("Refine","refine")<a href="refine>>html.update">Refine</a>')
    out = core.translate_html(src, TABLE)[0]
    self.assertTrue(out.startswith('<!-- #include x gui\\x.htm;image=Refine;1; -->\n<!-- Refine -->'
                                   '$spy.MakeHoverButton("Refine","refine")'))
    self.assertTrue(out.endswith('<a href="refine>>html.update">Verfeinern</a>'))

  def test_text_split_at_call(self):
    out = core.translate_html('<td>Flack parameter: $spy.get_flack()</td>', TABLE)[0]
    self.assertEqual(out, '<td>Flack-Parameter: $spy.get_flack()</td>')

  def test_attributes(self):
    out = core.translate_html('<a hint="Refine" href="Refine">x</a>', TABLE)[0]
    self.assertEqual(out, '<a hint="Verfeinern" href="Refine">x</a>')
    out = core.translate_html('<input type="button" value="Refine" name="Refine">', TABLE)[0]
    self.assertEqual(out, '<input type="button" value="Verfeinern" name="Refine">')
    out = core.translate_html('<input type="text" value="Refine">', TABLE)[0]
    self.assertEqual(out, '<input type="text" value="Refine">')

  def test_snippet_args(self):
    src = ('$+ html.Snippet(GetVar(default_link), "value=B", "hint=Assign to part B", '
           '"onclick=refine") $-\n$+ html.Snippet("x", "value=\'Hide Peanuts\'", "name=Refine") $-')
    out = core.translate_html(src, TABLE)[0]
    self.assertIn('"hint=PART B zuweisen"', out)
    self.assertIn('"value=\'Peanuts ausblenden\'"', out)
    self.assertIn('"onclick=refine"', out)
    self.assertIn('"name=Refine"', out)

  def test_marker_labels(self):
    table = {core.key_of('Contact Author'): 'Kontaktautor', core.key_of('Refine'): 'Verfeinern',
             core.key_of('CCDC Number'): 'CCDC-Nummer'}
    self.assertEqual(core.translate_html('<td>%Contact% %Author%</td>', table)[0], '<td>Kontaktautor</td>')
    self.assertEqual(core.translate_html('<b>%Refine%</b>', table)[0], '<b>Verfeinern</b>')
    self.assertEqual(core.translate_html('CCDC %Number%', table)[0], 'CCDC-Nummer')
    self.assertEqual(core.translate_html('<b>%Other% %Words%</b>', table)[0], '<b>%Other% %Words%</b>')

  def test_snippet_commas_kept(self):
    table = {core.key_of('Hint'): 'Erst dies, dann das.'}
    out = core.translate_html('$+ html.Snippet("x", "hint=Hint") $-', table)[0]
    self.assertIn('"hint=Erst dies, dann das."', out)

  def test_snippet_entities_quoted(self):
    table = {core.key_of('Molecular Volume'): 'Molekülvolumen',
             core.key_of('&mu; Plot'): '&mu;-Diagramm'}
    out = core.translate_html('$+ html.Snippet("x", "value=Molecular Volume") $-', table)[0]
    self.assertIn('"value=\'Molek&#252;lvolumen\'"', out)
    out = core.translate_html('$+ html.Snippet("x", "value=\'&mu; Plot\'") $-', table)[0]
    self.assertIn('"value=\'&mu;-Diagramm\'"', out)

  def test_script_untouched(self):
    src = '<script>var a = "<b>Refine</b>";</script><b>Refine</b>'
    self.assertEqual(core.translate_html(src, TABLE)[0],
                     '<script>var a = "<b>Refine</b>";</script><b>Verfeinern</b>')

  def test_every_gui_file_identity(self):
    """Mapping every key to itself must give back each etc/gui file unchanged:
    proves that the scanner loses or moves nothing."""
    files = gui_files()
    self.assertGreater(len(files), 100)
    for p in files:
      src = read(p)
      out, _ = core.translate_html(src, _Identity())
      self.assertEqual(out, src, p)

  def test_every_gui_file_only_text_changes(self):
    """With a table that translates everything, removing the visible strings
    from input and output must leave the same markup."""
    marker = _Marker()
    for p in gui_files():
      src = read(p)
      out, n = core.translate_html(src, marker)
      if not n:
        continue
      self.assertEqual(out.count('<'), src.count('<'), p)
      self.assertEqual(len(re.findall(r'\$[A-Za-z_]', out)), len(re.findall(r'\$[A-Za-z_]', src)), p)
      self.assertEqual(out.count('#include'), src.count('#include'), p)

  def test_load_dictionary(self):
    path = os.path.join(ROOT, 'dictionary.txt')
    if not os.path.exists(path):
      self.skipTest('no dictionary.txt')
    t = core.load_dictionary(path, 'German')
    self.assertGreater(len(t), 100)
    self.assertTrue(all(k == k.lower() for k in t))


class _Identity(dict):
  """Every lookup succeeds and returns the original text (see _identity_lookup)."""
  def __bool__(self):
    return True


class _Marker(dict):
  def __bool__(self):
    return True

  def get(self, k, default=None):
    return 'XX'


# identity needs the original spelling, not the key: patch lookup for that test
_orig_lookup = core.lookup


def _identity_lookup(text, table):
  if isinstance(table, _Identity):
    core_ = text.strip()
    if not core_ or not core.WORD.search(core_):
      return None
    return core_
  return _orig_lookup(text, table)


core.lookup = _identity_lookup


if __name__ == '__main__':
  unittest.main()
