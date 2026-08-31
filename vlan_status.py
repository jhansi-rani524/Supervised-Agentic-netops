from logger import log_event
import os
import yaml
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

def check_vlan_status(host, username, password, secret, expected_vlan_id=None, expected_interface=None):
    switch = {
        "device_type": "cisco_ios",
        "host": host,
        "username": username,
        "password": password,
        "secret": secret
    }
    try:
        connection = ConnectHandler(**switch)
        connection.enable()
        output = connection.send_command("show vlan brief")

        if expected_vlan_id is not None and expected_interface is not None:
            vlan_line_found = False
            port_assigned = False
            for line in output.splitlines():
                if line.strip().startswith(str(expected_vlan_id)):
                    vlan_line_found = True
                    if expected_interface.replace("Ethernet", "Et") in line:
                        port_assigned = True

            if not vlan_line_found:
                status = "down"
                details = f"VLAN {expected_vlan_id} not found on switch."
            elif not port_assigned:
                status = "down"
                details = f"VLAN {expected_vlan_id} exists, but {expected_interface} is not assigned to it."
            else:
                status = "ok"
                details = f"VLAN {expected_vlan_id} active with {expected_interface} correctly assigned."
        else:
            status = "ok"
            details = output

        log_event("vlan_status", host, status, details)
        return {"host": host, "status": status, "details": details}

    except Exception as e:
        log_event("vlan_status", host, "error", str(e))
        return {"host": host, "status": "error", "details": str(e)}
    finally:
        try:
            connection.disconnect()
        except:
            pass


if __name__ == "__main__":
    with open("vlan_inventory.yaml") as file:
        data = yaml.safe_load(file)

    switches = data["switches"]

    for name, details in switches.items():
        result = check_vlan_status(
            host=details["host"],
            username=os.getenv("JHANSI_USERNAME"),
            password=os.getenv("JHANSI_PASSWORD"),
            secret=os.getenv("JHANSI_SECRET"),
            expected_vlan_id=details["vlan_id"],
            expected_interface=details["interface"]
        )
        print(f"\n--- {name} ({result['host']}) ---")
        print(f"Status: {result['status']}")
        print(result['details'])