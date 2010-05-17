import string
import sys
import os
import hashlib
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

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import time
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
    self.history_filepath = r'%s/%s.hist' %(self.strdir,self.filename)
    self.rename = OV.FindValue('rename')
    self.his_file = None

  def create_history(self, solution=False):
    self._getItems()
    self.solve = solution
    got_history = False
    info = ""
    global tree
    if not tree:
      tree = HistoryTree()

    if os.path.splitext(self.filefull)[-1].lower() == '.cif':
      return # don't attempt to make a history if a cif is loaded
    filefull_lst = os.path.splitext(self.filefull)[0] + '.lst'
    if self.autochem or self.demo_mode:
      label = OV.GetParam('snum.history.autochem_next_solution')
    else:
      label = None
    if self.solve:
      tree.add_top_level_node(
        OV.HKLSrc(), self.filefull, filefull_lst, is_solution=True, label=label)
    else:
      tree.add_node(OV.HKLSrc(), self.filefull, filefull_lst)
    self.his_file = tree.active_node.name
    OV.SetParam('snum.history.current_node', tree.active_node.name)
    self._make_history_bars()
    self.saveHistory()
    #return self.his_file
    return tree.active_node.name

  def rename_history(self, name, label=None):
    if label is None: return
    node = tree._full_index.get(name)
    assert node is not None
    node.label = label
    self._make_history_bars()

  def revert_history(self, node_index):
    node = tree._full_index.get(node_index)
    assert node is not None
    if node.is_root:
      return
    tree.set_active_node(node)
    tree.active_node.set_params()
    filepath = OV.FilePath()
    filename = OV.FileName()
    resFile = "%s/%s.res" %(filepath, filename)
    lstFile = "%s/%s.lst" %(filepath, filename)
    resFileData = decompressFile(node.res)
    wFile = open(resFile, 'w')
    wFile.write(resFileData)
    wFile.close()
    if node.lst is not None:
      lstFileData = decompressFile(node.lst)
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
    self._make_history_bars()

  def saveHistory(self):
    self._getItems()
    variableFunctions.Pickle(tree,self.history_filepath)

  def loadHistory(self):
    self._getItems()
    global tree
    if os.path.exists(self.history_filepath):
      # new version
      history_path = self.history_filepath
    else:
      # old version
      history_path = r'%s/%s.history' %(self.strdir,self.filename)
    if os.path.exists(history_path):
      tree = variableFunctions.unPickle(history_path)
      if tree is None:
        # Not sure why this ever happens though...
        self._createNewHistory()
      try:
        historyName = tree.name
      except AttributeError:
        historyName = OV.FileName()
        tree.name = historyName

      if tree.version < 2.0:
        tree = _convert_history(tree)

      if tree.active_node is None:
        self._createNewHistory()
      elif tree.name != OV.FileName():
        self._createNewHistory()
    else:
      self._createNewHistory()

    self._make_history_bars()

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

  def is_empty(self):
    return tree.historyTree == {}

  def _createNewHistory(self):
    self.filename = olx.FileName()
    historyPicklePath = '/'.join([self.strdir,'%s.history' %self.filename])
    historyFolder = '/'.join([self.strdir,"%s-history" %self.filename])
    global tree
    if os.path.exists(historyFolder):
      tree = self._convertHistory(historyFolder)
    else:
      tree = HistoryTree()
      if olx.xf_au_GetAtomCount() == '0':
        return
      elif os.path.splitext(self.filefull)[-1] in ('.res', '.RES', '.ins', '.INS'):
        tree.add_top_level_node(OV.HKLSrc(), OV.FileFull(), os.path.splitext(OV.FileFull())[0] + '.lst', is_solution=False)

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
        self.current_solution = tree.newBranch(solution, os.path.splitext(solution)[0] + '.lst')
      else:
        self.current_solution = tree.newBranch(g[0], os.path.splitext(g[0])[0] + '.lst')
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
        tree.historyTree[sol_name].newLeaf(refinement[1], os.path.splitext(refinement[1])[0] + '.lst')
    return tree

  def _make_history_bars(self):
    if not OV.HasGUI():
      return
    full_tree = not OV.GetParam('snum.history.condensed_tree')
    OV.write_to_olex(
      'history_tree.ind', ''.join(make_html_tree(tree, [], 0, full_tree)))
    from Analysis import HistoryGraph
    HistoryGraph(tree)
    return

hist = History()
#OV.registerFunction(hist.delete_history)
OV.registerFunction(hist.rename_history)
OV.registerFunction(hist.revert_history)
OV.registerFunction(hist.create_history)
OV.registerFunction(hist.saveHistory)
OV.registerFunction(hist.loadHistory)
OV.registerFunction(hist.resetHistory)

class HistoryTree:

  is_root = True

  def __init__(self):
    self.primary_parent_node = None
    self.children = []
    self.active_child_node = None
    self.active_node = None
    self.name = OV.FileName()
    self._full_index = {self.name: self}
    self.version = 2.0
    self.hklFiles = {}
    self.next_sol_num = 1

  def add_top_level_node(self, hklPath, resPath, lstPath=None, is_solution=True, label=None):
    if len(self.children) == 0:
      saveOriginals(resPath, lstPath)

    if label is None:
      label = 'Solution %s' %self.next_sol_num
      self.next_sol_num += 1
    name = hashlib.md5(time.asctime(time.localtime())).hexdigest()
    node = Node(name, hklPath, resPath, lstPath, label=label,
                is_solution=is_solution, primary_parent_node=self)
    self.children.append(node)
    self.active_child_node = node
    self.active_node = node
    self._full_index.setdefault(name, node)
    if node.hkl is not None and node.hkl not in self.hklFiles:
      self.hklFiles.setdefault(node.hkl, compressFile(hklPath))

    #hist._make_history_bars()
    return self.active_child_node.name

  def add_node(self, hklPath, resPath, lstPath=None):
    assert self.active_child_node is not None
    ref_name = hashlib.md5(time.asctime(time.localtime())).hexdigest()
    node = Node(ref_name, hklPath, resPath, lstPath,
                primary_parent_node=self.active_node)
    self.active_node.add_child_node(node)
    self.active_node = node
    self._full_index.setdefault(ref_name, node)
    if node.hkl not in self.hklFiles:
      self.hklFiles.setdefault(node.hkl, compressFile(hklPath))

  def full_path(self):
    return full_path(self)

  def set_active_node(self, node):
    tree.active_node = node
    OV.SetParam('snum.history.current_node', node.name)
    while node.primary_parent_node is not None:
      node.primary_parent_node.active_child_node = node
      node = node.primary_parent_node

class Node:
  is_root = False

  def __init__(self,
               name,
               hklPath,
               resPath=None,
               lstPath=None,
               label=None,
               is_solution=False,
               primary_parent_node=None,
               history_leaf=None):
    self.children = []
    self.active_child_node = None
    self.name = name
    self.label = label
    self.primary_parent_node = primary_parent_node
    self.is_solution = is_solution
    self.R1 = None
    self.wR2 = None
    self.lst = None
    self.res = None
    self.hkl = None

    if hklPath and os.path.exists(hklPath):
      self.hkl = hashlib.md5('%f%s' %(os.path.getmtime(hklPath),hklPath)).hexdigest()

    if history_leaf is None:
      if resPath is not None and os.path.exists(resPath):
        self.res = compressFile(resPath)
        self.read_res(resPath)
      if lstPath is not None and os.path.exists(lstPath):
        self.read_lst(lstPath)

      if self.is_solution and OV.GetParam('snum.solution.program') == 'smtbx-solve':
        self.program = OV.GetParam('snum.solution.program')
        self.method = OV.GetParam('snum.solution.method')
      elif OV.GetParam('snum.refinement.program') == 'smtbx-refine':
        self.program = OV.GetParam('snum.refinement.program')
        self.method = OV.GetParam('snum.refinement.method')
        try:
          self.R1 = float(OV.GetParam('snum.refinement.last_R1'))
        except ValueError:
          pass
      else:
        self.program = None
        self.method = None

      OV.SetParam('snum.refinement.last_R1', self.R1)
      if self.is_solution:
        if self.program is None:
          self.program = OV.GetParam('snum.solution.program')
        if self.method is None:
          self.method = OV.GetParam('snum.solution.method')
      else:
        if self.program is None:
          self.program = OV.GetParam('snum.refinement.program')
        if self.method is None:
          self.method = OV.GetParam('snum.refinement.method')
    else:
      # XXX backwards compatibility 2010-01-15
      self.R1 = history_leaf.R1
      self.wR2 = history_leaf.wR2
      self.res = history_leaf.res
      self.lst = history_leaf.lst
      self.program_version = history_leaf.program_version
      if self.is_solution:
        self.program = history_leaf.solution_program
        self.method = history_leaf.solution_method
      else:
        self.program = history_leaf.refinement_program
        self.method = history_leaf.refinement_method

  def add_child_node(self, node):
    self.children.append(node)
    self.active_child_node = node

  def read_lst(self, filePath):
    try:
      lstValues = lst_reader.reader(filePath).values()
    except:
      lstValues = {'R1':'','wR2':''}
    if not self.is_solution:
      try:
        self.R1 = float(lstValues.get('R1', 'n/a'))
        self.wR2 = float(lstValues.get('wR2', 'n/a'))
      except ValueError:
        pass
    self.program_version = lstValues.get('version')

  def read_res(self, filePath):
    try:
      iresValues = ires_reader.reader(open(filePath)).values()
    except:
      iresValues = {'R1':''}
    try:
      self.R1 = float(iresValues['R1'])
    except ValueError:
      self.R1 = 'n/a'
    self.wR2 = 'n/a'

  def set_params(self):
    OV.SetParam('snum.refinement.last_R1',self.R1)
    OV.SetParam('snum.last_wR2',self.wR2)
    if self.is_solution:
      OV.set_solution_program(self.program, self.method)
    else:
      OV.set_refinement_program(self.program, self.method)

  def full_path(self):
    return full_path(self)

def full_path(self):
  result = [self.name]
  ppn = self.primary_parent_node
  while (ppn is not None):
    if (ppn.name == ""): break
    result.append(ppn.name)
    ppn = ppn.primary_parent_node
  result.reverse()
  return ".".join(result)

def index_node(node, full_index):
  if node.name not in full_index:
    full_index.setdefault(node.name, node)
  for child in node.children:
    index_node(child, full_index)
  return full_index

def delete_node(node):
  for child in node.children:
    delete_node(child)
  del(node)

def delete_history(node_name):
  node = tree._full_index.get(node_name)
  assert node is not None
  parent = node.primary_parent_node
  parent.children.remove(node)
  if len(parent.children) == 0:
    active_node = None
  else:
    active_node = parent.children[0]
    while active_node.active_child_node is not None:
      active_node = active_node.active_child_node
  delete_node(node)
  tree.set_active_node(active_node)
  tree._full_index = index_node(tree, {})
  hist.revert_history(active_node.name)
  hist._make_history_bars()


def saveOriginals(resPath, lstPath):
  backupFolder = '%s/originals' %OV.StrDir()
  if not os.path.exists(backupFolder):
    os.mkdir(backupFolder)
  for filePath in (resPath, lstPath):
    if filePath and os.path.exists(filePath):
      filename = os.path.basename(filePath)
      backupFileFull = '%s/%s' %(backupFolder,filename)
      shutil.copyfile(filePath,backupFileFull)

def compressFile(filePath):
  file = open(filePath)
  fileData = file.read()
  fileData = zlib.compress(fileData,9)
  return fileData

def decompressFile(fileData):
  return zlib.decompress(fileData)

#tree = HistoryTree()

def getAllHistories():
  solutions = ['%s<-%s' %(child.label, child.name) for child in tree.children]
  solutions.sort()
  historyList = []
  for item in solutions:
    historyList.append("%s;" %item)
  return ''.join(historyList)

def changeHistory(solution):
  node = tree._full_index.get(solution)
  assert node is not None
  tree.active_child_node = node
  while node.active_child_node is not None:
    node = node.active_child_node
  tree.set_active_node(node)
  hist.revert_history(node.name)
  OV.SetParam('snum.history.current_solution', solution)
  hist._make_history_bars()
  hist.rename = False

def make_history_bars():
  hist._make_history_bars()
OV.registerFunction(make_history_bars)

def popout_history_tree(width=800, height=500):
  width = int(width)
  height = int(height)
  font_colour = OV.GetParam('gui.html.font_colour')
  font_size = OV.GetParam('gui.html.font_size')
  html = """
<html>
  <body>
  <font color=%s size=%s face="Arial">
<!-- #include history-tree gui\snippets\snippet-history-tree.htm;width=%i;height=%i;prefix=POPUP;popup=history-tree.;1; -->
  </body>
  </font>
</html>
""" %(font_colour, font_size, width, height)
  htm_location = "popout-history-tree.htm"
  pop_name = 'history-tree'
  pop_str = "popup %s %s -b=stci -t='History Tree' -w=%s -h=%s -x=1 -y=50" %(
    #pop_name, htm_location, int(width), int(height))
    pop_name, htm_location, int(width*1.033), int(height*1.1))
  OV.write_to_olex(htm_location, html)
  olex.m(pop_str)
  olx.html_SetBorders(pop_name,0)
  olex.m(pop_str)
  #olx.html_Reload(pop_name)
OV.registerFunction(popout_history_tree)


def make_html_tree(node, tree_text, indent_level, full_tree=False,
                   start_count=0, end_count=0):
  indent = indent_level * '\t'
  if node.is_root:
    label = node.name
  elif node.label is not None:
    label = node.label
  else:
    label = '%s (%s)' %(node.program, node.method)
    try:
      label += ' - %.2f%%' %(node.R1 * 100)
    except (ValueError, TypeError):
      pass
  if full_tree:
    tree_text.append(indent + label + '\n' + indent + node.name + '\n')
    indent_level += 1
  elif (node.active_child_node is not None and
        len(node.active_child_node.children) > 1 or
        len(node.children) == 0):
    if start_count != end_count:
      label = "refinements %i - %i" %(start_count, end_count)
    child = node
    while (child.active_child_node is not None and
           len(child.active_child_node.children) <=1):
      child = child.active_child_node
    tree_text.append(indent + label + '\n' + indent + child.name + '\n')
    indent_level += 1
  elif (node.is_root or
        node.primary_parent_node.is_root or
        len(node.children) > 1# or
        #len(node.primary_parent_node.children) > 1
        ):
    start_count = end_count + 1
    tree_text.append(indent + label + '\n' + indent + node.name + '\n')
    indent_level += 1
  end_count +=1
  #tree_text.append(indent + label + '\n' + indent + node.name + '\n')
  for node in node.children:
    make_html_tree(
      node, tree_text, indent_level, full_tree, start_count, end_count)
  return tree_text

OV.registerFunction(getAllHistories)
OV.registerFunction(changeHistory)
OV.registerFunction(delete_history)



#########################################################
## START OF BACKWARDS COMPATIBILITY CLASSES 2010-01-19 ##
#########################################################

class HistoryBranch:
  def __init__(self,resPath,lstPath,solution=True):
    self.spaceGroup = OV.GetParam('snum.refinement.sg')
    self.historyBranch = {}
    if solution:
      tree.current_refinement = 'solution'
      self.historyBranch['solution'] = HistoryLeaf(resPath,lstPath)
      self.solution_program = self.historyBranch['solution'].solution_program
      self.solution_method = self.historyBranch['solution'].solution_method
    else:
      self.newLeaf(resPath,lstPath)
      self.solution_program = None
      self.solution_method = None
    self.name = None

  def newLeaf(self,resPath,lstPath):
    ref_num = str(len(self.historyBranch.keys()) + 1)
    if len(ref_num) == 1:
      ref_num = "0%s" %ref_num
    ref_name = 'refinement_%s' %ref_num
    tree.current_refinement = ref_name
    self.historyBranch[ref_name] = HistoryLeaf(resPath,lstPath)


class HistoryLeaf:
  def __init__(self,resPath,lstPath):
    self.solution_program = None
    self.solution_method = None
    self.refinement_program = None
    self.refinement_method = None
    self.program_version = None
    self.R1 = 'n/a'
    self.wR2 = 'n/a'
    self.lst = None
    self.res = None

    self.res = compressFile(resPath)
    ref_program = OV.GetParam('snum.refinement.program')
    sol_program = OV.GetParam('snum.solution.program')
    if tree.current_refinement == 'solution' and sol_program == 'smtbx-solve':
      self.solution_program = sol_program
      self.solution_method = OV.GetParam('snum.solution.method')
    elif tree.current_refinement != 'solution' and ref_program == 'smtbx-refine':
      self.refinement_program = ref_program
      self.refinement_method = OV.GetParam('snum.refinement.method')
      try:
        self.R1 = float(OV.GetParam('snum.refinement.last_R1'))
      except ValueError:
        pass

    elif os.path.exists(lstPath):
      self.lst = compressFile(lstPath)
      self.getLeafInfoFromLst(lstPath)
    else:
      self.getLeafInfoFromRes(resPath)
    OV.SetParam('snum.refinement.last_R1', self.R1)
    if tree.current_refinement == 'solution':
      if self.solution_program is None:
        self.solution_program = OV.GetParam('snum.solution.program')
      if self.solution_method is None:
        self.solution_method = OV.GetParam('snum.solution.method')
    else:
      if self.refinement_program is None:
        self.refinement_program = OV.GetParam('snum.refinement.program')
      if self.refinement_method is None:
        self.refinement_method = OV.GetParam('snum.refinement.method')

  def getLeafInfoFromLst(self, filePath):
    try:
      lstValues = lst_reader.reader(filePath).values()
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

  def getLeafInfoFromRes(self, filePath):
    try:
      iresValues = ires_reader.reader(open(filePath)).values()
    except:
      iresValues = {'R1':''}
    try:
      self.R1 = float(iresValues['R1'])
    except ValueError:
      self.R1 = 'n/a'
    self.wR2 = 'n/a'
    self.refinement_method = None
    self.refinement_program = None

  def setLeafInfo(self):
    OV.SetParam('snum.refinement.last_R1',self.R1)
    OV.SetParam('snum.last_wR2',self.wR2)
    if self.refinement_program is not None:
      if self.refinement_method is not None:
        OV.set_refinement_program(self.refinement_program, self.refinement_method)
      else:
        OV.set_refinement_program(self.refinement_program)

def _convert_history(history_tree):
  _tree = HistoryTree()
  hklPath = OV.HKLSrc()
  branch_names = history_tree.historyTree.keys()
  branch_names.sort()
  for branch_name in branch_names:
    branch = history_tree.historyTree[branch_name]
    leaf_names = branch.historyBranch.keys()
    leaf_names.sort()
    try:
      leaf_names.remove('solution')
      leaf_names.insert(0, 'solution') # move solution to front
    except ValueError:
      pass
    for leaf_name in leaf_names:
      leaf = branch.historyBranch[leaf_name]
      if leaf_name == 'solution':
        name = hashlib.md5(branch_name).hexdigest()
        node = Node(name, hklPath, is_solution=True, primary_parent_node=_tree, history_leaf=leaf)
        _tree.children.append(node)
        _tree.active_child_node = node
      else:
        name = hashlib.md5(branch_name + leaf_name).hexdigest()
        if _tree.active_node is None:
          node = Node(name, hklPath, is_solution=False, primary_parent_node=_tree, history_leaf=leaf)
          _tree.children.append(node)
          _tree.active_child_node = node
        else:
          node = Node(name, hklPath, is_solution=False, primary_parent_node=_tree.active_node, history_leaf=leaf)
          _tree.active_node.add_child_node(node)
      _tree.active_node = node
      _tree._full_index.setdefault(name, node)
  return _tree

############################################
## END OF BACKWARDS COMPATIBILITY CLASSES ##
############################################
