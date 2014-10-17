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

class LocalList:
  def __init__(self):
    self.dictionary = {}
    self.dictionary.setdefault('journals',
      getLocalDictionary('journals')['journals'])
    self.dictionary.setdefault('diffractometers',
      getLocalDictionary('diffractometers')['diffractometers'])
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
      self.dictionary['diffractometers'].setdefault(diffractometer, {'cif_def':'?'})
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

  def getListAffiliations(self):
    cursor = DBConnection().conn.cursor()
    sql = "SELECT * FROM affiliation"
    cursor.execute(sql)
    all_affiliations = cursor.fetchall()
    retVal = ""
    for affiliation in all_affiliations:
      retVal += "%s<-%s;" %(affiliation[1], affiliation[0])
    retVal += "++ ADD NEW ++<--1"
    return retVal

  def get_affiliation_address(self, id, list=False):
    cursor = DBConnection().conn.cursor()
    sql = "SELECT * FROM affiliation WHERE id=%s" %id
    cursor.execute(sql)
    address = cursor.fetchone()
    if not address:
      address = "?"
    if not list:
      address = ("\n").join(filter(None, address[1:]))
    else:
      return address
    return address

  def add_affiliation(self, id, name, department, address, city,
                       postcode, country):
    cursor = DBConnection().conn.cursor()
    if id < 0: id = None
    affiliation = (id, name, department, address, city, postcode, country)
    cursor.execute(
      "INSERT OR REPLACE INTO affiliation VALUES (?,?,?,?,?,?,?)",
      affiliation)
    DBConnection().conn.commit()
    return cursor.lastrowid


class Persons:
  def __init__(self):
    global persons
    persons = self
    OV.registerFunction(self.getListPeople)
    OV.registerFunction(self.add_person)
    OV.registerFunction(self.getPersonInfo)

  def changePersonInfo(self,person,item,info):
    pass

  def addNewPerson(self, aid, id=None, name=""):
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
    person = (id, aid, firstname, middlename, secondname, '', '', '')
    DBConnection().conn.cursor().execute(
      "INSERT OR REPLACE INTO person VALUES (id,affiliationid,firstname,middlename,lastname,email,phone)", person)
    DBConnection().conn.commit()
    d = {'firstname':person[2],
         'middlename':person[3],
         'lastname':person[4],
         'email':person[5],
         'phone':person[6],
         'aid':aid
         }
    d['displayname'] = self.make_display_name(d)
    return d

  def deletePersonById(self, id):
    sql = "DELETE FROM person WHERE id=%s" %id
    DBConnection().conn.cursor().execute(sql)
    DBConnection().conn.commit()

  def make_display_name(self, person,format="acta"):
    if format == "acta":
      if type(person) == tuple:
        surname = person[4]
        first_initial = person[2]
        second_initial = person[3]
      else:
        surname = person['lastname']
        first_initial = person['firstname']
        second_initial = person['middlename']
      if first_initial:
        first_initial = first_initial[0] + '.'
      if second_initial and first_initial:
        second_initial = second_initial[0] + '.'
      display = "%s, %s%s" %(surname, first_initial, second_initial)
    else:
      display = "%s %s %s" %(person[2], person[3], person[4])
    return display

  def getListPeople(self):
    cursor = DBConnection().conn.cursor()
    sql = "SELECT * FROM person"
    cursor.execute(sql)
    all_persons = cursor.fetchall()
    retVal_l = []
    for person in all_persons:
      v = "%s<-%s" %(self.make_display_name(person), person[0])
      retVal_l.append(v)
    retVal_l.sort()
    retVal_l.append("++ ADD NEW ++<--1")
    retVal = ";".join(retVal_l)
    return retVal

  def getPersonInfo(self,id,item):
    retStr = '?'
    if not id:
      return retStr
    currentPersonInfo = self.get_person_details(id)
    if not currentPersonInfo:
      return retStr
    if item in ('phone','email','address'):
      if item == "address":
        retStr = self.get_person_affiliation(id)
      else:
        retStr = currentPersonInfo[item]
    return retStr

  def findPersonId(self, name, email=None):
    if email:
      sql = "SELECT * FROM person WHERE email = '%s'" %(parts[i], parts[j])
    else:
      if ',' in name:
        parts = [x.strip(' ')for x in name.split(',')]
      elif ' ' in name:
        parts = name.split(' ')
      else:
        return None
      i,j = 0,1
      if '.' in parts[0]:
        parts[0] = parts[0].split('.')[0]
        i,j = j,i
      elif '.' in parts[1]:
        parts[1] = parts[1].split('.')[0]
        pass
      sql = "SELECT * FROM person WHERE lastname = '%s' AND firstname LIKE '%s%%'" %(parts[i], parts[j])
    cursor = DBConnection().conn.cursor()
    cursor.execute(sql)
    persons = cursor.fetchall()
    if not persons or len(persons) > 1:
      return None
    return persons[0][0]

  def get_person_details(self, id):
    if id < 0:
      person = 7*[""]
    else:
      cursor = DBConnection().conn.cursor()
      sql = "SELECT * FROM person WHERE id = %s" %(id)
      cursor.execute(sql)
      person = cursor.fetchone()
      if not person:
        return
    d = {'firstname':person[2],
         'middlename':person[3],
         'lastname':person[4],
         'email':person[5],
         'phone':person[6],
         'aid':person[1]
         }
    d['displayname'] = self.make_display_name(d)
    return d

  def get_person_affiliation(self, id, list=False):
    cursor = DBConnection().conn.cursor()
    sql = "SELECT affiliationid FROM person WHERE id=%s" %id
    cursor.execute(sql)
    aid = cursor.fetchone()
    if not aid:
      return '?'
    sql = "SELECT * FROM affiliation WHERE id=%s" %aid[0]
    cursor.execute(sql)
    address = cursor.fetchone()
    if not list:
      address = ('\n').join(address[3:]).replace('\n\n', '\n')
    else:
      return address
    return address

  def add_person(self, id, aid, firstname, middlename, lastname, email, phone):
    cursor = DBConnection().conn.cursor()
    if id < 0: id = None
    person = (id, aid, firstname, middlename, lastname, email, phone)
    cursor.execute("INSERT OR REPLACE INTO person VALUES (?,?,?,?,?,?,?)",
                   person)
    DBConnection().conn.commit()
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
  if dictionary.has_key('journals'):
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
  dbc = DBConnection()
  people = Persons()
  affiliations = Affiliations()
  if dbc.need_import:
    try:
      dbc.doImport()
    except:
      import sys
      sys.stdout.formatExceptionInfo()
      print('Failed to import legacy data...')

class DBConnection():
  _conn = None

  @property
  def conn(self):
    return DBConnection._conn

  @conn.setter
  def conn(c):
    DBConnection._conn = c

  def doImport(self):
    cursor = self.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='persons'")
    if not cursor.fetchall():
      self.ImportPickles()
    else:
      self.ImportDB()

  def ImportDB(self):
    cursor = self.conn.cursor()
    cursor.execute("SELECT * FROM affiliations")
    affiliations = cursor.fetchall()
    adict = {}
    for a in affiliations:
      cursor.execute("insert into affiliation values (?,?,?,?,?,?,?)",
                     (None, a[0], a[1], (' '.join(filter(None, a[2:4]))).strip(), a[4], a[5], a[7]))
      adict[a[8].strip()] = cursor.lastrowid
      self.conn.commit()
    cursor.execute("SELECT * FROM persons")
    persons = cursor.fetchall()
    for p in persons:
      aff = adict.get(p[5].strip(), None)
      if aff is None: continue
      cursor.execute("insert into person VALUES (?,?,?,?,?,?,?)",
                      (None, aff) + p[0:5])
      self.conn.commit()
    cursor.execute("drop table persons")
    cursor.execute("drop table affiliations")

  def ImportPickles(self):
    name = "people"
    picklePath = getPicklePath(name)
    if not os.path.exists(picklePath):
      return
    pfile = open(picklePath)
    dictionary = pickle.load(pfile)
    pfile.close()
    dictionary = dictionary[name]
    cr = DBConnection._conn.cursor()
    for k,v in dictionary.iteritems():
      a_all = v['address']
      if '\n' in a_all:
        a_all = a_all.split('\n')
      elif ',' in a_all:
        a_all = a_all.split(',')
      else:
        a_all = a_all.split()
      aname = a_all[0]
      affiliation = (aname, '', ' '.join(a_all[1:]), '', '', '')
      sql = "SELECT * FROM affiliation WHERE name like '%s'" %aname
      cr.execute(sql)
      existing_aff = cr.fetchone()
      if existing_aff:
        last_aff_id = existing_aff[0]
      else:
        cr.execute("INSERT OR REPLACE INTO affiliation VALUES (NULL,?,?,?,?,?,?)",
          affiliation)
        last_aff_id = cr.lastrowid
      DBConnection._conn.commit()
      firstname = middlename = secondname = ""
      if ',' in k:
        name = k.split(',')
        secondname = name[0]
        name = name[1].split()
        firstname = name[0]
        if len(name) > 1:
          middlename = ''.join(name[1:])
      else:
        name = k.split()
        if len(name) == 1:
          secondname = name[0]
        elif len(name) == 2:
          firstname = name[0]
          secondname = name[1]
        elif len(name) == 3:
          firstname = name[0]
          middlename = name[1]
          secondname = name[2]
        if not secondname or secondname.endswith('.'):
          firstname, secondname = secondname, firstname
      person = [last_aff_id, firstname, middlename, secondname, v['email'],
                v['phone']]
      cr.execute(
        "INSERT OR REPLACE INTO person VALUES (NULL,?,?,?,?,?,?)", person)
      DBConnection._conn.commit()

  def __init__(self):
    self.need_import = False
    if DBConnection._conn:
      return
    import sqlite3
    db_path = olex.f(OV.GetParam('user.report.db_location'))
    db_name = OV.GetParam('user.report.db_name')
    db_file = "%s/%s" %(db_path, db_name)
    if not os.path.exists(db_path):
      os.makedirs(db_path)
    exists = os.path.exists(db_file)
    DBConnection._conn = sqlite3.connect(db_file)
    if exists:
      cursor = DBConnection._conn.cursor()
      cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='person'")
      if not cursor.fetchall():
        exists = False
      else:
        pass #import OLD

    if not exists:
      cursor = DBConnection._conn.cursor()
      cursor.executescript("""
CREATE TABLE affiliation (
  id INTEGER NOT NULL, name TEXT, department TEXT, address TEXT, city TEXT,
  postcode TEXT, country TEXT, PRIMARY KEY(id));
CREATE TABLE person (
  id INTEGER NOT NULL, affiliationid INTEGER NOT NULL,
  firstname TEXT, middlename TEXT, lastname TEXT,
  email TEXT, phone TEXT,
  PRIMARY KEY(id),
  FOREIGN KEY(affiliationid)
    REFERENCES affiliation(id)
      ON DELETE CASCADE
      ON UPDATE NO ACTION);
CREATE INDEX affiliationfk ON person (affiliationid);
      """)
      DBConnection._conn.commit()
      self.need_import = True
