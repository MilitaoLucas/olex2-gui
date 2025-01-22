import sys, os
import hashlib
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
from olexFunctions import OV

import time
import zlib

tree = None

timing = False #bool(OV.GetParam('gui.timing'))

class HistoryFiles(object):
  def from_list(self, files):
    self.hkl = None
    self.dyn = None
    self.res = None
    self.cif_od = None
    self.files = []
    for f in files:
      if not os.path.exists(f):
        continue
      ext = os.path.splitext(f)[1]
      if ext ==".hkl":
        self.hkl = f
      elif ext == ".cif_od":
        self.cif_od = f
      elif ext == ".cif_cap":
        self.dyn = f
      elif ext == ".res" or ext == ".ins":
        self.res = f
      else:
        raise Exception("Undefined file found in the list!")
      self.files.append(f)

  def __init__(self, hkl_name, res_name):
    data_base = os.path.splitext(hkl_name)[0]
    self.from_list([hkl_name, res_name,
                   data_base + "_dyn.cif_cap",
                   data_base + ".cif_od"])

class History(ArgumentParser):
  def __init__(self):
    super(History, self).__init__()

  def _getItems(self):
    self.solve = False
    self.basedir = OV.BaseDir()
    self.filefull = OV.FileFull()
    self.filepath = OV.FilePath()
    self.filename = OV.ModelSrc()
    if os.path.exists(self.filefull):
      self.strdir = OV.StrDir()
    else:
      self.strdir = None
    self.datadir = OV.DataDir()
    self.history_filepath = os.path.join(self.strdir,self.filename) + ".hist6"
    self.rename = OV.FindValue('rename')
    self.his_file = None
    OV.registerFunction(self.make_graph,False,'History')

  def create_history(self, solution=False, label=None):
    self._getItems()
    self.solve = solution
    global tree
    if not tree:
      tree = HistoryTree()
    # don't attempt to make a history if a cif is loaded
    if os.path.splitext(self.filefull)[-1].lower() == '.cif' or OV.IsClientMode():
      return
    files = HistoryFiles(OV.HKLSrc(), self.filefull)
    if self.solve or not tree.children:
      tree.add_top_level_node(files, is_solution=True, label=label)
    if not self.solve:
      tree.add_node(files)
    self.his_file = tree.active_node.name
    OV.SetParam('snum.history.current_node', tree.active_node.name)
    if timing:
      t = time.time()
    if timing:
      print(time.time() - t)
    self.saveHistory()
    return tree.active_node.name

  def rename_history(self, name, label=None):
    if label is None: return
    label = label.strip()
    if not label: return
    node = tree._full_index.get(name)
    assert node is not None
    node.label = label

  def describe_node(self, node_id):
    try:
      node = tree._full_index.get(node_id)
      assert node is not None
      if node.is_root:
        return node_id
      if node.is_solution:
        return "%s-%s" %(node.program, node.method)
      else:
        import olex_core
        import phil_interface
        from phil_interface import phil_handler
        name = ""
        res = decompressFile(node.res).decode("utf-8")
        st = res.index("<olex2.extras>")
        end = res.index("</olex2.extras>")
        edr = src = None
        if st >= 0 and end >=0:
          params = res[st+14:end].replace("REM", "").replace("\n", "").replace("\r", "").strip()
          src = olex_core.GetStoredParams(params).get('Generic', None)
        if src:
          edr = OV.GetHeaderParam("ED.refinement.method", "Kinematic", src=src) != "Kinematic" and\
              node.program.startswith("olex2.refine")
        phil = None
        try:
          phil = phil_handler(master_phil=phil_interface.parse(
            file_name=os.path.join(olx.BaseDir(), "params.phil")),
            parse=phil_interface.parse)
          phil.adopt_phil(phil_file=os.path.join(olx.BaseDir(), "util", "pyUtil", "NoSpherA2", "NoSpherA2.phil"))
          phil.update(phil_string=zlib.decompress(node.phil).decode("utf-8"))
          olx.phil_handler.rebuild_index()
        except:
          phil = None
          if OV.IsDebugging():
            sys.stdout.formatExceptionInfo()
        if phil:
          nsf = phil.get_validated_param("snum.NoSpherA2.use_aspherical")
          if (edr or nsf) and src: #only olex2.refine
            name = "Dyn-" + OV.GetACI().EDI.get_method_name(src=src)
          else:
            rp = phil.get_validated_param("snum.refinement.program")
            name += rp
          if phil.get_validated_param("snum.refinement.use_solvent_mask"):
            name += "-mask"
          if nsf:
            name += "-NSF"
        else:
          if node.is_solution:
            name = node.program
          else:
            sn = node.solution_node
            name = "%s-%s" %(sn.program, node.program)
        if not node.is_solution:
          name += "-R-%.2f(%.2f)" %(node.R1*100, node.wR2*100)
        return name
    except:
      if OV.IsDebugging():
        sys.stdout.formatExceptionInfo()
      return node_id


  def create_archive(self, name, node_id):
    import zipfile
    if node_id:
      node = tree._full_index.get(node_id)
      assert node is not None
      filename = OV.FileName()
      with zipfile.ZipFile(name, 'w') as zout:
        res = decompressFile(node.res).decode("utf-8").split("\n")
        OV.update_HklSrc(res, filename+".hkl")
        zout.writestr(filename+".res", "\n".join(res), zipfile.ZIP_DEFLATED)
        zout.writestr(filename+".hkl", decompressFile(tree.getHklData(node)), zipfile.ZIP_DEFLATED)
        try:
          if node.dyn is not None:
            zout.writestr(filename+"_dyn_.cif_cap", decompressFile(tree.getDynData(node)), zipfile.ZIP_DEFLATED)
        except AttributeError:
          pass
        try:
          if node.cif_od is not None:
            zout.writestr(filename+".cif_od", decompressFile(tree.getCifODData(node)), zipfile.ZIP_DEFLATED)
        except AttributeError:
          pass
        try:
          if node.phil:
            zout.writestr("olex2/"+filename+".phil", zlib.decompress(node.phil), zipfile.ZIP_DEFLATED)
        except AttributeError:
          pass
        if node.lst is not None:
          zout.writestr(filename+".lst", decompressFile(node.lst), zipfile.ZIP_DEFLATED)
    else:
      file_exts = [".cif", ".fcf", ".cif_od", "_dyn_.cif_cap", ".lst", ".log", ".tsc", ".tscb"]
      filename = OV.FileName()
      filepath = OV.FilePath()
      ffilename = os.path.join(filepath, filename)
      with zipfile.ZipFile(name, 'w') as zout:
        res_fn = ffilename + ".res"
        if os.path.exists(res_fn):
          res = [l.rstrip('\r\n') for l in open(res_fn, "r").readlines()]
          OV.update_HklSrc(res, filename+".hkl")
          zout.writestr(filename+".res", '\n'.join(res), zipfile.ZIP_DEFLATED)
        try:
          zout.writestr("olex2/"+filename+".phil", get_snum_data(), zipfile.ZIP_DEFLATED)
        except:
          pass
        metacif = os.path.join(filepath, "olex2", filename) + ".metacif"
        if os.path.exists(metacif):
          zout.write(metacif, "olex2/"+filename+".metacif", zipfile.ZIP_DEFLATED)
        hklSrc = OV.HKLSrc()
        if os.path.exists(hklSrc):
          zout.write(hklSrc, filename + ".hkl", zipfile.ZIP_DEFLATED)
        for e in file_exts:
          fn = ffilename + e
          if os.path.exists(fn):
            zout.write(fn, filename + e, zipfile.ZIP_DEFLATED)

  def revert_to_original(self):
    node = tree._full_index.get(OV.FileName())
    self.revert_history(node.children[0].name)

  def revert_history(self, node_index):
    node = tree._full_index.get(node_index)
    assert node is not None
    if node.is_root:
      return
    tree.active_node = node
    node.set_params()
    filepath = OV.FilePath()
    filename = OV.FileName()
    resFile = os.path.join(filepath, filename + ".res")

    resFileData = decompressFile(node.res)
    with open(resFile, 'wb') as wFile:
      wFile.write(resFileData)

    lstFile = os.path.join(filepath, filename + ".lst")
    if node.lst is not None:
      lstFileData = decompressFile(node.lst)
      with open(lstFile, 'wb') as wFile:
        wFile.write(lstFileData)
    else:
      ## remove lst file if no lst file was saved in history
      if os.path.exists(lstFile):
        os.remove(lstFile)
    try:
      if node.phil:
        phil = zlib.decompress(node.phil) #.decode("utf-8")
        phil_fn = os.path.join(OV.StrDir(), OV.ModelSrc()) + ".phil"
        with open(phil_fn, "wb") as out:
          out.write(phil)
    except AttributeError:
      node.phil = None
    except:
      print("Failed to revert SNUM PHIL")

    original_sg = olex.f("sg()")
    olex.m("reap '%s' -no_save=true" %resFile)
    hklSrc = OV.HKLSrc()
    if not tree.isTheSameHklDigest(node, hklSrc):
      olx.Echo("Current HKL does not match the one from history - updating!", m='warning')
      hklFileData = decompressFile(tree.getHklData(node))
      with open(hklSrc, 'wb') as wFile:
        wFile.write(hklFileData)
      try:
        if node.dyn is not None:
          dynFile = os.path.splitext(hklSrc)[0] + "_dyn_.cif_cap"
          dynFileData = decompressFile(tree.getDynData(node))
          with open(dynFile, 'wb') as wFile:
            wFile.write(dynFileData)
      except AttributeError:
        node.dyn = None

    try:
      if node.cif_od is not None:
        cif_odFile = os.path.splitext(hklSrc)[0] + ".cif_od"
        if not os.path.exists(cif_odFile) and not tree.isTheSameCifODDigest(node, cif_odFile):
          cif_odFileData = decompressFile(tree.getCifODData(node))
          with open(cif_odFile, 'wb') as wFile:
            wFile.write(cif_odFileData)
    except AttributeError:
      node.cif_od = None

    olx.File() ## needed to make new .ins file
    if OV.HasGUI() and original_sg != olex.f("sg()"):
      olex.m("spy.run_skin sNumTitle")

  def saveHistory(self):
    if tree == None: # cif is loaded or no history
      return
    if timing:
      t = time.time()
    self._getItems()
    if self.strdir:
      variableFunctions.Pickle(tree,self.history_filepath + ".tmp")
      if os.path.exists(self.history_filepath):
        os.remove(self.history_filepath)
      os.rename(self.history_filepath + ".tmp", self.history_filepath)
    if timing:
      print("saveHistory took %4fs" %(time.time() - t))

  def loadHistory(self):
    if timing:
      t = time.time()
    self._getItems()
    global tree
    if os.path.exists(self.history_filepath):
      history_path = self.history_filepath
    else: # older versions
      history_path = os.path.join(self.strdir,self.filename) + ".hist5"
      if not os.path.exists(history_path):
        history_path = os.path.join(self.strdir,self.filename) + ".hist"
    if os.path.exists(history_path):
      tree = variableFunctions.unPickle(history_path)
      if tree is None:
        # Not sure why this ever happens though...
        self._createNewHistory()
      try:
        historyName = tree.name
      except AttributeError:
        historyName = OV.ModelSrc()
        tree.name = historyName

      tree.upgrade()

      if tree.active_node is None or tree.name != OV.ModelSrc():
        self._createNewHistory()
      if tree.active_node:
        OV.SetParam('snum.history.current_node', tree.active_node.name)
    else:
      self._createNewHistory()

    if timing:
      print("loadHistory took %4fs" %(time.time() - t))

  def _createNewHistory(self):
    self.filename = OV.ModelSrc()
    global tree
    tree = HistoryTree()
    tree.add_top_level_node(HistoryFiles(OV.HKLSrc(), OV.FileFull()),
                            is_solution=True)
    tree.active_node.program = 'Unknown'
    tree.active_node.method = 'Unknown'

  def make_graph(self):
    full_tree = not OV.GetParam('snum.history.condensed_tree')
    OV.write_to_olex(
      'history_tree.ind', ''.join(make_html_tree(tree, [], 0, full_tree)))
    from Analysis import HistoryGraph
    HistoryGraph(tree)

  def _update_history_display(self):
    pass


hist = History()
#OV.registerFunction(hist.delete_history)
OV.registerFunction(hist.rename_history)
OV.registerFunction(hist.revert_history)
OV.registerFunction(hist.create_history)
OV.registerFunction(hist.saveHistory)
OV.registerFunction(hist.loadHistory)


class Node(object):
  is_root = False
  link_table = []
  _children = []
  _active_child_node = None
  _primary_parent_node = None

  def __init__(self,
               link_table=None,
               name=None,
               files: HistoryFiles=None,
               label=None,
               is_solution=False,
               primary_parent_node=None,
               history_leaf=None):
    if link_table is None:
      # XXX backwards compatibility 2010-12-12
      # this should only happen if we are unpickling an old-style object of Node
      return
    self.link_table = link_table
    self._children = []
    self._active_child_node = None
    self.name = name
    self.label = label
    self.primary_parent_node = primary_parent_node
    self.is_solution = is_solution
    self.R1 = None
    self.wR2 = None
    self.lst = None
    self.res = None
    self.hkl = None
    self.dyn = None
    self.cif_od = None

    if files:
      if files.hkl:     self.hkl = digestPath(files.hkl)
      if files.dyn:     self.dyn = digestPath(files.dyn)
      if files.cif_od:  self.cif_od = digestPath(files.cif_od)

    if history_leaf is None:
      if files.res:
        self.res = compressFile(files.res)

      if self.is_solution:
        self.program = OV.GetParam('snum.solution.program')
        self.method = OV.GetParam('snum.solution.method')
      else:
        self.program = OV.GetParam('snum.refinement.program')
        self.method = OV.GetParam('snum.refinement.method')

        try:
          self.R1 = float(OV.GetParam('snum.refinement.last_R1'))
          self.wR2 = float(OV.GetParam('snum.refinement.last_wR2'))
        except:
          pass
      try:
        self.phil = zlib.compress(get_snum_data())
      except:
        self.phil = None

  def get_node_index(self, node):
    if node not in self.link_table:
      self.link_table.append(node)
      return len(self.link_table) -1
    else:
      return self.link_table.index(node)

  @property
  def active_child_node(self):
    if self._active_child_node is None:
      return None
    return self.link_table[self._active_child_node]
  @active_child_node.setter
  def active_child_node(self, node):
    self._active_child_node = self.get_node_index(node)
    if self._active_child_node not in self._children:
      self._children.append(self._active_child_node)

  @property
  def children(self):
    return [self.link_table[i] for i in self._children]
  @children.setter
  def children(self, children):
    for i, child in enumerate(children):
      children[i] = self.get_node_index(child)
    self._children = children

  @property
  def primary_parent_node(self):
    if self._primary_parent_node is None:
      return None
    return self.link_table[self._primary_parent_node]
  @primary_parent_node.setter
  def primary_parent_node(self, node):
    self._primary_parent_node = self.get_node_index(node)

  @property
  def solution_node(self):
    nd = self
    while nd and not nd.is_solution:
      nd = nd.primary_parent_node
    return nd

  def _null(self):
    for ch in self.children:
      ch._null()
    self._children = []
    self._active_child_node = None
    self._primary_parent_node = None

  def _reindex(self, old_table, new_index):
    self.link_table = new_index
    children = self._children
    self._children = []
    for ch in children:
      self._children.append(new_index.index(old_table[ch]))
    if self._active_child_node is not None:
      self._active_child_node = new_index.index(old_table[self._active_child_node])
    if self._primary_parent_node is not None:
      pn = old_table[self._primary_parent_node]
      self._primary_parent_node = new_index.index(pn)

  def set_params(self):
    OV.SetParam('snum.refinement.last_R1',self.R1)
    OV.SetParam('snum.refinement.last_wR2',self.wR2)
    if self.is_solution:
      OV.set_solution_program(OV.getCompatibleProgramName(self.program), self.method)
    else:
      if self.program != 'Unknown':
        OV.set_refinement_program(OV.getCompatibleProgramName(self.program), self.method)

  def __setstate__(self, state):
    self.__dict__.update(state)

class HistoryTree(Node):
  is_root = True

  def __init__(self):
    self._primary_parent_node = None
    self.link_table = []
    self._children = []
    self._active_child_node = None
    self._active_node = None
    self.name = OV.ModelSrc()
    self._full_index = {self.name: self}
    # 2.1 - the HKL digest is only,
    # 2.2 - the digest of actual reflections up to the end
    # 2.3 - fixing the digests as the other would stop when sum hkl=0, not abs
    # 2.4 - fixing so that 2.2-3 actually proceed to the end
    # 2.5 - add dyn support, use cif_od register
    # 2.6 - added snum phil
    self.version = 2.6
    self.hklFiles, self.dynFiles, self.cif_odFiles = {}, {}, {}
    #maps simple digest of the file timestamp and path to full one
    self.hklFilesMap, self.dynFilesMap, self.cif_odFilesMap = {}, {}, {}
    self.label = "root"
    self.next_sol_num = 1

  def _updateData(self, node: Node, files: HistoryFiles):
    if node.hkl is not None and node.hkl not in self.hklFiles:
      full_md = self.hklFilesMap.get(node.hkl, None)
      if full_md is None:
        full_md = digestHKLFile(files.hkl)
        self.hklFiles.setdefault(full_md, compressFile(files.hkl))
        self.hklFilesMap[node.hkl] = full_md
    if node.dyn is not None and node.dyn not in self.dynFiles:
      full_md = self.dynFilesMap.get(node.dyn, None)
      if full_md is None:
        full_md = digestFile(files.dyn)
        self.dynFiles.setdefault(full_md, compressFile(files.dyn))
        self.dynFilesMap[node.dyn] = full_md
    if node.cif_od is not None and node.cif_od not in self.cif_odFiles:
      full_md = self.cif_odFilesMap.get(node.cif_od, None)
      if full_md is None:
        full_md = digestFile(files.cif_od)
        self.cif_odFiles.setdefault(full_md, compressFile(files.cif_od))
        self.cif_odFilesMap[node.cif_od] = full_md

  def add_top_level_node(
    self, files: HistoryFiles, is_solution=True, label=None):
    if len(self.children) == 0:
      saveOriginals(files)

    if label is None:
      label = 'Solution %s' %self.next_sol_num
      self.next_sol_num += 1
    name = hashlib.md5(time.asctime(time.localtime()).encode('utf-8')).hexdigest()
    node = Node(self.link_table, name, files, label=label,
                is_solution=is_solution, primary_parent_node=self)
    self.children.append(node)
    self.active_child_node = node
    self.active_node = node
    self._full_index.setdefault(name, node)
    self._updateData(node, files)
    return self.active_child_node.name

  def add_node(self, files: HistoryFiles):
    ref_name = hashlib.md5(time.asctime(time.localtime()).encode()).hexdigest()
    node = Node(self.link_table, ref_name, files,
                primary_parent_node=self.active_node)
    self.active_node.active_child_node = node
    self.active_node = node
    self._full_index.setdefault(ref_name, node)
    self._updateData(node, files)

  @property
  def active_node(self):
    if self._active_node is None: return None
    return self.link_table[self._active_node]

  @active_node.setter
  def active_node(self, node):
    self._active_node = self.get_node_index(node)
    OV.SetParam('snum.history.current_node', node.name)
    while node._primary_parent_node is not None:
      node.primary_parent_node.active_child_node = node
      node = node.primary_parent_node

  def find_solution_node_by_label(self, label):
    for ndi in self._children:
      if self.link_table[ndi].label == label:
        return self.link_table[ndi]
    return None

  def del_node(self, child):
    # store old index
    old_table = [x for x in self.link_table]
    if child._primary_parent_node is not None:
      n_idx = self.link_table.index(child)
      pn = child.primary_parent_node
      pn._children.remove(n_idx)
      if pn._active_child_node == n_idx:
         pn._active_child_node = None
    child._null()
    new_lt = [self]
    for n in self.link_table:
      if n._primary_parent_node is not None:
        new_lt.append(n)
    self.link_table = new_lt
    for n in self.link_table:
      n._reindex(old_table, new_lt)
    self._full_index = index_node(self, {})

  def isTheSameHklDigest(self, node: Node, hklPath: str):
    md5 = self.hklFilesMap.get(node.hkl, node.hkl)
    return os.path.exists(hklPath) and digestHKLFile(hklPath) == md5

  def isTheSameDynDigest(self, node: Node, dynPath: str):
    md5 = self.dynFilesMap.get(node.dyn, node.dyn)
    return os.path.exists(dynPath) and digestFile(dynPath) == md5

  def isTheSameCifODDigest(self, node: Node, cif_odPath: str):
    md5 = self.cif_odFilesMap.get(node.cif_od, node.cif_od)
    return os.path.exists(cif_odPath) and digestFile(cif_odPath) == md5

  def getHklData(self, node):
    return self.hklFiles[self.hklFilesMap.get(node.hkl, node.hkl)]

  def getDynData(self, node):
    return self.dynFiles[self.dynFilesMap.get(node.dyn, node.dyn)]

  def getCifODData(self, node):
    return self.cif_odFiles[self.cif_odFilesMap.get(node.cif_od, node.cif_od)]

  def delete_solution_node_by_label(self, label):
    node = self.find_solution_node_by_label(label)
    if not node:
      return False
    self._active_node = None
    self.del_node(node)
    if len(self._children) == 0:
      self._active_node = None
    else:
      self._active_node = self._children[0]
    self._full_index = index_node(self, {})
    return True

  def __setstate__(self, state):
    Node.__setstate__(self, state)

  def _build_cif_od_register_etc(self, node: Node, call_id=0):
    """For upgrade from 2.4->2.5 only"""
    try:
      node.dyn = None
      if call_id > 0 and node.cif_od:
        if len(node.cif_od) != 32: # already upgraded?
          md = digestData(decompressFile(node.cif_od))
          self.cif_odFiles.setdefault(md, node.cif_od)
          node.cif_od = md
    except AttributeError:
      node.cif_od = None
    call_id += 1
    for c in node.children:
      self._build_cif_od_register_etc(c, call_id=call_id)

  def upgrade(self):
    current_version = 2.6 # current version
    if self.version == current_version:
      return
    start_time = time.time()
    if self.version < 2.2:
      new_index = {}
      self.hklFilesMap = {}
      for k,v in self.hklFiles.items():
        if not isinstance(v, (bytes, bytearray)):
          v = v.encode('latin1')
        md = digestHKLData(decompressFile(v))
        new_index.setdefault(md, v)
        self.hklFilesMap[k] = md
      self.hklFiles = new_index
    elif self.version < 2.4:
      new_index = {}
      r_index = {}
      # build reverse index
      for k,v in self.hklFilesMap.items():
        r_index.setdefault(v, list()).append(k)
      for k,v in self.hklFiles.items():
        if not isinstance(v, (bytes, bytearray)):
          v = v.encode('latin1')
        md = digestHKLData(decompressFile(v))
        new_index.setdefault(md, v)
        if k in r_index: # unbound HKL file?
          for hkl_d in r_index[k]:
            self.hklFilesMap[hkl_d] = md
      self.hklFiles = new_index
    if self.version < 2.5: # create cif_od register
      self.dynFiles, self.cif_odFiles = {}, {}
      self.dynFilesMap, self.cif_odFilesMap = {}, {}
      self._build_cif_od_register_etc(self)
    self.version = current_version
    print("History has been upgraded in: %.2f ms" %((time.time() - start_time)*1000))
    print("History contains %s HKL file(s), %s cif_od files and %s nodes" %(
      len(self.hklFiles),len(self.cif_odFiles),len(self._full_index)))


def index_node(node, full_index):
  if node.name not in full_index:
    full_index.setdefault(node.name, node)
  for child in node.children:
    index_node(child, full_index)
  return full_index

def delete_history(node_name):
  node = tree._full_index.get(node_name)
  if not node:
    for nd in tree.link_table:
      if nd.label == node_name:
        node = nd
        break
  if not node:
    print("Unknown branch: %s" %(node_name))
    return
  parent = node.primary_parent_node
  tree.del_node(node)
  if len(parent._children) == 0:
    active_node = None
  else:
    active_node = parent.children[0]
    while active_node.active_child_node is not None:
      active_node = active_node.active_child_node
  tree.active_node = active_node
  tree._full_index = index_node(tree, {})
  hist.revert_history(active_node.name)

def saveOriginals(originals: HistoryFiles):
  backupFolder = os.path.join(OV.StrDir(), "originals")
  if not os.path.exists(backupFolder):
    os.mkdir(backupFolder)
  duplicates = 0
  for filePath in originals.files:
    dest_base = os.path.join(backupFolder, os.path.basename(filePath))
    dest_file = dest_base
    src_stat = os.stat(filePath)
    src_sha256 =None
    #find unique backup name
    inc = 1
    do_copy = True
    while os.path.exists(dest_file):
      dest_stat = os.stat(dest_file)
      if src_stat.st_size == dest_stat.st_size:
        if src_stat.st_mtime == dest_stat.st_mtime:
          do_copy = False
          break
        else: # fall back to digests
          import hashlib
          if src_sha256 is None:
            src_sha256 = hashlib.sha256(open(filePath, 'rb').read()).hexdigest()
          if src_sha256 == hashlib.sha256(open(dest_file, 'rb').read()).hexdigest():
            do_copy = False
            break
      dest_file = "%s_%s" %(dest_base, inc)
      inc += 1
      duplicates += 1
    if do_copy:
      shutil.copy2(filePath, dest_file)
  if duplicates > 0:
    olx.Echo("%s Previous backups found!" %(duplicates), m="warning")

def compressFile(filePath):
  return zlib.compress(open(filePath, "rb").read(), 9)

def decompressFile(fileData):
  if not isinstance(fileData, (bytes, bytearray)):
    fileData = fileData.encode('latin1')
  return zlib.decompress(fileData)

def digestHKLData(fileData):
  import io
  md = hashlib.md5()
  input = io.BytesIO(fileData)
  l = input.readline()
  while l:
    try:
      s = abs(int(l[0:4])) + abs(int(l[4:8])) + abs(int(l[8:12]))
      if s == 0:
        break
    except:
      break
    md.update(l)
    l = input.readline()
  return md.hexdigest()

def digestHKLFile(filePath):
  return digestHKLData(open(filePath, "rb").read())

def digestFile(filePath):
  md = hashlib.md5()
  md.update(open(filePath, "rb").read())
  return md.hexdigest()

def digestData(fileData):
  import io
  md = hashlib.md5()
  input = io.BytesIO(fileData)
  md.update(input.read())
  return md.hexdigest()

def digestPath(filePath):
  return hashlib.md5(b'%f%s' %(os.path.getmtime(filePath),
                               filePath.encode('utf-8'))).hexdigest()
def get_snum_data():
  try:
    from io import StringIO
    out = StringIO()
    olx.phil_handler.save_param_file(
      file_name=None, out_stream=out,
        scope_name='snum', diff_only=True)
    return out.getvalue().encode("utf-8")
  except:
    return None

def make_history_bars():
  if olx.GetVar("update_history_bars", 'true') == 'false':
    olx.UnsetVar("update_history_bars")
    return
  hist.make_graph()
OV.registerFunction(make_history_bars)

def get(where, what):
  if tree:
    if where == 'solution':
      acn = tree.active_child_node
      solution = True
    else:
      acn = tree.active_node
      solution = False
    if acn and acn.is_solution == solution:
      if what == 'program':
        if acn.program.lower().startswith('shelx'):
          return acn.program.upper()
        return acn.program
      elif what == 'method':
        return acn.method
  return 'Unknown'
OV.registerFunction(get, namespace="history")

def popout_history_tree(width=800, height=500):
  width = int(width)
  height = int(height)
  font_colour = OV.GetParam('gui.html.font_colour')
  font_size = OV.GetParam('HtmlGuiFontSize')
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
  olx.html.SetBorders(pop_name,0)
  olex.m(pop_str)
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
        len(node.children) > 1
          #or node.program != node.primary_parent_node.program

        # or
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

OV.registerFunction(delete_history, False, "history")
