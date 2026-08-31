from dotenv import load_dotenv
import os

load_dotenv()

import yaml
from netmiko import ConnectHandler

with open("ospf_inventory.yaml") as file:
    data = yaml.safe_load(file)

def wildcard_mask(mask):
    return ".".join(str(255 - int(octet)) for octet in mask.split("."))

def push_ospf_config(router_name, details):
    """
    Pushes interface + OSPF config to ONE router.
    Does NOT check neighbor status - that's ospf_neighbor_down.py's job.
    """
    device = {
        "device_type": details["device_type"],
        "ip": details["host"],
        "username": os.getenv("JHANSI_USERNAME"),
        "password": os.getenv("JHANSI_PASSWORD"),
        "secret": os.getenv("JHANSI_SECRET"),
    }

    print(f"\nConnecting to the {router_name}")
    connection = ConnectHandler(**device)
    connection.enable()
    config_command = []

    for interface in details["interfaces"]:
        config_command.append(f"interface {interface['name']}")
        config_command.append(f"ip address {interface['ip']} {interface['mask']} ")
        config_command.append("no shutdown")

    config_command.append(f"router ospf {details['process_id']}")
    config_command.append(f"router-id {details['router_id']}")

    for interface in details["interfaces"]:
        wc = wildcard_mask(interface['mask'])
        config_command.append(f"network {interface['ip']} {wc} area {interface['area']}")

    output = connection.send_config_set(config_command)
    print(output)

    connection.disconnect()
    return output


if __name__ == "__main__":
    routers = data["routers"]
    for router_name, details in routers.items():
        push_ospf_config(router_name, details)

    print("\nAll routers configured. Use ospf_neighbor_down.py separately to check status.")


