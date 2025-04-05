import os
import sys
import htmlTools
import olex
import olx
import olex_core
import gui
import shutil
import time

from olexFunctions import OV

def begin_new_line():
  temp = '''
<tr ALIGN='left' NAME='SNUM_REFINEMENT_NSFF' width='100%'>
  <td valign='top' width="$GetVar(HtmlTableFirstcolWidth)" align='center' bgcolor="$GetVar(HtmlTableFirstcolColour)">'''
  temp += htmlTools.MakeHoverButton('btn-info@NoSpherA2 Option 1',"spy.make_help_box -name='NoSpherA2 Option 1' -popout='False' -helpTxt='Options'")
  temp +='''
  </td>
  <td colspan="#colspan">
    <table border="0" width="100%" cellpadding="1" cellspacing="1" Xbgcolor="#ffaaaa">
      <tr Xbgcolor="#aaffaa">
'''
  return temp

def end_line():
  return '''
      </tr>
    </table>
  </td>
</tr>
'''

def input_combo(name,items,value,onchange):
  temp =  '''<input
  type='combo'
  height='GetVar(HtmlComboHeight)'
  bgcolor='GetVar(HtmlInputBgColour)'
  fgcolor='GetVar(HtmlFontColour)'
  valign='center' ''' \
  + '''\nname="%s"
  width="100%%" '''%name \
  + '''\nvalue="%s"
  setdefault='false' '''%value \
  + '''\nitems="%s"
  disabled='false' '''%items
  temp += '''\nonchange="%s" '''%onchange 
  temp +='''\nreadonly='true'
  onchangealways='false'
  manage='false'
  custom='GetVar(custom_button);arrow_width: 20'
>
'''
  return temp

def checkbox(name,label,checked,oncheck,onuncheck,width=20):
  temp = '''
  <td "%d%%" align="left">
    <table cellpadding="0" cellspacing="0">
      <tr>
        <td>
          <font size="$GetVar('HtmlFontSizeControls')">
            <input
              type="checkbox"
              height="20"
              fgcolor="GetVar(HtmlFontColour)"
              bgcolor="GetVar(HtmlTableRowBgColour)"'''%width \
       + '''\nname="%s"'''%name \
       + '''\nlabel="%s "'''%label \
       + '''\nchecked="%s"'''%checked \
       + '''\noncheck="%s"'''%oncheck \
       + '''\nonuncheck="%s"'''%onuncheck \
       + '''
              value=""
              onclick=""
              right="false"
              manage="false"
              disabled="false"
              custom="GetVar(custom_button)"
            >
          </font>
        </td>  
        <td align='left'>
          <b>%s </b>
        </td>
      </tr>
    </table>
  </td>  
'''%label
  return temp

def make_hybrid_GUI(softwares_list_string):
  parts = OV.ListParts()
  if parts != None:
    parts = list(parts)
  if len(parts) <= 1:
    return begin_new_line() + "Hybrid is not possible with less than two parts!" + end_line()
  t = begin_new_line() + \
      checkbox(
    "iterative",
    "Iterative",
    "spy.GetParam(\'snum.NoSpherA2.full_HAR\')",
    "spy.SetParam(\'snum.NoSpherA2.full_HAR\',\'True\')>>html.Update()",
    "spy.SetParam(\'snum.NoSpherA2.full_HAR\',\'False\')>>html.Update()"
  ) + '''
<!-- ======= FULL HAR SWITCH ===================== -->

'''
  full_har = OV.GetParam('snum.NoSpherA2.full_HAR')
  if full_har == True:
    t +='''
<td width="18%">
<b>Max Cycles </b>
</td>
<td width='8%' align='left'>
  <input 
    type='spin', 
    width='50', 
    height='20'
    bgcolor="spy.GetParam(gui.html.input_bg_colour)"
    name='SET_SNUM_MAX_HAR',
    value='$spy.GetParam(snum.NoSpherA2.Max_HAR_Cycles)', 
    onchange='spy.SetParam(snum.NoSpherA2.Max_HAR_Cycles,html.GetValue(~name~))'
  > 
</td>
'''
  else:
    t +='''
  <td width="29%" align='center'>
    <font size="$GetVar('HtmlFontSizeControls')">
      <b>
        <input
          type="button"
          name="Update .tsc"
          value="Update .tsc"
          width="100%"
          height="GetVar(HtmlComboHeight)"
          onclick="spy.NoSpherA2.launch() >> html.Update() >> focus"
          bgcolor="GetVar(HtmlTableRowBgColour)"
          fgcolor="GetVar(linkButton.fgcolor)"
          fit="false"
          flat="GetVar(linkButton.flat)"
          hint=""
          disabled="false"
          custom="GetVar(custom_button)"
        >
      </b>
    </font>
  </td>'''

  t += '''
<!-- ======= FULL HAR SWITCH END ===================== -->
<td width="8%" align='right'>
  <b>CPUs</b>
</td>
<td width="10%" align='center'>
'''
  t += input_combo(
      "NoSpherA2_cpus@refine",
      "spy.NoSpherA2.getCPUListStr()",
      "spy.GetParam(\'snum.NoSpherA2.ncpus\')",
      "spy.SetParam(\'snum.NoSpherA2.ncpus\', html.GetValue(\'~name~\'))")
  t +='''
</td>
<td width="8%" align='right'>
  <b>Mem(Gb) </b>
</td>
<td width="9%" align='center'>
  <font size="$GetVar('HtmlFontSizeControls')">
    <input
      type="text"
      height="GetVar('HtmlInputHeight')"
      bgcolor="GetVar('HtmlInputBgColour')"
      fgcolor="GetVar(HtmlFontColour)"
      valign="center"
      name="NosPherA2_Memory"
      width="100%"
      value="spy.GetParam('snum.NoSpherA2.mem')"
      onchange="spy.SetParam('snum.NoSpherA2.mem', html.GetValue('~name~'))"
      onleave=""
      manage="false"
      password="false"
      multiline="false"
      disabled="false"
    >
  </font>
</td>'''
  t += end_line() + begin_new_line() +'''
<td width='13%' align='left'>
    <b>Integr. Accuracy</b>
</td>
<td width='16%' align="left">
'''
  t += input_combo(
    "NoSpherA2_becke_accuracy@refine",
    "'Low;Normal;High;Max'",
    "spy.GetParam(\'snum.NoSpherA2.becke_accuracy\')",
    "spy.SetParam(\'snum.NoSpherA2.becke_accuracy\', html.GetValue(\'~name~\'))")
  t += '''
</td> '''
  t += checkbox("H_Aniso",
                "H Aniso",
                "spy.GetParam(\'snum.NoSpherA2.h_aniso\')",
                "spy.SetParam(\'snum.NoSpherA2.h_aniso\',\'True\')",
                "spy.SetParam(\'snum.NoSpherA2.h_aniso\',\'False\')")
  t += checkbox("H_Afix 0",
                "No Afix",
                "spy.GetParam(\'snum.NoSpherA2.h_afix\')",
                "spy.SetParam(\'snum.NoSpherA2.h_afix\',\'True\')",
                "spy.SetParam(\'snum.NoSpherA2.h_afix\',\'False\')")
  t += end_line()
  for i in parts:
    if i == 0:
      continue
    t += begin_new_line() + "<td width='63%' align='center'>" + "<b>Part %d</b></td>"%i
    softwares_list = "Please Select" + str(softwares_list_string).replace("Hybrid;","")
    t += '''
<td width='13%' align='left'>
<b>Software</b>
</td>
'''
    t += '''
<td width='20%'>'''
    t += input_combo(
      "NoSpherA2_software_Part%d@refine"%(i+1), 
      softwares_list, 
      "spy.GetParam(\'snum.NoSpherA2.Hybrid.software_Part%d\')"%i, 
      "spy.SetParam(\'snum.NoSpherA2.Hybrid.software_Part%d\',html.GetValue(\'~name~\'))>>html.Update()"%i)
    t += "\n</td>\n"
    selected_software = OV.GetParam('snum.NoSpherA2.Hybrid.software_Part%d'%i)
    t += end_line() + begin_new_line()
    if selected_software != "discambMATT":
      if selected_software != "ELMOdb":
        t += '''
<td width="13%" align='left'>
    <b>Basis Set </b>
</td>
<td width="20%">
'''
        t += input_combo(
          "NoSpherA2_basis_Part%d@refine"%i, 
          "spy.NoSpherA2.getBasisListStr()", 
          "spy.GetParam(\'snum.NoSpherA2.Hybrid.basis_name_Part%d\')"%i,
          "spy.SetParam(\'snum.NoSpherA2.Hybrid.basis_name_Part%d\',html.GetValue(\'~name~\'))"%i)
        t += '''
</td>
<td width="11%" align='right'>
  <b>Method</b>
</td>
<td width="20%">
'''
        t += input_combo(
          "NoSpherA2_method_Part%d@refine"%i, 
          "spy.NoSpherA2.get_functional_list(spy.GetParam(\'snum.NoSpherA2.Hybrid.software_Part%d\'))"%i, 
          "spy.GetParam(\'snum.NoSpherA2.Hybrid.method_Part%d\')"%i,
          "spy.SetParam(\'snum.NoSpherA2.Hybrid.method_Part%d\',html.GetValue(\'~name~\'))"%i)
        t += '''
</td>'''
        t += checkbox("NoSpherA2_ORCA_Relativistics_PART%d@refine"%i, 
                      "Relativitics", 
                      "spy.GetParam(\'snum.NoSpherA2.Hybrid.Relativistic_Part%d\')"%i, 
                      "spy.SetParam(\'snum.NoSpherA2.Hybrid.Relativistic_Part%d\',\'True\')"%i, 
                      "spy.SetParam(\'snum.NoSpherA2.Hybrid.Relativistic_Part%d\',\'False\')"%i)        
        t += end_line() + begin_new_line() + '''
<td width='13%' align='left'>
  <b>Charge </b>
</td>
<td width='8%' align='left'>
  <input
    type='spin'
    width='50'
    height='17'
    max='1000'
    min='-1000'
    bgcolor='spy.GetParam(gui.html.input_bg_colour)' '''
        t += "\nname='SET_CHARGE_PART%d'"%i
        t += "\nvalue='$spy.GetParam(snum.NoSpherA2.Hybrid.charge_Part%d)'"%i
        t += "\nonchange='spy.SetParam(snum.NoSpherA2.Hybrid.charge_Part%d,html.GetValue(~name~))'"%i
        t += '''\n  >
</td>
<td width='16%' align='right'>
  <b>Multiplicity </b>
</td>
<td width='8%'>
  <input 
    type='spin', 
    width='50', 
    height='17'
    bgcolor="spy.GetParam(gui.html.input_bg_colour)"
    min='1' '''
        t += "\nname='SET_SNUM_MULTIPLICITY_PART%d',"%i
        t += "\nvalue='$spy.GetParam(snum.NoSpherA2.Hybrid.multiplicity_Part%d)',"%i
        t += "\nonchange='spy.SetParam(snum.NoSpherA2.Hybrid.multiplicity_Part%d,html.GetValue(~name~))'"%i
        t += '''\n  > 
</td>
'''
        if "ORCA" in selected_software:
          t += end_line() + begin_new_line() +'''
<td width="17%" align='left'>
    <b>SCF Thresh. </b>
</td>
<td width="20%">
'''
          t += input_combo("NoSpherA2_ORCA_SCF_Conv_Part%d@refine"%i,
                           "\'NoSpherA2SCF;SloppySCF;LooseSCF;NormalSCF;StrongSCF;TightSCF;VeryTightSCF;ExtremeSCF\'",
                           "spy.GetParam(\'snum.NoSpherA2.Hybrid.ORCA_SCF_Conv_Part%d\')"%i,
                           "spy.SetParam(\'snum.NoSpherA2.Hybrid.ORCA_SCF_Conv_Part%d', html.GetValue(\'~name~\'))"%i)
          t += '''
</td>
<td width="17%" align='right'>
    <b>SCF Strategy </b>
</td>
<td width="20%">
'''
          t += input_combo("NoSpherA2_ORCA_SCF_Strategy_Part%d@refine"%i,
                           "\'EasyConv;NormalConv;SlowConv;VerySlowConv\'",
                           "spy.GetParam(\'snum.NoSpherA2.Hybrid.ORCA_SCF_Strategy_Part%d\')"%i,
                           "spy.SetParam(\'snum.NoSpherA2.Hybrid.ORCA_SCF_Strategy_Part%d\', html.GetValue(\'~name~\'))"%i)
          t += '''
</td> 
<td width="13%" align='right'>
    <b>Solvation </b>
</td>
<td width="20%">
'''
          t += input_combo("NoSpherA2_ORCA_Solvation@refine",
                           "\'Vacuum;Water;Acetone;Acetonitrile;Ammonia;Benzene;CCl4;CH2CL2;Chloroform;Cyclohexane;DMF;DMSO;Ethanol;Hexane;Methanol;Octanol;Pyridine;THF;Toluene\'",
                           "spy.GetParam(\'snum.NoSpherA2.ORCA_Solvation\')",
                           "spy.SetParam(\'snum.NoSpherA2.ORCA_Solvation\', html.GetValue(\'~name~\'))")
          t += "\n</td>\n"
        elif "pySCF" in selected_software:
          t += end_line() + begin_new_line() + '''
<td width="10%" align='right'>
    <b>Damping </b>
</td>
<td width="10%">
'''
          t += input_combo("NoSpherA2_Hybrid_pySCF_Damping_Part%d@refine"%i,
                           "\'0.6;0.7;0.85;0.93\'",
                           "spy.GetParam(\'snum.NoSpherA2.Hybrid.pySCF_Damping_Part%d\')"%i,
                           "spy.SetParam(\'snum.NoSpherA2.Hybrid.pySCF_Damping_Part%d\', html.GetValue(\'~name~\'))"%i)
          t += '''
</td> 
<td width="13%" align='right'>
    <b>Solvation </b>
</td>
<td width="30%">
'''
          t += input_combo("NoSpherA2_ORCA_Solvation@refine",
                           "\'Vacuum;Water; Acetonitrile;Methanol;Ethanol;IsoQuinoline;Quinoline;Chloroform;DiethylEther;Dichloromethane;DiChloroEthane;CarbonTetraChloride;Benzene;Toluene;ChloroBenzene;NitroMethane;Heptane;CycloHexane;Aniline;Acetone;TetraHydroFuran;DiMethylSulfoxide;Argon;Krypton;Xenon;n-Octanol;1,1,1-TriChloroEthane;1,1,2-TriChloroEthane;1,2,4-TriMethylBenzene;1,2-DiBromoEthane;1,2-EthaneDiol;1,4-Dioxane;1-Bromo-2-MethylPropane;1-BromoOctane;1-BromoPentane;1-BromoPropane;1-Butanol;1-ChloroHexane;1-ChloroPentane;1-ChloroPropane;1-Decanol;1-FluoroOctane;1-Heptanol;1-Hexanol;1-Hexene;1-Hexyne;1-IodoButane;1-IodoHexaDecane;1-IodoPentane;1-IodoPropane;1-NitroPropane;1-Nonanol;1-Pentanol;1-Pentene;1-Propanol;2,2,2-TriFluoroEthanol;2,2,4-TriMethylPentane;2,4-DiMethylPentane;2,4-DiMethylPyridine;2,6-DiMethylPyridine;2-BromoPropane;2-Butanol;2-ChloroButane;2-Heptanone;2-Hexanone;2-MethoxyEthanol;2-Methyl-1-Propanol;2-Methyl-2-Propanol;2-MethylPentane;2-MethylPyridine;2-NitroPropane;2-Octanone;2-Pentanone;2-Propanol;2-Propen-1-ol;3-MethylPyridine;3-Pentanone;4-Heptanone;4-Methyl-2-Pentanone;4-MethylPyridine;5-Nonanone;AceticAcid;AcetoPhenone;a-ChloroToluene;Anisole;Benzaldehyde;BenzoNitrile;BenzylAlcohol;BromoBenzene;BromoEthane;Bromoform;Butanal;ButanoicAcid;Butanone;ButanoNitrile;ButylAmine;ButylEthanoate;CarbonDiSulfide;Cis-1,2-DiMethylCycloHexane;Cis-Decalin;CycloHexanone;CycloPentane;CycloPentanol;CycloPentanone;Decalin-mixture;DiBromomEthane;DiButylEther;DiEthylAmine;DiEthylSulfide;DiIodoMethane;DiIsoPropylEther;DiMethylDiSulfide;DiPhenylEther;DiPropylAmine;e-1,2-DiChloroEthene;e-2-Pentene;EthaneThiol;EthylBenzene;EthylEthanoate;EthylMethanoate;EthylPhenylEther;FluoroBenzene;Formamide;FormicAcid;HexanoicAcid;IodoBenzene;IodoEthane;IodoMethane;IsoPropylBenzene;m-Cresol;Mesitylene;MethylBenzoate;MethylButanoate;MethylCycloHexane;MethylEthanoate;MethylMethanoate;MethylPropanoate;m-Xylene;n-ButylBenzene;n-Decane;n-Dodecane;n-Hexadecane;n-Hexane;NitroBenzene;NitroEthane;n-MethylAniline;n-MethylFormamide-mixture;n,n-DiMethylAcetamide;n,n-DiMethylFormamide;n-Nonane;n-Octane;n-Pentadecane;n-Pentane;n-Undecane;o-ChloroToluene;o-Cresol;o-DiChloroBenzene;o-NitroToluene;o-Xylene;Pentanal;PentanoicAcid;PentylAmine;PentylEthanoate;PerFluoroBenzene;p-IsoPropylToluene;Propanal;PropanoicAcid;PropanoNitrile;PropylAmine;PropylEthanoate;p-Xylene;Pyridine;sec-ButylBenzene;tert-ButylBenzene;TetraChloroEthene;TetraHydroThiophene-s,s-dioxide;Tetralin;Thiophene;Thiophenol;trans-Decalin;TriButylPhosphate;TriChloroEthene;TriEthylAmine;Xylene-mixture;z-1,2-DiChloroEthene\'",
                           "spy.GetParam(\'snum.NoSpherA2.ORCA_Solvation\')",
                           "spy.SetParam(\'snum.NoSpherA2.ORCA_Solvation\', html.GetValue(\'~name~\'))")
          t += "\n</td>"
      else:
        #HAVE TO FINISCH ELMO LATER
        t += '''
<td width="13%" align='left'>
    <b>Basis Set </b>
</td>
<td width="20%">
  $+
    html.Snippet("gui/snippets/input-combo",
    "name=NoSpherA2_basis@refine",
    "items='6-31G;6-31G**;6-311G;6-311G**;cc-pVDZ;extrabasis'",
    "value=spy.GetParam(\'snum.NoSpherA2.basis_name\')",
    "onchange=spy.NoSpherA2.change_basisset(html.GetValue(\'~name~\'))>>html.Update()")
  $-
  </td>
'''
      
      t += end_line()
    else:
      t += "<td align='center'><b>So far no further options for discambMATT</b></td>" + end_line()
  
  return t