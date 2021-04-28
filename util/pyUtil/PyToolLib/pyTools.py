import sys
import olx
#import olex_core
from olexFunctions import OV
from ArgumentParser import ArgumentParser

class pyTools(ArgumentParser):
  def __init__(self, tool, function, param):
    super(pyTools, self).__init__(args=None, tool_arg=None)
    self.tool = tool
    self.function = function
    self.param = param
    self.debug = False
    #self.debug = True
    self.dispatching = {}
    self.timing = False

  def run(self):
    timing = self.timing
    debug = self.debug
    dispatching = self.dispatching
    tool = self.tool
    self.get_tool()
    tool = dispatching[tool](self.function, self.param)
    if debug:
      print("")
      print("")
      print("***********************************************")
      print("tool = %s" %self.tool)
      print("function = %s" %self.function)
      print("parameters = %s" %self.param)
      print(". . . . . . . . . . . . . . . . . . . . . . . .")
    try:
      if timing:
        import time
        beginT = time.time()
      tool.run()
      if timing:
        print("%s took %.3f seconds to complete" %(tool, time.time()-beginT))
    except:
      print("Tool %s has created an error" %tool, file=sys.stderr)
      sys.stderr.formatExceptionInfo()



  def get_tool(self):
    debug = self.debug
    tool = self.tool
    fun = self.function
    param = self.param
    dispatching = self.dispatching

    if tool in ["GuiSkinChanger", "sNumTitle", "timage", "MakeAllRBars", "BarGenerator"]:
      skin = self.gui_skin_name
      try:
        skin_path = "%s/util/pyUtil/PluginLib/skins/plugin-%sSkin" %(olx.BaseDir(), skin)
        if skin_path not in sys.path:
          sys.path.append("%s/util/pyUtil/PluginLib/skins/plugin-%sSkin" %(olx.BaseDir(), skin))
        PilTools = __import__("PilTools_%s" %skin)
        #print "pyTools -- Using %s skin." %"PilTools_%s: %s" %(skin, tool)
      except ImportError:
        #print "pyTools -- Using Default PilTools for Tool: %s" %tool
        import PilTools
      except Exception as err:
        raise

      if tool == "timage":
        try:
          dispatching.setdefault('timage', PilTools.timage)
        except Exception as err:
          raise
      elif tool == "sNumTitle":
        try:
          dispatching.setdefault('sNumTitle', PilTools.sNumTitle)
        except Exception as err:
          raise

      elif tool == "GuiSkinChanger":
        try:
          dispatching.setdefault('GuiSkinChanger', PilTools.GuiSkinChanger)
        except Exception as err:
          raise

      elif tool == "BarGenerator":
        try:
          dispatching.setdefault('BarGenerator', PilTools.BarGenerator)
        except Exception as err:
          raise

      elif tool == "MakeAllRBars":
        try:
          dispatching.setdefault('MakeAllRBars', PilTools.MakeAllRBars)
        except Exception as err:
          raise


    elif tool == "auto" or tool == "hadd":
    ## THESE SHOULD ALL BE COMMENTED UNLESS A DURHAM EXECUTABLE IS SUPPOSED TO BE MADE!
      from AutoStructure import auto, hadd
      dispatching.setdefault('auto', auto)
      dispatching.setdefault('hadd', hadd)

    elif tool == "dimas":
      if olx.IsPluginInstalled('MySQL')=='false':
        return
      try:
        from DimasInfo import dimas_info
        dispatching.setdefault('dimas', dimas_info)
      except:
        print("Dimas Server not available")
        sys.stderr.formatExceptionInfo()

    elif tool == "cif":
      from CifInfo import ExtractCifInfo
      dispatching.setdefault('cif', ExtractCifInfo)

    elif tool == "metacif":
      from CifInfo import MetaCif
      dispatching.setdefault('metacif', MetaCif)

    elif tool == "meta":
      from CifInfo import MetaCif
      dispatching.setdefault('meta', MetaCif)

    elif tool == "archive":
      from ArchiveStructure import archive
      dispatching.setdefault('archive', archive)

    elif tool == "history":
      from History import History
      dispatching.setdefault('history', History)

    elif tool == "superflip":
      from FileTools import superflip
      dispatching.setdefault('superflip', superflip)

    elif tool == "file":
      from FileTools import file_copy
      dispatching.setdefault('file_copy', file_copy)

    elif tool == "mm":
      if debug: print("Howdy, I am tool %s!" %tool)
      from FileTools import mm
      dispatching.setdefault('mm', mm)

    elif tool == "sg":
      from FileTools import sg
      dispatching.setdefault('sg', sg)

    elif tool == "HelpUpdate":
      from FileImporter import HelpUpdater
      dispatching.setdefault('HelpUpdate', HelpUpdater)

    elif tool == "RunPrg":
      from RunPrg import RunPrg
      dispatching.setdefault('RunPrg', RunPrg)

    elif tool == "RA":
      from AutoChem import RunPrgAuto
      print("Import finished")
      self.timing = True
      dispatching.setdefault('RA', RunPrgAuto)

    elif tool == "Analysis":
      from Analysis import Analysis
      dispatching.setdefault('Analysis', Analysis)

    elif tool == "MakeMovie":
      from MakeMovie import MakeMovie
      dispatching.setdefault('MakeMovie', MakeMovie)

    elif tool == "cctbx":
      bitmap = "working"
      OV.CreateBitmap(bitmap)
      from cctbx_olex_adapter import OlexCctbxAdapter
      dispatching.setdefault('cctbx', OlexCctbxAdapter)
      OV.DeleteBitmap(bitmap)

    elif tool == "Tutorials":
      if debug: print("Howdy, I am tool %s!" %tool)
      from Tutorials import Tutorials
      dispatching.setdefault('Tutorials', Tutorials)

    elif tool == "GuiTools":
      if debug: print("Howdy, I am tool %s!" %tool)
      from GuiTools import MakeGuiTools
      dispatching.setdefault('GuiTools', MakeGuiTools)

    elif tool == "BrukerSaint":
      from BrukerSaint import BrukerSaint
      dispatching.setdefault('BrukerSaint', BrukerSaint)

    elif tool == "sqlhelp":
      from OlexHelpToMySQL import ExportHelp
      dispatching.setdefault('sqlhelp', ExportHelp)

    #elif tool == "settings":
      #from htmlMaker import settingsPage
      #dispatching.setdefault('settings', settingsPage)


if __name__ == "__main__":
  tool = "Analysis"
  tool_function = "lst"
  tool_param = None
  #a = pyTools(tool, tool_function, tool_param)
  #a.run()
