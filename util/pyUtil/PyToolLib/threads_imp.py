import olex
import olx
import os
import sys
from threading import Thread
from threads import ThreadEx
from threads import ThreadRegistry
from olexFunctions import OlexFunctions
OV = OlexFunctions()


class NewsImageRetrivalThread(ThreadEx):
  instance = None
  image_list = {}
  active_image_list = {}

  def __init__(self, name):
    ThreadRegistry().register(NewsImageRetrivalThread)
    Thread.__init__(self)
    self.name = name
    NewsImageRetrivalThread.instance = self
    olex.registerFunction(self.get_sample_list, False, 'internal')
    olex.registerFunction(self.get_structure_from_url, False, 'internal')

  def run(self):
    from olexFunctions import OlexFunctions
    OV = OlexFunctions()
    import copy
    import random
    import olex_fs
    try:
      if not NewsImageRetrivalThread.image_list.get(self.name,None):
        NewsImageRetrivalThread.image_list[self.name] = self.get_list_from_server(list_name=self.name)
        if NewsImageRetrivalThread.image_list[self.name]:
           NewsImageRetrivalThread.image_list[self.name] = [l.strip() for l in NewsImageRetrivalThread.image_list[self.name]]

      if NewsImageRetrivalThread.image_list.get(self.name,None):
        if not NewsImageRetrivalThread.active_image_list.get(self.name,None):
          NewsImageRetrivalThread.active_image_list[self.name] = copy.copy(NewsImageRetrivalThread.image_list[self.name])

        img_url, url = self.get_image_from_list()
        if not img_url:
          return
        img_data = None
        if olex_fs.Exists(img_url):
          img_data = olex_fs.ReadFile(img_url)
        else:
          img = self.make_call(img_url)
          if img:
            img_data = img.read()
            if self.name == "splash":
              with open(os.path.join(olx.app.SharedDir(), 'splash.jpg'),'wb') as wFile:
                wFile.write(img_data)
              with open(os.path.join(olx.app.SharedDir(), 'splash.url'),'w') as wFile:
                wFile.write(url)
              with open(os.path.join(olx.app.SharedDir(), 'splash.id'),'w') as wFile:
                wFile.write(img_url)
            elif self.name == "news":
              olex.writeImage(img_url, img_data)
        tag = OV.GetTag().split('-')[0]
        if img_data and self.name == "news":
          olex.writeImage("news/news-%s_tmp" %tag, img_data)
          olx.SetVar('olex2.news_img_link_url', url)
          olx.Schedule(1, "spy.internal.resizeNewsImage()")
    except:
      sys.stdout.formatExceptionInfo()
      pass
    finally:
      NewsImageRetrivalThread.instance = None

  def get_image_from_list(self):
    from olexFunctions import OlexFunctions
    OV = OlexFunctions()
    img_url = None
    img_list = NewsImageRetrivalThread.active_image_list.get(self.name,None)
    if not img_list:
      return
    img_id = ""
    tags = None
    res_idx = -1
    if self.name == 'splash':
      if "-ac" in OV.GetTag():
        return None,None
      _ = os.path.join(olx.app.SharedDir(), 'splash.id')
      if not os.path.exists(_):
        with open(_,'w') as wFile:
          img_id = "splash.jpg"
          wFile.write(img_id)
      else:
        img_id = open(_,'r').read().strip().replace("http://", "")
      for idx, l in enumerate(img_list):
        if img_id in l:
          _ = l.split(',')
          if len(_) == 2 or (len(_) > 2 and OV.GetTag() in _[2:]):
            if (idx +1) < len(img_list):
              res_idx = idx
              break

      for idx in xrange(0, len(img_list)):
        res_idx += 1
        if res_idx >= len(img_list):
          res_idx = -1
        res = img_list[res_idx]
        if "," in res:
          _ = res.split(',')
          if len(_) == 2:
            img_url, url = _
            tags = None
          elif len(_) > 2:
            img_url, url = _[:2]
            tags = _[2:]
        else:
          img_url = res
          url = "www.olex2.org"

        if tags and OV.GetTag() not in tags:
          img_url = None
          continue
        else:
          break
    else:
      while img_list:
        res = img_list.pop(0)
        if "," in res:
          _ = res.split(',')
          if len(_) == 2:
            img_url, url = _
            tags = None
          elif len(_) > 2:
            img_url, url = _[:2]
            tags = _[2:]
        else:
          img_url = res
          url = "www.olex2.org"
        if tags and OV.GetTag() not in tags:
          img_url = None
          continue
        else:
          break

    if not img_url:
      return None, None

    if "://" not in img_url:
      return "http://%s" %(img_url.strip()), url.strip()
    return img_url.strip(), url.strip()

  def get_sample_list(self, which='samples'):
    url = OV.GetParam('olex2.samples.url') + r"/%s"%which + ".html"
    _ = self.make_call(url)
    if _ is None:
      return ""
    import gui
    from gui import help
    cont = _.read()
    help.make_help_box(helpTxt=cont, name="Sample_list")
    
  def get_structure_from_url(self, name, url=None):
    if not url:
      url = OV.GetParam('olex2.samples.url')
    url = '%s/%s.cif' %(url, name)
    _ = self.make_call(url)
    if _ is None:
      return ""
    p = os.path.join(OV.DataDir(), 'samples', name)
    if not os.path.exists(p):
      os.makedirs(p)
    pp = os.path.join(p, name + '.cif')  
    if not os.path.exists(pp):
      cont = _.read()
      with open(pp, 'w') as wFile:
        wFile.write(cont)
    else:
      print("Loading the existing structure; please delete this structure (cif file) if you want to get it again!")
    olex.m("reap '%s'" %pp)  


  def get_list_from_server(self, list_name='news'):
    if list_name == "news":
      url = 'http://www.olex2.org/adverts/olex2adverts.txt'
    elif list_name == "splash":
      url = 'http://www.olex2.org/adverts/splash.txt'
    elif list_name == "expired_pop":
      url = 'http://www.olex2.org/adverts/expired_pop.html'
    else:
      return
    _ = self.make_call(url)
    if _ is None:
      return ""
    l = _.readlines()
    _ = []
    for line in l:
      if line.strip().startswith("#"):
        continue
      _.append(line)
    return _

  def make_call(self, url):
    import HttpTools
    try:
      res = HttpTools.make_url_call(url, values = '', http_timeout=5)
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
