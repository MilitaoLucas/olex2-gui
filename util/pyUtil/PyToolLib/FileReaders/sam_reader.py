import os
import sys
import pprint
import xml.dom.minidom as minidom
from xml.dom.minidom import Node
import time

def metareader(sam_file,metadata):
  metadata['key'] = key
  rFileMeta = os.path.join(sam_file)
  print("MetaData File: ", rFileMeta)
  time.sleep(2)
  if os.path.exists(rFileMeta):
    if os.path.getsize(rFileMeta) < 1:
      print("Index empty")
    else:
      rFileM = open(rFileMeta,'r')
      for line in rFileM:
        mFileC = line
      rFileM.close()
      xmldoc = minidom.parse(rFileMeta)
      keywords= ['Cell', 'CellESD','MountType', 'CrystalSize', 'SpaceGroup', 'ScreenScans', 'CollectScans']
      #keywords= ['contributors']
      XScansValues = {}
      for keyword in keywords:
        if keyword == 'ScreenScans' or keyword == 'CollectScans':
          print("This is the XScans index what joy")
          XScans = xmldoc.getElementsByTagName(keyword)[0]
          #print XScans.toprettyxml()
          ai = 0
          for parent_name in XScans.getElementsByTagName('Scan'):
            #print parent_name.toprettyxml()
            #print parent_name.getElementsByTagName('ScanRange')[0].toprettyxml()
            #print parent_name.getElementsByTagName('GonioAxes')[0].toprettyxml()
            #print parent_name.getElementsByTagName('DetectorSettings')[0].toprettyxml()
            #print parent_name.getElementsByTagName('DetectorMode')[0].toprettyxml()
            ScanRange = parent_name.getElementsByTagName('ScanRange')[0].toxml()
            GonioAxes = parent_name.getElementsByTagName('GonioAxes')[0].toxml()
            DetectorSettings = parent_name.getElementsByTagName('DetectorSettings')[0].toxml()
            DetectorMode = parent_name.getElementsByTagName('DetectorMode')[0].toxml()
            XScansValues[ai] = {'ScanRange' : ScanRange, 'GonioAxes' : GonioAxes, 'DetectorSettings' : DetectorSettings, 'DetectorMode' : DetectorMode}
            ai=ai+1
        else:
          reflist = []
          name_result = []
          try:
            name = xmldoc.getElementsByTagName(keyword)
            #print "R: ", keyword, " : ", name[0].toxml().strip()
            #print "E:      ", name[0].attributes
          except:
            print("Missing: ", keyword)
            continue
          name_result.append(name[0].toxml().strip())
          name_result_joined = "".join(name_result)
          #print "something", name_result_joined
          metadata[keyword] = name_result_joined
        metadata['XScansValues'] = XScansValues
          #print a.value
  else:
    print("missing metadata file", rFileMeta)
    sys.exit(2)
  return metadata

if __name__ == '__main__':
  key = '/home/xray/olextrunk/jew--B00159--Crystal_2.sam'
  metadata = {}
  a = metareader(key, metadata)
  print("metadata")
  for keys in a:
    print(keys,':', a[keys],'\n')
  """  
  b = a['authors']
  print b
  for ai in b:
    print b[ai]['surname'],b[ai]['given_name']
  """
"""
  <ScreenScans>
    <Scan ScanNumber = "1" Axis = "Omega">
      <ScanRange Start = "-101.0" End = "70.0" Width = "1.0" Step = "10.0" Images = "18"/>
      <GonioAxes ChiOrKappa = "10.0" PhiOrOmega = "0.0"/>
      <DetectorSettings Distance = "40.0" Exposure = "20.0" TwoTheta = "-20.0"/>
      <DetectorMode Binning = "2" Dezinger = "No"/>
    </Scan>
  </ScreenScans>
  <CollectScans>
    <Scan ScanNumber = "1" Axis = "Omega">
      <ScanRange Start = "-110.0" End = "15.0" Width = "1.0" Step = "1.0" Images = "125"/>
      <GonioAxes ChiOrKappa = "-68.0" PhiOrOmega = "0.0"/>
      <DetectorSettings Distance = "40.0" Exposure = "10.0" TwoTheta = "-20.0"/>
      <DetectorMode Binning = "2" Dezinger = "No"/>
    </Scan>
"""
