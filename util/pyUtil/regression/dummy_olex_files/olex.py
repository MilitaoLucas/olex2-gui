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
  if args[0] == 'sg(%h)':
    return "P1"
  else:
    pass

def writeImage(filename, data, isPersistent=False):
  if not os.path.isdir('%s/VFS' %olx.tmp_dir):
    os.mkdir('%s/VFS' %olx.tmp_dir)
  f = open('%s/VFS/%s' %(olx.tmp_dir,filename), 'w')
  f.write(data)
  f.close()
