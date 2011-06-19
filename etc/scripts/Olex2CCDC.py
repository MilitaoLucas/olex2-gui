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
    self.cif = None
    self.fcf = None

  def ccdc_submit(self):
    if not self.check_and_get_prerequisites():
      return
    res = self.make_pop_box()
    if res == 0:
      print "Cancel: Nothing has been sent to the CCDC"
      return
    if res == 1:
      print "OK: Will do stuff now!"

    self.re_refine()
    self.check_and_get_files()


    url = OV.GetParam('user.ccdc.portal_url')
    self.params = {'__ac_password':OV.GetParam('user.ccdc.portal_passwd'),
              '__ac_name':OV.GetParam('user.ccdc.portal_username'),
              'zip': self.zip
              }

    self.send_request()

  def make_pop_box(self):
    OV.makeGeneralHtmlPop('olex2.ccdc.pop')
    res = olx.html_ShowModal('ccdc')
    res = int(res)
    return res

  def re_refine(self):
    olx.AddIns('LIST 4')
    olex.m('refine')
    from CifInfo import MergeCif
    MergeCif()

  def check_and_get_prerequisites(self):
    name = OV.get_cif_item('_publ_contact_author_name')
    if name != '?':
      email = userDictionaries.people.getPersonInfo(name,'email')
      address = userDictionaries.people.getPersonInfo(name,'address')
    else:
      print "Please supply at least a contact author name, address and e-mail!"
      olex.m("itemstate * 0 tab* 2 tab-work 1 logo1 1 index-work* 1 info-title 1")
      olex.m("itemstate cbtn* 1 cbtn-report 2 *settings 0 report-settings 1")
      olex.m("itemstate report-settings-h3-publication 1")
      return False
    return True

  def check_and_get_files(self):
    ## No Checking yet - only getting!
    cif = os.path.normpath(olx.file_ChangeExt(OV.FileFull(),'cif'))
    cif_t = open(cif, 'rb').read()
    fcf = os.path.normpath(olx.file_ChangeExt(OV.FileFull(),'fcf'))
    fcf_t = open(fcf, 'rb').read()
    name = OV.FileName()
    file = zipfile.ZipFile("%s.zip" %name, "w")

    info = zipfile.ZipInfo("%s.cif" %name)
    info.date_time = time.localtime(time.time())[:6]
    info.compress_type = zipfile.ZIP_DEFLATED
    file.writestr(info, cif_t)

    info = zipfile.ZipInfo("%s.fcf" %name)
    info.date_time = time.localtime(time.time())[:6]
    info.compress_type = zipfile.ZIP_DEFLATED
    file.writestr(info, fcf_t)

    file.close()


#    file.write('%s.cif' %name, cif, zipfile.ZIP_DEFLATED)
#    file.write('%s.fcf' %name, fcf, zipfile.ZIP_DEFLATED)
#    file.close
    zip = open("%s.zip"%name,'rb').read()
    self.zip = zip
    self.cif = cif
    self.fcf = fcf
    return True

  def send_request(self):
    print "Not sending at the moment!"
    return
    try:
      if "localhost" in url or "127.0.0.1" in url:
        proxy_support = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy_support)
        req = urllib2.Request(url)
        urllib2.install_opener(opener)
      else:
        proxy = olexex.get_proxy_from_usettings()
        proxies = {'http': proxy}
        proxy_support = urllib2.ProxyHandler(proxies)
      response = urllib2.urlopen(req,self.params)
      f = response.read()
    except Exception, err:
      print('Failed')
      f = err
    rFile.close()
    print f

CcdcSubmit_instance = CcdcSubmit()
OV.registerFunction(CcdcSubmit_instance.ccdc_submit)
