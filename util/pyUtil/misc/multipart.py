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
    else:
      header.append('Content-Disposition: form-data; name="%s"' %name)
      if not isinstance(self.item, str):
        self.item = str(self.item)
    header.append('')
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
    else:
      sock.send(self.item)
    sock.send('\r\n')

  def calc_size(self):
    if self.file_size is not None:
      return len(self.header) + self.file_size + 2
    return len(self.header) + len(self.item) + 2

class MultipartRequest:
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

  def get_method(self):
    return 'POST'

class EncodedURLRequest:
  def __init__(self, items=None):
    self.data = None
    if items:
      self.data = urllib.urlencode(items)

  def do_request(self, connection):
    if self.data:
      connection.putheader('Content-Type',
                           'application/x-www-form-urlencoded')
      connection.putheader('Content-Length', str(len(self.data)))
    connection.endheaders()
    if self.data:
      connection.send(self.data)

  def get_method(self):
    if self.data:
      return 'POST'
    return 'GET'

# use this for direct invocation
class DirectRequest:
  def __init__(self, data=None):
    self.data = data

  def select_handler(self):
    has_file = False
    if self.data is not None:
      dt = None
      if isinstance(self.data, dict):
        dt = self.data.items()
      elif isinstance(self.data, tuple):
        dt = self.data
      elif isinstance(self.data, list):
        dt = self.data
      if dt is not None:
        for (k,v) in dt:
          if isinstance(v, file):
            has_file = True
            break
      if has_file:
        return MultipartRequest(self.data)
    return EncodedURLRequest(self.data)

  def request(self, url, proxy=None):
    r = self.select_handler()
    if proxy:
      u = urlparse(proxy)
    else:
      u = urlparse(url)
    hc = httplib.HTTPConnection(u.hostname, u.port)
    hc.connect()
    if proxy:
      hc.putrequest(self.get_method(), urllib.quote(url))
    else:
      hc.putrequest(self.get_method(), urllib.quote(u.path))
    self.do_request(hc)
    return hc.getresponse()

#below are to be used with urllib2
class RequestHandler():
  def do_open(self, sender, http_class, request):
    host = request.get_host()
    if not host:
      raise urllib2.URLError('no host given')
    handler = DirectRequest(request.get_data()).select_handler()
    h = http_class(host)
    h._conn.timeout = request.timeout
    h.putrequest(handler.get_method(), request.get_selector())
    # set request-host
    scheme, sel = urllib.splittype(request.get_selector())
    sel_host, sel_path = urllib.splithost(sel)
    h.putheader('Host', sel_host or host)
    # add any inherited headers    
    for name, value in sender.parent.addheaders:
      name = name.capitalize()
      if name not in request.headers:
        h.putheader(name, value)
      for k, v in request.headers.items():
        h.putheader(k, v)
    try:
      handler.do_request(h)
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

class HTTPHandler(urllib2.HTTPHandler):
  def http_open(self, request):
    return RequestHandler().do_open(self, httplib.HTTP, request)

urllib2.HTTPHandler = HTTPHandler

try:
  class HTTPSHandler(urllib2.HTTPSHandler):
    def https_open(self, request):
      return RequestHandler().do_open(self, httplib.HTTPS, request)

  urllib2.HTTPSHandler = HTTPSHandler
  import sys
  if sys.platform == 'darwin':
    import ssl
    ssl._https_verify_certificates(False)
except:
  print 'HTTPS handler is not installed'
