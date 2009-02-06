# updateDBfromfile.py

#    Requires SQLFactory.py and DBConn.py
#    Finds folders where the file "Dimas 

import os
import time
import re
import SQLFactory

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
  fname = "96srv042"
  path = ""
      
  a = updateDBfromFile(path=path, fname=fname)
  a.main()
  