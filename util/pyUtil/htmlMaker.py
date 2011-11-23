import olx
import sys
import os
sys.path.append(r".\src")
import userDictionaries
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import htmlTools
import olexex_setup
import variableFunctions


def source_filesMetadataHtmlMaker():
  list = [
    {'varName':'snum.metacif.abs_file',
     'itemName':'abs %File%',
     'chooseFile':{'filter':'.abs files|*.abs'}
     },
    {'varName':'snum.metacif.pcf_file',
     'itemName':'pcf %File%',
     'chooseFile':{'filter':'.pcf files|*.pcf'}
     },
    {'varName':'snum.metacif.p4p_file',
     'itemName':'p4p %File%',
     'chooseFile':{'filter':'.p4p files|*.p4p'}
     },
    {'varName':'snum.metacif.smart_file',
     'itemName':'SMART %File%',
     'chooseFile':{'filter':'.ini files|*.ini'}
     },
    {'varName':'snum.metacif.saint_file',
     'itemName':'SAINT %File%',
     'chooseFile':{'filter':'.ini files|*.ini'}
     },
    {'varName':'snum.metacif.frames_file',
     'itemName':'%Frame% %File%',
     'chooseFile':{'filter':'All files(*.*)|*.*'}
     },
    {'varName':'snum.metacif.integ_file',
     'itemName':'%Integration% %File%',
     'chooseFile':{'filter':'._ls files|*._ls'}
     },
    {'varName':'snum.metacif.cad4_file',
     'itemName':'cad4 %File%',
     'chooseFile':{'filter':'.dat files|*.dat'}
     },
    {'varName':'snum.metacif.cif_od_file',
     'itemName':'Agilent %File%',
     'chooseFile':{'filter':'.cif_od files|*.cif_od'}
     },
    {'varName':'snum.metacif.crystal_clear_file',
     'itemName':'CrystalClear %File%',
     'chooseFile':{'filter':'CrystalClear.cif files|CrystalClear.cif'}
     },
  ]
  text = ''

  x = 0
  for i in range(len(list)):
    d = list[x]
    listFiles = 'snum.metacif.list_%s_files'  %'_'.join(
      d['varName'].split('.')[-1].split('_')[:-1])
    var = OV.GetParam(listFiles)
    if var is not None:
      if ';' in var:
        d.setdefault('items', 'spy.GetParam(%s)' %listFiles)
      x += 1
      file_type = '_'.join(d['varName'].split('.')[-1].split('_')[:-1])
      d.setdefault('onchange',"spy.SetParam(%s,'GetValue(SET_%s)')>>spy.AddVariableToUserInputList(%s)" %(d['varName'],str.upper(d['varName']).replace('.','_'),d['varName']))
      d['chooseFile'].setdefault('folder',OV.FilePath())
      d['chooseFile'].setdefault('file_type',file_type)
      d['chooseFile'].setdefault('caption',d['itemName'])
    else:
      del list[list.index(d)]

  text = htmlTools.makeHtmlTable(list)
  if text == '':
    retstr = 'No relevant files found'
  else:
    retstr = text

  return retstr
OV.registerFunction(source_filesMetadataHtmlMaker)


def currentResultFilesHtmlMaker(type='cif'):
  var = 'snum.current_result.%s' %type
  val = OV.GetParam(var)
  if not val:
    val = os.path.normpath(olx.file.ChangeExt(OV.FileFull(),type))

  list = (
    {'varName':str(var),
      'itemName':'%s File' %type,
      'value':val,
      'chooseFile':{
        'caption':'Choose %s file' %type,
        'filter':'.%s files|*.%s' %(type, type),
        'folder':'%s' %OV.FilePath(),
        'function':'spy.SetParam(%s,' %var
        },
      },
  )
  return htmlTools.makeHtmlTable(list)
OV.registerFunction(currentResultFilesHtmlMaker)

def absorption_correctionMetadataHtmlMaker():
  list = (
    {'varName':'_exptl_absorpt_correction_type',
     'items':'analytical;cylinder;empirical;gaussian;integration;multi-scan;none;numerical;psi-scan;refdelf;sphere',
     'itemName':'%Abs Type%'
     },
    {'varName':'_exptl_absorpt_process_details',
     'itemName':'%Abs Details%',
     'multiline':'multiline'
     },
    {'varName':'_exptl_absorpt_correction_T_max',
     'itemName':'%Abs T max%',
     },
    {'varName':'_exptl_absorpt_correction_T_min',
     'itemName':'%Abs T min%',
     },
  )
  return htmlTools.makeHtmlTable(list)
OV.registerFunction(absorption_correctionMetadataHtmlMaker)


def diffractionMetadataHtmlMaker():
  list = (
    {'varName':'snum.report.diffractometer',
     'readonly':'',
     'itemName':'%Diffractometer%',
     'items':userDictionaries.localList.getListDiffractometers(),
     'onchange':"spy.addToLocalList(GetValue(~name~),diffractometers)>>html.update",
     },
  )

  if OV.GetParam('snum.report.diffractometer') != '?':
    list += (
      {'varName':'snum.report.diffractometer_definition_file',
       'itemName':'%Definition File%',
       'value':userDictionaries.localList.getDiffractometerDefinitionFile(OV.GetParam('snum.report.diffractometer')),
       'chooseFile':{
         'caption':'Choose definition file',
         'filter':'.cif files|*.cif',
         'folder':'%s/etc/site' %OV.BaseDir(),
         'function':'spy.setDiffractometerDefinitionFile(spy.GetParam(snum.report.diffractometer),'
         },
       },
    )

  list += (
    {'varName':'_diffrn_ambient_temperature',
     'itemName':'%Diffraction T% (K)'
     },
    {'varName':'_cell_measurement_temperature',
     'itemName':'%Cell Measurement T% (K)'
     },
    {'varName':'_diffrn_special_details',
     'itemName':'%Special Details%',
     'multiline':'multiline'
     }
  )

  return htmlTools.makeHtmlTable(list)
OV.registerFunction(diffractionMetadataHtmlMaker)

def crystalMetadataHtmlMaker():
  list = (
    {'varName':'_chemical_name_systematic',
     'itemName':'%Systematic Name%',
     },
    {'varName':'_exptl_crystal_colour',
     'itemName':'%Colour%',
     'box1':{'varName':'_exptl_crystal_colour_lustre',
             'items':'?;.;metallic;dull;clear'
             },
     'box2':{'varName':'_exptl_crystal_colour_modifier',
             'items':'?;.;light;dark;whitish;blackish;grayish;brownish;reddish;pinkish;orangish;yellowish;greenish;bluish'
             },
     'box3':{'varName':'_exptl_crystal_colour_primary',
             'items':'?;colourless;white;black;gray;brown;red;pink;orange;yellow;green;blue;violet'
             },
     },
    {'varName':'_exptl_crystal_size',
     'itemName':'%Size%',
     'box1':{'varName':'_exptl_crystal_size_min',
             'width':'50'
             },
     'box2':{'varName':'_exptl_crystal_size_mid',
             'width':'50'
             },
     'box3':{'varName':'_exptl_crystal_size_max',
             'width':'50'
             },
     },
    {'varName':'_exptl_crystal_description',
     'itemName':'%Shape%',
     'items':'?;block;plate;needle;prism;irregular;cube;trapezoid;rect. Prism;rhombohedral;hexagonal;octahedral',
     },
    {'varName':'_exptl_crystal_preparation',
     'itemName':'%Preparation Details%',
     'multiline':'multiline',
     },
    {'varName':'_exptl_crystal_recrystallization_method',
     'itemName':'%Crystallisation Details%',
     'multiline':'multiline',
     },
    {'varName':'snum.report.crystal_mounting_method',
     'itemName':'%Crystal Mounting%',
     'multiline':'multiline',
     },
  )

  return htmlTools.makeHtmlTable(list)
OV.registerFunction(crystalMetadataHtmlMaker)

def collectionMetadataHtmlMaker():
  list = (
    {'varName':'snum.report.submitter',
     'itemName':'%Submitter%',
     'items':userDictionaries.people.getListPeople(),
     'readonly':'',
     'onchange':"spy.SetParam(snum.report.submitter,GetValue(~name~))>>spy.addNewPerson(GetValue(~name~))>>html.update",
     },
    {'varName':'snum.report.operator',
     'itemName':'%Operator%',
     'items':userDictionaries.people.getListPeople(),
     'readonly':'',
     'onchange':"spy.SetParam(snum.report.operator,GetValue(~name~))>>spy.addNewPerson(GetValue(~name~))>>html.update",
     },
    {'varName':'snum.report.date_submitted',
     'itemName':'%Date Submitted%',
     },
    {'varName':'snum.report.date_collected',
     'itemName':'%Date Collected%',
     },
  )

  return htmlTools.makeHtmlTable(list)
OV.registerFunction(collectionMetadataHtmlMaker)

def progressMetadataHtmlMaker():
  list = (
    {'varName':'snum.dimas.progress_status',
     'itemName':'%Status%',
     'items':'No Entry;Aborted;Rejected;Withdrawn;Lost;In Queue;Collecting;Reduction;Solving;Refining;Pending;Processing;Finishing;Finished;Publishing;Published;Published Duplicate;Known structure'
     },
    {'varName':'snum.dimas.progress_comment',
     'itemName':'%Comment%',
     'multiline':'multiline'
     },
  )
  return htmlTools.makeHtmlTable(list)
OV.registerFunction(progressMetadataHtmlMaker)

def referenceMetadataHtmlMaker():
  list = (
    {'varName':'snum.dimas.reference_csd_refcode',
     'itemName':'%CSD% %Refcode%',
     },
    {'varName':'snum.dimas.reference_publ_authors',
     'itemName':'%Authors%',
     },
    {'varName':'snum.dimas.reference_journal_name',
     'itemName':'%Journal%',
     'items':userDictionaries.localList.getListJournals()
     },
    {'varName':'snum.dimas.reference_journal_volume',
     'itemName':'%Volume%',
     },
    {'varName':'snum.dimas.reference_journal_pages',
     'itemName':'%Pages%',
     },
    {'varName':'snum.dimas.reference_journal_year',
     'itemName':'%Year%',
     },
    {'varName':'snum.dimas.reference_comment',
     'itemName':'%Comment%',
     'multiline':'multiline'
     },
  )
  return htmlTools.makeHtmlTable(list)
OV.registerFunction(referenceMetadataHtmlMaker)

def publicationMetadataHtmlMaker():
  list = [
    {'varName':'_database_code_depnum_ccdc_archive',
     'itemName':'CCDC %Number%',
     },
    {'varName':'_publ_contact_author_name',
     'itemName':'%Contact% %Author%',
     'items':userDictionaries.people.getListPeople(),
     'readonly':'',
     'onchange':'spy.gui.report.publication.OnContactAuthorChange(~name~)',
     },
    {'varName':'_publ_contact_author_address',
     'itemName':'%Contact% %Author% %Address%',
     'multiline':'multiline',
     'value':'spy.getPersonInfo(GetValue(SET__PUBL_CONTACT_AUTHOR_NAME),address)',
     'onchange':'spy.gui.report.publication.OnPersonInfoChange(SET__PUBL_CONTACT_AUTHOR_NAME,address,~name~)'
     },
    {'varName':'_publ_contact_author_email',
     'itemName':'%Contact% %Author% %Email%',
     'value':'spy.getPersonInfo(GetValue(SET__PUBL_CONTACT_AUTHOR_NAME),email)',
     'onchange':'spy.gui.report.publication.OnPersonInfoChange(SET__PUBL_CONTACT_AUTHOR_NAME,email,~name~)'
     },
    {'varName':'_publ_contact_author_phone',
     'itemName':'%Contact% %Author% %Phone%',
     'value':'spy.getPersonInfo(GetValue(SET__PUBL_CONTACT_AUTHOR_NAME),phone)',
     'onchange':'spy.gui.report.publication.OnPersonInfoChange(SET__PUBL_CONTACT_AUTHOR_NAME,phone,~name~)'
     },
#    {'varName':'InfoLine',
#     'itemName':'%Contact% %Author% %Phone%',
#     'value':'Authors to appear on paper. If the contact author should appear, the name needs to be added here.',
#     },
  ]
  listAuthors = OV.GetParam('snum.metacif.publ_author_names')
  if listAuthors is None:
    numberAuthors = 0
  else:
    numberAuthors = len(listAuthors.split(';'))
  for i in range(1,numberAuthors+1):
    authorRow = {
      'varName':'snum.metacif.publ_author_names',
      'ctrl_name':'SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s' %i,
      'readonly':'readonly',
      'value':"%s" %listAuthors.split(';')[i-1],
      'bgcolor':"%s" %OV.GetParam('gui.html.table_bg_colour'),
      'onchange':""
    }
    if numberAuthors == 1:
      authorRow.setdefault('itemName','')
      authorRow.setdefault('field1',{'itemName':'%Author%'})
      authorRow.setdefault('field2',{'itemName':'<a href="spy.move(del,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.update" target="Remove author from list"><zimg border="0" src="delete.png"></a>' %str(i),
                                     'fieldALIGN':'right'})

    elif i == 1:
      authorRow.setdefault('itemName','')
      authorRow.setdefault('field1',{'itemName':'%Authors%'})
      authorRow.setdefault('field2',{'itemName':'<zimg border="0" src="toolbar-up-off.png"><a href="spy.move(down,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.update" target="Move author down list"><zimg border="0" src="toolbar-down.png"></a> <a href="spy.move(del,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.update" target="Remove author from list"><zimg border="0" src="delete.png"></a>' %(str(i),str(i)),
                                     'fieldALIGN':'right'})
    elif i == numberAuthors:
      authorRow.setdefault('itemName','<a href="spy.move(up,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.update" target="Move author up list"><zimg border="0" src="toolbar-up.png"></a><zimg border="0" src="toolbar-down-off.png"><a href="spy.move(del,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.Update" target="Remove author from list"><zimg border="0" src="delete.png"></a>' %(str(i),str(i)))
      authorRow.setdefault('fieldALIGN','right')
      authorRow['bgcolor'] = OV.GetParam('gui.html.input_bg_colour')
    else:
      authorRow.setdefault('itemName','<a href="spy.move(up,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.Update" target="Move author up list"><zimg border="0" src="toolbar-up.png"></a> <a href="spy.move(down,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.Update" target="Move author down list"><zimg border="0" src="toolbar-down.png"></a> <a href="spy.move(del,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.Update" target="Remove author from list"><zimg border="0" src="delete.png"></a>' %(str(i),str(i),str(i)))
      authorRow.setdefault('fieldALIGN','right')

    list.append(authorRow)
  if numberAuthors > 0:
    s = '_' + str(numberAuthors)
    list.append(
      {'varName':'publ_author_address',
       'itemName':'%Author% %Address%',
       'multiline':'multiline',
       'value':'spy.getPersonInfo(GetValue(SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s),address)' %s,
       'onchange':'spy.changePersonInfo(GetValue(SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s),address,GetValue(~name~))>>spy.changeBoxColour(~name~,#FFDCDC)' %s
       }
    )
    list.append(
      {'varName':'publ_author_email',
       'itemName':'%Author% %Email%',
       'value':'spy.getPersonInfo(GetValue(SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s),email)' %s,
       'onchange':'spy.changePersonInfo(GetValue(SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s),email,GetValue(~name~))>>spy.changeBoxColour(~name~,#FFDCDC)' %s
       }
    )
  list.append(
    {'varName':'snum.metacif.publ_author_names',
     'ctrl_name':'ADD_PUBL_AUTHOR_NAME',
     'readonly':'',
     'itemName':'%Add% %Author%',
     'items':userDictionaries.people.getListPeople(),
     'value':'?',
     'onchange':"spy.gui.report.publication.OnAddNameToAuthorList(~name~)",
     }
  )

  for d in list:
    d.setdefault('ctrl_name','SET_%s' %str.upper(d['varName']).replace('.','_'))
    if 'ctrl_name' in d['varName']:
      d.setdefault('onchange',"spy.SetParam(%(varName)s,GetValue(~name~))>>spy.changeBoxColour(~name~,#FFDCDC)>>html.Update" %d)
    elif 'author_name' in d['varName']:
      d.setdefault('onchange','')
  retstr = htmlTools.makeHtmlTable(list)

  list = [
    {'varName':'_publ_requested_journal',
     'itemName':'%Requested% %Journal%',
     'items':userDictionaries.localList.getListJournals(),
     'readonly':'',
     'value':'spy.get_cif_item(_publ_requested_journal)',
     'onchange':'spy.addToLocalList(GetValue(~name~),requested_journal)>>spy.changeBoxColour(~name~,#FFDCDC)',
     }
  ]

  retstr += htmlTools.makeHtmlTable(list)

  retstr +="""
<tr VALIGN="center" ALIGN="left">
  <td></td>
  <td VALIGN="center" width="40%%" colspan=2>
    <a href="spy.contactLetter()>>html.Update" target="Edit Contact Letter"><b>Contact Letter</b></a>
  </td>
</tr>
"""

  retstr +="""
<tr VALIGN="center" ALIGN="left">
  <td></td>
  <td VALIGN="center" colspan=3 bgcolor=$spy.GetParam(gui.html.highlight_colour)>
    <b>Please add the contact author to the list of Authors if that person is to appear on the paper!</b></a>
  </td>
</tr>
"""
  
  return retstr
OV.registerFunction(publicationMetadataHtmlMaker)

def contactLetter():
  letterText = OV.get_cif_item('_publ_contact_letter','?','gui')
  if letterText is None:
    import datetime
    today = datetime.date.today()
    date = today.strftime("%x")
    journal = OV.get_cif_item('_publ_requested_journal')
    fileName = olx.FileName()
    authorList = OV.GetParam('snum.metacif.publ_author_names')
    authors = ''
    if authorList is None:
      numberAuthors = 0
    else:
      authorList = authorList.split(';')
      numberAuthors = len(authorList)
    for i in range(numberAuthors):
      author = authorList[i]
      if ',' in author:
        a = author.split(',')
        surname = a[0]
        initials = ''
        for forename in a[1].split():
          initials += '%s.' %forename[0].upper()
      else:
        a = author.split()
        surname = a[-1]
        initials = ''
        for forename in a[:-1]:
          initials += '%s.' %forename[0].upper()

      if i < numberAuthors - 2:
        authorAbbrev = initials + surname + ', '
      elif i == numberAuthors - 2:
        authorAbbrev = initials + surname + ' and '
      elif i > numberAuthors - 2:
        authorAbbrev = initials + surname
      authors += authorAbbrev
    letterText = """Date of submission %s

The CIF file contains data for the structure %s from
the paper 'ENTER PAPER TITLE' by
%s.
The paper will be submitted to %s.
""" %(date,fileName,authors,journal)

  inputText = OV.GetUserInput(0,'_publ_contact_letter',letterText)
  if inputText is not None:
    OV.set_cif_item('_publ_contact_letter', inputText);
  return ""
OV.registerFunction(contactLetter)

def move(arg,name):
  listNames = OV.GetParam('snum.metacif.publ_author_names').split(';')
  name_i = olx.GetValue(name)
  i = listNames.index(name_i)

  if arg.lower() == 'up':
    if i != 0:
      name_i_minus_1 = listNames[i-1]
      listNames[i] = name_i_minus_1
      listNames[i-1] = name_i
    else:
      pass

  elif arg.lower() == 'down':
    try:
      name_i_plus_1 = listNames[i+1]
      listNames[i] = name_i_plus_1
      listNames[i+1] = name_i
    except:
      pass

  elif arg in ('del','DEL'):
    del listNames[i]

  names = ';'.join(listNames)
  OV.SetParam('snum.metacif.publ_author_names', names)

  return ''
OV.registerFunction(move)

def restraint_builder(cmd):
  height = OV.GetParam('gui.html.combo_height')
  colspan = 6

  constraints = ["EXYZ", "EADP", "AFIX"]
  olex_conres = ["RRINGS", "TRIA"]

  html = []
  atom_pairs =  {
    "DFIX":["name_DFIX", "var_d: ", "var_s:0.02", "help_DFIX-use-help"],
    "DANG":["name_DANG", "var_d: ", "var_s:0.04", "help_Select atom pairs"],
    "SADI":["name_SADI", "var_s:0.02", "help_SADI-use-help"],
  }

  atom_names =  {
    "SAME":["name_SAME", "var_s1:0.02", "var_s2:0.02", "help_Select any number of atoms"],
    "CHIV":["name_CHIV", "var_V:0", "var_s:0.1", "help_Select any number of atoms"],
    "FLAT":["name_FLAT", "var_s1:0.1", "help_Select at least four atoms"],
    "DELU":["name_DELU", "var_s1:0.01", "var_s2:0.01", "help_Select any number of atoms"],
    "SIMU":["name_SIMU", "var_s:0.04", "var_st:0.08", "var_dmax:1.7", "help_Select any number of atoms"],
    "ISOR":["name_ISOR", "var_s:0.1", "var_st:0.2", "help_Select any number of atoms"],
    "EXYZ":["name_EXYZ", "help_exyz-htmhelp"],
    "EADP":["name_EADP", "help_eadp-htmhelp"],
    "AFIX":["name_AFIX", "var_m:6;5;10;11", "var_n:6;9", "help_AFIX-use-help"],
#    "RRINGS":["name_RRINGS", "var_d:1.39 ", "var_s1:0.02", "help_rrings-htmhelp"],
    "RRINGS":["name_RRINGS", "help_rrings-htmhelp"],
    "TRIA":["name_TRIA", "var_distance: ", "var_angle: ", "help_tria-htmhelp"],
  }

  if atom_pairs.has_key(cmd):
    l = atom_pairs[cmd]
  elif atom_names.has_key(cmd):
    l = atom_names[cmd]
  else:
    return "Please atoms and restraint, then press GO"
  onclick = ""
  pre_onclick = ""
  post_onclick = ""
  html_help = "Click on the help link for more info"
  itemcount = 0
  items = None
  var = None
  for item in l:
    itemcount += 1
    id = item.split("_")[0]
    tem = item.split("_")[1]
    if ":" in tem:
      var = tem.split(":")[0]
      val = tem.split(":")[1]
    if id == "name":
      name = tem
      onclick += "%s " %name
    elif id == "help":
      html_help = OV.TranslatePhrase(tem)
      html_help, d = htmlTools.format_help(html_help)
    elif id == "var":
      ctrl_name = "%s_%s_TEXT_BOX" %(name, var)
      pre_onclick += "SetVar\(%s_value,GetValue\(%s))>>" %(ctrl_name,ctrl_name)
      onclick += "GetValue\(%s) " %ctrl_name
      if val == " ":
        val = "$GetVar(%s_value,'')" %ctrl_name
      elif ';' in val:
        items = val
        val = items.split(';')[0]
      else:
        items = None
        val = val.strip()
      if items:
        width = 50
      else:
        width=50
      if var == "d":
        width=50
      d = {"ctrl_name":ctrl_name,
           "label":var,
           "valign":'center',
           "value":val,
           "width":width,
           "height":height,
           "bgcolor":"$spy.GetParam(gui.html.input_bg_colour)"
           }
      if items:
        d.setdefault("items",items)
      if var:
        html.append("<td width='15%%'>%s</td>" %htmlTools.makeHtmlInputBox(d))

  if name == "AFIX":
    itemcount += 2
    onclick_list = onclick.strip().split(' ')
    onclick = 'AFIX strcat\(%s,%s)' %(onclick_list[1],onclick_list[2])
    post_onclick = '>>labels -a'
    mode_ondown = "mode %s" %(onclick.replace('AFIX ','HFIX '))
    mode_onup = "mode off>>sel -u"
    mode_button_d = {
      "name":'AFIX_MODE',
      "value":"Mode",
      "ondown":"%s"%mode_ondown,
      "onup":"%s"%mode_onup,
      "width":50, "height":height,
      "hint":"Atoms subsequently clicked will become the pivot atom of a new rigid group",
    }
    clear_onclick = "sel atoms where xatom.afix==strcat\(%s,%s)>>Afix 0>>labels -a" %(onclick_list[1],onclick_list[2])
    clear_button_d = {
      "name":'AFIX_CLEAR',
      "value":"Clear",
      "onclick":"%s"%clear_onclick,
      "width":50, "height":height,
      "hint":"Removes the current AFIX command from the structure",
    }

  if name == "RRINGS":
    post_onclick = ">>sel -u"

  has_modes = []
  if name in has_modes:
    if haveSelection():
      onclick += " sel"
    else:
      onclick = "mode %s" %onclick
  else:
    onclick += " sel"

  onclick = "%s%s%s" %(pre_onclick, onclick, post_onclick)

  button_d = {
    "name":'%s_GO' %name,
    "value":"GO",
    "onclick":"%s"%onclick,
    "width":30,
    "height":28,
    "hint":"The %s command will be applied to all currently selected atoms" %name
  }
  if itemcount < colspan:
    html.append("<td></td>"*(colspan-itemcount)) # Space-filler
  if name == 'AFIX':
    html.append("<td width='25%%' align='right'>$spy.MakeHoverButton(button_small-clear@Afix,%s)</td>" %clear_onclick)
    html.append("<td width='25%%' align='right'>$spy.MakeHoverButton(button_small-mode@Afix,%s)</td>" %mode_ondown)

  html.append("<td width='25%%' align='right'>$spy.MakeHoverButton(button_small-go@%s,%s)</td>" %(name, onclick))

  #Add the help info as the last row in the table
  html.append("</td></tr><tr>")
  html.append(htmlTools.make_table_first_col(help_name=name, popout=True, help_image='normal'))
  html.append("<td colspan=%s bgcolor='%s'>%s</td></tr>" %(colspan, OV.GetParam('gui.html.table_firstcol_colour'), html_help, ))
  if name in constraints:
    wFilePath = r"constraint-vars.htm"
  elif name in olex_conres:
    wFilePath = r"olex-conres-vars.htm"
  else:
    wFilePath = r"restraint-vars.htm"

  OV.write_to_olex(wFilePath, '\n'.join(html))
  OV.UpdateHtml()
  return "Done"
OV.registerFunction(restraint_builder)

have_found_python_error = False

def checkErrLogFile():
  logfile = "%s/PythonError.log" %OV.DataDir()
  logfile = logfile.replace("\\\\", "\\")
  global have_found_python_error
  if not have_found_python_error:
    f = open(logfile, 'r')
    if len(f.readlines()) > 0:
      have_found_python_error = True
    f.close()
  if have_found_python_error:
    return '''
    <a href='external_edit "%s"'>
    <zimg border='0' src='toolbar-stop.png'></a>
    '''%(logfile)
  else: return ""
OV.registerFunction(checkErrLogFile)

def weightGuiDisplay():
  if olx.IsFileType('ires').lower() == 'false':
    return ''
  gui_green = OV.GetParam('gui.green')
  gui_orange = OV.GetParam('gui.orange')
  gui_red = OV.GetParam('gui.red')
  longest = 0
  retVal = ""
  current_weight = olx.Ins('weight')
  if current_weight == "n/a": return ""
  current_weight = current_weight.split()
  if len(current_weight) == 1:
    current_weight = [current_weight[0], '0']
  length_current = len(current_weight)
  suggested_weight = OV.GetParam('snum.refinement.suggested_weight')
  if suggested_weight is None: suggested_weight = []
  if len(suggested_weight) < length_current:
    for i in xrange (length_current - len(suggested_weight)):
      suggested_weight.append(0)
  if suggested_weight:
    for curr, sugg in zip(current_weight, suggested_weight):
      curr = float(curr)
      if round(curr, 4) == round(sugg, 4):
        colour = gui_green
      elif curr-curr*0.1 < sugg < curr+curr*0.1:
        colour = gui_orange
      else:
        colour = gui_red
      retVal += "<font size='2' color='%s'>%.4f(%.4f)</font> | " %(colour, curr, sugg)
    html_scheme = retVal.strip("| ")
  else:
    html_scheme = current_weight

  d = {'ctrl_name':'SET_SNUM_REFINEMENT_UPDATE_WEIGHT',
       'checked':OV.GetParam('snum.refinement.update_weight'),
       'oncheck':'spy.SetParam(snum.refinement.update_weight,true)',
       'onuncheck':'spy.SetParam(snum.refinement.update_weight,false)',
       'bgcolor':'spy.GetParam(gui.html.table_firstcol_colour)',
       'value':'',
       }
  box = htmlTools.make_tick_box_input(d)

  wght_str = ""
  for i in suggested_weight:
    wght_str += " %.4f" %i
  txt_tick_the_box = OV.TranslatePhrase("Tick the box to automatically update")
  txt_Weight = OV.TranslatePhrase("Weight")
  html = '''
<tr VALIGN='center' ALIGN='left' NAME='SNUM_REFINEMENT_UPDATE_WEIGHT'>
  <td width="2" bgcolor="$spy.GetParam(gui.html.table_firstcol_colour)"></td>
  <td VALIGN='right' colspan=3>
    <b><a target="%s" href="UpdateWght%s>>html.Update">%s: %s</a></b></td>
    <td VALIGN='center' ALIGN='right' colspan=1>%s</td>
</tr>
    ''' %(txt_tick_the_box, wght_str, txt_Weight, html_scheme, box)
  return html
OV.registerFunction(weightGuiDisplay)

def getCellHTML():
  crystal_systems = {
    'Triclinic':('a', 'b', 'c', '&alpha;', '&beta;', '&gamma;'),
    'Monoclinic':('a', 'b', 'c', '&beta;'),
    'Orthorhombic':('a', 'b', 'c'),
    'Tetragonal':('a', 'c',),
    'Hexagonal':('a', 'c'),
    'Trigonal':('a', 'c'),
    'Cubic':('a',),
  }

  cell_param_value_pairs = dict(zip(
    ('a', 'b', 'c', '&alpha;', '&beta;', '&gamma;'),
    ('_cell_length_a','_cell_length_b','_cell_length_c','_cell_angle_alpha','_cell_angle_beta','_cell_angle_gamma')))
  cell = {}
  for param, value in cell_param_value_pairs.items():
    if param in ('a','b','c'):
      cell[param] = dict(
        value = '%%%s%%' %value,
        unit = '&nbsp;&Aring;'
      )
    else:
      cell[param] = dict(
        value = '%%%s%%' %value,
        unit = '&deg;'
      )

  cell_html = dict((param, '<i>%s</i>&nbsp;= %s%s, ' %(param,cell[param]['value'],cell[param]['unit'])) for param in cell.keys())

  crystal_system = OV.olex_function('sg(%s)')

  html = ''.join(cell_html[param] for param in crystal_systems[crystal_system])

  return html
OV.registerFunction(getCellHTML)

def refineDataMaker():

  txt = """
<tr><td>R1(Fo > 4sig(Fo))</td><td>0.0511</td><td>R1(all data)</td><td>0.0690</td></tr>
<tr><td>wR2</td><td>0.1138</td><td>GooF</td><td>1.16</td></tr>
<tr><td>GooF(Restr)</td><td>1.16</td><td>Highest peak</td><td>0.32</td></tr>
<tr><td>Deepest hole</td><td>-0.32</td><td>Params</td><td>216</td></tr>
<tr><td>Refs(total)</td><td>6417</td><td>Refs(uni)</td><td>2803</td></tr>
<tr><td>Refs(Fo > 4sig(Fo))</td><td>2366</td><td>R(int)</td><td>0.061</td></tr>
<tr><td>R(sigma)</td><td>0.055</td><td>F000</td><td>364</td></tr>
<tr><td>&rho;/g*mm<sup>-3</sup></td><td>1.574</td><td>&mu;/mm<sup>-1</sup></td><td>0.140</td></tr>
"""
  OV.write_to_olex("refinedata.htm", txt)
  OV.UpdateHtml()
OV.registerFunction(refineDataMaker)
