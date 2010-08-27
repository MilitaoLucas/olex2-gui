import os
import string
import glob
from cStringIO import StringIO
import datetime

import olx
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

class cif_manager(object):

  def __init__(self):
    self.metacif_path = '%s/%s.metacif' %(OV.StrDir(), OV.FileName())
    if os.path.exists(self.metacif_path):
      f = open(self.metacif_path, 'rUb')
      self.cif_model = iotbx.cif.fast_reader(input_string=f.read()).model()
      f.close()
    else:
      self.cif_model = iotbx.cif.model.cif()
    self.master_cif_block = self.cif_model.get(OV.FileName())

  def set_data_item(self, key, value):
    self.master_cif_block[key] = value

  def get_data_item(self, key):
    return self.master_cif_block.get(key)


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
    self.list_twin = None
    self.list_abs = None

class CifTools(ArgumentParser):
  def __init__(self):
    super(CifTools, self).__init__()
    self.metacif_path = '%s/%s.metacif' %(OV.StrDir(), OV.FileName())
    if olx.cif_model is None or OV.FileName() not in olx.cif_model.keys():
      if os.path.isfile(self.metacif_path):
        olx.cif_model = self.read_metacif_file()
      else:
        olx.cif_model = model.cif()
        olx.cif_model[OV.FileName()] = model.block()
    self.cif_model = olx.cif_model
    self.cif_block = olx.cif_model[OV.FileName()]
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

  def read_metacif_file(self):
    if os.path.isfile(self.metacif_path):
      reader = iotbx.cif.reader(file_path=self.metacif_path)
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
      value = self.cif_model[OV.FileName()].get(size)
      if value is not None:
        dimensions.append(float(value))
    if dimensions:
      dimensions.sort()
      for i in range(len(dimensions)):
        self.cif_model[OV.FileName()][exptl_crystal_sizes[i]] = str(dimensions[i])

  def sort_crystal_colour(self):
    cif_block = self.cif_model[OV.FileName()]
    colour = cif_block.get('_exptl_crystal_colour')
    if colour is None:
      colours = []
      cif_items = ('_exptl_crystal_colour_lustre',
                   '_exptl_crystal_colour_modifier',
                   '_exptl_crystal_colour_primary')
      for item in cif_items:
        value = cif_block.get(item)
        if value is not None:
          colours.append(value)
      if colours:
        cif_block['_exptl_crystal_colour'] = ' '.join(colours)
    elif (colour in (
      "colourless","white","black","gray","brown","red","pink","orange",
      "yellow","green","blue","violet")):
      cif_block.setdefault('_exptl_crystal_colour_primary', colour)

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

class ValidateCif(object):
  def __init__(self, args):
    filepath = args.get('filepath', OV.file_ChangeExt(OV.FileFull(), 'cif'))
    cif_dic = args.get('cif_dic', 'cif_core.dic')
    show_warnings=(args.get('show_warnings', True) in (True, 'True', 'true'))
    if os.path.exists(filepath):
      f = open(filepath, 'rUb')
      cif_model = iotbx.cif.fast_reader(input_string=f.read()).model()
      f.close()
      cif_dic = validation.smart_load_dictionary(cif_dic)
      cif_model.validate(cif_dic, show_warnings)

OV.registerMacro(ValidateCif, """filepath&;cif_dic&;show_warnings""")

class ViewCifInfo(CifTools):
  def __init__(self):
    """First argument should be 'view' or 'merge'.

		'view' brings up an internal text editor with the metacif information in cif format.
		'merge' merges the metacif data with cif file from refinement, and brings up and external text editor with the merged cif file.
		"""
    super(ViewCifInfo, self).__init__()
    self.sort_crystal_dimensions()
    self.sort_crystal_colour()
    ## view metacif information in internal text editor
    s = StringIO()
    print >> s, self.cif_model
    text = s.getvalue()
    inputText = OV.GetUserInput(0,'Items to be entered into cif file', text)
    if inputText and inputText != text:
      reader = iotbx.cif.fast_reader(input_string=str(inputText))
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

OV.registerFunction(ViewCifInfo)

class MergeCif(CifTools):
  def __init__(self, edit=False):
    super(MergeCif, self).__init__()
    edit = (edit not in ('False','false',False))
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
    merge = []
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
    #active_node = History.tree.active_node
    active_solution = History.tree.active_child_node
    if active_solution is not None and active_solution.is_solution:
      solution_reference = SPD.programs[active_solution.program].reference
      atom_sites_solution_primary = SPD.programs[active_solution.program].methods[active_solution.method].atom_sites_solution
      OV.SetParam('snum.metacif.computing_structure_solution', solution_reference)
      OV.SetParam('snum.metacif.atom_sites_solution_primary', atom_sites_solution_primary)

    tools = ['smart', 'saint', 'integ', 'cad4', 'sad', 'pcf','frames', 'p4p', 'cif_od', 'cif_def', 'twin', 'abs']

    if "frames" in tools:
      p = self.sort_out_path(path, "frames")
      if p and self.metacifFiles.curr_frames != self.metacifFiles.prev_frames:
        import bruker_frames
        frames = bruker_frames.reader(p).cifItems()
        self.update_cif_block(frames)

    if "smart" in tools:
      p = self.sort_out_path(path, "smart")
      if p and self.metacifFiles.curr_smart != self.metacifFiles.prev_smart:
        import bruker_smart
        smart = bruker_smart.reader(p).cifItems()
        computing_data_collection = self.prepare_computing(smart, versions, "smart")
        smart.setdefault("_computing_data_collection", computing_data_collection)
        self.update_cif_block(smart)

    if "p4p" in tools:
      p = self.sort_out_path(path, "p4p")
      if p and self.metacifFiles != self.metacifFiles.prev_p4p:
        try:
          from p4p_reader import p4p_reader
          p4p = p4p_reader(p).read_p4p()
          self.update_cif_block(p4p)
        except:
          pass

    if "integ" in tools:
      p = self.sort_out_path(path, "integ")
      if p and self.metacifFiles.curr_integ != self.metacifFiles.prev_integ:
        import bruker_saint_listing
        integ = bruker_saint_listing.reader(p).cifItems()
        computing_data_reduction = self.prepare_computing(integ, versions, "saint")
        computing_data_reduction = string.strip((string.split(computing_data_reduction, "="))[0])
        integ.setdefault("_computing_data_reduction", computing_data_reduction)
        integ["computing_data_reduction"] = computing_data_reduction
        self.update_cif_block(integ)

    if "saint" in tools:
      p = self.sort_out_path(path, "saint")
      if p and self.metacifFiles.curr_saint != self.metacifFiles.prev_saint:
        import bruker_saint
        saint = bruker_saint.reader(p).cifItems()
        computing_cell_refinement = self.prepare_computing(saint, versions, "saint")
        saint.setdefault("_computing_cell_refinement", computing_cell_refinement)
        computing_data_reduction = self.prepare_computing(saint, versions, "saint")
        saint.setdefault("_computing_data_reduction", computing_data_reduction)
        self.update_cif_block(saint)

    if "abs" in tools:
      import abs_reader
      p = self.sort_out_path(path, "abs")
      if p and self.metacifFiles.curr_abs != self.metacifFiles.prev_abs:
        if abs_reader.abs_type(p) == "SADABS":
          if self.metacifFiles.curr_abs != self.metacifFiles.prev_abs:
            try:
              import abs_reader
              sad = abs_reader.reader(p).cifItems()
              version = self.prepare_computing(sad, versions, "sad")
              version = string.strip((string.split(version, "="))[0])
              t = self.prepare_exptl_absorpt_process_details(sad, version)
              sad.setdefault("_exptl_absorpt_process_details", t)
              merge.append(sad)
            except KeyError:
              print "There was an error reading the SADABS output file\n'%s'.\nThe file may be incomplete." %p
            #print "sad", sad
        elif abs_reader.abs_type(p) == "TWINABS":
          if self.metacifFiles.curr_abs != self.metacifFiles.prev_abs:
            try:
              import abs_reader
              twin = abs_reader.reader(p).twin_cifItems()
              version = self.prepare_computing(twin, versions, "twin")
              version = string.strip((string.split(version, "="))[0])
              t = self.prepare_exptl_absorpt_process_details(twin, version)
              twin.setdefault("_exptl_absorpt_process_details", t)
              merge.append(twin)
            except KeyError:
              print "There was an error reading the TWINABS output file\n'%s'.\nThe file may be incomplete." %p

    if 'pcf' in tools:
      p = self.sort_out_path(path, "pcf")
      if p and self.metacifFiles.curr_pcf != self.metacifFiles.prev_pcf:
        from pcf_reader import pcf_reader
        pcf = pcf_reader(p).read_pcf()
        self.update_cif_block(pcf)

    if "cad4" in tools:
      p = self.sort_out_path(path, "cad4")
      if p and self.metacifFiles.curr_cad4 != self.metacifFiles.prev_cad4:
        from cad4_reader import cad4_reader
        cad4 = cad4_reader(p).read_cad4()
        self.update_cif_block(cad4)

    if "cif_od" in tools:
      # Oxford Diffraction data collection CIF
      p = self.sort_out_path(path, "cif_od")
      if p and self.metacifFiles.curr_cif_od != self.metacifFiles.prev_cif_od:
        import iotbx.cif
        f = open(p, 'rUb')
        cif_od = iotbx.cif.fast_reader(input_string=f.read()).model().values()[0]
        f.close()
        #self.cif_block.update(cif_od)
        self.update_cif_block(cif_od)

    if "cif_def" in tools:
      # Diffractometer definition file
      diffractometer = OV.GetParam('snum.report.diffractometer')
      try:
        p = userDictionaries.localList.dictionary['diffractometers'][diffractometer]['cif_def']
      except KeyError:
        p = '?'
      if diffractometer not in ('','?') and p != '?' and os.path.exists(p):
        import cif_reader
        cif_def = cif_reader.reader(p).cifItems()
        self.update_cif_block(cif_def)

    self.write_metacif_file()

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
      versiontext = "Unknown"
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
