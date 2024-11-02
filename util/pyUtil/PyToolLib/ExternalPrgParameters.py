import os, sys
import olx
import olex
import olex_core
from olexFunctions import OV
import phil_interface
import libtbx.utils

from method_imp import *

global RPD
RPD = {}
global SPD
SPD = {}
global managed_references
managed_references = set()

class ExternalProgramDictionary(object):
  def __init__(self):
    self.programs = {}
    self.counter = 0

  def addProgram(self, program):
    program.order = self.counter
    self.programs.setdefault(program.name, program)
    self.counter += 1

  def __contains__(self, name):
    if type(name) == str:
      return name in self.programs
    else:
      return name in list(self.programs.values())

  def __iter__(self):
    return iter(self.programs.values())


class Program(object):
  def __init__(self, name, program_type, author, reference, brief_reference,
               execs=None,
               versions=None, phil_entry_name=None):
    self.name = name
    self.program_type = program_type
    self.author = author
    self.reference = reference
    self.brief_reference = brief_reference
    self.execs = execs
    self.versions = versions
    self.methods = {}
    self.counter = 0
    self.phil_entry_name = phil_entry_name

  def __contains__(self, name):
    if type(name) == str:
      return name in self.methods
    else:
      return name in list(self.methods.values())

  def __iter__(self):
    return iter(self.methods.values())

  def addMethod(self, method):
    method.order = self.counter
    self.methods.setdefault(method.name, method)
    self.counter += 1

def defineExternalPrograms():
  # define solution methods
  direct_methods = Method_shelx_direct_methods(direct_methods_phil)
  patterson = Method_shelx_solution(patterson_phil)
  xt_intrinsic_phasing = Method_shelxt(shelxt_phil_str)
  texp = Method_shelx_solution(texp_phil)
  dual_space = Method_shelxd(dual_space_phil)
  charge_flipping = Method_cctbx_ChargeFlip(charge_flipping_phil)
  sir97_dm = Method_SIR(sir_dm_phil)
  sir97_patt = Method_SIR(sir_patt_phil)
  sir2002_dm = Method_SIR(sir_dm_phil)
  sir2002_patt = Method_SIR(sir_patt_phil)
  sir2004_dm = Method_SIR(sir_dm_phil)
  sir2004_patt = Method_SIR(sir_patt_phil)
  sir2008_dm = Method_SIR(sir_dm_phil)
  sir2008_patt = Method_SIR(sir_patt_phil)
  sir2011_dm = Method_SIR(sir_dm_phil)
  sir2011_patt = Method_SIR(sir_patt_phil)
  sir2014_dm = Method_SIR(sir_dm_phil)
  sir2014_patt = Method_SIR(sir_patt_phil)
  superflip_cf = Method_Superflip(superflip_cf_phil)

  # define refinement methods
  least_squares = Method_shelx_refinement(get_LS_phil())
  cgls = Method_shelx_refinement(get_CGLS_phil())
  gauss_newton = Method_cctbx_refinement(gauss_newton_phil)
  levenberg_marquardt = Method_cctbx_refinement(levenberg_marquardt_phil)

  # define solution programs

  ShelXS = Program(
    name='ShelXS',
    program_type='solution',
    author="G.M.Sheldrick",
    reference="Sheldrick, G.M. (2008). Acta Cryst. A64, 112-122.",
    brief_reference="Sheldrick, 2008",
    execs=["shelxs.exe", "shelxs"],
    phil_entry_name="ShelXS")
  ShelXS97 = Program(
    name='ShelXS-1997',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxs97.exe", "shelxs97"])
  ShelXS86 = Program(
    name='ShelXS-1986',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxs86.exe", "shelxs86"])
  XS = Program(
    name='XS',
    program_type='solution',
    author="G.M.Sheldrick/Bruker",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xs.exe", "xs"],
    phil_entry_name="XS")
  XT = Program(
    name='XT',
    program_type='solution',
    author="G.M.Sheldrick/Bruker",
    reference="Sheldrick, G.M. (2015). Acta Cryst. A71, 3-8.",
    brief_reference="Sheldrick, 2015",
    execs=["xt.exe", "xt"],
    phil_entry_name="XT")
  ShelXT = Program(
    name='ShelXT',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=XT.reference,
    brief_reference=XT.brief_reference,
    execs=["shelxt.exe", "shelxt"],
    phil_entry_name="ShelXT")
  ShelXD = Program(
    name='ShelXD',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxd.exe", "shelxd"],
    phil_entry_name="ShelXD")
  ShelXD97 = Program(
    name='ShelXD-1997',
    program_type='solution',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxd97.exe", "shelxd97"])
  XM = Program(
    name='XM',
    program_type='solution',
    author="G.M.Sheldrick/Bruker",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xm.exe", "xm"],
    phil_entry_name="XM")
  smtbx_solve = Program(
    name='olex2.solve',
    program_type='solution',
    author="Luc Bourhis et al",
    reference="""Bourhis, L.J., Dolomanov, O.V., Gildea, R.J., Howard, J.A.K., Puschmann, H.
 (2015). Acta Cryst. A71, 59-75.""",
    brief_reference="Bourhis et al., 2015",
    )

  SIR97 = Program(
    name='SIR97',
    program_type='solution',
    author="Maria C. Burla, Rocco Caliandro, Mercedes Camalli, Benedetta Carrozzini,"+
        "Giovanni Luca Cascarano, Liberato De Caro, Carmelo Giacovazzo, Giampiero Polidori,"+
        "Dritan Siliqi, Riccardo Spagna",
    reference="""Burla, M.C., Caliandro, R., Camalli, M., Carrozzini, B., Cascarano, G.L.,
 De Caro, L., Giacovazzo, C., Polidori, G., Siliqi, D., Spagna, R.
 (2007). J. Appl. Cryst. 40, 609-613.""",
    brief_reference="Burla et al.,  2007",
    versions = '97',
    execs=["sir97.exe", "sir97"])
  SIR2002 = Program(
    name='SIR2002',
    program_type='solution',
    author=SIR97.author,
    reference=SIR97.reference,
    brief_reference=SIR97.brief_reference,
    versions = '2002',
    execs=["sir2002.exe", "sir2002"])
  SIR2004 = Program(
    name='SIR2004',
    program_type='solution',
    author=SIR97.author,
    reference=SIR97.reference,
    brief_reference=SIR97.brief_reference,
    versions = '2004',
    execs=["sir2004.exe", "sir2004"])
  SIR2008 = Program(
    name='SIR2008',
    program_type='solution',
    author=SIR97.author,
    reference=SIR97.reference,
    brief_reference=SIR97.brief_reference,
    versions = '2008',
    execs=["sir2008.exe", "sir2008"])
  SIR2011 = Program(
    name='SIR2011',
    program_type='solution',
    author=SIR97.author,
    reference=SIR97.reference,
    brief_reference=SIR97.brief_reference,
    versions = '2011',
    execs=["sir2011.exe", "sir2011"])
  SIR2014 = Program(
    name='SIR2014',
    program_type='solution',
    author=SIR97.author,
    reference=SIR97.reference,
    brief_reference=SIR97.brief_reference,
    versions = '2014',
    execs=["sir2014.exe", "sir2014"])
  Superflip = Program(
    name='Superflip',
    program_type='solution',
    author="A van der Lee, C.Dumas & L. Palatinus",
    reference="""Palatinus, L. & Chapuis, G. (2007). J. Appl. Cryst., 40, 786-790;
Palatinus, L. & van der Lee, A. (2008). J. Appl. Cryst. 41, 975-984;
Palatinus, L., Prathapa, S. J. & van Smaalen, S. (2012). J. Appl. Cryst. 45,
 575-580.""",
    brief_reference="""Palatinus & Chapuis, 2007;Palatinus & van der Lee, 2008;
Palatinus et al., 2012""",
    versions='260711',
    execs=["superflip.exe", "superflip"])

  ShelXS.addMethod(direct_methods)
  ShelXS.addMethod(patterson)
  ShelXS.addMethod(texp)
  ShelXS97.addMethod(direct_methods)
  ShelXS97.addMethod(patterson)
  ShelXS97.addMethod(texp)
  ShelXS86.addMethod(direct_methods)
  ShelXS86.addMethod(patterson)
  ShelXS86.addMethod(texp)
  XS.addMethod(direct_methods)
  XS.addMethod(patterson)
  XS.addMethod(texp)
  XT.addMethod(xt_intrinsic_phasing)
  ShelXT.addMethod(xt_intrinsic_phasing)
  ShelXD.addMethod(dual_space)
  ShelXD97.addMethod(dual_space)
  XM.addMethod(dual_space)
  smtbx_solve.addMethod(charge_flipping)
  SIR97.addMethod(sir97_dm)
  SIR97.addMethod(sir97_patt)
  SIR2002.addMethod(sir2002_dm)
  SIR2002.addMethod(sir2002_patt)
  SIR2004.addMethod(sir2004_dm)
  SIR2004.addMethod(sir2004_patt)
  SIR2008.addMethod(sir2008_dm)
  SIR2008.addMethod(sir2008_patt)
  SIR2011.addMethod(sir2011_dm)
  SIR2011.addMethod(sir2011_patt)
  SIR2014.addMethod(sir2014_dm)
  SIR2014.addMethod(sir2014_patt)
  Superflip.addMethod(superflip_cf)

  # define refinement programs
  ShelXL = Program(
    name='ShelXL',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference="Sheldrick, G.M. (2015). Acta Cryst. C71, 3-8.",
    brief_reference="Sheldrick, 2015",
    execs=["shelxl.exe", "shelxl"],
    phil_entry_name="ShelXL")
  ShelXL97 = Program(
    name='ShelXL-1997',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxl97.exe", "shelxl97"],
    phil_entry_name="ShelXL97")
  XL = Program(
    name='XL',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xl.exe", "xl"],
    phil_entry_name="ShelXL97")
  XLMP = Program(
    name='XLMP',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xlmp.exe", "xlmp"],
    phil_entry_name="XLMP")
  ShelXH97 = Program(
    name='ShelXH-1997',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxh.exe", "shelxh"],
    phil_entry_name="ShelXL97")
  XH = Program(
    name='XH',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["xh.exe", "xh"],
    phil_entry_name="ShelXL97")
  ShelXL_ifc = Program(
    name='ShelXL_ifc',
    program_type='refinement',
    author="G.M.Sheldrick",
    reference=ShelXS.reference,
    brief_reference=ShelXS.brief_reference,
    execs=["shelxl_ifc"],
    phil_entry_name="ShelXL97")
  smtbx_refine = Program(
    name='olex2.refine',
    program_type='refinement',
    author="L.J. Bourhis, O.V. Dolomanov, R.J. Gildea",
    reference=smtbx_solve.reference,
    brief_reference=smtbx_solve.brief_reference,
    phil_entry_name="cctbx"
  )
  #tonto_refine = Program(
  #  name='Tonto',
  #  program_type='refinement',
  #  author="D. Jayatilaka and D. J. Grimwood",
  #  reference="D. Jayatilaka and D. J. Grimwood (2003). Computational Science - ICCS, 4, 142-151",
  #  brief_reference="Jayatilaka & Grimwood, 2003",
  #  execs=["hart.exe", "hart"],
  #)

  RPD = ExternalProgramDictionary()
  for prg in (ShelXL, ShelXL97, XL, XLMP, ShelXH97, XH, ShelXL_ifc):
    prg.addMethod(least_squares)
    prg.addMethod(cgls)
    RPD.addProgram(prg)

  smtbx_refine.addMethod(gauss_newton)
  smtbx_refine.addMethod(levenberg_marquardt)
  RPD.addProgram(smtbx_refine)

  #tonto_refine.addMethod(Method_tonto_HAR(tonto_HAR_phil))
  #RPD.addProgram(tonto_refine)
  #HP don't add tonto_refine for the moment; it's not working as it stands


  SPD = ExternalProgramDictionary()
  for prg in (ShelXS, ShelXS97, ShelXS86, XS, XT, ShelXT, ShelXD, ShelXD97, XM,
              smtbx_solve, SIR97, SIR2002, SIR2004, SIR2008, SIR2011, SIR2014, Superflip):
    SPD.addProgram(prg)

  return SPD, RPD


  #{'name':'SHEL', 'values':['dmax:', 'dmin:0']},
  #{'name':'PATS', 'values':['+np or -dis:100', 'npt:', 'nf:5']},
  #{'name':'GROP', 'values':['nor:99', 'E<sub>g</sub>:1.5', 'd<sub>g</sub>:1.2', 'ntr:99']},
  #{'name':'PSMF', 'values':['pres:3.0', 'psfac:0.34']},
  #{'name':'FRES', 'values':['res:3.0',]},
  #{'name':'ESEL', 'values':['Emin:', 'dlim:1.0']},
  #{'name':'SHEL', 'values':['dmax:', 'dmin:0']},
  #{'name':'PATS', 'values':['+np or -dis:100', 'npt:', 'nf:5']},
  #{'name':'GROP', 'values':['nor:99', 'E<sub>g</sub>:1.5', 'd<sub>g</sub>:1.2', 'ntr:99']},
  #{'name':'PSMF', 'values':['pres:3.0', 'psfac:0.34']},
  #{'name':'FRES', 'values':['res:3.0',]},

  #{'name':'DSUL', 'values':['nss:0',]},
  #{'name':'TANG', 'values':['ftan:0.9', 'fex:0.4']},
  #{'name':'NTPR', 'values':['ntpr:100',]},
  #{'name':'SKIP', 'values':['min2:0.5',]},
  #{'name':'WEED', 'values':['fr:0.3',]},
  #{'name':'CCWT', 'values':['g:0.1',]},
  #{'name':'TEST', 'values':['CCmin:', 'delCC:']},
  #{'name':'KEEP', 'values':['nh:0',]},
  #{'name':'PREJ', 'values':['max:3', 'dsp:-0.01', 'mf:1']},
  #{'name':'SEED', 'values':['nrand:0',]},
  #{'name':'MOVE', 'values':['dx:0', 'dy:0', 'dz:0', 'sign:1']},



def get_program_dictionaries(cRPD=None, cSPD=None):
  global SPD
  global RPD

  if not cRPD or not cSPD:
    if RPD and SPD:
      return SPD, RPD
    else:
      SPD, RPD = defineExternalPrograms()
  return SPD, RPD

def get_managed_reference_set():
  global managed_references
  if managed_references: return managed_references
  sd, rd = get_program_dictionaries()
  rl = []
  for p in sd: rl.append(p.reference)
  for p in rd: rl.append(p.reference)
  managed_references = set([''.join(x.replace('\r', '').split()) for x in rl])
  return managed_references

def get_known(kind):
  sd, rd = get_program_dictionaries()
  if kind == 'solution':
    src = sd
  else:
    src = rd
  rv = []
  for p in src:
    rv.append(p.name)
  rv = sorted(rv, key=lambda s: s.lower())
  return ';'.join(rv)

olex.registerFunction(get_known, False, "programs")

if __name__ == '__main__':
  SPD, RPD = defineExternalPrograms()
