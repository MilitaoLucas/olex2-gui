import olx
import olex
import io
import os
from olexFunctions import OlexFunctions
OV = OlexFunctions()
from ImageTools import ImageTools
IT = ImageTools()
import re
import sys
green = OV.GetParam('gui.green')
red = OV.GetParam('gui.red')
import gui
debug = bool(OV.GetParam("olex2.debug", False))
olx.SetVar('show_restraints_table', "false")
global cache_restraint_table
cache_restraint_table = ""
global filtered_off
filtered_off = 0
olx.SetVar('restraint_filter', 2.0)


def append_row(rows, observed, target, delta, sigma, restraint, atoms):
  global filtered_off
  filter_val = float(olx.GetVar('restraint_filter'))
  dos = round(delta / sigma, 1)
  if abs(dos) >= filter_val:
    rows.append([observed, target, round(delta, 3), round(sigma, 3), dos, restraint, atoms])
  else:
    filtered_off += 1
  return rows


def parse_bond_restraints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split(":")[1])
  for i in range(number_restraints):
    atom1 = text[2 + 4 * i].split()[1]
    atom2 = text[3 + 4 * i].strip()
    line = text[5 + 4 * i].split()
    target = float(line[0])
    observed = float(line[1])
    delta = float(line[2])
    sigma = float(line[3])
    restraint = "DFIX"
    atoms = "%s %s" % (atom1, atom2)
    rows = append_row(rows, observed, target, delta, sigma, restraint, atoms)
  return rows


def parse_chirality_restraints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split(":")[1])
  for i in range(number_restraints):
    atoms = find_bits(string, "chirality", "both_signs").strip().split()
    info = find_bits(string, "residual", "\n\n").strip().split()
#    rows.append([observed, target, delta, sigma, "CHIV", "%s %s" % (atom1, atom2)])
  return rows


def parse_bond_angle_restraints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split(":")[1])
  for i in range(number_restraints):
    atom1 = text[2 + 5 * i].split()[1]
    atom2 = text[3 + 5 * i].strip()
    atom3 = text[4 + 5 * i].strip()
    line = text[6 + 5 * i].split()
    target = float(line[0])
    observed = float(line[1])
    delta = float(line[2])
    sigma = float(line[3])
    restraint = "ANGLE"
    atoms = "%s %s %s" % (atom1, atom2, atom3)
    rows = append_row(rows, observed, target, delta, sigma, restraint, atoms)
  return rows


def parse_adp_similarity_restraints(string):
  rows = []
  if not string:
    print("parse_ADP_similarity_restraints didn't receive a string. This is strange")
    return rows
  text = string.split('\n')
  number_restraints = int(text[0].split(":")[1])
  for i in range(number_restraints):
    line = text[2 + 2 * i]
    atoms = [line.split()[1]]
    count = 1
    line = text[2 + 2 * i + count]
    while "delta" not in line:
      atoms.append(line.strip())
      count += 1
      line = text[2 + 2 * i + count]
    atoms_string = ""
    for l in range(len(atoms)):
      atoms_string += " %s" % atoms[l]
    for j in range(6):
      line = text[5 + i * 6 + j].split()
      name = line[0]
      target = "-"
      observed = "-"
      delta = float(line[1])
      sigma = float(line[2])
      restraint = "RIGU"
      atoms = "%s" % (atoms_string)
      rows = append_row(rows, observed, target, delta, sigma, restraint, atoms)
  return rows


def parse_isotropic_adp_restraints(string):
  rows = []
  if not string:
    print("parse_ADP_similarity_restraints didn't receive a string. This is strange")
    return rows
  text = string.split('\n')
  number_restraints = int(text[0].split(":")[1])
  for i in range(number_restraints):
    line = text[2 + i * 8]
    atoms = [line.split()[1]]
    count = 1
    line = text[2 + i * 8 + count]
    while "delta" not in line:
      atoms.append(line.strip())
      count += 1
      line = text[2 + i + count]
    atoms_string = ""
    for l in range(len(atoms)):
      atoms_string += " %s" % atoms[l]
    line = text[4 + i * 8].split()
#      line = text[5 + i * 6 + j].split()
    name = line[0]
    target = "-"
    observed = "-"
    delta = float(line[1])
    sigma = float(line[2])
    restraint = "ISOR %s" % (name)
    atoms = "%s" % (atoms_string)
    rows = append_row(rows, observed, target, delta, sigma, restraint, atoms)
    i += 1
  return rows


def parse_bond_similarity_restraints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split(":")[1])
  line = text[3]
  for i in range(3, len(text)):
    if "delta" in text[i]:
      continue
    line = text[i].split()
    add = 0
    if line[0] == "bond":
      atoms = line[1].split('-')
      add = 1
    else:
      atoms = line[0].split('-')
    atoms_string = " ".join(atoms)
    delta = float(line[1 + add])
    sigma = float(line[2 + add])
    observed = '-'
    target = '-'
    restraint = "SADI"
    atoms = "%s" % (atoms_string)
    rows = append_row(rows, observed, target, delta, sigma, restraint, atoms)
  return rows


def parse_rigu_bond_restraints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split(":")[1])
  target = "-"
  observed = "-"
  for i in range(number_restraints):
    atom1 = text[2 + 6 * i].split()[1]
    atom2 = text[3 + 6 * i].strip()
    for j in range(3):
      line = text[j + 5 + 6 * i].split()
      delta = float(line[0])
      sigma = float(line[1])
      restraint = "RIGU %s" % j
      atoms = "%s %s" % (atom1, atom2)
      rows = append_row(rows, observed, target, delta, sigma, restraint, atoms)
  return rows


def mangle_fdb_data(tabledata):
  new_l = []
  for l in tabledata:
    _ = l[-1:][0].split()
    new_l.append(l[0:-1] + [_[0]] + [" ".join(_[1:])])
  return new_l

def make_fvar_table(*kwds):
  fvar_table: str = ""
  header = """
<tr ALIGN='left' NAME='SNUM_REFINEMENT_NSFF' width='100%'>
<!-- #include tool-help-first-column gui\blocks\tool-help-first-column.htm;help_ext=NoSpherA2_Options_1;1; -->

<!-- #include row_table_on gui\blocks\row_table_on.htm;1; -->"""
  footer = """<!-- #include row_table_off gui\blocks\row_table_off.htm;1; -->"""
  filling = """<td align="left"><b>FVAR:</b></td>"""
  fvars = []
  try:
    for i in range(20):
      fvars.append(olx.xf.rm.FVar(i))
  except:
    pass
  for i, var in enumerate(fvars):
    filling += """<td align="center"><b>""" + "%d:</b> %s </td>" % (i + 1, var)
  
  filling += "</b></td>"
  fvar_table = header + filling + footer
  return fvar_table

OV.registerFunction(make_fvar_table, False, "gui.restraints")

def make_restraints_table(*kwds):
  global cache_restraint_table
  global filtered_off
  filtered_off = 0
  filter_message = "No Restraints are shown"
  if olx.GetVar('show_restraints_table').lower() == 'false':
    top_line = gui.tools.TemplateProvider.get_template('restraints_top', force=debug) % {'filtered_off': filter_message}
    return top_line
  else:
    top_line = gui.tools.TemplateProvider.get_template('restraints_top', force=debug) % {'filtered_off': filter_message}
    retVal = top_line
    if cache_restraint_table and olx.GetVar('restraint_filter_changed','Flase') == "False":
      retVal = cache_restraint_table
      cache_restraint_table = ""
      return retVal

  software = OV.GetParam("snum.refinement.program")
  tabledata = []
  if "xl" in software.lower():
    import FragmentDB
    Ref = FragmentDB.refine_model_tasks.Refmod()
    lstfile = os.path.abspath(OV.FilePath() + os.path.sep + OV.FileName() + '.lst')
    if not os.path.exists(lstfile):
      print(".lst File not found!")
      return
    tabledata = mangle_fdb_data(Ref.fileparser(lstfile))
  else:
    from cctbx_olex_adapter import OlexCctbxAdapter
    cctbx_adaptor = OlexCctbxAdapter()
    temp = io.StringIO()
    cctbx_adaptor.restraints_manager().show_sorted(cctbx_adaptor._xray_structure, f=temp)
    output = temp.getvalue()

    restraints_l = ["Bond restraints",
                    "Bond similarity restraints",
                    "Bond angle restraints",
                    "ADP similarity restraints",
                    "Rigu bond restraints",
                    "Isotropic ADP restraints",
                    "Chirality restraints",
                    ]

    for restraint in restraints_l:
      if restraint in output:
        try:
          s = find_bits(output, restraint, "\n\n")
          bond_rows = globals()["parse_" + restraint.lower().replace(" ", "_")](s)
          tabledata += bond_rows
        except Exception as err:
          sys.stderr.formatExceptionInfo()
          _ = restraint.split()
          tabledata += [[0, 0, 0, 0, _[0].upper() + "_" + _[1].lower() + "_" + 'err', ""]]

  filter_message = "<b>%i</b> Restraints have been filtered" % filtered_off
  top_line = gui.tools.TemplateProvider.get_template('restraints_top', force=debug) % {'filtered_off': filter_message}
  cache_restraint_table = top_line + h_t.table_maker(tabledata)
  return cache_restraint_table


OV.registerFunction(make_restraints_table, False, "gui.restraints")


def find_bits(text, front, back):
  m = re.findall(r"%s(.*?)%s" % (front, back), text, re.DOTALL)
  return m[0]


class html_Table(object):
  """
  html table generator
  """

  def __init__(self):
    try:
      # more than two colors here are too crystmas treelike:
      self.grade_1_colour = OV.GetParam('gui.skin.diagnostics.colour_grade1')
      #self.grade_1_colour = self.rgb2hex(IT.adjust_colour(grade_1_colour, luminosity=1.8))
      
      self.grade_2_colour = OV.GetParam('gui.skin.diagnostics.colour_grade2')
      #self.grade_2_colour = self.rgb2hex(IT.adjust_colour(grade_2_colour, luminosity=1.8))
      
      self.grade_3_colour = OV.GetParam('gui.skin.diagnostics.colour_grade3')
      #self.grade_3_colour = self.rgb2hex(IT.adjust_colour(grade_3_colour, luminosity=1.8))
      
      self.grade_4_colour = OV.GetParam('gui.skin.diagnostics.colour_grade4')
      #self.grade_4_colour = self.rgb2hex(IT.adjust_colour(grade_4_colour, luminosity=1.8))
    except(ImportError, NameError):
      self.grade_2_colour = '#FFD100'
      self.grade_4_colour = '#FF1030'

  def rgb2hex(self, rgb):
    """
    return the hexadecimal string representation of an rgb colour
    """
    return '#%02x%02x%02x' % rgb

  def table_maker(self, tabledata=None):
    """
    builds a html table out of a datalist from the final
    cycle summary of a shelxl list file.
    """
    if tabledata is None:
      tabledata = []
    table = []
    for line in tabledata:
      table.append(self.row(line))
    footer = ""
    empty_data = """
    <b>There may be no restraints, they have been filtered or can not be evaluated.</b>
    """
    html = r"""
    <table width="100%" border="0" cellpadding="0" cellspacing="3">
      <tr>
         <td width='12%' align='left'><b>Observed </b></td>
         <td width='12%'align='left'><b>Target   </b></td>
         <td width='10%'align='center'><b>Dev    </b></td>
         <td width='10%'align='center'><b>Sig    </b></td>
         <td width='10%'align='center'><b>D/S    </b></td>
         <td width='10%'align='left'><b>Restr. </b></td>
         <td align='left'><b>Atoms </b></td>
      </tr>

      {0}
    </table>
      {1}
      """.format('\n'.join(table), footer)
    if not table:
      return empty_data
    return html

  def row(self, rowdata):
    """
    creates a table row for the restraints list.
    :type rowdata: list
    """
    restraints = ["SADI", "DFIX", "RIGU", "ISOR", "ANGLE"]
    td = []
    error = False
    bgcolor = ''
    try:
      #if abs(float(rowdata[4])) > 2.5 * float(rowdata[3]):
        #bgcolor = r"""bgcolor='{}'""".format(self.grade_2_colour)
      #if abs(float(rowdata[4])) > 3.5 * float(rowdata[3]):
        #bgcolor = r"""bgcolor='{}'""".format(self.grade_4_colour)

      _ = abs(float(rowdata[4]))
      if _ > 2.5:
        bgcolor = r"""bgcolor='{}'""".format(self.grade_4_colour)
      elif _ > 1.5:
        bgcolor = r"""bgcolor='{}'""".format(self.grade_3_colour)
      elif _ > 0.5:
        bgcolor = r"""bgcolor='{}'""".format(self.grade_2_colour)
      else:
        bgcolor = r"""bgcolor='{}'""".format(self.grade_1_colour)
    except ValueError:
      print("Unknown restraint occured.")
    for num, item in enumerate(rowdata):
      try:
        # align right for numbers:
        float(item)
        if num < 2:
          # do not colorize the first two columns:
          td.append(r"""<td align='left'> {} </td>""".format(item))
        else:
          if num == 4:
            td.append(r"""<td align='center' {0} ><b><font color='white'> {1} </font></b></td>""".format(bgcolor, item))
          else:
            td.append(r"""<td align='center' {0} ><b><font color='white'> {1:.3f} </font></b></td>""".format(bgcolor, item))
      except:
        if item.startswith('-'):
          # only a minus sign
          td.append(r"""<td align='left'> {} </td>""".format(item))
        else:
          if num < 6:
            if "err" in item:
              td.append(r"""<td align='left' bgcolor='%s' colspan='2' ><b><font color='white'> {} </font></b></td>""".format(item) % (red))
              error = True
            else:
              _ = item
              if " " in item:
                _ = item.split()[0]
              if _ in restraints:
                td.append(r"""<td align='left'><b> {} </b></td>""".format(item))
              else:
                td.append(r"""<td align='left'><a href='sel {}'>{} </a></td>""".format(item, item))
            continue
          # align left for words:
          if not error:
            td.append(r"""
              <td align='left'>
                <a href='sel {}'>{} </a>
              </td>
              <td align='right'>
                <a href="spy.gui.edit_restraints({})">Edit </a>
              </td>""".format(item, item, item))
    if not td:
      row = "<tr> No (disagreeable) restraints found in .lst file. </tr>"
    else:
      row = "<tr> {} </tr>".format(''.join(td))
    return row

  def edit_restraints(self, restr):
    """
    this method gets the atom list of a disagreeable restraint in olex2.
    The text string is then formated so that "editatom" can handle it.
    editatom opens an editor window with the respective atoms.
    :type restr: string like "SAME/SADI Co N11 Co N22"
    """
    # separate SAME/SADI:
    restr = restr.replace('/', ' ')
    restrlist = restr.split()
    atoms = []
    for i in restrlist:
      if i in ['xz', 'yz', 'xy', 'etc.', 'U11', 'U22', 'U33', 'U12', 'U13', 'U23']:
        continue
      else:
        # atoms.append(remove_partsymbol(i))  # Have to remove this, because new names needed for 'edit'
        atoms.append(i)
    OV.cmd('editatom {}'.format(' '.join(atoms)))

def get_existing_fvar_dropdown_items():
  FvarNum=0
  while OV.GetFVar(FvarNum) is not None:
    FvarNum+=1
  items = ""
  for i in range(FvarNum):
    i += 1
    items += "%s;" %(i+1)
  return items
OV.registerFunction(get_existing_fvar_dropdown_items, False, "gui.restraints")

def set_mode_fit():
  cmd = "mode fit -s"
  val_parts = olx.html.GetValue('SPLIT_PARTS', None)
  val_fvars = olx.html.GetValue('SPLIT_FVARS', None)
  val_restraints = olx.html.GetValue('SPLIT_RESTRAINTS', None)

  if val_restraints != "--":
    cmd += " %s" %val_restraints
  
  if val_parts != "auto":
    cmd += " -p=%s" % val_parts.split("/")[0].strip()

  if val_fvars != "auto":
    cmd += " -v=%s" % val_fvars

  olex.m(cmd)

OV.registerFunction(set_mode_fit, False, "gui.restraints")


h_t = html_Table()
OV.registerFunction(h_t.edit_restraints, False, "gui")
