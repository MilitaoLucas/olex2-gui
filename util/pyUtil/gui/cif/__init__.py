import olex
import olx
import os
import time

from olexFunctions import OlexFunctions
OV = OlexFunctions()


def GetCheckcifReport(outputtype='pdf'):
  import HttpTools
  #t_ = time.time()
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
  response = None
  print 'Sending report request'
  try:
    response = HttpTools.make_url_call(OV.GetParam('user.cif.checkcif.url'), params)
  except Exception, e:
    print 'Failed to receive Checkcif report...'
    print e

  rFile.close()
  if not response:
    return
  #outputtype = 'htm'
  if outputtype == "html":
    wFile = open(out_file_name,'w')
    wFile.write(response.read())
    wFile.close()
  elif outputtype == "pdf":
    l = response.readlines()
    for line in l:
      if "Download checkCIF report" in line:
        href = line.split('"')[1]
        print 'Downloading PDF report'
        response = None
        try:
          response = HttpTools.make_url_call(href,"")
          print 'Done'
        except Exception, e:
          print 'Failed to download PDF report...'
          print e
        if not response:
          return
        txt = response.read()
        wFile = open(out_file_name,'wb')
        wFile.write(txt)
        wFile.close()
  fileName = '%s'%os.path.join(OV.FilePath(),out_file_name)
  olx.Schedule(1, "'spy.threading.shell.run(\"%s\")'" %fileName)
  #print time.time() -t_


#OV.registerFunction(GetCheckcifReport, False, 'cif')
