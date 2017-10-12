#!python3

'''
    Author: Ricky Martinez
    Purpose: CGI Script was created to:
             Part 1:obtain values from a form and/or update the page according to a value 
             that was selected. 
             Part 2: The information obtained is then saved into a dictionary which is then used to
             submit the information to a database. 
             Part 3: The information is then emailed to a memeber of the team to inform them that a new request
             has been filled
'''

import jinja2
import cgi
import cgitb
import MySQLdb
import datetime
import collections
import os
import socket,struct
from subprocess import Popen, PIPE
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

cgitb.enable();
templates = jinja2.Environment(loader = jinja2.FileSystemLoader(searchpath="templates"))

#CONVERT ip string to Long int
def StringToLong(ip):
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L",packedIP)[0]

#GET DB info
with open('pythonmysql.ini','r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if i == 0:
            host = line[:-1]
        elif i == 1:
            username = line[:-1]
        elif i == 2:
            password = line[:-1]
#CONNECT to DB
db = MySQLdb.connect(host='127.0.0.1',user=username,passwd=password, db="NMG", unix_socket = "ysql.sock")
cur = db.cursor()

#CREATE datastructures
service_dictionary=collections.OrderedDict()
js_service_dictionary = {}
form_return_data = {}

#CREATE user and timestamp
user = os.environ["REMOTE_USER"]
timestamp = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
current_timestamp = datetime.datetime.today().strftime("%m/%d/%Y")
status = "False"

#GET form fields
form = cgi.FieldStorage()
form_region = form.getfirst("Region","Select")
form_service_name = form.getfirst("ServiceName","Select")
form_service_type = form.getlist("ServiceType")
form_customer_name = form.getfirst("CustomerName","")
form_customer_id = form.getfirst("CustomerID","")
addOrRemove = form.getlist('addOrRemove')
submit_btn = form.getfirst('Submit')

form_first_ip = form.getlist("FirstIP")
form_last_ip = form.getlist("LastIP")

match_firstLast= True
########################################
DEBUG_LIST=[]
DEBUG_LIST.append(form_customer_id);
########################################

blocked_ipAddress = []
with open('blocked_ip.txt') as g:
  blocked_ip = g.readlines()
  for ip_address in blocked_ip:
    blocked_ipAddress.append(ip_address.strip())

if form_first_ip and submit_btn=="Submit":
    #IF no last IP is entered, set last IP equal to firstIP (NO RANGE)
    for i in range(0,len(form_first_ip)):
        if form_first_ip[i]=='From':
            del form_first_ip[i]
        if len(form_first_ip) != len(form_last_ip):
            match_firstLast = False
        try:
            if form_last_ip[i]=='To' and match_firstLast:
                form_last_ip[i] = form_first_ip[i]
        except IndexError:
            if form_last_ip[i]=='To' and match_firstLast:
                form_last_ip[i] = form_first_ip[i]
    #IF no customer id is entered
    if not form_customer_id:
        form_customer_id = '0'

    if "add" not in form_return_data:
        form_return_data["add"]=[]
    if "remove" not in form_return_data:
        form_return_data["remove"]=[]


    #CREATES data structure for submitted form data
    for i in range(0,len(addOrRemove)):
        if match_firstLast:
            first_ip = form_first_ip[i]
            last_ip = form_last_ip[i]

            if addOrRemove[i] == "add":
                form_return_data["add"].append({
                    "Service Name"  :   form_service_type,
                    "First IP"      :   first_ip,
                    "Last IP"       :   last_ip,
                })
            if addOrRemove[i] == "remove":
                form_return_data["remove"].append({
                    "Service Name"  :   form_service_type,
                    "First IP"      :   first_ip,
                    "Last IP"       :   last_ip,
                })

filename = 'ServiceName_'+form_region+'.txt'
serv_lines = []
if form_region != "Select":
  with open(filename,'r') as f:
    serv_lines = f.readlines()
    #REMOVES first line of file '**** item1,item2,item3 *****'
    del serv_lines[0]

#CHECKS if form is submitted with no Region or Service Environment variables

#PARSES through ServiceNames_US/EU/JP.txt to get all necesarry info
for value in serv_lines:
  service_name = value.strip().split(',')[:1][0]
  group_type = value.strip().split(',')[1:2][0]
  group_name = value.strip().split(',')[2:3][0]
  service_group = value.strip().split(',')[3:4][0]
  if not service_group in service_dictionary:
    js_service_dictionary[service_group] = {}
    service_dictionary[service_group]=collections.OrderedDict()
  if not service_name in service_dictionary[service_group]:
    service_dictionary[service_group][service_name]=[]
    js_service_dictionary[service_group][service_name]=[]
  js_service_dictionary[service_group][service_name].append(group_type)
  service_dictionary[service_group][service_name].append(group_type)

#If there is a search
if form_service_type and form_first_ip and form_last_ip and form_customer_name:
  result = {}

######################### INSERTS data into DB for TWIPReg_Info ##############################

  twipRegInfo_query="INSERT IGNORE INTO IPReg_Info(Region,Submitter,Company_Name,Company_ID) VALUES('"+form_region+"','"+user+"','"+form_customer_name+"','"+form_customer_id+"')"
  cur.execute(twipRegInfo_query)
  db.commit()
  #GET the request ID
  request_id = int(cur.lastrowid)

  for data in form_return_data:
    if data=="add" and form_return_data[data]:
      #RESOLVE service id
      for service in form_return_data[data][0]["Service Name"]:
        service_id_query = "SELECT ID FROM TWIPReg_Services WHERE Name = '{}'".format(service)
        cur.execute(service_id_query)
        service_id = cur.fetchone()
        service_id =service_id[0]

        for i in range(0,len(form_return_data[data])):
          twipReg_Entitlement_query = "INSERT INTO TWIPReg_Entitlement(Request_ID,First_IP,Last_IP,Service_ID,AddRemove) VALUES({},'{}','{}',{},'{}')".format(request_id,form_return_data[data][i]["First IP"],form_return_data[data][i]["Last IP"],service_id,"Add")
          cur.execute(twipReg_Entitlement_query)
          DEBUG_LIST.append(twipReg_Entitlement_query)
          db.commit()
    if data=="remove" and form_return_data[data]:
      #RESOLVE service id
      for service in form_return_data[data][0]["Service Name"]:
        service_id_query = "SELECT ID FROM TWIPReg_Services WHERE Name = '{}'".format(cur_service_name)
        cur.execute(service_id_query)
        service_id = cur.fetchone()
        service_id = service_id[0]

        twipReg_Entitlement_query = "INSERT INTO TWIPReg_Entitlement(Request_ID,First_IP,Last_IP,Service_ID,AddRemove) VALUES({},'{}','{}',{},'{}')".format(request_id,form_return_data[data][0]["First IP"],form_return_data[data][0]["Last IP"],service_id,"Remove")
        cur.execute(twipReg_Entitlement_query)
        db.commit()

  status = "True";

  #Send email
  Subject = "External IP Registration Request " + current_timestamp +" - NEW"
  From = "username@email.com"
  To = 'user.name@email.com'
  command = '/usr/sbin/sendmail'

  msg = MIMEMultipart('alternative')
  msg['Subject']= Subject
  msg['From']= From
  msg['To']= To

  html = """\
    Content-Type: text/html \r\n

    <html><head></head><body>
    <table>
      <tr><td>Submitter:</td><td>{}</td><td></br></td></tr>
      <tr><td>Region:</td><td>{}</td><td></br></td></tr>
      <tr><td>Customer Name:</td><td>{}</td><td></br></td></tr>
      <tr><td>Customer ID:</td><td>{}</td><td></br></td></tr>
      <tr><td>Business Unit:</td><td>{}</td><td></br></td></tr>
      <tr><td>Service Type:</td><td></br></td>
  """.format(user,form_region,form_customer_name,form_customer_id,form_service_name)
  for i in range(0,len(form_service_type)):
    html += "<tr><td></td><td>{}</td></tr>".format(form_service_type[i])

  for i in range(0,len(form_first_ip)):
    html += "<tr><td>IP Range:</td><td>{} - {}</td><td>{}</td></tr>".format(form_first_ip[i], form_last_ip[i], addOrRemove[i])
  part2 = MIMEText(html, 'html')

  msg.attach(part2)

#  p = Popen([command, '-t', '-i'], stdin=PIPE, stdout=PIPE)
#  (stdout , stderr) = p.communicate(msg.as_string())

template = templates.get_template("Create_IPRequest.html")
print(template.render(service_dictionary=service_dictionary, js_service_dictionary=js_service_dictionary, form_region=form_region, timestamp=timestamp,user=user,form_service_name=form_service_name,status=status, blocked_ipAddress=blocked_ipAddress))
