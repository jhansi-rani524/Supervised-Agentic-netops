import yaml 
from netmiko import ConnectHandler

#import yaml
with open("ospf_mul.yaml") as file:
    data=  yaml.safe_load(file)

def wildcard_mask(mask):
    return ".".join(str(255 - int(octet)) for octet in mask.split("."))

routers= data["routers"]
for router, details in routers.items():
    device = {
        "device_type" : details["device_type"],
        "ip": details["host"],
        "username": details["username"],
        "password": details["password"]
    }

    print(f"\nConnecting to the {router}")
    connection = ConnectHandler(**device)
    connection.enable()
    config_command = []

    #Configuring the interfaces
    for interface in details["interfaces"]:
         config_command.append(f"interface {interface['name']}")
         config_command.append(f"ip address {interface['ip']} {interface['mask']} ")
         config_command.append("no shutdown")
         
    #OSPF configuration
    config_command.append(f"router ospf {details['process_id']}")
    config_command.append(f"router-id {details['router_id']}")

    for interface in details["interfaces"]:
         wc = wildcard_mask(interface['mask'])
         config_command.append(f"network {interface['ip']} {wc} area {interface['area']}")
         
    

    output = connection.send_config_set(config_command)
    print(output) 

   #verify OSPF output
    print(f"\n--- OSPF Neighbors for {router} ---")
    ospf_output = connection.send_command("show ip ospf neighbor", )
    print(ospf_output)

    # disconnecting the device
    connection.disconnect()