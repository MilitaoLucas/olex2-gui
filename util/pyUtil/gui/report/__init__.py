import olex
import olx
import os
import OlexVFS
import gui
import inspect

from olexFunctions import OV
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

  def OnPersonChange(self, box, param=None, person_id=None):
    import userDictionaries
    from  gui.db import userdb
    #pid = int(olx.html.GetValue(box))
    new = False
    if person_id:
      person = userdb.db.getPerson(int(person_id))
    else:
      person = userdb.db.Manage()
      new=True
    if person:
      rv = person.get_display_name()
      if new:
        olx.html.SetValue(box, rv)
      if param:
        OV.SetParam(param, person.id)
      return rv
    return None

  def ChangePersonInfo(self, person, item, value):
    if value == '': value = '?'
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
        print("%s is already in the list of authors" %newName)
      else:
        newValue = "%s;%s" %(oldValue, newName)
        changed = True
    if changed:
      OV.SetParam("snum.metacif.publ_author_names", newValue)
    return changed

  def OnAddNameToAuthorList(self, box_name,person_id=None):
    value = self.OnPersonChange(box_name, person_id=person_id)
    if self.AddNameToAuthorList(value):
      olx.html.Update()

  def DisplayMergeList(self):
    ciflist = OV.GetCifMergeFilesList()
    if not ciflist:
      s = "Only the built-in metacif file will be merged"
    else:
      s = ""
      for item in ciflist:
        if not item:
          continue
        display = os.path.basename(item)
        remove = """<a target='Remove from merge'
href='spy.gui.report.publication.remove_cif_from_merge_list("%s")>>html.Update'>
<font color='red'><zimg src='delete_small.png'></font></a>""" %item
        s += "<a target='Edit this CIF' href='shell %s'>%s</a>(%s) " %(
          item, display, remove)
    return s

  def add_cif_to_merge_list(cif_p):
    if not cif_p:
      return
    if not os.path.exists(cif_p):
      return
    ciflist = OV.GetCifMergeFilesList()
    if cif_p not in ciflist:
      ciflist.append(cif_p)
      OV.SetParam('snum.report.merge_these_cifs', ciflist)

  def remove_cif_from_merge_list(cif_p):
    ciflist = OV.GetCifMergeFilesList()
    idx = ciflist.index(cif_p)
    if idx != -1:
      del ciflist[idx]
    if not ciflist:
      ciflist = ""
    OV.SetParam('snum.report.merge_these_cifs', ciflist)

  def AddTemplateToMergeList(self, value=""):
    if not value:
      return
    ciflist = OV.GetCifMergeFilesList()
    if value not in ciflist:
      ciflist.append(value)
    OV.SetParam('snum.report.merge_these_cifs', ciflist)

  def OnPublicationTemplateChange(self, value):
    value = value.strip()
    OV.SetParam('snum.report.publication_style', value.lower())
    if value == 'general':
      OV.SetParam('snum.report.publication_paper', "")
      ciflist = OV.GetCifMergeFilesList()
      if ciflist:
        styles = ["_%s.cif" %(s) for s in ['acta']]
        ciflist = [f for f in ciflist if not s in f for s in styles]
      if not ciflist:
        ciflist = ""
      OV.SetParam('snum.report.merge_these_cifs', ciflist)
      return
    copy_from = "%s/etc/CIF/cif_templates/%s.cif" %(OV.BaseDir(), value)
    copy_to = "%s/%s_%s.cif" %(OV.FilePath(), OV.FileName(), value)
    if not os.path.isfile(copy_to):
      if os.path.isfile(copy_from):
        if copy_from.lower() != copy_to.lower():
          txt = open(copy_from,'r').read().replace("FileName()", OV.FileName())
          open(copy_to,'w').write(txt)
    ciflist = OV.GetCifMergeFilesList()
    if copy_to not in ciflist:
      ciflist.append(copy_to)
      OV.SetParam('snum.report.publication_paper', ciflist)
    OV.SetParam('snum.report.merge_these_cifs', ciflist)
    #olx.Shell(copy_to)

  olex.registerFunction(add_cif_to_merge_list, False, "gui.report.publication")
  olex.registerFunction(remove_cif_from_merge_list, False, "gui.report.publication")


pub = publication()
olex.registerFunction(pub.OnPersonChange, False, "gui.report.publication")
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
  hs = History.tree
  if not hs:
    return True
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
   x=sz[0] + w//2 + sw//2, y=sz[1] + h//2 - sh//2, w=sw, h=sh, s=True)
  res = olx.html.ShowModal(pop_name)
  if not res or int(res) == 1:
    return False
  if hs.active_child_node:
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
  imagelist = OV.standardizeListOfPaths(OV.GetParam('snum.metacif.list_crystal_images_files'))
  current_image = OV.standardizePath(OV.GetParam('snum.report.crystal_image'))
  idx = imagelist.index(current_image)
  for i in range(0,len(imagelist)):
    if olx.GetVar('stop_movie') == "True":
      OV.SetParam('snum.report.crystal_image',imagelist[idx])
      return
    idx = idx + 1
    if idx >= len(imagelist):
      idx = 0
    im_path = get_crystal_image(imagelist[idx])
    olx.html.SetImage('CRYSTAL_IMAGE',im_path)
    olx.html.SetValue('CURRENT_CRYSTAL_IMAGE', imagelist[idx])
    OV.Refresh()
OV.registerFunction(play_crystal_images, False, 'gui.report')

def advance_crystal_image(direction='forward'):
  imagelist = OV.standardizeListOfPaths(OV.GetParam('snum.metacif.list_crystal_images_files'))
  i = 0
  current_image = OV.standardizePath(OV.GetParam('snum.report.crystal_image'))
  for image in imagelist:
    i += 1
    if image == current_image:
      if direction == 'forward':
        if i != len(imagelist):
          p = imagelist[i]
        else:
          p = imagelist[0]
        OV.SetParam('snum.report.crystal_image',p)
        olx.html.SetImage('CRYSTAL_IMAGE',get_crystal_image(p))
        olx.html.SetValue('CURRENT_CRYSTAL_IMAGE', p)
        return
      else:
        if i != 1:
          p = imagelist[i-2]
        else:
          p = imagelist[len(imagelist)-1]
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
    current_image = OV.standardizePath(OV.GetParam('snum.report.crystal_image'))
  else:
    current_image = p
  if not current_image:
    from CifInfo import ExtractCifInfo
    ExtractCifInfo(run=True)
    current_image = OV.standardizePath(OV.GetParam('snum.report.crystal_image'))

  if get_path_only:
    if current_image:
      if '.vzs' in current_image:
        splitbit = '.vzs'
        directory = current_image.split(splitbit)[0] + splitbit
        if not images_zip_name == OV.FileName():
          import zipfile
          images_zip = zipfile.ZipFile(directory, "r")
          images_zip_name = OV.FileName()
        filename = current_image.split(splitbit)[1][1:]
        content = images_zip.read(filename)
        OlexVFS.write_to_olex("crystal_image.jpg", content)
        return "crystal_image.jpg"
      else:
        return OV.standardizePath(current_image)

  if not current_image:
#    print "No Current Image!"
    return None

  if '.vzs' in current_image:
    have_zip = True
    splitbit = '.vzs'
    directory = current_image.split(splitbit)[0] + splitbit
    if not os.path.exists(directory):
      print("The path %s should have existed. It does not" %directory)
      return None
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
    print(("There are only %s images, and you wanted to see %s" %(total, n)))
    return
  inc = int(total/n)
  for j in range(n):
    pos = j * inc
    if have_zip:
      content = images_zip.read(file_list[pos].filename)
    else:
      content = open(file_list[pos], 'rb').read()
    OlexVFS.write_to_olex("crystal_image_%s.jpg" %j, content)

  return "crystal_image.jpg"

OV.registerFunction(get_crystal_image, False, 'gui.report')

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


def remove_from_citation_list(item):
  try:
    current_refs = OV.get_cif_item('_publ_section_references', '').split('\n\n')
    idx = current_refs.index(item)
    if idx != -1:
      del current_refs[idx]
    if not current_refs:
      l = ""
    OV.set_cif_item('_publ_section_references','\n\n'.join(current_refs))
  except Exception as err:
    print(("Error in 'report.remove_from_citation: %s" %err))
OV.registerFunction(remove_from_citation_list, False, "report")

def add_to_citation_list(item):
  try:
    current_refs = OV.get_cif_item('_publ_section_references', '').split('\n\n')
    if item in current_refs:
      return
    new_list = [item]
    for item in current_refs:
      new_list.append(item)
    new_list.sort()
    OV.set_cif_item('_publ_section_references','\n\n'.join(new_list))
  except Exception as err:
    print(("Error in 'report.add_to_citation: %s" %err))
OV.registerFunction(add_to_citation_list, False, "report")

def get_reflections_stats_dictionary():
  import olex_core
  d_aliases = {
    "DataCount": "DataCount",
    "TotalReflections": "Total reflections (after filtering)",
    "UniqueReflections": "Unique reflections",
    "Completeness": "Completeness",
    "MeanIOverSigma": "Mean I/&sigma;",
    "FileMaxIndexes": "hkl<sub>max</sub> collected",
    "FileMinIndexes": "hkl<sub>min</sub> collected",
    "MaxIndexes": "hkl<sub>max</sub> used",
    "MinIndexes": "hkl<sub>min</sub> used",
    "LimDmax": "Lim d<sub>max</sub> collected",
    "LimDmin": "Lim d<sub>min</sub> collected",
    "MaxD": "d<sub>max</sub> used",
    "MinD": "d<sub>min</sub> used",
    "FriedelPairCount": "Friedel pairs",
    "FriedelOppositesMerged": "Friedel pairs merged",
    "InconsistentEquivalents": "Inconsistent equivalents",
    "Rint": "R<sub>int</sub>",
    "Rsigma": "R<sub>sigma</sub>",
    "IntensityTransformed": "Intensity transformed",
    "OmittedReflections": "Omitted reflections",
    "OmittedByUser": "Omitted by user (OMIT hkl)",
    "Redundancy": "Multiplicity",
    "ReflectionAPotMax": "Maximum multiplicity",
    "SystematicAbsencesRemoved": "Removed systematic absences",
    "FilteredOff": "Filtered off (SHEL/OMIT)"
  }
  stats = olex_core.GetHklStat()
  d = {}
  for item in stats:
    d.setdefault(item, {"value": stats[item], "html_item": d_aliases[item]})
  return d

def create_report():
  try:
    ac4i = None
    import AC6 as ac6
    try:
      ac4i = ac6.AC_instance
    except:
      ac4i = ac6.AC6.AC_instance
    if ac4i.HasAC():
      try:
        olex.m('spy.ac6.create_report()')
      except:
        print("Tried to make AC6 report and failed. Making default report instead")
        olex.m("report")
    else:
      olex.m("report")
  except Exception as e:
    print("Failed to make a report: %s" %str(e))

olex.registerFunction(create_report, False, "gui")
olex.registerFunction(get_crystal_image, False, "report")
olex.registerFunction(get_report_title, False, "report")
olex.registerFunction(ResolvePrograms, False, "report")
olex.registerFunction(get_reflections_stats_dictionary, False, "report")
