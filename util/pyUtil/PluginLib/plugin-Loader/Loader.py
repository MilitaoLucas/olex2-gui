import sys

import _plgl

olx.LoadDll("_plgl.pyd")
def getModule(name):
  dir = os.path.normpath("%s/modules" %(olx.app.SharedDir()))
  if not os.path.exists(dir):
    os.mkdir(dir)
  import HttpTools
  from zipfile import ZipFile
  from StringIO import StringIO
  try:
    url = "http://www.olex2.org/PluginProvider/get"
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

def loadModule(name):
  dir = os.path.normpath("%s/modules" %(olx.app.SharedDir()))
  if not os.path.exists(dir):
    print "Specified module %s does not exist" %name
    return
  key = "%s/%s/key" %(dir, name)
  if not os.path.exists(key):
    print "The module %s does not contain key file" %name
    return
  key = open(key).readline()
  try:
    if _plgl.loadPlugin(name, key):
      print "Module %s has been successfully loaded." %name
  except Exception, e:
    print e
  
OV.registerFunction(getModule, False, "plugins")
OV.registerFunction(loadModule, False, "plugins")
