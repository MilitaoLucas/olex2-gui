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
    from CifInfo import MergeCif
    MergeCif()
    try:
      if not self.check_and_get_prerequisites():
        return False
      res = self.make_pop_box()
      if res == 0:
        f = "Cancel: Nothing has been sent to the CCDC"
        print f
        return False
      if res == 1:
        print "Sending to the ccdc now..."
  
      self.zip_files()
  
      zip_file = open(self.zip_name, "rb")
      url = OV.GetParam('olex2.ccdc.url')
      destination =   OV.GetParam('olex2.ccdc.ccdc_mail')
      self.params = {
        '__ac_password':OV.GetParam('user.ccdc.portal_passwd'),
        '__ac_name':OV.GetParam('user.ccdc.portal_username'),
        'name': self.name,
        'email': self.email,
        'file_name': zip_file,
        'destination': destination,
      }
  
      OV.make_url_call(url, self.params)
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
    self.check_files()
    return True

  def check_files(self):
    cif_name =  OV.GetParam('snum.current_result.cif')
    if not cif_name:
      cif_name = os.path.normpath(olx.file_ChangeExt(OV.FileFull(),'cif'))
    fcf_name =  OV.GetParam('snum.current_result.fcf')
    if not fcf_name:
      fcf_name = os.path.normpath(olx.file_ChangeExt(OV.FileFull(),'fcf'))
    if not os.path.exists(cif_name):
      cif_name = "+++ PLEASE SELECT A CIF FILE +++"
    if not os.path.exists(fcf_name):
      fcf_name = "+++ PLEASE SELECT A FCF FILE +++"
    OV.SetParam('snum.current_result.cif',cif_name)
    OV.SetParam('snum.current_result.fcf',fcf_name)
    return True
  def zip_files(self):
    ## No Checking yet - only getting!
    
    
    cif_name = OV.GetParam('snum.current_result.cif')
    fcf_name = OV.GetParam('snum.current_result.fcf')
    if not os.path.exists(fcf_name):
      fcf_name = None
    file_name = OV.FileName()
    self.zip_name = "%s_ccdc_deposition.zip" %file_name
    zip = zipfile.ZipFile(self.zip_name, "w")
    zip.write(cif_name, file_name+".cif")
    if fcf_name:
      zip.write(fcf_name, file_name+".fcf")
    zip.close();
    return True

  def send_request(self, url):
    try:
      if "localhost" in url or "127.0.0.1" in url:
        proxy_support = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy_support)
      else:
        proxy = olexex.get_proxy_from_usettings()
        if proxy:
          proxy_support = urllib2.ProxyHandler({'http': proxy})
          opener = urllib2.build_opener(proxy_support)
        else:
          opener = urllib2.build_opener(urllib2.ProxyHandler({}))
      response = opener.open(url,self.params)
      f = response.read()
    except Exception, err:
      print('Data submission failed')
      f = err
    print f
    
CcdcSubmit_instance = CcdcSubmit()
OV.registerFunction(CcdcSubmit_instance.ccdc_submit)
