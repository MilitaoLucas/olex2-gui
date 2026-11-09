import htmlTools

from olexFunctions import OV
from variableFunctions import nsa2_get_param
from utilities import make_quick_button_gui, is_disordered

def begin_new_line(help_label="NoSpherA2_Options", scope="1", grid=False):
  # the help ID is help_label (a top-level heading of NoSpherA2.help.md); no -helpTxt,
  # which make_help_box would show verbatim instead of looking the ID up
  grid_mark = ' Xgrid="1"' if grid else ''
  return f'''<tr ALIGN='left' NAME='SNUM_REFINEMENT_NSFF' width='100%'>
  <td valign='top' width="$GetVar(HtmlTableFirstcolWidth)" align='center' bgcolor="$GetVar(HtmlTableFirstcolColour)">
  {htmlTools.MakeHoverButton(f'btn-info@{help_label}{scope}',f"spy.make_help_box -name='{help_label}' -popout='False'")}
  </td>
  <td colspan="1">
    <table border="0" width="100%" cellpadding="1" cellspacing="1" Xbgcolor="#ffaaaa"{grid_mark}>
      <tr Xbgcolor="#aaffaa">'''

def end_line():
  return '''
      </tr>
    </table>
  </td>
</tr>'''

def input_combo(name,items,value,onchange):
  return f'''<font size="$GetVar('HtmlFontSizeControls')">
  <input
    type='combo'
    height='GetVar(HtmlComboHeight)'
    bgcolor='GetVar(HtmlInputBgColour)'
    fgcolor='GetVar(HtmlFontColour)'
    valign='center' 
    name="{name}"
    width="100%"
    value="{value}"
    setdefault='false'
    items="{items}"
    disabled='false'
    onchange="{onchange}"
    readonly='true'
    onchangealways='false'
    manage='false'
    custom='GetVar(custom_button)'
  >
</font>'''

def standalone_combo(name,items,value,onchange,width=20):
  return f'''
  <td width="{width}%" align="left">
    {input_combo(name,items,value,onchange)}
  </td>'''

def labeled_combo(name,label,items,value,onchange,width_label=20, width_combo=30):
  return f'''
  <td width="{width_label}%" align="left">
    <b>{label} </b>
  </td>  
  <td width="{width_combo}%" align='left'>
    {input_combo(name,items,value,onchange)}
  </td>'''

def checkbox(name,label,checked,oncheck,onuncheck,bgcolor="GetVar(HtmlTableRowBgColour)"):
  return f'''<font size="$GetVar('HtmlFontSizeControls')">
    <input
      type="checkbox"
      height="GetVar('HtmlInputHeight')"
      fgcolor="GetVar(HtmlFontColour)"
      bgcolor="{bgcolor}"
      name="{name}"
      label="{label} "
      checked="{checked}"
      oncheck="{oncheck}"
      onuncheck="{onuncheck}"
      value=""
      onclick=""
      right="false"
      manage="false"
      disabled="false"
      custom="GetVar(custom_button)"
    >
  </font>'''

def labeled_checkbox(name,label,checked,oncheck,onuncheck,width=20):
  return f'''
  <td width='1%' align="left">
    {checkbox(name,label,checked,oncheck,onuncheck)}
  </td>  
  <td width="{width}%" align='left'>
    <b>{label} </b>
  </td>'''

def textbox(name,value,onchange):
  return f'''<font size="$GetVar('HtmlFontSizeControls')">
    <input
      type="text"
      height="GetVar('HtmlInputHeight')"
      bgcolor="GetVar('HtmlInputBgColour')"
      fgcolor="GetVar(HtmlFontColour)"
      valign="center"
      name="{name}"
      width="100%"
      value="{value}"
      onchange="{onchange}"
      onleave=""
      manage="false"
      password="false"
      multiline="false"
      disabled="false"
    >
  </font>'''

def labeled_text(name,label,value,onchange,width_label=20, width_textbox=30):
  return f'''
  <td width="{width_label}%" align="right">
    <b>{label} </b>
  </td>  
  <td width="{width_textbox}%" align='center'>
    {textbox(name,value,onchange)}
  </td>'''
  
def standalone_text(name,value,onchange,width=20):
  return f'''
  <td width="{width}%" align="center">
    {textbox(name,value,onchange)}
  </td>'''

def labeled_spin(name,label,value,onchange,width_label=20, width_spinbox=30, min_value=0, max_value=1000):
  return f'''
  <td width="{width_label}%" align="left">
    <b>{label} </b>
  </td>  
  <td width="{width_spinbox}%" align='left'>
    <input
      type='spin'
      width='100%'
      height="GetVar('HtmlInputHeight')"
      max='{max_value}'
      min='{min_value}'
      bgcolor='GetVar(HtmlInputBgColour)'
      name="{name}"
      value="{value}"
      onchange="{onchange}"
    >
  </td>'''

def button(name,label,onclick,width=20,hint=""):
  return f'''
  <td width="{width}%" align='center'>
    <font size="$GetVar('HtmlFontSizeControls')">
      <b>
        <input
          type="button"
          name="{name}"
          value="{label}"
          width="100%"
          height="GetVar(HtmlComboHeight)"
          onclick="{onclick}"
          bgcolor="GetVar(HtmlTableRowBgColour)"
          fgcolor="GetVar(linkButton.fgcolor)"
          fit="false"
          flat="GetVar(linkButton.flat)"
          hint="{hint}"
          disabled="false"
          custom="GetVar(custom_button)"
        >
      </b>
    </font>
  </td>'''

# ---------------------------------------------------------------------------
# Layout of the NoSpherA2 Options rows: a common grid with group boxes.
#
# Every row is its own table (one row per help button), so controls only line
# up across rows if every row uses the same column widths. The grid has four
# columns, each a bold label cell and a control cell; GRID_COLS gives their
# widths in % of the row.
#
# A row holds cells, and a cell occupies one or more whole columns:
#   g_field        label + control (span > 1 widens the control)
#   g_check        checkbox with its label, filling the whole column(s)
#   g_check_field  checkbox label + control (e.g. Embed [Mol])
#   g_button / g_text / g_raw / g_empty
#   g_group        a titled box (the style of the ED panels) spanning columns,
#                  whose own rows of cells sit on the same columns
# grid_row() places the cells left to right and pads the rest of the row, so
# a column that is absent in one row leaves the following ones in place.
# Keep labels short: a label longer than its cell wraps and breaks the row.
#
# Each row has one 'i' button; its help_label is a top-level heading of
# NoSpherA2.help.md ("NoSpherA2_Wavefunction" -> "# NoSpherA2 Wavefunction").
# ---------------------------------------------------------------------------

GRID_COLS = ((11, 16), (11, 15), (10, 12), (12, 13))
# a full-width group box whose rows hold at most three columns of cells uses
# three wider columns instead (so its combo boxes show their text)
GRID_COLS_3 = ((11, 22), (11, 22), (11, 23))
# empty space before every column but the first, in the units of GRID_COLS
GRID_GAP = 3

class _Frame:
  """Grid columns [first, first + n) of cols laid over a table that is 100%
  wide: the integer % widths of their gap, label and control cells. The cell
  edges are rounded, not the widths, so the widths of a row add up to 100."""
  def __init__(self, first=0, n=None, bgcolor="GetVar(HtmlTableRowBgColour)", cols=GRID_COLS):
    self.grid = cols
    self.first = first
    self.bgcolor = bgcolor
    cols = cols[first:] if n is None else cols[first:first + n]
    self.n = len(cols)
    edges, acc = [], 0
    for i, (l, c) in enumerate(cols):
      if i:
        acc += GRID_GAP
      edges.append(acc)   # label start
      acc += l
      edges.append(acc)   # control start
      acc += c
      edges.append(acc)   # column end
    self.edges = [int(round(100 * e / float(acc))) for e in edges]

  def gap(self, col):
    return self.edges[3 * col] - self.edges[3 * col - 1] if col else 0

  def label(self, col):
    return self.edges[3 * col + 1] - self.edges[3 * col]

  def span(self, col, span):
    """From the label of col to the end of col + span - 1, gaps included."""
    return self.edges[3 * (col + span - 1) + 2] - self.edges[3 * col]

def _bold(label):
  return f"<b>{label}&nbsp;</b>"

def _cells_html(cells, frame, context):
  """The <td>s of one row of cells on frame, padded to its full width."""
  col = 0
  html = []
  for span, render in cells:
    if col + span > frame.n:
      # a layout bug of the caller: render it anyway (the row wraps) but say so
      print("NoSpherA2 GUI: row '%s' has more than %d grid columns" % (context, frame.n))
      span = frame.n - col
      if span <= 0:
        break
    if col:
      html.append(f'''
  <td width="{frame.gap(col)}%"></td>''')
    html.append(render(frame, col, span))
    col += span
  if col < frame.n:
    html.append(f'''
  <td width="{frame.gap(col) + frame.span(col, frame.n - col)}%"></td>''')
  return "".join(html)

def g_field(label, control, span=1):
  def render(frame, col, span):
    width_label = frame.label(col)
    return f'''
  <td width="{width_label}%" align="left">{_bold(label)}</td>
  <td width="{frame.span(col, span) - width_label}%" align="left">{control}</td>'''
  return (span, render)

def _check_inline(name, label, checked, oncheck, onuncheck, bgcolor):
  return f'''<table border="0" cellpadding="0" cellspacing="0"><tr>
    <td>{checkbox(name, label, checked, oncheck, onuncheck, bgcolor)}</td>
    <td align="left">{_bold(label)}</td>
  </tr></table>'''

def g_check(name, label, checked, oncheck, onuncheck, span=1):
  return (span, lambda frame, col, span: f'''
  <td width="{frame.span(col, span)}%" align="left">{_check_inline(name, label, checked, oncheck, onuncheck, frame.bgcolor)}</td>''')

def g_check_field(name, label, checked, oncheck, onuncheck, control, span=1):
  def render(frame, col, span):
    width_label = frame.label(col)
    return f'''
  <td width="{width_label}%" align="left">{_check_inline(name, label, checked, oncheck, onuncheck, frame.bgcolor)}</td>
  <td width="{frame.span(col, span) - width_label}%" align="left">{control}</td>'''
  return (span, render)

def g_button(name, label, onclick, span=1, hint=""):
  return (span, lambda frame, col, span: f'''
  <td width="{frame.span(col, span)}%" align="center">{button_input(name, label, onclick, hint)}</td>''')

def g_text(text, span=1, bold=True, align="left"):
  content = _bold(text) if bold else text
  return (span, lambda frame, col, span: f'''
  <td width="{frame.span(col, span)}%" align="{align}">{content}</td>''')

def g_raw(html, span=1, align="left"):
  return (span, lambda frame, col, span: f'''
  <td width="{frame.span(col, span)}%" align="{align}">{html}</td>''')

def g_empty(span=1):
  return (span, lambda frame, col, span: f'''
  <td width="{frame.span(col, span)}%"></td>''')

def g_group(title, rows, span=4, cols=None):
  """A titled box over `span` grid columns; rows is a list of rows of cells,
  laid out on the same grid columns as the rows outside the box. A box over
  the whole grid whose rows need at most three columns gets GRID_COLS_3;
  cols=4 keeps the four columns (boxes that should line up with each other)."""
  rows = [cells for cells in rows if cells]
  needed = max([sum(s for s, _ in cells) for cells in rows] or [0])
  def render(frame, col, span):
    bgcolor = "GetVar(HtmlTableGroupBgColour)"
    if cols is None and frame.grid is GRID_COLS and span == len(GRID_COLS) and needed <= 3:
      inner = _Frame(0, None, bgcolor, GRID_COLS_3)
    else:
      inner = _Frame(frame.first + col, span, bgcolor, frame.grid)
    body = "".join(f'''
      <tr><td>
        <table Xgrid="1" border="0" width="100%" cellpadding="1" cellspacing="0"><tr>{_cells_html(cells, inner, title)}
        </tr></table>
      </td></tr>''' for cells in rows if cells)
    return f'''
  <td width="{frame.span(col, span)}%" valign="top">
    <table border="0" width="100%" cellpadding="1" cellspacing="0" bgcolor="$GetVar(HtmlTableGroupBgColour)">
      <tr><td bgcolor="$GetVar(HtmlTableGroupHeaderColour)">{_bold(title)}</td></tr>{body}
    </table>
  </td>'''
  return (span, render)

def grid_row(cells, help_label="NoSpherA2_Options", scope="1"):
  """One NoSpherA2 Options row: the help button and the cells on the common grid."""
  return begin_new_line(help_label, scope, grid=True) + _cells_html(cells, _Frame(), help_label) + end_line()

# bare controls, for the grid cells

def spinbox(name, value, onchange, min_value=0, max_value=1000):
  return f'''<input
      type='spin'
      width='100%'
      height="GetVar('HtmlInputHeight')"
      max='{max_value}'
      min='{min_value}'
      bgcolor='GetVar(HtmlInputBgColour)'
      name="{name}"
      value="{value}"
      onchange="{onchange}"
    >'''

def button_input(name, label, onclick, hint=""):
  return f'''<font size="$GetVar('HtmlFontSizeControls')">
      <b>
        <input
          type="button"
          name="{name}"
          value="{label}"
          width="100%"
          height="GetVar(HtmlComboHeight)"
          onclick="{onclick}"
          bgcolor="GetVar(HtmlTableRowBgColour)"
          fgcolor="GetVar(linkButton.fgcolor)"
          fit="false"
          flat="GetVar(linkButton.flat)"
          hint="{hint}"
          disabled="false"
          custom="GetVar(custom_button)"
        >
      </b>
    </font>'''

def _param_combo(name, items, key, update=False):
  onchange = f"spy.nsa2_set_param('{key}', html.GetValue('~name~'))"
  if update:
    onchange += " >> html.Update()"
  return input_combo(name, items, f"spy.nsa2_get_param('{key}')", onchange)

def _param_text(name, key, update=False):
  onchange = f"spy.nsa2_set_param('{key}', html.GetValue('~name~'))"
  if update:
    onchange += " >> html.Update()"
  return textbox(name, f"spy.nsa2_get_param('{key}')", onchange)

def _param_spin(name, key, min_value, max_value):
  return spinbox(name, f"spy.nsa2_get_param('{key}')",
                 f"spy.nsa2_set_param('{key}', html.GetValue('~name~'))", min_value, max_value)

def _param_check(name, label, key, update=False, span=1):
  tail = " >> html.Update()" if update else ""
  return g_check(name, label, f"spy.nsa2_get_param('{key}')",
                 f"spy.nsa2_set_param('{key}', True){tail}",
                 f"spy.nsa2_set_param('{key}', False){tail}", span=span)

# item lists

SCF_THRESHOLDS = "'NoSpherA2SCF;SloppySCF;LooseSCF;NormalSCF;StrongSCF;TightSCF;VeryTightSCF;ExtremeSCF'"
SCF_STRATEGIES = "'EasyConv;NormalConv;SlowConv;VerySlowConv'"
ORCA_SOLVENTS = "'Vacuum;Water;Acetone;Acetonitrile;Ammonia;Benzene;CCl4;CH2CL2;Chloroform;Cyclohexane;DMF;DMSO;Ethanol;Hexane;Methanol;Octanol;Pyridine;THF;Toluene'"
ORCA_SOLVENTS_CUSTOM = ORCA_SOLVENTS[:-1] + ";Custom'"
PYSCF_SOLVENTS = "'Vacuum;Water;Acetonitrile;Methanol;Ethanol;IsoQuinoline;Quinoline;Chloroform;DiethylEther;Dichloromethane;DiChloroEthane;CarbonTetraChloride;Benzene;Toluene;ChloroBenzene;NitroMethane;Heptane;CycloHexane;Aniline;Acetone;TetraHydroFuran;DiMethylSulfoxide;Argon;Krypton;Xenon;n-Octanol;1,1,1-TriChloroEthane;1,1,2-TriChloroEthane;1,2,4-TriMethylBenzene;1,2-DiBromoEthane;1,2-EthaneDiol;1,4-Dioxane;1-Bromo-2-MethylPropane;1-BromoOctane;1-BromoPentane;1-BromoPropane;1-Butanol;1-ChloroHexane;1-ChloroPentane;1-ChloroPropane;1-Decanol;1-FluoroOctane;1-Heptanol;1-Hexanol;1-Hexene;1-Hexyne;1-IodoButane;1-IodoHexaDecane;1-IodoPentane;1-IodoPropane;1-NitroPropane;1-Nonanol;1-Pentanol;1-Pentene;1-Propanol;2,2,2-TriFluoroEthanol;2,2,4-TriMethylPentane;2,4-DiMethylPentane;2,4-DiMethylPyridine;2,6-DiMethylPyridine;2-BromoPropane;2-Butanol;2-ChloroButane;2-Heptanone;2-Hexanone;2-MethoxyEthanol;2-Methyl-1-Propanol;2-Methyl-2-Propanol;2-MethylPentane;2-MethylPyridine;2-NitroPropane;2-Octanone;2-Pentanone;2-Propanol;2-Propen-1-ol;3-MethylPyridine;3-Pentanone;4-Heptanone;4-Methyl-2-Pentanone;4-MethylPyridine;5-Nonanone;AceticAcid;AcetoPhenone;a-ChloroToluene;Anisole;Benzaldehyde;BenzoNitrile;BenzylAlcohol;BromoBenzene;BromoEthane;Bromoform;Butanal;ButanoicAcid;Butanone;ButanoNitrile;ButylAmine;ButylEthanoate;CarbonDiSulfide;Cis-1,2-DiMethylCycloHexane;Cis-Decalin;CycloHexanone;CycloPentane;CycloPentanol;CycloPentanone;Decalin-mixture;DiBromomEthane;DiButylEther;DiEthylAmine;DiEthylSulfide;DiIodoMethane;DiIsoPropylEther;DiMethylDiSulfide;DiPhenylEther;DiPropylAmine;e-1,2-DiChloroEthene;e-2-Pentene;EthaneThiol;EthylBenzene;EthylEthanoate;EthylMethanoate;EthylPhenylEther;FluoroBenzene;Formamide;FormicAcid;HexanoicAcid;IodoBenzene;IodoEthane;IodoMethane;IsoPropylBenzene;m-Cresol;Mesitylene;MethylBenzoate;MethylButanoate;MethylCycloHexane;MethylEthanoate;MethylMethanoate;MethylPropanoate;m-Xylene;n-ButylBenzene;n-Decane;n-Dodecane;n-Hexadecane;n-Hexane;NitroBenzene;NitroEthane;n-MethylAniline;n-MethylFormamide-mixture;n,n-DiMethylAcetamide;n,n-DiMethylFormamide;n-Nonane;n-Octane;n-Pentadecane;n-Pentane;n-Undecane;o-ChloroToluene;o-Cresol;o-DiChloroBenzene;o-NitroToluene;o-Xylene;Pentanal;PentanoicAcid;PentylAmine;PentylEthanoate;PerFluoroBenzene;p-IsoPropylToluene;Propanal;PropanoicAcid;PropanoNitrile;PropylAmine;PropylEthanoate;p-Xylene;Pyridine;sec-ButylBenzene;tert-ButylBenzene;TetraChloroEthene;TetraHydroThiophene-s,s-dioxide;Tetralin;Thiophene;Thiophenol;trans-Decalin;TriButylPhosphate;TriChloroEthene;TriEthylAmine;Xylene-mixture;z-1,2-DiChloroEthene'"
ELMO_BASIS_SETS = "'6-31G;6-31G**;6-311G;6-311G**;cc-pVDZ;extrabasis'"

# the common cells

def method_cell():
  return g_field("Method", _param_combo("NoSpherA2_method@refine", "spy.NoSpherA2.get_functional_list()", "method"))

def basis_cell():
  return g_field("Basis", _param_combo("NoSpherA2_basis@refine", "spy.NoSpherA2.getBasisListStr()", "basis_name", update=True))

def cpu_cell():
  return g_field("CPUs", _param_combo("NoSpherA2_cpus@refine", "spy.NoSpherA2.getCPUListStr()", "ncpus"))

def memory_cell():
  return g_field("Mem/GB", _param_text("NosPherA2_Memory", "mem"))

def charge_cell():
  return g_field("Charge", _param_spin("NoSpherA2_Charge@refine", "charge", -1000, 1000))

def multiplicity_cell():
  return g_field("Mult.", _param_spin("NoSpherA2_Multiplicity@refine", "multiplicity", 1, 200))

def update_tsc_cell():
  return g_button("Update_TSC", "Update .tsc", "spy.NoSpherA2.launch() >> html.Update()",
                  hint="Generate new .tsc file with current settings")

def iterative_cells():
  """Iterative checkbox, then Update .tsc (one-off) or the cycle limit (iterative): two columns."""
  cells = [g_check("NoSpherA2_Iterative@refine", "Iterative",
                   "spy.nsa2_get_param('full_HAR')",
                   "spy.nsa2_set_param('full_HAR','True')>>html.Update()",
                   "spy.nsa2_set_param('full_HAR','False')>>html.Update()")]
  if nsa2_get_param('full_HAR') == True:
    cells.append(g_field("Cycles", _param_spin("NoSpherA2_Max_HAR_Cycles@refine", "Max_HAR_Cycles", 1, 100)))
  else:
    cells.append(update_tsc_cell())
  return cells

def relativistics_cell():
  return _param_check("NoSpherA2_Relativistics@refine", "Relativistic", "Relativistic")

def adv_basis_cells(update=True, adv=None):
  """Adv. Basis checkbox and, when ticked, the per-element basis string: one row."""
  if adv is None:
    adv = nsa2_get_param('basis_adv') == True
  cells = [_param_check("NoSpherA2_baseset_adv@refine", "Adv. Basis", "basis_adv", update=True)]
  if adv:
    cells.append(g_field("Elements", _param_text("NoSpherA2_Basis_Set_Extra@refine", "basis_adv_string", update=update), span=2))
  return cells

def ptb_prerefine_cells():
  # pTB cycles before the selected QM source; the switch-over lives in CctbxLib/aaff.py.
  # Ticked means pTB runs on the next refinement: once done it shows unticked, and only a new tick repeats it.
  done = bool(str(nsa2_get_param('PTB_PREREFINE_DONE') or '').strip())
  armed = bool(nsa2_get_param('PTB_PREREFINE')) and not done
  cells = [g_check("NoSpherA2_ptb_prerefine@refine",
                   "pTB pre-refine (done)" if done else "pTB pre-refine",
                   "true" if armed else "false",
                   "spy.nsa2_set_param('PTB_PREREFINE', True) >> spy.nsa2_set_param('PTB_PREREFINE_DONE', '') >> html.Update()",
                   "spy.nsa2_set_param('PTB_PREREFINE', False) >> html.Update()",
                   span=2 if done else 1)]
  if armed:
    cells.append(g_field("Cycles", _param_spin("NoSpherA2_ptb_prerefine_cycles@refine", "PTB_PREREFINE_CYCLES", 1, 100)))
  return cells

# the common rows

def wavefunction_row(rows, title="Wavefunction", integration=True):
  """The level of theory (3 columns) and the integration grid of NoSpherA2 (last column)."""
  if not integration:
    return grid_row([g_group(title, rows, span=4)], "NoSpherA2_Wavefunction")
  grid = g_field("Grid", input_combo("NoSpherA2_becke_accuracy@refine", "'Low;Normal;High;Max'",
                                     "spy.nsa2_get_param('becke_accuracy')",
                                     "spy.nsa2_set_param('becke_accuracy', html.GetValue('~name~'))"))
  return grid_row([g_group(title, rows, span=3), g_group("Integration", [[grid]], span=1)],
                  "NoSpherA2_Wavefunction")

def molecule_resources_row(molecule_rows=None, resource_rows=None):
  """Charge and multiplicity of the molecule | CPUs and memory of the job."""
  if molecule_rows is None:
    molecule_rows = [[charge_cell(), multiplicity_cell()]]
  if resource_rows is None:
    resource_rows = [[cpu_cell(), memory_cell()]]
  return grid_row([g_group("Molecule", molecule_rows, span=2), g_group("Resources", resource_rows, span=2)],
                  "NoSpherA2_Molecule_and_Resources")

def refinement_row(iterative=True, ptb=False, model=True):
  """The HAR cycle (one-off .tsc or iterative, pTB first) | the model (H aniso, no AFIX)."""
  har = [iterative_cells() if iterative else [g_empty(), update_tsc_cell()]]
  if ptb:
    har.append(ptb_prerefine_cells())
  cells = [g_group("HAR", har, span=2)]
  if model:
    cells.append(g_group("Model", [[_param_check("NoSpherA2_H_Aniso@refine", "H Aniso", "h_aniso"),
                                    _param_check("NoSpherA2_Afix_remove@refine", "No Afix", "h_afix")]], span=2))
  return grid_row(cells, "NoSpherA2_Refinement")

def orca_scf_row(damping=False):
  cells = [g_field("Thresh.", _param_combo("NoSpherA2_ORCA_SCF_Conv@refine", SCF_THRESHOLDS, "ORCA_SCF_Conv")),
           g_field("Strategy", _param_combo("NoSpherA2_ORCA_SCF_Strategy@refine", SCF_STRATEGIES, "ORCA_SCF_Strategy"))]
  if damping:
    cells.append(_param_check("NoSpherA2_ORCA_damp@refine", "Damping", "ORCA_DAMP"))
  return grid_row([g_group("SCF Convergence", [cells])], "NoSpherA2_SCF")

def custom_solvent_cells():
  return [g_empty(),
          g_field("Epsilon", _param_text("NoSpherA2_ORCA_Solvation_Custom_epsilon@refine", "ORCA_Solvation_CPCM_epsilon")),
          g_field("Refr. n", _param_text("NoSpherA2_ORCA_Solvation_Custom_refractive@refine", "ORCA_Solvation_CPCM_refrac")),
          g_field("Probe r", _param_text("NoSpherA2_ORCA_Solvation_Custom_probe@refine", "ORCA_Solvation_CPCM_rsolv"))]

def orca_environment_row(embedding=False):
  """Solvation, or (new ORCA, ordered structure) the crystal embedding that replaces it."""
  embed = embedding and nsa2_get_param('ORCA_USE_CRYSTAL_QMMM')
  solvent = g_field("Solvent", _param_combo("NoSpherA2_ORCA_Solvation@refine", ORCA_SOLVENTS_CUSTOM, "ORCA_Solvation", update=True), span=2)
  first = []
  if embedding:
    embed_type = _param_combo("NoSpherA2_ORCA_embedding_type@refine", "Mol;Ion", "ORCA_CRYSTAL_QMMM_TYPE", update=True) if embed else ""
    first.append(g_check_field("NoSpherA2_ORCA_embedding@refine", "Embed",
                               "spy.nsa2_get_param('ORCA_USE_CRYSTAL_QMMM')",
                               "spy.nsa2_set_param('ORCA_USE_CRYSTAL_QMMM', True) >> html.Update()",
                               "spy.nsa2_set_param('ORCA_USE_CRYSTAL_QMMM', False) >> html.Update()",
                               embed_type))
  else:
    first.append(g_empty())
  rows = [first]
  if embed:
    first += [g_field("Radius", _param_text("NoSpherA2_ORCA_embedding_radius@refine", "ORCA_CRYSTAL_QMMM_RADIUS")),
              g_field("Conv.", _param_text("NoSpherA2_ORCA_convergence@refine", "ORCA_CRYSTAL_QMMM_CONV")),
              g_field("HF lay.", _param_spin("NoSpherA2_ORCA_HF_Layers@refine", "ORCA_CRYSTAL_QMMM_HF_LAYERS", 0, 100))]
    if nsa2_get_param('ORCA_CRYSTAL_QMMM_TYPE') == "Ion":
      rows.append([g_empty(), g_empty(), g_empty(),
                   g_field("ECP lay.", _param_spin("NoSpherA2_ORCA_ECP_Layers@refine", "ORCA_CRYSTAL_QMMM_ECP_LAYERS", 0, 100))])
  else:
    first.append(solvent)
    if nsa2_get_param('ORCA_Solvation') == "Custom":
      rows.append(custom_solvent_cells())
  return grid_row([g_group("Crystal Environment", rows)], "NoSpherA2_Environment")

def disorder_row():
  return grid_row([g_group("Disorder", [[g_field("Groups", _param_text("NoSpherA2_grouped_parts@refine", "Disorder_Groups"), span=4)]])],
                  "NoSpherA2_Disorder")

def disorder_groups_text():
  return disorder_row() if is_disordered() else ""

def wsl_distro_cell(span=2):
  return g_field("WSL", _param_combo("NoSpherA2_WSL_distro@refine", "spy.NoSpherA2.get_distro_list()", "distro"), span)

def partitioning_scheme_line():
  if OV.GetParam('user.NoSpherA2.show_partitioning') != True:
    return ""
  ri_fit = nsa2_get_param('NoSpherA2_Partition') == "RI-Fit"
  rows = [[g_field("Scheme", _param_combo("NoSpherA2_partitioning_scheme@refine",
                                           "'Hirshfeld;RI-Fit;TFVC;Becke;MBIS;EMBIS'",
                                           "NoSpherA2_Partition", update=True))]]
  if ri_fit:
    rows[0].append(g_field("Aux.", _param_combo("NoSpherA2_Aux_basis@refine",
                                                 "auto;combo_basis_fit;def2_universal_jkfit;def2_universal_jfit;def2_svp_rifit;hgbsp3_7;def2_qzvppd_rifit;tzvp_jkfit;cc-pvqz-jkfit",
                                                 "auxiliary_basis", update=True), span=2))
    restrain = [g_field("Restrain", _param_combo("NoSpherA2_RI_restraint@refine",
                                                  "'Off;Hirshfeld;TFVC;MBIS;EMBIS;Nuclear;Mulliken;Sanderson'",
                                                  "RI_restraint", update=True))]
    # Nuclear, Mulliken and Sanderson only restrain charges, NoSpherA2 ignores the order for them
    if nsa2_get_param('RI_restraint') in ("Hirshfeld", "TFVC", "MBIS", "EMBIS"):
      restrain.append(g_field("Max l", _param_spin("NoSpherA2_RI_restraint_lmax@refine", "RI_restraint_lmax", 0, 8)))
    rows.append(restrain)
  return grid_row([g_group("Partitioning", rows)], "NoSpherA2_Partitioning")

def quick_buttons_row():
  return begin_new_line("NoSpherA2_Quick_Buttons") + make_quick_button_gui() + end_line()

# old-style helpers still used by the XCW block

def charge_spin():
  return labeled_spin("NoSpherA2_Charge@refine",
                      "Charge",
                      "spy.nsa2_get_param(\'charge\')",
                      "spy.nsa2_set_param(\'charge\',html.GetValue(\'~name~\'))",
                      width_label=11, width_spinbox=9, min_value=-1000, max_value=1000)

def multiplicity_spin():
  return labeled_spin("NoSpherA2_Multiplicity@refine",
                      "Multiplicity",
                      "spy.nsa2_get_param(\'multiplicity\')",
                      "spy.nsa2_set_param(\'multiplicity\',html.GetValue(\'~name~\'))",
                      width_label=14, width_spinbox=9, min_value=1, max_value=200)

# the per-program blocks

def make_hybrid_GUI(softwares_list_string, ptb=False):
  parts = OV.ListParts()
  if parts != None:
    parts = list(parts)
  if len(parts) <= 1:
    return grid_row([g_text("Hybrid is not possible with less than two parts!", span=4, bold=False)], "NoSpherA2_Hybrid")
  grid = g_field("Grid", input_combo("NoSpherA2_becke_accuracy@refine", "'Low;Normal;High;Max'",
                                     "spy.nsa2_get_param('becke_accuracy')",
                                     "spy.nsa2_set_param('becke_accuracy', html.GetValue('~name~'))"))
  t = grid_row([g_group("Integration", [[grid]], span=2), g_group("Resources", [[cpu_cell(), memory_cell()]], span=2)],
               "NoSpherA2_Molecule_and_Resources")
  t += refinement_row(ptb=ptb)
  t += partitioning_scheme_line()
  discamb = "  " + str(OV.GetParam('user.NoSpherA2.discamb_exe'))
  for i in parts:
    if i == 0:
      continue
    softwares_list = "Please Select" + str(softwares_list_string).replace("Hybrid;", "")
    rows = [[g_field("Program", input_combo("NoSpherA2_software_Part%d@refine" % (i + 1), softwares_list,
                                            "spy.nsa2_get_param('Hybrid.software_Part%d')" % i,
                                            "spy.nsa2_set_param('Hybrid.software_Part%d',html.GetValue('~name~'))>>html.Update()" % i),
                     span=2)]]
    selected_software = nsa2_get_param('Hybrid.software_Part%d' % i)
    if selected_software == discamb:
      rows.append([g_text("So far no further options for discambMATT", span=4, bold=False)])
    elif selected_software == "ELMOdb":
      # HAVE TO FINISH ELMO LATER
      rows.append([g_field("Basis", _param_combo("NoSpherA2_basis_Part%d@refine" % i, ELMO_BASIS_SETS, "Hybrid.basis_name_Part%d" % i))])
    else:
      rows.append([g_field("Basis", _param_combo("NoSpherA2_basis_Part%d@refine" % i, "spy.NoSpherA2.getBasisListStr()", "Hybrid.basis_name_Part%d" % i)),
                   g_field("Method", _param_combo("NoSpherA2_method_Part%d@refine" % i,
                                                  "spy.NoSpherA2.get_functional_list(spy.nsa2_get_param('Hybrid.software_Part%d'))" % i,
                                                  "Hybrid.method_Part%d" % i)),
                   _param_check("NoSpherA2_ORCA_Relativistics_PART%d@refine" % i, "Relativistic", "Hybrid.Relativistic_Part%d" % i)])
      rows.append([g_field("Charge", _param_spin("SET_CHARGE_PART%d@refine" % i, "Hybrid.charge_Part%d" % i, -1000, 1000)),
                   g_field("Mult.", _param_spin("SET_MULTIPLICITY_PART%d@refine" % i, "Hybrid.multiplicity_Part%d" % i, 1, 200))])
      if "ORCA" in selected_software:
        rows.append([g_field("SCF", _param_combo("NoSpherA2_ORCA_SCF_Conv_Part%d@refine" % i, SCF_THRESHOLDS, "Hybrid.ORCA_SCF_Conv_Part%d" % i)),
                     g_field("Strategy", _param_combo("NoSpherA2_ORCA_SCF_Strategy_Part%d@refine" % i, SCF_STRATEGIES, "Hybrid.ORCA_SCF_Strategy_Part%d" % i)),
                     g_field("Solvent", _param_combo("NoSpherA2_ORCA_Solvation@refine", ORCA_SOLVENTS, "ORCA_Solvation"), span=2)])
      elif "pySCF" in selected_software:
        rows.append([g_field("Damping", _param_combo("NoSpherA2_Hybrid_pySCF_Damping_Part%d@refine" % i, "'0.6;0.7;0.85;0.93'", "Hybrid.pySCF_Damping_Part%d" % i)),
                     g_field("Solvent", _param_combo("NoSpherA2_pyscf_Solvation@refine", PYSCF_SOLVENTS, "ORCA_Solvation"), span=3)])
    t += grid_row([g_group("Part %d" % i, rows, cols=4)], "NoSpherA2_Hybrid", str(i))
  return t

def make_xtb_GUI():
  t = wavefunction_row([[method_cell(), g_field("Temp./K", _param_text("NoSpherA2_xtb_temp@refine", "temperature"))]])
  t += molecule_resources_row()
  t += refinement_row()
  t += partitioning_scheme_line()
  return t

def make_ptb_GUI():
  t = wavefunction_row([[_param_check("NoSpherA2_purification@refine", "Purify", "PTB_use_purify", update=True)]])
  t += molecule_resources_row()
  t += refinement_row()
  t += disorder_groups_text()
  t += partitioning_scheme_line()
  return t

def make_SALTED_GUI():
  buttons = htmlTools.MakeHoverButton('toolbar-open', 'spy.NoSpherA2.appendDir(user.NoSpherA2.salted_models_list) >> html.Update()', 'on') + \
            "&nbsp;" + \
            htmlTools.MakeHoverButton('toolbar-delete', 'spy.NoSpherA2.removeDir(user.NoSpherA2.salted_models_list, html.GetValue(NoSpherA2_SALTED_model@refine)) >> html.Update()', 'on')
  t = grid_row([g_group("SALTED Model", [[g_field("Model", _param_combo("NoSpherA2_SALTED_model@refine", "spy.NoSpherA2.get_SALTED_model_locations()", "selected_salted_model"), span=2),
                                          g_raw(buttons)]], span=3),
                g_group("Resources", [[cpu_cell()]], span=1)],
               "NoSpherA2_Wavefunction")
  t += refinement_row()
  return t

def make_Thakkar_GUI():
  return grid_row([g_group("Thakkar IAM", [[
                     g_field("Cations", _param_text("NoSpherA2_Thakkar_cations@refine", "Thakkar_Cations")),
                     g_field("Anions", _param_text("NoSpherA2_Thakkar_anions@refine", "Thakkar_Anions")),
                     g_empty(),
                     g_button("Update_Thakkar_Model", "Update Model", "spy.NoSpherA2.launch() >> html.Update()",
                              hint="Generate new Thakkar model with current settings")]])],
                  "NoSpherA2_Thakkar")

def make_ELMOdb_GUI():
  t = wavefunction_row([[g_field("Basis", _param_combo("NoSpherA2_basis@refine", ELMO_BASIS_SETS, "basis_name"))]])
  t += molecule_resources_row()
  t += refinement_row()
  # ELMO specific options
  t += "<!-- #include ELMO_specific ../util/pyUtil/NoSpherA2/ELMO_specific.htm;help_ext=NoSpherA2 Extras;1; -->" + \
       partitioning_scheme_line()
  return t

def make_wfn_GUI():
  grid = g_field("Grid", input_combo("NoSpherA2_becke_accuracy@refine", "'Low;Normal;High;Max'",
                                     "spy.nsa2_get_param('becke_accuracy')",
                                     "spy.nsa2_set_param('becke_accuracy', html.GetValue('~name~'))"))
  return grid_row([g_group("Integration", [[grid]], span=2), g_group("Resources", [[cpu_cell(), memory_cell()]], span=2)],
                  "NoSpherA2_Molecule_and_Resources") + \
         refinement_row(iterative=False) + \
         partitioning_scheme_line()

def make_OCC_GUI(ptb=False):
  t = quick_buttons_row()
  t += wavefunction_row([[basis_cell(), method_cell()],
                         [g_field("DF Basis", _param_combo("NoSpherA2_OCC_DF_Basis@refine",
                                                           "'def2_universal_jkfit;cc-pvtz-jkfit;cc-pvqz-jkfit'",
                                                           "OCC_df_basis"), span=2)]])
  t += molecule_resources_row()
  t += refinement_row(ptb=ptb)
  t += disorder_groups_text()
  t += partitioning_scheme_line()
  return t

def make_ORCA_GUI(new_ORCA = True, ptb=False):
  # Wfn_Job never embeds a disordered structure, and its Embed. switch is hidden there, so it must not hide Solvation
  disordered = is_disordered()
  t = quick_buttons_row()
  t += wavefunction_row([[basis_cell(), method_cell(), relativistics_cell()], adv_basis_cells()])
  molecule = [[charge_cell(), multiplicity_cell()]]
  if new_ORCA and not disordered and nsa2_get_param('user.NoSpherA2.show_broken_sym'):
    molecule.append([_param_check("NoSpherA2_ORCA_use_brok_sym@refine", "Broken Symmetry", "ORCA_use_broken_sym", update=True, span=2)])
    if nsa2_get_param('ORCA_use_broken_sym'):
      molecule.append([g_field("Atoms", _param_text("NoSpherA2_ORCA_brok_sym_atoms@refine", "ORCA_Broken_sym_atoms")),
                       g_field("Spin", _param_text("NoSpherA2_ORCA_brok_sym_spins@refine", "ORCA_Broken_sym_spin"))])
  t += molecule_resources_row(molecule)
  t += orca_scf_row(damping=new_ORCA and not disordered)
  t += orca_environment_row(embedding=new_ORCA and not disordered)
  t += refinement_row(ptb=ptb)
  t += disorder_groups_text()
  t += partitioning_scheme_line()
  return t

def make_tonto_GUI():
  t = wavefunction_row([[basis_cell(), method_cell(), relativistics_cell()]])
  t += molecule_resources_row()
  t += grid_row([g_group("SCF Convergence", [[g_field("DIIS", _param_combo("NoSpherA2_tonto_DIIS@refine", "'0.1;0.01;0.001;0.0001;0.00001'", "DIIS"))]], span=1),
                 g_group("Crystal Environment", [[g_field("Cluster r", _param_text("NoSpherA2_tonto_cluster_radius@refine", "cluster_radius")),
                                                  _param_check("NoSpherA2_tonto_cluster_grow@refine", "Complete Cluster", "cluster_grow", span=2)]], span=3)],
                "NoSpherA2_Environment")
  t += refinement_row()
  t += partitioning_scheme_line()
  return t

def make_frag_HAR_GUI():
  t = quick_buttons_row()
  t += wavefunction_row([[basis_cell(), method_cell(), relativistics_cell()],
                         adv_basis_cells(update=False, adv=OV.GetParam('user.NoSpherA2.basis_adv') == True)])
  t += molecule_resources_row()
  t += orca_scf_row()
  t += orca_environment_row()
  t += grid_row([g_group("Fragments", [[
                   g_field("Rad. tol.", _param_text("NoSpherA2_frag_HAR_radius_tol@refine", "frag_HAR.radius_tolerance")),
                   _param_check("NoSpherA2_frag_HAR_test@refine", "Test Frags.", "frag_HAR.H_test"),
                   _param_check("NoSpherA2_frag_HAR_H_Box_Ex@refine", "H-bond", "frag_HAR.H_box_ex"),
                   _param_check("NoSpherA2_frag_HAR_min_H_bond@refine", "Min. H-bond", "frag_HAR.min_H_bond")]])],
                "NoSpherA2_Fragments")
  t += refinement_row()
  t += partitioning_scheme_line()
  return t

def make_pySCF_GUI(ptb=False):
  t = wavefunction_row([[basis_cell(), method_cell()]])
  t += molecule_resources_row(resource_rows=[[cpu_cell(), memory_cell()], [wsl_distro_cell()]])
  t += grid_row([g_group("SCF Convergence", [[g_field("Damping", _param_combo("NoSpherA2_Hybrid_pySCF_Damping@refine", "'0.6;0.7;0.85;0.93'", "pySCF_Damping"))]], span=1),
                 g_group("Crystal Environment", [[g_field("Solvent", _param_combo("NoSpherA2_ORCA_Solvation@refine", PYSCF_SOLVENTS, "ORCA_Solvation"), span=3)]], span=3)],
                "NoSpherA2_Environment")
  t += refinement_row(ptb=ptb)
  t += disorder_groups_text()
  t += partitioning_scheme_line()
  return t

def make_discambMATT_GUI():
  return refinement_row() + disorder_groups_text()

def make_xHARPY_GUI():
  k_boxes = "".join(
    "<td width='33%'>" + textbox("NoSpherA2_xHARPY_k_points%d" % k, "spy.nsa2_get_param('xharpy.k_points%d')" % k,
                                 "spy.nsa2_set_param('xharpy.k_points%d', html.GetValue('~name~'))" % k) + "</td>"
    for k in (1, 2, 3))
  k_table = f"<table border='0' width='100%' cellpadding='0' cellspacing='1'><tr>{k_boxes}</tr></table>"
  t = wavefunction_row([[method_cell(),
                         g_field("Spacing", textbox("NoSpherA2_xHARPY_grid_spacing", "spy.nsa2_get_param('xharpy.grid_spacing')",
                                                    "spy.nsa2_set_param('xharpy.grid_spacing', html.GetValue('~name~'))"))],
                        [g_field("k-points", k_table, span=2),
                         g_check("NoSpherA2_xHARPY_center_gamma", "Center Gamma",
                                 "spy.nsa2_get_param('xharpy.k_points_centre_gamma')",
                                 "spy.nsa2_set_param('xharpy.k_points_centre_gamma', True)",
                                 "spy.nsa2_set_param('xharpy.k_points_centre_gamma', False)", span=2)]],
                       title="Periodic Wavefunction", integration=False)
  t += grid_row([g_group("Resources", [[wsl_distro_cell(), cpu_cell(), memory_cell()]])], "NoSpherA2_Molecule_and_Resources")
  t += refinement_row(iterative=False, model=False)
  return t


def make_CE_GUI():
  if OV.GetParam('user.NoSpherA2.show_CE') != True:
    return ""
  from crystal_energies import crystal_energies_status
  t = begin_new_line("CrystalEnergies") + \
    "<td width='13%' align='left'><b>Energies</b></td>" + \
    labeled_text("NoSpherA2_CE_cutoff@refine",
                 "Cutoff/&Aring;",
                 "spy.nsa2_get_param('CE_cutoff')",
                 "spy.nsa2_set_param('CE_cutoff', html.GetValue('~name~'))",
                 width_label=9, width_textbox=7) + \
    labeled_combo("NoSpherA2_CE_model@refine",
                  "Model",
                  "spy.NoSpherA2.get_SALTED_model_locations()",
                  "spy.nsa2_get_param('selected_salted_model')",
                  "spy.nsa2_set_param('selected_salted_model', html.GetValue('~name~'))",
                  width_label=7, width_combo=20) + \
    button("NoSpherA2_CE_calc", "Calculate", "spy.NoSpherA2.crystal_energies_calculate()", width=13,
           hint="Predict every molecule with the SALTED model in the background and draw the pair energies as rods; cached until an atom moves") + \
    button("NoSpherA2_CE_recalc", "Redo", "spy.NoSpherA2.crystal_energies_recalculate()", width=8,
           hint="Discard the cached energies of this geometry and calculate again") + \
    button("NoSpherA2_CE_clear", "Clear", "spy.NoSpherA2.crystal_energies_clear() >> html.Update()", width=8,
           hint="Remove the rods") + \
    f"<td width='15%' align='center'><i>{crystal_energies_status()}</i></td>" + \
  end_line() + \
  begin_new_line("CrystalEnergies", scope="2") + \
    "<td width='13%' align='left'><b>Framework</b></td>" + \
    labeled_combo("NoSpherA2_CE_kind@refine",
                  "Kind",
                  "total;elst;pol;disp;rep;xc",
                  "spy.nsa2_get_param('CE_kind')",
                  "spy.nsa2_set_param('CE_kind', html.GetValue('~name~')) >> spy.NoSpherA2.crystal_energies_redraw()",
                  width_label=6, width_combo=11) + \
    labeled_combo("NoSpherA2_CE_pair@refine",
                  "Pair",
                  "spy.NoSpherA2.crystal_energies_pairs()",
                  "spy.nsa2_get_param('CE_pair')",
                  "spy.nsa2_set_param('CE_pair', html.GetValue('~name~')) >> spy.NoSpherA2.crystal_energies_redraw()",
                  width_label=6, width_combo=14) + \
    button("NoSpherA2_CE_visible", "Molecules on screen", "spy.NoSpherA2.crystal_energies_draw()", width=25,
           hint="Rods of the selected energy kind for every contact of the molecules on screen (all cached pairs, or the one chosen); one colour per kind, radius proportional to the energy, repulsive pale") + \
    button("NoSpherA2_CE_block", "Framework 3x3x3", "spy.NoSpherA2.crystal_energies_framework()", width=25,
           hint="The energy framework of the 3x3x3 block of cells around the origin cell") + \
  end_line()
  return t


def _xcw_text(name, label, key, width_label, width_textbox):
  return labeled_text(f"NoSpherA2_XCW_{name}@refine", label,
                      f"spy.nsa2_get_param('XCW.{key}')",
                      f"spy.nsa2_set_param('XCW.{key}', html.GetValue('~name~'))",
                      width_label=width_label, width_textbox=width_textbox)

def _xcw_checkbox(name, label, key, width):
  return labeled_checkbox(f"NoSpherA2_XCW_{name}@refine", label,
                          f"spy.nsa2_get_param('XCW.{key}')",
                          f"spy.nsa2_set_param('XCW.{key}', True)",
                          f"spy.nsa2_set_param('XCW.{key}', False)",
                          width=width)

def _xcw_combo(name, label, key, items, width_label, width_combo, update=False):
  onchange = f"spy.nsa2_set_param('XCW.{key}', html.GetValue('~name~'))"
  if update:
    onchange += " >> html.Update()"
  return labeled_combo(f"NoSpherA2_XCW_{name}@refine", label, items,
                       f"spy.nsa2_get_param('XCW.{key}')", onchange,
                       width_label=width_label, width_combo=width_combo)

def make_XCW_GUI():
  """The X-ray constrained wavefunction block. Experimental: shown only with
  user.NoSpherA2.show_XCW, see xcw.py for what the buttons run."""
  if OV.GetParam('user.NoSpherA2.show_XCW') != True:
    return ""
  from xcw import xcw_status, xcw_tscb_list
  basis_items = ("spy.NoSpherA2.xcw_basis_list()" if nsa2_get_param('XCW.basis_adv') == True
                 else "spy.NoSpherA2.getBasisListStr()")
  # label widths: about 1.3 % per character keeps every label on one line
  # basis and reference: the settings-file keywords basis_set, df_basis, rhf/uhf
  t = begin_new_line("NoSpherA2_XCW", "1") + \
      _xcw_combo("basis", "Basis Set", "basis_name", basis_items, 13, 24) + \
      _xcw_text("df_basis", "DF Basis", "df_basis", 13, 16) + \
      _xcw_combo("reference", "Reference", "reference", "rhf;uhf", 14, 12) + \
      end_line()
  t += begin_new_line("NoSpherA2_XCW", "basis") + \
       labeled_checkbox("NoSpherA2_XCW_basis_adv@refine", "Adv. Basis",
                        "spy.nsa2_get_param('XCW.basis_adv')",
                        "spy.nsa2_set_param('XCW.basis_adv', True) >> html.Update()",
                        "spy.nsa2_set_param('XCW.basis_adv', False) >> html.Update()",
                        width=17)
  if nsa2_get_param('XCW.basis_adv') == True:
    t += _xcw_text("basis_adv_string", "Element / BSE Basis", "basis_adv_string", 25, 50)
  t += end_line()
  if nsa2_get_param('XCW.basis_adv') == True:
    t += begin_new_line("NoSpherA2_XCW", "basis-note") + \
         "<td><i>Basis functions only: non-relativistic SCF, no DKH2 Hamiltonian.</i></td>" + \
         end_line()
  # fit target (f/f2, weighted) and the electron count
  t += begin_new_line("NoSpherA2_XCW", "2") + \
       _xcw_combo("target", "Target", "target", "F;F2", 10, 10) + \
       _xcw_checkbox("weighted", "Weighted", "weighted", 13) + \
       charge_spin() + \
       multiplicity_spin() + \
       "<td width='23%'></td>" + \
       end_line()
  # the lambda scan: start, step_size, end; the parameter count of the chi-square comes from the model
  t += begin_new_line("NoSpherA2_XCW", "3") + \
       _xcw_text("start", "&lambda; Start", "start", 12, 14) + \
       _xcw_text("step", "Step", "step_size", 8, 14) + \
       _xcw_text("end", "End", "end", 7, 14) + \
       "<td width='31%'></td>" + \
       end_line()
  # SCF presets
  t += begin_new_line("NoSpherA2_XCW", "4") + \
       _xcw_combo("scf", "SCF", "scf_preset", "sloppy;normal;tight;very_tight", 7, 19) + \
       _xcw_combo("conv", "Convergence", "conv_preset", "slow_conv;normal_conv;fast_conv", 17, 22) + \
       _xcw_text("max_iter", "Max Iter", "max_iter", 13, 10) + \
       end_line()
  # resources
  t += begin_new_line("NoSpherA2_XCW", "5") + \
       labeled_combo("NoSpherA2_XCW_cpus@refine", "CPUs", "spy.NoSpherA2.getCPUListStr()",
                     "spy.nsa2_get_param('ncpus')",
                     "spy.nsa2_set_param('ncpus', html.GetValue('~name~'))",
                     width_label=8, width_combo=10) + \
       labeled_text("NoSpherA2_XCW_mem@refine", "Mem(Gb)",
                    "spy.nsa2_get_param('mem')",
                    "spy.nsa2_set_param('mem', html.GetValue('~name~'))",
                    width_label=12, width_textbox=12) + \
       _xcw_checkbox("use_gpu", "GPU", "use_gpu", 8) + \
       _xcw_text("i_tensor_mb", "I Tensor MB", "i_tensor_mb", 16, 12) + \
       "<td width='21%'></td>" + \
       end_line()
  # run options: the -xcw_* command line flags
  t += begin_new_line("NoSpherA2_XCW", "6") + \
       _xcw_checkbox("gaussian_halt", "Gaussian Halt", "gaussian_halt", 19) + \
       _xcw_checkbox("incremental", "Incremental", "incremental", 17) + \
       _xcw_checkbox("extrapolate", "Extrapolate", "extrapolate", 17) + \
       _xcw_checkbox("tshb", ".tshb", "tshb", 12) + \
       _xcw_combo("partition", "Partition", "partition", "hirshfeld;becke;tfvc;mbis;embis;ri", 14, 18) + \
       end_line()
  t += begin_new_line("NoSpherA2_XCW", "7") + \
       _xcw_text("strong_cutoff", "Strong I/&sigma;", "strong_cutoff", 15, 12) + \
       _xcw_text("int_precision", "Int. Precision", "int_precision", 19, 12) + \
       "<td width='42%'></td>" + \
       end_line()
  # free text appended to the settings file, for keywords the GUI has no control for
  t += begin_new_line("NoSpherA2_XCW", "8") + \
       _xcw_text("extra", "Extra Settings", "extra_settings", 19, 75) + \
       end_line()
  # action row: run, stop, status and the table picker of the last run
  t += begin_new_line("NoSpherA2_XCW", "9") + \
       button("NoSpherA2_XCW_run", "Run XCW", "spy.NoSpherA2.xcw_run() >> html.Update()", width=12,
              hint="Write the settings file and start NoSpherA2 -do_XCW in the background") + \
       button("NoSpherA2_XCW_stop", "Stop", "spy.NoSpherA2.xcw_stop() >> html.Update()", width=8,
              hint="Kill the running XCW job") + \
       f"<td width='34%' align='left'><i>{xcw_status()}</i></td>"
  tscbs = xcw_tscb_list()
  if tscbs:
    t += _xcw_combo("tscb", "Table", "selected_tscb", tscbs, 8, 24) + \
         button("NoSpherA2_XCW_use", "Use", "spy.NoSpherA2.xcw_use_tscb() >> html.Update()", width=8,
                hint="Copy the chosen NA2_<lambda>.tscb/.tshb next to the structure and make it the tsc source")
  else:
    t += "<td width='40%'></td>"
  t += end_line()
  return t
