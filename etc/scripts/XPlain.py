from olexFunctions import OlexFunctions
OV = OlexFunctions()
import os
import olx

def XPlain():
  exe_file = olx.file.Which("XPlain.exe")
  if not exe_file:
    exe_file = r"C:\Rigaku\XPlain\XPlain.exe"
    if not os.path.exists(exe_file):
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
  cmdl = exe_file + ' /AutomaticChoice=0' + \
    ' /InputParameterFilename="' + cell_input_file + '"' + \
    ' /InputReflectionsFilename="' + hkl_file + '"' + \
    ' /OutputParameterFilename="' + out_file + '"' + \
    ' /OutputReflectionsFilename="' + hkl_out_file + '"'
  print 'Running:'
  print cmdl
  if not olx.Exec(cmdl + ' -s'):
    print 'Failed to execute the command...'
    return 1
  olx.WaitFor('process')
  print file(out_file, 'rb').read()
  return 0

OV.registerFunction(run_XPlain, False, 'external')