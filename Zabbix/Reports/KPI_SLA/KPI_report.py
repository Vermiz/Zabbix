########
#Author: Kamil Goluchowski
#Github: https://github.com/Vermiz
########
#
# Script for generate SLA/KPI report for item where tag name ICMP or Zabbix agent and host group id is 252 (for example).
# The script saves everything to an excel file and generates additional columns that calculate the unavailability time during and after working hours
# In excel, rows for which the value in the alert column is empty are additionally deleted. I'm only interested in the problems for which the message was sent because at that time maintenace was not set.
# If you need all alert comment line: 148 "df = df[df['alert'].notnull()]"
#
# Requirements: pip install pyzabbix, pandas
# Rember to change zabbix IP server, login, password and host group.
# Create folder KPI on c:\
#####

import os
from datetime import datetime, timedelta
import time
from pyzabbix import ZabbixAPI
import pandas as pd

# current date and time
now = datetime.datetime.now()
last = (now - timedelta(days=90))
tnow = datetime.timestamp(now)
tlast = datetime.timestamp(last)

try:
    start_time = tlast
    #start_time = '1675206060'
    #sys.argv[1]
except:
    start_time = int(time.time()) - 86400


try:
    till_time = tnow
    #till_time = '1682891940'
    #sys.argv[2]
except:
    till_time = int(time.time())

priorities = { 0 :'Not classified', 1 : 'Information', 2 : 'Warning', 3 : 'Average', 4 : 'High', 5 : 'Disaster'}

clock_format = '%Y-%m-%d %H:%M:%S'

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = "https://192.18.1.2"
zapi = ZabbixAPI(ZABBIX_SERVER)
# Disable SSL certificate verification
#zapi.session.verify = False
# Login to the Zabbix API
zapi.login("Admin", "Pass")
result = dict()

#groupids = 252 //this is host group for using to generate KPI/SLA report

events = zapi.event.get(time_from = start_time, time_till = till_time, source = 0, object = 0, selectTags = ['tag', 'value'], tags = [{"tag": "Application","value": "ICMP","operator": "1"}, {"tag": "Application","value": "Zabbix agent","operator": "1"}], groupids = 252, selectAcknowledges = 'count', select_alerts = ['eventid'], sortorder = 'DESC', output = 'extend', limit = 500)

for event in events:

    clock = int(event['clock'])
    triggerid = event['objectid']
    in_tags = event['tags']
    is_ack = event['acknowledged']
    eventid = event['eventid']
    r_eventid = event['r_eventid']
    status = 'OK'
    curr_time = datetime.utcfromtimestamp(int(time.time()))

    clock = datetime.utcfromtimestamp(int(clock))

    if r_eventid != '0':
        r_event_clock = zapi.event.get(eventids=r_eventid, source = 0, object = 0, selectAcknowledges = 'count', sortorder = 'DESC', output = ['eventid','clock'])
        r_clock = datetime.utcfromtimestamp(int(r_event_clock[0]['clock']))
        duration = r_clock - clock
        r_clock = r_clock.strftime(clock_format)
        status = 'RESOLVED'
    else:
        r_clock = '-'
        duration = curr_time - clock
    
    if is_ack == '1':
        is_ack = 'Yes'
    else:
        is_ack = 'No'

    trigger = zapi.trigger.get(triggerids = triggerid, expandDescription = True, selectHosts = ['name'], output = ['description', 'priority'])
    hostname = trigger[0]['hosts'][0]['name']
    trigger_name = trigger[0]['description']
    priority = priorities[int(trigger[0]['priority'])]

    clock = clock.strftime(clock_format)

#alert GET
    alert = zapi.alert.get(eventids = eventid, output = ['status'])
#TAG GET
    tags = ''
    for tag in in_tags:
        tags = tags + ' ' + tag['tag'] + ': ' + tag['value'] 

    with open('C:\KPI\kpitemp.csv', 'a') as f:
        print([priority], [clock], [r_clock], [status], [hostname], [trigger_name], [str(duration)], [is_ack], [alert], [tags], sep=';',end='\n', file=f) 

###Pandas modification
df = pd.read_csv("C:\KPI\kpitemp.csv", sep=';', names=["priority", "clock", "r_clock", "status", "hostname", "trigger_name", "duration", "is_ack", "alert", "tags"])

df['priority'] = df['priority'].map(lambda x: x.lstrip("'[").rstrip("']"))
df['clock'] = df['clock'].map(lambda x: x.lstrip("'[").rstrip("']"))
df['r_clock'] = df['r_clock'].map(lambda x: x.lstrip("'[").rstrip("']"))
df['status'] = df['status'].map(lambda x: x.lstrip("'[").rstrip("']"))
df['hostname'] = df['hostname'].map(lambda x: x.lstrip("'[").rstrip("']"))
df['trigger_name'] = df['trigger_name'].map(lambda x: x.lstrip("'[").rstrip("']"))
df['duration'] = df['duration'].map(lambda x: x.lstrip("'[").rstrip("']"))
df['is_ack'] = df['is_ack'].map(lambda x: x.lstrip("'[").rstrip("']"))
df['alert'] = df['alert'].map(lambda x: x.lstrip("'[").rstrip("']"))
df['tags'] = df['tags'].map(lambda x: x.lstrip("'[").rstrip("']"))
df = df.loc[df['status'] == "RESOLVED"]
df.to_excel("C:\KPI\KPI.xlsx",sheet_name="KPI", index=False)
df = pd.read_excel("C:\KPI\KPI.xlsx")
df['clock'] = pd.to_datetime(df['clock'])
df['r_clock'] = pd.to_datetime(df['r_clock'])
df['diff'] = df['r_clock'] - df['clock']
df['diff_sec'] = (df['r_clock'] - df['clock']).dt.total_seconds()

# Download value from column start_time_str i end_time_str
start_times = df["clock"]
end_times = df["r_clock"]

# Initialization empty list
business_hours_durations = []
out_of_business_hours_durations = []

# Iteration for start_time i end_time
for start_time, end_time in zip(start_times, end_times):
    business_hours_start = datetime.combine(start_time.date(), datetime.strptime("08:00", "%H:%M").time())
    business_hours_end = datetime.combine(start_time.date(), datetime.strptime("16:00", "%H:%M").time())

    business_hours_duration = max(timedelta(0), min(end_time, business_hours_end) - max(start_time, business_hours_start))
    out_of_business_hours_duration = (end_time - start_time) - business_hours_duration

    business_hours_durations.append(business_hours_duration)
    out_of_business_hours_durations.append(out_of_business_hours_duration)

# Add column
df["business_hours_duration"] = business_hours_durations
df["out_of_business_hours_duration"] = out_of_business_hours_durations
df = df[df['alert'].notnull()]
# Save data to finaly xlsx file
df.to_excel("C:\KPI\KPI.xlsx",sheet_name="KPI", index=False)

#Remove temp file:
os.remove('C:\KPI\kpitemp.csv')