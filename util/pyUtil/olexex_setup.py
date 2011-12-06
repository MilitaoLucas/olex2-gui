from olexFunctions import OlexFunctions
OV = OlexFunctions()

import htmlTools


import olex
import olx
import htmlTools
import variableFunctions

class SetupWizard(object):

  def tbxs(self, f):
    total_number = 6
    name = f.get('n','0')
    current = int(name)
    retVal = ""
    if current >= total_number:
      self.previous = str(current -1)
      self.next = '0'
    elif current <= 0:
      self.previous = str(total_number)
      self.next = '1'
    else:
      self.previous = str(current -1)
      self.next = str(current + 1)

    txt = '''
<zimg border="0" src="banner_setup.png" usemap="#map_setup">

<map name="map_setup">
<!-- Button PREVIOUS -->
    <area shape="rect"
      coords="250,0,295,60"
      href='spy.tbxs -n=%s' target='%%previous%%'>

<!-- Button NEXT-->
    <area shape="rect"
      coords="295,0,330,60"
      href='spy.tbxs -n=%s' target='%%next%%'>
</map>

<!-- #include tool-top gui/blocks/help-top.htm;image=blank;1; -->

'''% (self.previous, self.next)

    t = OV.TranslatePhrase('setup-txt-%s' %name)
    t, d = htmlTools.format_help(t)

    txt += r'''
<tr VALIGN='center' NAME='Setup Title'>
  <td width="8" bgcolor="$GetVar(HtmlHighlightColour)"></td>
    <td width='80%%' colspan='2' bgcolor="$GetVar(HtmlTableFirstcolColour)">
      <font size='4' color="$GetVar(HtmlFontColour">
        <b>
          %%setup-title-%s%%
        </b>
      </font>
    </td>
  </tr>
<tr>
  <td valign='top' width="8" bgcolor="$GetVar(HtmlTableFirstcolColour)"></td>
  <td colspan = 2>
  <font size = '3'>
    %s
  </font>
  </td>
</tr>

<tr>
  <td width="8" bgcolor="$GetVar(HtmlTableFirstcolColour)"></td>
  <td colspan='2' align='right'>%s

    <a href="html.Hide setup-box ">Close this Window</a>
  </td>
</tr>

'''%(name, t, htmlTools.make_edit_link("setup-txt", name))


    txt += r'''
<!-- #include tool-footer gui\blocks\tool-footer.htm;colspan=3;1; -->
'''
    wFilePath = r"setup-%s.htm" %name
    OV.write_to_olex(wFilePath, txt)
    olex.m("popup setup-box 'setup-%s.htm' -b=tc -t='%s' -w=340 -h=700 -x=50 -y=50" %(name, 'Olex2 Setup'))

    olx.html.SetBorders('setup-box', 2)
    OV.UpdateHtml('setup-box')
    return retVal


a = SetupWizard()
OV.registerMacro(a.tbxs, 'n-The name of the setup screen')


class ConfigSkin(object):
  def __init__(self):
    from ImageTools import ImageTools
    self.IT = ImageTools()

  def config_changed_var_val(self, var, value, args={}):
    #if "font_name" in var.lower():
      #val = olx.GetVar(var).split(';')[-1:][0]
      #olx.SetVar(var,val)
    if 'font_name' in var.lower():
      value = value.split(';')[-1:][0]
    if value:
      OV.SetVar(var,value)
      self.config[var]['val'] = value
      self.generate_config_box_text()
      self.create_config_box()

  def config_changed_luminosity(self, var, args):
    adjust = args['adjust']
    val = OV.FindValue("L_%s" %var)
    val += adjust
    OV.SetVar(var,val)
    self.config_changed_var_val(var)

  def read_config_file(self):
    config = {}
    cfgFile = open(self.cfgFileName, 'r')
    i = 0
    for line in cfgFile:
      i += 1
      line= line.strip()
      if line.startswith("#C"):
        config.setdefault('Comment%s' %str(i), {'val':"%s<br>" %line[2:].strip(), 'num':i})
      l = line.split("=")
      if len(l) > 1:
        if "_COLOUR" in l[0]:
          val = l[1]
          if "(" in val:
            val = self.IT.RGBToHTMLColor(eval(val))
          config.setdefault(l[0], {'num':i, 'val':val})
        else:
          config.setdefault(l[0], {'num':i, 'val':l[1]})
    self.config = config

  def getVarFromOlex(self):
    olexValues = variableFunctions.getVVD('gui')
    for var in self.config:
      if var.lower() in olexValues.keys():
        self.config[var]['val'] = olexValues[var.lower()]

  def generate_config_box_text(self):
    str = ""
    cfg = []
    first_col_width = 200
    for var in self.config:
      cfg.append((self.config[var].get('num'), var, self.config[var].get('val')))
    cfg.sort()
    str += '<table border=0>\n'
    for num, var, val in cfg:
      varName = var.replace('_',' ').capitalize()
      if "Comment" in var:
        str += "</table>\n"
        str += "<b>%s</b>\n" %val
        str += '<table border=0>\n'
      #elif var.startswith("L_"):
        #href = 'test'
        #str += "%s:\t<a href='%s'>%s</a><br>" %(var, href, val)
      elif "#" in val or "COLOUR" in var:
        if var.startswith("L_"): continue
        if not val:
          val = OV.FindValue(var)
        #href = "SetVar(%s,Color(hex,%s))" %(var, val)
        href = "spy.config_changed_var_val %s Color(hex,%s)" %(var,val)
        if "_grad_" in var.lower():
          href += ">>spy.SetGrad"
        elif "html_link_" in var.lower() or "html_bg_colour" in var.lower():
          href += ">>HtmlLoad index.htm"
        elif "_timage_" in var.lower() or "_snumtitle_" in var.lower() or "_tab_" in var.lower() or "_logo_" in var.lower() or "_highlight_" in var.lower():
          href += ">>panel"
        #str += "<tr valign='center'><td>%s</td><td width=80>some text</td></tr>\n" %var
        str += "<tr valign='center'><td width=%s>%s</td><td><a href='%s' target='Change %s'><zimg border='0' src='%s'></a></td></tr>\n" %(first_col_width, varName, href, varName.lower(), self.IT.make_colour_sample(val))

        ## This was an attempt to allow darker/lighter adjustment from the gui. It failed, cause the L_Var aren't actually stored in Olex
        #href_lighter = "spy.config_changed_luminosity %s -adjust=0.1" %var
        #href_darker = "spy.config_changed_luminosity %s -adjust=-0.1" %var
        #str += "<a href='%s'>lighter</a>|<a href='%s'>darker</a>" %(href_lighter, href_darker)
        #str += "<br>"
      elif "text" in var.lower() or "plane" in var.lower():
        mat = var.split("_")[1]
        ob = var.split("_")[2]
        if ob == 'text': ob = "Text"
        if ob == 'plane': ob = "Plane"
        if mat == 'infobox': mat = 'InfoBox'
        material = "%s.%s" %(mat,ob)
        href = "SetMaterial %s ChooseMaterial(GetMaterial(%s))" %(material, material)
        #href += ">>SetVar(%s, GetMaterial(%s))" %(var, material)
        href += ">>spy.config_changed_var_val %s GetMaterial(%s)" %(var,material)
        str += "<tr valign='center'><td width=%s>%s</td><td><a href='%s'>%s</a></td>\n" %(first_col_width, varName, href, val)
      elif "font_name" in var.lower():
        #href = "SetVar(%s,ChooseFont())" %(var)
        href = ">>spy.config_changed_var_val %s ChooseFont() " %(var)
        href += ">>panel"
        str += "<tr valign='center'><td width=%s>%s</td><td><a href='%s'>%s</a></td></tr>\n" %(first_col_width, varName, href, val)
#      else:
#        href = 'test'
#        str += "%s:\t<a href='%s'>%s</a><br>" %(var, href, val)
    self.str = str

  def create_config_box(self):
    wFilePath = r"%s-config.htm" %self.name
    cfgFileName = "'%s'" %self.cfgFileName
    self.str +='''
    </table>
    <br><a href="exec -o GetVar(defeditor) %s">Edit File</a>&nbsp;&nbsp<a href="html.Hide configuration-help ">Close this Window</a>
    ''' %cfgFileName
    OV.write_to_olex(wFilePath, self.str)

    if self.popout:
      boxWidth = 600
      length = len(self.str)
      boxHeight = int(length/3.2) + 100
      if boxHeight > 700:
        boxHeight = 700
      x = 10
      y = 50
      olx.Popup("%s-help"% self.name, wFilePath, "-b=tc -t='%s' -w=%i -d='echo' -h=%i -x=%i -y=%i" %(self.name, boxWidth, boxHeight, x, y))
    else:
      olx.html.Load(wFilePath)

  def config_box(self, args):
    self.str = ""
    self.name = args.get('name', None)
    self.popout = args.get('popout', False)
    self.cfgFileName = args.get('config', False)
    if not self.cfgFileName: return
    if self.popout == 'false':
      self.popout = False
    else:
      self.popout = True

    #self.config = variableFunctions.getVVD('gui')
    self.read_config_file()
    #self.getVarFromOlex()
    self.generate_config_box_text()
    self.create_config_box()


a = ConfigSkin()
OV.registerMacro(a.config_box, 'name-Name of the Config Box&;popout-True/False&;config-Name of the configuration file')
OV.registerMacro(a.config_changed_var_val, 'f')
#OV.registerMacro(a.config_changed_luminosity, 'adjust-Value to adjust the luminosity by')

