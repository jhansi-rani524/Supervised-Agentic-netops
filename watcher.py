import time
import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from ospf_status import check_ospf_neighbors
from bgp_status import check_bgp_neighbors
from interface import get_interface_status
from vlan_status import check_vlan_status
from logger import log_event

load_dotenv()

USERNAME = os.getenv("JHANSI_USERNAME")
PASSWORD = os.getenv("JHANSI_PASSWORD")
SECRET = os.getenv("JHANSI_SECRET")

routers = ["192.168.160.132", "192.168.160.133", "192.168.160.134", "192.168.160.135"]

# host -> (vlan_id, interface) for the VLAN each switch needs checked
switches = {
    "192.168.160.136": (10, "Ethernet0/0"),
    "192.168.160.137": (20, "Ethernet0/0"),
    "192.168.160.138": (30, "Ethernet0/0"),
}

# Memory: remembers the last result for each device/check, so we can spot
# "down twice in a row" instead of panicking on one bad reading.
last_status = {}


def watch_interfaces():
    while True:
        for host in routers:
            result = get_interface_status(host, USERNAME, PASSWORD, SECRET)
            check_and_report(f"interface_{host}", host, "interface", result["status"])
        time.sleep(15)


def watch_ospf():
    while True:
        for host in routers:
            result = check_ospf_neighbors(host, USERNAME, PASSWORD, SECRET)
            check_and_report(f"ospf_{host}", host, "ospf", result["status"])
        time.sleep(50)


def watch_bgp():
    while True:
        for host in routers:
            result = check_bgp_neighbors(host, USERNAME, PASSWORD, SECRET)
            check_and_report(f"bgp_{host}", host, "bgp", result["status"])
        time.sleep(100)


def watch_switches():
    while True:
        for host, (vlan_id, interface) in switches.items():
            interface_result = get_interface_status(host, USERNAME, PASSWORD, SECRET)
            check_and_report(f"interface_{host}", host, "interface", interface_result["status"])

            vlan_result = check_vlan_status(
                host, USERNAME, PASSWORD, SECRET,
                expected_vlan_id=vlan_id, expected_interface=interface
            )
            check_and_report(f"vlan_{host}", host, "vlan", vlan_result["status"])
        time.sleep(15)


def check_and_report(key, host, check_type, current_status):
    previous_status = last_status.get(key)

    if current_status != "ok" and previous_status != "ok" and previous_status is not None:
        if current_status == "error":
            problem_description = f"{check_type} check failed — device unreachable or connection error"
        else:
            problem_description = f"{check_type} is down (status: {current_status})"

        log_event("watcher", host, "PROBLEM_CONFIRMED", problem_description)
        print(f"[{now()}] CONFIRMED PROBLEM: {host} — {problem_description} (2 checks in a row)")
    elif current_status == "ok":
        print(f"[{now()}] OK: {check_type} on {host} is healthy")

    last_status[key] = current_status


def now():
    return datetime.now(ZoneInfo("America/Chicago")).strftime("%H:%M:%S")


if __name__ == "__main__":
    print("watcher.py started - watching interfaces, OSPF, BGP, and VLANs on a timer.")
    print("This only detects and logs problems. It never fixes anything automatically.")

    threading.Thread(target=watch_interfaces, daemon=True).start()
    threading.Thread(target=watch_ospf, daemon=True).start()
    threading.Thread(target=watch_bgp, daemon=True).start()
    threading.Thread(target=watch_switches, daemon=True).start()

    while True:
        time.sleep(1)



        