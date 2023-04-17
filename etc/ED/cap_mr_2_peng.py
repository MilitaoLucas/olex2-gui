import sys
import os

mr = {}

for l in open("SFAC_CAP_2022.txt", "r").readlines():
  l = l.strip()
  if not l or l.startswith('#'):  continue
  toks = l.split()
  symb = toks[1].upper()[0]
  if len(toks[1]) >= 2:
    symb += toks[1].lower()[1] 
  mr[symb] = toks[-1]

res = []

for l in open("SFAC_Peng_1999.txt", "r").readlines():
  l = l.strip()
  if not l or l.startswith('#'):
    res.append(l)
    continue
  toks = l.split()
  symb = toks[1].upper()[0]
  if len(toks[1]) >= 2:
    sl = toks[1].lower()[1] 
    if sl >= 'a' and sl <= 'z':
      symb += sl
  m = mr.get(symb, "")
  if not m:
    m = "ZZZ"
  res.append(" ".join(toks[:-1]) + ' ' + m)

with open("SFAC_Peng_1999_.txt", "w") as f:
  f.write("\n".join(res))
  
