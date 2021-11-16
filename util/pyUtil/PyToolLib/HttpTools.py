import urllib.request, urllib.error, urllib.parse
import os
import olx
from olexFunctions import OV

settings_read = False
auto_update = True
use_proxy_settings = True
proxy = None

def make_url_call_with_proxy(url, proxy, values, http_timeout = 5):
  if proxy:
    proxies = {'http': proxy}
  else:
    proxies = {}
  opener = urllib.request.build_opener(
    urllib.request.ProxyHandler(proxies))
  return opener.open(url,values, http_timeout)


def make_url_call(url, values=None, http_timeout = 5):
  global use_proxy_settings
  global proxy
  localhost = False
  if isinstance(url, urllib.request.Request):
    try:
      localhost = 'localhost' in url.get_host().lower()
    except:
      localhost = 'localhost' in url.host.lower() #py23

  elif isinstance(url, str):
    localhost = 'localhost' in url
  try:
    read_usettings()
    if not proxy:
      use_proxy_settings = False
  except:
    use_proxy_settings = False
  if use_proxy_settings and not localhost:
    try:
      read_usettings()
      res = make_url_call_with_proxy(url, proxy, values, http_timeout)
    except urllib.error.URLError: #try system settings
      try:
        res = urllib.request.urlopen(url,values, http_timeout)
        use_proxy_settings = False
      except Exception:
        raise
  else:
    res = urllib.request.urlopen(url,values, http_timeout)
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
