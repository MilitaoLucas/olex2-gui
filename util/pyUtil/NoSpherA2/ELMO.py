from olexFunctions import OV

def get_ntail_list():
  # for tailor made residues in ELMOdb
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    ntail_list = ['1',]
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if maxtail == 1:
      ntail_list_str = "1;"
    else:
      for n in range(1,maxtail):
        ntail_list.append(str(n+1))
        ntail_list_str = ';'.join(ntail_list)
    return ntail_list_str
OV.registerFunction(get_ntail_list,False,'NoSpherA2')

def get_resname():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    resnames = OV.GetParam('snum.NoSpherA2.ELMOdb.str_resname')
    resnames = resnames.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(resnames) < maxtail:
      diff = maxtail - len(resnames)
      for i in range(diff):
        resnames.append('???')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return resnames[n]
OV.registerFunction(get_resname,False,'NoSpherA2')

def get_nat():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    nat = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nat')
    nat = nat.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(nat) < maxtail:
      diff = maxtail - len(nat)
      for i in range(diff):
        nat.append('0')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return nat[n]
OV.registerFunction(get_nat,False,'NoSpherA2')

def get_nfrag():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    nfrag = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nfrag')
    nfrag = nfrag.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(nfrag) < maxtail:
      diff = maxtail - len(nfrag)
      for i in range(diff):
        nfrag.append('1')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return nfrag[n]
OV.registerFunction(get_nfrag,False,'NoSpherA2')

def get_ncltd():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    ncltd = OV.GetParam('snum.NoSpherA2.ELMOdb.str_ncltd')
    ncltd = ncltd.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(ncltd) < maxtail:
      diff = maxtail - len(ncltd)
      for i in range(diff):
        ncltd.append(False)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return ncltd[n]
OV.registerFunction(get_ncltd,False,'NoSpherA2')

def get_specac():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    specac = OV.GetParam('snum.NoSpherA2.ELMOdb.str_specac')
    specac = specac.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(specac) < maxtail:
      diff = maxtail - len(specac)
      for i in range(diff):
        specac.append(False)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return specac[n]
OV.registerFunction(get_specac,False,'NoSpherA2')

def get_exbsinp():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    exbsinp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_exbsinp')
    exbsinp = exbsinp.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(exbsinp) < maxtail:
      diff = maxtail - len(exbsinp)
      for i in range(diff):
        exbsinp.append('')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return exbsinp[n]
OV.registerFunction(get_exbsinp,False,'NoSpherA2')

def get_fraginp():
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    fraginp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_fraginp')
    fraginp = fraginp.split(';')
    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(fraginp) < maxtail:
      diff = maxtail - len(fraginp)
      for i in range(diff):
        fraginp.append('0')
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    return fraginp[n]
OV.registerFunction(get_fraginp,False,'NoSpherA2')

def change_resname(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    resnames = OV.GetParam('snum.NoSpherA2.ELMOdb.str_resname')
    resnames = resnames.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(resnames) < maxtail:
      diff = maxtail - len(resnames)
      for i in range(diff):
        resnames.append([])
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    resnames[n] = input
    str_resname = resnames
    str_resname = ";".join([str(i) for i in resnames])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_resname', str_resname)
    return resnames[n]
OV.registerFunction(change_resname,False,'NoSpherA2')

def change_nat(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    nat = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nat')
    nat = nat.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(nat) < maxtail:
      diff = maxtail - len(nat)
      for i in range(diff):
        nat.append(0)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    nat[n] = input
    str_nat = nat
    str_nat = ";".join([str(i) for i in nat])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_nat', str_nat)
    return nat[n]
OV.registerFunction(change_nat,False,'NoSpherA2')

def change_nfrag(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    nfrag = OV.GetParam('snum.NoSpherA2.ELMOdb.str_nfrag')
    nfrag = nfrag.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(nfrag) < maxtail:
      diff = maxtail - len(nfrag)
      for i in range(diff):
        nfrag.append(1)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    nfrag[n] = input
    str_nfrag = nfrag
    str_nfrag = ";".join([str(i) for i in nfrag])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_nfrag', str_nfrag)
    return nfrag[n]
OV.registerFunction(change_nfrag,False,'NoSpherA2')

def change_ncltd(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    ncltd = OV.GetParam('snum.NoSpherA2.ELMOdb.str_ncltd')
    ncltd = ncltd.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(ncltd) < maxtail:
      diff = maxtail - len(ncltd)
      for i in range(diff):
        ncltd.append(False)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    ncltd[n] = input
    str_ncltd = ncltd
    str_ncltd = ";".join([str(i) for i in ncltd])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_ncltd', str_ncltd)
    return ncltd[n]
OV.registerFunction(change_ncltd,False,'NoSpherA2')

def change_specac(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    specac = OV.GetParam('snum.NoSpherA2.ELMOdb.str_specac')
    specac = specac.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(specac) < maxtail:
      diff = maxtail - len(specac)
      for i in range(diff):
        specac.append(False)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    specac[n] = input
    str_specac = specac
    str_specac = ";".join([str(i) for i in specac])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_specac', str_specac)
    return specac[n]
OV.registerFunction(change_specac,False,'NoSpherA2')

def change_exbsinp(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    exbsinp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_exbsinp')
    exbsinp = exbsinp.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(exbsinp) < maxtail:
      diff = maxtail - len(exbsinp)
      for i in range(diff):
        exbsinp.append(0)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    exbsinp[n] = input
    str_exbsinp = exbsinp
    str_exbsinp = ";".join([str(i) for i in exbsinp])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_exbsinp', str_exbsinp)
    return exbsinp[n]
OV.registerFunction(change_exbsinp,False,'NoSpherA2')

def change_fraginp(input):
  tail = OV.GetParam('snum.NoSpherA2.ELMOdb.tail')
  if tail == True:
    fraginp = OV.GetParam('snum.NoSpherA2.ELMOdb.str_fraginp')
    fraginp = fraginp.split(';')

    maxtail = OV.GetParam('snum.NoSpherA2.ELMOdb.maxtail')
    if len(fraginp) < maxtail:
      diff = maxtail - len(fraginp)
      for i in range(diff):
        fraginp.append(0)
    ntail = OV.GetParam('snum.NoSpherA2.ELMOdb.ntail')
    n = ntail - 1
    fraginp[n] = input
    str_fraginp = fraginp
    str_fraginp = ";".join([str(i) for i in fraginp])
    OV.SetParam('snum.NoSpherA2.ELMOdb.str_fraginp', str_fraginp)
    return fraginp[n]
OV.registerFunction(change_fraginp,False,'NoSpherA2')