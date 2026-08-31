from logger import log_event
import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

down_states = ["Idle", "Active", "Connect"]

state_meanings = {
    "Idle": "Idle (BGP hasn't started trying to connect to this neighbor)",
    "Active": "Active (trying to connect, but not succeeding yet)",
    "Connect": "Connect (attempting the TCP connection, stuck)"
}

def check_bgp_neighbors(host, username, password, secret):
    router = {
        "device_type": "cisco_ios",
        "host": host,
        "username": username,
        "password": password,
        "secret": secret
    }

    try:
        connection = ConnectHandler(**router)
        connection.enable()

        bgp_output = connection.send_command("show ip bgp summary")

        lines = bgp_output.strip().splitlines()
        data_lines = []
        for index, line in enumerate(lines):
            if line.strip().startswith("Neighbor"):
                data_lines = lines[index + 1:]
                break

        if not data_lines:
            log_event("bgp_status", host, "no_neighbors", "")
            return {"host": host, "status": "no_neighbors", "details": []}

        details = []
        any_down = False

        for line in data_lines:
            if not line.strip():
                continue

            fields = line.split()
            if len(fields) < 9:
                continue

            neighbor_ip = fields[0]
            last_field = fields[-1]

            if last_field in down_states:
                any_down = True
                meaning = state_meanings.get(last_field, last_field)
                details.append(f"Neighbor {neighbor_ip} is DOWN, state: {meaning}")
            elif not last_field.isdigit():
                any_down = True
                meaning = state_meanings.get(last_field, last_field)
                details.append(f"Neighbor {neighbor_ip} is DOWN, state: {meaning}")
            else:
                details.append(f"Neighbor {neighbor_ip} is UP, prefixes received: {last_field}")

        status = "down" if any_down else "ok"
        log_event("bgp_status", host, status, "; ".join(details))
        return {"host": host, "status": status, "details": details}

    except Exception as e:
        log_event("bgp_status", host, "error", str(e))
        return {"host": host, "status": "error", "details": [str(e)]}

    finally:
        try:
            connection.disconnect()
        except:
            pass


if __name__ == "__main__":
    result = check_bgp_neighbors(
        host="192.168.160.132",
        username=os.getenv("JHANSI_USERNAME"),
        password=os.getenv("JHANSI_PASSWORD"),
        secret=os.getenv("JHANSI_SECRET")
    )
    print(f"\nHost: {result['host']}")
    print(f"Status: {result['status']}")
    for line in result["details"]:
        print(f" - {line}")