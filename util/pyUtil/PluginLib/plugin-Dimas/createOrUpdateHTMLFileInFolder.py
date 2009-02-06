# createOrUpdateHTMLFileInFolder.py

#    Requires SQLFactory.py and DBConn.py

#    self.create_and_update_all_HTML_files()
#    1) creates a list of all submission IDs from database
#    2) checks if the ID is valid (starts with two numbers)
#    3) if the folder path exists and html file does not exist: creates html file
#    4) if the html file exists but the databse entry has been changed since the 
#       html file was modified: overwrites old html file with updated html file
#    5) if neither of these are true, prints either "path doesn't exist" or "no change made to html file"

import string
import os
import time
import SQLFactory

class CreateHTMLFileFromInfoInDB(object):
  
  def __init__(self, path="", fname=""):
    self.ds = SQLFactory.SQLFactory(db='DimasDB')
    self.path = path
    self.fname = fname
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
      ID = item['ID']
      if len(ID) >= 6 and len(ID) <=8:
        self.fname = ID
        
        try:
          int(ID[0:2])
          self.fname = ID
          self.getPath()
          
          ## breakpoint to stop at particular file
          #if self.fname == "00asb001":
            #print self.fname
          #else:
            #pass
          
          ##overwrite all files
          #self.createHTMLFile()
          #print "Created HTML file for %s" %self.fname
          
          # update current exisiting files, create new files
          if os.path.exists(self.path) and not os.path.exists(self.filePath):
            self.createHTMLFile()
            self.createdFiles.append(self.fname)
            print "Created HTML file for %s" %self.fname
          elif os.path.exists(self.filePath) and self.compareFileModificationWithDatabaseTimestamps():
            self.createHTMLFile()
            self.updatedFiles.append(self.fname)
            print "Updated HTML file for %s" %self.fname
          elif not os.path.exists(self.path):
            #print "The path %s does not exist" %self.path
            pass
          else:
            #print "No change made to HTML file for %s" %self.fname
            pass
          
        except:
          print "!!!! %s either does not exist or is not a legitamate file name!!!!" %self.fname
          pass
      else:
        pass
      
    return self.createdFiles, self.updatedFiles, self.failed_files
    
  def getPath(self):
    if int(self.fname[0:2]) < 90:
      year = "20" + self.fname[0:2]
    elif int(self.fname[0:2]) >= 90:
      year = "19" + self.fname[0:2]
    
    self.path = "Y:\\%s\\%s" %(year, self.fname)
    self.filePath = "%s\\%s.html" %(self.path,self.fname)
    
  def createHTMLFile(self):
    self.getPath()
    if os.path.exists(self.path):
      self.sqls()
      self.list_all_labels()
      outfile = open(self.filePath, 'w')
      outfile.write("<html>\n<head>\n<title>%s</title>\n</head>\n<body>\n\n" %(self.fname))
      
      number_query_failures = 0
      
      for sql in self.list_sqls:
        i = self.list_sqls.index(sql)
        title = self.list_table_titles[i]
        list_labels = self.listAllLabels[i]
        try:
          self.query(sql)
          self.HTMLtable(outfile, list_labels, title)
        except:
          number_query_failures = number_query_failures + 1
      
      if number_query_failures == 7:
        self.failed_files.append(self.fname)
        print "Number of query failures = 7 for %s" %self.fname
        
      outfile.writelines("</body>\n</html>")
      outfile.close()
    else:
      print "A folder does not exist in the database for %s" %self.fname
    
  def HTMLtable(self, outfile, list_labels, title):
    
    outfile.write("""<h3><u>%s</u></h3>\n<table><COLGROUP span="1" width="300"><COLGROUP span="1">\n""" %title)
    
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
          outfile.write(txt)
      
      except:
        print "broken on HTML %s table, label = %s: %s" %(title,label,self.fname)
      
    outfile.write("</table><br>\n\n")
    
  def query(self, sql):
    
    self.dictionary = self.ds.run_select_sql(sql)[0]
    
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
    self.getPath()
    if os.path.exists(self.filePath):
      self.modified = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.path.getmtime(self.filePath)))
    else:
      print "The path %s does not exist" %self.filePath
    
  def getTimestampsFromDB(self):
    tuple = ("submission", "crystal", "diffraction", "refinement", "progress", "reference", "diffraction_cell")
    self.timestamp = []
    for item in tuple:
      try:
        self.query("""SELECT Timestamp FROM %s WHERE ID = "%s";""" %(item,self.fname))
        self.timestamp.append(self.dictionary['Timestamp'])
      except:
        pass
   
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
    
if __name__ == '__main__':
  path = ""
  fname = "00avc001"
    
  a = createHTMLFileFromInfoInDB(path=path, fname=fname)
  a.main()