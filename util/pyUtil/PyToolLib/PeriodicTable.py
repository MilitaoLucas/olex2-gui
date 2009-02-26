import olx
class PeriodicTable(object):
  def PeriodicTable(self):
    rFile = open("%s/ptablex.dat" %olx.BaseDir())
    f = rFile.readlines()
    pt = {}
    i = 0
    for li in f:
      if i == 0:
        i += 1
        continue
      i += 1
      li = li.split()
      el = li[0]
      pt.setdefault(el,{})
      pt[el].setdefault('symbol', el)
      pt[el].setdefault('mass', float(li[1]))
      pt[el].setdefault('name', li[2])
      pt[el].setdefault('Z', i-1)
    return pt
      
if __name__ == "__main__":
  a = PeriodicTable()
  a.PeriodicTable()
