# bruker_frames.py

class BrukerFrame(object):
	def __init__(self, filepath):
		self._cifItems = {}
		self._saint_cfg = {}
		rFile = open(filepath, 'r')
		self.data = rFile.read()
		rFile.close()
		self.readHeader()
		
	def readHeader(self):
		value = ""
		previousHeader = ""
		header_d = {}
		m = 0
		while "............................" not in self.data[m:m+80]:
			try:
				n = m + 8
				header = self.data[m:n]
				m = n
				n = m + 72
				value = self.data[m:n]
				m = n
				
				header = header.strip(':').strip()
				value = value.strip()
				if header == "":
					break
				if header != previousHeader:
					header_d.setdefault(header,value)
				else:
					header_d[header] += " %s" %value
				previousHeader = header
				
			except:
				break
			
		a = header_d['CSIZE'].split('|')
		a.sort()
		size = []
		for i in a:
			try:
				float(i)
				size.append(i)
			except:
				pass
			
		matrix = header_d['MATRIX'].split()
		
		self._cifItems['_diffrn_source_voltage'] = "%.0f" %float(header_d['SOURCEK'])
		self._cifItems['_diffrn_source_current'] = "%.0f" %float(header_d['SOURCEM'])
		self._cifItems['_diffrn_refln_scan_width'] = "%.2f" %float(header_d['RANGE'])
		self._cifItems['time'] = "%.2f" %float(header_d['CUMULAT'])
		self._cifItems['formula'] = "%s" %(header_d['CHEM'])
		self._cifItems['_diffrn_radiation_monochromator'] = header_d['FILTER']
		self._cifItems['_diffrn_radiation_wavelength'] = "%f" %float(header_d['WAVELEN'].split()[0])
		self._cifItems['_exptl_crystal_description'] = "%s" %(header_d['MORPH'])
		self._cifItems['_exptl_crystal_colour'] = "%s" %(header_d['CCOLOR'])
		if len(size) == 3:
			self._cifItems['_exptl_crystal_size_min'] = "%s" %(size[0])
			self._cifItems['_exptl_crystal_size_mid'] = "%s" %(size[1])
			self._cifItems['_exptl_crystal_size_max'] = "%s" %(size[2])
		self._cifItems['_diffrn_orient_matrix_UB_11'] = "%f" %float(matrix[0])
		self._cifItems['_diffrn_orient_matrix_UB_12'] = "%f" %float(matrix[1])
		self._cifItems['_diffrn_orient_matrix_UB_13'] = "%f" %float(matrix[2])
		self._cifItems['_diffrn_orient_matrix_UB_21'] = "%f" %float(matrix[3])
		self._cifItems['_diffrn_orient_matrix_UB_22'] = "%f" %float(matrix[4])
		self._cifItems['_diffrn_orient_matrix_UB_23'] = "%f" %float(matrix[5])
		self._cifItems['_diffrn_orient_matrix_UB_31'] = "%f" %float(matrix[6])
		self._cifItems['_diffrn_orient_matrix_UB_32'] = "%f" %float(matrix[7])
		self._cifItems['_diffrn_orient_matrix_UB_33'] = "%f" %float(matrix[8])
		
		ccdparam = header_d['CCDPARM'].split()
		self._saint_cfg.setdefault("READNOISE", ccdparam[0])
		self._saint_cfg.setdefault("EPERADU", ccdparam[1])
		self._saint_cfg.setdefault("EPERPHOTON", ccdparam[2])
		
		ccdparam = header_d['DETTYPE'].split()
		if ccdparam[0] == "CCD-PXL-L6000":
			self._saint_cfg.setdefault("PIXPERCM", ccdparam[1])
			self._saint_cfg.setdefault("CM_TO_GRID", ccdparam[2])
			self._saint_cfg.setdefault("BRASS_SPACING", ccdparam[4])
			self._saint_cfg.setdefault("D_ATTENUATION", "31.1977")
			self._cifItems.setdefault("_diffrn_measurement_device_type", "BRUKER SMART CCD 6000")
			self._cifItems.setdefault("_diffrn_detector_area_resol_mean", "8")
			
		if ccdparam[0] == "CCD-PXL":
			self._saint_cfg.setdefault("PIXPERCM", 81.920)
			self._saint_cfg.setdefault("CM_TO_GRID", 0.800)
			self._saint_cfg.setdefault("BRASS_SPACING", 0.2540)
			self._cifItems.setdefault("_diffrn_measurement_device_type", "BRUKER SMART CCD 1000")
			self._cifItems.setdefault("_diffrn_detector_area_resol_mean", "8")
			
	def cifItems(self):
		return self._cifItems
	
	def saint_cfg(self):
		return self._saint_cfg

class reader:
	def __init__(self, path):
		self._cifItems = {}
		self._saint_cfg = {}
		
		rFile = open(path, 'r')
		value = ""
		previousHeader = ""
		header_d = {}
		data = rFile.read()
		m = 0
		while "............................" not in data[m:m+80]:
			try:
				n = m + 8
				header = data[m:n]
				m = n
				n = m + 72
				value = data[m:n]
				m = n
				
				header = header.strip(':').strip()
				value = value.strip()
				if header == "":
					break
				if header != previousHeader:
					header_d.setdefault(header,value)
				else:
					header_d[header] += " %s" %value
				previousHeader = header
				
			except:
				break
			
		a = header_d['CSIZE'].split('|')
		a.sort()
		size = []
		for i in a:
			try:
				float(i)
				size.append(i)
			except:
				pass
			
		matrix = header_d['MATRIX'].split()
		
		self._cifItems['_diffrn_source_voltage'] = "%.0f" %float(header_d['SOURCEK'])
		self._cifItems['_diffrn_source_current'] = "%.0f" %float(header_d['SOURCEM'])
		self._cifItems['_diffrn_refln_scan_width'] = "%.2f" %float(header_d['RANGE'])
		self._cifItems['time'] = "%.2f" %float(header_d['CUMULAT'])
		self._cifItems['formula'] = "%s" %(header_d['CHEM'])
		self._cifItems['_diffrn_radiation_monochromator'] = header_d['FILTER']
		self._cifItems['_diffrn_radiation_wavelength'] = "%f" %float(header_d['WAVELEN'].split()[0])
		self._cifItems['_exptl_crystal_description'] = "%s" %(header_d['MORPH'])
		self._cifItems['_exptl_crystal_colour'] = "%s" %(header_d['CCOLOR'])
		if len(size) == 3:
			self._cifItems['_exptl_crystal_size_min'] = "%s" %(size[0])
			self._cifItems['_exptl_crystal_size_mid'] = "%s" %(size[1])
			self._cifItems['_exptl_crystal_size_max'] = "%s" %(size[2])
		self._cifItems['_diffrn_orient_matrix_UB_11'] = "%f" %float(matrix[0])
		self._cifItems['_diffrn_orient_matrix_UB_12'] = "%f" %float(matrix[1])
		self._cifItems['_diffrn_orient_matrix_UB_13'] = "%f" %float(matrix[2])
		self._cifItems['_diffrn_orient_matrix_UB_21'] = "%f" %float(matrix[3])
		self._cifItems['_diffrn_orient_matrix_UB_22'] = "%f" %float(matrix[4])
		self._cifItems['_diffrn_orient_matrix_UB_23'] = "%f" %float(matrix[5])
		self._cifItems['_diffrn_orient_matrix_UB_31'] = "%f" %float(matrix[6])
		self._cifItems['_diffrn_orient_matrix_UB_32'] = "%f" %float(matrix[7])
		self._cifItems['_diffrn_orient_matrix_UB_33'] = "%f" %float(matrix[8])
		
		ccdparam = header_d['CCDPARM'].split()
		self._saint_cfg.setdefault("READNOISE", ccdparam[0])
		self._saint_cfg.setdefault("EPERADU", ccdparam[1])
		self._saint_cfg.setdefault("EPERPHOTON", ccdparam[2])
		
		ccdparam = header_d['DETTYPE'].split()
		if ccdparam[0] == "CCD-PXL-L6000":
			self._saint_cfg.setdefault("PIXPERCM", ccdparam[1])
			self._saint_cfg.setdefault("CM_TO_GRID", ccdparam[2])
			self._saint_cfg.setdefault("BRASS_SPACING", ccdparam[4])
			self._saint_cfg.setdefault("D_ATTENUATION", "31.1977")
			self._cifItems.setdefault("_diffrn_measurement_device_type", "BRUKER SMART CCD 6000")
			self._cifItems.setdefault("_diffrn_detector_area_resol_mean", "8")
			
		if ccdparam[0] == "CCD-PXL":
			self._saint_cfg.setdefault("PIXPERCM", 81.920)
			self._saint_cfg.setdefault("CM_TO_GRID", 0.800)
			self._saint_cfg.setdefault("BRASS_SPACING", 0.2540)
			self._cifItems.setdefault("_diffrn_measurement_device_type", "BRUKER SMART CCD 1000")
			self._cifItems.setdefault("_diffrn_detector_area_resol_mean", "8")
			
	def cifItems(self):
		return self._cifItems
	
	def saint_cfg(self):
		return self._saint_cfg
		

#class bruker_frame:
	#def __init__(self, path):
		#self.path = path
		
	#def read_frame(self):
		#rFile = open(self.path, 'r')
		#value = ""
		#previousHeader = ""
		#header_d = {}
		#data = rFile.read()
		#m = 0
		#while "............................" not in data[m:m+80]:
			#try:
				#n = m + 8
				#header = data[m:n]
				#m = n
				#n = m + 72
				#value = data[m:n]
				#m = n
				
				#header = header.strip(':').strip()
				#value = value.strip()
				#if header == "":
					#break
				#if header != previousHeader:
					#header_d.setdefault(header,value)
				#else:
					#header_d[header] += " %s" %value
				#previousHeader = header
				
			#except:
				#break
			
		#a = header_d['CSIZE'].split('|')
		#a.sort()
		#size = []
		#for i in a:
			#try:
				#float(i)
				#size.append(i)
			#except:
				#pass
			
		#matrix = header_d['MATRIX'].split()
		
		#frame = {}
		#frame['_diffrn_source_power'] = "%.0f" %float(header_d['SOURCEK'])
		#frame['_diffrn_source_current'] = "%.0f" %float(header_d['SOURCEM'])
		#frame['_diffrn_refln_scan_width'] = "%.2f" %float(header_d['RANGE'])
		#frame['time'] = "%.2f" %float(header_d['CUMULAT'])
		#frame['formula'] = "%s" %(header_d['CHEM'])
		#frame['_diffrn_radiation_monochromator'] = header_d['FILTER']
		#frame['_diffrn_radiation_wavelength'] = "%f" %float(header_d['WAVELEN'].split()[0])
		#frame['_exptl_crystal_description'] = "%s" %(header_d['MORPH'])
		#frame['_exptl_crystal_colour'] = "%s" %(header_d['CCOLOR'])
		#if len(size) == 3:
			#frame['_exptl_crystal_size_min'] = "%s" %(size[0])
			#frame['_exptl_crystal_size_mid'] = "%s" %(size[1])
			#frame['_exptl_crystal_size_max'] = "%s" %(size[2])
		#frame['_diffrn_orient_matrix_UB_11'] = "%f" %float(matrix[0])
		#frame['_diffrn_orient_matrix_UB_12'] = "%f" %float(matrix[1])
		#frame['_diffrn_orient_matrix_UB_13'] = "%f" %float(matrix[2])
		#frame['_diffrn_orient_matrix_UB_21'] = "%f" %float(matrix[3])
		#frame['_diffrn_orient_matrix_UB_22'] = "%f" %float(matrix[4])
		#frame['_diffrn_orient_matrix_UB_23'] = "%f" %float(matrix[5])
		#frame['_diffrn_orient_matrix_UB_31'] = "%f" %float(matrix[6])
		#frame['_diffrn_orient_matrix_UB_32'] = "%f" %float(matrix[7])
		#frame['_diffrn_orient_matrix_UB_33'] = "%f" %float(matrix[8])
		
		#saint_cfg = {}
		
		#ccdparam = header_d['CCDPARM'].split()
		#saint_cfg.setdefault("READNOISE", ccdparam[0])
		#saint_cfg.setdefault("EPERADU", ccdparam[1])
		#saint_cfg.setdefault("EPERPHOTON", ccdparam[2])
		
		#ccdparam = header_d['DETTYPE'].split()
		#if ccdparam[0] == "CCD-PXL-L6000":
			#saint_cfg.setdefault("PIXPERCM", ccdparam[1])
			#saint_cfg.setdefault("CM_TO_GRID", ccdparam[2])
			#saint_cfg.setdefault("BRASS_SPACING", ccdparam[4])
			#saint_cfg.setdefault("D_ATTENUATION", "31.1977")
			#frame.setdefault("_diffrn_measurement_device_type", "BRUKER SMART-CCD 6K")
			#frame.setdefault("_diffrn_detector_area_resol_mean", "8")
			
		#if ccdparam[0] == "CCD-PXL":
			#saint_cfg.setdefault("PIXPERCM", 81.920)
			#saint_cfg.setdefault("CM_TO_GRID", 0.800)
			#saint_cfg.setdefault("BRASS_SPACING", 0.2540)
			#frame.setdefault("_diffrn_measurement_device_type", "BRUKER SMART-CCD 1K")
			#frame.setdefault("_diffrn_detector_area_resol_mean", "8")
		#self.saint_cfg = saint_cfg
		
		#return frame
	
if __name__ == '__main__':
	#a = bruker_frame('C:/datasets/08srv071/frm071_1.001')
	#frame = a.read_frame()
	#a = reader('C:/datasets/08srv071/frm071_1.001')
	#print a.cifItems()
	#print a.saint_cfg()
	a = BrukerFrame('C:/datasets/08srv071/frm071_1.001')
	print a.cifItems()
	print a.saint_cfg()
	