# pcf_reader.py

class pcf_reader:
	def __init__(self, path):
		self.path = path
		self.ignore = ["?", "'?'", ".", "'.'"]
		
	def read_pcf(self):
		"""Reads the .pcf file with the given path.
		
		Returns a dictionary of cif items found in the .pcf file."""
		
		pcf = {}
		rfile = open(self.path, 'r')
		lines = {}
		
		i = 0
		for line in rfile:
			lines[i] = line.strip()
			i += 1
			
		i = 0
		
		items = [ 
			"_symmetry_cell_setting",
			"_symmetry_space_group_name_H-M",
			#"_cell_measurement_temperature",
			"_exptl_crystal_description",
			"_exptl_crystal_colour",
			"_exptl_crystal_size_min",
			"_exptl_crystal_size_mid",
			"_exptl_crystal_size_max",
			"_exptl_crystal_density_meas",
			"_exptl_crystal_density_method",
			"_exptl_absorpt_correction_type",
			"_diffrn_radiation_monochromator",
			"_diffrn_source",
			"_diffrn_radiation_type",
			"_diffrn_measurement_device_type",
			"_diffrn_measurement_method",
			"_diffrn_detector_area_resol_mean",
			"_diffrn_standards_number",
			"_diffrn_standards_interval_count",
			#"_diffrn_standards_decay_%",
			"_cell_measurement_reflns_used",
			"_cell_measurement_theta_min",
			"_cell_measurement_theta_max",
			#"_diffrn_ambient_temperature",
		]
		
		for line in lines:
			for item in items:
				try:
					#if line.split()[0] == "%s" %item:
					if lines[i].split()[0] == "%s" %item:
						str_list = lines[i].split()[1:]
						if len(str_list) > 1:
							txt = ' '.join([s for s in str_list])
						else:
							txt = str_list[0]
						txt = txt.strip("'").rstrip()
						#txt = str.strip(txt, "'")
						if txt not in self.ignore:
							pcf.setdefault("%s" %item, "%s" %txt)
				except:
					#i += 1
					pass
			i += 1
		self.pcf_d = pcf
		return pcf
	
if __name__ == '__main__':
	a = pcf_reader('C:/datasets/Richard 4th year project/Crystals/06rjg003/work/rjg003_m.pcf')
	info = a.read_pcf()
	print
	