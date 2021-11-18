# (c) Oleg Dolomanov, OlexSys, 2011
# After importing this, urllib2.HTTPHandler and urllib2.HTTPSHandler
# will be overwritten with classes of this file
# Inspired by:
#   urllib2_file,
#   http://stackoverflow.com/questions/4434170/
#   http://code.activestate.com/recipes/146306/

from email.generator import Generator
from ssl import SSLCertVerificationError
import uuid
import mimetypes
import os
import io
import stat
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import http.client
import socket
from urllib.parse import urlparse

class Multipart:
  """ A component of form-data - multipart request """
  def __init__(self, item, name, boundary):
    if item is None:
      item = ""
    self.item = item
    self.file_size = None
    header = []
    header.append('--%s' %boundary)
    if isinstance(item, io.IOBase):
      # not everyone is keen in providing normalised paths
      file_name = item.name.replace('\\', '/').split('/')[-1]
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
      if isinstance(self.item, str):
        self.item = self.item.encode("utf-8")
    header.append('')
    header.append('')
    self.header = '\r\n'.join(header).encode("utf-8")


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
    sock.send(b'\r\n')

  def calc_size(self):
    if self.file_size is not None:
      return len(self.header) + self.file_size + 2
    return len(self.header) + len(self.item) + 2

class MultipartRequest:
  def __init__(self, items):
    self.boundary = '--%s--' %uuid.uuid4().hex
    self.parts = []
    self.length = 0
    if isinstance(items, dict):
      items = items.items()

    for key, value in items:
      mp = Multipart(value, key, self.boundary)
      self.parts.append(mp)
      self.length += mp.calc_size()
    self.header_ending = ('\r\n--%s--\r\n\r\n' %self.boundary).encode("utf-8")
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
      self.data = urllib.parse.urlencode(items).encode()

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
          if isinstance(v, io.IOBase):
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
    hc = http.client.HTTPConnection(u.hostname, u.port)
    hc.connect()
    if proxy:
      hc.putrequest(self.get_method(), urllib.parse.quote(url))
    else:
      hc.putrequest(self.get_method(), urllib.parse.quote(u.path))
    self.do_request(hc)
    return hc.getresponse()

#below are to be used with urllib2
class RequestHandler():
  def set_connection(self, sender, request, fall_back=False):
    handler = DirectRequest(request.data).select_handler()
    conn = sender.create(request.host, fall_back)
    conn.putrequest(handler.get_method(), request.selector)
    conn.timeout = request.timeout
    for name, value in sender.parent.addheaders:
      name = name.capitalize()
      if name not in request.headers:
        conn.putheader(name, value)
      for k, v in request.headers.items():
        conn.putheader(k, v)
    return (handler, conn)

  def do_open(self, sender, request):
    host = request.host
    if not host:
      raise urllib.error.URLError('no host given')
    handler, h = self.set_connection(sender, request)
    try:
      handler.do_request(h)
    except SSLCertVerificationError as ssle:
      try:
        handler, h = self.set_connection(sender, request, fall_back=True)
        handler.do_request(h)
      except Exception as exc:
        print("Failed to process SSL request: %s" %str(exc))
        raise urllib.error.URLError(ssle)
    except socket.error as e:
      raise urllib.error.URLError(e)
    response = h.getresponse()
    if response.getcode() == 200: #HTTP OK
      return response
    else:
      return sender.parent.error('http', request, response,
        response.getcode(), response.msg, response.getheaders())

class HTTPHandler(urllib.request.HTTPHandler):
  def http_open(self, request):
    return RequestHandler().do_open(self, request)

  def create(self, host, fall_back):
    return http.client.HTTPConnection(host)

urllib.request.HTTPHandler = HTTPHandler

try:
  import ssl
  fs_ssl_context = ssl.create_default_context()
  fs_ssl_context.check_hostname = False
  fs_ssl_context.verify_mode = ssl.CERT_NONE
  ssl_warning_printed = False

  class HTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, request):
      return RequestHandler().do_open(self, request)

    def create(self, host, fall_back=False):
      if fall_back:
        global ssl_warning_printed
        if not ssl_warning_printed:
          print("!!! DISABLING SSL CERTIFICATE VALIDATION FOR %s" %host)
          print("!!! CHECK THAT YOUR ROOT CA CERTIFICATES ARE UP-TO-DATE !!!")
          # print every time for now
          #ssl_warning_printed = True
        return http.client.HTTPSConnection(host, context=fs_ssl_context)
      return http.client.HTTPSConnection(host)


  urllib.request.HTTPSHandler = HTTPSHandler
  import sys
  if sys.platform == 'darwin' or sys.platform[:3] == 'lin':
    ssl_certs = os.environ.get('SSL_CERT_FILE', None)
    if not ssl_certs or not os.path.exists(ssl_certs):
      ca_paths = ['/etc/ssl/certs/ca-certificates.crt', # ubuntu
        '/etc/ssl/certs/ca-bundle.crt', #centos
        '/etc/ssl/cert.pem'] #mac
      for p in ca_paths:
        if os.path.exists(p):
          os.environ['SSL_CERT_FILE'] = p
          break
except:
  print('HTTPS handler is not installed')
