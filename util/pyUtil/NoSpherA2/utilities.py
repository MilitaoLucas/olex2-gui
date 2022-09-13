import functools
import gui
import os
import shutil
import time
import olx
import olex
import sys
from olexFunctions import OV
import OlexVFS
from PIL import ImageDraw, Image
from ImageTools import IT

try:
  from_outside = False
  p_path = os.path.dirname(os.path.abspath(__file__))
except:
  from_outside = True
  p_path = os.path.dirname(os.path.abspath("__file__"))

def scrub(cmd):
  log = gui.tools.LogListen()
  olex.m(cmd)
  return log.endListen()

def run_with_bitmap(bitmap_text):
  custom_bitmap(bitmap_text)
  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      OV.CreateBitmap(bitmap_text)
      try:
        return func(*args, **kwargs)
      except Exception as e:
        raise e
      finally:
        OV.DeleteBitmap(bitmap_text)
    return wrapper
  return decorator

def custom_bitmap(text):
  bitmap_font = "DefaultFont"
  bitmap = {
    text: {'label': text,
           'name': text,
              'color': '#ff4444',
              'size': (len(text) * 12, 32),
              'font_colour': "#ffffff",
              }
  }
  map = bitmap[text]
  colour = map.get('color', '#ffffff')
  name = map.get('name', 'untitled')
  txt = map.get('label', '')
  size = map.get('size')
  image = Image.new('RGB', size, colour)
  draw = ImageDraw.Draw(image)
  IT.write_text_to_draw(draw,
                        txt,
                             top_left = (5, -1),
                             font_name=bitmap_font,
                             font_size=24,
                             font_colour = map.get('font_colour', '#000000')
                             )
  OlexVFS.save_image_to_olex(image, name, 2)

@run_with_bitmap('Partitioning')
def cuqct_tsc(wfn_file, hkl_file, cif, groups, save_k_pts=False, read_k_pts=False):
  basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
  folder = OV.FilePath()
  name = OV.ModelSrc()
  final_log_name = name + ".partitionlog"
  if type([]) != type(wfn_file):
    gui.get_default_notification(
        txt="Calculating .tsc file from Wavefunction <b>%s</b>..."%os.path.basename(wfn_file),
        txt_col='black_text')
  ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
  if os.path.isfile(os.path.join(folder, final_log_name)):
    shutil.move(os.path.join(folder, final_log_name), os.path.join(folder, final_log_name + "_old"))
  args = []
  wfn_2_fchk = OV.GetVar("Wfn2Fchk")
  args.append(wfn_2_fchk)
  if not os.path.exists(hkl_file):
    from cctbx_olex_adapter import OlexCctbxAdapter
    cctbx_adaptor = OlexCctbxAdapter()
    with open(hkl_file, "w") as out:
      f_sq_obs = cctbx_adaptor.reflections.f_sq_obs
      f_sq_obs = f_sq_obs.complete_array(d_min_tolerance=0.01, d_min=f_sq_obs.d_max_min()[1]*0.95, d_max=f_sq_obs.d_max_min()[0], new_data_value=-1, new_sigmas_value=-1)
      f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
  if (int(ncpus) > 1):
    args.append('-cpus')
    args.append(ncpus)
  if (OV.GetParam('snum.NoSpherA2.wfn2fchk_debug') == True):
    args.append('-v')
  if (OV.GetParam('snum.NoSpherA2.wfn2fchk_ED') == True):
    args.append('-ED')
  if (OV.GetParam('snum.NoSpherA2.becke_accuracy') != "Normal"):
    args.append('-acc')
    if (OV.GetParam('snum.NoSpherA2.becke_accuracy') == "Low"):
      args.append('1')
    elif (OV.GetParam('snum.NoSpherA2.becke_accuracy') == "High"):
      args.append('3')
    elif (OV.GetParam('snum.NoSpherA2.becke_accuracy') == "Max"):
      args.append('4')
  if(save_k_pts):
    args.append('-skpts')
  if(read_k_pts):
    args.append('-rkpts')
  if "ECP" in basis_name:
    args.append("-ECP")
    mode = OV.GetParam('snum.NoSpherA2.wfn2fchk_ECP')
    args.append(str(mode))
  olex_refinement_model = OV.GetRefinementModel(False)

  if olex_refinement_model['hklf']['value'] >= 5:
    try:
      src = OV.HKLSrc()
      cmd = "HKLF5 -e '%s'" %src
      res = scrub(cmd)
      if "HKLF5 file is expected" in " ".join(res):
        pass
      elif "negative batch numbers" in " ".join(res):
        pass
      else:
        args.append("-twin")
        for i in res[4].split() + res[6].split() + res[8].split():
          args.append(str(float(i)))
    except:
      print("There is a problem with the HKLF5 file...")
  elif 'twin' in olex_refinement_model:
    c = olex_refinement_model['twin']['matrix']
    args.append("-twin")
    for row in c:
      for el in row:
        args.append(str(float(el)))
  
  if type([]) == type(wfn_file):
    if type([]) == type(cif):
      args.append("-cmtc")
      if len(wfn_file) != len(groups) or len(wfn_file) != len(groups):
        print("Insonstiant size of parameters! ERROR!")
        return
      for i in range(len(wfn_file)):
        args.append(wfn_file[i])
        args.append(cif[i])
        for j in range(len(groups[i])):
          groups[i][j] = str(groups[i][j])
        args.append(','.join(groups[i]))
    else:
      args.append("-cif")
      args.append(cif)
      args.append("-mtc")
      if len(wfn_file) != len(groups):
        print("Insonstiant size of parameters! ERROR!")
        return
      for i in range(len(wfn_file)):
        args.append(wfn_file[i])
        for j in range(len(groups[i])):
          groups[i][j] = str(groups[i][j])
        args.append(','.join(groups[i]))      
  else:
    args.append("-wfn")
    args.append(wfn_file)  
    args.append("-cif")
    args.append(cif)
    if(groups[0] != -1000):
      args.append('-group')
      for i in range(len(groups)):
        args.append(groups[i])
  args.append("-hkl")
  args.append(hkl_file)

  os.environ['cuqct_cmd'] = '+&-'.join(args)
  os.environ['cuqct_dir'] = folder
  import subprocess

  p = None
  if sys.platform[:3] == 'win':
    startinfo = subprocess.STARTUPINFO()
    startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startinfo.wShowWindow = 7
    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      return
    p = subprocess.Popen([pyl,
                          os.path.join(p_path, "cuqct-launch.py")],
                          startupinfo=startinfo)
  else:
    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      return
    p = subprocess.Popen([pyl,
                          os.path.join(p_path, "cuqct-launch.py")])

  out_fn = "NoSpherA2.log"

  tries = 0
  while not os.path.exists(out_fn):
    if p.poll() is None:
      time.sleep(1)
      tries += 1
      if tries >= 5:
        if "python" in args[2] and tries <=10:
          continue
        print("Failed to locate the output file")
        OV.SetVar('NoSpherA2-Error',"NoSpherA2-Output not found!")
        raise NameError('NoSpherA2-Output not found!')
    else:
      print("process ended before the output file was found")
      OV.SetVar('NoSpherA2-Error',"NoSpherA2 ended unexpectedly!")
      raise NameError('NoSpherA2 ended unexpectedly!')
  with open(out_fn, "rU") as stdout:
    while p.poll() is None:
      x = stdout.read()
      if x:
        print(x, end='')
        olx.xf.EndUpdate()
        if OV.HasGUI():
          olx.Refresh()
      else:
        olx.xf.EndUpdate()
        if OV.HasGUI():
          olx.Refresh()
      # if OV.GetVar("stop_current_process"):
      #  p.terminate()
      #  print("Calculation aborted by INTERRUPT!")
      #  OV.SetVar("stop_current_process", False)
      # else:
      #  time.sleep(0.1)

  sucess = False
  shutil.move(out_fn, final_log_name)
  with open(final_log_name, "r") as f:
    l = f.readlines()
    if "Writing tsc file...  ... done!\n" in l or "Writing tsc file...\n" in l:
      sucess = True
  
  if sucess == True:
    print("\n.tsc calculation ended!")
  else:
    print ("\nERROR during tsc calculation!")
    raise NameError('NoSpherA2-Output not complete!')

def get_nmo():
  if os.path.isfile(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn")) == False:
    return -1
  wfn = open(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn"))
  line = ""
  while "MOL ORBITAL" not in line:
    line = wfn.readline()
  values = line.split()
  return values[1]

def get_ncen():
  if os.path.isfile(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn")) == False:
    return -1
  wfn = open(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn"))
  line = ""
  while "MOL ORBITAL" not in line:
    line = wfn.readline()
  values = line.split()
  return values[6]

OV.registerFunction(get_nmo,True,'NoSpherA2')
OV.registerFunction(get_ncen, True, 'NoSpherA2')

def combine_tscs(match_phrase="_part_", no_check=False):
  gui.get_default_notification(txt="Combining .tsc files", txt_col='black_text')
  args = []
  NSP2_exe = OV.GetVar("Wfn2Fchk")
  args.append(NSP2_exe)
  if (no_check):
    args.append("-merge_nocheck")
  else:
    args.append("-merge")

  print("Combinging the .tsc files of disorder parts... Please wait...")
  sfc_name = OV.ModelSrc()

  tsc_dst = os.path.join(OV.FilePath(), sfc_name + "_total.tsc")
  if os.path.exists(tsc_dst):
    backup = os.path.join(OV.FilePath(), "tsc_backup")
    if not os.path.exists(backup):
      os.mkdir(backup)
    i = 1
    while (os.path.exists(os.path.join(backup,sfc_name + ".tsc") + "_%d"%i)):
      i = i + 1
    try:
      shutil.move(tsc_dst,os.path.join(backup,sfc_name + ".tsc") + "_%d"%i)
    except:
      pass

  if match_phrase != "":
    from os import walk
    _, _, filenames = next(walk(OV.FilePath()))
    for f in filenames:
      if match_phrase in f and ".tsc" in f:
        args.append(os.path.join(OV.FilePath(), f))
  else:
    print("ERROR! Please make sure threre is a match phrase to look for tscs!")
    return False
  startinfo = None

  from subprocess import Popen, PIPE
  from sys import stdout
  if sys.platform[:3] == 'win':
    from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW, SW_HIDE
    startinfo = STARTUPINFO()
    startinfo.dwFlags |= STARTF_USESHOWWINDOW
    startinfo.wShowWindow = SW_HIDE

  if startinfo == None:
    with Popen(args, stdout=PIPE) as p:
      for c in iter(lambda: p.stdout.read(1), b''):
        string = c.decode()
        stdout.write(string)
        stdout.flush()
        if '\r' in string or '\n' in string:
          olx.xf.EndUpdate()
          if OV.HasGUI():
            olx.Refresh()
  else:
    with Popen(args, stdout=PIPE, startupinfo=startinfo) as p:
      for c in iter(lambda: p.stdout.read(1), b''):
        string = c.decode()
        stdout.write(string)
        stdout.flush()
        if '\r' in string or '\n' in string:
          olx.xf.EndUpdate()
          if OV.HasGUI():
            olx.Refresh()

  tsc_dst = os.path.join(OV.FilePath(),sfc_name + "_total.tsc")
  shutil.move(os.path.join(OV.FilePath(),"combined.tsc"),tsc_dst)

  try:
    OV.SetParam('snum.NoSpherA2.file', tsc_dst)
    olx.html.SetValue('SNUM_REFINEMENT_NSFF_TSC_FILE', os.path.basename(tsc_dst))
  except:
    pass
  olx.html.Update()
  return True

OV.registerFunction(combine_tscs,True,'NoSpherA2')

def deal_with_parts():
  parts = OV.ListParts()
  if not parts:
    return
  grouped_parts = read_disorder_groups()
  if grouped_parts == []:
    groups = []
    for part in parts:
      if part == 0:
        continue
      groups.append(["0",str(part)])
      olex.m("showp 0 %s" %part)
      fn = "%s_part_%s.xyz" %(OV.ModelSrc(), part)
      olx.File(fn,p=8)
    olex.m("showp")
    return list(parts), groups
  else:
    result = []
    groups = []
    longest = 0
    for i in range(len(grouped_parts)):
      if len(grouped_parts[i]) > longest:
        longest = i
    
    for i in range(len(grouped_parts[longest])):
      command = "showp 0"
      groups.append(["0"])
      result.append(i+1)
      for j in range(len(grouped_parts)):
        if i >= len(grouped_parts[j]):
          command += " %d"%grouped_parts[j][0]
          groups[i].append(str(grouped_parts[j][0]))
        else:
          command += " %d"%grouped_parts[j][i]
          groups[i].append(str(grouped_parts[j][i]))
      olex.m(command)
      fn = "%s_part_%s.xyz" %(OV.ModelSrc(), i+1)
      olx.File(fn,p=8)
    # I will return only a simple sequence which maps onto the calculations to be done
    olex.m("showp")
    return result, groups
OV.registerFunction(deal_with_parts, True, 'NoSpherA2')

def check_for_matching_fcf():
  p = OV.FilePath()
  name = OV.ModelSrc()
  fcf = os.path.join(p,name + '.fcf')
  if os.path.exists(fcf):
    return True
  else:
    return False
OV.registerFunction(check_for_matching_fcf,True,'NoSpherA2')

def check_for_matching_wfn():
  p = OV.FilePath()
  name = OV.ModelSrc()
  wfn = os.path.join(p, name + '.wfn')
  wfx = os.path.join(p, name + '.wfx')
  gbw = os.path.join(p, name + '.gbw')
  if os.path.exists(wfn):
    return True
  elif os.path.exists(wfx):
    return True
  elif os.path.exists(gbw):
    return True
  else:
    return False
OV.registerFunction(check_for_matching_wfn,True,'NoSpherA2')

def read_disorder_groups():
  inp = OV.GetParam('snum.NoSpherA2.Disorder_Groups')
  if inp == None or inp == "":
    return []
  groups = inp.split(';')
  result = []
  for i in range(len(groups)):
    result.append([])
    for part in groups[i].split(','):
      if '-' in part:
        if len(part) > 2:
          a, b = part.split('-')
          result[i].extend(list(range(int(a),int(b)+1)))
        else:
          result[i].append(int(part))
      else:
        result[i].append(int(part))
  return result
OV.registerFunction(read_disorder_groups, True, 'NoSpherA2')

def is_disordered():
  parts = OV.ListParts()
  if not parts:
    return False
  else:
    return True
OV.registerFunction(is_disordered, True, 'NoSpherA2')

def org_min():
  OV.SetParam('snum.NoSpherA2.basis_name',"3-21G")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"SloppySCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"EasyConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.01")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.6")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(org_min, False, "NoSpherA2")
def org_small():
  OV.SetParam('snum.NoSpherA2.basis_name',"cc-pVDZ")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"NoSpherA2SCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"EasyConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.6")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(org_small, False, "NoSpherA2")
def org_final():
  OV.SetParam('snum.NoSpherA2.basis_name',"cc-pVTZ")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Normal")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"StrongSCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"EasyConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.0001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.6")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',True)
  olex.m("html.Update()")
OV.registerFunction(org_final, False, "NoSpherA2")

def light_min():
  OV.SetParam('snum.NoSpherA2.basis_name',"3-21G")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"SloppySCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.01")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(light_min, False, "NoSpherA2")
def light_small():
  OV.SetParam('snum.NoSpherA2.basis_name',"def2-SVP")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"NoSpherA2SCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(light_small, False, "NoSpherA2")
def light_final():
  OV.SetParam('snum.NoSpherA2.basis_name',"def2-TZVP")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Normal")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"StrongSCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.0001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',False)
  OV.SetParam('snum.NoSpherA2.full_HAR',True)
  olex.m("html.Update()")
OV.registerFunction(light_final, False, "NoSpherA2")

def heavy_min():
  OV.SetParam('snum.NoSpherA2.basis_name',"x2c-SVP")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"SloppySCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.01")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',True)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(heavy_min, False, "NoSpherA2")
def heavy_small():
  OV.SetParam('snum.NoSpherA2.basis_name',"jorge-DZP-DKH")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Low")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"NoSpherA2SCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',True)
  OV.SetParam('snum.NoSpherA2.full_HAR',False)
  olex.m("html.Update()")
OV.registerFunction(heavy_small, False, "NoSpherA2")
def heavy_final():
  OV.SetParam('snum.NoSpherA2.basis_name',"x2c-TZVP")
  OV.SetParam('snum.NoSpherA2.method',"PBE")
  OV.SetParam('snum.NoSpherA2.becke_accuracy',"Normal")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Conv',"StrongSCF")
  OV.SetParam('snum.NoSpherA2.ORCA_SCF_Strategy',"SlowConv")
  OV.SetParam('snum.NoSpherA2.cluster_radius',0)
  OV.SetParam('snum.NoSpherA2.DIIS',"0.0001")
  OV.SetParam('snum.NoSpherA2.pySCF_Damping',"0.85")
  OV.SetParam('snum.NoSpherA2.ORCA_Solvation',"Vacuum")
  OV.SetParam('snum.NoSpherA2.Relativistic',True)
  OV.SetParam('snum.NoSpherA2.full_HAR',True)
  olex.m("html.Update()")
OV.registerFunction(heavy_final, False, "NoSpherA2")

def make_quick_button_gui():
  import olexex

  max_Z, heaviest_element_in_formula = olexex.FindZOfHeaviestAtomInFormula()
  d = {}
  if max_Z < 10:
    d.setdefault('type', 'org')
    d.setdefault('description', 'Organic Molecule (Z &lt; 10) ')
  elif max_Z < 36:
    d.setdefault('type', 'light')
    d.setdefault('description', 'Light metal (Z &lt; 35) ')
  else:
    d.setdefault('type', 'heavy')
    d.setdefault('description', 'Heavy metal (Z  &gt; 35) ')

  buttons = ""
  base_col = OV.GetParam("gui.action_colour")
  for item in [("min", IT.adjust_colour(base_col, luminosity=1.0, as_format='hex'), "Test"),
               ("small", IT.adjust_colour(base_col, luminosity=0.9, as_format='hex'), "Work"),
               ("final", IT.adjust_colour(base_col, luminosity=0.8, as_format='hex'), "Final")]:
    d["qual"]=item[0]
    d["col"]=item[1]
    d["value"]=item[2]
    buttons += '''
    <td width="20%%">
      <input
        type="button"
        name="nosphera2_quick_button_%(type)s_%(qual)s"
        value="%(value)s"
        height="GetVar(HtmlComboHeight)"
        onclick="spy.SetParam('snum.NoSpherA2.Calculate',True)>>spy.NoSpherA2.%(type)s_%(qual)s()"
        bgcolor="%(col)s"
        fgcolor="#ffffff"
        fit="false"
        flat="GetVar(linkButton.flat)"
        hint=""
        disabled="false"
        custom="GetVar(custom_button)"
      >
    </td>''' % d

  d["buttons"]=buttons

  t='''
<td width="40%%" align='left'>
<b>%(description)s</b>
</td>
%(buttons)s
''' % d
  return t
OV.registerFunction(make_quick_button_gui, False, "NoSpherA2")