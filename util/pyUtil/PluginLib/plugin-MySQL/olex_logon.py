    
import os.path
import urllib2
import urllib

from olexFunctions import OlexFunctions
OV = OlexFunctions()

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

def web_authenticate():
    global username
    global password
    arg = 1
    if not username:
        title = "Username"
        contentText = "Please type the username you use to log on to the Olex2 portal\n"
        username = OV.GetUserInput(arg, title, contentText)
    if not password:
        title = "Password"
        contentText = "Please type your password\n"
        password = OV.GetUserInput(arg, title, contentText)
OV.registerFunction(web_authenticate)


def web_run_sql(sql = None):
    global password
    global username
    if not sql:
        return None
    web_authenticate()
    url = "http://www.olex2.org/content/DB/run_sql"
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
    
    