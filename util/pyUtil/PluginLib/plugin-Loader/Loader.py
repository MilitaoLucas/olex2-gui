import os
import sys
import olx
import olex

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path)

import _plgl
if sys.platform[:3] == 'win':
  ext = 'pyd'
else:
  ext = 'so'
olx.LoadDll("%s/_plgl.%s" %(path, ext))
def getModule(name):
  dir = os.path.normpath("%s/modules" %(olx.app.SharedDir()))
  if not os.path.exists(dir):
    os.mkdir(dir)
  import HttpTools
  from zipfile import ZipFile
  from StringIO import StringIO
  try:
    url = "http://www.olex2.org/PluginProvider/get"
    #url = "http://localhost:8080/PluginProvider/get"
    values = {
      'name': name,
      'at': _plgl.createAuthenticationToken()
    }
    f = HttpTools.make_url_call(url, values)
    f = f.read()
    if f.startswith('<html>'):
      print f
    else:
      zp = ZipFile(StringIO(f))
      zp.extractall(path=dir)
    print "Module %s has been successfully installed" %name
    print "You have 30 days to evaluate this module"
  except Exception, e:
    sys.stdout.formatExceptionInfo()

def loadAll():
  dir = os.path.normpath("%s/modules" %(olx.app.SharedDir()))
  if not os.path.exists(dir):
    return
  all = os.listdir(dir)
  for d in all:
    dl = os.path.normpath("%s/%s" %(dir, d))
    if not os.path.isdir(dl): continue
    key = os.path.normpath("%s/key" %(dl))
    if not os.path.exists(key):
      print "The module %s does not contain key file, skipping" %d
      continue
    key = open(key, 'rb').readline()
    try:
      if _plgl.loadPlugin(d, key):
        print "Module %s has been successfully loaded." %d
    except Exception, e:
      print 'Error occurred while loading module: %s' %d
      print e
  
olex.registerFunction(getModule, False, "plugins")
loadAll()

