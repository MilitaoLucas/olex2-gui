import olex

class ImageWriter:
  def init(self):
    self.position = 0
    self.data = ""
    self.name = ""

  def setName(self, name):
    self.name = name
    self.data = ""

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
  ImageToOlexWriter.setName(name)
  image.save(ImageToOlexWriter, "PNG")
  ImageToOlexWriter.endWrite(isPersistent)

def write_to_olex(filename, data, isPersistent=False):
  olex.writeImage(filename, data, isPersistent)	
  
def read_from_olex(filename):
  return olex.readImage(filename)
  
 
