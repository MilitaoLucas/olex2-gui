import os
import string
import glob
from io import StringIO
import datetime
import math
import pickle

import olx
import olex
import re
import gui

from ArgumentParser import ArgumentParser
import userDictionaries
import variableFunctions
from olexFunctions import OV
imer = debug = OV.IsDebugging()

import ExternalPrgParameters

import iotbx.cif
from iotbx.cif import model
from iotbx.cif import validation
from libtbx.utils import format_float_with_standard_uncertainty
olx.cif_model = None

import time
global now
now = time.time()
start = now
timings = []
global sum_totals
sum_totals = 0

class MetacifFiles:
  def __init__(self):
    self.tools = [
      'smart', 'saint', 'integ', 'cad4', 'sad', 'pcf', 'frames', 'p4p', 'cif_od',
      'crystal_images', 'crystal_clear', 'cif_def', 'twin', 'abs', 'cfx', 'cfx_LANA']

    for t in self.tools:
      setattr(self, "curr_" + t, None)
      setattr(self, "list_" + t, None)

  def fix_attrs(self):
    for t in self.tools:
      if "curr_" + t not in self.__dict__:
        setattr(self, "curr_" + t, None)
        setattr(self, "list_" + t, None)

class ValidateCif(object):
  def __init__(self, filepath=None, cif_dic='cif_core.dic', show_warnings=True):
    if not filepath:
      filepath = OV.file_ChangeExt(OV.FileFull(), 'cif')
    if os.path.isfile(filepath):
      with open(filepath, 'r') as f:
        cif_model = iotbx.cif.fast_reader(input_string=f.read()).model()
      print("Validating %s" %filepath)
      cif_dic = validation.smart_load_dictionary(cif_dic)
      error_handler = cif_model.validate(cif_dic, show_warnings)
      if error_handler.error_count == 0 and error_handler.warning_count == 0:
        print("No errors found")
      if OV.GetParam('user.cif.checkcif.send'):
        olex.m('spy.cif.GetCheckcifReport()')

OV.registerMacro(ValidateCif, """filepath&;cif_dic&;show_warnings""")

class CifTools(ArgumentParser):
  specials = {
    'snum.report.crystal_mounting_method': '_olex2_exptl_crystal_mounting_method',
    'snum.report.submission_special_instructions': '_olex2_submission_special_instructions',
    'snum.report.submission_original_sample_id': '_olex2_submission_original_sample_id',
    'snum.report.date_submitted': '_olex2_date_sample_submission',
    'snum.report.date_collected': '_olex2_date_sample_data_collection',
    'snum.report.date_completed': '_olex2_date_sample_completion',
  }

  def __init__(self):
    super(CifTools, self).__init__()
    model_src = OV.ModelSrc(force_cif_data=True)
    self.metacif_path = os.path.join(OV.StrDir(), model_src + ".metacif")
    self.data_name = model_src.replace(' ', '')
    just_loaded = False
    if olx.cif_model is None or self.data_name.lower() not in list(olx.cif_model.keys_lower.keys()):
      if os.path.isfile(self.metacif_path):
        olx.cif_model = self.read_metacif_file()
      if olx.cif_model is None:
        olx.cif_model = model.cif()
        olx.cif_model[self.data_name] = model.block()
      # fix for the data name if it comes differet from CifExtract...
      elif self.data_name.lower() not in olx.cif_model.keys_lower.keys()\
           and len(olx.cif_model.keys_lower) == 1:
        sk = list(olx.cif_model.keys())[0]
        olx.cif_model[self.data_name] = olx.cif_model[sk]
        del olx.cif_model[sk]

      just_loaded = True
    self.cif_model = olx.cif_model
    if not olx.cif_model:
      print("The Olex2 metacif file for this structure appears to be empty")
      return
    self.cif_block = olx.cif_model[self.data_name]
    if just_loaded:
      self.update_specials()
    #since reference formatting got changed - clearing the section to avoid
    #accumulation
    date = self.cif_block.get('_audit_creation_date', '')
    if date:
      try:
        if int(date.replace('-', '')) < 20140319:
          self.update_cif_block({'_publ_section_references' : ''}, force=True)
      except:
        self.update_cif_block({'_publ_section_references' : ''}, force=True)
    version = OV.GetProgramVersionByName('Olex2')
    self.olex2_reference_brief = "Olex2 %s (Dolomanov et al., 2009)" %version
    self.olex2_reference = """Dolomanov, O.V., Bourhis, L.J., Gildea, R.J, Howard, J.A.K. & Puschmann, H.
 (2009), J. Appl. Cryst. 42, 339-341."""
    olx.SetVar('olex2_reference_short', self.olex2_reference_brief)
    olx.SetVar('olex2_reference_long', self.olex2_reference)

    self.update_cif_block(
      {'_audit_creation_date': datetime.date.today().strftime('%Y-%m-%d'),
       '_audit_creation_method': 'Olex2 %s\n(compiled %s, GUI svn.r%i)' %(
         OV.GetTag(), OV.GetCompilationInfo(), OV.GetSVNVersion()),
       '_computing_molecular_graphics': self.olex2_reference_brief,
       '_computing_publication_material': self.olex2_reference_brief
    }, force=True)
    self.update_manageable()

  def save_specials(self):
    for special_item, special_cif in CifTools.specials.items():
      sv = OV.GetParam(special_item, '')
      if sv:
        self.cif_block[special_cif] = sv
      elif special_cif in self.cif_block:
        del self.cif_block[special_cif]

  def update_specials(self):
    for special_item, special_cif in CifTools.specials.items():
      if special_cif in self.cif_block:
        OV.SetParam(special_item, self.cif_block[special_cif])
      else:
        sv = OV.GetParam(special_item, '')
        if sv:
          self.cif_block[special_cif] = sv
    author_loop = self.cif_block.get_loop('_publ_author', None)
    if author_loop:
      OV.SetParam('snum.metacif.publ_author_names',
                  ';'.join(author_loop.get('_publ_author_name', [])).replace('"', ''))

  def update_manageable(self):
    self.sort_crystal_dimensions()
    self.sort_crystal_colour()
    self.sort_publication_info()
    self.sort_diffractometer()

  def read_metacif_file(self):
    if os.path.isfile(self.metacif_path):
      try:
        with open(self.metacif_path, 'r') as file_object:
          reader = iotbx.cif.reader(file_object=file_object)
          return reader.model()
      except:
        print("Failed reading the metadata, removing the file")
    return None

  def write_metacif_file(self):
    self.save_specials()
    with open(self.metacif_path, 'w') as f:
      print(self.cif_model, file=f)

  def sort_diffractometer(self):
    if not OV.GetParam('snum.report.diffractometer'):
      OV.SetParam('snum.report.diffractometer',
        self.cif_block.get('_diffrn_measurement_device_type'))


  def sort_crystal_dimensions(self):
    dimensions = []
    exptl_crystal_sizes = ('_exptl_crystal_size_min',
                           '_exptl_crystal_size_mid',
                           '_exptl_crystal_size_max')
    sz = olx.xf.exptl.Size().split('x')
    if sz[0] != '0':
      dimensions = sz
    else:
      for size in exptl_crystal_sizes:
        value = self.cif_block.get(size)
        if value is not None and value != "?":
          dimensions.append(float(value))
    if dimensions:
      dimensions.sort()
      for i in range(len(dimensions)):
        self.cif_block[exptl_crystal_sizes[i]] = str(dimensions[i])

  def sort_crystal_colour(self):
    colour = self.cif_block.get('_exptl_crystal_colour')
#    if colour is None or colour == '?':
    colours = []
    cif_items = ('_exptl_crystal_colour_lustre',
                 '_exptl_crystal_colour_modifier',
                 '_exptl_crystal_colour_primary')
    for item in cif_items:
      value = self.cif_block.get(item)
      if value not in (None, '?', '.'):
        colours.append(value)
    if colours:
      self.cif_block['_exptl_crystal_colour'] = ' '.join(colours)
    elif (colour in (
      "colourless","white","black","gray","brown","red","pink","orange",
      "yellow","green","blue","violet")):
      self.cif_block.setdefault('_exptl_crystal_colour_primary', colour)

  def update_cif_block(self, dictionary, force=False):
    user_modified = OV.GetParam('snum.metacif.user_modified')
    user_removed = OV.GetParam('snum.metacif.user_removed')
    user_added = OV.GetParam('snum.metacif.user_added')
    for key, value in dictionary.items():
      if not isinstance(key, str):
        continue
      if key.startswith('_') and value not in ('?', '.'):
        if force:
          self.cif_block[key] = value
          continue
        if not (user_added is not None and key in user_added or
                user_modified is not None and key in user_modified or
                user_removed is not None and key in user_removed):
          self.cif_block[key] = value
        else:
          pass
      if key == "_exptl_crystal_density_meas":
        self.cif_block[key] = value

#          print("Not updating %s from file" %key)

    # this requires special treatment
#    if '_diffrn_ambient_temperature' in dictionary:
#      OV.set_cif_item(
#        '_diffrn_ambient_temperature', dictionary['_diffrn_ambient_temperature'])
    import iotbx.cif
    if isinstance(dictionary, iotbx.cif.model.block):
      for key, value in dictionary.loops.items():
        self.cif_block[key] = value # overwrite these for now

  def sort_publication_info(self):
    publ_author_names = OV.GetParam('snum.metacif.publ_author_names')
    if publ_author_names is not None and publ_author_names not in ('?', ''):
      names = publ_author_names.split(';')
      if len(names):
        cif_loop = model.loop(
          header=('_publ_author_name', '_publ_author_email', '_publ_author_address'))
        for name in names:
          if name != '?':
            ID = userDictionaries.people.findPersonId(name)
            if ID != None:
              email = userDictionaries.people.getPersonInfo(ID,'email')
              address = userDictionaries.people.getPersonInfo(ID,'address')
              cif_loop.add_row((unicode_to_cif(name), email, unicode_to_cif(address)))
            else:
              cif_loop.add_row((name, "?", "?"))
          if '_publ_author' in self.cif_block.loops:
            del self.cif_block.loops['_publ_author']
          self.cif_block.add_loop(cif_loop)
    publ_contact_author_name = OV.get_cif_item('_publ_contact_author_name')
    if publ_contact_author_name is not None and publ_contact_author_name != '?':
      if '_publ_contact_author_name' in self.cif_block:
        del self.cif_block['_publ_contact_author_name'] # hack to make things in the right order
      ID = userDictionaries.people.findPersonId(publ_contact_author_name,
        OV.get_cif_item('_publ_contact_author_name', None))
      self.cif_block['_publ_contact_author_name'] = publ_contact_author_name
      self.cif_block['_publ_contact_author_email'] \
        = userDictionaries.people.getPersonInfo(ID,'email')
      self.cif_block['_publ_contact_author_phone'] \
        = userDictionaries.people.getPersonInfo(ID,'phone')
      self.cif_block['_publ_contact_author_address'] \
        = userDictionaries.people.getPersonInfo(ID,'address')
      self.cif_block['_publ_contact_author_id_orcid'] \
        = userDictionaries.people.getPersonInfo(ID,'orchid_id')

class SaveCifInfo(CifTools):
  def __init__(self):
    super(SaveCifInfo, self).__init__()
    self.write_metacif_file()

OV.registerFunction(SaveCifInfo)

class EditCifInfo(CifTools):
  def __init__(self, append=''):
    """First argument should be 'view' or 'merge'.

    'view' brings up an internal text editor with the metacif information in cif format.
    'merge' merges the metacif data with cif file from refinement, and brings up and external text editor with the merged cif file.
    """
    super(EditCifInfo, self).__init__()
    ## view metacif information in internal text editor
    s = StringIO()
    self.save_specials()
    print(self.cif_model, file=s)
    text = s.getvalue()
    text += "\n%s" %append
    inputText = OV.GetUserInput(0,'Items to be entered into cif file', text)
    if inputText and inputText != text:
      reader = iotbx.cif.reader(input_string=inputText)
      if reader.error_count():
        return
      updated_cif_model = reader.model()
      updated_values = list(updated_cif_model.values())
      current_values = list(self.cif_model.values())
      if '_diffrn_ambient_temperature' in updated_values[0]:
        OV.set_cif_item('_diffrn_ambient_temperature',
          updated_values[0]['_diffrn_ambient_temperature'])
      diff_1 = current_values[0].difference(updated_values[0])
      modified_items = diff_1._set
      removed_items = current_values[0]._set - updated_values[0]._set
      added_items = updated_values[0]._set - current_values[0]._set
      user_modified = OV.GetParam('snum.metacif.user_modified')
      user_removed = OV.GetParam('snum.metacif.user_removed')
      user_added = OV.GetParam('snum.metacif.user_added')
      for tem in added_items:
        if user_added is None:
          user_added = [tem]
        elif tem not in user_added:
          user_added.append(tem)
      for tem in removed_items:
        if user_removed is None:
          user_removed = [tem]
        elif tem not in user_removed:
          user_removed.append(tem)
      for tem in modified_items:
        if user_modified is None:
          user_modified = [tem]
        elif tem not in user_modified:
          user_modified.append(tem)
      olx.cif_model = updated_cif_model
      self.cif_model = olx.cif_model
      self.cif_block = olx.cif_model[self.data_name]
      self.update_specials()
      self.write_metacif_file()
      if user_modified is not None:
        OV.SetParam('snum.metacif.user_modified', user_modified)
      if user_removed is not None:
        OV.SetParam('snum.metacif.user_removed', user_removed)
      if user_added is not None:
        OV.SetParam('snum.metacif.user_added', user_added)
      OV.update_crystal_size()

OV.registerFunction(EditCifInfo)


class MergeCif(CifTools):
  def __init__(self, edit=False, force_create=True, evaluate_conflicts=True):
    ext = OV.FileExt()
    super(MergeCif, self).__init__()
    edit = (edit not in ('False','false',False))
    # check if cif exists and is up-to-date
    cif_path = os.path.join(OV.FilePath(), OV.FileName()) + ".cif"
    file_full = OV.FileFull()
    if (not os.path.isfile(cif_path) or
        os.path.getmtime(file_full) > os.path.getmtime(cif_path) + 10):
      if not force_create:
        return
      if OV.GetParam('user.cif.autorefine_if_no_cif_for_cifmerge'):
        prg = OV.GetParam('snum.refinement.program')
        method = OV.GetParam('snum.refinement.method')
        if prg.startswith("olex2.refine"):
          OV.set_refinement_program(prg, method)
        else:
          if method == 'CGLS':
            OV.set_refinement_program(prg, 'Least Squares')
        acta = olx.Ins('ACTA')
        if acta == 'n/a':
          olx.AddIns('ACTA')
        olex.m('refine')
      else:
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("There is no cif from a refinement program for merging.")
        print("If there is a cif, it is probably out of date.")
        print("You probably will need to refine your structure again.")
        print("If you are using SHELX, make sure you use the ACTA command.")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        return

    if ext and ext.lower() != "cif":
      ECI = ExtractCifInfo(evaluate_conflicts=evaluate_conflicts)
      ECI.run()
    self.write_metacif_file()
    ## merge metacif file with cif file from refinement
    merge_with = []
    for extra_cif in OV.GetCifMergeFilesList():
      if extra_cif:
        merge_with.append(extra_cif)
    merge_with.append(self.metacif_path+"&force=" + str(OV.GetParam('snum.metadata.force_metacif', False)))
    if len(merge_with) > 1:
      print("Merging with: " + ' '.join([os.path.split(x)[1] for x in merge_with[1:]]))
    OV.CifMerge(merge_with)
    self.finish_merge_cif()
    if edit:
      OV.external_edit('filepath()/filename().cif')
  def finish_merge_cif(self):
    pass

OV.registerFunction(MergeCif)


class ExtractCifInfo(CifTools):
  conflict_d = {}

  def __init__(self, evaluate_conflicts=True, run=False):
    self.state_file = os.path.join(OV.StrDir(), "matacif_cache.pickle")
    ext = OV.FileExt()
    if ext and ext.lower() == "cif":
      return
    super(ExtractCifInfo, self).__init__()
    if evaluate_conflicts or str(evaluate_conflicts).lower() == "true":
      evaluate_conflicts = True
    else:
      evaluate_conflicts = False
    if run or repr(run).lower() == "true":
      run= True
    else:
      run = False
    self.ignore = ["?", "'?'", ".", "'.'"]
    self.versions = {"default":[],"smart":{},"saint":{},"shelxtl":{},"xprep":{},"sad":{}, "twin":{}, "abs":{}}
    self.computing_citations_d = {}
    self.get_computing_citation_d()
    self.metacif = {}
    # restore state
    if os.path.exists(self.state_file):
      self.metacifFiles = pickle.load(open(self.state_file, "rb"))
      self.metacifFiles.fix_attrs()
    else:
      self.metacifFiles = MetacifFiles()

    self.evaluate_conflicts=evaluate_conflicts
    OV.registerFunction(self.conflict_evaluation,True,'extractcifinfo')
    if run:
      self.run()
    olx.cif_model = self.cif_model

  def run(self):
    import iotbx.cif
    self.SPD, self.RPD = ExternalPrgParameters.get_program_dictionaries()
    self.userInputVariables = OV.GetParam("snum.metacif.user_input_variables")
    basename = self.filename
    path = self.filepath

    import History
    active_solution = None if  History.tree is None else History.tree.active_child_node
    all_sources_d = {}

    curr_cif_p = OV.file_ChangeExt(OV.FileFull(), 'cif')
    str_solstion_from_cif = None
    if os.path.exists(curr_cif_p):
      try:
        with open(curr_cif_p, 'r') as f:
          current_cif = list(iotbx.cif.reader(input_string=f.read()).model().values())[0]
          all_sources_d[curr_cif_p] = current_cif
        try:
          str_solstion_from_cif = current_cif.get('_computing_structure_solution', None)
          if str_solstion_from_cif and str_solstion_from_cif == '?':
            str_solstion_from_cif = None
        except:
          pass
      except iotbx.cif.CifParserError as err:
        print("Failed to parse the CIF for conflicts analysis: %s")

    full_references = [self.olex2_reference]
    if active_solution is not None and active_solution.is_solution:
      ## Backwards Compatibility
      active_solution.program = OV.getCompatibleProgramName(active_solution.program)
      ## END
      try:
        prg = self.SPD.programs[active_solution.program]
        # take value from the CIF only if solved with XT
        if "xt" not in prg.name.lower():
          str_solstion_from_cif = None
        if str_solstion_from_cif is None:
          version, full = OV.GetProgramVersionByName(prg.name, returnFlag = True)
          if full:
            solution_reference = version
          else:
            pname = prg.name
            if prg.name.lower().startswith('shelx'):
              pname = prg.name.upper()
            solution_reference = "%s %s (%s)" %(pname, version, prg.brief_reference)
        else:
          solution_reference = str_solstion_from_cif
        full_references.append(prg.reference)
        olx.SetVar('solution_reference_short', prg.brief_reference)
        olx.SetVar('solution_reference_long', prg.reference)
        atom_sites_solution_primary = prg.methods[active_solution.method].atom_sites_solution
        force = True
      except:
        atom_sites_solution_primary = '?'
        solution_reference = '?'
        force = False
      self.update_cif_block({
        '_computing_structure_solution': solution_reference,
        '_atom_sites_solution_primary': atom_sites_solution_primary
      }, force = force)

    active_node = None if History.tree is None else History.tree.active_node

    if active_node is not None and not active_node.is_solution:
      ## Backwards Compatibility
      active_node.program = OV.getCompatibleProgramName(active_node.program)
      ## END
      try:
        prg = self.RPD.programs[active_node.program]
        version = OV.GetProgramVersionByName(prg.name)
        pname = prg.name
        if prg.name.lower().startswith("shelx"):
          pname = prg.name.upper()
        refinement_reference = "%s %s (%s)" %(pname, version, prg.brief_reference)
        full_references.append(prg.reference)
        olx.SetVar('refinement_reference_short', prg.brief_reference)
        olx.SetVar('refinement_reference_long', prg.reference)
        force = True
      except:
        refinement_reference = '?'
        force = False
      self.update_cif_block({
        '_computing_structure_refinement': refinement_reference}, force=force)

    ##RANDOM THINGS
    # OD Data Collection Date
    p, pp, update = self.sort_out_path(path, "od_frame_date")
    if p:
      try:
        info = os.stat(p)
        file_time = time.strftime('%Y-%m-%d', time.localtime(info.st_mtime))
        OV.SetParam('snum.report.date_collected', file_time)
      except:
        print("Error reading OD frame Date %s" %p)

    # OD Frame Image
    def choose_max_6(pp):
      j = len(pp)
      if j <= 5:
        return pp
      else:
        l = []
        for i in range(6):
          idx = ((i+1) * j//6) - j//5 + 1
          l.append(pp[idx])
        return l

    p, pp, update = self.sort_out_path(path, "od_frame_images")
    if p:
      try:
        OV.SetParam('snum.report.frame_image', p)
        OV.SetParam('snum.report.frame_images', pp)
      except:
        if debug:
          print("Error processing OD frame image %s" %p)
        pass

    # Crystal Image
    p, pp, update = self.sort_out_path(path, "crystal_images")
    if pp:
      try:
        OV.SetParam('snum.report.crystal_image', p)
        OV.SetParam('snum.report.crystal_images', choose_max_6(pp))
      except:
        print("Error processing crystal images %s" %p)

    # OD Notes File
    p, pp, update = self.sort_out_path(path, "notes_file")
    if p:
      try:
        OV.SetParam('snum.report.data_collection_notes', p)
      except:
        print("Error processing notes file %s" %p)

    all_sources_d.update(self.read_files(path, save_state=True))
    # Diffractometer definition file
    diffractometer = OV.GetParam('snum.report.diffractometer')
    try:
      p = userDictionaries.localList.dictionary['diffractometers'][diffractometer]['cif_def']
    except KeyError:
      p = '?'
    if diffractometer not in ('','?') and p != '?' and os.path.exists(p):
      with open(p, 'r') as f:
        content = "data_diffractometer_def\n" + f.read()
        content = content.replace("\xe2\x80\x98", "'")\
          .replace("\xe2\x80\x99", "'")\
          .replace("\xe2\x80\x9c", "\"")\
          .replace("\xe2\x80\x9d", "\"")
        diffractometer_def = list(iotbx.cif.reader(input_string=content).model().values())[0]
        self.exclude_cif_items(diffractometer_def)
      self.update_cif_block(diffractometer_def, force=False)
      all_sources_d[p] = diffractometer_def

    prg = OV.GetParam('snum.refinement.recompute_mask_before_refinement_prg')
    if prg == "Platon":
      mask_cif_path = os.path.splitext(OV.HKLSrc())[0] + "_sqd.sqf"
    else:
      mask_cif_path = os.path.splitext(OV.HKLSrc())[0] + ".sqf"
    # cleanup any and all mask entries -- then put updated values back if the mask is used.
    for i in ('_smtbx_masks_void', '_smtbx_masks_special_details',
              '_smtbx_masks_void_probe_radius', '_smtbx_masks_void_truncation_radius',
              '_platon_squeeze_void', '_platon_squeeze_details', '_platon_squeeze_void_probe_radius', '_platon_squeeze_special_details'):
      if i in self.cif_block:
        del self.cif_block[i]
    if os.path.isfile(mask_cif_path) and OV.GetParam('snum.refinement.use_solvent_mask'):
      import iotbx.cif
      mask_data = open(mask_cif_path, 'r').read()
      if not mask_data.strip().startswith("data"): # PLATON sqf files don't start with the data block line
        new_mask_data = "data_" + self.data_name + "\r\n"
        new_mask_data += "_platon_squeeze_special_details" + " ?" + "\r\n"
        new_mask_data += mask_data
        mask_f = StringIO(new_mask_data)
      else:
        mask_f = StringIO(mask_data)

      cif_block = iotbx.cif.reader(file_object=mask_f).model().get(self.data_name)
      if cif_block is not None and len(cif_block.loops) > 0:
        self.cif_block.update(cif_block)
        OV.SetParam('snum.masks.update_cif', False)

    ## I introduced this condition in order NOT to overwrite the temperature value
    if '_diffrn_ambient_temperature' not in self.cif_block:
      temp = olx.xf.exptl.Temperature()
      if temp != 'n/a':
        temp = temp.split('(')
        t = 273.15 + float(temp[0])
        if len(temp) > 1:
          if '.' in temp[0]:
            precision = len(temp[0].split('.')[1])
          else:
            precision = 0
          su = float(temp[1].split(')')[0]) / math.pow(10, precision)
          t = format_float_with_standard_uncertainty(t, su)
          self.cif_block['_diffrn_ambient_temperature'] = t
        else:
          self.cif_block['_diffrn_ambient_temperature'] = '{:.2f}'.format(t)

    if '_diffrn_ambient_temperature' in self.cif_block and\
       '_cell_measurement_temperature' not in self.cif_block:
      self.update_cif_block({
        '_cell_measurement_temperature': self.cif_block['_diffrn_ambient_temperature']
      })

    self.update_manageable()
    use_aspherical = OV.IsNoSpherA2()
    if use_aspherical:
      NoSpherA2_ref = """Kleemiss, F., Dolomanov, O.V., Bodensteiner, M., Peyerimhoff, N., Midgley, L.,
Bourhis, L.J., Genoni, A., Malaspina, L.A., Jayatilaka, D., Spencer, J.L.,
White, F., Grundkoetter-Stock, B., Steinhauer, S., Lentz, D., Puschmann, H.,
Grabowsky, S. (2021), Chem. Sci., 12, 1675-1692."""
      full_references.append(NoSpherA2_ref)
    if 'current_cif' in locals():
      disp_refine = "_atom_site_dispersion_real" in current_cif
      if disp_refine:
        disp_ref = """Meurer, F., Dolomanov, O.V., Hennig, C., Peyerimhoff, N., Kleemiss, F.,
Puschmann, H., Bodensteiner, M. (2022), IUCrJ, 9, 604-609."""
        full_references.append(disp_ref)
    # merge references
    full_references = [x for x in set(full_references)] #make unique
    current_refs = self.cif_block.get('_publ_section_references', '')
    ref = ""
    full_references_set =\
     set([''.join(x.replace('\r', '').split()) for x in full_references])\
      | ExternalPrgParameters.get_managed_reference_set()
    for l in current_refs.split('\n'):
      if not l.strip():
        if ref:
          ref_t = ''.join(ref.replace('\r', '').split())
          if ref_t not in full_references_set:
            full_references.append(ref)
            full_references_set.add(ref_t)
          ref = ""
      else:
        if ref:
          ref = "%s\n%s" %(ref, l)
        else:
          ref = l
    if ref:
      ref_t = ''.join(ref.replace('\r', '').split())
      if ref_t not in full_references_set:
        full_references.append(ref)
        full_references_set.add(ref_t)

    # clean up if has been inserted previosly but also if added by the user
    # through CifMerge or by hand...
    for x in full_references:
      if "1675-1692" in x and "2021" in x and not use_aspherical:
        full_references.remove(x)
      elif "604-609" in x and "2022" in x and not disp_refine:
        full_references.remove(x)
    full_references.sort()
    self.update_cif_block({
      '_publ_section_references': '\n\n'.join(full_references)}, force=True)

    self.write_metacif_file()
    self.all_sources_d = all_sources_d
    self.conflict_evaluation()

  def read_files(self, path, save_state):
    all_sources_d = {}
    versions = self.get_def()
    ##THINGS IN CIF FORMAT
    p, pp, update = self.sort_out_path(path, "smart")
    if update:
      try:
        import bruker_smart
        smart = bruker_smart.reader(p).cifItems()
        computing_data_collection = self.prepare_computing(smart, versions, "smart")
        smart.setdefault("_computing_data_collection", computing_data_collection)
        self.update_cif_block(smart)
        all_sources_d[p] = smart
      except Exception as err:
        print("Error reading Bruker SMART file %s: %s" %(p, err))

    p, pp, update = self.sort_out_path(path, "p4p")
    if update:
      try:
        from p4p_reader import p4p_reader
        p4p = p4p_reader(p).read_p4p()
        self.update_cif_block(p4p)
        all_sources_d[p] = p4p
      except:
        print("Error reading p4p file %s" %p)

    p, pp, update = self.sort_out_path(path, "integ")
    if update:
      try:
        import bruker_saint_listing
        integ = bruker_saint_listing.reader(p).cifItems()
        computing_data_reduction = self.prepare_computing(integ, versions, "saint")
        computing_data_reduction = computing_data_reduction.split("=")[0].strip()
        integ.setdefault("_computing_data_reduction", computing_data_reduction)
        integ.setdefault("_computing_cell_refinement", computing_data_reduction)
        integ["computing_data_reduction"] = computing_data_reduction
        self.update_cif_block(integ)
        all_sources_d[p] = integ
      except:
        print("Error reading Bruker Saint integration file %s" %p)

    p, pp, update = self.sort_out_path(path, "saint")
    if update:
      try:
        import bruker_saint
        saint = bruker_saint.reader(p).cifItems()
        computing_cell_refinement = self.prepare_computing(saint, versions, "saint")
        saint.setdefault("_computing_cell_refinement", computing_cell_refinement)
        computing_data_reduction = self.prepare_computing(saint, versions, "saint")
        saint.setdefault("_computing_data_reduction", computing_data_reduction)
        self.update_cif_block(saint)
        all_sources_d[p] = saint
      except:
        print("Error reading Bruker saint.ini")

    p, pp, update = self.sort_out_path(path, "abs")
    if update:
      try:
        import abs_reader
        abs_type = abs_reader.abs_type(p)
        if abs_type == "SADABS":
          sad = abs_reader.reader(p).cifItems()
          sad.setdefault('abs_file', p)
          version = self.prepare_computing(sad, versions, "sad")
          version = version.split("=")[0].strip()
          sad.setdefault('version', version)
          t = self.prepare_exptl_absorpt_process_details(sad, version)
          sad.setdefault("_exptl_absorpt_process_details", t)
          self.update_cif_block(sad, force=False)
          all_sources_d[p] = sad
        elif abs_type == "TWINABS":
          twin = abs_reader.reader(p).twin_cifItems()
          twin.setdefault('abs_file', p)
          version = self.prepare_computing(twin, versions, "twin")
          version = version.split("=")[0].strip()
          twin.setdefault('version', version)
          t = self.prepare_exptl_absorpt_process_details(twin, version)
          twin.setdefault("_exptl_absorpt_process_details", t)
          self.update_cif_block(twin, force=True)
          all_sources_d[p] = twin
      except Exception as e:
        if 'Unsupported program version' in str(e):
          print("%s for SADABS" %e)
        else:
          import traceback
          traceback.print_exc()
          print("There was an error reading the SADABS/TWINABS output file\n" +\
                "'%s'" %p + ".\nThe file may be incomplete.")
    else:
      sad = {'_exptl_absorpt_correction_T_max':'.',
             '_exptl_absorpt_correction_T_min':'.',
             '_exptl_absorpt_correction_type':'.',
             '_exptl_absorpt_process_details':'.'}
      self.update_cif_block(sad, force=True)

    p, pp, update = self.sort_out_path(path, "pcf")
    if update:
      try:
        from pcf_reader import pcf_reader
        pcf = pcf_reader(p).read_pcf()
        self.update_cif_block(pcf)
        all_sources_d[p] = pcf
      except:
        print("Error reading pcf file %s" %p)

    manu_cifs = ['cif_od', 'cfx', 'cfx_LANA']
    for manu_cif in manu_cifs:
      p, pp, update  = self.sort_out_path(path, manu_cif)
      if update:
        try:
          with open(p, 'r') as f:
            cif_s = list(iotbx.cif.reader(input_string=f.read()).model().values())[0]
            self.exclude_cif_items(cif_s)
            self.update_cif_block(cif_s, force=False)
            all_sources_d[p] = cif_s
        except Exception as e:
          print("Error reading %s CIF %s. The error was %s" %(manu_cif, p, e))


    # Rigaku data collection CIF
    p, pp, update = self.sort_out_path(path, "crystal_clear")
    sidefile = False
    if update:
      try:
        if sidefile: # what is this supposed to be???
          ciflist = OV.GetCifMergeFilesList()
          if p not in ciflist and os.path.exists(p):
            ## Add this file to list of merged files
            import gui
            gui.report.publication.add_cif_to_merge_list.__func__(p)
        else:
          with open(p, 'r') as f:
            crystal_clear = list(iotbx.cif.reader(input_string=f.read()).model().values())[0]
            self.exclude_cif_items(crystal_clear)
          self.update_cif_block(crystal_clear, force=False)
          all_sources_d[p] = crystal_clear

      except:
        print("Error reading Rigaku CIF %s" %p)

    if save_state:
      pickle.dump(self.metacifFiles, open(self.state_file, "wb"))
    return all_sources_d

  def conflict_evaluation(self, force=False):
    if self.evaluate_conflicts or force:
      ## Check for external CIF files that may want to be merged in as well.
      ## These may not start with the 'data_' identifier, so add it when required.
      l = OV.GetCifMergeFilesList()
      for item in l:
        item = item.strip()
        if not item:
          continue
        if item not in self.all_sources_d:
          try:
            with open(item, 'r') as f:
              _ = f.read()
              if not _.startswith("data"):
                _ = str("data_%s\r\n" %OV.ModelSrc() + _)
              cif_block = list(iotbx.cif.reader(input_string=_).model().values())[0]
              self.exclude_cif_items(cif_block)
              self.all_sources_d.setdefault(item, cif_block)
          except:
            pass
      self.sort_out_conflicting_sources()

  def sort_out_conflicting_sources(self):
    if olx.HasGUI() == 'false':
      return
    self.conflict_d = {}
    d = {}
    l = []
    k_l = set()
    for ld in self.all_sources_d:
      l.append(ld)
      for k in self.all_sources_d[ld]:
        if k not in k_l:
          k_l.add(k)
    self.conflict_d.setdefault('sources',l)

    resolved = OV.GetParam('snum.metadata.resolved_conflict_items')
    show_all_info = OV.GetParam('snum.metadata.show_all_cif_sources',False)

    have_conflicts = False
    already_resolved = 0
    conflict_count = 0
    for k in k_l:
      if not isinstance(k, str):
        continue
      l = []
      if k in resolved:
        already_resolved += 1
      for ld in self.all_sources_d:
        try:
          val = self.all_sources_d[ld].get(k,'')
          if isinstance(val, str):
            val = val.strip("'")
            l.append(val)
          else:
            #print "k is %s" %k
            continue
        except Exception as err:
          print(err)
      ll = set()
      for tem in l:
        if not tem: continue
        tem = tem.strip().strip("'").strip('"')
        if tem not in ll:
          ll.add(tem)
      if len(ll) > 1:
        if k.startswith('_'):
          conflict_count += 1
        self.conflict_d.setdefault(k,{})
        for ld in self.all_sources_d:
          try:
            val = self.all_sources_d[ld].get(k,'')
            if isinstance(val, str):
              val = val.strip("'")
            self.conflict_d[k].setdefault(ld, val)
          except Exception as err:
            print(err)

    if conflict_count and not already_resolved:
      print("There is conflicting information in the sources of metadata")
      from gui.metadata import conflicts
      conflicts(True, self.conflict_d)

    elif already_resolved < conflict_count:
      print("%s Out of %s conflicts have been resolved" %(already_resolved, conflict_count))
      from gui.metadata import conflicts
      conflicts(True, self.conflict_d)

    elif conflict_count and already_resolved == conflict_count:
      print("All %s conflicts have been resolved" %(conflict_count))
      from gui.metadata import conflicts
      conflicts(True, self.conflict_d)
# o: what is this supposed to do?
#    elif show_all_info:
#      print "There are no conflicts. All CIF info is shown in the pop-up window."
#      from gui.metadata import conflicts
#      conflicts(True, self.conflict_d)

    else:
      wFilePath = r"conflicts_html_window.htm"
      txt = '''
<tr>
<td bgcolor='%s'><font color='white'>
<b>There is no conflicting information in the sources of metadata</b>
</font><a href='spy.SetParam(snum.metadata.show_all_cif_sources,True)'>Show ALL</a></td></tr>''' %OV.GetParam('gui.green').hexadecimal
      OV.write_to_olex(wFilePath, txt)
#      print "There is NO conflicting information the sources of metadata"


  def exclude_cif_items(self, cif_block):
    # ignore cif items that should be provided by the refinement engine
    exclude_list = ('_cell_length',
                    '_audit', '_reflns', # These is only here because of STOE files
                    '_cell_angle',
                    '_cell_volume',
                    '_cell_formula',
                    '_cell_oxdiff',
                    '_symmetry',
                    '_exptl_absorpt_coefficient_mu',
                    '_diffrn_reflns_',
                    '_publ_author',
                    '_atom_type',
                    '_space_group_symop',
                    '_atom_site',
                    )
    for item in cif_block:
      for exclude in exclude_list:
        if item.startswith(exclude):
          try:
            del cif_block[item]
          except:
            print("Can't delete CIF item %s" %item)

  #def prepare_exptl_absorpt_process_details(self, dictionary, version, p):
    #parameter_ratio = dictionary["parameter_ratio"]
    #R_int_after = dictionary["Rint_after"]
    #R_int_before = dictionary["Rint_before"]
    #ratiominmax = dictionary["ratiominmax"]
    #lambda_correction = dictionary["lambda_correction"]

  def prepare_exptl_absorpt_process_details(self, ABS, version,):
    if ABS["abs_type"] == "TWINABS":
      t = ["%s was used for absorption correction.\n" %ABS['version']]
      txt = ""
      for component in range(1, int(ABS["number_twin_components"])+1):
        comp_d = ABS.get(str(component), None)
        # is single parameter set refined?
        if comp_d is None: continue
        t.append("\nFor component %s:\n" %(component))
        t.append("%s was %s before and %s after correction.\n"
                 %(comp_d["R_name"], comp_d["Rint_before"], comp_d["Rint_after"]))
        ratiominmax = comp_d.setdefault("ratiominmax", None)
        if ratiominmax != None:
          t.append("The Ratio of minimum to maximum transmission is %.2f.\n" %(float(ratiominmax)))
        if "Not present" not in ABS["lambda_correction"]:
          t.append("The \l/2 correction factor is %s\n" %(ABS["lambda_correction"]))
      for me in t:
        txt = txt + " %s"%me
      if 'Rint_3sig' in ABS and 'Rint' in ABS:
        txt += "\nFinal HKLF 4 output contains %s reflections, Rint = %s\n (%s with I > 3sig(I), Rint = %s)\n" %(
          ABS['Rint_refnum'], ABS['Rint'],
          ABS['Rint_3sig_refnum'], ABS['Rint_3sig'])
      exptl_absorpt_process_details = txt

    elif ABS["abs_type"] == "SADABS":
      txt = """
%(version)s was used for absorption correction.
%(R_name)s was %(Rint_before)s before and %(Rint_after)s after correction.
The Ratio of minimum to maximum transmission is %(ratiominmax)s.
The \l/2 correction factor is %(lambda_correction)s.
"""%ABS

      exptl_absorpt_process_details = txt
    return exptl_absorpt_process_details

  def prepare_computing(self, DICT, versions, name):
    version = DICT.get("prog_version","None")
    try:
      versiontext = (versions[name])[version].strip().strip("'")
    except KeyError:
      if version != "None":
        versiontext = ''
        if '/' in version:
          if name == 'sad':
            versiontext = "SADABS-"
          elif name == 'twin':
            versiontext = "TWINABS-"
          elif name == 'xprep':
            versiontext = "XPREP-"
          else:
            versiontext = "?-"
          if len(versiontext) > 2:
            versiontext += version
            versiontext += " (Bruker,%s)" %version.split(os.sep)[0]
          else:
            versiontext += version
        else:
          versiontext = self.enter_new_version(version, name).strip()
          if not versiontext:
            versiontext = "?"
          else:
            versions[name][version] = versiontext
      else:
        versiontext = "?"
    return versiontext

  def enter_new_version(self, version, name):
    title = "Enter new program version citation for %s %s which you want to appear in the CIF" %(name.upper(), version)
    contentText = "%s %s (?, 2016)" %(name.upper(), version)
    txt = OV.GetUserInput(1, title, contentText)
    if txt:
      afile = os.path.join(OV.DataDir(), "cif_info.def")
      with open(afile, 'a') as afile:
        afile.writelines("\n=%s=%s=     '%s'" %(name, version, txt))
    return txt

  def sort_out_path(self, directory, tool):
    """Returns the path of the most recent file in the given directory of the given type.
Searches for files of the given type in the given directory.
If no files are found, the parent directory is then searched.
If more than one file is present, the path of the most recent file is returned by default."""
    directory_l = OV.FileFull().split(os.sep)
    info = ""
    if tool == "smart":
      name = "smart"
      extension = ".ini"
    elif tool == "saint":
      name = "saint"
      extension = ".ini"
    elif tool == "abs":
      name = "*"
      extension = ".abs"
    elif tool == "sad":
      name = "*"
      extension = ".abs"
    elif tool == "twin":
      name = "*"
      extension = ".abs"
    elif tool == "integ":
      name = "*"
      extension = "._ls"
    elif tool == "cad4":
      name = "*"
      extension = ".dat"
    elif tool == "pcf":
      name = "*"
      extension = ".pcf"
    elif tool == "p4p":
      name = "*"
      extension = ".p4p"
    elif tool == "frames":
      name = "*_1"
      extension = ".001"
    elif tool == "cif_od":
      name = os.path.splitext(os.path.basename(OV.HKLSrc()))[0]
      extension = ".cif_od"
    elif tool == "cfx":
      name = OV.FileName()
      extension = ".cfx"
    elif tool == "cfx_LANA":
      name = OV.FileName()
      extension = ".cfx_LANA"
    elif tool == "crystal_clear":
      name = "CrystalClear"
      extension = ".cif"
    elif tool == "od_frame_date":
      name = OV.FileName()
      extension = "_1_1.img"
      directory = os.sep.join(directory_l[:-3] + ["frames"])
    elif tool == "od_frame_images":
      name = "*"
      extension = "*.jpg"
      directory = os.sep.join(directory_l[:-3] + ["frames", "jpg"])
    elif tool == "crystal_images" or tool == "crystal_images":
      l0, l = gui.tools.find_movie_folder(directory, directory_l)
      setattr(self.metacifFiles, "list_crystal_images_files", l)
      return l0, l, None

    elif tool == "notes_file":
      name = OV.FileName()
      extension = "_notes.txt"
      directory = os.sep.join(directory_l[:-3])
    else:
      return None, None, None

    #normalise name if the SQUEEZEd version is used.
    while name.endswith("_sq"):
      name = name[:-3]
    files = []
    for path in OV.ListFiles(os.path.join(directory, name+extension)):
      info = os.stat(path)
      files.append((info.st_mtime, path))
    if files:
      return self.file_choice(files, tool, "images" in tool)
    else:
      parent = os.path.dirname(directory)
      files = []
      for path in OV.ListFiles(os.path.join(parent, name + extension)):
        info = os.stat(path)
        files.append((info.st_mtime, path))
      if files:
        return self.file_choice(files,tool)
      else:
        return None, None, None

  def file_choice(self, info, tool, multiple=False):
    """Given a list of files, it will return the most recent file.
    Sets the list of files as a variable in Olex2, and also the file that is to
    be used. By default the most recent file is used.
    """
    info.sort()
    pp = None
    if multiple:
      pp = []
      for ifo in info:
        pp.append(OV.standardizePath(ifo[1]))

    info.reverse()

    returnvalue = ""
    curr_date = None
    if self.userInputVariables is None or "%s_file" %tool not in self.userInputVariables:
      files = ';'.join([FILE for date, FILE in info])
      try:
        curr_date = getattr(self.metacifFiles, "curr_%s" %tool)
        if curr_date:
          curr_date = curr_date[0]
        OV.SetParam("snum.metacif.list_%s_files" %tool, files)
        OV.SetParam("snum.metacif.%s_file" %tool, info[0][1])
        setattr(self.metacifFiles, "list_%s" %tool, files)
        setattr(self.metacifFiles, "curr_%s" %tool, info[0])
      except:
        pass
      returnvalue = info[0]
    else:
      x = OV.GetParam("snum.metacif.%s_file" %tool)
      if not x:
        return None, None, False
      x = os.path.normpath(x)
      if x is not None:
        for date, FILE in info:
          if x in FILE:
            setattr(self.metacifFiles,"curr_%s" %tool, (date,FILE))
            returnvalue = (date, FILE)
    if not returnvalue:
      returnvalue = info[0]
    if returnvalue:
      returnvalue = (OV.standardizePath(returnvalue[1]), returnvalue[0])
    return returnvalue[0], pp, returnvalue[1] != curr_date

  def get_def(self):
    versions = self.versions
    afile = os.path.join(OV.DataDir(), "cif_info.def")
    if not os.path.exists(afile):
      import shutil
      FILE = os.path.join(self.basedir, "etc", "site", "cif_info.def")
      shutil.copy(FILE, afile)
    with open(afile, 'r') as rfile:
      for line in rfile:
        if line[:1] == "_":
          versions["default"].append(line)
        elif line[:1] == "=":
          line = line.split("=",3)
          prgname = line[1]
          versionnumber = line[2]
          versiontext = line[3]
          versions[prgname].setdefault(versionnumber, versiontext)
    return versions

  def get_computing_citation_d(self):
    file_path = "%s/etc/site/computing_citations.def" %self.basedir
    with open(file_path, 'r') as rfile:
      for line in rfile:
        line = line.strip()
        if not line or line.startswith("#"):
          continue
        li = line.split("::")
        self.computing_citations_d.setdefault(li[0].strip(), li[1].strip())

############################################################
OV.registerFunction(ExtractCifInfo)

def reloadMetadata(force=False):
  """Reloads metadata stored in metacif file if the file name matches the data
   name or if force is set to True
  """
  try:
    fileName = OV.FileName()
    dataName = OV.ModelSrc()
    metacif_path = os.path.join(OV.StrDir(), dataName + ".metacif")
    dataName = fileName.replace(' ', '')
    #check if the
    if dataName != fileName and not force:
      return
    if os.path.exists(metacif_path):
      with open(metacif_path, 'r') as file_object:
        reader = iotbx.cif.reader(file_object=file_object)
        olx.cif_model = reader.model()
  except Exception as e:
    print("Failed to reload matadata: %s", e)

OV.registerFunction(reloadMetadata, False, "cif")

def getOrUpdateDimasVar(getOrUpdate):
  for var in [('snum_dimas_crystal_colour_base','exptl_crystal_colour_primary'),
              ('snum_dimas_crystal_colour_intensity','exptl_crystal_colour_modifier'),
              ('snum_dimas_crystal_colour_appearance','exptl_crystal_colour_lustre'),
              ('snum_dimas_crystal_name_systematic','chemical_name_systematic'),
              ('snum_dimas_crystal_size_min','exptl_crystal_size_min'),
              ('snum_dimas_crystal_size_med','exptl_crystal_size_mid'),
              ('snum_dimas_crystal_size_max','exptl_crystal_size_max'),
              ('snum_dimas_crystal_shape','exptl_crystal_description'),
              ('snum_dimas_crystal_crystallisation_comment','exptl_crystal_recrystallization_method'),
              ('snum_dimas_crystal_preparation_comment','exptl_crystal_preparation'),
              ('snum_dimas_diffraction_diffractometer','diffrn_measurement_device_type'),
              ('snum_dimas_diffraction_ambient_temperature','snum_metacif_diffrn_ambient_temperature'),
              ('snum_dimas_diffraction_comment','snum_metacif_diffrn_special_details'),
              ('snum.report.diffractometer','_diffrn_measurement_device_type')
              ]:
    if OV.GetParam(var[0]) != OV.GetParam('snum.metacif.%s' %var[-1]):
      if getOrUpdate == 'get':
        value = OV.GetParam(var[0])
        OV.SetParam('snum.metacif%s' %var[-1],value)
      elif getOrUpdate == 'update':
        value = OV.GetParam('snum.metacif.%s' %var[-1])
        OV.SetParam(var[0],value)
    else: continue

def set_source_file(file_type, file_path):
  if file_path != '':
    OV.SetParam('snum.metacif.%s_file' %file_type, file_path)
OV.registerFunction(set_source_file)

def unicode_to_cif(u):
  d = {
    '\xe0':'\`a',
    '\xe8':'\`e',
    '\xec':'\`i',
    '\xf2':'\`o',
    '\xf9':'\`u',

    '\xc0':'\`A',
    '\xc8':'\`E',
    '\xcc':'\`I',
    '\xd2':'\`O',
    '\xd9':'\`U',

    '\xe1':'\'a',
    '\xe9':'\'e',
    '\xed':'\'i',
    '\xf3':'\'o',
    '\xfa':'\'u',
    '\xfd':'\'y',

    '\xc1':'\'A',
    '\xc9':'\'E',
    '\xed':'\'I',
    '\xd3':'\'O',
    '\xda':'\'U',
    '\xdd':'\'Y',

    '\xe2':'\^a',
    '\xea':'\^e',
    '\xee':'\^i',
    '\xf4':'\^o',
    '\xfb':'\^u',

    '\xc2':'\^A',
    '\xca':'\^E',
    '\xce':'\^I',
    '\xd4':'\^O',
    '\xdb':'\^U',

    '\xe3':'\^a',
    '\xf1':'\^n',
    '\xf5':'\^o',

    '\xc3':'\^A',
    '\xd1':'\^N',
    '\xd5':'\^O',

    '\xe7':'\,c',

    '\xc7':'\,C',

 }
  retVal = ''
  for char in u:
    retVal += d.get(char,char)
  return retVal

for item in timings:
  print(item)
#print "Total Time: %s" %(time.time() - start)
