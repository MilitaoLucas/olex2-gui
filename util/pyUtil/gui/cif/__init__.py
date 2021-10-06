# py 2to3 compatibility

import olex
import olx
import os
import time
import gui
from olexFunctions import OlexFunctions
OV = OlexFunctions()
debug = bool(OV.GetParam('olex2.debug',False))

def threadPrint(str):
  olx.Schedule(1, "post \"%s\"" %str)

def extractHtmlValueFromLine(line, name):
  idx = line.find(name)
  if idx !=-1:
    toks = line[idx:].split('"')
    if len(toks) > 3 and toks[1].strip() == 'value=':
      return toks[2]
  return None

def GetCheckcifReport(outputtype='pdf', send_fcf=False):
  import HttpTools
  #t_ = time.time()
  output = OV.GetParam('user.cif.checkcif.format')
  if output:
    outputtype = output

  file_name = os.path.normpath(olx.file.ChangeExt(OV.FileFull(),'cif'))
  if not os.path.exists(file_name):
    threadPrint("\n ++ There is no cif file to check! Please add the 'ACTA' command to Shelx!")
    return
  out_file_name = "%s_cifreport.%s" %(OV.FileName(), outputtype)
  eindex = 1
  while os.path.exists(out_file_name):
    try:
      os.remove(out_file_name)
    except:
      out_file_name = "%s_cifreport-%i.%s" %(OV.FileName(), eindex, outputtype)
      eindex += 1

  metacif_path = '%s/%s.metacif' %(OV.StrDir(), OV.FileName())
  OV.CifMerge(metacif_path)

  rFile = open(file_name, 'rb')
  cif = rFile

  params = {
    "file": cif,
    "runtype": "symmonly",
    "referer": "checkcif_server",
    "outputtype": outputtype.upper(),
    'validtype': 'checkcif_only'
  }

  fcf_name = os.path.normpath(olx.file.ChangeExt(OV.FileFull(),'fcf'))
  if send_fcf:
    if not os.path.exists(fcf_name):
      threadPrint("You have requested full Checkcif report, but unfortunately the FCF file could not be located."+\
                  "\nPlease make sure that there is LIST 4 instruction is in your INS file before the refinement.")
      send_fcf = False
    else:
      params['validtype'] = 'checkcif_with_hkl'
  response = None
  threadPrint('Sending report request')
  try:
    if send_fcf:
      url = OV.GetParam('user.cif.checkcif.hkl_url')
    else:
      url = OV.GetParam('user.cif.checkcif.url')
    response = HttpTools.make_url_call(url, params, http_timeout=120)
  except Exception as e:
    threadPrint('Failed to receive Checkcif report...')
  finally:
    rFile.close()

  if not response: return

  if send_fcf: #file exists, correct URL picked
    line = ''.join(response.readlines())
    cif_id = extractHtmlValueFromLine(line, "Qcifid")
    cif_data_block = extractHtmlValueFromLine(line, "Qdatablock")
    if cif_id is None or cif_data_block is None:
      threadPrint("Could not locate CIF identification fields, aborting...")
      return
    fcf_file = open(fcf_name, 'rb')
    params['filehkl'] = fcf_file
    params['Qcifid'] = cif_id
    params['Qdatablock'] = cif_data_block
    del params['file']
    try:
      response = HttpTools.make_url_call(url, params, http_timeout=120)
    except Exception as e:
      threadPrint('Failed to receive full Checkcif report...')
    finally:
      fcf_file.close()

  if not response: return

  #outputtype = 'htm'
  if outputtype == "html":
    wFile = open(out_file_name,'w')
    wFile.write(response.read())
    wFile.close()
    threadPrint('Done')
  elif outputtype == "pdf":
    l = response.readlines()
    for line in l:
      if "checkcif.pdf" in line:
        href = line.split('"')[1]
        if href.startswith("//"):
          href = "https:" + href
        threadPrint('Downloading PDF report')
        response = None
        try:
          response = HttpTools.make_url_call(href,"")
          threadPrint('Done')
        except Exception as e:
          threadPrint('Failed to download PDF report...')
          print(e)
        if not response:
          return
        txt = response.read()
        wFile = open(out_file_name,'wb')
        wFile.write(txt)
        wFile.close()
  fileName = '%s'%os.path.join(OV.FilePath(),out_file_name)
  olx.Schedule(1, "spy.threading.shell.run(\"%s\")" %fileName)
  #print time.time() -t_


#OV.registerFunction(GetCheckcifReport, False, 'cif')


def is_it_global(string):
  retVal = False
  if 'global' in string.lower():
    retVal = True
  elif 'general' in string.lower():
    retVal = True
  elif string == "":
    retVal = True
  return retVal

def get_snums_in_cif():
  snums = []
  if OV.FileExt() != "cif":
    return [OV.FileName()]
  cnt = int(olx.xf.DataCount())
  for i in range(0, cnt):
    name = olx.xf.DataName(i)
    if not is_it_global(name):
      snums.append(name)
  return snums

def check_for_embedded_hkl():
  if olx.IsFileType('CIF') == 'false':
    return ""
  hklfile = os.path.join(olx.FilePath(), "%s%s" %(olx.xf.DataName(olx.xf.CurrentData()),".hkl"))
  if os.path.exists(hklfile):
    return "hkl file already exists"
  res = True
  res1 = olx.Cif('_shelx_hkl_file')
  res2 = olx.Cif('_iucr_refine_reflections_details')
  res3 = olx.Cif('_refln_index_h')
  res4 = olx.Cif('_diffrn_refln_index_h')
  if res1 == 'n/a' and res2 == 'n/a' and res3 == 'n/a' and res4 == 'n/a':
    res = olx.Cif('_refln', 0)
    res = False
  if res:
    reapfile = "%s%s" %(olx.xf.DataName(olx.xf.CurrentData()),".res")
    d = {'reapfile': reapfile}
    retVal = gui.tools.TemplateProvider.get_template('cif_export_gui',force=debug)%d
  else:
    retVal = "No hkl data embedded"

  return retVal
olex.registerFunction(check_for_embedded_hkl, False, "gui.cif")
