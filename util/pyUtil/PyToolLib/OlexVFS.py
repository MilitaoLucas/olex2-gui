import olex
import olex_fs
import io

class ImageWriter:
  def __init__(self):
    self.position = 0
    self.data = b""
    self.name = ""

  def setName(self, name):
    self.name = name
    self.data = b""

  def endWrite(self, isPersistent):
    if self.data:
      olex.writeImage(self.name, self.data, isPersistent)

  def write(self, data):
    self.data += data

  def seek(self, a, b):
    self.position = b

  def tell(self):
    return self.position

ImageToOlexWriter = ImageWriter()

def copy_image(name_from, name_to):
  f = olex.readImage(name_from)
  olex.writeImage(name_to, f)

def save_image_to_olex(image, name, isPersistent=0):
  buf = io.BytesIO()
  image.save(buf, format="PNG")
  data = buf.getvalue()
  olex.writeImage(str(name), data, int(isPersistent))

def write_to_olex(filename, data, isPersistent=0):
  if isinstance(data, str):
    data = data.encode("utf-8")
  elif isinstance(data, (bytearray, memoryview)):
    data = bytes(data)
  elif not isinstance(data, bytes):
    raise TypeError("Data must be bytes, bytearray, memoryview, or str")
  olex.writeImage(str(filename), data, int(isPersistent))

def read_from_olex(filename):
  try:
    return olex.readImage(filename)
  except:
    return None

def exists(filename):
  return olex_fs.Exists(filename)

olex.registerFunction(read_from_olex, False, "vfs")
