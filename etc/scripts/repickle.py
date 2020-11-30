import olx
import pickle

#read the pickle
fn = "%s/people.pickle" %olx.DataDir()
f = open(fn, "rb")
data = pickle.load(f)
f.close()
#create a huma readible file
tmp_fn = "%s/people.pickle.tmp" %olx.DataDir()
f = open(tmp_fn, "w")
for k, v in data.items():
  for k1, v1 in v.items():
    f.write("%s\n" %k1)
    for k2, v2 in v1.items():
      f.write("    %s: %s\n" %(k2, v2))
f.close()
#edit the file
olx.Exec("notepad -o -s '%s'" %tmp_fn)
#update the data
f = open(tmp_fn, "r")
dt = {}
data[list(data.keys())[0]] = dt
last_p = None
for l in f:
  l = l.rstrip()
  if not l: continue
  if l.startswith(' '):
    if last_p is None:
      raise Exception('Invalid syntax')
    l = l.strip().split(':')
    if len(l) != 2:
      raise Exception('Invalid syntax: numer of tokens')
    last_p[l[0]] = l[1]
    print("  New field %s: %s" %(l[0], l[1]))
  else:
    last_p = {}
    dt[l] = last_p
    print('New person: %s' %l)
f.close()
#store new data
f = open(fn, "wb")
pickle.dump(data, f)
f.close()