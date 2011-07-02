# (c) Oleg Dolomanov, OlexSys, 2011
# After importing this, urllib2.HTTPHandler and urllib2.HTTPSHandler
# will be overwritten with classes of this file
# Inspired by:
#   urllib2_file, 
#   http://stackoverflow.com/questions/4434170/
#   http://code.activestate.com/recipes/146306/

import mimetools
import mimetypes
import os
import stat
import urllib
import urllib2
import httplib
import socket
from urlparse import urlparse

class Multipart:
  """ A component of form-data - multipart request """
  def __init__(self, item, name, boundary):
    self.item = item
    self.file_size = None
    header = []
    header.append('--%s' %boundary)
    if isinstance(item, file):
      # not everyone is keen in providing normalised paths
      file_name = item.name.replace('\\', '/').split('/')[-1].encode('UTF-8')
      header.append('Content-Disposition: form-data; name="%s"; filename="%s"'
                         %(name, file_name))
      mime_type = mimetypes.guess_type(file_name)[0]
      if mime_type is None:
        mime_type = "application/octet-stream"
      header.append('Content-Type: %s' %mime_type)
      self.file_size = os.fstat(item.fileno())[stat.ST_SIZE]
      header.append('Content-Length: %i' %self.file_size)
      header.append('')
      header.append('')
    else:
      header.append('Content-Disposition: form-data; name="%s"' %name)
      header.append('')
      header.append(str(item).encode('UTF-8'))
      header.append('')
    self.header = '\r\n'.join(header)
    
    
  def send(self, sock):
    sock.send(self.header)
    if self.file_size is not None:
      self.item.seek(0)
      sz = 0xFFFF+1
      bf = self.item.read(sz)
      while bf:
        sock.send(bf)
        bf = self.item.read(sz)
      sock.send('\r\n')
  
  def calc_size(self):
    if self.file_size is not None:
      return len(self.header) + self.file_size + 2
    return len(self.header)

class MultipartRequest:
  """ Creates a multipart request, use 'direct' method for invoking
  this directly
  """
  def __init__(self, items):
    self.boundary = mimetools.choose_boundary()
    self.parts = []
    self.length = 0
    if isinstance(items, dict):
      items = items.items()
    
    for key, value in items:
      mp = Multipart(value, key, self.boundary)
      self.parts.append(mp)
      self.length += mp.calc_size()
    self.header_ending = '\r\n--%s--\r\n\r\n' %self.boundary
    self.length += len(self.header_ending)

  def do_request(self, connection):
    connection.putheader('Content-Type',
                         'multipart/form-data; boundary=%s' %self.boundary)
    connection.putheader('Content-Length', str(self.length))
    connection.endheaders()
    for p in self.parts:
      p.send(connection)
    connection.send(self.header_ending)

  def direct(self, url, proxy=None):
    if proxy:
      u = urlparse(proxy)
    else:
      u = urlparse(url)
    hc = httplib.HTTPConnection(u.hostname, u.port)
    hc.connect()
    if proxy:
      hc.putrequest('POST', urllib.quote(url))
    else:
      hc.putrequest('POST', urllib.quote(u.path))
    self.do_request(hc)
    return hc.getresponse()

#below are to be used with urllib2
class MultipartHandler():
  def do_open(self, sender, http_class, request):
    has_file = False
    items = {}
    data = request.get_data()
    if request.has_data():
      dt = None
      if isinstance(data, dict):  dt = data.items()
      elif isinstance(data, tuple):  dt = data
      if dt is not None:
        for (k,v) in dt:
          if isinstance(v, file):
            has_file = True
            break
      if not has_file and dt is not None:
        data = urllib.urlencode(data)
    host = request.get_host()
    if not host:
      raise urllib2.URLError('no host given')
    h = http_class(host)
    scheme, sel = urllib.splittype(request.get_selector())
    sel_host, sel_path = urllib.splithost(sel)
    if request.has_data():
      h.putrequest('POST', request.get_selector())
      if request.has_data() and not has_file:
        h.putheader('Content-Type', 'application/x-www-form-urlencoded')
        h.putheader('Content-Length', str(len(data)))
    else:
      h.putrequest('GET', request.get_selector())
    h.putheader('Host', sel_host or host)
    # add any inherited headers    
    for name, value in sender.parent.addheaders:
      name = name.capitalize()
      if name not in request.headers:
        h.putheader(name, value)
      for k, v in request.headers.items():
        h.putheader(k, v)
    try:
      if has_file:
        mq = MultipartRequest(request.get_data())
        mq.do_request(h)
      else:
        h.endheaders()
        if request.has_data():
          h.send(data)
    except socket.error, e:
      raise urllib2.URLError(e)
    code, msg, hdrs = h.getreply()
    fp = h.getfile()
    if code == 200: #HTTP OK
      response = urllib.addinfourl(fp, hdrs, request.get_full_url())
      response.code = code
      response.msg = msg
      return response
    else:
      return sender.parent.error('http', request, fp, code, msg, hdrs)

class HTTPMultipartHandler(urllib2.HTTPHandler):
  def http_open(self, request):
    return MultipartHandler().do_open(self, httplib.HTTP, request)

class HTTPSMultipartHandler(urllib2.HTTPSHandler):
  def https_open(self, request):
    return MultipartHandler().do_open(self, httplib.HTTPS, request)

urllib2.HTTPHandler = HTTPMultipartHandler
urllib2.HTTPSHandler = HTTPSMultipartHandler
