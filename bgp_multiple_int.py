import yaml 
from netmiko import ConnectHandler

#import yaml
with open("bgp_multiple_int.yaml") as file:
    data=  yaml.safe_load(file)

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
         
    #BGP configuration
    config_command.append(f"router bgp {details['asn']}")

    for neighbor in details["neighbors"]:
         config_command.append(f"neighbor {neighbor['ip']} remote-as {neighbor['remote_as']}")
         
    
    

    output = connection.send_config_set(config_command)
    print(output) 

   #verify BGP output
    print(f"\n--- BGP Summary for {router} ---")
    bgp_output = connection.send_command("show ip bgp summary", )
    print(bgp_output)

    # disconnecting the device
    connection.disconnect()  