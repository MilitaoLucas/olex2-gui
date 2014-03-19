import olex
import olx
import os
import OlexVFS

import inspect

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import userDictionaries

current_py_file_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

global images_zip
global images_zip_name
images_zip = None
images_zip_name = None

person_box_created = False
affiliation_box_created = False

def BGColorForValue(value):
  if value == '' or value == '?':
    return "#FFDCDC"
  return OV.GetParam('gui.html.input_bg_colour')


class publication:

  def make_person_box(self, box, edit=False):
    import userDictionaries
    person = olx.html.GetValue(box).strip()
    if not person:
      return ''
    person = userDictionaries.people.get_person_details(person)
    if person['displayname'] == "New Person":
      edit = True
    if not edit:
      return person
    person.setdefault('list_affiliations', userDictionaries.
    affiliations.getListAffiliations())
    person.setdefault('banner_colour', "#005096")

    pop_name = "Person"
    person.setdefault('pop_name',pop_name)
    txt=open("%s/person.htm" %current_py_file_path, 'r').read()
    txt = txt%person
    OV.write_to_olex("person.htm", txt)
    global person_box_created
    if person_box_created:
      olx.Popup(pop_name, 'person.htm', s=True)
    else:
      boxWidth = 500
      boxHeight = 400
      x,y = get_box_x_y(boxWidth, boxHeight)
      olx.Popup(pop_name, 'person.htm', s=True, b="tc", t=pop_name,
                w=boxWidth, h=boxHeight, x=x, y=y)
      person_box_created = True

    address = userDictionaries.affiliations.get_affiliation_address(
      person['affiliation'], list=False)
    olx.html.SetValue('Person.PEOPLE_FORM_ADDRESS', address)

    res = olx.html.ShowModal(pop_name)
    if res == '1':
      firstname = olx.html.GetValue('Person.PERSON_FIRSTNAME')
      middlename = olx.html.GetValue('Person.PERSON_MIDDLENAME')
      lastname = olx.html.GetValue('Person.PERSON_LASTNAME')
      email = olx.html.GetValue('Person.PERSON_EMAIL')
      phone = olx.html.GetValue('Person.PERSON_PHONE')
      affiliation = olx.html.GetValue('Person.PERSON_AFFILIATION')
      if not lastname.strip():
        return ''
      res = userDictionaries.people.add_person(firstname, middlename, lastname,
        email, phone, affiliation, displayname=None)[6]
    else:
      return ''
    return res

  def make_affiliation_box(self, box, edit=False):
    import userDictionaries
    affiliation = olx.html.GetValue(box).strip()
    if not affiliation:
      return ''
    d = {}
    if '++' in affiliation:
      edit = True
      address = ["","","","","","","","New Affiliation"]
    else:
      address = userDictionaries.affiliations.get_affiliation_address(
        affiliation, list=True)[0]
      if not edit:
        return address

    d.setdefault('name', address[0])
    d.setdefault('department', address[1])
    d.setdefault('address1', address[2])
    d.setdefault('address2', address[3])
    d.setdefault('city', address[4])
    d.setdefault('post_code', address[5])
    d.setdefault('country', address[6])
    d.setdefault('banner_colour', "#005096")
    pop_name = "Affiliation"
    d.setdefault('pop_name',pop_name)
    txt=open("%s/affiliation.htm" %current_py_file_path, 'r').read()%d
    OV.write_to_olex("affiliation.htm", txt)
    global affiliation_box_created
    if affiliation_box_created:
      olx.Popup(pop_name, 'affiliation.htm', s=True)
    else:
      boxWidth = 500
      boxHeight = 400
      x,y = get_box_x_y(boxWidth, boxHeight)
      olx.Popup(pop_name, 'affiliation.htm', s=True, b="tc", t=pop_name,
                w=boxWidth, h=boxHeight, x=x, y=y)
      affiliation_box_created = True

    res = olx.html.ShowModal(pop_name)
    if res == '1':
      name = olx.html.GetValue('Affiliation.AFFILIATION_NAME')
      department = olx.html.GetValue('Affiliation.AFFILIATION_DEPARTMENT')
      address1 = olx.html.GetValue('Affiliation.AFFILIATION_ADDRESS_LINE_1')
      address2 = olx.html.GetValue('Affiliation.AFFILIATION_ADDRESS_LINE_2')
      city = olx.html.GetValue('Affiliation.AFFILIATION_CITY')
      post_code = olx.html.GetValue('Affiliation.AFFILIATION_POST_CODE')
      region = olx.html.GetValue('Affiliation.AFFILIATION_REGION')
      country = olx.html.GetValue('Affiliation.AFFILIATION_COUNTRY')
      if not name.strip():
        return ''
      userDictionaries.affiliations.add_affiliation(name, department, address1,
        address2, city, post_code, region, country)
      res = userDictionaries.affiliations.get_affiliation_address(
        affiliation, list=True)[0]
    else:
      return ''
    return res


  def ChangeContactAuthor(self, person):
    if person == '': person = '?'
    if olx.cif_model is not None:
      data_name = OV.FileName().replace(' ', '')
      data_block = olx.cif_model[data_name]
      import userDictionaries
      if person != '?':
        if type(person) == dict:
          data_block["_publ_contact_author_email"] =\
          person['email']
          data_block["_publ_contact_author_phone"] =\
            person['phone']
          data_block["_publ_contact_author_address"] =\
            person['address_display']
        else:
          userDictionaries.people.getPersonInfo(person, 'email')
          userDictionaries.people.getPersonInfo(person, 'phone')
          userDictionaries.people.getPersonInfo(person, 'address')
      else:
        data_block["_publ_contact_author_email"] = '?'
        data_block["_publ_contact_author_phone"] = '?'
        data_block["_publ_contact_author_address"] = '?'
    if type(person) == dict:
      OV.set_cif_item("_publ_contact_author_name", person['displayname'])
    else:
      OV.set_cif_item("_publ_contact_author_name", person)

  def OnContactAuthorChange(self, person_box_name):
    self.ChangeContactAuthor(
      olx.html.GetValue(person_box_name).strip())

  def OnPersonChange(self, box, edit=False):
    import userDictionaries
    if edit == "True":
      edit=True
    new_value = olx.html.GetValue(box).strip()
    person = self.make_person_box(box, edit)
    retVal = ''
    if person:
      if type(person) == dict:
        address = userDictionaries.affiliations.get_affiliation_address(
          person['affiliation'], list=False)
        person.setdefault('address_display', address)
        olx.html.SetValue(box, person['displayname'])
        retVal = person['displayname']
      else:
        olx.html.SetValue(box, person)
        retVal = person
      if "contact" in box.lower():
        self.ChangeContactAuthor(person)
      if new_value.startswith('++'):
        olx.html.Update()
    return retVal

  def OnPersonAffiliationChange(self, box, author, edit=False):
    import userDictionaries
    if edit == "True":
      edit=True
    address = self.make_affiliation_box(box, edit)
    if address:
      olx.html.SetValue(box, address[0])
      olx.html.SetItems('Person.PERSON_AFFILIATION',
        userDictionaries.affiliations.getListAffiliations())
      olx.html.SetValue('Person.PERSON_AFFILIATION', address[0])
      address_display = ("\n").join(filter(None, address))
      olx.html.SetValue('Person.PEOPLE_FORM_ADDRESS', address_display)
      OV.set_cif_item('_publ_contact_author_address', address_display)
      self.ChangePersonInfo(author, 'address', address_display)
      olx.html.Update()

  def ChangePersonInfo(self, person, item, value):
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
    if not newName:
      return

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
    value = self.OnPersonChange(box_name)
    if self.AddNameToAuthorList(value):
      olx.html.Update()

  def DisplayMergeList(self):
    l = OV.GetParam('snum.report.merge_these_cifs', [])
    if not l:
      s = "Only the built-in metacif file will be merged"
    else:
      s = ""
      for item in l:
        if not item:
          continue
        display = os.path.basename(item)
        remove = """<a target='Remove from merge'
href='spy.gui.report.publication.remove_cif_from_merge_list(%s)>>html.Update'>
<font color='red'><b>x</b></font></a>""" %item
        s += "<a target='Edit this CIF' href='shell %s'>%s</a>(%s) " %(
          item, display, remove)
    return s

  def add_cif_to_merge_list(cif_p):
    if not cif_p:
      return
    l = OV.GetParam('snum.report.merge_these_cifs', [])
    l.append(cif_p)
    OV.SetParam('snum.report.merge_these_cifs', l)

  def remove_cif_from_merge_list(cif_p):
    l = OV.GetParam('snum.report.merge_these_cifs', [])
    idx = l.index(cif_p)
    if idx != -1:
      del l[idx]
    if not l:
      l = ""
    OV.SetParam('snum.report.merge_these_cifs', l)

  def AddTemplateToMergeList(self, value=""):
    if not value:
      return
    l = OV.GetParam('snum.report.merge_these_cifs', [])
    l.append(value)
    OV.SetParam('snum.report.merge_these_cifs', l)

  def OnPublicationTemplateChange(self, value):
    value = value.strip()
    OV.SetParam('snum.report.publication_style', value.lower())
    if value == 'general':
      OV.SetParam('snum.report.publication_paper', "")
      a = OV.GetParam('snum.report.merge_these_cifs', [])
      if a:
        styles = ["_%s.cif" %(s) for s in ['acta']]
        a = [f for f in a if not s in f for s in styles]
      if not a:
        a = ""
      OV.SetParam('snum.report.merge_these_cifs', a)
      return
    copy_from = "%s/etc/CIF/cif_templates/%s.cif" %(OV.BaseDir(), value)
    copy_to = "%s/%s_%s.cif" %(OV.FilePath(), OV.FileName(), value)
    if not os.path.isfile(copy_to):
      if os.path.isfile(copy_from):
        if copy_from.lower() != copy_to.lower():
          txt = open(copy_from,'r').read().replace("FileName()", OV.FileName())
          open(copy_to,'w').write(txt)
    a = OV.GetParam('snum.report.merge_these_cifs', [])
    if copy_to not in a:
      a.append(copy_to)
      OV.SetParam('snum.report.publication_paper', a)
    OV.SetParam('snum.report.merge_these_cifs', a)
    #olx.Shell(copy_to)

  olex.registerFunction(add_cif_to_merge_list, False, "gui.report.publication")
  olex.registerFunction(remove_cif_from_merge_list, False, "gui.report.publication")


pub = publication()
olex.registerFunction(pub.OnContactAuthorChange, False, "gui.report.publication")
olex.registerFunction(pub.OnPersonChange, False, "gui.report.publication")
olex.registerFunction(pub.OnPersonAffiliationChange, False, "gui.report.publication")
olex.registerFunction(pub.OnPersonInfoChange, False, "gui.report.publication")
olex.registerFunction(pub.OnAddNameToAuthorList, False, "gui.report.publication")
olex.registerFunction(pub.OnPublicationTemplateChange, False, "gui.report.publication")
olex.registerFunction(pub.AddTemplateToMergeList, False, "gui.report.publication")
olex.registerFunction(pub.DisplayMergeList, False, "gui.report.publication")

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
  olx.Popup(pop_name, olx.BaseDir() + "/etc/gui/report-resolve-programs.htm",
   t="Missing data", b="tc",
   x=sz[0] + w/2 + sw/2, y=sz[1] + h/2 - sh/2, w=sw, h=sh, s=True)
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

def get_report_title():
  title = OV.GetParam('snum.report.title')
  if not title:
    title = OV.FileName()
  if "()" in title:
    title = olex.f(title)
  OV.SetParam('snum.report.title', title)
  return title

def play_crystal_images():
  import time
  olx.SetVar('stop_movie',False)
  l = OV.standardizeListOfPaths(OV.GetParam('snum.metacif.list_crystal_images_files'))
  current_image = OV.standardizePath(OV.GetParam('snum.report.crystal_image'))
  idx = l.index(current_image)
  for i in xrange(0,len(l)):
    if olx.GetVar('stop_movie') == "True":
      OV.SetParam('snum.report.crystal_image',l[idx])
      return
    idx = idx + 1
    if idx >= len(l):
      idx = 0
    im_path = get_crystal_image(l[idx])
    olx.html.SetImage('CRYSTAL_IMAGE',im_path)
    olx.html.SetValue('CURRENT_CRYSTAL_IMAGE', l[idx])
    OV.Refresh()
OV.registerFunction(play_crystal_images, False, 'gui.report')

def advance_crystal_image(direction='forward'):
  l = OV.standardizeListOfPaths(OV.GetParam('snum.metacif.list_crystal_images_files'))
  i = 0
  current_image = OV.standardizePath(OV.GetParam('snum.report.crystal_image'))
  for image in l:
    i += 1
    if image == current_image:
      if direction == 'forward':
        if i != len(l):
          p = l[i]
        else:
          p = l[0]
        OV.SetParam('snum.report.crystal_image',p)
        olx.html.SetImage('CRYSTAL_IMAGE',get_crystal_image(p))
        olx.html.SetValue('CURRENT_CRYSTAL_IMAGE', p)
        return
      else:
        if i != 1:
          p = l[i-2]
        else:
          p = l[len(l)-1]
        OV.SetParam('snum.report.crystal_image',p)
        olx.html.SetImage('CRYSTAL_IMAGE',get_crystal_image(p))
        olx.html.SetValue('CURRENT_CRYSTAL_IMAGE', p)
        return
    else:
      continue
OV.registerFunction(advance_crystal_image, False, 'gui.report')

def get_crystal_image(p=None,n=4,get_path_only=True):
  global images_zip
  global images_zip_name
  if not p:
    current_image = OV.GetParam('snum.report.crystal_image')
  else:
    current_image = p
  if not current_image:
    from CifInfo import ExtractCifInfo
    ExtractCifInfo(run=True)
    current_image = OV.GetParam('snum.report.crystal_image')

  if get_path_only:
    if current_image:
      if '.vzs' in current_image:
        splitbit = '.vzs/'
        directory = current_image.split(splitbit)[0] + splitbit.replace("/", "")
        if not images_zip_name == OV.FileName():
          import zipfile
          images_zip = zipfile.ZipFile(directory, "r")
          images_zip_name = OV.FileName()
        filename = current_image.split(splitbit)[1]
        content = images_zip.read(filename)
        OlexVFS.write_to_olex("crystal_image.jpg", content)
        return "crystal_image.jpg"
      else:
        return OV.standardizePath(current_image)

  if not current_image:
    print "No Current Image!"
    return None

  if '.vzs' in current_image:
    have_zip = True
    splitbit = '.vzs/'
    directory = current_image.split(splitbit)[0] + splitbit.replace("/", "")
    import zipfile
    images_zip = zipfile.ZipFile(directory, "r")
    images_zip_name = OV.FileName()
    file_list = [x for x in images_zip.filelist if x.filename.endswith('.jpg')]

  else:
    have_zip = False
    import glob
    path = OV.GetParam('snum.report.crystal_images_path')
    if not path:
      path = os.path.split(current_image)[0]
    file_list = glob.glob("%s/*.jpg" %path)
    file_list = sort_images_with_integer_names(file_list, '.jpg')

  total = len(file_list)

  if n > total:
    print "There are only %s images, and you wanted to see %s" %(total, n)
    return
  inc = int(total/n)
  for j in xrange(n):
    pos = j * inc
    if have_zip:
      content = images_zip.read(file_list[pos].filename)
    else:
      content = open(file_list[pos], 'rb').read()
    OlexVFS.write_to_olex("crystal_image_%s.jpg" %j, content)

  return "crystal_image.jpg"

OV.registerFunction(get_crystal_image, False, 'gui.report')

def get_box_x_y(w, h):
  sz = [int(x) for x in olx.GetWindowSize().split(',')]
  y = (sz[3]-sz[1]-w)/2
  x = (sz[2]-sz[0]-w)/2
  if x < 0: x = 0
  if y < 0: y = 0
  return x,y

def sort_images_with_integer_names(image_list, ending=None):
  l = []
  max_char = 0
  min_char = 1000
  for path in image_list:
    if ending and not path.endswith(ending):
      continue
    chars = len(path)
    if chars > max_char:
      max_char = chars
    if chars < min_char:
      min_char = chars
    l.append(path)

  if not l:
    return l
  def sorting_list(txt):
    try:
      cut = len(txt) - min_char + 1
      return int(txt[-(cut + 4): -4])
    except:
      return 0
  l.sort(key=sorting_list)
  return l

olex.registerFunction(get_crystal_image, False, "report")
olex.registerFunction(get_report_title, False, "report")
olex.registerFunction(ResolvePrograms, False, "report")