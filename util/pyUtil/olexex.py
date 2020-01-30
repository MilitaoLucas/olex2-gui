from __future__ import division

import olex
import olex_fs
import glob
import olx
import os
import time
import math
import re
import olex_core
import sys
import programSettings
from subprocess import *
import gui

import htmlTools
import HttpTools

global _is_online
_is_online = False

sys.path.append(r".\src")
import History

import ExternalPrgParameters
SPD, RPD = ExternalPrgParameters.get_program_dictionaries()

from olexFunctions import OlexFunctions
OV = OlexFunctions()
import variableFunctions

import MakeMovie

import OlexVFS
import threads_imp as olxth

global cache
cache = {}

haveGUI = OV.HasGUI()
if haveGUI:
  import olex_gui

import Report
import random


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
    'rigu':'rigu',
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
      anharmonic_adp = atom.get('anharmonic_adp')
      if adp is None:
        uiso = atom.get('uiso')[0]
        u = (uiso,)
      else: u = adp[0]
      uiso_owner = atom.get('uisoOwner')
      if name[:1] != "Q":
        yield name, xyz, occu, u, anharmonic_adp, uiso_owner, element_type, self._fixed_variables.get(i)

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
    for shelxl_restraint in self.restraint_types:
      for restraint in self.model.get(shelxl_restraint, ()):
        restraint_type = self.restraint_types.get(shelxl_restraint)
        if restraint_type is None: continue

        if restraint_type == 'rigu':
          # removed isotropic atoms from RIGU restraint
          i_seqs = []
          for atom_restraint in restraint['atoms']:
            for residue in self.model['aunit']['residues']:
              for atom in residue['atoms']:
                if(atom['aunit_id']==atom_restraint[0]):
                  if 'adp' in atom:
                    i_seqs.append(atom_restraint[0])
                  break
          if(len(i_seqs)==0):
            continue
        else:
          i_seqs = [i[0] for i in restraint['atoms']]

        kwds = dict(i_seqs=i_seqs)
        if restraint_type not in (
          'adp_similarity', 'adp_u_eq_similarity', 'adp_volume_similarity',
          'rigid_bond', 'rigu', 'isotropic_adp', 'fixed_u_eq_adp'):
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
        elif restraint_type == 'rigu':
          kwds['sigma_12'] = restraint['esd1']
          kwds['sigma_13'] = restraint['esd2'] if restraint['esd2'] != 0 else None
        if restraint_type == 'bond':
          kwds['distance_ideal'] = value
        elif restraint_type in ('angle', 'dihedral'):
          kwds['angle_ideal'] = value
        elif restraint_type == 'chirality':
          kwds['volume_ideal'] = value
        elif restraint_type in ('fixed_u_eq_adp',):
          kwds['u_eq_ideal'] = value
        elif restraint_type in ('bond_similarity'):
          kwds['weights'] = [kwds['weight']]*len(i_seqs)
          if restraint_type == 'bond_similarity':
            sym_ops = kwds['sym_ops']
            kwds['i_seqs'] = [[i_seq for i_seq in i_seqs[i*2:(i+1)*2]]
                                     for i in range(int(len(i_seqs)/2))]
            kwds['sym_ops'] = [[sym_op for sym_op in sym_ops[i*2:(i+1)*2]]
                                       for i in range(int(len(sym_ops)/2))]
        if restraint_type in ('adp_similarity', 'isotropic_adp', 'rigid_bond', 'rigu'):
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
        elif restraint_type == 'chirality':
          # Expand each atom in the list to include the 3 neighbours
          for atom_restraint in restraint['atoms']:
            i_seqs = []
            sym_ops = []
            # looking for the pivot atom in the model
            for residue in self.model['aunit']['residues']:
              for atom in residue['atoms']:
                if(atom['aunit_id']==atom_restraint[0]): 
                  # found the pivot atom
                  i_seqs.append(atom_restraint[0])
                  sym_ops.append( (sgtbx.rt_mx(flat_list(atom_restraint[1][:-1]), atom_restraint[1][-1]) 
                    if atom_restraint[1] is not None else None) )
                  pivot_name = atom['label']
                  
                  # if symmetry related we have a tuple, not an int
                  for neighbour in atom['neighbours']: 
                    if(type(neighbour)==type(())):
                      neighbour_id=neighbour[0]
                    else:
                      neighbour_id=neighbour
                    
                    # now finding the type of the neighbour
                    getmeout=False
                    for residuebis in self.model['aunit']['residues']:
                      for atombis in residuebis['atoms']:
                        if(atombis['aunit_id']==neighbour_id):
                          if(atombis['type']!='H'): # only non hydrogen atom are considered
                            i_seqs.append(neighbour_id)
                            if(type(neighbour)==type(())):
                              sym_ops.append( (sgtbx.rt_mx(flat_list(neighbour[2][:-1]), neighbour[2][-1])) )
                            else:
                              sym_ops.append(None)
                            getmeout=True
                            break
                      if(getmeout): break
                  # end loop over neighbours
            # end search of pivot atom

            if(len(i_seqs)==4):
              yield restraint_type, dict(
                i_seqs=i_seqs,
                sym_ops=sym_ops,
                volume_ideal=-1.0*kwds['volume_ideal'], # cctbx has opposite site compare to shelxl
                both_signs=False,
                weight=kwds['weight'],
                )
            else:
              print("Warning: Invalid chirality (CHIV) restraint. "+ 
                "%s needs exactly 3 neighbours"%pivot_name)
          # end loop over each atom of chiv restraint

        elif restraint_type == 'planarity':
          # The planarity restraint is implemented using the CHIV restraint
          # len(i_seqs)-3 CHIV restraints are necessary and used
          # list of atom often is ordered, shuffle the list to give a random set of tetrahedron
          # this step is not done in shelx
          shuffle_ids=[i for i in range(len(i_seqs))]
          random.seed('Use of a fixed seed for a consistent set of indices')
          random.shuffle(shuffle_ids)
          for i in xrange(len(i_seqs)-3):
            yield 'chirality', dict(
              i_seqs=[i_seqs[i] for i in shuffle_ids[i:i+4]],
              sym_ops=[kwds['sym_ops'][i] for i in shuffle_ids[i:i+4]],
              volume_ideal=0.0,
              both_signs=False,
              weight=kwds['weight'],
              )
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
    expected_atoms = cell_volume/17
    present_atoms = self.number_non_hydrogen_atoms()
    expected_peaks = expected_atoms - present_atoms
    return int(round(expected_peaks))

  def getExpectedPeaks_and_AtomsPresent(self):
    cell_volume = float(olx.xf.au.GetVolume())
    expected_atoms = cell_volume/15
    present_atoms = self.number_non_hydrogen_atoms()
    expected_peaks = expected_atoms - present_atoms
    return int(round(expected_peaks)), int(round(present_atoms))


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

def OnMatchStart(argStr):
  OV.write_to_olex('match.htm', "<b>RMS (&Aring;)&nbsp;Matched Fragments</b><br>")
  SpyVar.MatchedFragments = {}
  SpyVar.MatchedRms = []
  return ""
if haveGUI:
  OV.registerCallback('startmatch',OnMatchStart)

def OnMatchFound(rms, fragA, fragB):
  import string
  fragA = "'%s'" %fragA.replace(",", " ")
  fragB = "'%s'" %fragB.replace(",", " ")
  fragL = string.ascii_uppercase
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

def SetFormulaFromInput():
  formula = OV.GetValue('SET_FORMULA')
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

def ChooseLabelContent(cmd):
  olx.Labels(**dict([(k, True) for k in cmd.split()]))
  return ""
OV.registerFunction(ChooseLabelContent)

def FindZOfHeaviestAtomInFormula():
  from PeriodicTable import PT
  retVal = 0
  pt = PT.PeriodicTable()
  f = olx.xf.GetFormula('list')
  if not f:
    return retVal
  f = f.split(',')
  largestZ = 0
  largestEle = ""
  for element in f:
    ele = element.split(":")[0]
    Z = int(pt[ele].get('Z'))
    if Z > largestZ:
      largestZ = Z
      largestEle = ele
  retVal = (largestZ,largestEle)
  return retVal
OV.registerFunction(FindZOfHeaviestAtomInFormula)

def get_auto_q_peaks():
  ctrl_name = 'SET_SNUM_REFINEMENT_MAX_PEAKS'
  manual_q = OV.GetParam('snum.refinement.manual_q_peak_override',0)
  if manual_q:
    if OV.HasGUI() and OV.IsControl(ctrl_name):
      olx.html.SetBG(ctrl_name,'#ffeeee')
      olx.html.SetValue(ctrl_name,manual_q)
    return manual_q

  heavy = OlexRefinementModel().getExpectedPeaks()
  if heavy <= 0:
    heavy = 0
  else:
    heavy += int(round(heavy*0.2))
  hydrogen = int(olx.HAddCount())
  q = heavy + hydrogen
  if q == 0: q = 5
  OV.SetVar('auto_q',q)
  return q

def FindZOfHeaviestAtomInFormua():
  #for compatibility of old AC versions
  return FindZOfHeaviestAtomInFormula()

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

def GetHklFileList():
  reflection_file_extensions = ["hkl", "hkp", "raw", 'hklf5', 'hkc']
  g = OV.ListFiles(OV.FilePath(), ';'.join(reflection_file_extensions))
  g.sort()
  try:
    a = OV.HKLSrc()
    if a and (a[0] == "'" or a[0] == '"'):
      a = a[1:-1]
  except:
    a = ""

  if not os.path.exists(a) and not g:
    print "There is no reflection file or the reflection file is not accessible"
  reflection_files = []
  file_names = set()
  for item in g:
    fn = OV.FileName(item)
    file_names.add(fn)
    reflection_files.append("%s.%s<-%s" %(fn, OV.FileExt(item), item))
  if len(reflection_files) > 1 and OV.FileName() not in file_names:
    reflection_files.insert(0, "None<-")
  return ';'.join(reflection_files)
if haveGUI:
  OV.registerFunction(GetHklFileList)

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
    #try:
      #OV.CopyVFSFile("cbtn-%s%s.png" %(btn,state),"cbtn-%s.png" %btn)
    #except:
      #olex.m('skin default_new')
    if state == 'on':
      OV.SetVar('gui_MainToolbarTabButtonActive',btn)
  return "Done"
if haveGUI:
  OV.registerFunction(setAllMainToolbarTabButtons)

def onRefinementProgramChange(prg_name, method=None, scope='snum'):
  if prg_name == 'Auto':
    OV.SetParam('autochem.refinement.method','Auto')
    return
  prg = RPD.programs[prg_name]
  if method is None or not method:
    method = sortDefaultMethod(prg)
    if not OV.IsFileType('cif'):
      if method == 'Least Squares' and olx.LSM() == 'CGLS':
        method = 'CGLS' # work-around for bug #26
  OV.SetParam("%s.refinement.program" %scope, prg_name)
  OV.SetParam('user.refinement.default_program', prg_name)
  OV.SetParam("%s.refinement.method" %scope, method)
  onRefinementMethodChange(prg_name, method)
OV.registerFunction(OV.set_refinement_program)

def onRefinementMethodChange(prg_name, method):
  if method in RPD.programs[prg_name].methods:
    programSettings.doProgramSettings(prg_name, method)
    OV.SetParam('user.refinement.default_method', method)
  else:
    print "Please choose a valid method for the refinement program %s" %prg_name
OV.registerFunction(onRefinementMethodChange)

def onSolutionProgramChange(prg_name, method=None, scope='snum'):
  if prg_name == "Auto":
    OV.SetParam('%s.solution.method' %scope, 'Auto')
    #olx.html.SetValue('SET_autochem_solution_METHOD', 'Auto')
    return

  if prg_name != 'Unknown':
    prg = SPD.programs[prg_name]
    if method is None or not method:
      method = sortDefaultMethod(prg)
      if method == 'Direct Methods' and olx.Ins('PATT') != 'n/a':
        method = 'Patterson Method' # work-around for bug #48
    OV.SetParam("%s.solution.program" %scope, prg_name)
    OV.SetParam("%s.solution.method" %scope, method)
    OV.SetParam('user.solution.default_program', prg_name)
    onSolutionMethodChange(prg_name, method)
OV.registerFunction(OV.set_solution_program)

def onSolutionMethodChange(prg_name, method):
  if method in SPD.programs[prg_name].methods:
    programSettings.doProgramSettings(prg_name, method)
    OV.SetParam('user.solution.default_method', method)
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
  p = [x.name for x in RPD.programs[prg]]
  p.sort()
  for item in p:
    display = RPD.programs[prg].methods[item].display
    retval += "%s<-%s;" %(display,item)
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
  try:
    return olx.has_recently_updated
  except:
    version = OV.GetSVNVersion()
    try:
      V = OV.FindValue('last_version','0')
      last_version = int(V)
    except Exception, err:
      print "Alert: Reset parameter 'last_version'"
      last_version = 0
      OV.SetVar('last_version','0')

    if version > last_version:
      olx.has_recently_updated = True
    else:
      olx.has_recently_updated = False
    OV.SetVar('last_version',str(version))
    OV.StoreParameter('last_version')
    return olx.has_recently_updated

def GetOptionalHyphenString(txt):
  txt = txt.replace ("/", "/" + u"\u200B")
  txt = txt.replace ("\\", "\\" + u"\u200B")
  txt = txt.replace ("\\", "\\" + " ")
  return txt
OV.registerFunction(GetOptionalHyphenString)

def GetTwinLawAndBASF(html=False):
  olex_refinement_model = OV.GetRefinementModel(False)
  curr_law = None
  basf_list = olex_refinement_model['hklf'].get('basf', [])
  if not basf_list:
    basf_list = olex_refinement_model.get('twin', {}).get('basf', [])
  basf_count = len(basf_list)
  if olex_refinement_model.has_key('twin'):
    c = olex_refinement_model['twin']['matrix']
    curr_law = []
    for row in c:
      for el in row:
        curr_law.append(el)
    curr_law = tuple(curr_law)

  txt = ""
  if curr_law:
    txt = repr(curr_law)
  basf = []
  if olx.IsFileType("ires") != "false":
    try:
      for i in range(basf_count):
        v = olx.xf.rm.BASF(i)
        if '(' not in v:
          v = ".3f" %float(v)
        basf.append(v)
    except:
      for i in range(basf_count):
        basf_val = olx.Lst("basf_%s" %(i+1))
        if basf_val == 'n/a':
          break
        basf.append(basf_val)
      if (len(basf) != basf_count):
        basf = ["%.3f" %x for x in basf_list]
  if not txt and not basf:
    return ""
  if basf:
    if txt: txt += ", "
    txt += "BASF [%s]" % ";".join(basf)

  if html:
    if curr_law:
      txt = "<tr><td><b><font color='%s'>TWIN LAW %s</font></b></td></tr>" %(
        OV.GetParam('gui.green_text').hexadecimal, txt)
    else:
      txt = "<tr><td><b><font color='%s'>HKLF 5 %s</font></b></td></tr>" %(
        OV.GetParam('gui.green_text').hexadecimal, txt)
  return txt
OV.registerFunction(GetTwinLawAndBASF)


def HklStatsAnalysis():
  import olex_core
  stats = olex_core.GetHklStat()
OV.registerFunction(HklStatsAnalysis)


def InstalledPlugins():
  import olex_core
  l = olex_core.GetPluginList()
  if l is None:
    l = []
  return list(l)

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


def getReportTitleSrc():
  import PIL
  from PIL import Image
  from PIL import ImageDraw
  from PIL import PngImagePlugin
  import StringIO
  import base64
  from PIL import EpsImagePlugin
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
  from ImageTools import ImageTools
  IT = ImageTools()
  image_name = OV.GetParam('snum.report.image')
  if image_name == "No Image":
#    OV.SetParam('snum.report.image',None)
    return
  elif image_name == "SCREENSHOT":
    olex.m('showq a false')
    olex.m('showq b false')
    olex.m('pict -pq screenshot.png 1')
    filefull = "%s/screenshot.png" %OV.FilePath()
    IT.trim_image(im=filefull, padding=2, border=0.2, border_col = "#ababab")
    OV.SetParam('snum.report.image',"screenshot.png")
OV.registerFunction(dealWithReportImage)

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
  from PIL import Image
  from PIL import PngImagePlugin
  import StringIO
  import base64
  from PIL import ImageDraw
  from PIL import EpsImagePlugin
  import StringIO
  make_border = OV.GetParam('snum.report.image_border')

  size_type = size[:1]
  size = int(size[1:])

  if imageName is None:
    imageName = 'snum.report.image'
    if not OV.HasGUI():
      return "No Image available in Headless Mode!"

  if "snum.report" in imageName:
    imagePath = OV.GetParam(imageName)
    if not imagePath:
      imageNameU = imageName.replace('snum', 'user')
      imagePath = OV.GetParam(imageNameU)
      if imagePath:
        OV.SetParam(imageName, imagePath)

  if imagePath == "Live Picture":
    err = """<font color='red'><b>You need DrawPlus installed for this feature</b></font>"""
    try:
      model = olex.f("JSON()")
      if model == False:
        return err
      base = os.path.join(olex.f(OV.GetParam('user.modules.location')), "modules")
      dp_base = os.path.join(base, "DrawPlus")
      with open(os.path.join(dp_base, "template.lip"), 'rb') as rFile:
        rv = rFile.read()
        rv += "<script type='application/json' id='model'>%s</script>" %(model)
        rv += "<script type='application/json' id='style'>%s</script>" %(
          olex.f("ExportColors('', 'current')"))
        return rv
    except Exception, e:
      #print str(e)
      return err

  if imagePath == "No Image" or not imagePath:
    return ""
  if "Dir()" in imagePath: # data/base/str
    imagePath = olex.f(imagePath)
    
  if type(imagePath) != list:
    imagePath_l = [imagePath]
  else:
    imagePath_l = imagePath
    
  html = ""
  for imagePath in imagePath_l:

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
        draw.line((0,0,width-1,0), fill = fill)
        draw.line((0,height -1,width-1,height -1), fill = fill)
        draw.line((0,0,0,height - 1), fill = fill)
        draw.line((width -1,0,width-1,height -1), fill = fill)
  
    out = StringIO.StringIO()
    IM.save(out, "PNG")
    data = base64.b64encode(out.getvalue())
    html +='''
  <!--[if IE]><img width=%s src='%s'><![endif]-->
  <![if !IE]><img width=%s src='data:image/png;base64,%s'><![endif]>
    '''%(int(size/2), os.path.split(imagePath)[1], int(size/2), data)
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

def revert_to_original():
  History.hist.revert_to_original()
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

def StringsAreEqual(str1, str2):
  return str1 == str2
OV.registerFunction(StringsAreEqual)

def StringsAreNotEqual(str1, str2):
  if str1 == str2:
    return False
  else:
    return True
OV.registerFunction(StringsAreNotEqual)

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

def formatted_date_from_timestamp(dte,date_format=None):
  if not date_format:
    date_format = OV.GetParam('snum.report.date_format')
  from datetime import date
  from datetime import datetime
  if not dte:
    return "No Date"
  if "-" in dte:
    if len(dte.split("-")[0]) == 4:
      try:
        dte = datetime.strptime(dte, "%Y-%m-%d")
        dte = dte.strftime(date_format)
        return dte
      except:
        return dte
  if "." in dte:
    dte = OV.GetParam(dte)
  if not dte:
    return None
  try:
    dte = float(dte)
  except:
    return "Not A Date"
  dte = date.fromtimestamp(dte)
  return dte.strftime(date_format)
OV.registerFunction(formatted_date_from_timestamp)

if not haveGUI:
  def tbxs(name):
    print "This is not available in Headless Olex"
    return ""
  #OV.registerFunction(tbxs)
OV.registerFunction(OV.IsPluginInstalled)
OV.registerFunction(OV.GetTag)

def SetMasking(v):
  if v == 'true':
    olx.AddIns('ABIN', q=True)
  else:
    olx.DelIns('ABIN')
  OV.SetParam('snum.refinement.use_solvent_mask', v)
OV.registerFunction(SetMasking)

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

def EditIns():
  olx.EditIns()
  programSettings.doProgramSettings(
    OV.GetParam('snum.refinement.program'),
    OV.GetParam('snum.refinement.method'))
  OV.SetParam("snum.refinement.use_solvent_mask", olx.Ins("ABIN") != "n/a")
  olx.html.Update()
OV.registerFunction(EditIns)

def FixMACQuotes(text):
  if text:
    return text.replace(u"\u2018", u"'")\
      .replace(u"\u2014", u"-")\
      .replace(u"\u2019", u"'")\
      .replace(u"\u201c", u"\"")\
      .replace(u"\u201d", u"\"")\
     .encode("ascii")
  return text
