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
import urllib
import urllib2



def ccdc_submit():
  #import urllib2
  #import urllib2_file

  file_name = os.path.normpath(olx.file_ChangeExt(OV.FileFull(),'cif'))
  rFile = open(file_name, 'rb')
  cif = rFile.read()

  url = OV.GetParam('user.ccdc.portal_url')
  params = {'__ac_password':OV.GetParam('user.ccdc.portal_passwd'),
            '__ac_name':OV.GetParam('user.ccdc.portal_username'),
#            'context':"None",
            'cif': cif
            }
#  params = urllib.urlencode(params)
#  f = urllib2.urlopen(url, params)

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
    response = urllib2.urlopen(req,params)
    f = response.read()
  except Exception, err:
    print('Failed')
    f = err
  rFile.close()
  print f
OV.registerFunction(ccdc_submit)

