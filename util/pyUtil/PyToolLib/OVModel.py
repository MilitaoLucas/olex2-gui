import auto_solution_engine.StructureModel as Model
import auto_solution_engine.SolutionStrategies as Solving
import auto_solution_engine.Strategies as Refining
import auto_solution_engine.Util.FileSystem as FS
import auto_solution_engine.StructureModelShelX97IO as StructureModelShelXIO
from auto_solution_engine.Formulae import MissingElements
from History import *
from Analysis import *

class OVModel(Model.StructureModel):
  def __init__(self, *args):
    try:
      import olx
      self.noOlex = False
    except:
      self.noOlex = True
    super(OVModel,self).__init__(*args)
    pathInfo = {}
    arguments = []
    self.last_R1 = 0
    self.last_wR2 = 0

  def on_sub_cycle_finished(self):
    r = self.R1
    if r != 0 and not (r - r*0.05) < self.last_R1 < (r + r*0.05):
      self.last_R1 = self.R1
      self.last_wR2 = self.wR2
      hist = History('create', r)
      hist.run()
      K = Analysis('lst', None)
      K.run()
      if olx: olx.html.Update()

    if not self.noOlex:
      filefull = olx.FileFull()
      filepath = olx.FilePath()
      filename = olx.FileName()
    else:
      filefull = (self.pathInfo['filefull'])
      filepath = (self.pathInfo['filepath'])
      filename = (self.pathInfo['filename'])


    serialiser = StructureModelShelXIO.RefinedStructureModelSerialiser(self)
    serialiser.grown = False
    serialiser.serialise()
    #filedir = FS.Path(r"%s" %(self.pathInfo['basedir']))
    #wFileName = str(self.pathInfo['filepath']) + r"\auto.res"
    serialiser.store("%s" %(filefull))
    if not self.noOlex: olx.Atreap(filefull)
