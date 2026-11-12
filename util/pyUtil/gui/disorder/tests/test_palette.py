"""The PART palette: every part gets a colour, and the designed ones keep the
promises made in palette.py.  No Olex2 needed."""
import itertools
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import palette as P

DESIGNED = sorted(P.DESIGNED)
KINDS = ('protan', 'deutan', 'tritan')


def pairs_of(parts):
  for p in parts:
    q = p + 1 if p > 0 else p - 1
    if p % 2 and q in parts:
      yield p, q


class EveryPartTest(unittest.TestCase):
  def test_any_number_has_a_colour_and_material(self):
    for p in list(range(-40, 0)) + list(range(1, 41)):
      self.assertRegex(P.html(p), r'^#[0-9a-f]{6}$', p)
      fields = P.material(p).split(';')
      self.assertEqual(fields[0], '85', p)
      self.assertEqual(len(fields), 5, p)
      for f in fields[1:4]:
        self.assertLess(int(f), 2 ** 32, p)
        self.assertEqual(int(f) >> 24, 255, p)  # opaque: the old PART 2 was nearly invisible

  def test_material_is_the_colour_in_olex2_byte_order(self):
    r, g, b = P.rgb(1)
    amb = int(P.material(1).split(';')[1])
    self.assertEqual((amb & 255, (amb >> 8) & 255, (amb >> 16) & 255),
                     tuple(int(round(x * 0.85)) for x in (r, g, b)))

  def test_names(self):
    self.assertEqual((P.collection(3), P.collection(-1)), ('_p3', '_pm1'))
    self.assertEqual((P.control(3), P.control(-2)), ('3', 'm2'))
    for p in (-3, 7):  # 'sel collection _p*' must still find them
      self.assertTrue(P.collection(p).startswith('_p'))
      self.assertTrue(re.match(r'^\w+$', P.collection(p)))

  def test_order(self):
    self.assertEqual(P.order({2, -1, 1, -2, 3}), [1, 2, 3, -1, -2])


class DesignedTest(unittest.TestCase):
  def test_all_apart(self):
    for a, b in itertools.combinations(DESIGNED, 2):
      self.assertGreaterEqual(P.distance(P.rgb(a), P.rgb(b)), 0.10, (a, b))

  def test_not_like_the_neighbouring_atoms(self):
    for p in DESIGNED:
      for element, colour in P.NEIGHBOURS.items():
        self.assertGreaterEqual(P.distance(P.rgb(p), P._hex_rgb(colour)), 0.11, (p, element))

  def test_pairs_survive_colour_blindness(self):
    for p, q in pairs_of(DESIGNED):
      for kind in KINDS:
        self.assertGreaterEqual(P.distance(P.rgb(p), P.rgb(q), kind), 0.12, (p, q, kind))

  def test_pairs_differ_in_lightness(self):
    for p, q in pairs_of(DESIGNED):
      self.assertGreaterEqual(abs(P.lch(p)[0] - P.lch(q)[0]), 0.15, (p, q))

  def test_common_parts_survive_colour_blindness(self):
    # 1, 2 and -1 are the parts most often seen together
    for a, b in itertools.combinations([1, 2, -1], 2):
      for kind in KINDS:
        self.assertGreaterEqual(P.distance(P.rgb(a), P.rgb(b), kind), 0.15, (a, b, kind))

  def test_designed_colours_fit_the_screen(self):
    for p in DESIGNED:
      L, C, h = P.lch(p)
      self.assertEqual(P.oklch_to_rgb(L, C, h), P.rgb(p))
      self.assertTrue(all(0 <= x <= 255 for x in P.rgb(p)))


class GeneratedTest(unittest.TestCase):
  def test_generated_pairs_are_apart(self):
    parts = list(range(9, 41)) + list(range(-40, -4))
    for p, q in pairs_of(parts):
      self.assertGreaterEqual(P.distance(P.rgb(p), P.rgb(q)), 0.15, (p, q))


class ToneInToneTest(unittest.TestCase):
  PARTS = [1, 2, 3, 4, 5, 6, 7, 8, -1, -2, -3, -4]

  def test_every_palette_has_a_description(self):
    self.assertEqual(sorted(P.DESCRIPTIONS), sorted(P.PALETTES))

  def test_pairs_survive_colour_blindness(self):
    for name in P.TONES:
      for p, q in pairs_of(self.PARTS):
        for kind in (None,) + KINDS:
          self.assertGreaterEqual(P.distance(P.rgb(p, name), P.rgb(q, name), kind), 0.2,
                                  (name, p, q, kind))

  def test_the_common_parts_are_apart(self):
    for name in P.TONES:
      for a, b in itertools.combinations([1, 2, -1, -2], 2):
        for kind in (None,) + KINDS:
          self.assertGreaterEqual(P.distance(P.rgb(a, name), P.rgb(b, name), kind), 0.085,
                                  (name, a, b, kind))

  def test_not_like_the_neighbouring_atoms(self):
    for name in P.TONES:
      for p in self.PARTS:
        for element, colour in P.NEIGHBOURS.items():
          self.assertGreaterEqual(P.distance(P.rgb(p, name), P._hex_rgb(colour)), 0.10,
                                  (name, p, element))

  def test_any_part_in_any_palette(self):
    for name in P.PALETTES:
      for p in list(range(-20, 0)) + list(range(1, 21)):
        self.assertRegex(P.html(p, name), r'^#[0-9a-f]{6}$', (name, p))

  def test_use(self):
    try:
      self.assertEqual(P.use('blues'), 'blues')
      self.assertEqual(P.html(1), P.html(1, 'blues'))
      self.assertEqual(P.use('no such'), 'contrast')
    finally:
      P.use('contrast')


class ButtonTest(unittest.TestCase):
  def test_text_is_readable(self):
    for p in list(range(-12, 0)) + list(range(1, 25)):
      text = P._hex_rgb(P.text_colour(p))
      self.assertGreaterEqual(P.contrast(P.rgb(p), text), 3.0, p)


if __name__ == '__main__':
  unittest.main()
