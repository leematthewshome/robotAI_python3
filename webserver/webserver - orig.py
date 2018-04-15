from flask import Flask
from flask import render_template
from flask import request
import os
import sqlite3

websrvApp = Flask(__name__)

TOPDIR = '/home/pi/robotAI/'
HOTWORD_PATH = '/home/pi/robotAI/static/hotwords/'


@websrvApp.route('/')
@websrvApp.route('/index')
@websrvApp.route('/index.html')
def index():
    return render_template('index.html')



@websrvApp.route('/config.html')
def config():
    #determine what category are we looking at
    thisCat = request.args.get('cat')
    if thisCat is None:
        thisCat = 'General'
    #connect to config database
    filename = os.path.join(TOPDIR, "static/sqlite/robotAI.sqlite")
    try:
        con = sqlite3.connect(filename)
        cur = con.cursor()
    except:
        return "Error. Could not connect to configuration database"
        
    #get list of config categories for menu
    SQL = "SELECT DISTINCT category FROM ConfigValues"
    cur.execute(SQL)
    rows = cur.fetchall()
    if not rows:
        return "Error. No rows found in table ConfigValues"
    catMenu = "<DIV class='header'>"
    catMenu += "<table border=0 width='100%'><tr>"
    for row in rows:
        catMenu += "<td class='menu'>&nbsp<a href='config.html?cat=%s'>%s</a></td>" % (str(row[0]), str(row[0]))
    catMenu += "</tr></table>"
    catMenu += "</DIV>"

    #build list of form items for selected category
    fieldLst = ""
    SQL = "SELECT label, code, value, type FROM ConfigValues WHERE category = '%s' order by code" % (thisCat)
    cur.execute(SQL)
    rows = cur.fetchall()
    if not rows:
        return "Error. No rows found in table ConfigValues"
    fieldLst += "<FORM action='config_save.html?cat=%s' method='POST'>" % (thisCat)
    fieldLst += "<table border=0 width='100%'>"
    for row in rows:
        label = row[0]
        code = row[1]
        value = row[2]
        type = row[3]
        fieldLst += "<tr><td width='200px'>%s</td><td>&nbsp</td><td>" % (label)
        # render 'list' field types using a dropdown listbox
        if type=="list":
            fieldLst += "<select class='config' name ='%s'>" % (code)
            SQL = "SELECT value FROM ListValues WHERE category='%s' AND code='%s'" % (thisCat, code)
            cur.execute(SQL)
            vals = cur.fetchall()
            for val in vals:
                iVal = val[0]
                if iVal == value:
                    fieldLst += "<option value='%s' SELECTED>%s</option>" % (iVal, iVal)
                else:
                    fieldLst += "<option value='%s'>%s</option>" % (iVal, iVal)
            fieldLst += "</select>"
		# render 'binary' field types in the list as a TRUE or FALSE dropdown
        elif type=="binary":
            fieldLst += "<select class='config' name='%s'>" % (code)
            if value=="TRUE":
                fieldLst += "<option value='TRUE' SELECTED>TRUE</option>"
                fieldLst += "<option value='FALSE'>FALSE</option>"
            else:
                fieldLst += "<option value='TRUE'>TRUE</option>"
                fieldLst += "<option value='FALSE' SELECTED>FALSE</option>"
            fieldLst += "</select>"
        # render 'display' field types in the list as non-editble values
        elif type=="display":
            fieldLst += value
        # render everything else as a simple text field
        else:
            fieldLst += "<input type='text' class='config' name='%s' value='%s'>" % (code, value)
        fieldLst += "</td></tr>"
    fieldLst += "</table>"
    
    con.close()
    return render_template('config.html', header=catMenu, body=fieldLst)

    
@websrvApp.route('/config_save.html', methods=['GET', 'POST'])
def config_save():
    message = ""
    thisCat = request.args.get("cat")
    filename = os.path.join(TOPDIR, "static/sqlite/robotAI.sqlite")
    try:
        con = sqlite3.connect(filename)
        cur = con.cursor()
    except:
        return "Error. Could not connect to configuration database"
    #loop through each posted value and update config database
    for key, value in request.form.items():
        SQL = "UPDATE ConfigValues SET value = '%s' WHERE code='%s' and category='%s'" % (value, key, thisCat)
        try:
            cur.execute(SQL)
            con.commit()
        except sqlite3.Error as e:
            message += ("<h6>Database error: %s </h6>" % e)
            break
        except Exception as e:
            message += ("<h6>Exception in _query: %s </h6>" % e)    
            break            
    #if no errors then set success message
    if message=="":
        message = "<h6>Configuration Updated.<br><br>You should restart to robotAI engine for changes to take effect.</h6>"
    #close connection and return results
    con.close()
    return render_template('config_save.html', message=message)

    
@websrvApp.route('/contacts.html')
def contacts():
    #get variables passed to the page (if any)
    first = request.args.get("first")
    last = request.args.get("last")
    mode = 'list'
    if first is not None or last is not None:
        mode = 'edit'
    #initialise all variables used in the logic of the page
    thisHTML = ''
    formHTML = ''
    if first is None:
        first = ''
    if last is None:
        last = ''
    email = ''
    mobile = ''
    softPhone = ''
    whiteList = ''
    white_true = ''
    white_false = 'selected'
    #connect to database to fetch contacts
    filename = os.path.join(TOPDIR, "static/sqlite/robotAI.sqlite")
    try:
        con = sqlite3.connect(filename)
        cur = con.cursor()
    except:
        return "Error. Could not connect to configuration database"

    #If we dont have a record to edit then display the list
    if mode == 'list':
        SQL = "SELECT FirstName, LastName, Email, Mobile, SoftPhone FROM Contacts"
        cur.execute(SQL)
        rows = cur.fetchall()
        if len(rows) == 0:
            thisHTML += "<table class='u-full-width'><thead><tr><th>&nbsp</th></tr></thead>"
            thisHTML += "<tbody><tr height='200px' align='center'>"
            thisHTML += "<td style='text-align:center; ' colspan='100%'>No contacts have been created yet.</td>"
            thisHTML += "</tr></tbody></table>"
        else:
            thisHTML += "<table class='u-full-width'>"
            thisHTML += "<thead><tr><th>First Name</th><th>Last Name</th><th>Email</th><th>Mobile</th><th>Soft Phone</th><th></th></tr></thead>"
            for row in rows:
                thisHTML += "<tr>";
                thisHTML += "<td>" + row[0] + "</a></td>"
                thisHTML += "<td>" + row[1] + "</td>"
                thisHTML += "<td>" + row[2] + "</td>"
                thisHTML += "<td>" + row[3] + "</td>"
                thisHTML += "<td>" + row[4] + "</td>"
                thisHTML += "<td><button class='button' onClick='editItem(\"" + row[0] + "\", \"" + row[1] + "\")'>Edit</button></td>"
                thisHTML += "</tr>"
            thisHTML += "</tbody>"
            thisHTML += "</table>"
    else:
        #we must have a record to edit to go and get it
        SQL = "SELECT FirstName, LastName, Email, Mobile, SoftPhone, WhiteList FROM Contacts where FirstName='%s' and LastName='%s'" % (first, last)
        cur.execute(SQL)
        rows = cur.fetchall()
        email = rows[0][2]
        mobile = rows[0][3]
        softPhone = rows[0][4]
        whiteList = rows[0][5]
        if whiteList == 'TRUE':
            white_true = 'selected'
            white_false = ''

    formHTML += '<table border="0" >'
    formHTML += '<tr><td nowrap>First Name &nbsp</td><td><input type="text" name="frmFirstName" id="frmFirstName" style="width:150pt" style="width:100pt" value="%s"></td></tr>' % (first)
    formHTML += '<tr><td nowrap>Last Name &nbsp</td><td><input type="text" name="frmLastName" id="frmLastName" style="width:150pt;" value="%s"></td></tr>' % (last)
    formHTML += '<tr><td nowrap>Mobile &nbsp</td><td><input type="text" name="frmMobile" id="frmMobile" style="width:150pt;" value="%s"></td></tr>' % (mobile)
    formHTML += '<tr><td nowrap>Email &nbsp</td><td><input type="text" name="frmEmail" id="frmEmail" style="width:250pt;" value="%s"></td></tr>' % (email)
    formHTML += '<tr><td nowrap>Soft Phone &nbsp</td><td><input type="text" name="frmSoftPhone" id="frmSoftPhone" style="width:250pt;" value="%s"></td></tr>' % (softPhone)
    formHTML += '<tr><td nowrap>White List &nbsp</td><td><select name="frmWhiteList" id="frmWhiteList" style="width:70pt;" >'
    formHTML += '<option value="TRUE" %s >TRUE</option>' % (white_true)
    formHTML += '<option value="FALSE" %s >FALSE</option>' % (white_false)
    formHTML += '</select></td></tr></table>'

    con.close()
    return render_template('contacts.html', body=thisHTML, form=formHTML)



    
@websrvApp.route('/', defaults={'path': ''})
@websrvApp.route('/<path:path>')
def catch_all(path):
    return render_template(path)

# ==========================================================================
# Run the webserver
# ==========================================================================
if __name__ == "__main__":
    websrvApp.run(host= '0.0.0.0', debug=True)
    
