"""
POST method
method="post" action="cw10" enctype="application/x-www-form-urlencoded">

Data:
application/x-www-form-urlencoded

Variables:
<input type="hidden" name="dlv" value="0"  />

server = "https://cds.dl.ac.uk/cgi-bin/cweb/"

Example:
Sending:https://cds.dl.ac.uk/cgi-bin/cweb/cw10?a=10.00&b=10.00&c=10.00
Searches for Unit Cell a=b=c=10.00

<form action="/cgi-bin/login/loginhandler.cgi" method=POST>
CDS username <input name="id" type="text" size="10">
<p>
CDS password <input name="pass" type="password" size="20">


"""
import os
import sys
import shutil
import re
#import olex
#import olx
import urllib2_file
import urllib2
from httplib import *
from urllib import *
import HTMLParser
#from olexFunctions import OlexFunctions
#OV = OlexFunctions()

'''
To run this script, type spy.OlexCDS() in Olex2
'''
# Fredrik Lundh
# This function removes HTML tags, and also converts character entities and character references. 
# Removes HTML markup from a text string.
#
# @param text The HTML source.
# @return The plain text.  If the HTML source contains non-ASCII
#     entities or character references, this is a Unicode string
def strip_html(text):
  def fixup(m):
    text = m.group(0)
    if text[:1] == "<":
        return "" # ignore tags
    if text[:2] == "&#":
        try:
            if text[:3] == "&#x":
                return unichr(int(text[3:-1], 16))
            else:
                return unichr(int(text[2:-1]))
        except ValueError:
            pass
    elif text[:1] == "&":
        import htmlentitydefs
        entity = htmlentitydefs.entitydefs.get(text[1:-1])
        if entity:
            if entity[:2] == "&#":
                try:
                    return unichr(int(entity[2:-1]))
                except ValueError:
                    pass
            else:
                return unicode(entity, "iso-8859-1")
    return text # leave as is
  return re.sub("(?s)<[^>]*>|&#?\w+;", fixup, text)

#def OlexCDS():
# First need to login
# Need to get login credentials from usettings.dat file
# I would like to MD5sum the password in the release version (not that CDS does that!)

# Usettings
#Olex2Path = olex.f("BaseDir()")
Olex2Path = "/home/xray/olexsvn"
usettings = open("%s/usettings.dat"%(Olex2Path), 'r')
cds_username = ""
cds_password = ""
URL="cds.dl.ac.uk"

# Find the key words
for usettings_line in usettings:
  if not cds_username or not cds_password:
    if "cds_username" in usettings_line:
      cds_id = usettings_line.split("=")[-1].strip()
      #print "cds_username = ", cds_id
    elif "cds_password" in usettings_line:
      cds_passwd = usettings_line.split("=")[-1].strip()
      #print "cds_password : Found"
  else:
    print "Unable to find CDS credentials"
    break
usettings.close()

# First URL is for authentication into the CDS to get our session cookie
print "Login Into CDS Server"

# Default connection information
HTTPConnection.debuglevel = 0
connection = HTTPSConnection(URL)

head = {"Content-Type" : "application/x-www-form-urlencoded", "Accept" : "text/plain"}
login_params = urlencode({
    "id": cds_id,
    "pass":cds_passwd
})

connection.request("POST", "/cgi-bin/login/loginhandler.cgi", login_params, head)
response = connection.getresponse()
#print DLCOOKIE
#print response.read()
if response.status == 200:
  # We can only get here with a successful login to the CDS returning webpage 200
  print "Login Successful"
  #print response.status
  #print response.getheaders()
  DLCOOKIE =  response.getheader('set-cookie').split(',')[1]
  print "Trying A Cell Search"
  # These are our unit cell parameters which will/could come from Olex2
  cell_a = 10.23
  cell_b = 10.23
  cell_c = 9.81
  cell_alpha = 90.0
  cell_beta = 90.0
  cell_gamma = 90.0
  
  # Ok, this takes the cell parameters and searches the CDS crystalweb service
  params = urlencode({
      "search" : "search",
      "dlv" : 0,
      "dbs": "A",
      "a": cell_a,
      "b": cell_b,
      "c": cell_c,
      "alpha": cell_alpha,
      "beta": cell_beta,
      "gamma": cell_gamma,
      "errs": 1,
      "erra": 1,
      #"spgr":
      #"spo":
      "s": "N"
  })
  head = {'Cookie': DLCOOKIE, "action": "cw10", "enctype" : "application/x-www-form-urlencoded"}
  #print response.read()
  connection.request("POST", "/cgi-bin/cweb/cw10", params, head)
  
  response = connection.getresponse()
  #print response.status
  #print response.read()
  
  if response.status == 200:
    print "Page Found Successfully, Outputting Request Body"
    for line_response in response.read().splitlines():
      #print "line response", line_response
      if "hits for your search" in line_response:
        results_line = line_response
        print "BingGO", results_line
        # Example string name="hitfile" value="/cweb/1268049669.9312.cwje"
        cds_hits_string = re.search(r'(?<=name\=\"hitfile\")*value\=\"/cweb/.*?\"', results_line)
        print cds_hits_string
        print cds_hits_string.group()
        cds_hitfile = cds_hits_string.group().split("\"")[1]
        print cds_hitfile
        number_of_hits = re.search(r'\d+', strip_html(results_line))
        number_of_hits_found = int(number_of_hits.group())
        if number_of_hits_found == 0:
          print "No results found"
        elif number_of_hits_found > 10:
          print "There are %d hits found do you wish to view them via CrystalWeb?"%number_of_hits_found
          print "There are less than 10 hits we are getting the hits now"
          head = {'Cookie': DLCOOKIE, "action": "cwd4", "enctype" : "application/x-www-form-urlencoded"}
          result_params = urlencode({
            "Display hits":"Display hits",
            "hitfile": cds_hitfile,
            "hitno": 1,
            "hpp":50,
            "dop": "A" # A, B, C, M
          })
          connection.request("POST", "/cgi-bin/cweb/cwd4", result_params, head)
          response = connection.getresponse()
          search_results = response.read()
          search_results_fix_grpahic = re.sub(r'(?<=src=")(?P<image>.*?")',
                                      r'https://cds.dl.ac.uk\g<image>',
                                      search_results)
          search_results_out = re.sub(r' action="(?P<action>\w+)"',
                                      r' action="https://cds.dl.ac.uk/cgi-bin/cweb/\g<action>"',
                                      search_results_fix_grpahic)
          # Here we need to change the path information for action="" for all actions to include the cds URL
          #CDS_res = open('%s/%s_CDS.html' %(OV.FilePath(), OV.FileName()), 'w')
          CDS_res = open('test_CDS.html', 'w')
          CDS_res.write("%s"%search_results_out)
          CDS_res.close()
          #olx.Shell('%s/%s_CDS.html' %(OV.FilePath(), OV.FileName()))
  
          search_results = response.read()
          print response.read()
        else:
          print "There are less than 10 hits we are getting the hits now"
          head = {'Cookie': DLCOOKIE, "action": "cwd4", "enctype" : "application/x-www-form-urlencoded"}
          result_params = urlencode({
            "Display hits":"Display hits",
            "hitfile": cds_hitfile,
            "hitno": 1,
            "hpp":10,
            "dop": "A" # A, B, C, M
          })
          connection.request("POST", "/cgi-bin/cweb/cwd4", result_params, head)
          response = connection.getresponse()
          search_results = response.read()
          i = 0
          lines={}
          for line_search_results in strip_html(search_results).splitlines():
            if line_search_results.strip():
              lines[i] = line_search_results.strip()
              i+=1
              continue
            #lines[i] = line_search_results.strip()
          i = 0
          CDS_hit_no = 0
          print "Outputing the Results"
          for line in lines:
            print "CDS_hit_no: ", CDS_hit_no
            #print lines[i]
            if "Hit number" in lines[i]:
                #print "Line = ", lines[i]
                hit_result = lines[i]
                print "HIT", hit_result
                print "CDS Result = ", lines[i+1]
                CDS_hit_no+=1
            if CDS_hit_no > 0:
              if "Cell data" in lines[i]:
                print "Cell Data line", lines[i]
                compound_name = lines[i+1]
                compound_formular = lines[i+2]
                compound_reference = lines[i+3]
                print "Compound name", compound_name
                print "Compound formula", compound_formular 
                print "Compound reference", compound_reference
              if "LengthsAngles" in lines[i]:
                compound_cell_a = lines[i+1]
                compound_cell_b = lines[i+2]
                compound_cell_c = lines[i+3]
                compound_cell_alpha = lines[i+1]
                compound_cell_beta = lines[i+2]
                compound_cell_gamma = lines[i+3]
                compound_system = lines[i+4]
                compound_spgr = lines[i+5]
                compound_spgr_no = lines[i+6]
                compound_Rf = lines[i+7]
                compound_Z = lines[i+8]
                compound_cell_volume = lines[i+9]
                print "Cell A", compound_cell_a
                print "Cell B", compound_cell_b
                print "Cell C", compound_cell_c
                print "Cell Alpha", compound_cell_alpha
                print "Cell Beta", compound_cell_beta
                print "Cell Gamma", compound_cell_gamma
                print "Cell System", compound_system
                print "Spacegroup", compound_spgr
                print "Spacegroup number", compound_spgr_no
                print "Rf", compound_Rf
                print "Z", compound_Z
                print "Cell Volume", compound_cell_volume
                CDS_hit_no+= 1
                # Put a formatted string in here also collect the information into an array rather than single run loops
            i+=1
            if CDS_hit_no == number_of_hits_found:
              print "Exiting", CDS_hit_no
              break
  if response.status == 302:
    print "We've been redirected"
  elif response.status == 404:
    print "Page Not Found"
  else:
    print response.status, response.reason
elif response.status == 404:
  print "Page Not Found"
else:
  print response.status, response.reason
connection.close()

 
#OV.registerFunction(OlexCDS)
