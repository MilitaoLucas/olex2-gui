from __future__ import division
import FileSystem as FS
from ArgumentParser import ArgumentParser
import glob, os
import copy
import string
import OlexVFS
#import olex_core
import time

try:
  import olx
  import olex
  datadir = olx.DataDir()
  basedir = olx.BaseDir()

except:
  pass

from olexFunctions import OlexFunctions
OV = OlexFunctions()

class MakeGuiTools(object):
  def __init__(self, tool_fun=None, tool_param=None):
    self.basedir = olx.BaseDir()
    self.gui_html_bg_colour = OV.GetParam('gui.html.bg_colour')
    self.tool_fun = tool_fun
    self.tool_param = tool_param
    tool={}
    self.language = False
    if olx.IsCurrentLanguage("German")=='true':
      self.language = "-de"
    self.line_left_col_color = OV.GetParam('gui.html.table_firstcol_colour')
    self.line_right_col_color = "#00ff00"
    self.line_left_colwidth = 8
    self.colspan=1
    self.tool_lines = []
    self.tool_line = []
    self.tool_line_txt = []
    self.tool_item = []
    self.tool_item_txt = []
    self.tool = []
    self.tool_name = ""
    self.IsFirstLine = True
    self.abort = False

  def set_language(self):
    if self.language:
      for tool in self.gui['tools']:
        display = self.gui['tools'][tool]['display%s' %self.language]
        target = self.gui['tools'][tool]['target%s' %self.language]
        if display:
          self.gui['tools'][tool]['display'] = display
        if target:	
          self.gui['tools'][tool]['target'] = target


  def get_gui_definition_single(self):
    tools={}
    tbx = {}
    tbx_li = {}
    tbx_tool = {}
    self.gui = {"tbx":tbx,"tbx_li":tbx_li,"tools":tbx_tool}


  def get_gui_definition_db(self):
    tools={}
    tbx = {}
    tbx_li = {}
    guifiles = ["tbx", "tbx_li", "tbx_tool"]

    for file in guifiles:
      filename = "%s/etc/gui/%s.csv" %(basedir, file)
      rFile = open(filename, 'r')
      res = self.read_gui_db_file(rFile)
      if file == "tbx":
        tbx = res
      elif file == "tbx_li":
        tbx_li = res
      elif file == "tbx_tool":
        tbx_tool = res
      rFile.close()
    self.gui = {"tbx":tbx,"tbx_li":tbx_li,"tools":tbx_tool}

  def read_gui_db_file(self, rFile):
    special = ["tbx_li", "href_", "box_", "tbx_tool_"]
    record_sep = "\t"
    record_strip = '"'
    d = {}
    i = 0
    fields = []
    for line in rFile:
      line = line[:-1]
      li = line.split("%s" %record_sep)
      if i == 0:
        i += 1
        for item in li:
          if item [1] == '"':
            item = item[1:-1]
          fields.append(item)
#					if item[:-1] not in special:
#						d[item_name].setdefault(item, "")
#					else:
#						d[item_name].setdefault(item[:-1], [])
      else:
        if li[0][1] == '"':
          name = li[0][1:-1]
        else:
          name = li[0]
        d.setdefault(name, {})
        for value, field  in zip(li, fields):
          if value and value[1] == '"':
            value = value[1:-1]
          if field[:-1] in special:
            d[name].setdefault(field[:-1], [])
            d[name][field[:-1]].append(value)
          else:
            d[name].setdefault(field, value)
            d[name][field] =  value
    return d


  def make_index_files(self):
    idx = {}
    idx_txt = {}
    for item in self.gui['tbx']:
      category = self.gui['tbx'][item]['category']
      idx_txt.setdefault(category, [])
      self.gui['tbx'][item].setdefault('include', 'include')

      txt = r"""
<!-- #%(include)s %(category)s-%(name)s gui\%(name)s.htm;gui\blocks\tool-off.htm;image=%(name)s;onclick=;1 -->""" %self.gui['tbx'][item]
      idx_txt[category].append(txt)

    for category in idx_txt:
      idx_file = "%s/etc/gui/blocks/index-%s-e.htm" %(basedir, category)
      rFile = open(idx_file, 'w')
      for line in idx_txt[category]:
        rFile.write(line)
      rFile.close()



  def get_gui_definition(self):
    tools={}
    tbx = {}
    tbx_li = {}

    fields = []
    items = []
    guideffile = "%s/etc/gui/guiTools.txt" %basedir
    rFile = open(guideffile, 'r')
    j = 0
    for line in rFile:
      values = []
      tbx_flag = False
      tbx_li_flag = False

      if j == 0:
        l = line[:-1]
        l = l.split('\t')
        for item in l:
          fields.append(item)
        j += 1
      else:
        l = line[:-1]
        l = l.split('\t')
        for item in l:
          values.append(string.strip(item))

        i = 0	
        for field, value in zip(fields, values):
          if i == 0 or tbx_flag:
            i += 1
            if value:
              if not tbx_flag:
                tbx_name = value
              tbx_flag = True
              tbx.setdefault(tbx_name,{})
              tbx[tbx_name].setdefault(field, value)
              tbx[tbx_name].setdefault("tbx_li",[])
              continue
            else:
              continue
          elif i == 1 or tbx_li_flag:
            #tbx_li = value
            if value:
              if not tbx_li_flag:
                tbx_li_name = value
                tbx[tbx_name]['tbx_li'].append(tbx_li_name)
                tbx_li.setdefault(tbx_li_name,{})
                tbx_li[tbx_li_name].setdefault('tools', [])
                tbx_li[tbx_li_name].setdefault('image',"")
              tbx_li_flag = True
              tbx_li[tbx_li_name].setdefault(field, value)
              tbx_li[tbx_li_name][field] = value
          elif i == 2:
            tool = value
            tools.setdefault(tool, {field:tool})
            tbx_li[tbx_li_name]['tools'].append(tool)


          else:
            tools[tool].setdefault(field, value)
            tools[tool][field] = value

          i += 1
    rFile.close()
    self.gui = {"tbx":tbx,"tbx_li":tbx_li,"tools":tools}


  def tool_tool(self):
    self.tool_name = "fools"
    self.category = "tools"
    #self.tool_lines = {'tools':[calculate_chn, calculate_isotopePattern], 'images':["toolbar-chn.png", "toolbar-chn.png"]}
    self.tool_lines = [{'tools':[calculate_chn], 'image':["toolbar-chn.png"]},
                       {'tools':[calculate_isotopePattern], 'image':["toolbar-ms.png"]}
                       ]

  def fun(self):
    if 'single' in self.tool_fun:
      # If this is called with the name of the single gui to make, it will need to get the gui definition from here
      if len(self.tool_fun.split(':')) > 1:
        a = getattr(self, "gui_def_%s" %self.tool_fun.split(':')[1])
        self.gui = a()
      # If this is called from a python internal part, the gui definition should be passed as a dictionary
      else:
        self.gui = self.tool_param

    else:
      self.get_gui_definition()
      self.make_index_files()
      self.set_language()
    i = 0
    if self.abort:
      return
    for tbx in self.gui['tbx']:
      self.tool_txt = ""
      self.tool_line_txt = []
      self.tbx = tbx
      tbx_lines = self.gui['tbx'][tbx]['tbx_li']
      for line in tbx_lines:
        if not line: continue
        self.tool_item_txt=[]
        self.tbx_li = line
        for tool in self.gui['tbx_li'][line]['tools']:
          if tool:
            self.tool = tool
            self.make_tool_item()
        self.make_tool_line()
        self.IsFirstLine = False
      self.make_tool()
      #self.write_to_olex()

  def run(self):
    if self.tool_fun == "fun" or 'single' in self.tool_fun:
      self.fun()
    else:
      self.make_tool_header()
      self.make_tool_footer()
      self.make_logo()
      self.make_Tool_Solve()

  def make_single_tool(self):
    p = self.tool_param
    self.tbx = p[0]
    self.tool_line_txt = p[1]
    tbx = {"twinning":
           {"category":'tools',
            'tbx':'name',
            'tbx_li':['test']
            }
           }
    tbx_li = {'test':
              {"category":'analysis', 
               'image':'cctbx', 
               'tbx-li':'test', 
               'tools':['testA']
               }
              }
    tools = {'testA':
             {'category':'analysis', 
              'display':"Fred waz ere", 
              'href':'fred'
              }
             }
    self.gui = {"tbx":tbx,"tbx_li":tbx_li,"tools":tools}



  def write_tool(self, name):
    #filename = r"%s/etc/gui/%s.htm" %(basedir, self.tbx)
    OlexVFS.write_to_olex(r"%s/etc/gui/%s.htm" %(basedir, self.tbx), self.tool_txt, 0)
    #wFile = open(filename, 'w')
    #wFile.write(self.tool_txt)
    #wFile.write("\n")
    #wFile.close()   

  def make_tool_header(self):
    name = r"blocks/tool-header"
    self.txt = []
    self.txt.append("<font color='#6f6f8b' size=")
    self.txt.append("<!-- #cmd $spy.gui.get_font_size() -->")
    self.txt.append(">\n<p>")
    self.write_tool(name)

  def make_tool_footer(self):
    name = r"blocks/tool-footer"
    self.txt = []
    self.txt.append("</table>")
    self.txt.append("</font>")
    self.write_tool(name)

  def make_logo(self):
    name = r"blocks/logo"
    self.txt = []
    self.txt.append('<zimg border="0" src="logo.png">')
    self.write_tool(name)

  def make_tool_item(self):
    self.col_count = 0
    separator = self.gui['tools'][self.tool].get('separator', "")
    tool_tem = self.gui['tools'][self.tool]
    tool_tem.setdefault('image_txt', "")
    tool_tem.setdefault('box1_txt', "")
    tool_tem.setdefault('box2_txt', "")
    tool_tem.setdefault('box3_txt', "")
    tool_tem.setdefault('href', "")
    tool_tem.setdefault('cmd1', "")
    tool_tem.setdefault('cmd2', "")
    tool_tem.setdefault('cmd3', "")
    tool_tem.setdefault('display',"")
    tool_tem.setdefault('target', "")
    tool_tem.setdefault('image', "")
    tool_tem.setdefault('control', "")
    tool_tem.setdefault('before', "")
    tool_tem.setdefault('after', "")
    tool_tem.setdefault('colspan', 0)
    tool_tem.setdefault('colwidth', '')
    tool_tem.setdefault('tool_begin', "")
    tool_tem.setdefault('tool_end', "")
    tool_tem.setdefault('align', "center")
    toolspan = tool_tem.get('colspan', 0)
    toolwidth = tool_tem.get('colwidth', '')
    if toolwidth:
      toolwidth = "width='%s'" %toolwidth

    if tool_tem['image']:
      tool_tem['image_txt'] = '\t\t<zimg border="0" src="toolbar-%(image)s.png"</td><td>' %tool_tem
      self.col_count += 1

    if tool_tem.get('box1', ""):
      tool_tem['box1_txt'] = '</td><td>%(box1)s<td>' %tool_tem
      self.col_count += 1
    hrefs = self.gui['tools'][self.tool].get('hrefs', "")	
    for href in hrefs:
      i = 1
      if href:
        tool_tem['href'] += "%s" % href
        if i < len(hrefs):
          tool_tem['href'] += ">>"
        i += 1
    if toolspan:
      tool_tem['tool_begin'] = "<td colspan=%s %s align='%s'>" %(toolspan, toolwidth, tool_tem['align'])
      tool_tem['tool_end'] = "</td>"
    if tool_tem['display'][-3:] == "png":
      im = tool_tem['display']
      tool_tem['display'] = '<zimg src="%s">' %im


    t = """
%(tool_begin)s		
%(image_txt)s
%(before)s
%(box1_txt)s
%(cmd1)s
<a href='%(href)s' target='%(target)s'>%(display)s%(control)s</a>
%(after)s
%(tool_end)s		
""" %(tool_tem)
    self.tool_item_txt.append((t, separator))

  def make_tool_line(self):
    tool_line = {}
    tooltxt=""
    toolspan = 1
    i = 0
    last = len(self.tool_item_txt)
    for item, separator in self.tool_item_txt:
      i += 1
      ende = False
#			toolspan = tool_tem.get('colspan',0)
#			if i == 1:
#				beg = "<td>"
#				if toolspan:
#					beg = "<td colspan='%s'>%s</td>" %(toolspan, item)
#				tooltxt += beg
#			if toolspan:
#				tooltxt += "<td colspan='%s'>%s</td>" %(tool_tem.get('colspan',1), item)
#				ende = True
      if separator == "|":
        tooltxt += "%s&nbsp;|&nbsp;" %(item)
      elif separator == "sp": 
        tooltxt += "%s&nbsp" %(item)
      elif separator == "": 
        tooltxt += "%s" %(item)
#			if i == last and not ende:
#				tooltxt += "</td>"


    tool_line.setdefault('image', self.gui['tbx_li'][self.tbx_li].get('image', ""))
    tool_line.setdefault('items', tooltxt)
    tool_line.setdefault('lcolcol', self.line_left_col_color)
    tool_line.setdefault('rcolcol', self.line_right_col_color)
    tool_line.setdefault('lcolwidth', self.line_left_colwidth)
    tool_line.setdefault('image_txt', '')
    tool_line.setdefault('header_line', '<table border="0" VALIGN="center" style="border-collapse: collapse" width="100%" cellpadding="1" cellspacing="1" bgcolor="#F3F3F3">') 
    tool_line.setdefault('footer_line', '</table>')
    if tool_line['image']:
      tool_line['image_txt'] = '\t\t<zimg border="0" src="toolbar-%(image)s.png">' %tool_line
    if self.IsFirstLine:
      tool_line['header_line'] = ""
      tool_line['footer_line'] = ""
    tool_line['header_line'] = ""
    tool_line['footer_line'] = ""

    t = """
%(header_line)s
<tr>
\t<td width="%(lcolwidth)s" bgcolor="%(lcolcol)s">
%(image_txt)s
\t</td>
\t\t%(items)s
\t</tr>
%(footer_line)s
""" %tool_line
    self.tool_line_txt.append(t)

  def make_tool(self):
    name = self.tbx
    self.tool_txt = ""
    self.tool_txt += r'<!-- #include tool-top gui\blocks\tool-top.htm;image=#image;1; -->'
    for line in self.tool_line_txt:
      self.tool_txt += line
    self.tool_txt+=r'<!-- #include tool-footer gui\blocks\tool-footer.htm;1; -->'
    #self.write_tool(name)
    OlexVFS.write_to_olex(r"%s/etc/gui/%s.htm" %(basedir, self.tbx), self.tool_txt, 0)



  def tl_reset(self):
    href = "reset"
    target = "Reset the Structure"
    display = "Reset"
    image_txt = ""
    if image:
      self.colspan += 1
      image_txt = '<zimg border="0" src="toolbar-%s.png">' %image
      self.txt_tool.append('\t\t<a href="%s" target="%%%s%%">%s</a></td><td>' %(href, target, image_txt))
    self.colspan += 1
    self.txt_tool.append('\t\t<a href="%s" target="%%%s%%">%%%s%%</a>' %(href, target, display))

  def tl_solve(self):
    href = "solve"
    target = "Solve the Structure"
    display = "Solve"

    if image:
      self.colspan += 1
      image_txt = '<zimg border="0" src="toolbar-%s.png">' %image
      self.txt_tool.append('\t\t<a href="%s" target="%%%s%%">%s</a></td><td>' %(href, target, image_txt))
    self.colspan += 1
    self.txt_tool.append('\t\t<a href="%s" target="%%%s%%">%%%s%%</a>' %(href, target, display))

  def _make_tool_line(self):
    self.txt.append('<tr>')
    self.txt.append('\t<td width="8" bgcolor="#E9E9E9">')
    self.txt.append('\t\t<zimg border="0" src="toolbar-%s.png">' %image)
    self.txt.append('\t</td>')
    self.txt.append('\t<td width="12" colspan="%i">' %self.colspan)
    for item in self.txt_tool:
      self.txt.append(item + "\n")
    self.txt.append('\t</td>')
    self.txt.append('</tr>')
    self.txt.append('</table>')




  def make_Tool_Solve(self):
    name = "solve"
    self.txt = []
    self.txt_tool = []
    self.txt.append(r'<!-- #include tool-top gui\blocks\tool-top.htm;image=#image;1; -->')

    self.colspan = 1
    self.tl_reset()
    self.tl_solve()

    self.make_tool_line()


    self.write_tool(name)
    OlexVFS.write_to_olex(r"%s/etc/gui/%s.htm" %(basedir, self.tbx), self.tool_txt, 0)
    self.txt.append(r'<!-- #include tool-footer gui\blocks\tool-footer.htm;1; -->')

  def box(self, box_d):
    box_d.setdefault('font-size',OV.GetVar(HtmlFontSizeControls))
    box_d.setdefault('label', 'Label')
    box_d.setdefault('width', 40)
    box_d.setdefault('height', 18)
    box_d.setdefault('type', 'text')
    box_d.setdefault('value', '')
    box_d.setdefault('image', '')
    box_d.setdefault('name', 'NoName')
    box_d.setdefault('items', "")
    box_d.setdefault('readonly',"")
    box_d.setdefault('label',"")
    box_d.setdefault('checked',"")
    box_d.setdefault('onchange', "")
    box_d.setdefault('onclick', "")
    box_d.setdefault('ondown', "")
    box_d.setdefault('onup', "")
    box_d.setdefault('colspan', 1)
    box_d.setdefault('oncheck', "")
    box_d.setdefault('onuncheck', "")
#		box_d.setdefault('sep_on', "<td colspan='%(colspan)s'<td>" %box_d)
#		box_d.setdefault('sep_off', "</td>")
#		if box_d['colspan'] == 0:
    box_d['sep_on'] = ""
    box_d['sep_off'] = ""

#<font size='%(font-size)s'> #this used to be first line of next block

    box = '''
%(sep_on)s
<font size='$GetVar(HtmlFontSizeControls)'>
<input 
type="%(type)s" 
label="%(label)s" 
name="%(name)s"  
width="%(width)s"  
height="%(height)s" 
value="%(value)s" 
items="%(items)s" 
onchange="%(onchange)s" 
onclick="%(onclick)s" 
oncheck="%(oncheck)s" 
onuncheck="%(onuncheck)s" 
onup="%(onup)s" 
ondown="%(ondown)s"
bgcolor="$GetVar(HtmlInputBgColour))" 
image="%(image)s"
%(readonly)s
%(checked)s
>
</font>
%(sep_off)s
'''%box_d
    return box


  def gui_def_refine(self):

    g = glob.glob(r"%s\*.hkl" %olx.FilePath())
    g.sort()
    reflection_files = ""
    try:
      a = olx.HKLSrc() 
    except:
      a = ""
    if a[:1] == "'":
      a = a[1:-1]

    if os.path.isfile(a):
      most_recent_reflection_file = a.split('\\')[-1]
      show_refl_date = time.strftime(r"%d/%b/%Y %H:%M", time.localtime(os.path.getctime(olx.HKLSrc())))
    else:
      if g:
        most_recent_reflection_file = g[0]
        show_refl_date = time.strftime(r"%d/%b/%Y %H:%M", time.localtime(os.path.getctime(g[0])))
      else:
        print "There is no reflection file or the reflection file is not accessible"
        self.abort = True
        return
    most_recent_reflection_file = ""	
    for item in g:
      reflection_files+="%s<-%s;" %(item.split("\\")[-1], item)
    try:
      weight =olx.Ins('weight')
      weight1 = olx.Ins('weight1')
    except:
      weight = r"n/a"
      weight1 = r"n/a"
    if OV.FindValue('auto_weight') == "True":
      autoweight = 'checked'
    else:
      autoweight = ''

    lsm_items = 'L.S.;CGLS;cctbx'
    #if OV.FindValue('anis') == "True":
    #	anis = 'checked'
    #else:
    #	anis = ''

    lines = ['refine_shelx', 'reflection_files', 'WGHT_scheme', 'formula', 'edit_files']

    tools_refine_shelx = ['refine_shelx', 'set_method', 'set_iterations', 'set_PLAN']
    tools_reflection_files = ['reflection_files', 'reflection_date']
    tools_WGHT_sheme = ['set_WGHT']
    tools_edit_files = ['edit_ins', 'edit_res', 'edit_lst', 'edit_cif']
    tools_formula = ['formula', 'fixunit']

    tbx = {"refine":
           {"category":'work',
            'tbx_li':lines
            }
           }

    tbx_li = {'refine_shelx':{"category":'work', 
                              'tools':tools_refine_shelx
                              },
              'reflection_files':{"category":'work', 
                                  'tools':tools_reflection_files
                                  },																		
              'WGHT_scheme':{"category":'work', 
                             'tools':tools_WGHT_sheme
                             },																		
              'edit_files':{"category":'work', 
                            'tools':tools_edit_files
                            },																		
              'formula':{"category":'work', 
                         'tools':tools_formula
                         },																		
              }

    tools = {'refine_shelx':
             {'category':'work-shelx', 
              'colspan':1, 
              'colwidth':'20%',
              'before':self.box({'type':'button',
                                 'width':50, 
                                 'name':'cmd_refine',
                                 'image':'btn-refine-on.png',
                                 'value':'%Refine%', 
                                 'onclick':'ls GetValue(set_method) GetValue(set_iterations)>>refine -1 GetValue(set_PLAN)', 
                                 }),
              },
             'set_method':
             {'category':'work-shelx', 
              'colspan':1, 
              'colwidth':'23%', 
              'before':self.box({'type':'combo',
                                 'width':50, 
                                 'name':'set_method',
                                 'value':'lsm()', 
                                 'items':lsm_items, 
                                 'label':'', 
                                 'onchange':'ls GetValue(set_method) GetValue(set_iterations)', 
                                 'readonly':'readonly'}),
              },
             'set_iterations':
             {'category':'work-shelx', 
              'colspan':1, 
              'colwidth':'33%', 
              'before':self.box({'type':'spin', 
                                 'width':42, 
                                 'name':'set_iterations',
                                 'value':'Ins(LS)', 
                                 'label':'Cycles '}),
              },
             'set_PLAN':
             {'category':'work-shelx', 
              'colspan':1, 
              'colwidth':'25%', 
              'before':self.box({'type':'spin', 
                                 'width':42, 
                                 'name':'set_PLAN',
                                 'value':'Ins(PLAN)', 
                                 'label':'Q '}),
              },

             'reflection_files':
             {'category':'work', 
              'colspan':2, 
              'before':self.box({'type':'combo', 
                                 'width':105, 
                                 'name':'Reflections', 
                                 'items':reflection_files, 
                                 'onchange':'HKLSrc(GetValue(Reflections))', 
                                 'value':'FileName(HKLSrc())', 
                                 'label':'', 
                                 'readonly':'readonly'}),
              },

             'reflection_date':
             {'category':'work', 
              'colspan':2, 
              'after':"%s" %show_refl_date,
              },

             'set_WGHT':
             {'category':'work',
              'colspan':3,
              'before':"WGHT: %s -> %s." % (weight,weight1),
              'after':self.box({'type':'checkbox', 
                                'width':12, 
                                'height':12,
                                'name':'AUTO_WGHT', 
                                'checked':autoweight,
                                'oncheck':'SetVar(auto_weight,True)',
                                'onuncheck':'SetVar(auto_weight,False)',
                                'value':''})
              },




             'Q_WGHT_CUTOFF':
             {'category':'work', 
              'colspan':1, 
              'before':self.box({'type':'spin', 
                                 'width':40, 
                                 'name':'WGHT_Q_cutoff_box', 
                                 'onchange':'SetVar(WGHT_Q_cutoff, GetValue(WGHT_Q_cutoff_box))', 
                                 'value':'GetVar(WGHT_Q_cutoff)', 
                                 'label':'Q-cut'})
              },

             'AUTO_WGHT':
             {'category':'work', 
              'colspan':1, 
              'before':self.box({'type':'checkbox', 
                                 'width':20, 
                                 'name':'AUTO_WGHT', 
                                 'checked':'checked', 
                                 'value':''})
              },

             'edit_ins':
             {'category':'work', 
              'colspan':1, 
              'display':'ins',
              'href':'edit ins',
              },

             'edit_res':
             {'category':'work', 
              'colspan':1, 
              'display':'res',
              'href':'edit res',
              },

             'edit_lst':
             {'category':'work', 
              'colspan':1, 
              'display':'lst',
              'href':'edit lst',
              },

             'edit_cif':
             {'category':'work', 
              'colspan':1, 
              'display':'cif',
              'href':'edit cif',
              },
             'formula':
             {'category':'work-shelx', 
              'colspan':3, 
              'before':self.box({'type':'text', 
                                 'width':145, 
                                 'name':'set_formula',
                                 'value':'xf.GetFormula()', 
                                 'label':'Formula '}),
              },

             'fixunit':
             {'category':'work-shelx', 
              'colspan':1, 
              'target':'Changes the formula to that of the current model',
              'href':'fixunit>>html.Update',
              'display':'Fix',
              },


             }
    return {"tbx":tbx,"tbx_li":tbx_li,"tools":tools}

  def gui_def_solve(self):
#		g = glob.glob(r"%s\*.hkl" %olx.FilePath())
#		g.sort()
#		reflection_files = ""
#		a = olx.HKLSrc() 
#		if a[:1] == "'":
#			a = a[1:-1]
#			
#		if os.path.isfile(a):
#			most_recent_reflection_file = a.split('\\')[-1]
#			show_refl_date = time.strftime(r"%d/%b/%Y %H:%M", time.localtime(os.path.getctime(olx.HKLSrc())))
#		else:
#			if g:
#				most_recent_reflection_file = g[0]
#				show_refl_date = time.strftime(r"%d/%b/%Y %H:%M", time.localtime(os.path.getctime(g[0])))
#			else:
#				print "There is no reflection file or the reflection file is not accessible"
#				self.abort = True
#				return
#		most_recent_reflection_file = ""	
#		for item in g:
#			reflection_files+="%s<-%s;" %(item.split("\\")[-1], item)

    lines = ['solve', 'space_group', 'formula']

    tbx = {"solve":
           {"category":'work',
            'tbx_li':lines
            }
           }

    tbx_li = {'solve':{"category":'work', 
                       'tools':['cmd_solve', 'solve_method', 'more_solve', 'cmd_more_solve']
                       },
              'space_group':{"category":'work', 
                             'tools':['space_group']
                             },																		
              'formula':{"category":'work', 
                         'tools':['formula','fixunit']
                         },																		
              }

    tools = {'cmd_solve':
             {'category':'work-shelx', 
              'colspan':1, 
              'colwidth':'25%', 
              'before':self.box({'type':'button',
                                 'width':50, 
                                 'image':'btn-solve-on.png',
                                 'name':'cmd_solve',
                                 'value':'%Solve%', 
                                 'onclick':'reset GetValue(set_solve_method) -c=\'GetValue(set_formula)\' -s=GetValue(set_space_group)>>solve', 
                                 }),
              },

             'solve_method':
             {'category':'work-shelx', 
              'colspan':1, 
              'colwidth':'25%', 
              'before':self.box({'type':'combo',
                                 'width':50, 
                                 'name':'set_solve_method',
                                 'value':'TREF', 
                                 'items':'TREF;PATT', 
                                 'label':'', 
                                 'onchange':'""', 
                                 'readonly':'readonly'
                                 }),
              },

             'more_solve':
             {'category':'work-shelx', 
              'colspan':1, 
              'colwidth':'30%', 
              'align':'center', 
              'after':self.box({'type':'spin',
                                'width':42, 
                                'name':'more_solve_tref',
                                'value':'5', 
                                'label':'Next '
                                }),
              },

             'cmd_more_solve':
             {'category':'work-shelx', 
              'colspan':1, 
              'colwidth':'20%', 
              'align':'center', 
              'href':'tref GetValue(more_solve_tref)', 
              'display':'Show'
              },



             'space_group':
             {'category':'work-shelx', 
              'colspan':4, 
              'before':self.box({'type':'combo',
                                 'width':65, 
                                 'name':'set_space_group',
                                 'items':'SGList()', 
                                 'label':'Please input or select Space Group ',
                                 'value':'sg(%n)',
                                 }),
              },

             'formula':
             {'category':'work-shelx', 
              'colspan':3, 
              'before':self.box({'type':'text', 
                                 'width':145, 
                                 'name':'set_formula',
                                 'value':'xf.GetFormula()', 
                                 'label':'Formula '}),
              },

             'fixunit':
             {'category':'work-shelx', 
              'colspan':1, 
              'target':'Changes the formula to that of the current model',
              'href':'fixunit>>html.Update',
              'display':'Fix',
              },


             'tidy':
             {'category':'work', 
              'colspan':1, 
              'before':self.box({'type':'checkbox', 
                                 'width':20, 
                                 'name':'tidy', 
                                 'oncheck':'echo Check', 
                                 'onuncheck':'SetVar(tidy,false)', 
                                 'checked':'checked', 
                                 'value':''})
              },


             }
    return {"tbx":tbx,"tbx_li":tbx_li,"tools":tools}


def make_program_choice_box(prg_type, prg_det, scope):
  if prg_det == 'program':
    func = 'Prgs'
  if prg_det == 'method':
    func = 'Methods'
  d = {'prg_type':prg_type, #refinement, solution
       'PRG_TYPE':prg_type.upper(), #REFINEMENT, SOLUTION
       'Prg_Type':prg_type.title(), #REFINEMENT, SOLUTION
       'prg_det':prg_det, #program, method
       'PRG_DET':prg_det.upper(), #PROGRAM, METHOD
       'Prg_Det':prg_det.title(), #PROGRAM, METHOD
       'scope':scope,
       'SCOPE':scope.upper(),
       'func':func,
       'func_arg':"",
       'func_arg2':"",
       }
  if prg_det == 'method':
    func_arg = 'spy.GetParam(%(scope)s.%(prg_type)s.program)' %d
    func_arg2 = 'GetValue(SET_%(SCOPE)s_%(PRG_TYPE)s_PROGRAM),GetValue(SET_%(SCOPE)s_%(PRG_TYPE)s_METHOD)' %d
  if prg_det == 'program':
    func_arg = 'GetValue(SET_%(SCOPE)s_%(PRG_TYPE)s_PROGRAM)'
    func_arg2 = 'GetValue(SET_%(SCOPE)s_%(PRG_TYPE)s_PROGRAM),GetValue(SET_%(SCOPE)s_%(PRG_TYPE)s_METHOD)' %d
  d['func_arg'] = func_arg
  d['func_arg2'] = func_arg2

  txt = '''
    <font size='$GetVar(HtmlFontSizeControls)'>
    <input
      type='combo'
      width='$eval(spy.GetParam(gui.htmlpanelwidth)/2 - spy.GetParam(gui.htmlpanelwidth_margin_adjust))' 
      height="$GetVar(HtmlComboHeight)"
      bgcolor="$GetVar(HtmlInputBgColour))"
      name='SET_%(SCOPE)s_%(PRG_TYPE)s_%(PRG_DET)s'
      value='$spy.GetParam(%(scope)s.%(prg_type)s.%(prg_det)s)'
      items='$spy.get%(Prg_Type)s%(func)s(%(func_arg)s)'
      label=''
      onchange="spy.Set%(Prg_Type)s%(Prg_Det)s(GetValue(SET_%(SCOPE)s_%(PRG_TYPE)s_%(PRG_DET)s))>>html.Update"
      readonly='readonly'
    >
    </font>
    ''' %d
  return txt

OV.registerFunction(make_program_choice_box)
#if __name__ == "__main__":
  #a = timage(size = 290, basedir = basedir)
  #a.run()


calculate_chn = {}
calculate_chn.setdefault('href', 'calcCHN')
calculate_chn.setdefault('display', 'Calculate CHN')
calculate_chn.setdefault('target', 'Calculate CHN Analysis for current Structure')

calculate_isotopePattern = {}
calculate_isotopePattern.setdefault('href', 'calcms')
calculate_isotopePattern.setdefault('display', 'Calculate MS')
calculate_isotopePattern.setdefault('target', 'Calculate Molecular Isotope Pattern (Mass Spectrum)')
