#-*- coding:utf8 -*-

import sys
sys.path.append(r"../plugin-MySQL")
sys.path.append(r"../../PyToolLib")
sys.path.append(r"../../../pyUtil")
#import initpy

#from ArgumentParser import ArgumentParser
import SQLFactory
import string
import time
import codecs
import Olex2Portal

from olexFunctions import OlexFunctions
OV = OlexFunctions()
import olx

#from HTMLParser import HTMLParser

#class MyParser(HTMLParser):
  #def __init__(self):
    #HTMLParser.__init__(self)
    #self.found_div = False
  #def handle_starttag(self, tag, attrs):
    #if tag == 'div':
      #for k,v in attrs:
        #if k == 'id' and v == 'result_box':
          #self.found_div = True
  #def handle_data(self, data):
    #if not self.found_div: 
      #self.translated_text = "No translation returned"
      #return
    #self.translated_text = data[1:-1] # to remove the quotes

    
    
    
class ImportDataIntoDB:
  def __init__(self):
    self.sourceSQL = SQLFactory.SQLFactory(db='DimasDB')  
    self.targetSQL = SQLFactory.SQLFactory(db='DimasDBLocal')
    self.tableMapping = {}
    self.fieldMapping = {'crystal':{'ID':'ID_service'},
                         'submission':{'ID':'ID_xray'},
                         'submission':{'ID_xray':'ID_service'},
                         'submission':{'Code':'CompoundCode'},
                         'diffraction':{'ID':'ID_service'},
                         'diffraction_cell':{'ID':'ID_service'},
                         }

    
  def updateField(self, table = 'submission', field = 'marvin'):
    Q = "SELECT ID, %s from %s" %(field, table)
    res = self.sourceSQL.run_select_sql(Q)
    for item in res:
      sNum = item["ID"]
      value = item[field]
      if value:
        value = value.strip("'")
        value = value.replace(r'"', '\\"')
        Q = 'UPDATE %s SET %s="%s" WHERE ID_xray = "%s"' %(table, field, value, sNum)
        res = self.targetSQL.run_sql(Q)
        print res, sNum
    
    
    
  def run(self):
    self.getSourceTables()
    self.getTargetTables()
    self.initialised = False
#    self.syncTable = ['submission']
    self.table = 'submission'
    self.doTable()
    
    self.initialised = True
    self.getTableMapping()
    self.table = 'submission'
    self.doTable()
    self.synchroniseSourceAndTargetTables()
    done = ['crystal']
    for table in self.syncTable:
      if table not in done:
        self.table = table
        self.doTable()
      
      
  def doTable(self):
    self.getSourceFields()
    self.getTargetFields()
    self.synchroniseSourceAndTargetFields()
    self.getSourceData()
    self.uploadData()
      
  def getTableMapping(self):
    self.tableMapping = {
                         'crystal_colourappearance':'xray_crystal_colourappearance',
                         'crystal_colourbase':'xray_crystal_colourbase',
                         'crystal_colourintensity':'xray_crystal_colourintensity',
                         'crystal_shape':'xray_crystal_shape',
                         'submission':'submission_xray',
                         'progress':'xray_progress',
                         'progress_status':'xray_progress_status',
                         'reference':'xray_reference',
                         'refinement':'xray_refinement',
                         'diffraction':'xray_diffraction',
                         'diffraction_cell':'xray_diffraction_cell',
                         'diffraction_diffractometer':'xray_diffraction_diffractometer',
                         'crystal':'xray_crystal',
                     }
    #self.tableMapping = {'submission':'submission_xray',
                     #}
    
  def uploadData(self):
    table = self.tableMapping.get(self.table, self.table)
    for ID in self.sourceData:
      if self.table != 'submission':
        self.sourceData[ID].setdefault('ID', ID)
      elif self.table == "submission" and self.initialised:
        self.sourceData[ID].setdefault('AnalysisCode', self.sourceData[ID]['CompoundCode'])
        del self.sourceData[ID]['CompoundCode']
        IDs =  self.sourceData[ID]['ID']
        self.sourceData[ID].setdefault('ID_service',IDs)
        Q = "SELECT id FROM submission WHERE id_xray = '%s'" %IDs
        res = self.targetSQL.run_select_sql(Q)
        try:
          self.sourceData[ID]['ID'] = res[0]['id']
        except:
          pass
      elif self.table == "submission":
        self.sourceData[ID].setdefault('ID_xray', ID)
        del self.sourceData[ID]['ID']
        
      else:
        IDs =  self.sourceData[ID]['ID']
        self.sourceData[ID].setdefault('ID_service',IDs)
        Q = "SELECT id FROM submission WHERE id_xray = '%s'" %IDs
        res = self.targetSQL.run_select_sql(Q)
        self.sourceData[ID]['ID'] = res[0]['id']
        del self.sourceData[ID]['ID_xray']
      Q = self.targetSQL.create_insert_or_update_sql(self.sourceData[ID], table)
      Q = Q.replace('"None"', 'Null')
#      Q = Q.replace("\r\n","")
#      while "  " in Q:
#        Q = Q.replace("  ", " ")
      res = self.targetSQL.run_sql(Q)
      print "Table: %s, ID: %s - %s" %(self.table, ID, res)
      
  def getSourceData(self):
    sourceData = {}
    try:
      mapping = self.fieldMapping[self.table]
    except:
      mapping = None
    fieldStr = ""
    for field in self.syncFields:
      fieldStr += "%s, " %field
    fieldStr = fieldStr.strip(", ")
    Q = "SELECT %s from %s" %(fieldStr, self.table)
    res = self.sourceSQL.run_select_sql(Q)
    for row in res:
      ID = row['ID']
      for field in row:
        value = row[field]
        if not value:
          if field[-2:] == "ID":
            row[field] = 0
          else:
            row[field] = None
        elif '"' in value:
          value = value.replace(r'"', r'\"')
          row[field] = value
      if mapping:
#        if len(ID) < 3:
#          continue
        for item in mapping:
          value = row[item]
          row.setdefault(mapping[item], value)
          del row[item]
        Q = "SELECT ID from submission WHERE ID_xray = '%s'" %ID
        res = self.targetSQL.run_select_sql(Q)
        for item in res:
          ID = res[0]['ID']
          
      sourceData.setdefault(ID, row)
    self.sourceData = sourceData
    
  def synchroniseSourceAndTargetFields(self):
    syncFields = []
    for item in self.sourceFields:
      if item in self.targetFields or item in self.fieldMapping[self.table]:
        syncFields.append(item)
    self.syncFields = syncFields
    
  def getSourceFields(self):
    table = self.table
    sourceFields = []
    Q = "SHOW FIELDS FROM %s" %table
    res = self.sourceSQL.run_select_sql(Q)
    for row in res:
      field = row['Field']
      sourceFields.append(field)
    self.sourceFields = sourceFields
    
  def getTargetFields(self):
    table = self.tableMapping.get(self.table, self.table)
    targetFields = []
    Q = "SHOW FIELDS FROM %s" %table
    res = self.targetSQL.run_select_sql(Q)
    for row in res:
      field = row['Field']
      targetFields.append(field)
    self.targetFields = targetFields
    
  
  def synchroniseSourceAndTargetTables(self):
    syncTable = []
    for item in self.tablesInSourceDB:
      if item in self.tablesInTargetDB or item in self.tableMapping:
        syncTable.append(item)
    self.syncTable = syncTable
    
  def getSourceTables(self):
    tablesInSourceDB = []
    Q = "SHOW FULL TABLES"
    res = self.sourceSQL.run_select_sql(Q)
    for item in res:
      k = item.get("Table_type")
      if k != "VIEW":
        tablesInSourceDB.append(item['Tables_in_dimas_plone'].lower())
    self.tablesInSourceDB = tablesInSourceDB
    
  def getTargetTables(self):
    tablesInTargetDB = []
    Q = "SHOW FULL TABLES"
    res = self.targetSQL.run_select_sql(Q)
    for item in res:
      k = item.get("Table_type")
      if k != "VIEW":
        tablesInTargetDB.append(item['Tables_in_dimas_e'].lower())
    self.tablesInTargetDB = tablesInTargetDB
    
    
class DownloadOlexLanguageDictionary:
  def __init__(self):
    import olx
    self.SQL = SQLFactory.SQLFactory(db='OlexGuiDB')  
    #self.basedir = r"C:\Documents and Settings\Horst\Desktop\olex"
    self.basedir = olx.BaseDir()
    self.dictionary_l = []
    self.dictF = "%s/dictionary.txt" %self.basedir
    #from OlexToMySQL import UploadOlexLanguageDictionary
    #self.uploadD = UploadOlexLanguageDictionary()
  
    
  def GoogleTranslate(self, txt, langIn, langOut):

    import httplib
    import urllib
    import urllib2
    import HTMLParser
    import re
        
    wwwcache = urllib2.ProxyHandler({'http': 'http://wwwcache.dur.ac.uk:8080'})
    opener = urllib2.build_opener(wwwcache)
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    #params = urllib.urlencode({'text':'happy', 'hl': 'en', 'langpair':'en|fr'})
    params = urllib.urlencode({'text':txt, 'hl': langIn, 'langpair':langIn+"|"+ langOut})
    response = opener.open('http://translate.google.com/translate_t', params)
    data = response.read()
    pat = re.compile(r"""
      <div \s+ [^>]* id \s* = \s* "?result_box [^>]* >
      (?: ' | ")? ([^<'"]+)
    """, re.X|re.M|re.S)
    m = pat.search(data)
    if m is None:
      return ""
    #assert m is not None
    translation = m.group(1)
    
    if translation:
      return translation
    
    
  def getGoogleTranslation(self, txt, langIn, langOut):
    import urllib
    url = "http://translate.google.com/translate_t?text=%s&hl=%s&langpair=%s|%s" %(txt, langIn, langIn, langOut)
    rFile = urllib.urlopen(url,proxies={'http': 'http://wwwcache.dur.ac.uk:8080/'})
    html_src = rFile.read()
    p = MyParser()
    p.reset()
    p.feed(html_src)
    if p.translated_text:
      print p.translated_text

  def EditHelpItem(self, OXD, language = "English"):
    import Olex2Portal
    #text = Olex2Portal.web_translation_item(OXD, language)
    language = olx.CurrentLanguage()
    text = self.downloadSingleTerm(OXD, language)
    text = unicode(text, 'utf-8')
#    try:
#      text = text.encode('utf-8')
#    except Exception, err:
#      print err
    
    if not text:
      return
    inputText = OV.GetUserInput(0,'Modify text for help entry %s in %s' %(OXD, language), text)
#    try:
#      inputText = inputText.encode('utf-8')
#    except Exception, err:
#      print err
      
    if inputText and inputText != text:
      res = self.uploadSingleTerm(OXD, language, inputText)
      print res
      res = self.downloadTranslation()
      print res
      OV.cmd('reload dictionary')
    else:
      print "Text has not changed"
      #res = self.downloadTranslation()
      #print res
      OV.cmd('reload dictionary')
    #print inputText
      
      
  def downloadSingleTerm(self, OXD, language = "English"):
    import Olex2Portal
    
    sql = "SELECT * FROM translation WHERE oxd='%s'" %(OXD)
    res = Olex2Portal.web_run_sql(sql)
    
    if res == "Unauthorised":
      return
    
    d = res[0]
    
    txt = d.get(language)
    
    if not txt:
      txt = "#######################################################\n"
      txt += "This is the <b>%s</b> translation of this item in progress.\n" %language
      txt += "You are the first person to work on a translation of this item\n"
      txt += "Please insert your translation here.\n"
      txt += "If you are finished, please delete these lines.\n"
      txt += "#######################################################\n\n"
      
      txt += d.get('English')
    
    if not txt:
      txt = '''
Line before a Table.
&&

~Headline~
Body text
XX command line text XX

&&
      '''
    return txt
  
  def uploadSingleTerm(self, OXD, field, value):
    d = {"OXD":OXD, field:value}
    sql = self.SQL.create_insert_or_update_sql(d, 'translation')
    
    import Olex2Portal
    text = Olex2Portal.web_run_sql(sql)
        
    #res = self.SQL.run_sql(sql)
    #print res, field, value
    return text
      
      
  def downloadTranslationMySQL(self):
    self.get_help()
    self.write_dict_file()
    print "Downloaded Dictionary from DB"
    OV.cmd("Reload dictionary")
    print "Reloaded Dictionary"
    return "Done"

  def get_help(self):
    placeholder = "."
    Q = "SELECT * FROM translation"

    res = self.SQL.run_select_sql(Q)
    #res = Olex2Portal.web_run_sql(script='run_sql', sql = Q)
    if res == "Unauthorised":
      return
    

    #lines = res.split("\n")
    #for line in lines:
    #  self.dictionary_l.append(line)
    
    languages = [('OXD',''),
                 ('English','en'),
                 ('French','fr'),
                 ('Arabic','ar'), 
                 ('Russian','ru'), 
                 ('Japanese','ja'), 
                 ('German','de'), 
                 ('Spanish','es'), 
                 ('Chinese','zh-CN'), 
                 ('Greek','el')]
    i = 0
    for entry in res:
      i += 1
#      if i == 1:
#        continue
      line = ""
      ID = entry.get('ID')
      if ID == "0":
        continue
      OXD = (entry.get('OXD', 'no entry')).strip()
      try:
        en = (entry.get('English', 'no entry')).strip()
      except AttributeError, err:
        raise err
      
      
      for language in languages:
        lang = language[0]
        short_lang = language[1]
        try:
          e = entry.get('%s' %lang).strip()
        except AttributeError:
          e = "."
        if not e:
          e = "."
          #print "Getting Google translation for '%s': %s" %(en, short_lang)
          #e = self.GoogleTranslate(en, 'en', short_lang)
          #self.uploadD.insertSingleTerm(ID, lang, e)
        #setattr(self, language, e)
        line += "%s\t" %e
      line = line[:-1]  
      line = line.replace("\n", "")
      line = line.replace("\t\t", "\t.\t")
      line += "\n"
      line = line.replace("\t\n", "\t.\n")
      line = line.replace("OXD", "OlexID")
      
      
      
      self.dictionary_l.append(line)

  def write_dict_file(self):
    wFile = open(self.dictF, 'w')
    wFile.write(codecs.BOM_UTF8 )
    wFile.close()
    wFile = codecs.open(self.dictF, 'a', 'utf-8')
    for line in self.dictionary_l:
      try:
        line = unicode( line, "utf-8" )
      except UnicodeDecodeError, err:
        print err
        print line
        continue
        
      wFile.write(line)
    wFile.close()

    
DownloadOlexLanguageDictionary_instance = DownloadOlexLanguageDictionary()
#OV.registerFunction(DownloadOlexLanguageDictionary_instance.EditHelpItem)
OV.registerFunction(DownloadOlexLanguageDictionary_instance.downloadTranslationMySQL)
    
    
    
class UploadOlexLanguageDictionary:
  def __init__(self):
    self.SQL = SQLFactory.SQLFactory(db='OlexGuiDB')  
    self.basedir = OV.BaseDir()
    self.dictionary_l = []
    self.dictF = "%s/dictionary_chinese.txt" %self.basedir

  def insertSingleTerm(self, ID, field, value):
    d = {"ID":ID, field:value}
    sql = self.SQL.create_insert_or_update_sql(d, 'translation')
    res = self.SQL.run_sql(sql)
    print res, field, value
    
  def run(self):
    self.read_dictionary()
    self.post_dictionary()
    
  def read_dictionary(self):
    rFile = open(self.dictF, 'r')
    for line in rFile:
      line = line.replace('\xef\xbb\xbf', "")
      line = line.replace('\n', "")
      line = line.split("\t")
      self.dictionary_l.append(line)
      
      

  def post_dictionary(self):
    table = 'translation'
    #fields = "ID, OXD, English, German, Spanish, Chinese, Russian, French, Greek, Arabic, Japanese, translationtypeID"
    #values = "'0','OlexID','English','German','Spanish','Chinese', 'Greek', 'Arabic', 'Japanese', 'TypeID'" 
    #Q="INSERT INTO %s (%s) VALUES (%s);"  %(table, fields, values)
    #res = self.SQL.run_sql(Q)
    #print res
    self.read_dictionary()
    fields = ['ID']
    fields += self.dictionary_l[0]
    fields += ['translationtypeID']
    
    i = 0
    values = []
    for line in self.dictionary_l:
      values = []
      i += 1
      ID  = i
      values.append(ID)
      j = 0
      for value in line:
        j += 1
        value = value.strip()
        value = value.replace('\xef\xbb\xbf', "")
        if value == ".": value = ""
        values.append(value)
        if j == 1:
          l = value.split(" ")
          if len(l) == 1:
            if "." not in l[0]:
              typeID = 1
            else:
              typeID = 2
          elif len(l) < 12:
            typeID = 2
          else:
            typeID = 3
      values.append(typeID)
      d = {}
      for field, value in zip(fields, values):
        d.setdefault(field, value)
      Q = self.SQL.create_insert_or_update_sql(d, 'translation')   
      Q = Q.replace("OlexID", "OXD")
      res = self.SQL.run_sql(Q)
      print res
    return True


UploadOlexLanguageDictionary_instance = UploadOlexLanguageDictionary()
OV.registerFunction(UploadOlexLanguageDictionary_instance.post_dictionary)
  
  
  
class ExportHelp(object):
  def __init__(self, tool_fun=None, tool_param=None):
    self.SQL = SQLFactory.SQLFactory()

  def run(self):
    olex_fun = olex_core.ExportFunctionList()
    olex_mac = olex_core.ExportMacroList()
    print "Olex Functions"
    olex_fun_d = {}
    olex_mac_d = {}
    total = len(olex_fun)
    i = 0
    for item in olex_fun:
      i += 1
      #print "Trying Function %s" %(item[0]),
      command = "%s()" %item[0]
      arguments = "'%s'" %item[1]
      builtin_desc = "'%s'" %item[2].replace(r"'",r"\'")
      olex_fun_d.setdefault(command, {})
      olex_fun_d[command].setdefault("ID", "'%s'" %command)
      olex_fun_d[command].setdefault("Arguments", arguments)
      olex_fun_d[command].setdefault("Builtin_Description", builtin_desc)
      olex_fun_d[command].setdefault("typeID", 2)
      sql = self.SQL.create_insert_or_update_sql(olex_fun_d[command], "commands")
      res = self.SQL.run_sql(sql)
      print "%s for %i/%i" %(res, i, total)

    print "Olex Macros"
    i = 0
    total = len(olex_mac)

    for item in olex_mac:
      i += 1
      command = item[0]
      print "Trying Macro %s" %(command),
      arguments = "'%s'" %item[1]
      builtin_desc = "'%s'" %item[2].replace(r"'",r"\'")
      olex_mac_d.setdefault(command, {})
      olex_mac_d[command].setdefault("ID", "'%s'" %command)
      olex_mac_d[command].setdefault("Arguments", arguments)
      olex_mac_d[command].setdefault("Builtin_Description", builtin_desc)
      olex_mac_d[command].setdefault("typeID", 1)
      sql = self.SQL.create_insert_or_update_sql(olex_mac_d[command], "commands")
      res = self.SQL.run_sql(sql)
      print "%s for %i/%i" %(res, i, total)
    
      
      
if __name__ == "__main__":
  print
  a = ImportDataIntoDB()
  a.updateField()
  
#  a = DownloadOlexLanguageDictionary()
#  a.runF()

  #a = UploadOlexLanguageDictionary()
  #a.run()
