import os
import olx

def registerMacro(*args, **kwds):
  pass

def registerFunction(*args, **kwds):
  pass

def registerCallback(*args, **kwds):
  pass

def m(*args, **kwds):
  pass

def f(*args, **kwds):
  pass

def writeImage(filename, data, isPersistent=False):
  if not os.path.isdir('%s/tmp/VFS' %olx.regression_dir):
    os.mkdir('%s/tmp/VFS' %olx.regression_dir)
  f = open('%s/tmp/VFS/%s' %(olx.regression_dir,filename), 'w')
  f.write(data)
  f.close()
