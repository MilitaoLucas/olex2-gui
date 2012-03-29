import olex
import olx
import os

from olexFunctions import OlexFunctions
OV = OlexFunctions()


def GetCheckcifReport(outputtype='pdf'):
  import HttpTools
  
  output = OV.GetParam('user.cif.checkcif.format')
  if output:
    outputtype = output

  file_name = os.path.normpath(olx.file.ChangeExt(OV.FileFull(),'cif'))
  if not os.path.exists(file_name):
    print "\n ++ There is no cif file to check! Please add the 'ACTA' command to Shelx!"
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
    "runtype": "symmonly",
    "referer": "checkcif_server",
    "outputtype": outputtype.upper(),
    "file": cif
  }

  response = HttpTools.make_url_call(OV.GetParam('user.cif.checkcif.url'), params)

  rFile.close()
  #outputtype = 'htm'
  if outputtype == "html":
    wFile = open(out_file_name,'w')
    wFile.write(response.read())
    wFile.close()
  elif outputtype == "pdf":
    rawFile = open("raw_cifreport.htm",'w')
    l = response.readlines()
    for line in l:
      rawFile.write(line)
      if "Download checkCIF report" in line:
        href = line.split('"')[1]
        response = HttpTools.make_url_call(href,"")
        txt = response.read()
        wFile = open(out_file_name,'wb')
        wFile.write(txt)
        wFile.close()
    rawFile.close()
  olx.Shell('%s'%os.path.join(OV.FilePath(),out_file_name))

OV.registerFunction(GetCheckcifReport, False, 'cif')
