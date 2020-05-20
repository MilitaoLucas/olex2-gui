import olx

"""
These imports are of user contributed scripts.
This file WILL be updated by us
"""

scripts = [
  'OlexPlaton',
  'OlexMail',
  'OlexCheckCIF',
  'OlexCDS',
  'flipsmall',
  'OlexBET',
  'Olexhole',
  #'OlexSir',
  #'LazyOlex',
]

if olx.HasGUI().lower() == "true":
  scripts += ['Olex2CCDC',
              'Tutorials',
              'XPlain',
              'ZSGH'
              ]



for script in scripts:
  try:
    __import__(script)
  except Exception as ex:
    print("Import from userScripts.py failed: %s" %ex)