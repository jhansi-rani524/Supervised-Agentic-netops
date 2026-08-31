import yaml 
import time
import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

with open("bgp_inventory.yaml") as file:
    data = yaml.safe_load(file)

routers = data["routers"]
connections = {}

# STEP 1: Configure BGP on every router first
for router, details in routers.items():
    device = {
        "device_type": details["device_type"],
        "ip": details["host"],
        "username": os.getenv("JHANSI_USERNAME"),
        "password": os.getenv("JHANSI_PASSWORD"),
        "secret": os.getenv("JHANSI_SECRET")
    }

    print(f"\nConnecting to the {router}")
    connection = ConnectHandler(**device)
    connection.enable()
    config_command = []

    for interface in details["interfaces"]:
        config_command.append(f"interface {interface['name']}")
        config_command.append(f"ip address {interface['ip']} {interface['mask']} ")
        config_command.append("no shutdown")

    config_command.append(f"router bgp {details['asn']}")

    for neighbor in details["neighbors"]:
        config_command.append(f"neighbor {neighbor['ip']} remote-as {neighbor['remote_as']}")

    output = connection.send_config_set(config_command)
    print(output)

    connections[router] = connection

# STEP 2: Check each router repeatedly, up to 50 seconds, until BGP comes up
for router, connection in connections.items():
    print(f"\n--- BGP Summary for {router} ---")
    for attempt in range(5):
        bgp_output = connection.send_command("show ip bgp summary")
        if "Idle" not in bgp_output and "never" not in bgp_output:
            print(bgp_output)
            break
        print("Not established yet, waiting 10 more seconds...")
        time.sleep(10)
    else:
        print(bgp_output)
        print("Note: some neighbors may still be Idle after 50 seconds. Check manually later.")

    connection.disconnect()

    