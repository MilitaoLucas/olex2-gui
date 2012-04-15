#-*- coding:utf8 -*-

import os.path
import urllib2
import urllib
import pickle

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import HttpTools

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

def make_logon_html():
  pop_name = "Logon"
  if OV.IsControl('%s.WEB_USERNAME'%pop_name):
    olx.html.ShowModal(pop_name)
  else:
    txt='''
  <body link="$GetVar(HtmlLinkColour)" bgcolor="$GetVar(HtmlBgColour)">
  <font color=$GetVar(HtmlFontColour  size=$GetVar(HtmlGuiFontSize) face="$GetVar(HtmlFontName)">
  <table border="0" VALIGN='center' style="border-collapse: collapse" width="100%" cellpadding="1" cellspacing="1" bgcolor="$GetVar(HtmlTableBgColour)">
  <tr>
    <td>
    %Username%: 
    </td>
     <td>
     
       <input 
         type="text" 
         bgcolor="$GetVar(HtmlInputBgColour))" 
         valign='center' 
         name="WEB_USERNAME"
         reuse
         width="90"  
         height="18" 
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
         bgcolor="$GetVar(HtmlInputBgColour))" 
         valign='center' 
         name="WEB_PASSWORD"
         password
         reuse
         width="90"  
         height="18" 
         value = "">
     </td>
     </tr>
     <tr>
     <td>
     </td>
     <td valign='centre'>
       <input 
         type="button" 
         bgcolor="$GetVar(HtmlInputBgColour))" 
         valign='center' 
         width="60"  
         height="22"
         onclick="html.EndModal(Logon,1)"
         value = "OK">
     </td>
     </tr>
     
     </table>
     </font>
     </body>
     '''
  
    OV.write_to_olex("logon.htm", txt)
    boxWidth = 300
    boxHeight = 200
    x = 400
    y = 400
    olx.Popup(pop_name, 'logon.htm', "-s -b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(pop_name, boxWidth, boxHeight, x, y))
    olx.Echo('html.ShowModal(%s)' %pop_name)


def web_run_sql(sql = None, script = 'run_sql'):
  """ This returns a dictionary with the content of the db query result """
  global password
  global username
  if not sql:
    return None
  web_authenticate()
  
#  sql = u"%s" %sql
  sql = sql.encode('utf-8')
#  url_phil = OV.GetParam('olex2.portal_url')
#  url = "http://www.olex2.org/content/DB/%s" %script
#  url = "http://www.olex2.org/%s" %script
  url = "%s/%s" %(url_phil, script)
  values = {'__ac_password':password,
            '__ac_name':username,
            'sqlQ':sql,
            }
  try:
    response = HttpTools.make_url_call(url, values)
  except Exception, err:
    print err
  
  try:
    d = pickle.load(response)
  except:
    username =""
    password = ""
    return "Unauthorised"

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
  try:
    response = HttpTools.make_url_call(url, values)
  except Exception, err:
    print err
    
  text = response.read()

  if "<!DOCTYPE html PUBLIC" in text:
    username = ""
    password = ""
    return "Unauthorised"
  return text

