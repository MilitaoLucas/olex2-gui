import functools
import gui
import os
import shutil
import time
import olx
import olex
import olex_core
import sys
import subprocess
from olexFunctions import OV
import OlexVFS
from PIL import ImageDraw, Image
from ImageTools import IT
from PilTools import timage
from cctbx import adptbx
from cctbx.array_family import flex
from decors import run_with_bitmap
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

def write_merged_hkl():
  folder = OV.FilePath()
  name = OV.ModelSrc()
  fn = os.path.join(folder, name + "_merged.hkl")
  print("Writing " + fn)
  from cctbx_olex_adapter import OlexCctbxAdapter
  cctbx_adaptor = OlexCctbxAdapter()
  with open(fn, "w") as out:
    f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_merged
    f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
  print("Done!")
OV.registerFunction(write_merged_hkl, False, "NoSpherA2")

@run_with_bitmap('Partitioning')
def cuqct_tsc(wfn_file, cif, groups, hkl_file=None, save_k_pts=False, read_k_pts=False):
  basis_name = OV.GetParam('snum.NoSpherA2.basis_name')
  folder = OV.FilePath()
  name = OV.ModelSrc()
  final_log_name = name + ".partitionlog"
  if type([]) != type(wfn_file):
    gui.get_default_notification(
        txt="Calculating .tsc file from Wavefunction <b>%s</b>..."%os.path.basename(wfn_file),
        txt_col='black_text')
    if OV.HasGUI():
      olx.html.Update()
      olx.Refresh()
  ncpus = OV.GetParam('snum.NoSpherA2.ncpus')
  if os.path.isfile(os.path.join(folder, final_log_name)):
    shutil.move(os.path.join(folder, final_log_name), os.path.join(folder, final_log_name + "_old"))
  args = []
  NoSpherA2 = OV.GetVar("NoSpherA2")
  args.append(NoSpherA2)
  if OV.GetParam('snum.NoSpherA2.source') == "SALTED":
    salted_model_dir = OV.GetParam('snum.NoSpherA2.selected_salted_model')
    args.append("-SALTED")
    args.append(salted_model_dir)
  if not hkl_file is None:
    if not os.path.exists(hkl_file):
      from cctbx_olex_adapter import OlexCctbxAdapter
      cctbx_adaptor = OlexCctbxAdapter()
      f_sq_obs = cctbx_adaptor.reflections.f_sq_obs_merged
      with open(hkl_file, "w") as out:
        f_sq_obs = f_sq_obs.complete_array(d_min_tolerance=0.01, d_min=f_sq_obs.d_min() * 0.95, d_max=f_sq_obs.d_max_min()[0], new_data_value=-1, new_sigmas_value=-1)
        f_sq_obs.export_as_shelx_hklf(out, normalise_if_format_overflow=True)
  if (int(ncpus) >= 1):
    args.append('-cpus')
    args.append(ncpus)
  if (OV.GetParam('snum.NoSpherA2.NoSpherA2_debug') == True):
    args.append('-v')
  if (OV.GetParam('snum.NoSpherA2.NoSpherA2_ED') == True):
    args.append('-ED')
  else:
    wavelength = float(olx.xf.exptl.Radiation())
    if wavelength < 0.1:
      args.append("-ED")
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
  software = OV.GetParam('snum.NoSpherA2.source')
  if "xTB" in software or "pTB" in software:
    args.append("-ECP")
    mode = OV.GetParam('snum.NoSpherA2.NoSpherA2_ECP')
    if "xTB" in software:
      args.append(str(2))
    elif "pTB" in software:
      args.append(str(3))
  elif "ECP" in basis_name:
    args.append("-ECP")
    mode = OV.GetParam('snum.NoSpherA2.NoSpherA2_ECP')
    args.append(str(mode))
  if (OV.GetParam('snum.NoSpherA2.NoSpherA2_RI_FIT') == True):
    auxiliary_basis = OV.GetParam('snum.NoSpherA2.auxiliary_basis')
    args.append("-RI_FIT")
    args.append(auxiliary_basis)
    mem = float(OV.GetParam('snum.NoSpherA2.mem')) * 1000 #Mem in MB
    args.append("-mem")
    args.append(str(mem))  

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
  d2 = olex_core.GetHklStat()
  args.append("-hkl_min_max")
  args.append(str(d2['FileMinIndices'][0]))
  args.append(str(d2['FileMaxIndices'][0]))
  args.append(str(d2['FileMinIndices'][1]))
  args.append(str(d2['FileMaxIndices'][1]))
  args.append(str(d2['FileMinIndices'][2]))
  args.append(str(d2['FileMaxIndices'][2]))
  #shel = olx.Ins('SHEL')
  #omit = olx.Ins('OMIT')
  #d_min = d2['MinD']
  #if shel != "n/a":
  #  d = float(shel.split()[-1])
  #  if d > d_min:
  #    d_min = d
  #if omit != "n/a":
  #  from cctbx import uctbx
  #  d = uctbx.two_theta_as_d(float(omit.split()[-1]),float(olx.xf.exptl.Radiation()),deg=True)
  #  if d > d_min:
  #    d_min = d
  #args.append("-dmin")
  #args.append(str(d_min * 0.95))
  if OV.IsEDRefinement():
    try:
      top_up_d = float(OV.GetACI().EDI.get_stored_param("refinement.top_up_d"))
      if top_up_d < d2['MinD']:
        args.append("-dmin")
        args.append(str(top_up_d))
    except:
      print("Failed to set dmin for TSC")
  if type([]) == type(wfn_file):
    if type([]) == type(cif):
      args.append("-cmtc")
      if len(wfn_file) != len(groups) or len(wfn_file) != len(groups):
        print("Inconsistant size of parameters! ERROR!")
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
        print("Inconsistant size of parameters! ERROR!")
        return
      for i in range(len(wfn_file)):
        args.append(wfn_file[i])
        for j in range(len(groups[i])):
          groups[i][j] = str(groups[i][j])
        args.append(','.join(groups[i]))
    if software == "Hybrid":
      args.append("-mtc_mult")
      for i in range(1, min(6, len(groups) + 1)):
        m =  OV.GetParam('snum.NoSpherA2.Hybrid.multiplicity_Part%d' % i)
        if m is None or m == 'None':
          m = 1
        args.append(str(m))
      args.append("-mtc_charge")
      for i in range(1, min(6, len(groups) + 1)):
        c = int(OV.GetParam('snum.NoSpherA2.Hybrid.charge_Part%d' % i))
        if c < 0:
          args.append("n"+str(c))
        else:
          args.append(str(c))
      args.append("-mtc_ECP")
      for i in range(1, min(6, len(groups) + 1)):
        ECP_m_C = 0
        sftw = OV.GetParam('snum.NoSpherA2.Hybrid.software_Part%d' % i)
        if sftw == "xTB":
          ECP_m_C = 2
        elif sftw == "pTB":
          ECP_m_C = 3
        args.append(str(ECP_m_C))
    else:
      args.append("-mtc_mult")
      for i in range(len(groups)):
        m =  OV.GetParam('snum.NoSpherA2.muliplicity')
        if m is None or m == 'None':
          m = 1
        args.append(str(m))
      args.append("-mtc_charge")
      for i in range(len(groups)):
        c = int(OV.GetParam('snum.NoSpherA2.charge'))
        if c < 0:
          args.append("n"+str(c))
        else:
          args.append(str(c))
      args.append("-mtc_ECP")
      for i in range(len(groups)):
        if software == "xTB":
          args.append("2")
        elif software == "pTB":
          args.append("3")
        elif "ECP" in basis_name:
          args.append("1")
        else:
          args.append("0")

    if any(".xyz" in f for f in wfn_file):
      Cations = OV.GetParam('snum.NoSpherA2.Thakkar_Cations')
      if Cations != "" and Cations != None:
        args.append("-Cations")
        args.append(Cations)
      Anions = OV.GetParam('snum.NoSpherA2.Thakkar_Anions')
      if Anions != "" and Anions != None:
        args.append("-Anions")
        args.append(Anions)
  else:
    args.append("-wfn")
    args.append(wfn_file)
    args.append("-cif")
    args.append(cif)
    args.append("-mult")
    m = OV.GetParam('snum.NoSpherA2.multiplicity')
    if m == 0:
      m = 1
    if m is None:
      m = 1
    args.append(str(m))
    args.append("-charge")
    c = OV.GetParam('snum.NoSpherA2.charge')
    args.append(str(c))
    if(groups[0] != -1000):
      args.append('-group')
      for i in range(len(groups)):
        args.append(groups[i])
    if ".xyz" in wfn_file:
      Cations = OV.GetParam('snum.NoSpherA2.Thakkar_Cations')
      if Cations != "" and Cations != None:
        args.append("-Cations")
        args.append(Cations)
      Anions = OV.GetParam('snum.NoSpherA2.Thakkar_Anions')
      if Anions != "" and Anions != None:
        args.append("-Anions")
        args.append(Anions)

  p = None
  if sys.platform[:3] == 'win':
    startinfo = subprocess.STARTUPINFO()
    startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startinfo.wShowWindow = 7
    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      return
    p = subprocess.Popen(args, startupinfo=startinfo)
  else:
    pyl = OV.getPYLPath()
    if not pyl:
      print("A problem with pyl is encountered, aborting.")
      return
    p = subprocess.Popen(args)

  out_fn = "NoSpherA2.log"

  tries = 0
  while not os.path.exists(out_fn):
    if p.poll() is None:
      time.sleep(1)
      tries += 1
      if tries >= 10:
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
  line = ""
  if os.path.isfile(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn")) == False:
    part_log_path =  os.path.join(OV.FilePath(),OV.ModelSrc()+".partitionlog")
    if os.path.exists(part_log_path):
      with open(part_log_path) as partlog:
        while "Number of MOs:" not in line:
          line = partlog.readline()
      values = line.split(":")
      return int(values[2])
    else:
      return -1
  else:
    with open(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn")) as wfn:
      while "MOL ORBITAL" not in line:
        line = wfn.readline()
    values = line.split()
    return int(values[1])

def get_ncen():
  if os.path.isfile(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn")) == False:
    return -1
  wfn = open(os.path.join(OV.FilePath(),OV.ModelSrc()+".wfn"))
  line = ""
  while "MOL ORBITAL" not in line:
    line = wfn.readline()
  values = line.split()
  return values[6]

OV.registerFunction(get_nmo, False, 'NoSpherA2')
OV.registerFunction(get_ncen, False, 'NoSpherA2')

@run_with_bitmap("Combining .tsc")
def combine_tscs(match_phrase="_part_", no_check=False):
  gui.get_default_notification(txt="Combining .tsc files", txt_col='black_text')
  args = []
  NSP2_exe = OV.GetVar("NoSpherA2")
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
      if match_phrase in f and (".tsc" in f or ".tscb" in f) :
        args.append(os.path.join(OV.FilePath(), f))
  else:
    print("ERROR! Please make sure threre is a match phrase to look for tscs!")
    return False
  startinfo = None

  if sys.platform[:3] == 'win':
    startinfo = subprocess.STARTUPINFO()
    startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startinfo.wShowWindow = subprocess.SW_HIDE

  if startinfo == None:
    with subprocess.Popen(args, stdout=subprocess.PIPE) as p:
      for c in iter(lambda: p.stdout.read(1), b''):
        string = c.decode()
        sys.stdout.write(string)
        sys.stdout.flush()
  else:
    with subprocess.Popen(args, stdout=subprocess.PIPE, startupinfo=startinfo) as p:
      for c in iter(lambda: p.stdout.read(1), b''):
        string = c.decode()
        sys.stdout.write(string)
        sys.stdout.flush()

  if os.path.exists("combined.tsc"):
    tsc_dst = sfc_name + "_total.tsc"
    shutil.move("combined.tsc", tsc_dst)
  elif os.path.exists("combined.tscb"):
    tsc_dst = sfc_name + "_total.tscb"
    shutil.move("combined.tscb", tsc_dst)

  try:
    OV.SetParam('snum.NoSpherA2.file', tsc_dst)
    olx.html.SetValue('SNUM_REFINEMENT_NSFF_TSC_FILE', os.path.basename(tsc_dst))
  except:
    pass
  if OV.HasGUI():
    olx.html.Update()
  return True

OV.registerFunction(combine_tscs, False, 'NoSpherA2')

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
OV.registerFunction(deal_with_parts, False, 'NoSpherA2')

def check_for_matching_fcf():
  p = OV.FilePath()
  name = OV.ModelSrc()
  fcf = os.path.join(p,name + '.fcf')
  if os.path.exists(fcf):
    return True
  else:
    return False
OV.registerFunction(check_for_matching_fcf, False, 'NoSpherA2')

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
OV.registerFunction(check_for_matching_wfn, False, 'NoSpherA2')

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
OV.registerFunction(read_disorder_groups, False, 'NoSpherA2')

def is_disordered():
  parts = OV.ListParts()
  if not parts:
    return False
  else:
    return True
OV.registerFunction(is_disordered, False, 'NoSpherA2')

def software():
  return OV.GetParam('snum.NoSpherA2.source')

def org_min():
  OV.SetParam('snum.NoSpherA2.basis_name',"3-21G")
  if "Tonto" in software():
    OV.SetParam('snum.NoSpherA2.method', "B3LYP")
  elif "ORCA" in software():
    if "5.0" in software() or "6.0" in software():
      OV.SetParam('snum.NoSpherA2.method', "r2SCAN")
    else:
      OV.SetParam('snum.NoSpherA2.method', "PBE")
  else:
    OV.SetParam('snum.NoSpherA2.method', "PBE")
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
  if "Tonto" in software():
    OV.SetParam('snum.NoSpherA2.method', "B3LYP")
  elif "ORCA" in software():
    if "5.0" in software() or "6.0" in software():
      OV.SetParam('snum.NoSpherA2.method', "r2SCAN")
    else:
      OV.SetParam('snum.NoSpherA2.method', "PBE")
  else:
    OV.SetParam('snum.NoSpherA2.method', "PBE")
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
  if "Tonto" in software():
    OV.SetParam('snum.NoSpherA2.method', "B3LYP")
  elif "ORCA" in software():
    if "5.0" in software() or "6.0" in software():
      OV.SetParam('snum.NoSpherA2.method', "r2SCAN")
    else:
      OV.SetParam('snum.NoSpherA2.method', "PBE")
  else:
    OV.SetParam('snum.NoSpherA2.method', "PBE")
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
  if "Tonto" in software():
    OV.SetParam('snum.NoSpherA2.method', "B3LYP")
  elif "ORCA" in software():
    if "5.0" in software() or "6.0" in software():
      OV.SetParam('snum.NoSpherA2.method', "r2SCAN")
    else:
      OV.SetParam('snum.NoSpherA2.method', "PBE")
  else:
    OV.SetParam('snum.NoSpherA2.method', "PBE")
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
  if "Tonto" in software():
    OV.SetParam('snum.NoSpherA2.method', "B3LYP")
  elif "ORCA" in software():
    if "5.0" or "6.0" in software():
      OV.SetParam('snum.NoSpherA2.method', "r2SCAN")
    else:
      OV.SetParam('snum.NoSpherA2.method', "PBE")
  else:
    OV.SetParam('snum.NoSpherA2.method', "PBE")
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
  if "Tonto" in software():
    OV.SetParam('snum.NoSpherA2.method', "B3LYP")
  elif "ORCA" in software():
    if "5.0" in software() or "6.0" in software():
      OV.SetParam('snum.NoSpherA2.method', "r2SCAN")
    else:
      OV.SetParam('snum.NoSpherA2.method', "PBE")
  else:
    OV.SetParam('snum.NoSpherA2.method', "PBE")
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
  if "Tonto" in software():
    OV.SetParam('snum.NoSpherA2.method', "B3LYP")
  elif "ORCA" in software():
    if "5.0" in software() or "6.0" in software():
      OV.SetParam('snum.NoSpherA2.method', "r2SCAN")
    else:
      OV.SetParam('snum.NoSpherA2.method', "PBE")
  else:
    OV.SetParam('snum.NoSpherA2.method', "PBE")
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
  if "Tonto" in software():
    OV.SetParam('snum.NoSpherA2.method', "B3LYP")
  elif "ORCA" in software():
    if "5.0" in software() or "6.0" in software():
      OV.SetParam('snum.NoSpherA2.method', "r2SCAN")
    else:
      OV.SetParam('snum.NoSpherA2.method', "PBE")
  else:
    OV.SetParam('snum.NoSpherA2.method', "PBE")
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
  if "Tonto" in software():
    OV.SetParam('snum.NoSpherA2.method', "B3LYP")
  elif "ORCA" in software():
    if "5.0" in software() or "6.0" in software():
      OV.SetParam('snum.NoSpherA2.method', "r2SCAN")
    else:
      OV.SetParam('snum.NoSpherA2.method', "PBE")
  else:
    OV.SetParam('snum.NoSpherA2.method', "PBE")
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

def calculate_number_of_electrons():
  from cctbx_olex_adapter import OlexCctbxAdapter
  ne = -int(OV.GetParam('snum.NoSpherA2.charge'))
  adapter = OlexCctbxAdapter()
  for sc in adapter.xray_structure().scatterers():
    Z = sc.electron_count()
    ne += Z
  return ne, adapter

def write_precise_model_file():
  from refinement import FullMatrixRefine
  from olexex import OlexRefinementModel
  use_tsc = OV.IsNoSpherA2()
  table_name = ""
  if use_tsc == True:
    table_name = str(OV.GetParam("snum.NoSpherA2.file"))
  try:
    fmr = FullMatrixRefine()
    if table_name != "":
      norm_eq = fmr.run(build_only=True, table_file_name=table_name)
    else:
      norm_eq = fmr.run(build_only=True)
    norm_eq.build_up(False)
    reparam = norm_eq.reparametrisation
    reparam.linearise()
    jac_tr = reparam.jacobian_transpose_matching_grad_fc()
    cov_matrix = flex.abs(flex.sqrt(norm_eq.covariance_matrix().matrix_packed_u_diagonal()))
    esds = jac_tr.transpose() * flex.double(cov_matrix)
    jac_tr = None
    annotations = reparam.component_annotations
  except:
    print("Could not obtain cctbx object and calculate ESDs!\n")
    return False
  f = open(OV.ModelSrc() + ".precise_model", "w")
  matrix_run = 0
  model = OlexRefinementModel()
  UC = norm_eq.xray_structure.unit_cell()
  f.write("Positions     a          b          c       and ESDs:\n")
  for atom in model._atoms:
    xyz = atom['crd'][0]
    f.write("{:5}".format(atom['label']))
    for x in range(3):
      f.write("{:12.8f}".format(xyz[x]))
    for x in range(3):
      f.write("{:12.8f}".format(esds[matrix_run + x]))
    matrix_run += 3
    has_adp = atom.get('adp')
    if has_adp != None:
      matrix_run += 6
    else:
      matrix_run += 1
    if matrix_run < len(annotations):
      if ".C111" in annotations[matrix_run]:
        matrix_run += 25
    if matrix_run < len(annotations):
      if 'occ' in annotations[matrix_run]:
        matrix_run += 1
    if matrix_run < len(annotations):
      if 'fp' in annotations[matrix_run]:
        matrix_run += 2
    f.write("\n")
  matrix_run = 0
  f.write("\n\nADPs      (11)        (22)        (33)        (23)        (13)        (12)        Ueq     And ESDs\n")
  for atom in model._atoms:
    has_adp = atom.get('adp')
    f.write("{:5}".format(atom['label']))
    matrix_run += 3
    if has_adp != None:
      adp = has_adp[0]
      adp = (adp[0], adp[1], adp[2], adp[5], adp[4], adp[3])
      uiso = adptbx.u_cart_as_u_iso(adp)
      adp = adptbx.u_cart_as_u_cif(UC, adp)
      for u in range(6):
        f.write("{:12.8f}".format(adp[u]))
      f.write("{:12.8f}".format(uiso))
      adp_esds = (esds[matrix_run],
                  esds[matrix_run + 1],
                  esds[matrix_run + 2],
                  esds[matrix_run + 3],
                  esds[matrix_run + 4],
                  esds[matrix_run + 5])
      u_iso_esd = adptbx.u_star_as_u_iso(UC, adp_esds)
      adp_esds = adptbx.u_star_as_u_cif(UC, adp_esds)
      for u in range(6):
        f.write("{:12.8f}".format(adp_esds[u]))
      f.write("{:12.8f}".format(u_iso_esd))
      matrix_run += 6
    else:
      for u in range(6):
        f.write("{:12s}".format(" ---"))
      f.write("{:12.8f}".format(atom['uiso'][0]))
      for u in range(6):
        f.write("{:12s}".format(" ---"))
      f.write("{:12.8f}".format(esds[matrix_run]))
      matrix_run += 1
    if matrix_run < len(annotations):
      if ".C111" in annotations[matrix_run]:
        matrix_run += 25
    if matrix_run < len(annotations):
      if 'occ' in annotations[matrix_run]:
        matrix_run += 1
    if matrix_run < len(annotations):
      if 'fdp' in annotations[matrix_run]:
        matrix_run += 2
    f.write("\n")

  connectivity_full = fmr.reparametrisation.connectivity_table
  xs = fmr.xray_structure()
  from scitbx import matrix
  import math
  from cctbx.crystal import calculate_distances
  cell_params = fmr.olx_atoms.getCell()
  cell_errors = fmr.olx_atoms.getCellErrors()
  cell_vcv = flex.pow2(matrix.diag(cell_errors).as_flex_double_matrix())
  dist_stats = {}
  dist_errs = {}
  for i in range(3):
    for j in range(i+1,3):
      if (cell_params[i] == cell_params[j] and
            cell_errors[i] == cell_errors[j] and
            cell_params[i+3] == 90 and
            cell_errors[i+3] == 0 and
            cell_params[j+3] == 90 and
            cell_errors[j+3] == 0):
        cell_vcv[i,j] = math.pow(cell_errors[i],2)
        cell_vcv[j,i] = math.pow(cell_errors[i],2)
  #Prepare the Cell Variance covariance matrix, since we need it for error propagation in distances
  cell_vcv = cell_vcv.matrix_symmetric_as_packed_u()
  sl = xs.scatterers().extract_labels()
  sf = xs.sites_frac()
  #This is VCV from refinement equations
  cm = norm_eq.covariance_matrix_and_annotations().matrix
  pm = xs.parameter_map()
  pat = connectivity_full.pair_asu_table

  # calculate the distances using the prepared information
  distances = calculate_distances(
              pat,
              sf,
              covariance_matrix=cm,
              cell_covariance_matrix=cell_vcv,
              parameter_map=pm)

  #The distances only exist once we iterate over them! Therefore build them and save them in this loop
  for i,d in enumerate(distances):
    bond = sl[d.i_seq]+"-"+sl[d.j_seq]
    dist_stats[bond] = distances.distances[i]
    var = distances.variances[i]
    if (var > 0) :
      dist_errs[bond] = math.sqrt(var)
    else:
      if abs(var) > 1E-12:
        dist_errs[bond] = math.sqrt(var)
      else:
        dist_errs[bond] = 0.0

  f.write("\n\nBondlengths and errors:\n")
  for key in dist_stats:
    f.write(f"{key} {dist_stats[key]} {dist_errs[key]}\n")

  f.close()
OV.registerFunction(write_precise_model_file, False, "NoSpherA2")

def get_tsc_file_dropdown_items():
    res = gui.GetFileListAsDropdownItems(OV.FilePath(), "tsc;tscb")
    t = res.split(";")
    if len(t[0]) == 0:
        OV.SetParam('snum.NoSpherA2.file', 'No .tsc/.tscb files found')
        return "No .tsc/.tscb files found"
    else:
        return res
OV.registerFunction(get_tsc_file_dropdown_items, False, "NoSpherA2")

@run_with_bitmap("Polarizibilities")
def calc_polarizabilities(efield = 0.005, resolution = 0.1, radius = 2.5):
  from NoSpherA2.NoSpherA2 import NoSpherA2_instance as nsp2
  from . import Wfn_Job
  pol_fol =  os.path.join("olex2", "Polarizability")
  if not os.path.exists(pol_fol):
    try:
      os.mkdir(pol_fol)
    except:
      pass
  OV.SetVar("Run_number", 0)
  wfn_job = Wfn_Job.wfn_Job(nsp2, olx.FileName(), dir="olex2\\Polarizability")
  wfn_job.write_orca_input(True, efield="00")
  wfn_job.run(copy=False)
  gbw_name = os.path.join(pol_fol, olx.FileName() + ".gbw")
  zero =  os.path.join(pol_fol, "zero.gbw")
  shutil.move(gbw_name, zero)
  wfn_job.write_orca_input(True, efield=f"x{efield}")
  wfn_job.run(copy=False)
  xp = os.path.join(pol_fol, "xp.gbw")
  shutil.move(gbw_name, xp)
  wfn_job.write_orca_input(True, efield=f"x-{efield}")
  wfn_job.run(copy=False)
  xm = os.path.join(pol_fol, "xm.gbw")
  shutil.move(gbw_name, xm)
  wfn_job.write_orca_input(True, efield=f"y{efield}")
  wfn_job.run(copy=False)
  yp = os.path.join(pol_fol, "yp.gbw")
  shutil.move(gbw_name, yp)
  wfn_job.write_orca_input(True, efield=f"y-{efield}")
  wfn_job.run(copy=False)
  ym = os.path.join(pol_fol, "ym.gbw")
  shutil.move(gbw_name, ym)
  wfn_job.write_orca_input(True, efield=f"z{efield}")
  wfn_job.run(copy=False)
  zp = os.path.join(pol_fol, "zp.gbw")
  shutil.move(gbw_name, zp)
  wfn_job.write_orca_input(True, efield=f"z-{efield}")
  wfn_job.run(copy=False)
  zm = os.path.join(pol_fol, "zm.gbw")
  shutil.move(gbw_name, zm)
  args = []
  NSP2_exe = OV.GetVar("NoSpherA2")
  args.append(NSP2_exe)
  args.append("-polarizabilities")
  args.append(zero)
  args.append(xp)
  args.append(xm)
  args.append(yp)
  args.append(ym)
  args.append(zp)
  args.append(zm)
  args.append("-e_field")
  args.append(str(efield))
  args.append("-resolution")
  args.append(str(resolution))
  args.append("-radius")
  args.append(str(radius))
  args.append("-cpus")
  args.append(OV.GetParam("snum.NoSpherA2.ncpus"))

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
  else:
    with Popen(args, stdout=PIPE, startupinfo=startinfo) as p:
      for c in iter(lambda: p.stdout.read(1), b''):
        string = c.decode()
        stdout.write(string)
        stdout.flush()

  NSA2_log = "NoSpherA2.log"
  if os.path.exists(NSA2_log):
    shutil.copy(NSA2_log, olx.FileName()+".polarizability")

OV.registerFunction(calc_polarizabilities, namespace="NoSpherA2")

#CHOOSE FOLDER UTILITIES! (Used in SALTED)
def setDir(phil_value) -> None:
  """Choose a directory and set the given phil value to the result.

      Args:
          None

      Returns:
          str: The chosen directory path.
      """
  try:
    a = olex.f('choosedir("Choose your data folder")')
  except:
    print("No selection made, Aborting!")
    return
  OV.SetParam(phil_value, a)
OV.registerFunction(setDir, False, "NoSpherA2")

def appendDir(phil_value) -> None:
  """Choose a directory and set teh given phil value to the result.

      Args:
          None

      Returns:
          str: The chosen directory path.
      """
  try:
    a = olex.f('choosedir("Choose your data folder")')
  except:
    print("No selection made, Aborting")
    return
  old = OV.GetParam(phil_value)
  if old is None:
    pass
  else:
    old += ";"+a
  OV.SetParam(phil_value, old)
OV.registerFunction(appendDir, False, "NoSpherA2")

def removeDir(phil_value, item_to_remove) -> None:
  """Choose a directory and set the given phil value to the result.

      Args:
          None

      Returns:
          str: The chosen directory path.
      """
  if item_to_remove == "" or item_to_remove == "Please Select":
    return
  item_to_remove = ";" + item_to_remove
  old = OV.GetParam(phil_value)
  old = old.replace(item_to_remove,"")

  OV.SetParam(phil_value, old)
OV.registerFunction(removeDir, False, "NoSpherA2")

def toggle_full_HAR():
  if OV.GetParam('snum.NoSpherA2.full_HAR') == True:
    OV.SetParam('snum.NoSpherA2.full_HAR', False)
  else:
    OV.SetParam('snum.NoSpherA2.full_HAR', True)
  OV.setItemstate("h3-NoSpherA2-extras 2")
  OV.setItemstate("h3-NoSpherA2-extras 1")
OV.registerFunction(toggle_full_HAR, False, "NoSpherA2")