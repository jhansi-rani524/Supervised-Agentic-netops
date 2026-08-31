import os
import time
import yaml
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from netmiko import ConnectHandler

from ospf_status import check_ospf_neighbors
from bgp_status import check_bgp_neighbors
from vlan_status import check_vlan_status
from logger import log_event

load_dotenv()

USERNAME = os.getenv("JHANSI_USERNAME")
PASSWORD = os.getenv("JHANSI_PASSWORD")
SECRET = os.getenv("JHANSI_SECRET")

# Safety guard: remediate.py will NEVER touch a device not on this list,
# no matter what watcher.py reports.
ALLOWED_ROUTERS = ["192.168.160.132", "192.168.160.133", "192.168.160.134", "192.168.160.135"]
ALLOWED_SWITCHES = ["192.168.160.136", "192.168.160.137", "192.168.160.138"]

MAX_ATTEMPTS = 3           # give up after this many tries for the same problem
COOLDOWN_SECONDS = 300     # don't retry the same device+check within 5 minutes

# Tracks attempts per device+check, so we don't retry forever or too fast.
# Shape: {"ospf_192.168.160.132": {"attempts": 1, "last_attempt": <timestamp>}}
remediation_history = {}


def now():
    return datetime.now(ZoneInfo("America/Chicago")).strftime("%H:%M:%S")


def can_attempt(key):
    """Checks the retry limit and cooldown before allowing a remediation attempt."""
    record = remediation_history.get(key)
    if record is None:
        return True, "first attempt"

    if record["attempts"] >= MAX_ATTEMPTS:
        return False, f"retry limit reached ({MAX_ATTEMPTS} attempts) — needs manual attention"

    seconds_since_last = time.time() - record["last_attempt"]
    if seconds_since_last < COOLDOWN_SECONDS:
        wait_left = int(COOLDOWN_SECONDS - seconds_since_last)
        return False, f"cooldown active — wait {wait_left} more seconds before retrying"

    return True, "retry allowed"


def record_attempt(key):
    record = remediation_history.get(key, {"attempts": 0, "last_attempt": 0})
    record["attempts"] += 1
    record["last_attempt"] = time.time()
    remediation_history[key] = record


def remediate_ospf(host):
    key = f"ospf_{host}"

    if host not in ALLOWED_ROUTERS:
        return {"host": host, "result": "blocked", "message": "host not in ALLOWED_ROUTERS"}

    allowed, reason = can_attempt(key)
    if not allowed:
        log_event("remediate", host, "SKIPPED", f"ospf remediation skipped: {reason}")
        return {"host": host, "result": "skipped", "message": reason}

    record_attempt(key)

    with open("ospf_inventory.yaml") as file:
        data = yaml.safe_load(file)
    details = next((d for d in data["routers"].values() if d["host"] == host), None)

    if details is None:
        return {"host": host, "result": "error", "message": "host not found in ospf_inventory.yaml"}

    device = {
        "device_type": details["device_type"],
        "ip": host,
        "username": USERNAME,
        "password": PASSWORD,
        "secret": SECRET,
    }

    try:
        connection = ConnectHandler(**device)
        connection.enable()

        process_id = details["process_id"]
        config_commands = [
            f"router ospf {process_id}",
            f"router-id {details['router_id']}"
        ]
        for interface in details["interfaces"]:
            config_commands.append(
                f"network {interface['ip']} 0.0.0.0 area {interface['area']}"
            )

        connection.send_config_set(config_commands)
        connection.save_config()
        connection.disconnect()

        time.sleep(5)
        check_result = check_ospf_neighbors(host, USERNAME, PASSWORD, SECRET)

        if check_result["status"] == "ok":
            log_event("remediate", host, "FIXED", "OSPF re-pushed and confirmed FULL")
            return {"host": host, "result": "fixed", "message": "OSPF re-applied, neighbors confirmed FULL"}
        else:
            log_event("remediate", host, "STILL_DOWN", f"OSPF re-pushed but still: {check_result['status']}")
            return {"host": host, "result": "still_down",
                    "message": f"Re-applied config, but OSPF is still {check_result['status']}"}

    except Exception as e:
        log_event("remediate", host, "ERROR", str(e))
        return {"host": host, "result": "error", "message": str(e)}


def remediate_bgp(host):
    key = f"bgp_{host}"

    if host not in ALLOWED_ROUTERS:
        return {"host": host, "result": "blocked", "message": "host not in ALLOWED_ROUTERS"}

    allowed, reason = can_attempt(key)
    if not allowed:
        log_event("remediate", host, "SKIPPED", f"bgp remediation skipped: {reason}")
        return {"host": host, "result": "skipped", "message": reason}

    record_attempt(key)

    with open("bgp_inventory.yaml") as file:
        data = yaml.safe_load(file)
    details = next((d for d in data["routers"].values() if d["host"] == host), None)

    if details is None:
        return {"host": host, "result": "error", "message": "host not found in bgp_inventory.yaml"}

    device = {
        "device_type": details["device_type"],
        "ip": host,
        "username": USERNAME,
        "password": PASSWORD,
        "secret": SECRET,
    }

    try:
        connection = ConnectHandler(**device)
        connection.enable()

        config_commands = [f"router bgp {details['asn']}"]
        for neighbor in details["neighbors"]:
            config_commands.append(f"neighbor {neighbor['ip']} remote-as {neighbor['remote_as']}")

        connection.send_config_set(config_commands)
        connection.send_command("clear ip bgp *")
        connection.save_config()
        connection.disconnect()

        time.sleep(10)
        check_result = check_bgp_neighbors(host, USERNAME, PASSWORD, SECRET)

        if check_result["status"] == "ok":
            log_event("remediate", host, "FIXED", "BGP re-pushed, session reset, confirmed up")
            return {"host": host, "result": "fixed", "message": "BGP re-applied and confirmed up"}
        else:
            log_event("remediate", host, "STILL_DOWN", f"BGP re-pushed but still: {check_result['status']}")
            return {"host": host, "result": "still_down",
                    "message": f"Re-applied config, but BGP is still {check_result['status']}"}

    except Exception as e:
        log_event("remediate", host, "ERROR", str(e))
        return {"host": host, "result": "error", "message": str(e)}


def remediate_vlan(host):
    key = f"vlan_{host}"

    if host not in ALLOWED_SWITCHES:
        return {"host": host, "result": "blocked", "message": "host not in ALLOWED_SWITCHES"}

    allowed, reason = can_attempt(key)
    if not allowed:
        log_event("remediate", host, "SKIPPED", f"vlan remediation skipped: {reason}")
        return {"host": host, "result": "skipped", "message": reason}

    record_attempt(key)

    with open("vlan_inventory.yaml") as file:
        data = yaml.safe_load(file)
    name = next((n for n, d in data["switches"].items() if d["host"] == host), None)
    details = data["switches"].get(name) if name else None

    if details is None:
        return {"host": host, "result": "error", "message": "host not found in vlan_inventory.yaml"}

    interface = details["interface"]
    vlan_id = details["vlan_id"]
    vlan_name = details["vlan_name"]

    device = {
        "device_type": "cisco_ios",
        "host": host,
        "username": USERNAME,
        "password": PASSWORD,
        "secret": SECRET,
    }

    try:
        connection = ConnectHandler(**device)
        connection.enable()

        commands = [
            f"vlan {vlan_id}",
            f"name {vlan_name}",
            "exit",
            f"interface {interface}",
            "switchport mode access",
            f"switchport access vlan {vlan_id}",
            "no shutdown",
            "end"
        ]

        connection.send_config_set(commands)
        connection.save_config()
        connection.disconnect()

        time.sleep(5)
        check_result = check_vlan_status(
            host, USERNAME, PASSWORD, SECRET,
            expected_vlan_id=vlan_id, expected_interface=interface
        )

        if check_result["status"] == "ok":
            log_event("remediate", host, "FIXED", f"VLAN {vlan_id} re-applied and confirmed")
            return {"host": host, "result": "fixed", "message": f"VLAN {vlan_id} re-applied and confirmed"}
        else:
            log_event("remediate", host, "STILL_DOWN", f"VLAN re-applied but still: {check_result['status']}")
            return {"host": host, "result": "still_down",
                    "message": f"Re-applied VLAN config, but still {check_result['status']}"}

    except Exception as e:
        log_event("remediate", host, "ERROR", str(e))
        return {"host": host, "result": "error", "message": str(e)}


if __name__ == "__main__":
    print("This is a manual test of remediate.py — pick one function to test by hand.")
    print("Example: remediate_ospf('192.168.160.132')")