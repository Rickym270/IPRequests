#!python
'''
    Author: Ricky Martinez
    Purpose: CGI Script was created to:
             Part 1:obtain values from a form and/or update the page according to a value 
             that was selected. 
             Part 2: The information obtained is then saved into a dictionary which is then used to
             submit the information to a database. The information that is submitted only works if the record
             was originally created already.
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
        elif i == 3:
            socket = line[:-1]
#CONNECT to DB
db = MySQLdb.connect(host=host,user=username,passwd=password, db="NMG", unix_socket = socket)
cur = db.cursor()

#CREATE form object
form = cgi.FieldStorage()

#CREATE datastructures
service_dictionary=collections.OrderedDict()
js_service_dictionary = {}
form_return_data = {}

#CREATE user and timestamp
submitter = False
status = False
req_id = False
form_region = False
form_service_name = False
service_env = False
res = False
service_res = []
region = False
res2 = False
res3 = False
entitle_id = False
service_group = None
isItToday = True
request_timestamp = None
current_timestamp = None
service_id_list = []
submit_btn = form.getfirst('Submit', '')
current_timestamp = datetime.datetime.today().strftime("%m/%d/%Y")
user = os.environ["REMOTE_USER"]


########################################
DEBUG_LIST=[]
########################################

#UNALLOWED ip Addresses
blocked_ipAddress = []
with open('IPAddress_NotAllowed.txt') as g:
        blocked_ip = g.readlines()
        for ip_address in blocked_ip:
                blocked_ipAddress.append(ip_address.strip())

#GET form fields
form_status = form.getfirst("Status")
form_region = form.getfirst("Region")
form_service_type = form.getlist("ServiceType")
form_customer_name = form.getfirst("CustomerName","")
form_customer_id = form.getfirst("CustomerID","")
addOrRemove = form.getlist('addOrRemove')
form_first_ip = form.getlist("FirstIP")
form_last_ip = form.getlist("LastIP")


#GET Request Id from URL
if os.environ.get("QUERY_STRING"):
    req_id = int(os.environ.get("QUERY_STRING").split('=')[1])

status_query = "SELECT Status from IPReg_Info WHERE Request_ID={}".format(req_id)
cur.execute(status_query)
status_res = cur.fetchone()
if status_res == None:
    req_id = False
elif status_res[0]=='Completed':
    req_id = False

if req_id and submit_btn=='':
    #RESOLVE most fields
    query = "SELECT * FROM IPReg_Info WHERE Request_ID = {}".format(req_id)
    cur.execute(query)
    res = cur.fetchone()

    timestamp = res[1]
    region = res[2]
    submitter = res[3]


    #RESOLVE IP Addresses and Add or Remove
    query2 = "SELECT Request_ID, First_IP, Last_IP, Service_ID, AddRemove  FROM IPReg_Entitlement WHERE Request_ID = {} ORDER BY Service_ID ASC".format(req_id)
    cur.execute(query2)
    res2 = cur.fetchall()
#    DEBUG_LIST.append(res2)

    #RESOLVE Service_ID
    for service_ids in res2:
        service_id_list.append(service_ids[3])
    service_id_list = list(set(service_id_list))

    query3= "SELECT Name,Environment from IPReg_Services WHERE ID = {} ".format(service_id_list[0])
    for serv_id in service_id_list[1:]:
        query3 += ' OR ID = {}'.format(serv_id)

    cur.execute(query3)
    res3 = cur.fetchall()

################################# GETS name of service based on service_id & serv_env: QUERY
    for service in res3:
        #EX. Returns 'EU Viewer'
        service_res.append(service[0])
    ##REGION
    form_region = form.getfirst("Region",region)
    region=form_region
    ##END REGION

    filename = "ServiceName_{}.txt".format(region)
    #CHECKS if form is submitted with no Region or Service Environment variables
    with open(filename,'r') as f:
        serv_lines = f.readlines()
        #REMOVES first line of file '**** item1,item2,item3 *****'
        del serv_lines[0]

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

    #Matches submitted service_name to get the service environment
    for service_group in service_dictionary:
        for service_region in service_dictionary[service_group]:
            if service_name == service_region:
                service_env = service_group
        service_group = service_group

    form_service_name = form.getfirst("ServiceName", res3[0][1])
################################### Part 2: Submit to DB #####################################
#Handles no lastIP entered
for i in range(0,len(form_first_ip)):
    try:
        form_last_ip[i]
    except IndexError:
        form_last_ip.append(form_first_ip[i])
#Handles no customer ID
if not form_customer_id:
    form_customer_id=''

if submit_btn == 'Submit':
    request_time_query = "SELECT Date FROM IPReg_Info WHERE Request_ID = {}".format(req_id)
    cur.execute(request_time_query)
    request_time = cur.fetchone()[0]
    request_time = request_time.strftime('%m/%d/%Y')
    ###CHECK time if past today###
    if request_time < current_timestamp:
        isItToday = False



    if "add" not in form_return_data:
       form_return_data["add"]=[]
    if "remove" not in form_return_data:
       form_return_data["remove"]=[]
    for i in range(0,len(addOrRemove)):
        try:
            first_ip = form_first_ip[i]
            last_ip = form_last_ip[i]
        except:
            form_last_ip[i] = form_first_ip[i]
            first_ip = form_first_ip[i]
            last_ip = form_last_ip[i]


        if addOrRemove[i] == "add":
            form_return_data["add"].append({
                "Region"        :   form_region,
                "Customer Name" :   form_customer_name,
                "Customer ID"   :   form_customer_id,
                "Service Name"  :   form_service_type,
                "Index"         :   i,
                "First IP"      :   first_ip,
                "Last IP"       :   last_ip,
            })
        if addOrRemove[i] == "remove":
            form_return_data["remove"].append({
                "Region"        :   form_region,
                "Customer Name" :   form_customer_name,
                "Customer ID"   :   form_customer_id,
                "Service Name"  :   form_service_type,
                "Index"         :   i,
                "First IP"      :   first_ip,
                "Last IP"       :   last_ip,
            })

    ##GENERATE QUERY 1.5.17
    if form_return_data["add"]:
        # Handles add case
        DEBUG_LIST.append(form_return_data);
        service_id_query = "SELECT ID FROM IPReg_Services WHERE Name= '{}'".format(form_return_data["add"][0]["Service Name"][0])
        for i in range(0,len(form_return_data["add"][0]["Service Name"])):
            service_id_query += " OR Name = '{}'".format(form_return_data["add"][0]["Service Name"][i])

##################################### IPReg_Info Insertion ########################################
        if not isItToday:
            ##INSERT INTO IPReg_INFO
            twipInfo_insertNew = "INSERT INTO IPReg_Info(Region, Submitter, Company_Name, Company_ID,Status) VALUES('{}','{}','{}','{}','{}')".format(form_return_data["add"][0]["Region"],user,form_return_data["add"][0]["Customer Name"],form_return_data["add"][0]["Customer ID"], form_status)
            DEBUG_LIST.append(twipInfo_insertNew)
            cur.execute(twipInfo_insertNew)
            db.commit()
        else:
            twipInfo_RemoveOld = "DELETE FROM IPReg_Info WHERE Request_ID = {}".format(req_id)
            twipEntitlement_RemoveOld = "DELETE FROM IPReg_Entitlement WHERE Request_ID={}".format(req_id)
            cur.execute(twipInfo_RemoveOld)
            cur.execute(twipEntitlement_RemoveOld)

            twipInfo_insertNew = "INSERT INTO IPReg_Info(Request_ID, Region, Submitter, Company_Name, Company_ID, Status) VALUES({},'{}','{}','{}','{}','{}')".format(req_id,form_return_data["add"][0]["Region"],user,form_return_data["add"][0]["Customer Name"],form_return_data["add"][0]["Customer ID"],form_status)
            cur.execute(twipInfo_insertNew)

        #GET last insert ID from IPReg_Info
        last_id_query = "SELECT MAX(Request_ID) FROM IPReg_Info"
        cur.execute(last_id_query)
        last_id = cur.fetchone()

    else:
        # Handles remove case
        service_id_query = "SELECT ID FROM IPReg_Services WHERE Name= '{}'".format(form_return_data["remove"][0]["Service Name"][0])
        for i in range(0,len(form_return_data["remove"][0]["Service Name"])):
            service_id_query += " OR Name = '{}'".format(form_return_data["remove"][0]["Service Name"][i])

        if not isItToday:
            # If it is not today,make new request
            twipInfo_insertNew = "INSERT INTO IPReg_Info(Region, Submitter, Company_Name, Company_ID, Status) VALUES('{}','{}','{}','{}','{}')".format(form_return_data["add"][0]["Region"],user,form_return_data["add"][0]["Customer Name"],form_return_data["add"][0]["Customer ID"],form_status)
            cur.execute(twipInfo_insertNew)
            db.commit()
        else:
            # If same day, delete request and insert new one
            twipInfo_RemoveOld = "DELETE FROM IPReg_Info WHERE Request_ID = {}".format(req_id)
            twipEntitlement_RemoveOld = "DELETE FROM IPReg_Entitlement WHERE Request_ID={}".format(req_id)
            cur.execute(twipInfo_RemoveOld)
            cur.execute(twipEntitlement_RemoveOld)
            db.commit()
            if form_return_data["add"]:
              twipInfo_insertNew = "INSERT INTO IPReg_Info(Request_ID, Region, Submitter, Company_Name, Company_ID, Status) VALUES({},'{}','{}','{}','{}','{}')".format(req_id,form_return_data["add"][0]["Region"],user,form_return_data["add"][0]["Customer Name"],form_return_data["add"][0]["Customer ID"], form_status)
              cur.execute(twipInfo_insertNew)
              db.commit()


        #GET last insert ID from IPReg_Info
        last_id_query = "SELECT MAX(Request_ID) FROM IPReg_Info"
        cur.execute(last_id_query)
        last_id = cur.fetchone()

################################## IPReg_Entitlement Insertion ####################################
    for data in form_return_data:
        if form_return_data[data]:
#            cur_service_name = form_return_data[data][0]["Service Name"][0]
            cur.execute(service_id_query)
            service_id = cur.fetchall()

            for id in service_id:
                for ip in form_return_data[data]:
                    if not isItToday:
                        twipEntitlementUpdate_query = "INSERT INTO IPReg_Entitlement(Request_ID,First_IP, Last_IP, Service_ID, AddRemove) VALUES({},'{}','{}',{},'{}')".format(last_id[0],ip["First IP"], ip["Last IP"], id[0], data.title());

#                       DEBUG_LIST.append(id)
#                       DEBUG_LIST.append(twipEntitlementUpdate_query)
                        cur.execute(twipEntitlementUpdate_query)
                        db.commit()
                    else:
                        twipEntitlement_insertNew = "INSERT INTO IPReg_Entitlement(Request_ID, First_IP, Last_IP,Service_ID,AddRemove) VALUES({},'{}','{}',{},'{}')".format(req_id, ip["First IP"], ip["Last IP"], id[0],data.title())
                        cur.execute(twipEntitlement_insertNew)
                        db.commit()


################################### Part 3: Send Email #########################################
    #Send email
    Subject = "External IP Registration Request "+current_timestamp+" - EDIT"
    From = "username@tradeweb.com"
    To = 'user.name@tradeweb.com'
    command = '/usr/sbin/sendmail'

    msg = MIMEMultipart('alternative')
    msg['Subject']=Subject
    msg['From']= From
    msg['To']= To

    html = """\
      <html><head></head><body>
                        <h3>Request Edited</h3>
      <table>
      <tr><td>Submitter:</td><td>{}</td><td></br></td></tr>
      <tr><td>Status:</td><td>{}</td><td></br></td></tr>
      <tr><td>Region:</td><td>{}</td><td></br></td></tr>
      <tr><td>Customer Name:</td><td>{}</td><td></br></td></tr>
      <tr><td>Customer ID:</td><td>{}</td><td></br></td></tr>
      <tr><td>Business Unit:</td><td>{}</td><td></br></td></tr>
      <tr><td>Service Type:</td><td></br></td>
    """.format(user,form_status,form_region,form_customer_name,form_customer_id,form.getfirst("ServiceName",res3))
    for i in range(0,len(form_service_type)):
      html += "<tr><td></td><td>{}</td></tr>".format(form_service_type[i])
    for i in range(0,len(form_first_ip)):
      html += "<tr><td>IP Range:</td><td>{} - {}</td><td>{}</td></tr>".format(form_first_ip[i], form_last_ip[i], addOrRemove[i])

    part2 = MIMEText(html, 'html')

    msg.attach(part2)

    p = Popen([command, '-t', '-i'], stdin=PIPE, stdout=PIPE)
    (stdout , stderr) = p.communicate(msg.as_string())

template = templates.get_template("Edit_IPRequest.html")
print(template.render(DEBUG_LIST=DEBUG_LIST, service_dictionary=service_dictionary, js_service_dictionary=js_service_dictionary, form_service_name=form_service_name, res=res, res2=res2, req_id=req_id, submit_btn = submit_btn, service_res=service_res, region=region, status=status, blocked_ipAddress=blocked_ipAddress))
