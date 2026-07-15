from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Device IP -> correct interface mapping
device_interfaces = {
    "192.168.160.136": "Ethernet0/1",
    "192.168.160.137": "Ethernet0/2",
    "192.168.160.138": "Ethernet0/3",
}

# VLAN Details
vlan_id = 10
vlan_name = "USERS"

for ip, interface in device_interfaces.items():
    print(f"\n🔧 Connecting to Switch {ip}")

    switch = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": "jhansi",
        "password": "mathematics322@",
        "secret": "mathematics322@",
        "global_delay_factor": 2,
        "fast_cli": False
    }

    try:
        connection = ConnectHandler(**switch)
        connection.enable()
        print("✅ Connected Successfully")

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
        print("\n📌 Configuration Output:\n")
        print(output)

        print("\n💾 Saving configuration...")
        save_output = connection.save_config()
        print(save_output)

        print("\n🔍 Verifying VLAN...")
        verify_output = connection.send_command("show vlan brief")
        print(verify_output)

        connection.disconnect()
        print(f"🔌 Disconnected from {ip}")

    except NetmikoTimeoutException:
        print(f"❌ Timeout while connecting to {ip}")
    except NetmikoAuthenticationException:
        print(f"❌ Authentication failed for {ip}")
    except Exception as e:
        print(f"❌ Error on {ip}: {str(e)}")