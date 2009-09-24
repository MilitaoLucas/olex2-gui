# p4p_reader.py

class p4p_reader:
	def __init__(self, path):
		self.path = path
		
	def read_p4p(self):
		"""Reads the .p4p file with the given path.
		
		Returns a dictionary of cif items found in the p4p file."""
		
		rFile = open(self.path, 'r')
		p4p = []
		for line in rFile:
			p4p.append(line)
		p4p_key = {"raw":{}, "cif":{}}
		i = 0
		for li in p4p:
			li = li.strip()
			if not li:
				continue
			if li[:2] == "  ":
				continue
			l = li.split()
			field = l[0].strip()
			value = li.split(field)[1].strip()
			if field != "REF05":
				p4p_key["raw"].setdefault(field, value)
			else: break
			
		ciflist=["_diffrn_source","_diffrn_radiation_wavelength","_diffrn_source_voltage","_diffrn_source_current","_diffrn_source_target"]
		have_cif_item = False
		value = ""
		for item in ciflist:
			if item == "_diffrn_source_target":
				if p4p_key["raw"]["SOURCE"]:
					value = p4p_key["raw"]["SOURCE"].split()[0]
			elif item == "_diffrn_radiation_wavelength":
				if p4p_key["raw"]["SOURCE"]:
					value = p4p_key["raw"]["SOURCE"].split()[1]
			elif item == "_diffrn_source_voltage":
				try:
					if p4p_key["raw"]["SOURCE"]:
						value = float(p4p_key["raw"]["SOURCE"].split()[5])
				except:
					value = "n/a"
			elif item == "_diffrn_source_current":
				try:
					if p4p_key["raw"]["SOURCE"]:
						value = float(p4p_key["raw"]["SOURCE"].split()[6])
				except:
					value = "n/a"
					
			if value and item == "_diffrn_source_target":
				p4p_key["cif"].setdefault('_diffrn_radiation_type', r"%s K\a" %value)
				have_cif_item = True
			elif value:
				p4p_key["cif"].setdefault(item, value)
				
		if p4p_key["cif"].has_key('_diffrn_source_voltage') and p4p_key["cif"].has_key('_diffrn_source_current'):
			p4p_key["cif"].setdefault('_diffrn_source_power', (p4p_key["cif"]['_diffrn_source_voltage'] * p4p_key["cif"]['_diffrn_source_current'])/1000)
		
		return p4p_key["cif"]
	
if __name__ == '__main__':
	a = p4p_reader('C:/datasets/08srv071/first.p4p')
	info = a.read_p4p()
	print
	