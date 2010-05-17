from __future__ import division

import olex
import glob
import olx
import os
import time
import olex_core
import sys
import programSettings
from subprocess import *

import socket
import urllib
import urllib2
URL = "http://dimas.dur.ac.uk/"

# timeout in seconds
timeout = 15
socket.setdefaulttimeout(timeout)

global _is_online
_is_online = False

sys.path.append(r".\src")
import History


import ExternalPrgParameters
SPD, RPD = ExternalPrgParameters.SPD, ExternalPrgParameters.RPD

from olexFunctions import OlexFunctions
OV = OlexFunctions()
import variableFunctions

import MakeMovie

import OlexVFS

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

class OlexRefinementModel(object):
  def __init__(self):
    olex_refinement_model = OV.GetRefinementModel(True)
    self._atoms = {}
    self.id_for_name = {}
    asu = olex_refinement_model['aunit']
    for residue in asu['residues']:
      for atom in residue['atoms']:
        if atom['label'].startswith('Q'):
          continue
        i = atom['tag']
        self._atoms.setdefault(i, atom)
        element_type = atom['type']
        self.id_for_name.setdefault(str(atom['label']), atom['aunit_id'])
    self._cell = olex_refinement_model['aunit']['cell']
    self.exptl = olex_refinement_model['exptl']
    self._afix = olex_refinement_model['afix']
    self.model= olex_refinement_model

  def atoms(self):
    return self._atoms.values()

  def iterator(self):
    for i, atom in self._atoms.items():
      name = str(atom['label'])
      element_type = str(atom['type'])
      xyz = atom['crd'][0]
      occu = atom['occu'][0]
      adp = atom.get('adp',None)
      if adp is None:
        uiso = atom.get('uiso')[0]
        u = (uiso,)
      else: u = adp[0]
      if name[:1] != "Q":
        yield name, xyz, occu, u, element_type

  def afix_iterator(self):
    for afix in self._afix:
      mn = afix['afix']
      m, n = divmod(mn, 10)
      pivot = afix['pivot']
      dependent = afix['dependent']
      pivot_neighbours = [i for i in self._atoms[pivot]['neighbours'] if not i in dependent]
      bond_length = afix['d']
      uiso = afix['u']
      yield m, n, pivot, dependent, pivot_neighbours, bond_length

  def restraint_iterator(self):
    for restraint_type in ('dfix','dang','flat','chiv'):
      for restraint in self.model[restraint_type]:
        kwds = dict(
          i_seqs = [i[0] for i in restraint['atoms']],
          sym_ops = [i[1] for i in restraint['atoms']],
          value = restraint['value'],
          weight = 1/math.pow(restraint['esd1'],2),
        )
        yield restraint_type, kwds

  def getCell(self):
    return [self._cell[param][0] for param in ('a','b','c','alpha','beta','gamma')]

  def numberAtoms(self):
    return sum(atom['occu'][0] for atom in self.atoms())

  def number_non_hydrogen_atoms(self):
    return sum(atom['occu'][0] for atom in self.atoms() if atom['type'] not in ('H','Q'))

  def currentFormula(self):
    curr_form = {}
    for atom in self.atoms():
      atom_type = atom['type']
      atom_occu = atom['occu'][0]
      curr_form.setdefault(atom_type, 0)
      curr_form[atom_type] += atom_occu
    return curr_form

  def getExpectedPeaks(self):
    cell_volume = float(olx.xf_au_GetVolume())
    expected_atoms = cell_volume/15
    #present_atoms = self.numberAtoms()
    present_atoms = self.number_non_hydrogen_atoms()
    expected_peaks = expected_atoms - present_atoms
    if expected_peaks < 5: expected_peaks = 5
    return int(expected_peaks)
##

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
  for atom  in OlexRefinementModel().atoms():
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
  if OV.IsPluginInstalled('ODAC'):
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

last_formula = None

def MakeElementButtonsFromFormula():
  global last_formula
  from PilTools import ButtonMaker
  icon_size = OV.GetParam('gui.html.icon_size')
  totalcount = 0
  btn_dict = {}
  f = olx.xf_GetFormula('list')
  if not f:
    return
  f = f.split(',')
  current_formula = OlexRefinementModel().currentFormula()
#  Z_prime = OV.GetParam('snum.refinement.Z_prime')
  Z_prime = float(olx.xf_au_GetZprime())
  Z = float(olx.xf_au_GetZ())
  html_elements = []
  for element in f:
    symbol = element.split(':')[0]
    max = float(element.split(':')[1])
    present = round(current_formula.get(symbol,0),2)
    if symbol != "H":
      totalcount += max

    max = max*Z_prime
    bgcolour = '#ff0000'
    if present < max:
      bgcolour = (250,250,250)
    elif present ==  max:
      bgcolour = (210,255,210)
    else:
      bgcolour = (255,210,210)
    command = "if strcmp(sel(),'') then 'mode name -t=%s' else 'name sel %s'>>sel -u" %(symbol, symbol)
    target = OV.TranslatePhrase('change_element-target')
    #command = "if strcmp(spy.GetParam(olex2.in_mode),'mode name -t=%s') then 'mode off' else \"if strcmp(sel(),'') then 'mode name -t=%s' else 'name sel %s'>>sel -u\"" %(symbol, symbol, symbol)
    
    html = '''
    <a href="%s" target="%s %s">
      <zimg name=IMG_BTN-ELEMENT%s border="0" src="btn-element%s.png"/>
    </a>&nbsp;'''%(command, target, symbol, symbol.upper(), symbol)
    
    html_elements.append(html)

#$spy.MakeActiveGuiButton(btn-element%s,%s)&nbsp;
#''' %(symbol, command))

    btn_dict.setdefault(
      symbol, {
        'txt':symbol,
        'bgcolour':bgcolour,
        'image_prefix':'element',
        'width':icon_size ,
        'top_left':(0,-1),
        'grad':False,
      })

  html_elements.append('''
<a href="if strcmp(sel(),'') then 'mode name -t=ChooseElement()' else 'name sel ChooseElement()"
   target="Chose Element from the periodic table">
<zimg border="0" src="btn-element....png"></a>
''')
  btn_dict.setdefault(
    'Table', {
      'txt':'...',
      'bgcolour':'#efefef',
      'width':int(icon_size*1.2),
      'image_prefix':'element',
      'top_left':(0,-1),
      'grad':False,
    })

  #hname = 'AddH'
  #btn_dict.setdefault('ADDH',
                      #{
                        #'txt':'%s' %hname,
                        #'bgcolour':'#efefef',
                        #'image_prefix':'element',
                        #'width':int(icon_size * 2),
                        #'font_size':10,
                        #'top_left':(2,0),
                        #'grad':False,
                      #})

  if current_formula != last_formula:
    last_formula = current_formula
    use_new = True
  else:
    use_new = True
    
  if use_new:
    from PilTools import timage
    TI = timage()
    for b in btn_dict:
      for state in ['on', 'off']:
        txt = btn_dict[b].get('txt')
        bgcolour = btn_dict[b].get('bgcolour')
        width = 21
        btn_type = 'tiny'
        IM = TI.make_timage(item_type='tinybutton', item=txt, state=state, width=width, colour=bgcolour)
        name = "btn-element%s%s.png" %(txt, state)
        OlexVFS.save_image_to_olex(IM, name, 1)
        if state == 'off':
          name = "btn-element%s.png" %(txt)
          OlexVFS.save_image_to_olex(IM, name, 1)
            
  else:
    bm = ButtonMaker(btn_dict)
    bm.run()
  cell_volume = 0
  Z = 1
#  Z_prime = OV.GetParam('snum.refinement.Z_prime')
  Z_prime = float(olx.xf_au_GetZprime())
  try:
    cell_volume = float(olx.xf_au_GetCellVolume())
  except:
    pass
  try:
    Z = float(olx.xf_au_GetZ())
  except:
    pass

  retStr = '\n'.join(html_elements)
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

  resolution = OV.GetParam("snum.calcvoid.resolution")
  distance = OV.GetParam("snum.calcvoid.distance")
  precise = OV.GetParam("snum.calcvoid.precise")
  cmd = "calcVoid -r=%s -d=%s" %(resolution, distance)
  if precise:
    cmd += " -p"
  olex.m(cmd)
  SetXgridView()

if haveGUI:
  OV.registerFunction(VoidView)

def MapView():
  if OV.IsControl('SNUM_CALCVOID_BUTTON'):
    # set calcvoid button to 'up' state
    olx.SetState('SNUM_CALCVOID_BUTTON','up')
    olx.SetLabel('SNUM_CALCVOID_BUTTON',OV.Translate('Calculate Voids'))

  map_type =  OV.GetParam("snum.map.type")
  map_source =  OV.GetParam("snum.map.source")
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

  if map_source == "olex":
    olex.m("calcFourier -%s -r=%s %s" %(map_type, map_resolution, mask_val))
  else:
    olex.m("calcFourier -%s -%s -r=%s %s" %(map_type, map_source, map_resolution, mask_val))

  SetXgridView()

if haveGUI:
  OV.registerFunction(MapView)

def SetXgridView():
  view = OV.GetParam("snum.xgrid.view")
  extended = OV.GetParam("snum.xgrid.extended")
  if view == "2D":
    olex.m("xgrid.RenderMode(plane)")
  elif view == "surface":
    olex.m("xgrid.RenderMode(fill)")
  elif view == "wire":
    olex.m("xgrid.RenderMode(line)")
  elif view == "points":
    olex.m("xgrid.RenderMode(point)")
  else:
    olex.m("xgrid.RenderMode(%s)" %view)
  olex.m("xgrid.Extended(%s)" %extended)

if haveGUI:
  OV.registerFunction(SetXgridView)

def GetHklFileList():
  reflections_files = []
  reflection_file_extensions = ["hkl", "hkp", "raw"]
  for extension in reflection_file_extensions:
    g = glob.glob(r"%s/*.%s" %(OV.FilePath(),extension))
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
                <td width="100%" bgcolor="$spy.GetParam(gui.html.font_colour)">
                        <-zimg border="0" src="#image.png">
                </td>
        </tr>
</table>
<table border="0" VALIGN='center' style="border-collapse: collapse" width="100%" cellpadding="1" cellspacing="1" bgcolor="$spy.GetParam(gui.html.table_bg_colour)">
'''

  txt += r'''
<tr VALIGN='center' NAME='Expand Short Contacts'>
  <td colspan=1 width="8" bgcolor="$spy.GetParam(gui.html.table_firstcol_colour)"></td>
    <td>
      <font size = '4'>
        <b>
          %%setup-title-%s%%
        </b>
      </font>
    </td>
  </tr>
<tr>
  <td valign='top' width="8" bgcolor="$spy.GetParam(gui.html.table_firstcol_colour)"><zimg border="0" src="info.png"></td>
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
      if tree.active_node is not None:
        R1 = tree.active_node.R1
      else:
        R1 = 'n/a'
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
      OV.CopyVFSFile("cbtn-%s-%s.png" %(item[0],state),"cbtn-%s.png" %item[0])
      OV.SetVar('gui_MainToolbarTabButtonActive',btn)
    elif state != 'inactive' and not isCif:
      OV.CopyVFSFile("cbtn-%s-off.png" %item[0],"cbtn-%s.png" %item[0])
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
    OV.CopyVFSFile("cbtn-%s-%s.png" %(btn,state),"cbtn-%s.png" %btn)
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

def onRefinementProgramChange(prg_name, method=None, scope='snum'):
  if prg_name == 'Auto':
    OV.SetParam('autochem.refinement.method','Auto')
    return
  prg = RPD.programs[prg_name]
  if method is None or not method:
    method = sortDefaultMethod(prg)
    if method == 'Least Squares' and olx.LSM() == 'CGLS':
      method = 'CGLS' # work-around for bug #26
  OV.SetParam("%s.refinement.method" %scope, method)
  onRefinementMethodChange(prg_name, method)
OV.registerFunction(OV.set_refinement_program)

def onRefinementMethodChange(prg_name, method):
  if method in RPD.programs[prg_name].methods:
    programSettings.doProgramSettings(prg_name, method)
  else:
    print "Please choose a valid method for the refinement program %s" %prg_name
OV.registerFunction(onRefinementMethodChange)

def onSolutionProgramChange(prg_name, method=None, scope='snum'):
  if prg_name == "Auto":
    OV.SetParam('autochem.solution.method','Auto')
    #olx.SetValue('SET_autochem_solution_METHOD', 'Auto')
    return

  prg = SPD.programs[prg_name]
  if method is None or not method:
    method = sortDefaultMethod(prg)
    if method == 'Direct Methods' and olx.Ins('PATT') != 'n/a':
      method = 'Patterson Method' # work-around for bug #48
  OV.SetParam("%s.solution.method" %scope, method)
  onSolutionMethodChange(prg_name, method)
OV.registerFunction(OV.set_solution_program)

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

def get_solution_programs(scope='snum'):
  global available_solution_programs
  if available_solution_programs is None:
    p = []
    for prg in SPD:
      a = which_program(prg)
      if not a:
        continue
      p.append(prg.name)
    p.sort()
    available_solution_programs = p
  else:
    p = available_solution_programs
  retval = ';'.join(p)
  if scope != 'snum':
    retval = 'Auto;' + retval
  return retval
OV.registerFunction(get_solution_programs)

def get_solution_methods(prg, scope='snum'):
  retval = ""
  if prg == '?': return retval
  if prg == 'Auto': return 'Auto'
  p = []
  for method in SPD.programs[prg]:
    p.append(method.name)
  p.sort()
  for item in p:
    retval += "%s;" %item
  if scope != 'snum':
    retval = 'Auto;' + retval
  return retval
OV.registerFunction(get_solution_methods)

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

available_refinement_programs = None
available_solution_programs = None

def get_refinement_programs(scope='snum'):
  global available_refinement_programs
  if available_refinement_programs is None:
    p = []
    for prg in RPD:
      a = which_program(prg)
      if not a:
        continue
      p.append(prg.name)
    p.sort()
    available_refinement_programs = p
  else:
    p = available_refinement_programs
  retval = ';'.join(p)
  if scope != 'snum':
    retval = 'Auto;' + retval
  return retval
OV.registerFunction(get_refinement_programs)

def get_refinement_methods(prg, scope='snum'):
  retval = ""
  if prg == '?': return retval
  if prg == 'Auto': return 'Auto'
  p = []
  for method in RPD.programs[prg]:
    p.append(method.name)
  p.sort()
  for item in p:
    retval += "%s;" %item
  if scope != 'snum':
    retval = 'Auto;' + retval
  return retval
OV.registerFunction(get_refinement_methods)

def QPeaksSlide(value):
  val = int(value) * 5
  if val >= 0: val = 100 - val
  else: val = -100 - val
  return val
OV.registerFunction(QPeaksSlide)

def UisoSelectSlide(value):
  val = int(value) * 5
  if val >= 0:
    val = 100 - val
    val = val * 0.001
    val = "> %.3f" %val
  else:
    val = val * 0.001 * -1
    val = "< %.3f" %val
#  print val
  return val
OV.registerFunction(UisoSelectSlide)


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
  #olx.WaitFor('process') # uncomment me!http://dimas.dur.ac.uk/olex-distro-odac/1.0-alpha/Durham-OLEX2-Demo/AutoChem%20Installer.exe
OV.registerFunction(runSadabs)

def getKey(key_directory=None, specific_key = None):
  if sys.platform[:3] != 'win':
    return None
  keyPath = "%s/Olex2u/OD/%s" %(os.environ['ALLUSERSPROFILE'], OV.GetTag())
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
  keyPath = "%s/Olex2u/OD/%s" %(os.environ['ALLUSERSPROFILE'], OV.GetTag())
  kl = []
  if not key_directory:
    key_directory = keyPath
  import glob
  g = glob.glob(r"%s/*.%s" %(key_directory, "priv"))
  for item in g:
    keyname = item.split("\\")[-1:][0]
    kl.append(keyname.split(".")[0])
  return kl


def GetCheckcifReport():

  import urllib2
  import urllib2_file

  file_name = '%s/%s.cif' %(OV.FilePath(), OV.FileName())
  rFile = open(file_name)
  #file_stat = os.stat(file_name)
  #cif = rFile.read()
  cif = rFile

  params = {
    "runtype": "symmonly",
    "referer": "checkcif_server",
    "outputtype": "html",
    "file": cif
  }

  f = urllib2.urlopen("http://vm02.iucr.org/cgi-bin/checkcif.pl", params)
  print f.read()

  #url = "http://vm02.iucr.org/cgi-bin/checkcif.pl"
  #data = urllib.urlencode(params)
  #print data
  #req = urllib2.Request(url, data)
  #response = urllib2.urlopen(req,data)
  #print response.read()
  rFile.close()
OV.registerFunction(GetCheckcifReport)

def GetHttpFile(f, force=False, fullURL = False):
  global _is_online
  retVal = None
  go_online = _is_online
  verbose = OV.FindValue("ac_verbose", "False")
  if go_online or force:
    try:
      if not fullURL:
        url = "%s/%s" %(URL, f.replace(" ",r"%20"))
      else:
        url = f
      if verbose: print "--> Getting %s" %url,
      path = urllib.URLopener()
      path.addheader('pragma', 'no-cache')
      conn = path.open(url)
      content = conn.read()
      if verbose: print "OK"
      conn.close()
      retVal = content
    except Exception, err:
      _is_online = False
      retVal = None
      print "Olex2 can not reach the update server: %s" %err
      print url
  else:
    retVal = None
  return retVal


def check_for_recent_update():
  retVal = False
  if OV.GetParam('olex2.has_recently_updated'):
    return True

  version = OV.GetSVNVersion()
  try:
    V = OV.FindValue('last_version','0')
    last_version = int(V)
  except Exception, err:
    print "Alert: Reset parameter 'last_version'"
    last_version = 0
    OV.SetVar('last_version','0')

#  print "Last Version: %i"%last_version
  if version > last_version:
    OV.SetParam('olex2.has_recently_updated',True)
    retVal = True
#    print "Olex2 has recently been updated"
  else:
    OV.SetParam('olex2.has_recently_updated',False)
    retVal = False
    #    print "Olex2 has not been updated"
  OV.SetVar('last_version',str(version))
  OV.StoreParameter('last_version', str(version))
  return retVal

def check_for_crypto():
  pass
  #if olx.IsPluginInstalled(r"Crypto").lower() == 'false':
    #import olex
    #olex.m(r"InstallPlugin Crypto")
  #if olx.IsPluginInstalled(r"ODAC").lower() == 'false':
    #import olex
    #olex.m(r"InstallPlugin ODAC")

def make_url_call(url, values):
  #url = "http://www.olex2.org/odac/update"
  data = urllib.urlencode(values)
  print data
  try:
    req = urllib2.Request(url)
    response = urllib2.urlopen(req,data)
    f = response.read()
  except:
    print "\n++++++++++++++++++++++++++++++++++++++++++++++"
    print "+ Could not reach update server at www.olex2.org"
    print "+ --------------------------------------------"
    print "+ Please make sure your computer is online"
    print "+ and that you can reach www.olex2.org"
    print "++++++++++++++++++++++++++++++++++++++++++++++\n"
    return False
  return f

def register_new_odac(username=None, pwd=None):
  OV.Cursor("Please wait while AutoChem will be installed")
  mac_address = OV.GetMacAddress()[0]
  computer_name = os.getenv('COMPUTERNAME')
  url = "http://www.olex2.org/odac/register_new"
  olex2_tag = OV.GetTag()
  if not username:
    print("Please provide a username and password")
    OV.Cursor()
    return
  if not pwd:
    print("Please provide a username and password")
    OV.Cursor()
    return
  values = {'__ac_password':pwd,
            '__ac_name':username,
            'olex2Tag':olex2_tag,
            'computerName':computer_name,
            'username':username,
            'macAddress':mac_address
            }
  f = make_url_call(url, values)

  if not f:
    print "Please provide a valid username and password, and make sure your computer is online."
    print "You may also have used up the numbr of allowable installs."
    return
  p = "%s/Olex2u/OD/%s" %(os.environ['ALLUSERSPROFILE'], olex2_tag)
  if not os.path.exists(p):
    os.makedirs(p)

  cont = GetHttpFile(f, force=True, fullURL = True)
  if cont:
    name = "AutoChem Installer.exe"
    wFile = open("%s/%s" %(p, name),'wb')
    wFile.write(cont)
    wFile.close()
  ins = "%s/AutoChem Installer.exe" %p
  cmd = r"%s /S" %ins
#  print cmd
  Popen(cmd, shell=False, stdout=PIPE).stdout
  for i in xrange(10):
    try:
      os.remove(ins)
      break
    except:
      time.sleep(5)
  print "AutoChem is now installed on your computer."
  print "Please restart Olex2 now."
  OV.Cursor()

OV.registerFunction(register_new_odac)

def updateACF(force=False):
  rFile = open(r"%s/odac_update.txt" %OV.BaseDir())
  txt = rFile.read()
  rFile.close()
  if force:
    print "Update is forced"
  elif txt == "False":
    print "No update required"
    return
  print "Now Updating..."

  mac_address = OV.GetMacAddress()
  username, computer_name = OV.GetUserComputerName()
  keyname = getKey()
  olex2_tag = OV.GetTag()

  username = "updater"
  password = "update456R"
  institution = keyname.split("-")[0]
  type_of_key = keyname.split("-")[-1]

  for mac_address in OV.GetMacAddress():
    url = "http://www.olex2.org/odac/update"
    values = {'__ac_password':password,
              '__ac_name':username,
              'context':"None",
              'institution':institution,
              'olex2Tag':olex2_tag,
              'typeOfKey':type_of_key,
              'computerName':computer_name,
              'macAddress':mac_address
              }
    data = urllib.urlencode(values)
    print data
    try:
      req = urllib2.Request(url)
      response = urllib2.urlopen(req,data)
      f = response.read()
    except:
      print "\n++++++++++++++++++++++++++++++++++++++++++++++"
      print "+ Could not reach update server at www.olex2.org"
      print "+ --------------------------------------------"
      print "+ Please make sure your computer is online"
      print "+ and that you can reach www.olex2.org"
      print "++++++++++++++++++++++++++++++++++++++++++++++\n"
      return
    if f:
      break

  new = True

  if not f:
    print "Updating has failed, previous files will be used"
    return

  if new:
    p = "%s/Olex2u/OD/%s" %(os.environ['ALLUSERSPROFILE'], olex2_tag)
    cont = GetHttpFile(f, force=True, fullURL = True)
    try:
      if cont:
        name = "AutoChem Updater.exe"
        wFile = open("%s/%s" %(p, name),'wb')
        wFile.write(cont)
        wFile.close()
      cmd = r"%s/AutoChem Updater.exe /S" %p
      print cmd
      Popen(cmd, shell=False, stdout=PIPE).stdout
      print "Updated"
      wFile = open(r"%s/odac_update.txt" %OV.BaseDir(),'w')
      wFile.write("False")
      rFile.close()
    except Exception, err:
      print "Error with updating %s" %err
      print "Please check your file permissions"


  else:
    import pickle
    try:
      l = pickle.load(response)
      p = "%s/Olex2u/OD/%s" %(os.environ['ALLUSERSPROFILE'], olex2_tag)

      for f in l:
        f = f.replace(r'/var/distro/www/', 'olex-')
        cont = GetHttpFile(f, force=True)
        name = f.split(r'/')[-1]
        if cont:
          wFile = open("%s/%s" %(p, name),'wb')
          wFile.write(cont)
          wFile.close()
          print "Written %s/%s" %(p, name)
      wFile = open(r"%s/util/pyUtil/PluginLib/odac_update.txt" %OV.BaseDir(),'w')
      wFile.write("False")
      rFile.close()

      cmd = r"%s/AutoChem Installer.exe /S" %p
      Popen(cmd, shell=False, stdout=PIPE).stdout

      print "Updated"

    except Exception, err:
      print "Empty response: %s" %err
      print repr(response)

OV.registerFunction(updateACF)


def GetACF():
  global _is_online
  no_update = False
  print "Starting ODAC..."
  if no_update:
    _is_online = False
    print "Will not update ODAC Files"
  check_for_crypto()

  cont = None
  tag = OV.GetTag()
  if not tag:
    print "You need to update Olex2 to at least version 1.0"
    return

  if not OV.IsPluginInstalled('Headless'):
    olex.m("installplugin Headless")

  updateACF()
  use_new = True
  if use_new:
    debug = OV.FindValue('odac_fb', False)
    debug =  OV.GetParam('odac.debug.debug')
    OV.SetVar('odac_fb', debug)
    debug_deep1 = OV.GetParam('odac.debug.debug_deep1')
    debug_deep2 = OV.GetParam('odac.debug.debug_deep2')
    OV.SetVar("ac_verbose",  OV.GetParam('odac.debug.verbose'))

  else:
    debug = OV.FindValue('odac_fb', False)
    debug = [False, True][1]
    debug_deep1 = [False, True][1]
    debug_deep2 = [False, True][1]
    OV.SetVar("ac_verbose", [False, True][1])

  keyname = getKey()


  if not debug:
    p = "%s/Olex2u/OD/%s" %(os.environ['ALLUSERSPROFILE'], tag)
    OV.SetParam('odac.source_dir',p)
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
    p = r"%s/util/pyUtil/PluginLib/plugin-AutoChemSRC/%s" %(olx.BaseDir(), tag)
    sys.path.append(p)
    OV.SetParam('odac.source_dir',p)
    try:
      print "Debug: Import entry_ac"
      import entry_ac
    except Exception, err:
      print "Failed: %s" %err
      odac_loaded = False

  if OV.GetParam('odac.is_active'):
    print "AutoChem loaded OK"
  else:
    print "AutoChem could not be started"

OV.registerFunction(GetACF)


def runODAC(cmd):
  if OV.GetParam('odac.is_active'):
    cmd = cmd.rstrip(" -")
    cmd += " -s"
    OV.Cursor('Starting ODAC')
    res = olex.m(cmd)


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
            }
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

def makeSpecialCifCharacter(txt):
  txt = txt.replace(r"\a", r"&alpha;")
  txt = txt.replace(r"\A", r"&Alpha;")
  txt = txt.replace(r"\b", r"&beta;")
  txt = txt.replace(r"\B", r"&Beta;")
  txt = txt.replace(r"\c", r"&chi;")
  txt = txt.replace(r"\C", r"&Chi;")
  txt = txt.replace(r"\d", r"&Delta;")
  txt = txt.replace(r"\D", r"&delta;")
  txt = txt.replace(r"\e", r"&epsilon;")
  txt = txt.replace(r"\E", r"&Epsilon;")
  txt = txt.replace(r"\f", r"&phi;")
  txt = txt.replace(r"\F", r"&Phi;")
  txt = txt.replace(r"\g", r"&gamma;")
  txt = txt.replace(r"\G", r"&Gamma;")
  txt = txt.replace(r"\h", r"&eta;")
  txt = txt.replace(r"\H", r"&Eta;")

  txt = txt.replace(r"\k", r"&kappa;")
  txt = txt.replace(r"\K", r"&Kappa;")
  txt = txt.replace(r"\l", r"&lambda;")
  txt = txt.replace(r"\L", r"&Lambda;")
  txt = txt.replace(r"\m", r"&nu;")
  txt = txt.replace(r"\M", r"&Mu;")
  txt = txt.replace(r"\n", r"&nu;")
  txt = txt.replace(r"\N", r"&Nu;")
  txt = txt.replace(r"\o", r"&omicron;")
  txt = txt.replace(r"\O", r"&Omicron;")
  txt = txt.replace(r"\p", r"&phi;")
  txt = txt.replace(r"\P", r"&Phi;")
  txt = txt.replace(r"\q", r"&theta;")
  txt = txt.replace(r"\Q", r"&Theta;")
  txt = txt.replace(r"\r", r"&rho;")
  txt = txt.replace(r"\R", r"&Rho;")
  txt = txt.replace(r"\s", r"&sigma;")
  txt = txt.replace(r"\S", r"&Sigma;")
  txt = txt.replace(r"\t", r"&tau;")
  txt = txt.replace(r"\T", r"&Tau;")
  txt = txt.replace(r"\u", r"&upsilon;")
  txt = txt.replace(r"\U", r"&Upsilon;")
  txt = txt.replace(r"\w", r"&omega;")
  txt = txt.replace(r"\W", r"&Omega;")
  txt = txt.replace(r"\x", r"&chi;")
  txt = txt.replace(r"\X", r"&Chi;")
  txt = txt.replace(r"\y", r"&psi;")
  txt = txt.replace(r"\Y", r"&Psi;")
  txt = txt.replace(r"\z", r"&zeta;")
  txt = txt.replace(r"\Z", r"&Zeta;")
  
  return txt
OV.registerFunction(makeSpecialCifCharacter)


def getReportTitleSrc():
  import PIL
  import Image
  import ImageDraw
  import PngImagePlugin
  import StringIO
  import base64
  import EpsImagePlugin
  from ImageTools import ImageTools
  IT = ImageTools()
  
  width = OV.GetParam('gui.report.width')
  height = OV.GetParam('gui.report.title.height')
  colour = OV.GetParam('gui.report.title.colour').rgb
  font_name = OV.GetParam('gui.report.title.font_name')
  font_size = OV.GetParam('gui.report.title.font_size')
  font_colour = OV.GetParam('gui.report.title.font_colour')
  
  sNum = OV.GetParam('snum.report.title')
  
  IM = Image.new('RGBA', (width, height), colour)
  draw = ImageDraw.Draw(IM)
  IT.write_text_to_draw(draw,
                 sNum,
                 align='right',
                 max_width=width,
                 font_name=font_name,
                 font_size=font_size,
                 font_colour=font_colour)
  
  ## This bits would insert a logo into the header, but it doesn't look good.
  #imagePath = OV.GetParam('snum.report.image')
  #imagePath = "%s/etc/CIF/styles/logo.png" %OV.BaseDir()
  #im = Image.open(imagePath)
  #imHeight = height
  #oSize = im.size
  #nWidth = int(oSize[0]*(imHeight/oSize[1]))
  #im = im.resize((nWidth, imHeight), Image.BICUBIC)
  
  #IM.paste(im, (0,0), im)
  

  p = "%s/report_tmp.png" %OV.DataDir()
  IM.save(p, "PNG")
  
  rFile = open(p, 'rb').read()
  data = base64.b64encode(rFile)
  retVal ='data:image/png;base64,' + data
  return retVal
OV.registerFunction(getReportTitleSrc)

def getReportImageSrc():
  imagePath = OV.GetParam('snum.report.image')
  if OV.FilePath(imagePath) == OV.FilePath():
    return olx.file_GetName(imagePath)
  else:
    return 'file:///%s' %imagePath
OV.registerFunction(getReportImageSrc)

def getReportImageData(size='w400', imageName=None):
  import PIL
  import Image
  import PngImagePlugin
  import StringIO
  import base64
  import EpsImagePlugin

  size_type = size[:1]
  size = int(size[1:])
  if imageName is None:
    imagePath = OV.GetParam('snum.report.image')
  else:
    imagePath = r"%s/etc/CIF/styles/%s.png" %(OV.BaseDir(),imageName)
  imageLocalSrc = imagePath.split("/")[-1:][0]
  imageLocalSrc = imageLocalSrc.split("\\")[-1:][0]
    
   
  IM = Image.open(imagePath)
  oSize = IM.size
  if size_type == "w":
    if oSize[1] != size:
      nHeight = int(oSize[1]*(size/oSize[0]))
      nWidth = size
      IM = IM.resize((nWidth, nHeight), Image.BICUBIC)
  elif size_type == "h":
    if oSize[0] != size:
      nHeight = size
      nWidth = int(oSize[0]*(size/oSize[1]))
      IM = IM.resize((nWidth, nHeight), Image.BICUBIC)
  p = "%s/report_tmp.png" %OV.DataDir()
  IM.save(p, "PNG")
  
  rFile = open(p, 'rb').read()
  data = base64.b64encode(rFile)
  d ='data:image/png;base64,' + data
  
  html = '''
<!--[if IE]><img width=500 src='%s'><![endif]-->
<![if !IE]><img width=500 src='data:image/png;base64,%s'><![endif]>
  '''%(imageLocalSrc, data)
  
  return html
OV.registerFunction(getReportImageData)

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

def reset_file_in_OFS(fileName,txt=" ",copyToDisk = False):
  OV.reset_file_in_OFS(fileName=fileName, txt=txt, copyToDisk=copyToDisk)
OV.registerFunction(reset_file_in_OFS)

def GetCurrentSelection():
  return OV.GetCurrentSelection()
OV.registerFunction(GetCurrentSelection)

def getAllHelpBoxes():
  import glob
  import re
  boxes = []
  for htmfile in glob.glob("%s/etc/gui/*.htm" %OV.BaseDir()):
    rFile = open(htmfile,'r')
    f = rFile.read()
    rFile.close()

    ## find all occurances of strings between help_ext=..; . These should be comma separated things to highlight.
    regex = re.compile(r"help_ext= (.*?)  ;", re.X)
    l = regex.findall(f)
    if l:
      for item in l:
        boxes.append(item)
  return boxes

def test_help_boxes():
  import htmlTools
  boxes = getAllHelpBoxes()
  for box in boxes:
    htmlTools.make_help_box({'name':box})
OV.registerFunction(test_help_boxes)


if not haveGUI:
  def tbxs(name):
    print "This is not available in Headless Olex"
    return ""
  #OV.registerFunction(tbxs)
OV.registerFunction(OV.IsPluginInstalled)
OV.registerFunction(OV.GetTag)

