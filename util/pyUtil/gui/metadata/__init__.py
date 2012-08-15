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
  for i in range(len(list)):
    d = list[x]
    listFiles = 'snum.metacif.list_%s_files'  %'_'.join(
      d['varName'].split('.')[-1].split('_')[:-1])
    var = OV.GetParam(listFiles)
    if var is not None:
      if ';' in var:
        d.setdefault('items', 'spy.GetParam(%s)' %listFiles)
      x += 1
      file_type = '_'.join(d['varName'].split('.')[-1].split('_')[:-1])
      d.setdefault('onchange',"spy.SetParam(%s,'html.GetValue(SET_%s)')>>spy.AddVariableToUserInputList(%s)" %(d['varName'],str.upper(d['varName']).replace('.','_'),d['varName']))
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

def set_cif_item(key, value):
  OV.set_cif_item(key, '%s' %value)

def make_conflict_link(item, val, src, cif_value):
  if val == cif_value:
    return "<b>%s</b>: <font color='green'><b>%s</b></font>" %(src, val)
  else:
    return '''<b>%s</b>:
    <a href='spy.gui.metadata.set_cif_item(%s,"%s")>>spy.MergeCif(False)>>html.Update'>%s</a>
'''%(src, item, val, val)

def conflicts():
  try:
    d = olx.CifInfo_metadata_conflicts.conflict_d
    if d:
      added_count = 0
      txt = '''
  <table cellpadding='0' collspacing='0' width='100%%'>
    <tr><td colspan='2'><font color='red'><b>There is conflicting information!</b></font></td></tr>
      '''

      for conflict in d:
        if not conflict.startswith("_"): continue
        cif = OV.get_cif_item(conflict)
        val = d[conflict]['val']
        if not val:
          val = 'n/a'
        val = val.strip("'")
        conflict_val = d[conflict]['conflict_val']
        if not conflict_val:
          conflict_val = 'n/a'
        conflict_val = conflict_val.strip("'")
        v_source = os.path.splitext(d[conflict]['val_source'])[1].lstrip('.').upper()
        c_source = os.path.splitext(d[conflict]['conflict_source'])[1].lstrip('.').upper()
        added_count += 1
        link2 = make_conflict_link(conflict, val, v_source, cif)
        link3 = make_conflict_link(conflict, conflict_val, c_source, cif)
        txt += '''
<tr><td width='50%%'><b>%s</b></td><td><font color='green'><b>%s</b></font></td></tr>
<tr><td colspan='2'>
  <table width='100%%' cellpadding='0' collspacing='0'>
   <tr><td width='25%%'>&nbsp;&nbsp;</td><td>%s</td><td>%s</td></tr>
  </table>
</td></tr>
  ''' %(conflict,
        cif,
        link2,
        link3,
        )
      txt += "</table>"
    else:
      txt = "<font color='green'><b>No conflicts in the meta-data</b></font>"

  except:
    return "Not Initialised or Something Bad has happened."
  if added_count == 0:
    txt = "<font color='green'><b>No conflicts in the meta-data</b></font>"
  return txt

olex.registerFunction(sources, False, "gui.metadata")
olex.registerFunction(conflicts, False, "gui.metadata")
olex.registerFunction(set_cif_item, False, "gui.metadata")
