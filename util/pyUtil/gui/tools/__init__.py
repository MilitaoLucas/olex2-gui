import olex
import olx
import os

from olexFunctions import OlexFunctions
OV = OlexFunctions()


class FolderView:
  root = None
  class node:
    name = None
    full_name = None
    parent = None
    content = None

    def __init__(self, name, full_name=None):
      self.name = name
      if full_name:
        self.full_name = full_name
      else:
        self.full_name = name

    def toStr(self, prefix=""):
      s = prefix+self.name
      s += "\n%s" %(self.full_name)
      if self.content:
        prefix += '\t'
        for c in self.content:
          s += '\n%s%s' %(prefix,c.toStr(prefix))
      return s

    def expand(self, mask, fname=""):
      self.content = []
      if not fname:
        fname = self.name
      for i in os.listdir(fname):
        dn = os.path.normpath(fname + '/' + i)
        if os.path.isdir(dn) and i != '.olex':
          dr = FolderView.node(i, dn)
          dr.expand(mask, dn)
          if len(dr.content):
            self.content.append(dr)
        else:
          if( os.path.splitext(i)[1] in mask):
            self.content.append(FolderView.node(i, dn))


  def list(self, mask=".ins;.res;.cif;.oxm"):
    r = OV.GetParam('user.folder_view_root')
    if not r:
      r = "."
    f = olx.ChooseDir('Select folder', '%s' %r)
    if f:
      self.root = FolderView.node(f)
      self.root.expand(mask=set(mask.split(';')))
      olx.html.Update()

  def generateHtml(self):
    import OlexVFS
    if not self.root:
      return "&nbsp;"
    OV.SetParam('user.folder_view_root', self.root.name)
    data = self.root.toStr()
    OlexVFS.write_to_olex('folder_view.data', data.encode('utf-8'))
    return "<input type='tree' manage noroot src='folder_view.data' name='fvt'"+\
  " onselect='spy.gui.tools.folder_view.loadStructure(html.GetValue(~name~))'"+\
  " height=200 width=" + str(int(olx.html.ClientWidth('self'))-30) + ">"

  def loadStructure(self, v):
    if os.path.isfile(v):
      olex.m("reap '%s'" %v)

fv = FolderView()
olex.registerFunction(fv.list, False, "gui.tools.folder_view")
olex.registerFunction(fv.generateHtml, False, "gui.tools.folder_view")
olex.registerFunction(fv.loadStructure, False, "gui.tools.folder_view")



def start_where():
  if olx.IsFileLoaded() == "false":
    return
  from gui import SwitchPanel
#  if olx.xf.au.GetAtomCount() == "0" and olx.IsFileType('ires') == "true":
#    SwitchPanel('work')
#    flash_gui_control('btn-solve')
#    print "Use 'Solve' button in tab 'Work' to solve the structure."
#    return

  if olx.IsVar('start_where') == 'false':
    where = OV.GetParam('user.start_where').lower()
    SwitchPanel(where)
    olx.SetVar('start_where',False)

olex.registerFunction(start_where, False, "gui.tools")


def flash_gui_control(control):
  ''' Flashes a control on the GUI in order to highlight it's position '''
  if ';' in control:
    n = int(control.split(';')[1])
    control = control.split(';')[0]
  else:
    n = 2

  control_name = "IMG_%s" %control.upper()
  if '@' in control:
    print "@ in control"
    control_image = control.lower().split('@')[0]
  else:
    control_image = control
  for i in xrange(n):
    if "element" in control:
      new_image = "up=%son.png" %control_image
      olx.html.SetImage(control_name,new_image)
    elif control.endswith('_bg'):
      cmd = 'html.setBG(%s,%s)' %(control_image.rstrip('_bg'), self.highlight_colour)
      olex.m(cmd)
    else:
      new_image = "up=%soff.png" %control_image
      olx.html.SetImage(control_name,new_image)
    OV.Refresh()
    olx.Wait(300)

    if "element" in control:
      new_image = "up=%soff.png" %control
      olx.html.SetImage(control_name,new_image)
    elif control.endswith('_bg'):
      cmd = 'html.setBG(%s,%s)' %(control.rstrip('_bg'), '#fffffe')
      olex.m(cmd)
    else:
      new_image = "up=%shighlight.png" %control_image
      olx.html.SetImage(control_name,new_image)
    OV.Refresh()
    olx.Wait(300)

  if not control.endswith('_bg'):
    new_image = "up=%soff.png" %control_image
    olx.html.SetImage(control_name,new_image)

olex.registerFunction(flash_gui_control, False, "gui.tools")

def get_OV_path(path):
  if "()" in path:
    p = getattr(OV, path.split('()')[0])()
    path = "%s/%s" %(p, path.split('()')[1])
  return path


def make_single_gui_image(img_txt="", type='h2'):
  from PilTools import timage
  import OlexVFS
  timage = timage()
  states = ["on", "off", "highlight", "", "hover", "hoveron"]
  for state in states:
    image = timage.make_timage(item_type=type, item=img_txt, state=state)
    if type == "h1":
      alias = "h2"
    else:
      alias = type
    name = "%s-%s%s.png" %(alias, img_txt.lower(), state)
    OlexVFS.save_image_to_olex(image, name, 2)  


def add_tool_to_index(scope="", link="", path="", location="", before="", filetype="", level="h1"):
  import OlexVFS
  if not OV.HasGUI:
    return

  if not scope:
    return

  if not link:
    return

  if not path:
    return

  ''' Automatically add a link to GUI to an Olex2 index file. '''
  if not location:
    location = OV.GetParam('%s.gui.location' %scope)
  if not before:
    before = OV.GetParam('%s.gui.before' %scope)
  if not location:
    return
  txt = OlexVFS.read_from_olex('%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir(), location))

  if not filetype:
    t = r'''
<!-- #include %s-%s %s/%s.htm;gui\blocks\tool-off.htm;image=%s;onclick=;1; -->''' %(scope, link, path, link, link)
  else:
    t = r'''
<!-- #includeif IsFileType('%s') %s-%s %s/%s.htm;gui\blocks\tool-off.htm;image=%s;onclick=;1; -->''' %(filetype, scope, link, path, link, link)


  index_text = ""
  if t not in txt:
    if before not in txt or before.lower() == "end":
      u = "%s\n%s" %(txt, t)
    else:
      u = ""
      for line in txt.strip().split("\r\n"):
        if not line:
          continue
        if "%s-%s" %(location, before) in line:
          u += "%s\n%s\n" %(t, line)
        else:
          u += "%s\n" %line.strip()
    OlexVFS.write_to_olex('%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir(), location), u, 0)
    index_text = u
  else:
    if run:
      OlexVFS.write_to_olex('%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir(), location), t, 0)
    else:
      if not index_text:
        text = txt
      else:
        text = index_text
      OlexVFS.write_to_olex('%s/etc/gui/blocks/index-%s.htm' %(OV.BaseDir(), location), text, 0)

  make_single_gui_image(link, type=level)