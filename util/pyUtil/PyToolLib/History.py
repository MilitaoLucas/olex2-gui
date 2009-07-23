import string
import sys
import os
import glob
import os.path
import shutil
import FileSystem as FS
from ArgumentParser import ArgumentParser
try:
  import olx
  import olex
except:
  pass
import variableFunctions

import olexFunctions
OV = olexFunctions.OV

import zlib
import lst_reader
import ires_reader

tree = None

class History(ArgumentParser):
  def __init__(self):
    super(History, self).__init__()
    
  def _getItems(self):
    
    self.demo_mode = OV.FindValue('autochem_demo_mode',False)
    
    self.autochem = False
    self.solve = False
    self.basedir = OV.BaseDir()
    self.filefull = OV.FileFull()
    self.filepath = OV.FilePath()
    self.filename = OV.FileName()
    self.strdir = OV.StrDir()
    self.datadir = OV.DataDir()      
    #self.getVariables('history')
    #self.getVariables('user_alert')
    self.params = olx.phil_handler.get_python_object()
    self.history_filepath = r'%s/%s.history' %(self.strdir,self.filename)
    self.rename = OV.FindValue('rename')
    self.his_file = None

  def setParams(self):
    olx.phil_handler.update_from_python(self.params)

  def create_history(self, solution=False):
    self._getItems()
    
    self.solve = solution
    
    got_history = False
    info = ""
    global tree
    if not tree:
      tree = HistoryTree()
      
    filefull_lst = OV.file_ChangeExt(self.filefull, 'lst')
    if self.autochem or self.demo_mode:
      branchName = self.params.snum.history.autochem_next_solution
    else:
      branchName = None
    if self.solve:
      self.current_solution = tree.newBranch(self.filefull, filefull_lst, branchName=branchName)
    else:
      self.current_refinement = tree.newLeaf(self.filefull, filefull_lst)
    self.his_file = "%s;%s" %(tree.current_solution, tree.current_refinement)
    
    self._make_history_bars()
    self.setParams()
    return self.his_file
  
  def delete_history(self, args):
    self._getItems()
    del_solution = args.get('solution')
    if not del_solution.strip():
      return
    if self.user_alert_delete_history[0] == 'R':
      delete = self.user_alert_delete_history[-1]
    elif self.user_alert_delete_history == 'Y':
      delete = OV.Alert('Olex2', "Are you sure you want to delete\nthe solution '%s'?" %del_solution, 'YNIR', "(Don't show this warning again)")
    else:
      return
      
    if 'Y' in delete:
      if del_solution in tree.historyTree.keys():
        del tree.historyTree[del_solution]
        solutions = tree.historyTree.keys()
        solutions.sort()
        tree.current_solution = solutions[0]
        changeHistory(tree.current_solution)
      else:
        print "Could not delete history '%s' " %del_solution
      
    if 'R' in delete and 'Y' in delete:
      self.user_alert_delete_history = 'RY'
      #self.setVariables('user_alert')
      self.setParams()
      variableFunctions.save_user_parameters('alert')

    self.setParams()

  def rename_history(self, args):
    self._getItems()
    old_solution_name = args.get('old','')
    new_solution_name = args.get('new','')
    if not new_solution_name.strip():
      print "Please provide a valid name"
    elif new_solution_name == old_solution_name:
      return
    OV.SetVar('rename',False)
    self._getItems()
    if new_solution_name in tree.historyTree.keys():
      if self.user_alert_overwrite_history[0] == 'R':
        rename = self.user_alert_overwrite_history[-1]
      elif self.user_alert_overwrite_history == 'Y':
        rename = OV.Alert('Olex2', "There is already a solution named '%s'.\nDo you want to overwrite this solution?" %new_solution_name, 'YNIR', "(Don't show this warning again)")
      else:
        return
      
      if 'Y' in rename:
        solution_name = new_solution_name
      else:
        return
      
      if 'R' in rename:
        self.user_alert_overwrite_history = 'RY'
        #self.setVariables('user_alert')
        self.setParams()
        variableFunctions.save_user_parameters('alert')
        
    else:
      solution_name = new_solution_name
      
    if solution_name:
      tree.historyTree[solution_name] = tree.historyTree[old_solution_name]
      del tree.historyTree[old_solution_name]
      tree.current_solution = solution_name
      self.params.snum.history.current_solution = solution_name
    self._make_history_bars()
    #self.setVariables('history')
    return
  
  def revert_history(self, args):
    self._getItems()
    self._revert_history(args)
    #self.setVariables('history')
    self.setParams()
    
  def _revert_history(self, args):
    solution = args.get('solution','')
    refinement = args.get('refinement','')
    if not solution or not refinement:
      return ''
    tree.current_solution = solution
    tree.current_refinement = refinement
    filepath = OV.FilePath()
    filename = self.filename
    resFile = "%s/%s.res" %(filepath, filename)
    lstFile = "%s/%s.lst" %(filepath, filename)
    
    leaf = tree.historyTree[solution].historyBranch[refinement]
    leaf.setLeafInfo()
    resFileData = decompressFile(leaf.res)
    wFile = open(resFile, 'w')
    wFile.write(resFileData)
    wFile.close()
    if leaf.lst:
      lstFileData = decompressFile(leaf.lst)
      wFile = open(lstFile, 'w')
      wFile.write(lstFileData)
      wFile.close()
    else:
      ## remove lst file if no lst file was saved in history
      if os.path.exists(lstFile):
        os.remove(lstFile)
    destination = "%s/%s.res" %(filepath, filename)
    destination = "'%s'" %destination.strip('"').strip("'")
    olx.Atreap("%s" %destination)
    olx.File() ## needed to make new .ins file
    
  def saveHistory(self):
    self._getItems()
    variableFunctions.Pickle(tree,self.history_filepath)
    #self.setVariables('history')
    self.setParams()
    
  def loadHistory(self):
    self._getItems()
    global tree
    if os.path.exists(self.history_filepath):
      tree = variableFunctions.unPickle(self.history_filepath)
      try:
        historyName = tree.name
      except:
        historyName = OV.FileName()
        tree.name = historyName
        
      if not tree.historyTree:
        self._createNewHistory()
      elif tree.name != OV.FileName():
        self._createNewHistory()
    else:
      self._createNewHistory()
      
    if tree.current_solution:
      self._make_history_bars()
    #self.setVariables('history')
    self.setParams()
      
  def resetHistory(self):
    self._getItems()
    backupFolder = '%s/originals' %OV.StrDir()
    resetFile = '%s.ins' %OV.FileName()
    if os.path.exists(backupFolder):
      for ext in ('res','ins','lst'):
        path = '%s/%s.%s' %(OV.FilePath(),OV.FileName(),ext)
        if os.path.exists(path):
          os.remove(path)
          
      for fileName in os.listdir(backupFolder):
        if fileName == '%s.res' %OV.FileName():
          resetFile = '%s.res' %(OV.FileName())
        backupFilePath = '%s/%s' %(backupFolder, fileName)
        if os.path.exists(backupFilePath):
          restorePath = '%s/%s' %(OV.FilePath(), fileName)
          shutil.copyfile(backupFilePath,restorePath)
          
    self.filefull = '%s/%s' %(OV.FilePath(), resetFile)
    olx.Atreap(self.filefull)
    self.params.snum.history.current_solution = 'Solution 01'
    self.params.snum.history.next_solution = 'Solution 01'
    self._createNewHistory()
    self.setParams()
    
  def _createNewHistory(self):
    self.filename = olx.FileName()
    historyPicklePath = '/'.join([self.strdir,'%s.history' %self.filename])
    historyFolder = '/'.join([self.strdir,"%s-history" %self.filename])
    global tree
    if os.path.exists(historyFolder):
      tree = self._convertHistory(historyFolder)
    else:
      tree = HistoryTree()
      if self.filefull[-4:] in ('.res', '.RES', '.ins', '.INS'):
        self.current_solution = tree.newBranch(self.filefull, OV.file_ChangeExt(self.filefull,'lst'),solution=False)
      else:
        pass
      
  def _convertHistory(self, historyFolder):
    folders = []
    items = os.listdir(historyFolder)
    for item in items:
      itemPath = '/'.join([historyFolder,item])
      if os.path.isdir(itemPath):
        folders.append(OV.standardizePath(itemPath))
        
    global tree
    tree = HistoryTree()
    for folder in folders:
      g = glob.glob(r'%s/*.res' %folder)
      g.sort()
      g = OV.standardizeListOfPaths(g)
      solution = r'%s/Solution.res' %folder
      if solution in g:
        g.remove(solution)
        self.current_solution = tree.newBranch(solution,OV.file_ChangeExt(solution,'lst'))
      else:
        self.current_solution = tree.newBranch(g[0],OV.file_ChangeExt(g[0],'lst'))
        g.remove(g[0])
      refinements = []
      for item in g:
        name = item.split('/')[-1]
        strNum = name.split('.')[0]
        try:
          number = int(strNum)
        except:
          try:
            strNum = strNum.split('_')[1]
            number = int(strNum)
          except:
            number = 0
        refinements.append((number,item))
      refinements.sort()
      sol_name = tree.current_solution
      for refinement in refinements:
        tree.historyTree[sol_name].newLeaf(refinement[1],OV.file_ChangeExt(refinement[1],'lst'))
    return tree
  
  def _make_history_bars(self):
    bars = []
    try:
      keys = tree.historyTree[tree.current_solution].historyBranch.keys()
    except KeyError:
      solution_keys = tree.historyTree.keys()
      solution_keys.sort()
      tree.current_solution = solution_keys[-1]
      keys = tree.historyTree[tree.current_solution].historyBranch.keys()
      self.params.snum.history.current_solution = tree.current_solution
    keys.sort()
    R1 = 1
    if 'solution' in keys:
      bars.append(('n/a',"'spy.revert_history -solution=\"GetValue(SET_HISTORY_CURRENT_SOLUTION)\" -refinement=solution>>UpdateHtml'",'Solution'))
      
    for item in keys:
      if 'refinement_' in item:
        leaf = tree.historyTree[tree.current_solution].historyBranch[item]
        R1 = leaf.R1
        href = "'spy.revert_history -solution=\"GetValue(SET_HISTORY_CURRENT_SOLUTION)\" -refinement=\"%s\">>UpdateHtml'" %(item)
        if R1 == 'n/a':
          R1 = 0.99
        target = "'R1: %0.2f%%25, Refinement: %s - %s'" %(R1*100,leaf.refinement_program,leaf.refinement_method)
        bars.append((R1,href,target))
        
    historyTextList = []
    scale = r"vscale.png"
    historyTextList.append(r"<zimg border=0 src=%s>" % (scale))
    
    for bar in bars:
      R = bar[0]
      href = bar[1]
      target = bar[2]
      
      Ri = R
      if Ri == 'n/a':
        image = 'vbar-sol.png'
      else:
        #if Ri > 0.22:
          #Ri = 0.22
        Ri = min(Ri, 0.22)
        image = 'vbar-%i.png' %int(Ri*1000)
        
      historyTextList.append(r"<a href=%s target=%s><zimg border=0 width='7' src=%s></a>" % (href,target,image))
      
    curr_history_branch = tree.historyTree[tree.current_solution]
    historyTextList.append("<br>")
    number_of_solutions = len(tree.historyTree.keys())
    if number_of_solutions > 1 and 'Autochem' not in self.params.snum.history.current_solution:
      historyTextList.append("<a href='spy.delete_history -solution=\"GetValue(SET_HISTORY_CURRENT_SOLUTION)\">>UpdateHtml' target='Delete current history'><zimg border='0' src='delete_small.png'></a>")
    if not self.demo_mode:
      historyTextList.append(' <b>%s</b> -  %s - %s' %(curr_history_branch.spaceGroup,curr_history_branch.solution_program,curr_history_branch.solution_method))
    
    historyText = '\n'.join(historyTextList)
#    if self.demo_mode:
#      historyText = ""
    OV.write_to_olex('history-info.htm',historyText)
  
hist = History()
OV.registerMacro(hist.delete_history, 'solution')
OV.registerMacro(hist.rename_history, 'old-Old refinement name&;new-New refinement name')
OV.registerMacro(hist.revert_history, 'solution-&;refinement-')
OV.registerFunction(hist.create_history)
OV.registerFunction(hist.saveHistory)
OV.registerFunction(hist.loadHistory)
OV.registerFunction(hist.resetHistory)

class HistoryTree:
  def __init__(self):
    self.historyTree = {}
    self.version = 1.0
    self.current_solution = None
    self.current_refinement = None
    self.name = OV.FileName()
    self.hklFiles = {}
    
  def saveOriginals(self, resPath, lstPath):
    backupFolder = '%s/originals' %OV.StrDir()
    if not os.path.exists(backupFolder):
      os.mkdir(backupFolder)
    for filePath in (resPath, lstPath):
      if filePath and os.path.exists(filePath):
        file = filePath.split('/')[-1]
        backupFileFull = '%s/%s' %(backupFolder,file)
        shutil.copyfile(filePath,backupFileFull)
        
  def newBranch(self, resPath, lstPath, branchName=None, solution=True):
    if len(self.historyTree.keys()) == 0:
      self.saveOriginals(resPath, lstPath)
      
    if not branchName:
      branchName = hist.params.snum.history.next_solution
    self.historyTree[branchName] = HistoryBranch(resPath,lstPath,solution=solution)
    self.current_solution = branchName
    hist.params.snum.history.current_solution = branchName
    
    if 'Autochem' in branchName:
      # Sort out next Autochem solution name
      next_sol_num = int(branchName.split()[-1]) + 1
      while True:
        if next_sol_num < 10:
          next_sol_name = 'Autochem 0%s' %next_sol_num
        else:
          next_sol_name = 'Autochem %s' %next_sol_num
        if self.historyTree.has_key(next_sol_name):
          next_sol_num += 1
        else:
          break
      hist.params.snum.history.autochem_next_solution = next_sol_name
    
    else:
      next_sol_num = int(branchName.split()[-1]) + 1
      while True:
        if next_sol_num < 10:
          next_sol_name = 'Solution 0%s' %next_sol_num
        else:
          next_sol_name = 'Solution %s' %next_sol_num
        if self.historyTree.has_key(next_sol_name):
          next_sol_num += 1
        else:
          break
      hist.params.snum.history.next_solution = next_sol_name
      
    hist._make_history_bars()
    #hist.setVariables('history')
    hist.setParams()
    return self.current_solution
  
  def newLeaf(self,resPath,lstPath):
    self.current_refinement = self.historyTree[self.current_solution].newLeaf(resPath,lstPath)
    return self.current_refinement
  
  
class HistoryBranch:
  def __init__(self,resPath,lstPath,solution=True):
    self.spaceGroup = OV.olex_function('sg(%n)')
    self.historyBranch = {}
    if solution:
      tree.current_refinement = 'solution'
      self.historyBranch['solution'] = HistoryLeaf(resPath,lstPath)
    else:
      self.newLeaf(resPath,lstPath)
    self.solution_program = OV.GetParam('snum.solution.program')
    self.solution_method = OV.GetParam('snum.solution.method')
    self.name = None
    
  def newLeaf(self,resPath,lstPath):
    ref_num = str(len(self.historyBranch.keys()) + 1)
    if len(ref_num) == 1:
      ref_num = "0%s" %ref_num
    ref_name = 'refinement_%s' %ref_num
    tree.current_refinement = ref_name
    self.historyBranch[ref_name] = HistoryLeaf(resPath,lstPath)
    return ref_name
  
class HistoryLeaf:
  def __init__(self,resPath,lstPath):
    self.solution_program = 'n/a'
    self.solution_method = 'n/a'
    self.refinement_program = 'n/a'
    self.refinement_method = 'n/a'
    self.program_version = 'n/a'
    self.R1 = 'n/a'
    self.wR2 = 'n/a'
    self.lst = None
    self.res = None
    
    self.res = compressFile(resPath)
    ref_program = OV.GetParam('snum.refinement.program')
    sol_program = OV.GetParam('snum.solution.program')
    if tree.current_refinement == 'solution' and 'smtbx' in sol_program:
      self.solution_program = sol_program
      self.solution_method = OV.GetParam('snum.solution.method')
    elif tree.current_refinement != 'solution' and 'smtbx' in ref_program:
      self.refinement_program = ref_program
      self.refinement_method = OV.GetParam('snum.refinement.method')
      try:
        self.R1 = float(OV.GetParam('snum.refinement.last_R1'))
      except ValueError:
        pass
        
    elif os.path.exists(lstPath):
      self.lst = compressFile(lstPath)
      self.getLeafInfo(lstPath)
    else:
      self.getLeafInfo(resPath)
      
  def getLeafInfo(self,filePath):
    if filePath[-4:] == '.lst':
      try:
        lst_file = open(filePath)
        lstValues = lst_reader.reader(lst_file).values()
        lst_file.close()
      except:
        lstValues = {'R1':'','wR2':''}
      try:
        self.R1 = float(lstValues.get('R1', 'n/a'))
        self.wR2 = float(lstValues.get('wR2', 'n/a'))
      except ValueError:
        self.R1 = 'n/a'
        self.wR2 = 'n/a'
        
      if self.R1 == 'n/a':
        self.solution_program = OV.GetParam('snum.solution.program')
        self.solution_method = OV.GetParam('snum.solution.method')
      else:
        self.refinement_program = OV.GetParam('snum.refinement.program')
        self.refinement_method = OV.GetParam('snum.refinement.method')
        
      self.program_version = lstValues.get('version',None)
      
    elif filePath[-4:] in ('.res', '.ins'):
      try:
        iresValues = ires_reader.reader(open(filePath)).values()
      except:
        iresValues = {'R1':''}
      try:
        self.R1 = float(iresValues['R1'])
      except ValueError:
        self.R1 = 'n/a'
      self.wR2 = 'n/a'
      self.refinement_method = 'n/a'
      self.refinement_program = 'n/a'
    OV.SetParam('snum.refinement.last_R1', self.R1)
      
  def setLeafInfo(self):
    OV.SetParam('snum.refinement.last_R1',self.R1)
    OV.SetParam('snum.last_wR2',self.wR2)
    if self.refinement_program != 'n/a':
      if self.refinement_method != 'n/a':
        OV.SetRefinementProgram(self.refinement_program, self.refinement_method)
      else:
        OV.SetRefinementProgram(self.refinement_program)

def compressFile(filePath):
  file = open(filePath)
  fileData = file.read()
  fileData = zlib.compress(fileData,9)
  return fileData

def decompressFile(fileData):
  return zlib.decompress(fileData)

tree = HistoryTree()

def getAllHistories():
  solutions = tree.historyTree.keys()
  solutions.sort()
  historyList = []
  for item in solutions:
    historyList.append("%s;" %item)
  return ''.join(historyList)

def changeHistory(solution):
  tree.current_solution = solution
  refinements = tree.historyTree[solution].historyBranch.keys()
  his_file_num = -1
  his_file = 'solution'
  for item in refinements:
    if 'solution' not in item:
      fileNum = item.split('_')[1]
      fileNum = int(fileNum)
      his_file_num = max(his_file_num, fileNum)
      if his_file_num == fileNum:
        his_file = item
      
  tree.current_refinement = his_file
  hist.revert_history({'solution':tree.current_solution,'refinement':tree.current_refinement})
  hist.params.snum.history.current_solution = solution
  hist._make_history_bars()
  hist.rename = False
  #hist.setVariables('history')
  hist.setParams()
  #OV.UpdateHtml() # uncomment me!
  
def historyChooserRenamer():
  if 'Autochem' in OV.GetParam('snum.history.current_solution'):
    autochem = True
  else:
    autochem = False
    #pass

  rename = OV.FindValue('rename')
  
  if not rename:
    text = """<td VALIGN='center' width="40%%" colspan=1>
    <b>%History%</b>
    </td>	
    
    <td VALIGN='center' colspan=1>
    <font size='2'> 
    <input 
      type='combo'
      width='$eval(htmlpanelwidth()/2 -15)',
      height="17" 
      bgcolor='$spy.GetParam(gui.html.input_bg_colour)'
      name='SET_HISTORY_CURRENT_SOLUTION',
      value='$spy.GetParam(snum.history.current_solution)'
      items='$spy.getAllHistories()'
      label='', 
      onchange='spy.changeHistory(GetValue(SET_HISTORY_CURRENT_SOLUTION))>>UpdateHtml'
      readonly='readonly'
    >
    </font>
    </td>
    """
    if not autochem:
      text += """
    <td VALIGN='center' colspan=1 width=55>
    <input 
      type="button"
      name="rename"
      width="50" 
      height="18" 
      value="Rename" 
      onclick="SetVar(rename,True)>>UpdateHtml"
    >
    </td>
    """
    
    else: text += """
    <td colspan=1 width="55">
    </td>
    """
    
  else:
    text = """<td VALIGN='center' width="40%%" colspan=1>
    <b>%Rename Solution%</b>
    </td>	
    
    <td VALIGN='center' colspan=1>
    <font size='2'> 
    <input 
      type='text',
      width='$eval(htmlpanelwidth()/2 -15)',
      height="17" 
      bgcolor='$spy.GetParam(gui.html.input_bg_colour)'
      name='SET_SNUM_HISTORY_CURRENT_SOLUTION',
      value='$spy.GetParam(snum.history.current_solution)'
      label='', 
      onchange="spy.rename_history -old=$spy.GetParam(snum.history.current_solution) -new=GetValue(SET_SNUM_HISTORY_CURRENT_SOLUTION)>>SetVar(rename,False)>>UpdateHtml"
    >
    </font>
    </td>
    <td VALIGN='center' colspan=1>
    <input 
      type="button" 
      name = "select-usio" 
      width="50" 
      height="18" 
      value="OK" 
      onclick="$spy.rename_history -old=$spy.GetParam(snum.history.current_solution) -new=GetValue(SET_SNUM_HISTORY_CURRENT_SOLUTION)>>SetVar(rename,False)>>UpdateHtml"
    >
    </td>
    """
  return OV.Translate(text)

OV.registerFunction(historyChooserRenamer)   
OV.registerFunction(getAllHistories)
OV.registerFunction(changeHistory)