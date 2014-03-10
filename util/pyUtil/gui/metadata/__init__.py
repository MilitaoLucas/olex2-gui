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
  if not text:
    text = '<tr><td>No relevant files found</td></tr>'

  return text

conflic_d = None

def add_resolved_conflict_item_to_phil(item, value):
  l = OV.GetParam('snum.metadata.resolved_conflict_items')
  l.append(item)
  OV.SetParam('snum.metadata.resolved_conflict_items', l)
  OV.set_cif_item(item, value)
  global conflict_d
  del conflict_d[item]
  conflicts(d=conflic_d)

def make_no_conflicts_gui(resolved, some_remain=False):
  if some_remain:
    txt = "<font color='red'><b>There are unresolved conflicts</b></font>"
  else:
    txt = "<font color='green'><b>All conflicts are resolved</b></font>"
  if len(resolved) > 1:
    txt += '''
<a href='spy.SetParam(snum.metadata.resolved_conflict_items,[])>>spy.ExtractCifInfo(True,True)>>html.Update'>Reset Previously Resolved Conflicts</a>'''
  if olx.html.IsPopup('conflicts') == "true" and not some_remain:
    olx.html.EndModal('conflicts', 0)
  wFilePath_gui = r"conflicts_html_window.htm"
  OV.write_to_olex(wFilePath_gui, "<tr><td>%s</td></tr>" %txt)



def conflicts(popout='auto', d=None):
  if popout == 'true':
    popout = True
  resolved = OV.GetParam('snum.metadata.resolved_conflict_items')
  head_colour = "#005096"
  col_even = "#cdcdcd"
  col_odd = "#dedede"
  conflict_count = 0

  try:
    try:
      if not d:
        from CifInfo import ExtractCifInfo
        ci = ExtractCifInfo(run=True)
        d = ci.conflict_d
    except:
      return 0
    global conflict_d
    conflict_d = d
    go_on = False
    for conflict in d:
      if conflict == "sources": continue
      if conflict not in resolved:
        go_on = True
        break
    if not go_on:
      make_no_conflicts_gui(resolved)
      return 0

    olx.CifInfo_metadata_conflicts = None
    if d:
      number_of_files = len(d['sources'])
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
      col_w = int(70/(number_of_files+1))
      for i in xrange(number_of_files+1):
        if i == number_of_files:
          txt += '''<td width='%i%%' bgcolor='%s'><font color='white'><b>User value</b></font></td>''' %(
            col_w, head_colour)
          break
        f = os.path.basename(d['sources'][i])
        txt += '''
    <td width='%i%%' bgcolor='%s'>
      <font color='white'><b>%s</b></font>
    </td>''' %(col_w, head_colour, f)
      txt += '</tr>' #Close TR for Header Row

      for conflict in d:
        txt += '''
  <tr>'''#CONFLICT TR OPEN
        if not conflict.startswith("_"): continue
        if conflict in resolved: continue
        conflict_count += 1
        cif = str(OV.get_cif_item(conflict)).strip("'")
        txt += '''
    <td width='30%%' bgcolor='%s'><font color='white'><b>%s
    <br><a href='spy.gui.metadata.add_resolved_conflict_item_to_phil("%s", ".")'>Unapplicable (.)</a>
    &nbsp;<a href='spy.gui.metadata.add_resolved_conflict_item_to_phil("%s", "?")'> Unknown (?)</a>
    </b></font></td>''' %(head_colour, conflict, conflict, conflict)
        for s, source in enumerate(d['sources']):
          if (s%2) == 0:
            bg = col_even
          else:
            bg = col_odd

          val = d[conflict].get(source,'n/a')
          if not val:
            display = "--"
          elif cif == val:
            display = '''
            <a href='spy.gui.metadata.add_resolved_conflict_item_to_phil("%s", "%s")'>
            <font color='green'>%s</font></a>''' %(conflict, val, val)
          else:
            display = '''
            <a href='spy.gui.metadata.add_resolved_conflict_item_to_phil("%s", "%s")'>
            <font color='red'>%s</font></a>''' %(conflict, val, val)
          #TD conflict value
          txt += '''<td width='%i%%' bgcolor='%s'>%s </td>''' %(col_w, bg, display)
        # user resolved value
        display = '''
<table width="100%%" cellpadding="0" cellspacing="0"><tr><td>
  <input type="text" name="%s_edit" value="?" width="100%%"></td></tr><tr><td>
  <input type="button" value="Use" width="100%%"
   onclick="spy.gui.metadata.add_resolved_conflict_item_to_phil('%s', html.GetValue('~popup_name~.%s_edit'))">
</td></tr></table>
''' %(conflict, conflict, conflict)
        txt += '''<td width='%i%%' bgcolor='%s'>%s </td>''' %(col_w, bg, display)

        txt += '''</tr>''' #CONFLICT TR CLOSE
      txt += '''</td></tr></table>'''

  except Exception, err:
    print err
    return 0
  make_no_conflicts_gui(resolved, conflict_count > 0)
  if conflict_count == 0:
      olx.html.Update()
      return
  if number_of_files > 1:
    wFilePath = r"conflicts.htm"
    OV.write_to_olex(wFilePath, "<html><body link='yellow'>%s</body></html>" %txt)
    screen_height = int(olx.GetWindowSize('gl').split(',')[3])
    screen_width = int(olx.GetWindowSize('gl').split(',')[2])
    box_x = int(screen_width*0.1)
    box_y = int(screen_height*0.1)
    box_width = screen_width - 2*box_x
    box_height = screen_height - 2*box_y
    main_spacer = box_height - 300
    if olx.html.IsPopup('conflicts') == "false":
      olx.Popup('conflicts', '%s' %wFilePath,
       b="tcr",  t="CIF Conflicts",
       w=box_width, h=box_height, x=box_x, y=box_y, s=False)
      olx.html.ShowModal('conflicts', True)
    else:
      olx.html.Update('conflicts')
  else:
    txt += '''
<tr><td><a href='spy.gui.metadata.conflicts(true)'>Popup Conflict Window</a></td></tr>'''
    wFilePath = r"conflicts.htm"
    OV.write_to_olex(wFilePath, txt)
  return conflict_count

olex.registerFunction(sources, False, "gui.metadata")
olex.registerFunction(conflicts, False, "gui.metadata")
olex.registerFunction(add_resolved_conflict_item_to_phil, False, "gui.metadata")
