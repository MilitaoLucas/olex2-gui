## Script (Python) "pull_numbers_translation"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=table='translationtype', items='translation', language='Spanish'
##title=
##
# pull_numbers_translation.py:

from Products.PythonScripts.standard import html_quote
request = container.REQUEST
RESPONSE =  request.RESPONSE
#table = "category"
#items = "commands"

sqlQ = "SELECT * from %s" %table
rs = context.sql(Qstring=sqlQ)
entries = {}
for entry in rs:
  entries.setdefault((entry[1], entry[0]))
totalcount = 0
i = 0



sqlQ = """
SELECT count( * ) as total_record
FROM %s WHERE %s Like '';
""" %("translation", language)

#print sqlQ
#return printed
rs = context.sql(Qstring=sqlQ)
for bit in rs:
  i += 1

  t = r'''
<td width="150" bgcolor="#efefef">
<a href="list_table_items?catID=0&entry=0&table=translationtype&itemss=translation&language=%s">%s (%s)</a></td>
''' %( language, "<font color='red'>Not Assigned</font>",  bit[0],)
  print '<table><tr>'
  print t


for entry, catID in entries:
  sqlQ = """
SELECT count( * ) as total_record
FROM %s INNER JOIN %s ON %s.%sID = %s.ID
WHERE (((%s.Name) Like '%s')); """ %(table, items, items, table, table, table, entry)
  rs = context.sql(Qstring=sqlQ)
  for bit in rs:
    i += 1
    t = r'''
<td width="120" bgcolor="#efefef">
<a href=list_table_items?catID=%s&entry=%s&table=%s&itemss=%s&language=%s>%s (%s)</a></td>
''' %(catID, entry,  table, items, language, entry,  bit[0],)
    print t
    if i == 5:
      print '</tr><tr>'
      i = 0
    totalcount += bit[0]
    
t = r'''
<td width="120"  bgcolor="#efefef">
<a href=list_tables_items?catID=&entry=%s&table=%s&itemss=%s&language=%s>All (%i)</a>
''' %(entry,  table, items, language, totalcount )
print t
print "</td></tr></table>"

return printed
