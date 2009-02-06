# bruker_saint.py

class bruker_saint:
	def __init__(self, path):
		self.path = path
		
	def read_saint(self):		
		"""Reads the saint.ini file with the given path.
		
		Returns a dictionary of cif items found in the saint.ini file."""
		
		saint = {}
		rfile = open(self.path, 'r')
		lines = {}
		
		i = 0
		for line in rfile:
			lines[i] = line.strip()
			i += 1
			
		i = 0
		for line in lines:
			try:
				if lines[i][:7] == "VERSION":
					saint.setdefault("prog_version", lines[i][-6:])
					
			except:
				i += 1
				pass
			i += 1
		self.saint_d = saint    
		return saint   
	
if __name__ == '__main__':
	a = bruker_saint('C:/datasets/08srv071/work/saint.ini')
	saint = a.read_saint()
	print
	