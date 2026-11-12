"""Olex2 user login: the person at this Olex2 is the one whose email is
user.email (DataDir's user.phil). With the TimerPlus plugin installed the
login is mandatory: if that email is not in the people database, a form asks
for the details the database needs, at every start until it is filled in.
Without TimerPlus nobody is asked. Someone already in the database under
another email picks themselves from the list; that email is then written to
their entry. After saving the form, and after every refinement, a structure
without an operator gets the logged-in user as operator ('Solved by') and CIF
contact author. Not for a structure that started from a CIF from elsewhere
(opened with no .ins/.res next to it): its operator is someone else, so it is
left to the user. The same after the operator was removed by hand.
spy.gui.login.assign_operator() fills it in by hand.

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
    if olx.IsFileLoaded() == 'true' and not no_auto_operator():
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


def _mark_path(name):
  return os.path.join(OV.StrDir(), name + logic.NO_AUTO_MARK)


def _names():
  return {n for n in (OV.FileName(), OV.ModelSrc()) if n}


def no_auto_operator():
  """True if the current structure's operator is not filled in automatically."""
  if not OV.StrDir():
    return False
  return any(os.path.exists(_mark_path(n)) for n in _names())


def _write_marks(names, reason):
  """Mark names; returns the newly marked ones."""
  new = [n for n in names if not os.path.exists(_mark_path(n))]
  if new:
    os.makedirs(OV.StrDir(), exist_ok=True)
  for n in new:
    with open(_mark_path(n), 'w', encoding='utf-8') as f:
      f.write("%s: %s, so the operator is not filled in automatically.\n" % (n, reason))
  return new


def stop_auto_operator():
  """The operator was removed by hand: do not fill it in again."""
  if OV.StrDir():
    _write_marks(_names(), "the operator was removed by hand")


def _on_file_change(arg):
  """Mark a CIF opened without an .ins/.res of the same name next to it."""
  try:
    if olx.IsFileLoaded() != 'true' or olx.IsFileType('cif') != 'true' or not OV.StrDir():
      return
    names = [OV.FileName(), olx.xf.DataName(olx.xf.CurrentData())]
    names = logic.external_cif_names(names, os.listdir(OV.FilePath()))
    if not _write_marks(names, "it came from a CIF from elsewhere"):
      return
    print("CIF from elsewhere: operator and contact author are not set automatically.")
  except Exception:
    _report("checking where the CIF came from")


class _RefineListener:
  def onEnd(self, caller):
    try:
      from RunPrg import RunRefinementPrg
      if isinstance(caller, RunRefinementPrg) and not no_auto_operator():
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
  try:
    olx.FileChangeListeners.append(_on_file_change)
  except AttributeError:
    olx.FileChangeListeners = [_on_file_change]
  if OV.HasGUI():
    olx.Schedule(2, 'spy.gui.login.check()')


_register()
