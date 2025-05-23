import sys
import olx
import olex
import olex_fs
import os
from olexFunctions import OV
from ImageTools import IT
import gui

import OlexVFS

import time

global ppi
if OV.HasGUI():
  import olex_gui
  ppi = olex_gui.GetPPI()[0]
else:
  ppi = 96


timing = False  # bool(OV.GetParam('gui.timing'))


def adjust_skin_colours():
  base_colour = OV.GetParam('gui.html.base_colour')
  item = ['tab', 'timage', 'snumtitle']
  for tem in item:
    if not OV.GetParam('gui.%s.base_colour' % tem):
      OV.SetParam('gui.%s.base_colour' % tem, base_colour)

  if OV.GetParam('gui.snumtitle.filefullinfo_colour') is None:
    OV.SetParam('gui.snumtitle.filefullinfo_colour',
                IT.adjust_colour(base_colour.rgb, luminosity=OV.GetParam('gui.snumtitle.filefullinfo_colour_L')))


def adjust_skin_luminosity():
  base_colour = OV.GetParam('gui.base_colour')

  scope_l = ['gui',
             'gui.timage',
             'gui.timage.button',
             'gui.timage.h1',
             'gui.timage.h3',
             'gui.timage.tab',
             'gui.timage.cbtn',
             'gui.timage.snumtitle']

  for scope in scope_l:
    gui = olx.gui_phil_handler.get_scope_by_name(scope)
    for object in gui.active_objects():
      if object.is_scope:
        continue
      try:
        data_type = object.type.phil_type
        if data_type == 'colour':
          name = object.name
          if object.extract() is None:
            name = object.name
            if "base_colour" in name:
              OV.SetParam('%s.%s' % (scope, name), base_colour)
            else:
              OV.SetParam('%s.%s' % (scope, name),
                          IT.adjust_colour(base_colour.rgb, luminosity=OV.GetParam('%s.%s_L' % (scope, name))))
          # print "%s.%s: %s" %(scope, name, OV.GetParam('%s.%s' %(scope,name)))
      except Exception as ex:
        print(ex)
        pass
        # print "Something has gone wrong with SKIN adjust_skin_luminosity: %s" %ex


def SetGrad():
  l = ['top_right', 'top_left', 'bottom_right', 'bottom_left']
  v = []
  for i in range(4):
    val = OV.GetParam('gui.grad_%s' % (l[i])).hexadecimal
    if not val:
      val = "#ffffff"
    val = IT.hex2dec(val)
    v.append(val)
  olx.Grad(v[0], v[1], v[2], v[3])


def SetMaterials():
  if OV.GetParam('gui.skin.materials_have_been_set'):
    return
  olx.SetMaterial("InfoBox.Text", OV.GetParam('gui.infobox_text'))
  olx.SetMaterial("InfoBox.Plane", OV.GetParam('gui.infobox_plane'))
  olx.SetMaterial("Console.Text", OV.GetParam('gui.infobox_text'))
  olx.SetMaterial("XGrid.+Surface", OV.GetParam('gui.xgrid.positive_surface_material'))
  olx.SetMaterial("XGrid.-Surface", OV.GetParam('gui.xgrid.negative_surface_material'))
  olex.m("gl.lm.ClearColor(%s)" % OV.GetParam('gui.skin.clearcolor'))
  olex.m("SetFont Default %s" % OV.GetParam('gui.console_font'))
  olex.m("SetFont Labels %s" % OV.GetParam('gui.labels_font'))
  # olx.HtmlPanelWidth(OV.GetParam('gui.htmlpanelwidth'))

  olex.m("lines %s" % OV.GetParam('gui.lines_of_cmd_text'))

  OV.SetParam('gui.skin.materials_have_been_set', True)


def load_user_gui_phil():
  gui_phil_path = "%s/gui.phil" % (OV.DataDir())
  if os.path.exists(gui_phil_path):
    gui_phil = open(gui_phil_path, 'r', encoding="utf-8").read()
    olx.gui_phil_handler.update(phil_string=gui_phil)


def check_os():
  if sys.platform == 'darwin':
    return "mac"
  if sys.platform == 'win32':
    return "win"
  else:
    return "lin"


def check_for_first_run():
  import olexex
  first_run = not os.path.exists("%s/global.odb" % OV.DataDir())
# 2016-07-26 do we need changing skin on update any longer? I doubt
# With the new scalable skins it should now be OK to run this.
  if first_run and OV.HasGUI():
    try:
      # olx.SkinUpdated is intentionally not there:
      olx.SkinUpdated
      return False
    except Exception as e:
      # print(e)
      olx.SkinUpdated = True
    startup_skin = OV.GetParam('gui.skin.name', 'default')
    if check_os().upper() == 'MAC' and startup_skin == 'default':
      startup_skin = "mac"
    _ = Skin()
    _.change_skin(startup_skin, internal_change=not first_run)
    return True
  return False

def deal_with_gui_phil(action):
  skin_name = OV.GetParam('gui.skin.name', 'default')
  skin_extension = OV.GetParam('gui.skin.extension', None)

  if timing:
    t = time.time()

  if action == 'load':
    OV.SetHtmlFontSize()
    OV.SetHtmlFontSizeControls()
    olx.gui_phil_handler.reset_scope('gui')
    gui_skin_phil_path = "%s/etc/skins/%s.phil" % (OV.BaseDir(), skin_name)
    if not os.path.isfile(gui_skin_phil_path):
      gui_skin_phil_path = "%s/gui.params" % (OV.BaseDir())
    if os.path.isfile(gui_skin_phil_path):
      gui_skin_phil = open(gui_skin_phil_path, 'r', encoding="utf-8").read()
      olx.gui_phil_handler.update(phil_string=gui_skin_phil)

    if skin_extension:
      gui_skin_phil_path = "%s/etc/skins/%s.phil" % (OV.BaseDir(), skin_extension)
      if os.path.isfile(gui_skin_phil_path):
        gui_skin_phil = open(gui_skin_phil_path, 'r', encoding="utf-8").read()
        olx.gui_phil_handler.update(phil_string=gui_skin_phil)
  else:
    gui_phil_path = "%s/gui.phil" % (OV.DataDir())
    olx.gui_phil_handler.save_param_file(
      file_name=gui_phil_path, scope_name='gui', diff_only=True)
  if timing:
    print("After 'Reading/Saving PHIL Stuff': %.2f s" % (time.time() - t))

def export_parameters(load_phil=True):
  if timing:
    t = time.time()
  if check_for_first_run():
    return
  if load_phil:
    deal_with_gui_phil(action='load')

  if OV.HasGUI():
    from gui import tools as gtools
    gtools.cache = {}
    table_width = int(olx.html.ClientWidth('self')) - 2 * int(olx.html.GetBorders())
    if sys.platform[:3] == 'win':
      table_width = int(table_width * 96 / ppi)
    OV.SetParam('HtmlTableWidth', table_width)
    OV.SetVar('HtmlTableWidth', table_width)

    OV.SetVar('HtmlGuiFontSize', OV.GetParam('gui.html.font_size'))
    OV.SetVar('HtmlFontSizeControls', OV.GetParam('gui.html.font_size_controls'))
    OV.SetVar('HtmlFontSizeLarge', OV.GetParam('gui.html.font_size_large'))
    OV.SetVar('HtmlFontSizeMedium', OV.GetParam('gui.html.font_size_medium'))
    OV.SetVar('HtmlFontSizeExtraLarge', OV.GetParam('gui.html.font_size_extra_large'))

    # Stepwise ajust relative font size according to cut-off
    font_size_steps = OV.GetParam('gui.font_size_steps')
    font_size_rel_size = OV.GetParam('gui.font_size_rel_size')
    _ = int(olx.html.ClientWidth('self'))
    for step, s in zip(font_size_steps, font_size_rel_size):
      step = int(step)
      s = int(s)
      if _ >= step:
        #if ppi > 96:
          #s += OV.GetParam('gui.ppi_font_adjust_amount')
        OV.SetVar('HtmlGuiFontSize', OV.GetParam('gui.html.font_size') + s)
        OV.SetVar('HtmlFontSizeControls', OV.GetParam('gui.html.font_size_controls') + s)
        OV.SetVar('HtmlFontSizeLarge', OV.GetParam('gui.html.font_size_large') + s)
        OV.SetVar('HtmlFontSizeMedium', OV.GetParam('gui.html.font_size_medium') + s)
        OV.SetVar('HtmlFontSizeExtraLarge', OV.GetParam('gui.html.font_size_extra_large') + s)
        break

  OV.SetVar('HtmlTableFirstcolColour', OV.GetParam('gui.html.table_firstcol_colour').hexadecimal)
  OV.SetVar('HtmlTableFirstcolWidth', OV.GetParam('gui.html.table_firstcol_width'))
  OV.SetVar('HtmlTableBgColour', OV.GetParam('gui.html.table_bg_colour').hexadecimal)
  OV.SetVar('HtmlTableGroupBgColour', OV.GetParam('gui.html.table_group_bg_colour').hexadecimal)
  OV.SetVar('HtmlTableGroupHeaderColour', OV.GetParam('gui.html.table_group_header_colour').hexadecimal)
  OV.SetVar('HtmlTableRowBgColour', OV.GetParam('gui.html.table_row_bg_colour').hexadecimal)
  OV.SetVar('HtmlInputBgColour', OV.GetParam('gui.html.input_bg_colour').hexadecimal)
  OV.SetVar('HtmlComboHeight', OV.GetParam('gui.html.combo_height'))
  OV.SetVar('HtmlComboWidth2', OV.GetParam('gui.html.combo_width_2'))
  OV.SetVar('HtmlInputHeight', OV.GetParam('gui.html.input_height'))
  OV.SetVar('HtmlHighlightColour', OV.GetParam('gui.html.highlight_colour').hexadecimal)
  OV.SetVar('gui.watermark', OV.GetParam('gui.watermark').hexadecimal)
  OV.SetVar('gui.action_colour', OV.GetParam('gui.action_colour').hexadecimal)
  OV.SetVar('gui.grey', OV.GetParam('gui.grey').hexadecimal)
  OV.SetVar('gui.blue', OV.GetParam('gui.blue').hexadecimal)
  OV.SetVar('gui.green', OV.GetParam('gui.green').hexadecimal)
  OV.SetVar('gui.dark_green', OV.GetParam('gui.dark_green').hexadecimal)
  OV.SetVar('gui.green_text', OV.GetParam('gui.green_text').hexadecimal)
  OV.SetVar('gui.orange', OV.GetParam('gui.orange').hexadecimal)
  OV.SetVar('gui.dark_yellow', OV.GetParam('gui.dark_yellow').hexadecimal)
  OV.SetVar('gui.red', OV.GetParam('gui.red').hexadecimal)
  OV.SetVar('ed_bg', OV.GetParam('gui.ed_bg').hexadecimal)
  OV.SetVar('ed_fg', OV.GetParam('gui.ed_fg').hexadecimal)
  OV.SetVar('HtmlCheckboxHeight', OV.GetParam('gui.html.checkbox_height'))
  OV.SetVar('HtmlCheckboxWidth', OV.GetParam('gui.html.checkbox_width'))
  OV.SetVar('HtmlCheckboxWidth2', OV.GetParam('gui.html.checkbox_width_2'))
  OV.SetVar('TimageColour', OV.GetParam('gui.timage.grad_colour').hexadecimal)
  OV.SetVar('HtmlSpinHeight', OV.GetParam('gui.html.spin_height'))
  OV.SetVar('HtmlLinkColour', OV.GetParam('gui.html.link_colour').hexadecimal)
  OV.SetVar('HtmlBgColour', OV.GetParam('gui.html.bg_colour').hexadecimal)
  OV.SetVar('HtmlFontName', OV.GetParam('gui.html.font_name'))
  OV.SetVar('HtmlFontColour', OV.GetParam('gui.html.font_colour').hexadecimal)
  OV.SetVar('HtmlPanelWidth', OV.GetParam('gui.htmlpanelwidth'))
  OV.SetVar('HtmlButtonHeight', OV.GetParam('gui.timage.button.height'))
  OV.SetVar('link_type', OV.GetParam('gui.skin.link_type'))
  OV.SetVar('default_link', OV.GetParam('gui.skin.default_link'))
  OV.SetVar('linkButton.flat', OV.GetParam('gui.skin.link_button.flat'))
  OV.SetVar('linkButton.fgcolor', OV.GetParam('gui.skin.link_button.fgcolor').hexadecimal)
  OV.SetVar('history_width', IT.history_width)
  OV.SetVar('button.highlight.lightness', OV.GetParam('gui.skin.button.highlight.lightness'))
  OV.SetVar('button.border.lightness', OV.GetParam('gui.skin.button.border.lightness'))
  OV.SetVar('custom_button', 'border.lightness: %s;highlight.lightness: %s' % (
    OV.GetParam('gui.skin.button.highlight.lightness'), OV.GetParam('gui.skin.button.border.lightness')))
  try:
    OV.SetVar('linkButton.bgcolor', OV.GetParam('gui.skin.link_button.bgcolor').hexadecimal)
  except:
    OV.SetVar('linkButton.bgcolor', OV.GetParam('gui.skin.link_button.bgcolor'))

  if timing:
    print("export_parameters took %.4fs" % (time.time() - t))


OV.registerFunction(export_parameters, False, 'skin')


class Skin():
  def __init__(self):
    load_user_gui_phil()
    export_parameters()
    self.sNum = ""
    self.sg = ""
    self.data_index = ""
    import PilTools
    self.TI = PilTools.TI
    OV.registerFunction(self.change_skin)
    OV.registerFunction(self.adjust_font_size_for_ppi, True, 'gui.skin')
    # self.change()

  def change_skin(self, info, internal_change=False):
    new_width = None
    if not info:
      if OV.HasGUI():
        info = olx.html.ClientWidth('self')
      else:
        info = OV.GetParam('gui.skin.base_width')

    if not internal_change:
      try:
        _ = float(info)
        if _ > 1:
          new_width = int(info)
        else:
          new_width = info

      except:
        toks = info.split('_')
        if len(toks) == 1:
          toks.append('')
        OV.SetParam('gui.skin.name', toks[0])
        OV.SetParam('gui.skin.extension', toks[1])
        deal_with_gui_phil('load')

    olx.fs.Clear()
    OlexVFS.write_to_olex('logo1_txt.htm', " ", 2)

    if timing:
      t1 = time.time()
      t2 = 0

    if not internal_change:
      w = new_width
      if not w:
        w = OV.GetParam('gui.htmlpanelwidth', None)
      if w:
        IT.set_htmlpanel_width(w)
#        olx.HtmlPanelWidth(w)

    try:
      adjust_skin_luminosity()
    except:
      pass

    if timing:
      t = time.time()
      print("After 'adjust_skin_luminosity': %.2f s (%.5f s)" % ((t - t1), (t - t2)))
      t2 = t

    self.TI.run_timage(force_images=False)
    if olx.IsFileLoaded() =='true':
      im = self.TI.make_timage('snumtitle', OV.FileName(), 'on', titleCase=False)
      OlexVFS.save_image_to_olex(im, "sNumTitle.png", 1)
    #import initpy
    # initpy.set_plugins_paths()

    if timing:
      t = time.time()
      print("After 'resize_skin_logo': %.2f s (%.5f s)" % ((t - t1), (t - t2)))
      t2 = t

    if timing:
      t = time.time()
      print("After 'sNumTitle': %.2f s (%.5f s)" % ((t - t1), (t - t2)))
      t2 = t

    if not internal_change and not new_width:
      SetGrad()
      SetMaterials()
      OV.setAllMainToolbarTabButtons()
      olex.m('htmlpanelswap %s' % OV.GetParam('gui.htmlpanel_side'))

    if OV.FileFull() != "none":
      from History import hist
      try:
        hist.make_history_bars()
      except:
        pass

    if timing:
      t = time.time()
      print("After 'Reload': %.2f s (%.5f s)" % ((t - t1), (t - t2)))
      t2 = t

    if timing:
      t = time.time()
      print("After 'Save PHIL': %.2f s (%.5f s)" % ((t - t1), (t - t2)))
      t2 = t

    export_parameters(load_phil=False)
    deal_with_gui_phil('save')

    if olx.IsFileLoaded() =='true':
      olex.m("spy.make_HOS()")

    try:
      for item in olx.VFSDependent:
        try:
          item.load_ressources()
        except Exception as err:
          print("Could not load ressources for '%s': %s" % (item, err))
    except:
      pass

    #try:
      #for plugin in olx.InstalledPlugins:
        #try:
          #plugin.setup_gui(force=True)
        #except Exception as err:
          #print("Could not update images for plugin '%s': %s" % (plugin, err))
    #except:
      #pass

    olx.FlushFS()

  def change(self):
    skin = OV.GetParam('gui.skin.name')
    skin_extension = OV.GetParam('gui.skin.extension')

    try:
      skin_path = "%s/util/pyUtil/PluginLib/skins/plugin-%sSkin" % (OV.BaseDir(), skin)
      if skin_path not in sys.path:
        sys.path.append("%s/util/pyUtil/PluginLib/skins/plugin-%sSkin" % (OV.BaseDir(), skin))
      PilTools = __import__("PilTools_%s" % skin)
      # print "pyTools -- Using %s skin." %"PilTools_%s: %s" %(skin, tool)
    except ImportError:
      # print "pyTools -- Using Default PilTools for Tool: %s" %tool
      import PilTools
    except Exception as err:
      raise
    self.GuiSkinChanger_instance = PilTools.GuiSkinChanger()
    self.GuiSkinChanger_instance.run_GuiSkinChanger()
    OV.SetVar('olex2_sNum_id_string', "")
    self.sNumTitle_instance = PilTools.sNumTitle()
    self.adjust_font_size_for_ppi()

  def run_skin(self, f):
    try:
      f = f.decode()
    except:
      pass
    new_width = OV.GetParam('gui.htmlpanelwidth')
    if new_width < 350:
      OV.SetParam('gui.skin.extension', 'small')
    if timing:
      t = time.time()
    if f == 'timage':
#      a = PilTools.timage()
      self.TI.run_timage(force_images=True)
      if timing:
        print("run_skin timage took %.4fs" % (time.time() - t))
    elif f == 'sNumTitle':
      if olx.IsFileLoaded() =='false': return
      try:
        data_idx = olx.xf.CurrentData() + olx.FileExt()
      except:
        data_idx = False
      try:
        sg =  olex.f('sg()')
      except:
        return
      if olex_fs.Exists("sNumTitle.png") and self.sNum == OV.FileName()\
         and self.sg == sg and self.data_index == data_idx:
        if timing:
          print("run_skin sNumTitle took %.4fs (not run)" % (time.time() - t))
        return
      items = {}
      sNum = items.setdefault("sNum", OV.FileName())
      image = self.TI.make_timage('snumtitle', sNum, 'on', titleCase=False)
      name = r"sNumTitle.png"
      OlexVFS.save_image_to_olex(image, name, 1)
      OV.CopyVFSFile(name, 'SNUMTITLE', 2)

      if timing:
        print("run_skin sNumTitle took %.4fs" % (time.time() - t))
      self.sNum = OV.FileName()
      try:
        self.sg = olex.f('sg()')
      except:
        self.sg = None
      try:
        self.data_index = olx.xf.CurrentData()
      except:
        self.data_index = False

    elif f == 'change':
      self.change()
      self.TI.run_timage()
      self.sNumTitle_instance.run_sNumTitle(force=True)
      if timing:
        print("run_skin change took %.4fs" % (time.time() - t))

    olx.FlushFS()

  def adjust_font_size_for_ppi(self):
    html_font_size = int(OV.FindValue('gui_html_font_size').strip())
    if ppi > 96:
      OV.SetVar('gui_html_font_size', html_font_size - 1)
    else:
      OV.SetVar('gui_html_font_size', html_font_size + 2)


Skin_instance = Skin()
OV.registerMacro(Skin_instance.run_skin, '')

OV.registerFunction(load_user_gui_phil)


def get_colour_choice(scope, what):
  import shlex
  if what == "value":
    val = OV.GetParam('%s.colour' % scope)
    return val
  elif what == "items":
    t = ""
    for item in OV.GetParam(variable='%s.colours' % scope, default='[@@elements]'):
      t += "%s;" % (item.split("@@")[1])
    return t + "[new colour]"


OV.registerFunction(get_colour_choice, False, 'gui.skin')


def define_new_bond_colour(name):
  pass


def get_user_bond_colour(colour):
  c = ""
  cc = ""
  _ = OV.GetParam('user.bonds.colour')
  for item in OV.GetParam(variable='user.bonds.colours', default='[@@elements]'):
    if item.split("@@")[1] == colour:
      c = item.split("@@")[0].replace("@", ";").replace("*", "")
    if item.split("@@")[1] == _:
      cc = item.split("@@")[0].replace("@", ";").replace("*", "")
  if not c:
    res = olex.m("SetVar(temp,ChooseMaterial(%s))" % cc)
    if not res:
      return
    c = olx.GetVar('temp')
    #c = '5;16744448;4294967168'
    l = OV.GetParam(variable='user.bonds.colours', default=[])
    _ = "%s@@%s" % (c.replace(";", "@"), colour)
    l.append(_)
    t = ""
    for item in l:
      t += "%s;" % (item.split("@@")[1])
    try:
      olx.html.SetItems("BOND_COLOUR_COMBO", t)
      olx.html.SetValue("BOND_COLOUR_COMBO", colour)
    except:
      pass
    OV.SetParam('user.bonds.colours', l)
  _ = "%s@@%s" % (c.replace(";", "@"), colour)
  OV.SetParam('user.bonds.colour', colour)
  return c


def change_bond_radius():
  rad = OV.GetParam('user.bonds.thickness')
  olex.m("brad %s" % rad)


def change_bond_colour(scope="", colour="", display_style="", bypass_collections=False):
  include_H = True

  if not colour:
    colour = OV.GetParam('snum.bonds.colour')
  if not colour:
    colour = OV.GetParam('user.bonds.colour')

  import shlex
  if "[" in colour:
    olx.html.SetValue('BOND_COLOUR_COMBO%s' % scope, "")
    return
  if "@" in colour:
    print("Please do not use the '@' character in colour names")
    return

  if not colour:
    colour = OV.GetParam('user.bonds.colour', 'elements')

  if include_H:
    olx.ShowH("a", True)
    olx.ShowH("b", False)

  _select_bonds(bypass_collections=bypass_collections)

  if colour == 'elements':
    olx.Mask(48)

    OV.SetParam('snum.bonds.colour', 'elements')
    OV.SetParam('snum.bonds.mask', 48)
  else:
    c = get_user_bond_colour(colour)
    olx.Mask(1)
    olx.SetMaterial("Singlecone", "%s" % str(c))

    OV.SetParam('snum.bonds.mask', 1)
    OV.SetParam('snum.bonds.colour', colour)

  if include_H:
    olex.m("sel -u")
    olex.m("sel bonds where xbond.b.bai.z == -1")
    olx.Sel("-u")
    olx.ShowH("b", True)
  if scope:
    olx.html.SetValue("BOND_COLOUR_COMBO%s" % scope, colour)


OV.registerFunction(change_bond_colour, True, 'gui.skin')


def _select_bonds(bypass_collections=False):
  if bypass_collections:
    olex.m("sel %s" % bypass_collections)
    olex.m("sel bonds where xbond.type==3")
    olex.m("sel -i")
  else:
    olex.m("showQ a false")
    olex.m("sel bonds where xbond.type==3")
    olex.m("sel -i")
  olex.m("sel atoms -u")


OV.registerFunction(_select_bonds, True, 'gui.skin')


def _get_available_html_width(margin_adjust=True, first_col_width_adjust=True, ppi_aware=True):
  width = int(olx.html.ClientWidth('self'))
  max_width = width
  if width < 100:
    width = OV.GetParam('gui.htmlpanelwidth')
  if margin_adjust:
    width = width - OV.GetParam('gui.htmlpanelwidth_margin_adjust')
  if first_col_width_adjust:
    width = width - OV.GetParam('gui.html.table_firstcol_width')
  if ppi_aware:
    width = int(width * ppi / 96)
    max_width = int(max_width * ppi / 96)

  if width <= 0:
    width = 10
  if max_width <= 0:
    max_width = 10

  return width, max_width


