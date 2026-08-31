from logger import log_event
from dotenv import load_dotenv
import os
from netmiko import ConnectHandler

load_dotenv()

def get_interface_status(host, username, password, secret):
    router = {
        "device_type": "cisco_ios",
        "host": host,
        "username": username,
        "password": password,
        "secret": secret
    }
    try:
        net_connect = ConnectHandler(**router)
        net_connect.enable()
        output = net_connect.send_command("sh ip int brief")
        log_event("interface_status", host, "ok", output)
        return {"host": host, "status": "ok", "details": output}
    except Exception as e:
        log_event("interface_status", host, "error", str(e))
        return {"host": host, "status": "error", "details": str(e)}
    finally:
        try:
            net_connect.disconnect()
        except:
            pass


if __name__ == "__main__":
    result = get_interface_status(
        host="192.168.160.132",
        username=os.getenv("JHANSI_USERNAME"),
        password=os.getenv("JHANSI_PASSWORD"),
        secret=os.getenv("JHANSI_SECRET")
    )
    print(f"\nHost: {result['host']}")
    print(f"Status: {result['status']}")
    print(result['details'])