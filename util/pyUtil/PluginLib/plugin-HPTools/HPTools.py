from __future__ import division
import os
import glob
import olx
import olex
import olexex
import time
import shutil
import sys

from olexFunctions import OlexFunctions
OV = OlexFunctions()

from ImageTools import ImageTools
IT = ImageTools()

import olex_core

import OlexVFS
print "Importing HPTools ..."

from RunPrg import RunRefinementPrg

sys.path.append("%s/util/pyUtil/PluginLib/plugin-AC2" %OV.BaseDir())

from AC2 import AC2
ac2 = AC2()


import SQLAlchemy


def db_test():
  pass
#  from sqlalchemy import create_engine
#  engine = create_engine('sqlite:///:memory:', echo=True)#

import time


def mm_observer(msg):
  print msg

def mm():
  f1 = OV.FileFull()
  f2 = "%s/originals/%s.res" %(OV.StrDir(), OV.FileName())
  exe = "%s/mm/%s.exe" %(OV.BaseDir(), "SimMKforOlexSys")
  p = '"%s" "%s" -c 2> %s/mm.txt' %(f1, f2, OV.FilePath())
  OV.registerCallback("procout", mm_observer)
  os.system("%s %s" %(exe,p))
#  olex.m('exec %s %s' %(exe, p))
  OV.unregisterCallback("procout", mm_observer)
OV.registerFunction(mm)

def r(name='fred', number_to_average=50):
  l = []
  number_to_average = int(number_to_average)
  rFile = open(r"%s\util\pyUtil\PluginLib\plugin-AC2\report\%s.csv" %(OV.BaseDir(),name), 'r').readlines()
  m =[]
  total_number = len(l)
  a = b = c = 0
  i = 0
  j = 0
  for line in rFile:
    i += 1
    j += 1
    line = line.split(',')
    if len(line) == 2:
      a += float(line[0])
      b += float(line[1])
      if i == number_to_average or i == total_number:
        m.append("%s %s %s\n" %(j, a/i, b/i))
        i = 0
        a = b = 0
    elif len(line) == 3:
      a += float(line[0])
      b += float(line[1])
      c += float(line[2])
      if i == number_to_average or i == total_number:
        m.append("%s %s %s %s\n" %(j, a/i, b/i, c/i))
        i = 0
        a = b = c = 0
        
        
  wFile = open(r"%s\util\pyUtil\PluginLib\plugin-AC2\report\%s%s.txt" %(OV.BaseDir(),name, number_to_average), 'w')
  for line in m:
    wFile.write(line)
  wFile.close()
  
OV.registerFunction(r)


def a():
  from Analysis import X_Y_plot
  XY = X_Y_plot()
  data = {}
  meta = {
    'imSize':(512,512),
    'Title':'Stats',
    'pop_html':'stats',
    'pop_name':'stats',
    "TopRightTitle":"",
    "FontScale":0.025,
  }
  data.setdefault('meta',meta)
    
  series = []
  metadata = {}
  x = [1,2,3]
  y = [1,2,3]
  series.append((x,y,metadata))
  x = [1,2,3]
  y = [1,4,9]
  series.append((x,y,metadata))
  x = [1,2,3]
  y = [1,12,20]
  series.append((x,y,metadata))
  
  data.setdefault('series',series)
    
  XY.run(data)
  
OV.registerFunction(a)

def m():
  import matplotlib
  import matplotlib.pyplot as plt
  plt.figure()
  #create some data
  x_series = [0,1,2,3,4,5]
  y_series_1 = [x**2 for x in x_series]
  y_series_2 = [x**3 for x in x_series]
 
  #plot the two lines
  plt.plot(x_series, y_series_1)
  plt.plot(x_series, y_series_2)
  plt.savefig("example.png")
  
OV.registerFunction(m)


def go_through_list():
  rFile = open(r"G:\HP\olex2-trunk\util\pyUtil\PluginLib\plugin-AutoChem2\report\list.txt", 'r').readlines()
  open_every_n = 1
  l = []
  wFile = open(r"G:\HP\olex2-trunk\util\pyUtil\PluginLib\plugin-AutoChem2\report\list_res.txt", 'w')
  for p in rFile:
    p = p.strip()
    path = '%s%s' % (r"G:/HP/", p)
    if not os.path.exists(path):
      continue
    olex.m('@reap %s' %file)
    html = "<html> Fred </html>"
    res = make_evaluate_html()
    if res:
      evaluate = olx.GetValue('Evaluate.EVALUATE')
    else:
      return
    l.append("%s,%s\n" %(p, evaluate))
    wFile.write("%s,%s\n" %(p, evaluate))
    wFile.flush()
OV.registerFunction(go_through_list)    
  
  
def make_evaluate_html():
  pop_name = "Evaluate"
  if OV.IsControl('%s.WEB_USERNAME'%pop_name):
    olx.html.ShowModal(pop_name)
  else:
    txt='''
  <body link="$GetVar(HtmlLinkColour)" bgcolor="$GetVar(HtmlBgColour)">
  <font color=$GetVar(HtmlFontColour  size=$GetVar(HtmlFontSize) face="$GetVar(HtmlFontName)">
  <table border="0" VALIGN='center' style="border-collapse: collapse" width="100%%" cellpadding="1" cellspacing="1" bgcolor="$GetVar(HtmlTableBgColour)">
  <tr>
    <td>
    Evaluate:
    </td>
     <td>

       <input
         type="text"
         bgcolor="$GetVar(HtmlInputBgColour))"
         valign='center'
         name="EVALUATE"
         reuse
         width="90"
         height="20"
         value = "">
     </td>
     </tr>
     <tr>
     <td>
     </td>
     <td valign='centre'>
       <input
         type="button"
         bgcolor="$GetVar(HtmlInputBgColour))"
         valign='center'
         width="60"
         height="22"
         onclick="html.EndModal(Evaluate,1)"
         value = "OK">
       <input
         type="button"
         bgcolor="$GetVar(HtmlInputBgColour))"
         valign='center'
         width="60"
         height="22"
         onclick="html.EndModal(Evaluate,0)"
         value = "Cancel">
     </td>
     </tr>

     </table>
     </font>
     </body>
     '''

    OV.write_to_olex("evaluate.htm", txt)
    boxWidth = 280
    boxHeight = 180
    x = 200
    y = 200
    olx.Popup(pop_name, 'evaluate.htm', "-s -b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(pop_name, boxWidth, boxHeight, x, y))
    res = olx.html.ShowModal(pop_name)
    res = int(res)
    return res


def t(cmd='hide'):
  
  d = {}
  d.setdefault('make_bitmap_image',"$spy.MakeHoverButton(button_small-go@bitmapp,cursor\(busy,'Please Wait. Making image. This may take some time')>>run 'pict -pq strcat\(GetValue\(IMAGE_BITMAP_NAME).,GetValue\(IMAGE_BITMAP_TYPE)) GetValue\(IMAGE_BITMAP_SIZE)'>>cursor\()")
  d.setdefault('hide',"$spy.MakeHoverButton(button_small-go@bitmapp,echo Thanks.")
  
  
  html = '<html>%s>>html.hide test)</html>' %d[cmd]
  html = '<html><a href="html.hide test"><zimg border="0" src="news/news-1.2"></a></html>'
  
  print html
  
  
  x = int(olx.GetMouseX())
  y = int(olx.GetMouseY())
  name = 'test'
  boxWidth = 200
  boxHeight = 200
  pop_name = "Test"
  wFilePath = r"%s.htm" %(name)
  OV.write_to_olex(wFilePath, html)

#  olx.Popup(pop_name, wFilePath, "-b=tc -t='%s' -w=%i -h=%i -x=%i -y=%i" %(name, boxWidth, boxHeight, x, y))

  olx.Popup(pop_name, wFilePath, "-w=%i -h=%i -x=%i -y=%i" %(name, boxWidth, boxHeight, x, y))
  
  
  print 'Hello'
OV.registerFunction(t)
  

class DBReader():
  def __init__(self):
    self.session = SQLAlchemy.get_session()
    self.drive_letter = OV.GetParam('hptools.batch.drive_letter')


  def get_query(self, use_db=None, exclude=""):
    op_disp = None
    if not use_db:
      use_db = OV.GetParam('hptools.batch.database')
    self.session = SQLAlchemy.get_session(use_db)
    if use_db == "--":
      if not op_disp: op_disp = "--"
      return
    
    action = OV.GetParam('hptools.batch.action')
    new_only = OV.GetParam('hptools.batch.run_new_only')
    self.q_list = []

    if exclude:
      table = getattr(SQLAlchemy, exclude)
      q_previous = self.session.query(table).all()
      self.q_list.append(q_previous)
      return "Previously excluded"
    
    filter_display = ""
    use_table1 = OV.GetParam('hptools.batch.filter_1.table')
    use_table2 = OV.GetParam('hptools.batch.filter_2.table')
    i = 0
    for use_table in [use_table1, use_table2]:
      i += 1
      if not use_table or use_table == "--":
#        q = None
#        self.q_list.append(q)
        continue
      var = OV.GetParam('hptools.batch.filter_%s.var' %i)
      op = OV.GetParam('hptools.batch.filter_%s.operator' %i)
      val = OV.GetParam('hptools.batch.filter_%s.val' %i)
      table = getattr(SQLAlchemy, use_table)
      if var == "--":
        q = self.session.query(table).all()
        self.q_list.append(q)
        if not op_disp: op_disp = "--"
        continue
      filter_item = getattr(table, var)
      if op == "<":
        q = self.session.query(table).filter(filter_item < val)
        op_disp = "&lt;"
      elif op == ">":
        q = self.session.query(table).filter(filter_item > val)
        op_disp = "&gt;"
      elif op == "=":
        q = self.session.query(table).filter(filter_item == val)
        op_disp = "="
      elif op == "!=":
        q = self.session.query(table).filter(filter_item != val)
        op_disp = "!="
      elif op == "cont":
        q = self.session.query(table).filter(filter_item.like("%" + val + "%"))
        op_disp = "contains"
      else:
        q = self.session.query(table).all()
      self.q_list.append(q)

      if filter_display:
        filter_display += " and "
      filter_display += "%s %s %s" %(var, op_disp, val)
    return filter_display

  def get_filtered_list(self, exclude=""):
    l = []
    filter_display = self.get_query(exclude=exclude)
    i = 0
    for q in self.q_list:
      l.append([])
      if not q:
        continue
      for item in q:
        p = item.path.lower()
        p = self.deal_with_drive_letter(p)
        l[i].append(p)
      i += 1
      
    if len(l) == 0:
      retVal = []
      
    elif len(l) == 1:
      retVal = l[0]
    
    else:
      m = []
      l1 = l[0]
      l2 = l[1]
      for item in l1:
        if item in l2:
          m.append(item)
      retVal = m

    return retVal, filter_display
  
  def deal_with_drive_letter(self, p):
    self.drive_letter = OV.GetParam('hptools.batch.drive_letter')
    if not p.lower().startswith(self.drive_letter):
      p = p.lower().replace('d:/', '%s/' %self.drive_letter)
    return p
  
  def filter_query(self):
    self.q = q
    
  def get_data(self):
    series = []
    
    x1 = []
    y1 = []
    hrefs1 = []
    targets1 = []
    x2 = []
    y2 = []
    hrefs2 = []
    targets2 = []
    
    self.q = self.get_query()
    if not self.q.count():
      print "No result"
      return
    i = 0
    
    filter_var_1 = OV.GetParam('hptools.batch.filter_1.var')
    filter_operator_1 = OV.GetParam('hptools.batch.filter_1.operator')
    try:
      filter_value_1 = float(OV.GetParam('hptools.batch.filter_1.val'))
    except:
      filter_value_1 = OV.GetParam('hptools.batch.filter_1.val')

    for ID, path, g4_r1_original, g4_r1_after in q:
      path = sort_out_drive(path)
      if g4_r1_after > 1:
        continue
      if g4_r1_original > 1:
        continue
      if filter_operator_1 == '<':
        if g4_r1_after/g4_r1_original < filter_value_1:
          continue
      elif filter_operator_1 == '>':
        if g4_r1_after/g4_r1_original > filter_value_1:
          continue
      elif filter_operator_1 == '=':
        if g4_r1_after/g4_r1_original != filter_value_1:
          continue

      x1.append(i)
      y1.append(g4_r1_original)
      hrefs1.append("reap %s" %path)
      targets1.append(ID)
      x2.append(i)
      y2.append(g4_r1_after)
      hrefs2.append("reap %s" %path)
      targets2.append(ID)
      i += 1
      
    series = [(x1,y1,hrefs1,targets1,
               {'label':'G4_R1_original',
                }),
              (x2,y2,hrefs2,targets2,
               {'label':'G4_R1_after',
                #'fit_slope':True,
                #'fit_y_intercept':1,
                }),
              ]
    make_xy_graph(series)
      
#      print "Atom Count of structure %s is %s " %(ID, q.value('atom_count'))


DBRReader_instance = DBReader()
OV.registerFunction(DBRReader_instance.get_data,False,'hp')


def make_xy_graph(series,):
  from Analysis import X_Y_plot
  XY = X_Y_plot()
  
  XY.graphInfo["imSize"] = (512,512)
  XY.graphInfo["Title"] = 'Statistics'
  XY.graphInfo["pop_html"] = 'stats'
  XY.graphInfo["pop_name"] = 'stats'
  XY.graphInfo["TopRightTitle"] = ""
  XY.graphInfo["FontScale"] = 0.025
  
  XY.series = series
  XY.run()




class FileCrawlies():
  def __init__(self):
    from Analysis import HealthOfStructure
    self.HOS = HealthOfStructure()
    #from g4 import g4
    #self.g4 = g4()
    self.DBR = DBReader()
    
    phil_file = r"%s/util/pyUtil/PluginLib/plugin-HPTools/hptools.phil" %(OV.BaseDir())
    self.plugin_path = r"%s/util/pyUtil/PluginLib/plugin-HPTools" %(OV.BaseDir())
    olx.phil_handler.adopt_phil(phil_file=phil_file)
    
    self._deal_with_phil()
    import FileSystem as FS
    self.mask = OV.GetParam('hptools.filecrawlies.mask')
    self.path = OV.GetParam('hptools.filecrawlies.path')
    self.path_from = OV.GetParam('hptools.filecrawlies.path_from')
    self.path_to = OV.GetParam('hptools.filecrawlies.path_to')
    self.overwrite = OV.GetParam('hptools.filecrawlies.overwrite')
    self.lowercase = OV.GetParam('hptools.filecrawlies.lowercase')
    self.graphX = [[],[]]
    self.graphY = [[],[]]
    self.marker_count=0
    #self.exclude_on_atom_count = 60
    self.exclude_on_run_original = OV.GetParam('hptools.batch.run_new_only')
    self.drive_letter = OV.GetParam('hptools.batch.drive_letter')
    self.db_table = OV.GetParam('hptools.batch.db_table')
    self.add_filecrawlies_link_to_index()


  def add_filecrawlies_link_to_index(self):
    ''' Automatically add a link to the HPTools GUI to an Olex2 index file. This link is not currently tidied up on exit. '''
    txt = OlexVFS.read_from_olex('%s/etc/gui/blocks/index-info.htm' %OV.BaseDir())
    t = r'''
<!-- #include database BaseDir()/util/pyUtil/PluginLib/plugin-HPTools/db_graphs.htm;gui\blocks\tool-off.htm;image=Database;onclick=;1; -->'''
    if t not in txt:
      txt = OlexVFS.write_to_olex('%s/etc/gui/blocks/index-info.htm' %OV.BaseDir(), txt + t, 0)

    
  def delete_all_dot_olex_folders(self):
    p = r"%s%s" %(OV.GetParam('hptools.batch.drive_letter'), OV.GetParam('hptools.batch.directory'))
    g = glob.glob("%s/%s" %(p,'*'))
    for folder in g:
      o = glob.glob("%s/%s" %(folder, '.olex'))
      for dotolex in o:
        shutil.rmtree(dotolex)
      h = glob.glob("%s/%s" %(folder, '*'))
      for folder1 in h:
        o = glob.glob("%s/%s" %(folder1,'.olex'))
        for dotolex in o:
          shutil.rmtree(dotolex)
        
    
  def _deal_with_phil(self, operation='read'):
    user_phil_file = "%s/hptools_user.phil" %(OV.DataDir())
    phil_file = r"%s/util/pyUtil/PluginLib/plugin-HPTools/hptools.phil" %(OV.BaseDir())
    if operation == "read":
      phil = open(phil_file, 'r').read()
      olx.phil_handler.adopt_phil(phil_string=phil)
      if os.path.exists(user_phil_file):
        olx.phil_handler.update(phil_file=user_phil_file)
    elif operation == "save":
      olx.phil_handler.save_param_file(
      file_name=user_phil_file, scope_name='hptools', diff_only=True)
    

  def get_exclude_l(self):
    exclude_l = []
    exclude_txt_files = ["FailedReap", "TooLarge", "CrashedFiles", "NoReflectionFile", "CurrentFile"]
    for f in exclude_txt_files:
      p = "%s/exclude_%s.txt" %(OV.DataDir(),f)
      if os.path.exists(p):
        rFile = open(p,'r')
        _ = rFile.readlines()
        for file in _:
          file = file.replace(".res", ".ins")
          exclude_l.append(file.strip())
        rFile.close()
        if f == "CurrentFile":
          self.add_to_exclude_file(file, "CrashedFiles")
    self.exclude_l = exclude_l

  def log_current_file(self, file):
    fie = file.replace(".res", ".ins")
    p = "%s/CurrentFile.txt" %OV.DataDir()
    if os.path.exists(p):
      os.remove(p)
    if file == "Done":
      return
    wFile = open(p,'w')
    wFile.write(file)
    wFile.write("\n")
    wFile.close()
    
  def bulk_copy_files (self):
    self.bulk_action_files(action='copy')

  def write_bulk_load_html(self, l, p, i, msg="", new=False):
    return
    first_col = OV.GetParam('gui.html.table_firstcol_width')
    if new:
      wFile = open("%s/batch_list.htm" %OV.DataDir(), 'w')
    else:
      _ = "%s/batch_list.htm" %OV.DataDir()
      if not os.path.exists(_):
        wFile = open(_, 'w')
        wFile.close()
      wFile = open(_, 'rb')
      c = wFile.readlines()
      wFile.close()
      wFile = open("%s/batch_list.htm" %OV.DataDir(), 'w')
    txt = "<tr><td width='%s'></td><td colspan='4'><b>File %i out of %i where %s</b></td></tr>\n" %(first_col, i, len(l), self.filter_display)
    wFile.write(txt)
    if new:
      for item in l:
        tem = item.split('/')[-1:][0].split('.')[0]
        txt = '''
<tr><td></td><td width='60'><a href='reap "%s"'>%s</a></td><td>In Queue</td></tr>\n''' %(item, tem)
        wFile.write(txt)
      #txt += '''
#<!-- #include row_table_off gui\blocks\row_table_off.htm;1; -->'''

    else:
      i = 0
      for line in c:
        if "out of" in line:
          continue
        if p:
          if p in line:
            tem = p.split('/')[-1:][0].split('.')[0]
            line = '''
<tr><td></td><td width='60'><a href='reap "%s"'>%s</a></td><td>%s</td></tr>\n''' %(p, tem, msg)
            line = line.replace("<tr><td></td>", "<tr><td bgcolor='#205c90'></td>")
        else:
          for q in l[i:]:
            if q in line:
              line = line.replace("<tr><td></td>", "<tr><td bgcolor='#4b0000'></td>")
              line = line.replace("<tr><td bgcolor='#205c90'></td>", "<tr><td bgcolor='#4b0000'></td>")
              break
            tem = q.split('/')[-1:][0].split('.')[0]
            line = '''
<tr><td></td><td width='60'><a href='reap "%s"'>%s</a></td><td>%s</td></tr>\n''' %(q, tem, "In Queue")
            line = line.replace("<tr><td></td>", "<tr><td bgcolor='#4b0000'></td>")
            line = line.replace("<tr><td bgcolor='#4b0000'></td>", "<tr><td bgcolor='#205c90'></td>")
            break
        i += 1  
        wFile.write(line.replace('\r',''))
    wFile.close()
    olx.html.Update()
    
  def get_list_from_text(self, make_copy=False):
    l = open(r"%s/list.txt" %self.plugin_path, 'r').readlines()
    if make_copy:
      destination = "G:/HP/DS_COPY"
      for path in l:
        path = path.lower()
        path = path.strip()
        directory = "%s/%s" %(destination, path.split("/")[0])
        if not os.path.exists(destination):
          os.makedirs(destination)
        path_to = destination + "/" + "/".join(path.split("/")[:-1])
        path_from = self.drive_letter + "/DSA/" + "/".join(path.split("/")[:-1])
        c_to = "%s/%s" %(destination, path)
        c_from = "%s/.olex/originals/%s.res" %(path_from, path.split('/')[-1:][0].split('.')[0])
        if not os.path.exists(c_to):
          os.makedirs(path_to)
        shutil.copyfile(c_from, c_to)
        c_to = c_to.replace('.res', '.hkl')
        c_from = "%s/%s.hkl" %(path_from, path.split('/')[-1:][0].split('.')[0])
        shutil.copyfile(c_from, c_to)
      pass

    m = []
    for f in l:
      m.append("%s/%s" %(r'G:/HP/DS_COPY', f.strip()))
      
    return m
  
       
  def bulk_load_files (self, action=''):
    self._deal_with_phil(operation='save')
    self.get_exclude_l()
    self.use_db = OV.GetParam('hptools.batch.database')
    action = OV.GetParam('hptools.batch.action')
    self.session = SQLAlchemy.get_session(self.use_db)
    filter_list = []
    previous_run_dbr_l = []
    self.filter_display = "no filter was used."
    if self.use_db != "--":
      filter_list, self.filter_display = self.DBR.get_filtered_list()
      self.exclude_on_run_original = OV.GetParam('hptools.batch.run_new_only')
    else:
      self.exclude_on_run_original = False
      action = 'scan'
      OV.SetParam('hptools.batch.action','ac2')
    
#    if action == "scan":
#      previous_run_dbr_l, self.previous_display = self.DBR.get_filtered_list(exclude='Structure')

    if action == "ac2":
      if OV.GetParam('hptools.batch.run_new_only'):
        previous_run_dbr_l, self.previous_display = self.DBR.get_filtered_list(exclude='ac2')
      else:
        previous_run_dbr_l, self.previous_display = self.DBR.get_filtered_list(exclude=None)
      
    if action == "oda":
      previous_run_dbr_l, self.previous_display = self.DBR.get_filtered_list(exclude='oda')
      
      
    l = self.bulk_action_files(action=action)
    
    if l:
      if self.use_db != "--":
        m = []
        for item in l:
          tem = item.lstrip(self.drive_letter)
          if tem.startswith("DS"): tem = tem.lstrip("DS")
          if action == "scan":
            if tem.lower() not in filter_list:
              m.append(item)
          else:
            if tem.lower() in filter_list:
              if OV.GetParam('hptools.batch.run_new_only'):
                if tem.lower() not in previous_run_dbr_l:
                  m.append(item)
              else:
                if tem.lower() in previous_run_dbr_l:
                  m.append(item)
                
        l = m
    elif not l:
      l = filter_list
    
    if not l:
      self.write_bulk_load_html(l, p="", i=0, new=False)
      print "Nothing to do"
      return
    if self.exclude_on_run_original:
      new = False
    else:
      new = True
    self.write_bulk_load_html(l, p="", i=0, new=new)
    if not action or action == "filter":
      return
    
    print("There are %s files in the list to do" %len(l))
    i = 0
    for file in l:
      #self.write_bulk_load_html(l, file, i, " *")
      i += 1
      if not file:
        continue
      if self.exclude_file(file):
        continue
      try:
        self.log_current_file(file)
        if OV.GetParam('olex2.stop_current_process'):
          print "Interrupted"
          return
        if file.replace(".res",".ins") in self.exclude_l:
          self.write_bulk_load_html(l, file, i, "Excluded")
          continue
        if self.reap_file(file):
          #self.make_image(file)
          #self.refine_file(file)
          #res = self.autochem_file(file)
          if action == "scan":
            print "Next up %s" %file
            olexex.revert_to_original()
            try:
              R1 = olx.CalcR()
              if R1:
                self.R1 = float(olx.CalcR().split(",")[1])
              else:
                self.add_to_exclude_file(file, 'FailedR1')
            except Exception, err:
              print "Something went wrong with getting the R factor: %s" %err
            try:  
              if self.use_db == "--":
                self.use_db = str(int(time.time()))
                OV.SetParam('hptools.batch.database', self.use_db)
                self.session = SQLAlchemy.get_session(self.use_db)
              path = file.lstrip(self.drive_letter)  
              self.add_to_db(path)
              self.session.commit()
            except Exception, err:
              print "Something went wrong with adding to db: %s" %err
              self.session.rollback()
              self.add_to_exclude_file(file, 'FailedR1')
              
          if action == "ac2" or action == "ac2_list":
            res = self.run_ac2(file)
            if res:
              try:
                self.session.commit()
              except:
                #self.add_to_exclude_file(file, "FailedCommit")
                res = res + "</td><td>Failed Commit"
            else:
              res = 'Mystery'
            self.write_bulk_load_html(l, file, i, res)
          
      except Exception, err:
        print "Something went wrong with %s: %s" %(OV.FileName(), err)
    self.log_current_file("DONE")
    
    
  def run_ac2(self, file):
    return self.run_auto_file(file, 'ac2')

  def run_oda(self, file):
    return self.run_auto_file(file, 'oda')
    
  def run_oda_and_ac2(self, file):
    self.run_auto_file(file, 'oda')
    self.run_auto_file(file, 'ac2')

  def run_auto_file(self, file, which):
    if not OV.HKLSrc():
      return False
#    olexex.revert_to_original()
#    self.r1_original = float(olx.CalcR().split(",")[1])
#    ata = olx.ATA(1)
    self.ata_original = 0.00
    self.r1_original = 0.00

    t = time.time()
    
    if which == "ac2":
      ac2.auto()
   
    elif which == "oda":  
      olex.m('oda')
      
    ata = olx.ATA(1)
    ata = float(ata.split(';')[1])
    t = (time.time() - t)
    r1 = float(olx.CalcR().split(",")[1])


    achieved = "No" 
    
    div_by_zero_bit = 0.00001
    ratio_r = (self.r1_original)/(r1+div_by_zero_bit)
    if ratio_r >= 0.9:
      font_colour = OV.GetParam('gui.green')
      achieved = "Yes"  
    elif ratio_r >= 0.8:
      font_colour = OV.GetParam('gui.orange')
      achieved = "Maybe"  
    elif ratio_r < 0.7:
      font_colour = OV.GetParam('gui.red')
      achieved = "No"  
    ratio_ata = (self.ata_original)/(ata + div_by_zero_bit)
    if ratio_ata <= 1:
      font_colour_a = OV.GetParam('gui.green')
      achieved = "Yes"
    elif ratio_ata <= 1.1:
      font_colour_a = OV.GetParam('gui.orange')
      achieved = "Maybe"
    elif ratio_ata > 1.1:
      font_colour_a = OV.GetParam('gui.red')
    ata_ret = "<b>ATA = </b>%.0f/<font color='%s'>%.0f</font>" %(self.ata_original, font_colour_a, ata)

    setattr(self, "achieved_%s" %which, achieved)
    setattr(self, "solution_name_%s" %which, "%s_%s" %(OV.GetParam('snum.solution.program'),OV.GetParam('snum.solution.method')))
    setattr(self, "t_%s" %which, "%.1f" %t)
    setattr(self, "r1_%s" %which, r1 )
    setattr(self, "ata_%s" %which, ata)
    setattr(self, "formula_%s" %which, olx.xf.au.GetFormula())
    setattr(self, "match_%s" %which, "n/a")

    path = file.lstrip(self.drive_letter)
    try:
      if which == "oda":
        self.add_oda_to_db(path)
      elif which == "ac2":
        self.add_ac2_to_db(path)
    except Exception, err:
      print err

      
    r1_ret = "<b>R1 = </b>%.2f/<font color='%s'>%.2f</font>" %((self.r1_original * 100), font_colour, (r1 * 100))
    t_ret = "<b>t = </b>%.1f" %t
    
    return r"%s</td><td>%s</td><td>%s" %(ata_ret, r1_ret, t_ret)
  
  def autochem_file(self, file):
    if OV.HKLSrc():
      l = [('ShelXS','Direct Methods'), ('olex2.solve','Charge Flipping'), ('SIR2008', 'Direct Methods'), ('g4','default')]
      l = [('ShelXS','Direct Methods'), ('olex2.solve','Charge Flipping'), ('SIR2008', 'Direct Methods'), ('g4','default')]
      for tup in l:
        prg = tup[0]
        method = tup[1]
        prg = prg.replace('.','')
        self.run_prg(prg, method)
      try:
        self.add_odac_to_db(file)
        #self.make_graph()
      except Exception, err:
        print err
      return True
    
  def run_prg(self, prg, method):
    olexex.revert_to_original()
    try:
      self.r1_original = float(olx.CalcR().split(",")[1])
    except:
      self.r1_original = 1.0
    setattr(self, "%s_r1_original" %prg, self.r1_original)
    t = time.time()
    
    if prg == "g4":
      try:
        self.run_g4_auto(prg, method)
      except Exception, err:
        print err
        
    else:
      try:
        self.run_oda(prg, method)
      except Exception, err:
        print err
  
      
    self.t = time.time() - t
    setattr(self, "%s_t" %prg, self.t)
    try:
      self.r1_after = float(olx.CalcR().split(",")[1])
    except:
      self.r1_after = 1.0
    setattr(self, "%s_r1_after" %prg, self.r1_after)
    
  def run_g4_auto(self, prg, method):
      self.g4.auto()

  def run_oda(self, prg, method):
    if prg == "olex2solve": prg = "olex2.solve"
    OV.SetParam('autochem.solution.program', prg)
    OV.SetParam('autochem.solution.method', method)
    try:
      olex.m('oda')
    except:
      pass
    
    
  def make_graph(self):
    values = [self.ShelXS_r1_original, self.ShelXS_r1_after]
    no_of_series = len(values)
    if len(self.graphX) != no_of_series:
      self.graphX.append([])
      self.graphY.append([])
    i = 0
    for i in xrange(no_of_series):
      self.graphX[i].append(self.marker_count)
      self.graphY[i].append(values[i])
    self.marker_count += 1
    
    
    from Analysis import X_Y_plot
    XY = X_Y_plot()
    data = {}
    meta = {
      'imSize':(512,512),
      'Title':'Stats',
      'pop_html':'stats',
      'pop_name':'stats',
      "TopRightTitle":"",
      "FontScale":0.025,
    }
    data.setdefault('meta',meta)
    
    i = 0
    metadata = {}
    for tem in self.graphX:
      series = []
      x = self.graphX[i]
      y = self.graphY[i]
      series.append((x,y,metadata))
      i += 1
    
    data.setdefault('series',series)
      
    XY.run(data)

  def add_to_exclude_file(self, file, exclude_file_type):
    file = file.replace(".res", ".ins")
    _ = "%s/exclude_%s.txt" %(OV.DataDir(), exclude_file_type)
    if not os.path.exists(_):
      wFile = open(_,'w')
    else:
      wFile = open(_,'a')
    wFile.write(file)
    wFile.write("\n")
    wFile.close()

  def exclude_file(self, file):
    retVal = False
    if self.db_table == "--":
      return retVal
    if self.exclude_on_run_original:
      table = getattr(SQLAlchemy, self.db_table)
      val = file.lower()[1:]
      filter_item = getattr(table, 'path')
      q = self.session.query(table).filter(filter_item.like("%" + val + "%"))
      if q.count():
        return True
    elif file in self.exclude_l:
      msg = "%s --- previously excluded" %file
      print msg
      retVale = True
    else:
      return retVal
   
  def refine_file(self, file):
    if OV.HKLSrc():
      if self.session.query(SQLAlchemy.Structure.ID).filter_by(path=file.lower()).count() != 0:
        return
      olexex.revert_to_original()
      OV.set_refinement_program('ShelXL', 'CGLS')
      try:
        t = time.time()
        olex.m('refine 1 5')
        self.t_shelxl = time.time() - t
        self.R1_shelxl = olexex.GetRInfo(format='float')
      except Exception, err:
        print err
        self.R1_shelxl = 0
        
      olexex.revert_to_original()
      OV.set_refinement_program('olex2.refine', 'Gauss-Newton')
      try:
        t = time.time()
        olex.m('refine 1 5')
        self.t_olex2refine = time.time() - t
        self.R1_olex2refine = olexex.GetRInfo(format='float')
      except Exception, err:
        print err
        self.R1_olex2 = 0
   
  def reap_file(self, file):
    #olex.m('@reap %s' %file)
    olex.m('reap %s' %file)
    if OV.FileFull().lower() != file.lower():
      self.add_to_exclude_file(file, "FailedReap")
      return False
    if not OV.HKLSrc():
      self.add_to_exclude_file(file, "NoReflectionFile")
      return False
    return True

  def make_image(self,file=None):
    if not file:
      file = OV.FileFull()
      destination_folder = OV.FilePath()
    im_file_name = '%s\%s_auto.png' %(destination_folder, OV.FileName())
    olex.m("pict -pq %s %s" %(im_file_name, 650))
    
    txt_l = []
    
    txt_l.append((OV.FileName(), {'font_size':24,}))
    hos = self.HOS.get_HOS_d()
    if hos:
      txt = "%.2f%%(completeness)<br>%.2f%%(R<sub>int</sub>)" %(hos['Completeness']*100, hos['Rint']*100)
    else:
      txt = "No Reflection File!"
    txt_l.append((txt, {'font_size':18,
                        'line_gap':12,
                        'font_colour':'#ff0000',
                        'left':20,
                        }))
    
#    txt = OV.GetCrystalData()
#    txt_l.append((txt, {'font_size':18,
#                        'line_gap':12,
#                        'font_colour':'#4b0000',
#                        'left':20,
#                        }))
    
    im, draw = annotate_image_with_text(im_file_name, txt_l)
    im = IT.make_round_corners(im, radius=20, colour=(0,0,0,0))
    im.save(im_file_name)


  def add_ac2_oda_to_db(self, file):
    _ = SQLAlchemy.ac2_oda(ID=str(OV.FileName()),
                      path=str(file.lower()),
                      r1_original=self.r1_original,
                      r1_oda=self.r1_oda,
                      r1_ac2=self.r1_ac2,
                      ata_original=self.ata_original,
                      ata_oda=self.ata_oda,
                      ata_ac2=self.ata_ac2,
                      t_oda=self.t_oda,
                      t_ac2=self.t_ac2,
                      solution_name_oda=self.solution_name_oda,
                      solution_name_ac2=self.solution_name_ac2,
                      )
    self.session.add(_)


  def add_ac2_to_db(self, path):
    _ = SQLAlchemy.ac2(ID=str(OV.FileName()),
                      path=path,
                      r1_original=self.r1_original,
                      r1_ac2=self.r1_ac2,
                      ata_original=self.ata_original,
                      ata_ac2=self.ata_ac2,
                      time_ac2=self.t_ac2,
                      solution_ac2=self.solution_name_ac2,
                      achieved_ac2=self.achieved_ac2,
                      formula_ac2=self.formula_ac2,
                      match_ac2=self.match_ac2)
    __ = self.session.merge(_)
    self.session.add(__)
    
  def add_oda_to_db(self, file):
    _ = SQLAlchemy.oda(ID=str(OV.FileName()),
                      path=str(file.lower()),
                      r1_original=self.r1_original,
                      r1_oda=self.r1_oda,
                      ata_original=self.ata_original,
                      ata_oda=self.ata_oda,
                      time_oda=self.t_oda,
                      solution_oda=self.solution_name_oda)
    self.session.add(_)
    

  def add_odac_to_db(self, file):
    _ = SQLAlchemy.ODAC(ID=str(OV.FileName()),
                                   path=str(file.lower()),
                                   ShelXS_r1_original=self.ShelXS_r1_original,
                                   ShelXS_r1_after=self.ShelXS_r1_after,
                                   ShelXS_t=self.ShelXS_t,
                                   olex2solve_r1_original=self.olex2solve_r1_original,
                                   olex2solve_r1_after=self.olex2solve_r1_after,
                                   olex2solve_t=self.olex2solve_t,
                                   SIR2008_r1_original=self.SIR2008_r1_original,
                                   SIR2008_r1_after=self.SIR2008_r1_after,
                                   SIR2008_t=self.SIR2008_t,
                                   g4_r1_original=self.g4_r1_original,
                                   g4_r1_after=self.g4_r1_after,
                                   g4_t=self.g4_t,
                                   )
    self.session.add(_)
    
  def check_for_twinning_in_ins(self):
    txt = open(OV.FileFull(), 'r').read()
    if "twin" in txt.lower():
      return "True"
    else:
      return "False"
    
  def add_to_db(self, path):
    if not self.session:
      self.session = SQLAlchemy.get_session(self.use_db)
    hos = self.HOS.get_HOS_d()
    max_Z = olexex.FindZOfHeaviestAtomInFormua()
    olexex.revert_to_original()
    r1_original = float(olx.CalcR().split(",")[1])
    ata = olx.ATA(1)
    ata_original = float(ata.split(';')[1])
    from olexex import OlexRefinementModel
    ORM = OlexRefinementModel()
    atom_count = ORM.number_non_hydrogen_atoms()
    twin = self.check_for_twinning_in_ins()

    if hos:
      txt = "%.2f%%(comp), %.2f%%(Rint)" %(hos['Completeness']*100, hos['Rint']*100)
      _ = SQLAlchemy.Structure(ID=str(OV.FileName()),
                                   path=path,
                                   volume=olx.xf.au.GetVolume(),
                                   cell=olx.xf.au.GetCell(),
                                   formula=olx.xf.GetFormula(),
                                   atom_count=atom_count,
                                   space_group=olx.xf.au.GetCellSymm(),
                                   z_prime=olx.xf.au.GetZprime(),
                                   r1_original=r1_original,
                                   ata_original=ata_original,
                                   max_Z=max_Z,
                                   twin=twin,
                                   )
      __ = self.session.merge(_)
      self.session.add(__)
      #try:
        #self.session.add(_)
      #except:
        #self.session.merge(_)
      #finally:
        #print "DB PROBLEM"
      ##_ = SQLAlchemy.Reflections(ID=str(OV.FileName()),
                                   ##path=path,
                                   ##r_int=hos['Rint'],
                                   ##ios=hos['MeanIOverSigma'],
                                   ##completeness=hos['Completeness'],
                                   ##)
      ##__ = self.session.merge(_)
      ##self.session.add(__)
    else:
      txt = "No Reflection File!"
    print txt
    
      
  def bulk_action_files (self, mask="hklres", path_from=r"Z:", path_to=r"C:\DS\Data",overwrite=True,lowercase=True, action='copy', filename_in_filepath=True):
    phil_file = r"%s/util/pyUtil/PluginLib/plugin-HpTools/hptools.phil" %(OV.BaseDir())
    olx.phil_handler.adopt_phil(phil_file=phil_file)
    file_l = []
    path_from = OV.standardizePath(self.path_from)
    path_to = OV.standardizePath(self.path_to)
    path = OV.standardizePath(self.path)
    folders = []
    if action == 'copy':
      p = path_from
    if action == "ac2":
      p = r"%s%s" %(OV.GetParam('hptools.batch.drive_letter'), OV.GetParam('hptools.batch.directory'))
    if action == "ac2_list":
      c_from = r"%s/%s" %(OV.GetParam('hptools.batch.drive_letter'), 'DS_COPY')
      c_to = r"%s/%s" %(OV.GetParam('hptools.batch.drive_letter'), 'DS_COPY_NEW')
      if not os.path.exists(c_to):
        shutil.copytree(c_from, c_to)
      c_from = r"%s/%s/DS_COPY.sqlite" %(OV.GetParam('hptools.batch.drive_letter'), 'DS_COPY')
      c_to = r"%s/%s" %(OV.DataDir(), 'DS_COPY.sqlite')
      if not os.path.exists(c_to):
        shutil.copyfile(c_from, c_to)
      action = "ac2"
      return self.get_list_from_text()
    if action == "scan":
      p = r"%s%s" %(OV.GetParam('hptools.batch.drive_letter'), OV.GetParam('hptools.batch.directory'))
    else:
      p = r"%s%s" %(OV.GetParam('hptools.batch.drive_letter'), OV.GetParam('hptools.batch.directory'))
    if not os.path.exists(p):
      print "The directory %s does not exist" %p
      return
    p1 = os.listdir(p)
    for item in p1:
      folders.append(OV.standardizePath("%s/%s" %(p, item)))
      try:
        p2 = os.listdir("%s/%s" %(p, item))
        for tem in p2:
          folders.append(OV.standardizePath("%s/%s/%s" %(p, item, tem)))
      except:
        continue
  
    masks = []
    if "*" in self.mask:
      masks.append(self.mask)
    else:
      if "hkl" in self.mask:
        masks.append("*.hkl")
      if "ins" in self.mask:
        masks.append("*.ins")
      if "res" in self.mask:
        masks.append("*.res")
      if "lst" in self.mask:
        masks.append("*.lst")
  
    for folder in folders:
      #print repr(folder)
      for mask in masks:
        g = glob.glob("%s/%s" %(folder,mask))
        new_folder = folder.replace(p,self.path_to)
        for file in g:
          if filename_in_filepath:
            if file.split("\\")[1].split('.')[0].lower() not in new_folder.lower():
              continue

          file = OV.standardizePath(file)
          if action == 'copy':
            if not os.path.exists(new_folder):
              os.makedirs(new_folder)
            try:
              FS.Node("%s" %file.lower()).copy_file((file.replace(p,self.path_to)),overwrite=self.overwrite)
              file_l.append(OV.standardizePath(file))
            except:
              pass
          else:
            if not self.exclude_file(file):
              file_l.append(OV.standardizePath(file))
    return file_l

FileCrawlies_instance = FileCrawlies()
OV.registerFunction(FileCrawlies_instance.bulk_copy_files)
OV.registerFunction(FileCrawlies_instance.bulk_load_files, False, 'hp')
OV.registerFunction(FileCrawlies_instance.make_image)
OV.registerFunction(FileCrawlies_instance.delete_all_dot_olex_folders, False, 'hp')

def sort_out_drive(path):
  drive = OV.GetParam('hptools.batch.drive_letter')
  if drive:
    if "d:" in path.lower() and drive not in path:
      path = path.replace("D:",drive)
      path = path.replace("d:",drive)
    if "c:" in path.lower() and drive not in path:
      path = path.replace("C:",drive)
      path = path.replace("c:",drive)
  return path

def annotate_image_with_text(im_file_name, txt_l):
  destination_folder = OV.GetParam('hptools.images.destination_folder')
  font_size_small = OV.GetParam('hptools.images.font_size_small')
  font_size_big = OV.GetParam('hptools.images.font_size_big')
  font_size = OV.GetParam('hptools.images.font_size_big')
  font_name = OV.GetParam('hptools.images.font_name')
  font_colour = OV.GetParam('hptools.images.colour')
  width = OV.GetParam('hptools.images.width')
  addendum = OV.GetParam('hptools.images.addendum')
  line_gap = OV.GetParam('hptools.images.line_gap')
  left = OV.GetParam('hptools.images.left')
  top = OV.GetParam('hptools.images.top')
  
  im, draw = IT.get_im_and_draw_from_filename(im_file_name)
  
  dy = top
  i = 0
  for item in txt_l:
    txt = item[0]
    params = item[1]
    if i == 0: gap = 0
    else:
      gap = params.get('line_gap',line_gap)
      
    dx, dy = IT.write_text_to_draw(draw=draw,
                                   top_left=(params.get('left',left), dy + gap),
                                   txt=txt,
                                   font_size=params.get('font_size',font_size),
                                   font_colour=params.get('font_colour',font_colour),
                                   translate=False,
                                   )
    i += 1
  return im, draw

def set_hptools_run_batch_image():
  action = OV.GetParam('hptools.batch.action')
  control = "IMG_HPTOOLS_RUN_BATCH"
  if OV.IsControl(control):
    if action == "ac2":
      OV.SetImage(control,"button-run_batch_ac2off.png")
    elif action == "oda":
      OV.SetImage(control,"button-run_batch_odaoff.png")
    elif action == "filter":
      OV.SetImage(control,"button-filter_databaseoff.png")
    elif action == "scan":
      OV.SetImage(control,"button-scan_directoryoff.png")
OV.registerFunction(set_hptools_run_batch_image)
  

def get_hptools_database_items():
  import glob
  items_l = []
  g = glob.glob("%s/*.sqlite" %(OV.DataDir()))
  for item in g:
    f = item.split("\\")[-1:][0]
    f = f.split('.sqlite')[0]
    f = f.split('.')[0]
    if f != "DatabaseRunFull":
      items_l.append(f)
  txt = "--;"
  for item in items_l:
    txt += "%s;" %item
  return txt
OV.registerFunction(get_hptools_database_items)

def get_hptools_table_items():
  items_l = [
    '--',
    'Structure',
    'Reflections',
    'ac2',
    'oda',
  ]
  txt = ""
  for item in items_l:
    txt += "%s;" %item
  return txt
OV.registerFunction(get_hptools_table_items)

def get_hptools_filter_items(n):
  table = OV.GetParam('hptools.batch.filter_%s.table' %n)
  if not table or table == "--":
    items_l = ["--"]
    
  elif table == "Structure":
    items_l = [
      '--',
      'volume',
      'formula',
      'path',
      'atom_count',
      'z_prime',
      'max_Z',
    ]

  elif table == "Reflections":
    items_l = [
      '--',
      'r_int',
      'completeness',
    ]

  elif table == "ac2":
    items_l = [
      '--',
      'r1_original',
      'r1_ac2',
      'ata_original',
      'ata_ac2',
      'time_ac2',
      'solution_ac2',
      'achieved_ac2',
    ]

  elif table == "oda":
    items_l = [
      '--',
      'r1_original',
      'r1_oda',
      'ata_original',
      'ata_oda',
      'time_oda',
      'solution_oda'
      'achieved_oda',
    ]

  txt = ""

  for item in items_l:
    txt += "%s;" %item
  OV.SetParam('hptools.batch.filter_%s.var_list' %n, txt)
  olex.m('SetItems(AC2_SET_HPTOOLS_BATCH_FILTER_%s_VAR,%s)' %(n, txt))
OV.registerFunction(get_hptools_filter_items)

def get_hptools_filter_values(n):
  var = OV.GetParam('hptools.batch.filter_%s.var' %n)
  items_l = ["--"]
  if var == "z_prime":
    items_l = [
      '--',
      '0.5',
      '1',
      '1.5',
      '2',
    ]

  elif var == "max_Z":
    items_l = [
      '--',
      '6',
      '7',
      '11',
      '20',
      '30',
      '50',
    ]


  elif var == "atom_count":
    items_l = [
      '--',
      '20',
      '30',
      '40',
      '50',
      '60',
      '70',
      '80',
    ]

  elif var == "volume":
    items_l = [
      '--',
      '200',
      '400',
      '600',
      '800',
      '1000',
    ]

  elif var == "r_int" or "r1" in var:
    items_l = [
      '--',
      '0.02',
      '0.04',
      '0.06',
      '0.08',
      '0.10',
      '0.15',
      '0.20',
      '0.25',
    ]

  elif 'achieved' in var:
    items_l = [
      '--',
      'Yes',
      'No',
      'Maybe',
    ]
  

  txt = ""
  for item in items_l:
    txt += "%s;" %item
  OV.SetParam('hptools.batch.filter_%s.val_list' %n, txt)
  olex.m('SetItems(AC2_SET_HPTOOLS_BATCH_FILTER_%s_VAL,%s)' %(n, txt))




if __name__ == '__main__':
  db_test()
