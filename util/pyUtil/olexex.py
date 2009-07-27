import olex
import glob
import olx
import os
import time
import olex_core
import sys
import programSettings

import socket
import urllib
URL = "http://dimas.dur.ac.uk/"

# timeout in seconds
timeout = 15
socket.setdefaulttimeout(timeout)


sys.path.append(r".\src")
import History


import ExternalPrgParameters
SPD, RPD = ExternalPrgParameters.defineExternalPrograms()

from olexFunctions import OlexFunctions
OV = OlexFunctions()
import variableFunctions

haveGUI = OV.HasGUI()

if __debug__:
  #gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS)
  #gc.set_debug(gc.DEBUG_STATS)
  #gc.set_debug(gc.DEBUG_SAVEALL | gc.DEBUG_STATS)
  
  def dump():
    #a = gc.get_threshold()
    dump_garbage()
    #a = gc.garbage
    #b = gc.collect()
  OV.registerFunction(dump)
  
  def collect(generation=None):
    print gc.get_count()
    if generation != None:
      a = gc.collect(generation)
    else:
      a = gc.collect()
    print "%s garbage items collected" %a
  OV.registerFunction(collect)
  
  def getObjectCount():
    #a = gc.get_objects()
    a = get_all_objects()
    #a = []
    print "Number of objects: %s" %len(a)
    #print a[0]
    #print a[50]
    #print a[-10]
    #print "\n\n"
    a = []
    gc.collect()
    return ''
  OV.registerFunction(getObjectCount)
  
  def dump_garbage():
    """
    show us what's the garbage about
    """
    
    # force collection
    print "\nGARBAGE:"
    a = gc.collect()
    print "%s objects collected" %a
    
    print "\nGARBAGE OBJECTS:"
    for x in gc.garbage:
        s = str(x)
        if len(s) > 80: s = s[:80]
        print type(x),"\n  ", s
        if type(x).__name__ == 'function':
          print x.func_code
          #print x.func_name
          
    print 'Size of garbage is: ',len(gc.garbage)
    
  # Recursively expand slist's objects
  # into olist, using seen to track
  # already processed objects.
  def _getr(slist, olist, seen):
    for e in slist:
      if id(e) in seen:
        continue
      seen[id(e)] = None
      olist.append(e)
      tl = gc.get_referents(e)
      if tl:
        _getr(tl, olist, seen)

  # The public function.
  def get_all_objects():
    """Return a list of all live Python
    objects, not including the list itself."""
    gcl = gc.get_objects()
    olist = []
    seen = {}
    # Just in case:
    seen[id(gcl)] = None
    seen[id(olist)] = None
    seen[id(seen)] = None
    # _getr does the real work.
    _getr(gcl, olist, seen)
    return olist
  
  # -*- Mode: Python; tab-width: 4 -*-
  
  import types
  
  def get_refcounts():
    d = {}
    sys.modules
    # collect all classes
    for m in sys.modules.values():
      for sym in dir(m):
        o = getattr (m, sym)
        if type(o) is types.ClassType:
          d[o] = sys.getrefcount (o)
    # sort by refcount
    pairs = map (lambda x: (x[1],x[0]), d.items())
    pairs.sort()
    pairs.reverse()
    return pairs
  
  def print_top_100():
    for n, c in get_refcounts()[:100]:
      print '%10d %s' % (n, c.__name__)
      
  OV.registerFunction(print_top_100)

#if headless:
  #from olexexc import *
#else:
  #from olexexh import *

#GuiFunctions.registerFunctions()

class SpyVar(object):
  MatchedFragments = {}
  MatchedRms = []

class OlexAtoms(object):
  def __init__(self):
    self.id_for_name = {}
    #self.atoms = []
    self.atoms = [atom for atom in self.iterator()]
    
  def iterator(self):
    for i in xrange(int(olx.xf_au_GetAtomCount())):
      #name = olx.xf_au_GetAtomName(i)
      #xyz = stt(olx.xf_au_GetAtomCrd(i))
      #u = stt(olx.xf_au_GetAtomU(i))
      #type = olx.xf_au_GetAtomType(i)
      #occu = float(olx.xf_au_GetAtomOccu(i))
      atom = {}
      name = olx.xf_au_GetAtomName(i)
      atom.setdefault('name', name)
      atom.setdefault('xyz', stt(olx.xf_au_GetAtomCrd(i)))
      atom.setdefault('u', stt(olx.xf_au_GetAtomU(i)))
      atom.setdefault('type', olx.xf_au_GetAtomType(i))
      atom.setdefault('occu', float(olx.xf_au_GetAtomOccu(i)))
      atom.setdefault('afix', olx.xf_au_GetAtomAfix(i))
      
      
      if name[:1] != "Q" and olx.xf_au_IsAtomDeleted(i) == "false":
        #yield name, xyz, u, type, occu
        yield atom
        #self.id_for_name[name] = str(i)
        #self.atoms.setdefault(name, atom)
        
  def olexAtoms(self):
    #return [i for i in self.iterator()]
    return self.atoms
  
  def numberAtoms(self):
    #return sum(atom['occu'] for atom in self.iterator())
    return sum(atom['occu'] for atom in self.atoms)
  
  def number_non_hydrogen_atoms(self):
    #return sum(atom['occu'] for atom in self.iterator() if atom['type'] not in ('H','Q'))
    return sum(atom['occu'] for atom in self.atoms if atom['type'] not in ('H','Q'))
  
  def currentFormula(self):
    curr_form = {}
    #for atom in self.iterator():
    for atom in self.atoms:
      atom_type = atom['type']
      atom_occu = atom['occu']
      curr_form.setdefault(atom_type, 0)
      curr_form[atom_type] += atom_occu
    return curr_form
  
  def getExpectedPeaks(self):
    #olex_atoms = [i for i in OlexAtoms().iterator()]
    cell_volume = float(olx.xf_au_GetVolume())
    expected_atoms = cell_volume/15
    present_atoms = self.numberAtoms()
    present_atoms = self.number_non_hydrogen_atoms()
    expected_peaks = expected_atoms - present_atoms 
    if expected_peaks < 5: expected_peaks = 5
    return int(expected_peaks)
  
def stt(str):
  l = []
  s = str.split(",")
  for item in s:
    l.append(float(item))
  retval = tuple(l)
  return retval

def get_refine_ls_hydrogen_treatment():
  afixes_present = []
  afixes = {0:'refall',
            1:'noref',
            2:'refxyz',
            3:'constr',
            4:'refxyz',
            5:'constr',
            7:'refxyz',
            8:'refxyz',
            }
  a = OlexAtoms()
  for atom in a.olexAtoms():
    if atom['type'] == 'H':
      afix = atom['afix']
      n = int(afix[-1])
      if len(afix) > 1:
        m = int(afix[:-1])
      else:
        m = 0
      if not afixes[n] in afixes_present:
        afixes_present.append(afixes[n])
  if len(afixes_present) == 0:
    return 'undef'
  elif len(afixes_present) == 1:
    return afixes_present[0]
  else:
    return 'mixed'
      
OV.registerFunction(get_refine_ls_hydrogen_treatment)

def GetAvailableRefinementProgs():
  retStr = "cctbx LBFGS<-cctbx;"
  retStr += "ShelXL L.S.;"
  retStr += "ShelXL CGLS;"
  retStr += "ShelXH L.S.;"
  retStr += "ShelXH CGLS;"
  if OV.IsPluginInstalled('AutoChem'):
    retStr+= "cctbx AutoChem<-cctbx AutoChem"
  return retStr
OV.registerFunction(GetAvailableRefinementProgs)

def GetAvailableSolutionProgs():
  retStr = "cctbx;"
  a = olx.file_Which('XS.exe')
  if a == "":
    a = olx.file_Which('ShelXS.exe')
  if a:
    retStr += "ShelXS;"
  return retStr
OV.registerFunction(GetAvailableSolutionProgs)


def OnMatchStart(argStr):
  OV.write_to_olex('match.htm', "<b>RMS (&Aring;)&nbsp;Matched Fragments</b><br>")
  SpyVar.MatchedFragments = {}
  SpyVar.MatchedRms = []
  return ""
if haveGUI:
  OV.registerCallback('startmatch',OnMatchStart)

def OnMatchFound(rms, fragA, fragB):
  fragA = "'%s'" %fragA.replace(",", " ")
  fragB = "'%s'" %fragB.replace(",", " ")
  fragL = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U']
  if len(SpyVar.MatchedFragments) > 16:
    return
  if fragA not in SpyVar.MatchedFragments:
    idA = fragL[len(SpyVar.MatchedFragments)]
    SpyVar.MatchedFragments.setdefault(fragA, {'fragID':idA})
  else:
    idA = SpyVar.MatchedFragments[fragA].get('fragID')
  if fragB not in SpyVar.MatchedFragments:
    idB = fragL[len(SpyVar.MatchedFragments)]
    SpyVar.MatchedFragments.setdefault(fragB, {'fragID':idB})
  else:
    idB = SpyVar.MatchedFragments[fragB].get('fragID')
    
  rms = float(rms)
  SpyVar.MatchedRms.append(rms)
  outStr = ""
  try:
    outStr += olex.readImage('match.htm')
  except:
    pass
  
  outStr+='<font size="3"><b>'
  if rms < 0.2:
    outStr += '<font color="#10c237">%.4f</font>&nbsp;' %(rms)
  elif rms < 1:
    outStr += '<font color="#f59b0e">%.4f</font>&nbsp;' %(rms)
  elif rms < 2:
    outStr += '<font color="#d72e13">%.4f</font>&nbsp;' %(rms)
  else:
    outStr += '<font color="#d72e13">%.4f</font>&nbsp;' %(rms)
  outStr+='</b>&nbsp;<a href="Sel %s"><b>%s</b></a>&nbsp;' %(fragA, idA)
  outStr+='<a href="Sel %s"><b>%s </b></a>' %(fragB, idB)
  outStr+="<br></font>"
  
  OV.write_to_olex('match.htm',outStr)
if haveGUI:
  OV.registerCallback('onmatch',OnMatchFound)

#def getScreenSize():
  #retval = ()
  #from win32api import GetSystemMetrics
  #width = GetSystemMetrics (0)
  #height = GetSystemMetrics (1)
  #retval =  (width, height)
  #print retval
  #olx.SetVar("screen_width", width)
  #olx.SetVar("screen_height", height)
  #return "OK"
#OV.registerFunction(getScreenSize)

def SetFormulaFromInput():
  formula = olx.GetValue('SET_FORMULA')
  if not formula:
    return
  f = formula.split()
  Z = float(olx.xf_au_GetZ())
  argStr = ""
  for element in f:
    try:
      n = int(element[1:])*Z
      el = element[:1] 
    except:
      n = int(element[2:])*Z
      el = element[:2]
    argStr += "%s:%i," %(el, n)
  argStr = argStr.strip(',')  
  argStr = "'%s'" %argStr
  olx.xf_SetFormula(argStr)
  return ""
if haveGUI:
  OV.registerFunction(SetFormulaFromInput)


#def suvvd():
  #from RunPrg import RunPrg
  #a = RunPrg()
  #a.save_user_parameters()
  #print "The current settings have been saved for this user"
  #return ""
#OV.registerFunction(suvvd)


def ChooseLabelContent(cmd):
  s = ""
  switches = cmd.split()
  for switch in switches:
    s += "-%s " %switch
  olx.Labels(s)
  return ""
OV.registerFunction(ChooseLabelContent)

def FindZOfHeaviestAtomInFormua():
  from PeriodicTable import PeriodicTable
  retVal = 0
  PT = PeriodicTable()
  pt = PT.PeriodicTable()
  f = olx.xf_GetFormula('list')
  if not f:
    return retVal
  f = f.split(',')
  largestZ = 0
  for element in f:
    ele = element.split(":")[0]
    Z = int(pt[ele].get('Z'))
    if Z > largestZ:
      largestZ = Z
  retVal = largestZ
  return retVal

OV.registerFunction(FindZOfHeaviestAtomInFormua)

def MakeElementButtonsFromFormula():
  from PilTools import ButtonMaker
  icon_size = int(OV.FindValue('gui_html_icon_size'))
  retStr = ""
  totalcount = 0
  btn_dict = {}
  f = olx.xf_GetFormula('list')
  if not f:
    return
  f = f.split(',')
  current_formula = OlexAtoms().currentFormula()
  Z_prime = OV.GetParam('snum.refinement.Z_prime')
  for element in f:
    symbol = element.split(':')[0]
    max = float(element.split(':')[1])
    max = max*Z_prime
    present = round(current_formula.get(symbol,0),2)
    if symbol != "H":
      totalcount += max
    if present < max:
      bgcolour = (250,250,250)
    elif present ==  max:
      bgcolour = (210,255,210)
    else:
      bgcolour = (255,210,210)
    #retStr += '''
#<a href="if str.cmp(sel(),'') then 'mode name -t=%s' else 'name sel %s'>>sel -u" target="Subsequently clicked atoms will be made into %s">
#<zimg border="0" src="element-%s.png"></a>
#''' %(symbol, symbol, symbol, symbol)
    retStr += '''
<a href="if strcmp(sel(),'') then 'mode name -t=%s' else 'name sel %s'>>sel -u" target="Subsequently clicked atoms will be made into %s">
<zimg border="0" src="element-%s.png"></a>
''' %(symbol, symbol, symbol, symbol)
    
    btn_dict.setdefault(symbol,
                        {
                          'txt':symbol,
                          'bgcolour':bgcolour,
                          'image_prefix':'element',
                          'width':icon_size ,
                          'top_left':(0,-1),
                          #'grad':{'grad_colour':bgcolour,'fraction':1,'increment':10,'steps':0.2},
                          'grad':False,
                        })
    
  retStr += ''' 
<a href="if str.cmp(sel(),'') then 'mode name -t=ChooseElement()' else 'name sel ChooseElement()" target="Chose Element from the periodic table">
<zimg border="0" src="element-....png"></a>&nbsp;
'''
  btn_dict.setdefault('Table',
                      {
                        'txt':'...', 
                        'bgcolour':'#efefef',
                        'width':int(icon_size*1.2),
                        'image_prefix':'element',
                        'top_left':(0,-1),
                        #'grad':{'fraction':1,'increment':10,'steps':0.2},
                        'grad':False,
                      })
  
  hname = 'AddH'
  retStr += ''' 
<a href="showH a true>>HADD>>refine" target="Add Hydrogen">
<zimg border="0" src="element-%s.png"></a>
''' %hname
  
  btn_dict.setdefault('ADDH',
                      {
                        'txt':'%s' %hname, 
                        'bgcolour':'#efefef',
                        'image_prefix':'element',
                        'width':int(icon_size * 2),
                        'font_size':12,
                        'top_left':(2,0),
                        #'grad':{'fraction':1,'increment':10,'steps':0.2},
                        'grad':False,
                      })
  
  bm = ButtonMaker(btn_dict)
  bm.run()
  cell_volume = 0
  Z = 1
  Z_prime = OV.GetParam('snum.refinement.Z_prime')
  try:
    cell_volume = float(olex.f('Cell(volume)'))
  except:
    pass
  try:
    Z = float(olx.xf_au_GetZ())
  except:
    pass
  
  if cell_volume and totalcount:
    atomic_volume = (cell_volume)/(totalcount * Z)
    OV.SetVar('current_atomic_volume','%.1f' %atomic_volume)
    retStr = retStr.replace("\n","")
  else:
    OV.SetVar('current_atomic_volume','n/a')
  return str(retStr)
if haveGUI:
  OV.registerFunction(MakeElementButtonsFromFormula)

def CheckBoxValue(var, def_val='false'):
  if '.' in var:
    value = OV.GetParam(var)
  else:
    value = OV.FindValue(var,def_val) # XXX this should be gotten rid of
  if value in (True, 'True', 'true'):
    retVal = 'checked'
  else:
    retVal = ''
  return str(retVal)
if haveGUI:
  OV.registerFunction(CheckBoxValue)

def VoidView(recalculate='0'):
  if OV.IsControl('SNUM_MAP_BUTTON'):
    # set electron density map button to 'up' state
    olx.SetState('SNUM_MAP_BUTTON','up')
    olx.SetLabel('SNUM_MAP_BUTTON',OV.Translate('Calculate'))
    
  map_view =  OV.GetParam("snum.calcvoid_view")
  
  if recalculate == "1":
    olex.m("calcVoid")
    
  if map_view == "2D":
    olex.m("xgrid.3D(false)")
  elif map_view == "surface":
    olex.m("xgrid.3D(true)")
    olex.m("xgrid.fillmode(fill)")
  elif map_view == "wire":
    olex.m("xgrid.3D(true)")
    olex.m("xgrid.fillmode(line)")
  elif map_view == "points":
    olex.m("xgrid.3D(true)")
    olex.m("xgrid.fillmode(point)")
    
if haveGUI:
  OV.registerFunction(VoidView)

def MapView(recalculate='0'):
  if OV.IsControl('SNUM_CALCVOID_BUTTON'):
    # set calcvoid button to 'up' state
    olx.SetState('SNUM_CALCVOID_BUTTON','up')
    olx.SetLabel('SNUM_CALCVOID_BUTTON',OV.Translate('Calculate Voids'))
    
  map_type =  OV.GetParam("snum.map.type")
  map_source =  OV.GetParam("snum.map.source")
  map_view =  OV.GetParam("snum.map.view")
  map_resolution = OV.GetParam("snum.map.resolution")
  mask = OV.GetParam("snum.map.mask")
  
  if map_type == "fcalc":
    map_type = "calc"
  elif map_type == "fobs":
    map_type = "obs"
    
  if mask:
    mask_val = "-m"
  else:
    mask_val = ""
  
    
  if recalculate == "1":
    if map_source == "olex":
      olex.m("calcFourier -%s -r=%s %s" %(map_type, map_resolution, mask_val))
    else:
      olex.m("calcFourier -%s -%s -r=%s %s" %(map_type, map_source, map_resolution, mask_val))
      
  if map_view == "2D":
    olex.m("xgrid.3D(false)")
  elif map_view == "surface":
    olex.m("xgrid.3D(true)")
    olex.m("xgrid.fillmode(fill)")
  elif map_view == "wire":
    olex.m("xgrid.3D(true)")
    olex.m("xgrid.fillmode(line)")
  elif map_view == "points":
    olex.m("xgrid.3D(true)")
    olex.m("xgrid.fillmode(point)")
    
if haveGUI:
  OV.registerFunction(MapView)

def GetHklFileList():
  reflections_files = []
  reflection_file_extensions = ["hkl", "raw"]
  for extension in reflection_file_extensions:
    g = glob.glob(r"%s/*.%s" %(OV.FilePath(),extension))
    if sys.platform.startswith('linux'):
      bigG = glob.glob(r"%s/*.%s" %(OV.FilePath(),extension))
      # Added to make glob look for either case for Linux just incase the HKL isn't lowercase.
      g += bigG
    reflections_files += g
  g = reflections_files
  g.sort()
  reflection_files = ""
  try:
    a = OV.HKLSrc() 
    if a[:1] == "'":
      a = a[1:-1]
  except:
    a = ""
    
  if os.path.isfile(a):
    most_recent_reflection_file = a.split('//')[-1]
    show_refl_date = time.strftime(r"%d/%b/%Y %H:%M", time.localtime(os.path.getctime(OV.HKLSrc())))
  else:
    if g:
      most_recent_reflection_file = g[0]
      show_refl_date = time.strftime(r"%d/%b/%Y %H:%M", time.localtime(os.path.getctime(g[0])))
    else:
      print "There is no reflection file or the reflection file is not accessible"
      return
  most_recent_reflection_file = ""      
  for item in g:
    reflection_files+="%s.%s<-%s;" %(OV.FileName(item), OV.FileExt(item), item)
  return str(reflection_files)
if haveGUI:
  OV.registerFunction(GetHklFileList)

def tbxs_(name):
  retVal = ""
  txt = r'''
<!-- #include header gui\blocks\tool-header.htm;1; -->
<table border="0" style="border-collapse: collapse" width="100%" id="#tool" cellpadding="0" cellspacing="1">
        <tr>
                <td width="100%" bgcolor="$getVar(gui_html_font_colour)">
                        <-zimg border="0" src="#image.png">
                </td>
        </tr>
</table>
<table border="0" VALIGN='center' style="border-collapse: collapse" width="100%" cellpadding="1" cellspacing="1" bgcolor="$getVar(gui_html_table_bg_colour)">
'''
  
  txt += r'''
<tr VALIGN='center' NAME='Expand Short Contacts'>
  <td colspan=1 width="8" bgcolor="$getVar(gui_html_table_firstcol_colour)"></td>
    <td>
      <font size = '4'>
        <b>	
          %%setup-title-%s%%
        </b>
      </font>
    </td>
  </tr>
<tr>
  <td valign='top' width="8" bgcolor="$getVar(gui_html_table_firstcol_colour)"><zimg border="0" src="info.png"></td>
  <td>	
    %%setup-txt-%s%%
    <br>
    <a href=htmlpanelswap>Swap the position of the GUI panel</a>
    <br>
    <a href='skin HP'>Skin HP</a>
    <br>
    <a href='skin OD'>Skin OD</a>
  </td>
</tr>
'''%(name, name)
  
  txt += r'''
<!-- #include tool-footer gui\blocks\tool-footer.htm;1; -->
'''
  wFilePath = r"setup-%s.htm" %name
  OV.write_to_olex(wFilePath, txt)
  olex.m("popup setup-box 'setup-%s.htm' -b=tc -t='%s' -w=400 -h=400 -x=100 -y=200" %(name, name))
  return retVal
#OV.registerFunction(tbxs)

def GetRInfo(txt=""):
  use_history_for_R1_display = True
  if use_history_for_R1_display:
    if olx.IsFileType('cif') == "true":
      R1 = olx.Cif('_refine_ls_R_factor_gt')
    else:
      tree = History.tree
      try:
        if tree.current_refinement == 'solution':
          R1 = 'Solution'
        else:
          R1 = tree.historyTree[tree.current_solution].historyBranch[tree.current_refinement].R1
      except KeyError:
        R1 = 'n/a'
      except AttributeError:
        tree.current_refinement = OV.GetParam('snum.refinement.current_refinement')
        tree.current_solution = OV.GetParam('snum.refinement.current_solution')
        R1 = 'n/a'
      except:
        R1 = 'n/a'
        print 'Someother exception'
      
    try:
      R1 = float(R1)
      col = GetRcolour(R1)
      R1 = "%.2f" %(R1*100)
      t = r"<td colspan='1' align='center' rowspan='2'><font size='4' color='%s'><b>%s%%</b></font></td>" %(col, R1)
    except:
      t = "<td colspan='1' rowspan='2' align='center'><font size='4'><b>%s</b></font></td>" %R1
    finally:
      return t
    
  else:
    if txt:
      t = "<td colspan='1' rowspan='2' align='center'><font size='4'><b>%s</b></font></td>" %txt
    else:
      try:
        look = olex.f('IsVar(snum_refinement_last_R1)')
        if look == "true":
          R1 = olex.f('GetVar(snum_refinement_last_R1)')
        else:
          if olx.IsFileType('cif') == "true":
            R1 = olx.Cif('_refine_ls_R_factor_gt')
          else:
            R1 = olex.f('Lst(R1)')
      except:
        R1 = 0
      try:
        R1 = float(R1)
        col = GetRcolour(R1)
        R1 = "%.2f" %(R1*100)
        t = r"<td colspan='1' align='center' rowspan='2'><font size='4' color='%s'><b>%s%%</b></font></td>" %(col, R1)
      except:
        t = "<td colspan='1' rowspan='2' align='center'><font size='4'><b>%s</b></font></td>" %R1
    #wFile = open(r"%s/displayR.htm" %olx.StrDir(), 'w')
    #wFile.write(t)
    #wFile.close()
    return t
OV.registerFunction(GetRInfo)

def GetRcolour(R1):
  retVal = ""
  try:
    R1 = float(R1)
    if R1 > 0.20:
      retVal=OV.FindValue('gui_red')
    elif R1 >0.10:
      retVal=OV.FindValue('gui_orange')
    else:
      retVal=OV.FindValue('gui_green')
  except:
    retVal='grey'
  return str(retVal)

def setMainToolbarTabButtons(btn, state=""):
  isCif = OV.IsFileType('cif')
  if isCif and btn != 'report': state = 'inactive'
  btns = [("solve", "solution-settings"), ("refine", "refinement-settings"), ("report","report-settings")]
  for item in btns:
    if item[0] == btn:
      if not state:
        state = olx.html_GetItemState(item[1])
      if state == '-1':
        state = "off"
      elif state == '0':
        state = "on"
      OV.CopyVFSFile("cbtn-%s%s.png" %(item[0],state),"cbtn-%s.png" %item[0])
      OV.SetVar('gui_MainToolbarTabButtonActive',btn)
    elif state != 'inactive' and not isCif:
      OV.CopyVFSFile("cbtn-%soff.png" %item[0],"cbtn-%s.png" %item[0])
  return "Done"
if haveGUI:
  OV.registerFunction(setMainToolbarTabButtons)

def setAllMainToolbarTabButtons():
  isCif = OV.IsFileType('cif')
  btns = [("solve", "solution-settings"), ("refine", "refinement-settings"), ("report","report-settings")]
  for item in btns:
    btn = item[0]
    if isCif and btn != 'report': 
      state = 'inactive'
      if olx.html_IsItem(item[1]) == 'true':
        olx.html_ItemState(item[1],'-1')
    else:
      state = ''
      #state = 'off'
    if not state:
      #if OV.IsControl(item[1]): 
      if olx.html_IsItem(item[1]) == 'true':
        try:
          state = olx.html_GetItemState(item[1])
        except RuntimeError:
          pass
        if state == '-1':
          state = "off"
        elif state == '0':
          state = "on"
      else:
        state = 'off'
    OV.CopyVFSFile("cbtn-%s%s.png" %(btn,state),"cbtn-%s.png" %btn)
    if state == 'on':
      OV.SetVar('gui_MainToolbarTabButtonActive',btn)
  return "Done"
if haveGUI:
  OV.registerFunction(setAllMainToolbarTabButtons)

def onCrystalColourChange():
  if variableFunctions.initialisingVariables:
    return
  lustre = OV.FindValue('snum_metacif_exptl_crystal_colour_lustre')
  modifier = OV.FindValue('snum_metacif_exptl_crystal_colour_modifier')
  primary = OV.FindValue('snum_metacif_exptl_crystal_colour_primary')
  colour = ' '.join(item for item in (lustre,modifier,primary) if item != '?')
  if colour:
    OV.SetVar('snum_metacif_exptl_crystal_colour', colour)
OV.registerFunction(onCrystalColourChange)

def onRefinementProgramChange(prg_name, method=None):
  prg = RPD.programs[prg_name]
  if method is None:
    method = sortDefaultMethod(prg)
  OV.SetParam("snum.refinement.method", method)
  onRefinementMethodChange(prg_name, method)
OV.registerFunction(OV.SetRefinementProgram)

def onRefinementMethodChange(prg_name, method):
  if method in RPD.programs[prg_name].methods:
    programSettings.doProgramSettings(prg_name, method)
  else:
    print "Please choose a valid method for the refinement program %s" %prg_name
OV.registerFunction(onRefinementMethodChange)

def onSolutionProgramChange(prg_name, method=None):
  prg = SPD.programs[prg_name]
  if method is None:
    method = sortDefaultMethod(prg)
  OV.SetParam("snum.solution.method", method)
  onSolutionMethodChange(prg_name, method)
OV.registerFunction(OV.SetSolutionProgram)

def onSolutionMethodChange(prg_name, method):
  if method in SPD.programs[prg_name].methods:
    programSettings.doProgramSettings(prg_name, method)
  else:
    print "Please choose a valid method for the solution program %s" %prg_name
  return
OV.registerFunction(onSolutionMethodChange)

def sortDefaultMethod(prg):
  methods = []
  for method in prg:
    order = method.order
    methods.append((order, method))
  methods.sort()
  default = methods[0][1].name
  return default

def getSolutionPrgs():
  retval = ""
  p = []
  for prg in SPD:
    a = which_program(prg)
    if not a:
      continue
    p.append(prg.name)
  p.sort()
  for item in p:
    retval += "%s;" %item
  return retval
OV.registerFunction(getSolutionPrgs)

def getSolutionMethods(prg):
  retval = ""
  if prg == '?': return retval
  p = []
  for method in SPD.programs[prg]:
    p.append(method.name)
  p.sort()
  for item in p:
    retval += "%s;" %item
  return retval
OV.registerFunction(getSolutionMethods)

def which_program(prg):
  if "smtbx" in prg.name:
    return True
  if prg.name in SPD or prg.name in RPD:
    exec_l = prg.execs
  else:
    exec_l = ["%s.exe" %prg, "%s" %prg, "%s" %prg.lower()]
  for item in exec_l:
    a = olx.file_Which('%s' %item)
    if a:
      break
  if 'wingx' in a.lower():
    print "%s seems to be part of a WinGX installation. These ShelX executable cannot be used with Olex" %item
    return False
  return a
OV.registerFunction(which_program)

def getmap(mapName):
  if not OV.IsFileType('cif') and mapName != 'report':
    return '#map_%s' %mapName
  else:
    return ''
if haveGUI:
  OV.registerFunction(getmap)

def getRefinementPrgs():
  retval = ""
  p = []
  for prg in RPD:
    a = which_program(prg)
    if not a:
      continue
    p.append(prg.name)
    
  p.sort()
  for item in p:
    retval += "%s;" %item
  return retval
OV.registerFunction(getRefinementPrgs)

def getRefinementMethods(prg):
  retval = ""
  if prg == '?': return retval
  p = []
  for method in RPD.programs[prg]:
    p.append(method.name)
  p.sort()
  for item in p:
    retval += "%s;" %item
  return retval
OV.registerFunction(getRefinementMethods)

def QPeaksSlide(value):
  val = int(value) * 5
  if val >= 0: val = 100 - val
  else: val = -100 - val
  return val
OV.registerFunction(QPeaksSlide)

def createRMSDisplay(outStr):
  for rms in SpyVar.MatchedRms:
    if rms < 0.2:
      outStr += '<font color="#10c237">%.4f</font>&nbsp;' %(rms)
    elif rms < 1:
      outStr += '<font color="#f59b0e">%.4f</font>&nbsp;' %(rms)
    elif rms < 2:
      outStr += '<font color="#d72e13">%.4f</font>&nbsp;' %(rms)
    else:
      outStr += '<font color="#d72e13">%.4f</font>&nbsp;' %(rms)
  return outStr

def haveSelection():
  retVal = False
  res = olx.Sel()
  if res == "":
    retVal = False
  else:
    retVal = True
  return retVal

def install_plugin(plugin, args):
  user_alert_uninstall_plugin = OV.FindValue('user_alert_uninstall_plugin')
  if not plugin: return
  poke = olx.IsPluginInstalled("%s" %plugin)
  if poke == 'false':
    try:
      olex.m("installplugin %s" %plugin)
      pass
    except:
      print "The plugin %s does not exist"
    return
  
  if user_alert_uninstall_plugin[0] == 'R':
    delete = user_alert_uninstall_plugin[-1]
  elif user_alert_uninstall_plugin == 'Y':
    delete = OV.Alert('Olex2', "This will delete all files and folders of plugin '%s'. Are you sure you want to continue?" %plugin, 'YNIR', "(Don't show this warning again)")
  else:
    returnspy.install_plugin
    
  if 'Y' in delete:
    olex.m("installplugin %s" %plugin)
    pass
    
  if 'R' in delete:
    user_alert_uninstall_plugin = 'RY'
    self.setVariables('alert')
    variableFunctions.save_user_parameters('alert')
OV.registerMacro(install_plugin, "")

def runSadabs():    
  olx.User("'%s'" %OV.FilePath())
  olx.Exec("sadabs")
  #olx.WaitFor('process') # uncomment me!
OV.registerFunction(runSadabs)

def getKey(key_directory=None, specific_key = None):
  if sys.platform[:3] != 'win':
    return None
  keyPath = "%s/Olex2u/OD/" %os.environ['ALLUSERSPROFILE']
  if not key_directory:
    key_directory = keyPath
  if specific_key:
    g = glob.glob(r"%s/%s.%s" %(key_directory, specific_key, "priv"))
    for item in g:
      return item.split("\\")[-1:][0]

  import glob
  g = glob.glob(r"%s/*.%s" %(key_directory, "priv"))
  for item in g:
    keyname = item.split("\\")[-1:][0]
    return keyname.split(".")[0]
    

def getKeys(key_directory=None):
  keyPath = "%s/Olex2u/OD/" %os.environ['ALLUSERSPROFILE']
  kl = []
  if not key_directory:
    key_directory = keyPath
  import glob
  g = glob.glob(r"%s/*.%s" %(key_directory, "priv"))
  for item in g:
    keyname = item.split("\\")[-1:][0]
    kl.append(keyname.split(".")[0])
  return kl
  

def GetHttpFile(f, force=False):
  retVal = None
  go_online = OV.GetParam("olex2.is_online")
  verbose = OV.FindValue("ac_verbose", "False")
  if go_online or force:
    try:
      url = "%s/%s" %(URL, f.replace(" ",r"%20"))
      if verbose: print "--> Getting %s" %url,
      path = urllib.URLopener()
      path.addheader('pragma', 'no-cache')
      conn = path.open(url)
      content = conn.read()
      if verbose: print "OK"
      conn.close()
      retVal = content
    except Exception, err:
      OV.SetParam("olex2.is_online",False)
      retVal = None
      print "Olex2 can not reach the update server: %s" %err
      print url
  else:
    retVal = None
  return retVal


def check_for_recent_update():
  retVal = False
  path = "%s/version.txt" %OV.BaseDir()
  try:
    rFile = open(path, 'r')
    line = rFile.read()
    version = int(line.split("SVN Revision No. ")[1])
  except:
    version = 1
  last_version = int(OV.GetParam('olex2.last_version'))
#  print "Last Version: %i"%last_version
  if version > last_version:
    OV.SetParam('olex2.has_recently_updated',True)
    retVal = True
#    print "Olex2 has recently been updated"
  else:
    OV.SetParam('olex2.has_recently_updated',False)
    retVal = False
    #    print "Olex2 has not been updated"
  OV.SetParam('olex2.last_version',version)
  return retVal

def check_for_crypto():
  if olx.IsPluginInstalled(r"Crypto").lower() == 'false':
    import olex
    olex.m(r"InstallPlugin Crypto")
  if olx.IsPluginInstalled(r"AutoChem").lower() == 'false':
    import olex
    olex.m(r"InstallPlugin AutoChem")

def GetACF():
  
  no_update = False
  print "Starting ODAC..."
  if no_update:
    OV.SetParam('olex2.is_online',False)
    print "Will not update ODAC Files"
  check_for_crypto()  
  
  cont = None
  tag = OV.GetTag()
  if not tag:
    print "You need to update Olex2 to at least version 1.0"
    return
  
  debug = OV.FindValue('odac_fb', False)
  debug = True
  debug = False
  debug_deep1 = True
  debug_deep2 = False
  OV.SetVar("ac_verbose", False)
  keyname = getKey()
  

  if not debug:
    p = "%s/Olex2u/OD/" %os.environ['ALLUSERSPROFILE']
    if not os.path.exists(p):
      os.makedirs(p)
    name = "entry_ac"
    f = "/olex-distro-odac/%s/%s/%s.py" %(tag, keyname, name)
    if not os.path.exists("%s/entry_ac.py" %p):
      cont = GetHttpFile(f, force=True)
      if cont:
        wFile = open("%s/%s.py" %(p, name),'w') 
        wFile.write(cont)
        wFile.close()
      if not cont:
        print "Olex2 was not able to go online and fetch a necessary file."
        print "Please make sure that your computer is online and try again."
        return
    else:
      try:
        if check_for_recent_update() and not no_update:
          cont = GetHttpFile(f)
        if cont:
          wFile = open("%s/%s.py" %(p, name),'w') 
          wFile.write(cont)
          wFile.close()
      except Exception, err:
        print "Could not update ODAC file %s: %s" %(name, err)
      if not cont:
        wFile = open("%s/%s.py" %(p, name),'r')
        cont = wFile.read()
        wFile.close()
        if not cont:
          print "Olex2 can not access a necessary file."
          print "Please make sure that your computer is online and try again."
          return
    try:    
      sys.modules[name] = types.ModuleType(name)
      exec cont in sys.modules[name].__dict__
      odac_loaded = True
    except Exception, err:
      odac_loaded = False
      print "ODAC failed to load correctly"

  else:
    print "Debugging Mode is on. File System Based files will be used!"
    OV.SetVar("ac_debug", True)
    OV.SetVar("ac_verbose", True)
    if debug_deep1:
      OV.SetVar("ac_debug_deep1", True)
    if debug_deep2:
      OV.SetVar("ac_debug_deep2", True)
    sys.path.append(r"%s/util/pyUtil/PluginLib/plugin-AutoChemSRC/%s/" %(olx.BaseDir(), tag))
    try:
      print "Debug: Import entry_ac"
      import entry_ac
      print "Debug: entry_ac imported OK"
      odac_loaded = True
    except Exception, err:
      print "Failed: %s" %err
      odac_loaded = False

  if odac_loaded:
    OV.SetVar("HaveODAC", True)
    print "ODAC started OK"
OV.registerFunction(GetACF)
  

def runODAC(cmd):
  if OV.FindValue('HaveODAC',False):
    cmd = cmd.rstrip(" -")
    cmd += " -s"
    olex.m("cursor(busy,'Starting ODAC')")
    res = olex.m(cmd)
    if res != 1:
      print "An Error occured with running ODAC"
      olex.m("cursor()")
      
    
  else:
    print "ODAC has failed to initialize or is not installed"
  
OV.registerFunction(runODAC)
  


def HklStatsAnalysis():
  import olex_core
  stats = olex_core.GetHklStat()
OV.registerFunction(HklStatsAnalysis)
  

def InstalledPlugins():
  import olex_core
  l = olex_core.GetPluginList()
  return l

def AvailablePlugins():    
  plugins = {'ODSkin':
             {'display':'Oxford Diffraction Skin',
              'blurb':'A custom-made visual design for Oxford Diffraction'},
             'cctbx':
             {'display':'smtbx-cctbx',
              'blurb':'This will install all of the cctbx as well as the newly developed smtbx. This Small Molecule Tool Box provides totally new solution and refinement functionality.'
              }}
  s = "<hr>"
  green = OV.FindValue('gui_green', "#00ff00")
  red = OV.FindValue('gui_red', "#ff0000")
  for plugin in plugins:
    display = plugins[plugin].get('display', plugin)
    blurb = plugins[plugin].get('blurb', plugin)
    if olx.IsPluginInstalled("%s" %plugin) == 'true':
      s += "<font size='+1'><b>%s</b></font> <a href='spy.install_plugin %s>>html.reload setup-box'><font size='+1' color=%s>Uninstall</font></a><br>%s<br><br>" %(display, plugin, green, blurb)
    else:
      s += "<font size='+1'><b>%s</b></font> <a href='spy.install_plugin %s>>html.reload setup-box'><font size='+1' color=%s>Install</font></a><br>%s<br><br>" %(display, plugin, red, blurb)
  return s
OV.registerFunction(AvailablePlugins)

def AvailableSkins():    
  skins = {'OD':{'display':'Oxford Diffraction Skin'}, 'HP':{'display':'Grey'}, 'default':{'display':'Default'}}
  s = "<hr>"
  for skin in skins:
    
    if OV.FindValue('gui_skin_name') == skin:
      s += "<a href='skin %s>>html.reload setup-box'><b>%s</b></a><br>" %(skin, skins[skin].get('display', skin))
    else:
      s += "<a href='skin %s>>html.reload setup-box'>%s</a><br>" %(skin, skins[skin].get('display', skin))
  return s
if haveGUI:
  OV.registerFunction(AvailableSkins)

def AvailableExternalPrograms(prgType):
  if prgType == 'refinement':
    dict = RPD
  elif prgType == 'solution':
    dict = SPD
    
  p = {}
  for prg in dict:
    a = which_program(prg)
    if not a:
      continue
    p.setdefault(prg.name,a)
    
  return p

def AvailableExternalProgramsHtml():
  d = {}
  d.setdefault('refinement', AvailableExternalPrograms('refinement'))
  d.setdefault('solution', AvailableExternalPrograms('solution'))
  
def getReportImageSrc():
  imagePath = OV.GetParam('snum.report.image')
  if OV.FilePath(imagePath) == OV.FilePath():
    return olx.file_GetName(imagePath)
  else:
    return 'file:///%s' %imagePath
OV.registerFunction(getReportImageSrc)
  
def stopDebugging():
  try:
    import wingdbstub
    wingdbstub.debugger.ProgramQuit()
  except:
    pass
  return
OV.registerFunction(stopDebugging)
  
def StoreSingleParameter(var, args):
  if var:
    OV.StoreParameter(var)
OV.registerMacro(StoreSingleParameter, "")




if not haveGUI:
  def tbxs(name):
    print "This is not available in Headless Olex"
    return ""
  #OV.registerFunction(tbxs)
OV.registerFunction(OV.IsPluginInstalled) 