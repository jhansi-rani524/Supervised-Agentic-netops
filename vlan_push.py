import os
import yaml
from dotenv import load_dotenv
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

load_dotenv()

with open("vlan_inventory.yaml") as file:
    data = yaml.safe_load(file)

switches = data["switches"]

for name, details in switches.items():
    ip = details["host"]
    interface = details["interface"]
    vlan_id = details["vlan_id"]
    vlan_name = details["vlan_name"]

    print(f"\nAbout to configure {name} ({ip}):")
    print(f"  VLAN: {vlan_id} ({vlan_name})")
    print(f"  Interface: {interface}")
    confirm = input("Proceed? (y/n): ").strip().lower()

    if confirm != "y":
        print(f"Skipped {name}.")
        continue

    print(f"\nConnecting to Switch {name} ({ip})")

    switch = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": os.getenv("JHANSI_USERNAME"),
        "password": os.getenv("JHANSI_PASSWORD"),
        "secret": os.getenv("JHANSI_SECRET"),
        "global_delay_factor": 2,
        "fast_cli": False
    }

    try:
        connection = ConnectHandler(**switch)
        connection.enable()
        print("Connected successfully")

        vlan_commands = [
            f"vlan {vlan_id}",
            f"name {vlan_name}",
            "exit",
            f"interface {interface}",
            "switchport mode access",
            f"switchport access vlan {vlan_id}",
            "no shutdown",
            "end"
        ]

        output = connection.send_config_set(vlan_commands)
        print("\nConfiguration output:\n")
        print(output)

        print("\nSaving configuration...")
        save_output = connection.save_config()
        print(save_output)

        connection.disconnect()
        print(f"Disconnected from {name}")

    except NetmikoTimeoutException:
        print(f"Timeout while connecting to {ip}")
    except NetmikoAuthenticationException:
        print(f"Authentication failed for {ip}")
    except Exception as e:
        print(f"Error on {ip}: {str(e)}")