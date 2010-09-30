import os
import string
import glob
from cStringIO import StringIO
import datetime

import olx
import olex
from ArgumentParser import ArgumentParser
import userDictionaries
import variableFunctions
from olexFunctions import OlexFunctions
OV = OlexFunctions()

import ExternalPrgParameters
SPD, RPD = ExternalPrgParameters.SPD, ExternalPrgParameters.RPD

import iotbx.cif
from iotbx.cif import model
from iotbx.cif import validation
olx.cif_model = None
olex2_reference = """\
;
O. V. Dolomanov, L. J. Bourhis, R. J. Gildea, J. A. K. Howard and H. Puschmann,
OLEX2: a complete structure solution, refinement and analysis program.
J. Appl. Cryst. (2009). 42, 339-341.
;"""


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

OV.registerMacro(ValidateCif, """filepath&;cif_dic&;show_warnings""")

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
    self.update_cif_block(
      {'_audit_creation_date': today.strftime('%Y-%m-%d'),
       '_audit_creation_method': """
;
  Olex2 %s
  (compiled %s, GUI svn.r%i)
;
""" %(OV.GetTag(), OV.GetCompilationInfo(), OV.GetSVNVersion())
    })
    self.update_cif_block(
      {'_computing_molecular_graphics': olex2_reference,
       '_computing_publication_material': olex2_reference
       })

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

  def sort_crystal_dimensions(self):
    dimensions = []
    exptl_crystal_sizes = ('_exptl_crystal_size_min',
                           '_exptl_crystal_size_mid',
                           '_exptl_crystal_size_max')
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
    if colour is None or colour == '?':
      colours = []
      cif_items = ('_exptl_crystal_colour_lustre',
                   '_exptl_crystal_colour_modifier',
                   '_exptl_crystal_colour_primary')
      for item in cif_items:
        value = self.cif_block.get(item)
        if value is not None:
          colours.append(value)
      if colours:
        self.cif_block['_exptl_crystal_colour'] = ' '.join(colours)
    elif (colour in (
      "colourless","white","black","gray","brown","red","pink","orange",
      "yellow","green","blue","violet")):
      self.cif_block.setdefault('_exptl_crystal_colour_primary', colour)

  def update_cif_block(self, dictionary):
    user_modified = OV.GetParam('snum.metacif.user_modified')
    user_removed = OV.GetParam('snum.metacif.user_removed')
    user_added = OV.GetParam('snum.metacif.user_added')
    for key, value in dictionary.iteritems():
      if key.startswith('_') and value not in ('?', '.'):
        if not (user_added is not None and key in user_added or
                user_modified is not None and key in user_modified or
                user_removed is not None and key in user_removed):
          self.cif_block[key] = value
    import iotbx.cif
    if isinstance(dictionary, iotbx.cif.model.block):
      for key, value in dictionary.loops.iteritems():
        self.cif_block[key] = value # overwrite these for now


class SaveCifInfo(CifTools):
  def __init__(self):
    super(SaveCifInfo, self).__init__()
    self.write_metacif_file()

OV.registerFunction(SaveCifInfo)

class EditCifInfo(CifTools):
  def __init__(self):
    """First argument should be 'view' or 'merge'.

    'view' brings up an internal text editor with the metacif information in cif format.
    'merge' merges the metacif data with cif file from refinement, and brings up and external text editor with the merged cif file.
    """
    super(EditCifInfo, self).__init__()
    self.sort_crystal_dimensions()
    self.sort_crystal_colour()
    ## view metacif information in internal text editor
    s = StringIO()
    print >> s, self.cif_model
    text = s.getvalue()
    inputText = OV.GetUserInput(0,'Items to be entered into cif file', text)
    if inputText and inputText != text:
      reader = iotbx.cif.reader(input_string=str(inputText))
      if reader.error_count():
        return
      updated_cif_model = reader.model()
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


class MergeCif(CifTools):
  def __init__(self, edit=False):
    super(MergeCif, self).__init__()
    edit = (edit not in ('False','false',False))
    # check if cif exists and is up-to-date
    cif_path = '%s/%s.cif' %(OV.FilePath(), OV.FileName())
    file_full = OV.FileFull()
    if (not os.path.isfile('%s/%s.cif' %(OV.FilePath(), OV.FileName())) or
        os.path.getmtime(file_full) > os.path.getmtime(cif_path)):
      prg = OV.GetParam('snum.refinement.program')
      method = OV.GetParam('snum.refinement.method')
      if prg == 'smtbx-refine':
        OV.set_refinement_program(prg, 'Full Matrix')
        if not os.path.isfile("%s/%s.vcov" %(OV.FilePath(),OV.FileName())):
          olex.m('refine')
        print "Creating cif:"
        olex.m('CifCreate')
        # pre-merge (info about refinement)
        from cctbx_olex_adapter import OlexCctbxAdapter
        xs = OlexCctbxAdapter().xray_structure()
        cif_block = xs.as_cif_block()
        s = StringIO()
        print >> s, cif_block
        OV.write_to_olex('xs.cif', s.getvalue())
        OV.CifMerge('xs.cif')
      else:
        if method == 'CGLS':
          OV.set_refinement_program(prg, 'Least Squares')
        acta = olx.Ins('ACTA')
        if acta == 'n/a':
          olx.AddIns('ACTA')
        olex.m('refine')

    ## merge metacif file with cif file from refinement
    OV.CifMerge(self.metacif_path)
    ## open merged cif file in external text editor
    if edit:
      OV.external_edit('filepath()/filename().cif')
OV.registerFunction(MergeCif)


class ExtractCifInfo(CifTools):
  def __init__(self):
    super(ExtractCifInfo, self).__init__()
    self.ignore = ["?", "'?'", ".", "'.'"]
    self.versions = {"default":[],"smart":{},"saint":{},"shelxtl":{},"xprep":{},"sad":{}, "twin":{}, "abs":{}}
    self.metacif = {}
    self.metacifFiles = MetacifFiles()
    self.run()
    olx.cif_model = self.cif_model

  def run(self):
    self.userInputVariables = OV.GetParam("snum.metacif.user_input_variables")
    basename = self.filename
    path = self.filepath
    merge_cif_file = "%s/%s" %(path, "fileextract.cif")
    cif_file = "%s/%s%s" %(path, basename, ".cif")
    tmp = "%s/%s" %(path, "tmp.cif")

    info = ""
    for p in glob.glob(os.path.join(path, basename + ".cif")):
      info = os.stat(p)

    versions = self.get_def()

    import History
    active_solution = History.tree.active_child_node
    if active_solution is not None and active_solution.is_solution:
      solution_reference = SPD.programs[active_solution.program].reference
      atom_sites_solution_primary = SPD.programs[active_solution.program].methods[active_solution.method].atom_sites_solution
      OV.SetParam('snum.metacif.computing_structure_solution', solution_reference)
      OV.SetParam('snum.metacif.atom_sites_solution_primary', atom_sites_solution_primary)

    p = self.sort_out_path(path, "frames")
    if p and self.metacifFiles.curr_frames != self.metacifFiles.prev_frames:
      try:
        import bruker_frames
        frames = bruker_frames.reader(p).cifItems()
        self.update_cif_block(frames)
      except:
        print "Error reading Bruker frame file %s" %p

    p = self.sort_out_path(path, "smart")
    if p and self.metacifFiles.curr_smart != self.metacifFiles.prev_smart:
      try:
        import bruker_smart
        smart = bruker_smart.reader(p).cifItems()
        computing_data_collection = self.prepare_computing(smart, versions, "smart")
        smart.setdefault("_computing_data_collection", computing_data_collection)
        self.update_cif_block(smart)
      except:
        print "Error reading Bruker SMART file %s" %p

    p = self.sort_out_path(path, "p4p")
    if p and self.metacifFiles != self.metacifFiles.prev_p4p:
      try:
        from p4p_reader import p4p_reader
        p4p = p4p_reader(p).read_p4p()
        self.update_cif_block(p4p)
      except:
        print "Error reading p4p file %s" %p

    p = self.sort_out_path(path, "integ")
    if p and self.metacifFiles.curr_integ != self.metacifFiles.prev_integ:
      try:
        import bruker_saint_listing
        integ = bruker_saint_listing.reader(p).cifItems()
        computing_data_reduction = self.prepare_computing(integ, versions, "saint")
        computing_data_reduction = string.strip((string.split(computing_data_reduction, "="))[0])
        integ.setdefault("_computing_data_reduction", computing_data_reduction)
        integ["computing_data_reduction"] = computing_data_reduction
        self.update_cif_block(integ)
      except:
        print "Error reading Bruker Saint integration file %s" %p

    p = self.sort_out_path(path, "saint")
    if p and self.metacifFiles.curr_saint != self.metacifFiles.prev_saint:
      try:
        import bruker_saint
        saint = bruker_saint.reader(p).cifItems()
        computing_cell_refinement = self.prepare_computing(saint, versions, "saint")
        saint.setdefault("_computing_cell_refinement", computing_cell_refinement)
        computing_data_reduction = self.prepare_computing(saint, versions, "saint")
        saint.setdefault("_computing_data_reduction", computing_data_reduction)
        self.update_cif_block(saint)
      except:
        print "Error reading Bruker saint.ini"

    p = self.sort_out_path(path, "abs")
    if p and self.metacifFiles.curr_abs != self.metacifFiles.prev_abs:
      try:
        import abs_reader
        abs_type = abs_reader.abs_type(p)
        if abs_type == "SADABS":
          sad = abs_reader.reader(p).cifItems()
          version = self.prepare_computing(sad, versions, "sad")
          version = string.strip((string.split(version, "="))[0])
          t = self.prepare_exptl_absorpt_process_details(sad, version)
          sad.setdefault("_exptl_absorpt_process_details", t)
          self.update_cif_block(sad)
        elif abs_type == "TWINABS":
          twin = abs_reader.reader(p).twin_cifItems()
          version = self.prepare_computing(twin, versions, "twin")
          version = string.strip((string.split(version, "="))[0])
          t = self.prepare_exptl_absorpt_process_details(twin, version)
          twin.setdefault("_exptl_absorpt_process_details", t)
          self.update_cif_block(twin)
      except:
        print "There was an error reading the SADABS/TWINABS output file\n'%s'.\nThe file may be incomplete." %(p)

    p = self.sort_out_path(path, "pcf")
    if p and self.metacifFiles.curr_pcf != self.metacifFiles.prev_pcf:
      try:
        from pcf_reader import pcf_reader
        pcf = pcf_reader(p).read_pcf()
        self.update_cif_block(pcf)
      except:
        print "Error reading pcf file %s" %p

    p = self.sort_out_path(path, "cad4")
    if p and self.metacifFiles.curr_cad4 != self.metacifFiles.prev_cad4:
      try:
        from cad4_reader import cad4_reader
        cad4 = cad4_reader(p).read_cad4()
        self.update_cif_block(cad4)
      except:
        print "Error reading cad4 file %s" %p

    # Oxford Diffraction data collection CIF
    p = self.sort_out_path(path, "cif_od")
    if p and self.metacifFiles.curr_cif_od != self.metacifFiles.prev_cif_od:
      try:
        import iotbx.cif
        f = open(p, 'rUb')
        cif_od = iotbx.cif.reader(input_string=f.read()).model().values()[0]
        self.exclude_cif_items(cif_od)
        f.close()
        self.update_cif_block(cif_od)
      except:
        print "Error reading Oxford Diffraction CIF %s" %p

    # Rigaku data collection CIF
    p = self.sort_out_path(path, "crystal_clear")
    if p and self.metacifFiles.curr_crystal_clear != self.metacifFiles.prev_crystal_clear:
      try:
        import iotbx.cif
        f = open(p, 'rUb')
        cif = iotbx.cif.reader(input_string=f.read()).model()
        for key, cif_block in cif.iteritems():
          if key.lower() not in ('global', 'general'):
            break
        self.exclude_cif_items(cif_block)
        f.close()
        self.update_cif_block(cif_block)
      except:
        print "Error reading Rigaku CIF %s" %p

    # Diffractometer definition file
    diffractometer = OV.GetParam('snum.report.diffractometer')
    try:
      p = userDictionaries.localList.dictionary['diffractometers'][diffractometer]['cif_def']
    except KeyError:
      p = '?'
    if diffractometer not in ('','?') and p != '?' and os.path.exists(p):
      try:
        import cif_reader
        cif_def = cif_reader.reader(p).cifItems()
        self.update_cif_block(cif_def)
      except:
        print "Error reading local diffractometer definition file %s" %p

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

    self.write_metacif_file()

  def exclude_cif_items(self, cif_block):
    # ignore cif items that should be provided by the refinement engine
    exclude_list = ('_cell_length', '_cell_angle', '_cell_volume', '_cell_formula',
                    '_cell_oxdiff', '_symmetry', '_exptl_absorpt_coefficient_mu')
    for item in cif_block:
      for exclude in exclude_list:
        if item.startswith(exclude):
          del cif_block[item]

  def prepare_exptl_absorpt_process_details(self, dictionary, version):
    parameter_ratio = dictionary["parameter_ratio"]
    R_int_after = dictionary["Rint_after"]
    R_int_before = dictionary["Rint_before"]
    ratiominmax = dictionary["ratiominmax"]
    lambda_correction = dictionary["lambda_correction"]

  def prepare_exptl_absorpt_process_details(self, abs, version):
    if abs["abs_type"] == "TWINABS":
      t = ["%s was used for absorption correction.\n" %(version)]
      txt = "\n;\n"
      for component in range(1, int(abs["number_twin_components"])+1):
        #print "component", component
        parameter_ratio = abs["%s"%component]["parameter_ratio"]
        R_int_after = abs["%s"%component]["Rint_after"]
        R_int_before = abs["%s"%component]["Rint_before"]
        ratiominmax = abs["%s"%component]["ratiominmax"]
        lambda_correction = abs["lambda_correction"]
        t.append("For component %s:\n" %(component))
        t.append("R(int) was %s before and %s after correction.\n" %(R_int_before, R_int_after))
        t.append("The Ratio of minimum to maximum transmission is %.2f.\n" %(float(ratiominmax)))
      t.append("The \l/2 correction factor is %s\n;\n" %(lambda_correction))
      for me in t:
        txt = txt + " %s"%me
      exptl_absorpt_process_details = "%s"%txt

    elif abs["abs_type"] == "SADABS":
      parameter_ratio = abs["parameter_ratio"]
      R_int_after = abs["Rint_after"]
      R_int_before = abs["Rint_before"]
      ratiominmax = abs["ratiominmax"]
      lambda_correction = abs["lambda_correction"]

      t = ["%s was used for absorption correction." %(version),
           "R(int) was %s before and %s after correction." %(R_int_before, R_int_after),
           "The Ratio of minimum to maximum transmission is %s." %(ratiominmax),
           "The \l/2 correction factor is %s" %(lambda_correction)]

      txt = " %s\n %s\n %s\n %s" %(t[0], t[1], t[2], t[3])
      exptl_absorpt_process_details = "\n;\n%s\n;\n" %txt
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
		If more than one file is present, the path of the most recent file is returned by default.
		"""

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
      name = "*m"
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
    else:
      return "Tool not found"

    files = []
    for path in glob.glob(os.path.join(directory, name+extension)):
      info = os.stat(path)
      files.append((info.st_mtime, path))
    if files:
      return OV.standardizePath(self.file_choice(files,tool))
    else:
      parent = os.path.dirname(directory)
      files = []
      for path in glob.glob(os.path.join(parent, name + extension)):
        info = os.stat(path)
        files.append((info.st_mtime, path))
      if files:
        return OV.standardizePath(self.file_choice(files,tool))

  def file_choice(self, info, tool):
    """Given a list of files, it will return the most recent file.

		Sets the list of files as a variable in olex, and also the file that is to be used.
		By default the most recent file is used.
		"""
    info.sort()
    info.reverse()
    i = 0
    listFiles = []
    returnvalue = ""
    if self.userInputVariables is None or "%s_file" %tool not in self.userInputVariables:
      for date, file in info:
        a = file.split('/')[-2:]
        shortFilePath = ""
        for bit in a:
          shortFilePath += "/" + bit
        listFiles.append("%s" %shortFilePath)
        i += 1
      files = ';'.join(listFiles)
      try:
        setattr(self.metacifFiles, "prev_%s" %tool, getattr(self.metacifFiles, "curr_%s" %tool))
        OV.SetParam("snum.metacif.list_%s_files" %tool, files)
        setattr(self.metacifFiles, "list_%s" %tool, files)
        OV.SetParam("snum.metacif.%s_file" %tool, listFiles[0])
        setattr(self.metacifFiles, "curr_%s" %tool, info[0])
      except:
        pass
      returnvalue = info[0][1]
    else:
      x = OV.GetParam("snum.metacif.%s_file" %tool)
      if x is not None:
        for date, file in info:
          if x in file:
            setattr(self.metacifFiles,"curr_%s" %tool, (date,file))
            returnvalue = file
          else:
            pass
    if not returnvalue:
      returnvalue = info[0][1]
    else:
      pass
    return returnvalue

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
    return versions

OV.registerFunction(ExtractCifInfo)


############################################################


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
