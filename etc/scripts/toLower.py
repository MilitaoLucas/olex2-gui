import olexex
import olx
for a in olexex.OlexRefinementModel().atoms():
  l = a['type'] + a['label'][len(a['type']):].lower()
  if l != a['label']:
    print(a['label'] + " -> " + l)
    olx.xf.au.SetAtomlabel(a['aunit_id'], l)
