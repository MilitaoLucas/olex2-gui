"""
Tests for gui/help/help_index.py -- run from util/pyUtil/gui/help:

    python -m unittest test_help_index
"""

import os
import shutil
import tempfile
import unittest

import help_index as H


def _write(path, text):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, 'w', encoding='utf8') as f:
    f.write(text)


class HelpIndexTest(unittest.TestCase):

  def setUp(self):
    self.base = tempfile.mkdtemp()
    self.root = os.path.join(self.base, 'util', 'pyUtil')

  def tearDown(self):
    shutil.rmtree(self.base)

  def test_only_help_md_files(self):
    _write(os.path.join(self.root, 'gui', 'moiety', 'moiety.help.md'), "# Moiety\nText\n")
    _write(os.path.join(self.root, 'gui', 'moiety', 'README.md'), "# Notes\nnot help\n")
    _write(os.path.join(self.root, '_AC7d', 'x.help.md'), "# Copy\nskipped\n")
    _write(os.path.join(self.root, '.git', 'y.help.md'), "# Git\nskipped\n")
    index, dups = H.build_index(self.base)
    self.assertEqual(sorted(index['entries']), ['MOIETY'])
    self.assertEqual(index['entries']['MOIETY']['src'], 'util/pyUtil/gui/moiety/moiety.help.md')
    self.assertEqual(dups, [])

  def test_all_md_for_explicit_folders(self):
    _write(os.path.join(self.root, 'ACED', 'aced.md'), "# Aced\nText\n")
    self.assertEqual(len(H.find_help_files(os.path.join(self.root, 'ACED'))), 0)
    self.assertEqual(len(H.find_help_files(os.path.join(self.root, 'ACED'), all_md=True)), 1)

  def test_headings_preamble_and_subheadings(self):
    p = os.path.join(self.root, 'a.help.md')
    _write(p, "---\ntitle: x\n---\n[comment]: < note >\n"
              "# Peak Sliders\nIntro\n## Detail\nMore\n# Other Tool\nText\n")
    entries = dict(H.parse_help_file(p, self.base))
    self.assertEqual(sorted(entries), ['OTHER_TOOL', 'PEAK_SLIDERS'])
    self.assertIn('<h2>Detail</h2>', entries['PEAK_SLIDERS'])
    self.assertNotIn('<p>', entries['PEAK_SLIDERS'])

  def test_target_entries_are_raw(self):
    p = os.path.join(self.root, 'a.help.md')
    # the marker is the end of the heading: "# start-target"
    _write(p, "# start-target\nStart here!\n- Sample\n")
    self.assertEqual(dict(H.parse_help_file(p, self.base))['START-TARGET'], 'Start here!\n- Sample')

  def test_image_markers_relative_to_base(self):
    p = os.path.join(self.root, 'gui', 'moiety', 'moiety.help.md')
    _write(p, "# Moiety\n![0.5 The table](images/table.png)\n")
    html = dict(H.parse_help_file(p, self.base))['MOIETY']
    self.assertIn('{{HELPIMG|util/pyUtil/gui/moiety/images/table.png|0.5|The table}}', html)

  def test_dollar_escaping(self):
    p = os.path.join(self.root, 'a.help.md')
    _write(p, "# Tool\nCost $5, run $spy.x()\n")
    html = dict(H.parse_help_file(p, self.base))['TOOL']
    self.assertIn('\\$5', html)
    self.assertIn('$spy.x()', html)

  def test_rebuild_replaces_a_files_entries_and_reports_duplicates(self):
    a = os.path.join(self.root, 'a.help.md')
    b = os.path.join(self.root, 'b.help.md')
    _write(a, "# One\nx\n# Two\ny\n")
    _write(b, "# Two\nfrom b\n")
    entries, files, dups = H.build([a, b], self.base)
    self.assertEqual(dups, [('TWO', 'util/pyUtil/a.help.md', 'util/pyUtil/b.help.md')])
    _write(a, "# Three\nz\n")             # edited: One gone, Three new
    H.build([a], self.base, entries, files)
    self.assertNotIn('ONE', entries)
    self.assertIn('THREE', entries)
    self.assertEqual(entries['TWO']['src'], 'util/pyUtil/b.help.md')

  def test_index_round_trip(self):
    _write(os.path.join(self.root, 'a.help.md'), "# Tool\nText\n")
    index, _ = H.build_index(self.base)
    path = os.path.join(self.base, H.INDEX_NAME)
    H.write_index(index, path)
    self.assertEqual(H.read_index(path), index)
    self.assertIsNone(H.read_index(os.path.join(self.base, 'missing.json')))


if __name__ == '__main__':
  unittest.main()
