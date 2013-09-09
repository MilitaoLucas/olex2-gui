import os
import string
import glob
from cStringIO import StringIO
import datetime
import math

import olx
import olex
from ArgumentParser import ArgumentParser
import userDictionaries
import variableFunctions
from olexFunctions import OlexFunctions
OV = OlexFunctions()

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

def timer(which="",leader=" -- "):
  global now
  global sum_totals
  diff = time.time()-now
  sum_totals += diff
  timings.append("%s%s - %.2f s (%.2f)" %(leader, which, diff, sum_totals))
  now = time.time()


class MetacifFiles:
  def __init__(self):
    self.curr_smart = None
    self.curr_saint = None
    self.curr_integ = None
    self.curr_cad4 = None
    self.curr_sad = None
    self.curr_pcf = None
    self.curr_frames = None
    self.curr_p4p = None
    self.curr_cif_od = None
    self.curr_crystal_images = None
    self.curr_crystal_clear = None
    self.curr_cif_def = None
    self.curr_twin = None
    self.curr_abs = None

    self.prev_smart = None
    self.prev_saint = None
    self.prev_integ = None
    self.prev_cad4 = None
    self.prev_sad = None
    self.prev_pcf = None
    self.prev_frames = None
    self.prev_p4p = None
    self.prev_cif_od = None
    self.prev_crystal_images = None
    self.prev_crystal_clear = None
    self.prev_cif_def = None
    self.prev_twin = None
    self.prev_abs = None

    self.list_smart = None
    self.list_saint = None
    self.list_integ = None
    self.list_cad4 = None
    self.list_sad = None
    self.list_pcf = None
    self.list_frames = None
    self.list_p4p = None
    self.list_cif_od = None
    self.list_crystal_images = None
    self.list_crystal_clear = None
    self.list_twin = None
    self.list_abs = None

class ValidateCif(object):
  def __init__(self, args):
    filepath = args.get('filepath', OV.file_ChangeExt(OV.FileFull(), 'cif'))
    cif_dic = args.get('cif_dic', 'cif_core.dic')
    show_warnings=(args.get('show_warnings', True) in (True, 'True', 'true'))
    if os.path.isfile(filepath):
      f = open(filepath, 'rUb')
      cif_model = iotbx.cif.fast_reader(input_string=f.read()).model()
      f.close()
      print "Validating %s" %filepath
      cif_dic = validation.smart_load_dictionary(cif_dic)
      error_handler = cif_model.validate(cif_dic, show_warnings)
      if error_handler.error_count == 0 and error_handler.warning_count == 0:
        print "No errors found"
      if OV.GetParam('user.cif.checkcif.send'):
        olex.m('spy.cif.GetCheckcifReport()')

OV.registerMacro(ValidateCif, """filepath&;cif_dic&;show_warnings""")
#timer('Register ValidateCif')

class CifTools(ArgumentParser):
  def __init__(self):
    super(CifTools, self).__init__()
    self.metacif_path = '%s/%s.metacif' %(OV.StrDir(), OV.FileName())
    self.data_name = OV.FileName().replace(' ', '')
    if olx.cif_model is None or self.data_name not in olx.cif_model.keys():
      if os.path.isfile(self.metacif_path):
        olx.cif_model = self.read_metacif_file()
      else:
        olx.cif_model = model.cif()
        olx.cif_model[self.data_name] = model.block()
    self.cif_model = olx.cif_model
    self.cif_block = olx.cif_model[self.data_name]
    today = datetime.date.today()
    reference_style = OV.GetParam('snum.report.publication_style', 'acta').lower()
    self.olex2_reference_short = "Olex2"

    if reference_style == "acta":

      self.olex2_reference = """
Olex2 %s (compiled %s, GUI svn.r%i)
""" %(OV.GetTag(), OV.GetCompilationInfo(), OV.GetSVNVersion())
    else:
      self.olex2_reference = """
O. V. Dolomanov, L. J. Bourhis, R. J. Gildea, J. A. K. Howard and H. Puschmann,
OLEX2: a complete structure solution, refinement and analysis program.
J. Appl. Cryst. (2009). 42, 339-341.
"""
    self.update_cif_block(
      {'_audit_creation_date': today.strftime('%Y-%m-%d'),
       '_audit_creation_method': """
;
Olex2 %s
(compiled %s, GUI svn.r%i)
;
""" %(OV.GetTag(), OV.GetCompilationInfo(), OV.GetSVNVersion())
    })
    olx.SetVar('olex2_reference_short', self.olex2_reference_short)
    self.update_cif_block(
      {'_computing_molecular_graphics': self.olex2_reference,
       '_computing_publication_material': self.olex2_reference
       }, force=False)
    self.sort_crystal_dimensions()
    self.sort_crystal_colour()
    self.sort_publication_info()
    self.sort_diffractometer()

  def read_metacif_file(self):
    if os.path.isfile(self.metacif_path):
      file_object = open(self.metacif_path, 'rb')
      reader = iotbx.cif.reader(file_object=file_object)
      file_object.close()
      return reader.model()

  def write_metacif_file(self):
    f = open(self.metacif_path, 'wb')
    print >> f, self.cif_model
    f.close()

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
        if value is not None:
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
      if value is not None and "." not in value:
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
    for key, value in dictionary.iteritems():
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
      for key, value in dictionary.loops.iteritems():
        self.cif_block[key] = value # overwrite these for now

  def sort_publication_info(self):
    publ_author_names = OV.GetParam('snum.metacif.publ_author_names')
    if publ_author_names is not None and publ_author_names not in ('?', ''):
      names = publ_author_names.split(';')
      if len(names):
        cif_loop = model.loop(
          header=('_publ_author_name','_publ_author_email','_publ_author_address'))
        for name in names:
          if name != '?':
            email = userDictionaries.people.getPersonInfo(name,'email')
            address = userDictionaries.people.getPersonInfo(name,'address')
            cif_loop.add_row((name, email, address))
          if '_publ_author' in self.cif_block.loops:
            del self.cif_block.loops['_publ_author']
          self.cif_block.add_loop(cif_loop)
    publ_contact_author_name = OV.get_cif_item('_publ_contact_author_name')
    if publ_contact_author_name is not None and publ_contact_author_name != '?':
      if '_publ_contact_author_name' in self.cif_block:
        del self.cif_block['_publ_contact_author_name'] # hack to make things in the right order
      self.cif_block['_publ_contact_author_name'] = publ_contact_author_name
      self.cif_block['_publ_contact_author_email'] \
        = userDictionaries.people.getPersonInfo(publ_contact_author_name,'email')
      self.cif_block['_publ_contact_author_phone'] \
        = userDictionaries.people.getPersonInfo(publ_contact_author_name,'phone')
      self.cif_block['_publ_contact_author_address'] \
        = userDictionaries.people.getPersonInfo(publ_contact_author_name,'address')

class SaveCifInfo(CifTools):
  def __init__(self):
    super(SaveCifInfo, self).__init__()
    self.write_metacif_file()

OV.registerFunction(SaveCifInfo)
#timer('Register SaveCifInfo')

class EditCifInfo(CifTools):
  def __init__(self, append=''):
    """First argument should be 'view' or 'merge'.

    'view' brings up an internal text editor with the metacif information in cif format.
    'merge' merges the metacif data with cif file from refinement, and brings up and external text editor with the merged cif file.
    """
    super(EditCifInfo, self).__init__()
    ## view metacif information in internal text editor
    s = StringIO()
    print >> s, self.cif_model
    text = s.getvalue()
    text += "\n%s" %append
    inputText = OV.GetUserInput(0,'Items to be entered into cif file', text)
    if inputText and inputText != text:
      reader = iotbx.cif.reader(input_string=str(inputText))
      if reader.error_count():
        return
      updated_cif_model = reader.model()
      if '_diffrn_ambient_temperature' in updated_cif_model.values()[0]:
        OV.set_cif_item(
          '_diffrn_ambient_temperature',
          updated_cif_model.values()[0]['_diffrn_ambient_temperature'])
      diff_1 = self.cif_model.values()[0].difference(updated_cif_model.values()[0])
      modified_items = diff_1._set
      removed_items = self.cif_model.values()[0]._set\
                    - updated_cif_model.values()[0]._set
      added_items = updated_cif_model.values()[0]._set\
                  - self.cif_model.values()[0]._set
      user_modified = OV.GetParam('snum.metacif.user_modified')
      user_removed = OV.GetParam('snum.metacif.user_removed')
      user_added = OV.GetParam('snum.metacif.user_added')
      for item in added_items:
        if user_added is None:
          user_added = [item]
        elif item not in user_added:
          user_added.append(item)
      for item in removed_items:
        if user_removed is None:
          user_removed = [item]
        elif item not in user_removed:
          user_removed.append(item)
      for item in modified_items:
        if user_modified is None:
          user_modified = [item]
        elif item not in user_modified:
          user_modified.append(item)
      olx.cif_model = updated_cif_model
      self.cif_model = olx.cif_model
      self.write_metacif_file()
      if user_modified is not None:
        OV.SetParam('snum.metacif.user_modified', user_modified)
      if user_removed is not None:
        OV.SetParam('snum.metacif.user_removed', user_removed)
      if user_added is not None:
        OV.SetParam('snum.metacif.user_added', user_added)

OV.registerFunction(EditCifInfo)
#timer('Register EditCifInfo')


class MergeCif(CifTools):
  def __init__(self, edit=False, force_create=True, evaluate_conflicts=True):
    super(MergeCif, self).__init__()
    edit = (edit not in ('False','false',False))
    # check if cif exists and is up-to-date
    cif_path = '%s/%s.cif' %(OV.FilePath(), OV.FileName())
    file_full = OV.FileFull()
    if (not os.path.isfile(cif_path) or
        os.path.getmtime(file_full) > os.path.getmtime(cif_path) + 10):
      if not force_create:
        return
      if OV.GetParam('user.cif.autorefine_if_no_cif_for_cifmerge'):
        prg = OV.GetParam('snum.refinement.program')
        method = OV.GetParam('snum.refinement.method')
        if prg == 'olex2.refine':
          OV.set_refinement_program(prg, 'Gauss-Newton')
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

    ECI = ExtractCifInfo(evaluate_conflicts=evaluate_conflicts)
    ECI.run()
    self.write_metacif_file()
    ## merge metacif file with cif file from refinement
    OV.CifMerge(self.metacif_path)
    for extra_cif in OV.GetParam('snum.report.merge_these_cifs',[]):
      if extra_cif:
        olx.Cif2Doc(extra_cif)
        merge_name = "%s_doc.cif" %OV.FileName()
        print "Merging with %s" %("%s" %merge_name)
        OV.CifMerge(merge_name)
    self.finish_merge_cif()
    if edit:
      OV.external_edit('filepath()/filename().cif')
  def finish_merge_cif(self):
    pass

OV.registerFunction(MergeCif)


class ExtractCifInfo(CifTools):
  conflict_d = {}

  def __init__(self, evaluate_conflicts=True, run=False):
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
    self.metacif = {}
    self.metacifFiles = MetacifFiles()
    self.evaluate_conflicts=evaluate_conflicts
    if run:
      self.run()
    olx.cif_model = self.cif_model

  def run(self):
    import iotbx.cif
    self.SPD, self.RPD = ExternalPrgParameters.get_program_dictionaries()
    reference_style = OV.GetParam('snum.report.publication_style', 'acta').lower()
    self.userInputVariables = OV.GetParam("snum.metacif.user_input_variables")
    basename = self.filename
    path = self.filepath
    merge_cif_file = "%s/%s" %(path, "fileextract.cif")
    cif_file = "%s/%s%s" %(path, basename, ".cif")
    tmp = "%s/%s" %(path, "tmp.cif")

    info = ""
    for p in OV.ListFiles(os.path.join(path, basename + ".cif")):
      info = os.stat(p)

    versions = self.get_def()

    import History
    active_solution = History.tree.active_child_node
    all_sources_d = {}

    curr_cif_p = OV.file_ChangeExt(OV.FileFull(), 'cif')
    if os.path.exists(curr_cif_p):
      f = open(curr_cif_p, 'rUb')
      current_cif = iotbx.cif.reader(input_string=f.read()).model().values()[0]
      f.close()
      all_sources_d[curr_cif_p] = current_cif

    if active_solution is not None and active_solution.is_solution:

      ## Backwards Compatibility
      if active_solution.program == "smtbx-solve":
        active_solution.program = "olex2.solve"
      ## END
      try:
        if reference_style == 'acta':
          solution_reference = self.SPD.programs[active_solution.program].name
        else:
          solution_reference = self.SPD.programs[active_solution.program].reference
        olx.SetVar('solution_reference_short', self.SPD.programs[active_solution.program].name)
        olx.SetVar('solution_reference_long', solution_reference)
        atom_sites_solution_primary = self.SPD.programs[active_solution.program]\
          .methods[active_solution.method].atom_sites_solution
        force = True
      except:
        atom_sites_solution_primary = '?'
        solution_reference = '?'
        force = False
      self.update_cif_block({
        '_computing_structure_solution': solution_reference,
        '_atom_sites_solution_primary': atom_sites_solution_primary
      }, force = force)
    active_node = History.tree.active_node
    if active_node is not None and not active_node.is_solution:

      ## Backwards Compatibility
      if active_node.program == "smtbx-refine":
        active_node.program = "olex2.refine"
      ## END
      try:
        if reference_style == 'acta':
          refinement_reference = self.RPD.programs[active_node.program].name
        else:
          refinement_reference = self.RPD.programs[active_node.program].reference
        olx.SetVar('refinement_reference_short', self.RPD.programs[active_node.program].name)
        olx.SetVar('refinement_reference_long', refinement_reference)
        force = True
      except:
        refinement_reference = '?'
        force = False
      self.update_cif_block({
        '_computing_structure_refinement': refinement_reference}, force=force)

    ##RANDOM THINGS
    p, pp = self.sort_out_path(path, "frames")
    if p and self.metacifFiles.curr_frames != self.metacifFiles.prev_frames:
      try:
        info = os.stat(p)
        file_time = info.st_mtime
      except:
        print "Error reading Bruker frame file %s" %p
    # OD Data Collection Date
    p, pp = self.sort_out_path(path, "od_frame_date")
    if p:
      try:
        info = os.stat(p)
        file_time = info.st_mtime
        OV.SetParam('snum.report.date_collected', file_time)
      except:
        print "Error reading OD frame Date %s" %p

    # OD Frame Image
    p, pp = self.sort_out_path(path, "od_frame_images")
    if p:
      try:
        #info = os.stat(p)
        #file_time = info.st_mtime
        OV.SetParam('snum.report.frame_image', p)
        OV.SetParam('snum.report.frame_images', pp)
      except:
        print "Error reading OD frame image %s" %p

    # OD Crystal Image
    p, pp = self.sort_out_path(path, "od_crystal_images")
    if pp:
      try:
        OV.SetParam('snum.report.crystal_image', p)
        l = []
        j = len(pp)
        if j <= 5:
          l = pp
        else:
          for i in xrange(6):
            idx = ((i+1) * j/6) - j/5 + 1
            l.append(pp[idx])
        OV.SetParam('snum.report.crystal_images', l)
      except:
        print "Error reading OD crystal image %s" %p

    # OD Notes File
    p, pp = self.sort_out_path(path, "notes_file")
    if p:
      try:
        info = os.stat(p)
        file_time = info.st_mtime
        OV.SetParam('snum.report.data_collection_notes', p)
      except:
        print "Error reading OD crystal image %s" %p

    # Bruker Crystal Image
    p, pp = self.sort_out_path(path, "bruker_crystal_images")
    if pp:
      try:
        OV.SetParam('snum.report.crystal_image', p)
        l = []
        j = len(pp)
        if j <= 5:
          l = pp
        else:
          for i in xrange(6):
            idx = ((i+1) * j/6) - j/5 + 1
            l.append(pp[idx])
        OV.SetParam('snum.report.crystal_images', l)
      except:
        print "Error reading Bruker crystal image %s" %p



    ##THINGS IN CIF FORMAT
    p, pp = self.sort_out_path(path, "smart")
    if p and self.metacifFiles.curr_smart != self.metacifFiles.prev_smart:
      try:
        import bruker_smart
        smart = bruker_smart.reader(p).cifItems()
        computing_data_collection = self.prepare_computing(smart, versions, "smart")
        smart.setdefault("_computing_data_collection", computing_data_collection)
        self.update_cif_block(smart)
        all_sources_d[p] = smart

      except Exception, err:
        print "Error reading Bruker SMART file %s: %s" %(p, err)

    p, pp = self.sort_out_path(path, "p4p")
    if p and self.metacifFiles != self.metacifFiles.prev_p4p:
      try:
        from p4p_reader import p4p_reader
        p4p = p4p_reader(p).read_p4p()
        self.update_cif_block(p4p)
        all_sources_d[p] = p4p
      except:
        print "Error reading p4p file %s" %p

    p, pp = self.sort_out_path(path, "integ")
    if p and self.metacifFiles.curr_integ != self.metacifFiles.prev_integ:
      try:
        import bruker_saint_listing
        integ = bruker_saint_listing.reader(p).cifItems()
        computing_data_reduction = self.prepare_computing(integ, versions, "saint")
        computing_data_reduction = string.strip((string.split(computing_data_reduction, "="))[0])
        integ.setdefault("_computing_data_reduction", computing_data_reduction)
        integ["computing_data_reduction"] = computing_data_reduction
        self.update_cif_block(integ)
        all_sources_d[p] = integ
      except:
        print "Error reading Bruker Saint integration file %s" %p

    p, pp = self.sort_out_path(path, "saint")
    if p and self.metacifFiles.curr_saint != self.metacifFiles.prev_saint:
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
        print "Error reading Bruker saint.ini"

    p, pp = self.sort_out_path(path, "abs")
    if p and self.metacifFiles.curr_abs != self.metacifFiles.prev_abs:
      try:
        import abs_reader
        abs_type = abs_reader.abs_type(p)
        if abs_type == "SADABS":
          sad = abs_reader.reader(p).cifItems()
          sad.setdefault('abs_file', p)
          version = self.prepare_computing(sad, versions, "sad")
          version = string.strip((string.split(version, "="))[0])
          sad.setdefault('version', version)
          t = self.prepare_exptl_absorpt_process_details(sad, version)
          sad.setdefault("_exptl_absorpt_process_details", t)
          self.update_cif_block(sad, force=False)
          all_sources_d[p] = sad
        elif abs_type == "TWINABS":
          twin = abs_reader.reader(p).twin_cifItems()
          twin.setdefault('abs_file', p)
          version = self.prepare_computing(twin, versions, "twin")
          version = string.strip((string.split(version, "="))[0])
          twin.setdefault('version', version)
          t = self.prepare_exptl_absorpt_process_details(twin, version)
          twin.setdefault("_exptl_absorpt_process_details", t)
          self.update_cif_block(twin, force=True)
          all_sources_d[p] = twin
      except Exception, e:
        if 'Unsupported program version' in str(e):
          print "%s for SADABS" %e
        else:
          import traceback
          traceback.print_exc()
          print "There was an error reading the SADABS/TWINABS output file\n" +\
                "'%s'" %p + ".\nThe file may be incomplete."
    else:
      sad = {'_exptl_absorpt_correction_T_max':'.',
             '_exptl_absorpt_correction_T_min':'.',
             '_exptl_absorpt_correction_type':'.',
             '_exptl_absorpt_process_details':'.'}
      self.update_cif_block(sad, force=True)

    p, pp = self.sort_out_path(path, "pcf")
    if p and self.metacifFiles.curr_pcf != self.metacifFiles.prev_pcf:
      try:
        from pcf_reader import pcf_reader
        pcf = pcf_reader(p).read_pcf()
        self.update_cif_block(pcf)
        all_sources_d[p] = pcf
      except:
        print "Error reading pcf file %s" %p

    #p, pp = self.sort_out_path(path, "cad4")
    #if p and self.metacifFiles.curr_cad4 != self.metacifFiles.prev_cad4:
      #try:
        #from cad4_reader import cad4_reader
        #cad4 = cad4_reader(p).read_cad4()
        #self.update_cif_block(cad4)
        #all_sources_d[p] = cad4
      #except:
        #print "Error reading cad4 file %s" %p

    #import iotbx.cif
    #merge_files = OV.GetParam('snum.report.merge_these_cifs',[])
    #merge_files.append(self.metacif_path)
##    if OV.GetParam('snum.report.merge_these_cifs',[])
    #for p in merge_files:
      #if not p or not os.path.exists(p):
        #continue
      #f = open(p, 'rUb')
      #content = f.read().strip()
      #if not content.startswith('data_'):
        #if not '\ndata_' in content:
          #content = "data_n\n" + content
      #f.close()
      #c = iotbx.cif.reader(input_string=content).model().values()[0]
      #self.exclude_cif_items(c)
      #f.close()
      #self.update_cif_block(c, force=False)
      #all_sources_d[p] = c


    # Oxford Diffraction data collection CIF
    p,pp  = self.sort_out_path(path, "cif_od")
    if p: # and self.metacifFiles.curr_cif_od != self.metacifFiles.prev_cif_od:
      try:
        import iotbx.cif
        f = open(p, 'rUb')
        cif_od = iotbx.cif.reader(input_string=f.read()).model().values()[0]
        self.exclude_cif_items(cif_od)
        f.close()
        self.update_cif_block(cif_od, force=False)
        all_sources_d[p] = cif_od
      except:
        print "Error reading Oxford Diffraction CIF %s" %p


    # Rigaku data collection CIF
    p, pp = self.sort_out_path(path, "crystal_clear")
    if p: # and self.metacifFiles.curr_crystal_clear != self.metacifFiles.prev_crystal_clear:
      f = open(p, 'rUb')
      crystal_clear = iotbx.cif.reader(input_string=f.read()).model().values()[0]
      self.exclude_cif_items(crystal_clear)
      f.close()
      self.update_cif_block(crystal_clear, force=False)
      all_sources_d[p] = crystal_clear

      #try:
        #import iotbx.cif
        #f = open(p, 'rUb')
        #cif = iotbx.cif.reader(input_string=f.read()).model()
        #for key, cif_block in cif.iteritems():
          #if key.lower() not in ('global', 'general'):
            #break
        #self.exclude_cif_items(cif_block)
        #f.close()
        #self.update_cif_block(cif_block)
        #all_sources_d[p] = cif_block
      #except:
        #print "Error reading Rigaku CIF %s" %p

    # Diffractometer definition file
    diffractometer = OV.GetParam('snum.report.diffractometer')
    try:
      p = userDictionaries.localList.dictionary['diffractometers'][diffractometer]['cif_def']
    except KeyError:
      p = '?'
    if diffractometer not in ('','?') and p != '?' and os.path.exists(p):
      f = open(p, 'rUb')
      content = "data_diffractometer_def\n" + f.read()
      diffractometer_def = iotbx.cif.reader(input_string=content).model().values()[0]
      self.exclude_cif_items(diffractometer_def)
      f.close()
      self.update_cif_block(diffractometer_def, force=False)
      all_sources_d[p] = diffractometer_def

      #try:
        #import cif_reader
        #cif_def = cif_reader.reader(p).cifItems()
        #self.update_cif_block(cif_def)
        #all_sources_d[p] = cif_block
      #except:
        #print "Error reading local diffractometer definition file %s" %p

    # smtbx solvent masks output file
    mask_cif_path = '%s/%s-mask.cif' %(OV.StrDir(), OV.FileName())
    if (os.path.isfile(mask_cif_path)
        and OV.GetParam('snum.refinement.use_solvent_mask')
        and (OV.GetParam('snum.masks.update_cif')
             or '_smtbx_masks_void' not in self.cif_block)):
      import iotbx.cif
      f = open(mask_cif_path, 'rUb')
      cif_block = iotbx.cif.reader(file_object=f).model().get(self.data_name)
      f.close()
      if cif_block is not None:
        self.cif_block.update(cif_block)
        OV.SetParam('snum.masks.update_cif', False)
    elif (not OV.GetParam('snum.refinement.use_solvent_mask')
          and '_smtbx_masks_void' in self.cif_block):
      del self.cif_block['_smtbx_masks_void']
      if '_smtbx_masks_special_details' in self.cif_block:
        del self.cif_block['_smtbx_masks_special_details']

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
        self.cif_block['_diffrn_ambient_temperature'] = t

    ## I have uncommented these lines below on 18/7/11 - I can't see what they were
    ## doing other than making the wrong temperature make a comeback...
    #if '_diffrn_ambient_temperature' in self.cif_block:
      #self.update_cif_block({
        #'_cell_measurement_temperature': self.cif_block['_diffrn_ambient_temperature']
      #})

    self.write_metacif_file()
    self.all_sources_d = all_sources_d
    if self.evaluate_conflicts:
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
      l = []
      if k in resolved:
        already_resolved += 1
      for ld in self.all_sources_d:
        try:
          val = self.all_sources_d[ld].get(k,'')
          if type(val) == str:
            val = val.strip("'")
          else:
            #print "k is %s" %k
            continue
        except Exception, err:
          print err
        l.append(val)
      ll = set()
      for item in l:
        if not item: continue
        item = item.strip().strip("'").strip('"')
        if item not in ll:
          ll.add(item)
      if len(ll) > 1:
        if k.startswith('_'):
          conflict_count += 1
        self.conflict_d.setdefault(k,{})
        for ld in self.all_sources_d:
          try:
            val = self.all_sources_d[ld].get(k,'')
            if type(val) == str:
              val = val.strip("'")
          except Exception, err:
            print err
          self.conflict_d[k].setdefault(ld,val)

    if conflict_count and not already_resolved:
      print "There is conflicting information in the sources of metadata"
      from gui.metadata import conflicts
      conflicts(True, self.conflict_d)

    elif already_resolved < conflict_count:
      print "%s Out of %s conflicts have been resolved" %(already_resolved, conflict_count)
      from gui.metadata import conflicts
      conflicts(True, self.conflict_d)

    elif conflict_count and already_resolved == conflict_count:
      print "All %s conflicts have been resolved" %(conflict_count)
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
<td></td>
<td bgcolor='%s'><font color='white'>
<b>There is no conflicting information in the sources of metadata</b>
</font><a href='spy.SetParam(snum.metadata.show_all_cif_sources,True)'>Show ALL</a></td></tr>''' %OV.GetParam('gui.green').hexadecimal
      OV.write_to_olex(wFilePath, txt)
#      print "There is NO conflicting information the sources of metadata"


  def exclude_cif_items(self, cif_block):
    # ignore cif items that should be provided by the refinement engine
    exclude_list = ('_cell_length',
                    '_cell_angle',
                    '_cell_volume',
                    '_cell_formula',
                    '_cell_oxdiff',
                    '_symmetry',
                    '_exptl_absorpt_coefficient_mu',
                    '_audit_creation',
                    '_diffrn_reflns_',
                    '_diffrn_measurement_details',
                    '_publ_author',
                    '_atom_type',
                    '_space_group_symop',
                    '_atom_site',
                    )
    for item in cif_block:
      for exclude in exclude_list:
        if item.startswith(exclude):
          del cif_block[item]

  #def prepare_exptl_absorpt_process_details(self, dictionary, version, p):
    #parameter_ratio = dictionary["parameter_ratio"]
    #R_int_after = dictionary["Rint_after"]
    #R_int_before = dictionary["Rint_before"]
    #ratiominmax = dictionary["ratiominmax"]
    #lambda_correction = dictionary["lambda_correction"]

  def prepare_exptl_absorpt_process_details(self, abs, version,):
    if abs["abs_type"] == "TWINABS":
      t = ["%s was used for absorption correction.\n" %abs['version']]
      txt = ""
      for component in range(1, int(abs["number_twin_components"])+1):
        # is single parameter set refined?
        if str(component) not in abs: continue
        comp_d = abs[str(component)]
        t.append("\nFor component %s:\n" %(component))
        t.append("%s was %s before and %s after correction.\n"
                 %(comp_d["R_name"], comp_d["Rint_before"], comp_d["Rint_after"]))
        ratiominmax = comp_d.setdefault("ratiominmax", None)
        if ratiominmax != None:
          t.append("The Ratio of minimum to maximum transmission is %.2f.\n" %(float(ratiominmax)))
        else:
          t.append("The Ratio of minimum to maximum transmission not present.\n")
        t.append("The \l/2 correction factor is %s\n" %(abs["lambda_correction"]))
      for me in t:
        txt = txt + " %s"%me
      if 'Rint_3sig' in abs and 'Rint' in abs:
        txt += "\nFinal HKLF 4 output contains %s reflections, Rint = %s\n (%s with I > 3sig(I), Rint = %s)\n" %(
          abs['Rint_refnum'], abs['Rint'],
          abs['Rint_3sig_refnum'], abs['Rint_3sig'])
      exptl_absorpt_process_details = txt

    elif abs["abs_type"] == "SADABS":
      txt = """
%(version)s was used for absorption correction.
%(R_name)s was %(Rint_before)s before and %(Rint_after)s after correction.
The Ratio of minimum to maximum transmission is %(ratiominmax)s.
The \l/2 correction factor is %(lambda_correction)s.
"""%abs

      exptl_absorpt_process_details = txt
    return exptl_absorpt_process_details

  def prepare_computing(self, dict, versions, name):
    version = dict.get("prog_version","None")
    try:
      versiontext = (versions[name])[version].strip().strip("'")
    except KeyError:
      if version != "None":
        print "Version %s of the programme %s is not in the list of known versions" %(version, name)
      versiontext = "?"
    return versiontext

  def enter_new_version(self, dict, version, name):
    arg = 1
    title = "Enter new version"
    contentText = "Please type the text you wish to see in the CIF for %s %s: \n"%(name, version)
    txt = OV.GetUserInput(arg, title, contentText)
    txt = "'" + txt + "'\n"
    yn = OV.Alert("Olex2", "Do you wish to add this to the list of known versions?", "YN")
    if yn == "Y":
      afile = olexdir + "/util/Cif/" + "cif_info.def"
      afile = open(afile, 'a')
      afile.writelines("\n=%s=     %s=%s =" %(name, version, txt))
      afile.close()
    return txt

  def sort_out_path(self, directory, tool):
    """Returns the path of the most recent file in the given directory of the given type.
Searches for files of the given type in the given directory.
If no files are found, the parent directory is then searched.
If more than one file is present, the path of the most recent file is returned by default."""

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
      name = OV.FileName()
      extension = ".cif_od"
    elif tool == "crystal_clear":
      name = "CrystalClear"
      extension = ".cif"
    elif tool == "od_frame_date":
      name = OV.FileName()
      extension = "_1_1.img"
      directory_l = OV.FileFull().replace('\\','/').split("/")
      directory = ("/").join(directory_l[:-3])
      directory += '/frames'
    elif tool == "od_frame_images":
      name = "*"
      extension = "*.jpg"
      directory_l = OV.FileFull().replace('\\','/').split("/")
      directory = ("/").join(directory_l[:-3])
      directory += '/frames/jpg/'

    elif tool == "bruker_crystal_images":
      name = OV.FileName()
      extension = "*.jpg"
      directory_l = OV.FileFull().replace('\\','/').split("/")
      directory = ("/").join(directory_l[:-3])
      directory += '/%s.vzs' %OV.FileName()
      i = 1
      while not os.path.exists(directory):
        directory = ("/").join(directory_l[:-(3 - i)])
        directory += '/%s.vzs' %OV.FileName()
        i += 1
        if i == 4:
          return None, None

      if OV.FileName() not in directory:
        print "Crystal images found, but crystal name not in path!"
        return None, None

      zip_n = OV.file_ChangeExt(directory, 'zip')
      import zipfile
      z = zipfile.ZipFile(directory, "r")
      l = []
      for filename in z.namelist():
        if filename and ".jpg" in filename:
          l.append(r'%s/%s' %(directory, filename))
      OV.SetParam("snum.metacif.list_crystal_images_files", l)
      setattr(self.metacifFiles, "list_crystal_images_files", l)
      return l[0], l

    elif tool == "od_crystal_images":
      name = OV.FileName()
      extension = "*.jpg"
      directory_l = OV.FileFull().replace('\\','/').split("/")
      directory += '/movie'
      i = 1
      while not os.path.exists(directory):
        directory = ("/").join(directory_l[:-(3 - i)])
        directory += '/movie'
        i += 1
        if i == 4:
          return None, None

      if OV.FileName() not in directory:
        print "Crystal images found, but crystal name not in path!"
        return None, None

      l = []
      for path in OV.ListFiles(os.path.join(directory, "*.jpg")):
        l.append(path)
      OV.SetParam("snum.metacif.list_crystal_images_files", (l))
      setattr(self.metacifFiles, "list_crystal_images_files", (l))
      return l[0], l


    elif tool == "notes_file":
      name = OV.FileName()
      extension = "_notes.txt"
      directory_l = OV.FileFull().replace('\\','/').split("/")
      directory = ("/").join(directory_l[:-3])
    else:
      return None, None

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
        return None, None

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
    if self.userInputVariables is None or "%s_file" %tool not in self.userInputVariables:
      files = ';'.join([file for date, file in info])
      try:
        setattr(self.metacifFiles, "prev_%s" %tool, getattr(self.metacifFiles, "curr_%s" %tool))
        OV.SetParam("snum.metacif.list_%s_files" %tool, files)
        setattr(self.metacifFiles, "list_%s" %tool, files)
        OV.SetParam("snum.metacif.%s_file" %tool, info[0][1])
        setattr(self.metacifFiles, "curr_%s" %tool, info[0])
      except:
        pass
      returnvalue = info[0][1]
    else:
      x = OV.GetParam("snum.metacif.%s_file" %tool)
      if not x:
        return None
      x = os.path.normpath(x)
      if x is not None:
        for date, file in info:
          if x in file:
            setattr(self.metacifFiles,"curr_%s" %tool, (date,file))
            returnvalue = file
    if not returnvalue:
      returnvalue = info[0][1]
    if returnvalue:
      returnvalur = OV.standardizePath(returnvalue)
    return returnvalue, pp

  def get_def(self):
    olexdir = self.basedir
    versions = self.versions
    file = "%s/etc/site/cif_info.def" %self.basedir
    rfile = open(file, 'r')
    for line in rfile:
      if line[:1] == "_":
        versions["default"].append(line)
      elif line[:1] == "=":
        line = string.split(line, "=",3)
        prgname = line[1]
        versionnumber = line[2]
        versiontext = line[3]
        versions[prgname].setdefault(versionnumber, versiontext)
    rfile.close()
    return versions



############################################################

OV.registerFunction(ExtractCifInfo)


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
              ('snum_dimas_diffraction_comment','snum_metacif_diffrn_special_details')
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


for item in timings:
  print item
#print "Total Time: %s" %(time.time() - start)
