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

def conflicts():
  added_count = 0
  resolved = OV.GetParam('snum.metadata.resolved_conflict_items')
  try:
    if not olx.CifInfo_metadata_conflicts:
      from CifInfo import ExtractCifInfo
      ExtractCifInfo()
    d = olx.CifInfo_metadata_conflicts.conflict_d
    olx.CifInfo_metadata_conflicts = None
    if d:
      added_count = 0
      txt = '''
  <table cellpadding='0' collspacing='0' width='100%%'>
    <tr><td colspan='2'><font color='red'><b>There is conflicting information!</b></font></td></tr>
      '''
      for conflict in d:
        if not conflict.startswith("_"): continue
        if conflict in resolved: continue

        cif = OV.get_cif_item(conflict)
        val = d[conflict]['val']
        if not val:
          val = 'n/a'
        val = val.strip("'")
        conflict_val = d[conflict]['conflict_val']
        if not conflict_val:
          conflict_val = 'n/a'
        conflict_val = conflict_val.strip("'")
        v_source = os.path.split(d[conflict]['val_source'])[1]
        c_source = os.path.split(d[conflict]['conflict_source'])[1]
        added_count += 1
        link2 = make_conflict_link(conflict, val, v_source, cif)
        link3 = make_conflict_link(conflict, conflict_val, c_source, cif)
        if cif == conflict_val:
          link2, link3 = link3, link2
        cif_val = '.'
        if cif != val and cif != conflict_val:
          cif_val = '''
<a href='spy.gui.metadata.add_resolved_conflict_item_to_phil(%s)
>>html.Update'><font color='green'>%s</font></a>''' %(conflict, cif)

        txt += '''
<tr>
  <td width='50%%'>
    <table border="0" VALIGN='center' style="border-collapse: collapse" width="100%%" cellpadding="1" cellspacing="1" bgcolor="$GetVar(HtmlTableRowBgColour)">

    <tr><td>
    <b>%s</b>
    </td></tr>
    <tr><td align='center'>%s</td></tr></table>
  <td width='25%%'>
  %s
  </td>
  <td width='25%%'>
  %s
  </td>
</tr>
  ''' %(conflict,
        cif_val,
        link2,
        link3,
        )
      txt += "</table>"
    else:
      txt = "<font color='green'><b>No conflicts in the meta-data or all conflicts resolved</b></font><a href='spy.SetParam('snum.metadata.resolved_conflict_items','')"

  except:
    return "Not Initialised or Something Bad has happened."
  if added_count == 0:
    l = []
    txt = '''
<font color='green'><b>No conflicts in the meta-data</b></font>'''
    if len(resolved) > 1:
      txt += '''
<a href='spy.SetParam(snum.metadata.resolved_conflict_items,[])>>spy.ExtractCifInfo()>>html.Update'>Reset Previous Conflicts</a>'''

  return txt

olex.registerFunction(sources, False, "gui.metadata")
olex.registerFunction(conflicts, False, "gui.metadata")
olex.registerFunction(set_cif_item, False, "gui.metadata")
olex.registerFunction(add_resolved_conflict_item_to_phil, False, "gui.metadata")
