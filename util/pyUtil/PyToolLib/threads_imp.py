import olex
import olex_core
import olx
import os
import sys
from threading import Thread
from threads import ThreadEx
from threads import ThreadRegistry
from olexFunctions import OV

class NewsImageRetrivalThread(ThreadEx):
  instance = None
  image_list = {}
  active_image_list = {}

  def __init__(self, name):
    ThreadRegistry().register(NewsImageRetrivalThread)
    Thread.__init__(self)
    self.name = name
    self.olex2tag = get_tag()
    NewsImageRetrivalThread.instance = self
    olex.registerFunction(self.get_server_content, False, 'internal')
    olex.registerFunction(self.get_sample_list, False, 'internal')
    olex.registerFunction(self.get_structure_from_url, False, 'internal')
    olex.registerFunction(self.get_styles_from_url, False, 'internal')

  def run(self):
    import copy
    import random
    import olex_fs
    try:
      olex_core.IncRunningThreadsCount()
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
            try:
              img_data = img.read()
            except:
              print("Could not read image data from news list")
              return
            if self.name == "splash":
              with open(os.path.join(olx.app.SharedDir(), 'splash.jpg'),'wb') as wFile:
                wFile.write(img_data)
              with open(os.path.join(olx.app.SharedDir(), 'splash.url'),'w') as wFile:
                wFile.write(url)
              with open(os.path.join(olx.app.SharedDir(), 'splash.id'),'w') as wFile:
                wFile.write(img_url)
            elif self.name == "news":
              olex.writeImage(img_url, img_data)
        tag = self.olex2tag.split('-')[0]
        if img_data and self.name == "news":
          olex.writeImage("news/news-%s_tmp" %tag, img_data)
          olx.SetVar('olex2.news_img_link_url', url)
          olx.Schedule(1, "spy.internal.resizeNewsImage()")
    except:
      sys.stdout.formatExceptionInfo()
      pass
    finally:
      olex_core.DecRunningThreadsCount()
      NewsImageRetrivalThread.instance = None

  def get_image_from_list(self):
    img_url = None
    img_list = NewsImageRetrivalThread.active_image_list.get(self.name,None)
    if not img_list:
      return
    img_id = ""
    tags = None
    res_idx = -1
    if self.name == 'splash':
      #if "-ac" in self.olex2tag:
        #return None,None
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
          if len(_) == 2 or (len(_) > 2 and self.olex2tag in _[2:]):
            if (idx +1) < len(img_list):
              res_idx = idx
              break

      for idx in range(0, len(img_list)):
        res_idx += 1
        if res_idx >= len(img_list):
          res_idx = -1
        res = img_list[res_idx]
        if "," in res:
          _ = res.split(',')
          if len(_) == 2:
            if "-ac" in self.olex2tag:
              continue
            img_url, url = _
            tags = None
          elif len(_) > 2:
            img_url, url = _[:2]
            tags = _[2:]
        else:
          img_url = res
          url = "www.olex2.org"

        if tags and self.olex2tag not in tags:
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
        if tags and self.olex2tag not in tags:
          img_url = None
          continue
        else:
          if "-ac" in self.olex2tag:
            continue
          break

    if not img_url:
      return None, None

    if "://" not in img_url:
      return "http://%s" %(img_url.strip()), url.strip()
    return img_url.strip(), url.strip()
  
  def get_sample_list(self, which='samples', ext="html", urlbase="defaultURL"):
    self.get_server_content(which=which, ext=ext, urlbase=urlbase)

  def get_server_content(self, which='samples', ext="html", urlbase="defaultURL"):
    if urlbase == "defaultURL":
      urlbase = OV.GetParam('olex2.samples.url')
    url = f"{urlbase}/{which}.{ext}"
    _ = self.make_call(url)
    if _ is None:
      print(f"{url} can not be reached")
      return ""
    from gui import help

    cont = _.read().decode()
    if ext == "md":
      cont = help.gh.convert_md_to_html(md_input=cont)
    help.gh.make_help_box(helpTxt=cont, name=f"{which}")

  def get_structure_from_url(self, name, url=None):
    isZip = False
    if not url:
      url = OV.GetParam('olex2.samples.url')

    if ".zip" not in name:
      url = '%s/%s.cif' %(url, name)
    else:
      url = '%s/%s' %(url, name)
      isZip = True

    reap_base = None
    if not isZip:
      p = os.path.join(OV.DataDir(), 'samples', name)
      if not os.path.exists(p):
        _ = self.make_call(url)
        if _ is None:
          return ""
        os.makedirs(p)
      pp = os.path.join(p, name + '.cif')
      if not os.path.exists(pp):
        cont = _.read().decode()
        with open(pp, 'w') as wFile:
          wFile.write(cont)
      reap_base = os.path.splitext(pp)[0]
    else:
      bare_name = os.path.splitext(name)[0]
      p = os.path.join(OV.DataDir(), 'samples', bare_name)
      pp = p + ".zip"
      reap_base = os.path.join(p, bare_name)
      if not os.path.exists(p):
        _ = self.make_call(url)
        if _ is None:
          print("Are you online?")
          return ""
        cont = _.read()
        with open(pp, 'wb') as wFile:
          wFile.write(cont)
        import zipfile
        with zipfile.ZipFile(pp, 'r') as zip_ref:
          zip_ref.extractall(p)
    if reap_base:
      for ext in ['res', 'ins', 'cif']:
        fn = "%s.%s" %(reap_base, ext)
        if os.path.exists(fn):
          olex.m("reap '%s'" %fn)
          return

  def get_styles_from_url(self, name, url=None):
    if not url:
      url_base = OV.GetParam('olex2.samples.url')
    l = [('style','glds'), ('scene','glsp')]
    p = os.path.join(OV.DataDir(), 'styles')
    if not os.path.exists(p):
      os.makedirs(p)
    for item in l:
      url = '%s/%s.%s' %(url_base, name, item[1])
      _ = self.make_call(url)
      if _ is None:
        return ""
      pp = os.path.join(p, name + "." + item[1])
      cont = _.read().decode()
      with open(pp, 'w') as wFile:
        wFile.write(cont)
      import gui.tools
    gui.tools.set_style_and_scene(style=name, scene=name, src_dir=p)

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
      if line.strip().startswith(b"#"):
        continue
      _.append(line.decode('utf-8'))
    return _

  def make_call(self, url):
    import HttpTools
    try:
      res = HttpTools.make_url_call(url, http_timeout=5)
    except Exception as err:
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
      olex_core.IncRunningThreadsCount()
      cif.GetCheckcifReport(send_fcf=self.send_fcf)
    except Exception as e:
      pass
    finally:
      olex_core.DecRunningThreadsCount()
      CheckCifRetrivalThread.instance = None

def get_news_image_from_server(name=""):
  from olexFunctions import OlexFunctions
  if not OV.canNetwork(show_msg=False):
    return
  if NewsImageRetrivalThread.instance is None:
    NewsImageRetrivalThread(name).start()
olex.registerFunction(get_news_image_from_server)

def resizeNewsImage():
  from PilTools import TI
  TI.resize_news_image(vfs=True)
  img_url = olx.GetVar('olex2.news_img_link_url', '')
  if img_url:
    OV.SetParam('olex2.news_img_link_url', img_url)
    olx.UnsetVar('olex2.news_img_link_url')
olex.registerFunction(resizeNewsImage, False, 'internal')


def GetCheckcifReport(send_fcf=False):
  from olexFunctions import OlexFunctions
  if not OV.canNetwork():
    return
  if CheckCifRetrivalThread.instance is None:
    CheckCifRetrivalThread(OV.get_bool_from_any(send_fcf)).start()
  else:
    olx.Alert("Please wait", "The Checkcif request is in progress", "IO")
olex.registerFunction(GetCheckcifReport, False, 'cif')

def get_tag():
  tag = OV.GetTag()
  if "-ac" in tag:
    t = tag.split("-")
    return "-".join(t[:2])
  else:
    return tag