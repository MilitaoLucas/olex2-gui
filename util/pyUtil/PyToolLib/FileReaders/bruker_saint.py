# bruker_saint.py

class reader:
	def __init__(self, path):	
		"""Reads the saint.ini file with the given path.
		
		Returns a dictionary of cif items found in the saint.ini file."""
		
		self._cifItems = {}
		rfile = open(path, 'r')
		lines = {}
		
		i = 0
		for line in rfile:
			lines[i] = line.strip()
			i += 1
			
		i = 0
		for line in lines:
			try:
				if lines[i][:7] == "VERSION":
					self._cifItems.setdefault("prog_version", lines[i][-6:])
					
			except:
				i += 1
				pass
			i += 1

	def cifItems(self):
		return self._cifItems

if __name__ == '__main__':
	a = bruker_saint('C:/datasets/08srv071/work/saint.ini')
	saint = a.cifItems()
	print
