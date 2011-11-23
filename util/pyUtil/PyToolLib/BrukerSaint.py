from __future__ import division
#import FileSystem as FS
from ArgumentParser import ArgumentParser
import glob, os
import sys
import copy
import string
import time
import subprocess
try:
  import olx
  import olex
except:
  pass
import CifInfo
import OlexVFS
from ImageTools import ImageTools
from threading import Thread
from olexFunctions import OlexFunctions
OV = OlexFunctions()

metacif = CifInfo.MetaCif

class SaintThreading(Thread):
  def __init__(self,instance):
    Thread.__init__(self)
    self.instance = instance
  def run(self):
    count = 0
    text = ''
    while True:
      line = self.instance.saint_pid.stdout.readline()
      if line:
        count += 1
        line = string.replace(line,'\r','')
        sys.stdout.write(line)
      else:
        break
      
      if 'End global unit cell refinement' in line:
        break
      
class BufferFlusher(Thread):
  def __init__(self,instance):
    Thread.__init__(self)
    self.instance = instance
  def run(self):
    while True:
      self.instance.saint_pid.stdout.flush()
      if self.instance.saint_pid.poll():
        break

class BrukerSaint(ImageTools):
  def __init__(self, tool_fun='ini', tool_param=None):
    super(BrukerSaint, self).__init__()
    self.fun = tool_fun
    self.param = tool_param
    self.exit = False
    self.have_gui = False
    self.current_run_no = ""
    self.have_evaluation = False
    self.have_box_picture = False
    self.boxes_link = ""
    self.last_box_drawn = ""
    self.need_integration_options = True
    self.saint_key = {}
    self.ls_statistics = {}
    self.p4p_key = {}
    self.saint_cfg = {}
    self.mcd = {}
    self.laue_class_list = []
    self.ls_file = ""
    self.ls_file_d = {}
    self.laue_class_def = {}
    self.datadir = olx.DataDir()
    self.basedir = olx.BaseDir()
    self.filepath = olx.FilePath()
    self.filename = olx.FileName()
    self.filefull = olx.FileFull()
    self.frame_directory = olx.FilePath()
    self.frame_directory = ""
    self.outdir = r"%s/%s" %(self.frame_directory, "olex")


  def run(self):

    try:
      if self.fun == 'reset':
        self.reset_gui_content()
        if self.exit:
          return
      self.get_info_smart_ini()
      if self.exit:
        return
      self.get_p4p_selection()
      self.get_frames()
      if self.exit:
        return
      if self.fun == 'ini':
        self.make_gui_content_evaluate_frames()
      elif self.fun == 'slam':
        self.have_gui = True
        self.check_gui_for_user_input()
        self.make_gui_content_evaluate_frames()
        self.write_cmd_file()
      elif self.fun == "funz":
        self.get_integration_boxes()
        self.make_box_image()
      elif self.fun == "rename_box":
        
        self.make_box_image()
      
      elif self.fun == 'exec':
        self.have_gui = True
        self.most_recent_p4p = olx.GetValue('p4p')
        self.write_saint_ini_file()
        self.write_cmd_file()
        #outdir = r"%s\olex" %(self.filepath)

        ## Delete potentially confusing files from previous runs
        if not os.path.isdir(self.outdir):
          os.mkdir(self.outdir)
        rmlist = [r"*._ls", r"*m.hkl", r"*.raw"]  
        for rmf in rmlist:
          g = glob.glob("%s/%s%s" %(self.outdir, self.frame_base, rmf))
          for item in g:
            rmfile = item
            if os.path.isfile(rmfile):
              os.remove(rmfile)
              
        #olx.Exec("saint %s\olex.slm" %self.filepath)
        #olx.ProcessCmd("nl")
        #olx.ProcessCmd("quit nl")
        #olx.ProcessCmd("exit nl nl")
        cur_dir = os.getcwd()
        os.chdir(self.outdir)
        PIPE = subprocess.PIPE
        #PIPE = None
        creationflag=8
        
        self.saint_pid=subprocess.Popen(r"saint olex.slm",stdin=PIPE,stdout=PIPE,stderr=PIPE,creationflags=creationflag)
        #self.saint_pid=subprocess.Popen(r"saint olex.slm")
        
        
        thread = SaintThreading(self)
        flushThread = BufferFlusher(self)
        thread.start()
        flushThread.start()
        self.observe_outdir()
        #if thread.isAlive():
          #thread.join()
        while thread.isAlive():
          time.sleep(0.25)
          continue
        import win32api
        win32api.TerminateProcess(int(self.saint_pid._handle), -1)

        #self.saint_pid=os.spawnlp(os.P_NOWAIT, "saint.exe", "%s\olex.slm" %self.filepath)
        #self.insert_into_meta_cif() #Temporarily Disabled!
        
        #global terminated
        #terminated = False
        
        #olex.m('exec saint olex.slm')
        
        #thread = SaintThreading(self)
        #thread.start()
        
        #olx.WaitFor('process')
        #terminated = True
        
        
        #thread.join()
        #olx.WaitFor('process')
        
        ## If there is only one run, there won't be a m.raw file. hence rename the one called 1 to m
#        f = "%s/%s%s" %(self.outdir, self.frame_base, "m.raw")
#        g = "%s/%s%s" %(self.outdir, self.frame_base, "1.raw")
#        if not os.path.isfile(f):
#          if os.path(g):
#            os.rename(g, f)
        
        ## If there is already a model of that name, load it. Otherwise load the p4p file
        structure = "%s/%s%s" %(self.outdir, self.frame_base, "m.ins")
        if os.path.isfile(r'%s/%sm.raw' %(self.outdir, self.frame_base)):
          p4p = '%s/%sm.p4p' %(self.outdir, self.frame_base)
        else:
          p4p = '%s/%s1.p4p' %(self.outdir, self.frame_base)
        #olx.Atreap(p4p)
          
        os.chdir(cur_dir)
        if os.path.isfile(structure):
          olx.Atreap(structure)
          olx.HKLSrc("%s.hkl" %(p4p[:-4]))
        else:
          olx.Atreap(p4p)
          self.make_reset_structure_gui()
        olx.html.Update()
          
    except Exception, ex:
      print "There was a problem in BrukerSaint"
      sys.stderr.formatExceptionInfo()
      print repr(ex)
      
      
  def make_box_image(self):
    #import PngImagePlugin
    import Image
    import ImageDraw, ImageChops
    scale = 1
    size = (27, 27)
    im = Image.new('RGBA', size, '#efefef')
    draw = ImageDraw.Draw(im)
    
    boxes = []
    for box in self.ls_file_d['boxes']:
      boxes.append(box)
    if not boxes:
      return
    boxes.sort()
    boxes.reverse()
    box = boxes[0]
    if box == self.last_box_drawn:
      return
    if int(box.split("-")[0]) > 3:
      if not self.last_box_drawn:
        return

    row = 0
    for li in self.ls_file_d['boxes'][box]:
      col = 0
      for item in li:
        if int(item) == 100:
          r = 255
          b = 0 #(int(item)-95) * (20)
          g = 0
        elif int(item) > 80:
          r = 180
          b = (int(item)-80) * (5)
          g = (int(item)-80) * (10)

        elif int(item) < 10:
          r = 0
          b = int(item) * (255/100)
          g = int(item) * (15)

        else:
          r = 0 #int(item) * (255/100)
          b = int(item) * (450/100)
          g = int(item) * (400/100)
        colour = (int(1*r), int(1*g), int(1*b))
        draw.rectangle((col, row, col+1, row+1), fill=colour)
        col += 1
      row += 1
  
    im = im.resize((150, 150), Image.BICUBIC)
    draw = ImageDraw.Draw(im)
    font_name = "Arial"
    font_size = 10
    font = self.registerFontInstance(font_name, font_size)

    name = r"%s" %box
    draw.text((1, 0), "Run %s" %name, font=font, fill=(255, 128, 0))
    OlexVFS.save_image_to_olex(im, "box.png", 0)
    OlexVFS.save_image_to_olex(im, "%s.png" %name, 0)
    if name.split("-")[0] != self.last_box_drawn.split("-")[0]:
      if name.split("-")[0] != '1':
        self.boxes_link += "<br>"
      self.boxes_link += "<b>Run %s</b><br>" %name.split("-")[0]
    self.boxes_link += '<a href="setimage(boximage,%s.png)">%s</a>&nbsp;' %(name, name.split("-")[1])
    self.have_box_picture = True
    self.last_box_drawn = name
    #im.save(r"%s\box.png" %self.filepath)


  def get_integration_boxes(self):
    #if not self.ls_file:
    #  self.ls_file = r"C:\Datasets\sucrose\295\10deg\10s\olex\sucrose1._ls"
    ls_file = {}
    lsf = []
    ls_file.setdefault("boxes", {})
    run = self.ls_file.split(".")[0][-1:]
    self.ls_statistics.setdefault(run, {})
    self.ls_statistics[run].setdefault("Reflections",{"Number":0,"Rejected":0,"Predicted":0,"IOSIG":0})
    run = self.ls_file.split(".")[0][-1:]
    rFile = open(self.ls_file, 'r')
    j = 0
    for li in rFile:
      lsf.append(li)
    i = 0
    lastline = 0
    for line in lsf:
      if "\n" in line:
        line = line[:-1]
      i += 1
      if "!Averaged profile:" in line:
        if i < lastline:
          continue
        j += 1
        if len(str(j)) == 1:
          jj = "0%s" %j
        else:
          jj = j
        box_id = "%s-%s" %(run, jj)
        ls_file['boxes'].setdefault(box_id, [])
        for k in xrange(29):
          if len(lsf) <= i + k:
            return
          dataline = lsf[i + k]
          if "!Averaged profile:" in dataline:
            continue
          dataline = dataline.replace("100", " 100 ") 
          ls_file['boxes'][box_id].append((dataline).split())
          lastline = i + k
          
      elif "Number of reflections read" in line:
        self.ls_statistics[run]["Reflections"]["Number"] =  int(string.strip(line.split('=')[1]))
      elif r"# Rejected due to poor spot shape" in line:
        self.ls_statistics[run]["Reflections"]["Rejected"] =  int(string.strip(line.split(':')[1]).split()[0])
      elif r"Total HKLs predicted: " in line:
        self.ls_statistics[run]["Reflections"]["Predicted"] =  int(string.strip(line.split(':')[1]).split()[0])
      elif r"Average I/sigma:" in line:
        self.ls_statistics[run]["Reflections"]["IOSIG"] =  round(float((string.strip(line.split(':')[1]).split()[0])))
  
      self.ls_file_d = ls_file
  
  def ls(self, line):
    #print "GGG"
    if "Number of reflections read" in line:
      #self.ls_statistics[run]["Reflections"]["Number"] =  int(string.strip(line.split('=')[1]))
      print line
    elif r"# Rejected due to poor spot shape" in line:
      #self.ls_statistics[run]["Reflections"]["Rejected"] =  int(string.strip(line.split(':')[1]).split()[0])
      print line
    elif r"Total HKLs predicted: " in line:
      #self.ls_statistics[run]["Reflections"]["Predicted"] =  int(string.strip(line.split(':')[1]).split()[0])
      print line
    elif r"Average I/sigma:" in line:
      #self.ls_statistics[run]["Reflections"]["IOSIG"] =  round(float((string.strip(line.split(':')[1]).split()[0])))
      print line

  def observe_outdir_(self):
    OV.registerCallback("procout", self.ls)

  def observe_outdir(self):
    self.ls_file_d = {}
    last_file_read = False
    final_p4p_file = '%s/%sm.p4p' %(self.outdir, self.frame_base)
    if os.path.isfile(final_p4p_file):
      os.remove(final_p4p_file)
    while not os.path.isfile('%s/%sm.p4p' %(self.outdir, self.frame_base)):
      #if self.terminated:
        #return
      time.sleep(1)
      ls_file = get_most_recent_file("%s/%s*._ls" %(self.outdir, self.frame_base))
      if ls_file:
        current_run_no = "%s" %((ls_file.split("._ls")[-2:-1])[-1:])[0][-1:]
        if not last_file_read or last_file_read == ls_file:
          self.ls_file = ls_file
          last_file_read = self.ls_file
        else:
          self.ls_file = last_file_read
          last_file_read = ls_file
      else:
        continue
      self.current_run_no = current_run_no
      self.current_run = "%s%s" %(self.frame_base, self.current_run_no)
      self.need_integration_options = False
      self.get_integration_boxes()
      
      
      if self.ls_file_d:
        self.make_box_image()
      self.make_gui_content_evaluate_frames()
      #self.saint_pid.stdout.flush()
      olx.html.Update()
      OV.Refresh()
      
      #global terminated
      #if terminated == True:
        #return
      #else:
        #pass
      if not self.saint_pid.poll() is None:
        return
      
      #rFile = open(ls_file, 'r')
      
    print "Done"
    

  def write_saint_ini_file(self):
    saint_file = "%s/%s" %(self.filepath, "saint.ini")
    wFile = open(saint_file, 'w')
    
    wFile.write("[CONFIGURE]\n")
    if not self.saint_cfg:
      self.get_frames()
    for item in self.saint_cfg:
      wFile.write("%s=%s\n" %(item, self.saint_cfg[item]))
    wFile.close()
    
    
  def get_info_from_p4p(self):
    d = CifInfo.get_info_from_p4p(self.most_recent_p4p)
    self.p4p_key = d["raw"]
    self.p4p_cif = d["cif"]

#               rFile = open(self.most_recent_p4p, 'r')
#               p4p = []
#               for line in rFile:
#                       p4p.append(line)
#               p4p_key = {}
#               i = 0
#               for li in p4p:
#                       if li[:2] == "  ":
#                               continue
#                       l = li.split()
#                       field = string.strip(l[0])
#                       value = string.strip(li.split(field)[1])
#                       if field != "REF05":
#                               p4p_key.setdefault(field, value)
#   self.p4p_key = p4p_key

    self.saint_key.setdefault('selPG', "1-")                
    bravais = self.p4p_key['BRAVAIS']
    cell = self.p4p_key['CELL'].split()
    if not self.laue_class_list:
      self.make_laue_class_list()
    for item in self.laue_class_list:
      inlist = string.lower(item[1])
      b1 = string.lower(bravais.split()[0])
      b2 = string.lower(bravais.split("(")[0])
      if inlist==b1 or inlist==b2:
        i =-1
        failed = True
        for val in item[3]:
          i += 1
          if not val:
            continue
          elif float(val) == round(float(cell[i])):
            self.saint_key['pointgroup'] = item[0]
            self.saint_key['constrain_integration'] = item[4]
            self.saint_key['constrain_globalrefine'] = item[4]

            failed = False
          else:
            failed = True
            break
        if not failed:
          self.saint_key['selPG'] = item[0]
        pass
      
    spotsize = (self.p4p_key["MOSAIC"]).split()
    self.saint_key.setdefault("XSIZE", spotsize[0])
    self.saint_key.setdefault("YSIZE", spotsize[0])
    self.saint_key.setdefault("ZSIZE", spotsize[1])
    

  def insert_into_meta_cif(self):
    a = metacif(self.mcd, None)
    a.run()


  def get_frames(self):
    
    g = glob.glob("%s/%s*" %(self.frame_directory, self.frame_base))
    runs = {}
    for item in g:
      f = item.split("\\")[-1:][0]
      f = f.split(self.frame_base)[1]
      f = f.split('.')
      try:
        run = f[0]
        currFrame = f[1]
        n = int(currFrame)
        runs.setdefault(run, {'nFrames':0, 'firstFrame': currFrame, 'lastFrame':currFrame, 
                    'width':0, 'time':0, 'kV':0, 'mA':0})
        runs[run]['nFrames'] += 1
        if n > int(runs[run]['lastFrame']):
          runs[run]['lastFrame'] = currFrame
        if n <= int(runs[run]['firstFrame']):
          runs[run]['firstFrame'] = currFrame

        if currFrame == runs[run]['firstFrame']:
          rFile = open(item, 'r')
          header = ""
          for li in rFile:
            header = li
          rFile.close()
          
          header = header.split(":")
          header_d = {}
          i = 0
          value = ""
          descriptor = ""
          for item in header:
            item = string.split(string.strip(item))
            if len(item) > 2:
              value += string.join(item[:-1])
            elif len(item) > 1:
              value += item[0]
            else:
              value = string.strip(value)
            header_d.setdefault(descriptor, value)
            header_d[descriptor] = value
            if item[-1] == descriptor:
              value += " "
            else:
              descriptor = item[-1]
              value = ""
            i += 1
          runs[run]['kV'] = "%.0f" %float(header_d['SOURCEM'])
          runs[run]['mA'] = "%.0f" %float(header_d['SOURCEK'])
          runs[run]['width'] = "%.2f" %float(header_d['RANGE'])
          runs[run]['time'] = "%.2f" %float(header_d['CUMULAT'])
          runs[run]['formula'] = "%s" %(header_d['CHEM'])
          
          saint_cfg = {}
          
          ccdparam = header_d['CCDPARM'].split()
          saint_cfg.setdefault("READNOISE", ccdparam[0])
          saint_cfg.setdefault("EPERADU", ccdparam[1])
          saint_cfg.setdefault("EPERPHOTON", ccdparam[2])
          
          ccdparam = header_d['DETTYPE'].split()
          if ccdparam[0] == "CCD-PXL-L6000":
            saint_cfg.setdefault("PIXPERCM", ccdparam[1])
            saint_cfg.setdefault("CM_TO_GRID", ccdparam[2])
            saint_cfg.setdefault("BRASS_SPACING", ccdparam[4])
            saint_cfg.setdefault("D_ATTENUATION", "31.1977")
            self.mcd.setdefault("_diffrn_measurement_device_type", "'BRUKER SMART CCD 6000'")
            self.mcd.setdefault("_diffrn_detector_area_resol_mean", "8")

          if ccdparam[0] == "CCD-PXL":
            saint_cfg.setdefault("PIXPERCM", 81.920)
            saint_cfg.setdefault("CM_TO_GRID", 0.800)
            saint_cfg.setdefault("BRASS_SPACING", 0.2540)
            self.mcd.setdefault("_diffrn_measurement_device_type", "'BRUKER SMART CCD 1000'")
            self.mcd.setdefault("_diffrn_detector_area_resol_mean", "8")
          self.saint_cfg = saint_cfg

      except:
        pass
    sRuns = []
    for run in runs:
      sRuns.append([run, runs[run]])
    if not sRuns:
      print "Your smart.ini file does not match any runs in your directory"
      self.exit=True
      return
    sRuns.sort()
    self.runs = sRuns
    
  def get_info_smart_ini(self):
    filename = r"%s\smart.ini" %self.filepath
    l = (olx.FilePath().split("\\")[:-1])
    p = "\\".join(l)
    filename_up = r"%s/smart.ini" %p
    if os.path.isfile(filename):
      rFile =  open(filename, 'r')
      self.frame_directory = self.filepath
    elif os.path.isfile(filename_up):
      rFile = open(filename_up, 'r')
      self.frame_directory = p
   
    else:
      txt = []
      txt.append("<td><zimg src=warning.png></td><td><b>You need to open a p4p file that is in the same directory as your frames and the smart.ini file.</b>")
      self.make_gui_tool(txt, make_line=True)
#                       print "Please make sure there is a smart.ini file next to your selected p4p file"
      self.exit = True
      return
    smart_ini = []
    for line in rFile:
      smart_ini.append(line)
    i = 0
    for li in smart_ini:
      i += 1
      if string.strip(li) == "[SCAN/MULTI]":
        frame_base = (smart_ini[i].split('=')[1])
        break
    frame_base = frame_base.split('\n')[0]  
    if len(frame_base) > 7:
      frame_base = frame_base[:7]
    self.frame_base = frame_base


  def get_p4p_selection(self):
    g = OV.ListFiles("%s/*.p4p" %(self.frame_directory))
    files = []      
    for path in g:
      info = os.stat(path)
      files.append((info.st_mtime, path))
    files.sort()
    files.reverse()
    most_recent = files[0][1]
    self.most_recent_p4p = most_recent
    #self.most_recent_p4p = self.filefull
    l = most_recent.split('\\')
    self.most_recent_p4p_name = l[-1:][0]
    self.all_p4p_files = files


  def integration_options(self):
    
    pass

  def write_cmd_file(self):
    self.check_gui_for_user_input()
    frames = ""
    nframes = ""
    outfiles = ""
    orientation = ""
    frames += r"%s/%s%s.%s" %(self.frame_directory, self.frame_base, self.runs[0][0], self.runs[0][1]['firstFrame'])
    outfiles += r"%s/%s%s.raw" %(self.outdir, self.frame_base, self.runs[0][0])
    nframes += str(self.runs[0][1]['nFrames'])
    if self.most_recent_p4p:
      orientation += r"%s" %self.most_recent_p4p
    else:
      orientation += r"%s/%s%s.p4p" %(self.frame_directory, self.frame_base, self.runs[0][0])
      
    i = 0
    for items in self.runs:
      if i != 0:
        frames += r",%s%s.%s" %(self.frame_base, self.runs[i][0], self.runs[i][1]['firstFrame'])
        outfiles += r",%s%s.raw" %(self.frame_base, self.runs[i][0])
        nframes += r",%s" %str(self.runs[i][1]['nFrames'])
        if self.most_recent_p4p:
          orientation += r",%s" %self.most_recent_p4p_name
        else:
          orientation += r",%s%s.p4p" %(self.frame_base, self.runs[0][0])

      else:
        pass
      i += 1
    if not self.saint_key:
      self.get_info_from_p4p()
      
    self.saint_key.setdefault('title', self.frame_base)
    self.saint_key.setdefault('frames', frames)
    self.saint_key.setdefault('nframes', nframes)
    self.saint_key.setdefault('outfiles', outfiles)
    self.saint_key.setdefault('orientation', orientation)
    self.saint_key.setdefault('pointgroup', '1-')
    self.saint_key.setdefault('resolution', '0.71')
    self.saint_key.setdefault('NODECAY', '/NODECAY')
    self.saint_key.setdefault('NOCORFILT', '/NOCORFILT')
    self.saint_key.setdefault('GREFLIM', '9999')
    self.saint_key.setdefault('XSIZE', '1.2')
    self.saint_key.setdefault('YSIZE', '1.2')
    self.saint_key.setdefault('ZSIZE', '0.8')
    self.saint_key.setdefault('BLEND', '')
    self.saint_key.setdefault('NORESIZE', '')
    self.saint_key.setdefault('constrain_integration', 1)
    self.saint_key.setdefault('constrain_globalrefine',  1)

    if self.have_gui:
      self.check_gui_for_user_input()
      #try:
        #checkboxes = ['NODECAY', 'NOCORFILT', 'BLEND', 'NORESIZE']
        #for box in checkboxes:
          #s = olx.GetState(box)
          #if s == 'true':
            #self.saint_key[box] = ""
          #else:
            #self.saint_key[box] = "/%s" %box
      #except:
        #pass

    #if self.have_gui:
      #try:
        #self.saint_key['pointgroup'] = olx.GetValue("POINTGROUP")
        #self.saint_key['resolution'] = olx.GetValue("RESOLUTION")
        #self.saint_key['GREFLIM'] = olx.GetValue("GREFLIM")
        #self.saint_key['XSIZE'] = olx.GetValue("XSIZE")
        #self.saint_key['YSIZE'] = olx.GetValue("YSIZE")
        #self.saint_key['ZSIZE'] = olx.GetValue("ZSIZE")
      #except:
        #pass
    
    saint_cmd = ""
    saint_cmd += r"""
INTEGRATE /TITLE="%(title)s" &
"%(frames)s" &
"%(outfiles)s" &
/ORIENTATION="%(orientation)s" &
/SPATIAL=$P4P /TIMEOUT=0.00 /NFRAMES=%(nframes)s /EXPOSURE=0.00 &
/TTM=12.17 /ROLL=0.00 /BATCH=1 /CRYSTAL=1 &
/SNAP=100 /RESOLUTION=%(resolution)s /IOVSIGMA=-3.0 /VERBOSITY=1 &
/POINTGROUP="%(pointgroup)s" /LATTICE=0 /XSIZE=%(XSIZE)s /YSIZE=%(YSIZE)s /ZSIZE=%(ZSIZE)s &
/STRONG=10.0 /LSFIT /LSFREQ=0 /K1=%(constrain_integration)s /L1=512 /GLOBAL /K2=%(constrain_globalrefine)s /L2=0 &
/TPROF=0.050 %(BLEND)s /LTHR=-999.00 /LRES=9999.000 /ORTUPDSCALE=1.00 &
/GREFLIM="%(GREFLIM)s" /BGSIG=3.00 /ACTTHRESH=0.00 /BGCSCALE=0 /BGQSCALE=6 &
/AMNAME=$NEW %(NOCORFILT)s %(NODECAY)s %(NORESIZE)s /MACHINE_ERROR=0.005 /ESDSCALE=1.000 /2THETA=-9999.000 &
/OMEGA=-9999.000 /PHI=-9999.000 /CHI=-9999.000 /IAXIS=-9999 &
/WIDTH=-9999.000 /OVRTIME=-9999.0000 /ALPHA12 /TWINBOXRATIO=1.800 &
/VOLTARGET=1.000 /VOLANGSTROMS=1.000 /QUEUEHALF=7 /PROFXHALF=4 &
/PROFYHALF=4 /PROFZHALF=4 /LORENTZ=0.0200 /LORMODEL=0.0750 /MAXSATIND=1 &
/TWINSEPARATION=1.000 /TWINMINCOMVOL=0.0400 /GRLVERR=0.0250 
""" %self.saint_key
    self.saint_cmd = saint_cmd
    self.slam_file = r'%s/%s' %(self.outdir, 'olex.slm')
    if not os.path.isdir(self.outdir):
      os.mkdir(self.outdir)
    wFile = open(self.slam_file, 'w')
    wFile.write(saint_cmd)
    wFile.close()


  def check_gui_for_user_input(self):
    if not self.laue_class_def:
      self.make_laue_class_list()
    checkboxes_off = ['NOCORFILT', 'BLEND', 'NODECAY', ]
    for box in checkboxes_off:
      self.saint_key["%s_state" %box] = ""
    checkboxes_on = ['NORESIZE']
    for box in checkboxes_on:
      self.saint_key["%s_state" %box] = "checked"
    
    if not self.have_gui:
      return
    try:
      checkboxes = checkboxes_on + checkboxes_off
      for box in checkboxes:
        s = olx.GetState(box)
        if s == 'true':
          self.saint_key[box] = ""

        else:
          self.saint_key[box] = "/%s" %box
      self.saint_key['pointgroup'] = olx.GetValue("POINTGROUP")
      self.saint_key['constrain_integration'] = self.laue_class_def[self.saint_key['pointgroup']]['constraint']
      self.saint_key['constrain_globalrefine'] = self.laue_class_def[self.saint_key['pointgroup']]['constraint']
      self.saint_key['resolution'] = olx.GetValue("RESOLUTION")
      self.saint_key['GREFLIM'] = olx.GetValue("GREFLIM")
      self.saint_key['XSIZE'] = olx.GetValue("XSIZE")
      self.saint_key['YSIZE'] = olx.GetValue("YSIZE")
      self.saint_key['ZSIZE'] = olx.GetValue("ZSIZE")
      self.outdir = olx.GetValue("outdir")
    except:
      pass
    

  def make_laue_class_list(self):
    
    laue_class = []
    laue_class.append([r"1-", 'triclinic', 'ticlinic', (None,None,None,None,None,None,), 0])
    laue_class.append([r"2mC", 'monoclinic', 'monoclinic C-Unique', (None,None,None,90,90,None), 2])
    laue_class.append([r"2mB", 'monoclinic', 'monoclinic B-Unique',(None,None,None,90,None,90), 3])
    laue_class.append([r"2mA", 'monoclinic', 'monoclinic A-Unique',(None,None,None,None,90,90), 4])
    laue_class.append([r"mmm", 'orthorhombic', 'orthorhombic', (None,None,None,90,90,90), 5])
    laue_class.append([r"4/m", 'tetragonal', 'low-symmetry tetragonal', ('a','a','c',90,90,90), 6])
    laue_class.append([r"4/mmm",'tetragonal', 'high-symmety tetragonal', ('a','a','c',90,90,90), 6])   
    laue_class.append([r"3-H", 'trigonal', 'low-symmety trigonal - hexagonal axes', ('a','a','c',90,90,120), 7])
    laue_class.append([r"3-R", 'trigonal', 'low-symmetry trigonal - rhombohedral axes', ('a','a','a','alpha','alpha','alpha'), 7])
    laue_class.append([r"3-m1",'trigonal', 'high-symmety trigonal - hexagonal axes', ('a','a','c',90,90,120), 7])
    laue_class.append([r"3-1m",'trigonal','high-symmetry trigonal-  rhombohedral axes', ('a','a','c',90,90,120), 7])
    laue_class.append([r"3-m", 'trigonal', 'high-symmetry trigonal - rhombohedral axes', ('a','a','a','alpha','alpha','alpha'), 7])
    laue_class.append([r"6/m", 'hexagonal', 'low symmetry hexagonal', ('a','a','c',90,90,120), 7])
    laue_class.append([r"6/mmm",'hexagonal', 'high symmetry hexagonal', ('a','a','c',90,90,120), 7])
    laue_class.append([r"m3-", 'cubic', 'low symmetry cubic', ('a','a','a','alpha','alpha','alpha'), 9])
    laue_class.append([r"m3-", 'cubic', 'high symmetry cubic', ('a','a','a','alpha','alpha','alpha'), 9])
    self.laue_class_list = laue_class
    
    self.laue_class_def = {}
    for item in laue_class:
      self.laue_class_def.setdefault(item[0], {'name':item[1], 'full_name':item[2], 'condiditon':item[3], 'constraint':item[4]})

  def make_gui_saint_cmd(self):
    self.check_gui_for_user_input()
    pointgroup_itemlist = ""
    if not self.laue_class_list:
      self.make_laue_class_list()
    if not self.p4p_key:
      self.get_info_from_p4p()
    selected_pointgroup = self.saint_key['selPG']
  
    for item in self.laue_class_list:
      pointgroup_itemlist += "%s;" %item[0]
    self.saint_key.setdefault("POINTGROUP", pointgroup_itemlist)
    self.saint_key.setdefault("selPG", selected_pointgroup)
    self.saint_key.setdefault("GREFLIM", '9999')
    self.write_cmd_file()
    self.saint_key.setdefault("slam", self.saint_cmd)
    self.saint_key.setdefault("slam_file", self.slam_file)
#    if not self.saint_key["NORESIZE"]:
#      self.saint_key.setdefault("noresize_tick", 'checked')
#    else:
#      self.saint_key.setdefault("noresize_tick", '')
      
    if self.have_gui:
      self.check_gui_for_user_input()
      
      
      
#               t = r"""</table>
#<table border="0" VALIGN='center' style="border-collapse: collapse" width="100%%" cellpadding="1" cellspacing="1" bgcolor="#F3F3F3">

    
    t = r"""
<tr><td width="8" bgcolor="#E9E9E9"></td>
<td width="45%%">Pointgroup:</td><td align='center'><input type="combo" name="POINTGROUP" items="%(POINTGROUP)s" width="50"  height="17" value="%(selPG)s" onchange="echo getvalue(POINTGROUP) readonly"></td>
<td width="45%%">Resolution/A:</td><td align='center'><input type="text" name="RESOLUTION" width="35" height="17" value="0.71" onchange="echo getvalue(RESOLUTION)"></td>

</tr><tr ><td width="8" bgcolor="#E9E9E9"></td>
<td width="45%%">X Size</td><td><input type="text" name="XSIZE" width="38"  height="17" value="%(XSIZE)s"></td>
<td width="45%%">Y Size</td><td><input type="text" name="YSIZE" width="38"  height="17" value="%(YSIZE)s"></td>

</tr><tr ><td width="8" bgcolor="#E9E9E9"></td>
<td width="45%%">Z Size</td><td><input type="text" name="ZSIZE" width="38"  height="17" value="%(ZSIZE)s"></td>
<td width="45%%">Optimise</td><td><input type="checkbox" name="NORESIZE" %(NORESIZE_state)s height='12' width='12'></td>

</tr><tr><td width="8" bgcolor="#E9E9E9"></td>
<td width="45%%">Reflections:</td><td align='center'><input type="text" name="GREFLIM" items="%(GREFLIM)s" width="38"  height="17" value="%(GREFLIM)s" onchange="spy BrukerSaint slam"></td>
<td width="45%%">Blend 9 Profiles</td><td align='center'><input type="checkbox" %(BLEND_state)s name="BLEND"  height = '12' width="12"></td>

</tr><tr><td width="8" bgcolor="#E9E9E9"></td>
</td><td>Apply Decay Correction</td><td align='center'><input width = '12' height='12' bgcolor="#F3F3F3" type="checkbox" %(NODECAY_state)s name="NODECAY" onchange="echo getdata(NODECAY)"></td>
</td><td>Correlation Filter On</td><td align='center'><input width = '12' value="Correlation Filter" bgcolor="#F3F3F3" type="checkbox" %(NOCORFILT_state)s name="NOCORFILT" onchange="echo getdata(NOCORFILT)"></td>

</tr><tr><td width="8" bgcolor="#E9E9E9"></td>
<td width="45%%" colspan='4' align='center'><a href='spy BrukerSaint slam>>external_edit "%(slam_file)s"'>Edit Instructions</a></td>

<tr></table>"""%self.saint_key
    self.have_gui = True
    txt = []
    if self.need_integration_options:
      txt.append(t)
    return txt

  def make_gui_content_evaluate_frames(self):
    #morefile = r"'%s/etc/gui/more-%s.htm'" %(self.basedir, self.frame_base)
    self.outdir = r"%s/%s" %(self.frame_directory, "olex")
    morename = "more-%s.htm" %self.frame_base
    morefile = r"%s/etc/gui/%s" %(self.basedir, morename)
    txt = []
    txt.append(r'<tr><td width="8" bgcolor="#E9E9E9"><a href="html.ItemState %s 1 0" target="Expand"><zimg src="$toolbar-expand.png"></a></td>' %("'%s'" %morename))
    nFrames = ""
    txt.append('<td colspan="4">Series <b>%s</b>: (%s)</td></tr>' %(self.frame_base, string.strip(nFrames)))
    framedata_d = {}
    for run in self.runs:
      nFrames += ("%s ") %(run[1]['nFrames'])
      framedata = r"""[<b>%(width)s</b>&deg;, <b>%(time)s</b>s, <b>%(mA)s</b>mA, <b>%(kV)s</b>kV]""" %(run[1])
      if self.ls_statistics.has_key(run[0]):
        if self.ls_statistics[run[0]].has_key('Reflections'):
          framedata = r"""[%(Predicted)s/<b>%(Number)s</b>/%(Rejected)s. I/<font face="Symbol">s</font>=%(IOSIG)s]""" %(self.ls_statistics[run[0]]['Reflections'])
      framedata_d.setdefault(run[0], framedata)
    
    mtxt = []
    i = 0
    for run in self.runs:
      if run[0] == self.current_run_no:
        current=True
      else:
        current=False

      if i == 0:
        mtxt.append(r'<tr><td width="8" bgcolor="#E9E9E9"><a href="html.ItemState %s 0" target="Collapse"><zimg src="$toolbar-collapse.png"></a></td>' %("'%s'" %morename))
      else:
        mtxt.append(r'<tr><td width="8" bgcolor="#E9E9E9"></td>')
      if current:
        mtxt.append("<font color='#ff0000'>")
        mtxt.append(r'<td colspan="4"><zimg src="$toolbar-line.png"> Run <b>%s</b> (%i frames) %s</td></tr>' %(run[0], run[1]['nFrames'], framedata_d[run[0]]))
      else:
        mtxt.append(r'<td colspan="4"><zimg src="$toolbar-line.png"> Run <b>%s</b> (%i frames) %s</td></tr>' %(run[0], run[1]['nFrames'], framedata_d[run[0]]))
      if current:
        mtxt.append("</font>")

      i += 1
    t = ""
    for item in mtxt:
      t+= "%s\n" %item
    olex.writeImage(morefile, t)    

    txt.append("<!-- #include %s %s;1; -->" %(morename, morefile))
    

    items = ""
    for item in self.all_p4p_files:
      p4p_full = item[1]
      p4p_name = p4p_full.split("\\")[-1:][0]
      items += "%s<-%s;" %(p4p_name,p4p_full)
    
    t = r"""<tr><td width="8" bgcolor="#E9E9E9"></td>
<td width='20'><a href="spy BrukerSaint exec">Integrate</a></td>
<td colspan='3'><input type="combo" name="p4p" items="%s" width="180"  height="17" value="%s" onchange="echo getvalue(p4p)" readonly></td>
</td><tr>"""%(items, self.most_recent_p4p_name)
    txt.append(t)
    t = r"""<tr><td width="8" bgcolor="#E9E9E9"></td>
<td><a href='setvalue(outdir,choosedir())'>Output<zimg src="$toolbar-open.png"></a>
<td colspan='3'><input type="text" name="outdir" width="180"  height="17" value="%s" onchange="echo getvalue(outdir)"/></td>
</td><tr>"""%(self.outdir)
    txt.append(t)

    
    if self.have_box_picture:
      txt.append('<tr><td></td><td colspan="2"><zimg src="box.png" width="150" height="150"></td>')
    if self.need_integration_options:  
      t = self.make_gui_saint_cmd()[0]
      txt.append(t)
    self.make_gui_tool(txt, destination='memory')
    self.have_evaluation = True
    


  def reset_gui_content(self):
    txt = [r'<a href="spy BrukerSaint ini">Click here to evaluate frames in the current folder</a>']
    self.make_gui_tool(txt, make_line=True, destination='disk')
    self.exit = True

  def make_reset_structure_gui(self):
    try:
      sglist = olx.SGList()
      sgtop = sglist.split(";")[0]
      filename = olx.FileName()
    except:
      sglist = ""
      sgtop = ""
    t = """<tr><td><a href="reset -s=getvalue(space_gr) -c=getvalue(formula)>>solve">Solve</a></td>
<td>Sp.Gr.</td><td><input type="combo" name="space_gr" items="%s" value="%s" width="60"  height="17" value="" readonly></td>
<td>Formula</td><td><input type="text" name="formula"  width="80"  height="17" value="%s"></td></tr>
<tr><td><a href="file getvalue(filename).ins>>reset -s=getvalue(space_gr) -c=getvalue(formula)>>HKLSrc(%s.hkl)>>html.ItemState solution-settings 0 1">Reset structure</a></td>
<td>Output File</td><input type="text" name="filename" width="80" height="17" value="%s"></td></tr>
"""%(sglist, sgtop, self.runs[0][1]['formula'], filename, filename)

    OV.SetVar('snum_refinement_sg_list', sglist)
    OV.SetVar('snum_refinement_sg', sgtop)
    txt = []
    txt.append(t)
    if self.have_box_picture:
      txt.append('</table><table><tr v-align="top"><td><zimg name="boximage" src="box.png" width="150" height="150"></td>')
      txt.append("<td>%s</td></tr></table></font>" %self.boxes_link)
    self.make_gui_tool(txt, make_line=True)
    self.exit = True
    
  def make_gui_tool(self, txt, make_line=False, destination='memory'):
    filename = r"%s/etc/gui/bruker-saint.htm" %(self.basedir)
    t = ""
    t+= "%s\n" %r"<!-- #include tool-top gui\blocks\tool-top.htm;image=#image;1; -->"
    if make_line:
      t += "%s\n" %r'<td width="8" bgcolor="#E9E9E9"></td><td>'
    for item in txt:
      t+= "%s\n" %item
    if make_line:
      t += "%s\n" %r'</td>'
    t+= "%s\n" %r"<!-- #include tool-footer gui\blocks\tool-footer.htm;1; -->"
    olex.writeImage(filename, t)    
    if destination== 'disk':
      wFile = open(filename, 'w')
      wFile.write(t)
      wFile.close()
    
if __name__ == "__main__":
  a = BrukerSaint()
  a.funz()

def get_most_recent_file(filepath):
  g = glob.glob("%s" %(filepath))
  files = []      
  most_recent=""
  for path in g:
    info = os.stat(path)
    files.append((info.st_mtime, path))
    files.sort()
    files.reverse()
    most_recent = files[0][1]
  return most_recent



