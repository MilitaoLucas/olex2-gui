import SQLFactory
#import readCif
import string
import sys
import os
#import olex_core
#dsa = SQLFactories.SQLFactory()
ds = SQLFactory.SQLFactory()
#from Streams import Unbuffered
#sys.stdout = Unbuffered(sys.stdout)
try:
  import olx
  datadir = olx.DataDir()
  basedir = olx.BaseDir()
except:
  pass

from olexFunctions import OlexFunctions
OV = OlexFunctions()

def _mkdir(newdir):
  """works the way a good mkdir should :)
    - already exists, silently complete
    - regular file in the way, raise an exception
    - parent directory(ies) does not exist, make them as well
  """
  if os.path.isdir(newdir):
    pass
  elif os.path.isfile(newdir):
    raise OSError("a file with the same name as the desired " \
            "dir, '%s', already exists." % newdir)
  else:
    head, tail = os.path.split(newdir)
    if head and not os.path.isdir(head):
      _mkdir(head)
    #print "_mkdir %s" % repr(newdir)
    if tail:
      os.mkdir(newdir)


class MainController(object):

  def __init__(self):
    self._dict = {}
    self.cif = {}
    self.people = {}

  def __getitem__(self, key):
    pass


  def updateData(self, dataUpdate, data, sNum):
    fieldANDvalue = {}
    for field in dataUpdate:
      type = dataUpdate[field][0]
      table = dataUpdate[field][1]
      value = data[sNum][field]
      fieldANDvalue.setdefault(table, "")
      fieldANDvalue[table] = fieldANDvalue[table] + "%s = '%s'," %(field, value)
    for table in fieldANDvalue:
      s = fieldANDvalue[table][:-1]
      if len(s) > 0: ds.txtUPDATE(table="dimas_%s" %table, fieldANDvalue=s, equals = sNum)

  def getWarningCtrl(self):
    warningCtrl = []
    sql = "SELECT * FROM gui_warnings"
    res = ds.run_select_sql(sql)
    for entry in res:
      warningCtrl.append(entry)
    return warningCtrl
  def getsNumDictionary(self, sqlFilter, sNum):
    filtersNum = {}
    sNumDictionary = {}
    sNumDictionaryDelete = []
    submissionDetailsYsNo = False

    for domain in sqlFilter:
      sqlFilterValue = (sqlFilter[domain])[:-5]       #the [:-5] gets rid of the trailing ' AND ' This should be changed!
      sqlFilterValue = string.replace(sqlFilterValue,"*","%")
      sqlFilterValue = string.replace(sqlFilterValue,"?","%")
      if sqlFilterValue != "":
        if domain == "submission":
          fieldList = ["ID", "SubmitterID", "OperatorID", "DateSubmission"]
          submissionDetailsYsNo = False
        elif domain == "progress":
          fieldList = ["ID", "statusID"]
          #submissionDetailsYsNo = False
        else:
          fieldList = ["ID"]
        fields = ""
        for item in fieldList:
          fields = fields + item + ","
        fields = fields[:-1]
        sql = "SELECT %s FROM %s WHERE %s" %(fields, domain, sqlFilterValue)
        d = ds.run_select_sql(sql)
        if not d:
          sNumDictionary.setdefault(sNum, {})
          sNumDictionary[sNum].setdefault(domain, {})
          continue

        #if len(sNumDictionary) ==0:
        for sNum in d:
          sNumDictionary.setdefault(sNum[0], {})
          sNumDictionary[sNum[0]].setdefault(domain, {})

          for field,value in zip(fieldList,sNum):
            sNumDictionary[sNum[0]][domain].setdefault(field, value)
            #sNumDictionary[sNum[0]][domain][field] = value

    return sNumDictionary


  def getPerson(self, ID):
    strField = ""
    person = {}
    fields = ["id", "surname", "givenname", "account", "nickname", "institutionid", "phone", "room", "email"]
    for field in fields:
      strField = strField + field + ","
    strField = strField[:-1]
    sql = "SELECT %s FROM people WHERE ID = %s" %(strField, ID)
    p = ds.run_select_sql(sql)
    for item in p:
      #sNumDictionary[sNum[0]] = {}
      for field,value in zip(fields,item):
        person.setdefault(field, value)
    return person

  def getCrystal(self, ID):
    strField = ""
    person = {}
    fields = ["id", "surname", "givenname", "account", "nickname", "institutionid", "phone", "room", "email"]
    for field in fields:
      strField = strField + field + ","
    strField = strField[:-1]
    sql = "SELECT %s FROM people WHERE ID = %s" %(strField, ID)
    p = ds.run_select_sql(sql)
    for item in p:
      #sNumDictionary[sNum[0]] = {}
      for field,value in zip(fields,item):
        person.setdefault(field, value)
    return person



  def getPeople(self):
    people = self.people
    strField = ""
    fields = ["id", "surname", "givenname", "account", "nickname", "institutionid", "phone", "room", "email"]
    for field in fields:
      strField = strField + field + ","
    strField = strField[:-1]
    sql = "SELECT %s FROM people" %strField
    p = ds.run_select_sql(sql)
    i = 0
    for ppl in p:
      j = 0
      people[ppl[0]] = {}
      for item in ppl:
        people[ppl[0]][fields[j]] = item
        j +=1

    strField = ""
    fields = ["id", "idn", "frames", "raw", "refine", "archive"]
    for field in fields:
      strField = strField + field + ","
    strField = strField[:-1]
    sql = "SELECT %s FROM path" %strField
    p = ds.run_select_sql(sql)
    i = 0
    for ppl in p:
      j = 0
      people[ppl[0]]["path"] = {}
      for item in ppl:
        try:
          item = string.replace(item, '/', '\\')
        except:
          pass
        people[ppl[0]]["path"][fields[j]] = item
        j +=1
    self.people = people
    return people

  def selectPath(self, path="Frames", IDN = "HPD"):
    sql = "SELECT %s FROM path WHERE IDN = '%s'" %(path, IDN)
    path = ds.run_select_sql(sql)
    if len(path) > 0:
      path = path[0]
    else:
      path = "Double click here to set preferences."
    self.lblPath.SetLabel(path)
    return path

  def updatePath(self, wherepath, IDN, newpath):
    fieldANDvalue = ""
    field = wherepath
    value = newpath
    fieldANDvalue = fieldANDvalue + r"%s = '%s'," %(field, value)
    fieldANDvalue = fieldANDvalue[:-1]
    ds.txtUPDATE(table="path", fieldANDvalue=fieldANDvalue, where = "idn", equals = IDN)

  def getDataFromCif(self, path, filename):
    self.cif = self.getItemDictionary()
    #fred = cif.readCif(path, filename)
    pass

  def getItemDictionary(self):
    self.cif = {}
    strField = ""
    fields = ["cif_item", "dimas_item", "file", "file_item"]
    for field in fields:
      strField = strField + field + ","
    strField = strField[:-1]
    sql = "SELECT %s FROM cif" %strField
    c = ds.run_select_sql(sql)
    i = 0
    for cif in c:
      self.cif[cif[2]]={}
    for cif in c:
      self.cif[cif[2]][cif[0]]=[]
    for cif in c:
      self.cif[cif[2]][cif[0]].append([(cif[1]),(cif[3])])

    return self.cif


  def getAllControlsData(self, ctrls, sNum, sNumData):
    dq = {}
    fields = ""
    tables = ""
    sNumFilter = " = '%s'" %sNum
    fieldList = []
    #print sNumFilter

    sql = ""
    for c in ctrls:
      type = ctrls[c][0]
      table = ctrls[c][1]
      field = ctrls[c][2]
      extension = ctrls[c][3]
      if extension != "": extension = "_%s" %(extension)
      if type == "txt":
        dq.setdefault(table, {})
        dq[table].setdefault("field", [])
        dq[table]["field"].append(field)
        fieldList.append(field)
      elif type == "cmb":
        dq.setdefault(table, {})
        field = "%s%s" %(field,extension)
        field = field
        dq[table].setdefault("field", [])
        dq[table]["field"].append(field)
        fieldList.append(field)
      elif type == "cxt":
        dq.setdefault(table, {})
        field = "%s%s" %(field,extension)
        dq[table].setdefault("field", [])
        dq[table]["field"].append(field)
        fieldList.append(field)


    for table in dq:
      condition = "WHERE sNum = '%s'" %(sNum)
      sql = ""
      for item in dq[table]["field"]:
        sql = "%s%s, " %(sql,item)
      fields = sql[:-2]
      tableS = "dimas_%s" %(table)
      sql = "SELECT %s FROM %s %s" %(fields, tableS, condition)
      res = ds.txtMulti(sql)

      for s in res:
        sNumData.setdefault(sNum, {})
        for field, value in zip(dq[table]["field"], res[0]):
          sNumData[sNum][field] = value

    return sNumData
    #print

  def cmbChoices(self, ctrls):
    data = {}
    people = self.people
    for c in ctrls:
      type = ctrls[c][0]
      table = ctrls[c][1]
      field = ctrls[c][2]
      extension = ctrls[c][3]
      if extension != "": extension = "_%s" %extension
      if type == "cmb":
        l=ds.choiceSQL(base = field)
        field = field + extension
      elif type == "cxt":
        if field == "Submitter" or field == "Operator":
          l = []
          for ppl in people:
            name = str(people[ppl]["givenname"]) + " " + str(people[ppl]["surname"])
            l.append((name, ppl))
          field = field + extension

      else:
        continue
      for choice in l:
        data.setdefault(field,{})
        data[field].setdefault("DIS", {})
        data[field].setdefault(extension[1:], {})
        data[field]["DIS"][choice[0]] = choice[1]
        data[field][extension[1:]][choice[1]]  = choice[0]


    return data

  def wildcard(self, e):
    e = str(e)
    e = string.replace(e,'*','%')
    e = string.replace(e,'?','%')
    return e



class dimas_info(object):

  def __init__(self, function, param=None):
    self.basedir = olx.BaseDir()
    self.filefull = olx.FileFull()
    self.filepath = olx.FilePath()
    self.filename = olx.FileName()
    self.function = function
    try:
      self.param = param.split(";")[0]
    except:
      self.param = param
    self.debug = False
    if self.debug: print self.basedir
    self.dimas_d = {}
  
  def format_html_reference(self):
    
    if not self.dimas_d.get('publ_authors','None') or self.dimas_d.get('publ_authors','None') == "None":
      sql = """SELECT submission.ID, submission.DateSubmission, submission.ChemicalName, submission.FormulaSubmitted, submission.Code, submission.MeasurementTemperature, submission.ListType, submission.ListReasons, submission.Comment, submitter_fullnames.display, account_fullnames.display, operator_fullnames.display, progress_status.display
FROM progress_status INNER JOIN ((people_fullnames AS operator_fullnames RIGHT JOIN (people_fullnames AS account_fullnames RIGHT JOIN (people_fullnames AS submitter_fullnames RIGHT JOIN submission ON submitter_fullnames.ID = submission.SubmitterID) ON account_fullnames.ID = submission.AccountID) ON operator_fullnames.ID = submission.OperatorID) INNER JOIN progress ON submission.ID = progress.ID) ON progress_status.ID = progress.StatusID
WHERE (((submission.ID)="%s"));
""" %self.filename
      try:
        rs = ds.run_select_sql(sql, how=1)
      except:
        return ""
      html = '''
%(account_fullnames.display)s, %(operator_fullnames.display)s, %(display)s; Private Communication.
''' %rs[0]

    else:
    
      html = '''
%(publ_authors)s; %(journal_name_full)s; %(journal_year)s
''' %self.dimas_d
    
    return html

  def run(self):
    if self.filename == "none":
      return
    fun = self.function
    if fun == "info":
      self.dimas_d = self.sql_get_info()
      self.display_dimas()
      self.make_olex_variables()
      return self.dimas_d
    
    if fun == "reference":
      self.dimas_d = self.sql_get_reference()
      html = self.format_html_reference()
      OV.SetVar('snum_html_reference', html)
    
    elif fun == "resetVar":
      self.reset_olex_variables()

    elif fun == "sql_dimas":
      self.sql_get_info()
      return self.dimas_d

    elif fun == "load":
      id = self.param
      OV.Cursor("busy", "'Loading Structure %s. Please Wait'" %id)
      self.load_dimas(id)
      #OV.Cursor()

    elif fun == "archive":
      self.archive('*')

    else:
      print "Please enter an argument for the DIMAS tool: 'info', 'load' or 'archive'"

  def test_tables(self):
    sNum = self.filename
    txt = ""
    sql = "SELECT SubmitterID, AccountID, OperatorID FROM submission WHERE ID = '%s'" %(sNum)
    rs = ds.run_select_sql(sql)
    for entry in rs:
      print entry

    tables = ["submission", "crystal", "progress"]
    for table in tables:
      sql = "SELECT * FROM %s WHERE ID = '%s'" %(table, sNum)
      rs = ds.run_select_sql(sql)
      if not rs:
        txt += "! %s has no entry in table \t %s" %(sNum, table)
        txt += "\n"
      else:
        txt += "+ %s has an entry in table \t %s" %(sNum, table)
        txt += "\n"
    return txt


  def format_date(self, Date):
    try:
      retval = "%s-%s-%s" %(Date.day, Date.month, Date.year)
    except AttributeError:
      retval = "No Date"
    try:
      d = (Date.split()[0]).split("-")
      retval = "%s-%s-%s" %(d[2], d[1], d[0])
    except:
      "No Date second go"
    return retval


  def spacers (self, args, fixed, maxlen):
    n = 0
    for item in args:
      n += len(item)
    n = float(maxlen - (n + fixed))
    n = n/2

    try:
      if str(n)[-1:] == '0':
        spacer1 = " " * int(n)
        spacer2 = spacer1
      else:
        n = int(n)
        spacer1 = " " * n
        spacer2 = " " * (n + 1)

    except TypeError:
      n = int(n)
      spacer1 = " " * n
      spacer2 = " " * (n + 1)
    return spacer1, spacer2


  def load_dimas(self, id):
    import os, zlib

    dimasdir = datadir + r"\dimas\%s" %id
    if self.debug: print dimasdir
    resfile = dimasdir + r"\%s.ins" %id
    inspath = dimasdir + r"\%s.ins" %id

    if self.debug: print resfile
    hklfile = dimasdir + r"\%s.hkl" %id
    if self.debug: print hklfile

    sql = """
SELECT submission.ID, refinement_data.res, diffraction_data.hkl
FROM (submission INNER JOIN diffraction_data ON submission.ID = diffraction_data.ID) INNER JOIN refinement_data ON submission.ID = refinement_data.ID
WHERE (((submission.ID)='%s'));""" %(id)

    rs = ds.run_select_sql(sql, how=0)
    if not rs:
      print "\n*** There is no hkl file deposited for structure %s\n" %id
      return

    if not os.path.isdir(dimasdir):
      _mkdir(dimasdir)

    for item in rs:
      res = zlib.decompress(item[1])
      resfile = open(resfile, 'wb')
      resfile.write(res)
      resfile.close()

      hkl = zlib.decompress(item[2])
      hklfile = open(hklfile, 'w')
      hklfile.write(hkl)
      hklfile.close()
      print inspath
      if olx:
        import PilTools
        olx.Clear()
        olx.Atreap(r"%s" %inspath)
#        width = olx.HtmlPanelWidth()
#        width = 290
#        tool_arg = '100;100;160;None;None;None'
#        makeImage = PilTools.sNumTitle(width, tool_arg)
#        makeImage.run()
      else:
        print "*cmd=clear"
        print "*cmd=reap '%s'" %inspath

  def sql_get_reference(self):
    sNum = self.filename
    d = {}
    rs = {}
    view_table = "reference"
    fields = ("ID", "CCDCNo", "REFCODE", "publ_authors", "journal_year", "journal_volume", "journal_name_full")
    sql = "SELECT * FROM %s WHERE ID = '%s'" %(view_table, sNum)
    
    try:
      rs = ds.run_select_sql(sql, how=1)
      
    except:
      return '2003'
    
    if rs:
      return rs[0]
    else:
      raise "rs[0] is not there"

  def sql_get_info(self):
    sNum = self.filename
    d = {}
    rs = {}
    view_table = "submission"
    fields = ("ID", "submitter", "Phone", "Lab", "account", "operator", "DateSubmitted", "DateCollected", "DateCompleted", "status", "crystallisation", "preparation")
    sql = "SELECT * FROM %s WHERE ID = '%s'" %(view_table, sNum)
    
    sql = """SELECT submission.ID, submission.DateSubmission, submission.ChemicalName, submission.FormulaSubmitted, submission.Code, submission.MeasurementTemperature, submission.ListType, submission.ListReasons, submission.Comment, submitter_fullnames.display, account_fullnames.display, operator_fullnames.display, progress_status.display
FROM progress_status INNER JOIN ((people_fullnames AS operator_fullnames RIGHT JOIN (people_fullnames AS account_fullnames RIGHT JOIN (people_fullnames AS submitter_fullnames RIGHT JOIN submission ON submitter_fullnames.ID = submission.SubmitterID) ON account_fullnames.ID = submission.AccountID) ON operator_fullnames.ID = submission.OperatorID) INNER JOIN progress ON submission.ID = progress.ID) ON progress_status.ID = progress.StatusID
WHERE (((submission.ID)="%s"));
    """ %sNum
    try:
      rs = ds.run_select_sql(sql, how=1)
    except:
      return '2003'
    if not rs:
      rs.setdefault("submitter", 'n/a')
      rs.setdefault("operator", 'n/a')
    return rs[0]  
#    for item in rs:
#      for name, info in zip(fields, item):
#          d.setdefault(name, info)
#    self.dimas_d = d
#    if not d:
#      d.setdefault("submitter", 'n/a')
#      d.setdefault("operator", 'n/a')
#    else:
#      if not d["submitter"]:
#        d.setdefault("submitter", 'n/a')
#      if not d["operator"]:
#        d.setdefault("operator", 'n/a')
#    return d

  def make_olex_variables(self):
    if self.dimas_d:
      d = self.dimas_d
      OV.SetVar("operator",d.get("operator", 'Unknown'))
      OV.SetVar("submitter",d.get("submitter", 'Unknown'))
      OV.SetVar("account",d.get("account", 'Unknown'))
      OV.SetVar("DateCollected",d.get("DateCollected", 'Unknown'))
      OV.SetVar("DateSubmitted",d.get("DateSubmitted", 'Unknown'))
      OV.SetVar("preparation",d.get("preparation", 'Unknown'))
    else:
      print "No dimas_d dictionary"

  def reset_olex_variables(self):
    d = self.dimas_d
    OV.SetVar("operator"," ")
    OV.SetVar("submitter"," ")
    OV.SetVar("account"," ")
    OV.SetVar("DateCollected"," ")
    OV.SetVar("DateSubmitted"," ")
    OV.SetVar("preparation","Prep details would be here if there were any on DIMAS")
    
    
  def display_dimas(self):
    d = self.dimas_d
    try:
      ID = d["ID"]
    except:
      return
    txt = []
    if not d:
      print "This structure is not in the DIMAS database"
      txt = self.test_tables()
      print txt
      return
    ID = d.get("ID", r"n/a")
    operator = d.get("operator_fullnames.display", r"n/a")
    submitter = d.get("display", r"n/a")
    account = d.get("account_fullnames.display",r"n/a")
    if not account:
      account = "Outside Job"
    status = d.get("progress_status.display",r"n/a")
    DateSubmitted = self.format_date(d.get("DateSubmission", None))
    DateCollected = self.format_date(d.get("DateCollected", None))
    DateCompleted = self.format_date(d.get("DateCompleted", None))
    
    maxlen = 80
    txt.append("+++++++++++++++++  DURHAM UNIVERSITY CRYSTALLORAPHY LABORATORY  ++++++++++++++++")
    txt.append("+                                                                              +")

    spacer1, spacer2 = self.spacers([ID, operator], 41, maxlen)
    txt.append("+ %sSTRUCTURE %s was solved and refined by %s%s +" %(spacer1, ID, operator, spacer2))

    spacer1, spacer2 = self.spacers([DateSubmitted, submitter], 21, maxlen)
    txt.append("+ %sSubmitted on %s by %s%s +" %(spacer1, DateSubmitted, submitter, spacer2))

    spacer1, spacer2 = self.spacers([account, status], 20, maxlen)
    txt.append("+ %sGroup: %s Status: %s%s +" %(spacer1, account, status, spacer2))

    txt.append("+                                                                              +")
    txt.append("+" * maxlen)

    for line in txt:
      print line
    print
    self.txt = txt



  def archive(self, files):
    import glob
    import os
    import FileSystem as FS
    txt = []
    maxlen = 80
    txt.append("+++++++++++++++++  DURHAM UNIVERSITY CRYSTALLORAPHY LABORATORY  ++++++++++++++++")
    txt.append("+                                                                              +")

    filepath = self.filepath
    filename = self.filename
    basedir = self.basedir

    diffraction = ['.hkl', 'smart.ini', 'matrix0.p4p', '*m.raw']
    reduction = ['*.abs', 'saint.ini', '*m._ls']
    refinement = ['.res', '.ins', '.lst', '.cif']
    finishing = ['*.jpg', '*.jpeg', '*.ps', '*.eps','*.rtf', '*.doc', '*.pdf', '*.png' ]

    if files == '*':
      #files = ['.res', '.ins', '.lst', '.cif',
               #'*.abs', '*.ini', '*m._ls', '*m.raw',
               #'*.jpg', '*.jpeg', '*.ps', '*.eps',
               #'*.rtf', '*.doc', '*.pdf' ]
      files = [diffraction, reduction, refinement, finishing]
    elif  files == '*.*':
      arguments = '*'
    sNum = filename
    def_file = basedir + r"\etc\site\archive.def"

    if sNum[:1] == "9":
      prefix = "19"
    elif sNum[:1] == "0":
      prefix = "20"
    else:
      print "This structure does not conform to naming conventions and can not be archived at present"
      return

    year = prefix + sNum[:2]

    rfile = open(def_file, 'r')
    for item in rfile:
      item = string.split(item, "=")
      if item[0] == "UNCPATH":
        directory = item[1]
      elif item[0] == "FOLDERS":
        folder_structure = item[1]
    if folder_structure == "Year":
      directory = directory + year

    info = ""
    for fullpath in glob.glob(os.path.join(directory)):
      info = os.stat(fullpath)
    if not info:
      yn = raw_input("Folder %s does not exist. Do you want to create it? [n]\n"%(directory))
      if yn == "yes" or yn == "y":
        os.mkdir(directory)
      else:
        return

    info = ""
    directory = directory + "\\" + sNum
    for fullpath in glob.glob(os.path.join(directory)):
      info = os.stat(fullpath)
    yn = ''
    if info:
      print directory
      print "This structure is already archived"
      #yn = raw_input("Do you want to add to this folder? [n]\n")
      yn = 'y'
    else:
      os.mkdir(directory)
      yn = 'y'

    if yn == 'y' or yn == 'yes':
      filelist = []
      for group in files:
        for item in group:
          if item[0] == ".":
            filelist.append("%s%s" %(sNum, item))
          elif item[0] == "*":
            for fullpath in glob.glob(os.path.join(filepath + "\\" + item)):
              item = string.split(fullpath, "\\")[-1:][0]
              filelist.append(item)
          else:
            filelist.append("%s" %(item))

      for filename in filelist:
        #shutil.copyfile("%s\\%s" %(filepath, file), "%s\\%s" (directory, file))
        file = directory + "\\" + filename
        try:
          FS.Node("%s\\%s" %(filepath, filename)).copy_file((file),overwrite=False)
          print "--> %s " %file
          res = self.uploadFiles(file, sNum)
        except FS.ExistingNode:
          print "The file %s already exists!" %filename
        except:
          try:
            f = filepath.split("\\")
            level_up = ""
            for i in range (len(f) -1):
              level_up += "%s\\" %f[i]
              i += 1
            print level_up
            FS.Node("%s\\%s" %(level_up, filename)).copy_file((file),overwrite=False)
            print "--> %s " %file
            res = self.uploadFiles(file, sNum)
          except:
            print "The file %s appears to be missing" %filename

    else:
      print "Good Bye"

  def dimas_cif(self):
    basename = self.filename
    txt = get_dimas(basename)
    return txt


  def uploadFiles(self, file, sNum):
    import FileSystem as FS
    import zlib
    import MySQLdb
    
    res = ''
    table = ''
    type = ''
    ID = sNum
    
    if file[-3:] == "hkl":
      table = "diffraction_data"
      type = "hkl"
    elif file[-3:] == 'p4p':
      table = "diffraction_data"
      type = "p4p"
    elif file[-9:] == 'smart.ini':
      table = "diffraction_data"
      type = "smart"
    #elif file[-9:] == 'saint.ini':
      #table = "diffraction_data"
      #type = "saint"
    elif file[-3:] == 'res':
      table = "refinement_data"
      type = "res"
    elif file[-3:] == 'cif':
      table = "refinement_data"
      type = "cif"
    elif file[-3:] == 'doc':
      table = "refinement_data"
      type = "doc"
      
    if table:
      f_node = FS.Node(file)
      fileData = f_node.open().read()
      fileData = zlib.compress(fileData,9)
      fileData = MySQLdb.escape_string(fileData)
      #fileData = ds.escape_strings(fileData)
      sql = r'INSERT %s (ID,%s) VALUES("%s","%s") ON DUPLICATE KEY UPDATE %s="%s";' %(table, type, ID, fileData, type, fileData,)
      #sql = r'INSERT %s (ID,%s) VALUES("%s","%s");' %(table, type, ID, fileData)
      try:
        res = ds.run_sql(sql)
      except:
        log.write("%s There was an error with this table %s\n" %(ID, table))
        
      subject = table.split('_')[0]
      sql = r'INSERT %s (ID,data_%sID) VALUES("%s","%s") ON DUPLICATE KEY UPDATE data_%sID="%s";' %(subject, string.capwords(type), ID, ID, string.capwords(type), ID,)
      try:
        res2 = ds.run_sql(sql)
      except:
        log.write("%s There was an error with this table %s\n" %(ID, table))
        
    return res

#if __name__ == '__main__':
# txt = get_dimas(sys.argv[1])
  #for line in txt:
  # print line

  #print "END"
