## Script (Python) "insert_translation"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=insert_translation
##
# insert.py

from Products.PythonScripts.standard import html_quote

table = context.REQUEST.get('table')

fields = ""
values = ""
update = ""
exclude = ['form.button.submit', 'table']
for item in context.REQUEST.form:
    if item not in exclude:
        fields += "%s," %item
        if item == "last_modified_by":
            value = str(context.portal_membership.getAuthenticatedMember())
        else:
            value = context.REQUEST.get(item)
        if item == "ID":
            ID = value
        values += "'%s'," %value
        update += "%s='%s'," %(item, value)
values = values.strip(",")
values = values.replace("'", "\'")
values = values.replace('"', '\"')
fields = fields.strip(",")
update = update.strip(",")


Q="INSERT INTO %s (%s) VALUES (%s) ON DUPLICATE KEY UPDATE %s;"  %(table, fields, values, update)

#print Q
#return printed
result = context.sql(Qstring=Q)


came_from = "translation#%s" %(ID)
return came_from



url = r"%s/content/translation" %context.portal_url()

return url
