from olexFunctions import OV
from variableFunctions import nsa2_get_param, nsa2_set_param

def get_ntail_list():
  # for tailor made residues in ELMOdb
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    ntail_list = ['1',]
    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if maxtail == 1:
      ntail_list_str = "1;"
    else:
      for n in range(1,maxtail):
        ntail_list.append(str(n+1))
        ntail_list_str = ';'.join(ntail_list)
    return ntail_list_str
OV.registerFunction(get_ntail_list,False,'NoSpherA2')

def get_resname():
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    resnames = nsa2_get_param('ELMOdb.str_resname')
    resnames = resnames.split(';')
    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(resnames) < maxtail:
      diff = maxtail - len(resnames)
      for i in range(diff):
        resnames.append('???')
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    return resnames[n]
OV.registerFunction(get_resname,False,'NoSpherA2')

def get_nat():
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    nat = nsa2_get_param('ELMOdb.str_nat')
    nat = nat.split(';')
    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(nat) < maxtail:
      diff = maxtail - len(nat)
      for i in range(diff):
        nat.append('0')
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    return nat[n]
OV.registerFunction(get_nat,False,'NoSpherA2')

def get_nfrag():
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    nfrag = nsa2_get_param('ELMOdb.str_nfrag')
    nfrag = nfrag.split(';')
    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(nfrag) < maxtail:
      diff = maxtail - len(nfrag)
      for i in range(diff):
        nfrag.append('1')
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    return nfrag[n]
OV.registerFunction(get_nfrag,False,'NoSpherA2')

def get_ncltd():
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    ncltd = nsa2_get_param('ELMOdb.str_ncltd')
    ncltd = ncltd.split(';')
    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(ncltd) < maxtail:
      diff = maxtail - len(ncltd)
      for i in range(diff):
        ncltd.append(False)
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    return ncltd[n]
OV.registerFunction(get_ncltd,False,'NoSpherA2')

def get_specac():
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    specac = nsa2_get_param('ELMOdb.str_specac')
    specac = specac.split(';')
    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(specac) < maxtail:
      diff = maxtail - len(specac)
      for i in range(diff):
        specac.append(False)
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    return specac[n]
OV.registerFunction(get_specac,False,'NoSpherA2')

def get_exbsinp():
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    exbsinp = nsa2_get_param('ELMOdb.str_exbsinp')
    exbsinp = exbsinp.split(';')
    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(exbsinp) < maxtail:
      diff = maxtail - len(exbsinp)
      for i in range(diff):
        exbsinp.append('')
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    return exbsinp[n]
OV.registerFunction(get_exbsinp,False,'NoSpherA2')

def get_fraginp():
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    fraginp = nsa2_get_param('ELMOdb.str_fraginp')
    fraginp = fraginp.split(';')
    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(fraginp) < maxtail:
      diff = maxtail - len(fraginp)
      for i in range(diff):
        fraginp.append('0')
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    return fraginp[n]
OV.registerFunction(get_fraginp,False,'NoSpherA2')

def change_resname(input):
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    resnames = nsa2_get_param('ELMOdb.str_resname')
    resnames = resnames.split(';')

    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(resnames) < maxtail:
      diff = maxtail - len(resnames)
      for i in range(diff):
        resnames.append([])
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    resnames[n] = input
    str_resname = resnames
    str_resname = ";".join([str(i) for i in resnames])
    nsa2_set_param('ELMOdb.str_resname', str_resname)
    return resnames[n]
OV.registerFunction(change_resname,False,'NoSpherA2')

def change_nat(input):
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    nat = nsa2_get_param('ELMOdb.str_nat')
    nat = nat.split(';')

    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(nat) < maxtail:
      diff = maxtail - len(nat)
      for i in range(diff):
        nat.append(0)
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    nat[n] = input
    str_nat = nat
    str_nat = ";".join([str(i) for i in nat])
    nsa2_set_param('ELMOdb.str_nat', str_nat)
    return nat[n]
OV.registerFunction(change_nat,False,'NoSpherA2')

def change_nfrag(input):
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    nfrag = nsa2_get_param('ELMOdb.str_nfrag')
    nfrag = nfrag.split(';')

    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(nfrag) < maxtail:
      diff = maxtail - len(nfrag)
      for i in range(diff):
        nfrag.append(1)
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    nfrag[n] = input
    str_nfrag = nfrag
    str_nfrag = ";".join([str(i) for i in nfrag])
    nsa2_set_param('ELMOdb.str_nfrag', str_nfrag)
    return nfrag[n]
OV.registerFunction(change_nfrag,False,'NoSpherA2')

def change_ncltd(input):
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    ncltd = nsa2_get_param('ELMOdb.str_ncltd')
    ncltd = ncltd.split(';')

    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(ncltd) < maxtail:
      diff = maxtail - len(ncltd)
      for i in range(diff):
        ncltd.append(False)
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    ncltd[n] = input
    str_ncltd = ncltd
    str_ncltd = ";".join([str(i) for i in ncltd])
    nsa2_set_param('ELMOdb.str_ncltd', str_ncltd)
    return ncltd[n]
OV.registerFunction(change_ncltd,False,'NoSpherA2')

def change_specac(input):
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    specac = nsa2_get_param('ELMOdb.str_specac')
    specac = specac.split(';')

    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(specac) < maxtail:
      diff = maxtail - len(specac)
      for i in range(diff):
        specac.append(False)
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    specac[n] = input
    str_specac = specac
    str_specac = ";".join([str(i) for i in specac])
    nsa2_set_param('ELMOdb.str_specac', str_specac)
    return specac[n]
OV.registerFunction(change_specac,False,'NoSpherA2')

def change_exbsinp(input):
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    exbsinp = nsa2_get_param('ELMOdb.str_exbsinp')
    exbsinp = exbsinp.split(';')

    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(exbsinp) < maxtail:
      diff = maxtail - len(exbsinp)
      for i in range(diff):
        exbsinp.append(0)
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    exbsinp[n] = input
    str_exbsinp = exbsinp
    str_exbsinp = ";".join([str(i) for i in exbsinp])
    nsa2_set_param('ELMOdb.str_exbsinp', str_exbsinp)
    return exbsinp[n]
OV.registerFunction(change_exbsinp,False,'NoSpherA2')

def change_fraginp(input):
  tail = nsa2_get_param('ELMOdb.tail')
  if tail:
    fraginp = nsa2_get_param('ELMOdb.str_fraginp')
    fraginp = fraginp.split(';')

    maxtail = nsa2_get_param('ELMOdb.maxtail')
    if len(fraginp) < maxtail:
      diff = maxtail - len(fraginp)
      for i in range(diff):
        fraginp.append(0)
    ntail = nsa2_get_param('ELMOdb.ntail')
    n = ntail - 1
    fraginp[n] = input
    str_fraginp = fraginp
    str_fraginp = ";".join([str(i) for i in fraginp])
    nsa2_set_param('ELMOdb.str_fraginp', str_fraginp)
    return fraginp[n]
OV.registerFunction(change_fraginp,False,'NoSpherA2')