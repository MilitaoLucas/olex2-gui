import os
import sys
from ArgumentParser import ArgumentParser
from PIL import ImageFont

# fonts already reported as not installed (one line per font and session)
_reported_missing = set()
# bare font file name -> full path, or None when not installed (per session:
# a font installed meanwhile is found after a restart)
_found_fonts = {}

# Fonts Olex2 names but does not ship: the user installs them when needed
# (drawn labels in translated languages).  Noto: SIL Open Font License.
NOTO_HINT = "free from https://fonts.google.com/noto"
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
    native_font_name, native_font_name_bold = self.native_font_names()
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
          self.font_file(default_font_name),
          default_font_name
          ),
        "fontInstance":{}
          },
      "DefaultFont Bold":{
        "font_src":(
          self.font_file(default_font_name_bold),
          default_font_name_bold,
          ),
        "fontInstance":{}
          },
      # Olex2's own fonts (gui.params as shipped), whatever skin or theme is in
      # use: graphs drawn without the theme colours (Analysis.graph_fonts)
      "NativeFont":{
        "font_src":(
          self.font_file(native_font_name),
          native_font_name,
          ),
        "fontInstance":{}
          },
      "NativeFont Bold":{
        "font_src":(
          self.font_file(native_font_name_bold),
          native_font_name_bold,
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

      ##################################################### Noto (not shipped)
      # Fallbacks for drawn text the GUI font has no glyphs for
      # (ImageTools.deal_with_encodings_and_languages).  Not shipped: install
      # them into the user's fonts folder or the system fonts.  Any of the
      # file names will do (static, variable or the noto-cjk release).
      "Noto Sans":{  # Latin, Greek, Cyrillic
        "font_src":(
          "NotoSans-Regular.ttf",
          "NotoSans-VariableFont_wdth,wght.ttf",
          ),
        "install":"Noto Sans (Greek, Cyrillic), " + NOTO_HINT,
        "fontInstance":{}
          },
      "Noto Sans Bold":{
        "font_src":(
          "NotoSans-Bold.ttf",
          "NotoSans-Regular.ttf",
          "NotoSans-VariableFont_wdth,wght.ttf",
          ),
        "install":"Noto Sans (Greek, Cyrillic), " + NOTO_HINT,
        "fontInstance":{}
          },
      "Noto Sans Arabic":{
        "font_src":(
          "NotoSansArabic-Regular.ttf",
          "NotoSansArabic-VariableFont_wdth,wght.ttf",
          ),
        "install":"Noto Sans Arabic, " + NOTO_HINT,
        "fontInstance":{}
          },
      "Noto Sans Arabic Bold":{
        "font_src":(
          "NotoSansArabic-Bold.ttf",
          "NotoSansArabic-Regular.ttf",
          "NotoSansArabic-VariableFont_wdth,wght.ttf",
          ),
        "install":"Noto Sans Arabic, " + NOTO_HINT,
        "fontInstance":{}
          },
      "Noto Sans SC":{  # Chinese, and Japanese kana and kanji
        "font_src":(
          "NotoSansSC-Regular.ttf",
          "NotoSansSC-Regular.otf",
          "NotoSansSC-VariableFont_wght.ttf",
          "NotoSansCJKsc-Regular.otf",
          "NotoSansCJK-Regular.ttc",
          ),
        "install":"Noto Sans SC (Chinese, Japanese), " + NOTO_HINT,
        "fontInstance":{}
          },
      "Noto Sans SC Bold":{
        "font_src":(
          "NotoSansSC-Bold.ttf",
          "NotoSansSC-Bold.otf",
          "NotoSansCJKsc-Bold.otf",
          "NotoSansCJK-Bold.ttc",
          "NotoSansSC-Regular.ttf",
          "NotoSansSC-Regular.otf",
          "NotoSansSC-VariableFont_wght.ttf",
          ),
        "install":"Noto Sans SC (Chinese, Japanese), " + NOTO_HINT,
        "fontInstance":{}
          },

      ##################################################### Chinese
      "Chinese":{
        #"font_src":"arialbd.ttf",
        "font_src":(
          r"%s/etc/gui/fonts/HDZB_7.ttf" %self.basedir,
          r"msyh.ttc",
          r"MSYH.TTF",
          r"simsun.ttc",
          r"NotoSansSC-Regular.ttf",
          ),
        "fontInstance":{}
          },

      "Chinese Bold":{
        #"font_src":"arialbd.ttf",
        "font_src":(
          r"msyhbd.ttc",
          r"MSYHB.TTF",
          r"NotoSansSC-Bold.ttf",
          ),
        "fontInstance":{}
          },

      "YaHei":{
        "font_src":(
          "msyh.ttc",  # Windows 8 and later; MSYH.TTF before
          "MSYH.TTF",
          "NotoSansSC-Regular.ttf",
          ),
        "fontInstance":{}
          },

      "YaHei Bold":{
        "font_src":(
          "msyhbd.ttc",
          "MSYHB.TTF",
          "NotoSansSC-Bold.ttf",
          ),
        "fontInstance":{}
          },

      "Simsun TTC":{
        "font_src":(
          "simsun.ttc",
          "NotoSansSC-Regular.ttf",
          ),
        "fontInstance":{}
          },

      "Simhei TTF":{
        "font_src":(
          "simhei.ttf",
          "NotoSansSC-Regular.ttf",
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
    self.add_font_files()
    return self.fonts

  def native_font_names(self):
    """Regular and bold font files of gui.params as shipped (the master phil),
    not the skin's or the theme's."""
    import olx
    fallback = ("Signika-Regular.ttf", "Signika-Bold.ttf")
    if not hasattr(olx, 'gui_phil_handler'):  # no GUI phil yet (headless)
      return fallback
    gui = olx.gui_phil_handler.master_phil.extract().gui
    return (gui.default_font_name or fallback[0], gui.default_font_name_bold or fallback[1])

  def font_dirs(self):
    """Fonts the user added (theme designer, Fonts tab) first, then the shipped ones."""
    return [os.path.join(self.datadir, "fonts"),
            os.path.join(self.basedir, "etc", "gui", "fonts")]

  def font_file(self, name):
    """Full path of font file 'name' from font_dirs(), or the shipped path."""
    import os
    for d in self.font_dirs():
      p = os.path.join(d, name)
      if os.path.isfile(p):
        return p
    return r"%s/etc/gui/fonts/%s" %(self.basedir, name)

  def add_font_files(self):
    """Every .ttf/.otf in font_dirs() can be named by its file name without
    extension (e.g. a skin's font_name = Inter-Regular)."""
    import os
    for d in self.font_dirs():
      if not os.path.isdir(d):
        continue
      for fn in sorted(os.listdir(d)):
        stem, ext = os.path.splitext(fn)
        if ext.lower() in (".ttf", ".otf") and stem not in self.fonts:
          self.fonts[stem] = {"font_src": (os.path.join(d, fn), fn), "fontInstance": {}}
          # <b> in drawn text asks for "<name> Bold"
          self.fonts.setdefault("%s Bold" % stem,
                                {"font_src": (os.path.join(d, fn), fn), "fontInstance": {}})

  def font_search_dirs(self):
    """Where a font file named without a path is looked for: Olex2's font
    folders, then the system's (all users and the current user)."""
    dirs = list(self.font_dirs())
    home = os.path.expanduser("~")
    if sys.platform == "win32":
      windir = os.environ.get("WINDIR")
      if windir:
        dirs.append(os.path.join(windir, "Fonts"))
      local = os.environ.get("LOCALAPPDATA")
      if local:
        dirs.append(os.path.join(local, "Microsoft", "Windows", "Fonts"))
    elif sys.platform == "darwin":
      dirs += ["/System/Library/Fonts", "/Library/Fonts",
               os.path.join(home, "Library", "Fonts")]
    else:
      dirs += ["/usr/share/fonts", "/usr/local/share/fonts",
               os.path.join(home, ".local", "share", "fonts"),
               os.path.join(home, ".fonts")]
    return dirs

  def find_font(self, src):
    """Full path of font file 'src' (a path, or a bare file name looked for in
    font_search_dirs(), case-insensitively), or None when it is nowhere."""
    if os.path.isabs(src):
      return src if os.path.isfile(src) else None
    if src in _found_fonts:
      return _found_fonts[src]
    _found_fonts[src] = self._search_font(src)
    return _found_fonts[src]

  def _search_font(self, src):
    want = src.lower()
    for d in self.font_search_dirs():
      p = os.path.join(d, src)
      if os.path.isfile(p):
        return p
    # Linux and macOS keep fonts in sub-folders, with the case of the name
    # varying (Windows folders are flat and case-insensitive: done above)
    if sys.platform == "win32":
      return None
    for d in self.font_search_dirs():
      for root, _dirs, files in os.walk(d):
        for fn in files:
          if fn.lower() == want:
            return os.path.join(root, fn)
    return None

  def report_missing_font(self, font_name, reason=None):
    """One line (per font and session) that font 'font_name' is not
    installed, which files would do, and where to put them."""
    if font_name in _reported_missing:
      return
    _reported_missing.add(font_name)
    entry = self.fonts.get(font_name, {})
    files = entry.get("font_src", ())
    if entry.get("install"):
      what = entry["install"]
    elif files:
      what = "one of %s" % ", ".join(os.path.basename(f) for f in files)
    else:
      what = "it"
    msg = "Font '%s' is not installed. Please install %s" % (font_name, what)
    msg += " (into %s or the system fonts)." % os.path.normpath(
      os.path.join(self.datadir, "fonts"))
    if reason:
      msg += " Needed for: %s" % reason
    print(msg)

  def registerFontInstance(self, font_name, font_size, encoding='unic'):
    """PIL font for key 'font_name' (or a font file name) at font_size: the
    first of its font_src files that loads; when none does, a line says the
    font must be installed and the shipped Vera stands in."""
    entry = self.fonts.setdefault(font_name, {})
    instances = entry.setdefault("fontInstance", {})
    fontInstance = instances.get(font_size)
    if fontInstance:
      return fontInstance
    # an unknown name may itself be a font file PIL can find
    srcs = entry.get("font_src") or (font_name,)
    for src in srcs:
      try:
        fontInstance = ImageFont.truetype(self.find_font(src) or src, font_size,
                                          encoding=encoding)
        break
      except (IOError, OSError, ValueError):
        continue  # not installed or not readable: try the next one
    if fontInstance is None:
      self.report_missing_font(font_name)
      failsafe = r"%s/etc/gui/fonts/Vera.ttf" %self.basedir
      fontInstance = ImageFont.truetype(failsafe, font_size, encoding=encoding)
    instances[font_size] = fontInstance
    return fontInstance
