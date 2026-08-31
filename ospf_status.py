from logger import log_event
from dotenv import load_dotenv
import os

load_dotenv()

from netmiko import ConnectHandler

# OSPF states considered "down" or "not fully formed"
DOWN_STATES = ["DOWN", "ATTEMPT", "INIT", "2-WAY", "EXSTART", "EXCHANGE", "LOADING"]


def check_ospf_neighbors(host, username, password, secret):
    """
    Read-only check: connects to ONE router, checks OSPF neighbor status.
    Never pushes config - safe to call repeatedly from watcher.py.
    Returns a dict: {"host": ..., "status": "ok"/"down"/"no_neighbors"/"error", "details": [...]}
    """
    router = {
        "device_type": "cisco_ios",
        "host": host,
        "username": username,
        "password": password,
        "secret": secret,
    }

    result = {"host": host, "status": "ok", "details": []}

    try:
        connection = ConnectHandler(**router)
        connection.enable()

        ospf_output = connection.send_command("show ip ospf neighbor")
        lines = ospf_output.strip().splitlines()

        if not lines:
            result["status"] = "no_neighbors"
            result["details"].append("No OSPF neighbors found at all.")
            log_event("ospf_status", host, result["status"], "; ".join(result["details"]))
            return result

        data_lines = []
        for index, line in enumerate(lines):
            if line.strip().startswith("Neighbor ID"):
                data_lines = lines[index + 1:]
                break

        if not data_lines:
            result["status"] = "no_neighbors"
            result["details"].append("No OSPF summary data found.")
            log_event("ospf_status", host, result["status"], "; ".join(result["details"]))
            return result

        found_down = False
        for line in data_lines:
            if not line.strip():
                continue
            fields = line.split()
            if len(fields) < 6:
                continue

            neighbor_id = fields[0]
            state_field = fields[2]
            state = state_field.split("/")[0]

            if state in DOWN_STATES:
                found_down = True
                result["details"].append(f"Neighbor {neighbor_id} is in state {state} (not fully up)")

        if found_down:
            result["status"] = "down"
        else:
            result["details"].append("All OSPF neighbors are FULL.")
        log_event("ospf_status", host, result["status"], "; ".join(result["details"]))    

    except Exception as e:
        result["status"] = "error"
        result["details"].append(str(e))
        log_event("ospf_status", host, "error", str(e))

    finally:
        try:
            connection.disconnect()
        except:
            pass

    return result


if __name__ == "__main__":
    result = check_ospf_neighbors(
        host="192.168.160.132",
        username=os.getenv("JHANSI_USERNAME"),
        password=os.getenv("JHANSI_PASSWORD"),
        secret=os.getenv("JHANSI_SECRET"),
    )
    print(f"\nHost: {result['host']}")
    print(f"Status: {result['status']}")
    for line in result["details"]:
        print(f" - {line}")