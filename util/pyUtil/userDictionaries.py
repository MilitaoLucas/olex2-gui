# userDictionaries.py
import os
import pickle

import olex
import olx

from olexFunctions import OlexFunctions
import copy
OV = OlexFunctions()

people = None
persons = None
localList = None
affiliations = None
experimantal = None

def sql_update_str(table_name, d):
  sql = ["UPDATE %s SET" %table_name]
  fields = []
  for k,v in d.iteritems():
    if k != 'id':
      if v is None: v = ""
      elif isinstance(v, basestring):
        v = v.replace("'", "''")
      fields.append("%s='%s'" %(k, v))
  sql.append("%s where id='%s'" %(','.join(fields), d['id']))
  res = ' '.join(sql)
  return res

def sql_insert_str(table_name, d):
  sql = ["INSERT INTO %s" %table_name]
  fields, values = [], []
  for k,v in d.iteritems():
    if k != 'id':
      fields.append(k)
      if v is None: v = ""
      elif isinstance(v, basestring):
        v = v.replace("'", "''")
      values.append("'%s'" %v)
  sql.append("(%s)" %(','.join(fields)))
  sql.append("VALUES (%s)" %(','.join(values)))
  res = ' '.join(sql)
  return res

def get_sql(table_name, d):
  if not d.get('id', None):
    return sql_insert_str(table_name, d)
  return sql_update_str(table_name, d)

class person:
  def __init__(self, affiliationid, id=None, firstname="", middlename="",
               lastname="", email="", phone=""):
    if type(affiliationid) == tuple:
      sql_res = affiliationid
      self.id = sql_res[0]
      self.affiliationid = sql_res[1]
      self.firstname = sql_res[2]
      self.middlename = sql_res[3]
      self.lastname = sql_res[4]
      self.email = sql_res[5]
      self.phone = sql_res[6]
    else:
      self.affiliationid = affiliationid
      self.id = id
      self.firstname= firstname
      self.middlename = middlename
      self.lastname = lastname
      self.email = email
      self.phone = phone

  def update(self):
    cursor = DBConnection().conn.cursor()
    cursor.execute(get_sql('person', self.__dict__))
    DBConnection().conn.commit()
    self.lastrowid = cursor.lastrowid
    return self

  def get_display_name(self, format="acta", affiliation=False):
    if format == "acta":
      surname = self.lastname
      first_initial = self.firstname
      second_initial = self.middlename
      if first_initial:
        first_initial = first_initial[0] + '.'
      if second_initial and first_initial:
        second_initial = second_initial[0] + '.'
      display = "%s, %s%s" %(surname, first_initial, second_initial)
    else:
      display = "%s %s %s" %(self.firstname, self.middlename, self.lastname)
      while "  " in display:
        display = display.replace("  ", " ")
    if affiliation:
      st = self.get_affiliation()
      if st.name:
        if st.department:
          display = "%s / %s-%s" %(display, st.name, st.department)
        else:
          display = "%s / %s" %(display, st.name)
      else:
        display = "%s / unknown" %display
    return display

  def as_dict(self):
    d = copy.deepcopy(self.__dict__)
    d['displayname'] = self.get_display_name(d)
    return d

  def get_affiliation(self):
    if self.affiliationid is None:
      return site()
    cursor = DBConnection().conn.cursor()
    sql = "SELECT * FROM affiliation WHERE id=%s" %self.affiliationid
    cursor.execute(sql)
    return site(cursor.fetchone())

class site:
  def __init__(self, id=None, name="", department="", address="", city="",
                postcode="", country=""):
    if id and type(id) == tuple:
      sql_res = id
      self.id = sql_res[0]
      self.name = sql_res[1]
      self.department = sql_res[2]
      self.address = sql_res[3]
      self.city = sql_res[4]
      self.postcode = sql_res[5]
      self.country = sql_res[6]
    else:
      self.id = id
      self.name = name
      self.department = department
      self.address = address
      self.city = city
      self.postcode = postcode
      self.country = country

  def get_address(self):
    return '\n'.join(filter(
      None, (self.address, self.city, self.postcode, self.country)))

  def update(self):
    cursor = DBConnection().conn.cursor()
    cursor.execute(get_sql('affiliation', self.__dict__))
    DBConnection().conn.commit()
    self.lastrowid = cursor.lastrowid
    return self

  def as_dict(self):
    d = copy.deepcopy(self.__dict__)
    return d

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

  def getListAffiliations(self):
    cursor = DBConnection().conn.cursor()
    sql = "SELECT * FROM affiliation"
    cursor.execute(sql)
    all_affiliations = cursor.fetchall()
    retVal = ""
    for affiliation in all_affiliations:
      if affiliation[2]:
        retVal += "%s [%s]<-%s;" %(affiliation[1], affiliation[2], affiliation[0])
      else:
        retVal += "%s<-%s;" %(affiliation[1], affiliation[0])
    return retVal

  def get_site(self, id):
    if id is None:
      return site()
    else:
      cursor = DBConnection().conn.cursor()
      sql = "SELECT * FROM affiliation WHERE id=%s" %id
      cursor.execute(sql)
      return site(cursor.fetchone())

  def deleteSiteById(self, id):
    sql = "DELETE FROM affiliation WHERE id=%s" %id
    DBConnection().conn.cursor().execute(sql)
    DBConnection().conn.commit()


class Persons:
  def __init__(self):
    global persons
    persons = self
    OV.registerFunction(self.getListPeople)
    OV.registerFunction(self.getPersonInfo)

  def deletePersonById(self, id):
    sql = "DELETE FROM person WHERE id=%s" %id
    DBConnection().conn.cursor().execute(sql)
    DBConnection().conn.commit()

  def getListPeople(self, site_id = None, edit=True):
    cursor = DBConnection().conn.cursor()
    if not site_id or site_id == "None":
      sql = "SELECT * FROM person"
      show_affiliation = False
    else:
      show_affiliation = False
      sql = "SELECT * FROM person where affiliationid=%s" %site_id
    cursor.execute(sql)
    all_persons = cursor.fetchall()
    retVal_l = []
    for p in all_persons:
      v = "%s<-%s" %(person(p).get_display_name(affiliation=show_affiliation), p[0])
      retVal_l.append(v)
    retVal_l.sort()
    if edit and edit != "False":
      retVal_l.append("Edit...<--1")
    retVal = ";".join(retVal_l)
    return retVal

  def getPersonInfo(self,id,item):
    retStr = '?'
    if not id:
      return retStr
    person = self.get_person(id)
    if item in ('phone','email','address'):
      if item == "address":
        retStr = person.get_affiliation().get_address()
      else:
        retStr = person.__dict__[item]
    elif item == "displayname":
      retStr = person.get_display_name()
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
      sql = 'SELECT * FROM person WHERE lastname = "%s" AND firstname LIKE "%s%%"' %(parts[i], parts[j])
    cursor = DBConnection().conn.cursor()
    cursor.execute(sql)
    persons = cursor.fetchall()
    if not persons or len(persons) > 1:
      return None
    return persons[0][0]

  def get_person(self, id):
    if id is None:
      return person(1)
    else:
      cursor = DBConnection().conn.cursor()
      sql = "SELECT * FROM person WHERE id = %s" %(id)
      cursor.execute(sql)
      return person(cursor.fetchone())


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
      s = site()
      s.name = a[0]
      s.department = a[1]
      s.address = (' '.join(filter(None, a[2:4]))).strip()
      s.city = a[4]
      s.postcode = a[5]
      s.update()
      self.conn.commit()
      adict[s.name] = s.lastrowid
    cursor.execute("SELECT * FROM persons")
    persons = cursor.fetchall()
    for d in persons:
      aff = adict.get(d[5].strip(), None)
      if aff is None: continue
      p = person(aff)
      p.firstname = d[0]
      p.middlename = d[1]
      p.lastname = d[2]
      p.email= d[3]
      p.phone = d[4]
      p.update()
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
    for k,v in dictionary.iteritems():
      a_all = v['address']
      if '\n' in a_all:
        a_all = a_all.split('\n')
      elif ',' in a_all:
        a_all = a_all.split(',')
      else:
        a_all = a_all.split()
      aname = a_all[0]
      sql = "SELECT * FROM affiliation WHERE name like '%s'" %aname
      cr = DBConnection._conn.cursor()
      cr.execute(sql)
      existing_aff = cr.fetchone()
      if existing_aff:
        last_aff_id = existing_aff[0]
      else:
        s = site(name=aname, address=' '.join(a_all[1:])).update()
        last_aff_id = s.lastrowid
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
      p = person(last_aff_id, None, firstname, middlename,
                  secondname, v['email'], v['phone'])
      p.update()

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
    DBConnection._conn.cursor().execute("pragma foreign_keys=ON")
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
