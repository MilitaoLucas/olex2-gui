import os
import fnmatch
import re
import glob
from olexFunctions import OV
debug = OV.IsDebugging()
have_help = True
from htmlTools import *

import pickle as pickle

import olex
import olx
import gui
import olex_core

p_path = os.path.dirname(os.path.abspath(__file__))
OV.SetVar('help_path', p_path)

try:
  from . import markdown2
  if debug:
    print("markdown2 imported!")
except Exception as err:
  print(err)
  with open(os.path.join(p_path, 'markdown2.pyo'), 'r') as f:
    markdown2 = imp.load_compiled('markdown2', os.path.join(p_path, 'markdown2.pyo'))
  print("markdown2 imported through imp.")

from PluginTools import VFSDependent


class GetHelp(VFSDependent):

  def load_ressources(self):
    p = os.path.join(OV.BaseDir(), "util", "pyUtil", "gui", "help", "images")
    if os.path.exists(p):
      gui.helpImagesToOlexVFS(p, base="images")
    else:
      p = os.path.join(OV.BaseDir(), "util", "pyUtil", "gui", "help", "help.zip")
      if os.path.exists(p):
        gui.zipToOlexVFS(p)


  def __init__(self):
    super(GetHelp, self).__init__()
    import gui
    self.git_url = OV.GetParam('gui.help.git_url')
    language = olx.CurrentLanguage()
    self.language = "EN"
    if language == "German":
      self.language = "DE"

    olex.registerFunction(self.get_help, False, "gui")
    olex.registerFunction(self.get_help_item, False, "gui")
    self.load_ressources()
    ws = olx.GetWindowSize('gl').split(',')
    self.box_width = int(int(ws[2]) * OV.GetParam('gui.help.width_fraction') - 40)
    self.p_path = p_path
    self.get_templates()
    self.all_help_d = {}
    self.all_help_d_file = os.path.join(OV.DataDir(), 'all_help_d.pickle')
    self.help_root = os.path.join(OV.BaseDir(), "util", "pyUtil", "gui", "help")
    OV.registerFunction(self.git_help, True, "githelp")
    OV.registerMacro(self.make_help_box, '''name-Name of the Box&;popout-True/False&;
    type-Type of Box (help or tutorial)&;helpTxt-The help text to appear in the help box&;toolName-name of the tool where the help shall appear&'''
                     )

  def convert_md_to_html_pandoc(self, md_input):
    import subprocess
    """Convert Markdown content to HTML using Pandoc."""
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0  # Windows fix
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html"],
          input=md_input,
          text=True,
          capture_output=True,
          creationflags=creation_flags  # Prevents black box on Windows
      )
    return result.stdout

  def convert_md_to_html(self, md_input):
    """Convert Markdown content to HTML using markdown2 (no external process)."""
    return gh.format_html(markdown2.markdown(md_input, extras=["fenced-code-blocks"]))

  def get_help_item(self, help_id):
    help_id = help_id.replace(" ", "_")
    help_id = help_id.upper()
    return olx.GetVar(help_id, "No Help Here!")

  def make_call(self, url):
    import HttpTools
    try:
      res = HttpTools.make_url_call(url, values='', http_timeout=5)
    except Exception as err:
      return None
    return res

  def get_latest_help_file(self, which):
    url = OV.GetParam('olex2.samples.url') + r"/%s" % which + ".htm"
    _ = self.make_call(url)
    if _ is None:
      return ""
    cont = _.read()
    return cont

  def get_templates(self):
    gui.tools.TemplateProvider.get_all_templates(path=self.p_path, mask="*.html")

  def get_help(self, quick=True):

    if self.all_help_d:
      self.get_help_from_text_file()
      with open(self.all_help_d_file, 'wb') as pickle_file:
        pickle.dump(self.all_help_d, pickle_file)

  def get_help_from_text_file(self):
    language = 'EN'
    help_file_n = 'HELP_%s.htm' % language
    builtin_help_location = os.path.join(OV.BaseDir(), 'util', 'pyUtil', 'gui', 'help', 'gui')
    base = os.path.join(OV.BaseDir(), "util", "pyUtil", "gui", "help")
    rFile = self.get_latest_help_file('HELP_%s' % language)
    self.all_help = os.path.join(OV.DataDir(), help_file_n)

    if rFile:
      with open(self.all_help, 'wb') as wFile:
        wFile.write(rFile)
    else:
      if not os.path.exists(self.all_help):
        self.all_help = os.path.join(builtin_help_location, help_file_n)
      rFile = gui.file_open(path=self.all_help, base=base)
      if not rFile:
        return

    help_l = rFile.split("<h1>")
    for help in help_l:
      help = help.strip()
      if not help:
        continue
      if "</h1>" not in help:
        continue
      var = help.split("</h1>")[0].strip()
      help = help.split("</h1>")[1].strip()
#      olex_core.SetVar(var, help)
      self.all_help_d[var] = help
      if debug:
        print("  - %s" % var)

  def format_html(self, txt):
    while "\n" in txt:
      txt = txt.replace("\n", "")
    regex_source = os.path.join(self.p_path, "regex_format_help.txt")
    if os.path.exists(regex_source):
      txt = gui.tools.run_regular_expressions(txt, regex_source, base=self.p_path)
    txt = txt.replace("help_root", self.help_root)
    gui_link = os.path.join(p_path, 'gui-link')
    txt = txt.replace("GetVar(gui_link)", gui_link)
    return txt

  def _initialise_all_help_d(self):
    if olexex.check_for_recent_update():
      if os.path.exists(self.all_help_d_file):
        os.remove(self.all_help_d_file)
    if not self.all_help_d:
      if os.path.exists(self.all_help_d_file):
        with open(self.all_help_d_file, 'rb') as rFile:
          self.all_help_d = pickle.load(rFile)
      else:
        self.all_help_d.setdefault("paths", [])
        #self.get_help()
        _ = os.path.join(OV.BaseDir(), "util", "pyUtil")
        self.git_help(specific=_, force=True)
        _ = os.path.join(OV.DataDir(), "modules")
        self.git_help(specific=_, force=True)

  def git_help(self, quick=True, specific=False, force=False):
    if specific:
      self.source_dir = os.path.dirname(specific)
      self.all_help = ""
    else:
      builtin_help_location = os.path.join(OV.BaseDir(), 'util', 'pyUtil', 'gui', 'help')
      self.all_help = os.path.join(builtin_help_location, 'gui', 'HELP_EN.htm')
      if not hasattr(self, 'source_dir'):
        self.source_dir = specific

      try:
        copy_files = ("githelp_templates.html", "tutorials_templates.html")
        for cp_file in copy_files:
          copy_from = os.path.join(self.p_path, cp_file)
          copy_to = os.path.join(builtin_help_location, cp_file)
          copyfile(copy_from, copy_to)
      except:
        print("Can not copy files; most probably Olex2 was not started in Admin Mode")

      if "false" in repr(quick).lower():
        quick = False
      if quick:
        try:
          if os.path.exists(self.help_pickle_file):
            self.help = pickle.load(open(self.help_pickle_file, 'r'))
            for item in self.help:
              OV.SetVar(item, self.help[item])
          return
        except:
          "Something went wrong with pickling the help file"

      if os.path.exists(self.all_help):
        print("Deleting builtin help at %s" % self.all_help)
        try:
          os.remove(self.all_help)
        except Exception as err:
          print("Can not remove self.all_help: %s" % err)

    matches = get_md_files_by_folder(self.source_dir)

    if debug:
      print("==================")
      print("Building help text")
      print("==================")

    for fPath in matches:
      if not matches[fPath]:
        continue
      _ = fPath
      if fPath == ".":
        _ = ""
      srcDir = os.path.join(self.source_dir, _)
      if srcDir not in self.all_help_d['paths']:
        force = True
      help_done_marker_file = os.path.join(srcDir, "help_done.txt")

      if debug:
        print(f"Help for: {srcDir}")
      if os.path.exists(help_done_marker_file):
        os.remove(help_done_marker_file)
      for fFile in matches[fPath]:
        md_file = os.path.join(srcDir, fFile)
        with open(md_file, encoding="utf8", errors='ignore') as f:
          fc = f.read()

        self.parse_help(fc, srcDir, md_file)

      self.all_help_d['paths'].append(srcDir)
      #try:
        #wFile = open(help_done_marker_file, 'w')
        #wFile.close()
      #except:
        #t = f'''
        #==========================================================================
        #The help system tried to write a file, but this file could not be written:\n
        #{os.path.exists(help_done_marker_file)}\n
        #Please restart Olex2 in Admin mode.
        #==========================================================================
        #'''
        #print(t)

    with open(self.all_help_d_file, 'wb') as pickle_file:
      pickle.dump(self.all_help_d, pickle_file)

  def parse_help(self, fc, fDir, md_file):
    fc = fc.replace("####", "@@@@")
    fc = fc.replace("###", "@@@")
    fc = fc.replace("##", "@@")
    l = fc.split("\n#")
    self.help_type = ""
    target_marker = "-target\n"
    help_marker = "-help\n"
    info_marker = "-info\n"
    for item in l:
      if not item:
        continue
      item = item.strip()
      try:
        var = item.split("\n")[0].lstrip("#").strip().replace(" ", "_").upper()
        val = "\n".join(item.split("\n")[1:])
      except:
        var = md_path
        val = item
      if target_marker in item:
        self.help_type = 'target'
        help = item.split(target_marker)[1].strip()

      else:
        self.help_type = 'help'
        val = val.replace("@@@@", "####").replace("@@@", "###").replace("@@", "##").replace("|", "||")
        html = markdown2.markdown(val, extras=["wiki-tables", "fenced-code-blocks"])
        if "img" in html:
          regex = r'(<img[^>]*\bsrc="([^"]+)"[^>]*\balt="([^"]+)"[^>]*>)'
          matches = re.findall(regex, html)
          results = []
          for full_match, src, alt in matches:
            width = 1
            if " " in alt:
              try:
                width = float(alt.split(" ")[0])
                alt = " ".join(alt.split(" ")[1:])
              except:
                pass
            results.append({
              'full_match': full_match,
              'src': src,
              'alt': alt,
              'width': width,
            })
          for result in results:
            img_src = os.path.join(fDir, result['src'])
            if not os.path.exists(img_src):
              img_src = os.path.join(self.help_root, 'images', result['src'])
              if not os.path.exists(img_src):
                img_src = os.path.join(self.help_root, 'images', '404.png')

            result.setdefault('img_src', img_src)
            width = int(int(self.box_width) * width)
            result['width'] = width
            help_image_html = gui.tools.TemplateProvider.get_template('help_image_html') % result
            html = html.replace(f"{result['full_match']}", help_image_html)

        html = html.replace("\$", "$").replace("$", "\$").replace("\$spy", "$spy")
        help = gh.format_html(html)

      help = help.strip().replace("<p>", "").replace("</p>", "")
      help = help.replace("<zimg", "<zimg")
      help = help.replace("<table><tbody><tr><td>", "<table width='100%%'><tbody><tr><td width='25%%'>")

      if self.all_help:
        try:
          wFile = open(self.all_help, 'ab')
          var_dis = "\n\n<h1>" + var + "</h1>\n"
          wFile.write(var_dis)
          wFile.write(help)
          wFile.close()
        except Exception as err:
          print("-->> " + var + "--" + repr(err))
          try:
            wFile.write(repr(help))
            wFile.close()
          except:
            pass

      if debug and self.help_type == 'help':
        p = p_path
        gui.tools.TemplateProvider.get_template(template_file='githelp_templates.html', base=p, path=p, mask="*.html")
        edit_help = gui.tools.TemplateProvider.get_template(name='edit_help', path=p) % md_file
        compile_help = gui.tools.TemplateProvider.get_template('compile_help') % md_file
        help = edit_help + compile_help + help

      OV.SetVar(var, help)
      self.all_help_d[var] = help

      if debug:
        print("  - %s" % var)
        #_ = OV.GetVar('last_help_box')
        #if _:
          #import gui
          #gui.help.make_help_box(name=_)
          #OV.SetVar('last_help_box', "")

  def make_help_box(self, d={}, name={}, helpTxt=None, popout=False, box_type='help', toolName=None):
    OV.SetVar('last_help_box', name)
    name = getGenericSwitchName(name).replace("h3-", "")
    _ = ""
    md_box = True
    if helpTxt == '#helpTxt':
      id = name.upper().replace("-", "_")
      try:
        _ = self.all_help_d.get(name.upper().replace("-", "_"))
        if _:
          md_box = True
      except:
        pass

    if not _:
      if helpTxt and os.path.exists(helpTxt):
        _ = open(helpTxt, 'r').read()

      elif helpTxt:
        _ = olx.GetVar(helpTxt, helpTxt)

      elif not helpTxt or helpTxt == "#helpTxt":
        _ = olx.GetVar(name, None)
        _ = olx.GetVar(name.upper().replace("-", "_"), None)

    helpTxt = _

    if popout == 'false':
      popout = False
    else:
      popout = True

    if not name:
      return
    if "-h3-" in name:
      t = name.split("-h3-")
      help_src = t[1]
      title = help_src.replace("-", " ")

    if "h3-" in name:
      t = name.split("h3-")
      help_src = name
      title = t[1].replace("-", " ")

    elif "-" in name:
      title = name.replace("-", " ")
      help_src = name
    else:
      title = name
      help_src = name
  #  titleTxt = OV.TranslatePhrase("%s" %title.title())
    titleTxt = title
    if box_type == "tutorial":
      titleTxt = titleTxt
      t = titleTxt.split("_")
      if len(t) > 1:
        titleTxt = "%s: %s" % (t[0], t[1])

    title = title.title()
    if not helpTxt or helpTxt == "None":
      helpTxt = OV.TranslatePhrase("%s-%s" % (help_src, box_type))
    helpTxt = helpTxt.replace("\r", "")
    helpTxt, d = format_help(helpTxt)
    d.setdefault('next', name)
    d.setdefault('previous', name)

    editLink = make_edit_link(name, box_type)

    if box_type != "help":
      banner_include = "<zimg border='0' src='banner_%s.png' usemap='map_tutorial'>" % box_type
      banner_include += """

  <map name="map_tutorial">
  <!-- Button PREVIOUS -->
      <area shape="rect" usemap="#map_setup"
        coords="290,0,340,60"
        href='spy.make_help_box -name=%(previous)s -type=tutorial' target='%%previous%%: %(previous)s'>

  <!-- Button NEXT-->
      <area shape="rect"
        coords="340,0,400,60"
        href='spy.make_help_box -name=%(next)s -type=tutorial' target='%%next%%: %(next)s'>
  </map>
      """ % d

    else:
      banner_include = ""
    if not popout:
      return_items = r'''
    <a href="spy.make_help_box -name='%s' -popout=True>>htmlhome">
      <zimg border='0' src='popout.png'>
    </a>
    <a href=htmlhome><zimg border='0' src='return.png'>
    </a>
  ''' % name

    else:
      return_items = ""

    if md_box:
      from ImageTools import ImageTools
      IT = ImageTools()
      d = {'title': titleTxt.replace("_", " "),
           'body': helpTxt,
           'font_size_base': OV.GetParam('gui.help.base_font_size', '3'),
           'font_colour': OV.GetParam('gui.help.font_colour').hexadecimal,
           'bg_colour': OV.GetParam('gui.help.bg_colour').hexadecimal,
           'h1_colour': OV.GetParam('gui.help.h1_colour').hexadecimal,
           'h2_colour': OV.GetParam('gui.help.h2_colour').hexadecimal,
           'h3_colour': OV.GetParam('gui.help.h3_colour').hexadecimal,
           'highlight_colour': OV.GetParam('gui.help.highlight_colour').hexadecimal,
           }
      template = OV.GetParam('gui.help.pop_template', 'md_box').rstrip(".html").rstrip(".htm")
      p = OV.GetParam('gui.help.src', os.path.join(OV.BaseDir(), 'etc', 'help', 'gui'))
      txt = get_template(template) % d

    else:
      txt = get_template('pop_help', base_path=p)
      txt = txt % (banner_include, name, titleTxt, helpTxt, return_items, editLink)

    wFilePath = r"%s-%s.htm" % (name, box_type)
    wFilePath = wFilePath.replace(" ", "_")
    #from ImageTools import ImageTools
    #IT = ImageTools()
    #txt = IT.get_unicode_characters(txt)
    OV.write_to_olex(wFilePath, txt)

    if box_type == 'help':
      if md_box:
        ws = olx.GetWindowSize('gl').split(',')
        boxWidth = int(int(ws[2]) * OV.GetParam('gui.help.width_fraction', 0.3))
        if boxWidth < 500:
          boxWidth = 500
        boxHeight = int(ws[3]) - 30
        ws = olx.GetWindowSize().split(',')
        x = int(ws[0]) + int(ws[2]) // 2 - boxWidth - 2
        y = int(ws[1]) + 50

      else:
        boxWidth = OV.GetParam('gui.help_box.width')
        length = len(helpTxt)
        tr = helpTxt.count('<br>')

        boxHeight = int(length / (boxWidth / OV.GetParam('gui.help_box.height_factor'))) + int(OV.GetParam('gui.help_box.height_constant') * (tr + 2))
        if boxHeight > OV.GetParam('gui.help_box.height_max'):
          boxHeight = OV.GetParam('gui.help_box.height_max')
        if boxHeight < 150:
          boxHeight = 150

        x = 10
        y = 50
        mouse = True
        if mouse:
          mouseX = int(olx.GetMouseX())
          mouseY = int(olx.GetMouseY())
          y = mouseY
          if mouseX > 300:
            x = mouseX + 10 - boxWidth
          else:
            x = mouseX - 10
    else:
      if box_type == 'tutorial' and tutorial_box_initialised:
        pass
      else:
        ws = olx.GetWindowSize().split(',')
        x = int(ws[0])
        y = int(ws[1]) + 50
        ws = olx.GetWindowSize('gl').split(',')
        boxWidth = int(400)
        boxHeight = int(ws[3]) - 90

    if popout:
      if box_type == 'tutorial':
        pop_name = "Tutorial"
        name = "Tutorial"
      else:
        pop_name = "%s-%s" % (name, box_type)
      if box_type == 'tutorial' and tutorial_box_initialised:
        olx.Popup(tutorial_box_initialised, wFilePath)
      else:
        if md_box:
          pop_name = "md_box"
        pop_name = pop_name.replace(" ", "_")
        title = 'Olex2 Help'
        webview = False
        if webview:
          t = '''
          <input type=webview value='%s' width='%s' height='%s'>
          ''' % (wFilePath, boxWidth, boxHeight)
          webView = r"md_web.htm"
          OV.write_to_olex(webView, t)
          wFilePath = webView

        if "true" in olx.html.IsPopup(pop_name).lower():
          olx.Popup(pop_name, wFilePath)
        else:
          olx.Popup(pop_name, wFilePath, b="tcr", t=title, w=boxWidth, h=boxHeight, x=x, y=y)
          olx.html.SetBorders(pop_name, 5)
        if box_type == 'tutorial':
          tutorial_box_initialised = pop_name

    else:
      olx.html.Load(wFilePath)
  #  popup '%1-tbxh' 'basedir()/etc/gui/help/%1.htm' -b=tc -t='%1' -w=%3 -h=%2 -x=%4 -y=%5">


def get_template(name, base_path=None):
  return gui.tools.TemplateProvider.get_template(name)

from .Tutorials import AutoDemo

class AutoDemoTemp(AutoDemo):
  def __init__(self, name='default_auto_tutorial', reading_speed=2):
    super(AutoDemoTemp, self).__init__(name='default_auto_tutorial', reading_speed=2)
    self.source_base = p_path
    self.source_dir = os.path.join(self.source_base, 'tutorials', 'EN')
    self.p_path = gh.p_path
    gui.tools.TemplateProvider.get_all_templates(path=self.p_path, mask="*.html")
    self.make_tutorial_gui_html()

  def make_tutorial_gui_html(self):
    mask = "*.txt"
    g = glob.glob("%s%s%s" % (self.source_dir, os.sep, mask))
    t = ""
    for item in g:
      if debug:
        pass
        #print(item + "..")
      item_name = os.path.basename(item).split(".txt")[0]

      href = "spy.demo.run_autodemo(item_name)"
      value = item_name
      t += '''
      $+
      html.Snippet(GetVar(default_link),
      "value=%s",
      "onclick=%s",
      )$-''' % (value, href)
    olx.SetVar('tutorial_html', t)

  def make_tutbox_popup(self):
    have_image = self.make_tutbox_image()

    self.format_txt()

    self.pop_title = self.current_tutorial_file.split(os.sep)[-1:][0].split(".")[0].replace("_", " ").title()
    if debug:
      edit = '<a href="shell %s">Edit</a>' % self.current_tutorial_file
    else:
      edit = ""

#    self.txt = markdown2.markdown(self.txt, extras=["wiki-tables"])
    self.txt = gh.format_html(self.txt)

    d = {}
    d.setdefault('pop_name', self.pop_name)
    d.setdefault('bg_colour', self.bg_colour)
    d['bg_colour'] = self.bg_colour
    d['button_bar_colour'] = self.button_bar_colour
    d.setdefault('font_colour', self.font_colour)
    d.setdefault('txt', self.txt)
    d.setdefault('src', self.current_tutorial_file)
    d.setdefault('title', self.pop_title)
    d.setdefault('edit', self.pop_name)
    d.setdefault('edit_link', gui.tools.TemplateProvider.get_template('edit_link') % d)

    if OV.IsControl('%s' % self.pop_name):
      pass
      #olx.html.ShowModal(self.pop_name)
    else:
      if self.interactive:
        txt = gui.tools.TemplateProvider.get_template('pop_tutorials') % d
      else:
        txt = gui.tools.TemplateProvider.get_template('pop_tutorials_loop') % d

      OV.write_to_olex("%s.htm" % self.pop_name.lower(), txt)
      if self.interactive:
        boxWidth = 450
        boxHeight = 320
      else:
        boxWidth = 450
        boxHeight = 250
      ws = olx.GetWindowSize().split(',')
      #x = int(ws[2])/2 - boxWidth/2
      #y = int(ws[3])/2 - boxHeight/2
      x = 50
      y = 50
      if self.have_box_already:
        olx.Popup(self.pop_name, '%s.htm' % self.pop_name.lower(), t=self.pop_name)
      else:
        if self.interactive:
          olx.Popup(self.pop_name, '%s.htm' % self.pop_name.lower(),
                    b='t', t=self.pop_name, w=boxWidth, h=boxHeight, x=x, y=y)
          olx.html.SetFocus(self.pop_name + '.TUTORIAL_NEXT')
        else:
          olx.Popup(self.pop_name, '%s.htm' % self.pop_name.lower(), **{'b': 't', 't': self.pop_name, 'w': boxWidth, 'h': boxHeight, 'x': x, 'y': y})
        self.have_box_already = True
      OV.Refresh()
      if not self.interactive:
        sleep = len(self.cmd_content) * self.reading_speed
        olx.Wait(sleep)
      return

  def run_autodemo(self, name, other_popup_name=""):
    try:
      self.user_structure = OV.FileFull()
      self.set_box_bg_colour()
      self.items = []
      self.item_counter = 0
      if other_popup_name and olx.IsPopup(other_popup_name):
        olx.html.Hide(other_popup_name)

      if name:
        self.name = name

      self.read_tutorial_definitions()
      olx.Clear()
      self.get_demo_item()
      cmd_type = self.run_demo_item()
    except Exception as err:
      print("+++ ERROR IN TUTORIALS: %s" % err)
      sys.stderr.formatExceptionInfo()
      self.end_tutorial()

  def read_tutorial_definitions(self, specific=None):
    if specific:
      self.source_dir = specific
    else:
      specific = OV.GetVar('githelp_tutorial_src', None)
      if specific:
        self.source_dir = specific

    ## First read in the commands that preceeds all tutorials
    self.items = gui.tools.TemplateProvider.get_template('all_tutorials_preamble').split("\n")

    ## Then read in the actual tutorial
    _ = os.path.join(self.source_dir, self.name + ".txt")
    self.current_tutorial_file = _
    if debug:
      print("opening %s" % self.current_tutorial_file)
    rFile = gui.file_open(_, mode='r', base=p_path)
    l = rFile.split("\n")
    self.items = self.items + l
    self.items = self.items + gui.tools.TemplateProvider.get_template('all_tutorials_end').split("\n")


def pandoc(kind='pdf', md_path=None, out_path=None):
  ac_path = "D:\\Users\\Horst\\Documents\\Olex2-1.5-dev\\util\\pyUtil\\AC5d\\"
  out_tex = os.path.join(ac_path, 'fred.tex')
  out_pdf = os.path.join(ac_path, 'fred.pdf')
  md = os.path.join(ac_path, 'AC5_classes.md')
  if kind == "tex":
    os.system('pandoc -o %s -f markdown -t latex %s' % (out_tex, md))

  else:
    os.system('pandoc %s -o %s' % (md, out_pdf))

OV.registerFunction(pandoc, False, 'help')


def get_md_files_by_folder(root_folder):
  md_files_dict = {}

  # Walk through the directory tree
  for folder_path, _, files in os.walk(root_folder):
    if ".git" in folder_path:
      continue
    # Filter for .md files in the current folder
    md_files = [file for file in files if file.endswith('.md')]

    # Use the relative path of the folder as the key
    relative_path = os.path.relpath(folder_path, root_folder)
    md_files_dict[relative_path] = md_files

  return md_files_dict

gh = GetHelp()
gh._initialise_all_help_d()

if have_help:
  AutoDemoTemp()

