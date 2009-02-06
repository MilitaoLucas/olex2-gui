import DBConn
import MySQLdb

#getDB = DBConn.ChemDBConn()
#conn = getDB.initialise()
#cur = conn.cursor()
#sql = "SELECT * FROM people WHERE ID = '1'"
#cur.execute(sql)
#res = cur.fetchall()
#conn.commit()


import sys
import zlib
import string

class UpdateException:
  def __init__(self, sql_exception): self.sql_exception = sql_exception
  def __str__(self): return "Failure: (SQL exception '%s')" % ((self.sql_exception))


class SQLFactory(object):
  def __init__(self, db='DimasDB'):
    if db == 'OlexGuiDB':
      getDB = DBConn.OlexGuiDBConn()
    elif db == 'DimasDB':
      getDB = DBConn.DimasDBConn()
    elif db == 'DimasDBLocal':
      getDB = DBConn.DimasDBConnLocal()
    else:
      return
      
    self.db, self.conn = getDB.initialise()
    self.cur = self.conn.cursor()

  def escape_characters(self, string):
    '''A general routine to escape caracters that would otherwise interfere with SQL'''
    escaped = {}
    for k,v in value_for_key.iteritems():
      escaped[k] = v.replace(",", "\\,")
      return escaped

  def escape_strings(self, string):
    return DBConn.MySQLdb.escape_string(string)

  def run_sql(self, sql):
    ''' This will run and and commit any sql '''
    #sql = self.escape_strings(sql)
    try:
      cur = self.conn.cursor()
      cur.execute(sql)
      self.conn.commit()
      return "Success"
    
    except Exception, ex:
      print ex

    #except self.conn.IntegrityError, ex:
      #raise UpdateException(ex)

    #except self.conn.OperationalError, ex:
      ##pass
      #raise UpdateException(ex)
    
  def run_select_sql(self, sql, how=1):
    ''' This will run any sql query'''
    try:
      db = self.db
      db.query(sql)
      r = db.store_result()
      rs = r.fetch_row(maxrows=0, how=how)
      return rs
    except:
      return ""
      
   

  def run_select_sql_(self, sql):
    ''' This will run any sql query'''
    res = []
    cur = self.conn.cursor()
    cur.execute(sql)
    res = cur.fetchall()
    return res

  def run_select_sql_return_list(self, sql):
    ''' This will run any sql query'''
    # how = 0
    db = self.db
    db.query(sql)
    r = db.store_result()
    rs = r.fetch_row(maxrows=0, how=2)
    return rs


  def create_insert_or_update_sql(self, value_for_key, table):
    ''' value_for_key is a dictionary with key:value '''
    sql_tmpl = "INSERT %s (%s) VALUES (%s) ON DUPLICATE KEY UPDATE %s" % (
      table,
      ', '.join(value_for_key.iterkeys()),
      ', '.join([ '"%%(%s)s"' % f for f in value_for_key.iterkeys() ]),
      ', '.join(['%s="%%(%s)s"' % (f,f) for f in value_for_key.iterkeys()if not f.startswith('ID')])
      )
    sql = sql_tmpl % value_for_key
    #print sql
    return sql

  def create_insert_sql(self, value_for_key, table):
    ''' value_for_key is a dictionary with key:value '''
    sql_tmpl = "INSERT %s (%s) VALUES (%s)" % (
      table,
      ', '.join(value_for_key.iterkeys()),
      ', '.join([ '"%%(%s)s"' % f for f in value_for_key.iterkeys() ])
      )
    sql = sql_tmpl % value_for_key
    #print sql
    return sql


  def create_update_sql(self, value_for_key, table):
    sql_tmpl = "UPDATE %s SET %s WHERE ID = %s" % (
      table,
      ', '.join(["%s=%%(%s)s" % (f,f) for f in value_for_key.iterkeys()if not f.startswith('ID')]),
      value_for_key['ID']
    )
    sql = sql_tmpl % value_for_key
    #print sql
    return sql
  # commit sql to the database


  def testing(self):
    sql = "SELECT * from people WHERE id = '1'"
    res = self.run_select_sql(sql)
  

if __name__ == "__main__":
  a = SQLFactory()
  a.testing()
