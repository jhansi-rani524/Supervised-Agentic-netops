from netmiko import ConnectHandler
router = {
    "device_type":"cisco_ios",
    "host":"192.168.160.135",
    "username":"jhansi",
    "password":"mathematics322@",
    "secret":"mathematics322@",
}
net_connect=ConnectHandler(**router)
net_connect.enable()
output=net_connect.send_command("sh ip int brief")
print(output)
net_connect.disconnect()
