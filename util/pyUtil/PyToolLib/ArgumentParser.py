try:
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  import variableFunctions as VF
except:
  import olex
  from olexFunctions import OlexFunctions
  OV = OlexFunctions()
  import variableFunctions as VF


class ArgumentParser(object):

  def __init__(self, args=None, tool_arg=None):
    self.basedir = OV.BaseDir()
    self.filefull = OV.FileFull()
    self.filepath = OV.FilePath()
    self.filename = OV.FileName()
    self.datadir = OV.DataDir()

  def getVariables(self,whichVariables):
    dictionary = VF.getVVD(whichVariables)
    for item in dictionary.items():
      varName = item[0]
      value = item[1]
      if type(value) != unicode:
        pass
      setattr(self,varName,value)
    return
  
  def setVariables(self,whichVariables):
    width = OV.FindValue('gui_htmlpanelwidth')
    dictionary = VF.getVVD(whichVariables)
    for item in dictionary.keys():
      varName = item
      value = getattr(self,varName)
      OV.SetVar(varName,value)
    OV.SetVar('gui_htmlpanelwidth', width)
    return
  