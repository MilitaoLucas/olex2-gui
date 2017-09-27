import os
import fnmatch
import re

from olexFunctions import OlexFunctions
OV = OlexFunctions()
debug = bool(OV.GetParam("olex2.debug", False))

import olex
import olx
import gui

p_path = os.path.dirname(os.path.abspath(__file__))
OV.SetVar('help_path', p_path)

class GetHelp(object):
  def __init__(self):
    self.git_url = OV.GetParam('gui.help.git_url')
    language = olx.CurrentLanguage()
    self.language = "EN"
    if language == "German":
      self.language = "DE"

    olex.registerFunction(self.get_help, False, "gui")
    ws = olx.GetWindowSize('gl')
    ws = ws.split(',')
    self.box_width = int(int(ws[2])*OV.GetParam('gui.help.width_fraction') - 40)
    self.p_path = p_path
    self.get_templates()
    try:
      self.get_help()
    except:
      pass

  def format_html(self, txt):
    while "\n" in txt:
      txt = txt.replace("\n", "")
    #regex_source = os.sep.join([self.source_dir, "regex_format_help.txt"])
    regex_source = os.sep.join([self.p_path, "regex_format_help.txt"])
    if os.path.exists(regex_source):
      txt = gui.tools.run_regular_expressions(txt, regex_source)
    #gui_link = os.sep.join([p_path, 'gui-link'])
    txt = txt.replace("GetVar(gui_link)","GetVar(gui.skin.link_type")
    return txt

  def get_templates(self):
    gui.tools.TemplateProvider.get_all_templates(path=self.p_path, mask="*.html")

  def get_help(self, quick=True):
    builtin_help_location = os.sep.join([OV.BaseDir(), 'util', 'pyUtil', 'gui', 'help', 'gui'])
    all_help = os.sep.join([builtin_help_location, 'HELP_EN.htm'])
    if os.path.exists(all_help):
      rFile = open(all_help, 'rb').read()
    else:
      print "No help file installed"
      return
#    OV.SetVar('All-Inline-Help', rFile)
    help_l = rFile.split("<h1>")
    for help in help_l:
      help = help.strip()
      if not help:
        continue
      if "</h1>" not in help:
        continue
      var = help.split("</h1>")[0].strip()
      help = help.split("</h1>")[1].strip()
      OV.SetVar(var, help)
      print "  - %s" %var

gh = GetHelp()

from htmlTools import *
def make_help_box(args):
  global tutorial_box_initialised
  d = {}
  name = args.get('name', None)
  d = args.get('d', {})
  name = getGenericSwitchName(name).lstrip("h3-")
  helpTxt = args.get('helpTxt', None)

  _= ""
  md_box = True
  if helpTxt == '#helpTxt':
    try:
      _ = OV.GetVar(name.upper().replace("-", "_"))
      if _:
        md_box = True
    except:
      pass

  if not _:
    if helpTxt and os.path.exists(helpTxt):
      _ = open(helpTxt, 'r').read()

    elif helpTxt:
      _ = olx.GetVar(helpTxt,None)

    elif not helpTxt or helpTxt == "#helpTxt":
      _ = olx.GetVar(name,None)
      _ = olx.GetVar(name.upper().replace("-", "_"),None)

  helpTxt = _

  popout = args.get('popout', False)
  box_type =args.get('type', 'help')
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
      titleTxt = "%s: %s" %(t[0], t[1])

  title = title.title()
  if not helpTxt or helpTxt == "None":
    helpTxt = OV.TranslatePhrase("%s-%s" %(help_src, box_type))
  helpTxt = helpTxt.replace("\r", "")
  helpTxt, d = format_help(helpTxt)
  d.setdefault('next',name)
  d.setdefault('previous',name)

  editLink = make_edit_link(name, box_type)

  if box_type != "help":
    banner_include = "<zimg border='0' src='banner_%s.png' usemap='map_tutorial'>" %box_type
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
    """ %d

  else:
    banner_include = ""
  if not popout:
    return_items = r'''
  <a href="spy.make_help_box -name='%s' -popout=True>>htmlhome">
    <zimg border='0' src='popout.png'>
  </a>
  <a href=htmlhome><zimg border='0' src='return.png'>
  </a>
''' %name

  else:
    return_items = ""

  if md_box:
    d = {'title':titleTxt.replace("_", " "), 'body':helpTxt, 'font_size_base':OV.GetParam('gui.help.base_font_size','3')}
    template = OV.GetParam('gui.help.pop_template', 'md_box').rstrip(".html").rstrip(".htm")
    p = OV.GetParam('gui.help.src', os.sep.join([OV.BaseDir(), 'etc', 'help', 'gui']))
    txt = get_template(template)%d

  else:
    txt = get_template('pop_help', base_path=p)
    txt = txt %(banner_include, name, titleTxt, helpTxt, return_items, editLink)

  wFilePath = r"%s-%s.htm" %(name, box_type)
  wFilePath = wFilePath.replace(" ", "_")
  #from ImageTools import ImageTools
  #IT = ImageTools()
  #txt = IT.get_unicode_characters(txt)
  OV.write_to_olex(wFilePath, txt)

  if box_type == 'help':
    if md_box:
      ws = olx.GetWindowSize('gl')
      ws = ws.split(',')
      boxWidth = int(int(ws[2])*OV.GetParam('gui.help.width_fraction',0.3))
      boxHeight = int(ws[3]) - 30
      x = int(ws[2]) - boxWidth -2
      y = int(ws[1]) + 50

    else:

      boxWidth = OV.GetParam('gui.help_box.width')
      length = len(helpTxt)
      tr = helpTxt.count('<br>')

      boxHeight = int(length/(boxWidth/OV.GetParam('gui.help_box.height_factor'))) + int(OV.GetParam('gui.help_box.height_constant') * (tr+2))
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
      ws = olx.GetWindowSize('gl')
      ws = ws.split(',')
      x = int(ws[0])
      y = int(ws[1]) + 50
      boxWidth = int(400)
      boxHeight = int(ws[3]) - 90

  if popout:
    if box_type == 'tutorial':
      pop_name = "Tutorial"
      name = "Tutorial"
    else:
      pop_name = "%s-%s"%(name, box_type)
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
        ''' %(wFilePath, boxWidth, boxHeight)
        webView = r"md_web.htm"
        OV.write_to_olex(webView, t)
        wFilePath = webView

      if "true" in olx.html.IsPopup(pop_name).lower():
        olx.Popup(pop_name, wFilePath)
      else:

        olx.Popup(pop_name, wFilePath,
          b="tcr", t=title, w=boxWidth, h=boxHeight, x=x, y=y)
        olx.html.SetBorders(pop_name,5)
      if box_type == 'tutorial':
        tutorial_box_initialised = pop_name

  else:
    olx.html.Load(wFilePath)
#  popup '%1-tbxh' 'basedir()/etc/gui/help/%1.htm' -b=tc -t='%1' -w=%3 -h=%2 -x=%4 -y=%5">

OV.registerMacro(make_help_box, '''name-Name of the Box&;popout-True/False&;
type-Type of Box (help or tutorial)&;helpTxt-The help text to appear in the help box&;toolName-name of the tool where the help shall appear&'''
)

def get_template(name, base_path=None):
  return gui.tools.TemplateProvider.get_template(name)


from Tutorials import AutoDemo
class AutoDemoTemp(AutoDemo):
  def __init__(self, name='default_auto_tutorial', reading_speed=2):
    super(AutoDemoTemp, self).__init__(name='default_auto_tutorial', reading_speed=2)
    self.source_base = p_path
    self.source_dir = os.sep.join([self.source_base, 'tutorials', 'EN'])
    self.p_path = gh.p_path
    gui.tools.TemplateProvider.get_all_templates(path=self.p_path, mask="*.html")


  def make_tutbox_popup(self):
    have_image = self.make_tutbox_image()

    self.format_txt()

    self.pop_title = self.current_tutorial_file.split(os.sep)[-1:][0].split(".")[0].replace("_", " ").title()
    if debug:
      edit = '<a href="shell %s">Edit</a>' %self.current_tutorial_file
    else:
      edit = ""

#    self.txt = markdown2.markdown(self.txt, extras=["wiki-tables"])
    self.txt = gh.format_html(self.txt)

    d = {}
    d.setdefault('pop_name',self.pop_name)
    d.setdefault('bg_colour',self.bg_colour)
    d['bg_colour'] = self.bg_colour
    d['button_bar_colour'] = self.button_bar_colour
    d.setdefault('font_colour',self.font_colour)
    d.setdefault('txt', self.txt)
    d.setdefault('src', self.current_tutorial_file)
    d.setdefault('title', self.pop_title)
    d.setdefault('edit', self.pop_name)
    d.setdefault('edit_link', gui.tools.TemplateProvider.get_template('edit_link')%d)

    if OV.IsControl('%s'%self.pop_name):
      pass
      #olx.html.ShowModal(self.pop_name)
    else:
      if self.interactive:
        txt = gui.tools.TemplateProvider.get_template('pop_tutorials')%d
      else:
        txt = gui.tools.TemplateProvider.get_template('pop_tutorials_loop')%s

      txt = txt.decode('utf-8')

      OV.write_to_olex("%s.htm" %self.pop_name.lower(), txt)
      boxWidth = 450
      boxHeight = 320
      x = OV.GetHtmlPanelX() - boxWidth - 40
      y = 70
      if self.have_box_already:
        olx.Popup(self.pop_name, '%s.htm' %self.pop_name.lower(), t=self.pop_name)
      else:
        if self.interactive:
          olx.Popup(self.pop_name, '%s.htm' %self.pop_name.lower(),
           b='t', t=self.pop_name, w=boxWidth, h=boxHeight, x=x, y=y)
          olx.html.SetFocus(self.pop_name + '.TUTORIAL_NEXT')
        else:
          boxWidth = 400
          boxHeight = 250
          x = OV.GetHtmlPanelX() - boxWidth - 40
          y = 75
          olx.Popup(self.pop_name, '%s.htm' %self.pop_name.lower(), **{'b':'t', 't':self.pop_name, 'w':boxWidth, 'h':boxHeight, 'x':x, 'y':y})
        self.have_box_already = True
        #olx.html.Show(self.pop_name)
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


    except Exception, err:
      print "+++ ERROR IN TUTORIALS: %s" %err
      sys.stderr.formatExceptionInfo()
      self.end_tutorial()

  def read_tutorial_definitions(self):
    ## First read in the commands that preceeds all tutorials
    self.items = gui.tools.TemplateProvider.get_template('all_tutorials_preamble').split("\n")

    ## Then read in the actual tutorial
    _ = os.sep.join([self.source_dir, self.name + ".txt"])
    self.current_tutorial_file = _
    if debug:
      print "opening %s" %self.current_tutorial_file
    rFile = open(_,'r')
    self.items = self.items + rFile.readlines()
    rFile.close()
    self.items = self.items + gui.tools.TemplateProvider.get_template('all_tutorials_end').split("\n")

AutoDemoTemp_instance = AutoDemoTemp()

