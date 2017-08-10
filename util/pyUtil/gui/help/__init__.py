import markdown2
print "markdown2 imported!"
import os
import fnmatch
import re


from olexFunctions import OlexFunctions
OV = OlexFunctions()
debug = bool(OV.GetParam("olex2.debug", False))


import olex
import olx
import gui
import cPickle as pickle


try:
  from ImageTools import IT
except:
  from ImageTools import ImageTools
  IT = ImageTools()


class GetHelp(object):
  def __init__(self):
    self.git_url = OV.GetParam('gui.help.git_url')
    language = olx.CurrentLanguage()
    self.language = "EN"
    if language == "German":
      self.language = "DE"

    self.source_dir = OV.GetParam('gui.help.src', os.sep.join([OV.BaseDir(), 'etc', 'help', 'gui', language]))

    olex.registerFunction(self.get_help, False, "gui")
    ws = olx.GetWindowSize('gl')
    ws = ws.split(',')
    self.box_width = int(int(ws[2])*OV.GetParam('gui.help.width_fraction') - 40)
    self.help = {}
    self.help_pickle_file = os.sep.join([OV.DataDir(),'help.pickle'])

  def format_html(self, txt):
    while "\n" in txt:
      txt = txt.replace("\n", "")
    regex_source = os.sep.join([self.source_dir, "regex_format_help.txt"])
    if os.path.exists(regex_source):
      txt = gui.tools.run_regular_expressions(txt, regex_source)
    return txt

  def get_help(self, quick=True):
    if "false" in repr(quick).lower():
      quick = False
    if quick:
      try:
        if os.path.exists(self.help_pickle_file):
          self.help = pickle.load(open(self.help_pickle_file,'r'))
          for item in self.help:
            OV.SetVar(item, self.help[item])
        return
      except:
        "Something went wrong with pickling the help file"

    matches = []
    for root, dirnames, filenames in os.walk(self.source_dir):
      for filename in fnmatch.filter(filenames, '*.md'):
        matches.append((root.replace(self.source_dir, 'help').replace("\\", "_") + "_" + filename.replace('.md', ""),os.path.join(root, filename)))

    if debug:
      print "Building help icon text"
      print "======================="

    for var,md_path in matches:
      if debug:
        print md_path
      fc = (open(md_path,'r').read())
      fc = fc.replace("####", "@@@@")
      fc = fc.replace("###", "@@@")
      fc = fc.replace("##", "@@")

      l = fc.split("#")

      help_type = ""
      target_marker = "-target\n"
      help_marker = "-help\n"
      info_marker = "-info\n"
      for item in l:
        if not item:
          continue
        item = item.strip()
        try:
          var = item.split("\n")[0].lstrip("#").replace(" ", "_").upper()
          val = "\n".join(item.split("\n")[1:])
        except:
          var = md_path
          val = item
        if target_marker in item:
          help_type = 'target'
          help = item.split(target_marker)[1].strip()

        else:
          help_type = 'help'
          val = val.replace("@@@@", "####").replace("@@@", "###").replace("@@", "##").replace("|", "||")
          html = markdown2.markdown(val, extras=["wiki-tables"])
          if "img" in html:
            src = os.sep.join(md_path.split("\\")[:-1])
            html = html.replace(r'<img src="', r'<zimg width="%s" src="%s%s'%(self.box_width, src , os.sep))
          html = html.replace("\$", "$").replace("$", "\$").replace("\$spy", "$spy")
          help = self.format_html(html)

        help = help.strip().replace("<p>","").replace("</p>","")
        help = help.replace("<zimg", "<p><zimg")
        help = help.replace("<table><tbody><tr><td>", "<table width='100%%'><tbody><tr><td width='25%%'>")
        OV.SetVar(var, help)
        self.help[var] = help
        if debug:
          print "  - %s" %var
    pickle.dump(self.help, open(self.help_pickle_file, 'wb'))

gh = GetHelp()

