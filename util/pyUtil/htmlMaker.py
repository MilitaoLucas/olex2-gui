import olx
import sys
sys.path.append(r".\src")
import userDictionaries
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import htmlTools
import olexex_setup
import variableFunctions

def sourceFilesHtmlMaker():
  list = [
    {'varName':'snum.metacif.sad_file',
     'itemName':'SADABS %File%',
     'chooseFile':{'filter':'*.abs'}
     },
    {'varName':'snum.metacif.pcf_file',
     'itemName':'pcf %File%',
     'chooseFile':{'filter':'*.pcf'}
     },
    {'varName':'snum.metacif.p4p_file',
     'itemName':'p4p %File%',
     'chooseFile':{'filter':'*.p4p'}
     },
    {'varName':'snum.metacif.smart_file',
     'itemName':'SMART %File%',
     'chooseFile':{'filter':'*.ini'}
     },                                      
    {'varName':'snum.metacif.saint_file',
     'itemName':'SAINT %File%',
     'chooseFile':{'filter':'*.ini'}
     },                      
    {'varName':'snum.metacif.frames_file',
     'itemName':'%Frame% %File%',
     'chooseFile':{'filter':'*.*'}
     },                      
    {'varName':'snum.metacif.integ_file',
     'itemName':'%Integration% %File%',
     'chooseFile':{'filter':'*._ls'}
     },                      
    {'varName':'snum.metacif.cad4_file',
     'itemName':'cad4 %File%',
     'chooseFile':{'filter':'*.dat'}
     },                      
  ]
  text = ''

  x = 0
  for i in range(len(list)):
    d = list[x]
    listFiles = 'snum.metacif.list_%s_files'  %d['varName'].split('.')[-1].split('_')[-2]
    var = OV.GetParam(listFiles)
    if var is not None:
      if ';' in var:
        d.setdefault('items', 'spy.GetParam(%s)' %listFiles)
      x += 1
      file_type = d['varName'].split('.')[-1].split('_')[0]
      d.setdefault('onchange',"spy.SetParam(%s,'GetValue(SET_%s)')>>spy.AddVariableToUserInputList(%s)>>spy cif" %(d['varName'],str.upper(d['varName']).replace('.','_'),d['varName']))
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
OV.registerFunction(sourceFilesHtmlMaker)

def diffractionMetadataHtmlMaker():
  list = (
    {'varName':'snum.report.diffractometer',
     'readonly':'',
     'itemName':'%Diffractometer%',
     'items':userDictionaries.localList.getListDiffractometers(),
     'onchange':"spy.addToLocalList(GetValue(SET_SNUM_REPORT_DIFFRACTOMETER),diffractometers)>>updatehtml",
     },
  )

  if OV.GetParam('snum.report.diffractometer') != '?':
    list += (
      {'varName':'snum.report.diffractometer_definition_file',
       'itemName':'%Definition File%',
       'value':userDictionaries.localList.getDiffractometerDefinitionFile(OV.GetParam('snum.report.diffractometer')),
       'chooseFile':{
         'caption':'Choose definition file',
         'filter':'*.cif',
         'folder':'%s/Util/SiteSpecific' %OV.BaseDir(),
         'function':'spy.setDiffractometerDefinitionFile(spy.GetParam(snum.metacif.diffrn_measurement_device_type),'
         },
       },
    )
    
  list += (
    {'varName':'snum.metacif.diffrn_ambient_temperature',
     'itemName':'%Diffraction Temperature% (K)'
     },					
    {'varName':'snum.metacif.cell_measurement_temperature',
     'itemName':'%Cell Measurement Temperature% (K)'
     },
    {'varName':'snum.metacif.diffrn_special_details',
     'itemName':'%Special Details%',
     'multiline':'multiline'
     }
  )

  return htmlTools.makeHtmlTable(list)
OV.registerFunction(diffractionMetadataHtmlMaker)

def crystalMetadataHtmlMaker():
  list = (
    {'varName':'snum.metacif.chemical_name_systematic',
     'itemName':'%Systematic Name%',
     },
    {'varName':'snum.metacif.exptl_crystal_colour',
     'itemName':'%Colour%',
     'box1':{'varName':'snum.metacif.exptl_crystal_colour_lustre',
             'items':'?;metallic;dull;clear'
             },
     'box2':{'varName':'snum.metacif.exptl_crystal_colour_modifier',
             'items':'?;light;dark;whitish;blackish;grayish;brownish;reddish;pinkish;orangish;yellowish;greenish;bluish'
             },
     'box3':{'varName':'snum.metacif.exptl_crystal_colour_primary',
             'items':'?;colourless;white;black;gray;brown;red;pink;orange;yellow;green;blue;violet'
             },
     },
    {'varName':'snum.metacif.exptl_crystal_size',
     'itemName':'%Size%',
     'box1':{'varName':'snum.metacif.exptl_crystal_size_min',
             'width':'50'
             },
     'box2':{'varName':'snum.metacif.exptl_crystal_size_mid',
             'width':'50'
             },
     'box3':{'varName':'snum.metacif.exptl_crystal_size_max',
             'width':'50'
             },
     },
    {'varName':'snum.metacif.exptl_crystal_description',
     'itemName':'%Shape%',
     'items':'?;block;plate;needle;prism;irregular;cube;trapezoid;rect. Prism;rhombohedral;hexagonal;octahedral',
     },
    {'varName':'snum.metacif.exptl_crystal_preparation',
     'itemName':'%Preparation Details%',
     'multiline':'multiline',
     },
    {'varName':'snum.metacif.exptl_crystal_recrystallization_method',
     'itemName':'%Crystallisation Details%',
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
     'onchange':"spy.SetParam(snum.report.submitter,GetValue(SET_SNUM_REPORT_SUBMITTER))>>spy.addNewPerson(GetValue(SET_SNUM_REPORT_SUBMITTER))>>updatehtml",
     },
    {'varName':'snum.report.operator',
     'itemName':'%Operator%',
     'items':userDictionaries.people.getListPeople(),
     'readonly':'',
     'onchange':"spy.SetParam(snum.report.operator,GetValue(SET_SNUM_REPORT_OPERATOR))>>spy.addNewPerson(GetValue(SET_SNUM_REPORT_OPERATOR))>>updatehtml",
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
     'itemName':'%Volume%',
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
    {'varName':'snum.dimas.reference_ccdc_number',
     'itemName':'CCDC %Number%',
     },
    {'varName':'snum.metacif.publ_contact_author_name',
     'itemName':'%Contact% %Author%',
     'items':userDictionaries.people.getListPeople(),
     'readonly':'',
     'onchange':'spy.SetParam(snum.metacif.publ_contact_author_name,GetValue(SET_SNUM_METACIF_PUBL_CONTACT_AUTHOR_NAME))>>spy.AddVariableToUserInputList(publ_contact_author_name)>>UpdateHtml'
     },
    {'varName':'publ_contact_author_address',
     'itemName':'%Contact% %Author% %Address%',
     'multiline':'multiline',
     'value':'spy.getPersonInfo(GetValue(SET_SNUM_METACIF_PUBL_CONTACT_AUTHOR_NAME),address)',
     'onleave':'spy.changePersonInfo(GetValue(SET_SNUM_METACIF_PUBL_CONTACT_AUTHOR_NAME),address,GetValue(SET_PUBL_CONTACT_AUTHOR_ADDRESS))>>updatehtml'
     },
    {'varName':'publ_contact_author_email',
     'itemName':'%Contact% %Author% %Email%',
     'value':'spy.getPersonInfo(GetValue(SET_SNUM_METACIF_PUBL_CONTACT_AUTHOR_NAME),email)',
     'onleave':'spy.changePersonInfo(GetValue(SET_SNUM_METACIF_PUBL_CONTACT_AUTHOR_NAME),email,GetValue(SET_PUBL_CONTACT_AUTHOR_EMAIL))>>updatehtml'
     },
    {'varName':'publ_contact_author_phone',
     'itemName':'%Contact% %Author% %Phone%',
     'value':'spy.getPersonInfo(GetValue(SET_SNUM_METACIF_PUBL_CONTACT_AUTHOR_NAME),phone)',
     'onleave':'spy.changePersonInfo(GetValue(SET_SNUM_METACIF_PUBL_CONTACT_AUTHOR_NAME),phone,GetValue(SET_PUBL_CONTACT_AUTHOR_PHONE))>>updatehtml'
     },
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
      'bgcolor':"%s" %OV.FindValue('gui_html_table_bg_colour'),
      'onchange':""
    }
    if numberAuthors == 1:
      authorRow.setdefault('itemName','')
      authorRow.setdefault('field1',{'itemName':'%Author%'})
      authorRow.setdefault('field2',{'itemName':'<a href="spy.move(del,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>updatehtml" target="Remove author from list"><zimg border="0" src="gui/images/toolbar-delete.png"></a>' %str(i),
                                     'fieldALIGN':'right'})

    elif i == 1:
      authorRow.setdefault('itemName','')
      authorRow.setdefault('field1',{'itemName':'%Authors%'})
      authorRow.setdefault('field2',{'itemName':'<zimg border="0" src="gui/images/toolbar-up-off.png"><a href="spy.move(down,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>updatehtml" target="Move author down list"><zimg border="0" src="gui/images/toolbar-down.png"></a> <a href="spy.move(del,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>updatehtml" target="Remove author from list"><zimg border="0" src="gui/images/toolbar-delete.png"></a>' %(str(i),str(i)),
                                     'fieldALIGN':'right'})
    elif i == numberAuthors:
      authorRow.setdefault('itemName','<a href="spy.move(up,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>updatehtml" target="Move author up list"><zimg border="0" src="gui/images/toolbar-up.png"></a><zimg border="0" src="gui/images/toolbar-down-off.png"><a href="spy.move(del,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>updatehtml" target="Remove author from list"><zimg border="0" src="gui/images/toolbar-delete.png"></a>' %(str(i),str(i)))
      authorRow.setdefault('fieldALIGN','right')
      authorRow['bgcolor'] = OV.FindValue('gui_html_input_bg_colour')
    else:
      authorRow.setdefault('itemName','<a href="spy.move(up,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>updatehtml" target="Move author up list"><zimg border="0" src="gui/images/toolbar-up.png"></a> <a href="spy.move(down,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>updatehtml" target="Move author down list"><zimg border="0" src="gui/images/toolbar-down.png"></a> <a href="spy.move(del,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>updatehtml" target="Remove author from list"><zimg border="0" src="gui/images/toolbar-delete.png"></a>' %(str(i),str(i),str(i)))
      authorRow.setdefault('fieldALIGN','right')
      
    list.append(authorRow)
  if numberAuthors > 0:
    s = '_' + str(numberAuthors)
    list.append(                            
      {'varName':'publ_author_address',
       'itemName':'%Author% %Address%',
       'multiline':'multiline',
       'value':'spy.getPersonInfo(GetValue(SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s),address)' %s,
       'onleave':'spy.changePersonInfo(GetValue(SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s),address,GetValue(SET_PUBL_AUTHOR_ADDRESS))>>updatehtml' %s
       }
    )
    list.append(
      {'varName':'publ_author_email',
       'itemName':'%Author% %Email%',
       'value':'spy.getPersonInfo(GetValue(SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s),email)' %s,
       'onleave':'spy.changePersonInfo(GetValue(SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s),email,GetValue(SET_PUBL_AUTHOR_EMAIL))>>updatehtml' %s
       }
    )
  list.append(    
    {'varName':'snum.metacif.publ_author_names',
     'ctrl_name':'ADD_PUBL_AUTHOR_NAME',
     'readonly':'',
     'itemName':'%Add% %Author%',
     'items':userDictionaries.people.getListPeople(),
     'value':'?',
     'onchange':"spy.AddNameToAuthorList(GetValue(ADD_PUBL_AUTHOR_NAME))>>updatehtml",
     'onleave':"spy.AddNameToAuthorList(GetValue(ADD_PUBL_AUTHOR_NAME))>>updatehtml",
     }
  )

  for d in list:
    d.setdefault('ctrl_name','SET_%s' %str.upper(d['varName']).replace('.','_'))
    if 'ctrl_name' in d['varName']:
      d.setdefault('onchange',"spy.SetParam(%(varName)s,GetValue(%(ctrl_name)s))>>spy.changeBoxColour(%(ctrl_name)s,#FFDCDC)>>updatehtml" %d)
    elif 'author_name' in d['varName']:
      d.setdefault('onchange','')
    elif 'author' in d['varName']:
      d.setdefault('onleave','')
  retstr = htmlTools.makeHtmlTable(list)

  list = [
    {'varName':'snum.metacif.publ_requested_journal',
     'itemName':'%Requested% %Journal%',
     'items':userDictionaries.localList.getListJournals(),
     'readonly':'',
     'onchange':'spy.addToLocalList(GetValue(SET_SNUM_METACIF_PUBL_REQUESTED_JOURNAL),requested_journal)>>updatehtml',
     }
  ]

  retstr += htmlTools.makeHtmlTable(list)

  retstr +=       """
<tr VALIGN="center" ALIGN="left">
         <td VALIGN="center" width="40%%" colspan=2>

         <a href="spy.contactLetter()>>updatehtml" target="Edit Contact Letter"><b>Contact Letter</b></a>
         </td>   
</tr>
"""
  return retstr
OV.registerFunction(publicationMetadataHtmlMaker)

def contactLetter():
  user_input_variables = OV.GetParam('snum.metacif.user_input_variables')
  if user_input_variables is None or 'publ_contact_letter' not in user_input_variables:
    import datetime
    today = datetime.date.today()
    date = today.strftime("%x")
    journal = OV.GetParam('snum.metacif.publ_requested_journal')
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

  else:
    letterText = OV.GetParam('snum.metacif.publ_contact_letter')
    
  inputText = OV.GetUserInput(0,'_publ_contact_letter',letterText)
  if inputText == '':
    OV.SetParam('snum.metacif.publ_contact_letter', letterText)
  elif inputText != letterText:
    OV.SetParam('snum.metacif.publ_contact_letter', inputText)
    variableFunctions.AddVariableToUserInputList('publ_contact_letter')
  elif 'publ_contact_letter' not in OV.GetParam('snum.metacif.user_input_variables'):
    OV.SetParam('snum.metacif.publ_contact_letter', letterText)
  else:
    pass
  return ""
OV.registerFunction(contactLetter)

def AddNameToAuthorList(newName):
  oldValue = OV.GetParam("snum.metacif.publ_author_names")
  if newName != '?':
    if oldValue is None:
      newValue = newName
    elif newName in oldValue:
      newValue = oldValue
      print "%s is already in the list of authors" %newName
    else:
      newValue = oldValue + ";" + newName
    OV.SetParam("snum.metacif.publ_author_names", newValue)
  return ""
OV.registerFunction(AddNameToAuthorList)

def move(arg,name):
  listNames = OV.GetParam('snum.metacif.publ_author_names').split(';')
  name_i = olx.GetValue(name)
  i = listNames.index(name_i)
  
  if arg in ('up','UP'):
    if i != 0:
      name_i_minus_1 = listNames[i-1]
      listNames[i] = name_i_minus_1
      listNames[i-1] = name_i
    else:
      pass
    
  elif arg in ('down','DOWN'):
    try:
      name_i_plus_1 = listNames[i+1]
      listNames[i] = name_i_plus_1
      listNames[i+1] = name_i
    except:
      pass
    
  elif arg in ('del','DEL'):
    del listNames[i]
    
  names = ';'.join(listNames)
  if not names:
    names = '?'
  OV.SetParam('snum.metacif.publ_author_names', names)
  
  return ''
OV.registerFunction(move)

def restraint_builder(cmd):
  colspan = 6
  
  constraints = ["EXYZ", "EADP", "AFIX"]
  olex_conres = ["RRINGS", "TRIA"]
  
  html = ""
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
    "RRINGS":["name_RRINGS", "var_d: ", "var_s1:0.02", "help_rrings-htmhelp"],
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
      #html += "<td><b>%s</b></td>" %tem
    elif id == "help":
      html_help = OV.TranslatePhrase(tem)
      html_help, d = htmlTools.format_help(html_help)
    elif id == "var":
      ctrl_name = "%s_%s_TEXT_BOX" %(name, var)
      pre_onclick += "SetVar(%s_value,GetValue(%s))>>" %(ctrl_name,ctrl_name)
      onclick += "GetValue(%s) " %ctrl_name
      if val == " ":
        val = "$GetVar(%s_value,'')" %ctrl_name
      elif ';' in val:
        items = val
        val = items.split(';')[0]
      else:
        items = None
        val = val.strip()
      if items:
        width = 40
      else:
        width=50
      if var == "d":
        width=50
      d = {"ctrl_name":ctrl_name,
           "label":var,
           "value":val,
           "width":width,
           "height":17,
           "bgcolor":"$getVar(gui_html_input_bg_colour)"
           }
      if items:
        d.setdefault("items",items)
      #html += "<td width='20%%'>%s</td>" %make_input_text_box(d)
      if var:
        html += "<td width='15%%'>%s</td>" %htmlTools.makeHtmlInputBox(d)
      
  if name == "AFIX":
    itemcount += 2
    onclick_list = onclick.strip().split(' ')
    onclick = 'AFIX strcat(%s,%s)' %(onclick_list[1],onclick_list[2])
    post_onclick = '>>labels -a'
    mode_ondown = "mode %s" %(onclick.replace('AFIX ','HFIX '))
    mode_onup = "mode off>>sel -u"
    mode_button_d = {
      "name":'AFIX_MODE',
      "value":"Mode",
      "ondown":"%s"%mode_ondown,
      "onup":"%s"%mode_onup,
      "width":40, "height":28,
      "hint":"Atoms subsequently clicked will become the pivot atom of a new rigid group",
    }
    clear_onclick = "sel atoms where xatom.afix ==  strcat(%s,%s)>>Afix 0>>labels -a" %(onclick_list[1],onclick_list[2])
    clear_button_d = {
      "name":'AFIX_CLEAR',
      "value":"Clear",
      "onclick":"%s"%clear_onclick,
      "width":40, "height":28,
      "hint":"Removes the current AFIX command from the structure",
    }
    
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
    html+= "<td></td>"*(colspan-itemcount) # Space-filler
  if name == 'AFIX':
    html += "<td width='25%%' align='right'>%s</td>" %htmlTools.make_input_button(clear_button_d)
    html += "<td width='25%%' align='right'>%s</td>" %htmlTools.make_input_button(mode_button_d)
  html += "<td width='10%%' align='right'>%s</td>" %htmlTools.make_input_button(button_d)
  
  #Add the help info as the last row in the table
  html += "</td></tr>"
  html += htmlTools.make_table_first_col(make_help=(name,'True'), help_image='normal')
  html += "<td colspan=%s bgcolor='%s'>%s</td></tr>" %(colspan, OV.FindValue('gui_html_table_firstcol_colour'), html_help, )
  if name in constraints:
    wFilePath = r"constraint-vars.htm"
  elif name in olex_conres:
    wFilePath = r"olex-conres-vars.htm"
  else:
    wFilePath = r"restraint-vars.htm"
    
  OV.write_to_olex(wFilePath, html)
  OV.UpdateHtml()
  return "Done"
OV.registerFunction(restraint_builder)

def checkErrLogFile():
  retVal = ""
  logfile = "%s/PythonError.log" %OV.DataDir()
  logfile = logfile.replace("\\\\", "\\")
  try:
    rFile = open(logfile, 'r')
  except:
    return retVal
  f = rFile.readlines()
  if len(f) != 0:
    txt = "This is a transcript of the error encountered by Olex2\n"
    for line in f:
      txt += line
    txt = "'%s'" %txt
    txt = txt.replace("\n", "--")
    txt = txt.replace("\\", "/")
    #retVal = '''
#<a href='external_edit %s>>shell "mailto:horst.puschmann@gmail.com?subject=Olex Python Error&body=%s"'>
#<zimg border='0' src='gui\\images\\toolbar-stop.png'></a>
#'''%(logfile, txt)
    retVal = '''
<a href='external_edit "%s"'>
<zimg border='0' src='gui\\images\\toolbar-stop.png'></a>
'''%(logfile)
  return retVal
OV.registerFunction(checkErrLogFile)

def weightGuiDisplay():
  gui_green = OV.FindValue('gui_green')
  gui_orange = OV.FindValue('gui_orange')
  gui_red = OV.FindValue('gui_red')
  try:
    longest = 0
    retVal = ""
    current_weight = olx.Ins('weight').split()
    if len(current_weight) == 1:
      current_weight = [current_weight[0], '0']
    length_current = len(current_weight)
    suggested_weight = olx.Ins('weight1').split()
    if len(suggested_weight) < length_current:
      for i in xrange (length_current - len(suggested_weight)):
        suggested_weight.append('0')
    if suggested_weight:
      for curr, sugg in zip(current_weight, suggested_weight):
        c = curr.replace(".", "")
        if len(c) > longest:
          longest = len(c)
        s = sugg.replace(".", "")
        if len(s) > longest:
          longest = len(s)
      
      for curr, sugg in zip(current_weight, suggested_weight):
        while len(curr) < longest and curr != "0":
          curr += '0'
        while len(sugg) < longest and sugg != "0":
          sugg += '0'
        if curr == sugg:
          colour = gui_green 
        elif float(curr)-float(curr)*0.1 < float(sugg) < float(curr)+float(curr)*0.1:
          colour = gui_orange
        else:
          colour = gui_red
        retVal += "<font size='2' color='%s'>%s(%s)</font> | " %(colour, curr, sugg)  
      retVal = retVal.strip("| ")
    else:
      retVal = current_weight
    return retVal
  except:
    return ""
OV.registerFunction(weightGuiDisplay)

def getCellHTML():
  crystal_systems = {
    'Triclinic':('a', 'b', 'c', '&alpha;', '&beta;', '&gamma;'),
    'Monoclinic':('a', 'b', 'c', '&beta;'),
    'Orthorhombic':('a', 'b', 'c'),
    'Tetragonal':('c',),
    'Cubic':('a',),
    'Hexagonal':('a', 'c'),
    'Trigonal':('a', 'c'),
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
