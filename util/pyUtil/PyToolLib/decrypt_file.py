import sys
import ezPyCrypto
import olx
import olexex
import os

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
    passding = "%s%s%s"%(cr1,cr2,self.keyname)
    k = ezPyCrypto.key(pubprivkey,passphrase=passding)
    
    # Decrypt this file
    txt = k.decString(self.fileContent)
    
    # Spill the beans
    return txt
  
  def sign_file(self, cr1, cr2, file_name):
    path = "%s/%s" %(self.key_directory, file_name)
    
    fd = open(r"%s/%s.priv" %(self.key_directory, self.keyname), "rb")
    pubprivkey = fd.read()
    fd.close()
    passding = "%s%s%s"%(cr1,cr2,self.keyname)
    k = ezPyCrypto.key(pubprivkey,passphrase=passding)
    
    wFile = open(path,'a')
    wFile.write(self.fileContent)
    wFile.close()
    
    fd = open(path)
    doctxt = fd.read()
    fd.close()
    
    sig = k.signString(doctxt)

    # Write out the signature
    fd = open("%s.sig" %path, "w")
    fd.write(sig)
    fd.close()
    
  def read_signed_file(self, cr1, cr2, file_name):
    path = "%s/%s" %(self.key_directory, file_name)
    fd = open(r"%s/%s.priv" %(self.key_directory, self.keyname), "rb")
    pubprivkey = fd.read()
    fd.close()
    passding = "%s%s%s"%(cr1,cr2,self.keyname)
    k = ezPyCrypto.key(pubprivkey,passphrase=passding)
    
    if os.path.exists(path):
      fd = open(path)
      doc = fd.read()
      fd.close()
    else:
      print("No demo licence file found.")
      return False
#      self.sign_file(cr1, cr2, file_name)
#      return self.fileContent
      
    
    # Read in the signature
    fd = open("%s.sig" %path)
    sig = fd.read()
    fd.close()
    if k.verifyString(doc, sig):
      print("Verification successful - signature is authentic")
      return doc
    else:
      print("Verification failed - bad signature")
      return False
      
    
