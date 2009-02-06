import sys
sys.path.insert(0, r"C:\Documents and Settings\Horst\Desktop\olex\util\pyUtil\AsLib")

#sys.path.append(r"C:\bn\src")
#print "** Python version: %s ***" % sys.version
import string
from ArgumentParser import ArgumentParser

from auto_solution_engine import StructureModel as Model
from auto_solution_engine import SolutionStrategies as Solving
from auto_solution_engine import Strategies as Refining
from auto_solution_engine import ShelX97Factory
from auto_solution_engine import ToolsFactory
from auto_solution_engine import StrategiesToolbox
from auto_solution_engine.Util import FileSystem as FS
from auto_solution_engine import StructureModel
from auto_solution_engine import SolutionStrategies
from auto_solution_engine import Strategies
from auto_solution_engine.Util import FileSystem as fs
from auto_solution_engine import PeriodicTable
from auto_solution_engine import ShelX97Run
from auto_solution_engine.Util.Streams import DebugStream
from auto_solution_engine.Util.Streams import Unbuffered
from auto_solution_engine import ToolsFactory
import olx
ToolsFactory.ToolsFactorySingleton.singleton_name = "ShelX"

ShelX97Run._debug_ShelX97Run = False
StrategiesToolbox.DebugLevels.tool_level = StrategiesToolbox.DebugLevels.NoDebug




class auto(ArgumentParser):
  def __init__(self, args, tool_arg):
    super(auto, self).__init__(args, tool_arg)


    try:
      self.sol_args = args[4]
    except:
      self.sol_args = "def"

    try:
      self.ref_args = args[5]
    except:
      self.ref_args = "def"


    self.sNumPathList = []
    if tool_arg == "list":
      list = open(r"C:\DS\Debug\run.txt")
      for path in list:
        self.sNumPathList.append(path[:-1])

    self.start_from_solved = False
    self.args = args
    self.tool_args = tool_arg
    self.data_dir = olx.DataDir()

  def run(self):
    hfile = r"%s\History.htm" %self.data_dir
    FS.Node.remove(FS.Node(hfile))
    self.solution_settings()
    self.refinement_settings()
    self.process_and_catch()
    self.clean_temp()

  def solution_settings(self):
    settings = []
    args = self.sol_args
    for item in string.split(args, ","):
      settings.append(item)

    if settings[0] == "def":
      sol = SolutionStrategies.InitialSolution()
    elif settings[0] == "DualSpace":
      sol = SolutionStrategies.DualSpaceSearchStrategy(threshold_CC=0.75, max_tries=200)
    elif settings[0] == "Pattex":
      sol = SolutionStrategies.PattersonThenPartialExpansionStrategy(heavy_Z = 12)
    elif settings[0] == "Direct":
      sol = SolutionStrategies.DirectMethodStrategy()
    elif settings[0] == "DropInversion":
      sol = SolutionStrategies.DropDeadFred()
    elif settings[0] == "None":
      sol = None
    else:
      sol = SolutionStrategies.InitialSolution()

    self.sol = sol


  def refinement_settings(self):
    import string
    args = self.ref_args
    ref = Strategies.StrategyController()
    settings = []

    if args == "def":
      pass

    for item in string.split(args, ","):
      settings.append(item)

    if settings[0] == "Formula":
      if settings[1] == "enforce":
        ref.use_formula_elts_only = False
      elif settings[1] == "elements_only":
        ref.use_formula_elts_only = True

    self.ref = ref

  def process_one(self):
    #sys.stdout=Unbuffered(sys.stdout)

    basedir = self.basedir

    sol = self.sol
    ref = self.ref
    #sys.stdout.flush()
    print "+++++++++++++++++++++++++++++++++++++* v. 22-10-06 + "
    print "Structure: %s" %(self.filefull)
    print
    print

    useModel = 'OVModel'
    #useModel = 'OlexViewedModel'

    usefile = FS.Path(self.filefull)
    #resback = FS.Path("%s\\%s"%(filepath, "AutoStructureBackup.ins"))
    #FS.Node("%s" %(usefile)).copy_file((resback),overwrite=True)

    if useModel == 'OVModel':
      from OVModel import OVModel
      #OVModel.pathInfo= self.pathInfo
      OVModel.arguments= self.args
      model = OVModel(sol, ref)

    elif useModel == 'OlexViewedModel':
      from OlexViewedModel import OlexViewedModel
      model = OlexViewedModel(sol, ref)
      OlexViewedModel.usefile = usefile
      OlexViewedModel.autodir = self.filepath
      try:
        OlexViewedModel.basedir = "%s\\%s\\%s" %(basedir, "etc", "olex_data")
      except:
        OlexViewedModel.basedir = "%s\\%s\\%s" %(basedir, "tutorial", "olex_data")

      try:
        OlexViewedModel.olexdir = "%s\\%s" %(basedir, "etc")
      except:
        OlexViewedModel.olexdir = "%s\\%s" %(basedir, "tutorial")

      OlexViewedModel.create_history = True
      model.initialise_olex()
    else:
      return 'Please select the Model to use'

    model.retrieve(usefile)

    if sol:
      model.solve()

    if useModel == 'OlexViewedModel': OlexViewedModel.refineYesNo = 1
    model.refine()

    if useModel == 'OlexViewedModel': model.finish_olex()

    self.clean_temp()

    print "=========== %s =========== ok"  %(self.filefull)
    return model.R1*100

  def clean_temp(self):
    pass
    ##d = FS.Node(r'C:\Documents and Settings\Horst\Local Settings\Temp')
    ##for f in d.list('tF*.*'):
    ##  f.remove()

  def process_and_catch(self):
    import traceback
    try:
      if not self.sNumPathList:
        self.process_one()
      else:
        for sNumPath in self.sNumPathList:
          p = sNumPath.split("\\")
          filepath = ""
          for i in range(len(p) -1):
            filepath += p[i] + "\\"
          self.filepath = filepath[:-2]
          self.filename = p[-2]
          self.filefull = sNumPath
          self.process_one()


        self.process_all()
    except Exception, err:
      print "\n"
      print "!!!!!!!!!!! EXCEPTION: %s:%s" % (err.__doc__, err)
      print

  def process_all(self):
    for sNumPath in self.sNumPathList:
      try:
        p = sNumPath.split("\\")
        #   sNumPath = self.filefulld

        filepath = ""
        for i in range(len(p) -1):
          filepath += p[i] + "\\"
        self.filepath = filepath[:-2]
        self.filename = p[-2]
        self.filefull = sNumPath
        self.process_one()
        #sys.stdin.readline()
      except Exception, err:
        print "\n"
        print "!!!!!!!!!!! EXCEPTION: %s:%s" % (err.__doc__, err)
        continue

    sys.stdin = sys.__stdin__

    #print "Finished!"
    #sys.exit()

class hadd(ArgumentParser):

  def __init__(self, args, tool_arg):
    super(hadd, self).__init__(args, tool_arg)
    self.ref = Strategies.StrategyController()
    self.model = OlexViewedModel(refinement_strategy = self.ref)

  def run(self):
    self.model.retrieve(self.filefull, status=self.model.RefinedStatus)
    print "+   --> Debugging Adding Hydrogens >>>"
    #self.model.q_peak_intensity_cut_off = 2
    print "Bond Cutoff: %s"%self.model.q_peak_bond_cut_off
    print "Min Length: %s" %self.model.q_peak_bond_min_length
    print "Intensity cutoff: %s" %self.model.q_peak_intensity_cut_off

    #self.model.Q_peaks_filtering = True
    self.model.make_fourier_map()
    print "+   --> Adding Hydrogens >>>"
    self.model.hydrogens_on = True
    print "+   --> Refining <<<"
    self.model.q_peak_intensity_cut_off = 0.5
    self.model.Q_peaks_filtering = True
    print "Bond Cutoff: %s"%self.model.q_peak_bond_cut_off
    print "Min Length: %s" %self.model.q_peak_bond_min_length
    print "Intensity cutoff: %s" %self.model.q_peak_intensity_cut_off

    self.model.fit(force_fit=True)
    print "+++++++++++++++++++++++++++++++++++++++ %s DONE +" %"hadd"
    #print "*cmd=@reap %s.res" %self.filename
