from __future__ import division

import olex
import olex_fs
import glob
import olx
import os
import time
import math
import olex_core
import sys
import programSettings
from subprocess import *

import htmlTools
import HttpTools

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
if haveGUI:
  import olex_gui

def txt():
  try:
    import uuid
    # This creates a custom unique filename determined by the the currently loaded in url
    output_file_name = "%s.txt"%uuid.uuid3(uuid.NAMESPACE_OID, '%s'%str(OV.FileFull()))
    # This is passed to the altered version of text creating the custom log instead of output.txt
    # Change:
    # &nbsp;$spy.MakeHoverButton(toolbar-text, 'Text') to
    # &nbsp;$spy.MakeHoverButton(toolbar-text, 'spy.txt\()')
    # in gui/blocks/snum-info.txt to make it default

    olx.Text(output_file_name)
  except ImportError, err:
    print "Could not initialise spy.txt() function: %s" %err
OV.registerFunction(txt)

def expand(start, finish, increment=1):
  """
  expand creates returns a list based on start, finish and increment
  So C1, C6 would produce:
  C1 C2 C3 C4 C5 C6
  """
  import string
  start_atom = str(start).translate(None, string.digits).lower()
  start_number = int(str(start).translate(None, string.ascii_letters))
  finish_atom = str(finish).translate(None, string.digits).lower()
  finish_number = int(str(finish).translate(None, string.ascii_letters))
  if (finish_atom != start_atom) or (start_number == finish_number):
    print "The start and end element types must be the same and the numbers different"
    return
  return_string = []
  for x in range(start_number, finish_number+1, int(increment)):
    return_string.append('%s%d'%(start_atom,x))
  return ' '.join(return_string)
OV.registerFunction(expand)

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
  restraint_types = {
    'dfix':'bond',
    'dang':'bond',
    'flat':'planarity',
    'chiv':'chirality',
    'sadi':'bond_similarity',
    'simu':'adp_similarity',
    'delu':'rigid_bond',
    'isor':'isotropic_adp',
    'olex2.restraint.angle':'angle',
    'olex2.restraint.dihedral':'dihedral',
    'olex2.restraint.adp_u_eq':'fixed_u_eq_adp',
    'olex2.restraint.adp_u_eq_similar':'adp_u_eq_similarity',
    'olex2.restraint.adp_volume_similar':'adp_volume_similarity',
  }

  constraint_types = {
    'eadp':'adp',
    'exyz':'site',
  }

  def __init__(self):
    olex_refinement_model = OV.GetRefinementModel(True)
    self._atoms = []
    self._fixed_variables = {}
    self.atom_ids = []
    asu = olex_refinement_model['aunit']
    for residue in asu['residues']:
      for atom in residue['atoms']:
        self._atoms.append(atom)
        element_type = atom['type']
        self.atom_ids.append(atom['aunit_id'])
    vars = olex_refinement_model['variables']['variables']
    if len(vars) > 0:
      for var in vars[0]['references']:
        self._fixed_variables.setdefault(var['id'], [])
        self._fixed_variables[var['id']].append(var)
    self._cell = olex_refinement_model['aunit']['cell']
    self.exptl = olex_refinement_model['exptl']
    self._afix = olex_refinement_model['afix']
    self.model= olex_refinement_model

  def atoms(self):
    return self._atoms

  def disorder_parts(self):
    return [atom['part'] for atom in self._atoms]

  def iterator(self):
    for i, atom in enumerate(self._atoms):
      name = str(atom['label'])
      element_type = str(atom['type'])
      xyz = atom['crd'][0]
      occu = atom['occu'][0]
      adp = atom.get('adp')
      if adp is None:
        uiso = atom.get('uiso')[0]
        u = (uiso,)
      else: u = adp[0]
      uiso_owner = atom.get('uisoOwner')
      if name[:1] != "Q":
        yield name, xyz, occu, u, uiso_owner, element_type, self._fixed_variables.get(i)

  def afix_iterator(self):
    for afix in self._afix:
      mn = afix['afix']
      m, n = divmod(mn, 10)
      pivot = afix['pivot']
      dependent = afix['dependent']
      pivot_neighbours = [
        i for i in self._atoms[pivot]['neighbours']
        if not i in dependent]
      if len(dependent) == 0: continue
      dependent_part = self._atoms[dependent[0]]['part']
      #pivot_neighbours = None
      bond_length = afix['d']
      uiso = afix['u']
      yield m, n, pivot, dependent, pivot_neighbours, bond_length

  def restraints_iterator(self, pair_sym_table=None):
    from libtbx.utils import flat_list
    from cctbx import sgtbx
    for shelxl_restraint in (self.restraint_types):
      for restraint in self.model.get(shelxl_restraint, ()):
        restraint_type = self.restraint_types.get(shelxl_restraint)
        if restraint_type is None: continue
        i_seqs = [i[0] for i in restraint['atoms']]
        kwds = dict(i_seqs=i_seqs)
        if restraint_type not in (
          'adp_similarity', 'adp_u_eq_similarity', 'adp_volume_similarity',
          'rigid_bond', 'isotropic_adp', 'fixed_u_eq_adp'):
          kwds['sym_ops'] = [
            (sgtbx.rt_mx(flat_list(i[1][:-1]), i[1][-1]) if i[1] is not None else None)
            for i in restraint['atoms']]
          if restraint_type in ('angle', 'dihedral'):
            esd_val = restraint['esd1']*180/math.pi
          else:
            esd_val = restraint['esd1']
          kwds['weight'] = 1/math.pow(esd_val,2)
        value = restraint['value']
        if restraint_type in ('adp_similarity', 'adp_u_eq_similarity',
                              'adp_volume_similarity',
                              'isotropic_adp', 'fixed_u_eq_adp'):
          kwds['sigma'] = restraint['esd1']
          if restraint_type in ('adp_similarity', 'isotropic_adp'):
            kwds['sigma_terminal'] = restraint['esd2'] if restraint['esd2'] != 0 else None
        elif restraint_type == 'rigid_bond':
          kwds['sigma_12'] = restraint['esd1']
          kwds['sigma_13'] = restraint['esd2'] if restraint['esd2'] != 0 else None
        if restraint_type == 'bond':
          kwds['distance_ideal'] = value
        elif restraint_type in ('angle', 'dihedral'):
          kwds['angle_ideal'] = value
        elif restraint_type in ('fixed_u_eq_adp',):
          kwds['u_eq_ideal'] = value
        elif restraint_type in ('bond_similarity', 'planarity'):
          kwds['weights'] = [kwds['weight']]*len(i_seqs)
          if restraint_type == 'bond_similarity':
            sym_ops = kwds['sym_ops']
            kwds['i_seqs'] = [[i_seq for i_seq in i_seqs[i*2:(i+1)*2]]
                                     for i in range(int(len(i_seqs)/2))]
            kwds['sym_ops'] = [[sym_op for sym_op in sym_ops[i*2:(i+1)*2]]
                                       for i in range(int(len(sym_ops)/2))]
        if restraint_type in ('adp_similarity', 'isotropic_adp', 'rigid_bond'):
          kwds['pair_sym_table'] = pair_sym_table
        if 'weights' in kwds:
          del kwds['weight']
        if restraint_type in ('bond', ):
          for i in range(int(len(i_seqs)/2)):
            yield restraint_type, dict(
              weight=kwds['weight'],
              distance_ideal=kwds['distance_ideal'],
              i_seqs=kwds['i_seqs'][i*2:(i+1)*2],
              sym_ops=kwds['sym_ops'][i*2:(i+1)*2])
        elif restraint_type in ('angle', ):
          for i in range(int(len(i_seqs)/3)):
            yield restraint_type, dict(
              weight=kwds['weight'],
              angle_ideal=kwds['angle_ideal'],
              i_seqs=kwds['i_seqs'][i*3:(i+1)*3],
              sym_ops=kwds['sym_ops'][i*3:(i+1)*3])
        elif restraint_type in ('dihedral', ):
          for i in range(int(len(i_seqs)/4)):
            yield restraint_type, dict(
              weight=kwds['weight'],
              angle_ideal=kwds['angle_ideal'],
              i_seqs=kwds['i_seqs'][i*4:(i+1)*4],
              sym_ops=kwds['sym_ops'][i*4:(i+1)*4])
        else:
          yield restraint_type, kwds

  def constraints_iterator(self):
    from libtbx.utils import flat_list
    from cctbx import sgtbx
    for shelxl_constraint in (self.constraint_types):
      for constraint in self.model[shelxl_constraint]:
        constraint_type = self.constraint_types.get(shelxl_constraint)
        if constraint_type is None: continue
        if constraint_type == "adp":
          i_seqs = [i[0] for i in constraint['atoms']]
          kwds = dict(i_seqs=i_seqs)
        else:
          kwds = {"i_seqs": constraint}
        yield constraint_type, kwds

  def getCell(self):
    return [self._cell[param][0] for param in ('a','b','c','alpha','beta','gamma')]

  def getCellErrors(self):
    return [self._cell[param][1] for param in ('a','b','c','alpha','beta','gamma')]

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
    cell_volume = float(olx.xf.au.GetVolume())
    expected_atoms = cell_volume/15
    present_atoms = self.number_non_hydrogen_atoms()
    expected_peaks = expected_atoms - present_atoms
    if expected_peaks < 5: expected_peaks = 5
    return int(expected_peaks)

  def getExpectedPeaks_and_AtomsPresent(self):
    cell_volume = float(olx.xf.au.GetVolume())
    expected_atoms = cell_volume/15
    present_atoms = self.number_non_hydrogen_atoms()
    expected_peaks = expected_atoms - present_atoms
    if expected_peaks < 5: expected_peaks = 5
    return int(expected_peaks), int(present_atoms)


def get_refine_ls_hydrogen_treatment():
  afixes_present = []
  afixes = {0:'refall',
            1:'noref',
            2:'refxyz',
            3:'constr',
            4:'constr',
            5:'constr',
            7:'constr',
            8:'constr',
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
  a = olx.file.Which('XS.exe')
  if a == "":
    a = olx.file.Which('ShelXS.exe')
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
  Z = float(olx.xf.au.GetZ())
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
  olx.xf.SetFormula(argStr)
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
  f = olx.xf.GetFormula('list')
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

def ElementButtonStates(symbol):
  if OV.GetParam('olex2.full_mode') == 'name -t=%s' %symbol:
    olex.m('mode off')
  else:
    if olex.f('Sel()') == '':
      olex.m('mode name -t=%s' %symbol)
    else:
      olex.m('name sel %s' %symbol)
      olex.m('sel -u')
if haveGUI:
  OV.registerFunction(ElementButtonStates)


def MakeElementButtonsFromFormula():
  global last_formula
  global last_elements_html

  current_formula = OlexRefinementModel().currentFormula()


  #if current_formula == last_formula:
    #return last_elements_html

  from PilTools import ButtonMaker
  icon_size = OV.GetParam('gui.skin.icon_size')
  totalcount = 0
  btn_dict = {}
  f = olx.xf.GetFormula('list')
  if not f:
    return
  f = f.split(',')

  Z_prime = float(olx.xf.au.GetZprime())
  Z = float(olx.xf.au.GetZ())
  html = ""
  for element in f:
    symbol = element.split(':')[0]
    max = float(element.split(':')[1])
    max = round(max, 2)
    present = round(current_formula.get(symbol,0),2)
    if symbol != "H":
      totalcount += max

    max = max*Z_prime
    c = ""
    if present < max:
      bgcolour = (250,250,250)
      c = 'b'
    elif present ==  max:
      bgcolour = (210,255,210)
      c = 'g'
    else:
      bgcolour = (255,210,210)
      c = 'r'

    if c:
      name = "btn-element%s_%s" %(symbol, c)

    else:
      name = "btn-element%s" %(symbol)

    command = "if strcmp(sel(),'') then 'mode name -t=%s' else 'name sel %s'>>sel -u" %(symbol, symbol)
    target = OV.TranslatePhrase('change_element-target')
    #command = "if strcmp(spy.GetParam(olex2.in_mode),'mode name -t=%s') then 'mode off' else %%22 if strcmp(sel(),'') then 'mode name -t=%s' else 'name sel %s'>>sel -u%%22" %(symbol, symbol, symbol)
    command = 'spy.ElementButtonStates(%s)' %symbol
    namelower = 'btn-element%s' %(symbol)
    d = {}
    d.setdefault('namelower', name)
    d.setdefault('symbol', symbol)
    d.setdefault('cmds', command)
    d.setdefault('target', target + symbol)
    d.setdefault('bgcolor', OV.GetParam('gui.html.table_firstcol_colour'))
    html += '''
<input
  name=IMG_BTN-ELEMENT%(symbol)s
  type="button"
  image="up=%(namelower)soff.png,down=%(namelower)son.png,hover=%(namelower)shover.png",disable=%(namelower)sdisable.png"
  hint="%(target)s"
  onclick="%(cmds)s"
  bgcolor=%(bgcolor)s
>
''' %d


  d['namelower'] = 'Table'
  html +=  '''
<input
  name=IMG_BTN-ELEMENT...
  type="button"
  image="up=%(namelower)soff.png,down=%(namelower)son.png,hover=%(namelower)shover.png",disable=%(namelower)sdisable.png"
  hint="Chose Element from the periodic table"
  onclick="if strcmp(sel(),'') then 'mode name -t=ChooseElement()' else 'name sel ChooseElement()'"
  bgcolor=%(bgcolor)s
>
''' %d


  if current_formula != last_formula:
    last_formula = current_formula

  OV.write_to_olex('element_buttons.htm', html, 0)

  im_name='IMG_BTN-ELEMENT%s' %symbol
  OV.SetImage(im_name, name)

  SetAtomicVolumeInSnumPhil(totalcount)

if haveGUI:
  OV.registerFunction(MakeElementButtonsFromFormula)

def SetAtomicVolumeInSnumPhil(totalcount):
  cell_volume = 0
  Z = 1
  Z_prime = float(olx.xf.au.GetZprime())
  try:
    cell_volume = float(olx.xf.au.GetCellVolume())
  except:
    pass
  try:
    Z = float(olx.xf.au.GetZ())
  except:
    pass

  if cell_volume and totalcount:
    atomic_volume = (cell_volume)/(totalcount * Z)
    OV.SetParam('snum.solution.current_atomic_volume','%.1f' %atomic_volume)
  else:
    OV.SetParam('snum.solution.current_atomic_volume',None)

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

def GetHklFileList():
  reflection_file_extensions = ["hkl", "hkp", "raw", 'hklf5', 'hkc']
  g = OV.ListFiles(OV.FilePath(), ';'.join(reflection_file_extensions))
  g.sort()
  try:
    a = OV.HKLSrc().replace('\\', '/')
    if a[0] == "'" or a[0] == '"':
      a = a[1:-1]
  except:
    a = ""

  if not os.path.isfile(a) and not g:
    print "There is no reflection file or the reflection file is not accessible"
  reflection_files = ""
  for item in g:
    reflection_files+="%s.%s<-%s;" %(OV.FileName(item), OV.FileExt(item), item)
  return reflection_files
if haveGUI:
  OV.registerFunction(GetHklFileList)

def tbxs_(name):
  retVal = ""
  txt = r'''
<!-- #include header gui\blocks\tool-header.htm;1; -->
<table border="0" style="border-collapse: collapse" width="100%" id="#tool" cellpadding="0" cellspacing="1">
        <tr>
                <td width="100%" bgcolor="$GetVar(HtmlFontColour">
                        <-zimg border="0" src="#image.png">
                </td>
        </tr>
</table>
<table border="0" VALIGN='center' style="border-collapse: collapse" width="100%" cellpadding="1" cellspacing="1" bgcolor="$GetVar(HtmlTableBgColour)">
'''

  txt += r'''
<tr VALIGN='center' NAME='Expand Short Contacts'>
  <td colspan=1 width="8" bgcolor="$GetVar(HtmlTableFirstcolColour)"></td>
    <td>
      <font size = '4'>
        <b>
          %%setup-title-%s%%
        </b>
      </font>
    </td>
  </tr>
<tr>
  <td valign='top' width="8" bgcolor="$GetVar(HtmlTableFirstcolColour)"><zimg border="0" src="info.png"></td>
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

def GetRInfo(txt="",format='html'):
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
    if OV.HasGUI():
      font_size = OV.GetParam('gui.html.font_size_large')
    else:
      font_size = 14

    if 'html' in format:
      try:
        R1 = float(R1)
        col = GetRcolour(R1)
        R1 = "%.2f" %(R1*100)

        if 'report' in format:
          t = r"<font size='%s'>R1 = <font color='%s'><b>%s%%</b></font></font>" %(font_size, col, R1)
        else:
          t = r"<font size='%s'>R1 = <font color='%s'><b>%s%%</b></font></font>" %(font_size, col, R1)

      except:
        t = "<td colspan='2' align='right' rowspan='2' align='right'><font size='%s'><b>%s</b></font></td>" %(font_size, R1)
      finally:
        return t

    elif format == 'float':
      try:
        t = float(R1)
      except:
        t = 0
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
      if OV.HasGUI():
        retVal=OV.GetParam('gui.red')
      else:
        retVal="#b40000"
    elif R1 >0.10:
      if OV.HasGUI():
        retVal=OV.GetParam('gui.orange')
      else:
        retVal="#ff8f00"
    else:
      if OV.HasGUI():
        retVal=OV.GetParam('gui.green')
      else:
        retVal = "#00b400"

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
        state = olx.html.GetItemState(item[1])
      if state == '-1':
        state = "off"
      elif state == '0':
        state = "on"
      #OV.CopyVFSFile("cbtn-%s2%s.png" %(item[0],state),"cbtn-%s2.png" %item[0])
      OV.SetImage("IMG_CBTN-%s2" %btn.upper(),"cbtn-%s2%s.png" %(item[0], state))
      OV.SetImage("IMG_BTN-%s2" %btn.upper(),"btn-%s2%s.png" %(item[0], state))
      OV.SetVar('gui_MainToolbarTabButtonActive',btn)
    elif state != 'inactive' and not isCif:
      OV.CopyVFSFile("cbtn-%s2off.png" %item[0],"cbtn-%s2.png" %item[0])
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
      if olx.html.IsItem(item[1]) == 'true':
        olx.html.ItemState(item[1],'-1')
    else:
      state = ''
      #state = 'off'
    if not state:
      #if OV.IsControl(item[1]):
      if olx.html.IsItem(item[1]) == 'true':
        try:
          state = olx.html.GetItemState(item[1])
        except RuntimeError:
          pass
        if state == '-1':
          state = "off"
        elif state == '0':
          state = "on"
        elif state == '1':
          state = "off"
      else:
        state = 'off'
    try:
      OV.CopyVFSFile("cbtn-%s%s.png" %(btn,state),"cbtn-%s.png" %btn)
    except:
      olex.m('skin default_new')
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
  OV.SetParam("%s.refinement.program" %scope, prg_name)
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
    OV.SetParam('%s.solution.method' %scope, 'Auto')
    #olx.SetValue('SET_autochem_solution_METHOD', 'Auto')
    return

  if prg_name != 'Unknown':
    prg = SPD.programs[prg_name]
    if method is None or not method:
      method = sortDefaultMethod(prg)
      if method == 'Direct Methods' and olx.Ins('PATT') != 'n/a':
        method = 'Patterson Method' # work-around for bug #48
    OV.SetParam("%s.solution.program" %scope, prg_name)
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
  if prg == '?' or prg == 'Unknown': return retval
  if prg == 'Auto':
    OV.SetParam("%s.solution.method" %scope,'Auto')
    return 'Auto'
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
  if "olex2" in prg.name.lower():
    return True
  if prg.name in SPD or prg.name in RPD:
    exec_l = prg.execs
  else:
    exec_l = ["%s.exe" %prg, "%s" %prg, "%s" %prg.lower()]
  for item in exec_l:
    a = olx.file.Which('%s' %item)
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
  if prg == '?' or prg == 'Unknown': return retval
  if prg == 'Auto':
    OV.SetParam("%s.refinement.method" %scope,'Auto')
    return 'Auto'
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
  res = OV.olex_function('sel()')
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


def getKeys(key_directory):
  kl = []
  import glob
  g = glob.glob(r"%s/*.%s" %(key_directory, "priv"))
  for item in g:
    keyname = item.split("\\")[-1:][0]
    kl.append(keyname.split(".")[0])
  return kl

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
  OV.StoreParameter('last_version')
  return retVal

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
            'context':"None",
            'macAddress':mac_address,
            }
  try:
    f = HttpTools.make_url_call(url, values)
  except Exception, err:
    print "You may have exceeded the number of AutoChem installs."
    print "Please contact contact xrdapplications@agilent.com for further information."
    return

  f = f.read()

  if not f:
    print "Please provide a valid username and password, and make sure your computer is online."
    print "You may also have used up the number of allowable installs."
    return

  elif not f.endswith(".exe"):
    print "Please provide valid username and password. If this problem persitsts, please"
    print "contact xrdapplications@agilent.com for further information."
    return


  p = "%s/Olex2u/OD/%s" %(os.environ['ALLUSERSPROFILE'], olex2_tag)
  p = os.path.abspath(p)
  if not os.path.exists(p):
    os.makedirs(p)
  else:
    try:
      import shutil
      shutil.rmtree(p)
      os.makedirs(p)
    except Exception, err:
      print "The installer could not delete this folder: %s" %p
      print "Please remove all files in this folder manually and run the installer again."
      olex.m('exec -o explorer "%s"' %p)
      return


  cont = GetHttpFile(f, force=True, fullURL = True)
  if cont:
    name = "AutoChem Installer.exe"
    wFile = open("%s/%s" %(p, name),'wb')
    wFile.write(cont)
    wFile.close()
  else:
    print "Could not get %s" %f
    return
  ins = "%s/AutoChem Installer.exe" %p
  cmd = r"%s /S" %ins
#  print cmd
  olx.Shell(ins)
#  Popen(cmd, shell=True, stdout=PIPE).stdout
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


def settings_tree():
  l = []
  added = []
  handlers = [olx.phil_handler, olx.gui_phil_handler]
  for handler in handlers:
    raw_l = handler.get_root_scope_names()
    for item in raw_l:
      s = handler.get_scope_by_name(item)
      if item not in added:
        l.append("%s (%s)\n%s\n" %(item, s.short_caption, item))
        added.append(item)
      for tem in s.objects:
        if tem.is_scope:
          l.append("\t%s (%s)\n%s.%s\n" %(tem.name, tem.short_caption, item, tem.name))
          for em in tem.objects:
            if em.is_scope:
              l.append("\t\t%s (%s)\n%s.%s.%s\n" %(em.name, em.short_caption, item, tem.name, em.name))
              for m in em.objects:
                if m.is_scope:
                  l.append("\t\t\t%s (%s)\n%s.%s.%s.%s\n" %(m.name, m.short_caption, item, tem.name, em.name, m.name))
                  for m1 in m.objects:
                    if m1.is_scope:
                      l.append("\t\t\t\t%s (%s)\n%s.%s.%s.%s.%s\n" %(m1.name, m1.short_caption, item, tem.name, em.name, m.name, m1.name))


  OV.write_to_olex('settings_tree.ind', ''.join(l))
OV.registerFunction(settings_tree)


def GetOptionalHyphenString(txt):
  txt = txt.replace ("/", "/" + u"\u200B")
  txt = txt.replace ("\\", "\\" + u"\u200B")
  txt = txt.replace ("\\", "\\" + " ")
  return txt
OV.registerFunction(GetOptionalHyphenString)

def GetTwinLaw(html=False):
  olex_refinement_model = OV.GetRefinementModel(False)
  if olex_refinement_model.has_key('twin'):
    c = olex_refinement_model['twin']['matrix']
    curr_law = []
    for row in c:
      for el in row:
        curr_law.append(el)
    curr_law = tuple(curr_law)
  else:
    return

  txt = repr(curr_law)
  if html:
    txt = "<tr><td colspan='4'><b><font color='%s'>TWIN LAW %s</font></b></td></tr>" %(OV.GetParam('gui.red').hexadecimal, repr(curr_law))
  return txt
OV.registerFunction(GetTwinLaw)


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
  plugins = {
            }
  s = "<hr>"
  green = OV.GetParam('gui.green')
  red = OV.GetParam('gui.red')
  for plugin in plugins:
    display = plugins[plugin].get('display', plugin)
    blurb = plugins[plugin].get('blurb', plugin)
    if olx.IsPluginInstalled("%s" %plugin) == 'true':
      s += "<font size='+1'><b>%s</b></font> <a href='spy.install_plugin %s>>html.Update setup-box'><font size='+1' color=%s>Uninstall</font></a><br>%s<br><br>" %(display, plugin, green, blurb)
    else:
      s += "<font size='+1'><b>%s</b></font> <a href='spy.install_plugin %s>>html.Update setup-box'><font size='+1' color=%s>Install</font></a><br>%s<br><br>" %(display, plugin, red, blurb)
  return s
OV.registerFunction(AvailablePlugins)

def AvailableSkins():
  skins = {'OD':{'display':'Oxford Diffraction Skin'}, 'HP':{'display':'Grey'}, 'default':{'display':'Default'}}
  s = "<hr>"
  for skin in skins:

    if OV.FindValue('gui_skin_name') == skin:
      s += "<a href='skin %s>>html.Update setup-box'><b>%s</b></a><br>" %(skin, skins[skin].get('display', skin))
    else:
      s += "<a href='skin %s>>html.Update setup-box'>%s</a><br>" %(skin, skins[skin].get('display', skin))
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
  rFile.close()
  retVal ='data:image/png;base64,' + data
  return retVal
OV.registerFunction(getReportTitleSrc)

def dealWithReportImage():
  #OV.GetParam('snum.re
  image_name = OV.GetParam('snum.report.image')
  if image_name == "No Image":
#    OV.SetParam('snum.report.image',None)
    return
  elif image_name == "screenshot":
    olex.m('showq false')
    olex.m('pict -pq screenshot.png 1')
    OV.SetParam('snum.report.image',"%s\screenshot.png" %OV.FilePath())
OV.registerFunction(dealWithReportImage)

def dealWithReportName():
  report_name = OV.GetParam('snum.report.name')
  if not report_name:
    OV.SetParam('snum.report.name',OV.FileName())
    return
OV.registerFunction(dealWithReportName)

def getReportImageSrc():
  imagePath = OV.GetParam('snum.report.image')
  if OV.FilePath(imagePath) == OV.FilePath():
    return olx.file.GetName(imagePath)
  else:
    return 'file:///%s' %imagePath
OV.registerFunction(getReportImageSrc)

def getReportExtraCIFItems(name_td_class, value_td_class, type='html'):
  cf_name = OV.file_ChangeExt(OV.FileFull(), 'cif')
  rv = ''
  if not os.path.exists(cf_name):
    return rv
  try:
    import iotbx
    fo = file(cf_name, "rUb")
    reader = iotbx.cif.reader(file_object=fo)
    fo.close()
    models = []
    for k, v in reader.model().iteritems():
      if k.lower() != 'global':
        models.append(v)
    if len(models) > 1:
      return rv
    flack = models[0]["_refine_ls_abs_structure_Flack"]
    if flack:
      if type == 'html':
        rv = "<tr><td class='%s'>Flack parameter</td><td class='%s'>%s</td></tr>"\
          %(name_td_class,value_td_class,flack)
      else:
        rv = r"Flack parameter & %s\\" % flack.replace('-', '@@-@@')

  except Exception, err:
    print err
    pass
  return rv
OV.registerFunction(getReportExtraCIFItems)

def get_text_from_vfs(item):
  return OV.get_txt_from_vfs(item)
OV.registerFunction(get_text_from_vfs)

def getReportPhilItem(philItem=None):
  item = OV.GetParam(philItem)
  if not item:
    philItemU = philItem.replace('snum', 'user')
    item = OV.GetParam(philItemU)
    if item:
      OV.SetParam(philItem, item)
  return item
OV.registerFunction(getReportPhilItem)

def getReportImageData(size='w400', imageName=None):

  import PIL
  import Image
  import PngImagePlugin
  import StringIO
  import base64
  import ImageDraw
  import EpsImagePlugin
  make_border = False

  size_type = size[:1]
  size = int(size[1:])

  if imageName is None:
    imageName = 'snum.report.image'
    make_border = OV.GetParam('snum.report.image_border')
    if not OV.HasGUI():
      return "No Image available in Headless Mode! <img width=0 src=''>"

  if "snum.report" in imageName:
    imagePath = OV.GetParam(imageName)

    if not imagePath:
      imageNameU = imageName.replace('snum', 'user')
      imagePath = OV.GetParam(imageNameU)
      if imagePath:
        OV.SetParam(imageName, imagePath)

  if imagePath == "No Image" or imagePath is None:
    return ""
  if type(imagePath) == unicode:
    imagePaths = []
    imagePaths.append(imagePath)
  else:
    imagePaths = imagePath
  html = ""
  i = 0
  for imagePath in imagePaths:
    i += 1
    if imagePath.startswith(r'BaseDir()'):
      imagePath = "%s/%s" %(OV.BaseDir(), imagePath.lstrip('BaseDir()'))
    if not os.path.exists(imagePath):
      OV.SetParam(imageName, None)
  #    print "The previously made screenshot has been removed. Please select 'screenshot' to make a new one"
      return
  #  else:
  #    imagePath = r"%s/etc/CIF/styles/%s.png" %(OV.BaseDir(),imageName)
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

    if make_border:
      from ImageTools import ImageTools
      IT = ImageTools()
      draw = ImageDraw.Draw(IM)
      fill = '#ababab'
      width, height = IM.size
      for i in xrange(make_border):
        draw.line((i,i,width-1-i,i), fill = fill)
        draw.line((i,height -1-i,width-1-i,height -1-i), fill = fill)
        draw.line((i,i,i,height - 1-i), fill = fill)
        draw.line((width -1-i,i,width-1-i,height -1-i), fill = fill)
#      weight = make_border
#      draw.line((0, int(weight/2)) + (IM.size[0], int(weight/2)), fill=fill, width=weight)
#      draw.line((0, 0) + (0, IM.size[1]), fill=fill, width=weight)
#      draw.line((IM.size[0] - weight, 0) + (IM.size[0] - weight, IM.size[1] - weight), fill=fill, width=weight)
#      draw.line((0, IM.size[1] - weight ) + (IM.size[0] - weight, IM.size[1] - weight) , fill=fill, width=weight)
#      del draw

    p = "%s/report_tmp_%i.png" %(OV.DataDir(), i)
    IM.save(p, "PNG")

    rFile = open(p, 'rb')
    img = rFile.read()
    data = base64.b64encode(img)
    d ='data:image/png;base64,' + data

    html += '''
  <!--[if IE]><img width=%s src='%s'><![endif]-->
  <![if !IE]><img width=%s src='data:image/png;base64,%s'><![endif]>
    '''%(int(size/2), imageLocalSrc, int(size/2), data)

  return html
OV.registerFunction(getReportImageData)


def getFileContents(p):
  if "snum.report" in p:
    p = OV.GetParam(p)
  if not p:
    return
  if not os.path.exists(p):
    return "%s does not exist" %p
  return open(p, 'rb').read()
OV.registerFunction(getFileContents)


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
  for htmfile in OV.ListFiles("%s/etc/gui/*.htm" %OV.BaseDir()):
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

def olex_fs_copy(src_file, dst_file):
  txt = olex_fs.ReadFile(src_file)
  olex_fs.NewFile(dst_file,txt)
OV.registerFunction(olex_fs_copy)

def isPro():
  p = "%s/pro.txt" %OV.BaseDir()
  if os.path.exists(p):
    OV.SetParam('olex2.hover_buttons',True)
    return True
  else:
    return False
OV.registerFunction(isPro)

def switch_tab_for_tutorials(tabname):
  olex.m("html.ItemState index* 0")
  olex.m("html.ItemState logo 0")
  olex.m("html.ItemState index-%s 1" %tabname)
  olex.m("html.ItemState info-title 1")
  if tabname.lower() == "work":
    olex.m("html.ItemState solve-settings 2")
    olex.m("html.ItemState refine-settings 2")
    olex.m("html.ItemState report-settings 2")
    olex.m("html.ItemState %s-toolbox 1" %tabname)
  olex.m("html.ItemState tab* 2")
OV.registerFunction(switch_tab_for_tutorials)

def revert_to_original():
  extensions = ['res','ins','cif']
  for extension in extensions:
    path = "%s/.olex/originals/%s.%s" %(OV.FilePath(), OV.FileName(), extension)
    if os.path.exists(path):
      rFile = open(path,'rb')
      txt = rFile.read()
      rFile.close()
      outpath = OV.file_ChangeExt(OV.FileFull(),'ins')
      wFile = open(outpath,'wb')
      wFile.write(txt)
      wFile.close()
      OV.AtReap(outpath)
      print("Reverted to the original file %s" %path)
      if OV.HasGUI():
        olx.html.Update()
      return
  print("Could not revert to any original file!")
OV.registerFunction(revert_to_original)

def fade_in(speed=0):
  speed = OV.GetParam('user.use_fader')
  if speed == 0:
    return
  olex.m("fade 1 0 -%s" %speed)
  olex.m('waitfor fade')
  olex.m("ceiling off")
OV.registerFunction(fade_in)

def fade_out(speed=0):
  speed = OV.GetParam('user.use_fader')
  if speed == 0:
    return
  olex.m("fader.InitFG()")
  olex.m("fader.visible(true)")
  olex.m("fade 0 1 %s" %speed)
  olex.m("waitfor fade")
OV.registerFunction(fade_out)

def GetImageFilename(image_type):
  filename = OV.GetParam('snum.image.%s.name' %image_type.lower())
  if image_type == "PS":
    fileext = "eps"
  elif image_type == "PR":
    fileext = "pov"
  else:
    fileext = OV.GetParam('snum.image.%s.type' %image_type.lower())
  if not filename:
    try:
      filename = OV.GetValue('IMAGE_%s_NAME' % image_type)
    except:
      filename = None
    if not filename:
      import gui
      filename = gui.FileSave("Choose Filename", "*.%s" %fileext, OV.FilePath())
    if not filename:
      return None, None, None
  if filename.endswith(".%s" %fileext):
    filefull = "'%s'" %filename
  else:
    filefull = "'%s.%s'" %(filename, fileext)
  OV.SetParam('snum.image.%s.name' %image_type.lower(),None)
  return filefull, filename, fileext

def StringsAreEqual(str1, str2):
  if str1 == str2:
    return True
  else:
    return False
OV.registerFunction(StringsAreEqual)

def StringsAreNotEqual(str1, str2):
  if str1 == str2:
    return False
  else:
    return True
OV.registerFunction(StringsAreNotEqual)


def GetBitmapImageInstructions():
  filefull, filename, fileext = GetImageFilename(image_type = "BITMAP")
  if not filefull:
    return
  filesize = OV.GetValue('IMAGE_BITMAP_SIZE')

  OV.Cursor('busy','Please Wait. Making image %s.%s. This may take some time' %(filename, fileext))
  olex.m('pict -pq %s %s' %(filefull, filesize))
  OV.Cursor()
OV.registerFunction(GetBitmapImageInstructions)

def GetPRImageInstructions():
  filefull, filename, fileext = GetImageFilename(image_type = "PR")
  if not filefull:
    return
  OV.Cursor('busy','Please Wait. Making image %s.%s. This may take some time' %(filename, fileext))
  olex.m('pictPR %s' %filefull)
  print 'Image %s created' %filefull
  OV.Cursor()
OV.registerFunction(GetPRImageInstructions)

def GetPSImageInstructions():
  filefull, filename, fileext = GetImageFilename(image_type = "PS")
  if not filefull:
    return
  OV.Cursor('busy','Please Wait. Making image %s.%s. This may take some time' %(filename, fileext))
  olex.m('brad %s' %OV.GetParam('snum.image.ps.bond_width'))

  colour_line = OV.GetParam('snum.image.ps.colour_line')
  colour_bond = OV.GetParam('snum.image.ps.colour_bond')
  colour_fill = OV.GetParam('snum.image.ps.colour_fill')
  image_perspective = OV.GetParam('snum.image.ps.perspective')
  lw_ellipse = str(OV.GetParam('snum.image.ps.outline_width'))
  lw_octant = str(OV.GetParam('snum.image.ps.octant_width'))
  lw_pie = str(OV.GetParam('snum.image.ps.pie_width'))
  lw_font = str(OV.GetParam('snum.image.ps.font_weight'))
  div_pie = str(OV.GetParam('snum.image.ps.octant_count'))
  scale_hb = str(OV.GetParam('snum.image.ps.h_bond_width'))

  olex.m("pictps" + \
         " " + filefull + \
         " " + colour_line + \
         " " + colour_bond + \
         " " + colour_fill + \
         " " + "-lw_ellipse=" + lw_ellipse + \
         " " + "-lw_octant=" + lw_octant + \
         " " + "-lw_pie=" + lw_pie + \
         " " + "-lw_font=" + lw_font + \
         " " + "-div_pie=" + div_pie + \
         " " + "-scale_hb=" + scale_hb)
  olex.m('brad 0.8')
  print 'Image %s created' %filefull
  OV.Cursor()
OV.registerFunction(GetPSImageInstructions)


def check_for_selection(need_selection=True):
  res = haveSelection()
  if not res and need_selection:
    print "\n++ This action requires a selection of atoms!"
    return False
  else:
    return True
OV.registerFunction(check_for_selection)

def round_to_n_digits(f, n=2):
  n = int(n)
  if len(f) < n:
    return f
  try:
    f = float(f)
    return "%.*f" %(n,f)
  except:
    return f
OV.registerFunction(round_to_n_digits)

def standardise_path(path):
  return OV.standardizePath(path)
OV.registerFunction(standardise_path)

def play_crystal_images():
  import time
  l = OV.GetParam('snum.metacif.list_crystal_images_files')[0].split(';')
  for image in l:
    if os.path.exists(image):
      OV.SetParam('snum.report.crystal_image',OV.standardizePath(image))
      olx.html.SetImage('CRYSTAL_IMAGE',image)
      OV.Refresh()
OV.registerFunction(play_crystal_images)


def advance_crystal_image(direction='forward'):
  l = OV.GetParam('snum.metacif.list_crystal_images_files')[0].split(';')
  i = 0
  for image in l:
    i += 1
    if image == OV.GetParam('snum.report.crystal_image'):
      if direction == 'forward':
        if i != len(l):
          p = l[i]
          OV.SetParam('snum.report.crystal_image',p)
          olx.html.SetImage('CRYSTAL_IMAGE',p)
          return
        else:
          print "Last image of the series!"
          return
      else:
        if i != 1:
          p = l[i-2]
          OV.SetParam('snum.report.crystal_image',p)
          olx.html.SetImage('CRYSTAL_IMAGE',p)
          return
        else:
          print "First image of the series!"
          return
    else:
      continue

  #p = OV.GetParam('snum.report.crystal_image')
  #n = int(p.split('\\')[-1].split(OV.FileName())[1].split('.')[0])
  #if direction == 'forward':
    #n += 1
  #else:
    #n -= 1
  #base = ("\\").join(p.split('\\')[:-1])
  #p = r"%s\%s%i%s" %(base, OV.FileName(), n, ".jpg")
  #if os.path.exists(p):
    #OV.SetParam('snum.report.crystal_image',p)
    #olx.html.SetImage('CRYSTAL_IMAGE',p)
OV.registerFunction(advance_crystal_image)

def getCellHTML():
  crystal_systems = {
    'Triclinic':('a', 'b', 'c', '&alpha;', '&beta;', '&gamma;'),
    'Monoclinic':('a', 'b', 'c', '&beta;'),
    'Orthorhombic':('a', 'b', 'c'),
    'Tetragonal':('a', 'c',),
    'Hexagonal':('a', 'c'),
    'Trigonal':('a', 'c'),
    'Cubic':('a',),
  }

  cell_param_value_pairs = dict(zip(
    ('a', 'b', 'c', '&alpha;', '&beta;', '&gamma;'),
    ('_cell_length_a','_cell_length_b','_cell_length_c','_cell_angle_alpha','_cell_angle_beta','_cell_angle_gamma')))
  cell = {}
  for param, value in cell_param_value_pairs.items():
    if param in ('a','b','c'):
      cell[param] = dict(
        value = '%%%s%%' %value,
        unit = '&nbsp;&Aring;'
      )
    else:
      cell[param] = dict(
        value = '%%%s%%' %value,
        unit = '&deg;'
      )

  cell_html = dict((param, '<i>%s</i>&nbsp;= %s%s, ' %(param,cell[param]['value'],cell[param]['unit'])) for param in cell.keys())

  crystal_system = OV.olex_function('sg(%s)')

  html = ''.join(cell_html[param] for param in crystal_systems[crystal_system])

  return html
OV.registerFunction(getCellHTML)



def formatted_date_from_timestamp(dte):
  if "." in dte:
    dte = OV.GetParam(dte)
  from datetime import date
  if not dte:
    return None
  try:
    dte = float(dte)
  except:
    return "Not A Date"
  dte = date.fromtimestamp(dte)
  return dte.strftime(OV.GetParam('snum.report.date_format'))
OV.registerFunction(formatted_date_from_timestamp)


def get_news_image_from_server(name=""):
  from ImageTools import ImageTools
  IT = ImageTools()
  if not name:
    url = 'http://www.olex2.org/randomimg'
  else:
    url = 'http://www.olex2.org/olex2images/%s/image' %name
  try:
    image = HttpTools.make_url_call(url,'').read()
  except Exception, err:
    print "Downloading image from %s has failed: %s" %(url, err)
    return
  if image:
    tag = OV.GetTag().split('-')[0]
    wFile = open('%s/etc/news/news-%s.png' %(OV.BaseDir(), tag),'wb')
    wFile.write(image)
    wFile.close()
    IT.resize_news_image()
OV.registerFunction(get_news_image_from_server)


if not haveGUI:
  def tbxs(name):
    print "This is not available in Headless Olex"
    return ""
  #OV.registerFunction(tbxs)
OV.registerFunction(OV.IsPluginInstalled)
OV.registerFunction(OV.GetTag)

#
def GetHttpFile(f, force=False, fullURL = False):
  URL = "http://dimas.dur.ac.uk/"
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
      response = HttpTools.make_url_call(url,"")
      content = response.read()
      if verbose: print "OK"
      retVal = content
    except Exception, err:
      _is_online = False
      retVal = None
      print "Olex2 can not reach the update server: %s" %err
      print url
  else:
    retVal = None
  return retVal