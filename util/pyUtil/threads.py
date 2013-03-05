import olex
import olx

import os
import sys
import thread
import time
from threading import Thread

from olexFunctions import OlexFunctions
OV = OlexFunctions()

# implement force_exit to premature thread termination
class ThreadEx(Thread):
  def force_exit(self):
    import ctypes
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident,
       ctypes.py_object(SystemExit))
    if res == 0:
      raise ValueError("invalid thread id")
    elif res != 1:
      ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
      raise SystemError("PyThreadState_SetAsyncExc failed")

#must be called before destroying host application  
def joinAll():
  threads = [NewsImageRetrivalThread, CheckCifRetrivalThread]
  for th in threads:
    try:
      if th.instance: th.instance.join(1)
      if th.instance:
        th.instance.force_exit()
    except Exception, e:
      print e
      pass
   
class ShellExec:
  def run(self, arg):
    olx.Shell(arg)
    
class NewsImageRetrivalThread(ThreadEx):
  instance = None
  def __init__(self, name):
    Thread.__init__(self)
    self.name = name
    NewsImageRetrivalThread.instance = self
    
  def run(self):
    import HttpTools
    try:
      if not self.name:
        url = 'http://www.olex2.org/randomimg'
      else:
        url = 'http://www.olex2.org/olex2images/%s/image' %self.name
      try:
        image = HttpTools.make_url_call(url, values = '', http_timeout=0.2).read()
      except Exception, err:
    #    print "Downloading image from %s has failed: %s" %(url, err)
        return
      if image:
        tag = OV.GetTag().split('-')[0]
        olex.writeImage("news/news-%s_tmp" %tag, image)
        olx.Schedule(1, "'spy.internal.resizeNewsImage()'")
    except:
      pass
    finally:
      NewsImageRetrivalThread.instance = None
      
class CheckCifRetrivalThread(ThreadEx):
  instance = None
  def __init__(self):
    Thread.__init__(self)
    CheckCifRetrivalThread.instance = self
    
  def run(self):
    import gui.cif as cif
    try:
      cif.GetCheckcifReport()
    except:
      pass
    finally:
      CheckCifRetrivalThread.instance = None
      
def get_news_image_from_server(name=""):
  if NewsImageRetrivalThread.instance is None:
    NewsImageRetrivalThread(name).start()
olex.registerFunction(get_news_image_from_server)

def resizeNewsImage():
  from ImageTools import ImageTools
  IT = ImageTools()
  IT.resize_news_image(vfs=True)
olex.registerFunction(resizeNewsImage, False, 'internal')
      

def GetCheckcifReport():
  if CheckCifRetrivalThread.instance is None:
    CheckCifRetrivalThread().start()
  else:
    olx.Alert("Please wait", "The Checkcif request is in progress", "IO")
olex.registerFunction(GetCheckcifReport, False, 'cif')
  

shellExec = ShellExec()
olex.registerFunction(shellExec.run, False, "threading.shell")

olex.registerFunction(joinAll, False, "threading")
