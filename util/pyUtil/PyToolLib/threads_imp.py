import olex
import olx
import os
from threading import Thread
from threads import ThreadEx
from threads import ThreadRegistry


class NewsImageRetrivalThread(ThreadEx):
  instance = None
  image_list = {}
  active_image_list = {}

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
      if not NewsImageRetrivalThread.image_list.get(self.name,None):
        NewsImageRetrivalThread.image_list[self.name] = self.get_list_from_server(list_name=self.name)

      if NewsImageRetrivalThread.image_list.get(self.name,None):
        if not NewsImageRetrivalThread.active_image_list.get(self.name,None):
          NewsImageRetrivalThread.active_image_list[self.name] = copy.copy(NewsImageRetrivalThread.image_list[self.name])

        img_url, url = self.get_image_from_list()
        if not img_url:
          return

        if olex_fs.Exists(img_url):
          img_data = olex_fs.ReadFile(img_url)
        else:
          img = self.make_call(img_url)
          if img:
            img_data = img.read()
            if self.name == "splash":
              with open(os.sep.join([olx.app.SharedDir(), 'splash.jpg']),'wb') as wFile:
                wFile.write(img_data)
              with open(os.sep.join([olx.app.SharedDir(), 'splash.url']),'w') as wFile:
                wFile.write(url)
              with open(os.sep.join([olx.app.SharedDir(), 'splash.id']),'w') as wFile:
                wFile.write(img_url)
            elif self.name == "news":
              olex.writeImage(img_url, img_data)
        tag = OV.GetTag().split('-')[0]
        if self.name == "news":
          olex.writeImage("news/news-%s_tmp" %tag, img_data)
          olx.SetVar('olex2.news_img_link_url', url)
          olx.Schedule(1, "spy.internal.resizeNewsImage()")
    except:
      pass
    finally:
      NewsImageRetrivalThread.instance = None

  def get_image_from_list(self):
    img_url = None
    img_list = NewsImageRetrivalThread.active_image_list.get(self.name,None)
    if not img_list:
      return
    img_id = ""
    tag = None
    res = None
    if self.name == 'splash':
      _ = os.sep.join([olx.app.SharedDir(), 'splash.id'])
      if not os.path.exists(_):
        with open(_,'w') as wFile:
          img_id = "splash.jpg"
          wFile.write(img_id)
      else:
        img_id = open(_,'r').read().strip().strip("http://")
      first_res = img_list[0]
      for idx, l in enumerate(img_list):
        if img_id in l:
          if (idx +1) < len(img_list):
            res = img_list[idx+1]
            break
      if not res:
        res = first_res
    else:
      res = img_list.pop(0)
    if "," in res:
      _ = res.split(',')
      if len(_) == 2:
        img_url, url = res.split(',')
      elif len(_) == 3:
        img_url, url, tag = res.split(',')
    else:
      img_url = res
      url = "www.olex2.org"

    if tag:
      if tag.strip() != olx.olex2_tag:
        img_url = None

    if "://" not in img_url:
      return "http://%s" %(img_url.strip()), url.strip()
    return img_url.strip(), url.strip()

  def get_list_from_server(self, list_name='news'):
    if list_name == "news":
      url = 'http://www.olex2.org/adverts/olex2adverts.txt'
    elif list_name == "splash":
      url = 'http://www.olex2.org/adverts/splash.txt'
    l = self.make_call(url).readlines()
    _ = []
    for line in l:
      if line.strip().startswith("#"):
        continue
      _.append(line)
    return _

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
    ThreadRegistry().register(CheckCifRetrivalThread)
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
  from olexFunctions import OlexFunctions
  if not OlexFunctions().canNetwork(show_msg=False):
    return
  if NewsImageRetrivalThread.instance is None:
    NewsImageRetrivalThread(name).start()
olex.registerFunction(get_news_image_from_server)

def resizeNewsImage():
  from PilTools import TI
  TI.resize_news_image(vfs=True)
  img_url = olx.GetVar('olex2.news_img_link_url', '')
  if img_url:
    from olexFunctions import OlexFunctions
    OV = OlexFunctions()
    OV.SetParam('olex2.news_img_link_url', img_url)
    olx.UnsetVar('olex2.news_img_link_url')
olex.registerFunction(resizeNewsImage, False, 'internal')


def GetCheckcifReport(send_fcf=False):
  from olexFunctions import OlexFunctions
  if not OlexFunctions().canNetwork():
    return
  if CheckCifRetrivalThread.instance is None:
    CheckCifRetrivalThread(send_fcf in [True, 'true']).start()
  else:
    olx.Alert("Please wait", "The Checkcif request is in progress", "IO")
olex.registerFunction(GetCheckcifReport, False, 'cif')
