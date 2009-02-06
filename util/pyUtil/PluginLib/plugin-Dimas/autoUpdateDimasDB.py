# autoUpdateDimasDB.py
import os
import sys
sys.path.append(r"../plugin-MySQL")
import time
import pywintypes, win32api, win32con
import glob
import pickle
import re
import SQLFactory
import zlib
from openbabel import *

#from createOrUpdateHTMLFileInFolder import CreateHTMLFileFromInfoInDB
#from updateDBfromfile import UpdateDBfromFile

def getPath(fname,dbBaseDir):
  """Returns the folder path, file path and structure ID number of a given file based on the filename."""
  if int(fname[0:2]) < 90:
    year = "20" + fname[0:2]
  elif int(fname[0:2]) >= 90:
    year = "19" + fname[0:2]
  
  ID = fname.split(".")[0]
  folderPath = "%s\\%s\\%s" %(dbBaseDir,year, ID)
  filePath = "%s\\%s" %(folderPath,fname)
  
  return folderPath, filePath, ID

class AutoUpdateDimasDB(object):
  def __init__(self, dir, database, types=['cif', 'hkl', 'p4p', 'prp', 'res', 'doc']):
    """The first argument is the basedirectory of the database.
    Second argument is the database.
    The third argument is a list of file types"""
    self.ds = SQLFactory.SQLFactory(db=database)
    self.dir = dir
    self.logPath = r"%s\log.txt" %self.dir
    self.timestampsFilePath = "%s\\timestamps.pickle" %self.dir
    
    self.types = types
    
  def run(self):   
    # Turn off read-only attribute of log file and then open in append mode, write start time to log file
    self.change_file_attribute(self.logPath, readOnly = False)
    self.log = open(self.logPath, 'a')
    self.log.write("Start time: %s\n\n" %time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time())))
    
    
    self.updateFromFile()
    self.get_list_of_files()
    self.cifDataItems()
    self.do_smiles()
    self.uploadFiles(update=True)
    self.createHTMLFiles()
    
    # Write finish time to log file, trim the file size, close the file, then make it to read-only
    self.log.write("\nFinish time: %s\n\n----------------------------------------------\n\n" %time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time())))
    self.trimLogFileSize(numberLines=2000)
    self.log.close()
    self.change_file_attribute(self.logPath, readOnly = True)
    
  def change_file_attribute(self, filePath, hidden=False, readOnly=False):
    """Changes the file attributes 'Hidden' and 'Read-only'.
    
    First argument is the path of the file whose attributes are to be changed.
    Second and third arguments are the values of hidden and readOnly, which should be either True or False.
    """
    x = win32api.GetFileAttributes(filePath)
    if hidden == True:
      x |= win32con.FILE_ATTRIBUTE_HIDDEN
    elif hidden == False:
      x &= ~win32con.FILE_ATTRIBUTE_HIDDEN
    win32api.SetFileAttributes(filePath, x)
    
    if readOnly == True:
      x |= win32con.FILE_ATTRIBUTE_READONLY
    elif readOnly == False:
      x &= ~win32con.FILE_ATTRIBUTE_READONLY
    win32api.SetFileAttributes(filePath, x)
    
  def cifDataItems(self):
    """Defines a list of cif items to be extracted from a cif file and uploaded to the dimas database.
    
    The value of each dictioanry item is another dictionary which contains the database table name and
    the alias or field name for that cif item.
    The method 'uploadDataItems' is then called for each modified cif file to upload extract the cif
    items from the cif file and upload them to the dimas database.
    """
    data_items = {
      '_refine_ls_R_factor_gt':{'table':'refinement', 'alias':'refine_ls_R_factor_gt'},
      '_refine_ls_R_factor_obs':{'table':'refinement', 'alias':'refine_ls_R_factor_gt'},
      '_diffrn_ambient_temperature':{'table':'diffraction', 'alias':'diffrn_ambient_temperature'},
      '_symmetry_cell_setting':{'table':'refinement', 'alias':'Setting'},
      '_symmetry_space_group_name_H-M':{'table':'refinement', 'alias':'SpaceGroup'},
      '_exptl_crystal_colour':{'table':'crystal', 'alias':'exptl_crystal_colour'},
      '_exptl_crystal_size_min':{'table':'crystal', 'alias':'exptl_crystal_size_min'},
      '_exptl_crystal_size_mid':{'table':'crystal', 'alias':'exptl_crystal_size_mid'},
      '_exptl_crystal_size_max':{'table':'crystal', 'alias':'exptl_crystal_size_max'},
      '_exptl_crystal_description':{'table':'crystal', 'alias':'CifShape'},
                }
    type = "cif"
    table = "diffraction"
    
    for file in self.modifiedFiles["*.%s" %type]:
      folderPath,cifPath,ID = getPath(file,self.dir)
      self.uploadDataItems(cifPath,ID,data_items,update=True)
      
  def do_smiles(self):
    """Creates smiles and inchi files for all modified cif files, and then uploads the files to the dimas database."""
    self.log.write("\n")
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
    
    type = "cif"
    for folder in self.modifiedFiles["*.%s" %type]:
      folderPath,cifPath,ID = getPath(folder,self.dir)
      if os.path.exists(cifPath):
          
        if ID in bable_crash:
          continue
        if 'meta' in ID:
          continue
        
        try:
          smi, inchi = self.create_smiles(cifPath)
        except:
          self.log.write("@@@@@ %s has caused OpenBabel to fail @@@@\n" %str(cifPath))
          print "@@@@@ %s has caused OpenBabel to fail @@@@" %str(cifPath)
          continue
        sql = r'INSERT refinement (ID,Smile,Inchi) VALUES("%s","%s","%s") ON DUPLICATE KEY UPDATE Smile="%s", Inchi="%s";' %( ID, smi, inchi, smi, inchi)
        try:
          res = self.ds.run_sql(sql)
        except:
          self.log.write("!!!! OpenBabel sql failed for %s!!!!\n" %ID)
          print "PROBLEM!!!!"
      else:
        print "No cif file in %s" %ID
      self.log.flush()
        
  def create_smiles(self, cifPath):
    """Creates SMILES and InChi files from the given cif path, returns the smiles and inchi strings."""
    obConversion = OBConversion()
    obConversion.SetInFormat("cif")
    obConversion.SetOutFormat("smi")
    obmol = OBMol()
    print "Going to read %s for SMILE conversion" %cifPath
    #time.sleep(1)
    try:
      notatend = obConversion.ReadFile(obmol,cifPath)
    except:
      return 
    outSmile = obConversion.WriteString(obmol)
    smileFile = "%ssmi" %cifPath[:-3]
    wFile = open(smileFile, 'w')
    wFile.write(outSmile)
    wFile.close()
    self.log.write("Written %s\n" %smileFile)
    obConversion.SetInFormat("cif")
    #obConversion.SetOutFormat("inchi a")
    obConversion.SetOutFormat("inchi")
    #obConversion.AddOption( "a", OBConversion.OUTOPTIONS )
    obmol = OBMol()
    print "Going to read %s for INCHI conversion" %cifPath
    notatend = obConversion.ReadFile(obmol,cifPath)
    outInchi = obConversion.WriteString(obmol)
    inchiFile = "%sinchi" %cifPath[:-3]
    wFile = open(inchiFile, 'w')
    wFile.write(outInchi)
    wFile.close()
    self.log.write("Written %s\n" %inchiFile)
    print "Written %s" %inchiFile
    return outSmile, outInchi
    
  def uploadDataItems(self, filePath, ID, data_items={}, update=False):
    """Reads a cif file and uploads each cif item in a dictionary of cif items to the dimas database.
    
    First argument is the path of the cif file.
    Second argument is the dimas structure ID, or service number.
    Third argument a dictionary of cif data items to be extracted from the cif file.
    The value of each dictionary item is another dictionary which contains the database table name and
    the alias or field name for that cif item.
    If update is set to True (default value is False), and the specified structure ID is already in the
    table, the old row is will be updated.
    """
    if os.path.exists(filePath):
      fileData = open(filePath,'rb').readlines()
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
          sql = """INSERT INTO %s (ID, %s) VALUES ("%s", "%s") ON DUPLICATE KEY UPDATE %s = "%s" """ %(table,db_field,ID,value,db_field,value)
        else:
          sql = self.ds.create_insert_sql({'ID':"'%s'" %ID, '%s' %db_field:"'%s'" %value}, table)
          
        try:
          res = self.ds.run_sql(sql)
          dataadded += "%s = %s\n" %(data_item, str(value))
        except:
          self.log.write("!!!! %s There was an error with this table %s!!!!\n" %(ID, table))
        
      self.log.write("Inserted into %s from cif file:\n%s\n" %(ID, dataadded[:]))

      print "Inserted into %s: %s" %(ID, dataadded[:])
    else:
      print "No cif file in %s" 
    
    self.log.flush()
      
    return 
  
  def uploadFiles(self, update=False, compress=True):
    """Uploads each file in self.modifiedFiles to the dimas database.
    
    If update is set to True (default value is False), and the specified structure ID is already in the
    table, the file in the database will be replaced by the modified file.
    If compress is set to True (default value is True), the file will be compressed using the zlib module
    before being uploaded to the database.
    """
    
    self.log.write("\n")
    # sort out which files are to go in which table in the database
    diffraction_files = ('hkl','p4p','prp')
    refinement_files = ('cif', 'res', 'doc')
    for type in self.types:
      for file in self.modifiedFiles["*.%s" %type]:
        folderPath,filePath,ID = getPath(file,self.dir)
        if os.path.exists(filePath):
          fileData = open(filePath,'rb').read()
          if compress:
            fileData = zlib.compress(fileData,9)
          fileData = self.ds.escape_strings(fileData)
          if type in diffraction_files:
            table = "diffraction_data"
          elif type in refinement_files:
            table = "refinement_data"          
          else:
            pass
          
          if update:
            sql = r'INSERT %s (ID,%s) VALUES("%s","%s") ON DUPLICATE KEY UPDATE %s="%s";' %(table, type, ID, fileData, type, fileData,)
          else:
            sql = r'INSERT %s (ID,%s) VALUES("%s","%s");' %(table, type, ID, fileData)
          res = self.ds.run_sql(sql)
          
          if res == "Success":
            self.log.write("Successfully uploaded %s file for %s\n" %(type, ID))
          elif res == "Failure":
            self.log.write("!!!! The upload of %s file for %s failed!!!!\n" %(type, ID))
          print "%s with %s file of %s" %(res, type, ID)
    
          self.log.flush()
    
  def updateFromFile(self):
    """Updates the dimas database for structures where an update file has been created or modified."""
    StructuresUpdatedFromFile = UpdateDBfromFile().updateDBfromFile()
    if StructuresUpdatedFromFile:
      self.log.write("The dimas database was updated from a dimas_update.txt file for the following structures: %s\n\n" %StructuresUpdatedFromFile)
      self.log.flush()
    
  def createHTMLFiles(self):
    """Creates or updates html files containing information about the each structure in its database folder."""
    #from createOrUpdateHTMLFileInFolder2 import CreateHTMLFileFromInfoInDB
    createdHtmlFiles,updatedHtmlFiles,failedHtmlFiles = CreateHTMLFileFromInfoInDB(self.dir).create_and_update_all_HTML_files()
    if createdHtmlFiles or updatedHtmlFiles or failedHtmlFiles:
      self.log.write("\n")
      if createdHtmlFiles:
        self.log.write("New HTML files created: %s\n" %createdHtmlFiles)
      if updatedHtmlFiles:
        self.log.write("HTML files updated: %s\n" %updatedHtmlFiles)
      if failedHtmlFiles:
        self.log.write("The following files failed whilst trying to update the HTML file: %s\n" %failedHtmlFiles)
    else:
      self.log.write("No HTML files were created or updated")
    self.log.flush()
          
  def get_list_of_files(self):
    """Gets a list of all files of type given in the list 'type' that have been modified.
    
    The modification time for each file is compared with the timestamp stored in the timestamps.pickle file.
    """
    
    print "Compiling a list of all modified %s files in %s. This might take some time" %(self.types, self.dir)
    type_full = []
    self.modifiedFiles = {}
    
    for i in range(len(self.types)):
      type_full.append("*.%s" %self.types[i])
    
    if os.path.exists(self.timestampsFilePath):
      inFile = open(self.timestampsFilePath, "r")
      try:
        self.pickle_modification_times = pickle.load(inFile)
      except ValueError:
        # error loading pickle file
        self.pickle_modification_times = {}
    else:
      self.pickle_modification_times = {}
      
    self.change_file_attribute(self.timestampsFilePath, readOnly = False, hidden = False)
      
    for type in type_full:
      print "Compiling a list of modified %s files" %type
      modifiedFiles = []
      
      for year in range(1993,2009):
        path = "%s\\%s" %(self.dir,year)
        list_dir = os.listdir(path)
        for dir in list_dir:
          fileTypePath = "%s\\%s\\%s" %(path, dir, type)
          fileList = glob.glob(fileTypePath)
          if not fileList:
            pass
          else:
            for file in self.checkIfFileModified(fileList):
              modifiedFiles.append(file)
      self.modifiedFiles[type] = modifiedFiles
    
    self.updateTimestampsFile()
    self.change_file_attribute(self.timestampsFilePath, readOnly = True, hidden = True)
    
  def checkIfFileModified(self,fileList):
    """Checks a if any files in a list of files have been modified, and returns a list of modified files."""
    for file in fileList:
      modifiedFiles = []
      fileName = file.split("\\")[-1]
      ID = fileName.split(".")[0]
      if re.match("\d\d", ID) and len(ID) in (6,7,8):
        fileModificationTime = os.path.getmtime(file)
        if not self.pickle_modification_times.has_key(fileName):
          self.pickle_modification_times[fileName]=fileModificationTime
          modifiedFiles.append(fileName)
        elif fileModificationTime > self.pickle_modification_times[fileName]:
          self.pickle_modification_times[fileName]=fileModificationTime
          modifiedFiles.append(fileName)
        else:
          pass
        
    return modifiedFiles
      
  def _getModifiedFolders(self, list_dir, dir):
    
    new_modification_times = {}
    modifiedFolders = []
  
    for item in list_dir:
      path = "%s\\%s" %(dir,item)
      if os.path.isdir(path) and re.match("\d\d", item):
        new_modification_times[item] = os.path.getmtime(path)
    
    for key in new_modification_times.keys():
      if not self.pickle_modification_times.has_key(key):
        modifiedFolders.append(key)
        self.pickle_modification_times[key]=os.path.getmtime(path)
      elif new_modification_times[key] > self.pickle_modification_times[key]:
        modifiedFolders.append(key)
        self.pickle_modification_times[key] = new_modification_times[key]
      else:
        pass
      
    return modifiedFolders
      
  def updateTimestampsFile(self):
    """Dumps the updated timestamps dictionary to the pickle file."""
    outFile = open(self.timestampsFilePath, 'w')
    pickle.dump(self.pickle_modification_times,outFile)
    outFile.close()
    return
  
  #def getPath(self,fname):
    #"""Returns the folder path, file path and structure ID number of a given file based on the filename."""
    #if int(fname[0:2]) < 90:
      #year = "20" + fname[0:2]
    #elif int(fname[0:2]) >= 90:
      #year = "19" + fname[0:2]
    
    #ID = fname.split(".")[0]
    #folderPath = "%s\\%s\\%s" %(self.dir,year, ID)
    #filePath = "%s\\%s" %(folderPath,fname)
    
    #return folderPath, filePath, ID
  
  def trimLogFileSize(self,numberLines=500):
    """Trims the size of the log file so that the number of lines it contains is less than the given number."""
    self.change_file_attribute(self.logPath, hidden = False)
    f = open(self.logPath, 'r')
    lines = f.readlines()
    while len(lines) > numberLines:
      i = 0
      while lines[i][:10] != "----------":
        i += 1
      f.close()
      f = open(self.logPath, 'w')
      f.writelines(lines[i+2:])
      f.close()
      f = open(self.logPath, 'r')
      lines = f.readlines()
      
    f.close()
    self.change_file_attribute(self.logPath, hidden = True)
    return
  

class CreateHTMLFileFromInfoInDB:
  def __init__(self, dir):
    self.ds = SQLFactory.SQLFactory(db='DimasDB')
    self.dir = dir
    self.createdFiles = []
    self.updatedFiles = []
    self.failed_files = []
  
  def main(self):
   
    #self.createHTMLFile()    
    self.create_and_update_all_HTML_files()
        
  def create_and_update_all_HTML_files(self):
    sql = """SELECT submission.ID FROM submission"""
    list_ID = self.ds.run_select_sql(sql)
    #list_ID = ({'ID': '00srv150'}, {'ID': '00srv151'}, {'ID': '00srv152'}, {'ID': '00srv153'}, {'ID': '00srv154'}, {'ID': '00srv155'}, {'ID': '00srv156'}, {'ID': '00srv157'}, {'ID': '00srv158'}, {'ID': '00srv159'}, {'ID': '00srv160'}, {'ID': '00srv161'}, {'ID': '00srv162'}, {'ID': '00srv163'}, {'ID': '00srv164'}, {'ID': '00srv165'}, {'ID': '00srv166'}, {'ID': '00srv168'}, {'ID': '00srv169'}, {'ID': '00srv170'}, {'ID': '00srv171'}, {'ID': '00srv172'}, {'ID': '00srv173'}, {'ID': '00srv174'}, {'ID': '00srv175'}, {'ID': '00srv176'}, {'ID': '00srv177'}, {'ID': '00srv178'}, {'ID': '00srv179'})
    for item in list_ID:
      fname = item['ID']
      if len(fname) >= 6 and len(fname) <=8:
        try:
          int(fname[0:2])
          folderPath, filePath, ID = getPath(fname,self.dir)
          
          ## breakpoint to stop at particular file
          #if fname == "00asb001":
            #print fname
          #else:
            #pass
          
          ##overwrite all files
          #self.createHTMLFile()
          #print "Created HTML file for %s" %fname
          
          # update current exisiting files, create new files
          if os.path.exists(folderPath) and not os.path.exists(filePath):
            CreateHtmlFile(fname,folderPath).createHTMLFile()
            #self.createHTMLFile()
            self.createdFiles.append(fname)
            print "Created HTML file for %s" %fname
          elif os.path.exists(self.filePath) and self.compareFileModificationWithDatabaseTimestamps():
            CreateHtmlFile(fname,folderPath).createHTMLFile()
            #self.createHTMLFile()
            self.updatedFiles.append(fname)
            print "Updated HTML file for %s" %fname
          elif not os.path.exists(folderPath):
            #print "The path %s does not exist" %self.path
            pass
          else:
            #print "No change made to HTML file for %s" %fname
            pass
          
        except:
          print "!!!! %s either does not exist or is not a legitamate file name!!!!" %fname
          pass
      else:
        pass
      
    return self.createdFiles, self.updatedFiles, self.failed_files
  
  def compareFileModificationWithDatabaseTimestamps(self):
    self.getTimeHTMLLastModified()
    self.getTimestampsFromDB()
    
    a = 0
    for i in self.timestamp:
      if i > self.modified:
        a = a + 1
      else:
        pass
    
    if a == 0:
      #print "The database has not been modified for %s" %self.fname
      return False
    else:
      print "The database has been modified for %s" %self.fname
      return True
    
  def getTimeHTMLLastModified(self):
    #self.getPath()
    if os.path.exists(self.htmlPath):
      self.modified = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.path.getmtime(self.htmlPath)))
    else:
      print "The path %s does not exist" %self.htmlPath
    
  def getTimestampsFromDB(self):
    tuple = ("submission", "crystal", "diffraction", "refinement", "progress", "reference", "diffraction_cell")
    self.timestamp = []
    for item in tuple:
      try:
        self.query("""SELECT Timestamp FROM %s WHERE ID = "%s";""" %(item,self.fname))
        self.timestamp.append(self.dictionary['Timestamp'])
      except:
        pass
    
  #def getPath(self,fname,dbBaseDir):
    #"""Returns the folder path, file path and structure ID number of a given file based on the filename."""
    #if int(fname[0:2]) < 90:
      #year = "20" + fname[0:2]
    #elif int(fname[0:2]) >= 90:
      #year = "19" + fname[0:2]
    
    #ID = fname.split(".")[0]
    #folderPath = "%s\\%s\\%s" %(dbBaseDir,year, ID)
    #filePath = "%s\\%s" %(folderPath,fname)
    
    #return folderPath, filePath, ID
    
    
class CreateHtmlFile:
  def __init__(self,fname,folderPath):
    self.ds = SQLFactory.SQLFactory(db='DimasDB')
    self.fname = fname
    self.folderPath = folderPath
    self.htmlPath = "%s\\%s.html" %(self.folderPath,self.fname)
    
  def createHTMLFile(self):
    #self.getPath()
    if os.path.exists(self.folderPath):
      self.sqls()
      self.list_all_labels()
      self.outfile = open(self.htmlPath, 'w')
      self.outfile.write("<html>\n<head>\n<title>%s</title>\n</head>\n<body>\n\n" %(self.fname))
      
      number_query_failures = 0
      
      for sql in self.list_sqls:
        i = self.list_sqls.index(sql)
        title = self.list_table_titles[i]
        list_labels = self.listAllLabels[i]
        try:
          self.query(sql)
          self.HTMLtable(list_labels, title)
        except:
          number_query_failures = number_query_failures + 1
      
      if number_query_failures == 7:
        self.failed_files.append(self.fname)
        print "Number of query failures = 7 for %s" %self.fname
        
      self.outfile.writelines("</body>\n</html>")
      self.outfile.close()
    else:
      print "A folder does not exist in the database for %s" %self.fname
    
  def HTMLtable(self, list_labels, title):
    
    self.outfile.write("""<h3><u>%s</u></h3>\n<table><COLGROUP span="1" width="300"><COLGROUP span="1">\n""" %title)
    
    time.sleep(0.1)
    
    for i in range(0,len(list_labels)):
      a = len(list_labels)
      b = len(list_labels[i])
      try:
        label = list_labels[i][0]
        info = self.dictionary[list_labels[i][1]]
        infoEnd = self.dictionary[list_labels[i][-1]]
        if not info and (not infoEnd):
          pass
        
        else:
          if title == "Unit Cell":
            # for unit cell info
            info2 = self.dictionary[list_labels[i][2]]
            txt = """\t<tr><td><b>%s</b></td><td>%s(%s)<td></tr>\n""" %(label, info, info2)
            
          elif title == "Reference" and label == "Reference":
            
            journal = self.dictionary[list_labels[i][2]]
            volume = self.dictionary[list_labels[i][3]]
            pages = self.dictionary[list_labels[i][4]]
            year = self.dictionary[list_labels[i][5]]
            txt = """\t<tr><td><b>%s</b></td><td>%s, <i>%s</i>, <b>%s</b>, %s, (%s)<td></tr>\n""" %(label, info, journal, volume, pages, year)
            
          elif title == "Crystal" and label == "Size":
            
            size_min = info
            size_med = self.dictionary[list_labels[i][2]]
            size_max = self.dictionary[list_labels[i][3]]
            
            txt = """\t<tr><td><b>%s</b></td><td>%s x %s x %s mm<sup>3</sup><td></tr>\n""" %(label,size_min,size_med,size_max)
          
          elif title == "Crystal" and label == "Colour":
            
            colour_appearance = info
            colour_intensity = self.dictionary[list_labels[i][2]]
            colour_base = self.dictionary[list_labels[i][3]]
            
            txt = """\t<tr><td><b>%s</b></td><td>%s %s %s<td></tr>\n""" %(label,colour_appearance,colour_intensity,colour_base)
            
          else:
            txt = """\t<tr><td><b>%s</b></td><td>%s<td></tr>\n""" %(label, info)
            
            
          txt = str.replace(txt, "None", "")  
          self.outfile.write(txt)
      
      except:
        print "broken on HTML %s table, label = %s: %s" %(title,label,self.fname)
      
    self.outfile.write("</table><br>\n\n")
    
  def query(self, sql):
    
    self.dictionary = self.ds.run_select_sql(sql)[0]
    


   
  def sqls(self):
    progress_sql = """SELECT progress_status.display, progress.DateCollected, progress.DateCompleted, progress.Comment
    FROM progress LEFT JOIN progress_status ON progress.StatusID = progress_status.ID
    WHERE (((progress.ID)="%s"));
    """ %self.fname
    
    reference_sql = """SELECT reference.*
    FROM reference
    WHERE (((reference.ID)="%s"));
    """ %self.fname
    
    refinement_sql = """SELECT refinement.Comment, refinement.refine_ls_R_factor_gt, refinement.Smile, refinement.Inchi, refinement.Setting, refinement.SpaceGroup
    FROM refinement
    WHERE (((refinement.ID)="%s"));
    """ %self.fname
    
    diffract_sql = """SELECT diffraction.Comment, diffraction.diffrn_ambient_temperature, diffraction_diffractometer.display
    FROM diffraction LEFT JOIN diffraction_diffractometer ON diffraction.DiffractometerID = diffraction_diffractometer.ID
    WHERE (((diffraction.ID)="%s"));
    """ %self.fname
    
    submission_sql = """SELECT submission.ID, submission.DateSubmission, submission.ChemicalName, submission.FormulaSubmitted, submission.Code, submission.MeasurementTemperature, submission.ListType, submission.ListReasons, submission.Comment, submitter_fullnames.display, account_fullnames.display, operator_fullnames.display
    FROM people_fullnames AS operator_fullnames RIGHT JOIN (people_fullnames AS account_fullnames RIGHT JOIN (people_fullnames AS submitter_fullnames RIGHT JOIN submission ON submitter_fullnames.ID = submission.SubmitterID) ON account_fullnames.ID = submission.AccountID) ON operator_fullnames.ID = submission.OperatorID
    WHERE (((submission.ID)="%s"));
    """ %self.fname
    
    crystal_sql = """SELECT crystal_colourappearance.display, crystal_colourintensity.display, crystal_colourbase.display, crystal.exptl_crystal_colour, crystal.exptl_crystal_size_min, crystal.exptl_crystal_size_med, crystal.exptl_crystal_size_max, crystal_shape.display, crystal.CifShape, crystal.NameSystematic, crystal.FormulaSum, crystal.Mass, crystal.MeltingPoint_1, crystal.MeltingPoint_2, crystal.MeltingPoint_3, crystal.Density, crystal.Comment, crystal.CommentPreparation, crystal.CommentCrystallisation
    FROM crystal_shape RIGHT JOIN (crystal_colourintensity RIGHT JOIN (crystal_colourbase RIGHT JOIN (crystal_colourappearance RIGHT JOIN crystal ON crystal_colourappearance.ID = crystal.ColourAppearanceID) ON crystal_colourbase.ID = crystal.ColourBaseID) ON crystal_colourintensity.ID = crystal.ColourIntensityID) ON crystal_shape.ID = crystal.ShapeID
    WHERE (((crystal.ID)="%s"));
    """ %self.fname
    
    diff_cell_sql = """SELECT diffraction_cell.cell_a, diffraction_cell.cell_b, diffraction_cell.cell_c, diffraction_cell.cell_alpha, diffraction_cell.cell_beta, diffraction_cell.cell_gamma, diffraction_cell.cell_volume, diffraction_cell.cell_a_err, diffraction_cell.cell_b_err, diffraction_cell.cell_c_err, diffraction_cell.cell_alpha_err, diffraction_cell.cell_beta_err, diffraction_cell.cell_gamma_err, diffraction_cell.cell_volume_err
    FROM diffraction_cell
    WHERE (((diffraction_cell.ID)="%s"));
    """ %self.fname
    
    self.list_sqls = [submission_sql,crystal_sql,diffract_sql,refinement_sql,progress_sql,reference_sql, diff_cell_sql]
    self.list_table_titles = ['Submission', 'Crystal', 'Diffraction', 'Refinement', 'Progress', 'Reference', 'Unit Cell']
  
  def list_all_labels(self):
    
    submission_list = [("Submission ID", "ID"), ("Submission Date", "DateSubmission"), ("Submitter", "display"), ("Account Surname", "account_fullnames.display"), ("Operator Surname", "operator_fullnames.display"), ("Formula Submitted", "FormulaSubmitted"), ("Chemist Codename", "Code"), ("Measurement Temperature", "MeasurementTemperature"), ("Type", "ListType"), ("Reasons", "ListReasons"), ("Comment", "Comment")]
    crystal_list = [("Colour","display","crystal_colourintensity.display","crystal_colourbase.display"), ("Size", "exptl_crystal_size_min", "exptl_crystal_size_med", "exptl_crystal_size_max"), ("Shape", "crystal_shape.display"), ("Sum Formula", "FormulaSum"), ("Mass", "Mass"), ("Melting Point", "MeltingPoint_1"), ("Density", "Density"), ("Comment", "Comment"), ("Experimental Details of Sample Preparation", "CommentPreparation"), ("Experimental Details of Crystallisation", "CommentCrystallisation")]
    diffraction_list = [("Diffractometer Name", "display"), ("Diffraction Temperature", "diffrn_ambient_temperature"), ("Comment", "Comment")]
    refinement_list = [("R Factor", "refine_ls_R_factor_gt"), ("SMILES", "Smile"), ("InChI", "Inchi"), ("Setting", "Setting"), ("Space Group", "SpaceGroup"), ("Comment", "Comment")]
    progress_list = [("Progress Status", "display"), ("Date Collected", "DateCollected"), ("Date Completed", "DateCompleted"), ("Comment", "Comment")]
    reference_list = [("CCDCNo", "CCDCNo"), ("CSD REFCODE", "REFCODE"), ("Reference", "publ_authors", "journal_name_full", "journal_volume", "journal_pages", "journal_year")]
    diff_cell_list = [("a", "cell_a", "cell_a_err"), ("b", "cell_b", "cell_b_err"), ("c", "cell_c", "cell_c_err"), ("alpha", "cell_alpha", "cell_alpha_err"), ("beta", "cell_beta", "cell_beta_err"), ("gamma", "cell_gamma", "cell_gamma_err"), ("Volume", "cell_volume", "cell_volume_err")]
    
    self.listAllLabels = [submission_list, crystal_list, diffraction_list, refinement_list, progress_list, reference_list, diff_cell_list]


class UpdateDBfromFile(object):
  def __init__(self, path=""):
    self.ds = SQLFactory.SQLFactory(db='DimasDB')
    self.path = path
    #self.fname = fname

  def main(self):
    
    self.updateDBfromFile()
    
  def updateDBfromFile(self):
    self.getDictionariesForLinkedTables() 
    self.getListAllStructures()
    self.updatedStructures = []
    for item in self.listID:
      ID = item['ID']
      if len(ID) >= 6 and len(ID) <=8:
        
        try:
          int(ID[0:2])
          self.fname = ID
          self.getPath()
          self.filePath = "%s\\dimas_update.txt" %self.path
          

          if os.path.exists(self.filePath) and self.compareUpdateDimasFileModificationWithDatabaseTimestamps():
            self.getInfoFromFile()
            self.createSQLs()
            self.updatedStructures.append(self.fname)
            print "The database has been updated for %s" %self.fname
          #else:
            #print self.fname
        except:
          pass
      else:
        pass
    print "The database has been updated for the following structures: %s" %self.updatedStructures
    
    return self.updatedStructures
    
  def getListAllStructures(self):
    sql = """SELECT submission.ID FROM submission"""
    self.listID = self.ds.run_select_sql(sql)
    
  def getPath(self):
    if int(self.fname[0:2]) < 90:
      year = "20" + self.fname[0:2]
    elif int(self.fname[0:2]) >= 90:
      year = "19" + self.fname[0:2]
      
    self.path = "Y:\\%s\\%s" %(year, self.fname)

  def getInfoFromFile(self):
    path = self.path
    filePath = self.filePath
    
    if os.path.exists(filePath):
      text = open(filePath, 'r').readlines()
      i = 0
      tempDict = {}
      for line in text:
        
        if ":" in line:
          a = line.split(":")
          label = a[0]
          item = a[1].split("(")[0]
          tempDict[label] = item.strip()
        else:
          pass
        
        i += 1
    
    self.lablesToDB = {'Crystal Colour Base': 'crystal_colourbase.display','Crystal Colour Appearance': 'crystal_colourappearance.display', 'Crystal Colour Intensity': 'crystal_colourintensity.display', 
                       'Crystal Size (max)': 'crystal.exptl_crystal_size_max', 'Crystal Size (med)': 'crystal.exptl_crystal_size_med', 'Crystal Size (min)': 'crystal.exptl_crystal_size_min',
                       'Published Authors': 'reference.publ_authors','Date Completed': 'progress.DateCompleted', 
                       'Journal Volume': 'reference.journal_volume','Journal Year': 'reference.journal_year', 
                       'CCDCNo': 'reference.CCDCNo', 'REFCODE': 'reference.REFCODE', 'Journal Name': 'reference.journal_name_full', 
                       'Progress Status': 'progress_status.display', 'Journal Pages': 'reference.journal_pages', 
                       'Reference Comment': 'reference.Comment', 'Date Collected': 'progress.DateCollected', 
                       'Crystal Shape': 'crystal_shape.display', 'Progress Comment': 'progress.Comment'}
    
    self.newDict = {}
    
    for i in tempDict:
      
      DBlabel = self.lablesToDB[i]
      self.newDict[DBlabel] = tempDict[i]
     
  def createSQLs(self):
    
    for i in self.newDict.keys():
      tableName = i.split(".")[0]
      fieldName = i.split(".")[1]
      
      ## break at particular filename
      #if self.fname == "00srv000":
        #print
      
      if self.newDict[i] == '?':
        pass
      
      elif not self.newDict[i]:
        pass
      
      else:
        if "_" in tableName:
          tableName_1 = tableName.split("_")[0]
          tableName_2 = tableName.split("_")[1]
          
          tuple = self.dictionaryOfTuples[tableName]
          
          display = self.newDict[i]
          # reset id to None
          id = None
          
          for dict in tuple:
            if dict[i].lower() == display.lower():
              id = dict["%s.ID" %tableName]
            else:
              pass
            
          sql = """INSERT INTO %s (ID,%sID) VALUES ("%s",%s) ON DUPLICATE KEY UPDATE %sID = %s""" %(tableName_1,tableName_2,self.fname,id,tableName_2,id)
          #sql = """UPDATE %s SET %s.%sID = %s WHERE ((%s.ID = %s))""" %(tableName_1,tableName_1,tableName_2,id,tableName_1,self.fname)
        
        else:            
          sql = """INSERT INTO %s (ID, %s) VALUES ("%s", '%s') ON DUPLICATE KEY UPDATE %s = '%s'""" %(tableName,fieldName,self.fname,self.newDict[i],fieldName,self.newDict[i])
          #sql = """UPDATE %s SET %s = %s WHERE ((%s.ID = %s))""" %(tableName,i,self.newDict[i],tableName,self.fname)
        
        self.updateOrInsertIntoDB(sql)
  
  def updateOrInsertIntoDB(self,sql):
    try:
      self.ds.run_sql(sql)
    except:
      print "sql failed: " + sql
      pass
    
    
  def getDictionariesForLinkedTables(self):
    list = ['crystal_colourbase.display','crystal_colourappearance.display','crystal_colourintensity.display','crystal_shape.display','progress_status.display']
      
    self.dictionaryOfTuples = {}
    
    for item in list:
      tablename = item.split(".")[0]
      sql = """SELECT %s.ID, %s FROM %s """ %(tablename, item, tablename)
      return_list = self.ds.run_select_sql_return_list(sql)
      self.dictionaryOfTuples[tablename] = return_list
      
    self.dictionaryOfTuples['progress_status'] = ({'progress_status.ID': '8', 'progress_status.display': 'Rejected'}, 
                                                  {'progress_status.ID': '40', 'progress_status.display': 'Publishing'}, 
                                                  {'progress_status.ID': '30', 'progress_status.display': 'Finishing'}, 
                                                  {'progress_status.ID': '20', 'progress_status.display': 'Solving'}, 
                                                  {'progress_status.ID': '10', 'progress_status.display': 'Collecting'},
                                                  {'progress_status.ID': '51', 'progress_status.display': 'Withdrawn'}, 
                                                  {'progress_status.ID': '25', 'progress_status.display': 'Refining'}, 
                                                  {'progress_status.ID': '15', 'progress_status.display': 'Reduction'}, 
                                                  {'progress_status.ID': '1', 'progress_status.display': 'Aborted'}, 
                                                  {'progress_status.ID': '2', 'progress_status.display': 'Finished'}, 
                                                  {'progress_status.ID': '3', 'progress_status.display': 'Do You Know?'}, 
                                                  {'progress_status.ID': '4', 'progress_status.display': 'Lost'}, 
                                                  {'progress_status.ID': '5', 'progress_status.display': 'Processing'}, 
                                                  {'progress_status.ID': '6', 'progress_status.display': 'Published'}, 
                                                  {'progress_status.ID': '7', 'progress_status.display': 'Pending'}, 
                                                  {'progress_status.ID': '9', 'progress_status.display': 'In Queue'}, 
                                                  {'progress_status.ID': '0', 'progress_status.display': 'No Entry'}, 
                                                  {'progress_status.ID': '46', 'progress_status.display': 'Published Duplicate'},
                                                  {'progress_status.ID': '47', 'progress_status.display': 'Known structure'}
                                                )
    
  def compareUpdateDimasFileModificationWithDatabaseTimestamps(self):
    self.getTimeUpdateDimasFileLastModified()
    self.getTimestampsFromDB()
    
    mostRecentTimestamp = max(self.timestamp)
    
    if self.modified > mostRecentTimestamp:
      print "The update file has been modified for %s" %self.fname
      return True
    
    else:
      #print "The update file has not been modified for %s" %self.fname
      return False
    
  def getTimeUpdateDimasFileLastModified(self):
    self.modified = None
    if os.path.exists(self.filePath):
      self.modified = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.path.getmtime(self.filePath)))
    else:
      print "The path %s does not exist" %self.filePath
    
  def getTimestampsFromDB(self):
    tuple = ("submission", "crystal", "diffraction", "refinement", "progress", "reference", "diffraction_cell")
    self.timestamp = []
    for item in tuple:
      try:
        dictionary = self.ds.run_select_sql("""SELECT Timestamp FROM %s WHERE ID = "%s";""" %(item,self.fname))
        self.timestamp.append(dictionary[0]['Timestamp'])
      except:
        pass


if __name__ == '__main__':
  a = AutoUpdateDimasDB(dir=r"Y:",database='DimasDB',types=['cif','hkl','p4p','prp','res','doc'])
  a.run()