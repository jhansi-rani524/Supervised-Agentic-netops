import yaml 
import logging
from netmiko import ConnectHandler

#logging configuration
logging.basicConfig(
    filename= "bgp_full_log.log",
    level = logging.INFO,
    format = "%(asctime)s -  %(levelname)s - %(message)s"
)


#import yaml
with open("bgp_multiple_int.yaml") as file:
    data=  yaml.safe_load(file)

routers= data["routers"]
for router, details in routers.items():
    try:
        device = {
        "device_type" : details["device_type"],
        "ip": details["host"],
        "username": details["username"],
        "password": details["password"]
        }

        print(f"\nConnecting to the {router}")
        logging.info(f"{router} - Connection started")
        connection = ConnectHandler(**device)
        logging.info(f"{router} - Connection started")
        
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
         
        logging.info(f"{router} - sending configuration")
    
    

        output = connection.send_config_set(config_command)
        print(output) 
        logging.info(f"{router} - Configuration Apllied Successfully")
    
        #verify BGP output
        print(f"\n--- BGP Summary for {router} ---")
        bgp_output = connection.send_command("show ip bgp summary", )
        print(bgp_output)
        logging.info(f"{router} - BGP verification succesfully completed")
    
        # disconnecting the device
        connection.disconnect()  
        logging.info(f"{router} - Disconnected succesfully")
        print(f"{router} Completed succesfully")
    except Exception as e:
        logging.error(f"{router} - failed: {str(e)}")
        print(f"{router} Faile")
        print(f"Error:{e}")    

    