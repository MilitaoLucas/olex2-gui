import olex
import olx

from olexFunctions import OlexFunctions
OV = OlexFunctions()

def BGColorForValue(value):
  if value == '' or value == '?':
    return "#FFDCDC"
  return OV.GetParam('gui.html.input_bg_colour')
  

class publication:
  def ChangeContactAuthor(self, person):
    if person == '': person = '?'
    if olx.cif_model is not None:
      data_name = OV.FileName().replace(' ', '')
      data_block = olx.cif_model[data_name]
      import userDictionaries
      if person != '?':
        data_block["_publ_contact_author_email"] =\
          userDictionaries.people.getPersonInfo(person, 'email')
        data_block["_publ_contact_author_phone"] =\
          userDictionaries.people.getPersonInfo(person, 'phone')
        data_block["_publ_contact_author_address"] =\
          userDictionaries.people.getPersonInfo(person, 'address')
      else:
        data_block["_publ_contact_author_email"] = '?'
        data_block["_publ_contact_author_phone"] = '?'
        data_block["_publ_contact_author_address"] = '?'
    OV.set_cif_item("_publ_contact_author_name", person)

  def OnContactAuthorChange(self, person_box_name):
    self.ChangeContactAuthor(
      olx.GetValue(person_box_name).strip())
    olx.UpdateHtml()

  def ChangePersonInfo(self, person, item, value):
    import userDictionaries
    if value == '': value = '?'
    userDictionaries.people.changePersonInfo(person, item, value)
    curent_person = OV.get_cif_item("_publ_contact_author_name")
    if curent_person == person:
      key = None
      if item == "email":
        key = "_publ_contact_author_email"
      elif item == "address":
        key = "_publ_contact_author_address"
      elif item == "phone":
        key = "_publ_contact_author_phone"
      if key is not None:
        OV.set_cif_item(key, value)

  def OnPersonInfoChange(self, person_box_name, item, box_name):
    value = olx.GetValue(box_name).strip()
    self.ChangePersonInfo(
      olx.GetValue(person_box_name),
      item,
      value)
    olx.html_SetBG(box_name, BGColorForValue(value))

  def AddNameToAuthorList(self, newName):
    oldValue = OV.GetParam("snum.metacif.publ_author_names")
    changed = False
    if newName not in ('?', ''):
      if oldValue is None:
        newValue = newName
        changed = True
      elif newName in oldValue:
        newValue = oldValue
        print "%s is already in the list of authors" %newName
      else:
        newValue = oldValue + ";" + newName
        changed = True
    if changed:
      OV.SetParam("snum.metacif.publ_author_names", newValue)
    return changed
  
  def OnAddNameToAuthorList(self, box_name):
    value = olx.GetValue(box_name).strip()
    if self.AddNameToAuthorList(value):
      olx.UpdateHtml()
  
pub = publication()
olex.registerFunction(pub.OnContactAuthorChange, False, "gui.report.publication")
olex.registerFunction(pub.OnPersonInfoChange, False, "gui.report.publication")
olex.registerFunction(pub.OnAddNameToAuthorList, False, "gui.report.publication")
