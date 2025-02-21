#import PngImagePlugin
from PIL import Image
from PIL import ImageFont, ImageDraw, ImageChops, ImageColor

# Rounded corners
# (c) 2008 www.stani.be
# License: same as PIL
cache = {}
CROSS                   = ('Cross')
ROUNDED                 = ('Rounded')
SQUARE                  = ('Square')

CORNERS                 = [ROUNDED,SQUARE,CROSS]
CORNER_ID               = 'rounded_corner_r%d_f%d'
CROSS_POS               = (CROSS,CROSS,CROSS,CROSS)
ROUNDED_POS             = (ROUNDED,ROUNDED,ROUNDED,ROUNDED)
ROUNDED_RECTANGLE_ID    = 'rounded_rectangle_r%d_f%d_s%s_p%s'

def round_image(image,cache={},radius=100,fill=255,pos=ROUNDED_POS,
                back_colour='#FFFFFF', solid_colour=None):
  if image.mode != 'RGBA':
    image = image.convert('RGBA')
  mask    = create_rounded_rectangle(image.size,cache,radius,fill,pos)
  if solid_colour:
    solidcolor = Image.new("RGBA", image.size, solid_colour)
    #mask = Image.eval(mask, lambda p: 255 * (int(p != 0)))
  image.paste(Image.new('RGB',image.size,back_colour),(0,0),
              ImageChops.invert(mask))
  image.putalpha(mask)
  image = image.convert('RGB')
  return image

def create_corner(radius=100,fill=255,factor=50):
  corner  = Image.new('L',(factor*radius,factor*radius),0)
  draw    = ImageDraw.Draw(corner)
  draw.pieslice((0,0,2*factor*radius,2*factor*radius),180,270,fill=fill)
  corner  = corner.resize((radius,radius),Image.LANCZOS)
  return corner

def create_rounded_rectangle(size=(600,400),cache={},radius=100,fill=255,
                             pos=ROUNDED_POS):
  #rounded_rectangle
  im_x, im_y  = size
  rounded_rectangle_id    = ROUNDED_RECTANGLE_ID%(radius,fill,size,pos)
  if rounded_rectangle_id in cache:
    return cache[rounded_rectangle_id]
  else:
    #cross
    cross_id    = ROUNDED_RECTANGLE_ID%(radius,fill,size,CROSS_POS)
    if cross_id in cache:
      cross   = cache[cross_id]
    else:
      cross   = cache[cross_id]   = Image.new('L',size,0)
      draw    = ImageDraw.Draw(cross)
      draw.rectangle((radius,0,im_x-radius,im_y),fill=fill)
      draw.rectangle((0,radius,im_x,im_y-radius),fill=fill)
    if pos==CROSS_POS:
      return cross
    #corner
    corner_id   = CORNER_ID%(radius,fill)
    if corner_id in cache:
      corner  = cache[corner_id]
    else:
      corner  = cache[corner_id] = create_corner(radius,fill)
    #rounded rectangle
    rectangle   = Image.new('L',(radius,radius),255)
    rounded_rectangle   = cross.copy()
    for index, angle in enumerate(pos):
      if angle == CROSS:
        break
      if angle == ROUNDED:
        element = corner
      else:
        element = rectangle
      if index%2:
        x       = im_x-radius
        element = element.transpose(Image.FLIP_LEFT_RIGHT)
      else:
        x       = 0
      if index < 2:
        y       = 0
      else:
        y       = im_y-radius
        element = element.transpose(Image.FLIP_TOP_BOTTOM)
      rounded_rectangle.paste(element,(x,y))
    cache[rounded_rectangle_id] = rounded_rectangle
    return rounded_rectangle

if __name__ == "__main__":
  cache = {}
  image = Image.new('RGB', (50, 20), (80,130,130))
  image.save("C:/fred.png")

  #thumbnail = round_image(image.thumbnail(size, filter), cache, radius)
  thumbnail = round_image(image, cache, 10, solid_colour=(80,130,130))
  thumbnail.save("C:/fred1.png")
