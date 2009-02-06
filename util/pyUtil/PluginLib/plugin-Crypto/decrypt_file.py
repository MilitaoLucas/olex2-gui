import sys
import ezPyCrypto
import olx
import olexex

class decrypt_file():

  def __init__(self, fileObj, src_directory, plugin_directory, key_directory):
    self.fileObj = fileObj
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
    
    # Read in an encrypted file
    rFile = self.fileObj
    #rFile = open(r"%s/%s_d" %(self.src_directory, self.filename), 'rb')
    encoded_script_text = rFile.read()
    rFile.close()
    
    # Decrypt this file
    txt = k.decString(encoded_script_text)
    
    # Spill the beans
    return txt
