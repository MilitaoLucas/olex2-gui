# cif_reader.py

class reader:
	def __init__(self, path):
		"""Reads the *.cif file with the given path.
		
		Returns a dictionary of cif items found in the *.cif file."""
		
		self._cifItems = {}
		special_details = {}
		
		rFile = open(path, 'r')
		lines = []
		
		#for line in rFile:
			#lines.append(line.strip())
		
		lines = [line.strip() for line in rFile]
		a = -1
		for li in lines:
			a += 1
			#li = li.strip()
			if not li:
				continue
			
			l = li.split()
			if len(l) <= 1:
				i = 1
				value = ""
				if li == "\n":
					continue
				if li[:1] == ';':
					continue
				if li[:1] == "_":
					field = li.strip()
					value += "%s" %(lines[a+i])
					i+= 1
					while lines[a+i][:1] != ";":
						value += "\n%s" %(lines[a+i])
						i+=1
					value += "\n;"
					self._cifItems.setdefault(field,value)
					
			elif li[0] == '_':
				l = li.split()
				field = l[0].strip()
				value = li.split(field)[1].strip(' \'"')
				self._cifItems.setdefault(field,value)
		
		#mcif = inputText.split('\n')
		
		#meta = []
		#a = -1
		#for line in mcif:
			#a+= 1
			#field = ""
			#apd=""
			#l = line.split()
			#if len(l) <= 1:
				#i = 1
				#value = ""
				#if line == "\n":
					#continue
				#if line[:1] == ';':
					#continue
				#if line[:1] == "_":
					#field = line[:-1].strip()
					#value += "%s" %(mcif[a+i])
					#i+= 1
					#while mcif[a+i][:1] != ";":
						#value += "\n%s" %(mcif[a+i])
						#i+=1
					#value += "\n;"
					
					#try:
						#oldValue = OV.FindValue('snum_metacif%s' %field).rstrip().lstrip()
						#if value != oldValue:
							#OV.SetVar('snum_metacif%s' %field,value)
							#variableFunctions.AddVariableToUserInputList('snum_metacif%s' %field)
						#else:
							#continue
					#except:
						#OV.SetVar('snum_metacif%s' %field,value)
			#else:
				#if line[:1] == "_":
					#field = line.split()[0]
					#x = line.split()[1:]
					#value = ""
					#if len(x) > 1:
						#for thing in x:
							#value += "%s " %thing					
					#else:
						#value = x[0]
					#value = value.replace("'", "").rstrip()
					#try:
						#oldValue = OV.FindValue('snum_metacif%s' %field).strip()
						#if value != oldValue:
							#OV.SetVar('snum_metacif%s' %field, value)
							#variableFunctions.AddVariableToUserInputList('snum_metacif%s' %field)
						#else:
							#continue
					#except:
						#OV.SetVar('snum_metacif%s' %field, value)
				#elif line == "\n":
					#continue
				#elif line[:1] == "#":
					#continue
				#else:
					#continue
			
	def cifItems(self):
		return self._cifItems
	
if __name__ == '__main__':
	a = reader('C:\Users\Richard\Documents\My Received Files\DC.cif')
	print a.cifItems()