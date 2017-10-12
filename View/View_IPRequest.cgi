#!python

import jinja2
import cgi
import cgitb
import MySQLdb
import datetime
import collections
import os
import socket,struct #FOR inet_aton
import calendar

cgitb.enable();
templates = jinja2.Environment(loader = jinja2.FileSystemLoader(searchpath="templates"))

############
DEBUG_LIST = []
############
##INITIATE DB Connection
with open('pythonmysql.ini','r') as f:
  lines = f.readlines()
  for i, line in enumerate(lines):
    if i == 0:
      host = line[:-1]
    elif i == 1:
      username = line[:-1]
    elif i == 2:
      password = line[:-1]
    elif i == 3:
      socket = line[:-1]

db = MySQLdb.connect(host=host,user=username,passwd=password,db="NMG", unix_socket=sock
et)
cur = db.cursor()

#INITIATE necessary instances
last_DayOfMonth = ''
query_date = ''
disabled_m = "disabled"
disabled_d = "disabled"
result = {}
formatted_month = None
formatted_day = None


#GET Current Sys Time
year = int(datetime.datetime.now().year)
month = int(datetime.datetime.now().month)
day = int(datetime.datetime.now().day)


#GET submitted time
form = cgi.FieldStorage()
form_year = form.getfirst("SearchYear","Year")
form_month = form.getfirst("SearchMonth","Month")
form_day = form.getfirst("SearchDay","Day")
form_submit = form.getfirst("Submit")

if form_year != "Year":
    disabled_m = None
if form_month != "Month":
    disabled_d = None

dateInformation = {
    'Year'      :   form_year,
    'Month'     :   form_month,
    'Day'       :   form_day,
}
#GET last day of month for dropdown
if not disabled_d:
    LastDay = calendar.monthrange(int(form_year),int(form_month))[1]
    dateInformation["LastDay"] = LastDay

#GET Submitted search query
form_submitter = form.getfirst("Submitter",'')
form_region = form.getfirst("Region",'Select')
form_company_name = form.getfirst("CompanyName",'')
form_status = form.getfirst("Status",'Select')

if form_region == 'Select':
  form_region = ''
if form_status == 'Select':
  form_status = ''

formInformation = {
    'Submitter'     :   form_submitter,
    'Region'        :   form_region,
    'Company_Name'  :   form_company_name,
    'Status'        :   form_status,
}

#BUILD query
form_items = formInformation.items()
query = "SELECT * FROM IPReg_Info WHERE 1=1"

if dateInformation['Year'] != 'Year':
  query_date = " AND DATE_FORMAT(Date,'%Y') = '{}'".format(dateInformation['Year'
])
if dateInformation['Month'] != 'Month':
  if int(dateInformation['Month'])<10:
      formatted_month = '0'+dateInformation['Month']
  else:
    formatted_month = dateInformation['Month']
    query_date = " AND DATE_FORMAT(Date,'%Y-%m') = '{}-{}'".format(dateInformation['Year'],formatted_month)
    
if dateInformation['Day'] != 'Day':
  if int(dateInformation['Day'])<10:
    formatted_day = '0'+dateInformation['Day']
  else:
    formatted_day = dateInformation['Day']
  query_date = " AND DATE_FORMAT(Date,'%Y-%m-%d') = '{}-{}-{}'".format(dateInform
ation['Year'],formatted_month,formatted_day)

query = query + query_date
for key, value in form_items:
  if value != '' and value != key:
    query += " AND {} = '{}'".format(key,value)

  if form_submit == 'Search':
    cur.execute(query)
    query_return = cur.fetchall()

    for value in query_return:
      RequestID = value[0]
      TimeStamp = value[1]
      Region = value[2]
      Submitter = value[3]
      Company_Name = value[4]
      Company_ID = value[5]
      Status = value[6]

      if not "data" in result:
        result["data"] = []
      result["data"].append({
        "RequestID"     :   RequestID,
        "Timestamp"     :   TimeStamp,
        "Region"        :   Region,
        "Submitter"     :   Submitter,
        "CompanyName"   :   Company_Name,
        "CompanyID"     :   Company_ID,
        "Status"        :   Status
      })

    if formInformation['Region'] == '':
        formInformation['Region'] = 'Select'
    if formInformation['Status'] == '':
        formInformation['Status']= 'Select'


template = templates.get_template("View_IPRequest.html")
print(template.render(DEBUG_LIST=DEBUG_LIST, dateInformation=dateInformation, disabled_
m = disabled_m, disabled_d = disabled_d, result=result, formInformation=formInformation
,year=year))
