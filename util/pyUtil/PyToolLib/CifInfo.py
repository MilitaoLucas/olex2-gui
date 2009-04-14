import sys
import os
import string
import glob
#import FileSystem as FS

from ArgumentParser import ArgumentParser
import userDictionaries
import variableFunctions
from olexFunctions import OlexFunctions
OV = OlexFunctions()

#from ExternalPrgParameters import DefineExternalPrgParameters
#a = DefineExternalPrgParameters()
#SPD, RPD = a.run()
import ExternalPrgParameters
SPD, RPD = ExternalPrgParameters.defineExternalPrograms()


#from DimasInfo import dimas_cif
#from Streams import Unbuffered
#import dimas_info
#sys.stdin = Unbuffered(sys.stdin)
#sys.stdout = Unbuffered(sys.stdout)

smart = {}

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
	def __init__(self, args=None, tool_arg=None):
		"""First argument should be 'view' or 'merge'.
		
		'view' brings up an internal text editor with the metacif information in cif format.
		'merge' merges the metacif data with cif file from refinement, and brings up and external text editor with the merged cif file.
		"""
		super(MetaCif, self).__init__(args, tool_arg=None)
		try:
			self.arg = args.split(',')[0]
		except:
			pass		
		try:
			self.tool_arg = tool_arg.split(';')[0]
		except:
			pass
		
			
	def run_MetaCif(self, f, args):
		self.arg = f
		edit = bool(args.get('edit',False))
		
		if self.arg == 'view':
			## view metacif information in internal text editor
			self.viewCifInfoInOlex()
		elif self.arg == 'merge':
			self.writeMetacifFile()
			## merge metacif file with cif file from refinement
			OV.CifMerge('meta.cif')
			## open merged cif file in external text editor
			if edit:
				OV.external_edit('filepath()/filename().cif')
				#olex.m("external_edit 'filepath()/filename().cif'")
	
	def viewCifInfoInOlex(self):
		"""Brings up popup text editor in olex containing the text to be added to the cif file."""
		
		metacifInfo = variableFunctions.getVVD('metacif')
		
		text = self.prepareCifItems(metacifInfo)
		
		#inputText = olex.f("""GetUserInput(0,'Items to be entered into cif file',"'%s'")""" %text)
		inputText = OV.GetUserInput(0,'Items to be entered into cif file',text)
		
		if inputText and inputText != text:
			self.read_input_text(inputText)
		else:
			inputText = text
			
		return inputText
	
	def writeMetacifFile(self):
		"""Writes the file 'meta.cif' to the Olex virtual FS."""
		
		metacifInfo = variableFunctions.getVVD('metacif')
		text = self.prepareCifItems(metacifInfo)
		
		## write file to virtual FS
		OV.write_to_olex('meta.cif', text)
		
	def prepareCifItems(self,metacifInfo):
		"""Returns a string in cif format of all items in a dictionary of cif items."""
		
		listText = []
		
		## Sort crystal dimensions
		dimensions = []
		for item in ('snum_metacif_exptl_crystal_size_min','snum_metacif_exptl_crystal_size_mid','snum_metacif_exptl_crystal_size_max'):
			if metacifInfo.has_key(item):
				dimensions.append(metacifInfo[item])
		if dimensions:
			dimensions.sort()
			try:
				metacifInfo['snum_metacif_exptl_crystal_size_min'] = dimensions[0]
				metacifInfo['snum_metacif_exptl_crystal_size_mid'] = dimensions[1]
				metacifInfo['snum_metacif_exptl_crystal_size_max'] = dimensions[2]
			except IndexError:
				pass

		for key, obj in metacifInfo.items():
			#key = item[0]
			#obj = item[1]
			if 'file' not in key and 'snum_user_input' not in key:
				if type(obj) not in (int,float,str,bool,unicode):
					value = obj.value
				else:
					value = obj
				cifName = key.split('%s' %'snum_metacif')[1]
				separation = " "*(40-len(cifName))
				
				if cifName not in ('_list_people'):
					if value == '?':
						pass
					elif cifName == '_publ_author_names' and OV.FindValue('snum_metacif_publ_author_names') != '?':
						#publ_author_loop = ['loop_\n',' _publ_author_name\n',' _publ_author_email\n',' _publ_author_address\n\n',]
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
							s = "%s%s%s" %(cifName,separation,value)
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
			else:
				pass
			
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
					field = line[:-1].strip()
					value += "%s" %(mcif[a+i])
					i+= 1
					while mcif[a+i][:1] != ";":
						value += "\n%s" %(mcif[a+i])
						i+=1
					value += "\n;"
					
					try:
						oldValue = OV.FindValue('snum_metacif%s' %field).rstrip().lstrip()
						if value != oldValue:
							OV.SetVar('snum_metacif%s' %field,value)
							variableFunctions.AddVariableToUserInputList('snum_metacif%s' %field)
						else:
							continue
					except:
						OV.SetVar('snum_metacif%s' %field,value)
			else:
				if line[:1] == "_":
					field = line.split()[0]
					x = line.split()[1:]
					value = ""
					if len(x) > 1:
						for thing in x:
							value += "%s " %thing					
					else:
						value = x[0]
					value = value.replace("'", "").rstrip()
					try:
						oldValue = OV.FindValue('snum_metacif%s' %field).strip()
						if value != oldValue:
							OV.SetVar('snum_metacif%s' %field, value)
							variableFunctions.AddVariableToUserInputList('snum_metacif%s' %field)
						else:
							continue
					except:
						OV.SetVar('snum_metacif%s' %field, value)
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

MetaCif_instance = MetaCif()
OV.registerMacro(MetaCif_instance.run_MetaCif, 'edit-True/False')    
		
		
		
class CifTools(ArgumentParser):
	def __init__(self, args=None, tool_arg=None):
		super(CifTools, self).__init__(args, tool_arg)
		self.ignore = ["?", "'?'", ".", "'.'"]
		self.versions = {"default":[],"smart":{},"saint":{},"shelxtl":{},"xprep":{},"sad":{}}
		self.metacif = {}
		self.tool_args = tool_arg

	def run(self):
		self.cif_info()
		
	def insert_into_meta_cif(self):
		for item in merge:
			for bit in item:
				if bit[:1] == "_":
					self.metacif.setdefault(bit, string.strip(item[bit]))
					self.metacif[bit] = string.strip(item[bit])
		a = MetaCif(self.metacif, None)
		a.run()

#	def cif_info(self, f, args={}):
	def run_CifTools(self, f, args={}):
		
		merge = []
		
		filefull = self.filefull
		filepath = self.filepath
		filename = self.filename
		basedir = self.basedir
		arguments = self.tool_args
		self.userInputVariables = OV.FindValue("snum_user_input_variables")
		
		basename = filename
		path = filepath
		args = []
		arguments = []
		if not arguments:
			args.append("smart")
			args.append("saint")
			args.append("integ")
			args.append("sad")
			args.append("cad4")
			args.append("p4p")
			
		merge_cif_file = "%s/%s" %(path, "fileextract.cif")
		cif_file = "%s/%s%s" %(path, basename, ".cif")
		tmp = "%s/%s" %(path, "tmp.cif")
		
		info = ""
		for p in glob.glob(os.path.join(path, basename + ".cif")):
			info = os.stat(p)
			
		versions = self.get_def()
		
		import History
		try:
			solution_branch = History.tree.historyTree[History.tree.current_solution]
			current_refinement = solution_branch.historyBranch[History.tree.current_refinement]
			solution_reference = SPD.programs[solution_branch.solution_program].reference
			OV.SetVar('snum_metacif_computing_structure_solution', solution_reference)
			
			atom_sites_solution_primary = SPD.programs[solution_branch.solution_program].methods[solution_branch.solution_method].atom_sites_solution
			OV.SetVar('snum_metacif_atom_sites_solution_primary', atom_sites_solution_primary)
		except KeyError:
			pass
		
		tools = ['smart', 'saint', 'integ', 'cad4', 'sad', 'pcf','frames', 'p4p', 'cif_od', 'cif_def']
		
		if "frames" in tools:
			p = self.sort_out_path(path, "frames")
			if p != "File Not Found" and metacifFiles.curr_frames != metacifFiles.prev_frames:
				from bruker_frames import BrukerFrame
				frames = BrukerFrame(p).cifItems()
				merge.append(frames)
				
		if "smart" in tools:
			p = self.sort_out_path(path, "smart")
			if p != "File Not Found" and metacifFiles.curr_smart != metacifFiles.prev_smart:
				import bruker_smart
				smart = bruker_smart.reader(p).cifItems()
				computing_data_collection = self.prepare_computing(smart, versions, "smart")
				smart.setdefault("_computing_data_collection", computing_data_collection)
				merge.append(smart)
				
		if "p4p" in tools:
			p = self.sort_out_path(path, "p4p")
			if p != "File Not Found" and metacifFiles.curr_p4p != metacifFiles.prev_p4p:
				try:
					from p4p_reader import p4p_reader
					p4p = p4p_reader(p).read_p4p()
					merge.append(p4p)
				except:
					pass
				
		if "integ" in tools:
			p = self.sort_out_path(path, "integ")
			if p != "File Not Found" and metacifFiles.curr_integ != metacifFiles.prev_integ:
				integ = get_info_from_mls(p)["raw"]
				computing_data_reduction = self.prepare_computing(integ, versions, "saint")
				computing_data_reduction = string.strip((string.split(computing_data_reduction, "="))[0])
				integ.setdefault("_computing_data_reduction", computing_data_reduction)
				integ["computing_data_reduction"] = computing_data_reduction
				merge.append(integ)
		
		if "saint" in tools:
			p = self.sort_out_path(path, "saint")
			if p != "File Not Found" and metacifFiles.curr_saint != metacifFiles.prev_saint:
				from bruker_saint import bruker_saint
				saint = bruker_saint(p).read_saint()
				computing_cell_refinement = self.prepare_computing(saint, versions, "saint")
				saint.setdefault("_computing_cell_refinement", computing_cell_refinement)
				computing_data_reduction = self.prepare_computing(saint, versions, "saint")
				saint.setdefault("_computing_data_reduction", computing_data_reduction)
				merge.append(saint)
				
		if "sad" in tools:
			p = self.sort_out_path(path, "sad")
			if p != "File Not Found" and metacifFiles.curr_sad != metacifFiles.prev_sad:
				try:
					from sadabs import Sadabs
					sad = Sadabs(p).read_sad()
					version = self.prepare_computing(sad, versions, "sad")
					version = string.strip((string.split(version, "="))[0])
					t = self.prepare_exptl_absorpt_process_details(sad, version)
					sad.setdefault("_exptl_absorpt_process_details", t)
					merge.append(sad)
				except KeyError:
					print "There was an error reading the SADABS output file\n'%s'.\nThe file may be incomplete." %p
				
		if 'pcf' in tools:
			p = self.sort_out_path(path, "pcf")
			if p != "File Not Found" and metacifFiles.curr_pcf != metacifFiles.prev_pcf:
				from pcf_reader import pcf_reader
				pcf = pcf_reader(p).read_pcf()
				merge.append(pcf)
				
		if "cad4" in tools:
			p = self.sort_out_path(path, "cad4")
			if p != "File Not Found" and metacifFiles.curr_cad4 != metacifFiles.prev_cad4:
				from cad4_reader import cad4_reader
				cad4 = cad4_reader(p).read_cad4()
				merge.append(cad4)
				
		if "cif_od" in tools:
			# Oxford Diffraction data collection CIF
			p = self.sort_out_path(path, "cif_od")
			if p != "File Not Found" and metacifFiles.curr_cif_od != metacifFiles.prev_cif_od:
				import cif_reader
				cif_od = cif_reader.reader(p).cifItems()
				merge.append(cif_od)
				
		if "cif_def" in tools:
			# Diffractometer definition file
			diffractometer = OV.FindValue('snum_report_diffractometer')
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
		userInputVariables = OV.FindValue("snum_user_input_variables")
		
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
			for item in d.keys():
				if item not in dataAdded and item not in userInputVariables:
					if item[0] == '_' and item.split('_')[1] in cifLabels:
						value = d[item]
						OV.SetVar("snum_metacif%s" %(item), value)
						dataAdded.append(item)
				else: continue
				
		colour = OV.FindValue("snum_metacif_exptl_crystal_colour")
		if colour in "colourless;white;black;gray;brown;red;pink;orange;yellow;green;blue;violet" and "_exptl_crystal_colour_primary" not in userInputVariables:
			OV.SetVar("snum_metacif_exptl_crystal_colour_primary", colour)
			
	
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
			afile = olexdir + "/Util/Cif/" + "cif_info.def"
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
			name = "exp"
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
		if "snum_metacif_%s_file" %tool not in self.userInputVariables:
			for date, file in info:
				a = file.split('/')[-2:]
				shortFilePath = ""
				for bit in a:
					shortFilePath += "/" + bit 
				listFiles.append("%s" %shortFilePath)
				i += 1
			files = ';'.join(listFiles)
			try:
				setattr(metacifFiles, "prev_%s" %tool, getattr(metacifFiles, "curr_%s" %tool))
				OV.SetVar("snum_metacif_list_%s_files" %tool, files)
				setattr(metacifFiles, "list_%s" %tool, files)
				OV.SetVar("snum_metacif_%s_file" %tool, listFiles[0])
				setattr(metacifFiles, "curr_%s" %tool, info[0])
			except:
				pass
			returnvalue = info[0][1]
		else:
			x = OV.FindValue("snum_metacif_%s_file" %tool)
			for date, file in info:
				if x in file:
					setattr(metacifFiles,"curr_%s" %tool, (date,file))
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
		file = "%s/util/SiteSpecific/cif_info.def" %self.basedir
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

CifTools_instance = CifTools()
OV.registerMacro(CifTools_instance.run_CifTools, '')    

def getOrUpdateDimasVar(getOrUpdate):
	for var in [('snum_dimas_crystal_colour_base','_exptl_crystal_colour_primary'),
							('snum_dimas_crystal_colour_intensity','_exptl_crystal_colour_modifier'),
							('snum_dimas_crystal_colour_appearance','_exptl_crystal_colour_lustre'),
							('snum_dimas_crystal_name_systematic','_chemical_name_systematic'),
							('snum_dimas_crystal_size_min','_exptl_crystal_size_min'),
							('snum_dimas_crystal_size_med','_exptl_crystal_size_mid'),
							('snum_dimas_crystal_size_max','_exptl_crystal_size_max'),
							('snum_dimas_crystal_shape','_exptl_crystal_description'),
							('snum_dimas_crystal_crystallisation_comment','_exptl_crystal_recrystallization_method'),
							('snum_dimas_crystal_preparation_comment','_exptl_crystal_preparation'),
							('snum_dimas_diffraction_diffractometer','_diffrn_measurement_device_type'),
							('snum_dimas_diffraction_ambient_temperature','snum_metacif_diffrn_ambient_temperature'),
							('snum_dimas_diffraction_comment','snum_metacif_diffrn_special_details')
							]:
		if OV.FindValue(var[0]) != OV.FindValue('snum_metacif%s' %var[-1]):
			if getOrUpdate == 'get':
				value = OV.FindValue(var[0]) 
				OV.SetVar('snum_metacif%s' %var[-1],value)
		
			elif getOrUpdate == 'update':
				value = OV.FindValue('snum_metacif%s' %var[-1])
				OV.SetVar(var[0],value)
		else: continue
		
	
def get_info_from_p4p(p4p_file):
	rFile = open(p4p_file, 'r')
	p4p = []
	for line in rFile:
		p4p.append(line)
	p4p_key = {"raw":{}, "cif":{}}
	p4p_key["raw"].setdefault("SOURCE", "")
	i = 0
	for li in p4p:
		li = string.strip(li)
		if not li:
			continue
		if li[:2] == "  ":
			continue
		l = li.split()
		field = string.strip(l[0])
		value = string.strip(li.split(field)[1])
		if field != "REF05":
			p4p_key["raw"].setdefault(field, value)
			
	ciflist=["_diffrn_radiation_wavelength"]
	have_cif_item = False
	value = ""
	for item in ciflist:
		if item == "_diffrn_radiation_wavelength":
			if p4p_key["raw"]["SOURCE"]:
				value = p4p_key["raw"]["SOURCE"].split()[0]
				
			if value:
				p4p_key["cif"].setdefault(item, r"'%s K\a'" %value)
				have_cif_item = True
	if have_cif_item:
		metacif = MetaCif
		a = metacif(p4p_key["cif"], None)
		a.run()
	return p4p_key

def get_info_from_mls(file):
	two_theta_min = 0
	two_theta_max = 0
	used = 0
	
	rFile = open(file, 'r')
	mls = []
	for line in rFile:
		mls.append(line)
	mls_key = {"raw":{}, "cif":{}}
	i = 0
	for li in mls:
		i += 1
		l = li.split()
		if li[:5] == "SAINT":
			mls_key["raw"].setdefault("prog_version", string.strip(li[6:]))
		elif li == "Reflection Summary:\n":
			two_theta_min = float(string.strip(mls[i+2].split()[-2]))
			two_theta_max = float(string.strip(mls[i+2].split()[-1]))
			used = string.strip(mls[i+2].split()[-5])
			best = string.strip(mls[i+2].split()[-3])
			worst = string.strip(mls[i+2].split()[-2])
		elif "Range of reflections used:" in li:
			two_theta_min = float(string.strip(mls[i+1].split()[-2]))
			two_theta_max = float(string.strip(mls[i+1].split()[-1]))
			best = string.strip(mls[i+1].split()[1])
			worst = string.strip(mls[i+1].split()[0])
		elif "Orientation least squares, component" in li:
			u = string.strip(li.split("(")[1])
			used = string.strip(u.split()[0])

	mls_key["raw"].setdefault("_cell_measurement_theta_min", "%.3f" %(two_theta_min/2))
	mls_key["raw"]["_cell_measurement_theta_min"] = "%.3f" %(two_theta_min/2)
	mls_key["raw"].setdefault("_cell_measurement_theta_max", "%.3f" %(two_theta_max/2))
	mls_key["raw"]["_cell_measurement_reflns_used"] = "%s" %(used)

	return mls_key