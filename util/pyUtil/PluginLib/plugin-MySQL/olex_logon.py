#-*- coding:utf8 -*-

import os.path
import urllib2
import urllib
import pickle

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

def make_logon_html():
  pop_name = "Logon"
  if OV.IsControl('%s.WEB_USERNAME'%pop_name):
    olx.html_ShowModal(pop_name)
  else:
    txt='''
  <body link="$spy.GetParam(gui.html.link_colour)" bgcolor="$spy.GetParam(gui.html.bg_colour)">
  <font color=$spy.GetParam(gui.html.font_colour)  size=$spy.GetParam(gui.html.font_size) face="$spy.GetParam(gui.html.font_name)">
  <table border="0" VALIGN='center' style="border-collapse: collapse" width="100%" cellpadding="1" cellspacing="1" bgcolor="$spy.GetParam(gui.html.table_bg_colour)">
  <tr>
    <td>
    %Username%: 
    </td>
     <td>
     
       <input 
         type="text" 
         bgcolor="$spy.GetParam(gui.html.input_bg_colour)" 
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
         bgcolor="$spy.GetParam(gui.html.input_bg_colour)" 
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
         bgcolor="$spy.GetParam(gui.html.input_bg_colour)" 
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
    
  
def web_authenticate():
  global username
  global password
  if not username:
    make_logon_html()
    username = olx.GetValue('Logon.WEB_USERNAME')
    password = olx.GetValue('Logon.WEB_PASSWORD')
    print username
OV.registerFunction(web_authenticate)


def web_run_sql(sql = None, script = 'run_sql'):
  """ This returns a dictionary with the content of the db query result """
  global password
  global username
  if not sql:
    return None
  web_authenticate()
  
#  sql = u"%s" %sql
  sql = sql.encode('utf-8')
  
  url = "http://www.olex2.org/content/DB/%s" %script
  url = "http://www.olex2.org/%s" %script
  values = {'__ac_password':password,
            '__ac_name':username,
            'sqlQ':sql,
            }
  data = urllib.urlencode(values)
  req = urllib2.Request(url)
  response = urllib2.urlopen(req,data)
  
  
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
  data = urllib.urlencode(values)
  req = urllib2.Request(url)
  response = urllib2.urlopen(req,data)
  text = response.read()

  if "<!DOCTYPE html PUBLIC" in text:
    username = ""
    password = ""
    return "Unauthorised"
  return text

