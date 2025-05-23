from ArgumentParser import ArgumentParser
from PIL import ImageFont
#import pickle
#import shelve
from PIL import PngImagePlugin
#import FontFile

class FontInstances(ArgumentParser):
  def __init__(self):
    super(FontInstances, self).__init__()
    try:
      OlexFonts = r"%s\OlexFonts.pickle" %self.datadir
      #d = shelve.open(OlexFonts, 'n') # open, with (g)dbm filename -- no suffix
      #self.fonts =  d
      #d.close()       # close it
      #OlexFonts = r"%s\OlexFonts.pickle" %self.datadir
      #self.fonts = pickle.load(OlexFonts)
    except:
      pass

  def pickleFonts(self, font_name, font_size, font):
    import pickle
#    a = FontFile.FontFile()

    OlexFonts = r"%s\OlexFonts.pickle" %self.datadir

    #d = shelve.open(OlexFonts) # open, with (g)dbm filename -- no suffix
    #d = self.fonts   # store data at key (overwrites old data if
                    ## using an existing key)
    #d.close()       # close it


    pFile = open(OlexFonts, 'w')
    p = pickle.dumps(self.fonts)
    pFile.write(p)
    pFile.close()

  def defineFonts(self):
    from olexFunctions import OV
    default_font_name = OV.GetParam("gui.default_font_name")
    default_font_name_bold = OV.GetParam("gui.default_font_name_bold")
    self.fonts = {
      ##################################################### texgyretermes
      "Serif":{
        "font_src":(
          r"texgyretermes-regular.otf",
          r"%s/etc/gui/fonts/texgyretermes-regular.otf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Serif Bold":{
        "font_src":(
          r"texgyretermes-bold.otf",
          r"%s/etc/gui/fonts/texgyretermes-bold.otf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Serif Italic":{
        "font_src":(
          r"texgyretermes-italic.otf",
          r"%s/etc/gui/fonts/texgyretermes-italic.otf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Serif Bold Italic":{
        "font_src":(
          r"texgyretermes-bolditalic.otf",
          r"%s/etc/gui/fonts/texgyretermes-bolditalic.otf" %self.basedir,
          ),
        "fontInstance":{}
          },

      ##################################################### Cambria
      "Cambria":{
        "font_src":(
          r"cambria.ttc",
          r"%s/etc/gui/fonts/Vera.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Cambria Bold":{
        "font_src":(
          r"cambriab.ttc",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Cambria Italic":{
        "font_src":(
          r"cambriai.ttc",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Cambria Bold Italic":{
        "font_src":(
          r"cambriaz.ttc",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      ##################################################### Gerogia
      "Georgia":{
        "font_src":(
          r"georgia.ttf",
          r"%s/etc/gui/fonts/Vera.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Georgia Bold":{
        "font_src":(
          r"georgiab.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Georgia Italic":{
        "font_src":(
          r"georgiai.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Georgia Bold Italic":{
        "font_src":(
          r"georgiaz.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      ##################################################### Verdana
      "Verdana":{
        "font_src":(
          r"verdana.ttf",
          r"%s/etc/gui/fonts/Vera.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },
      "Verdana Bold":{
        "font_src":(
          r"verdanabd.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Verdana Italic":{
        "font_src":(
          r"verdanai.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      ##################################################### Gill
      "Gill":{
        "font_src":(
          r"GIL____.ttf",
          r"%s/etc/gui/fonts/Vera.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },
      "Gill Bold":{
        "font_src":(
          r"GILB____.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Verdana Italic":{
        "font_src":(
          r"GILI____.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },


      ##################################################### Default
      "DefaultFont":{
        "font_src":(
          r"%s/etc/gui/fonts/%s" %(self.basedir,default_font_name),
          default_font_name
          ),
        "fontInstance":{}
          },
      "DefaultFont Bold":{
        "font_src":(
          r"%s/etc/gui/fonts/%s" %(self.basedir,default_font_name_bold),
          default_font_name_bold,
          ),
        "fontInstance":{}
          },
      "DefaultFont Light":{
        "font_src":(
          r"%s/etc/gui/fonts/Signika-Light.ttf" %self.basedir,
          "Signika-Light.ttf",
          ),
        "fontInstance":{}
          },


      ##################################################### Vera
      "Vera":{
        "font_src":(
          r"%s/etc/gui/fonts/Vera.ttf" %self.basedir,
          "verdana.ttf"
          ),
        "fontInstance":{}
          },
      "Vera Bold":{
        "font_src":(
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          "verdanab.ttf",
          ),
        "fontInstance":{}
          },
      "Vera Italic":{
        "font_src":(
          r"%s/etc/gui/fonts/VeraIt.ttf" %self.basedir,
          "verdana.ttf"
          ),
        "fontInstance":{}
          },
      "Vera Bold Italic":{
        "font_src":(
          r"%s/etc/gui/fonts/VeraBI.ttf" %self.basedir,
          "verdanab.ttf",
          ),
        "fontInstance":{}
          },

      ##################################################### Vera Mono
      "VeraMono":{
        "font_src":(
          r"%s/etc/gui/fonts/VeraMono.ttf" %self.basedir,
          "verdana.ttf"
          ),
        "fontInstance":{}
          },
      "VeraMono Bold":{
        "font_src":(
          r"%s/etc/gui/fonts/VeraMoBd.ttf" %self.basedir,
          "verdanab.ttf",
          ),
        "fontInstance":{}
          },
      "VeraMono Italic":{
        "font_src":(
          r"%s/etc/gui/fonts/VeraMoIt.ttf" %self.basedir,
          "verdana.ttf"
          ),
        "fontInstance":{}
          },
      "VeraMono Bold Italic":{
        "font_src":(
          r"%s/etc/gui/fonts/VeraMoBI.ttf" %self.basedir,
          "verdanab.ttf",
          ),
        "fontInstance":{}
          },
      ##################################################### Vera SE
      "VeraSE":{
        "font_src":(
          r"%s/etc/gui/fonts/VeraSe.ttf" %self.basedir,
          "verdana.ttf"
          ),
        "fontInstance":{}
          },
      "VeraSE Bold":{
        "font_src":(
          r"%s/etc/gui/fonts/VeraSeBd.ttf" %self.basedir,
          "verdanab.ttf",
          ),
        "fontInstance":{}
          },

      ##################################################### Arial
      "Arial":{
        "font_src":(
          "Arial.ttf",
          r"%s/etc/gui/fonts/Vera.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Arial Bold":{
        #"font_src":"arialbd.ttf",
        "font_src":(
          "Arialbd.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Arial UTF":{
        "font_src":(
          "arialuni.ttf",
          "arialuni.ttf"
          ),
        "fontInstance":{}
          },

      ##################################################### Chinese
      "Chinese":{
        #"font_src":"arialbd.ttf",
        "font_src":(
          r"%s/etc/gui/fonts/HDZB_7.ttf" %self.basedir,
          r"MSYH.TTF",
          r"simsun.ttc",
          r"arialuni.ttf"
          ),
        "fontInstance":{}
          },

      "Chinese Bold":{
        #"font_src":"arialbd.ttf",
        "font_src":(
          r"MSYHB.TTF",
          ),
        "fontInstance":{}
          },

      "YaHei":{
        "font_src":(
          "MSYH.TTF",
          ),
        "fontInstance":{}
          },

      "YaHei Bold":{
        "font_src":(
          "MSYHB.TTF",
          ),
        "fontInstance":{}
          },

      "Simsun TTC":{
        "font_src":(
          "simsun.ttc",
          "arialuni.ttf"
          ),
        "fontInstance":{}
          },

      "Simhei TTF":{
        "font_src":(
          "simhei.ttf",
          "arialuni.ttf"
          ),
        "fontInstance":{}
          },

      "Simsun TTF":{
        "font_src":(
          "simsun.ttf",
          "simsun.ttf"
          ),
        "fontInstance":{}
          },


      ##################################################### Trebuchet
      "Trebuchet":{
        "font_src":(
          "trebuc.ttf",
          r"%s/etc/gui/fonts/Vera.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },
      "Trebuchet Bold":{
        "font_src":(
        "trebucbd.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
        ),
        "fontInstance":{}
          },

      ##################################################### Courier
      "Courier":{
        "font_src":(
          "cour.ttf",
          r"%s/etc/gui/fonts/Vera.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },
      "Courier Bold":{
        "font_src":(
        "courbd.ttf",
          r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
        ),
        "fontInstance":{}
          },

      ##################################################### Avant Garde
      "Avant Garde":{
        "font_src":(
          "Avant Garde Book BT.ttf",
          r"%s/etc/gui/fonts/Vera.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },
      "Avant Garde Bold":{
        "font_src":(
        "Avant Garde Demi BT.ttf",
        r"%s/etc/gui/fonts/VeraBd.ttf" %self.basedir,
        ),
        "fontInstance":{}
          },



      ##################################################### Garamond
      "Garamond Bold":{
        "font_src":(
          r"Garamondbd.ttf",
          r"Times.ttf",
          r"%s/etc/gui/fonts/VeraSe.ttf" %self.basedir,
          "arial.ttf"
          ),
        "fontInstance":{}
          },

      ##################################################### Times
      "Times":{
        "font_src":(
          "times.ttf",
          r"%s/etc/gui/fonts/VeraSe.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Times Bold Italic":{
        "font_src":(
          "timesbi.ttf",
          r"%s/etc/gui/fonts/VeraSeBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      "Times Bold":{
        "font_src":(
          "timesbd.ttf",
          r"%s/etc/gui/fonts/VeraSeBd.ttf" %self.basedir,
          ),
        "fontInstance":{}
          },

      ##################################################### Various Test Fonts
      "Helvetica":{
        "font_src":(
          r"%s/etc/gui/fonts/HelveticaMedCd.ttf" %self.basedir,
          "trebuchet.ttf"
          ),
        "fontInstance":{}
          },

      "Helvetica Bold":{
        "font_src":(
          r"%s/etc/gui/fonts/HelveticaMedCd.ttf" %self.basedir,
          "trebuchet.ttf"
          ),
        "fontInstance":{}
          },

      "Optane":{
        "font_src":(
          r"%s/etc/gui/fonts/Optane.ttf" %self.basedir,
          "trebuchet.ttf"
          ),
        "fontInstance":{}
          },

      "Optane Bold":{
        "font_src":(
          r"%s/etc/gui/fonts/Optane Bold.ttf" %self.basedir,
          "trebuchet.ttf"
          ),
        "fontInstance":{}
          },

      "Potter":{
        "font_src":(
          r"%s/etc/gui/fonts/POTTERYB.ttf" %self.basedir,
          "trebuchet.ttf"
          ),
        "fontInstance":{}
          },


      "Crystallography":{
        "font_src":(
          r"%s/etc/gui/fonts/Crystallography.ttf" %self.basedir,
          "trebuchet.ttf"
          ),
        "fontInstance":{}
          },

      "Crystallography Bold":{
        "font_src":(
          r"%s/etc/gui/fonts/Crystallography.ttf" %self.basedir,
          "trebuchet.ttf"
          ),
        "fontInstance":{}
          },
        }
    #for font_name in self.fonts:
      #self.registerFontInstance(font_name, 10)
    return self.fonts

  def registerFontInstance(self, font_name, font_size, encoding='unic'):
    #font_src = r"%s\etc\gui\fonts\Vera.ttf" %self.basedir
    #f = open(font_src)
    #fontInstance = ImageFont.truetype(f, font_size, encoding=self.gui_language_encoding)

    ##IF the selected font is not in the above dictionary, we can try and get the font from the system.
    ##This doesn't work, because PIL needs the actual filename of the font, and not just the name of it.
    ##It looks like they might change this sometime soon.

    if font_name not in self.fonts:
      self.fonts.setdefault(font_name,{})
      self.fonts[font_name].setdefault("fontInstance",{})
      try:
        fontInstance = ImageFont.truetype(font_name, font_size, encoding=encoding)
      except IOError as err:
        print(err)
      failsafe = r"%s/etc/gui/fonts/Vera.ttf" %self.basedir
      fontInstance = ImageFont.truetype(failsafe, font_size, encoding=encoding)
      self.fonts[font_name]["fontInstance"].setdefault(font_size,fontInstance)

    pleasePickleMe = False
    font_src_t = self.fonts[font_name]["font_src"]
    fontInstance = self.fonts[font_name]["fontInstance"].get(font_size, None)
    if not fontInstance:
      try:
        first_choice = font_src_t[0]
        fontInstance = ImageFont.truetype(first_choice, font_size, encoding=encoding)
        self.fonts[font_name]["fontInstance"].setdefault(font_size,fontInstance)
      except:
        try:
          failsafe = font_src_t[-1]
          fontInstance = ImageFont.truetype(failsafe, font_size, encoding=encoding)
          self.fonts[font_name]["fontInstance"].setdefault(font_size,fontInstance)
        except:
          failsafe = r"%s/etc/gui/fonts/Vera.ttf" %self.basedir
          fontInstance = ImageFont.truetype(failsafe, font_size, encoding=encoding)
          self.fonts[font_name]["fontInstance"].setdefault(font_size,fontInstance)
    return fontInstance
