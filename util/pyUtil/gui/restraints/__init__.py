import olx
import io
import os
from olexFunctions import OlexFunctions
OV = OlexFunctions()
from ImageTools import ImageTools
IT = ImageTools()

def parse_bond_restraints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split()[2])
  for i in range(number_restraints):
    atom1 = text[2+4*i].split()[1]
    atom2 = text[3+4*i].strip()
    line = text[5+4*i].split()
    target = float(line[0])
    observed = float(line[1])
    delta = float(line[2])
    sigma = float(line[3])
    rows.append([observed,target,delta,sigma,"DFIX","%s %s"%(atom1,atom2)])
  return rows

def parse_angle_restarints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split()[3])
  for i in range(number_restraints):
    atom1 = text[2+5*i].split()[1]
    atom2 = text[3+5*i].strip()
    atom3 = text[4+5*i].strip()
    line = text[6+5*i].split()
    target = float(line[0])
    observed = float(line[1])
    delta = float(line[2])
    sigma = float(line[3])
    rows.append([observed,target,delta,sigma,"Angle","%s %s %s"%(atom1,atom2,atom3)])
  return rows

def parse_ADP_similarity_restraints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split()[3])
  for i in range(number_restraints):
    line = text[2+2*i]
    atoms = [line.split()[1]]
    count = 1
    line = text[2+2*i+count]
    while "delta" not in line: 
      atoms.append(line.strip())
      count += 1
      line = text[2+2*i+count]
    atoms_string = ""
    for l in range(len(atoms)):
      atoms_string += " %s"%atoms[l]
    for j in range(6):
      line = text[5+i*6+j].split()
      name = line[0]
      target = "-"
      observed = "-"
      delta = float(line[1])
      sigma = float(line[2])
      rows.append([observed,target,delta,sigma,"RIGU %s"%(name),"%s"%(atoms_string)])
  return rows

def parse_bond_sim_restraints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split()[3])
  line = text[3]
  for i in range(3,len(text)):
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
    delta = float(line[1+add])
    sigma = float(line[2+add])
    observed = '-'
    target = '-'
    rows.append([observed,target,delta,sigma,"SADI","%s"%(atoms_string)])
  return rows

def parse_rigu_restraints(string):
  rows = []
  text = string.split('\n')
  number_restraints = int(text[0].split()[3])
  for i in range(number_restraints):
    atom1 = text[2+6*i].split()[1]
    atom2 = text[3+6*i].strip()
    line = text[5+6*i].split()
    target = "-"
    observed = "-"
    delta = float(line[0])
    sigma = float(line[1])
    rows.append([observed,target,delta,sigma,"RIGU 1","%s %s"%(atom1,atom2)])
    line = text[6+6*i].split()
    target = "-"
    observed = "-"
    delta = float(line[0])
    sigma = float(line[1])
    rows.append([observed,target,delta,sigma,"RIGU 2","%s %s"%(atom1,atom2)])
    line = text[7+6*i].split()
    target = "-"
    observed = "-"
    delta = float(line[0])
    sigma = float(line[1])
    rows.append([observed,target,delta,sigma,"RIGU 3","%s %s"%(atom1,atom2)])    
  return rows

def make_Restraints_Table():
  software = OV.GetParam("snum.refinement.program")
  tabledata = []
  if "xl" in software.lower():
    import FragmentDB
    Ref = FragmentDB.refine_model_tasks.Refmod()
    lstfile = os.path.abspath(OV.FilePath() + os.path.sep + OV.FileName() + '.lst')
    if not os.path.exists(lstfile):
      print(".lst File not found!")
      return
    tabledata = Ref.fileparser(lstfile)
  else:
    from cctbx_olex_adapter import OlexCctbxAdapter
    cctbx_adaptor = OlexCctbxAdapter()
    temp = io.StringIO()
    cctbx_adaptor.restraints_manager().show_sorted(cctbx_adaptor._xray_structure,f=temp)
    output = temp.getvalue()
    bonds = "Bond restraints" in output
    angles = "Bond angle restraints" in output
    adp_sim = "ADP similarity restraints" in output
    bond_sim = "Bond similarity restraints" in output
    rigu = "Rigu bond restraints" in output
    if bonds:
      bond_rows = parse_bond_restraints(output[output.find("Bond restraints"):output.find("\n\n")])
      tabledata += bond_rows
      output = output[output.find("\n\n")+2:]
    if angles:
      angle_rows = parse_angle_restarints(output[output.find("Bond angle restraints"):output.find("\n\n")])
      tabledata += angle_rows
      output = output[output.find("\n\n")+2:]
    if bond_sim:
      bond_sim_rows = parse_bond_sim_restraints(output[output.find("Bond similarity restraints"):output.find("\n\n")])
      tabledata += bond_sim_rows
      output = output[output.find("\n\n")+2:]
    if rigu:
      rigu_rows = parse_rigu_restraints(output[output.find("Rigu bond restraints"):output.find("\n\n")])
      tabledata += rigu_rows
      output = output[output.find("\n\n")+2:]
    if adp_sim:
      adp_sim_rows = parse_ADP_similarity_restraints(output[output.find("ADP similarity restraints"):output.find("\n\n")])
      tabledata += adp_sim_rows
      output = output[output.find("\n\n")+2:]
  rest = output
  return h_t.table_maker(tabledata)

OV.registerFunction(make_Restraints_Table,False,"gui")

class html_Table(object):
  """
  html table generator
  """

  def __init__(self):
    try:
      # more than two colors here are too crystmas treelike:
      grade_2_colour = OV.GetParam('gui.skin.diagnostics.colour_grade2')
      self.grade_2_colour = self.rgb2hex(IT.adjust_colour(grade_2_colour, luminosity=1.8))
      grade_4_colour = OV.GetParam('gui.skin.diagnostics.colour_grade4')
      self.grade_4_colour = self.rgb2hex(IT.adjust_colour(grade_4_colour, luminosity=1.8))
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
    <table width="100%" border="0" cellpadding="0" cellspacing="3" > 
      <tr>
         <td align='center'> Observed </td>
         <td align='center'> Target   </td>
         <td align='center'> Delta    </td>
         <td align='center'> Sigma    </td>
         <td align='right'> Restraint </td>
         <td align='left'> Atoms </td> 
      </tr>
        <tr>
         <td align='center'> -- </td>
         <td align='center'> -- </td>
         <td align='center'> -- </td>
         <td align='center'> -- </td>
         <td align='center'> -- </td> 
      </tr>
    </table>"""
    html = r"""
    <table width="100%" border="0" cellpadding="0" cellspacing="3"> 
      <tr>
         <td align='center'> Observed </td>
         <td align='center'> Target   </td>
         <td align='center'> Error    </td>
         <td align='center'> Sigma    </td>
         <td align='right'> Restraint </td> 
         <td align='left'> Atoms </td> 
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
    td = []
    bgcolor = ''
    try:
      if abs(float(rowdata[2])) > 2.5 * float(rowdata[3]):
        bgcolor = r"""bgcolor='{}'""".format(self.grade_2_colour)
      if abs(float(rowdata[2])) > 3.5 * float(rowdata[3]):
        bgcolor = r"""bgcolor='{}'""".format(self.grade_4_colour)
    except ValueError:
      print("Unknown restraint occured.")
    for num, item in enumerate(rowdata):
      try:
        # align right for numbers:
        float(item)
        if num < 2:
          # do not colorize the first two columns:
          td.append(r"""<td align='right'> {} </td>""".format(item))
        else:
          td.append(r"""<td align='right' {0}> {1} </td>""".format(bgcolor, item))
      except:
        if item.startswith('-'):
          # only a minus sign
          td.append(r"""<td align='center'> {} </td>""".format(item))
        else:
          if num < 5:
            td.append(r"""<td align='right'> {} </td>""".format(item))
            continue
          # align left for words:
          td.append(r"""
            <td align='left'>  
              {}
            </td>
            <td align='right'>
              <a href="spy.gui.edit_restraints({})"> Edit </a> 
            </td>""".format(item, item))
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
    
h_t = html_Table()
OV.registerFunction(h_t.edit_restraints,False,"gui")