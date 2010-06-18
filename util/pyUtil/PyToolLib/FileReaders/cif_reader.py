# cif_reader.py

class reader:
  def __init__(self, path):
    """Reads the *.cif file with the given path.

    Returns a dictionary of cif items found in the *.cif file."""

    self._cifItems = {}
    special_details = {}
    rFile = open(path, 'r')
    lines = []
    lines = [line.strip() for line in rFile]
    a = -1
    for li in lines:
      a += 1
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

  def cifItems(self):
    return self._cifItems
