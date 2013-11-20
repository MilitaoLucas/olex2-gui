#make_movie.py
from ArgumentParser import ArgumentParser
import os
import olx
from olexFunctions import OlexFunctions
OV = OlexFunctions()

class MakeMovie():
  def __init__(self):
    self.i = 0

  def run_MakeMovie(self):
    self.axis = OV.GetParam('snum.image.image_series.rotation_around_axis')
    self.frames = OV.GetParam('snum.image.image_series.number_of_frames')
    self.steps = OV.GetParam('snum.image.image_series.degrees_of_rotation')
    self.size = OV.GetParam('snum.image.image_series.size_of_frames')
    self.filepath = OV.FilePath()
    
    print "Making %i frames by rotating around axis %i in %.2f degree steps in size %.2f" %(self.frames, self.axis, self.steps, self.size)
    path = "%s/movie" %(self.filepath)
    if not os.path.exists(path):
      os.mkdir(path)
    for i in xrange(self.frames):
      olx.Rota(self.axis, self.steps)
      OV.Refresh()
      if i > 99: number = i
      elif i < 10: number = "00%i" %i
      elif i < 100: number = "0%i" %i
      olx.Pict("%s/%s.bmp" %(path, number), "%.3f" %(self.size))

  def run_complex(self):
    movie = self
    #movie = movie()
    movie.macrobegin()
    movie.motion(format='bmp', frames=300, rotation=60, type='middle', hdirect='right', zoom = 0)
    movie.macroend()


  def macrobegin(self):
    wfile = self.wfile
    wfile.write("<m2 help='Create Movie'\n  <body\n <cmd\n")

  def macroend(self):
    wfile = self.wfile
    wfile.write("      \\>\n    \\>\n  \\>")

  def write_commands(self, txt):
    wfile = self.wfile
    self.i += 1
    i = self.i
    if i < 100: number = "0%i" %i
    if i < 10: number = "00%i" %i
    if i > 99: number = i
    format = 'bmp'
    pict=  '<cmd1 cmd="Picta %s.%s 1"\\>\n' %(number, format)
    wfile.write(pict)
    txt_rota =  '    <cmd1 cmd="rota 3 0.5"\\>\n'
    wfile.write(txt_rota)
    txt_wait =  '    <cmd1 cmd="wait 50"\\>\n'
    wfile.write(txt_wait)

    for t in txt:
      wfile.write(t)

  def motion(self, format='bmp', frames=10, rotation=1, type='start', hdirect='right', speedmin=0, zoom=0):
    totalrot = 0
    rotations = []

    if type != 'middle':
      for j in range (frames):
        y = j*j
        degrees = y
        if degrees < speedmin:
          continue
        rotations.append(degrees)
        totalrot+=degrees
        print "Totalrot = %.3f" %(totalrot)
    else:
      if self.maxdegree != 0:
        counter = rotation/self.maxdegree
        degrees = self.maxdegree
      else:
        counter = frames
        degrees = float(rotation)/float(frames)

      for j in range (counter):
        rotations.append(degrees)
        totalrot+=degrees
        self.maxdegree = degrees
        print "Totalrot = %.3f" %(totalrot)

    if type == "end":
      rotations.reverse()
    if hdirect == 'left':
      hsign = "-"
    else:
      hsign = ""

    totaldegrees = 0
    txt_zoom = ""
    for item in rotations:
      try:
        degrees = (float(item)/float(totalrot)) * rotation
      except:
        degrees = 0
      if degrees > self.maxdegree: self.maxdegree = degrees
      if degrees:
        txt_rota =  '    <cmd1 cmd="rota 2 %s%.3f"\\>\n' %(hsign,degrees)
      else:
        txt_rota = ""
      if zoom:
        txt_zoom =  '    <cmd1 cmd="zoom eval((zoom()^.5 + %.4f)^2.2)"\\>\n' %(zoom)
      totaldegrees += degrees
      self.write_commands([txt_rota, txt_zoom])
      print "Totaldegrees = %.3f" %totaldegrees


  if __name__ == '__main__':
    movie = movie()
    movie.macrobegin()

    ## Flyththrough quartz
    movie.motion(format='bmp', frames=30, rotation=0.2, type='start', hdirect='right', zoom = 4)
    movie.motion(format='bmp', frames=30, rotation=0.2, type='middle', hdirect='right', zoom = 4)
    movie.motion(format='bmp', frames=30, rotation=0.2, type='end', hdirect='right', zoom = 4)
    movie.motion(format='bmp', frames=30, rotation=0.2, type='start', hdirect='left', zoom = 4)
    movie.motion(format='bmp', frames=30, rotation=0.2, type='middle', hdirect='left', zoom = 4)
    movie.motion(format='bmp', frames=30, rotation=0.2, type='end', hdirect='left', zoom = 4)

    ## Wiggle Quartz
    #movie.motion(format='bmp', frames=20, rotation=3, type='start', hdirect='right')
    #movie.motion(format='bmp', frames=0, rotation=3, type='middle', hdirect='right')
    #movie.motion(format='bmp', frames=20, rotation=3, type='end', hdirect='right', speedmin = 30)
    #movie.motion(format='bmp', frames=20, rotation=3, type='start', hdirect='right', speedmin = 30)
    #movie.motion(format='bmp', frames=0, rotation=3, type='middle', hdirect='right')
    #movie.motion(format='bmp', frames=20, rotation=3, type='end', hdirect='right')
    #movie.motion(format='bmp', frames=20, rotation=3, type='start', hdirect='left')
    #movie.motion(format='bmp', frames=0, rotation=3, type='middle', hdirect='left')
    #movie.motion(format='bmp', frames=20, rotation=3, type='end', hdirect='left', speedmin = 30)
    #movie.motion(format='bmp', frames=20, rotation=3, type='start', hdirect='left', speedmin = 30)
    #movie.motion(format='bmp', frames=0, rotation=3, type='middle', hdirect='left')
    #movie.motion(format='bmp', frames=20, rotation=3, type='end', hdirect='left')

    movie.macroend()




    #movie.motion(format='bmp', frames=10, rotation=3, type='start', hdirect='left')
    #movie.motion(format='bmp', frames=0, rotation=3, type='middle', hdirect='left')
    #movie.motion(format='bmp', frames=10, rotation=3, type='end', hdirect='left', speedmin = 10)
    #movie.motion(format='bmp', frames=10, rotation=3, type='start', hdirect='left', speedmin = 10)
    #movie.motion(format='bmp', frames=0, rotation=3, type='middle', hdirect='left')
    #movie.motion(format='bmp', frames=10, rotation=3, type='end', hdirect='left')

    
MakeMovie_instance = MakeMovie()
OV.registerFunction(MakeMovie_instance.run_MakeMovie)

    