import olex
import olx
import os

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
      olx.html.GetValue(person_box_name).strip())
    olx.html.Update()

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
    value = olx.html.GetValue(box_name).strip()
    self.ChangePersonInfo(
      olx.html.GetValue(person_box_name),
      item,
      value)
    olx.html.SetBG(box_name, BGColorForValue(value))

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
        newValue = "%s;%s" %(oldValue, newName)
        changed = True
    if changed:
      OV.SetParam("snum.metacif.publ_author_names", newValue)
    return changed

  def OnAddNameToAuthorList(self, box_name):
    value = olx.html.GetValue(box_name).strip()
    if self.AddNameToAuthorList(value):
      olx.html.Update()

pub = publication()
olex.registerFunction(pub.OnContactAuthorChange, False, "gui.report.publication")
olex.registerFunction(pub.OnPersonInfoChange, False, "gui.report.publication")
olex.registerFunction(pub.OnAddNameToAuthorList, False, "gui.report.publication")

def ResolvePrograms():
  if not OV.HasGUI():
    return True
  import History
  import olex_gui
  if not(History.get('solution', 'program') == 'Unknown' or\
         History.get('refinement', 'program') == 'Unknown'):
    return True
  sz = [int(i) for i in olx.GetWindowSize().split(',')]
  w = int(olx.html.ClientWidth('self'))
  h = int(olx.html.ClientHeight('self'))
  sw = 650
  sh = 200
  pop_name = 'report_resolve'
  olx.Popup("%s '%s/etc/gui/report-resolve-programs.htm' -x=%d -y=%d -w=%d -h=%d -s"
            %(pop_name, olx.BaseDir(),
              sz[0] + w/2 + sw/2,
              sz[1] + h/2 - sh/2,
              sw,
              sh) +
            " -b=tc -t='Missing data'")
  res = olx.html.ShowModal(pop_name)
  if not res or int(res) == 1:
    return False
  hs = History.tree
  if olex_gui.IsControl('solution_method', pop_name):
    hs.active_child_node.is_solution = True
    hs.active_child_node.program = olx.html.GetValue("%s.solution_program" %pop_name)
    hs.active_child_node.method = olx.html.GetValue("%s.solution_method" %pop_name)
  if olex_gui.IsControl('refinement_method', pop_name):
    if hs.active_node.is_solution:
      hs.add_node(OV.HKLSrc(), OV.FileFull(),
                  os.path.splitext(OV.FileFull())[0] + '.lst')
    hs.active_node.program = olx.html.GetValue("%s.refinement_program" %pop_name)
    hs.active_node.method = olx.html.GetValue("%s.refinement_method" %pop_name)
  History.make_history_bars()
  return True

olex.registerFunction(ResolvePrograms, False, "report")
