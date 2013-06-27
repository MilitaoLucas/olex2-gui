# userDictionaries.py
import os
import pickle

import olex
import olx

from olexFunctions import OlexFunctions
OV = OlexFunctions()

people = None
persons = None
localList = None
affiliations = None
experimantal = None

class People:
  def __init__(self):
    self.dictionary = getLocalDictionary('people')
    global people
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
  
  def get_person_details(self, person):
    return person

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
        OV.set_cif_item('_diffrn_measurement_device_type', newValue)
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



class Affiliations:
  def __init__(self):
    global affiliations
    affiliations = self
    OV.registerFunction(self.getListAffiliations)
    OV.registerFunction(self.add_affiliation)
    try:
      self.new_affiliation_db()
    except:
      pass

  def new_affiliation_db(self):
    cursor = DBConnection.conn.cursor()
    cursor.execute("""CREATE TABLE affiliations
                      (Name TEXT, Department TEXT, Address1 TEXT, Address2 TEXT, City TEXT, PostCode TEXT, Region TEXT, Country TEXT, displayname TEXT UNIQUE) 
                   """)
    #affiliations = [
      #('Durham University', 'Department of Chemistry', 'South Road', '', 'Durham', 'DH6 1LE', 'County Durham', 'U.K', 'Durham University, Durham'),
      #('VUW', 'School of Chemical and Physical Sciences', '', '', 'Wellington', '6001', '', 'New Zealand', 'VUW, Wellington'),
      #('North Maharashtra University', 'School of Chemical Sciences', 'Umavi Nagar', '', 'Jalgaon', '425 001', '', 'India', 'North Maharashtra University Jalagon'),
      #('Vidyasagar University', 'Department of Chemistry and Chemical Technology', 'South Road', '', 'Midnapore', '7210102', 'West Bengal', 'India', 'Vidyasagar University Midnapore'),
    #]
    #cursor.executemany("INSERT INTO affiliations VALUES (?,?,?,?,?,?,?,?,?)", affiliations)
    DBConnection.conn.commit()

  def getListAffiliations(self):
    cursor = DBConnection.conn.cursor()
    sql = "SELECT * FROM affiliations"
    cursor.execute(sql)
    all_affiliations = cursor.fetchall()
    retVal = ""
    for affiliation in all_affiliations:
      retVal += "%s;" %affiliation[0]
    retVal += "-- ADD NEW --"
    return retVal
  
  def get_affiliation_address(self, affiliation, list=False):
    cursor = DBConnection.conn.cursor()
    sql = "SELECT * FROM affiliations WHERE name like '%s'" %affiliation
    cursor.execute(sql)
    address = cursor.fetchall()
    if not address:
      address = "?"
    if not list:
      address = ("\n").join(filter(None, address[0]))
    else:
      return address
    return address

  def add_affiliation(self, name, department, address1, address2, city, postcode, region, country):
    cursor = DBConnection.conn.cursor()
    conn = DBConnection.conn
    displayname = "%s %s" %(name, city)
    affiliations = [
      (name, department, address1, address2, city, postcode, region, country, displayname),
    ]
    cursor.executemany("INSERT OR REPLACE INTO affiliations VALUES (?,?,?,?,?,?,?,?,?)", affiliations)
    conn.commit()


class Persons:
  def __init__(self):
    global persons
    persons = self
    OV.registerFunction(self.getListPeople)
    OV.registerFunction(self.add_person)
    OV.registerFunction(self.getPersonInfo)
    try:
      self.new_person_db()
    except:
      pass
    
  def changePersonInfo(self,person,item,info):
    pass

  def new_person_db(self):
    cursor = DBConnection.cursor
    cursor.execute("""CREATE TABLE persons
                      (firstname TEXT, middlename TEXT, lastname TEXT, email TEXT, phone TEXT, affiliation TEXT, displayname TEXT UNIQUE) 
                   """)  
    #persons = [
      #('Horst', '', 'Puschmann', 'horst.puschmann@gmail.com', '+44 191 334 2004', 'Durham University' 'Horst Puschmann'),
      #('John', '', 'Spencer', 'john.spencer@vuw.ac.uk', '+44 191 334 2004','', ''),
    #]
    #cursor.executemany("INSERT INTO persons VALUES (?,?,?,?,?,?,?)", persons)
    DBConnection.conn.commit()

  def addNewPerson(self, name=""):
    firstname = middlename = secondname = ""
    if name:
      name = name.split()
      if len(name) == 1:
        secondname = name[0]
      elif len(name) == 2:
        firstname = name[0]
        secondname = name[1]
      elif len(name) == 3:
        firstname = name[0]
        middlename = name[1]
        secondname = name[2]
    person = (firstname, middlename, secondname, '', '', '', 'New person')
    DBConnection.conn.cursor().execute("INSERT OR REPLACE INTO persons VALUES (?,?,?,?,?,?,?)", person)
    DBConnection.conn.commit()
    d = {'firstname':person[0],
         'middlename':person[1],
         'lastname':person[2],
         'email':person[3],
         'phone':person[4],
         'affiliation':person[5],
         'displayname':person[6],
         }
    return d

  def deletePersonByDisplayname(self, displayname):
    sql = "DELETE FROM persons WHERE displayname=displayname"
    DBConnection.conn.cursor().execute(sql)
    DBConnection.conn.commit()

  def make_display_name(self, person,format="acta"):
    if format == "acta":
      if type(person) == tuple:
        surname = person[2]
        first_initial = person[0]
        second_initial = person[1]
      else:
        surname = person['lastname']
        first_initial = person['firstname']
        second_initial = person['middlename']
      if first_initial:
        first_initial = first_initial[0] + "."
      if second_initial:
        second_initial = second_initial[0] + "."

      display = "%s, %s%s" %(surname, first_initial, second_initial)

    else:
      display = "%s %s %s" %(person[0], person[1], person[2])
      display = display.replace("  ", " ")
      display = display.replace("  ", " ")
      display = display.replace("  ", " ")
    return display

  def getListPeople(self):
    cursor = DBConnection.conn.cursor()
    sql = "SELECT * FROM persons"
    cursor.execute(sql)
    all_persons = cursor.fetchall()
    retVal_l = []
    for person in all_persons:
      display = self.make_display_name(person)
      retVal_l.append(display)
    retVal_l.sort()
    retVal_l.append("-- ADD NEW --")
    retVal = ";".join(retVal_l)
    return retVal

  def getPersonInfo(self,person,item):
    retStr = '?'
    if not person:
      return retStr
#    if not self.isPerson(person):
#      self.addNewPerson(person)
    currentPersonInfo = self.get_person_details(person)
    if not currentPersonInfo:
      return retStr
    if item in ('phone','email','address'):
      if item == "address":
        retStr = self.get_person_affiliation(person)
      else:
        retStr = currentPersonInfo[item]
    return retStr

  def get_person_details(self, displayname):
    cursor = DBConnection.conn.cursor()
    if "--" in displayname or not displayname:
      person = ["","","","","","","New Person"]
    else:
      sql = "SELECT * FROM persons WHERE displayname like '%s'" %(displayname)
      cursor.execute(sql)
      res = cursor.fetchall()
      if not res:
        return
      else:
        person = res[0]
    d = {'firstname':person[0],
         'middlename':person[1],
         'lastname':person[2],
         'email':person[3],
         'phone':person[4],
         'affiliation':person[5],
         'displayname':person[6],
         }
    return d
  
  def get_person_affiliation(self, displayname, list=False):
    cursor = DBConnection.conn.cursor()
    sql = "SELECT affiliation FROM persons WHERE displayname like '%s'" %displayname
    cursor.execute(sql)
    affiliation = cursor.fetchone()
    sql = "SELECT * FROM affiliations WHERE name like '%s'" %affiliation
    cursor.execute(sql)
    address = cursor.fetchall()
    if not address:
      address = "?"
    if not list:
      address = ('\n').join(address[0][:-1])
      address = address.replace('\n\n', '\n')
      address = address.replace('\n\n', '\n')
    else:
      return address
    return address

  def add_person(self, firstname, middlename, lastname, email, phone, affiliation, displayname):
    if not displayname:
      displayname = self.make_display_name((firstname, middlename, lastname))
    cursor = DBConnection.conn.cursor()
    person = (firstname, middlename, lastname, email, phone, affiliation, displayname)
    cursor.execute("INSERT OR REPLACE INTO persons VALUES (?,?,?,?,?,?,?)", person)
    DBConnection.conn.commit()
    return person

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

def import_from_pickle(conn, cursor):
  d = getLocalDictionary('people')


def init_userDictionaries():
  global people
  global affiliations
  use_db = OV.GetParam('user.report.use_db')
  import_data = False
  if use_db:
    DBConnection()
    people = Persons()
    affiliations = Affiliations()
  else:
    people = People()
#  experimantal = Experimental(conn, cursor)
  
class DBConnection():
  conn = None
  cursor = None
  
  def __init__(self):
    if DBConnection.conn:
      return
    import sqlite3
    db_path = OV.GetParam('user.report.db_location').replace("DataDir()", OV.DataDir())
    db_name = OV.GetParam('user.report.db_name')
    db_file = "%s/%s" %(db_path, db_name)
    if not os.path.exists(db_path):
      os.makedirs(db_path)
    if not os.path.exists(db_file):
      import_data = True
      wFile = open(db_file,'w')
      wFile.close()
    DBConnection.conn = sqlite3.connect(db_file)
