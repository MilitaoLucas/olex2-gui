import olex
import olx
import os

from olexFunctions import OlexFunctions
OV = OlexFunctions()


def sources():
  import htmlTools
  list = [
    {'varName':'snum.metacif.abs_file',
     'itemName':'.abs',
     'chooseFile':{'filter':'.abs files|*.abs'}
     },
    {'varName':'snum.metacif.pcf_file',
     'itemName':'.pcf',
     'chooseFile':{'filter':'.pcf files|*.pcf'}
     },
    {'varName':'snum.metacif.p4p_file',
     'itemName':'.p4p',
     'chooseFile':{'filter':'.p4p files|*.p4p'}
     },
    {'varName':'snum.metacif.smart_file',
     'itemName':'Bruker SMART',
     'chooseFile':{'filter':'.ini files|*.ini'}
     },
    {'varName':'snum.metacif.saint_file',
     'itemName':'Bruker SAINT',
     'chooseFile':{'filter':'.ini files|*.ini'}
     },
    {'varName':'snum.metacif.frames_file',
     'itemName':'Bruker %Frame%',
     'chooseFile':{'filter':'All files(*.*)|*.*'}
     },
    {'varName':'snum.metacif.integ_file',
     'itemName':'%Bruker Integration%',
     'chooseFile':{'filter':'._ls files|*._ls'}
     },
    {'varName':'snum.metacif.cad4_file',
     'itemName':'Nonius cad4',
     'chooseFile':{'filter':'.dat files|*.dat'}
     },
    {'varName':'snum.metacif.cif_od_file',
     'itemName':'Agilent CIF',
     'chooseFile':{'filter':'.cif_od files|*.cif_od'}
     },
    {'varName':'snum.metacif.crystal_clear_file',
     'itemName':'Rigaku CrystalClear CIF',
     'chooseFile':{'filter':'CrystalClear.cif files|CrystalClear.cif'}
     },
    {'varName':'snum.metacif.sams_file',
     'itemName':'SAMS',
     'chooseFile':{'filter':'.sams files|.sams'}
     },
  ]
  text = ''

  x = 0
  filePath = OV.FilePath()
  for i in range(len(list)):
    d = list[x]
    listFiles = 'snum.metacif.list_%s_files'  %'_'.join(
      d['varName'].split('.')[-1].split('_')[:-1])
    var = OV.GetParam(listFiles)
    if var is not None:
      if ';' in var[-1] > 1:
        files = ';'.join([olx.file.RelativePath(i, filePath) for i in var[-1].split(';')])
        d.setdefault('items', files)
        value_name = 'snum.metacif.%s_file'  %'_'.join(
          d['varName'].split('.')[-1].split('_')[:-1])
        value = OV.GetParam(value_name)
      else:
        value = var[-1]
      d.setdefault('value', olx.file.RelativePath(value, filePath))

      x += 1
      file_type = '_'.join(d['varName'].split('.')[-1].split('_')[:-1])
      d.setdefault('onchange',"spy.SetParam('%s',html.GetValue('SET_%s'))>>spy.AddVariableToUserInputList('%s')>>html.Update"
                    %(d['varName'],str.upper(d['varName']).replace('.','_'),d['varName']))
      d['chooseFile'].setdefault('folder',OV.FilePath())
      d['chooseFile'].setdefault('file_type',file_type)
      d['chooseFile'].setdefault('caption',d['itemName'])
    else:
      del list[list.index(d)]

  text = htmlTools.makeHtmlTable(list)
  if text == '':
    retstr = 'No relevant files found'
  else:
    retstr = text

  return retstr

def add_resolved_conflict_item_to_phil(item):
  l = OV.GetParam('snum.metadata.resolved_conflict_items')
  l.append(item)
  OV.SetParam('snum.metadata.resolved_conflict_items', l)
  conflicts()

def set_cif_item(key, value):
  OV.set_cif_item(key, '%s' %value)

def make_conflict_link(item, val, src, cif_value):
  if val == cif_value:
    return '''
<table border="0" VALIGN='center' style="border-collapse: collapse" width="100%%" cellpadding="1" cellspacing="1" bgcolor="$GetVar('HtmlTableRowBgColour')">
<tr><td><b>%s</b></td></tr><tr><td>
<a href='
spy.gui.metadata.add_resolved_conflict_item_to_phil(%s)
>>html.Update'><font color='green'>%s</font></a></td></tr></table>
'''%(src, item, val)
  else:
    return '''
<table border="0" VALIGN='center' style="border-collapse: collapse" width="100%%" cellpadding="1" cellspacing="1" bgcolor="$GetVar('HtmlTableRowBgColour')">
<tr><td><b>%s</b></td></tr><tr><td>
<a href=
"spy.gui.metadata.set_cif_item('%s','%s')
>>spy.MergeCif('False')
>>spy.gui.metadata.add_resolved_conflict_item_to_phil('%s')
>>html.Update">%s</a></td></tr></table>
'''%(src, item, val, item, val)


def make_no_conflicts_gui(resolved):
      txt = '''
  <font color='green'><b>No conflicts in the meta-data</b></font>'''
      if len(resolved) > 1:
        txt += '''
  <a href='spy.SetParam(snum.metadata.resolved_conflict_items,[])>>spy.ExtractCifInfo()>>html.Update'>Reset Previously Resolved Conflicts</a>'''
      if olx.html.IsPopup('conflicts') == "true":
        olx.html.Hide('conflicts')
      wFilePath_gui = r"conflicts_html_window.htm"
      OV.write_to_olex(wFilePath_gui, txt)
  

def conflicts(popout='auto', d=None):
  if popout == 'true':
    popout = True
  added_count = 0
  resolved = OV.GetParam('snum.metadata.resolved_conflict_items')
  head_colour = "#005096"
  col_even = "#cdcdcd"
  col_odd = "#dedede"

  try:
    if not olx.CifInfo_metadata_conflicts:
      from CifInfo import ExtractCifInfo
      ExtractCifInfo()
    try:
      if not d:
        d = olx.CifInfo_metadata_conflicts.conflict_d
    except:
      return "strange"
    go_on = False
    for conflict in d:
      if conflict == "sources": continue
      if conflict not in resolved:
        go_on = True
    if not go_on:
      make_no_conflicts_gui(resolved)
      return
        
    olx.CifInfo_metadata_conflicts = None
    if d:
      number_of_files = len(d['sources'])
      added_count = 0
      txt = "<table width='100%'><tr><td>" #START: encase everything in a table
      colspan = number_of_files + 1
      txt += '''
<table cellpadding='1' collspacing='1' width='100%%'>
  <tr>
    <td colspan='%s'><font size='4' color='red'><b>There is conflicting information!</b></font></td>
  </tr>
  <tr>
    <td colspan='%s'><font size='2'><b>Some of your files contain conflicting information regarding information that should go into your cif file. Please select the correct values by clicking on the links below.</b></font>
    </td>
  </tr>
      ''' %(colspan,colspan)#TOP section
      
      txt += '''
  
  <tr>
    <td width='30%%'><font color='white'><b></b></font>
    </td>''' #TR for Header Row
      for i in xrange(number_of_files):
        f = os.path.basename(d['sources'][i])
        txt += '''
    <td width='%i%%' bgcolor='%s'>
      <font color='white'><b>%s</b></font>
    </td>''' %(int(70/number_of_files), head_colour, f)
      txt += '''
  </tr>''' #Close TR for Header Row

      for conflict in d:
        added_count += 1
        txt += '''
  <tr>'''#CONFLICT TR OPEN
        if not conflict.startswith("_"): continue
        if conflict in resolved: continue
        cif = str(OV.get_cif_item(conflict)).strip("'")
        txt += '''
    <td width='30%%' bgcolor='%s'><font color='white'><b>%s</b></font></td>''' %(head_colour, conflict)
        s = 0
        for source in d['sources']:
          s += 1
          if s%2==0:
            bg = col_even
          else:
            bg = col_odd
          
          val = d[conflict].get(source,'n/a')
          if not val:
            display = "--"
          elif cif == val:
            display = '''
            <a href='spy.gui.metadata.add_resolved_conflict_item_to_phil(%s)
            >>html.Update'><font color='green'>%s</font></a>''' %(conflict, val)
          else:
            display = '''
            <a href='spy.gui.metadata.add_resolved_conflict_item_to_phil(%s)
            >>html.Update'><font color='red'>%s</font></a>''' %(conflict, val)
          txt += '''
    <td width='%i%%' bgcolor='%s'>%s
    </td>''' %(int(70/number_of_files), bg, display) #TD conflict value
        txt += '''
  </tr>''' #CONFLICT TR CLOSE
      txt += '''
  </td></tr></table>'''

    else:
      make_no_conflicts_gui(resolved)
      
      #txt = "<font color='green'><b>No conflicts in the meta-data or all conflicts resolved</b></font><a href='spy.SetParam('snum.metadata.resolved_conflict_items','')"

  except Exception, err:
    print err
    return "Not Initialised or Something Bad has happened."

  if len(resolved) > 1:
    make_no_conflicts_gui(resolved)
    
    #txt += '''
#<tr><td><a href='spy.SetParam(snum.metadata.resolved_conflict_items,[])>>spy.ExtractCifInfo()>>html.Update'>Reset Previously Resolved Conflicts</a></td></tr>'''
  
  if number_of_files > 1:
    wFilePath = r"conflicts.htm"
    OV.write_to_olex(wFilePath, txt + "</table>")
    
    #t = '''
#<tr><td><a href='spy.gui.metadata.conflicts(true)'>Popup Conflict Window</a></td></tr>'''
    #wFilePath_gui = r"conflicts_html_window.htm"
    #OV.write_to_olex(wFilePath_gui, t)
    
    screen_height = int(olx.GetWindowSize('gl').split(',')[3])
    screen_width = int(olx.GetWindowSize('gl').split(',')[2])
    box_x = int(screen_width*0.1)
    box_y = int(screen_height*0.1)
    box_width = screen_width - 2*box_x
    box_height = screen_height - 2*box_y
    main_spacer = box_height - 300
    if olx.html.IsPopup('conflicts') == "false":
      olx.Popup('conflicts', '%s' %wFilePath, "-b=tcr -t='CIF Conflicts' -w=%i -h=%i -x=%i -y=%i" %(box_width, box_height, box_x, box_y))
    else:
      olx.Popup('conflicts', '%s' %wFilePath)
  else:
    txt += '''
<tr><td><a href='spy.gui.metadata.conflicts(true)'>Popup Conflict Window</a></td></tr>'''
    wFilePath = r"conflicts.htm"
    OV.write_to_olex(wFilePath, txt)
    return txt

olex.registerFunction(sources, False, "gui.metadata")
olex.registerFunction(conflicts, False, "gui.metadata")
olex.registerFunction(set_cif_item, False, "gui.metadata")
olex.registerFunction(add_resolved_conflict_item_to_phil, False, "gui.metadata")
