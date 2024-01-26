import os
import re
from fractions import Fraction
from olexFunctions import OV
import OlexVFS

try:
  from_outside = False
  p_path = os.path.dirname(os.path.abspath(__file__))
except:
  from_outside = True
  p_path = os.path.dirname(os.path.abspath("__file__"))

import olx
import olex
import iotbx.cif.model
import CifInfo

debug = OV.IsDebugging()

global mask_info_has_updated
mask_info_has_updated = False

gui_green = OV.GetParam('gui.green').hexadecimal
gui_orange = OV.GetParam('gui.orange').hexadecimal
gui_red = OV.GetParam('gui.red').hexadecimal
gui_grey = OV.GetParam('gui.grey').hexadecimal
gui_light_grey = OV.GetParam('gui.light_grey').hexadecimal
gui_highlight = OV.GetParam('gui.html.highlight_colour').hexadecimal
gui_width = OV.GetParam('gui.htmlpanelwidth')

OV.SetParam('snum.masks.special_detail_colour', gui_green)

from PeriodicTable import PeriodicTable
PT = PeriodicTable()
pt = PT.PeriodicTable()

import gui
template_path = os.path.join(OV.DataDir(), 'mask_output.htm')
if not os.path.exists(template_path):
  template_path = os.path.join(p_path, 'mask_output.htm')


def get_mask_info():
  if not olx.cif_model:
    import CifInfo
    CifInfo.ExtractCifInfo()

  global mask_info_has_updated
  import gui

  output_fn = '%s_masking_info.htm' % OV.ModelSrc()
  get_template = gui.tools.TemplateProvider.get_template

  if olx.IsFileLoaded() != 'true':
    return return_note("")
  if (olx.IsFileType('cif') == 'true'):
    return return_note("")

  based_on = OV.GetParam('user.masks.based_on')
  based_on_display = "Asymmetric Unit"
  if based_on == "FU":
    based_on_display = "Formula Unit"
  elif based_on == "Cell":
    based_on_display = "Unit Cell"

#  print ".. %s .." %template_path
  global current_sNum
  current_sNum = OV.ModelSrc()

  prg = OV.GetParam('snum.refinement.recompute_mask_before_refinement_prg', "Olex2")
  if prg == "Platon":
    base = "platon_squeeze"
  else:
    base = "smtbx_masks"
#  change_hklsrc_according_to_mask_prg(prg)

  d = {}
  d['table_bg'] = olx.GetVar('HtmlTableBgColour')
  d['based_on'] = based_on
  d['based_on_display'] = based_on_display
  d['row_begin'] = get_template('row_begin', path=template_path, force=debug) % d
  d['row_end'] = get_template('row_end', path=template_path, force=debug) % d
  d['table_begin'] = get_template('table_begin', path=template_path, force=debug) % d
  d["note"] = "No Masking Information"
  d["note_bg"] = OV.GetVar('HtmlHighlightCOlour')

  _ = escape_param_names(name=OV.ModelSrc())
  mask_special_details_vn = "%s_%s" % (_, "mask_special_details")

  is_CIF = (olx.IsFileType('cif') == 'true')
  sqf = None
  if is_CIF:
    volumes = olx.Cif('_%s_void_volume' % base).split(",")
    electrons = olx.Cif('_%s_void_count_electrons' % base).split(",")
    contents = olx.Cif('_%s_void_content' % base).split(",")
    details = olx.Cif('_%s_details' % base).split(",")
    mask_special_details = olx.Cif('_%s_special_details' % base).split(",")
    mask_special_details = mask_special_details[0].strip().lstrip("'").rstrip("'")

  else:
    try:
      sqf_f = get_sqf_name(base=base)
      rFile = open(sqf_f, 'r').read()
      if "platon_squeeze" in rFile:
        base = "platon_squeeze"
      if not rFile.startswith("data_"):
        rFile = "data_%s\n" % str(current_sNum) + rFile

      sqf = iotbx.cif.fast_reader(input_string=rFile).model()
    except Exception as err:
      return return_note(note="No masking info yet! ", col=gui_green)
    if sqf:
      if current_sNum not in sqf:
        sqf_block = sqf[sqf.keys()[0]]
        OV.PrintMaskHKLWarning(
          "Warning: mask data name (%s) does not match file name (%s) - check HKL file used for the refinement!"
            % (sqf.keys()[0], current_sNum))
      else:
        sqf_block = sqf[current_sNum]
      olx.cif_model[current_sNum].update(sqf_block)
    volumes = olx.cif_model[current_sNum].get('_%s_void_volume' % base)
    if not volumes:
      return return_note(note="No void has been found.", col=gui_orange)
    electrons = olx.cif_model[current_sNum].get('_%s_void_count_electrons' % base)
    contents = olx.cif_model[current_sNum].get('_%s_void_content' % base)
    details = olx.cif_model[current_sNum].get('_%s_details' % base)
    mask_special_details = olx.cif_model[current_sNum].get('_%s_special_details' % base)
    if mask_special_details:
      mask_special_details = mask_special_details.strip()

  numbers = olx.cif_model[current_sNum].get('_%s_void_nr' % base, None)

  if numbers == ['n/a']:
    return return_note(note="No Voids Found", col=gui_green)

  if not numbers:
    numbers = olx.cif_model[current_sNum].get('_%s_void_nr' % base)
    if not numbers:
      if is_CIF:
        numbers = olx.Cif('_%s_void_nr' % base).split(",")
        if not numbers:
          return return_note(note="No Voids in CIF", col=gui_green)

  Z = float(olx.xf.au.GetZ())
  Zprime = float(olx.xf.au.GetZprime())
  number_of_symm_op = round(Z / Zprime)
  Z = round(Z)
  Zprime = Z / number_of_symm_op

  t = get_template('mask_output_table_begin', path=template_path, force=debug) % d
  t += get_template('mask_output_table_header_rp', path=template_path, force=debug) % d

  ident_l = []
  for number, volume, electron, content in zip(numbers, volumes, electrons, contents):
    volume = "%.0f" % round(float(volume), 0)
    electron = "%.0f" % round(float(electron), 0)
    ident_l.append((volume, electron))

  accounted_for = {}
  sum_content = []

  sum_e = 0

  total_void_volume = 0
  total_void_electrons = 0
  total_void_accounted_for_electrons = 0
  total_void_no = 0
  f = get_adjust_for_base_factor()
  for number, volume, electron, content in zip(numbers, volumes, electrons, contents):
    multi_idx = []
    electrons_accounted_for = 0
    non_h_accounted_for = 0
    volume = float(volume)
    electron = float(electron)
    volume = "%.0f" % round(volume, 0)
    electron = "%.0f" % round(electron, 0)
    _ = (volume, electron)

    got_it = False
    for accounted_for_entry in accounted_for:
      if volume in accounted_for_entry:
        got_it = True
    if got_it:
      continue

    multiplicity = 0
    i = 1
    _idx = []
    for occ in ident_l:
#      if _ == occ:
      if volume == occ[0]:
        multiplicity += 1
        _idx.append(str(i))
      i += 1
    for bit in _idx:
      multi_idx.append("%s|%s" % (bit, multiplicity))
    accounted_for.setdefault(volume, [])
    accounted_for[volume].append(_[0])

    moiety = OV.get_cif_item('_chemical_formula_moiety', None)
    if not moiety or "[]" in moiety or "[+ solvents]" in moiety:
      moiety = olx.xf.latt.GetMoiety()

    electron = float(electron) * multiplicity
    volume = float(volume) * multiplicity

    if float(volume) < 15:
      continue

    #f = get_adjust_for_base_factor()
    #volume *= f
    #electron *= f

    d['number'] = number
    d['electron'] = "%.0f" % float(electron)
    d['volume'] = "%.0f" % float(volume)
    d['multiplicity'] = format_number(multiplicity)
    d['formula'] = get_rounded_formula(as_string_sep=" ")
    d['moiety'] = moiety
    d['based_on'] = based_on
    d['based_on_display'] = based_on_display

    total_void_electrons += electron
    total_void_volume += volume
    total_void_no += 1

    content = content.strip("'")

    _ = content.split(",")

    content_disp_l = []

    for entry in _:
      if not entry or entry == "?":
        continue
      sum_content.append((multiplicity, entry))
      entity, user_number = split_entity(entry)
      user_number = float(user_number)
      ent = moieties.get(entity.lower(), entity)
      ent = formula_cleaner(str(ent))

      try:
        Z, N = get_sum_electrons_from_formula(ent)
        electrons_accounted_for += Z * user_number
        non_h_accounted_for += N * user_number
      except:
        electrons_accounted_for += 0

      if entity and entity != "?":
        _ = "%s %s" % (format_number(multiplicity * user_number / f), entity)
        if ent:
          content_disp_l.append(_)
        else:
          content_disp_l.append("<font color=%s><b>%s</b></font>" % (gui.red, _))
      else:
        _ = "<font color=%s><b>%s</b></font>" % (gui.red, entity)
        content_disp_l.append(_)
    content_disp = ", ".join(content_disp_l)

    electrons_accounted_for = electrons_accounted_for * multiplicity
    non_h_accounted_for = non_h_accounted_for * multiplicity

    if volume == "n/a":
      return

    total_void_accounted_for_electrons += electrons_accounted_for
    eaf = electrons_accounted_for
    eafd = "%.0f" % (electrons_accounted_for / f)
    electron_bg = gui_red
    electron_fg = "#eeeeee"
    if eaf - (0.1 * eaf) < float(electron) < eaf + (0.1 * eaf):
      electron_bg = gui_green
    elif eaf - (0.2 * eaf) < float(electron) < eaf + (0.2 * eaf):
      electron_bg = gui_orange
    e_accounted_for_display = eafd

    if float(electron) != 0:
      v_over_e = float(volume) / float(electron)
      if v_over_e < OV.GetParam('user.masks.v_over_e.lower'):
        v_over_e_html = "<font color='%s'><b>%.1f </b></font>" % (gui_red, v_over_e)
      elif v_over_e > OV.GetParam('user.masks.v_over_e.upper'):
        v_over_e_html = "<font color='%s'><b>%.1f </b></font>" % (gui_red, v_over_e)
      else:
        v_over_e_html = "<font color='%s'><b>%.1f </b></font>" % (gui_green, v_over_e)
    else:
      v_over_e_html = "n/a"
    d['v_over_e'] = v_over_e_html

    if float(volume) != 0:
      v_over_n_html = "n/a"
      if non_h_accounted_for != 0:
        v_over_n = float(volume) / non_h_accounted_for
        if v_over_n < 20:
          v_over_n_html = "<font color='%s'><b>%.1f </b></font>" % (gui_red, v_over_n)
        elif v_over_n > 50:
          v_over_n_html = "<font color='%s'><b>%.1f </b></font>" % (gui_red, v_over_n)
        else:
          v_over_n_html = "<font color='%s'><b>%.1f </b></font>" % (gui_green, v_over_n)
    try:
      float(content_disp)
      content_disp = ""
    except:
      pass

    d['v_over_n'] = v_over_n_html
    d['content_disp'] = content_disp
    d['multi_idx'] = ":".join(multi_idx)
    content = get_template('mask_content_with_edit', path=template_path, force=debug) % d
    details = '<a href="spy.add_mask_content(%s,detail)"> (Edit)</a>' % ":".join(multi_idx)
    d['content'] = content
    d['details'] = details
    d['e_accounted_for_display'] = e_accounted_for_display
    d['electron_bg'] = electron_bg
    d['electron_fg'] = electron_fg
    d['electrons_disp'] = electron / f
    d['volume_disp'] = volume / f
    d['e_accounted_for_raw'] = electrons_accounted_for
    t += get_template('mask_output_table_row_rp', path=template_path, force=debug) % d
  t += get_template('mask_output_based_on', path=template_path, force=debug) % d

  #-- FINAL BLOCK ###############

  total_formula = get_rounded_formula()
  total_electrons_accounted_for = 0
  add_to_formula = ""
  add_to_moiety = ""

  for entry in sum_content:
    entity = entry[1]
    if "?" in entity:
      add_to_moiety = "[+ solvents]"
      continue
    multiplicity = float(entry[0])
    entity, multi = split_entity(entity)
    multi = float(multi)
    ent = moieties.get(entity.lower(), entity)
    ent_disp = ent.replace(" ", "")
    ent = " ".join(re.findall(r'\d+|[A-Z][a-z]*', ent))
    ent = formula_cleaner(str(ent))
    try:
      total_electrons_accounted_for += get_sum_electrons_from_formula(ent)[0] * user_number * number_of_symm_op
    except:
      total_electrons_accounted_for += 0
    f = number_of_symm_op * Zprime
    add_to_formula = _add_formula(add_to_formula, ent, multi / f * multiplicity)
    add_to_moiety += "%s[%s], " % (format_number(multi / f * multiplicity), ent_disp)

  total_formula = _add_formula(total_formula, add_to_formula, 1)
  add_to_moiety = add_to_moiety.rstrip(", ")
  if not add_to_moiety:
    add_to_moiety = OV.GetVar(get_sqf_name() + "_add_to_moiety", "")
  OV.SetVar(get_sqf_name() + "_add_to_moiety", add_to_moiety)
  suggested_moiety = "%s, %s" % (olx.xf.latt.GetMoiety(), add_to_moiety)
  if "[+ solvents]" in suggested_moiety:
    olex.m("spy.set_cif_item(_chemical_formula_moiety,'%s')" % suggested_moiety)

  total_void_no_plural = ""
  if total_void_no > 1:
    total_void_no_plural = "s"

  d['suggested_moiety'] = suggested_moiety
  d['add_to_moiety'] = add_to_moiety
  d['suggested_sum'] = total_formula.replace(".0 ", " ")
  d['add_to_formula'] = add_to_formula.replace(".0 ", " ")
  d['base'] = base
  d['current_sNum'] = current_sNum
  d['escaped_model_src'] = escape_param_names(OV.ModelSrc())

  d['total_void_electrons'] = total_void_electrons
  d['total_void_accounted_for_electrons'] = total_void_accounted_for_electrons
  d['total_void_volume'] = total_void_volume
  d['total_void_no_plural'] = total_void_no_plural
  d['total_void_no'] = total_void_no

  # If auto-add is on, updat the formulae
  if bool(OV.GetParam('snum.refinement.auto_add_masked_moieties')):
    if olx.xf.GetFormula() != d['suggested_sum']:
      olx.xf.SetFormula("%(suggested_sum)s" % d)
    if add_to_moiety not in olx.xf.latt.GetMoiety():
      olex.m("spy.set_cif_item(_chemical_formula_moiety,'%s')" % suggested_moiety)

  # Set the background colour of the Formula + and Moiety + buttons.
  if add_to_moiety not in OV.get_cif_item('_chemical_formula_moiety'):
    if OV.IsControl("ADD_TO_MASK_MOIETY"):
      olx.html.SetBG("ADD_TO_MASK_MOIETY", gui_red)
      OV.SetVar("ADD_TO_MASK_MOIETY_BG", gui_red)
  else:
    OV.SetVar("ADD_TO_MASK_MOIETY_BG", OV.GetParam('gui.green').hexadecimal)

  if gui.tools.is_masked_moiety_in_formula(olx.xf.GetFormula('', 3)):
    if OV.IsControl("ADD_TO_MASK_FORMULA"):
      olx.html.SetBG("ADD_TO_MASK_FORMULA", gui_red)
      OV.SetVar("ADD_TO_MASK_FORMULA_BG", gui_red)
  else:
    OV.SetVar("ADD_TO_MASK_FORMULA_BG", gui_green)
  ####################################################################

  template_value = get_template('mask_special_detail_default', path=template_path, force=debug) % d
  template_value = template_value.strip()
  if mask_special_details:
    if "[]" in mask_special_details:
      mask_special_details = template_value

  if mask_special_details == "?" or not mask_special_details or mask_info_has_updated:
    mask_special_details = template_value
    mask_info_has_updated = False
  if mask_special_details == template_value:
    OV.SetParam('snum.masks.special_detail_colour', gui_red)
    OV.SetParam('snum.masks.special_detail_button_text', 'Use & Edit')
  else:
    OV.SetParam('snum.masks.special_detail_colour', gui_green)
    OV.SetParam('snum.masks.special_detail_button_text', 'Edit')
    # if add_to_formula:
      #mask_special_details = get_template('mask_special_detail_default', path=template_path, force=debug)%d
    # else:
      #mask_special_details = ""
  if mask_special_details:
    mask_special_details = mask_special_details.strip().lstrip('"').rstrip('"').replace("\r", " ")
  if mask_info_has_updated:
    olx.cif_model[current_sNum]['_%s_special_details' % base] = mask_special_details
    update_sqf_file(current_sNum, '_%s_special_details' % base)
  if mask_special_details is None:
    mask_special_details = ''
  d['mask_special_details'] = mask_special_details
  d['mask_special_details_vn'] = mask_special_details_vn
  d['ADD_TO_MASK_FORMULA_BG'] = OV.GetVar('ADD_TO_MASK_FORMULA_BG')
  OV.SetVar(mask_special_details_vn, mask_special_details)

  if add_to_formula:
    if not OV.GetParam('snum.refinement.auto_add_masked_moieties'):
      t += get_template('mask_output_end_rp', path=template_path, force=debug) % d
    t += get_template('mask_special_details', path=template_path, force=debug) % d
  t += get_template('mask_output_table_end', path=template_path, force=debug) % d
  OlexVFS.write_to_olex(output_fn, t)
  return output_fn


OV.registerFunction(get_mask_info, False, 'gui.tools')


def get_moieties_from_list():
  moieties = {}
  _ = os.path.join(OV.DataDir(), 'moieties.cvs')
  if os.path.exists(_):
    pass
  else:
    _ = os.path.join(p_path, 'moieties.csv')
  rFile = open(_, 'r').readlines()
  for line in rFile:
    if line.startswith("#") or line == '\n':
      continue
    nick, formula = line.split(";")
    nick = nick.strip()
    formula = formula.strip()
    if nick and formula:
      moieties.setdefault(nick, formula)
  return moieties


moieties = get_moieties_from_list()


import decimal
import random


def get_rounded_formula(rnd=2, as_string_sep=""):
  # get actual and not user formula
  formula = olx.xf.GetFormula('list', rnd, True)
  if as_string_sep:
    formula = formula.split(",")
    formula = as_string_sep.join(formula).replace(":", "")
  return formula

# def format_number(num):
  # return round(num,3)


def format_number(num):
  if "." in str(num):
    _ = str(num).split(".")[1]
    if _.startswith('99'):
      num = round(num, 0)
    elif _.startswith('00'):
      num = round(num, 0)
  s = str(num)
  if s.endswith(".0"):
    retVal = int(num)
  elif s.endswith(".5"):
    retVal = round(num, 1)
  elif s.endswith(".25") or s.endswith(".25"):
    retVal = round(num, 2)

  else:
    retVal = round(num, 3)
  return retVal


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
  return Z, N


def split_entity(entry):
  try:
    entry = entry.strip()
    entity = entry.lstrip('0123456789./(')
    multi = entry[:(len(entry) - len(entity))]
    if not multi:
      multi = 1
    else:
      if "/" in multi:
        #multi = float(multi.split("/")[0])/float(multi.split("/")[1])
        multi = Fraction(int(multi.split("/")[0]), int(multi.split("/")[1]))
    entity = entity.strip().rstrip("(")
  except:
    entity = ""
    multi = 1
  return entity, multi


# !HP remove once updated in main!
#from gui.tools import Templates
# class TemplatesTemp(object):
  # def __init__(self,):
    #nparent = gui.tools.TemplateProvider
    #self.parent.get_all_templates = self.get_all_templates

  # def get_all_templates(self, path=None, mask="*.*", marker='{-}'):
    # '''
    # Parses the path for template files.
    # '''
    # if not path:
      #path = os.path.join(OV.BaseDir(), 'util', 'pyUtil', 'gui', 'templates')
    # if path[-4:-3] != ".": #i.e. a specific template file has been provided
      #g = glob.glob("%s%s%s" %(path,os.sep,mask))
    # else:
      #g = [path]
    # for f_path in g:
      #fc = open(f_path, 'r').read()
      # if not self.parent._extract_templates_from_text(fc,marker=marker):
        #name = os.path.basename(os.path.normpath(f_path))
        #self.templates[name] = fc
# TemplatesTemp()

cleaned_formulae = {}


def formula_cleaner(formula):
  formula = formula.replace(" ", "").replace(" ", "")
  # formula = unicode(formula) #py3HP
  if formula in cleaned_formulae:
    return cleaned_formulae[formula]
  retVal = ""
  el = ""
  n = ""
  i = 0
  for char in formula:
    if str.isnumeric(char) or str.isspace(char) or str.islower(char):
      continue
    while str.isalpha(char):
      i += 1
      if not el:
        el += char
      else:
        if str.islower(char):
          el += char
        elif str.isupper(char):
          n = "1"
          i -= 1
          break
      char = formula[i:(i + 1)]
    while str.isnumeric(char):
      i += 1
      n += char
      char = formula[i:(i + 1)]
    if el and n == "":
      n = 1
    retVal += "%s%s " % (el, n)
    n = ""
    el = ""
  if debug:
    print("%s --> %s" % (formula, retVal.strip()))
  cleaned_formulae[formula] = retVal
  return retVal.strip()


def update_metacif(sNum, file_name):
  pass
  ciflist = OV.GetCifMergeFilesList()
  if file_name not in ciflist:
    gui.report.publication.add_cif_to_merge_list.__func__(file_name)

  try:
    olex.m("spy.gui.report.publication.add_cif_to_merge_list(%s)" % file_name)
  except:
    return

  # ATTEMPT 2
  from CifInfo import CifTools
  CT = CifTools()
  CT.update_cif_block(olx.cif_model[sNum], force=True)

  # ATTEMPT 1
  #metacif_path = '%s%s%s.metacif' %(OV.StrDir(), os.sep, sNum)
  # with open(metacif_path, 'wb') as f:
    #print >> f, olx.cif_model[sNum]
  # olex.m('cifmerge')


def get_sqf_name(full=True, base=None):
  if not base:
    base = _get_mask_base()
  if full:
    l = [".sqf", "_sq.sqf", "_sqd.sqf"]
    for ending in l:
      if "platon" in base.lower():
        if "_sq" not in ending:
          continue
      retVal = os.path.splitext(OV.HKLSrc())[0] + ending
      if os.path.exists(retVal):
        return retVal
  else:
    retVal = "%s.sqf" % (current_sNum)
  return retVal


def edit_mask_special_details(txt, base, sNum):
  user_value = str(OV.GetUserInput(0, "Edit _mask_special_details", txt))
  if user_value == "None":
    return
  if user_value:
    olx.cif_model[current_sNum]['_%s_special_details' % base] = user_value
    update_sqf_file(current_sNum, '_%s_special_details' % base)
    OV.SetParam('snum.masks.special_detail_colour', gui_green)
    OV.SetParam('snum.masks.special_detail_button_text', 'Edit')
    OV.UpdateHtml(force=True)


OV.registerFunction(edit_mask_special_details)


def update_sqf_file(current_sNum, scope, scope2=None):
  sqf_file = get_sqf_name()
  if os.path.exists(sqf_file):
    with open(sqf_file, 'r') as original:
      data = original.read()
    with open(sqf_file, 'w') as modified:
      modified.write("data_%s\n" % OV.ModelSrc() + data)
    with open(sqf_file, 'r') as f:
      cif_block = iotbx.cif.reader(file_object=f).model()

    if not scope2:
      cif_block[current_sNum][scope] = olx.cif_model[current_sNum][scope]
    else:
      cif_block[current_sNum][scope][scope2] = olx.cif_model[current_sNum][scope][scope2]

    with open(sqf_file, 'w') as f:
      print(cif_block, file=f)

    if os.path.exists(sqf_file.replace(".sqf", ".cif")):
      CifInfo.MergeCif()


def _get_mask_base():
  if OV.IsControl('SNUM_REFINEMENT_RECOMPUTE_MASK_BEFORE_REFINEMENT_PRG'):
    base = olx.html.GetValue('SNUM_REFINEMENT_RECOMPUTE_MASK_BEFORE_REFINEMENT_PRG').lower()
    if "platon" in base.lower():
      base = "platon_squeeze"
    elif "olex2" in base.lower():
      base = "smtbx_masks"
  else:
    if OV.HKLSrc().rstrip(".hkl").endswith("_sq"):
      base = "platon_squeeze"
    else:
      base = "smtbx_masks"
  return base


def add_mask_content(i, which):
  global mask_info_has_updated
  global current_sNum
  current_sNum = OV.ModelSrc()

  base = _get_mask_base()

  is_CIF = (olx.IsFileType('cif') == 'true')
  if ":" not in i:
    i_l = [str(i)]
  else:
    i_l = i.split(":")
  current_sNum = OV.ModelSrc()
  contents = olx.cif_model[current_sNum].get('_%s_void_%s' % (base, which))
  if not contents:
    if is_CIF:
      contents = olx.Cif('_%s_void_nr' % base).split(",")
    else:
      contents = olx.cif_model[current_sNum].get('_%s_void_%s' % (base, which))
  if not contents:
    return return_note(note="No void has been found.", col=gui_orange)

  try:
    disp = ",".join(i_l)
  except:
    disp = "fix me!"

  based_on = OV.GetParam('user.masks.based_on')
  based_on_display = "Asymmetric unit"
  if based_on == "FU":
    based_on_display = "Formula Unit"
  elif based_on == "Cell":
    based_on_display = "Unit Cell"

  f = get_adjust_for_base_factor()
  c = contents[int(i_l[0].split("|")[0]) - 1]
  multiplicity = int(i_l[0].split("|")[1])

  if c == "?":
    c = ""
  c = c.lstrip("'").rstrip("'")

  c_l = c.split(",")
  c_new_l = []
  for c in c_l:
    c = c.strip()
    n = 1
    m = c
    if " " in c:
      n, m = c.split()
      n = format_number(multiplicity * float(n) / f)

    if m != "?" and m != "":
      c = "%s %s" % (n, m)
    else:
      c = m
    c_new_l.append(c)
  c = ", ".join(c_new_l)

  user_value = str(OV.GetUserInput(0, "Edit Mask %s for Void No %s based on %s" % (which, disp, based_on_display), c)).strip()
  if user_value == "None":
    return
  if not user_value:
    user_value = "?"

  user_value_l = user_value.split(",")
  user_value_new_l = []
  for string in user_value_l:
    string = string.lstrip().rstrip()
    if " " in string:
      val, entity = string.split()
    elif "(" in string:
      val, entity = string.split("(")
      val = int(val)
      entity = entity.rstrip().rstrip(")")

    else:
      entity = string
      val = "1"
    if "/" in val:
      _ = val.split("/")
      val = Fraction(int(_[0]), int(_[1]))
    _ = format_number(float(val) * f / multiplicity)
    user_value_new_l.append("%s %s" % (format_number(float(val) * f / multiplicity), entity))
  user_value = ",".join(user_value_new_l)

  _ = list(contents)
  for idx in i_l:
    idx = int(idx.split("|")[0]) - 1
    _[idx] = user_value

  #mask = OV.get_cif_item('_%s_void' %base)
  olx.cif_model[current_sNum]['_%s_void' % base]['_%s_void_content' % base] = _
  update_sqf_file(current_sNum, '_%s_void' % base, '_%s_void_content' % base)

  mask_info_has_updated = True
  # olex.m("spy.makeFormulaForsNumInfo()")
  get_mask_info()
  OV.UpdateHtml(force=True)
#  change_based_on_button_states()


def get_adjust_for_base_factor():
  Z = float(olx.xf.au.GetZ())
  Zprime = float(olx.xf.au.GetZprime())
  number_of_symm_op = round(Z / Zprime)
  based_on = OV.GetParam('user.masks.based_on')
  if based_on == "ASU":
    f = number_of_symm_op
  elif based_on == "FU":
    f = number_of_symm_op * Zprime
  elif based_on == "Cell":
    f = 1
  return round(f)


def _add_formula(curr, new, multi=1):
  if "," in curr:
    curr_l = curr.split(",")
  else:
    curr_l = curr.split()
  new_l = new.split()
  updated_d = {}

  # if len(new_l) == 1:
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
      if i == 1:  # don't mulitply the already existing bits
        tail = round(tail * multi, 2)
      updated_d.setdefault(head, 0)
      updated_d[head] += tail
    i += 1
  l = []
  l_beginning = []
  for item in updated_d:
    if item == "C" or item == "H":
      l_beginning.append("%s%s " % (item, format_number(updated_d[item])))
    else:
      l.append("%s%s " % (item, format_number(updated_d[item])))
  l.sort()
  l_beginning.sort()
  l = l_beginning + l

  retVal = ""
  for item in l:
    retVal += item
  return retVal


def status_bg(var, val, status='on'):
  var = OV.GetParam(var)
  if var.lower() == val.lower():
    return gui_highlight


OV.registerFunction(status_bg)


def return_note(note, note_details="", col=OV.GetVar('HtmlHighlightCOlour')):
  output_fn = '%s_masking_info.htm' % OV.ModelSrc()
  d = {"note": note,
       "note_details": note_details,
       "note_bg": col}
  t = gui.tools.TemplateProvider.get_template('masking_note', path=template_path, force=debug) % d
  OlexVFS.write_to_olex(output_fn, t)
  return output_fn


def escape_param_names(name):
  l = ["[", "]", "(", ")"]
  for item in l:
    name = name.replace(item, "_")
  return name


def change_hklsrc_according_to_mask_prg(prg):
  OV.SetParam('snum.refinement.recompute_mask_before_refinement_prg', prg)
  target = ""

  # sort_out_masking_hkl()
  #import glob
  #files_to_delete = glob.glob("*.sqf")
  # for fn in files_to_delete:
    # os.remove(fn)

  if target and OV.HasGUI() and OV.IsControl("SET_REFLECTIONS_parent_name"):
    olx.html.SetBG('SET_REFLECTIONS_parent_name', OV.GetParam('gui.green').hexadecimal)
    olx.html.SetValue('SET_REFLECTIONS_parent_name', os.path.basename(target))
    get_mask_info()
  OV.UpdateHtml(force=True)


def change_based_on_button_states():
  l = ["BASE_ON_CELL", "BASE_ON_FU", "BASE_ON_ASU"]
  based_on = OV.GetParam('user.masks.based_on')
  for btn in l:
    if not OV.IsControl(btn):
      return
    if btn == "BASE_ON_CELL" and based_on == 'Cell':
      state = "true"
    elif btn == "BASE_ON_FU" and based_on == 'FU':
      state = "true"
    elif btn == "BASE_ON_ASU" and based_on == 'ASU':
      state = "true"
    else:
      state = "false"

    if state == "true":
      olx.html.SetBG(btn, 'gui_green')
      l.remove(btn)
      for btn in l:
        olx.html.SetBG(btn, 'gui_light_grey')
      break

def sort_out_masking_hkl():
  pass
  #_ = OV.GetParam("snum.refinement.recompute_mask_before_refinement_prg")
  # if _ == "Platon":
    # if "_sq" not in OV.HKLSrc():
      #fn = OV.HKLSrc().replace(".", "_sq.")
      # if os.path.exists(fn):
        # OV.HKLSrc(fn)
  # else:
    # if "_sq" in OV.HKLSrc():
      #fn = OV.HKLSrc().replace("_sq.", ".")
      # if not os.path.exists(fn):
        #import shutil
        #shutil.copy2(OV.HKLSrc(), fn)
      # OV.HKLSrc(fn)

OV.registerFunction(change_based_on_button_states)
OV.registerFunction(change_hklsrc_according_to_mask_prg)
OV.registerFunction(add_mask_content)
OV.registerFunction(formula_cleaner)
