import olex
import olx
import os
from threading import Thread
from threads import ThreadEx
from threads import ThreadRegistry
    
class NewsImageRetrivalThread(ThreadEx):
  instance = None
  image_list = None
  active_image_list = None
  
  def __init__(self, name):
    ThreadRegistry().register(NewsImageRetrivalThread)
    Thread.__init__(self)
    self.name = name
    NewsImageRetrivalThread.instance = self
    
  def run(self):
    from olexFunctions import OlexFunctions
    OV = OlexFunctions()
    import copy
    import random
    import olex_fs
    try:
      if not NewsImageRetrivalThread.image_list:
        NewsImageRetrivalThread.image_list = self.get_list_from_server()
        
      if NewsImageRetrivalThread.image_list:
        if not NewsImageRetrivalThread.active_image_list:
          NewsImageRetrivalThread.active_image_list = copy.copy(NewsImageRetrivalThread.image_list)
          random.shuffle(NewsImageRetrivalThread.active_image_list)
        img_url, url = self.get_image_from_list()

        if olex_fs.Exists(img_url):
          img_data = olex_fs.ReadFile(img_url)
        else:
          img = self.make_call(img_url)
          if img:
            img_data = img.read()
            olex.writeImage(img_url, img_data)
        tag = OV.GetTag().split('-')[0]
        olex.writeImage("news/news-%s_tmp" %tag, img_data)
        OV.SetParam('olex2.news_img_link_url', url)
        olx.Schedule(1, "spy.internal.resizeNewsImage()")
    except:
      pass
    finally:
      NewsImageRetrivalThread.instance = None

  def get_image_from_list(self):
    if not NewsImageRetrivalThread.active_image_list:
      return
    res = NewsImageRetrivalThread.active_image_list.pop(0)
    if "," in res:
      img_url, url = res.split(',')
    else:
      img_url = res
      url = "www.olex2.org"
    if "://" not in img_url:
      return "http://%s" %(img_url.strip()), url.strip()
    return img_url.strip(), url.strip()

  def get_list_from_server(self):
    url = 'http://www.olex2.org/olex2adverts.txt'
    return self.make_call(url).readlines()

  def make_call(self, url):
    import HttpTools
    try:
      res = HttpTools.make_url_call(url, values = '', http_timeout=0.2)
    except Exception, err:
      return None
    return res
      
class CheckCifRetrivalThread(ThreadEx):
  instance = None
  def __init__(self, send_fcf):
    ThreadRegistry().register(NewsImageRetrivalThread)
    Thread.__init__(self)
    self.send_fcf = send_fcf
    CheckCifRetrivalThread.instance = self
    
  def run(self):
    import gui.cif as cif
    try:
      cif.GetCheckcifReport(send_fcf=self.send_fcf)
    except Exception, e:
      #print e
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
      

def GetCheckcifReport(send_fcf=False):
  if CheckCifRetrivalThread.instance is None:
    CheckCifRetrivalThread(send_fcf in [True, 'true']).start()
  else:
    olx.Alert("Please wait", "The Checkcif request is in progress", "IO")
olex.registerFunction(GetCheckcifReport, False, 'cif')
