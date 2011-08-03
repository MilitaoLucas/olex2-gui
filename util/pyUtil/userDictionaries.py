# userDictionaries.py
import os
import pickle

import olex
import olx

from olexFunctions import OlexFunctions
OV = OlexFunctions()

people = None
localList = None

class People:
  def __init__(self):
    self.dictionary = getLocalDictionary('people')
    global people
    people = self
    OV.registerFunction(self.getPersonInfo)
    OV.registerFunction(self.changePersonInfo)
    OV.registerFunction(self.addNewPerson)

  def getPersonInfo(self,person,item):
    retStr = '?'
    if not person:
      return retStr
    if not self.isPerson(person):
      self.addNewPerson(person)
    currentPersonInfo = self.dictionary['people'][person]

    if item in ('phone','email','address'):
      retStr = currentPersonInfo[item]

    return retStr

  def changePersonInfo(self,person,item,info):
    if not person:
      return
    elif not self.isPerson(person):
      self.addNewPerson(person)

    if item in ('email','phone','address'):
      self.dictionary['people'][person][item] = info

    #print "Changed %s for %s to %s" %(item,person,info)
    saveLocalDictionary(self.dictionary)

  def isPerson(self,person):
    return self.dictionary['people'].has_key(person)

  def addNewPerson(self,person):
    currentPersonInfo = {'email':'?','phone':'?','address':'?'}
    self.dictionary['people'].setdefault(person, currentPersonInfo)
    listPeople = ''
    for item in self.dictionary['people'].keys():
      listPeople += '%s;' %item
    OV.SetParam('snum.metacif.list_people', listPeople)
    saveLocalDictionary(self.dictionary)

  def getListPeople(self):
    return self.getList('people')

  def getList(self,whatList):
    retStr = ''
    for item in sorted(self.dictionary[whatList].keys()):
      retStr += '%s;' %item
    return retStr

class LocalList:
  def __init__(self):
    self.dictionary = {}
    self.dictionary.setdefault('journals',getLocalDictionary('journals')['journals'])
    self.dictionary.setdefault('diffractometers',getLocalDictionary('diffractometers')['diffractometers'])
    global localList
    localList = self
    OV.registerFunction(self.addToLocalList)
    OV.registerFunction(self.setDiffractometerDefinitionFile)

  def addToLocalList(self,newValue, whatList):
    if whatList == 'requested_journal':
      whatList = 'journals'
      journalType = 'requested'
    elif whatList == 'reference_journal':
      whatList = 'journals'
      journalType = 'reference'

    if whatList in ('diffractometers','journals'):
      if not self.dictionary[whatList].has_key(newValue):
        if whatList == 'diffractometers':
          self.dictionary[whatList].setdefault(newValue,{'cif_def':'?'})
        else:
          self.dictionary[whatList].setdefault(newValue,'')

        saveDict = {whatList:self.dictionary[whatList]}
        saveLocalDictionary(saveDict)

      if whatList == 'diffractometers':
        OV.SetParam('snum.report.diffractometer', newValue)
        if not os.path.exists(self.getDiffractometerDefinitionFile(newValue)):
          OV.SetParam('snum.metacif.diffrn_measurement_device_type', newValue)
      elif whatList == 'journals':
        if journalType == 'requested':
          OV.set_cif_item('_publ_requested_journal', newValue)
        elif journalType == 'reference':
          OV.SetVar('snum_dimas_reference_journal_name', newValue)
    else:
      print "Argument %s not allowed for parameter whatList" %whatList
    return ""

  def getListJournals(self):
    return self.getList('journals')

  def getListDiffractometers(self):
    return self.getList('diffractometers')

  def getList(self,whatList):
    retStr = ''
    for item in sorted(self.dictionary[whatList].keys()):
      retStr += '%s;' %item
    return retStr

  def setDiffractometerDefinitionFile(self,diffractometer,filepath):
    if os.path.exists(filepath):
      if diffractometer in ('?',''):
        diffractometer = OV.FileName(filepath)
        self.addToLocalList(diffractometer,'diffractometers')
      self.dictionary['diffractometers'][diffractometer]['cif_def'] = filepath
      saveDict = {'diffractometers':self.dictionary['diffractometers']}
      saveLocalDictionary(saveDict)
    else:
      print "The file specified does not exist"
    return ''

  def getDiffractometerDefinitionFile(self,diffractometer):
    try:
      cif_def = self.dictionary['diffractometers'][diffractometer]['cif_def']
    except KeyError:
      cif_def = '?'
    return cif_def


def getLocalDictionary(whichDict):
  picklePath = getPicklePath(whichDict)
  if not os.path.exists(picklePath):
    createNewLocalDictionary(whichDict)

  pfile = open(picklePath)
  dictionary = pickle.load(pfile)
  pfile.close()
  if whichDict == 'diffractometers':
    dictionary = convertDiffractometerDictionary(dictionary)

  return dictionary

def convertDiffractometerDictionary(dictionary):
  if '' in dictionary['diffractometers'].values():
    for item, value in dictionary['diffractometers'].items():
      if value == '':
        dictionary['diffractometers'][item] = {'cif_def':'?'}
    saveLocalDictionary(dictionary)
  return dictionary

def createNewLocalDictionary(whichDict):
  import variableFunctions
  picklePath = getPicklePath(whichDict)
  if whichDict == 'people':
    dictionary = {
      'people':{
        },
    }
  elif whichDict == 'diffractometers':
    dictionary = {
      'diffractometers':{
        },
    }
  elif whichDict == 'journals':
    dictionary = {
      'journals':{
        '?':'',
        'Acta Cryst':'',
        'Acta Crystallogr.,Sect.B:Struct.Sci.':'',
        'Acta Crystallogr.,Sect.C:Cryst.Struct.Commun.':'',
        'Acta Crystallogr.,Sect.E:Struct.Rep.Online':'',
        'Adv.Mater.':'',
        'Angew.Chem.':'',
        'Int.Ed.':'',
        'Appl.Organomet.Chem.':'',
        'Aust.J.Chem.':'',
        'Beilstein J.Org.Chem.':'',
        'C.R.Chim.':'',
        'Can.J.Chem.':'',
        'Chem.-Eur.J.':'',
        'Chem.Commun.':'',
        'Chem.Mater.':'',
        'Collect.Czech.Chem.Commun.':'',
        'Cryst.Growth Des.':'',
        'Crystal Engineering':'',
        'CrystEngComm':'',
        'Dalton Trans.':'',
        'Eur.J.Inorg.Chem.':'',
        'Eur.J.Org.Chem.':'',
        'Faraday Discuss.':'',
        'Helv.Chim.Acta':'',
        'Heteroat.Chem.':'',
        'Inorg.Chem.':'',
        'Inorg.Chem.Commun.':'',
        'Inorg.Chim.Acta':'',
        'J.Am.Chem.Soc.':'',
        'J.Chem.Soc.,Dalton Trans.':'',
        'J.Chem.Soc.,Perkin Trans.1':'',
        'J.Chem.Soc.,Perkin Trans.2':'',
        'J.Cluster Sci.':'',
        'J.Fluorine Chem.':'',
        'J.Heterocycl.Chem.':'',
        'J.Inclusion Phenom.Macrocyclic Chem.':'',
        'J.Mater.Chem.':'',
        'J.Mol.Struct.':'',
        'J.Org.Chem.':'',
        'J.Organomet.Chem.':'',
        'J.Phys.Chem.A':'',
        'J.Phys.Org.Chem.':'',
        'J.Polym.Sci.,Part A:Polym.Chem.':'',
        'Nanotechnology':'',
        'Nat.Mater':'',
        'New J.Chem.(Nouv.J.Chim.)':'',
        'Nonlinear Optics':'',
        'Org.Biomol.Chem.':'',
        'Organic Letters':'',
        'Organometallics':'',
        'Polyhedron':'',
        'Private Communication':'',
        'Struct.Chem.':'',
        'Synlett':'',
        'Synth.Met.':'',
        'Synthesis':'',
        'Tetrahedron':'',
        'Tetrahedron Lett.':'',
        'Tetrahedron:Asymm.':'',
        'Z.Anorg.Allg.Chem.':'',
        'Zh.Org.Khim.(Russ.)(Russ.J.Org.Chem.)':'',
      }
    }
  variableFunctions.Pickle(dictionary,picklePath)

def saveLocalDictionary(dictionary):
  import variableFunctions
  if dictionary.has_key('people'):
    picklePath = getPicklePath('people')
  elif dictionary.has_key('journals'):
    picklePath = getPicklePath('journals')
  elif dictionary.has_key('diffractometers'):
    picklePath = getPicklePath('diffractometers')
  variableFunctions.Pickle(dictionary,picklePath)

def getPicklePath(whichDict):
  directory = OV.DataDir()
  picklePath = r'%s/%s.pickle' %(directory,whichDict)
  return picklePath
