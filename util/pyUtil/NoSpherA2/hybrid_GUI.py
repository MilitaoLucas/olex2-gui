from functools import lru_cache
from typing import List, Optional

import htmlTools
import olx
from NoSpherA2.olx_gui.components.item_component import Ignore, LabeledGeneralComponent, Filler
from NoSpherA2.olx_gui.dominate.tags import p, td
from olexFunctions import OV
from utilities import make_quick_button_gui, is_disordered
import ast
import textwrap
from utilities import software
import os
import sys
import inspect
from contextlib import contextmanager

@contextmanager
def local_chdir(directory: str):
  """
  This changes the directory just for the context. So you don't change the global directory of the script
  """
  prev_cwd = os.getcwd()
  os.chdir(directory)
  try:
    yield
  finally:
    os.chdir(prev_cwd)

@lru_cache(maxsize=None) # This doesn't change, so there is no reason to run it more than once.
def setup_software_static(exe_pre: str):
  """The setup_software in NoSpherA2 class is kind of annoying to deal with, so this does the same thing but returns
  the exe path instead of modifying the class
  """
  # Determine platform-specific executable name
  exe_name = exe_pre + (".exe" if sys.platform.startswith("win") else "")
  # Changedir to BaseDir() before
  with local_chdir(OV.BaseDir()):
    exe_path = olx.file.Which(exe_name)
  return exe_path

@lru_cache(maxsize=None) # This doesn't change, so there is no reason to run it more than once.
def get_cpu_list_static():
  soft = software()
  import multiprocessing
  max_cpu = multiprocessing.cpu_count()
  cpu_list = ['1',]
  hyperthreading = OV.GetParam('user.refinement.has_HT')
  if hyperthreading:
    max_cpu /= 2
  for n in range(1, int(max_cpu)):
    cpu_list.append(str(n + 1))
  # ORCA and Tonto rely on MPI, so only make it available if mpiexec is found
  if soft == "Tonto" or "ORCA" in soft or soft == "fragHAR":
    if not os.path.exists(setup_software_static("mpiexec")):
      return '1'
  # otherwise allow more CPUs
  return ';'.join(cpu_list)

def patch_function_inplace(module, func_name, old_text, new_text):
    # 1. Get the old function object
    old_func = getattr(module, func_name)

    # 2. Get source and modify it
    source = inspect.getsource(old_func)
    new_source = source.replace(old_text, new_text)

    # 3. Compile the new function temporarily
    # We create a temporary scope to hold the new function
    temp_scope = module.__dict__.copy()
    exec(new_source, temp_scope)
    new_func = temp_scope[func_name]

    # 4. SWAP THE INTERNALS (The Magic Step)
    # We overwrite the __code__ object of the old function
    old_func.__code__ = new_func.__code__

def replace_function_in_file(file_path, func_name, new_code):
    """
    Replaces a function definition in a file with new code.

    :param file_path: Path to the .py file
    :param func_name: Name of the function to replace (string)
    :param new_code: The new source code as a string
    """
    # 1. Read the file
    with open(file_path, "r") as f:
        source_lines = f.readlines()

    source_text = "".join(source_lines)
    tree = ast.parse(source_text)

    # 2. Find the target function node
    target_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            target_node = node
            break

    if not target_node:
        raise ValueError(f"Function '{func_name}' not found in {file_path}")

    # 3. Determine Start/End Lines
    # Handle decorators: if present, the function starts at the first decorator
    if target_node.decorator_list:
        start_line = target_node.decorator_list[0].lineno - 1
    else:
        start_line = target_node.lineno - 1

    end_line = target_node.end_lineno  # Available in Python 3.8+

    # 4. Handle Indentation
    # We grab the indentation from the first line of the original function
    original_indent = source_lines[start_line][: -len(source_lines[start_line].lstrip())]

    # We strip the new code of its own common indentation, then apply the original file's indentation
    # This ensures that if you paste a top-level function into a class, it gets indented correctly.
    dedented_new_code = textwrap.dedent(new_code).strip()
    indented_new_code = textwrap.indent(dedented_new_code, original_indent)

    # 5. Reconstruct the file content
    # Everything before the function + New Code + Everything after the function
    new_file_content = (
        "".join(source_lines[:start_line]) +
        indented_new_code + "\n" +
        "".join(source_lines[end_line:])
    )

    # 6. Write back to disk
    with open(file_path, "w") as f:
        f.write(new_file_content)

    print(f"Successfully replaced '{func_name}' in {file_path}")

def begin_new_line(help_label="NoSpherA2_Options_1", scope="1"):
  return f'''<tr ALIGN='left' NAME='SNUM_REFINEMENT_NSFF' width='100%'>
  <td valign='top' width="$GetVar(HtmlTableFirstcolWidth)" align='center' bgcolor="$GetVar(HtmlTableFirstcolColour)">
  {htmlTools.MakeHoverButton(f'btn-info@{help_label}{scope}',f"spy.make_help_box -name='{help_label}' -popout='False' -helpTxt='Options'")}
  </td>
  <td colspan="1">
    <table border="0" width="100%" cellpadding="1" cellspacing="1" Xbgcolor="#ffaaaa">
      <tr Xbgcolor="#aaffaa">'''

def end_line():
  return '''
      </tr>
    </table>
  </td>
</tr>'''

_ACTIVE_MANAGER: Optional['LineManager'] = None
_ACTIVE_LINE: Optional['Line'] = None

class LineManager:
  def __init__(self):
    self.lines = []
    self.combined_strings = ""

  def __enter__(self):
    global _ACTIVE_MANAGER
    if _ACTIVE_MANAGER is not None:
      raise RuntimeError("Nesting LineManagers is not allowed!")

    _ACTIVE_MANAGER = self
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    global _ACTIVE_MANAGER
    _ACTIVE_MANAGER = None

    for line in self.lines:
      self.combined_strings += line.line_str

  def __str__(self):
    return self.combined_strings

  def __repr__(self):
    return str(self)

class Line:
  def __init__(self, help_label="NoSpherA2_Options_1", scope="1"):
    self.help_label = help_label
    self.scope = scope
    self.line_str = ""
    self.components = []

    if _ACTIVE_MANAGER is None:
      raise RuntimeError("Called Line() outside of a LineManager!")

    _ACTIVE_MANAGER.lines.append(self)

  def __enter__(self):
    global _ACTIVE_LINE
    if _ACTIVE_LINE is not None:
      raise RuntimeError("Nesting Lines is not allowed!")

    self.line_str = begin_new_line(self.help_label, self.scope)
    _ACTIVE_LINE = self
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    global _ACTIVE_LINE
    _ACTIVE_LINE = None

    for comp in self.components:
      self.line_str += comp
    self.line_str += end_line()

def lw(component_str: str):
  if _ACTIVE_LINE is None:
    raise RuntimeError("Called lw() outside of a Line!")
  _ACTIVE_LINE.components.append(component_str)


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

def checkbox(name,label,checked,oncheck,onuncheck):
  return f'''<font size="$GetVar('HtmlFontSizeControls')">
    <input
      type="checkbox"
      height="GetVar('HtmlInputHeight')"
      fgcolor="GetVar(HtmlFontColour)"
      bgcolor="GetVar(HtmlTableRowBgColour)"
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

def method_combo():
  return labeled_combo("NoSpherA2_method@refine",                                          
                      "Method",
                      "spy.NoSpherA2.get_functional_list()",
                      "spy.GetParam(\'snum.NoSpherA2.method\')",
                      "spy.SetParam(\'snum.NoSpherA2.method\',html.GetValue(\'~name~\'))",
                      width_label=11, width_combo=17)

def basis_combo():
  return labeled_combo("NoSpherA2_basis@refine",
                      "Basis Set",
                      "spy.NoSpherA2.getBasisListStr()",
                      "spy.GetParam(\'snum.NoSpherA2.basis_name\')",
                      "spy.SetParam(\'snum.NoSpherA2.basis_name\',html.GetValue(\'~name~\')) >> html.Update()",
                      width_label=12, width_combo=19)

def cpu_combo():
  return labeled_combo("NoSpherA2_cpus@refine",
                      "CPUs",
                      "spy.NoSpherA2.getCPUListStr()",
                      "spy.GetParam(\'snum.NoSpherA2.ncpus\')",
                      "spy.SetParam(\'snum.NoSpherA2.ncpus\', html.GetValue(\'~name~\'))",
                      width_label=8, width_combo=10)

def memory_text():
  return labeled_text("NosPherA2_Memory",
                      "Mem(Gb)",
                      "spy.GetParam('snum.NoSpherA2.mem')",
                      "spy.SetParam('snum.NoSpherA2.mem', html.GetValue('~name~'))",
                      width_label=10, width_textbox=20)
  
def charge_spin():
  return labeled_spin("NoSpherA2_Charge@refine",
                      "Charge",
                      "spy.GetParam(\'snum.NoSpherA2.charge\')",
                      "spy.SetParam(\'snum.NoSpherA2.charge\',html.GetValue(\'~name~\'))",
                      width_label=11, width_spinbox=9, min_value=-1000, max_value=1000)
  
def multiplicity_spin():
  return labeled_spin("NoSpherA2_Multiplicity@refine",
                      "Multiplicity",
                      "spy.GetParam(\'snum.NoSpherA2.multiplicity\')",
                      "spy.SetParam(\'snum.NoSpherA2.multiplicity\',html.GetValue(\'~name~\'))",
                      width_label=14, width_spinbox=9, min_value=1, max_value=200)
  
def iterative_checkbox():
  return labeled_checkbox("NoSpherA2_Iterative@refine",
                         "Iterative",
                         "spy.GetParam(\'snum.NoSpherA2.full_HAR\')",
                         "spy.SetParam(\'snum.NoSpherA2.full_HAR\',\'True\')>>html.Update()",
                         "spy.SetParam(\'snum.NoSpherA2.full_HAR\',\'False\')>>html.Update()",
                         width=15)

def cycles_spin():
  return labeled_spin("NoSpherA2_Max_HAR_Cycles@refine",
                      "Max Cycles",
                      "spy.GetParam(\'snum.NoSpherA2.Max_HAR_Cycles\')",
                      "spy.SetParam(\'snum.NoSpherA2.Max_HAR_Cycles\',html.GetValue(\'~name~\'))",
                      width_label=17, width_spinbox=8, min_value=1, max_value=100)
  
def update_tsc_button():
  return button("Update_TSC",
                "Update .tsc",
                "spy.NoSpherA2.launch() >> html.Update()",
                width=10,
                hint="Generate new .tsc file with current settings")

def integration_accuracy_combo():
  return labeled_combo("NoSpherA2_becke_accuracy@refine",
                        "Integr. Accuracy",
                        "'Low;Normal;High;Max'",
                        "spy.GetParam(\'snum.NoSpherA2.becke_accuracy\')",
                        "spy.SetParam(\'snum.NoSpherA2.becke_accuracy\', html.GetValue(\'~name~\'))",
                        width_label=19, width_combo=15)
  
def relativistics_checkbox():
  return labeled_checkbox("NoSpherA2_Relativistics@refine",
                         "Relativitics",
                         "spy.GetParam(\'snum.NoSpherA2.Relativistic\')",
                         "spy.SetParam(\'snum.NoSpherA2.Relativistic\',\'True\')",
                         "spy.SetParam(\'snum.NoSpherA2.Relativistic\',\'False\')",
                         width=18)

def h_aniso_checkbox():
  return labeled_checkbox("NoSpherA2_H_Aniso@refine",
                         "H Aniso",
                         "spy.GetParam(\'snum.NoSpherA2.h_aniso\')",
                         "spy.SetParam(\'snum.NoSpherA2.h_aniso\',\'True\')",
                         "spy.SetParam(\'snum.NoSpherA2.h_aniso\',\'False\')",
                         width=18)
  
def no_afix_checkbox():
  return labeled_checkbox("NoSpherA2_Afix_remove@refine",
                         "No Afix",
                         "spy.GetParam(\'snum.NoSpherA2.h_afix\')",
                         "spy.SetParam(\'snum.NoSpherA2.h_afix\',\'True\')",
                         "spy.SetParam(\'snum.NoSpherA2.h_afix\',\'False\')",
                         width=20)

def disorder_groups_text():
  return begin_new_line("NoSpherA2_Options_Grouped_Parts") + labeled_text("NoSpherA2_grouped_parts@refine",
                      "Grouped Parts",
                      "spy.GetParam('snum.NoSpherA2.Disorder_Groups')",
                      "spy.SetParam('snum.NoSpherA2.Disorder_Groups', html.GetValue('~name~'))",
                      width_label=20, width_textbox=20) + end_line()

def pyscf_damping():
  return labeled_combo("NoSpherA2_Hybrid_pySCF_Damping@refine",
                      "Damping",
                      "'0.6;0.7;0.85;0.93'",
                      "spy.GetParam('snum.NoSpherA2.Hybrid.pySCF_Damping')",
                      "spy.SetParam('snum.NoSpherA2.Hybrid.pySCF_Damping', html.GetValue('~name~'))",
                      width_label=15, width_combo=20)

def pyscf_solvation():
  return labeled_combo("NoSpherA2_ORCA_Solvation@refine",
                      "Solvation",
                      "'Vacuum;Water;Acetonitrile;Methanol;Ethanol;IsoQuinoline;Quinoline;Chloroform;DiethylEther;Dichloromethane;DiChloroEthane;CarbonTetraChloride;Benzene;Toluene;ChloroBenzene;NitroMethane;Heptane;CycloHexane;Aniline;Acetone;TetraHydroFuran;DiMethylSulfoxide;Argon;Krypton;Xenon;n-Octanol;1,1,1-TriChloroEthane;1,1,2-TriChloroEthane;1,2,4-TriMethylBenzene;1,2-DiBromoEthane;1,2-EthaneDiol;1,4-Dioxane;1-Bromo-2-MethylPropane;1-BromoOctane;1-BromoPentane;1-BromoPropane;1-Butanol;1-ChloroHexane;1-ChloroPentane;1-ChloroPropane;1-Decanol;1-FluoroOctane;1-Heptanol;1-Hexanol;1-Hexene;1-Hexyne;1-IodoButane;1-IodoHexaDecane;1-IodoPentane;1-IodoPropane;1-NitroPropane;1-Nonanol;1-Pentanol;1-Pentene;1-Propanol;2,2,2-TriFluoroEthanol;2,2,4-TriMethylPentane;2,4-DiMethylPentane;2,4-DiMethylPyridine;2,6-DiMethylPyridine;2-BromoPropane;2-Butanol;2-ChloroButane;2-Heptanone;2-Hexanone;2-MethoxyEthanol;2-Methyl-1-Propanol;2-Methyl-2-Propanol;2-MethylPentane;2-MethylPyridine;2-NitroPropane;2-Octanone;2-Pentanone;2-Propanol;2-Propen-1-ol;3-MethylPyridine;3-Pentanone;4-Heptanone;4-Methyl-2-Pentanone;4-MethylPyridine;5-Nonanone;AceticAcid;AcetoPhenone;a-ChloroToluene;Anisole;Benzaldehyde;BenzoNitrile;BenzylAlcohol;BromoBenzene;BromoEthane;Bromoform;Butanal;ButanoicAcid;Butanone;ButanoNitrile;ButylAmine;ButylEthanoate;CarbonDiSulfide;Cis-1,2-DiMethylCycloHexane;Cis-Decalin;CycloHexanone;CycloPentane;CycloPentanol;CycloPentanone;Decalin-mixture;DiBromomEthane;DiButylEther;DiEthylAmine;DiEthylSulfide;DiIodoMethane;DiIsoPropylEther;DiMethylDiSulfide;DiPhenylEther;DiPropylAmine;e-1,2-DiChloroEthene;e-2-Pentene;EthaneThiol;EthylBenzene;EthylEthanoate;EthylMethanoate;EthylPhenylEther;FluoroBenzene;Formamide;FormicAcid;HexanoicAcid;IodoBenzene;IodoEthane;IodoMethane;IsoPropylBenzene;m-Cresol;Mesitylene;MethylBenzoate;MethylButanoate;MethylCycloHexane;MethylEthanoate;MethylMethanoate;MethylPropanoate;m-Xylene;n-ButylBenzene;n-Decane;n-Dodecane;n-Hexadecane;n-Hexane;NitroBenzene;NitroEthane;n-MethylAniline;n-MethylFormamide-mixture;n,n-DiMethylAcetamide;n,n-DiMethylFormamide;n-Nonane;n-Octane;n-Pentadecane;n-Pentane;n-Undecane;o-ChloroToluene;o-Cresol;o-DiChloroBenzene;o-NitroToluene;o-Xylene;Pentanal;PentanoicAcid;PentylAmine;PentylEthanoate;PerFluoroBenzene;p-IsoPropylToluene;Propanal;PropanoicAcid;PropanoNitrile;PropylAmine;PropylEthanoate;p-Xylene;Pyridine;sec-ButylBenzene;tert-ButylBenzene;TetraChloroEthene;TetraHydroThiophene-s,s-dioxide;Tetralin;Thiophene;Thiophenol;trans-Decalin;TriButylPhosphate;TriChloroEthene;TriEthylAmine;Xylene-mixture;z-1,2-DiChloroEthene'",
                      "spy.GetParam('snum.NoSpherA2.ORCA_Solvation')",
                      "spy.SetParam('snum.NoSpherA2.ORCA_Solvation', html.GetValue('~name~'))",
                      width_label=13, width_combo=30)
  
def partitioning_scheme_line():
  if OV.GetParam('user.NoSpherA2.show_partitioning') != True:
    return ""
  temp = begin_new_line("NoSpherA2_Options_RIFit") + \
          labeled_combo("NoSpherA2_partitioning_scheme@refine",
                        "Partitioning Scheme",
                        "'Hirshfeld;RI-Fit;TFVC;Becke'",
                        "spy.GetParam('snum.NoSpherA2.NoSpherA2_Partition')",
                        "spy.SetParam('snum.NoSpherA2.NoSpherA2_Partition', html.GetValue('~name~')) >> html.Update()",
                        width_label=24, width_combo=16)
  if OV.GetParam('snum.NoSpherA2.NoSpherA2_Partition') == "RI-Fit":
      temp += labeled_combo("NoSpherA2_Aux_basis@refine",
                          "Auxiliary Basis",
                          "auto;combo_basis_fit;def2_universal_jkfit;def2_universal_jfit;def2_svp_rifit;hgbsp3_7;def2_qzvppd_rifit;tzvp_jkfit;cc-pvqz-jkfit",
                          "spy.GetParam('snum.NoSpherA2.auxiliary_basis')",
                          "spy.SetParam('snum.NoSpherA2.auxiliary_basis', html.GetValue('~name~')) >> html.Update()",
                          width_label=18, width_combo=25)
      if OV.GetParam('snum.NoSpherA2.auxiliary_basis') == "auto":
          temp += labeled_text("NoSpherA2_custom_aux_basis@refine",
                              "Beta",
                              "spy.GetParam('snum.NoSpherA2.auxiliary_basis_beta')",
                              "spy.SetParam('snum.NoSpherA2.auxiliary_basis_beta', html.GetValue('~name~'))",
                              width_label=8, width_textbox=10)
      else:
        temp += "<td width='18%'></td>"
  else:
      temp += "<td width='43%'></td>"
  temp += end_line()
  return temp

def WSL_distro():
  return labeled_combo("NoSpherA2_WSL_distro@refine",
                      "WSL Distro",
                      "spy.NoSpherA2.get_distro_list()",
                      "spy.GetParam('snum.NoSpherA2.distro')",
                      "spy.SetParam('snum.NoSpherA2.distro', html.GetValue('~name~'))",
                      width_label=15, width_combo=30)

def make_hybrid_GUI(softwares_list_string):
  parts = OV.ListParts()
  if parts != None:
    parts = list(parts)
  if len(parts) <= 1:
    return begin_new_line() + "Hybrid is not possible with less than two parts!" + end_line()
  t = begin_new_line() + \
      cpu_combo() + \
      memory_text() + \
      iterative_checkbox()
  full_har = OV.GetParam('snum.NoSpherA2.full_HAR')
  if full_har == True:
    t += cycles_spin()
  else:
    t += update_tsc_button()

  
  t += end_line() + begin_new_line() + integration_accuracy_combo() + h_aniso_checkbox() + no_afix_checkbox() + end_line()
  t += end_line() + begin_new_line("NoSpherA2_Options_3") + integration_accuracy_combo() + h_aniso_checkbox() + no_afix_checkbox() + end_line() + partitioning_scheme_line()
  for i in parts:
    if i == 0:
      continue
    t += begin_new_line() + "<td width='63%' align='center'>" + "<b>Part %d</b></td>"%i
    softwares_list = "Please Select" + str(softwares_list_string).replace("Hybrid;","")
    t += labeled_combo(
      "NoSpherA2_software_Part%d@refine"%(i+1),
      "Software",
      softwares_list,
      "spy.GetParam(\'snum.NoSpherA2.Hybrid.software_Part%d\')"%i, 
      "spy.SetParam(\'snum.NoSpherA2.Hybrid.software_Part%d\',html.GetValue(\'~name~\'))>>html.Update()"%i)
    selected_software = OV.GetParam('snum.NoSpherA2.Hybrid.software_Part%d'%i)
    t += end_line() + begin_new_line("NoSpherA2_Options_2")
    if selected_software != "  " + str(OV.GetParam('user.NoSpherA2.discamb_exe')):
      if selected_software != "ELMOdb":
        t += labeled_combo(
          "NoSpherA2_basis_Part%d@refine"%i,
          "Basis Set",
          "spy.NoSpherA2.getBasisListStr()", 
          "spy.GetParam(\'snum.NoSpherA2.Hybrid.basis_name_Part%d\')"%i,
          "spy.SetParam(\'snum.NoSpherA2.Hybrid.basis_name_Part%d\',html.GetValue(\'~name~\'))"%i,
          13, 20)
        t += labeled_combo(
          "NoSpherA2_method_Part%d@refine"%i, 
          "Method",
          "spy.NoSpherA2.get_functional_list(spy.GetParam(\'snum.NoSpherA2.Hybrid.software_Part%d\'))"%i, 
          "spy.GetParam(\'snum.NoSpherA2.Hybrid.method_Part%d\')"%i,
          "spy.SetParam(\'snum.NoSpherA2.Hybrid.method_Part%d\',html.GetValue(\'~name~\'))"%i,
          11, 20)
        t += labeled_checkbox("NoSpherA2_ORCA_Relativistics_PART%d@refine"%i, 
                      "Relativitics", 
                      "spy.GetParam(\'snum.NoSpherA2.Hybrid.Relativistic_Part%d\')"%i, 
                      "spy.SetParam(\'snum.NoSpherA2.Hybrid.Relativistic_Part%d\',\'True\')"%i, 
                      "spy.SetParam(\'snum.NoSpherA2.Hybrid.Relativistic_Part%d\',\'False\')"%i)        
        t += end_line() + \
             begin_new_line() + \
             labeled_spin("SET_CHARGE_PART%d@refine"%i,
                                                          "Charge",
                      "spy.GetParam(\'snum.NoSpherA2.Hybrid.charge_Part%d\')"%i,
                      "spy.SetParam(\'snum.NoSpherA2.Hybrid.charge_Part%d\',html.GetValue(\'~name~\'))"%i,
                      width_label=13, width_spinbox=8, min_value=-1000, max_value=1000) + \
             labeled_spin("SET_MULTIPLICITY_PART%d@refine"%i,
                      "Multiplicity",
                      "spy.GetParam(\'snum.NoSpherA2.Hybrid.multiplicity_Part%d\')"%i,
                      "spy.SetParam(\'snum.NoSpherA2.Hybrid.multiplicity_Part%d\',html.GetValue(\'~name~\'))"%i,
                      width_label=16, width_spinbox=8, min_value=1, max_value=200)
        if "ORCA" in selected_software:
          t += end_line() + begin_new_line() + \
               labeled_combo("NoSpherA2_ORCA_SCF_Conv_Part%d@refine"%i,
                             "SCF Thresh.",
                           "\'NoSpherA2SCF;SloppySCF;LooseSCF;NormalSCF;StrongSCF;TightSCF;VeryTightSCF;ExtremeSCF\'",
                           "spy.GetParam(\'snum.NoSpherA2.Hybrid.ORCA_SCF_Conv_Part%d\')"%i,
                           "spy.SetParam(\'snum.NoSpherA2.Hybrid.ORCA_SCF_Conv_Part%d', html.GetValue(\'~name~\'))"%i,
                           17, 20)
          t += labeled_combo("NoSpherA2_ORCA_SCF_Strategy_Part%d@refine"%i,
                             "SCF Strategy",
                           "\'EasyConv;NormalConv;SlowConv;VerySlowConv\'",
                           "spy.GetParam(\'snum.NoSpherA2.Hybrid.ORCA_SCF_Strategy_Part%d\')"%i,
                           "spy.SetParam(\'snum.NoSpherA2.Hybrid.ORCA_SCF_Strategy_Part%d\', html.GetValue(\'~name~\'))"%i,
                           17, 20)
          t += labeled_combo("NoSpherA2_ORCA_Solvation@refine",
                             "Solvation",
                           "\'Vacuum;Water;Acetone;Acetonitrile;Ammonia;Benzene;CCl4;CH2CL2;Chloroform;Cyclohexane;DMF;DMSO;Ethanol;Hexane;Methanol;Octanol;Pyridine;THF;Toluene\'",
                           "spy.GetParam(\'snum.NoSpherA2.ORCA_Solvation\')",
                           "spy.SetParam(\'snum.NoSpherA2.ORCA_Solvation\', html.GetValue(\'~name~\'))",
                           13, 20)
        elif "pySCF" in selected_software:
          t += end_line() + begin_new_line() + \
               labeled_combo("NoSpherA2_Hybrid_pySCF_Damping_Part%d@refine"%i,
                             "Damping",
                           "\'0.6;0.7;0.85;0.93\'",
                           "spy.GetParam(\'snum.NoSpherA2.Hybrid.pySCF_Damping_Part%d\')"%i,
                           "spy.SetParam(\'snum.NoSpherA2.Hybrid.pySCF_Damping_Part%d\', html.GetValue(\'~name~\'))"%i,
                           10, 10) + \
               labeled_combo("NoSpherA2_pyscf_Solvation@refine",
                           "Solvation"
                           "\'Vacuum;Water; Acetonitrile;Methanol;Ethanol;IsoQuinoline;Quinoline;Chloroform;DiethylEther;Dichloromethane;DiChloroEthane;CarbonTetraChloride;Benzene;Toluene;ChloroBenzene;NitroMethane;Heptane;CycloHexane;Aniline;Acetone;TetraHydroFuran;DiMethylSulfoxide;Argon;Krypton;Xenon;n-Octanol;1,1,1-TriChloroEthane;1,1,2-TriChloroEthane;1,2,4-TriMethylBenzene;1,2-DiBromoEthane;1,2-EthaneDiol;1,4-Dioxane;1-Bromo-2-MethylPropane;1-BromoOctane;1-BromoPentane;1-BromoPropane;1-Butanol;1-ChloroHexane;1-ChloroPentane;1-ChloroPropane;1-Decanol;1-FluoroOctane;1-Heptanol;1-Hexanol;1-Hexene;1-Hexyne;1-IodoButane;1-IodoHexaDecane;1-IodoPentane;1-IodoPropane;1-NitroPropane;1-Nonanol;1-Pentanol;1-Pentene;1-Propanol;2,2,2-TriFluoroEthanol;2,2,4-TriMethylPentane;2,4-DiMethylPentane;2,4-DiMethylPyridine;2,6-DiMethylPyridine;2-BromoPropane;2-Butanol;2-ChloroButane;2-Heptanone;2-Hexanone;2-MethoxyEthanol;2-Methyl-1-Propanol;2-Methyl-2-Propanol;2-MethylPentane;2-MethylPyridine;2-NitroPropane;2-Octanone;2-Pentanone;2-Propanol;2-Propen-1-ol;3-MethylPyridine;3-Pentanone;4-Heptanone;4-Methyl-2-Pentanone;4-MethylPyridine;5-Nonanone;AceticAcid;AcetoPhenone;a-ChloroToluene;Anisole;Benzaldehyde;BenzoNitrile;BenzylAlcohol;BromoBenzene;BromoEthane;Bromoform;Butanal;ButanoicAcid;Butanone;ButanoNitrile;ButylAmine;ButylEthanoate;CarbonDiSulfide;Cis-1,2-DiMethylCycloHexane;Cis-Decalin;CycloHexanone;CycloPentane;CycloPentanol;CycloPentanone;Decalin-mixture;DiBromomEthane;DiButylEther;DiEthylAmine;DiEthylSulfide;DiIodoMethane;DiIsoPropylEther;DiMethylDiSulfide;DiPhenylEther;DiPropylAmine;e-1,2-DiChloroEthene;e-2-Pentene;EthaneThiol;EthylBenzene;EthylEthanoate;EthylMethanoate;EthylPhenylEther;FluoroBenzene;Formamide;FormicAcid;HexanoicAcid;IodoBenzene;IodoEthane;IodoMethane;IsoPropylBenzene;m-Cresol;Mesitylene;MethylBenzoate;MethylButanoate;MethylCycloHexane;MethylEthanoate;MethylMethanoate;MethylPropanoate;m-Xylene;n-ButylBenzene;n-Decane;n-Dodecane;n-Hexadecane;n-Hexane;NitroBenzene;NitroEthane;n-MethylAniline;n-MethylFormamide-mixture;n,n-DiMethylAcetamide;n,n-DiMethylFormamide;n-Nonane;n-Octane;n-Pentadecane;n-Pentane;n-Undecane;o-ChloroToluene;o-Cresol;o-DiChloroBenzene;o-NitroToluene;o-Xylene;Pentanal;PentanoicAcid;PentylAmine;PentylEthanoate;PerFluoroBenzene;p-IsoPropylToluene;Propanal;PropanoicAcid;PropanoNitrile;PropylAmine;PropylEthanoate;p-Xylene;Pyridine;sec-ButylBenzene;tert-ButylBenzene;TetraChloroEthene;TetraHydroThiophene-s,s-dioxide;Tetralin;Thiophene;Thiophenol;trans-Decalin;TriButylPhosphate;TriChloroEthene;TriEthylAmine;Xylene-mixture;z-1,2-DiChloroEthene\'",
                           "spy.GetParam(\'snum.NoSpherA2.ORCA_Solvation\')",
                           "spy.SetParam(\'snum.NoSpherA2.ORCA_Solvation\', html.GetValue(\'~name~\'))",
                           13, 30)
      else:
        #HAVE TO FINISCH ELMO LATER
        t += labeled_combo(
          "NoSpherA2_basis_Part%d@refine"%i,
          "Basis Set",
          "'6-31G;6-31G**;6-311G;6-311G**;cc-pVDZ;extrabasis'", 
          "spy.GetParam(\'snum.NoSpherA2.Hybrid.basis_name_Part%d\')"%i,
          "spy.SetParam(\'snum.NoSpherA2.Hybrid.basis_name_Part%d\',html.GetValue(\'~name~\'))"%i,
          13, 20)
      
      t += end_line()
    else:
      t += "<td align='center'><b>So far no further options for discambMATT</b></td>" + end_line()
  
  return t

def make_xtb_GUI():
  # Method, CPUs, Memory
  t = begin_new_line() + method_combo() + cpu_combo() + memory_text() + end_line()
  # Charge, Multiplicity, iterative and Update/Max cycles
  t += begin_new_line("NoSpherA2_Options_2") + \
        charge_spin() + \
        multiplicity_spin() + \
        iterative_checkbox()
  full_har = OV.GetParam('snum.NoSpherA2.full_HAR')
  if full_har == False:
    t += update_tsc_button()
  else:
    t += cycles_spin()
  t += end_line()
  # Integration Accuracy, H Aniso, No Afix
  t += begin_new_line("NoSpherA2_Options_3") + \
        integration_accuracy_combo() + \
        labeled_text("NoSpherA2_xtb_temp@refine",
                      "Temp. (K)",
                      "spy.GetParam('snum.NoSpherA2.temperature')",
                      "spy.SetParam('snum.NoSpherA2.temperature', html.GetValue('~name~'))",
                      width_label=15, width_textbox=9) + \
        h_aniso_checkbox() + \
        no_afix_checkbox() + \
        end_line()
  t += partitioning_scheme_line()
  return t

def make_ptb_GUI():
  # CPUs, Memory, Purification
  t = begin_new_line() + cpu_combo() + memory_text() + \
    labeled_checkbox("NoSpherA2_purification@refine",
                     "Purify",
                     "spy.GetParam('snum.NoSpherA2.PTB_use_purify')",
                     "spy.SetParam('snum.NoSpherA2.PTB_use_purify', True) >> html.Update()",
                     "spy.SetParam('snum.NoSpherA2.PTB_use_purify', False) >> html.Update()",
                     width=2) +\
    end_line()
  # Charge, Multiplicity, iterative and Update/Max cycles
  t += begin_new_line("NoSpherA2_Options_2") + charge_spin() + multiplicity_spin() + iterative_checkbox()
  iterative = OV.GetParam('snum.NoSpherA2.full_HAR')
  if iterative == False:
    t += update_tsc_button()
  else:
    t += cycles_spin()
  t += end_line()
  # Integration Accuracy, H Aniso, No Afix
  t += begin_new_line("NoSpherA2_Options_3") + \
        integration_accuracy_combo() + \
        h_aniso_checkbox() + \
        no_afix_checkbox() + \
        end_line()
  if is_disordered():
    t += disorder_groups_text()
  t += partitioning_scheme_line()
  return t

def make_SALTED_GUI():
  #Model, add, delete buttons & CPUs
  t = begin_new_line() + \
    labeled_combo("NoSpherA2_SALTED_model@refine",
                  "Model",
                  "spy.NoSpherA2.get_SALTED_model_locations()",
                  "spy.GetParam('snum.NoSpherA2.selected_salted_model')",
                  "spy.SetParam('snum.NoSpherA2.selected_salted_model', html.GetValue('~name~'))",
                  width_label=10, width_combo=50) + \
    f"<td width='5%' align='left'>{htmlTools.MakeHoverButton('toolbar-open','spy.NoSpherA2.appendDir(user.NoSpherA2.salted_models_list) >> html.Update()', 'on')}</td>" + \
    f"<td width='5%' align='left'>{htmlTools.MakeHoverButton('toolbar-delete','spy.NoSpherA2.removeDir(user.NoSpherA2.salted_models_list, html.GetValue(NoSpherA2_SALTED_model@refine)) >> html.Update()', 'on')}</td>" + \
  cpu_combo() + \
  end_line()
  return t

def make_Thakkar_GUI():
  # Cations & Anions, update button
  return begin_new_line() + \
    labeled_text("NoSpherA2_Thakkar_cations@refine",
                  "Cations",
                  "spy.GetParam('snum.NoSpherA2.Thakkar_Cations')",
                  "spy.SetParam('snum.NoSpherA2.Thakkar_Cations', html.GetValue('~name~'))",
                  width_label=15, width_textbox=25) + \
    labeled_text("NoSpherA2_Thakkar_anions@refine",
                  "Anions",
                  "spy.GetParam('snum.NoSpherA2.Thakkar_Anions')",
                  "spy.SetParam('snum.NoSpherA2.Thakkar_Anions', html.GetValue('~name~'))",
                  width_label=15, width_textbox=25) + \
    button("Update_Thakkar_Model",
            "Update Model",
            "spy.NoSpherA2.launch() >> html.Update()",
            width=20,
            hint="Generate new Thakkar model with current settings") + end_line()

def make_ELMOdb_GUI():
  # Basis Set, CPUs, Memory
  t = begin_new_line() + \
    labeled_combo("NoSpherA2_basis@refine",
                  "Basis Set",
                  "'6-31G;6-31G**;6-311G;6-311G**;cc-pVDZ;extrabasis'",
                  "spy.GetParam('snum.NoSpherA2.basis_name')",
                  "spy.SetParam('snum.NoSpherA2.basis_name', html.GetValue('~name~'))",
                  width_label=15, width_combo=50) + \
      cpu_combo() + memory_text() + end_line()
  # Charge, Multiplicity, iterative and Update/Max cycles
  t += begin_new_line("NoSpherA2_Options_2") + charge_spin() + multiplicity_spin() + iterative_checkbox()
  iterative = OV.GetParam('snum.NoSpherA2.full_HAR')
  if iterative == False:
    t += update_tsc_button()
  else:
    t += cycles_spin()
  t += end_line()
  # Integration Accuracy, H Aniso, No Afix
  t += begin_new_line("NoSpherA2_Options_3") +integration_accuracy_combo() + h_aniso_checkbox() + no_afix_checkbox() + end_line()
  # ELMO specific options
  t += "<!-- #include ELMO_specific ../util/pyUtil/NoSpherA2/ELMO_specific.htm;help_ext=NoSpherA2 Extras;1; -->" + \
        partitioning_scheme_line()
  return t

def make_wfn_GUI():
  return begin_new_line() + \
      cpu_combo() + \
      memory_text() + \
      update_tsc_button()+ \
      end_line() + \
      begin_new_line() + \
      integration_accuracy_combo() + \
      h_aniso_checkbox() + \
      no_afix_checkbox() + \
      end_line() + \
      partitioning_scheme_line()

def make_ORCA_GUI(new_ORCA = True):
  # Quick buttons
  t = begin_new_line() + make_quick_button_gui() + end_line()
  # Basis Set, Method, CPUs, Memory
  t += begin_new_line() + \
        basis_combo() + \
        method_combo() + \
        cpu_combo() + \
        memory_text() + \
        end_line()
  adv = OV.GetParam('snum.NoSpherA2.basis_adv')
  if adv == True:
    t += begin_new_line() + \
          labeled_text("NoSpherA2_Basis_Set_Extra@refine",
                       "Adv. Basis Set",
                       "spy.GetParam('snum.NoSpherA2.basis_adv_string')",
                       "spy.SetParam('snum.NoSpherA2.basis_adv_string', html.GetValue('~name~')) >> html.Update()",
                       width_label=15, width_textbox=50) + end_line()
  # Charge, Multiplicity, iterative and Update/Max cycles
  t += begin_new_line("NoSpherA2_Options_2") + \
        labeled_checkbox("NoSpherA2_baseset_adv@refine",
                         "Adv.",
                         "spy.GetParam('snum.NoSpherA2.basis_adv')",
                         "spy.SetParam('snum.NoSpherA2.basis_adv', True) >> html.Update()",
                         "spy.SetParam('snum.NoSpherA2.basis_adv', False) >> html.Update()",
                         width=2) + \
        charge_spin() + \
        multiplicity_spin() + \
        iterative_checkbox()
  full_har = OV.GetParam('snum.NoSpherA2.full_HAR')
  if full_har == False:
    t += update_tsc_button()
  else:
    t += cycles_spin()
  t += end_line()
  # Integration Accuracy, Relativistics, H Aniso, No Afix
  t += begin_new_line("NoSpherA2_Options_3") + \
        integration_accuracy_combo() + \
        relativistics_checkbox() + \
        h_aniso_checkbox() + \
        no_afix_checkbox() + \
        end_line()
  # ORCA specific options: SCF Thresh., SCF Strategy, Solvation
  t += begin_new_line("NoSpherA2 Extras") + \
        labeled_combo("NoSpherA2_ORCA_SCF_Conv@refine",
                      "SCF Thresh.",
                      "'NoSpherA2SCF;SloppySCF;LooseSCF;NormalSCF;StrongSCF;TightSCF;VeryTightSCF;ExtremeSCF'",
                      "spy.GetParam(\'snum.NoSpherA2.ORCA_SCF_Conv\')",
                      "spy.SetParam(\'snum.NoSpherA2.ORCA_SCF_Conv\', html.GetValue(\'~name~\'))",
                      width_label=17, width_combo=20) + \
        labeled_combo("NoSpherA2_ORCA_SCF_Strategy@refine",
                      "SCF Strategy",
                      "'EasyConv;NormalConv;SlowConv;VerySlowConv'",
                      "spy.GetParam(\'snum.NoSpherA2.ORCA_SCF_Strategy\')",
                      "spy.SetParam(\'snum.NoSpherA2.ORCA_SCF_Strategy\', html.GetValue(\'~name~\'))",
                      width_label=17, width_combo=20) + \
        labeled_combo("NoSpherA2_ORCA_Solvation@refine",
                      "Solvation",
                      "'Vacuum;Water;Acetone;Acetonitrile;Ammonia;Benzene;CCl4;CH2CL2;Chloroform;Cyclohexane;DMF;DMSO;Ethanol;Hexane;Methanol;Octanol;Pyridine;THF;Toluene;Custom'",
                      "spy.GetParam(\'snum.NoSpherA2.ORCA_Solvation\')",
                      "spy.SetParam(\'snum.NoSpherA2.ORCA_Solvation\', html.GetValue(\'~name~\')) >> html.Update()",
                      width_label=13, width_combo=30) + \
        end_line()
  custom_solvation = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
  if custom_solvation == "Custom":
    t += begin_new_line() + \
          labeled_text("NoSpherA2_ORCA_Solvation_Custom_epsilon@refine",
                       "Epsilon",
                       "spy.GetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_epsilon')",
                       "spy.SetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_epsilon', html.GetValue('~name~'))",
                       width_label=15, width_textbox=20) + \
          labeled_text("NoSpherA2_ORCA_Solvation_Custom_refractive@refine",
                       "Refractive Index",
                       "spy.GetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_refrac')",
                       "spy.SetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_refrac', html.GetValue('~name~'))",
                       width_label=15, width_textbox=20) + \
          labeled_text("NoSpherA2_ORCA_Solvation_Custom_probe@refine",
                      "Probe Radius (A)",
                      "spy.GetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_rsolv')",
                      "spy.SetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_rsolv', html.GetValue('~name~'))",
                      width_label=15, width_textbox=20) + \
          end_line()
  if is_disordered():
    t += disorder_groups_text()
  elif new_ORCA:
    t += begin_new_line() + \
         labeled_checkbox("NoSpherA2_ORCA_damp@refine",
                          "Damp.",
                          "spy.GetParam('snum.NoSpherA2.ORCA_DAMP')",
                          "spy.SetParam('snum.NoSpherA2.ORCA_DAMP', True)",
                          "spy.SetParam('snum.NoSpherA2.ORCA_DAMP', False)",
                          width=8) + \
         labeled_checkbox("NoSpherA2_ORCA_embedding@refine",
                          "Embed.",
                          "spy.GetParam('snum.NoSpherA2.ORCA_USE_CRYSTAL_QMMM')",
                          "spy.SetParam('snum.NoSpherA2.ORCA_USE_CRYSTAL_QMMM', True) >> html.Update()",
                          "spy.SetParam('snum.NoSpherA2.ORCA_USE_CRYSTAL_QMMM', False) >> html.Update()",
                          width=10)
    embed = OV.GetParam('snum.NoSpherA2.ORCA_USE_CRYSTAL_QMMM')
    if embed:
      t += standalone_combo("NoSpherA2_ORCA_embedding_type@refine",
                            "Mol;Ion",
                            "spy.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_TYPE')",
                            "spy.SetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_TYPE', html.GetValue('~name~')) >> html.Update()",
                            width=11) + \
           labeled_text("NoSpherA2_ORCA_embedding_radius@refine",
                        "Embed. rad.",
                        "spy.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_RADIUS')",
                        "spy.SetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_RADIUS', html.GetValue('~name~'))",
                        width_label=11, width_textbox=8) + \
           labeled_text("NoSpherA2_ORCA_convergence@refine",
                        "Charge Conv.",
                        "spy.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_CONV')",
                        "spy.SetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_CONV', html.GetValue('~name~'))",
                        width_label=11, width_textbox=8) + \
           labeled_spin("NoSpherA2_ORCA_HF_Layers@refine",
                        "HF Layers",
                        "spy.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_HF_LAYERS')",
                        "spy.SetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_HF_LAYERS', html.GetValue('~name~'))",
                        width_label=11, width_spinbox=8, min_value=0, max_value=100)
      ion = OV.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_TYPE')
      if ion == "Ion":
        t += labeled_spin("NoSpherA2_ORCA_ECP_Layers@refine",
                          "ECP Layers",
                          "spy.GetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_ECP_LAYERS')",
                          "spy.SetParam('snum.NoSpherA2.ORCA_CRYSTAL_QMMM_ECP_LAYERS', html.GetValue('~name~'))",
                          width_label=11, width_spinbox=8, min_value=0, max_value=100)
    t += end_line()
  t += partitioning_scheme_line()
  return t

def make_OCC_GUI():
  import json
  from olx_gui.components.table import RowConfig, Row, RowManager
  from olx_gui.components.item_component import raw, ComboBox, InputSpinner, InputCheckbox, InputLinkButton, Cycle
  from pathlib import Path
  rows = RowManager()
  occ_data_path = Path(OV.BaseDir()) / "occ_data"
  full_har = OV.GetParam('snum.NoSpherA2.full_HAR')
  with open(occ_data_path / "basis_list.json", "r") as f:
    basis: list = json.load(f)

  with open(occ_data_path / "method_list.json", "r") as f:
    methods: list = json.load(f)

  with open(occ_data_path / "solvent_list.json", "r") as f:
    solvents: list = json.load(f)

  with rows:
    config = RowConfig()
    config.tr3_parameters.pop("bgcolor")
    with Row("AutoSelect", config=config, help_ext="NoSpherA2_Quick_Buttons"):
      raw(make_quick_button_gui())

    config.table2_parameters.pop("width")
    with Row("second", config=config, help_ext="NoSpherA2_Options_1"):
      ComboBox("NoSpherA2_basis@refine",
               txt_label="Basis Set",
               items=f"\"{';'.join(basis)}\"", # Olex2 kind of breaks for some reason with occ basis without double quotes
               value="spy.GetParam('snum.NoSpherA2.basis_name')",
               onchange="spy.NoSpherA2.change_basisset(html.GetValue('~name~'))",
      )

      ComboBox("NoSpherA2_method@refine",
               txt_label="Method",
               items=";".join(methods),
               value="spy.GetParam('snum.NoSpherA2.method')",
               onchange="spy.SetParam('snum.NoSpherA2.method', html.GetValue('~name~'))",
               tdwidth="25%"
      )

      ComboBox("NoSpherA2_cpus@refine",
               txt_label="CPUs",
               items=get_cpu_list_static(),
               value="spy.GetParam('snum.NoSpherA2.ncpus')",
               onchange="spy.SetParam('snum.NoSpherA2.ncpus', html.GetValue('~name~'))",
               tdwidth="30%"
      )

    config.table2_parameters["width"] = "100%"
    max_cycles = InputSpinner(bgcolor="spy.GetParam(gui.html.input_bg_colour)",
                          min='1',
                          txt_label="Max Cycles",
                          name='SET_SNUM_MULTIPLICITY',
                          value='$spy.GetParam(snum.NoSpherA2.multiplicity)',
                          onchange="spy.SetParam(snum.NoSpherA2.multiplicity,html.GetValue(~name~))",
                          width="100%",
                          hidden=True
                          )
    link_button = InputLinkButton(name="link_button",
                                  value="Update .tsc & .wfn",
                                  onclick="spy.NoSpherA2.launch() >> html.Update()",
                                  )
    with  Row("third", config=config, help_ext="NoSpherA2_Options_2"):
      InputSpinner("SET_CHARGE",
                           txt_label="Charge",
                           value='$spy.GetParam(snum.NoSpherA2.charge)',
                           onchange='spy.SetParam(snum.NoSpherA2.charge,html.GetValue(~name~))',
                           width="100%"
                           )
      InputSpinner(bgcolor="spy.GetParam(gui.html.input_bg_colour)",
                                 min='1',
                                 txt_label="Multiplicity",
                                 name='SET_SNUM_MULTIPLICITY',
                                 value='$spy.GetParam(snum.NoSpherA2.multiplicity)',
                                 onchange="spy.SetParam(snum.NoSpherA2.multiplicity,html.GetValue(~name~))",
                                 width="100%"
                   )
      InputCheckbox(name="Iterative",
                              txt_label="Iterative",
                              checked="spy.GetParam('snum.NoSpherA2.full_HAR')",
                              oncheck="spy.NoSpherA2.toggle_full_HAR()",
                              bgcolor="GetVar(HtmlTableFirstcolColour)",
                              onuncheck="spy.NoSpherA2.toggle_full_HAR()",
                              tdwidth="20%",
                              label_left=False
                              )
      Cycle(max_cycles, link_button, "spy.GetParam('snum.NoSpherA2.full_HAR')")
    solvationCombo = ComboBox(
      "NoSpherA2_solv",
        txt_label="Solvent",
        items=f"\"{';'.join(solvents)}\"",
        value="spy.GetParam('snum.NoSpherA2.occ.solvent')",
        onchange="spy.SetParam('snum.NoSpherA2.occ.solvent', html.GetValue('~name~'))",
        tdwidth="25%"
    )
    fill =  Filler()
    with Row("line4", config=config, help_ext="NoSpherA2_Options_3"):
      InputCheckbox(
        name="H_Aniso",
        txt_label="H Aniso",
        checked="spy.GetParam('snum.NoSpherA2.h_aniso')",
        oncheck="spy.SetParam('snum.NoSpherA2.h_aniso','True')",
        bgcolor="GetVar(HtmlTableFirstcolColour)",
        onuncheck="spy.SetParam('snum.NoSpherA2.h_aniso','False')",
      )

      InputCheckbox(
        name="H_Afix 0",
        txt_label="No Afix",
        checked="spy.GetParam('snum.NoSpherA2.h_afix')",
        oncheck="spy.SetParam('snum.NoSpherA2.h_afix','True')",
        bgcolor="GetVar(HtmlTableFirstcolColour)",
        onuncheck="spy.SetParam('snum.NoSpherA2.h_afix','False')",
      )

      InputCheckbox(
        name="occ_solvation",
        txt_label="Solvation",
        checked="spy.GetParam('snum.NoSpherA2.occ.solvation')",
        oncheck="spy.SetParam('snum.NoSpherA2.occ.solvation','True')>>html.Update",
        bgcolor="GetVar(HtmlTableFirstcolColour)",
        onuncheck="spy.SetParam('snum.NoSpherA2.occ.solvation','False')>>html.Update",
      )
      Cycle(solvationCombo, fill, "spy.GetParam('snum.NoSpherA2.occ.solvation')")

    with Row("line5", config=config, help_ext="NoSpherA2_Options_3"):
      InputLinkButton(
        name="edit_input",
        value="Edit_OCC_input_file",
        align="center",
        bgcolor="#C8C8C9",
        onclick="spy.NoSpherA2.edit_occ_input()",
      )
  return str(rows)

def make_tonto_GUI():
  # Basis Set, Method, CPUs, Memory
  t = begin_new_line() + \
        basis_combo() + \
        method_combo() + \
        cpu_combo() + \
        memory_text() + \
        end_line()
  # Charge, Multiplicity, iterative and Update/Max cycles
  t += begin_new_line("NoSpherA2_Options_2") + \
        charge_spin() + \
        multiplicity_spin() + \
        iterative_checkbox()
  full_har = OV.GetParam('snum.NoSpherA2.full_HAR')
  if full_har == False:
    t += update_tsc_button()
  else:
    t += cycles_spin()
  t += end_line()
  # Integration Accuracy, H Aniso, No Afix
  t += begin_new_line("NoSpherA2_Options_3") + \
        integration_accuracy_combo() + \
        relativistics_checkbox() + \
        h_aniso_checkbox() + \
        no_afix_checkbox() + \
        end_line()
  t += begin_new_line("NoSpherA2 Extras") + \
        labeled_text("NoSpherA2_tonto_cluster_radius@refine",
                      "Cluster r",
                      "spy.GetParam('snum.NoSpherA2.cluster_radius')",
                      "spy.SetParam('snum.NoSpherA2.cluster_radius', html.GetValue('~name~'))",
                      width_label=13, width_textbox=6) + \
        labeled_combo("NoSpherA2_tonto_DIIS@refine",
                      "DIIS Conv.",
                      "'0.1;0.01;0.001;0.0001;0.00001'",
                      "spy.GetParam('snum.NoSpherA2.DIIS')",
                      "spy.SetParam('snum.NoSpherA2.DIIS', html.GetValue('~name~'))",
                      width_label=16, width_combo=20) + \
        labeled_checkbox("NoSpherA2_tonto_cluster_grow@refine",
                         "Complete Cluster",
                         "spy.GetParam('snum.NoSpherA2.cluster_grow')",
                         "spy.SetParam('snum.NoSpherA2.cluster_grow', True)",
                         "spy.SetParam('snum.NoSpherA2.cluster_grow', False)",
                         width=5) + end_line()
  t += partitioning_scheme_line()
  return t
  
def make_frag_HAR_GUI():
  # Basis Set, Method, CPUs, Memory
  t = begin_new_line() + \
        basis_combo() + \
        labeled_checkbox("NoSpherA2_baseset_adv@refine",
                         "Adv.",
                         "spy.GetParam('snum.NoSpherA2.basis_adv')",
                         "spy.SetParam('snum.NoSpherA2.basis_adv', True) >> html.Update()",
                         "spy.SetParam('snum.NoSpherA2.basis_adv', False) >> html.Update()",
                         width=2) + \
        method_combo() + \
        cpu_combo() + \
        memory_text() + \
        end_line()
  adv = OV.GetParam('user.NoSpherA2.basis_adv')
  if adv == True:
    t += begin_new_line() + \
          labeled_text("NoSpherA2_Basis_Set_Extra@refine",
                       "Adv. Basis Set",
                       "spy.GetParam('snum.NoSpherA2.basis_adv_string')",
                       "spy.SetParam('snum.NoSpherA2.basis_adv_string', html.GetValue('~name~'))",
                       width_label=15, width_textbox=50) + end_line()
  # Charge, Multiplicity, iterative and Update/Max cycles
  t += begin_new_line("NoSpherA2_Options_2") + \
        charge_spin() + \
        multiplicity_spin() + \
        iterative_checkbox()
  full_har = OV.GetParam('snum.NoSpherA2.full_HAR')
  if full_har == False:
    t += update_tsc_button()
  else:
    t += cycles_spin()
  t += end_line()
  # Integration Accuracy, Relativistics, H Aniso, No Afix
  t += begin_new_line("NoSpherA2_Options_3") + \
        integration_accuracy_combo() + \
        relativistics_checkbox() + \
        h_aniso_checkbox() + \
        no_afix_checkbox() + \
        end_line()
  # ORCA specific options: SCF Thresh., SCF Strategy, Solvation
  t += begin_new_line("NoSpherA2 Extras") + \
        labeled_combo("NoSpherA2_ORCA_SCF_Conv@refine",
                      "SCF Thresh.",
                      "'NoSpherA2SCF;SloppySCF;LooseSCF;NormalSCF;StrongSCF;TightSCF;VeryTightSCF;ExtremeSCF'",
                      "spy.GetParam(\'snum.NoSpherA2.ORCA_SCF_Conv\')",
                      "spy.SetParam(\'snum.NoSpherA2.ORCA_SCF_Conv\', html.GetValue(\'~name~\'))",
                      width_label=17, width_combo=20) + \
        labeled_combo("NoSpherA2_ORCA_SCF_Strategy@refine",
                      "SCF Strategy",
                      "'EasyConv;NormalConv;SlowConv;VerySlowConv'",
                      "spy.GetParam(\'snum.NoSpherA2.ORCA_SCF_Strategy\')",
                      "spy.SetParam(\'snum.NoSpherA2.ORCA_SCF_Strategy\', html.GetValue(\'~name~\'))",
                      width_label=17, width_combo=20) + \
        labeled_combo("NoSpherA2_ORCA_Solvation@refine",
                      "Solvation",
                      "'Vacuum;Water;Acetone;Acetonitrile;Ammonia;Benzene;CCl4;CH2CL2;Chloroform;Cyclohexane;DMF;DMSO;Ethanol;Hexane;Methanol;Octanol;Pyridine;THF;Toluene;Custom'",
                      "spy.GetParam(\'snum.NoSpherA2.ORCA_Solvation\')",
                      "spy.SetParam(\'snum.NoSpherA2.ORCA_Solvation\', html.GetValue(\'~name~\'))",
                      width_label=13, width_combo=30) + \
        end_line()
  custom_solvation = OV.GetParam('snum.NoSpherA2.ORCA_Solvation')
  if custom_solvation == "Custom":
    t += begin_new_line() + \
          labeled_text("NoSpherA2_ORCA_Solvation_Custom_epsilon@refine",
                       "Epsilon",
                       "spy.GetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_epsilon')",
                       "spy.SetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_epsilon', html.GetValue('~name~'))",
                       width_label=15, width_textbox=20) + \
          labeled_text("NoSpherA2_ORCA_Solvation_Custom_refractive@refine",
                       "Refractive Index",
                       "spy.GetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_refrac')",
                       "spy.SetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_refrac', html.GetValue('~name~'))",
                       width_label=15, width_textbox=20) + \
          labeled_text("NoSpherA2_ORCA_Solvation_Custom_probe@refine",
                      "Probe Radius (A)",
                      "spy.GetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_rsolv')",
                      "spy.SetParam('snum.NoSpherA2.ORCA_Solvation_CPCM_rsolv', html.GetValue('~name~'))",
                      width_label=15, width_textbox=20) + \
          end_line()
  t += begin_new_line() + \
        labeled_text("NoSpherA2_frag_HAR_radius_tol@refine",
                      "Radius Tol.",
                      "spy.GetParam('snum.NoSpherA2.frag_HAR.radius_tolerance')",
                      "spy.SetParam('snum.NoSpherA2.frag_HAR.radius_tolerance', html.GetValue('~name~'))",
                      width_label=8, width_textbox=9) + \
        labeled_checkbox("NoSpherA2_frag_HAR_test@refine",
                          "Test Fragments",
                          "spy.GetParam('snum.NoSpherA2.frag_HAR.H_test')",
                          "spy.SetParam('snum.NoSpherA2.frag_HAR.H_test', True)",
                          "spy.SetParam('snum.NoSpherA2.frag_HAR.H_test', False)",
                          width=1) + \
        labeled_checkbox("NoSpherA2_frag_HAR_H_Box_Ex@refine",
                          "H-bond",
                          "spy.GetParam('snum.NoSpherA2.frag_HAR.H_box_ex')",
                          "spy.SetParam('snum.NoSpherA2.frag_HAR.H_box_ex', True)",
                          "spy.SetParam('snum.NoSpherA2.frag_HAR.H_box_ex', False)",
                          width=1) + \
        labeled_checkbox("NoSpherA2_frag_HAR_min_H_bond@refine",
                          "Min. H-bond",
                          "spy.GetParam('snum.NoSpherA2.frag_HAR.min_H_bond')",
                          "spy.SetParam('snum.NoSpherA2.frag_HAR.min_H_bond', True)",
                          "spy.SetParam('snum.NoSpherA2.frag_HAR.min_H_bond', False)",
                          width=1) + \
        end_line()
  t += partitioning_scheme_line()
  return t

def make_pySCF_GUI():
  # Method, CPUs, Memory
  t = begin_new_line() + basis_combo() + method_combo() + cpu_combo() + memory_text() + end_line()
  # Charge, Multiplicity, iterative and Update/Max cycles
  t += begin_new_line("NoSpherA2_Options_2") + \
        charge_spin() + \
        multiplicity_spin() + \
        iterative_checkbox() + \
        end_line()
  full_har = OV.GetParam('snum.NoSpherA2.full_HAR')
  if full_har == False:
    t += update_tsc_button()
  else:
    t += cycles_spin()
  t += end_line()
  # Integration Accuracy, H Aniso, No Afix
  t += begin_new_line("NoSpherA2_Options_3") + \
        integration_accuracy_combo() + \
        h_aniso_checkbox() + \
        no_afix_checkbox() + \
        end_line()
  t +=  pyscf_damping()+ \
        pyscf_solvation() + \
        WSL_distro() + end_line()
  if is_disordered():
    t += disorder_groups_text()
  t += partitioning_scheme_line()
  return t

def make_discambMATT_GUI():
  t = begin_new_line() + \
    iterative_checkbox()
  iterative = OV.GetParam('snum.NoSpherA2.full_HAR')
  if iterative == False:
    t += update_tsc_button()
  else:
    t += cycles_spin()
  t += end_line() + begin_new_line("NoSpherA2_Options_3") + h_aniso_checkbox() + no_afix_checkbox() + end_line()
  if is_disordered():
    t += disorder_groups_text()
  return t

def make_xHARPY_GUI():
  # Method, CPUs, Memory
  t = begin_new_line() + method_combo() + \
    labeled_text("NoSpherA2_xHARPY_grid_spacing",
                 "Grid spacing (Ang)",
                 "spy.GetParam('snum.NoSpherA2.xharpy.grid_spacing')",
                 "spy.SetParam('snum.NoSpherA2.xharpy.grid_spacing', html.GetValue('~name~'))",
                 width_label=15, width_textbox=12) + \
    cpu_combo() + memory_text() + end_line()
  # Charge, Multiplicity, iterative and Update/Max cycles
  t += begin_new_line() + labeled_text("NoSpherA2_xHARPY_k_points1",
                                       "K-point grid",
                                        "spy.GetParam('snum.NoSpherA2.xharpy.k_points1')",
                                        "spy.SetParam('snum.NoSpherA2.xharpy.k_points1', html.GetValue('~name~'))",
                                        width_label=15, width_textbox=12) + \
    standalone_text("NoSpherA2_xHARPY_k_points2",
             "spy.GetParam('snum.NoSpherA2.xharpy.k_points2')",
             "spy.SetParam('snum.NoSpherA2.xharpy.k_points2', html.GetValue('~name~'))", 12) + \
    standalone_text("NoSpherA2_xHARPY_k_points3",
             "spy.GetParam('snum.NoSpherA2.xharpy.k_points3')",
             "spy.SetParam('snum.NoSpherA2.xharpy.k_points3', html.GetValue('~name~'))", 12) + \
    labeled_checkbox("NoSpherA2_xHARPY_center_gamma",
                     "Center Gamma",
                     "spy.GetParam('snum.NoSpherA2.xharpy.k_points_centre_gamma')",
                     "spy.SetParam('snum.NoSpherA2.xharpy.k_points_centre_gamma', True)",
                     "spy.SetParam('snum.NoSpherA2.xharpy.k_points_centre_gamma', False)",
                      width=10) + \
    end_line()
  t += begin_new_line() + WSL_distro() + update_tsc_button() + end_line()
  return t
