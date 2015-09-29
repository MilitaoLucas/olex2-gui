import os
import gui
import olex
import olx

class UsersDB:
  site_items = ('name', 'department', 'address', 'city', 'country', 'postcode')
  person_items = ('firstname', 'middlename', 'lastname', 'email', 'phone')
  def __init__(self):
    self.site = None
    self.person = None
    self.pop_name = "users-db"

  def ctrl(self, n):
    return "%s.%s" % (self.pop_name, n)

  def setMessage(self, txt=""):
    olx.html.SetLabel(self.ctrl("message"), txt)

  def Manage(self):
    w, h = 650, 700
    x, y = gui.GetBoxPosition(w, h)
    path = "%s/etc/gui/tools/users-db.htm" % (olx.BaseDir())
    olx.Popup(self.pop_name, path, s=True, b="tc", t="Manage users and sites",
           w=w, h=h, x=x, y=y)
    self.setSite(None)
    self.setPerson(None)
    self.setMessage()
    res = olx.html.ShowModal(self.pop_name)
    if res == "1":
      return self.person
    return None

  def getSiteList(self):
    from userDictionaries import affiliations
    return affiliations.getListAffiliations()

  def setSite(self, t):
    if not t:
      for i in self.site_items:
        olx.html.SetValue(self.ctrl(i), '')
      olx.html.SetEnabled(self.ctrl("DeleteSite"), False)
      olx.html.SetEnabled(self.ctrl("UpdateSite"), False)
      olx.html.SetEnabled(self.ctrl("AddPerson"), False)
      self.site = None
      self.setPerson(None)
      olx.html.SetItems(self.ctrl("People"), '')
      return
    from userDictionaries import affiliations
    self.site = affiliations.get_site(t)
    for i in self.site_items:
      olx.html.SetValue(self.ctrl(i), self.site.__dict__[i])
    olx.html.SetItems(self.ctrl("People"), self.getPeopleList(t))
    olx.html.SetEnabled(self.ctrl("UpdateSite"), True)
    olx.html.SetEnabled(self.ctrl("DeleteSite"), True)
    olx.html.SetEnabled(self.ctrl("AddPerson"), True)
    self.setPerson(None)
    self.setMessage()

  def updateSite_(self, id):
    import userDictionaries as ud
    if not self.site:
      if id:
        self.setMessage("Please select a site to update")
        return
      self.site = ud.site()
    else:
      self.site.id = id
    for i in self.site_items:
      self.site.__dict__[i] = olx.html.GetValue(self.ctrl(i))
    name = self.site.name.strip()
    if not name:
      self.setMessage("Non-empty name is expected")
      return
    self.site.id = id
    self.site.update()
    self.setSite(None)
    olx.html.SetItems(self.ctrl("Sites"), self.getSiteList())
    self.setMessage()

  def updateSite(self):
    self.updateSite_(self.site.id)

  def addSite(self):
    self.updateSite_(None)
    self.setSite(None)

  def deleteSite(self):
    from userDictionaries import affiliations
    affiliations.deleteSiteById(self.site.id)
    olx.html.SetItems(self.ctrl("Sites"), self.getSiteList())
    self.setSite(None)

  def getPeopleList(self, t):
    from userDictionaries import persons
    return persons.getListPeople(site_id=t, edit=False)

  def setPerson(self, t):
    if not t:
      for i in self.person_items:
        olx.html.SetValue(self.ctrl(i), '')
      olx.html.SetEnabled(self.ctrl("UpdatePerson"), False)
      olx.html.SetEnabled(self.ctrl("DeletePerson"), False)
      self.person = None
      return
    from userDictionaries import persons
    self.person = persons.get_person(t)
    for i in self.person_items:
      olx.html.SetValue(self.ctrl(i), self.person.__dict__[i])
    olx.html.SetEnabled(self.ctrl("UpdatePerson"), True)
    olx.html.SetEnabled(self.ctrl("DeletePerson"), True)
    self.setMessage()

  def updatePerson_(self, id):
    import userDictionaries as ud
    if not self.person:
      if id:
        self.setMessage("Please select a person to update")
        return
      self.person = ud.person(self.site.id)
    else:
      self.person.id = id
    for i in self.person_items:
      self.person.__dict__[i] = olx.html.GetValue(self.ctrl(i))
    lastname = self.person.lastname.strip()
    if not lastname:
      self.setMessage("Non-empty last name is expected")
      return
    self.person.update()
    self.setPerson(None)
    olx.html.SetItems(self.ctrl("People"),
      self.getPeopleList(self.site.id))
    self.setMessage()

  def updatePerson(self):
    self.updatePerson_(self.person.id)

  def addPerson(self):
    self.updatePerson_(None)
    self.setPerson(None)

  def deletePerson(self):
    from userDictionaries import persons
    persons.deletePersonById(self.person.id)
    olx.html.SetItems(self.ctrl("People"),
      self.getPeopleList(self.site.id))
    self.setPerson(None)

db = UsersDB()
olex.registerFunction(db.Manage, False, "gui.db")
olex.registerFunction(db.getSiteList, False, "gui.db")
olex.registerFunction(db.setSite, False, "gui.db")
olex.registerFunction(db.addSite, False, "gui.db")
olex.registerFunction(db.updateSite, False, "gui.db")
olex.registerFunction(db.deleteSite, False, "gui.db")
olex.registerFunction(db.getPeopleList, False, "gui.db")
olex.registerFunction(db.setPerson, False, "gui.db")
olex.registerFunction(db.addPerson, False, "gui.db")
olex.registerFunction(db.updatePerson, False, "gui.db")
olex.registerFunction(db.deletePerson, False, "gui.db")
