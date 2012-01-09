from olexFunctions import OlexFunctions
OV = OlexFunctions()
import os
import olx
import olex_gui
from string import Template

class XPlain:
  def __init__(self):
    self.exe_file = olx.file.Which("XPlain.exe")
    if not self.exe_file:
      self.exe_file = r"C:\Rigaku\XPlain\XPlain.exe"
    if not os.path.exists(self.exe_file):
      self.exe_file = None

  def exists(self):
    return self.exe_file != None

  def run(self):
    if not self.exe_file:
      print 'Could not locate the XPlain executable, aborting...'
      return 1
        
    loaded_file = OV.FileFull()
    exts = ('ins', 'res', 'cif')
    cell_input_file = None
    hkl_file = olx.HKLSrc()
    if not os.path.exists(hkl_file):
      hkl_file = file.ChangeExt(loaded_file, 'hkl')
    if not os.path.exists(hkl_file):
      print 'Could not locate HKL file, aborting...'
      return 1
    for e in exts:
      fn = olx.file.ChangeExt(loaded_file, e)
      if os.path.exists(fn):
        cell_input_file = fn
        break
    if not cell_input_file:
      print 'Could not locate cell input file, aborting...'
      return 1
    out_dir = olx.StrDir() + '\\'
    out_file = out_dir + olx.FileName() + "-xplain.out"
    hkl_out_file = out_dir + olx.FileName() + "-xplain.hkl"
    cmdl = self.exe_file + ' /AutomaticChoice=0' + \
      ' /InputParameterFilename="' + cell_input_file + '"' + \
      ' /InputReflectionsFilename="' + hkl_file + '"' + \
      ' /OutputParameterFilename="' + out_file + '"' + \
      ' /OutputReflectionsFilename="' + hkl_out_file + '"'
    if not olx.Exec(cmdl + ' -s'):
      print 'Failed to execute the command...'
      return 1
    out_ = file(out_file, 'rb').readlines()
    out = {}
    for l in out_:
      l = l.split('=')
      if len(l) != 2: continue
      v = l[1].strip()
      if len(v) == 0: continue
      if v[0] == '{' and v[-1] == '}': v = v[1:-1]
      out[l[0].strip()] = v
    sgs = []
    sg0 = ''
    cell_counter = 0
    line_cnt = len(out)
    while True:
      cell_line = "ConstrainedCell%i" %cell_counter
      if not out.has_key(cell_line):
        break
      esd_line = "ConstrainedCellSU%i" %cell_counter
      sg_line = "SpaceGroupNameHMAlt%i" %cell_counter
      hklf_line = "DiffrnReflnsTransfMatrix%i" %cell_counter
      sg_line_tmpl = "$%s<-$%s,$%s,$%s,$%s" %(sg_line, sg_line, cell_line, esd_line, hklf_line)
      sgs.append(Template(sg_line_tmpl).substitute(out))
      if cell_counter == 0: sg0 = out[sg_line]
      cell_counter = cell_counter + 1
    if len(sgs) == 0:
      return 1
    rv = ';'.join(sgs)
    OV.SetParam('snum.refinement.sg_list', rv)
    control_name = 'SET_SNUM_REFINEMENT_SPACE_GROUP'
    if olex_gui.IsControl(control_name):
      olx.html.SetItems(control_name, rv)
      olx.html.SetValue(control_name, sg0.replace(' ', ''))
    return 0

x = XPlain()
OV.registerFunction(x.exists, False, 'xplain')
OV.registerFunction(x.run, False, 'xplain')