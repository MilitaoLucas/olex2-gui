"""Olex2 user login: the person at this Olex2 is the one whose email is
user.email (DataDir's user.phil). With the TimerPlus plugin installed the
login is mandatory: if that email is not in the people database, a form asks
for the details the database needs, at every start until it is filled in.
Without TimerPlus nobody is asked. Someone already in the database under
another email picks themselves from the list; that email is then written to
their entry. After saving the form, and after every refinement, a structure
without an operator gets the logged-in user as operator ('Solved by') and CIF
contact author.

spy.gui.login.show() opens the form again.
"""
import os
import sys

import olex
import olx
from olexFunctions import OV

from . import logic

POP = 'olex2-login'
PAGE = 'olex2-login.htm'   # built by gui.db.form, written to OlexFS
FIELDS = ('email', 'firstname', 'lastname', 'affiliation', 'new_affiliation', 'phone', 'orcid')


def _conn():
  import userDictionaries
  return userDictionaries.DBConnection().conn


def _ctrl(name):
  return '%s.%s' % (POP, name)


def _report(what):
  """The login must never stop Olex2 from working: say what failed and go on
  (re-raise under the Wing debugger)."""
  print("Login: %s failed: %s" % (what, sys.exc_info()[1]))
  if hasattr(sys, '_wing_debugger'):
    raise


def current_user():
  """(person id, display name) of the logged-in user, or None."""
  pid, status = logic.find_user(_conn(), OV.GetParam('user.email'))
  if status != 'found':
    return None
  import userDictionaries
  return pid, userDictionaries.persons.get_person(pid).get_display_name()


def timerplus_installed():
  import olex_core
  return 'TimerPlus' in (olex_core.GetPluginList() or [])


def check():
  """At start-up, for TimerPlus users only: show the form unless the user is
  known."""
  try:
    if not (OV.HasGUI() and timerplus_installed()):
      return
    if logic.find_user(_conn(), OV.GetParam('user.email'))[1] != 'found':
      show()
  except Exception:
    _report("start-up check")


def show():
  w, h = 560, 600
  import gui
  from gui.db import form
  x, y = gui.GetBoxPosition(w, h)
  OV.write_to_olex(PAGE, form.login_page())
  olx.Popup(POP, PAGE, s=True, b='tc',
            t='Welcome to Olex2', w=w, h=h, x=x, y=y)
  OV.SetPopBorder(POP, 0)
  OV.SetControlValue(_ctrl('email'), OV.GetParam('user.email') or '')
  status = logic.find_user(_conn(), OV.GetParam('user.email'))[1]
  _message({'duplicate': "Several people in the database have this email.",
            'found': "You are already in the database."}.get(status, ''))
  OV.ShowModal(POP)


def _message(text):
  OV.SetControlLabel(_ctrl('message'), text)


def affiliations():
  import userDictionaries
  return userDictionaries.affiliations.getListAffiliations()


def people():
  """Combo items for 'I am already listed as'."""
  return ';'.join('%s<-%s' % (label.replace(';', ','), pid)
                  for pid, label in logic.people_items(_conn()))


def pick(person_id):
  """A person chosen from the list: show their details. An email typed in
  before is kept; Save then writes it to that person."""
  fields = logic.person_fields(_conn(), person_id) if not logic.is_empty(person_id) else None
  if not fields:
    return
  typed = (OV.GetControlValue(_ctrl('email')) or '').strip()
  if typed and logic.find_user(_conn(), typed)[1] == 'missing':
    fields['email'] = typed
  for name in FIELDS:
    if name in fields:
      OV.SetControlValue(_ctrl(name), fields[name])
  _message('')


def save():
  values = {f: (OV.GetControlValue(_ctrl(f)) or '').strip() for f in FIELDS + ('person',)}
  try:
    if not logic.is_empty(values['person']):
      logic.claim_person(_conn(), values['person'], values['email'])
    else:
      logic.add_user(_conn(), values['email'], values['firstname'], values['lastname'],
                     affiliation_id=values['affiliation'] or None,
                     affiliation_name=values['new_affiliation'],
                     phone=values['phone'], orcid=values['orcid'])
  except ValueError as e:
    _message(str(e))
    return
  from variableFunctions import SaveUserParams
  OV.SetParam('user.email', logic.normalise_email(values['email']))
  SaveUserParams()
  olx.html.EndModal(POP, 1)
  try:
    if olx.IsFileLoaded() == 'true':
      assign_operator()
  except Exception:
    _report("setting the operator")


def later():
  """'Not now': asked again at the next start."""
  olx.html.EndModal(POP, 0)


def assign_operator():
  """Fill in an empty operator and contact author with the logged-in user."""
  user = current_user()
  if not user:
    return
  changes = logic.operator_changes(
    user[0], user[1], OV.GetParam('snum.report.operator'),
    OV.get_cif_item('_publ_contact_author_name'))
  if 'operator' in changes:
    OV.SetParam('snum.report.operator', changes['operator'])
  if 'contact' in changes:
    OV.set_cif_item('_publ_contact_author_name', changes['contact'])
    from gui.report import pub
    pub.AddNameToAuthorList(changes['contact'])
  if changes:
    print("Operator and contact author: %s" % user[1])


class _RefineListener:
  def onEnd(self, caller):
    try:
      from RunPrg import RunRefinementPrg
      if isinstance(caller, RunRefinementPrg):
        assign_operator()
    except Exception:
      _report("setting the operator")


def _register():
  for f in (show, save, later, affiliations, people, pick, assign_operator, check):
    olex.registerFunction(f, False, 'gui.login')
  try:
    from RunPrg import LM
    LM.register_listener(_RefineListener().onEnd, 'onEnd')
  except Exception:
    _report("registering the refinement listener")
  if OV.HasGUI():
    olx.Schedule(2, 'spy.gui.login.check()')


_register()
