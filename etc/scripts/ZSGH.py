from olexFunctions import OlexFunctions
OV = OlexFunctions()
import os
import olx
import sys

class ZSGH:
  def __init__(self):
    if sys.platform[:3] == 'win':
      self.exe_file = olx.file.Which("zsgh.exe")
    else:
      self.exe_file = olx.file.Which("zsgh")
    if not self.exe_file:
      self.exe_file = None

  def exists(self):
    return self.exe_file != None

  def run(self, run_auto=True, sync=False):
    if not self.exe_file:
      print 'Could not locate the ZSGH executable, aborting...'
      return False
    return olx.Exec("zsgh", olx.FileName(), o=True, s=sync)

x = ZSGH()
OV.registerFunction(x.exists, False, 'zsgh')
OV.registerFunction(x.run, False, 'zsgh')
