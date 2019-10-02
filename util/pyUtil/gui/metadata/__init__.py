import olex
import olx
import os

from olexFunctions import OlexFunctions
OV = OlexFunctions()

import gui.tools
gett = gui.tools.TemplateProvider.get_template

def sources():
  import htmlTools
  list_l = [
    {'varName':'snum.metacif.cif_od_file',
     'itemName':'CIF_OD',
     'chooseFile':{'filter':'.cif_od files|*.cif_od'}
     },
    {'varName':'snum.metacif.crystal_clear_file',
     'itemName':'Rigaku CrystalClear CIF',
     'chooseFile':{'filter':'CrystalClear.cif files|CrystalClear.cif'}
     },
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
    {'varName':'snum.metacif.sams_file',
     'itemName':'SAMS',
     'chooseFile':{'filter':'.sams files|.sams'}
     },
  ]
  x = 0
  filePath = OV.FilePath()
  for i in range(len(list_l)):
    d = list_l[x]
    #listFiles = 'snum.metacif.list_%s_files'  %'_'.join(
      #d['varName'].split('.')[-1].split('_')[:-1])

    listFiles = 'snum.metacif.%s_file'  %'_'.join(
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
        value = var
      d.setdefault('value', olx.file.RelativePath(value, filePath))

      x += 1
      file_type = '_'.join(d['varName'].split('.')[-1].split('_')[:-1])
      d.setdefault('onchange',"spy.SetParam('%s',html.GetValue('SET_%s'))>>spy.AddVariableToUserInputList('%s')>>html.Update"
                    %(d['varName'],str.upper(d['varName']).replace('.','_'),d['varName']))
      d['chooseFile'].setdefault('folder',OV.FilePath())
      d['chooseFile'].setdefault('file_type',file_type)
      d['chooseFile'].setdefault('caption',d['itemName'])

      if "cif_od" in listFiles.lower() or "crystal_clear" in listFiles.lower():
        if os.path.exists(filePath):
          del list_l[1:]
          break

    else:
      del list_l[list_l.index(d)]


  text = htmlTools.makeHtmlTable(list_l)
  if not text:
    text = '<tr><td>No relevant files found</td></tr>'

  return text

conflic_d = None

def add_resolved_conflict_item_to_phil(item, value):
  l = OV.GetParam('snum.metadata.resolved_conflict_items')
  l.append(item)
  OV.SetParam('snum.metadata.resolved_conflict_items', l)
  OV.set_cif_item(item, value.replace("<br>", "\n"))
  global conflict_d
  del conflict_d[item]
  conflicts(d=conflict_d)

def resolve_all(idx):
  global conflict_d
  idx = int(idx)
  key = conflict_d['sources'][idx]
  l = OV.GetParam('snum.metadata.resolved_conflict_items')
  for i,v in conflict_d.iteritems():
    if not i.startswith('_'): continue
    l.append(i)
    OV.set_cif_item(i, v[key])
  OV.SetParam('snum.metadata.resolved_conflict_items', l)
  print("All conflicts are resolved")
  conflict_d = None
  make_no_conflicts_gui(l, False)

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

  gui_dd = {'head_colour':head_colour,
        'col_even':col_even,
        'col_odd':"#dedede",
        'action_colour':OV.GetParam('gui.action_colour').hexadecimal,
        'gui_red':OV.GetParam('gui.red').hexadecimal,
        }

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

      ## CONFLICTS TOP SECTION ###########################
      gui_d = {'colspan':colspan}
      gui_d.update(gui_dd)
      txt += gett('conflicts_top_section')%gui_d
      ## END TOP SECTION #################################

      txt += gett('conflicts_header_row_start')

      col_w = int(70/(number_of_files+1))
      for i in xrange(number_of_files+1):
        if i == number_of_files:
          txt += gett('conflicts_user_value_header')%gui_d
          break
        f = os.path.basename(d['sources'][i])

        ## HEADER ROW FILES ##################################
        gui_d = {'col_w':col_w, 'no_of_file':i, 'basename': f}
        gui_d.update(gui_dd)
        txt += gett('conflicts_header_row_files')%gui_d
        ######################################################

        #%(col_w, head_colour, f, i, i)
      txt += '</tr>' #Close TR for Header Row

      for conflict in d:
        ######################################
        gui_d = {'conflict':conflict}
        gui_d.update(gui_dd)
        txt += "<tr>" #CONFLICT TR OPEN
        if not conflict.startswith("_"): continue
        if conflict in resolved: continue
        conflict_count += 1
        cif = str(OV.get_cif_item(conflict)).strip("'")
        txt += gett('conflicts_conflict')%gui_d

        for s, source in enumerate(d['sources']):
          if (s%2) == 0:
            bg = col_even
          else:
            bg = col_odd

          val = d[conflict].get(source,'n/a').replace("\n", "<br>")
          colour = ""
          if not val:
            display = "--"
          elif cif == val:
            colour = OV.GetParam('gui.green').hexadecimal
          else:
            colour = OV.GetParam('gui.red').hexadecimal

          ###########################################
          gui_d = {'conflict':conflict,'val':val, 'colour':colour, 'bg':bg, 'col_w':col_w}
          gui_d.update(gui_dd)

          display = gett('conflicts_display_1')%gui_d
          ############################################
          gui_d['display'] = display

          #TD conflict value
          txt += gett('conflicts_conflict_value')%gui_d
        # user resolved value

        ################################################################
        gui_d = {'conflict':conflict,'val':val, 'colour':colour, 'bg':bg, 'col_w':col_w}
        gui_d.update(gui_dd)
        display = gett('conflicts_display_2')%gui_d
        ##################################################################
        gui_d['display'] = display
        txt += gett('conflicts_conflict_value')%gui_d
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
    box_x = int(screen_width*0.01)
    box_y = int(screen_height*0.08)
    box_width = screen_width - box_x
    box_height = screen_height - box_y
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
olex.registerFunction(resolve_all, False, "gui.metadata")

