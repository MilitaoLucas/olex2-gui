import os
import sys
import shutil
import re
import olex
import olexex
import olx
import olex_core
from olexFunctions import OlexFunctions
OV = OlexFunctions()
import userDictionaries

import zipfile
import time

import urllib
import urllib2


class CcdcSubmit():
  def __init__(self):
    self.zip_name = None

  def ccdc_submit(self):
    zip_file = None
    try:
      if not self.check_and_get_prerequisites():
        return False
      res = self.make_pop_box()
      if res == 0:
        print "Cancel: Nothing has been sent to the CCDC"
        return False
      if res == 1:
        print "OK: Will do stuff now!"
  
      self.re_refine()
      self.check_and_get_files()
  
      zip_file = open(self.zip_name, "rb")
      url = OV.GetParam('user.ccdc.portal_url')
      self.params = {
        '__ac_password':OV.GetParam('user.ccdc.portal_passwd'),
        '__ac_name':OV.GetParam('user.ccdc.portal_username'),
        'name': self.name,
        'email': self.email,
        'file_name': zip_file
      }
  
      url = "http://ccdc.opencryst.org/deposit"
      self.send_request(url)
      return True
    finally:
      if zip_file is not None:
        zip_file.close()
      self.zip_name = None
    return False

  def make_pop_box(self):
    OV.makeGeneralHtmlPop('olex2.ccdc.pop')
    res = olx.html_ShowModal('ccdc')
    return int(res)

  def re_refine(self):
    olx.AddIns('LIST 4')
    olex.m('refine')
    from CifInfo import MergeCif
    MergeCif()

  def check_and_get_prerequisites(self):
    self.name = OV.get_cif_item('_publ_contact_author_name')
    if len(self.name) > 1 and self.name != '?':
      self.email = userDictionaries.people.getPersonInfo(self.name, 'email')
      #http://code.activestate.com/recipes/65215-e-mail-address-validation/      
      if not re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", self.email):
        print "Failed to validate e-mail address"
        return False
      self.address = userDictionaries.people.getPersonInfo(self.name,'address')
    else:
      print "Please supply at least a contact author name, address and e-mail!"
      olex.m("itemstate * 0 tab* 2 tab-work 1 logo1 1 index-work* 1 info-title 1")
      olex.m("itemstate cbtn* 1 cbtn-report 2 *settings 0 report-settings 1")
      olex.m("itemstate report-settings-h3-publication 1")
      return False
    return True

  def check_and_get_files(self):
    ## No Checking yet - only getting!
    cif_name = os.path.normpath(olx.file_ChangeExt(OV.FileFull(),'cif'))
    fcf_name = os.path.normpath(olx.file_ChangeExt(OV.FileFull(),'fcf'))
    file_name = OV.FileName()
    self.zip_name = "%s_ccdc_deposition.zip" %file_name
    zip = zipfile.ZipFile(self.zip_name, "w")
    zip.write(cif_name, file_name+".cif")
    zip.write(fcf_name, file_name+".fcf")
    zip.close();
    return True

  def send_request(self, url):
    #print "Not sending at the moment!"
    #return
    try:
      if "localhost" in url or "127.0.0.1" in url:
        proxy_support = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)
      else:
        proxy = olexex.get_proxy_from_usettings()
        proxies = {'http': proxy}
        proxy_support = urllib2.ProxyHandler(proxies)
      response = urllib2.urlopen(url,self.params)
      f = response.read()
    except Exception, err:
      print('Data submission failed')
      f = err
    print f

CcdcSubmit_instance = CcdcSubmit()
OV.registerFunction(CcdcSubmit_instance.ccdc_submit)
