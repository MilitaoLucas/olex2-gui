#-*- coding:utf8 -*-

import os.path
import urllib2
import urllib
import pickle
import time
import codecs
import base64

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import olx

global username
username = ""
global password
password = ""

def clear_printed_response():
  path = OV.BaseDir()
  wFile = open(r"%s/etc/gui/blocks/fred.htm" %path,'w')
  wFile.write("Sorry")
  wFile.close()

def print_response(response):
  path = OV.BaseDir()
  wFile = open(r"%s/etc/gui/blocks/fred.htm" %path,'w')
  wFile.write(response.read())
  wFile.close()


def make_translate_gui_items_html(item_l):
  pop_name = "Translate"
  boxHeight = 100
  if OV.IsControl('%s.WEB_USERNAME'%pop_name):
    olx.html_ShowModal(pop_name)
  else:
    txt='''
  <body link="$getVar(gui_html_link_colour)" bgcolor="$getVar(gui_html_bg_colour)">
  <font color=$getVar(gui_html_font_colour)  size=$getVar(gui_html_font_size) face="$getVar(gui_html_font_name)">
  <table border="0" VALIGN='center' style="border-collapse: collapse" width="100%" cellpadding="1" cellspacing="1" bgcolor="$getVar(gui_html_table_bg_colour)">
  '''
    
  for item in item_l:
    if not item:
      continue
    boxHeight += 30
    value = OV.TranslatePhrase(item)
    txt += '''
  
  <tr>
    <td>
    %s: 
    </td>
     <td>
       <input 
         type="text" 
         bgcolor="$getVar(gui_html_input_bg_colour)" 
         valign='center' 
         name="%s"
         reuse
         width="300"  
         height="20" 
         value = "%s">
     </td>
     </tr>
     ''' %(item, item, value)
    
  txt += '''
     <tr>
     <td>
     </td>
     <td valign='centre'>
       <input 
         type="button" 
         bgcolor="$getVar(gui_html_input_bg_colour)" 
         valign='center' 
         width="60"  
         height="22"
         onclick="html.EndModal(Translate,1)"
         name="TRANSLATE OK"
         value = "OK">
       <input 
         type="button" 
         bgcolor="$getVar(gui_html_input_bg_colour)" 
         valign='center' 
         width="60"  
         height="22"
         onclick="html.EndModal(Translate,0)"
         name="TRANSLATE CANCEL"
         value = "Cancel">
     </td>
     </tr>
     
     </table>
     </font>
     </body>
  '''
  try:
    txt = txt.encode('utf-8')
  except:
    pass
  OV.write_to_olex("Translate.htm", txt)
  boxWidth = 500
  if boxHeight > 500:
    boxHeight = 500
  x = 200
  y = 200
  olx.Popup(pop_name, 'Translate.htm', "-s -b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(pop_name, boxWidth, boxHeight, x, y))
  res = olx.html_ShowModal(pop_name)
  res = int(res)
  return res
  
  
def make_logon_html():
  pop_name = "Logon"
  if OV.IsControl('%s.WEB_USERNAME'%pop_name):
    olx.html_ShowModal(pop_name)
  else:
    txt='''
  <body link="$getVar(gui_html_link_colour)" bgcolor="$getVar(gui_html_bg_colour)">
  <font color=$getVar(gui_html_font_colour)  size=$getVar(gui_html_font_size) face="$getVar(gui_html_font_name)">
  <b>Please log on to our server with the username and password you use at www.olex2.org.<br></b>
  <table border="0" VALIGN='center' style="border-collapse: collapse" width="100%" cellpadding="1" cellspacing="1" bgcolor="$getVar(gui_html_table_bg_colour)">
  <tr>
    <td>
    %Username%: 
    </td>
     <td>
     
       <input 
         type="text" 
         bgcolor="$getVar(gui_html_input_bg_colour)" 
         valign='center' 
         name="WEB_USERNAME"
         reuse
         width="90"  
         height="20" 
         value = "">
     </td>
     </tr>
     <tr>
    <td>
    %Password%: 
    </td>
     <td>
       <input 
         type="text" 
         bgcolor="$getVar(gui_html_input_bg_colour)" 
         valign='center' 
         name="WEB_PASSWORD"
         password
         reuse
         width="90"  
         height="20" 
         value = "">
     </td>
     </tr>
     <tr>
     <td>
     </td>
     <td valign='centre'>
       <input 
         type="button" 
         bgcolor="$getVar(gui_html_input_bg_colour)" 
         valign='center' 
         width="60"  
         height="22"
         onclick="html.EndModal(Logon,1)"
         value = "OK">
       <input 
         type="button" 
         bgcolor="$getVar(gui_html_input_bg_colour)" 
         valign='center' 
         width="60"  
         height="22"
         onclick="html.EndModal(Logon,0)"
         value = "Cancel">
     </td>
     </tr>
     
     </table>
     </font>
     </body>
     '''
  
    OV.write_to_olex("logon.htm", txt)
    boxWidth = 280
    boxHeight = 180
    x = 200
    y = 200
    olx.Popup(pop_name, 'logon.htm', "-s -b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(pop_name, boxWidth, boxHeight, x, y))
    res = olx.html_ShowModal(pop_name)
    res = int(res)
    return res
    
  
def web_authenticate():
  global username
  global password
  if not username:
    res = make_logon_html()
    if res:
      username = olx.GetValue('Logon.WEB_USERNAME')
      password = olx.GetValue('Logon.WEB_PASSWORD')
      print username
      return True
    else:
      return False
OV.registerFunction(web_authenticate)


def web_run_sql(sql = None, script = 'run_sql'):
  """ This returns a dictionary with the content of the db query result """
  global password
  global username
  if not sql:
    return None
  web_authenticate()
  try:
    sql = u"%s" %sql
    sql = sql.encode('utf-8')
  except Exception, err:
    print err
  sql = base64.b64encode(sql) 
  script = "Olex2Sql"
  url = "http://www.olex2.org/content/DB/%s" %script
  #url = "http://www.olex2.org/%s" %script
  values = {'__ac_password':password,
            '__ac_name':username,
            'sqlQ':sql,
            }
  data = urllib.urlencode(values)
  req = urllib2.Request(url)
  response = urllib2.urlopen(req,data)
  
  
  
  try:
    d = pickle.load(response)
  except Exception, err:
    if "Forgot your password" in response.read():
      username =""
      password = ""
      return "Unauthorised"
    else:
      d = {}

  return d



def web_translation_item(OXD=None, language='English'):
  global password
  global username
  web_authenticate()
  url = "http://www.olex2.org/content/DB/sqltest"
  values = {'__ac_password':password,
            '__ac_name':username,
            'language':language,
            'OXD':OXD}
  data = urllib.urlencode(values)
  req = urllib2.Request(url)
  response = urllib2.urlopen(req,data)
  text = response.read()

  if "<!DOCTYPE html PUBLIC" in text:
    username = ""
    password = ""
    return "Unauthorised"
  return text

class DownloadOlexLanguageDictionary:
  def __init__(self):
    #self.SQL = SQLFactory.SQLFactory(db='OlexGuiDB')  
    #self.basedir = r"C:\Documents and Settings\Horst\Desktop\olex"
    self.basedir = olx.BaseDir()
    self.dictionary_l = []
    self.dictF = "%s/dictionary.txt" %self.basedir
    #from OlexToMySQL import UploadOlexLanguageDictionary
    #self.uploadD = UploadOlexLanguageDictionary()


  def EditHelpItem(self, OXD, language = "English"):
    #text = olex_logon.web_translation_item(OXD, language)
    language = olx.CurrentLanguage()
    text = self.downloadSingleTerm(OXD, language)
    try:
      text = unicode(text, 'utf-8')
    except:
      pass
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
      OV.cmd('reload dictionary')

  def EditGuiItem(self,OXD,language="English"):
    res = web_authenticate()
    if not username:
      return
    language = olx.CurrentLanguage()
    self.language = language
    
    path = "etc"
    if 'index' in OXD:
      path = "etc/gui/blocks"
      tool_name = OXD
      gui_file = "%s/%s/%s.htm" % (olx.BaseDir(),path, OXD)
    else:
      tool_name = OXD.split("\\")[1].split(".")[0]
      gui_file = "%s/%s/%s" % (olx.BaseDir(),path, OXD)
      
    #text = olex_logon.web_translation_item(OXD, language)
    language = olx.CurrentLanguage()
    rFile = open(gui_file,'r')
    text = rFile.read()
    if not text:
      return
    
    inputText = OV.GetUserInput(0,'Modify text for help entry %s in %s' %(OXD, language), text)
    if inputText and inputText != text:
      wFile = open(gui_file,'w')
      wFile.write(inputText)
    else:
      inputText = text
    
      
    if "<!-- #include" in inputText:
      rFile = open(gui_file,'r')
      l = rFile.readlines()
      rFile.close()
      for line in l:
        line = line.replace(";", " ;")
        if line.startswith("<!-- #include"):
          ll = line.split()
          for item in ll:
            if ".htm" in item:
              includefile = r"%s/etc/%s" %(OV.BaseDir(), item)
              try:
                rFile = open(includefile,'r')
              except:
                print "Not found: %s" %includefile
                continue
              inputText += rFile.read()
              rFile.close()
              rFile = open(includefile,'r')
              m = rFile.readlines()
              rFile.close()
              for mline in m:
                mline = mline.replace(";", " ;")
                if mline.startswith("<!-- #include"):
                  mm = mline.split()
                  for item in mm:
                    if ".htm" in item:
                      includefile = r"%s/etc/%s" %(OV.BaseDir(), item)
                      try:
                        rFile = open(includefile,'r')
                      except:
                        print "Not found: %s" %includefile
                        continue
                      inputText += rFile.read()
      
    import re
    regex = re.compile(r"\% (.*?) \%", re.X)
    m = regex.findall(inputText)
    m = list(set(m))
    
    res = make_translate_gui_items_html(m)
    if res:
      OV.Cursor('busy', "Please wait while uploading your changes")
      ok = self.upload_items(m)
      if ok != "OK":
        for i in xrange(4):
          OV.Refresh()
          print "Upload failed, trying %i more times (%s)" %(4 - i, ok)
          ok = self.upload_items(m)
      if ok == "OK":
        self.downloadTranslation()
        OV.htmlReload()
      else:
        print "Upload has failed: %s" %ok
      OV.Cursor()
      
  def upload_items(self, m):
    try:
      total = len(m)
      i = 0
      l = []
      for OXD in m:
        if not OXD:
          continue
        i += 1
        try:
          value = olx.GetValue('Translate.%s' %OXD)
        except:
          continue
        d = {"OXD":OXD, self.language:value}
        sql = self.create_insert_or_update_sql(d, 'translation')
        l.append(sql)
      txt = pickle.dumps(l)
      text = web_run_sql(txt)
      return "OK"
        
    except Exception, err:
      return err
    
      
      
  def downloadSingleTerm(self, OXD, language = "English"):
      
    sql = "SELECT * FROM translation WHERE oxd='%s'" %(OXD)
    res = web_run_sql(sql)
    
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
    sql = self.create_insert_or_update_sql(d, 'translation')
    
    text = web_run_sql(sql)
        
    #res = self.SQL.run_sql(sql)
    #print res, field, value
    return text
        
        
  def downloadTranslation(self):
    self.get_help()
    self.write_dict_file()
    print "Downloaded Dictionary from DB"
    OV.cmd("Reload dictionary")
    print "Reloaded Dictionary"
    return "Done"
  
  def get_help(self):
    placeholder = "."
    Q = "SELECT * FROM translation"
  
    #res = self.SQL.run_select_sql(Q)
    res = web_run_sql(script='run_sql', sql = Q)
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
      line = ""
      ID = entry.get('ID')
      if ID == "0":
        continue
      OXD = (entry.get('OXD', 'no entry')).strip()
      try:
        en = (entry.get('English', 'no entry')).strip()
      except AttributeError, err:
        pass
        #raise err
      
      
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
    rFile = open(self.dictF, 'r')
    old = rFile.read()
    try:
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
    except Exception, err:
      print err
      wFile = open(self.dictF, 'w')
      wFile.write(old)
      wFile.close()
      

  def create_insert_or_update_sql(self, value_for_key, table):
    ''' value_for_key is a dictionary with key:value '''
    sql_tmpl = "INSERT %s (%s) VALUES (%s) ON DUPLICATE KEY UPDATE %s" % (
      table,
      ', '.join(value_for_key.iterkeys()),
      ', '.join([ '"%%(%s)s"' % f for f in value_for_key.iterkeys() ]),
      ', '.join(['%s="%%(%s)s"' % (f,f) for f in value_for_key.iterkeys()if not f.startswith('ID')])
      )
    sql = sql_tmpl % value_for_key
    #print sql
    return sql    
    
    
DownloadOlexLanguageDictionary_instance = DownloadOlexLanguageDictionary()
OV.registerFunction(DownloadOlexLanguageDictionary_instance.EditHelpItem)
OV.registerFunction(DownloadOlexLanguageDictionary_instance.EditGuiItem)
OV.registerFunction(DownloadOlexLanguageDictionary_instance.downloadTranslation)


