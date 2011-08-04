#from __future__ import division
# -*- coding: latin-1 -*-

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import urllib2


def make_url_call(url, values, use_system_proxy=True):
  proxy = get_proxy_from_usettings()
  if proxy:
    proxies = {'http': proxy}
  else:
    proxies = {}
  try:
    if not use_system_proxy:
      opener = urllib2.build_opener(
        urllib2.ProxyHandler(proxies))
      return opener.open(url,values)
    else:
      return urllib2.urlopen(url,values)
  except Exception:
    raise
  finally:
    pass
      
def get_proxy_from_usettings():
  rFile = open("%s/usettings.dat" %OV.BaseDir(),'r')
  lines = rFile.readlines()
  rFile.close()
  proxy = None
  for line in lines:
    if line.startswith('proxy='):
      proxy = line.split('proxy=')[1].strip()
  if proxy:
    print "Using Proxy server %s" %proxy
  else:
    pass
#    print "No Proxy server is set"
  return proxy
