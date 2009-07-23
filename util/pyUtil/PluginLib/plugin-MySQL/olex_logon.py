
import os.path
import urllib2
import urllib

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
  txt='''
  <body link="$getVar(gui_html_link_colour)" bgcolor="$getVar(gui_html_bg_colour)">
  <font color=$getVar(gui_html_font_colour)  size=$getVar(gui_html_font_size) face="$getVar(gui_html_font_name)">
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
         bgcolor="$getVar(gui_html_input_bg_colour)" 
         valign='center' 
         name="WEB_PASSWORD"
         password
         width="90"  
         height="18" 
         value = "">
     </td>
     </tr>
     <tr h-align='centre'>
     <td colspan = '2' h-align='centre'>
       <input 
         type="button" 
         bgcolor="$getVar(gui_html_input_bg_colour)" 
         valign='center' 
         name="WEB_OK"
         width="60"  
         height="22" 
         value = "OK">
     </td>
     </tr>
     
     </table>
     </font>
     </body>
     '''
  
  OV.write_to_olex("logon.htm", txt)
  pop_name = "Logon"
  boxWidth = 300
  boxHeight = 200
  x = 400
  y = 400
  olx.Popup(pop_name, 'logon.htm', "-b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(pop_name, boxWidth, boxHeight, x, y))


def web_authenticate():
  global username
  global password
  arg = 1
  if not username:
    make_logon_html()
#    title = "Username"
#    contentText = "Please type the username you use to log on to the Olex2 portal\n"
#    username = OV.GetUserInput(arg, title, contentText)
#  if not password:
#    title = "Password"
#    contentText = "Please type your password\n"
#    password = OV.GetUserInput(arg, title, contentText)
OV.registerFunction(web_authenticate)


def web_run_sql(sql = None, script = 'run_sql'):
  global password
  global username
  if not sql:
    return None
  web_authenticate()
  url = "http://www.olex2.org/content/DB/%s" %script
  values = {'__ac_password':password,
            '__ac_name':username,
            'sql':sql,
            }
  data = urllib.urlencode(values)
  req = urllib2.Request(url)
  response = urllib2.urlopen(req,data)
  text = response.read()

  if "<!DOCTYPE html PUBLIC" in text:
    username = ""
    password = ""
    return "Unauthorised"
  return text




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

