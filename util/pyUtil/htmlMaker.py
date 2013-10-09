import olx
import sys
import os
sys.path.append(r".\src")
import userDictionaries
## This used to be in in init.py. Why? 

from olexFunctions import OlexFunctions
OV = OlexFunctions()
import htmlTools
import olexex_setup
import variableFunctions

from gui.images import *
GI = GuiImages()


class GeneratedGuiMaker(object):
  def __init__(self):
    
    self.use_db = OV.GetParam('user.report.use_db')
    
    ## Define buttons, actions and hints: UP, DOWN, EDIT and DELETE
    number = "%s"
    onclick="spy.move(up,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.update" %number
    hint="Move author up"
    self.up = GI.get_action_button_html('up', onclick, hint)
    
    onclick="spy.move(down,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.update" %number
    hint="Move author down"
    self.down = GI.get_action_button_html('down', onclick, hint)
    
    onclick="spy.move(del,SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s)>>html.Update" %number
    hint="Remove author from paper"
    self.delete = GI.get_action_button_html('delete', onclick, hint)
  
    
    if self.use_db:
      onclick="spy.gui.report.publication.OnPersonChange(SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s,edit=True)>>html.update" %number
      hint="Edit author"
      self.edit = GI.get_action_button_html('edit', onclick, hint)
    else:
      self.edit = " "
    
    if self.use_db:
      onclick="spy.gui.report.publication.OnPersonChange(SET_SNUM_METACIF_%s,edit=True)>>html.update"
      hint="Edit author"
      self.edit_subop = GI.get_action_button_html('edit', onclick, hint)
    else:
      self.edit_subop = " "


  def currentResultFilesHtmlMaker(self, type='cif'):
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
  
  def absorption_correctionMetadataHtmlMaker(self, ):
    list = (
      {'varName':'_exptl_absorpt_correction_type',
       'items':"'analytical;cylinder;empirical;gaussian;integration;multi-scan;none;numerical;psi-scan;refdelf;sphere'",
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
  
  
  def diffractionMetadataHtmlMaker(self, ):
  
    list = (
      {'varName':'snum.report.diffractometer',
       'readonly':'',
       'itemName':'%Diffractometer%',
       'items': "'%s'" %userDictionaries.localList.getListDiffractometers(),
       'onchange':"spy.addToLocalList(html.GetValue(~name~),diffractometers)>>html.update",
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
       },
      {'varName':'_refine_special_details',
       'itemName':'%Refine Special Details%',
       'multiline':'multiline'
       }
    )
  
    return htmlTools.makeHtmlTable(list)
  OV.registerFunction(diffractionMetadataHtmlMaker)
  
  def crystalMetadataHtmlMaker(self):
    list = (
      {'varName':'_chemical_name_systematic',
       'itemName':'%Systematic Name%',
       'width':'100%'
       },
      {'varName':'_exptl_crystal_colour',
       'itemName':'%Colour%',
       'box1':{'varName':'_exptl_crystal_colour_lustre',
               'items':'?;.;metallic;dull;clear',
               'width':'33%' 
               },
       'box2':{'varName':'_exptl_crystal_colour_modifier',
               'items':"'?;.;light;dark;whiteish;blackish;grayish;brownish;reddish;pinkish;orangish;yellowish;greenish;bluish'",
               'width':'34%' 
               },
       'box3':{'varName':'_exptl_crystal_colour_primary',
               'items':"'?;colourless;white;black;gray;brown;red;pink;orange;yellow;green;blue;violet'",
               'width':'33%' 
               },
       },
      {'varName':'_exptl_crystal_size',
       'itemName':'%Size% & %Shape%',
       'box1':{'varName':'_exptl_crystal_size_min',
               'width':'20%'
               },
       'box2':{'varName':'_exptl_crystal_size_mid',
               'width':'20%'
               },
       'box3':{'varName':'_exptl_crystal_size_max',
               'width':'20%'
               },
       'box4':{'varName':'_exptl_crystal_description',
               'items': "'?;block;plate;needle;prism;irregular;cube;trapezoid;rect. Prism;rhombohedral;hexagonal;octahedral;plank'",
               'width':'40%'
               },
       },
  
      {'varName':'_exptl_crystal_preparation',
       'itemName':'%Preparation Details%',
       'multiline':'multiline',
       'width':'100%'
       },
  
  
      {'varName':'_exptl_crystal_recrystallization_method',
       'itemName':'%Crystallisation Details%',
       'multiline':'multiline',
       'width':'100%'
  ,
       },
  
      {'varName':'snum.report.crystal_mounting_method',
       'itemName':'%Crystal Mounting%',
       'multiline':'multiline',
       'width':'100%'
       },
    )
  
    return htmlTools.makeHtmlTable(list)
  
  def collectionMetadataHtmlMaker(self, ):
    items = userDictionaries.people.getListPeople()
    if self.use_db :
      onchange = '''spy.gui.report.publication.OnPersonChange('~name~')>>spy.SetParam('snum.report.%s',html.GetValue('~name~'))'''
  
    else:
      onchange = '''spy.SetParam('snum.report.%s',html.GetValue('~name~'))>>spy.addNewPerson(html.GetValue('~name~'))>>html.update'''
  
  
    subop = ["SUBMITTER", "OPERATOR"]
  
    list = []
    for tem in subop:
      authorRow = {
        'varName':'snum.report.%s' %tem.lower(),
        'ctrl_name':'SET_SNUM_METACIF_%s' %tem,
        'readonly':'',
        'items': items,
        'bgcolor':"'%s'" %OV.GetParam('gui.html.table_bg_colour'),
        'onchange':onchange % tem.lower(),
      }
      authorRow.setdefault('itemName','')
      authorRow.setdefault('field1',
                           {'itemName':tem.title(),
                            'fieldWidth':'70%%',
                            'bgcolor':'#ff0000',
                            })
      _ = "%s" %(self.edit_subop)
      if self.use_db:
        _ = _ %(tem)
        
      authorRow.setdefault('field2',{'itemName':_,
                                     'fieldWidth':'30%%',
                                     'fieldALIGN':'right'})
      list.append(authorRow)
    
    list.append(
      {
      'varName':'snum.report.date_submitted',
       'itemName':'%Date Submitted%',
      }
    )
    list.append(
      {
      'varName':'snum.report.date_collected',
       'itemName':'%Date Collected%',
      }
    )
  
    return htmlTools.makeHtmlTable(list)
  OV.registerFunction(collectionMetadataHtmlMaker)
  
  def citationsMetadataHtmlMaker(self, ):
    txt = "<b>Current Citations</b>:<br>"
    ref_l = OV.get_cif_item('_publ_section_references').split('\n')
    if not ref_l:
      ref = "<b>_publ_section_references</b> is currently missing or empty."
    else:
      for item in ref_l:
        item = item.strip()
        if item:
          txt += "%s<br>" %item
    return txt.rstrip('<br>')

  def progressMetadataHtmlMaker(self, ):
    list = (
      {'varName':'snum.dimas.progress_status',
       'itemName':'%Status%',
       'items': "'No Entry;Aborted;Rejected;Withdrawn;Lost;In Queue;Collecting;Reduction;Solving;Refining;Pending;Processing;Finishing;Finished;Publishing;Published;Published Duplicate;Known structure'"
       },
      {'varName':'snum.dimas.progress_comment',
       'itemName':'%Comment%',
       'multiline':'multiline'
       },
    )
    return htmlTools.makeHtmlTable(list)
  OV.registerFunction(progressMetadataHtmlMaker)
  
  def referenceMetadataHtmlMaker(self, ):
    list = (
      {'varName':'snum.dimas.reference_csd_refcode',
       'itemName':'%CSD% %Refcode%',
       },
      {'varName':'snum.dimas.reference_publ_authors',
       'itemName':'%Authors%',
       },
      {'varName':'snum.dimas.reference_journal_name',
       'itemName':'%Journal%',
       'items': "'%s'" %userDictionaries.localList.getListJournals()
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
  
  def publicationMetadataHtmlMaker(self, ):
    items = userDictionaries.people.getListPeople()
    if self.use_db:
      onchange = "spy.gui.report.publication.OnPersonChange('~name~', html.GetValue('SET__PUBL_CONTACT_AUTHOR_NAME'))"
    else:
      onchange = "spy.gui.report.publication.OnContactAuthorChange(~name~)"
  
    list = [
        {'varName':'user.report.use_db',
         'readonly':'',
         'itemName':'%Data Source%',
         'href':'shell %s/%s' %(OV.GetParam('user.report.db_location'),OV.GetParam('user.report.db_name')),
         'value':'$spy.GetParam(user.report.use_db)',
         'items': 'Use Dictionary [legacy]<-False;Use SQLite DB [experimental]<-True' ,
         'onchange':"spy.SetParam(user.report.use_db,html.GetValue(~name~))>>echo 'Restart of Olex2 is required for this change to take effect!'",
         },
  
      {'varName':'_database_code_depnum_ccdc_archive',
       'itemName':'CCDC %Number%',
       },
      {'varName':'_publ_contact_author_name',
       'itemName':'%Contact% %Author%',
       'items':items,
       'readonly':'',
       'onchange': onchange,
       }]
  
    if not self.use_db:
      extra_l = [
      #{'varName':'_publ_contact_author_affiliation',
       #'itemName':'%Affiliation%',
  ##     'items': "'%s'" %userDictionaries.affiliations.getListAffiliations(),
       #'value': "spy.getPersonInfo(html.GetValue('SET__PUBL_CONTACT_AUTHOR_AFFILIATION'),'affiliation')",
       #'onchange': "spy.gui.report.publication.OnPersonAffiliationChange('~name~', html.GetValue('SET__PUBL_CONTACT_AUTHOR_NAME'))"
       #},
      
      {'varName':'_publ_contact_author_address',
       'itemName':'%Contact% %Author% %Address%',
       'multiline':'multiline',
       'value': "spy.getPersonInfo(html.GetValue('SET__PUBL_CONTACT_AUTHOR_NAME'),'address')",
       'onchange': "spy.gui.report.publication.OnPersonInfoChange('SET__PUBL_CONTACT_AUTHOR_NAME','address','~name~')"
       },
      
      {'varName':'_publ_contact_author_email',
       'itemName':'%Contact% %Author% %Email%',
       'value': "spy.getPersonInfo(html.GetValue('SET__PUBL_CONTACT_AUTHOR_NAME'),'email')",
       'onchange':"spy.gui.report.publication.OnPersonInfoChange('SET__PUBL_CONTACT_AUTHOR_NAME','email','~name~')"
       },
      {'varName':'_publ_contact_author_phone',
       'itemName':'%Contact% %Author% %Phone%',
       'value': "spy.getPersonInfo(html.GetValue('SET__PUBL_CONTACT_AUTHOR_NAME'),'phone')",
       'onchange': "spy.gui.report.publication.OnPersonInfoChange('SET__PUBL_CONTACT_AUTHOR_NAME','phone','~name~')"
       },
  
      {'varName':'InfoLine',
       'itemName':'Info',
       'value':'<b>Please Note</b>: The Contact Author does not automatically appear in the author list unless that person is explicitly added below.',
       },
      ]
      list = list + extra_l
  
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
        'value':"'%s'" %listAuthors.split(';')[i-1],
        'bgcolor':"'%s'" %OV.GetParam('gui.html.table_bg_colour'),
        'onchange':""
      }
      if numberAuthors == 1:
        authorRow.setdefault('itemName','')
        authorRow.setdefault('field1',{'itemName':'%Author%'})
        _ = "%s%s" %(self.delete, self.edit)
        if self.use_db:
          _ = _ %(i,i)
        else:
          _ = _ %(i)
        authorRow.setdefault('field2',{'itemName':_,
                                      'fieldALIGN':'right'})
  
      elif i == 1:
        box = "SET_SNUM_METACIF_PUBL_AUTHOR_NAMES_%s" %i
        authorRow.setdefault('itemName','')
        authorRow.setdefault('field1',{'itemName':'Authors</td><td>'})
        _ = "%s%s%s" %(self.down, self.delete, self.edit)
        if self.use_db:
          _ = _%(i,i,i)
        else:
          _ = _%(i,i)
          
        authorRow.setdefault('field2',
                             {'itemName':_,
                              'fieldALIGN':'right'}
                             )
      elif i == numberAuthors:
        _ = "%s%s%s" %(self.up, self.delete, self.edit)
        if self.use_db:
          _ = _%(i,i,i)
        else:
          _ = _%(i,i)
          
        authorRow.setdefault('itemName',_)
        authorRow.setdefault('fieldALIGN','right')
        authorRow['bgcolor'] = OV.GetParam('gui.html.input_bg_colour')
      else:
        _ = "%s%s%s%s" %(self.up, self.down, self.delete, self.edit)
        if self.use_db:
          _ = _%(i,i,i,i)
        else:
          _ = _%(i,i,i)
          
        authorRow.setdefault('itemName',_)
        authorRow.setdefault('fieldALIGN','right')
  
      list.append(authorRow)
    if numberAuthors > 0:
      s = '_' + str(numberAuthors)
    else:
      s = None
  
    if not self.use_db and s:
  # BEGIN extra
      #list.append(
        #{'varName':'_publ_author_affiliation',
         #'itemName':'%Affiliation%',
  ##       'items': "'%s'" %userDictionaries.affiliations.getListAffiliations(),
         #'value': "spy.getPersonInfo(html.GetValue('SET__PUBL_AUTHOR_AFFILIATION'),'affiliation')",
         #'onchange': "spy.gui.report.publication.OnPersonAffiliationChange('~name~', html.GetValue('SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s'))"%s,
         #},
      #)
      list.append(
        {'varName':'publ_author_address',
         'itemName':'%Author% %Address%',
         'multiline':'multiline',
         'value':"spy.getPersonInfo(html.GetValue('SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s'),'address')" %s,
         'onchange':"spy.changePersonInfo(html.GetValue('SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s'),'address',html.GetValue('~name~'))>>spy.changeBoxColour('~name~','#FFDCDC')" %s
         }
      )
      list.append(
        {'varName':'publ_author_email',
         'itemName':'%Author% %Email%',
         'value': "spy.getPersonInfo(html.GetValue('SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s'),'email')" %s,
         'onchange':"spy.changePersonInfo(html.GetValue('SET_SNUM_METACIF_PUBL_AUTHOR_NAMES%s'),'email',html.GetValue('~name~'))>>spy.changeBoxColour('~name~','#FFDCDC')" %s
         }
      )
  
    list.append(
      {'varName':'snum.metacif.publ_author_names',
       'ctrl_name':'ADD_PUBL_AUTHOR_NAME',
       'itemName':'%Add% %Author%',
       'items': "'%s'" %userDictionaries.people.getListPeople(),
       'value':'?',
       'onchange':"spy.gui.report.publication.OnAddNameToAuthorList('~name~')",
       }
    )
  
    for d in list:
      d.setdefault('ctrl_name','SET_%s' %str.upper(d['varName']).replace('.','_'))
      if 'ctrl_name' in d['varName']:
        d.setdefault('onchange',"spy.SetParam('%(varName)s',html.GetValue('~name~'))>>spy.changeBoxColour('~name~','#FFDCDC')>>html.Update" %d)
      elif 'author_name' in d['varName']:
        d.setdefault('onchange','')
  
    list.append(
      {'varName':'_publ_requested_journal',
       'itemName':'%Requested% %Journal%',
       'items': "'%s'" %userDictionaries.localList.getListJournals(),
       'readonly':'',
       'value':'spy.get_cif_item(_publ_requested_journal)',
       'onchange':"spy.addToLocalList(html.GetValue('~name~'),'requested_journal')>>spy.changeBoxColour('~name~','#FFDCDC')",
       })
  
  
    list.append( {'varName':'snum.report.publication_style', 'readonly':'',
                  'itemName':'%Journal Style%', 'items': "general;acta",
                  'value':"spy.GetParam('snum.report.publication_style')",
                  'onchange':"spy.gui.report.publication.OnPublicationTemplateChange(html.GetValue(~name~))>>html.update",
                  }, )
  
    #if OV.GetParam('snum.report.publication_paper') != '?':
      #list += (
        #{'varName':'snum.report.publication_paper',
         #'itemName':'%Add Template CIF%',
         #'value':'$spy.gui.report.publication.DisplayMergeList()',
         #'chooseFile':{
           #'caption':'Choose definition file',
           #'filter':'.cif files|*.cif',
           #'folder':'%s/CIF/cif_templates' %OV.BaseDir(),
           #'function':'spy.gui.report.publication.AddTemplateToMergeList('
           #},
         #},
      #)
  
  
  
  
    retstr = htmlTools.makeHtmlTable(list)
  
    retstr +="""
  <tr VALIGN="center" ALIGN="left">
    <td colspan='2'>
      <a href="spy.contactLetter()>>html.Update" target="Edit Contact Letter"><b>Contact Letter</b></a>
    </td>
  </tr>
  """
  
    #retstr +="""
  #<tr VALIGN="center" ALIGN="left">
    #<td colspan='2' VALIGN="center" bgcolor=$GetVar(HtmlHighlightColour)>
      #<b>Please add the contact author to the list of Authors if that person is to appear on the paper!</b></a>
    #</td>
  #</tr>
  #"""
  
    return retstr
  OV.registerFunction(publicationMetadataHtmlMaker)
  
  def contactLetter(self, ):
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
  
  def move(self, arg,name):
    listNames = OV.GetParam('snum.metacif.publ_author_names').split(';')
    name_i = olx.html.GetValue(name)
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

GGM = GeneratedGuiMaker()
OV.registerFunction(GGM.absorption_correctionMetadataHtmlMaker)
OV.registerFunction(GGM.collectionMetadataHtmlMaker)
OV.registerFunction(GGM.contactLetter)
OV.registerFunction(GGM.crystalMetadataHtmlMaker)
OV.registerFunction(GGM.currentResultFilesHtmlMaker)
OV.registerFunction(GGM.diffractionMetadataHtmlMaker)
OV.registerFunction(GGM.progressMetadataHtmlMaker)
OV.registerFunction(GGM.publicationMetadataHtmlMaker)
OV.registerFunction(GGM.publicationMetadataHtmlMaker)
OV.registerFunction(GGM.referenceMetadataHtmlMaker)



def restraint_builder(cmd):
  height = OV.GetParam('gui.html.combo_height')
  colspan = 3

  first_col_bg = OV.GetParam('gui.html.table_firstcol_colour')
  table_row_bg = OV.GetParam('gui.html.table_firstcol_colour')


  constraints = ["EXYZ", "EADP", "AFIX"]
  olex_conres = ["RRINGS", "TRIA", "ADPUEQ", "ADPVOL", "ANGLE", "DIANG"]

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
    "RIGU":["name_RIGU", "var_s:0.004", "var_st:0.004", "help_Select any number of atoms"],
    "ISOR":["name_ISOR", "var_s:0.1", "var_st:0.2", "help_Select any number of atoms"],
    "EXYZ":["name_EXYZ", "help_exyz-htmhelp"],
    "EADP":["name_EADP", "help_eadp-htmhelp"],
    "AFIX":["name_AFIX", "var_m:6;5;10;11", "var_n:6;9", "help_AFIX-use-help"],
#    "RRINGS":["name_RRINGS", "var_d:1.39 ", "var_s1:0.02", "help_rrings-htmhelp"],
    "RRINGS":["name_RRINGS", "help_rrings-htmhelp"],
    "TRIA":["name_TRIA", "var_d: ", "var_angle: ", "help_tria-htmhelp"],
    "ADPUEQ":["name_ADPUEQ", "var_n:0.05 ", "help_adpueq-htmhelp", "cmd_restrain adp ueq"],
    "ADPVOL":["name_ADPVOL", "help_adpvol-htmhelp", "cmd_restrain adp volume"],
    "ANGLE":["name_ANGLE", "var_n: ", "help_angle-htmhelp", "cmd_restrain angle"],
    "DIANG":["name_DIANG", "var_n: ", "help_diang-htmhelp", "cmd_restrain dihedral"],
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
  ib = ""
  varcount = 0
  cmd = ""
  for item in l:
    if "var" in item:
      varcount += 1
    if "cmd" in item:
      cmd = item.split("_")[1]

  for item in l:
    itemcount += 1
    id = item.split("_")[0]
    tem = item.split("_")[1]
    val = ""
    if ":" in tem:
      var = tem.split(":")[0]
      val = tem.split(":")[1]
    if id == "name":
      name = tem
      if not cmd:
        onclick += "%s " %name
      else:
        onclick += "%s " %cmd
    elif id == "help":
      html_help = OV.TranslatePhrase(tem)
      html_help, d = htmlTools.format_help(html_help)
    elif id == "cmd":
      cmd = val
    elif id == "var":
      ctrl_name = "%s_%s_TEXT_BOX" %(name, var)
      pre_onclick += "SetVar\(%s_value,html.GetValue\(%s))>>" %(ctrl_name,ctrl_name)
      onclick += "html.GetValue\(%s) " %ctrl_name
      if val == " ":
        val = "$GetVar(%s_value,'')" %ctrl_name
      elif ';' in val:
        items = val
        val = items.split(';')[0]
      else:
        items = None
        val = val.strip()
      if items:
        width='100%'
      else:
        width='100%'
      if var == "d":
        width='100%'
      width='33%'
      b_width='60%'
      if name == 'AFIX':
        width='50%'
        b_width='80%'
      d = {"ctrl_name":ctrl_name,
           "label":var,
           "valign":'center',
           "value":val,
           "width":b_width,
           "height":height,
           "bgcolor":"$GetVar('HtmlInputBgColour')"
           }
      if items:
        d.setdefault("items",items)
      if var:
        ib += "<td align='left' width='%s' bgcolor='%s'>%s</td>" %(width, table_row_bg, htmlTools.makeHtmlInputBox(d))

  if ib:
    if name == "AFIX":
      var_max = 2
      td_width = '35%'
    else:
      var_max = 3
      td_width = '80%'

    while varcount < var_max:
      ib += "<td align='center' width='33%%' bgcolor='%s'></td>" %table_row_bg
      varcount += 1

    html.append("<td width='%s'><table border='0' style='border-collapse: collapse' width='100%%' cellpadding='1' cellspacing='0'><tr>%s</tr></table></td>" %(td_width, ib))

  if name == "AFIX":
#    itemcount += 2
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
      "width":'100%',
      "height":height,
      "hint":"Atoms subsequently clicked will become the pivot atom of a new rigid group",
    }
    clear_onclick = "sel atoms where xatom.afix==strcat\(%s,%s)>>Afix 0>>labels -a" %(onclick_list[1],onclick_list[2])

    clear_button_d = {
      "name":'AFIX_CLEAR',
      "value":"Clear",
      "onclick":"%s"%clear_onclick,
      "width":'100%',
      "height":height,
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
    pass
    #onclick += " sel"

  onclick = "%s%s%s" %(pre_onclick, onclick, post_onclick)

  button_d = {
    "name":'%s_GO' %name,
    "value":"GO",
    "onclick":"%s"%onclick,
    "width":20,
    "height":"$GetVar(HtmlComboHeight)",
    "hint":"The %s command will be applied to all currently selected atoms" %name
  }
  if varcount == 0:
    fill = colspan-itemcount
    if not fill:
      fill = 1
    html.append("<td bgcolor='%s' width=100%%></td>"*(fill) %table_row_bg) # Space-filler
  btns = ""
  width='20%'
  if name == 'AFIX':
    btns += '$spy.MakeHoverButton("button_small-clear@Afix","%s")' %clear_onclick
    btns+= '$spy.MakeHoverButton("button_small-mode@Afix","%s")' %mode_ondown
    width='60%'
  btns += '$spy.MakeHoverButton("button_small-go@%s","%s")' %(name, onclick)

  html.append("<td width='%s' align='right' bgcolor='%s'>%s</td>" %(width,table_row_bg,btns))

  #Add the help info as the last row in the table
  html.append("</td></tr><tr bgcolor='%s'>" %table_row_bg,)
  html.append(htmlTools.make_table_first_col(help_name=name, popout=True, help_image='normal'))
  html.append("<td colspan=%s bgcolor='%s'>%s</td></tr>" %(colspan, first_col_bg, html_help, ))
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
      if curr-curr*0.01 <= sugg <= curr+curr*0.01:
        colour = gui_green
      elif curr-curr*0.1 < sugg < curr+curr*0.1:
        colour = gui_orange
      else:
        colour = gui_red
      retVal += "<font color='%s'>%.3f(%.3f)</font> | " %(colour, curr, sugg)
#      retVal += "<font color='%s'>%.3f(%s)</font> | " %(colour, curr, repr(sugg)[-2:])
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
  box1 = htmlTools.make_tick_box_input(d)

  box2 = '''
<input
  type='text'
  width='100%%'
  height="$GetVar(HtmlInputHeight)"
  bgcolor="spy.GetParam(gui.html.input_bg_colour)"
  name='UPDATE_WEIGHT_MINR1'
  valign='center'
  align='left'
  value='%s'
  onchange="spy.SetParam('snum.refinement.update_weight_maxR1',html.GetValue(~name~))"
 >
''' %OV.GetParam('snum.refinement.update_weight_maxR1')

  wght_str = ""
  for i in suggested_weight:
    wght_str += " %.3f" %i
  txt_tick_the_box = OV.TranslatePhrase("Tick the box to automatically update")
  txt_Weight = OV.TranslatePhrase("Weight")
  html = '''
  <td align='left' width='50%%'>
    <b>%s: <a target="%s" href="UpdateWght%s>>html.Update">%s</a></b>
  </td>
  <td align="center" width="3%%">%s
  </td>
  <td ALIGN='center' width='32%%'><b>Auto-update</b> when R1 &lt;
  </td>
  <td ALIGN='center' width='13%%'>%s
  </td>
  <td ALIGN='center' width='2%%'>%%
  </td>
    ''' %(txt_Weight, "Update Weighting Scheme", wght_str, html_scheme, box1, box2)
  return html
OV.registerFunction(weightGuiDisplay)


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
