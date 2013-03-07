#from __future__ import division
# -*- coding: latin-1 -*-

from olexFunctions import OlexFunctions
OV = OlexFunctions()
OV.use_proxy_settings = True
import urllib2
import os
import olx


def make_url_call_with_proxy(url, proxy, values, http_timeout = 7):
  if proxy:
    proxies = {'http': proxy}
  else:
    proxies = {}
  opener = urllib2.build_opener(
    urllib2.ProxyHandler(proxies))
  return opener.open(url,values, http_timeout)


def make_url_call(url, values, http_timeout = 7):
  proxy_used = False
  if OV.use_proxy_settings:
    try:
      proxy = get_proxy_from_usettings()
      res = make_url_call_with_proxy(url, proxy, values, http_timeout)
    except urllib2.URLError: #try system settings
      try:
        res = urllib2.urlopen(url,values, http_timeout)
        OV.use_proxy_settings = False
      except Exception:
        raise
  else:
    try:
      res = urllib2.urlopen(url,values, http_timeout)
    except urllib2.URLError: #try setting file
      try:
        proxy = get_proxy_from_usettings()
        res = make_url_call_with_proxy(url, proxy, values)
        OV.use_proxy_settings = True
      except Exception:
        raise
  return res
      
def get_proxy_from_usettings():
  proxy = None
  settings_filename = "%s/usettings.dat" %olx.app.ConfigDir()
  if not os.path.exists(settings_filename):
    settings_filename = "%s/usettings.dat" %olx.app.BaseDir()
  if not os.path.exists(settings_filename):
    return proxy
  rFile = open(settings_filename)
  lines = rFile.readlines()
  rFile.close()
  for line in lines:
    if line.startswith('proxy='):
      proxy = line.split('proxy=')[1].strip()
  return proxy
