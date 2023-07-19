SLA/KPI report

Script for generate SLA/KPI report for item where tag name ICMP or Zabbix agent and host group id is 252 (for example).
The script saves everything to an excel file and generates additional columns that calculate the unavailability time during and after working hours.

In excel, rows for which the value in the alert column is empty are additionally deleted. I'm only interested in the problems for which the message was sent because at that time maintenace was not set.
If you need all alert comment line: 148 "df = df[df['alert'].notnull()]".
