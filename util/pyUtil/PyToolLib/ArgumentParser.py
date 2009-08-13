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
    try:
      self.basedir = OV.BaseDir()
      self.filefull = OV.FileFull()
      self.filepath = OV.FilePath()
      self.filename = OV.FileName()
      self.datadir = OV.DataDir()
    except:
      self.basedir = r"C:\Documents and Settings\Horst\Desktop\olex"
      self.filefull = r"C:\Documents and Settings\Horst\Desktop\olex\sample_data\sucrose\sucrose.lst"
      self.filepath = r"C:\Documents and Settings\Horst\Desktop\olex\sample_data\sucrose"
      self.filename = "sucrose"
      self.datadir = r"C:\Documents and Settings\Horst\Application Data\Olex2"
      
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
  