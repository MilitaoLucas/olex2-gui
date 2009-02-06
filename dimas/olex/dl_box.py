## Script (Python) "dl_box"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=ID, topic, fields='*', mode="display", br="all", sol="", filter="", catID="", dbentrydisplay=""
##title=
##
## Warnings:
##  Prints, but never reads 'printed' variable.
##  Prints, but never reads 'printed' variable.
##
# dl_box.py

from Products.PythonScripts.standard import html_quote
request = container.REQUEST
RESPONSE =  request.RESPONSE
url = context.REQUEST.URL
from DateTime import DateTime
now = DateTime()
userRight = []
m = mode.split("_")
debug = False

try:
    mode = m[0]
    newtype=m[1]
except:
    pass

def get_PID():
    membership_tool=context.portal_membership
    member = membership_tool.getAuthenticatedMember()
    PID = member.PID
    return PID

def getUserStatus(ID):
    permissions = []
    Q="SELECT AccountID, SubmitterID, OperatorID FROM submission WHERE ID = '%s'" %ID
    result = context.sql(Qstring=Q)
    for item in result:
        if item.AccountID == PID:
            permissions.append("Account")
        if item.SubmitterID == PID:
            permissions.append("Submitter")
        if item.OperatorID == PID:
            permissions.append("Operator")
    return permissions
    

def get_translate_dict():
    d = {'categoryID': ('Category 1', (60,1)),\
    'secondaryCategoryID': ('Category 2', (60,1)),\
    'Related': ('Related Commands', (40,1)),\
    'typeID': ('Command Type', (60,1)),\
    'Standard_Help': ('Standard_Help', (120,4)),\
    'Basic_Help': ('Basic_Help', (120,2)),\
    'Definition': ('Definition', (120,4)),\
                      }
    
    translate_dict = {}
    size_dict = {}
    for item in d:
        translate_dict.setdefault(item, d[item][0])
        size_dict.setdefault(item, d[item][1])
    return translate_dict, size_dict

exclude_list = ['Timestamp', 'Parameters', 'Cmd', 'Display', 'imagesID', 'Builtin_Description',]
hidden_list = ['last_modified_by', 'last_modified_on']
unmodifiable_list = ['Builtin_Description', ]
special_list = []
sudo_list = [0, 240, 27]

if mode == "edit":
    exclude_list.append('Timestamp')
#if mode == "new":
#    exclude_list.append('Smiles')

translate_dict, size_dict = get_translate_dict()


size_d = size_dict



people_list = ['Account', 'Submitter', 'Operator']

def date_chooser(field, value):
    years = ['--year', 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006]
    #months = [(None, None)('January',1), ('February',2) 'March':3, 'April':4, 'May':5, 'June':6, 'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}
    months = [('--month', None), ('January',1), ('February',2), ('March',3), ('April',4), ('May',5), ('June',6), ('July',7), ('August',8), ('September',9), ('October',10), ('November',11), ('December',12)]
    days = ['--day',1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]

    #return value

    if value:
        sel_day = value.day()
        sel_month = value.month()
        sel_year = value.year()
    else:
        sel_day = '--year'
        sel_month = '--month'
        sel_year = '--day'

    date_box = '<span><select name="%s_day">' %(field)
    for item in days:
        display = item
        id = item
        if id == sel_day:
            date_box += '<option selected value="%s">%s' %(sel_day,  sel_day)
        else:
            date_box += '<option value="%s">%s' %(id, display)
    date_box += '</select>'    

    date_box += '<select name="%s_month">' %(field)
    for item in months:
        display = item[0]
        id = item[1]
        #id = item
        if id == sel_month:
            date_box += '<option selected value="%s">%s' %(sel_month,  display)
        else:
            date_box += '<option value="%s">%s' %(id, display)
    date_box += '</select>'    

    date_box += '<select name="%s_year">' %(field)
    for item in years:
        display = item
        id = item
        if id == sel_year:
            date_box += '<option selected value="%s">%s' %(sel_year,  sel_year)
        else:
            date_box += '<option value="%s">%s' %(id, display)
    date_box += '</select>'    
    date_box += '</span>'

    return date_box

def submitter_chooser(nick="hp"):
    Q = "SELECT id FROM people_status WHERE nickname like '%s'" %nick
    result = context.sql(Qstring=Q)
    if result:
        for item in result:
            submitter = item[0]
            if not submitter:
                submitter = None
    else:
        submitter = None
    return submitter


def listToTick(field, label, value):
    retval = "<b>%s%s: %s</b>" %(Al, label, Zl)

    if mode == 'display':
        a = Al
        if not value:
            value = "None"
        if field == "ListToxicities" or field == "ListSensitivities":
            a = A2
        retval += "<b>%s%s%s</b>" %(a, value, Z)
        return retval

    else:
        enabled = "enabled"
        

    if field == "ListToxicities":
        val = "harmful, toxic, very toxic, explosive"
    elif field == "ListSensitivities":
        val = "air, water, light"
    elif field == "ListReason":
        val = "connectivity study, full analysis"
    elif field == "ListType":
        val = "standard X-Ray, charge density, neutron"
    elif field == "ListPreviousAnalyses":
        val = "NMR, CHN, MS"
    elif field == "ListReasons":
        val = "Confirm Connectivty, Obtain Structural Details"


    oval = value.split(",")
    v = val.split(",")
    values = []
    for item in v:
        values.append(item)
    for item in oval:
        if item not in v:
            values.append(item)
    
    for item in values:
        if not item:
            continue
        if debug: print "'%s'" %item
        checked = ''
        if item in oval:
            checked = 'checked'
        retval+= '%s%s%s<input type="checkbox" name="%s_%s" %s %s/> ' %(Al, item, Zl, field, item, checked, enabled)

    retval+= '%s%s%s <input type="text" name="%s_%s" value="" size="20"/> ' %(Al, "other", Zl, field, "other")
    retval += Z
    return retval


def create_list_table(dlListAdd_l):
    if topic == "submission":
        listCol = 8
    else:
        listCol = 4
    width = (100/listCol)
    tab = '<table><td width="%.0f%%" valign="top">' %width
    j = len(dlListAdd_l)
    perCol = int(j/listCol) +1
    perCol = [perCol, perCol*2, perCol*3, perCol*4, perCol*5, perCol*6, perCol*7, perCol*8]
    i=0
    for item in dlListAdd_l:
        i+=1
        if not item:
            item = '<font color="blue">This item is VERY strangely NONE</font>'
        else:
            tab+= "%s<br>" %item
        if i in perCol:
            tab += '</td><td width="%.0f%%" valign="top">' %width
    tab += r'</td></colgroup></table>'
    return tab

def getLookupFields(field, value, alias, label):
    ## These are the lookup fields: They should all end in 'ID' in the DB  ------------- LOOKUP
    field = field[:-2]
    dlAdd = '<font color="red"><b>This should not be seen and %s in  getLookupFields is to blame</b></font>' %field    #These are the COLOUR fields. They should all begin with 'Colour' in the DB  --- COLOUR
    if field[:6] == "Colour":
        field = field.split("Colour")[1]
        #lookup = string.lower("crystal_colour%s" %(field))
        lookup = ("crystal_Colour%s" %(field))
        if mode == "display":
            result = context.select_display(ID=value, table=lookup)
        else:
            result = context.select_box(lookup, value, 10)
        if field == 'Base':
            dlAdd = "%s%s%s" %(A, result, Z)
        elif field == 'Appearance':
            dlAdd = "%s%s%s%s " %(label, A, result, Z)
        elif field == 'Intensity':
            dlAdd = "%s%s%s " %(A, result, Z)

    #These are the PEOPLE fields. --------------------------------------------------- PEOPLE
    elif field in people_list:
        if mode == "display":
            if value:
                value = context.person_with_link(value)
            else:
                value = "None"
        else:
            if PID not in sudo_list: #This will enable the drop-down menu for submitter
                if mode == 'new' and field == "Submitter":
                    value = context.select_display(ID=value, table="people_fullnames")
                elif mode == 'new' and field == "Account":
                    value = context.select_display(ID=value, table="people_fullnames")
                elif mode == 'new' and field == "Operator":
                    lookup = field.split("ID")[0]
                    value = context.select_people_box(lookup, value, 30)
            else:
                lookup = field.split("ID")[0]
                value = context.select_people_box(lookup, value, 30)
        dlAdd = "%s%s%s%s" %(label, A , value, Z)


    #These are the FILE fields. They should all begin with '-------------------------  FILES
    elif field[:4] == "data":
    
        if field == "data_Marvin":
            if value and value != "None":
                dlAdd = 'Marvin val<input type="text" name="marvin" value=%s size="30"/>' %value 
                #dlAdd = 'm<textarea rows="3" cols="60" name="marvin" value=%s></textarea>' %value 
            else:
                dlAdd = 'Marvin NoVal<input type="text" name="marvin" value="None" size="30"/>'
                #dlAdd = 'M<textarea rows="3" cols="60" name="marvin" value=%s></textarea>' %value 


        else:
            lookup = string.lower("%s_data" %(topic))
            field = field.split("_")[1]
            dlAdd = '<a href="../display/display_file?ID=%s&table=%s&field=%s">%s</a>' %(ID, lookup, field, field)

        
        
    #These are the other lookup fields  ---------------------------------------------- OTHER
    else:    
        #lookup = string.lower("%s_%s" %(topic, field))
        lookup = ("%s_%s" %(topic, field))
        lookup = ("%s" %(field))
        if mode == "display":
            result = context.select_display(ID=value, table=lookup)
        else:
            result = context.select_box(lookup, value, 10)
        dlAdd = '%s%s%s%s' %(label,  A, result, Z)
    return dlAdd

def getSpecialFields(field, value, alias, label):
    dlAdd = '<font color="red"><b>This should not be seen and %s in  getSpecialFields is to blame</b></font>' %field
    # These are the DATE fields. They should all begin with 'Date' in the DB   ---------  DATES
    if field[:4] == "List":
        dlAdd = listToTick(field, alias, value)

    elif field == "Smiles":
        if value and value != "None":
            dlAdd = '<input type="hidden" name="Smiles" value=%s size="10"/>' %value 

        else:
            dlAdd = '<input type="hidden" name="Smiles" value="None" size="10"/>'

    elif field == "Marvin":
        if value and value != "None":
            dlAdd = '<input type="hidden" name="Marvin" value=%s' %value 
            #dlAdd = 'm<textarea rows="3" cols="60" name="Marvin" value=%s></textarea>' %value 
        else:
            dlAdd = '<input type="hidden" name="Marvin" value="None"'
            #dlAdd = 'M<textarea rows="3" cols="60" name="Marvin" value=%s></textarea>' %value 

      
      
    elif field[:4] == "Date":
        if PID in sudo_list:
            value = date_chooser(field, value)
            dlAdd = '%s%s%s%s' %(label, A, value, Z)
            return dlAdd
        
        if field == "DateSubmission" and mode != 'display':
            dlAdd = "NoShow"
            return dlAdd
        if value:
            local_value = context.toLocalizedTime(value,long_format=0)
        if mode == "edit" and field != 'DateSubmitted':
            value = date_chooser(field, value)
        elif mode == "new":
            value = local_value
        elif mode == "display":
            if value:
                value = local_value
            else:
                value = ""
        dlAdd = '%s%s%s%s' %(label, A, value, Z)
        if mode == "new":
            dlAdd = "NoShow"

    elif field[:2] == "Is":
        if mode == "edit" or mode == "new":
            value = '<input type="checkbox" name="%s" checked ="%s" />' %(field, value)
        elif mode == "display":
            value = '<input type="checkbox" name="%s" checked ="%s" disabled />' %(field, value)
        dlAdd = '%s%s%s%s' %(label, A, value, Z)


    # These are CHEMICAL FORMULA fields. They should all begin with 'Formula'  -------- FORMULA
    elif field[:7] == "Formula":
        alias = field[7:]
        dlAdd += '%s: <b>%s</b>' %(alias, value )
        if mode == 'display':
            if value:
                value = context.display_formula(value)
            else:
                value = ""
        elif mode == "list":
            if value:
                value = context.display_formula(value)
                value = '<font size="1">%s</font>' %value
            else:
                value = ""
        elif mode == 'edit' or mode == 'new':
            value = '<input type="text" name="%s" value="%s" size="%s" />' %(field, value, 30)
        dlAdd = '%s%s%s%s' %(label, A, value, Z)

    # These are the SIZE fields. They should all begin with 'SIZE' in the DB   ----------  SIZE
    elif field[:4] == "Size":
        f = field.split("Size")
        a = A
        z = Z
        if value:
            value = "%.2f" %float(value)
        if mode == "edit" or mode == "new":
            value = '<input type="text" name="%s" value="%s" size="%s" />' %(field, value, 6)
            a = ""
            z = ""
        if f[1] == 'Min':
            dlAdd = '%s%s%s%s x ' %(label, a, value, z)
        elif f[1] == 'Max':
            dlAdd = '%s%s%s mm<sup>3</sup>' %(a, value, z)
        else:
            dlAdd = '%s%s%s x ' %(a, value, z)

    # These are the MELTING POINT fields.  -------------------------------------   MELTING POINT
    elif field[:12] == "MeltingPoint":
        f = field.split("MeltingPoint_")
        if value != "None":
            try:
                value = "%.0f" %(float(value))
            except:
                value = ""
        if f[1] == '1':
            if mode == 'edit' or mode == "new":
                value = '<input type="text" name="%s" value="%s" size="%s" />' %("MeltingPoint_1", value, 5)
            dlAdd = '%s%s%s%s - ' %(label, A, value, Z)
        elif f[1] == '3':
            if mode == 'edit' or mode == "new":
                value = '<input type="text" name="%s" value="%s" size="%s" />' %("MeltingPoint_3", value, 5)
            dlAdd = '%s%s%s <B>&deg;C</b>' %(A, value, Z) 
        else:
            if mode == 'edit'  or mode == "new":
                value = '<input type="text" name="%s" value="%s" size="%s" />' %("MeltingPoint_2", value, 5)
            dlAdd = '%s%s%s - ' %(A, value, Z)  
 
    elif field[:7] == "Comment":
        if field in translate_dict:
            alias = translate_dict[field]
        else:
            alias = field
        if mode == "edit" or mode == "new":
            dlAdd = '%s: <textarea rows="1" cols="60" name="%s">%s </textarea><br>'%(alias, field, str(value))
        else:
            dlAdd = '%s%s%s%s'%(label, A, str(value), Z)

    return dlAdd

def getIDFields(value, topic):
    dlAdd = '<font color="red"><b>This should not be seen and %s in  getIDFields is to blame</b></font>' %field    
    if topic == "people_status":
        value = context.person_with_link(value)
        dlAdd = "%s%s%s" %(A , value, Z)
    elif topic == "progress":
        str = '<a style="text-decoration:none" href="../structures/structures_tem?ID=%s"><b>%s</b></a>' %(value, value)
        dlAdd = "%s%s%s" %(A , str, Z)
    elif topic == "submission":
        str = '<a style="text-decoration:none" href="../structures/structures_tem?ID=%s"><b>%s</b></a>' %(value, value)
        dlAdd = "%s%s%s" %(A , str, Z)
    else:
        dlAdd = ""
    return dlAdd
    dlToAdd += create_display_dl(dlAdd_l)

def createDisplayDl(dl_add_l, br):
    dlToAdd = ""
    fcount = 0
    fround = 0
    for item in dlAdd_l:
        item = doUnicode(item)
        if item == "NoShow":
            continue

        fcount += 1
        #print "fcount: %s, fround: %s, %s<br>" %(fcount, fround, field)
        if not item:
            item = '<font color="blue">This item is strangely NONE</font>'
        dlToAdd += item
        try:
            c = int(br[fround])
        except:
            br = "all"
        if br == "all":
            dlToAdd += '<br>'
        elif fcount == int(br[fround]):
            dlToAdd += '<br>'
            fcount = 0
            fround += 1        
        else:
            dlToAdd += '  '
    dlToAdd = doUnicode(dlToAdd)
    return dlToAdd

def get_subtable(fields):
    subtable = []
    subfield = []
    nfields = ""
    fields = fields.split(",")
    for field in fields:
        f = field.split(".")
        if len(f) > 1:
            subtable.append(f[0])
            subfield.append(f[1])
        else:
            nfields+= "%s, " % field
    fields = nfields[:-2]
    return fields, subtable, subfield


def loop_result(result):
    subkey = ID
    for item in result:
        i = 0
        for field in l:
            i += 1

            ## Exclude items listed in the exclude_list  ------------------------------   EXCLUDE TERMS
            if field in exclude_list:
                dlAdd = ""
                continue
            
            if field == "ID" and mode != "list":
                dlAdd = ""
                continue
            
            value=getattr(item, field)
            if mode != "display":
                if not value:
                    value = ""
                if value == 0:
                    value = ""

            if field in translate_dict:
                alias = translate_dict[field]
            else:
                alias = field
            
            if not listing:
                label = "%s%s%s: " %(Al, alias, Zl)
            else: label = ""
            
            if len(field) > 3 and field[-2:] == "ID":
                dlAdd = getLookupFields(field, value, alias, label)
            
            elif field == "ID":
                dlAdd = getIDFields(value, topic) 
                subkey = value
            elif field in s_list:
                dlAdd = getSpecialFields(field, value, alias, label)
            
            else:
                if mode == "edit" or mode == "new":
                    if field in unmodifiable_list:
                        dlAdd = '%s%s' %(label,str(value)) 
                    elif field in hidden_list:
                        dlAdd = '<input type="hidden" name="%s" value="%s">'%(field, value)
                    else:
                        s = size_d.get(field, (80,2))
                        try:
                            height = int(s[1])
                            size = int(s[0])
                            if size > 60: label += '<br>'
                            dlAdd = '%s<textarea rows="%i" cols="%i" name="%s">%s</textarea>' %(label, height, size,field,str(value)) 
                        except:
                            size = s
                            #dlAdd = 'Beee %s<input type="text" name="%s" value="%s" size=%i><br>'%(label, field, str(value), size )
                            dlAdd = '%s<textarea rows="%i" cols="%i" name="%s">%s</textarea>' %(label, height, size,field,str(value)) 

                else:
                    #dlAdd = '%s%s%s%s'%(label, A, str(value), Z)
                    dlAdd = 'Buuu %s<textarea rows="%i" cols="%i" name="%s" value=%s></textarea>' %(label, height, size,field,str(value)) 

            dlAdd_l.append(dlAdd)
    return dlAdd_l, subkey


def doUnicode(str):
    try:
        str = unicode(str, "utf-8")
    except:
        str = str
    return str

# ####################################################################################################################
# ####################################################################################################################
# ####################################################################################################################

#PID = get_PID()
#permissions = getUserStatus(ID)
#return permissions

if br != "all":
    br = br.split("_")

try:
    t = topic.split(".")
    table = "%s_%s" %(t[0], t[1])
    topic = t[1]
except:
    table = topic


fields, subtable, subfield = get_subtable(fields)

Q="SELECT %s FROM %s WHERE ID = '%s'" %(fields, table, ID)
if filter:
    f = filter.split(".")
    field = f[0]
    condition = f[1]
    if debug: print "Condition = %s" %condition
    try:
        isnot = condition.split("NOT:")[1]
        conditionSQL = "AND %s NOT LIKE '%s'" %(field, isnot)
        if debug: print "ISnot is set to '%s'" %conditionSQL
    except:
        conditionSQL = ""
        if debug: print "ISnot is set to '%s'" %conditionSQL

    Q="SELECT %s FROM %s WHERE ID = '%s' %s" %(fields, table, ID, conditionSQL)
    if debug: print
    if debug: print Q

listing = False
m = mode.split(".")
if len(m) > 1:
    mode = m[0]
    filter = m[1]
    Q="SELECT %s FROM %s WHERE %s = '%s'" %(fields, table, filter, ID)
    listing = True 


dlAdd_l = []
result = context.sql(Qstring=Q)

#return sNum
    
dlListAdd_l = []
dlAdd = '<font color="red"><b>"This should never be seen"</b></font>'
dlListAdd = '<font color="red"><b>"This should never be seen"</b></font>'
dlToAdd = '<input type="hidden" name="%s" value="%s">'%('ID', ID)
dlToAdd = '<input type="hidden" name="%s" value="%s">'%('table', topic)

if not result:
    if table == "people_status":
        return ""
    else:
        dlToAdd += ('<font color="red"><b>No record found for:</b></font><br>%s<p>' %Q)

A = '<B>'
Z = '</B>'
Al = '<font color="#35649E">'
A2 = '<font color="red">'
Zl = '</font>'
box_size = 5
l = result.names()
perCol = 2
listCol = 1
s_list = []
dl_add = ""



for field in l:
    for item in special_list:
        if len(field.split(item)) > 1:
            #print "%s:%s<br>" %(item, field)
            s_list.append(field)

dlAdd_l, subkey = loop_result(result)

dlToAdd = ""
if mode == "edit" or mode == "new":
    dlToAdd += '<input type="hidden" name="ID" value=%s size="20">' %ID
    dlToAdd += '<input type="hidden" name="table" value=%s size="20">' %topic
    #dlToAdd += '<input type="hidden" name="catID" value=%s size="20">' %catID
    #dlToAdd += '<input type="hidden" name="dbentrydisplay" value=%s size="20">' %dbentrydisplay
#if table == "submission":
#    dlToAdd = '<input type="text" name="%s" value="%s">'%('ID', ID)
#dlToAdd += '<input type="hidden" name="sNum" value=%s size="20">' %ID

br = doUnicode(br)
dlToAdd = doUnicode(dlToAdd)
#dlAdd_l = doUnicode(dlAdd_l)


if mode != 'list':
    dlToAdd += createDisplayDl(dlAdd_l, br)
else:
    dlToAdd += create_list_table(dlAdd_l)

#print permissions
#print topic
#return printed

editlink = ""
if mode == "display":
    submitteredit = ["submission", "crystal"]
    if topic in submitteredit:
        if not permissions:
            edit_topic = ""
            editlink = ""

    operatoredit = ["progress", "diffraction", "reference", "refinement"]
    if topic in operatoredit:
        if "Operator" not in permissions:
            edit_topic = ""
            editlink = ""
    else:
        edit_topic = '%s/edit_%s?ID=%s&table=%s' %(topic, topic, ID, table)
        editlink = "<a href=%s><img src=%s></a>" %(edit_topic, '../portal_skins/plone_images/edit.gif')
else:
    editlink = ""


dlHeader = '<span><dl id="%s" class="collapsible %s" inline>\
            <dt class="collapsibleHeader">%s</dt>\
                <dd class="collapsibleContent">\
                <table>\
                <tr>' %(topic, sol, topic)

edtLink = '<td>%s</td>' %editlink

dlBody = '<td>%s</td>' %dlToAdd

dlFooter = '   </tr>\
                </table>\
                </dd>\
            </dl></span>'

#dlHeader = unicode(dlHeader, "utf-8")
#edtLink = unicode(dlBody, "utf-8")
dlFooter = unicode(dlFooter, "utf-8")

rStr = dlHeader + edtLink + dlBody + dlFooter
#rStr = unicode( rStr, "utf-8" )
return rStr
