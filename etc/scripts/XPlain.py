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

  def run(self, run_auto=True, sync=False):
    if not self.exe_file:
      print('Could not locate the XPlain executable, aborting...')
      return False
    run_auto = run_auto not in ('False', 'false', False)
    loaded_file = OV.FileFull()
    exts = ('ins', 'res', 'cif')
    cell_input_file = None
    hkl_file = olx.HKLSrc()
    if not os.path.exists(hkl_file):
      hkl_file = olx.file.ChangeExt(loaded_file, 'hkl')
    if not os.path.exists(hkl_file):
      print('Could not locate HKL file, aborting...')
      return False
    #print 'Hkl file: ' + hkl_file
    for e in exts:
      fn = olx.file.ChangeExt(loaded_file, e)
      if os.path.exists(fn):
        cell_input_file = fn
        break
    if not cell_input_file:
      fn = os.path.normpath(olx.FilePath() + '/CrystalClear.cif')
      if os.path.exists(fn):
        cell_input_file = fn
    if not cell_input_file:
      print('Could not locate cell input file, aborting...')
      return False
    out_dir = olx.StrDir() + '\\'
    out_file = self.get_output_name()
    hkl_out_file = out_dir + olx.FileName() + "-xplain.hkl"
    log_out_file = out_dir + olx.FileName() + "-xplain.log"
    cmdl = '/InputParameterFilename="' + cell_input_file + '"' + \
      ' /InputReflectionsFilename="' + hkl_file + '"'
    if not run_auto:
      if sync:
        r = olx.Exec(self.exe_file, cmdl, o=True, s=True)
      else:
        r = olx.Exec(self.exe_file, cmdl, o=True)
      if r == 1: return True
      return False
    cmdl += ' /AutomaticChoice=0' + \
      ' /OutputParameterFilename="' + out_file + '"' + \
      ' /OutputReflectionsFilename="' + hkl_out_file + '"' + \
      ' /LogFilename="' + log_out_file + '"'
    if not olx.Exec(self.exe_file, cmdl, s=True):
      print('Failed to execute the command...')
      return False

    version = ''
    if not(os.path.exists(log_out_file)):
      print('Could not locate the output log file')
      return False
    else:
      f = file(log_out_file)
      try:
        f.readline()
        version = f.readline().strip().split()[1]
      except:
        print('Could not locate XPlain version')
      f.close()
    if version:
      print('XPlain version: ' + version)

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
    print('Found space groups:')
    while True:
      cell_line = "ConstrainedCell%i" %cell_counter
      if cell_line not in out:
        break
      esd_line = "ConstrainedCellSU%i" %cell_counter
      sg_line = "SpaceGroupNameHMAlt%i" %cell_counter
      hklf_line = "DiffrnReflnsTransfMatrix%i" %cell_counter
      symm_line = "SpaceGroupSymopOperationXyz%i" %cell_counter
      latt_line = "SHELXLATT%i" %cell_counter
      sg_line_tmpl = "$%s<-$%s~$%s~$%s~$%s~$%s" %(sg_line, symm_line, latt_line,
        cell_line, esd_line, hklf_line)
      # P1/P-1 and just centered SG will not have this
      out.setdefault(symm_line, '')
      sgs.append(Template(sg_line_tmpl).substitute(out))
      if cell_counter == 0: sg0 = out[sg_line]
      cell_counter = cell_counter + 1
      print("%i: %s" %(cell_counter, out[sg_line]))
    if len(sgs) == 0:
      print('None')
      return False
    rv = ';'.join(sgs)
    OV.SetParam('snum.refinement.sg_list', rv)
    control_name = 'SET_SNUM_REFINEMENT_SPACE_GROUP'
    if olex_gui.IsControl(control_name):
      v = olx.html.GetValue(control_name)
      olx.html.SetItems(control_name, rv)
      olx.html.SetValue(control_name, v)
    return True

  def output_exists(self):
    return os.path.exists(self.get_output_name())

  def get_output_name(self):
    out_dir = olx.StrDir() + '\\'
    return out_dir + olx.FileName() + "-xplain.out"


x = XPlain()
OV.registerFunction(x.exists, False, 'xplain')
OV.registerFunction(x.run, False, 'xplain')
OV.registerFunction(x.output_exists, False, 'xplain')
OV.registerFunction(x.get_output_name, False, 'xplain')