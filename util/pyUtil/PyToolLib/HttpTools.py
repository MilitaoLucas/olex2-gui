#from __future__ import division
# -*- coding: latin-1 -*-

from olexFunctions import OlexFunctions
OV = OlexFunctions()
settings_read = False
auto_update = True
use_proxy_settings = True
proxy = None

import urllib2
import os
import olx

def make_url_call_with_proxy(url, proxy, values, http_timeout = 5):
  if proxy:
    proxies = {'http': proxy}
  else:
    proxies = {}
  opener = urllib2.build_opener(
    urllib2.ProxyHandler(proxies))
  return opener.open(url,values, http_timeout)


def make_url_call(url, values, http_timeout = 5):
  global use_proxy_settings
  global proxy
  localhost = False
  if isinstance(url, urllib2.Request):
    localhost = 'localhost' in url.get_host().lower()
  elif isinstance(url, basestring):
    localhost = 'localhost' in url
  if use_proxy_settings and not localhost:
    try:
      read_usettings()
      res = make_url_call_with_proxy(url, proxy, values, http_timeout)
    except urllib2.URLError: #try system settings
      try:
        res = urllib2.urlopen(url,values, http_timeout)
        use_proxy_settings = False
      except Exception:
        raise
  else:
    try:
      res = urllib2.urlopen(url,values, http_timeout)
    except urllib2.URLError: #try setting file
      try:
        read_usettings()
        res = make_url_call_with_proxy(url, proxy, values, http_timeout)
        use_proxy_settings = True
      except Exception:
        raise
  return res

def read_usettings():
  global settings_read
  if settings_read: return
  settings_read = True
  global proxy
  global auto_update
  if proxy:
    return proxy
  settings_filename = "%s/usettings.dat" %olx.app.ConfigDir()
  if not os.path.exists(settings_filename):
    settings_filename = "%s/usettings.dat" %olx.app.BaseDir()
  if not os.path.exists(settings_filename):
    return proxy
  lines = open(settings_filename).readlines()
  for line in lines:
    if line.startswith('proxy='):
      proxy = line.split('=')[-1].strip()
    elif line.startswith('update='):
      v = line.split('=')[-1].strip()
      if v == 'Never':
        auto_update = False
  return proxy
