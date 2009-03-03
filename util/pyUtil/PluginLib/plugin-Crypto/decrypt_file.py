import sys
import ezPyCrypto
import olx
import olexex

class decrypt_file():

  def __init__(self, fileContent, src_directory, plugin_directory, key_directory):
    self.fileContent = fileContent
    self.src_directory = src_directory
    self.plugin_directory = plugin_directory
    self.key_directory = key_directory
    self.keyname = olexex.getKey(self.key_directory)
    
   
  def decrypt_file(self, cr1, cr2):
    
    # Read in a private key
    fd = open(r"%s/%s.priv" %(self.key_directory, self.keyname), "rb")
    pubprivkey = fd.read()
    fd.close()
    
    # Create a key object, and auto-import private key
    passding = "%s%s"%(cr1,cr2)
    k = ezPyCrypto.key(pubprivkey,passphrase=passding)
    
    # Decrypt this file
    txt = k.decString(self.fileContent)
    
    # Spill the beans
    return txt
