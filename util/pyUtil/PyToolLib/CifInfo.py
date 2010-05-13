import os
import string
import glob

import olx
from ArgumentParser import ArgumentParser
import userDictionaries
import variableFunctions
from olexFunctions import OlexFunctions
OV = OlexFunctions()

import ExternalPrgParameters
SPD, RPD = ExternalPrgParameters.SPD, ExternalPrgParameters.RPD

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

    self.list_smart = None
    self.list_saint = None
    self.list_integ = None
    self.list_cad4 = None
    self.list_sad = None
    self.list_pcf = None
    self.list_frames = None
    self.list_p4p = None
    self.list_cif_od = None


class MetaCif(ArgumentParser):
  def __init__(self, merge=False, edit=False):
    """First argument should be 'view' or 'merge'.

		'view' brings up an internal text editor with the metacif information in cif format.
		'merge' merges the metacif data with cif file from refinement, and brings up and external text editor with the merged cif file.
		"""
    super(MetaCif, self).__init__()
    merge = (merge not in ('False','false',False))
    edit = (edit not in ('False','false',False))

    if not merge:
      ## view metacif information in internal text editor
      self.viewCifInfoInOlex()
    else:
      self.writeMetacifFile()
      ## merge metacif file with cif file from refinement
      OV.CifMerge('meta.cif')
      ## open merged cif file in external text editor
      if edit:
        OV.external_edit('filepath()/filename().cif')

  def viewCifInfoInOlex(self):
    """Brings up popup text editor in olex containing the text to be added to the cif file."""

    text = self.prepareCifItems()
    inputText = OV.GetUserInput(0,'Items to be entered into cif file',text)

    if inputText and inputText != text:
      self.read_input_text(inputText)
    else:
      inputText = text

    return inputText

  def writeMetacifFile(self):
    """Writes the file 'meta.cif' to the Olex virtual FS."""

    text = self.prepareCifItems()
    ## write file to virtual FS
    OV.write_to_olex('meta.cif', text)

  def sort_crystal_dimensions(self):
    params = OV.Params()
    metacif = params.snum.metacif
    dimensions = []
    for item in ('exptl_crystal_size_min','exptl_crystal_size_mid','exptl_crystal_size_max'):
      value = OV.GetParam('snum.metacif.%s' %item)
      if value is not None:
        dimensions.append(value)
    dimensions = [item for item in (metacif.exptl_crystal_size_min,
                                    metacif.exptl_crystal_size_mid,
                                    metacif.exptl_crystal_size_max) if item is not None]
    if dimensions:
      dimensions.sort()
      try:
        metacif.exptl_crystal_size_min = dimensions[0]
        metacif.exptl_crystal_size_mid = dimensions[1]
        metacif.exptl_crystal_size_max = dimensions[2]
      except IndexError:
        pass
    params.snum.metacif = metacif
    olx.phil_handler.update_from_python(params)

  def prepareCifItems(self):
    """Returns a string in cif format of all items in a dictionary of cif items."""

    self.sort_crystal_dimensions()
    listText = []
    name_value_pairs = olx.phil_handler.name_value_pairs('snum.metacif')
    for name, value in name_value_pairs:
      if 'file' in name or 'user_input' in name:
        continue
      cifName = '_' + name.split('snum.metacif.')[1]
      if cifName == '_symmetry_space_group_name_H_M':
        cifName = '_symmetry_space_group_name_H-M'
      separation = " "*(40-len(cifName))
      if cifName not in ('_list_people'):
        if value is None:
          continue
        elif value == '?':
          continue
        elif cifName == '_publ_author_names' and OV.GetParam_as_string('snum.metacif.publ_author_names') != '?':
          loop = [('_publ_author_name','_publ_author_email','_publ_author_address')]
          names = value.split(';')
          for name in names:
            if name != '?':
              email = userDictionaries.people.getPersonInfo(name,'email')
              add = userDictionaries.people.getPersonInfo(name,'address')
              address = ''
              for line in add.split('\n'):
                address += ' %s\n' %line
              loop.append((name,email,address))
          loopText = self.prepareLoop(loop)
          listText.append(loopText)
        elif cifName == '_publ_contact_author_name':
          name = value
          if name != '?':
            email = userDictionaries.people.getPersonInfo(name,'email')
            phone = userDictionaries.people.getPersonInfo(name,'phone')
            add = userDictionaries.people.getPersonInfo(name,'add')
            address = ''
            for line in add.split('\n'):
              address += ' %s\n' %line
            publ_contact_author_text = ''
            for item in [('_publ_contact_author_name',name),('_publ_contact_author_email',email),('_publ_contact_author_phone',phone)]:
              separation = " "*(40-len(item[0]))
              publ_contact_author_text += "%s%s'%s'\n" %(item[0],separation,item[1])
            listText.append(publ_contact_author_text)
        elif cifName == '_publ_contact_letter' and value != '?':
          letterText = '_publ_contact_letter\n;\n'
          for line in value.split('\n'):
            letterText += ' %s\n' %line
          letterText += ';\n'
          listText.append(letterText)
        else:
          if type(value) == float or type(value) == int:
            s = "%s%s%s\n" %(cifName,separation,value)
          elif value and value[0:2] == '\n;' and value != ';\n ?\n;':
            s = "%s%s" %(cifName,value)
          elif value and value[0:1] == ';' and value != ';\n ?\n;':
            s = "%s%s\n%s\n" %(cifName,separation,value)
          elif ' ' in value:
            s = "%s%s'%s'\n" %(cifName,separation,value)
          elif ',' in value:
            s = "%s%s'%s'\n" %(cifName,separation,value)
          elif value:
            s = "%s%s%s\n" %(cifName,separation,value)
          else:
            s = None
          if s:
            listText.append(s)
    listText.sort()
    if listText != []:
      text = ''.join(listText)
    else:
      text = "No cif information has been found"
    return text

  def prepareLoop(self,loop):
    strList = ['loop_\n']
    for item in loop:
      for line in item:
        if '\n' in line:
          strList.append(';\n%s;\n' %line)
        elif ' ' in line:
          strList.append("'%s'\n" %line)
        else:
          strList.append("%s\n" %line)
    return ''.join(strList)

  def read_input_text(self, inputText):
    """Reads input text from internal text editor and saves as variables in Olex those that have changed.

		For each cif item, if the value of the cif item has changed, the new value of the variable will be saved in Olex
		and the variable added to the list of variables that have been modified by the user.
		The Olex variables are then saved as a pickle file.
		"""

    mcif = inputText.split('\n')
    meta = []
    a = -1
    for line in mcif:
      a+= 1
      field = ""
      apd=""
      l = line.split()
      if len(l) <= 1:
        i = 1
        value = ""
        if line == "\n":
          continue
        if line[:1] == ';':
          continue
        if line[:1] == "_":
          field = line[1:].strip()
          value += "%s" %(mcif[a+i])
          i+= 1
          while mcif[a+i][:1] != ";":
            value += "\n%s" %(mcif[a+i])
            i+=1
          value += "\n;"
          try:
            oldValue = OV.GetParam_as_string('snum.metacif.%s' %field)
            if oldValue is not None and value != str(oldValue).rstrip().lstrip():
              OV.SetParam('snum.metacif.%s' %field,value)
              variableFunctions.AddVariableToUserInputList('%s' %field)
            else:
              continue
          except:
            OV.SetParam('snum.metacif.%s' %field,value[1:])
      else:
        if line[:1] == "_":
          field = line.split()[0][1:]
          x = line.split()[1:]
          value = ""
          if len(x) > 1:
            for thing in x:
              value += "%s " %thing
          else:
            value = x[0]
          value = value.replace("'", "").rstrip()
          try:
            oldValue = OV.GetParam_as_string('snum.metacif.%s' %field)
            if oldValue is not None and value != str(oldValue).strip():
              if value in ('?', '.'):
                OV.SetParam('snum.metacif.%s' %field, None)
              else:
                OV.SetParam('snum.metacif.%s' %field, value)
              variableFunctions.AddVariableToUserInputList('%s' %field)
            else:
              continue
          except:
            OV.SetParam('snum.metacif.%s' %field, value)
        elif line == "\n":
          continue
        elif line[:1] == "#":
          continue
        else:
          continue

  def read_meta_file(self, metacif):
    rFile=open(metacif, 'r')
    mcif = []
    meta = []
    for line in rFile:
      mcif.append(line)
    for line in mcif:
      field = ""
      apd=""
      l = line.split()
      if len(l) <= 1:
        i = 0
        value = ""
        if line == "\n":
          continue
        if line == ';\n':
          continue
        if line[:1] == "_":
          field = line[:-1]
          value += "%s" %(mcif[i+1])
          i+= 1
          while mcif[i+1][:1] != ";":
            value += (mcif[i+2])
            i+=1
          apd = "%s\n%s" %(field, value)
      else:
        if line[:1] == "_":
          apd = line
          field = line.split()[0]
        elif line == "\n":
          continue
        elif line[:1] == "#":
          apd = line
        else:
          continue
      if field in self.toInsert:
        continue
      if apd not in meta:
        meta.append(apd)
    rFile.close()
    return meta

  def insert_item(self):
    metacifInfo = variableFunctions.getVVD('metacif')
    listText = self.prepareCifItems(metacifInfo)
    listText.sort()
    text = ""
    if listText != []:
      for item in listText:
        text += item
    joinstr =  "/"
    dir_up = joinstr.join(self.filepath.split(joinstr)[:-1])
    meta = []

OV.registerFunction(MetaCif)

class CifTools(ArgumentParser):
  def __init__(self):
    super(CifTools, self).__init__()
    self.ignore = ["?", "'?'", ".", "'.'"]
    self.versions = {"default":[],"smart":{},"saint":{},"shelxtl":{},"xprep":{},"sad":{}}
    self.metacif = {}
    self.metacifFiles = MetacifFiles()
    self.run()

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

    tools = ['smart', 'saint', 'integ', 'cad4', 'sad', 'pcf','frames', 'p4p', 'cif_od', 'cif_def']

    if "frames" in tools:
      p = self.sort_out_path(path, "frames")
      if p != "File Not Found" and self.metacifFiles.curr_frames != self.metacifFiles.prev_frames:
        import bruker_frames
        frames = bruker_frames.reader(p).cifItems()
        merge.append(frames)

    if "smart" in tools:
      p = self.sort_out_path(path, "smart")
      if p != "File Not Found" and self.metacifFiles.curr_smart != self.metacifFiles.prev_smart:
        import bruker_smart
        smart = bruker_smart.reader(p).cifItems()
        computing_data_collection = self.prepare_computing(smart, versions, "smart")
        smart.setdefault("_computing_data_collection", computing_data_collection)
        merge.append(smart)

    if "p4p" in tools:
      p = self.sort_out_path(path, "p4p")
      if p != "File Not Found" and self.metacifFiles != self.metacifFiles.prev_p4p:
        try:
          from p4p_reader import p4p_reader
          p4p = p4p_reader(p).read_p4p()
          merge.append(p4p)
        except:
          pass

    if "integ" in tools:
      p = self.sort_out_path(path, "integ")
      if p != "File Not Found" and self.metacifFiles.curr_integ != self.metacifFiles.prev_integ:
        import bruker_saint_listing
        integ = bruker_saint_listing.reader(p).cifItems()
        computing_data_reduction = self.prepare_computing(integ, versions, "saint")
        computing_data_reduction = string.strip((string.split(computing_data_reduction, "="))[0])
        integ.setdefault("_computing_data_reduction", computing_data_reduction)
        integ["computing_data_reduction"] = computing_data_reduction
        merge.append(integ)

    if "saint" in tools:
      p = self.sort_out_path(path, "saint")
      if p != "File Not Found" and self.metacifFiles.curr_saint != self.metacifFiles.prev_saint:
        import bruker_saint
        saint = bruker_saint.reader(p).cifItems()
        computing_cell_refinement = self.prepare_computing(saint, versions, "saint")
        saint.setdefault("_computing_cell_refinement", computing_cell_refinement)
        computing_data_reduction = self.prepare_computing(saint, versions, "saint")
        saint.setdefault("_computing_data_reduction", computing_data_reduction)
        merge.append(saint)

    if "sad" in tools:
      p = self.sort_out_path(path, "sad")
      if p != "File Not Found" and self.metacifFiles.curr_sad != self.metacifFiles.prev_sad:
        try:
          import sadabs
          sad = sadabs.reader(p).cifItems()
          version = self.prepare_computing(sad, versions, "sad")
          version = string.strip((string.split(version, "="))[0])
          t = self.prepare_exptl_absorpt_process_details(sad, version)
          sad.setdefault("_exptl_absorpt_process_details", t)
          merge.append(sad)
        except KeyError:
          print "There was an error reading the SADABS output file\n'%s'.\nThe file may be incomplete." %p

    if 'pcf' in tools:
      p = self.sort_out_path(path, "pcf")
      if p != "File Not Found" and self.metacifFiles.curr_pcf != self.metacifFiles.prev_pcf:
        from pcf_reader import pcf_reader
        pcf = pcf_reader(p).read_pcf()
        merge.append(pcf)

    if "cad4" in tools:
      p = self.sort_out_path(path, "cad4")
      if p != "File Not Found" and self.metacifFiles.curr_cad4 != self.metacifFiles.prev_cad4:
        from cad4_reader import cad4_reader
        cad4 = cad4_reader(p).read_cad4()
        merge.append(cad4)

    if "cif_od" in tools:
      # Oxford Diffraction data collection CIF
      p = self.sort_out_path(path, "cif_od")
      if p != "File Not Found" and self.metacifFiles.curr_cif_od != self.metacifFiles.prev_cif_od:
        import cif_reader
        cif_od = cif_reader.reader(p).cifItems()
        merge.append(cif_od)

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
        merge.append(cif_def)
    self.setVariables(merge)

  def setVariables(self,info):
    dataAdded = []
    userInputVariables = OV.GetParam("snum.metacif.user_input_variables")

    for d in info:
      cifLabels = ['diffrn','cell','symmetry','exptl','computing']
      ## sort crystal dimensions into correct order
      dimensions = []
      for item in ('_exptl_crystal_size_min','_exptl_crystal_size_mid','_exptl_crystal_size_max'):
        if item not in dataAdded and d.has_key(item):
          dimensions.append(d[item])
      if dimensions:
        dimensions.sort()
        try:
          d['_exptl_crystal_size_min'] = dimensions[0]
          d['_exptl_crystal_size_mid'] = dimensions[1]
          d['_exptl_crystal_size_max'] = dimensions[2]
        except IndexError:
          pass
      for item, value in d.items():
        if item not in dataAdded\
           and (userInputVariables is None
                or item.lstrip('_') not in userInputVariables):
          if item[0] == '_' and item.split('_')[1] in cifLabels:
            if item == '_symmetry_cell_setting':
              value = value.lower()
            if value == '?':
              value = None
            OV.SetParam("snum.metacif.%s" %(item[1:].replace('-','_').replace('/','_over_')), value)
            dataAdded.append(item)
        else: continue

    colour = OV.GetParam("snum.metacif.exptl_crystal_colour")
    if colour in (
      "colourless","white","black","gray","brown","red","pink","orange","yellow","green","blue","violet")\
       and userInputVariables is not None\
       and "exptl_crystal_colour_primary" not in userInputVariables:
      OV.SetParam("snum.metacif.exptl_crystal_colour_primary", colour)

  def get_defaults():
    defs = {}
    defs.setdefault("_exptl_crystal_density_meas","       'not measured'\n")
    defs.setdefault("_diffrn_detector_area_resol_mean","  8\n")
    defs.setdefault("_diffrn_standards_number","          .\n")
    defs.setdefault("_diffrn_standards_interval_count","  .\n")
    defs.setdefault("_diffrn_standards_decay_%","         .\n")
    return defs

  def merge_cifs(self, merge, cif, tmp, basename):
    try:
      rfile_cif = open(cif, 'r')
    except IOError:
      "The file can't be written at this time"
      return "End"
    rfile_merge = open(merge, 'r')
    wfile = open(tmp, 'w')
    cif_content = {}
    merge_content = {}
    lines = []

    for line in rfile_merge:
      if line == "": line = "BLANK"
      lines.append(string.strip(line))

    skip = 0
    i = 0
    for line in lines:
      free_txt = ""
      if skip > 0:
        skip -= 1
        continue
      if line == "": line = "BLANK"
      txt = string.split(line, " ", 1)
      try:
        merge_content.setdefault(txt[0], txt[1])
      except IndexError:
        if (txt[0])[:1] != "_":
          continue
        else:
          while (lines[i+1])[:1] != "_":
            skip += 1
            t = lines[i+1]
            if t != ";":
              t = " %s" %t
            elif t == ";":
              if skip == 1: t = "\n;"

            free_txt = "%s%s\n" %(free_txt,  t)
            i += 1
          merge_content.setdefault(txt[0], free_txt)
      i += 1

    lines = []
    for line in rfile_cif:
      lines.append(string.strip(line))
    i = 0
    for line in lines:
      if line == "": line = "BLANK"
      txt = string.split(line)
      try:
        cif_content.setdefault(txt[0], txt[1])
      except IndexError:
        if (txt[0])[:1] != "_":
          continue
        else:
          free_txt = ""
          while (lines[i+1])[:1] != "_":
            t = lines[i+1]
            if t != ";":
              t = " %s" %t
            free_txt = "%s%s\n" %(free_txt,  t)
            i += 1
          cif_content.setdefault(txt[0], free_txt)
      i += 1

      ## Write the combined file
    skip = 0
    i = 0
    for line in lines:
      if line == "":
        line = "BLANK"
      if line == ";" and lines[i+1] == "?" and lines[i+2] == ";":
        topic = "_exptl_special_details"
        try:
          if lines[i-1] == topic and merge_content[topic]:
            skip = 3
        except KeyError:
          pass

      if skip != 0:
        skip -= 1
        i += 1
        continue

      txt = string.split(line)
      try:
        if txt[0] in merge_content:
          descriptor = txt[0]
          value = string.strip(merge_content[txt[0]])
          spaces = 34 - len(descriptor)
          spacer = " " * spaces
          if descriptor == "_exptl_special_details":
            value = "\n" + value
            spacer = ""
          line = "%s%s%s" %(descriptor, spacer, value)
      except IndexError:
        i += 1
        continue
      if line == "BLANK":
        line = ""
      txt = "%s\n" %line
      wfile.writelines(txt)
      i += 1

  def prepare_exptl_absorpt_process_details(self, abs, version):
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

  def prepare_exptl_special_details(self, smart):
    """Prepares the text for the _exptl_special_details cif item using details obtained from the smart.ini file."""

    txt = """
        The data collection nominally covered a full sphere of reciprocal space by
        a combination of %(scans)i sets of \\w scans each set at different \\f and/or
        2\\q angles and each scan (%(scantime)s s exposure) covering %(scanwidth)s\ degrees in \\w.
        The crystal to detector distance was %(distance)s cm.
"""%smart
    exptl_special_details = "\n;%s;\n" %txt
    return exptl_special_details

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

  def prepare_diffractometer_data(self, smart):
    diffractometers = {}
    diffractometers["1k"] = {}
    diffractometers["6k"] = {}
    diffractometers["apex"] = {}
    diffractometers["1k"]["_diffrn_detector_area_resol_mean"] = "8"
    diffractometers["6k"]["_diffrn_detector_area_resol_mean"] = "8"
    diffractometers["apex"]["_diffrn_detector_area_resol_mean"] = "8"
    version = smart["version"]

  def write_merge_file(self, path, merge):
    file = path
    afile = open(file, 'w')
    for section in merge:
      for item in section:
        if item[:1] == "_":
          spacers = 35 - len(item)
          txt = "%s%s%s\n" %(item, " "*spacers, section[item])
          afile.write(txt)

  def sort_out_path(self, directory, tool):
    """Returns the path of the most recent file in the given directory of the given type.

		Searches for files of the given type in the given directory.
		If no files are found, the parent directory is then searched.
		If more than one file is present, the path of the most recent file is returned by default.
		"""

    parent = ""
    info = ""
    if tool == "smart":
      name = "smart"
      extension = ".ini"
    elif tool == "saint":
      name = "saint"
      extension = ".ini"
    elif tool == "sad":
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
    if info:
      returnvalue = self.file_choice(files,tool)
    else:
      p = string.split(directory, "/")
      p[-1:] = ""
      for bit in p:
        parent = parent + bit + "/"
      files = []
      for path in glob.glob(os.path.join(parent, name + extension)):
        info = os.stat(path)
        files.append((info.st_mtime, path))
      if info:
        returnvalue = self.file_choice(files,tool)
      else:

        returnvalue = "File Not Found"
    return OV.standardizePath(returnvalue)

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

OV.registerFunction(CifTools)

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
