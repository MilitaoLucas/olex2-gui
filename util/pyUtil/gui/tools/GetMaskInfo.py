import os
import re
from olexFunctions import OlexFunctions
OV = OlexFunctions()
try:
  from_outside = False
  p_path = os.path.dirname(os.path.abspath(__file__))
except:
  from_outside = True
  p_path = os.path.dirname(os.path.abspath("__file__"))

import olx
import iotbx.cif.model
import CifInfo

debug = bool(OV.GetParam("olex2.debug", False))

global mask_info_has_updated
mask_info_has_updated = False

gui_green = OV.GetParam('gui.green')
gui_orange = OV.GetParam('gui.orange')
gui_red = OV.GetParam('gui.red')
gui_grey = OV.GetParam('gui.grey')

from PeriodicTable import PeriodicTable
PT = PeriodicTable()
pt = PT.PeriodicTable()


def get_mask_info():
  global mask_info_has_updated
  import gui
  get_template = gui.tools.TemplateProvider.get_template
  template_path = os.path.join(OV.DataDir(), 'mask_output.htm')
  if not os.path.exists(template_path):
    template_path = os.path.join(p_path, 'mask_output.htm')
    
  
#  print ".. %s .." %template_path
  global current_sNum
  current_sNum = OV.ModelSrc()
  if OV.HKLSrc().rstrip(".hkl").endswith("_sq"):
    base = "platon_squeeze"
  else:
    base = "smtbx_masks"
  
  d = {}
#  d['table_bg'] =  OV.GetParam('gui.html.table_firstcol_colour')
  d['table_bg'] =  olx.GetVar('HtmlTableBgColour')
  
  is_CIF = (olx.IsFileType('cif') == 'true')

  numbers = olx.cif_model[current_sNum].get('_%s_void_nr' %base, None)

  if numbers == [u'n/a']:
    return "no mask info"

  if not numbers:
    numbers = olx.cif_model[current_sNum].get('_%s_void_nr' %base)
    if not numbers:
      if is_CIF:
        numbers = olx.Cif('_%s_void_nr' %base).split(",")
        if not numbers:
          return "No mask information"
      else:
        return "No mask information"

  if is_CIF:
    volumes = olx.Cif('_%s_void_volume' %base).split(",")
    electrons = olx.Cif('_%s_void_count_electrons' %base).split(",")
    contents = olx.Cif('_%s_void_content' %base).split(",")
    details = olx.Cif('_%s_details' %base).split(",")
    mask_special_details = olx.Cif('_%s_special_details' %base).split(",")
    mask_special_details = mask_special_details[0].strip().lstrip("'").rstrip("'")

  else:
    volumes = olx.cif_model[current_sNum].get('_%s_void_volume' %base)
    electrons = olx.cif_model[current_sNum].get('_%s_void_count_electrons' %base)
    contents = olx.cif_model[current_sNum].get('_%s_void_content' %base)
    details = olx.cif_model[current_sNum].get('_%s_details' %base)
    mask_special_details = olx.cif_model[current_sNum].get('_%s_special_details' %base)
    if mask_special_details: mask_special_details = mask_special_details.strip()

  Z =float(olx.xf.au.GetZ())
  Zprime = float(olx.xf.au.GetZprime())
  number_of_symm_op = round(Z/Zprime)
  Z = round(Z)
  Zprime = Z/number_of_symm_op

  t = "<table bgcolor='%s' border='0' cellspacing='1' cellpadding='2' width='100%%'>" %"#ababab"
  t += get_template('mask_output_table_header_rp', path=template_path, force=debug)%d

  ident_l = []
  for number, volume, electron, content in zip(numbers, volumes, electrons, contents):
    volume = "%.0f" %round(float(volume),0)
    electron = "%.0f" %round(float(electron),0)
    ident_l.append((volume,electron))

  accounted_for = {}
  sum_content = []

  sum_e = 0
  
  total_void_volume = 0
  total_void_electrons = 0
  total_void_accounted_for_electrons = 0
  total_void_no = 0
  
  for number, volume, electron, content in zip(numbers, volumes, electrons, contents):
    volume = "%.0f" %round(float(volume),0)
    electron = "%.0f" %round(float(electron),0)
    _ = (volume,electron)

    got_it = False
    for accounted_for_entry in accounted_for:
      if volume in accounted_for_entry:
        got_it = True
    if got_it:
      continue

    multiplicity = 0
    multi_idx = []
    i = 1
    for occ in ident_l:
#      if _ == occ:
      if volume == occ[0]:
        multiplicity += 1
        multi_idx.append(str(i))

      i += 1
    accounted_for.setdefault(volume, [])
    accounted_for[volume].append(_[0])

    moiety = OV.get_cif_item('_chemical_formula_moiety',None)
    if not moiety:
      moiety = olx.xf.latt.GetMoiety()


    d['number'] = number
    electron = float(electron) * multiplicity
    volume = float(volume) * multiplicity
    d['electron'] = "%.0f" %float(electron)
    d['volume'] = "%.0f" %float(volume)
    d['multiplicity'] = format_number(multiplicity)
    d['formula'] = get_rounded_formula(as_string_sep=" ")
    d['moiety'] = moiety
    
    total_void_electrons += electron
    total_void_volume += volume
    total_void_no += 1

    
    content = content.strip("'")

    #if multiplicity == 1:
      #multiplicity = Z

    factor = number_of_symm_op

    _ = content.split(",")

    electrons_accounted_for = 0
    non_h_accounted_for = 0
    for entry in _:
      sum_content.append((factor, entry))
      entity, multi = split_entity(entry)
      multi = float(multi)
      ent = moieties.get(entity.lower(), entity)
      ent = formula_cleaner(unicode(ent))

      try:
        Z, N = get_sum_electrons_from_formula(ent)
        electrons_accounted_for += Z * multi * factor
        non_h_accounted_for += N * multi * factor
      except:
        electrons_accounted_for += 0

    if volume == "n/a":
      return

    if float(volume) < 15:
      continue

    total_void_accounted_for_electrons += electrons_accounted_for

    if electrons_accounted_for - (0.1 * electrons_accounted_for) < float(electron) < electrons_accounted_for + (0.1 * electrons_accounted_for):
      electrons_accounted_for_display = "<font color='%s'><b>%.0f</b></font>" %(gui_green,electrons_accounted_for)
    elif electrons_accounted_for - (0.2 * electrons_accounted_for) < float(electron) < electrons_accounted_for + (0.2 * electrons_accounted_for):
      electrons_accounted_for_display = "<font color='%s'><b>%.0f</b></font>" %(gui_orange, electrons_accounted_for)
    else:
      electrons_accounted_for_display = "<font color='%s'><b>%.0f</b></font>" %(gui_red,electrons_accounted_for)

    if float(electron) != 0:
      v_over_e  = float(volume)/float(electron)
      if v_over_e < 3:
        v_over_e_html = "<font color='%s'><b>%.1f</b></font>" %(gui_red,v_over_e)
      elif v_over_e > 7:
        v_over_e_html = "<font color='%s'><b>%.1f</b></font>" %(gui_red,v_over_e)
      else:
        v_over_e_html = "<font color='%s'><b>%.1f</b></font>" %(gui_green,v_over_e)
    else: v_over_e_html = "n/a"
    d['v_over_e'] = v_over_e_html


    if float(volume) != 0:
      v_over_n_html = "n/a"
      if non_h_accounted_for != 0:
        v_over_n  = float(volume)/non_h_accounted_for
        if v_over_n < 20:
          v_over_n_html = "<font color='%s'><b>%.1f</b></font>" %(gui_red,v_over_n)
        elif v_over_n > 50:
          v_over_n_html = "<font color='%s'><b>%.1f</b></font>" %(gui_red,v_over_n)
        else:
          v_over_n_html = "<font color='%s'><b>%.1f</b></font>" %(gui_green,v_over_n)
    d['v_over_n'] = v_over_n_html


    content = '%s <a target="Please enter the contents that are present in this void." href="spy.add_mask_content(%s,content)">(Edit)</a>' %(content, ":".join(multi_idx))
    details = '<a href="spy.add_mask_content(%s,detail)"> (Edit)</a>' %":".join(multi_idx)
    d['content'] = content
    d['details'] = details
    d['e_accounted_for'] = electrons_accounted_for_display
    d['e_accounted_for_raw'] = electrons_accounted_for
    t += get_template('mask_output_table_row_rp', path=template_path, force=debug) %d
  t += "</table>"

  #-- FINAL BLOCK ###############
  
  total_formula = get_rounded_formula()
  total_electrons_accounted_for = 0
  add_to_formula = ""
  add_to_moiety = ""
  for entry in sum_content:
    entity = entry[1]
    if "?" in entity:
      continue
    entity, multi = split_entity(entity)
    multi = float(multi)
    #head = entity.lstrip('0123456789./')
    #multi = entity[:(len(entity)-len(head))]
    #if not multi: multi = 1
    #multi = float(multi)
    #multiplicity = entry[0]
    #entity = head.strip()
    ent = moieties.get(entity.lower(), entity)
    ent_disp = ent.replace(" ", "")
    ent = " ".join(re.split("(?<=[0-9])(?=[a-zA-Z])",ent))
    ent = formula_cleaner(unicode(ent))

    try:
      total_electrons_accounted_for += get_sum_electrons_from_formula(ent) * multi * factor * Z
    except:
      total_electrons_accounted_for += 0

    factor = round(float(multi)/Zprime,3)

    total_formula = _add_formula(total_formula, ent, factor)
    add_to_formula = _add_formula(add_to_formula, ent, factor)
    
    if str(factor).endswith(".0"):
      factor = int(factor)
    add_to_moiety += "%s[%s], " %(factor, ent_disp)

  add_to_moiety = add_to_moiety.rstrip(", ")
  suggested_moiety = "%s, %s" %(olx.xf.latt.GetMoiety(), add_to_moiety)

  total_void_no_plural = ""
  if total_void_no > 1:
    total_void_no_plural = "s"

  d['suggested_moiety'] = suggested_moiety
  d['add_to_moiety'] = add_to_moiety
  d['suggested_sum']= total_formula
  d['add_to_formula']= add_to_formula
  d['base']= base
  d['current_sNum']= current_sNum

  d['total_void_electrons'] = total_void_electrons
  d['total_void_accounted_for_electrons'] = total_void_accounted_for_electrons
  d['total_void_volume'] = total_void_volume
  d['total_void_no_plural'] = total_void_no_plural
  d['total_void_no'] = total_void_no

  if mask_special_details == "?" or mask_info_has_updated:
    if add_to_formula:
      mask_special_details = get_template('mask_special_detail_default', path=template_path, force=debug)%d
    else:
      mask_special_details = ""
    mask_info_has_updated = False
  if mask_special_details:
    mask_special_details = mask_special_details.strip().lstrip('"').rstrip('"').replace("\r","")
  if mask_info_has_updated:
    olx.cif_model[current_sNum]['_%s_special_details' %base] = mask_special_details
    update_sqf_file(current_sNum, '_%s_special_details' %base)

  d['mask_special_details']= mask_special_details

  if add_to_formula:
    t += get_template('mask_output_end_rp', path=template_path, force=debug)%d
    t += get_template('mask_special_details', path=template_path, force=debug)%d
  return t
OV.registerFunction(get_mask_info, False, 'gui.tools')

def get_moieties_from_list():
  moieties = {}
  _ = os.path.join(OV.DataDir(),'moieties.cvs')
  if os.path.exists(_):
    pass
  else:
    _ = os.path.join(p_path,'moieties.csv')
  rFile = open(_,'r').readlines()
  for line in rFile:
    nick,formula = line.split(",")
    nick = nick.strip()
    formula = formula.strip()
    if nick and formula:
      moieties.setdefault(nick, formula)
  return moieties


moieties = get_moieties_from_list()


import decimal
import random

def get_rounded_formula(rnd=2, as_string_sep=""):
  formula = olx.xf.GetFormula('list',rnd)
  if as_string_sep:
    formula = formula.split(",")
    formula = as_string_sep.join(formula).replace(":","")
  return formula

def format_number(num):
  return round(num,3)

def get_sum_electrons_from_formula(f):
  Z = 0
  N = 0
  if not f:
    return retVal
  f = f.split()
  for entry in f:
    element = entry.rstrip('0123456789')
    try:
      number = float(entry[len(element):])
    except:
      number = 1
    Z += int(pt[element].get('Z')) * number
    if element != "H":
      N += number
  return Z,N

def split_entity(entry):
  try:
    entry = entry.strip()
    entity = entry.lstrip('0123456789./(')
    multi = entry[:(len(entry)-len(entity))]
    if not multi:
      multi = 1
    else:
      if "/" in multi:
        multi = float(multi.split("/")[0])/float(multi.split("/")[1])
    entity = entity.strip().rstrip("(")
  except:
    entity = ""
    multi= 1
  return entity, multi


##!HP remove once updated in main!
#from gui.tools import Templates
#class TemplatesTemp(object):
  #def __init__(self,):
    #nparent = gui.tools.TemplateProvider
    #self.parent.get_all_templates = self.get_all_templates

  #def get_all_templates(self, path=None, mask="*.*", marker='{-}'):
    #'''
    #Parses the path for template files.
    #'''
    #if not path:
      #path = os.path.join(OV.BaseDir(), 'util', 'pyUtil', 'gui', 'templates')
    #if path[-4:-3] != ".": #i.e. a specific template file has been provided
      #g = glob.glob("%s%s%s" %(path,os.sep,mask))
    #else:
      #g = [path]
    #for f_path in g:
      #fc = open(f_path, 'r').read()
      #if not self.parent._extract_templates_from_text(fc,marker=marker):
        #name = os.path.basename(os.path.normpath(f_path))
        #self.templates[name] = fc
#TemplatesTemp()

cleaned_formulae = {}
def formula_cleaner(formula):
  formula = formula.replace(" ", "").replace(" ", "")
  if cleaned_formulae.has_key(formula):
    return cleaned_formulae[formula]
  retVal = ""
  el = ""
  n = ""
  i = 0
  for char in formula:
    if unicode.isnumeric(char) or unicode.isspace(char) or unicode.islower(char):
      continue
    while unicode.isalpha(char):
      i += 1
      if not el:
        el += char
      else:
        if unicode.islower(char):
          el += char
        elif unicode.isupper(char):
          n = "1"
          i -= 1
          break
      char = formula[i:(i+1)]
    while unicode.isnumeric(char):
      i += 1
      n += char
      char = formula[i:(i+1)]
    if el and n == "":
      n = 1
    retVal += "%s%s "%(el, n)
    n = ""
    el = ""
  if debug:
    print "%s --> %s" %(formula, retVal.strip())
  cleaned_formulae[formula] = retVal
  return retVal.strip()


def update_metacif(sNum, file_name):
  pass
  ciflist = OV.GetCifMergeFilesList()
  if file_name not in ciflist:
    gui.report.publication.add_cif_to_merge_list.im_func(file_name)
  
  
  try:
    olex.m("spy.gui.report.publication.add_cif_to_merge_list(%s)" %file_name)
  except:
    return


  # ATTEMPT 2
  from CifInfo import CifTools
  CT = CifTools()
  CT.update_cif_block(olx.cif_model[sNum],force=True)

  # ATTEMPT 1  
  #metacif_path = '%s%s%s.metacif' %(OV.StrDir(), os.sep, sNum)
  #with open(metacif_path, 'wb') as f:
    #print >> f, olx.cif_model[sNum]
  #olex.m('cifmerge')  

def get_sqf_name(full=True):
  if full:
    retVal = OV.HKLSrc().replace(".hkl", ".sqf")
  else:
    retVal = "%s.sqf" %(current_sNum)  
  return retVal

def edit_mask_special_details(txt,base,sNum):
  user_value = str(OV.GetUserInput(0, "Edit _mask_special_details", txt))
  if user_value == "None":
    return
  if user_value:
    olx.cif_model[current_sNum]['_%s_special_details' %base] = user_value
    model_src = OV.ModelSrc()
    update_sqf_file(current_sNum, '_%s_special_details' %base)
    #update_metacif(sNum, get_sqf_name())
    olx.html.Update()

OV.registerFunction(edit_mask_special_details)

def update_sqf_file(current_sNum, scope, scope2=None):
  sqf_file = get_sqf_name()
  if os.path.exists(sqf_file):
    with file(sqf_file, 'r') as original: data = original.read()
    with file(sqf_file, 'w') as modified: modified.write("data_%s\n"%OV.ModelSrc() + data)    
    with open(sqf_file, 'rb') as f:
      cif_block = iotbx.cif.reader(file_object=f).model()

    if not scope2:
      cif_block[current_sNum][scope] = olx.cif_model[current_sNum][scope]
    else:
      cif_block[current_sNum][scope][scope2] = olx.cif_model[current_sNum][scope][scope2]

    from iotbx.cif import model
    cif = model.cif()
    cif = cif_block
    
    with open(sqf_file, 'w') as f:
      print >> f, cif
    f.close()
    CifInfo.MergeCif()

def add_mask_content(i,which):
  global mask_info_has_updated
  global current_sNum
  current_sNum = OV.ModelSrc()
  if OV.HKLSrc().rstrip(".hkl").endswith("_sq"):
    base = "platon_squeeze"
  else:
    base = "smtbx_masks"
  
  is_CIF = (olx.IsFileType('cif') == 'true')
  if ":" not in i:
    i_l = [str(i)]
  else:
    i_l = i.split(":")
  current_sNum = OV.ModelSrc()
  contents = olx.cif_model[current_sNum].get('_%s_void_%s' %(base, which))
  if not contents:
    if is_CIF:
      contents = olx.Cif('_%s_void_nr' %base).split(",")
  try:
    disp = ",".join(i_l)
  except:
    disp = "fix me!"
  c = contents[int(i_l[0])-1]
  if c == "?":
    c = ""
  c = c.lstrip("'").rstrip("'")
  user_value = str(OV.GetUserInput(0, "Edit Mask %s for Void No %s"%(which, disp), c)).strip()
  if user_value == "None":
    return
  if not user_value:
    user_value = "?"

  _ = list(contents)
  for idx in i_l:
    idx = int(idx) - 1
    _[idx] = user_value
    
  mask = OV.get_cif_item('_%s_void' %base)
  olx.cif_model[current_sNum]['_%s_void' %base]['_%s_void_content' %base] = _
  update_sqf_file(current_sNum, '_%s_void' %base, '_%s_void_content' %base)
  mask_info_has_updated = True
  olx.html.Update()
  
  
def _add_formula(curr, new, multi = 1):
  if "," in curr:
    curr_l = curr.split(",")
  else:
    curr_l = curr.split()
  new_l = new.split()
  updated_d = {}

  #if len(new_l) == 1:
    #retVal = "please adjust manually!"

  _ = [curr_l, new_l]
  i = 0
  for item in _:
    if not item:
      i += 1
      continue
    for tem in item:
      if not tem:
        continue
      if ":" in tem:
        head = tem.split(":")[0]
        tail = tem.split(":")[1]
      else:
        head = tem.rstrip('0123456789./')
        tail = tem[len(head):]
      if tail:
        tail = float(tail)
      else:
        tail = 1.0
      if i == 1: #don't mulitply the already existing bits
        tail = round(tail * multi,2)
      updated_d.setdefault(head, 0)
      updated_d[head] += tail
    i += 1
  l = []
  for item in updated_d:
    l.append ("%s%s " %(item, format_number(updated_d[item])))

  l.sort()
  retVal = ""
  for item in l:
    retVal += item
  return retVal
  

OV.registerFunction(add_mask_content)
OV.registerFunction(formula_cleaner)
