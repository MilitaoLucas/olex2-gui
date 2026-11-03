import os
import fnmatch
import re
import glob
from olexFunctions import OV
debug = OV.IsDebugging()
have_help = True
from htmlTools import *


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
from . import help_index


class GetHelp(VFSDependent):
  """
  The help behind the 'i' buttons. Help comes from *.help.md files
  (help_index.py), compiled into gui/help/help_index.json at release time.
  Nothing is read at startup: the index is loaded on the first lookup, plus
  help shipped by plugins / modules (PluginLib, DataDir()/modules), which is
  compiled on demand and cached in DataDir() until those files change.
  In development (debug or developer mode) a help file that changed since
  it was indexed is recompiled when one of its entries is shown.
  """

  def load_ressources(self):
    p = os.path.join(OV.BaseDir(), "util", "pyUtil", "gui", "help", "images")
    if os.path.exists(p):
      gui.helpImagesToOlexVFS(p, base="images")

  def __init__(self):
    super(GetHelp, self).__init__()
    import gui
    self.git_url = OV.GetParam('gui.help.git_url')
    language = olx.CurrentLanguage()
    self.language = "EN"
    if language == "German":
      self.language = "DE"

    olex.registerFunction(self.get_help_item, False, "gui")
    self.load_ressources()
    ws = olx.GetWindowSize('gl').split(',')
    self.box_width = int(int(ws[2]) * OV.GetParam('gui.help.width_fraction') - 40)
    self.p_path = p_path
    self.get_templates()
    self.help_root = os.path.join(OV.BaseDir(), "util", "pyUtil", "gui", "help")
    self._index = None          # {'entries': {ID: {'html', 'src'}}, 'files': {src: mtime}}
    OV.registerFunction(self.git_help, True, "githelp")
    OV.registerFunction(self.rebuild, False, "help")
    OV.registerMacro(self.make_help_box, '''name-Name of the Box&;popout-True/False&;
    type-Type of Box (help or tutorial)&;helpTxt-The help text to appear in the help box&;toolName-name of the tool where the help shall appear&;scope-plugin scope: <SCOPE>_<NAME> is looked up first&'''
                     )

  # -------------------------------------------------------------------------
  # Index
  # -------------------------------------------------------------------------

  def _developing(self):
    return debug or OV.IsDeveloping()

  def _extra_roots(self):
    """Folders whose own *.help.md are compiled on demand (plugins, modules)."""
    return [os.path.join(OV.BaseDir(), "util", "pyUtil", "PluginLib"),
            os.path.join(OV.DataDir(), "modules")]

  def _extra_cache_path(self):
    return os.path.join(OV.DataDir(), 'help_extra_index.json')

  def _load_index(self):
    """Shipped index + plugin/module help; built on the first lookup."""
    if self._index is not None:
      return self._index
    base = OV.BaseDir()
    index = help_index.read_index(os.path.join(self.p_path, help_index.INDEX_NAME))
    if index is None:
      # no (current) index shipped -- e.g. a development checkout
      index, dups = help_index.build_index(base)
      for hid, a, b in dups:
        print("Help: duplicate ID %s in %s and %s" % (hid, a, b))
    entries, files = index['entries'], index['files']

    # plugins / modules: their *.help.md, recompiled only when changed
    extra = help_index.read_index(self._extra_cache_path()) or {'entries': {}, 'files': {}}
    found = []
    for root in self._extra_roots():
      if os.path.isdir(root):
        found += help_index.find_help_files(root) + help_index.legacy_help_files(base, root)
    found_rel = {os.path.relpath(p, base).replace(os.sep, '/'): p for p in found}
    stale = [p for rel, p in found_rel.items()
             if rel not in files and extra['files'].get(rel) != os.path.getmtime(p)]
    gone = [rel for rel in extra['files'] if rel not in found_rel]
    if stale or gone:
      for rel in gone:
        extra['files'].pop(rel, None)
        for hid in [k for k, v in extra['entries'].items() if v['src'] == rel]:
          del extra['entries'][hid]
      help_index.build(stale, base, extra['entries'], extra['files'])
      extra['version'] = help_index.INDEX_VERSION
      try:
        help_index.write_index(extra, self._extra_cache_path())
      except OSError as err:
        print("Help: could not cache plugin help: %s" % err)
    for hid, e in extra['entries'].items():
      entries.setdefault(hid, e)        # core help wins over plugin help
    files.update(extra['files'])
    self._index = {'entries': entries, 'files': files}
    return self._index

  def _refresh_if_changed(self, entry):
    """Development: recompile the entry's help file if it changed."""
    files = self._index['files']
    path = os.path.join(OV.BaseDir(), entry['src'])
    try:
      mtime = os.path.getmtime(path)
    except OSError:
      return
    if files.get(entry['src']) != mtime:
      help_index.build([path], OV.BaseDir(), self._index['entries'], files)

  def lookup(self, help_id):
    """HTML for a help ID ready for display, or None."""
    index = self._load_index()
    entry = index['entries'].get(help_id)
    if entry is None:
      # rows generated at run time are numbered (ReportPlus:
      # ...ADDITIONAL_IMAGES_3): one entry without the number covers them
      m = re.match(r'^(.*)_\d+$', help_id)
      if m:
        help_id = m.group(1)
        entry = index['entries'].get(help_id)
    if entry is None:
      return None
    if self._developing():
      self._refresh_if_changed(entry)
      entry = index['entries'].get(help_id)
      if entry is None:
        return None
    return self._display_html(entry)

  def _display_html(self, entry):
    html = re.sub(r'\{\{HELPIMG\|([^|]*)\|([^|]*)\|([^}]*)\}\}', self._image_html, entry['html'])
    html = self.format_html(html)
    if self._developing():
      md_file = os.path.join(OV.BaseDir(), entry['src'])
      try:
        html = (gui.tools.TemplateProvider.get_template('edit_help') % md_file +
                gui.tools.TemplateProvider.get_template('compile_help') % md_file + html)
      except Exception as err:
        print("Help: no edit/compile links: %s" % err)
    return html

  def _image_html(self, m):
    rel, frac, alt = m.group(1), m.group(2), m.group(3)
    img_src = os.path.join(OV.BaseDir(), rel)
    if not os.path.exists(img_src):
      img_src = os.path.join(self.help_root, 'images', os.path.basename(rel))
      if not os.path.exists(img_src):
        img_src = os.path.join(self.help_root, 'images', '404.png')
    try:
      width = int(int(self.box_width) * float(frac))
    except ValueError:
      width = int(self.box_width)
    d = {'full_match': m.group(0), 'src': rel, 'alt': alt, 'width': width, 'img_src': img_src}
    return gui.tools.TemplateProvider.get_template('help_image_html') % d

  def rebuild(self, write=True):
    """
    spy.help.rebuild() -- recompile all help (development; also picks up
    new *.help.md files) and, if possible, write help_index.json.
    """
    index, dups = help_index.build_index(OV.BaseDir())
    for hid, a, b in dups:
      print("Help: duplicate ID %s in %s and %s" % (hid, a, b))
    if write in (True, 'True', 'true'):
      try:
        help_index.write_index(index, os.path.join(self.p_path, help_index.INDEX_NAME))
      except OSError as err:
        print("Help: could not write the help index: %s" % err)
    self._index = None
    try:
      os.remove(self._extra_cache_path())
    except FileNotFoundError:
      pass
    self._load_index()
    print("Help: %i entries" % len(self._index['entries']))

  def git_help(self, quick=True, specific=False, force=False):
    """
    Compatibility (ACED, the 'Recompile' link): specific = a help file ->
    recompile it; specific = a folder -> add all its .md files as help.
    """
    index = self._load_index()
    if not specific:
      self.rebuild()
      return
    if os.path.isfile(specific):
      paths = [specific]
    else:
      paths = help_index.find_help_files(specific, all_md=True)
    help_index.build(paths, OV.BaseDir(), index['entries'], index['files'])

  # -------------------------------------------------------------------------

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
    help_id = help_id.replace(" ", "_").upper()
    html = self.lookup(help_id)
    return html if html is not None else olx.GetVar(help_id, "No Help Here!")

  def make_call(self, url):
    import HttpTools
    try:
      res = HttpTools.make_url_call(url, values='', http_timeout=5)
    except Exception as err:
      return None
    return res

  def get_templates(self):
    gui.tools.TemplateProvider.get_all_templates(path=self.p_path, mask="*.html")

  @staticmethod
  def _code_button(m):
    """
    <code>cmd</code> -> a button that runs cmd, as wide as its text. The
    link snippet defaults to width=100%: without a width the buttons were
    full width in running text and collapsed to zero width in some cells.
    """
    cmd = m.group(1).replace('"', "'")
    width = 7 * len(cmd) + 16
    return ('$+ html.Snippet(GetVar(default_link),"value=%s","hint=%s","onclick=%s",'
            '"width=%i","fit=false","flat=True","fgcolor=#ffffff",'
            '"bgcolor=GetVar(gui.action_colour)")$-' % (cmd, cmd, cmd, width))

  def format_html(self, txt):
    while "\n" in txt:
      txt = txt.replace("\n", "")
    regex_source = os.path.join(self.p_path, "regex_format_help.txt")
    if os.path.exists(regex_source):
      txt = gui.tools.run_regular_expressions(txt, regex_source, base=self.p_path)
    # inline code = a runnable command (help convention); done here, after
    # the regex rules (one of which also produces <code>), rather than in
    # regex_format_help.txt, so the button gets a width fitting its text
    txt = re.sub(r'<code>(.*?)</code>', self._code_button, txt)
    txt = txt.replace("help_root", self.help_root)
    gui_link = os.path.join(p_path, 'gui-link')
    txt = txt.replace("GetVar(gui_link)", gui_link)
    return txt

  def make_help_box(self, d={}, name={}, helpTxt=None, popout=False, box_type='help', toolName=None, scope=None):
    OV.SetVar('last_help_box', name)
    name = getGenericSwitchName(name).replace("h3-", "")
    _ = ""
    md_box = True
    help_id = name.upper().replace("-", "_").replace(" ", "_")
    # a plugin's tool names are often generic (ReportPlus: Settings,
    # Collections): its scope picks e.g. REPORTPLUS_SETTINGS first. An unset
    # scope arrives as the unsubstituted placeholder '#scope'.
    if scope and not str(scope).startswith('#'):
      _ = self.lookup("%s_%s" % (str(scope).upper(), help_id))
    if not _ and helpTxt == '#helpTxt':
      _ = self.lookup(help_id)

    if not _:
      if helpTxt and os.path.exists(helpTxt):
        _ = open(helpTxt, 'r').read()

      elif helpTxt:
        _ = olx.GetVar(helpTxt, helpTxt)

      elif not helpTxt or helpTxt == "#helpTxt":
        _ = self.lookup(help_id) or olx.GetVar(help_id, None)

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

        if OV.IsPopup(pop_name):
          olx.Popup(pop_name, wFilePath)
        else:
          olx.Popup(pop_name, wFilePath, b="tcr", t=title, w=boxWidth, h=boxHeight, x=x, y=y)
          OV.SetPopBorder(pop_name, 5)
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
      #OV.ShowModal(self.pop_name)
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

if have_help:
  AutoDemoTemp()

