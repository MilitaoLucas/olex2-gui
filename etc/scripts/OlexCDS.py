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
#from olexFunctions import OlexFunctions
#OV = OlexFunctions()

'''
To run this script, type spy.OlexCDS() in Olex2
'''

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

# Find the key words
for usettings_line in usettings:
  if not cds_username or not cds_password:
    if "cds_username" in usettings_line:
      cds_id = usettings_line.split("=")[-1].strip()
      print "cds_username = ", cds_id
    elif "cds_password" in usettings_line:
      cds_passwd = usettings_line.split("=")[-1].strip()
      print "cds_password : Found"
  else:
    print "Unable to find CDS credentials"
    break
usettings.close()

# First URL is for authentication into the CDS to get our session cookie
print "Login Into CDS Server"

# Default connection information
HTTPConnection.debuglevel = 0
connection = HTTPSConnection("cds.dl.ac.uk")

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
  print response.status
  print response.getheaders()
  DLCOOKIE =  response.getheader('set-cookie').split(',')[1]
  print "Trying A Cell Search"
  # These are our unit cell parameters which will/could come from Olex2
  cell_a = 10
  cell_b = 10
  cell_c = 10
  cell_alpha = 90
  cell_beta = 90
  cell_gamma = 90
  
  # Ok, this takes the cell parameters and searches the CDS crystalweb service
  params = urlencode({
      "search" : "search",
      "dlv" : 0,
      "dbs": "A",
      "a": cell_a,
      "b": cell_b,
      "c": cell_c
      #"alpha": cell_alpha,
      #"beta": cell_beta,
      #"gamma": cell_gamma,
      #"errs": 5,
      #"erra": 10,
      #"spgr": "N"
  })
  head = {'Cookie': DLCOOKIE, "action": "cw10", "enctype" : "application/x-www-form-urlencoded"}
  #print response.read()
  connection.request("POST", "/cgi-bin/cweb/cw10", params, head)
  
  response = connection.getresponse()
  print response.status
  #print response.read()
  
  if response.status == 200:
    print "Page Found Successfully, Outputting Request Body"
    print response.read()
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
