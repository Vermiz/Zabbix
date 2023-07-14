########
#Author: Kamil Goluchowski
#Github: https://github.com/Vermiz
########
#
# Script for check last_value for item: Example: Version of zabbix_agent
# in this case I check if the zabbix agent is up to date.
#
# Requirements: pip install pyzabbix
# Rember to change zabbix IP server, login, password and host group.
#####

from pyzabbix import ZabbixAPI

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = "https://192.18.1.2"
zapi = ZabbixAPI(ZABBIX_SERVER)
# Disable SSL certificate verification
#zapi.session.verify = False

# Login to the Zabbix API
zapi.login("Admin", "Pass")
# Download item where item_key "agent.version"

# ID hostgroupu for filter only windows and linux.
hostgroup_ids = [2, 3]

# Download all enabled host in hostgroups: hostgroup_ids
hosts = zapi.host.get(output=["host"], groupids=hostgroup_ids, filter={"status": 0})

# Item key
item_key = "agent.version"

# File name
file_name = "c:\ReportZabbixVersion.csv"

with open("c:\ReportZabbixVersion.csv", "w") as file:
    file.write(f"Host:; IP:; Zabbix agent Version:\n")
    # Download last value for item and host.
    for host in hosts:
        host_name = host["host"]
        
        item = zapi.item.get(output=["itemid"], hostids=host["hostid"], filter={"key_": item_key})
        if item:
            item_id = item[0]["itemid"]
            
            history = zapi.history.get(
                output=["value"],
                history=1,  # Historia (0 - number value, 1 - text, 2 - logs)
                sortfield="clock",
                sortorder="DESC",
                limit=1,
                itemids=[item_id]
            )
            host_ips = zapi.hostinterface.get(output=["ip"], hostids=host["hostid"])
            ips = [interface["ip"] for interface in host_ips]
            
            if history:
                last_value = history[0]["value"]
                
                file.write(f"{host_name}; {', '.join(ips)}; {last_value}\n")
            else:
                file.write(f"No data for item key: '{item_key}' and host: '{host_name}'\n")
        else:
            file.write(f"No item with key: '{item_key}' for host '{host_name}'\n")

print(f"Data save to file: {file_name}")
