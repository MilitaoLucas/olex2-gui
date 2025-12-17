import os
import gui
import olex
import olx

class UsersDB:
  site_items = ('name', 'department', 'address', 'city', 'country', 'postcode')
  person_items = ('firstname', 'middlename', 'lastname', 'email', 'phone', 'orchid_id')
  def __init__(self):
    self.site = None
    self.person = None
    self.pop_name = "users-db"

  def ctrl(self, n):
    return "%s.%s" % (self.pop_name, n)

  def setMessage(self, txt=""):
    OV.SetControlLabel(self.ctrl("message"), txt)

  def Manage(self):
    w, h = 650, 700
    x, y = gui.GetBoxPosition(w, h)
    path = "%s/etc/gui/tools/users-db.htm" % (olx.BaseDir())
    path = os.path.join(olx.BaseDir(), "etc", "gui", "tools", "users-db.htm")
    olx.Popup(self.pop_name, path, s=True, b="tc", t="Manage users and sites",
           w=w, h=h, x=x, y=y)
    self.setSite(None)
    self.setPerson(None)
    self.setMessage()
    res = OV.ShowModal(self.pop_name)
    if res == "1":
      return self.person
    return None

  def getSiteList(self):
    from userDictionaries import affiliations
    return affiliations.getListAffiliations()

  def setSite(self, t):
    if not t:
      for i in self.site_items:
        OV.SetControlValue(self.ctrl(i), '')
      OV.SetControlEnabled(self.ctrl("DeleteSite"), False)
      OV.SetControlEnabled(self.ctrl("UpdateSite"), False)
      OV.SetControlEnabled(self.ctrl("AddPerson"), False)
      self.site = None
      self.setPerson(None)
      OV.SetControlItems(self.ctrl("People"), '')
      return
    from userDictionaries import affiliations
    self.site = affiliations.get_site(t)
    for i in self.site_items:
      OV.SetControlValue(self.ctrl(i), self.site.__dict__[i])
    OV.SetControlItems(self.ctrl("People"), self.getPeopleList(t))
    OV.SetControlEnabled(self.ctrl("UpdateSite"), True)
    OV.SetControlEnabled(self.ctrl("DeleteSite"), True)
    OV.SetControlEnabled(self.ctrl("AddPerson"), True)
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
      self.site.__dict__[i] = OV.GetControlValue(self.ctrl(i))
    name = self.site.name.strip()
    if not name:
      self.setMessage("Non-empty name is expected")
      return
    self.site.id = id
    self.site.update()
    self.setSite(None)
    OV.SetControlItems(self.ctrl("Sites"), self.getSiteList())
    self.setMessage()

  def updateSite(self):
    self.updateSite_(self.site.id)

  def addSite(self):
    self.updateSite_(None)
    self.setSite(None)

  def deleteSite(self):
    from userDictionaries import affiliations
    affiliations.deleteSiteById(self.site.id)
    OV.SetControlItems(self.ctrl("Sites"), self.getSiteList())
    self.setSite(None)
    
  def getPeopleList(self, t):
    from userDictionaries import persons
    return persons.getListPeople(site_id=t, edit=False)

  def getPerson(self, t):
    from userDictionaries import persons
    return persons.get_person(id=t)

  def setPerson(self, t):
    if not t:
      for i in self.person_items:
        OV.SetControlValue(self.ctrl(i), '')
      OV.SetControlEnabled(self.ctrl("UpdatePerson"), False)
      OV.SetControlEnabled(self.ctrl("DeletePerson"), False)
      self.person = None
      return
    from userDictionaries import persons
    self.person = persons.get_person(t)
    for i in self.person_items:
      OV.SetControlValue(self.ctrl(i), self.person.__dict__[i])
    OV.SetControlEnabled(self.ctrl("UpdatePerson"), True)
    OV.SetControlEnabled(self.ctrl("DeletePerson"), True)
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
      self.person.__dict__[i] = OV.GetControlValue(self.ctrl(i))
    lastname = self.person.lastname.strip()
    if not lastname:
      self.setMessage("Non-empty last name is expected")
      return
    self.person.update()
    self.setPerson(None)
    OV.SetControlItems(self.ctrl("People"),
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
    OV.SetControlItems(self.ctrl("People"),
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
olex.registerFunction(db.getPerson, False, "gui.db")
olex.registerFunction(db.addPerson, False, "gui.db")
olex.registerFunction(db.updatePerson, False, "gui.db")
olex.registerFunction(db.deletePerson, False, "gui.db")
