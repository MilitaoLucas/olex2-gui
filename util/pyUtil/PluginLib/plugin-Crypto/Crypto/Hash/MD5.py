
# Just use the MD5 module from the Python standard library

__revision__ = "$Id: MD5.py,v 1.4 2002/07/11 14:31:19 akuchling Exp $"


import hashlib
def new(data=""):
    return hashlib.md5(data)
digest_size = new().digest_size


#from md5 import *

#import md5
#if hasattr(md5, 'digestsize'):
    #digest_size = digestsize
    #del digestsize
#del md5

