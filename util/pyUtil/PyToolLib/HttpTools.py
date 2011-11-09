#from __future__ import division
# -*- coding: latin-1 -*-

from olexFunctions import OlexFunctions
OV = OlexFunctions()
OV.use_proxy_settings = True
import urllib2

http_timeout = 7

def make_url_call_with_proxy(url, proxy, values):
  if proxy:
    proxies = {'http': proxy}
  else:
    proxies = {}
  opener = urllib2.build_opener(
    urllib2.ProxyHandler(proxies))
  return opener.open(url,values, http_timeout)


def make_url_call(url, values):
  proxy_used = False
  if OV.use_proxy_settings:
    try:
      proxy = get_proxy_from_usettings()
      res = make_url_call_with_proxy(url, proxy, values)
    except urllib2.URLError: #try system settings
      try:
        res = urllib2.urlopen(url,values, http_timeout)
        OV.use_proxy_settings = False
      except Exception:
        raise
  else:
    try:
      res = urllib2.urlopen(url,values, http_timeout)
      OV.use_proxy_settings = False
    except urllib2.URLError: #try setting file
      try:
        proxy = get_proxy_from_usettings()
        res = make_url_call_with_proxy(url, proxy, values)
        OV.use_proxy_settings = True
      except Exception:
        raise
  return res
      
def get_proxy_from_usettings():
  rFile = open("%s/usettings.dat" %OV.BaseDir(),'r')
  lines = rFile.readlines()
  rFile.close()
  proxy = None
  for line in lines:
    if line.startswith('proxy='):
      proxy = line.split('proxy=')[1].strip()
  return proxy
