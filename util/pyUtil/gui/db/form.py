"""HTML for the people-database windows (the login form and Manage users and
sites), in the style of the Olex2 Help window: its background, a large title,
grouped sections and coloured buttons. Colours come from style.current().

Plain functions returning strings, so the pages can be tested without
Olex2. Every input sits in a one-pixel cell of the border colour: wxWidgets
draws no visible border round its controls on a dark background.
"""

try:
  from . import style
except ImportError:   # tests: imported without the package
  import style

LABEL_WIDTH = '30%'


def page(title, body, p, intro='', header_right=''):
  """header_right: controls on the title line, right-aligned (e.g. a chooser)."""
  span = ' colspan="2"' if header_right else ''
  intro = ('<tr><td%s><font color="%s">%s</font></td></tr>' % (span, p['muted'], intro)
           if intro else '')
  right = ('<td align="right" valign="center">%s</td>' % header_right) if header_right else ''
  return (
    '<html>\n<body bgcolor="%(bg)s" link="%(highlight)s">\n'
    '<font face="$GetVar(HtmlFontName)" color="%(font)s">\n'
    '<table border="0" cellpadding="6" cellspacing="0" width="100%%">\n'
    '<tr><td valign="center"><font size="5" color="%(title)s"><b>' % p + title
    + '&nbsp;</b></font></td>' + right + '</tr>\n'
    + intro + '\n'
    '<tr><td%s><font color="%s"><b><input type="label" name="message" width="100%%"></b>'
    '</font></td></tr>\n</table>\n' % (span, p['highlight'])
    + body +
    '\n</font>\n</body>\n</html>\n')


def section(title, rows, p, width='100%'):
  """A group of rows on a slightly lighter panel, with a header row."""
  return (
    '<table border="0" cellpadding="4" cellspacing="0" width="%s" bgcolor="%s">\n'
    '<tr bgcolor="%s"><td colspan="2"><font color="%s"><b>%s&nbsp;</b></font></td></tr>\n'
    '%s\n</table>\n' % (width, p['panel'], p['group'], p['title'], title, ''.join(rows)))


def spacer(height=8):
  return '<table border="0" cellpadding="0" cellspacing="0"><tr><td height="%i"></td></tr></table>\n' % height


def row(label, control, p, label_width=LABEL_WIDTH):
  return ('<tr><td width="%s" valign="center"><b>%s&nbsp;</b></td>'
          '<td valign="center">%s</td></tr>\n' % (label_width, label, control))


def full_row(content):
  return '<tr><td colspan="2">%s</td></tr>\n' % content


def hint(text, p):
  return full_row('<font color="%s">%s</font>' % (p['muted'], text))


def boxed(control, p):
  """The control inside a one-pixel border drawn by the html."""
  return ('<table border="0" cellpadding="1" cellspacing="0" width="100%%" bgcolor="%s">'
          '<tr><td bgcolor="%s"><font size="$GetVar(HtmlFontSizeControls)">%s</font>'
          '</td></tr></table>' % (p['border'], p['input_bg'], control))


def _colours(p):
  return 'bgcolor="%s" fgcolor="%s"' % (p['input_bg'], p['input_fg'])


def text(name, p):
  return boxed('<input type="text" name="%s" width="100%%" height="$GetVar(HtmlInputHeight)" %s>'
               % (name, _colours(p)), p)


def combo(name, items, p, onchange=''):
  onchange = ' onchange="%s"' % onchange if onchange else ''
  return boxed('<input type="combo" name="%s" width="100%%" height="$GetVar(HtmlComboHeight)"'
               ' items="%s" readonly %s%s>' % (name, items, _colours(p), onchange), p)


def listbox(name, items, p, height, onselect):
  items = ' items="%s"' % items if items else ''
  return boxed('<input type="list" name="%s" width="100%%" height="%i"%s %s onselect="%s">'
               % (name, height, items, _colours(p), onselect), p)


def checkbox(name, p, checked=False):
  return ('<input type="checkbox" name="%s" %sbgcolor="%s" fgcolor="%s" height="20">'
          % (name, 'checked="true" ' if checked else '', p['panel'], p['font']))


def button(value, onclick, p, name='', primary=False, width=90):
  """Flat buttons like the command buttons in the Help window; the primary
  one in the action colour."""
  name = ' name="%s"' % name if name else ''
  bg = p['action'] if primary else p['group']
  return ('<font size="$GetVar(HtmlFontSizeControls)"><b><input type="button"%s value="%s"'
          ' width="%i" height="$GetVar(HtmlComboHeight)" bgcolor="%s" fgcolor="%s"'
          ' flat="true" fit="false" onclick="%s"></b></font>'
          % (name, value, width, bg, p['button_fg'], onclick))


def buttons(left, right=()):
  """A row of buttons: 'left' on the left, 'right' on the right."""
  cells = ''.join('<td>%s</td>' % b for b in left)
  cells += '<td width="100%"></td>'
  cells += ''.join('<td align="right">%s</td>' % b for b in right)
  return ('<table border="0" cellpadding="3" cellspacing="0" width="100%%"><tr>%s</tr></table>\n'
          % cells)


# --- the login form (gui.login) --------------------------------------------

def login_page(p=None):
  p = p or style.current()
  known = section("Already in the database?", [
    row("I am", combo('person', 'spy.gui.login.people()', p,
                      'spy.gui.login.pick(html.GetValue(~name~))'), p),
    hint("Pick yourself, check the email below and press Save: that email then identifies you.", p),
  ], p)
  details = section("Your details", [
    row("Email", text('email', p), p),
    row("First name", text('firstname', p), p),
    row("Last name", text('lastname', p), p),
    row("Institution", combo('affiliation', 'spy.gui.login.affiliations()', p), p),
    row("or a new one", text('new_affiliation', p), p),
    row("Phone", text('phone', p), p),
    row("ORCID", text('orcid', p), p),
    hint("Phone and ORCID are optional.", p),
  ], p)
  body = (known + spacer() + details + spacer() +
          buttons([button("Not now", 'spy.gui.login.later()', p)],
                  [button("Save", 'spy.gui.login.save()', p, primary=True)]))
  return page("Who are you?", body, p, intro=(
    "Olex2 records you as the operator ('Solved by') and contact author of the "
    "structures you work on. Your details go into the people database set up "
    "for this computer or your institution."))


# --- Manage users and sites (gui.db) ---------------------------------------

SITE_FIELDS = (('Institution', 'name'), ('Department', 'department'),
               ('Address', 'address'), ('City', 'city'), ('Post code', 'postcode'),
               ('Country', 'country'))
PERSON_FIELDS = (('First name', 'firstname'), ('Middle name', 'middlename'),
                 ('Last name', 'lastname'), ('Email', 'email'), ('ORCID', 'orchid_id'),
                 ('Phone', 'phone'))


def _list_and_details(list_title, list_html, details_title, rows, button_row, p):
  left = section(list_title, [full_row(list_html)], p)
  right = section(details_title, rows + [full_row(button_row)], p)
  return ('<table border="0" cellpadding="0" cellspacing="0" width="100%%"><tr>'
          '<td width="34%%" valign="top">%s</td><td width="2%%"></td>'
          '<td width="64%%" valign="top">%s</td></tr></table>\n' % (left, right))


def users_page(p=None, clear_label=None):
  """clear_label: opened to pick a structure's person (Operator, Submitter),
  a button with this label sets that role to nobody (EndModal 2)."""
  p = p or style.current()
  sites = _list_and_details(
    "Sites", listbox('Sites', 'spy.gui.db.getSiteList()', p, 180,
                     'spy.gui.db.setSite(html.GetValue(~name~))'),
    "Site details", [row(label, text(name, p), p, '35%') for label, name in SITE_FIELDS],
    buttons([button("Update", 'spy.gui.db.updateSite()', p, name='UpdateSite'),
             button("Add as new", 'spy.gui.db.addSite()', p, name='AddSite', primary=True),
             button("Delete", 'spy.gui.db.deleteSite()', p, name='DeleteSite')]), p)
  people = _list_and_details(
    "People", listbox('People', '', p, 180,
                      'spy.gui.db.setPerson(html.GetValue(~name~))'),
    "Person details",
    [row(label, text(name, p), p, '35%') for label, name in PERSON_FIELDS]
    + [row("Author by default", checkbox('add_author', p), p, '35%')],
    buttons([button("Update", 'spy.gui.db.updatePerson()', p, name='UpdatePerson'),
             button("Add as new", 'spy.gui.db.addPerson()', p, name='AddPerson', primary=True),
             button("Delete", 'spy.gui.db.deletePerson()', p, name='DeletePerson')]), p)
  body = (sites + spacer() + people + spacer() +
          buttons([button(clear_label, "html.EndModal('~popup_name~', 2)", p, name='Clear', width=140)]
                  if clear_label else [],
                  [button("OK", "html.EndModal('~popup_name~', 1)", p, primary=True)]))
  return page("Users and sites", body, p, intro=(
    "Pick a site to see its people. 'Add as new' adds what is in the boxes; "
    "a new person goes to the site picked on the left."))
