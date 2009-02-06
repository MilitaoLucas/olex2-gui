## Script (Python) "get_translation"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=table, items, catID, entry, language
##title=
##
# list_table_items.py:

 
#from Products.PythonScripts.standard import html_quote
#request = container.REQUEST
#RESPONSE =  request.RESPONSE


#from Products.CMFCore.utils import getToolByName 
#translation_service = getToolByName(context, 'translation_service') 
#msg = translation_service.utranslate(domain='PloneXL8', 
                                     #msgid='You have taken ownership of this translation.', 
                                     #default='You have taken ownership of this translation.', 
                                     #context=context) 
#msg = msg.encode('utf-8') 
#print msg
#return printed


debug = False

if debug: print table, items, catID, entry

#table = "category"
#items = "commands"
a = context.portal_membership.getAuthenticatedMember()
if str(a) !="Anonymous User":
  member = True
else:
  member = False

if member:
  edit_topic = 'edit_translation?ID=%s&entry=%s&table=%s&catID=%s&language=%s&OXD=%s' %("0", entry, items, catID, language, '0' )
  newentry = "<b><a href=%s>Create New Entry</a></b>" %(edit_topic)
  print newentry

ID = "NotAssigned"
if catID == '0':
  sqlQ = """
SELECT  * FROM %s WHERE %s Like '';
""" %("translation", language)
  rs = context.sql(Qstring=sqlQ)

else:
  try:
    ID = int(catID)
    IDA = ID
    sqlQ = "SELECT * from %s WHERE %sID=%s" %(items, table, ID)
    rs = context.sql(Qstring=sqlQ)
  except:
    sqlQ = "SELECT * from %s" %(items)
    rs = context.sql(Qstring=sqlQ)
    ID = None
    entry = "All"

if debug: print ID, sqlQ
#return printed

if entry == '0':
  display = "Not Assigned"
else:
  display = entry

#This block switches on the summary view of primary IDs. Not useful if it's only numbers!
print '<h1>%s listed in the category <font color="red">%s</font></h1><p>' %(items, display)
print '<table><tr>'
i = 0
for item in rs:
  display_id = str(item["OXD"]).replace("_", " ")
  if len(display_id) > 30:
    display_id = "%s..." %display_id[:30]
  i += 1
  if ID:
    print '<td bgcolor="#efefef"><a href="list_table_items?catID=%s&entry=%s&table=translation&itemss=%s&language=%s#%s">%s</a></td>' %(ID, entry, items, language, display_id, display_id,)
  if i == 4:
    print '</tr><tr>'
    i = 0
print "</td></tr></table>"

for item in rs:
  display_id = str(item["OXD"]).replace("_", " ")
  if len(display_id) > 30:
    display_id = "%s..." %display_id[:30]

  id = str(item["ID"]).replace(' ', r'%20')
  edit_topic = 'edit_translation?ID=%s&entry=%s&table=%s&catID=%s&language=%s&OXD=%s' %(id, entry, items, catID, language,display_id)
  delete_entry = 'delete_entry?ID=%s&entry=%s&table=%s&catID=%s' %(id, entry, items, catID)
  if member:
    editlink = "<a href=%s><img src=%s></a>" %(edit_topic, '../portal_skins/plone_images/edit.gif')
    editlink +=  "<a href=%s><img src=%s></a>" %(delete_entry, '../portal_skins/plone_images/delete_icon.gif')
  else:
    editlink = ""

  modified_by = item['last_modified_by']
  modified_on = item['last_modified_on']

  print '<br><table>'
  print '<a name="%s"><tr margin-top="20px"><td style="color: red; font-weight: bold">%s%s</td></tr></a>' %(display_id, display_id, editlink)
  if items:
    t = '''<tr bgcolor="#ababab">
<td width="300">English</td>
<td width="300">%s</td>
<td width="100">Modified By</td>
<td width="100">Modified On</td>
</tr>'''%language
    
    language_txt = item[language]
    language_txt = unicode(language_txt, "utf-8" )
    if not language_txt:
        language_txt = '<a href=%s><font color="#ff0000"><b>Please Add!</b></font></a>' %edit_topic
    english = item['English']
    english = unicode(english, "utf-8" )
#    spanish = item['Spanish']
#    spanish = unicode(spanish, "utf-8" )
#    if not spanish:
#        spanish = '<a href=%s><font color="#ff0000"><b>Please Add!</b></font></a>' %edit_topic
#    german = item['German']
#    german = unicode(german, "utf-8" )
#    if not german:
#        german = '<a href=%s><font color="#ff0000"><b>Bitte HinzufÌgen!</b></font></a>' %edit_topic
#    chinese = item['Chinese']
#    chinese = unicode(chinese, "utf-8" )
#    if not chinese:
#        spanish = '<a href=%s><font color="#ff0000"><b>Please Add!</b></font></a>' %edit_topic


    if not modified_by: modified_by = ""
    print t
    t = '''<tr>
<td VALIGN="TOP" width="300" bgcolor="#dedede">%s</td>
<td VALIGN="TOP" width="300" bgcolor="#efefef">%s</td>
<td VALIGN="TOP" width="100" bgcolor="#dedede">%s</td>
<td VALIGN="TOP" width="100" bgcolor="#efefef">%s</td>
</tr>'''%(english, language_txt, modified_by, modified_on)
    #t = context.rs_ext_command(t)
    print t

  print '</table>'
    
    
print "<a href=new_command?cat=%s>New Entry</a>" %entry
return printed
