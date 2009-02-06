#import MySQLdb
import sys
import zlib
import re
import time
from openbabel import *
try:
  import FileSystem as FS
except:
  pass
import string
import SQLFactory

class UpdateException:
  def __init__(self, sql_exception): self.sql_exception = sql_exception
  def __str__(self): return "Failure: (SQL exception '%s')" % ((self.sql_exception))


class UpdateDimasDB(object):

  def __init__(self):
    self.ds = SQLFactory.SQLFactory(db='DimasDB')

#      self.conn = MySQLdb.connect(host, user, passwd, db)

#  def __init__(self, host='129.234.12.100', user='DIMAS', passwd='fddd-anode', db='OlexGui'):
#     self.conn = MySQLdb.connect(host, user, passwd, db)

#  def __init__(self, host='129.234.12.100', user='DIMAS', passwd='fddd-anode', db='chem'):
#      self.conn = MySQLdb.connect(host, user, passwd, db)

  def run(self, what_to_run="cif_data_items", where_to_run=r"Y:"):
    table = "diffraction_cell"
    dir = where_to_run

    if what_to_run == "cif_data_items":
      data_items = {
        '_refine_ls_R_factor_gt':{'table':'refinement', 'alias':'refine_ls_R_factor_gt'},
        '_refine_ls_R_factor_obs':{'table':'refinement', 'alias':'refine_ls_R_factor_gt'},
        '_diffrn_ambient_temperature':{'table':'diffraction', 'alias':'diffrn_ambient_temperature'},
        '_symmetry_cell_setting':{'table':'refinement', 'alias':'Setting'},
        '_symmetry_space_group_name_H-M':{'table':'refinement', 'alias':'SpaceGroup'},
                  }
      type = "cif"
      table = "diffraction"
      type = "cif"
      rs = self.upload_data_item(dir, type, data_items=data_items, update=True)

    elif what_to_run == "smiles":
      rs = self.do_smiles(dir)

  def create_smiles(self, cifFile):
    obConversion = OBConversion()
    obConversion.SetInFormat("cif")
    obConversion.SetOutFormat("smi")
    obmol = OBMol()
    print "Going to read %s for SMILE conversion" %cifFile
    #time.sleep(1)
    try:
      notatend = obConversion.ReadFile(obmol,cifFile)
    except:
      return 
    outSmile = obConversion.WriteString(obmol)
    smileFile = "%ssmi" %cifFile[:-3]
    wFile = open(smileFile, 'w')
    wFile.write(outSmile)
    wFile.close()
    obConversion.SetInFormat("cif")
    #obConversion.SetOutFormat("inchi a")
    obConversion.SetOutFormat("inchi")
    #obConversion.AddOption( "a", OBConversion.OUTOPTIONS )
    obmol = OBMol()
    print "Going to read %s for INCHI conversion" %cifFile
    notatend = obConversion.ReadFile(obmol,cifFile)
    outInchi = obConversion.WriteString(obmol)
    inchiFile = "%sinchi" %cifFile[:-3]
    wFile = open(inchiFile, 'w')
    wFile.write(outInchi)
    wFile.close()
    print "Written %s" %inchiFile
    return outSmile, outInchi


  def upload_png(self, dir, table, type):
    types = ["png", "gif", "jpg"]
    log = open("%s\log.txt" %dir, 'w')

    for type in types:
      files = "*.%s" %type
      png_files = FS.Node(dir).walk(files)

      for png_info in png_files:
        png_path = png_info.path
        png_node = FS.Node(png_path)
        ID = str(png_path.basename)
        ID = ID.split(".")[0]
        #ID = ID.replace("-", "xxx")

        fileData = png_node.open('rb').read()
        #fileData = zlib.compress(fileData,9)
        fileData = MySQLdb.escape_string(fileData)
        #sql = r'INSERT submission_img (sNum,img) VALUES("%s","%s") ON DUPLICATE KEY UPDATE img="%s";' %(sNum, fileData, fileData,)
        sql = r'INSERT %s (Name, Img, Type, Display) VALUES ("%s", "%s", "%s", "%s") ON DUPLICATE KEY UPDATE Img="%s", Type="%s", Display="%s";' %(table, ID,fileData,type,ID, fileData,type,ID)
        res = ds.sqlINSERT(sql)
        ds.conn.commit()
        print "Inserted %s" %ID

  def get_list_of_files(self, dir, type):
    print "Compiling a list of %s files in %s and all subdirectories. This might take some time" %(type, dir)
    type_full = "*.%s" %type
    f_files = FS.Node(dir).walk(type_full)
    log = open("%s\log.txt" %dir, 'w')
    list_of_files = []
    for f_info in f_files:
      f_path = f_info.path
      f_node = FS.Node(f_path)
      ID = str(f_path.basename)
      ID = ID.split(".")[0]
      try:
        float(ID[:2])
      except:
        log.write("%s: non standard name" %ID)
        continue
      list_of_files.append({"ID":ID,"path":str(f_path)})
    return list_of_files

  def do_smiles(self, dir):
    bable_crash = ['96srv031', 
                   '96srv059', 
                   '96srv071', 
                   '96srv077',
                   '96srv078',
                   '96srv079',
                   '96srv080',
                   '96srv083',
                   '96srv086',
                   '96srv087',
                   '96srv088',
                   '96srv089',
                   '96srv093',
                   '96srv096',
                   '96srv097',
                   '96srv098',
                   '96srv099',
                   '96srv109',
                   '96srv112',
                   '96srv116',
                   '96srv117',
                   '00CKB005',
                   '01srv096',
                   '01srv146',
                   '04srv388',
                   '05srv152',
                   '06srv070',
                 ]
    bable_crash = []
    list_of_files = self.get_list_of_files(dir, "cif")
    for file in list_of_files:
      path = file.get('path')
      ID = file.get('ID')
      if ID in bable_crash:
        continue
      if 'meta' in ID:
        continue
      
      try:
        smi, inchi = self.create_smiles(path)
      except:
        print "@@@@@ %s has caused OpenBabel to fail @@@@" %str(path)
        continue
      sql = r'INSERT refinement (ID,Smile,Inchi) VALUES("%s","%s","%s") ON DUPLICATE KEY UPDATE Smile="%s", Inchi="%s";' %( ID, smi, inchi, smi, inchi)
      try:
        res = self.ds.run_sql(sql)
      except:
        print "PROBLEM!!!!"
        
  def test_upload_file(self):
    #rFile = open(r"C:\test.smi", 'r')
    rFile = open(r"S:\00srv000.cif", 'r')
    fileData = rFile.read()
    fileData = zlib.compress(fileData,9)
    fileData = self.ds.escape_strings(fileData)
    ID = '00srv000'
    type = 'cif'
    table = 'refinement_data'
    
    sql = r'INSERT %s (ID,%s) VALUES("%s","%s") ON DUPLICATE KEY UPDATE %s="%s";' %(table, type, ID, fileData, type, fileData,)
    res = self.ds.run_sql(sql)


  def upload_file(self, dir, type, table, update=False):
    type_full = "*.%s" %type
    f_files = FS.Node(dir).walk(type_full)
    log = open("%s\log.txt" %dir, 'w')
    subject = table.split("_")[0]

    for f_info in f_files:
      f_path = f_info.path
      f_node = FS.Node(f_path)
      ID = str(f_path.basename)
      ID = ID.split(".")[0]
      try:
        float(ID[:2])
      except:
        log.write("%s: non standard name" %ID)
        continue
      fileData = f_node.open('rb').read()
      fileData = zlib.compress(fileData,9)
      fileData = self.ds.escape_strings(fileData)

      if update:
        sql = r'INSERT %s (ID,%s) VALUES("%s","%s") ON DUPLICATE KEY UPDATE %s="%s";' %(table, type, ID, fileData, type, fileData,)
      else:
        sql = r'INSERT %s (ID,%s) VALUES("%s","%s");' %(table, type, ID, fileData)
      try:
        res = self.ds.run_sql(sql)
      except:
        log.write("%s There was an error with this table %s\n" %(ID, table))

      #sql = r'INSERT %s (ID,data_%sID) VALUES("%s","%s") ON DUPLICATE KEY UPDATE data_%sID="%s";' %(subject, string.capwords(type), ID, ID, string.capwords(type), ID,)
      try:
        res = self.ds.run_sql(sql)
      except:
        log.write("%s There was an error with this table %s\n" %(ID, table))

      print "Inserted %s" %ID
      log.flush()
    log.close()

  def upload_data_item(self, dir, type, data_items=[], update=False):
    type_full = "*.%s" %type
    f_files = FS.Node(dir).walk(type_full)
    log = open("%s\log.txt" %dir, 'w')

    for f_info in f_files:
      f_path = f_info.path
      f_node = FS.Node(f_path)
      ID = str(f_path.basename)
      ID = ID.split(".")[0]
      try:
        float(ID[:2])
      except:
        log.write("%s: non standard name" %ID)
        continue

      fileData = f_node.open('rb').readlines()
      dataadded = ""
      for data_item in data_items:
        value = False
        for item in fileData:
          item = item.strip()
          try:
            if item.split()[0] == data_item:
              try:
                value = "%s" %item.split(data_item)[1].strip().strip("'")
              except:
                pass
              break
          except:
            continue
        if not value:
          print "Not updated %s: No value for %s" %(ID, data_item)
          continue
        table = data_items[data_item].get('table')
        subject = table.split("_")[0]
        db_field = data_items[data_item].get('alias', data_item)
        if update:
          sql = self.ds.create_update_sql({'ID':"'%s'" %ID, '%s' %db_field:"'%s'" %value}, table)
          #sql = r'INSERT %s (ID,%s) VALUES("%s","%s") ON DUPLICATE KEY UPDATE %s="%s";' %(table, type, ID, fileData, type, fileData,)
        else:
          sql = self.ds.create_insert_sql({db_field:value}, table)
          #sql = r'INSERT %s (ID,%s) VALUES("%s","%s");' %(table, type, ID, fileData)
        try:
          res = self.ds.run_sql(sql)
          dataadded += "%s=%s, " %(data_item, str(value))
        except:
          log.write("%s There was an error with this table %s\n" %(ID, table))

      print "Inserted into %s: %s" %(ID, dataadded[:-2])
      log.flush()
    log.close()

    
    
  def help_to_db(self):
    sql = "SELECT * from categories"
    rs = ds.sqlSQL(sql)
    categories = {}
    for entry in rs:
      categories.setdefault(entry[1], entry[0])

    file = "G:\help.xld"
    rFile = open(file, 'r')
    f = []
    for line in rFile:
      f.append(line)

    i = 0
    for line in f:
      if line[:2] == " <":
        li = line.split(' help="')
        name = li[0]
        name = name.strip()
        name = name[1:]

        help = li[1]
        help = help.strip()
        help = help[:-1]
        help = help.replace('" switch0="', 'Options: ')
        help = help.replace('" switch1="', ' ')
        help = help.replace('" switch2="', ' ')
        help = help.replace('" switch3="', ' ')
        help = help.replace('" switch4="', ' ')

        cat = f[i+2]
        cat = cat.replace("<", "")
        cat = cat.replace(r"\>", "")
        cat = cat.strip()
        cat = cat.lower()
        try:
          category = categories[cat]
        except:
          category = 0

        sql = r'INSERT commands (Name, Help1, CategoryID) VALUES("%s","%s", "%s");' %(name, help, category)
        try:
          rs = ds.sqlSQL(sql)
          ds.conn.commit()
        except:
          print "FAILURE: %s, %s, %s" %(name, category, help)
        print "Inserted %s, %s, %s" %(name, category, help)
      i += 1


  def pull_numbers(self, items, table):

    sql = "SELECT * from %s" %table
    rs = ds.sqlSQL(sql)
    entries = {}
    for entry in rs:
      entries.setdefault(entry[1])
    for entry in entries:
      sqlQ = """
SELECT count( * ) as total_record
FROM %s INNER JOIN %s ON commands.%sID = ID
WHERE (((%s.Name) Like '%s')); """ %(items, table, table, table, entry)
      rs = ds.sqlSQL(sqlQ)
      print entry, rs[0]

  def insert_diffraction_cell_data(self, dir, type, table, update=False, standardnames=True):
    
    type_full = "*.%s" %type
    f_files = FS.Node(dir).walk(type_full)
    log = open("%s\log.txt" %dir, 'w')
    subject = table.split("_")[0]

    for f_info in f_files:
      f_path = f_info.path
      f_node = FS.Node(f_path)
      ID = str(f_path.basename)
      ID = ID.split(".")[0]
      if standardnames:
        try:
          float(ID[:2])
        except:
          log.write("%s: non standard name\n" %ID)
          continue
      self.cifItems = {'exptl_crystal_colour':"'n/a'",
                        'exptl_crystal_size_max':"'n/a'",
                        'exptl_crystal_size_med':"'n/a'",
                        'exptl_crystal_size_min':"'n/a'",
                        'symmetry_cell_setting':"'n/a'",
                        'symmetry_space_group_name_H-M':"'n/a'",
                        'ID':"'%s'" %ID,
                       }

      fileData = f_node.open('rb').readlines()
      for line in fileData:
        sl = line.split()
        if len(sl) > 1:
          self.cif_items(line)
          try:
            if sl[0] == "_cell_length_a":
              sp = sl[1].split('(')
              a = str(sp[0])
              err_a = sp[1][:-1]

            elif sl[0] == "_cell_length_b":
              sp = sl[1].split('(')
              b = str(sp[0])
              err_b = sp[1][:-1]

            elif sl[0] == "_cell_length_c":
              sp = sl[1].split('(')
              c = str(sp[0])
              err_c = sp[1][:-1]

            elif sl[0] == "_cell_angle_alpha":
              sp = sl[1].split('(')
              alpha = str(sp[0])
              try:
                err_alpha = sp[1][:-1]
              except:
                err_alpha = '0'

            elif sl[0] == "_cell_angle_beta":
              sp = sl[1].split('(')
              beta = str(sp[0])
              try:
                err_beta = sp[1][:-1]
              except:
                err_beta = '0'

            elif sl[0] == "_cell_angle_gamma":
              sp = sl[1].split('(')
              gamma = str(sp[0])
              try:
                err_gamma = sp[1][:-1]
              except:
                err_gamma = '0'

            elif sl[0] == "_cell_volume":
              sp = sl[1].split('(')
              volume = str(sp[0])
              err_volume = sp[1][:-1]

          except:
            print "Something is seriosly wrong with %s" %ID
            log.write("Something is seriously wront with the cif file of %s\n" %(ID))
            

      try:
        sql = """
INSERT %s
(ID, cell_a, cell_b , cell_c, cell_alpha, cell_beta, cell_gamma, cell_volume, cell_a_err, cell_b_err, cell_c_err, cell_alpha_err, cell_beta_err, cell_gamma_err, cell_volume_err)
VALUES("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s" )
ON DUPLICATE KEY UPDATE cell_a="%s", cell_b="%s", cell_c="%s", cell_alpha="%s", cell_beta="%s", cell_gamma="%s", cell_volume="%s", cell_a_err="%s", cell_b_err="%s", cell_c_err="%s", cell_alpha_err="%s", cell_beta_err="%s", cell_gamma_err="%s", cell_volume_err="%s";
""" %(table, ID, a, b, c, alpha, beta, gamma, volume, err_a, err_b, err_c, err_alpha, err_beta, err_gamma, err_volume, a, b, c, alpha, beta, gamma, volume, err_a, err_b, err_c, err_alpha, err_beta, err_gamma, err_volume,)
        res = self.ds.run_sql(sql)
        self.ds.conn.commit()
        sql = self.ds.create_insert_or_update_sql(self.cifItems, 'crystal')
        #sql = self.ds.escape_strings(sql)
        res = self.ds.run_sql(sql)

      except:
        log.write("%s There was an error with this table %s\n" %(ID, table))

      #sql = r'INSERT %s (ID,data_%sID) VALUES("%s","%s") ON DUPLICATE KEY UPDATE data_%sID="%s";' %(subject, string.capwords(type), ID, ID, string.capwords(type), ID,)
      #try:
      # res = ds.sqlINSERT(sql)
      #except:
      # log.write("%s There was an error with this table %s\n" %(ID, table))

      print "%s for cell info for %s: %s, %s, %s, %s, %s, %s, " %(res, ID, a, b, c, alpha, beta, gamma)
      log.flush()
    log.close()

  def update_help(self):
    host='129.234.12.100'
    user='DIMAS'
    passwd='fddd-anode'
    db='OlexGui'
    self.conn = MySQLdb.connect(host, user, passwd, db)
    sqlQ = "SELECT commands.ID, commands.Standard_Help, category.Name FROM commands INNER JOIN category ON commands.categoryID = category.ID;"
    res = []
    cur = self.conn.cursor()
    cur.execute(sqlQ)
    res = cur.fetchall()
    self.write_help_file(res)

  def write_help_file(self, res):
    wFile = open("C:\help.xld", 'w')
    wFile.write('<xl_help\n')
    for result in res:
      command = result[0]
      help_txt = result[1]
      cat = result[2]
      wFile.write(' <%s help="%s"\n' %(command, help_txt))
      wFile.write('  <category\n')
      wFile.write('   <%s \>\n' %cat)
      wFile.write('  \>\n')
      wFile.write(' \>\n\n')
    wFile.write("\>")

  def cif_items(self, string):
    
    for item in self.cifItems:
      regex = re.compile(r"  _%s \s+ (.*)"%(item),  re.X)  
      m = regex.findall(string)
      if m:
        for bit in m:
          str = "'%s'" %bit[:-2]
          self.cifItems[item] = str

if __name__ == '__main__':
  python_lib = r"C:\Documents and Settings\Horst\Desktop\olex\util\pyUtil\PythonLib"
  sys.path.insert(0, python_lib)
  import FileSystem as FS

  a = UpdateDimasDB()

  a.test_upload_file()
  #what_to_run = "smiles"
  #where_to_run = r"Y:\2007"
  #a.run(what_to_run=what_to_run, where_to_run=where_to_run)

#  ds = SQLFactory()
#  res = ds.update_help()

  #res = ds.pull_numbers("commands", "category")
  #res = ds.help_to_db()

# table = "images"
# dir = "C://t//olex_img"
# type = "gif"
# res = ds.upload_png(dir, table, type)


### Insert data from cif files on Y: into table
  #what_to_run = "cif_data_items"
  #where_to_run = r"Y:"
  #a.run(what_to_run=what_to_run, where_to_run=where_to_run)
