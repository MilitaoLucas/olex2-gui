"""The people-database pages (form.py) and their colours (style.py)."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import form
import style


class StyleTest(unittest.TestCase):
  def test_dark_help_colours_give_lighter_boxes(self):
    p = style.palette({'bg': '#222222', 'font': '#ffffff'})
    self.assertEqual(p['bg'], '#222222')
    self.assertTrue(style.is_dark(p['input_bg']))
    self.assertGreater(style._rgb(p['input_bg'])[0], 0x22)
    self.assertGreater(style._rgb(p['border'])[0], style._rgb(p['input_bg'])[0])
    self.assertEqual(p['input_fg'], '#ffffff')

  def test_light_background_gives_darker_boxes(self):
    p = style.palette({'bg': '#ffffff', 'font': '#000000'})
    self.assertLess(style._rgb(p['border'])[0], 0xff)

  def test_broken_values_fall_back(self):
    class Colour:
      hexadecimal = '#102030'
    p = style.palette({'bg': None, 'font': 'nonsense', 'highlight': Colour()})
    self.assertEqual((p['bg'], p['font'], p['highlight']), ('#222222', '#ffffff', '#102030'))


class FormTest(unittest.TestCase):
  P = style.palette()

  def check_page(self, html, names):
    for tag in ('table', 'tr', 'td', 'font'):
      self.assertEqual(len(re.findall('<%s[ >]' % tag, html)), html.count('</%s>' % tag), tag)
    self.assertNotIn('%(', html)
    found = [(kind, name) for kind, name in re.findall(r'<input type="(\w+)" name="(\w+)"', html)
             if kind != 'button']
    self.assertEqual(sorted(n for _, n in found), sorted(names))
    for kind, name in found:
      if kind in ('text', 'combo', 'list'):   # boxed: drawn border round it
        i = html.index('name="%s"' % name)
        self.assertIn('bgcolor="%s"' % self.P['border'], html[html.rfind('<table', 0, i):i])

  def test_login_page(self):
    html = form.login_page(self.P)
    self.check_page(html, ['message', 'person', 'email', 'firstname', 'lastname',
                           'affiliation', 'new_affiliation', 'phone', 'orcid'])
    self.assertIn('spy.gui.login.save()', html)
    self.assertIn('bgcolor="%s"' % self.P['bg'], html)

  def test_users_page_keeps_the_control_names(self):
    html = form.users_page(self.P)
    self.check_page(html, ['message', 'Sites', 'People', 'add_author']
                    + [n for _, n in form.SITE_FIELDS + form.PERSON_FIELDS])
    for name in ('UpdateSite', 'AddSite', 'DeleteSite', 'UpdatePerson', 'AddPerson', 'DeletePerson'):
      self.assertEqual(html.count('name="%s"' % name), 1, name)
    self.assertIn("html.EndModal('~popup_name~', 1)", html)


if __name__ == '__main__':
  unittest.main()
